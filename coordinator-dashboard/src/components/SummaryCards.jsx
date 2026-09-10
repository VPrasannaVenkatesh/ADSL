import React from 'react';
import { ShieldCheck, Eye, AlertTriangle, ShieldAlert, Cpu } from 'lucide-react';

export function SummaryCards({ summary }) {
  const s = summary?.summary || {};
  const total = summary?.total_coordinated || 0;
  const avgScore = summary?.average_risk_score || 0.0;

  const cards = [
    {
      key: 'total',
      label: 'TOTAL COORDINATED',
      value: total,
      sub: `Avg Risk: ${avgScore.toFixed(1)} / 100`,
      color: '#8B5CF6',
      icon: Cpu,
    },
    {
      key: 'ALLOW',
      label: 'ALLOW (0–30)',
      value: s.ALLOW || 0,
      sub: 'Standard flow permitted',
      color: 'var(--allow)',
      icon: ShieldCheck,
    },
    {
      key: 'MONITOR',
      label: 'MONITOR (31–60)',
      value: s.MONITOR || 0,
      sub: 'Behavioral flag logged',
      color: 'var(--monitor)',
      icon: Eye,
    },
    {
      key: 'REVIEW',
      label: 'REVIEW (61–80)',
      value: s.REVIEW || 0,
      sub: 'Elevated cross-bank risk',
      color: 'var(--review)',
      icon: AlertTriangle,
    },
    {
      key: 'CONTROLLED_ACTION',
      label: 'CONTROLLED ACTION (81–100)',
      value: s.CONTROLLED_ACTION || 0,
      sub: 'Critical multi-bank risk',
      color: 'var(--controlled-action)',
      icon: ShieldAlert,
    },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(175px, 1fr))',
      gap: 12,
      padding: '0 24px 20px',
    }}>
      {cards.map(({ key, label, value, sub, color, icon: Icon }) => (
        <div key={key} className="card" style={{ borderLeft: `3px solid ${color}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              {label}
            </span>
            <Icon size={14} color={color} />
          </div>
          <div className="mono" style={{ fontSize: '1.6rem', fontWeight: 800, color }}>
            {Number(value).toLocaleString()}
          </div>
          {key !== 'total' && total > 0 ? (
            <div style={{ marginTop: 8 }}>
              <div className="score-bar">
                <div className="score-bar-fill" style={{ width: `${(value / total) * 100}%`, background: color }} />
              </div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 4 }}>
                {((value / total) * 100).toFixed(1)}% of coordinated txns
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
              {sub}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
