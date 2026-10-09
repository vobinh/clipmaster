"""
ClipMaster Sync Manager — BYOS (Bring Your Own Supabase)

Cho phép người dùng tự cấu hình Supabase project riêng để đồng bộ
các mục đã ghim (pinned clips) giữa các máy.

Sử dụng trực tiếp REST API (PostgREST & Supabase Management API)
qua Python standard library (urllib.request), HOÀN TOÀN KHÔNG CẦN
cài đặt thêm pip package (không cần `supabase` hay `requests`).

Luồng hoạt động:
  1. User nhập Project URL + Anon Key → lưu vào sync_config.json (chmod 600)
  2. Lần đầu: nhập PAT → app tự động tạo bảng qua Management API → PAT không lưu
  3. Mỗi khi app khởi động: kéo thay đổi từ cloud về local, đẩy local lên cloud
  4. Mỗi khi user ghim/bỏ ghim: tự động push lên cloud ngay lập tức
"""

import os
import json
import threading
import urllib.request
import urllib.error
import urllib.parse
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
# SyncManager: logic đồng bộ chính qua PostgREST
# ─────────────────────────────────────────────────

class SyncManager:
    """
    Quản lý toàn bộ việc đồng bộ pinned clips với Supabase BYOS qua PostgREST.
    Dùng thư viện chuẩn urllib.request — không cần cài đặt pip package.
    Thread-safe: các thao tác mạng đều chạy trong daemon thread.
    """

    def __init__(self, db):
        """
        Args:
            db: instance của Database (src.database.Database)
        """
        self.db = db
        self.config = SyncConfig()
        self._lock = threading.Lock()

    # ── Trạng thái ──────────────────────────────

    def is_configured(self) -> bool:
        """Trả về True nếu đã cấu hình Supabase credentials."""
        return self.config.load() is not None

    def get_configured_url(self) -> Optional[str]:
        """Trả về URL đã lưu hoặc None."""
        creds = self.config.load()
        return creds[0] if creds else None

    def _reset_client(self) -> None:
        """Giữ tương thích API (không cần client object với urllib)."""
        pass

    # ── REST Helper ─────────────────────────────

    def _rest_request(
        self,
        method: str,
        path: str,
        data: Optional[dict | list] = None,
        extra_headers: Optional[dict] = None,
        creds: Optional[tuple[str, str]] = None,
        timeout: float = 15.0,
    ):
        """Thực hiện HTTP request tới Supabase PostgREST endpoint."""
        if not creds:
            creds = self.config.load()
        if not creds:
            raise ValueError("Chưa cấu hình Supabase credentials")

        base_url, api_key = creds
        url = f"{base_url.rstrip('/')}/rest/v1{path}"

        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ClipMaster/1.0",
        }
        if extra_headers:
            headers.update(extra_headers)

        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_data = response.read().decode("utf-8")
            if res_data:
                return json.loads(res_data)
            return None

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
        project_ref = extract_project_ref(url)
        if not project_ref:
            return False, "URL không hợp lệ. Ví dụ: https://xxxx.supabase.co"

        api_url = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
        headers = {
            "Authorization": f"Bearer {pat.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "ClipMaster/1.0",
        }
        body = json.dumps({"query": SCHEMA_SQL}).encode("utf-8")
        req = urllib.request.Request(api_url, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                if response.status in (200, 201):
                    return True, "Đã tạo bảng thành công"
                return True, "Đã khởi tạo database"

        except urllib.error.HTTPError as e:
            status_code = e.code
            try:
                err_body = e.read().decode("utf-8", errors="ignore")
                detail = json.loads(err_body).get("message", err_body[:200])
            except Exception:
                detail = str(e)

            if status_code == 401:
                return False, "PAT không hợp lệ hoặc đã hết hạn"
            elif status_code == 403:
                return False, "PAT không có quyền truy cập project này"
            elif status_code == 404:
                return False, "Không tìm thấy project. Kiểm tra lại URL"
            else:
                return False, f"Lỗi server ({status_code}): {detail}"

        except urllib.error.URLError as e:
            return False, f"Không kết nối được: {e.reason}"
        except Exception as e:
            return False, f"Lỗi: {e}"

    def test_connection(self, url: str, key: str) -> tuple[bool, str]:
        """
        Kiểm tra URL + anon key có hợp lệ không qua PostgREST.

        Returns:
            (True, "OK") nếu kết nối thành công và bảng tồn tại
            (False, "TABLE_NOT_FOUND") nếu kết nối OK nhưng bảng chưa tạo
            (False, <lỗi>) nếu kết nối thất bại
        """
        try:
            self._rest_request(
                method="GET",
                path="/pinned_clips?select=id&limit=1",
                creds=(url.strip(), key.strip()),
                timeout=10.0,
            )
            return True, "OK"
        except urllib.error.HTTPError as e:
            status = e.code
            try:
                err_text = e.read().decode("utf-8", errors="ignore").lower()
            except Exception:
                err_text = ""

            if status == 404 or ("relation" in err_text and "does not exist" in err_text):
                return False, "TABLE_NOT_FOUND"
            if status in (401, 403) or "jwt" in err_text or "invalid api key" in err_text:
                return False, "API Key không hợp lệ"
            if "relation" in err_text and "not exist" in err_text:
                return False, "TABLE_NOT_FOUND"

            return False, f"Lỗi HTTP {status}: {err_text[:100]}"
        except urllib.error.URLError as e:
            return False, "Không kết nối được. Kiểm tra URL và internet"
        except Exception as e:
            err = str(e).lower()
            if "relation" in err and "does not exist" in err:
                return False, "TABLE_NOT_FOUND"
            return False, f"Lỗi: {str(e)[:120]}"

    # ── Thao tác Push (Local → Cloud) ──────────

    def push_pin(self, clip: dict) -> bool:
        """
        Đẩy 1 mục vừa được ghim lên cloud.
        Dùng thread riêng để không block UI.
        """
        if not self.is_configured():
            return False

        def _push():
            try:
                now = _now_iso()
                record = {
                    "content_hash": clip["content_hash"],
                    "type": clip["type"],
                    "content": clip.get("content"),
                    "char_count": clip.get("char_count", 0),
                    "line_count": clip.get("line_count", 0),
                    "created_at": _ts_to_iso(clip.get("created_at", 0)),
                    "updated_at": now,
                    "deleted_at": None,
                }
                self._rest_request(
                    method="POST",
                    path="/pinned_clips?on_conflict=content_hash",
                    data=record,
                    extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                )
            except Exception as e:
                print(f"[Sync] push_pin error: {e}")

        threading.Thread(target=_push, daemon=True).start()
        return True

    def push_unpin(self, content_hash: str) -> bool:
        """
        Đánh dấu soft-delete khi user bỏ ghim một mục.
        Các máy khác sẽ nhận thay đổi này qua pull_changes_since().
        """
        if not self.is_configured():
            return False

        def _unpin():
            try:
                now = _now_iso()
                quoted_hash = urllib.parse.quote(content_hash)
                self._rest_request(
                    method="PATCH",
                    path=f"/pinned_clips?content_hash=eq.{quoted_hash}",
                    data={"deleted_at": now, "updated_at": now},
                    extra_headers={"Prefer": "return=minimal"},
                )
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
        if not self.is_configured():
            return []
        try:
            data = self._rest_request(
                method="GET",
                path="/pinned_clips?select=*&deleted_at=is.null&order=updated_at.desc",
            )
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[Sync] pull_all error: {e}")
            return []

    def pull_changes_since(self, iso_timestamp: str) -> list[dict]:
        """
        Kéo chỉ những thay đổi sau lần sync cuối.
        Bao gồm cả các mục bị soft-delete (để sync bỏ ghim).
        """
        if not self.is_configured():
            return []
        try:
            quoted_ts = urllib.parse.quote(iso_timestamp)
            data = self._rest_request(
                method="GET",
                path=f"/pinned_clips?select=*&updated_at=gt.{quoted_ts}",
            )
            return data if isinstance(data, list) else []
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
            if local_pinned:
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
                    self._rest_request(
                        method="POST",
                        path="/pinned_clips?on_conflict=content_hash",
                        data=records,
                        extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                    )
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
