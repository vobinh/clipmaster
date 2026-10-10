use crate::clipboard::ClipboardManager;
use crate::database::{ClipItem, Database, NoteItem, Stats};
use std::sync::Arc;
use tauri::{AppHandle, Emitter, Manager, State};

pub struct AppState {
    pub db: Arc<Database>,
    pub clipboard: Arc<ClipboardManager>,
}

#[tauri::command]
pub fn get_clips(
    state: State<AppState>,
    filter_type: Option<String>,
    query: Option<String>,
    limit: Option<i64>,
    offset: Option<i64>,
) -> Result<Vec<ClipItem>, String> {
    let f = filter_type.unwrap_or_else(|| "all".to_string());
    let q = query.unwrap_or_default();
    let l = limit.unwrap_or(200);
    let o = offset.unwrap_or(0);

    state
        .db
        .get_clips(&f, &q, l, o)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_clip_image(state: State<AppState>, id: i64) -> Result<String, String> {
    let clip = state
        .db
        .get_clip_by_id(id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| "Clip not found".to_string())?;

    let path_str = clip.image_path.ok_or_else(|| "No image path".to_string())?;
    let path = std::path::Path::new(&path_str);
    if !path.exists() {
        return Err("Image file not found".to_string());
    }

    let bytes = std::fs::read(path).map_err(|e| e.to_string())?;
    use base64::Engine;
    let b64 = base64::engine::general_purpose::STANDARD.encode(&bytes);
    Ok(format!("data:image/png;base64,{}", b64))
}

#[tauri::command]
pub fn copy_clip(
    state: State<AppState>,
    app_handle: AppHandle,
    id: i64,
) -> Result<(), String> {
    let clip = state
        .db
        .get_clip_by_id(id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| "Clip not found".to_string())?;

    if clip.r#type == "image" {
        if let Some(ref path_str) = clip.image_path {
            state.clipboard.set_image_from_path(path_str, &clip.content_hash)?;

            let auto_paste = state.db.get_setting("auto_paste", "1") == "1";
            if auto_paste {
                if let Some(window) = app_handle.get_webview_window("main") {
                    window.hide().ok();
                }
            }
            return Ok(());
        }
    } else if let Some(ref content) = clip.content {
        state.clipboard.set_text(content)?;

        let auto_paste = state.db.get_setting("auto_paste", "1") == "1";
        if auto_paste {
            if let Some(window) = app_handle.get_webview_window("main") {
                window.hide().ok();
            }
        }
        return Ok(());
    }

    Err("Clip content cannot be copied".to_string())
}

#[tauri::command]
pub fn copy_text(
    state: State<AppState>,
    app_handle: AppHandle,
    text: String,
) -> Result<(), String> {
    state.clipboard.set_text(&text)?;
    let auto_paste = state.db.get_setting("auto_paste", "1") == "1";
    if auto_paste {
        if let Some(window) = app_handle.get_webview_window("main") {
            window.hide().ok();
        }
    }
    Ok(())
}

