"""
ClipMaster Sync Manager — BYOS (Bring Your Own Supabase)

Cho phép người dùng tự cấu hình Supabase project riêng để đồng bộ
các mục đã ghim (pinned clips) giữa các máy.

Luồng hoạt động:
  1. User nhập Project URL + Anon Key → lưu vào sync_config.json (chmod 600)
  2. Lần đầu: nhập PAT → app tự động tạo bảng qua Management API → PAT không lưu
  3. Mỗi khi app khởi động: kéo thay đổi từ cloud về local, đẩy local lên cloud
  4. Mỗi khi user ghim/bỏ ghim: tự động push lên cloud ngay lập tức
"""

import os
import json
import threading
from datetime import datetime, timezone
from typing import Optional

CONFIG_PATH = os.path.expanduser("~/.local/share/clipmaster/sync_config.json")

# SQL schema tạo bảng — chạy 1 lần duy nhất qua Management API
SCHEMA_SQL = """
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
"""


def _now_iso() -> str:
    """Trả về thời gian hiện tại theo ISO 8601 UTC."""
    return datetime.now(timezone.utc).isoformat()


def _ts_to_iso(timestamp: float) -> str:
    """Chuyển Unix timestamp (float) sang ISO 8601 UTC."""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def extract_project_ref(url: str) -> Optional[str]:
    """
    Trích xuất project ref từ Supabase URL.
    Ví dụ: 'https://abcxyz123.supabase.co' → 'abcxyz123'
    """
    try:
        host = url.strip().rstrip("/").split("//")[-1]
        ref = host.split(".")[0]
        return ref if ref else None
    except Exception:
        return None


# ─────────────────────────────────────────────────
# SyncConfig: quản lý lưu trữ credentials
# ─────────────────────────────────────────────────

