#!/usr/bin/env bash
# ==============================================================================
# ClipMaster - Gỡ cài đặt
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Đang gỡ cài đặt ClipMaster..."

# 1. Dừng và vô hiệu hóa service
systemctl --user stop clipmaster.service 2>/dev/null || true
systemctl --user disable clipmaster.service 2>/dev/null || true
pkill -f "clipmaster.py" 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/clipmaster.service"
systemctl --user daemon-reload 2>/dev/null || true

# 2. Xóa phím tắt và autostart
python3 "$SCRIPT_DIR/clipmaster.py" --remove-shortcut 2>/dev/null || true
rm -f "$HOME/.local/share/applications/clipmaster.desktop"
rm -f "$HOME/.config/autostart/clipmaster.desktop"

echo "✓ Đã gỡ bỏ ClipMaster thành công."
