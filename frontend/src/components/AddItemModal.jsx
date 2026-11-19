import React, { useState } from 'react';
import { Banner } from '@astryxdesign/core/Banner';
import { Button } from '@astryxdesign/core/Button';
import { Dialog, DialogHeader } from '@astryxdesign/core/Dialog';
import { Field } from '@astryxdesign/core/Field';
import { TextInput } from '@astryxdesign/core/TextInput';
import { addDays, getTaipeiTodayStr } from '../data/mockData';
import { PlusIcon } from './Icons';

const PRESETS = [
  { name: '雞蛋', emoji: '🥚', quantity: 2, unit: '顆', price: 20 },
  { name: '白飯', emoji: '🍚', quantity: 1, unit: '碗', price: 15 },
  { name: '嫩豆腐', emoji: '🧈', quantity: 1, unit: '盒', price: 25 },
  { name: '吐司', emoji: '🍞', quantity: 2, unit: '片', price: 20 },
  { name: '牛奶', emoji: '🥛', quantity: 1, unit: '瓶', price: 65 },
  { name: '香蕉', emoji: '🍌', quantity: 2, unit: '根', price: 25 },
  { name: '起司片', emoji: '🧀', quantity: 2, unit: '片', price: 25 },
  { name: '高麗菜', emoji: '🥬', quantity: 1, unit: '顆', price: 50 },
];

export function AddItemModal({ isOpen, existingOwners, onClose, onSubmit }) {
  const today = getTaipeiTodayStr();
  const [name, setName] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [unit, setUnit] = useState('份');
  const [expiresOn, setExpiresOn] = useState(addDays(today, 2));
  const [owner, setOwner] = useState('');
  const [price, setPrice] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const ownerQuickOptions = Array.from(
    new Set([...(existingOwners || []), '小明', '小美', '阿哲'])
  ).filter(Boolean);

  function resetFields() {
    setName('');
    setQuantity('1');
    setUnit('份');
    setExpiresOn(addDays(getTaipeiTodayStr(), 2));
    setOwner('');
    setPrice('');
    setError('');
    setSubmitting(false);
  }

  function handleOpenChange(open) {
    if (!open) {
      resetFields();
      onClose();
    }
  }

  function applyPreset(preset) {
    setName(preset.name);
    setQuantity(String(preset.quantity));
    setUnit(preset.unit);
    setPrice(String(preset.price));
    setError('');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim()) {
      setError('請輸入食材名稱');
      return;
    }
    if (!expiresOn) {
      setError('請選擇到期日');
      return;
    }

    setError('');
    setSubmitting(true);
    try {
      await onSubmit({
        name: name.trim(),
        quantity: Number(quantity) > 0 ? Number(quantity) : 1,
        unit: unit.trim() || '個',
        expires_on: expiresOn,
        owner: owner.trim(),
        price: price === '' ? 0 : Math.max(0, Math.round(Number(price) || 0)),
      });
      resetFields();
    } catch (err) {
      setError(err?.message || '新增失敗，請稍後再試');
      setSubmitting(false);
    }
  }

  const quickDates = [
    { label: '今天', value: today },
    { label: '明天', value: addDays(today, 1) },
    { label: '+3 天', value: addDays(today, 3) },
    { label: '+7 天', value: addDays(today, 7) },
  ];

  return (
    <Dialog
      isOpen={isOpen}
      onOpenChange={handleOpenChange}
      purpose="form"
      width={440}
      maxHeight="90dvh"
      className="add-item-dialog"
    >
      <div className="dialog-body-shell">
        <DialogHeader
          title="新增冰箱食材"
          subtitle="記下到期日與室友，不再放到忘記"
          onOpenChange={handleOpenChange}
        />

        <form className="modal-form" onSubmit={handleSubmit} noValidate>
          {/* 常用宿舍食材快選 */}
          <div className="form-group">
            <span className="form-label-sm">常用食材快填</span>
            <div className="preset-strip">
              {PRESETS.map((p) => (
                <button
                  key={p.name}
                  type="button"
                  className={`preset-chip ${name === p.name ? 'is-active' : ''}`}
                  onClick={() => applyPreset(p)}
                >
                  <span aria-hidden="true">{p.emoji}</span>
                  <span>{p.name}</span>
                </button>
              ))}
            </div>
          </div>

          <TextInput
            label="食材名稱"
            isRequired
            width="100%"
            placeholder="例如：嫩豆腐、雞蛋、隔夜白飯"
            value={name}
            onChange={(val) => setName(val)}
            hasAutoFocus
          />

          <div className="form-row-2">
            <TextInput
              label="數量"
              width="100%"
              inputMode="decimal"
              value={quantity}
              onChange={(val) => setQuantity(val)}
            />

            <TextInput
              label="單位"
              width="100%"
              placeholder="顆 / 盒 / 包"
              value={unit}
              onChange={(val) => setUnit(val)}
            />
          </div>

          <Field label="到期日" isRequired width="100%">
            <div className="date-field-stack">
              <div className="quick-date-row">
                {quickDates.map((qd) => (
                  <button
                    key={qd.label}
                    type="button"
                    className={`quick-pill ${expiresOn === qd.value ? 'is-active' : ''}`}
                    onClick={() => setExpiresOn(qd.value)}
                  >
                    {qd.label}
                  </button>
                ))}
              </div>
              <input
                type="date"
                className="native-date-input tabular-nums"
                value={expiresOn}
                onChange={(e) => setExpiresOn(e.target.value)}
                required
              />
            </div>
          </Field>

          <div className="form-row-2">
            <div className="owner-field-col">
              <TextInput
                label="屬於哪位室友"
                width="100%"
                placeholder="留空代表共用"
                value={owner}
                onChange={(val) => setOwner(val)}
              />
              <div className="quick-owner-row">
                {ownerQuickOptions.slice(0, 4).map((ow) => (
                  <button
                    key={ow}
                    type="button"
                    className={`mini-chip ${owner === ow ? 'is-active' : ''}`}
                    onClick={() => setOwner(owner === ow ? '' : ow)}
                  >
                    {ow}
                  </button>
                ))}
              </div>
            </div>

            <TextInput
              label="估計價值（NT$）"
              width="100%"
              inputMode="numeric"
              placeholder="例：30"
              value={price}
              onChange={(val) => setPrice(val)}
            />
          </div>

          {error && (
            <Banner status="error" title={error} />
          )}

          <div className="modal-footer">
            <Button
              variant="ghost"
              size="md"
              label="取消"
              onClick={() => handleOpenChange(false)}
            />
            <Button
              type="submit"
              variant="primary"
              size="md"
              icon={<PlusIcon size={16} />}
              label={submitting ? '加入中…' : '放入冰箱'}
              isLoading={submitting}
            />
          </div>
        </form>
      </div>
    </Dialog>
  );
}
