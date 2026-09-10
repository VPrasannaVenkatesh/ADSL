import React, { useState, useEffect } from 'react';
import { UserCheck, Shield, AlertTriangle, RefreshCw, Clock, Layers, Zap } from 'lucide-react';

const RISK_COLORS = {
  LOW: '#10B981',
  MEDIUM: '#F59E0B',
  HIGH: '#F97316',
  CRITICAL: '#EF4444',
};

export function StoredProfilesView({ selectedBank = 'ALL' }) {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterBank, setFilterBank] = useState(selectedBank || 'ALL');
  const [filterLevel, setFilterLevel] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      let url = 'http://localhost:8001/api/risk/profiles?limit=100';
      if (filterBank && filterBank !== 'ALL') url += `&bank=${encodeURIComponent(filterBank)}`;
      if (filterLevel) url += `&risk_level=${encodeURIComponent(filterLevel)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setProfiles(data.profiles || []);
      }
    } catch (err) {
      console.error('Error fetching stored profiles:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, [filterBank, filterLevel]);

  const filtered = profiles.filter((p) => {
    if (!searchTerm) return true;
    return p.account_id.toLowerCase().includes(searchTerm.toLowerCase());
  });

  return (
    <div style={{ padding: '20px 24px' }}>
      {/* Informational Banner on Smart Stored Risk */}
      <div style={{
        background: 'rgba(59, 130, 246, 0.08)',
        border: '1px solid rgba(59, 130, 246, 0.25)',
        borderRadius: '10px',
        padding: '14px 18px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}>
        <Shield size={22} color="#60A5FA" />
        <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
          <strong style={{ color: '#93C5FD' }}>Bank Risk Provider Architecture:</strong> Stored behavioural risk profiles are returned directly to ADSL via <code style={{ color: '#F43F5E', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>GET /risk/account/{'{account_id}'}</code> without recalculation on request. Recalculation triggers only upon meaningful behavioural changes (velocity spikes, amount anomalies, unusual devices, or fan-in/fan-out hops).
        </div>
      </div>

      {/* Filter Controls */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '14px',
        marginBottom: '16px',
        flexWrap: 'wrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <input
            type="text"
            placeholder="Search Account ID (e.g. SBI-101)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '8px 14px',
              fontSize: '0.82rem',
              color: '#fff',
              outline: 'none',
              width: '260px',
            }}
          />

          <div style={{ display: 'flex', gap: '6px' }}>
            {['ALL', 'SBI', 'AXIS', 'IOB'].map((b) => (
              <button
                key={b}
                onClick={() => setFilterBank(b)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  border: filterBank === b ? '1px solid #3B82F6' : '1px solid var(--border)',
                  background: filterBank === b ? 'rgba(59, 130, 246, 0.25)' : 'transparent',
                  color: filterBank === b ? '#60A5FA' : 'var(--text-muted)',
                }}
              >
                {b}
              </button>
            ))}
          </div>

          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '7px 12px',
              fontSize: '0.78rem',
              color: '#fff',
              outline: 'none',
            }}
          >
            <option value="">All Risk Levels</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>

        <button
          onClick={fetchProfiles}
          style={{
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '7px 14px',
            fontSize: '0.78rem',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh Stored Profiles</span>
        </button>
      </div>

      {/* Profiles Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '14px',
      }}>
        {filtered.map((prof) => {
          const color = RISK_COLORS[prof.risk_level] || '#6B7280';
          return (
            <div
              key={prof.account_id}
              style={{
                background: 'rgba(12, 17, 26, 0.75)',
                border: `1px solid rgba(255, 255, 255, 0.08)`,
                borderRadius: '10px',
                padding: '16px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* Top Bank Strip */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '3px',
                background: color,
              }} />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontWeight: '800', fontSize: '0.95rem', color: '#FFFFFF', letterSpacing: '0.02em' }}>
                    {prof.account_id}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Bank Ledger: <strong style={{ color: '#93C5FD' }}>{prof.bank_name}</strong>
                  </div>
                </div>

                <div style={{
                  background: `${color}20`,
                  border: `1px solid ${color}60`,
                  color: color,
                  fontWeight: '800',
                  fontSize: '0.72rem',
                  padding: '3px 8px',
                  borderRadius: '6px',
                }}>
                  {prof.risk_level} • {prof.risk_score}
                </div>
              </div>

              {/* Recalculation Badge & Reason */}
              <div style={{
                marginTop: '12px',
                padding: '8px 10px',
                borderRadius: '6px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.05)',
                fontSize: '0.72rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                  <span>Smart Recalculations:</span>
                  <strong style={{ color: '#E2E8F0' }}>{prof.recalculation_count}</strong>
                </div>
                <div style={{ marginTop: '4px', color: '#94A3B8', fontSize: '0.7rem' }}>
                  Trigger: <span style={{ color: '#CBD5E1' }}>{prof.last_trigger_reason || 'INITIAL_BASELINE'}</span>
                </div>
              </div>

              {/* Factors */}
              {prof.risk_factors && prof.risk_factors.length > 0 && (
                <div style={{ marginTop: '10px' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Active Risk Factors:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {prof.risk_factors.slice(0, 3).map((f, i) => (
                      <span
                        key={i}
                        style={{
                          fontSize: '0.66rem',
                          background: 'rgba(249, 115, 22, 0.12)',
                          color: '#FDBA74',
                          border: '1px solid rgba(249, 115, 22, 0.25)',
                          padding: '2px 6px',
                          borderRadius: '4px',
                        }}
                      >
                        {typeof f === 'string' ? f : JSON.stringify(f)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Timestamp */}
              <div style={{
                marginTop: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '0.68rem',
                color: 'var(--text-muted)',
              }}>
                <Clock size={12} />
                <span>Last Updated: {prof.last_updated ? new Date(prof.last_updated).toLocaleString() : 'N/A'}</span>
              </div>
            </div>
          );
        })}

        {filtered.length === 0 && !loading && (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No stored account risk profiles found matching filters.
          </div>
        )}
      </div>
    </div>
  );
}
