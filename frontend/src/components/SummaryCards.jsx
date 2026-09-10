import React from 'react';
import {
  Activity,
  CheckCircle2,
  Eye,
  ShieldAlert,
  Lock,
  Building2,
} from 'lucide-react';

export function SummaryCards({ bankStats, simulatorStatus }) {
  const stats = simulatorStatus?.stats || {};

  // Total Transactions
  const totalTx = bankStats?.total_transactions || stats.total_generated || 0;

  // Completed Transactions
  const completedTx = bankStats?.completed ?? stats.completed_count ?? 0;

  // Monitoring Transactions
  const monitoringTx = bankStats?.monitoring ?? stats.monitoring_count ?? 0;

  // Honeypot Transactions
  const honeypotTx = bankStats?.honeypot ?? stats.honeypot_count ?? 0;

  // Lien Protected: count and total amount
  const lienCount = bankStats?.lien_protected_count ?? stats.lien_protected_count ?? 0;
  const lienAmount = bankStats?.lien_protected_amount ?? stats.lien_protected_amount ?? 0;

  const formatCurrency = (amt) => {
    if (!amt) return '₹0';
    if (amt >= 10000000) return `₹${(amt / 10000000).toFixed(2)} Cr`;
    if (amt >= 100000) return `₹${(amt / 100000).toFixed(2)} L`;
    return `₹${Number(amt).toLocaleString('en-IN')}`;
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '12px',
      margin: '0 24px 18px 24px',
    }}>
      {/* 1. TOTAL TRANSACTIONS */}
      <div className="glass-panel" style={{ padding: '14px 18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: '700', letterSpacing: '0.05em' }}>TOTAL TRANSACTIONS</span>
          <Activity size={16} color="var(--accent-cyan)" />
        </div>
        <div className="mono" style={{ fontSize: '1.45rem', fontWeight: '800', color: '#FFFFFF', marginTop: '4px' }}>
          {Number(totalTx).toLocaleString()}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)', marginTop: '2px' }}>
          Total transactions generated
        </div>
      </div>

      {/* 2. COMPLETED */}
      <div className="glass-panel" style={{ padding: '14px 18px', borderLeft: '3px solid #10B981' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#34D399' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: '700', letterSpacing: '0.05em' }}>COMPLETED</span>
          <CheckCircle2 size={16} color="#10B981" />
        </div>
        <div className="mono" style={{ fontSize: '1.45rem', fontWeight: '800', color: '#10B981', marginTop: '4px' }}>
          {Number(completedTx).toLocaleString()}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
          Approved & executed
        </div>
      </div>

      {/* 3. MONITORING */}
      <div className="glass-panel" style={{ padding: '14px 18px', borderLeft: '3px solid #F59E0B' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#FBBF24' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: '700', letterSpacing: '0.05em' }}>MONITORING</span>
          <Eye size={16} color="#F59E0B" />
        </div>
        <div className="mono" style={{ fontSize: '1.45rem', fontWeight: '800', color: '#FBBF24', marginTop: '4px' }}>
          {Number(monitoringTx).toLocaleString()}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
          Observing behaviour
        </div>
      </div>

      {/* 4. HONEYPOT */}
      <div className="glass-panel" style={{ padding: '14px 18px', borderLeft: '3px solid #06B6D4' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#22D3EE' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: '700', letterSpacing: '0.05em' }}>HONEYPOT</span>
          <ShieldAlert size={16} color="#06B6D4" />
        </div>
        <div className="mono" style={{ fontSize: '1.45rem', fontWeight: '800', color: '#22D3EE', marginTop: '4px' }}>
          {Number(honeypotTx).toLocaleString()}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
          Controlled environment
        </div>
      </div>

      {/* 5. LIEN PROTECTED */}
      <div className="glass-panel" style={{ padding: '14px 18px', borderLeft: '3px solid #F97316' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#FB923C' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: '700', letterSpacing: '0.05em' }}>LIEN PROTECTED</span>
          <Lock size={16} color="#F97316" />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
          <span className="mono" style={{ fontSize: '1.45rem', fontWeight: '800', color: '#FB923C' }}>
            {Number(lienCount).toLocaleString()}
          </span>
          <span className="mono" style={{ fontSize: '0.88rem', fontWeight: '700', color: '#FDBA74' }}>
            ({formatCurrency(lienAmount)})
          </span>
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
          Funds protected under lien
        </div>
      </div>

      {/* 6. CONNECTED BANKS */}
      <div className="glass-panel" style={{ padding: '14px 18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: '700', letterSpacing: '0.05em' }}>CONNECTED BANKS</span>
          <Building2 size={16} color="#A855F7" />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', marginTop: '6px', fontSize: '0.74rem', fontWeight: '700' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#60A5FA' }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#3B82F6' }} />
            <span>SBI</span>
            <span style={{ color: '#34D399', fontSize: '0.68rem', fontWeight: '600' }}>CONNECTED</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#F472B6' }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#EC4899' }} />
            <span>AXIS</span>
            <span style={{ color: '#34D399', fontSize: '0.68rem', fontWeight: '600' }}>CONNECTED</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#FBBF24' }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#F59E0B' }} />
            <span>IOB</span>
            <span style={{ color: '#34D399', fontSize: '0.68rem', fontWeight: '600' }}>CONNECTED</span>
          </div>
        </div>
      </div>
    </div>
  );
}
