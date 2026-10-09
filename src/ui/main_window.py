"""
ClipMaster Main Window
Floating clipboard history popup inspired by Windows + V.
"""

import os
from typing import Dict, Any, Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, GLib

from ..database import Database
from ..clipboard_manager import ClipboardManager
from ..i18n import t
from ..theme_manager import apply_theme_mode, toggle_theme_mode
from ..sync_manager import SyncManager
from .history_item_row import HistoryItemRow
from .settings_dialog import SettingsDialog


class MainWindow(Adw.ApplicationWindow):
    def __init__(
        self,
        app: Adw.Application,
        db: Database,
        clipboard_mgr: ClipboardManager,
        sync_mgr: SyncManager = None,
    ):
        super().__init__(application=app)
        self.app = app
        self.db = db
        self.clipboard_mgr = clipboard_mgr
        self.sync_mgr = sync_mgr

        self.lang = self.db.get_setting("language", "vi")
        self.current_filter = "all"
        self.current_query = ""
        self._filter_buttons = {}

        # Apply saved theme mode
        apply_theme_mode(self.db.get_setting("theme_mode", "dark"))
        Adw.StyleManager.get_default().connect("notify::dark", self._on_dark_changed)

        self._setup_window_properties()
        self._load_css()
        self._build_ui()
        self._setup_key_controller()
        self.reload_history()

    def _setup_window_properties(self):
        self.set_title("ClipMaster - Clipboard History (Win + V)")
        self.set_default_size(460, 620)
        self.add_css_class("clipmaster-window")

        # Configure Icon theme so GTK can always find clipmaster icon
        display = Gdk.Display.get_default()
        if display:
            theme = Gtk.IconTheme.get_for_display(display)
            assets_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "assets")
            )
            if os.path.exists(assets_dir):
                theme.add_search_path(assets_dir)
            user_icon_dir = os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps")
            if os.path.exists(user_icon_dir):
                theme.add_search_path(user_icon_dir)
        self.set_icon_name("clipmaster")

        # Hide window on close instead of destroying
        self.connect("close-request", self._on_close_request)

    def _load_css(self):
        css_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "assets", "style.css")
        )
        if os.path.exists(css_file):
            provider = Gtk.CssProvider()
            provider.load_from_path(css_file)
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )

    def _build_ui(self):
        # Toast Overlay wrapping everything
        self.toast_overlay = Adw.ToastOverlay()

        # Main Vertical Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # 1. Header Bar
        header = Adw.HeaderBar()
        self.title_widget = Adw.WindowTitle(
            title=t("app_title", self.lang),
            subtitle=t("app_subtitle", self.lang)
        )
        header.set_title_widget(self.title_widget)

        # Quick Auto-Record Toggle Button (Bật/Tắt tự động ghi nhớ)
        self.record_btn = Gtk.Button()
        self.record_btn.add_css_class("record-btn")
        self.record_btn.connect("clicked", self._on_toggle_record)
        header.pack_start(self.record_btn)

        # Settings Button
        self.settings_btn = Gtk.Button()
        self.settings_btn.set_icon_name("preferences-system-symbolic")
        self.settings_btn.set_tooltip_text(t("tooltip_settings", self.lang))
        self.settings_btn.connect("clicked", self._open_settings)
        header.pack_end(self.settings_btn)

        # Theme Toggle Button (Chế độ Sáng / Tối)
        self.theme_btn = Gtk.Button()
        self.theme_btn.add_css_class("theme-btn")
        self.theme_btn.connect("clicked", self._on_toggle_theme)
        header.pack_end(self.theme_btn)

        # Clear Unpinned Button
        self.clear_btn = Gtk.Button()
        self.clear_btn.set_icon_name("user-trash-symbolic")
        self.clear_btn.set_tooltip_text(t("tooltip_clear", self.lang))
        self.clear_btn.connect("clicked", self._confirm_clear_unpinned)
        header.pack_end(self.clear_btn)

        main_box.append(header)

        # Pause Warning Banner (Hiển thị khi tạm dừng ghi nhớ)
        self.pause_banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.pause_banner.add_css_class("pause-banner")

        pause_icon = Gtk.Image.new_from_icon_name("media-playback-pause-symbolic")
        self.pause_banner.append(pause_icon)

        self.pause_lbl = Gtk.Label(label=t("pause_banner_text", self.lang))
        self.pause_lbl.add_css_class("pause-banner-lbl")
        self.pause_lbl.set_halign(Gtk.Align.START)
        self.pause_lbl.set_hexpand(True)
        self.pause_banner.append(self.pause_lbl)

        self.resume_btn = Gtk.Button(label=t("pause_banner_resume", self.lang))
        self.resume_btn.add_css_class("pause-banner-btn")
        self.resume_btn.connect("clicked", self._on_toggle_record)
        self.pause_banner.append(self.resume_btn)

        main_box.append(self.pause_banner)

        # 2. Search Entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.add_css_class("search-bar")
        self._set_search_placeholder(t("search_placeholder", self.lang))
        self.search_entry.connect("search-changed", self._on_search_changed)
        main_box.append(self.search_entry)

        # 3. Category Filter Chips / Tabs
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        filter_box.add_css_class("filter-box")
        filter_box.set_halign(Gtk.Align.CENTER)

        filters = [
            ("all", "filter_all"),
            ("text", "filter_text"),
            ("code", "filter_code"),
            ("url", "filter_url"),
            ("image", "filter_image"),
            ("pinned", "filter_pinned")
        ]

        for f_key, f_trans_key in filters:
            btn = Gtk.Button(label=t(f_trans_key, self.lang))
            btn.add_css_class("filter-chip")
            if f_key == self.current_filter:
                btn.add_css_class("active")
            btn.connect("clicked", self._make_filter_handler(f_key))
            self._filter_buttons[f_key] = (btn, f_trans_key)
            filter_box.append(btn)

        main_box.append(filter_box)

        # 4. History List in Scrolled Window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # Stack to switch between List and Empty state
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # List Box
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.add_css_class("boxed-list")
        self.list_box.connect("row-activated", self._on_row_activated)
        scrolled.set_child(self.list_box)
        self.stack.add_named(scrolled, "list")

        # Empty State
        empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        empty_box.add_css_class("empty-box")
        empty_box.set_valign(Gtk.Align.CENTER)
        empty_box.set_halign(Gtk.Align.CENTER)

        empty_icon = Gtk.Image.new_from_icon_name("edit-copy-symbolic")
        empty_icon.set_pixel_size(64)
        empty_icon.set_opacity(0.4)
        empty_box.append(empty_icon)

        self.empty_title = Gtk.Label(label=t("empty_title", self.lang))
        self.empty_title.add_css_class("empty-title")
        empty_box.append(self.empty_title)

        self.empty_desc = Gtk.Label(label=t("empty_desc", self.lang))
        self.empty_desc.add_css_class("empty-desc")
        self.empty_desc.set_justify(Gtk.Justification.CENTER)
        empty_box.append(self.empty_desc)

        self.stack.add_named(empty_box, "empty")
        main_box.append(self.stack)

        # 5. Bottom Status Bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_bar.add_css_class("status-bar")

        self.status_lbl = Gtk.Label(label="...")
        self.status_lbl.set_halign(Gtk.Align.START)
        status_bar.append(self.status_lbl)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        status_bar.append(spacer)

        self.hint_lbl = Gtk.Label(label=t("status_hint", self.lang))
        self.hint_lbl.set_halign(Gtk.Align.END)
        status_bar.append(self.hint_lbl)

        main_box.append(status_bar)

        self.toast_overlay.set_child(main_box)
        self.set_content(self.toast_overlay)

    def _setup_key_controller(self):
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        # Esc -> Hide window
        if keyval == Gdk.KEY_Escape:
            self.hide()
            return True

        # Ctrl+F -> Focus search bar
        if (state & Gdk.ModifierType.CONTROL_MASK) and (keyval == Gdk.KEY_f or keyval == Gdk.KEY_F):
            self.search_entry.grab_focus()
            return True

        # Delete key on selected item -> delete it
        if keyval == Gdk.KEY_Delete:
            selected_row = self.list_box.get_selected_row()
            if selected_row and hasattr(selected_row, "clip"):
                self._delete_clip(selected_row.clip.get("id"))
                return True

        # Return / Enter key on selected item -> copy & paste
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            selected_row = self.list_box.get_selected_row()
            if selected_row and hasattr(selected_row, "clip"):
                self._select_clip(selected_row.clip)
                return True

        return False

    def _make_filter_handler(self, filter_key: str):
        def handler(button):
            self.set_filter(filter_key)
        return handler

    def set_filter(self, filter_key: str):
        self.current_filter = filter_key
        for k, (btn, _) in self._filter_buttons.items():
            if k == filter_key:
                btn.add_css_class("active")
            else:
                btn.remove_css_class("active")
        self.reload_history()

    def _on_search_changed(self, entry):
        self.current_query = entry.get_text()
        self.reload_history()

    def _set_search_placeholder(self, text: str):
        if hasattr(self.search_entry, "set_placeholder_text"):
            self.search_entry.set_placeholder_text(text)
        else:
            self.search_entry.set_property("placeholder-text", text)

    def _update_localized_texts(self):
        """Update all static labels when language is changed."""
        self.title_widget.set_subtitle(t("app_subtitle", self.lang))
        self._set_search_placeholder(t("search_placeholder", self.lang))
        self.settings_btn.set_tooltip_text(t("tooltip_settings", self.lang))
        self.clear_btn.set_tooltip_text(t("tooltip_clear", self.lang))
        self.pause_lbl.set_text(t("pause_banner_text", self.lang))
        self.resume_btn.set_label(t("pause_banner_resume", self.lang))
        self.empty_title.set_text(t("empty_title", self.lang))
        self.empty_desc.set_text(t("empty_desc", self.lang))
        self.hint_lbl.set_text(t("status_hint", self.lang))
        self._update_theme_btn_ui()

        for k, (btn, trans_key) in self._filter_buttons.items():
            btn.set_label(t(trans_key, self.lang))

    def _update_theme_btn_ui(self):
        sm = Adw.StyleManager.get_default()
        if sm.get_dark():
            self.theme_btn.set_icon_name("weather-clear-night-symbolic")
            self.theme_btn.set_tooltip_text(t("tooltip_theme_dark", self.lang))
        else:
            self.theme_btn.set_icon_name("display-brightness-symbolic")
            self.theme_btn.set_tooltip_text(t("tooltip_theme_light", self.lang))

    def _on_dark_changed(self, style_mgr, gparam):
        self._update_theme_btn_ui()

    def _on_toggle_theme(self, btn):
        new_mode = toggle_theme_mode(self.db)
        self._update_theme_btn_ui()
        toast_msg = t("toast_theme_dark" if new_mode == "dark" else "toast_theme_light", self.lang)
        self.show_toast(toast_msg)

    def reload_history(self):
        """Reload clips from SQLite and populate ListBox."""
        # Refresh current language
        self.lang = self.db.get_setting("language", "vi")
        self._update_localized_texts()

        try:
            max_limit = int(self.db.get_setting("max_history", "200"))
        except (ValueError, TypeError):
            max_limit = 200

        clips = self.db.get_clips(
            filter_type=self.current_filter,
            query=self.current_query,
            limit=max_limit
        )

        # Clear existing rows
        while True:
            row = self.list_box.get_row_at_index(0)
            if not row:
                break
            self.list_box.remove(row)

        if not clips:
            self.stack.set_visible_child_name("empty")
        else:
            self.stack.set_visible_child_name("list")
            for clip in clips:
                row = HistoryItemRow(
                    clip=clip,
                    on_select=self._select_clip,
                    on_pin=self._toggle_pin,
                    on_delete=self._delete_clip,
                    lang=self.lang
                )
                self.list_box.append(row)

            # Auto select first row
            first = self.list_box.get_row_at_index(0)
            if first:
                self.list_box.select_row(first)

        # Update stats
        stats = self.db.get_stats()
        self.status_lbl.set_text(t("status_total", self.lang, total=stats['total'], pinned=stats['pinned']))
        self._update_record_status_ui()

    def _update_record_status_ui(self):
        is_rec = self.clipboard_mgr.is_recording()
        if is_rec:
            self.record_btn.set_icon_name("media-record-symbolic")
            self.record_btn.set_tooltip_text(t("tooltip_record_on", self.lang))
            self.record_btn.remove_css_class("record-btn-paused")
            self.record_btn.add_css_class("record-btn-active")
            self.pause_banner.set_visible(False)
        else:
            self.record_btn.set_icon_name("media-playback-pause-symbolic")
            self.record_btn.set_tooltip_text(t("tooltip_record_off", self.lang))
            self.record_btn.remove_css_class("record-btn-active")
            self.record_btn.add_css_class("record-btn-paused")
            self.pause_banner.set_visible(True)

    def _on_toggle_record(self, btn):
        new_state = self.clipboard_mgr.toggle_recording()
        self._update_record_status_ui()
        if new_state:
            self.show_toast(t("toast_record_resumed", self.lang))
        else:
            self.show_toast(t("toast_record_paused", self.lang))

    def _on_row_activated(self, listbox, row):
        if row and hasattr(row, "clip"):
            self._select_clip(row.clip)

    def _select_clip(self, clip: Dict[str, Any]):
        """Copy selected clip back into clipboard and simulate paste."""
        self.clipboard_mgr.copy_to_clipboard(clip, auto_paste=True)
        self.hide()

    def _toggle_pin(self, clip_id: int):
        # Lấy content_hash trước khi toggle (cần để push unpin)
        clip = self.db.get_clip_by_id(clip_id)
        is_pinned = self.db.toggle_pin(clip_id)
        msg = t("toast_pinned", self.lang) if is_pinned else t("toast_unpinned", self.lang)
        self.show_toast(msg)
        self.reload_history()

        # Sync lên cloud nếu đã cấu hình
        if self.sync_mgr and clip:
            content_hash = clip.get("content_hash", "")
            if is_pinned:
                updated_clip = self.db.get_clip_by_id(clip_id) or clip
                self.sync_mgr.push_pin(updated_clip)
            else:
                self.sync_mgr.push_unpin(content_hash)

    def _delete_clip(self, clip_id: int):
        clip = self.db.get_clip_by_id(clip_id)
        is_pinned = clip.get("is_pinned", 0) if clip else 0
        content_hash = clip.get("content_hash", "") if clip else ""

        self.db.delete_clip(clip_id)
        self.show_toast(t("toast_deleted", self.lang))
        self.reload_history()

        if self.sync_mgr and is_pinned and content_hash:
            self.sync_mgr.push_unpin(content_hash)

    def _confirm_clear_unpinned(self, btn):
        deleted = self.db.clear_unpinned()
        self.show_toast(t("toast_cleared", self.lang, count=deleted))
        self.reload_history()

    def _open_settings(self, btn):
        dialog = SettingsDialog(
            self,
            self.db,
            on_settings_changed=self.reload_history,
            sync_mgr=self.sync_mgr,
        )
        dialog.present()

    def show_toast(self, message: str):
        toast = Adw.Toast.new(message)
        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)

    def toggle_visibility(self):
        """Toggle popup visibility and focus search input."""
        if self.get_visible():
            self.hide()
        else:
            self.reload_history()
            self.present()
            self.search_entry.grab_focus()

    def _on_close_request(self, window):
        self.hide()
        return True  # Prevent destroy, keep alive in background
