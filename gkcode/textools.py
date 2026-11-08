# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp', 'templates', 'polyglot', 'plugins']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


def _chk(v):
    if isinstance(v, int) and v.bit_length() > _MAX_BITS:
        raise ValueError("Kết quả quá lớn")
    return v


def _safe_pow(a, b):
    if isinstance(a, int) and isinstance(b, int) and b > 0 and a.bit_length() * b > _MAX_BITS:
        raise ValueError("Kết quả quá lớn")
    return _chk(a ** b)


def _safe_lshift(a, b):
    if isinstance(a, int) and isinstance(b, int) and b > 0 and a.bit_length() + b > _MAX_BITS:
        raise ValueError("Kết quả quá lớn")
    return _chk(operator.lshift(a, b))


def _safe_factorial(n):
    if n > 2000:
        raise ValueError("Giai thừa quá lớn (tối đa 2000)")
    return math.factorial(n)


_SAFE_FUNCS = {n: getattr(math, n) for n in (
    "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "log", "log10",
    "log2", "exp", "floor", "ceil", "fabs", "radians", "degrees", "gcd", "hypot")}
_SAFE_FUNCS.update(abs=abs, round=round, min=min, max=max,
                   factorial=_safe_factorial, pow=_safe_pow)
_SAFE_CONSTS = {"pi": math.pi, "e": math.e, "tau": math.tau}
_BINOPS = {ast.Add: lambda a, b: _chk(a + b), ast.Sub: lambda a, b: _chk(a - b),
           ast.Mult: lambda a, b: _chk(a * b),
           ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
           ast.Mod: operator.mod, ast.Pow: _safe_pow, ast.BitAnd: operator.and_,
           ast.BitOr: operator.or_, ast.BitXor: operator.xor,
           ast.LShift: _safe_lshift, ast.RShift: operator.rshift}
_UNOPS = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Invert: operator.invert}


def safe_eval(expr):
    """Tính biểu thức toán học an toàn (không chạy code tùy ý, chặn số quá lớn)."""
    if len(expr) > _MAX_EXPR_LEN:
        raise ValueError("Biểu thức quá dài")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            return _chk(n.value)
        if isinstance(n, ast.BinOp) and type(n.op) in _BINOPS:
            return _BINOPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _UNOPS:
            return _UNOPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Name) and n.id in _SAFE_CONSTS:
            return _SAFE_CONSTS[n.id]
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id in _SAFE_FUNCS and not n.keywords:
            return _SAFE_FUNCS[n.func.id](*[ev(a) for a in n.args])
        raise ValueError("Biểu thức không được hỗ trợ")
    return ev(ast.parse(expr.strip(), mode="eval"))


