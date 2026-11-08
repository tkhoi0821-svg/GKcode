# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


def user_plugin_dir():
    d = os.path.join(os.path.expanduser("~"), ".pyapp", "plugins")
    os.makedirs(d, exist_ok=True)
    return d


def user_libs_dir():
    """Thư viện cài riêng cho plugin (pip --target). Dùng được cả khi app là file .exe."""
    d = os.path.join(os.path.expanduser("~"), ".pyapp", "libs")
    os.makedirs(d, exist_ok=True)
    return d


def enable_user_libs():
    d = user_libs_dir()
    if d not in sys.path:
        sys.path.append(d)      # cuối danh sách: không đè lên module đã đóng gói trong exe


def is_plugin_file(path):
    if not path:
        return False
    p = os.path.normcase(os.path.abspath(path))
    return any(p.startswith(os.path.normcase(os.path.abspath(d)) + os.sep)
               for d in app_plugin_dirs())


def user_snippets_path():
    d = os.path.join(os.path.expanduser("~"), ".pyapp")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "snippets.json")


def app_plugin_dirs():
    base = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
            else APP_DIR)
    return [os.path.join(base, "plugins"), user_plugin_dir()]


def run_capture(args, timeout=60, cwd=None):
    """Chạy lệnh, chờ xong, trả về (mã thoát, stdout, stderr)."""
    try:
        r = subprocess.run(args, capture_output=True, timeout=timeout, cwd=cwd,
                           creationflags=NO_WINDOW)
        return r.returncode, decode_output(r.stdout), decode_output(r.stderr)
    except (OSError, subprocess.TimeoutExpired) as e:
        return -1, "", str(e)


class CaptureThread(QThread):
    """Chạy lệnh ở nền để giao diện không bị đơ."""
    done = pyqtSignal(object)   # (mã thoát, stdout, stderr)

    def __init__(self, args, timeout=60, cwd=None, parent=None):
        super().__init__(parent)
        self.args, self.timeout, self.cwd = list(args), timeout, cwd

    def run(self):
        self.done.emit(run_capture(self.args, self.timeout, self.cwd))


