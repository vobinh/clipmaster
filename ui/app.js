/**
 * ClipMaster - Cross-Platform Modern Frontend Controller
 * Tauri v2 IPC Bridge & Interactive UI Logic & RemixIcon Design System
 */

// ── IPC Abstraction Layer ──────────────────────────────────────────
function getTauri() {
  return typeof window.__TAURI__ !== 'undefined' ? window.__TAURI__ : null;
}

function getTauriInvoke() {
  const tauri = getTauri();
  if (!tauri) return null;
  if (tauri.core && typeof tauri.core.invoke === 'function') {
    return tauri.core.invoke;
  }
  if (typeof tauri.invoke === 'function') {
    return tauri.invoke;
  }
  return null;
}

async function invoke(command, args = {}) {
  const tauriInvoke = getTauriInvoke();
  if (tauriInvoke) {
    try {
      return await tauriInvoke(command, args);
    } catch (err) {
      console.error(`[IPC Error] ${command}:`, err);
      throw err;
    }
  } else {
    console.warn(`[Fallback] Tauri core not detected for command: ${command}`);
    return mockInvoke(command, args);
  }
}

// In-memory mock for testing in browser without Tauri backend
const mockStore = {
  clips: [
    { id: 1, type: "code", content: "git checkout -b feature/rust-tauri\ngit push -u origin feature/rust-tauri", is_pinned: 1, created_at: Date.now() / 1000 - 120, updated_at: Date.now() / 1000 - 120 },
    { id: 2, type: "url", content: "https://tauri.app/v2/guides/getting-started/", is_pinned: 0, created_at: Date.now() / 1000 - 600, updated_at: Date.now() / 1000 - 600 },
    { id: 3, type: "color", content: "#3b82f6", is_pinned: 0, created_at: Date.now() / 1000 - 1800, updated_at: Date.now() / 1000 - 1800 },
    { id: 4, type: "text", content: "ClipMaster - Trình quản lý Clipboard đa nền tảng tối ưu hiệu năng cao bằng Rust và Tauri v2.", is_pinned: 0, created_at: Date.now() / 1000 - 7200, updated_at: Date.now() / 1000 - 7200 },
    { id: 5, type: "image", content: null, image_width: 320, image_height: 180, is_pinned: 0, created_at: Date.now() / 1000 - 300, updated_at: Date.now() / 1000 - 300 }
  ],
  notes: [
    { id: 1, title: "Lệnh build nhanh", content: "cargo tauri build\ncargo tauri dev", is_pinned: 1, color: "#3b82f6", created_at: Date.now() / 1000 - 3600, updated_at: Date.now() / 1000 - 3600 }
  ],
  settings: {
    max_history: "200",
    auto_paste: "1",
    theme_mode: "dark",
    notes_pin_enabled: "0",
    notes_pin_hash: "",
    language: "vi"
  }
};

async function mockInvoke(cmd, args) {
  switch (cmd) {
    case 'get_clips': {
      let res = [...mockStore.clips];
      const filter = args.filterType || args.filter_type || 'all';
      if (filter === 'pinned') res = res.filter(c => c.is_pinned === 1);
      else if (filter !== 'all') res = res.filter(c => c.type === filter);
      if (args.query) res = res.filter(c => (c.content || "").toLowerCase().includes(args.query.toLowerCase()));
      return res.sort((a, b) => (b.is_pinned - a.is_pinned) || (b.updated_at - a.updated_at));
    }
    case 'get_clip_image': {
      return "data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='180' viewBox='0 0 320 180'%3E%3Crect width='320' height='180' fill='%231e293b' rx='8'/%3E%3Ccircle cx='160' cy='75' r='28' fill='%236366f1'/%3E%3Cpath d='M146 75l10-10 10 10 14-14' stroke='white' stroke-width='3' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3Ctext x='160' y='130' fill='%2394a3b8' font-family='sans-serif' font-size='13' text-anchor='middle'%3EClipMaster Image (320 × 180)%3C/text%3E%3C/svg%3E";
    }
    case 'get_notes': {
      let res = [...mockStore.notes];
      const filterPinned = args.filterPinned ?? args.filter_pinned;
      if (filterPinned) res = res.filter(n => n.is_pinned === 1);
      if (args.query) res = res.filter(n => (n.title || "").toLowerCase().includes(args.query.toLowerCase()) || n.content.toLowerCase().includes(args.query.toLowerCase()));
      return res.sort((a, b) => (b.is_pinned - a.is_pinned) || (b.updated_at - a.updated_at));
    }
    case 'copy_clip':
    case 'copy_text':
      navigator.clipboard?.writeText(args.text || mockStore.clips.find(c => c.id === args.id)?.content || "");
      return;
    case 'toggle_pin_clip': {
      const c = mockStore.clips.find(i => i.id === args.id);
      if (c) c.is_pinned = c.is_pinned ? 0 : 1;
      return !!c?.is_pinned;
    }
    case 'delete_clip':
      mockStore.clips = mockStore.clips.filter(c => c.id !== args.id);
      return true;
    case 'clear_unpinned': {
      const initLen = mockStore.clips.length;
      mockStore.clips = mockStore.clips.filter(c => c.is_pinned === 1);
      return initLen - mockStore.clips.length;
    }
    case 'get_stats':
      return { total: mockStore.clips.length, pinned: mockStore.clips.filter(c => c.is_pinned === 1).length };
    case 'save_note': {
      if (args.id) {
        const n = mockStore.notes.find(i => i.id === args.id);
        if (n) {
          n.title = args.title;
          n.content = args.content;
          n.color = args.color;
          n.updated_at = Date.now() / 1000;
          return n.id;
        }
      }
      const newId = Date.now();
      mockStore.notes.unshift({ id: newId, title: args.title, content: args.content, is_pinned: 0, color: args.color, created_at: Date.now() / 1000, updated_at: Date.now() / 1000 });
      return newId;
    }
    case 'delete_note':
      mockStore.notes = mockStore.notes.filter(n => n.id !== args.id);
      return true;
    case 'toggle_pin_note': {
      const n = mockStore.notes.find(i => i.id === args.id);
      if (n) n.is_pinned = n.is_pinned ? 0 : 1;
      return !!n?.is_pinned;
    }
    case 'is_notes_pin_enabled':
      return mockStore.settings.notes_pin_enabled === "1";
    case 'has_notes_pin':
      return !!(mockStore.settings.pin || mockStore.settings.notes_pin_hash);
    case 'verify_notes_pin':
      return args.pin === "1234" || args.pin === mockStore.settings.pin;
    case 'set_notes_pin':
      mockStore.settings.notes_pin_enabled = "1";
      mockStore.settings.pin = args.pin;
      return true;
    case 'change_notes_pin': {
      const hasPin = !!(mockStore.settings.pin || mockStore.settings.notes_pin_hash);
      const oldPin = args.oldPin || args.old_pin;
      const newPin = args.newPin || args.new_pin;
      if (hasPin) {
        if (!oldPin || (oldPin !== "1234" && oldPin !== mockStore.settings.pin)) {
          throw new Error("Mã PIN hiện tại không chính xác!");
        }
      }
      if (!newPin || newPin.length !== 4 || !/^\d{4}$/.test(newPin)) {
        throw new Error("Mã PIN phải gồm đúng 4 chữ số (0-9)!");
      }
      mockStore.settings.notes_pin_enabled = "1";
      mockStore.settings.pin = newPin;
      return true;
    }
    case 'disable_notes_pin':
      mockStore.settings.notes_pin_enabled = "0";
      return;
    case 'get_setting':
      return mockStore.settings[args.key] || args.default_val || "";
    case 'set_setting':
      mockStore.settings[args.key] = args.value;
      return;
    case 'get_all_settings':
      return { ...mockStore.settings };
    case 'reset_settings':
      mockStore.settings = { max_history: "200", auto_paste: "1", theme_mode: "dark", accent_color: "indigo", notes_pin_enabled: "0", language: "vi" };
      return;
    case 'set_autostart':
      mockStore.settings.autostart = args.enabled ? "1" : "0";
      return;
    case 'test_sync_connection':
      return "Đã kết nối máy chủ đồng bộ thử nghiệm thành công!";
    case 'toggle_clipboard_pause':
      mockStore.is_paused = !mockStore.is_paused;
      return mockStore.is_paused;
    case 'is_clipboard_paused':
      return !!mockStore.is_paused;
    case 'open_url':
      window.open(args.url, '_blank');
      return;
    case 'drag_window':
      return;
    case 'hide_window':
    case 'close_window':
      console.log(`[Window Action] ${cmd}`);
      return;
    default:
      return null;
  }
}

// ── i18n Translation Engine ─────────────────────────────────────────
let currentLang = 'vi';

function t(key, params = {}) {
  const dict = (window.I18N && window.I18N[currentLang]) || (window.I18N && window.I18N['vi']) || {};
  let text = dict[key] !== undefined ? dict[key] : key;
  if (typeof text === 'string') {
    Object.keys(params).forEach(param => {
      text = text.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
    });
  }
  return text;
}

