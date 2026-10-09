/**
 * ClipMaster - Cross-Platform Modern Frontend Controller
 * Tauri v2 IPC Bridge & Interactive UI Logic
 */

// ── IPC Abstraction Layer ──────────────────────────────────────────
const isTauri = typeof window.__TAURI__ !== 'undefined' && typeof window.__TAURI__.core !== 'undefined';

async function invoke(command, args = {}) {
  if (isTauri) {
    try {
      return await window.__TAURI__.core.invoke(command, args);
    } catch (err) {
      console.error(`[IPC Error] ${command}:`, err);
      throw err;
    }
  } else {
    return mockInvoke(command, args);
  }
}

// In-memory mock for testing in browser without Tauri backend
const mockStore = {
  clips: [
    { id: 1, type: "code", content: "git checkout -b feature/rust-tauri\ngit push -u origin feature/rust-tauri", is_pinned: 1, created_at: Date.now() / 1000 - 120, updated_at: Date.now() / 1000 - 120 },
    { id: 2, type: "url", content: "https://tauri.app/v2/guides/getting-started/", is_pinned: 0, created_at: Date.now() / 1000 - 600, updated_at: Date.now() / 1000 - 600 },
    { id: 3, type: "color", content: "#3b82f6", is_pinned: 0, created_at: Date.now() / 1000 - 1800, updated_at: Date.now() / 1000 - 1800 },
    { id: 4, type: "text", content: "ClipMaster - Trình quản lý Clipboard đa nền tảng tối ưu hiệu năng cao bằng Rust và Tauri v2.", is_pinned: 0, created_at: Date.now() / 1000 - 7200, updated_at: Date.now() / 1000 - 7200 }
  ],
  notes: [
    { id: 1, title: "Lệnh build nhanh", content: "cargo tauri build\ncargo tauri dev", is_pinned: 1, color: "#3b82f6", created_at: Date.now() / 1000 - 3600, updated_at: Date.now() / 1000 - 3600 }
  ],
  settings: {
    max_history: "200",
    auto_paste: "1",
    theme_mode: "dark",
    notes_pin_enabled: "0",
    notes_pin_hash: ""
  }
};

async function mockInvoke(cmd, args) {
  switch (cmd) {
    case 'get_clips': {
      let res = [...mockStore.clips];
      if (args.filter_type === 'pinned') res = res.filter(c => c.is_pinned === 1);
      else if (args.filter_type && args.filter_type !== 'all') res = res.filter(c => c.type === args.filter_type);
      if (args.query) res = res.filter(c => c.content?.toLowerCase().includes(args.query.toLowerCase()));
      return res.sort((a, b) => (b.is_pinned - a.is_pinned) || (b.updated_at - a.updated_at));
    }
    case 'get_notes': {
      let res = [...mockStore.notes];
      if (args.filter_pinned) res = res.filter(n => n.is_pinned === 1);
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
    case 'verify_notes_pin':
      return args.pin === "1234" || args.pin === mockStore.settings.pin;
    case 'set_notes_pin':
      mockStore.settings.notes_pin_enabled = "1";
      mockStore.settings.pin = args.pin;
      return true;
    case 'disable_notes_pin':
      mockStore.settings.notes_pin_enabled = "0";
      return;
    case 'get_setting':
      return mockStore.settings[args.key] || args.default_val || "";
    case 'set_setting':
      mockStore.settings[args.key] = args.value;
      return;
    case 'hide_window':
    case 'close_window':
      console.log(`[Window Action] ${cmd}`);
      return;
    default:
      return null;
  }
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
  activeNoteColor: ''
};

// ── DOM References ─────────────────────────────────────────────────
const DOM = {
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
  searchWrapper: document.getElementById('search-wrapper'),
  btnSearchToggle: document.getElementById('btn-search-toggle'),
  searchInput: document.getElementById('search-input'),
  btnSearchClear: document.getElementById('btn-search-clear'),

  // Header actions
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
  toast: document.getElementById('toast')
};

// ── Time & Formatting Helpers ──────────────────────────────────────
function formatRelativeTime(timestamp) {
  if (!timestamp) return "";
  const now = Date.now() / 1000;
  const diff = Math.max(0, now - timestamp);

  if (diff < 15) return "Vừa xong";
  if (diff < 60) return `${Math.floor(diff)} giây trước`;
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
  
  const d = new Date(timestamp * 1000);
  const pad = n => n.toString().padStart(2, '0');
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function showToast(message) {
  DOM.toast.textContent = message;
  DOM.toast.classList.add('show');
  setTimeout(() => {
    DOM.toast.classList.remove('show');
  }, 1600);
}

// ── Data Loading & Rendering ───────────────────────────────────────
async function loadClips() {
  if (state.mode !== 'history') return;

  try {
    const clips = await invoke('get_clips', {
      filter_type: state.historyFilter,
      query: state.searchQuery,
      limit: 200,
      offset: 0
    });

    state.currentItems = clips || [];
    renderHistoryCards(state.currentItems);

    const stats = await invoke('get_stats');
    DOM.footerStatus.textContent = `Tổng cộng: ${stats?.total || 0} mục (${stats?.pinned || 0} đã ghim)`;
  } catch (err) {
    console.error("Failed to load clips:", err);
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
      filter_pinned: state.notesFilter === 'pinned',
      limit: 200
    });

    state.currentItems = notes || [];
    renderNoteCards(state.currentItems);

    const pinnedCount = state.currentItems.filter(n => n.is_pinned).length;
    DOM.footerStatus.textContent = `Ghi chú: ${state.currentItems.length} mục (${pinnedCount} đã ghim)`;
  } catch (err) {
    console.error("Failed to load notes:", err);
  }
}

