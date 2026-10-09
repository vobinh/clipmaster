# 📋 ClipMaster - Windows + V Clipboard History for Linux

<p align="center">
  <a href="#-tiếng-việt">🇻🇳 Tiếng Việt</a> •
  <a href="#-english">🇬🇧 English</a>
</p>

---

# 🇻🇳 Tiếng Việt

**ClipMaster** là ứng dụng quản lý lịch sử Clipboard (khay nhớ tạm) cao cấp dành cho Ubuntu và Linux (GNOME / Zorin OS / Debian), mang trải nghiệm **Windows + V** mượt mà, tiện lợi lên hệ điều hành Linux của bạn.

---

## ✨ Tính năng nổi bật

- ⚡ **Phím tắt toàn cục Win + V (`Super + V`)**: Bấm `Win + V` bất cứ lúc nào trên desktop để bật/tắt cửa sổ danh sách clipboard.
- 🎨 **Giao diện hiện đại & Dark Mode (GTK4 + Libadwaita)**: Thiết kế đẹp mắt, bo tròn tinh tế, hỗ trợ đầy đủ **Chế độ Tối (Dark Mode)**, **Chế độ Sáng (Light Mode)** và **Tự động theo hệ thống**. Nút chuyển đổi nhanh Dark/Light ngay trên thanh tiêu đề!
- 📝 **Tab Ghi chú riêng biệt (Personal Notes) & Nút FAB**:
  - Quản lý ghi chú cá nhân tiện lợi bên cạnh lịch sử clipboard với 2 tab chuyển đổi `📋 Lịch sử` và `📝 Ghi chú`.
  - Nút Floating Action Button (FAB) `+` nổi ở góc phải giúp tạo ghi chú mới tức thì (`Ctrl + N`).
  - Hỗ trợ ghim ghi chú quan trọng, chỉnh sửa, sao chép 1-click hoặc dán nhanh.
- 🔒 **Bảo mật mã PIN 4 số cho Ghi chú**:
  - Tùy chọn cài đặt mã PIN bảo vệ toàn bộ ghi chú riêng tư.
  - Màn hình mở khóa bằng bàn phím số ảo hoặc bàn phím máy tính cực kỳ bảo mật và trực quan.
  - Tự động khóa linh hoạt: Khóa ngay lập tức khi chuyển tab, sau 1 phút, 5 phút, 15 phút, 30 phút hoặc chỉ khi tắt app.
  - **Cơ chế chống dò mã PIN**: Tự động khóa và đếm ngược 30 giây sau mỗi 3 lần nhập sai liên tiếp.
- ☁️ **Đồng bộ đám mây / Máy chủ riêng (BYOS - Bring Your Own Server)**:
  - Đồng bộ hóa lịch sử clipboard và ghi chú cá nhân xuyên suốt các thiết bị máy tính qua máy chủ riêng (Cloud / Self-hosted).
  - Hỗ trợ linh hoạt 3 chế độ đồng bộ: **Đồng bộ 2 chiều (Hai chiều)**, **Chỉ đồng bộ lên (Tải lên)**, hoặc **Chỉ đồng bộ xuống (Tải về)**.
  - Tự động cấu hình và tạo bảng dữ liệu trên server cho người dùng mới hoàn toàn khi kết nối lần đầu.
- 🔍 **Thanh Tìm kiếm & Bộ lọc gộp 1 dòng thông minh**:
  - Gộp nút Tìm kiếm `[ 🔍 ]` và các thẻ lọc thể loại trên cùng một hàng giúp tiết kiệm chiều cao cửa sổ.
  - Nút tìm kiếm đặt ở đầu dòng, khi click hoặc nhấn `Ctrl + F` sẽ mở rộng toàn dòng mượt mà với hiệu ứng chuyển cảnh; bấm `Esc` hoặc xóa rỗng sẽ tự thu gọn lại.