def register_builtin_text_tools(api, menu):
    def target():
        sel = api.selection()
        return (sel, True) if sel else (api.text(), False)

    def apply(fn):
        def run():
            text, is_sel = target()
            if not text:
                api.status("Không có nội dung")
                return
            try:
                new = fn(text)
            except Exception as e:  # noqa: BLE001
                api.error(f"Không xử lý được: {e}")
                return
            if is_sel:
                api.replace_selection(new)
            else:
                api.set_text(new)
        return run

    def show_hash(algo):
        def run():
            text, _ = target()
            h = hashlib.new(algo, text.encode("utf-8")).hexdigest()
            api.copy(h)
            api.message(f"{algo.upper()}:\n{h}\n\n(đã chép vào clipboard)", "Hash")
        return run

    def calc():
        sel = api.selection().strip()
        if not sel:
            expr = api.ask("Biểu thức (vd: 2*pi*5, sqrt(2)+1, 0xFF+1):")
            if not expr:
                return
            insert = True
        else:
            expr, insert = sel, False
        try:
            val = safe_eval(expr)
        except Exception as e:  # noqa: BLE001
            api.error(f"Không tính được: {e}")
            return
        if insert:
            api.insert(str(val))
        else:
            api.replace_selection(f"{expr} = {val}")
        api.status(f"{expr} = {val}")

    def pick_color():
        c = QColorDialog.getColor(QColor("#3794ff"), api.window, "Chọn màu")
        if c.isValid():
            api.insert(c.name())

    def dec_hex():
        s = api.selection().strip()
        if not s:
            api.status("Hãy chọn một số")
            return
        try:
            api.replace_selection(str(int(s, 16)) if s.lower().startswith("0x") else hex(int(s)))
        except ValueError:
            api.error(f"'{s}' không phải số nguyên")

    def dedupe(text):
        seen, out = set(), []
        for ln in text.split("\n"):
            if ln not in seen:
                seen.add(ln)
                out.append(ln)
        return "\n".join(out)

    def json_minify(text):
        return json.dumps(json.loads(text), separators=(",", ":"), ensure_ascii=False)

    def b64d(text):
        return base64.b64decode(text.strip()).decode("utf-8")

    items = [
        ("Base64: mã hóa", apply(lambda t: base64.b64encode(t.encode("utf-8")).decode())),
        ("Base64: giải mã", apply(b64d)),
        ("URL: mã hóa", apply(lambda t: urllib.parse.quote(t, safe=""))),
        ("URL: giải mã", apply(urllib.parse.unquote)),
        ("JSON: thu gọn (minify)", apply(json_minify)),
        ("Xóa dòng trùng", apply(dedupe)),
        ("Đảo ngược thứ tự dòng", apply(lambda t: "\n".join(reversed(t.split("\n"))))),
        None,
        ("Hash MD5", show_hash("md5")),
        ("Hash SHA-1", show_hash("sha1")),
        ("Hash SHA-256", show_hash("sha256")),
        None,
        ("Tính biểu thức (chọn hoặc nhập)", calc),
        ("Đổi số thập phân ↔ hex", dec_hex),
        ("Chọn màu → chèn #rrggbb", pick_color),
        ("Chèn UUID", lambda: api.insert(str(uuid.uuid4()))),
        ("Chèn ngày giờ (ISO)", lambda: api.insert(datetime.datetime.now().isoformat(timespec="seconds"))),
        ("Chèn Unix timestamp", lambda: api.insert(str(int(time.time())))),
    ]
    for it in items:
        if it is None:
            api.add_separator(menu)
        else:
            api.add_action(it[0], it[1], menu=menu)


# Trình xem: JSON tree, bảng (CSV), ảnh, Regex tester, TODO panel
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico"}


def _json_type(v):
    if isinstance(v, bool):
        return "boolean"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return "number"
    return "string"


def _add_json(parent, key, val, depth=0):
    if isinstance(val, dict) and depth < 60:
        it = QTreeWidgetItem(parent, [str(key), f"{{ }}  {len(val)} khóa", "object"])
        for k, v in list(val.items())[:5000]:
            _add_json(it, k, v, depth + 1)
    elif isinstance(val, (list, tuple)) and depth < 60:
        it = QTreeWidgetItem(parent, [str(key), f"[ ]  {len(val)} phần tử", "array"])
        for i, v in enumerate(list(val)[:5000]):
            _add_json(it, i, v, depth + 1)
    else:
        shown = json.dumps(val, ensure_ascii=False, default=str)
        QTreeWidgetItem(parent, [str(key), shown[:2000], _json_type(val)])


class JsonTreeDialog(QDialog):
    def __init__(self, parent, data, title="JSON"):
        super().__init__(parent)
        self.setWindowTitle(f"JSON dạng cây - {title}")
        self.resize(640, 520)
        lay = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Khóa", "Giá trị", "Kiểu"])
        self.tree.setColumnWidth(0, 220)
        self.tree.setColumnWidth(1, 300)
        _add_json(self.tree.invisibleRootItem(), "(gốc)", data)
        self.tree.expandToDepth(1)
        lay.addWidget(self.tree, 1)
        row = QHBoxLayout()
        a, b = QPushButton("Mở rộng hết"), QPushButton("Thu gọn")
        a.clicked.connect(self.tree.expandAll)
        b.clicked.connect(lambda: (self.tree.collapseAll(), self.tree.expandToDepth(0)))
        row.addWidget(a)
        row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)


