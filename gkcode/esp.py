# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


def list_serial_ports():
    """[(tên cổng, nhãn hiển thị, nghi là ESP/USB-serial?)]"""
    if QSerialPortInfo is None:
        return []
    out = []
    for p in QSerialPortInfo.availablePorts():
        vid = p.vendorIdentifier() if p.hasVendorIdentifier() else 0
        tag = ESP_VIDS.get(vid, "")
        label = f"{p.portName()} - {p.description() or 'Serial'}" + (f"  ★ {tag}" if tag else "")
        out.append((p.portName(), label, bool(tag)))
    out.sort(key=lambda x: (not x[2], x[0]))
    return out


def tool_port(port):
    """COM3 giữ nguyên; trên Linux/macOS 'ttyUSB0' -> '/dev/ttyUSB0'."""
    if port and os.name != "nt" and not port.startswith("/"):
        return "/dev/" + port
    return port


def build_esptool_args(py_cmd, chip, port, baud, action):
    port = tool_port(port)
    args = list(py_cmd[1:]) + ["-m", "esptool"]
    if chip and chip != "auto":
        args += ["--chip", chip]
    if port:
        args += ["--port", port]
    if baud:
        args += ["--baud", str(baud)]
    return args + list(action)


def default_flash_rows(preset, chip):
    # ESP32 cổ điển nạp bootloader ở 0x1000; S3/C3/C6/S2 ở 0x0
    boot = "0x1000" if chip in ("esp32", "auto", "esp8266") else "0x0"
    if preset == 0:
        return [["0x0", ""]]
    if preset == 1:
        return [["0x10000", ""]]
    return [[boot, ""], ["0x8000", ""], ["0xe000", ""], ["0x10000", ""]]


class EspFlashDialog(QDialog):
    PRESETS = ["1 file gộp (merged .bin) @ 0x0",
               "Chỉ app @ 0x10000",
               "Arduino đầy đủ (bootloader / partitions / boot_app0 / app)"]

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        s = win.settings
        self.setWindowTitle("Nạp firmware ESP (esptool)")
        self.resize(660, 470)
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        self.chip = QComboBox()
        self.chip.addItems(ESP_CHIPS)
        self.chip.setCurrentText(s.value("esp/chip", "esp32s3"))
        self.port = QComboBox()
        self.port.setMinimumWidth(240)
        refresh = QPushButton("⟳")
        refresh.setFixedWidth(30)
        refresh.setToolTip("Quét lại cổng COM")
        self.baud = QComboBox()
        self.baud.addItems(ESP_BAUDS)
        self.baud.setCurrentText(str(s.value("esp/baud", "460800")))
        for lbl, w in (("Chip:", self.chip), ("Cổng:", self.port)):
            top.addWidget(QLabel(lbl))
            top.addWidget(w)
        top.addWidget(refresh)
        top.addWidget(QLabel("Baud:"))
        top.addWidget(self.baud)
        lay.addLayout(top)

        prow = QHBoxLayout()
        prow.addWidget(QLabel("Mẫu bố cục:"))
        self.preset = QComboBox()
        self.preset.addItems(self.PRESETS)
        prow.addWidget(self.preset, 1)
        lay.addLayout(prow)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Địa chỉ flash", "File .bin"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        lay.addWidget(self.table, 1)

        trow = QHBoxLayout()
        add_b, del_b, browse_b = QPushButton("+ Dòng"), QPushButton("− Xóa dòng"), QPushButton("Chọn file...")
        for b in (add_b, del_b, browse_b):
            trow.addWidget(b)
        trow.addStretch(1)
        lay.addLayout(trow)

        arow = QHBoxLayout()
        self.flash_b = QPushButton("⚡ Nạp (write_flash)")
        erase_b = QPushButton("Xóa flash")
        info_b = QPushButton("Thông tin chip")
        mac_b = QPushButton("Đọc MAC")
        bak_b = QPushButton("Sao lưu flash")
        for b in (self.flash_b, erase_b, info_b, mac_b, bak_b):
            arow.addWidget(b)
        lay.addLayout(arow)
        lay.addWidget(QLabel("Giữ nút BOOT khi cắm nếu board không tự vào chế độ nạp. "
                             "Kết quả hiện ở Terminal của app."))

        try:
            rows = json.loads(s.value("esp/rows", "") or "[]")
        except (ValueError, TypeError):
            rows = []
        for r in rows or default_flash_rows(0, self.chip.currentText()):
            self._add_row(r[0], r[1])
        self.refresh_ports(s.value("esp/port", ""))

        refresh.clicked.connect(lambda: self.refresh_ports())
        self.preset.activated.connect(self._apply_preset)
        add_b.clicked.connect(lambda: self._add_row("0x0", ""))
        del_b.clicked.connect(self._del_row)
        browse_b.clicked.connect(self._browse)
        self.flash_b.clicked.connect(self.do_flash)
        erase_b.clicked.connect(self.do_erase)
        info_b.clicked.connect(self.do_info)
        mac_b.clicked.connect(lambda: self._run([("Đọc MAC", ["read_mac"])]))
        bak_b.clicked.connect(self.do_backup)

    #  bảng
    def _add_row(self, addr, path):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(addr))
        self.table.setItem(r, 1, QTableWidgetItem(path))

    def _del_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)

    def _browse(self):
        r = self.table.currentRow()
        if r < 0:
            if self.table.rowCount() == 0:
                self._add_row("0x0", "")
            r = 0
        f, _ = QFileDialog.getOpenFileName(self, "Chọn firmware", "", "Firmware (*.bin);;Tất cả (*)")
        if f:
            self.table.setItem(r, 1, QTableWidgetItem(f))

    def _apply_preset(self, idx):
        self.table.setRowCount(0)
        for a, f in default_flash_rows(idx, self.chip.currentText()):
            self._add_row(a, f)

    def refresh_ports(self, keep=""):
        cur = keep or self.port.currentData()
        self.port.clear()
        ports = list_serial_ports()
        for name, label, _esp in ports:
            self.port.addItem(label, name)
        if not ports:
            self.port.addItem("(không thấy cổng nào)", "")
        if cur:
            i = self.port.findData(cur)
            if i >= 0:
                self.port.setCurrentIndex(i)

    #  hành động
    def _rows(self):
        out = []
        for r in range(self.table.rowCount()):
            a = (self.table.item(r, 0).text() if self.table.item(r, 0) else "").strip()
            f = (self.table.item(r, 1).text() if self.table.item(r, 1) else "").strip()
            if a or f:
                out.append([a, f])
        return out

    def _save(self):
        s = self.win.settings
        s.setValue("esp/chip", self.chip.currentText())
        s.setValue("esp/baud", self.baud.currentText())
        s.setValue("esp/port", self.port.currentData() or "")
        s.setValue("esp/rows", json.dumps(self._rows()))

    def _run(self, actions):
        port = self.port.currentData() or ""
        if not port and QMessageBox.question(
                self, "Chưa chọn cổng",
                "Chưa có cổng COM. Để esptool tự dò cổng?") != QMessageBox.Yes:
            return
        self._save()
        self.win.esptool_run(actions, self.chip.currentText(), port, self.baud.currentText())

    def do_flash(self):
        pairs = []
        for a, f in self._rows():
            if not re.fullmatch(r"0x[0-9a-fA-F]+|\d+", a):
                QMessageBox.warning(self, "Địa chỉ sai", f"Địa chỉ '{a}' không hợp lệ (vd 0x10000).")
                return
            if not os.path.isfile(f):
                QMessageBox.warning(self, "Thiếu file", f"Không tìm thấy file:\n{f}")
                return
            pairs += [a, f]
        if not pairs:
            QMessageBox.information(self, "Chưa có file", "Hãy chọn ít nhất một file .bin.")
            return
        self._run([("Nạp firmware", ["write_flash"] + pairs)])

    def do_erase(self):
        if QMessageBox.question(self, "Xóa flash", "Xóa TOÀN BỘ flash của chip?\n"
                                "Mọi dữ liệu và firmware sẽ mất.") == QMessageBox.Yes:
            self._run([("Xóa flash", ["erase_flash"])])

    def do_info(self):
        self._run([("Thông tin chip", ["chip_id"]), ("Flash ID", ["flash_id"])])

    def do_backup(self):
        out, _ = QFileDialog.getSaveFileName(self, "Lưu bản sao lưu flash", "flash_backup.bin",
                                             "Binary (*.bin)")
        if out:
            self._run([("Sao lưu flash", ["read_flash", "0", "ALL", out])])


ESP_BOARDS = [      # (nhãn, FQBN arduino-cli, board PlatformIO, chip)
    ("ESP32 Dev Module", "esp32:esp32:esp32", "esp32dev", "esp32"),
    ("ESP32-S3 Dev Module", "esp32:esp32:esp32s3", "esp32-s3-devkitc-1", "esp32s3"),
    ("LilyGO T-Display S3", "esp32:esp32:lilygo_t_display_s3", "lilygo-t-display-s3", "esp32s3"),
    ("ESP32-C3 Dev Module", "esp32:esp32:esp32c3", "esp32-c3-devkitm-1", "esp32c3"),
    ("ESP32-C6 Dev Module", "esp32:esp32:esp32c6", "esp32-c6-devkitc-1", "esp32c6"),
    ("ESP32-S2 Dev Module", "esp32:esp32:esp32s2", "esp32-s2-saola-1", "esp32s2"),
    ("ESP8266 NodeMCU", "esp8266:esp8266:nodemcuv2", "nodemcuv2", "esp8266"),
]
ESP_CORE_URLS = {
    "esp32": "https://espressif.github.io/arduino-esp32/package_esp32_index.json",
    "esp8266": "https://arduino.esp8266.com/stable/package_esp8266com_index.json",
}

# arduino-cli: tiện ích gọi lệnh + đọc JSON (viết phòng thủ vì định dạng JSON đổi theo phiên bản)
ARDUINO_HOME = os.path.join(os.path.expanduser("~"), ".gkcode", "arduino-cli")
_LIVE_THREADS = set()     # giữ tham chiếu tới thread nền đang chạy (tránh bị hủy giữa chừng)


def managed_arduino_cli():
    p = os.path.join(ARDUINO_HOME, "arduino-cli" + EXE_EXT)
    return p if os.path.isfile(p) else ""


def _g(d, *names, default=None):
    """Lấy khóa đầu tiên có mặt (không phân biệt hoa/thường) trong dict."""
    if not isinstance(d, dict):
        return default
    low = {str(k).lower(): v for k, v in d.items()}
    for n in names:
        v = low.get(n.lower())
        if v is not None:
            return v
    return default


def _vkey(v):
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.\-+]", str(v)))


def acli_json(cli, args, timeout=180):
    """-> (mã thoát, dữ liệu JSON hoặc None, văn bản lỗi)"""
    code, out, err = run_capture([cli] + list(args) + ["--format", "json"], timeout)
    data = None
    try:
        data = json.loads(out) if out.strip() else None
    except ValueError:
        data = None
    return code, data, (err.strip() or ("" if data is not None else out.strip()))


def bg_run(parent, fn, cb):
    """Chạy fn() ở nền, gọi cb(kết quả) ở luồng giao diện."""
    th = FuncThread(fn, parent=None)
    _LIVE_THREADS.add(th)

    def fin(res, th=th):
        try:
            cb(res)
        finally:
            _LIVE_THREADS.discard(th)
    th.done.connect(fin)
    th.start()
    return th


def parse_platforms(data):
    items = _g(data, "platforms", default=[]) if isinstance(data, dict) else (data or [])
    out = []
    for p in items or []:
        pid = _g(p, "id")
        if not pid:
            continue
        rel = _g(p, "releases", default={})
        versions = sorted(rel.keys(), key=_vkey, reverse=True) if isinstance(rel, dict) else []
        latest = _g(p, "latest_version", "latest") or (versions[0] if versions else "")
        installed = _g(p, "installed_version", "installed") or ""
        name = ""
        if isinstance(rel, dict) and rel:
            r = rel.get(str(latest)) or rel.get(str(installed)) or rel[versions[0]]
            name = _g(r, "name") or ""
        out.append({"id": str(pid), "name": str(name or _g(p, "name") or pid),
                    "installed": installed if isinstance(installed, str) else "",
                    "latest": latest if isinstance(latest, str) else str(latest),
                    "maintainer": str(_g(p, "maintainer") or ""), "versions": versions})
    out.sort(key=lambda x: (not x["installed"], x["name"].lower()))
    return out