- 🏷️ **Tự động nhận diện nội dung thông minh**:
  - 📝 **Văn bản thông thường (Text)**: Hiển thị độ dài và số dòng.
  - 💻 **Mã nguồn (Code)**: Nhận diện cú pháp lập trình, hiển thị font monospace.
  - 🔗 **Liên kết (URL)**: Trích xuất tên miền trang web (`github.com`, `google.com`...).
  - 🎨 **Mã màu sắc (HEX / RGB / HSL)**: Hiển thị ô màu mẫu trực quan (`#3B82F6`, `rgb(...)`).
  - 🖼️ **Hình ảnh & Ảnh chụp màn hình**: Tự động lưu và hiển thị ảnh thumbnail xem trước.
- 📌 **Ghim nội dung quan trọng (Pin)**: Các mục được ghim sẽ luôn được giữ lại và không bị xóa khi dọn dẹp.
- 🚀 **Tự động dán (Auto-paste)**: Click vào mục bất kỳ hoặc nhấn Enter để sao chép lại vào clipboard và tự động dán vào ứng dụng bạn đang soạn thảo.
- 🌐 **Đa ngôn ngữ (Tiếng Việt & English)**: Hỗ trợ chuyển đổi nhanh giữa Tiếng Việt và Tiếng Anh trong phần Cài đặt hoặc qua dòng lệnh.
- ⏸️ **Công tắc Tạm dừng ghi nhớ (Chế độ riêng tư)**: Bật/tắt nhanh tính năng tự động lưu. Khi bạn cần sao chép mật khẩu, mã xác thực hay dữ liệu tạm thời không muốn lưu vào lịch sử, chỉ cần 1 click để tạm dừng.
- 🧹 **Dọn dẹp thông minh**: Tự động giới hạn số lượng mục lưu trữ hoặc xóa toàn bộ các mục chưa ghim với 1 nút bấm.
- ⚙️ **Chạy ngầm cực nhẹ**: Sử dụng SQLite lưu trữ an toàn, tiêu tốn chưa đến 15MB RAM và gần như 0% CPU khi chạy nền.

---

## 🚀 Cài đặt & Khởi động

### Cách 1: Chạy script tự động trực tiếp từ thư mục
```bash
./install.sh
```
Script sẽ tự động:
1. Cấp quyền thực thi và dọn các tiến trình cũ.
2. Đăng ký phím tắt **Win + V** trong cài đặt GNOME.
3. Tạo icon ứng dụng ClipMaster trong menu ứng dụng.
4. Kích hoạt dịch vụ chạy ngầm tự động mỗi khi mở máy (Systemd user service).

---

### Cách 2: Tự đóng gói file `.deb` (Debian / Ubuntu / Zorin OS)
Nếu bạn muốn tạo file cài đặt `.deb` để chia sẻ cho các máy khác:
```bash
./build_deb.sh
```
Sau đó cài đặt gói đã tạo:
```bash
sudo apt install ./clipmaster_1.0.0_all.deb
```

---

### Cách 3: Đóng gói và cài đặt qua Snap (Snapcraft / Snap Store)
Cấu hình Snap đã được tạo sẵn tại thư mục `snap/`:
- **Đóng gói file `.snap` bằng Snapcraft:**
  ```bash
  snapcraft
  ```
- **Cài đặt file `.snap` cục bộ:**
  ```bash
  sudo snap install clipmaster_1.0.0_amd64.snap --dangerous
  ```
- **Đăng ký và phát hành lên Snap Store:**
  ```bash
  snapcraft login
  snapcraft register clipmaster
  snapcraft upload clipmaster_1.0.0_amd64.snap --release=stable
  ```

---

### Cách 4: Sử dụng bằng dòng lệnh (CLI)

- **Bật / tắt cửa sổ danh sách:**
  ```bash
  python3 clipmaster.py --toggle
  ```
- **Chuyển sang chế độ tối (Dark Mode):**
  ```bash
  python3 clipmaster.py --theme dark
  ```
