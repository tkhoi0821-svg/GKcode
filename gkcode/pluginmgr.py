# -*- coding: utf-8 -*-
"""GKcode 4.4: Quản lý plugin — danh sách, bật/tắt từng plugin, cài từ file / zip / URL, gỡ,
và plugin có sẵn (thư mục plugins/ cạnh main.py, kiểm bằng manifest.json)."""
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'langs', 'terminal', 'nettools', 'esp', 'templates', 'polyglot',
           'plugins', 'textools', 'toolsmixin', 'viewers', 'media', 'prefs', 'filetypes']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n

BUNDLED_DIR = app_plugin_dirs()[0]       # thư mục plugins cạnh main.py (hoặc cạnh file .exe khi đã đóng gói)
MAX_PLUGIN_DOWNLOAD = 5 * 1024 * 1024


def plugin_meta(path):
    """Đọc PLUGIN = {...} (name, version, author, description) bằng ast — không chạy code plugin."""
    meta = {"name": os.path.splitext(os.path.basename(path))[0], "version": "", "author": "", "description": ""}
    try:
        with open(path, "rb") as f:
            tree = ast.parse(f.read().decode("utf-8-sig", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        meta["description"] = "(không đọc được file)"
        return meta
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PLUGIN" for t in n.targets):
            try:
                d = ast.literal_eval(n.value)
                if isinstance(d, dict):
                    for k in meta:
                        if k in d:
                            meta[k] = str(d[k])
            except (ValueError, SyntaxError):
                pass
            return meta
    doc = ast.get_docstring(tree)
    if doc:
        meta["description"] = doc.strip().split("\n")[0]
    return meta


def bundled_manifest():
    try:
        with open(os.path.join(BUNDLED_DIR, "manifest.json"), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def is_bundled_verified(path, digest):
    """Plugin đi kèm app: khớp sha256 trong manifest.json thì khỏi hỏi 'cho phép plugin?'."""
    if os.path.normcase(os.path.dirname(os.path.abspath(path))) != os.path.normcase(os.path.abspath(BUNDLED_DIR)):
        return False
    return bundled_manifest().get(os.path.basename(path)) == digest


def scan_plugins():
    """[{name, path, source('bundled'|'user'), meta}] — trùng tên: thư mục đứng trước thắng (như load_plugins)."""
    out, seen = [], set()
    for d in app_plugin_dirs():
        if not os.path.isdir(d):
            continue
        bundled = os.path.normcase(os.path.abspath(d)) == os.path.normcase(os.path.abspath(BUNDLED_DIR))
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".py") or fn.startswith("_"):
                continue
            name = fn[:-3]
            if name in seen:
                continue
            seen.add(name)
            p = os.path.join(d, fn)
            out.append({"name": name, "path": p, "source": "bundled" if bundled else "user", "meta": plugin_meta(p)})
    return out


def fetch_plugin_sources(url, workdir):
    """Tải .py hoặc .zip từ URL -> danh sách đường dẫn .py (chưa tin cậy) trong workdir."""
    require_http(url)
    last = None
    for u in normalize_download_url(url):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "GKcode"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read(MAX_PLUGIN_DOWNLOAD + 1)
            if len(data) > MAX_PLUGIN_DOWNLOAD:
                raise ValueError("File quá lớn (> 5 MB)")
            break
        except Exception as e:  # noqa: BLE001
            last, data = e, None
    if data is None:
        raise ValueError("Không tải được: %s" % last)
    if data[:2] == b"PK":
        zp = os.path.join(workdir, "dl.zip")
        with open(zp, "wb") as f:
            f.write(data)
        return extract_plugin_py(zp, workdir)
    name = suggest_filename(url) or "plugin.py"
    if not name.endswith(".py"):
        name += ".py"
    p = os.path.join(workdir, re.sub(r"[^\w.\-]", "_", name))
    with open(p, "wb") as f:
        f.write(data)
    return [p]


def extract_plugin_py(zip_path, workdir):
    """Lấy các file .py ở thư mục gốc (hoặc trong đúng 1 thư mục con, hoặc 'plugins/') của zip. Không giải nén gì khác."""
    out = []
    with zipfile.ZipFile(zip_path) as z:
        for i in z.infolist():
            n = i.filename.replace("\\", "/")
            parts = [x for x in n.split("/") if x]
            if i.is_dir() or not parts or parts[-1].startswith("_") or not parts[-1].endswith(".py"):
                continue
            if ".." in parts or len(parts) > 3 or i.file_size > MAX_PLUGIN_DOWNLOAD:
                continue
            if len(parts) >= 2 and parts[-2] not in ("plugins",) and len(parts) != 2:
                continue
            dest = os.path.join(workdir, re.sub(r"[^\w.\-]", "_", parts[-1]))
            with z.open(i) as src, open(dest, "wb") as dst:
                dst.write(src.read(MAX_PLUGIN_DOWNLOAD))
            out.append(dest)
    if not out:
        raise ValueError("Không thấy file .py plugin nào trong zip")
    return out


class PluginManagerDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Quản lý plugin")
        self.resize(940, 520)
        lay = QVBoxLayout(self)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Bật", "Tên", "Phiên bản", "Tác giả", "Mô tả", "Nguồn / trạng thái"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        lay.addWidget(self.table, 1)
        self.info = QLabel("")
        self.info.setWordWrap(True)
        lay.addWidget(self.info)
        row = QHBoxLayout()
        for text, fn in (("Thêm từ file / zip...", self.add_file), ("Cài từ URL...", self.add_url),
                         ("Mở file", self.open_file), ("Mở thư mục", self.open_dir), ("Gỡ plugin", self.remove)):
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch(1)
        self.apply_btn = QPushButton("Áp dụng (tải lại plugin)")
        self.apply_btn.clicked.connect(self.apply)
        close = QPushButton("Đóng")
        close.clicked.connect(self.accept)
        row.addWidget(self.apply_btn)
        row.addWidget(close)
        lay.addLayout(row)
        self.table.itemChanged.connect(self._toggled)
        self.refresh()

    def _disabled(self):
        return self.win._plugin_disabled()

    def refresh(self):
        self.table.blockSignals(True)
        entries = scan_plugins()
        self.entries = entries
        dis = self._disabled()
        running = {n for n, _a, _m in getattr(self.win, "plugin_apis", [])}
        self.table.setRowCount(len(entries))
        for r, e in enumerate(entries):
            m = e["meta"]
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked if e["name"] in dis else Qt.Checked)
            self.table.setItem(r, 0, chk)
            self.table.setItem(r, 1, QTableWidgetItem(m["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(m["version"]))
            self.table.setItem(r, 3, QTableWidgetItem(m["author"]))
            self.table.setItem(r, 4, QTableWidgetItem(m["description"]))
            state = "Tắt" if e["name"] in dis else ("Đang chạy" if e["name"] in running else "Chưa nạp")
            src = "Có sẵn" if e["source"] == "bundled" else "Của bạn"
            self.table.setItem(r, 5, QTableWidgetItem("%s · %s" % (src, state)))
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.blockSignals(False)
        self.info.setText("%d plugin. Tích/bỏ tích ô 'Bật' rồi bấm 'Áp dụng'. Plugin chạy code Python với toàn quyền "
                          "của bạn — chỉ cài từ nguồn tin cậy." % len(entries))

    def _toggled(self, item):
        if item.column() != 0:
            return
        name = self.entries[item.row()]["name"]
        dis = self._disabled()
        if item.checkState() == Qt.Checked:
            dis.discard(name)
        else:
            dis.add(name)
        self.win._set_plugin_disabled(dis)

    def _current(self):
        r = self.table.currentRow()
        return self.entries[r] if 0 <= r < len(self.entries) else None

    def apply(self):
        self.win.load_plugins()
        self.refresh()

    def add_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn plugin (.py hoặc .zip)", "",
                                                "Plugin (*.py *.zip);;Tất cả (*)")
        srcs, tmp = [], None
        for f in files:
            if f.lower().endswith(".zip"):
                tmp = tmp or tempfile.mkdtemp(prefix="gk_plg_")
                try:
                    srcs += extract_plugin_py(f, tmp)
                except Exception as e:  # noqa: BLE001
                    QMessageBox.warning(self, "Zip lỗi", "%s: %s" % (os.path.basename(f), e))
            else:
                srcs.append(f)
        self._install(srcs)

    def add_url(self):
        url, ok = QInputDialog.getText(self, "Cài plugin từ URL",
                                       "Link file .py / .zip (hoặc link GitHub .../blob/... , repo):")
        if not ok or not url.strip():
            return
        tmp = tempfile.mkdtemp(prefix="gk_plg_")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            srcs = fetch_plugin_sources(url.strip(), tmp)
        except Exception as e:  # noqa: BLE001
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "Không cài được", str(e))
            return
        QApplication.restoreOverrideCursor()
        self._install(srcs)

    def _install(self, srcs):
        if srcs:
            self.win.import_plugin_sources(srcs)
        self.refresh()

    def open_file(self):
        e = self._current()
        if e:
            self.win.open_path(e["path"])

    def open_dir(self):
        e = self._current()
        d = os.path.dirname(e["path"]) if e else user_plugin_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))

    def remove(self):
        e = self._current()
        if not e:
            return
        if e["source"] == "bundled":
            QMessageBox.information(self, "Plugin có sẵn", "Plugin đi kèm app thì tắt bằng ô 'Bật', không gỡ.")
            return
        if QMessageBox.question(self, "Gỡ plugin", "Xóa file plugin '%s'?\n%s" % (e["name"], e["path"])) != QMessageBox.Yes:
            return
        try:
            os.remove(e["path"])
        except OSError as ex:
            QMessageBox.warning(self, "Lỗi", str(ex))
            return
        self.win.load_plugins()
        self.refresh()