def parse_boards(data):
    items = _g(data, "boards", default=[]) if isinstance(data, dict) else (data or [])
    out = []
    for b in items or []:
        fq, name = _g(b, "fqbn"), _g(b, "name")
        if fq and name:
            out.append((str(name), str(fq)))
    out.sort(key=lambda x: x[0].lower())
    return out


def parse_lib_search(data):
    items = _g(data, "libraries", default=[]) if isinstance(data, dict) else (data or [])
    out = []
    for l in items or []:
        name = _g(l, "name")
        if not name:
            continue
        latest = _g(l, "latest", default={})
        rel = _g(l, "releases", default={})
        versions = sorted(rel.keys(), key=_vkey, reverse=True) if isinstance(rel, dict) else []
        ver = _g(latest, "version") or (versions[0] if versions else "")
        if ver and ver not in versions:
            versions.insert(0, ver)
        out.append({"name": str(name), "latest": str(ver or ""),
                    "author": str(_g(latest, "author") or ""),
                    "sentence": str(_g(latest, "sentence") or ""), "versions": versions,
                    "installed": ""})
    return out


def parse_lib_list(data):
    items = _g(data, "installed_libraries", default=[]) if isinstance(data, dict) else (data or [])
    out = []
    for it in items or []:
        lib = _g(it, "library", default=it)
        name = _g(lib, "name")
        if not name:
            continue
        ex = _g(lib, "examples", default=[]) or []
        out.append({"name": str(name), "installed": str(_g(lib, "version") or ""),
                    "dir": str(_g(lib, "install_dir", "installdir") or ""),
                    "examples": [str(x) for x in ex if isinstance(x, str)],
                    "author": str(_g(lib, "author") or ""),
                    "sentence": str(_g(lib, "sentence") or ""),
                    "location": str(_g(lib, "location") or ""),
                    "latest": str(_g(_g(it, "release", default={}), "version") or "")})
    return out


def parse_ports(data):
    items = _g(data, "detected_ports", default=[]) if isinstance(data, dict) else (data or [])
    out = []
    for it in items or []:
        port = _g(it, "port", default={})
        addr = _g(port, "address")
        if not addr:
            continue
        boards = [(str(_g(b, "name") or ""), str(_g(b, "fqbn") or ""))
                  for b in (_g(it, "matching_boards", default=[]) or [])]
        out.append({"address": str(addr), "label": str(_g(port, "label") or addr),
                    "protocol": str(_g(port, "protocol") or ""), "boards": boards})
    return out


def parse_options(data):
    out = []
    for o in _g(data, "config_options", default=[]) or []:
        key = _g(o, "option")
        vals = []
        for v in _g(o, "values", default=[]) or []:
            vals.append((str(_g(v, "value") or ""), str(_g(v, "value_label") or _g(v, "value") or ""),
                         bool(_g(v, "selected", default=False))))
        if key and vals:
            out.append((str(key), str(_g(o, "option_label") or key), vals))
    return out


def acli_urls(cli):
    _c, data, _e = acli_json(cli, ["config", "dump"], 30)
    return list(_g(_g(data, "board_manager", default={}), "additional_urls", default=[]) or [])


def acli_set_urls(cli, urls):
    if urls:
        code, out, err = run_capture([cli, "config", "set", "board_manager.additional_urls"] + list(urls), 30)
        if code != 0:
            run_capture([cli, "config", "init"], 30)
            code, out, err = run_capture([cli, "config", "set", "board_manager.additional_urls"] + list(urls), 30)
        return code == 0, err or out
    code, out, err = run_capture([cli, "config", "delete", "board_manager.additional_urls"], 30)
    return code == 0, err or out


def acli_ensure_urls(cli, names=("esp32", "esp8266")):
    """Thêm URL gói board ESP32/ESP8266 vào cấu hình arduino-cli nếu thiếu."""
    cur = acli_urls(cli)
    new = [ESP_CORE_URLS[n] for n in names if ESP_CORE_URLS[n] not in cur]
    if not new:
        return True
    ok, _m = acli_set_urls(cli, cur + new)
    return ok


def default_sketchbook():
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.join(docs if os.name == "nt" and os.path.isdir(docs) else os.path.expanduser("~"), "Arduino")


def acli_sketchbook(cli):
    if cli:
        _c, data, _e = acli_json(cli, ["config", "dump"], 30)
        d = _g(_g(data, "directories", default={}), "user")
        if d:
            return str(d)
    return default_sketchbook()


def safe_extract_tar(path, dest):
    import tarfile
    base = os.path.realpath(dest)
    with tarfile.open(path) as t:
        members = t.getmembers()
        if len(members) > 50000 or sum(m.size for m in members) > MAX_UNZIP_BYTES:
            raise ValueError("Gói quá lớn")
        for m in members:
            target = os.path.realpath(os.path.join(dest, m.name))
            if not (target == base or target.startswith(base + os.sep)):
                raise ValueError(f"Đường dẫn không an toàn: {m.name}")
            if not (m.isfile() or m.isdir()):
                raise ValueError(f"Loại mục không hỗ trợ: {m.name}")
        t.extractall(dest)


def arduino_cli_urls():
    env = os.environ.get("GKCODE_ARDUINO_CLI_URL")
    if env:
        return [env]
    import platform
    arm = platform.machine().lower() in ("arm64", "aarch64")
    if os.name == "nt":
        osn, ext = "Windows", "zip"
    elif sys.platform == "darwin":
        osn, ext = "macOS", "tar.gz"
    else:
        osn, ext = "Linux", "tar.gz"
    arch = "ARM64" if arm else "64bit"
    return [f"https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_{osn}_{arch}.{ext}"]


def install_arduino_cli_from(archive, names):
    """Giải nén arduino-cli vào ARDUINO_HOME, kiểm tra chạy được, cấu hình URL board ESP.
    -> (0, đường dẫn cli, "") hoặc (-1, "", lỗi)   [chạy ở luồng nền]"""
    tmp = tempfile.mkdtemp(prefix="gkcli_")
    try:
        if archive.lower().endswith(".zip"):
            safe_extract_zip(archive, tmp)
        else:
            safe_extract_tar(archive, tmp)
        found = ""
        for r, _d, files in os.walk(tmp):
            if "arduino-cli" + EXE_EXT in files:
                found = os.path.join(r, "arduino-cli" + EXE_EXT)
                break
        if not found:
            return -1, "", "Không thấy arduino-cli trong gói tải về"
        os.makedirs(ARDUINO_HOME, exist_ok=True)
        dst = os.path.join(ARDUINO_HOME, "arduino-cli" + EXE_EXT)
        shutil.copy2(found, dst)
        os.chmod(dst, 0o755)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    code, out, err = run_capture([dst, "version"], 30)
    if code != 0:
        return -1, "", f"arduino-cli không chạy được: {err or out}"
    acli_ensure_urls(dst, names)
    return 0, dst, out.strip()


SKETCH_TEMPLATES = {
    "Trống (setup/loop)": "void setup() {\n  Serial.begin(115200);\n}\n\nvoid loop() {\n\n}\n",
    "Blink - nháy LED": (
        "#ifndef LED_BUILTIN\n#define LED_BUILTIN 2\n#endif\n\n"
        "void setup() {\n  pinMode(LED_BUILTIN, OUTPUT);\n}\n\n"
        "void loop() {\n  digitalWrite(LED_BUILTIN, HIGH);\n  delay(500);\n"
        "  digitalWrite(LED_BUILTIN, LOW);\n  delay(500);\n}\n"),
    "Hello Serial": (
        "int counter = 0;\n\nvoid setup() {\n  Serial.begin(115200);\n  delay(500);\n"
        "  Serial.println(\"Xin chao tu GKcode!\");\n}\n\n"
        "void loop() {\n  Serial.print(\"dem: \");\n  Serial.println(counter++);\n  delay(1000);\n}\n"),
    "Đọc nút bấm": (
        "const int BUTTON_PIN = 0;   // nút BOOT trên hầu hết board ESP\n"
        "#ifndef LED_BUILTIN\n#define LED_BUILTIN 2\n#endif\n\n"
        "void setup() {\n  pinMode(BUTTON_PIN, INPUT_PULLUP);\n  pinMode(LED_BUILTIN, OUTPUT);\n"
        "  Serial.begin(115200);\n}\n\n"
        "void loop() {\n  bool pressed = digitalRead(BUTTON_PIN) == LOW;\n"
        "  digitalWrite(LED_BUILTIN, pressed ? HIGH : LOW);\n"
        "  Serial.println(pressed ? \"nhan\" : \"nha\");\n  delay(100);\n}\n"),
    "Đồ thị Serial Plotter (sin/cos)": (
        "void setup() {\n  Serial.begin(115200);\n}\n\n"
        "void loop() {\n  float t = millis() / 1000.0;\n"
        "  Serial.print(\"sin:\");\n  Serial.print(sin(t));\n"
        "  Serial.print(\",cos:\");\n  Serial.println(cos(t));\n  delay(30);\n}\n"),
    "WiFi - quét mạng": (
        "#if defined(ESP8266)\n#include <ESP8266WiFi.h>\n#else\n#include <WiFi.h>\n#endif\n\n"
        "void setup() {\n  Serial.begin(115200);\n  WiFi.mode(WIFI_STA);\n  WiFi.disconnect();\n  delay(100);\n}\n\n"
        "void loop() {\n  Serial.println(\"Dang quet...\");\n  int n = WiFi.scanNetworks();\n"
        "  for (int i = 0; i < n; i++) {\n    Serial.printf(\"%2d. %s (%d dBm)\\n\", i + 1, WiFi.SSID(i).c_str(), WiFi.RSSI(i));\n  }\n"
        "  Serial.println();\n  delay(5000);\n}\n"),
    "WiFi - Web server bật/tắt LED": (
        "#if defined(ESP8266)\n#include <ESP8266WiFi.h>\n#include <ESP8266WebServer.h>\nESP8266WebServer server(80);\n"
        "#else\n#include <WiFi.h>\n#include <WebServer.h>\nWebServer server(80);\n#endif\n\n"
        "#ifndef LED_BUILTIN\n#define LED_BUILTIN 2\n#endif\n\n"
        "const char* SSID = \"TEN_WIFI\";\nconst char* PASS = \"MAT_KHAU\";\n\n"
        "void handleRoot() {\n  server.send(200, \"text/html\",\n"
        "    \"<h1>GKcode ESP</h1><a href='/on'>BAT</a> | <a href='/off'>TAT</a>\");\n}\n\n"
        "void setup() {\n  Serial.begin(115200);\n  pinMode(LED_BUILTIN, OUTPUT);\n  WiFi.begin(SSID, PASS);\n"
        "  while (WiFi.status() != WL_CONNECTED) { delay(300); Serial.print('.'); }\n"
        "  Serial.println();\n  Serial.println(WiFi.localIP());\n"
        "  server.on(\"/\", handleRoot);\n"
        "  server.on(\"/on\", []() { digitalWrite(LED_BUILTIN, HIGH); handleRoot(); });\n"
        "  server.on(\"/off\", []() { digitalWrite(LED_BUILTIN, LOW); handleRoot(); });\n"
        "  server.begin();\n}\n\nvoid loop() {\n  server.handleClient();\n}\n"),
}

SIZE_PATTERNS = [
    (re.compile(r"Sketch uses (\d+) bytes \((\d+)%\) of program storage space\. Maximum is (\d+) bytes"),
     "flash"),
    (re.compile(r"Global variables use (\d+) bytes \((\d+)%\) of dynamic memory.*?Maximum is (\d+) bytes"),
     "ram"),
]
PIO_SIZE_RE = re.compile(r"^(RAM|Flash):\s*\[[=\s]*\]\s*[\d.]+%\s*\(used (\d+) bytes from (\d+) bytes\)", re.M)
PROBLEM_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):(?:(?P<col>\d+):)?\s*(?P<sev>fatal error|error|warning|note):\s*(?P<msg>.*)$",
    re.M)


