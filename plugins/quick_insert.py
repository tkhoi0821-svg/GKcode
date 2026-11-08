"""Chèn nhanh: UUID, ngày giờ, Lorem ipsum, giấy phép MIT."""
import datetime
import uuid

PLUGIN = {"name": "Chèn nhanh", "version": "1.0", "author": "GKcode",
          "description": "Chèn UUID, ngày/giờ, Lorem ipsum, header giấy phép MIT tại con trỏ (menu Plugins > Chèn nhanh)."}

LOREM = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
         "dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip "
         "ex ea commodo consequat.")
MIT = """MIT License

Copyright (c) {year} {holder}

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software.
"""
COMMENT = {"python": "# ", "ruby": "# ", "bash": "# ", "yaml": "# ", "toml": "# ", "lua": "-- ", "sql": "-- "}


def register(api):
    api.add_action("UUID mới", lambda: api.insert(str(uuid.uuid4())))
    api.add_action("Ngày hôm nay (YYYY-MM-DD)", lambda: api.insert(datetime.date.today().isoformat()))
    api.add_action("Ngày giờ hiện tại", lambda: api.insert(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    api.add_action("Unix timestamp", lambda: api.insert(str(int(datetime.datetime.now().timestamp()))))
    api.add_action("Lorem ipsum", lambda: api.insert(LOREM))

    def license_header():
        v = api.form("Header giấy phép MIT", [("holder", "Tên tác giả", "text", "Tên của bạn"),
                                              ("year", "Năm", "int", datetime.date.today().year)])
        if not v:
            return
        text = MIT.format(year=v["year"], holder=v["holder"]).rstrip("\n")
        lang = api.language() or ""
        if lang in COMMENT:
            body = "\n".join((COMMENT[lang] + l).rstrip() for l in text.split("\n"))
        elif lang in ("html", "xml"):
            body = "<!--\n" + text + "\n-->"
        else:
            body = "/*\n" + text + "\n*/"
        api.set_text(body + "\n\n" + api.text())

    api.add_action("Header giấy phép MIT (đầu file)", license_header)