function renderHistoryCards(items) {
  DOM.itemsList.innerHTML = '';
  state.selectedIndex = -1;

  if (items.length === 0) {
    DOM.emptyState.classList.remove('hidden');
    DOM.emptyTitle.textContent = "Chưa có nội dung sao chép nào";
    DOM.emptyDesc.textContent = state.searchQuery 
      ? "Không tìm thấy kết quả phù hợp với từ khóa." 
      : "Sao chép bất kỳ văn bản, code hoặc liên kết (Ctrl + C) để lưu tự động.";
    return;
  }

  DOM.emptyState.classList.add('hidden');

  items.forEach((item, index) => {
    const card = document.createElement('div');
    card.className = `clip-card ${index === 0 ? 'selected' : ''}`;
    card.dataset.index = index;
    card.dataset.id = item.id;

    if (index === 0) state.selectedIndex = 0;

    let typeBadgeLabel = item.type.toUpperCase();
    let previewHtml = '';

    if (item.type === 'color') {
      previewHtml = `
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="width: 18px; height: 18px; border-radius: 4px; background: ${escapeHtml(item.content)}; border: 1px solid rgba(255,255,255,0.2); display: inline-block;"></span>
          <span class="card-content font-mono">${escapeHtml(item.content)}</span>
        </div>`;
    } else if (item.type === 'code') {
      previewHtml = `<div class="card-content code">${escapeHtml(item.content)}</div>`;
    } else {
      previewHtml = `<div class="card-content">${escapeHtml(item.content || "")}</div>`;
    }

    card.innerHTML = `
      <div class="card-header">
        <span class="card-badge">${typeBadgeLabel}</span>
        <span class="card-time">${formatRelativeTime(item.updated_at)}</span>
      </div>
      ${previewHtml}
      <div class="card-actions">
        <button class="card-btn ${item.is_pinned ? 'pinned' : ''}" data-action="pin" title="${item.is_pinned ? 'Bỏ ghim' : 'Ghim'}">
          ${item.is_pinned ? '📌' : '📍'}
        </button>
        <button class="card-btn" data-action="delete" title="Xóa">🗑️</button>
      </div>
    `;

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

    DOM.itemsList.appendChild(card);
  });
}

