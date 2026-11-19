import React, { useMemo, useState } from 'react';
import { Badge } from '@astryxdesign/core/Badge';
import { Banner } from '@astryxdesign/core/Banner';
import { Button } from '@astryxdesign/core/Button';
import { ClickableCard } from '@astryxdesign/core/ClickableCard';
import { EmptyState } from '@astryxdesign/core/EmptyState';
import { SegmentedControl, SegmentedControlItem } from '@astryxdesign/core/SegmentedControl';
import { Skeleton } from '@astryxdesign/core/Skeleton';
import { Token } from '@astryxdesign/core/Token';
import { ingredientsMatch, isExpiredUnsafe } from '../data/mockData';
import {
  ApplianceIcon,
  ArrowLeftIcon,
  ChevronRightIcon,
  ClockIcon,
  SparklesIcon,
  TrashIcon,
} from './Icons';

export function SuggestionsView({
  selectedItems,
  suggestionsData,
  loading,
  markingWasted,
  onBack,
  onSelectRecipe,
  onMarkSelectedWasted,
}) {
  const [toolFilter, setToolFilter] = useState('all');

  const recipes = suggestionsData?.recipes ?? [];
  const source = suggestionsData?.source ?? 'rules';

  const filteredRecipes = useMemo(() => {
    if (toolFilter === 'all') return recipes;
    return recipes.filter((entry) => entry.recipe.tool === toolFilter);
  }, [recipes, toolFilter]);

  const selectedValueSum = useMemo(
    () => selectedItems.reduce((sum, it) => sum + (Number(it.price) || 0), 0),
    [selectedItems]
  );

  const expiredUnsafeItems = useMemo(
    () => selectedItems.filter(isExpiredUnsafe),
    [selectedItems]
  );

  const allSelectedAreUnsafeExpired =
    selectedItems.length > 0 && expiredUnsafeItems.length === selectedItems.length;

  return (
    <div className="view-suggestions">
      <div className="subview-header">
        <Button
          variant="ghost"
          size="sm"
          icon={<ArrowLeftIcon size={16} />}
          label="回冰箱"
          onClick={onBack}
        />
        <h1 className="subview-title">救援料理推薦</h1>
        <Badge
          variant={source === 'ai' ? 'purple' : 'neutral'}
          label={source === 'ai' ? 'AI 推薦' : '規則式'}
        />
      </div>

      {/* 已勾選食材摘要 */}
      <section className="selected-context-card" aria-label="本次勾選的食材">
        <div className="selected-context-top">
          <span className="selected-context-label">準備搶救的食材</span>
          {selectedValueSum > 0 && (
            <span className="selected-context-value tabular-nums">
              總價值 NT${selectedValueSum}
            </span>
          )}
        </div>
        <div className="selected-context-pills">
          {selectedItems.map((it) => (
            <Token
              key={it.id}
              label={`${it.emoji || '🥫'} ${it.name}${it.days_left < 0 ? '（已過期）' : ''}`}
              color={it.urgency === 'red' ? 'red' : it.urgency === 'yellow' ? 'yellow' : 'green'}
              size="sm"
            />
          ))}
        </div>
      </section>

      {/* 部分勾選含高風險過期食材但仍有其他可救援食材時，顯示溫馨食安提示 */}
      {expiredUnsafeItems.length > 0 && !allSelectedAreUnsafeExpired && (
        <Banner
          status="warning"
          title="已略過高風險過期食材"
          description={`為了安全，已過期的「${expiredUnsafeItems.map((it) => it.name).join('、')}」不列入推薦，建議回冰箱直接標記丟掉。`}
        />
      )}

      {/* 器具快篩（Astryx SegmentedControl） */}
      {recipes.length > 0 && (
        <div className="tool-segment-wrap">
          <SegmentedControl
            value={toolFilter}
            onChange={setToolFilter}
            label="依宿舍器具篩選"
            size="sm"
          >
            <SegmentedControlItem value="all" label={`全部 (${recipes.length})`} />
            <SegmentedControlItem
              value="電鍋"
              label="電鍋"
              icon={<ApplianceIcon tool="電鍋" size={14} />}
            />
            <SegmentedControlItem
              value="微波爐"
              label="微波爐"
              icon={<ApplianceIcon tool="微波爐" size={14} />}
            />
          </SegmentedControl>
        </div>
      )}

      {loading ? (
        <div className="skeleton-list" aria-label="配對推薦食譜中">
          {[0, 1, 2].map((n) => (
            <Skeleton key={n} width="100%" height={180} radius={3} index={n} />
          ))}
        </div>
      ) : recipes.length === 0 && allSelectedAreUnsafeExpired ? (
        <div className="safety-empty-card">
          <Banner
            status="warning"
            title="為了安全，過期的肉類、海鮮、乳製品與豆腐不建議再食用"
            description={`你勾選的「${expiredUnsafeItems.map((it) => it.name).join('、')}」已經過期，容易滋生細菌或變質，系統不會拿來配對食譜。`}
          />
          <div className="safety-empty-actions">
            <Button
              variant="destructive"
              size="md"
              width="100%"
              icon={<TrashIcon size={16} />}
              label={
                markingWasted
                  ? '標記丟掉中…'
                  : `標記丟掉（${expiredUnsafeItems.length} 樣）並回冰箱`
              }
              isLoading={markingWasted}
              onClick={() => onMarkSelectedWasted(expiredUnsafeItems)}
            />
            <Button
              variant="secondary"
              size="md"
              width="100%"
              label="回冰箱重新勾選"
              isDisabled={markingWasted}
              onClick={onBack}
            />
          </div>
        </div>
      ) : filteredRecipes.length === 0 ? (
        <div className="empty-state-wrap">
          <EmptyState
            title={
              recipes.length === 0
                ? '暫時找不到剛好符合的宿舍食譜'
                : `目前沒有只用「${toolFilter}」的推薦食譜`
            }
            description={
              recipes.length === 0
                ? '試著多勾選 1–2 樣冰箱常見食材（像雞蛋、白飯、吐司、豆腐），配對率會高很多！'
                : '切換回「全部」看看另一種器具的救援料理吧。'
            }
            actions={
              recipes.length === 0 ? (
                <Button
                  variant="secondary"
                  size="md"
                  label="回去重新勾選食材"
                  onClick={onBack}
                />
              ) : (
                <Button
                  variant="secondary"
                  size="md"
                  label="顯示全部器具"
                  onClick={() => setToolFilter('all')}
                />
              )
            }
          />
        </div>
      ) : (
        <div className="recipe-list">
          {filteredRecipes.map((entry, idx) => {
            const { recipe, uses = [], also_in_fridge = [], missing = [], score, reason } = entry;
            // 只顯示「不在 uses 且不在 also_in_fridge」的可省略加分食材，避免矛盾
            const extraOptionalList = (recipe.optional ?? []).filter(
              (opt) =>
                !uses.some((u) => ingredientsMatch(u, opt)) &&
                !also_in_fridge.some((a) => ingredientsMatch(a.name, opt))
            );
            const isTopPick = idx === 0 && toolFilter === 'all';
            const hasExpiredWarning = Boolean(
              reason && reason.includes('已過期，請先確認外觀氣味再使用')
            );

            return (
              <ClickableCard
                key={recipe.id}
                label={`查看食譜：${recipe.title}`}
                padding={4}
                elevation="low"
                className={`recipe-card ${isTopPick ? 'is-top-pick' : ''}`}
                onClick={() => onSelectRecipe(entry)}
              >
                <div className="recipe-card-inner">
                  <div className="recipe-card-head">
                    <span className="recipe-emoji-tile" aria-hidden="true">
                      {recipe.emoji || '🍲'}
                    </span>
                    <div className="recipe-head-main">
                      <div className="recipe-title-row">
                        <h2 className="recipe-title">{recipe.title}</h2>
                        <Badge
                          variant="green"
                          label={`${score} 分`}
                          className="tabular-nums"
                        />
                      </div>
                      <div className="recipe-meta-pills">
                        <Badge
                          variant={recipe.tool === '微波爐' ? 'teal' : 'orange'}
                          icon={<ApplianceIcon tool={recipe.tool} size={13} />}
                          label={recipe.tool}
                        />
                        <Badge
                          variant="neutral"
                          icon={<ClockIcon size={13} />}
                          label={`${recipe.minutes} 分鐘`}
                          className="tabular-nums"
                        />
                        {isTopPick && <Badge variant="success" label="最佳救援" />}
                      </div>
                    </div>
                  </div>

                  {reason && (
                    <div
                      className={`recipe-reason-strip ${
                        hasExpiredWarning ? 'is-safety-note' : ''
                      }`}
                    >
                      <SparklesIcon size={14} />
                      <span>{reason}</span>
                    </div>
                  )}

                  <div className="recipe-ingredients-summary">
                    <div className="ing-summary-row">
                      <span className="ing-summary-label">用到你選的</span>
                      <div className="ing-pill-group">
                        {uses.map((u) => (
                          <Token key={u} label={u} color="green" size="sm" />
                        ))}
                      </div>
                    </div>

                    {also_in_fridge.length > 0 && (
                      <div className="ing-summary-row">
                        <span className="ing-summary-label">冰箱裡也有</span>
                        <div className="ing-pill-group">
                          {also_in_fridge.map((it) => (
                            <Token
                              key={it.id ?? it.name}
                              label={
                                it.days_left < 0
                                  ? `${it.name}（已過期）`
                                  : it.days_left <= 1
                                    ? `${it.name}（快到期）`
                                    : it.name
                              }
                              color="teal"
                              size="sm"
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="ing-summary-row">
                      <span className="ing-summary-label">還缺食材</span>
                      <div className="ing-pill-group">
                        {missing.length === 0 ? (
                          <Badge variant="success" label="零缺料！現在就能做" />
                        ) : (
                          missing.map((m) => (
                            <Token key={m} label={m} color="orange" size="sm" />
                          ))
                        )}
                      </div>
                    </div>

                    {extraOptionalList.length > 0 && (
                      <div className="ing-optional-note">
                        可省略加分：{extraOptionalList.join('、')}
                      </div>
                    )}
                  </div>

                  <div className="recipe-card-foot">
                    <span>看完整步驟，煮完記錄救援</span>
                    <ChevronRightIcon size={16} />
                  </div>
                </div>
              </ClickableCard>
            );
          })}
        </div>
      )}
    </div>
  );
}