function applyLanguage(lang) {
  currentLang = (lang === 'en' || lang === 'vi') ? lang : 'vi';
  document.documentElement.setAttribute('lang', currentLang);

  // 1. Static text elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key) el.textContent = t(key);
  });

  // 2. Tooltips with data-i18n-title
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    if (key) el.title = t(key);
  });

  // 3. Placeholders with data-i18n-placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (key) el.placeholder = t(key);
  });

  // 4. Dynamic Mode Subtitle & Search Placeholder
  if (state.mode === 'notes') {
    DOM.appSubtitle.textContent = t('app_subtitle_notes');
    DOM.searchInput.placeholder = t('search_notes_placeholder');
  } else {
    DOM.appSubtitle.textContent = t('app_subtitle');
    DOM.searchInput.placeholder = t('search_placeholder');
  }

  // 5. Dynamic Empty State Texts
  if (state.currentItems.length === 0) {
    if (state.mode === 'history') {
      DOM.emptyTitle.textContent = t('empty_history_title');
      DOM.emptyDesc.textContent = state.searchQuery 
        ? t('empty_history_search') 
        : t('empty_history_desc');
    } else {
      DOM.emptyTitle.textContent = t('empty_notes_title');
      DOM.emptyDesc.textContent = state.searchQuery 
        ? t('empty_notes_search') 
        : t('empty_notes_desc');
    }
  }

  // 6. Security PIN Settings status label
  const elPinStatus = document.getElementById('setting-pin-status');
  const elPinToggle = document.getElementById('setting-pin-toggle');
  if (elPinStatus && elPinToggle) {
    elPinStatus.textContent = elPinToggle.checked ? t('pin_status_on') : t('pin_status_off');
  }

  // 7. Select options text in settings
  const elThemeDark = document.querySelector('#setting-theme-mode option[value="dark"]');
  const elThemeLight = document.querySelector('#setting-theme-mode option[value="light"]');
  if (elThemeDark) elThemeDark.textContent = t('theme_dark');
  if (elThemeLight) elThemeLight.textContent = t('theme_light');

  const historyOpts = {
    "50": t('opt_50_items'),
    "100": t('opt_100_items'),
    "200": t('opt_200_items'),
    "500": t('opt_500_items'),
    "1000": t('opt_1000_items')
  };
  Object.keys(historyOpts).forEach(val => {
    const opt = document.querySelector(`#setting-max-history option[value="${val}"]`);
    if (opt) opt.textContent = historyOpts[val];
  });

  const pinTimeoutOpts = {
    "60": t('pin_time_60'),
    "300": t('pin_time_300'),
    "900": t('pin_time_900'),
    "1800": t('pin_time_1800'),
    "0": t('pin_time_close')
  };
  Object.keys(pinTimeoutOpts).forEach(val => {
    const opt = document.querySelector(`#setting-pin-timeout option[value="${val}"]`);
    if (opt) opt.textContent = pinTimeoutOpts[val];
  });

  const syncDirOpts = {
    "bidirectional": t('sync_dir_both'),
    "push_only": t('sync_dir_push'),
    "pull_only": t('sync_dir_pull')
  };
  Object.keys(syncDirOpts).forEach(val => {
    const opt = document.querySelector(`#setting-sync-direction option[value="${val}"]`);
    if (opt) opt.textContent = syncDirOpts[val];
  });

  // 8. Sync setting language dropdown value
  const elLang = document.getElementById('setting-language');
  if (elLang) elLang.value = currentLang;

  // Sync Pause Button Tooltip
  if (DOM.btnPause) {
    DOM.btnPause.title = state.isPaused ? t('tooltip_resume') : t('tooltip_pause');
  }

  // 9. Re-render current items & footer status for localized time badges & tooltips
  if (state.mode === 'history') {
    if (state.currentItems.length > 0) renderHistoryCards(state.currentItems);
    updateFooterStatusHistory();
  } else {
    if (state.currentItems.length > 0) renderNoteCards(state.currentItems);
    updateFooterStatusNotes();
  }

  // 10. Update Sync Status text if configured
  const syncStatusText = document.getElementById('sync-status-text');
  const settingUrl = document.getElementById('setting-sync-url');
  if (syncStatusText && settingUrl && settingUrl.value.trim()) {
    syncStatusText.innerHTML = '<i class="ri-checkbox-circle-fill" style="color: #10b981; margin-right: 4px;"></i> <span>' + escapeHtml(t('sync_connected_status', 'Đã kết nối Supabase BYOS:') + ' ' + settingUrl.value.trim()) + '</span>';
  }
}

// ── Theme & Accent Management ───────────────────────────────────────
function updateThemeUI(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('icon-theme');
  if (icon) {
    icon.className = theme === 'dark' ? 'ri-moon-line' : 'ri-sun-line';
  }
}

function updateAccentColorUI(colorId) {
  const validColors = ['indigo', 'emerald', 'ocean', 'rose', 'amber', 'violet'];
  const color = validColors.includes(colorId) ? colorId : 'indigo';
  state.accentColor = color;
  document.documentElement.setAttribute('data-accent', color);

  const dots = document.querySelectorAll('.theme-color-dot');
  dots.forEach(dot => {
    dot.classList.toggle('active', dot.dataset.color === color);
  });
}

function setupAccentColorPicker() {
  const palette = document.getElementById('theme-color-palette');
  if (!palette) return;

  palette.addEventListener('click', async (e) => {
    const dot = e.target.closest('.theme-color-dot');
    if (!dot) return;

    const color = dot.dataset.color;
    if (color) {
      updateAccentColorUI(color);
      await invoke('set_setting', { key: 'accent_color', value: color });
    }
  });
}

// ── Application State ──────────────────────────────────────────────
const state = {
  mode: 'history', // 'history' | 'notes'
  historyFilter: 'all',
  notesFilter: 'all',
  searchQuery: '',
  selectedIndex: -1,
  currentItems: [],
  notesUnlocked: false,
  pinBuffer: '',
  pinFailedAttempts: 0,
  lockoutTimer: null,
  lockoutRemaining: 0,
  activeNoteColor: '',
  accentColor: 'indigo',
  isPaused: false
};

// ── DOM References ─────────────────────────────────────────────────
const DOM = {
  statusIndicator: document.getElementById('status-indicator'),
  tabHistory: document.getElementById('tab-history'),
  tabNotes: document.getElementById('tab-notes'),
  historyFilters: document.getElementById('history-filters'),
  notesFilters: document.getElementById('notes-filters'),
  itemsList: document.getElementById('items-list'),
  emptyState: document.getElementById('empty-state'),
  emptyTitle: document.getElementById('empty-title'),
  emptyDesc: document.getElementById('empty-desc'),
  footerStatus: document.getElementById('footer-status'),
  appSubtitle: document.getElementById('app-subtitle'),
  
  // Search
  searchInput: document.getElementById('search-input'),
  btnSearchClear: document.getElementById('btn-search-clear'),

  // Header actions
  btnPause: document.getElementById('btn-pause'),
  iconPause: document.getElementById('icon-pause'),
  btnClear: document.getElementById('btn-clear'),
  btnTheme: document.getElementById('btn-theme'),
  btnSettings: document.getElementById('btn-settings'),
  btnClose: document.getElementById('btn-close'),

  // PIN lock
  pinLockScreen: document.getElementById('pin-lock-screen'),
  pinKeypad: document.getElementById('pin-keypad'),
  pinDots: [
    document.getElementById('dot-0'),
    document.getElementById('dot-1'),
    document.getElementById('dot-2'),
    document.getElementById('dot-3')
  ],
  pinErrorMsg: document.getElementById('pin-error-msg'),
  pinSubtitle: document.getElementById('pin-subtitle'),
  btnPinBack: document.getElementById('btn-pin-back'),

  // FAB
  btnFabCreateNote: document.getElementById('btn-fab-create-note'),

  // Scroll Navigation
  contentArea: document.querySelector('.content-area'),
  scrollNavGroup: document.getElementById('scroll-nav-group'),
  btnScrollTop: document.getElementById('btn-scroll-top'),
  btnScrollBottom: document.getElementById('btn-scroll-bottom'),

  // Modals
  modalNote: document.getElementById('modal-note'),
  modalNoteTitle: document.getElementById('modal-note-title'),
  noteId: document.getElementById('note-id'),
  noteInputTitle: document.getElementById('note-input-title'),
  noteInputContent: document.getElementById('note-input-content'),
  noteColorPicker: document.getElementById('note-color-picker'),
  btnCloseNoteModal: document.getElementById('btn-close-note-modal'),
  btnCancelNote: document.getElementById('btn-cancel-note'),
  btnSaveNote: document.getElementById('btn-save-note'),

  modalSettings: document.getElementById('modal-settings'),
  btnCloseSettingsModal: document.getElementById('btn-close-settings-modal'),
  settingMaxHistory: document.getElementById('setting-max-history'),
  settingAutoPaste: document.getElementById('setting-auto-paste'),
  settingNewPin: document.getElementById('setting-new-pin'),
  btnSetPin: document.getElementById('btn-set-pin'),
  btnDisablePin: document.getElementById('btn-disable-pin'),
  settingPinStatus: document.getElementById('setting-pin-status'),
  btnSaveSettings: document.getElementById('btn-save-settings'),

  // Toast
  toast: document.getElementById('toast'),
  toastText: document.getElementById('toast-text')
};

// ── Time & Formatting Helpers ──────────────────────────────────────
function formatRelativeTime(timestamp) {
  if (!timestamp) return "";
  const now = Date.now() / 1000;
  const diff = Math.max(0, now - timestamp);

  if (diff < 15) return t('time_just_now');
  if (diff < 60) return t('time_secs_ago', { secs: Math.floor(diff) });
  if (diff < 3600) return t('time_mins_ago', { mins: Math.floor(diff / 60) });
  if (diff < 86400) return t('time_hours_ago', { hours: Math.floor(diff / 3600) });
  
  const d = new Date(timestamp * 1000);
  const pad = n => n.toString().padStart(2, '0');
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatDate(timestamp) {
  if (!timestamp) return "";
  const ms = timestamp > 1e11 ? timestamp : timestamp * 1000;
  const d = new Date(ms);
  const pad = n => n.toString().padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
}

function localizeSyncMessage(msg) {
  if (!msg) return "";
  const s = String(msg).trim();
  if (s.includes("Kết nối Supabase BYOS thành công") || s.includes("Sẵn sàng đồng bộ") || s.toLowerCase().includes("ready to sync") || s.toLowerCase().includes("connected to supabase")) {
    return t('sync_test_success', 'Kết nối Supabase BYOS thành công! (Sẵn sàng đồng bộ)');
  }
  if (s.includes("Đồng bộ hoàn tất") || s.includes("mới nhất") || s.toLowerCase().includes("up to date")) {
    return t('sync_up_to_date', 'Đồng bộ hoàn tất: Dữ liệu đã đồng bộ mới nhất.');
  }
  if (s.includes("Đồng bộ thành công") || s.toLowerCase().includes("sync successful")) {
    const match = s.match(/\((.*?)\)/);
    if (match) {
      return `${t('toast_sync_success', 'Đồng bộ đám mây thành công!')} (${match[1]})`;
    }
    return t('toast_sync_success', 'Đồng bộ đám mây thành công!');
  }
  if (s.includes("Vui lòng cấu hình") || s.includes("Chưa cấu hình") || s.toLowerCase().includes("configure")) {
    return t('sync_missing_config', 'Vui lòng cấu hình URL và API Key trước khi đồng bộ.');
  }
  if (s.includes("đang bị tắt trong Cài đặt") || s.toLowerCase().includes("disabled in settings")) {
    return t('sync_disabled_error', 'Tính năng đồng bộ đám mây đang bị tắt trong Cài đặt.');
  }
  if (s.includes("TABLE_NOT_FOUND")) {
    return t('wizard_need_db', 'Kết nối thành công! Cần khởi tạo database...');
  }
  if (s.includes("RLS_BLOCKED")) {
    return t('wizard_rls_blocked', 'Bảng bị chặn ghi bởi Row Level Security (RLS). Cần cập nhật schema...');
  }
  return s.replace(/^Error:\s*/i, '');
}

let toastTimer = null;
function showToast(message, type = 'success') {
  if (!DOM.toast) return;
  const icon = document.getElementById('toast-icon');
  const toastMsg = (message && typeof message === 'string') ? message : t('toast_pin_saved');
  if (DOM.toastText) DOM.toastText.textContent = toastMsg;
  else DOM.toast.textContent = toastMsg;

  if (icon) {
    if (type === 'error') icon.className = 'ri-error-warning-fill';
    else if (type === 'info') icon.className = 'ri-information-fill';
    else icon.className = 'ri-check-circle-line';
  }

  DOM.toast.className = `toast show ${type}`;

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    DOM.toast.classList.remove('show');
  }, 2200);
}

