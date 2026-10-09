"""
ClipMaster Sync Setup Dialog
Giao diện cấu hình BYOS (Bring Your Own Supabase) cho người dùng.

Luồng:
  Bước 1 — Nhập URL + Anon Key → kiểm tra kết nối
  Bước 2 — Nếu bảng chưa tồn tại → nhập PAT để tự động tạo bảng
  Bước 3 — Lưu config, chạy initial sync, hiện trạng thái thành công
"""

import threading
import webbrowser

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from ..sync_manager import SyncManager
from ..i18n import t


# URL hướng dẫn lấy PAT
PAT_GUIDE_URL = "https://supabase.com/dashboard/account/tokens"
SUPABASE_DASHBOARD_URL = "https://supabase.com/dashboard"


class SyncSetupDialog(Adw.Window):
    """
    Dialog cấu hình đồng bộ BYOS theo dạng multi-step:
      Step 1: Nhập URL + Anon Key
      Step 2: Nhập PAT (chỉ khi bảng chưa tạo)
      Done:   Hiển thị trạng thái thành công
    """

    def __init__(
        self,
        parent_window: Gtk.Window,
        sync_mgr: SyncManager,
        lang: str = "vi",
        on_connected: callable = None,
    ):
        super().__init__()
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_default_size(480, -1)
        self.set_title("☁️ Đồng bộ Pinned Items" if lang == "vi" else "☁️ Sync Pinned Items")

        self.sync_mgr = sync_mgr
        self.lang = lang
        self.on_connected = on_connected

        # State
        self._url = ""
        self._key = ""
        self._is_loading = False

        self._build_ui()

    # ─── Build UI ────────────────────────────────

    def _build_ui(self):
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header bar
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        root_box.append(header)

        # Content
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self._stack.set_margin_start(24)
        self._stack.set_margin_end(24)
        self._stack.set_margin_top(12)
        self._stack.set_margin_bottom(24)

        self._stack.add_named(self._build_step1_page(), "step1")
        self._stack.add_named(self._build_step2_page(), "step2")
        self._stack.add_named(self._build_done_page(), "done")

        root_box.append(self._stack)
        self.set_content(root_box)

    def _build_step1_page(self) -> Gtk.Widget:
        """Bước 1: Nhập URL + Anon Key."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

        # Mô tả
        lbl = Gtk.Label()
        lbl.set_markup(
            "<b>Bước 1 / 2</b>\n"
            "Nhập thông tin Supabase project của bạn.\n"
            "<small>Lấy tại: Supabase Dashboard → Settings → API</small>"
            if self.lang == "vi" else
            "<b>Step 1 of 2</b>\n"
            "Enter your Supabase project credentials.\n"
            "<small>Find these at: Supabase Dashboard → Settings → API</small>"
        )
        lbl.set_wrap(True)
        lbl.set_xalign(0)
        box.append(lbl)

        # URL entry
        url_group = Adw.PreferencesGroup()
        self._url_row = Adw.EntryRow()
        self._url_row.set_title(
            "Project URL" if self.lang == "en"
            else "Project URL"
        )
        self._url_row.set_input_purpose(Gtk.InputPurpose.URL)

        # Điền sẵn nếu đã có config
        existing = self.sync_mgr.get_configured_url()
        if existing:
            self._url_row.set_text(existing)

        url_group.add(self._url_row)

        # Anon Key entry
        self._key_row = Adw.PasswordEntryRow()
        self._key_row.set_title(
            "Anon Public Key" if self.lang == "en"
            else "Anon Key (anon public)"
        )
        url_group.add(self._key_row)

        box.append(url_group)

        # Status label
        self._step1_status = Gtk.Label(label="")
        self._step1_status.set_xalign(0)
        self._step1_status.add_css_class("caption")
        box.append(self._step1_status)

        # Buttons row
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_row.set_halign(Gtk.Align.END)

        # Nút mở dashboard
        open_btn = Gtk.Button(
            label="🌐 Mở Dashboard" if self.lang == "vi" else "🌐 Open Dashboard"
        )
        open_btn.connect("clicked", lambda _: webbrowser.open(SUPABASE_DASHBOARD_URL))
        btn_row.append(open_btn)

        # Nút tiếp theo
        self._next_btn = Gtk.Button(
            label="Kiểm tra kết nối →" if self.lang == "vi" else "Test Connection →"
        )
        self._next_btn.add_css_class("suggested-action")
        self._next_btn.connect("clicked", self._on_step1_next)
        btn_row.append(self._next_btn)

        box.append(btn_row)
        return box

    def _build_step2_page(self) -> Gtk.Widget:
        """Bước 2: Nhập PAT để tự động tạo bảng."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

        lbl = Gtk.Label()
        lbl.set_markup(
            "<b>Bước 2 / 2 — Khởi tạo database</b>\n"
            "Cần tạo bảng dữ liệu trong Supabase của bạn.\n"
            "Nhập <b>Personal Access Token (PAT)</b> để app tự động thực hiện.\n\n"
            "<small>⚠️ PAT chỉ dùng 1 lần và <b>không được lưu lại</b>.</small>"
            if self.lang == "vi" else
            "<b>Step 2 of 2 — Database Setup</b>\n"
            "Need to create a table in your Supabase project.\n"
            "Enter your <b>Personal Access Token (PAT)</b> to auto-setup.\n\n"
            "<small>⚠️ The PAT is used once and <b>never stored</b>.</small>"
        )
        lbl.set_wrap(True)
        lbl.set_xalign(0)
        box.append(lbl)

        pat_group = Adw.PreferencesGroup()
        self._pat_row = Adw.PasswordEntryRow()
        self._pat_row.set_title("Personal Access Token (PAT)")
        pat_group.add(self._pat_row)
        box.append(pat_group)

        # Status
        self._step2_status = Gtk.Label(label="")
        self._step2_status.set_xalign(0)
        self._step2_status.add_css_class("caption")
        box.append(self._step2_status)

        # Spinner
        self._spinner = Gtk.Spinner()
        self._spinner.set_halign(Gtk.Align.CENTER)
        self._spinner.set_size_request(32, 32)
        box.append(self._spinner)

        # Buttons
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_row.set_halign(Gtk.Align.END)

        back_btn = Gtk.Button(
            label="← Quay lại" if self.lang == "vi" else "← Back"
        )
        back_btn.connect("clicked", lambda _: self._stack.set_visible_child_name("step1"))
        btn_row.append(back_btn)

        guide_btn = Gtk.Button(
            label="📖 Hướng dẫn lấy PAT" if self.lang == "vi" else "📖 How to get PAT"
        )
        guide_btn.connect("clicked", lambda _: webbrowser.open(PAT_GUIDE_URL))
        btn_row.append(guide_btn)

        self._setup_btn = Gtk.Button(
            label="✨ Tự động thiết lập" if self.lang == "vi" else "✨ Auto Setup"
        )
        self._setup_btn.add_css_class("suggested-action")
        self._setup_btn.connect("clicked", self._on_step2_setup)
        btn_row.append(self._setup_btn)

        box.append(btn_row)
        return box

    def _build_done_page(self) -> Gtk.Widget:
        """Trang hoàn thành."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_valign(Gtk.Align.CENTER)

        icon = Gtk.Label(label="✅")
        icon.add_css_class("title-1")
        icon.set_halign(Gtk.Align.CENTER)
        box.append(icon)

        self._done_lbl = Gtk.Label()
        self._done_lbl.set_markup(
            "<b>Đồng bộ đã được kích hoạt!</b>\n"
            "Các mục ghim sẽ tự động đồng bộ giữa các máy."
            if self.lang == "vi" else
            "<b>Sync activated!</b>\n"
            "Pinned items will now sync automatically across your devices."
        )
        self._done_lbl.set_wrap(True)
        self._done_lbl.set_justify(Gtk.Justification.CENTER)
        box.append(self._done_lbl)

        close_btn = Gtk.Button(
            label="Đóng" if self.lang == "vi" else "Close"
        )
        close_btn.add_css_class("suggested-action")
        close_btn.set_halign(Gtk.Align.CENTER)
        close_btn.connect("clicked", lambda _: self.close())
        box.append(close_btn)

        return box

    # ─── Step logic ──────────────────────────────

    def _on_step1_next(self, _btn):
        """Xử lý khi nhấn 'Kiểm tra kết nối'."""
        url = self._url_row.get_text().strip()
        key = self._key_row.get_text().strip()

        if not url or not key:
            self._set_step1_status("⚠️ Vui lòng nhập đầy đủ URL và API Key.", error=True)
            return

        self._url = url
        self._key = key
        self._set_step1_status(
            "🔄 Đang kiểm tra kết nối..." if self.lang == "vi" else "🔄 Testing connection...",
            error=False
        )
        self._next_btn.set_sensitive(False)

        def _test():
            ok, msg = self.sync_mgr.test_connection(url, key)
            GLib.idle_add(self._on_connection_result, ok, msg)

        threading.Thread(target=_test, daemon=True).start()

    def _on_connection_result(self, ok: bool, msg: str):
        self._next_btn.set_sensitive(True)

        if ok:
            # Kết nối OK và bảng đã có → lưu và đồng bộ luôn
            self._set_step1_status("✅ Kết nối thành công!", error=False)
            self._finalize_connection()

        elif msg in ("TABLE_NOT_FOUND", "RLS_BLOCKED"):
            # Bảng chưa tồn tại hoặc bị chặn bởi RLS
            if msg == "RLS_BLOCKED":
                status_txt = (
                    "⚠️ Bảng bị chặn ghi bởi Row Level Security (RLS). Cần cập nhật schema..."
                    if self.lang == "vi"
                    else "⚠️ Table writes blocked by Row Level Security (RLS). Schema update needed..."
                )
            else:
                status_txt = (
                    "✅ Kết nối thành công! Cần khởi tạo database..."
                    if self.lang == "vi"
                    else "✅ Connected! Database setup needed..."
                )
            self._set_step1_status(status_txt, error=False)
            GLib.timeout_add(600, lambda: self._stack.set_visible_child_name("step2") or False)

        else:
            self._set_step1_status(f"❌ {msg}", error=True)

    def _on_step2_setup(self, _btn):
        """Xử lý khi nhấn 'Tự động thiết lập'."""
        pat = self._pat_row.get_text().strip()
        if not pat:
            self._set_step2_status("⚠️ Vui lòng nhập PAT.", error=True)
            return

        self._setup_btn.set_sensitive(False)
        self._spinner.start()
        self._set_step2_status(
            "🔄 Đang tạo bảng dữ liệu..." if self.lang == "vi" else "🔄 Creating database table...",
            error=False
        )

        def _setup():
            ok, msg = self.sync_mgr.auto_setup_schema(self._url, pat)
            GLib.idle_add(self._on_setup_result, ok, msg)

        threading.Thread(target=_setup, daemon=True).start()

    def _on_setup_result(self, ok: bool, msg: str):
        self._spinner.stop()
        self._setup_btn.set_sensitive(True)

        if ok:
            self._set_step2_status("✅ Bảng đã được tạo thành công!", error=False)
            GLib.timeout_add(500, lambda: self._finalize_connection() or False)
        else:
            self._set_step2_status(f"❌ {msg}", error=True)

    def _finalize_connection(self):
        """Lưu config, chạy initial sync, chuyển sang trang Done."""
        # Lưu URL + Key (PAT KHÔNG lưu)
        self.sync_mgr.config.save(self._url, self._key)
        self.sync_mgr._reset_client()

        # Chạy initial sync trong nền
        def _do_sync():
            self.sync_mgr.sync_on_startup()
            GLib.idle_add(lambda: self._on_sync_done())

        threading.Thread(target=_do_sync, daemon=True).start()

        # Chuyển sang trang Done ngay (sync chạy ngầm)
        self._stack.set_visible_child_name("done")

        if self.on_connected:
            try:
                self.on_connected()
            except Exception:
                pass

    def _on_sync_done(self):
        """Callback sau khi initial sync hoàn thành."""
        pass  # UI đã ở trang Done, không cần làm gì thêm

    # ─── Helpers ─────────────────────────────────

    def _set_step1_status(self, msg: str, error: bool = False):
        self._step1_status.set_text(msg)
        if error:
            self._step1_status.add_css_class("error")
        else:
            self._step1_status.remove_css_class("error")

    def _set_step2_status(self, msg: str, error: bool = False):
        self._step2_status.set_text(msg)
        if error:
            self._step2_status.add_css_class("error")
        else:
            self._step2_status.remove_css_class("error")
