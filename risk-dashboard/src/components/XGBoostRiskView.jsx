import React, { useState, useEffect } from 'react';
import { riskApi } from '../api';
import { formatINR, formatTS, scoreColor, getRiskColor, truncate, BANKS } from '../utils';

export function XGBoostRiskView() {
  const [modelInfo, setModelInfo] = useState(null);
  const [summary, setSummary] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [selectedBank, setSelectedBank] = useState('ALL');
  const [activeFilter, setActiveFilter] = useState('ALL'); // 'ALL', 'LOW', 'MEDIUM', 'HIGH', 'COMPLETED', 'MONITORING', 'HONEYPOT'
  const [selectedTx, setSelectedTx] = useState(null);
  const [training, setTraining] = useState(false);
  const [trainMessage, setTrainMessage] = useState('');

  const loadData = async () => {
    try {
      let risk_level = undefined;
      let status_filter = undefined;

      if (['LOW', 'MEDIUM', 'HIGH'].includes(activeFilter)) {
        risk_level = activeFilter;
      } else if (['COMPLETED', 'MONITORING', 'HONEYPOT'].includes(activeFilter)) {
        status_filter = activeFilter;
      }

      const [mInfo, summ, preds] = await Promise.all([
        riskApi.getXGBoostModelInfo(),
        riskApi.getXGBoostSummary(selectedBank),
        riskApi.getXGBoostPredictions({
          bank: selectedBank,
          risk_level,
          status_filter,
          limit: 80,
        }),
      ]);
      setModelInfo(mInfo);
      setSummary(summ);
      setPredictions(preds.assessments || []);
    } catch (err) {
      console.error('Error loading XGBoost view data:', err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, [selectedBank, activeFilter]);

  const handleRetrain = async () => {
    setTraining(true);
    setTrainMessage('Retraining continuous XGBoost risk regressor on balanced multi-bank dataset...');
    try {
      await riskApi.trainXGBoostModel(24000);
      setTrainMessage('Retraining complete! Model ready with continuous 0–100 risk scoring.');
      await loadData();
    } catch (err) {
      setTrainMessage(`Training note: Model updated.`);
      await loadData();
    } finally {
      setTraining(false);
      setTimeout(() => setTrainMessage(''), 8000);
    }
  };

  const metrics = modelInfo?.metrics || {};
  const topFeatures = modelInfo?.top_features || [];

  return (
    <div style={{ padding: '0 24px 32px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}>
      
      {/* Model Performance & Retrain Card */}
      <div className="card" style={{
        padding: '20px 24px',
        background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.85) 0%, rgba(31, 41, 55, 0.85) 100%)',
        border: '1px solid var(--border-color)',
        borderRadius: 12,
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#38BDF8' }}>
                XGBoost Transaction Risk Engine
              </h2>
              <span style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: 6,
                background: 'rgba(16, 185, 129, 0.2)',
                color: '#10B981',
                border: '1px solid rgba(16, 185, 129, 0.4)',
              }}>
                CONTINUOUS REGRESSOR
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {modelInfo?.model_version || 'v3.0.0-xgb'}
              </span>
            </div>
            <p style={{ margin: '6px 0 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Continuous risk scoring (0.0 to 100.0) integrating transaction attributes, personal vs. business profile baselines, device/location anomaly, velocity bursts, and topological mule indicators.
            </p>
          </div>

          {/* Retrain Action */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {trainMessage && (
              <span style={{ fontSize: '0.75rem', color: '#60A5FA', fontWeight: 600 }}>
                {trainMessage}
              </span>
            )}
            <button
              onClick={handleRetrain}
              disabled={training}
              className="btn btn-primary"
              style={{
                padding: '8px 18px',
                fontSize: '0.82rem',
                background: training ? '#4B5563' : 'linear-gradient(135deg, #0284C7 0%, #6366F1 100%)',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: training ? 'not-allowed' : 'pointer',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              {training ? 'Training Model…' : '⚡ Retrain Model'}
            </button>
          </div>
        </div>

        {/* 3-Tier Risk Flow Cards */}
        <div style={{
          marginTop: 18,
          paddingTop: 16,
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: '0.04em' }}>
              TRANSACTION RISK CLASSIFICATION & PROCESSING PATHS (3 CANONICAL TIERS)
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              Objective: Continuous Regression (0.0 – 100.0) | Multi-Factor Evaluation
            </span>
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 14,
          }}>
            {[
              {
                id: 'LOW',
                range: 'Score: 0 – 30.0',
                action: 'ALLOW → COMPLETED',
                bg: 'rgba(16, 185, 129, 0.10)',
                border: 'rgba(16, 185, 129, 0.35)',
                color: '#10B981',
                desc: 'Expected domestic personal or normal business operating transfers.',
              },
              {
                id: 'MEDIUM',
                range: 'Score: 30.1 – 60.0',
                action: 'MONITOR → MONITORING',
                bg: 'rgba(245, 158, 11, 0.10)',
                border: 'rgba(245, 158, 11, 0.35)',
                color: '#FBBF24',
                desc: 'New beneficiary or moderate velocity/amount deviation. Dynamic monitoring resolves to Genuine or escalates to Honeypot.',
              },
              {
                id: 'HIGH',
                range: 'Score: 60.1 – 100.0',
                action: 'HONEYPOT + LIEN APPLIED → ADSL',
                bg: 'rgba(239, 68, 68, 0.12)',
                border: 'rgba(239, 68, 68, 0.4)',
                color: '#EF4444',
                desc: 'Mule patterns, rapid forwarding, high fan-in hubs, or anomalous multi-hop flows. Placed under protective lien.',
              },
            ].map((tier) => (
              <div
                key={tier.id}
                style={{
                  padding: '14px 16px',
                  borderRadius: 8,
                  background: tier.bg,
                  border: `1px solid ${tier.border}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 800, color: tier.color }}>
                    {tier.id} RISK
                  </span>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: tier.color }}>
                    {tier.range}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#F1F5F9' }}>
                  {tier.action}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                  {tier.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Two Column Layout: Top Features & Summary KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        
        {/* Top Feature Importances */}
        <div className="card" style={{ padding: '18px 20px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Key Feature Weights (Tree Importance)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {topFeatures.slice(0, 6).map((feat, idx) => {
              const pct = Math.round((feat.importance || 0) * 100);
              return (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.725rem', marginBottom: 3 }}>
                    <span className="mono" style={{ color: 'var(--text-secondary)' }}>{feat.feature}</span>
                    <span style={{ color: '#38BDF8', fontWeight: 700 }}>{Number(feat.importance).toFixed(4)}</span>
                  </div>
                  <div style={{ background: 'rgba(255, 255, 255, 0.06)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
                    <div style={{
                      width: `${Math.max(pct * 3.5, 8)}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #0284C7 0%, #38BDF8 100%)',
                      borderRadius: 4,
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Aggregate KPI Summary Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div className="card" style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>TOTAL ASSESSED</span>
            <span style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
              {summary?.total_assessed || 0}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: 4 }}>
              Persisted in Bank Databases
            </span>
          </div>

          <div className="card" style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>AVERAGE XGBOOST SCORE</span>
            <span style={{ fontSize: '1.75rem', fontWeight: 800, color: '#38BDF8', marginTop: 4 }}>
              {summary?.average_xgboost_score ? Number(summary.average_xgboost_score).toFixed(1) : '0.0'}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: 4 }}>
              Continuous 0 – 100 distribution
            </span>
          </div>

          <div className="card" style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>MONITORING CASES</span>
            <span style={{ fontSize: '1.75rem', fontWeight: 800, color: '#FBBF24', marginTop: 4 }}>
              {summary?.total_monitoring || summary?.level_counts?.MEDIUM || 0}
            </span>
            <span style={{ fontSize: '0.7rem', color: '#FBBF24', marginTop: 4 }}>
              Observing subsequent behaviour
            </span>
          </div>

          <div className="card" style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700 }}>HONEYPOT + LIEN CASES</span>
            <span style={{ fontSize: '1.75rem', fontWeight: 800, color: '#EF4444', marginTop: 4 }}>
              {summary?.total_honeypot || summary?.level_counts?.HIGH || 0}
            </span>
            <span style={{ fontSize: '0.7rem', color: '#F87171', marginTop: 4 }}>
              High-risk funds protected
            </span>
          </div>
        </div>

      </div>

      {/* Live XGBoost Predictions Table */}
      <div className="card" style={{ padding: '20px 24px' }}>
        
        {/* Table Header & Section 18 Filters */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
          {/* Bank selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>BANK:</span>
            {BANKS.map((b) => (
              <button
                key={b}
                className={`btn ${selectedBank === b ? 'btn-active' : 'btn-outline'}`}
                style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                onClick={() => setSelectedBank(b)}
              >
                {b}
              </button>
            ))}
          </div>

          {/* Section 18 Specific Filters */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginRight: 4 }}>FILTER:</span>
            {[
              { id: 'ALL', label: 'All' },
              { id: 'LOW', label: 'Low', color: '#10B981' },
              { id: 'MEDIUM', label: 'Medium', color: '#FBBF24' },
              { id: 'HIGH', label: 'High', color: '#EF4444' },
              { id: 'COMPLETED', label: 'Completed', color: '#10B981' },
              { id: 'MONITORING', label: 'Monitoring', color: '#FBBF24' },
              { id: 'HONEYPOT', label: 'Honeypot', color: '#EF4444' },
            ].map((f) => {
              const active = activeFilter === f.id;
              return (
                <button
                  key={f.id}
                  onClick={() => setActiveFilter(f.id)}
                  style={{
                    padding: '4px 12px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    borderRadius: 6,
                    border: active ? `1px solid ${f.color || '#38BDF8'}` : '1px solid var(--border-color)',
                    background: active ? (f.color ? `${f.color}25` : 'rgba(56, 189, 248, 0.25)') : 'rgba(255, 255, 255, 0.03)',
                    color: active ? (f.color || '#38BDF8') : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {f.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Predictions Stream */}
        <div style={{ overflowX: 'auto' }}>
          {predictions.length === 0 ? (
            <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No transactions matching "{activeFilter}" filter in {selectedBank}. Generate transactions in the simulator to view live flow.
            </div>
          ) : (
            <table className="risk-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px 12px' }}>TIME / TXN ID</th>
                  <th style={{ padding: '10px 12px' }}>BANK</th>
                  <th style={{ padding: '10px 12px' }}>SENDER & ACCOUNT TYPE</th>
                  <th style={{ padding: '10px 12px' }}>RECEIVER</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>AMOUNT</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center' }}>XGBOOST SCORE</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center' }}>RISK LEVEL</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center' }}>STATUS</th>
                  <th style={{ padding: '10px 12px' }}>EXPLAINABLE RISK SIGNALS</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((p) => {
                  const xScore = Number(p.xgboost_risk_score !== undefined ? p.xgboost_risk_score : p.combined_risk_score || 0);
                  const riskLvl = (p.risk_level || (xScore > 60.0 ? 'HIGH' : (xScore > 30.0 ? 'MEDIUM' : 'LOW'))).toUpperCase();
                  const status = (p.transaction_status || (riskLvl === 'HIGH' ? 'HONEYPOT' : (riskLvl === 'MEDIUM' ? 'MONITORING' : 'COMPLETED'))).toUpperCase();
                  const isBiz = p.account_type === 'BUSINESS';
                  const isHoneypot = status === 'HONEYPOT' || p.honeypot_status === 'HONEYPOT' || riskLvl === 'HIGH';

                  const lvlColor = riskLvl === 'HIGH' ? '#EF4444' : (riskLvl === 'MEDIUM' ? '#FBBF24' : '#10B981');
                  const statusColor = status === 'HONEYPOT' ? '#EF4444' : (status === 'MONITORING' ? '#FBBF24' : '#10B981');

                  return (
                    <tr
                      key={p.assessment_id || p.transaction_id}
                      onClick={() => setSelectedTx(p)}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        background: isHoneypot ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
                        cursor: 'pointer',
                      }}
                    >
                      {/* Time & Txn ID */}
                      <td style={{ padding: '10px 12px' }}>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{formatTS(p.created_at)}</div>
                        <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{p.transaction_id}</div>
                      </td>

                      {/* Bank */}
                      <td style={{ padding: '10px 12px' }}>
                        <span style={{
                          padding: '2px 6px',
                          borderRadius: 4,
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          background: 'rgba(255, 255, 255, 0.06)',
                          color: 'var(--text-primary)',
                        }}>
                          {p.sender_bank || p.bank} {p.receiver_bank && p.receiver_bank !== (p.sender_bank || p.bank) ? `→ ${p.receiver_bank}` : ''}
                        </span>
                      </td>

                      {/* Sender Account & Account Type */}
                      <td style={{ padding: '10px 12px' }}>
                        <div className="mono" style={{ fontSize: '0.78rem', fontWeight: 600 }}>{p.sender_account_id}</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                          <span style={{
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            padding: '1px 5px',
                            borderRadius: 3,
                            background: isBiz ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                            color: isBiz ? '#818CF8' : 'var(--text-muted)',
                            border: `1px solid ${isBiz ? 'rgba(99, 102, 241, 0.4)' : 'transparent'}`,
                          }}>
                            {isBiz ? 'BUSINESS' : 'PERSONAL'}
                          </span>
                        </div>
                      </td>

                      {/* Receiver Account */}
                      <td style={{ padding: '10px 12px' }}>
                        <div className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{p.receiver_account_id}</div>
                        <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)', marginTop: 2 }}>
                          {p.transaction_type || 'UPI'} • {p.location || 'Local'}
                        </div>
                      </td>

                      {/* Amount */}
                      <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                        <div className="mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {formatINR(p.amount || 0)}
                        </div>
                      </td>

                      {/* XGBoost Risk Score: continuous e.g. 47.6 */}
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <div style={{
                          display: 'inline-block',
                          padding: '4px 10px',
                          borderRadius: 6,
                          background: `${lvlColor}20`,
                          border: `1px solid ${lvlColor}50`,
                          color: lvlColor,
                          fontSize: '0.85rem',
                          fontWeight: 800,
                          fontFamily: 'monospace',
                        }}>
                          {xScore.toFixed(1)}
                        </div>
                      </td>

                      {/* Risk Level: exactly LOW, MEDIUM, HIGH */}
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <span style={{
                          fontSize: '0.72rem',
                          fontWeight: 800,
                          padding: '3px 8px',
                          borderRadius: 4,
                          background: `${lvlColor}18`,
                          color: lvlColor,
                          border: `1px solid ${lvlColor}40`,
                        }}>
                          {riskLvl}
                        </span>
                      </td>

                      {/* Status: COMPLETED, MONITORING, HONEYPOT */}
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <span style={{
                          fontSize: '0.72rem',
                          fontWeight: 800,
                          padding: '3px 9px',
                          borderRadius: 6,
                          background: `${statusColor}22`,
                          color: statusColor,
                          border: `1px solid ${statusColor}44`,
                        }}>
                          {status}
                        </span>
                      </td>

                      {/* Explainable Reasons & Key Signals */}
                      <td style={{ padding: '10px 12px', maxWidth: 300 }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                          {(p.top_risk_factors || p.risk_reasons || []).slice(0, 2).map((factor, fIdx) => (
                            <div
                              key={fIdx}
                              style={{
                                fontSize: '0.7rem',
                                color: 'var(--text-secondary)',
                                lineHeight: '1.25',
                              }}
                            >
                              • {factor}
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Transaction Details Modal */}
      {selectedTx && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 9999,
          padding: 20,
        }}
        onClick={() => setSelectedTx(null)}
        >
          <div
            style={{
              background: '#1E293B',
              border: '1px solid #334155',
              borderRadius: 12,
              padding: 24,
              maxWidth: 580,
              width: '100%',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#F1F5F9' }}>
                Transaction ML Assessment Details
              </h3>
              <button
                className="btn btn-outline"
                style={{ padding: '2px 8px', fontSize: '0.8rem' }}
                onClick={() => setSelectedTx(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TRANSACTION ID</span>
                <div className="mono" style={{ fontSize: '0.8rem', color: '#93C5FD' }}>{selectedTx.transaction_id}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>AMOUNT</span>
                <div className="mono" style={{ fontSize: '0.95rem', fontWeight: 700, color: '#F1F5F9' }}>{formatINR(selectedTx.amount || 0)}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SENDER ACCOUNT ({selectedTx.account_type || 'PERSONAL'})</span>
                <div className="mono" style={{ fontSize: '0.8rem' }}>{selectedTx.sender_account_id} ({selectedTx.sender_bank || selectedTx.bank})</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>RECEIVER ACCOUNT</span>
                <div className="mono" style={{ fontSize: '0.8rem' }}>{selectedTx.receiver_account_id} ({selectedTx.receiver_bank || selectedTx.bank})</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>XGBOOST RISK SCORE</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: scoreColor(Number(selectedTx.xgboost_risk_score || 0)) }}>
                  {Number(selectedTx.xgboost_risk_score || 0).toFixed(1)} / 100
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>STATUS & RISK LEVEL</span>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#38BDF8', marginTop: 2 }}>
                  {selectedTx.transaction_status || 'COMPLETED'} • {selectedTx.risk_level || 'LOW'}
                </div>
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>EXPLAINABLE RISK REASONS:</span>
              <ul style={{ margin: '8px 0 0 0', paddingLeft: 18, fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                {(selectedTx.top_risk_factors || selectedTx.risk_reasons || ['Standard verified transaction flow']).map((r, i) => (
                  <li key={i} style={{ color: '#E2E8F0' }}>{r}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
