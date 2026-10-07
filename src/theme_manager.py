"""
ClipMaster Theme Manager
Manages application dark, light, and system themes via Libadwaita StyleManager.
"""

from typing import List, Tuple
import gi
gi.require_version("Adw", "1")
from gi.repository import Adw


THEME_MODES: List[Tuple[str, str]] = [
    ("system", "theme_system"),
    ("dark", "theme_dark"),
    ("light", "theme_light"),
]


def apply_theme_mode(theme_mode: str) -> None:
    """Apply the specified theme mode to the application via Libadwaita."""
    sm = Adw.StyleManager.get_default()
    if theme_mode == "dark":
        sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    elif theme_mode == "light":
        sm.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
    else:  # "system" or "default"
        sm.set_color_scheme(Adw.ColorScheme.DEFAULT)


def get_current_theme_mode(db) -> str:
    """Retrieve saved theme mode from settings, defaulting to 'dark'."""
    return db.get_setting("theme_mode", "dark")


def toggle_theme_mode(db) -> str:
    """Toggle between dark and light mode, save to db, and apply immediately."""
    sm = Adw.StyleManager.get_default()
    is_currently_dark = sm.get_dark()
    new_mode = "light" if is_currently_dark else "dark"
    db.set_setting("theme_mode", new_mode)
    apply_theme_mode(new_mode)
    return new_mode
