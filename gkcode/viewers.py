# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp', 'templates', 'polyglot', 'plugins', 'textools', 'toolsmixin']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


MAGIC_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "Ảnh PNG"), (b"\xff\xd8\xff", "Ảnh JPEG"), (b"GIF8", "Ảnh GIF"),
    (b"BM", "Ảnh BMP"), (b"RIFF", "RIFF (WAV/AVI/WEBP)"), (b"%PDF", "PDF"),
    (b"PK\x03\x04", "ZIP / DOCX / APK / PT (PyTorch)"), (b"MZ", "Windows EXE/DLL (PE)"),
    (b"\x7fELF", "Linux ELF"), (b"glTF", "GLB (glTF nhị phân)"),
    (b"Kaydara FBX Binary", "FBX nhị phân"), (b"OggS", "Ogg"), (b"ID3", "MP3 (ID3)"),
    (b"\x1aE\xdf\xa3", "Matroska / WebM"), (b"\x1f\x8b", "GZIP"), (b"7z\xbc\xaf", "7-Zip"),
    (b"Rar!", "RAR"), (b"SQLite format 3", "SQLite"), (b"\x80\x02", "Pickle (v2)"),
    (b"\x80\x04", "Pickle (v4)"), (b"\x93NUMPY", "NumPy .npy"), (b"OTTO", "Font OpenType"),
    (b"\x00\x01\x00\x00", "Font TrueType"), (b"fLaC", "FLAC"),
]


def sniff_file_type(head):
    """Đoán loại file từ vài byte đầu."""
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return "MP4 / MOV / M4A (ISO media)"
    for sig, name in MAGIC_SIGNATURES:
        if head.startswith(sig):
            return name
    return "Không rõ"


def hex_dump_lines(data, base=0, width=16):
    """Trả về các dòng hexdump: offset | hex | ascii."""
    out = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        hx = " ".join("%02X" % b for b in chunk)
        if len(chunk) > 8:
            hx = hx[:23] + " " + hx[23:]
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append("%08X  %-48s  %s" % (base + i, hx, asc))
    return out


# Mesh: mỗi hàm trả về (verts, faces) hoặc raise ValueError
# verts = [(x,y,z)], faces = [(i,j,k,...)]
MESH_EXTS = {".glb", ".gltf", ".obj", ".stl", ".ply", ".fbx", ".off"}


def _triangulate(poly):
    return [(poly[0], poly[i], poly[i + 1]) for i in range(1, len(poly) - 1)]


def parse_obj(path):
    verts, faces = [], []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("f "):
                idx = []
                for tok in line.split()[1:]:
                    i = int(tok.split("/")[0])
                    idx.append(i - 1 if i > 0 else len(verts) + i)
                if len(idx) >= 3:
                    faces.extend(_triangulate(idx))
    if not verts:
        raise ValueError("OBJ không có đỉnh nào")
    return verts, faces


def parse_off(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        toks = f.read().split()
    if not toks or not toks[0].startswith("OFF"):
        raise ValueError("Không phải file OFF")
    nv, nf = int(toks[1]), int(toks[2])
    p = 4
    verts = [(float(toks[p + 3 * i]), float(toks[p + 3 * i + 1]), float(toks[p + 3 * i + 2]))
             for i in range(nv)]
    p += 3 * nv
    faces = []
    for _ in range(nf):
        n = int(toks[p])
        idx = [int(x) for x in toks[p + 1:p + 1 + n]]
        faces.extend(_triangulate(idx))
        p += n + 1
    return verts, faces


def parse_stl(path):
    with open(path, "rb") as f:
        data = f.read()
    verts, faces = [], []
    n_tri = _struct.unpack_from("<I", data, 80)[0] if len(data) >= 84 else -1
    if len(data) == 84 + 50 * n_tri:           # STL nhị phân
        for i in range(n_tri):
            base = 84 + 50 * i + 12
            a = len(verts)
            for k in range(3):
                verts.append(_struct.unpack_from("<3f", data, base + 12 * k))
            faces.append((a, a + 1, a + 2))
    else:                                       # STL ascii
        cur = []
        for line in data.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("vertex"):
                p = line.split()
                cur.append((float(p[1]), float(p[2]), float(p[3])))
                if len(cur) == 3:
                    a = len(verts)
                    verts.extend(cur)
                    faces.append((a, a + 1, a + 2))
                    cur = []
    if not faces:
        raise ValueError("STL trống")
    return verts, faces


_PLY_TYPES = {"char": "b", "uchar": "B", "int8": "b", "uint8": "B", "short": "h", "ushort": "H",
              "int16": "h", "uint16": "H", "int": "i", "uint": "I", "int32": "i", "uint32": "I",
              "float": "f", "float32": "f", "double": "d", "float64": "d"}


def parse_ply(path):
    with open(path, "rb") as f:
        data = f.read()
    end = data.find(b"end_header")
    if end < 0:
        raise ValueError("PLY thiếu header")
    nl = data.find(b"\n", end)
    header = data[:end].decode("ascii", errors="replace").splitlines()
    body = data[nl + 1:]
    fmt, elements = "ascii", []
    for line in header:
        p = line.split()
        if not p:
            continue
        if p[0] == "format":
            fmt = p[1]
        elif p[0] == "element":
            elements.append([p[1], int(p[2]), []])
        elif p[0] == "property" and elements:
            elements[-1][2].append(p[1:])
    verts, faces = [], []
    if fmt == "ascii":
        lines = body.decode("utf-8", errors="replace").split("\n")
        li = 0
        for name, cnt, props in elements:
            names = [pp[-1] for pp in props]
            for _ in range(cnt):
                t = lines[li].split()
                li += 1
                if name == "vertex":
                    verts.append((float(t[names.index("x")]), float(t[names.index("y")]),
                                  float(t[names.index("z")])))
                elif name == "face":
                    n = int(t[0])
                    faces.extend(_triangulate([int(x) for x in t[1:1 + n]]))
    else:
        e = "<" if fmt == "binary_little_endian" else ">"
        pos = 0
        for name, cnt, props in elements:
            for _ in range(cnt):
                row = {}
                for pp in props:
                    if pp[0] == "list":
                        ct, it = _PLY_TYPES[pp[1]], _PLY_TYPES[pp[2]]
                        n = _struct.unpack_from(e + ct, body, pos)[0]
                        pos += _struct.calcsize(ct)
                        vals = _struct.unpack_from(e + it * n, body, pos)
                        pos += _struct.calcsize(it) * n
                        row[pp[-1]] = vals
                    else:
                        t = _PLY_TYPES[pp[0]]
                        row[pp[-1]] = _struct.unpack_from(e + t, body, pos)[0]
                        pos += _struct.calcsize(t)
                if name == "vertex":
                    verts.append((row["x"], row["y"], row["z"]))
                elif name == "face":
                    lst = row.get("vertex_indices") or row.get("vertex_index") or ()
                    faces.extend(_triangulate(list(lst)))
    if not verts:
        raise ValueError("PLY không có đỉnh")
    return verts, faces


_GLTF_COMP = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
              5125: ("I", 4), 5126: ("f", 4)}
