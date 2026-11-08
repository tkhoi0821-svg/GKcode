# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


# Mẫu dự án
TEMPLATES = [
    dict(label="Python: script", desc="Một file .py có hàm main()", single=True,
         main="__NAME__.py", files={"__NAME__.py": """def main():
    print("Hello from __NAME__")


if __name__ == "__main__":
    main()
"""}),
    dict(label="Python: ứng dụng PyQt5", desc="Cửa sổ PyQt5 có nút bấm", single=True,
         main="__NAME__.py", files={"__NAME__.py": """import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("__NAME__")
        self.resize(480, 320)
        self.count = 0
        self.label = QLabel("Chưa bấm lần nào")
        self.label.setAlignment(Qt.AlignCenter)
        btn = QPushButton("Bấm tôi")
        btn.clicked.connect(self.on_click)
        box = QVBoxLayout()
        box.addWidget(self.label)
        box.addWidget(btn)
        central = QWidget()
        central.setLayout(box)
        self.setCentralWidget(central)

    def on_click(self):
        self.count += 1
        self.label.setText(f"Đã bấm {self.count} lần")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
"""}),
    dict(label="Python: web server Flask", desc="Flask + requirements.txt", single=False,
         main="app.py", files={"app.py": """from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello from __NAME__"


@app.route("/api/ping")
def ping():
    return jsonify(ok=True)


if __name__ == "__main__":
    # 127.0.0.1: chỉ máy này truy cập được (debugger Flask cho phép chạy code từ xa,
    # đừng mở ra mạng LAN bằng host="0.0.0.0" khi còn debug=True).
    app.run(host="127.0.0.1", port=5000, debug=True)
""", "requirements.txt": "Flask\n"}),
    dict(label="Python: công cụ dòng lệnh (argparse)", desc="CLI có tham số", single=True,
         main="__NAME__.py", files={"__NAME__.py": """import argparse


def main():
    parser = argparse.ArgumentParser(description="__NAME__")
    parser.add_argument("input", help="đầu vào")
    parser.add_argument("-v", "--verbose", action="store_true", help="in chi tiết")
    args = parser.parse_args()
    if args.verbose:
        print("Đang xử lý:", args.input)
    print(args.input)


if __name__ == "__main__":
    main()
"""}),
    dict(label="C: Hello", desc="main.c", single=False, main="main.c",
         files={"main.c": '#include <stdio.h>\n\nint main(void) {\n    printf("Hello from __NAME__\\n");\n    return 0;\n}\n'}),
    dict(label="C++: Hello", desc="main.cpp", single=False, main="main.cpp",
         files={"main.cpp": '#include <iostream>\n\nint main() {\n    std::cout << "Hello from __NAME__" << std::endl;\n    return 0;\n}\n'}),
    dict(label="Go: Hello", desc="main.go", single=False, main="main.go",
         files={"main.go": 'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("Hello from __NAME__")\n}\n'}),
    dict(label="Java: Main", desc="Main.java", single=False, main="Main.java",
         files={"Main.java": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello from __NAME__");\n    }\n}\n'}),
    dict(label="JavaScript: Node", desc="index.js", single=False, main="index.js",
         files={"index.js": 'console.log("Hello from __NAME__");\n'}),
    dict(label="HTML: trang web", desc="index.html + style.css + script.js", single=False,
         main="index.html",
         files={"index.html": '<!DOCTYPE html>\n<html lang="vi">\n<head>\n  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1">\n  <title>__NAME__</title>\n  <link rel="stylesheet" href="style.css">\n</head>\n<body>\n  <h1>__NAME__</h1>\n  <button id="btn">Bấm tôi</button>\n  <script src="script.js"></script>\n</body>\n</html>\n',
                "style.css": "body {\n  font-family: system-ui, sans-serif;\n  margin: 2rem;\n}\n",
                "script.js": 'document.getElementById("btn").addEventListener("click", () => {\n  alert("Xin chào!");\n});\n'}),
    dict(label="ESP32 Arduino: Blink (.ino)", desc="Sketch Arduino nhấp nháy LED + Serial",
         single=False, main="__NAME__.ino",
         files={"__NAME__.ino": """#ifndef LED_BUILTIN
#define LED_BUILTIN 2   // đổi theo board
#endif

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("LED ON");
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("LED OFF");
  delay(500);
}
"""}),
    dict(label="ESP32-S3 PlatformIO: Blink", desc="platformio.ini + src/main.cpp", single=False,
         main="src/main.cpp",
         files={"platformio.ini": """[env:esp32-s3-devkitc-1]
platform = espressif32
board = esp32-s3-devkitc-1   ; LilyGO T-Display S3: lilygo-t-display-s3
framework = arduino
monitor_speed = 115200
build_flags =
    -DARDUINO_USB_CDC_ON_BOOT=1
""", "src/main.cpp": """#include <Arduino.h>

#ifndef LED_BUILTIN
#define LED_BUILTIN 2
#endif

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  Serial.println("tick");
  delay(500);
}
""", ".gitignore": ".pio\n.vscode\n"}),
    dict(label="ESP32 MicroPython: main.py", desc="Nhấp nháy LED bằng MicroPython", single=False,
         main="main.py",
         files={"main.py": """from machine import Pin
import time

led = Pin(2, Pin.OUT)   # đổi số chân theo board

while True:
    led.value(not led.value())
    print("tick")
    time.sleep(0.5)
"""}),
    dict(label="Unity C#: MonoBehaviour", desc="Script Unity cơ bản", single=True,
         main="__CLASS__.cs",
         files={"__CLASS__.cs": """using UnityEngine;

public class __CLASS__ : MonoBehaviour
{
    void Start()
    {
        Debug.Log("__CLASS__ started");
    }

    void Update()
    {
    }
}
"""}),
    dict(label="Unity C#: người chơi góc nhìn thứ nhất (Rigidbody)",
         desc="Di chuyển WASD + nhìn chuột + nhảy (Unity 2022 và Unity 6)", single=True,
         main="__CLASS__.cs",
         files={"__CLASS__.cs": """using UnityEngine;

[RequireComponent(typeof(Rigidbody))]
public class __CLASS__ : MonoBehaviour
{
    public float moveSpeed = 5f;
    public float jumpForce = 5f;
    public float mouseSensitivity = 2f;
    public float groundCheckDistance = 1.1f;   // ~ nửa chiều cao Capsule + chút dung sai
    public Transform cameraTransform;

    Rigidbody rb;
    float pitch;
    bool grounded;

    // Unity 6 đổi Rigidbody.velocity thành linearVelocity
    Vector3 Vel
    {
#if UNITY_6000_0_OR_NEWER
        get { return rb.linearVelocity; }
        set { rb.linearVelocity = value; }
#else
        get { return rb.velocity; }
        set { rb.velocity = value; }
#endif
    }

    void Awake()
    {
        rb = GetComponent<Rigidbody>();
        rb.freezeRotation = true;
        Cursor.lockState = CursorLockMode.Locked;
    }

    void Update()
    {
        transform.Rotate(0f, Input.GetAxis("Mouse X") * mouseSensitivity, 0f);
        pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * mouseSensitivity, -85f, 85f);
        if (cameraTransform != null)
            cameraTransform.localEulerAngles = new Vector3(pitch, 0f, 0f);

        grounded = Physics.Raycast(transform.position, Vector3.down, groundCheckDistance);
        if (Input.GetButtonDown("Jump") && grounded)
            rb.AddForce(Vector3.up * jumpForce, ForceMode.Impulse);
    }

    void FixedUpdate()
    {
        Vector3 dir = (transform.right * Input.GetAxisRaw("Horizontal")
                     + transform.forward * Input.GetAxisRaw("Vertical")).normalized;
        Vector3 v = dir * moveSpeed;
        Vel = new Vector3(v.x, Vel.y, v.z);
    }
}
"""}),
    dict(label="Blender: script bpy", desc="Tạo khối lập phương + keyframe", single=True,
         main="__NAME__.py",
         files={"__NAME__.py": """import bpy

# Xóa mọi object trong scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
cube = bpy.context.active_object
cube.name = "__NAME__"
cube.keyframe_insert(data_path="location", frame=1)
cube.location.z = 3
cube.keyframe_insert(data_path="location", frame=60)
print("Xong:", cube.name)
"""}),
    dict(label="README.md + .gitignore (Python)", desc="Khung tài liệu cho repo mới", single=False,
         main="README.md",
         files={"README.md": "# __NAME__\n\nMô tả dự án.\n\n## Chạy\n\n```\npython main.py\n```\n",
                ".gitignore": "__pycache__/\n*.pyc\n.venv/\ndist/\nbuild/\n*.spec\n_build/\n"}),
]


def make_class_name(name):
    c = re.sub(r"\W", "_", name.strip()) or "NewScript"
    if c[0].isdigit():
        c = "_" + c
    return c[0].upper() + c[1:]


class TemplateDialog(QDialog):
    def __init__(self, parent, default_dir):
        super().__init__(parent)
        self.setWindowTitle("Tạo dự án / file mới từ mẫu")
        self.resize(560, 460)
        lay = QVBoxLayout(self)
        self.list = QListWidget()
        for t in TEMPLATES:
            self.list.addItem(t["label"])
        self.list.setCurrentRow(0)
        lay.addWidget(self.list, 1)
        self.desc = QLabel(TEMPLATES[0]["desc"])
        lay.addWidget(self.desc)
        lay.addWidget(QLabel("Tên:"))
        self.name_edit = QLineEdit("my_project")
        lay.addWidget(self.name_edit)
        lay.addWidget(QLabel("Tạo trong thư mục:"))
        row = QHBoxLayout()
        self.dir_edit = QLineEdit(default_dir)
        b = QPushButton("Chọn...")
        b.clicked.connect(self._browse)
        row.addWidget(self.dir_edit, 1)
        row.addWidget(b)
        lay.addLayout(row)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.list.currentRowChanged.connect(
            lambda i: self.desc.setText(TEMPLATES[i]["desc"] if i >= 0 else ""))
        self.list.itemDoubleClicked.connect(lambda _i: self.accept())

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục", self.dir_edit.text())
        if d:
            self.dir_edit.setText(d)

    def values(self):
        return (self.list.currentRow(), self.name_edit.text().strip(), self.dir_edit.text().strip())


def create_from_template(index, name, parent_dir):
    """Tạo file theo mẫu. Trả về (thư mục dự án, file chính, danh sách file đã tạo, bỏ qua)."""
    t = TEMPLATES[index]
    name = clean_name(name)
    cls = make_class_name(name)
    root = parent_dir if t["single"] else os.path.join(parent_dir, name)
    created, skipped = [], []
    for rel, content in t["files"].items():
        rel = rel.replace("__NAME__", name).replace("__CLASS__", cls)
        content = content.replace("__NAME__", name).replace("__CLASS__", cls)
        path = os.path.join(root, *rel.split("/"))
        if os.path.exists(path):
            skipped.append(path)
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        created.append(path)
    main_rel = t["main"].replace("__NAME__", name).replace("__CLASS__", cls)
    return root, os.path.join(root, *main_rel.split("/")), created, skipped


# Python console tích hợp
class PyConsole(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(5000)
        self.output.setFont(pick_font(10))
        self.input = HistoryLineEdit()
        self.input.setPlaceholderText(">>> gõ lệnh Python (có sẵn: api, win, editor; :reset để làm mới)")
        lay.addWidget(self.output, 1)
        lay.addWidget(self.input)
        self._reset_ns()
        self.output.setPlainText(
            f"Python {sys.version.split()[0]} - console trong {APP_NAME}\n"
            "Biến: api (API của app), win (cửa sổ chính), editor (tab hiện tại)\n"
            "Ví dụ: api.text()[:50]   |   api.message('xin chào')   |   :reset\n")
        self.input.returnPressed.connect(self._submit)
        self.apply_theme(THEMES.get(win.theme_name, THEMES[DEFAULT_THEME]))

    def _reset_ns(self):
        self.ns = {"__name__": "__console__", "win": self.win, "api": self.win.builtin_api,
                   "editor": None}
        self.console = pycode.InteractiveConsole(self.ns)
        self._more = False

    def apply_theme(self, t):
        self.output.setStyleSheet(
            f"QPlainTextEdit {{ background: {t['terminal_bg']}; color: {t['terminal_fg']}; border: none; }}")

    def _submit(self):
        line = self.input.text()
        self.input.push(line)
        self.input.clear()
        if line.strip() == ":reset":
            self._reset_ns()
            self.output.appendPlainText("[Đã làm mới console]")
            return
        self.output.appendPlainText(("... " if self._more else ">>> ") + line)
        self.ns["editor"] = self.win.current_editor()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            self._more = self.console.push(line)
        out = buf.getvalue().rstrip("\n")
        if out:
            self.output.appendPlainText(out)
        self.output.ensureCursorVisible()


# API riêng cho plugin / script
# Chạy nhiều ngôn ngữ (polyglot) - plugin dùng để kết hợp Python với C, Go, ...
POLY_LANGS = ("python", "c", "cpp", "go", "java", "javascript", "rust")
POLY_EXT = {"python": ".py", "c": ".c", "cpp": ".cpp", "go": ".go", "java": ".java",
            "javascript": ".js", "rust": ".rs"}
