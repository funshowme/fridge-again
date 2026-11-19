/**
 * 冰箱第二春 — API 串接與自動離線備案層
 *
 * 設計重點：
 * 1. 所有真實請求一律使用相對路徑 `/api/...`（不寫死本機網址或連接埠）。
 * 2. 支援手動切換開關（自動偵測 / 真實後端 / 離線示範 Mock）。
 * 3. 自動離線備案（必做）：當 API 連不到、超時或回傳非 JSON（如網站預覽不跑 Python）時，
 *    自動無縫改用內建示範資料 + 前端版規則式推薦並存於 localStorage，保證核心 5 步都能走完。
 */

import {
  computeRuleSuggestions,
  createSeedHistory,
  createSeedItems,
  getTaipeiNowIso,
  guessEmoji,
  hydrateItem,
  SEED_RECIPES,
} from '../data/mockData';

const STORAGE_KEY = 'fridge_again_mock_state_v2';
const MODE_KEY = 'fridge_again_data_mode_v1';

// mode: 'auto' | 'api' | 'mock'
let preferredMode = loadSavedMode();
let activeSource = preferredMode === 'mock' ? 'mock' : 'unknown'; // 'api' | 'mock' | 'unknown'
let backendAiMode = 'offline'; // 'offline' | 'online'
let fallbackNotice = null;
const listeners = new Set();

function loadSavedMode() {
  try {
    const val = window.localStorage.getItem(MODE_KEY);
    if (val === 'auto' || val === 'api' || val === 'mock') return val;
  } catch {
    // ignore storage errors in restricted contexts
  }
  return 'auto';
}

function saveMode(mode) {
  try {
    window.localStorage.setItem(MODE_KEY, mode);
  } catch {
    // ignore
  }
}

function notify() {
  const snapshot = getConnectionState();
  listeners.forEach((cb) => cb(snapshot));
}

export function subscribeConnection(listener) {
  listeners.add(listener);
  listener(getConnectionState());
  return () => listeners.delete(listener);
}

export function getConnectionState() {
  return {
    preferredMode,
    activeSource: activeSource === 'unknown' ? 'mock' : activeSource,
    backendAiMode,
    fallbackNotice,
    isMock: activeSource !== 'api',
  };
}

export function clearFallbackNotice() {
  fallbackNotice = null;
  notify();
}

// --- Mock persistent state ---

function createFreshMockState() {
  const history = createSeedHistory();
  return {
    nextItemId: 100,
    nextRescueId: 200,
    items: createSeedItems(),
    rescued_count: history.rescued_count,
    saved_ntd: history.saved_ntd,
    wasted_count: history.wasted_count,
    recent: history.recent,
  };
}

function loadMockState() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && Array.isArray(parsed.items)) {
        // 每次讀取重新計算 days_left 與 urgency，確保跨日依然準確
        parsed.items = parsed.items.map(hydrateItem);
        return parsed;
      }
    }
  } catch {
    // ignore corrupted storage
  }
  const fresh = createFreshMockState();
  saveMockState(fresh);
  return fresh;
}

function saveMockState(state) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // ignore
  }
}

export function resetMockData() {
  const fresh = createFreshMockState();
  saveMockState(fresh);
  return fresh;
}

function buildStatsFromMock(state) {
  const denom = state.rescued_count + state.wasted_count;
  const rescue_rate = denom === 0 ? 0 : Number((state.rescued_count / denom).toFixed(2));
  return {
    rescued_count: state.rescued_count,
    saved_ntd: state.saved_ntd,
    wasted_count: state.wasted_count,
    rescue_rate,
    recent: state.recent.slice(0, 5),
  };
}

// --- Network helper with JSON validation & timeout ---

class NetworkUnavailableError extends Error {
  constructor(message) {
    super(message);
    this.name = 'NetworkUnavailableError';
  }
}

