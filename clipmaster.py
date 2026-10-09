#!/usr/bin/env python3
"""
ClipMaster - Trình quản lý lịch sử sao chép giống Windows + V trên Ubuntu / Linux
"""

import os
import sys
import socket
import threading

# Ensure local src package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

from src.database import Database
from src.clipboard_manager import ClipboardManager
from src.ui.main_window import MainWindow
from src.theme_manager import apply_theme_mode, toggle_theme_mode
from src.sync_manager import SyncManager
from src.shortcut_manager import (
    install_super_v_shortcut,
    remove_super_v_shortcut,
    setup_autostart,
    setup_desktop_entry,
    is_shortcut_installed,
    get_current_shortcut,
    set_custom_shortcut,
    format_shortcut_display
)

# Set application name and program name for GNOME / Wayland window tracking
GLib.set_prgname("clipmaster")
GLib.set_application_name("ClipMaster")


def get_ipc_socket_path():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", os.path.expanduser("~/.local/share/clipmaster"))
    return os.path.join(runtime_dir, "clipmaster_ipc.sock")


def send_ipc_command(cmd: str) -> bool:
    """Send command to running instance if one exists. Returns True if handled."""
    sock_path = get_ipc_socket_path()
    if not os.path.exists(sock_path):
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(0.8)
            client.connect(sock_path)
            client.sendall(f"{cmd}\n".encode())
            resp = client.recv(1024)
            return resp.strip() == b"OK"
    except Exception:
        try:
            os.unlink(sock_path)
        except OSError:
            pass
        return False


def start_ipc_server(on_command_callback):
    """Start background socket listener for CLI / IPC commands."""
    sock_path = get_ipc_socket_path()
    if os.path.exists(sock_path):
        try:
            os.unlink(sock_path)
        except OSError:
            pass

    try:
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(sock_path)
        server.listen(5)
    except Exception:
        return None

    def listen_loop():
        while True:
            try:
                conn, _ = server.accept()
                with conn:
                    data = conn.recv(1024).decode().strip()
                    if data:
                        on_command_callback(data)
                    conn.sendall(b"OK\n")
            except Exception:
                break

    t = threading.Thread(target=listen_loop, daemon=True)
    t.start()
    return server


