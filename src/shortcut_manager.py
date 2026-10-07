"""
ClipMaster Shortcut and Desktop Integration Manager
Configures global shortcut (Win+V or custom) in GNOME and autostart entries.
"""

import os
import sys
import ast
import subprocess

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk

CLIPMASTER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "clipmaster.py")
)
CUSTOM_PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/clipmaster/"
CUSTOM_SCHEMA = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{CUSTOM_PATH}"


def get_clipmaster_command() -> str:
    """Return executable command: system binary if installed via .deb or local python script."""
    if os.path.exists("/usr/bin/clipmaster"):
        return "/usr/bin/clipmaster"
    return f"python3 {CLIPMASTER_PATH}"


def get_icon_path_or_name() -> str:
    if os.path.exists("/usr/share/icons/hicolor/scalable/apps/clipmaster.svg"):
        return "clipmaster"
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icon.svg"))

POPULAR_SHORTCUTS = [
    ("<Super>v", "Win + V (Mặc định)"),
    ("<Control><Alt>v", "Ctrl + Alt + V"),
    ("<Control><Shift>v", "Ctrl + Shift + V"),
    ("<Alt>v", "Alt + V"),
    ("<Super><Shift>v", "Win + Shift + V"),
    ("<Super>c", "Win + C"),
]


def get_current_custom_keybindings() -> list:
    try:
        res = subprocess.run(
            ["gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"],
            capture_output=True, text=True, check=True
        )
        raw = res.stdout.strip()
        if raw.startswith("@as "):
            raw = raw[4:]
        return ast.literal_eval(raw)
    except Exception as e:
        print(f"Error reading custom-keybindings: {e}")
        return []


def get_current_shortcut() -> str:
    """Read the currently configured shortcut from gsettings."""
    try:
        bindings = get_current_custom_keybindings()
        if CUSTOM_PATH not in bindings:
            return ""
        res = subprocess.run(
            ["gsettings", "get", CUSTOM_SCHEMA, "binding"],
            capture_output=True, text=True, check=True
        )
        val = res.stdout.strip().replace("'", "").replace('"', "")
        return val
    except Exception:
        return ""


def is_shortcut_installed() -> bool:
    shortcut = get_current_shortcut()
    return bool(shortcut)


def format_shortcut_display(shortcut_str: str) -> str:
    """Format shortcut string to a friendly human-readable label."""
    if not shortcut_str:
        return "Chưa cài đặt"
    
    # Check presets
    for key, label in POPULAR_SHORTCUTS:
        if key.lower() == shortcut_str.lower():
            return label

    # Try GTK accelerator parser
    success, keyval, mods = Gtk.accelerator_parse(shortcut_str)
    if success:
        label = Gtk.accelerator_get_label(keyval, mods)
        # Replace Super with Win for Windows familiar users
        label = label.replace("Super", "Win").replace("Control", "Ctrl")
        return label

    # Fallback cleanup
    cleaned = (
        shortcut_str.replace("<Super>", "Win + ")
        .replace("<Control>", "Ctrl + ")
        .replace("<Primary>", "Ctrl + ")
        .replace("<Alt>", "Alt + ")
        .replace("<Shift>", "Shift + ")
    )
    return cleaned.upper() if len(cleaned) <= 10 else cleaned


def set_custom_shortcut(shortcut_str: str) -> bool:
    """
    Registers a given shortcut string to open ClipMaster,
    and resolves GNOME default conflicts if necessary.
    """
    if not shortcut_str:
        return remove_super_v_shortcut()

    try:
        # 1. If using <Super>v, unbind from GNOME's toggle-message-tray
        if "<super>v" in shortcut_str.lower():
            res = subprocess.run(
                ["gsettings", "get", "org.gnome.shell.keybindings", "toggle-message-tray"],
                capture_output=True, text=True
            )
            if "<Super>v" in res.stdout or "<super>v" in res.stdout:
                subprocess.run(
                    ["gsettings", "set", "org.gnome.shell.keybindings", "toggle-message-tray", "['<Super>m']"],
                    check=True
                )

        # 2. Add custom keybinding path to list if missing
        bindings = get_current_custom_keybindings()
        if CUSTOM_PATH not in bindings:
            bindings.append(CUSTOM_PATH)
            subprocess.run(
                ["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", str(bindings)],
                check=True
            )

        # 3. Configure shortcut parameters
        exec_cmd = f"{get_clipmaster_command()} --toggle"
        display_name = f"ClipMaster ({format_shortcut_display(shortcut_str)})"
        subprocess.run(["gsettings", "set", CUSTOM_SCHEMA, "name", display_name], check=True)
        subprocess.run(["gsettings", "set", CUSTOM_SCHEMA, "command", exec_cmd], check=True)
        subprocess.run(["gsettings", "set", CUSTOM_SCHEMA, "binding", shortcut_str], check=True)

        return True
    except Exception as e:
        print(f"Failed to set custom shortcut: {e}")
        return False


def install_super_v_shortcut() -> bool:
    """Default installer helper for Win+V."""
    return set_custom_shortcut("<Super>v")


def remove_super_v_shortcut() -> bool:
    try:
        bindings = get_current_custom_keybindings()
        if CUSTOM_PATH in bindings:
            bindings.remove(CUSTOM_PATH)
            subprocess.run(
                ["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", str(bindings)],
                check=True
            )
        subprocess.run(["gsettings", "reset-recursively", CUSTOM_SCHEMA])
        return True
    except Exception as e:
        print(f"Failed to remove shortcut: {e}")
        return False


def setup_desktop_entry() -> bool:
    """Create .desktop launcher in ~/.local/share/applications/"""
    app_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(app_dir, exist_ok=True)
    icon_path = get_icon_path_or_name()
    exec_cmd = f"{get_clipmaster_command()} --toggle"
    desktop_file = os.path.join(app_dir, "clipmaster.desktop")

    content = f"""[Desktop Entry]
Name=ClipMaster
GenericName=Clipboard Manager
Comment=Trình quản lý lịch sử sao chép tương tự Win + V
Exec={exec_cmd}
Icon={icon_path}
Terminal=false
Type=Application
Categories=Utility;Accessories;
Keywords=clipboard;paste;copy;history;win+v;
StartupNotify=false
"""
    try:
        with open(desktop_file, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(desktop_file, 0o755)
        return True
    except Exception as e:
        print(f"Error creating desktop entry: {e}")
        return False


def setup_autostart(enable: bool = True) -> bool:
    """Enable or disable autostart in ~/.config/autostart/"""
    autostart_dir = os.path.expanduser("~/.config/autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    autostart_file = os.path.join(autostart_dir, "clipmaster.desktop")

    if not enable:
        if os.path.exists(autostart_file):
            try:
                os.remove(autostart_file)
            except OSError:
                pass
        return True

    icon_path = get_icon_path_or_name()
    exec_cmd = f"{get_clipmaster_command()} --daemon"
    content = f"""[Desktop Entry]
Name=ClipMaster Daemon
Comment=Khởi động ClipMaster chạy ngầm khi đăng nhập
Exec={exec_cmd}
Icon={icon_path}
Terminal=false
Type=Application
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""
    try:
        with open(autostart_file, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(autostart_file, 0o755)
        return True
    except Exception as e:
        print(f"Error creating autostart entry: {e}")
        return False


def is_autostart_enabled() -> bool:
    autostart_file = os.path.expanduser("~/.config/autostart/clipmaster.desktop")
    return os.path.exists(autostart_file)
