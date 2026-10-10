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

pub fn ensure_desktop_integration() {
    if let Ok(home) = std::env::var("HOME") {
        let home_path = std::path::PathBuf::from(&home);
        let hicolor_dir = home_path.join(".local/share/icons/hicolor");

        // 1. Install scalable icon (.svg)
        let svg_dir = hicolor_dir.join("scalable/apps");
        std::fs::create_dir_all(&svg_dir).ok();

        let possible_svgs = [
            std::path::PathBuf::from("/usr/share/icons/hicolor/scalable/apps/clipmaster.svg"),
            std::path::PathBuf::from("assets/icon.svg"),
            std::path::PathBuf::from("../assets/icon.svg"),
        ];

        for src in &possible_svgs {
            if src.exists() {
                std::fs::copy(src, svg_dir.join("clipmaster.svg")).ok();
                std::fs::copy(src, svg_dir.join("com.clipmaster.app.svg")).ok();
                std::fs::copy(src, svg_dir.join("app.svg")).ok();
                break;
            }
        }

        // 2. Install PNG icons for fast dock/taskbar resolution (128x128, 512x512, 32x32)
        let png_sizes = [("128x128", "128x128.png"), ("512x512", "icon.png"), ("32x32", "32x32.png")];
        for (dir_name, file_name) in png_sizes {
            let target_dir = hicolor_dir.join(dir_name).join("apps");
            std::fs::create_dir_all(&target_dir).ok();
            let possible_pngs = [
                std::path::PathBuf::from(format!("src-tauri/icons/{}", file_name)),
                std::path::PathBuf::from(format!("icons/{}", file_name)),
            ];
            for src in &possible_pngs {
                if src.exists() {
                    std::fs::copy(src, target_dir.join("clipmaster.png")).ok();
                    std::fs::copy(src, target_dir.join("app.png")).ok();
                    std::fs::copy(src, target_dir.join("com.clipmaster.app.png")).ok();
                    break;
                }
            }
        }

        // 3. Install desktop launchers (clipmaster.desktop, app.desktop, com.clipmaster.app.desktop)
        let app_dir = home_path.join(".local/share/applications");
        std::fs::create_dir_all(&app_dir).ok();
        let exec_cmd = get_executable_command();

        let desktop_content = format!(
            "[Desktop Entry]\nName=ClipMaster\nGenericName=Clipboard Manager\nComment=Windows + V style Clipboard History Manager for Linux\nExec={}\nIcon=clipmaster\nTerminal=false\nType=Application\nCategories=Utility;Accessories;\nStartupNotify=false\nStartupWMClass=clipmaster\n",
            exec_cmd
        );

        let dev_desktop_content = format!(
            "[Desktop Entry]\nName=ClipMaster\nGenericName=Clipboard Manager\nComment=Windows + V style Clipboard History Manager for Linux\nExec={}\nIcon=clipmaster\nTerminal=false\nType=Application\nCategories=Utility;Accessories;\nStartupNotify=false\nStartupWMClass=app\n",
            exec_cmd
        );

        std::fs::write(app_dir.join("clipmaster.desktop"), &desktop_content).ok();
        std::fs::write(app_dir.join("com.clipmaster.app.desktop"), &desktop_content).ok();
        std::fs::write(app_dir.join("app.desktop"), &dev_desktop_content).ok();

        // 4. Refresh desktop & icon caches
        let _ = Command::new("update-desktop-database").arg(&app_dir).output();
        let _ = Command::new("gtk-update-icon-cache")
            .args(["-q", "-t", "-f"])
            .arg(&hicolor_dir)
            .output();
    }
}

pub fn ensure_shortcut_registered(db: &Database) {
    ensure_desktop_integration();
    let shortcut = db.get_setting("shortcut", "<Super>v");
    install_gnome_shortcut(&shortcut);
}
