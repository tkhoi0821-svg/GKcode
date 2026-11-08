# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp', 'templates', 'polyglot']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


def find_project_python(root):
    """Tìm python trong venv của dự án (.venv / venv / env)."""
    for d in (".venv", "venv", "env", ".env"):
        for rel in (("Scripts", "python.exe"), ("bin", "python")):
            p = os.path.join(root, d, *rel)
            if os.path.isfile(p):
                return p
    return None


class CCompilerDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Trình biên dịch C / C++")
        self.setMinimumWidth(560)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Trình biên dịch C (C++ tự lấy bản đi kèm: g++ / clang++):"))
        row = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.addItem("Tự động (dò trong PATH)", "")
        for name, p in detect_c_compilers():
            self.combo.addItem(f"{name}  -  {p}", p)
        if CFG.C_COMPILER:
            i = self.combo.findData(CFG.C_COMPILER)
            if i < 0:
                self.combo.addItem(CFG.C_COMPILER, CFG.C_COMPILER)
                i = self.combo.count() - 1
            self.combo.setCurrentIndex(i)
        browse = QPushButton("Chọn file...")
        browse.clicked.connect(self._browse)
        row.addWidget(self.combo, 1)
        row.addWidget(browse)
        lay.addLayout(row)
        self.info = QLabel("")
        self.info.setWordWrap(True)
        lay.addWidget(self.info)
        form = QFormLayout()
        self.cflags = QLineEdit(CFG.C_FLAGS)
        self.cppflags = QLineEdit(CFG.CPP_FLAGS)
        self.cflags.setPlaceholderText("vd: -std=c17 -Wall -Wextra -g")
        self.cppflags.setPlaceholderText("vd: -std=c++17 -Wall -Wextra")
        form.addRow("Cờ cho C:", self.cflags)
        form.addRow("Cờ cho C++:", self.cppflags)
        lay.addLayout(form)
        btns = QHBoxLayout()
        test_b, help_b = QPushButton("Kiểm tra thử"), QPushButton("Cách cài trình biên dịch...")
        test_b.clicked.connect(self.test)
        help_b.clicked.connect(self.install_help)
        btns.addWidget(test_b)
        btns.addWidget(help_b)
        btns.addStretch(1)
        lay.addLayout(btns)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.combo.currentIndexChanged.connect(lambda _i: self._show_info())
        self.combo.editTextChanged.connect(lambda _t: self._show_info())
        self._show_info()

    def _browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn trình biên dịch", "", "Tất cả (*)")
        if f:
            self.combo.addItem(f, f)
            self.combo.setCurrentIndex(self.combo.count() - 1)

    def path(self):
        i = self.combo.currentIndex()
        txt = self.combo.currentText().strip()
        if i >= 0 and txt == self.combo.itemText(i):
            return self.combo.itemData(i) or ""
        return txt            # người dùng gõ tay

    def _resolved(self):
        p = self.path()
        return p if p and os.path.isfile(p) else find_tool("gcc", "clang", "cc", "tcc")

    def _show_info(self):
        p = self._resolved()
        self.info.setText(f"→ {p}\n{compiler_version(p)}" if p
                          else "Không tìm thấy trình biên dịch nào. Bấm 'Cách cài trình biên dịch...'.")

    def test(self):
        cc = self._resolved()
        if not cc:
            QMessageBox.warning(self, "Kiểm tra", NO_CC_MSG)
            return
        tmp = tempfile.mkdtemp(prefix="pyapp_cc_")
        try:
            src, exe = os.path.join(tmp, "t.c"), os.path.join(tmp, "t" + EXE_EXT)
            with open(src, "w", encoding="utf-8", newline="\n") as f:
                f.write('#include <stdio.h>\nint main(void){puts("GKcode C OK");return 0;}\n')
            code, out, err = run_capture([cc, src] + split_flags(self.cflags.text()) + ["-o", exe], 60, tmp)
            if code != 0:
                QMessageBox.critical(self, "Biên dịch lỗi", (err or out)[-1500:])
                return
            code, out, err = run_capture([exe], 10, tmp)
            QMessageBox.information(self, "Kiểm tra thử",
                                    f"Biên dịch và chạy thành công.\nKết quả: {out.strip()}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def install_help(self):
        if os.name == "nt":
            r = QMessageBox.question(
                self, "Cài trình biên dịch (Windows)",
                "Cách đơn giản nhất: tải w64devkit (GCC gọn nhẹ, giải nén là dùng):\n"
                "https://github.com/skeeto/w64devkit/releases\n\n"
                "Hoặc cài MSYS2 (https://www.msys2.org) rồi chạy: pacman -S mingw-w64-ucrt-x86_64-gcc\n\n"
                "Sau khi cài, thêm thư mục bin vào PATH (hoặc chọn file gcc.exe bằng nút 'Chọn file...').\n\n"
                "Mở trang tải w64devkit ngay?")
            if r == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl("https://github.com/skeeto/w64devkit/releases"))
        elif sys.platform == "darwin":
            QMessageBox.information(self, "Cài trình biên dịch (macOS)",
                                    "Mở Terminal và chạy:\n\n    xcode-select --install")
        else:
            QMessageBox.information(self, "Cài trình biên dịch (Linux)",
                                    "Debian/Ubuntu:   sudo apt install build-essential\n"
                                    "Fedora:               sudo dnf install gcc gcc-c++\n"
                                    "Arch:                  sudo pacman -S gcc")

    def values(self):
        return {"path": self.path(), "flags": self.cflags.text().strip(),
                "cppflags": self.cppflags.text().strip()}


