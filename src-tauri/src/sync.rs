use crate::database::{ClipItem, Database, NoteItem};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::time::Duration;

pub const SCHEMA_SQL: &str = r#"
CREATE TABLE IF NOT EXISTS pinned_clips (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    type         TEXT NOT NULL,
    content      TEXT,
    char_count   INTEGER DEFAULT 0,
    line_count   INTEGER DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL,
    deleted_at   TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_pinned_updated
    ON pinned_clips(updated_at DESC)
    WHERE deleted_at IS NULL;

ALTER TABLE pinned_clips ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'pinned_clips' AND policyname = 'allow_anon_all'
    ) THEN
        CREATE POLICY allow_anon_all ON pinned_clips
            FOR ALL
            TO anon, authenticated
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS user_notes (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    title        TEXT,
    content      TEXT NOT NULL,
    is_pinned    INTEGER DEFAULT 0,
    color        TEXT,
    created_at   TIMESTAMPTZ NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL,
    deleted_at   TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_notes_updated
    ON user_notes(updated_at DESC)
    WHERE deleted_at IS NULL;

ALTER TABLE user_notes ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'user_notes' AND policyname = 'allow_anon_all_notes'
    ) THEN
        CREATE POLICY allow_anon_all_notes ON user_notes
            FOR ALL
            TO anon, authenticated
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;
"#;

