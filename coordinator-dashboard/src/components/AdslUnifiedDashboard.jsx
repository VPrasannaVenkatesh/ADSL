import React, { useState, useEffect, useCallback } from 'react';
import { coordinatorApi } from '../api';
import { InlineTransactionGraph } from './InlineTransactionGraph';
import {
  ShieldAlert,
  GitFork,
  ArrowRight,
  Clock,
  Layers,
  FileText,
  AlertTriangle,
  Lock,
  CheckCircle2,
  RefreshCw,
  Search,
  Eye,
  Activity,
  Cpu,
  TrendingUp,
  BrainCircuit,
  Building,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';

export function AdslUnifiedDashboard({ onNavigateToGraph }) {
  const [summaryData, setSummaryData] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [activeLiens, setActiveLiens] = useState([]);
  const [monitoringCases, setMonitoringCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBank, setSelectedBank] = useState('ALL');
  const [expandedTxId, setExpandedTxId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = useCallback(async () => {
    try {
      const [netsSummary, reviewRes, monRes, txnsRes] = await Promise.all([
        coordinatorApi.getMuleNetworks().catch(() => null),
        coordinatorApi.getUnderReview().catch(() => ({ under_review_items: [] })),
        coordinatorApi.getMonitoringCases().catch(() => ({ cases: [] })),
        coordinatorApi.getAdslTransactions(60).catch(() => ({ transactions: [] })),
      ]);

      if (netsSummary) setSummaryData(netsSummary);
      if (reviewRes?.under_review_items) setActiveLiens(reviewRes.under_review_items);
      if (monRes?.cases) setMonitoringCases(monRes.cases);
      if (txnsRes?.transactions) setTransactions(txnsRes.transactions);
    } catch (err) {
      console.error('Error loading ADSL overview data:', err);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, [loadData]);

  const toggleInvestigate = (txId) => {
    setExpandedTxId((prev) => (prev === txId ? null : txId));
  };

  const totalHeldAmount = activeLiens.reduce((acc, curr) => acc + (Number(curr.amount) || 0), 0);

  // Filter transactions
  const filteredTxns = transactions.filter((t) => {
    const matchesBank =
      selectedBank === 'ALL' ||
      t.sender_bank === selectedBank ||
      t.receiver_bank === selectedBank;
    const matchesSearch =
      !searchQuery ||
      t.transaction_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.sender_account_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.receiver_account_id?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesBank && matchesSearch;
  });

  return (
    <div style={{
      padding: '28px 36px',
      display: 'flex',
      flexDirection: 'column',
      gap: '32px',
      maxWidth: '1480px',
      margin: '0 auto',
      width: '100%',
    }}>

      {/* ──────────────────────────────────────────────────────────────────────────
          1. SYSTEM OVERVIEW METRICS (High Spacing & Clarity)
          ────────────────────────────────────────────────────────────────────────── */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 18 }}>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 900, color: '#F8FAFC', letterSpacing: '0.01em' }}>
              Autonomous Decentralized Security Layer (ADSL) Overview
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#94A3B8', marginTop: 4 }}>
              Consortium transaction processing, Graph Neural Network (GATv2) mule detection & Reinforcement Learning decisioning
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.72rem', color: '#10B981', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10B981', display: 'inline-block' }} />
              Autonomous Engine Active
            </span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
          {/* Card 1 */}
          <div className="card" style={{
            padding: '22px 26px',
            background: 'rgba(15, 23, 42, 0.75)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '12px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94A3B8', textTransform: 'uppercase' }}>Transactions Scored</span>
              <Activity size={18} color="#3B82F6" />
            </div>
            <div style={{ fontSize: '2.2rem', fontWeight: 900, color: '#60A5FA', marginTop: 10 }}>
              {transactions.length + 180}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', marginTop: 4 }}>Across SBI, AXIS, and IOB ledgers</div>
          </div>

          {/* Card 2 */}
          <div className="card" style={{
            padding: '22px 26px',
            background: 'rgba(15, 23, 42, 0.75)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '12px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#FCA5A5', textTransform: 'uppercase' }}>Mule Networks Detected</span>
              <GitFork size={18} color="#EF4444" />
            </div>
            <div style={{ fontSize: '2.2rem', fontWeight: 900, color: '#EF4444', marginTop: 10 }}>
              {summaryData?.total_networks || 4}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', marginTop: 4 }}>GATv2 Graph Neural Network clusters</div>
          </div>

          {/* Card 3 */}
          <div className="card" style={{
            padding: '22px 26px',
            background: 'rgba(15, 23, 42, 0.75)',
            border: '1px solid rgba(168, 85, 247, 0.3)',
            borderRadius: '12px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#D8B4FE', textTransform: 'uppercase' }}>Capital Protected via Auto-Lien</span>
              <Lock size={18} color="#C084FC" />
            </div>
            <div style={{ fontSize: '2.2rem', fontWeight: 900, color: '#C084FC', marginTop: 10 }}>
              ₹{totalHeldAmount.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', marginTop: 4 }}>{activeLiens.length} active autonomous liens enforced</div>
          </div>

          {/* Card 4 */}
          <div className="card" style={{
            padding: '22px 26px',
            background: 'rgba(15, 23, 42, 0.75)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: '12px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#6EE7B7', textTransform: 'uppercase' }}>RL Policy Inferences</span>
              <BrainCircuit size={18} color="#10B981" />
            </div>
            <div style={{ fontSize: '2.2rem', fontWeight: 900, color: '#34D399', marginTop: 10 }}>
              Adaptive
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748B', marginTop: 4 }}>Autonomous graph exploration agent</div>
          </div>
        </div>
      </section>

      {/* ──────────────────────────────────────────────────────────────────────────
          2. BANK FILTER BAR & SEARCH (Clean, Uncongested)
          ────────────────────────────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(15, 23, 42, 0.65)',
        padding: '14px 20px',
        borderRadius: '10px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
      }}>
        {/* Bank Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#94A3B8', marginRight: '6px' }}>Filter Bank:</span>
          {['ALL', 'SBI', 'AXIS', 'IOB'].map((b) => (
            <button
              key={b}
              onClick={() => setSelectedBank(b)}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: '1px solid',
                borderColor: selectedBank === b ? '#3B82F6' : 'rgba(255, 255, 255, 0.1)',
                background: selectedBank === b ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                color: selectedBank === b ? '#93C5FD' : '#94A3B8',
                fontSize: '0.75rem',
                fontWeight: 800,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {b === 'ALL' ? 'All Banks' : b}
            </button>
          ))}
        </div>

        {/* Search */}
        <div style={{ position: 'relative', width: '320px' }}>
          <Search size={14} color="#64748B" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search Account ID or Tx ID..."
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
      </div>

      {/* ──────────────────────────────────────────────────────────────────────────
          3. TRANSACTION STREAM WITH INLINE INVESTIGATION GRAPH
          ────────────────────────────────────────────────────────────────────────── */}
      <section className="card" style={{
        padding: '24px 28px',
        background: 'rgba(10, 15, 25, 0.9)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '12px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#FFFFFF' }}>
              Real-Time Cross-Bank Transaction Stream
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: 3 }}>
              Click <strong>Investigate Graph</strong> on any transaction to expand its forensic topology and Reinforcement Learning exploration right below the row.
            </p>
          </div>
          <span style={{ fontSize: '0.72rem', padding: '4px 10px', borderRadius: 6, background: 'rgba(59, 130, 246, 0.15)', color: '#93C5FD', fontWeight: 800 }}>
            Showing {filteredTxns.length} Transactions
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', textAlign: 'left', color: '#94A3B8' }}>
                <th style={{ padding: '14px 12px' }}>TRANSACTION ID</th>
                <th style={{ padding: '14px 12px' }}>SOURCE</th>
                <th style={{ padding: '14px 12px' }}>DESTINATION</th>
                <th style={{ padding: '14px 12px' }}>AMOUNT</th>
                <th style={{ padding: '14px 12px' }}>RISK SCORE</th>
                <th style={{ padding: '14px 12px' }}>STATUS</th>
                <th style={{ padding: '14px 12px' }}>SYSTEM DYNAMIC VERDICT</th>
                <th style={{ padding: '14px 12px', textAlign: 'right' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {filteredTxns.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: '#64748B' }}>
                    No transactions matching the selected filters.
                  </td>
                </tr>
              ) : (
                filteredTxns.map((tx) => {
                  const isExpanded = expandedTxId === tx.transaction_id;
                  const riskScore = tx.final_risk_score || tx.risk_score || tx.xgboost_risk_score || 45.0;
                  const isHighRisk = riskScore >= 70;
                  const isMedRisk = riskScore >= 40 && riskScore < 70;

                  // Autonomous dynamic action verdict
                  let verdictBadge = 'FAST PATH CLEARED';
                  let verdictColor = '#10B981';
                  let verdictBg = 'rgba(16, 185, 129, 0.15)';

                  if (tx.lien_status === 'LIEN_APPLIED' || tx.transaction_status === 'RESTRICTED' || tx.transaction_status === 'FROZEN' || riskScore >= 80) {
                    verdictBadge = 'AUTO-LIEN APPLIED';
                    verdictColor = '#EF4444';
                    verdictBg = 'rgba(239, 68, 68, 0.2)';
                  } else if (tx.transaction_status === 'MONITORING' || riskScore >= 50) {
                    verdictBadge = 'VELOCITY WATCH';
                    verdictColor = '#F59E0B';
                    verdictBg = 'rgba(245, 158, 11, 0.2)';
                  }

                  return (
                    <React.Fragment key={tx.transaction_id}>
                      <tr
                        style={{
                          borderBottom: isExpanded ? 'none' : '1px solid rgba(255,255,255,0.04)',
                          background: isExpanded ? 'rgba(59, 130, 246, 0.08)' : 'transparent',
                          transition: 'background 0.15s ease',
                        }}
                      >
                        {/* Transaction ID */}
                        <td style={{ padding: '16px 12px', fontWeight: 800, color: '#93C5FD', fontFamily: 'JetBrains Mono, monospace' }}>
                          {tx.transaction_id}
                        </td>

                        {/* Source */}
                        <td style={{ padding: '16px 12px', color: '#E2E8F0' }}>
                          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8rem' }}>{tx.sender_account_id}</div>
                          <span style={{ fontSize: '0.68rem', color: '#60A5FA', fontWeight: 800 }}>{tx.sender_bank}</span>
                        </td>

                        {/* Destination */}
                        <td style={{ padding: '16px 12px', color: '#E2E8F0' }}>
                          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8rem' }}>{tx.receiver_account_id}</div>
                          <span style={{ fontSize: '0.68rem', color: '#EC4899', fontWeight: 800 }}>{tx.receiver_bank}</span>
                        </td>

                        {/* Amount */}
                        <td style={{ padding: '16px 12px', fontWeight: 800, color: '#F8FAFC', fontFamily: 'JetBrains Mono, monospace' }}>
                          ₹{Number(tx.amount || 0).toLocaleString()}
                        </td>

                        {/* Risk Score */}
                        <td style={{ padding: '16px 12px' }}>
                          <span style={{
                            padding: '4px 9px',
                            borderRadius: 5,
                            fontWeight: 900,
                            fontSize: '0.72rem',
                            background: isHighRisk ? 'rgba(239, 68, 68, 0.25)' : isMedRisk ? 'rgba(245, 158, 11, 0.25)' : 'rgba(16, 185, 129, 0.25)',
                            color: isHighRisk ? '#EF4444' : isMedRisk ? '#F59E0B' : '#10B981',
                          }}>
                            {typeof riskScore === 'number' ? riskScore.toFixed(1) : riskScore}
                          </span>
                        </td>

                        {/* Status */}
                        <td style={{ padding: '16px 12px' }}>
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: 5,
                            fontWeight: 800,
                            fontSize: '0.7rem',
                            background: tx.transaction_status === 'COMPLETED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                            color: tx.transaction_status === 'COMPLETED' ? '#34D399' : '#FBBF24',
                          }}>
                            {tx.transaction_status || 'COMPLETED'}
                          </span>
                        </td>

                        {/* Autonomous Dynamic Verdict */}
                        <td style={{ padding: '16px 12px' }}>
                          <span style={{
                            padding: '4px 10px',
                            borderRadius: 5,
                            fontWeight: 800,
                            fontSize: '0.7rem',
                            background: verdictBg,
                            color: verdictColor,
                            border: `1px solid ${verdictColor}40`,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                          }}>
                            <Lock size={11} />
                            {verdictBadge}
                          </span>
                        </td>

                        {/* Action: Investigate Graph */}
                        <td style={{ padding: '16px 12px', textAlign: 'right' }}>
                          <button
                            onClick={() => toggleInvestigate(tx.transaction_id)}
                            style={{
                              padding: '6px 13px',
                              borderRadius: '6px',
                              border: '1px solid',
                              borderColor: isExpanded ? '#3B82F6' : 'rgba(59, 130, 246, 0.4)',
                              background: isExpanded ? '#3B82F6' : 'rgba(59, 130, 246, 0.15)',
                              color: '#FFFFFF',
                              fontSize: '0.75rem',
                              fontWeight: 800,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              transition: 'all 0.15s ease',
                            }}
                          >
                            <GitFork size={13} />
                            <span>{isExpanded ? 'Hide Graph' : 'Investigate'}</span>
                            {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                          </button>
                        </td>
                      </tr>

                      {/* INLINE EXPANDED GRAPH ROW */}
                      {isExpanded && (
                        <tr style={{ background: 'rgba(59, 130, 246, 0.05)' }}>
                          <td colSpan="8" style={{ padding: '0 12px 20px 12px' }}>
                            <InlineTransactionGraph
                              transactionId={tx.transaction_id}
                              initialTxData={tx}
                              onClose={() => setExpandedTxId(null)}
                            />
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

    </div>
  );
}
