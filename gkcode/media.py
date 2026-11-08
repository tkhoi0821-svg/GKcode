# -*- coding: utf-8 -*-
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor', 'terminal', 'nettools', 'esp', 'templates', 'polyglot', 'plugins', 'textools', 'toolsmixin', 'viewers']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n


def fmt_time(sec):
    sec = max(0, int(sec))
    return "%d:%02d:%02d" % (sec // 3600, sec % 3600 // 60, sec % 60) if sec >= 3600 else \
        "%d:%02d" % (sec // 60, sec % 60)


class MediaPlayerDialog(QDialog):
    def __init__(self, parent, path):
        super().__init__(parent)
        from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent  # có thể ném ImportError
        from PyQt5.QtMultimediaWidgets import QVideoWidget
        self.win = parent
        self.path = path
        self.QMediaPlayer = QMediaPlayer
        self.setWindowTitle(os.path.basename(path))
        self.resize(900, 600)
        lay = QVBoxLayout(self)
        self.video = QVideoWidget()
        self.video.setMinimumHeight(300)
        lay.addWidget(self.video, 1)
        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video)
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.seek = QSlider(Qt.Horizontal)
        self.seek.setRange(0, 0)
        self.seek.sliderMoved.connect(self.player.setPosition)
        lay.addWidget(self.seek)
        row = QHBoxLayout()
        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self.toggle)
        row.addWidget(self.play_btn)
        for text, d in (("−5s", -5000), ("+5s", 5000)):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, dd=d: self.player.setPosition(max(0, self.player.position() + dd)))
            row.addWidget(b)
        self.time = QLabel("0:00 / 0:00")
        row.addWidget(self.time)
        row.addStretch(1)
        self.rate = QComboBox()
        for r in ("0.25x", "0.5x", "1x", "1.5x", "2x"):
            self.rate.addItem(r)
        self.rate.setCurrentText("1x")
        self.rate.currentTextChanged.connect(lambda t: self.player.setPlaybackRate(float(t[:-1])))
        row.addWidget(QLabel("Tốc độ"))
        row.addWidget(self.rate)
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(80)
        self.vol.setMaximumWidth(110)
        self.vol.valueChanged.connect(self.player.setVolume)
        self.player.setVolume(80)
        row.addWidget(QLabel("🔊"))
        row.addWidget(self.vol)
        if os.path.splitext(path)[1].lower() in VIDEO_EXTS:
            b = QPushButton("📷 Chụp khung")
            b.clicked.connect(self.snapshot)
            row.addWidget(b)
        b = QPushButton("✂ Dựng nhanh")
        b.clicked.connect(lambda: _std_dialog(parent, QuickCutDialog(parent, [path])))
        row.addWidget(b)
        lay.addLayout(row)
        self.msg = QLabel("")
        lay.addWidget(self.msg)
        self.player.positionChanged.connect(self._pos)
        self.player.durationChanged.connect(lambda d: self.seek.setRange(0, d))
        self.player.stateChanged.connect(
            lambda s: self.play_btn.setText("⏸" if s == QMediaPlayer.PlayingState else "▶"))
        self.player.error.connect(lambda *_: self.msg.setText(
            "Lỗi phát: %s  (thiếu codec? thử Preferences > Video, hoặc mở bằng Dựng nhanh để chuyển đổi)"
            % self.player.errorString()))
        if cfg_get(parent, "media/autoplay", True, bool):
            self.player.play()

    def toggle(self):
        if self.player.state() == self.QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _pos(self, pos):
        if not self.seek.isSliderDown():
            self.seek.setValue(pos)
        self.time.setText("%s / %s" % (fmt_time(pos / 1000), fmt_time(self.player.duration() / 1000)))

    def snapshot(self):
        ff = find_ffmpeg(self.win)
        if not ff:
            self.msg.setText("Cần ffmpeg để chụp khung (Preferences > Video & Dựng nhanh).")
            return
        out = os.path.join(os.path.dirname(self.path), "%s_%s.png" % (
            os.path.splitext(os.path.basename(self.path))[0], fmt_time(self.player.position() / 1000).replace(":", "-")))
        rc, _o, err = run_capture([ff, "-y", "-ss", "%.3f" % (self.player.position() / 1000.0), "-i", self.path,
                                   "-frames:v", "1", out], timeout=60)
        if rc == 0 and os.path.isfile(out):
            self.win.view_image(out)
        else:
            self.msg.setText("Chụp thất bại: " + err[-200:])

    def closeEvent(self, e):
        self.player.stop()
        super().closeEvent(e)