_GLTF_NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def parse_gltf(path):
    """GLB hoặc glTF (.gltf + .bin / data URI). Bỏ qua animation/skin/vật liệu."""
    with open(path, "rb") as f:
        raw = f.read()
    glb_bin = None
    if raw[:4] == b"glTF":
        pos, js = 12, None
        while pos + 8 <= len(raw):
            ln, ctype = _struct.unpack_from("<II", raw, pos)
            chunk = raw[pos + 8:pos + 8 + ln]
            if ctype == 0x4E4F534A:
                js = json.loads(chunk.decode("utf-8"))
            elif ctype == 0x004E4942 and glb_bin is None:
                glb_bin = chunk
            pos += 8 + ln + (-ln % 4)
        if js is None:
            raise ValueError("GLB thiếu chunk JSON")
    else:
        js = json.loads(raw.decode("utf-8-sig"))
    bufs = []
    for b in js.get("buffers", []):
        uri = b.get("uri")
        if uri is None:
            bufs.append(glb_bin or b"")
        elif uri.startswith("data:"):
            bufs.append(base64.b64decode(uri.split(",", 1)[1]))
        else:
            with open(os.path.join(os.path.dirname(path), urllib.parse.unquote(uri)), "rb") as bf:
                bufs.append(bf.read())

    def read_acc(i):
        acc = js["accessors"][i]
        ch, size = _GLTF_COMP[acc["componentType"]]
        nc = _GLTF_NCOMP[acc["type"]]
        cnt = acc["count"]
        bv = js["bufferViews"][acc["bufferView"]] if "bufferView" in acc else None
        if bv is None:
            return [(0,) * nc] * cnt
        data = bufs[bv["buffer"]]
        start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        stride = bv.get("byteStride") or nc * size
        out = []
        for k in range(cnt):
            out.append(_struct.unpack_from("<" + ch * nc, data, start + k * stride))
        return out

    def node_matrix(n):
        if "matrix" in n:
            m = n["matrix"]
            return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
        t = n.get("translation", [0, 0, 0])
        q = n.get("rotation", [0, 0, 0, 1])
        s = n.get("scale", [1, 1, 1])
        x, y, z, w = q
        r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
             [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
             [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
        return [[r[0][0] * s[0], r[0][1] * s[1], r[0][2] * s[2], t[0]],
                [r[1][0] * s[0], r[1][1] * s[1], r[1][2] * s[2], t[1]],
                [r[2][0] * s[0], r[2][1] * s[1], r[2][2] * s[2], t[2]],
                [0, 0, 0, 1]]

    def mul(a, b):
        return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

    verts, faces = [], []
    ident = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]

    def emit_mesh(mi, m):
        for prim in js["meshes"][mi].get("primitives", []):
            if prim.get("mode", 4) not in (4, 5, 6):
                continue
            pos = read_acc(prim["attributes"]["POSITION"])
            base = len(verts)
            for (x, y, z) in pos:
                verts.append((m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3],
                              m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3],
                              m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3]))
            if "indices" in prim:
                idx = [t[0] for t in read_acc(prim["indices"])]
            else:
                idx = list(range(len(pos)))
            mode = prim.get("mode", 4)
            if mode == 4:
                tri = [(idx[i] + base, idx[i + 1] + base, idx[i + 2] + base)
                       for i in range(0, len(idx) - 2, 3)]
            elif mode == 5:
                tri = [(idx[i] + base, idx[i + 1] + base, idx[i + 2] + base)
                       if i % 2 == 0 else (idx[i + 1] + base, idx[i] + base, idx[i + 2] + base)
                       for i in range(len(idx) - 2)]
            else:
                tri = [(idx[0] + base, idx[i] + base, idx[i + 1] + base)
                       for i in range(1, len(idx) - 1)]
            faces.extend(tri)

    def walk(ni, parent, depth=0):
        if depth > 64:
            return
        n = js["nodes"][ni]
        m = mul(parent, node_matrix(n))
        if "mesh" in n:
            emit_mesh(n["mesh"], m)
        for c in n.get("children", []):
            walk(c, m, depth + 1)

    scenes = js.get("scenes")
    if scenes and js.get("nodes"):
        roots = scenes[js.get("scene", 0)].get("nodes", [])
        for r in roots:
            walk(r, ident)
    else:
        for mi in range(len(js.get("meshes", []))):
            emit_mesh(mi, ident)
    if not verts:
        raise ValueError("glTF không có mesh nào")
    return verts, faces


#  FBX (nhị phân + ascii cơ bản): chỉ lấy hình học (Vertices / PolygonVertexIndex)
def _fbx_read_binary(data):
    ver = _struct.unpack_from("<I", data, 23)[0]
    big = ver >= 7500

    def read_node(pos):
        if big:
            end, nprops, plen = _struct.unpack_from("<QQQ", data, pos)
            pos += 24
        else:
            end, nprops, plen = _struct.unpack_from("<III", data, pos)
            pos += 12
        nlen = data[pos]
        pos += 1
        if end == 0:
            return None, pos
        name = data[pos:pos + nlen].decode("latin-1")
        pos += nlen
        props = []
        pend = pos + plen
        for _ in range(nprops):
            t = chr(data[pos])
            pos += 1
            if t in "YCIFDL":
                fmt = {"Y": "<h", "C": "<?", "I": "<i", "F": "<f", "D": "<d", "L": "<q"}[t]
                props.append(_struct.unpack_from(fmt, data, pos)[0])
                pos += _struct.calcsize(fmt)
            elif t in "fdlib":
                cnt, enc, clen = _struct.unpack_from("<III", data, pos)
                pos += 12
                raw = data[pos:pos + clen]
                pos += clen
                if enc == 1:
                    raw = _zlib.decompress(raw)
                code = {"f": "f", "d": "d", "l": "q", "i": "i", "b": "?"}[t]
                props.append(_struct.unpack("<%d%s" % (cnt, code), raw[:cnt * _struct.calcsize(code)]))
            elif t in "SR":
                ln = _struct.unpack_from("<I", data, pos)[0]
                pos += 4
                props.append(bytes(data[pos:pos + ln]))
                pos += ln
            else:
                raise ValueError("FBX: kiểu thuộc tính lạ %r" % t)
        pos = pend
        children = []
        while pos < end:
            ch, pos = read_node(pos)
            if ch is None:
                break
            children.append(ch)
        return (name, props, children), end

    pos, nodes = 27, []
    while pos < len(data) - 13:
        node, pos = read_node(pos)
        if node is None:
            break
        nodes.append(node)
    return nodes


def _fbx_find_geometries(nodes):
    out = []

    def rec(ns):
        for name, props, ch in ns:
            if name == "Geometry":
                vs = pi = None
                for n2, p2, _c in ch:
                    if n2 == "Vertices" and p2:
                        vs = p2[0]
                    elif n2 == "PolygonVertexIndex" and p2:
                        pi = p2[0]
                if vs and pi:
                    out.append((vs, pi))
            rec(ch)
    rec(nodes)
    return out


def _fbx_ascii_geoms(text):
    out = []
    for m in re.finditer(r"Vertices:\s*\*\d+\s*\{\s*a:\s*([^}]*)\}", text):
        vs = [float(x) for x in m.group(1).replace("\n", "").split(",") if x.strip()]
        rest = text[m.end():m.end() + 20_000_000]
        m2 = re.search(r"PolygonVertexIndex:\s*\*\d+\s*\{\s*a:\s*([^}]*)\}", rest)
        if m2:
            pi = [int(x) for x in m2.group(1).replace("\n", "").split(",") if x.strip()]
            out.append((vs, pi))
    return out


def parse_fbx(path):
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith(b"Kaydara FBX Binary"):
        geoms = _fbx_find_geometries(_fbx_read_binary(data))
    else:
        geoms = _fbx_ascii_geoms(data.decode("utf-8", errors="replace"))
    verts, faces = [], []
    for vs, pi in geoms:
        base = len(verts)
        for i in range(0, len(vs) - 2, 3):
            verts.append((vs[i], vs[i + 1], vs[i + 2]))
        poly = []
        for v in pi:
            if v < 0:
                poly.append((~v) + base)
                if len(poly) >= 3:
                    faces.extend(_triangulate(poly))
                poly = []
            else:
                poly.append(v + base)
    if not verts:
        raise ValueError("Không tìm thấy hình học trong FBX (có thể là file chỉ có animation/skeleton)")
    return verts, faces


def parse_mesh_any(path):
    """Đọc mesh theo đuôi. Đuôi lạ: thử trimesh (nếu đã cài). Trả về (verts, faces, ghi_chú)."""
    ext = os.path.splitext(path)[1].lower()
    fn = {".glb": parse_gltf, ".gltf": parse_gltf, ".obj": parse_obj, ".stl": parse_stl,
          ".ply": parse_ply, ".fbx": parse_fbx, ".off": parse_off}.get(ext)
    err = None
    if fn:
        try:
            v, f = fn(path)
            return v, f, ""
        except Exception as e:  # noqa: BLE001
            err = e
    try:
        import trimesh  # noqa: PLC0415
        sc = trimesh.load(path, force="mesh")
        v = [tuple(map(float, x)) for x in sc.vertices]
        f = [tuple(int(i) for i in x) for x in sc.faces]
        if v:
            return v, f, "(đọc bằng trimesh)"
    except Exception as e2:  # noqa: BLE001
        err = err or e2
    raise ValueError(str(err) if err else "Định dạng mesh chưa hỗ trợ")


def mesh_stats(verts, faces):
    if not verts:
        return "trống"
    mn = [min(v[i] for v in verts) for i in range(3)]
    mx = [max(v[i] for v in verts) for i in range(3)]
    return "%d đỉnh, %d tam giác, kích thước %.3g × %.3g × %.3g" % (
        len(verts), len(faces), mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2])


# PyTorch .pt / .pth: đọc cấu trúc bằng unpickler GIẢ (không import, không chạy code)
PICKLE_DANGEROUS = {
    "os", "posix", "nt", "subprocess", "sys", "socket", "shutil", "builtins", "importlib",
    "runpy", "pty", "ctypes", "webbrowser", "requests", "urllib", "http", "commands", "pip",
}
PICKLE_DANGEROUS_NAMES = {"eval", "exec", "compile", "system", "popen", "__import__", "open",
                          "getattr", "setattr"}
