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
    """Return executable command: system binary if installed via snap/deb or local python script."""
    if os.path.exists("/snap/bin/clipmaster"):
        return "/snap/bin/clipmaster"
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
    # 1. Try dconf first (works in Snap and does not require compiled schemas)
    try:
        res = subprocess.run(
            ["dconf", "read", "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"],
            capture_output=True, text=True
        )
        if res.returncode == 0:
            raw = res.stdout.strip()
            if raw.startswith("@as "):
                raw = raw[4:]
            if not raw or raw == "[]":
                return []
            return ast.literal_eval(raw)
    except Exception:
        pass

    # 2. Fallback to gsettings
    try:
        res = subprocess.run(
            ["gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"],
            capture_output=True, text=True
        )
        if res.returncode == 0:
            raw = res.stdout.strip()
            if raw.startswith("@as "):
                raw = raw[4:]
            if not raw or raw == "[]":
                return []
            return ast.literal_eval(raw)
    except Exception as e:
        print(f"Error reading custom-keybindings: {e}")
    return []


def get_current_shortcut() -> str:
    """Read the currently configured shortcut from dconf or gsettings."""
    # 1. Try dconf first
    try:
        res = subprocess.run(
            ["dconf", "read", f"{CUSTOM_PATH}binding"],
            capture_output=True, text=True
        )
        if res.returncode == 0 and res.stdout.strip():
            val = res.stdout.strip().replace("'", "").replace('"', "")
            if val:
                return val
    except Exception:
        pass

    # 2. Fallback to gsettings
    try:
        bindings = get_current_custom_keybindings()
        if CUSTOM_PATH in bindings:
            res = subprocess.run(
                ["gsettings", "get", CUSTOM_SCHEMA, "binding"],
                capture_output=True, text=True
            )
            if res.returncode == 0 and res.stdout.strip():
                val = res.stdout.strip().replace("'", "").replace('"', "")
                return val
    except Exception:
        pass

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
    Uses dconf (primary) with gsettings fallback.
    """
    if not shortcut_str:
        return remove_super_v_shortcut()

    exec_cmd = f"{get_clipmaster_command()} --toggle"
    display_name = f"ClipMaster ({format_shortcut_display(shortcut_str)})"
    success = False

    # 1. Resolve GNOME <Super>v conflict with toggle-message-tray
    if "<super>v" in shortcut_str.lower():
        try:
            subprocess.run(
                ["dconf", "write", "/org/gnome/shell/keybindings/toggle-message-tray", "['<Super>m']"],
                capture_output=True
            )
        except Exception:
            pass
        try:
            subprocess.run(
                ["gsettings", "set", "org.gnome.shell.keybindings", "toggle-message-tray", "['<Super>m']"],
                capture_output=True
            )
        except Exception:
            pass

    # 2. Add custom keybinding path to list
    bindings = get_current_custom_keybindings()
    if CUSTOM_PATH not in bindings:
        bindings.append(CUSTOM_PATH)
    bindings_repr = str(bindings)

    # 3. Write via dconf
    try:
        r1 = subprocess.run(
            ["dconf", "write", "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings", bindings_repr],
            capture_output=True
        )
        r2 = subprocess.run(
            ["dconf", "write", f"{CUSTOM_PATH}name", f"'{display_name}'"],
            capture_output=True
        )
        r3 = subprocess.run(
            ["dconf", "write", f"{CUSTOM_PATH}command", f"'{exec_cmd}'"],
            capture_output=True
        )
        r4 = subprocess.run(
            ["dconf", "write", f"{CUSTOM_PATH}binding", f"'{shortcut_str}'"],
            capture_output=True
        )
        if r1.returncode == 0 and r2.returncode == 0 and r3.returncode == 0 and r4.returncode == 0:
            success = True
    except Exception as e:
        print(f"dconf set failed: {e}")

    # 4. Also sync via gsettings if available
    try:
        subprocess.run(
            ["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", bindings_repr],
            capture_output=True
        )
        subprocess.run(["gsettings", "set", CUSTOM_SCHEMA, "name", display_name], capture_output=True)
        subprocess.run(["gsettings", "set", CUSTOM_SCHEMA, "command", exec_cmd], capture_output=True)
        r = subprocess.run(["gsettings", "set", CUSTOM_SCHEMA, "binding", shortcut_str], capture_output=True)
        if r.returncode == 0:
            success = True
    except Exception:
        pass

    return success


def install_super_v_shortcut() -> bool:
    """Default installer helper for Win+V."""
    return set_custom_shortcut("<Super>v")


def remove_super_v_shortcut() -> bool:
    bindings = get_current_custom_keybindings()
    if CUSTOM_PATH in bindings:
        bindings.remove(CUSTOM_PATH)
    bindings_repr = str(bindings)

    # Reset via dconf
    try:
        subprocess.run(
            ["dconf", "write", "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings", bindings_repr],
            capture_output=True
        )
        subprocess.run(
            ["dconf", "reset", "-f", CUSTOM_PATH],
            capture_output=True
        )
    except Exception:
        pass

    # Reset via gsettings
    try:
        subprocess.run(
            ["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", bindings_repr],
            capture_output=True
        )
        subprocess.run(["gsettings", "reset-recursively", CUSTOM_SCHEMA], capture_output=True)
    except Exception:
        pass

    return True


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