#[tauri::command]
pub fn toggle_pin_clip(state: State<AppState>, id: i64) -> Result<bool, String> {
    state.db.toggle_pin(id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn delete_clip(state: State<AppState>, id: i64) -> Result<bool, String> {
    state.db.delete_clip(id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn clear_unpinned(state: State<AppState>) -> Result<usize, String> {
    state.db.clear_unpinned().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_stats(state: State<AppState>) -> Result<Stats, String> {
    state.db.get_stats().map_err(|e| e.to_string())
}

// ── Notes ──────────────────────────────────────────────

#[tauri::command]
pub fn get_notes(
    state: State<AppState>,
    query: Option<String>,
    filter_pinned: Option<bool>,
    limit: Option<i64>,
) -> Result<Vec<NoteItem>, String> {
    let q = query.unwrap_or_default();
    let p = filter_pinned.unwrap_or(false);
    let l = limit.unwrap_or(200);

    state.db.get_notes(&q, p, l).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn save_note(
    state: State<AppState>,
    id: Option<i64>,
    title: Option<String>,
    content: String,
    color: Option<String>,
) -> Result<i64, String> {
    let t = title.as_deref();
    let c = color.as_deref();

    if let Some(note_id) = id {
        state
            .db
            .update_note(note_id, t, &content, c)
            .map_err(|e| e.to_string())?;
        Ok(note_id)
    } else {
        let new_id = state
            .db
            .add_note(t, &content, false, c)
            .map_err(|e| e.to_string())?
            .ok_or_else(|| "Content cannot be empty".to_string())?;
        Ok(new_id)
    }
}

#[tauri::command]
pub fn delete_note(state: State<AppState>, id: i64) -> Result<bool, String> {
    state.db.delete_note(id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn toggle_pin_note(state: State<AppState>, id: i64) -> Result<bool, String> {
    state.db.toggle_pin_note(id).map_err(|e| e.to_string())
}

// ── Security & PIN ─────────────────────────────────────

#[tauri::command]
pub fn is_notes_pin_enabled(state: State<AppState>) -> bool {
    state.db.is_notes_pin_enabled()
}

#[tauri::command]
pub fn has_notes_pin(state: State<AppState>) -> bool {
    let hash = state.db.get_setting("notes_pin_hash", "");
    !hash.trim().is_empty()
}

#[tauri::command]
pub fn verify_notes_pin(state: State<AppState>, pin: String) -> bool {
    state.db.verify_notes_pin(&pin)
}

#[tauri::command]
pub fn set_notes_pin(state: State<AppState>, pin: String) -> bool {
    state.db.set_notes_pin(&pin)
}

#[tauri::command]
pub fn change_notes_pin(
    state: State<AppState>,
    old_pin: Option<String>,
    new_pin: String,
) -> Result<bool, String> {
    let hash = state.db.get_setting("notes_pin_hash", "");
    if !hash.trim().is_empty() {
        let old = old_pin.ok_or_else(|| "Vui lòng nhập mã PIN hiện tại".to_string())?;
        if !state.db.verify_notes_pin(&old) {
            return Err("Mã PIN hiện tại không chính xác!".to_string());
        }
    }

    let trimmed = new_pin.trim();
    if trimmed.len() != 4 || !trimmed.chars().all(|c| c.is_ascii_digit()) {
        return Err("Mã PIN phải gồm đúng 4 chữ số (0-9)!".to_string());
    }

    if state.db.set_notes_pin(trimmed) {
        Ok(true)
    } else {
        Err("Không thể cập nhật mã PIN".to_string())
    }
}

#[tauri::command]
pub fn disable_notes_pin(state: State<AppState>) {
    state.db.disable_notes_pin();
}

// ── Settings ───────────────────────────────────────────

#[tauri::command]
pub fn get_setting(state: State<AppState>, key: String, default_val: Option<String>) -> String {
    let def = default_val.unwrap_or_default();
    state.db.get_setting(&key, &def)
}

#[tauri::command]
pub fn set_setting(app: tauri::AppHandle, state: State<AppState>, key: String, value: String) -> Result<(), String> {
    state.db.set_setting(&key, &value).map_err(|e| e.to_string())?;
    if key == "shortcut" {
        #[cfg(target_os = "linux")]
        {
            crate::shortcut::install_gnome_shortcut(&value);
        }
    } else if key == "language" {
        crate::update_tray_language(&app, &value);
    }
    Ok(())
}

#[tauri::command]
pub fn get_all_settings(state: State<AppState>) -> Result<std::collections::HashMap<String, String>, String> {
    state.db.get_all_settings().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn reset_settings(state: State<AppState>) -> Result<(), String> {
    state.db.reset_settings().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn set_autostart(state: State<AppState>, enabled: bool) -> Result<(), String> {
    state.db.set_setting("autostart", if enabled { "1" } else { "0" }).map_err(|e| e.to_string())?;

    #[cfg(target_os = "linux")]
    {
        if let Ok(home) = std::env::var("HOME") {
            let autostart_dir = std::path::PathBuf::from(home).join(".config").join("autostart");
            let desktop_path = autostart_dir.join("clipmaster.desktop");
            if enabled {
                std::fs::create_dir_all(&autostart_dir).ok();
                if let Ok(exe) = std::env::current_exe() {
                    let content = format!(
                        "[Desktop Entry]\nType=Application\nName=ClipMaster\nComment=Modern Cross-Platform Clipboard Manager\nExec=\"{}\"\nIcon=clipmaster\nTerminal=false\nCategories=Utility;\nX-GNOME-Autostart-enabled=true\n",
                        exe.display()
                    );
                    std::fs::write(desktop_path, content).ok();
                }
            } else {
                std::fs::remove_file(desktop_path).ok();
            }
        }
    }
    Ok(())
}

#[tauri::command]
pub async fn test_sync_connection(
    state: State<'_, AppState>,
    url: Option<String>,
    key: Option<String>,
) -> Result<String, String> {
    let final_url = url.unwrap_or_else(|| state.db.get_setting("sync_url", ""));
    let final_key = key.unwrap_or_else(|| state.db.get_setting("sync_token", ""));
    crate::sync::test_connection(&final_url, &final_key).await
}

#[tauri::command]
pub async fn auto_setup_sync_schema(
    url: String,
    pat: String,
) -> Result<String, String> {
    crate::sync::auto_setup_schema(&url, &pat).await
}

#[tauri::command]
pub async fn sync_now(state: State<'_, AppState>) -> Result<String, String> {
    crate::sync::sync_now(&state.db).await
}

// ── Window Controls & Actions ──────────────────────────

#[tauri::command]
pub fn drag_window(app_handle: AppHandle) -> Result<(), String> {
    if let Some(window) = app_handle.get_webview_window("main") {
        window.start_dragging().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub fn hide_window(app_handle: AppHandle) {
    if let Some(window) = app_handle.get_webview_window("main") {
        window.hide().ok();
    }
}

#[tauri::command]
pub fn close_window(app_handle: AppHandle) {
    if let Some(window) = app_handle.get_webview_window("main") {
        window.close().ok();
    }
}

// ── Clipboard Pause / Resume Controls ──────────────────

#[tauri::command]
pub fn toggle_clipboard_pause(app_handle: AppHandle, state: State<AppState>) -> Result<bool, String> {
    let paused = state.clipboard.toggle_pause();
    crate::update_tray_menu(&app_handle);
    app_handle.emit("clipboard_pause_changed", paused).ok();
    Ok(paused)
}

#[tauri::command]
pub fn is_clipboard_paused(state: State<AppState>) -> Result<bool, String> {
    Ok(state.clipboard.is_paused())
}

#[tauri::command]
pub fn open_url(url: String) -> Result<(), String> {
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(&url)
            .spawn()
            .map_err(|e| format!("Không thể mở trình duyệt: {}", e))?;
    }
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("cmd")
            .args(["/c", "start", &url])
            .spawn()
            .map_err(|e| format!("Không thể mở trình duyệt: {}", e))?;
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&url)
            .spawn()
            .map_err(|e| format!("Không thể mở trình duyệt: {}", e))?;
    }
    Ok(())
}


