# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


# Themes
THEMES = {
    "dark": {
        "label": "Dark (mặc định)", "bg": "#1e1e1e", "fg": "#d4d4d4",
        "keyword": "#569CD6", "string": "#CE9178", "comment": "#6A9955",
        "number": "#B5CEA8", "func": "#DCDCAA", "line_bg": "#2a2d2e",
        "gutter_bg": "#252526", "gutter_fg": "#858585",
        "terminal_bg": "#0c0c0c", "terminal_fg": "#cccccc",
        "tab_bg": "#2d2d2d", "tab_fg": "#cccccc", "tab_active_bg": "#1e1e1e",
        "accent": "#3794ff", "window_bg": "#1e1e1e",
    },
    "light": {
        "label": "Light", "bg": "#ffffff", "fg": "#1e1e1e",
        "keyword": "#0000ff", "string": "#a31515", "comment": "#008000",
        "number": "#098658", "func": "#795e26", "line_bg": "#f0f0f0",
        "gutter_bg": "#f3f3f3", "gutter_fg": "#7a7a7a",
        "terminal_bg": "#f5f5f5", "terminal_fg": "#1e1e1e",
        "tab_bg": "#ececec", "tab_fg": "#333333", "tab_active_bg": "#ffffff",
        "accent": "#0066cc", "window_bg": "#f0f0f0",
    },
    "than_dem": {
        "label": "Than Đêm", "bg": "#272822", "fg": "#f8f8f2",
        "keyword": "#f92672", "string": "#e6db74", "comment": "#75715e",
        "number": "#ae81ff", "func": "#a6e22e", "line_bg": "#3e3d32",
        "gutter_bg": "#2d2e27", "gutter_fg": "#8f908a",
        "terminal_bg": "#1e1f1c", "terminal_fg": "#f8f8f2",
        "tab_bg": "#2d2e27", "tab_fg": "#cccccc", "tab_active_bg": "#272822",
        "accent": "#66d9ef", "window_bg": "#272822",
    },
    "bien_dem": {
        "label": "Biển Đêm", "bg": "#002b36", "fg": "#839496",
        "keyword": "#859900", "string": "#2aa198", "comment": "#586e75",
        "number": "#d33682", "func": "#b58900", "line_bg": "#073642",
        "gutter_bg": "#073642", "gutter_fg": "#586e75",
        "terminal_bg": "#00212b", "terminal_fg": "#839496",
        "tab_bg": "#073642", "tab_fg": "#93a1a1", "tab_active_bg": "#002b36",
        "accent": "#268bd2", "window_bg": "#002b36",
    },
    "tim_huyen": {
        "label": "Tím Huyền", "bg": "#282a36", "fg": "#f8f8f2",
        "keyword": "#ff79c6", "string": "#f1fa8c", "comment": "#6272a4",
        "number": "#bd93f9", "func": "#50fa7b", "line_bg": "#343746",
        "gutter_bg": "#21222c", "gutter_fg": "#6272a4",
        "terminal_bg": "#191a21", "terminal_fg": "#f8f8f2",
        "tab_bg": "#21222c", "tab_fg": "#cfcfe0", "tab_active_bg": "#282a36",
        "accent": "#bd93f9", "window_bg": "#282a36",
    },
    "bang_gia": {
        "label": "Băng Giá", "bg": "#2e3440", "fg": "#d8dee9",
        "keyword": "#81a1c1", "string": "#a3be8c", "comment": "#616e88",
        "number": "#b48ead", "func": "#88c0d0", "line_bg": "#3b4252",
        "gutter_bg": "#2b303b", "gutter_fg": "#616e88",
        "terminal_bg": "#242933", "terminal_fg": "#d8dee9",
        "tab_bg": "#2b303b", "tab_fg": "#d8dee9", "tab_active_bg": "#2e3440",
        "accent": "#88c0d0", "window_bg": "#2e3440",
    },
}
# GIAO DIỆN HIỆN ĐẠI: theme 2026, icon SVG, stylesheet phẳng, badge file
def _mix(a, b, t):
    ca, cb = QColor(a), QColor(b)
    return QColor(int(ca.red() * (1 - t) + cb.red() * t), int(ca.green() * (1 - t) + cb.green() * t),
                  int(ca.blue() * (1 - t) + cb.blue() * t)).name()


