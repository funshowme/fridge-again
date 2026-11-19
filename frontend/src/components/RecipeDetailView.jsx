import React, { useMemo, useState } from 'react';
import { Badge } from '@astryxdesign/core/Badge';
import { Banner } from '@astryxdesign/core/Banner';
import { Button } from '@astryxdesign/core/Button';
import { Card } from '@astryxdesign/core/Card';
import { Token } from '@astryxdesign/core/Token';
import {
  ApplianceIcon,
  ArrowLeftIcon,
  CheckIcon,
  ClockIcon,
  SparklesIcon,
} from './Icons';
import { ingredientsMatch } from '../data/mockData';

export function RecipeDetailView({
  suggestion,
  allFridgeItems,
  selectedItems,
  submittingRescue,
  onBack,
  onConfirmCooked,
}) {
  const [checkedSteps, setCheckedSteps] = useState([]);

  const { recipe, uses, uses_item_ids, also_in_fridge = [], missing, score, reason } = suggestion;

  const itemsToRescue = useMemo(() => {
    const idSet = new Set(
      uses_item_ids && uses_item_ids.length > 0
        ? uses_item_ids
        : selectedItems.map((it) => it.id)
    );
    const matched = allFridgeItems.filter((it) => idSet.has(it.id));
    return matched.length > 0 ? matched : selectedItems;
  }, [uses_item_ids, allFridgeItems, selectedItems]);

  const estimatedSaved = useMemo(
    () => itemsToRescue.reduce((sum, it) => sum + (Number(it.price) || 0), 0),
    [itemsToRescue]
  );

  const hasExpiredItem = useMemo(
    () =>
      itemsToRescue.some((it) => Number(it.days_left ?? 0) < 0) ||
      also_in_fridge.some((it) => Number(it.days_left ?? 0) < 0),
    [itemsToRescue, also_in_fridge]
  );

  const ingredientChecklist = useMemo(() => {
    const optionalList = recipe.optional ?? [];

    return (recipe.ingredients ?? []).map((ing) => {
      let badgeVariant = 'info';
      let label = '冰箱裡也有';

      if (uses.some((u) => ingredientsMatch(u, ing))) {
        badgeVariant = 'success';
        label = '已勾選救援';
      } else if (also_in_fridge.some((a) => ingredientsMatch(a.name, ing))) {
        badgeVariant = 'teal';
        label = optionalList.some((o) => ingredientsMatch(o, ing))
          ? '冰箱也有（可省）'
          : '冰箱裡也有';
      } else if (optionalList.some((o) => ingredientsMatch(o, ing))) {
        const inFridge = allFridgeItems.some((it) => ingredientsMatch(it.name, ing));
        badgeVariant = 'neutral';
        label = inFridge ? '冰箱也有（可省）' : '可省略';
      } else if (missing.some((m) => ingredientsMatch(m, ing))) {
        badgeVariant = 'warning';
        label = '需自備';
      }

      return { name: ing, badgeVariant, label };
    });
  }, [recipe, uses, also_in_fridge, missing, allFridgeItems]);

  function toggleStep(index) {
    setCheckedSteps((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  }

  return (
    <div className="view-detail">
      <div className="subview-header">
        <Button
          variant="ghost"
          size="sm"
          icon={<ArrowLeftIcon size={16} />}
          label="回推薦"
          onClick={onBack}
        />
        <h1 className="subview-title">食譜詳情</h1>
        <Badge variant="green" label={`${score} 分`} className="tabular-nums" />
      </div>

      {/* 食譜主視覺卡 */}
      <Card padding={4} elevation="low" className="detail-hero-card">
        <div className="detail-hero-top">
          <div className="detail-emoji-tile" aria-hidden="true">
            {recipe.emoji || '🍲'}
          </div>
          <div className="detail-hero-text">
            <h2 className="detail-recipe-title">{recipe.title}</h2>
            <div className="recipe-meta-pills">
              <Badge
                variant={recipe.tool === '微波爐' ? 'teal' : 'orange'}
                icon={<ApplianceIcon tool={recipe.tool} size={13} />}
                label={`只用${recipe.tool}`}
              />
              <Badge
                variant="neutral"
                icon={<ClockIcon size={13} />}
                label={`約 ${recipe.minutes} 分鐘`}
                className="tabular-nums"
              />
            </div>
          </div>
        </div>

        {reason && (
          <div
            className={`recipe-reason-strip ${
              hasExpiredItem ? 'is-safety-note' : ''
            }`}
          >
            <SparklesIcon size={14} />
            <span>{reason}</span>
          </div>
        )}
      </Card>

      {hasExpiredItem && (
        <Banner
          status="warning"
          title="過期食材食安提醒"
          description="本料理包含已過期食材，烹調前請先確認外觀、質地與氣味正常再使用。"
        />
      )}

      {/* 本次將救回的食材預覽 */}
      <Card padding={4} elevation="none" className="detail-section-card detail-rescue-preview">
        <div className="detail-section-head">
          <h3 className="detail-section-title">煮完將救回這些食材</h3>
          {estimatedSaved > 0 && (
            <Badge
              variant="success"
              label={`預計省 NT$${estimatedSaved}`}
              className="tabular-nums"
            />
          )}
        </div>
        <div className="rescue-target-pills">
          {itemsToRescue.map((it) => (
            <Token
              key={it.id}
              label={`${it.emoji || '🥫'} ${it.name}${it.price > 0 ? ` · NT$${it.price}` : ''}`}
              color="green"
              size="sm"
            />
          ))}
        </div>
      </Card>

      {/* 所需食材清單 */}
      <Card padding={4} elevation="none" className="detail-section-card">
        <div className="detail-section-head">
          <h3 className="detail-section-title">準備材料</h3>
          <span className="detail-section-sub tabular-nums">
            共 {ingredientChecklist.length} 樣
          </span>
        </div>
        <ul className="detail-ingredient-list">
          {ingredientChecklist.map((row) => (
            <li key={row.name} className="detail-ingredient-row">
              <span className="detail-ing-name">{row.name}</span>
              <Badge variant={row.badgeVariant} label={row.label} />
            </li>
          ))}
        </ul>
      </Card>

      {/* 步驟清單（可點擊勾選進度） */}
      <Card padding={4} elevation="none" className="detail-section-card">
        <div className="detail-section-head">
          <h3 className="detail-section-title">宿舍極簡步驟</h3>
          <span className="detail-section-sub tabular-nums">
            已完成 {checkedSteps.length}/{recipe.steps.length}
          </span>
        </div>

        <ol className="steps-list">
          {recipe.steps.map((stepText, idx) => {
            const done = checkedSteps.includes(idx);
            return (
              <li key={idx} className={`step-item ${done ? 'is-done' : ''}`}>
                <button
                  type="button"
                  className="step-toggle-btn"
                  aria-pressed={done}
                  onClick={() => toggleStep(idx)}
                >
                  <span className="step-num tabular-nums">
                    {done ? <CheckIcon size={14} /> : idx + 1}
                  </span>
                  <span className="step-text">{stepText}</span>
                </button>
              </li>
            );
          })}
        </ol>
      </Card>

      {/* 底部固定「我煮了！」主按鈕 */}
      <div className="floating-action-dock">
        <div className="detail-cta-bar">
          <Button
            variant="primary"
            size="lg"
            width="100%"
            icon={<CheckIcon size={18} />}
            label={
              submittingRescue
                ? '記錄救援中…'
                : estimatedSaved > 0
                  ? `我煮了！救回 ${itemsToRescue.length} 樣（省 NT$${estimatedSaved}）`
                  : `我煮了！救回這 ${itemsToRescue.length} 樣食材`
            }
            isLoading={submittingRescue}
            onClick={() =>
              onConfirmCooked({
                item_ids: itemsToRescue.map((it) => it.id),
                recipe_id: recipe.id,
                rescuedItems: itemsToRescue,
                recipe,
              })
            }
            className="cooked-confirm-btn"
          />
        </div>
      </div>
    </div>
  );
}
