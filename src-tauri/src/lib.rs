pub mod clipboard;
pub mod commands;
pub mod database;
pub mod ipc;
pub mod shortcut;
pub mod sync;

use std::sync::Arc;
use commands::*;
use database::Database;
use clipboard::ClipboardManager;
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Manager,
};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let db = Arc::new(Database::new(None).expect("Failed to initialize database"));
    let clipboard = Arc::new(ClipboardManager::new());

    let db_for_setup = Arc::clone(&db);
    let clipboard_for_setup = Arc::clone(&clipboard);

    tauri::Builder::default()
        .manage(AppState {
            db: Arc::clone(&db),
            clipboard: Arc::clone(&clipboard),
        })
        .invoke_handler(tauri::generate_handler![
            get_clips,
            get_clip_image,
            copy_clip,
            copy_text,
            toggle_pin_clip,
            delete_clip,
            clear_unpinned,
            get_stats,
            get_notes,
            save_note,
            delete_note,
            toggle_pin_note,
            is_notes_pin_enabled,
            has_notes_pin,
            verify_notes_pin,
            set_notes_pin,
            change_notes_pin,
            disable_notes_pin,
            get_setting,
            set_setting,
            get_all_settings,
            reset_settings,
            set_autostart,
            test_sync_connection,
            auto_setup_sync_schema,
            sync_now,
            hide_window,
            close_window,
            drag_window,
            toggle_clipboard_pause,
            is_clipboard_paused,
            open_url,
        ])
        .setup(move |app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // Start background clipboard listener thread
            clipboard_for_setup.start_listener(
                Arc::clone(&db_for_setup),
                app.handle().clone(),
            );

            // Start background IPC Server for --toggle CLI shortcut
            ipc::start_ipc_server(app.handle().clone());

            // Ensure GNOME global shortcut is registered on Linux
            #[cfg(target_os = "linux")]
            {
                shortcut::ensure_shortcut_registered(&db_for_setup);
            }

            // Ensure window icon is explicitly set
            if let Some(window) = app.get_webview_window("main") {
                if let Some(icon) = app.default_window_icon() {
                    window.set_icon(icon.clone()).ok();
                }
            }

            // Setup Tray Menu with saved language & pause status
            let lang = db_for_setup.get_setting("language", "vi");
            let is_paused = clipboard_for_setup.is_paused();
            let (toggle_label, pause_label, quit_label, tooltip) = get_tray_labels(&lang, is_paused);

            let toggle_item = MenuItemBuilder::with_id("toggle", toggle_label).build(app)?;
            let pause_item = MenuItemBuilder::with_id("pause_toggle", pause_label).build(app)?;
            let quit_item = MenuItemBuilder::with_id("quit", quit_label).build(app)?;
            let menu = MenuBuilder::new(app)
                .item(&toggle_item)
                .separator()
                .item(&pause_item)
                .separator()
                .item(&quit_item)
                .build()?;

            let mut tray_builder = TrayIconBuilder::with_id("main-tray")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .tooltip(tooltip);

            if let Some(icon) = app.default_window_icon() {
                tray_builder = tray_builder.icon(icon.clone());
            }

            let _tray = tray_builder
                .on_menu_event(|app, event| match event.id().as_ref() {
                    "toggle" => {
                        if let Some(window) = app.get_webview_window("main") {
                            if window.is_visible().unwrap_or(false) {
                                window.hide().ok();
                            } else {
                                window.show().ok();
                                window.set_focus().ok();
                            }
                        }
                    }
                    "pause_toggle" => {
                        let state = app.state::<AppState>();
                        let paused = state.clipboard.toggle_pause();
                        update_tray_menu(app);
                        app.emit("clipboard_pause_changed", paused).ok();
                    }
                    "quit" => {
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            if window.is_visible().unwrap_or(false) {
                                window.hide().ok();
                            } else {
                                window.show().ok();
                                window.set_focus().ok();
                            }
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running clipmaster application");
}

pub fn get_tray_labels(lang: &str, is_paused: bool) -> (&'static str, &'static str, &'static str, &'static str) {
    if lang == "en" {
        let pause_label = if is_paused { "▶ Resume Monitoring" } else { "⏸ Pause Monitoring" };
        let tooltip = if is_paused { "ClipMaster - Monitoring Paused" } else { "ClipMaster - Clipboard Manager" };
        ("Toggle ClipMaster", pause_label, "Quit", tooltip)
    } else {
        let pause_label = if is_paused { "▶ Tiếp tục theo dõi (Resume)" } else { "⏸ Tạm dừng theo dõi (Pause)" };
        let tooltip = if is_paused { "ClipMaster - Đã tạm dừng theo dõi" } else { "ClipMaster - Quản lý Clipboard" };
        ("Hiện / Ẩn ClipMaster", pause_label, "Thoát", tooltip)
    }
}

pub fn update_tray_menu(app: &tauri::AppHandle) {
    if let Some(tray) = app.tray_by_id("main-tray") {
        let state = app.state::<AppState>();
        let lang = state.db.get_setting("language", "vi");
        let is_paused = state.clipboard.is_paused();

        let (toggle_label, pause_label, quit_label, tooltip) = get_tray_labels(&lang, is_paused);
        tray.set_tooltip(Some(tooltip)).ok();

        if let Ok(toggle_item) = MenuItemBuilder::with_id("toggle", toggle_label).build(app) {
            if let Ok(pause_item) = MenuItemBuilder::with_id("pause_toggle", pause_label).build(app) {
                if let Ok(quit_item) = MenuItemBuilder::with_id("quit", quit_label).build(app) {
                    if let Ok(menu) = MenuBuilder::new(app)
                        .item(&toggle_item)
                        .separator()
                        .item(&pause_item)
                        .separator()
                        .item(&quit_item)
                        .build()
                    {
                        tray.set_menu(Some(menu)).ok();
                    }
                }
            }
        }
    }
}

pub fn update_tray_language(app: &tauri::AppHandle, _lang: &str) {
    update_tray_menu(app);
}