// ── Reusable In-App Confirmation Modal ────────────────────────────
function showConfirmDialog({
  title = t('confirm_title'),
  message = '',
  confirmText = t('confirm_btn_ok'),
  cancelText = t('confirm_btn_cancel'),
  isDanger = true,
  onConfirm = null
} = {}) {
  const modal = document.getElementById('modal-confirm');
  if (!modal) return;
  const titleEl = document.getElementById('confirm-title');
  const descEl = document.getElementById('confirm-desc');
  const btnOk = document.getElementById('btn-confirm-ok');
  const btnCancel = document.getElementById('btn-confirm-cancel');
  const iconWrapper = document.getElementById('confirm-icon-wrapper');
  const icon = document.getElementById('confirm-icon');

  if (titleEl) titleEl.textContent = title;
  if (descEl) descEl.textContent = message;
  if (btnOk) btnOk.textContent = confirmText;
  if (btnCancel) btnCancel.textContent = cancelText;

  // Confirm button is always synchronized as primary
  if (btnOk) btnOk.className = 'btn-primary';

  if (isDanger) {
    if (iconWrapper) iconWrapper.className = 'confirm-icon-wrapper';
    if (icon) icon.className = 'ri-error-warning-fill';
  } else {
    if (iconWrapper) iconWrapper.className = 'confirm-icon-wrapper info';
    if (icon) icon.className = 'ri-information-fill';
  }

  modal.classList.remove('hidden');

  const cleanup = () => {
    modal.classList.add('hidden');
    btnOk.onclick = null;
    btnCancel.onclick = null;
  };

  btnCancel.onclick = () => cleanup();
  btnOk.onclick = async () => {
    cleanup();
    if (onConfirm) await onConfirm();
  };
}

// ── Data Loading & Rendering ───────────────────────────────────────
const clipImageCache = new Map();

async function loadCardImage(imgEl, id, placeholderEl) {
  if (clipImageCache.has(id)) {
    imgEl.src = clipImageCache.get(id);
    imgEl.classList.remove('hidden');
    if (placeholderEl) placeholderEl.classList.add('hidden');
    return;
  }

  try {
    const dataUri = await invoke('get_clip_image', { id });
    if (dataUri) {
      clipImageCache.set(id, dataUri);
      imgEl.src = dataUri;
      imgEl.classList.remove('hidden');
      if (placeholderEl) placeholderEl.classList.add('hidden');
    }
  } catch (err) {
    console.error("Failed to load clip image:", id, err);
    if (placeholderEl) {
      placeholderEl.innerHTML = `<i class="ri-image-line"></i> <span>${t('image_load_failed')}</span>`;
    }
  }
}

async function loadClips() {
  if (state.mode !== 'history') return;

  try {
    const clips = await invoke('get_clips', {
      filterType: state.historyFilter,
      filter_type: state.historyFilter,
      query: state.searchQuery,
      limit: 200,
      offset: 0
    });

    state.currentItems = clips || [];
    renderHistoryCards(state.currentItems);
    await updateFooterStatusHistory();
  } catch (err) {
    console.error("Failed to load clips:", err);
  }
}

async function updateFooterStatusHistory() {
  try {
    const stats = await invoke('get_stats');
    DOM.footerStatus.textContent = t('footer_clips_status', { total: stats?.total || 0, pinned: stats?.pinned || 0 });
  } catch (e) {
    const pinned = state.currentItems.filter(c => c.is_pinned).length;
    DOM.footerStatus.textContent = t('footer_clips_status', { total: state.currentItems.length, pinned });
  }
}

async function loadNotes() {
  if (state.mode !== 'notes') return;

  // Check if PIN lock is active
  const pinEnabled = await invoke('is_notes_pin_enabled');
  if (pinEnabled && !state.notesUnlocked) {
    showPinLockScreen();
    return;
  }

  hidePinLockScreen();

  try {
    const notes = await invoke('get_notes', {
      query: state.searchQuery,
      filterPinned: state.notesFilter === 'pinned',
      filter_pinned: state.notesFilter === 'pinned',
      limit: 200
    });

    state.currentItems = notes || [];
    renderNoteCards(state.currentItems);
    updateFooterStatusNotes();
  } catch (err) {
    console.error("Failed to load notes:", err);
  }
}

function updateFooterStatusNotes() {
  const pinnedCount = state.currentItems.filter(n => n.is_pinned).length;
  DOM.footerStatus.textContent = t('footer_notes_status', { total: state.currentItems.length, pinned: pinnedCount });
}

function renderHistoryCards(items) {
  DOM.itemsList.innerHTML = '';
  state.selectedIndex = -1;

  if (items.length === 0) {
    DOM.emptyState.classList.remove('hidden');
    DOM.emptyTitle.textContent = t('empty_history_title');
    DOM.emptyDesc.textContent = state.searchQuery 
      ? t('empty_history_search') 
      : t('empty_history_desc');
    updateScrollNavVisibility();
    return;
  }

  DOM.emptyState.classList.add('hidden');

  items.forEach((item, index) => {
    const card = document.createElement('div');
    card.className = `clip-card ${index === 0 ? 'selected' : ''}`;
    card.dataset.index = index;
    card.dataset.id = item.id;

    if (index === 0) state.selectedIndex = 0;

    let typeBadgeLabel = (item.type || "text").toUpperCase();
    let typeIcon = 'ri-text';
    if (item.type === 'code') typeIcon = 'ri-code-s-slash-line';
    else if (item.type === 'url') typeIcon = 'ri-link';
    else if (item.type === 'color') typeIcon = 'ri-palette-line';
    else if (item.type === 'image') typeIcon = 'ri-image-line';

    let previewHtml = '';
    if (item.type === 'color') {
      previewHtml = `
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="width: 16px; height: 16px; border-radius: 4px; background: ${escapeHtml(item.content)}; border: 1px solid rgba(255,255,255,0.2); display: inline-block;"></span>
          <span class="card-content font-mono">${escapeHtml(item.content)}</span>
        </div>`;
    } else if (item.type === 'code') {
      previewHtml = `
        <div class="card-code-wrapper">
          <div class="card-content code">${escapeHtml(item.content)}</div>
        </div>`;
    } else if (item.type === 'image') {
      const dimensions = (item.image_width && item.image_height) 
        ? `${item.image_width} × ${item.image_height} px` 
        : 'Image';
      const cached = clipImageCache.get(item.id);

      previewHtml = `
        <div class="card-image-wrapper">
          <div class="image-loading-placeholder ${cached ? 'hidden' : ''}">
            <i class="ri-loader-4-line"></i>
            <span>${t('image_loading')}</span>
          </div>
          <img class="card-image-preview ${cached ? '' : 'hidden'}" src="${cached || ''}" alt="Image preview" loading="lazy" />
          <div class="card-image-info">
            <span><i class="ri-image-line"></i> ${dimensions}</span>
          </div>
        </div>`;
    } else {
      previewHtml = `<div class="card-content">${escapeHtml(item.content || "")}</div>`;
    }

    const isUrl = item.type === 'url' || isLikelyUrl(item.content);
    const openLinkBtnHtml = isUrl ? `
      <button class="card-btn" data-action="open-link" title="${t('tooltip_open_link')}">
        <i class="ri-external-link-line"></i>
      </button>` : '';

    card.innerHTML = `
      <div class="card-header">
        <span class="card-badge"><i class="${typeIcon}"></i> ${typeBadgeLabel}</span>
        <span class="card-time">${formatRelativeTime(item.updated_at)}</span>
      </div>
      ${previewHtml}
      <div class="card-actions">
        ${openLinkBtnHtml}
        <button class="card-btn ${item.is_pinned ? 'pinned' : ''}" data-action="pin" title="${item.is_pinned ? t('tooltip_unpin') : t('tooltip_pin')}">
          <i class="${item.is_pinned ? 'ri-pushpin-fill' : 'ri-pushpin-line'}"></i>
        </button>
        <button class="card-btn" data-action="delete" title="${t('tooltip_delete')}">
          <i class="ri-delete-bin-line"></i>
        </button>
      </div>
    `;

    // Lazy load image preview if not already cached
    if (item.type === 'image') {
      const imgEl = card.querySelector('.card-image-preview');
      const placeholderEl = card.querySelector('.image-loading-placeholder');
      if (imgEl && !clipImageCache.has(item.id)) {
        loadCardImage(imgEl, item.id, placeholderEl);
      }
    }

    // Click on card body copies item
    card.addEventListener('click', async (e) => {
      if (e.target.closest('[data-action]')) return;
      selectCard(index);
      await copyItem(item.id);
    });

    // Pin button
    const btnPin = card.querySelector('[data-action="pin"]');
    btnPin.addEventListener('click', async (e) => {
      e.stopPropagation();
      await togglePinClip(item.id);
    });

    // Delete button
    const btnDel = card.querySelector('[data-action="delete"]');
    btnDel.addEventListener('click', async (e) => {
      e.stopPropagation();
      await deleteClip(item.id);
    });

    // Open Link button
    const btnOpenLink = card.querySelector('[data-action="open-link"]');
    if (btnOpenLink) {
      btnOpenLink.addEventListener('click', async (e) => {
        e.stopPropagation();
        await openLink(item.content);
      });
    }

    DOM.itemsList.appendChild(card);
  });
  updateScrollNavVisibility();
}

function renderNoteCards(notes) {
  DOM.itemsList.innerHTML = '';
  state.selectedIndex = -1;

  if (notes.length === 0) {
    DOM.emptyState.classList.remove('hidden');
    DOM.emptyTitle.textContent = t('empty_notes_title');
    DOM.emptyDesc.textContent = state.searchQuery 
      ? t('empty_notes_search') 
      : t('empty_notes_desc');
    updateScrollNavVisibility();
    return;
  }

  DOM.emptyState.classList.add('hidden');

  notes.forEach((note, index) => {
    const card = document.createElement('div');
    card.className = `clip-card ${index === 0 ? 'selected' : ''}`;
    card.dataset.index = index;
    card.dataset.id = note.id;

    if (note.color) {
      card.style.borderLeft = `3px solid ${note.color}`;
    }

    if (index === 0) state.selectedIndex = 0;

    const titleHtml = note.title ? `<div style="font-weight: 700; font-size: 13px; margin-bottom: 2px;">${escapeHtml(note.title)}</div>` : '';

    card.innerHTML = `
      <div class="card-header">
        <span class="card-badge" style="background: rgba(168, 85, 247, 0.12); color: #c084fc;"><i class="ri-sticky-note-line"></i> NOTE</span>
        <span class="card-time">${formatRelativeTime(note.updated_at)}</span>
      </div>
      ${titleHtml}
      <div class="card-content">${escapeHtml(note.content)}</div>
      <div class="card-actions">
        <button class="card-btn" data-action="edit" title="${t('tooltip_edit')}">
          <i class="ri-edit-line"></i>
        </button>
        <button class="card-btn ${note.is_pinned ? 'pinned' : ''}" data-action="pin" title="${note.is_pinned ? t('tooltip_unpin') : t('tooltip_pin')}">
          <i class="${note.is_pinned ? 'ri-pushpin-fill' : 'ri-pushpin-line'}"></i>
        </button>
        <button class="card-btn" data-action="delete" title="${t('tooltip_delete')}">
          <i class="ri-delete-bin-line"></i>
        </button>
      </div>
    `;

    // Click on note copies text
    card.addEventListener('click', async (e) => {
      if (e.target.closest('[data-action]')) return;
      selectCard(index);
      await invoke('copy_text', { text: note.content });
      showToast(t('toast_note_pasted'));
    });

    // Edit button
    card.querySelector('[data-action="edit"]').addEventListener('click', (e) => {
      e.stopPropagation();
      openNoteModal(note);
    });

    // Pin button
    card.querySelector('[data-action="pin"]').addEventListener('click', async (e) => {
      e.stopPropagation();
      await invoke('toggle_pin_note', { id: note.id });
      loadNotes();
    });

    // Delete button
    card.querySelector('[data-action="delete"]').addEventListener('click', async (e) => {
      e.stopPropagation();
      await invoke('delete_note', { id: note.id });
      loadNotes();
    });

    DOM.itemsList.appendChild(card);
  });
  updateScrollNavVisibility();
}

