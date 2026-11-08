"""Thống kê dự án: số file / dòng code theo ngôn ngữ."""
import os

PLUGIN = {"name": "Thống kê dự án", "version": "1.0", "author": "GKcode",
          "description": "Đếm file, dòng code, dòng trống theo ngôn ngữ trong thư mục dự án (Plugins > Thống kê dự án)."}

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "build", "dist", ".idea", ".vscode", "target"}
LANGS = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".c": "C", ".h": "C/C++ header",
         ".cpp": "C++", ".cc": "C++", ".hpp": "C++ header", ".cs": "C#", ".java": "Java", ".go": "Go", ".rs": "Rust",
         ".kt": "Kotlin", ".swift": "Swift", ".php": "PHP", ".rb": "Ruby", ".lua": "Lua", ".html": "HTML",
         ".css": "CSS", ".scss": "SCSS", ".json": "JSON", ".md": "Markdown", ".sql": "SQL", ".sh": "Shell",
         ".ino": "Arduino", ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".xml": "XML"}


def register(api):
    def run():
        root = api.project_root()
        if not root or not os.path.isdir(root):
            api.message("Hãy mở một thư mục dự án trước (File > Open Folder).")
            return
        stats, files = {}, 0
        for base, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for n in names:
                lang = LANGS.get(os.path.splitext(n)[1].lower())
                if not lang:
                    continue
                try:
                    if os.path.getsize(os.path.join(base, n)) > 5_000_000:
                        continue
                    with open(os.path.join(base, n), "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.read().split("\n")
                except OSError:
                    continue
                s = stats.setdefault(lang, [0, 0, 0])
                s[0] += 1
                s[1] += sum(1 for x in lines if x.strip())
                s[2] += sum(1 for x in lines if not x.strip())
                files += 1
        if not stats:
            api.message("Không thấy file code nào trong: " + root)
            return
        rows = sorted(stats.items(), key=lambda kv: -kv[1][1])
        tot = [sum(v[i] for _k, v in rows) for i in range(3)]
        out = ["Dự án: %s" % root, "", "%-16s %7s %9s %8s" % ("Ngôn ngữ", "File", "Dòng code", "Dòng trống"), "-" * 44]
        for k, v in rows:
            out.append("%-16s %7d %9d %8d" % (k, v[0], v[1], v[2]))
        out += ["-" * 44, "%-16s %7d %9d %8d" % ("TỔNG", tot[0], tot[1], tot[2])]
        api.show_text("Thống kê dự án", "\n".join(out))

    api.add_action("Thống kê dự án", run)
