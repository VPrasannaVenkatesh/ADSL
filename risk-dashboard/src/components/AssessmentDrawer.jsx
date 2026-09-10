import React from 'react';
import { formatINR, scoreColor, getRiskColor } from '../utils';
import { ShieldAlert, TrendingUp, Activity, Cpu, MapPin, Users, Clock, Network } from 'lucide-react';

const ICONS = {
  amount_risk:              ShieldAlert,
  velocity_risk:            TrendingUp,
  behaviour_deviation_risk: Activity,
  device_risk:              Cpu,
  location_risk:            MapPin,
  counterparty_risk:        Users,
  timing_risk:              Clock,
  network_pattern_risk:     Network,
};

const LABELS = {
  amount_risk:              'Amount Risk',
  velocity_risk:            'Velocity Risk',
  behaviour_deviation_risk: 'Behaviour Deviation',
  device_risk:              'Device Risk',
  location_risk:            'Location Risk',
  counterparty_risk:        'Counterparty Risk',
  timing_risk:              'Timing Risk',
  network_pattern_risk:     'Network Pattern',
};

function ComponentCard({ name, value }) {
  const Icon = ICONS[name] || Activity;
  const color = scoreColor(value);
  return (
    <div className="component-item">
      <div className="component-label" style={{ display: 'flex', alignItems: 'center', gap: 6, color }}>
        <Icon size={12} />
        {LABELS[name]}
      </div>
      <div className="component-score" style={{ color }}>{value.toFixed(1)}</div>
      <div className="score-bar" style={{ marginTop: 8 }}>
        <div className="score-bar-fill" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  );
}

export function AssessmentDrawer({ assessment, onClose }) {
  if (!assessment) return null;

  const levelColor = getRiskColor(assessment.risk_level);
  const components = assessment.components || {
    amount_risk: assessment.amount_risk,
    velocity_risk: assessment.velocity_risk,
    behaviour_deviation_risk: assessment.behaviour_deviation_risk,
    device_risk: assessment.device_risk,
    location_risk: assessment.location_risk,
    counterparty_risk: assessment.counterparty_risk,
    timing_risk: assessment.timing_risk,
    network_pattern_risk: assessment.network_pattern_risk,
  };

  return (
    <>
      <div className="overlay" onClick={onClose} />
      <div className="drawer" style={{ padding: 24 }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: 4 }}>
              Risk Assessment Detail
            </div>
            <div className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              {assessment.assessment_id}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.4rem', lineHeight: 1 }}
          >×</button>
        </div>

        {/* Score Hero */}
        <div style={{
          background: `${levelColor}14`,
          border: `1px solid ${levelColor}40`,
          borderRadius: 12,
          padding: '20px 24px',
          textAlign: 'center',
          marginBottom: 20,
        }}>
          <div style={{ fontSize: '3.5rem', fontWeight: 900, fontFamily: 'JetBrains Mono, monospace', color: levelColor, lineHeight: 1 }}>
            {assessment.final_risk_score?.toFixed(1)}
          </div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.1em', color: levelColor, marginTop: 4 }}>
            {assessment.risk_level} RISK
          </div>
          <div className="score-bar" style={{ marginTop: 12, maxWidth: 200, margin: '12px auto 0' }}>
            <div className="score-bar-fill" style={{ width: `${assessment.final_risk_score}%`, background: levelColor }} />
          </div>
        </div>

        {/* Transaction Info */}
        <div style={{ marginBottom: 20 }}>
          <SectionTitle>Transaction Details</SectionTitle>
          <InfoRow label="Transaction ID" value={assessment.transaction_id} mono />
          <InfoRow label="Account" value={assessment.account_id} mono />
          <InfoRow label="Bank / Role"
            value={
              <span>
                <BankBadge bank={assessment.bank_name || assessment.components?.bank_name} />&nbsp;
                <span style={{ color: assessment.role === 'SENDER' ? '#60A5FA' : '#A78BFA', fontSize: '0.75rem', fontWeight: 700 }}>
                  {assessment.role}
                </span>
              </span>
            }
          />
          <InfoRow label="Amount" value={formatINR(assessment.amount)} />
          <InfoRow label="Type" value={assessment.transaction_type} />
          <InfoRow label="Timestamp" value={assessment.assessment_timestamp ? new Date(assessment.assessment_timestamp).toLocaleString('en-IN') : '–'} />
        </div>

        {/* 8 Risk Components */}
        <div style={{ marginBottom: 20 }}>
          <SectionTitle>Risk Component Breakdown</SectionTitle>
          <div className="component-grid">
            {Object.entries(components).map(([k, v]) =>
              v != null ? <ComponentCard key={k} name={k} value={Number(v)} /> : null
            )}
          </div>
        </div>

        {/* Explainable Reasons */}
        <div>
          <SectionTitle>Why This Score Was Generated</SectionTitle>
          {assessment.risk_reasons?.length > 0 ? (
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {assessment.risk_reasons.map((r, i) => (
                <li key={i} style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderLeft: `3px solid ${levelColor}`,
                  borderRadius: 8,
                  padding: '10px 14px',
                  fontSize: '0.82rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5,
                }}>
                  {r}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>No anomalous patterns detected.</p>
          )}
        </div>
      </div>
    </>
  );
}

function SectionTitle({ children }) {
  return (
    <div style={{
      fontSize: '0.7rem',
      fontWeight: 700,
      letterSpacing: '0.07em',
      textTransform: 'uppercase',
      color: 'var(--text-muted)',
      marginBottom: 10,
      paddingBottom: 6,
      borderBottom: '1px solid var(--border)',
    }}>
      {children}
    </div>
  );
}

function InfoRow({ label, value, mono }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)', gap: 16 }}>
      <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem', flexShrink: 0 }}>{label}</span>
      <span style={{ color: 'var(--text-primary)', fontSize: '0.78rem', fontFamily: mono ? 'JetBrains Mono, monospace' : 'inherit', textAlign: 'right', wordBreak: 'break-all' }}>
        {value || '–'}
      </span>
    </div>
  );
}

function BankBadge({ bank }) {
  const colors = { SBI: '#3B82F6', AXIS: '#EC4899', IOB: '#F59E0B' };
  return (
    <span style={{
      background: `${colors[bank] || '#6366F1'}20`,
      color: colors[bank] || '#6366F1',
      border: `1px solid ${colors[bank] || '#6366F1'}40`,
      borderRadius: 5,
      padding: '1px 7px',
      fontSize: '0.7rem',
      fontWeight: 800,
      letterSpacing: '0.05em',
    }}>
      {bank}
    </span>
  );
}