def table_from_data(data):
    """Chuẩn hóa dict-of-lists / list-of-dicts / list-of-lists thành (header, rows)."""
    if isinstance(data, dict):
        if data and all(isinstance(v, (list, tuple)) for v in data.values()):
            keys = list(data)
            n = max(len(v) for v in data.values())
            return keys, [[data[k][i] if i < len(data[k]) else "" for k in keys] for i in range(n)]
        return ["Khóa", "Giá trị"], [[k, v] for k, v in data.items()]
    data = list(data)
    if data and all(isinstance(r, dict) for r in data):
        keys = []
        for r in data:
            for k in r:
                if k not in keys:
                    keys.append(k)
        return keys, [[r.get(k, "") for k in keys] for r in data]
    rows = [list(r) if isinstance(r, (list, tuple)) else [r] for r in data]
    w = max((len(r) for r in rows), default=0)
    return [str(i + 1) for i in range(w)], [r + [""] * (w - len(r)) for r in rows]


class TableDialog(QDialog):
    MAX_ROWS = 5000

    def __init__(self, parent, header, rows, title="Bảng"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(760, 480)
        lay = QVBoxLayout(self)
        shown = rows[:self.MAX_ROWS]
        self.table = QTableWidget(len(shown), len(header))
        self.table.setHorizontalHeaderLabels([str(h) for h in header])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        for r, row in enumerate(shown):
            for c, v in enumerate(row[:len(header)]):
                self.table.setItem(r, c, QTableWidgetItem("" if v is None else str(v)))
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)
        lay.addWidget(self.table, 1)
        extra = f" (chỉ hiện {self.MAX_ROWS} dòng đầu)" if len(rows) > self.MAX_ROWS else ""
        lay.addWidget(QLabel(f"{len(rows)} dòng, {len(header)} cột{extra}. Bấm tiêu đề cột để sắp xếp."))


REGEX_SCRIPT = r'''
import sys, json, re
d = json.load(sys.stdin)
fl = 0
for ch, f in (("i", re.I), ("m", re.M), ("s", re.S)):
    if ch in d["flags"]:
        fl |= f
try:
    rx = re.compile(d["p"], fl)
except re.error as e:
    print(json.dumps({"err": str(e)})); sys.exit()
out = []
for m in rx.finditer(d["t"]):
    out.append([m.start(), m.end(), list(m.groups())])
    if len(out) >= 2000:
        break
print(json.dumps({"m": out}))
'''


class RegexThread(QThread):
    """Chạy regex trong tiến trình riêng có timeout, nên pattern backtracking thảm họa
    không làm đơ app."""
    done = pyqtSignal(int, object)

    def __init__(self, seq, pattern, flags, text, parent=None):
        super().__init__(parent)
        self.seq, self.payload = seq, json.dumps({"p": pattern, "flags": flags, "t": text})

    def run(self):
        py = get_python_command()
        if py is None:
            self.done.emit(self.seq, {"err": "Không tìm thấy Python"})
            return
        try:
            r = subprocess.run(py + ["-c", REGEX_SCRIPT], input=self.payload.encode("utf-8"),
                               capture_output=True, timeout=3, creationflags=NO_WINDOW)
            self.done.emit(self.seq, json.loads(r.stdout.decode("utf-8") or "{}"))
        except subprocess.TimeoutExpired:
            self.done.emit(self.seq, {"err": "Quá 3 giây - pattern có thể bị backtracking thảm họa"})
        except (OSError, ValueError) as e:
            self.done.emit(self.seq, {"err": str(e)})