# PHẦN 2C - Dựng nhanh: cắt / ghép / tốc độ / chữ / nhạc nền (dùng ffmpeg)
def find_ffmpeg(win=None):
    p = cfg_get(win, "ffmpeg/path", "") if win is not None else ""
    if p and os.path.isfile(p):
        return p
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg  # noqa: PLC0415
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.isfile(p):
            return p
    except Exception:  # noqa: BLE001
        pass
    for c in (r"C:\ffmpeg\bin\ffmpeg.exe", r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
              os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"),
              "/usr/local/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg"):
        if os.path.isfile(c):
            return c
    return None


def ffmpeg_probe(ff, path):
    """Đọc thời lượng / độ phân giải / fps / có âm thanh bằng `ffmpeg -i` (không cần ffprobe)."""
    _rc, out, err = run_capture([ff, "-hide_banner", "-i", path], timeout=30)
    txt = (out or "") + (err or "")
    d = {"dur": 0.0, "w": 0, "h": 0, "fps": 30.0, "audio": "Audio:" in txt}
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", txt)
    if m:
        d["dur"] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    m = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})", txt)
    if m:
        d["w"], d["h"] = int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+(?:\.\d+)?)\s*fps", txt)
    if m:
        d["fps"] = float(m.group(1))
    return d


def _atempo_chain(sp):
    parts = []
    while sp > 2.0:
        parts.append("atempo=2.0")
        sp /= 2.0
    while sp < 0.5:
        parts.append("atempo=0.5")
        sp /= 0.5
    parts.append("atempo=%.4f" % sp)
    return ",".join(parts)


def _ff_path(p):
    return p.replace("\\", "/").replace(":", r"\:")


