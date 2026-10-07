"""
ClipMaster Clipboard Manager
Monitors system clipboard for new entries (text, code, links, images)
and synchronizes selections across Wayland and X11/XWayland.
"""

import os
import shutil
import time
import subprocess
import threading
from typing import Optional, Callable

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib

from .database import Database, IMAGES_DIR
from .utils import detect_content_type


class ClipboardManager:
    def __init__(self, db: Database, on_new_clip: Optional[Callable] = None):
        self.db = db
        self.on_new_clip = on_new_clip
        self.last_hash = ""
        self.has_wl_copy = shutil.which("wl-copy") is not None
        self.has_wl_paste = shutil.which("wl-paste") is not None
        self.has_xsel = shutil.which("xsel") is not None
        self.has_xdotool = shutil.which("xdotool") is not None
        self.is_monitoring = False
        self._lock = threading.Lock()

        # Initialize last_hash from existing clipboard so startup doesn't trigger spurious notification
        current = self.read_clipboard_text_sync()
        if current:
            self.last_hash = Database.compute_hash(content=current)
            # Ensure current is in DB
            c_type = detect_content_type(current)
            self.db.add_clip(clip_type=c_type, content=current)

    def start_monitoring(self):
        """Start listening to clipboard events."""
        if self.is_monitoring:
            return
        self.is_monitoring = True

        # 1. GDK Clipboard Changed Listener
        display = Gdk.Display.get_default()
        if display:
            self.gdk_clipboard = display.get_clipboard()
            self.gdk_clipboard.connect("changed", self._on_gdk_changed)

        # 2. Fallback periodic check (checks every 1.2s to catch external events cleanly)
        GLib.timeout_add(1200, self._periodic_check)

    def _on_gdk_changed(self, clipboard):
        """Called when GDK clipboard changes."""
        GLib.idle_add(self._check_and_process_clipboard)

    def _periodic_check(self) -> bool:
        """Lightweight timer checking for clipboard updates."""
        if not self.is_monitoring:
            return False
        self._check_and_process_clipboard()
        return True

    def is_recording(self) -> bool:
        return self.db.get_setting("auto_record", "1") == "1"

    def set_recording(self, enable: bool):
        self.db.set_setting("auto_record", "1" if enable else "0")

    def toggle_recording(self) -> bool:
        new_state = not self.is_recording()
        self.set_recording(new_state)
        return new_state

    def _check_and_process_clipboard(self):
        """Inspect clipboard and persist if new."""
        # If auto-recording is turned off (paused / incognito mode)
        if not self.is_recording():
            # Keep last_hash in sync with current clipboard so re-enabling doesn't dump private text
            text = self.read_clipboard_text_sync()
            if text:
                self.last_hash = Database.compute_hash(content=text)
            return

        # 1. First check text
        text = self.read_clipboard_text_sync()
        if text and text.strip():
            c_hash = Database.compute_hash(content=text)
            if c_hash != self.last_hash:
                self.last_hash = c_hash
                c_type = detect_content_type(text)
                clip = self.db.add_clip(clip_type=c_type, content=text)
                if clip and self.on_new_clip:
                    self.on_new_clip(clip)
                return

        # 2. Check image if enabled
        if self.db.get_setting("save_images", "1") == "1":
            self._check_clipboard_image()

    def _check_clipboard_image(self):
        """Check if clipboard contains an image texture."""
        display = Gdk.Display.get_default()
        if not display:
            return
        clip = display.get_clipboard()
        formats = clip.get_formats()
        mime_types = formats.get_mime_types() or []

        has_image = any("image/" in m for m in mime_types)
        if not has_image:
            return

        def texture_callback(clipboard, result):
            try:
                texture = clipboard.read_texture_finish(result)
                if not texture:
                    return

                width = texture.get_width()
                height = texture.get_height()
                if width <= 0 or height <= 0:
                    return

                # Create temp file to hash
                now_str = str(time.time())
                tmp_path = os.path.join(IMAGES_DIR, f"temp_{now_str}.png")
                texture.save_to_png(tmp_path)

                with open(tmp_path, "rb") as f:
                    img_bytes = f.read()

                img_hash = Database.compute_hash(image_bytes=img_bytes)
                final_path = os.path.join(IMAGES_DIR, f"img_{img_hash[:16]}.png")

                if img_hash != self.last_hash:
                    self.last_hash = img_hash
                    os.replace(tmp_path, final_path)
                    clip = self.db.add_clip(
                        clip_type="image",
                        image_path=final_path,
                        image_width=width,
                        image_height=height,
                        image_bytes=img_bytes,
                    )
                    if clip and self.on_new_clip:
                        self.on_new_clip(clip)
                else:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            except Exception as e:
                # Silently catch non-image or locked clipboard
                pass

        clip.read_texture_async(None, texture_callback)

    def read_clipboard_text_sync(self) -> str:
        """Fast synchronous text reader using xsel or wl-paste."""
        if self.has_xsel:
            try:
                res = subprocess.run(
                    ["xsel", "-b", "-o"],
                    capture_output=True,
                    text=True,
                    timeout=0.3
                )
                if res.returncode == 0 and res.stdout:
                    return res.stdout
            except Exception:
                pass

        if self.has_wl_paste:
            try:
                res = subprocess.run(
                    ["wl-paste", "--no-newline"],
                    capture_output=True,
                    text=True,
                    timeout=0.3
                )
                if res.returncode == 0 and res.stdout:
                    return res.stdout
            except Exception:
                pass

        return ""

    def copy_to_clipboard(self, clip: dict, auto_paste: bool = True):
        """Set content back into clipboard and optionally simulate paste."""
        clip_type = clip.get("type", "text")
        content = clip.get("content", "")
        img_path = clip.get("image_path")

        # Update last_hash so we don't trigger duplicate loop
        if clip_type == "image" and img_path and os.path.exists(img_path):
            with open(img_path, "rb") as f:
                self.last_hash = Database.compute_hash(image_bytes=f.read())
            self._set_clipboard_image(img_path)
        else:
            self.last_hash = Database.compute_hash(content=content)
            self._set_clipboard_text(content)

        if auto_paste and self.db.get_setting("auto_paste", "1") == "1":
            self.simulate_paste()

    def _set_clipboard_text(self, text: str):
        """Sets clipboard text across GDK, xsel, and wl-copy."""
        # 1. GDK
        try:
            display = Gdk.Display.get_default()
            if display:
                display.get_clipboard().set(text)
        except Exception:
            pass

        # 2. xsel
        if self.has_xsel:
            try:
                p = subprocess.Popen(["xsel", "-b", "-i"], stdin=subprocess.PIPE)
                p.communicate(text.encode("utf-8", errors="ignore"))
            except Exception:
                pass

        # 3. wl-copy
        if self.has_wl_copy:
            try:
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                p.communicate(text.encode("utf-8", errors="ignore"))
            except Exception:
                pass

    def _set_clipboard_image(self, img_path: str):
        """Set image file into clipboard."""
        try:
            texture = Gdk.Texture.new_from_filename(img_path)
            display = Gdk.Display.get_default()
            if display and texture:
                display.get_clipboard().set_texture(texture)
        except Exception:
            pass

        if self.has_wl_copy:
            try:
                with open(img_path, "rb") as f:
                    p = subprocess.Popen(["wl-copy", "-t", "image/png"], stdin=subprocess.PIPE)
                    p.communicate(f.read())
            except Exception:
                pass

    def simulate_paste(self):
        """Simulates Ctrl+V using xdotool after a small delay."""
        if not self.has_xdotool:
            return

        def _do_paste():
            time.sleep(0.18)  # Allow previous window to regain focus
            try:
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
                    capture_output=True,
                    timeout=0.5
                )
            except Exception:
                pass

        threading.Thread(target=_do_paste, daemon=True).start()
