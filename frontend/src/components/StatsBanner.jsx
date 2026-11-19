import React, { useState } from 'react';
import { Card } from '@astryxdesign/core/Card';
import { ChevronDownIcon, SparklesIcon } from './Icons';

export function StatsBanner({ stats, loading }) {
  const [showRecent, setShowRecent] = useState(false);

  const rescuedCount = stats?.rescued_count ?? 0;
  const savedNtd = stats?.saved_ntd ?? 0;
  const wastedCount = stats?.wasted_count ?? 0;
  const rescueRatePct = Math.round((stats?.rescue_rate ?? 0) * 100);
  const recent = stats?.recent ?? [];

  return (
    <Card padding={4} elevation="low" className="stats-banner" aria-label="救援成果統計">
      <div className="stats-banner-top">
        <div className="stats-banner-badge">
          <SparklesIcon size={13} />
          <span>冰箱救援戰績</span>
        </div>
        <span className="stats-wasted-chip tabular-nums">
          丟掉 {wastedCount} 樣
        </span>
      </div>

      <div className={`stats-grid ${loading ? 'is-loading' : ''}`}>
        <div className="stat-cell">
          <div className="stat-value tabular-nums">
            {rescuedCount}
            <span className="stat-unit">樣</span>
          </div>
          <div className="stat-label">已救回食材</div>
        </div>

        <div className="stat-divider" aria-hidden="true" />

        <div className="stat-cell">
          <div className="stat-value tabular-nums">
            <span className="stat-currency">NT$</span>
            {savedNtd.toLocaleString('zh-TW')}
          </div>
          <div className="stat-label">累計省下</div>
        </div>

        <div className="stat-divider" aria-hidden="true" />

        <div className="stat-cell">
          <div className="stat-value tabular-nums">
            {rescueRatePct}
            <span className="stat-unit">%</span>
          </div>
          <div className="stat-label">救援成功率</div>
        </div>
      </div>

      {recent.length > 0 && (
        <div className="stats-recent-wrap">
          <button
            type="button"
            className="stats-recent-toggle"
            onClick={() => setShowRecent((prev) => !prev)}
            aria-expanded={showRecent}
          >
            <span className="stats-recent-preview">
              最近救援：{recent[0].recipe_title}（{recent[0].item_names.join('、')}）
            </span>
            <ChevronDownIcon
              size={14}
              className={`stats-chevron ${showRecent ? 'is-open' : ''}`}
            />
          </button>

          {showRecent && (
            <ul className="stats-recent-list">
              {recent.map((rec) => (
                <li key={rec.id} className="stats-recent-item">
                  <span className="stats-recent-title">{rec.recipe_title}</span>
                  <span className="stats-recent-items">
                    救回 {rec.item_names.join('、')}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Card>
  );
}