- **Chuyển sang chế độ sáng (Light Mode):**
  ```bash
  python3 clipmaster.py --theme light
  ```
- **Chuyển sang tự động theo hệ thống (System Default):**
  ```bash
  python3 clipmaster.py --theme system
  ```
- **Bật / tắt nhanh Dark/Light Mode:**
  ```bash
  python3 clipmaster.py --toggle-theme
  ```
- **Đổi ngôn ngữ sang Tiếng Anh (English):**
  ```bash
  python3 clipmaster.py --set-lang en
  ```
- **Đổi ngôn ngữ sang Tiếng Việt:**
  ```bash
  python3 clipmaster.py --set-lang vi
  ```
- **Tạm dừng tự động ghi nhớ (Chế độ ẩn danh):**
  ```bash
  python3 clipmaster.py --pause
  ```
- **Bật lại tự động ghi nhớ:**
  ```bash
  python3 clipmaster.py --resume
  ```
- **Bật / tắt nhanh tự động ghi nhớ:**
  ```bash
  python3 clipmaster.py --toggle-record
  ```
- **Kiểm tra trạng thái & phím tắt đang sử dụng:**
  ```bash
  python3 clipmaster.py --status
  ```
- **Thay đổi phím tắt qua CLI (ví dụ: Ctrl + Alt + V):**
  ```bash
  python3 clipmaster.py --set-shortcut '<Control><Alt>v'
  ```
- **Đặt lại phím tắt mặc định Win + V:**
  ```bash
  python3 clipmaster.py --set-shortcut '<Super>v'
  ```
- **Xóa các mục chưa ghim:**
  ```bash
  python3 clipmaster.py --clear
  ```

---

## ⚙️ Tùy chỉnh phím tắt trong giao diện (GUI)

Bạn có thể thay đổi phím tắt bất kỳ lúc nào trực tiếp trong ứng dụng:
1. Mở ClipMaster bằng phím tắt hiện tại hoặc gõ `python3 clipmaster.py --toggle`.
2. Bấm vào biểu tượng **⚙️ Cài đặt** ở góc trên bên phải.
3. Trong mục **Phím tắt hệ thống**:
   - Chọn nhanh các mẫu phổ biến: `Win + V`, `Ctrl + Alt + V`, `Ctrl + Shift + V`, `Alt + V`, `Win + Shift + V`...
   - Hoặc bấm nút **"Đổi phím tắt..."**: một cửa sổ trực quan sẽ hiện ra, bạn chỉ cần nhấn tổ hợp phím bất kỳ trên bàn phím (hoặc gõ mã phím tắt) rồi bấm **Lưu phím tắt**.
4. Phím tắt mới sẽ có hiệu lực ngay lập tức trong toàn bộ hệ thống!

---

## ⌨️ Phím tắt khi mở ClipMaster

| Phím tắt | Tác vụ |
| :--- | :--- |
| **Win + V** (`Super + V`) | Mở hoặc đóng ClipMaster từ bất kỳ đâu |
| **Mũi tên Lên / Xuống** | Di chuyển lựa chọn giữa các mục |
| **Enter** | Sao chép mục đã chọn & tự động dán |
| **Ctrl + F** | Mở rộng thanh tìm kiếm và focus ô nhập |
| **Ctrl + N** | Tạo ghi chú mới nhanh chóng |
| **Delete** | Xóa mục đang được chọn |
| **Esc** | Thu gọn tìm kiếm / Quay lại từ màn hình PIN / Đóng cửa sổ |

---

## 📁 Cấu trúc thư mục dự án