async function fetchJson(relativePath, options = {}, timeoutMs = 2500) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  let response;
  try {
    response = await fetch(relativePath, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });
  } catch (err) {
    window.clearTimeout(timer);
    throw new NetworkUnavailableError(err?.message || '無法連線至後端服務');
  }
  window.clearTimeout(timer);

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');

  if (!isJson) {
    // 例如純靜態預覽（vite preview / 靜態託管）回傳 index.html 或 404 HTML
    throw new NetworkUnavailableError('後端尚未啟動或目前為靜態預覽模式');
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new NetworkUnavailableError('後端回應格式異常');
  }

  if (!response.ok) {
    const hasApiErrorContract = Boolean(data?.error?.code && data?.error?.message);
    const message = data?.error?.message || `請求失敗（HTTP ${response.status}）`;
    // 任何 5xx、405（靜態主機拒收 POST）或非本系統規格的 404，皆視為無後端並自動切至示範模式
    if (
      response.status >= 500 ||
      response.status === 405 ||
      (response.status === 404 && !hasApiErrorContract)
    ) {
      throw new NetworkUnavailableError(message);
    }
    const err = new Error(message);
    err.code = data?.error?.code || 'INTERNAL';
    err.status = response.status;
    throw err;
  }

  return data;
}

export async function probeBackend() {
  if (preferredMode === 'mock') {
    activeSource = 'mock';
    backendAiMode = 'offline';
    notify();
    return { ok: true, source: 'mock', ai: 'offline' };
  }

  try {
    const health = await fetchJson('/api/health', { method: 'GET' }, 1800);
    if (health && health.ok) {
      activeSource = 'api';
      backendAiMode = health.ai === 'online' ? 'online' : 'offline';
      fallbackNotice = null;
      notify();
      return { ok: true, source: 'api', ai: backendAiMode };
    }
    throw new NetworkUnavailableError('健康檢查未通過');
  } catch {
    activeSource = 'mock';
    backendAiMode = 'offline';
    if (preferredMode === 'api') {
      fallbackNotice = '無法連線到後端 API，已自動切換為內建示範資料。';
    } else {
      fallbackNotice = null;
    }
    notify();
    return { ok: false, source: 'mock', ai: 'offline' };
  }
}

export async function setDataMode(mode) {
  preferredMode = mode;
  saveMode(mode);
  fallbackNotice = null;
  if (mode === 'mock') {
    activeSource = 'mock';
    backendAiMode = 'offline';
    notify();
    return { ok: true, source: 'mock' };
  }
  return probeBackend();
}

async function runWithFallback(apiFn, mockFn) {
  if (preferredMode === 'mock') {
    activeSource = 'mock';
    return mockFn();
  }

  if (activeSource === 'unknown') {
    await probeBackend();
  }

  if (activeSource === 'mock' && preferredMode === 'auto') {
    return mockFn();
  }

  try {
    const result = await apiFn();
    if (activeSource !== 'api') {
      activeSource = 'api';
      notify();
    }
    return result;
  } catch (err) {
    if (err instanceof NetworkUnavailableError) {
      activeSource = 'mock';
      backendAiMode = 'offline';
      fallbackNotice = '後端 API 暫時連不到，已自動改用內建示範資料。';
      notify();
      return mockFn();
    }
    throw err;
  }
}

// --- Public API Functions (matching docs/API.md v1) ---

export async function getItems(status = 'in_fridge') {
  return runWithFallback(
    () => fetchJson(`/api/items?status=${encodeURIComponent(status)}`, { method: 'GET' }),
    () => {
      const state = loadMockState();
      const items = state.items
        .filter((it) => it.status === status)
        .map(hydrateItem)
        .sort((a, b) => a.expires_on.localeCompare(b.expires_on) || a.id - b.id);
      return { items };
    }
  );
}

