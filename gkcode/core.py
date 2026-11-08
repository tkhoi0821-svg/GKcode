# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


def _atomic_write_bytes(path, data):
    real = os.path.realpath(path)
    folder = os.path.dirname(real) or "."
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=".gk_", suffix=".tmp", dir=folder)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(real):
            try:
                shutil.copymode(real, tmp)
            except OSError:
                pass
        os.replace(tmp, real)
        tmp = None
    except OSError:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        with open(path, "wb") as f:
            f.write(data)


# Ngôn ngữ / công cụ
CFG.PY_OVERRIDE = ""      # đường dẫn python do người dùng chọn (Preferences)


def get_python_command():
   
    
    if CFG.PY_OVERRIDE and os.path.isfile(CFG.PY_OVERRIDE):
        return [CFG.PY_OVERRIDE]
    if not getattr(sys, "frozen", False):
        return [sys.executable]
    py_launcher = shutil.which("py")
    if py_launcher:
        return [py_launcher, "-3"]
    for name in ("python", "python3"):
        p = shutil.which(name)
        if p:
            return [p]
    return None


def find_tool(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


EXE_EXT = ".exe" if os.name == "nt" else ""

#  Trình biên dịch C / C++ (chọn trong Tools > Trình biên dịch C/C++)
CFG.C_COMPILER = ""          # đường dẫn do người dùng chọn ("" = tự dò trong PATH)
CFG.C_FLAGS = "-Wall"        # cờ thêm cho C
CFG.CPP_FLAGS = "-Wall"      # cờ thêm cho C++
NO_CC_MSG = ("Chưa có trình biên dịch C/C++.\nMở Tools → Trình biên dịch C/C++... để chọn "
             "hoặc xem cách cài (GCC / MinGW-w64, Clang, TinyCC).")


def split_flags(text):
    try:
        return shlex.split(text or "", posix=(os.name != "nt"))
    except ValueError:
        return (text or "").split()


def get_c_compiler(cpp=False):
    if CFG.C_COMPILER and os.path.isfile(CFG.C_COMPILER):
        if not cpp:
            return CFG.C_COMPILER
        d, b = os.path.split(CFG.C_COMPILER)
        stem = os.path.splitext(b)[0]
        low = stem.lower()
        sibling = None
        if low.endswith("gcc"):
            sibling = stem[:-3] + "g++"
        elif low.endswith("clang"):
            sibling = stem + "++"
        elif low == "cc":
            sibling = "c++"
        if sibling:
            p = os.path.join(d, sibling + EXE_EXT)
            if os.path.isfile(p):
                return p
            p = find_tool(sibling)
            if p:
                return p
    names = ("g++", "clang++", "c++") if cpp else ("gcc", "clang", "cc", "tcc")
    return find_tool(*names)


def detect_c_compilers():
    """[(tên, đường dẫn)] các trình biên dịch C tìm thấy trong PATH."""
    out = []
    for n in ("gcc", "clang", "cc", "tcc"):
        p = shutil.which(n)
        if p and p not in [x[1] for x in out]:
            out.append((n, p))
    return out


def cc_flag_list(cpp=False):
    return split_flags(CFG.CPP_FLAGS if cpp else CFG.C_FLAGS)


def cc_args(cc, cpp, src, out, opt=False):
    """Tham số gọi trình biên dịch: nguồn + cờ người dùng + -o out (+ -lm cho C trên Linux/macOS)."""
    args = [src] + (["-O2"] if opt else []) + cc_flag_list(cpp) + ["-o", out]
    if not cpp and os.name != "nt" and "tcc" not in os.path.basename(cc).lower():
        args.append("-lm")
    return args


def compiler_version(path):
    for flag in ("--version", "-v"):
        code, out, err = run_capture([path, flag], 10)
        text = (out or err).strip()
        if text:
            return text.splitlines()[0]
    return "(không đọc được phiên bản)"

EXT_TO_LANG = {
    ".py": "python", ".pyw": "python",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    ".go": "go",
    ".java": "java",
    ".js": "javascript", ".mjs": "javascript",
    ".json": "json",
    ".ino": "arduino", ".pde": "arduino",
}
TEXT_EXTS = set(EXT_TO_LANG) | {
    ".txt", ".md", ".html", ".css", ".xml", ".yaml", ".yml", ".ini", ".cfg",
    ".toml", ".csv", ".bat", ".sh", ".ino", ".cs", ".rs", ".ts", ".log",
}
RUNNABLE = {"python", "c", "cpp", "go", "java", "javascript"}
RUN_TEMPLATES = {}      # ngôn ngữ do plugin đăng ký: {lang: {"steps": [...], "need": [...]}}

LANGUAGE_LABELS = {
    "python": "Python", "c": "C", "cpp": "C++", "go": "Go", "java": "Java",
    "javascript": "JavaScript (Node.js)", "json": "JSON", "arduino": "Arduino / ESP (.ino)",
    None: "Văn bản",
}


LANG_EXT = {"python": ".py", "c": ".c", "cpp": ".cpp", "go": ".go",
            "java": ".java", "javascript": ".js", "arduino": ".ino"}

# Snippet: gõ từ khóa rồi nhấn Tab. $0 = vị trí con trỏ sau khi chèn.
SNIPPETS = {
    "python": {
        "ifmain": 'if __name__ == "__main__":\n    main()$0',
        "defn": "def $0():\n    pass",
        "cls": "class $0:\n    def __init__(self):\n        pass",
        "forr": "for i in range($0):\n    pass",
        "tryx": "try:\n    $0\nexcept Exception as e:\n    print(e)",
        "wopen": 'with open("$0", "r", encoding="utf-8") as f:\n    data = f.read()',
    },
    "c": {
        "main": "#include <stdio.h>\n\nint main(void) {\n    $0\n    return 0;\n}",
        "forr": "for (int i = 0; i < $0; i++) {\n    \n}",
    },
    "cpp": {
        "main": "#include <iostream>\n\nint main() {\n    $0\n    return 0;\n}",
        "forr": "for (int i = 0; i < $0; i++) {\n    \n}",
    },
    "go": {
        "main": 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("$0")\n}',
    },
    "java": {
        "main": "public class Main {\n    public static void main(String[] args) {\n        $0\n    }\n}",
        "psvm": "public static void main(String[] args) {\n    $0\n}",
        "sout": "System.out.println($0);",
    },
    "javascript": {
        "log": "console.log($0);",
        "fn": "function $0() {\n    \n}",
    },
    "arduino": {
        "sketch": "void setup() {\n    $0\n}\n\nvoid loop() {\n    \n}",
        "setup": "void setup() {\n    $0\n}",
        "loop": "void loop() {\n    $0\n}",
        "pm": "pinMode($0, OUTPUT);",
        "dw": "digitalWrite($0, HIGH);",
        "dr": "int v = digitalRead($0);",
        "ser": "Serial.begin(115200);$0",
        "sp": "Serial.println($0);",
        "blink": "digitalWrite(LED_BUILTIN, HIGH);\n    delay(500);\n    digitalWrite(LED_BUILTIN, LOW);\n    delay(500);$0",
        "forr": "for (int i = 0; i < $0; i++) {\n    \n}",
    },
}