def find_up(start, name):
    """Tìm ngược lên các thư mục cha xem có file/thư mục `name` không."""
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, name)):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def clean_name(name):
    """Làm sạch tên dự án: chặn '../', ký tự cấm của hệ điều hành."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", (name or "").strip()).strip(". ")
    return name or "my_project"


def require_http(url):
    if urllib.parse.urlparse(url).scheme.lower() not in ("http", "https"):
        raise ValueError("Chỉ hỗ trợ liên kết http / https")


# Tải xuống
def normalize_download_url(url):
    """Trả về danh sách URL sẽ thử lần lượt (tự đổi link GitHub cho đúng)."""
    url = url.strip()
    m = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/blob/(.+)$", url)
    if m:
        return [f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{m.group(3)}"]
    m = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/tree/([^/?#]+)/?$", url)
    if m:
        u, r, b = m.groups()
        return [f"https://github.com/{u}/{r}/archive/refs/heads/{b}.zip"]
    m = re.match(r"^https?://github\.com/([^/]+)/([^/#?]+?)(?:\.git)?/?$", url)
    if m:
        u, r = m.groups()
        return [f"https://github.com/{u}/{r}/archive/refs/heads/main.zip",
                f"https://github.com/{u}/{r}/archive/refs/heads/master.zip"]
    return [url]


def suggest_filename(url):
    first = normalize_download_url(url)[0]
    m = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/archive/refs/heads/(.+)\.zip$", first)
    if m:
        return f"{m.group(2)}-{m.group(3)}.zip"
    name = os.path.basename(urllib.parse.unquote(urllib.parse.urlparse(first).path))
    return clean_name(name) if name else "download"


def repo_name_from_url(url):
    tail = re.split(r"[/:]", url.strip().rstrip("/"))[-1]
    return re.sub(r"\.git$", "", tail) or "repo"


def safe_extract_zip(zpath, dest):
    """Giải nén zip, chặn zip-slip và zip-bomb. Trả về thư mục gốc."""
    with zipfile.ZipFile(zpath) as z:
        infos = z.infolist()
        if len(infos) > 50000:
            raise ValueError("Zip có quá nhiều file")
        if sum(i.file_size for i in infos) > MAX_UNZIP_BYTES:
            raise ValueError("Dung lượng giải nén quá lớn (> 2 GB)")
        base = os.path.realpath(dest)
        names = z.namelist()
        for n in names:
            target = os.path.realpath(os.path.join(dest, n))
            if not (target == base or target.startswith(base + os.sep)):
                raise ValueError(f"Đường dẫn không an toàn trong zip: {n}")
        z.extractall(dest)
    tops = {n.split("/")[0] for n in names if n.strip("/")}
    return os.path.join(dest, tops.pop()) if len(tops) == 1 else dest


class DownloadThread(QThread):
    progress = pyqtSignal(object, object)   # (đã tải, tổng - 0 nếu không rõ)
    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, urls, dest, parent=None):
        super().__init__(parent)
        self.urls = list(urls)
        self.dest = dest
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        last_err = "Không có URL"
        tmp = self.dest + ".part"
        for url in self.urls:
            try:
                require_http(url)
                req = urllib.request.Request(
                    url, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    total = resp.headers.get("Content-Length")
                    total = int(total) if total and total.isdigit() else 0
                    os.makedirs(os.path.dirname(self.dest) or ".", exist_ok=True)
                    got = 0
                    with open(tmp, "wb") as f:
                        while True:
                            if self._cancel:
                                raise RuntimeError("Đã hủy")
                            chunk = resp.read(65536)
                            if not chunk:
                                break
                            f.write(chunk)
                            got += len(chunk)
                            self.progress.emit(got, total)
                os.replace(tmp, self.dest)
                self.done.emit(self.dest)
                return
            except Exception as e:  # noqa: BLE001
                last_err = f"{url}\n{e}"
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except OSError:
                    pass
                if self._cancel:
                    break
        self.failed.emit(last_err)


class DownloadDialog(QDialog):
    def __init__(self, win, url="", unzip=False):
        super().__init__(win)
        self.win = win
        self.thread_ = None
        self._name_touched = False
        self.setWindowTitle("Tải xuống từ URL")
        self.setMinimumWidth(560)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("URL (file, link GitHub blob/repo/zip...):"))
        self.url_edit = QLineEdit(url)
        lay.addWidget(self.url_edit)

        lay.addWidget(QLabel("Lưu vào thư mục:"))
        row = QHBoxLayout()
        start = win.settings.value("dl/dir", "") or win._project_root()
        self.dir_edit = QLineEdit(start)
        browse = QPushButton("Chọn...")
        browse.clicked.connect(self._browse)
        row.addWidget(self.dir_edit, 1)
        row.addWidget(browse)
        lay.addLayout(row)

        lay.addWidget(QLabel("Tên file:"))
        self.name_edit = QLineEdit(suggest_filename(url) if url else "")
        lay.addWidget(self.name_edit)

        self.unzip_cb = QCheckBox("Giải nén nếu là .zip (rồi mở thư mục trong Explorer của app)")
        self.unzip_cb.setChecked(unzip)
        self.open_cb = QCheckBox("Mở file trong editor sau khi tải (file text)")
        self.open_cb.setChecked(True)
        lay.addWidget(self.unzip_cb)
        lay.addWidget(self.open_cb)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setFormat("Sẵn sàng")
        lay.addWidget(self.bar)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        lay.addWidget(self.status)

        btns = QHBoxLayout()
        self.go_btn = QPushButton("Tải xuống")
        self.cancel_btn = QPushButton("Đóng")
        btns.addStretch(1)
        btns.addWidget(self.go_btn)
        btns.addWidget(self.cancel_btn)
        lay.addLayout(btns)

        self.url_edit.textChanged.connect(self._on_url)
        self.name_edit.textEdited.connect(lambda _t: setattr(self, "_name_touched", True))
        self.go_btn.clicked.connect(self.start)
        self.cancel_btn.clicked.connect(self.close)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục", self.dir_edit.text())
        if d:
            self.dir_edit.setText(d)

    def _on_url(self, text):
        if not self._name_touched:
            self.name_edit.setText(suggest_filename(text) if text.strip() else "")
        low = text.strip().lower()
        if low.split("?")[0].endswith(".zip") or (
                "github.com/" in low and "/blob/" not in low and "raw." not in low):
            self.unzip_cb.setChecked(True)

    def start(self):
        url = self.url_edit.text().strip()
        folder = self.dir_edit.text().strip()
        name = os.path.basename(self.name_edit.text().strip()) or suggest_filename(url)
        if not url or not folder:
            QMessageBox.warning(self, "Thiếu thông tin", "Cần nhập URL và thư mục lưu.")
            return
        try:
            require_http(url)
        except ValueError as e:
            QMessageBox.warning(self, "URL không hợp lệ", str(e))
            return
        dest = os.path.join(folder, name)
        if os.path.exists(dest) and QMessageBox.question(
                self, "File đã tồn tại", f"'{name}' đã có. Ghi đè?") != QMessageBox.Yes:
            return
        self.win.settings.setValue("dl/dir", folder)
        self.go_btn.setEnabled(False)
        self.bar.setFormat("Đang tải... %p%")
        self.bar.setRange(0, 0)
        self.status.setText("")
        t = DownloadThread(normalize_download_url(url), dest, self)
        t.progress.connect(self._on_progress)
        t.done.connect(self._on_done)
        t.failed.connect(self._on_failed)
        self.thread_ = t
        t.start()

    def _on_progress(self, got, total):
        if total:
            self.bar.setRange(0, 100)
            self.bar.setValue(int(got * 100 / total))
        self.status.setText(f"{got / 1048576:.2f} MB" + (f" / {total / 1048576:.2f} MB" if total else ""))

    def _on_done(self, dest):
        self.bar.setRange(0, 100)
        self.bar.setValue(100)
        self.bar.setFormat("Hoàn tất ✔")
        self.go_btn.setEnabled(True)
        msg = f"Đã lưu: {dest}"
        try:
            if dest.lower().endswith(".zip") and self.unzip_cb.isChecked():
                out = safe_extract_zip(dest, os.path.dirname(dest))
                msg += f"\nĐã giải nén vào: {out}"
                self.win._set_explorer_root(out)
            elif self.open_cb.isChecked() and os.path.splitext(dest)[1].lower() in TEXT_EXTS:
                self.win.open_path(dest)
        except (OSError, ValueError, zipfile.BadZipFile) as e:
            msg += f"\nLỗi xử lý sau khi tải: {e}"
        self.status.setText(msg)
        self.win.terminal.appendPlainText(msg)

    def _on_failed(self, err):
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFormat("Thất bại")
        self.go_btn.setEnabled(True)
        self.status.setText(f"Lỗi: {err}")

    def closeEvent(self, e):
        if self.thread_ is not None and self.thread_.isRunning():
            self.thread_.cancel()
            self.thread_.wait(2000)
        super().closeEvent(e)


class CloneDialog(QDialog):
    def __init__(self, parent, default_dir):
        super().__init__(parent)
        self._touched = False
        self.setWindowTitle("Git: Clone từ URL")
        self.setMinimumWidth(520)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("URL repository (https://github.com/user/repo.git):"))
        self.url_edit = QLineEdit()
        lay.addWidget(self.url_edit)
        lay.addWidget(QLabel("Thư mục cha:"))
        row = QHBoxLayout()
        self.dir_edit = QLineEdit(default_dir)
        b = QPushButton("Chọn...")
        b.clicked.connect(self._browse)
        row.addWidget(self.dir_edit, 1)
        row.addWidget(b)
        lay.addLayout(row)
        lay.addWidget(QLabel("Tên thư mục:"))
        self.name_edit = QLineEdit()
        lay.addWidget(self.name_edit)
        lay.addWidget(QLabel("Nhánh (để trống = mặc định):"))
        self.branch_edit = QLineEdit()
        lay.addWidget(self.branch_edit)
        self.shallow_cb = QCheckBox("Clone nông (--depth 1, nhanh và nhẹ hơn)")
        lay.addWidget(self.shallow_cb)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.url_edit.textChanged.connect(self._on_url)
        self.name_edit.textEdited.connect(lambda _t: setattr(self, "_touched", True))

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục cha", self.dir_edit.text())
        if d:
            self.dir_edit.setText(d)

    def _on_url(self, t):
        if not self._touched:
            self.name_edit.setText(repo_name_from_url(t) if t.strip() else "")

    def values(self):
        return {"url": self.url_edit.text().strip(), "dir": self.dir_edit.text().strip(),
                "name": self.name_edit.text().strip(), "branch": self.branch_edit.text().strip(),
                "shallow": self.shallow_cb.isChecked()}


# ESP / Serial
try:
    from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
except ImportError:  # pragma: no cover
    QSerialPort = QSerialPortInfo = None

ESP_VIDS = {0x303A: "Espressif", 0x10C4: "CP210x", 0x1A86: "CH340/CH9102", 0x0403: "FTDI"}
ESP_CHIPS = ["auto", "esp32", "esp32s3", "esp32s2", "esp32c3", "esp32c6", "esp8266"]
ESP_BAUDS = ["115200", "230400", "460800", "921600", "1500000"]