MODERN_THEMES = {
    "modern_dark": {
        "label": "Modern Dark (2026)", "bg": "#1f1f1f", "fg": "#cccccc",
        "keyword": "#569cd6", "string": "#ce9178", "comment": "#6a9955",
        "number": "#b5cea8", "func": "#dcdcaa", "line_bg": "#282828",
        "gutter_bg": "#1f1f1f", "gutter_fg": "#6e7681",
        "terminal_bg": "#181818", "terminal_fg": "#cccccc",
        "tab_bg": "#181818", "tab_fg": "#9d9d9d", "tab_active_bg": "#1f1f1f",
        "accent": "#0078d4", "window_bg": "#181818",
        "sidebar_bg": "#181818", "activity_bg": "#181818", "border": "#2b2b2b"},
    "github_dark": {
        "label": "GitHub Dark", "bg": "#0d1117", "fg": "#e6edf3",
        "keyword": "#ff7b72", "string": "#a5d6ff", "comment": "#8b949e",
        "number": "#79c0ff", "func": "#d2a8ff", "line_bg": "#161b22",
        "gutter_bg": "#0d1117", "gutter_fg": "#6e7681",
        "terminal_bg": "#010409", "terminal_fg": "#e6edf3",
        "tab_bg": "#010409", "tab_fg": "#8b949e", "tab_active_bg": "#0d1117",
        "accent": "#2f81f7", "window_bg": "#010409",
        "sidebar_bg": "#010409", "activity_bg": "#010409", "border": "#30363d"},
    "modern_light": {
        "label": "Modern Light (2026)", "bg": "#ffffff", "fg": "#3b3b3b",
        "keyword": "#0000ff", "string": "#a31515", "comment": "#008000",
        "number": "#098658", "func": "#795e26", "line_bg": "#f5f5f5",
        "gutter_bg": "#ffffff", "gutter_fg": "#8a8a8a",
        "terminal_bg": "#f8f8f8", "terminal_fg": "#3b3b3b",
        "tab_bg": "#f8f8f8", "tab_fg": "#616161", "tab_active_bg": "#ffffff",
        "accent": "#005fb8", "window_bg": "#f8f8f8",
        "sidebar_bg": "#f8f8f8", "activity_bg": "#f0f0f0", "border": "#e5e5e5"},
}
MODERN_THEMES.update({
    "tokyo_night": {
        "label": "Phố Đêm", "bg": "#1a1b26", "fg": "#c0caf5",
        "keyword": "#bb9af7", "string": "#9ece6a", "comment": "#565f89",
        "number": "#ff9e64", "func": "#7aa2f7", "line_bg": "#202330",
        "gutter_bg": "#1a1b26", "gutter_fg": "#3b4261",
        "terminal_bg": "#16161e", "terminal_fg": "#c0caf5",
        "tab_bg": "#16161e", "tab_fg": "#787c99", "tab_active_bg": "#1a1b26",
        "accent": "#7aa2f7", "window_bg": "#16161e",
        "sidebar_bg": "#16161e", "activity_bg": "#13131a", "border": "#292e42"},
    "one_dark": {
        "label": "Xám Than", "bg": "#282c34", "fg": "#abb2bf",
        "keyword": "#c678dd", "string": "#98c379", "comment": "#5c6370",
        "number": "#d19a66", "func": "#61afef", "line_bg": "#2c313a",
        "gutter_bg": "#282c34", "gutter_fg": "#4b5263",
        "terminal_bg": "#21252b", "terminal_fg": "#abb2bf",
        "tab_bg": "#21252b", "tab_fg": "#9da5b4", "tab_active_bg": "#282c34",
        "accent": "#61afef", "window_bg": "#21252b",
        "sidebar_bg": "#21252b", "activity_bg": "#1b1f23", "border": "#3b4048"},
    "ca_phe_sua": {
        "label": "Cà Phê Sữa", "bg": "#1e1e2e", "fg": "#cdd6f4",
        "keyword": "#cba6f7", "string": "#a6e3a1", "comment": "#6c7086",
        "number": "#fab387", "func": "#89b4fa", "line_bg": "#262637",
        "gutter_bg": "#1e1e2e", "gutter_fg": "#585b70",
        "terminal_bg": "#181825", "terminal_fg": "#cdd6f4",
        "tab_bg": "#181825", "tab_fg": "#a6adc8", "tab_active_bg": "#1e1e2e",
        "accent": "#89b4fa", "window_bg": "#181825",
        "sidebar_bg": "#181825", "activity_bg": "#11111b", "border": "#313244"},
    "nau_co_dien": {
        "label": "Nâu Cổ Điển", "bg": "#282828", "fg": "#ebdbb2",
        "keyword": "#fb4934", "string": "#b8bb26", "comment": "#928374",
        "number": "#d3869b", "func": "#fabd2f", "line_bg": "#32302f",
        "gutter_bg": "#282828", "gutter_fg": "#7c6f64",
        "terminal_bg": "#1d2021", "terminal_fg": "#ebdbb2",
        "tab_bg": "#1d2021", "tab_fg": "#a89984", "tab_active_bg": "#282828",
        "accent": "#fe8019", "window_bg": "#1d2021",
        "sidebar_bg": "#1d2021", "activity_bg": "#181a1b", "border": "#3c3836"},
    "rose_pine": {
        "label": "Rosé Pine", "bg": "#191724", "fg": "#e0def4",
        "keyword": "#31748f", "string": "#f6c177", "comment": "#6e6a86",
        "number": "#ebbcba", "func": "#c4a7e7", "line_bg": "#1f1d2e",
        "gutter_bg": "#191724", "gutter_fg": "#524f67",
        "terminal_bg": "#12101c", "terminal_fg": "#e0def4",
        "tab_bg": "#16141f", "tab_fg": "#908caa", "tab_active_bg": "#191724",
        "accent": "#c4a7e7", "window_bg": "#16141f",
        "sidebar_bg": "#16141f", "activity_bg": "#12101a", "border": "#26233a"},
    "night_owl": {
        "label": "Cú Đêm", "bg": "#011627", "fg": "#d6deeb",
        "keyword": "#c792ea", "string": "#ecc48d", "comment": "#637777",
        "number": "#f78c6c", "func": "#82aaff", "line_bg": "#0b2942",
        "gutter_bg": "#011627", "gutter_fg": "#4b6479",
        "terminal_bg": "#010e1a", "terminal_fg": "#d6deeb",
        "tab_bg": "#010e1a", "tab_fg": "#5f7e97", "tab_active_bg": "#011627",
        "accent": "#82aaff", "window_bg": "#010e1a",
        "sidebar_bg": "#010e1a", "activity_bg": "#010b14", "border": "#122d42"},
})


def _mk_theme(label, bg, fg, kw, st, cm, nm, fn, accent, side, act, border, line, gut, term=None, tab=None, tabfg=None):
    return {"label": label, "bg": bg, "fg": fg, "keyword": kw, "string": st, "comment": cm,
            "number": nm, "func": fn, "line_bg": line, "gutter_bg": bg, "gutter_fg": gut,
            "terminal_bg": term or side, "terminal_fg": fg, "tab_bg": tab or side,
            "tab_fg": tabfg or cm, "tab_active_bg": bg, "accent": accent, "window_bg": side,
            "sidebar_bg": side, "activity_bg": act, "border": border}


