use std::io::{Read, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::path::PathBuf;
use std::time::Duration;
use tauri::{AppHandle, Manager};

pub fn get_ipc_socket_path() -> PathBuf {
    if let Ok(runtime_dir) = std::env::var("XDG_RUNTIME_DIR") {
        let p = PathBuf::from(runtime_dir).join("clipmaster_ipc.sock");
        return p;
    }

    if let Ok(home) = std::env::var("HOME") {
        let p = PathBuf::from(home)
            .join(".local")
            .join("share")
            .join("clipmaster")
            .join("clipmaster_ipc.sock");
        if let Some(parent) = p.parent() {
            std::fs::create_dir_all(parent).ok();
        }
        return p;
    }

    PathBuf::from("/tmp/clipmaster_ipc.sock")
}

pub fn send_toggle_command() -> bool {
    let sock_path = get_ipc_socket_path();
    if !sock_path.exists() {
        return false;
    }

    if let Ok(mut stream) = UnixStream::connect(&sock_path) {
        stream.set_read_timeout(Some(Duration::from_millis(500))).ok();
        stream.set_write_timeout(Some(Duration::from_millis(500))).ok();

        if stream.write_all(b"toggle\n").is_err() {
            return false;
        }

        let mut buf = [0u8; 16];
        if let Ok(n) = stream.read(&mut buf) {
            let resp = String::from_utf8_lossy(&buf[..n]);
            return resp.trim() == "OK";
        }
    } else {
        // Stale socket, remove it
        std::fs::remove_file(&sock_path).ok();
    }

    false
}

pub fn start_ipc_server(app_handle: AppHandle) {
    let sock_path = get_ipc_socket_path();

    if sock_path.exists() {
        if send_toggle_command() {
            return;
        }
        std::fs::remove_file(&sock_path).ok();
    }

    if let Some(parent) = sock_path.parent() {
        std::fs::create_dir_all(parent).ok();
    }

    let listener = match UnixListener::bind(&sock_path) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("[ClipMaster IPC] Failed to bind Unix socket: {}", e);
            return;
        }
    };

    println!("[ClipMaster IPC] Server listening on {:?}", sock_path);

    std::thread::spawn(move || {
        for stream_res in listener.incoming() {
            if let Ok(mut stream) = stream_res {
                let mut buf = [0u8; 128];
                if let Ok(n) = stream.read(&mut buf) {
                    let cmd = String::from_utf8_lossy(&buf[..n]).trim().to_string();
                    if cmd == "toggle" {
                        let app_clone = app_handle.clone();
                        let _ = app_handle.run_on_main_thread(move || {
                            if let Some(window) = app_clone.get_webview_window("main") {
                                if window.is_visible().unwrap_or(false) {
                                    window.hide().ok();
                                } else {
                                    window.show().ok();
                                    window.unminimize().ok();
                                    window.set_focus().ok();
                                }
                            }
                        });
                    }
                    let _ = stream.write_all(b"OK\n");
                }
            }
        }

        std::fs::remove_file(&sock_path).ok();
    });
}
