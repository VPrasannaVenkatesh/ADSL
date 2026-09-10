import React, { useState, useEffect } from 'react';
import {
  Building2,
  Users,
  Coins,
  ArrowRightLeft,
  Search,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import { simulatorApi } from '../api/simulatorApi';

export function BankAnalyticsView({ bankStats, onSelectAccount }) {
  const [accounts, setAccounts] = useState([]);
  const [selectedBank, setSelectedBank] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const res = await simulatorApi.getAccounts({
        bank: selectedBank,
        search: searchTerm || undefined,
        limit: 80,
      });
      setAccounts(res.accounts || []);
    } catch (err) {
      console.error('Failed to load accounts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, [selectedBank, searchTerm]);

  const banks = bankStats?.banks || {};

  const formatCurrency = (amt) => `₹${Number(amt || 0).toLocaleString('en-IN')}`;

  return (
    <div style={{ margin: '0 24px 24px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* 3 Bank Comparison Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        
        {/* SBI Card */}
        <div className="glass-panel" style={{ padding: '20px', borderTop: '3px solid #3B82F6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building2 size={20} color="#60A5FA" />
              <span style={{ fontSize: '1rem', fontWeight: '700', color: '#60A5FA' }}>STATE BANK OF INDIA</span>
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }} className="mono">sbi_db</span>
          </div>

          <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div style={{ background: 'rgba(7,9,14,0.6)', padding: '10px', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TOTAL TRANSACTIONS</div>
              <div className="mono" style={{ fontSize: '1.2rem', fontWeight: '700', color: '#FFFFFF', marginTop: '2px' }}>
                {banks.SBI?.transactions?.toLocaleString() || 0}
              </div>
            </div>
            <div style={{ background: 'rgba(7,9,14,0.6)', padding: '10px', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TOTAL VOLUME</div>
              <div className="mono" style={{ fontSize: '1.1rem', fontWeight: '700', color: '#10B981', marginTop: '2px' }}>
                {formatCurrency(banks.SBI?.volume)}
              </div>
            </div>
          </div>

          <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Active Accounts: <strong>{banks.SBI?.accounts || 500}</strong></span>
            <span>Cross-Bank Txns: <strong style={{ color: '#C084FC' }}>{banks.SBI?.cross_bank || 0}</strong></span>
          </div>
        </div>

        {/* AXIS Card */}
        <div className="glass-panel" style={{ padding: '20px', borderTop: '3px solid #EC4899' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building2 size={20} color="#F472B6" />
              <span style={{ fontSize: '1rem', fontWeight: '700', color: '#F472B6' }}>AXIS BANK</span>
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }} className="mono">axis_db</span>
          </div>

          <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div style={{ background: 'rgba(7,9,14,0.6)', padding: '10px', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TOTAL TRANSACTIONS</div>
              <div className="mono" style={{ fontSize: '1.2rem', fontWeight: '700', color: '#FFFFFF', marginTop: '2px' }}>
                {banks.AXIS?.transactions?.toLocaleString() || 0}
              </div>
            </div>
            <div style={{ background: 'rgba(7,9,14,0.6)', padding: '10px', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TOTAL VOLUME</div>
              <div className="mono" style={{ fontSize: '1.1rem', fontWeight: '700', color: '#10B981', marginTop: '2px' }}>
                {formatCurrency(banks.AXIS?.volume)}
              </div>
            </div>
          </div>

          <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Active Accounts: <strong>{banks.AXIS?.accounts || 500}</strong></span>
            <span>Cross-Bank Txns: <strong style={{ color: '#C084FC' }}>{banks.AXIS?.cross_bank || 0}</strong></span>
          </div>
        </div>

        {/* IOB Card */}
        <div className="glass-panel" style={{ padding: '20px', borderTop: '3px solid #F59E0B' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building2 size={20} color="#FBBF24" />
              <span style={{ fontSize: '1rem', fontWeight: '700', color: '#FBBF24' }}>INDIAN OVERSEAS BANK</span>
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }} className="mono">iob_db</span>
          </div>

          <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div style={{ background: 'rgba(7,9,14,0.6)', padding: '10px', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TOTAL TRANSACTIONS</div>
              <div className="mono" style={{ fontSize: '1.2rem', fontWeight: '700', color: '#FFFFFF', marginTop: '2px' }}>
                {banks.IOB?.transactions?.toLocaleString() || 0}
              </div>
            </div>
            <div style={{ background: 'rgba(7,9,14,0.6)', padding: '10px', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TOTAL VOLUME</div>
              <div className="mono" style={{ fontSize: '1.1rem', fontWeight: '700', color: '#10B981', marginTop: '2px' }}>
                {formatCurrency(banks.IOB?.volume)}
              </div>
            </div>
          </div>

          <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Active Accounts: <strong>{banks.IOB?.accounts || 500}</strong></span>
            <span>Cross-Bank Txns: <strong style={{ color: '#C084FC' }}>{banks.IOB?.cross_bank || 0}</strong></span>
          </div>
        </div>

      </div>

      {/* Account Explorer Table */}
      <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
        
        {/* Table Filter Controls */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={18} color="var(--accent-cyan)" />
            <span style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-primary)' }}>
              ACCOUNT REGISTRY EXPLORER
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {['ALL', 'SBI', 'AXIS', 'IOB'].map((b) => (
              <button
                key={b}
                onClick={() => setSelectedBank(b)}
                style={{
                  background: selectedBank === b ? 'rgba(0,229,255,0.15)' : 'rgba(255,255,255,0.04)',
                  color: selectedBank === b ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  border: selectedBank === b ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)',
                  padding: '5px 12px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                }}
              >
                {b}
              </button>
            ))}

            <div style={{ position: 'relative', width: '200px' }}>
              <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search account ID, name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-control"
                style={{ paddingLeft: '32px', fontSize: '0.785rem', height: '32px' }}
              />
            </div>
          </div>
        </div>

        {/* Table Body */}
        <div style={{ maxHeight: '450px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem' }}>
            <thead>
              <tr style={{ background: 'rgba(7,9,14,0.6)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', textAlign: 'left', fontSize: '0.725rem' }}>
                <th style={{ padding: '10px 16px' }}>ACCOUNT ID</th>
                <th style={{ padding: '10px 16px' }}>BANK</th>
                <th style={{ padding: '10px 16px' }}>HOLDER NAME</th>
                <th style={{ padding: '10px 16px' }}>TYPE</th>
                <th style={{ padding: '10px 16px', textAlign: 'right' }}>CURRENT BALANCE</th>
                <th style={{ padding: '10px 16px' }}>LOCATION</th>
                <th style={{ padding: '10px 16px', textAlign: 'center' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((acc) => (
                <tr key={acc.account_id} className="glass-panel-hover" style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '10px 16px' }}>
                    <span className="mono" style={{ fontWeight: '700', color: 'var(--accent-cyan)' }}>
                      {acc.account_id}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '0.7rem',
                      fontWeight: '700',
                      background: acc.bank === 'SBI' ? 'rgba(59,130,246,0.15)' : acc.bank === 'AXIS' ? 'rgba(236,72,153,0.15)' : 'rgba(245,158,11,0.15)',
                      color: acc.bank === 'SBI' ? '#60A5FA' : acc.bank === 'AXIS' ? '#F472B6' : '#FBBF24',
                    }}>
                      {acc.bank}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px', fontWeight: '600', color: 'var(--text-primary)' }}>
                    {acc.customer_name}
                  </td>
                  <td style={{ padding: '10px 16px', color: 'var(--text-secondary)' }}>
                    {acc.account_type}
                  </td>
                  <td style={{ padding: '10px 16px', textAlign: 'right' }} className="mono">
                    <strong style={{ color: '#10B981' }}>{formatCurrency(acc.current_balance)}</strong>
                  </td>
                  <td style={{ padding: '10px 16px', color: 'var(--text-muted)' }}>
                    {acc.home_location}
                  </td>
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                    <button
                      className="btn-secondary"
                      onClick={() => onSelectAccount(acc.bank, acc.account_id)}
                      style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                    >
                      <span>Inspect</span>
                      <ExternalLink size={12} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>

    </div>
  );
}