```
clipMaster/
├── clipmaster.py            # Điểm khởi chạy chính của ứng dụng
├── install.sh               # Script cài đặt tự động 1-click
├── uninstall.sh             # Script gỡ cài đặt
├── build_deb.sh             # Script đóng gói thành file cài .deb
├── snap/
│   ├── snapcraft.yaml       # Cấu hình đóng gói Snapcraft (Snap Store)
│   └── gui/                 # Desktop launcher và icon cho Snap
├── assets/
│   ├── icon.svg             # Icon vector của ứng dụng
│   └── style.css            # Giao diện CSS tùy biến (Dark/Light card design)
└── src/
    ├── database.py          # Quản lý cơ sở dữ liệu SQLite lưu lịch sử & ghi chú
    ├── clipboard_manager.py # Bộ theo dõi và đồng bộ clipboard ngầm
    ├── sync_manager.py      # Bộ đồng bộ hóa Cloud / BYOS (Upload, Download, 2-way)
    ├── shortcut_manager.py  # Đăng ký phím tắt Win+V với GNOME
    ├── theme_manager.py     # Quản lý Dark/Light/System theme qua Libadwaita
    ├── i18n.py              # Đa ngôn ngữ (Tiếng Việt & English)
    ├── utils.py             # Phân loại định dạng & format thời gian
    └── ui/
        ├── main_window.py       # Cửa sổ chính Adw.ApplicationWindow
        ├── history_item_row.py  # Card hiển thị từng mục clipboard
        ├── note_item_row.py     # Card hiển thị từng mục ghi chú
        ├── note_editor_dialog.py # Dialog tạo & chỉnh sửa ghi chú
        ├── pin_dialog.py        # Dialog cài đặt & đổi mã PIN bảo mật
        ├── sync_setup_dialog.py # Dialog cấu hình đồng bộ hóa Cloud/BYOS
        ├── settings_dialog.py   # Cửa sổ tùy chọn và cấu hình
        └── shortcut_dialog.py   # Dialog ghi nhận phím tắt bàn phím
```

---

## 🛠️ Dịch vụ nền (Systemd)

- Xem trạng thái dịch vụ ngầm:
  ```bash
  systemctl --user status clipmaster.service
  ```
- Khởi động lại dịch vụ:
  ```bash
  systemctl --user restart clipmaster.service
  ```
- Dừng dịch vụ:
  ```bash
  systemctl --user stop clipmaster.service
  ```

---

## 🗑️ Gỡ cài đặt
Nếu không muốn sử dụng nữa, bạn chỉ cần chạy:
```bash
./uninstall.sh
```
Mọi phím tắt và dịch vụ nền sẽ được khôi phục về mặc định nguyên bản của hệ thống.

---
---

# 🇬🇧 English

**ClipMaster** is a premium clipboard history manager for Ubuntu and Linux (GNOME / Zorin OS / Debian), bringing the seamless, intuitive **Windows + V** experience to your Linux desktop.

---

## ✨ Features

- ⚡ **Global Shortcut Win + V (`Super + V`)**: Press `Win + V` anywhere on your desktop to toggle the clipboard history popup.
- 🎨 **Modern Interface & Dark Mode (GTK4 + Libadwaita)**: Gorgeous rounded card aesthetics with full support for **Dark Mode**, **Light Mode**, and **System Default**. Quick theme toggle button right on the header bar!
- 📝 **Dedicated Personal Notes & Floating Action Button (FAB)**:
  - Keep important notes separate from clipboard history via seamless tab switching (`📋 History` & `📝 Notes`).
  - Floating Action Button (FAB) `+` in the bottom-right corner for rapid note creation (`Ctrl + N`).
  - Pin, edit, 1-click copy, or delete notes effortlessly.
- 🔒 **4-Digit PIN Security for Notes**:
  - Optional 4-digit PIN protection to keep your private notes secure.
  - Sleek lock screen with on-screen numeric keypad and hardware keyboard support.
  - Configurable auto-lock timeout: Immediately upon switching tabs, 1 minute, 5 minutes, 15 minutes, 30 minutes, or on app exit.
  - **Brute-force lockout**: Automatically triggers a 30-second live countdown lock after every 3 consecutive incorrect PIN attempts.
- ☁️ **Cloud & BYOS (Bring Your Own Server) Synchronization**:
  - Sync both clipboard history and notes across multiple machines via custom server or cloud backends.
  - 3 flexible sync modes: **Two-way Sync (Upload & Download)**, **Upload Only**, or **Download Only**.
  - Automatic database schema bootstrapping on fresh server setups upon first connection.
