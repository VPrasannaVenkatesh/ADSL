import React from 'react';
import { Building, ShieldCheck, UserX, AlertOctagon, Info, Wallet } from 'lucide-react';
import { formatINR } from '../utils/formatters';

export const BankDistributionTable = ({ banks = [] }) => {
  if (!banks || banks.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '32px', margin: '0 20px 24px 20px', textAlign: 'center' }}>
        <Building size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px auto' }} />
        <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '4px' }}>No Banks in Simulation</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Configure scenario parameters above and click <strong>GENERATE ENVIRONMENT</strong> to instantiate banks.
        </p>
      </div>
    );
  }

  // Calculate totals
  const totalGenuine = banks.reduce((acc, b) => acc + (b.genuine_accounts_count || 0), 0);
  const totalMule = banks.reduce((acc, b) => acc + (b.mule_accounts_count || 0), 0);
  const totalCompromised = banks.reduce((acc, b) => acc + (b.compromised_accounts_count || 0), 0);
  const totalAccounts = banks.reduce((acc, b) => acc + (b.total_accounts_count || 0), 0);
  const totalLiquidity = banks.reduce((acc, b) => acc + (b.total_liquidity || 0), 0);

  return (
    <div className="glass-panel" style={{ padding: '24px', margin: '0 20px 24px 20px' }}>
      
      {/* Table Header & Ground Truth Notice */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Building size={18} color="var(--accent-cyan)" />
            <span>Bank Distribution & Ground-Truth Hierarchy</span>
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Showing {banks.length} simulated financial institutions
          </span>
        </div>

        {/* Evaluation Ground Truth Notice Badge */}
        <div style={{
          background: 'rgba(168, 85, 247, 0.12)',
          border: '1px solid rgba(168, 85, 247, 0.4)',
          borderRadius: '8px',
          padding: '6px 14px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.75rem',
          color: '#E9D5FF'
        }}>
          <Info size={14} color="#C084FC" />
          <span>
            <strong>SIMULATION GROUND TRUTH</strong>: Account classifications are simulation labels for post-hoc validation only.
          </span>
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px 14px' }}>Bank Name</th>
              <th style={{ padding: '12px 14px' }}>Code</th>
              <th style={{ padding: '12px 14px' }}>Bank ID</th>
              <th style={{ padding: '12px 14px', color: 'var(--status-genuine)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={14} />
                  <span>Genuine</span>
                </div>
              </th>
              <th style={{ padding: '12px 14px', color: 'var(--status-mule)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <UserX size={14} />
                  <span>Mule</span>
                </div>
              </th>
              <th style={{ padding: '12px 14px', color: 'var(--status-compromised)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <AlertOctagon size={14} />
                  <span>Compromised</span>
                </div>
              </th>
              <th style={{ padding: '12px 14px' }}>Total Accounts</th>
              <th style={{ padding: '12px 14px', textAlign: 'right' }}>Total Liquidity</th>
            </tr>
          </thead>
          <tbody>
            {banks.map((b) => (
              <tr 
                key={b.id} 
                style={{ 
                  borderBottom: '1px solid rgba(255,255,255,0.04)',
                  transition: 'background 0.15s ease' 
                }}
                className="table-row-hover"
              >
                <td style={{ padding: '12px 14px', fontWeight: '600', color: 'var(--text-primary)' }}>
                  {b.bank_name}
                </td>
                <td style={{ padding: '12px 14px' }}>
                  <span className="mono" style={{ background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem' }}>
                    {b.bank_code}
                  </span>
                </td>
                <td style={{ padding: '12px 14px', color: 'var(--text-muted)' }} className="mono">
                  {b.bank_id}
                </td>
                <td style={{ padding: '12px 14px', color: 'var(--status-genuine)', fontWeight: '600' }}>
                  {b.genuine_accounts_count}
                </td>
                <td style={{ padding: '12px 14px', color: 'var(--status-mule)', fontWeight: '600' }}>
                  {b.mule_accounts_count}
                </td>
                <td style={{ padding: '12px 14px', color: 'var(--status-compromised)', fontWeight: '600' }}>
                  {b.compromised_accounts_count}
                </td>
                <td style={{ padding: '12px 14px', fontWeight: '600' }}>
                  {b.total_accounts_count}
                </td>
                <td style={{ padding: '12px 14px', textAlign: 'right', fontWeight: '600', color: 'var(--accent-cyan)' }} className="mono">
                  {formatINR(b.total_liquidity)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr style={{ borderTop: '2px solid var(--border-color)', background: 'rgba(0, 229, 255, 0.03)', fontWeight: '700' }}>
              <td style={{ padding: '12px 14px' }}>TOTALS ({banks.length} Banks)</td>
              <td style={{ padding: '12px 14px' }}>--</td>
              <td style={{ padding: '12px 14px' }}>--</td>
              <td style={{ padding: '12px 14px', color: 'var(--status-genuine)' }}>{totalGenuine}</td>
              <td style={{ padding: '12px 14px', color: 'var(--status-mule)' }}>{totalMule}</td>
              <td style={{ padding: '12px 14px', color: 'var(--status-compromised)' }}>{totalCompromised}</td>
              <td style={{ padding: '12px 14px' }}>{totalAccounts}</td>
              <td style={{ padding: '12px 14px', textAlign: 'right', color: 'var(--accent-cyan)' }} className="mono">
                {formatINR(totalLiquidity)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

    </div>
  );
};
