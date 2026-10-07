#!/usr/bin/env bash
# ==============================================================================
# ClipMaster - Cài đặt trình quản lý Clipboard (Win + V) trên Ubuntu / Linux
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "    🚀 Cài đặt ClipMaster (Windows + V trên Linux)       "
echo "=========================================================="

# 1. Cấp quyền thực thi
chmod +x "$SCRIPT_DIR/clipmaster.py"
if [ -f "$SCRIPT_DIR/uninstall.sh" ]; then
    chmod +x "$SCRIPT_DIR/uninstall.sh"
fi

# 2. Dừng các phiên bản cũ đang chạy ngầm
pkill -f "clipmaster.py" 2>/dev/null || true

# 3. Cài đặt icon vào hệ thống icon của người dùng
mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"
cp "$SCRIPT_DIR/assets/icon.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/clipmaster.svg"
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

# 4. Cài đặt phím tắt Win + V và launcher
python3 "$SCRIPT_DIR/clipmaster.py" --install-shortcut

# 3. Cấu hình systemd user service để chạy ngầm tự động
mkdir -p "$HOME/.config/systemd/user"
cat << EOF > "$HOME/.config/systemd/user/clipmaster.service"
[Unit]
Description=ClipMaster Clipboard Daemon (Win+V Manager)
PartOf=graphical-session.target
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $SCRIPT_DIR/clipmaster.py --daemon
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical-session.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now clipmaster.service

echo ""
echo "=========================================================="
echo "    ✅ CÀI ĐẶT THÀNH CÔNG!                               "
echo "=========================================================="
echo "  📌 Cách sử dụng:"
echo "     1. Nhấn phím 'Win + V' (hoặc 'Super + V') trên bàn phím"
echo "        cửa sổ ClipMaster sẽ hiện ra ngay lập tức!"
echo "     2. Click chuột hoặc nhấn Enter vào bất kỳ mục nào để dán."
echo "     3. Nhấn Esc để đóng cửa sổ bất cứ lúc nào."
echo "     4. Gõ vào ô tìm kiếm hoặc nhấn Ctrl+F để lọc lịch sử."
echo ""
echo "  📊 Trạng thái hiện tại:"
python3 "$SCRIPT_DIR/clipmaster.py" --status
echo "=========================================================="
