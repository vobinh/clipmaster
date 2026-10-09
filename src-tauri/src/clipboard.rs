use crate::database::{compute_sha256, Database};
use arboard::Clipboard;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use tauri::{AppHandle, Emitter};

pub fn detect_content_type(text: &str) -> &'static str {
    let clean = text.trim();
    if clean.is_empty() {
        return "text";
    }

    // Hex color: #fff or #ffffff or #ffffffff
    if clean.starts_with('#') && (clean.len() == 4 || clean.len() == 7 || clean.len() == 9) {
        if clean[1..].chars().all(|c| c.is_ascii_hexdigit()) {
            return "color";
        }
    }

    // RGB / RGBA / HSL color
    if (clean.starts_with("rgb(") || clean.starts_with("rgba(") || clean.starts_with("hsl("))
        && clean.ends_with(')')
    {
        return "color";
    }

    // URL
    if (clean.starts_with("http://") || clean.starts_with("https://") || clean.starts_with("ftp://"))
        && !clean.contains('\n')
        && !clean.contains(' ')
    {
        return "url";
    }

    // JSON
    if (clean.starts_with('{') && clean.ends_with('}'))
        || (clean.starts_with('[') && clean.ends_with(']'))
    {
        if clean.len() > 10 && (clean.contains(':') || clean.contains(',')) {
            return "code";
        }
    }

    // Code keywords
    let code_keywords = [
        "fn ", "def ", "function ", "class ", "import ", "from ", "#include",
        "const ", "let ", "var ", "console.log", "println!", "SELECT ", "INSERT INTO ",
        "UPDATE ", "WHERE ", "<!DOCTYPE", "<div", "<html", "<span", "#!/bin/",
        "sudo apt", "git commit", "docker run", "npm install", "cargo ",
    ];

    for kw in code_keywords {
        if clean.contains(kw) {
            return "code";
        }
    }

    // Multi-line code markers
    let lines: Vec<&str> = clean.lines().collect();
    if lines.len() >= 3 {
        let markers = lines
            .iter()
            .filter(|l| {
                let trimmed = l.trim();
                trimmed.ends_with(';')
                    || trimmed.ends_with('{')
                    || trimmed.ends_with('}')
                    || trimmed.ends_with(':')
                    || l.starts_with("    ")
                    || l.starts_with('\t')
            })
            .count();

        if (markers as f64 / lines.len() as f64) > 0.4 {
            return "code";
        }
    }

    "text"
}

pub struct ClipboardManager {
    last_hash: Arc<Mutex<String>>,
    is_paused: Arc<std::sync::atomic::AtomicBool>,
}

impl ClipboardManager {
    pub fn new() -> Self {
        Self {
            last_hash: Arc::new(Mutex::new(String::new())),
            is_paused: Arc::new(std::sync::atomic::AtomicBool::new(false)),
        }
    }

    pub fn is_paused(&self) -> bool {
        self.is_paused.load(std::sync::atomic::Ordering::Relaxed)
    }

    pub fn set_paused(&self, paused: bool) {
        self.is_paused.store(paused, std::sync::atomic::Ordering::Relaxed);
    }

    pub fn toggle_pause(&self) -> bool {
        let current = self.is_paused.load(std::sync::atomic::Ordering::Relaxed);
        let next = !current;
        self.is_paused.store(next, std::sync::atomic::Ordering::Relaxed);
        next
    }

    pub fn set_text(&self, text: &str) -> Result<(), String> {
        let mut clip = Clipboard::new().map_err(|e| e.to_string())?;
        
        // Update last_hash to prevent re-recording our own copied clip
        let hash = compute_sha256(text.as_bytes());
        if let Ok(mut h) = self.last_hash.lock() {
            *h = hash;
        }

        clip.set_text(text).map_err(|e| e.to_string())
    }

    pub fn start_listener(
        &self,
        db: Arc<Database>,
        app_handle: AppHandle,
    ) {
        let last_hash_clone = Arc::clone(&self.last_hash);
        let is_paused_clone = Arc::clone(&self.is_paused);

        thread::spawn(move || {
            let mut clip_res = Clipboard::new();
            if let Err(ref e) = clip_res {
                eprintln!("[ClipMaster] Cảnh báo khởi tạo clipboard: {}", e);
            }

            loop {
                thread::sleep(Duration::from_millis(400));

                // If clipboard recording is paused or auto_record is disabled, skip checking
                if is_paused_clone.load(std::sync::atomic::Ordering::Relaxed) {
                    continue;
                }

                let auto_record = db.get_setting("auto_record", "1") != "0";
                if !auto_record {
                    continue;
                }

                let text_res = match &mut clip_res {
                    Ok(clip) => clip.get_text(),
                    Err(_) => {
                        clip_res = Clipboard::new();
                        match &mut clip_res {
                            Ok(clip) => clip.get_text(),
                            Err(_) => continue,
                        }
                    }
                };

                if let Ok(text) = text_res {
                    let clean = text.trim();
                    if !clean.is_empty() {
                        let hash = compute_sha256(text.as_bytes());
                        let mut last = last_hash_clone.lock().unwrap();

                        if *last != hash {
                            *last = hash.clone();
                            drop(last);

                            let c_type = detect_content_type(&text);
                            if let Ok(Some(saved)) = db.add_clip(c_type, Some(&text), None, 0, 0, &hash) {
                                println!("[ClipMaster] 📋 Đã lưu clip mới: {} ký tự (loại: {})", text.len(), c_type);
                                app_handle.emit("clipboard_changed", &saved).ok();
                            }
                        }
                    }
                }
            }
        });
    }
}
