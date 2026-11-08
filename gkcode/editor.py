# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


# Syntax highlighter (quét từng ký tự: đúng với chuỗi / comment nhiều dòng)
KEYWORDS = {
    "python": [
        "and", "as", "assert", "async", "await", "break", "class", "continue",
        "def", "del", "elif", "else", "except", "finally", "for", "from",
        "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or",
        "pass", "raise", "return", "try", "while", "with", "yield", "None",
        "True", "False", "self", "match", "case", "print", "len", "range",
        "int", "str", "float", "list", "dict", "set", "tuple", "bool",
    ],
    "c": [
        "auto", "break", "case", "char", "const", "continue", "default", "do",
        "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "inline", "int", "long", "register", "return", "short", "signed",
        "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned",
        "void", "volatile", "while", "NULL", "uint8_t", "uint16_t", "uint32_t",
        "int8_t", "int16_t", "int32_t", "size_t", "bool", "true", "false",
    ],
    "cpp": [
        "alignas", "auto", "bool", "break", "case", "catch", "char", "class",
        "const", "constexpr", "continue", "default", "delete", "do", "double",
        "else", "enum", "explicit", "extern", "false", "float", "for", "friend",
        "if", "inline", "int", "long", "namespace", "new", "noexcept", "nullptr",
        "operator", "override", "private", "protected", "public", "return",
        "short", "signed", "sizeof", "static", "struct", "switch", "template",
        "this", "throw", "true", "try", "typedef", "typename", "union",
        "unsigned", "using", "virtual", "void", "volatile", "while", "std",
        "string", "vector", "uint8_t", "uint16_t", "uint32_t", "size_t",
    ],
    "go": [
        "break", "case", "chan", "const", "continue", "default", "defer", "else",
        "fallthrough", "for", "func", "go", "goto", "if", "import", "interface",
        "map", "package", "range", "return", "select", "struct", "switch",
        "type", "var", "true", "false", "nil", "int", "string", "bool",
        "float64", "byte", "error", "make", "len", "append",
    ],
    "java": [
        "abstract", "boolean", "break", "byte", "case", "catch", "char", "class",
        "const", "continue", "default", "do", "double", "else", "enum",
        "extends", "final", "finally", "float", "for", "if", "implements",
        "import", "instanceof", "int", "interface", "long", "new", "package",
        "private", "protected", "public", "return", "short", "static", "super",
        "switch", "synchronized", "this", "throw", "throws", "try", "void",
        "volatile", "while", "true", "false", "null", "String", "var",
    ],
    "javascript": [
        "async", "await", "break", "case", "catch", "class", "const",
        "continue", "debugger", "default", "delete", "do", "else", "export",
        "extends", "finally", "for", "function", "if", "import", "in",
        "instanceof", "let", "new", "of", "return", "super", "switch", "this",
        "throw", "try", "typeof", "var", "void", "while", "with", "yield",
        "true", "false", "null", "undefined", "console", "require",
    ],
    "json": ["true", "false", "null"],
}

_C_LIKE = dict(line="//", block=True, triple=(), backtick=False, preproc=False,
               brace=True, indent="    ")
LANG_CFG = {
    "python": dict(line="#", block=False, triple=('"""', "'''"), backtick=False,
                   preproc=False, brace=False, indent="    "),
    "c": dict(_C_LIKE, preproc=True),
    "cpp": dict(_C_LIKE, preproc=True),
    "go": dict(_C_LIKE, backtick=True, indent="\t"),
    "java": dict(_C_LIKE, triple=('"""',)),
    "javascript": dict(_C_LIKE, backtick=True),
    "json": dict(line=None, block=False, triple=(), backtick=False,
                 preproc=False, brace=True, indent="  "),
}

KEYWORDS["arduino"] = list(dict.fromkeys(KEYWORDS["cpp"] + [
    "setup", "loop", "pinMode", "digitalWrite", "digitalRead", "analogRead", "analogWrite",
    "delay", "delayMicroseconds", "millis", "micros", "Serial", "Wire", "SPI", "WiFi",
    "HIGH", "LOW", "INPUT", "OUTPUT", "INPUT_PULLUP", "LED_BUILTIN", "byte", "boolean",
    "String", "word", "attachInterrupt", "detachInterrupt", "constrain", "random",
    "randomSeed", "tone", "noTone", "pulseIn", "shiftIn", "shiftOut", "int8_t", "int16_t",
    "int32_t", "int64_t", "uint64_t",
]))
LANG_CFG["arduino"] = dict(_C_LIKE, preproc=True)

# trạng thái block: id -> (chuỗi kết thúc, loại format)
ML_STATES = {1: ('"""', "string"), 2: ("'''", "string"),
             3: ("*/", "comment"), 4: ("`", "string"), 5: ("-->", "comment")}
MAX_HL_LINE = 4000          # dòng dài hơn mức này chỉ tô tối thiểu (tránh đơ với file minify / dữ liệu)


class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme, lang="python"):
        super().__init__(document)
        self.theme = theme
        self.lang = lang
        self._build()

    def _build(self):
        t = self.theme

        def fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Bold)
            f.setFontItalic(italic)
            return f

        self.f_kw = fmt(t["keyword"], bold=True)
        self.f_str = fmt(t["string"])
        self.f_cm = fmt(t["comment"], italic=True)
        self.f_num = fmt(t["number"])
        self.f_func = fmt(t["func"])
        self.cfg = LANG_CFG.get(self.lang)
        kws = KEYWORDS.get(self.lang, [])
        self.kw_re = QRegExp(r"\b(?:%s)\b" % "|".join(kws)) if kws else None
        self.num_re = QRegExp(
            r"\b(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b")
        self.func_re = QRegExp(r"\b[A-Za-z_]\w*(?=\s*\()")
        self.def_re = QRegExp(
            r"\b(?:def|class|func|function|fn|fun|struct|interface|enum|trait|namespace|record)\s+([A-Za-z_]\w*)")
        self.tag_re = QRegExp(r"</?[A-Za-z][\w:.-]*|/?>")
        self.attr_re = QRegExp(r"\b([A-Za-z_:@][\w:.-]*)(?==)")
        self.css_prop_re = QRegExp(r"[A-Za-z-]+(?=\s*:)")
        self.css_sel_re = QRegExp(r"[.#][A-Za-z_][\w-]*")
        self.css_hex_re = QRegExp(r"#[0-9a-fA-F]{3,8}\b")
        self.deco_re = QRegExp(r"^\s*@\w+(?:\.\w+)*")
        self.pre_re = QRegExp(r"^\s*#\s*\w+")

    def set_theme(self, theme):
        self.theme = theme
        self._build()
        self.rehighlight()

    def set_language(self, lang):
        if lang == self.lang:
            return
        self.lang = lang
        self._build()
        self.rehighlight()

    def _apply(self, rx, fmt, text, group=0):
        idx = rx.indexIn(text)
        while idx >= 0:
            length = rx.matchedLength()
            if length == 0:
                break
            if group:
                self.setFormat(rx.pos(group), len(rx.cap(group)), fmt)
            else:
                self.setFormat(idx, length, fmt)
            idx = rx.indexIn(text, idx + length)

    def highlightBlock(self, text):
        cfg = self.cfg
        if cfg is None:
            self.setCurrentBlockState(0)
            return

        if len(text) > MAX_HL_LINE:          # dòng quá dài: bỏ tô màu, giữ nguyên trạng thái block
            self.setCurrentBlockState(max(self.previousBlockState(), 0))
            return

        #  quy tắc regex (từ khóa, số, tên hàm)
        if cfg.get("markup"):
            self._apply(self.tag_re, self.f_kw, text)
            self._apply(self.attr_re, self.f_func, text, group=1)
        elif cfg.get("css"):
            self._apply(self.css_sel_re, self.f_func, text)
            self._apply(self.css_prop_re, self.f_kw, text)
            self._apply(self.css_hex_re, self.f_num, text)
        elif self.lang != "json":
            self._apply(self.func_re, self.f_func, text)
            self._apply(self.def_re, self.f_func, text, group=1)
        if self.kw_re is not None:
            self._apply(self.kw_re, self.f_kw, text)
        self._apply(self.num_re, self.f_num, text)
        if self.lang == "python":
            self._apply(self.deco_re, self.f_func, text)
        if cfg["preproc"]:
            self._apply(self.pre_re, self.f_kw, text)

        #  quét chuỗi / comment (ghi đè lên các quy tắc trên)
        fmt_of = {"string": self.f_str, "comment": self.f_cm}
        state = max(self.previousBlockState(), 0)
        i, n = 0, len(text)
        lc = cfg["line"]
        triple = cfg["triple"]
        while i < n:
            if state:
                end_tok, kind = ML_STATES[state]
                j = text.find(end_tok, i)
                if j == -1:
                    self.setFormat(i, n - i, fmt_of[kind])
                    self.setCurrentBlockState(state)
                    return
                self.setFormat(i, j + len(end_tok) - i, fmt_of[kind])
                i = j + len(end_tok)
                state = 0
                continue

            if lc and text.startswith(lc, i):
                self.setFormat(i, n - i, self.f_cm)
                break
            if cfg.get("html_comment") and text.startswith("<!--", i):
                self.setFormat(i, 4, self.f_cm)
                state = 5
                i += 4
                continue
            if cfg["block"] and text.startswith("/*", i):
                self.setFormat(i, 2, self.f_cm)
                state = 3
                i += 2
                continue
            hit = False
            for tok in triple:
                if text.startswith(tok, i):
                    self.setFormat(i, 3, self.f_str)
                    state = 1 if tok == '"""' else 2
                    i += 3
                    hit = True
                    break
            if hit:
                continue
            ch = text[i]
            if cfg["backtick"] and ch == "`":
                self.setFormat(i, 1, self.f_str)
                state = 4
                i += 1
                continue
            if ch in "\"'":
                j = i + 1
                while j < n:
                    if text[j] == "\\":
                        j += 2
                        continue
                    if text[j] == ch:
                        j += 1
                        break
                    j += 1
                j = min(j, n)
                self.setFormat(i, j - i, self.f_str)
                i = j
                continue
            i += 1
        self.setCurrentBlockState(state)


