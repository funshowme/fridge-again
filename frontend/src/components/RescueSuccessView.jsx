import React from 'react';
import { Badge } from '@astryxdesign/core/Badge';
import { Button } from '@astryxdesign/core/Button';
import { Card } from '@astryxdesign/core/Card';
import { Token } from '@astryxdesign/core/Token';
import { CheckIcon, SparklesIcon } from './Icons';

export function RescueSuccessView({ rescueResult, onBackHome }) {
  const { recipe, rescuedItems, rescue, stats } = rescueResult;
  const savedThisTime = rescue?.saved_ntd ?? 0;
  const rescueRatePct = Math.round((stats?.rescue_rate ?? 0) * 100);
  const recent = stats?.recent ?? [];

  return (
    <div className="view-success">
      <Card padding={5} elevation="low" className="success-hero-card" aria-live="polite">
        <div className="confetti-layer" aria-hidden="true">
          <span className="confetti-dot d1" />
          <span className="confetti-dot d2" />
          <span className="confetti-dot d3" />
          <span className="confetti-dot d4" />
          <span className="confetti-dot d5" />
          <span className="confetti-dot d6" />
        </div>

        <div className="success-check-ring" aria-hidden="true">
          <CheckIcon size={34} />
        </div>

        <Badge
          variant="success"
          icon={<SparklesIcon size={13} />}
          label="Second Chance 達成！"
          className="success-kicker-badge"
        />

        <h1 className="success-headline">救援成功！</h1>
        <p className="success-subcopy">
          你用「<strong>{recipe.emoji} {recipe.title}</strong>」給了 {rescuedItems.length} 樣食材第二次機會
        </p>

        <div className="success-savings-box">
          <div className="success-savings-label">這一餐直接幫荷包省下</div>
          <div className="success-savings-amount tabular-nums">
            NT${savedThisTime.toLocaleString('zh-TW')}
          </div>
          <div className="success-rescued-chips">
            {rescuedItems.map((it) => (
              <Token
                key={it.id}
                label={`${it.emoji || '🥫'} ${it.name}`}
                color="green"
                size="sm"
              />
            ))}
          </div>
          <p className="success-removed-note">以上食材已自動從冰箱清單移出</p>
        </div>
      </Card>

      {/* 更新後的累計戰績 */}
      <Card padding={4} elevation="low" className="success-stats-card" aria-label="更新後的救援統計">
        <h2 className="success-stats-title">最新冰箱救援戰績</h2>
        <div className="success-stats-grid">
          <div className="success-stat-tile">
            <span className="success-stat-num tabular-nums">
              {stats?.rescued_count ?? 0}
              <small>樣</small>
            </span>
            <span className="success-stat-label">累計救回</span>
          </div>
          <div className="success-stat-tile">
            <span className="success-stat-num tabular-nums">
              <small>NT$</small>
              {(stats?.saved_ntd ?? 0).toLocaleString('zh-TW')}
            </span>
            <span className="success-stat-label">累計省下</span>
          </div>
          <div className="success-stat-tile">
            <span className="success-stat-num tabular-nums">
              {rescueRatePct}
              <small>%</small>
            </span>
            <span className="success-stat-label">救援率</span>
          </div>
        </div>

        {recent.length > 0 && (
          <div className="success-recent-box">
            <div className="success-recent-heading">最近救援紀錄</div>
            <ul className="success-recent-list">
              {recent.slice(0, 3).map((rec, idx) => (
                <li
                  key={rec.id}
                  className={`success-recent-row ${idx === 0 ? 'is-latest' : ''}`}
                >
                  <span className="success-recent-recipe">{rec.recipe_title}</span>
                  <span className="success-recent-items">
                    {rec.item_names.join('、')}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Card>

      <div className="success-actions">
        <Button
          variant="primary"
          size="lg"
          width="100%"
          label="回到我的冰箱"
          onClick={onBackHome}
          className="primary-home-btn"
        />
      </div>
    </div>
  );
}
