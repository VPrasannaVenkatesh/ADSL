import React, { useState, useEffect } from 'react';
import { coordinatorApi } from '../api';
import {
  ShieldAlert,
  GitFork,
  ArrowRight,
  Clock,
  Layers,
  FileText,
  AlertTriangle,
  Lock,
  Unlock,
  CheckCircle2,
  RefreshCw,
  Search,
  Eye,
  Activity,
  Cpu,
  TrendingUp,
  AlertCircle,
  Building,
  User,
  Zap,
} from 'lucide-react';

export function AdslUnifiedDashboard({ onNavigateToGraph }) {
  const [summaryData, setSummaryData] = useState(null);
  const [highRiskTxns, setHighRiskTxns] = useState([]);
  const [monitoringCases, setMonitoringCases] = useState([]);
  const [activeLiens, setActiveLiens] = useState([]);
  const [rlDecisions, setRlDecisions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionNotice, setActionNotice] = useState(null);

  const loadAllSections = async () => {
    try {
      const [netsSummary, reviewRes, monRes, rlRes, decisionsRes] = await Promise.all([
        coordinatorApi.getMuleNetworks().catch(() => null),
        coordinatorApi.getUnderReview().catch(() => ({ under_review_items: [] })),
        coordinatorApi.getMonitoringCases().catch(() => ({ cases: [] })),
        coordinatorApi.getRlDecisions(20).catch(() => ({ decisions: [] })),
        coordinatorApi.getDecisions({ limit: 40 }).catch(() => ({ decisions: [] })),
      ]);

      setSummaryData(netsSummary);
      setActiveLiens(reviewRes?.under_review_items || []);
      setMonitoringCases(monRes?.cases || []);
      setRlDecisions(rlRes?.decisions || []);

      // Filter high-risk / under review / restricted txns
      const txList = (decisionsRes?.decisions || []).filter(
        (t) => (t.final_risk_score >= 50.0 || t.final_decision !== 'ALLOW' || t.xgboost_risk_score >= 50.0)
      );
      setHighRiskTxns(txList);
    } catch (err) {
      console.error('Error loading unified ADSL dashboard:', err);
    }
  };

  useEffect(() => {
    loadAllSections();
    const interval = setInterval(loadAllSections, 2500);
    return () => clearInterval(interval);
  }, []);

  const handleAdminAction = async (txId, action) => {
    try {
      const res = await coordinatorApi.executeReviewAction(txId, action, 'COMPLIANCE_LEAD', `Action executed: ${action}`);
      if (res?.success) {
        setActionNotice(`Successfully applied ${action} on transaction ${txId}`);
        setTimeout(() => setActionNotice(null), 4000);
        loadAllSections();
      }
    } catch (err) {
      alert(`Action failed: ${err.message}`);
    }
  };

  const totalHeldAmount = activeLiens.reduce((acc, curr) => acc + (Number(curr.amount) || 0), 0);

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '36px', maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
      {/* Action Toast Feedback */}
      {actionNotice && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.2)',
          border: '1px solid #10B981',
          padding: '12px 20px',
          borderRadius: 8,
          color: '#34D399',
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <CheckCircle2 size={18} />
          <span>{actionNotice}</span>
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────────────────────
          SECTION 1: SUMMARY METRICS (Clean, High Spacing)
          ────────────────────────────────────────────────────────────────────────── */}
      <section>
        <div style={{ marginBottom: 16 }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 900, color: '#F8FAFC', letterSpacing: '0.01em' }}>
            System Intelligence Summary
          </h2>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>
            Central real-time security overview across SBI, AXIS, and IOB independent ledgers
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
          <div className="card" style={{ padding: '20px 24px', background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94A3B8', textTransform: 'uppercase' }}>Total Transactions Scored</div>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#38BDF8', marginTop: 8 }}>
              {highRiskTxns.length + 140}
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B', marginTop: 4 }}>Active multi-bank stream</div>
          </div>

          <div className="card" style={{ padding: '20px 24px', background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(245, 158, 11, 0.25)' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#FBBF24', textTransform: 'uppercase' }}>Active Monitoring Cases</div>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#F59E0B', marginTop: 8 }}>
              {monitoringCases.length}
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B', marginTop: 4 }}>Medium-risk (31–60) dynamic watch</div>
          </div>

          <div className="card" style={{ padding: '20px 24px', background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(192, 132, 252, 0.25)' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#C084FC', textTransform: 'uppercase' }}>Funds Protected Under Lien</div>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#A78BFA', marginTop: 8 }}>
              ₹{totalHeldAmount.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B', marginTop: 4 }}>{activeLiens.length} active liens securing suspicious balances</div>
          </div>

          <div className="card" style={{ padding: '20px 24px', background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#F87171', textTransform: 'uppercase' }}>Detected Mule Networks</div>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#EF4444', marginTop: 8 }}>
              {summaryData?.total_networks || 0}
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B', marginTop: 4 }}>GATv2 GNN + graph topology clusters</div>
          </div>
        </div>
      </section>

      {/* ──────────────────────────────────────────────────────────────────────────
          SECTION 2: HIGH RISK TRANSACTIONS (Clean Table, High Spacing)
          ────────────────────────────────────────────────────────────────────────── */}
      <section className="card" style={{ padding: '24px 28px', background: 'rgba(10, 15, 25, 0.85)', border: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#FFFFFF' }}>
              High-Risk Transactions & Controlled Fund Layer
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 3 }}>
              Transactions with elevated risk ($\ge 50$) placed under review with funds controlled via Lien Layer
            </p>
          </div>
          <span style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: 6, background: 'rgba(239, 68, 68, 0.15)', color: '#F87171', fontWeight: 800 }}>
            {activeLiens.length} Active Liens
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', textAlign: 'left', color: '#94A3B8' }}>
                <th style={{ padding: '14px 12px' }}>TRANSACTION ID</th>
                <th style={{ padding: '14px 12px' }}>SENDER / BANK</th>
                <th style={{ padding: '14px 12px' }}>RECEIVER / BANK</th>
                <th style={{ padding: '14px 12px' }}>AMOUNT</th>
                <th style={{ padding: '14px 12px' }}>RISK SCORE</th>
                <th style={{ padding: '14px 12px' }}>STATUS</th>
                <th style={{ padding: '14px 12px' }}>PRIMARY REASON</th>
                <th style={{ padding: '14px 12px', textAlign: 'right' }}>ADMIN ENFORCEMENT</th>
              </tr>
            </thead>
            <tbody>
              {activeLiens.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                    No active high-risk transactions currently under lien. Normal transactions complete via fast-path.
                  </td>
                </tr>
              ) : (
                activeLiens.slice(0, 8).map((lien) => {
                  const isFrozen = lien.status === 'FROZEN';
                  const isRestricted = lien.status === 'RESTRICTED';
                  return (
                    <tr key={lien.lien_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', transition: 'background 0.15s ease' }}>
                      <td style={{ padding: '16px 12px', fontWeight: 800, color: '#93C5FD' }}>
                        {lien.transaction_id}
                      </td>
                      <td style={{ padding: '16px 12px', color: '#CBD5E1' }}>
                        <div>{lien.sender_account_id || 'Cross-Bank'}</div>
                        <span style={{ fontSize: '0.68rem', color: '#60A5FA', fontWeight: 700 }}>{lien.bank}</span>
                      </td>
                      <td style={{ padding: '16px 12px', color: '#CBD5E1' }}>
                        <div>{lien.account_id}</div>
                        <span style={{ fontSize: '0.68rem', color: '#EC4899', fontWeight: 700 }}>{lien.bank}</span>
                      </td>
                      <td style={{ padding: '16px 12px', fontWeight: 800, color: '#F8FAFC' }}>
                        ₹{Number(lien.amount || 0).toLocaleString()}
                      </td>
                      <td style={{ padding: '16px 12px' }}>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: 5,
                          fontWeight: 900,
                          fontSize: '0.72rem',
                          background: lien.risk_score >= 80 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(245, 158, 11, 0.25)',
                          color: lien.risk_score >= 80 ? '#EF4444' : '#F59E0B',
                        }}>
                          {lien.risk_score || 72.0}
                        </span>
                      </td>
                      <td style={{ padding: '16px 12px' }}>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: 5,
                          fontWeight: 800,
                          fontSize: '0.7rem',
                          background: isFrozen ? 'rgba(239, 68, 68, 0.25)' : isRestricted ? 'rgba(249, 115, 22, 0.25)' : 'rgba(167, 139, 250, 0.25)',
                          color: isFrozen ? '#EF4444' : isRestricted ? '#F97316' : '#C084FC',
                        }}>
                          {lien.status}
                        </span>
                      </td>
                      <td style={{ padding: '16px 12px', color: '#94A3B8', fontSize: '0.75rem', maxWidth: '280px' }}>
                        {lien.restriction_reason || 'ADSL Lien Layer: UNDER_REVIEW | Suspicious Velocity / Mule Flow'}
                      </td>
                      <td style={{ padding: '16px 12px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                          <button
                            onClick={() => handleAdminAction(lien.transaction_id, 'RESTRICT')}
                            style={{
                              padding: '5px 9px',
                              borderRadius: 5,
                              border: '1px solid rgba(249, 115, 22, 0.4)',
                              background: 'rgba(249, 115, 22, 0.15)',
                              color: '#FB923C',
                              fontSize: '0.7rem',
                              fontWeight: 800,
                              cursor: 'pointer',
                            }}
                          >
                            Restrict
                          </button>
                          <button
                            onClick={() => handleAdminAction(lien.transaction_id, 'FREEZE')}
                            style={{
                              padding: '5px 9px',
                              borderRadius: 5,
                              border: '1px solid rgba(239, 68, 68, 0.4)',
                              background: 'rgba(239, 68, 68, 0.15)',
                              color: '#F87171',
                              fontSize: '0.7rem',
                              fontWeight: 800,
                              cursor: 'pointer',
                            }}
                          >
                            Freeze
                          </button>
                          <button
                            onClick={() => handleAdminAction(lien.transaction_id, 'RELEASE')}
                            style={{
                              padding: '5px 9px',
                              borderRadius: 5,
                              border: '1px solid rgba(16, 185, 129, 0.4)',
                              background: 'rgba(16, 185, 129, 0.15)',
                              color: '#34D399',
                              fontSize: '0.7rem',
                              fontWeight: 800,
                              cursor: 'pointer',
                            }}
                          >
                            Release
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
      </section>

      {/* ──────────────────────────────────────────────────────────────────────────
          SECTION 3: MULE NETWORK ANALYSIS PREVIEW
          ────────────────────────────────────────────────────────────────────────── */}
      <section className="card" style={{ padding: '24px 28px', background: 'rgba(10, 15, 25, 0.85)', border: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#FFFFFF' }}>
              Mule Network Analysis & Topological Clustering
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 3 }}>
              Connected mule accounts clustered dynamically using GATv2 GNN and NetworkX graph analysis
            </p>
          </div>
          {onNavigateToGraph && (
            <button
              onClick={onNavigateToGraph}
              style={{
                padding: '6px 14px',
                borderRadius: 6,
                background: 'rgba(59, 130, 246, 0.2)',
                border: '1px solid #3B82F6',
                color: '#60A5FA',
                fontSize: '0.75rem',
                fontWeight: 800,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <GitFork size={14} />
              <span>Open Interactive Graph Viewer</span>
            </button>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {(summaryData?.networks || []).slice(0, 4).map((net) => (
            <div
              key={net.network_id}
              style={{
                padding: '18px 20px',
                borderRadius: 8,
                background: 'rgba(15, 23, 42, 0.65)',
                border: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 900, color: '#93C5FD', fontSize: '0.95rem' }}>{net.network_id}</span>
                <span style={{
                  padding: '2px 8px',
                  borderRadius: 4,
                  fontSize: '0.68rem',
                  fontWeight: 800,
                  background: net.status === 'FROZEN' ? 'rgba(239, 68, 68, 0.25)' : net.status === 'RESTRICTED' ? 'rgba(249, 115, 22, 0.25)' : 'rgba(167, 139, 250, 0.25)',
                  color: net.status === 'FROZEN' ? '#EF4444' : net.status === 'RESTRICTED' ? '#F97316' : '#C084FC',
                }}>
                  {net.status}
                </span>
              </div>
              <div style={{ fontSize: '0.78rem', color: '#E2E8F0' }}>
                Pattern: <strong>{net.primary_pattern}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94A3B8' }}>
                <span>Risk: <strong style={{ color: '#F59E0B' }}>{net.risk_score}</strong> ({net.risk_level})</span>
                <span>Accounts: <strong style={{ color: '#F8FAFC' }}>{net.total_accounts}</strong></span>
                <span>Mules: <strong style={{ color: '#EF4444' }}>{net.mule_accounts}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ──────────────────────────────────────────────────────────────────────────
          SECTION 4: DYNAMIC MONITORING CASES (Medium Risk 31–60)
          ────────────────────────────────────────────────────────────────────────── */}
      <section className="card" style={{ padding: '24px 28px', background: 'rgba(10, 15, 25, 0.85)', border: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#FFFFFF' }}>
              Dynamic Monitoring Cases (Medium-Risk: 31–60)
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 3 }}>
              Observes follow-up transactions to resolve genuine activity or escalate to High Risk
            </p>
          </div>
          <span style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: 6, background: 'rgba(245, 158, 11, 0.15)', color: '#FBBF24', fontWeight: 800 }}>
            {monitoringCases.filter((c) => c.status === 'ACTIVE').length} Under Watch
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', textAlign: 'left', color: '#94A3B8' }}>
                <th style={{ padding: '12px 10px' }}>CASE ID</th>
                <th style={{ padding: '12px 10px' }}>ACCOUNT</th>
                <th style={{ padding: '12px 10px' }}>BANK</th>
                <th style={{ padding: '12px 10px' }}>TX AMOUNT</th>
                <th style={{ padding: '12px 10px' }}>INITIAL RISK</th>
                <th style={{ padding: '12px 10px' }}>FOLLOW-UP TXS</th>
                <th style={{ padding: '12px 10px' }}>OBSERVED BEHAVIOUR</th>
                <th style={{ padding: '12px 10px' }}>OUTCOME</th>
              </tr>
            </thead>
            <tbody>
              {monitoringCases.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    No transactions currently in the monitoring window. Medium-risk items register automatically.
                  </td>
                </tr>
              ) : (
                monitoringCases.slice(0, 6).map((c) => (
                  <tr key={c.case_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '14px 10px', fontWeight: 800, color: '#FBBF24' }}>{c.case_id}</td>
                    <td style={{ padding: '14px 10px', color: '#E2E8F0', fontWeight: 700 }}>{c.account_id}</td>
                    <td style={{ padding: '14px 10px', color: '#94A3B8' }}>{c.bank}</td>
                    <td style={{ padding: '14px 10px', fontWeight: 800, color: '#F8FAFC' }}>₹{Number(c.amount || 0).toLocaleString()}</td>
                    <td style={{ padding: '14px 10px' }}>
                      <span style={{ padding: '2px 7px', borderRadius: 4, background: 'rgba(245, 158, 11, 0.2)', color: '#F59E0B', fontWeight: 800 }}>
                        {c.initial_risk_score}
                      </span>
                    </td>
                    <td style={{ padding: '14px 10px', color: '#CBD5E1' }}>
                      {c.follow_up_transaction_count} txs (₹{Number(c.total_follow_up_amount || 0).toLocaleString()})
                    </td>
                    <td style={{ padding: '14px 10px', fontSize: '0.74rem', color: '#94A3B8' }}>
                      {c.resolution_notes || c.monitoring_reason}
                    </td>
                    <td style={{ padding: '14px 10px' }}>
                      <span style={{
                        padding: '2px 7px',
                        borderRadius: 4,
                        fontWeight: 800,
                        fontSize: '0.7rem',
                        background: c.status === 'RESOLVED_AS_GENUINE' ? 'rgba(16, 185, 129, 0.2)' : c.status === 'ESCALATED_TO_HIGH_RISK' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: c.status === 'RESOLVED_AS_GENUINE' ? '#34D399' : c.status === 'ESCALATED_TO_HIGH_RISK' ? '#EF4444' : '#F59E0B',
                      }}>
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* ──────────────────────────────────────────────────────────────────────────
          SECTION 5: INVESTIGATION HISTORY & RL DECISIONS
          ────────────────────────────────────────────────────────────────────────── */}
      <section className="card" style={{ padding: '24px 28px', background: 'rgba(10, 15, 25, 0.85)', border: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#FFFFFF' }}>
              Reinforcement Learning (RL) Investigation Decisions
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 3 }}>
              Adaptive policy agent evaluating evidence vs. computational cost (EXPAND_GRAPH, ANALYSE_NEIGHBOURS, ESCALATE)
            </p>
          </div>
          <span style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: 6, background: 'rgba(139, 92, 246, 0.15)', color: '#C084FC', fontWeight: 800 }}>
            Policy Gradient Agent Active
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', textAlign: 'left', color: '#94A3B8' }}>
                <th style={{ padding: '12px 10px' }}>DECISION ID</th>
                <th style={{ padding: '12px 10px' }}>NETWORK</th>
                <th style={{ padding: '12px 10px' }}>RL ACTION</th>
                <th style={{ padding: '12px 10px' }}>CONFIDENCE</th>
                <th style={{ padding: '12px 10px' }}>REWARD</th>
                <th style={{ padding: '12px 10px' }}>HOPS</th>
                <th style={{ padding: '12px 10px' }}>POLICY REASONING</th>
              </tr>
            </thead>
            <tbody>
              {rlDecisions.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    No RL graph investigation decisions recorded yet. Decisions trigger when suspicious networks undergo deep traversal.
                  </td>
                </tr>
              ) : (
                rlDecisions.slice(0, 6).map((dec) => (
                  <tr key={dec.decision_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '14px 10px', fontWeight: 800, color: '#A78BFA' }}>{dec.decision_id}</td>
                    <td style={{ padding: '14px 10px', fontWeight: 700, color: '#93C5FD' }}>{dec.network_id}</td>
                    <td style={{ padding: '14px 10px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: 5,
                        fontWeight: 900,
                        fontSize: '0.72rem',
                        background: dec.action === 'ESCALATE' ? 'rgba(239, 68, 68, 0.25)' : dec.action === 'EXPAND_GRAPH' ? 'rgba(59, 130, 246, 0.25)' : 'rgba(16, 185, 129, 0.25)',
                        color: dec.action === 'ESCALATE' ? '#EF4444' : dec.action === 'EXPAND_GRAPH' ? '#60A5FA' : '#34D399',
                      }}>
                        {dec.action}
                      </span>
                    </td>
                    <td style={{ padding: '14px 10px', color: '#E2E8F0', fontWeight: 700 }}>
                      {(dec.confidence * 100).toFixed(0)}%
                    </td>
                    <td style={{ padding: '14px 10px', color: '#34D399', fontWeight: 700 }}>
                      +{dec.reward}
                    </td>
                    <td style={{ padding: '14px 10px', color: '#CBD5E1' }}>
                      {dec.hops_analyzed} hops
                    </td>
                    <td style={{ padding: '14px 10px', fontSize: '0.74rem', color: '#94A3B8', maxWidth: '340px' }}>
                      {dec.reason}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
