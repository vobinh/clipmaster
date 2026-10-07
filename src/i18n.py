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
        "search_placeholder": "🔍 Tìm kiếm nội dung đã copy... (Ctrl+F)",

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
        "search_placeholder": "🔍 Search copied history... (Ctrl+F)",

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
