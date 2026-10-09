"""
ClipMaster Note Editor Dialog
Modal dialog for creating and editing personal notes.
"""

from typing import Callable, Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw

from ..i18n import t


class NoteEditorDialog(Adw.Window):
    def __init__(
        self,
        parent_window: Gtk.Window,
        on_saved: Callable[[str, str, Optional[int]], None],
        note_id: Optional[int] = None,
        initial_title: str = "",
        initial_content: str = "",
        lang: str = "vi",
    ):
        super().__init__()
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.lang = lang
        self.note_id = note_id
        self.on_saved = on_saved

        dlg_title = t("note_dialog_edit_title" if note_id else "note_dialog_new_title", self.lang)
        self.set_title(dlg_title)
        self.set_default_size(480, 440)

        self._build_ui(initial_title, initial_content)
        self._setup_shortcuts()

    def _build_ui(self, initial_title: str, initial_content: str):
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # HeaderBar
        header = Adw.HeaderBar()
        dlg_title = t("note_dialog_edit_title" if self.note_id else "note_dialog_new_title", self.lang)
        header.set_title_widget(Adw.WindowTitle(title=dlg_title))

        # Cancel Button
        cancel_btn = Gtk.Button(label=t("btn_cancel", self.lang))
        cancel_btn.connect("clicked", lambda _: self.close())
        header.pack_start(cancel_btn)

        # Save Button
        self.save_btn = Gtk.Button(label=t("btn_save_note", self.lang))
        self.save_btn.add_css_class("suggested-action")
        self.save_btn.connect("clicked", self._on_save_clicked)
        header.pack_end(self.save_btn)

        content_box.append(header)

        # Form Body
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        form_box.set_margin_top(16)
        form_box.set_margin_bottom(16)
        form_box.set_margin_start(16)
        form_box.set_margin_end(16)
        form_box.set_vexpand(True)

        # 1. Title Row
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title_lbl = Gtk.Label(label=t("note_title_label", self.lang))
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.add_css_class("dim-label")
        title_box.append(title_lbl)

        self.title_entry = Gtk.Entry()
        self.title_entry.set_placeholder_text(t("note_title_placeholder", self.lang))
        if initial_title:
            self.title_entry.set_text(initial_title)
        title_box.append(self.title_entry)
        form_box.append(title_box)

        # 2. Content Row
        content_field_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_field_box.set_vexpand(True)

        content_lbl = Gtk.Label(label=t("note_content_label", self.lang))
        content_lbl.set_halign(Gtk.Align.START)
        content_lbl.add_css_class("dim-label")
        content_field_box.append(content_lbl)

        # Frame for TextView
        text_frame = Gtk.Frame()
        text_frame.set_vexpand(True)
        text_frame.add_css_class("note-text-frame")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_vexpand(True)
        self.text_view.set_left_margin(12)
        self.text_view.set_right_margin(12)
        self.text_view.set_top_margin(10)
        self.text_view.set_bottom_margin(10)

        self.text_buffer = self.text_view.get_buffer()
        if initial_content:
            self.text_buffer.set_text(initial_content)
        self.text_buffer.connect("changed", self._on_buffer_changed)

        scrolled.set_child(self.text_view)
        text_frame.set_child(scrolled)
        content_field_box.append(text_frame)

        # Shortcut hint
        hint_lbl = Gtk.Label(label="Ctrl + Enter: Lưu  •  Esc: Hủy" if self.lang == "vi" else "Ctrl + Enter: Save  •  Esc: Cancel")
        hint_lbl.set_halign(Gtk.Align.END)
        hint_lbl.add_css_class("dim-label")
        hint_lbl.add_css_class("caption")
        content_field_box.append(hint_lbl)

        form_box.append(content_field_box)
        content_box.append(form_box)

        self.set_content(content_box)
        self._update_save_sensitivity()

        # Focus: focus content if title already exists, otherwise focus title
        if initial_title:
            self.text_view.grab_focus()
        else:
            self.title_entry.grab_focus()

    def _on_buffer_changed(self, buffer):
        self._update_save_sensitivity()

    def _update_save_sensitivity(self):
        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()
        text = self.text_buffer.get_text(start_iter, end_iter, False).strip()
        self.save_btn.set_sensitive(len(text) > 0)

    def _setup_shortcuts(self):
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True

        if (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if self.save_btn.get_sensitive():
                self._on_save_clicked(self.save_btn)
            return True

        return False

    def _on_save_clicked(self, _btn):
        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()
        content = self.text_buffer.get_text(start_iter, end_iter, False).strip()
        if not content:
            return

        title = self.title_entry.get_text().strip()
        self.on_saved(title, content, self.note_id)
        self.close()
