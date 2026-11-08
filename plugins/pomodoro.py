"""Đồng hồ Pomodoro hiện ở thanh trạng thái."""
from PyQt5.QtWidgets import QLabel

PLUGIN = {"name": "Pomodoro", "version": "1.0", "author": "GKcode",
          "description": "Làm việc 25 phút, nghỉ 5 phút; đồng hồ nằm ở thanh trạng thái (Plugins > Pomodoro)."}


def register(api):
    label = QLabel("🍅 --:--")
    label.setToolTip("Pomodoro — bấm menu Plugins > Pomodoro để bắt đầu")
    api.add_statusbar_widget(label)
    st = {"left": 0, "mode": "idle", "run": False}
    WORK, BREAK = 25 * 60, 5 * 60

    def show():
        m, s = divmod(max(st["left"], 0), 60)
        icon = {"work": "🍅", "break": "☕", "idle": "🍅"}[st["mode"]]
        label.setText("%s %02d:%02d%s" % (icon, m, s, "" if st["run"] or st["mode"] == "idle" else " ⏸"))

    def tick():
        if not st["run"]:
            return
        st["left"] -= 1
        if st["left"] <= 0:
            if st["mode"] == "work":
                st.update(mode="break", left=BREAK)
                api.notify("Hết 25 phút làm việc — nghỉ 5 phút nhé!")
            else:
                st.update(mode="work", left=WORK)
                api.notify("Hết giờ nghỉ — vào việc thôi!")
        show()

    def start():
        if st["mode"] == "idle":
            st.update(mode="work", left=WORK)
        st["run"] = True
        show()

    def pause():
        st["run"] = False
        show()

    def reset():
        st.update(mode="idle", left=0, run=False)
        label.setText("🍅 --:--")

    api.timer(1000, tick)
    api.add_action("Bắt đầu / tiếp tục", start)
    api.add_action("Tạm dừng", pause)
    api.add_action("Đặt lại", reset)