class RegexDialog(QDialog):
    COLORS = ["#264f78", "#5a3d7a"]

    def __init__(self, parent, text=""):
        super().__init__(parent)
        self.setWindowTitle("Regex tester")
        self.resize(680, 560)
        self._seq = 0
        self._threads = []
        lay = QVBoxLayout(self)
        row = QHBoxLayout()
        self.pattern = QLineEdit()
        self.pattern.setPlaceholderText(r"Pattern, vd: (\d+)-(\w+)")
        self.cb = {ch: QCheckBox(label) for ch, label in
                   (("i", "i (không phân biệt hoa/thường)"), ("m", "m"), ("s", "s"))}
        row.addWidget(self.pattern, 1)
        for c in self.cb.values():
            row.addWidget(c)
        lay.addLayout(row)
        self.text = QPlainTextEdit(text)
        self.text.setFont(pick_font(10))
        lay.addWidget(self.text, 2)
        self.info = QLabel("")
        lay.addWidget(self.info)
        self.list = QListWidget()
        lay.addWidget(self.list, 1)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._run)
        self.pattern.textChanged.connect(lambda _t: self._timer.start(350))
        self.text.textChanged.connect(lambda: self._timer.start(350))
        for c in self.cb.values():
            c.toggled.connect(lambda _v: self._timer.start(100))
        self.list.currentRowChanged.connect(self._select)
        self._matches = []

    def _run(self):
        pat = self.pattern.text()
        if not pat:
            self.info.setText("")
            self.list.clear()
            self.text.setExtraSelections([])
            return
        self._seq += 1
        flags = "".join(ch for ch, c in self.cb.items() if c.isChecked())
        t = RegexThread(self._seq, pat, flags, self.text.toPlainText()[:200000], self)
        t.done.connect(self._on_result)
        t.finished.connect(lambda t=t: self._threads.remove(t) if t in self._threads else None)
        self._threads.append(t)
        t.start()

    def _on_result(self, seq, res):
        if seq != self._seq:
            return
        self.list.clear()
        if "err" in res:
            self.info.setText("⚠ " + res["err"])
            self.text.setExtraSelections([])
            self._matches = []
            return
        self._matches = res.get("m", [])
        sels = []
        doc_text = self.text.toPlainText()
        for i, (s, e, groups) in enumerate(self._matches):
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor(self.COLORS[i % 2]))
            cur = self.text.textCursor()
            cur.setPosition(s)
            cur.setPosition(e, QTextCursor.KeepAnchor)
            sel.cursor = cur
            sels.append(sel)
            g = "  " + str(groups) if groups else ""
            self.list.addItem(f"#{i + 1} [{s}:{e}] {doc_text[s:e]!r}{g}")
        self.text.setExtraSelections(sels)
        self.info.setText(f"{len(self._matches)} khớp" + (" (giới hạn 2000)" if len(self._matches) >= 2000 else ""))

    def _select(self, row):
        if 0 <= row < len(self._matches):
            s, e, _g = self._matches[row]
            cur = self.text.textCursor()
            cur.setPosition(s)
            cur.setPosition(e, QTextCursor.KeepAnchor)
            self.text.setTextCursor(cur)

    def closeEvent(self, e):
        self._seq += 1
        for t in list(self._threads):
            t.wait(3500)
        super().closeEvent(e)


TODO_RE = re.compile(r"(?:#|//|/\*|\*|--|<!--|;)\s*(TODO|FIXME|HACK|XXX|BUG)\b[:\s(]*(.*)")


class TodoScanThread(QThread):
    done = pyqtSignal(object)

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = root
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        out, files = [], 0
        for dp, dns, fns in os.walk(self.root):
            dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
            for fn in fns:
                if self._stop or files > 4000:
                    self.done.emit(out)
                    return
                p = os.path.join(dp, fn)
                if os.path.splitext(fn)[1].lower() not in TEXT_EXTS:
                    continue
                try:
                    if os.path.getsize(p) > 1_000_000:
                        continue
                    files += 1
                    with open(p, encoding="utf-8", errors="replace") as f:
                        for n, line in enumerate(f, 1):
                            if len(line) < 600:
                                m = TODO_RE.search(line)
                                if m:
                                    out.append((p, n, m.group(1), m.group(2).strip()[:200]))
                except OSError:
                    continue
        self.done.emit(out)