MODERN_THEMES.update({
    "vercel_dark": _mk_theme("Vercel Midnight (2026)", "#000000", "#ededed", "#ff7ac6", "#50e3c2", "#6f6f6f",
                             "#f5a623", "#79b8ff", "#0070f3", "#0a0a0a", "#000000", "#262626", "#111111", "#444444", "#050505", None, "#8f8f8f"),
    "linear_dark": _mk_theme("Linear Violet (2026)", "#17181c", "#e2e4ea", "#a78bfa", "#86efac", "#656a78",
                             "#fbbf77", "#7dd3fc", "#7c6cf0", "#131418", "#0f1013", "#2a2c34", "#1d1f25", "#4a4e5c", "#101114", None, "#8a8f9e"),
    "zed_one": _mk_theme("Zed One (2026)", "#282c33", "#dce0e5", "#b477cf", "#a1c181", "#5d636f",
                         "#bf956a", "#74ade8", "#74ade8", "#2f343e", "#252930", "#3a3f4b", "#2d3139", "#4e5666", "#21252b", None, "#9aa0ab"),
    "ayu_mirage": _mk_theme("Ayu Mirage", "#1f2430", "#cccac2", "#ffad66", "#d5ff80", "#6c7a8b",
                            "#dfbfff", "#73d0ff", "#ffcc66", "#1c212b", "#171b24", "#2d3441", "#242b38", "#4a5568", "#191e28", None, "#8a95a6"),
    "rung_sau": _mk_theme("Rừng Sâu", "#2d353b", "#d3c6aa", "#e67e80", "#a7c080", "#7a8478",
                            "#d699b6", "#7fbbb3", "#a7c080", "#272e33", "#1e2326", "#3d484d", "#343f44", "#5c6a72", "#232a2e", None, "#9aa89c"),
    "song_lam": _mk_theme("Sóng Lam", "#1f1f28", "#dcd7ba", "#957fb8", "#98bb6c", "#727169",
                          "#d27e99", "#7e9cd8", "#7e9cd8", "#181820", "#16161d", "#2a2a37", "#2a2a37", "#54546d", "#16161d", None, "#8a8980"),
    "hoang_hon_tim": _mk_theme("Hoàng Hôn Tím", "#292d3e", "#a6accd", "#c792ea", "#c3e88d", "#676e95",
                           "#f78c6c", "#82aaff", "#82aaff", "#232635", "#1b1e2b", "#34384d", "#303348", "#4e5579", "#202331", None, "#8087ad"),
    "tim_huyen": _mk_theme("Tím Huyền Plus", "#282a36", "#f8f8f2", "#ff79c6", "#f1fa8c", "#6272a4",
                         "#bd93f9", "#50fa7b", "#bd93f9", "#21222c", "#191a21", "#383a4a", "#2f3241", "#575b78", "#1e1f29", None, "#9aa0c8"),
    "bien_sang": _mk_theme("Biển Sáng", "#fdf6e3", "#586e75", "#859900", "#2aa198", "#93a1a1",
                                 "#d33682", "#268bd2", "#268bd2", "#eee8d5", "#e6dfc8", "#d9d2bc", "#f5eed8", "#93a1a1", "#f5eed8", None, "#657b83"),
    "paper_light": _mk_theme("Paper White (2026)", "#fcfcfd", "#24292f", "#cf222e", "#0a3069", "#8c959f",
                             "#0550ae", "#8250df", "#0969da", "#f6f8fa", "#eef1f4", "#d8dee4", "#f3f5f7", "#9aa4af", "#f6f8fa", None, "#57606a"),
    "high_contrast": _mk_theme("High Contrast Pro", "#000000", "#ffffff", "#ff9ff3", "#7bed9f", "#8fa3b5",
                               "#ffd166", "#5ec8ff", "#ffd400", "#0b0b0b", "#000000", "#6b6b6b", "#1a1a1a", "#a0a0a0", "#000000", None, "#d0d0d0"),
})
THEMES = {**MODERN_THEMES, **THEMES}
DEFAULT_THEME = "linear_dark"
UI_OPTS = {"status_accent": True, "radius": 8}
THEME_EDIT_KEYS = [
    ("bg", "Nền editor"), ("fg", "Chữ"), ("keyword", "Từ khóa"), ("string", "Chuỗi"),
    ("comment", "Chú thích"), ("number", "Số"), ("func", "Hàm"), ("accent", "Màu nhấn (accent)"),
    ("line_bg", "Dòng hiện tại"), ("gutter_bg", "Nền số dòng"), ("gutter_fg", "Chữ số dòng"),
    ("window_bg", "Nền cửa sổ"), ("sidebar_bg", "Nền sidebar"), ("activity_bg", "Nền activity bar"),
    ("tab_bg", "Nền thanh tab"), ("terminal_bg", "Nền terminal"), ("border", "Viền"),
]


def _lum(c):
    c = QColor(c)
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c.red()) + 0.7152 * f(c.green()) + 0.0722 * f(c.blue())


def contrast_ratio(a, b):
    la, lb = _lum(a), _lum(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)


def load_custom_themes(settings):
    try:
        raw = settings.value("ui/custom_themes", "") or ""
        data = json.loads(raw) if raw else {}
    except (ValueError, TypeError):
        data = {}
    base = THEMES.get(DEFAULT_THEME) or next(iter(THEMES.values()))
    for k, t in (data.items() if isinstance(data, dict) else []):
        if isinstance(t, dict):
            full = dict(base)
            full.update({a: b for a, b in t.items() if isinstance(b, str)})
            full["custom"] = True
            full.setdefault("label", k)
            THEMES[k] = full


def load_ui_opts(settings):
    try:
        UI_OPTS["status_accent"] = str(settings.value("ui/status_accent", "true")).lower() in ("true", "1")
        UI_OPTS["radius"] = max(0, min(16, int(settings.value("ui/radius", 8))))
    except (TypeError, ValueError):
        pass


def apply_app_palette(t):
    """Đặt QPalette toàn app theo theme: widget (kể cả của plugin) không còn chữ đen trên nền tối."""
    app = QApplication.instance()
    if app is None:
        return
    pal = ui_palette(t)
    p = QPalette()
    C = QColor
    for role, col in ((QPalette.Window, pal["window"]), (QPalette.WindowText, t["fg"]),
                      (QPalette.Base, t["bg"]), (QPalette.AlternateBase, pal["side"]),
                      (QPalette.Text, t["fg"]), (QPalette.Button, pal["card"]),
                      (QPalette.ButtonText, t["fg"]), (QPalette.BrightText, "#ffffff"),
                      (QPalette.ToolTipBase, pal["menu"]), (QPalette.ToolTipText, t["fg"]),
                      (QPalette.Highlight, t["accent"]), (QPalette.HighlightedText, pal["on_accent"]),
                      (QPalette.Link, t["accent"]), (QPalette.PlaceholderText, pal["muted"])):
        p.setColor(role, C(col))
    for role in (QPalette.Text, QPalette.ButtonText, QPalette.WindowText):
        p.setColor(QPalette.Disabled, role, C(pal["muted"]))
    app.setPalette(p)


