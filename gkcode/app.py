# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp', 'templates', 'polyglot', 'plugins', 'textools', 'toolsmixin', 'viewers', 'media', 'prefs', 'extras']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


class WelcomePage(QWidget):
    """Trang chào: phủ lên vùng soạn thảo khi chưa có gì để làm việc."""

    def __init__(self, win):
        super().__init__(win.tabs)
        self.win = win
        self.setObjectName("welcome")
        self.setAttribute(Qt.WA_StyledBackground, True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 0, 24, 0)
        outer.addStretch(1)
        box = QWidget()
        box.setMinimumWidth(560)
        box.setMaximumWidth(800)
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        title = QLabel(APP_NAME)
        title.setObjectName("wTitle")
        sub_l = QLabel(f"Python IDE  \u00b7  v{APP_VERSION}")
        sub_l.setObjectName("wSub")
        v.addWidget(title)
        v.addWidget(sub_l)
        v.addSpacing(20)
        cols = QHBoxLayout()
        cols.setSpacing(32)
        left = QVBoxLayout()
        left.setSpacing(6)
        left.addWidget(self._head("BẮT ĐẦU"))
        for name, sc, slot in (
                ("Tệp trống", "Ctrl+N", win.welcome_dismiss),
                ("Mở tệp...", "Ctrl+O", win.open_file),
                ("Mở thư mục...", "", win.open_folder),
                ("Tạo từ mẫu dự án...", "", win.new_from_template),
                ("Command Palette", "Ctrl+Shift+P", win.command_palette)):
            left.addWidget(self._row(name, sc, slot))
        left.addStretch(1)
        self.recent_box = QWidget()
        rv = QVBoxLayout(self.recent_box)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(6)
        rv.addWidget(self._head("MỞ GẦN ĐÂY"))
        self.recent_list = QVBoxLayout()
        self.recent_list.setSpacing(6)
        rv.addLayout(self.recent_list)
        rv.addStretch(1)
        cols.addLayout(left, 1)
        cols.addWidget(self.recent_box, 1)
        v.addLayout(cols)
        v.addSpacing(16)
        tips = QLabel("Ctrl+P mở nhanh   \u00b7   F5 chạy   \u00b7   F6 build EXE   "
                      "\u00b7   F11 chế độ Zen")
        tips.setObjectName("wKey")
        v.addWidget(tips)
        centered = QHBoxLayout()
        centered.addStretch(1)
        centered.addWidget(box, 100)
        centered.addStretch(1)
        outer.addLayout(centered)
        outer.addStretch(2)

    @staticmethod
    def _head(text):
        lb = QLabel(text)
        lb.setObjectName("wHead")
        return lb

    def _row(self, name, right, slot, obj="wAct"):
        b = QPushButton()
        b.setObjectName(obj)
        b.setCursor(Qt.PointingHandCursor)
        b.setFixedHeight(38)
        h = QHBoxLayout(b)
        h.setContentsMargins(14, 0, 14, 0)
        a = QLabel(name)
        k = QLabel(right)
        k.setObjectName("wKey")
        for w in (a, k):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)
        h.addWidget(a)
        h.addStretch(1)
        h.addWidget(k)
        b.clicked.connect(lambda _=False, s=slot: s())
        return b

    def refresh_recent(self):
        while self.recent_list.count():
            wd = self.recent_list.takeAt(0).widget()
            if wd is not None:
                wd.setParent(None)
                wd.deleteLater()
        try:
            files = json.loads(self.win.settings.value("recent/files", "[]") or "[]")
        except (ValueError, TypeError):
            files = []
        files = [p for p in files if os.path.isfile(p)][:5]
        for p in files:
            folder = os.path.basename(os.path.dirname(p))
            self.recent_list.addWidget(
                self._row(os.path.basename(p), folder[:18],
                          lambda path=p: self.win.open_path(path), "wRecent"))
        if not files:
            empty = QLabel("Chưa có tệp nào gần đây")
            empty.setObjectName("wKey")
            self.recent_list.addWidget(empty)

    def apply_theme(self, t):
        pal = ui_palette(t)
        self.setStyleSheet(f"""
#welcome {{ background: {t['bg']}; }}
#welcome QLabel {{ background: transparent; color: {pal['fg']}; }}
#welcome QLabel#wTitle {{ font-size: 34pt; font-weight: 700; color: {pal['accent']}; }}
#welcome QLabel#wSub {{ color: {pal['muted']}; font-size: 11pt; }}
#welcome QLabel#wHead {{ color: {pal['muted']}; font-size: 8pt; font-weight: 600; }}
#welcome QLabel#wKey {{ color: {pal['muted']}; font-size: 9pt; }}
#welcome QPushButton#wAct, #welcome QPushButton#wRecent {{
    background: {pal['side']}; border: 1px solid {pal['border']}; border-radius: 8px; }}
#welcome QPushButton#wAct:hover, #welcome QPushButton#wRecent:hover {{
    border-color: {pal['accent']}; background: {pal['hover']}; }}
""")