_TORCH_DTYPES = {"Float": "float32", "Double": "float64", "Half": "float16", "BFloat16": "bfloat16",
                 "Long": "int64", "Int": "int32", "Short": "int16", "Char": "int8", "Byte": "uint8",
                 "Bool": "bool", "ComplexFloat": "complex64", "ComplexDouble": "complex128"}
_DTYPE_BYTES = {"float32": 4, "float64": 8, "float16": 2, "bfloat16": 2, "int64": 8, "int32": 4,
                "int16": 2, "int8": 1, "uint8": 1, "bool": 1, "complex64": 8, "complex128": 16}


class _PStub:
    _qual = "?"

    def __init__(self, *a, **k):
        self.args, self.kw, self.state = a, k, None

    def __setstate__(self, st):
        self.state = st

    def __repr__(self):
        return "<%s>" % self._qual

    def __call__(self, *a, **k):
        return _PStub(*a, **k)


class _SafeUnpickler(_pickle.Unpickler):
    def __init__(self, f, record):
        super().__init__(f)
        self.record = record

    def find_class(self, module, name):
        self.record.append((module, name))
        if module == "collections" and name == "OrderedDict":
            return _collections.OrderedDict
        if module == "builtins" and name in ("set", "frozenset", "list", "dict", "tuple", "slice"):
            return {"set": set, "frozenset": frozenset, "list": list, "dict": dict,
                    "tuple": tuple, "slice": slice}[name]
        return type(name, (_PStub,), {"_qual": "%s.%s" % (module, name)})

    def persistent_load(self, pid):
        return ("__storage__", pid)


def _tensor_info(obj):
    """Nếu obj là lời gọi _rebuild_tensor*, trả về (shape, dtype, numel) - ngược lại None."""
    if isinstance(obj, _PStub) and "rebuild_tensor" in obj._qual and len(obj.args) >= 3:
        st, shape = obj.args[0], obj.args[2]
        dtype = "?"
        if isinstance(st, tuple) and len(st) == 2 and isinstance(st[1], tuple):
            pid = st[1]
            for item in pid:
                q = getattr(item, "_qual", "")
                if q.endswith("Storage"):
                    dtype = _TORCH_DTYPES.get(q.split(".")[-1].replace("Storage", ""), q)
        try:
            shape = tuple(int(x) for x in shape)
        except (TypeError, ValueError):
            return None
        n = 1
        for s in shape:
            n *= s
        return shape, dtype, n
    return None


def inspect_torch_file(path):
    """Trả về dict: kind, entries(list zip), globals(list), danger(list), tensors[(tên, shape, dtype, n)],
    tree_text, total_params, total_bytes."""
    info = {"kind": "", "zip": [], "globals": [], "danger": [], "tensors": [],
            "text": "", "params": 0, "bytes": 0, "error": ""}
    record = []
    pkl = None
    if zipfile.is_zipfile(path):
        info["kind"] = "PyTorch zip (torch.save mới)"
        with zipfile.ZipFile(path) as z:
            info["zip"] = [(i.filename, i.file_size) for i in z.infolist()]
            cand = [i.filename for i in z.infolist() if i.filename.endswith("data.pkl")]
            if cand:
                pkl = z.read(cand[0])
    else:
        info["kind"] = "PyTorch legacy / pickle thuần"
        with open(path, "rb") as f:
            pkl = f.read(64 * 1024 * 1024)
    if pkl is None:
        info["error"] = "Không thấy data.pkl trong file"
        return info
    try:
        obj = _SafeUnpickler(io.BytesIO(pkl), record).load()
    except Exception as e:  # noqa: BLE001
        info["error"] = "Không đọc được pickle: %s" % e
        try:
            ops = []
            for op, arg, _pos in _pickletools.genops(pkl):
                if op.name in ("GLOBAL", "STACK_GLOBAL") and arg:
                    ops.append(str(arg))
            record.extend(tuple(a.split(" ", 1)) if " " in a else ("?", a) for a in ops[:200])
        except Exception:  # noqa: BLE001
            pass
        obj = None
    seen = []
    for g in record:
        if g not in seen:
            seen.append(g)
    info["globals"] = ["%s.%s" % g for g in seen]
    for m, n in seen:
        if m.split(".")[0] in PICKLE_DANGEROUS or n in PICKLE_DANGEROUS_NAMES:
            info["danger"].append("%s.%s" % (m, n))
    lines = []

    def walk(o, name, depth):
        if len(info["tensors"]) > 20000 or depth > 12:
            return
        ti = _tensor_info(o)
        if ti:
            shape, dtype, n = ti
            info["tensors"].append((name, shape, dtype, n))
            info["params"] += n
            info["bytes"] += n * _DTYPE_BYTES.get(dtype, 4)
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, "%s.%s" % (name, k) if name else str(k), depth + 1)
        elif isinstance(o, (list, tuple)):
            for i, v in enumerate(o[:200]):
                walk(v, "%s[%d]" % (name, i), depth + 1)
        elif isinstance(o, _PStub):
            if isinstance(o.state, dict):
                walk(o.state, name, depth + 1)
            lines.append("%s: %r" % (name or "(gốc)", o))
        elif isinstance(o, (int, float, str, bool)) or o is None:
            lines.append("%s = %r" % (name or "(gốc)", o if not isinstance(o, str) else o[:200]))
    if obj is not None:
        walk(obj, "", 0)
    info["text"] = "\n".join(lines[:400])
    return info


# Intel HEX (.hex) - firmware vi điều khiển
def parse_intel_hex(text):
    """Trả về dict: segments[(addr, bytes)], errors[], start, total. Kiểm tra checksum."""
    mem, errors, base, start = {}, [], 0, None
    nrec = 0
    for ln, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if not line.startswith(":"):
            errors.append("Dòng %d: không bắt đầu bằng ':'" % ln)
            continue
        try:
            raw = bytes.fromhex(line[1:])
        except ValueError:
            errors.append("Dòng %d: ký tự hex sai" % ln)
            continue
        if len(raw) < 5 or raw[0] != len(raw) - 5:
            errors.append("Dòng %d: độ dài record sai" % ln)
            continue
        if sum(raw) & 0xFF:
            errors.append("Dòng %d: sai checksum" % ln)
        nrec += 1
        n, addr, rt = raw[0], (raw[1] << 8) | raw[2], raw[3]
        data = raw[4:4 + n]
        if rt == 0:
            for i, b in enumerate(data):
                mem[base + addr + i] = b
        elif rt == 1:
            break
        elif rt == 2 and n == 2:
            base = ((data[0] << 8) | data[1]) << 4
        elif rt == 4 and n == 2:
            base = ((data[0] << 8) | data[1]) << 16
        elif rt in (3, 5) and n == 4:
            start = int.from_bytes(data, "big")
    segs, cur = [], None
    for a in sorted(mem):
        if cur and a == cur[0] + len(cur[1]):
            cur[1].append(mem[a])
        else:
            cur = [a, bytearray([mem[a]])]
            segs.append(cur)
    return {"segments": [(a, bytes(b)) for a, b in segs], "errors": errors,
            "start": start, "total": len(mem), "records": nrec}


# Kiểm tra API plugin TRƯỚC khi nhập / nạp (phân tích tĩnh bằng ast - không chạy code)
API_RISKY_CALLS = {
    "os.system": "chạy lệnh shell", "os.popen": "chạy lệnh shell", "os.remove": "xóa file",
    "os.unlink": "xóa file", "os.rmdir": "xóa thư mục", "shutil.rmtree": "xóa cả thư mục",
    "subprocess.run": "chạy chương trình ngoài", "subprocess.Popen": "chạy chương trình ngoài",
    "subprocess.call": "chạy chương trình ngoài", "subprocess.check_output": "chạy chương trình ngoài",
    "eval": "eval()", "exec": "exec()", "compile": "compile()", "__import__": "import động",
    "socket.socket": "mở kết nối mạng", "urllib.request.urlopen": "tải dữ liệu từ mạng",
    "requests.get": "tải dữ liệu từ mạng", "requests.post": "gửi dữ liệu lên mạng",
    "ctypes.CDLL": "gọi thư viện native", "winreg.SetValue": "ghi registry",
}


def _stdlib_names():
    names = set(getattr(sys, "stdlib_module_names", ()))
    return names | set(sys.builtin_module_names) | {"__future__"}