class ContrastFixer(QObject):
    """Plugin hay đặt màu chữ cứng (vd color:#333) → hòa vào nền tối. Khi widget hiện ra, nếu độ tương
    phản < 3:1 so với nền thì đổi sang màu chữ của theme."""
    KINDS = None

    def __init__(self, win):
        super().__init__(win)
        self.win = win

    def eventFilter(self, o, e):
        if e.type() == QEvent.Show and isinstance(o, (QLabel, QCheckBox, QRadioButton, QPushButton, QGroupBox)):
            try:
                self._fix(o)
            except Exception:
                pass
        return False

    def _fix(self, w):
        t = THEMES.get(self.win.theme_name)
        if not t:
            return
        ss = w.styleSheet()
        bg_default = t["window_bg"]
        if ss and "color" in ss and getattr(w, "_gk_fixed", None) != ss:
            m = re.search(r'(?<![-\w])color\s*:\s*(#[0-9a-fA-F]{3,8}|[a-zA-Z]+)', ss)
            if m:
                fg = QColor(m.group(1))
                bgm = re.search(r'background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,8})', ss)
                bg = QColor(bgm.group(1)) if bgm else QColor(bg_default)
                if fg.isValid() and bg.isValid() and contrast_ratio(fg, bg) < 3.0:
                    new = (("#ffffff" if _lum(bg) < 0.4 else "#111111") if bgm else t["fg"])
                    w.setStyleSheet(ss[:m.start(1)] + new + ss[m.end(1):])
                    w._gk_fixed = w.styleSheet()
        if isinstance(w, QLabel) and "color" in (w.text() or "") and "<" in (w.text() or ""):
            txt = w.text()
            bg = QColor(bg_default)

            def sub(m):
                c = QColor(m.group(2))
                if c.isValid() and contrast_ratio(c, bg) < 3.0:
                    return m.group(1) + t["fg"]
                return m.group(0)
            new = re.sub(r'(color\s*:\s*)(#[0-9a-fA-F]{3,8})', sub, txt)
            if new != txt:
                w.setText(new)


def ui_palette(t):
    dark = QColor(t["bg"]).lightness() < 128
    window = t["window_bg"]
    side = t.get("sidebar_bg") or t["gutter_bg"]
    ac = QColor(t["accent"])
    return {
        "window": window, "bg": t["bg"], "fg": t["fg"], "accent": t["accent"],
        "side": side,
        "activity": t.get("activity_bg") or _mix(window, "#000000", 0.25 if dark else 0.05),
        "border": t.get("border") or _mix(t["bg"], t["fg"], 0.14),
        "hover": _mix(window, t["fg"], 0.09),
        "muted": _mix(t["fg"], t["bg"], 0.40),
        "input": t["bg"] if dark else "#ffffff",
        "menu": _mix(side, t["fg"], 0.05),
        "scroll": _mix(t["bg"], t["fg"], 0.22),
        "tab_bg": t["tab_bg"], "panel": t["terminal_bg"],
        "sel": f"rgba({ac.red()}, {ac.green()}, {ac.blue()}, 70)",
        "accent_a": f"rgba({ac.red()}, {ac.green()}, {ac.blue()}, 60)",
        "accent_h": _mix(t["accent"], "#ffffff", 0.18),
        "accent_p": _mix(t["accent"], "#000000", 0.22),
        "on_accent": "#ffffff" if ac.lightness() < 170 else "#111111",
        "card": _mix(side, t["fg"], 0.035),
        "glow": f"rgba({ac.red()}, {ac.green()}, {ac.blue()}, 38)",
        "soft_border": _mix(t.get("border") or t["bg"], t["bg"], 0.35),
        "status_bg": _mix(t["accent"], "#000000", 0.22) if UI_OPTS["status_accent"] else (t.get("activity_bg") or window),
        "status_fg": ("#ffffff" if ac.lightness() < 170 else "#111111") if UI_OPTS["status_accent"] else _mix(t["fg"], t["bg"], 0.40),
        "r": f"{UI_OPTS['radius']}px", "rs": f"{max(0, UI_OPTS['radius'] - 2)}px", "rl": f"{UI_OPTS['radius'] + 2}px",
    }


