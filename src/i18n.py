"""
ClipMaster Internationalization (i18n) Module
Supports Vietnamese (vi) and English (en).
"""

from typing import Dict, Any, Optional

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "vi": {
        # App Info
        "app_title": "ClipMaster",
        "app_subtitle": "Lịch sử Clipboard (Win + V)",
        "search_placeholder": "Tìm kiếm nội dung đã copy... (Ctrl+F)",

        # Filter Tabs
        "filter_all": "🌟 Tất cả",
        "filter_text": "📝 Văn bản",
        "filter_code": "💻 Code",
        "filter_url": "🔗 Link",
        "filter_image": "🖼️ Ảnh",
        "filter_pinned": "📌 Đã ghim",

        # Type Badges
        "badge_code": "MÃ CODE",
        "badge_link": "LINK: {domain}",
        "badge_color": "MÀU SẮC",
        "badge_image": "ẢNH ({w}x{h})",
        "badge_image_simple": "ẢNH",
        "badge_text": "VĂN BẢN ({chars} ký tự)",
        "badge_text_simple": "VĂN BẢN",

        # Card Buttons Tooltips
        "tooltip_unpin": "Bỏ ghim",
        "tooltip_pin": "Ghim mục này (không bị xóa)",
        "tooltip_copy": "Sao chép & dán ngay",
        "tooltip_delete": "Xóa khỏi lịch sử",
        "tooltip_settings": "Cài đặt & cấu hình",
        "tooltip_clear": "Xóa toàn bộ mục chưa ghim",
        "tooltip_record_on": "Tự động ghi nhớ: Đang BẬT (Bấm để tạm dừng)",
        "tooltip_record_off": "Tự động ghi nhớ: Đang TẮT (Bấm để bật lại)",
        "tooltip_theme_dark": "Giao diện: Tối (Bấm để chuyển sang Sáng)",
        "tooltip_theme_light": "Giao diện: Sáng (Bấm để chuyển sang Tối)",

        # Empty State
        "empty_title": "Chưa có nội dung sao chép nào",
        "empty_desc": "Sao chép văn bản, đường link hoặc ảnh (Ctrl + C)\nchúng sẽ tự động xuất hiện ở đây!\n\nNhấn Win + V bất cứ lúc nào để mở ClipMaster.",

        # Status Bar
        "status_total": "Tổng cộng: {total} mục  (Đã ghim: {pinned})",
        "status_hint": "Enter: Dán  •  Esc: Đóng",

        # Pause Warning Banner
        "pause_banner_text": "Đang tạm dừng ghi nhớ — nội dung copy sẽ không được lưu.",
        "pause_banner_resume": "Bật lại",

        # Toasts
        "toast_pinned": "📌 Đã ghim mục này",
        "toast_unpinned": "Đã bỏ ghim mục này",
        "toast_deleted": "🗑️ Đã xóa khỏi lịch sử",
        "toast_cleared": "🧹 Đã dọn dẹp {count} mục chưa ghim",
        "toast_record_resumed": "🟢 Đã tiếp tục tự động ghi nhớ clipboard",
        "toast_record_paused": "⏸️ Đã tạm dừng ghi nhớ (chế độ ẩn danh)",
        "toast_theme_dark": "🌙 Đã chuyển sang chế độ tối (Dark mode)",
        "toast_theme_light": "☀️ Đã chuyển sang chế độ sáng (Light mode)",

        # Notes Feature
        "tab_history": "📋 Lịch sử",
        "tab_notes": "📝 Ghi chú",
        "btn_create_note": "➕ Tạo ghi chú",
        "tooltip_create_note": "Tạo ghi chú mới (Ctrl+N)",
        "tooltip_edit_note": "Chỉnh sửa ghi chú",
        "note_dialog_new_title": "Tạo ghi chú mới",
        "note_dialog_edit_title": "Chỉnh sửa ghi chú",
        "note_title_label": "Tiêu đề (tùy chọn)",
        "note_title_placeholder": "Tiêu đề ghi chú...",
        "note_content_label": "Nội dung ghi chú",
        "note_content_placeholder": "Nhập nội dung ghi chú ở đây...",
        "btn_save_note": "Lưu ghi chú",
        "empty_notes_title": "Chưa có ghi chú nào",
        "empty_notes_desc": "Bấm nút '+ Tạo ghi chú' ở trên (hoặc nhấn Ctrl+N)\nđể lưu lại các đoạn mẫu câu, lệnh hay thông tin cần nhớ.",
        "status_notes_total": "Tổng cộng: {total} ghi chú  (Đã ghim: {pinned})",
        "toast_note_saved": "💾 Đã lưu ghi chú thành công",
        "toast_note_updated": "✏️ Đã cập nhật ghi chú",
        "toast_note_deleted": "🗑️ Đã xóa ghi chú",
        "toast_note_copied": "📋 Đã sao chép nội dung ghi chú",
        "filter_notes_all": "🌟 Tất cả",
        "filter_notes_pinned": "📌 Đã ghim",
        "search_notes_placeholder": "Tìm kiếm trong ghi chú...",

        # Notes PIN Security
        "pin_lock_title": "🔒 Ghi chú được bảo vệ bằng mã PIN",
        "pin_lock_subtitle": "Vui lòng nhập mã PIN 4 chữ số để mở khóa",
        "pin_lock_placeholder": "Mã PIN 4 số...",
        "btn_unlock": "Mở khóa",
        "pin_error_incorrect": "❌ Mã PIN không chính xác. Vui lòng thử lại.",
        "pin_lockout_msg": "⏳ Nhập sai quá 3 lần. Vui lòng chờ {seconds}s để thử lại",
        "pin_attempts_warning": "❌ Sai mã PIN. Bạn còn {remaining} lần thử",
        "btn_back_to_history": "← Quay lại Lịch sử",
        "group_notes_security": "🔐 Bảo mật Ghi chú",
        "group_notes_sec": "🔐 Bảo mật Ghi chú",
        "row_pin_enable": "Bảo vệ bằng mã PIN 4 số",
        "row_pin_enable_sub": "Yêu cầu mã PIN 4 số khi truy cập phần Ghi chú",
        "row_pin_change": "Đổi mã PIN",
        "row_pin_change_sub": "Thay đổi mã PIN 4 số hiện tại",
        "btn_change_pin": "Đổi mã PIN...",
        "row_pin_timeout": "Tự động khóa lại",
        "row_pin_timeout_sub": "Thời gian ghi nhớ mở khóa đúng PIN",
        "pin_timeout_0": "Khóa ngay lập tức (Mỗi lần vào Ghi chú)",
        "pin_timeout_60": "Sau 1 phút",
        "pin_timeout_300": "Sau 5 phút (Mặc định)",
        "pin_timeout_900": "Sau 15 phút",
        "pin_timeout_1800": "Sau 30 phút",
        "pin_timeout_close": "Khi đóng cửa sổ ClipMaster",
        "pin_dlg_title_set": "Cài đặt mã PIN 4 số",
        "pin_dlg_title_change": "Đổi mã PIN Ghi chú",
        "pin_dlg_current": "Mã PIN hiện tại",
        "pin_dlg_new": "Mã PIN mới (4 chữ số)",
        "pin_dlg_confirm": "Xác nhận mã PIN mới",
        "pin_dlg_err_len": "Mã PIN phải gồm đúng 4 chữ số (0-9)",
        "pin_dlg_err_mismatch": "Mã PIN xác nhận không trùng khớp",
        "pin_dlg_err_current": "Mã PIN hiện tại không chính xác",
        "toast_pin_enabled": "🔒 Đã kích hoạt bảo vệ bằng mã PIN",
        "toast_pin_disabled": "🔓 Đã tắt bảo vệ bằng mã PIN",
        "toast_pin_changed": "🔑 Đã đổi mã PIN thành công",

        # Settings Window
        "settings_title": "Cài đặt ClipMaster",
        "page_general": "Chung",

        # Settings: Appearance & Theme
        "group_appearance": "Giao diện &amp; Hiển thị",
        "row_theme": "Chế độ giao diện (Dark / Light)",
        "row_theme_sub": "Tùy chọn nền tối, sáng hoặc tự động theo hệ thống",
        "theme_system": "🌓 Tự động (Theo hệ thống)",
        "theme_dark": "🌙 Chế độ tối (Dark Mode)",
        "theme_light": "☀️ Chế độ sáng (Light Mode)",

        # Settings: Language
        "group_language": "Ngôn ngữ / Language",
        "row_language": "Ngôn ngữ giao diện",
        "row_language_sub": "Chọn ngôn ngữ hiển thị cho ClipMaster",

        # Settings: Shortcut
        "group_shortcut": "Phím tắt hệ thống",
        "group_shortcut_desc": "Tùy chỉnh phím tắt mở nhanh cửa sổ ClipMaster từ bất kỳ đâu",
        "row_active_shortcut": "Phím tắt đang sử dụng",
        "btn_change_shortcut": "Đổi phím tắt...",
        "row_preset": "Chọn nhanh phím tắt mẫu",
        "row_preset_sub": "Chọn một trong các tổ hợp phím phổ biến",
        "custom_option": "Tùy chỉnh khác...",

        # Settings: Behavior
        "group_behavior": "Trải nghiệm &amp; Hành vi",
        "row_auto_record": "Tự động ghi nhớ (Auto Record)",
        "row_auto_record_sub": "Tự động lưu nội dung mới khi copy. Tắt khi copy mật khẩu hoặc dữ liệu tạm thời.",
        "row_auto_paste": "Tự động dán (Auto Paste)",
        "row_auto_paste_sub": "Tự động nhấn Ctrl + V ngay sau khi click chọn mục",
        "row_save_images": "Lưu hình ảnh clipboard",
        "row_save_images_sub": "Tự động lưu ảnh chụp màn hình và ảnh copy",
        "row_autostart": "Khởi động cùng hệ thống",
        "row_autostart_sub": "Tự động chạy ngầm ClipMaster khi đăng nhập",

        # Settings: Storage
        "group_storage": "Lưu trữ lịch sử",
        "row_max_items": "Số lượng mục lưu trữ tối đa",
        "row_max_items_sub": "Các mục chưa ghim cũ nhất sẽ tự động được dọn dẹp",

        # Settings: Sync (BYOS)
        "group_sync": "☁️ Đồng bộ đám mây (BYOS)",
        "group_sync_desc": "Đồng bộ các mục đã ghim giữa nhiều máy qua Supabase project của riêng bạn",
        "row_sync_status": "Trạng thái kết nối",
        "row_sync_status_connected": "● Đã kết nối",
        "row_sync_status_disconnected": "○ Chưa kết nối",
        "row_sync_url": "Supabase URL",
        "row_sync_direction": "Hướng đồng bộ",
        "row_sync_direction_sub": "Tùy chọn tải lên, tải về hoặc cả hai chiều",
        "sync_dir_both": "🔄 Hai chiều (Tải về & Tải lên)",
        "sync_dir_download": "⬇️ Chỉ tải về từ Cloud (Download only)",
        "sync_dir_upload": "⬆️ Chỉ tải lên Cloud (Upload only)",
        "btn_sync_setup": "Cấu hình đồng bộ...",
        "btn_sync_now": "🔄 Đồng bộ ngay",
        "btn_sync_disconnect": "Ngắt kết nối",
        "toast_sync_done": "☁️ Đồng bộ hoàn tất",
        "toast_sync_disconnected": "Đã ngắt kết nối đồng bộ",

        # Settings: Danger
        "group_danger": "Dọn dẹp",
        "row_clear_all": "Xóa toàn bộ lịch sử",
        "row_clear_all_sub": "Xóa tất cả các mục chưa ghim",
        "btn_clear_now": "Dọn dẹp ngay",

        # Shortcut Dialog
        "shortcut_dlg_title": "Cài đặt phím tắt mới",
        "shortcut_dlg_header": "Bấm tổ hợp phím trên bàn phím",
        "shortcut_dlg_desc": "Nhấn tổ hợp phím bất kỳ (ví dụ: Ctrl + Alt + V, Win + C, F8...)\nhoặc chỉnh sửa mã phím tắt bên dưới:",
        "shortcut_dlg_accel_label": "Mã hệ thống: {code}",
        "shortcut_dlg_manual": "Mã phím tắt (GNOME Accelerator):",
        "shortcut_dlg_invalid": "Phím tắt không hợp lệ",
        "btn_default_win_v": "Mặc định (Win+V)",
        "btn_cancel": "Hủy",
        "btn_save": "Lưu phím tắt",

        # Relative Time
        "time_just_now": "Vừa xong",
        "time_secs_ago": "{secs} giây trước",
        "time_mins_ago": "{mins} phút trước",
        "time_hours_ago": "{hours} giờ trước",
        "time_yesterday": "Hôm qua {time}",
    },

    "en": {
        # App Info
        "app_title": "ClipMaster",
        "app_subtitle": "Clipboard History (Win + V)",
        "search_placeholder": "Search copied history... (Ctrl+F)",

        # Filter Tabs
        "filter_all": "🌟 All",
        "filter_text": "📝 Text",
        "filter_code": "💻 Code",
        "filter_url": "🔗 Links",
        "filter_image": "🖼️ Images",
        "filter_pinned": "📌 Pinned",

        # Type Badges
        "badge_code": "CODE",
        "badge_link": "LINK: {domain}",
        "badge_color": "COLOR",
        "badge_image": "IMAGE ({w}x{h})",
        "badge_image_simple": "IMAGE",
        "badge_text": "TEXT ({chars} chars)",
        "badge_text_simple": "TEXT",

        # Card Buttons Tooltips
        "tooltip_unpin": "Unpin item",
        "tooltip_pin": "Pin item (protect from clearing)",
        "tooltip_copy": "Copy & paste now",
        "tooltip_delete": "Delete from history",
        "tooltip_settings": "Settings & configuration",
        "tooltip_clear": "Clear all unpinned items",
        "tooltip_record_on": "Auto-record: ON (Click to pause)",
        "tooltip_record_off": "Auto-record: OFF (Click to resume)",
        "tooltip_theme_dark": "Theme: Dark (Click to switch to Light mode)",
        "tooltip_theme_light": "Theme: Light (Click to switch to Dark mode)",

        # Empty State
        "empty_title": "No clipboard history yet",
        "empty_desc": "Copy any text, link, or image (Ctrl + C)\nand it will automatically appear here!\n\nPress Win + V anytime to open ClipMaster.",

        # Status Bar
        "status_total": "Total: {total} items  (Pinned: {pinned})",
        "status_hint": "Enter: Paste  •  Esc: Close",

        # Pause Warning Banner
        "pause_banner_text": "Auto-recording paused — copied items will not be saved.",
        "pause_banner_resume": "Resume",

        # Toasts
        "toast_pinned": "📌 Item pinned",
        "toast_unpinned": "Item unpinned",
        "toast_deleted": "🗑️ Deleted from history",
        "toast_cleared": "🧹 Cleared {count} unpinned items",
        "toast_record_resumed": "🟢 Clipboard auto-recording resumed",
        "toast_record_paused": "⏸️ Clipboard recording paused (private mode)",
        "toast_theme_dark": "🌙 Switched to Dark mode",
        "toast_theme_light": "☀️ Switched to Light mode",

        # Notes Feature
        "tab_history": "📋 History",
        "tab_notes": "📝 Notes",
        "btn_create_note": "➕ New Note",
        "tooltip_create_note": "Create new note (Ctrl+N)",
        "tooltip_edit_note": "Edit note",
        "note_dialog_new_title": "Create New Note",
        "note_dialog_edit_title": "Edit Note",
        "note_title_label": "Title (optional)",
        "note_title_placeholder": "Note title...",
        "note_content_label": "Note Content",
        "note_content_placeholder": "Type your note content here...",
        "btn_save_note": "Save Note",
        "empty_notes_title": "No personal notes yet",
        "empty_notes_desc": "Click '+ New Note' above (or press Ctrl+N)\nto save templates, snippets, or important reminders.",
        "status_notes_total": "Total: {total} notes  (Pinned: {pinned})",
        "toast_note_saved": "💾 Note saved successfully",
        "toast_note_updated": "✏️ Note updated",
        "toast_note_deleted": "🗑️ Note deleted",
        "toast_note_copied": "📋 Note copied to clipboard",
        "filter_notes_all": "🌟 All",
        "filter_notes_pinned": "📌 Pinned",
        "search_notes_placeholder": "Search notes...",

        # Notes PIN Security
        "pin_lock_title": "🔒 Notes Protected by PIN",
        "pin_lock_subtitle": "Please enter your 4-digit PIN to unlock",
        "pin_lock_placeholder": "4-digit PIN...",
        "btn_unlock": "Unlock",
        "pin_error_incorrect": "❌ Incorrect PIN. Please try again.",
        "pin_lockout_msg": "⏳ 3 failed attempts. Please wait {seconds}s to try again",
        "pin_attempts_warning": "❌ Incorrect PIN. {remaining} attempt(s) left",
        "btn_back_to_history": "← Back to History",
        "group_notes_security": "🔐 Notes Security",
        "group_notes_sec": "🔐 Notes Security",
        "row_pin_enable": "Protect with 4-digit PIN",
        "row_pin_enable_sub": "Require 4-digit PIN to access Notes",
        "row_pin_change": "Change PIN",
        "row_pin_change_sub": "Update your current 4-digit PIN",
        "btn_change_pin": "Change PIN...",
        "row_pin_timeout": "Auto-lock Timeout",
        "row_pin_timeout_sub": "How long to keep Notes unlocked after correct PIN",
        "pin_timeout_0": "Immediately (Every time opening Notes)",
        "pin_timeout_60": "After 1 minute",
        "pin_timeout_300": "After 5 minutes (Default)",
        "pin_timeout_900": "After 15 minutes",
        "pin_timeout_1800": "After 30 minutes",
        "pin_timeout_close": "When closing ClipMaster window",
        "pin_dlg_title_set": "Set 4-Digit PIN",
        "pin_dlg_title_change": "Change Notes PIN",
        "pin_dlg_current": "Current PIN",
        "pin_dlg_new": "New 4-Digit PIN",
        "pin_dlg_confirm": "Confirm New PIN",
        "pin_dlg_err_len": "PIN must be exactly 4 digits (0-9)",
        "pin_dlg_err_mismatch": "Confirmation PIN does not match",
        "pin_dlg_err_current": "Current PIN is incorrect",
        "toast_pin_enabled": "🔒 PIN protection enabled",
        "toast_pin_disabled": "🔓 PIN protection disabled",
        "toast_pin_changed": "🔑 PIN updated successfully",

        # Settings Window
        "settings_title": "ClipMaster Settings",
        "page_general": "General",

        # Settings: Appearance & Theme
        "group_appearance": "Appearance &amp; Theme",
        "row_theme": "Color Scheme (Dark / Light)",
        "row_theme_sub": "Choose dark mode, light mode, or follow system theme",
        "theme_system": "🌓 Follow System",
        "theme_dark": "🌙 Dark Mode",
        "theme_light": "☀️ Light Mode",

        # Settings: Language
        "group_language": "Language",
        "row_language": "Display Language",
        "row_language_sub": "Select interface language for ClipMaster",

        # Settings: Shortcut
        "group_shortcut": "System Shortcut",
        "group_shortcut_desc": "Customize shortcut to open ClipMaster popup from anywhere",
        "row_active_shortcut": "Active shortcut",
        "btn_change_shortcut": "Change shortcut...",
        "row_preset": "Quick preset shortcuts",
        "row_preset_sub": "Choose from common key combinations",
        "custom_option": "Custom shortcut...",

        # Settings: Behavior
        "group_behavior": "Behavior &amp; Experience",
        "row_auto_record": "Auto Record Clipboard",
        "row_auto_record_sub": "Automatically capture new copied items. Turn off when copying passwords or sensitive data.",
        "row_auto_paste": "Auto Paste",
        "row_auto_paste_sub": "Automatically press Ctrl + V immediately after selecting an item",
        "row_save_images": "Save Clipboard Images",
        "row_save_images_sub": "Automatically save screenshots and copied images",
        "row_autostart": "Launch on Startup",
        "row_autostart_sub": "Run ClipMaster in the background on login",

        # Settings: Storage
        "group_storage": "History Storage",
        "row_max_items": "Maximum items stored",
        "row_max_items_sub": "Oldest unpinned items will be automatically pruned",

        # Settings: Sync (BYOS)
        "group_sync": "☁️ Cloud Sync (BYOS)",
        "group_sync_desc": "Sync pinned items across devices using your own Supabase project",
        "row_sync_status": "Connection Status",
        "row_sync_status_connected": "● Connected",
        "row_sync_status_disconnected": "○ Not connected",
        "row_sync_url": "Supabase URL",
        "row_sync_direction": "Sync Direction",
        "row_sync_direction_sub": "Choose upload, download, or two-way sync mode",
        "sync_dir_both": "🔄 Two-way (Upload & Download)",
        "sync_dir_download": "⬇️ Download only (from Cloud)",
        "sync_dir_upload": "⬆️ Upload only (to Cloud)",
        "btn_sync_setup": "Configure sync...",
        "btn_sync_now": "🔄 Sync now",
        "btn_sync_disconnect": "Disconnect",
        "toast_sync_done": "☁️ Sync complete",
        "toast_sync_disconnected": "Cloud sync disconnected",

        # Settings: Danger
        "group_danger": "Cleanup",
        "row_clear_all": "Clear All History",
        "row_clear_all_sub": "Delete all unpinned items",
        "btn_clear_now": "Clear Now",

        # Shortcut Dialog
        "shortcut_dlg_title": "Configure Shortcut",
        "shortcut_dlg_header": "Press keys on your keyboard",
        "shortcut_dlg_desc": "Press any key combination (e.g. Ctrl + Alt + V, Win + C, F8...)\nor edit the system code below:",
        "shortcut_dlg_accel_label": "System code: {code}",
        "shortcut_dlg_manual": "Shortcut code (GNOME Accelerator):",
        "shortcut_dlg_invalid": "Invalid shortcut combination",
        "btn_default_win_v": "Default (Win+V)",
        "btn_cancel": "Cancel",
        "btn_save": "Save Shortcut",

        # Relative Time
        "time_just_now": "Just now",
        "time_secs_ago": "{secs}s ago",
        "time_mins_ago": "{mins}m ago",
        "time_hours_ago": "{hours}h ago",
        "time_yesterday": "Yesterday {time}",
    }
}

AVAILABLE_LANGUAGES = [
    ("vi", "Tiếng Việt"),
    ("en", "English"),
]


def t(key: str, lang: str = "vi", **kwargs) -> str:
    """Translate key with optional formatting arguments."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["vi"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
