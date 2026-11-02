#!/usr/bin/env sh
# Cài GKcode vào menu ứng dụng (Fedora/Ubuntu/Arch...):  ./install_linux.sh   |  gỡ: ./install_linux.sh --remove
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor/256x256/apps"
if [ "$1" = "--remove" ]; then
  rm -f "$APPS/gkcode.desktop" "$ICONS/gkcode.png" "$HOME/Desktop/gkcode.desktop"
  echo "Đã gỡ GKcode khỏi menu."; exit 0
fi
command -v python3 >/dev/null || { echo "Cần cài python3"; exit 1; }
python3 -c "import PyQt5" 2>/dev/null || { echo "Thiếu PyQt5 -> chạy: pip install --user PyQt5"; exit 1; }
mkdir -p "$APPS" "$ICONS"
cp "$DIR/icon.png" "$ICONS/gkcode.png"
cat > "$APPS/gkcode.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=GKcode
GenericName=Code Editor
Comment=IDE Python / ESP / Arduino
Exec=python3 "$DIR/main.py" %F
Path=$DIR
Icon=$ICONS/gkcode.png
Terminal=false
Categories=Development;IDE;TextEditor;
MimeType=text/plain;text/x-python;text/x-csrc;text/x-c++src;text/x-csharp;text/html;text/css;application/json;text/markdown;
StartupWMClass=gkcode
StartupNotify=true
EOF
chmod +x "$APPS/gkcode.desktop"
[ -d "$HOME/Desktop" ] && cp "$APPS/gkcode.desktop" "$HOME/Desktop/gkcode.desktop" && chmod +x "$HOME/Desktop/gkcode.desktop"
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" 2>/dev/null || true
echo "Xong! Mở menu ứng dụng, gõ 'GKcode' để chạy (nếu chưa thấy, đăng xuất/đăng nhập lại)."
