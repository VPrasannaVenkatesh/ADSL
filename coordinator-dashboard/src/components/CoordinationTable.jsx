import React from 'react';
import { formatTS, scoreColor, getRiskColor, truncate, BANKS, DECISIONS, LEVELS, BANK_THEME } from '../utils';
import { ArrowRight, ShieldCheck, Eye, AlertTriangle, ShieldAlert } from 'lucide-react';

const DECISION_ICONS = {
  ALLOW: ShieldCheck,
  MONITOR: Eye,
  REVIEW: AlertTriangle,
  CONTROLLED_ACTION: ShieldAlert,
};

export function CoordinationTable({ decisions, selected, onSelect, filters, onFiltersChange }) {
  return (
    <div style={{ padding: '0 24px' }}>
      {/* Filter Bar */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 10,
        marginBottom: 14,
        alignItems: 'center',
      }}>
        {/* Bank filter */}
        <div style={{ display: 'flex', gap: 6 }}>
          {BANKS.map(b => {
            const theme = BANK_THEME[b];
            return (
              <button
                key={b}
                className={`btn ${filters.bank === b ? 'btn-active' : 'btn-outline'}`}
                style={{ padding: '6px 12px', fontSize: '0.75rem', color: theme && filters.bank === b ? theme.color : undefined }}
                onClick={() => onFiltersChange({ ...filters, bank: b })}
              >
                {b}
              </button>
            );
          })}
        </div>

        {/* Decision Filter */}
        <select
          className="filter-input"
          value={filters.decision || ''}
          onChange={e => onFiltersChange({ ...filters, decision: e.target.value })}
        >
          <option value="">All Decisions</option>
          {DECISIONS.filter(Boolean).map(d => (
            <option key={d} value={d}>{d.replace('_', ' ')}</option>
          ))}
        </select>

        {/* Risk Level Filter */}
        <select
          className="filter-input"
          value={filters.risk_level || ''}
          onChange={e => onFiltersChange({ ...filters, risk_level: e.target.value })}
        >
          <option value="">All Risk Levels</option>
          {LEVELS.filter(Boolean).map(l => <option key={l} value={l}>{l}</option>)}
        </select>

        {/* Transaction ID Filter */}
        <input
          className="filter-input"
          placeholder="Search Transaction ID…"
          value={filters.transaction_id || ''}
          onChange={e => onFiltersChange({ ...filters, transaction_id: e.target.value })}
          style={{ width: 220 }}
        />

        {/* Coordination ID Filter */}
        <input
          className="filter-input"
          placeholder="Search Coordination ID…"
          value={filters.coordination_id || ''}
          onChange={e => onFiltersChange({ ...filters, coordination_id: e.target.value })}
          style={{ width: 220 }}
        />

        <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Showing <strong style={{ color: 'var(--text-primary)' }}>{decisions.length}</strong> coordinated decisions
        </span>
      </div>

      {/* Table Container */}
      <div style={{ borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto', maxHeight: 'calc(100vh - 360px)', overflowY: 'auto' }}>
          <table className="coord-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Coordination ID</th>
                <th>Transaction ID</th>
                <th>Participating Banks</th>
                <th>Sender Risk</th>
                <th>Receiver Risk</th>
                <th>Coordinated Score</th>
                <th>Risk Level</th>
                <th>Final Decision</th>
                <th>Top Decision Factor</th>
              </tr>
            </thead>
            <tbody>
              {decisions.length === 0 && (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Waiting for live coordinated decisions from participating banks…
                  </td>
                </tr>
              )}
              {decisions.map(d => {
                const sTheme = BANK_THEME[d.sender_bank] || {};
                const rTheme = BANK_THEME[d.receiver_bank] || {};
                const isSelected = selected?.coordination_id === d.coordination_id;
                const DecIcon = DECISION_ICONS[d.final_decision] || ShieldCheck;

                return (
                  <tr
                    key={d.coordination_id}
                    className={isSelected ? 'selected' : ''}
                    onClick={() => onSelect(d)}
                  >
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                      {formatTS(d.coordination_timestamp)}
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: '0.72rem', color: '#8B5CF6' }}>
                        {truncate(d.coordination_id, 16)}
                      </span>
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                        {truncate(d.transaction_id, 20)}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span style={{
                          background: sTheme.bg || '#3B82F620',
                          color: sTheme.color || '#3B82F6',
                          border: `1px solid ${sTheme.border || '#3B82F640'}`,
                          borderRadius: 4,
                          padding: '1px 6px',
                          fontSize: '0.68rem',
                          fontWeight: 800,
                        }}>
                          {d.sender_bank}
                        </span>
                        <ArrowRight size={11} color="var(--text-muted)" />
                        <span style={{
                          background: rTheme.bg || '#EC489920',
                          color: rTheme.color || '#EC4899',
                          border: `1px solid ${rTheme.border || '#EC489940'}`,
                          borderRadius: 4,
                          padding: '1px 6px',
                          fontSize: '0.68rem',
                          fontWeight: 800,
                        }}>
                          {d.receiver_bank}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span className="mono" style={{ fontSize: '0.78rem', fontWeight: 700, color: scoreColor(d.sender_risk_score) }}>
                          {d.sender_risk_score.toFixed(1)}
                        </span>
                        <span className={`badge-level level-${d.sender_risk_level}`} style={{ fontSize: '0.62rem' }}>
                          {d.sender_risk_level}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span className="mono" style={{ fontSize: '0.78rem', fontWeight: 700, color: scoreColor(d.receiver_risk_score) }}>
                          {d.receiver_risk_score.toFixed(1)}
                        </span>
                        <span className={`badge-level level-${d.receiver_risk_level}`} style={{ fontSize: '0.62rem' }}>
                          {d.receiver_risk_level}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 95 }}>
                        <span className="mono" style={{ fontWeight: 800, fontSize: '0.9rem', color: scoreColor(d.final_risk_score) }}>
                          {d.final_risk_score.toFixed(1)}
                        </span>
                        <div className="score-bar" style={{ flex: 1, height: 4 }}>
                          <div className="score-bar-fill" style={{ width: `${d.final_risk_score}%`, background: scoreColor(d.final_risk_score) }} />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`badge-level level-${d.final_risk_level}`}>{d.final_risk_level}</span>
                    </td>
                    <td>
                      <span className={`badge-decision badge-${d.final_decision}`}>
                        <DecIcon size={12} />
                        {d.final_decision.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.73rem', color: 'var(--text-muted)', maxWidth: 260 }}>
                      <span style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {d.decision_reasons?.[0] || '–'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