def parse_sizes(text):
    res = {}
    for rx, key in SIZE_PATTERNS:
        m = rx.search(text)
        if m:
            res[key] = (int(m.group(1)), int(m.group(3)))
    for m in PIO_SIZE_RE.finditer(text):
        res["flash" if m.group(1) == "Flash" else "ram"] = (int(m.group(2)), int(m.group(3)))
    return res


def parse_problems(text):
    seen, out = set(), []
    for m in PROBLEM_RE.finditer(text):
        sev = "error" if m.group("sev") in ("error", "fatal error") else m.group("sev")
        key = (m.group("file"), m.group("line"), m.group("col"), sev, m.group("msg"))
        if key in seen:
            continue
        seen.add(key)
        out.append({"file": m.group("file"), "line": int(m.group("line")),
                    "col": int(m.group("col") or 1), "sev": sev, "msg": m.group("msg").strip()})
    return out


def plot_values(line):
    """'a:1,b:2' | '1 2 3' | 'x=3.5' -> [(tên, giá trị)]"""
    res = []
    for i, m in enumerate(PLOT_RE.finditer(line)):
        name = (m.group(1) or "").strip() or f"v{i + 1}"
        try:
            res.append((name, float(m.group(2))))
        except ValueError:
            pass
    return res


PLOT_RE = re.compile(r"(?:([A-Za-z_][\w .\-]*?)\s*[:=]\s*)?(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)(?![\w.])")


def copy_sketch(src_dir, sketchbook):
    """Chép thư mục sketch/ví dụ vào sketchbook (đảm bảo tên .ino = tên thư mục). -> đường dẫn .ino"""
    name = os.path.basename(os.path.normpath(src_dir))
    os.makedirs(sketchbook, exist_ok=True)
    dst, n = os.path.join(sketchbook, name), 2
    while os.path.exists(dst):
        dst = os.path.join(sketchbook, f"{name}_{n}")
        n += 1
    shutil.copytree(src_dir, dst, ignore=shutil.ignore_patterns(".*", "build", "__pycache__"))
    inos = sorted(f for f in os.listdir(dst) if f.lower().endswith(".ino"))
    want = os.path.basename(dst) + ".ino"
    if inos and want not in inos:
        os.replace(os.path.join(dst, inos[0]), os.path.join(dst, want))
        inos = [want]
    return os.path.join(dst, inos[0] if inos else want)


def _mk_table(headers, widths=None):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setSelectionMode(QTableWidget.SingleSelection)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setStretchLastSection(True)
    for i, w in enumerate(widths or []):
        t.setColumnWidth(i, w)
    return t