def check_plugin_source(source, filename="plugin.py", api_methods=(), app_api_version="0",
                        module_exists=None):
    """Trả về dict {ok, errors[], warnings[], notes[], missing_modules[], api_used[], unknown_api[],
    requires, risky[]}.  errors = lỗi chắc chắn (plugin sẽ hỏng), warnings = nên xem lại."""
    rep = {"ok": True, "errors": [], "warnings": [], "notes": [], "missing_modules": [],
           "api_used": [], "unknown_api": [], "requires": None, "risky": [], "has_register": False,
           "imports": []}
    try:
        tree = ast.parse(source, filename)
    except SyntaxError as e:
        rep["errors"].append("Lỗi cú pháp dòng %s: %s" % (e.lineno, e.msg))
        rep["ok"] = False
        return rep
    std = _stdlib_names()
    known = set(api_methods)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "register":
            rep["has_register"] = True
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in ("REQUIRES_API", "API_VERSION", "MIN_API"):
                    try:
                        rep["requires"] = str(ast.literal_eval(node.value))
                    except Exception:  # noqa: BLE001
                        pass
    if not rep["has_register"]:
        rep["errors"].append("Thiếu hàm register(api) - app sẽ không nạp được plugin này.")
    # tên tham số của register (thường là api)
    api_name = "api"
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "register" and node.args.args:
            api_name = node.args.args[0].arg
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module.split(".")[0])
    rep["imports"] = sorted(mods)
    for m in sorted(mods):
        if m in std or m == "PyQt5":
            continue
        ok = True
        if module_exists:
            try:
                ok = bool(module_exists(m))
            except Exception:  # noqa: BLE001
                ok = False
        if not ok:
            rep["missing_modules"].append(m)
    used = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                and node.value.id == api_name:
            used.setdefault(node.attr, node.lineno)
    rep["api_used"] = sorted(used)
    for name, line in sorted(used.items()):
        if known and name not in known:
            rep["unknown_api"].append((name, line))
    for name, line in rep["unknown_api"]:
        rep["errors"].append("Dòng %d: api.%s() không tồn tại trong API %s của app." % (
            line, name, app_api_version))
    # so sánh phiên bản API
    if rep["requires"]:
        try:
            need = tuple(int(x) for x in re.findall(r"\d+", rep["requires"])[:3])
            have = tuple(int(x) for x in re.findall(r"\d+", str(app_api_version))[:3])
            if need > have:
                rep["errors"].append("Plugin yêu cầu API %s nhưng app chỉ có %s." % (
                    rep["requires"], app_api_version))
        except ValueError:
            rep["warnings"].append("Không hiểu khai báo REQUIRES_API = %r" % rep["requires"])
    else:
        rep["notes"].append("Plugin chưa khai báo REQUIRES_API (ví dụ REQUIRES_API = \"2.0\").")
    # lời gọi rủi ro
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            parts = []
            while isinstance(f, ast.Attribute):
                parts.append(f.attr)
                f = f.value
            if isinstance(f, ast.Name):
                parts.append(f.id)
            dotted = ".".join(reversed(parts))
            if dotted in API_RISKY_CALLS:
                rep["risky"].append((dotted, API_RISKY_CALLS[dotted], node.lineno))
    for dotted, why, line in rep["risky"][:30]:
        rep["warnings"].append("Dòng %d: %s() - %s." % (line, dotted, why))
    if rep["missing_modules"]:
        rep["warnings"].append("Thiếu thư viện: " + ", ".join(rep["missing_modules"])
                               + " (app có thể cài giúp).")
    rep["ok"] = not rep["errors"]
    return rep


def format_plugin_report(rep, name):
    L = ["Kiểm tra plugin '%s'" % name, ""]
    L.append("Kết quả: " + ("ĐẠT ✔" if rep["ok"] else "CÓ LỖI ✘"))
    if rep["api_used"]:
        L.append("API dùng: " + ", ".join("api." + a for a in rep["api_used"]))
    if rep["imports"]:
        L.append("Thư viện import: " + ", ".join(rep["imports"]))
    for title, key in (("LỖI", "errors"), ("CẢNH BÁO", "warnings"), ("GHI CHÚ", "notes")):
        if rep[key]:
            L.append("")
            L.append(title + ":")
            L.extend("  • " + x for x in rep[key])
    return "\n".join(L)


def inspect_safetensors(path):
    """Đọc header .safetensors (JSON) - không nạp dữ liệu tensor."""
    info = {"kind": "safetensors", "zip": [], "globals": [], "danger": [], "tensors": [],
            "text": "", "params": 0, "bytes": 0, "error": ""}
    with open(path, "rb") as f:
        n = _struct.unpack("<Q", f.read(8))[0]
        if n > 100 * 1024 * 1024:
            info["error"] = "Header quá lớn - không phải safetensors?"
            return info
        hdr = json.loads(f.read(n).decode("utf-8"))
    names = {"F32": "float32", "F64": "float64", "F16": "float16", "BF16": "bfloat16", "I64": "int64",
             "I32": "int32", "I16": "int16", "I8": "int8", "U8": "uint8", "BOOL": "bool"}
    meta = hdr.pop("__metadata__", None)
    for k, v in hdr.items():
        shape = tuple(v.get("shape", ()))
        dt = names.get(v.get("dtype"), str(v.get("dtype")))
        c = 1
        for s in shape:
            c *= s
        info["tensors"].append((k, shape, dt, c))
        info["params"] += c
        info["bytes"] += c * _DTYPE_BYTES.get(dt, 4)
    if meta:
        info["text"] = "\n".join("%s = %s" % (k, str(v)[:200]) for k, v in meta.items())
    return info


# PHẦN 2A - Registry trình mở file + Ảnh / Hex / PyTorch / Intel HEX
from PyQt5.QtWidgets import (
    QSlider, QDoubleSpinBox, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QAbstractItemView,
)
from PyQt5.QtGui import QImageReader, QMovie, QTransform

try:
    from PyQt5.QtSvg import QSvgRenderer as _QSvgRenderer
except ImportError:  # pragma: no cover
    _QSvgRenderer = None


def cfg_get(win, key, default=None, typ=None):
    """Đọc QSettings và ép kiểu (QSettings hay trả về chuỗi 'true'/'false')."""
    try:
        v = win.settings.value(key, default)
    except Exception:  # noqa: BLE001
        return default
    if typ is bool:
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes", "on")
        return bool(v)
    if typ is int:
        try:
            return int(v)
        except (TypeError, ValueError):
            return default
    if typ is float:
        try:
            return float(v)
        except (TypeError, ValueError):
            return default
    return v


# Registry trình mở file
OPENERS = []      # [{key,name,exts,fn,owner,sniff}]


def register_opener(key, name, exts, fn, owner=None, sniff=None):
    """fn(win, path) -> True nếu đã mở xong, False để thử trình khác.
    sniff(head_bytes) -> bool: nhận file theo nội dung (dùng cho file không có đuôi quen)."""
    any_ = "*" in list(exts)
    exts = [e.lower() if e.startswith(".") else "." + e.lower() for e in exts if e and e != "*"]
    ent = {"key": key, "name": name, "exts": exts, "fn": fn, "owner": owner, "sniff": sniff,
           "any": any_}
    OPENERS[:] = [o for o in OPENERS if o["key"] != key]
    OPENERS.append(ent)
    return ent


def unregister_opener(ent):
    if ent in OPENERS:
        OPENERS.remove(ent)


def _opener_config(win):
    try:
        d = json.loads(win.settings.value("openers/config", "{}") or "{}")
        return d if isinstance(d, dict) else {}
    except (ValueError, TypeError):
        return {}


def opener_exts(win, ent):
    c = _opener_config(win).get(ent["key"], {})
    if isinstance(c.get("exts"), str):
        return [e if e.startswith(".") else "." + e for e in re.split(r"[\s,;]+", c["exts"].lower()) if e]
    return ent["exts"]


def opener_enabled(win, ent):
    return bool(_opener_config(win).get(ent["key"], {}).get("enabled", True))


def candidate_openers(win, path, head=b"", by_ext=True, by_sniff=True):
    ext = os.path.splitext(path)[1].lower()
    plug = [o for o in OPENERS if o["owner"]]
    built = [o for o in OPENERS if not o["owner"]]
    out = []
    for o in plug + built:
        if not opener_enabled(win, o):
            continue
        if by_ext and ext and ext in opener_exts(win, o):
            out.append(o)
        elif by_sniff and o["any"]:
            out.append(o)
        elif by_sniff and o["sniff"]:
            try:
                if o["sniff"](head):
                    out.append(o)
            except Exception:  # noqa: BLE001
                pass
    return out


def run_openers(win, path, head=b"", by_ext=True, by_sniff=True):
    for o in candidate_openers(win, path, head, by_ext, by_sniff):
        try:
            if o["fn"](win, path):
                return True
        except Exception:  # noqa: BLE001
            win.terminal.appendPlainText(f"[trình mở '{o['name']}'] LỖI:\n" + traceback.format_exc())
    return False


def read_head(path, n=64):
    try:
        with open(path, "rb") as f:
            return f.read(n)
    except OSError:
        return b""


def _std_dialog(win, dlg):
    dlg.setAttribute(Qt.WA_DeleteOnClose)
    dlg.show()
    dlg.raise_()
    if not hasattr(win, "_extra_dialogs"):
        win._extra_dialogs = []
    win._extra_dialogs.append(dlg)
    win._extra_dialogs = [d for d in win._extra_dialogs if _alive(d)]
    return dlg