- 🔍 **Unified Single-Row Search & Filter Bar**:
  - Search button `[ 🔍 ]` and filter chips combined into a single compact row to maximize vertical reading area.
  - Positioned at the start of the row, clicking the search icon or pressing `Ctrl + F` smoothly expands into a full search bar; pressing `Esc` or clearing focus collapses it back.
- 🏷️ **Smart Content Detection**:
  - 📝 **Plain Text**: Displays character and line count.
  - 💻 **Source Code**: Recognizes programming syntax, rendered in monospace typography.
  - 🔗 **Links (URL)**: Extracts domain names (`github.com`, `google.com`...).
  - 🎨 **Color Codes (HEX / RGB / HSL)**: Displays an interactive preview color swatch (`#3B82F6`, `rgb(...)`).
  - 🖼️ **Images & Screenshots**: Automatically saves and previews thumbnail images.
- 📌 **Pin Important Items**: Pinned clips will never be cleared during automated pruning or history cleanup.
- 🚀 **Auto-paste**: Click any item or press Enter to copy it to clipboard and automatically paste into your active application.
- 🌐 **Multilingual (English & Vietnamese)**: Switch seamlessly between English and Vietnamese in Settings or via CLI.
- ⏸️ **Privacy Mode (Pause Auto-recording)**: One-click toggle to pause recording when copying passwords, OTP tokens, or confidential data.
- 🧹 **Smart Pruning**: Configurable history limits and one-click bulk deletion of unpinned items.
- ⚙️ **Ultra Lightweight**: Backed by secure SQLite storage, consuming under 15MB RAM and near-zero CPU when idle.

---

## 🚀 Installation & Getting Started

### Method 1: Automated Script Installation
```bash
./install.sh
```
This script will automatically:
1. Grant execute permissions and terminate older background processes.
2. Register the **Win + V** global shortcut in GNOME Settings.
3. Create the ClipMaster application desktop launcher and icon.
4. Enable and start the systemd user daemon on login.

---

### Method 2: Build Debian Package (`.deb`)
If you want to package ClipMaster into a `.deb` installer to share with other machines:
```bash
./build_deb.sh
```
Then install the generated package:
```bash
sudo apt install ./clipmaster_1.0.0_all.deb
```

---

### Method 3: Build & Install via Snap (Snapcraft / Snap Store)
Snap configuration is pre-configured in the `snap/` directory:
- **Build `.snap` package using Snapcraft:**
  ```bash
  snapcraft
  ```
- **Install `.snap` package locally:**
  ```bash
  sudo snap install clipmaster_1.0.0_amd64.snap --dangerous
  ```
- **Register and publish to Snap Store:**
  ```bash
  snapcraft login
  snapcraft register clipmaster
  snapcraft upload clipmaster_1.0.0_amd64.snap --release=stable
  ```

---

### Method 4: Command Line Interface (CLI)

- **Toggle history popup window:**
  ```bash
  python3 clipmaster.py --toggle
  ```
- **Switch to Dark Mode:**
  ```bash
  python3 clipmaster.py --theme dark
  ```
- **Switch to Light Mode:**
  ```bash
  python3 clipmaster.py --theme light
  ```
- **Follow system color scheme:**
  ```bash
  python3 clipmaster.py --theme system
  ```
- **Quick toggle between Dark and Light:**
  ```bash
  python3 clipmaster.py --toggle-theme
  ```
- **Set interface language to English:**
  ```bash
  python3 clipmaster.py --set-lang en
  ```
- **Set interface language to Vietnamese:**
  ```bash
  python3 clipmaster.py --set-lang vi
  ```
- **Pause clipboard recording (Privacy mode):**
  ```bash
  python3 clipmaster.py --pause
  ```
- **Resume clipboard recording:**
  ```bash
  python3 clipmaster.py --resume
  ```
