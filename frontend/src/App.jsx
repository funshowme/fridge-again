import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Banner } from '@astryxdesign/core/Banner';
import { LinkProvider } from '@astryxdesign/core/Link';
import { Theme } from '@astryxdesign/core/theme';
import { neutralTheme } from '@astryxdesign/theme-neutral/built';

import { AddItemModal } from './components/AddItemModal';
import { FridgeView } from './components/FridgeView';
import { Header } from './components/Header';
import { RecipeDetailView } from './components/RecipeDetailView';
import { RescueSuccessView } from './components/RescueSuccessView';
import { SuggestionsView } from './components/SuggestionsView';
import {
  clearFallbackNotice,
  createItem,
  deleteItem,
  getConnectionState,
  getItems,
  getStats,
  getSuggestions,
  patchItem,
  probeBackend,
  recordRescue,
  resetMockData,
  setDataMode,
  subscribeConnection,
} from './services/api';

const MAX_SELECT = 5;

function SimpleLink({ href, children, ...props }) {
  return (
    <a href={href} {...props}>
      {children}
    </a>
  );
}

export default function App() {
  // 核心 5 步畫面狀態：fridge -> suggestions -> detail -> success
  const [step, setStep] = useState('fridge');

  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [loadingHome, setLoadingHome] = useState(true);

  const [selectedIds, setSelectedIds] = useState([]);
  const [newlyAddedId, setNewlyAddedId] = useState(null);

  const [suggestionsData, setSuggestionsData] = useState(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  const [activeSuggestion, setActiveSuggestion] = useState(null);
  const [submittingRescue, setSubmittingRescue] = useState(false);
  const [markingWasted, setMarkingWasted] = useState(false);
  const [rescueResult, setRescueResult] = useState(null);

  const [addModalOpen, setAddModalOpen] = useState(false);
  const [errorBanner, setErrorBanner] = useState('');
  const [toastMessage, setToastMessage] = useState('');
  const [connection, setConnection] = useState(() => getConnectionState());

  const showToast = useCallback((msg) => {
    setToastMessage(msg);
    window.clearTimeout(showToast._timer);
    showToast._timer = window.setTimeout(() => setToastMessage(''), 2600);
  }, []);

  const loadHomeData = useCallback(async () => {
    setLoadingHome(true);
    setErrorBanner('');
    try {
      const [itemsRes, statsRes] = await Promise.all([
        getItems('in_fridge'),
        getStats(),
      ]);
      const loadedItems = itemsRes?.items ?? [];
      setItems(loadedItems);
      setStats(statsRes);
      setSelectedIds((prev) =>
        prev.filter((id) => loadedItems.some((it) => it.id === id))
      );
    } catch (err) {
      setErrorBanner(err?.message || '載入冰箱資料失敗');
    } finally {
      setLoadingHome(false);
    }
  }, []);

  useEffect(() => {
    const unsub = subscribeConnection(setConnection);
    (async () => {
      await probeBackend();
      await loadHomeData();
    })();
    return unsub;
  }, [loadHomeData]);

  const selectedItems = useMemo(() => {
    const idSet = new Set(selectedIds);
    return items.filter((it) => idSet.has(it.id));
  }, [items, selectedIds]);

  const existingOwners = useMemo(
    () => Array.from(new Set(items.map((it) => it.owner).filter(Boolean))),
    [items]
  );

  function handleToggleSelect(id) {
    setSelectedIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((itemId) => itemId !== id);
      }
      if (prev.length >= MAX_SELECT) {
        showToast(`一次最多勾選 ${MAX_SELECT} 樣食材喔！`);
        return prev;
      }
      return [...prev, id];
    });
  }

  function handleQuickSelectUrgent(ids) {
    setSelectedIds(ids.slice(0, MAX_SELECT));
  }

  async function handleRequestSuggestions() {
    if (selectedIds.length === 0) return;
    setErrorBanner('');
    setLoadingSuggestions(true);
    try {
      const data = await getSuggestions(selectedIds);
      setSuggestionsData(data);
      setStep('suggestions');
      window.scrollTo({ top: 0, behavior: 'instant' });
    } catch (err) {
      setErrorBanner(err?.message || '取得推薦食譜失敗，請稍後再試');
    } finally {
      setLoadingSuggestions(false);
    }
  }

  function handleSelectRecipe(entry) {
    setActiveSuggestion(entry);
    setStep('detail');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function handleConfirmCooked({ item_ids, recipe_id, rescuedItems, recipe }) {
    setSubmittingRescue(true);
    setErrorBanner('');
    try {
      const res = await recordRescue({
        item_ids,
        recipe_id,
        action: 'cooked',
      });
      setStats(res.stats);
      setRescueResult({
        recipe,
        rescuedItems,
        rescue: res.rescue,
        stats: res.stats,
      });
      // 同步從清單移除已救援食材並清空勾選
      const rescuedSet = new Set(item_ids);
      setItems((prev) => prev.filter((it) => !rescuedSet.has(it.id)));
      setSelectedIds([]);
      setStep('success');
      window.scrollTo({ top: 0, behavior: 'instant' });
    } catch (err) {
      setErrorBanner(err?.message || '記錄救援失敗，請再試一次');
    } finally {
      setSubmittingRescue(false);
    }
  }

  async function handleBackHomeFromSuccess() {
    setStep('fridge');
    setActiveSuggestion(null);
    setSuggestionsData(null);
    setRescueResult(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    await loadHomeData();
  }

  async function handleCreateItem(payload) {
    const res = await createItem(payload);
    const created = res?.item;
    setAddModalOpen(false);
    await loadHomeData();
    if (created?.id) {
      setNewlyAddedId(created.id);
      window.setTimeout(() => setNewlyAddedId(null), 2600);
    }
    showToast(`已將「${payload.name}」放進冰箱！`);
  }

  async function handleMarkWasted(item) {
    setErrorBanner('');
    try {
      await patchItem(item.id, { status: 'wasted' });
      setSelectedIds((prev) => prev.filter((id) => id !== item.id));
      await loadHomeData();
      showToast(`已將「${item.name}」標記為丟掉`);
    } catch (err) {
      setErrorBanner(err?.message || '更新食材狀態失敗');
    }
  }

  async function handleMarkSelectedWasted(targetItems) {
    if (!targetItems || targetItems.length === 0) return;
    setMarkingWasted(true);
    setErrorBanner('');
    try {
      for (const item of targetItems) {
        await patchItem(item.id, { status: 'wasted' });
      }
      setSelectedIds([]);
      setSuggestionsData(null);
      setStep('fridge');
      window.scrollTo({ top: 0, behavior: 'instant' });
      await loadHomeData();
      showToast(`已將 ${targetItems.length} 樣過期食材標記為丟掉，統計已更新`);
    } catch (err) {
      setErrorBanner(err?.message || '標記丟掉失敗，請再試一次');
    } finally {
      setMarkingWasted(false);
    }
  }

  async function handleDeleteItem(item) {
    setErrorBanner('');
    try {
      await deleteItem(item.id);
      setSelectedIds((prev) => prev.filter((id) => id !== item.id));
      await loadHomeData();
      showToast(`已刪除誤填的「${item.name}」`);
    } catch (err) {
      setErrorBanner(err?.message || '刪除食材失敗');
    }
  }

  async function handleModeChange(mode) {
    const result = await setDataMode(mode);
    setStep('fridge');
    setSelectedIds([]);
    await loadHomeData();
    if (mode === 'mock') {
      showToast('已切換為內建示範資料（Mock）');
    } else if (result.source === 'api') {
      showToast('已連線到真實後端 API');
    } else {
      showToast('後端尚未連線，維持內建示範模式');
    }
  }

  async function handleResetMock() {
    resetMockData();
    setStep('fridge');
    setSelectedIds([]);
    await loadHomeData();
    showToast('已重置示範資料（恢復 16 樣食材與初始戰績）');
  }

  return (
    <Theme theme={neutralTheme} mode="light">
      <LinkProvider component={SimpleLink}>
        <div className="app-shell">
          <Header
            connection={connection}
            onModeChange={handleModeChange}
            onResetMock={handleResetMock}
            onBrandClick={() => {
              setStep('fridge');
              window.scrollTo({ top: 0, behavior: 'instant' });
            }}
          />

          <main className="app-main">
            {connection.fallbackNotice && (
              <div className="banner-wrap">
                <Banner
                  status="info"
                  title="已啟用離線示範資料"
                  description={connection.fallbackNotice}
                  isDismissable
                  onDismiss={clearFallbackNotice}
                />
              </div>
            )}

            {errorBanner && (
              <div className="banner-wrap">
                <Banner
                  status="error"
                  title="操作發生問題"
                  description={errorBanner}
                  isDismissable
                  onDismiss={() => setErrorBanner('')}
                />
              </div>
            )}

            {step === 'fridge' && (
              <FridgeView
                items={items}
                stats={stats}
                loading={loadingHome}
                selectedIds={selectedIds}
                newlyAddedId={newlyAddedId}
                submittingSuggestions={loadingSuggestions}
                onToggleSelect={handleToggleSelect}
                onQuickSelectUrgent={handleQuickSelectUrgent}
                onClearSelection={() => setSelectedIds([])}
                onOpenAddModal={() => setAddModalOpen(true)}
                onMarkWasted={handleMarkWasted}
                onDeleteItem={handleDeleteItem}
                onRequestSuggestions={handleRequestSuggestions}
              />
            )}

            {step === 'suggestions' && (
              <SuggestionsView
                selectedItems={selectedItems}
                suggestionsData={suggestionsData}
                loading={loadingSuggestions}
                markingWasted={markingWasted}
                onBack={() => {
                  setStep('fridge');
                  window.scrollTo({ top: 0, behavior: 'instant' });
                }}
                onSelectRecipe={handleSelectRecipe}
                onMarkSelectedWasted={handleMarkSelectedWasted}
              />
            )}

            {step === 'detail' && activeSuggestion && (
              <RecipeDetailView
                suggestion={activeSuggestion}
                allFridgeItems={items}
                selectedItems={selectedItems}
                submittingRescue={submittingRescue}
                onBack={() => {
                  setStep('suggestions');
                  window.scrollTo({ top: 0, behavior: 'instant' });
                }}
                onConfirmCooked={handleConfirmCooked}
              />
            )}

            {step === 'success' && rescueResult && (
              <RescueSuccessView
                rescueResult={rescueResult}
                onBackHome={handleBackHomeFromSuccess}
              />
            )}
          </main>

          <AddItemModal
            isOpen={addModalOpen}
            existingOwners={existingOwners}
            onClose={() => setAddModalOpen(false)}
            onSubmit={handleCreateItem}
          />

          {toastMessage && (
            <div className="toast-pill" role="status" aria-live="polite">
              {toastMessage}
            </div>
          )}
        </div>
      </LinkProvider>
    </Theme>
  );
}