function renderNoteCards(notes) {
  DOM.itemsList.innerHTML = '';
  state.selectedIndex = -1;

  if (notes.length === 0) {
    DOM.emptyState.classList.remove('hidden');
    DOM.emptyTitle.textContent = "Chưa có ghi chú nào";
    DOM.emptyDesc.textContent = state.searchQuery 
      ? "Không tìm thấy ghi chú phù hợp với từ khóa." 
      : "Nhấn nút (＋) ở góc dưới để tạo ghi chú mới.";
    return;
  }

  DOM.emptyState.classList.add('hidden');

  notes.forEach((note, index) => {
    const card = document.createElement('div');
    card.className = `clip-card ${index === 0 ? 'selected' : ''}`;
    card.dataset.index = index;
    card.dataset.id = note.id;

    if (note.color) {
      card.style.borderLeft = `4px solid ${note.color}`;
    }

    if (index === 0) state.selectedIndex = 0;

    const titleHtml = note.title ? `<div style="font-weight: 700; font-size: 13px; margin-bottom: 2px;">${escapeHtml(note.title)}</div>` : '';

    card.innerHTML = `
      <div class="card-header">
        <span class="card-badge" style="background: rgba(168, 85, 247, 0.15); color: #c084fc;">NOTE</span>
        <span class="card-time">${formatRelativeTime(note.updated_at)}</span>
      </div>
      ${titleHtml}
      <div class="card-content">${escapeHtml(note.content)}</div>
      <div class="card-actions">
        <button class="card-btn" data-action="edit" title="Chỉnh sửa">✏️</button>
        <button class="card-btn ${note.is_pinned ? 'pinned' : ''}" data-action="pin" title="${note.is_pinned ? 'Bỏ ghim' : 'Ghim'}">
          ${note.is_pinned ? '📌' : '📍'}
        </button>
        <button class="card-btn" data-action="delete" title="Xóa">🗑️</button>
      </div>
    `;

    // Click on note copies text
    card.addEventListener('click', async (e) => {
      if (e.target.closest('[data-action]')) return;
      selectCard(index);
      await invoke('copy_text', { text: note.content });
      showToast("Đã dán ghi chú!");
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
    await invoke('copy_clip', { id });
    showToast("Đã sao chép vào bộ nhớ tạm!");
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
    await invoke('delete_clip', { id });
    await loadClips();
  } catch (err) {
    console.error("Delete clip failed:", err);
  }
}

// ── Search & Filter Interactions ───────────────────────────────────
function setupSearchAndFilters() {
  DOM.btnSearchToggle.addEventListener('click', () => {
    DOM.searchWrapper.classList.add('expanded');
    DOM.searchInput.focus();
  });

  DOM.btnSearchClear.addEventListener('click', () => {
    if (DOM.searchInput.value) {
      DOM.searchInput.value = '';
      state.searchQuery = '';
      triggerReload();
    } else {
      DOM.searchWrapper.classList.remove('expanded');
    }
  });

  let debounceTimer = null;
  DOM.searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      state.searchQuery = e.target.value;
      triggerReload();
    }, 150);
  });

  // History Filter Chips
  DOM.historyFilters.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      DOM.historyFilters.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.historyFilter = chip.dataset.filter;
      loadClips();
    });
  });

  // Notes Filter Chips
  DOM.notesFilters.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      DOM.notesFilters.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.notesFilter = chip.dataset.filter;
      loadNotes();
    });
  });
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
    DOM.appSubtitle.textContent = "Lịch sử Clipboard (Win + V)";
    hidePinLockScreen();
    loadClips();
  });

  DOM.tabNotes.addEventListener('click', () => {
    if (state.mode === 'notes') return;
    state.mode = 'notes';
    DOM.tabNotes.classList.add('active');
    DOM.tabHistory.classList.remove('active');
    DOM.historyFilters.classList.add('hidden');
    DOM.notesFilters.classList.remove('hidden');
    DOM.btnFabCreateNote.classList.remove('hidden');
    DOM.appSubtitle.textContent = "Ghi chú bảo mật & Cá nhân";
    loadNotes();
  });
}

// ── PIN Lock Screen Logic (4-Dot & 30s Lockout) ────────────────────
function showPinLockScreen() {
  DOM.pinLockScreen.classList.remove('hidden');
  DOM.itemsList.classList.add('hidden');
  DOM.emptyState.classList.add('hidden');
  DOM.btnFabCreateNote.classList.add('hidden');
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
      DOM.pinErrorMsg.textContent = `Sai mã PIN. Còn lại ${3 - state.pinFailedAttempts} lần thử.`;
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
      DOM.pinSubtitle.textContent = "Vui lòng nhập mã PIN 4 chữ số để mở khóa";
      DOM.pinKeypad.querySelectorAll('button').forEach(b => b.disabled = false);
      state.pinBuffer = '';
      updatePinDots();
    } else {
      DOM.pinErrorMsg.textContent = `Khóa tạm thời: Vui lòng đợi ${state.lockoutRemaining}s`;
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
    DOM.modalNoteTitle.textContent = "Chỉnh sửa ghi chú";
    DOM.noteId.value = note.id;
    DOM.noteInputTitle.value = note.title || '';
    DOM.noteInputContent.value = note.content || '';
    state.activeNoteColor = note.color || '';
  } else {
    DOM.modalNoteTitle.textContent = "Tạo ghi chú mới";
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
      alert("Vui lòng nhập nội dung ghi chú!");
      return;
    }

    const title = DOM.noteInputTitle.value.trim() || null;
    const id = DOM.noteId.value ? parseInt(DOM.noteId.value, 10) : null;
    const color = state.activeNoteColor || null;

    try {
      await invoke('save_note', { id, title, content, color });
      closeNoteModal();
      showToast("Đã lưu ghi chú thành công!");
      loadNotes();
    } catch (err) {
      console.error("Save note failed:", err);
      alert("Lỗi khi lưu ghi chú: " + err);
    }
  });
}