function selectCard(index) {
  const cards = DOM.itemsList.querySelectorAll('.clip-card');
  if (cards.length === 0) return;

  cards.forEach(c => c.classList.remove('selected'));
  state.selectedIndex = Math.max(0, Math.min(index, cards.length - 1));
  const target = cards[state.selectedIndex];
  if (target) {
    target.classList.add('selected');
    target.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }
}

async function copyItem(id) {
  try {
    const item = state.currentItems.find(c => c.id === id);
    await invoke('copy_clip', { id });
    if (item && item.type === 'image') {
      showToast(t('toast_image_copied'));
    } else {
      showToast(t('toast_copied'));
    }
  } catch (err) {
    console.error("Copy failed:", err);
  }
}

async function togglePinClip(id) {
  try {
    await invoke('toggle_pin_clip', { id });
    await loadClips();
  } catch (err) {
    console.error("Pin toggle failed:", err);
  }
}

async function deleteClip(id) {
  try {
    clipImageCache.delete(id);
    await invoke('delete_clip', { id });
    await loadClips();
  } catch (err) {
    console.error("Delete clip failed:", err);
  }
}

// ── Search & Filter Interactions ───────────────────────────────────
function setupSearchAndFilters() {
  let debounceTimer = null;

  DOM.searchInput.addEventListener('input', (e) => {
    const val = e.target.value;
    if (DOM.btnSearchClear) {
      if (val) DOM.btnSearchClear.classList.remove('hidden');
      else DOM.btnSearchClear.classList.add('hidden');
    }

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      state.searchQuery = val;
      triggerReload();
    }, 150);
  });

  if (DOM.btnSearchClear) {
    DOM.btnSearchClear.addEventListener('click', () => {
      DOM.searchInput.value = '';
      state.searchQuery = '';
      DOM.btnSearchClear.classList.add('hidden');
      DOM.searchInput.focus();
      triggerReload();
    });
  }

  // History Filter Chips
  DOM.historyFilters.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      DOM.historyFilters.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      chip.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
      state.historyFilter = chip.dataset.filter;
      loadClips();
    });
  });

  // Notes Filter Chips
  DOM.notesFilters.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      DOM.notesFilters.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      chip.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
      state.notesFilter = chip.dataset.filter;
      loadNotes();
    });
  });

  // Smooth horizontal mouse-wheel scrolling for Filter Chips
  const filterChipsScroll = document.getElementById('filter-chips-container');
  if (filterChipsScroll) {
    filterChipsScroll.addEventListener('wheel', (e) => {
      if (e.deltaY !== 0) {
        e.preventDefault();
        filterChipsScroll.scrollLeft += e.deltaY;
      }
    }, { passive: false });
  }
}

function triggerReload() {
  if (state.mode === 'history') loadClips();
  else loadNotes();
}

// ── Mode Switcher (History vs Notes) ───────────────────────────────
function setupModeSwitcher() {
  DOM.tabHistory.addEventListener('click', () => {
    if (state.mode === 'history') return;
    state.mode = 'history';
    DOM.tabHistory.classList.add('active');
    DOM.tabNotes.classList.remove('active');
    DOM.historyFilters.classList.remove('hidden');
    DOM.notesFilters.classList.add('hidden');
    DOM.btnFabCreateNote.classList.add('hidden');
    DOM.appSubtitle.textContent = t('app_subtitle');
    DOM.searchInput.placeholder = t('search_placeholder');
    hidePinLockScreen();
    loadClips();
    updateScrollNavVisibility();
  });

  DOM.tabNotes.addEventListener('click', () => {
    if (state.mode === 'notes') return;
    state.mode = 'notes';
    DOM.tabNotes.classList.add('active');
    DOM.tabHistory.classList.remove('active');
    DOM.historyFilters.classList.add('hidden');
    DOM.notesFilters.classList.remove('hidden');
    DOM.btnFabCreateNote.classList.remove('hidden');
    DOM.appSubtitle.textContent = t('app_subtitle_notes');
    DOM.searchInput.placeholder = t('search_notes_placeholder');
    loadNotes();
    updateScrollNavVisibility();
  });
}

// ── PIN Lock Screen Logic (4-Dot & 30s Lockout) ────────────────────
function showPinLockScreen() {
  DOM.pinLockScreen.classList.remove('hidden');
  DOM.itemsList.classList.add('hidden');
  DOM.emptyState.classList.add('hidden');
  DOM.btnFabCreateNote.classList.add('hidden');
  DOM.scrollNavGroup?.classList.add('hidden');
  state.pinBuffer = '';
  updatePinDots();
  DOM.pinErrorMsg.classList.add('hidden');
}

function hidePinLockScreen() {
  DOM.pinLockScreen.classList.add('hidden');
  DOM.itemsList.classList.remove('hidden');
  if (state.mode === 'notes') {
    DOM.btnFabCreateNote.classList.remove('hidden');
  }
  updateScrollNavVisibility();
}

function updatePinDots() {
  DOM.pinDots.forEach((dot, index) => {
    if (index < state.pinBuffer.length) {
      dot.classList.add('filled');
    } else {
      dot.classList.remove('filled');
      dot.classList.remove('error');
    }
  });
}

async function handlePinInput(digit) {
  if (state.lockoutRemaining > 0) return;
  if (state.pinBuffer.length >= 4) return;

  state.pinBuffer += digit;
  updatePinDots();

  if (state.pinBuffer.length === 4) {
    await verifyPinBuffer();
  }
}

async function verifyPinBuffer() {
  const pin = state.pinBuffer;
  const isValid = await invoke('verify_notes_pin', { pin });

  if (isValid) {
    state.notesUnlocked = true;
    state.pinFailedAttempts = 0;
    hidePinLockScreen();
    loadNotes();
  } else {
    state.pinFailedAttempts++;
    DOM.pinDots.forEach(dot => dot.classList.add('error'));

    if (state.pinFailedAttempts >= 3) {
      startLockoutTimer(30);
    } else {
      DOM.pinErrorMsg.textContent = t('pin_err_incorrect', { attempts: 3 - state.pinFailedAttempts });
      DOM.pinErrorMsg.classList.remove('hidden');
      setTimeout(() => {
        state.pinBuffer = '';
        updatePinDots();
      }, 500);
    }
  }
}

function startLockoutTimer(seconds) {
  state.lockoutRemaining = seconds;
  DOM.pinKeypad.querySelectorAll('button').forEach(b => b.disabled = true);

  clearInterval(state.lockoutTimer);
  state.lockoutTimer = setInterval(() => {
    state.lockoutRemaining--;
    if (state.lockoutRemaining <= 0) {
      clearInterval(state.lockoutTimer);
      state.pinFailedAttempts = 0;
      DOM.pinErrorMsg.classList.add('hidden');
      DOM.pinSubtitle.textContent = t('pin_subtitle');
      DOM.pinKeypad.querySelectorAll('button').forEach(b => b.disabled = false);
      state.pinBuffer = '';
      updatePinDots();
    } else {
      DOM.pinErrorMsg.textContent = t('pin_err_lockout', { seconds: state.lockoutRemaining });
      DOM.pinErrorMsg.classList.remove('hidden');
    }
  }, 1000);
}

function setupPinKeypad() {
  DOM.pinKeypad.addEventListener('click', (e) => {
    const keyBtn = e.target.closest('.key-btn');
    if (!keyBtn || keyBtn.disabled) return;

    const key = keyBtn.dataset.key;
    const action = keyBtn.dataset.action;

    if (key) {
      handlePinInput(key);
    } else if (action === 'clear') {
      state.pinBuffer = '';
      updatePinDots();
    } else if (action === 'backspace') {
      state.pinBuffer = state.pinBuffer.slice(0, -1);
      updatePinDots();
    }
  });

  DOM.btnPinBack.addEventListener('click', () => {
    DOM.tabHistory.click();
  });
}

// ── Note Modal (Create & Edit) ─────────────────────────────────────
function openNoteModal(note = null) {
  DOM.modalNote.classList.remove('hidden');
  if (note) {
    DOM.modalNoteTitle.textContent = t('modal_note_edit');
    DOM.noteId.value = note.id;
    DOM.noteInputTitle.value = note.title || '';
    DOM.noteInputContent.value = note.content || '';
    state.activeNoteColor = note.color || '';
  } else {
    DOM.modalNoteTitle.textContent = t('modal_note_new');
    DOM.noteId.value = '';
    DOM.noteInputTitle.value = '';
    DOM.noteInputContent.value = '';
    state.activeNoteColor = '';
  }

  // Set active color dot
  DOM.noteColorPicker.querySelectorAll('.color-dot-btn').forEach(dot => {
    if (dot.dataset.color === state.activeNoteColor) {
      dot.classList.add('selected');
    } else {
      dot.classList.remove('selected');
    }
  });

  setTimeout(() => DOM.noteInputContent.focus(), 50);
}

function closeNoteModal() {
  DOM.modalNote.classList.add('hidden');
}

function setupNoteModal() {
  DOM.btnFabCreateNote.addEventListener('click', () => openNoteModal());
  DOM.btnCloseNoteModal.addEventListener('click', closeNoteModal);
  DOM.btnCancelNote.addEventListener('click', closeNoteModal);

  DOM.noteColorPicker.addEventListener('click', (e) => {
    const dot = e.target.closest('.color-dot-btn');
    if (!dot) return;
    DOM.noteColorPicker.querySelectorAll('.color-dot-btn').forEach(d => d.classList.remove('selected'));
    dot.classList.add('selected');
    state.activeNoteColor = dot.dataset.color;
  });

  DOM.btnSaveNote.addEventListener('click', async () => {
    const content = DOM.noteInputContent.value.trim();
    if (!content) {
      showToast(t('alert_note_content_empty'), 'error');
      DOM.noteInputContent.focus();
      return;
    }

    const title = DOM.noteInputTitle.value.trim() || null;
    const id = DOM.noteId.value ? parseInt(DOM.noteId.value, 10) : null;
    const color = state.activeNoteColor || null;

    try {
      await invoke('save_note', { id, title, content, color });
      closeNoteModal();
      showToast(t('toast_note_saved'));
      loadNotes();
    } catch (err) {
      console.error("Save note failed:", err);
      showToast(err?.toString() || t('err_save_note', "Lỗi lưu ghi chú"), 'error');
    }
  });
}

