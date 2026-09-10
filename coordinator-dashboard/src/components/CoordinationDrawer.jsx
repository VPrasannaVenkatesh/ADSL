import React from 'react';
import { formatTS, scoreColor, getDecisionColor, getRiskColor, BANK_THEME } from '../utils';
import { ShieldCheck, Eye, AlertTriangle, ShieldAlert, Lock, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';

const DECISION_ICONS = {
  ALLOW: ShieldCheck,
  MONITOR: Eye,
  REVIEW: AlertTriangle,
  CONTROLLED_ACTION: ShieldAlert,
};

export function CoordinationDrawer({ decision, onClose }) {
  if (!decision) return null;

  const decColor = getDecisionColor(decision.final_decision);
  const DecIcon = DECISION_ICONS[decision.final_decision] || ShieldCheck;
  const sTheme = BANK_THEME[decision.sender_bank] || { color: '#3B82F6' };
  const rTheme = BANK_THEME[decision.receiver_bank] || { color: '#EC4899' };

  return (
    <>
      <div className="overlay" onClick={onClose} />
      <div className="drawer" style={{ padding: 24 }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18 }}>
          <div>
            <div style={{ fontSize: '0.68rem', color: '#8B5CF6', fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 3 }}>
              Decentralized Risk Coordination Audit
            </div>
            <div className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              {decision.coordination_id}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.4rem', lineHeight: 1 }}
          >×</button>
        </div>

        {/* Privacy Preservation Guarantee Box */}
        <div style={{
          background: 'rgba(139, 92, 246, 0.08)',
          border: '1px solid rgba(139, 92, 246, 0.25)',
          borderRadius: 8,
          padding: '10px 14px',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          marginBottom: 18,
        }}>
          <Lock size={16} color="#A78BFA" />
          <div style={{ fontSize: '0.73rem', color: '#DDD6FE', lineHeight: 1.4 }}>
            <strong>Privacy Preserved:</strong> The coordinator accessed only risk scores and explainable factors. Customer names, balances, and ledger histories were retained locally inside private bank databases.
          </div>
        </div>

        {/* Decision Hero */}
        <div style={{
          background: `${decColor}14`,
          border: `1px solid ${decColor}40`,
          borderRadius: 12,
          padding: '20px 24px',
          textAlign: 'center',
          marginBottom: 20,
        }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: decColor, marginBottom: 8 }}>
            <DecIcon size={20} />
            <span style={{ fontSize: '0.85rem', fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              FINAL DECISION: {decision.final_decision.replace('_', ' ')}
            </span>
          </div>

          <div style={{ fontSize: '3.2rem', fontWeight: 900, fontFamily: 'JetBrains Mono, monospace', color: decColor, lineHeight: 1 }}>
            {decision.final_risk_score.toFixed(1)}
          </div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em', color: 'var(--text-secondary)', marginTop: 4 }}>
            COORDINATED RISK LEVEL: <span style={{ color: decColor, fontWeight: 800 }}>{decision.final_risk_level}</span>
          </div>

          <div className="score-bar" style={{ marginTop: 12, maxWidth: 220, margin: '12px auto 0' }}>
            <div className="score-bar-fill" style={{ width: `${decision.final_risk_score}%`, background: decColor }} />
          </div>
        </div>

        {/* Transaction Metadata */}
        <div style={{ marginBottom: 20 }}>
          <SectionTitle>Transaction Context</SectionTitle>
          <InfoRow label="Transaction ID" value={decision.transaction_id} mono />
          <InfoRow
            label="Participating Banks"
            value={
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: sTheme.color, fontWeight: 800 }}>{decision.sender_bank}</span>
                <ArrowRight size={12} color="var(--text-muted)" />
                <span style={{ color: rTheme.color, fontWeight: 800 }}>{decision.receiver_bank}</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  ({decision.sender_bank === decision.receiver_bank ? 'Intra-Bank' : 'Cross-Bank'})
                </span>
              </div>
            }
          />
          <InfoRow label="Coordination Time" value={formatTS(decision.coordination_timestamp)} />
        </div>

        {/* Side-by-Side Bank Risk Responses */}
        <div style={{ marginBottom: 22 }}>
          <SectionTitle>Participating Bank Risk Reports</SectionTitle>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            
            {/* Sender Bank */}
            <div style={{
              background: 'var(--bg-surface)',
              border: `1px solid ${sTheme.color}35`,
              borderRadius: 10,
              padding: '14px 14px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, color: sTheme.color }}>
                  {decision.sender_bank} (Sender)
                </span>
                <span className={`badge-level level-${decision.sender_risk_level}`}>
                  {decision.sender_risk_level}
                </span>
              </div>
              <div className="mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: scoreColor(decision.sender_risk_score) }}>
                {decision.sender_risk_score.toFixed(1)}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
                Account: <span className="mono" style={{ color: 'var(--text-secondary)' }}>{decision.sender_masked_account}</span>
              </div>

              {decision.sender_indicators?.length > 0 && (
                <div style={{ marginTop: 10, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                  <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
                    Reported Indicators:
                  </div>
                  {decision.sender_indicators.map((ind, i) => (
                    <div key={i} style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: 3 }}>
                      • {ind}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Receiver Bank */}
            <div style={{
              background: 'var(--bg-surface)',
              border: `1px solid ${rTheme.color}35`,
              borderRadius: 10,
              padding: '14px 14px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, color: rTheme.color }}>
                  {decision.receiver_bank} (Receiver)
                </span>
                <span className={`badge-level level-${decision.receiver_risk_level}`}>
                  {decision.receiver_risk_level}
                </span>
              </div>
              <div className="mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: scoreColor(decision.receiver_risk_score) }}>
                {decision.receiver_risk_score.toFixed(1)}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
                Account: <span className="mono" style={{ color: 'var(--text-secondary)' }}>{decision.receiver_masked_account}</span>
              </div>

              {decision.receiver_indicators?.length > 0 && (
                <div style={{ marginTop: 10, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                  <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
                    Reported Indicators:
                  </div>
                  {decision.receiver_indicators.map((ind, i) => (
                    <div key={i} style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: 3 }}>
                      • {ind}
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        </div>

        {/* Synthesis & Decision Reasons */}
        <div style={{ marginBottom: 20 }}>
          <SectionTitle>Synthesis & Decision Reasons</SectionTitle>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {decision.decision_reasons.map((r, i) => (
              <li key={i} style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderLeft: `3px solid ${decColor}`,
                borderRadius: 8,
                padding: '10px 14px',
                fontSize: '0.8rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
              }}>
                {r}
              </li>
            ))}
          </ul>
        </div>

        {/* Third Bank Excluded Notice */}
        <div style={{
          fontSize: '0.7rem',
          color: 'var(--text-muted)',
          textAlign: 'center',
          padding: '10px',
          borderTop: '1px solid var(--border)',
        }}>
          🛡️ Non-participating bank databases were completely excluded from this coordination request.
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