# Code editor
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.editor.gutter_click(event.pos())


OPEN_CLOSE = {"(": ")", "[": "]", "{": "}"}
CLOSERS = set(OPEN_CLOSE.values())
ALL_BRACKETS = set(OPEN_CLOSE) | CLOSERS
CLOSE_TO_OPEN = {v: k for k, v in OPEN_CLOSE.items()}


class Minimap(QWidget):
    """Bản đồ thu nhỏ của file, nằm bên phải editor. Bấm / kéo để cuộn nhanh."""
    WIDTH = 96
    LINE_H = 2

    def __init__(self, editor):
        super().__init__(editor)
        self.ed = editor
        self._cache = None
        self._cache_h = -1
        self._step = 1
        self._dirty = True
        self._drag = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(self.WIDTH)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(160)
        self._timer.timeout.connect(self.update)
        editor.textChanged.connect(self.invalidate)
        editor.verticalScrollBar().valueChanged.connect(lambda _v: self.update())

    def invalidate(self):
        self._dirty = True
        self._timer.start()

    def _rebuild(self):
        doc = self.ed.document()
        n = max(1, doc.blockCount())
        h = max(1, self.height())
        lh = self.LINE_H
        step = max(1, -(-n * lh // h))
        rows = -(-n // step)
        pm = QPixmap(self.WIDTH, max(1, rows * lh))
        pm.fill(Qt.transparent)
        th = self.ed.theme

        def col(key, alpha):
            c = QColor(th[key])
            c.setAlpha(alpha)
            return c

        base, com = col("fg", 140), col("comment", 175)
        fn, kw = col("func", 235), col("keyword", 175)
        run = re.compile(r"\S+")
        p = QPainter(pm)
        for r in range(rows):
            block = doc.findBlockByNumber(r * step)
            if not block.isValid():
                break
            text = block.text().expandtabs(4)[:self.WIDTH - 8]
            st = text.lstrip()
            if not st:
                continue
            if st.startswith(("#include", "import ", "from ", "return ", "if ", "for ",
                              "while ", "elif ", "else")):
                c = kw
            elif st.startswith(("#", "//", "/*", "*", "--", "\'\'\'", '"""')):
                c = com
            elif st.startswith(("def ", "class ", "async def ", "function ", "func ", "fn ")):
                c = fn
            else:
                c = base
            for m in run.finditer(text):
                p.fillRect(4 + m.start(), r * lh, m.end() - m.start(), 1, c)
        p.end()
        self._cache, self._cache_h, self._step = pm, self.height(), step
        self._dirty = False

    def _visible_lines(self):
        return max(1, self.ed.viewport().height() // max(1, self.ed.fontMetrics().lineSpacing()))

    def paintEvent(self, _event):
        if self._dirty or self._cache is None or self._cache_h != self.height():
            self._rebuild()
        p = QPainter(self)
        th = self.ed.theme
        p.fillRect(self.rect(), QColor(th["bg"]))
        p.drawPixmap(0, 0, self._cache)
        first = self.ed.firstVisibleBlock().blockNumber()
        y = int(first / self._step * self.LINE_H)
        hh = max(10, int(self._visible_lines() / self._step * self.LINE_H))
        ac = QColor(th["accent"])
        fill = QColor(ac)
        fill.setAlpha(34)
        p.fillRect(0, y, self.width(), hh, fill)
        edge = QColor(ac)
        edge.setAlpha(110)
        p.setPen(QPen(edge))
        p.drawLine(0, y, self.width(), y)
        p.drawLine(0, y + hh, self.width(), y + hh)
        sep = QColor(th["fg"])
        sep.setAlpha(28)
        p.fillRect(0, 0, 1, self.height(), sep)

    def _scroll_to(self, ypos):
        line = ypos / self.LINE_H * self._step
        self.ed.verticalScrollBar().setValue(int(line - self._visible_lines() / 2))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = True
            self._scroll_to(e.y())

    def mouseMoveEvent(self, e):
        if self._drag:
            self._scroll_to(e.y())

    def mouseReleaseEvent(self, _e):
        self._drag = False

    def wheelEvent(self, e):
        vs = self.ed.verticalScrollBar()
        vs.setValue(vs.value() - e.angleDelta().y() // 40)


class CodeEditor(QPlainTextEdit):
    TOP_MARGIN = 26
    zoomRequested = pyqtSignal(int)
    lintChanged = pyqtSignal()
    large_mode = False           # file lớn: tắt tô màu / minimap / lint để không đơ

    def __init__(self, theme=None, font_size=11, lang="python"):
        super().__init__()
        self.file_path = None
        self.lang = lang
        self.theme = theme or THEMES[DEFAULT_THEME]
        self.search_selections = []
        self.lint_error = None            # (số dòng, thông báo) hoặc None
        self.encoding = "utf-8"
        self.eol = "\n"
        self.breadcrumb = QLabel(self)
        self.breadcrumb.setTextFormat(Qt.RichText)
        self._bc_timer = QTimer(self)
        self._bc_timer.setSingleShot(True)
        self._bc_timer.setInterval(70)
        self._bc_timer.timeout.connect(self.update_breadcrumb)
        self.lint_items = []              # [(dòng, thông báo)] từ lint provider của plugin
        self.tab_size = 4
        self.show_guides = True
        self.folded = []                  # [QTextCursor] đầu các vùng đang gập
        self.bookmarks = []               # [QTextCursor]
        self._fold_timer = QTimer(self)
        self._fold_timer.setSingleShot(True)
        self._fold_timer.timeout.connect(lambda: self._relayout_folds())
        self._lint_timer = QTimer(self)
        self._lint_timer.setSingleShot(True)
        self._lint_timer.setInterval(700)
        self._lint_timer.timeout.connect(self._run_lint)
        self.textChanged.connect(lambda: self._lint_timer.start())
        self.textChanged.connect(self._schedule_fold_refresh)
        self.setAcceptDrops(True)
        self.setFrameShape(QPlainTextEdit.NoFrame)

        self.minimap = None
        self.minimap_on = True
        self._mm_shown = False
        self.line_number_area = LineNumberArea(self)
        self.set_font_size(font_size)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.refresh_selections)
        self.cursorPositionChanged.connect(lambda: self._bc_timer.start())
        self.update_line_number_area_width(0)

        self.highlighter = CodeHighlighter(self.document(), self.theme, lang)
        self.minimap = Minimap(self)
        self.minimap.hide()
        self.verticalScrollBar().rangeChanged.connect(
            lambda *_: QTimer.singleShot(0, self._place_minimap))
        self._place_minimap()

        # autocomplete
        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer_model = QStringListModel(self)
        self.completer.setModel(self._completer_model)
        self.completer.activated[str].connect(self._insert_completion)

        self.apply_theme(self.theme)

    #  cấu hình
    @property
    def cfg(self):
        return LANG_CFG.get(self.lang)

    @property
    def indent_unit(self):
        return self.cfg["indent"] if self.cfg else "    "

    def set_language(self, lang):
        self.lang = lang
        self.highlighter.set_language(lang)
        self._lint_timer.start(50)

    def set_font_size(self, size):
        self.setFont(pick_font(size))
        self.setTabStopDistance(self.tab_size * self.fontMetrics().horizontalAdvance(" "))
        self.update_line_number_area_width(0)
        self.line_number_area.update()

    def apply_theme(self, theme):
        self.theme = theme
        self.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {theme['bg']}; "
            f"color: {theme['fg']}; border: none; "
            f"selection-background-color: {theme['accent']}; "
            f"selection-color: white; }}"
        )
        self.completer.popup().setStyleSheet(
            f"QListView {{ background: {theme['tab_bg']}; color: {theme['tab_fg']}; "
            f"border: 1px solid {theme['accent']}; }} "
            f"QListView::item:selected {{ background: {theme['accent']}; color: white; }}"
        )
        self.highlighter.set_theme(theme)
        pal = ui_palette(theme)
        self.breadcrumb.setStyleSheet(
            f"QLabel {{ background: {theme['bg']}; color: {pal['muted']}; padding: 0 14px; "
            f"border-bottom: 1px solid {pal['border']}; font-size: 9pt; }}")
        self._bc_colors = (pal["muted"], pal["fg"], pal["muted"])
        self.update_breadcrumb()
        self.line_number_area.update()
        self.refresh_selections()
        if self.minimap is not None:
            self.minimap.invalidate()

    #  kéo thả file
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            win = self.window()
            if hasattr(win, "open_path"):
                for url in event.mimeData().urls():
                    win.open_path(url.toLocalFile())
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    #  số dòng
    def line_number_area_width(self):
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 30 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), self.TOP_MARGIN,
                                Minimap.WIDTH if self._mm_shown else 0, 0)

    def set_large_mode(self, on=True):
        """Chế độ file lớn: tắt các tính năng tốn CPU trên toàn tài liệu."""
        self.large_mode = bool(on)
        if on:
            self.highlighter.setDocument(None)
            self._lint_timer.stop()
            self.lint_error, self.lint_items = None, []
            self.setLineWrapMode(QPlainTextEdit.NoWrap)
        else:
            self.highlighter.setDocument(self.document())
        self.set_minimap(self.minimap_on)

    def load_text_chunked(self, text, chunk=400000, on_done=None, on_progress=None):
        """Nạp văn bản lớn từng đợt (mỗi đợt xử lý xong mới trả quyền cho giao diện)."""
        self.setUndoRedoEnabled(False)
        self.setUpdatesEnabled(False)
        self.clear()
        state = {"pos": 0}
        cur = QTextCursor(self.document())

        def step():
            p = state["pos"]
            if p >= len(text):
                self.setUndoRedoEnabled(True)
                self.setUpdatesEnabled(True)
                self.moveCursor(QTextCursor.Start)
                self.document().setModified(False)
                if on_done:
                    on_done()
                return
            end = min(len(text), p + chunk)
            nl = text.find("\n", end)
            end = len(text) if nl < 0 or nl - end > 200000 else nl + 1
            cur.movePosition(QTextCursor.End)
            cur.insertText(text[p:end])
            state["pos"] = end
            if on_progress:
                on_progress(end, len(text))
            QTimer.singleShot(0, step)
        step()

    def set_minimap(self, on):
        self.minimap_on = bool(on) and not self.large_mode
        self._place_minimap()

    def _place_minimap(self):
        mm = self.minimap
        if mm is None:
            return
        want = self.minimap_on and self.width() >= 560
        if want != self._mm_shown:
            self._mm_shown = want
            mm.setVisible(want)
            self.update_line_number_area_width(0)
        if want:
            vp = self.viewport().geometry()
            mm.setGeometry(vp.right() + 1, vp.top(), Minimap.WIDTH, vp.height())
            mm.raise_()

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top() + self.TOP_MARGIN, self.line_number_area_width(),
                  max(0, cr.height() - self.TOP_MARGIN)))
        self.breadcrumb.setGeometry(QRect(cr.left(), cr.top(), cr.width(), self.TOP_MARGIN))
        self._place_minimap()

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(self.theme["gutter_bg"]))
        _sep = QColor(self.theme.get("border") or self.theme["gutter_fg"])
        painter.setPen(_sep)
        painter.drawLine(self.line_number_area.width() - 1, event.rect().top(),
                         self.line_number_area.width() - 1, event.rect().bottom())
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        current = self.textCursor().blockNumber()
        dim = QColor(self.theme["gutter_fg"])
        bm = {c.blockNumber() for c in self.bookmarks}
        fo = self._folded_numbers()
        lint_lines = {ln for ln, _m in self.lint_items}
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if number == current:
                    painter.fillRect(QRect(0, int(top), self.line_number_area.width() - 1,
                                           int(bottom - top)), QColor(self.theme["line_bg"]))
                    painter.fillRect(QRect(0, int(top), 2, int(bottom - top)), QColor(self.theme["accent"]))
                    painter.setPen(QColor(self.theme["accent"]))
                else:
                    painter.setPen(dim)
                painter.drawText(
                    0, int(top), self.line_number_area.width() - 20,
                    self.fontMetrics().height(), Qt.AlignRight, str(number + 1))
                if number in bm:
                    painter.fillRect(QRect(0, int(top) + 1, 4, self.fontMetrics().height() - 2),
                                     QColor(self.theme["accent"]))
                if self.is_foldable(block):
                    painter.setPen(dim)
                    painter.drawText(
                        self.line_number_area.width() - 16, int(top), 14,
                        self.fontMetrics().height(), Qt.AlignCenter,
                        "▸" if number in fo else "▾")
                if self.lint_error and number + 1 == self.lint_error[0]:
                    painter.setPen(QColor("#f14c4c"))
                    painter.drawText(5, int(top), 12, self.fontMetrics().height(),
                                     Qt.AlignLeft, "●")
                elif number + 1 in lint_lines:
                    painter.setPen(QColor("#e5c07b"))
                    painter.drawText(5, int(top), 12, self.fontMetrics().height(),
                                     Qt.AlignLeft, "●")
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            number += 1

    #  tô dòng hiện tại / cặp ngoặc / kết quả tìm kiếm
    def set_search_matches(self, cursors):
        color = QColor(self.theme["accent"])
        color.setAlpha(90)
        sels = []
        for c in cursors:
            s = QTextEdit.ExtraSelection()
            s.format.setBackground(color)
            s.cursor = c
            sels.append(s)
        self.search_selections = sels
        self.refresh_selections()

    def refresh_selections(self):
        sels = []
        if not self.isReadOnly():
            s = QTextEdit.ExtraSelection()
            s.format.setBackground(QColor(self.theme["line_bg"]))
            s.format.setProperty(QTextFormat.FullWidthSelection, True)
            s.cursor = self.textCursor()
            s.cursor.clearSelection()
            sels.append(s)
        sels += self.search_selections
        if self.lint_error:
            block = self.document().findBlockByNumber(self.lint_error[0] - 1)
            if block.isValid():
                s = QTextEdit.ExtraSelection()
                s.format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
                s.format.setUnderlineColor(QColor("#f14c4c"))
                c = QTextCursor(block)
                c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                s.cursor = c
                sels.append(s)
        for ln, _msg in self.lint_items:
            block = self.document().findBlockByNumber(ln - 1)
            if block.isValid():
                s = QTextEdit.ExtraSelection()
                s.format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
                s.format.setUnderlineColor(QColor("#e5c07b"))
                c = QTextCursor(block)
                c.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                s.cursor = c
                sels.append(s)
        sels += self._word_selections()
        sels += self._bracket_selections()
        self.setExtraSelections(sels)
        self.line_number_area.update()

    def _word_selections(self):
        """Tô nhẹ mọi vị trí của từ đang đặt con trỏ ."""
        if self.isReadOnly() or self.lang is None or self.document().characterCount() > 150000:
            return []
        cur = self.textCursor()
        if cur.hasSelection():
            return []
        cur.select(QTextCursor.WordUnderCursor)
        word = cur.selectedText()
        if len(word) < 2 or not re.fullmatch(r"\w+", word):
            return []
        color = QColor(self.theme["accent"])
        color.setAlpha(46)
        flags = QTextDocument.FindCaseSensitively | QTextDocument.FindWholeWords
        doc, out, c = self.document(), [], QTextCursor(self.document())
        while len(out) < 300:
            c = doc.find(word, c, flags)
            if c.isNull():
                break
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(color)
            sel.cursor = c
            out.append(sel)
        return out if len(out) > 1 else []

    def _bracket_selections(self):
        if self.document().characterCount() > 300000 or self.lang is None:
            return []
        text = self.toPlainText()
        pos = self.textCursor().position()
        for idx in (pos - 1, pos):
            if 0 <= idx < len(text) and text[idx] in ALL_BRACKETS:
                other = self._find_match(text, idx)
                if other is None:
                    return []
                color = QColor(self.theme["accent"])
                color.setAlpha(120)
                out = []
                for p in (idx, other):
                    s = QTextEdit.ExtraSelection()
                    s.format.setBackground(color)
                    c = QTextCursor(self.document())
                    c.setPosition(p)
                    c.setPosition(p + 1, QTextCursor.KeepAnchor)
                    s.cursor = c
                    out.append(s)
                return out
        return []

    @staticmethod
    def _find_match(text, idx):
        ch = text[idx]
        if ch in OPEN_CLOSE:
            open_ch, close_ch = ch, OPEN_CLOSE[ch]
            rng = range(idx, min(len(text), idx + 100000))
        else:
            open_ch, close_ch = ch, CLOSE_TO_OPEN[ch]
            rng = range(idx, max(-1, idx - 100000), -1)
        depth = 0
        for j in rng:
            c = text[j]
            if c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return j
        return None

    #  zoom bằng Ctrl + lăn chuột
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self.zoomRequested.emit(1 if event.angleDelta().y() > 0 else -1)
            event.accept()
        else:
            super().wheelEvent(event)

    #  chỉnh sửa theo dòng
    def _selected_blocks(self):
        doc = self.document()
        cur = self.textCursor()
        first = doc.findBlock(cur.selectionStart())
        end_pos = cur.selectionEnd()
        last = doc.findBlock(end_pos)
        if cur.hasSelection() and end_pos == last.position() and last != first:
            last = last.previous()
        blocks, b = [], first
        while b.isValid():
            blocks.append(b)
            if b == last:
                break
            b = b.next()
        return blocks

    def indent_selection(self):
        cur = self.textCursor()
        cur.beginEditBlock()
        for b in self._selected_blocks():
            c = QTextCursor(b)
            c.insertText(self.indent_unit)
        cur.endEditBlock()

    def unindent_selection(self):
        unit = self.indent_unit
        cur = self.textCursor()
        cur.beginEditBlock()
        for b in self._selected_blocks():
            text = b.text()
            if text.startswith("\t"):
                n = 1
            else:
                n = min(len(unit), len(text) - len(text.lstrip(" ")))
            if n:
                c = QTextCursor(b)
                c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, n)
                c.removeSelectedText()
        cur.endEditBlock()

    def toggle_comment(self):
        token = (self.cfg or {}).get("line") or "#"
        blocks = self._selected_blocks()
        lines = [b for b in blocks if b.text().strip()]
        if not lines:
            return
        all_commented = all(b.text().lstrip().startswith(token) for b in lines)
        cur = self.textCursor()
        cur.beginEditBlock()
        if all_commented:
            for b in lines:
                text = b.text()
                col = len(text) - len(text.lstrip())
                n = len(token) + (1 if text[col + len(token):col + len(token) + 1] == " " else 0)
                c = QTextCursor(b)
                c.setPosition(b.position() + col)
                c.setPosition(b.position() + col + n, QTextCursor.KeepAnchor)
                c.removeSelectedText()
        else:
            min_col = min(len(b.text()) - len(b.text().lstrip()) for b in lines)
            for b in lines:
                c = QTextCursor(b)
                c.setPosition(b.position() + min_col)
                c.insertText(token + " ")
        cur.endEditBlock()

    def duplicate_line(self):
        cur = self.textCursor()
        doc = self.document()
        cur.beginEditBlock()
        if cur.hasSelection():
            text = cur.selectedText()
            end = cur.selectionEnd()
            c = QTextCursor(doc)
            c.setPosition(end)
            c.insertText(text)
        else:
            block = cur.block()
            col = cur.positionInBlock()
            c = QTextCursor(doc)
            c.setPosition(block.position() + len(block.text()))
            c.insertText("\n" + block.text())
            nc = QTextCursor(doc)
            nc.setPosition(block.position() + len(block.text()) + 1 + col)
            self.setTextCursor(nc)
        cur.endEditBlock()

    def move_lines(self, direction):
        doc = self.document()
        blocks = self._selected_blocks()
        first, last = blocks[0], blocks[-1]
        other = first.previous() if direction < 0 else last.next()
        if not other.isValid():
            return
        sel_start = first.position()
        sel_end = last.position() + len(last.text())
        c = QTextCursor(doc)
        c.setPosition(sel_start)
        c.setPosition(sel_end, QTextCursor.KeepAnchor)
        text = c.selectedText().replace("\u2029", "\n")
        other_text = other.text()
        c.beginEditBlock()
        if direction < 0:
            o_pos = other.position()
            c.setPosition(o_pos)
            c.setPosition(sel_end, QTextCursor.KeepAnchor)
            c.insertText(text + "\n" + other_text)
            new_start = o_pos
        else:
            o_end = other.position() + len(other_text)
            c.setPosition(sel_start)
            c.setPosition(o_end, QTextCursor.KeepAnchor)
            c.insertText(other_text + "\n" + text)
            new_start = sel_start + len(other_text) + 1
        c.endEditBlock()
        nc = QTextCursor(doc)
        nc.setPosition(new_start)
        nc.setPosition(new_start + len(text), QTextCursor.KeepAnchor)
        self.setTextCursor(nc)

    def goto_line(self, line):
        block = self.document().findBlockByNumber(max(0, line - 1))
        if not block.isValid():
            block = self.document().lastBlock()
        c = QTextCursor(block)
        self.setTextCursor(c)
        self.centerCursor()


    #  tab / thụt lề
    def set_tab_size(self, n):
        self.tab_size = n
        self.setTabStopDistance(n * self.fontMetrics().horizontalAdvance(" "))
        self.viewport().update()

    def _indent_cols(self, text):
        n = 0
        for ch in text:
            if ch == " ":
                n += 1
            elif ch == "\t":
                n += self.tab_size - n % self.tab_size
            else:
                break
        return n

    def convert_indent(self, to_spaces=True):
        n = self.tab_size
        out = []
        for ln in self.toPlainText().split("\n"):
            body = ln.lstrip(" \t")
            cols = self._indent_cols(ln[:len(ln) - len(body)])
            if to_spaces:
                out.append(" " * cols + body)
            else:
                out.append("\t" * (cols // n) + " " * (cols % n) + body)
        self.replace_all_text("\n".join(out))

    def join_lines(self):
        blocks = self._selected_blocks()
        first = blocks[0]
        last = blocks[-1]
        if len(blocks) == 1:
            last = first.next()
            if not last.isValid():
                return
        texts, b = [], first
        while b.isValid():
            t = b.text()
            texts.append(t.rstrip() if b == first else t.strip())
            if b == last:
                break
            b = b.next()
        c = QTextCursor(self.document())
        c.setPosition(first.position())
        c.setPosition(last.position() + len(last.text()), QTextCursor.KeepAnchor)
        c.insertText(" ".join(t for t in texts if t))

    def insert_line_below(self):
        blk = self.textCursor().block()
        line = blk.text()
        indent = line[:len(line) - len(line.lstrip(" \t"))]
        s = line.rstrip()
        extra = ""
        if (self.lang == "python" and s.endswith(":")) or \
                ((self.cfg or {}).get("brace") and s.endswith(("{", "(", "["))):
            extra = self.indent_unit
        c = QTextCursor(blk)
        c.movePosition(QTextCursor.EndOfBlock)
        c.insertText("\n" + indent + extra)
        self.setTextCursor(c)
        self.ensureCursorVisible()

    #  gập code (code folding)
    def is_foldable(self, block):
        t = block.text()
        if not t.strip():
            return False
        base = self._indent_cols(t)
        b = block.next()
        while b.isValid():
            bt = b.text()
            if bt.strip():
                return self._indent_cols(bt) > base
            b = b.next()
        return False

    def fold_range(self, block):
        """Block cuối của vùng gập bắt đầu ở `block` (None nếu không gập được)."""
        t = block.text()
        if not t.strip():
            return None
        base = self._indent_cols(t)
        last, b = None, block.next()
        while b.isValid():
            bt = b.text()
            if bt.strip():
                if self._indent_cols(bt) <= base:
                    break
                last = b
            b = b.next()
        return last

    def _folded_numbers(self):
        return {c.blockNumber() for c in self.folded}

    def _schedule_fold_refresh(self):
        if self.folded:
            self._fold_timer.start(120)

    def _relayout_folds(self):
        doc = self.document()
        # bỏ các vùng gập không còn hợp lệ (dòng bị xóa / không còn thụt lề con)
        keep, hidden = [], set()
        for c in self.folded:
            blk = c.block()
            if not blk.isValid() or not self.is_foldable(blk):
                continue
            last = self.fold_range(blk)
            if last is None:
                continue
            keep.append(c)
            b = blk.next()
            while b.isValid():
                hidden.add(b.blockNumber())
                if b == last:
                    break
                b = b.next()
        self.folded = keep
        b = doc.firstBlock()
        changed = False
        while b.isValid():
            vis = b.blockNumber() not in hidden
            if b.isVisible() != vis:
                b.setVisible(vis)
                b.setLineCount(max(1, b.lineCount()) if vis else 0)
                changed = True
            b = b.next()
        if changed:
            doc.markContentsDirty(0, max(0, doc.characterCount() - 1))
            try:
                doc.documentLayout().requestUpdate()
            except AttributeError:
                pass
        cur = self.textCursor()
        if not cur.block().isVisible():
            b = cur.block()
            while b.isValid() and not b.isVisible():
                b = b.previous()
            if b.isValid():
                self.setTextCursor(QTextCursor(b))
        self.viewport().update()
        self.line_number_area.update()

    def toggle_fold(self, block):
        n = block.blockNumber()
        for c in self.folded:
            if c.blockNumber() == n:
                self.folded.remove(c)
                break
        else:
            if self.fold_range(block) is None:
                return
            self.folded.append(QTextCursor(block))
        self._relayout_folds()

    def toggle_fold_at_cursor(self):
        b = self.textCursor().block()
        if not self.is_foldable(b):
            base = self._indent_cols(b.text())
            p = b.previous()
            while p.isValid():
                if p.text().strip() and self._indent_cols(p.text()) < base \
                        and self.is_foldable(p):
                    b = p
                    break
                p = p.previous()
            else:
                return
        self.toggle_fold(b)

    def fold_all(self):
        b = self.document().firstBlock()
        while b.isValid():
            if self.is_foldable(b) and b.blockNumber() not in self._folded_numbers():
                self.folded.append(QTextCursor(b))
            b = b.next()
        self._relayout_folds()

    def unfold_all(self):
        if self.folded:
            self.folded = []
            self._relayout_folds()

    #  breadcrumb (đường dẫn > hàm hiện tại)
    def _symbol_chain(self):
        b = self.textCursor().block()
        t = b.text()
        cur = self._indent_cols(t) if t.strip() else 10 ** 6
        chain, n, first = [], 0, True
        while b.isValid() and n < 4000:
            t = b.text()
            n += 1
            if t.strip():
                m = OUTLINE_GENERIC.match(t)
                if not m and self.lang in ("c", "cpp", "java", "arduino") and not t.rstrip().endswith(";") \
                        and not t.startswith((" ", "\t")):
                    m = OUTLINE_CFUNC.match(t)
                    if m and m.group(1) in OUTLINE_SKIP:
                        m = None
                if m:
                    ind = self._indent_cols(t)
                    if ind < cur or (first and ind <= cur):
                        chain.append(m.group(1))
                        cur = ind
                        if ind == 0:
                            break
            first = False
            b = b.previous()
        return list(reversed(chain))

    def update_breadcrumb(self):
        muted, fg, sep = getattr(self, "_bc_colors", ("#888888", "#cccccc", "#555555"))
        parts = []
        fp = self.file_path
        if fp:
            win = self.window()
            root = win._project_root() if hasattr(win, "_project_root") else ""
            try:
                rel = os.path.relpath(fp, root) if root else fp
                if rel.startswith(".."):
                    rel = os.path.join(os.path.basename(os.path.dirname(fp)), os.path.basename(fp))
            except ValueError:
                rel = os.path.basename(fp)
            parts = rel.replace("\\", "/").split("/")
            if len(parts) > 4:
                parts = ["…"] + parts[-3:]
        else:
            parts = ["untitled"]
        chev = f' <span style="color:{sep}">›</span> '
        html = [f'<span style="color:{muted}">{p}</span>' for p in parts[:-1]]
        html.append(f'<span style="color:{fg}">{parts[-1]}</span>')
        for s in self._symbol_chain():
            html.append(f'<span style="color:{muted}">ƒ {s}</span>')
        self.breadcrumb.setText(chev.join(html))

    #  bookmark
    def toggle_bookmark(self, line=None):
        blk = self.textCursor().block() if line is None \
            else self.document().findBlockByNumber(line)
        for c in self.bookmarks:
            if c.blockNumber() == blk.blockNumber():
                self.bookmarks.remove(c)
                break
        else:
            self.bookmarks.append(QTextCursor(blk))
        self.line_number_area.update()

    def goto_bookmark(self, direction=1):
        lines = sorted({c.blockNumber() for c in self.bookmarks})
        if not lines:
            return
        cur = self.textCursor().blockNumber()
        if direction > 0:
            nxt = [l for l in lines if l > cur]
            target = nxt[0] if nxt else lines[0]
        else:
            prv = [l for l in lines if l < cur]
            target = prv[-1] if prv else lines[-1]
        if not self.document().findBlockByNumber(target).isVisible():
            self.unfold_all()
        self.goto_line(target + 1)

    def clear_bookmarks(self):
        self.bookmarks = []
        self.line_number_area.update()

    def gutter_click(self, pos):
        block = self.firstVisibleBlock()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        while block.isValid():
            h = self.blockBoundingRect(block).height()
            if block.isVisible() and top <= pos.y() < top + h:
                if pos.x() >= self.line_number_area.width() - 18 and self.is_foldable(block):
                    self.toggle_fold(block)
                else:
                    self.toggle_bookmark(block.blockNumber())
                return
            if top > pos.y():
                return
            top += h
            block = block.next()

    #  đường kẻ thụt lề
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.show_guides or self.lang is None:
            return
        p = QPainter(self.viewport())
        col = QColor(self.theme["gutter_fg"])
        col.setAlpha(70)
        p.setPen(col)
        cw = self.fontMetrics().horizontalAdvance(" ")
        off = self.contentOffset()
        x0 = off.x() + self.document().documentMargin()
        unit = 2 if self.lang == "json" else 4
        block = self.firstVisibleBlock()
        top = self.blockBoundingGeometry(block).translated(off).top()
        limit = event.rect().bottom()
        while block.isValid() and top <= limit:
            h = self.blockBoundingRect(block).height()
            if block.isVisible() and h > 0:
                t = block.text()
                if t.strip():
                    cols = self._indent_cols(t)
                    k = unit
                    while k < cols:
                        x = int(x0 + k * cw)
                        p.drawLine(x, int(top), x, int(top + h))
                        k += unit
            top += h
            block = block.next()
        p.end()

    def _provider_lints(self):
        win = self.window()
        provs = getattr(win, "_lint_providers", None)
        if not provs or self.document().characterCount() > 1000000:
            return []
        text, items = self.toPlainText(), []
        for fn in list(provs):
            try:
                for r in fn(text, self.lang, self.file_path) or []:
                    if isinstance(r, dict):
                        r = (r.get("line", 1), r.get("message", ""))
                    items.append((int(r[0]), str(r[1])))
            except Exception:  # noqa: BLE001
                pass
        return sorted(set(items))[:200]

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        acts = getattr(self.window(), "_context_actions", [])
        if acts:
            menu.addSeparator()
            for text, cb in acts:
                a = menu.addAction(text)
                a.triggered.connect(lambda _=False, c=cb: c())
        menu.exec_(event.globalPos())

    #  kiểm tra cú pháp (Python)
    def _run_lint(self):
        err = None
        if self.large_mode:
            return
        if self.lang == "python" and self.document().characterCount() < 400000:
            try:
                ast.parse(self.toPlainText())
            except SyntaxError as e:
                err = (e.lineno or 1, e.msg or "Lỗi cú pháp")
            except (ValueError, RecursionError):
                err = None
        items = self._provider_lints()
        if err != self.lint_error or items != self.lint_items:
            self.lint_error = err
            self.lint_items = items
            self.refresh_selections()
            self.lintChanged.emit()

    #  snippet
    def _try_snippet(self, cur):
        snippets = SNIPPETS.get(self.lang)
        if not snippets:
            return False
        prefix = self._prefix_before_cursor()
        tpl = snippets.get(prefix)
        if tpl is None:
            return False
        line = cur.block().text()
        indent = line[:len(line) - len(line.lstrip(" \t"))]
        text = tpl.replace("    ", self.indent_unit).replace("\n", "\n" + indent)
        pos = text.find("$0")
        text = text.replace("$0", "")
        cur.beginEditBlock()
        cur.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(prefix))
        start = cur.selectionStart()
        cur.insertText(text)
        cur.endEditBlock()
        nc = QTextCursor(self.document())
        nc.setPosition(start + (pos if pos >= 0 else len(text)))
        self.setTextCursor(nc)
        self.completer.popup().hide()
        return True

    #  các lệnh chỉnh sửa thêm
    def delete_line(self):
        blocks = self._selected_blocks()
        first, last = blocks[0], blocks[-1]
        start = first.position()
        end = last.position() + len(last.text())
        if last.next().isValid():
            end += 1
        elif first.previous().isValid():
            start -= 1
        c = QTextCursor(self.document())
        c.setPosition(start)
        c.setPosition(end, QTextCursor.KeepAnchor)
        c.removeSelectedText()

    def change_case(self, upper=True):
        cur = self.textCursor()
        if not cur.hasSelection():
            cur.select(QTextCursor.WordUnderCursor)
        if not cur.hasSelection():
            return
        start = cur.selectionStart()
        text = cur.selectedText()
        new = text.upper() if upper else text.lower()
        cur.insertText(new)
        nc = QTextCursor(self.document())
        nc.setPosition(start)
        nc.setPosition(start + len(new), QTextCursor.KeepAnchor)
        self.setTextCursor(nc)

    def select_next_occurrence(self):
        """Ctrl+D: chọn từ dưới con trỏ, lặp lại sẽ nhảy tới lần xuất hiện kế tiếp."""
        cur = self.textCursor()
        if not cur.hasSelection():
            cur.select(QTextCursor.WordUnderCursor)
            if cur.hasSelection():
                self.setTextCursor(cur)
            return
        text = cur.selectedText()
        doc = self.document()
        found = doc.find(text, cur.selectionEnd(), QTextDocument.FindCaseSensitively)
        if found.isNull():
            found = doc.find(text, 0, QTextDocument.FindCaseSensitively)
        if not found.isNull():
            self.setTextCursor(found)
            self.ensureCursorVisible()

    @staticmethod
    def _split_words(s):
        s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
        return [w for w in re.split(r"[^A-Za-z0-9]+", s) if w]

    def convert_case_style(self, style):
        cur = self.textCursor()
        if not cur.hasSelection():
            cur.select(QTextCursor.WordUnderCursor)
        if not cur.hasSelection():
            return
        words = [w.lower() for w in self._split_words(cur.selectedText())]
        if not words:
            return
        if style == "snake":
            new = "_".join(words)
        elif style == "kebab":
            new = "-".join(words)
        elif style == "camel":
            new = words[0] + "".join(w.capitalize() for w in words[1:])
        elif style == "pascal":
            new = "".join(w.capitalize() for w in words)
        else:
            new = "_".join(words).upper()
        start = cur.selectionStart()
        cur.insertText(new)
        nc = QTextCursor(self.document())
        nc.setPosition(start)
        nc.setPosition(start + len(new), QTextCursor.KeepAnchor)
        self.setTextCursor(nc)

    def rename_symbol(self):
        cur = self.textCursor()
        if not cur.hasSelection():
            cur.select(QTextCursor.WordUnderCursor)
        old = cur.selectedText().strip()
        if not old:
            return
        new, ok = QInputDialog.getText(self, "Đổi tên symbol",
                                       f"Đổi tên '{old}' trong file này thành:", text=old)
        if not ok or not new or new == old:
            return
        pat = re.compile(r"(?<![\w])" + re.escape(old) + r"(?![\w])")
        text = self.toPlainText()
        res, n = pat.subn(lambda m: new, text)
        if n:
            c = QTextCursor(self.document())
            c.beginEditBlock()
            c.select(QTextCursor.Document)
            c.insertText(res)
            c.endEditBlock()

    def sort_lines(self):
        blocks = self._selected_blocks()
        if len(blocks) < 2:
            blocks = []
            b = self.document().firstBlock()
            while b.isValid():
                blocks.append(b)
                b = b.next()
        first, last = blocks[0], blocks[-1]
        texts = sorted((b.text() for b in blocks), key=str.lower)
        c = QTextCursor(self.document())
        c.setPosition(first.position())
        c.setPosition(last.position() + len(last.text()), QTextCursor.KeepAnchor)
        c.insertText("\n".join(texts))

    def trim_trailing_ws(self):
        doc = self.document()
        c = QTextCursor(doc)
        c.beginEditBlock()
        blocks, b = [], doc.firstBlock()
        while b.isValid():
            blocks.append(b)
            b = b.next()
        for b in blocks:
            t = b.text()
            kept = len(t.rstrip(" \t"))
            if kept != len(t):
                r = QTextCursor(b)
                r.setPosition(b.position() + kept)
                r.setPosition(b.position() + len(t), QTextCursor.KeepAnchor)
                r.removeSelectedText()
        c.endEditBlock()

    def normalize_for_save(self):
        """Xóa khoảng trắng cuối dòng và đảm bảo file kết thúc bằng xuống dòng."""
        self.trim_trailing_ws()
        if self.document().lastBlock().text() != "":
            c = QTextCursor(self.document())
            c.movePosition(QTextCursor.End)
            c.insertText("\n")

    def set_show_whitespace(self, on):
        opt = self.document().defaultTextOption()
        flags = opt.flags()
        if on:
            flags |= QTextOption.ShowTabsAndSpaces
        else:
            flags &= ~QTextOption.ShowTabsAndSpaces
        opt.setFlags(flags)
        self.document().setDefaultTextOption(opt)

    def replace_all_text(self, text):
        """Thay toàn bộ nội dung nhưng giữ (gần đúng) vị trí con trỏ."""
        line = self.textCursor().blockNumber()
        col = self.textCursor().positionInBlock()
        c = QTextCursor(self.document())
        c.beginEditBlock()
        c.select(QTextCursor.Document)
        c.insertText(text)
        c.endEditBlock()
        block = self.document().findBlockByNumber(line)
        if not block.isValid():
            block = self.document().lastBlock()
        nc = QTextCursor(block)
        nc.setPosition(block.position() + min(col, len(block.text())))
        self.setTextCursor(nc)

    def selected_code(self):
        cur = self.textCursor()
        if cur.hasSelection():
            return cur.selectedText().replace("\u2029", "\n")
        return cur.block().text()

    #  autocomplete
    def _prefix_before_cursor(self):
        c = self.textCursor()
        line = c.block().text()[:c.positionInBlock()]
        m = re.search(r"[A-Za-z_]\w*$", line)
        return m.group(0) if m else ""

    def _insert_completion(self, text):
        prefix = self._prefix_before_cursor()
        tc = self.textCursor()
        tc.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(prefix))
        tc.insertText(text)
        self.setTextCursor(tc)

    def _maybe_complete(self, force=False):
        prefix = self._prefix_before_cursor()
        popup = self.completer.popup()
        if len(prefix) < 2 and not force:
            popup.hide()
            return
        words = set(KEYWORDS.get(self.lang, []))
        if self.document().characterCount() < 500000:
            words |= set(re.findall(r"[A-Za-z_]\w{2,}", self.toPlainText()))
        words.discard(prefix)
        self._completer_model.setStringList(sorted(words, key=str.lower))
        self.completer.setCompletionPrefix(prefix)
        if self.completer.completionCount() == 0:
            popup.hide()
            return
        popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
        cr = self.cursorRect()
        cr.setWidth(popup.sizeHintForColumn(0)
                    + popup.verticalScrollBar().sizeHint().width() + 8)
        self.completer.complete(cr)

    #  bàn phím
    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        popup = self.completer.popup()

        if popup.isVisible() and key in (
                Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab,
                Qt.Key_Backtab):
            event.ignore()
            return

        if key == Qt.Key_Space and mods & Qt.ControlModifier:
            self._maybe_complete(force=True)
            return

        cur = self.textCursor()

        if key == Qt.Key_Tab and not mods & (Qt.ControlModifier | Qt.AltModifier):
            if not cur.hasSelection() and self._try_snippet(cur):
                return
            if cur.hasSelection() and cur.block() != self.document().findBlock(
                    cur.selectionEnd()):
                self.indent_selection()
            elif self.indent_unit == "\t":
                cur.insertText("\t")
            else:
                n = 4 - (cur.positionInBlock() % 4)
                cur.insertText(" " * n)
            return
        if key == Qt.Key_Backtab:
            self.unindent_selection()
            return

        if key in (Qt.Key_Return, Qt.Key_Enter) and not mods & Qt.ControlModifier:
            self._auto_indent_newline()
            return

        if key == Qt.Key_Backspace and not cur.hasSelection() and not mods:
            line = cur.block().text()
            col = cur.positionInBlock()
            if 0 < col < len(line):
                prev, nxt = line[col - 1], line[col]
                if (OPEN_CLOSE.get(prev) == nxt) or (prev == nxt and prev in "\"'"):
                    cur.beginEditBlock()
                    cur.deletePreviousChar()
                    cur.deleteChar()
                    cur.endEditBlock()
                    return

        text = event.text()
        if text and len(text) == 1 and not mods & (Qt.ControlModifier | Qt.AltModifier):
            if self._handle_pair_typing(text, cur):
                return

        super().keyPressEvent(event)

        if text and (text.isalnum() or text == "_") \
                and not mods & (Qt.ControlModifier | Qt.AltModifier):
            self._maybe_complete()
        elif popup.isVisible() and key not in (Qt.Key_Shift, Qt.Key_Control,
                                               Qt.Key_Alt, Qt.Key_Backspace):
            popup.hide()
        elif popup.isVisible() and key == Qt.Key_Backspace:
            self._maybe_complete()

    def _auto_indent_newline(self):
        cur = self.textCursor()
        line = cur.block().text()
        col = cur.positionInBlock()
        before, after = line[:col], line[col:]
        indent = line[:len(line) - len(line.lstrip(" \t"))]
        unit = self.indent_unit
        cfg = self.cfg or {}
        stripped = before.rstrip()

        cur.beginEditBlock()
        if not cfg.get("brace") and self.lang == "python":
            extra = unit if stripped.endswith(":") else ""
            if not extra and re.match(r"^(return|pass|break|continue|raise)\b",
                                      stripped.lstrip()) and indent.startswith(unit):
                indent = indent[:-len(unit)]
            cur.insertText("\n" + indent + extra)
        elif cfg.get("brace") and stripped.endswith(("{", "(", "[")):
            if after.lstrip()[:1] in CLOSERS:
                cur.insertText("\n" + indent + unit + "\n" + indent)
                cur.movePosition(QTextCursor.Up)
                cur.movePosition(QTextCursor.EndOfLine)
            else:
                cur.insertText("\n" + indent + unit)
        else:
            cur.insertText("\n" + indent)
        cur.endEditBlock()
        self.setTextCursor(cur)
        self.ensureCursorVisible()

    def _handle_pair_typing(self, ch, cur):
        line = cur.block().text()
        col = cur.positionInBlock()
        nxt = line[col] if col < len(line) else ""
        prev = line[col - 1] if col > 0 else ""

        if ch in OPEN_CLOSE:
            close = OPEN_CLOSE[ch]
            if cur.hasSelection():
                sel = cur.selectedText()
                cur.insertText(ch + sel + close)
                return True
            if nxt == "" or nxt.isspace() or nxt in ")]},;":
                cur.insertText(ch + close)
                cur.movePosition(QTextCursor.Left)
                self.setTextCursor(cur)
                return True
            return False
        if ch in CLOSERS and nxt == ch and not cur.hasSelection():
            cur.movePosition(QTextCursor.Right)
            self.setTextCursor(cur)
            return True
        if ch in "\"'":
            if cur.hasSelection():
                sel = cur.selectedText()
                cur.insertText(ch + sel + ch)
                return True
            if nxt == ch:
                cur.movePosition(QTextCursor.Right)
                self.setTextCursor(cur)
                return True
            if prev.isalnum() or prev == "_" or nxt.isalnum() \
                    or line[:col].endswith(ch * 2):
                return False
            cur.insertText(ch + ch)
            cur.movePosition(QTextCursor.Left)
            self.setTextCursor(cur)
            return True
        return False


