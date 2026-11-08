# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


def decode_output(data):
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode(locale.getpreferredencoding(False) or "latin-1",
                           errors="replace")


class HistoryLineEdit(QLineEdit):
    """Ô nhập có lịch sử (phím ↑ / ↓)."""

    def __init__(self):
        super().__init__()
        self.history = []
        self._idx = 0

    def push(self, text):
        if text and (not self.history or self.history[-1] != text):
            self.history.append(text)
        self._idx = len(self.history)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Up and self.history:
            self._idx = max(0, self._idx - 1)
            self.setText(self.history[self._idx])
            return
        if e.key() == Qt.Key_Down and self.history:
            self._idx = min(len(self.history), self._idx + 1)
            self.setText(self.history[self._idx] if self._idx < len(self.history) else "")
            return
        super().keyPressEvent(e)


# Terminal: màu ANSI + link file:dòng
SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")
LINK_RE = re.compile(
    r'File "(?P<p1>[^"]+)", line (?P<l1>\d+)'
    r'|(?P<p2>(?:[A-Za-z]:)?[^\s:"\'()<>|*?]+\.[A-Za-z0-9_+]{1,6}):(?P<l2>\d+)(?::\d+)?'
    r'|(?P<p3>(?:[A-Za-z]:)?[^\s:"\'()<>|*?]+\.[A-Za-z0-9_+]{1,6})\((?P<l3>\d+)(?:,\d+)?\)'
    r'|(?P<p4>(?:[A-Za-z]:[\\/]|/)[^\s:"\'<>|*?]+\.[A-Za-z0-9_+]{1,6})')
ANSI16_DARK = ["#7a7a7a", "#f14c4c", "#23d18b", "#f5f543", "#3b8eea", "#d670d6", "#29b8db", "#e5e5e5",
               "#a0a0a0", "#ff6b6b", "#4ee89f", "#ffe066", "#6cb2ff", "#f09af0", "#5fd7f0", "#ffffff"]
ANSI16_LIGHT = ["#000000", "#cd3131", "#00835a", "#949800", "#0451a5", "#bc05bc", "#0598bc", "#555555",
                "#666666", "#cd3131", "#14a014", "#a0a500", "#0451a5", "#bc05bc", "#0598bc", "#a5a5a5"]


