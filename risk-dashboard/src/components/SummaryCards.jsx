import React from 'react';
import { ShieldAlert, TrendingUp, AlertTriangle, Zap } from 'lucide-react';

const ICONS = { LOW: TrendingUp, MEDIUM: AlertTriangle, HIGH: Zap, CRITICAL: ShieldAlert };
const COLORS = { LOW: 'var(--low)', MEDIUM: 'var(--medium)', HIGH: 'var(--high)', CRITICAL: 'var(--critical)' };

export function SummaryCards({ summary }) {
  const s = summary?.summary || {};
  const total = s.total || 0;

  const cards = [
    { key: 'total', label: 'Total Assessments', value: total, color: '#6366F1', icon: ShieldAlert },
    { key: 'LOW', label: 'Low Risk', value: s.LOW || 0, color: 'var(--low)', icon: TrendingUp },
    { key: 'MEDIUM', label: 'Medium Risk', value: s.MEDIUM || 0, color: 'var(--medium)', icon: AlertTriangle },
    { key: 'HIGH', label: 'High Risk', value: s.HIGH || 0, color: 'var(--high)', icon: Zap },
    { key: 'CRITICAL', label: 'Critical Risk', value: s.CRITICAL || 0, color: 'var(--critical)', icon: ShieldAlert },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
      gap: 12,
      padding: '0 24px 20px',
    }}>
      {cards.map(({ key, label, value, color, icon: Icon }) => (
        <div key={key} className="card" style={{ borderLeft: `3px solid ${color}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              {label}
            </span>
            <Icon size={14} color={color} />
          </div>
          <div className="mono" style={{ fontSize: '1.6rem', fontWeight: 800, color }}>
            {Number(value).toLocaleString()}
          </div>
          {key !== 'total' && total > 0 && (
            <div style={{ marginTop: 8 }}>
              <div className="score-bar">
                <div className="score-bar-fill" style={{ width: `${(value / total) * 100}%`, background: color }} />
              </div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 4 }}>
                {((value / total) * 100).toFixed(1)}% of total
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
