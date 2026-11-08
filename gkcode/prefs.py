# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp', 'templates', 'polyglot', 'plugins', 'textools', 'toolsmixin', 'viewers', 'media']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


# PHẦN 2D - Kiểm API plugin, Cài đặt mới (dạng tab), ExtrasMixin cho cửa sổ chính
def public_api_names():
    names = {n for n, _m in inspect.getmembers(PyAppAPI) if not n.startswith("_")}
    return names | {"win", "name"}


def module_available(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


class PluginCheckDialog(QDialog):
    """Báo cáo kiểm tra API. mode: 'import' (Nhập), 'load' (Nạp bất chấp), 'view' (chỉ xem)."""

    def __init__(self, win, name, rep, mode="view"):
        super().__init__(win)
        self.win, self.rep = win, rep
        self.setWindowTitle("Kiểm API plugin - " + name)
        self.resize(640, 460)
        lay = QVBoxLayout(self)
        head = QLabel(("✔ Đạt: " if rep["ok"] else "✘ Có lỗi: ") + name)
        head.setStyleSheet("font-weight:600;font-size:14px;color:%s;" % ("#4caf50" if rep["ok"] else "#ef5350"))
        lay.addWidget(head)
        txt = QPlainTextEdit()
        txt.setReadOnly(True)
        txt.setFont(mono_font(9))
        txt.setPlainText(format_plugin_report(rep, name))
        lay.addWidget(txt, 1)
        bb = QHBoxLayout()
        if rep["missing_modules"]:
            pk = sorted({PIP_NAME_MAP.get(m, m) for m in rep["missing_modules"]})
            b = QPushButton("Cài thư viện thiếu (%s)" % ", ".join(pk))
            b.clicked.connect(lambda: win._pip_install(pk))
            bb.addWidget(b)
        bb.addStretch(1)
        if mode == "view":
            ok = QPushButton("Đóng")
            ok.clicked.connect(self.accept)
            bb.addWidget(ok)
        else:
            ok = QPushButton("Nhập plugin" if mode == "import" else "Vẫn nạp")
            if not rep["ok"]:
                ok.setText(ok.text() + " (bất chấp lỗi)")
            ok.clicked.connect(self.accept)
            cancel = QPushButton("Hủy")
            cancel.clicked.connect(self.reject)
            bb.addWidget(ok)
            bb.addWidget(cancel)
        lay.addLayout(bb)


class PreferencesDialog(QDialog):
    """Cài đặt dạng tab: tìm kiếm, nhiều nhóm, xuất/nhập JSON, đặt lại, Áp dụng."""

    DEFAULTS = {"img_bg": "checker", "img_smooth": True, "img_fit_cap": True, "img_slide": 3,
                "mesh_max": 25000, "mesh_wire": False, "ffmpeg": "", "autoplay": True, "crf": 23,
                "preset": "veryfast", "api_mode": "warn", "hex_unknown": True}
    SKIP_EXPORT = ("plugins/trusted", "plugins/checked")

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Cài đặt (Preferences)")
        self.resize(1000, 700)
        self._orig_theme = win.theme_name
        outer = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setObjectName("prefSearch")
        self.search.setPlaceholderText("🔍 Tìm cài đặt...  (vd: ảnh, ffmpeg, tab, plugin, hex)")
        self.search.textChanged.connect(self._filter)
        outer.addWidget(self.search)
        body = QHBoxLayout()
        self.nav = QListWidget()
        self.nav.setObjectName("prefNav")
        self.nav.setFixedWidth(230)
        self.nav.setFocusPolicy(Qt.NoFocus)
        self.stack = QStackedWidget()
        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)
        outer.addLayout(body, 1)
        self.pages = []
        self._build_pages()
        for lb in self.stack.findChildren(QLabel):
            if not lb.objectName():
                lb.setWordWrap(True)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)
        row = QHBoxLayout()
        for text, fn in (("Xuất JSON...", self.export_json), ("Nhập JSON...", self.import_json),
                         ("Đặt lại mặc định", self.reset_defaults)):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, f=fn: f())
            row.addWidget(b)
        row.addStretch(1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        bb.button(QDialogButtonBox.Apply).clicked.connect(lambda: win._apply_prefs(self.values()))
        row.addWidget(bb)
        outer.addLayout(row)

    #  dựng trang
    def _page(self, title, keywords):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 14, 22, 14)
        hdr = QLabel(title.strip())
        hdr.setObjectName("prefTitle")
        lay.addWidget(hdr)
        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(16)
        lay.addLayout(form)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        sc.setWidget(w)
        self.stack.addWidget(sc)
        self.nav.addItem(title)
        self.nav.item(self.nav.count() - 1).setSizeHint(QSize(0, 42))
        self.pages.append((title, keywords.lower() + " " + title.lower()))
        return form, lay

    def _build_pages(self):
        win = self.win
        s = win.settings
        #  Giao diện
        form, lay = self._page("🎨  Giao diện", "theme giao diện font chữ cỡ")
        self.theme = QComboBox()
        for k, t in THEMES.items():
            self.theme.addItem(t["label"], k)
        self.theme.setCurrentIndex(max(0, self.theme.findData(win.theme_name)))
        self.font = QSpinBox()
        self.font.setRange(7, 40)
        self.font.setValue(win.font_size)
        form.addRow("Giao diện:", self.theme)
        form.addRow("Cỡ chữ:", self.font)
        self.status_acc = QCheckBox("Thanh trạng thái tô màu nhấn (accent)")
        self.status_acc.setChecked(UI_OPTS["status_accent"])
        self.radius = QSpinBox()
        self.radius.setRange(0, 16)
        self.radius.setSuffix(" px")
        self.radius.setValue(UI_OPTS["radius"])
        form.addRow("Bo góc giao diện:", self.radius)
        form.addRow(self.status_acc)
        self.status_acc.toggled.connect(lambda _=False: self._live_ui())
        self.radius.valueChanged.connect(lambda _=0: self._live_ui())
        #  trình chỉnh màu theme
        self._dirty = False
        self._cust = dict(THEMES[win.theme_name])
        grp = QGroupBox("🎛  Tùy chỉnh màu (xem trước trực tiếp)")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(14)
        g.setVerticalSpacing(8)
        self._cbtn = {}
        for i, (k, lab) in enumerate(THEME_EDIT_KEYS):
            b = QPushButton()
            b.setFixedSize(78, 26)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, kk=k, ll=lab: self._pick_color(kk, ll))
            self._cbtn[k] = b
            g.addWidget(QLabel(lab), i // 2, (i % 2) * 2)
            g.addWidget(b, i // 2, (i % 2) * 2 + 1)
        brow = QHBoxLayout()
        for text, fn in (("💾 Lưu thành theme mới...", self._save_as), ("↩ Hoàn tác màu", self._undo_colors),
                         ("🗑 Xóa theme riêng", self._delete_theme)):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, f=fn: f())
            brow.addWidget(b)
        brow.addStretch(1)
        g.addLayout(brow, (len(THEME_EDIT_KEYS) + 1) // 2, 0, 1, 4)
        lay.addWidget(grp)
        lay.addWidget(QLabel("Chọn theme gốc ở ô 'Giao diện' rồi đổi từng màu. Bấm OK/Áp dụng để lưu "
                             "(sửa theme có sẵn sẽ lưu thành 'Theme của tôi')."))
        self._refresh_btns()
        self.theme.currentIndexChanged.connect(self._theme_changed)
        lay.addStretch(1)
        #  Soạn thảo
        form, lay = self._page("✏️  Soạn thảo", "tab wrap xuống dòng khoảng trắng thụt lề trim lưu")
        self.tab = QComboBox()
        self.tab.addItems(["2", "4", "8"])
        self.tab.setCurrentText(str(win.tab_size))
        self.wrap = QCheckBox("Tự xuống dòng (word wrap)")
        self.wrap.setChecked(win.word_wrap)
        self.ws = QCheckBox("Hiện khoảng trắng / tab")
        self.ws.setChecked(win.show_ws)
        self.guides = QCheckBox("Hiện đường kẻ thụt lề")
        self.guides.setChecked(win.show_guides)
        self.trim = QCheckBox("Tự dọn khoảng trắng cuối dòng khi lưu")
        self.trim.setChecked(win.trim_on_save)
        form.addRow("Độ rộng Tab:", self.tab)
        for w in (self.wrap, self.ws, self.guides, self.trim):
            form.addRow(w)
        lay.addStretch(1)
        #  Chạy & Python
        form, lay = self._page("▶️  Chạy & Python", "python interpreter venv autosave tự lưu chạy f5 bat sh")
        self.autosave = QSpinBox()
        self.autosave.setRange(0, 3600)
        self.autosave.setSuffix(" giây (0 = tắt)")
        self.autosave.setValue(win.autosave_secs)
        self.runsave = QCheckBox("Tự lưu file trước khi chạy (F5)")
        self.runsave.setChecked(win.autosave_before_run)
        py_row = QHBoxLayout()
        self.py_edit = QLineEdit(s.value("py/interpreter", "") or "")
        self.py_edit.setPlaceholderText("(mặc định: Python hệ thống / py launcher)")
        browse = QPushButton("Chọn...")
        venv = QPushButton("venv dự án")
        py_row.addWidget(self.py_edit, 1)
        py_row.addWidget(browse)
        py_row.addWidget(venv)
        browse.clicked.connect(self._browse)
        venv.clicked.connect(self._venv)
        form.addRow("Tự lưu mỗi:", self.autosave)
        form.addRow("Python interpreter:", py_row)
        form.addRow(self.runsave)
        form.addRow(QLabel("F5 chạy được: .py .c .cpp .go .java .js .bat/.cmd .ps1 .sh; "
                           "F5 trên .hex mở trình phân tích Intel HEX."))
        lay.addStretch(1)
        #  Trình mở file
        form, lay = self._page("📂  Trình mở file", "opener mở file fbx glb binary nhị phân hex plugin đuôi")
        self.chk_hex = QCheckBox("File nhị phân không ai nhận → mở bằng Hex viewer (thay vì 'Bỏ qua file nhị phân')")
        self.chk_hex.setChecked(cfg_get(win, "openers/hex_unknown", True, bool))
        form.addRow(self.chk_hex)
        self.otable = QTableWidget(0, 4)
        self.otable.setHorizontalHeaderLabels(["Bật", "Trình mở", "Đuôi file (cách nhau bằng dấu cách)", "Nguồn"])
        self.otable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.otable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.otable.verticalHeader().setVisible(False)
        conf = _opener_config(win)
        for o in OPENERS:
            r = self.otable.rowCount()
            self.otable.insertRow(r)
            c = conf.get(o["key"], {})
            it0 = QTableWidgetItem("")
            it0.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            it0.setCheckState(Qt.Checked if c.get("enabled", True) else Qt.Unchecked)
            it1 = QTableWidgetItem(o["name"])
            it1.setFlags(Qt.ItemIsEnabled)
            it1.setData(Qt.UserRole, o["key"])
            ex = " ".join(e.lstrip(".") for e in opener_exts(win, o)) or ("(mọi file nhị phân)" if o["any"] else "")
            it2 = QTableWidgetItem(ex)
            if o["any"] and not o["exts"]:
                it2.setFlags(Qt.ItemIsEnabled)
            it3 = QTableWidgetItem("Plugin: " + o["owner"] if o["owner"] else "Có sẵn")
            it3.setFlags(Qt.ItemIsEnabled)
            for k, it in enumerate((it0, it1, it2, it3)):
                self.otable.setItem(r, k, it)
        lay.addWidget(self.otable, 1)
        lay.addWidget(QLabel("Plugin có thể thêm trình mở riêng bằng api.register_opener(...) "
                             "(ví dụ mở .blend, .dae, .3ds). Trình mở của plugin được thử trước."))
        #  Ảnh
        form, lay = self._page("🖼️  Trình xem ảnh", "ảnh image nền caro zoom slideshow")
        self.img_bg = QComboBox()
        for k, t in (("checker", "Caro (thấy trong suốt)"), ("dark", "Tối"), ("light", "Sáng"), ("black", "Đen")):
            self.img_bg.addItem(t, k)
        self.img_bg.setCurrentIndex(max(0, self.img_bg.findData(cfg_get(win, "img/bg", "checker"))))
        self.img_smooth = QCheckBox("Làm mịn khi phóng to nhỏ (tắt tự động khi zoom ≥ 400%)")
        self.img_smooth.setChecked(cfg_get(win, "img/smooth", True, bool))
        self.img_fit = QCheckBox("'Vừa khung' không phóng to ảnh nhỏ quá 100%")
        self.img_fit.setChecked(cfg_get(win, "img/fit_cap", True, bool))
        self.img_slide = QSpinBox()
        self.img_slide.setRange(1, 60)
        self.img_slide.setSuffix(" giây / ảnh")
        self.img_slide.setValue(cfg_get(win, "img/slide_secs", 3, int))
        form.addRow("Màu nền:", self.img_bg)
        form.addRow(self.img_smooth)
        form.addRow(self.img_fit)
        form.addRow("Slideshow:", self.img_slide)
        lay.addStretch(1)
        #  3D
        form, lay = self._page("🧊  Mesh 3D", "3d mesh fbx glb obj stl ply tam giác")
        self.mesh_max = QSpinBox()
        self.mesh_max.setRange(2000, 300000)
        self.mesh_max.setSingleStep(5000)
        self.mesh_max.setValue(cfg_get(win, "mesh/max_faces", 25000, int))
        self.mesh_wire = QCheckBox("Mở mesh ở chế độ lưới (wireframe)")
        self.mesh_wire.setChecked(cfg_get(win, "mesh/wire", False, bool))
        form.addRow("Số tam giác tối đa khi vẽ:", self.mesh_max)
        form.addRow(self.mesh_wire)
        form.addRow(QLabel("Mesh lớn hơn giới hạn sẽ được giảm mẫu để vẫn xoay mượt (bản vẽ phần mềm, không GPU)."))
        lay.addStretch(1)
        #  Video
        form, lay = self._page("🎬  Video & Dựng nhanh", "video ffmpeg dựng nhanh cắt ghép crf autoplay")
        fr = QHBoxLayout()
        self.ffmpeg = QLineEdit(cfg_get(win, "ffmpeg/path", "") or "")
        self.ffmpeg.setPlaceholderText("(tự dò: PATH, imageio-ffmpeg, WinGet...)")
        fb = QPushButton("Chọn...")
        fd = QPushButton("Dò")
        fi = QPushButton("Cài imageio-ffmpeg")
        fr.addWidget(self.ffmpeg, 1)
        for b in (fb, fd, fi):
            fr.addWidget(b)
        fb.clicked.connect(self._pick_ffmpeg)
        fd.clicked.connect(self._detect_ffmpeg)
        fi.clicked.connect(lambda: win._pip_install(["imageio-ffmpeg"]))
        self.ff_info = QLabel("")
        self.autoplay = QCheckBox("Tự phát khi mở video/audio")
        self.autoplay.setChecked(cfg_get(win, "media/autoplay", True, bool))
        self.crf = QSpinBox()
        self.crf.setRange(14, 40)
        self.crf.setValue(cfg_get(win, "cut/crf", 23, int))
        self.preset = QComboBox()
        self.preset.addItems(["ultrafast", "veryfast", "medium", "slow"])
        self.preset.setCurrentText(cfg_get(win, "cut/preset", "veryfast") or "veryfast")
        form.addRow("ffmpeg:", fr)
        form.addRow(self.ff_info)
        form.addRow(self.autoplay)
        form.addRow("CRF mặc định:", self.crf)
        form.addRow("Tốc độ encode:", self.preset)
        lay.addStretch(1)
        #  Plugin & API
        form, lay = self._page("🧩  Plugin & API", "plugin api kiểm tra nhập import tin tưởng")
        self.api_mode = QComboBox()
        for k, t in (("warn", "Cảnh báo: hỏi khi plugin có lỗi API (khuyến nghị)"),
                     ("strict", "Nghiêm ngặt: chặn plugin có lỗi API"), ("off", "Tắt kiểm tra")):
            self.api_mode.addItem(t, k)
        self.api_mode.setCurrentIndex(max(0, self.api_mode.findData(cfg_get(win, "api/mode", "warn"))))
        form.addRow("Kiểm API trước khi nạp:", self.api_mode)
        for text, fn in (("Nhập plugin (kiểm API trước)...", win.import_plugin),
                         ("Kiểm tra mọi plugin đang có → tab báo cáo", win.check_all_plugins),
                         ("Quên các plugin đã tin tưởng", win.forget_trusted_plugins),
                         ("Mở thư mục plugins", lambda: QDesktopServices.openUrl(
                             QUrl.fromLocalFile(user_plugin_dir())))):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, f=fn: f())
            form.addRow(b)
        lay.addStretch(1)
        #  Nâng cao
        form, lay = self._page("⚙️  Nâng cao", "xuất nhập json reset cấu hình backup")
        form.addRow(QLabel("Nơi lưu cấu hình: " + (s.fileName() or "(registry)")))
        form.addRow(QLabel("Xuất/Nhập JSON ở góc dưới. Danh sách plugin đã tin tưởng KHÔNG nằm trong file xuất "
                           "(để file cấu hình của người khác không tự cấp quyền cho plugin)."))
        lay.addStretch(1)

    #  trình chỉnh theme
    def _refresh_btns(self):
        for k, b in self._cbtn.items():
            c = self._cust.get(k, "#000000")
            b.setStyleSheet("QPushButton { background: %s; border: 1px solid rgba(136,136,136,140); border-radius: 6px; }"
                            "QPushButton:hover { border: 2px solid %s; }" % (c, self._cust.get("accent", "#fff")))
            b.setToolTip(str(c))

    def _pick_color(self, k, lab):
        c = QColorDialog.getColor(QColor(self._cust.get(k, "#000000")), self, lab)
        if not c.isValid():
            return
        self._cust[k] = c.name()
        if k in ("bg",):
            self._cust["tab_active_bg"] = c.name()
        self._dirty = True
        self._refresh_btns()
        self.win.preview_theme(self._cust)

    def _theme_changed(self, _i=0):
        key = self.theme.currentData()
        if key in THEMES:
            self._cust = dict(THEMES[key])
            self._dirty = False
            self._refresh_btns()
            self.win.preview_theme(self._cust)

    def _undo_colors(self):
        self._theme_changed()

    def _live_ui(self):
        UI_OPTS["status_accent"] = self.status_acc.isChecked()
        UI_OPTS["radius"] = self.radius.value()
        self.win.preview_theme(self._cust)

    def _commit_custom(self, key, name=None):
        t = dict(self._cust)
        if name:
            nk = "custom_" + (re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "theme")
            label = name
        elif THEMES.get(key, {}).get("custom"):
            nk, label = key, THEMES[key]["label"]
        else:
            nk, label = "my_theme", "Theme của tôi"
        t["label"] = label
        t["custom"] = True
        self.win.save_custom_theme(nk, t)
        self.theme.blockSignals(True)
        i = self.theme.findData(nk)
        if i < 0:
            self.theme.addItem(label, nk)
            i = self.theme.findData(nk)
        self.theme.setCurrentIndex(i)
        self.theme.blockSignals(False)
        self._dirty = False
        return nk

    def _save_as(self):
        name, ok = QInputDialog.getText(self, "Lưu theme", "Tên theme mới:")
        if ok and name.strip():
            self._commit_custom(self.theme.currentData(), name.strip())

    def _delete_theme(self):
        key = self.theme.currentData()
        if not THEMES.get(key, {}).get("custom"):
            QMessageBox.information(self, "Xóa theme", "Chỉ xóa được theme riêng do bạn tạo.")
            return
        self.win.delete_custom_theme(key)
        self.theme.blockSignals(True)
        self.theme.removeItem(self.theme.findData(key))
        self.theme.setCurrentIndex(max(0, self.theme.findData(self.win.theme_name)))
        self.theme.blockSignals(False)
        self._theme_changed()

    def reject(self):
        self.win.preview_theme(THEMES.get(self._orig_theme, THEMES[DEFAULT_THEME]))
        UI_OPTS["status_accent"] = str(self.win.settings.value("ui/status_accent", "true")).lower() in ("true", "1")
        try:
            UI_OPTS["radius"] = int(self.win.settings.value("ui/radius", 8))
        except (TypeError, ValueError):
            pass
        self.win.preview_theme(THEMES.get(self._orig_theme, THEMES[DEFAULT_THEME]))
        super().reject()

    #  tiện ích
    def _filter(self, text):
        t = text.strip().lower()
        first = -1
        for i, (_title, kw) in enumerate(self.pages):
            hit = (not t) or t in kw
            self.nav.item(i).setHidden(not hit)
            if hit and first < 0:
                first = i
        if first >= 0 and self.nav.item(self.nav.currentRow()).isHidden():
            self.nav.setCurrentRow(first)

    def _browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn python", self.py_edit.text(), "Python (python*);;Tất cả (*)")
        if f:
            self.py_edit.setText(f)

    def _venv(self):
        p = find_project_python(self.win._project_root())
        if p:
            self.py_edit.setText(p)
        else:
            QMessageBox.information(self, "venv", "Không thấy .venv / venv / env trong thư mục dự án.")

    def _pick_ffmpeg(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn ffmpeg", self.ffmpeg.text(), "ffmpeg (ffmpeg*);;Tất cả (*)")
        if f:
            self.ffmpeg.setText(f)
            self._detect_ffmpeg()

    def _detect_ffmpeg(self):
        old = self.win.settings.value("ffmpeg/path", "")
        self.win.settings.setValue("ffmpeg/path", self.ffmpeg.text().strip())
        p = find_ffmpeg(self.win)
        self.win.settings.setValue("ffmpeg/path", old)
        if not p:
            self.ff_info.setText("✘ Không tìm thấy ffmpeg.")
            return
        rc, out, err = run_capture([p, "-version"], timeout=15)
        self.ff_info.setText("✔ %s\n%s" % (p, (out or err).splitlines()[0] if (out or err) else ""))

    def values(self):
        ops = {}
        for r in range(self.otable.rowCount()):
            key = self.otable.item(r, 1).data(Qt.UserRole)
            ops[key] = {"enabled": self.otable.item(r, 0).checkState() == Qt.Checked,
                        "exts": self.otable.item(r, 2).text().strip()}
            if ops[key]["exts"].startswith("(mọi"):
                ops[key].pop("exts")
        tkey = self.theme.currentData()
        if self._dirty:
            tkey = self._commit_custom(tkey)
        return {"theme": tkey, "status_accent": self.status_acc.isChecked(),
                "radius": self.radius.value(), "font_size": self.font.value(),
                "tab_size": int(self.tab.currentText()), "autosave": self.autosave.value(),
                "python": self.py_edit.text().strip(), "wrap": self.wrap.isChecked(),
                "ws": self.ws.isChecked(), "guides": self.guides.isChecked(),
                "trim": self.trim.isChecked(), "runsave": self.runsave.isChecked(),
                "img_bg": self.img_bg.currentData(), "img_smooth": self.img_smooth.isChecked(),
                "img_fit_cap": self.img_fit.isChecked(), "img_slide": self.img_slide.value(),
                "mesh_max": self.mesh_max.value(), "mesh_wire": self.mesh_wire.isChecked(),
                "ffmpeg": self.ffmpeg.text().strip(), "autoplay": self.autoplay.isChecked(),
                "crf": self.crf.value(), "preset": self.preset.currentText(),
                "api_mode": self.api_mode.currentData(), "hex_unknown": self.chk_hex.isChecked(),
                "openers": ops}

    def reset_defaults(self):
        d = self.DEFAULTS
        self.img_bg.setCurrentIndex(max(0, self.img_bg.findData(d["img_bg"])))
        self.img_smooth.setChecked(d["img_smooth"])
        self.img_fit.setChecked(d["img_fit_cap"])
        self.img_slide.setValue(d["img_slide"])
        self.mesh_max.setValue(d["mesh_max"])
        self.mesh_wire.setChecked(d["mesh_wire"])
        self.ffmpeg.setText(d["ffmpeg"])
        self.autoplay.setChecked(d["autoplay"])
        self.crf.setValue(d["crf"])
        self.preset.setCurrentText(d["preset"])
        self.api_mode.setCurrentIndex(max(0, self.api_mode.findData(d["api_mode"])))
        self.chk_hex.setChecked(d["hex_unknown"])
        for r in range(self.otable.rowCount()):
            self.otable.item(r, 0).setCheckState(Qt.Checked)
            key = self.otable.item(r, 1).data(Qt.UserRole)
            for o in OPENERS:
                if o["key"] == key and (o["exts"] or not o["any"]):
                    self.otable.item(r, 2).setText(" ".join(e.lstrip(".") for e in o["exts"]))
        QMessageBox.information(self, "Đặt lại", "Đã đặt lại các mục mới về mặc định. Bấm OK/Áp dụng để lưu.")

    def export_json(self):
        p, _ = QFileDialog.getSaveFileName(self, "Xuất cài đặt", "gkcode_settings.json", "JSON (*.json)")
        if not p:
            return
        data = {}
        for k in self.win.settings.allKeys():
            if k in self.SKIP_EXPORT:
                continue
            v = self.win.settings.value(k)
            try:
                json.dumps(v)
                data[k] = v
            except (TypeError, ValueError):
                pass
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"app": APP_NAME, "version": APP_VERSION, "settings": data}, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "Đã xuất", "%d mục → %s" % (len(data), p))

    def import_json(self):
        p, _ = QFileDialog.getOpenFileName(self, "Nhập cài đặt", "", "JSON (*.json)")
        if not p:
            return
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f).get("settings", {})
        except (OSError, ValueError, AttributeError) as e:
            QMessageBox.warning(self, "Lỗi", "Không đọc được file: %s" % e)
            return
        n = 0
        for k, v in data.items():
            if k in self.SKIP_EXPORT or not isinstance(k, str):
                continue
            self.win.settings.setValue(k, v)
            n += 1
        QMessageBox.information(self, "Đã nhập", "%d mục. Đóng rồi mở lại Cài đặt (hoặc khởi động lại app) "
                                "để thấy hết thay đổi." % n)
