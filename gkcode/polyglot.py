# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp', 'templates']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


def polyglot_available(lang):
    if lang == "python":
        return get_python_command() is not None
    if lang == "c":
        return bool(get_c_compiler(False))
    if lang == "cpp":
        return bool(get_c_compiler(True))
    need = {"c": ("gcc",), "cpp": ("g++",), "go": ("go",), "java": ("javac", "java"),
            "javascript": ("node",), "rust": ("rustc",)}.get(lang)
    return bool(need) and all(find_tool(n) for n in need)


def _write_extra_files(tmp, files):
    """Ghi các file phụ ({đường_dẫn_tương_đối: nội_dung}) vào thư mục tạm. Trả về danh sách path."""
    out = []
    for rel, content in (files or {}).items():
        rel = str(rel).replace("\\", "/")
        if os.path.isabs(rel) or ".." in rel.split("/") or not rel:
            raise ValueError(f"Đường dẫn file phụ không hợp lệ: {rel}")
        p = os.path.join(tmp, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        out.append(p)
    return out


def run_polyglot(lang, source, stdin_text="", args=(), timeout=60, files=None):
    """Biên dịch (nếu cần) rồi chạy `source`. `files` = file phụ (header, module...) cùng thư mục.
    Trả về (mã thoát, stdout, stderr)."""
    if lang not in POLY_LANGS:
        return -1, "", f"Ngôn ngữ chưa hỗ trợ: {lang}"
    if not polyglot_available(lang):
        return -1, "", f"Máy chưa có công cụ để chạy {lang} (gcc / g++ / go / javac / node / rustc)."
    tmp = tempfile.mkdtemp(prefix="pyapp_poly_")
    try:
        cls = "Main"
        if lang == "java":
            m = re.search(r"public\s+(?:final\s+)?class\s+(\w+)", source)
            cls = m.group(1) if m else "Main"
            src = os.path.join(tmp, cls + ".java")
        else:
            src = os.path.join(tmp, "main" + POLY_EXT[lang])
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(source)
        try:
            extra = _write_extra_files(tmp, files)
        except (ValueError, OSError) as e:
            return -1, "", str(e)
        same = [p for p in extra if p.endswith(POLY_EXT[lang])
                or (lang == "cpp" and p.endswith((".cc", ".cxx")))]
        exe = os.path.join(tmp, "prog" + EXE_EXT)
        build = None
        if lang == "python":
            cmd = get_python_command() + ["-u", src]
        elif lang == "c":
            build = [get_c_compiler(False), src] + same + ["-O2", "-o", exe, "-lm"]
            cmd = [exe]
        elif lang == "cpp":
            build = [get_c_compiler(True), src] + same + ["-O2", "-o", exe]
            cmd = [exe]
        elif lang == "go":
            build = [find_tool("go"), "build", "-o", exe, src] + same
            cmd = [exe]
        elif lang == "rust":
            build = [find_tool("rustc"), src, "-O", "-o", exe]
            cmd = [exe]
        elif lang == "java":
            build = [find_tool("javac"), src] + same
            cmd = [find_tool("java"), "-cp", tmp, cls]
        else:  # javascript
            cmd = [find_tool("node"), src]
        if build:
            code, out, err = run_capture(build, timeout, tmp)
            if code != 0:
                return code, out, err
        try:
            r = subprocess.run(cmd + [str(a) for a in args],
                               input=(stdin_text or "").encode("utf-8"),
                               capture_output=True, timeout=timeout, cwd=tmp,
                               creationflags=NO_WINDOW)
        except (OSError, subprocess.TimeoutExpired) as e:
            return -1, "", str(e)
        return r.returncode, decode_output(r.stdout), decode_output(r.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


#  gọi C trực tiếp trong tiến trình (ctypes)
_C_LIB_CACHE = {}
_CT_NAMES = {"int": "c_int", "uint": "c_uint", "long": "c_long", "longlong": "c_longlong",
             "size_t": "c_size_t", "float": "c_float", "double": "c_double", "bool": "c_bool",
             "char": "c_char", "str": "c_char_p", "bytes": "c_char_p", "ptr": "c_void_p",
             "void": None, "None": None}


def build_c_library(code, flags=(), cpp=False):
    """Biên dịch `code` (C/C++) thành thư viện dùng chung (có cache) và nạp bằng ctypes.CDLL.
    Lưu ý: chạy cùng tiến trình với app - lỗi con trỏ trong C có thể làm app thoát đột ngột."""
    import ctypes
    cc = get_c_compiler(cpp)
    if not cc:
        raise RuntimeError("Chưa cài trình biên dịch C/C++ (gcc / clang).")
    key = hashlib.sha256((("cpp:" if cpp else "c:") + code + "|" + " ".join(flags)).encode(
        "utf-8")).hexdigest()[:20]
    if key in _C_LIB_CACHE:
        return _C_LIB_CACHE[key]
    d = os.path.join(tempfile.gettempdir(), "pyapp_clib")
    os.makedirs(d, exist_ok=True)
    ext = ".dll" if os.name == "nt" else (".dylib" if sys.platform == "darwin" else ".so")
    lib = os.path.join(d, key + ext)
    if not os.path.exists(lib):
        src = os.path.join(d, key + (".cpp" if cpp else ".c"))
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        cmd = [cc, "-shared", "-O2", src, "-o", lib] + list(flags)
        if os.name != "nt":
            cmd.insert(2, "-fPIC")
        if not cpp:
            cmd.append("-lm")
        rc, out, err = run_capture(cmd, 120, d)
        if rc != 0 or not os.path.exists(lib):
            raise RuntimeError("Biên dịch C lỗi:\n" + (err or out))
    _C_LIB_CACHE[key] = ctypes.CDLL(lib)
    return _C_LIB_CACHE[key]


def call_c_function(code, func, args=(), restype="int", argtypes=None, flags=(), cpp=False):
    """Gọi hàm `func` trong `code` C. Kiểu: int, uint, long, size_t, float, double, bool, str,
    ptr, void; thêm "[]" cho mảng số (vd "double[]", ảo thành con trỏ; mảng được sửa tại chỗ
    và trả về trong `out_arrays`). Trả về (giá_trị, [mảng_sau_gọi])."""
    import ctypes
    lib = build_c_library(code, flags, cpp)
    fn = getattr(lib, func)

    def ct(name):
        if name.endswith("[]"):
            base = _CT_NAMES.get(name[:-2])
            if base is None:
                raise ValueError("Kiểu mảng không hợp lệ: " + name)
            return ctypes.POINTER(getattr(ctypes, base))
        if name not in _CT_NAMES:
            raise ValueError("Kiểu không hỗ trợ: " + name)
        n = _CT_NAMES[name]
        return None if n is None else getattr(ctypes, n)

    args = list(args)
    argtypes = list(argtypes) if argtypes else [
        "double[]" if isinstance(a, (list, tuple)) and a and isinstance(a[0], float)
        else "int[]" if isinstance(a, (list, tuple))
        else "double" if isinstance(a, float) else "str" if isinstance(a, (str, bytes))
        else "int" for a in args]
    if len(argtypes) != len(args):
        raise ValueError("Số kiểu tham số khác số tham số")
    fn.restype = ct(restype)
    fn.argtypes = [ct(t) for t in argtypes]
    conv, arrays = [], []
    for a, t in zip(args, argtypes):
        if t.endswith("[]"):
            elem = getattr(ctypes, _CT_NAMES[t[:-2]])
            arr = (elem * max(1, len(a)))(*a)
            arrays.append(arr)
            conv.append(arr)
        elif t in ("str", "bytes") and isinstance(a, str):
            conv.append(a.encode("utf-8"))
        else:
            conv.append(a)
    res = fn(*conv)
    if isinstance(res, bytes):
        res = res.decode("utf-8", "replace")
    return res, [list(a) for a in arrays]


class FuncThread(QThread):
    """Chạy một hàm ở nền, trả kết quả qua tín hiệu done."""
    done = pyqtSignal(object)

    def __init__(self, fn, *args, parent=None):
        super().__init__(parent)
        self.fn, self.args = fn, args

    def run(self):
        try:
            res = self.fn(*self.args)
        except Exception as e:  # noqa: BLE001
            res = (-1, "", f"{type(e).__name__}: {e}")
        self.done.emit(res)


# Vẽ code thành ảnh (có tô màu cú pháp)
def render_code_to_image(code, lang=None, theme_key="tim_huyen", title="", font_size=13,
                         scale=2.0, line_numbers=True, chrome=True, max_lines=400):
    """Trả về QImage chứa code đã tô màu theo theme."""
    t = THEMES.get(theme_key, THEMES[DEFAULT_THEME])
    lines = code.replace("\r\n", "\n").expandtabs(4).split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        lines = [""]
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["... (đã cắt bớt)"]
    font = pick_font(font_size)
    fm = QFontMetrics(font)

    def make_doc(right=False):
        d = QTextDocument()
        d.setDocumentMargin(0)
        d.setDefaultFont(font)
        o = QTextOption()
        o.setWrapMode(QTextOption.NoWrap)
        if right:
            o.setAlignment(Qt.AlignRight)
        d.setDefaultTextOption(o)
        return d

    cdoc = make_doc()
    CodeHighlighter(cdoc, t, lang)
    cdoc.setPlainText("\n".join(lines))
    code_w = max(280, int(math.ceil(cdoc.idealWidth())) + 2)
    code_h = int(math.ceil(cdoc.size().height()))

    nw = fm.horizontalAdvance("9") * len(str(len(lines))) if line_numbers else 0
    ndoc = None
    if line_numbers:
        ndoc = make_doc(True)
        ndoc.setPlainText("\n".join(str(i) for i in range(1, len(lines) + 1)))
        ndoc.setTextWidth(nw)
    gap = 18 if line_numbers else 0
    pad = 26
    bar = 38 if chrome else 0
    margin = 36 if chrome else 0
    W = max(340, pad * 2 + nw + gap + code_w)
    H = pad * 2 + bar + code_h
    tw, th = W + margin * 2, H + margin * 2

    img = QImage(int(tw * scale), int(th * scale), QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    p.scale(scale, scale)
    if chrome:
        grad = QLinearGradient(0, 0, tw, th)
        grad.setColorAt(0, QColor(t["accent"]))
        grad.setColorAt(1, QColor(t["gutter_bg"]).darker(170))
        p.fillRect(QRectF(0, 0, tw, th), QBrush(grad))
        p.setPen(Qt.NoPen)
        for i in range(8):
            p.setBrush(QColor(0, 0, 0, 12))
            p.drawRoundedRect(QRectF(margin - i, margin + 10 - i, W + 2 * i, H + 2 * i),
                              12 + i, 12 + i)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(t["bg"]))
    p.drawRoundedRect(QRectF(margin, margin, W, H), 12, 12)
    if chrome:
        for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
            p.setBrush(QColor(c))
            p.drawEllipse(QPointF(margin + 22 + i * 22, margin + bar / 2.0), 6, 6)
        if title:
            p.setPen(QColor(t["gutter_fg"]))
            p.setFont(font)
            p.drawText(QRectF(margin, margin, W, bar), Qt.AlignCenter, title)

    def draw(doc, x, y, color):
        ctx = QAbstractTextDocumentLayout.PaintContext()
        pal = QPalette()
        pal.setColor(QPalette.Text, QColor(color))
        ctx.palette = pal
        p.save()
        p.translate(x, y)
        doc.documentLayout().draw(p, ctx)
        p.restore()

    x0, y0 = margin + pad, margin + bar + pad
    if ndoc is not None:
        draw(ndoc, x0, y0, t["gutter_fg"])
    draw(cdoc, x0 + nw + gap, y0, t["fg"])
    p.end()
    return img


# Plugin mặc định (cài vào ~/.pyapp/plugins ở lần chạy đầu)
PLUGIN_CODE_TO_IMAGE = r'''# pyapp-default-plugin v3.1 (file này do app tạo; sửa tay rồi thì app sẽ không ghi đè)
# Plugin mặc định: Code → Ảnh
# Xuất đoạn code (đang chọn, hoặc cả file) thành ảnh PNG có tô màu cú pháp.
# Phần vẽ do app đảm nhiệm bằng Qt (api.code_to_image); plugin lo giao diện.
import os

THEME_KEYS = ["tim_huyen", "dark", "than_dem", "bang_gia", "bien_dem", "light"]


def register(api):
    def source():
        sel = api.selection()
        return sel if sel.strip() else api.text()

    def make(chrome=True):
        code = source()
        if not code.strip():
            api.status("Không có code để xuất")
            return None
        key = api.choose("Chọn theme cho ảnh", THEME_KEYS, 0)
        if not key:
            return None
        title = os.path.basename(api.file_path() or "untitled")
        try:
            return api.code_to_image(code, api.language(), theme=key,
                                     title=title, chrome=chrome)
        except Exception as e:
            api.error("Không tạo được ảnh: " + str(e))
            return None

    def to_png(chrome=True):
        img = make(chrome)
        if img is None:
            return
        path = api.pick_file(save=True, filter="PNG (*.png)", title="Lưu ảnh code")
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        if img.save(path):
            api.status("Đã lưu ảnh: " + path, 5000)
            api.log("[code_to_image] đã lưu", path)
            api.open_folder(path)
        else:
            api.error("Không ghi được file ảnh:\n" + path)

    def to_clipboard():
        img = make(True)
        if img is not None:
            api.copy_image(img)
            api.status("Đã chép ảnh vào clipboard", 4000)

    api.add_separator("Plugins")
    api.add_action("Code → Ảnh PNG (có khung cửa sổ)...", lambda: to_png(True),
                   shortcut="Ctrl+Alt+I", menu="Plugins")
    api.add_action("Code → Ảnh PNG (không khung)...", lambda: to_png(False), menu="Plugins")
    api.add_action("Code → Ảnh → clipboard", to_clipboard, menu="Plugins")
'''

PLUGIN_CODE_TO_3D = r'''# pyapp-default-plugin v3.1 (file này do app tạo; sửa tay rồi thì app sẽ không ghi đè)
# Plugin mặc định: Code → 3D ("Code City")
# Python phân tích code -> chương trình C (biên dịch bằng gcc) dựng mô hình 3D
# dạng OBJ -> Python vẽ lại và cho xoay / zoom. Không có gcc thì tự dùng Python.
#   chiều cao tòa nhà = số dòng của hàm, độ rộng + màu = độ phức tạp, xanh dương = class
import ast
import math
import re

from PyQt5.QtCore import Qt, QPointF, QTimer
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

C_SOURCE = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAXN 2000

typedef struct {
    int kind, lines, cx;
    char name[96];
} Item;

static Item items[MAXN];

static void vtx(double x, double y, double z) { printf("v %.3f %.3f %.3f\n", x, y, z); }
static void quad(int a, int b, int c, int d) { printf("f %d %d %d %d\n", a, b, c, d); }

static void color_for(const Item *it, double *r, double *g, double *b) {
    if (it->kind == 1) { *r = 0.30; *g = 0.55; *b = 0.95; return; }
    double t = it->cx / 15.0;
    if (t > 1.0) t = 1.0;
    *r = 0.25 + 0.70 * t;
    *g = 0.85 - 0.60 * t;
    *b = 0.30;
}

int main(void) {
    char line[512];
    int n = 0;
    while (n < MAXN && fgets(line, sizeof line, stdin)) {
        Item *it = &items[n];
        char nm[96] = "";
        if (sscanf(line, "%d %d %d %95[^\n]", &it->kind, &it->lines, &it->cx, nm) >= 3) {
            if (nm[0] == '\0') strcpy(nm, "item");
            for (char *p = nm; *p; p++)
                if (*p == ' ' || *p == '\t' || *p == '\r') *p = '_';
            strcpy(it->name, nm);
            n++;
        }
    }
    if (n == 0) { fprintf(stderr, "khong co du lieu\n"); return 2; }

    int cols = (int)ceil(sqrt((double)n));
    int rows = (n + cols - 1) / cols;
    const double cell = 3.0;
    double gx = cols * cell + 1.0, gz = rows * cell + 1.0;
    int vb = 1;

    printf("# code city: %d khoi\n", n);
    printf("o ground\n# color 0.16 0.17 0.20\n");
    vtx(-1.0, 0.0, -1.0); vtx(gx, 0.0, -1.0); vtx(gx, 0.0, gz); vtx(-1.0, 0.0, gz);
    quad(vb, vb + 1, vb + 2, vb + 3);
    vb += 4;

    for (int i = 0; i < n; i++) {
        const Item *it = &items[i];
        int c = i % cols, r = i / cols;
        int k = it->cx > 20 ? 20 : it->cx;
        double w = 0.9 + 0.12 * k + (it->kind == 1 ? 0.4 : 0.0);
        if (w > 2.7) w = 2.7;
        double h = 0.4 + 0.45 * pow((double)(it->lines > 0 ? it->lines : 1), 0.75);
        double x0 = c * cell + (cell - w) / 2.0, z0 = r * cell + (cell - w) / 2.0;
        double x1 = x0 + w, z1 = z0 + w;
        double cr, cg, cb;
        color_for(it, &cr, &cg, &cb);
        printf("o %s\n# color %.3f %.3f %.3f\n", it->name, cr, cg, cb);
        printf("# info dong=%d, do_phuc_tap=%d\n", it->lines, it->cx);
        vtx(x0, 0.0, z0); vtx(x1, 0.0, z0); vtx(x1, 0.0, z1); vtx(x0, 0.0, z1);
        vtx(x0, h, z0); vtx(x1, h, z0); vtx(x1, h, z1); vtx(x0, h, z1);
        quad(vb + 4, vb + 5, vb + 6, vb + 7);
        quad(vb, vb + 1, vb + 5, vb + 4);
        quad(vb + 3, vb + 2, vb + 6, vb + 7);
        quad(vb, vb + 3, vb + 7, vb + 4);
        quad(vb + 1, vb + 2, vb + 6, vb + 5);
        vb += 8;
    }
    return 0;
}
"""

BRANCH = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.ExceptHandler,
          ast.IfExp, ast.BoolOp, ast.comprehension, ast.Assert)
FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)
MAX_ITEMS = 400


#  phân tích code
def _span(node):
    return getattr(node, "end_lineno", node.lineno) - node.lineno + 1


def analyze_python(tree):
    items = []

    def visit(node, prefix):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, FUNCS):
                cx = 1 + sum(isinstance(n, BRANCH) for n in ast.walk(ch))
                items.append((0, _span(ch), cx, prefix + ch.name))
                visit(ch, prefix + ch.name + ".")
            elif isinstance(ch, ast.ClassDef):
                methods = sum(isinstance(c, FUNCS) for c in ch.body)
                items.append((1, _span(ch), max(1, methods), prefix + ch.name))
                visit(ch, prefix + ch.name + ".")
            else:
                visit(ch, prefix)

    visit(tree, "")
    return items


CLASS_RE = re.compile(
    r"^\s*(?:(?:public|private|protected|static|abstract|final|export)\s+)*"
    r"(?:class|struct|interface|enum)\b")
BRANCH_RE = re.compile(r"\b(?:if|for|while|case|catch|elif|switch)\b|&&|\|\||\?")


def analyze_generic(api, text, lang):
    lines = text.split("\n")
    outline = api.outline(text, lang)
    items = []
    for i, (ln, name) in enumerate(outline):
        end = outline[i + 1][0] - 1 if i + 1 < len(outline) else len(lines)
        body = "\n".join(lines[ln - 1:end])
        cx = 1 + len(BRANCH_RE.findall(body))
        kind = 1 if CLASS_RE.match(lines[ln - 1]) else 0
        items.append((kind, max(1, end - ln + 1), cx, name))
    return items


def analyze(api, text, lang):
    items = None
    if lang == "python":
        try:
            items = analyze_python(ast.parse(text))
        except SyntaxError:
            items = None
    if items is None:
        items = analyze_generic(api, text, lang)
    if len(items) > MAX_ITEMS:
        keep = sorted(sorted(range(len(items)), key=lambda i: -items[i][1])[:MAX_ITEMS])
        items = [items[i] for i in keep]
    return [(k, l, c, re.sub(r"\s+", "_", n)) for k, l, c, n in items]


#  dự phòng bằng Python (khi không có gcc)
def py_city(items):
    n = len(items)
    cols = max(1, math.ceil(math.sqrt(n)))
    rows = (n + cols - 1) // cols
    cell = 3.0
    gx, gz = cols * cell + 1.0, rows * cell + 1.0
    out = ["# code city (python): %d khoi" % n, "o ground", "# color 0.16 0.17 0.20",
           "v -1 0 -1", "v %.3f 0 -1" % gx, "v %.3f 0 %.3f" % (gx, gz), "v -1 0 %.3f" % gz,
           "f 1 2 3 4"]
    vb = 5
    for i, (kind, lines, cx, name) in enumerate(items):
        c, r = i % cols, i // cols
        k = min(cx, 20)
        w = min(2.7, 0.9 + 0.12 * k + (0.4 if kind == 1 else 0.0))
        h = 0.4 + 0.45 * (max(lines, 1) ** 0.75)
        x0, z0 = c * cell + (cell - w) / 2, r * cell + (cell - w) / 2
        x1, z1 = x0 + w, z0 + w
        if kind == 1:
            col = (0.30, 0.55, 0.95)
        else:
            t = min(1.0, cx / 15.0)
            col = (0.25 + 0.70 * t, 0.85 - 0.60 * t, 0.30)
        out += ["o " + name, "# color %.3f %.3f %.3f" % col,
                "# info dong=%d, do_phuc_tap=%d" % (lines, cx)]
        for y in (0.0, h):
            for x, z in ((x0, z0), (x1, z0), (x1, z1), (x0, z1)):
                out.append("v %.3f %.3f %.3f" % (x, y, z))
        for q in ((4, 5, 6, 7), (0, 1, 5, 4), (3, 2, 6, 7), (0, 3, 7, 4), (1, 2, 6, 5)):
            out.append("f " + " ".join(str(vb + j) for j in q))
        vb += 8
    return "\n".join(out) + "\n"


def parse_obj(text):
    verts, objs, cur = [], [], None
    for ln in text.splitlines():
        if ln.startswith("o "):
            cur = {"name": ln[2:].strip(), "color": (0.6, 0.6, 0.6), "faces": [], "info": ""}
            objs.append(cur)
        elif ln.startswith("# color") and cur is not None:
            try:
                cur["color"] = tuple(float(x) for x in ln.split()[2:5])
            except ValueError:
                pass
        elif ln.startswith("# info") and cur is not None:
            cur["info"] = ln[6:].strip()
        elif ln.startswith("v "):
            try:
                verts.append(tuple(float(x) for x in ln.split()[1:4]))
            except ValueError:
                pass
        elif ln.startswith("f ") and cur is not None:
            try:
                cur["faces"].append([int(t.split("/")[0]) - 1 for t in ln.split()[1:]])
            except ValueError:
                pass
    return verts, objs


#  khung nhìn 3D
class Viewer(QWidget):
    def __init__(self, verts, objs, theme):
        super().__init__()
        self.verts, self.objs, self.theme = verts, objs, theme
        self.yaw, self.pitch, self.zoom = 0.7, 0.6, 1.0
        self.hover = -1
        self._faces = []
        self._last = None
        self.setMinimumSize(640, 460)
        self.setMouseTracking(True)
        if verts:
            mins = [min(v[i] for v in verts) for i in range(3)]
            maxs = [max(v[i] for v in verts) for i in range(3)]
        else:
            mins = maxs = [0.0, 0.0, 0.0]
        self.c = [(a + b) / 2.0 for a, b in zip(mins, maxs)]
        self.radius = max(0.001, max(
            (math.sqrt(sum((v[i] - self.c[i]) ** 2 for i in range(3))) for v in verts),
            default=1.0))

    def reset_view(self):
        self.yaw, self.pitch, self.zoom = 0.7, 0.6, 1.0
        self.update()

    def _project(self):
        w, h = self.width(), self.height()
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        dist = 2.6 * self.radius / self.zoom
        f = 0.95 * min(w, h) * dist / (2.0 * self.radius)
        pts = []
        for x, y, z in self.verts:
            x -= self.c[0]
            y -= self.c[1]
            z -= self.c[2]
            x1 = x * cy + z * sy
            z1 = -x * sy + z * cy
            y2 = y * cp + z1 * sp
            z2 = -y * sp + z1 * cp
            depth = max(0.01, z2 + dist)
            pts.append((w / 2.0 + f * x1 / depth, h / 2.0 - f * y2 / depth, z2, x1, y2))
        return pts

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(self.theme["bg"]))
        pts = self._project()
        faces = []
        for oi, o in enumerate(self.objs):
            ground = o["name"] == "ground"
            for fi in o["faces"]:
                if len(fi) < 3 or max(fi) >= len(pts) or min(fi) < 0:
                    continue
                ps = [pts[i] for i in fi]
                depth = sum(q[2] for q in ps) / len(ps)
                faces.append((0 if ground else 1, -depth, oi, ps))
        faces.sort(key=lambda t: (t[0], t[1]))
        self._faces = []
        light = (0.35, 0.75, -0.55)
        ln = math.sqrt(sum(a * a for a in light))
        for _g, _d, oi, ps in faces:
            a, b, c = ps[0], ps[1], ps[2]
            ux, uy, uz = b[3] - a[3], b[4] - a[4], b[2] - a[2]
            vx, vy, vz = c[3] - a[3], c[4] - a[4], c[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            nl = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            br = 0.35 + 0.65 * abs((nx * light[0] + ny * light[1] + nz * light[2]) / (nl * ln))
            r, g, bl = self.objs[oi]["color"]
            col = QColor(int(min(255, r * 255 * br)), int(min(255, g * 255 * br)),
                         int(min(255, bl * 255 * br)))
            hov = oi == self.hover
            p.setPen(QPen(QColor(255, 255, 255) if hov else QColor(0, 0, 0, 90),
                          1.8 if hov else 0.8))
            p.setBrush(QBrush(col))
            poly = QPolygonF([QPointF(q[0], q[1]) for q in ps])
            p.drawPolygon(poly)
            self._faces.append((poly, oi))
        p.setPen(QColor(self.theme["fg"]))
        if 0 <= self.hover < len(self.objs):
            o = self.objs[self.hover]
            p.drawText(12, 22, "%s   %s" % (o["name"], o["info"]))
        p.setPen(QColor(self.theme["gutter_fg"]))
        p.drawText(12, self.height() - 10,
                   "Kéo: xoay  |  Lăn chuột: zoom  |  Rê chuột: xem thông tin")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._last = e.pos()

    def mouseReleaseEvent(self, _e):
        self._last = None

    def mouseMoveEvent(self, e):
        if (e.buttons() & Qt.LeftButton) and self._last is not None:
            d = e.pos() - self._last
            self._last = e.pos()
            self.yaw += d.x() * 0.01
            self.pitch = max(-0.2, min(1.5, self.pitch + d.y() * 0.01))
            self.update()
            return
        pt = QPointF(e.pos())
        h = -1
        for poly, oi in reversed(self._faces):
            if self.objs[oi]["name"] != "ground" and poly.containsPoint(pt, Qt.OddEvenFill):
                h = oi
                break
        if h != self.hover:
            self.hover = h
            self.update()

    def wheelEvent(self, e):
        k = 1.1 if e.angleDelta().y() > 0 else 1 / 1.1
        self.zoom = max(0.3, min(8.0, self.zoom * k))
        self.update()


class CityDialog(QDialog):
    def __init__(self, api, obj_text, engine):
        super().__init__(api.window)
        self.api, self.obj_text = api, obj_text
        self.setWindowTitle("Code → 3D")
        self.resize(900, 660)
        self.setAttribute(Qt.WA_DeleteOnClose)
        verts, objs = parse_obj(obj_text)
        self.view = Viewer(verts, objs, api.theme())
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("%d khối  ·  engine: %s  ·  cao = số dòng, màu/rộng = độ phức "
                             "tạp (xanh→đỏ), xanh dương = class" % (max(0, len(objs) - 1), engine)))
        lay.addWidget(self.view, 1)
        row = QHBoxLayout()
        self.spin_b = QPushButton("Tự xoay")
        self.spin_b.setCheckable(True)
        reset_b, save_b, close_b = QPushButton("Đặt lại góc nhìn"), QPushButton("Xuất .obj..."), QPushButton("Đóng")
        for b in (self.spin_b, reset_b, save_b):
            row.addWidget(b)
        row.addStretch(1)
        row.addWidget(close_b)
        lay.addLayout(row)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.spin_b.toggled.connect(lambda on: self.timer.start(30) if on else self.timer.stop())
        reset_b.clicked.connect(self.view.reset_view)
        save_b.clicked.connect(self.export_obj)
        close_b.clicked.connect(self.close)

    def _tick(self):
        self.view.yaw += 0.012
        self.view.update()

    def export_obj(self):
        path = self.api.pick_file(save=True, filter="Wavefront OBJ (*.obj)", title="Lưu mô hình 3D")
        if not path:
            return
        if not path.lower().endswith(".obj"):
            path += ".obj"
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(self.obj_text)
        except OSError as e:
            self.api.error("Không ghi được file:\n%s" % e)
            return
        self.api.status("Đã lưu " + path, 5000)
        self.api.open_folder(path)


#  plugin
def register(api):
    state = {"dlg": None}

    def show(obj_text, engine):
        dlg = CityDialog(api, obj_text, engine)
        state["dlg"] = dlg
        dlg.show()

    def city():
        text = api.text()
        lang = api.language() or "python"
        items = analyze(api, text, lang)
        if not items:
            api.status("Không tìm thấy hàm/class nào để dựng 3D", 4000)
            return
        stdin = "\n".join("%d %d %d %s" % it for it in items) + "\n"
        if api.has_tool("c"):
            api.status("Đang biên dịch C và dựng mô hình 3D...", 4000)

            def done(res):
                code, out, err = res
                if code == 0 and out.strip():
                    show(out, "C (gcc)")
                else:
                    api.log("[code_to_3d] C lỗi, chuyển sang Python:", (err or out)[:500])
                    show(py_city(items), "Python (C bị lỗi)")

            api.run_code_async("c", C_SOURCE, done, stdin=stdin, timeout=60)
        else:
            show(py_city(items), "Python (chưa cài gcc)")

    def open_obj():
        path = api.pick_file(filter="Wavefront OBJ (*.obj);;Tất cả (*)", title="Mở file .obj")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            api.error(str(e))
            return
        verts, objs = parse_obj(text)
        if not verts or not objs:
            api.error("File .obj không có hình để vẽ (cần dòng 'o', 'v', 'f').")
            return
        show(text, "file .obj")

    api.add_separator("Plugins")
    api.add_action("Code → 3D (Code City, dùng C)", city, shortcut="Ctrl+Alt+3", menu="Plugins")
    api.add_action("Xem file .obj bất kỳ...", open_obj, menu="Plugins")
'''

DEFAULT_PLUGINS = {
    "code_to_image.py": PLUGIN_CODE_TO_IMAGE,
    "code_to_3d.py": PLUGIN_CODE_TO_3D,
}