def ansi_256(n, pal):
    if n < 16:
        return QColor(pal[n])
    if n < 232:
        n -= 16
        lv = [0, 95, 135, 175, 215, 255]
        return QColor(lv[n // 36], lv[(n // 6) % 6], lv[n % 6])
    g = 8 + (n - 232) * 10
    return QColor(g, g, g)


def apply_sgr(fmt, params, pal):
    """Trả về QTextCharFormat mới sau khi áp mã SGR (vd '1;31')."""
    codes = [int(x) if x.isdigit() else 0 for x in params.split(";")] if params else [0]
    f = QTextCharFormat(fmt)
    i = 0
    while i < len(codes):
        c = codes[i]
        if c == 0:
            f = QTextCharFormat()
        elif c == 1:
            f.setFontWeight(QFont.Bold)
        elif c == 3:
            f.setFontItalic(True)
        elif c == 4:
            f.setFontUnderline(True)
        elif c == 22:
            f.setFontWeight(QFont.Normal)
        elif c == 23:
            f.setFontItalic(False)
        elif c == 24:
            f.setFontUnderline(False)
        elif 30 <= c <= 37:
            f.setForeground(QColor(pal[c - 30]))
        elif 90 <= c <= 97:
            f.setForeground(QColor(pal[8 + c - 90]))
        elif c == 39:
            f.clearForeground()
        elif 40 <= c <= 47:
            f.setBackground(QColor(pal[c - 40]))
        elif 100 <= c <= 107:
            f.setBackground(QColor(pal[8 + c - 100]))
        elif c == 49:
            f.clearBackground()
        elif c in (38, 48) and i + 1 < len(codes):
            col = None
            if codes[i + 1] == 5 and i + 2 < len(codes):
                col = ansi_256(max(0, min(255, codes[i + 2])), pal)
                i += 2
            elif codes[i + 1] == 2 and i + 4 < len(codes):
                col = QColor(*[max(0, min(255, v)) for v in codes[i + 2:i + 5]])
                i += 4
            if col is not None:
                (f.setForeground if c == 38 else f.setBackground)(col)
        i += 1
    return f


class EscLineEdit(QLineEdit):
    escaped = pyqtSignal()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.escaped.emit()
            return
        super().keyPressEvent(e)


class LinkOutput(QPlainTextEdit):
    """Khung output: click file.py:123 để nhảy tới dòng; Ctrl+C/V/F kiểu terminal."""
    link_clicked = pyqtSignal(str, int)
    find_requested = pyqtSignal()
    paste_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.base_dirs = lambda: []
        self.viewport().setMouseTracking(True)

    def _resolve(self, path):
        if os.path.isabs(path):
            return path if os.path.isfile(path) else None
        for b in self.base_dirs():
            if b:
                p = os.path.join(b, path)
                if os.path.isfile(p):
                    return p
        return None

    def link_at(self, pos):
        cur = self.cursorForPosition(pos)
        text, col = cur.block().text(), cur.positionInBlock()
        for m in LINK_RE.finditer(text):
            if m.start() <= col <= m.end():
                path = m.group("p1") or m.group("p2") or m.group("p3") or m.group("p4")
                line = m.group("l1") or m.group("l2") or m.group("l3") or "0"
                full = self._resolve(path)
                if full:
                    return full, int(line)
        return None

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        if e.buttons() == Qt.NoButton:
            self.viewport().setCursor(Qt.PointingHandCursor if self.link_at(e.pos())
                                      else Qt.IBeamCursor)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if e.button() == Qt.LeftButton and not self.textCursor().hasSelection():
            hit = self.link_at(e.pos())
            if hit:
                self.link_clicked.emit(*hit)

    def event(self, e):
        if e.type() == QEvent.ShortcutOverride and (e.modifiers() & Qt.ControlModifier) \
                and e.key() in (Qt.Key_F, Qt.Key_C, Qt.Key_V, Qt.Key_A):
            e.accept()
            return True
        return super().event(e)

    def keyPressEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            if e.key() == Qt.Key_F:
                self.find_requested.emit()
                return
            if e.key() == Qt.Key_V:
                self.paste_requested.emit(QApplication.clipboard().text())
                return
        super().keyPressEvent(e)


class TerminalPanel(QWidget):
    """Chạy các bước (biên dịch, chạy...) bằng QProcess, hiển thị output trực
    tiếp, cho phép nhập liệu (stdin) và dừng tiến trình."""

    def __init__(self, theme=None):
        super().__init__()
        self.theme = theme or THEMES[DEFAULT_THEME]
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.find_edit = EscLineEdit()
        self.find_edit.setPlaceholderText("Tìm trong output (Enter = kế tiếp, Esc = đóng)")
        self.find_edit.hide()
        lay.addWidget(self.find_edit)
        self.output = LinkOutput()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(20000)
        self.output.setFont(pick_font(10))
        lay.addWidget(self.output, 1)

        row = QHBoxLayout()
        row.setContentsMargins(4, 3, 4, 3)
        self.prompt = QLabel("›")
        self.input = HistoryLineEdit()
        self.input.setPlaceholderText(
            "Nhập dữ liệu cho chương trình (input) rồi nhấn Enter...")
        self.stop_btn = QPushButton("■ Dừng")
        self.eof_btn = QPushButton("EOF")
        self.eof_btn.setToolTip("Đóng stdin (Ctrl+D): báo cho chương trình hết dữ liệu nhập")
        self.clear_btn = QPushButton("Xóa")
        self.copy_btn = QPushButton("Sao chép")
        self.save_btn = QPushButton("Lưu log...")
        row.addWidget(self.prompt)
        row.addWidget(self.input, 1)
        row.addWidget(self.stop_btn)
        row.addWidget(self.eof_btn)
        row.addWidget(self.copy_btn)
        row.addWidget(self.save_btn)
        row.addWidget(self.clear_btn)
        lay.addLayout(row)

        self.process = None
        self.queue = []
        self.total_steps = 0
        self.cwd = None
        self.path_map = {}
        self.cleanup_paths = []
        self.last_output = ""
        self.on_output = None
        self._ansi_fmt = QTextCharFormat()
        self._esc_carry = ""
        self._pal = ANSI16_DARK
        self._t0 = 0.0
        self._label = "?"
        self._reset_callbacks()

        self.input.returnPressed.connect(self._send_input)
        self.stop_btn.clicked.connect(lambda: self.stop())
        self.eof_btn.clicked.connect(self.send_eof)
        self.clear_btn.clicked.connect(self.output.clear)
        self.copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.output.toPlainText()))
        self.save_btn.clicked.connect(self.save_log)
        self.output.find_requested.connect(self.show_find)
        self.output.paste_requested.connect(self._paste)
        self.find_edit.returnPressed.connect(self._find_next)
        self.find_edit.escaped.connect(self._hide_find)
        self._set_running(False)
        self.apply_theme(self.theme)

    def _reset_callbacks(self):
        self.on_done = None
        self.on_step = None
        self.on_fail = None

    def apply_theme(self, theme):
        self.theme = theme
        self._pal = ANSI16_LIGHT if QColor(theme['terminal_bg']).lightness() > 128 else ANSI16_DARK
        self.output.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {theme['terminal_bg']}; "
            f"color: {theme['terminal_fg']}; border: none; }}")
        self.prompt.setStyleSheet(f"color: {theme['accent']}; font-weight: bold;")

    def _set_running(self, running):
        self.stop_btn.setEnabled(running)
        self.input.setEnabled(running)
        self.eof_btn.setEnabled(running)
        self.input.setPlaceholderText(
            "Nhập dữ liệu cho chương trình (input) rồi nhấn Enter..." if running
            else "Chương trình chưa chạy - nhấn F5 để chạy")
        if running:
            # setFocus trên widget đang bị disable thì vô hiệu -> focus sau khi đã bật
            QTimer.singleShot(0, self.input.setFocus)

    #  ghi output
    # Output được đệm rồi đổ ra từng đợt nhỏ (mỗi ~20ms) để chương trình in rất nhiều
    # dòng không làm đơ giao diện. last_output cập nhật ngay để logic "thiếu thư viện" vẫn đúng.
    FLUSH_CHARS = 48000          # tối đa ký tự hiển thị mỗi đợt
    MAX_PENDING = 3000000        # quá mức này: bỏ phần giữa, chỉ giữ phần mới nhất

    def _write(self, text):
        for k, v in self.path_map.items():   # đổi tên file tạm thành tên thật
            text = text.replace(k, v)
        self.last_output = (self.last_output + ANSI_RE.sub("", text.replace("\r\n", "\n")))[-30000:]
        if not hasattr(self, "_pending"):
            self._pending, self._pending_len = [], 0
            self._flush_timer = QTimer(self)
            self._flush_timer.setInterval(20)
            self._flush_timer.timeout.connect(self._flush_pending)
        self._pending.append(text)
        self._pending_len += len(text)
        if self._pending_len > self.MAX_PENDING:
            joined = "".join(self._pending)
            drop = len(joined) - self.MAX_PENDING // 2
            joined = "\n>>> (đã bỏ qua %d KB output để giữ giao diện mượt)\n" % (drop // 1024) + joined[drop:]
            self._pending, self._pending_len = [joined], len(joined)
        if not self._flush_timer.isActive():
            self._flush_timer.start()

    def _flush_pending(self):
        if not self._pending:
            self._flush_timer.stop()
            return
        joined = "".join(self._pending)
        if len(joined) > self.FLUSH_CHARS:
            cut = joined.rfind("\n", 0, self.FLUSH_CHARS)
            cut = cut + 1 if cut > 0 else self.FLUSH_CHARS
            chunk, rest = joined[:cut], joined[cut:]
            self._pending, self._pending_len = [rest], len(rest)
        else:
            chunk, self._pending, self._pending_len = joined, [], 0
        self._write_now(chunk)

    def flush_all(self):
        while getattr(self, "_pending", None):
            self._flush_pending()

    def _write_now(self, text):
        text = self._esc_carry + text
        self._esc_carry = ""
        m = re.search(r"\x1b(?:\[[0-9;?]*)?$", text)   # mã ANSI bị cắt giữa chừng
        if m:
            self._esc_carry, text = m.group(0), text[:m.start()]
        text = text.replace("\r\n", "\n")
        segments, pos = [], 0
        for mm in SGR_RE.finditer(text):
            segments.append((text[pos:mm.start()], self._ansi_fmt))
            self._ansi_fmt = apply_sgr(self._ansi_fmt, mm.group(1), self._pal)
            pos = mm.end()
        segments.append((text[pos:], self._ansi_fmt))
        cur = self.output.textCursor()
        cur.movePosition(QTextCursor.End)
        for seg, fmt in segments:
            seg = ANSI_RE.sub("", seg)
            for i, part in enumerate(seg.split("\r")):
                if i > 0:  # '\r' đơn: ghi đè dòng hiện tại (thanh tiến trình pip...)
                    cur.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
                    cur.removeSelectedText()
                if part:
                    cur.insertText(part, fmt)
        self.output.setTextCursor(cur)
        self.output.ensureCursorVisible()

    #  tìm / dán / lưu
    def show_find(self):
        self.find_edit.show()
        self.find_edit.setFocus()
        self.find_edit.selectAll()

    def _hide_find(self):
        self.find_edit.hide()
        self.output.setFocus()

    def _find_next(self):
        t = self.find_edit.text()
        if t and not self.output.find(t):
            cur = self.output.textCursor()
            cur.movePosition(QTextCursor.Start)
            self.output.setTextCursor(cur)
            self.output.find(t)

    def _paste(self, text):
        self.input.insert(text.replace("\r", "").replace("\n", " "))
        self.input.setFocus()

    def save_log(self):
        f, _ = QFileDialog.getSaveFileName(self, "Lưu log terminal", "terminal.log", "Log (*.log *.txt)")
        if f:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(self.output.toPlainText())

    def appendPlainText(self, text):
        self._write(text + "\n")

    def _send_input(self):
        text = self.input.text()
        self.input.push(text)
        self.input.clear()
        self.send_input(text)

    def send_eof(self):
        """Đóng stdin của tiến trình đang chạy (EOF)."""
        p = self.process
        if p is not None and p.state() != QProcess.NotRunning:
            p.closeWriteChannel()
            self._write("^D\n")

    def send_input(self, text):
        """Gửi một dòng vào stdin của tiến trình đang chạy. Trả về True nếu gửi được."""
        p = self.process
        if p is None or p.state() == QProcess.NotRunning:
            return False
        if p.state() == QProcess.Starting and not p.waitForStarted(3000):
            return False        # trước đây gõ lúc tiến trình đang khởi động bị nuốt mất
        self._write(text + "\n")
        p.write((text + "\n").encode("utf-8"))
        return True

    #  hàng đợi
    def run_queue(self, steps, on_done=None, on_step=None, on_fail=None,
                  cwd=None, cleanup_paths=None, path_map=None):
        self.stop(silent=True)
        self.queue = list(steps)
        self.total_steps = len(steps)
        self.on_done, self.on_step, self.on_fail = on_done, on_step, on_fail
        self.cwd = cwd
        self.path_map = dict(path_map or {})
        self.cleanup_paths = list(cleanup_paths or [])
        self.last_output = ""
        self._t0 = time.time()
        self._run_next()

    def _run_next(self):
        if not self.queue:
            self._write(f">>> Hoàn tất tất cả các bước ({time.time() - self._t0:.2f}s).\n")
            cb = self.on_done
            self._reset_callbacks()
            self._set_running(False)
            self._cleanup()
            if cb:
                cb()
            return
        label, program, args = self.queue.pop(0)
        self._ansi_fmt = QTextCharFormat()
        self._label = label
        if self.on_step:
            self.on_step(self.total_steps - len(self.queue), self.total_steps, label)
        self._write(f"\n>>> {label}: {program} {' '.join(args)}\n")

        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.MergedChannels)
        if self.cwd:
            proc.setWorkingDirectory(self.cwd)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("PYTHONIOENCODING", "utf-8")
        if not os.environ.get("NO_COLOR"):
            env.insert("FORCE_COLOR", "1")
        proc.setProcessEnvironment(env)
        proc.readyReadStandardOutput.connect(lambda p=proc: self._read(p))
        proc.finished.connect(lambda code, st, p=proc: self._step_finished(p, code, st))
        proc.errorOccurred.connect(lambda err, p=proc, prog=program: self._on_error(p, err, prog))
        proc.finished.connect(proc.deleteLater)
        self.process = proc
        self._set_running(True)
        proc.start(program, args)

    def _read(self, proc):
        if proc is not self.process:
            return
        data = bytes(proc.readAllStandardOutput())
        if data:
            text = decode_output(data)
            self._write(text)
            if self.on_output:
                try:
                    self.on_output(text)
                except Exception:  # noqa: BLE001
                    pass

    def _step_finished(self, proc, code, status):
        if proc is not self.process:
            return
        self._read(proc)
        self.process = None
        if code != 0 or status == QProcess.CrashExit:
            self._fail(code)
        else:
            self._run_next()

    def _on_error(self, proc, err, program):
        if err == QProcess.FailedToStart and proc is self.process:
            self.process = None
            self._write(f">>> Không thể khởi chạy: {program}\n")
            self._fail(-1)

    def _fail(self, code):
        self._write(f">>> Bước thất bại (mã thoát {code}). Dừng lại.\n")
        cb, label = self.on_fail, self._label
        self.queue = []
        self._reset_callbacks()
        self._set_running(False)
        self._cleanup()
        if cb:
            cb(label, code)

    def stop(self, silent=False):
        proc = self.process
        self.process = None
        had_work = proc is not None or bool(self.queue)
        self.queue = []
        self._reset_callbacks()
        if proc is not None:
            proc.kill()
        self._set_running(False)
        if had_work and not silent:
            self._write("\n>>> Đã dừng.\n")
        if had_work:
            old = self.cleanup_paths
            self.cleanup_paths = []
            QTimer.singleShot(500, lambda: self._cleanup(old))
        return had_work

    def _cleanup(self, paths=None):
        own = paths is None
        for p in (self.cleanup_paths if own else paths):
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                elif os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass
        if own:
            self.cleanup_paths = []