OUTLINE_GENERIC = re.compile(
    r"^\s*(?:async\s+def|def|class|func|function|struct|interface|enum)\s+([A-Za-z_]\w*)")
OUTLINE_CFUNC = re.compile(
    r"^\s*(?:[\w:<>\*&~]+\s+)+[\*&]*([A-Za-z_~]\w*)\s*\(")
OUTLINE_SKIP = {"if", "for", "while", "switch", "return", "else", "catch", "sizeof",
                "new", "delete", "throw", "case"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", "dist", "build", ".venv",
             "venv", "_build", ".idea", ".vscode", ".mypy_cache"}


NAME_TO_LANG = {}       # tên file đặc biệt (Dockerfile, Makefile...) -> ngôn ngữ


def get_language(file_path):
    if not file_path:
        return None
    name = os.path.basename(file_path).lower()
    if name in NAME_TO_LANG:
        return NAME_TO_LANG[name]
    return EXT_TO_LANG.get(os.path.splitext(file_path)[1].lower())


def read_text_file(path):
    """Đọc file text; trả về None nếu là file nhị phân."""
    with open(path, "rb") as f:
        data = f.read()
    if b"\0" in data[:8192]:
        return None
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode(locale.getpreferredencoding(False) or "latin-1",
                       errors="replace")


def detect_eol(text):
    crlf = text.count("\r\n")
    counts = [(text.count("\n") - crlf, "\n"), (crlf, "\r\n"), (text.count("\r") - crlf, "\r")]
    best = max(counts, key=lambda x: x[0])
    return best[1] if best[0] > 0 else "\n"