QSS_TEMPLATE = """
QMainWindow, QDialog { background: @window@; }
QDialog QLabel, QCheckBox, QRadioButton { color: @fg@; }
QCheckBox, QRadioButton { spacing: 8px; }
QMenuBar { background: @activity@; color: @muted@; padding: 2px 6px; border-bottom: 1px solid @border@; }
QMenuBar::item { padding: 5px 10px; border-radius: 5px; background: transparent; }
QMenuBar::item:selected { background: @hover@; color: @fg@; }
QMenu { background: @menu@; color: @fg@; border: 1px solid @border@; border-radius: @rl@; padding: 6px; }
QMenu::item { padding: 7px 30px 7px 14px; border-radius: @rs@; margin: 1px 0; }
QMenu::item:selected { background: @accent@; color: @on_accent@; }
QMenu::item:disabled { color: @muted@; }
QMenu::separator { height: 1px; background: @border@; margin: 5px 8px; }
QToolBar { background: @window@; border: none; spacing: 2px; padding: 3px 8px; }
QToolBar::separator { background: @border@; width: 1px; height: 1px; margin: 6px 8px; }
QToolBar#activityBar { background: @activity@; border: none; border-right: 1px solid @border@; padding: 4px 0; spacing: 0; }
QToolButton { color: @fg@; padding: 5px; border-radius: @rs@; background: transparent; border: none; }
QToolButton:hover { background: @hover@; }
QToolButton:pressed { background: @accent_a@; }
QToolBar#activityBar QToolButton { padding: 13px 14px; border-radius: 0; border-left: 3px solid transparent; }
QToolBar#activityBar QToolButton:hover { background: @hover@; }
QToolBar#activityBar QToolButton:checked { background: @glow@; border-left: 3px solid @accent@; }
QToolBar QPushButton#cmdPill { background: @input@; border: 1px solid @border@; border-radius: 12px;
    color: @muted@; padding: 5px 18px; min-width: 340px; text-align: center; }
QToolBar QPushButton#cmdPill:hover { border-color: @accent@; color: @fg@; background: @card@; }
QStatusBar { background: @status_bg@; color: @status_fg@; border-top: none; }
QStatusBar::item { border: none; }
QStatusBar QLabel { color: @status_fg@; padding: 0 10px; font-weight: 500; }
QStatusBar QPushButton { background: transparent; color: @status_fg@; border: none; border-radius: 4px; padding: 2px 10px; }
QStatusBar QPushButton:hover { background: rgba(128,128,128,60); color: @status_fg@; }
QDockWidget { color: @muted@; }
QDockWidget::title { background: @side@; padding: 10px 14px; text-align: left; font-size: 8pt;
    font-weight: 700; letter-spacing: 1px; color: @muted@; border-bottom: 1px solid @border@; }
QTreeView, QListWidget { background: @side@; color: @fg@; border: none; outline: 0; }
QTreeView::item { padding: 4px 2px; border-radius: @rs@; margin: 0 4px; }
QListWidget::item { padding: 5px 8px; border-radius: @rs@; margin: 1px 4px; }
QTreeView::item:hover, QListWidget::item:hover { background: @hover@; }
QTreeView::item:selected, QListWidget::item:selected { background: @sel@; color: @fg@; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: @input@; color: @fg@; border: 1px solid @border@;
    border-radius: @r@; padding: 5px 10px; selection-background-color: @accent@; selection-color: @on_accent@; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid @accent@; background: @input@; }
QLineEdit:hover, QComboBox:hover { border-color: @muted@; }
QComboBox::drop-down { border: none; width: 20px; }
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 0; border: none; }
QComboBox QAbstractItemView { background: @menu@; color: @fg@; selection-background-color: @accent@;
    border: 1px solid @border@; outline: 0; }
QPushButton { background: @card@; color: @fg@; border: 1px solid @border@; border-radius: @r@; padding: 6px 16px; }
QPushButton:hover { border-color: @accent@; background: @hover@; }
QPushButton:pressed { background: @border@; }
QPushButton:default { background: @accent@; color: @on_accent@; border-color: @accent@; font-weight: 600; }
QPushButton:default:hover { background: @accent_h@; }
QPushButton:default:pressed { background: @accent_p@; }
QPushButton:disabled { color: @muted@; }
TerminalPanel QPushButton, FindBar QPushButton { padding: 3px 10px; font-size: 8.5pt; background: transparent;
    border: 1px solid transparent; color: @muted@; }
TerminalPanel QPushButton:hover, FindBar QPushButton:hover { background: @hover@; color: @fg@; border-color: @border@; }
QPlainTextEdit#addData { background: @input@; color: @fg@; border: 1px solid @border@; border-radius: @rs@; }
QTableWidget { background: @bg@; color: @fg@; gridline-color: @border@; border: 1px solid @border@;
    alternate-background-color: @side@; selection-background-color: @sel@; selection-color: @fg@; }
QHeaderView::section { background: @side@; color: @muted@; border: 0; border-bottom: 1px solid @border@; padding: 5px 8px; }
QScrollBar:vertical { background: transparent; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: @scroll@; min-height: 36px; border-radius: 4px; margin: 2px 3px; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:vertical:pressed { background: @accent@; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: @scroll@; min-width: 36px; border-radius: 4px; margin: 3px 2px; }
QScrollBar::handle:horizontal:hover, QScrollBar::handle:horizontal:pressed { background: @accent@; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page { background: none; width: 0; height: 0; }
QSplitter::handle { background: @border@; }
QSplitter::handle:vertical { height: 1px; }
QSplitter::handle:horizontal { width: 1px; }
QMainWindow::separator { background: @border@; width: 1px; height: 1px; }
QToolTip { background: @menu@; color: @fg@; border: 1px solid @border@; padding: 5px 10px; border-radius: @rs@; }
QProgressBar { background: @card@; border: none; border-radius: 4px; height: 6px; text-align: center; }
QProgressBar::chunk { background: @accent@; border-radius: 4px; }
QGroupBox { border: 1px solid @border@; border-radius: @rl@; margin-top: 12px; padding: 12px 8px 8px 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: @muted@; }
QTabWidget#settingsTabs::pane { border: 1px solid @border@; border-radius: @r@; }
QLabel { color: @fg@; background: transparent; }
QCheckBox, QRadioButton, QGroupBox { color: @fg@; }
QTextBrowser, QTextEdit { background: @input@; color: @fg@; border: 1px solid @border@; border-radius: @rs@;
    selection-background-color: @accent@; selection-color: @on_accent@; }
QDialog QPlainTextEdit { background: @input@; color: @fg@; border: 1px solid @border@; border-radius: @rs@; }
QListView, QTreeWidget, QTableView { background: @bg@; color: @fg@; border: 1px solid @border@; }
QSlider::groove:horizontal { background: @border@; height: 4px; border-radius: 2px; }
QSlider::handle:horizontal { background: @accent@; width: 14px; margin: -5px 0; border-radius: 7px; }
QSlider::sub-page:horizontal { background: @accent@; border-radius: 2px; }
QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; border: 1px solid @muted@; background: @input@; }
QCheckBox::indicator { border-radius: 4px; }
QRadioButton::indicator { border-radius: 9px; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked { background: @accent@; border-color: @accent@; }
QCheckBox::indicator:hover, QRadioButton::indicator:hover { border-color: @accent@; }
QScrollArea { border: none; background: transparent; }
QListWidget#prefNav { background: @side@; border: none; border-right: 1px solid @border@; padding: 10px 4px; font-size: 10pt; }
QListWidget#prefNav::item { padding: 9px 12px; margin: 2px 6px; border-radius: @rs@; }
QListWidget#prefNav::item:selected { background: @accent@; color: @on_accent@; font-weight: 600; }
QListWidget#prefNav::item:hover:!selected { background: @hover@; }
QLabel#prefTitle { font-size: 16pt; font-weight: 700; padding: 2px 0 12px 0; color: @fg@; }
QLabel#prefHint { color: @muted@; padding: 2px 0 8px 0; }
QFrame#prefCard { background: @card@; border: 1px solid @border@; border-radius: @rl@; }
QLineEdit#prefSearch { padding: 8px 14px; border-radius: 16px; font-size: 10pt; }
"""