// ── Settings Modal ─────────────────────────────────────────────────
async function openSettingsModal() {
  DOM.modalSettings.classList.remove('hidden');

  const maxHistory = await invoke('get_setting', { key: 'max_history', default_val: '200' });
  const autoPaste = await invoke('get_setting', { key: 'auto_paste', default_val: '1' });
  const pinEnabled = await invoke('is_notes_pin_enabled');

  DOM.settingMaxHistory.value = maxHistory || '200';
  DOM.settingAutoPaste.checked = autoPaste === '1';
  DOM.settingPinStatus.textContent = pinEnabled ? "Trạng thái: ĐÃ BẬT bảo vệ PIN" : "Trạng thái: Chưa bật";
  DOM.settingPinStatus.style.color = pinEnabled ? "var(--success-color)" : "var(--text-muted)";
}

function closeSettingsModal() {
  DOM.modalSettings.classList.add('hidden');
}

function setupSettingsModal() {
  DOM.btnSettings.addEventListener('click', openSettingsModal);
  DOM.btnCloseSettingsModal.addEventListener('click', closeSettingsModal);

  DOM.btnSetPin.addEventListener('click', async () => {
    const pin = DOM.settingNewPin.value.trim();
    if (pin.length !== 4 || !/^\d{4}$/.test(pin)) {
      alert("Mã PIN phải gồm đúng 4 chữ số (0-9)!");
      return;
    }
    await invoke('set_notes_pin', { pin });
    DOM.settingNewPin.value = '';
    DOM.settingPinStatus.textContent = "Trạng thái: ĐÃ BẬT bảo vệ PIN";
    DOM.settingPinStatus.style.color = "var(--success-color)";
    showToast("Đã cập nhật mã PIN bảo mật!");
  });

  DOM.btnDisablePin.addEventListener('click', async () => {
    await invoke('disable_notes_pin');
    DOM.settingPinStatus.textContent = "Trạng thái: Đã tắt mã PIN";
    DOM.settingPinStatus.style.color = "var(--text-muted)";
    state.notesUnlocked = true;
    showToast("Đã tắt bảo vệ bằng mã PIN!");
  });

  DOM.btnSaveSettings.addEventListener('click', async () => {
    await invoke('set_setting', { key: 'max_history', value: DOM.settingMaxHistory.value });
    await invoke('set_setting', { key: 'auto_paste', value: DOM.settingAutoPaste.checked ? '1' : '0' });
    closeSettingsModal();
    showToast("Đã lưu thiết lập!");
  });
}

// ── Global Keyboard Navigation ─────────────────────────────────────
function setupKeyboardNavigation() {
  window.addEventListener('keydown', async (e) => {
    // If modal is open, let user type inside inputs
    if (!DOM.modalNote.classList.contains('hidden') || !DOM.modalSettings.classList.contains('hidden')) {
      if (e.key === 'Escape') {
        closeNoteModal();
        closeSettingsModal();
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
      DOM.searchWrapper.classList.add('expanded');
      DOM.searchInput.focus();
      return;
    }

    // Ctrl + N new note shortcut
    if ((e.ctrlKey || e.metaKey) && (e.key === 'n' || e.key === 'N')) {
      e.preventDefault();
      if (state.mode !== 'notes') DOM.tabNotes.click();
      openNoteModal();
      return;
    }

    // Escape closes search or hides window
    if (e.key === 'Escape') {
      if (DOM.searchWrapper.classList.contains('expanded')) {
        DOM.searchWrapper.classList.remove('expanded');
        DOM.searchInput.value = '';
        state.searchQuery = '';
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
          showToast("Đã dán ghi chú!");
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

  DOM.btnClear.addEventListener('click', async () => {
    if (confirm("Bạn có chắc chắn muốn xóa tất cả các mục lịch sử chưa được ghim?")) {
      const removed = await invoke('clear_unpinned');
      showToast(`Đã dọn dẹp ${removed} mục.`);
      await loadClips();
    }
  });

  // Dark / Light Theme
  DOM.btnTheme.addEventListener('click', async () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    DOM.btnTheme.textContent = nextTheme === 'dark' ? '🌙' : '☀️';
    await invoke('set_setting', { key: 'theme_mode', value: nextTheme });
  });
}

// ── Listen for System Clipboard Events ─────────────────────────────
function setupClipboardListener() {
  if (isTauri && window.__TAURI__.event) {
    window.__TAURI__.event.listen('clipboard_changed', (event) => {
      if (state.mode === 'history') {
        loadClips();
      }
    });
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
  setupModeSwitcher();
  setupSearchAndFilters();
  setupPinKeypad();
  setupNoteModal();
  setupSettingsModal();
  setupKeyboardNavigation();
  setupHeaderActions();
  setupClipboardListener();

  // Load saved theme
  const savedTheme = await invoke('get_setting', { key: 'theme_mode', default_val: 'dark' });
  document.documentElement.setAttribute('data-theme', savedTheme || 'dark');
  DOM.btnTheme.textContent = savedTheme === 'dark' ? '🌙' : '☀️';

  // Initial load
  await loadClips();
}

document.addEventListener('DOMContentLoaded', init);
