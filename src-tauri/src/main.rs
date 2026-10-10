// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|arg| arg == "--toggle" || arg == "-t") {
        if app_lib::ipc::send_toggle_command() {
            return;
        }
    }

    app_lib::run();
}
