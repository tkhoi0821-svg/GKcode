# -*- coding: utf-8 -*-
"""GKcode - Python IDE (gói nhiều module).

Các module được nạp theo thứ tự phụ thuộc; sau đó _link() bổ sung các tên tham
chiếu chéo (module trước dùng tên của module sau) để mọi module thấy đủ tên."""
import importlib as _il

_ORDER = ["common", "core", "theme", "editor", "langs", "terminal", "nettools", "esp", "templates",
          "polyglot", "plugins", "textools", "toolsmixin", "viewers", "media", "prefs", "filetypes", "pluginmgr",
          "extras", "app"]


def _link():
    mods = [_il.import_module(__name__ + "." + n) for n in _ORDER]
    for m in mods:
        g = vars(m)
        for o in mods:
            if o is m:
                continue
            for k, v in vars(o).items():
                if not k.startswith("__") and k not in g:
                    g[k] = v


_link()

if False:  # pragma: no cover - giúp PyInstaller thấy các module nạp động ở trên
    from . import (common, core, theme, editor, langs, terminal, nettools, esp, templates,  # noqa: F401
                   polyglot, plugins, textools, toolsmixin, viewers, media, prefs, filetypes, pluginmgr, extras, app)
from .common import APP_NAME, APP_VERSION  # noqa: E402,F401
