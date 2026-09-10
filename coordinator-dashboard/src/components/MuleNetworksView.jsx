import React, { useState, useEffect, useRef } from 'react';
import {
  Network,
  Shield,
  AlertTriangle,
  Users,
  Eye,
  ArrowRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  CheckCircle2,
  Lock,
  ChevronRight,
  X,
  Sliders,
  DollarSign,
  Activity,
  Layers,
} from 'lucide-react';
import { coordinatorApi } from '../api';

const ROLE_COLORS = {
  SOURCE: '#3B82F6',
  MULE_HUB: '#EF4444',
  MULE_RELAY: '#F97316',
  DISPERSER: '#EC4899',
  SINK: '#10B981',
  SUSPICIOUS: '#F59E0B',
  NORMAL: '#6B7280',
};

const CLASSIFICATION_COLORS = {
  MULE: '#EF4444',
  SUSPICIOUS: '#F59E0B',
  NORMAL: '#10B981',
};

export function MuleNetworksView() {
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedNetwork, setSelectedNetwork] = useState(null);
  const [networkDetail, setNetworkDetail] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  // Dynamic Live Streaming Controls
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [liveAlert, setLiveAlert] = useState(null);
  const prevNetworkCountRef = useRef(0);

  // Filters for graph
  const [bankFilter, setBankFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');

  // Zoom & Pan for interactive canvas
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });

  // Action status toast
  const [actionFeedback, setActionFeedback] = useState(null);

  const fetchSummary = async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const data = await coordinatorApi.getMuleNetworks();
      if (data) {
        if (prevNetworkCountRef.current > 0 && data.total_networks > prevNetworkCountRef.current) {
          const newClusters = data.total_networks - prevNetworkCountRef.current;
          setLiveAlert(`🚨 Live Alert: GATv2 model identified ${newClusters} new Mule Network cluster!`);
          setTimeout(() => setLiveAlert(null), 5000);
        }
        prevNetworkCountRef.current = data.total_networks;
        setSummaryData(data);
      }
    } catch (err) {
      console.error('Error fetching mule networks summary:', err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const loadNetworkDetail = async (networkId, isSilent = false) => {
    try {
      const data = await coordinatorApi.getMuleNetworkDetail(networkId);
      setNetworkDetail(data);
      if (!isSilent) {
        setSelectedNetwork(networkId);
        setSelectedNode(null);
        setZoomLevel(1);
        setPanOffset({ x: 0, y: 0 });
      }
    } catch (err) {
      console.error('Error loading network detail:', err);
    }
  };

  // Real-time dynamic background loop (every 2.2 seconds)
  useEffect(() => {
    fetchSummary(true);
    const timer = setInterval(() => {
      if (autoRefresh) {
        fetchSummary(false);
        if (selectedNetwork) {
          loadNetworkDetail(selectedNetwork, true);
        }
      }
    }, 2200);
    return () => clearInterval(timer);
  }, [autoRefresh, selectedNetwork]);

  const handleAdminAction = async (transactionId, action) => {
    try {
      const res = await coordinatorApi.executeReviewAction(
        transactionId,
        action,
        'COMPLIANCE_LEAD_01',
        `Admin decision applied: ${action}`
      );
      setActionFeedback({
        message: `Transaction ${transactionId}: Successfully set to ${res.new_status}`,
        type: 'success',
      });
      setTimeout(() => setActionFeedback(null), 4000);
      fetchSummary(false);
      if (selectedNetwork) {
        loadNetworkDetail(selectedNetwork, true);
      }
    } catch (err) {
      setActionFeedback({
        message: `Action ${action} failed. Ensure backend port 8002 is active.`,
        type: 'error',
      });
      setTimeout(() => setActionFeedback(null), 4000);
    }
  };

  const handleAccountAction = async (accountId, action, bank) => {
    try {
      const res = await coordinatorApi.executeAccountAction(
        accountId,
        action,
        bank || 'SBI',
        'COMPLIANCE_LEAD_01',
        `Direct Node Enforcement: ${action}`
      );
      setActionFeedback({
        message: `Account ${accountId}: Successfully enforced ${action} -> Status: ${res.new_status}`,
        type: 'success',
      });
      setTimeout(() => setActionFeedback(null), 4000);
      fetchSummary(false);
      if (selectedNetwork) {
        loadNetworkDetail(selectedNetwork, true);
      }
    } catch (err) {
      setActionFeedback({
        message: `Account action ${action} failed: ${err.message}`,
        type: 'error',
      });
      setTimeout(() => setActionFeedback(null), 4000);
    }
  };

  // Filtered nodes and edges for graph view
  const nodes = (networkDetail?.nodes || []).filter((n) => {
    if (bankFilter !== 'ALL' && n.bank !== bankFilter) return false;
    if (riskFilter !== 'ALL') {
      if (riskFilter === 'CRITICAL' && n.behaviour_risk < 80) return false;
      if (riskFilter === 'HIGH' && (n.behaviour_risk < 60 || n.behaviour_risk >= 80)) return false;
      if (riskFilter === 'MEDIUM' && (n.behaviour_risk < 30 || n.behaviour_risk >= 60)) return false;
      if (riskFilter === 'LOW' && n.behaviour_risk >= 30) return false;
    }
    return true;
  });

  const visibleNodeIds = new Set(nodes.map((n) => n.account_id));
  const edges = (networkDetail?.edges || []).filter(
    (e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
  );

  // Position nodes in a radial circular or layered layout
  const nodePositions = {};
  const totalNodes = nodes.length || 1;
  const centerX = 360;
  const centerY = 240;
  const radius = Math.min(220, 60 + totalNodes * 20);

  nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / totalNodes;
    nodePositions[node.account_id] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  return (
    <div style={{ padding: '24px', minHeight: '100%' }}>
      {/* Toast */}
      {actionFeedback && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: actionFeedback.type === 'error' ? 'rgba(239, 68, 68, 0.95)' : 'rgba(16, 185, 129, 0.95)',
          color: '#fff',
          padding: '12px 20px',
          borderRadius: '8px',
          boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
          zIndex: 9999,
          fontSize: '0.85rem',
          fontWeight: '700',
        }}>
          {actionFeedback.message}
        </div>
      )}

      {/* Real-Time Live Alert Banner */}
      {liveAlert && (
        <div
          className="alert-toast-banner"
          style={{
            background: 'linear-gradient(90deg, rgba(239, 68, 68, 0.95), rgba(185, 28, 28, 0.95))',
            color: '#FFFFFF',
            padding: '12px 20px',
            borderRadius: '8px',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 8px 24px rgba(239, 68, 68, 0.35)',
            fontWeight: '700',
            fontSize: '0.85rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle size={20} />
            <span>{liveAlert}</span>
          </div>
          <button
            onClick={() => setLiveAlert(null)}
            style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Header with Title & Live Controls */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '14px',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#FFFFFF', letterSpacing: '-0.01em' }}>
              MULE NETWORKS INVESTIGATION
            </h2>
            <span style={{
              fontSize: '0.7rem',
              fontWeight: '800',
              padding: '2px 8px',
              borderRadius: '6px',
              background: 'rgba(239, 68, 68, 0.15)',
              color: '#EF4444',
              border: '1px solid rgba(239, 68, 68, 0.4)',
            }}>
              GNN CLUSTERED
            </span>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '3px' }}>
            Autonomous multi-bank mule grouping, network-level role assignment, and controlled funds lien tracking.
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 14px',
              borderRadius: '8px',
              border: autoRefresh ? '1px solid #10B981' : '1px solid var(--border)',
              background: autoRefresh ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255,255,255,0.05)',
              color: autoRefresh ? '#34D399' : 'var(--text-muted)',
              fontSize: '0.76rem',
              fontWeight: '800',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <span
              className={autoRefresh ? 'live-dot' : ''}
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: autoRefresh ? '#10B981' : '#64748B',
              }}
            />
            {autoRefresh ? 'LIVE STREAM: ON (2s)' : 'LIVE STREAM: PAUSED'}
          </button>

          <button
            onClick={() => fetchSummary(true)}
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '8px 16px',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '14px',
        marginBottom: '24px',
      }}>
        <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>TOTAL NETWORKS</div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#60A5FA', marginTop: '4px' }}>
            {summaryData?.total_networks ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Discovered by ADSL</div>
        </div>

        <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>CRITICAL NETWORKS</div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#EF4444', marginTop: '4px' }}>
            {summaryData?.critical_networks ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Risk Score ≥ 80</div>
        </div>

        <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>MULE ACCOUNTS DETECTED</div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#F97316', marginTop: '4px' }}>
            {summaryData?.mule_accounts_detected ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>GNN Confidence ≥ 85%</div>
        </div>

        <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>SUSPICIOUS ACCOUNTS</div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#F59E0B', marginTop: '4px' }}>
            {summaryData?.suspicious_accounts ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Behavioural deviation flags</div>
        </div>

        <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>NETWORKS UNDER REVIEW</div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#A78BFA', marginTop: '4px' }}>
            {summaryData?.networks_under_review ?? 0}
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Lien Holds Active</div>
        </div>
      </div>

      {/* Main Content Layout: Networks Table & Interactive Graph Viewer */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Networks Table */}
        <div className="card" style={{ padding: '20px', background: 'rgba(10, 15, 25, 0.8)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#FFFFFF' }}>
              Detected Mule Networks
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Click any network row to open interactive graph investigation
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px' }}>NETWORK ID</th>
                  <th style={{ padding: '10px' }}>RISK SCORE</th>
                  <th style={{ padding: '10px' }}>RISK LEVEL</th>
                  <th style={{ padding: '10px' }}>MULE ACCOUNTS</th>
                  <th style={{ padding: '10px' }}>SUSPICIOUS</th>
                  <th style={{ padding: '10px' }}>TOTAL</th>
                  <th style={{ padding: '10px' }}>BANKS INVOLVED</th>
                  <th style={{ padding: '10px' }}>PRIMARY PATTERN</th>
                  <th style={{ padding: '10px' }}>STATUS</th>
                  <th style={{ padding: '10px', textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {(summaryData?.networks || []).length === 0 ? (
                  <tr>
                    <td colSpan="9" style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                      <Network size={36} style={{ margin: '0 auto 12px', opacity: 0.4, color: '#60A5FA' }} />
                      <div style={{ fontSize: '0.95rem', fontWeight: '700', color: '#E2E8F0', marginBottom: '6px' }}>
                        No Mule Networks Tracked Yet
                      </div>
                      <div style={{ fontSize: '0.8rem', maxWidth: '480px', margin: '0 auto', lineHeight: '1.4' }}>
                        Mule networks and interactive graph topologies appear dynamically as live transactions stream from the simulator and the GATv2 GNN model detects suspicious money mule clusters.
                      </div>
                    </td>
                  </tr>
                ) : (
                  (summaryData?.networks || []).map((net) => {
                    const isSelected = selectedNetwork === net.network_id;
                    const isCritical = net.risk_level === 'CRITICAL';
                    return (
                      <tr
                      key={net.network_id}
                      onClick={() => loadNetworkDetail(net.network_id)}
                      style={{
                        borderBottom: '1px solid rgba(255,255,255,0.05)',
                        background: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                        cursor: 'pointer',
                        transition: 'background 0.15s ease',
                      }}
                    >
                      <td style={{ padding: '12px 10px', fontWeight: '800', color: '#93C5FD' }}>
                        {net.network_id}
                      </td>
                      <td style={{ padding: '12px 10px', fontWeight: '800', color: isCritical ? '#EF4444' : '#F59E0B' }}>
                        {net.risk_score}
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '5px',
                          fontSize: '0.7rem',
                          fontWeight: '800',
                          background: isCritical ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                          color: isCritical ? '#EF4444' : '#F59E0B',
                        }}>
                          {net.risk_level}
                        </span>
                      </td>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#F87171' }}>
                        {net.mule_accounts}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#FBBF24' }}>
                        {net.suspicious_accounts}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#E2E8F0' }}>
                        {net.total_accounts}
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {(net.banks_involved || []).map((b) => (
                            <span key={b} style={{
                              fontSize: '0.68rem',
                              padding: '1px 5px',
                              borderRadius: '3px',
                              background: 'rgba(255,255,255,0.06)',
                              color: b === 'SBI' ? '#60A5FA' : b === 'AXIS' ? '#EC4899' : '#FBBF24',
                              fontWeight: '700',
                            }}>
                              {b}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td style={{ padding: '12px 10px', color: '#CBD5E1', fontWeight: '600' }}>
                        {net.primary_pattern}
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        {(() => {
                          const st = net.status || 'UNDER_REVIEW';
                          let bg = 'rgba(167, 139, 250, 0.25)';
                          let color = '#C084FC';
                          if (st === 'FROZEN') {
                            bg = 'rgba(239, 68, 68, 0.25)';
                            color = '#EF4444';
                          } else if (st === 'RESTRICTED') {
                            bg = 'rgba(249, 115, 22, 0.25)';
                            color = '#F97316';
                          } else if (st === 'UNDER_REVIEW') {
                            bg = 'rgba(167, 139, 250, 0.25)';
                            color = '#C084FC';
                          } else if (st === 'MONITORING') {
                            bg = 'rgba(245, 158, 11, 0.25)';
                            color = '#F59E0B';
                          } else {
                            bg = 'rgba(16, 185, 129, 0.2)';
                            color = '#34D399';
                          }
                          return (
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '5px',
                              fontSize: '0.7rem',
                              fontWeight: '800',
                              background: bg,
                              color: color,
                            }}>
                              {st}
                            </span>
                          );
                        })()}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right' }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            loadNetworkDetail(net.network_id);
                          }}
                          style={{
                            padding: '4px 10px',
                            borderRadius: '5px',
                            border: '1px solid rgba(59, 130, 246, 0.4)',
                            background: 'rgba(59, 130, 246, 0.15)',
                            color: '#93C5FD',
                            fontSize: '0.72rem',
                            fontWeight: '700',
                            cursor: 'pointer',
                          }}
                        >
                          Investigate
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
            </table>
          </div>
        </div>

        {/* Interactive Mule Network Graph & Forensics Panel */}
        {networkDetail && (
          <div className="card" style={{ padding: '20px', background: 'rgba(10, 15, 25, 0.95)', border: '1px solid rgba(59, 130, 246, 0.35)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: '800', color: '#FFFFFF' }}>
                    Interactive Graph Forensics: {networkDetail.network_id}
                  </h3>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: '800',
                    color: networkDetail.risk_level === 'CRITICAL' ? '#EF4444' : '#F59E0B',
                  }}>
                    Risk Score: {networkDetail.risk_score}
                  </span>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '5px',
                    fontSize: '0.7rem',
                    fontWeight: '800',
                    background: networkDetail.status === 'FROZEN' ? 'rgba(239, 68, 68, 0.25)' :
                                networkDetail.status === 'RESTRICTED' ? 'rgba(249, 115, 22, 0.25)' :
                                networkDetail.status === 'UNDER_REVIEW' ? 'rgba(167, 139, 250, 0.25)' : 'rgba(245, 158, 11, 0.25)',
                    color: networkDetail.status === 'FROZEN' ? '#EF4444' :
                           networkDetail.status === 'RESTRICTED' ? '#F97316' :
                           networkDetail.status === 'UNDER_REVIEW' ? '#C084FC' : '#F59E0B',
                  }}>
                    {networkDetail.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Pattern: <strong style={{ color: '#E2E8F0' }}>{networkDetail.primary_pattern}</strong> &nbsp;•&nbsp;
                  Trigger Transaction: <code>{networkDetail.trigger_transaction_id}</code>
                </div>
              </div>

              {/* Graph Toolbar & Filters */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '4px', borderRadius: '6px' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', paddingLeft: '4px' }}>Bank:</span>
                  {['ALL', 'SBI', 'AXIS', 'IOB'].map((b) => (
                    <button
                      key={b}
                      onClick={() => setBankFilter(b)}
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.68rem',
                        fontWeight: '700',
                        border: 'none',
                        cursor: 'pointer',
                        background: bankFilter === b ? '#3B82F6' : 'transparent',
                        color: bankFilter === b ? '#fff' : 'var(--text-muted)',
                      }}
                    >
                      {b}
                    </button>
                  ))}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '4px', borderRadius: '6px' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', paddingLeft: '4px' }}>Risk:</span>
                  {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((r) => (
                    <button
                      key={r}
                      onClick={() => setRiskFilter(r)}
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '0.68rem',
                        fontWeight: '700',
                        border: 'none',
                        cursor: 'pointer',
                        background: riskFilter === r ? '#8B5CF6' : 'transparent',
                        color: riskFilter === r ? '#fff' : 'var(--text-muted)',
                      }}
                    >
                      {r}
                    </button>
                  ))}
                </div>

                {/* Zoom Controls */}
                <div style={{ display: 'flex', gap: '2px' }}>
                  <button
                    onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.2))}
                    title="Zoom In"
                    style={{
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid var(--border)',
                      borderRadius: '4px',
                      padding: '5px 8px',
                      color: '#fff',
                      cursor: 'pointer',
                    }}
                  >
                    <ZoomIn size={14} />
                  </button>
                  <button
                    onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.2))}
                    title="Zoom Out"
                    style={{
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid var(--border)',
                      borderRadius: '4px',
                      padding: '5px 8px',
                      color: '#fff',
                      cursor: 'pointer',
                    }}
                  >
                    <ZoomOut size={14} />
                  </button>
                  <button
                    onClick={() => {
                      setZoomLevel(1);
                      setPanOffset({ x: 0, y: 0 });
                    }}
                    title="Reset View"
                    style={{
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid var(--border)',
                      borderRadius: '4px',
                      padding: '5px 8px',
                      color: '#fff',
                      cursor: 'pointer',
                    }}
                  >
                    <Maximize2 size={14} />
                  </button>
                </div>
              </div>
            </div>

            {/* Canvas Container + Node Inspector Sidebar */}
            <div style={{ display: 'grid', gridTemplateColumns: selectedNode ? '1fr 340px' : '1fr', gap: '16px' }}>
              {/* Interactive SVG Canvas */}
              <div
                style={{
                  background: 'rgba(5, 8, 14, 0.95)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: '10px',
                  height: '520px',
                  overflow: 'hidden',
                  position: 'relative',
                  cursor: isDraggingRef.current ? 'grabbing' : 'grab',
                }}
                onMouseDown={(e) => {
                  isDraggingRef.current = true;
                  dragStartRef.current = { x: e.clientX - panOffset.x, y: e.clientY - panOffset.y };
                }}
                onMouseMove={(e) => {
                  if (isDraggingRef.current) {
                    setPanOffset({
                      x: e.clientX - dragStartRef.current.x,
                      y: e.clientY - dragStartRef.current.y,
                    });
                  }
                }}
                onMouseUp={() => {
                  isDraggingRef.current = false;
                }}
                onMouseLeave={() => {
                  isDraggingRef.current = false;
                }}
              >
                <svg
                  width="100%"
                  height="100%"
                  viewBox="0 0 720 480"
                  style={{
                    transform: `scale(${zoomLevel}) translate(${panOffset.x}px, ${panOffset.y}px)`,
                    transformOrigin: 'center center',
                    transition: isDraggingRef.current ? 'none' : 'transform 0.1s ease',
                  }}
                >
                  {/* Arrow marker definition */}
                  <defs>
                    <marker
                      id="arrow"
                      viewBox="0 0 10 10"
                      refX="22"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748B" />
                    </marker>
                    <marker
                      id="arrow-active"
                      viewBox="0 0 10 10"
                      refX="22"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#38BDF8" />
                    </marker>
                    <marker
                      id="arrow-halted"
                      viewBox="0 0 10 10"
                      refX="22"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#EF4444" />
                    </marker>
                    <marker
                      id="arrow-review"
                      viewBox="0 0 10 10"
                      refX="22"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#C084FC" />
                    </marker>
                  </defs>

                  {/* Edges with Transaction Flow Directions & Amounts */}
                  {edges.map((e, idx) => {
                    const src = nodePositions[e.source];
                    const tgt = nodePositions[e.target];
                    if (!src || !tgt) return null;
                    const isConnectedToSelected =
                      selectedNode && (e.source === selectedNode.account_id || e.target === selectedNode.account_id);
                    const midX = (src.x + tgt.x) / 2;
                    const midY = (src.y + tgt.y) / 2;

                    const isHalted = Boolean(e.flow_stopped || e.status === 'UNDER_REVIEW' || e.status === 'RESTRICTED' || e.status === 'FROZEN');
                    const isFrozenOrRestricted = e.status === 'RESTRICTED' || e.status === 'FROZEN';
                    const isUnderReview = e.status === 'UNDER_REVIEW';

                    return (
                      <g key={idx}>
                        {/* Static base connection */}
                        <line
                          x1={src.x}
                          y1={src.y}
                          x2={tgt.x}
                          y2={tgt.y}
                          stroke={
                            isFrozenOrRestricted
                              ? '#EF4444'
                              : isUnderReview
                              ? '#C084FC'
                              : isConnectedToSelected
                              ? '#38BDF8'
                              : '#334155'
                          }
                          strokeWidth={isHalted ? 2.6 : isConnectedToSelected ? 2.5 : 1.5}
                          strokeDasharray={isHalted ? '6,4' : e.is_cross_bank ? '5,4' : 'none'}
                          markerEnd={
                            isFrozenOrRestricted
                              ? 'url(#arrow-halted)'
                              : isUnderReview
                              ? 'url(#arrow-review)'
                              : isConnectedToSelected
                              ? 'url(#arrow-active)'
                              : 'url(#arrow)'
                          }
                        />

                        {/* Animated Live Transaction Flow along the directed edge ONLY if money flow is active */}
                        {!isHalted ? (
                          <line
                            x1={src.x}
                            y1={src.y}
                            x2={tgt.x}
                            y2={tgt.y}
                            stroke={isConnectedToSelected ? '#F43F5E' : '#38BDF8'}
                            strokeWidth={isConnectedToSelected ? 3 : 2}
                            strokeDasharray="6,6"
                            className="flow-line-pulse"
                            opacity="0.85"
                            pointerEvents="none"
                          />
                        ) : (
                          /* Flow Finished Badge when money flow stops due to risk score */
                          <g>
                            <circle
                              cx={midX}
                              cy={midY - 14}
                              r="7"
                              fill={isFrozenOrRestricted ? 'rgba(239, 68, 68, 0.3)' : 'rgba(192, 132, 252, 0.3)'}
                              stroke={isFrozenOrRestricted ? '#EF4444' : '#C084FC'}
                              strokeWidth="1.2"
                            />
                            <text
                              x={midX}
                              y={midY - 11}
                              textAnchor="middle"
                              fill={isFrozenOrRestricted ? '#EF4444' : '#C084FC'}
                              fontSize="8"
                              fontWeight="800"
                            >
                              {isFrozenOrRestricted ? '✕' : '🔒'}
                            </text>
                          </g>
                        )}

                        <rect
                          x={midX - 38}
                          y={midY - 8}
                          width="76"
                          height="16"
                          rx="4"
                          fill={isFrozenOrRestricted ? 'rgba(30, 10, 15, 0.95)' : isUnderReview ? 'rgba(25, 15, 35, 0.95)' : 'rgba(15, 23, 42, 0.90)'}
                          stroke={isFrozenOrRestricted ? '#EF4444' : isUnderReview ? '#C084FC' : 'rgba(255,255,255,0.08)'}
                          strokeWidth={isHalted ? 1.5 : 1}
                        />
                        <text
                          x={midX}
                          y={midY + 4}
                          textAnchor="middle"
                          fill={isFrozenOrRestricted ? '#FCA5A5' : isUnderReview ? '#E9D5FF' : '#94A3B8'}
                          fontSize="9"
                          fontWeight="700"
                        >
                          ₹{(e.amount || 0).toLocaleString()} {isHalted ? (isFrozenOrRestricted ? ' [HALT]' : ' [LIEN]') : ''}
                        </text>
                      </g>
                    );
                  })}

                  {/* Nodes */}
                  {nodes.map((node) => {
                    const pos = nodePositions[node.account_id];
                    if (!pos) return null;
                    const isSelected = selectedNode?.account_id === node.account_id;
                    const color = CLASSIFICATION_COLORS[node.classification] || '#6B7280';
                    const roleColor = ROLE_COLORS[node.network_role] || '#6B7280';

                    return (
                      <g
                        key={node.account_id}
                        transform={`translate(${pos.x}, ${pos.y})`}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedNode(node);
                        }}
                        style={{ cursor: 'pointer' }}
                      >
                        {/* Dynamic pulsing halo for MULE or SUSPICIOUS nodes */}
                        {(node.classification === 'MULE' || node.classification === 'SUSPICIOUS') && (
                          <circle
                            r="24"
                            fill="none"
                            stroke={color}
                            strokeWidth="2"
                            className="node-pulse-halo"
                          />
                        )}

                        {/* Glow halo for selected or mule */}
                        {(isSelected || node.classification === 'MULE') && (
                          <circle r="22" fill={color} opacity="0.25" />
                        )}

                        {/* Outer node circle */}
                        <circle
                          r="15"
                          fill="#0F172A"
                          stroke={isSelected ? '#38BDF8' : color}
                          strokeWidth={isSelected ? 3 : 2}
                        />

                        {/* Inner role core */}
                        <circle r="6" fill={roleColor} />

                        {/* Live GNN Confidence Pill above Node */}
                        {node.gnn_mule_probability >= 0.35 && (
                          <g transform="translate(0, -22)">
                            <rect
                              x="-25"
                              y="-7"
                              width="50"
                              height="13"
                              rx="3"
                              fill="#831843"
                              stroke="#F43F5E"
                              strokeWidth="0.8"
                            />
                            <text
                              x="0"
                              y="3"
                              textAnchor="middle"
                              fill="#FDA4AF"
                              fontSize="7.5"
                              fontWeight="900"
                            >
                              GNN {(node.gnn_mule_probability * 100).toFixed(0)}%
                            </text>
                          </g>
                        )}

                        {/* Account label */}
                        <text
                          y="26"
                          textAnchor="middle"
                          fill={isSelected ? '#38BDF8' : '#F8FAFC'}
                          fontSize="10"
                          fontWeight="700"
                        >
                          {node.account_id}
                        </text>

                        {/* Role tag */}
                        <text
                          y="37"
                          textAnchor="middle"
                          fill={roleColor}
                          fontSize="8"
                          fontWeight="800"
                        >
                          {node.network_role}
                        </text>
                      </g>
                    );
                  })}
                </svg>

                {/* Graph Legend Overlay */}
                <div style={{
                  position: 'absolute',
                  bottom: '12px',
                  left: '12px',
                  background: 'rgba(15, 23, 42, 0.85)',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  fontSize: '0.68rem',
                  display: 'flex',
                  gap: '12px',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#EF4444' }} />
                    <span style={{ color: '#E2E8F0' }}>Mule</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B' }} />
                    <span style={{ color: '#E2E8F0' }}>Suspicious</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }} />
                    <span style={{ color: '#E2E8F0' }}>Normal</span>
                  </div>
                  <span style={{ color: 'var(--text-muted)' }}>• Drag to pan, scroll to zoom</span>
                </div>
              </div>

              {/* Node Details Inspector Sidebar (All 13 Required Properties) */}
              {selectedNode && (
                <div style={{
                  background: 'rgba(12, 18, 30, 0.95)',
                  border: '1px solid rgba(59, 130, 246, 0.35)',
                  borderRadius: '10px',
                  padding: '18px',
                  overflowY: 'auto',
                  maxHeight: '520px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div style={{ fontWeight: '800', fontSize: '0.95rem', color: '#FFFFFF' }}>
                      Account Inspector
                    </div>
                    <button
                      onClick={() => setSelectedNode(null)}
                      style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                    >
                      <X size={16} />
                    </button>
                  </div>

                  <div style={{ marginBottom: '14px' }}>
                    <div style={{ fontSize: '1.05rem', fontWeight: '900', color: '#93C5FD' }}>
                      {selectedNode.account_id}
                    </div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      Bank: <strong style={{ color: '#E2E8F0' }}>{selectedNode.bank}</strong> &nbsp;•&nbsp;
                      Role: <strong style={{ color: ROLE_COLORS[selectedNode.network_role] }}>{selectedNode.network_role}</strong>
                    </div>
                  </div>

                  {/* 13 Attributes Grid */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.74rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Classification:</span>
                      <strong style={{ color: CLASSIFICATION_COLORS[selectedNode.classification] }}>
                        {selectedNode.classification}
                      </strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Behaviour Risk Score:</span>
                      <strong style={{ color: selectedNode.behaviour_risk >= 70 ? '#EF4444' : '#F59E0B' }}>
                        {selectedNode.behaviour_risk} / 100
                      </strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>XGBoost Risk Score:</span>
                      <strong style={{ color: selectedNode.xgboost_risk >= 70 ? '#EF4444' : '#60A5FA' }}>
                        {selectedNode.xgboost_risk} / 100
                      </strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>GNN Mule Probability:</span>
                      <strong style={{ color: '#EC4899' }}>
                        {(selectedNode.gnn_mule_probability * 100).toFixed(1)}%
                      </strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Incoming Transactions:</span>
                      <strong style={{ color: '#E2E8F0' }}>{selectedNode.incoming_transactions}</strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Outgoing Transactions:</span>
                      <strong style={{ color: '#E2E8F0' }}>{selectedNode.outgoing_transactions}</strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Fan-In Pattern:</span>
                      <strong style={{ color: selectedNode.fan_in ? '#EF4444' : '#10B981' }}>
                        {selectedNode.fan_in ? 'DETECTED' : 'None'}
                      </strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Fan-Out Pattern:</span>
                      <strong style={{ color: selectedNode.fan_out ? '#EF4444' : '#10B981' }}>
                        {selectedNode.fan_out ? 'DETECTED' : 'None'}
                      </strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Rapid Forwarding:</span>
                      <strong style={{ color: selectedNode.rapid_forwarding ? '#F97316' : '#10B981' }}>
                        {selectedNode.rapid_forwarding ? 'HIGH VELOCITY' : 'None'}
                      </strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Amount Splitting:</span>
                      <strong style={{ color: selectedNode.amount_splitting ? '#F59E0B' : '#10B981' }}>
                        {selectedNode.amount_splitting ? 'SMURFING PATTERN' : 'None'}
                      </strong>
                    </div>
                  </div>

                  {/* Connected accounts list */}
                  <div style={{ marginTop: '12px' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Connected Accounts ({(selectedNode.connected_accounts || []).length}):
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {(selectedNode.connected_accounts || []).map((acc) => (
                        <span
                          key={acc}
                          style={{
                            fontSize: '0.65rem',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: 'rgba(255,255,255,0.06)',
                            color: '#94A3B8',
                          }}
                        >
                          {acc}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Direct Account Enforcement Actions on Selected Node */}
                  <div style={{ marginTop: '14px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '10px' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: '800', color: '#60A5FA', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Lock size={12} />
                      <span>Direct Account Enforcement: {selectedNode.account_id}</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '10px' }}>
                      <button
                        onClick={() => handleAccountAction(selectedNode.account_id, 'FREEZE', selectedNode.bank)}
                        style={{
                          padding: '6px 8px',
                          borderRadius: '5px',
                          border: '1px solid #EF4444',
                          background: 'rgba(239, 68, 68, 0.22)',
                          color: '#FCA5A5',
                          fontSize: '0.68rem',
                          fontWeight: '800',
                          cursor: 'pointer',
                        }}
                      >
                        ❄️ FREEZE NODE
                      </button>

                      <button
                        onClick={() => handleAccountAction(selectedNode.account_id, 'RESTRICT', selectedNode.bank)}
                        style={{
                          padding: '6px 8px',
                          borderRadius: '5px',
                          border: '1px solid #F97316',
                          background: 'rgba(249, 115, 22, 0.18)',
                          color: '#FDBA74',
                          fontSize: '0.68rem',
                          fontWeight: '800',
                          cursor: 'pointer',
                        }}
                      >
                        ⛔ RESTRICT
                      </button>

                      <button
                        onClick={() => handleAccountAction(selectedNode.account_id, 'MONITOR', selectedNode.bank)}
                        style={{
                          padding: '6px 8px',
                          borderRadius: '5px',
                          border: '1px solid #F59E0B',
                          background: 'rgba(245, 158, 11, 0.15)',
                          color: '#FDE68A',
                          fontSize: '0.68rem',
                          fontWeight: '800',
                          cursor: 'pointer',
                        }}
                      >
                        👁️ MONITOR
                      </button>

                      <button
                        onClick={() => handleAccountAction(selectedNode.account_id, 'RELEASE', selectedNode.bank)}
                        style={{
                          padding: '6px 8px',
                          borderRadius: '5px',
                          border: '1px solid #10B981',
                          background: 'rgba(16, 185, 129, 0.18)',
                          color: '#6EE7B7',
                          fontSize: '0.68rem',
                          fontWeight: '800',
                          cursor: 'pointer',
                        }}
                      >
                        ✅ RESTORE
                      </button>
                    </div>
                  </div>

                  {/* Trigger Transaction Admin Actions */}
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '10px' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: '700', color: '#94A3B8', marginBottom: '8px' }}>
                      Cluster Trigger Txn Actions ({networkDetail.trigger_transaction_id}):
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                      <button
                        onClick={() => handleAdminAction(networkDetail.trigger_transaction_id, 'RELEASE')}
                        style={{
                          padding: '6px 8px',
                          borderRadius: '5px',
                          border: '1px solid #10B981',
                          background: 'rgba(16, 185, 129, 0.15)',
                          color: '#34D399',
                          fontSize: '0.68rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        RELEASE FUNDS
                      </button>

                      <button
                        onClick={() => handleAdminAction(networkDetail.trigger_transaction_id, 'MONITOR')}
                        style={{
                          padding: '6px 8px',
                          borderRadius: '5px',
                          border: '1px solid #F59E0B',
                          background: 'rgba(245, 158, 11, 0.15)',
                          color: '#FBBF24',
                          fontSize: '0.68rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        MONITOR
                      </button>

                      <button
                        onClick={() => handleAdminAction(networkDetail.trigger_transaction_id, 'RESTRICT')}
                        style={{
                          padding: '6px 8px',
                          borderRadius: '5px',
                          border: '1px solid #F97316',
                          background: 'rgba(249, 115, 22, 0.15)',
                          color: '#FB923C',
                          fontSize: '0.68rem',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        RESTRICT
                      </button>

                      <button
                        onClick={() => handleAdminAction(networkDetail.trigger_transaction_id, 'FREEZE')}
                        style={{
                          padding: '6px 8px',
                          borderRadius: '5px',
                          border: '1px solid #EF4444',
                          background: 'rgba(239, 68, 68, 0.25)',
                          color: '#FCA5A5',
                          fontSize: '0.68rem',
                          fontWeight: '800',
                          cursor: 'pointer',
                        }}
                      >
                        FREEZE
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
