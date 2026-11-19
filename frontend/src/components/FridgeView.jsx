import React, { useMemo, useState } from 'react';
import { Button } from '@astryxdesign/core/Button';
import { EmptyState } from '@astryxdesign/core/EmptyState';
import { Skeleton } from '@astryxdesign/core/Skeleton';
import { ArrowRightIcon, PlusIcon, SparklesIcon } from './Icons';
import { IngredientCard } from './IngredientCard';
import { StatsBanner } from './StatsBanner';

const MAX_SELECT = 5;

export function FridgeView({
  items,
  stats,
  loading,
  selectedIds,
  newlyAddedId,
  submittingSuggestions,
  onToggleSelect,
  onQuickSelectUrgent,
  onClearSelection,
  onOpenAddModal,
  onMarkWasted,
  onDeleteItem,
  onRequestSuggestions,
}) {
  const [urgencyFilter, setUrgencyFilter] = useState('all');
  const [ownerFilter, setOwnerFilter] = useState('all');

  const counts = useMemo(() => {
    const res = { all: items.length, red: 0, yellow: 0, green: 0 };
    for (const item of items) {
      if (item.urgency === 'red') res.red += 1;
      else if (item.urgency === 'yellow') res.yellow += 1;
      else res.green += 1;
    }
    return res;
  }, [items]);

  const owners = useMemo(() => {
    const set = new Set();
    let hasShared = false;
    for (const item of items) {
      if (item.owner) set.add(item.owner);
      else hasShared = true;
    }
    const list = Array.from(set);
    if (hasShared) list.push('__shared__');
    return list;
  }, [items]);

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (urgencyFilter !== 'all' && item.urgency !== urgencyFilter) {
        return false;
      }
      if (ownerFilter === '__shared__' && item.owner !== '') {
        return false;
      }
      if (ownerFilter !== 'all' && ownerFilter !== '__shared__' && item.owner !== ownerFilter) {
        return false;
      }
      return true;
    });
  }, [items, urgencyFilter, ownerFilter]);

  const selectedItems = useMemo(() => {
    const idSet = new Set(selectedIds);
    return items.filter((it) => idSet.has(it.id));
  }, [items, selectedIds]);

  const urgentItems = useMemo(
    () => items.filter((it) => it.urgency === 'red'),
    [items]
  );

  return (
    <div className="view-fridge">
      <StatsBanner stats={stats} loading={loading} />

      <div className="section-header-row">
        <div className="section-heading-group">
          <h1 className="section-title">
            我的冰箱
            <span className="section-count tabular-nums">{items.length}</span>
          </h1>
          <p className="section-hint">勾選 1–5 樣食材，30 秒找宿舍救援料理</p>
        </div>

        <Button
          variant="primary"
          size="md"
          icon={<PlusIcon size={16} />}
          label="新增食材"
          onClick={onOpenAddModal}
        />
      </div>

      {/* 急迫度篩選 */}
      <div className="filter-strip" role="tablist" aria-label="依到期急迫度篩選">
        <button
          type="button"
          role="tab"
          aria-selected={urgencyFilter === 'all'}
          className={`filter-chip ${urgencyFilter === 'all' ? 'is-active' : ''}`}
          onClick={() => setUrgencyFilter('all')}
        >
          <span>全部</span>
          <span className="filter-count tabular-nums">{counts.all}</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={urgencyFilter === 'red'}
          className={`filter-chip filter-chip--red ${urgencyFilter === 'red' ? 'is-active' : ''}`}
          onClick={() => setUrgencyFilter('red')}
        >
          <span className="chip-dot chip-dot--red" aria-hidden="true" />
          <span>急需救援</span>
          <span className="filter-count tabular-nums">{counts.red}</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={urgencyFilter === 'yellow'}
          className={`filter-chip filter-chip--yellow ${urgencyFilter === 'yellow' ? 'is-active' : ''}`}
          onClick={() => setUrgencyFilter('yellow')}
        >
          <span className="chip-dot chip-dot--yellow" aria-hidden="true" />
          <span>3 天內</span>
          <span className="filter-count tabular-nums">{counts.yellow}</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={urgencyFilter === 'green'}
          className={`filter-chip filter-chip--green ${urgencyFilter === 'green' ? 'is-active' : ''}`}
          onClick={() => setUrgencyFilter('green')}
        >
          <span className="chip-dot chip-dot--green" aria-hidden="true" />
          <span>還新鮮</span>
          <span className="filter-count tabular-nums">{counts.green}</span>
        </button>
      </div>

      {/* 室友標籤篩選 */}
      {owners.length > 1 && (
        <div className="owner-strip" aria-label="依室友篩選">
          <button
            type="button"
            className={`owner-chip ${ownerFilter === 'all' ? 'is-active' : ''}`}
            onClick={() => setOwnerFilter('all')}
          >
            全部室友
          </button>
          {owners.map((owner) => (
            <button
              key={owner}
              type="button"
              className={`owner-chip ${ownerFilter === owner ? 'is-active' : ''}`}
              onClick={() => setOwnerFilter(owner)}
            >
              {owner === '__shared__' ? '共用' : owner}
            </button>
          ))}
        </div>
      )}

      {/* 一鍵勾選急需救援食材 */}
      {urgentItems.length > 0 && selectedIds.length === 0 && !loading && (
        <div className="urgent-nudge">
          <div className="urgent-nudge-text">
            <strong>有 {urgentItems.length} 樣快過期了！</strong>
            <span>挑 1–3 樣先救起來吧</span>
          </div>
          <Button
            variant="secondary"
            size="sm"
            label={`一鍵選前 ${Math.min(3, urgentItems.length)} 樣`}
            onClick={() =>
              onQuickSelectUrgent(urgentItems.slice(0, 3).map((it) => it.id))
            }
            className="urgent-quick-btn"
          />
        </div>
      )}

      {/* 食材清單 */}
      {loading ? (
        <div className="skeleton-list" aria-label="載入食材中">
          {[0, 1, 2, 3].map((n) => (
            <Skeleton key={n} width="100%" height={76} radius={3} index={n} />
          ))}
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="empty-state-wrap">
          <EmptyState
            title={items.length === 0 ? '冰箱目前空空的！' : '這個篩選條件下沒有食材'}
            description={
              items.length === 0
                ? '點右上角新增食材，開始記錄宿舍冰箱的保存期限。'
                : '切回「全部」查看冰箱裡的其他食材。'
            }
            actions={
              items.length === 0 ? (
                <Button
                  variant="primary"
                  size="md"
                  label="新增第一樣食材"
                  onClick={onOpenAddModal}
                />
              ) : (
                <Button
                  variant="secondary"
                  size="md"
                  label="顯示全部食材"
                  onClick={() => {
                    setUrgencyFilter('all');
                    setOwnerFilter('all');
                  }}
                />
              )
            }
          />
        </div>
      ) : (
        <div className="ingredient-list">
          {filteredItems.map((item) => (
            <IngredientCard
              key={item.id}
              item={item}
              selected={selectedIds.includes(item.id)}
              disabledSelect={selectedIds.length >= MAX_SELECT}
              isNew={newlyAddedId === item.id}
              onToggle={onToggleSelect}
              onMarkWasted={onMarkWasted}
              onDelete={onDeleteItem}
            />
          ))}
        </div>
      )}

      {/* 底部浮動勾選操作列（核心步驟 2） */}
      <div className="floating-action-dock">
        <div className={`selection-bar ${selectedItems.length > 0 ? 'has-selection' : ''}`}>
          <div className="selection-bar-info">
            {selectedItems.length === 0 ? (
              <span className="selection-placeholder">
                勾選上方食材（1–{MAX_SELECT} 樣）即可找救援料理
              </span>
            ) : (
              <>
                <div className="selection-summary-row">
                  <span className="selection-count-text tabular-nums">
                    已選 {selectedItems.length}/{MAX_SELECT} 樣
                  </span>
                  <button
                    type="button"
                    className="selection-clear-btn"
                    onClick={onClearSelection}
                  >
                    清除
                  </button>
                </div>
                <div className="selection-names-preview">
                  {selectedItems.map((it) => `${it.emoji || ''} ${it.name}`).join('、')}
                </div>
              </>
            )}
          </div>

          <Button
            variant="primary"
            size="lg"
            width="100%"
            icon={<SparklesIcon size={16} />}
            endContent={!submittingSuggestions ? <ArrowRightIcon size={16} /> : undefined}
            label={submittingSuggestions ? '尋找食譜中…' : '給它們第二次機會'}
            isDisabled={selectedItems.length === 0}
            isLoading={submittingSuggestions}
            onClick={onRequestSuggestions}
            className="primary-rescue-btn"
          />
        </div>
      </div>
    </div>
  );
}