// ── Settings Modal (Multi-Tab Preferences) ─────────────────────────
async function openSettingsModal() {
  DOM.modalSettings.classList.remove('hidden');

  let settings = {};
  try {
    settings = await invoke('get_all_settings') || {};
  } catch (err) {
    console.error("Failed to fetch all settings:", err);
  }

  // General tab
  const themeMode = settings.theme_mode || 'dark';
  const language = settings.language || currentLang || 'vi';
  const autostart = settings.autostart === '1';
  const accentColor = settings.accent_color || 'indigo';

  const elTheme = document.getElementById('setting-theme-mode');
  const elLang = document.getElementById('setting-language');
  const elAutostart = document.getElementById('setting-autostart');
  if (elTheme) elTheme.value = themeMode;
  if (elLang) elLang.value = language;
  if (elAutostart) elAutostart.checked = autostart;
  updateAccentColorUI(accentColor);

  // Storage tab
  const autoRecord = settings.auto_record !== '0';
  const autoPaste = settings.auto_paste !== '0';
  const saveImages = settings.save_images !== '0';
  const maxHistory = settings.max_history || '200';

  const elAutoRecord = document.getElementById('setting-auto-record');
  const elAutoPaste = document.getElementById('setting-auto-paste');
  const elSaveImages = document.getElementById('setting-save-images');
  const elMaxHistory = document.getElementById('setting-max-history');
  if (elAutoRecord) elAutoRecord.checked = autoRecord;
  if (elAutoPaste) elAutoPaste.checked = autoPaste;
  if (elSaveImages) elSaveImages.checked = saveImages;
  if (elMaxHistory) elMaxHistory.value = maxHistory;

  // Shortcut tab
  const shortcut = settings.shortcut || '<Super>v';
  const elShortcut = document.getElementById('setting-shortcut-preset');
  if (elShortcut) elShortcut.value = shortcut;

  // Security tab
  const pinEnabled = await invoke('is_notes_pin_enabled');
  const hasPin = await invoke('has_notes_pin');
  const pinTimeout = settings.notes_pin_timeout || '300';
  const elPinToggle = document.getElementById('setting-pin-toggle');
  const elPinTimeout = document.getElementById('setting-pin-timeout');
  const elPinStatus = document.getElementById('setting-pin-status');
  const rowChangePin = document.getElementById('row-change-pin');

  if (elPinToggle) elPinToggle.checked = pinEnabled;
  if (elPinTimeout) elPinTimeout.value = pinTimeout;
  if (elPinStatus) {
    elPinStatus.textContent = pinEnabled ? t('pin_status_on') : t('pin_status_off');
    elPinStatus.style.color = pinEnabled ? "var(--success)" : "var(--text-tertiary)";
  }
  if (rowChangePin) {
    rowChangePin.style.display = hasPin ? 'flex' : 'none';
  }

  // Sync tab
  const syncToggle = settings.sync_enabled === '1';
  const syncUrl = settings.sync_url || '';
  const syncToken = settings.sync_token || '';
  const syncDirection = settings.sync_direction || 'bidirectional';
  const elSyncToggle = document.getElementById('setting-sync-toggle');
  const elSyncUrl = document.getElementById('setting-sync-url');
  const elSyncToken = document.getElementById('setting-sync-token');
  const elSyncDirection = document.getElementById('setting-sync-direction');
  if (elSyncToggle) elSyncToggle.checked = syncToggle;
  if (elSyncUrl) elSyncUrl.value = syncUrl;
  if (elSyncToken) elSyncToken.value = syncToken;
  if (elSyncDirection) elSyncDirection.value = syncDirection;

  const lastSyncAt = parseFloat(settings.last_sync_at || '0');
  updateSyncTabViews(syncUrl, syncToggle, lastSyncAt);
}

function updateSyncTabViews(syncUrl, syncEnabled, lastSyncAt = 0) {
  const unconfiguredView = document.getElementById('sync-unconfigured-view');
  const configuredView = document.getElementById('sync-configured-view');
  const urlValEl = document.getElementById('sync-info-url-val');
  const lastValEl = document.getElementById('sync-info-last-val');
  const syncToggle = document.getElementById('setting-sync-toggle');

  const isConfigured = Boolean(syncUrl && syncUrl.trim() && syncEnabled);

  if (unconfiguredView) unconfiguredView.classList.toggle('hidden', isConfigured);
  if (configuredView) configuredView.classList.toggle('hidden', !isConfigured);

  if (isConfigured) {
    if (urlValEl) urlValEl.textContent = syncUrl;
    if (lastValEl) {
      lastValEl.textContent = lastSyncAt > 0 ? formatDate(lastSyncAt) : t('time_just_now', 'Vừa xong');
    }
    if (syncToggle) syncToggle.checked = true;
  }
}

function closeSettingsModal() {
  DOM.modalSettings.classList.add('hidden');
}

// ── PIN Dialog Modal Logic (Set / Change PIN) ─────────────────────
let pinDialogState = {
  hasExistingPin: false,
  onSaved: null,
  onCancelled: null
};

function openPinDialog({ hasExistingPin = false, onSaved = null, onCancelled = null } = {}) {
  pinDialogState = { hasExistingPin, onSaved, onCancelled };

  const modal = document.getElementById('modal-pin');
  const titleEl = document.getElementById('pin-modal-title');
  const groupCurrent = document.getElementById('group-pin-current');
  const errorBox = document.getElementById('pin-modal-error');
  const errorText = document.getElementById('pin-modal-error-text');
  const inputCurrent = document.getElementById('pin-input-current');
  const inputNew = document.getElementById('pin-input-new');
  const inputConfirm = document.getElementById('pin-input-confirm');

  if (!modal) return;

  if (titleEl) {
    titleEl.textContent = hasExistingPin ? t('pin_dlg_title_change') : t('pin_dlg_title_set');
  }

  if (groupCurrent) {
    groupCurrent.style.display = hasExistingPin ? 'flex' : 'none';
  }

  if (inputCurrent) inputCurrent.value = '';
  if (inputNew) inputNew.value = '';
  if (inputConfirm) inputConfirm.value = '';

  // Reset peek states to password
  [inputCurrent, inputNew, inputConfirm].forEach(inp => {
    if (inp) inp.type = 'password';
  });
  modal.querySelectorAll('.btn-peek i').forEach(icon => {
    icon.className = 'ri-eye-line';
  });

  if (errorBox) errorBox.classList.add('hidden');
  if (errorText) errorText.textContent = '';

  modal.classList.remove('hidden');

  setTimeout(() => {
    if (hasExistingPin && inputCurrent) inputCurrent.focus();
    else if (inputNew) inputNew.focus();
  }, 60);
}

function closePinDialog(cancelled = false) {
  const modal = document.getElementById('modal-pin');
  if (modal) modal.classList.add('hidden');
  if (cancelled && pinDialogState.onCancelled) {
    pinDialogState.onCancelled();
  }
}

function showPinModalError(msg, focusEl = null) {
  const errorBox = document.getElementById('pin-modal-error');
  const errorText = document.getElementById('pin-modal-error-text');
  if (errorText) errorText.textContent = msg;
  if (errorBox) {
    errorBox.classList.remove('hidden');
    errorBox.style.animation = 'none';
    errorBox.offsetHeight;
    errorBox.style.animation = '';
  }
  if (focusEl) focusEl.focus();
}

function setupPinDialog() {
  const btnClose = document.getElementById('btn-close-pin-modal');
  const btnCancel = document.getElementById('btn-cancel-pin');
  const btnSave = document.getElementById('btn-save-pin-modal');
  const inputCurrent = document.getElementById('pin-input-current');
  const inputNew = document.getElementById('pin-input-new');
  const inputConfirm = document.getElementById('pin-input-confirm');

  if (btnClose) btnClose.addEventListener('click', () => closePinDialog(true));
  if (btnCancel) btnCancel.addEventListener('click', () => closePinDialog(true));

  // Restrict inputs to 4 digits & handle Enter to submit
  [inputCurrent, inputNew, inputConfirm].forEach(inp => {
    if (!inp) return;
    inp.addEventListener('input', (e) => {
      e.target.value = e.target.value.replace(/\D/g, '').slice(0, 4);
    });
    inp.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (btnSave) btnSave.click();
      }
    });
  });

  // Peek buttons (eye toggle)
  document.querySelectorAll('.btn-peek').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.dataset.target;
      const targetInput = document.getElementById(targetId);
      const icon = btn.querySelector('i');
      if (targetInput && icon) {
        if (targetInput.type === 'password') {
          targetInput.type = 'text';
          icon.className = 'ri-eye-off-line';
        } else {
          targetInput.type = 'password';
          icon.className = 'ri-eye-line';
        }
      }
    });
  });

  // Save PIN button
  if (btnSave) {
    btnSave.addEventListener('click', async () => {
      const errorBox = document.getElementById('pin-modal-error');
      if (errorBox) errorBox.classList.add('hidden');

      // 1. If hasExistingPin: check current PIN
      if (pinDialogState.hasExistingPin) {
        const curVal = inputCurrent.value.trim();
        if (!curVal) {
          showPinModalError(t('pin_dlg_err_current_empty'), inputCurrent);
          return;
        }
        const isOk = await invoke('verify_notes_pin', { pin: curVal });
        if (!isOk) {
          showPinModalError(t('pin_dlg_err_current'), inputCurrent);
          return;
        }
      }

      // 2. Check new PIN length
      const newVal = inputNew.value.trim();
      if (newVal.length !== 4 || !/^\d{4}$/.test(newVal)) {
        showPinModalError(t('pin_dlg_err_len'), inputNew);
        return;
      }

      // 3. Check confirm PIN
      const confVal = inputConfirm.value.trim();
      if (newVal !== confVal) {
        showPinModalError(t('pin_dlg_err_mismatch'), inputConfirm);
        return;
      }

      // 4. Save new PIN via backend
      try {
        const oldVal = pinDialogState.hasExistingPin ? inputCurrent.value.trim() : null;
        await invoke('change_notes_pin', {
          oldPin: oldVal,
          old_pin: oldVal,
          newPin: newVal,
          new_pin: newVal
        });

        closePinDialog(false);

        // Refresh settings UI
        const elPinStatus = document.getElementById('setting-pin-status');
        const elPinToggle = document.getElementById('setting-pin-toggle');
        const rowChangePin = document.getElementById('row-change-pin');
        if (elPinStatus) {
          elPinStatus.textContent = t('pin_status_on');
          elPinStatus.style.color = "var(--success)";
        }
        if (elPinToggle) elPinToggle.checked = true;
        if (rowChangePin) rowChangePin.style.display = 'flex';

        if (pinDialogState.onSaved) {
          await pinDialogState.onSaved();
        } else {
          showToast(pinDialogState.hasExistingPin ? t('toast_pin_changed') : t('toast_pin_saved'));
        }
      } catch (err) {
        showPinModalError(err?.toString() || "Lỗi lưu mã PIN", inputNew);
      }
    });
  }
}