def _alive(w):
    try:
        w.isVisible()
        return True
    except RuntimeError:
        return False


def mono_font(size=10):
    f = QFont("Consolas")
    f.setStyleHint(QFont.Monospace)
    f.setFixedPitch(True)
    f.setPointSize(size)
    return f


def human_size(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return ("%d %s" % (n, u)) if u == "B" else ("%.1f %s" % (n, u))
        n /= 1024.0


# Trình xem ảnh nâng cấp
def image_exts():
    s = {"." + bytes(x).decode().lower() for x in QImageReader.supportedImageFormats()}
    s |= {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico"}
    if _QSvgRenderer is not None:
        s.add(".svg")
    return s


class _ImageView(QGraphicsView):
    zoomChanged = pyqtSignal(float)
    hoverPixel = pyqtSignal(int, int)
    toggled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.item = QGraphicsPixmapItem()
        self.scene().addItem(self.item)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setFrameShape(QFrame.NoFrame)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.bg = "checker"
        self.zoom = 1.0
        self.smooth = True

    def drawBackground(self, p, rect):
        cols = {"dark": "#1e1e1e", "light": "#f2f2f2", "black": "#000000", "checker": "#2a2a2a"}
        p.fillRect(rect, QColor(cols.get(self.bg, "#2a2a2a")))
        if self.bg != "checker" or self.item.pixmap().isNull():
            return
        area = self.item.sceneBoundingRect().intersected(rect)
        if area.isEmpty():
            return
        s = 10.0 / max(self.zoom, 1e-6)
        c1, c2 = QColor("#cfcfcf"), QColor("#9a9a9a")
        x0 = self.item.sceneBoundingRect().left()
        y0 = self.item.sceneBoundingRect().top()
        i0, j0 = int((area.left() - x0) // s), int((area.top() - y0) // s)
        i1, j1 = int((area.right() - x0) // s) + 1, int((area.bottom() - y0) // s) + 1
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                r = QRectF(x0 + i * s, y0 + j * s, s, s).intersected(area)
                if not r.isEmpty():
                    p.fillRect(r, c1 if (i + j) % 2 == 0 else c2)

    def set_zoom(self, z):
        z = max(0.01, min(float(z), 64.0))
        self.zoom = z
        self.resetTransform()
        self.scale(z, z)
        self.item.setTransformationMode(
            Qt.SmoothTransformation if (self.smooth and z < 4) else Qt.FastTransformation)
        self.viewport().update()
        self.zoomChanged.emit(z)

    def wheelEvent(self, e):
        k = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self.set_zoom(self.zoom * k)

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        pt = self.item.mapFromScene(self.mapToScene(e.pos()))
        self.hoverPixel.emit(int(pt.x()), int(pt.y()))

    def mouseDoubleClickEvent(self, e):
        self.toggled.emit()


class ImageViewerDialog(QDialog):
    """Trình xem ảnh: zoom/kéo, xoay/lật, nền caro, duyệt ảnh trong thư mục, slideshow,
    GIF động, SVG, bút chọn màu (hover), copy/lưu."""

    def __init__(self, parent, path):
        super().__init__(parent)
        self.win = parent
        self.setWindowTitle(os.path.basename(path))
        self.resize(980, 700)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.path = path
        self.img = QImage()
        self.orig = QImage()
        self.rot, self.fh, self.fv = 0, False, False
        self.movie = None
        self.files, self.idx = [], 0
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        bar = QHBoxLayout()
        self.view = _ImageView()
        self.view.smooth = cfg_get(parent, "img/smooth", True, bool)
        self.view.bg = cfg_get(parent, "img/bg", "checker") or "checker"
        self.fit_cap = cfg_get(parent, "img/fit_cap", True, bool)

        def btn(text, fn, tip=""):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(lambda _=False: fn())
            bar.addWidget(b)
            return b
        btn("◀", lambda: self.step(-1), "Ảnh trước (←)")
        btn("▶", lambda: self.step(1), "Ảnh sau (→)")
        btn("−", lambda: self.view.set_zoom(self.view.zoom / 1.25), "Thu nhỏ (-)")
        btn("+", lambda: self.view.set_zoom(self.view.zoom * 1.25), "Phóng to (+)")
        btn("1:1", lambda: self.view.set_zoom(1.0), "100% (0)")
        btn("Vừa", self.fit, "Vừa khung (F)")
        btn("Lấp đầy", lambda: self.fit(cap=False), "Phóng to lấp khung")
        btn("⟲", lambda: self.rotate(-90), "Xoay trái (L)")
        btn("⟳", lambda: self.rotate(90), "Xoay phải (R)")
        btn("⇋", lambda: self.flip(True), "Lật ngang (H)")
        btn("⇅", lambda: self.flip(False), "Lật dọc (V)")
        self.bg_btn = btn("Nền", self.cycle_bg, "Đổi nền: caro / tối / sáng / đen (B)")
        self.show_btn = btn("▶ Slideshow", self.toggle_show, "Space")
        btn("Copy", self.copy_image, "Ctrl+C")
        btn("Lưu...", self.save_as)
        btn("⛶", self.toggle_full, "Toàn màn hình (F11)")
        bar.addStretch(1)
        lay.addLayout(bar)
        lay.addWidget(self.view, 1)
        row = QHBoxLayout()
        self.info = QLabel("")
        self.pix_info = QLabel("")
        self.pix_info.setMinimumWidth(260)
        row.addWidget(self.info, 1)
        row.addWidget(self.pix_info)
        lay.addLayout(row)
        self.view.zoomChanged.connect(lambda z: self._update_info())
        self.view.hoverPixel.connect(self._hover)
        self.view.toggled.connect(lambda: self.fit() if abs(self.view.zoom - 1.0) < 1e-6
                                  else self.view.set_zoom(1.0))
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.step(1, wrap=True))
        self._scan_folder()
        self.load(path)

    #  nạp ảnh
    def _scan_folder(self):
        d = os.path.dirname(self.path) or "."
        exts = image_exts()
        try:
            names = [n for n in os.listdir(d) if os.path.splitext(n)[1].lower() in exts]
        except OSError:
            names = [os.path.basename(self.path)]

        def nat(s):
            return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]
        names.sort(key=nat)
        self.files = [os.path.join(d, n) for n in names]
        try:
            self.idx = [os.path.normcase(f) for f in self.files].index(os.path.normcase(self.path))
        except ValueError:
            self.files.append(self.path)
            self.idx = len(self.files) - 1

    def load(self, path):
        self.path = path
        self.setWindowTitle(os.path.basename(path))
        if self.movie is not None:
            self.movie.stop()
            self.movie = None
        self.rot, self.fh, self.fv = 0, False, False
        ext = os.path.splitext(path)[1].lower()
        img = QImage()
        if ext == ".svg" and _QSvgRenderer is not None:
            r = _QSvgRenderer(path)
            sz = r.defaultSize()
            if sz.isEmpty():
                sz = QSize(512, 512)
            k = max(1.0, 1600.0 / max(sz.width(), sz.height()))
            img = QImage(int(sz.width() * k), int(sz.height() * k), QImage.Format_ARGB32_Premultiplied)
            img.fill(0)
            p = QPainter(img)
            r.render(p)
            p.end()
        else:
            rd = QImageReader(path)
            rd.setAutoTransform(True)
            img = rd.read()
            if ext == ".gif" and rd.imageCount() > 1:
                self.movie = QMovie(path)
                self.movie.frameChanged.connect(self._movie_frame)
                self.movie.start()
        self.orig = img
        self._rebuild(refit=True)

    def _movie_frame(self, _n):
        if self.movie is None:
            return
        pm = self.movie.currentPixmap()
        if not pm.isNull():
            self.img = pm.toImage()
            self.view.item.setPixmap(pm)

    def _rebuild(self, refit=False):
        if self.orig.isNull():
            self.view.item.setPixmap(QPixmap())
            self.info.setText("Không đọc được ảnh (định dạng chưa được Qt hỗ trợ).")
            return
        im = self.orig
        if self.fh or self.fv:
            im = im.mirrored(self.fh, self.fv)
        if self.rot:
            im = im.transformed(QTransform().rotate(self.rot), Qt.SmoothTransformation)
        self.img = im
        self.view.item.setPixmap(QPixmap.fromImage(im))
        self.view.scene().setSceneRect(QRectF(im.rect()))
        if refit:
            QTimer.singleShot(0, self.fit)
        self._update_info()

    def fit(self, cap=None):
        if self.img.isNull():
            return
        cap = self.fit_cap if cap is None else cap
        vp = self.view.viewport().size()
        z = min(vp.width() / max(1, self.img.width()), vp.height() / max(1, self.img.height()))
        self.view.set_zoom(min(z, 1.0) if cap else z)
        self.view.centerOn(self.view.item)

    def _update_info(self):
        if self.img.isNull():
            return
        try:
            size = os.path.getsize(self.path)
        except OSError:
            size = 0
        extra = "  •  GIF động" if self.movie is not None else ""
        self.info.setText("%d/%d  %s  •  %d×%d px  •  %s  •  %d%%%s" % (
            self.idx + 1, len(self.files), os.path.basename(self.path), self.img.width(),
            self.img.height(), human_size(size), round(self.view.zoom * 100), extra))

    def _hover(self, x, y):
        if self.img.isNull() or not (0 <= x < self.img.width() and 0 <= y < self.img.height()):
            self.pix_info.setText("")
            return
        c = self.img.pixelColor(x, y)
        self.pix_info.setText("(%d, %d)  %s  rgba(%d,%d,%d,%d)" % (
            x, y, c.name().upper(), c.red(), c.green(), c.blue(), c.alpha()))

    #  thao tác
    def step(self, d, wrap=True):
        if len(self.files) < 2:
            return
        self.idx = (self.idx + d) % len(self.files)
        self.load(self.files[self.idx])

    def rotate(self, deg):
        if self.movie is None:
            self.rot = (self.rot + deg) % 360
            self._rebuild(refit=True)

    def flip(self, horizontal):
        if self.movie is None:
            if horizontal:
                self.fh = not self.fh
            else:
                self.fv = not self.fv
            self._rebuild()

    def cycle_bg(self):
        order = ["checker", "dark", "light", "black"]
        self.view.bg = order[(order.index(self.view.bg) + 1) % 4]
        self.view.viewport().update()

    def toggle_show(self):
        if self.timer.isActive():
            self.timer.stop()
            self.show_btn.setText("▶ Slideshow")
        else:
            self.timer.start(max(1, cfg_get(self.win, "img/slide_secs", 3, int)) * 1000)
            self.show_btn.setText("⏸ Dừng")

    def toggle_full(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def copy_image(self):
        if not self.img.isNull():
            QApplication.clipboard().setImage(self.img)
            self.pix_info.setText("Đã copy ảnh")

    def save_as(self):
        if self.img.isNull():
            return
        p, _ = QFileDialog.getSaveFileName(self, "Lưu ảnh", os.path.splitext(self.path)[0] + "_edit.png",
                                           "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;WebP (*.webp)")
        if p and not self.img.save(p):
            QMessageBox.warning(self, "Lưu ảnh", "Không lưu được: " + p)

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key_Left:
            self.step(-1)
        elif k == Qt.Key_Right:
            self.step(1)
        elif k in (Qt.Key_Plus, Qt.Key_Equal):
            self.view.set_zoom(self.view.zoom * 1.25)
        elif k == Qt.Key_Minus:
            self.view.set_zoom(self.view.zoom / 1.25)
        elif k == Qt.Key_0:
            self.view.set_zoom(1.0)
        elif k == Qt.Key_F:
            self.fit()
        elif k == Qt.Key_R:
            self.rotate(90)
        elif k == Qt.Key_L:
            self.rotate(-90)
        elif k == Qt.Key_H:
            self.flip(True)
        elif k == Qt.Key_V:
            self.flip(False)
        elif k == Qt.Key_B:
            self.cycle_bg()
        elif k == Qt.Key_Space:
            self.toggle_show()
        elif k == Qt.Key_F11:
            self.toggle_full()
        elif k == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        elif k == Qt.Key_C and (e.modifiers() & Qt.ControlModifier):
            self.copy_image()
        else:
            super().keyPressEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if abs(self.view.zoom - 1.0) > 1e-6 and getattr(self, "_auto_fit", False):
            self.fit()

    def closeEvent(self, e):
        self.timer.stop()
        if self.movie is not None:
            self.movie.stop()
        super().closeEvent(e)


# Hex viewer: mở được MỌI file (đọc theo trang nên file lớn vẫn nhẹ)
class HexViewerDialog(QDialog):
    PAGE = 16 * 2048

    def __init__(self, parent, path):
        super().__init__(parent)
        self.win = parent
        self.path = path
        self.size = os.path.getsize(path)
        self.page_off = 0
        self.setWindowTitle("Hex - " + os.path.basename(path))
        self.resize(900, 640)
        lay = QVBoxLayout(self)
        head = read_head(path, 64)
        self.title = QLabel("%s  •  %s  •  Loại: %s" % (
            os.path.basename(path), human_size(self.size), sniff_file_type(head)))
        self.title.setWordWrap(True)
        lay.addWidget(self.title)
        row = QHBoxLayout()
        for text, fn in (("⏮", lambda: self.goto(0)), ("◀ Trang", lambda: self.goto(self.page_off - self.PAGE)),
                         ("Trang ▶", lambda: self.goto(self.page_off + self.PAGE)),
                         ("⏭", lambda: self.goto(self.size))):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, f=fn: f())
            row.addWidget(b)
        self.off_edit = QLineEdit()
        self.off_edit.setPlaceholderText("Tới offset (vd 0x1F40 hoặc 8000)")
        self.off_edit.returnPressed.connect(self._goto_edit)
        row.addWidget(self.off_edit, 1)
        lay.addLayout(row)
        row2 = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(["Hex (DE AD BE EF)", "Text UTF-8", "Text UTF-16"])
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Tìm trong cả file...")
        self.find_edit.returnPressed.connect(lambda: self.find(1))
        row2.addWidget(self.mode)
        row2.addWidget(self.find_edit, 1)
        for text, fn in (("Tìm tiếp", lambda: self.find(1)), ("Tìm lùi", lambda: self.find(-1)),
                         ("Strings → tab", self.extract_strings), ("SHA-256", self.sha),
                         ("Mở bằng...", self.open_with)):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, f=fn: f())
            row2.addWidget(b)
        lay.addLayout(row2)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(mono_font(10))
        self.text.setLineWrapMode(QPlainTextEdit.NoWrap)
        lay.addWidget(self.text, 1)
        self.status = QLabel("")
        lay.addWidget(self.status)
        self.goto(0)

    def goto(self, off):
        off = max(0, min(off, max(0, self.size - 1)))
        off -= off % 16
        self.page_off = off
        with open(self.path, "rb") as f:
            f.seek(off)
            data = f.read(self.PAGE)
        self.text.setPlainText("\n".join(hex_dump_lines(data, off)))
        self.status.setText("Offset 0x%X – 0x%X / 0x%X  (%d%%)" % (
            off, off + len(data), self.size, int(100 * (off + len(data)) / max(1, self.size))))

    def _parse_int(self, s):
        s = s.strip().lower()
        return int(s, 16) if s.startswith("0x") else int(s)

    def _goto_edit(self):
        try:
            self.goto(self._parse_int(self.off_edit.text()))
        except ValueError:
            self.status.setText("Offset không hợp lệ")

    def _needle(self):
        t = self.find_edit.text()
        if not t:
            return b""
        m = self.mode.currentIndex()
        if m == 0:
            try:
                return bytes.fromhex(re.sub(r"[\s,]|0x", "", t))
            except ValueError:
                return b""
        return t.encode("utf-8" if m == 1 else "utf-16-le")

    def find(self, direction):
        nd = self._needle()
        if not nd:
            self.status.setText("Mẫu tìm không hợp lệ")
            return
        chunk = 4 * 1024 * 1024
        start = self.page_off + (16 if direction > 0 else 0)
        pos = start
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            with open(self.path, "rb") as f:
                if direction > 0:
                    while pos < self.size:
                        f.seek(pos)
                        buf = f.read(chunk + len(nd))
                        i = buf.find(nd)
                        if i >= 0:
                            return self._hit(pos + i)
                        pos += chunk
                else:
                    end = start
                    while end > 0:
                        b0 = max(0, end - chunk)
                        f.seek(b0)
                        buf = f.read(end - b0 + len(nd) - 1)
                        i = buf.rfind(nd)
                        if i >= 0:
                            return self._hit(b0 + i)
                        end = b0
        finally:
            QApplication.restoreOverrideCursor()
        self.status.setText("Không tìm thấy")

    def _hit(self, off):
        self.goto(off)
        self.status.setText("Tìm thấy tại offset 0x%X (%d)" % (off, off))

    def extract_strings(self):
        limit = 64 * 1024 * 1024
        with open(self.path, "rb") as f:
            data = f.read(limit)
        out = ["%08X  %s" % (m.start(), m.group().decode("latin-1"))
               for m in re.finditer(rb"[\x20-\x7e]{5,}", data)]
        out += ["%08X  [u16] %s" % (m.start(), m.group().decode("utf-16-le", "replace"))
                for m in re.finditer(rb"(?:[\x20-\x7e]\x00){5,}", data)]
        ed = self.win.new_tab(content="\n".join(out[:200000]))
        if hasattr(ed, "set_language"):
            ed.set_language(None)

    def sha(self):
        h = hashlib.sha256()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            with open(self.path, "rb") as f:
                for blk in iter(lambda: f.read(8 * 1024 * 1024), b""):
                    h.update(blk)
                    QApplication.processEvents()
        finally:
            QApplication.restoreOverrideCursor()
        self.status.setText("SHA-256: " + h.hexdigest())

    def open_with(self):
        self.win.open_with_dialog(self.path)


# PyTorch .pt / .pth - xem cấu trúc, KHÔNG chạy code trong file
class TorchInspectDialog(QDialog):
    def __init__(self, parent, path):
        super().__init__(parent)
        self.win = parent
        self.path = path
        self.setWindowTitle("PyTorch - " + os.path.basename(path))
        self.resize(860, 620)
        lay = QVBoxLayout(self)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.info = (inspect_safetensors(path) if path.lower().endswith(".safetensors")
                         else inspect_torch_file(path))
        finally:
            QApplication.restoreOverrideCursor()
        i = self.info
        head = "%s  •  %s  •  %s" % (os.path.basename(path), human_size(os.path.getsize(path)), i["kind"])
        if i["tensors"]:
            head += "\n%d tensor  •  %s tham số  •  ~%s (nếu nạp đủ)" % (
                len(i["tensors"]), "{:,}".format(i["params"]), human_size(i["bytes"]))
        lay.addWidget(QLabel(head))
        if i["danger"]:
            warn = QLabel("⚠ File gọi hàm nguy hiểm khi nạp (torch.load sẽ CHẠY code này): "
                          + ", ".join(i["danger"][:8]) + "\nĐừng nạp bằng torch.load nếu không tin nguồn. "
                          "Cửa sổ này chỉ đọc cấu trúc, không chạy gì.")
            warn.setWordWrap(True)
            warn.setStyleSheet("background:#5a1d1d;color:#ffd5d5;padding:6px;border-radius:4px;")
            lay.addWidget(warn)
        else:
            ok = QLabel("🛡 Đọc an toàn: không import / không chạy code trong file.")
            lay.addWidget(ok)
        if i["error"]:
            lay.addWidget(QLabel("Lưu ý: " + i["error"]))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Lọc theo tên tensor...")
        self.search.textChanged.connect(self._filter)
        lay.addWidget(self.search)
        tabs = QTabWidget()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tên", "Shape", "dtype", "Tham số", "Dung lượng"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        for name, shape, dtype, n in i["tensors"]:
            QTreeWidgetItem(self.tree, [name, "×".join(map(str, shape)) or "scalar", dtype,
                                        "{:,}".format(n), human_size(n * _DTYPE_BYTES.get(dtype, 4))])
        for c in range(1, 5):
            self.tree.resizeColumnToContents(c)
        self.tree.setColumnWidth(0, 360)
        tabs.addTab(self.tree, "Tensors (%d)" % len(i["tensors"]))
        misc = QPlainTextEdit()
        misc.setReadOnly(True)
        misc.setFont(mono_font(9))
        misc.setPlainText(i["text"] or "(không có giá trị phụ)")
        tabs.addTab(misc, "Giá trị khác")
        gl = QPlainTextEdit()
        gl.setReadOnly(True)
        gl.setFont(mono_font(9))
        gl.setPlainText("\n".join(i["globals"]) or "(không có)")
        tabs.addTab(gl, "Hàm/Class được gọi (%d)" % len(i["globals"]))
        if i["zip"]:
            zp = QPlainTextEdit()
            zp.setReadOnly(True)
            zp.setFont(mono_font(9))
            zp.setPlainText("\n".join("%10d  %s" % (s, n) for n, s in i["zip"]))
            tabs.addTab(zp, "Trong zip (%d)" % len(i["zip"]))
        lay.addWidget(tabs, 1)
        row = QHBoxLayout()
        b1 = QPushButton("Xuất danh sách → tab mới")
        b1.clicked.connect(self.export_text)
        b2 = QPushButton("Xem hex")
        b2.clicked.connect(lambda: _std_dialog(self.win, HexViewerDialog(self.win, self.path)))
        row.addWidget(b1)
        row.addWidget(b2)
        row.addStretch(1)
        lay.addLayout(row)

    def _filter(self, text):
        t = text.lower()
        for k in range(self.tree.topLevelItemCount()):
            it = self.tree.topLevelItem(k)
            it.setHidden(bool(t) and t not in it.text(0).lower())

    def export_text(self):
        i = self.info
        lines = ["# %s" % os.path.basename(self.path),
                 "# %d tensor, %s tham số" % (len(i["tensors"]), "{:,}".format(i["params"])), ""]
        lines += ["%-60s %-24s %-9s %s" % (n, "×".join(map(str, s)) or "scalar", d, "{:,}".format(c))
                  for n, s, d, c in i["tensors"]]
        self.win.new_tab(content="\n".join(lines))


# Intel HEX (.hex) - firmware
class IntelHexDialog(QDialog):
    def __init__(self, parent, path=None, text=None):
        super().__init__(parent)
        self.win = parent
        self.path = path
        if text is None:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        self.res = parse_intel_hex(text)
        r = self.res
        self.setWindowTitle("Intel HEX - " + (os.path.basename(path) if path else "bộ đệm"))
        self.resize(820, 600)
        lay = QVBoxLayout(self)
        if not r["records"]:
            lay.addWidget(QLabel("Không phải file Intel HEX hợp lệ (không có record ':' nào)."))
            return
        lo = r["segments"][0][0] if r["segments"] else 0
        hi = (r["segments"][-1][0] + len(r["segments"][-1][1]) - 1) if r["segments"] else 0
        s = "%d record  •  %s dữ liệu  •  %d vùng  •  địa chỉ 0x%X – 0x%X" % (
            r["records"], human_size(r["total"]), len(r["segments"]), lo, hi)
        if r["start"] is not None:
            s += "  •  entry 0x%X" % r["start"]
        lay.addWidget(QLabel(s))
        if r["errors"]:
            e = QLabel("⚠ %d lỗi: %s" % (len(r["errors"]), "; ".join(r["errors"][:5])))
            e.setWordWrap(True)
            e.setStyleSheet("background:#5a1d1d;color:#ffd5d5;padding:6px;border-radius:4px;")
            lay.addWidget(e)
        else:
            lay.addWidget(QLabel("✔ Checksum tất cả record đều đúng."))
        self.table = QTableWidget(len(r["segments"]), 3)
        self.table.setHorizontalHeaderLabels(["Bắt đầu", "Kết thúc", "Kích thước"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for k, (a, b) in enumerate(r["segments"]):
            for c, v in enumerate(("0x%08X" % a, "0x%08X" % (a + len(b) - 1), "%d B" % len(b))):
                self.table.setItem(k, c, QTableWidgetItem(v))
        self.table.setMaximumHeight(150)
        self.table.itemSelectionChanged.connect(self._show_seg)
        lay.addWidget(self.table)
        self.dump = QPlainTextEdit()
        self.dump.setReadOnly(True)
        self.dump.setFont(mono_font(10))
        self.dump.setLineWrapMode(QPlainTextEdit.NoWrap)
        lay.addWidget(self.dump, 1)
        row = QHBoxLayout()
        b = QPushButton("Lưu thành .bin (lấp 0xFF chỗ trống)...")
        b.clicked.connect(self.save_bin)
        row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        if r["segments"]:
            self.table.selectRow(0)

    def _show_seg(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        a, b = self.res["segments"][rows[0].row()]
        shown = b[:65536]
        txt = "\n".join(hex_dump_lines(shown, a))
        if len(b) > len(shown):
            txt += "\n... (còn %d byte)" % (len(b) - len(shown))
        self.dump.setPlainText(txt)

    def save_bin(self):
        segs = self.res["segments"]
        if not segs:
            return
        lo = segs[0][0]
        hi = segs[-1][0] + len(segs[-1][1])
        if hi - lo > 64 * 1024 * 1024:
            QMessageBox.warning(self, "Quá lớn", "Khoảng địa chỉ quá rộng để ghi thành .bin.")
            return
        base = os.path.splitext(self.path)[0] if self.path else "firmware"
        p, _ = QFileDialog.getSaveFileName(self, "Lưu .bin", base + ".bin", "Binary (*.bin)")
        if not p:
            return
        buf = bytearray(b"\xff" * (hi - lo))
        for a, b in segs:
            buf[a - lo:a - lo + len(b)] = b
        with open(p, "wb") as f:
            f.write(buf)
        QMessageBox.information(self, "Đã lưu", "%s\nBắt đầu tại địa chỉ 0x%X, %d byte." % (p, lo, len(buf)))


# PHẦN 2B - Mesh 3D (GLB/FBX/OBJ/STL/PLY/...) và Media player
class MeshView(QWidget):
    def __init__(self, verts, faces, max_faces=25000, zup=False):
        super().__init__()
        self.setMinimumSize(560, 420)
        self.setMouseTracking(True)
        self.mode = "solid+wire" if len(faces) < 3000 else "solid"
        self.cull = False
        self.yaw, self.pitch, self.zoom = 0.6, 0.4, 1.0
        self.pan = [0.0, 0.0]
        self._last = None
        self._btn = None
        self.interacting = False
        self.idle = QTimer(self)
        self.idle.setSingleShot(True)
        self.idle.timeout.connect(self._end_interact)
        self.set_data(verts, faces, max_faces, zup)

    @staticmethod
    def _subset(verts, faces, limit):
        if len(faces) > limit:
            step = len(faces) / float(limit)
            faces = [faces[int(i * step)] for i in range(limit)]
        remap, nv, nf = {}, [], []
        for f in faces:
            nf_ = []
            for i in f:
                j = remap.get(i)
                if j is None:
                    j = len(nv)
                    remap[i] = j
                    nv.append(verts[i])
                nf_.append(j)
            nf.append(tuple(nf_))
        return nv, nf

    def set_data(self, verts, faces, max_faces, zup):
        self.total_faces = len(faces)
        if zup:
            verts = [(x, z, -y) for (x, y, z) in verts]
        self.hi = self._subset(verts, faces, max_faces)
        self.lo = self._subset(self.hi[0], self.hi[1], 4000)
        vs = self.hi[0] or [(0, 0, 0)]
        mn = [min(v[i] for v in vs) for i in range(3)]
        mx = [max(v[i] for v in vs) for i in range(3)]
        self.c = [(a + b) / 2.0 for a, b in zip(mn, mx)]
        self.radius = max(1e-9, max(math.sqrt(sum((v[i] - self.c[i]) ** 2 for i in range(3))) for v in vs))
        self.update()

    def reset(self, yaw=0.6, pitch=0.4):
        self.yaw, self.pitch, self.zoom, self.pan = yaw, pitch, 1.0, [0.0, 0.0]
        self.update()

    def _end_interact(self):
        self.interacting = False
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, not self.interacting)
        p.fillRect(self.rect(), QColor("#1b1d23"))
        verts, faces = self.lo if self.interacting else self.hi
        w, h = self.width(), self.height()
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        dist = 2.8 * self.radius / self.zoom
        f = 0.9 * min(w, h) * dist / (2.0 * self.radius)
        c0, c1, c2 = self.c
        P = []
        for x, y, z in verts:
            x -= c0
            y -= c1
            z -= c2
            x1 = x * cy + z * sy
            z1 = -x * sy + z * cy
            y2 = y * cp + z1 * sp
            z2 = -y * sp + z1 * cp
            d = max(0.01 * self.radius, z2 + dist)
            P.append((w / 2.0 + self.pan[0] + f * x1 / d, h / 2.0 + self.pan[1] - f * y2 / d, z2, x1, y2))
        mode = "wire" if self.interacting and self.mode == "solid+wire" else self.mode
        if mode == "points":
            p.setPen(QPen(QColor("#8fb3d9"), 2))
            for q in P:
                p.drawPoint(int(q[0]), int(q[1]))
        else:
            order = []
            for fi in faces:
                if len(fi) < 3:
                    continue
                a, b, c = P[fi[0]], P[fi[1]], P[fi[2]]
                order.append(((a[2] + b[2] + c[2]) / 3.0, fi))
            if mode != "wire":
                order.sort(key=lambda t: -t[0])
            L = (0.35, 0.8, -0.5)
            ln = math.sqrt(sum(v * v for v in L))
            for _d, fi in order:
                a, b, c = P[fi[0]], P[fi[1]], P[fi[2]]
                ux, uy, uz = b[3] - a[3], b[4] - a[4], b[2] - a[2]
                vx, vy, vz = c[3] - a[3], c[4] - a[4], c[2] - a[2]
                nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
                nl = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
                if self.cull and nz > 0:
                    continue
                poly = QPolygonF([QPointF(P[i][0], P[i][1]) for i in fi])
                if mode == "wire":
                    p.setPen(QPen(QColor("#8fb3d9"), 1))
                    p.setBrush(Qt.NoBrush)
                else:
                    br = 0.28 + 0.72 * abs((nx * L[0] + ny * L[1] + nz * L[2]) / (nl * ln))
                    p.setBrush(QBrush(QColor(int(143 * br), int(179 * br), int(217 * br))))
                    p.setPen(QPen(QColor(0, 0, 0, 70), 0.7) if mode == "solid+wire" else Qt.NoPen)
                p.drawPolygon(poly)
        p.setPen(QColor("#9aa4b2"))
        shown = len(self.hi[1])
        note = "" if shown >= self.total_faces else "  (hiển thị %d/%d tam giác)" % (shown, self.total_faces)
        p.drawText(10, h - 10, "Kéo trái: xoay • Kéo phải/giữa: dời • Lăn: zoom • Nhấp đúp: reset" + note)

    def mousePressEvent(self, e):
        self._last, self._btn = e.pos(), e.button()
        self.interacting = True

    def mouseReleaseEvent(self, _e):
        self._last = None
        self.idle.start(120)

    def mouseMoveEvent(self, e):
        if self._last is None:
            return
        d = e.pos() - self._last
        self._last = e.pos()
        if self._btn == Qt.LeftButton:
            self.yaw += d.x() * 0.01
            self.pitch = max(-1.55, min(1.55, self.pitch + d.y() * 0.01))
        else:
            self.pan[0] += d.x()
            self.pan[1] += d.y()
        self.update()

    def wheelEvent(self, e):
        self.interacting = True
        self.zoom = max(0.1, min(40.0, self.zoom * (1.12 if e.angleDelta().y() > 0 else 1 / 1.12)))
        self.idle.start(150)
        self.update()

    def mouseDoubleClickEvent(self, _e):
        self.reset()


class MeshViewerDialog(QDialog):
    def __init__(self, parent, path, data=None, title=None):
        super().__init__(parent)
        self.win = parent
        self.path = path
        self.setWindowTitle("3D - " + (title or os.path.basename(path)))
        self.resize(900, 680)
        lay = QVBoxLayout(self)
        if data is not None:
            verts, faces = data[0], data[1]
            note = ""
        else:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                verts, faces, note = parse_mesh_any(path)
            finally:
                QApplication.restoreOverrideCursor()
        ext = os.path.splitext(path or "")[1].lower()
        max_faces = cfg_get(parent, "mesh/max_faces", 25000, int)
        zup = ext in (".stl", ".ply", ".off")
        self.view = MeshView(verts, faces, max_faces, zup)
        self._raw = (verts, faces, max_faces)
        if cfg_get(parent, "mesh/wire", False, bool):
            self.view.mode = "wire"
        bar = QHBoxLayout()
        for text, mode in (("Đặc", "solid"), ("Đặc + lưới", "solid+wire"), ("Lưới", "wire"), ("Điểm", "points")):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, m=mode: self._set_mode(m))
            bar.addWidget(b)
        cull = QCheckBox("Ẩn mặt sau")
        cull.toggled.connect(lambda v: (setattr(self.view, "cull", v), self.view.update()))
        self.zchk = QCheckBox("Z lên")
        self.zchk.setChecked(zup)
        self.zchk.toggled.connect(self._reload)
        bar.addWidget(cull)
        bar.addWidget(self.zchk)
        for text, (yaw, pitch) in (("Trước", (0, 0)), ("Bên", (math.pi / 2, 0)), ("Trên", (0, 1.55)),
                                   ("Reset", (0.6, 0.4))):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, a=(yaw, pitch): self.view.reset(*a))
            bar.addWidget(b)
        if data is None and ext in (".obj", ".gltf", ".off", ".ply", ".stl", ".fbx"):
            b = QPushButton("Mở dạng text")
            b.clicked.connect(lambda: parent.open_path(path, force_text=True))
            bar.addWidget(b)
        if data is None:
            b = QPushButton("Hex")
            b.clicked.connect(lambda: _std_dialog(parent, HexViewerDialog(parent, path)))
            bar.addWidget(b)
        bar.addStretch(1)
        lay.addLayout(bar)
        lay.addWidget(self.view, 1)
        lay.addWidget(QLabel("%s %s" % (mesh_stats(verts, faces), note)))

    def _set_mode(self, m):
        self.view.mode = m
        self.view.update()

    def _reload(self, z):
        v, f, mx = self._raw
        self.view.set_data(v, f, mx, z)


# Media player (video / audio)
MEDIA_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv", ".m4v", ".mpg", ".mpeg",
              ".3gp", ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".opus", ".wma"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv", ".m4v", ".mpg", ".mpeg", ".3gp"}
