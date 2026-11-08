"""Công cụ Markdown: căn bảng, tạo mục lục."""
import re

PLUGIN = {"name": "Markdown tools", "version": "1.0", "author": "GKcode",
          "description": "Căn đẹp bảng Markdown (đoạn chọn hoặc cả file) và chèn mục lục từ các tiêu đề."}


def _cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def format_tables(text):
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", lines[i + 1]) \
                and "-" in lines[i + 1]:
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            rows = [_cells(l) for l in lines[i:j]]
            n = max(len(r) for r in rows)
            rows = [r + [""] * (n - len(r)) for r in rows]
            w = [max(3, max(len(r[c]) for k, r in enumerate(rows) if k != 1)) for c in range(n)]
            fmt = lambda r: "| " + " | ".join(r[c].ljust(w[c]) for c in range(n)) + " |"
            sep = []
            for c in range(n):
                raw = rows[1][c]
                left, right = raw.startswith(":"), raw.endswith(":")
                sep.append((":" if left else "-") + "-" * (w[c] - 2) + (":" if right else "-"))
            out += [fmt(rows[0]), "| " + " | ".join(sep) + " |"] + [fmt(r) for r in rows[2:]]
            i = j
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def make_toc(text):
    toc, fence = [], False
    for l in text.split("\n"):
        if l.strip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,6})\s+(.+?)\s*#*$", l)
        if m:
            title = m.group(2)
            slug = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
            toc.append("%s- [%s](#%s)" % ("  " * (len(m.group(1)) - 1), title, slug))
    return "\n".join(toc)


def register(api):
    def fmt():
        sel = api.selection()
        if sel:
            api.replace_selection(format_tables(sel))
        else:
            api.set_text(format_tables(api.text()))
        api.status("Đã căn bảng Markdown")

    def toc():
        t = make_toc(api.text())
        if not t:
            api.message("Chưa có tiêu đề (#) nào trong file.")
            return
        api.insert(t + "\n")

    api.add_action("Căn bảng Markdown", fmt)
    api.add_action("Chèn mục lục (TOC)", toc)