# Thanh Tìm / Thay thế
class FindBar(QWidget):
    MAX_HIGHLIGHT = 2000

    def __init__(self, get_editor, parent=None):
        super().__init__(parent)
        self.get_editor = get_editor
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 4, 6, 4)
        outer.setSpacing(3)

        r1 = QHBoxLayout()
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Tìm...")
        self.count_label = QLabel("")
        self.count_label.setMinimumWidth(110)
        prev_btn, next_btn, close_btn = QPushButton("▲"), QPushButton("▼"), QPushButton("✕")
        for b, tip in ((prev_btn, "Kết quả trước (Shift+F3)"),
                       (next_btn, "Kết quả sau (F3)"), (close_btn, "Đóng (Esc)")):
            b.setFixedWidth(30)
            b.setToolTip(tip)
        self.case_cb = QCheckBox("Aa")
        self.case_cb.setToolTip("Phân biệt hoa/thường")
        self.word_cb = QCheckBox("Từ")
        self.word_cb.setToolTip("Khớp cả từ")
        self.regex_cb = QCheckBox(".*")
        self.regex_cb.setToolTip("Biểu thức chính quy (regex)")
        for w in (self.find_edit, prev_btn, next_btn, self.case_cb, self.word_cb,
                  self.regex_cb, self.count_label, close_btn):
            r1.addWidget(w, 1 if w is self.find_edit else 0)
        outer.addLayout(r1)

        self.replace_row = QWidget()
        r2 = QHBoxLayout(self.replace_row)
        r2.setContentsMargins(0, 0, 0, 0)
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Thay bằng...")
        rep_btn, rep_all_btn = QPushButton("Thay"), QPushButton("Thay tất cả")
        r2.addWidget(self.replace_edit, 1)
        r2.addWidget(rep_btn)
        r2.addWidget(rep_all_btn)
        outer.addWidget(self.replace_row)

        self.find_edit.textChanged.connect(self._on_text_changed)
        self.find_edit.returnPressed.connect(lambda: self.find_next(True))
        self.replace_edit.returnPressed.connect(self.replace_one)
        next_btn.clicked.connect(lambda: self.find_next(True))
        prev_btn.clicked.connect(lambda: self.find_next(False))
        close_btn.clicked.connect(self.close_bar)
        rep_btn.clicked.connect(self.replace_one)
        rep_all_btn.clicked.connect(self.replace_all)
        for cb in (self.case_cb, self.word_cb, self.regex_cb):
            cb.toggled.connect(self._on_text_changed)
        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self.close_bar,
                  context=Qt.WidgetWithChildrenShortcut)
        self.hide()

    #  helpers
    def show_find(self, replace=False):
        ed = self.get_editor()
        if ed is not None:
            sel = ed.textCursor().selectedText()
            if sel and "\u2029" not in sel:
                self.find_edit.setText(sel)
        self.replace_row.setVisible(replace)
        self.show()
        self.find_edit.setFocus()
        self.find_edit.selectAll()
        self._on_text_changed()

    def close_bar(self):
        ed = self.get_editor()
        if ed is not None:
            ed.set_search_matches([])
            ed.setFocus()
        self.hide()

    def _query(self):
        text = self.find_edit.text()
        if not text:
            return None
        if self.regex_cb.isChecked():
            rx = QRegExp(text, Qt.CaseSensitive if self.case_cb.isChecked()
                         else Qt.CaseInsensitive)
            if not rx.isValid():
                self.count_label.setText("Regex lỗi")
                return None
            return rx
        return text

    def _flags(self):
        flags = QTextDocument.FindFlags()
        if self.case_cb.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.word_cb.isChecked() and not self.regex_cb.isChecked():
            flags |= QTextDocument.FindWholeWords
        return flags

    def _on_text_changed(self, *_):
        ed = self.get_editor()
        if ed is None or not self.isVisible():
            return
        if self.find_edit.text():
            self.find_next(True, keep=True)
        else:
            self.count_label.setText("")
        self.update_highlights()

    def refresh(self):
        if self.isVisible():
            self.update_highlights()

    def update_highlights(self):
        ed = self.get_editor()
        if ed is None:
            return
        q = self._query()
        if q is None:
            ed.set_search_matches([])
            if not self.find_edit.text():
                self.count_label.setText("")
            return
        doc, flags = ed.document(), self._flags()
        matches = []
        c = QTextCursor(doc)
        total = 0
        while True:
            found = doc.find(q, c, flags)
            if found.isNull():
                break
            total += 1
            if len(matches) < self.MAX_HIGHLIGHT:
                matches.append(found)
            if not found.hasSelection():
                break
            c = found
            if total >= 100000:
                break
        ed.set_search_matches(matches)
        self.count_label.setText(f"{total} kết quả" if total else "Không tìm thấy")

    #  tìm / thay
    def find_next(self, forward=True, keep=False):
        ed = self.get_editor()
        q = self._query()
        if ed is None or q is None:
            return False
        doc = ed.document()
        flags = self._flags()
        if not forward:
            flags |= QTextDocument.FindBackward
        cur = ed.textCursor()
        if keep:
            cur.setPosition(cur.selectionStart())
        found = doc.find(q, cur, flags)
        if found.isNull():
            wrap = QTextCursor(doc)
            wrap.movePosition(QTextCursor.Start if forward else QTextCursor.End)
            found = doc.find(q, wrap, flags)
        if found.isNull():
            return False
        ed.setTextCursor(found)
        ed.ensureCursorVisible()
        return True

    def _selection_matches(self, cur, q):
        sel = cur.selectedText()
        if isinstance(q, QRegExp):
            return q.exactMatch(sel)
        if self.case_cb.isChecked():
            return sel == q
        return sel.lower() == q.lower()

    def replace_one(self):
        ed = self.get_editor()
        q = self._query()
        if ed is None or q is None:
            return
        cur = ed.textCursor()
        if cur.hasSelection() and self._selection_matches(cur, q):
            cur.insertText(self.replace_edit.text())
            ed.setTextCursor(cur)
        self.find_next(True)
        self.update_highlights()

    def replace_all(self):
        ed = self.get_editor()
        q = self._query()
        if ed is None or q is None:
            return
        doc, flags = ed.document(), self._flags()
        rep = self.replace_edit.text()
        c = QTextCursor(doc)
        c.beginEditBlock()
        count = 0
        while count < 100000:
            found = doc.find(q, c, flags)
            if found.isNull() or not found.hasSelection():
                break
            found.insertText(rep)
            c = found
            count += 1
        c.endEditBlock()
        self.update_highlights()
        self.count_label.setText(f"Đã thay {count}")


