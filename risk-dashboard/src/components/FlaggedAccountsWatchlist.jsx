import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Search,
  Download,
  AlertTriangle,
  UserCheck,
  TrendingUp,
  Lock,
  Building,
  ArrowUpRight,
  Eye,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';

export function FlaggedAccountsWatchlist({ selectedBank, onSelectAccount }) {
  const [flaggedAccounts, setFlaggedAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);

  const fetchFlaggedAccounts = async () => {
    setLoading(true);
    try {
      const bankParam = selectedBank === 'ALL' ? '' : `bank=${selectedBank}&`;
      let res = await fetch(`/api/risk/flagged-accounts?${bankParam}limit=100`);
      if (!res.ok) {
        res = await fetch(`/api/accounts?${bankParam}limit=100`);
      }
      if (res.ok) {
        const data = await res.json();
        setFlaggedAccounts(data.accounts || []);
      }
    } catch (err) {
      console.error('Error loading flagged accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlaggedAccounts();
  }, [selectedBank]);

  const handleDownloadReport = async (acc) => {
    setDownloadingId(acc.account_id);
    try {
      let res = await fetch(`/api/accounts/${acc.bank}/${acc.account_id}/report`);
      if (!res.ok) {
        res = await fetch(`/api/risk/account/${acc.account_id}/report?bank=${acc.bank}`);
      }
      if (res.ok) {
        const data = await res.json();
        const text = data.report_text || JSON.stringify(data, null, 2);
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${acc.bank}_Risk_Report_${acc.account_id}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to download report:', err);
    } finally {
      setDownloadingId(null);
    }
  };

  const filtered = flaggedAccounts.filter((a) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      a.account_id?.toLowerCase().includes(q) ||
      a.customer_name?.toLowerCase().includes(q) ||
      a.account_number?.toLowerCase().includes(q)
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Search & Filter Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(15, 23, 42, 0.7)',
        padding: '14px 20px',
        borderRadius: '10px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldAlert size={18} color="#EF4444" />
          <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#F8FAFC' }}>
            Flagged & High-Risk Accounts Watchlist
          </span>
          <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: 4, background: 'rgba(239, 68, 68, 0.2)', color: '#F87171', fontWeight: 800 }}>
            {filtered.length} At-Risk Accounts
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ position: 'relative', width: '320px' }}>
            <Search size={14} color="#64748B" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search Account ID or Holder Name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 12px 7px 34px',
                borderRadius: '6px',
                background: 'rgba(5, 10, 20, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#FFFFFF',
                fontSize: '0.78rem',
                outline: 'none',
              }}
            />
          </div>
          <button
            onClick={fetchFlaggedAccounts}
            disabled={loading}
            style={{
              padding: '7px 12px',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#CBD5E1',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <RefreshCw size={12} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {/* Flagged Accounts Table */}
      <div style={{
        background: 'rgba(10, 15, 25, 0.85)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '10px',
        overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', textAlign: 'left', color: '#94A3B8' }}>
              <th style={{ padding: '14px 16px' }}>ACCOUNT ID</th>
              <th style={{ padding: '14px 16px' }}>CUSTOMER / BUSINESS</th>
              <th style={{ padding: '14px 16px' }}>BANK</th>
              <th style={{ padding: '14px 16px' }}>ACCOUNT TYPE</th>
              <th style={{ padding: '14px 16px' }}>CURRENT BALANCE</th>
              <th style={{ padding: '14px 16px' }}>DYNAMIC RISK STATUS</th>
              <th style={{ padding: '14px 16px', textAlign: 'right' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {loading && filtered.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: '#64748B' }}>
                  Loading flagged accounts from core bank ledger...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: '#64748B' }}>
                  No accounts flagged with elevated risk for {selectedBank === 'ALL' ? 'any bank' : selectedBank}.
                </td>
              </tr>
            ) : (
              filtered.map((acc) => {
                const isRestricted = acc.account_status !== 'ACTIVE';
                return (
                  <tr
                    key={acc.account_id}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '14px 16px', fontWeight: 800, color: '#93C5FD', fontFamily: 'JetBrains Mono, monospace' }}>
                      {acc.account_id}
                    </td>
                    <td style={{ padding: '14px 16px', color: '#F8FAFC' }}>
                      <div>{acc.customer_name}</div>
                      <span style={{ fontSize: '0.7rem', color: '#64748B', fontFamily: 'JetBrains Mono, monospace' }}>
                        {acc.account_number}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{
                        fontSize: '0.72rem',
                        fontWeight: 800,
                        color: acc.bank === 'SBI' ? '#3B82F6' : acc.bank === 'AXIS' ? '#EC4899' : '#F59E0B',
                      }}>
                        {acc.bank}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#CBD5E1' }}>
                      <span style={{
                        padding: '3px 7px',
                        borderRadius: 4,
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        background: acc.account_type === 'BUSINESS' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255, 255, 255, 0.06)',
                        color: acc.account_type === 'BUSINESS' ? '#C084FC' : '#CBD5E1',
                      }}>
                        {acc.account_type}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px', fontWeight: 800, color: '#FFFFFF', fontFamily: 'JetBrains Mono, monospace' }}>
                      ₹{Number(acc.current_balance || 0).toLocaleString()}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{
                            padding: '2px 6px',
                            borderRadius: 4,
                            fontSize: '0.68rem',
                            fontWeight: 900,
                            background: acc.risk_level === 'CRITICAL' ? 'rgba(239, 68, 68, 0.25)' : acc.risk_level === 'HIGH' ? 'rgba(249, 115, 22, 0.25)' : 'rgba(245, 158, 11, 0.25)',
                            color: acc.risk_level === 'CRITICAL' ? '#EF4444' : acc.risk_level === 'HIGH' ? '#F97316' : '#F59E0B',
                          }}>
                            Score: {acc.risk_score || 50}
                          </span>
                          <span style={{
                            padding: '2px 6px',
                            borderRadius: 4,
                            fontSize: '0.68rem',
                            fontWeight: 800,
                            background: isRestricted ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                            color: isRestricted ? '#EF4444' : '#F59E0B',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}>
                            <Lock size={10} />
                            {isRestricted ? 'RESTRICTED / LIEN' : 'UNDER MONITORING'}
                          </span>
                        </div>
                        {acc.risk_factors && acc.risk_factors.length > 0 && (
                          <div style={{ fontSize: '0.68rem', color: '#94A3B8', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={acc.risk_factors[0]}>
                            • {acc.risk_factors[0]}
                          </div>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <button
                          onClick={() => onSelectAccount && onSelectAccount(acc)}
                          style={{
                            padding: '5px 11px',
                            borderRadius: '5px',
                            border: '1px solid rgba(59, 130, 246, 0.4)',
                            background: 'rgba(59, 130, 246, 0.15)',
                            color: '#93C5FD',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '5px',
                          }}
                        >
                          <Eye size={12} />
                          Dossier
                        </button>
                        <button
                          onClick={() => handleDownloadReport(acc)}
                          disabled={downloadingId === acc.account_id}
                          style={{
                            padding: '5px 11px',
                            borderRadius: '5px',
                            border: '1px solid rgba(16, 185, 129, 0.4)',
                            background: 'rgba(16, 185, 129, 0.15)',
                            color: '#34D399',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '5px',
                          }}
                        >
                          <Download size={12} />
                          {downloadingId === acc.account_id ? 'Exporting...' : 'Report'}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