class SyncConfig:
    """Lưu và tải Supabase URL + Anon Key từ file local."""

    def save(self, url: str, key: str) -> None:
        """Lưu config với quyền 600 (chỉ owner đọc được)."""
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        data = {
            "supabase_url": url.strip().rstrip("/"),
            "supabase_key": key.strip(),
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.chmod(CONFIG_PATH, 0o600)

    def load(self) -> Optional[tuple[str, str]]:
        """Tải config. Trả về (url, key) hoặc None nếu chưa cấu hình."""
        if not os.path.exists(CONFIG_PATH):
            return None
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
            url = data.get("supabase_url", "").strip()
            key = data.get("supabase_key", "").strip()
            if url and key:
                return url, key
        except Exception:
            pass
        return None

    def clear(self) -> None:
        """Xóa config (ngắt kết nối)."""
        try:
            if os.path.exists(CONFIG_PATH):
                os.remove(CONFIG_PATH)
        except OSError:
            pass


# ─────────────────────────────────────────────────
# SyncManager: logic đồng bộ chính
# ─────────────────────────────────────────────────

class SyncManager:
    """
    Quản lý toàn bộ việc đồng bộ pinned clips với Supabase BYOS.
    Thread-safe: các thao tác mạng đều chạy trong daemon thread.
    """

    def __init__(self, db):
        """
        Args:
            db: instance của Database (src.database.Database)
        """
        self.db = db
        self.config = SyncConfig()
        self._client = None
        self._client_lock = threading.Lock()

    # ── Trạng thái ──────────────────────────────

    def is_configured(self) -> bool:
        """Trả về True nếu đã cấu hình Supabase credentials."""
        return self.config.load() is not None

    def get_configured_url(self) -> Optional[str]:
        """Trả về URL đã lưu hoặc None."""
        creds = self.config.load()
        return creds[0] if creds else None

    # ── Supabase client ──────────────────────────

    def _get_client(self):
        """Lấy Supabase client, khởi tạo nếu chưa có. Thread-safe."""
        with self._client_lock:
            if self._client:
                return self._client
            creds = self.config.load()
            if not creds:
                return None
            try:
                from supabase import create_client
                url, key = creds
                self._client = create_client(url, key)
                return self._client
            except ImportError:
                print("[Sync] Thiếu thư viện supabase: pip install supabase")
                return None
            except Exception as e:
                print(f"[Sync] Lỗi khởi tạo client: {e}")
                return None

    def _reset_client(self) -> None:
        """Đặt lại client (dùng sau khi thay đổi config)."""
        with self._client_lock:
            self._client = None

    # ── Setup: tự động tạo schema qua Management API ──

    def auto_setup_schema(self, url: str, pat: str) -> tuple[bool, str]:
        """
        Gọi Supabase Management API để tự động tạo bảng pinned_clips.
        PAT (Personal Access Token) chỉ dùng ở đây và KHÔNG được lưu lại.

        Args:
            url: Supabase project URL
            pat: Personal Access Token (tạo tại supabase.com → Account → Tokens)

        Returns:
            (success: bool, message: str)
        """
        import requests as _requests

        project_ref = extract_project_ref(url)
        if not project_ref:
            return False, "URL không hợp lệ. Ví dụ: https://xxxx.supabase.co"

        try:
            resp = _requests.post(
                f"https://api.supabase.com/v1/projects/{project_ref}/database/query",
                headers={
                    "Authorization": f"Bearer {pat.strip()}",
                    "Content-Type": "application/json",
                },
                json={"query": SCHEMA_SQL},
                timeout=20,
            )

            if resp.status_code == 200:
                return True, "Đã tạo bảng thành công"
            elif resp.status_code == 401:
                return False, "PAT không hợp lệ hoặc đã hết hạn"
            elif resp.status_code == 403:
                return False, "PAT không có quyền truy cập project này"
            elif resp.status_code == 404:
                return False, "Không tìm thấy project. Kiểm tra lại URL"
            else:
                try:
                    detail = resp.json().get("message", resp.text[:200])
                except Exception:
                    detail = resp.text[:200]
                return False, f"Lỗi server ({resp.status_code}): {detail}"

        except _requests.Timeout:
            return False, "Kết nối timeout. Thử lại sau"
        except _requests.ConnectionError:
            return False, "Không có kết nối internet"
        except Exception as e:
            return False, f"Lỗi: {e}"

    def test_connection(self, url: str, key: str) -> tuple[bool, str]:
        """
        Kiểm tra URL + anon key có hợp lệ không.

        Returns:
            (True, "OK") nếu kết nối thành công và bảng tồn tại
            (False, "TABLE_NOT_FOUND") nếu kết nối OK nhưng bảng chưa tạo
            (False, <lỗi>) nếu kết nối thất bại
        """
        try:
            from supabase import create_client
            client = create_client(url.strip(), key.strip())
            client.table("pinned_clips").select("id").limit(1).execute()
            return True, "OK"
        except ImportError:
            return False, "Thiếu thư viện supabase: pip install supabase"
        except Exception as e:
            err = str(e).lower()
            if "relation" in err and "does not exist" in err:
                return False, "TABLE_NOT_FOUND"
            if "invalid api key" in err or "invalid jwt" in err:
                return False, "API Key không hợp lệ"
            if "connection" in err or "network" in err or "resolve" in err:
                return False, "Không kết nối được. Kiểm tra URL và internet"
            return False, f"Lỗi: {str(e)[:120]}"

    # ── Thao tác Push (Local → Cloud) ──────────

    def push_pin(self, clip: dict) -> bool:
        """
        Đẩy 1 mục vừa được ghim lên cloud.
        Chạy trong calling thread (thường là GLib main thread).
        Dùng thread riêng để không block UI.
        """
        client = self._get_client()
        if not client:
            return False

        def _push():
            try:
                now = _now_iso()
                client.table("pinned_clips").upsert(
                    {
                        "content_hash": clip["content_hash"],
                        "type": clip["type"],
                        "content": clip.get("content"),
                        "char_count": clip.get("char_count", 0),
                        "line_count": clip.get("line_count", 0),
                        "created_at": _ts_to_iso(clip.get("created_at", 0)),
                        "updated_at": now,
                        "deleted_at": None,
                    },
                    on_conflict="content_hash",
                ).execute()
            except Exception as e:
                print(f"[Sync] push_pin error: {e}")

        threading.Thread(target=_push, daemon=True).start()
        return True

    def push_unpin(self, content_hash: str) -> bool:
        """
        Đánh dấu soft-delete khi user bỏ ghim một mục.
        Các máy khác sẽ nhận thay đổi này qua pull_changes_since().
        """
        client = self._get_client()
        if not client:
            return False

        def _unpin():
            try:
                now = _now_iso()
                client.table("pinned_clips").update(
                    {"deleted_at": now, "updated_at": now}
                ).eq("content_hash", content_hash).execute()
            except Exception as e:
                print(f"[Sync] push_unpin error: {e}")

        threading.Thread(target=_unpin, daemon=True).start()
        return True

    # ── Thao tác Pull (Cloud → Local) ──────────

    def pull_all(self) -> list[dict]:
        """
        Kéo toàn bộ pinned items đang active từ cloud về.
        Dùng cho initial sync lần đầu kết nối.
        """
        client = self._get_client()
        if not client:
            return []
        try:
            result = (
                client.table("pinned_clips")
                .select("*")
                .is_("deleted_at", "null")
                .order("updated_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[Sync] pull_all error: {e}")
            return []

    def pull_changes_since(self, iso_timestamp: str) -> list[dict]:
        """
        Kéo chỉ những thay đổi sau lần sync cuối.
        Bao gồm cả các mục bị soft-delete (để sync bỏ ghim).
        """
        client = self._get_client()
        if not client:
            return []
        try:
            result = (
                client.table("pinned_clips")
                .select("*")
                .gt("updated_at", iso_timestamp)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[Sync] pull_changes_since error: {e}")
            return []

    # ── Sync tổng hợp ───────────────────────────

    def sync_on_startup(self, on_done: Optional[callable] = None) -> None:
        """
        Chạy đồng bộ đầy đủ khi app khởi động.
        Nên gọi trong daemon thread để không block UI.

        1. Pull thay đổi từ cloud về local
        2. Push local pinned lên cloud (merge)
        3. Cập nhật last_sync_at
        """
        if not self.is_configured():
            return

        try:
            last_sync = self.db.get_setting(
                "last_sync_at", "1970-01-01T00:00:00+00:00"
            )

            # 1. Pull changes từ cloud
            changes = self.pull_changes_since(last_sync)
            pulled = 0
            for item in changes:
                if item.get("deleted_at"):
                    # Bỏ ghim local nếu cloud đã unpin
                    self.db.unpin_by_hash(item["content_hash"])
                else:
                    # Thêm hoặc ghim mục từ cloud vào local
                    self.db.pin_or_add_by_hash(item)
                    pulled += 1

            # 2. Push local pinned lên cloud (để máy khác nhận)
            local_pinned = self.db.get_pinned_for_sync()
            pushed = 0
            client = self._get_client()
            if client and local_pinned:
                now = _now_iso()
                records = [
                    {
                        "content_hash": clip["content_hash"],
                        "type": clip["type"],
                        "content": clip.get("content"),
                        "char_count": clip.get("char_count", 0),
                        "line_count": clip.get("line_count", 0),
                        "created_at": _ts_to_iso(clip.get("created_at", 0)),
                        "updated_at": _ts_to_iso(clip.get("updated_at", 0)),
                        "deleted_at": None,
                    }
                    for clip in local_pinned
                ]
                try:
                    client.table("pinned_clips").upsert(
                        records, on_conflict="content_hash"
                    ).execute()
                    pushed = len(records)
                except Exception as e:
                    print(f"[Sync] batch push error: {e}")

            # 3. Cập nhật thời gian sync cuối
            self.db.set_setting("last_sync_at", _now_iso())

            if pulled > 0 or pushed > 0:
                print(f"[Sync] Startup sync: ↓{pulled} pulled, ↑{pushed} pushed")

        except Exception as e:
            print(f"[Sync] sync_on_startup error: {e}")
        finally:
            if on_done:
                try:
                    on_done()
                except Exception:
                    pass

    def run_startup_sync_async(self, on_done: Optional[callable] = None) -> None:
        """Chạy sync_on_startup trong daemon thread."""
        threading.Thread(
            target=self.sync_on_startup,
            kwargs={"on_done": on_done},
            daemon=True,
        ).start()