TAB_QSS_TEMPLATE = """
QTabWidget::pane { border: 0; }
QTabBar { background: @activity@; }
QTabBar::tab { background: transparent; color: @muted@; padding: 8px 8px 8px 16px; margin: 6px 2px 0 2px;
    border: 1px solid transparent; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; min-width: 90px; }
QTabBar::tab:selected { background: @bg@; color: @fg@; border: 1px solid @border@; border-top: 2px solid @accent@; border-bottom: none; }
QTabBar::tab:hover:!selected { background: @hover@; color: @fg@; }
"""


def _fill_template(tpl, pal):
    return re.sub(r"@(\w+)@", lambda m: pal[m.group(1)], tpl)


def app_stylesheet(t):
    return _fill_template(QSS_TEMPLATE, ui_palette(t))


def tab_stylesheet(t):
    return _fill_template(TAB_QSS_TEMPLATE, ui_palette(t))


#  icon SVG (nét mảnh)
try:
    from PyQt5.QtSvg import QSvgRenderer
except ImportError:  # pragma: no cover
    QSvgRenderer = None

SVG_PATHS = {
    "explorer": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "git": '<circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="9" r="2.5"/>'
           '<path d="M6 8.5v7"/><path d="M18 11.5a6 6 0 0 1-6 6H8.5"/>',
    "todo": '<path d="M9 6h11M9 12h11M9 18h11"/><path d="M3.5 6l1.2 1.2L6.8 5M3.5 12l1.2 1.2L6.8 11M3.5 18l1.2 1.2L6.8 17"/>',
    "plugins": '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/>'
               '<rect x="4" y="13" width="7" height="7" rx="1.5"/><path d="M16.5 13v7M13 16.5h7"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1'
                'M16.6 16.6l2.1 2.1M18.7 5.3l-2.1 2.1M7.4 16.6l-2.1 2.1"/>',
    "run": '<path d="M7 4.5v15l12-7.5z"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="2"/>',
    "save": '<path d="M5 3h11l3 3v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M7 3v5h8V3M7 21v-7h10v7"/>',
    "build": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
    "newfile": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M12 12v6M9 15h6"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "dot": '<circle cx="12" cy="12" r="5"/>',
}
SVG_PATHS["open"] = SVG_PATHS["folder"]
SVG_PATHS["esp"] = ('<rect x="7" y="7" width="10" height="10" rx="1.5"/>'
                    '<path d="M9 3v4M15 3v4M9 17v4M15 17v4M3 9h4M3 15h4M17 9h4M17 15h4"/>')

# --- v4.4: thêm nhiều icon (nét 24x24, kiểu outline) ---
SVG_PATHS.update({
    "terminal": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9l3 3-3 3M13 15h4"/>',
    "bug": '<rect x="8" y="8" width="8" height="11" rx="4"/><path d="M9 8a3 3 0 0 1 6 0M4 13h4M16 13h4M5 7l3 2M19 7l-3 2M5 20l3-2.5M19 20l-3-2.5"/>',
    "palette": '<path d="M12 3a9 9 0 1 0 0 18c1.4 0 2-1 1.5-2-.6-1.2.2-2.5 1.6-2.5H17a4 4 0 0 0 4-4c0-5-4-9.5-9-9.5z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7" r="1"/><circle cx="15" cy="7" r="1"/>',
    "markdown": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 15V9l2.5 3L12 9v6M16 9v6M14.5 13.5L16 15l1.5-1.5"/>',
    "stats": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "rename": '<path d="M4 20h4L19 9a2.1 2.1 0 0 0-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
    "update": '<path d="M21 12a9 9 0 0 1-15.5 6.2M3 12a9 9 0 0 1 15.5-6.2"/><path d="M18.5 2v4h-4M5.5 22v-4h4"/>',
    "download": '<path d="M12 3v12M7 10l5 5 5-5M4 20h16"/>',
    "upload": '<path d="M12 21V9M7 14l5-5 5 5M4 4h16"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "incognito": '<path d="M3 12h18M5.5 12c.8-4.5 2.6-7 6.5-7s5.7 2.5 6.5 7"/><circle cx="8" cy="17.5" r="2.5"/><circle cx="16" cy="17.5" r="2.5"/><path d="M10.5 17h3"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.7"/><path d="M21 16l-5-5-8 8"/>',
    "video": '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3z"/>',
    "audio": '<path d="M4 10v4h4l5 4V6L8 10z"/><path d="M16.5 9a4 4 0 0 1 0 6M19 6.5a7.5 7.5 0 0 1 0 11"/>',
    "cube": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
    "hex": '<path d="M8 4L4 12l4 8M16 4l4 8-4 8"/>',
    "cpu": '<rect x="7" y="7" width="10" height="10" rx="1.5"/><rect x="10" y="10" width="4" height="4"/><path d="M9 3v4M15 3v4M9 17v4M15 17v4M3 9h4M3 15h4M17 9h4M17 15h4"/>',
    "plot": '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>',
    "wand": '<path d="M5 19L17 7l2 2L7 21z"/><path d="M14 4v3M12.5 5.5h3M19 14v3M17.5 15.5h3"/>',
    "scissors": '<circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><path d="M8 7.5L20 18M8 16.5L20 6"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    "bookmark": '<path d="M6 3h12v18l-6-4-6 4z"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "code": '<path d="M8 7l-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>',
    "braces": '<path d="M8 4c-2 0-3 1-3 3v2c0 1.5-1 3-2 3 1 0 2 1.5 2 3v2c0 2 1 3 3 3M16 4c2 0 3 1 3 3v2c0 1.5 1 3 2 3-1 0-2 1.5-2 3v2c0 2-1 3-3 3"/>',
    "canvas": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 15l5-4 4 3 4-5 5 4"/>',
    "zip": '<path d="M5 3h9l5 5v13H5z"/><path d="M14 3v5h5M10 8h2M10 11h2M10 14h2M10 17h2"/>',
})
SVG_PATHS.update({
    "font": '<path d="M4 20L10 5l6 15M6.5 15h7M17 11h3.5a2 2 0 0 1 0 4H17zM17 15h4a2 2 0 0 1 0 4h-4z"/>',
    "database": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>',
    "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    "sheet": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 10h16M4 15h16M10 4v16"/>',
    "slides": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M12 16v4M8 20h8"/>',
    "shader": '<path d="M12 3l9 16H3z"/><path d="M12 9l4.5 8h-9z"/>',
    "disk": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.5"/><path d="M12 3a9 9 0 0 1 9 9"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M16 7l3 3M14 9l2 2"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
    "book": '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11"/>',
    "chip": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "text": '<path d="M5 6h14M5 11h14M5 16h9"/>',
})
# nhóm file: đuôi -> nhóm; nhóm -> (màu nền, tên glyph SVG). Dùng cho icon cây thư mục khi đuôi chưa có huy hiệu riêng.
FILE_CATEGORY = {}
CATEGORY_STYLE = {
    "archive": ("#8d6e63", "zip"), "audio": ("#26a69a", "audio"), "video": ("#ef5350", "video"),
    "image": ("#a371f7", "image"), "model3d": ("#ec407a", "cube"), "font": ("#5c6bc0", "font"),
    "database": ("#f9a825", "database"), "document": ("#2b579a", "doc"), "sheet": ("#217346", "sheet"),
    "slides": ("#d24726", "slides"), "binary": ("#607d8b", "hex"), "firmware": ("#00979d", "chip"),
    "shader": ("#7e57c2", "shader"), "hardware": ("#2e7d32", "cpu"), "disk": ("#78909c", "disk"),
    "key": ("#c2185b", "key"), "config": ("#6d8086", "gear"), "book": ("#8e6a3d", "book"),
    "data": ("#cbb34a", "braces"), "text": ("#8a8f98", "text"), "code": ("#3f7ee8", "code"),
}
SVG_FILLED = {"run", "stop", "dot"}


