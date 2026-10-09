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

            cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                is_pinned INTEGER DEFAULT 0,
                color TEXT DEFAULT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(is_pinned)")
            
            # Default settings
            defaults = {
                "max_history": "200",
                "save_images": "1",
                "auto_paste": "1",
                "auto_record": "1",
                "theme_mode": "dark",
                "language": "vi",
                "shortcut": "<Super>v",
                "notes_pin_enabled": "0",
                "notes_pin_hash": "",
                "notes_pin_timeout": "300"
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

    # ─────────────────────────────────────────────
    # Sync helpers (dùng bởi SyncManager — BYOS)
    # ─────────────────────────────────────────────

    def get_pinned_for_sync(self) -> List[Dict[str, Any]]:
        """Trả về tất cả các mục đang được ghim để đẩy lên cloud."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT content_hash, type, content, char_count, line_count, "
                "created_at, updated_at FROM clips WHERE is_pinned = 1"
            )
            return [dict(row) for row in cur.fetchall()]

    def pin_or_add_by_hash(self, remote_item: Dict[str, Any]) -> None:
        """
        Nhận một mục từ cloud và đảm bảo nó tồn tại và được ghim ở local.
        Nếu mục đã có (theo content_hash) → cập nhật is_pinned = 1.
        Nếu chưa có → thêm mới với is_pinned = 1.
        Chỉ áp dụng cho text/code/url/color (không sync image).
        """
        content_hash = remote_item.get("content_hash")
        clip_type = remote_item.get("type", "text")
        content = remote_item.get("content")

        # Bỏ qua image — không sync file nhị phân
        if clip_type == "image" or not content_hash:
            return

        now = time.time()

        # Parse ISO timestamp từ cloud về Unix float
        def _parse_ts(iso_str) -> float:
            if not iso_str:
                return now
            try:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
                return dt.timestamp()
            except Exception:
                return now

        created_at = _parse_ts(remote_item.get("created_at"))
        updated_at = _parse_ts(remote_item.get("updated_at"))

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, is_pinned FROM clips WHERE content_hash = ?",
                (content_hash,)
            )
            existing = cur.fetchone()

            changed = False
            if existing:
                # Chỉ cập nhật is_pinned nếu chưa ghim
                if existing["is_pinned"] == 0:
                    cur.execute(
                        "UPDATE clips SET is_pinned = 1, updated_at = ? WHERE id = ?",
                        (updated_at, existing["id"])
                    )
                    changed = True
            else:
                # Thêm mục mới từ cloud
                char_count = remote_item.get("char_count", len(content) if content else 0)
                line_count = remote_item.get("line_count",
                                             len(content.splitlines()) if content else 0)
                cur.execute(
                    """INSERT OR IGNORE INTO clips
                       (type, content, content_hash, image_path,
                        image_width, image_height, char_count, line_count,
                        is_pinned, created_at, updated_at)
                       VALUES (?, ?, ?, NULL, 0, 0, ?, ?, 1, ?, ?)""",
                    (clip_type, content, content_hash,
                     char_count, line_count, created_at, updated_at)
                )
                changed = True
            conn.commit()
            return changed

    def unpin_by_hash(self, content_hash: str) -> None:
        """
        Bỏ ghim một mục theo content_hash.
        Dùng khi cloud báo mục này đã bị unpin từ máy khác.
        """
        if not content_hash:
            return
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE clips SET is_pinned = 0 WHERE content_hash = ?",
                (content_hash,)
            )
            conn.commit()

    # ── Notes Management (Ghi chú cá nhân) ─────────

    def add_note(
        self,
        title: Optional[str],
        content: str,
        is_pinned: bool = False,
        color: Optional[str] = None,
    ) -> Optional[int]:
        """Tạo mới một ghi chú cá nhân."""
        if not content or not content.strip():
            return None
        now = time.time()
        c_hash = hashlib.sha256(f"{now}_{content}".encode("utf-8")).hexdigest()
        clean_title = title.strip() if title else ""

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO notes (title, content, content_hash, is_pinned, color, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (clean_title, content.strip(), c_hash, 1 if is_pinned else 0, color, now, now),
            )
            note_id = cur.lastrowid
            conn.commit()
            return note_id

    def update_note(
        self,
        note_id: int,
        title: Optional[str],
        content: str,
        color: Optional[str] = None,
    ) -> bool:
        """Cập nhật nội dung/tiêu đề của ghi chú đã có."""
        if not content or not content.strip():
            return False
        now = time.time()
        clean_title = title.strip() if title else ""

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE notes
                   SET title = ?, content = ?, color = COALESCE(?, color), updated_at = ?
                   WHERE id = ?""",
                (clean_title, content.strip(), color, now, note_id),
            )
            updated = cur.rowcount > 0
            conn.commit()
            return updated

    def delete_note(self, note_id: int) -> bool:
        """Xóa vĩnh viễn ghi chú theo ID."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted

    def toggle_pin_note(self, note_id: int) -> bool:
        """Bật/tắt ghim cho ghi chú."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT is_pinned FROM notes WHERE id = ?", (note_id,))
            row = cur.fetchone()
            if not row:
                return False
            new_pinned = 0 if row["is_pinned"] else 1
            cur.execute("UPDATE notes SET is_pinned = ?, updated_at = ? WHERE id = ?", (new_pinned, time.time(), note_id))
            conn.commit()
            return bool(new_pinned)

    def get_notes(
        self,
        query: str = "",
        filter_pinned: bool = False,
        limit: int = 200,
    ) -> list[dict]:
        """Lấy danh sách ghi chú với tìm kiếm và sắp xếp."""
        sql = "SELECT * FROM notes WHERE 1=1"
        params = []

        if filter_pinned:
            sql += " AND is_pinned = 1"

        if query and query.strip():
            sql += " AND (title LIKE ? OR content LIKE ?)"
            q_like = f"%{query.strip()}%"
            params.extend([q_like, q_like])

        sql += " ORDER BY is_pinned DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def get_note_by_id(self, note_id: int) -> Optional[dict]:
        """Lấy chi tiết 1 ghi chú theo ID."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_all_notes_for_sync(self) -> list[dict]:
        """Lấy tất cả ghi chú phục vụ đồng bộ đám mây."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM notes")
            return [dict(r) for r in cur.fetchall()]

    def upsert_note_from_cloud(self, remote_note: dict) -> bool:
        """
        Đồng bộ 1 ghi chú từ Cloud về SQLite.
        - Nếu chưa có content_hash: thêm mới.
        - Nếu đã có: cập nhật nếu cloud có updated_at mới hơn.
        """
        content_hash = remote_note.get("content_hash")
        content = remote_note.get("content")
        if not content_hash or not content:
            return False

        now = time.time()
        def _parse_ts(iso_str) -> float:
            if not iso_str:
                return now
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
                return dt.timestamp()
            except Exception:
                return now

        created_at = _parse_ts(remote_note.get("created_at"))
        updated_at = _parse_ts(remote_note.get("updated_at"))
        title = remote_note.get("title") or ""
        is_pinned = 1 if remote_note.get("is_pinned") else 0
        color = remote_note.get("color")

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, updated_at FROM notes WHERE content_hash = ?", (content_hash,))
            existing = cur.fetchone()

            changed = False
            if existing:
                if updated_at > existing["updated_at"]:
                    cur.execute(
                        """UPDATE notes
                           SET title = ?, content = ?, is_pinned = ?, color = ?, updated_at = ?
                           WHERE id = ?""",
                        (title, content, is_pinned, color, updated_at, existing["id"]),
                    )
                    changed = True
            else:
                cur.execute(
                    """INSERT INTO notes (title, content, content_hash, is_pinned, color, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (title, content, content_hash, is_pinned, color, created_at, updated_at),
                )
                changed = True
            conn.commit()
            return changed

    def delete_note_by_hash(self, content_hash: str) -> bool:
        """Xóa ghi chú theo content_hash (khi máy khác xóa trên cloud)."""
        if not content_hash:
            return False
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM notes WHERE content_hash = ?", (content_hash,))
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted

    # ── Notes Security (Mã PIN bảo vệ Ghi chú) ─────

    def is_notes_pin_enabled(self) -> bool:
        """Kiểm tra tính năng bảo vệ bằng mã PIN có đang bật không."""
        enabled = self.get_setting("notes_pin_enabled", "0") == "1"
        pin_hash = self.get_setting("notes_pin_hash", "").strip()
        return enabled and bool(pin_hash)

    def set_notes_pin(self, pin: str) -> bool:
        """Thiết lập mã PIN 4 chữ số mới."""
        if not pin or len(pin.strip()) != 4 or not pin.strip().isdigit():
            return False
        h = hashlib.sha256(pin.strip().encode("utf-8")).hexdigest()
        self.set_setting("notes_pin_hash", h)
        self.set_setting("notes_pin_enabled", "1")
        return True

    def verify_notes_pin(self, pin: str) -> bool:
        """Kiểm tra mã PIN nhập vào có khớp không."""
        if not pin:
            return False
        saved_hash = self.get_setting("notes_pin_hash", "").strip()
        if not saved_hash:
            return False
        h = hashlib.sha256(pin.strip().encode("utf-8")).hexdigest()
        return h == saved_hash

    def disable_notes_pin(self) -> None:
        """Tắt bảo vệ bằng mã PIN."""
        self.set_setting("notes_pin_enabled", "0")


