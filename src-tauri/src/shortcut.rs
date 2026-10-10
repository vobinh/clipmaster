use std::path::Path;
use std::process::Command;
use crate::database::Database;

pub fn get_executable_command() -> String {
    // 1. If standard system binary exists, prefer it
    if Path::new("/usr/bin/clipmaster").exists() {
        return "/usr/bin/clipmaster --toggle".to_string();
    }
    if Path::new("/snap/bin/clipmaster").exists() {
        return "/snap/bin/clipmaster --toggle".to_string();
    }

    // 2. In development or local runs, use the current binary path
    if let Ok(current_exe) = std::env::current_exe() {
        return format!("{} --toggle", current_exe.to_string_lossy());
    }

    "clipmaster --toggle".to_string()
}

pub fn install_gnome_shortcut(shortcut_key: &str) -> bool {
    let custom_path = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/clipmaster/";
    let custom_schema = format!("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{}", custom_path);
    let exec_cmd = get_executable_command();
    let display_name = "ClipMaster";
    let binding = shortcut_key.trim();

    // 1. If shortcut contains <Super>v, resolve GNOME default conflict
    if binding.to_lowercase().contains("<super>v") {
        let _ = Command::new("gsettings")
            .args(["set", "org.gnome.shell.keybindings", "toggle-message-tray", "['<Super>m']"])
            .output();
        let _ = Command::new("dconf")
            .args(["write", "/org/gnome/shell/keybindings/toggle-message-tray", "['<Super>m']"])
            .output();
    }

    // 2. Read existing custom keybindings
    let mut bindings: Vec<String> = Vec::new();
    if let Ok(output) = Command::new("gsettings")
        .args(["get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"])
        .output()
    {
        let raw = String::from_utf8_lossy(&output.stdout).trim().to_string();
        let cleaned = raw.trim_start_matches("@as ").trim();
        for item in cleaned.split(',') {
            let item = item.trim().trim_matches(|c| c == '[' || c == ']' || c == '\'' || c == '"' || c == ' ');
            if !item.is_empty() {
                bindings.push(item.to_string());
            }
        }
    }

    if !bindings.iter().any(|b| b == custom_path) {
        bindings.push(custom_path.to_string());
    }

    let bindings_repr = format!("[{}]", bindings.iter().map(|b| format!("'{}'", b)).collect::<Vec<_>>().join(", "));

    // 3. Set via gsettings
    let _ = Command::new("gsettings")
        .args(["set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", &bindings_repr])
        .output();
    let _ = Command::new("gsettings")
        .args(["set", &custom_schema, "name", display_name])
        .output();
    let _ = Command::new("gsettings")
        .args(["set", &custom_schema, "command", &exec_cmd])
        .output();
    let res = Command::new("gsettings")
        .args(["set", &custom_schema, "binding", binding])
        .output();

    // 4. Set via dconf for desktop session daemons
    let _ = Command::new("dconf")
        .args(["write", "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings", &bindings_repr])
        .output();
    let _ = Command::new("dconf")
        .args(["write", &format!("{}name", custom_path), &format!("'{}'", display_name)])
        .output();
    let _ = Command::new("dconf")
        .args(["write", &format!("{}command", custom_path), &format!("'{}'", exec_cmd)])
        .output();
    let _ = Command::new("dconf")
        .args(["write", &format!("{}binding", custom_path), &format!("'{}'", binding)])
        .output();

    res.map(|o| o.status.success()).unwrap_or(false)
}

pub fn ensure_shortcut_registered(db: &Database) {
    let shortcut = db.get_setting("shortcut", "<Super>v");
    install_gnome_shortcut(&shortcut);
}
