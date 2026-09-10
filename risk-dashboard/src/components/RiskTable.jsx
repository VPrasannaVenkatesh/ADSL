import React from 'react';
import { formatINR, formatTS, scoreColor, getRiskColor, truncate, BANKS, LEVELS } from '../utils';

const BANK_COLOR = { SBI: '#3B82F6', AXIS: '#EC4899', IOB: '#F59E0B' };

export function RiskTable({ assessments, selected, onSelect, filters, onFiltersChange }) {
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
          {BANKS.map(b => (
            <button
              key={b}
              className={`btn ${filters.bank === b ? 'btn-active' : 'btn-outline'}`}
              style={{ padding: '6px 12px', fontSize: '0.75rem', color: b !== 'ALL' && filters.bank === b ? BANK_COLOR[b] : undefined }}
              onClick={() => onFiltersChange({ ...filters, bank: b })}
            >
              {b}
            </button>
          ))}
        </div>

        {/* Risk Level filter */}
        <select
          className="filter-input"
          value={filters.risk_level || ''}
          onChange={e => onFiltersChange({ ...filters, risk_level: e.target.value })}
        >
          <option value="">All Levels</option>
          {LEVELS.filter(Boolean).map(l => <option key={l} value={l}>{l}</option>)}
        </select>

        {/* Account ID filter */}
        <input
          className="filter-input"
          placeholder="Filter by Account ID…"
          value={filters.account_id || ''}
          onChange={e => onFiltersChange({ ...filters, account_id: e.target.value })}
          style={{ width: 200 }}
        />

        {/* TXN ID filter */}
        <input
          className="filter-input"
          placeholder="Filter by Transaction ID…"
          value={filters.transaction_id || ''}
          onChange={e => onFiltersChange({ ...filters, transaction_id: e.target.value })}
          style={{ width: 230 }}
        />

        <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Showing <strong style={{ color: 'var(--text-primary)' }}>{assessments.length}</strong> assessments
        </span>
      </div>

      {/* Table */}
      <div style={{ borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto', maxHeight: 'calc(100vh - 360px)', overflowY: 'auto' }}>
          <table className="risk-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Transaction ID</th>
                <th>Account</th>
                <th>Bank</th>
                <th>Role</th>
                <th>Amount</th>
                <th>Type</th>
                <th>Risk Score</th>
                <th>Level</th>
                <th>Top Reason</th>
              </tr>
            </thead>
            <tbody>
              {assessments.length === 0 && (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Waiting for live risk assessments from the simulator…
                  </td>
                </tr>
              )}
              {assessments.map(a => {
                const color = getRiskColor(a.risk_level);
                const isSelected = selected?.assessment_id === a.assessment_id;
                return (
                  <tr
                    key={a.assessment_id}
                    className={isSelected ? 'selected' : ''}
                    onClick={() => onSelect(a)}
                  >
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                      {formatTS(a.assessment_timestamp)}
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                        {truncate(a.transaction_id, 22)}
                      </span>
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-primary)' }}>
                        {a.account_id}
                      </span>
                    </td>
                    <td>
                      <span style={{
                        background: `${BANK_COLOR[a.bank_name]}20`,
                        color: BANK_COLOR[a.bank_name] || '#6366F1',
                        border: `1px solid ${BANK_COLOR[a.bank_name]}40`,
                        borderRadius: 5,
                        padding: '2px 8px',
                        fontSize: '0.7rem',
                        fontWeight: 800,
                      }}>
                        {a.bank_name}
                      </span>
                    </td>
                    <td>
                      <span style={{
                        color: a.role === 'SENDER' ? '#60A5FA' : '#A78BFA',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                      }}>
                        {a.role}
                      </span>
                    </td>
                    <td className="mono" style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.8rem' }}>
                      {formatINR(a.amount)}
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {a.transaction_type}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 100 }}>
                        <span className="mono" style={{ fontWeight: 800, fontSize: '0.88rem', color: scoreColor(a.final_risk_score) }}>
                          {a.final_risk_score?.toFixed(1)}
                        </span>
                        <div className="score-bar" style={{ flex: 1, height: 4 }}>
                          <div className="score-bar-fill" style={{ width: `${a.final_risk_score}%`, background: scoreColor(a.final_risk_score) }} />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`badge badge-${a.risk_level}`}>{a.risk_level}</span>
                    </td>
                    <td style={{ fontSize: '0.73rem', color: 'var(--text-muted)', maxWidth: 260 }}>
                      <span style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {a.risk_reasons?.[0] || '–'}
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