def svg_pixmap(name, color, size=24, dpr=2.0):
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.fill(Qt.transparent)
    pm.setDevicePixelRatio(dpr)
    body = SVG_PATHS.get(name, "")
    if QSvgRenderer is None or not body:
        return pm
    fill = color if name in SVG_FILLED else "none"
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%s" stroke="%s" '
           'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">%s</svg>'
           % (fill, color, body))
    r = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    p = QPainter(pm)
    r.render(p, QRectF(0, 0, size, size))
    p.end()
    return pm


def make_icon(name, normal, active=None, checked=None, size=24):
    ic = QIcon()
    ic.addPixmap(svg_pixmap(name, normal, size), QIcon.Normal, QIcon.Off)
    ic.addPixmap(svg_pixmap(name, active or normal, size), QIcon.Active, QIcon.Off)
    ck = svg_pixmap(name, checked or active or normal, size)
    ic.addPixmap(ck, QIcon.Normal, QIcon.On)
    ic.addPixmap(ck, QIcon.Active, QIcon.On)
    return ic


#  badge loại file
FILE_BADGES = {
    ".py": ("Py", "#3776ab", "#ffffff"), ".pyw": ("Py", "#3776ab", "#ffffff"),
    ".js": ("JS", "#f7df1e", "#222222"), ".mjs": ("JS", "#f7df1e", "#222222"),
    ".ts": ("TS", "#3178c6", "#ffffff"), ".c": ("C", "#5c6bc0", "#ffffff"),
    ".h": ("H", "#7e57c2", "#ffffff"), ".cpp": ("C+", "#00599c", "#ffffff"),
    ".cc": ("C+", "#00599c", "#ffffff"), ".hpp": ("H+", "#7e57c2", "#ffffff"),
    ".go": ("Go", "#00add8", "#ffffff"), ".java": ("Jv", "#e76f00", "#ffffff"),
    ".json": ("{}", "#cbb34a", "#222222"), ".md": ("M", "#42a5f5", "#ffffff"),
    ".html": ("<>", "#e44d26", "#ffffff"), ".css": ("#", "#2965f1", "#ffffff"),
    ".ino": ("∞", "#00979d", "#ffffff"), ".cs": ("C#", "#68217a", "#ffffff"),
    ".rs": ("Rs", "#c97a4a", "#ffffff"), ".sh": ("$", "#4eaa25", "#ffffff"),
    ".bat": ("$", "#4eaa25", "#ffffff"), ".yml": ("Y", "#cb171e", "#ffffff"),
    ".yaml": ("Y", "#cb171e", "#ffffff"), ".toml": ("T", "#9c4221", "#ffffff"),
    ".txt": ("≡", "#8a8f98", "#ffffff"), ".csv": ("▦", "#217346", "#ffffff"),
    ".xml": ("<>", "#f08d49", "#ffffff"), ".png": ("▣", "#a371f7", "#ffffff"),
    ".jpg": ("▣", "#a371f7", "#ffffff"), ".log": ("≡", "#8a8f98", "#ffffff"),
}