def _find_font():
    for f in (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/Library/Fonts/Arial.ttf"):
        if os.path.isfile(f):
            return f
    return None


OUT_FORMATS = [("MP4 (H.264)", ".mp4"), ("MP4 (H.265 / HEVC)", ".mp4"), ("WebM (VP9)", ".webm"),
               ("GIF động", ".gif"), ("MP3 - chỉ âm thanh", ".mp3"), ("WAV - chỉ âm thanh", ".wav")]
RESOLUTIONS = [("Giữ theo clip đầu", None), ("1920×1080 (ngang)", (1920, 1080)),
               ("1280×720 (ngang)", (1280, 720)), ("1080×1920 (dọc 9:16)", (1080, 1920)),
               ("1080×1080 (vuông)", (1080, 1080)), ("854×480", (854, 480))]


class TimelineBar(QWidget):
    selected = pyqtSignal(int)

    def __init__(self, clips):
        super().__init__()
        self.clips, self.sel = clips, -1
        self.setMinimumHeight(64)
        self.setMaximumHeight(64)

    @staticmethod
    def clip_len(c):
        return max(0.01, (c["end"] - c["start"]) / max(0.01, c["speed"]))

    def _rects(self):
        tot = sum(self.clip_len(c) for c in self.clips) or 1.0
        x, out, W = 4.0, [], self.width() - 8.0
        for c in self.clips:
            w = max(18.0, W * self.clip_len(c) / tot)
            out.append(QRectF(x, 8, w - 2, self.height() - 16))
            x += w
        return out

    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#16181d"))
        cols = ["#3b6ea8", "#7a4fa3", "#2f8f6b", "#a8693b", "#a83b5c"]
        for i, r in enumerate(self._rects()):
            p.setBrush(QBrush(QColor(cols[i % 5])))
            p.setPen(QPen(QColor("#ffffff") if i == self.sel else QColor("#000000"), 2 if i == self.sel else 1))
            p.drawRoundedRect(r, 5, 5)
            p.setPen(QColor("#ffffff"))
            c = self.clips[i]
            p.drawText(r.adjusted(5, 2, -3, -2), Qt.AlignLeft | Qt.AlignVCenter,
                       "%d  %s\n%.1fs  ×%g" % (i + 1, os.path.basename(c["path"])[:18], self.clip_len(c), c["speed"]))
        p.end()

    def mousePressEvent(self, e):
        for i, r in enumerate(self._rects()):
            if r.contains(QPointF(e.pos())):
                self.sel = i
                self.selected.emit(i)
                self.update()
                return


class QuickCutDialog(QDialog):
    """Dựng nhanh - dựng video cơ bản bằng ffmpeg."""

    def __init__(self, parent, paths=()):
        super().__init__(parent)
        self.win = parent
        self.ff = find_ffmpeg(parent)
        self.clips = []
        self.texts = []
        self.proc = None
        self._loading = False
        self.setWindowTitle("Dựng nhanh - dựng video nhanh")
        self.resize(1180, 760)
        root = QHBoxLayout(self)
        #  trái: danh sách clip + preview + timeline
        left = QVBoxLayout()
        self.preview = None
        try:
            from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
            from PyQt5.QtMultimediaWidgets import QVideoWidget
            self._QMC = QMediaContent
            self.video = QVideoWidget()
            self.video.setMinimumSize(520, 300)
            self.player = QMediaPlayer(self)
            self.player.setVideoOutput(self.video)
            left.addWidget(self.video, 1)
            self.preview = True
        except ImportError:
            left.addWidget(QLabel("Không có QtMultimedia - vẫn dựng/xuất được, chỉ không xem trước."), 1)
        self.seek = QSlider(Qt.Horizontal)
        left.addWidget(self.seek)
        tr = QHBoxLayout()
        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self._toggle)
        self.tlabel = QLabel("0.00 s")
        tr.addWidget(self.play_btn)
        tr.addWidget(self.tlabel)
        for text, fn, tip in (("[ IN", self._set_in, "Đặt điểm bắt đầu tại vị trí hiện tại"),
                              ("OUT ]", self._set_out, "Đặt điểm kết thúc tại vị trí hiện tại"),
                              ("✂ Chia", self._split, "Chia clip thành 2 tại vị trí hiện tại")):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.clicked.connect(lambda _=False, f=fn: f())
            tr.addWidget(b)
        tr.addStretch(1)
        left.addLayout(tr)
        self.timeline = TimelineBar(self.clips)
        self.timeline.selected.connect(self._select)
        left.addWidget(self.timeline)
        lr = QHBoxLayout()
        for text, fn in (("+ Thêm clip...", self.add_clips), ("Xóa", self._remove), ("↑", lambda: self._move(-1)),
                         ("↓", lambda: self._move(1)), ("Nhân đôi", self._dup)):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, f=fn: f())
            lr.addWidget(b)
        left.addLayout(lr)
        self.listw = QListWidget()
        self.listw.setMaximumHeight(110)
        self.listw.currentRowChanged.connect(self._select)
        left.addWidget(self.listw)
        root.addLayout(left, 3)
        #  phải: thuộc tính
        right = QVBoxLayout()
        g = QGroupBox("Clip đang chọn")
        f = QFormLayout(g)
        self.sp_start = QDoubleSpinBox()
        self.sp_end = QDoubleSpinBox()
        for s in (self.sp_start, self.sp_end):
            s.setDecimals(2)
            s.setRange(0, 86400)
            s.setSuffix(" s")
            s.valueChanged.connect(self._clip_changed)
        self.sp_speed = QDoubleSpinBox()
        self.sp_speed.setRange(0.1, 8.0)
        self.sp_speed.setSingleStep(0.25)
        self.sp_speed.setValue(1.0)
        self.sp_speed.setSuffix("×")
        self.sp_vol = QSpinBox()
        self.sp_vol.setRange(0, 400)
        self.sp_vol.setValue(100)
        self.sp_vol.setSuffix(" %")
        self.chk_mute = QCheckBox("Tắt tiếng clip")
        self.cb_rot = QComboBox()
        self.cb_rot.addItems(["Không xoay", "Xoay 90° phải", "Xoay 180°", "Xoay 90° trái"])
        self.chk_flip = QCheckBox("Lật ngang")
        for w, sig in ((self.sp_speed, "valueChanged"), (self.sp_vol, "valueChanged"),
                       (self.chk_mute, "toggled"), (self.cb_rot, "currentIndexChanged"),
                       (self.chk_flip, "toggled")):
            getattr(w, sig).connect(self._clip_changed)
        f.addRow("Bắt đầu:", self.sp_start)
        f.addRow("Kết thúc:", self.sp_end)
        f.addRow("Tốc độ:", self.sp_speed)
        f.addRow("Âm lượng:", self.sp_vol)
        f.addRow(self.chk_mute)
        f.addRow("Xoay:", self.cb_rot)
        f.addRow(self.chk_flip)
        right.addWidget(g)
        g2 = QGroupBox("Chữ chèn (phụ đề)")
        v2 = QVBoxLayout(g2)
        self.text_list = QListWidget()
        self.text_list.setMaximumHeight(70)
        v2.addWidget(self.text_list)
        r2 = QHBoxLayout()
        b = QPushButton("+ Thêm chữ...")
        b.clicked.connect(self._add_text)
        b2 = QPushButton("Xóa")
        b2.clicked.connect(self._del_text)
        r2.addWidget(b)
        r2.addWidget(b2)
        v2.addLayout(r2)
        right.addWidget(g2)
        g3 = QGroupBox("Xuất video")
        f3 = QFormLayout(g3)
        self.cb_fmt = QComboBox()
        for n, _e in OUT_FORMATS:
            self.cb_fmt.addItem(n)
        self.cb_res = QComboBox()
        for n, _s in RESOLUTIONS:
            self.cb_res.addItem(n)
        self.cb_fps = QComboBox()
        self.cb_fps.addItems(["Giữ nguyên", "24", "30", "60"])
        self.sp_crf = QSpinBox()
        self.sp_crf.setRange(14, 40)
        self.sp_crf.setValue(cfg_get(parent, "cut/crf", 23, int))
        self.sp_crf.setToolTip("Nhỏ = đẹp/nặng, lớn = nhẹ/mờ. 18–28 là hợp lý.")
        self.cb_preset = QComboBox()
        self.cb_preset.addItems(["ultrafast", "veryfast", "medium", "slow"])
        self.cb_preset.setCurrentText(cfg_get(parent, "cut/preset", "veryfast") or "veryfast")
        self.sp_fin = QDoubleSpinBox()
        self.sp_fout = QDoubleSpinBox()
        for s in (self.sp_fin, self.sp_fout):
            s.setRange(0, 10)
            s.setSingleStep(0.5)
            s.setSuffix(" s")
        self.music = QLineEdit()
        self.music.setPlaceholderText("(tuỳ chọn) nhạc nền .mp3/.wav")
        mb = QPushButton("...")
        mb.clicked.connect(self._pick_music)
        mrow = QHBoxLayout()
        mrow.addWidget(self.music, 1)
        mrow.addWidget(mb)
        self.sp_mvol = QSpinBox()
        self.sp_mvol.setRange(0, 300)
        self.sp_mvol.setValue(40)
        self.sp_mvol.setSuffix(" %")
        self.chk_copy = QCheckBox("Cắt nhanh, không encode lại (1 clip, chỉ cắt)")
        f3.addRow("Định dạng:", self.cb_fmt)
        f3.addRow("Kích thước:", self.cb_res)
        f3.addRow("FPS:", self.cb_fps)
        f3.addRow("Chất lượng CRF:", self.sp_crf)
        f3.addRow("Tốc độ encode:", self.cb_preset)
        f3.addRow("Mờ dần vào:", self.sp_fin)
        f3.addRow("Mờ dần ra:", self.sp_fout)
        f3.addRow("Nhạc nền:", mrow)
        f3.addRow("Âm lượng nhạc:", self.sp_mvol)
        f3.addRow(self.chk_copy)
        right.addWidget(g3)
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("File xuất...")
        ob = QPushButton("Lưu thành...")
        ob.clicked.connect(self._pick_out)
        orow = QHBoxLayout()
        orow.addWidget(self.out_edit, 1)
        orow.addWidget(ob)
        right.addLayout(orow)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        right.addWidget(self.bar)
        er = QHBoxLayout()
        self.export_btn = QPushButton("▶ Xuất video")
        self.export_btn.clicked.connect(self.export)
        self.cancel_btn = QPushButton("Dừng")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel)
        er.addWidget(self.export_btn, 1)
        er.addWidget(self.cancel_btn)
        right.addLayout(er)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(90)
        self.log.setFont(mono_font(8))
        right.addWidget(self.log)
        rw = QWidget()
        rw.setLayout(right)
        rw.setMaximumWidth(380)
        root.addWidget(rw, 1)
        if self.preview:
            self.player.positionChanged.connect(self._pos)
            self.player.durationChanged.connect(lambda d: self.seek.setRange(0, d))
            self.seek.sliderMoved.connect(self.player.setPosition)
        if not self.ff:
            self._no_ffmpeg()
        for p in paths:
            self._add_path(p)

    #  ffmpeg
    def _no_ffmpeg(self):
        self.log.appendPlainText("Chưa tìm thấy ffmpeg. Cách nhanh: cài `pip install imageio-ffmpeg` "
                                 "(Preferences > Video & Dựng nhanh có nút cài), hoặc `winget install ffmpeg`, "
                                 "hoặc chọn ffmpeg.exe thủ công trong Preferences.")

    def _need_ff(self):
        self.ff = find_ffmpeg(self.win)
        if not self.ff:
            self._no_ffmpeg()
            QMessageBox.warning(self, "Thiếu ffmpeg", "Chưa có ffmpeg. Xem hướng dẫn trong khung nhật ký bên dưới.")
        return self.ff

    #  clip
    def add_clips(self):
        ps, _ = QFileDialog.getOpenFileNames(self, "Chọn video / audio", "",
                                             "Media (*.mp4 *.mkv *.avi *.mov *.webm *.wmv *.flv *.m4v *.mp3 *.wav "
                                             "*.m4a *.ogg *.flac);;Tất cả (*)")
        for p in ps:
            self._add_path(p)

    def _add_path(self, p):
        if not self._need_ff():
            return
        info = ffmpeg_probe(self.ff, p)
        if info["dur"] <= 0:
            self.log.appendPlainText("Không đọc được thời lượng: " + p)
            return
        self.clips.append({"path": p, "dur": info["dur"], "w": info["w"], "h": info["h"], "fps": info["fps"],
                           "audio": info["audio"], "start": 0.0, "end": info["dur"], "speed": 1.0,
                           "vol": 100, "mute": False, "rot": 0, "flip": False})
        if not self.out_edit.text():
            self.out_edit.setText(os.path.splitext(p)[0] + "_edit.mp4")
        self._refresh(len(self.clips) - 1)

    def _refresh(self, sel=-1):
        self.listw.blockSignals(True)
        self.listw.clear()
        for i, c in enumerate(self.clips):
            self.listw.addItem("%d. %s  [%.1f–%.1f s]  ×%g" % (i + 1, os.path.basename(c["path"]),
                                                              c["start"], c["end"], c["speed"]))
        self.listw.blockSignals(False)
        self.timeline.sel = sel
        self.timeline.update()
        if 0 <= sel < len(self.clips):
            self.listw.setCurrentRow(sel)
            self._select(sel)

    def _cur(self):
        i = self.timeline.sel
        return (i, self.clips[i]) if 0 <= i < len(self.clips) else (-1, None)

    def _select(self, i):
        if not (0 <= i < len(self.clips)):
            return
        self.timeline.sel = i
        self.timeline.update()
        c = self.clips[i]
        self._loading = True
        self.sp_start.setRange(0, c["dur"])
        self.sp_end.setRange(0, c["dur"])
        self.sp_start.setValue(c["start"])
        self.sp_end.setValue(c["end"])
        self.sp_speed.setValue(c["speed"])
        self.sp_vol.setValue(c["vol"])
        self.chk_mute.setChecked(c["mute"])
        self.cb_rot.setCurrentIndex(c["rot"] // 90)
        self.chk_flip.setChecked(c["flip"])
        self._loading = False
        if self.preview:
            self.player.setMedia(self._QMC(QUrl.fromLocalFile(c["path"])))
            self.player.setPosition(int(c["start"] * 1000))
            self.player.pause()

    def _clip_changed(self, *_a):
        if self._loading:
            return
        i, c = self._cur()
        if c is None:
            return
        c["start"] = min(self.sp_start.value(), self.sp_end.value() - 0.05)
        c["end"] = max(self.sp_end.value(), c["start"] + 0.05)
        c["speed"] = self.sp_speed.value()
        c["vol"] = self.sp_vol.value()
        c["mute"] = self.chk_mute.isChecked()
        c["rot"] = self.cb_rot.currentIndex() * 90
        c["flip"] = self.chk_flip.isChecked()
        self.listw.blockSignals(True)
        self.listw.item(i).setText("%d. %s  [%.1f–%.1f s]  ×%g" % (
            i + 1, os.path.basename(c["path"]), c["start"], c["end"], c["speed"]))
        self.listw.blockSignals(False)
        self.timeline.update()

    def _remove(self):
        i, c = self._cur()
        if c is not None:
            del self.clips[i]
            self._refresh(min(i, len(self.clips) - 1))

    def _move(self, d):
        i, c = self._cur()
        j = i + d
        if c is not None and 0 <= j < len(self.clips):
            self.clips[i], self.clips[j] = self.clips[j], self.clips[i]
            self._refresh(j)

    def _dup(self):
        i, c = self._cur()
        if c is not None:
            self.clips.insert(i + 1, dict(c))
            self._refresh(i + 1)

    #  preview
    def _toggle(self):
        if not self.preview:
            return
        from PyQt5.QtMultimedia import QMediaPlayer
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶")
        else:
            i, c = self._cur()
            if c is not None and not (c["start"] * 1000 <= self.player.position() < c["end"] * 1000):
                self.player.setPosition(int(c["start"] * 1000))
            self.player.play()
            self.play_btn.setText("⏸")

    def _pos(self, ms):
        if not self.seek.isSliderDown():
            self.seek.setValue(ms)
        self.tlabel.setText("%.2f s" % (ms / 1000.0))
        i, c = self._cur()
        if c is not None and ms >= c["end"] * 1000:
            self.player.pause()
            self.play_btn.setText("▶")

    def _now(self):
        return self.player.position() / 1000.0 if self.preview else 0.0

    def _set_in(self):
        if self._cur()[1] is not None:
            self.sp_start.setValue(min(self._now(), self.sp_end.value() - 0.05))

    def _set_out(self):
        if self._cur()[1] is not None:
            self.sp_end.setValue(max(self._now(), self.sp_start.value() + 0.05))

    def _split(self):
        i, c = self._cur()
        t = self._now()
        if c is None or not (c["start"] + 0.05 < t < c["end"] - 0.05):
            self.log.appendPlainText("Đưa vị trí xem trước vào giữa clip rồi mới Chia.")
            return
        c2 = dict(c)
        c2["start"], c["end"] = t, t
        self.clips.insert(i + 1, c2)
        self._refresh(i)

    #  chữ
    def _add_text(self):
        t, ok = QInputDialog.getText(self, "Chữ chèn", "Nội dung:")
        if not ok or not t.strip():
            return
        total = self._total_len() or 5.0
        s, ok = QInputDialog.getDouble(self, "Chữ chèn", "Hiện từ giây thứ:", 0.0, 0.0, 86400.0, 1)
        if not ok:
            return
        e, ok = QInputDialog.getDouble(self, "Chữ chèn", "Đến giây thứ:", min(total, s + 3.0), 0.0, 86400.0, 1)
        if not ok:
            return
        pos, ok = QInputDialog.getItem(self, "Chữ chèn", "Vị trí:", ["Dưới", "Giữa", "Trên"], 0, False)
        if not ok:
            return
        self.texts.append({"text": t, "start": s, "end": max(e, s + 0.1), "pos": pos})
        self.text_list.addItem("“%s”  %.1f–%.1f s  (%s)" % (t[:24], s, e, pos))

    def _del_text(self):
        r = self.text_list.currentRow()
        if r >= 0:
            del self.texts[r]
            self.text_list.takeItem(r)

    def _pick_music(self):
        p, _ = QFileDialog.getOpenFileName(self, "Nhạc nền", "", "Audio (*.mp3 *.wav *.m4a *.ogg *.flac);;Tất cả (*)")
        if p:
            self.music.setText(p)

    def _pick_out(self):
        ext = OUT_FORMATS[self.cb_fmt.currentIndex()][1]
        p, _ = QFileDialog.getSaveFileName(self, "Lưu video", self.out_edit.text() or "output" + ext,
                                           "Media (*%s);;Tất cả (*)" % ext)
        if p:
            self.out_edit.setText(p)

    def _total_len(self):
        return sum(TimelineBar.clip_len(c) for c in self.clips)

    #  dựng lệnh ffmpeg
    def build_command(self, out, tmpdir):
        fmt = self.cb_fmt.currentIndex()
        c0 = self.clips[0]
        res = RESOLUTIONS[self.cb_res.currentIndex()][1]
        W, H = res if res else (c0["w"] or 1280, c0["h"] or 720)
        W, H = W - W % 2, H - H % 2
        fps_t = self.cb_fps.currentText()
        fps = float(fps_t) if fps_t.replace(".", "").isdigit() else (c0["fps"] or 30.0)
        total = self._total_len()
        n = len(self.clips)
        simple = (self.chk_copy.isChecked() and n == 1 and abs(c0["speed"] - 1) < 1e-6 and not self.texts
                  and not self.music.text().strip() and not c0["rot"] and not c0["flip"]
                  and self.sp_fin.value() == 0 and self.sp_fout.value() == 0 and fmt in (0, 1, 2))
        if simple:
            return ([self.ff, "-y", "-hide_banner", "-progress", "pipe:1", "-nostats", "-ss", "%.3f" % c0["start"],
                     "-to", "%.3f" % c0["end"], "-i", c0["path"], "-c", "copy", out], total)
        args = [self.ff, "-y", "-hide_banner", "-progress", "pipe:1", "-nostats"]
        for c in self.clips:
            args += ["-i", c["path"]]
        music = self.music.text().strip()
        if music:
            args += ["-i", music]
        fc, vlist = [], ""
        for i, c in enumerate(self.clips):
            s, e, sp = c["start"], c["end"], c["speed"]
            v = "[%d:v]trim=start=%.3f:end=%.3f,setpts=(PTS-STARTPTS)/%.4f" % (i, s, e, sp)
            if c["rot"] == 90:
                v += ",transpose=1"
            elif c["rot"] == 180:
                v += ",hflip,vflip"
            elif c["rot"] == 270:
                v += ",transpose=2"
            if c["flip"]:
                v += ",hflip"
            v += (",scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black,"
                  "setsar=1,fps=%.3f,format=yuv420p[v%d]" % (W, H, W, H, fps, i))
            fc.append(v)
            dur_out = (e - s) / sp
            if c["audio"] and not c["mute"]:
                fc.append("[%d:a]atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS,%s,volume=%.2f,aresample=44100,"
                          "aformat=channel_layouts=stereo[a%d]" % (i, s, e, _atempo_chain(sp), c["vol"] / 100.0, i))
            else:
                fc.append("anullsrc=r=44100:cl=stereo,atrim=duration=%.3f,asetpts=PTS-STARTPTS[a%d]" % (dur_out, i))
            vlist += "[v%d][a%d]" % (i, i)
        fc.append("%sconcat=n=%d:v=1:a=1[vc][ac]" % (vlist, n))
        vlabel, alabel = "vc", "ac"
        # chữ
        font = _find_font()
        for k, t in enumerate(self.texts):
            tf = os.path.join(tmpdir, "t%d.txt" % k)
            with open(tf, "w", encoding="utf-8") as f:
                f.write(t["text"])
            y = {"Dưới": "h-th-%d" % max(30, H // 12), "Giữa": "(h-th)/2", "Trên": "%d" % max(30, H // 12)}[t["pos"]]
            dt = ("drawtext=textfile='%s':%sfontsize=%d:fontcolor=white:borderw=3:bordercolor=black:"
                  "x=(w-text_w)/2:y=%s:enable='between(t,%.2f,%.2f)'" % (
                      _ff_path(tf), ("fontfile='%s':" % _ff_path(font)) if font else "", max(18, H // 18), y,
                      t["start"], t["end"]))
            fc.append("[%s]%s[vt%d]" % (vlabel, dt, k))
            vlabel = "vt%d" % k
        fi, fo = self.sp_fin.value(), self.sp_fout.value()
        if fi > 0 or fo > 0:
            chain = []
            if fi > 0:
                chain.append("fade=t=in:st=0:d=%.2f" % fi)
            if fo > 0:
                chain.append("fade=t=out:st=%.2f:d=%.2f" % (max(0, total - fo), fo))
            fc.append("[%s]%s[vf]" % (vlabel, ",".join(chain)))
            vlabel = "vf"
            ach = []
            if fi > 0:
                ach.append("afade=t=in:st=0:d=%.2f" % fi)
            if fo > 0:
                ach.append("afade=t=out:st=%.2f:d=%.2f" % (max(0, total - fo), fo))
            fc.append("[%s]%s[af]" % (alabel, ",".join(ach)))
            alabel = "af"
        if music:
            fc.append("[%d:a]aresample=44100,volume=%.2f,aloop=loop=-1:size=2000000000,atrim=duration=%.3f[mus]"
                      % (n, self.sp_mvol.value() / 100.0, total))
            fc.append("[%s][mus]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[am]" % alabel)
            alabel = "am"
        if fmt == 3:       # GIF (bỏ âm thanh)
            fc.append("[%s]anullsink" % alabel)
            fc.append("[%s]fps=15,scale=min(480\\,iw):-1:flags=lanczos,split[g1][g2];[g1]palettegen[pg];"
                      "[g2][pg]paletteuse[vg]" % vlabel)
            args += ["-filter_complex", ";".join(fc), "-map", "[vg]", "-loop", "0", out]
            return args, total
        args += ["-filter_complex", ";".join(fc)]
        if fmt in (4, 5):
            args = args[:-2] + ["-filter_complex", ";".join(fc + ["[%s]nullsink" % vlabel])]
            args += ["-map", "[%s]" % alabel, "-vn"]
            args += ["-c:a", "libmp3lame", "-q:a", "2"] if fmt == 4 else ["-c:a", "pcm_s16le"]
        else:
            args += ["-map", "[%s]" % vlabel, "-map", "[%s]" % alabel]
            crf, pr = str(self.sp_crf.value()), self.cb_preset.currentText()
            if fmt == 0:
                args += ["-c:v", "libx264", "-crf", crf, "-preset", pr, "-pix_fmt", "yuv420p",
                         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
            elif fmt == 1:
                args += ["-c:v", "libx265", "-crf", crf, "-preset", pr, "-tag:v", "hvc1", "-pix_fmt", "yuv420p",
                         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
            else:
                args += ["-c:v", "libvpx-vp9", "-crf", crf, "-b:v", "0", "-c:a", "libopus"]
        args.append(out)
        return args, total

    #  xuất
    def export(self):
        if not self._need_ff():
            return
        if not self.clips:
            QMessageBox.information(self, "Chưa có clip", "Bấm '+ Thêm clip...' trước.")
            return
        out = self.out_edit.text().strip()
        ext = OUT_FORMATS[self.cb_fmt.currentIndex()][1]
        if not out:
            self._pick_out()
            out = self.out_edit.text().strip()
            if not out:
                return
        if os.path.splitext(out)[1].lower() != ext:
            out = os.path.splitext(out)[0] + ext
            self.out_edit.setText(out)
        self._tmp = tempfile.mkdtemp(prefix="gkcut_")
        try:
            args, total = self.build_command(out, self._tmp)
        except Exception:  # noqa: BLE001
            self.log.appendPlainText(traceback.format_exc())
            return
        self._total, self._out = max(0.1, total), out
        self.log.clear()
        self.log.appendPlainText("ffmpeg " + " ".join(shlex.quote(a) if " " in a else a for a in args[1:]))
        self.bar.setValue(0)
        self.proc = QProcess(self)
        self.proc.readyReadStandardOutput.connect(self._read_out)
        self.proc.readyReadStandardError.connect(
            lambda: self.log.appendPlainText(bytes(self.proc.readAllStandardError()).decode("utf-8", "replace")[-600:]))
        self.proc.finished.connect(self._done)
        self.export_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.proc.start(args[0], args[1:])

    def _read_out(self):
        txt = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
        for m in re.finditer(r"out_time_(?:us|ms)=(\d+)", txt):
            self.bar.setValue(min(1000, int(int(m.group(1)) / 1e6 * 1000 / self._total)))

    def _cancel(self):
        if self.proc is not None:
            self.proc.kill()

    def _done(self, code, _status):
        self.export_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        shutil.rmtree(getattr(self, "_tmp", ""), ignore_errors=True)
        if code == 0 and os.path.isfile(self._out):
            self.bar.setValue(1000)
            r = QMessageBox.question(self, "Xong", "Đã xuất:\n%s\n(%s)\n\nMở xem luôn?" % (
                self._out, human_size(os.path.getsize(self._out))))
            if r == QMessageBox.Yes:
                self.win.open_path(self._out)
        else:
            QMessageBox.warning(self, "Xuất lỗi", "ffmpeg trả về mã %s. Xem nhật ký bên dưới." % code)

    def closeEvent(self, e):
        if self.proc is not None and self.proc.state() != QProcess.NotRunning:
            self.proc.kill()
        if self.preview:
            self.player.stop()
        super().closeEvent(e)