class TodoPanel(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.thread_ = None
        self.items = []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        row = QHBoxLayout()
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Lọc (TODO, FIXME, tên file...)")
        b = QPushButton("Quét lại")
        row.addWidget(self.filter, 1)
        row.addWidget(b)
        lay.addLayout(row)
        self.list = QListWidget()
        lay.addWidget(self.list, 1)
        self.count = QLabel("")
        lay.addWidget(self.count)
        b.clicked.connect(self.refresh)
        self.filter.textChanged.connect(self._fill)
        self.list.itemActivated.connect(self._open)

    def refresh(self):
        if self.thread_ is not None and self.thread_.isRunning():
            return
        self.count.setText("Đang quét...")
        t = TodoScanThread(self.win._project_root(), self)
        t.done.connect(self._on_done)
        self.thread_ = t
        t.start()

    def _on_done(self, items):
        self.items = items
        self._fill()

    def _fill(self):
        q = self.filter.text().strip().lower()
        root = self.win._project_root()
        self.list.clear()
        shown = 0
        for p, n, tag, text in self.items:
            rel = os.path.relpath(p, root) if root else p
            label = f"[{tag}] {text}   -   {rel}:{n}"
            if q and q not in label.lower():
                continue
            it = QListWidgetItem(label)
            it.setData(Qt.UserRole, (p, n))
            self.list.addItem(it)
            shown += 1
        self.count.setText(f"{shown} / {len(self.items)} mục")

    def _open(self, item):
        p, n = item.data(Qt.UserRole)
        self.win.open_at(p, n)


class GitPanel(QWidget):
    """Panel Git: nhánh, danh sách file thay đổi, stage / unstage / diff / commit."""

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.root = None
        self._busy = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        self.branch = QLabel("Git: -")
        lay.addWidget(self.branch)
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.ExtendedSelection)
        lay.addWidget(self.list, 1)
        r1, r2 = QHBoxLayout(), QHBoxLayout()
        self.btns = {}
        for row, items in ((r1, (("Làm mới", self.refresh), ("Stage", self.stage),
                                 ("Unstage", self.unstage), ("Diff", self.diff))),
                           (r2, (("Commit...", self.commit), ("Pull", self.pull),
                                 ("Push", self.push)))):
            for text, slot in items:
                b = QPushButton(text)
                b.clicked.connect(lambda _=False, s=slot: s())
                row.addWidget(b)
                self.btns[text] = b
        lay.addLayout(r1)
        lay.addLayout(r2)
        self.list.itemActivated.connect(lambda _i: self.open_selected())

    #  tiện ích
    def _git_args(self, args, cb):
        git = find_tool("git")
        if git is None or self.root is None:
            return
        self.win._capture_async([git] + args, cb, 30, self.root)

    def _paths(self):
        return [i.data(Qt.UserRole) for i in self.list.selectedItems() if i.data(Qt.UserRole)]

    def _run_then_refresh(self, args):
        def done(res):
            if res[0] != 0:
                self.win.terminal.appendPlainText(f"[git] {res[2] or res[1]}")
            self.refresh()
        self._git_args(args, done)

    #  làm mới
    def refresh(self):
        if self._busy:
            return
        root = find_up(self.win._project_root(), ".git")
        self.root = root
        if root is None or find_tool("git") is None:
            self.list.clear()
            self.branch.setText("Git: (không phải repo hoặc chưa cài git)")
            self.win.set_branch_text("")
            return
        self._busy = True

        def done(res):
            self._busy = False
            code, out, err = res
            self.list.clear()
            if code != 0:
                self.branch.setText("Git: lỗi - " + (err.strip().splitlines() or ["?"])[-1])
                return
            lines = out.splitlines()
            head = lines[0][3:] if lines and lines[0].startswith("## ") else ""
            self.branch.setText(f"Nhánh: {head}  -  {len(lines) - (1 if head else 0)} thay đổi")
            self.win.set_branch_text(head.split("...")[0])
            for ln in lines[1 if head else 0:]:
                xy, path = ln[:2], ln[3:]
                if " -> " in path:
                    path = path.split(" -> ")[-1]
                path = path.strip('"')
                it = QListWidgetItem(f"{xy}  {path}")
                it.setData(Qt.UserRole, path)
                self.list.addItem(it)

        self._git_args(["status", "--porcelain=v1", "-b"], done)

    #  thao tác
    def stage(self):
        p = self._paths()
        if p:
            self._run_then_refresh(["add", "--"] + p)

    def unstage(self):
        p = self._paths()
        if p:
            self._run_then_refresh(["restore", "--staged", "--"] + p)

    def diff(self):
        p = self._paths()
        if not p:
            return

        def show(res):
            text = res[1] or res[2] or "(không có thay đổi)"
            ed = self.win.new_tab(content=text)
            ed.set_language(None)
            ed.document().setModified(False)
        self._git_args(["diff", "HEAD", "--"] + p, show)

    def open_selected(self):
        p = self._paths()
        if p and self.root:
            self.win.open_path(os.path.join(self.root, p[0]))

    def commit(self):
        msg, ok = QInputDialog.getText(self, "Git commit",
                                       "Nội dung commit (commit các file đã stage;\n"
                                       "nếu chưa stage gì sẽ add tất cả):")
        if not ok or not msg.strip():
            return
        git = find_tool("git")
        if git is None or self.root is None:
            return

        def after_status(res):
            staged = any(l[:1] not in (" ", "?") for l in res[1].splitlines())
            steps = [] if staged else [("git add", ["add", "-A"])]
            steps.append(("git commit", ["commit", "-m", msg.strip()]))
            self.win._git(steps, cwd=self.root,
                          on_done=lambda: (self.win._on_done(), self.refresh()))
        self._git_args(["status", "--porcelain=v1"], after_status)

    def pull(self):
        self.win._git([("git pull", ["pull"])], cwd=self.root,
                      on_done=lambda: (self.win._on_done(), self.refresh()))

    def push(self):
        self.win._git([("git push", ["push"])], cwd=self.root,
                      on_done=lambda: (self.win._on_done(), self.refresh()))