FILE_BADGES.update({
    ".tsx": ("TS", "#3178c6", "#ffffff"), ".mts": ("TS", "#3178c6", "#ffffff"), ".cts": ("TS", "#3178c6", "#ffffff"),
    ".jsx": ("JX", "#f7df1e", "#222222"), ".cjs": ("JS", "#f7df1e", "#222222"),
    ".cxx": ("C+", "#00599c", "#ffffff"), ".hh": ("H+", "#7e57c2", "#ffffff"), ".hxx": ("H+", "#7e57c2", "#ffffff"),
    ".kt": ("Kt", "#7f52ff", "#ffffff"), ".kts": ("Kt", "#7f52ff", "#ffffff"), ".php": ("Ph", "#777bb4", "#ffffff"),
    ".rb": ("Rb", "#cc342d", "#ffffff"), ".lua": ("Lu", "#000080", "#ffffff"), ".sql": ("DB", "#e38c00", "#ffffff"),
    ".scss": ("S", "#cf649a", "#ffffff"), ".less": ("L", "#1d365d", "#ffffff"), ".htm": ("<>", "#e44d26", "#ffffff"),
    ".svg": ("◇", "#ffb13b", "#222222"), ".xaml": ("<>", "#512bd4", "#ffffff"), ".vue": ("V", "#42b883", "#ffffff"),
    ".ini": ("≡", "#6d8086", "#ffffff"), ".cfg": ("≡", "#6d8086", "#ffffff"), ".conf": ("≡", "#6d8086", "#ffffff"),
    ".ps1": (">_", "#012456", "#ffffff"), ".gitignore": ("◆", "#f05033", "#ffffff"),
    ".gif": ("▣", "#a371f7", "#ffffff"), ".jpeg": ("▣", "#a371f7", "#ffffff"), ".webp": ("▣", "#a371f7", "#ffffff"),
    ".bmp": ("▣", "#a371f7", "#ffffff"), ".ico": ("▣", "#a371f7", "#ffffff"),
    ".mp4": ("▶", "#ef5350", "#ffffff"), ".mkv": ("▶", "#ef5350", "#ffffff"), ".avi": ("▶", "#ef5350", "#ffffff"),
    ".mov": ("▶", "#ef5350", "#ffffff"), ".webm": ("▶", "#ef5350", "#ffffff"),
    ".mp3": ("♪", "#26a69a", "#ffffff"), ".wav": ("♪", "#26a69a", "#ffffff"), ".flac": ("♪", "#26a69a", "#ffffff"),
    ".ogg": ("♪", "#26a69a", "#ffffff"), ".m4a": ("♪", "#26a69a", "#ffffff"),
    ".glb": ("3D", "#ec407a", "#ffffff"), ".gltf": ("3D", "#ec407a", "#ffffff"), ".fbx": ("3D", "#ec407a", "#ffffff"),
    ".obj": ("3D", "#ec407a", "#ffffff"), ".stl": ("3D", "#ec407a", "#ffffff"), ".ply": ("3D", "#ec407a", "#ffffff"),
    ".zip": ("Z", "#8d6e63", "#ffffff"), ".7z": ("Z", "#8d6e63", "#ffffff"), ".rar": ("Z", "#8d6e63", "#ffffff"),
    ".tar": ("Z", "#8d6e63", "#ffffff"), ".gz": ("Z", "#8d6e63", "#ffffff"),
    ".pdf": ("PD", "#d32f2f", "#ffffff"), ".exe": ("⚙", "#607d8b", "#ffffff"), ".dll": ("⚙", "#607d8b", "#ffffff"),
    ".bin": ("01", "#607d8b", "#ffffff"), ".hex": ("01", "#607d8b", "#ffffff"),
    ".pt": ("AI", "#ee4c2c", "#ffffff"), ".pth": ("AI", "#ee4c2c", "#ffffff"),
    ".safetensors": ("AI", "#ee4c2c", "#ffffff"), ".ckpt": ("AI", "#ee4c2c", "#ffffff"),
    ".docx": ("W", "#2b579a", "#ffffff"), ".xlsx": ("X", "#217346", "#ffffff"), ".pptx": ("P", "#d24726", "#ffffff"),
})
_BADGE_CACHE = {}


def badge_pixmap(ext, size=16, dpr=2.0):
    key = (ext.lower(), size)
    if key in _BADGE_CACHE:
        return _BADGE_CACHE[key]
    entry = FILE_BADGES.get(ext.lower())
    glyph = None
    if entry is None:
        cat = FILE_CATEGORY.get(ext.lower())
        if cat in CATEGORY_STYLE:
            entry, glyph = ("", CATEGORY_STYLE[cat][0], "#ffffff"), CATEGORY_STYLE[cat][1]
    label, bg, fg = entry or ("•", "#6b7280", "#ffffff")
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.fill(Qt.transparent)
    pm.setDevicePixelRatio(dpr)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(bg))
    p.drawRoundedRect(QRectF(0.5, 0.5, size - 1, size - 1), 3.5, 3.5)
    if glyph:
        g = svg_pixmap(glyph, "#ffffff", size - 5, dpr)
        p.drawPixmap(QPointF(2.5, 2.5), g)
        p.end()
        _BADGE_CACHE[key] = pm
        return pm
    f = QFont()
    f.setBold(True)
    f.setPixelSize(10 if len(label) == 1 else 8)
    p.setFont(f)
    p.setPen(QColor(fg))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, label)
    p.end()
    _BADGE_CACHE[key] = pm
    return pm


def badge_icon(ext):
    return QIcon(badge_pixmap(ext))


class ModernIconProvider(QFileIconProvider):
    """Icon Explorer: thư mục vàng nhạt + badge màu theo đuôi file."""

    def __init__(self):
        super().__init__()
        self._folder = QIcon(svg_pixmap("folder", "#dcb67a", 16))

    def icon(self, arg):
        if isinstance(arg, QFileInfo):
            if arg.isDir():
                return self._folder
            name = arg.fileName().lower()
            return badge_icon(name if name in FILE_BADGES else "." + arg.suffix())
        if arg == QFileIconProvider.Folder:
            return self._folder
        return badge_icon(".txt")


class TabCloseButton(QToolButton):
    """Nút đóng tab: hiện chấm ● khi chưa lưu, rê chuột vào thì thành ✕."""

    def __init__(self, on_close):
        super().__init__()
        self.setAutoRaise(True)
        self.setFixedSize(18, 18)
        self.setIconSize(QSize(12, 12))
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Đóng")
        self._mod = False
        self._hover = False
        self._icons = None
        self.setStyleSheet("QToolButton { border: none; border-radius: 4px; padding: 0; background: transparent; }"
                           "QToolButton:hover { background: rgba(128, 128, 128, 70); }")
        self.clicked.connect(on_close)

    def set_icons(self, close_icon, dot_icon):
        self._icons = (close_icon, dot_icon)
        self._refresh()

    def set_modified(self, m):
        self._mod = bool(m)
        self._refresh()

    def _refresh(self):
        if self._icons:
            self.setIcon(self._icons[1] if (self._mod and not self._hover) else self._icons[0])

    def enterEvent(self, e):
        self._hover = True
        self._refresh()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self._refresh()
        super().leaveEvent(e)



def pick_font(size):
    families = set(QFontDatabase().families())
    for fam in ("Cascadia Code", "Consolas", "JetBrains Mono", "DejaVu Sans Mono",
                "Menlo", "Courier New"):
        if fam in families:
            f = QFont(fam, size)
            break
    else:
        f = QFont("Monospace", size)
    f.setStyleHint(QFont.Monospace)
    return f
