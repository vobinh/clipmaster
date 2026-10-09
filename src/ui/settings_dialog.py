"""
ClipMaster Settings Dialog
Preferences configuration for shortcuts, autostart, history limits, and language.
"""

from typing import Callable

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from ..database import Database
from ..shortcut_manager import (
    get_current_shortcut,
    set_custom_shortcut,
    remove_super_v_shortcut,
    format_shortcut_display,
    is_shortcut_installed,
    is_autostart_enabled,
    setup_autostart,
    POPULAR_SHORTCUTS
)
from ..i18n import t, AVAILABLE_LANGUAGES
from ..theme_manager import apply_theme_mode, THEME_MODES
from ..sync_manager import SyncManager
from .shortcut_dialog import ShortcutRecordDialog
from .sync_setup_dialog import SyncSetupDialog
from .pin_dialog import SetPinDialog


class SettingsDialog(Adw.PreferencesWindow):
    def __init__(
        self,
        parent_window: Gtk.Window,
        db: Database,
        on_settings_changed: Callable,
        sync_mgr: SyncManager = None,
    ):
        super().__init__()
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_default_size(500, 580)

        self.db = db
        self.on_settings_changed = on_settings_changed
        self.sync_mgr = sync_mgr
        self.lang = self.db.get_setting("language", "vi")
        self._updating_combo = False
        self._updating_lang = False
        self._updating_theme = False
        self._updating_limit = False
        self._updating_sync_dir = False
        self._updating_pin_switch = False
        self._updating_pin_timeout = False

        self._build_ui()
        self._update_localized_texts()

    def _build_ui(self):
        # Only create a single page once
        self.page = Adw.PreferencesPage()
        self.page.set_icon_name("preferences-system-symbolic")

        # --- Group 0: Giao diện / Appearance & Theme ---
        self.group_appearance = Adw.PreferencesGroup()

        self.theme_row = Adw.ComboRow()
        self._updating_theme = True
        theme_names = [t(k, self.lang) for _, k in THEME_MODES]
        self.theme_row.set_model(Gtk.StringList.new(theme_names))
        cur_theme = self.db.get_setting("theme_mode", "dark")
        theme_indices = {"system": 0, "dark": 1, "light": 2}
        self.theme_row.set_selected(theme_indices.get(cur_theme, 1))
        self._updating_theme = False
        self.theme_row.connect("notify::selected", self._on_theme_changed)

        self.group_appearance.add(self.theme_row)
        self.page.add(self.group_appearance)

        # --- Group 1: Ngôn ngữ / Language ---
        self.group_lang = Adw.PreferencesGroup()

        self.lang_row = Adw.ComboRow()
        lang_model = Gtk.StringList.new([name for _, name in AVAILABLE_LANGUAGES])
        self.lang_row.set_model(lang_model)

        self._updating_lang = True
        self.lang_row.set_selected(1 if self.lang == "en" else 0)
        self._updating_lang = False
        self.lang_row.connect("notify::selected", self._on_language_changed)

        self.group_lang.add(self.lang_row)
        self.page.add(self.group_lang)

        # --- Group 1: Phím tắt hệ thống ---
        self.group_shortcut = Adw.PreferencesGroup()

        # Current Shortcut Row
        self.shortcut_row = Adw.ActionRow()

        # Change button
        self.change_shortcut_btn = Gtk.Button()
        self.change_shortcut_btn.add_css_class("suggested-action")
        self.change_shortcut_btn.set_valign(Gtk.Align.CENTER)
        self.change_shortcut_btn.connect("clicked", self._open_shortcut_record_dialog)
        self.shortcut_row.add_suffix(self.change_shortcut_btn)

        self.group_shortcut.add(self.shortcut_row)

        # Quick Preset ComboRow
        self.preset_row = Adw.ComboRow()
        self.preset_row.connect("notify::selected", self._on_preset_selected)

        self.group_shortcut.add(self.preset_row)
        self.page.add(self.group_shortcut)

        # --- Group 2: Trải nghiệm & Tác vụ ---
        self.group_behavior = Adw.PreferencesGroup()

        # Auto Record Switch (Tự động ghi nhớ)
        self.auto_record_row = Adw.ActionRow()
        self.auto_record_switch = Gtk.Switch()
        self.auto_record_switch.set_valign(Gtk.Align.CENTER)
        self.auto_record_switch.set_active(self.db.get_setting("auto_record", "1") == "1")
        self.auto_record_switch.connect("notify::active", self._on_auto_record_toggled)
        self.auto_record_row.add_suffix(self.auto_record_switch)
        self.group_behavior.add(self.auto_record_row)

        # Auto Paste Switch
        self.auto_paste_row = Adw.ActionRow()
        self.auto_paste_switch = Gtk.Switch()
        self.auto_paste_switch.set_valign(Gtk.Align.CENTER)
        self.auto_paste_switch.set_active(self.db.get_setting("auto_paste", "1") == "1")
        self.auto_paste_switch.connect("notify::active", self._on_auto_paste_toggled)
        self.auto_paste_row.add_suffix(self.auto_paste_switch)
        self.group_behavior.add(self.auto_paste_row)

        # Save Images Switch
        self.images_row = Adw.ActionRow()
        self.images_switch = Gtk.Switch()
        self.images_switch.set_valign(Gtk.Align.CENTER)
        self.images_switch.set_active(self.db.get_setting("save_images", "1") == "1")
        self.images_switch.connect("notify::active", self._on_save_images_toggled)
        self.images_row.add_suffix(self.images_switch)
        self.group_behavior.add(self.images_row)

        # Autostart on boot
        self.autostart_row = Adw.ActionRow()
        self.autostart_switch = Gtk.Switch()
        self.autostart_switch.set_valign(Gtk.Align.CENTER)
        self.autostart_switch.set_active(is_autostart_enabled())
        self.autostart_switch.connect("notify::active", self._on_autostart_toggled)
        self.autostart_row.add_suffix(self.autostart_switch)
        self.group_behavior.add(self.autostart_row)

        self.page.add(self.group_behavior)

        # --- Group 3: Giới hạn lưu trữ ---
        self.group_storage = Adw.PreferencesGroup()

        self.limit_row = Adw.ComboRow()
        self.limit_row.connect("notify::selected", self._on_limit_changed)
        self.group_storage.add(self.limit_row)

        self.page.add(self.group_storage)

        # --- Group 3.5: Bảo mật Ghi chú / Notes Security ---
        self.group_notes_sec = Adw.PreferencesGroup()

        self.pin_enable_row = Adw.ActionRow()
        self.pin_switch = Gtk.Switch()
        self.pin_switch.set_valign(Gtk.Align.CENTER)
        self.pin_switch.set_active(self.db.is_notes_pin_enabled())
        self.pin_switch.connect("notify::active", self._on_pin_switch_toggled)
        self.pin_enable_row.add_suffix(self.pin_switch)
        self.group_notes_sec.add(self.pin_enable_row)

        self.pin_change_row = Adw.ActionRow()
        self.change_pin_btn = Gtk.Button()
        self.change_pin_btn.set_valign(Gtk.Align.CENTER)
        self.change_pin_btn.connect("clicked", self._on_change_pin_clicked)
        self.pin_change_row.add_suffix(self.change_pin_btn)
        self.group_notes_sec.add(self.pin_change_row)

        self.pin_timeout_row = Adw.ComboRow()
        self.pin_timeout_row.connect("notify::selected", self._on_pin_timeout_changed)
        self.group_notes_sec.add(self.pin_timeout_row)

        self.page.add(self.group_notes_sec)

        # --- Group 4: Đồng bộ đám mây (BYOS Sync) ---
        self.group_sync = Adw.PreferencesGroup()

        # Trạng thái kết nối
        self.sync_status_row = Adw.ActionRow()
        self.sync_status_lbl = Gtk.Label()
        self.sync_status_lbl.set_valign(Gtk.Align.CENTER)
        self.sync_status_row.add_suffix(self.sync_status_lbl)
        self.group_sync.add(self.sync_status_row)

        # URL đang kết nối
        self.sync_url_row = Adw.ActionRow()
        self.group_sync.add(self.sync_url_row)

        # Hướng đồng bộ
        self.sync_direction_row = Adw.ComboRow()
        self.sync_direction_row.connect("notify::selected", self._on_sync_direction_changed)
        self.group_sync.add(self.sync_direction_row)

        # Nút hành động
        sync_btn_row = Adw.ActionRow()
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_valign(Gtk.Align.CENTER)

        self.sync_setup_btn = Gtk.Button()
        self.sync_setup_btn.add_css_class("suggested-action")
        self.sync_setup_btn.connect("clicked", self._on_sync_setup)
        btn_box.append(self.sync_setup_btn)

        self.sync_now_btn = Gtk.Button()
        self.sync_now_btn.connect("clicked", self._on_sync_now)
        btn_box.append(self.sync_now_btn)

        self.sync_disconnect_btn = Gtk.Button()
        self.sync_disconnect_btn.add_css_class("destructive-action")
        self.sync_disconnect_btn.connect("clicked", self._on_sync_disconnect)
        btn_box.append(self.sync_disconnect_btn)

        sync_btn_row.add_suffix(btn_box)
        self.group_sync.add(sync_btn_row)

        self.page.add(self.group_sync)

        # --- Group 5: Vùng nguy hiểm ---
        self.group_danger = Adw.PreferencesGroup()

        self.clear_all_row = Adw.ActionRow()
        self.clear_btn = Gtk.Button()
        self.clear_btn.add_css_class("destructive-action")
        self.clear_btn.set_valign(Gtk.Align.CENTER)
        self.clear_btn.connect("clicked", self._on_clear_unpinned)
        self.clear_all_row.add_suffix(self.clear_btn)
        self.group_danger.add(self.clear_all_row)

        self.page.add(self.group_danger)

        self.add(self.page)

    def _update_localized_texts(self):
        """Update all labels and descriptions in place without adding new pages/tabs."""
        self.set_title(t("settings_title", self.lang))
        self.page.set_title(t("page_general", self.lang))

        # Appearance Group
        self.group_appearance.set_title(t("group_appearance", self.lang))
        self.theme_row.set_title(t("row_theme", self.lang))
        self.theme_row.set_subtitle(t("row_theme_sub", self.lang))
        self._updating_theme = True
        theme_names = [t(k, self.lang) for _, k in THEME_MODES]
        cur_theme_sel = self.theme_row.get_selected()
        self.theme_row.set_model(Gtk.StringList.new(theme_names))
        self.theme_row.set_selected(cur_theme_sel)
        self._updating_theme = False

        # Language Group
        self.group_lang.set_title(t("group_language", self.lang))
        self.lang_row.set_title(t("row_language", self.lang))
        self.lang_row.set_subtitle(t("row_language_sub", self.lang))

        # Shortcut Group
        self.group_shortcut.set_title(t("group_shortcut", self.lang))
        self.group_shortcut.set_description(t("group_shortcut_desc", self.lang))
        self.shortcut_row.set_title(t("row_active_shortcut", self.lang))
        self.change_shortcut_btn.set_label(t("btn_change_shortcut", self.lang))
        self._update_shortcut_row_subtitle()

        self.preset_row.set_title(t("row_preset", self.lang))
        self.preset_row.set_subtitle(t("row_preset_sub", self.lang))

        # Update preset options
        self._updating_combo = True
        preset_labels = [label for _, label in POPULAR_SHORTCUTS] + [t("custom_option", self.lang)]
        self.preset_row.set_model(Gtk.StringList.new(preset_labels))
        self._sync_preset_selection()
        self._updating_combo = False

        # Behavior Group
        self.group_behavior.set_title(t("group_behavior", self.lang))
        self.auto_record_row.set_title(t("row_auto_record", self.lang))
        self.auto_record_row.set_subtitle(t("row_auto_record_sub", self.lang))
        self.auto_paste_row.set_title(t("row_auto_paste", self.lang))
        self.auto_paste_row.set_subtitle(t("row_auto_paste_sub", self.lang))
        self.images_row.set_title(t("row_save_images", self.lang))
        self.images_row.set_subtitle(t("row_save_images_sub", self.lang))
        self.autostart_row.set_title(t("row_autostart", self.lang))
        self.autostart_row.set_subtitle(t("row_autostart_sub", self.lang))

        # Storage Group
        self.group_storage.set_title(t("group_storage", self.lang))
        self.limit_row.set_title(t("row_max_items", self.lang))
        self.limit_row.set_subtitle(t("row_max_items_sub", self.lang))
        unit = "items" if self.lang == "en" else "mục"
        limit_options = [f"50 {unit}", f"100 {unit}", f"200 {unit}", f"500 {unit}", f"1000 {unit}"]
        cur_limit = self.db.get_setting("max_history", "200")
        mapping = {"50": 0, "100": 1, "200": 2, "500": 3, "1000": 4}
        target_idx = mapping.get(str(cur_limit), 2)

        self._updating_limit = True
        self.limit_row.set_model(Gtk.StringList.new(limit_options))
        self.limit_row.set_selected(target_idx)
        self._updating_limit = False

        # Danger Group
        self.group_danger.set_title(t("group_danger", self.lang))
        self.clear_all_row.set_title(t("row_clear_all", self.lang))
        self.clear_all_row.set_subtitle(t("row_clear_all_sub", self.lang))
        self.clear_btn.set_label(t("btn_clear_now", self.lang))

        # Notes Security Group
        self._update_notes_sec_group()

        # Sync Group
        self._update_sync_group()

    def _on_theme_changed(self, combo, gparam):
        if self._updating_theme:
            return
        idx = combo.get_selected()
        if 0 <= idx < len(THEME_MODES):
            new_mode = THEME_MODES[idx][0]
            self.db.set_setting("theme_mode", new_mode)
            apply_theme_mode(new_mode)
            if self.on_settings_changed:
                self.on_settings_changed()

    def _on_language_changed(self, combo, gparam):
        if self._updating_lang:
            return
        idx = combo.get_selected()
        new_lang = AVAILABLE_LANGUAGES[idx][0] if 0 <= idx < len(AVAILABLE_LANGUAGES) else "vi"
        if new_lang != self.lang:
            self.lang = new_lang
            self.db.set_setting("language", new_lang)
            # Update all labels in place without touching pages or tabs!
            self._update_localized_texts()
            self.on_settings_changed()

    def _update_shortcut_row_subtitle(self):
        current = get_current_shortcut() or self.db.get_setting("shortcut", "<Super>v")
        if current:
            disp = format_shortcut_display(current)
            lbl = "Shortcut" if self.lang == "en" else "Tổ hợp phím"
            disp_esc = GLib.markup_escape_text(disp)
            cur_esc = GLib.markup_escape_text(current)
            self.shortcut_row.set_subtitle(f"{lbl}: {disp_esc} ({cur_esc})")
        else:
            self.shortcut_row.set_subtitle("Not configured" if self.lang == "en" else "Chưa được kích hoạt")

    def _sync_preset_selection(self):
        self._updating_combo = True
        current = get_current_shortcut() or self.db.get_setting("shortcut", "<Super>v")
        matched = False
        for idx, (key, _) in enumerate(POPULAR_SHORTCUTS):
            if key.lower() == current.lower():
                self.preset_row.set_selected(idx)
                matched = True
                break
        if not matched:
            self.preset_row.set_selected(len(POPULAR_SHORTCUTS))
        self._updating_combo = False

    def _on_preset_selected(self, combo, gparam):
        if self._updating_combo:
            return
        idx = combo.get_selected()
        if idx < len(POPULAR_SHORTCUTS):
            key, label = POPULAR_SHORTCUTS[idx]
            self._apply_new_shortcut(key)
        else:
            self._open_shortcut_record_dialog(None)

    def _open_shortcut_record_dialog(self, btn):
        current = get_current_shortcut() or self.db.get_setting("shortcut", "<Super>v")
        dialog = ShortcutRecordDialog(
            parent_window=self,
            current_shortcut=current,
            on_saved=self._apply_new_shortcut,
            lang=self.lang
        )
        dialog.present()

    def _apply_new_shortcut(self, shortcut_str: str):
        set_custom_shortcut(shortcut_str)
        self.db.set_setting("shortcut", shortcut_str)
        self._update_shortcut_row_subtitle()
        self._sync_preset_selection()
        if self.on_settings_changed:
            self.on_settings_changed()

    def _on_auto_record_toggled(self, switch, gparam):
        val = "1" if switch.get_active() else "0"
        self.db.set_setting("auto_record", val)
        self.on_settings_changed()

    def _on_auto_paste_toggled(self, switch, gparam):
        val = "1" if switch.get_active() else "0"
        self.db.set_setting("auto_paste", val)
        self.on_settings_changed()

    def _on_save_images_toggled(self, switch, gparam):
        val = "1" if switch.get_active() else "0"
        self.db.set_setting("save_images", val)
        self.on_settings_changed()

    def _on_autostart_toggled(self, switch, gparam):
        setup_autostart(switch.get_active())

    def _on_limit_changed(self, combo, gparam):
        if self._updating_limit:
            return
        vals = ["50", "100", "200", "500", "1000"]
        idx = combo.get_selected()
        if 0 <= idx < len(vals):
            self.db.set_setting("max_history", vals[idx])
            if self.on_settings_changed:
                self.on_settings_changed()

    def _on_clear_unpinned(self, btn):
        self.db.clear_unpinned()
        self.on_settings_changed()

    def _on_sync_direction_changed(self, combo, gparam):
        if self._updating_sync_dir:
            return
        vals = ["both", "download_only", "upload_only"]
        idx = combo.get_selected()
        if 0 <= idx < len(vals):
            new_dir = vals[idx]
            self.db.set_setting("sync_direction", new_dir)
            if self.on_settings_changed:
                self.on_settings_changed()

    # ─── Notes Security Group ────────────────────

    def _update_notes_sec_group(self):
        """Cập nhật giao diện nhóm bảo mật ghi chú."""
        self.group_notes_sec.set_title(t("group_notes_sec", self.lang))
        self.pin_enable_row.set_title(t("row_pin_enable", self.lang))
        self.pin_enable_row.set_subtitle(t("row_pin_enable_sub", self.lang))

        is_enabled = self.db.is_notes_pin_enabled()
        self._updating_pin_switch = True
        self.pin_switch.set_active(is_enabled)
        self._updating_pin_switch = False

        self.pin_change_row.set_title(t("row_pin_change", self.lang))
        self.pin_change_row.set_subtitle(t("row_pin_change_sub", self.lang))
        self.change_pin_btn.set_label(t("btn_change_pin", self.lang))
        self.pin_change_row.set_visible(is_enabled)

        self.pin_timeout_row.set_title(t("row_pin_timeout", self.lang))
        self.pin_timeout_row.set_subtitle(t("row_pin_timeout_sub", self.lang))
        self.pin_timeout_row.set_visible(is_enabled)

        timeout_options = [
            t("pin_timeout_0", self.lang),
            t("pin_timeout_60", self.lang),
            t("pin_timeout_300", self.lang),
            t("pin_timeout_900", self.lang),
            t("pin_timeout_1800", self.lang),
            t("pin_timeout_close", self.lang),
        ]
        cur_timeout = self.db.get_setting("notes_pin_timeout", "300")
        timeout_map = {"0": 0, "60": 1, "300": 2, "900": 3, "1800": 4, "on_close": 5}
        target_idx = timeout_map.get(str(cur_timeout), 2)

        self._updating_pin_timeout = True
        self.pin_timeout_row.set_model(Gtk.StringList.new(timeout_options))
        self.pin_timeout_row.set_selected(target_idx)
        self._updating_pin_timeout = False

    def _on_pin_switch_toggled(self, switch, gparam):
        if self._updating_pin_switch:
            return
        active = switch.get_active()
        if active:
            # Nếu chưa có mã PIN hash trong DB, mở dialog tạo mới
            has_hash = bool(self.db.get_setting("notes_pin_hash", "").strip())
            if has_hash:
                self.db.set_setting("notes_pin_enabled", "1")
                self._update_notes_sec_group()
                self._show_toast(t("toast_pin_enabled", self.lang))
                if self.on_settings_changed:
                    self.on_settings_changed()
            else:
                def _on_set(new_pin: str):
                    self.db.set_notes_pin(new_pin)
                    self._update_notes_sec_group()
                    self._show_toast(t("toast_pin_enabled", self.lang))
                    if self.on_settings_changed:
                        self.on_settings_changed()

                dlg = SetPinDialog(
                    parent_window=self,
                    has_existing_pin=False,
                    verify_current_cb=None,
                    on_pin_set=_on_set,
                    lang=self.lang,
                )
                def _on_close_check(_widget):
                    if not self.db.is_notes_pin_enabled():
                        self._updating_pin_switch = True
                        self.pin_switch.set_active(False)
                        self._updating_pin_switch = False
                dlg.connect("destroy", _on_close_check)
                dlg.present()
        else:
            self.db.disable_notes_pin()
            self._update_notes_sec_group()
            self._show_toast(t("toast_pin_disabled", self.lang))
            if self.on_settings_changed:
                self.on_settings_changed()

    def _on_change_pin_clicked(self, _btn):
        def _on_pin_changed(new_pin: str):
            self.db.set_notes_pin(new_pin)
            self._show_toast(t("toast_pin_changed", self.lang))
            if self.on_settings_changed:
                self.on_settings_changed()

        dlg = SetPinDialog(
            parent_window=self,
            has_existing_pin=True,
            verify_current_cb=self.db.verify_notes_pin,
            on_pin_set=_on_pin_changed,
            lang=self.lang,
        )
        dlg.present()

    def _on_pin_timeout_changed(self, combo, gparam):
        if self._updating_pin_timeout:
            return
        vals = ["0", "60", "300", "900", "1800", "on_close"]
        idx = combo.get_selected()
        if 0 <= idx < len(vals):
            self.db.set_setting("notes_pin_timeout", vals[idx])
            if self.on_settings_changed:
                self.on_settings_changed()

    def _show_toast(self, message: str, timeout: int = 2):
        toast = Adw.Toast(title=message)
        toast.set_timeout(timeout)
        self.add_toast(toast)

    # ─── Sync Group ──────────────────────────────

    def _update_sync_group(self):
        """Cập nhật UI của group sync dựa trên trạng thái kết nối."""
        self.group_sync.set_title(t("group_sync", self.lang))
        self.group_sync.set_description(t("group_sync_desc", self.lang))
        self.sync_status_row.set_title(t("row_sync_status", self.lang))

        is_connected = self.sync_mgr is not None and self.sync_mgr.is_configured()

        if is_connected:
            url = self.sync_mgr.get_configured_url() or ""
            self.sync_status_lbl.set_markup(
                f'<span foreground="#4CAF50">{t("row_sync_status_connected", self.lang)}</span>'
            )
            self.sync_url_row.set_title(t("row_sync_url", self.lang))
            self.sync_url_row.set_subtitle(url)
            self.sync_url_row.set_visible(True)

            # Cập nhật dòng chọn hướng đồng bộ
            self.sync_direction_row.set_title(t("row_sync_direction", self.lang))
            self.sync_direction_row.set_subtitle(t("row_sync_direction_sub", self.lang))
            dir_options = [
                t("sync_dir_both", self.lang),
                t("sync_dir_download", self.lang),
                t("sync_dir_upload", self.lang),
            ]
            cur_dir = self.db.get_setting("sync_direction", "both")
            dir_map = {"both": 0, "download_only": 1, "upload_only": 2}
            target_dir_idx = dir_map.get(cur_dir, 0)

            self._updating_sync_dir = True
            self.sync_direction_row.set_model(Gtk.StringList.new(dir_options))
            self.sync_direction_row.set_selected(target_dir_idx)
            self._updating_sync_dir = False
            self.sync_direction_row.set_visible(True)

            self.sync_now_btn.set_visible(True)
            self.sync_disconnect_btn.set_visible(True)
            self.sync_setup_btn.set_label(t("btn_sync_setup", self.lang))
        else:
            self.sync_status_lbl.set_markup(
                f'<span foreground="#9E9E9E">{t("row_sync_status_disconnected", self.lang)}</span>'
            )
            self.sync_url_row.set_visible(False)
            self.sync_direction_row.set_visible(False)
            self.sync_now_btn.set_visible(False)
            self.sync_disconnect_btn.set_visible(False)
            self.sync_setup_btn.set_label(t("btn_sync_setup", self.lang))

        self.sync_setup_btn.set_label(t("btn_sync_setup", self.lang))
        self.sync_now_btn.set_label(t("btn_sync_now", self.lang))
        self.sync_disconnect_btn.set_label(t("btn_sync_disconnect", self.lang))

    def _on_sync_setup(self, _btn):
        """Mở dialog cấu hình BYOS Sync."""
        if not self.sync_mgr:
            return
        dialog = SyncSetupDialog(
            parent_window=self,
            sync_mgr=self.sync_mgr,
            lang=self.lang,
            on_connected=self._on_sync_connected,
        )
        dialog.present()

    def _on_sync_connected(self):
        """Callback sau khi cấu hình sync thành công."""
        self._update_sync_group()
        # Toast thông báo
        toast = Adw.Toast(title=t("toast_sync_done", self.lang))
        toast.set_timeout(2)
        self.add_toast(toast)

    def _on_sync_now(self, _btn):
        """Kích hoạt đồng bộ thủ công ngay lập tức."""
        if not self.sync_mgr:
            return
        self.sync_now_btn.set_sensitive(False)

        def _done(success: bool = True, msg: str = ""):
            from gi.repository import GLib
            def _ui():
                self.sync_now_btn.set_sensitive(True)
                if success:
                    title = t("toast_sync_done", self.lang)
                    timeout = 2
                else:
                    if "RLS" in msg or "row-level security" in msg.lower():
                        title = (
                            "⚠️ Lỗi RLS: Supabase đang chặn ghi. Cần tạo Policy."
                            if self.lang == "vi"
                            else "⚠️ RLS Error: Supabase blocked writes. Policy needed."
                        )
                    else:
                        title = f"❌ {msg[:60]}"
                    timeout = 4
                toast = Adw.Toast(title=title)
                toast.set_timeout(timeout)
                self.add_toast(toast)
                self.on_settings_changed()
            GLib.idle_add(_ui)

        self.sync_mgr.run_startup_sync_async(on_done=_done)

    def _on_sync_disconnect(self, _btn):
        """Ngắt kết nối và xóa config."""
        if not self.sync_mgr:
            return
        self.sync_mgr.config.clear()
        self.sync_mgr._reset_client()
        self._update_sync_group()
        toast = Adw.Toast(title=t("toast_sync_disconnected", self.lang))
        toast.set_timeout(2)
        self.add_toast(toast)

