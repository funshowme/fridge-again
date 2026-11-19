import React, { useState } from 'react';
import { Badge } from '@astryxdesign/core/Badge';
import { Button } from '@astryxdesign/core/Button';
import { IconButton } from '@astryxdesign/core/IconButton';
import { isExpiredUnsafe } from '../data/mockData';
import { CheckIcon, MoreIcon, TrashIcon } from './Icons';

function formatDaysLeft(daysLeft) {
  if (daysLeft < 0) return `已過期 ${Math.abs(daysLeft)} 天`;
  if (daysLeft === 0) return '今天到期';
  if (daysLeft === 1) return '明天到期';
  return `剩 ${daysLeft} 天`;
}

function formatShortDate(dateStr) {
  if (!dateStr || !dateStr.includes('-')) return '';
  const [, m, d] = dateStr.split('-');
  return `${Number(m)}/${Number(d)}`;
}

function getUrgencyBadgeVariant(urgency) {
  if (urgency === 'red') return 'error';
  if (urgency === 'yellow') return 'warning';
  return 'success';
}

export function IngredientCard({
  item,
  selected,
  disabledSelect,
  isNew,
  onToggle,
  onMarkWasted,
  onDelete,
}) {
  const [actionsOpen, setActionsOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const urgencyClass = `urgency-${item.urgency || 'green'}`;
  const isExpired = Number(item.days_left ?? 0) < 0;
  const expiredUnsafe = isExpiredUnsafe(item);
  const daysText = formatDaysLeft(item.days_left);

  async function handleAction(fn) {
    setBusy(true);
    try {
      await fn(item);
    } finally {
      setBusy(false);
      setActionsOpen(false);
    }
  }

  return (
    <article
      className={`ingredient-card ${urgencyClass} ${isExpired ? 'is-expired' : ''} ${
        selected ? 'is-selected' : ''
      } ${isNew ? 'is-newly-added' : ''}`}
    >
      <div className="ingredient-main">
        <button
          type="button"
          className="ingredient-select-area"
          role="checkbox"
          aria-checked={selected}
          disabled={!selected && disabledSelect}
          onClick={() => onToggle(item.id)}
        >
          <span className={`custom-checkbox ${selected ? 'is-checked' : ''}`} aria-hidden="true">
            {selected && <CheckIcon size={13} />}
          </span>

          <span className="ingredient-emoji-tile" aria-hidden="true">
            {item.emoji || '🥫'}
          </span>

          <span className="ingredient-info">
            <span className="ingredient-name-row">
              <span className="ingredient-name">{item.name}</span>
              <span className="ingredient-qty tabular-nums">
                {item.quantity} {item.unit}
              </span>
            </span>

            <span className="ingredient-meta-row">
              <span className="owner-tag">{item.owner ? item.owner : '共用'}</span>
              {item.price > 0 && (
                <span className="price-tag tabular-nums">NT${item.price}</span>
              )}
              <span className="date-tag tabular-nums">{formatShortDate(item.expires_on)} 到期</span>
            </span>

            {isExpired && (
              <span className={`expired-safety-hint ${expiredUnsafe ? 'is-high-risk' : ''}`}>
                {expiredUnsafe
                  ? '過期生鮮不建議食用，建議直接標記丟掉'
                  : '已過期 · 烹調前請確認外觀氣味'}
              </span>
            )}
          </span>
        </button>

        <div className="ingredient-right">
          <Badge
            variant={getUrgencyBadgeVariant(item.urgency)}
            label={daysText}
            className={`urgency-astrx-badge tabular-nums ${
              isExpired ? 'is-expired-badge' : ''
            }`}
          />

          <IconButton
            label={`操作 ${item.name}`}
            icon={<MoreIcon size={16} />}
            variant="ghost"
            size="sm"
            onClick={() => setActionsOpen((prev) => !prev)}
            aria-expanded={actionsOpen}
          />
        </div>
      </div>

      {actionsOpen && (
        <div className="ingredient-action-tray">
          <Button
            variant="destructive"
            size="sm"
            icon={<TrashIcon size={14} />}
            label="壞了，標記丟掉"
            isDisabled={busy}
            onClick={() => handleAction(onMarkWasted)}
          />
          <Button
            variant="secondary"
            size="sm"
            label="刪除誤填"
            isDisabled={busy}
            onClick={() => handleAction(onDelete)}
          />
          <Button
            variant="ghost"
            size="sm"
            label="取消"
            isDisabled={busy}
            onClick={() => setActionsOpen(false)}
          />
        </div>
      )}
    </article>
  );
}