- **Toggle auto-recording on/off:**
  ```bash
  python3 clipmaster.py --toggle-record
  ```
- **Inspect current status and shortcut:**
  ```bash
  python3 clipmaster.py --status
  ```
- **Set a custom shortcut via CLI (e.g. Ctrl + Alt + V):**
  ```bash
  python3 clipmaster.py --set-shortcut '<Control><Alt>v'
  ```
- **Reset to default shortcut Win + V:**
  ```bash
  python3 clipmaster.py --set-shortcut '<Super>v'
  ```
- **Clear all unpinned items:**
  ```bash
  python3 clipmaster.py --clear
  ```

---

## ⚙️ Customize Shortcuts in GUI

You can customize your activation shortcut anytime inside the app:
1. Open ClipMaster via your shortcut or run `python3 clipmaster.py --toggle`.
2. Click the **⚙️ Settings** icon in the top right corner.
3. Under **System Shortcut**:
   - Choose a popular preset: `Win + V`, `Ctrl + Alt + V`, `Ctrl + Shift + V`, `Alt + V`, `Win + Shift + V`...
   - Or click **"Change shortcut..."**: press any key combination on your keyboard (or enter GNOME accelerator string) and click **Save Shortcut**.
4. The new shortcut takes effect immediately across your entire system!

---

## ⌨️ Keyboard Navigation

| Shortcut | Action |
| :--- | :--- |
| **Win + V** (`Super + V`) | Toggle ClipMaster from anywhere |
| **Up / Down Arrows** | Navigate through history items |
| **Enter** | Copy selected clip & auto-paste |
| **Ctrl + F** | Expand search bar and focus input |
| **Ctrl + N** | Create a new personal note |
| **Delete** | Delete the selected clip |
| **Esc** | Collapse search / Return from PIN screen / Close window |

---

## 📁 Project Structure

```
clipMaster/
├── clipmaster.py            # Application entry point
├── install.sh               # 1-click automated installer
├── uninstall.sh             # Clean uninstaller
├── build_deb.sh             # Debian package builder
├── snap/
│   ├── snapcraft.yaml       # Snapcraft package configuration (Snap Store)
│   └── gui/                 # Desktop launcher and application icon for Snap
├── assets/
│   ├── icon.svg             # High-resolution vector icon
│   └── style.css            # Custom stylesheet (Dark/Light card design)
└── src/
    ├── database.py          # SQLite history, notes, and preferences database
    ├── clipboard_manager.py # Background clipboard monitor and daemon
    ├── sync_manager.py      # Cloud / BYOS sync engine (Upload, Download, 2-way)
    ├── shortcut_manager.py  # GNOME global shortcut binding
    ├── theme_manager.py     # Libadwaita Dark/Light/System theme manager
    ├── i18n.py              # Internationalization (Vietnamese & English)
    ├── utils.py             # Content type heuristics and formatters
    └── ui/
        ├── main_window.py       # Main Adw.ApplicationWindow
        ├── history_item_row.py  # Card row rendering component
        ├── note_item_row.py     # Note card row rendering component
        ├── note_editor_dialog.py # Note editor modal dialog
        ├── pin_dialog.py        # 4-digit PIN setup and change dialog
        ├── sync_setup_dialog.py # Cloud & BYOS sync configuration modal
        ├── settings_dialog.py   # Preferences window
        └── shortcut_dialog.py   # Interactive shortcut recorder dialog
```

---

## 🛠️ Systemd Service Management

- Check background daemon status:
  ```bash
  systemctl --user status clipmaster.service
  ```
- Restart daemon:
  ```bash
  systemctl --user restart clipmaster.service
  ```
- Stop daemon:
  ```bash
  systemctl --user stop clipmaster.service
  ```

---

## 🗑️ Uninstallation
To completely remove ClipMaster:
```bash
./uninstall.sh
```
All system shortcuts, desktop entries, and background services will be removed cleanly.
