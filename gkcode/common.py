 # -*- coding: utf-8 -*-
#gkCODE make with GrayKazu.studio
#wed https://gkcode.graykazucode.workers.dev 
"""
Gray kazu 2012.CC BY 4.0 
tiktok @graykazu
""
GKcode - Python IDE (+ sketch .ino: F5 biên dịch/nạp/Serial, F6 xuất firmware .bin, F7 kiểm tra biên dịch;
v4.2: + trình mở file đa năng (ảnh/3D GLB-FBX-OBJ/video/hex/.pt), Dựng nhanh, F5 chạy .bat/.ps1/.sh/.hex,
Cài đặt dạng tab, kiểm API plugin trước khi nhập; v4.0: + minimap, trang chào, splash, 6 theme mới, chế độ Zen, tô từ trùng; v3.1: + gập code, bookmark, Preferences, chọn interpreter, pyflakes,
plugin Code→Ảnh / Code→3D (Python + C), chạy đa ngôn ngữ trong plugin)

Tính năng chính
  * Editor: tô màu cú pháp 6 ngôn ngữ (có chuỗi/comment nhiều dòng), số dòng,
    tự thụt lề, tự đóng ngoặc/nháy, gợi ý code (autocomplete), tô cặp ngoặc,
    Ctrl+/ comment, Ctrl+D nhân đôi dòng, Alt+Lên/Xuống di chuyển dòng, zoom.
  * Tìm / Thay thế (Ctrl+F / Ctrl+H) có Aa / từ nguyên / regex, tô mọi kết quả.
  * Explorer thư mục (Ctrl+B), nhớ phiên làm việc, hỏi lưu khi đóng.
  * Terminal: nhập liệu cho input(), nút Dừng, tự gợi ý cài thư viện thiếu.
  * Công cụ: tải URL, Git, nạp firmware ESP (esptool), Serial Monitor, mẫu dự án,
    Python Console, công cụ văn bản, plugin (menu Plugins).
  * Build EXE: PyInstaller với hidden-import, add-data, icon, onefile/onedir,
    tự dọn file tạm.
    phụ đề do claude chèn (chứng chỉ cc BY 4.0)
"""
import sys
import os
import re
import ast
import io
import json
import time
import tempfile
import subprocess
import textwrap
import shutil
import locale
import traceback
import math
import operator
import inspect
import hashlib
import base64
import uuid
import codecs
import datetime
import zipfile
import shlex
import contextlib
import importlib.util
import urllib.request
import urllib.parse
import csv
import code as pycode

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QPlainTextEdit, QTextEdit, QWidget,
    QVBoxLayout, QHBoxLayout, QSplitter, QFileDialog, QMessageBox, QAction,
    QActionGroup, QToolBar, QStyleFactory, QInputDialog, QLineEdit, QDialog,
    QLabel, QPushButton, QRadioButton, QButtonGroup, QDialogButtonBox,
    QProgressBar, QCompleter, QCheckBox, QDockWidget, QTreeView,
    QFileSystemModel, QShortcut, QListWidget, QListWidgetItem,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QColorDialog,
    QFormLayout, QSpinBox, QTreeWidget, QTreeWidgetItem, QScrollArea, QMenu, QToolButton,
    QFileIconProvider, QTabBar, QSplashScreen,
)
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QStackedWidget, QFrame
from PyQt5.QtCore import QObject
from PyQt5.QtGui import (
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QPainter, QTextFormat,
    QIcon, QTextCursor, QTextDocument, QKeySequence, QFontDatabase,
    QDesktopServices, QTextOption, QImage, QLinearGradient, QBrush, QPalette, QPen,
    QPolygonF, QFontMetrics, QAbstractTextDocumentLayout, QPixmap, QCursor,
)
from PyQt5.QtCore import (
    Qt, QRect, QSize, QProcess, QRegExp, QSettings, QTimer, pyqtSignal,
    QStringListModel, QProcessEnvironment, QUrl, QThread, QIODevice, QRectF, QPointF, QEvent, QByteArray, QFileInfo, QFileSystemWatcher,
)

class CFG:
    """Cấu hình dùng chung có thể gán lại (thay cho biến global)."""


APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # thư mục gốc (chứa main.py, plugins/, icon.ico)
APP_NAME = "GKcode"
APP_VERSION = "4.4"
REPO_SLUG = "tkhoi0821-svg/GKcode"          # GitHub: chủ/repo (dùng cho "Kiểm tra cập nhật")
REPO_URL = "https://github.com/" + REPO_SLUG
API_VERSION = "2.1"
