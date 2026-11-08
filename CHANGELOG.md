# Nhật ký thay đổi

## 4.4
**Cấu trúc**
- Tách `main.py` 16.000 dòng thành package `gkcode/` (19 module) + `main.py` khởi chạy mỏng.
- Thêm `install_linux.sh`, `install_windows.bat`, icon ứng dụng, workflow GitHub Actions (CI + build bản phát hành).

**Ngôn ngữ & tệp**
- Tô màu + nhận đuôi file: C#, TypeScript, Rust, Kotlin, PHP, Ruby, Lua, CSS/SCSS, HTML/XML, YAML, TOML, INI, SQL,
  Swift, Dart, Scala, Groovy/Gradle, Zig, Perl, R, Haskell, Elixir, Objective-C, GLSL/HLSL, Verilog, VHDL, Assembly,
  LaTeX, Markdown, Protobuf, GraphQL, CMake, Makefile, Dockerfile. Nhận theo cả tên file (`Dockerfile`, `.env`...).
- Trình mở mới: kho nén (zip/tar/jar/apk/whl), SQLite (xem bảng + SELECT chỉ-đọc), font ttf/otf.
- Hơn 35 icon SVG mới; icon theo nhóm cho ~300 đuôi file.

**Hiệu năng**
- File > 2 MB đọc ở luồng nền, nạp từng đợt; > 6 MB tự vào chế độ file lớn (tắt tô màu / minimap / lint).
- Dòng > 100.000 ký tự bị cắt khi hiển thị (mở chỉ-đọc, không cho lưu đè).
- Terminal đệm output: chương trình in hàng trăm nghìn dòng không làm đơ giao diện.

**Soạn thảo**
- Chọn lần xuất hiện kế tiếp (Ctrl+Alt+J), đổi tên symbol (Ctrl+Alt+F2), đổi kiểu đặt tên (snake/camel/Pascal/kebab/UPPER),
  xem trước Markdown (Ctrl+Alt+M), thống kê tài liệu.

**Plugin**
- Plugins > Quản lý plugin: bật/tắt, cài từ file / zip / URL (kể cả link GitHub), gỡ.
- 4 plugin có sẵn: Thống kê dự án, Pomodoro, Chèn nhanh, Markdown tools.
- Plugin khai báo thông tin bằng `PLUGIN = {...}`.

**Khác**
- Help > Kiểm tra cập nhật (đọc phiên bản trên GitHub).
- Linux: tự chọn Wayland (lùi về X11); sửa lỗi giao diện trống với PyQt5 pip trên KDE/Wayland.

## 4.3 và cũ hơn
Xem lịch sử commit.