class PyAppAPI:
    """API của GKcode - đối tượng `api` được truyền vào plugin và script.

    Plugin là file .py đặt trong  ~/.pyapp/plugins  (hoặc thư mục plugins cạnh app),
    chứa hàm  register(api).  Ví dụ:

        def register(api):
            api.add_action("Chào", lambda: api.message("Xin chào!"))
    """

    def __init__(self, win, name="script"):
        self.win = win
        self.name = name
        self._owned = []
        self._submenu = None

    #  thông tin
    @property
    def version(self):
        """Phiên bản của app."""
        return APP_VERSION

    @property
    def window(self):
        """Cửa sổ chính (PyApp) - dùng khi cần truy cập sâu hơn."""
        return self.win

    @property
    def terminal(self):
        """Terminal của app."""
        return self.win.terminal

    @property
    def editor(self):
        """Editor (CodeEditor) của tab hiện tại, hoặc None."""
        return self.win.current_editor()

    def theme(self):
        """Dict màu của theme hiện tại."""
        return dict(THEMES[self.win.theme_name])

    #  soạn thảo
    def text(self):
        """Toàn bộ nội dung tab hiện tại."""
        ed = self.editor
        return ed.toPlainText() if ed else ""

    def set_text(self, text):
        """Thay toàn bộ nội dung tab hiện tại (hoàn tác được bằng Ctrl+Z)."""
        ed = self.editor
        if ed:
            ed.replace_all_text(text)

    def selection(self):
        """Đoạn đang chọn (chuỗi rỗng nếu không chọn gì)."""
        ed = self.editor
        return ed.textCursor().selectedText().replace("\u2029", "\n") if ed else ""

    def replace_selection(self, text):
        """Thay đoạn đang chọn bằng `text` (hoặc chèn tại con trỏ nếu không chọn)."""
        ed = self.editor
        if ed:
            ed.textCursor().insertText(text)

    def insert(self, text):
        """Chèn `text` tại vị trí con trỏ."""
        self.replace_selection(text)

    def new_file(self, content="", lang="python"):
        """Mở tab mới (chưa đặt tên) với nội dung và ngôn ngữ cho trước."""
        ed = self.win.new_tab(content=content)
        ed.set_language(lang)
        return ed

    def open(self, path):
        """Mở file trong editor."""
        self.win.open_path(path)

    def save(self):
        """Lưu tab hiện tại. Trả về True nếu thành công."""
        return self.win.save_file()

    def file_path(self):
        """Đường dẫn file của tab hiện tại (None nếu chưa lưu)."""
        ed = self.editor
        return ed.file_path if ed else None

    def language(self):
        """Khóa ngôn ngữ của tab hiện tại: python, c, cpp, go, java, javascript..."""
        ed = self.editor
        return ed.lang if ed else None

    def goto_line(self, n):
        """Nhảy tới dòng số n."""
        ed = self.editor
        if ed:
            ed.goto_line(n)

    def project_root(self):
        """Thư mục dự án hiện tại (thư mục đang mở trong Explorer)."""
        return self.win._project_root()

    def set_project_root(self, path):
        """Đặt thư mục dự án và hiển thị trong Explorer."""
        self.win._set_explorer_root(path)

    #  giao diện
    def _top_menu(self, title):
        for a in self.win.menuBar().actions():
            m = a.menu()
            if m is not None and m.title().replace("&", "") == title:
                return m
        m = self.win.menuBar().addMenu(title)
        self._owned.append(("menu", m, None))
        return m

    def _plugin_submenu(self):
        if self._submenu is None:
            self._submenu = self.win.plugins_menu.addMenu(self.name)
        return self._submenu

    def _resolve_menu(self, menu):
        if menu is None:
            return self._plugin_submenu()
        if isinstance(menu, str):
            return self._top_menu(menu)
        return menu

    def _safe(self, fn, *args):
        try:
            return fn(*args)
        except Exception:  # noqa: BLE001
            self.win.terminal.appendPlainText(
                f"\n[plugin {self.name}] LỖI:\n" + traceback.format_exc())

    def add_action(self, text, callback, shortcut=None, menu=None):
        """Thêm mục menu. menu=None -> menu con của plugin trong 'Plugins';
        menu='Tools' (hoặc tên menu có sẵn / tên mới) -> menu đó. callback không nhận tham số."""
        target = self._resolve_menu(menu)
        a = QAction(text, self.win)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(lambda _=False: self._safe(callback))
        target.addAction(a)
        self._owned.append(("action", a, target))
        return a

    def add_separator(self, menu=None):
        """Thêm đường kẻ phân cách vào menu."""
        target = self._resolve_menu(menu)
        a = target.addSeparator()
        self._owned.append(("action", a, target))

    def add_toolbar_button(self, text, callback, tooltip=None):
        """Thêm nút lên thanh công cụ."""
        a = QAction(text, self.win)
        if tooltip:
            a.setToolTip(tooltip)
        a.triggered.connect(lambda _=False: self._safe(callback))
        self.win.toolbar.addAction(a)
        self._owned.append(("toolbar", a, self.win.toolbar))
        return a

    def add_dock(self, title, widget, area="right"):
        """Thêm panel (QWidget bất kỳ) vào cửa sổ. area: left/right/bottom/top."""
        areas = {"left": Qt.LeftDockWidgetArea, "right": Qt.RightDockWidgetArea,
                 "bottom": Qt.BottomDockWidgetArea, "top": Qt.TopDockWidgetArea}
        d = QDockWidget(title, self.win)
        d.setObjectName(f"plugin_{self.name}_{title}")
        d.setWidget(widget)
        self.win.addDockWidget(areas.get(area, Qt.RightDockWidgetArea), d)
        self._owned.append(("dock", d, None))
        return d

    def add_snippet(self, lang, key, template):
        """Thêm snippet: gõ `key` + Tab. Trong template dùng $0 cho vị trí con trỏ."""
        SNIPPETS.setdefault(lang, {})[key] = template
        self._owned.append(("snippet", (lang, key), None))

    def on(self, event, callback):
        """Đăng ký sự kiện: start, open, save, run, quit, change (sau khi ngừng gõ 0,3s),
        cursor (con trỏ dời), tab_change, tab_close, theme (callback nhận tên theme).
        callback(editor|tên_theme|None)."""
        wrapped = lambda *a: self._safe(callback, *a)  # noqa: E731
        self.win._events.setdefault(event, []).append(wrapped)
        self._owned.append(("event", (event, wrapped), None))

    def unload(self):
        """(Nội bộ) gỡ mọi thứ plugin đã thêm."""
        for kind, obj, parent in reversed(self._owned):
            try:
                if kind in ("action", "toolbar"):
                    parent.removeAction(obj)
                elif kind == "menu":
                    self.win.menuBar().removeAction(obj.menuAction())
                    obj.deleteLater()
                elif kind == "dock":
                    self.win.removeDockWidget(obj)
                    obj.deleteLater()
                elif kind == "snippet":
                    SNIPPETS.get(obj[0], {}).pop(obj[1], None)
                elif kind == "event":
                    lst = self.win._events.get(obj[0], [])
                    if obj[1] in lst:
                        lst.remove(obj[1])
                elif kind == "timer":
                    obj.stop()
                    obj.deleteLater()
                elif kind == "context":
                    if obj in self.win._context_actions:
                        self.win._context_actions.remove(obj)
                elif kind == "lint":
                    if obj in self.win._lint_providers:
                        self.win._lint_providers.remove(obj)
                elif kind == "statusw":
                    self.win.statusBar().removeWidget(obj)
                    obj.deleteLater()
                elif kind == "theme":
                    key, act = obj
                    if self.win.theme_name == key:
                        self.win.set_theme(DEFAULT_THEME)
                    self.win._theme_menu.removeAction(act)
                    self.win._theme_actions.pop(act, None)
                    THEMES.pop(key, None)
                elif kind == "language":
                    self._restore_language(obj)
                elif kind == "shortcut":
                    obj.setEnabled(False)
                    obj.deleteLater()
                elif kind == "explorer":
                    if obj in self.win._explorer_actions:
                        self.win._explorer_actions.remove(obj)
                elif kind == "opener":
                    unregister_opener(obj)
            except (RuntimeError, ValueError):
                pass
        self._owned = []
        if self._submenu is not None:
            try:
                self.win.plugins_menu.removeAction(self._submenu.menuAction())
                self._submenu.deleteLater()
            except RuntimeError:
                pass
            self._submenu = None

    #  trình mở file (4.2)
    def register_opener(self, name, exts, callback, sniff=None):
        """Đăng ký trình mở file: callback(path) -> True nếu đã mở xong (False = thử trình khác).
        exts như ['.fbx', '.blend']; thêm '*' để nhận mọi file nhị phân chưa ai nhận.
        sniff(head_bytes) -> bool để nhận file theo nội dung. Trình mở của plugin được thử trước trình có sẵn."""
        key = "plugin:%s:%s" % (self.name, name)
        ent = register_opener(key, name, list(exts), lambda _w, p: bool(self._safe(callback, p)),
                              owner=self.name, sniff=sniff)
        self._owned.append(("opener", ent, None))
        return ent

    def show_mesh(self, verts, faces, title="Mesh 3D"):
        """Hiện mesh 3D: verts=[(x,y,z)], faces=[(i,j,k,...)] - dùng khi plugin tự đọc được định dạng lạ."""
        _std_dialog(self.win, MeshViewerDialog(self.win, "", data=(verts, faces), title=title))

    def parse_mesh(self, path):
        """Đọc GLB/glTF/OBJ/STL/PLY/FBX/OFF → (verts, faces)."""
        v, f, _note = parse_mesh_any(path)
        return v, f

    def view_hex(self, path):
        """Mở file bằng Hex viewer."""
        _std_dialog(self.win, HexViewerDialog(self.win, path))

    def view_image(self, path):
        """Mở ảnh bằng trình xem ảnh."""
        self.win._show(ImageViewerDialog(self.win, path))

    def play_media(self, path):
        """Phát video/audio."""
        _op_media(self.win, path)

    def ffmpeg_path(self):
        """Đường dẫn ffmpeg (hoặc None)."""
        return find_ffmpeg(self.win)

    def check_plugin_source(self, source):
        """Kiểm API tĩnh một đoạn mã plugin → dict báo cáo (ok, errors, warnings, unknown_api...)."""
        return check_plugin_source(source, "plugin.py", public_api_names(), API_VERSION, module_available)

    #  hộp thoại
    def message(self, text, title="Thông báo"):
        """Hiện hộp thông báo."""
        QMessageBox.information(self.win, title, str(text))

    def error(self, text, title="Lỗi"):
        """Hiện hộp báo lỗi."""
        QMessageBox.critical(self.win, title, str(text))

    def confirm(self, question, title="Xác nhận"):
        """Hỏi Có/Không. Trả về True nếu chọn Có."""
        return QMessageBox.question(self.win, title, str(question)) == QMessageBox.Yes

    def ask(self, prompt, default="", title="Nhập"):
        """Hỏi một chuỗi. Trả về chuỗi hoặc None nếu hủy."""
        v, ok = QInputDialog.getText(self.win, title, prompt, QLineEdit.Normal, default)
        return v if ok else None

    def choose(self, title, items, current=0):
        """Chọn một mục trong danh sách chuỗi. Trả về mục chọn hoặc None."""
        v, ok = QInputDialog.getItem(self.win, title, title, list(items), current, False)
        return v if ok else None

    def pick_file(self, save=False, filter="Tất cả (*)", title="Chọn file"):
        """Hộp chọn file. Trả về đường dẫn ('' nếu hủy)."""
        if save:
            p, _ = QFileDialog.getSaveFileName(self.win, title, "", filter)
        else:
            p, _ = QFileDialog.getOpenFileName(self.win, title, "", filter)
        return p

    def pick_folder(self, title="Chọn thư mục"):
        """Hộp chọn thư mục. Trả về đường dẫn ('' nếu hủy)."""
        return QFileDialog.getExistingDirectory(self.win, title)

    def status(self, text, ms=3000):
        """Hiện chữ ngắn ở thanh trạng thái."""
        self.win.statusBar().showMessage(str(text), ms)

    def copy(self, text):
        """Chép chuỗi vào clipboard."""
        QApplication.clipboard().setText(str(text))

    #  terminal / chạy lệnh
    def log(self, *args):
        """In ra Terminal của app."""
        self.win.terminal.appendPlainText(" ".join(str(a) for a in args))

    def run(self, command, cwd=None, on_done=None, label=None):
        """Chạy lệnh ngoài (list hoặc chuỗi) trong Terminal, có stdin/Dừng."""
        args = list(command) if isinstance(command, (list, tuple)) else \
            shlex.split(command, posix=(os.name != "nt"))
        if not args:
            return
        prog = shutil.which(args[0]) or args[0]
        self.win.terminal.run_queue(
            [(label or os.path.basename(args[0]), prog, args[1:])],
            on_done=on_done, on_step=self.win._on_step, on_fail=self.win._on_fail,
            cwd=cwd or self.project_root())

    def python(self, *args, cwd=None, on_done=None):
        """Chạy `python <args>` bằng đúng Python mà app dùng. vd api.python('-m','pip','list')"""
        py = get_python_command()
        if py is None:
            self.error("Không tìm thấy Python trên máy này.")
            return
        self.win.terminal.run_queue(
            [("python " + " ".join(args[:3]), py[0], py[1:] + list(args))],
            on_done=on_done, on_step=self.win._on_step, on_fail=self.win._on_fail,
            cwd=cwd or self.project_root())

    def capture(self, command, timeout=60, cwd=None):
        """Chạy lệnh và chờ xong. Trả về (mã thoát, stdout, stderr)."""
        args = list(command) if isinstance(command, (list, tuple)) else \
            shlex.split(command, posix=(os.name != "nt"))
        return run_capture(args, timeout=timeout, cwd=cwd)

    #  mạng
    def download(self, url, dest=None, on_done=None, on_error=None):
        """Tải file ở nền (không đơ app). Link GitHub blob/repo được tự đổi cho đúng.
        on_done(đường_dẫn) / on_error(thông_báo) chạy ở luồng giao diện."""
        dest = dest or os.path.join(self.project_root(), suggest_filename(url))
        t = DownloadThread(normalize_download_url(url), dest)
        self.win._threads.append(t)

        def finish(cb, arg):
            if t in self.win._threads:
                self.win._threads.remove(t)
            if cb:
                self._safe(cb, arg)

        t.done.connect(lambda p: finish(on_done, p))
        t.failed.connect(lambda e: finish(on_error or (lambda m: self.log("Tải lỗi:", m)), e))
        t.start()
        return t

    def http_get(self, url, timeout=15):
        """Gửi GET (chỉ http/https) và trả về nội dung dạng chuỗi (chặn đến khi xong)."""
        require_http(url)
        req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return decode_output(r.read())

    def ports(self):
        """Danh sách cổng serial: [(tên, mô tả, nghi_là_ESP)]."""
        return list_serial_ports()

    #  đa ngôn ngữ / hình ảnh
    def has_tool(self, lang):
        """True nếu máy có trình biên dịch/chạy cho `lang` (python, c, cpp, go, java, javascript, rust)."""
        return polyglot_available(lang)

    def run_code(self, lang, source, stdin="", args=(), timeout=60, files=None):
        """Biên dịch + chạy `source` bằng ngôn ngữ `lang`, chờ xong. Trả về (mã thoát, stdout, stderr).
        files={'util.h': '...', 'util.c': '...'} = file phụ cùng thư mục (header, module).
        Chạy ở luồng hiện tại - với việc nặng hãy dùng run_code_async."""
        return run_polyglot(lang, source, stdin, args, timeout, files)

    def run_code_async(self, lang, source, callback, stdin="", args=(), timeout=60, files=None):
        """Như run_code nhưng chạy ở nền; callback((mã, stdout, stderr)) chạy ở luồng giao diện."""
        t = FuncThread(run_polyglot, lang, source, stdin, tuple(args), timeout, files)
        self.win._threads.append(t)

        def fin(res):
            if t in self.win._threads:
                self.win._threads.remove(t)
            self._safe(callback, res)
        t.done.connect(fin)
        t.start()
        return t

    def outline(self, text=None, lang=None):
        """Danh sách hàm/class: [(số_dòng, tên)] (số dòng bắt đầu từ 1)."""
        text = self.text() if text is None else text
        lang = lang or self.language()
        out = []
        for n, line in enumerate(text.split("\n"), 1):
            m = OUTLINE_GENERIC.match(line)
            if not m and lang in ("c", "cpp", "java", "arduino") and not line.rstrip().endswith(";"):
                m = OUTLINE_CFUNC.match(line)
                if m and m.group(1) in OUTLINE_SKIP:
                    m = None
            if m:
                out.append((n, m.group(1)))
        return out

    def code_to_image(self, code, lang=None, theme=None, title="", chrome=True,
                      line_numbers=True, scale=2.0):
        """Vẽ `code` thành QImage (tô màu cú pháp theo theme)."""
        return render_code_to_image(code, lang, theme or self.win.theme_name, title,
                                    self.win.font_size, scale, line_numbers, chrome)

    def copy_image(self, image):
        """Chép QImage vào clipboard."""
        QApplication.clipboard().setImage(image)

    def open_folder(self, path):
        """Mở thư mục chứa `path` bằng trình quản lý file của hệ điều hành."""
        d = path if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))

    #  hiển thị dữ liệu
    #  API v2.0
    @property
    def api_version(self):
        """Phiên bản API plugin (hiện là 2.0)."""
        return API_VERSION

    def send_input(self, text):
        """Gửi một dòng vào stdin của chương trình đang chạy. Trả về True nếu gửi được."""
        return self.win.terminal.send_input(str(text))

    def is_running(self):
        """True nếu Terminal đang chạy một tiến trình."""
        p = self.win.terminal.process
        return p is not None and p.state() != QProcess.NotRunning

    def run_file(self):
        """Chạy tab hiện tại (như bấm F5)."""
        self.win.run_current_file()

    def add_explorer_action(self, text, callback):
        """Thêm mục vào menu chuột phải của Explorer. callback(đường_dẫn_file_hoặc_thư_mục)."""
        item = (text, lambda p: self._safe(callback, p))
        self.win._explorer_actions.append(item)
        self._owned.append(("explorer", item, None))

    def add_keybinding(self, sequence, callback):
        """Gán phím tắt toàn cửa sổ, vd api.add_keybinding('Ctrl+Alt+K', fn). Tự gỡ khi plugin bị gỡ."""
        sc = QShortcut(QKeySequence(sequence), self.win)
        sc.activated.connect(lambda: self._safe(callback))
        self._owned.append(("shortcut", sc, None))
        return sc

    def run_with_args(self, args=""):
        """Chạy tab hiện tại với tham số dòng lệnh `args` (chuỗi), vd api.run_with_args('-v input.txt')."""
        self.win.run_with_args(args)

    def last_output(self):
        """Phần cuối output của Terminal (tối đa ~30000 ký tự, đã bỏ mã màu)."""
        return self.win.terminal.last_output

    def send_eof(self):
        """Đóng stdin của chương trình đang chạy (EOF)."""
        self.win.terminal.send_eof()

    def theme_name(self):
        """Khóa theme hiện tại."""
        return self.win.theme_name

    def recent_files(self):
        """Danh sách file mở gần đây."""
        try:
            lst = json.loads(self.win.settings.value("recent/files", "[]") or "[]")
        except (ValueError, TypeError):
            lst = []
        return [p for p in lst if os.path.isfile(p)]

    def bookmarks(self):
        """Danh sách dòng có bookmark ở tab hiện tại (từ 1)."""
        ed = self.editor
        return sorted({c.blockNumber() + 1 for c in ed.bookmarks}) if ed else []

    def toggle_bookmark(self, line=None):
        """Bật/tắt bookmark ở dòng `line` (từ 1; bỏ trống = dòng hiện tại)."""
        ed = self.editor
        if ed:
            ed.toggle_bookmark(None if line is None else line - 1)

    def fold_all(self):
        """Gập mọi vùng code ở tab hiện tại."""
        ed = self.editor
        if ed:
            ed.fold_all()

    def unfold_all(self):
        """Mở mọi vùng code đã gập."""
        ed = self.editor
        if ed:
            ed.unfold_all()

    def undo(self):
        """Hoàn tác ở tab hiện tại."""
        ed = self.editor
        if ed:
            ed.undo()

    def redo(self):
        """Làm lại ở tab hiện tại."""
        ed = self.editor
        if ed:
            ed.redo()

    def format_code(self):
        """Định dạng code tab hiện tại (black / JSON)."""
        self.win.format_code()

    def json_view(self, data, title="JSON"):
        """Hiện dữ liệu (object hoặc chuỗi JSON) dạng cây gấp được."""
        if isinstance(data, (str, bytes)):
            data = json.loads(data)
        d = JsonTreeDialog(self.win, data, title)
        d.setAttribute(Qt.WA_DeleteOnClose)
        d.show()
        return d

    def table(self, data, title="Bảng"):
        """Hiện bảng từ list-of-dict / list-of-list / dict-of-list."""
        header, rows = table_from_data(data)
        d = TableDialog(self.win, header, rows, title)
        d.setAttribute(Qt.WA_DeleteOnClose)
        d.show()
        return d

    #  lưu trữ riêng
    def get(self, key, default=None):
        """Đọc giá trị đã lưu của plugin (JSON)."""
        raw = self.win.settings.value(f"plugins/{self.name}/{key}", None)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return default

    def set(self, key, value):
        """Lưu giá trị (phải là kiểu JSON được) cho plugin."""
        self.win.settings.setValue(f"plugins/{self.name}/{key}", json.dumps(value))


    # ================= API mở rộng
    #  soạn thảo chi tiết
    def cursor(self):
        """Vị trí con trỏ: (dòng, cột), đều bắt đầu từ 1."""
        ed = self.editor
        if not ed:
            return (1, 1)
        c = ed.textCursor()
        return (c.blockNumber() + 1, c.positionInBlock() + 1)

    def set_cursor(self, line, col=1):
        """Đặt con trỏ tại (dòng, cột) và cuộn tới đó."""
        ed = self.editor
        if not ed:
            return
        b = ed.document().findBlockByNumber(max(0, line - 1))
        if not b.isValid():
            b = ed.document().lastBlock()
        c = QTextCursor(b)
        c.setPosition(b.position() + max(0, min(col - 1, len(b.text()))))
        ed.setTextCursor(c)
        ed.centerCursor()

    def cursor_offset(self):
        """Vị trí con trỏ theo số ký tự từ đầu file."""
        ed = self.editor
        return ed.textCursor().position() if ed else 0

    def select_range(self, start, end):
        """Chọn đoạn theo số ký tự [start, end)."""
        ed = self.editor
        if not ed:
            return
        c = QTextCursor(ed.document())
        c.setPosition(max(0, start))
        c.setPosition(max(0, end), QTextCursor.KeepAnchor)
        ed.setTextCursor(c)

    def line(self, n=None):
        """Nội dung dòng n (từ 1); bỏ trống = dòng hiện tại."""
        ed = self.editor
        if not ed:
            return ""
        b = ed.textCursor().block() if n is None else ed.document().findBlockByNumber(n - 1)
        return b.text() if b.isValid() else ""

    def line_count(self):
        """Số dòng của tab hiện tại."""
        ed = self.editor
        return ed.blockCount() if ed else 0

    def word_at_cursor(self):
        """Từ đang nằm dưới con trỏ (chuỗi rỗng nếu không có)."""
        ed = self.editor
        if not ed:
            return ""
        c = ed.textCursor()
        c.select(QTextCursor.WordUnderCursor)
        return c.selectedText()

    def insert_snippet(self, template):
        """Chèn mẫu có $0 (vị trí con trỏ sau khi chèn), tự thụt lề theo dòng hiện tại."""
        ed = self.editor
        if not ed:
            return
        cur = ed.textCursor()
        line = cur.block().text()
        indent = line[:len(line) - len(line.lstrip(" \t"))]
        text = template.replace("\n", "\n" + indent)
        pos = text.find("$0")
        text = text.replace("$0", "")
        start = cur.selectionStart()
        cur.insertText(text)
        nc = QTextCursor(ed.document())
        nc.setPosition(start + (pos if pos >= 0 else len(text)))
        ed.setTextCursor(nc)

    def find_all(self, pattern, regex=False, case=False):
        """Tìm trong tab hiện tại. Trả về [(dòng, cột, đoạn_khớp)] (dòng/cột từ 1)."""
        flags = 0 if case else re.IGNORECASE
        rx = re.compile(pattern if regex else re.escape(pattern), flags)
        out = []
        for n, ln in enumerate(self.text().split("\n"), 1):
            for m in rx.finditer(ln):
                out.append((n, m.start() + 1, m.group(0)))
        return out

    def replace_all(self, old, new, regex=False, case=False):
        """Thay mọi chỗ khớp trong tab hiện tại. Trả về số chỗ đã thay."""
        flags = 0 if case else re.IGNORECASE
        rx = re.compile(old if regex else re.escape(old), flags)
        text, n = rx.subn(new if regex else new.replace("\\", "\\\\"), self.text())
        if n:
            self.set_text(text)
        return n

    #  tab
    def tabs(self):
        """Danh sách tab: [{'index','title','path','lang','modified'}]."""
        out = []
        for i in range(self.win.tabs.count()):
            ed = self.win.tabs.widget(i)
            out.append({"index": i, "title": self.win.tabs.tabText(i), "path": ed.file_path,
                        "lang": ed.lang, "modified": ed.document().isModified()})
        return out

    def tab_text(self, index):
        """Toàn bộ nội dung của tab số `index` (từ 0)."""
        ed = self.win.tabs.widget(index)
        return ed.toPlainText() if ed else ""

    def switch_tab(self, index):
        """Chuyển sang tab số `index` (từ 0)."""
        if 0 <= index < self.win.tabs.count():
            self.win.tabs.setCurrentIndex(index)

    def close_tab(self, index=None):
        """Đóng tab (mặc định tab hiện tại; có hỏi lưu nếu chưa lưu)."""
        self.win.close_tab(self.win.tabs.currentIndex() if index is None else index)

    def set_language(self, lang):
        """Đổi ngôn ngữ (tô màu) của tab hiện tại."""
        ed = self.editor
        if ed:
            ed.set_language(lang)
            self.win.update_status()

    #  file / hệ thống
    def read_file(self, path):
        """Đọc file văn bản (tự đoán encoding) và trả về chuỗi."""
        r = read_text_file(path)
        if r is None:
            raise ValueError("Đây là file nhị phân, không đọc được dạng văn bản: " + path)
        return r

    def write_file(self, path, text, make_dirs=True):
        """Ghi chuỗi ra file UTF-8 (LF). Trả về path."""
        d = os.path.dirname(os.path.abspath(path))
        if make_dirs:
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return path

    def clipboard(self):
        """Nội dung chữ trong clipboard."""
        return QApplication.clipboard().text()

    def open_url(self, url):
        """Mở link http/https bằng trình duyệt mặc định."""
        require_http(url)
        QDesktopServices.openUrl(QUrl(url))

    def stop(self):
        """Dừng tiến trình đang chạy trong Terminal."""
        self.win.stop_process()

    def clear_terminal(self):
        """Xóa Terminal."""
        self.win.terminal.output.clear()

    #  hộp thoại / hiển thị
    def show_text(self, title, text, monospace=True):
        """Hiện cửa sổ chỉ đọc chứa văn bản dài (có chọn / chép)."""
        dlg = QDialog(self.win)
        dlg.setWindowTitle(title)
        dlg.resize(720, 520)
        v = QVBoxLayout(dlg)
        te = QPlainTextEdit()
        te.setReadOnly(True)
        te.setPlainText(str(text))
        if monospace:
            te.setFont(pick_font(self.win.font_size))
        v.addWidget(te)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(dlg.reject)
        bb.accepted.connect(dlg.accept)
        v.addWidget(bb)
        dlg.show()
        self.win._threads_dialogs = getattr(self.win, "_threads_dialogs", [])
        self.win._threads_dialogs.append(dlg)
        dlg.finished.connect(lambda _=0, d=dlg: self.win._threads_dialogs.remove(d)
                             if d in self.win._threads_dialogs else None)
        return dlg

    def show_image(self, image, title="Ảnh"):
        """Hiện QImage / QPixmap / đường dẫn ảnh trong cửa sổ có thanh cuộn."""
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtWidgets import QScrollArea
        if isinstance(image, str):
            pm = QPixmap(image)
        elif isinstance(image, QImage):
            pm = QPixmap.fromImage(image)
        else:
            pm = image
        dlg = QDialog(self.win)
        dlg.setWindowTitle(title)
        dlg.resize(min(1000, pm.width() + 40), min(760, pm.height() + 40))
        v = QVBoxLayout(dlg)
        lab = QLabel()
        lab.setPixmap(pm)
        sa = QScrollArea()
        sa.setWidget(lab)
        v.addWidget(sa)
        dlg.show()
        self.win._threads_dialogs = getattr(self.win, "_threads_dialogs", [])
        self.win._threads_dialogs.append(dlg)
        dlg.finished.connect(lambda _=0, d=dlg: self.win._threads_dialogs.remove(d)
                             if d in self.win._threads_dialogs else None)
        return dlg

    def form(self, title, fields):
        """Hộp nhập nhiều trường. fields = [(khóa, nhãn, kiểu, mặc_định[, lựa_chọn])]
        với kiểu: text | int | float | bool | choice | multiline. Trả về dict hoặc None nếu hủy."""
        dlg = QDialog(self.win)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(420)
        v = QVBoxLayout(dlg)
        fl = QFormLayout()
        widgets = {}
        for f in fields:
            key, label, kind, default = f[:4]
            opts = f[4] if len(f) > 4 else []
            if kind == "int":
                w = QSpinBox()
                w.setRange(-2 ** 31, 2 ** 31 - 1)
                w.setValue(int(default or 0))
            elif kind == "float":
                from PyQt5.QtWidgets import QDoubleSpinBox
                w = QDoubleSpinBox()
                w.setRange(-1e12, 1e12)
                w.setDecimals(4)
                w.setValue(float(default or 0))
            elif kind == "bool":
                w = QCheckBox()
                w.setChecked(bool(default))
            elif kind == "choice":
                w = QComboBox()
                w.addItems([str(o) for o in opts])
                if default in opts:
                    w.setCurrentIndex(list(opts).index(default))
            elif kind == "multiline":
                w = QPlainTextEdit(str(default or ""))
                w.setFixedHeight(110)
            else:
                w = QLineEdit(str(default or ""))
            widgets[key] = (kind, w)
            fl.addRow(label, w)
        v.addLayout(fl)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        v.addWidget(bb)
        if dlg.exec_() != QDialog.Accepted:
            return None
        out = {}
        for key, (kind, w) in widgets.items():
            out[key] = (w.value() if kind in ("int", "float") else w.isChecked() if kind == "bool"
                        else w.currentText() if kind == "choice"
                        else w.toPlainText() if kind == "multiline" else w.text())
        return out

    def progress(self, text=None, value=None, maximum=100):
        """Thanh tiến trình của app. progress('Đang xử lý') = đang chạy (không rõ %);
        progress('Xong', 50, 100) = 50%; progress() = trả về 'Sẵn sàng'."""
        p = self.win.progress
        if text is None:
            p.setRange(0, 1)
            p.setValue(0)
            p.setFormat("Sẵn sàng")
        elif value is None:
            p.setRange(0, 0)
            p.setFormat(str(text))
        else:
            p.setRange(0, max(1, maximum))
            p.setValue(max(0, min(value, maximum)))
            p.setFormat(f"{text} ({value}/{maximum})")

    def notify(self, text, ms=5000):
        """Báo ngắn ở thanh trạng thái và ghi vào Terminal."""
        self.status(text, ms)
        self.log(f"[{self.name}] {text}")

    #  nền / hẹn giờ
    def timer(self, ms, callback, repeat=True):
        """Gọi callback() mỗi `ms` mili-giây (repeat=False: chỉ một lần). Tự dừng khi plugin bị gỡ."""
        t = QTimer(self.win)
        t.setSingleShot(not repeat)
        t.timeout.connect(lambda: self._safe(callback))
        t.start(ms)
        self._owned.append(("timer", t, None))
        return t

    def run_async(self, fn, callback=None, *args):
        """Chạy fn(*args) ở luồng nền (không đơ app); callback(kết_quả) chạy ở luồng giao diện.
        Nếu fn báo lỗi, kết quả là (-1, '', 'Tên lỗi: ...')."""
        t = FuncThread(fn, *args)
        self.win._threads.append(t)

        def fin(res):
            if t in self.win._threads:
                self.win._threads.remove(t)
            if callback:
                self._safe(callback, res)
        t.done.connect(fin)
        t.start()
        return t

    #  mở rộng giao diện
    def add_context_action(self, text, callback):
        """Thêm mục vào menu chuột phải của editor."""
        item = (text, lambda: self._safe(callback))
        self.win._context_actions.append(item)
        self._owned.append(("context", item, None))

    def add_statusbar_widget(self, widget):
        """Thêm widget (QLabel, nút...) vào thanh trạng thái, bên phải."""
        self.win.statusBar().addPermanentWidget(widget)
        self._owned.append(("statusw", widget, None))
        return widget

    def add_lint_provider(self, fn):
        """Đăng ký bộ kiểm tra lỗi cho mọi ngôn ngữ. fn(text, lang, path) trả về
        [(dòng, thông_báo)] (hoặc [{'line','message'}]). Lỗi hiện gạch vàng + chấm ở lề.
        fn chạy ở luồng giao diện sau khi ngừng gõ ~0,7s nên phải nhanh."""
        self.win._lint_providers.append(fn)
        self._owned.append(("lint", fn, None))
        for i in range(self.win.tabs.count()):
            self.win.tabs.widget(i)._lint_timer.start(50)

    def add_theme(self, key, colors, label=None, base="dark"):
        """Thêm theme mới: colors là dict ghi đè lên theme `base` (bg, fg, keyword, string,
        comment, number, func, line_bg, gutter_bg, gutter_fg, accent, ...)."""
        if key in THEMES:
            raise ValueError(f"Theme '{key}' đã tồn tại")
        t = dict(THEMES[base])
        t.update(colors)
        t["label"] = label or key
        THEMES[key] = t
        a = QAction(t["label"], self.win)
        a.setCheckable(True)
        a.setActionGroup(self.win._theme_group)
        a.triggered.connect(lambda _=False, k=key: self.win.set_theme(k))
        self.win._theme_menu.addAction(a)
        self.win._theme_actions[a] = key
        self._owned.append(("theme", (key, a), None))

    def set_theme(self, name):
        """Chuyển theme (dark, light, than_dem, bien_dem, tim_huyen, bang_gia hoặc theme plugin thêm)."""
        self.win.set_theme(name)

    def add_language(self, key, label, exts, line_comment="#", block_comment=False,
                     keywords=(), triple=(), backtick=False, preproc=False, brace=True,
                     indent="    ", run=None, need=()):
        """Đăng ký ngôn ngữ mới: tô màu, comment, mở file theo đuôi và (tuỳ chọn) chạy bằng F5.
        run = [(nhãn, chương_trình, [tham_số])] với {file} {dir} {base} {exe}, ví dụ
        run=[('Chạy', 'ruby', ['{file}'])]. Biên dịch: [('Build','gcc',['{file}','-o','{exe}']),
        ('Chạy','{exe}',[])]."""
        exts = [e if e.startswith(".") else "." + e for e in exts]
        snap = {"key": key, "exts": exts, "prev": {
            "cfg": LANG_CFG.get(key), "kw": KEYWORDS.get(key), "label": LANGUAGE_LABELS.get(key),
            "ext": LANG_EXT.get(key), "run": RUN_TEMPLATES.get(key), "runnable": key in RUNNABLE,
            "map": {e: EXT_TO_LANG.get(e) for e in exts},
            "text": {e: e in TEXT_EXTS for e in exts}}}
        for e in exts:
            EXT_TO_LANG[e] = key
            TEXT_EXTS.add(e)
        LANGUAGE_LABELS[key] = label
        LANG_EXT[key] = exts[0]
        LANG_CFG[key] = dict(line=line_comment, block=block_comment, triple=tuple(triple),
                             backtick=backtick, preproc=preproc, brace=brace, indent=indent)
        KEYWORDS[key] = list(keywords)
        if run:
            RUN_TEMPLATES[key] = {"steps": [tuple(s) for s in run], "need": list(need)}
            RUNNABLE.add(key)
        self._owned.append(("language", snap, None))
        for i in range(self.win.tabs.count()):
            ed = self.win.tabs.widget(i)
            if ed.lang == key:
                ed.highlighter._build()
                ed.highlighter.rehighlight()

    def _restore_language(self, snap):
        key, prev = snap["key"], snap["prev"]

        def put(d, v):
            if v is None:
                d.pop(key, None)
            else:
                d[key] = v
        put(LANG_CFG, prev["cfg"])
        put(KEYWORDS, prev["kw"])
        put(LANGUAGE_LABELS, prev["label"])
        put(LANG_EXT, prev["ext"])
        put(RUN_TEMPLATES, prev["run"])
        if not prev["runnable"]:
            RUNNABLE.discard(key)
        for e in snap["exts"]:
            if prev["map"][e] is None:
                EXT_TO_LANG.pop(e, None)
            else:
                EXT_TO_LANG[e] = prev["map"][e]
            if not prev["text"][e]:
                TEXT_EXTS.discard(e)

    #  C / panel web
    def load_c(self, code, flags=(), cpp=False):
        """Biên dịch code C/C++ thành thư viện dùng chung và trả về ctypes.CDLL (có cache).
        Cẩn thận: chạy cùng tiến trình với app."""
        return build_c_library(code, flags, cpp)

    def call_c(self, code, func, args=(), restype="int", argtypes=None, flags=(), cpp=False):
        """Gọi hàm C trực tiếp: api.call_c(src, 'add', [1, 2]) -> (3, []).
        Kiểu: int, uint, long, size_t, float, double, bool, str, ptr, void và 'double[]', 'int[]'.
        Trả về (giá_trị, [các mảng sau khi gọi])."""
        return call_c_function(code, func, args, restype, argtypes, flags, cpp)

    def add_dock_webview(self, title, html="", area="right"):
        """Thêm panel hiển thị HTML. Dùng QtWebEngine nếu có (chạy được JS/WebGL), nếu không
        thì QTextBrowser (HTML đơn giản). Trả về (dock, view); view.setHtml(...) để cập nhật."""
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
            view = QWebEngineView()
        except Exception:  # noqa: BLE001
            from PyQt5.QtWidgets import QTextBrowser
            view = QTextBrowser()
            view.setOpenExternalLinks(True)
        view.setHtml(html)
        return self.add_dock(title, view, area), view


