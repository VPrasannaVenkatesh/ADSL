import React from 'react';
import { 
  Network, 
  Building, 
  ShieldCheck, 
  UserX, 
  AlertOctagon, 
  ArrowRight, 
  CornerDownRight,
  GitCommit
} from 'lucide-react';
import { formatINR } from '../utils/formatters';

export const EnvironmentPreview = ({ banks = [], activeScenario = '', config = null }) => {
  if (!banks || banks.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '32px', margin: '0 20px 24px 20px', textAlign: 'center' }}>
        <Network size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px auto' }} />
        <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '4px' }}>Topology Preview Empty</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Generate a simulation scenario to visualize the bank hierarchy and scenario flow preview.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ padding: '24px', margin: '0 20px 24px 20px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Network size={18} color="var(--accent-cyan)" />
            <span>Simulation Topology & Scenario Flow Preview</span>
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Structural environment preview prior to live transaction generation (Module 2)
          </span>
        </div>

        <div style={{
          background: 'rgba(0, 229, 255, 0.1)',
          border: '1px solid var(--accent-cyan)',
          borderRadius: '8px',
          padding: '4px 12px',
          fontSize: '0.75rem',
          fontWeight: '600',
          color: 'var(--accent-cyan)'
        }}>
          SCENARIO: {activeScenario || config?.scenario_type || 'STANDARD'}
        </div>
      </div>

      {/* Scenario Blueprint Card */}
      <div style={{
        background: 'rgba(7, 9, 14, 0.7)',
        border: '1px solid var(--border-color)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '24px'
      }}>
        <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Scenario Architecture Flow Preview
        </span>

        <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid var(--status-genuine)',
            borderRadius: '6px',
            padding: '8px 14px',
            fontSize: '0.8rem',
            fontWeight: '600',
            color: 'var(--status-genuine)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <ShieldCheck size={15} />
            <span>Origin: Genuine / Victim Pool</span>
          </div>

          <ArrowRight size={16} color="var(--text-muted)" />

          <div style={{
            background: 'rgba(245, 158, 11, 0.15)',
            border: '1px solid var(--status-mule)',
            borderRadius: '6px',
            padding: '8px 14px',
            fontSize: '0.8rem',
            fontWeight: '600',
            color: 'var(--status-mule)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <UserX size={15} />
            <span>Mule Routing Layer ({config?.scenario_parameters?.num_hops || 4} Hops)</span>
          </div>

          <ArrowRight size={16} color="var(--text-muted)" />

          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid var(--status-compromised)',
            borderRadius: '6px',
            padding: '8px 14px',
            fontSize: '0.8rem',
            fontWeight: '600',
            color: 'var(--status-compromised)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <AlertOctagon size={15} />
            <span>Destination Off-Ramp / Compromised Nodes</span>
          </div>
        </div>
      </div>

      {/* Bank & Account Hierarchy Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '16px',
      }}>
        {banks.map((bank) => (
          <div 
            key={bank.id}
            className="glass-panel"
            style={{
              padding: '16px',
              background: 'rgba(13, 17, 26, 0.85)',
              border: '1px solid var(--border-color)',
            }}
          >
            {/* Bank Card Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Building size={16} color="var(--accent-cyan)" />
                <span style={{ fontWeight: '700', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                  {bank.bank_name}
                </span>
              </div>
              <span className="mono" style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px' }}>
                {bank.bank_code}
              </span>
            </div>

            {/* Account Distribution Sub-Tree */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 8px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.08)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--status-genuine)' }}>
                  <CornerDownRight size={13} />
                  <span>Genuine Accounts:</span>
                </span>
                <strong style={{ color: 'var(--status-genuine)' }}>{bank.genuine_accounts_count}</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 8px', borderRadius: '4px', background: 'rgba(245, 158, 11, 0.08)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--status-mule)' }}>
                  <CornerDownRight size={13} />
                  <span>Mule Accounts:</span>
                </span>
                <strong style={{ color: 'var(--status-mule)' }}>{bank.mule_accounts_count}</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 8px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.08)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--status-compromised)' }}>
                  <CornerDownRight size={13} />
                  <span>Compromised:</span>
                </span>
                <strong style={{ color: 'var(--status-compromised)' }}>{bank.compromised_accounts_count}</strong>
              </div>
            </div>

            {/* Total Accounts & Liquidity */}
            <div style={{ marginTop: '12px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <span>Total: {bank.total_accounts_count} accounts</span>
              <span className="mono" style={{ color: 'var(--accent-cyan)' }}>{formatINR(bank.total_liquidity)}</span>
            </div>

          </div>
        ))}
      </div>

    </div>
  );
};
