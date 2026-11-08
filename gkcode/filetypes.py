# -*- coding: utf-8 -*-
"""GKcode 4.4: hỗ trợ thêm nhiều loại tệp — ngôn ngữ lập trình, nhóm icon, và trình mở mới
(kho nén zip/tar, cơ sở dữ liệu SQLite, font chữ)."""
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'langs', 'terminal', 'nettools', 'esp', 'templates', 'polyglot',
           'plugins', 'textools', 'toolsmixin', 'viewers', 'media', 'prefs']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n
import sqlite3
import tarfile

#  1. Ngôn ngữ thêm (tô màu cú pháp + nhận đuôi file)
_hash = dict(_NOCFG, line="#", indent="    ")
_slash = dict(_C_LIKE)
_lang("swift", "Swift", [".swift"], dict(_slash),
      "associatedtype class deinit enum extension fileprivate func import init inout internal let open operator "
      "private protocol public rethrows static struct subscript typealias var break case continue default defer do "
      "else fallthrough for guard if in repeat return switch where while as Any catch false is nil super self Self "
      "throw throws true try async await actor print String Int Double Bool Array Dictionary".split(),
      snippets={"main": 'print("$0")'})
_lang("dart", "Dart", [".dart"], dict(_slash, backtick=False),
      "abstract as assert async await break case catch class const continue covariant default deferred do dynamic "
      "else enum export extends extension external factory false final finally for Function get hide if implements "
      "import in interface is late library mixin new null on operator part required rethrow return set show static "
      "super switch sync this throw true try typedef var void while with yield print String int double bool List Map".split(),
      snippets={"main": "void main() {\n  print('$0');\n}"})
_lang("scala", "Scala", [".scala", ".sc"], dict(_slash),
      "abstract case catch class def do else extends false final finally for forSome if implicit import lazy match "
      "new null object override package private protected return sealed super this throw trait true try type val var "
      "while with yield given using enum println".split())
_lang("groovy", "Groovy / Gradle", [".groovy", ".gradle"], dict(_slash),
      "abstract as assert boolean break byte case catch char class continue def default do double else enum extends "
      "false final finally float for if implements import in instanceof int interface long new null package private "
      "protected public return short static super switch this throw throws true try void while println "
      "plugins dependencies repositories".split())
_lang("objc", "Objective-C", [".m", ".mm"], dict(_slash, preproc=True),
      "@interface @implementation @end @property @selector @protocol @class @synthesize @autoreleasepool id nil "
      "NO YES self super NSString NSArray NSObject BOOL IBOutlet if else for while return void int char float".split())
_lang("zig", "Zig", [".zig"], dict(_NOCFG, line="//", brace=True, indent="    "),
      "addrspace align allowzero and anyframe anytype asm async await break callconv catch comptime const continue "
      "defer else enum errdefer error export extern fn for if inline linksection noalias noinline nosuspend opaque or "
      "orelse packed pub resume return struct suspend switch test threadlocal try union unreachable usingnamespace "
      "var volatile while true false null undefined".split())
_lang("perl", "Perl", [".pl", ".pm"], dict(_hash),
      "my our local use strict warnings sub if elsif else unless while until for foreach last next redo return "
      "package require print printf push pop shift unshift keys values defined undef die eval".split(),
      run=[("Chạy (perl)", "perl", ["{file}"])] if find_tool("perl") else None)
_lang("r", "R", [".r", ".R"], dict(_hash),
      "if else repeat while function for next break TRUE FALSE NULL Inf NaN NA in library require return print "
      "c list data.frame matrix paste cat".split(),
      run=[("Chạy (Rscript)", "Rscript", ["{file}"])] if find_tool("Rscript") else None)
_lang("haskell", "Haskell", [".hs"], dict(_NOCFG, line="--", block=False, indent="  "),
      "case class data default deriving do else foreign if import in infix infixl infixr instance let module newtype "
      "of then type where Maybe Just Nothing Int String Bool IO main putStrLn".split())
_lang("elixir", "Elixir", [".ex", ".exs"], dict(_hash, indent="  "),
      "def defp defmodule defmacro defstruct do end if else unless cond case with for fn when and or not in import "
      "alias require use quote unquote true false nil IO.puts spawn receive send".split(),
      run=[("Chạy (elixir)", "elixir", ["{file}"])] if find_tool("elixir") else None)