class ReplPanel(QWidget):
    """Python REPL chạy trong tiến trình riêng: lệnh treo không làm đơ app."""

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.proc = None
        self._dec = codecs.getincrementaldecoder("utf-8")(errors="replace")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(5000)
        self.output.setFont(pick_font(10))
        self.input = HistoryLineEdit()
        self.input.setPlaceholderText("Python (tiến trình riêng, không có api) - Enter để gửi")
        row = QHBoxLayout()
        row.setContentsMargins(4, 2, 4, 2)
        self.restart_b, self.stop_b = QPushButton("Khởi động lại"), QPushButton("Dừng")
        row.addWidget(self.input, 1)
        row.addWidget(self.restart_b)
        row.addWidget(self.stop_b)
        lay.addWidget(self.output, 1)
        lay.addLayout(row)
        self.input.returnPressed.connect(self._submit)
        self.restart_b.clicked.connect(self.start)
        self.stop_b.clicked.connect(self.stop)
        self.apply_theme(THEMES.get(win.theme_name, THEMES[DEFAULT_THEME]))

    def apply_theme(self, t):
        self.output.setStyleSheet(
            f"QPlainTextEdit {{ background: {t['terminal_bg']}; color: {t['terminal_fg']}; border: none; }}")

    def running(self):
        return self.proc is not None and self.proc.state() != QProcess.NotRunning

    def start(self):
        self.stop()
        py = get_python_command()
        if py is None:
            self.output.appendPlainText("Không tìm thấy Python.")
            return
        p = QProcess(self)
        p.setProcessChannelMode(QProcess.MergedChannels)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        env.insert("PYTHONUTF8", "1")
        p.setProcessEnvironment(env)
        p.setWorkingDirectory(self.win._project_root())
        p.readyRead.connect(self._read)
        p.finished.connect(lambda c, _s: self.output.appendPlainText(f"\n[REPL kết thúc, mã {c}]"))
        self.proc = p
        self._dec = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.output.clear()
        p.start(py[0], py[1:] + ["-u", "-i", "-q"])

    def stop(self):
        if self.running():
            self.proc.readyRead.disconnect()
            self.proc.kill()
            self.proc.waitForFinished(1000)
        self.proc = None

    def _read(self):
        text = self._dec.decode(bytes(self.proc.readAll())).replace("\r\n", "\n").replace("\r", "")
        cur = self.output.textCursor()
        cur.movePosition(QTextCursor.End)
        cur.insertText(text)
        self.output.moveCursor(QTextCursor.End)

    def send_text(self, text):
        if not self.running():
            self.start()
            if not self.proc.waitForStarted(3000):
                return
        if not text.endswith("\n"):
            text += "\n"
        if "\n" in text.strip("\n"):
            text += "\n"        # dòng trống để kết thúc khối lệnh nhiều dòng
        self.proc.write(text.encode("utf-8"))

    def _submit(self):
        line = self.input.text()
        self.input.push(line)
        self.input.clear()
        self.send_text(line)