def read_text_file_ex(path):
    """Đọc file text -> (nội dung, mã hóa, EOL) hoặc None nếu là nhị phân.
    Nhớ mã hóa và EOL gốc để lưu lại đúng như cũ (không tự đổi CRLF -> LF, mất BOM...)."""
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith(codecs.BOM_UTF8):
        enc = "utf-8-sig"
    elif data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        enc = "utf-16"
    else:
        if b"\0" in data[:8192]:
            return None
        try:
            data.decode("utf-8")
            enc = "utf-8"
        except UnicodeDecodeError:
            enc = (locale.getpreferredencoding(False) or "latin-1").lower()
            if enc.replace("-", "").replace("_", "") in ("utf8", "ascii", "usascii"):
                enc = "latin-1"      # latin-1 đọc/ghi lại không mất byte nào
    try:
        text = data.decode(enc)
    except (UnicodeDecodeError, LookupError):
        enc, text = "latin-1", data.decode("latin-1")
    eol = detect_eol(text)
    return text.replace("\r\n", "\n").replace("\r", "\n"), enc, eol


def get_run_steps(file_path, lang, py_cmd):
    """Trả về (steps, error, cleanup_paths) cho nút Run (F5)."""
    base = os.path.splitext(os.path.basename(file_path))[0]
    workdir = os.path.dirname(file_path) or "."
    tmp_exe = os.path.join(workdir, f"_run_{base}{EXE_EXT}")

    tpl = RUN_TEMPLATES.get(lang)
    if tpl:
        ph = {"file": file_path, "dir": workdir, "base": base, "exe": tmp_exe}
        steps, used_exe = [], False
        for label, prog, args in tpl["steps"]:
            exe = prog.format(**ph) if "{" in prog else prog
            full = exe if os.path.isabs(exe) else find_tool(exe)
            if not full:
                return None, f"Chưa cài '{exe}' (cần để chạy {lang}).", []
            a = [x.format(**ph) for x in args]
            used_exe = used_exe or any("{exe}" in x for x in list(args) + [prog])
            steps.append((label, full, a))
        return steps, None, ([tmp_exe] if used_exe else [])
    if lang == "python":
        return [("Đang chạy", py_cmd[0], py_cmd[1:] + ["-u", file_path])], None, []
    if lang in ("c", "cpp"):
        cc = get_c_compiler(lang == "cpp")
        if not cc:
            return None, NO_CC_MSG, []
        return [(f"Biên dịch ({os.path.basename(cc)})", cc,
                 cc_args(cc, lang == "cpp", file_path, tmp_exe)),
                ("Chạy chương trình", tmp_exe, [])], None, [tmp_exe]
    if lang == "go":
        go = find_tool("go")
        if not go:
            return None, "Chưa cài Go. Tải tại https://go.dev/dl/", []
        return [("Chạy (go run)", go, ["run", file_path])], None, []
    if lang == "java":
        javac, java = find_tool("javac"), find_tool("java")
        if not javac or not java:
            return None, "Chưa cài JDK (javac/java). Hãy cài Java JDK.", []
        return [("Biên dịch (javac)", javac, [file_path]),
                ("Chạy (java)", java, ["-cp", workdir, base])], None, []
    if lang == "javascript":
        node = find_tool("node")
        if not node:
            return None, "Chưa cài Node.js. Tải tại https://nodejs.org/", []
        return [("Chạy (node)", node, [file_path])], None, []
    return None, "Chưa hỗ trợ chạy loại file này.", []