# Hộp thoại Build EXE
class BuildOptionsDialog(QDialog):
    def __init__(self, parent, settings, default_name, default_out, lang):
        super().__init__(parent)
        self.settings = settings
        self.is_python = lang == "python"
        self.setWindowTitle("Tùy chọn Build EXE")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Tên file .exe:"))
        self.name_edit = QLineEdit(default_name)
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Thư mục xuất:"))
        out_row = QHBoxLayout()
        self.out_edit = QLineEdit(settings.value("build/out_dir", "") or default_out)
        out_browse = QPushButton("Chọn...")
        out_browse.clicked.connect(self.browse_out_dir)
        out_row.addWidget(self.out_edit)
        out_row.addWidget(out_browse)
        layout.addLayout(out_row)

        self.py_widgets = []

        def add_py(w):
            layout.addWidget(w)
            self.py_widgets.append(w)

        add_py(QLabel("Icon (.ico) - để trống nếu dùng icon mặc định:"))
        icon_holder = QWidget()
        icon_row = QHBoxLayout(icon_holder)
        icon_row.setContentsMargins(0, 0, 0, 0)
        self.icon_edit = QLineEdit(settings.value("build/icon_path", ""))
        icon_browse = QPushButton("Chọn...")
        icon_browse.clicked.connect(self.browse_icon)
        icon_row.addWidget(self.icon_edit)
        icon_row.addWidget(icon_browse)
        add_py(icon_holder)

        add_py(QLabel("Kiểu đóng gói:"))
        mode_holder = QWidget()
        mode_row = QHBoxLayout(mode_holder)
        mode_row.setContentsMargins(0, 0, 0, 0)
        self.onefile_radio = QRadioButton("Onefile (1 file exe duy nhất)")
        self.onedir_radio = QRadioButton("Onedir (1 thư mục, mở nhanh hơn)")
        g1 = QButtonGroup(self)
        g1.addButton(self.onefile_radio)
        g1.addButton(self.onedir_radio)
        (self.onefile_radio if settings.value("build/onefile", "true") == "true"
         else self.onedir_radio).setChecked(True)
        mode_row.addWidget(self.onefile_radio)
        mode_row.addWidget(self.onedir_radio)
        add_py(mode_holder)

        add_py(QLabel("Cửa sổ console:"))
        con_holder = QWidget()
        con_row = QHBoxLayout(con_holder)
        con_row.setContentsMargins(0, 0, 0, 0)
        self.windowed_radio = QRadioButton("Ẩn console (app có giao diện)")
        self.console_radio = QRadioButton("Hiện console (để xem lỗi/log)")
        g2 = QButtonGroup(self)
        g2.addButton(self.windowed_radio)
        g2.addButton(self.console_radio)
        (self.console_radio if settings.value("build/console", "false") == "true"
         else self.windowed_radio).setChecked(True)
        con_row.addWidget(self.windowed_radio)
        con_row.addWidget(self.console_radio)
        add_py(con_holder)

        add_py(QLabel("Hidden imports (cách nhau bằng dấu phẩy) - cho thư viện "
                      "PyInstaller bỏ sót:"))
        self.hidden_edit = QLineEdit(settings.value("build/hidden", ""))
        add_py(self.hidden_edit)

        add_py(QLabel("Thêm file/thư mục dữ liệu (mỗi dòng: nguồn;đích). "
                      "Ví dụ: assets;assets"))
        self.data_edit = QPlainTextEdit()
        self.data_edit.setObjectName("addData")
        self.data_edit.setFixedHeight(60)
        self.data_edit.setPlainText(settings.value("build/add_data", ""))
        add_py(self.data_edit)

        self.clean_cb = QCheckBox("Xóa thư mục build tạm sau khi xong")
        self.clean_cb.setChecked(settings.value("build/clean", "true") == "true")
        self.open_cb = QCheckBox("Mở thư mục xuất khi build thành công")
        self.open_cb.setChecked(settings.value("build/open", "true") == "true")
        layout.addWidget(self.clean_cb)
        layout.addWidget(self.open_cb)

        for w in self.py_widgets:
            w.setEnabled(self.is_python)
        self.clean_cb.setEnabled(self.is_python)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_out_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục xuất", self.out_edit.text() or os.getcwd())
        if d:
            self.out_edit.setText(d)

    def browse_icon(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn icon", "", "Icon Files (*.ico)")
        if f:
            self.icon_edit.setText(f)

    def get_values(self):
        hidden = [h.strip() for h in self.hidden_edit.text().split(",") if h.strip()]
        data = [ln.strip() for ln in self.data_edit.toPlainText().splitlines()
                if ln.strip()]
        return {
            "name": self.name_edit.text().strip(),
            "out_dir": self.out_edit.text().strip(),
            "icon_path": self.icon_edit.text().strip(),
            "onefile": self.onefile_radio.isChecked(),
            "console": self.console_radio.isChecked(),
            "hidden": hidden,
            "add_data": data,
            "clean": self.clean_cb.isChecked(),
            "open_out": self.open_cb.isChecked(),
        }

    def save_to_settings(self):
        v = self.get_values()
        s = self.settings
        s.setValue("build/out_dir", v["out_dir"])
        s.setValue("build/icon_path", v["icon_path"])
        s.setValue("build/onefile", "true" if v["onefile"] else "false")
        s.setValue("build/console", "true" if v["console"] else "false")
        s.setValue("build/hidden", ", ".join(v["hidden"]))
        s.setValue("build/add_data", "\n".join(v["add_data"]))
        s.setValue("build/clean", "true" if v["clean"] else "false")
        s.setValue("build/open", "true" if v["open_out"] else "false")


# Hộp chọn nhanh (Command Palette / Quick Open / Outline)
class PickerDialog(QDialog):
    MAX_ITEMS = 300

    def __init__(self, parent, title, items, placeholder="Gõ để lọc..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(640, 420)
        self.items = items            # list[(nhãn, dữ liệu)]
        self._sel = None
        lay = QVBoxLayout(self)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.list = QListWidget()
        lay.addWidget(self.edit)
        lay.addWidget(self.list, 1)
        self.edit.textChanged.connect(self._filter)
        self.edit.returnPressed.connect(self._accept_current)
        self.list.itemActivated.connect(lambda _i: self._accept_current())
        self._filter("")
        self.edit.setFocus()

    def _filter(self, text):
        words = text.lower().split()
        self.list.clear()
        shown = 0
        for idx, (label, _data) in enumerate(self.items):
            low = label.lower()
            if all(w in low for w in words):
                it = QListWidgetItem(label)
                it.setData(Qt.UserRole, idx)
                self.list.addItem(it)
                shown += 1
                if shown >= self.MAX_ITEMS:
                    break
        if self.list.count():
            self.list.setCurrentRow(0)

    def _accept_current(self):
        it = self.list.currentItem()
        if it is not None:
            self._sel = it.data(Qt.UserRole)
            self.accept()

    def selected(self):
        return None if self._sel is None else self.items[self._sel][1]

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Up, Qt.Key_Down) and self.list.count():
            row = self.list.currentRow() + (1 if e.key() == Qt.Key_Down else -1)
            self.list.setCurrentRow(max(0, min(self.list.count() - 1, row)))
            return
        super().keyPressEvent(e)


# Cửa sổ chính
# BỘ CÔNG CỤ MỞ RỘNG: Plugin API, Tải URL, Git, ESP, Serial, Mẫu dự án, Console
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
MAX_UNZIP_BYTES = 2 * 1024 ** 3
