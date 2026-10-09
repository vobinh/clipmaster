"""
ClipMaster Note Item Row
Component rendering each personal note card with title, content preview, and action buttons.
"""

from typing import Callable, Dict, Any

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Pango

from ..utils import format_relative_time, truncate_text
from ..i18n import t


class NoteItemRow(Gtk.ListBoxRow):
    def __init__(
        self,
        note: Dict[str, Any],
        on_select: Callable[[Dict[str, Any]], None],
        on_edit: Callable[[Dict[str, Any]], None],
        on_pin: Callable[[int], None],
        on_delete: Callable[[int], None],
        lang: str = "vi",
    ):
        super().__init__()
        self.note = note
        self.on_select = on_select
        self.on_edit = on_edit
        self.on_pin = on_pin
        self.on_delete = on_delete
        self.lang = lang

        self.set_activatable(True)
        self.set_selectable(True)
        self._build_ui()

    def _build_ui(self):
        is_pinned = bool(self.note.get("is_pinned", 0))
        updated_at = self.note.get("updated_at", self.note.get("created_at", 0))
        title = (self.note.get("title") or "").strip()
        content = (self.note.get("content") or "").strip()

        # Main Card Container
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.add_css_class("clip-card")
        card.add_css_class("note-card")
        if is_pinned:
            card.add_css_class("pinned")

        # Top Bar: Badge, Time, Action buttons
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Note Badge
        badge = Gtk.Label(label="📝 GHI CHÚ" if self.lang == "vi" else "📝 NOTE")
        badge.add_css_class("type-badge")
        badge.add_css_class("badge-note")
        badge.set_halign(Gtk.Align.START)
        top_bar.append(badge)

        # Updated time
        time_lbl = Gtk.Label(label=format_relative_time(updated_at, self.lang))
        time_lbl.add_css_class("meta-label")
        time_lbl.set_halign(Gtk.Align.START)
        top_bar.append(time_lbl)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        top_bar.append(spacer)

        # Actions Box
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)

        # 1. Pin Button
        pin_btn = Gtk.Button()
        pin_btn.add_css_class("card-btn")
        pin_icon = Gtk.Image.new_from_icon_name("starred-symbolic")
        pin_btn.set_child(pin_icon)
        pin_btn.set_tooltip_text(t("tooltip_unpin", self.lang) if is_pinned else t("tooltip_pin", self.lang))
        if is_pinned:
            pin_btn.add_css_class("pin-active")
        pin_btn.connect("clicked", lambda _: self.on_pin(self.note.get("id")))
        actions_box.append(pin_btn)

        # 2. Edit Button
        edit_btn = Gtk.Button()
        edit_btn.add_css_class("card-btn")
        edit_btn.set_child(Gtk.Image.new_from_icon_name("document-edit-symbolic"))
        edit_btn.set_tooltip_text(t("tooltip_edit_note", self.lang))
        edit_btn.connect("clicked", lambda _: self.on_edit(self.note))
        actions_box.append(edit_btn)

        # 3. Copy / Use Button
        copy_btn = Gtk.Button()
        copy_btn.add_css_class("card-btn")
        copy_btn.set_child(Gtk.Image.new_from_icon_name("edit-copy-symbolic"))
        copy_btn.set_tooltip_text(t("tooltip_copy", self.lang))
        copy_btn.connect("clicked", lambda _: self.on_select(self.note))
        actions_box.append(copy_btn)

        # 4. Delete Button
        del_btn = Gtk.Button()
        del_btn.add_css_class("card-btn")
        del_btn.add_css_class("delete-btn")
        del_btn.set_child(Gtk.Image.new_from_icon_name("user-trash-symbolic"))
        del_btn.set_tooltip_text(t("tooltip_delete", self.lang))
        del_btn.connect("clicked", lambda _: self.on_delete(self.note.get("id")))
        actions_box.append(del_btn)

        top_bar.append(actions_box)
        card.append(top_bar)

        # Note Title (if any)
        if title:
            title_lbl = Gtk.Label(label=title)
            title_lbl.add_css_class("note-title-label")
            title_lbl.set_halign(Gtk.Align.START)
            title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            title_lbl.set_max_width_chars(50)
            card.append(title_lbl)

        # Note Content preview
        preview_text = truncate_text(content, max_lines=4, max_chars=300)
        content_lbl = Gtk.Label(label=preview_text)
        content_lbl.add_css_class("note-content-label")
        content_lbl.set_halign(Gtk.Align.START)
        content_lbl.set_wrap(True)
        content_lbl.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        content_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        content_lbl.set_lines(3)
        content_lbl.set_xalign(0.0)
        card.append(content_lbl)

        self.set_child(card)
