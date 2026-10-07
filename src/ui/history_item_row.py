"""
ClipMaster History Item Row
Component rendering each clipboard entry card with rich preview and action buttons.
"""

import os
from typing import Callable, Dict, Any

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Gdk, Pango

from ..utils import format_relative_time, extract_domain, truncate_text


class HistoryItemRow(Gtk.ListBoxRow):
    def __init__(
        self,
        clip: Dict[str, Any],
        on_select: Callable[[Dict[str, Any]], None],
        on_pin: Callable[[int], None],
        on_delete: Callable[[int], None],
        lang: str = "vi"
    ):
        super().__init__()
        self.clip = clip
        self.on_select = on_select
        self.on_pin = on_pin
        self.on_delete = on_delete
        self.lang = lang

        self.set_activatable(True)
        self.set_selectable(True)
        self._build_ui()

    def _build_ui(self):
        from ..i18n import t
        clip_type = self.clip.get("type", "text")
        is_pinned = bool(self.clip.get("is_pinned", 0))
        created_at = self.clip.get("updated_at", self.clip.get("created_at", 0))

        # Main Card Container
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.add_css_class("clip-card")
        if is_pinned:
            card.add_css_class("pinned")

        # Top Bar: Badge, Metadata, Action Buttons
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Type Badge
        badge = Gtk.Label()
        badge.add_css_class("type-badge")
        if clip_type == "code":
            badge.set_text(t("badge_code", self.lang))
            badge.add_css_class("badge-code")
        elif clip_type == "url":
            domain = extract_domain(self.clip.get("content", ""))
            badge.set_text(t("badge_link", self.lang, domain=domain))
            badge.add_css_class("badge-url")
        elif clip_type == "color":
            badge.set_text(t("badge_color", self.lang))
            badge.add_css_class("badge-color")
        elif clip_type == "image":
            w = self.clip.get("image_width", 0)
            h = self.clip.get("image_height", 0)
            txt = t("badge_image", self.lang, w=w, h=h) if w and h else t("badge_image_simple", self.lang)
            badge.set_text(txt)
            badge.add_css_class("badge-image")
        else:
            chars = self.clip.get("char_count", 0)
            txt = t("badge_text", self.lang, chars=chars) if chars > 0 else t("badge_text_simple", self.lang)
            badge.set_text(txt)
            badge.add_css_class("badge-text")
        badge.set_halign(Gtk.Align.START)
        top_bar.append(badge)

        # Relative Time Label
        time_lbl = Gtk.Label(label=format_relative_time(created_at, self.lang))
        time_lbl.add_css_class("meta-label")
        time_lbl.set_halign(Gtk.Align.START)
        top_bar.append(time_lbl)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        top_bar.append(spacer)

        # Action Buttons Container
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)

        # Pin Button
        pin_btn = Gtk.Button()
        pin_btn.add_css_class("card-btn")
        pin_icon = Gtk.Image.new_from_icon_name("starred-symbolic")
        pin_btn.set_child(pin_icon)
        pin_btn.set_tooltip_text(t("tooltip_unpin", self.lang) if is_pinned else t("tooltip_pin", self.lang))
        if is_pinned:
            pin_btn.add_css_class("pin-active")
        pin_btn.connect("clicked", self._on_pin_clicked)
        actions_box.append(pin_btn)

        # Copy / Select Button
        copy_btn = Gtk.Button()
        copy_btn.add_css_class("card-btn")
        copy_btn.set_child(Gtk.Image.new_from_icon_name("edit-copy-symbolic"))
        copy_btn.set_tooltip_text(t("tooltip_copy", self.lang))
        copy_btn.connect("clicked", lambda b: self.on_select(self.clip))
        actions_box.append(copy_btn)

        # Delete Button
        del_btn = Gtk.Button()
        del_btn.add_css_class("card-btn")
        del_btn.add_css_class("delete-btn")
        del_btn.set_child(Gtk.Image.new_from_icon_name("user-trash-symbolic"))
        del_btn.set_tooltip_text(t("tooltip_delete", self.lang))
        del_btn.connect("clicked", self._on_delete_clicked)
        actions_box.append(del_btn)

        top_bar.append(actions_box)
        card.append(top_bar)

        # Body Preview
        body = self._create_body_widget(clip_type)
        if body:
            card.append(body)

        self.set_child(card)

    def _create_body_widget(self, clip_type: str) -> Gtk.Widget:
        content = self.clip.get("content", "") or ""

        if clip_type == "image":
            img_path = self.clip.get("image_path")
            if img_path and os.path.exists(img_path):
                img_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                try:
                    picture = Gtk.Picture.new_for_filename(img_path)
                    picture.set_can_shrink(True)
                    picture.set_content_fit(Gtk.ContentFit.CONTAIN)
                    picture.set_size_request(-1, 90)
                    picture.add_css_class("image-thumbnail")
                    img_box.append(picture)
                except Exception:
                    pass
                return img_box
            return Gtk.Label(label="[Hình ảnh]")

        elif clip_type == "color":
            color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            swatch = Gtk.Box()
            swatch.add_css_class("color-swatch")
            swatch.set_size_request(26, 26)

            # Apply background color via CSS provider
            css_prov = Gtk.CssProvider()
            css_prov.load_from_data(f".color-swatch {{ background-color: {content.strip()}; }}".encode())
            swatch.get_style_context().add_provider(css_prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

            color_box.append(swatch)

            lbl = Gtk.Label(label=content.strip())
            lbl.add_css_class("content-text")
            lbl.set_halign(Gtk.Align.START)
            color_box.append(lbl)
            return color_box

        elif clip_type == "code":
            lines = content.strip().splitlines()
            preview_lines = lines[:4]
            preview = "\n".join(preview_lines)
            if len(lines) > 4:
                preview += f"\n... (+{len(lines)-4} dòng)"

            lbl = Gtk.Label(label=preview)
            lbl.add_css_class("content-code")
            lbl.set_wrap(True)
            lbl.set_wrap_mode(Pango.WrapMode.CHAR)
            lbl.set_max_width_chars(50)
            lbl.set_xalign(0.0)
            lbl.set_selectable(False)
            return lbl

        elif clip_type == "url":
            lbl = Gtk.Label(label=content.strip())
            lbl.add_css_class("content-text")
            lbl.set_wrap(True)
            lbl.set_wrap_mode(Pango.WrapMode.CHAR)
            lbl.set_max_width_chars(50)
            lbl.set_xalign(0.0)
            lbl.set_selectable(False)
            return lbl

        else:
            # Regular text
            lines = content.strip().splitlines()
            preview_lines = lines[:3]
            preview = "\n".join(preview_lines)
            if len(lines) > 3:
                preview += f"\n... (+{len(lines)-3} dòng)"
            elif len(preview) > 200:
                preview = preview[:200] + "..."

            lbl = Gtk.Label(label=preview)
            lbl.add_css_class("content-text")
            lbl.set_wrap(True)
            lbl.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            lbl.set_max_width_chars(50)
            lbl.set_xalign(0.0)
            lbl.set_selectable(False)
            return lbl

    def _on_pin_clicked(self, button):
        clip_id = self.clip.get("id")
        if clip_id:
            self.on_pin(clip_id)

    def _on_delete_clicked(self, button):
        clip_id = self.clip.get("id")
        if clip_id:
            self.on_delete(clip_id)