#[derive(Debug, Serialize, Deserialize)]
pub struct CloudClipRecord {
    pub content_hash: String,
    pub r#type: String,
    pub content: Option<String>,
    pub char_count: i64,
    pub line_count: i64,
    pub created_at: String,
    pub updated_at: String,
    pub deleted_at: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CloudNoteRecord {
    pub content_hash: String,
    pub title: Option<String>,
    pub content: String,
    pub is_pinned: i64,
    pub color: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    pub deleted_at: Option<String>,
}

fn ts_to_iso(ts: f64) -> String {
    let secs = ts.floor() as i64;
    let nsecs = ((ts - ts.floor()) * 1_000_000_000.0) as u32;
    if let Some(dt) = DateTime::from_timestamp(secs, nsecs) {
        dt.to_rfc3339()
    } else {
        Utc::now().to_rfc3339()
    }
}

fn iso_to_ts(iso: &str) -> f64 {
    if let Ok(dt) = DateTime::parse_from_rfc3339(iso) {
        dt.timestamp() as f64 + (dt.timestamp_subsec_nanos() as f64 / 1_000_000_000.0)
    } else {
        chrono::Utc::now().timestamp() as f64
    }
}

pub fn extract_project_ref(url: &str) -> Option<String> {
    let trimmed = url.trim().trim_end_matches('/');
    let host = trimmed.split("//").last()?;
    let ref_part = host.split('.').next()?;
    if !ref_part.is_empty() {
        Some(ref_part.to_string())
    } else {
        None
    }
}

fn make_client() -> reqwest::Client {
    reqwest::Client::builder()
        .timeout(Duration::from_secs(12))
        .build()
        .unwrap_or_else(|_| reqwest::Client::new())
}

pub async fn test_connection(url: &str, key: &str) -> Result<String, String> {
    let base_url = url.trim().trim_end_matches('/');
    let api_key = key.trim();

    if base_url.is_empty() || api_key.is_empty() {
        return Err("Vui lòng nhập đầy đủ Supabase URL và API Key".to_string());
    }

    let client = make_client();

    // 1. Check pinned_clips table
    let clips_url = format!("{}/rest/v1/pinned_clips?select=id&limit=1", base_url);
    let resp = client
        .get(&clips_url)
        .header("apikey", api_key)
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Accept", "application/json")
        .send()
        .await
        .map_err(|e| format!("Không thể kết nối đến máy chủ: {}", e))?;

    let status = resp.status();
    if status.as_u16() == 404 {
        return Err("Chưa tạo bảng trên Supabase! Bảng 'pinned_clips' không tồn tại.".to_string());
    }
    if status.as_u16() == 401 || status.as_u16() == 403 {
        return Err("API Key (anon public key) không hợp lệ hoặc bị từ chối!".to_string());
    }
    if !status.is_success() {
        let err_body = resp.text().await.unwrap_or_default();
        return Err(format!("Lỗi kiểm tra bảng: {} ({})", status, err_body));
    }

    // 2. Check user_notes table
    let notes_url = format!("{}/rest/v1/user_notes?select=id&limit=1", base_url);
    let resp_notes = client
        .get(&notes_url)
        .header("apikey", api_key)
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Accept", "application/json")
        .send()
        .await
        .map_err(|e| format!("Không thể kết nối đến user_notes: {}", e))?;

    if resp_notes.status().as_u16() == 404 {
        return Err("Bảng 'user_notes' chưa được tạo trên Supabase!".to_string());
    }

    // 3. Probe write test
    let probe_hash = "__clipmaster_probe__";
    let now = Utc::now().to_rfc3339();
    let probe_row = serde_json::json!({
        "content_hash": probe_hash,
        "type": "probe",
        "content": "probe",
        "char_count": 0,
        "line_count": 0,
        "created_at": now,
        "updated_at": now,
        "deleted_at": now,
    });

    let probe_url = format!("{}/rest/v1/pinned_clips?on_conflict=content_hash", base_url);
    let probe_resp = client
        .post(&probe_url)
        .header("apikey", api_key)
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .header("Prefer", "resolution=merge-duplicates,return=minimal")
        .json(&probe_row)
        .send()
        .await;

    if let Ok(p_res) = probe_resp {
        if !p_res.status().is_success() {
            let p_body = p_res.text().await.unwrap_or_default();
            if p_body.to_lowercase().contains("policy") || p_body.to_lowercase().contains("row-level security") {
                return Err("Bảng có sẵn nhưng RLS (Row Level Security) đang chặn quyền ghi!".to_string());
            }
        } else {
            // Clean up probe record
            let del_url = format!("{}/rest/v1/pinned_clips?content_hash=eq.{}", base_url, probe_hash);
            let _ = client
                .delete(&del_url)
                .header("apikey", api_key)
                .header("Authorization", format!("Bearer {}", api_key))
                .send()
                .await;
        }
    }

    Ok("Kết nối Supabase BYOS thành công! (Sẵn sàng đồng bộ)".to_string())
}

pub async fn auto_setup_schema(url: &str, pat: &str) -> Result<String, String> {
    let project_ref = extract_project_ref(url)
        .ok_or_else(|| "Không thể nhận diện Project Ref từ Supabase URL".to_string())?;

    let api_url = format!("https://api.supabase.com/v1/projects/{}/database/query", project_ref);
    let client = make_client();

    let resp = client
        .post(&api_url)
        .header("Authorization", format!("Bearer {}", pat.trim()))
        .header("Content-Type", "application/json")
        .json(&serde_json::json!({ "query": SCHEMA_SQL }))
        .send()
        .await
        .map_err(|e| format!("Không thể kết nối đến Supabase Management API: {}", e))?;

    if resp.status().is_success() {
        Ok("Đã tự động khởi tạo bảng 'pinned_clips' và 'user_notes' thành công!".to_string())
    } else {
        let err_text = resp.text().await.unwrap_or_default();
        Err(format!("Không thể tạo bảng qua PAT: {}", err_text))
    }
}

pub async fn sync_now(db: &Database) -> Result<String, String> {
    let enabled = db.get_setting("sync_enabled", "0") == "1";
    let url = db.get_setting("sync_url", "");
    let key = db.get_setting("sync_token", "");
    let direction = db.get_setting("sync_direction", "bidirectional");

    if !enabled {
        return Err("Tính năng đồng bộ đám mây đang bị tắt trong Cài đặt".to_string());
    }

    let base_url = url.trim().trim_end_matches('/');
    let api_key = key.trim();

    if base_url.is_empty() || api_key.is_empty() {
        return Err("Vui lòng cấu hình URL và API Key trước khi đồng bộ".to_string());
    }

    let client = make_client();
    let mut pulled_clips = 0;
    let mut pushed_clips = 0;
    let mut pulled_notes = 0;
    let mut pushed_notes = 0;

    // ── 1. SYNC PINNED CLIPS ────────────────────────────
    // 1a. Pull pinned clips from Cloud
    if direction == "bidirectional" || direction == "pull_only" {
        let pull_url = format!("{}/rest/v1/pinned_clips?select=*&deleted_at=is.null", base_url);
        if let Ok(resp) = client
            .get(&pull_url)
            .header("apikey", api_key)
            .header("Authorization", format!("Bearer {}", api_key))
            .header("Accept", "application/json")
            .send()
            .await
        {
            if resp.status().is_success() {
                if let Ok(cloud_records) = resp.json::<Vec<CloudClipRecord>>().await {
                    for r in cloud_records {
                        let item = ClipItem {
                            id: 0,
                            r#type: r.r#type,
                            content: r.content,
                            content_hash: r.content_hash,
                            image_path: None,
                            image_width: 0,
                            image_height: 0,
                            char_count: r.char_count,
                            line_count: r.line_count,
                            is_pinned: 1,
                            created_at: iso_to_ts(&r.created_at),
                            updated_at: iso_to_ts(&r.updated_at),
                        };
                        if let Ok(inserted) = db.upsert_clip_from_cloud(&item) {
                            if inserted {
                                pulled_clips += 1;
                            }
                        }
                    }
                }
            }
        }
    }

    // 1b. Push local pinned clips to Cloud
    if direction == "bidirectional" || direction == "push_only" {
        if let Ok(local_pinned) = db.get_pinned_for_sync() {
            if !local_pinned.is_empty() {
                let records: Vec<CloudClipRecord> = local_pinned
                    .into_iter()
                    .map(|c| CloudClipRecord {
                        content_hash: c.content_hash,
                        r#type: c.r#type,
                        content: c.content,
                        char_count: c.char_count,
                        line_count: c.line_count,
                        created_at: ts_to_iso(c.created_at),
                        updated_at: ts_to_iso(c.updated_at),
                        deleted_at: None,
                    })
                    .collect();

                let push_url = format!("{}/rest/v1/pinned_clips?on_conflict=content_hash", base_url);
                if let Ok(resp) = client
                    .post(&push_url)
                    .header("apikey", api_key)
                    .header("Authorization", format!("Bearer {}", api_key))
                    .header("Content-Type", "application/json")
                    .header("Prefer", "resolution=merge-duplicates,return=minimal")
                    .json(&records)
                    .send()
                    .await
                {
                    if resp.status().is_success() {
                        pushed_clips = records.len();
                    }
                }
            }
        }
    }

    // ── 2. SYNC USER NOTES ──────────────────────────────
    // 2a. Pull notes from Cloud
    if direction == "bidirectional" || direction == "pull_only" {
        let pull_url = format!("{}/rest/v1/user_notes?select=*&deleted_at=is.null", base_url);
        if let Ok(resp) = client
            .get(&pull_url)
            .header("apikey", api_key)
            .header("Authorization", format!("Bearer {}", api_key))
            .header("Accept", "application/json")
            .send()
            .await
        {
            if resp.status().is_success() {
                if let Ok(cloud_notes) = resp.json::<Vec<CloudNoteRecord>>().await {
                    for r in cloud_notes {
                        let note = NoteItem {
                            id: 0,
                            title: r.title,
                            content: r.content,
                            content_hash: r.content_hash,
                            is_pinned: r.is_pinned,
                            color: r.color,
                            created_at: iso_to_ts(&r.created_at),
                            updated_at: iso_to_ts(&r.updated_at),
                        };
                        if let Ok(changed) = db.upsert_note_from_cloud(&note) {
                            if changed {
                                pulled_notes += 1;
                            }
                        }
                    }
                }
            }
        }
    }

    // 2b. Push local notes to Cloud
    if direction == "bidirectional" || direction == "push_only" {
        if let Ok(local_notes) = db.get_all_notes_for_sync() {
            if !local_notes.is_empty() {
                let records: Vec<CloudNoteRecord> = local_notes
                    .into_iter()
                    .map(|n| CloudNoteRecord {
                        content_hash: n.content_hash,
                        title: n.title,
                        content: n.content,
                        is_pinned: n.is_pinned,
                        color: n.color,
                        created_at: ts_to_iso(n.created_at),
                        updated_at: ts_to_iso(n.updated_at),
                        deleted_at: None,
                    })
                    .collect();

                let push_url = format!("{}/rest/v1/user_notes?on_conflict=content_hash", base_url);
                if let Ok(resp) = client
                    .post(&push_url)
                    .header("apikey", api_key)
                    .header("Authorization", format!("Bearer {}", api_key))
                    .header("Content-Type", "application/json")
                    .header("Prefer", "resolution=merge-duplicates,return=minimal")
                    .json(&records)
                    .send()
                    .await
                {
                    if resp.status().is_success() {
                        pushed_notes = records.len();
                    }
                }
            }
        }
    }

    // Save last sync timestamp
    let now_ts = chrono::Utc::now().timestamp() as f64;
    db.set_setting("last_sync_at", &now_ts.to_string()).ok();

    let mut parts = Vec::new();
    if pulled_clips > 0 {
        parts.push(format!("↓{}", pulled_clips));
    }
    if pushed_clips > 0 {
        parts.push(format!("↑{}", pushed_clips));
    }
    if pulled_notes > 0 {
        parts.push(format!("📝↓{}", pulled_notes));
    }
    if pushed_notes > 0 {
        parts.push(format!("📝↑{}", pushed_notes));
    }

    if parts.is_empty() {
        Ok("Đồng bộ hoàn tất: Dữ liệu đã đồng bộ mới nhất".to_string())
    } else {
        Ok(format!("Đồng bộ thành công ({})", parts.join(", ")))
    }
}
