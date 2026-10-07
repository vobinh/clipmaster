#!/usr/bin/env bash
# ==============================================================================
# ClipMaster - Script đóng gói thành file cài đặt .deb cho Ubuntu / Debian / Zorin OS
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_NAME="clipmaster"
VERSION="1.0.0"
ARCH="all"
DEB_DIR="$SCRIPT_DIR/build/deb_pkg"
OUTPUT_DEB="$SCRIPT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo "=========================================================="
echo "    📦 Đang đóng gói ClipMaster thành file cài đặt .deb   "
echo "=========================================================="

# 1. Dọn dẹp thư mục build cũ
rm -rf "$SCRIPT_DIR/build"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/lib/clipmaster"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$DEB_DIR/usr/lib/systemd/user"

# 2. Tạo file DEBIAN/control
cat << 'EOF' > "$DEB_DIR/DEBIAN/control"
Package: clipmaster
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, xsel, xdotool
Maintainer: Torin <support@clipmaster.local>
Description: Modern Clipboard Manager for Ubuntu / Linux (Win+V style)
 ClipMaster is a premium clipboard history manager for GNOME and Ubuntu-based
 distributions, bringing the seamless Windows + V experience to Linux with
 instant search, pinned items, auto-paste, and dark mode support.
EOF

# 3. Tạo file DEBIAN/postinst
cat << 'EOF' > "$DEB_DIR/DEBIAN/postinst"
#!/bin/sh
set -e

chmod +x /usr/lib/clipmaster/clipmaster.py
chmod +x /usr/bin/clipmaster

if which update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi

if which gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi

exit 0
EOF
chmod 755 "$DEB_DIR/DEBIAN/postinst"

# 4. Tạo file DEBIAN/prerm
cat << 'EOF' > "$DEB_DIR/DEBIAN/prerm"
#!/bin/sh
set -e
exit 0
EOF
chmod 755 "$DEB_DIR/DEBIAN/prerm"

# 5. Copy mã nguồn ứng dụng vào /usr/lib/clipmaster/
cp -r "$SCRIPT_DIR/clipmaster.py" "$DEB_DIR/usr/lib/clipmaster/"
cp -r "$SCRIPT_DIR/src" "$DEB_DIR/usr/lib/clipmaster/"
cp -r "$SCRIPT_DIR/assets" "$DEB_DIR/usr/lib/clipmaster/"

# Xóa các file cache pycache thừa nếu có
find "$DEB_DIR/usr/lib/clipmaster" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 6. Tạo file thực thi /usr/bin/clipmaster
cat << 'EOF' > "$DEB_DIR/usr/bin/clipmaster"
#!/bin/sh
exec python3 /usr/lib/clipmaster/clipmaster.py "$@"
EOF
chmod 755 "$DEB_DIR/usr/bin/clipmaster"

# 7. Tạo file launcher .desktop
cat << 'EOF' > "$DEB_DIR/usr/share/applications/clipmaster.desktop"
[Desktop Entry]
Name=ClipMaster
GenericName=Clipboard Manager
GenericName[vi]=Trình quản lý Clipboard
Comment=Windows + V style Clipboard History Manager for Linux
Comment[vi]=Quản lý lịch sử sao chép clipboard giống Windows + V
Exec=/usr/bin/clipmaster --toggle
Icon=clipmaster
Terminal=false
Type=Application
Categories=Utility;Accessories;
Keywords=clipboard;paste;copy;history;win+v;clipmaster;
StartupNotify=false
EOF
chmod 644 "$DEB_DIR/usr/share/applications/clipmaster.desktop"

# 8. Copy Icon hệ thống
cp "$SCRIPT_DIR/assets/icon.svg" "$DEB_DIR/usr/share/icons/hicolor/scalable/apps/clipmaster.svg"
chmod 644 "$DEB_DIR/usr/share/icons/hicolor/scalable/apps/clipmaster.svg"

# 9. Copy systemd user service template
cat << 'EOF' > "$DEB_DIR/usr/lib/systemd/user/clipmaster.service"
[Unit]
Description=ClipMaster Clipboard Daemon (Win+V Manager)
PartOf=graphical-session.target
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/clipmaster --daemon
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical-session.target
EOF
chmod 644 "$DEB_DIR/usr/lib/systemd/user/clipmaster.service"

# 10. Đóng gói thành file .deb bằng dpkg-deb
echo "Đang đóng gói deb bằng dpkg-deb..."
dpkg-deb --build --root-owner-group "$DEB_DIR" "$OUTPUT_DEB"

# Dọn dẹp thư mục tạm
rm -rf "$SCRIPT_DIR/build"

echo ""
echo "=========================================================="
echo "    ✅ ĐÓNG GÓI THÀNH CÔNG!                               "
echo "=========================================================="
echo "  📁 File cài đặt đã được tạo tại:"
echo "     👉 $OUTPUT_DEB"
echo ""
echo "  💡 Cách cài đặt file .deb này:"
echo "     - Cách 1: Click đúp vào file để mở trong Software Center / Eddy"
echo "     - Cách 2: Chạy lệnh terminal:"
echo "       sudo apt install ./$(basename "$OUTPUT_DEB")"
echo "       hoặc:"
echo "       sudo dpkg -i $(basename "$OUTPUT_DEB")"
echo "=========================================================="