# Terminal
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class FileLoadThread(QThread):
    """Đọc + giải mã file lớn ở luồng nền để giao diện không bị treo."""
    loaded = pyqtSignal(str, object)      # đường dẫn, (nội dung, mã hóa, EOL, bị_cắt) | None (nhị phân)
    failed = pyqtSignal(str, str)

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path

    def run(self):
        try:
            res = read_text_file_ex(self.path)
            truncated = False
            if res is not None:
                content, enc, eol = res
                if len(content) > MAX_LINE_CHARS and max(map(len, content.split("\n"))) > MAX_LINE_CHARS:
                    # dòng khổng lồ (JSON/JS minify...) làm Qt đứng hàng chục giây: chỉ hiển thị phần đầu
                    content = "\n".join(
                        l if len(l) <= MAX_LINE_CHARS else
                        l[:MAX_LINE_CHARS] + " …[đã cắt %s ký tự]" % format(len(l) - MAX_LINE_CHARS, ",")
                        for l in content.split("\n"))
                    truncated = True
                res = (content, enc, eol, truncated)
            self.loaded.emit(self.path, res)
        except Exception as ex:  # noqa: BLE001
            self.failed.emit(self.path, str(ex))


MAX_LINE_CHARS = 100000                   # dòng dài hơn mức này bị cắt khi hiển thị (file mở ở chế độ chỉ đọc)
LARGE_FILE_BYTES = 2 * 1024 * 1024        # >2MB: đọc ở luồng nền
HUGE_FILE_BYTES = 6 * 1024 * 1024         # >6MB: chế độ file lớn (tắt tô màu, minimap...)