class PyApp(ExtrasMixin, ToolsMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("PyAppTools", "PyApp")
        load_custom_themes(self.settings)
        load_ui_opts(self.settings)
        self.theme_name = self.settings.value("ui/theme", DEFAULT_THEME)
        if str(self.settings.value("ui/ui_rev", "")) != "43":   # 4.3: chuyển sang theme mới một lần
            self.theme_name = DEFAULT_THEME
            self.settings.setValue("ui/theme", DEFAULT_THEME)
            self.settings.setValue("ui/ui_rev", "43")
        if self.theme_name not in THEMES:
            self.theme_name = DEFAULT_THEME
        try:
            self.font_size = int(self.settings.value("ui/font_size", 11))
        except (TypeError, ValueError):
            self.font_size = 11
        self.word_wrap = self.settings.value("ui/wrap", False, type=bool)
        self.autosave_before_run = self.settings.value("run/autosave", False, type=bool)
        self.trim_on_save = self.settings.value("edit/trim_on_save", False, type=bool)
        self.show_ws = self.settings.value("ui/show_ws", False, type=bool)
        self.show_guides = self.settings.value("ui/guides", True, type=bool)
        self.show_minimap = self.settings.value("ui/minimap", True, type=bool)
        try:
            self.tab_size = int(self.settings.value("edit/tab_size", 4))
        except (TypeError, ValueError):
            self.tab_size = 4
        try:
            self.autosave_secs = int(self.settings.value("edit/autosave_secs", 0))
        except (TypeError, ValueError):
            self.autosave_secs = 0
        CFG.PY_OVERRIDE = self.settings.value("py/interpreter", "") or ""
        CFG.C_COMPILER = self.settings.value("cc/path", "") or ""
        CFG.C_FLAGS = self.settings.value("cc/flags", "-Wall")
        CFG.CPP_FLAGS = self.settings.value("cc/cppflags", "-Wall")
        self._closed_paths = []
        self._rerun = None
        self._tools_init()

        self.setWindowTitle(f"{APP_NAME} - Python IDE")
        self.resize(1200, 780)
        self.setAcceptDrops(True)

        for _ic in ("icon.png", "icon.ico"):
            icon_path = os.path.join(getattr(sys, "_MEIPASS", APP_DIR), _ic)
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break

        #  tabs + thanh tìm kiếm
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.findbar = FindBar(self.current_editor)
        editor_area = QWidget()
        ev = QVBoxLayout(editor_area)
        ev.setContentsMargins(0, 0, 0, 0)
        ev.setSpacing(0)
        ev.addWidget(self.findbar)
        ev.addWidget(self.tabs, 1)

        #  terminal + progress
        self.terminal = TerminalPanel(THEMES[self.theme_name])
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFormat("Sẵn sàng")
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.bottom = QWidget()
        bv = QVBoxLayout(self.bottom)
        bv.setContentsMargins(0, 0, 0, 0)
        bv.setSpacing(0)
        bv.addWidget(self.progress)
        bv.addWidget(self.terminal)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(editor_area)
        self.splitter.addWidget(self.bottom)
        self.splitter.setSizes([560, 220])
        self.setCentralWidget(self.splitter)

        #  explorer
        self.fs_model = QFileSystemModel()
        self.tree = QTreeView()
        self.tree.setModel(self.fs_model)
        self._icon_provider = ModernIconProvider()
        self.fs_model.setIconProvider(self._icon_provider)
        self.tree.setIndentation(14)
        self.tree.setIconSize(QSize(16, 16))
        for col in (1, 2, 3):
            self.tree.hideColumn(col)
        self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(self._on_tree_double_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._tree_menu)
        self.dock = QDockWidget("Thư mục", self)
        self.dock.setObjectName("explorerDock")
        self.dock.setWidget(self.tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        folder = self.settings.value("explorer/root", "")
        if folder and os.path.isdir(folder):
            self._set_explorer_root(folder)
        else:
            self.dock.hide()

        #  status bar
        self.pos_label = QLabel("")
        self.lang_label = QLabel("")
        self.enc_label = self._status_button("UTF-8", self._enc_menu)
        self.eol_label = self._status_button("LF", self._eol_menu)
        for w in (self.pos_label, self.lang_label, self.enc_label, self.eol_label):
            self.statusBar().addPermanentWidget(w)
        self.lint_label = QLabel("")
        self.statusBar().addWidget(self.lint_label)
        self._build_search_dock()

        self._build_menu_and_toolbar()
        self._build_console_dock()
        self._build_activity_bar()
        self._register_builtin_tools()
        self._register_extras()
        self._install_default_plugins()
        self.load_plugins()
        self.load_user_snippets()
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._autosave_tick)
        self._apply_autosave_timer()
        self.py_label = QLabel("")
        self.statusBar().addPermanentWidget(self.py_label)
        self._update_py_label()

        #  khôi phục phiên làm việc
        self._restore_session()
        if self.tabs.count() == 0:
            self.new_tab()
        self._welcome_hidden = False
        self.welcome = WelcomePage(self)
        self.welcome.hide()
        self.tabs.installEventFilter(self)
        self.tabs.currentChanged.connect(self._schedule_welcome)
        self._contrast_fixer = ContrastFixer(self)
        QApplication.instance().installEventFilter(self._contrast_fixer)
        self.set_theme(self.theme_name)
        self._schedule_welcome()
        geo = self.settings.value("ui/geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        state = self.settings.value("ui/state")
        if state is not None:
            self.restoreState(state)
        self._upper_dock_titles()
        self.statusBar().setSizeGripEnabled(False)
        QTimer.singleShot(0, lambda: self.emit_event("start"))

    #  theme
    #  giao diện hiện đại
    def _apply_modern_ui(self, t):
        pal = ui_palette(t)
        self.tabs.setStyleSheet(tab_stylesheet(t))
        self.tabs.tabBar().setIconSize(QSize(14, 14))
        self.tabs.tabBar().setDrawBase(False)
        self.progress.setStyleSheet(
            f"QProgressBar {{ background: {pal['side']}; color: {pal['muted']}; border: none; "
            f"border-top: 1px solid {pal['border']}; height: 18px; font-size: 8.5pt; text-align: left; "
            f"padding-left: 10px; }} QProgressBar::chunk {{ background: {pal['accent_a']}; }}")
        self.findbar.setAttribute(Qt.WA_StyledBackground, True)
        self.findbar.setStyleSheet(
            f"FindBar {{ background: {pal['side']}; border-bottom: 1px solid {pal['border']}; }} "
            f"QLabel, QCheckBox {{ color: {pal['muted']}; }}")
        self.tree.setStyleSheet("")
        if hasattr(self, "branch_label"):
            self.branch_label.setStyleSheet(f"color: {pal['accent']}; font-weight: 600;")
        if hasattr(self, "_icon_provider"):
            self._icon_provider._folder = QIcon(svg_pixmap("folder", "#dcb67a", 16))
            self.tree.viewport().update()
        # icon activity bar
        for act, name in getattr(self, "_activity", []):
            act.setIcon(make_icon(name, pal["muted"], pal["fg"], pal["fg"]))
        # icon thanh công cụ
        base = _mix(t["fg"], t["bg"], 0.15)
        for act, name, color in getattr(self, "_tb_icons", []):
            act.setIcon(make_icon(name, color or base, color or t["fg"], size=20))
        if hasattr(self, "_pill"):
            self._pill.setIcon(QIcon(svg_pixmap("search", pal["muted"], 16)))
        self._tab_icons = (make_icon("close", pal["muted"], pal["fg"], size=12),
                           make_icon("dot", pal["fg"], pal["fg"], size=12))
        for i in range(self.tabs.count()):
            btn = getattr(self.tabs.widget(i), "_tab_btn", None)
            if btn is not None:
                btn.set_icons(*self._tab_icons)
                btn.set_modified(self.tabs.widget(i).document().isModified())

    def _build_activity_bar(self):
        bar = QToolBar("Activity")
        bar.setObjectName("activityBar")
        bar.setMovable(False)
        bar.setOrientation(Qt.Vertical)
        bar.setAllowedAreas(Qt.LeftToolBarArea)
        bar.setIconSize(QSize(24, 24))
        bar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        bar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.addToolBar(Qt.LeftToolBarArea, bar)
        self.activity = bar
        self._activity = []

        def dock_button(name, tip, dock):
            a = QAction(tip, self)
            a.setCheckable(True)
            a.setToolTip(tip)
            a.setChecked(not dock.isHidden())
            a.toggled.connect(lambda on, d=dock: d.setVisible(on))

            def sync(v, act=a):
                act.blockSignals(True)
                act.setChecked(v)
                act.blockSignals(False)
            dock.visibilityChanged.connect(sync)
            bar.addAction(a)
            self._activity.append((a, name))

        dock_button("explorer", "Thư mục (Ctrl+B)", self.dock)
        dock_button("search", "Tìm trong thư mục (Ctrl+Shift+F)", self.search_dock)
        dock_button("git", "Git (Ctrl+Shift+G)", self.git_dock)
        dock_button("todo", "TODO / FIXME (Ctrl+Alt+T)", self.todo_dock)
        dock_button("esp", "ESP IDE (Ctrl+Alt+E)", self.esp_ide_dock)
        pl = QAction("Plugins", self)
        pl.setToolTip("Plugins")
        pl.triggered.connect(lambda: self.plugins_menu.exec_(QCursor.pos()))
        bar.addAction(pl)
        self._activity.append((pl, "plugins"))
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Preferred, spacer.sizePolicy().Expanding)
        bar.addWidget(spacer)
        st = QAction("Cài đặt", self)
        st.setToolTip("Cài đặt (Ctrl+,)")
        st.triggered.connect(self.open_preferences)
        bar.addAction(st)
        self._activity.append((st, "settings"))

    def _build_command_pill(self, tb):
        left, right = QWidget(), QWidget()
        for w in (left, right):
            w.setSizePolicy(w.sizePolicy().Expanding, w.sizePolicy().Preferred)
        self._pill = QPushButton()
        self._pill.setObjectName("cmdPill")
        self._pill.setCursor(Qt.PointingHandCursor)
        self._pill.setFocusPolicy(Qt.NoFocus)
        self._pill.clicked.connect(self.quick_open)
        tb.addWidget(left)
        tb.addWidget(self._pill)
        tb.addWidget(right)
        self._update_pill()

    def _update_pill(self):
        if not hasattr(self, "_pill"):
            return
        root = self.settings.value("explorer/root", "") or ""
        name = os.path.basename(root) if root else APP_NAME
        self._pill.setText(f"{name}   ·   Ctrl+P để mở nhanh")

    def _upper_dock_titles(self):
        for d in self.findChildren(QDockWidget):
            d.setWindowTitle(d.windowTitle().upper())

    def set_theme(self, theme_name):
        if theme_name not in THEMES:
            return
        self.theme_name = theme_name
        t = THEMES[theme_name]
        self.settings.setValue("ui/theme", theme_name)
        self._paint_theme(t)
        for action, name in getattr(self, "_theme_actions", {}).items():
            action.setChecked(name == theme_name)
        self.emit_event("theme", theme_name)

    def preview_theme(self, t):
        """Xem trước theme (chưa lưu) khi đang chỉnh trong Cài đặt."""
        self._paint_theme(t)

    def _paint_theme(self, t):
        apply_app_palette(t)
        self.setStyleSheet(app_stylesheet(t))
        self._apply_modern_ui(t)
        self.terminal.apply_theme(t)
        if getattr(self, "welcome", None) is not None:
            self.welcome.apply_theme(t)
        if hasattr(self, "console"):
            self.console.apply_theme(t)
            self.repl.apply_theme(t)
        for i in range(self.tabs.count()):
            self.tabs.widget(i).apply_theme(t)

    def _persist_custom_themes(self):
        data = {k: {a: b for a, b in v.items() if isinstance(b, str)} for k, v in THEMES.items() if v.get("custom")}
        self.settings.setValue("ui/custom_themes", json.dumps(data, ensure_ascii=False))

    def save_custom_theme(self, key, t):
        t = dict(t)
        t["custom"] = True
        THEMES[key] = t
        self._persist_custom_themes()
        for act, k in self._theme_actions.items():
            if k == key:
                act.setText(t["label"])
                return
        a = QAction(t["label"], self)
        a.setCheckable(True)
        a.setActionGroup(self._theme_group)
        a.triggered.connect(lambda _=False, kk=key: self.set_theme(kk))
        self._theme_menu.addAction(a)
        self._theme_actions[a] = key

    def delete_custom_theme(self, key):
        if not THEMES.get(key, {}).get("custom"):
            return
        THEMES.pop(key, None)
        self._persist_custom_themes()
        for act, k in list(self._theme_actions.items()):
            if k == key:
                self._theme_menu.removeAction(act)
                self._theme_actions.pop(act, None)
        if self.theme_name == key:
            self.set_theme(DEFAULT_THEME)

    #  minimap / zen / welcome
    def toggle_minimap(self, checked):
        self.show_minimap = bool(checked)
        self.settings.setValue("ui/minimap", self.show_minimap)
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if hasattr(ed, "set_minimap"):
                ed.set_minimap(self.show_minimap)

    def toggle_zen(self):
        """F11: toàn màn hình, ẩn explorer / toolbar / terminal / status bar."""
        st = getattr(self, "_zen", None)
        if st is None:
            hidden = [w for w in (self.findChildren(QDockWidget) + self.findChildren(QToolBar)
                                  + [self.statusBar(), self.bottom]) if w.isVisible()]
            for w in hidden:
                w.hide()
            self._zen = {"hidden": hidden, "max": self.isMaximized()}
            self.showFullScreen()
        else:
            for w in st["hidden"]:
                w.show()
            self._zen = None
            self.showMaximized() if st["max"] else self.showNormal()
        ed = self.current_editor()
        if ed is not None:
            ed.setFocus()

    def welcome_dismiss(self):
        self._welcome_hidden = True
        self._refresh_welcome()
        ed = self.current_editor()
        if ed is not None:
            ed.setFocus()

    def _schedule_welcome(self, *_):
        QTimer.singleShot(0, self._refresh_welcome)

    def _place_welcome(self):
        r = self.tabs.rect()
        r.setTop(self.tabs.tabBar().height())
        self.welcome.setGeometry(r)

    def _refresh_welcome(self):
        w = getattr(self, "welcome", None)
        if w is None:
            return
        show = False
        if self.tabs.count() == 1:
            ed = self.tabs.widget(0)
            doc = ed.document()
            show = (ed.file_path is None and doc.isEmpty() and not doc.isModified())
        if not show:
            self._welcome_hidden = False
        if show and not self._welcome_hidden:
            self._place_welcome()
            w.refresh_recent()
            w.show()
            w.raise_()
        else:
            w.hide()

    def eventFilter(self, obj, ev):
        if (obj is self.tabs and ev.type() == QEvent.Resize
                and getattr(self, "welcome", None) is not None and self.welcome.isVisible()):
            self._place_welcome()
        return super().eventFilter(obj, ev)

    #  drag & drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.open_path(url.toLocalFile())
        event.acceptProposedAction()

    #  progress bar
    def _on_step(self, done, total, label):
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(done - 1)
        self.progress.setFormat(f"{label}... ({done}/{total})")

    def _on_done(self):
        self.progress.setValue(self.progress.maximum())
        self.progress.setFormat("Hoàn tất ✔")

    def _on_fail(self, label, code):
        self.progress.setFormat(f"Thất bại ở bước: {label} (mã {code})")

    #  tabs
    def current_editor(self):
        return self.tabs.currentWidget()

    def new_tab(self, file_path=None, content=""):
        theme = THEMES.get(self.theme_name, THEMES[DEFAULT_THEME])
        lang = get_language(file_path) if file_path else "python"
        editor = CodeEditor(theme, self.font_size, lang)
        editor.setLineWrapMode(QPlainTextEdit.WidgetWidth if self.word_wrap
                               else QPlainTextEdit.NoWrap)
        editor.setPlainText(content)
        editor.file_path = file_path
        editor.document().setModified(False)
        editor.document().modificationChanged.connect(
            lambda _m, e=editor: self._update_tab_title(e))
        editor.cursorPositionChanged.connect(
            lambda e=editor: self.update_status() if e is self.current_editor() else None)
        editor.selectionChanged.connect(
            lambda e=editor: self.update_status() if e is self.current_editor() else None)
        editor.zoomRequested.connect(self.zoom)
        editor.lintChanged.connect(
            lambda e=editor: self.update_lint_label() if e is self.current_editor() else None)
        editor.set_show_whitespace(self.show_ws)
        editor.show_guides = self.show_guides
        editor.set_minimap(self.show_minimap)
        editor.textChanged.connect(self._schedule_welcome)
        editor.set_tab_size(self.tab_size)
        editor.textChanged.connect(
            lambda: self._change_timer.start(300) if self._events.get("change") else None)
        editor.cursorPositionChanged.connect(
            lambda e=editor: self.emit_event("cursor", e)
            if self._events.get("cursor") and e is self.current_editor() else None)
        index = self.tabs.addTab(editor, "")
        # clicked(bool) truyền `checked` vào tham số đầu tiên -> cần _c để không ghi đè ed
        btn = TabCloseButton(lambda _c=False, ed=editor: self.close_tab(self.tabs.indexOf(ed)))
        self.tabs.tabBar().setTabButton(index, QTabBar.RightSide, btn)
        editor._tab_btn = btn          # giữ tham chiếu Python, nếu không PyQt sẽ mất kiểu
        if getattr(self, "_tab_icons", None):
            btn.set_icons(*self._tab_icons)
        self.tabs.setCurrentIndex(index)
        self._update_tab_title(editor)
        editor.setFocus()
        return editor

    def _update_tab_title(self, editor):
        idx = self.tabs.indexOf(editor)
        if idx < 0:
            return
        name = os.path.basename(editor.file_path) if editor.file_path else "untitled.py"
        self.tabs.setTabText(idx, name)
        if editor.file_path and editor.file_path not in self._watcher.files():
            self._watcher.addPath(editor.file_path)
        self.tabs.setTabIcon(idx, badge_icon(os.path.splitext(name)[1]))
        btn = getattr(editor, "_tab_btn", None)
        if btn is not None:
            btn.set_modified(editor.document().isModified())
        editor.update_breadcrumb()
        self.tabs.setTabToolTip(idx, editor.file_path or "Chưa lưu")
        if editor is self.current_editor():
            self._update_window_title()

    def _update_window_title(self):
        ed = self.current_editor()
        if ed is None:
            self.setWindowTitle(f"{APP_NAME} - Python IDE")
            return
        name = os.path.basename(ed.file_path) if ed.file_path else "untitled.py"
        star = "*" if ed.document().isModified() else ""
        self.setWindowTitle(f"{name}{star} - {APP_NAME}")

    def _on_tab_changed(self, _index):
        self.emit_event("tab_change", self.current_editor())
        self._update_window_title()
        self.update_status()
        self.update_lint_label()
        self.findbar.refresh()

    def update_lint_label(self):
        ed = self.current_editor()
        if ed is not None and ed.lint_error:
            self.lint_label.setText(f"⚠ Dòng {ed.lint_error[0]}: {ed.lint_error[1]}")
        elif ed is not None and ed.lint_items:
            more = f" (+{len(ed.lint_items) - 1})" if len(ed.lint_items) > 1 else ""
            self.lint_label.setText(f"⚠ Dòng {ed.lint_items[0][0]}: {ed.lint_items[0][1]}{more}")
        else:
            self.lint_label.setText("")

    def update_status(self):
        ed = self.current_editor()
        if ed is None:
            return
        c = ed.textCursor()
        txt = f"Dòng {c.blockNumber() + 1}, Cột {c.positionInBlock() + 1}"
        sel = len(c.selectedText())
        if sel:
            txt += f"  ({sel} ký tự chọn)"
        self.pos_label.setText(txt)
        self.lang_label.setText(LANGUAGE_LABELS.get(ed.lang, "Văn bản"))
        self.enc_label.setText({"utf-8": "UTF-8", "utf-8-sig": "UTF-8 BOM",
                                "utf-16": "UTF-16"}.get(ed.encoding, ed.encoding.upper()))
        self.eol_label.setText({"\n": "LF", "\r\n": "CRLF", "\r": "CR"}.get(ed.eol, "LF"))

    def close_tab(self, index):
        editor = self.tabs.widget(index)
        if editor is None:
            return
        if not self.maybe_save(editor):
            return
        self.emit_event("tab_close", editor)
        if editor.file_path:
            self._closed_paths.append(editor.file_path)
            del self._closed_paths[:-20]
        self.tabs.removeTab(index)
        editor.deleteLater()
        if self.tabs.count() == 0:
            self.new_tab()
        self._schedule_welcome()

    def close_current_tab(self):
        if self.tabs.count():
            self.close_tab(self.tabs.currentIndex())

    #  file actions
    def open_path(self, path, force_text=False):
        if not path or not os.path.isfile(path):
            return
        head = read_head(path, 64)
        if not force_text and run_openers(self, path, head, by_ext=True, by_sniff=False):
            return
        norm = os.path.normcase(os.path.abspath(path))
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if ed.file_path and os.path.normcase(os.path.abspath(ed.file_path)) == norm:
                self.tabs.setCurrentIndex(i)
                return
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        if size > LARGE_FILE_BYTES:
            self._open_path_async(path, head, size)
            return
        try:
            res = read_text_file_ex(path)
        except OSError as e:
            self.terminal.appendPlainText(f"Không thể mở file: {path} ({e})")
            return
        self._finish_open(path, head, res)

    def _open_path_async(self, path, head, size):
        """File lớn: đọc ở luồng nền, nạp vào editor từng đợt, giao diện luôn phản hồi."""
        if not hasattr(self, "_loaders"):
            self._loaders = {}
        if path in self._loaders:
            return
        self.statusBar().showMessage(f"Đang đọc {os.path.basename(path)} ({human_size(size)})...")
        th = FileLoadThread(path, self)
        self._loaders[path] = th
        th.loaded.connect(lambda p, res, h=head, sz=size: self._on_big_loaded(p, h, res, sz))
        th.failed.connect(lambda p, msg: (self._loaders.pop(p, None),
                                          self.terminal.appendPlainText(f"Không thể mở file: {p} ({msg})")))
        th.finished.connect(th.deleteLater)
        th.start()

    def _on_big_loaded(self, path, head, res, size):
        self._loaders.pop(path, None)
        if res is None:
            self.statusBar().clearMessage()
            self._finish_open(path, head, None)
            return
        content, enc, eol, truncated = res
        reuse = self._reusable_blank_tab()
        self._add_recent(path)
        new_ed = self.new_tab(file_path=path, content="")
        new_ed.encoding, new_ed.eol = enc, eol
        huge = size > HUGE_FILE_BYTES or truncated
        new_ed.truncated = truncated
        if huge:
            new_ed.set_large_mode(True)
        name = os.path.basename(path)

        def done():
            new_ed.document().setModified(False)
            note = " (chế độ file lớn: tắt tô màu cú pháp)" if huge else ""
            if truncated:
                new_ed.setReadOnly(True)
                note = " — CHỈ ĐỌC: có dòng quá dài đã bị cắt khi hiển thị, không thể lưu đè file gốc"
            self.statusBar().showMessage(f"Đã mở {name}{note}", 6000)
            self.update_status()
            self.emit_event("open", new_ed)
        new_ed.load_text_chunked(
            content, on_done=done,
            on_progress=lambda a, b: self.statusBar().showMessage(f"Đang nạp {name}: {a * 100 // b}%"))
        if reuse is not None:
            self.tabs.removeTab(self.tabs.indexOf(reuse))
            reuse.deleteLater()

    def _reusable_blank_tab(self):
        if self.tabs.count() == 1:
            ed = self.tabs.widget(0)
            if ed.file_path is None and not ed.document().isModified() and not ed.toPlainText():
                return ed
        return None

    def _finish_open(self, path, head, res):
        content = res[0] if res else None
        if content is None:
            if run_openers(self, path, head, by_ext=False, by_sniff=True):
                return
            self.terminal.appendPlainText(f"Bỏ qua file nhị phân: {path}")
            return
        reuse = self._reusable_blank_tab()
        self._add_recent(path)
        new_ed = self.new_tab(file_path=path, content=content)
        new_ed.encoding, new_ed.eol = res[1], res[2]
        self.update_status()
        if reuse is not None:
            self.tabs.removeTab(self.tabs.indexOf(reuse))
            reuse.deleteLater()
        self.emit_event("open", new_ed)

    def open_file(self):
        start = self.settings.value("ui/last_dir", "")
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open File", start,
            "Code Files (*.py *.pyw *.c *.h *.cpp *.cc *.hpp *.go *.java *.js "
            "*.json);;All Files (*)")
        for p in paths:
            self.open_path(p)
        if paths:
            self.settings.setValue("ui/last_dir", os.path.dirname(paths[0]))

    def open_folder(self):
        d = QFileDialog.getExistingDirectory(
            self, "Mở thư mục", self.settings.value("explorer/root", ""))
        if d:
            self._set_explorer_root(d)

    def _set_explorer_root(self, folder):
        self.fs_model.setRootPath(folder)
        self.tree.setRootIndex(self.fs_model.index(folder))
        self.dock.setWindowTitle((os.path.basename(folder) or folder).upper())
        self._update_pill()
        self.dock.show()
        self.settings.setValue("explorer/root", folder)

    def _on_tree_double_click(self, index):
        path = self.fs_model.filePath(index)
        if os.path.isfile(path):
            self.open_path(path)

    def _write_file(self, editor, path):
        if getattr(editor, "truncated", False):
            QMessageBox.warning(self, "Chỉ đọc", "File này được mở ở dạng rút gọn (có dòng quá dài bị cắt) "
                                "nên không thể lưu, để tránh làm mất dữ liệu gốc.")
            return False
        if self.trim_on_save:
            editor.normalize_for_save()
        text = editor.toPlainText()
        if editor.eol != "\n":
            text = text.replace("\n", editor.eol)
        try:
            data = text.encode(editor.encoding)
        except (UnicodeEncodeError, LookupError):
            if QMessageBox.question(
                    self, "Mã hóa",
                    f"Nội dung có ký tự không lưu được bằng {editor.encoding}.\n"
                    "Lưu bằng UTF-8?") != QMessageBox.Yes:
                return False
            editor.encoding = "utf-8"
            data = text.encode("utf-8")
        try:
            _atomic_write_bytes(path, data)
        except OSError as e:
            QMessageBox.critical(self, "Lỗi lưu file", f"Không thể lưu:\n{path}\n\n{e}")
            return False
        return True

    def _save_editor(self, editor, force_dialog=False, quiet=False):
        path = editor.file_path
        if not path or force_dialog:
            start = path or os.path.join(self.settings.value("ui/last_dir", ""),
                                         "untitled.py")
            path, _ = QFileDialog.getSaveFileName(
                self, "Save As", start,
                "Python (*.py);;C (*.c);;C++ (*.cpp);;Go (*.go);;Java (*.java);;"
                "JavaScript (*.js);;JSON (*.json);;All Files (*)")
            if not path:
                return False
            if not os.path.splitext(path)[1]:
                path += ".py"
        if not self._write_file(editor, path):
            return False
        editor.file_path = path
        editor.set_language(get_language(path))
        editor.document().setModified(False)
        self.settings.setValue("ui/last_dir", os.path.dirname(path))
        self._add_recent(path)
        self._update_tab_title(editor)
        self.update_status()
        if quiet:
            self.statusBar().showMessage(f"Tự lưu: {os.path.basename(path)}", 2000)
        else:
            self.terminal.appendPlainText(f"Saved: {path}")
        self.emit_event("save", editor)
        return True

    def save_file(self):
        ed = self.current_editor()
        return self._save_editor(ed) if ed else False

    def save_file_as(self):
        ed = self.current_editor()
        return self._save_editor(ed, force_dialog=True) if ed else False

    def save_all(self):
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if ed.document().isModified():
                self.tabs.setCurrentIndex(i)
                if not self._save_editor(ed):
                    return

    def maybe_save(self, editor):
        if not editor.document().isModified():
            return True
        self.tabs.setCurrentWidget(editor)
        name = os.path.basename(editor.file_path) if editor.file_path else "untitled.py"
        r = QMessageBox.question(
            self, "Lưu thay đổi?", f"'{name}' có thay đổi chưa lưu.\nBạn muốn lưu không?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save)
        if r == QMessageBox.Save:
            return self._save_editor(editor)
        return r == QMessageBox.Discard

    #  phiên
    def _restore_session(self):
        try:
            files = json.loads(self.settings.value("session/files", "[]") or "[]")
            current = int(self.settings.value("session/current", 0))
        except (ValueError, TypeError):
            return
        for p in files:
            if os.path.isfile(p):
                self.open_path(p)
        if 0 <= current < self.tabs.count():
            self.tabs.setCurrentIndex(current)
        prev = self.tabs.currentIndex()
        try:
            untitled = json.loads(self.settings.value("session/untitled", "[]") or "[]")
        except (ValueError, TypeError):
            untitled = []
        for u in untitled:
            ed = self.new_tab(content=u.get("text", ""))
            ed.set_language(u.get("lang", "python"))
            ed.document().setModified(True)
        if untitled and prev >= 0 and self.tabs.count() > len(untitled):
            self.tabs.setCurrentIndex(prev)

    def _save_session(self):
        paths, current = [], 0
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if ed.file_path:
                if i == self.tabs.currentIndex():
                    current = len(paths)
                paths.append(ed.file_path)
        untitled = []
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if not ed.file_path and ed.toPlainText().strip():
                untitled.append({"lang": ed.lang, "text": ed.toPlainText()[:200000]})
        self.settings.setValue("session/untitled", json.dumps(untitled))
        self.settings.setValue("session/files", json.dumps(paths))
        self.settings.setValue("session/current", current)
        self.settings.setValue("ui/geometry", self.saveGeometry())
        self.settings.setValue("ui/state", self.saveState())
        self.settings.setValue("ui/font_size", self.font_size)
        self.settings.setValue("ui/wrap", self.word_wrap)
        self.settings.setValue("ui/guides", self.show_guides)
        self.settings.setValue("edit/tab_size", self.tab_size)
        self.settings.setValue("edit/autosave_secs", self.autosave_secs)

    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            # tab chưa đặt tên được tự giữ lại cho lần mở sau nên không cần hỏi
            if ed.file_path and not self.maybe_save(ed):
                event.ignore()
                return
        self.emit_event("quit")
        self._tools_shutdown()
        self.unload_plugins()
        if self.serial_monitor is not None:
            self.serial_monitor.close_port()
        self.terminal.stop(silent=True)
        self._save_session()
        event.accept()

    #  xem / zoom
    def zoom(self, delta):
        if delta == 0:
            self.font_size = 11
        else:
            self.font_size = max(7, min(40, self.font_size + delta))
        for i in range(self.tabs.count()):
            self.tabs.widget(i).set_font_size(self.font_size)

    def toggle_wrap(self, checked):
        self.word_wrap = checked
        mode = QPlainTextEdit.WidgetWidth if checked else QPlainTextEdit.NoWrap
        for i in range(self.tabs.count()):
            self.tabs.widget(i).setLineWrapMode(mode)

    def goto_line_dialog(self):
        ed = self.current_editor()
        if ed is None:
            return
        n, ok = QInputDialog.getInt(
            self, "Đi tới dòng", f"Số dòng (1 - {ed.blockCount()}):",
            ed.textCursor().blockNumber() + 1, 1, max(1, ed.blockCount()))
        if ok:
            ed.goto_line(n)
            ed.setFocus()

    def _editor_do(self, method, *args):
        ed = self.current_editor()
        if ed is not None:
            getattr(ed, method)(*args)

    def toggle_terminal(self, checked):
        self.bottom.setVisible(checked)

    #  build
    def build_to_exe(self):
        try:
            self._build_to_exe_impl()
        except Exception:
            self.terminal.appendPlainText(
                "\n>>> LỖI khi build EXE:\n" + traceback.format_exc())

    def _build_to_exe_impl(self):
        editor = self.current_editor()
        if editor is None or not self._save_editor(editor):
            return
        file_path = editor.file_path
        lang = get_language(file_path)
        if lang == "arduino":
            self._run_arduino(editor, "export")
            return
        if lang not in RUNNABLE:
            QMessageBox.warning(
                self, "Chưa hỗ trợ",
                "Chưa hỗ trợ build loại file này (chỉ hỗ trợ: .py .c .cpp .go .java .js .ino).")
            return

        file_dir = os.path.dirname(file_path)
        default_name = os.path.splitext(os.path.basename(file_path))[0]
        dialog = BuildOptionsDialog(self, self.settings, default_name,
                                    os.path.join(file_dir, "dist"), lang)
        if dialog.exec_() != QDialog.Accepted:
            return
        v = dialog.get_values()
        dialog.save_to_settings()
        name, out_dir = v["name"], v["out_dir"]
        if not name or not out_dir:
            QMessageBox.warning(self, "Thiếu thông tin",
                                "Cần nhập tên file và thư mục xuất.")
            return
        os.makedirs(out_dir, exist_ok=True)

        py_cmd = get_python_command() if lang == "python" else None
        if lang == "python" and py_cmd is None:
            QMessageBox.critical(
                self, "Không tìm thấy Python",
                "Máy này chưa cài Python (hoặc Python không nằm trong PATH).\n"
                "Để build EXE, máy cần có Python thật cài sẵn.\n"
                "Hãy cài Python từ python.org và tick 'Add to PATH' khi cài, "
                "rồi mở lại app.")
            return

        packages = (detect_third_party_imports(editor.toPlainText(), file_dir)
                    if lang == "python" else [])
        steps, output_hint, error, cleanup = get_build_steps(
            file_path, name, out_dir, lang, py_cmd, packages)
        if error:
            QMessageBox.critical(self, "Không thể build", error)
            return
        if packages:
            self.terminal.appendPlainText(
                f"Phát hiện thư viện cần cài: {', '.join(packages)}")

        if lang == "python":
            work = os.path.join(out_dir, "_build")
            args = ["-m", "PyInstaller", "--noconfirm", "--clean",
                    "--onefile" if v["onefile"] else "--onedir",
                    "--console" if v["console"] else "--windowed",
                    "--workpath", work, "--specpath", work]
            if v["icon_path"]:
                args += ["--icon", v["icon_path"]]
            for h in v["hidden"]:
                args += ["--hidden-import", h]
            for line in v["add_data"]:
                args += ["--add-data", line.replace(";", os.pathsep)]
            args += ["--name", name, "--distpath", out_dir, file_path]
            steps.append(("Build EXE", py_cmd[0], py_cmd[1:] + args))
            if v["clean"]:
                cleanup = cleanup + [work]

        def done():
            self.terminal.appendPlainText(f"Kết quả: {os.path.join(out_dir, output_hint.split(' ')[0])}")
            self._on_done()
            if v["open_out"]:
                QDesktopServices.openUrl(QUrl.fromLocalFile(out_dir))

        self.terminal.run_queue(steps, on_done=done, on_step=self._on_step,
                                on_fail=self._on_fail, cwd=file_dir,
                                cleanup_paths=cleanup)

    #  run
    def run_current_file(self, pre_steps=None):
        """F5: chạy nội dung đang gõ trong editor (không cần lưu)."""
        try:
            editor = self.current_editor()
            if editor is None:
                return
            if self._run_special(editor):
                return
            if editor.lang == "arduino":
                self._run_arduino(editor, "run")
                return
            if self.autosave_before_run and editor.document().isModified():
                self._saving_for_run = True
                try:
                    saved = self._save_editor(editor)
                finally:
                    self._saving_for_run = False
                if not saved:
                    return
            use_buffer = editor.document().isModified() or not editor.file_path
            self._launch(editor.lang, editor.file_path, editor.toPlainText(),
                         use_buffer, pre_steps)
        except Exception:
            self.terminal.appendPlainText(
                "\n>>> LỖI khi chạy file:\n" + traceback.format_exc())

    def _run_arduino(self, ed, mode="run"):
        """F5 / F6 / F7 trên sketch .ino - dùng ESP IDE (arduino-cli, hoặc PlatformIO nếu có platformio.ini).
        run    = biên dịch + nạp + mở Serial Monitor (chưa chọn cổng COM -> chỉ biên dịch)
        export = biên dịch + xuất firmware (.bin/.elf...) ra thư mục build/ rồi mở thư mục đó
        build  = chỉ biên dịch để xem lỗi / cảnh báo, không nạp"""
        try:
            if ed is None:
                return
            if not ed.file_path and not self._save_editor(ed):
                return
            if not self.esp_ide_dock.isVisible():
                self.esp_ide_dock.show()      # để thấy board / cổng, thanh Flash-RAM và danh sách lỗi
            panel = self.esp_ide
            action = mode
            if mode == "run":
                if panel.port_name():
                    action = "upload_monitor"
                else:
                    action = "build"
                    self.terminal.appendPlainText(
                        "[Chưa chọn cổng COM trong ESP IDE → chỉ biên dịch, không nạp. "
                        "Cắm board, bấm ⟳ rồi nhấn F5 lại để nạp.]")
            self._rerun = lambda pre, e=ed, m=mode: self._run_arduino(e, m)
            panel.run(action)
        except Exception:
            self.terminal.appendPlainText(
                "\n>>> LỖI khi chạy sketch Arduino:\n" + traceback.format_exc())

    def run_selection(self):
        """F9: chạy đoạn đang chọn (hoặc dòng hiện tại)."""
        editor = self.current_editor()
        if editor is None:
            return
        code = editor.selected_code()
        if not code.strip():
            return
        if editor.lang == "python":
            code = textwrap.dedent(code)
        if not code.endswith("\n"):
            code += "\n"
        self._launch(editor.lang, editor.file_path, code, True,
                     title="đoạn code đang chọn")

    def _launch(self, lang, orig, code, use_buffer, pre_steps=None, title=None):
        if lang == "arduino":
            QMessageBox.information(
                self, "Sketch Arduino",
                "Sketch .ino không chạy riêng từng đoạn.\n"
                "F5: biên dịch + nạp (+ Serial Monitor)  ·  F6: xuất firmware  ·  F7: chỉ biên dịch.")
            return
        if lang not in RUNNABLE:
            QMessageBox.warning(
                self, "Chưa hỗ trợ",
                "Chưa hỗ trợ chạy loại file này (chỉ hỗ trợ: .py .c .cpp .go .java .js .ino).")
            return
        py_cmd = get_python_command() if lang == "python" else None
        if lang == "python" and py_cmd is None:
            QMessageBox.critical(
                self, "Không tìm thấy Python",
                "Máy này chưa cài Python (hoặc Python không nằm trong PATH).\n"
                "Hãy cài Python từ python.org và tick 'Add to PATH' khi cài.")
            return

        run_path, cleanup, path_map = orig, [], {}
        cwd = os.path.dirname(orig) if orig else None
        if use_buffer or not orig:
            ext = os.path.splitext(orig)[1] if orig else LANG_EXT[lang]
            base = os.path.splitext(os.path.basename(orig))[0] if orig else "untitled"
            try:
                if orig and lang != "java":
                    # cạnh file thật để import / đường dẫn tương đối vẫn đúng
                    run_path = os.path.join(os.path.dirname(orig), f"_tmp_run_{base}{ext}")
                    cleanup.append(run_path)
                else:
                    tmpdir = tempfile.mkdtemp(prefix="pyapp_")
                    cleanup.append(tmpdir)
                    run_path = os.path.join(tmpdir, base + ext)
                with open(run_path, "w", encoding="utf-8",
                          newline="\r\n" if lang == "batch" else "\n") as f:
                    f.write(code)
            except OSError as e:
                QMessageBox.critical(self, "Lỗi", f"Không tạo được file tạm:\n{e}")
                return
            cwd = os.path.dirname(orig) if orig else os.path.expanduser("~")
            path_map = {run_path: orig or f"{base}{ext}"}

        steps, error, extra = get_run_steps(run_path, lang, py_cmd)
        if error:
            for p in cleanup:
                shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else None
            QMessageBox.critical(self, "Thiếu công cụ", error)
            return
        extra_args = self._run_args_for(orig)
        if extra_args and steps:
            lbl, prog, a = steps[-1]
            steps[-1] = (lbl, prog, list(a) + extra_args)
        steps = list(pre_steps or []) + steps
        what = title or ("bản đang gõ (chưa lưu)" if use_buffer else "file")
        name = os.path.basename(orig) if orig else "untitled"
        self.terminal.appendPlainText(
            f"\n=== Chạy {what} ({LANGUAGE_LABELS.get(lang, lang)}): {name} ===")
        self._rerun = lambda pre, a=(lang, orig, code, use_buffer, title): \
            self._launch(*a, pre_steps=pre)
        self.terminal.input.setFocus()
        self.emit_event("run", self.current_editor())
        self.terminal.run_queue(
            steps, on_done=lambda: (self._on_done(), self.emit_event("run_done", self.current_editor())),
            on_step=self._on_step,
            on_fail=lambda label, c, lg=lang: self._on_run_fail(label, c, lg),
            cwd=cwd, cleanup_paths=cleanup + extra, path_map=path_map)

    def _on_run_fail(self, label, code, lang):
        self._on_fail(label, code)
        if lang != "python":
            return
        missing = re.findall(r"No module named '([\w\.]+)'", self.terminal.last_output)
        if missing:
            mod = missing[-1].split(".")[0]
            pkg = PIP_NAME_MAP.get(mod, mod)
            QTimer.singleShot(0, lambda: self._offer_install(pkg))

    def _offer_install(self, pkg):
        r = QMessageBox.question(
            self, "Thiếu thư viện",
            f"Chương trình cần thư viện '{pkg}' nhưng chưa được cài.\n"
            "Cài ngay rồi chạy lại?")
        if r != QMessageBox.Yes or self._rerun is None:
            return
        py_cmd = get_python_command()
        if py_cmd is None:
            return
        pre = [(f"Cài {pkg}", py_cmd[0],
                py_cmd[1:] + ["-m", "pip", "install", "--disable-pip-version-check", pkg])]
        self._rerun(pre)

    def install_libs_for_current(self):
        ed = self.current_editor()
        if ed is None or ed.lang != "python":
            QMessageBox.information(self, "Cài thư viện", "Chỉ áp dụng cho file Python.")
            return
        py_cmd = get_python_command()
        if py_cmd is None:
            QMessageBox.critical(self, "Không tìm thấy Python",
                                 "Máy này chưa cài Python (hoặc không nằm trong PATH).")
            return
        local = os.path.dirname(ed.file_path) if ed.file_path else None
        packages = detect_third_party_imports(ed.toPlainText(), local)
        if not packages:
            QMessageBox.information(self, "Cài thư viện",
                                    "Không phát hiện thư viện bên thứ ba nào cần cài.")
            return
        extra, done = [], self._on_done
        if is_plugin_file(ed.file_path):
            # plugin chạy bên trong app nên thư viện phải nằm trong ~/.pyapp/libs
            packages = [p for p in packages if not p.lower().startswith("pyqt5")]
            if not packages:
                QMessageBox.information(
                    self, "Cài thư viện",
                    "Plugin này chỉ dùng module Qt (PyQt5), vốn nằm sẵn trong app và không "
                    "cài được bằng pip. Nếu báo thiếu module Qt, cần build lại app với module đó "
                    "trong py_app.spec (hiddenimports).")
                return
            extra = ["--upgrade", "--target", user_libs_dir()]
            done = self._after_plugin_libs
        self.terminal.appendPlainText(f"\nThư viện cần cài: {', '.join(packages)}")
        steps = [("Cài thư viện", py_cmd[0],
                  py_cmd[1:] + ["-m", "pip", "install",
                                "--disable-pip-version-check"] + extra + packages)]
        self.terminal.run_queue(steps, on_done=done, on_step=self._on_step,
                                on_fail=self._on_fail)

    def diagnose_media(self):
        """Tools → Chẩn đoán đa phương tiện: in ra backend / định dạng mà Qt phát được."""
        out = ["", "=== Chẩn đoán đa phương tiện ==="]
        try:
            from PyQt5.QtMultimedia import QMediaPlayer
        except Exception as e:
            out.append(f"Không nạp được QtMultimedia: {e}")
        else:
            out.append("QT_MULTIMEDIA_PREFERRED_PLUGINS = "
                       + os.environ.get("QT_MULTIMEDIA_PREFERRED_PLUGINS", "(chưa đặt)"))
            for mime in ("video/mp4", "video/x-matroska", "video/webm", "audio/mpeg"):
                out.append(f"hasSupport({mime}) = {int(QMediaPlayer.hasSupport(mime))}"
                           "   (0 = không phát được, 1-3 = có)")
            for lp in QApplication.libraryPaths():
                d = os.path.join(lp, "mediaservice")
                names = sorted(os.listdir(d)) if os.path.isdir(d) else None
                out.append(f"{d}: {names if names is not None else 'KHÔNG CÓ THƯ MỤC'}")
        self.terminal.appendPlainText("\n".join(out))

    def _after_plugin_libs(self, reload=False):
        importlib.invalidate_caches()
        self._on_done()
        if reload:
            self.load_plugins()
            return
        self.statusBar().showMessage("Đã cài thư viện cho plugin. Plugins → nạp lại để áp dụng.",
                                     8000)

    def install_plugin_libs(self):
        """Tools → Cài thư viện cho plugin: pip install --target ~/.pyapp/libs."""
        py_cmd = get_python_command()
        if py_cmd is None:
            QMessageBox.critical(self, "Không tìm thấy Python",
                                 "Máy này chưa cài Python (hoặc không nằm trong PATH).")
            return
        text, ok = QInputDialog.getText(
            self, "Cài thư viện cho plugin",
            "Tên thư viện, cách nhau bằng dấu cách (ví dụ: requests pillow numpy).\n"
            f"Sẽ cài vào: {user_libs_dir()}")
        if not ok or not text.strip():
            return
        pkgs = text.split()
        bad = [p for p in pkgs if p.startswith("-") or not re.fullmatch(r"[A-Za-z0-9_.\-\[\],<>=!~]+", p)]
        if bad:
            QMessageBox.warning(self, "Cài thư viện", f"Tên không hợp lệ: {', '.join(bad)}")
            return
        if any(p.lower().startswith("pyqt5") for p in pkgs):
            QMessageBox.information(
                self, "Cài thư viện",
                "PyQt5 đã nằm sẵn trong app, không cài thêm. Nếu thiếu module Qt (ví dụ "
                "QtMultimedia) thì cần build lại app: thêm module đó vào hiddenimports trong "
                "py_app.spec.")
            return
        self.terminal.appendPlainText(f"\nCài cho plugin: {', '.join(pkgs)}")
        steps = [("Cài thư viện cho plugin", py_cmd[0],
                  py_cmd[1:] + ["-m", "pip", "install", "--disable-pip-version-check",
                                "--upgrade", "--target", user_libs_dir()] + pkgs)]
        self.terminal.run_queue(steps, on_done=self._after_plugin_libs, on_step=self._on_step,
                                on_fail=self._on_fail)

    #  gần đây / điều hướng
    def _add_recent(self, path):
        path = os.path.abspath(path)
        try:
            lst = json.loads(self.settings.value("recent/files", "[]") or "[]")
        except (ValueError, TypeError):
            lst = []
        lst = [p for p in lst if p != path]
        lst.insert(0, path)
        self.settings.setValue("recent/files", json.dumps(lst[:12]))

    def _rebuild_recent_menu(self):
        self.recent_menu.clear()
        try:
            lst = json.loads(self.settings.value("recent/files", "[]") or "[]")
        except (ValueError, TypeError):
            lst = []
        lst = [p for p in lst if os.path.isfile(p)]
        if not lst:
            self.recent_menu.addAction("(trống)").setEnabled(False)
            return
        for p in lst:
            a = QAction(p, self)
            a.triggered.connect(lambda _=False, q=p: self.open_path(q))
            self.recent_menu.addAction(a)

    def _project_root(self):
        root = self.settings.value("explorer/root", "")
        if root and os.path.isdir(root):
            return root
        ed = self.current_editor()
        if ed is not None and ed.file_path:
            return os.path.dirname(ed.file_path)
        return os.getcwd()

    @staticmethod
    def _iter_project_files(root, limit=20000):
        n = 0
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in TEXT_EXTS:
                    yield os.path.join(dirpath, fn)
                    n += 1
                    if n >= limit:
                        return

    def command_palette(self):
        items = []

        def clean(t):
            return t.replace("&&", "\0").replace("&", "").replace("\0", "&")

        def walk(menu, prefix):
            for a in menu.actions():
                if a.isSeparator():
                    continue
                text = clean(a.text())
                if a.menu() is not None:
                    walk(a.menu(), prefix + text + " › ")
                    continue
                if not text:
                    continue
                sc = a.shortcut().toString()
                items.append((prefix + text + (f"    [{sc}]" if sc else ""), a))

        for ma in self.menuBar().actions():
            if ma.menu() is not None:
                walk(ma.menu(), clean(ma.text()) + " › ")
        dlg = PickerDialog(self, "Command Palette", items, "Gõ tên lệnh...")
        if dlg.exec_() == QDialog.Accepted and dlg.selected() is not None:
            dlg.selected().trigger()

    def quick_open(self):
        root = self._project_root()
        items = [(os.path.relpath(p, root), p)
                 for p in self._iter_project_files(root, 5000)]
        dlg = PickerDialog(self, f"Mở nhanh file - {root}", items, "Gõ tên file...")
        if dlg.exec_() == QDialog.Accepted and dlg.selected():
            self.open_path(dlg.selected())

    def goto_symbol(self):
        ed = self.current_editor()
        if ed is None:
            return
        items = []
        for n, line in enumerate(ed.toPlainText().split("\n"), 1):
            m = OUTLINE_GENERIC.match(line)
            if not m and ed.lang in ("c", "cpp", "java", "arduino") and not line.rstrip().endswith(";"):
                m = OUTLINE_CFUNC.match(line)
                if m and m.group(1) in OUTLINE_SKIP:
                    m = None
            if m:
                items.append((f"{n:>5}   {line.strip()[:100]}", n))
        if not items:
            self.statusBar().showMessage("Không tìm thấy hàm/class nào", 3000)
            return
        dlg = PickerDialog(self, "Đi tới hàm / class", items, "Gõ để lọc...")
        if dlg.exec_() == QDialog.Accepted and dlg.selected():
            ed.goto_line(dlg.selected())
            ed.setFocus()

    #  tìm trong thư mục
    def _build_search_dock(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 4, 4, 4)
        row = QHBoxLayout()
        self.fif_edit = QLineEdit()
        self.fif_edit.setPlaceholderText("Tìm trong thư mục (Enter)...")
        self.fif_case = QCheckBox("Aa")
        btn = QPushButton("Tìm")
        row.addWidget(self.fif_edit, 1)
        row.addWidget(self.fif_case)
        row.addWidget(btn)
        self.fif_list = QListWidget()
        self.fif_status = QLabel("")
        row2 = QHBoxLayout()
        self.fif_replace = QLineEdit()
        self.fif_replace.setPlaceholderText("Thay bằng... (ghi thẳng ra đĩa)")
        rbtn = QPushButton("Thay tất cả")
        row2.addWidget(self.fif_replace, 1)
        row2.addWidget(rbtn)
        rbtn.clicked.connect(self.replace_in_files)
        v.addLayout(row)
        v.addLayout(row2)
        v.addWidget(self.fif_list, 1)
        v.addWidget(self.fif_status)
        self.search_dock = QDockWidget("Tìm trong thư mục", self)
        self.search_dock.setObjectName("searchDock")
        self.search_dock.setWidget(w)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.search_dock)
        self.search_dock.hide()
        self.fif_edit.returnPressed.connect(self.find_in_files)
        btn.clicked.connect(self.find_in_files)
        self.fif_list.itemActivated.connect(self._open_search_result)

    def show_find_in_files(self):
        ed = self.current_editor()
        if ed is not None:
            sel = ed.textCursor().selectedText()
            if sel and "\u2029" not in sel:
                self.fif_edit.setText(sel)
        self.search_dock.show()
        self.fif_edit.setFocus()
        self.fif_edit.selectAll()

    def find_in_files(self):
        q = self.fif_edit.text()
        if not q:
            return
        root = self._project_root()
        case = self.fif_case.isChecked()
        needle = q if case else q.lower()
        self.fif_list.clear()
        count = files = 0
        for path in self._iter_project_files(root):
            try:
                if os.path.getsize(path) > 2000000:
                    continue
                text = read_text_file(path)
            except OSError:
                continue
            if text is None:
                continue
            files += 1
            for ln, line in enumerate(text.split("\n"), 1):
                if needle in (line if case else line.lower()):
                    it = QListWidgetItem(
                        f"{os.path.relpath(path, root)}:{ln}   {line.strip()[:140]}")
                    it.setData(Qt.UserRole, (path, ln))
                    self.fif_list.addItem(it)
                    count += 1
                    if count >= 1000:
                        break
            if count >= 1000:
                break
            if files % 40 == 0:
                QApplication.processEvents()
        self.fif_status.setText(
            f"{count} kết quả trong {files} file" + (" (đã cắt bớt)" if count >= 1000 else ""))

    def _open_search_result(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        path, ln = data
        self.open_path(path)
        ed = self.current_editor()
        if ed is not None and ed.file_path and \
                os.path.normcase(os.path.abspath(ed.file_path)) == \
                os.path.normcase(os.path.abspath(path)):
            ed.goto_line(ln)
            ed.setFocus()

    #  định dạng
    def format_code(self):
        ed = self.current_editor()
        if ed is None:
            return
        code = ed.toPlainText()
        if ed.lang == "json":
            try:
                new = json.dumps(json.loads(code), indent=2, ensure_ascii=False) + "\n"
            except ValueError as e:
                QMessageBox.warning(self, "Định dạng JSON", f"JSON không hợp lệ:\n{e}")
                return
            ed.replace_all_text(new)
            return
        if ed.lang != "python":
            QMessageBox.information(self, "Định dạng",
                                    "Hiện hỗ trợ định dạng Python (black) và JSON.")
            return
        py = get_python_command()
        if py is None:
            QMessageBox.critical(self, "Không tìm thấy Python",
                                 "Máy này chưa cài Python (hoặc không nằm trong PATH).")
            return
        try:
            r = subprocess.run(
                py + ["-m", "black", "-q", "-"], input=code.encode("utf-8"),
                capture_output=True, timeout=60,
                creationflags=0x08000000 if os.name == "nt" else 0)
        except (OSError, subprocess.TimeoutExpired) as e:
            QMessageBox.warning(self, "Không thể định dạng", str(e))
            return
        err = r.stderr.decode("utf-8", "replace")
        if r.returncode == 0:
            ed.replace_all_text(r.stdout.decode("utf-8"))
            self.statusBar().showMessage("Đã định dạng bằng black", 3000)
        elif "No module named black" in err:
            if QMessageBox.question(
                    self, "Thiếu black",
                    "Chưa cài 'black' để định dạng code. Cài ngay?") == QMessageBox.Yes:
                self.terminal.run_queue(
                    [("Cài black", py[0], py[1:] + ["-m", "pip", "install",
                                                    "--disable-pip-version-check", "black"])],
                    on_done=self._on_done, on_step=self._on_step, on_fail=self._on_fail)
        else:
            QMessageBox.warning(self, "Không thể định dạng", err[-1500:])

    def toggle_autosave_run(self, checked):
        self.autosave_before_run = checked
        self.settings.setValue("run/autosave", checked)

    def toggle_trim_on_save(self, checked):
        self.trim_on_save = checked
        self.settings.setValue("edit/trim_on_save", checked)

    def toggle_whitespace(self, checked):
        self.show_ws = checked
        self.settings.setValue("ui/show_ws", checked)
        for i in range(self.tabs.count()):
            self.tabs.widget(i).set_show_whitespace(checked)

    #  thay thế trong thư mục
    def replace_in_files(self):
        q = self.fif_edit.text()
        if not q:
            return
        rep_text = self.fif_replace.text()
        root = self._project_root()
        rx = re.compile(re.escape(q), 0 if self.fif_case.isChecked() else re.IGNORECASE)
        dirty = {os.path.normcase(os.path.abspath(self.tabs.widget(i).file_path))
                 for i in range(self.tabs.count())
                 if self.tabs.widget(i).file_path and self.tabs.widget(i).document().isModified()}
        hits, skipped = [], []
        for path in self._iter_project_files(root):
            try:
                if os.path.getsize(path) > 2000000:
                    continue
                res = read_text_file_ex(path)
            except OSError:
                continue
            if res is None:
                continue
            n = len(rx.findall(res[0]))
            if not n:
                continue
            if os.path.normcase(os.path.abspath(path)) in dirty:
                skipped.append(path)          # tab đang sửa dở: không ghi đè
                continue
            hits.append((path, n, res))
        if not hits:
            self.fif_status.setText("Không có gì để thay" + (
                f" ({len(skipped)} file đang sửa dở bị bỏ qua)" if skipped else ""))
            return
        total = sum(h[1] for h in hits)
        if QMessageBox.question(
                self, "Thay trong thư mục",
                f"Thay {total} chỗ trong {len(hits)} file?\n'{q}' → '{rep_text}'\n\n"
                "Thao tác ghi thẳng ra đĩa và không hoàn tác được.") != QMessageBox.Yes:
            return
        done_files = done_n = 0
        for path, n, (text, enc, eol) in hits:
            new = rx.sub(lambda _m: rep_text, text)
            if eol != "\n":
                new = new.replace("\n", eol)
            try:
                with open(path, "wb") as f:
                    f.write(new.encode(enc))
                done_files += 1
                done_n += n
            except (OSError, UnicodeEncodeError, LookupError):
                skipped.append(path)
        msg = f"Đã thay {done_n} chỗ trong {done_files} file"
        if skipped:
            msg += f" (bỏ qua {len(skipped)} file)"
        self.fif_status.setText(msg)
        self.terminal.appendPlainText("[thay thế] " + msg)

    #  menu chuột phải của Explorer
    @staticmethod
    def _safe_filename(name):
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", (name or "").strip())
        return "" if name in ("", ".", "..") else name

    def _tree_menu(self, pos):
        idx = self.tree.indexAt(pos)
        path = self.fs_model.filePath(idx) if idx.isValid() else self._project_root()
        folder = path if os.path.isdir(path) else os.path.dirname(path)
        m = QMenu(self)
        m.addAction("File mới...").triggered.connect(lambda: self._explorer_new(folder, False))
        m.addAction("Thư mục mới...").triggered.connect(lambda: self._explorer_new(folder, True))
        if idx.isValid():
            m.addSeparator()
            m.addAction("Đổi tên...").triggered.connect(lambda: self._explorer_rename(path))
            m.addAction("Xóa...").triggered.connect(lambda: self._explorer_delete(path))
            m.addSeparator()
            m.addAction("Chép đường dẫn").triggered.connect(
                lambda: QApplication.clipboard().setText(path))
            m.addAction("Mở trong trình quản lý file").triggered.connect(
                lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(folder)))
        if self._explorer_actions:
            m.addSeparator()
            for text, cb in self._explorer_actions:
                m.addAction(text).triggered.connect(lambda _=False, c=cb, p=path: c(p))
        m.exec_(self.tree.viewport().mapToGlobal(pos))

    def _explorer_new(self, folder, is_dir):
        name, ok = QInputDialog.getText(self, "Mới", "Tên thư mục:" if is_dir else "Tên file:")
        name = self._safe_filename(name) if ok else ""
        if not name:
            return
        target = os.path.join(folder, name)
        if os.path.exists(target):
            QMessageBox.warning(self, "Đã tồn tại", f"'{name}' đã có trong thư mục này.")
            return
        try:
            if is_dir:
                os.makedirs(target)
            else:
                open(target, "w", encoding="utf-8").close()
        except OSError as e:
            QMessageBox.critical(self, "Lỗi", str(e))
            return
        if not is_dir:
            self.open_path(target)

    def _explorer_rename(self, path):
        name, ok = QInputDialog.getText(self, "Đổi tên", "Tên mới:", QLineEdit.Normal,
                                        os.path.basename(path))
        name = self._safe_filename(name) if ok else ""
        if not name or name == os.path.basename(path):
            return
        new = os.path.join(os.path.dirname(path), name)
        if os.path.exists(new):
            QMessageBox.warning(self, "Đã tồn tại", f"'{name}' đã có.")
            return
        try:
            os.rename(path, new)
        except OSError as e:
            QMessageBox.critical(self, "Lỗi", str(e))
            return
        old_abs, new_abs = os.path.abspath(path), os.path.abspath(new)
        for i in range(self.tabs.count()):       # cập nhật các tab đang mở file này
            ed = self.tabs.widget(i)
            if not ed.file_path:
                continue
            fp = os.path.abspath(ed.file_path)
            if fp == old_abs or fp.startswith(old_abs + os.sep):
                ed.file_path = new_abs + fp[len(old_abs):]
                ed.set_language(get_language(ed.file_path))
                self._update_tab_title(ed)
        self.update_status()

    def _explorer_delete(self, path):
        what = "thư mục (cả nội dung bên trong)" if os.path.isdir(path) else "file"
        if QMessageBox.question(
                self, "Xóa", f"Xóa vĩnh viễn {what}:\n{path}\n\nKhông thể hoàn tác.") != QMessageBox.Yes:
            return
        try:
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
        except OSError as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    #  snippet của người dùng
    def load_user_snippets(self):
        for lang, keys in getattr(self, "_user_snip", {}).items():
            for k in keys:
                SNIPPETS.get(lang, {}).pop(k, None)
        self._user_snip = {}
        p = user_snippets_path()
        if not os.path.isfile(p):
            return
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict)
        except (OSError, ValueError, AssertionError) as e:
            self.terminal.appendPlainText(f"[snippets] {p} không đọc được: {e}")
            return
        n = 0
        for lang, d in data.items():
            if not isinstance(d, dict):
                continue
            for k, tpl in d.items():
                if isinstance(tpl, str) and k:
                    SNIPPETS.setdefault(lang, {})[k] = tpl
                    self._user_snip.setdefault(lang, set()).add(k)
                    n += 1
        self.statusBar().showMessage(f"Đã nạp {n} snippet của bạn", 3000)

    def open_user_snippets(self):
        p = user_snippets_path()
        if not os.path.exists(p):
            example = {"python": {"pmain": "def main():\n    $0\n"},
                       "javascript": {"clog": "console.log($0);"}}
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(example, indent=2, ensure_ascii=False) + "\n")
        self.open_path(p)
        self.terminal.appendPlainText(
            "Snippet: gõ từ khóa + Tab. $0 = vị trí con trỏ. Lưu file này là tự nạp lại.")

    #  trình biên dịch C / C++
    def choose_c_compiler(self):
        dlg = CCompilerDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        v = dlg.values()
        CFG.C_COMPILER, CFG.C_FLAGS, CFG.CPP_FLAGS = v["path"], v["flags"], v["cppflags"]
        self.settings.setValue("cc/path", CFG.C_COMPILER)
        self.settings.setValue("cc/flags", CFG.C_FLAGS)
        self.settings.setValue("cc/cppflags", CFG.CPP_FLAGS)
        cc = get_c_compiler(False)
        self.terminal.appendPlainText(f"Trình biên dịch C: {cc or '(không tìm thấy)'}   cờ: {CFG.C_FLAGS}")
        cpp = get_c_compiler(True)
        self.terminal.appendPlainText(f"Trình biên dịch C++: {cpp or '(không tìm thấy)'}   cờ: {CFG.CPP_FLAGS}")

    def compile_check(self):
        """Chỉ biên dịch để xem lỗi/cảnh báo (không tạo exe, không chạy). Lỗi bấm được để nhảy tới dòng."""
        ed = self.current_editor()
        if ed is not None and ed.lang == "arduino":
            self._run_arduino(ed, "build")
            return
        if ed is None or ed.lang not in ("c", "cpp"):
            self.statusBar().showMessage("Chỉ kiểm tra biên dịch được file C / C++ / Arduino (.ino)", 3000)
            return
        cpp = ed.lang == "cpp"
        cc = get_c_compiler(cpp)
        if not cc:
            QMessageBox.critical(self, "Thiếu trình biên dịch", NO_CC_MSG)
            return
        orig = ed.file_path
        base = os.path.splitext(os.path.basename(orig))[0] if orig else "untitled"
        ext = os.path.splitext(orig)[1] if orig else LANG_EXT[ed.lang]
        try:
            if orig:
                tmp = os.path.join(os.path.dirname(orig), f"_tmp_chk_{base}{ext}")
                cleanup, cwd = [tmp], os.path.dirname(orig)
            else:
                d = tempfile.mkdtemp(prefix="pyapp_")
                tmp, cleanup, cwd = os.path.join(d, base + ext), [d], os.path.expanduser("~")
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                f.write(ed.toPlainText())
        except OSError as e:
            QMessageBox.critical(self, "Lỗi", f"Không tạo được file tạm:\n{e}")
            return
        if "tcc" in os.path.basename(cc).lower():
            obj = tmp + ".o"
            cleanup.append(obj)
            args = [tmp, "-c", "-o", obj] + cc_flag_list(cpp)
        else:
            args = [tmp, "-fsyntax-only"] + cc_flag_list(cpp)
        name = orig or f"{base}{ext}"
        self.terminal.appendPlainText(f"\n=== Kiểm tra biên dịch ({os.path.basename(cc)}): {os.path.basename(name)} ===")
        self.terminal.run_queue(
            [("Kiểm tra biên dịch", cc, args)],
            on_done=lambda: (self._on_done(),
                             self.terminal.appendPlainText("Không có lỗi biên dịch ✔")),
            on_step=self._on_step, on_fail=self._on_fail, cwd=cwd,
            cleanup_paths=cleanup, path_map={tmp: name})

    #  chạy lại / watch / lệnh shell
    def rerun_last(self):
        if self._rerun is not None:
            self._rerun(None)
        else:
            self.run_current_file()

    def toggle_run_on_save(self, checked):
        self.run_on_save = checked
        self.statusBar().showMessage(
            "Tự chạy lại mỗi khi lưu: " + ("BẬT" if checked else "tắt"), 3000)

    def run_shell_command(self):
        cmd, ok = QInputDialog.getText(
            self, "Chạy lệnh", "Lệnh (chạy trong thư mục dự án):",
            QLineEdit.Normal, self.settings.value("shell/last", "") or "")
        if not ok or not cmd.strip():
            return
        self.settings.setValue("shell/last", cmd)
        try:
            args = shlex.split(cmd, posix=(os.name != "nt"))
        except ValueError as e:
            QMessageBox.warning(self, "Lệnh sai", str(e))
            return
        prog = shutil.which(args[0])
        if not prog and os.name == "nt":          # lệnh dựng sẵn của cmd (dir, type...)
            prog, args = shutil.which("cmd") or "cmd", ["/c"] + args
        elif not prog:
            self.terminal.appendPlainText(f">>> Không tìm thấy lệnh: {args[0]}")
            return
        self.terminal.run_queue([(args[0], prog, args[1:])], on_done=self._on_done,
                                on_step=self._on_step, on_fail=self._on_fail,
                                cwd=self._project_root())

    #  tự nạp lại khi file bị đổi bên ngoài
    def _on_file_changed(self, path):
        QTimer.singleShot(300, lambda p=path: self._reload_if_changed(p))

    def _reload_if_changed(self, path):
        if os.path.exists(path) and path not in self._watcher.files():
            self._watcher.addPath(path)      # một số trình soạn thảo ghi đè bằng file mới
        target = os.path.normcase(os.path.abspath(path))
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if not ed.file_path or os.path.normcase(os.path.abspath(ed.file_path)) != target:
                continue
            try:
                res = read_text_file_ex(path)
            except OSError:
                return
            if res is None or res[0] == ed.toPlainText():
                return                        # không đổi (vd: chính app vừa lưu)
            if ed.document().isModified() and QMessageBox.question(
                    self, "File đã đổi",
                    f"'{os.path.basename(path)}' vừa bị thay đổi bên ngoài.\n"
                    "Nạp lại và bỏ các sửa đổi chưa lưu?") != QMessageBox.Yes:
                return
            ed.replace_all_text(res[0])
            ed.encoding, ed.eol = res[1], res[2]
            ed.document().setModified(False)
            self.statusBar().showMessage(f"Đã nạp lại: {os.path.basename(path)}", 4000)
            return

    #  chạy với tham số dòng lệnh
    def _args_key(self, path):
        return "runargs/" + hashlib.md5((path or "untitled").encode("utf-8")).hexdigest()

    def _run_args_for(self, path):
        raw = self.settings.value(self._args_key(path), "") or ""
        try:
            return shlex.split(raw, posix=(os.name != "nt")) if raw else []
        except ValueError:
            return []

    def run_with_args(self, args=None):
        """Chạy file hiện tại kèm tham số dòng lệnh (lưu riêng cho từng file)."""
        ed = self.current_editor()
        if ed is None:
            return
        key = self._args_key(ed.file_path)
        if args is None:
            args, ok = QInputDialog.getText(
                self, "Tham số dòng lệnh",
                "Tham số (lưu cho file này, để trống = không có):",
                QLineEdit.Normal, self.settings.value(key, "") or "")
            if not ok:
                return
        self.settings.setValue(key, args)
        self.run_current_file()

    def send_selection_to_stdin(self):
        """Gửi đoạn chọn (hoặc dòng hiện tại) vào stdin của chương trình đang chạy."""
        ed = self.current_editor()
        if ed is None:
            return
        text = ed.selected_code()
        if not text.strip():
            return
        if not self.terminal.send_input(text.rstrip("\n")):
            self.statusBar().showMessage("Chưa có chương trình nào đang chạy", 3000)

    def stop_process(self):
        if self.terminal.stop():
            self.progress.setFormat("Đã dừng")

    #  v3.1: tiện ích mới
    def reopen_closed_tab(self):
        while self._closed_paths:
            p = self._closed_paths.pop()
            if os.path.isfile(p):
                self.open_path(p)
                return
        self.statusBar().showMessage("Không có tab nào để mở lại", 3000)

    def toggle_guides(self, checked):
        self.show_guides = checked
        self.settings.setValue("ui/guides", checked)
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            ed.show_guides = checked
            ed.viewport().update()

    def set_tab_size(self, n):
        self.tab_size = n
        for i in range(self.tabs.count()):
            self.tabs.widget(i).set_tab_size(n)

    def _apply_autosave_timer(self):
        if self.autosave_secs > 0:
            self._autosave_timer.start(self.autosave_secs * 1000)
        else:
            self._autosave_timer.stop()

    def _autosave_tick(self):
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if ed.file_path and ed.document().isModified():
                self._save_editor(ed, quiet=True)

    def _update_py_label(self):
        py = get_python_command()
        self.py_label.setText("🐍 " + (os.path.basename(py[0]) if py else "không có python")
                              + (" (đã chọn)" if CFG.PY_OVERRIDE else ""))
        self.py_label.setToolTip(" ".join(py) if py else "")

    def set_interpreter(self, path):
        CFG.PY_OVERRIDE = path or ""
        self.settings.setValue("py/interpreter", CFG.PY_OVERRIDE)
        self._update_py_label()

    def choose_interpreter(self):
        root = self._project_root()
        cands = []
        vp = find_project_python(root) if root else None
        if vp:
            cands.append(f"venv dự án: {vp}")
        cands.append("Mặc định (Python hệ thống / py launcher)")
        cands.append("Chọn file python khác...")
        cur = get_python_command()
        v, ok = QInputDialog.getItem(
            self, "Python interpreter", f"Đang dùng: {' '.join(cur) if cur else '(không có)'}",
            cands, 0, False)
        if not ok:
            return
        if v.startswith("venv dự án: "):
            self.set_interpreter(v[len("venv dự án: "):])
        elif v.startswith("Mặc định"):
            self.set_interpreter("")
        else:
            f, _ = QFileDialog.getOpenFileName(self, "Chọn python", "", "Python (python*);;Tất cả (*)")
            if f:
                self.set_interpreter(f)
        self.terminal.appendPlainText("Python interpreter: " + " ".join(get_python_command() or ["(không có)"]))

    def open_preferences(self):
        dlg = PreferencesDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        self._apply_prefs(dlg.values())

    def lint_current_file(self):
        """pyflakes (nếu thiếu thì hỏi cài) cho file Python hiện tại."""
        ed = self.current_editor()
        if ed is None or ed.lang != "python":
            self.statusBar().showMessage("Chỉ kiểm tra được file Python", 3000)
            return
        py = get_python_command()
        if py is None:
            QMessageBox.critical(self, "Không có Python", "Không tìm thấy Python trên máy này.")
            return
        tmp = tempfile.mkdtemp(prefix="pyapp_lint_")
        name = os.path.basename(ed.file_path) if ed.file_path else "untitled.py"
        src = os.path.join(tmp, "buf.py")
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(ed.toPlainText())
        self.statusBar().showMessage("Đang kiểm tra bằng pyflakes...", 0)

        def done(res):
            shutil.rmtree(tmp, ignore_errors=True)
            code, out, err = res
            self.statusBar().clearMessage()
            if "No module named" in err and "pyflakes" in err:
                if QMessageBox.question(self, "Thiếu pyflakes",
                                        "Chưa cài 'pyflakes'. Cài ngay?") == QMessageBox.Yes:
                    self._pip_install(["pyflakes"])
                return
            text = (out + err).replace(src, name).strip()
            if not text:
                self.terminal.appendPlainText(f"[pyflakes] {name}: không có cảnh báo ✔")
                return
            self.terminal.appendPlainText(f"[pyflakes] {name}:\n{text}")
            m = re.search(r":(\d+):", text)
            if m:
                ed.goto_line(int(m.group(1)))

        self._capture_async(py + ["-m", "pyflakes", src], done, timeout=60, cwd=tmp)

    def diff_with_file(self):
        import difflib
        ed = self.current_editor()
        if ed is None:
            return
        other, _ = QFileDialog.getOpenFileName(self, "So sánh với file...", "", "Tất cả (*)")
        if not other:
            return
        try:
            b = read_text_file(other)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Không đọc được", str(e))
            return
        if b is None:
            QMessageBox.warning(self, "Không so sánh được", "File nhị phân.")
            return
        a_name = os.path.basename(ed.file_path) if ed.file_path else "(tab hiện tại)"
        diff = "\n".join(difflib.unified_diff(
            ed.toPlainText().splitlines(), b.splitlines(), a_name, os.path.basename(other),
            lineterm=""))
        tab = self.new_tab(content=diff or "(hai file giống nhau)")
        tab.set_language(None)
        tab.document().setModified(False)

    def _install_default_plugins(self):
        """Ghi 2 plugin mặc định (Code→Ảnh, Code→3D) vào ~/.pyapp/plugins nếu chưa có."""
        d = user_plugin_dir()
        trusted = self._trusted_plugins()
        changed = False
        for fn, code in DEFAULT_PLUGINS.items():
            path = os.path.join(d, fn)
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        old = f.read()
                    if "pyapp-default-plugin" not in old.split("\n", 1)[0] or old == code:
                        pass_write = False
                    else:
                        pass_write = True      # bản mặc định cũ -> nâng cấp
                else:
                    pass_write = True
                if pass_write:
                    with open(path, "w", encoding="utf-8", newline="\n") as f:
                        f.write(code)
                    changed = True
                with open(path, "rb") as f:
                    digest = hashlib.sha256(f.read()).hexdigest()
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    first = f.readline()
                # chỉ tin tưởng sẵn bản do chính app tạo (còn nguyên nội dung nhúng)
                if "pyapp-default-plugin" in first and hashlib.sha256(
                        code.encode("utf-8")).hexdigest() == digest and trusted.get(path) != digest:
                    trusted[path] = digest
                    changed = True
            except OSError:
                continue
        if changed:
            self.settings.setValue("plugins/trusted", json.dumps(trusted))

    def about(self):
        QMessageBox.about(
            self, f"Về {APP_NAME}",
            f"<b>{APP_NAME} - Python IDE</b> v{APP_VERSION}<br>"
            "Editor đa ngôn ngữ (Python, C/C++, C#, JS/TS, Rust, Go, Java, HTML/CSS và nhiều hơn).<br>"
            "Chạy, build EXE, Git, ESP/Arduino, plugin, trình xem ảnh / 3D / hex / media, Dựng nhanh.<br>"
            f"<a href='{REPO_URL}'>{REPO_URL}</a>")

    #  UI setup
    def _act(self, text, slot, shortcut=None, parent_menu=None, checkable=False):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(shortcut)
        if checkable:
            a.setCheckable(True)
            a.toggled.connect(slot)
        else:
            a.triggered.connect(lambda _=False: slot())
        if parent_menu is not None:
            parent_menu.addAction(a)
        return a

    def _build_menu_and_toolbar(self):
        menu = self.menuBar()

        # File
        fm = menu.addMenu("File")
        new_a = self._act("New Tab", self.new_tab, "Ctrl+N", fm)
        open_a = self._act("Open...", self.open_file, "Ctrl+O", fm)
        self._act("Open Folder...", self.open_folder, "Ctrl+Shift+O", fm)
        self.recent_menu = fm.addMenu("Mở gần đây")
        self.recent_menu.aboutToShow.connect(self._rebuild_recent_menu)
        fm.addSeparator()
        save_a = self._act("Save", self.save_file, "Ctrl+S", fm)
        self._act("Save As...", self.save_file_as, "Ctrl+Shift+S", fm)
        self._act("Save All", self.save_all, "Ctrl+Alt+S", fm)
        fm.addSeparator()
        self._act("Close Tab", self.close_current_tab, "Ctrl+W", fm)
        self._act("Exit", self.close, "Ctrl+Q", fm)

        # Edit
        em = menu.addMenu("Edit")
        for text, method, key in (
                ("Undo", "undo", QKeySequence.Undo), ("Redo", "redo", QKeySequence.Redo),
                (None, None, None),
                ("Cut", "cut", QKeySequence.Cut), ("Copy", "copy", QKeySequence.Copy),
                ("Paste", "paste", QKeySequence.Paste),
                ("Select All", "selectAll", QKeySequence.SelectAll)):
            if text is None:
                em.addSeparator()
                continue
            a = QAction(text, self)
            a.setShortcut(key)
            a.triggered.connect(lambda _=False, m=method: self._editor_do(m))
            em.addAction(a)
        em.addSeparator()
        find_a = self._act("Tìm...", lambda: self.findbar.show_find(False), "Ctrl+F", em)
        self._act("Thay thế...", lambda: self.findbar.show_find(True), "Ctrl+H", em)
        self._act("Tìm tiếp", lambda: self.findbar.find_next(True), "F3", em)
        self._act("Tìm lùi", lambda: self.findbar.find_next(False), "Shift+F3", em)
        self._act("Đi tới dòng...", self.goto_line_dialog, "Ctrl+G", em)
        em.addSeparator()
        self._act("Comment / Bỏ comment", lambda: self._editor_do("toggle_comment"),
                  "Ctrl+/", em)
        self._act("Nhân đôi dòng", lambda: self._editor_do("duplicate_line"),
                  "Ctrl+D", em)
        self._act("Chuyển dòng lên", lambda: self._editor_do("move_lines", -1),
                  "Alt+Up", em)
        self._act("Chuyển dòng xuống", lambda: self._editor_do("move_lines", 1),
                  "Alt+Down", em)
        self._act("Gợi ý code", lambda: self._editor_do("_maybe_complete", True),
                  "Ctrl+Space", em)
        em.addSeparator()
        self._act("Xóa dòng", lambda: self._editor_do("delete_line"), "Ctrl+Shift+K", em)
        self._act("Chuyển thành CHỮ HOA", lambda: self._editor_do("change_case", True),
                  "Ctrl+Shift+U", em)
        self._act("Chuyển thành chữ thường", lambda: self._editor_do("change_case", False),
                  "Ctrl+Shift+L", em)
        self._act("Sắp xếp dòng (A-Z)", lambda: self._editor_do("sort_lines"), None, em)
        self._act("Xóa khoảng trắng cuối dòng", lambda: self._editor_do("trim_trailing_ws"),
                  None, em)
        trim_a = self._act("Tự dọn khoảng trắng khi lưu", self.toggle_trim_on_save,
                           None, em, checkable=True)
        trim_a.setChecked(self.trim_on_save)
        self._chk = getattr(self, "_chk", {})
        self._chk["trim"] = trim_a
        em.addSeparator()
        self._act("Nối các dòng (Join)", lambda: self._editor_do("join_lines"), "Ctrl+J", em)
        self._act("Chèn dòng mới bên dưới", lambda: self._editor_do("insert_line_below"),
                  "Ctrl+Return", em)
        self._act("Đổi thụt lề: Tab → khoảng trắng",
                  lambda: self._editor_do("convert_indent", True), None, em)
        self._act("Đổi thụt lề: khoảng trắng → Tab",
                  lambda: self._editor_do("convert_indent", False), None, em)
        self._act("So sánh với file khác (diff)...", self.diff_with_file, None, em)
        self._act("Mở lại tab vừa đóng", self.reopen_closed_tab, "Ctrl+Shift+T", em)
        em.addSeparator()
        self._act("Chọn lần xuất hiện kế tiếp", lambda: self._editor_do("select_next_occurrence"),
                  "Ctrl+Alt+J", em)
        self._act("Đổi tên symbol trong file...", lambda: self._editor_do("rename_symbol"), "Ctrl+Alt+F2", em)
        cm = em.addMenu("Đổi kiểu đặt tên")
        for lbl, key in (("snake_case", "snake"), ("camelCase", "camel"), ("PascalCase", "pascal"),
                         ("kebab-case", "kebab"), ("UPPER_SNAKE", "upper")):
            self._act(lbl, lambda k=key: self._editor_do("convert_case_style", k), None, cm)
        em.addSeparator()
        self._act("Xem trước Markdown", self.show_markdown_preview, "Ctrl+Alt+M", em)
        self._act("Thống kê tài liệu", self.show_doc_stats, None, em)

        # View
        vm = menu.addMenu("View")
        theme_menu = vm.addMenu("Giao diện (Theme)")
        group = QActionGroup(self)
        self._theme_menu, self._theme_group = theme_menu, group
        self._theme_actions = {}
        for key, t in THEMES.items():
            a = QAction(t["label"], self)
            a.setCheckable(True)
            a.setActionGroup(group)
            a.triggered.connect(lambda _=False, k=key: self.set_theme(k))
            theme_menu.addAction(a)
            self._theme_actions[a] = key
        vm.addSeparator()
        self._act("Gập / mở vùng code tại con trỏ", lambda: self._editor_do("toggle_fold_at_cursor"),
                  "Ctrl+Shift+[", vm)
        self._act("Gập tất cả", lambda: self._editor_do("fold_all"), "Ctrl+Alt+[", vm)
        self._act("Mở tất cả", lambda: self._editor_do("unfold_all"), "Ctrl+Alt+]", vm)
        vm.addSeparator()
        self._act("Bật / tắt bookmark dòng này", lambda: self._editor_do("toggle_bookmark"),
                  "Ctrl+F2", vm)
        self._act("Bookmark kế tiếp", lambda: self._editor_do("goto_bookmark", 1), "F2", vm)
        self._act("Bookmark trước", lambda: self._editor_do("goto_bookmark", -1), "Shift+F2", vm)
        self._act("Xóa mọi bookmark", lambda: self._editor_do("clear_bookmarks"), None, vm)
        vm.addSeparator()
        self._act("Phóng to chữ", lambda: self.zoom(1), "Ctrl+=", vm)
        self._act("Thu nhỏ chữ", lambda: self.zoom(-1), "Ctrl+-", vm)
        self._act("Cỡ chữ mặc định", lambda: self.zoom(0), "Ctrl+0", vm)
        vm.addSeparator()
        wrap_a = self._act("Tự xuống dòng (Word wrap)", self.toggle_wrap,
                           "Alt+Z", vm, checkable=True)
        wrap_a.setChecked(self.word_wrap)
        self._chk = getattr(self, "_chk", {})
        self._chk["wrap"] = wrap_a
        ws_a = self._act("Hiện khoảng trắng / tab", self.toggle_whitespace, None, vm,
                         checkable=True)
        ws_a.setChecked(self.show_ws)
        self._chk = getattr(self, "_chk", {})
        self._chk["ws"] = ws_a
        gd_a = self._act("Đường kẻ thụt lề", self.toggle_guides, None, vm, checkable=True)
        gd_a.setChecked(self.show_guides)
        self._chk = getattr(self, "_chk", {})
        self._chk["guides"] = gd_a
        mm_a = self._act("Hiện minimap", self.toggle_minimap, None, vm, checkable=True)
        mm_a.setChecked(self.show_minimap)
        self._chk = getattr(self, "_chk", {})
        self._chk["minimap"] = mm_a
        self._act("Chế độ Zen (toàn màn hình, ẩn khung phụ)", self.toggle_zen, "F11", vm)
        self._act("Cài đặt (Preferences)...", self.open_preferences, "Ctrl+,", vm)
        vm.addAction(self.dock.toggleViewAction())
        self.dock.toggleViewAction().setShortcut("Ctrl+B")
        term_a = self._act("Hiện Terminal", self.toggle_terminal, "Ctrl+`", vm,
                           checkable=True)
        term_a.setChecked(True)
        self._act("Xóa Terminal", self.terminal.output.clear, None, vm)

        # Run / Build / Tools
        rm = menu.addMenu("Run")
        run_a = self._act("Run File (F5)", self.run_current_file, "F5", rm)
        stop_a = self._act("Dừng (Shift+F5)", self.stop_process, "Shift+F5", rm)
        self._act("Chạy đoạn đang chọn (F9)", self.run_selection, "F9", rm)
        self._act("Gửi đoạn chọn vào stdin chương trình", self.send_selection_to_stdin,
                  "Ctrl+Alt+Return", rm)
        self._act("Chạy với tham số dòng lệnh...", self.run_with_args, "Ctrl+Shift+F5", rm)
        self._act("Gửi EOF (đóng stdin)", lambda: self.terminal.send_eof(), "Ctrl+Alt+D", rm)
        self._act("Chạy lại lần trước", self.rerun_last, "F4", rm)
        self._act("Tự chạy lại khi lưu (watch)", self.toggle_run_on_save, None, rm, checkable=True)
        auto_a = self._act("Tự lưu file trước khi chạy", self.toggle_autosave_run,
                           None, rm, checkable=True)
        auto_a.setChecked(self.autosave_before_run)
        self._chk = getattr(self, "_chk", {})
        self._chk["runsave"] = auto_a
        bm = menu.addMenu("Build")
        build_a = self._act("Cài thư viện && Build EXE (F6)", self.build_to_exe, "F6", bm)
        self._act("Kiểm tra biên dịch C/C++ / Arduino (không chạy) (F7)", self.compile_check, "F7", bm)
        tm = menu.addMenu("Tools")
        self._act("Cài thư viện cho file hiện tại (pip)",
                  self.install_libs_for_current, None, tm)
        self._act("Cài thư viện cho plugin (vào ~/.pyapp/libs)...",
                  self.install_plugin_libs, None, tm)
        self._act("Chẩn đoán đa phương tiện (video/âm thanh)",
                  self.diagnose_media, None, tm)
        self._act("Định dạng code (black / JSON)", self.format_code, "Alt+Shift+F", tm)
        self._act("Kiểm tra lỗi (pyflakes)", self.lint_current_file, "Alt+Shift+L", tm)
        self._act("Chọn Python interpreter / venv...", self.choose_interpreter, None, tm)
        self._act("Trình biên dịch C/C++...", self.choose_c_compiler, None, tm)
        self._build_tools_menus(menu, tm)
        gm = menu.addMenu("Go")
        self._act("Command Palette...", self.command_palette, "Ctrl+Shift+P", gm)
        self._act("Mở nhanh file...", self.quick_open, "Ctrl+P", gm)
        self._act("Đi tới hàm / class...", self.goto_symbol, "Ctrl+R", gm)
        self._act("Tìm trong thư mục...", self.show_find_in_files, "Ctrl+Shift+F", gm)
        hm = menu.addMenu("Help")
        self._act("Giới thiệu", self.about, None, hm)
        self._act("Tài liệu API plugin", self.show_api_reference, None, hm)
        hm.addSeparator()
        self._act("Kiểm tra cập nhật...", self.check_for_updates, None, hm)
        self._act("Trang GitHub", self.open_github, None, hm)
        self._act("Báo lỗi / góp ý", self.open_github_issues, None, hm)

        # Toolbar
        tb = QToolBar("Main")
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        self.toolbar = tb
        self.addToolBar(tb)
        for a in (new_a, open_a, save_a):
            tb.addAction(a)
        tb.addSeparator()
        tb.addAction(run_a)
        tb.addAction(stop_a)
        tb.addAction(build_a)
        tb.addSeparator()
        tb.addAction(find_a)
        md_a = QAction("Xem trước Markdown", self)
        md_a.triggered.connect(self.show_markdown_preview)
        st_a = QAction("Thống kê tài liệu", self)
        st_a.triggered.connect(self.show_doc_stats)
        rn_a = QAction("Đổi tên symbol", self)
        rn_a.triggered.connect(lambda: self._editor_do("rename_symbol"))
        tb.addSeparator()
        for _a in (rn_a, md_a, st_a):
            tb.addAction(_a)
        tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        tb.setIconSize(QSize(20, 20))
        self._tb_icons = [(new_a, "newfile", None), (open_a, "open", None), (save_a, "save", None),
                          (run_a, "run", "#3fb950"), (stop_a, "stop", "#f85149"),
                          (build_a, "build", None), (find_a, "search", None),
                          (rn_a, "rename", None), (md_a, "markdown", None), (st_a, "stats", None)]
        for act, _n, _c in self._tb_icons:
            sc = act.shortcut().toString()
            act.setToolTip(act.text().replace("&", "") + (f"  ({sc})" if sc else ""))
        self._build_command_pill(tb)


