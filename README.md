# GKcode 4.4

IDE Python/ESP/Arduino viết bằng PyQt5 (giao diện tiếng Việt).

## Chạy
    pip install -r requirements.txt
    python main.py            # hoặc run.bat / run.sh

> Linux/Wayland: main.py tự đặt `QT_QPA_PLATFORM=wayland;xcb`. Nếu giao diện vẫn trống, thử
> `QT_QPA_PLATFORM=xcb QT_X11_NO_MITSHM=1 python3 main.py`.

## Cài thành ứng dụng desktop
- Linux: `./install_linux.sh` (tạo mục GKcode trong menu ứng dụng + icon; gỡ bằng `--remove`)
- Windows: bấm đúp `install_windows.bat` (tạo lối tắt GKcode ngoài Desktop)

## Cấu trúc
    main.py            điểm khởi chạy
    gkcode/
      common.py        import chung, APP_VERSION, CFG (cấu hình dùng chung)
      core.py          tiện ích, ngôn ngữ, lệnh chạy/build
      theme.py         theme, QSS, icon SVG, huy hiệu file
      editor.py        highlighter, CodeEditor, FindBar, nạp file lớn
      langs.py         ngôn ngữ bổ sung: C#, TS, Rust, CSS, HTML, ...
      terminal.py      terminal (output đệm, không đơ)
      nettools.py      tải URL, git clone, thư mục plugin
      esp.py           ESP / Arduino IDE, Serial Plotter/Monitor
      templates.py     mẫu dự án, Python console
      polyglot.py      chạy đa ngôn ngữ, Code→Ảnh/3D
      plugins.py       PyAppAPI (API plugin), hộp thoại trình biên dịch C
      textools.py      công cụ văn bản, JSON, Regex, TODO, Git, REPL
      toolsmixin.py    menu công cụ
      viewers.py       trình xem ảnh/3D/hex/torch, đăng ký trình mở file
      media.py         trình phát, Dựng nhanh (ffmpeg)
      prefs.py         Cài đặt, kiểm API plugin
      extras.py        ExtrasMixin (v4.4: outline, Markdown, thống kê...)
      app.py           cửa sổ chính PyApp, splash, main()

## Mới trong 4.4
- Tách thành package nhiều module (dễ bảo trì, build bằng `--collect-submodules gkcode`).
- Thêm ngôn ngữ: C#, TypeScript, Rust, Kotlin, PHP, Ruby, Lua, CSS/SCSS, HTML/XML, YAML, TOML, INI, SQL;
  thêm từ khoá C++ hiện đại; nhận thêm đuôi file (.hh .hxx .jsx .jsonc ...).
- Hỗ trợ thêm ~25 ngôn ngữ/loại tệp: Swift, Dart, Scala, Groovy/Gradle, Zig, Perl, R, Haskell, Elixir, Objective-C,
  GLSL/HLSL, Verilog, VHDL, Assembly, LaTeX, Markdown, Protobuf, GraphQL, CMake, Makefile, Dockerfile...
  (nhận cả theo tên file: Dockerfile, Makefile, CMakeLists.txt, .gitignore, .env, package.json...).
- Trình mở mới: kho nén (zip/tar/tgz/jar/apk/whl), cơ sở dữ liệu SQLite (xem bảng + SELECT chỉ-đọc), font ttf/otf.
- Icon theo nhóm cho hàng trăm đuôi file (nén, âm thanh, video, ảnh, 3D, font, CSDL, tài liệu, firmware, khoá...).
- Hơn 35 icon SVG mới, huy hiệu cho ~60 loại file, 3 nút thanh công cụ mới.
- Chống đơ: file >2MB đọc ở luồng nền và nạp từng đợt; >6MB tắt tô màu/minimap/lint; dòng >100k ký tự
  bị cắt (mở chỉ đọc); terminal đệm output nên chương trình in hàng trăm nghìn dòng vẫn mượt.
- Chỉnh sửa: chọn lần xuất hiện kế tiếp (Ctrl+Alt+J), đổi tên symbol (Ctrl+Alt+F2), đổi kiểu đặt tên
  (snake/camel/Pascal/kebab/UPPER), xem trước Markdown (Ctrl+Alt+M), thống kê tài liệu.

## Đóng gói .exe
    pyinstaller --noconfirm --windowed --name GKcode --collect-submodules gkcode main.py
