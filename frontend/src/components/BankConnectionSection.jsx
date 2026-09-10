import React from 'react';
import { Building2, Database, Activity, CheckCircle2 } from 'lucide-react';

export function BankConnectionSection({ bankStats, selectedBank, onSelectBank }) {
  const banksData = bankStats?.banks || {};

  const banks = [
    {
      code: 'SBI',
      name: 'State Bank of India',
      db: 'sbi_db',
      brandColor: '#3B82F6',
      badgeBg: 'rgba(59, 130, 246, 0.12)',
      badgeBorder: 'rgba(59, 130, 246, 0.35)',
    },
    {
      code: 'AXIS',
      name: 'Axis Bank Ltd',
      db: 'axis_db',
      brandColor: '#EC4899',
      badgeBg: 'rgba(236, 72, 153, 0.12)',
      badgeBorder: 'rgba(236, 72, 153, 0.35)',
    },
    {
      code: 'IOB',
      name: 'Indian Overseas Bank',
      db: 'iob_db',
      brandColor: '#F59E0B',
      badgeBg: 'rgba(245, 158, 11, 0.12)',
      badgeBorder: 'rgba(245, 158, 11, 0.35)',
    },
  ];

  return (
    <div style={{ margin: '0 24px 18px 24px' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '10px',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.75rem',
          fontWeight: '700',
          color: 'var(--text-muted)',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
        }}>
          <Building2 size={15} color="var(--accent-cyan)" />
          <span>CONNECTED BANK SYSTEMS & INDEPENDENT LEDGERS</span>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '0.72rem',
          color: '#34D399',
          fontWeight: '600',
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: '#10B981',
            boxShadow: '0 0 8px #10B981',
          }} />
          <span>ALL 3 BANK CORE SYSTEMS SYNCHRONIZED</span>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '12px',
      }}>
        {banks.map((bank) => {
          const stats = banksData[bank.code] || {};
          const txCount = stats.transactions || 0;
          const isSelected = selectedBank === bank.code;

          return (
            <div
              key={bank.code}
              onClick={() => onSelectBank && onSelectBank(bank.code)}
              className="glass-panel"
              style={{
                padding: '14px 18px',
                borderLeft: `4px solid ${bank.brandColor}`,
                cursor: 'pointer',
                background: isSelected ? 'rgba(0, 229, 255, 0.08)' : 'rgba(13, 18, 28, 0.75)',
                borderColor: isSelected ? 'var(--accent-cyan)' : 'var(--border-color)',
                transition: 'all 0.2s ease',
              }}
              title={`Click to view ${bank.code} transactions`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    background: bank.badgeBg,
                    border: `1px solid ${bank.badgeBorder}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '800',
                    fontSize: '0.78rem',
                    color: bank.brandColor,
                  }}>
                    {bank.code}
                  </div>
                  <div>
                    <div style={{ fontWeight: '700', fontSize: '0.92rem', color: '#FFFFFF' }}>
                      {bank.code}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {bank.name}
                    </div>
                  </div>
                </div>

                {/* Connection Status Pill */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '3px 10px',
                  borderRadius: '20px',
                  background: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid rgba(16, 185, 129, 0.35)',
                  fontSize: '0.72rem',
                  fontWeight: '700',
                  color: '#34D399',
                }}>
                  <span style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: '#10B981',
                    boxShadow: '0 0 6px #10B981',
                  }} />
                  <span>CONNECTED</span>
                </div>
              </div>

              <div style={{
                marginTop: '12px',
                paddingTop: '10px',
                borderTop: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.75rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)' }}>
                  <Database size={13} color="var(--accent-cyan)" />
                  <span>Database:</span>
                  <code style={{ color: 'var(--text-secondary)', fontWeight: '600' }}>{bank.db}</code>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)' }}>
                  <Activity size={13} color="#10B981" />
                  <span>Active Txns:</span>
                  <strong className="mono" style={{ color: '#FFFFFF' }}>{Number(txCount).toLocaleString()}</strong>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
