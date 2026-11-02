# -*- coding: utf-8 -*-
"""Chạy GKcode:  python main.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Linux: ưu tiên Wayland (KDE/GNOME), tự lùi về X11 nếu không dùng được.
# PyQt5 bản pip trên XWayland có thể vẽ giao diện trống/vỡ -> tránh bằng cách dùng Wayland gốc.
if sys.platform.startswith("linux") and "QT_QPA_PLATFORM" not in os.environ \
        and os.environ.get("WAYLAND_DISPLAY"):
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"
from gkcode.app import main  # noqa: E402

if __name__ == "__main__":
    main()
