/**
 * ClipMaster i18n Translation Dictionary
 * Clean professional text without unicode emojis
 * Vietnamese (vi) and English (en)
 */

const I18N = {
  vi: {
    // Header & App Info
    app_title: "ClipMaster",
    app_subtitle: "Lịch sử Clipboard (Win + V)",
    app_subtitle_notes: "Ghi chú bảo mật & Cá nhân",
    tooltip_clear: "Xóa toàn bộ mục chưa ghim",
    tooltip_theme: "Chuyển chế độ Sáng / Tối",
    tooltip_settings: "Cài đặt",
    tooltip_close: "Đóng (Esc)",

    // Mode Switcher
    tab_history: "Lịch sử",
    tab_notes: "Ghi chú",

    // Search
    search_placeholder: "Tìm kiếm nội dung đã copy...",
    search_notes_placeholder: "Tìm kiếm trong ghi chú...",
    tooltip_search_toggle: "Tìm kiếm (Ctrl+F)",
    tooltip_search_clear: "Xóa tìm kiếm (Esc)",

    // Filters
    filter_all: "Tất cả",
    filter_text: "Văn bản",
    filter_code: "Code",
    filter_url: "Liên kết",
    filter_image: "Hình ảnh",
    filter_pinned: "Đã ghim",

    // Empty States
    empty_history_title: "Chưa có nội dung sao chép nào",
    empty_history_desc: "Sao chép bất kỳ văn bản, code hoặc liên kết (Ctrl + C) để lưu tự động.",
    empty_history_search: "Không tìm thấy kết quả phù hợp với từ khóa.",
    empty_notes_title: "Chưa có ghi chú nào",
    empty_notes_desc: "Nhấn nút thêm ở góc dưới để tạo ghi chú mới.",
    empty_notes_search: "Không tìm thấy ghi chú phù hợp với từ khóa.",

    // Footer
    footer_hint: "↑↓ Chọn • Enter Dán • Del Xóa",
    footer_clips_status: "Tổng cộng: {total} mục ({pinned} đã ghim)",
    footer_notes_status: "Ghi chú: {total} mục ({pinned} đã ghim)",

    // PIN Lock Screen
    pin_title: "Ghi chú được bảo vệ bằng mã PIN",
    pin_subtitle: "Vui lòng nhập mã PIN 4 chữ số để mở khóa",
    pin_key_clear: "Xóa hết",
    pin_btn_back: "Quay lại Lịch sử",
    pin_err_incorrect: "Sai mã PIN. Còn lại {attempts} lần thử.",
    pin_err_lockout: "Khóa tạm thời: Vui lòng đợi {seconds}s",

    // Note Modal
    tooltip_fab_note: "Tạo ghi chú mới (Ctrl+N)",
    modal_note_new: "Tạo ghi chú mới",
    modal_note_edit: "Chỉnh sửa ghi chú",
    note_label_title: "Tiêu đề (Tùy chọn)",
    note_placeholder_title: "Ví dụ: Tài khoản, Ý tưởng, Lệnh Git...",
    note_label_content: "Nội dung ghi chú *",
    note_placeholder_content: "Nhập nội dung ghi chú ở đây...",
    note_label_color: "Màu đánh dấu",
    btn_cancel: "Hủy",
    btn_save_note: "Lưu ghi chú",

    // Settings Modal
    settings_title: "Cài đặt ClipMaster",
    settings_tab_general: "Chung",
    settings_tab_storage: "Bộ nhớ",
    settings_tab_shortcut: "Phím tắt",
    settings_tab_security: "Bảo mật PIN",
    settings_tab_sync: "Đồng bộ",
    settings_tab_maintenance: "Dọn dẹp",
    settings_tab_about: "Thông tin",

    // Settings General
    sec_appearance: "Giao diện & Trải nghiệm",
    row_theme: "Chế độ giao diện",
    row_theme_desc: "Giao diện màu tối, sáng hoặc theo hệ thống",
    theme_dark: "Tối (Dark)",
    theme_light: "Sáng (Light)",
    row_lang: "Ngôn ngữ hiển thị",
    row_lang_desc: "Ngôn ngữ giao diện ứng dụng",
    sec_system: "Hệ thống",
    row_autostart: "Khởi động cùng hệ thống",
    row_autostart_desc: "Tự động chạy ClipMaster khi bật máy tính",

    // Settings Storage
    sec_behavior: "Hành vi Clipboard",
    row_auto_record: "Tự động ghi nhớ (Auto Record)",
    row_auto_record_desc: "Tự động lưu nội dung mới khi bạn nhấn Ctrl+C",
    row_auto_paste: "Tự động dán (Auto Paste)",
    row_auto_paste_desc: "Tự động dán và ẩn cửa sổ khi click chọn mục",
    row_save_images: "Lưu hình ảnh (Save Images)",
    row_save_images_desc: "Lưu trữ ảnh khi chụp màn hình hoặc copy ảnh",
    sec_limits: "Giới hạn lưu trữ",
    row_max_history: "Số lượng mục tối đa",
    row_max_history_desc: "Số mục chưa ghim tối đa được lưu trữ",
    opt_50_items: "50 mục",
    opt_100_items: "100 mục",
    opt_200_items: "200 mục (Mặc định)",
    opt_500_items: "500 mục",
    opt_1000_items: "1000 mục",

    // Settings Shortcut
    sec_shortcut: "Phím tắt toàn hệ thống",
    row_shortcut: "Phím tắt mở ClipMaster",
    row_shortcut_desc: "Nhấn tổ hợp phím này ở bất cứ đâu để mở ứng dụng",
    shortcut_hint: "Gợi ý: Trên Linux & Windows, phím Super + V (Win + V) mang lại trải nghiệm mở khay clipboard trực quan và tiện lợi nhất.",

    // Settings Security
    sec_pin_protect: "Bảo vệ mục Ghi chú",
    row_pin_protect: "Khóa Ghi chú bằng mã PIN",
    pin_status_on: "Trạng thái: ĐÃ BẬT bảo vệ PIN",
    pin_status_off: "Trạng thái: Chưa bật",
    sec_pin_setup: "Thiết lập mã PIN",
    pin_input_placeholder: "Nhập mã PIN mới (4 số)",
    btn_save_pin: "Lưu mã PIN",
    pin_hint: "Mã PIN gồm đúng 4 chữ số (0-9) dùng để bảo vệ quyền riêng tư các ghi chú.",
    row_pin_timeout: "Tự động khóa lại sau",
    row_pin_timeout_desc: "Thời gian không hoạt động trước khi khóa lại",
    pin_time_60: "1 phút",
    pin_time_300: "5 phút (Mặc định)",
    pin_time_900: "15 phút",
    pin_time_1800: "30 phút",
    pin_time_close: "Ngay khi đóng cửa sổ",

    // Settings Sync
    sec_sync: "Đồng bộ đám mây (BYOS)",
    row_sync_enable: "Bật đồng bộ đám mây",
    row_sync_enable_desc: "Đồng bộ các mục ghim và ghi chú giữa các thiết bị",
    sync_url_label: "URL Máy chủ (Sync Server URL)",
    sync_token_label: "Mã xác thực (API Token / Key)",
    row_sync_direction: "Hướng đồng bộ",
    row_sync_direction_desc: "Quy tắc trao đổi dữ liệu",
    sync_dir_both: "Hai chiều (Tải lên & Tải về)",
    sync_dir_push: "Chỉ tải lên máy chủ",
    sync_dir_pull: "Chỉ tải về từ máy chủ",
    btn_test_sync: "Kiểm tra kết nối",

    // Settings Maintenance
    sec_cleanup: "Dọn dẹp dữ liệu",
    row_clear_unpinned: "Xóa lịch sử chưa ghim",
    row_clear_unpinned_desc: "Giữ lại các mục quan trọng đã ghim",
    btn_clear_now: "Xóa ngay",
    sec_reset: "Khôi phục mặc định",
    row_reset_all: "Đặt lại toàn bộ cài đặt",
    row_reset_all_desc: "Khôi phục tất cả thiết lập về trạng thái ban đầu",
    btn_reset_now: "Khôi phục",

    // Settings About
    about_version: "Phiên bản 2.0.0 (Native Rust Edition)",
    about_desc: "Trình quản lý bộ nhớ tạm đa nền tảng tối ưu hiệu năng cao bằng Rust và Tauri v2. Hỗ trợ Linux, Windows và macOS.",
    about_copyright: "Giữ bản quyền © 2026 ClipMaster Open Source.",
    btn_save_settings: "Đóng & Lưu",

    // Card Actions
    tooltip_pin: "Ghim mục",
    tooltip_unpin: "Bỏ ghim",
    tooltip_delete: "Xóa",
    tooltip_edit: "Chỉnh sửa",

    // Alerts & Toasts
    alert_pin_length: "Mã PIN phải gồm đúng 4 chữ số (0-9)!",
    alert_pin_enter_first: "Vui lòng nhập 4 chữ số vào ô bên dưới và nhấn 'Lưu mã PIN' để kích hoạt.",
    alert_note_content_empty: "Vui lòng nhập nội dung ghi chú!",
    toast_copied: "Đã sao chép vào bộ nhớ tạm!",
    toast_note_pasted: "Đã dán ghi chú!",
    toast_note_saved: "Đã lưu ghi chú thành công!",
    toast_pin_saved: "Đã lưu mã PIN bảo mật!",
    toast_pin_disabled: "Đã tắt bảo vệ bằng mã PIN!",
    toast_settings_saved: "Đã lưu toàn bộ cài đặt!",
    toast_defaults_restored: "Đã khôi phục cài đặt gốc!",
    toast_cleaned: "Đã dọn dẹp {count} mục.",
    confirm_clear_unpinned: "Bạn có chắc chắn muốn xóa tất cả các mục lịch sử chưa được ghim?",
    confirm_reset_settings: "Khôi phục toàn bộ cài đặt về trạng thái ban đầu?",

    // Time
    time_just_now: "Vừa xong",
    time_secs_ago: "{secs} giây trước",
    time_mins_ago: "{mins} phút trước",
    time_hours_ago: "{hours} giờ trước"
  },

  en: {
    // Header & App Info
    app_title: "ClipMaster",
    app_subtitle: "Clipboard History (Win + V)",
    app_subtitle_notes: "Secure & Personal Notes",
    tooltip_clear: "Clear all unpinned items",
    tooltip_theme: "Toggle Light / Dark mode",
    tooltip_settings: "Settings",
    tooltip_close: "Close (Esc)",

    // Mode Switcher
    tab_history: "History",
    tab_notes: "Notes",

    // Search
    search_placeholder: "Search copied history...",
    search_notes_placeholder: "Search within notes...",
    tooltip_search_toggle: "Search (Ctrl+F)",
    tooltip_search_clear: "Clear search (Esc)",

    // Filters
    filter_all: "All",
    filter_text: "Text",
    filter_code: "Code",
    filter_url: "Links",
    filter_image: "Images",
    filter_pinned: "Pinned",

    // Empty States
    empty_history_title: "No clipboard history yet",
    empty_history_desc: "Copy any text, code snippet, or link (Ctrl + C) to auto-save.",
    empty_history_search: "No matching results found for this query.",
    empty_notes_title: "No notes yet",
    empty_notes_desc: "Click the add button below to create your first note.",
    empty_notes_search: "No matching notes found for this query.",

    // Footer
    footer_hint: "↑↓ Select • Enter Paste • Del Delete",
    footer_clips_status: "Total: {total} items ({pinned} pinned)",
    footer_notes_status: "Notes: {total} items ({pinned} pinned)",

    // PIN Lock Screen
    pin_title: "Notes protected by PIN code",
    pin_subtitle: "Please enter your 4-digit PIN to unlock",
    pin_key_clear: "Clear",
    pin_btn_back: "Back to History",
    pin_err_incorrect: "Incorrect PIN. {attempts} attempts remaining.",
    pin_err_lockout: "Temporarily locked: Please wait {seconds}s",

    // Note Modal
    tooltip_fab_note: "Create new note (Ctrl+N)",
    modal_note_new: "Create New Note",
    modal_note_edit: "Edit Note",
    note_label_title: "Title (Optional)",
    note_placeholder_title: "E.g. Credentials, Ideas, Git commands...",
    note_label_content: "Note Content *",
    note_placeholder_content: "Write your note content here...",
    note_label_color: "Tag Color",
    btn_cancel: "Cancel",
    btn_save_note: "Save Note",

    // Settings Modal
    settings_title: "ClipMaster Settings",
    settings_tab_general: "General",
    settings_tab_storage: "Storage",
    settings_tab_shortcut: "Shortcuts",
    settings_tab_security: "PIN Security",
    settings_tab_sync: "Cloud Sync",
    settings_tab_maintenance: "Maintenance",
    settings_tab_about: "About",

    // Settings General
    sec_appearance: "Appearance & Interface",
    row_theme: "Color Theme",
    row_theme_desc: "Dark, Light or follow system preferences",
    theme_dark: "Dark",
    theme_light: "Light",
    row_lang: "Display Language",
    row_lang_desc: "Application user interface language",
    sec_system: "System",
    row_autostart: "Start on System Boot",
    row_autostart_desc: "Automatically launch ClipMaster when computer starts",

    // Settings Storage
    sec_behavior: "Clipboard Behavior",
    row_auto_record: "Auto Record",
    row_auto_record_desc: "Automatically save copied items on Ctrl+C",
    row_auto_paste: "Auto Paste",
    row_auto_paste_desc: "Paste and auto-hide window upon selecting an item",
    row_save_images: "Save Images",
    row_save_images_desc: "Store images when screenshots or graphics are copied",
    sec_limits: "Storage Limits",
    row_max_history: "Maximum History Size",
    row_max_history_desc: "Maximum unpinned clips to preserve",
    opt_50_items: "50 items",
    opt_100_items: "100 items",
    opt_200_items: "200 items (Default)",
    opt_500_items: "500 items",
    opt_1000_items: "1000 items",

    // Settings Shortcut
    sec_shortcut: "System-wide Hotkey",
    row_shortcut: "Global Hotkey",
    row_shortcut_desc: "Press this hotkey anywhere to open ClipMaster",
    shortcut_hint: "Tip: On Linux & Windows, Super + V (Win + V) provides the most intuitive and standard clipboard experience.",

    // Settings Security
    sec_pin_protect: "Protect Notes Section",
    row_pin_protect: "Lock Notes with PIN",
    pin_status_on: "Status: PIN protection ACTIVE",
    pin_status_off: "Status: Disabled",
    sec_pin_setup: "Set PIN Code",
    pin_input_placeholder: "Enter new PIN (4 digits)",
    btn_save_pin: "Save PIN",
    pin_hint: "The PIN must be exactly 4 digits (0-9) to secure your personal notes.",
    row_pin_timeout: "Auto Lock Timeout",
    row_pin_timeout_desc: "Inactivity timeout before locking notes again",
    pin_time_60: "1 minute",
    pin_time_300: "5 minutes (Default)",
    pin_time_900: "15 minutes",
    pin_time_1800: "30 minutes",
    pin_time_close: "Immediately upon window close",

    // Settings Sync
    sec_sync: "Cloud Sync (BYOS)",
    row_sync_enable: "Enable Cloud Sync",
    row_sync_enable_desc: "Synchronize pinned items and notes across devices",
    sync_url_label: "Server URL (Sync Server URL)",
    sync_token_label: "Authentication Token (API Token / Key)",
    row_sync_direction: "Sync Direction",
    row_sync_direction_desc: "Data exchange policy",
    sync_dir_both: "Bidirectional (Upload & Download)",
    sync_dir_push: "Upload only (Push)",
    sync_dir_pull: "Download only (Pull)",
    btn_test_sync: "Test Connection",

    // Settings Maintenance
    sec_cleanup: "Data Maintenance",
    row_clear_unpinned: "Clear Unpinned Clips",
    row_clear_unpinned_desc: "Keep important pinned clips intact",
    btn_clear_now: "Clear Now",
    sec_reset: "Reset Defaults",
    row_reset_all: "Reset All Settings",
    row_reset_all_desc: "Restore all preferences to their factory defaults",
    btn_reset_now: "Reset",

    // Settings About
    about_version: "Version 2.0.0 (Native Rust Edition)",
    about_desc: "High-performance cross-platform clipboard manager built with Rust and Tauri v2. Runs on Linux, Windows, and macOS.",
    about_copyright: "Copyright © 2026 ClipMaster Open Source.",
    btn_save_settings: "Close & Save",

    // Card Actions
    tooltip_pin: "Pin item",
    tooltip_unpin: "Unpin",
    tooltip_delete: "Delete",
    tooltip_edit: "Edit",

    // Alerts & Toasts
    alert_pin_length: "PIN code must be exactly 4 digits (0-9)!",
    alert_pin_enter_first: "Please enter 4 digits below and click 'Save PIN' to activate.",
    alert_note_content_empty: "Please enter note content!",
    toast_copied: "Copied to clipboard!",
    toast_note_pasted: "Note pasted!",
    toast_note_saved: "Note saved successfully!",
    toast_pin_saved: "PIN code updated!",
    toast_pin_disabled: "PIN protection disabled!",
    toast_settings_saved: "Settings saved successfully!",
    toast_defaults_restored: "Factory settings restored!",
    toast_cleaned: "Cleaned {count} items.",
    confirm_clear_unpinned: "Are you sure you want to clear all unpinned items?",
    confirm_reset_settings: "Reset all settings to default values?",

    // Time
    time_just_now: "Just now",
    time_secs_ago: "{secs}s ago",
    time_mins_ago: "{mins}m ago",
    time_hours_ago: "{hours}h ago"
  }
};

window.I18N = I18N;