class BoardsManagerDialog(QDialog):
    """Boards Manager: tìm / cài / gỡ / cập nhật core board (esp32, esp8266, arduino...)."""

    def __init__(self, panel):
        super().__init__(panel.win)
        self.panel = panel
        self.platforms = []
        self.setWindowTitle("Boards Manager")
        self.resize(820, 520)
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Lọc theo tên / ID / nhà phát triển (vd: esp32)")
        self.only_inst = QCheckBox("Chỉ đã cài")
        upd = QPushButton("Cập nhật index")
        urls = QPushButton("URL board bổ sung...")
        top.addWidget(self.search, 1)
        top.addWidget(self.only_inst)
        top.addWidget(upd)
        top.addWidget(urls)
        lay.addLayout(top)
        self.table = _mk_table(["Tên", "ID", "Đã cài", "Mới nhất", "Nhà phát triển"],
                               [300, 150, 80, 80])
        lay.addWidget(self.table, 1)
        self.info = QLabel("Đang tải danh sách...")
        self.info.setWordWrap(True)
        lay.addWidget(self.info)
        row = QHBoxLayout()
        self.ver = QComboBox()
        self.ver.setMinimumWidth(120)
        self.install_btn = QPushButton("Cài đặt")
        self.remove_btn = QPushButton("Gỡ")
        row.addWidget(QLabel("Phiên bản:"))
        row.addWidget(self.ver)
        row.addWidget(self.install_btn)
        row.addWidget(self.remove_btn)
        row.addStretch(1)
        close = QPushButton("Đóng")
        row.addWidget(close)
        lay.addLayout(row)
        self.search.textChanged.connect(self.refill)
        self.only_inst.toggled.connect(self.refill)
        self.table.itemSelectionChanged.connect(self._sel)
        self.install_btn.clicked.connect(self.do_install)
        self.remove_btn.clicked.connect(self.do_remove)
        upd.clicked.connect(self.update_index)
        urls.clicked.connect(self.edit_urls)
        close.clicked.connect(self.close)
        self._sel()

    def showEvent(self, e):
        super().showEvent(e)
        self.reload()

    def reload(self):
        cli = self.panel.need_cli()
        if not cli:
            self.info.setText("Chưa có arduino-cli - dùng 'Cài arduino-cli' trong ESP IDE.")
            return
        self.info.setText("Đang tải danh sách board...")
        bg_run(self, lambda: acli_json(cli, ["core", "search"]), self._loaded)

    def _loaded(self, res):
        code, data, err = res
        self.platforms = parse_platforms(data)
        if code != 0 and not self.platforms:
            self.info.setText("Lỗi: " + (err or "không đọc được danh sách") +
                              "\nThử 'Cập nhật index' hoặc thêm URL board ESP.")
        else:
            has_esp = any(p["id"] in ("esp32:esp32", "esp8266:esp8266") for p in self.platforms)
            self.info.setText(f"{len(self.platforms)} gói board." +
                              ("" if has_esp else "  Chưa thấy ESP32/ESP8266: bấm 'Cập nhật index' "
                                                  "(sẽ tự thêm URL ESP)."))
        self.refill()

    def refill(self):
        q = self.search.text().strip().lower()
        t = self.table
        t.setRowCount(0)
        for p in self.platforms:
            if self.only_inst.isChecked() and not p["installed"]:
                continue
            if q and q not in (p["name"] + " " + p["id"] + " " + p["maintainer"]).lower():
                continue
            r = t.rowCount()
            t.insertRow(r)
            for c, v in enumerate((p["name"], p["id"], p["installed"], p["latest"], p["maintainer"])):
                it = QTableWidgetItem(v)
                if c == 0:
                    it.setData(Qt.UserRole, p["id"])
                t.setItem(r, c, it)

    def current(self):
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        pid = self.table.item(rows[0].row(), 0).data(Qt.UserRole)
        return next((p for p in self.platforms if p["id"] == pid), None)

    def _sel(self):
        p = self.current()
        self.ver.clear()
        self.install_btn.setEnabled(p is not None)
        self.remove_btn.setEnabled(bool(p and p["installed"]))
        if not p:
            return
        for v in (p["versions"] or [p["latest"]]):
            self.ver.addItem(v, v)
        if p["installed"] and p["latest"] and _vkey(p["latest"]) > _vkey(p["installed"]):
            self.install_btn.setText(f"Cập nhật → {p['latest']}")
        else:
            self.install_btn.setText("Cài đặt" if not p["installed"] else "Cài lại / đổi phiên bản")

    def do_install(self):
        p, cli = self.current(), self.panel.need_cli()
        if not p or not cli:
            return
        ver = self.ver.currentData()
        spec = p["id"] + (f"@{ver}" if ver else "")
        steps = [("Cài " + spec, cli, ["core", "install", spec])]
        self.panel.cli_queue(steps, then=lambda: (self.reload(), self.panel.reload_after_core()))

    def do_remove(self):
        p, cli = self.current(), self.panel.need_cli()
        if not p or not cli:
            return
        if QMessageBox.question(self, "Gỡ board", f"Gỡ {p['id']}?") != QMessageBox.Yes:
            return
        self.panel.cli_queue([("Gỡ " + p["id"], cli, ["core", "uninstall", p["id"]])],
                             then=self.reload)

    def update_index(self):
        cli = self.panel.need_cli()
        if not cli:
            return
        acli_ensure_urls(cli)
        self.panel.cli_queue([("Cập nhật index", cli, ["core", "update-index"])], then=self.reload)

    def edit_urls(self):
        cli = self.panel.need_cli()
        if not cli:
            return
        d = QDialog(self)
        d.setWindowTitle("URL quản lý board bổ sung")
        d.resize(620, 300)
        lay = QVBoxLayout(d)
        lay.addWidget(QLabel("Mỗi dòng một URL package_*_index.json:"))
        ed = QPlainTextEdit("\n".join(acli_urls(cli)))
        lay.addWidget(ed, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lay.addWidget(bb)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        if d.exec_() == QDialog.Accepted:
            urls = [u.strip() for u in ed.toPlainText().splitlines() if u.strip()]
            ok, msg = acli_set_urls(cli, urls)
            if not ok:
                QMessageBox.warning(self, "Boards Manager", "Không lưu được cấu hình:\n" + msg)
            else:
                self.update_index()


class LibraryManagerDialog(QDialog):
    """Library Manager: tìm / cài / gỡ / nâng cấp thư viện Arduino."""

    def __init__(self, panel):
        super().__init__(panel.win)
        self.panel = panel
        self.rows = []
        self.installed = {}
        self.setWindowTitle("Library Manager")
        self.resize(860, 540)
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Gõ tên thư viện rồi Enter (để trống = thư viện đã cài)")
        go = QPushButton("Tìm")
        self.only_inst = QCheckBox("Chỉ đã cài")
        top.addWidget(self.search, 1)
        top.addWidget(go)
        top.addWidget(self.only_inst)
        lay.addLayout(top)
        self.table = _mk_table(["Tên", "Đã cài", "Mới nhất", "Tác giả", "Mô tả"], [200, 70, 70, 140])
        lay.addWidget(self.table, 1)
        self.info = QLabel("")
        lay.addWidget(self.info)
        row = QHBoxLayout()
        self.ver = QComboBox()
        self.ver.setMinimumWidth(110)
        self.install_btn = QPushButton("Cài đặt")
        self.remove_btn = QPushButton("Gỡ")
        up = QPushButton("Nâng cấp tất cả")
        more = QToolButton()
        more.setText("Cài từ ▾")
        more.setPopupMode(QToolButton.InstantPopup)
        mm = QMenu(more)
        mm.addAction("File .zip...").triggered.connect(lambda _=False: self.install_zip())
        mm.addAction("Git URL...").triggered.connect(lambda _=False: self.install_git())
        more.setMenu(mm)
        row.addWidget(QLabel("Phiên bản:"))
        row.addWidget(self.ver)
        row.addWidget(self.install_btn)
        row.addWidget(self.remove_btn)
        row.addWidget(up)
        row.addWidget(more)
        row.addStretch(1)
        close = QPushButton("Đóng")
        row.addWidget(close)
        lay.addLayout(row)
        self.search.returnPressed.connect(self.do_search)
        go.clicked.connect(self.do_search)
        self.only_inst.toggled.connect(self.refill)
        self.table.itemSelectionChanged.connect(self._sel)
        self.install_btn.clicked.connect(self.do_install)
        self.remove_btn.clicked.connect(self.do_remove)
        up.clicked.connect(self.do_upgrade)
        close.clicked.connect(self.close)
        self._sel()

    def showEvent(self, e):
        super().showEvent(e)
        self.do_search()

    def do_search(self):
        cli = self.panel.need_cli()
        if not cli:
            return
        q = self.search.text().strip()
        self.info.setText("Đang tìm..." if q else "Đang đọc thư viện đã cài...")

        def work():
            lc, ld, le = acli_json(cli, ["lib", "list"], 60)
            inst = parse_lib_list(ld)
            if not q:
                return lc, inst, [], le
            sc, sd, se = acli_json(cli, ["lib", "search", q], 240)
            return sc, inst, parse_lib_search(sd), se
        bg_run(self, work, self._found)

    def _found(self, res):
        code, inst, found, err = res
        self.installed = {l["name"]: l for l in inst}
        if self.search.text().strip():
            self.rows = found
        else:
            self.rows = [dict(l, versions=[l["installed"]]) for l in inst]
        for r in self.rows:
            r["installed"] = self.installed.get(r["name"], {}).get("installed", "")
        self.info.setText(f"{len(self.rows)} thư viện" + (f" - lỗi: {err}" if code != 0 and err else ""))
        self.refill()

    def refill(self):
        t = self.table
        t.setRowCount(0)
        for l in self.rows:
            if self.only_inst.isChecked() and not l["installed"]:
                continue
            r = t.rowCount()
            t.insertRow(r)
            for c, v in enumerate((l["name"], l["installed"], l["latest"], l["author"], l["sentence"])):
                it = QTableWidgetItem(v)
                if c == 0:
                    it.setData(Qt.UserRole, l["name"])
                t.setItem(r, c, it)

    def current(self):
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        name = self.table.item(rows[0].row(), 0).data(Qt.UserRole)
        return next((l for l in self.rows if l["name"] == name), None)

    def _sel(self):
        l = self.current()
        self.ver.clear()
        self.install_btn.setEnabled(l is not None)
        self.remove_btn.setEnabled(bool(l and l["installed"]))
        if l:
            for v in (l["versions"] or [l["latest"]]):
                if v:
                    self.ver.addItem(v, v)

    def do_install(self):
        l, cli = self.current(), self.panel.need_cli()
        if not l or not cli:
            return
        ver = self.ver.currentData()
        spec = l["name"] + (f"@{ver}" if ver else "")
        self.panel.cli_queue([("Cài thư viện " + spec, cli, ["lib", "install", spec])],
                             then=self.do_search)

    def do_remove(self):
        l, cli = self.current(), self.panel.need_cli()
        if not l or not cli:
            return
        if QMessageBox.question(self, "Gỡ thư viện", f"Gỡ '{l['name']}'?") != QMessageBox.Yes:
            return
        self.panel.cli_queue([("Gỡ " + l["name"], cli, ["lib", "uninstall", l["name"]])],
                             then=self.do_search)

    def do_upgrade(self):
        cli = self.panel.need_cli()
        if cli:
            self.panel.cli_queue([("Nâng cấp thư viện", cli, ["lib", "upgrade"])], then=self.do_search)

    def _allow_unsafe(self, cli):
        run_capture([cli, "config", "set", "library.enable_unsafe_install", "true"], 30)

    def install_zip(self):
        cli = self.panel.need_cli()
        f, _ = QFileDialog.getOpenFileName(self, "Chọn thư viện .zip", "", "Zip (*.zip)")
        if cli and f:
            self._allow_unsafe(cli)
            self.panel.cli_queue([("Cài từ zip", cli, ["lib", "install", "--zip-path", f])],
                                 then=self.do_search)

    def install_git(self):
        cli = self.panel.need_cli()
        url, ok = QInputDialog.getText(self, "Cài từ Git", "URL git (https://github.com/...):")
        url = url.strip() if ok else ""
        if cli and url and not url.startswith("-"):
            self._allow_unsafe(cli)
            self.panel.cli_queue([("Cài từ git", cli, ["lib", "install", "--git-url", url])],
                                 then=self.do_search)


class BoardPickerDialog(QDialog):
    """Chọn board trong danh sách board đã cài (giống Tools > Board)."""

    def __init__(self, panel):
        super().__init__(panel.win)
        self.panel = panel
        self.chosen = None
        self.setWindowTitle("Chọn board")
        self.resize(520, 480)
        lay = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Lọc board (vd: s3, nodemcu, t-display)...")
        self.list = QListWidget()
        self.info = QLabel("Đang tải...")
        lay.addWidget(self.search)
        lay.addWidget(self.list, 1)
        lay.addWidget(self.info)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        mg = bb.addButton("Boards Manager...", QDialogButtonBox.ActionRole)
        lay.addWidget(bb)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        mg.clicked.connect(lambda: (self.reject(), self.panel.open_boards_manager()))
        self.search.textChanged.connect(self.refill)
        self.list.itemDoubleClicked.connect(lambda _i: self.accept())
        self.boards = []
        cli = panel.need_cli()
        if cli:
            bg_run(self, lambda: acli_json(cli, ["board", "listall"], 120), self._loaded)
        else:
            self.info.setText("Chưa có arduino-cli.")

    def _loaded(self, res):
        self.boards = parse_boards(res[1])
        self.info.setText(f"{len(self.boards)} board đã cài." if self.boards else
                          "Chưa có board nào - mở Boards Manager để cài core ESP32/ESP8266.")
        self.refill()

    def refill(self):
        q = self.search.text().strip().lower()
        self.list.clear()
        for name, fq in self.boards:
            if q and q not in (name + " " + fq).lower():
                continue
            it = QListWidgetItem(f"{name}   ({fq})")
            it.setData(Qt.UserRole, (name, fq))
            self.list.addItem(it)
        if self.list.count():
            self.list.setCurrentRow(0)

    def accept(self):
        it = self.list.currentItem()
        self.chosen = it.data(Qt.UserRole) if it else None
        super().accept()


class BoardOptionsDialog(QDialog):
    """Menu Tools của board (Partition Scheme, Flash Size, PSRAM, USB CDC, Upload Speed...)."""

    def __init__(self, panel, fqbn, current):
        super().__init__(panel.win)
        self.setWindowTitle("Tùy chọn board - " + fqbn)
        self.combos, self.result_opts = [], ""
        cli = panel.need_cli()
        self.ok_load = False
        lay = QVBoxLayout(self)
        if not cli:
            lay.addWidget(QLabel("Chưa có arduino-cli."))
            return
        code, data, err = acli_json(cli, ["board", "details", "-b", fqbn], 60)
        opts = parse_options(data)
        if not opts:
            lay.addWidget(QLabel("Không đọc được tùy chọn board.\nCó thể core của board này chưa được cài "
                                 "(mở Boards Manager)." + (f"\n\n{err}" if err else "")))
            return
        self.ok_load = True
        cur = dict(kv.split("=", 1) for kv in current.split(",") if "=" in kv)
        form = QFormLayout()
        for key, label, vals in opts:
            cb = QComboBox()
            for v, vl, sel in vals:
                cb.addItem(vl, v)
            want = cur.get(key)
            i = cb.findData(want) if want is not None else -1
            if i < 0:
                i = next((n for n, (_v, _l, s) in enumerate(vals) if s), 0)
            cb.setCurrentIndex(i)
            self.combos.append((key, cb))
            form.addRow(label + ":", cb)
        w = QWidget()
        w.setLayout(form)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(w)
        lay.addWidget(sc, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        reset = bb.addButton("Mặc định", QDialogButtonBox.ResetRole)
        lay.addWidget(bb)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        reset.clicked.connect(lambda: [c.setCurrentIndex(0) for _k, c in self.combos])
        self.resize(520, min(640, 120 + 36 * len(opts)))

    def accept(self):
        self.result_opts = ",".join(f"{k}={c.currentData()}" for k, c in self.combos)
        super().accept()


class ExamplesDialog(QDialog):
    """Examples: mẫu GKcode + ví dụ của core/thư viện đã cài. Mở bản sao trong sketchbook."""

    def __init__(self, panel):
        super().__init__(panel.win)
        self.panel = panel
        self.setWindowTitle("Examples")
        self.resize(560, 560)
        lay = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Lọc ví dụ...")
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.info = QLabel("")
        lay.addWidget(self.search)
        lay.addWidget(self.tree, 1)
        lay.addWidget(self.info)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        self.open_btn = bb.addButton("Mở ví dụ", QDialogButtonBox.AcceptRole)
        lay.addWidget(bb)
        bb.rejected.connect(self.close)
        self.open_btn.clicked.connect(self.open_current)
        self.tree.itemDoubleClicked.connect(lambda *_: self.open_current())
        self.search.textChanged.connect(self.apply_filter)
        self._populate([])
        cli = panel.need_cli()
        if cli:
            self.info.setText("Đang quét ví dụ trong thư viện đã cài...")
            fq = panel.fqbn()
            bg_run(self, lambda: self._scan(cli, fq), self._scanned)

    @staticmethod
    def _scan(cli, fqbn):
        args = ["lib", "list"] + (["--fqbn", fqbn] if fqbn else [])
        code, data, _e = acli_json(cli, args, 120)
        libs = parse_lib_list(data)
        if not libs and fqbn:
            libs = parse_lib_list(acli_json(cli, ["lib", "list"], 120)[1])
        res = []
        for l in libs:
            found = []
            base = os.path.join(l["dir"], "examples") if l["dir"] else ""
            if base and os.path.isdir(base):
                for r, dirs, files in os.walk(base):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    if any(f.lower().endswith(".ino") for f in files):
                        found.append((os.path.relpath(r, base), r))
                        dirs[:] = []
            else:
                found = [(os.path.basename(p), p) for p in l["examples"] if os.path.isdir(p)]
            if found:
                res.append((l["name"], l["location"], sorted(found)))
        res.sort(key=lambda x: (x[1] != "platform", x[0].lower()))
        return res

    def _scanned(self, res):
        if isinstance(res, tuple):       # lỗi từ FuncThread
            self.info.setText("Không quét được: " + str(res[2]))
            return
        self._populate(res)
        n = sum(len(x[2]) for x in res)
        self.info.setText(f"{n} ví dụ từ {len(res)} thư viện.")

    def _populate(self, libs):
        self.tree.clear()
        g = QTreeWidgetItem(["Mẫu GKcode (có sẵn)"])
        for name in SKETCH_TEMPLATES:
            it = QTreeWidgetItem(g, [name])
            it.setData(0, Qt.UserRole, ("tpl", name))
        self.tree.addTopLevelItem(g)
        g.setExpanded(True)
        for lname, loc, items in libs:
            top = QTreeWidgetItem([lname + ("  (core)" if loc == "platform" else "")])
            for rel, path in items:
                it = QTreeWidgetItem(top, [rel.replace(os.sep, " / ")])
                it.setData(0, Qt.UserRole, ("dir", path))
            self.tree.addTopLevelItem(top)
        self.apply_filter()

    def apply_filter(self):
        q = self.search.text().strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            vis = 0
            for j in range(top.childCount()):
                c = top.child(j)
                hide = bool(q) and q not in (c.text(0) + " " + top.text(0)).lower()
                c.setHidden(hide)
                vis += 0 if hide else 1
            top.setHidden(vis == 0)
            if q and vis:
                top.setExpanded(True)

    def open_current(self):
        it = self.tree.currentItem()
        data = it.data(0, Qt.UserRole) if it else None
        if not data:
            return
        kind, val = data
        try:
            if kind == "tpl":
                path = self.panel.create_sketch(re.sub(r"[^A-Za-z0-9]+", "_", val).strip("_") or "sketch",
                                                SKETCH_TEMPLATES[val], unique=True)
            else:
                path = copy_sketch(val, self.panel.sketchbook())
        except OSError as e:
            QMessageBox.warning(self, "Examples", f"Không tạo được bản sao: {e}")
            return
        self.panel.win.open_path(path)
        self.panel.refresh_status()
        self.close()


class ArduinoSetupDialog(QDialog):
    """Tải & cài arduino-cli một chạm, cấu hình URL ESP32/ESP8266 và cài core."""

    def __init__(self, panel):
        super().__init__(panel.win)
        self.panel = panel
        self.dl = None
        self.setWindowTitle("Cài đặt arduino-cli")
        self.setMinimumWidth(480)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("GKcode sẽ tải arduino-cli (chính thức từ downloads.arduino.cc) về\n" +
                             ARDUINO_HOME + "\nrồi cài sẵn core board bạn chọn:"))
        self.c32 = QCheckBox("ESP32 (esp32:esp32) - ESP32, S2, S3, C3, C6...")
        self.c32.setChecked(True)
        self.c82 = QCheckBox("ESP8266 (esp8266:esp8266) - NodeMCU, Wemos D1...")
        self.c82.setChecked(True)
        lay.addWidget(self.c32)
        lay.addWidget(self.c82)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setVisible(False)
        self.msg = QLabel("")
        self.msg.setWordWrap(True)
        lay.addWidget(self.bar)
        lay.addWidget(self.msg)
        row = QHBoxLayout()
        self.go = QPushButton("Tải và cài đặt")
        have = QPushButton("Tôi đã có arduino-cli...")
        cancel = QPushButton("Hủy")
        row.addWidget(self.go)
        row.addWidget(have)
        row.addStretch(1)
        row.addWidget(cancel)
        lay.addLayout(row)
        self.go.clicked.connect(self.start)
        have.clicked.connect(self.pick_existing)
        cancel.clicked.connect(self.cancel)

    def names(self):
        return [n for n, cb in (("esp32", self.c32), ("esp8266", self.c82)) if cb.isChecked()]

    def pick_existing(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn arduino-cli", "", "Tất cả (*)")
        if f:
            self.panel.win.settings.setValue("esp/arduino_cli", f)
            self.panel.refresh_status()
            self.accept()

    def start(self):
        self.go.setEnabled(False)
        self.bar.setVisible(True)
        urls = arduino_cli_urls()
        ext = ".zip" if urls[0].lower().endswith(".zip") else ".tar.gz"
        dest = os.path.join(ARDUINO_HOME, "download", "arduino-cli" + ext)
        self.dl = DownloadThread(urls, dest)
        self.dl.progress.connect(self._prog)
        self.dl.done.connect(self._downloaded)
        self.dl.failed.connect(self._failed)
        self.msg.setText("Đang tải...")
        self.dl.start()

    def _prog(self, got, total):
        if total:
            self.bar.setRange(0, 100)
            self.bar.setValue(int(got * 100 / total))
        else:
            self.bar.setRange(0, 0)
        self.msg.setText(f"Đang tải... {got // 1024} KB" + (f" / {total // 1024} KB" if total else ""))

    def _failed(self, err):
        self.go.setEnabled(True)
        self.bar.setVisible(False)
        self.msg.setText("Tải thất bại:\n" + err + "\n\nBạn có thể tải thủ công rồi bấm 'Tôi đã có arduino-cli...'.")

    def _downloaded(self, path):
        self.msg.setText("Đang giải nén và cấu hình...")
        self.bar.setRange(0, 0)
        names = self.names()
        bg_run(self, lambda: install_arduino_cli_from(path, names), self._installed)

    def _installed(self, res):
        code, cli, info = res
        self.bar.setVisible(False)
        if code != 0:
            self.go.setEnabled(True)
            self.msg.setText("Lỗi cài đặt: " + str(info))
            return
        self.panel.win.settings.setValue("esp/arduino_cli", cli)
        self.panel.refresh_status()
        steps = [("Cập nhật index", cli, ["core", "update-index"])]
        for n in self.names():
            steps.append((f"Cài core {n}", cli, ["core", "install", f"{n}:{n}"]))
        self.accept()
        self.panel.cli_queue(steps, then=self.panel.reload_after_core)

    def cancel(self):
        if self.dl is not None and self.dl.isRunning():
            self.dl.cancel()
        self.reject()


class PlotCanvas(QWidget):
    COLORS = ["#4fc3f7", "#ff8a65", "#aed581", "#ba68c8", "#ffd54f", "#4db6ac", "#f06292", "#90a4ae"]

    def __init__(self, dlg):
        super().__init__()
        self.dlg = dlg
        self.setMinimumSize(420, 260)

    def paintEvent(self, _e):
        d = self.dlg
        p = QPainter(self)
        t = THEMES.get(d.win.theme_name, THEMES[DEFAULT_THEME])
        bg, fg = QColor(t["terminal_bg"]), QColor(t["terminal_fg"])
        p.fillRect(self.rect(), bg)
        left, top, right, bottom = 56, 28, 12, 12
        plot = QRectF(left, top, max(10, self.width() - left - right), max(10, self.height() - top - bottom))
        data = {k: list(v) for k, v in d.series.items() if v and (d.visible.get(k, True))}
        if not data:
            p.setPen(fg)
            p.drawText(self.rect(), Qt.AlignCenter, "Chưa có dữ liệu - board in dạng  tên:giá_trị,tên2:giá_trị2")
            return
        lo = min(min(v) for v in data.values())
        hi = max(max(v) for v in data.values())
        if hi - lo < 1e-9:
            lo, hi = lo - 1, hi + 1
        pad = (hi - lo) * 0.08
        lo, hi = lo - pad, hi + pad
        grid = QColor(fg)
        grid.setAlpha(50)
        p.setFont(pick_font(8))
        for i in range(6):
            y = plot.bottom() - plot.height() * i / 5
            p.setPen(QPen(grid, 1))
            p.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            p.setPen(fg)
            p.drawText(QRectF(0, y - 8, left - 4, 16), Qt.AlignRight | Qt.AlignVCenter,
                       f"{lo + (hi - lo) * i / 5:.4g}")
        n = d.maxpts.value()
        for idx, (name, vals) in enumerate(data.items()):
            color = QColor(self.COLORS[list(d.series).index(name) % len(self.COLORS)])
            p.setPen(QPen(color, 1.6))
            pts = vals[-n:]
            prev = None
            for i, v in enumerate(pts):
                x = plot.right() - (len(pts) - 1 - i) * plot.width() / max(n - 1, 1)
                y = plot.bottom() - (v - lo) / (hi - lo) * plot.height()
                pt = QPointF(x, y)
                if prev is not None:
                    p.drawLine(prev, pt)
                prev = pt
        x = left
        for name in d.series:
            color = QColor(self.COLORS[list(d.series).index(name) % len(self.COLORS)])
            if not d.visible.get(name, True):
                color.setAlpha(70)
            p.fillRect(QRectF(x, 9, 10, 10), color)
            p.setPen(fg)
            last = d.series[name][-1] if d.series[name] else 0
            txt = f"{name} = {last:.4g}"
            p.drawText(QPointF(x + 14, 18), txt)
            x += 28 + p.fontMetrics().horizontalAdvance(txt)


class SerialPlotterDialog(QDialog):
    """Serial Plotter: vẽ đồ thị giá trị số mà board in ra Serial (hỗ trợ 'tên:giá_trị' như Arduino)."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.series = {}
        self.visible = {}
        self.buf = ""
        self.paused = False
        self.setWindowTitle("Serial Plotter")
        self.resize(760, 460)
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        self.state = QLabel("")
        self.maxpts = QSpinBox()
        self.maxpts.setRange(20, 5000)
        self.maxpts.setValue(300)
        self.pause_btn = QPushButton("Tạm dừng")
        self.pause_btn.setCheckable(True)
        clear = QPushButton("Xóa")
        conn = QPushButton("Mở/đóng cổng")
        mon = QPushButton("Cổng / baud...")
        top.addWidget(self.state, 1)
        top.addWidget(QLabel("Số điểm:"))
        top.addWidget(self.maxpts)
        top.addWidget(self.pause_btn)
        top.addWidget(clear)
        top.addWidget(conn)
        top.addWidget(mon)
        lay.addLayout(top)
        self.canvas = PlotCanvas(self)
        lay.addWidget(self.canvas, 1)
        self.pause_btn.toggled.connect(lambda v: setattr(self, "paused", v))
        clear.clicked.connect(self.clear)
        conn.clicked.connect(self.toggle_port)
        mon.clicked.connect(win.open_serial_monitor)
        self.maxpts.valueChanged.connect(lambda _v: self.canvas.update())
        self.canvas.mousePressEvent = self._click
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def monitor(self):
        w = self.win
        if w.serial_monitor is None:
            w.serial_monitor = SerialMonitorDialog(w)
        sm = w.serial_monitor
        if self.feed not in sm.listeners:
            sm.listeners.append(self.feed)
        return sm

    def showEvent(self, e):
        super().showEvent(e)
        self.monitor()
        self.timer.start(100)
        self._tick()

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)

    def _tick(self):
        sm = self.monitor()
        self.state.setText("● Đang nhận dữ liệu" if sm.is_open() else
                           "○ Cổng chưa mở - bấm 'Mở/đóng cổng'")
        self.canvas.update()

    def toggle_port(self):
        sm = self.monitor()
        sm.toggle_port()
        self._tick()

    def clear(self):
        self.series.clear()
        self.buf = ""
        self.canvas.update()

    def _click(self, ev):
        # bấm vào chú thích để ẩn/hiện một đường
        if ev.y() > 28:
            return
        x = 56
        fm = self.canvas.fontMetrics()
        for name in list(self.series):
            txt = f"{name} = {self.series[name][-1] if self.series[name] else 0:.4g}"
            w = 28 + fm.horizontalAdvance(txt)
            if x <= ev.x() <= x + w:
                self.visible[name] = not self.visible.get(name, True)
                self.canvas.update()
                return
            x += w

    def feed(self, text):
        if self.paused:
            return
        self.buf += text
        lines = self.buf.split("\n")
        self.buf = lines.pop()[-2000:]
        for line in lines:
            for name, val in plot_values(line)[:8]:
                if name not in self.series and len(self.series) >= 8:
                    continue
                s = self.series.setdefault(name, [])
                s.append(val)
                if len(s) > 5000:
                    del s[:1000]


class EspIdePanel(QWidget):
    """ESP IDE: biên dịch / nạp / monitor cho Arduino (arduino-cli), PlatformIO và MicroPython."""
    FRAMEWORKS = [("Tự nhận theo dự án", "auto"), ("Arduino (arduino-cli)", "arduino"),
                  ("PlatformIO", "pio"), ("MicroPython (mpremote)", "mpy")]

    def __init__(self, win):
        super().__init__()
        self.win = win
        s = win.settings
        self._buf, self._prev_tap, self._tapping = [], None, False
        self._sb = ""
        self._dlgs = {}
        self.plotter = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)

        def tool(text, tip, fn):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.setToolButtonStyle(Qt.ToolButtonTextOnly)
            b.setMinimumWidth(34)
            b.clicked.connect(lambda _=False, f=fn: f())
            return b
        bar = QHBoxLayout()
        bar.setSpacing(4)
        bar.addWidget(tool("✓", "Verify - biên dịch (F8)", lambda: self.run("build")))
        bar.addWidget(tool("→", "Upload - biên dịch và nạp (Ctrl+F8)", lambda: self.run("upload")))
        bar.addWidget(tool("＋", "Sketch mới", self.new_sketch))
        sk = QToolButton()
        sk.setText("📂▾")
        sk.setToolTip("Mở sketch / Sketchbook")
        sk.setPopupMode(QToolButton.InstantPopup)
        self.sk_menu = QMenu(sk)
        self.sk_menu.aboutToShow.connect(self._fill_sketch_menu)
        sk.setMenu(self.sk_menu)
        bar.addWidget(sk)
        bar.addWidget(tool("🔌", "Serial Monitor", self.open_monitor))
        bar.addWidget(tool("📈", "Serial Plotter", self.open_plotter))
        bar.addStretch(1)
        lay.addLayout(bar)

        form = QFormLayout()
        self.fw = QComboBox()
        for label, key in self.FRAMEWORKS:
            self.fw.addItem(label, key)
        self.fw.setCurrentIndex(max(0, self.fw.findData(s.value("esp/ide/fw", "auto"))))
        self.board = QComboBox()
        self.board.setEditable(True)
        for label, fqbn, _p, _c in ESP_BOARDS:
            self.board.addItem(f"{label}  ({fqbn})", fqbn)
        try:
            for label, fqbn in json.loads(s.value("esp/ide/recent", "[]")):
                if self.board.findData(fqbn) < 0:
                    self.board.addItem(label, fqbn)
        except (ValueError, TypeError):
            pass
        saved = s.value("esp/ide/fqbn", "esp32:esp32:esp32s3")
        i = self.board.findData(saved)
        if i >= 0:
            self.board.setCurrentIndex(i)
        else:
            self.board.setEditText(saved)
        self._last_fqbn = self.fqbn()
        brow = QHBoxLayout()
        pick = QPushButton("…")
        pick.setFixedWidth(30)
        pick.setToolTip("Chọn board trong danh sách đã cài (Tools > Board)")
        brow.addWidget(self.board, 1)
        brow.addWidget(pick)
        self.opts = QLineEdit(s.value("esp/ide/opts", ""))
        self.opts.setPlaceholderText("Partition, Flash, PSRAM, USB CDC... → nút ⚙")
        orow = QHBoxLayout()
        gear = QPushButton("⚙")
        gear.setFixedWidth(30)
        gear.setToolTip("Tùy chọn board (Tools): Partition Scheme, Flash Size, PSRAM, Upload Speed...")
        orow.addWidget(self.opts, 1)
        orow.addWidget(gear)
        self.env = QComboBox()
        prow = QHBoxLayout()
        self.port = QComboBox()
        self.port.setMinimumWidth(130)
        rb = QPushButton("⟳")
        rb.setFixedWidth(30)
        rb.setToolTip("Quét lại cổng COM")
        det = QPushButton("Nhận board")
        det.setToolTip("Dò board đang cắm (arduino-cli board list) và chọn đúng board + cổng")
        prow.addWidget(self.port, 1)
        prow.addWidget(rb)
        prow.addWidget(det)
        self.warn = QComboBox()
        for label, key in (("Warnings: Mặc định", "default"), ("Warnings: Không", "none"),
                           ("Warnings: Nhiều hơn", "more"), ("Warnings: Tất cả", "all")):
            self.warn.addItem(label, key)
        self.warn.setCurrentIndex(max(0, self.warn.findData(s.value("esp/ide/warn", "default"))))
        self.verbose = QCheckBox("Verbose")
        self.verbose.setChecked(str(s.value("esp/ide/verbose", "false")).lower() == "true")
        wrow = QHBoxLayout()
        wrow.addWidget(self.warn, 1)
        wrow.addWidget(self.verbose)
        form.addRow("Khung:", self.fw)
        form.addRow("Board:", brow)
        form.addRow("Tùy chọn:", orow)
        form.addRow("Env (PIO):", self.env)
        form.addRow("Cổng:", prow)
        form.addRow("Biên dịch:", wrow)
        lay.addLayout(form)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        lay.addWidget(self.status)
        self.setup_btn = QPushButton("⬇ Cài arduino-cli + core ESP (tự động)")
        self.setup_btn.clicked.connect(self.open_setup)
        lay.addWidget(self.setup_btn)

        self.flash_bar, self.ram_bar = QProgressBar(), QProgressBar()
        for b, name in ((self.flash_bar, "Flash"), (self.ram_bar, "RAM")):
            b.setRange(0, 100)
            b.setFormat(f"{name}: -")
            b.setValue(0)
            b.setTextVisible(True)
            lay.addWidget(b)
        self.prob_label = QLabel("Problems")
        lay.addWidget(self.prob_label)
        self.problems = QListWidget()
        self.problems.setMinimumHeight(90)
        self.problems.itemActivated.connect(self._open_problem)
        self.problems.itemClicked.connect(self._open_problem)
        lay.addWidget(self.problems, 1)

        more = QToolButton()
        more.setText("Công cụ ▾")
        more.setPopupMode(QToolButton.InstantPopup)
        mm = QMenu(more)
        for text, fn in (
                ("Boards Manager...", self.open_boards_manager),
                ("Library Manager...", self.open_library_manager),
                ("Examples...", self.open_examples),
                ("Sketch mới...", self.new_sketch),
                (None, None),
                ("Nạp + Serial Monitor", lambda: self.run("upload_monitor")),
                ("Dọn bản biên dịch", lambda: self.run("clean")),
                ("Cổng / board đang cắm (arduino-cli)", self.board_list),
                (None, None),
                ("Cài arduino-cli + core ESP (tự động)...", self.open_setup),
                ("Cài core ESP cho Arduino (arduino-cli)", self.install_core),
                ("Cài PlatformIO (pip)", lambda: self.win._pip_install(["platformio"])),
                ("Cài mpremote cho MicroPython (pip)", lambda: self.win._pip_install(["mpremote"])),
                (None, None),
                ("MicroPython: chạy file trên board (không lưu)", lambda: self.run("run")),
                ("MicroPython: liệt kê file trên board", self.mpy_ls),
                ("MicroPython: cài gói (mip)...", self.install_library),
                (None, None),
                ("Nạp firmware / esptool...", self.win.open_esp_dialog),
                ("Dự án ESP mới từ mẫu...", self.win.new_from_template),
                ("Đặt thư mục Sketchbook...", self.choose_sketchbook)):
            if text is None:
                mm.addSeparator()
            else:
                mm.addAction(text).triggered.connect(lambda _=False, f=fn: f())
        more.setMenu(mm)
        r = QHBoxLayout()

        def mk(text, fn):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, f=fn: f())
            return b
        r.addWidget(mk("Boards", self.open_boards_manager))
        r.addWidget(mk("Libraries", self.open_library_manager))
        r.addWidget(mk("Examples", self.open_examples))
        r.addWidget(more)
        lay.addLayout(r)

        rb.clicked.connect(lambda: self.refresh_ports())
        det.clicked.connect(self.detect_board)
        pick.clicked.connect(self.pick_board)
        gear.clicked.connect(self.edit_options)
        self.board.activated.connect(lambda _i: self._board_changed())
        self.fw.currentIndexChanged.connect(lambda _i: self.refresh_status())
        self.refresh_ports(s.value("esp/ide/port", ""))
        self.refresh_status()

    #  arduino-cli: thiết lập, cấu hình
    def need_cli(self, ask=True):
        cli = self._arduino_cli()
        if not cli and ask:
            if QMessageBox.question(self, "arduino-cli",
                                    "Chưa có arduino-cli. Tải và cài tự động ngay?") == QMessageBox.Yes:
                self.open_setup()
        return cli

    def open_setup(self):
        d = ArduinoSetupDialog(self)
        d.exec_()

    def cli_queue(self, steps, cwd=None, then=None):
        def done():
            self.win._on_done()
            if then:
                then()
        self.win.terminal.run_queue(steps, on_done=done, on_step=self.win._on_step,
                                    on_fail=self._on_fail, cwd=cwd or self.win._project_root())

    def reload_after_core(self):
        self.refresh_status()

    def _dialog(self, key, cls):
        d = self._dlgs.get(key)
        if d is None:
            d = self._dlgs[key] = cls(self)
        d.show()
        d.raise_()
        d.activateWindow()
        return d

    def open_boards_manager(self):
        if self.need_cli():
            self._dialog("boards", BoardsManagerDialog)

    def open_library_manager(self):
        info = self.detect()
        if info is not None and info["kind"] != "arduino":
            self.install_library()
            return
        if self.need_cli():
            self._dialog("libs", LibraryManagerDialog)

    def open_examples(self):
        d = ExamplesDialog(self)       # tạo mới để quét lại theo board hiện tại
        self._dlgs["examples"] = d
        d.show()

    def open_plotter(self):
        if self.plotter is None:
            self.plotter = SerialPlotterDialog(self.win)
        self.plotter.show()
        self.plotter.raise_()

    #  board / tùy chọn
    def _board_changed(self):
        f = self.fqbn()
        if f != self._last_fqbn:
            self._last_fqbn = f
            self.opts.setText("")

    def set_board(self, label, fqbn, keep_opts=False):
        i = self.board.findData(fqbn)
        if i < 0:
            self.board.insertItem(0, f"{label}  ({fqbn})", fqbn)
            i = 0
            try:
                rec = [x for x in json.loads(self.win.settings.value("esp/ide/recent", "[]")) if x[1] != fqbn]
            except (ValueError, TypeError):
                rec = []
            rec.insert(0, [f"{label}  ({fqbn})", fqbn])
            self.win.settings.setValue("esp/ide/recent", json.dumps(rec[:8]))
        self.board.setCurrentIndex(i)
        if not keep_opts:
            self._board_changed()

    def pick_board(self):
        if not self.need_cli():
            return
        d = BoardPickerDialog(self)
        if d.exec_() == QDialog.Accepted and d.chosen:
            self.set_board(d.chosen[0], d.chosen[1])

    def edit_options(self):
        if not self.need_cli():
            return
        d = BoardOptionsDialog(self, self.fqbn(), self.opts.text().strip())
        if d.ok_load and d.exec_() == QDialog.Accepted:
            self.opts.setText(d.result_opts)
        elif not d.ok_load:
            d.exec_()

    def detect_board(self):
        cli = self.need_cli()
        if not cli:
            return
        self.status.setText("Đang dò board...")

        def done(res):
            ports = parse_ports(res[1])
            self.refresh_ports()
            self.refresh_status()
            if not ports:
                QMessageBox.information(self, "Nhận board", "Không thấy board nào đang cắm.")
                return
            want = tool_port(self.port_name())
            pick = next((p for p in ports if p["address"] == want and p["boards"]), None) \
                or next((p for p in ports if p["boards"]), None)
            if pick is None:
                lst = "\n".join(f"{p['address']} - {p['label']}" for p in ports)
                QMessageBox.information(self, "Nhận board",
                                        "Thấy cổng nhưng arduino-cli chưa nhận ra loại board:\n" + lst +
                                        "\n\nHãy chọn board thủ công (nút …).")
                return
            name, fq = pick["boards"][0]
            self.set_board(name, fq)
            for n in range(self.port.count()):
                if tool_port(self.port.itemData(n) or "") == pick["address"]:
                    self.port.setCurrentIndex(n)
                    break
            self.win.terminal.appendPlainText(f"[Nhận board] {name} ({fq}) @ {pick['address']}")
        bg_run(self, lambda: acli_json(cli, ["board", "list"], 60), done)

    #  sketchbook
    def sketchbook(self):
        s = self.win.settings.value("esp/sketchbook", "")
        if s:
            return s
        if not self._sb:
            cli = self._arduino_cli()
            self._sb = acli_sketchbook(cli) if cli else default_sketchbook()
        return self._sb

    def choose_sketchbook(self):
        d = QFileDialog.getExistingDirectory(self, "Thư mục Sketchbook", self.sketchbook())
        if d:
            self.win.settings.setValue("esp/sketchbook", d)

    def create_sketch(self, name, code, unique=False):
        base = self.sketchbook()
        os.makedirs(base, exist_ok=True)
        folder, n = os.path.join(base, name), 2
        if os.path.exists(folder):
            if not unique:
                raise OSError(f"Đã có sketch tên '{name}' trong sketchbook")
            while os.path.exists(os.path.join(base, f"{name}_{n}")):
                n += 1
            name = f"{name}_{n}"
            folder = os.path.join(base, name)
        os.makedirs(folder)
        path = os.path.join(folder, name + ".ino")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        return path

    def new_sketch(self):
        d = QDialog(self)
        d.setWindowTitle("Sketch mới")
        lay = QVBoxLayout(d)
        form = QFormLayout()
        name = QLineEdit("sketch_" + datetime.datetime.now().strftime("%b%d").lower())
        tpl = QComboBox()
        tpl.addItems(list(SKETCH_TEMPLATES))
        form.addRow("Tên sketch:", name)
        form.addRow("Mẫu:", tpl)
        lay.addLayout(form)
        lay.addWidget(QLabel("Lưu trong: " + self.sketchbook()))
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lay.addWidget(bb)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        if d.exec_() != QDialog.Accepted:
            return
        nm = name.text().strip()
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_\-]{0,62}", nm):
            QMessageBox.warning(self, "Sketch mới", "Tên chỉ gồm chữ không dấu, số, _ và -.")
            return
        try:
            path = self.create_sketch(nm, SKETCH_TEMPLATES[tpl.currentText()])
        except OSError as e:
            QMessageBox.warning(self, "Sketch mới", str(e))
            return
        self.win.open_path(path)
        self.refresh_status()

    def _fill_sketch_menu(self):
        m = self.sk_menu
        m.clear()
        m.addAction("Sketch mới...").triggered.connect(lambda _=False: self.new_sketch())
        m.addAction("Mở thư mục sketch...").triggered.connect(lambda _=False: self.open_sketch_dialog())
        m.addSeparator()
        base = self.sketchbook()
        try:
            names = sorted(n for n in os.listdir(base)
                           if os.path.isfile(os.path.join(base, n, n + ".ino")))
        except OSError:
            names = []
        for n in names[:40]:
            m.addAction(n).triggered.connect(
                lambda _=False, p=os.path.join(base, n, n + ".ino"): self._open_sketch(p))
        if not names:
            m.addAction("(sketchbook trống)").setEnabled(False)

    def _open_sketch(self, path):
        self.win.open_path(path)
        self.refresh_status()

    def open_sketch_dialog(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục sketch", self.sketchbook())
        if not d:
            return
        inos = sorted(f for f in os.listdir(d) if f.lower().endswith(".ino"))
        if not inos:
            QMessageBox.information(self, "Mở sketch", "Thư mục này không có file .ino.")
            return
        want = os.path.basename(d) + ".ino"
        self._open_sketch(os.path.join(d, want if want in inos else inos[0]))

    #  kết quả biên dịch: dung lượng + danh sách lỗi
    def _tap_on(self):
        t = self.win.terminal
        self._buf = []
        self._tap_off()
        prev = t.on_output

        def tap(text, prev=prev):
            self._buf.append(text)
            if prev:
                prev(text)
        self._prev_tap, self._tapping = prev, True
        t.on_output = tap

    def _tap_off(self):
        if self._tapping:
            self.win.terminal.on_output = self._prev_tap
            self._tapping = False
        return ANSI_RE.sub("", "".join(self._buf)).replace("\r\n", "\n")

    def _show_results(self, text):
        sizes = parse_sizes(text)
        for key, bar, name in (("flash", self.flash_bar, "Flash"), ("ram", self.ram_bar, "RAM")):
            if key in sizes:
                used, mx = sizes[key]
                pct = int(used * 100 / mx) if mx else 0
                bar.setValue(min(pct, 100))
                bar.setFormat(f"{name}: {used:,} / {mx:,} byte ({pct}%)")
        probs = parse_problems(text)
        self.problems.clear()
        errs = sum(1 for p in probs if p["sev"] == "error")
        warns = sum(1 for p in probs if p["sev"] == "warning")
        self.prob_label.setText(f"Problems: {errs} lỗi, {warns} cảnh báo")
        icons = {"error": "✖", "warning": "⚠", "note": "ℹ"}
        for p in probs[:300]:
            it = QListWidgetItem(f"{icons.get(p['sev'], '·')} {os.path.basename(p['file'])}:{p['line']}  {p['msg']}")
            it.setToolTip(f"{p['file']}:{p['line']}:{p['col']}\n{p['msg']}")
            it.setData(Qt.UserRole, (p["file"], p["line"]))
            col = {"error": "#e5534b", "warning": "#d29922"}.get(p["sev"])
            if col:
                it.setForeground(QColor(col))
            self.problems.addItem(it)
        if probs:
            self.problems.scrollToTop()

    def _open_problem(self, it):
        data = it.data(Qt.UserRole)
        if not data:
            return
        path, line = data
        if not os.path.isabs(path):
            info = self.detect()
            path = os.path.join(info["root"] if info else self.win._project_root(), path)
        if os.path.isfile(path):
            self.win.open_path(path)
            ed = self.win.current_editor()
            if ed is not None:
                ed.goto_line(line)

    #  thông tin dự án
    def fqbn(self):
        i, txt = self.board.currentIndex(), self.board.currentText().strip()
        if i >= 0 and txt == self.board.itemText(i):
            return self.board.itemData(i)
        return txt

    def full_fqbn(self):
        o = self.opts.text().strip().strip(":")
        return self.fqbn() + (":" + o if o else "")

    def port_name(self):
        return self.port.currentData() or ""

    def refresh_ports(self, keep=""):
        cur = keep or self.port.currentData()
        self.port.clear()
        ports = list_serial_ports()
        for name, label, _esp in ports:
            self.port.addItem(label, name)
        if not ports:
            self.port.addItem("(không thấy cổng nào)", "")
        if cur:
            i = self.port.findData(cur)
            if i >= 0:
                self.port.setCurrentIndex(i)

    def refresh(self):
        self.refresh_ports()
        self.refresh_status()

    def detect(self):
        mode = self.fw.currentData()
        ed = self.win.current_editor()
        path = ed.file_path if ed is not None and ed.file_path else None
        base = os.path.dirname(os.path.abspath(path)) if path else self.win._project_root()

        def inos(d):
            try:
                return sorted(f for f in os.listdir(d) if f.lower().endswith(".ino"))
            except OSError:
                return []
        if mode in ("auto", "pio"):
            root = find_up(base, "platformio.ini") or find_up(self.win._project_root(), "platformio.ini")
            if root:
                return {"kind": "pio", "root": root, "file": path}
        if mode in ("auto", "arduino") and inos(base):
            f = path if path and path.lower().endswith(".ino") else os.path.join(base, inos(base)[0])
            return {"kind": "arduino", "root": base, "file": f}
        if mode in ("auto", "mpy") and path and path.lower().endswith(".py"):
            return {"kind": "mpy", "root": base, "file": path}
        if mode in ("auto", "arduino"):
            root = self.win._project_root()
            if inos(root):
                return {"kind": "arduino", "root": root, "file": os.path.join(root, inos(root)[0])}
        return None

    def _arduino_cli(self):
        p = self.win.settings.value("esp/arduino_cli", "") or ""
        if p and os.path.isfile(p):
            return p
        return managed_arduino_cli() or find_tool("arduino-cli")

    def _pio_cmd(self):
        p = find_tool("pio", "platformio")
        if p:
            return [p]
        py = get_python_command()
        return (py + ["-m", "platformio"]) if py else None

    def _mpremote_cmd(self):
        p = find_tool("mpremote")
        if p:
            return [p]
        py = get_python_command()
        return (py + ["-m", "mpremote"]) if py else None

    def refresh_status(self):
        info = self.detect()
        if info is None:
            self.status.setText("Chưa nhận ra dự án ESP: mở file .ino (＋ = sketch mới), thư mục có "
                                "platformio.ini hoặc file .py (MicroPython).")
            self.setup_btn.setVisible(not self._arduino_cli())
            return
        kind = info["kind"]
        name = {"arduino": "Arduino sketch", "pio": "PlatformIO", "mpy": "MicroPython"}[kind]
        ok = {"arduino": bool(self._arduino_cli()), "pio": bool(self._pio_cmd()),
              "mpy": bool(self._mpremote_cmd())}[kind]
        txt = f"Dự án: {name}\n{info['root']}"
        if not ok:
            txt += "\n⚠ Chưa có công cụ - xem menu 'Công cụ ▾'"
        self.status.setText(txt)
        self.setup_btn.setVisible(kind == "arduino" and not ok)
        if kind == "pio":
            cur = self.env.currentData()
            self.env.clear()
            self.env.addItem("(mặc định)", "")
            try:
                with open(os.path.join(info["root"], "platformio.ini"), encoding="utf-8",
                          errors="replace") as f:
                    for m in re.finditer(r"^\[env:([^\]]+)\]", f.read(), re.M):
                        self.env.addItem(m.group(1), m.group(1))
            except OSError:
                pass
            i = self.env.findData(cur)
            if i >= 0:
                self.env.setCurrentIndex(i)

    def _save(self):
        s = self.win.settings
        s.setValue("esp/ide/fw", self.fw.currentData())
        s.setValue("esp/ide/fqbn", self.fqbn())
        s.setValue("esp/ide/opts", self.opts.text().strip())
        s.setValue("esp/ide/port", self.port_name())
        s.setValue("esp/ide/warn", self.warn.currentData())
        s.setValue("esp/ide/verbose", "true" if self.verbose.isChecked() else "false")

    def _flush_saves(self):
        w = self.win
        for i in range(w.tabs.count()):
            ed = w.tabs.widget(i)
            if ed.file_path and ed.document().isModified():
                w._save_editor(ed, quiet=True)

    #  tạo bước chạy
    def _sketch_dir(self, file):
        d = os.path.dirname(os.path.abspath(file))
        try:
            inos = sorted(f for f in os.listdir(d) if f.lower().endswith(".ino"))
        except OSError as e:
            return None, [], {}, str(e)
        if not inos:
            return None, [], {}, f"Không thấy file .ino trong {d}"
        if os.path.basename(d) + ".ino" in inos:
            return d, [], {}, None
        # arduino-cli bắt buộc tên thư mục = tên file .ino -> biên dịch bản sao tạm
        main = os.path.splitext(os.path.basename(file))[0] if file.lower().endswith(".ino") \
            else os.path.splitext(inos[0])[0]
        tmp = tempfile.mkdtemp(prefix="gkesp_")
        dst = os.path.join(tmp, main)
        shutil.copytree(d, dst, ignore=shutil.ignore_patterns(".*", "build", ".pio", "__pycache__", "*.exe"))
        return dst, [tmp], {dst: d}, None

    def _steps(self, action, info, port):
        """-> (steps, cwd, cleanup, path_map, lỗi)"""
        kind, root = info["kind"], info["root"]
        up = action in ("upload", "upload_monitor")
        if kind == "arduino":
            cli = self._arduino_cli()
            if not cli:
                return None, None, [], {}, ("Chưa có arduino-cli.\nTải tại https://arduino.github.io/arduino-cli/ "
                                            "rồi thêm vào PATH, hoặc dùng PlatformIO (menu 'Thêm ▾' → Cài PlatformIO).")
            if action == "clean":
                return [("Dọn cache", cli, ["cache", "clean"])], root, [], {}, None
            if action == "run":
                return None, None, [], {}, "Chỉ dùng cho MicroPython."
            sketch, cleanup, pmap, err = self._sketch_dir(info["file"])
            if err:
                return None, None, [], {}, err
            extra = []
            if self.warn.currentData() != "default":
                extra += ["--warnings", self.warn.currentData()]
            if self.verbose.isChecked():
                extra.append("-v")
            out = ["--output-dir", os.path.join(root, "build")] if action == "export" else []
            args = (["compile", "--fqbn", self.full_fqbn()] + extra + out +
                    (["--upload", "-p", port] if up else []) + [sketch])
            label = "Biên dịch & nạp" if up else ("Biên dịch & xuất firmware" if out else "Biên dịch")
            return [(label, cli, args)], root, cleanup, pmap, None
        if kind == "pio":
            pio = self._pio_cmd()
            if not pio:
                return None, None, [], {}, "Không tìm thấy Python để chạy PlatformIO."
            env = self.env.currentData()
            base = pio[1:] + ["run", "-d", root] + (["-e", env] if env else [])
            if action == "clean":
                return [("Dọn", pio[0], base + ["-t", "clean"])], root, [], {}, None
            if action == "run":
                return None, None, [], {}, "Chỉ dùng cho MicroPython."
            if up:
                return [("Biên dịch & nạp", pio[0], base + ["-t", "upload"] +
                         (["--upload-port", port] if port else []))], root, [], {}, None
            return [("Biên dịch", pio[0], base)], root, [], {}, None
        # MicroPython
        file = info["file"]
        py = get_python_command()
        if action in ("build", "export"):
            if not py:
                return None, None, [], {}, "Không tìm thấy Python."
            code = "import ast,sys;ast.parse(open(sys.argv[1],encoding='utf-8').read())"
            return [("Kiểm tra cú pháp", py[0], py[1:] + ["-c", code, file])], root, [], {}, None
        if action == "clean":
            return None, None, [], {}, "MicroPython không có bước dọn."
        mp = self._mpremote_cmd()
        if not mp:
            return None, None, [], {}, "Không tìm thấy Python để chạy mpremote."
        conn = ["connect", port]
        if action == "run":
            return [("Chạy trên board", mp[0], mp[1:] + conn + ["run", file])], root, [], {}, None
        target = ":" + (os.path.basename(file) if os.path.basename(file) in ("boot.py", "main.py") else "main.py")
        return [("Chép lên board", mp[0], mp[1:] + conn + ["fs", "cp", file, target]),
                ("Khởi động lại board", mp[0], mp[1:] + conn + ["reset"])], root, [], {}, None

    def run(self, action):
        info = self.detect()
        if info is None:
            QMessageBox.information(self, "ESP IDE", "Chưa nhận ra dự án ESP.\n"
                                    "Mở file .ino, thư mục có platformio.ini hoặc file .py MicroPython.")
            return
        if info["kind"] == "arduino" and not self._arduino_cli():
            self.need_cli()      # hỏi tải & cài arduino-cli tự động, xong nhấn lại F5 / F8
            return
        self._save()
        self._flush_saves()
        port = tool_port(self.port_name())
        needs_port = action in ("upload", "upload_monitor", "run") and (info["kind"] != "pio" or action == "run")
        if needs_port and not port:
            QMessageBox.warning(self, "Chưa chọn cổng", "Hãy chọn cổng COM của board (nút ⟳ để quét lại).")
            return
        sm = self.win.serial_monitor
        if action not in ("build", "clean", "export") and sm is not None and sm.is_open():
            sm.close_port()      # cổng phải rảnh để nạp
            self.win.terminal.appendPlainText("[Đã đóng Serial Monitor để nạp]")
        steps, cwd, cleanup, pmap, err = self._steps(action, info, port)
        if err:
            QMessageBox.critical(self, "ESP IDE", err)
            return
        self.win.terminal.appendPlainText(f"\n=== ESP IDE ({info['kind']}): {action} ===")
        monitor = action == "upload_monitor"
        export_dir = None
        if action == "export":
            export_dir = {"arduino": os.path.join(info["root"], "build"),
                          "pio": os.path.join(info["root"], ".pio", "build")}.get(info["kind"])
        self._tap_on()
        self.win.terminal.run_queue(
            steps, on_done=lambda: self._done(monitor, export_dir), on_step=self.win._on_step,
            on_fail=self._on_fail, cwd=cwd, cleanup_paths=cleanup, path_map=pmap)

    def _announce_export(self, d):
        """Liệt kê firmware vừa xuất (.bin/.hex/.elf/.uf2) và mở thư mục chứa."""
        found = []
        for r, _dirs, files in os.walk(d):
            for f in files:
                if f.lower().endswith((".bin", ".hex", ".elf", ".uf2")):
                    found.append(os.path.join(r, f))
        t = self.win.terminal
        if found:
            t.appendPlainText("Firmware đã xuất:\n" + "\n".join("  " + p for p in sorted(found)[:12]))
        if os.path.isdir(d):
            QDesktopServices.openUrl(QUrl.fromLocalFile(d))

    def _done(self, monitor, export_dir=None):
        self.win._on_done()
        self._show_results(self._tap_off())
        if export_dir:
            self._announce_export(export_dir)
        if monitor:
            QTimer.singleShot(1200, self.open_monitor_and_connect)   # chờ board khởi động lại

    def open_monitor(self):
        self.win.open_serial_monitor()
        sm = self.win.serial_monitor
        sm.refresh_ports(self.port_name())

    def open_monitor_and_connect(self):
        self.open_monitor()
        sm = self.win.serial_monitor
        i = sm.port_cb.findData(self.port_name())
        if i >= 0:
            sm.port_cb.setCurrentIndex(i)
        if not sm.is_open():
            sm.open_port()

    def _on_fail(self, label, code):
        self.win._on_fail(label, code)
        tapped = self._tap_off()
        if tapped:
            self._show_results(tapped)
        out = tapped or self.win.terminal.last_output
        if "No module named platformio" in out:
            QTimer.singleShot(0, lambda: self._offer_pip("platformio"))
        elif "No module named mpremote" in out:
            QTimer.singleShot(0, lambda: self._offer_pip("mpremote"))
        elif re.search(r"platform .*not installed|Platform '.*' not found|Unknown FQBN|"
                       r"no core|core .* not installed", out, re.I):
            QTimer.singleShot(0, self._offer_core)

    def _offer_pip(self, pkg):
        if QMessageBox.question(self, "Thiếu công cụ", f"Chưa cài '{pkg}'. Cài ngay bằng pip?") == QMessageBox.Yes:
            self.win._pip_install([pkg])

    def _offer_core(self):
        if QMessageBox.question(self, "Thiếu core board",
                                "Có vẻ chưa cài core ESP cho arduino-cli. Cài ngay?") == QMessageBox.Yes:
            self.install_core()

    #  thao tác phụ
    def _queue(self, steps, cwd=None, then=None):
        self.cli_queue(steps, cwd, then)

    def install_core(self):
        cli = self.need_cli()
        if not cli:
            return
        parts = self.fqbn().split(":")
        core = ":".join(parts[:2]) if len(parts) >= 2 else "esp32:esp32"
        url = ESP_CORE_URLS.get(parts[0], ESP_CORE_URLS["esp32"])
        self._queue([("Cập nhật index", cli, ["core", "update-index", "--additional-urls", url]),
                     ("Cài core " + core, cli, ["core", "install", core, "--additional-urls", url])])

    def install_library(self):
        info = self.detect()
        if info is None:
            QMessageBox.information(self, "ESP IDE", "Chưa nhận ra dự án ESP.")
            return
        name, ok = QInputDialog.getText(self, "Cài thư viện", "Tên thư viện (vd: Adafruit NeoPixel, TFT_eSPI):")
        name = name.strip() if ok else ""
        if not name or name.startswith("-"):
            return
        kind = info["kind"]
        if kind == "arduino":
            cli = self._arduino_cli()
            steps = [("Cài thư viện", cli, ["lib", "install", name])] if cli else None
        elif kind == "pio":
            pio = self._pio_cmd()
            steps = [("Cài thư viện", pio[0], pio[1:] + ["pkg", "install", "-d", info["root"],
                                                        "--library", name])] if pio else None
        else:
            mp, port = self._mpremote_cmd(), tool_port(self.port_name())
            steps = [("Cài gói", mp[0], mp[1:] + ["connect", port, "mip", "install", name])] \
                if mp and port else None
        if not steps:
            QMessageBox.warning(self, "ESP IDE", "Thiếu công cụ hoặc chưa chọn cổng.")
            return
        self._queue(steps, info["root"])

    def board_list(self):
        cli = self._arduino_cli()
        if cli:
            self._queue([("Board đang cắm", cli, ["board", "list"])])
        else:
            QMessageBox.information(self, "arduino-cli", "Chưa có arduino-cli.")

    def mpy_ls(self):
        mp, port = self._mpremote_cmd(), tool_port(self.port_name())
        if not mp or not port:
            QMessageBox.warning(self, "MicroPython", "Thiếu mpremote hoặc chưa chọn cổng.")
            return
        self._queue([("Liệt kê file board", mp[0], mp[1:] + ["connect", port, "fs", "ls"])])


class SerialMonitorDialog(QDialog):
    BAUDS = ["300", "1200", "2400", "4800", "9600", "19200", "38400", "57600", "74880",
             "115200", "230400", "460800", "921600", "1500000", "2000000"]

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Serial Monitor")
        self.resize(780, 540)
        self._line_start = True
        self.listeners = []     # hàm nhận văn bản serial (Serial Plotter...)
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.port = QSerialPort(self) if QSerialPort is not None else None
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        self.port_cb = QComboBox()
        self.port_cb.setMinimumWidth(240)
        refresh = QPushButton("⟳")
        refresh.setFixedWidth(30)
        self.baud_cb = QComboBox()
        self.baud_cb.addItems(self.BAUDS)
        self.baud_cb.setCurrentText(str(win.settings.value("serial/baud", "115200")))
        self.open_btn = QPushButton("Mở cổng")
        self.reset_btn = QPushButton("Reset (RTS)")
        top.addWidget(QLabel("Cổng:"))
        top.addWidget(self.port_cb)
        top.addWidget(refresh)
        top.addWidget(QLabel("Baud:"))
        top.addWidget(self.baud_cb)
        top.addWidget(self.open_btn)
        top.addWidget(self.reset_btn)
        top.addStretch(1)
        lay.addLayout(top)

        self.out = QPlainTextEdit()
        self.out.setReadOnly(True)
        self.out.setMaximumBlockCount(30000)
        self.out.setFont(pick_font(10))
        t = THEMES.get(win.theme_name, THEMES[DEFAULT_THEME])
        self.out.setStyleSheet(f"QPlainTextEdit {{ background: {t['terminal_bg']}; "
                               f"color: {t['terminal_fg']}; border: none; }}")
        lay.addWidget(self.out, 1)

        row = QHBoxLayout()
        self.input = HistoryLineEdit()
        self.input.setPlaceholderText("Gõ lệnh gửi tới board rồi Enter...")
        self.eol = QComboBox()
        self.eol.addItems(["Không", "\\n", "\\r\\n", "\\r"])
        self.eol.setCurrentIndex(1)
        send = QPushButton("Gửi")
        row.addWidget(self.input, 1)
        row.addWidget(self.eol)
        row.addWidget(send)
        lay.addLayout(row)

        opt = QHBoxLayout()
        self.ts_cb = QCheckBox("Dấu thời gian")
        self.scroll_cb = QCheckBox("Tự cuộn")
        self.scroll_cb.setChecked(True)
        clear, save = QPushButton("Xóa"), QPushButton("Lưu log...")
        opt.addWidget(self.ts_cb)
        opt.addWidget(self.scroll_cb)
        opt.addStretch(1)
        opt.addWidget(clear)
        opt.addWidget(save)
        lay.addLayout(opt)

        refresh.clicked.connect(lambda: self.refresh_ports())
        self.open_btn.clicked.connect(self.toggle_port)
        self.reset_btn.clicked.connect(self.reset_board)
        send.clicked.connect(self.send)
        self.input.returnPressed.connect(self.send)
        clear.clicked.connect(self.out.clear)
        save.clicked.connect(self.save_log)
        if self.port is not None:
            self.port.readyRead.connect(self._on_ready)
            self.port.errorOccurred.connect(self._on_error)
        else:
            self.out.setPlainText("PyQt5.QtSerialPort không khả dụng trên máy này.")
            self.open_btn.setEnabled(False)
        self.refresh_ports(win.settings.value("serial/port", ""))

    def refresh_ports(self, keep=""):
        cur = keep or self.port_cb.currentData()
        self.port_cb.clear()
        ports = list_serial_ports()
        for name, label, _esp in ports:
            self.port_cb.addItem(label, name)
        if not ports:
            self.port_cb.addItem("(không thấy cổng nào)", "")
        if cur:
            i = self.port_cb.findData(cur)
            if i >= 0:
                self.port_cb.setCurrentIndex(i)

    def is_open(self):
        return self.port is not None and self.port.isOpen()

    def toggle_port(self):
        if self.is_open():
            self.close_port()
        else:
            self.open_port()

    def open_port(self):
        name = self.port_cb.currentData()
        if not name:
            QMessageBox.information(self, "Serial", "Chưa chọn cổng.")
            return False
        self.port.setPortName(name)
        self.port.setBaudRate(int(self.baud_cb.currentText()))
        self.port.setDataBits(QSerialPort.Data8)
        self.port.setParity(QSerialPort.NoParity)
        self.port.setStopBits(QSerialPort.OneStop)
        self.port.setFlowControl(QSerialPort.NoFlowControl)
        if not self.port.open(QIODevice.ReadWrite):
            self._append(f"[Không mở được {name}: {self.port.errorString()}]\n")
            return False
        s = self.win.settings
        s.setValue("serial/port", name)
        s.setValue("serial/baud", self.baud_cb.currentText())
        self.open_btn.setText("Đóng cổng")
        self._append(f"[Đã mở {name} @ {self.baud_cb.currentText()}]\n")
        return True

    def close_port(self):
        if self.port is not None and self.port.isOpen():
            self.port.close()
            self._append("[Đã đóng cổng]\n")
        self.open_btn.setText("Mở cổng")

    def reset_board(self):
        if not self.is_open():
            return
        p = self.port
        p.setDataTerminalReady(False)
        p.setRequestToSend(True)
        QTimer.singleShot(120, lambda: p.isOpen() and p.setRequestToSend(False))

    def send(self):
        if not self.is_open():
            self._append("[Chưa mở cổng]\n")
            return
        text = self.input.text()
        self.input.push(text)
        self.input.clear()
        eol = {0: "", 1: "\n", 2: "\r\n", 3: "\r"}[self.eol.currentIndex()]
        self.port.write((text + eol).encode("utf-8"))

    def _on_ready(self):
        text = self._decoder.decode(bytes(self.port.readAll()))
        text = text.replace("\r\n", "\n").replace("\r", "")
        for fn in list(self.listeners):
            try:
                fn(text)
            except Exception:  # noqa: BLE001
                pass
        if self.ts_cb.isChecked():
            text = self._stamp(text)
        else:
            self._line_start = text.endswith("\n")
        self._append(text)

    def _stamp(self, text):
        out = []
        for chunk in text.splitlines(True):
            if self._line_start:
                out.append(datetime.datetime.now().strftime("[%H:%M:%S.%f")[:-3] + "] ")
            out.append(chunk)
            self._line_start = chunk.endswith("\n")
        return "".join(out)

    def _append(self, text):
        cur = self.out.textCursor()
        cur.movePosition(QTextCursor.End)
        cur.insertText(text)
        if self.scroll_cb.isChecked():
            self.out.moveCursor(QTextCursor.End)
            self.out.ensureCursorVisible()

    def _on_error(self, err):
        if self.port is None or err == QSerialPort.NoError:
            return
        if err == QSerialPort.ResourceError:
            self._append(f"[Mất kết nối: {self.port.errorString()}]\n")
            self.close_port()

    def save_log(self):
        f, _ = QFileDialog.getSaveFileName(self, "Lưu log", "serial_log.txt", "Text (*.txt)")
        if f:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(self.out.toPlainText())

    def closeEvent(self, e):
        self.close_port()
        super().closeEvent(e)