def make_splash():
    """Màn hình khởi động vẽ bằng code (không cần file ảnh)."""
    w, h, dpr = 560, 300, 2.0
    key = QSettings("PyAppTools", "PyApp").value("ui/theme", DEFAULT_THEME)
    t = THEMES.get(key, THEMES[DEFAULT_THEME])
    pm = QPixmap(int(w * dpr), int(h * dpr))
    pm.setDevicePixelRatio(dpr)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    g = QLinearGradient(0, 0, w, h)
    g.setColorAt(0, QColor(t["window_bg"]))
    g.setColorAt(1, QColor(_mix(t["window_bg"], t["accent"], 0.28)))
    p.fillRect(0, 0, w, h, QBrush(g))
    ac = QColor(t["accent"])
    glow = QColor(ac)
    glow.setAlpha(40)
    p.setPen(Qt.NoPen)
    p.setBrush(glow)
    p.drawEllipse(QPointF(w - 40, 40), 150, 150)
    p.setBrush(QColor(ac.red(), ac.green(), ac.blue(), 22))
    p.drawEllipse(QPointF(w - 40, 40), 220, 220)
    p.setBrush(ac)
    p.drawRoundedRect(QRectF(44, 70, 64, 64), 16, 16)
    p.setPen(QColor("#ffffff"))
    f = QFont("Segoe UI", 1)
    f.setPixelSize(36)
    f.setBold(True)
    p.setFont(f)
    p.drawText(QRectF(44, 70, 64, 64), Qt.AlignCenter, "GK")
    p.setPen(QColor(t["fg"]))
    f.setPixelSize(40)
    p.setFont(f)
    p.drawText(QRectF(128, 66, 400, 50), Qt.AlignLeft | Qt.AlignVCenter, APP_NAME)
    f.setBold(False)
    f.setPixelSize(15)
    p.setFont(f)
    p.setPen(QColor(_mix(t["fg"], t["bg"], 0.35)))
    p.drawText(QRectF(130, 112, 400, 24), Qt.AlignLeft | Qt.AlignVCenter,
               f"Python IDE  \u00b7  v{APP_VERSION}")
    p.setPen(QPen(QColor(ac.red(), ac.green(), ac.blue(), 120), 1))
    p.setBrush(Qt.NoBrush)
    p.drawRect(QRectF(0.5, 0.5, w - 1, h - 1))
    p.end()
    splash = QSplashScreen(pm, Qt.WindowStaysOnTopHint)
    splash.showMessage("    Đang khởi động...", Qt.AlignBottom | Qt.AlignLeft,
                       QColor(_mix(t["fg"], t["bg"], 0.25)))
    return splash