export async function createItem(payload) {
  const cleanPayload = {
    name: String(payload.name || '').trim(),
    quantity: Number(payload.quantity) > 0 ? Number(payload.quantity) : 1,
    unit: String(payload.unit || '').trim() || '個',
    expires_on: payload.expires_on,
    owner: String(payload.owner || '').trim(),
    price: Number(payload.price) >= 0 ? Math.round(Number(payload.price)) : 0,
  };

  return runWithFallback(
    () =>
      fetchJson('/api/items', {
        method: 'POST',
        body: JSON.stringify(cleanPayload),
      }),
    () => {
      if (!cleanPayload.name || !cleanPayload.expires_on) {
        throw new Error('請填寫食材名稱與到期日');
      }
      const state = loadMockState();
      const newItem = hydrateItem({
        id: state.nextItemId++,
        ...cleanPayload,
        emoji: guessEmoji(cleanPayload.name),
        status: 'in_fridge',
        created_at: getTaipeiNowIso(),
      });
      state.items.push(newItem);
      saveMockState(state);
      return { item: newItem };
    }
  );
}

export async function patchItem(id, patch) {
  return runWithFallback(
    () =>
      fetchJson(`/api/items/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(patch),
      }),
    () => {
      const state = loadMockState();
      const idx = state.items.findIndex((it) => it.id === id);
      if (idx === -1) throw new Error('找不到這個食材');
      const prevStatus = state.items[idx].status;
      const updated = hydrateItem({ ...state.items[idx], ...patch });
      state.items[idx] = updated;
      if (prevStatus !== 'wasted' && updated.status === 'wasted') {
        state.wasted_count += 1;
      }
      saveMockState(state);
      return { item: updated };
    }
  );
}

export async function deleteItem(id) {
  return runWithFallback(
    () => fetchJson(`/api/items/${id}`, { method: 'DELETE' }),
    () => {
      const state = loadMockState();
      const exists = state.items.some((it) => it.id === id);
      if (!exists) throw new Error('找不到這個食材');
      state.items = state.items.filter((it) => it.id !== id);
      saveMockState(state);
      return { ok: true };
    }
  );
}

export async function getSuggestions(itemIds) {
  return runWithFallback(
    () =>
      fetchJson('/api/suggestions', {
        method: 'POST',
        body: JSON.stringify({ item_ids: itemIds }),
      }),
    () => {
      const state = loadMockState();
      const inFridge = state.items.filter((it) => it.status === 'in_fridge').map(hydrateItem);
      const recipes = computeRuleSuggestions(inFridge, itemIds);
      return {
        source: 'rules',
        recipes,
      };
    }
  );
}

export async function recordRescue({ item_ids, recipe_id, action = 'cooked' }) {
  return runWithFallback(
    () =>
      fetchJson('/api/rescues', {
        method: 'POST',
        body: JSON.stringify({ item_ids, recipe_id, action }),
      }),
    () => {
      const state = loadMockState();
      const targetSet = new Set(item_ids);
      const rescuedItems = [];

      state.items = state.items.map((it) => {
        if (targetSet.has(it.id) && it.status === 'in_fridge') {
          rescuedItems.push(it);
          return { ...it, status: action === 'shared' ? 'shared' : 'rescued' };
        }
        return it;
      });

      const saved_ntd = rescuedItems.reduce((sum, it) => sum + (Number(it.price) || 0), 0);
      const recipe = SEED_RECIPES.find((r) => r.id === recipe_id);
      const nowIso = getTaipeiNowIso();
      const rescueId = state.nextRescueId++;

      state.rescued_count += rescuedItems.length;
      state.saved_ntd += saved_ntd;
      state.recent = [
        {
          id: rescueId,
          recipe_title: recipe ? recipe.title : '宿舍救援料理',
          item_names: rescuedItems.map((it) => it.name),
          created_at: nowIso,
        },
        ...state.recent,
      ].slice(0, 5);

      saveMockState(state);

      return {
        rescue: {
          id: rescueId,
          item_ids,
          recipe_id,
          action,
          saved_ntd,
          created_at: nowIso,
        },
        stats: buildStatsFromMock(state),
      };
    }
  );
}

export async function getStats() {
  return runWithFallback(
    () => fetchJson('/api/stats', { method: 'GET' }),
    () => {
      const state = loadMockState();
      return buildStatsFromMock(state);
    }
  );
}
