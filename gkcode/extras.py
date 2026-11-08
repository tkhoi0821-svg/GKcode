# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp', 'templates', 'polyglot', 'plugins', 'textools', 'toolsmixin', 'viewers', 'media', 'prefs']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


# Hàm mở file + ghép vào cửa sổ chính
def _op_image(win, path):
    win._show(ImageViewerDialog(win, path))
    return True


def _op_mesh(win, path):
    try:
        dlg = MeshViewerDialog(win, path)
    except (ValueError, OSError, KeyError, IndexError, _struct.error) as e:
        win.terminal.appendPlainText("[3D] %s: không dựng được mesh (%s)" % (os.path.basename(path), e))
        return False
    _std_dialog(win, dlg)
    return True


def _op_media(win, path):
    try:
        dlg = MediaPlayerDialog(win, path)
    except ImportError:
        win.terminal.appendPlainText("Thiếu QtMultimedia → mở bằng trình phát của hệ thống: " + path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        return True
    _std_dialog(win, dlg)
    return True


def _op_torch(win, path):
    try:
        dlg = TorchInspectDialog(win, path)
    except Exception as e:  # noqa: BLE001
        win.terminal.appendPlainText("[pt] %s: %s" % (os.path.basename(path), e))
        return False
    _std_dialog(win, dlg)
    return True


def _op_hex(win, path):
    if not cfg_get(win, "openers/hex_unknown", True, bool):
        win.terminal.appendPlainText(f"Bỏ qua file nhị phân: {path}")
        return True
    win.terminal.appendPlainText(f"File nhị phân → mở bằng Hex viewer: {path}")
    _std_dialog(win, HexViewerDialog(win, path))
    return True


def _ver_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:4]) or (0,)


class UpdateCheckThread(QThread):
    """Hỏi GitHub phiên bản mới nhất (đọc APP_VERSION trong gkcode/common.py của nhánh main/master)."""
    result = pyqtSignal(str, str)          # (phiên bản mới nhất, lỗi)

    def run(self):
        err = ""
        for branch in ("main", "master"):
            url = "https://raw.githubusercontent.com/%s/%s/gkcode/common.py" % (REPO_SLUG, branch)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "GKcode-update-check"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    txt = r.read(200000).decode("utf-8", "replace")
                m = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', txt, re.M)
                if m:
                    self.result.emit(m.group(1), "")
                    return
                err = "Không đọc được số phiên bản trên GitHub"
            except Exception as e:  # noqa: BLE001
                err = str(e)
        self.result.emit("", err)