_lang("glsl", "Shader (GLSL/HLSL)", [".glsl", ".vert", ".frag", ".geom", ".comp", ".hlsl", ".shader", ".wgsl"],
      dict(_slash, preproc=True),
      "attribute const uniform varying layout in out inout void float int uint bool vec2 vec3 vec4 ivec2 ivec3 "
      "ivec4 mat2 mat3 mat4 sampler2D samplerCube struct if else for while return discard precision highp mediump "
      "lowp float2 float3 float4 float4x4 Texture2D SamplerState cbuffer fn var let".split())
_lang("verilog", "Verilog / SystemVerilog", [".v", ".sv", ".vh", ".svh"], dict(_slash),
      "module endmodule input output inout wire reg logic assign always always_ff always_comb initial begin end if "
      "else case endcase for while posedge negedge parameter localparam integer genvar generate endgenerate "
      "function endfunction task endtask".split())
_lang("vhdl", "VHDL", [".vhd", ".vhdl"], dict(_NOCFG, line="--", indent="    "),
      "architecture begin end entity is of port map signal variable process if then else elsif case when others "
      "library use all in out inout std_logic std_logic_vector integer boolean component generic loop for while".split())
_lang("asm", "Assembly", [".asm", ".s", ".S", ".nasm"], dict(_NOCFG, line=";", indent="    "),
      "mov add sub mul div push pop call ret jmp je jne jz jnz cmp test lea int nop and or xor not shl shr inc dec "
      "section global extern db dw dd dq equ eax ebx ecx edx esi edi esp ebp rax rbx rcx rdx rsp rbp".split())
_lang("latex", "LaTeX", [".tex", ".sty", ".cls"], dict(_NOCFG, line="%", indent="  "),
      r"\begin \end \documentclass \usepackage \section \subsection \chapter \title \author \maketitle \item "
      r"\label \ref \cite \textbf \textit \frac \sum \int".split())
_lang("markdown", "Markdown", [".md", ".markdown", ".mdx"], dict(_NOCFG, triple=("```",), indent="  "), ())
_lang("protobuf", "Protocol Buffers", [".proto"], dict(_slash),
      "syntax package import option message enum service rpc returns repeated optional required oneof map reserved "
      "string bytes bool int32 int64 uint32 uint64 float double".split())
_lang("graphql", "GraphQL", [".graphql", ".gql"], dict(_hash, indent="  "),
      "query mutation subscription fragment on type interface union enum input scalar schema extend directive "
      "implements true false null".split())
_lang("cmake", "CMake", [".cmake"], dict(_hash, indent="  "),
      "if elseif else endif foreach endforeach while endwhile function endfunction macro endmacro set unset option "
      "project add_executable add_library target_link_libraries target_include_directories find_package include "
      "install message cmake_minimum_required".split())
_lang("makefile", "Makefile", [".mk"], dict(_hash, indent="\t"),
      "ifeq ifneq ifdef ifndef else endif include define endef export override all clean install .PHONY".split())
_lang("dockerfile", "Dockerfile", [".dockerfile"], dict(_hash, indent="    "),
      "FROM RUN CMD LABEL EXPOSE ENV ADD COPY ENTRYPOINT VOLUME USER WORKDIR ARG ONBUILD STOPSIGNAL HEALTHCHECK "
      "SHELL AS".split())