def main():
    # Khi build bằng --windowed, sys.stdout/stderr là None: print() sẽ gây lỗi
    # thầm lặng làm cả thao tác "biến mất" không báo gì.
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()

    def show_error(exc_type, exc_value, exc_tb):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            QMessageBox.critical(None, "Lỗi", msg[-3000:])
        except Exception:
            pass

    sys.excepthook = show_error
    enable_user_libs()
    if os.name == "nt":
        # DirectShow (mặc định của Qt 5.15) thường không phát được mp4 nếu máy thiếu codec
        os.environ.setdefault("QT_MULTIMEDIA_PREFERRED_PLUGINS", "windowsmediafoundation")

    if os.name == "nt":
        try:       # để taskbar Windows hiện đúng icon / nhóm cửa sổ của app
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GKcode.IDE.4")
        except Exception:
            pass
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setDesktopFileName("gkcode")      # khớp gkcode.desktop để dock/taskbar hiện đúng icon
    app.setStyle(QStyleFactory.create("Fusion"))
    fams = set(QFontDatabase().families())
    for fam in ("Segoe UI Variable Text", "Segoe UI", "Inter", "SF Pro Text", "Noto Sans",
                "Ubuntu", "Cantarell", "DejaVu Sans"):
        if fam in fams:
            f = QFont(fam)
            f.setPointSizeF(9.5)
            app.setFont(f)
            break
    splash = None
    try:
        splash = make_splash()
        splash.show()
        app.processEvents()
    except Exception:
        splash = None
    window = PyApp()
    window.show()
    if splash is not None:
        splash.finish(window)
    # mở file truyền qua dòng lệnh: GKcode.exe file1.py file2.py
    for p in sys.argv[1:]:
        window.open_path(p)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