function setupSettingsModal() {
  DOM.btnSettings.addEventListener('click', openSettingsModal);
  DOM.btnCloseSettingsModal.addEventListener('click', closeSettingsModal);

  // Tab navigation
  const navTabs = document.getElementById('settings-nav-tabs');
  if (navTabs) {
    navTabs.addEventListener('click', (e) => {
      const btn = e.target.closest('.settings-nav-btn');
      if (!btn) return;
      navTabs.querySelectorAll('.settings-nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });

      const tabId = btn.dataset.tab;
      document.querySelectorAll('[id^="tab-pane-"]').forEach(pane => pane.classList.add('hidden'));
      const activePane = document.getElementById(`tab-pane-${tabId}`);
      if (activePane) activePane.classList.remove('hidden');
    });

    // Smooth horizontal mouse-wheel scrolling for Settings Nav Tabs
    navTabs.addEventListener('wheel', (e) => {
      if (e.deltaY !== 0) {
        e.preventDefault();
        navTabs.scrollLeft += e.deltaY;
      }
    }, { passive: false });
  }

  // Theme switch inside settings immediately reflects
  const elTheme = document.getElementById('setting-theme-mode');
  if (elTheme) {
    elTheme.addEventListener('change', async () => {
      const val = elTheme.value;
      updateThemeUI(val);
      await invoke('set_setting', { key: 'theme_mode', value: val });
    });
  }

  // Language switch inside settings immediately reflects
  const elLang = document.getElementById('setting-language');
  if (elLang) {
    elLang.addEventListener('change', async () => {
      const newLang = elLang.value;
      applyLanguage(newLang);
      await invoke('set_setting', { key: 'language', value: newLang });
      showToast(t('toast_settings_saved'));
    });
  }

  // Open Change PIN Dialog button
  const btnOpenPinDialog = document.getElementById('btn-open-pin-dialog');
  if (btnOpenPinDialog) {
    btnOpenPinDialog.addEventListener('click', () => {
      openPinDialog({
        hasExistingPin: true,
        onSaved: () => {
          showToast(t('toast_pin_changed'));
        }
      });
    });
  }

  // PIN Toggle switch
  const elPinToggle = document.getElementById('setting-pin-toggle');
  if (elPinToggle) {
    elPinToggle.addEventListener('change', async () => {
      const elPinStatus = document.getElementById('setting-pin-status');
      const rowChangePin = document.getElementById('row-change-pin');

      if (!elPinToggle.checked) {
        await invoke('disable_notes_pin');
        state.notesUnlocked = true;
        if (elPinStatus) {
          elPinStatus.textContent = t('pin_status_off');
          elPinStatus.style.color = "var(--text-tertiary)";
        }
        showToast(t('toast_pin_disabled'));
      } else {
        const hasPin = await invoke('has_notes_pin');
        if (hasPin) {
          await invoke('set_setting', { key: 'notes_pin_enabled', value: '1' });
          if (elPinStatus) {
            elPinStatus.textContent = t('pin_status_on');
            elPinStatus.style.color = "var(--success)";
          }
          if (rowChangePin) rowChangePin.style.display = 'flex';
          showToast(t('toast_pin_enabled'));
        } else {
          openPinDialog({
            hasExistingPin: false,
            onSaved: () => {
              elPinToggle.checked = true;
              if (elPinStatus) {
                elPinStatus.textContent = t('pin_status_on');
                elPinStatus.style.color = "var(--success)";
              }
              if (rowChangePin) rowChangePin.style.display = 'flex';
              showToast(t('toast_pin_saved'));
            },
            onCancelled: () => {
              elPinToggle.checked = false;
            }
          });
        }
      }
    });
  }


  // Test Sync Connection
  const btnTestSync = document.getElementById('btn-test-sync');
  if (btnTestSync) {
    btnTestSync.addEventListener('click', async () => {
      const statusText = document.getElementById('sync-status-text');
      if (statusText) statusText.textContent = t('sync_status_testing', 'Đang kiểm tra kết nối máy chủ Supabase...');

      try {
        const rawMsg = await invoke('test_sync_connection');
        const msg = localizeSyncMessage(rawMsg);
        showToast(msg, 'success');
        if (statusText) statusText.textContent = msg;
      } catch (err) {
        const rawErr = err?.toString() || '';
        const errMsg = localizeSyncMessage(rawErr) || t('sync_test_failed', 'Lỗi kiểm tra kết nối');
        showToast(errMsg, 'error');
        if (statusText) statusText.textContent = errMsg;
      }
    });
  }

  // Sync Now Button
  const btnSyncNow = document.getElementById('btn-sync-now');
  if (btnSyncNow) {
    btnSyncNow.addEventListener('click', async () => {
      const syncToggle = document.getElementById('setting-sync-toggle');
      const syncDirection = document.getElementById('setting-sync-direction')?.value || 'bidirectional';

      if (syncToggle) syncToggle.checked = true;
      await invoke('set_setting', { key: 'sync_enabled', value: '1' });
      await invoke('set_setting', { key: 'sync_direction', value: syncDirection });

      const statusText = document.getElementById('sync-status-text');
      if (statusText) statusText.textContent = t('sync_status_syncing', 'Đang tiến hành đồng bộ dữ liệu đám mây...');

      try {
        const rawMsg = await invoke('sync_now');
        const msg = localizeSyncMessage(rawMsg);
        showToast(msg, 'success');
        if (statusText) statusText.textContent = msg;
        const lastValEl = document.getElementById('sync-info-last-val');
        if (lastValEl) lastValEl.textContent = t('time_just_now', 'Vừa xong');
        await loadClips();
        if (state.mode === 'notes') await loadNotes();
      } catch (err) {
        const rawErr = err?.toString() || '';
        const errMsg = localizeSyncMessage(rawErr) || t('toast_sync_failed', 'Lỗi đồng bộ đám mây!');
        showToast(errMsg, 'error');
        if (statusText) statusText.textContent = errMsg;
      }
    });
  }

  // Maintenance: Clear unpinned
  const btnSettingsClear = document.getElementById('btn-settings-clear-unpinned');
  if (btnSettingsClear) {
    btnSettingsClear.addEventListener('click', () => {
      showConfirmDialog({
        title: t('confirm_title'),
        message: t('confirm_clear_unpinned'),
        onConfirm: async () => {
          const removed = await invoke('clear_unpinned');
          showToast(t('toast_cleaned', { count: removed }));
          await loadClips();
        }
      });
    });
  }

  // Maintenance: Reset defaults
  const btnReset = document.getElementById('btn-reset-defaults');
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      showConfirmDialog({
        title: t('confirm_title'),
        message: t('confirm_reset_settings'),
        onConfirm: async () => {
          await invoke('reset_settings');
          applyLanguage('vi');
          updateThemeUI('dark');
          showToast(t('toast_defaults_restored'));
          closeSettingsModal();
          await loadClips();
        }
      });
    });
  }

  // Save & Close Settings
  DOM.btnSaveSettings.addEventListener('click', async () => {
    const elTheme = document.getElementById('setting-theme-mode');
    const elLang = document.getElementById('setting-language');
    const elAutostart = document.getElementById('setting-autostart');
    const elAutoRecord = document.getElementById('setting-auto-record');
    const elAutoPaste = document.getElementById('setting-auto-paste');
    const elSaveImages = document.getElementById('setting-save-images');
    const elMaxHistory = document.getElementById('setting-max-history');
    const elShortcut = document.getElementById('setting-shortcut-preset');
    const elPinTimeout = document.getElementById('setting-pin-timeout');
    const elSyncToggle = document.getElementById('setting-sync-toggle');
    const elSyncUrl = document.getElementById('setting-sync-url');
    const elSyncToken = document.getElementById('setting-sync-token');
    const elSyncDirection = document.getElementById('setting-sync-direction');

    if (elTheme) {
      updateThemeUI(elTheme.value);
      await invoke('set_setting', { key: 'theme_mode', value: elTheme.value });
    }
    if (state.accentColor) {
      await invoke('set_setting', { key: 'accent_color', value: state.accentColor });
    }
    if (elLang) {
      const langVal = elLang.value;
      applyLanguage(langVal);
      await invoke('set_setting', { key: 'language', value: langVal });
    }
    if (elAutostart) await invoke('set_autostart', { enabled: elAutostart.checked });
    if (elAutoRecord) await invoke('set_setting', { key: 'auto_record', value: elAutoRecord.checked ? '1' : '0' });
    if (elAutoPaste) await invoke('set_setting', { key: 'auto_paste', value: elAutoPaste.checked ? '1' : '0' });
    if (elSaveImages) await invoke('set_setting', { key: 'save_images', value: elSaveImages.checked ? '1' : '0' });
    if (elMaxHistory) await invoke('set_setting', { key: 'max_history', value: elMaxHistory.value });
    if (elShortcut) await invoke('set_setting', { key: 'shortcut', value: elShortcut.value });
    if (elPinTimeout) await invoke('set_setting', { key: 'notes_pin_timeout', value: elPinTimeout.value });
    if (elSyncToggle) await invoke('set_setting', { key: 'sync_enabled', value: elSyncToggle.checked ? '1' : '0' });
    if (elSyncUrl) await invoke('set_setting', { key: 'sync_url', value: elSyncUrl.value.trim() });
    if (elSyncToken) await invoke('set_setting', { key: 'sync_token', value: elSyncToken.value.trim() });
    if (elSyncDirection) await invoke('set_setting', { key: 'sync_direction', value: elSyncDirection.value });

    closeSettingsModal();
    showToast(t('toast_settings_saved'));
  });
}