NAME_TO_LANG.update({
    "dockerfile": "dockerfile", "makefile": "makefile", "gnumakefile": "makefile", "cmakelists.txt": "cmake",
    "gemfile": "ruby", "rakefile": "ruby", "jenkinsfile": "groovy", "build.gradle": "groovy",
    ".gitignore": "ini", ".gitattributes": "ini", ".editorconfig": "ini", ".env": "ini",
    ".bashrc": "bash", ".zshrc": "bash", ".profile": "bash", "requirements.txt": "ini",
    "package.json": "json", "tsconfig.json": "json", "composer.json": "json",
})
FILE_BADGES.update({
    "dockerfile": ("Dk", "#2496ed", "#ffffff"), "makefile": ("Mk", "#6d8086", "#ffffff"),
    "cmakelists.txt": ("Cm", "#064f8c", "#ffffff"), ".gitignore": ("◆", "#f05033", "#ffffff"),
    ".gitattributes": ("◆", "#f05033", "#ffffff"), ".env": ("⚙", "#ecd53f", "#222222"),
    "requirements.txt": ("Py", "#3776ab", "#ffffff"), "package.json": ("{}", "#cb3837", "#ffffff"),
    "license": ("©", "#d4a017", "#222222"), "readme.md": ("i", "#42a5f5", "#ffffff"),
    ".swift": ("Sw", "#f05138", "#ffffff"), ".dart": ("Da", "#0175c2", "#ffffff"), ".scala": ("Sc", "#dc322f", "#ffffff"),
    ".groovy": ("Gr", "#4298b8", "#ffffff"), ".gradle": ("Gr", "#02303a", "#ffffff"), ".zig": ("Zg", "#f7a41d", "#222222"),
    ".pl": ("Pl", "#39457e", "#ffffff"), ".r": ("R", "#276dc3", "#ffffff"), ".hs": ("λ", "#5e5086", "#ffffff"),
    ".ex": ("Ex", "#6e4a7e", "#ffffff"), ".exs": ("Ex", "#6e4a7e", "#ffffff"), ".m": ("OC", "#438eff", "#ffffff"),
    ".mm": ("OC", "#438eff", "#ffffff"), ".v": ("Vl", "#2e7d32", "#ffffff"), ".sv": ("Sv", "#2e7d32", "#ffffff"),
    ".vhd": ("Vh", "#2e7d32", "#ffffff"), ".asm": ("As", "#6e4c13", "#ffffff"), ".s": ("As", "#6e4c13", "#ffffff"),
    ".tex": ("Tx", "#3d6117", "#ffffff"), ".proto": ("Pb", "#4a7fb5", "#ffffff"), ".graphql": ("Gq", "#e535ab", "#ffffff"),
    ".gql": ("Gq", "#e535ab", "#ffffff"), ".cmake": ("Cm", "#064f8c", "#ffffff"), ".mk": ("Mk", "#6d8086", "#ffffff"),
    ".markdown": ("M", "#42a5f5", "#ffffff"), ".mdx": ("M", "#fcb32c", "#222222"),
    ".ipynb": ("Nb", "#f37726", "#ffffff"), ".lock": ("🔒", "#6d8086", "#ffffff"),
})

#  2. Nhóm tệp -> icon (đuôi chưa có huy hiệu riêng sẽ lấy theo nhóm)
for _cat, _exts in {
    "archive": "zip 7z rar tar gz tgz bz2 xz zst lz cab jar war apk aab whl egg deb rpm pkg dmg msi snap appimage",
    "audio": "mp3 wav flac ogg m4a aac opus wma aiff mid midi amr",
    "video": "mp4 mkv avi mov webm wmv flv m4v mpg mpeg 3gp ts m2ts",
    "image": "png jpg jpeg gif bmp webp ico tif tiff heic avif psd xcf raw cr2 nef dng svg",
    "model3d": "glb gltf fbx obj stl ply off dae 3ds blend usd usdz step stp iges dxf dwg",
    "font": "ttf otf woff woff2 eot fon",
    "database": "db sqlite sqlite3 mdb accdb sql dump rdb",
    "document": "pdf doc docx odt rtf pages epub mobi djvu",
    "sheet": "xls xlsx ods csv tsv numbers",
    "slides": "ppt pptx odp key",
    "binary": "exe dll so dylib o a lib class pyc pyd bin dat out elf",
    "firmware": "hex uf2 elf bin img rom fw",
    "shader": "glsl vert frag hlsl wgsl spv",
    "hardware": "kicad_pcb kicad_sch sch brd gbr gtl gbl drl step eagle fzz pcb",
    "disk": "iso img vhd vmdk vdi qcow2",
    "key": "pem crt cer key pub p12 pfx gpg asc",
    "config": "ini cfg conf config properties env plist reg desktop service",
    "book": "tex bib",
    "data": "json jsonc json5 xml yaml yml toml ndjson jsonl parquet npy npz pkl pickle h5 hdf5 pt pth ckpt safetensors onnx",
    "text": "txt log rst nfo",
    "code": "py js ts c h cpp cs java go rs swift kt rb php lua sh bat ps1 html css scss sql",
}.items():
    for _e in _exts.split():
        FILE_CATEGORY.setdefault("." + _e.lower(), _cat)

for _e in (".sqlite", ".sqlite3", ".db", ".s3db"):
    TEXT_EXTS.discard(_e)
TEXT_EXTS |= {".env", ".lock", ".gitignore", ".editorconfig", ".bib", ".rst", ".ndjson", ".jsonl", ".ipynb",
              ".gradle", ".properties", ".plist", ".desktop", ".service", ".reg", ".diff", ".patch", ".cmake"}

#  3. Trình mở mới
ARCHIVE_EXTS = [".zip", ".jar", ".war", ".apk", ".aab", ".whl", ".egg", ".tar", ".tgz", ".gz", ".bz2", ".xz",
                ".tbz2", ".txz"]


def _human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return ("%d %s" % (n, u)) if u == "B" else ("%.1f %s" % (n, u))
        n /= 1024.0


