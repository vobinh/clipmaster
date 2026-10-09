"""
ClipMaster Set/Change PIN Dialog
Dialog allowing users to set or change their 4-digit PIN for Notes security.
"""

from typing import Callable, Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from ..i18n import t


class SetPinDialog(Adw.Window):
    def __init__(
        self,
        parent_window: Gtk.Window,
        has_existing_pin: bool,
        verify_current_cb: Optional[Callable[[str], bool]],
        on_pin_set: Callable[[str], None],
        lang: str = "vi",
    ):
        super().__init__()
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.lang = lang
        self.has_existing_pin = has_existing_pin
        self.verify_current_cb = verify_current_cb
        self.on_pin_set = on_pin_set

        title = t("pin_dlg_title_change" if has_existing_pin else "pin_dlg_title_set", self.lang)
        self.set_title(title)
        self.set_default_size(380, -1)
        self.set_resizable(False)

        self._build_ui(title)

    def _build_ui(self, title: str):
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # HeaderBar
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=title))

        cancel_btn = Gtk.Button(label=t("btn_cancel", self.lang))
        cancel_btn.connect("clicked", lambda _: self.close())
        header.pack_start(cancel_btn)

        self.save_btn = Gtk.Button(label=t("btn_save", self.lang) if self.lang == "vi" else "Save")
        self.save_btn.add_css_class("suggested-action")
        self.save_btn.connect("clicked", self._on_save_clicked)
        header.pack_end(self.save_btn)

        root_box.append(header)

        # Body
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        body.set_margin_top(20)
        body.set_margin_bottom(24)
        body.set_margin_start(24)
        body.set_margin_end(24)

        # Lock Icon header
        icon = Gtk.Image.new_from_icon_name("channel-secure-symbolic")
        icon.set_pixel_size(48)
        icon.add_css_class("pin-header-icon")
        body.append(icon)

        # Error label
        self.err_lbl = Gtk.Label()
        self.err_lbl.add_css_class("pin-error-lbl")
        self.err_lbl.set_visible(False)
        self.err_lbl.set_wrap(True)
        body.append(self.err_lbl)

        # 1. Current PIN (only if existing)
        if self.has_existing_pin:
            cur_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            lbl = Gtk.Label(label=t("pin_dlg_current", self.lang))
            lbl.set_halign(Gtk.Align.START)
            lbl.add_css_class("dim-label")
            cur_box.append(lbl)

            self.curr_entry = Gtk.PasswordEntry()
            self.curr_entry.set_placeholder_text("••••")
            self._restrict_4_digits(self.curr_entry)
            cur_box.append(self.curr_entry)
            body.append(cur_box)
        else:
            self.curr_entry = None

        # 2. New PIN
        new_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        lbl_new = Gtk.Label(label=t("pin_dlg_new", self.lang))
        lbl_new.set_halign(Gtk.Align.START)
        lbl_new.add_css_class("dim-label")
        new_box.append(lbl_new)

        self.new_entry = Gtk.PasswordEntry()
        self.new_entry.set_placeholder_text("••••")
        self._restrict_4_digits(self.new_entry)
        new_box.append(self.new_entry)
        body.append(new_box)

        # 3. Confirm PIN
        conf_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        lbl_conf = Gtk.Label(label=t("pin_dlg_confirm", self.lang))
        lbl_conf.set_halign(Gtk.Align.START)
        lbl_conf.add_css_class("dim-label")
        conf_box.append(lbl_conf)

        self.conf_entry = Gtk.PasswordEntry()
        self.conf_entry.set_placeholder_text("••••")
        self._restrict_4_digits(self.conf_entry)
        conf_box.append(self.conf_entry)
        body.append(conf_box)

        root_box.append(body)
        self.set_content(root_box)

        if self.curr_entry:
            self.curr_entry.grab_focus()
        else:
            self.new_entry.grab_focus()

    def _restrict_4_digits(self, entry: Gtk.PasswordEntry):
        def _on_changed(_e):
            txt = _e.get_text()
            clean = "".join(ch for ch in txt if ch.isdigit())[:4]
            if txt != clean:
                _e.set_text(clean)
        entry.connect("changed", _on_changed)

    def _show_error(self, msg: str):
        self.err_lbl.set_text(msg)
        self.err_lbl.set_visible(True)

    def _on_save_clicked(self, _btn):
        # 1. Verify current PIN if required
        if self.has_existing_pin and self.curr_entry:
            curr_val = self.curr_entry.get_text().strip()
            if not self.verify_current_cb or not self.verify_current_cb(curr_val):
                self._show_error(t("pin_dlg_err_current", self.lang))
                self.curr_entry.grab_focus()
                return

        # 2. Check new PIN
        new_val = self.new_entry.get_text().strip()
        if len(new_val) != 4 or not new_val.isdigit():
            self._show_error(t("pin_dlg_err_len", self.lang))
            self.new_entry.grab_focus()
            return

        # 3. Check confirm PIN
        conf_val = self.conf_entry.get_text().strip()
        if new_val != conf_val:
            self._show_error(t("pin_dlg_err_mismatch", self.lang))
            self.conf_entry.grab_focus()
            return

        # Success!
        self.on_pin_set(new_val)
        self.close()
