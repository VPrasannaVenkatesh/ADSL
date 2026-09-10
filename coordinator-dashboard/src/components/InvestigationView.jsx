import React, { useState, useEffect } from 'react';
import { coordinatorApi } from '../api';
import { formatINR, formatTS, scoreColor, getRiskColor, truncate, BANKS } from '../utils';
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
} from 'lucide-react';

export function InvestigationView() {
  const [monitoredData, setMonitoredData] = useState({ monitored_transactions: [], count: 0 });
  const [liensData, setLiensData] = useState({ active_liens_count: 0, total_held_amount: 0, recent_liens: [] });
  const [selectedTx, setSelectedTx] = useState(null);
  const [provenance, setProvenance] = useState(null);
  const [propagation, setPropagation] = useState(null);
  const [subgraph, setSubgraph] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [releaseNote, setReleaseNote] = useState('');
  const [actionMessage, setActionMessage] = useState('');

  const loadData = async () => {
    try {
      const [mon, liens] = await Promise.all([
        coordinatorApi.getMonitoredEntities(40),
        coordinatorApi.getLiens(),
      ]);
      setMonitoredData(mon);
      setLiensData(liens);

      // Auto-select first if none selected
      if (!selectedTx && mon.monitored_transactions.length > 0) {
        selectTransactionForInvestigation(mon.monitored_transactions[0]);
      }
    } catch (err) {
      console.error('Error loading investigation data:', err);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 3000);
    return () => clearInterval(timer);
  }, []);

  const selectTransactionForInvestigation = async (tx) => {
    setSelectedTx(tx);
    setLoadingDetails(true);
    try {
      const accId = tx.receiver_account_id || tx.sender_account_id;
      const [prov, prop, sub] = await Promise.all([
        coordinatorApi.getProvenance(accId, 3),
        coordinatorApi.getRiskPropagation(accId, tx.amount ? 80.0 : 50.0, 60.0),
        coordinatorApi.getSubgraph(accId, 2),
      ]);
      setProvenance(prov);
      setPropagation(prop);
      setSubgraph(sub);
    } catch (err) {
      console.error('Error fetching investigation details:', err);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleReleaseLien = async (lienId) => {
    if (!releaseNote) {
      alert('Please enter an investigator audit reason to release this lien.');
      return;
    }
    try {
      await coordinatorApi.releaseLien(lienId, 'INV-AML-007', releaseNote);
      setActionMessage(`Lien ${lienId} released successfully.`);
      setReleaseNote('');
      loadData();
      setTimeout(() => setActionMessage(''), 6000);
    } catch (err) {
      alert(`Error releasing lien: ${err.message}`);
    }
  };

  const handleExportReport = () => {
    if (!selectedTx) return;
    const reportText = `
========================================================================
       ADSL BANKING SECURITY - FORMAL INVESTIGATION AUDIT REPORT
========================================================================
Generated: ${new Date().toISOString()}
Investigator: Senior AML Forensic Agent (ADSL Network Layer)

[1] TRANSACTION IDENTIFIERS
  Transaction ID    : ${selectedTx.transaction_id}
  Sender Bank       : ${selectedTx.sender_bank}
  Sender Account    : ${selectedTx.sender_account_id}
  Receiver Bank     : ${selectedTx.receiver_bank}
  Receiver Account  : ${selectedTx.receiver_account_id}
  Amount            : INR ${Number(selectedTx.amount || 0).toLocaleString('en-IN')}
  Status            : ${selectedTx.status}

[2] MULTI-HOP FUND PROVENANCE SUMMARY
  Total Inflow      : INR ${Number(provenance?.total_inflow || 0).toLocaleString('en-IN')}
  Total Outflow     : INR ${Number(provenance?.total_outflow || 0).toLocaleString('en-IN')}
  Pass-Through Ratio: ${((provenance?.pass_through_ratio || 0) * 100).toFixed(1)}%
  Active Hops Count : ${provenance?.provenance_chains?.length || 0} sequences

[3] CONTEXTUAL RISK PROPAGATION
  Direct TX Risk    : ${propagation?.direct_transaction_risk || 0.0} / 100
  Account Behav Risk: ${propagation?.account_behavioural_risk || 0.0} / 100
  Network Contextual: ${propagation?.network_contextual_risk || 0.0} / 100
  Composite Risk    : ${propagation?.composite_propagated_risk || 0.0} / 100

[4] CONTROLLED FUNDS & LIEN STATUS
  Active Liens Held : ${liensData.active_liens_count}
  Total Held Funds  : INR ${liensData.total_held_amount.toLocaleString('en-IN')}
========================================================================
`;
    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Audit_Report_${selectedTx.transaction_id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ padding: '0 24px 32px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}>
      
      {/* Top Banner KPI Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
        
        <div className="card" style={{ padding: '16px 20px', borderLeft: '4px solid #EC4899' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 800 }}>MONITORED TRANSACTIONS</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 900, color: '#F472B6', marginTop: 4 }}>
            {monitoredData.monitored_transactions.length}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Active in multi-hop network
          </div>
        </div>

        <div className="card" style={{ padding: '16px 20px', borderLeft: '4px solid #EF4444' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 800 }}>CONTROLLED LIENS / RESTRICTIONS</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 900, color: '#EF4444', marginTop: 4 }}>
            {liensData.active_liens_count}
          </div>
          <div style={{ fontSize: '0.7rem', color: '#FCA5A5', marginTop: 4 }}>
            Amount-level holds applied
          </div>
        </div>

        <div className="card" style={{ padding: '16px 20px', borderLeft: '4px solid #F59E0B' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 800 }}>FUNDS PROTECTED UNDER LIEN</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 900, color: '#FBBF24', marginTop: 4 }}>
            ₹{Number(liensData.total_held_amount || 0).toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Preserved without ledger loss
          </div>
        </div>

        <div className="card" style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <button
            onClick={handleExportReport}
            disabled={!selectedTx}
            className="btn btn-primary"
            style={{
              padding: '10px 16px',
              fontSize: '0.8rem',
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              background: 'linear-gradient(135deg, #6366F1 0%, #EC4899 100%)',
              border: 'none',
              borderRadius: 8,
              cursor: selectedTx ? 'pointer' : 'not-allowed',
            }}
          >
            <FileText size={15} />
            <span>Export Investigation Audit</span>
          </button>
          {actionMessage && (
            <span style={{ fontSize: '0.72rem', color: '#10B981', textAlign: 'center', marginTop: 6, fontWeight: 700 }}>
              {actionMessage}
            </span>
          )}
        </div>

      </div>

      {/* Main 2-Column Split: Monitored List + Dossier */}
      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20 }}>
        
        {/* Left: Flagged / Monitored Transactions Stream */}
        <div className="card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', maxHeight: '720px', overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Flagged Transactions Stream
            </h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {monitoredData.monitored_transactions.length} items
            </span>
          </div>

          {monitoredData.monitored_transactions.length === 0 ? (
            <div style={{ padding: '40px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No transactions currently flagged or monitored.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {monitoredData.monitored_transactions.map((tx) => {
                const isSelected = selectedTx?.transaction_id === tx.transaction_id;
                const isRestricted = tx.status === 'RESTRICTED';
                return (
                  <div
                    key={tx.transaction_id}
                    onClick={() => selectTransactionForInvestigation(tx)}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 8,
                      border: isSelected ? '1px solid #EC4899' : '1px solid var(--border-color)',
                      background: isSelected ? 'rgba(236, 72, 153, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="mono" style={{ fontSize: '0.72rem', fontWeight: 800, color: isRestricted ? '#EF4444' : '#FBBF24' }}>
                        {tx.status}
                      </span>
                      <span className="mono" style={{ fontSize: '0.75rem', fontWeight: 700, color: '#10B981' }}>
                        ₹{Number(tx.amount || 0).toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 3 }}>
                      {tx.transaction_id}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, fontSize: '0.75rem' }}>
                      <span className="mono" style={{ color: 'var(--text-primary)' }}>{tx.sender_account_id}</span>
                      <ArrowRight size={11} color="var(--text-muted)" />
                      <span className="mono" style={{ color: 'var(--text-primary)' }}>{tx.receiver_account_id}</span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6, fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      <span>{tx.sender_bank} ➔ {tx.receiver_bank}</span>
                      {tx.dwell_time_seconds >= 0 && (
                        <span style={{ color: tx.dwell_time_seconds <= 60 ? '#EF4444' : 'var(--text-muted)' }}>
                          Dwell: {Math.round(tx.dwell_time_seconds)}s
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Active Investigation Dossier */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          
          {selectedTx ? (
            <>
              {/* Dossier Header */}
              <div className="card" style={{ padding: '16px 20px', borderLeft: '4px solid #6366F1' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                        Forensic Dossier: {selectedTx.transaction_id}
                      </h3>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: 4,
                        fontSize: '0.7rem',
                        fontWeight: 800,
                        background: selectedTx.status === 'RESTRICTED' ? 'rgba(239, 68, 68, 0.25)' : 'rgba(245, 158, 11, 0.2)',
                        color: selectedTx.status === 'RESTRICTED' ? '#EF4444' : '#FBBF24',
                      }}>
                        {selectedTx.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                      Flow: {selectedTx.sender_bank} ({selectedTx.sender_account_id}) ➔ {selectedTx.receiver_bank} ({selectedTx.receiver_account_id})
                    </div>
                  </div>

                  <div className="mono" style={{ fontSize: '1.25rem', fontWeight: 900, color: '#10B981' }}>
                    ₹{Number(selectedTx.amount || 0).toLocaleString('en-IN')}
                  </div>
                </div>
              </div>

              {/* Subgraph Topology Map */}
              <div className="card" style={{ padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <h4 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <GitFork size={14} color="#C084FC" />
                    <span>Transaction Network Subgraph (2-Hop Ego Graph)</span>
                  </h4>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {subgraph?.node_count || 0} Nodes • {subgraph?.edge_count || 0} Directed Edges
                  </span>
                </div>

                {/* Subgraph Node/Edge List Visualizer */}
                <div style={{
                  background: 'rgba(5, 7, 9, 0.6)',
                  borderRadius: 8,
                  padding: '12px 14px',
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 10,
                  maxHeight: '160px',
                  overflowY: 'auto',
                }}>
                  {subgraph?.nodes?.map((n) => (
                    <div
                      key={n.id}
                      style={{
                        padding: '4px 8px',
                        borderRadius: 6,
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: n.id === selectedTx.receiver_account_id ? '1px solid #EC4899' : '1px solid var(--border-color)',
                        fontSize: '0.72rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                      }}
                    >
                      <span style={{ fontWeight: 700, color: n.bank === 'SBI' ? '#60A5FA' : n.bank === 'AXIS' ? '#C084FC' : '#FBBF24' }}>
                        {n.bank}
                      </span>
                      <span className="mono" style={{ color: 'var(--text-primary)' }}>{n.id}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Fund Provenance Tree (Upstream -> Downstream) */}
              <div className="card" style={{ padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h4 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Layers size={14} color="#60A5FA" />
                    <span>Fund Lineage Provenance (Source ➔ Relays ➔ Downstream)</span>
                  </h4>
                  <span style={{ fontSize: '0.72rem', color: '#F472B6', fontWeight: 700 }}>
                    Pass-Through Ratio: {((provenance?.pass_through_ratio || 0) * 100).toFixed(1)}%
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  {/* Upstream Sources */}
                  <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px 12px', borderRadius: 8 }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#60A5FA', marginBottom: 6 }}>
                      UPSTREAM INFLOW SOURCES ({provenance?.upstream_sources?.length || 0})
                    </div>
                    {provenance?.upstream_sources?.length === 0 ? (
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Origin account; no recent upstream hops</div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {provenance?.upstream_sources?.map((s, idx) => (
                          <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                            <span className="mono">{s.source_account} ({s.source_bank})</span>
                            <span className="mono" style={{ color: '#10B981', fontWeight: 700 }}>₹{s.amount?.toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Downstream Destinations */}
                  <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '10px 12px', borderRadius: 8 }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#F472B6', marginBottom: 6 }}>
                      DOWNSTREAM DISPERSION SINKS ({provenance?.downstream_destinations?.length || 0})
                    </div>
                    {provenance?.downstream_destinations?.length === 0 ? (
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Terminal sink; no downstream forwarding yet</div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {provenance?.downstream_destinations?.map((d, idx) => (
                          <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                            <span className="mono">{d.destination_account} ({d.destination_bank})</span>
                            <span className="mono" style={{ color: '#FBBF24', fontWeight: 700 }}>₹{d.amount?.toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Risk Propagation Breakdown */}
              <div className="card" style={{ padding: '16px 20px' }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AlertTriangle size={14} color="#F59E0B" />
                  <span>Controlled Risk Propagation Breakdown</span>
                </h4>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, textAlign: 'center' }}>
                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '8px', borderRadius: 6 }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>DIRECT TX RISK</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: scoreColor(propagation?.direct_transaction_risk || 0) }}>
                      {propagation?.direct_transaction_risk || 0}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '8px', borderRadius: 6 }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>ACCOUNT BEHAV RISK</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: scoreColor(propagation?.account_behavioural_risk || 0) }}>
                      {propagation?.account_behavioural_risk || 0}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '8px', borderRadius: 6 }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>NETWORK CONTEXTUAL</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: scoreColor(propagation?.network_contextual_risk || 0) }}>
                      {propagation?.network_contextual_risk || 0}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '8px', borderRadius: 6 }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>COMPOSITE RISK</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: scoreColor(propagation?.composite_propagated_risk || 0) }}>
                      {propagation?.composite_propagated_risk || 0}
                    </div>
                  </div>
                </div>

                {/* Propagation Reasons */}
                {propagation?.propagation_sources?.length > 0 && (
                  <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {propagation.propagation_sources.map((ps, idx) => (
                      <span key={idx} style={{ fontSize: '0.7rem', color: '#FCA5A5' }}>
                        • {ps.reason}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Controlled Funds / Lien Layer Actions */}
              <div className="card" style={{ padding: '16px 20px', borderLeft: '4px solid #EF4444' }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Lock size={14} color="#EF4444" />
                  <span>Controlled Funds & Lien Layer Management</span>
                </h4>

                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  <input
                    type="text"
                    placeholder="Enter senior AML investigator release reason..."
                    value={releaseNote}
                    onChange={(e) => setReleaseNote(e.target.value)}
                    style={{
                      flex: 1,
                      background: 'rgba(255, 255, 255, 0.04)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 6,
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.78rem',
                      outline: 'none',
                    }}
                  />
                  <button
                    onClick={() => handleReleaseLien(liensData.recent_liens[0]?.lien_id || 'LIEN_SAMPLE')}
                    className="btn btn-outline"
                    style={{
                      padding: '8px 16px',
                      fontSize: '0.78rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <Unlock size={13} />
                    <span>Authorize Lien Release</span>
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Select a transaction from the left panel to open its forensic investigation dossier.
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
