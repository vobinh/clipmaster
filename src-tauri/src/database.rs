use rusqlite::{params, Connection, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ClipItem {
    pub id: i64,
    pub r#type: String,
    pub content: Option<String>,
    pub content_hash: String,
    pub image_path: Option<String>,
    pub image_width: i64,
    pub image_height: i64,
    pub char_count: i64,
    pub line_count: i64,
    pub is_pinned: i64,
    pub created_at: f64,
    pub updated_at: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct NoteItem {
    pub id: i64,
    pub title: Option<String>,
    pub content: String,
    pub content_hash: String,
    pub is_pinned: i64,
    pub color: Option<String>,
    pub created_at: f64,
    pub updated_at: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Stats {
    pub total: i64,
    pub pinned: i64,
}

#[allow(dead_code)]
pub struct Database {
    conn: Mutex<Connection>,
    db_path: PathBuf,
    images_dir: PathBuf,
}

fn current_time() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}

pub fn compute_sha256(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

pub fn get_default_storage_dir() -> PathBuf {
    #[cfg(target_os = "windows")]
    {
        if let Ok(appdata) = std::env::var("APPDATA") {
            return PathBuf::from(appdata).join("clipmaster");
        }
    }

    #[cfg(target_os = "macos")]
    {
        if let Ok(home) = std::env::var("HOME") {
            return PathBuf::from(home)
                .join("Library")
                .join("Application Support")
                .join("clipmaster");
        }
    }

    // Default Linux / Unix (~/.local/share/clipmaster)
    if let Ok(home) = std::env::var("HOME") {
        PathBuf::from(home).join(".local").join("share").join("clipmaster")
    } else {
        PathBuf::from("clipmaster_data")
    }
}

impl Database {
    pub fn new(storage_dir: Option<PathBuf>) -> Result<Self> {
        let dir = storage_dir.unwrap_or_else(get_default_storage_dir);
        let images_dir = dir.join("images");
        fs::create_dir_all(&dir).ok();
        fs::create_dir_all(&images_dir).ok();

        let db_path = dir.join("clipmaster.db");
        let conn = Connection::open(&db_path)?;

        let db = Database {
            conn: Mutex::new(conn),
            db_path,
            images_dir,
        };

        db.init_schema()?;
        Ok(db)
    }

    fn init_schema(&self) -> Result<()> {
        let conn = self.conn.lock().unwrap();

        conn.execute(
            "CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                content TEXT,
                content_hash TEXT UNIQUE NOT NULL,
                image_path TEXT,
                image_width INTEGER DEFAULT 0,
                image_height INTEGER DEFAULT 0,
                char_count INTEGER DEFAULT 0,
                line_count INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )",
            [],
        )?;

        conn.execute("CREATE INDEX IF NOT EXISTS idx_clips_updated ON clips(updated_at DESC)", [])?;
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clips_type ON clips(type)", [])?;
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clips_pinned ON clips(is_pinned)", [])?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                is_pinned INTEGER DEFAULT 0,
                color TEXT DEFAULT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )",
            [],
        )?;

        conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC)", [])?;
        conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(is_pinned)", [])?;

        // Seed default settings
        let defaults = [
            ("max_history", "200"),
            ("save_images", "1"),
            ("auto_paste", "1"),
            ("auto_record", "1"),
            ("theme_mode", "dark"),
            ("language", "vi"),
            ("shortcut", "<Super>v"),
            ("notes_pin_enabled", "0"),
            ("notes_pin_hash", ""),
            ("notes_pin_timeout", "300"),
        ];

        for (k, v) in defaults {
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?1, ?2)",
                params![k, v],
            )?;
        }

        Ok(())
    }

    pub fn get_images_dir(&self) -> PathBuf {
        self.images_dir.clone()
    }

    pub fn add_clip(
        &self,
        clip_type: &str,
        content: Option<&str>,
        image_path: Option<&str>,
        image_width: i64,
        image_height: i64,
        content_hash: &str,
    ) -> Result<Option<ClipItem>> {
        let now = current_time();
        let conn = self.conn.lock().unwrap();

        // Check if item already exists by hash
        let mut stmt = conn.prepare("SELECT id FROM clips WHERE content_hash = ?1")?;
        let existing = stmt.query_row(params![content_hash], |row| row.get::<_, i64>(0)).ok();

        if let Some(id) = existing {
            // Update timestamp to bump to top
            conn.execute(
                "UPDATE clips SET updated_at = ?1 WHERE id = ?2",
                params![now, id],
            )?;
            drop(stmt);
            return self.get_clip_by_id_locked(&conn, id);
        }

        drop(stmt);

        let char_count = content.map(|c| c.chars().count() as i64).unwrap_or(0);
        let line_count = content.map(|c| c.lines().count() as i64).unwrap_or(0);

        conn.execute(
            "INSERT INTO clips (
                type, content, content_hash, image_path,
                image_width, image_height, char_count, line_count,
                is_pinned, created_at, updated_at
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, 0, ?9, ?9)",
            params![
                clip_type,
                content,
                content_hash,
                image_path,
                image_width,
                image_height,
                char_count,
                line_count,
                now
            ],
        )?;

        let clip_id = conn.last_insert_rowid();

        // Prune history
        let max_history: i64 = conn
            .query_row(
                "SELECT value FROM settings WHERE key = 'max_history'",
                [],
                |r| r.get::<_, String>(0),
            )
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(200);

        self.prune_history_locked(&conn, max_history);

        self.get_clip_by_id_locked(&conn, clip_id)
    }

    fn prune_history_locked(&self, conn: &Connection, max_items: i64) {
        let unpinned_cnt: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM clips WHERE is_pinned = 0",
                [],
                |r| r.get(0),
            )
            .unwrap_or(0);

        if unpinned_cnt > max_items {
            let overflow = unpinned_cnt - max_items;
            let stmt = conn
                .prepare(
                    "SELECT id, image_path FROM clips WHERE is_pinned = 0 ORDER BY updated_at ASC LIMIT ?1",
                )
                .ok();

            if let Some(mut stmt) = stmt {
                let to_delete: Vec<(i64, Option<String>)> = stmt
                    .query_map(params![overflow], |row| {
                        Ok((row.get(0)?, row.get(1)?))
                    })
                    .ok()
                    .map(|rows| rows.filter_map(Result::ok).collect())
                    .unwrap_or_default();

                for (id, img_path) in to_delete {
                    if let Some(path) = img_path {
                        fs::remove_file(path).ok();
                    }
                    conn.execute("DELETE FROM clips WHERE id = ?1", params![id]).ok();
                }
            }
        }
    }

    fn get_clip_by_id_locked(&self, conn: &Connection, id: i64) -> Result<Option<ClipItem>> {
        let mut stmt = conn.prepare(
            "SELECT id, type, content, content_hash, image_path, image_width, image_height,
                    char_count, line_count, is_pinned, created_at, updated_at
             FROM clips WHERE id = ?1",
        )?;

        let mut rows = stmt.query(params![id])?;
        if let Some(row) = rows.next()? {
            Ok(Some(ClipItem {
                id: row.get(0)?,
                r#type: row.get(1)?,
                content: row.get(2)?,
                content_hash: row.get(3)?,
                image_path: row.get(4)?,
                image_width: row.get(5)?,
                image_height: row.get(6)?,
                char_count: row.get(7)?,
                line_count: row.get(8)?,
                is_pinned: row.get(9)?,
                created_at: row.get(10)?,
                updated_at: row.get(11)?,
            }))
        } else {
            Ok(None)
        }
    }

    pub fn get_clip_by_id(&self, id: i64) -> Result<Option<ClipItem>> {
        let conn = self.conn.lock().unwrap();
        self.get_clip_by_id_locked(&conn, id)
    }

    pub fn get_clips(
        &self,
        filter_type: &str,
        query: &str,
        limit: i64,
        offset: i64,
    ) -> Result<Vec<ClipItem>> {
        let conn = self.conn.lock().unwrap();

        let mut sql = String::from(
            "SELECT id, type, content, content_hash, image_path, image_width, image_height,
                    char_count, line_count, is_pinned, created_at, updated_at
             FROM clips WHERE 1=1",
        );

        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

        if filter_type == "pinned" {
            sql.push_str(" AND is_pinned = 1");
        } else if matches!(filter_type, "text" | "code" | "url" | "image" | "color") {
            sql.push_str(" AND type = ?");
            params_vec.push(Box::new(filter_type.to_string()));
        }

        let trimmed_query = query.trim();
        if !trimmed_query.is_empty() {
            sql.push_str(" AND (content LIKE ? OR (type = 'image' AND image_path LIKE ?))");
            let pattern = format!("%{}%", trimmed_query);
            params_vec.push(Box::new(pattern.clone()));
            params_vec.push(Box::new(pattern));
        }

        sql.push_str(" ORDER BY is_pinned DESC, updated_at DESC LIMIT ? OFFSET ?");
        params_vec.push(Box::new(limit));
        params_vec.push(Box::new(offset));

        let mut stmt = conn.prepare(&sql)?;
        let param_refs: Vec<&dyn rusqlite::ToSql> = params_vec.iter().map(|p| p.as_ref()).collect();

        let rows = stmt.query_map(param_refs.as_slice(), |row| {
            Ok(ClipItem {
                id: row.get(0)?,
                r#type: row.get(1)?,
                content: row.get(2)?,
                content_hash: row.get(3)?,
                image_path: row.get(4)?,
                image_width: row.get(5)?,
                image_height: row.get(6)?,
                char_count: row.get(7)?,
                line_count: row.get(8)?,
                is_pinned: row.get(9)?,
                created_at: row.get(10)?,
                updated_at: row.get(11)?,
            })
        })?;

        let mut clips = Vec::new();
        for r in rows {
            if let Ok(c) = r {
                clips.push(c);
            }
        }
        Ok(clips)
    }

    pub fn toggle_pin(&self, id: i64) -> Result<bool> {
        let conn = self.conn.lock().unwrap();
        let current_pinned: Option<i64> = conn
            .query_row("SELECT is_pinned FROM clips WHERE id = ?1", params![id], |r| {
                r.get(0)
            })
            .ok();

        if let Some(pinned) = current_pinned {
            let new_pinned = if pinned == 1 { 0 } else { 1 };
            conn.execute(
                "UPDATE clips SET is_pinned = ?1 WHERE id = ?2",
                params![new_pinned, id],
            )?;
            Ok(new_pinned == 1)
        } else {
            Ok(false)
        }
    }

    pub fn delete_clip(&self, id: i64) -> Result<bool> {
        let conn = self.conn.lock().unwrap();
        let img_path: Option<String> = conn
            .query_row("SELECT image_path FROM clips WHERE id = ?1", params![id], |r| {
                r.get(0)
            })
            .ok()
            .flatten();

        if let Some(path) = img_path {
            fs::remove_file(path).ok();
        }

        let affected = conn.execute("DELETE FROM clips WHERE id = ?1", params![id])?;
        Ok(affected > 0)
    }

    pub fn clear_unpinned(&self) -> Result<usize> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT image_path FROM clips WHERE is_pinned = 0")?;
        let img_paths: Vec<Option<String>> = stmt
            .query_map([], |row| row.get(0))?
            .filter_map(Result::ok)
            .collect();

        for img in img_paths.into_iter().flatten() {
            fs::remove_file(img).ok();
        }

        let affected = conn.execute("DELETE FROM clips WHERE is_pinned = 0", [])?;
        Ok(affected)
    }

    pub fn get_stats(&self) -> Result<Stats> {
        let conn = self.conn.lock().unwrap();
        let total: i64 = conn
            .query_row("SELECT COUNT(*) FROM clips", [], |r| r.get(0))
            .unwrap_or(0);
        let pinned: i64 = conn
            .query_row("SELECT COUNT(*) FROM clips WHERE is_pinned = 1", [], |r| {
                r.get(0)
            })
            .unwrap_or(0);

        Ok(Stats { total, pinned })
    }

    // ── Settings ───────────────────────────────────────
    pub fn get_setting(&self, key: &str, default: &str) -> String {
        let conn = self.conn.lock().unwrap();
        conn.query_row(
            "SELECT value FROM settings WHERE key = ?1",
            params![key],
            |r| r.get::<_, String>(0),
        )
        .unwrap_or_else(|_| default.to_string())
    }

    pub fn set_setting(&self, key: &str, value: &str) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?1, ?2)
             ON CONFLICT(key) DO UPDATE SET value = ?2",
            params![key, value],
        )?;
        Ok(())
    }

    pub fn get_all_settings(&self) -> Result<std::collections::HashMap<String, String>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT key, value FROM settings")?;
        let rows = stmt.query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })?;

        let mut map = std::collections::HashMap::new();
        for r in rows.flatten() {
            map.insert(r.0, r.1);
        }
        Ok(map)
    }

    pub fn reset_settings(&self) -> Result<()> {
        {
            let conn = self.conn.lock().unwrap();
            conn.execute("DELETE FROM settings", [])?;
        }
        self.init_schema()?;
        Ok(())
    }

    // ── Notes ──────────────────────────────────────────
    pub fn add_note(
        &self,
        title: Option<&str>,
        content: &str,
        is_pinned: bool,
        color: Option<&str>,
    ) -> Result<Option<i64>> {
        let trimmed_content = content.trim();
        if trimmed_content.is_empty() {
            return Ok(None);
        }

        let now = current_time();
        let hash_input = format!("{}_{}", now, trimmed_content);
        let c_hash = compute_sha256(hash_input.as_bytes());
        let clean_title = title.unwrap_or("").trim();

        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO notes (title, content, content_hash, is_pinned, color, created_at, updated_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?6)",
            params![
                clean_title,
                trimmed_content,
                c_hash,
                if is_pinned { 1 } else { 0 },
                color,
                now
            ],
        )?;

        Ok(Some(conn.last_insert_rowid()))
    }

    pub fn update_note(
        &self,
        id: i64,
        title: Option<&str>,
        content: &str,
        color: Option<&str>,
    ) -> Result<bool> {
        let trimmed_content = content.trim();
        if trimmed_content.is_empty() {
            return Ok(false);
        }

        let now = current_time();
        let clean_title = title.unwrap_or("").trim();

        let conn = self.conn.lock().unwrap();
        let affected = conn.execute(
            "UPDATE notes SET title = ?1, content = ?2, color = COALESCE(?3, color), updated_at = ?4
             WHERE id = ?5",
            params![clean_title, trimmed_content, color, now, id],
        )?;

        Ok(affected > 0)
    }

    pub fn delete_note(&self, id: i64) -> Result<bool> {
        let conn = self.conn.lock().unwrap();
        let affected = conn.execute("DELETE FROM notes WHERE id = ?1", params![id])?;
        Ok(affected > 0)
    }

    pub fn toggle_pin_note(&self, id: i64) -> Result<bool> {
        let conn = self.conn.lock().unwrap();
        let current_pinned: Option<i64> = conn
            .query_row("SELECT is_pinned FROM notes WHERE id = ?1", params![id], |r| {
                r.get(0)
            })
            .ok();

        if let Some(pinned) = current_pinned {
            let new_pinned = if pinned == 1 { 0 } else { 1 };
            let now = current_time();
            conn.execute(
                "UPDATE notes SET is_pinned = ?1, updated_at = ?2 WHERE id = ?3",
                params![new_pinned, now, id],
            )?;
            Ok(new_pinned == 1)
        } else {
            Ok(false)
        }
    }

    pub fn get_notes(&self, query: &str, filter_pinned: bool, limit: i64) -> Result<Vec<NoteItem>> {
        let conn = self.conn.lock().unwrap();

        let mut sql = String::from(
            "SELECT id, title, content, content_hash, is_pinned, color, created_at, updated_at
             FROM notes WHERE 1=1",
        );
        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

        if filter_pinned {
            sql.push_str(" AND is_pinned = 1");
        }

        let trimmed_query = query.trim();
        if !trimmed_query.is_empty() {
            sql.push_str(" AND (title LIKE ? OR content LIKE ?)");
            let q_param = format!("%{}%", trimmed_query);
            params_vec.push(Box::new(q_param.clone()));
            params_vec.push(Box::new(q_param));
        }

        sql.push_str(" ORDER BY is_pinned DESC, updated_at DESC LIMIT ?");
        params_vec.push(Box::new(limit));

        let mut stmt = conn.prepare(&sql)?;
        let param_refs: Vec<&dyn rusqlite::ToSql> = params_vec.iter().map(|p| p.as_ref()).collect();

        let rows = stmt.query_map(param_refs.as_slice(), |row| {
            Ok(NoteItem {
                id: row.get(0)?,
                title: row.get(1)?,
                content: row.get(2)?,
                content_hash: row.get(3)?,
                is_pinned: row.get(4)?,
                color: row.get(5)?,
                created_at: row.get(6)?,
                updated_at: row.get(7)?,
            })
        })?;

        let mut notes = Vec::new();
        for r in rows {
            if let Ok(n) = r {
                notes.push(n);
            }
        }
        Ok(notes)
    }

    pub fn get_note_by_id(&self, id: i64) -> Result<Option<NoteItem>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, title, content, content_hash, is_pinned, color, created_at, updated_at
             FROM notes WHERE id = ?1",
        )?;

        let mut rows = stmt.query(params![id])?;
        if let Some(row) = rows.next()? {
            Ok(Some(NoteItem {
                id: row.get(0)?,
                title: row.get(1)?,
                content: row.get(2)?,
                content_hash: row.get(3)?,
                is_pinned: row.get(4)?,
                color: row.get(5)?,
                created_at: row.get(6)?,
                updated_at: row.get(7)?,
            }))
        } else {
            Ok(None)
        }
    }

    // ── PIN Security ───────────────────────────────────
    pub fn is_notes_pin_enabled(&self) -> bool {
        let enabled = self.get_setting("notes_pin_enabled", "0") == "1";
        let hash = self.get_setting("notes_pin_hash", "");
        enabled && !hash.trim().is_empty()
    }

    pub fn set_notes_pin(&self, pin: &str) -> bool {
        let trimmed = pin.trim();
        if trimmed.len() != 4 || !trimmed.chars().all(|c| c.is_ascii_digit()) {
            return false;
        }

        let hash = compute_sha256(trimmed.as_bytes());
        self.set_setting("notes_pin_hash", &hash).ok();
        self.set_setting("notes_pin_enabled", "1").ok();
        true
    }

    pub fn verify_notes_pin(&self, pin: &str) -> bool {
        let saved_hash = self.get_setting("notes_pin_hash", "");
        if saved_hash.trim().is_empty() {
            return false;
        }

        let input_hash = compute_sha256(pin.trim().as_bytes());
        input_hash == saved_hash.trim()
    }

    pub fn disable_notes_pin(&self) {
        self.set_setting("notes_pin_enabled", "0").ok();
    }
}
