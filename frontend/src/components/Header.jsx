import React, { useEffect, useRef, useState } from 'react';
import { Button } from '@astryxdesign/core/Button';
import { StatusDot } from '@astryxdesign/core/StatusDot';
import { RefreshIcon, SproutIcon } from './Icons';

export function Header({
  connection,
  onModeChange,
  onResetMock,
  onBrandClick,
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const popoverRef = useRef(null);

  useEffect(() => {
    if (!menuOpen) return;
    function handleOutsideClick(e) {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [menuOpen]);

  const isLive = connection.activeSource === 'api';

  const pillLabel = isLive
    ? connection.backendAiMode === 'online'
      ? '後端 · AI'
      : '後端 API'
    : '示範模式';

  async function handleSelectMode(mode) {
    setSwitching(true);
    try {
      await onModeChange(mode);
    } finally {
      setSwitching(false);
      setMenuOpen(false);
    }
  }

  return (
    <header className="app-header">
      <button
        type="button"
        className="brand-button"
        onClick={onBrandClick}
        aria-label="回到冰箱第二春首頁"
      >
        <span className="brand-mark">
          <SproutIcon size={20} />
        </span>
        <span className="brand-text">
          <span className="brand-title">冰箱第二春</span>
          <span className="brand-subtitle">宿舍快過期食材救援</span>
        </span>
      </button>

      <div className="mode-control" ref={popoverRef}>
        <button
          type="button"
          className={`mode-pill ${isLive ? 'mode-pill--live' : 'mode-pill--mock'}`}
          onClick={() => setMenuOpen((prev) => !prev)}
          aria-expanded={menuOpen}
          aria-haspopup="menu"
          title="切換資料來源（後端 API / 離線示範）"
        >
          <span aria-hidden="true" className="mode-dot-wrap">
            <StatusDot
              variant={isLive ? 'success' : 'warning'}
              isPulsing={isLive}
              label=""
            />
          </span>
          <span>{pillLabel}</span>
        </button>

        {menuOpen && (
          <div className="mode-popover" role="menu">
            <div className="mode-popover-title">資料來源切換</div>
            <p className="mode-popover-desc">
              目前使用：<strong>{isLive ? '真實後端 API' : '內建示範資料（Mock）'}</strong>
            </p>

            <div className="mode-options">
              <button
                type="button"
                role="menuitemradio"
                aria-checked={connection.preferredMode === 'auto'}
                className={`mode-option ${connection.preferredMode === 'auto' ? 'is-active' : ''}`}
                disabled={switching}
                onClick={() => handleSelectMode('auto')}
              >
                <span className="mode-option-label">自動偵測（推薦）</span>
                <span className="mode-option-hint">優先連後端，連不到自動切示範資料</span>
              </button>

              <button
                type="button"
                role="menuitemradio"
                aria-checked={connection.preferredMode === 'mock'}
                className={`mode-option ${connection.preferredMode === 'mock' ? 'is-active' : ''}`}
                disabled={switching}
                onClick={() => handleSelectMode('mock')}
              >
                <span className="mode-option-label">示範資料（Mock）</span>
                <span className="mode-option-hint">純前端內建 16 樣食材與 19 道宿舍食譜</span>
              </button>

              <button
                type="button"
                role="menuitemradio"
                aria-checked={connection.preferredMode === 'api'}
                className={`mode-option ${connection.preferredMode === 'api' ? 'is-active' : ''}`}
                disabled={switching}
                onClick={() => handleSelectMode('api')}
              >
                <span className="mode-option-label">連線後端 API</span>
                <span className="mode-option-hint">串接相對路徑 /api/*（失聯時自動備援）</span>
              </button>
            </div>

            {!isLive && (
              <div className="mode-popover-footer">
                <Button
                  variant="secondary"
                  size="sm"
                  width="100%"
                  icon={<RefreshIcon size={14} />}
                  label="重置示範資料（恢復 16 樣）"
                  onClick={() => {
                    onResetMock();
                    setMenuOpen(false);
                  }}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