class ClipMasterApplication(Adw.Application):
    def __init__(self):
        in_snap = "SNAP" in os.environ
        app_id = None if in_snap else "com.clipmaster.ClipMaster"
        super().__init__(
            application_id=app_id,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        self.db = Database()
        self.clipboard_mgr = None
        self.sync_mgr = None
        self.window = None
        self._is_held = False
        self.ipc_server = None

        if not in_snap:
            try:
                self.register(None)
            except GLib.GError:
                self.set_application_id(None)
                self.register(None)

    def do_startup(self):
        Adw.Application.do_startup(self)

        # Apply saved theme mode
        apply_theme_mode(self.db.get_setting("theme_mode", "dark"))

        self.clipboard_mgr = ClipboardManager(
            db=self.db,
            on_new_clip=self._on_new_clip
        )
        self.clipboard_mgr.start_monitoring()

        # Khởi tạo SyncManager và chạy startup sync trong nền
        self.sync_mgr = SyncManager(db=self.db)
        if self.sync_mgr.is_configured():
            def _on_startup_sync(success, msg):
                if success and hasattr(self, "window") and self.window:
                    GLib.idle_add(self.window.reload_history)
            self.sync_mgr.run_startup_sync_async(on_done=_on_startup_sync)

        # Start IPC socket server for single-instance commands
        self.ipc_server = start_ipc_server(self._handle_ipc_command)

        # Ensure global shortcut (Win + V by default) is configured on startup
        try:
            if not get_current_shortcut():
                install_super_v_shortcut()
                self.db.set_setting("shortcut", "<Super>v")
        except Exception as e:
            print(f"Notice: Could not auto-install default shortcut: {e}")

        # Hold application so it continues running in background
        if not self._is_held:
            self.hold()
            self._is_held = True

    def _handle_ipc_command(self, cmd: str):
        if cmd == "toggle":
            GLib.idle_add(self._toggle_from_ipc)
        elif cmd == "clear":
            self.db.clear_unpinned()
            if self.window:
                GLib.idle_add(self.window.reload_history)
        elif cmd == "reload":
            if self.window:
                GLib.idle_add(self.window.reload_history)

    def _toggle_from_ipc(self):
        self._ensure_window()
        self.window.toggle_visibility()

    def do_activate(self):
        self._ensure_window()
        self.window.toggle_visibility()

    def do_command_line(self, command_line):
        args = command_line.get_arguments()

        if "--install-shortcut" in args:
            ok1 = install_super_v_shortcut()
            ok2 = setup_autostart(True)
            ok3 = setup_desktop_entry()
            if ok1 and ok2 and ok3:
                print("✓ Đã cài đặt phím tắt Win + V (<Super>v) và khởi động cùng hệ thống thành công!")
            else:
                print("⚠️ Cài đặt phím tắt có lỗi xảy ra.")
            if not self.window:
                self.quit()
            return 0

        if "--remove-shortcut" in args:
            remove_super_v_shortcut()
            setup_autostart(False)
            print("✓ Đã gỡ bỏ phím tắt Win + V.")
            if not self.window:
                self.quit()
            return 0

        if "--theme" in args:
            idx = args.index("--theme")
            if idx + 1 < len(args):
                new_theme = args[idx + 1]
                if new_theme in ("dark", "light", "system"):
                    self.db.set_setting("theme_mode", new_theme)
                    apply_theme_mode(new_theme)
                    print(f"✓ Đã chuyển giao diện sang: {new_theme}")
            if not self.window:
                self.quit()
            return 0

        if "--toggle-theme" in args:
            new_theme = toggle_theme_mode(self.db)
            print(f"✓ Đã chuyển giao diện sang: {new_theme}")
            if not self.window:
                self.quit()
            return 0

        if "--clear" in args:
            cnt = self.db.clear_unpinned()
            print(f"✓ Đã xóa {cnt} mục chưa ghim khỏi lịch sử.")
            if self.window:
                GLib.idle_add(self.window.reload_history)
            else:
                self.quit()
            return 0

        if "--status" in args:
            stats = self.db.get_stats()
            shortcut_ok = is_shortcut_installed()
            cur_theme = self.db.get_setting("theme_mode", "dark")
            theme_names = {"dark": "Tối / Dark 🌙", "light": "Sáng / Light ☀️", "system": "Theo hệ thống / System 🌓"}
            print("=== ClipMaster Status ===")
            print(f"Giao diện / Theme: {theme_names.get(cur_theme, cur_theme)}")
            print(f"Tổng số mục: {stats['total']}")
            print(f"Đã ghim: {stats['pinned']}")
            print(f"Phím tắt Win + V: {'Đã kích hoạt' if shortcut_ok else 'Chưa kích hoạt'}")
            if not self.window:
                self.quit()
            return 0

        if "--daemon" in args:
            # Running as background service
            self._ensure_window()
            return 0

        # Default or --toggle: Show / toggle popup window
        self._ensure_window()
        self.window.toggle_visibility()
        return 0

    def _ensure_window(self):
        if not self.window:
            self.window = MainWindow(
                app=self,
                db=self.db,
                clipboard_mgr=self.clipboard_mgr,
                sync_mgr=self.sync_mgr,
            )

    def _on_new_clip(self, clip):
        """Called when a new clipboard item is captured."""
        if self.window and self.window.get_visible():
            GLib.idle_add(self.window.reload_history)


def handle_cli_direct(args):
    """Handle instant CLI flags directly in caller terminal."""
    if len(args) <= 1:
        return False

    arg = args[1]
    if arg in ("-h", "--help"):
        print("ClipMaster - Clipboard Manager cho Ubuntu / Linux (tương tự Win + V)")
        print("")
        print("Sử dụng: clipmaster [TÙY CHỌN]")
        print("")
        print("Tùy chọn:")
        print("  --toggle                 Bật / tắt cửa sổ lịch sử")
        print("  --daemon                 Chạy ngầm theo dõi clipboard")
        print("  --theme <dark|light|system>  Đổi giao diện (Tối / Sáng / Theo hệ thống)")
        print("  --toggle-theme           Chuyển đổi nhanh chế độ sáng / tối")
        print("  --set-lang <vi|en>       Đổi ngôn ngữ hiển thị (Tiếng Việt / English)")
        print("  --toggle-record          Bật / tắt nhanh tính năng tự động ghi nhớ (Pause/Resume)")
        print("  --pause                  Tạm dừng tự động ghi nhớ (chế độ ẩn danh)")
        print("  --resume                 Tiếp tục tự động ghi nhớ")
        print("  --install-shortcut       Cài đặt phím tắt mặc định Win + V (<Super>v) và autostart")
        print("  --set-shortcut <PHÍM>    Đổi phím tắt tùy chỉnh (ví dụ: '<Control><Alt>v', '<Super>c')")
        print("  --remove-shortcut        Gỡ bỏ phím tắt toàn cục")
        print("  --clear                  Xóa toàn bộ mục chưa ghim")
        print("  --status                 Xem thống kê và phím tắt hiện tại")
        print("  --help                   Hiển thị thông tin trợ giúp này")
        return True

    if arg == "--status":
        db = Database()
        stats = db.get_stats()
        cur_shortcut = get_current_shortcut()
        disp = format_shortcut_display(cur_shortcut) if cur_shortcut else "Chưa kích hoạt"
        is_rec = db.get_setting("auto_record", "1") == "1"
        cur_lang = db.get_setting("language", "vi")
        lang_name = "Tiếng Việt (vi)" if cur_lang == "vi" else "English (en)"
        cur_theme = db.get_setting("theme_mode", "dark")
        theme_names = {"dark": "Tối / Dark 🌙", "light": "Sáng / Light ☀️", "system": "Theo hệ thống / System 🌓"}
        print("=== ClipMaster Status ===")
        print(f"Giao diện / Theme: {theme_names.get(cur_theme, cur_theme)}")
        print(f"Ngôn ngữ / Language: {lang_name}")
        print(f"Tổng số mục: {stats['total']}")
        print(f"Đã ghim: {stats['pinned']}")
        print(f"Phím tắt kích hoạt: {disp} ({cur_shortcut if cur_shortcut else 'None'})")
        print(f"Tự động ghi nhớ: {'Đang BẬT 🟢' if is_rec else 'Đang TẠM DỪNG ⏸️'}")
        return True

    if arg == "--theme":
        if len(args) < 3 or args[2] not in ("dark", "light", "system"):
            print("⚠️ Vui lòng chỉ định 'dark' (Tối), 'light' (Sáng) hoặc 'system' (Hệ thống). Ví dụ: python3 clipmaster.py --theme dark")
            return True
        db = Database()
        new_theme = args[2]
        db.set_setting("theme_mode", new_theme)
        names = {"dark": "Tối (Dark) 🌙", "light": "Sáng (Light) ☀️", "system": "Theo hệ thống (System) 🌓"}
        print(f"✓ Đã chuyển giao diện sang: {names.get(new_theme, new_theme)}")
        return True

    if arg == "--toggle-theme":
        db = Database()
        cur = db.get_setting("theme_mode", "dark")
        new_theme = "light" if cur == "dark" else "dark"
        db.set_setting("theme_mode", new_theme)
        names = {"dark": "Tối (Dark) 🌙", "light": "Sáng (Light) ☀️"}
        print(f"✓ Đã chuyển giao diện sang: {names.get(new_theme, new_theme)}")
        return True

    if arg == "--set-lang":
        if len(args) < 3 or args[2] not in ("vi", "en"):
            print("⚠️ Vui lòng chỉ định 'vi' (Tiếng Việt) hoặc 'en' (English). Ví dụ: python3 clipmaster.py --set-lang en")
            return True
        db = Database()
        new_lang = args[2]
        db.set_setting("language", new_lang)
        name = "Tiếng Việt" if new_lang == "vi" else "English"
        print(f"✓ Đã chuyển ngôn ngữ sang: {name} ({new_lang})")
        return True

    if arg == "--pause":
        db = Database()
        db.set_setting("auto_record", "0")
        print("⏸️ Đã tạm dừng tự động ghi nhớ clipboard (nội dung copy sẽ không được lưu).")
        return True

    if arg == "--resume":
        db = Database()
        db.set_setting("auto_record", "1")
        print("🟢 Đã tiếp tục tự động ghi nhớ clipboard.")
        return True

    if arg == "--toggle-record":
        db = Database()
        cur = db.get_setting("auto_record", "1") == "1"
        new_val = "0" if cur else "1"
        db.set_setting("auto_record", new_val)
        if new_val == "1":
            print("🟢 Đã tiếp tục tự động ghi nhớ clipboard.")
        else:
            print("⏸️ Đã tạm dừng tự động ghi nhớ clipboard (chế độ ẩn danh).")
        return True

    if arg == "--set-shortcut":
        if len(args) < 3:
            print("⚠️ Vui lòng chỉ định tổ hợp phím. Ví dụ: python3 clipmaster.py --set-shortcut '<Control><Alt>v'")
            return True
        new_key = args[2]
        ok = set_custom_shortcut(new_key)
        if ok:
            disp = format_shortcut_display(new_key)
            print(f"✓ Đã đổi phím tắt thành công: {disp} ({new_key})")
        else:
            print(f"⚠️ Đổi phím tắt thất bại cho mã: {new_key}")
        return True

    if arg == "--install-shortcut":
        ok1 = install_super_v_shortcut()
        ok2 = setup_autostart(True)
        ok3 = setup_desktop_entry()
        if ok1 and ok2 and ok3:
            print("✓ Đã cài đặt phím tắt Win + V (<Super>v) và khởi động cùng hệ thống thành công!")
        else:
            print("⚠️ Cài đặt phím tắt có lỗi xảy ra.")
        return True

    if arg == "--remove-shortcut":
        remove_super_v_shortcut()
        setup_autostart(False)
        print("✓ Đã gỡ bỏ phím tắt toàn cục.")
        return True

    if arg == "--clear":
        db = Database()
        cnt = db.clear_unpinned()
        print(f"✓ Đã xóa {cnt} mục chưa ghim khỏi lịch sử.")
        return True

    return False


def main():
    if handle_cli_direct(sys.argv):
        sys.exit(0)

    # If --toggle or default launch is requested, delegate to running instance if one exists
    is_toggle_req = (len(sys.argv) <= 1) or (len(sys.argv) > 1 and sys.argv[1] == "--toggle")
    if is_toggle_req:
        if send_ipc_command("toggle"):
            sys.exit(0)

    app = ClipMasterApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)


if __name__ == "__main__":
    main()