class ExtrasMixin:
    """Chức năng mở rộng của GKcode 4.2 (trình mở file, Dựng nhanh, kiểm API plugin, cài đặt mới)."""

    #  đăng ký
    def _register_extras(self):
        OPENERS[:] = [o for o in OPENERS if o["owner"]]
        register_opener("image", "Trình xem ảnh", sorted(image_exts() - {".svg"}), _op_image)
        register_opener("mesh", "Mesh 3D (GLB/FBX/OBJ/STL/PLY...)", sorted(MESH_EXTS), _op_mesh)
        register_opener("media", "Video / Audio", sorted(MEDIA_EXTS), _op_media)
        register_opener("torch", "PyTorch / safetensors", [".pt", ".pth", ".ckpt", ".safetensors"], _op_torch)
        register_more_openers()
        register_opener("hex", "Hex viewer (mọi file nhị phân còn lại)", ["*"], _op_hex)
        self._register_run_langs()

    #  v4.4: outline, markdown preview, thống kê
    #  kiểm tra cập nhật (GitHub)
    def check_for_updates(self):
        if getattr(self, "_upd_thread", None) is not None:
            return
        self.statusBar().showMessage("Đang kiểm tra cập nhật...", 5000)
        th = UpdateCheckThread(self)
        self._upd_thread = th
        th.result.connect(self._on_update_result)
        th.finished.connect(lambda: setattr(self, "_upd_thread", None))
        th.finished.connect(th.deleteLater)
        th.start()

    def _on_update_result(self, latest, err):
        if err and not latest:
            QMessageBox.warning(self, "Kiểm tra cập nhật",
                                "Không kiểm tra được (có thể chưa có mạng hoặc repo chưa công khai):\n%s" % err)
            return
        if _ver_tuple(latest) > _ver_tuple(APP_VERSION):
            box = QMessageBox(self)
            box.setWindowTitle("Có bản mới")
            box.setText("GKcode %s đã ra mắt (bạn đang dùng %s)." % (latest, APP_VERSION))
            box.setInformativeText("Mở trang GitHub để tải bản mới?")
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if box.exec_() == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl(REPO_URL + "/releases"))
        else:
            QMessageBox.information(self, "Kiểm tra cập nhật", "Bạn đang dùng bản mới nhất (%s)." % APP_VERSION)

    def open_github(self):
        QDesktopServices.openUrl(QUrl(REPO_URL))

    def open_github_issues(self):
        QDesktopServices.openUrl(QUrl(REPO_URL + "/issues/new"))

    def show_markdown_preview(self):
        from PyQt5.QtWidgets import QTextBrowser
        ed = self.current_editor()
        if ed is None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Xem trước Markdown")
        dlg.resize(760, 640)
        lay = QVBoxLayout(dlg)
        tb = QTextBrowser()
        tb.setOpenExternalLinks(True)
        tb.setMarkdown(ed.toPlainText())
        lay.addWidget(tb)
        dlg.exec_()

    def show_doc_stats(self):
        ed = self.current_editor()
        if ed is None:
            return
        t = ed.toPlainText()
        sel = ed.textCursor().selectedText()
        lines = t.split("\n")
        nospace = len(re.sub(r"\s", "", t))
        msg = (f"Dòng: {len(lines)}  (không rỗng: {sum(1 for l in lines if l.strip())})\n"
               f"Từ: {len(t.split())}\nKý tự: {len(t)}  (không tính khoảng trắng: "
               f"{nospace})\nByte UTF-8: {len(t.encode('utf-8'))}")
        if sel:
            msg += f"\n\nĐang chọn: {len(sel)} ký tự, {len(sel.split())} từ"
        QMessageBox.information(self, "Thống kê tài liệu", msg)

    def _register_run_langs(self):
        def reg(key, label, exts, comment, kws, steps, tool_names):
            if tool_names and not find_tool(*tool_names):
                return
            for e in exts:
                EXT_TO_LANG[e] = key
                TEXT_EXTS.add(e)
            LANGUAGE_LABELS[key] = label
            LANG_EXT[key] = exts[0]
            LANG_CFG[key] = dict(line=comment, block=False, triple=(), backtick=False, preproc=False,
                                 brace=False, indent="    ")
            KEYWORDS[key] = list(kws)
            RUN_TEMPLATES[key] = {"steps": steps, "need": []}
            RUNNABLE.add(key)
        bat_kw = ["echo", "set", "if", "else", "for", "in", "do", "goto", "call", "exit", "pause", "rem", "setlocal",
                  "endlocal", "cd", "dir", "copy", "move", "del", "mkdir", "rmdir", "start", "title", "cls",
                  "errorlevel", "exist", "not", "defined", "equ", "neq", "lss", "leq", "gtr", "geq", "chcp", "type"]
        if os.name == "nt":
            reg("batch", "Batch (.bat/.cmd)", [".bat", ".cmd"], "::", bat_kw + [k.upper() for k in bat_kw],
                [("Chạy batch", "cmd", ["/c", "call", "{file}"])], ("cmd",))
            reg("powershell", "PowerShell", [".ps1"], "#",
                ["function", "param", "if", "else", "elseif", "foreach", "for", "while", "return", "try", "catch",
                 "finally", "switch", "throw", "Write-Host", "Write-Output", "Get-ChildItem"],
                [("Chạy PowerShell", find_tool("powershell", "pwsh") or "powershell",
                  ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "{file}"])], ("powershell", "pwsh"))
        else:
            reg("powershell", "PowerShell", [".ps1"], "#", ["function", "param", "if", "else", "foreach", "return"],
                [("Chạy PowerShell", "pwsh", ["-NoProfile", "-File", "{file}"])], ("pwsh",))
        reg("bash", "Shell (.sh)", [".sh"], "#",
            ["if", "then", "else", "elif", "fi", "for", "while", "do", "done", "case", "esac", "function", "echo",
             "exit", "export", "local", "return", "set", "source"],
            [("Chạy shell", find_tool("bash", "sh") or "bash", ["{file}"])], ("bash", "sh"))

    #  mở file
    def _open_unknown_binary(self, path):
        _op_hex(self, path)

    def open_with_dialog(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Chọn file để mở bằng trình xem", self._project_root(),
                                                  "Tất cả (*)")
            if not path:
                return
        names = [o["name"] for o in OPENERS if opener_enabled(self, o)]
        names += ["Hex viewer", "Trình soạn thảo (text)", "Chương trình mặc định của hệ thống"]
        pick, ok = QInputDialog.getItem(self, "Mở bằng", os.path.basename(path), names, 0, False)
        if not ok:
            return
        if pick == "Hex viewer":
            _std_dialog(self, HexViewerDialog(self, path))
        elif pick == "Trình soạn thảo (text)":
            self.open_path(path, force_text=True)
        elif pick.startswith("Chương trình"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            for o in OPENERS:
                if o["name"] == pick:
                    try:
                        o["fn"](self, path)
                    except Exception:  # noqa: BLE001
                        self.terminal.appendPlainText(traceback.format_exc())

    def _pick_and_open(self, title, filt, fn):
        p, _ = QFileDialog.getOpenFileName(self, title, self._project_root(), filt)
        if p:
            fn(self, p)

    def view_mesh(self):
        self._pick_and_open("Chọn mesh 3D", "Mesh (*.glb *.gltf *.fbx *.obj *.stl *.ply *.off);;Tất cả (*)", _op_mesh)

    def view_hex(self):
        self._pick_and_open("Chọn file", "Tất cả (*)", lambda w, p: _std_dialog(w, HexViewerDialog(w, p)))

    def view_media(self):
        self._pick_and_open("Chọn video / audio", "Media (*" + " *".join(sorted(MEDIA_EXTS)) + ");;Tất cả (*)", _op_media)

    def view_torch(self):
        self._pick_and_open("Chọn .pt / .pth / .safetensors", "Model (*.pt *.pth *.ckpt *.safetensors);;Tất cả (*)",
                            _op_torch)

    def view_intelhex(self):
        ed = self.current_editor()
        if ed is None:
            return
        _std_dialog(self, IntelHexDialog(self, ed.file_path, ed.toPlainText()))

    def open_quickcut(self, paths=()):
        _std_dialog(self, QuickCutDialog(self, list(paths)))

    def _extras_view_menu(self, vm, tm):
        vm.addSeparator()
        self._act("Mở file bằng trình xem...", self.open_with_dialog, None, vm)
        self._act("Mesh 3D (GLB / FBX / OBJ / STL / PLY)...", self.view_mesh, None, vm)
        self._act("Hex viewer...", self.view_hex, None, vm)
        self._act("Phát video / audio...", self.view_media, None, vm)
        self._act("PyTorch .pt / safetensors...", self.view_torch, None, vm)
        self._act("Intel HEX (tab hiện tại)", self.view_intelhex, None, vm)
        self._act("Dựng nhanh - dựng video...", self.open_quickcut, "Ctrl+Alt+V", tm)

    def _run_special(self, ed):
        """F5 trên file không phải ngôn ngữ chạy được: .hex / mesh text / svg → mở trình xem tương ứng."""
        p = ed.file_path
        if not p:
            return False
        ext = os.path.splitext(p)[1].lower()
        if ed.lang in RUNNABLE or ext not in (".hex", ".obj", ".gltf", ".off", ".ply", ".stl", ".svg"):
            return False
        if ed.document().isModified() and not self._save_editor(ed):
            return True
        if ext == ".hex":
            _std_dialog(self, IntelHexDialog(self, p, ed.toPlainText()))
        elif ext == ".svg":
            _op_image(self, p)
        else:
            _op_mesh(self, p)
        return True

    #  cài đặt
    def _apply_extra_prefs(self, v):
        s = self.settings
        for k, key in (("img_bg", "img/bg"), ("img_smooth", "img/smooth"), ("img_fit_cap", "img/fit_cap"),
                       ("img_slide", "img/slide_secs"), ("mesh_max", "mesh/max_faces"), ("mesh_wire", "mesh/wire"),
                       ("ffmpeg", "ffmpeg/path"), ("autoplay", "media/autoplay"), ("crf", "cut/crf"),
                       ("preset", "cut/preset"), ("api_mode", "api/mode"), ("hex_unknown", "openers/hex_unknown")):
            if k in v:
                s.setValue(key, v[k])
        if "openers" in v:
            s.setValue("openers/config", json.dumps(v["openers"]))

    def _apply_prefs(self, v):
        UI_OPTS["status_accent"] = bool(v.get("status_accent", True))
        UI_OPTS["radius"] = int(v.get("radius", 8))
        self.settings.setValue("ui/status_accent", UI_OPTS["status_accent"])
        self.settings.setValue("ui/radius", UI_OPTS["radius"])
        self.set_theme(v["theme"])
        if v["font_size"] != self.font_size:
            self.font_size = v["font_size"]
            for i in range(self.tabs.count()):
                self.tabs.widget(i).set_font_size(self.font_size)
        self.set_tab_size(v["tab_size"])
        self.autosave_secs = v["autosave"]
        self._apply_autosave_timer()
        self.set_interpreter(v["python"])
        self.word_wrap = v["wrap"]
        self.toggle_wrap(v["wrap"])
        self.toggle_whitespace(v["ws"])
        self.toggle_guides(v["guides"])
        self.toggle_trim_on_save(v["trim"])
        self.toggle_autosave_run(v["runsave"])
        for key, act in getattr(self, "_chk", {}).items():
            act.blockSignals(True)
            act.setChecked(v[key])
            act.blockSignals(False)
        self._apply_extra_prefs(v)
        self._save_session()
        self.statusBar().showMessage("Đã lưu cài đặt", 3000)

    #  kiểm API plugin
    def _check_plugin_file(self, path):
        with open(path, "rb") as f:
            raw = f.read()
        src = raw.decode("utf-8-sig", errors="replace")
        rep = check_plugin_source(src, path, public_api_names(), API_VERSION, module_available)
        return rep, hashlib.sha256(raw).hexdigest()

    def _plugin_precheck(self, path, name):
        """True = cho nạp. Dùng ở load_plugins: kiểm tĩnh bằng ast, không chạy code plugin."""
        mode = cfg_get(self, "api/mode", "warn") or "warn"
        if mode == "off":
            return True
        try:
            rep, digest = self._check_plugin_file(path)
        except OSError:
            return True
        for w in rep["warnings"][:5]:
            self.terminal.appendPlainText("[plugin %s] cảnh báo: %s" % (name, w))
        if rep["ok"]:
            return True
        try:
            seen = json.loads(self.settings.value("plugins/checked", "{}") or "{}")
        except (ValueError, TypeError):
            seen = {}
        if seen.get(path) == digest:
            return True
        if mode == "strict":
            self.terminal.appendPlainText("[plugin %s] BỊ CHẶN (chế độ nghiêm ngặt):\n%s" % (
                name, format_plugin_report(rep, name)))
            return False
        if PluginCheckDialog(self, name, rep, "load").exec_() == QDialog.Accepted:
            seen[path] = digest
            self.settings.setValue("plugins/checked", json.dumps(seen))
            return True
        self.terminal.appendPlainText("[plugin %s] bỏ qua (không qua kiểm API)" % name)
        return False

    def _plugin_disabled(self):
        try:
            d = json.loads(self.settings.value("plugins/disabled", "[]") or "[]")
            return set(d) if isinstance(d, list) else set()
        except (ValueError, TypeError):
            return set()

    def _set_plugin_disabled(self, names):
        self.settings.setValue("plugins/disabled", json.dumps(sorted(names)))

    def open_plugin_manager(self):
        PluginManagerDialog(self).exec_()

    def import_plugin(self):
        """Nhập plugin .py vào thư mục plugins - kiểm API TRƯỚC khi chép/nạp."""
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn plugin (.py) để nhập", "", "Plugin Python (*.py)")
        self.import_plugin_sources(files)

    def import_plugin_sources(self, files):
        done = 0
        for src in files:
            name = os.path.splitext(os.path.basename(src))[0]
            try:
                rep, digest = self._check_plugin_file(src)
            except OSError as e:
                QMessageBox.warning(self, "Lỗi", "Không đọc được %s: %s" % (src, e))
                continue
            if PluginCheckDialog(self, name, rep, "import").exec_() != QDialog.Accepted:
                continue
            dest = os.path.join(user_plugin_dir(), name + ".py")
            if os.path.exists(dest) and QMessageBox.question(
                    self, "Ghi đè?", "Đã có plugin '%s'. Ghi đè?" % name) != QMessageBox.Yes:
                continue
            shutil.copyfile(src, dest)
            trusted = self._trusted_plugins()
            trusted[dest] = digest          # người dùng vừa xem báo cáo và đồng ý nhập
            self.settings.setValue("plugins/trusted", json.dumps(trusted))
            try:
                seen = json.loads(self.settings.value("plugins/checked", "{}") or "{}")
            except (ValueError, TypeError):
                seen = {}
            seen[dest] = digest
            self.settings.setValue("plugins/checked", json.dumps(seen))
            dis = self._plugin_disabled()
            if name in dis:
                dis.discard(name)
                self._set_plugin_disabled(dis)
            done += 1
        if done:
            self.load_plugins()
            self.statusBar().showMessage("Đã nhập %d plugin" % done, 4000)

    def check_plugin_current(self):
        ed = self.current_editor()
        if ed is None:
            return
        name = os.path.basename(ed.file_path or "tab hiện tại")
        rep = check_plugin_source(ed.toPlainText(), name, public_api_names(), API_VERSION, module_available)
        PluginCheckDialog(self, name, rep, "view").exec_()

    def check_all_plugins(self):
        lines = ["# Báo cáo kiểm API plugin (API %s)" % API_VERSION, ""]
        for d in app_plugin_dirs():
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".py") and not fn.startswith("_"):
                    try:
                        rep, _dg = self._check_plugin_file(os.path.join(d, fn))
                        lines += [format_plugin_report(rep, fn), "", "-" * 60, ""]
                    except OSError:
                        pass
        self.new_tab(content="\n".join(lines))