// ── BYOS Sync Setup Wizard ─────────────────────────────────────────
function setupSyncWizard() {
  const wizardModal = document.getElementById('modal-sync-wizard');
  if (!wizardModal) return;

  const btnOpenWizard = document.getElementById('btn-open-sync-wizard');
  const btnCloseWizard = document.getElementById('btn-close-sync-wizard');

  const stepInd1 = document.getElementById('wizard-step-ind-1');
  const stepInd2 = document.getElementById('wizard-step-ind-2');
  const stepInd3 = document.getElementById('wizard-step-ind-3');
  const stepLine1 = document.getElementById('wizard-line-1');
  const stepLine2 = document.getElementById('wizard-line-2');

  const page1 = document.getElementById('wizard-page-1');
  const page2 = document.getElementById('wizard-page-2');
  const page3 = document.getElementById('wizard-page-3');

  const inputUrl = document.getElementById('wizard-input-url');
  const inputKey = document.getElementById('wizard-input-key');
  const inputPat = document.getElementById('wizard-input-pat');

  const step1Status = document.getElementById('wizard-step1-status');
  const step2Status = document.getElementById('wizard-step2-status');

  const btnOpenDashboard = document.getElementById('btn-wizard-open-dashboard');
  const btnStep1Next = document.getElementById('btn-wizard-step1-next');
  const btnStep2Back = document.getElementById('btn-wizard-step2-back');
  const btnOpenPatGuide = document.getElementById('btn-wizard-open-pat-guide');
  const btnStep2Setup = document.getElementById('btn-wizard-step2-setup');
  const btnFinish = document.getElementById('btn-wizard-finish');

  function setStep(stepNum) {
    if (page1) page1.classList.toggle('hidden', stepNum !== 1);
    if (page2) page2.classList.toggle('hidden', stepNum !== 2);
    if (page3) page3.classList.toggle('hidden', stepNum !== 3);

    if (stepInd1) stepInd1.className = 'wizard-step-item' + (stepNum === 1 ? ' active' : (stepNum > 1 ? ' completed' : ''));
    if (stepInd2) stepInd2.className = 'wizard-step-item' + (stepNum === 2 ? ' active' : (stepNum > 2 ? ' completed' : ''));
    if (stepInd3) stepInd3.className = 'wizard-step-item' + (stepNum === 3 ? ' active completed' : '');

    if (stepLine1) stepLine1.className = 'wizard-step-line' + (stepNum > 1 ? ' completed' : '');
    if (stepLine2) stepLine2.className = 'wizard-step-line' + (stepNum > 2 ? ' completed' : '');
  }

  function setStep1Status(text, type = '') {
    if (!step1Status) return;
    step1Status.className = 'wizard-status-msg' + (type ? ' ' + type : '');
    if (!text) {
      step1Status.innerHTML = '';
      return;
    }
    let iconHtml = '';
    if (type === 'loading') iconHtml = '<i class="ri-loader-4-line spin" style="margin-right: 5px; vertical-align: -1px;"></i>';
    else if (type === 'success') iconHtml = '<i class="ri-checkbox-circle-fill" style="margin-right: 5px; vertical-align: -1px;"></i>';
    else if (type === 'error') iconHtml = '<i class="ri-error-warning-fill" style="margin-right: 5px; vertical-align: -1px;"></i>';

    step1Status.innerHTML = iconHtml + escapeHtml(text);
  }

  function setStep2Status(text, type = '') {
    if (!step2Status) return;
    step2Status.className = 'wizard-status-msg' + (type ? ' ' + type : '');
    if (!text) {
      step2Status.innerHTML = '';
      return;
    }
    let iconHtml = '';
    if (type === 'loading') iconHtml = '<i class="ri-loader-4-line spin" style="margin-right: 5px; vertical-align: -1px;"></i>';
    else if (type === 'success') iconHtml = '<i class="ri-checkbox-circle-fill" style="margin-right: 5px; vertical-align: -1px;"></i>';
    else if (type === 'error') iconHtml = '<i class="ri-error-warning-fill" style="margin-right: 5px; vertical-align: -1px;"></i>';

    step2Status.innerHTML = iconHtml + escapeHtml(text);
  }

  function openSyncWizard() {
    const currentUrl = document.getElementById('setting-sync-url')?.value.trim() || '';
    const currentToken = document.getElementById('setting-sync-token')?.value.trim() || '';
    if (inputUrl) inputUrl.value = currentUrl;
    if (inputKey) inputKey.value = currentToken;
    if (inputPat) inputPat.value = '';

    setStep1Status('');
    setStep2Status('');
    if (btnStep1Next) btnStep1Next.disabled = false;
    if (btnStep2Setup) btnStep2Setup.disabled = false;

    setStep(1);
    wizardModal.classList.remove('hidden');
    setTimeout(() => inputUrl?.focus(), 50);
  }

  function closeSyncWizard() {
    wizardModal.classList.add('hidden');
    if (inputPat) inputPat.value = ''; // Ensure PAT is wiped from memory
  }

  if (btnOpenWizard) {
    btnOpenWizard.addEventListener('click', openSyncWizard);
  }

  if (btnCloseWizard) {
    btnCloseWizard.addEventListener('click', closeSyncWizard);
  }

  if (btnOpenDashboard) {
    btnOpenDashboard.addEventListener('click', async () => {
      try {
        await invoke('open_url', { url: 'https://supabase.com/dashboard' });
      } catch (e) {
        window.open('https://supabase.com/dashboard', '_blank');
      }
    });
  }

  if (btnOpenPatGuide) {
    btnOpenPatGuide.addEventListener('click', async () => {
      try {
        await invoke('open_url', { url: 'https://supabase.com/dashboard/account/tokens' });
      } catch (e) {
        window.open('https://supabase.com/dashboard/account/tokens', '_blank');
      }
    });
  }

  // Step 1: Test connection & check if database exists
  if (btnStep1Next) {
    btnStep1Next.addEventListener('click', async () => {
      const url = inputUrl?.value.trim() || '';
      const key = inputKey?.value.trim() || '';

      if (!url || !key) {
        setStep1Status(t('wizard_err_missing_info', 'Vui lòng nhập đầy đủ URL và Anon API Key.'), 'error');
        return;
      }

      setStep1Status(t('wizard_testing', 'Đang kiểm tra kết nối...'), 'loading');
      btnStep1Next.disabled = true;

      try {
        await invoke('test_sync_connection', { url, key });

        // Both tables exist and write test passed!
        setStep1Status(t('wizard_test_ok', 'Kết nối thành công!'), 'success');

        await finalizeSyncConnection(url, key);

        setTimeout(() => {
          showDonePage(url);
        }, 500);

      } catch (err) {
        btnStep1Next.disabled = false;
        const errMsg = err?.toString() || '';

        if (errMsg.includes('TABLE_NOT_FOUND') || errMsg.includes('RLS_BLOCKED')) {
          if (errMsg.includes('RLS_BLOCKED')) {
            setStep1Status(t('wizard_rls_blocked', 'Bảng bị chặn ghi bởi Row Level Security (RLS). Cần cập nhật schema...'), 'error');
          } else {
            setStep1Status(t('wizard_need_db', 'Kết nối thành công! Cần khởi tạo database...'), 'success');
          }

          // Auto-advance to Step 2 (Database Setup) after 600ms
          setTimeout(() => {
            setStep(2);
            setTimeout(() => inputPat?.focus(), 60);
          }, 600);
        } else {
          setStep1Status(errMsg.replace(/^Error:\s*/, '') || 'Lỗi kiểm tra kết nối', 'error');
        }
      }
    });
  }

  // Step 2: Back button
  if (btnStep2Back) {
    btnStep2Back.addEventListener('click', () => {
      setStep(1);
      if (btnStep1Next) btnStep1Next.disabled = false;
    });
  }

  // Step 2: Auto setup schema using PAT
  if (btnStep2Setup) {
    btnStep2Setup.addEventListener('click', async () => {
      const url = inputUrl?.value.trim() || '';
      const key = inputKey?.value.trim() || '';
      const pat = inputPat?.value.trim() || '';

      if (!pat) {
        setStep2Status(t('wizard_err_missing_pat', 'Vui lòng nhập Personal Access Token (PAT).'), 'error');
        return;
      }

      setStep2Status(t('wizard_creating_db', 'Đang tạo bảng dữ liệu...'), 'loading');
      btnStep2Setup.disabled = true;

      try {
        await invoke('auto_setup_sync_schema', { url, pat });

        setStep2Status(t('wizard_create_ok', 'Bảng đã được tạo thành công!'), 'success');
        if (inputPat) inputPat.value = ''; // Discard PAT immediately

        await finalizeSyncConnection(url, key);

        setTimeout(() => {
          showDonePage(url);
        }, 600);

      } catch (err) {
        btnStep2Setup.disabled = false;
        const errMsg = err?.toString() || 'Lỗi khởi tạo bảng';
        setStep2Status(errMsg.replace(/^Error:\s*/, ''), 'error');
      }
    });
  }

  async function finalizeSyncConnection(url, key) {
    await invoke('set_setting', { key: 'sync_enabled', value: '1' });
    await invoke('set_setting', { key: 'sync_url', value: url });
    await invoke('set_setting', { key: 'sync_token', value: key });

    const settingToggle = document.getElementById('setting-sync-toggle');
    const settingUrl = document.getElementById('setting-sync-url');
    const settingToken = document.getElementById('setting-sync-token');
    const syncStatusText = document.getElementById('sync-status-text');

    if (settingToggle) settingToggle.checked = true;
    if (settingUrl) settingUrl.value = url;
    if (settingToken) settingToken.value = key;
    if (syncStatusText) {
      syncStatusText.innerHTML = '<i class="ri-checkbox-circle-fill" style="color: #10b981; margin-right: 4px;"></i> <span>' + escapeHtml(t('sync_connected_status', 'Đã kết nối Supabase BYOS:') + " " + url) + '</span>';
    }

    // Switch to configured view
    updateSyncTabViews(url, true, Date.now() / 1000);

    // Trigger background initial sync
    try {
      invoke('sync_now').then(async () => {
        await loadClips();
        if (state.mode === 'notes') await loadNotes();
      }).catch(e => console.warn("Background initial sync notice:", e));
    } catch (e) {
      console.warn("Background initial sync notice:", e);
    }
  }

  function showDonePage(url) {
    const doneUrlEl = document.getElementById('wizard-done-project-url');
    if (doneUrlEl) doneUrlEl.textContent = url;
    setStep(3);
  }

  // Reconfigure sync button
  const btnReconfigure = document.getElementById('btn-reconfigure-sync');
  if (btnReconfigure) {
    btnReconfigure.addEventListener('click', openSyncWizard);
  }

  // Disconnect sync button
  const btnDisconnect = document.getElementById('btn-disconnect-sync');
  if (btnDisconnect) {
    btnDisconnect.addEventListener('click', () => {
      showConfirmDialog({
        title: t('btn_disconnect_sync', 'Ngắt kết nối'),
        message: t('confirm_disconnect_sync', 'Bạn có chắc chắn muốn ngắt kết nối đồng bộ đám mây? Dữ liệu cục bộ trên máy vẫn sẽ được giữ nguyên.'),
        onConfirm: async () => {
          await invoke('set_setting', { key: 'sync_enabled', value: '0' });
          await invoke('set_setting', { key: 'sync_url', value: '' });
          await invoke('set_setting', { key: 'sync_token', value: '' });

          const elSyncUrl = document.getElementById('setting-sync-url');
          const elSyncToken = document.getElementById('setting-sync-token');
          if (elSyncUrl) elSyncUrl.value = '';
          if (elSyncToken) elSyncToken.value = '';
          if (inputUrl) inputUrl.value = '';
          if (inputKey) inputKey.value = '';

          updateSyncTabViews('', false, 0);
          showToast(t('toast_sync_disconnected', 'Đã ngắt kết nối đồng bộ đám mây!'));
        }
      });
    });
  }

  if (btnFinish) {
    btnFinish.addEventListener('click', () => {
      closeSyncWizard();
      showToast(t('toast_sync_success', 'Đồng bộ đám mây thành công!'));
    });
  }

  window.closeSyncWizard = closeSyncWizard;
}