def get_build_steps(file_path, name, out_dir, lang, py_cmd, packages):
    """Trả về (steps, output_hint, error, cleanup_paths) cho nút Build (F6)."""
    if lang == "python":
        steps = [("Kiểm tra / cài PyInstaller", py_cmd[0],
                  py_cmd[1:] + ["-m", "pip", "install",
                                "--disable-pip-version-check", "pyinstaller"])]
        if packages:
            steps.append(("Cài thư viện code sử dụng", py_cmd[0],
                          py_cmd[1:] + ["-m", "pip", "install",
                                        "--disable-pip-version-check"] + packages))
        return steps, f"{name}.exe", None, []

    exe = os.path.join(out_dir, name + EXE_EXT)
    if lang in ("c", "cpp"):
        cc = get_c_compiler(lang == "cpp")
        if not cc:
            return None, None, NO_CC_MSG, []
        return [(f"Biên dịch EXE ({os.path.basename(cc)})", cc,
                 cc_args(cc, lang == "cpp", file_path, exe, opt=True))], \
            os.path.basename(exe), None, []
    if lang == "go":
        go = find_tool("go")
        if not go:
            return None, None, "Chưa cài Go. Tải tại https://go.dev/dl/", []
        return [("Build EXE (go build)", go, ["build", "-o", exe, file_path])], \
            os.path.basename(exe), None, []
    if lang == "java":
        javac, jar = find_tool("javac"), find_tool("jar")
        if not javac or not jar:
            return None, None, "Chưa cài JDK đầy đủ (javac/jar).", []
        classdir = os.path.join(out_dir, f"_classes_{name}")
        jarpath = os.path.join(out_dir, name + ".jar")
        main_cls = os.path.splitext(os.path.basename(file_path))[0]
        return [("Biên dịch (javac)", javac, ["-d", classdir, file_path]),
                ("Đóng gói (jar)", jar,
                 ["cfe", jarpath, main_cls, "-C", classdir, "."])], \
            f"{name}.jar (chạy bằng: java -jar {name}.jar)", None, [classdir]
    if lang == "javascript":
        return None, None, (
            "JavaScript/Node không thể đóng gói trực tiếp thành .exe bằng công "
            "cụ này. Bạn có thể chạy thử bằng F5, hoặc dùng 'pkg' "
            "(npm i -g pkg) để đóng gói Node thành exe."), []
    return None, None, "Chưa hỗ trợ build EXE cho loại file này.", []


# import-name -> pip-package-name
PIP_NAME_MAP = {
    "cv2": "opencv-python", "PIL": "Pillow", "sklearn": "scikit-learn",
    "skimage": "scikit-image", "bs4": "beautifulsoup4", "yaml": "PyYAML",
    "dotenv": "python-dotenv", "Crypto": "pycryptodome", "serial": "pyserial",
    "win32com": "pywin32", "win32api": "pywin32", "win32gui": "pywin32",
    "docx": "python-docx", "pptx": "python-pptx", "telebot": "pyTelegramBotAPI",
    "discord": "discord.py", "flask": "Flask", "django": "Django",
    "attr": "attrs", "jwt": "PyJWT", "magic": "python-magic", "usb": "pyusb",
    "git": "GitPython", "dateutil": "python-dateutil", "fitz": "PyMuPDF",
    "psycopg2": "psycopg2-binary", "MySQLdb": "mysqlclient", "zmq": "pyzmq",
    "OpenGL": "PyOpenGL", "wx": "wxPython", "Xlib": "python-xlib",
    "serial_asyncio": "pyserial-asyncio", "esptool": "esptool",
}

STDLIB_FALLBACK = set(sys.builtin_module_names) | {
    "os", "sys", "re", "math", "json", "time", "datetime", "random",
    "itertools", "functools", "collections", "subprocess", "threading",
    "multiprocessing", "socket", "http", "urllib", "pathlib", "shutil", "glob",
    "csv", "sqlite3", "logging", "argparse", "typing", "enum", "abc", "copy",
    "io", "string", "traceback", "unittest", "asyncio", "queue", "hashlib",
    "base64", "struct", "pickle", "tkinter", "xml", "email", "ctypes",
    "platform", "getpass", "tempfile", "zipfile", "tarfile", "gzip",
    "configparser", "dataclasses", "locale", "ast", "importlib", "inspect",
    "contextlib", "operator", "statistics", "decimal", "fractions", "secrets",
    "signal", "select", "ssl", "textwrap", "uuid", "warnings", "weakref",
    "zlib", "bisect", "heapq", "array", "codecs", "html", "webbrowser",
}
try:
    STDLIB_FALLBACK |= set(sys.stdlib_module_names)  # py3.10+
except AttributeError:
    pass


def detect_third_party_imports(source_code, local_dir=None):
    """Trả về danh sách tên gói pip cần cài (bỏ thư viện chuẩn + module cục bộ)."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                modules.add(node.module.split(".")[0])

    result, seen = [], set()
    for m in sorted(modules):
        if m in STDLIB_FALLBACK:
            continue
        if local_dir and (os.path.exists(os.path.join(local_dir, m + ".py"))
                          or os.path.isdir(os.path.join(local_dir, m))):
            continue
        pkg = PIP_NAME_MAP.get(m, m)
        if pkg not in seen:
            seen.add(pkg)
            result.append(pkg)
    return result
