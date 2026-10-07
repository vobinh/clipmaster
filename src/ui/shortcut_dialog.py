"""
ClipMaster Shortcut Dialog
Interactive keyboard shortcut recorder and custom editor.
"""

from typing import Callable, Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw

from ..shortcut_manager import format_shortcut_display
from ..i18n import t


class ShortcutRecordDialog(Adw.Window):
    def __init__(
        self,
        parent_window: Gtk.Window,
        current_shortcut: str,
        on_saved: Callable[[str], None],
        lang: str = "vi"
    ):
        super().__init__()
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.lang = lang
        self.set_title(t("shortcut_dlg_title", self.lang))
        self.set_default_size(420, 360)
        self.set_resizable(False)

        self.current_shortcut = current_shortcut or "<Super>v"
        self.detected_accel = self.current_shortcut
        self.on_saved = on_saved

        self._build_ui()
        self._setup_key_listener()

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)

        # Header Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_lbl = Gtk.Label(label=t("shortcut_dlg_header", self.lang))
        title_lbl.add_css_class("title-2")
        title_box.append(title_lbl)

        desc_lbl = Gtk.Label(label=t("shortcut_dlg_desc", self.lang))
        desc_lbl.set_justify(Gtk.Justification.CENTER)
        desc_lbl.add_css_class("dim-label")
        title_box.append(desc_lbl)
        main_box.append(title_box)

        # Big Key Badge Box (Interactive visual display)
        self.badge_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.badge_box.set_halign(Gtk.Align.CENTER)
        self.badge_box.set_valign(Gtk.Align.CENTER)
        self.badge_box.set_margin_top(8)
        self.badge_box.set_margin_bottom(8)

        self.key_label = Gtk.Label(label=format_shortcut_display(self.current_shortcut))
        self.key_label.add_css_class("title-1")
        self.key_label.add_css_class("accent")
        self.badge_box.append(self.key_label)

        self.raw_accel_label = Gtk.Label(label=t("shortcut_dlg_accel_label", self.lang, code=self.current_shortcut))
        self.raw_accel_label.add_css_class("caption")
        self.raw_accel_label.add_css_class("dim-label")
        self.badge_box.append(self.raw_accel_label)

        main_box.append(self.badge_box)

        # Manual Entry Box
        entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        entry_lbl = Gtk.Label(label=t("shortcut_dlg_manual", self.lang))
        entry_lbl.set_halign(Gtk.Align.START)
        entry_box.append(entry_lbl)

        self.entry = Gtk.Entry()
        self.entry.set_text(self.current_shortcut)
        self.entry.connect("changed", self._on_entry_changed)
        entry_box.append(self.entry)
        main_box.append(entry_box)

        # Quick Preset Buttons
        presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        presets_box.set_halign(Gtk.Align.CENTER)

        default_btn = Gtk.Button(label=t("btn_default_win_v", self.lang))
        default_btn.connect("clicked", lambda b: self._set_accel("<Super>v"))
        presets_box.append(default_btn)

        ctrl_alt_btn = Gtk.Button(label="Ctrl+Alt+V")
        ctrl_alt_btn.connect("clicked", lambda b: self._set_accel("<Control><Alt>v"))
        presets_box.append(ctrl_alt_btn)

        ctrl_shift_btn = Gtk.Button(label="Ctrl+Shift+V")
        ctrl_shift_btn.connect("clicked", lambda b: self._set_accel("<Control><Shift>v"))
        presets_box.append(ctrl_shift_btn)

        main_box.append(presets_box)

        # Bottom Action Buttons
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        actions_box.set_halign(Gtk.Align.END)
        actions_box.set_margin_top(12)

        cancel_btn = Gtk.Button(label=t("btn_cancel", self.lang))
        cancel_btn.connect("clicked", lambda b: self.close())
        actions_box.append(cancel_btn)

        self.save_btn = Gtk.Button(label=t("btn_save", self.lang))
        self.save_btn.add_css_class("suggested-action")
        self.save_btn.connect("clicked", self._on_save_clicked)
        actions_box.append(self.save_btn)

        main_box.append(actions_box)

        self.set_content(main_box)

        main_box.append(actions_box)

        self.set_content(main_box)

    def _setup_key_listener(self):
        controller = Gtk.EventControllerKey.new()
        controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(controller)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        # Esc -> close dialog
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True

        # Enter inside manual text entry is handled by entry
        if self.entry.has_focus():
            return False

        # If Enter outside entry -> Save
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self._on_save_clicked(self.save_btn)
            return True

        # Ignore standalone modifier keypresses
        if keyval in (
            Gdk.KEY_Shift_L, Gdk.KEY_Shift_R,
            Gdk.KEY_Control_L, Gdk.KEY_Control_R,
            Gdk.KEY_Alt_L, Gdk.KEY_Alt_R,
            Gdk.KEY_Super_L, Gdk.KEY_Super_R,
            Gdk.KEY_Meta_L, Gdk.KEY_Meta_R
        ):
            return False

        # Filter modifier masks
        mods = state & (
            Gdk.ModifierType.CONTROL_MASK
            | Gdk.ModifierType.ALT_MASK
            | Gdk.ModifierType.SUPER_MASK
            | Gdk.ModifierType.SHIFT_MASK
        )

        accel = Gtk.accelerator_name(keyval, mods)
        if accel:
            self._set_accel(accel)
            return True

        return False

    def _set_accel(self, accel: str):
        self.detected_accel = accel
        self.entry.set_text(accel)
        self.key_label.set_text(format_shortcut_display(accel))
        self.raw_accel_label.set_text(f"Mã hệ thống: {accel}")

    def _on_entry_changed(self, entry):
        val = entry.get_text().strip()
        ok, keyval, mods = Gtk.accelerator_parse(val)
        if ok or val == "":
            self.detected_accel = val
            self.key_label.set_text(format_shortcut_display(val))
            self.raw_accel_label.set_text(f"Mã hệ thống: {val}")
            self.save_btn.set_sensitive(True)
        else:
            self.key_label.set_text("Phím tắt không hợp lệ")
            self.save_btn.set_sensitive(False)

    def _on_save_clicked(self, btn):
        accel = self.detected_accel.strip()
        if accel:
            self.on_saved(accel)
        self.close()