// ── Global Keyboard Navigation ─────────────────────────────────────
function setupKeyboardNavigation() {
  window.addEventListener('keydown', async (e) => {
    // If modal is open, let user type inside inputs
    const isModalOpen = !DOM.modalNote.classList.contains('hidden') 
      || !DOM.modalSettings.classList.contains('hidden')
      || !document.getElementById('modal-pin')?.classList.contains('hidden')
      || !document.getElementById('modal-sync-wizard')?.classList.contains('hidden')
      || !document.getElementById('modal-confirm')?.classList.contains('hidden');

    if (isModalOpen) {
      if (e.key === 'Escape') {
        closeNoteModal();
        closeSettingsModal();
        closePinDialog(true);
        if (window.closeSyncWizard) window.closeSyncWizard();
        document.getElementById('modal-confirm')?.classList.add('hidden');
      }
      return;
    }

    // PIN lock screen typing
    if (!DOM.pinLockScreen.classList.contains('hidden')) {
      if (/^[0-9]$/.test(e.key)) {
        handlePinInput(e.key);
      } else if (e.key === 'Backspace') {
        state.pinBuffer = state.pinBuffer.slice(0, -1);
        updatePinDots();
      } else if (e.key === 'Escape') {
        DOM.tabHistory.click();
      }
      return;
    }

    // Ctrl + F search shortcut
    if ((e.ctrlKey || e.metaKey) && (e.key === 'f' || e.key === 'F')) {
      e.preventDefault();
      DOM.searchInput.focus();
      DOM.searchInput.select();
      return;
    }

    // Ctrl + N new note shortcut
    if ((e.ctrlKey || e.metaKey) && (e.key === 'n' || e.key === 'N')) {
      e.preventDefault();
      if (state.mode !== 'notes') DOM.tabNotes.click();
      openNoteModal();
      return;
    }

    // Escape clears search or hides window
    if (e.key === 'Escape') {
      if (DOM.searchInput.value) {
        DOM.searchInput.value = '';
        state.searchQuery = '';
        if (DOM.btnSearchClear) DOM.btnSearchClear.classList.add('hidden');
        triggerReload();
      } else {
        await invoke('hide_window');
      }
      return;
    }

    // Don't intercept arrow keys if focused on search input
    if (document.activeElement === DOM.searchInput) {
      if (e.key === 'ArrowDown') {
        DOM.searchInput.blur();
        selectCard(0);
      }
      return;
    }

    // Arrow navigation
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectCard(state.selectedIndex + 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectCard(state.selectedIndex - 1);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (state.selectedIndex >= 0 && state.currentItems[state.selectedIndex]) {
        const item = state.currentItems[state.selectedIndex];
        if (state.mode === 'history') {
          await copyItem(item.id);
        } else {
          await invoke('copy_text', { text: item.content });
          showToast(t('toast_note_pasted'));
        }
      }
    } else if (e.key === 'Delete') {
      e.preventDefault();
      if (state.selectedIndex >= 0 && state.currentItems[state.selectedIndex]) {
        const item = state.currentItems[state.selectedIndex];
        if (state.mode === 'history') {
          await deleteClip(item.id);
        } else {
          await invoke('delete_note', { id: item.id });
          loadNotes();
        }
      }
    }
  });
}

// ── Header Actions & Utilities ─────────────────────────────────────
function setupHeaderActions() {
  DOM.btnClose.addEventListener('click', async () => {
    await invoke('hide_window');
  });

  DOM.btnClear.addEventListener('click', () => {
    showConfirmDialog({
      title: t('confirm_title'),
      message: t('confirm_clear_unpinned'),
      onConfirm: async () => {
        const removed = await invoke('clear_unpinned');
        showToast(t('toast_cleaned', { count: removed }));
        await loadClips();
      }
    });
  });

  // Dark / Light Theme
  DOM.btnTheme.addEventListener('click', async () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    updateThemeUI(nextTheme);
    await invoke('set_setting', { key: 'theme_mode', value: nextTheme });
  });

  // Pause / Resume Clipboard Monitoring
  setupPauseButton();

  // Native Window Dragging
  setupWindowDrag();
}

function setupPauseButton() {
  if (DOM.btnPause) {
    DOM.btnPause.addEventListener('click', async () => {
      try {
        const isPaused = await invoke('toggle_clipboard_pause');
        updatePauseUI(isPaused);
        showToast(isPaused ? t('toast_clipboard_paused') : t('toast_clipboard_resumed'));
      } catch (e) {
        console.error("Toggle pause error:", e);
      }
    });
  }
}

function updatePauseUI(isPaused) {
  state.isPaused = isPaused;
  const iconPause = document.getElementById('icon-pause');
  const indicator = document.getElementById('status-indicator');

  if (DOM.btnPause && iconPause) {
    if (isPaused) {
      iconPause.className = 'ri-play-circle-line';
      DOM.btnPause.title = t('tooltip_resume');
      DOM.btnPause.classList.add('paused');
      if (indicator) {
        indicator.className = 'status-indicator paused';
        indicator.title = currentLang === 'en' ? "Clipboard monitoring paused" : "Đã tạm dừng theo dõi clipboard";
      }
    } else {
      iconPause.className = 'ri-pause-circle-line';
      DOM.btnPause.title = t('tooltip_pause');
      DOM.btnPause.classList.remove('paused');
      if (indicator) {
        indicator.className = 'status-indicator active';
        indicator.title = currentLang === 'en' ? "Clipboard monitoring active" : "Đang theo dõi bộ nhớ tạm";
      }
    }
  }
}

function setupWindowDrag() {
  const header = document.querySelector('.header-bar');
  if (header) {
    header.addEventListener('mousedown', (e) => {
      // Don't drag if clicking buttons, inputs or icons
      if (e.target.closest('button') || e.target.closest('input') || e.target.closest('select') || e.target.closest('.icon-btn')) {
        return;
      }
      if (e.button === 0) { // Primary left mouse button
        invoke('drag_window').catch(() => {});
      }
    });
  }
}

// ── Listen for System Clipboard Events ─────────────────────────────
function setupClipboardListener() {
  const tauri = getTauri();
  if (tauri && tauri.event && typeof tauri.event.listen === 'function') {
    tauri.event.listen('clipboard_changed', (event) => {
      console.log("[Clipboard Event] New clip detected:", event);
      if (state.mode === 'history') {
        loadClips();
      }
    });
  }
}

// ── Floating Scroll Navigation ─────────────────────────────────────
function updateScrollNavVisibility() {
  if (!DOM.scrollNavGroup || !DOM.contentArea) return;

  const isPinLocked = DOM.pinLockScreen && !DOM.pinLockScreen.classList.contains('hidden');
  const isEmpty = DOM.emptyState && !DOM.emptyState.classList.contains('hidden');

  if (isPinLocked || isEmpty) {
    DOM.scrollNavGroup.classList.add('hidden');
    return;
  }

  const { scrollTop, scrollHeight, clientHeight } = DOM.contentArea;
  const isScrollable = scrollHeight > clientHeight + 40;

  if (!isScrollable) {
    DOM.scrollNavGroup.classList.add('hidden');
    return;
  }

  DOM.scrollNavGroup.classList.remove('hidden');

  // Adjust placement above Notes FAB if present
  const isNotesFabVisible = DOM.btnFabCreateNote && !DOM.btnFabCreateNote.classList.contains('hidden');
  DOM.scrollNavGroup.classList.toggle('above-fab', isNotesFabVisible);

  // Dim buttons when at top or bottom limits
  const isAtTop = scrollTop <= 15;
  const isAtBottom = scrollTop + clientHeight >= scrollHeight - 15;

  if (DOM.btnScrollTop) {
    DOM.btnScrollTop.disabled = isAtTop;
    DOM.btnScrollTop.classList.toggle('disabled', isAtTop);
  }
  if (DOM.btnScrollBottom) {
    DOM.btnScrollBottom.disabled = isAtBottom;
    DOM.btnScrollBottom.classList.toggle('disabled', isAtBottom);
  }
}

function setupScrollNav() {
  if (!DOM.scrollNavGroup || !DOM.contentArea) return;

  DOM.btnScrollTop?.addEventListener('click', (e) => {
    e.stopPropagation();
    DOM.contentArea.scrollTo({ top: 0, behavior: 'smooth' });
  });

  DOM.btnScrollBottom?.addEventListener('click', (e) => {
    e.stopPropagation();
    DOM.contentArea.scrollTo({ top: DOM.contentArea.scrollHeight, behavior: 'smooth' });
  });

  DOM.contentArea.addEventListener('scroll', () => {
    updateScrollNavVisibility();
  });

  window.addEventListener('resize', () => {
    updateScrollNavVisibility();
  });
}

function isLikelyUrl(str) {
  if (!str) return false;
  const s = str.trim();
  return /^https?:\/\//i.test(s) || /^ftp:\/\//i.test(s) || /^www\.[a-z0-9-]+\.[a-z]{2,}/i.test(s);
}

async function openLink(rawUrl) {
  if (!rawUrl) return;
  let url = rawUrl.trim();
  if (!/^https?:\/\//i.test(url) && !/^ftp:\/\//i.test(url) && !/^mailto:/i.test(url)) {
    url = 'https://' + url;
  }
  try {
    await invoke('open_url', { url });
  } catch (err) {
    console.warn("invoke open_url error, fallback to window.open:", err);
    window.open(url, '_blank');
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ── Initialization ─────────────────────────────────────────────────
async function init() {
  console.log("[ClipMaster] Initializing with RemixIcon Design System...");
  const hasTauri = !!getTauriInvoke();
  if (DOM.statusIndicator) {
    if (hasTauri) {
      DOM.statusIndicator.classList.add('active');
      DOM.statusIndicator.title = "Đã kết nối Rust Tauri backend (Native)";
    } else {
      DOM.statusIndicator.classList.remove('active');
      DOM.statusIndicator.title = "Chế độ Standalone Browser (Không có backend)";
    }
  }

  setupModeSwitcher();
  setupSearchAndFilters();
  setupPinKeypad();
  setupPinDialog();
  setupNoteModal();
  setupSettingsModal();
  setupSyncWizard();
  setupKeyboardNavigation();
  setupHeaderActions();
  setupClipboardListener();
  setupScrollNav();
  setupAccentColorPicker();

  // Load saved theme
  try {
    const savedTheme = await invoke('get_setting', { key: 'theme_mode', default_val: 'dark' });
    updateThemeUI(savedTheme || 'dark');
  } catch (e) {
    console.error("Theme load error:", e);
    updateThemeUI('dark');
  }

  // Load saved accent color
  try {
    const savedAccent = await invoke('get_setting', { key: 'accent_color', default_val: 'indigo' });
    updateAccentColorUI(savedAccent || 'indigo');
  } catch (e) {
    console.error("Accent color load error:", e);
    updateAccentColorUI('indigo');
  }

  // Load saved language
  try {
    const savedLang = await invoke('get_setting', { key: 'language', default_val: 'vi' });
    applyLanguage(savedLang || 'vi');
  } catch (e) {
    console.error("Language load error:", e);
    applyLanguage('vi');
  }

  // Load initial pause state
  try {
    const initialPaused = await invoke('is_clipboard_paused');
    updatePauseUI(!!initialPaused);
  } catch (e) {
    console.warn("Could not check pause status:", e);
  }

  // Initial load
  await loadClips();

  // Auto-sync on startup if enabled
  try {
    const syncEnabled = await invoke('get_setting', { key: 'sync_enabled', default_val: '0' });
    if (syncEnabled === '1') {
      invoke('sync_now').then(async (msg) => {
        console.log("[Sync Startup]:", msg);
        await loadClips();
        if (state.mode === 'notes') await loadNotes();
      }).catch(err => {
        console.warn("[Sync Startup Error]:", err);
      });
    }
  } catch (e) {
    // Ignore
  }
}

document.addEventListener('DOMContentLoaded', init);
