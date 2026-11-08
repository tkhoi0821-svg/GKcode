# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp', 'templates', 'polyglot', 'plugins', 'textools']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


# Mixin gắn vào cửa sổ chính
class ToolsMixin:
    #  khởi tạo
    def _tools_init(self):
        self._events = {}
        self._context_actions = []     # [(chữ, callback)] menu chuột phải editor
        self._lint_providers = []      # [fn(text, lang, path) -> [(dòng, thông báo)]]
        self._change_timer = QTimer(self)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(
            lambda: self.emit_event("change", self.current_editor()))
        self._threads = []
        self.run_on_save = False
        self._saving_for_run = False
        self._explorer_actions = []     # [(chữ, callback(path))] menu chuột phải Explorer
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self.plugin_apis = []          # [(tên, api, module)]
        self.serial_monitor = None
        self.esp_dialog = None
        self.download_dialog = None
        self.builtin_api = PyAppAPI(self, "builtin")
        self._script_api = PyAppAPI(self, "script")

    def emit_event(self, name, *args):
        for cb in list(self._events.get(name, [])):
            try:
                cb(*args)
            except Exception:  # noqa: BLE001
                self.terminal.appendPlainText(f"[sự kiện {name}] LỖI:\n" + traceback.format_exc())

    def _build_console_dock(self):
        self.console = PyConsole(self)
        self.console_dock = QDockWidget("Python Console", self)
        self.console_dock.setObjectName("consoleDock")
        self.console_dock.setWidget(self.console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)
        self.console_dock.hide()
        self.git_panel = GitPanel(self)
        self.git_dock = QDockWidget("Git", self)
        self.git_dock.setObjectName("gitDock")
        self.git_dock.setWidget(self.git_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.git_dock)
        self.git_dock.hide()
        self.git_dock.visibilityChanged.connect(
            lambda v: self.git_panel.refresh() if v else None)
        self.repl = ReplPanel(self)
        self.repl_dock = QDockWidget("Python REPL (tiến trình riêng)", self)
        self.repl_dock.setObjectName("replDock")
        self.repl_dock.setWidget(self.repl)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.repl_dock)
        self.tabifyDockWidget(self.console_dock, self.repl_dock)
        self.repl_dock.hide()
        self.repl_dock.visibilityChanged.connect(
            lambda v: self.repl.start() if v and not self.repl.running() else None)
        self.esp_ide = EspIdePanel(self)
        self.esp_ide_dock = QDockWidget("ESP IDE", self)
        self.esp_ide_dock.setObjectName("espIdeDock")
        self.esp_ide_dock.setWidget(self.esp_ide)
        self.addDockWidget(Qt.RightDockWidgetArea, self.esp_ide_dock)
        self.esp_ide_dock.hide()
        self.esp_ide_dock.visibilityChanged.connect(
            lambda v: self.esp_ide.refresh() if v else None)
        self.tabs.currentChanged.connect(
            lambda _i: self.esp_ide.refresh_status() if self.esp_ide_dock.isVisible() else None)
        self.todo_panel = TodoPanel(self)
        self.todo_dock = QDockWidget("TODO", self)
        self.todo_dock.setObjectName("todoDock")
        self.todo_dock.setWidget(self.todo_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.todo_dock)
        self.tabifyDockWidget(self.git_dock, self.todo_dock)
        self.todo_dock.hide()
        self.todo_dock.visibilityChanged.connect(
            lambda v: self.todo_panel.refresh() if v else None)
        self._todo_timer = QTimer(self)
        self._todo_timer.setSingleShot(True)
        self._todo_timer.timeout.connect(self.todo_panel.refresh)
        self.terminal.output.base_dirs = lambda: [self.terminal.cwd, self._project_root()]
        self.terminal.output.link_clicked.connect(self.open_at)
        self.terminal.on_output = lambda t: self.emit_event("output", t)
        self.branch_label = QLabel("")
        self.statusBar().addPermanentWidget(self.branch_label)
        self._git_timer = QTimer(self)
        self._git_timer.setSingleShot(True)
        self._git_timer.timeout.connect(self.git_panel.refresh)
        self._events.setdefault("save", []).append(self._on_save_internal)

    def set_branch_text(self, text):
        self.branch_label.setText(f"⎇ {text}" if text else "")

    def _on_save_internal(self, ed):
        sp = getattr(ed, "file_path", None)
        if sp and os.path.abspath(sp) == os.path.abspath(user_snippets_path()):
            self.load_user_snippets()
        if self.run_on_save and not self._saving_for_run and ed is self.current_editor() \
                and getattr(ed, "lang", None) in RUNNABLE:
            QTimer.singleShot(150, self.run_current_file)
        # lưu file trong thư mục plugin -> tự tin tưởng bản của chính mình và nạp lại
        path = getattr(ed, "file_path", None)
        if path:
            ap = os.path.abspath(path)
            if ap.endswith(".py") and os.path.dirname(ap) in [os.path.abspath(d) for d in app_plugin_dirs()]:
                try:
                    with open(ap, "rb") as f:
                        digest = hashlib.sha256(f.read()).hexdigest()
                    trusted = self._trusted_plugins()
                    if ap in trusted or QMessageBox.question(
                            self, "Plugin", "Tin tưởng và nạp plugin này?") == QMessageBox.Yes:
                        trusted[ap] = digest
                        self.settings.setValue("plugins/trusted", json.dumps(trusted))
                        QTimer.singleShot(0, self.load_plugins)
                except OSError:
                    pass
        self._git_timer.start(500)
        if self.todo_dock.isVisible():
            self._todo_timer.start(1200)

    def open_at(self, path, line=0):
        """Mở file và nhảy tới dòng (click link trong terminal, panel TODO...)."""
        self.open_path(path)
        ed = self.current_editor()
        if ed is not None and line and ed.file_path and \
                os.path.normcase(os.path.abspath(ed.file_path)) == os.path.normcase(os.path.abspath(path)):
            ed.goto_line(line)

    def _editor_text(self):
        ed = self.current_editor()
        if ed is None:
            return "", ""
        sel = ed.textCursor().selectedText().replace("\u2029", "\n")
        return (sel if sel.strip() else ed.toPlainText()), os.path.basename(ed.file_path or "tab")

    def _show(self, dlg):
        dlg.setAttribute(Qt.WA_DeleteOnClose)
        dlg.show()
        dlg.raise_()

    def view_json(self):
        text, name = self._editor_text()
        try:
            data = json.loads(text)
        except ValueError as e:
            QMessageBox.warning(self, "JSON không hợp lệ", str(e))
            return
        self._show(JsonTreeDialog(self, data, name))

    def view_csv(self):
        text, name = self._editor_text()
        if not text.strip():
            return
        try:
            try:
                dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            rows = [r for r in csv.reader(io.StringIO(text), dialect)][:200001]
        except csv.Error as e:
            QMessageBox.warning(self, "CSV lỗi", str(e))
            return
        if not rows:
            return
        header = rows[0]
        header += [""] * (max(len(r) for r in rows) - len(header))
        self._show(TableDialog(self, header, rows[1:], f"CSV - {name}"))

    def view_image(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self, "Chọn ảnh", self._project_root(),
                "Ảnh (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.ico *.svg *.tif *.tiff *.tga);;Tất cả (*)")
        if path:
            self._show(ImageViewerDialog(self, path))

    def open_regex_tester(self):
        ed = self.current_editor()
        sel = ed.textCursor().selectedText().replace("\u2029", "\n") if ed else ""
        self._show(RegexDialog(self, sel))

    #  trạng thái: mã hóa / EOL
    def _status_button(self, text, callback):
        b = QPushButton(text)
        b.setFlat(True)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(callback)
        return b

    def _enc_menu(self):
        ed = self.current_editor()
        if ed is None:
            return
        m = QMenu(self)
        for label, enc in (("UTF-8", "utf-8"), ("UTF-8 có BOM", "utf-8-sig"), ("UTF-16", "utf-16"),
                           ("Windows-1252 (Tây Âu)", "cp1252"), ("Windows-1258 (Việt)", "cp1258"),
                           ("Latin-1", "latin-1")):
            a = m.addAction(label)
            a.setCheckable(True)
            a.setChecked(ed.encoding == enc)
            a.triggered.connect(lambda _=False, e=enc: self._set_encoding(ed, e))
        m.exec_(QCursor.pos())

    def _eol_menu(self):
        ed = self.current_editor()
        if ed is None:
            return
        m = QMenu(self)
        for label, eol in (("LF  (Linux / macOS)", "\n"), ("CRLF  (Windows)", "\r\n"), ("CR  (Mac cũ)", "\r")):
            a = m.addAction(label)
            a.setCheckable(True)
            a.setChecked(ed.eol == eol)
            a.triggered.connect(lambda _=False, e=eol: self._set_eol(ed, e))
        m.exec_(QCursor.pos())

    def _set_encoding(self, ed, enc):
        if ed.encoding != enc:
            ed.encoding = enc
            ed.document().setModified(True)      # lưu lại để áp dụng
            self.update_status()

    def _set_eol(self, ed, eol):
        if ed.eol != eol:
            ed.eol = eol
            ed.document().setModified(True)
            self.update_status()

    def send_selection_to_repl(self):
        ed = self.current_editor()
        if ed is None:
            return
        code = ed.selected_code()
        if not code.strip():
            return
        self.repl_dock.show()
        self.repl_dock.raise_()
        self.repl.send_text(textwrap.dedent(code))

    def _tools_shutdown(self):
        self.repl.stop()

    def _register_builtin_tools(self):
        register_builtin_text_tools(self.builtin_api, self._text_menu)

    def _capture_async(self, args, callback, timeout=60, cwd=None):
        t = CaptureThread(args, timeout, cwd)
        self._threads.append(t)

        def fin(res):
            if t in self._threads:
                self._threads.remove(t)
            callback(res)
        t.done.connect(fin)
        t.start()

    #  menu
    def _build_tools_menus(self, menu, tm):
        tm.addSeparator()
        self._act("Tải xuống từ URL...", self.open_download_dialog, "Ctrl+Shift+D", tm)
        self._act("Tải link đang chép trong clipboard", self.download_from_clipboard, None, tm)
        self._act("Dự án / file mới từ mẫu...", self.new_from_template, "Ctrl+Shift+N", tm)
        tm.addSeparator()
        self._act("Cài thư viện pip (nhập tên)...", self.pip_install_prompt, None, tm)
        self._act("pip list → tab mới", self.pip_list_tab, None, tm)
        self._act("Chạy lệnh shell...", self.run_shell_command, "Ctrl+Alt+X", tm)
        self._act("Snippet của tôi (snippets.json)...", self.open_user_snippets, None, tm)
        self._act("Nạp lại snippet", self.load_user_snippets, None, tm)
        self._act("Python REPL (tiến trình riêng)", lambda: self.repl_dock.setVisible(
            not self.repl_dock.isVisible()), "Ctrl+Shift+R", tm)
        self._act("Gửi đoạn chọn vào REPL", self.send_selection_to_repl, "Ctrl+Shift+Return", tm)
        self._act("Python Console", lambda: self.console_dock.setVisible(
            not self.console_dock.isVisible()), "Ctrl+Shift+Y", tm)
        tm.addSeparator()
        vm = tm.addMenu("Trình xem / kiểm tra")
        self._act("JSON dạng cây", self.view_json, None, vm)
        self._act("CSV dạng bảng", self.view_csv, None, vm)
        self._act("Xem ảnh...", self.view_image, None, vm)
        self._extras_view_menu(vm, tm)
        self._act("Regex tester...", self.open_regex_tester, "Ctrl+Alt+R", vm)
        self._act("Panel TODO / FIXME", lambda: self.todo_dock.setVisible(
            not self.todo_dock.isVisible()), "Ctrl+Alt+T", tm)
        self._text_menu = tm.addMenu("Công cụ văn bản")

        gm = menu.addMenu("Git")
        self._act("Panel Git", lambda: self.git_dock.setVisible(
            not self.git_dock.isVisible()), "Ctrl+Shift+G", gm)
        gm.addSeparator()
        self._act("Clone từ URL...", self.git_clone, None, gm)
        self._act("Khởi tạo repo (init)", lambda: self._git([("git init", ["init"])]), None, gm)
        gm.addSeparator()
        self._act("Status", lambda: self._git([("git status", ["status", "-sb"])]), None, gm)
        self._act("Diff", lambda: self._git([("git diff", ["diff", "--stat"])]), None, gm)
        self._act("Log (20 commit)", lambda: self._git(
            [("git log", ["log", "--oneline", "--graph", "--decorate", "-20"])]), None, gm)
        gm.addSeparator()
        self._act("Add tất cả + Commit...", self.git_commit, None, gm)
        self._act("Pull", lambda: self._git([("git pull", ["pull"])]), None, gm)
        self._act("Push", lambda: self._git([("git push", ["push"])]), None, gm)

        em = menu.addMenu("ESP / Serial")
        self._act("ESP IDE (panel)", lambda: self.esp_ide_dock.setVisible(
            not self.esp_ide_dock.isVisible()), "Ctrl+Alt+E", em)
        self._act("ESP: Biên dịch", lambda: self.esp_ide.run("build"), "F8", em)
        self._act("ESP: Biên dịch + Nạp", lambda: self.esp_ide.run("upload"), "Ctrl+F8", em)
        self._act("ESP: Nạp + Serial Monitor", lambda: self.esp_ide.run("upload_monitor"),
                  "Ctrl+Shift+F8", em)
        self._act("ESP: Dọn", lambda: self.esp_ide.run("clean"), None, em)
        em.addSeparator()
        self._act("Boards Manager...", lambda: self.esp_ide.open_boards_manager(), None, em)
        self._act("Library Manager...", lambda: self.esp_ide.open_library_manager(), None, em)
        self._act("Examples...", lambda: self.esp_ide.open_examples(), None, em)
        self._act("Sketch mới...", lambda: self.esp_ide.new_sketch(), "Ctrl+Alt+N", em)
        self._act("Serial Plotter...", lambda: self.esp_ide.open_plotter(), "Ctrl+Alt+P", em)
        self._act("Cài arduino-cli + core ESP (tự động)...", lambda: self.esp_ide.open_setup(), None, em)
        em.addSeparator()
        self._act("Nạp firmware ESP...", self.open_esp_dialog, None, em)
        self._act("Serial Monitor...", self.open_serial_monitor, "Ctrl+Shift+M", em)
        self._act("Cài / cập nhật esptool", lambda: self._pip_install(["esptool"]), None, em)

        self.plugins_menu = menu.addMenu("Plugins")
        self._act("Quản lý plugin...", self.open_plugin_manager, None, self.plugins_menu)
        self._act("Tải lại plugins", self.load_plugins, None, self.plugins_menu)
        self._act("Mở thư mục plugins", lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(user_plugin_dir())), None, self.plugins_menu)
        self._act("Tạo plugin mẫu (hello.py)", self.create_sample_plugin, None, self.plugins_menu)
        self._act("Xem tài liệu API plugin", self.show_api_reference, None, self.plugins_menu)
        self._act("Nhập plugin (kiểm API trước)...", self.import_plugin, None, self.plugins_menu)
        self._act("Kiểm API của tab hiện tại (như plugin)", self.check_plugin_current, None, self.plugins_menu)
        self._act("Chạy file hiện tại như script (có api)", self.run_as_script, "Ctrl+F5",
                  self.plugins_menu)
        self._act("Quên các plugin đã tin tưởng", self.forget_trusted_plugins, None,
                  self.plugins_menu)
        self.plugins_menu.addSeparator()

    #  tải xuống
    def open_download_dialog(self, url="", unzip=False):
        if self.download_dialog is not None and self.download_dialog.isVisible():
            self.download_dialog.raise_()
            return
        self.download_dialog = DownloadDialog(self, url, unzip)
        self.download_dialog.show()

    def download_from_clipboard(self):
        txt = QApplication.clipboard().text().strip()
        if txt.lower().startswith(("http://", "https://")):
            self.open_download_dialog(txt.splitlines()[0])
        else:
            self.open_download_dialog()

    #  mẫu dự án
    def new_from_template(self):
        dlg = TemplateDialog(self, self._project_root())
        if dlg.exec_() != QDialog.Accepted:
            return
        idx, name, folder = dlg.values()
        if idx < 0 or not name or not folder:
            QMessageBox.warning(self, "Thiếu thông tin", "Cần chọn mẫu, nhập tên và thư mục.")
            return
        try:
            root, main_path, created, skipped = create_from_template(idx, name, folder)
        except OSError as e:
            QMessageBox.critical(self, "Lỗi", f"Không tạo được file:\n{e}")
            return
        if not TEMPLATES[idx]["single"]:
            self._set_explorer_root(root)
        if os.path.isfile(main_path):
            self.open_path(main_path)
        msg = f"Đã tạo {len(created)} file trong {root}"
        if skipped:
            msg += f" (bỏ qua {len(skipped)} file đã tồn tại)"
        self.terminal.appendPlainText(msg)

    #  pip
    def _pip_install(self, pkgs):
        py = get_python_command()
        if py is None:
            QMessageBox.critical(self, "Không tìm thấy Python",
                                 "Máy này chưa cài Python (hoặc không nằm trong PATH).")
            return
        self.terminal.run_queue(
            [("Cài " + " ".join(pkgs), py[0],
              py[1:] + ["-m", "pip", "install", "--disable-pip-version-check", "-U"] + pkgs)],
            on_done=self._on_done, on_step=self._on_step, on_fail=self._on_fail,
            cwd=self._project_root())

    def pip_install_prompt(self):
        text, ok = QInputDialog.getText(self, "Cài thư viện",
                                        "Tên thư viện (cách nhau bằng dấu cách):")
        if not ok or not text.strip():
            return
        pkgs = text.split()
        bad = [p for p in pkgs if p.startswith("-")]
        if bad:
            QMessageBox.warning(self, "Không hợp lệ",
                                f"Chỉ nhập tên thư viện, không nhập tùy chọn: {bad[0]}")
            return
        self._pip_install(pkgs)

    def pip_list_tab(self):
        py = get_python_command()
        if py is None:
            QMessageBox.critical(self, "Không tìm thấy Python", "Chưa tìm thấy Python.")
            return
        self.statusBar().showMessage("Đang lấy danh sách thư viện...", 5000)

        def show(res):
            code, out, err = res
            self.new_tab(content=out if code == 0 else (err or out))

        self._capture_async(py + ["-m", "pip", "list", "--disable-pip-version-check"], show, 60)

    #  git
    def _git(self, steps, cwd=None, on_done=None, need_repo=True):
        git = find_tool("git")
        if git is None:
            QMessageBox.critical(self, "Thiếu Git",
                                 "Không tìm thấy 'git' trong PATH. Hãy cài Git rồi mở lại app.")
            return
        cwd = cwd or self._project_root()
        if need_repo and steps[0][1][0] != "init" and find_up(cwd, ".git") is None:
            QMessageBox.information(self, "Git", f"'{cwd}' chưa nằm trong repo Git nào.")
            return
        self.terminal.run_queue([(lbl, git, args) for lbl, args in steps],
                                on_done=on_done or (lambda: (self._on_done(), self.git_panel.refresh())),
                                on_step=self._on_step, on_fail=self._on_fail, cwd=cwd)

    def git_clone(self):
        dlg = CloneDialog(self, self._project_root())
        if dlg.exec_() != QDialog.Accepted:
            return
        v = dlg.values()
        if not v["url"] or not v["dir"]:
            QMessageBox.warning(self, "Thiếu thông tin", "Cần nhập URL và thư mục cha.")
            return
        if v["url"].startswith("-") or v["branch"].startswith("-"):
            QMessageBox.warning(self, "Không hợp lệ", "URL / nhánh không được bắt đầu bằng '-'.")
            return
        name = clean_name(v["name"] or repo_name_from_url(v["url"]))
        args = ["clone", "--progress"]
        if v["shallow"]:
            args += ["--depth", "1"]
        if v["branch"]:
            args += ["-b", v["branch"]]
        args += ["--", v["url"], name]
        target = os.path.join(v["dir"], name)
        os.makedirs(v["dir"], exist_ok=True)

        def done():
            self._on_done()
            if os.path.isdir(target):
                self._set_explorer_root(target)
        self._git([("git clone", args)], cwd=v["dir"], on_done=done, need_repo=False)

    def git_commit(self):
        msg, ok = QInputDialog.getText(self, "Git commit", "Nội dung commit:")
        if ok and msg.strip():
            self._git([("git add", ["add", "-A"]), ("git commit", ["commit", "-m", msg.strip()])])

    #  ESP / Serial
    def open_esp_dialog(self):
        if self.esp_dialog is None:
            self.esp_dialog = EspFlashDialog(self)
        self.esp_dialog.refresh_ports()
        self.esp_dialog.show()
        self.esp_dialog.raise_()

    def open_serial_monitor(self):
        if self.serial_monitor is None:
            self.serial_monitor = SerialMonitorDialog(self)
        self.serial_monitor.show()
        self.serial_monitor.raise_()

    def esptool_run(self, actions, chip, port, baud):
        py = get_python_command()
        if py is None:
            QMessageBox.critical(self, "Không tìm thấy Python",
                                 "Cần Python thật để chạy esptool.")
            return
        sm = self.serial_monitor      # esptool cần cổng rảnh
        if sm is not None and sm.is_open():
            sm.close_port()
            self.terminal.appendPlainText("[Đã đóng Serial Monitor để esptool dùng cổng]")
        steps = [(lbl, py[0], build_esptool_args(py, chip, port, baud, act))
                 for lbl, act in actions]
        self.terminal.run_queue(steps, on_done=self._on_done, on_step=self._on_step,
                                on_fail=self._on_esp_fail, cwd=self._project_root())

    def _on_esp_fail(self, label, code):
        self._on_fail(label, code)
        if "No module named esptool" in self.terminal.last_output:
            QTimer.singleShot(0, self._offer_esptool)

    def _offer_esptool(self):
        if QMessageBox.question(self, "Thiếu esptool",
                                "Chưa cài 'esptool'. Cài ngay?") == QMessageBox.Yes:
            self._pip_install(["esptool"])

    #  plugin
    def _trusted_plugins(self):
        try:
            d = json.loads(self.settings.value("plugins/trusted", "{}") or "{}")
            return d if isinstance(d, dict) else {}
        except (ValueError, TypeError):
            return {}

    def forget_trusted_plugins(self):
        self.settings.setValue("plugins/trusted", "{}")
        self.statusBar().showMessage("Đã xóa danh sách plugin tin tưởng", 3000)

    def unload_plugins(self):
        for name, api, mod in reversed(self.plugin_apis):
            try:
                fn = getattr(mod, "unregister", None)
                if fn:
                    fn(api)
            except Exception:  # noqa: BLE001
                self.terminal.appendPlainText(
                    f"[plugin {name}] LỖI khi gỡ:\n" + traceback.format_exc())
            api.unload()
        self.plugin_apis = []

    def load_plugins(self):
        self.unload_plugins()
        trusted = self._trusted_plugins()
        seen, loaded, missing = set(), 0, set()
        for d in app_plugin_dirs():
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.endswith(".py") or fn.startswith("_"):
                    continue
                name, path = fn[:-3], os.path.join(d, fn)
                if name in seen:
                    continue
                seen.add(name)
                if name in self._plugin_disabled():
                    self.terminal.appendPlainText(f"[plugin {name}] đang tắt (Plugins > Quản lý plugin)")
                    continue
                try:
                    with open(path, "rb") as f:
                        digest = hashlib.sha256(f.read()).hexdigest()
                except OSError:
                    continue
                if trusted.get(path) != digest and not is_bundled_verified(path, digest):
                    r = QMessageBox.question(
                        self, "Cho phép plugin?",
                        f"Plugin '{name}' sẽ chạy code Python với toàn quyền của bạn.\n{path}\n\n"
                        "Chỉ chọn Yes nếu bạn tin nguồn của file này.")
                    if r != QMessageBox.Yes:
                        self.terminal.appendPlainText(f"[plugin {name}] bỏ qua (chưa được tin tưởng)")
                        continue
                    trusted[path] = digest
                    self.settings.setValue("plugins/trusted", json.dumps(trusted))
                if not self._plugin_precheck(path, name):
                    continue
                api = PyAppAPI(self, name)
                try:
                    spec = importlib.util.spec_from_file_location(f"pyapp_plugin_{name}", path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    mod.register(api)
                    self.plugin_apis.append((name, api, mod))
                    loaded += 1
                except Exception as exc:  # noqa: BLE001
                    api.unload()
                    self.terminal.appendPlainText(
                        f"[plugin {name}] LỖI khi nạp:\n" + traceback.format_exc())
                    if isinstance(exc, ModuleNotFoundError) and exc.name:
                        missing.add(exc.name)
        self.statusBar().showMessage(f"Đã nạp {loaded} plugin", 3000)
        if missing:
            self._offer_plugin_libs(missing)

    def _offer_plugin_libs(self, missing):
        """Plugin thiếu thư viện: hỏi rồi tự cài vào ~/.pyapp/libs và nạp lại."""
        qt = sorted(n for n in missing if n.split(".")[0] == "PyQt5")
        if qt:
            self.terminal.appendPlainText(
                "[plugin] Thiếu module Qt: " + ", ".join(qt) + ". Module Qt nằm sẵn trong app "
                "nên không cài bằng pip được; hãy dùng bản build mới nhất của app.")
        pkgs = sorted({PIP_NAME_MAP.get(n.split(".")[0], n.split(".")[0])
                       for n in missing if n.split(".")[0] != "PyQt5"})
        tried = getattr(self, "_plugin_libs_tried", set())
        pkgs = [p for p in pkgs if p not in tried]
        if not pkgs:
            return
        py_cmd = get_python_command()
        if py_cmd is None:
            self.terminal.appendPlainText(
                "[plugin] Thiếu thư viện " + ", ".join(pkgs) + " nhưng máy chưa có Python để cài.")
            return
        r = QMessageBox.question(
            self, "Plugin thiếu thư viện",
            f"Plugin cần thư viện: {', '.join(pkgs)}\n\nCài vào {user_libs_dir()} "
            "rồi tự nạp lại plugin?")
        if r != QMessageBox.Yes:
            return
        self._plugin_libs_tried = tried | set(pkgs)
        steps = [("Cài thư viện cho plugin", py_cmd[0],
                  py_cmd[1:] + ["-m", "pip", "install", "--disable-pip-version-check",
                                "--upgrade", "--target", user_libs_dir()] + pkgs)]
        self.terminal.run_queue(steps, on_done=lambda: self._after_plugin_libs(reload=True),
                                on_step=self._on_step, on_fail=self._on_fail)

    def create_sample_plugin(self):
        path = os.path.join(user_plugin_dir(), "hello.py")
        if os.path.exists(path):
            self.open_path(path)
            return
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(SAMPLE_PLUGIN)
        self.open_path(path)
        self.terminal.appendPlainText(f"Đã tạo plugin mẫu: {path}  (lưu rồi chọn Plugins > Tải lại plugins)")

    def show_api_reference(self):
        ed = self.new_tab(content=api_reference_text())
        ed.set_language("python")

    def run_as_script(self):
        ed = self.current_editor()
        if ed is None:
            return
        ns = {"__name__": "__script__", "api": self._script_api}
        try:
            exec(compile(ed.toPlainText(), ed.file_path or "<script>", "exec"), ns)
        except Exception:  # noqa: BLE001
            self.terminal.appendPlainText("\n[script] LỖI:\n" + traceback.format_exc())


# PHẦN 1 - Logic thuần Python (không phụ thuộc Qt)
# Bộ đọc mesh (GLB/glTF/OBJ/STL/PLY/FBX), Hex, PyTorch (.pt) an toàn, Intel HEX,
# và bộ kiểm tra API plugin trước khi nhập.
import struct as _struct
import zlib as _zlib
import pickle as _pickle
import pickletools as _pickletools
import collections as _collections