SAMPLE_PLUGIN = '''# Plugin mẫu cho GKcode - lưu trong ~/.pyapp/plugins/hello.py
# Sau khi sửa: menu Plugins > Tải lại plugins

# (tuỳ chọn) thông tin hiện trong Plugins > Quản lý plugin
PLUGIN = {"name": "Hello", "version": "1.0", "author": "Bạn", "description": "Plugin mẫu: chữ HOA, chào, snippet."}


def register(api):
    def upper_selection():
        sel = api.selection()
        if sel:
            api.replace_selection(sel.upper())
        else:
            api.status("Hãy chọn đoạn text trước")

    api.add_action("Chữ HOA đoạn chọn", upper_selection, shortcut="Ctrl+Alt+U")
    api.add_action("Xin chào", lambda: api.message("Xin chào từ plugin!"))
    api.add_toolbar_button("Hi", lambda: api.log("Hi từ plugin"))
    api.add_snippet("python", "pmain", 'def main():\\n    $0\\n')
    api.on("save", lambda ed: api.status(f"Đã lưu {ed.file_path}"))


def unregister(api):
    pass   # (không bắt buộc) dọn dẹp thêm khi tải lại / tắt plugin
'''


def api_reference_text():
    lines = [f"# API của {APP_NAME} v{APP_VERSION}", "",
             (PyAppAPI.__doc__ or "").strip(), "", "## Các hàm / thuộc tính", ""]
    for name, member in inspect.getmembers(PyAppAPI):
        if name.startswith("_"):
            continue
        doc = (inspect.getdoc(member) or "").split("\n")[0]
        if isinstance(member, property):
            lines.append(f"- api.{name}   (thuộc tính)  - {doc}")
        elif callable(member):
            sig = str(inspect.signature(member)).replace("(self, ", "(").replace("(self)", "()")
            lines.append(f"- api.{name}{sig}  - {doc}")
    lines += ["", "## Sự kiện cho api.on(event, callback)", "",
              "- start: app khởi động xong", "- open(editor): vừa mở file",
              "- save(editor): vừa lưu file", "- run(editor): vừa chạy chương trình",
              "- run_done(editor): chương trình chạy xong thành công",
              "- output(text): Terminal vừa nhận thêm output",
              "- quit: app sắp đóng", "",
              "## Ví dụ plugin", "", SAMPLE_PLUGIN]
    return "\n".join(lines)


# Tính toán an toàn + Công cụ văn bản dựng sẵn (viết bằng chính API ở trên)
_MAX_BITS = 20000          # kết quả số nguyên tối đa ~6000 chữ số
_MAX_EXPR_LEN = 1000
