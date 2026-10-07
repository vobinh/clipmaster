"""
ClipMaster Database Manager
SQLite storage for clipboard history and preferences.
"""

import os
import sqlite3
import hashlib
import time
from typing import List, Dict, Any, Optional

DB_DIR = os.path.expanduser("~/.local/share/clipmaster")
DB_PATH = os.path.join(DB_DIR, "clipmaster.db")
IMAGES_DIR = os.path.join(DB_DIR, "images")


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS clips (
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
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_clips_updated ON clips(updated_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_clips_type ON clips(type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_clips_pinned ON clips(is_pinned)")

            cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """)
            
            # Default settings
            defaults = {
                "max_history": "200",
                "save_images": "1",
                "auto_paste": "1",
                "auto_record": "1",
                "theme_mode": "dark",
                "language": "vi",
                "shortcut": "<Super>v"
            }
            for k, v in defaults.items():
                cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
            conn.commit()

    @staticmethod
    def compute_hash(content: Optional[str] = None, image_bytes: Optional[bytes] = None) -> str:
        h = hashlib.sha256()
        if content:
            h.update(content.encode("utf-8", errors="ignore"))
        elif image_bytes:
            h.update(image_bytes)
        return h.hexdigest()

    def add_clip(
        self,
        clip_type: str,
        content: Optional[str] = None,
        image_path: Optional[str] = None,
        image_width: int = 0,
        image_height: int = 0,
        image_bytes: Optional[bytes] = None,
    ) -> Optional[Dict[str, Any]]:
        """Add or update an item in clipboard history."""
        now = time.time()
        c_hash = self.compute_hash(content=content, image_bytes=image_bytes)
        char_count = len(content) if content else 0
        line_count = len(content.splitlines()) if content else 0

        with self._get_connection() as conn:
            cur = conn.cursor()
            # Check existing
            cur.execute("SELECT id, is_pinned, image_path FROM clips WHERE content_hash = ?", (c_hash,))
            existing = cur.fetchone()
            
            if existing:
                clip_id = existing["id"]
                # Update timestamp to bring to top
                cur.execute(
                    "UPDATE clips SET updated_at = ? WHERE id = ?",
                    (now, clip_id)
                )
                conn.commit()
                return self.get_clip_by_id(clip_id)

            # Insert new
            cur.execute("""
                INSERT INTO clips (
                    type, content, content_hash, image_path,
                    image_width, image_height, char_count, line_count,
                    is_pinned, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """, (
                clip_type, content, c_hash, image_path,
                image_width, image_height, char_count, line_count,
                now, now
            ))
            clip_id = cur.lastrowid

            # Auto cleanup exceeding limit
            max_history = int(self.get_setting("max_history", "200"))
            self._prune_history(conn, max_history)

            conn.commit()
            return self.get_clip_by_id(clip_id)

    def _prune_history(self, conn: sqlite3.Connection, max_items: int):
        """Keep only up to max_items unpinned clips, deleting old files."""
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM clips WHERE is_pinned = 0")
        unpinned_count = cur.fetchone()["cnt"]
        if unpinned_count > max_items:
            overflow = unpinned_count - max_items
            cur.execute("""
                SELECT id, image_path FROM clips
                WHERE is_pinned = 0
                ORDER BY updated_at ASC
                LIMIT ?
            """, (overflow,))
            to_delete = cur.fetchall()
            ids_to_del = [row["id"] for row in to_delete]
            for row in to_delete:
                img = row["image_path"]
                if img and os.path.exists(img):
                    try:
                        os.remove(img)
                    except OSError:
                        pass
            if ids_to_del:
                placeholders = ",".join("?" for _ in ids_to_del)
                cur.execute(f"DELETE FROM clips WHERE id IN ({placeholders})", ids_to_del)

    def get_clip_by_id(self, clip_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_clips(
        self,
        filter_type: str = "all",
        query: str = "",
        limit: int = 150,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch clips based on tab filter and search query."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            conditions = []
            params = []

            # Filter type
            if filter_type == "pinned":
                conditions.append("is_pinned = 1")
            elif filter_type in ("text", "code", "url", "image", "color"):
                conditions.append("type = ?")
                params.append(filter_type)

            # Search query
            if query and query.strip():
                conditions.append("content LIKE ?")
                params.append(f"%{query.strip()}%")

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            sql = f"""
                SELECT * FROM clips
                {where_clause}
                ORDER BY is_pinned DESC, updated_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def toggle_pin(self, clip_id: int) -> bool:
        """Toggle pinned status of a clip. Returns new is_pinned value."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT is_pinned FROM clips WHERE id = ?", (clip_id,))
            row = cur.fetchone()
            if not row:
                return False
            new_val = 0 if row["is_pinned"] == 1 else 1
            cur.execute("UPDATE clips SET is_pinned = ? WHERE id = ?", (new_val, clip_id))
            conn.commit()
            return bool(new_val)

    def delete_clip(self, clip_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT image_path FROM clips WHERE id = ?", (clip_id,))
            row = cur.fetchone()
            if row and row["image_path"] and os.path.exists(row["image_path"]):
                try:
                    os.remove(row["image_path"])
                except OSError:
                    pass
            cur.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
            conn.commit()
            return cur.rowcount > 0

    def clear_unpinned(self) -> int:
        """Clear all clips that are not pinned."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT image_path FROM clips WHERE is_pinned = 0")
            rows = cur.fetchall()
            for r in rows:
                if r["image_path"] and os.path.exists(r["image_path"]):
                    try:
                        os.remove(r["image_path"])
                    except OSError:
                        pass
            cur.execute("DELETE FROM clips WHERE is_pinned = 0")
            conn.commit()
            return cur.rowcount

    def get_stats(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as total FROM clips")
            total = cur.fetchone()["total"]
            cur.execute("SELECT COUNT(*) as pinned FROM clips WHERE is_pinned = 1")
            pinned = cur.fetchone()["pinned"]
            return {"total": total, "pinned": pinned}

    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?",
                (key, value, value)
            )
            conn.commit()