class ArchiveViewerDialog(QDialog):
    """Xem nội dung kho nén (zip/tar) và giải nén an toàn; mở nhanh file bên trong."""

    def __init__(self, win, path):
        super().__init__(win)
        self.win, self.path = win, path
        self.setWindowTitle("Kho nén — " + os.path.basename(path))
        self.resize(780, 520)
        self.is_zip = zipfile.is_zipfile(path)
        rows = []
        if self.is_zip:
            with zipfile.ZipFile(path) as z:
                for i in z.infolist():
                    rows.append((i.filename, i.file_size, i.compress_size,
                                 "%04d-%02d-%02d %02d:%02d" % i.date_time[:5], i.is_dir()))
        else:
            with tarfile.open(path) as t:
                for m in t.getmembers():
                    rows.append((m.name, m.size, m.size, datetime.datetime.fromtimestamp(m.mtime).strftime(
                        "%Y-%m-%d %H:%M"), m.isdir()))
        lay = QVBoxLayout(self)
        self.table = QTableWidget(len(rows), 4)
        self.table.setHorizontalHeaderLabels(["Tên", "Kích thước", "Đã nén", "Sửa lúc"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        for r, (n, sz, cs, dt, isdir) in enumerate(rows[:20000]):
            self.table.setItem(r, 0, QTableWidgetItem(("📁 " if isdir else "") + n))
            self.table.setItem(r, 1, QTableWidgetItem("" if isdir else _human(sz)))
            self.table.setItem(r, 2, QTableWidgetItem("" if isdir else _human(cs)))
            self.table.setItem(r, 3, QTableWidgetItem(dt))
            self.table.item(r, 0).setData(Qt.UserRole, (n, isdir))
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.cellDoubleClicked.connect(lambda r, _c: self.open_selected())
        lay.addWidget(self.table, 1)
        total = sum(r[1] for r in rows)
        lay.addWidget(QLabel(f"{len(rows)} mục, {_human(total)} sau khi giải nén. "
                             "Bấm đúp một file để mở nhanh trong editor."))
        row = QHBoxLayout()
        b1, b2 = QPushButton("Mở file đã chọn"), QPushButton("Giải nén tất cả...")
        b1.clicked.connect(self.open_selected)
        b2.clicked.connect(self.extract_all)
        row.addStretch(1)
        row.addWidget(b1)
        row.addWidget(b2)
        lay.addLayout(row)

    def open_selected(self):
        r = self.table.currentRow()
        if r < 0:
            return
        name, isdir = self.table.item(r, 0).data(Qt.UserRole)
        if isdir:
            return
        tmp = tempfile.mkdtemp(prefix="gk_arc_")
        try:
            if self.is_zip:
                with zipfile.ZipFile(self.path) as z:
                    if os.path.isabs(name) or ".." in name.replace("\\", "/").split("/"):
                        raise ValueError("Đường dẫn không an toàn")
                    out = z.extract(name, tmp)
            else:
                with tarfile.open(self.path) as t:
                    m = t.getmember(name)
                    if not m.isfile() or os.path.isabs(name) or ".." in name.split("/"):
                        raise ValueError("Mục không mở được")
                    t.extract(m, tmp)
                    out = os.path.join(tmp, name)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Không mở được", str(e))
            return
        self.win.open_path(out)

    def extract_all(self):
        dest = QFileDialog.getExistingDirectory(self, "Giải nén vào thư mục...", os.path.dirname(self.path))
        if not dest:
            return
        try:
            (safe_extract_zip if self.is_zip else safe_extract_tar)(self.path, dest)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Giải nén lỗi", str(e))
            return
        QMessageBox.information(self, "Xong", "Đã giải nén vào:\n" + dest)


class SqliteViewerDialog(QDialog):
    """Xem bảng trong file SQLite (mở chỉ-đọc) và chạy truy vấn SELECT."""
    MAX_ROWS = 2000

    def __init__(self, win, path):
        super().__init__(win)
        self.setWindowTitle("SQLite — " + os.path.basename(path))
        self.resize(900, 560)
        uri = "file:" + urllib.request.pathname2url(os.path.abspath(path)) + "?mode=ro"
        self.con = sqlite3.connect(uri, uri=True)
        lay = QHBoxLayout(self)
        left = QVBoxLayout()
        self.tables = QListWidget()
        self.tables.setMaximumWidth(220)
        for n, kind in self.con.execute(
                "SELECT name, type FROM sqlite_master WHERE type IN ('table','view') "
                "AND name NOT LIKE 'sqlite_%' ORDER BY type, name"):
            self.tables.addItem(("▦ " if kind == "table" else "◫ ") + n)
        left.addWidget(QLabel("Bảng / view"))
        left.addWidget(self.tables, 1)
        lay.addLayout(left)
        right = QVBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText("SELECT ... (chỉ đọc) rồi Enter")
        self.grid = QTableWidget()
        self.grid.setEditTriggers(QTableWidget.NoEditTriggers)
        self.status = QLabel("")
        right.addWidget(self.query)
        right.addWidget(self.grid, 1)
        right.addWidget(self.status)
        lay.addLayout(right, 1)
        self.tables.currentTextChanged.connect(self.pick)
        self.query.returnPressed.connect(lambda: self.run(self.query.text()))
        if self.tables.count():
            self.tables.setCurrentRow(0)

    def pick(self, text):
        name = text[2:].replace('"', '""')
        self.query.setText(f'SELECT * FROM "{name}"')
        self.run(self.query.text())

    def run(self, sql):
        if not sql.strip().lower().startswith(("select", "pragma", "with", "explain")):
            self.status.setText("Chỉ cho phép SELECT / PRAGMA / WITH (kết nối chỉ-đọc).")
            return
        try:
            cur = self.con.execute(sql)
            cols = [d[0] for d in (cur.description or [])]
            rows = cur.fetchmany(self.MAX_ROWS + 1)
        except sqlite3.Error as e:
            self.status.setText("Lỗi: %s" % e)
            return
        more = len(rows) > self.MAX_ROWS
        rows = rows[:self.MAX_ROWS]
        self.grid.clear()
        self.grid.setColumnCount(len(cols))
        self.grid.setRowCount(len(rows))
        self.grid.setHorizontalHeaderLabels(cols)
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                self.grid.setItem(r, c, QTableWidgetItem(
                    "<blob %d byte>" % len(v) if isinstance(v, bytes) else ("NULL" if v is None else str(v))))
        self.grid.resizeColumnsToContents()
        self.status.setText("%d dòng%s, %d cột" % (len(rows), " (còn nữa, chỉ hiện %d đầu)" % self.MAX_ROWS if more else "",
                                                 len(cols)))

    def closeEvent(self, e):
        try:
            self.con.close()
        finally:
            super().closeEvent(e)


class FontPreviewDialog(QDialog):
    """Xem trước font chữ (ttf/otf): bảng chữ, số, tiếng Việt, và mẫu theo nhiều cỡ."""
    SAMPLE = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxyz\n0123456789 !@#$%^&*()\n"
              "Tiếng Việt: Ăn quả nhớ kẻ trồng cây — ạ ả ã à á ơ ư đ")

    def __init__(self, win, path):
        super().__init__(win)
        fid = QFontDatabase.addApplicationFont(path)
        fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
        if not fams:
            raise ValueError("Không đọc được font")
        self.setWindowTitle("Font — " + fams[0])
        self.resize(720, 560)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>%s</b>  (%s)" % (fams[0], os.path.basename(path))))
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        inner = QWidget()
        il = QVBoxLayout(inner)
        for size in (12, 18, 28, 44):
            lb = QLabel(self.SAMPLE if size <= 18 else self.SAMPLE.split("\n")[0])
            f = QFont(fams[0])
            f.setPixelSize(size)
            lb.setFont(f)
            lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
            il.addWidget(QLabel("%d px" % size))
            il.addWidget(lb)
        il.addStretch(1)
        sc.setWidget(inner)
        lay.addWidget(sc, 1)


def _open_archive(win, path):
    if not (zipfile.is_zipfile(path) or tarfile.is_tarfile(path)):
        return False                       # ví dụ .gz thường: để trình khác xử lý
    _std_dialog(win, ArchiveViewerDialog(win, path))
    return True


def _open_sqlite(win, path):
    if read_head(path, 16) != b"SQLite format 3\x00":
        return False                       # .db không phải SQLite
    _std_dialog(win, SqliteViewerDialog(win, path))
    return True


def _open_font(win, path):
    _std_dialog(win, FontPreviewDialog(win, path))
    return True


def _sniff_sqlite(head):
    return head.startswith(b"SQLite format 3\x00")


def register_more_openers():
    register_opener("archive", "Kho nén (zip/tar)", ARCHIVE_EXTS, _open_archive)
    register_opener("sqlite", "Cơ sở dữ liệu SQLite", [".sqlite", ".sqlite3", ".db", ".s3db"], _open_sqlite,
                    sniff=_sniff_sqlite)
    register_opener("font", "Font chữ", [".ttf", ".otf"], _open_font)
