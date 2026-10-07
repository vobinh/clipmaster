#!/usr/bin/env bash
# ==============================================================================
# ClipMaster - Gỡ cài đặt
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Đang gỡ cài đặt ClipMaster..."

# 1. Dừng và vô hiệu hóa service, tắt tiến trình
systemctl --user stop clipmaster.service 2>/dev/null || true
systemctl --user disable clipmaster.service 2>/dev/null || true
pkill -9 -f "clipmaster.py" 2>/dev/null || true
pkill -9 -f "/snap/bin/clipmaster" 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/clipmaster.service"
systemctl --user daemon-reload 2>/dev/null || true

# 2. Xóa phím tắt và autostart
python3 "$SCRIPT_DIR/clipmaster.py" --remove-shortcut 2>/dev/null || true
rm -f "$HOME/.local/share/applications/clipmaster.desktop"
rm -f "$HOME/.local/share/applications/com.clipmaster.ClipMaster.desktop"
rm -f "$HOME/.config/autostart/clipmaster.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/clipmaster.svg"

# 3. Cập nhật cache hệ thống
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "✓ Đã gỡ bỏ sạch sẽ ClipMaster."
