"""
ClipMaster Sync Manager — BYOS (Bring Your Own Supabase)

Cho phép người dùng tự cấu hình Supabase project riêng để đồng bộ
các mục đã ghim (pinned clips) giữa các máy.

Sử dụng trực tiếp REST API (PostgREST & Supabase Management API)
qua Python standard library (urllib.request), HOÀN TOÀN KHÔNG CẦN
cài đặt thêm pip package (không cần `supabase` hay `requests`).

Luồng hoạt động:
  1. User nhập Project URL + Anon Key → lưu vào sync_config.json (chmod 600)
  2. Lần đầu: nhập PAT → app tự động tạo bảng + RLS policy qua Management API
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

# SQL schema tạo bảng & cấu hình Row Level Security (RLS)
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

-- Kích hoạt RLS và tạo policy cho phép đọc/ghi với anon key
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

-- Bảng lưu trữ Ghi chú cá nhân (user_notes)
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
        self._is_syncing = False
        self._last_ondemand_ts = 0.0

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
        """Thực hiện HTTP request tới Supabase PostgREST endpoint với giải mã lỗi chi tiết."""
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

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res_data = response.read().decode("utf-8")
                if res_data:
                    return json.loads(res_data)
                return None
        except urllib.error.HTTPError as e:
            try:
                err_text = e.read().decode("utf-8", errors="ignore")
                err_json = json.loads(err_text)
                msg = err_json.get("message") or err_json.get("error") or err_text
                code = str(err_json.get("code", ""))
            except Exception:
                msg = str(e)
                code = ""

            if code == "42501" or "row-level security" in msg.lower():
                raise RuntimeError(
                    "RLS_BLOCKED: Bảng pinned_clips bị chặn bởi Row-Level Security (RLS). "
                    "Cần thêm policy cho phép anon key đọc/ghi."
                )
            raise RuntimeError(f"HTTP {e.code}: {msg}")

    # ── Setup: tự động tạo schema qua Management API ──

    def auto_setup_schema(self, url: str, pat: str) -> tuple[bool, str]:
        """
        Gọi Supabase Management API để tự động tạo bảng pinned_clips và RLS policy.
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
                    return True, "Đã tạo bảng và cấu hình RLS thành công"
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
        Kiểm tra URL + anon key:
        1. Kiểm tra tồn tại bảng (GET)
        2. Kiểm tra quyền ghi / RLS (POST probe row và dọn dẹp)

        Returns:
            (True, "OK") nếu kết nối thành công và ghi được
            (False, "TABLE_NOT_FOUND") nếu bảng chưa tạo
            (False, "RLS_BLOCKED") nếu bảng có nhưng RLS chặn ghi
            (False, <lỗi>) nếu kết nối thất bại
        """
        creds = (url.strip(), key.strip())

        # 1. Kiểm tra tồn tại bảng
        try:
            self._rest_request(
                method="GET",
                path="/pinned_clips?select=id&limit=1",
                creds=creds,
                timeout=10.0,
            )
        except RuntimeError as e:
            err = str(e).lower()
            if "rls_blocked" in err:
                return False, "RLS_BLOCKED"
            if "relation" in err and "does not exist" in err:
                return False, "TABLE_NOT_FOUND"
            if "404" in err:
                return False, "TABLE_NOT_FOUND"
            if "401" in err or "403" in err or "jwt" in err or "invalid api key" in err:
                return False, "API Key không hợp lệ"
            return False, str(e)[:120]
        except urllib.error.URLError:
            return False, "Không kết nối được. Kiểm tra URL và internet"
        except Exception as e:
            return False, f"Lỗi: {str(e)[:120]}"

        # 2. Kiểm tra quyền ghi (thử probe upsert)
        probe_hash = "__clipmaster_probe__"
        now = _now_iso()
        probe_record = {
            "content_hash": probe_hash,
            "type": "probe",
            "content": "probe",
            "char_count": 0,
            "line_count": 0,
            "created_at": now,
            "updated_at": now,
            "deleted_at": now,
        }
        try:
            self._rest_request(
                method="POST",
                path="/pinned_clips?on_conflict=content_hash",
                data=probe_record,
                extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                creds=creds,
                timeout=10.0,
            )
            # Dọn dẹp probe row sau khi test thành công
            try:
                self._rest_request(
                    method="DELETE",
                    path=f"/pinned_clips?content_hash=eq.{probe_hash}",
                    creds=creds,
                    timeout=5.0,
                )
            except Exception:
                pass
            return True, "OK"
        except RuntimeError as e:
            err = str(e).lower()
            if "rls_blocked" in err or "42501" in err:
                return False, "RLS_BLOCKED"
            return False, str(e)[:120]
        except Exception as e:
            return False, f"Lỗi kiểm tra ghi: {str(e)[:120]}"

    # ── Thao tác Push (Local → Cloud) ──────────

    def push_pin(self, clip: dict) -> bool:
        """
        Đẩy 1 mục vừa được ghim lên cloud.
        Dùng thread riêng để không block UI.
        """
        if not self.is_configured():
            return False
        # Nếu chế độ là download_only thì không đẩy lên cloud
        if self.db.get_setting("sync_direction", "both") == "download_only":
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
        Xóa mục đã bỏ ghim khỏi Supabase.
        Dùng DELETE để Supabase không giữ các dòng thừa (tombstone).
        """
        if not self.is_configured():
            return False
        # Nếu chế độ là download_only thì không can thiệp cloud
        if self.db.get_setting("sync_direction", "both") == "download_only":
            return False

        def _unpin():
            try:
                quoted_hash = urllib.parse.quote(content_hash)
                self._rest_request(
                    method="DELETE",
                    path=f"/pinned_clips?content_hash=eq.{quoted_hash}",
                )
            except Exception as e:
                print(f"[Sync] push_unpin error: {e}")

        threading.Thread(target=_unpin, daemon=True).start()
        return True

    # ── Thao tác Pull (Cloud → Local) ──────────

    def pull_all(self, timeout: float = 8.0) -> list[dict]:
        """
        Kéo toàn bộ pinned items đang active từ cloud về.
        Bảo đảm nếu local bị xóa hoặc máy mới cài đặt thì khôi phục đủ 100%.
        """
        if not self.is_configured():
            return []
        try:
            data = self._rest_request(
                method="GET",
                path="/pinned_clips?select=*&order=updated_at.desc",
                timeout=timeout,
            )
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[Sync] pull_all error: {e}")
            return []

    # ── Thao tác Đồng bộ Ghi chú (Notes Sync) ──

    def push_note(self, note: dict) -> bool:
        """
        Đẩy 1 ghi chú (vừa tạo, sửa hoặc đổi ghim) lên Supabase user_notes.
        Chạy trong background thread.
        """
        if not self.is_configured():
            return False
        if self.db.get_setting("sync_direction", "both") == "download_only":
            return False

        def _push():
            try:
                record = {
                    "content_hash": note["content_hash"],
                    "title": note.get("title") or "",
                    "content": note.get("content", ""),
                    "is_pinned": 1 if note.get("is_pinned") else 0,
                    "color": note.get("color"),
                    "created_at": _ts_to_iso(note.get("created_at", time.time())),
                    "updated_at": _ts_to_iso(note.get("updated_at", time.time())),
                    "deleted_at": None,
                }
                self._rest_request(
                    method="POST",
                    path="/user_notes?on_conflict=content_hash",
                    data=record,
                    extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                )
            except Exception as e:
                print(f"[Sync] push_note error: {e}")

        import time
        threading.Thread(target=_push, daemon=True).start()
        return True

    def push_delete_note(self, content_hash: str) -> bool:
        """
        Xóa ghi chú khỏi Supabase khi người dùng xóa trên máy này.
        """
        if not self.is_configured():
            return False
        if self.db.get_setting("sync_direction", "both") == "download_only":
            return False

        def _del():
            try:
                quoted = urllib.parse.quote(content_hash)
                self._rest_request(
                    method="DELETE",
                    path=f"/user_notes?content_hash=eq.{quoted}",
                )
            except Exception as e:
                print(f"[Sync] push_delete_note error: {e}")

        threading.Thread(target=_del, daemon=True).start()
        return True

    def pull_all_notes(self, timeout: float = 8.0) -> list[dict]:
        """Kéo toàn bộ ghi chú từ user_notes trên Supabase về."""
        if not self.is_configured():
            return []
        try:
            data = self._rest_request(
                method="GET",
                path="/user_notes?select=*&order=updated_at.desc",
                timeout=timeout,
            )
            return data if isinstance(data, list) else []
        except Exception as e:
            err_str = str(e)
            if "404" in err_str:
                # Bảng user_notes chưa được tạo trên Supabase
                raise RuntimeError("TABLE_USER_NOTES_NOT_FOUND: Chưa tạo bảng user_notes trên Supabase")
            print(f"[Sync] pull_all_notes error: {e}")
            return []

    # ── Sync hai chiều tổng hợp ─────────────────

    def sync_on_startup(
        self,
        on_done: Optional[callable] = None,
        timeout: float = 8.0,
    ) -> tuple[bool, str]:
        """
        Đồng bộ linh hoạt cả Pinned Clips và Ghi chú (Notes):
        - both: Đầy đủ 2 chiều (vừa kéo về vừa đẩy lên).
        - download_only: Chỉ kéo từ Cloud về Local, không bao giờ ghi đè Cloud.
        - upload_only: Chỉ đẩy từ Local lên Cloud (backup), không kéo về.
        """
        if not self.is_configured():
            if on_done:
                on_done(False, "Chưa cấu hình Supabase")
            return False, "Chưa cấu hình Supabase"

        error_msg = ""
        success = True
        pulled = 0
        pushed = 0
        unpinned = 0
        pulled_notes = 0
        pushed_notes = 0
        deleted_notes = 0
        notes_table_missing = False

        try:
            import time
            direction = self.db.get_setting("sync_direction", "both")
            last_sync_str = self.db.get_setting("last_sync_at", "0")
            try:
                last_sync_ts = float(last_sync_str)
            except ValueError:
                try:
                    dt = datetime.fromisoformat(last_sync_str.replace("Z", "+00:00"))
                    last_sync_ts = dt.timestamp()
                except Exception:
                    last_sync_ts = 0.0

            cloud_hashes = {}

            # 1. Kéo Pinned Clips từ Cloud về Local
            if direction in ("both", "download_only"):
                cloud_items = self.pull_all(timeout=timeout)
                cloud_hashes = {
                    item["content_hash"]: item
                    for item in cloud_items
                    if "content_hash" in item
                }

                for c_hash, item in cloud_hashes.items():
                    if self.db.pin_or_add_by_hash(item):
                        pulled += 1

                # Nếu là download_only: đồng bộ trạng thái unpin theo cloud
                if direction == "download_only":
                    local_pinned = self.db.get_pinned_for_sync()
                    for clip in local_pinned:
                        l_hash = clip.get("content_hash")
                        if l_hash and l_hash not in cloud_hashes:
                            self.db.unpin_by_hash(l_hash)
                            unpinned += 1

            # 2. Đẩy Pinned Clips từ Local lên Cloud
            if direction in ("both", "upload_only"):
                local_pinned = self.db.get_pinned_for_sync()
                to_push = []

                for clip in local_pinned:
                    l_hash = clip.get("content_hash")
                    if not l_hash:
                        continue

                    if direction == "both" and l_hash in cloud_hashes:
                        continue

                    clip_updated_at = clip.get("updated_at", 0.0)

                    if direction == "both" and last_sync_ts > 0 and clip_updated_at <= last_sync_ts:
                        self.db.unpin_by_hash(l_hash)
                        unpinned += 1
                    else:
                        to_push.append(clip)

                if to_push:
                    now = _now_iso()
                    records = [
                        {
                            "content_hash": clip["content_hash"],
                            "type": clip["type"],
                            "content": clip.get("content"),
                            "char_count": clip.get("char_count", 0),
                            "line_count": clip.get("line_count", 0),
                            "created_at": _ts_to_iso(clip.get("created_at", 0)),
                            "updated_at": now,
                            "deleted_at": None,
                        }
                        for clip in to_push
                    ]
                    try:
                        self._rest_request(
                            method="POST",
                            path="/pinned_clips?on_conflict=content_hash",
                            data=records,
                            extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                            timeout=timeout,
                        )
                        pushed = len(records)
                    except Exception as e:
                        print(f"[Sync] batch push error: {e}")
                        error_msg = str(e)
                        success = False

            # ──────────────────────────────────────────
            # 3. Đồng bộ Ghi chú (Notes Sync - Tất cả ghi chú)
            # ──────────────────────────────────────────
            cloud_notes_hashes = {}

            # 3a. Kéo Ghi chú từ Cloud về Local
            if direction in ("both", "download_only"):
                try:
                    cloud_notes_list = self.pull_all_notes(timeout=timeout)
                    cloud_notes_hashes = {
                        item["content_hash"]: item
                        for item in cloud_notes_list
                        if "content_hash" in item
                    }

                    for c_hash, item in cloud_notes_hashes.items():
                        if self.db.upsert_note_from_cloud(item):
                            pulled_notes += 1

                    if direction == "download_only" and cloud_notes_list:
                        for l_note in self.db.get_all_notes_for_sync():
                            l_hash = l_note.get("content_hash")
                            if l_hash and l_hash not in cloud_notes_hashes:
                                self.db.delete_note_by_hash(l_hash)
                                deleted_notes += 1
                except Exception as e:
                    if "user_notes" in str(e).lower() or "404" in str(e):
                        notes_table_missing = True
                    print(f"[Sync] Notes pull error: {e}")

            # 3b. Đẩy Ghi chú từ Local lên Cloud
            if direction in ("both", "upload_only") and not notes_table_missing:
                try:
                    local_notes = self.db.get_all_notes_for_sync()
                    notes_to_push = []

                    for l_note in local_notes:
                        l_hash = l_note.get("content_hash")
                        if not l_hash:
                            continue

                        if direction == "both" and l_hash in cloud_notes_hashes:
                            c_item = cloud_notes_hashes[l_hash]
                            c_updated_str = c_item.get("updated_at")
                            try:
                                dt = datetime.fromisoformat(c_updated_str.replace("Z", "+00:00"))
                                c_ts = dt.timestamp()
                            except Exception:
                                c_ts = 0.0

                            l_updated = l_note.get("updated_at", 0.0)
                            if l_updated > c_ts + 0.5:
                                notes_to_push.append(l_note)
                            continue

                        l_updated = l_note.get("updated_at", 0.0)
                        if direction == "both" and last_sync_ts > 0 and l_updated <= last_sync_ts:
                            self.db.delete_note_by_hash(l_hash)
                            deleted_notes += 1
                        else:
                            notes_to_push.append(l_note)

                    if notes_to_push:
                        records = [
                            {
                                "content_hash": n["content_hash"],
                                "title": n.get("title") or "",
                                "content": n["content"],
                                "is_pinned": 1 if n.get("is_pinned") else 0,
                                "color": n.get("color"),
                                "created_at": _ts_to_iso(n.get("created_at", time.time())),
                                "updated_at": _ts_to_iso(n.get("updated_at", time.time())),
                                "deleted_at": None,
                            }
                            for n in notes_to_push
                        ]
                        self._rest_request(
                            method="POST",
                            path="/user_notes?on_conflict=content_hash",
                            data=records,
                            extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                            timeout=timeout,
                        )
                        pushed_notes = len(records)
                except Exception as e:
                    if "user_notes" in str(e).lower() or "404" in str(e):
                        notes_table_missing = True
                    print(f"[Sync] Notes push error: {e}")

            # Cập nhật thời điểm sync
            if success:
                self.db.set_setting("last_sync_at", str(time.time()))
                msg_parts = []
                if pulled:
                    msg_parts.append(f"↓{pulled}")
                if pushed:
                    msg_parts.append(f"↑{pushed}")
                if unpinned:
                    msg_parts.append(f"✕{unpinned}")
                if pulled_notes:
                    msg_parts.append(f"📝↓{pulled_notes}")
                if pushed_notes:
                    msg_parts.append(f"📝↑{pushed_notes}")
                if deleted_notes:
                    msg_parts.append(f"📝✕{deleted_notes}")
                if notes_table_missing:
                    msg_parts.append("⚠️ Cần tạo bảng user_notes trên Supabase")

                change_str = f" ({', '.join(msg_parts)})" if msg_parts else ""
                msg = f"Đồng bộ thành công{change_str}"
            else:
                msg = f"Đồng bộ gặp lỗi: {error_msg}"

            print(f"[Sync] Kết quả: {msg}")

        except Exception as e:
            success = False
            msg = f"Lỗi đồng bộ: {e}"
            print(f"[Sync] {msg}")
        finally:
            if on_done:
                try:
                    on_done(success, msg)
                except Exception as e:
                    print(f"[Sync] on_done callback error: {e}")

        return success, msg

    def run_startup_sync_async(self, on_done: Optional[callable] = None) -> None:
        """Chạy sync_on_startup trong daemon thread."""
        threading.Thread(
            target=self.sync_on_startup,
            kwargs={"on_done": on_done},
            daemon=True,
        ).start()

    def trigger_ondemand_sync(
        self,
        min_interval_seconds: float = 30.0,
        on_updated: Optional[callable] = None,
    ) -> bool:
        """
        Kích hoạt đồng bộ nhẹ khi người dùng mở cửa sổ Win+V.
        Áp dụng cơ chế Throttling / Debounce:
        1. Nếu chưa cấu hình Supabase -> Bỏ qua.
        2. Nếu đang có luồng sync đang chạy -> Bỏ qua (chống chồng chéo luồng).
        3. Nếu khoảng cách từ lần sync gần nhất < min_interval_seconds -> Bỏ qua (chống spam phím Win+V).
        4. Chạy trong daemon thread, không block UI thread.
        5. Timeout mạng ngắn (4.0s) để nếu rớt mạng thì thoát ngay, không treo.
        6. Chỉ gọi on_updated khi thực sự có thay đổi từ Cloud (pulled > 0 hoặc unpinned > 0).

        Returns:
            True nếu đã kích hoạt luồng sync, False nếu bị throttle/bỏ qua.
        """
        if not self.is_configured():
            return False

        import time
        now = time.time()

        with self._lock:
            if self._is_syncing:
                return False
            if (now - self._last_ondemand_ts) < min_interval_seconds:
                return False
            self._is_syncing = True
            self._last_ondemand_ts = now

        def _worker():
            try:
                # Timeout ngắn (4.0s)
                success, msg = self.sync_on_startup(timeout=4.0)
                # Chỉ reload UI khi thực sự có thay đổi kéo về hoặc bỏ ghim
                if success and ("↓" in msg or "✕" in msg):
                    if on_updated:
                        on_updated()
            except Exception:
                pass
            finally:
                with self._lock:
                    self._is_syncing = False

        threading.Thread(target=_worker, daemon=True).start()
        return True
