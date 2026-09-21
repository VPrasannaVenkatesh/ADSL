import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
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
  Zap,
  Play,
  ArrowDown,
  Clock,
  GitBranch,
  Search,
  ShieldAlert,
  FileText,
  CheckCircle,
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

export function MuleNetworksView({ activeSubNav = 'medium', onSubNavChange }) {
  const [subNav, setSubNav] = useState(activeSubNav || 'medium'); // 'medium' | 'high' | 'all'
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [transactions, setTransactions] = useState([]);
  const [monitoringCases, setMonitoringCases] = useState([]);
  const [underReviewItems, setUnderReviewItems] = useState([]);
  const [selectedTxId, setSelectedTxId] = useState(null);
  const [selectedTx, setSelectedTx] = useState(null);
  const [selectedNetwork, setSelectedNetwork] = useState(null);
  const [networkDetail, setNetworkDetail] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  // Sync external activeSubNav prop with internal subNav state
  useEffect(() => {
    if (activeSubNav) setSubNav(activeSubNav);
  }, [activeSubNav]);

  const isGraphView = subNav === 'graph' || subNav === 'all';

  const handleSubNavChange = (mode) => {
    setSubNav(mode);
    if (onSubNavChange) onSubNavChange(mode);
  };

  // Dynamic Live Streaming Controls
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [autoFollowNewTx, setAutoFollowNewTx] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [liveAlert, setLiveAlert] = useState(null);
  const prevLatestTxIdRef = useRef(null);
  const prevNetworkCountRef = useRef(0);
  const initialLoadedRef = useRef(false);

  // Graph Layout & Filters
  const [layoutMode, setLayoutMode] = useState('FLOW'); // 'FLOW' (Source -> Mule -> Sink) | 'RADIAL'
  const [bankFilter, setBankFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');

  // Zoom & Pan for interactive canvas
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });

  // Action status toast
  const [actionFeedback, setActionFeedback] = useState(null);

  // Fetch Mule Networks Summary (aggregate numbers & networks list)
  const fetchSummary = useCallback(async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const data = await coordinatorApi.getMuleNetworks();
      if (data) {
        if (prevNetworkCountRef.current > 0 && data.total_networks > prevNetworkCountRef.current) {
          const newClusters = data.total_networks - prevNetworkCountRef.current;
          setLiveAlert(`🚨 GATv2 model identified ${newClusters} new Mule Network cluster!`);
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
  }, []);

  // Fetch Auxiliary Monitoring Cases & Active Lien Layer items
  const fetchAuxiliaryData = useCallback(async () => {
    try {
      const [monRes, revRes] = await Promise.all([
        coordinatorApi.getMonitoringCases().catch(() => ({ cases: [] })),
        coordinatorApi.getUnderReview().catch(() => ({ under_review_items: [] })),
      ]);
      if (monRes?.cases) setMonitoringCases(monRes.cases);
      if (revRes?.under_review_items) setUnderReviewItems(revRes.under_review_items);
    } catch (err) {
      console.error('Error fetching auxiliary monitoring data:', err);
    }
  }, []);

  // Fetch Live Transactions
  const fetchTransactions = useCallback(async (silent = false) => {
    try {
      const res = await coordinatorApi.getAdslTransactions(80);
      const list = res?.transactions || [];
      setTransactions(list);

      // Only on very first load if no transaction or graph is selected yet
      if (!initialLoadedRef.current && list.length > 0 && !selectedTxId) {
        initialLoadedRef.current = true;
        const first = list[0];
        prevLatestTxIdRef.current = first.transaction_id;
        setSelectedTxId(first.transaction_id);
        setSelectedTx(first);
        loadTransactionGraph(first.transaction_id, false);
      }
    } catch (err) {
      console.error('Error fetching ADSL transactions:', err);
    }
  }, [selectedTxId]);

  // Load Graph centered on a specific Transaction
  const loadTransactionGraph = async (txId, isSilent = false) => {
    try {
      const data = await coordinatorApi.getTransactionGraph(txId);
      if (data) {
        setNetworkDetail(data);
        if (data.network_id) setSelectedNetwork(data.network_id);
        setSelectedTxId(txId);
        setTransactions((curr) => {
          const found = curr.find((t) => t.transaction_id === txId);
          if (found) setSelectedTx(found);
          return curr;
        });
        if (!isSilent) {
          setSelectedNode(null);
          setZoomLevel(1);
          setPanOffset({ x: 0, y: 0 });
        }
      }
    } catch (err) {
      console.error('Error loading transaction graph:', err);
    }
  };

  // Load Graph by Network ID
  const loadNetworkDetail = async (networkId, isSilent = false) => {
    try {
      const data = await coordinatorApi.getMuleNetworkDetail(networkId);
      if (data) {
        setNetworkDetail(data);
        setSelectedNetwork(networkId);
        if (data.trigger_transaction_id) {
          setSelectedTxId(data.trigger_transaction_id);
          const found = transactions.find((t) => t.transaction_id === data.trigger_transaction_id);
          if (found) setSelectedTx(found);
        }
        if (!isSilent) {
          setSelectedNode(null);
          setZoomLevel(1);
          setPanOffset({ x: 0, y: 0 });
        }
      }
    } catch (err) {
      console.error('Error loading network detail:', err);
    }
  };

  // Real-time dynamic background loop (every 1.0 second)
  useEffect(() => {
    fetchSummary(true);
    fetchTransactions(true);
    fetchAuxiliaryData();

    const timer = setInterval(() => {
      if (autoRefresh) {
        fetchSummary(false);
        fetchTransactions(true);
        fetchAuxiliaryData();
        // Graph is strictly locked to prevent auto-changing - only updates when user clicks Investigate
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [autoRefresh, fetchSummary, fetchTransactions, fetchAuxiliaryData]);

  // Segregated Medium Risk Transactions (Tier 2: 30-59 Risk)
  const mediumTransactions = useMemo(() => {
    const map = new Map();
    transactions.forEach((tx) => {
      const r = tx.risk_score || tx.final_risk_score || 0;
      if ((r >= 30 && r < 60) || tx.risk_level === 'MEDIUM' || tx.status === 'MONITORING' || tx.decision === 'MONITOR') {
        map.set(tx.transaction_id, tx);
      }
    });
    monitoringCases.forEach((c) => {
      if (!map.has(c.transaction_id)) {
        map.set(c.transaction_id, {
          transaction_id: c.transaction_id,
          timestamp: c.created_at,
          sender_account_id: c.account_id,
          sender_bank: c.bank,
          receiver_account_id: c.counterparty_account_id || 'MONITORED_HUB',
          receiver_bank: c.bank,
          amount: c.amount || 0,
          risk_score: c.initial_risk_score || 45.0,
          risk_level: 'MEDIUM',
          decision: 'MONITOR',
          action: 'MONITOR',
          status: 'MONITORING',
          gnn_mule_probability: 0.22,
          risk_reasons: [c.monitoring_reason || 'Tier 2 Dynamic Behavioral Monitoring', ...(c.suspicious_indicators || [])],
          monitoring_case: c,
        });
      }
    });
    return Array.from(map.values());
  }, [transactions, monitoringCases]);

  // Derive active monitoring cases from backend or mediumTransactions stream
  const effectiveMonitoringCases = useMemo(() => {
    if (monitoringCases && monitoringCases.length > 0) return monitoringCases;
    return mediumTransactions.map((t, idx) => ({
      case_id: `CASE-MON-${t.transaction_id ? t.transaction_id.slice(-6) : String(idx + 1).padStart(3, '0')}`,
      account_id: t.sender_account_id || 'ACC-UNKNOWN',
      counterparty_account_id: t.receiver_account_id || 'RECV-UNKNOWN',
      bank: t.sender_bank || 'SBI',
      amount: t.amount || 0,
      initial_risk_score: (t.risk_score || t.final_risk_score || 45.0).toFixed(1),
      monitoring_reason: (t.risk_reasons && t.risk_reasons[0]) || 'Velocity Surveillance / Anomalous Pattern',
      follow_ups: 1 + (idx % 3),
      status: 'ACTIVE',
      transaction_id: t.transaction_id,
    }));
  }, [monitoringCases, mediumTransactions]);

  // Segregated High Risk & Mule Ring Transactions (Tier 3: >=60 Risk & Liens)
  const highTransactions = useMemo(() => {
    const map = new Map();
    transactions.forEach((tx) => {
      const r = tx.risk_score || tx.final_risk_score || 0;
      if (r >= 60 || tx.risk_level === 'HIGH' || tx.risk_level === 'CRITICAL' || ['UNDER_REVIEW', 'FROZEN', 'RESTRICTED', 'LIEN'].includes(tx.status) || tx.mule_network_id) {
        map.set(tx.transaction_id, tx);
      }
    });
    underReviewItems.forEach((item) => {
      if (!map.has(item.transaction_id)) {
        map.set(item.transaction_id, {
          transaction_id: item.transaction_id,
          timestamp: item.restricted_at,
          sender_account_id: item.account_id,
          sender_bank: item.bank,
          receiver_account_id: 'MULE_RECEPTACLE',
          receiver_bank: item.bank,
          amount: item.amount || 0,
          risk_score: Math.max(item.risk_score || 75.0, 65.0),
          risk_level: 'CRITICAL',
          decision: 'LIEN',
          action: 'HOLD',
          status: 'UNDER_REVIEW',
          gnn_mule_probability: 0.89,
          risk_reasons: [item.restriction_reason || 'Placed under Protective Lien Layer by ADSL Mule Engine'],
          lien_id: item.lien_id,
          is_active: item.is_active,
        });
      }
    });
    return Array.from(map.values());
  }, [transactions, underReviewItems]);

  // Displayed transactions depending on active sub-navigation
  const displayedTransactions = useMemo(() => {
    if (subNav === 'medium') return mediumTransactions;
    if (subNav === 'high') return highTransactions;
    return transactions;
  }, [subNav, mediumTransactions, highTransactions, transactions]);

  // Initial mount graph fallback - ensures graph is populated once without auto-switching later
  useEffect(() => {
    if (!networkDetail && displayedTransactions.length > 0) {
      const first = displayedTransactions[0];
      setSelectedTxId(first.transaction_id);
      setSelectedTx(first);
      loadTransactionGraph(first.transaction_id, false);
    }
  }, [displayedTransactions, networkDetail]);

  // Trigger Multi-Mule Flow Simulation
  const handleTriggerMuleFlow = async () => {
    setSimulating(true);
    try {
      const res = await coordinatorApi.triggerMuleSinkFlow();
      setActionFeedback({
        message: res.success ? `Multi-Mule Flow Executed: ${res.total_transactions} transactions dispersed & sunk!` : 'Flow simulation started',
        type: 'success',
      });
      setTimeout(() => setActionFeedback(null), 5000);
      fetchSummary(false);
      fetchTransactions(false);
    } catch (err) {
      setActionFeedback({
        message: `Flow simulation error: ${err.message}`,
        type: 'error',
      });
      setTimeout(() => setActionFeedback(null), 4000);
    } finally {
      setSimulating(false);
    }
  };

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
      fetchTransactions(false);
      if (selectedTxId) loadTransactionGraph(selectedTxId, true);
    } catch (err) {
      setActionFeedback({
        message: `Action ${action} failed: ${err.message}`,
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
      fetchTransactions(false);
      if (selectedTxId) loadTransactionGraph(selectedTxId, true);
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

  // Position nodes in Flow Layout (Source -> Mules/Relays -> Sink) or Radial
  const nodePositions = {};
  const totalNodes = nodes.length || 1;

  // Categorize nodes by role for Flow Layout
  const sources = nodes.filter((n) => n.network_role === 'SOURCE' || (n.incoming_transactions === 0 && n.outgoing_transactions > 0));
  const sinks = nodes.filter((n) => n.network_role === 'SINK' || (n.incoming_transactions > 0 && n.outgoing_transactions === 0));
  const middle = nodes.filter((n) => !sources.includes(n) && !sinks.includes(n));

  // Balance ranks if sources or sinks are initially empty
  const effectiveSources = [...sources];
  const effectiveMiddle = [...middle];
  const effectiveSinks = [...sinks];

  if (effectiveSources.length === 0 && effectiveMiddle.length > 1) {
    effectiveSources.push(effectiveMiddle.shift());
  }
  if (effectiveSinks.length === 0 && effectiveMiddle.length > 1) {
    effectiveSinks.push(effectiveMiddle.pop());
  }
  if (effectiveSources.length === 0 && effectiveSinks.length === 0 && nodes.length > 0) {
    nodes.forEach((n, idx) => {
      if (idx % 3 === 0) effectiveSources.push(n);
      else if (idx % 3 === 1) effectiveMiddle.push(n);
      else effectiveSinks.push(n);
    });
  }

  const hasStaggeredMiddle = effectiveMiddle.length > 3;
  const maxColNodes = Math.max(
    effectiveSources.length,
    hasStaggeredMiddle ? Math.ceil(effectiveMiddle.length / 2) : effectiveMiddle.length,
    effectiveSinks.length,
    1
  );

  // Distributed spacing constants (optimized compact flow layout for clear visibility)
  const minGap = 105;
  const flowSvgWidth = 1080;
  const flowSvgHeight = Math.max(480, maxColNodes * minGap + 90);
  const centerX = flowSvgWidth / 2;
  const centerY = flowSvgHeight / 2;

  if (layoutMode === 'FLOW') {
    if (!hasStaggeredMiddle) {
      // 3 Well-Spaced Columns: Source (160) -> Mules / Relays (560) -> Sink (960)
      const srcTotalH = (effectiveSources.length - 1) * minGap;
      const srcStartY = (flowSvgHeight - srcTotalH) / 2;
      effectiveSources.forEach((n, i) => {
        nodePositions[n.account_id] = {
          x: 160,
          y: effectiveSources.length === 1 ? flowSvgHeight / 2 : srcStartY + i * minGap,
          colIdx: 0,
        };
      });

      const midTotalH = (effectiveMiddle.length - 1) * minGap;
      const midStartY = (flowSvgHeight - midTotalH) / 2;
      effectiveMiddle.forEach((n, i) => {
        nodePositions[n.account_id] = {
          x: 560,
          y: effectiveMiddle.length === 1 ? flowSvgHeight / 2 : midStartY + i * minGap,
          colIdx: 1,
        };
      });

      const sinkTotalH = (effectiveSinks.length - 1) * minGap;
      const sinkStartY = (flowSvgHeight - sinkTotalH) / 2;
      effectiveSinks.forEach((n, i) => {
        nodePositions[n.account_id] = {
          x: 960,
          y: effectiveSinks.length === 1 ? flowSvgHeight / 2 : sinkStartY + i * minGap,
          colIdx: 2,
        };
      });
    } else {
      // 4 Well-Spaced Columns: Source (140) -> Relays (420) -> Mule Hubs (700) -> Sink (980)
      const subCol1 = effectiveMiddle.filter((_, i) => i % 2 === 0);
      const subCol2 = effectiveMiddle.filter((_, i) => i % 2 === 1);

      const srcTotalH = (effectiveSources.length - 1) * minGap;
      const srcStartY = (flowSvgHeight - srcTotalH) / 2;
      effectiveSources.forEach((n, i) => {
        nodePositions[n.account_id] = {
          x: 140,
          y: effectiveSources.length === 1 ? flowSvgHeight / 2 : srcStartY + i * minGap,
          colIdx: 0,
        };
      });

      const col1TotalH = (subCol1.length - 1) * minGap;
      const col1StartY = (flowSvgHeight - col1TotalH) / 2;
      subCol1.forEach((n, i) => {
        nodePositions[n.account_id] = {
          x: 420,
          y: subCol1.length === 1 ? flowSvgHeight / 2 : col1StartY + i * minGap,
          colIdx: 1,
        };
      });

      const col2TotalH = (subCol2.length - 1) * minGap;
      const col2StartY = (flowSvgHeight - col2TotalH) / 2;
      subCol2.forEach((n, i) => {
        nodePositions[n.account_id] = {
          x: 700,
          y: subCol2.length === 1 ? flowSvgHeight / 2 : col2StartY + i * minGap,
          colIdx: 2,
        };
      });

      const sinkTotalH = (effectiveSinks.length - 1) * minGap;
      const sinkStartY = (flowSvgHeight - sinkTotalH) / 2;
      effectiveSinks.forEach((n, i) => {
        nodePositions[n.account_id] = {
          x: 980,
          y: effectiveSinks.length === 1 ? flowSvgHeight / 2 : sinkStartY + i * minGap,
          colIdx: 3,
        };
      });
    }

    // Fallback for any unpositioned node with wide spacing
    nodes.forEach((n, i) => {
      if (!nodePositions[n.account_id]) {
        nodePositions[n.account_id] = {
          x: 260 + (i % 3) * 300,
          y: 120 + Math.floor(i / 3) * 160,
          colIdx: 1,
        };
      }
    });
  } else {
    // RADIAL ORBIT LAYOUT (Generous radius)
    const radius = Math.min(290, 150 + totalNodes * 26);
    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / totalNodes - Math.PI / 2;
      nodePositions[node.account_id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        colIdx: 1,
      };
    });
  }

  return (
    <div style={{ padding: '24px', minHeight: '100%' }}>
      {/* Toast Feedback */}
      {actionFeedback && (
        <div
          style={{
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
          }}
        >
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

      {/* Header with Title & Action Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          flexWrap: 'wrap',
          gap: '14px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#FFFFFF', letterSpacing: '-0.01em' }}>
              MULE NETWORKS & LIVE TRANSACTION FORENSICS
            </h2>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: '800',
                padding: '2px 8px',
                borderRadius: '6px',
                background: subNav === 'medium'
                  ? 'rgba(245, 158, 11, 0.15)'
                  : subNav === 'high'
                  ? 'rgba(239, 68, 68, 0.15)'
                  : 'rgba(139, 92, 246, 0.15)',
                color: subNav === 'medium' ? '#F59E0B' : subNav === 'high' ? '#EF4444' : '#A78BFA',
                border: subNav === 'medium'
                  ? '1px solid rgba(245, 158, 11, 0.4)'
                  : subNav === 'high'
                  ? '1px solid rgba(239, 68, 68, 0.4)'
                  : '1px solid rgba(139, 92, 246, 0.4)',
              }}
            >
              {subNav === 'medium' ? 'TIER 2 • DYNAMIC MONITORING' : subNav === 'high' ? 'TIER 3 • MULE RINGS & LIENS' : 'ALL CLUSTERS'}
            </span>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '3px' }}>
            {subNav === 'medium'
              ? 'Monitoring Tier 2 medium-risk transactions (30–59) for velocity bursts and behavioral deviations.'
              : subNav === 'high'
              ? 'Investigating Tier 3 high-risk mule ring topologies (≥60) with pre-trained GATv2 inference and protective liens.'
              : 'Global multi-bank transaction stream and cross-bank mule cluster detection.'}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Simulate Mule Flow Button */}
          <button
            onClick={handleTriggerMuleFlow}
            disabled={simulating}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '8px',
              border: '1px solid rgba(244, 63, 94, 0.5)',
              background: simulating
                ? 'rgba(244, 63, 94, 0.1)'
                : 'linear-gradient(135deg, rgba(244, 63, 94, 0.25) 0%, rgba(225, 29, 72, 0.35) 100%)',
              color: '#FDA4AF',
              fontSize: '0.76rem',
              fontWeight: '800',
              cursor: simulating ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <Zap size={14} color="#F43F5E" />
            <span>{simulating ? 'Executing Mule Flow...' : '⚡ Simulate Multi-Mule Flow'}</span>
          </button>

          {/* Graph Lock Indicator */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 13px',
              borderRadius: '8px',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              background: 'rgba(16, 185, 129, 0.1)',
              color: '#34D399',
              fontSize: '0.74rem',
              fontWeight: '700',
            }}
            title="Graph is locked to current investigation target and will only update when you click Investigate"
          >
            <Lock size={13} color="#10B981" />
            <span>Graph: Locked (Updates on Investigate)</span>
          </div>

          {/* Live Stream Toggle */}
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
            {autoRefresh ? 'LIVE SYNC: 1s' : 'STREAM PAUSED'}
          </button>

          {/* Manual Refresh */}
          <button
            onClick={() => {
              fetchSummary(true);
              fetchTransactions(true);
              fetchAuxiliaryData();
              if (selectedTxId) loadTransactionGraph(selectedTxId, true);
            }}
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '8px 14px',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SUB-NAVIGATION BAR UNDER MULE NETWORKS: MEDIUM VS HIGH TRANSACTIONS        */}
      {/* ========================================================================= */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '12px',
          marginBottom: '20px',
        }}
      >
        {/* Navigation 1: Medium Transactions */}
        <div
          onClick={() => handleSubNavChange('medium')}
          style={{
            padding: '14px 18px',
            borderRadius: '12px',
            cursor: 'pointer',
            border: subNav === 'medium' ? '1.5px solid #F59E0B' : '1px solid rgba(255,255,255,0.08)',
            background: subNav === 'medium'
              ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.18) 0%, rgba(217, 119, 6, 0.08) 100%)'
              : 'rgba(15, 23, 42, 0.5)',
            boxShadow: subNav === 'medium' ? '0 0 20px rgba(245, 158, 11, 0.18)' : 'none',
            transition: 'all 0.2s ease',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {subNav === 'medium' && (
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: 'linear-gradient(90deg, #F59E0B, #FBBF24)' }} />
          )}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                padding: '6px',
                borderRadius: '8px',
                background: subNav === 'medium' ? 'rgba(245, 158, 11, 0.25)' : 'rgba(255,255,255,0.05)',
                color: '#F59E0B',
              }}>
                <ShieldAlert size={18} />
              </div>
              <div>
                <div style={{ fontSize: '0.95rem', fontWeight: '800', color: subNav === 'medium' ? '#FFFFFF' : '#E2E8F0' }}>
                  Medium Transactions
                </div>
                <div style={{ fontSize: '0.68rem', color: '#FBBF24', fontWeight: '700' }}>
                  Tier 2 Dynamic Monitoring (Risk 30–59)
                </div>
              </div>
            </div>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: '900',
              padding: '3px 10px',
              borderRadius: '20px',
              background: subNav === 'medium' ? '#F59E0B' : 'rgba(245, 158, 11, 0.15)',
              color: subNav === 'medium' ? '#000' : '#FBBF24',
            }}>
              {mediumTransactions.length} Txns
            </span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            Real-time behavioral deviations, velocity anomalies, and automated dynamic monitoring tracking genuine follow-ups vs mule escalations.
          </div>
        </div>

        {/* Navigation 2: High Transactions */}
        <div
          onClick={() => handleSubNavChange('high')}
          style={{
            padding: '14px 18px',
            borderRadius: '12px',
            cursor: 'pointer',
            border: subNav === 'high' ? '1.5px solid #EF4444' : '1px solid rgba(255,255,255,0.08)',
            background: subNav === 'high'
              ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.18) 0%, rgba(185, 28, 28, 0.08) 100%)'
              : 'rgba(15, 23, 42, 0.5)',
            boxShadow: subNav === 'high' ? '0 0 20px rgba(239, 68, 68, 0.2)' : 'none',
            transition: 'all 0.2s ease',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {subNav === 'high' && (
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: 'linear-gradient(90deg, #EF4444, #F87171)' }} />
          )}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                padding: '6px',
                borderRadius: '8px',
                background: subNav === 'high' ? 'rgba(239, 68, 68, 0.25)' : 'rgba(255,255,255,0.05)',
                color: '#EF4444',
              }}>
                <AlertTriangle size={18} />
              </div>
              <div>
                <div style={{ fontSize: '0.95rem', fontWeight: '800', color: subNav === 'high' ? '#FFFFFF' : '#E2E8F0' }}>
                  High Transactions
                </div>
                <div style={{ fontSize: '0.68rem', color: '#F87171', fontWeight: '700' }}>
                  Tier 3 Mule Rings & Liens (Risk ≥ 60)
                </div>
              </div>
            </div>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: '900',
              padding: '3px 10px',
              borderRadius: '20px',
              background: subNav === 'high' ? '#EF4444' : 'rgba(239, 68, 68, 0.15)',
              color: subNav === 'high' ? '#FFF' : '#F87171',
            }}>
              {highTransactions.length} Txns
            </span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            Multi-hop mule network forensics, GATv2 neural classification, active Lien Layer holds, and admin enforcement (Release, Restrict, Freeze).
          </div>
        </div>

        {/* Topology Graph Option */}
        <div
          onClick={() => handleSubNavChange('graph')}
          style={{
            padding: '14px 18px',
            borderRadius: '12px',
            cursor: 'pointer',
            border: isGraphView ? '1.5px solid #8B5CF6' : '1px solid rgba(255,255,255,0.08)',
            background: isGraphView
              ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.18) 0%, rgba(109, 40, 217, 0.08) 100%)'
              : 'rgba(15, 23, 42, 0.5)',
            boxShadow: isGraphView ? '0 0 20px rgba(139, 92, 246, 0.18)' : 'none',
            transition: 'all 0.2s ease',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {isGraphView && (
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: 'linear-gradient(90deg, #8B5CF6, #C084FC)' }} />
          )}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                padding: '6px',
                borderRadius: '8px',
                background: isGraphView ? 'rgba(139, 92, 246, 0.25)' : 'rgba(255,255,255,0.05)',
                color: '#A78BFA',
              }}>
                <Network size={18} />
              </div>
              <div>
                <div style={{ fontSize: '0.95rem', fontWeight: '800', color: isGraphView ? '#FFFFFF' : '#E2E8F0' }}>
                  Topology Graph & Clusters
                </div>
                <div style={{ fontSize: '0.68rem', color: '#C084FC', fontWeight: '700' }}>
                  Interactive Multi-Bank Canvas
                </div>
              </div>
            </div>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: '900',
              padding: '3px 10px',
              borderRadius: '20px',
              background: isGraphView ? '#8B5CF6' : 'rgba(139, 92, 246, 0.15)',
              color: isGraphView ? '#FFF' : '#C084FC',
            }}>
              {transactions.length} Total
            </span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            Interactive graph forensics with directed edges, flow/radial layouts, and automated RL investigation decisions.
          </div>
        </div>
      </div>

      {/* Dynamic KPI Cards Based on Active Sub-Navigation */}
      {subNav === 'medium' ? (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '14px',
            marginBottom: '24px',
          }}
        >
          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #F59E0B' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>MEDIUM TRANSACTIONS</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#F59E0B', marginTop: '4px' }}>
              {mediumTransactions.length}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#FBBF24', marginTop: '2px' }}>Risk Score 30 – 59</div>
          </div>

          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #FBBF24' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>DYNAMIC MONITORING CASES</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#FBBF24', marginTop: '4px' }}>
              {monitoringCases.filter((c) => c.status === 'ACTIVE').length || mediumTransactions.length}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Active Watchlist</div>
          </div>

          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #60A5FA' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>AVG MEDIUM RISK</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#60A5FA', marginTop: '4px' }}>
              {mediumTransactions.length > 0
                ? (
                    mediumTransactions.reduce((acc, t) => acc + (t.risk_score || t.final_risk_score || 45), 0) /
                    mediumTransactions.length
                  ).toFixed(1)
                : '43.5'}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Continuous Score Baseline</div>
          </div>

          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #34D399' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>GENUINE RATIO EXPECTED</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#34D399', marginTop: '4px' }}>
              ~85%
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Non-Disruptive Holds</div>
          </div>

          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #A78BFA' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>CROSS-BANK ANOMALIES</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#A78BFA', marginTop: '4px' }}>
              {mediumTransactions.filter((t) => t.sender_bank && t.receiver_bank && t.sender_bank !== t.receiver_bank).length}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Inter-Bank Velocity</div>
          </div>
        </div>
      ) : subNav === 'high' ? (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '14px',
            marginBottom: '24px',
          }}
        >
          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #EF4444' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>HIGH & CRITICAL TXNS</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#EF4444', marginTop: '4px' }}>
              {highTransactions.length}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#F87171', marginTop: '2px' }}>Risk Score ≥ 60</div>
          </div>

          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #F97316' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>CRITICAL MULE CLUSTERS</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#F97316', marginTop: '4px' }}>
              {summaryData?.critical_networks ?? 0}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Multi-Hop Rings</div>
          </div>

          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #A78BFA' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>ACTIVE PROTECTIVE LIENS</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#A78BFA', marginTop: '4px' }}>
              {underReviewItems.length || summaryData?.networks_under_review || 0}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Controlled Action Holds</div>
          </div>

          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #EC4899' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>MULE ACCOUNTS DETECTED</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#EC4899', marginTop: '4px' }}>
              {summaryData?.mule_accounts_detected ?? 0}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>GNN Confidence ≥ 85%</div>
          </div>

          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '3px solid #10B981' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>PROTECTED LIEN VOLUME</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#10B981', marginTop: '4px' }}>
              ₹{(highTransactions.reduce((acc, t) => acc + (t.amount || 0), 0) || 450000).toLocaleString('en-IN')}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Prevented Extraction</div>
          </div>
        </div>
      ) : (
        /* All Clusters KPI Cards */
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '14px',
            marginBottom: '24px',
          }}
        >
          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>TOTAL NETWORKS</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#60A5FA', marginTop: '4px' }}>
              {summaryData?.total_networks ?? 0}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Clusters Identified</div>
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
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Behavioural Flags</div>
          </div>

          <div className="card" style={{ padding: '16px', background: 'rgba(15, 23, 42, 0.65)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '600' }}>ACTIVE LIEN HOLDS</div>
            <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#A78BFA', marginTop: '4px' }}>
              {summaryData?.networks_under_review ?? 0}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Controlled Actions</div>
          </div>
        </div>
      )}

      {/* Main Container */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* ========================================================================= */}
        {/* SECTION 1: SEGREGATED TRANSACTIONS STREAM TABLE                           */}
        {/* ========================================================================= */}
        <div className="card" style={{ padding: '20px', background: 'rgba(10, 15, 25, 0.85)', order: isGraphView ? 2 : 1 }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '14px',
              flexWrap: 'wrap',
              gap: '8px',
            }}
          >
            <div>
              <h3 style={{ fontSize: '0.98rem', fontWeight: '800', color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '8px' }}>
                {subNav === 'medium' ? (
                  <ShieldAlert size={17} color="#F59E0B" />
                ) : subNav === 'high' ? (
                  <AlertTriangle size={17} color="#EF4444" />
                ) : (
                  <Activity size={16} color="#38BDF8" />
                )}
                <span>
                  {subNav === 'medium'
                    ? 'Medium Risk Monitored Transactions'
                    : subNav === 'high'
                    ? 'High Risk & Mule Ring Transactions'
                    : 'Live Coordinated Transactions'}
                </span>
                <span
                  style={{
                    fontSize: '0.7rem',
                    padding: '2px 7px',
                    borderRadius: '4px',
                    background:
                      subNav === 'medium'
                        ? 'rgba(245, 158, 11, 0.18)'
                        : subNav === 'high'
                        ? 'rgba(239, 68, 68, 0.18)'
                        : 'rgba(56, 189, 248, 0.15)',
                    color: subNav === 'medium' ? '#FBBF24' : subNav === 'high' ? '#F87171' : '#38BDF8',
                    border:
                      subNav === 'medium'
                        ? '1px solid rgba(245, 158, 11, 0.35)'
                        : subNav === 'high'
                        ? '1px solid rgba(239, 68, 68, 0.35)'
                        : '1px solid rgba(56, 189, 248, 0.3)',
                  }}
                >
                  {displayedTransactions.length} {subNav === 'medium' ? 'Monitored' : subNav === 'high' ? 'High / Liens' : 'Active'} Txns
                </span>
              </h3>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {subNav === 'medium'
                  ? 'Showing transactions with risk scores 30–59 undergoing automated dynamic behavioral monitoring.'
                  : subNav === 'high'
                  ? 'Showing high-risk transactions (≥60) with GATv2 neural mule detection and protective lien holds.'
                  : 'Click any transaction row below to display its network graph directly underneath.'}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <button
                onClick={() => {
                  document.getElementById('graph-forensics-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }}
                style={{
                  padding: '5px 12px',
                  borderRadius: '6px',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                  background: 'rgba(56, 189, 248, 0.12)',
                  color: '#38BDF8',
                  fontSize: '0.74rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease',
                }}
                title="View interactive graph canvas"
              >
                <Network size={13} />
                <span>View Graph Canvas</span>
              </button>

              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {selectedTxId ? (
                  <span style={{ color: subNav === 'medium' ? '#FBBF24' : subNav === 'high' ? '#F87171' : '#38BDF8', fontWeight: '700' }}>
                    Selected: <code>{selectedTxId}</code>
                  </span>
                ) : (
                  'Select a transaction to inspect graph'
                )}
              </div>
            </div>
          </div>

          <div style={{ overflowX: 'auto', maxHeight: '280px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
              <thead style={{ position: 'sticky', top: 0, background: '#0A0F1A', zIndex: 5 }}>
                <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '8px 10px' }}>TRANSACTION ID</th>
                  <th style={{ padding: '8px 10px' }}>TIMESTAMP</th>
                  <th style={{ padding: '8px 10px' }}>SENDER</th>
                  <th style={{ padding: '8px 10px' }}>RECEIVER</th>
                  <th style={{ padding: '8px 10px' }}>AMOUNT</th>
                  <th style={{ padding: '8px 10px' }}>XGB RISK</th>
                  <th style={{ padding: '8px 10px' }}>GNN MULE %</th>
                  <th style={{ padding: '8px 10px' }}>DECISION</th>
                  <th style={{ padding: '8px 10px' }}>STATUS</th>
                  <th style={{ padding: '8px 10px', textAlign: 'right' }}>INVESTIGATE</th>
                </tr>
              </thead>
              <tbody>
                {displayedTransactions.length === 0 ? (
                  <tr>
                    <td colSpan="10" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                      <Activity size={28} style={{ margin: '0 auto 8px', opacity: 0.4, color: '#60A5FA' }} />
                      <div>
                        {subNav === 'medium'
                          ? 'No medium-risk transactions currently detected.'
                          : subNav === 'high'
                          ? 'No high-risk mule ring transactions currently detected. Click "⚡ Simulate Multi-Mule Flow" to generate live high-risk flows.'
                          : 'Streaming live transactions from backend...'}
                      </div>
                    </td>
                  </tr>
                ) : (
                  displayedTransactions.map((tx) => {
                    const isSelected = selectedTxId === tx.transaction_id;
                    const risk = tx.risk_score || tx.final_risk_score || 0;
                    const isCritical = risk >= 80;
                    const isHigh = risk >= 60;
                    const isMed = risk >= 30;

                    let statusBg = 'rgba(16, 185, 129, 0.15)';
                    let statusColor = '#34D399';
                    if (tx.status === 'FROZEN') {
                      statusBg = 'rgba(239, 68, 68, 0.25)';
                      statusColor = '#EF4444';
                    } else if (tx.status === 'RESTRICTED') {
                      statusBg = 'rgba(249, 115, 22, 0.25)';
                      statusColor = '#F97316';
                    } else if (tx.status === 'UNDER_REVIEW') {
                      statusBg = 'rgba(167, 139, 250, 0.25)';
                      statusColor = '#C084FC';
                    } else if (tx.status === 'MONITORING') {
                      statusBg = 'rgba(245, 158, 11, 0.25)';
                      statusColor = '#F59E0B';
                    }

                    return (
                      <tr
                        key={tx.transaction_id}
                        onClick={() => {
                          setSelectedTxId(tx.transaction_id);
                          setSelectedTx(tx);
                          loadTransactionGraph(tx.transaction_id);
                          document.getElementById('graph-forensics-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }}
                        style={{
                          borderBottom: '1px solid rgba(255,255,255,0.05)',
                          background: isSelected ? 'rgba(59, 130, 246, 0.18)' : 'transparent',
                          cursor: 'pointer',
                          transition: 'background 0.12s ease',
                          outline: isSelected ? '1px solid rgba(59, 130, 246, 0.4)' : 'none',
                        }}
                      >
                        <td style={{ padding: '8px 10px', fontWeight: '800', color: isSelected ? '#38BDF8' : '#93C5FD' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            {isSelected && <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#38BDF8' }} />}
                            <code>{tx.transaction_id}</code>
                          </div>
                        </td>
                        <td style={{ padding: '8px 10px', color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                          {tx.timestamp || tx.transaction_timestamp
                            ? new Date(tx.timestamp || tx.transaction_timestamp).toLocaleTimeString('en-IN')
                            : 'Live'}
                        </td>
                        <td style={{ padding: '8px 10px' }}>
                          <span
                            style={{
                              fontSize: '0.65rem',
                              padding: '1px 5px',
                              borderRadius: '3px',
                              background: 'rgba(255,255,255,0.07)',
                              marginRight: '6px',
                              fontWeight: '800',
                              color: tx.sender_bank === 'SBI' ? '#60A5FA' : tx.sender_bank === 'AXIS' ? '#EC4899' : '#FBBF24',
                            }}
                          >
                            {tx.sender_bank}
                          </span>
                          <span style={{ color: '#E2E8F0', fontWeight: '600' }}>
                            {tx.sender_account_id || tx.sender_account || 'SRC'}
                          </span>
                        </td>
                        <td style={{ padding: '8px 10px' }}>
                          <span
                            style={{
                              fontSize: '0.65rem',
                              padding: '1px 5px',
                              borderRadius: '3px',
                              background: 'rgba(255,255,255,0.07)',
                              marginRight: '6px',
                              fontWeight: '800',
                              color: tx.receiver_bank === 'SBI' ? '#60A5FA' : tx.receiver_bank === 'AXIS' ? '#EC4899' : '#FBBF24',
                            }}
                          >
                            {tx.receiver_bank}
                          </span>
                          <span style={{ color: '#E2E8F0', fontWeight: '600' }}>
                            {tx.receiver_account_id || tx.receiver_account || 'RCV'}
                          </span>
                        </td>
                        <td style={{ padding: '8px 10px', fontWeight: '800', color: '#F1F5F9' }}>
                          ₹{(tx.amount || 0).toLocaleString()}
                        </td>
                        <td
                          style={{
                            padding: '8px 10px',
                            fontWeight: '800',
                            color: isCritical ? '#EF4444' : isHigh ? '#F97316' : isMed ? '#F59E0B' : '#10B981',
                          }}
                        >
                          {risk.toFixed(1)}
                        </td>
                        <td style={{ padding: '8px 10px' }}>
                          {tx.gnn_mule_probability ? (
                            <span
                              style={{
                                padding: '1px 6px',
                                borderRadius: '4px',
                                fontSize: '0.68rem',
                                fontWeight: '800',
                                background: tx.gnn_mule_probability >= 0.35 ? 'rgba(244, 63, 94, 0.2)' : 'rgba(255,255,255,0.05)',
                                color: tx.gnn_mule_probability >= 0.35 ? '#FDA4AF' : 'var(--text-muted)',
                              }}
                            >
                              {(tx.gnn_mule_probability * 100).toFixed(0)}%
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>-</span>
                          )}
                        </td>
                        <td style={{ padding: '8px 10px', fontWeight: '700', color: '#E2E8F0' }}>
                          {tx.decision || 'ALLOW'}
                        </td>
                        <td style={{ padding: '8px 10px' }}>
                          <span
                            style={{
                              padding: '2px 7px',
                              borderRadius: '4px',
                              fontSize: '0.68rem',
                              fontWeight: '800',
                              background: statusBg,
                              color: statusColor,
                            }}
                          >
                            {tx.status || 'COMPLETED'}
                          </span>
                        </td>
                        <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedTxId(tx.transaction_id);
                              setSelectedTx(tx);
                              loadTransactionGraph(tx.transaction_id);
                              document.getElementById('graph-forensics-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }}
                            style={{
                              padding: '4px 10px',
                              borderRadius: '5px',
                              border: isSelected ? '1px solid #38BDF8' : '1px solid rgba(59, 130, 246, 0.4)',
                              background: isSelected ? 'rgba(59, 130, 246, 0.3)' : 'rgba(59, 130, 246, 0.12)',
                              color: isSelected ? '#38BDF8' : '#93C5FD',
                              fontSize: '0.72rem',
                              fontWeight: '800',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px',
                            }}
                          >
                            <Search size={11} />
                            <span>{isSelected ? 'Investigating (Active)' : 'Investigate'}</span>
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

        {/* ========================================================================= */}
        {/* SECTION 2: INTERACTIVE GRAPH FORENSICS (DIRECTLY BELOW THE TRANSACTION)   */}
        {/* ========================================================================= */}
        <div
          id="graph-forensics-section"
          className="card"
          style={{
            padding: '20px',
            background: 'rgba(10, 15, 25, 0.95)',
            border: '1px solid rgba(59, 130, 246, 0.4)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
            order: isGraphView ? 1 : 2,
          }}
        >
          {/* Active Transaction Banner directly at the top of the graph */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px',
              flexWrap: 'wrap',
              gap: '12px',
              paddingBottom: '14px',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: '900',
                    padding: '3px 9px',
                    borderRadius: '5px',
                    background: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)',
                    color: '#FFFFFF',
                    letterSpacing: '0.02em',
                  }}
                >
                  ACTIVE TRANSACTION GRAPH
                </span>

                <h3 style={{ fontSize: '1.05rem', fontWeight: '800', color: '#FFFFFF', margin: 0 }}>
                  {selectedTx ? (
                    <span>
                      <code>{selectedTx.transaction_id}</code> &nbsp;
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        ({selectedTx.sender_account_id || selectedTx.sender_account} ──► {selectedTx.receiver_account_id || selectedTx.receiver_account})
                      </span>
                    </span>
                  ) : (
                    <span>Network Topology Forensics</span>
                  )}
                </h3>

                {networkDetail && (
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: '5px',
                      fontSize: '0.7rem',
                      fontWeight: '800',
                      background:
                        networkDetail.status === 'FROZEN'
                          ? 'rgba(239, 68, 68, 0.25)'
                          : networkDetail.status === 'RESTRICTED'
                          ? 'rgba(249, 115, 22, 0.25)'
                          : networkDetail.status === 'UNDER_REVIEW'
                          ? 'rgba(167, 139, 250, 0.25)'
                          : 'rgba(245, 158, 11, 0.25)',
                      color:
                        networkDetail.status === 'FROZEN'
                          ? '#EF4444'
                          : networkDetail.status === 'RESTRICTED'
                          ? '#F97316'
                          : networkDetail.status === 'UNDER_REVIEW'
                          ? '#C084FC'
                          : '#F59E0B',
                    }}
                  >
                    {networkDetail.status || 'MONITORING'}
                  </span>
                )}
              </div>

              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Cluster: <strong style={{ color: '#93C5FD' }}>{networkDetail?.network_id || 'LOCAL-SUBGRAPH'}</strong>
                &nbsp;•&nbsp; Pattern: <strong style={{ color: '#F1F5F9' }}>{networkDetail?.primary_pattern || 'DIRECT_TRANSFER'}</strong>
                &nbsp;•&nbsp; Cluster Risk Score:{' '}
                <strong style={{ color: (networkDetail?.risk_score || 0) >= 70 ? '#EF4444' : '#F59E0B' }}>
                  {networkDetail?.risk_score || 45.0}
                </strong>
                &nbsp;•&nbsp; Connected Nodes: <strong style={{ color: '#E2E8F0' }}>{nodes.length}</strong>
                &nbsp;•&nbsp; Flow Edges: <strong style={{ color: '#E2E8F0' }}>{edges.length}</strong>
              </div>
            </div>

            {/* Graph Toolbar & Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              {/* Layout Switcher */}
              <div style={{ display: 'flex', background: 'rgba(255,255,255,0.06)', padding: '3px', borderRadius: '6px' }}>
                <button
                  onClick={() => setLayoutMode('FLOW')}
                  style={{
                    padding: '3px 8px',
                    borderRadius: '4px',
                    border: 'none',
                    fontSize: '0.68rem',
                    fontWeight: '800',
                    cursor: 'pointer',
                    background: layoutMode === 'FLOW' ? '#3B82F6' : 'transparent',
                    color: layoutMode === 'FLOW' ? '#fff' : 'var(--text-muted)',
                  }}
                  title="Directed Left-to-Right Flow (Source -> Mules -> Sink)"
                >
                  Flow Layout
                </button>
                <button
                  onClick={() => setLayoutMode('RADIAL')}
                  style={{
                    padding: '3px 8px',
                    borderRadius: '4px',
                    border: 'none',
                    fontSize: '0.68rem',
                    fontWeight: '800',
                    cursor: 'pointer',
                    background: layoutMode === 'RADIAL' ? '#3B82F6' : 'transparent',
                    color: layoutMode === 'RADIAL' ? '#fff' : 'var(--text-muted)',
                  }}
                  title="Radial Circular Layout"
                >
                  Radial Layout
                </button>
              </div>

              {/* Bank Filter */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '3px', borderRadius: '6px' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', paddingLeft: '4px' }}>Bank:</span>
                {['ALL', 'SBI', 'AXIS', 'IOB'].map((b) => (
                  <button
                    key={b}
                    onClick={() => setBankFilter(b)}
                    style={{
                      padding: '2px 7px',
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

              {/* Risk Filter */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '3px', borderRadius: '6px' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', paddingLeft: '4px' }}>Risk:</span>
                {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'].map((r) => (
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

              {/* Manual Reload of Current Graph */}
              <button
                onClick={() => {
                  if (selectedTxId) loadTransactionGraph(selectedTxId, false);
                  else if (selectedNetwork) loadNetworkDetail(selectedNetwork, false);
                }}
                title="Reload current forensic graph"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '5px 10px',
                  borderRadius: '5px',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  background: 'rgba(59, 130, 246, 0.15)',
                  color: '#93C5FD',
                  fontSize: '0.7rem',
                  fontWeight: '800',
                  cursor: 'pointer',
                }}
              >
                <RefreshCw size={11} />
                <span>Refresh Graph</span>
              </button>

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
                  <ZoomIn size={13} />
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
                  <ZoomOut size={13} />
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
                  <Maximize2 size={13} />
                </button>
              </div>
            </div>
          </div>

          {/* Canvas Container + Node Inspector Sidebar */}
          <div style={{ display: 'grid', gridTemplateColumns: selectedNode ? '1fr 340px' : '1fr', gap: '16px' }}>
            {/* Interactive SVG Canvas */}
            <div
              style={{
                background: '#070B14',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '10px',
                height: '580px',
                overflow: 'hidden',
                position: 'relative',
                cursor: isDraggingRef.current ? 'grabbing' : 'grab',
                backgroundImage: 'radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px)',
                backgroundSize: '24px 24px',
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
              {nodes.length === 0 ? (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    color: 'var(--text-muted)',
                  }}
                >
                  <Network size={42} style={{ opacity: 0.3, marginBottom: '12px', color: '#38BDF8' }} />
                  <div style={{ fontWeight: '700', color: '#E2E8F0', fontSize: '0.95rem', marginBottom: '6px' }}>
                    Awaiting Transaction Selection
                  </div>
                  <div style={{ fontSize: '0.8rem', maxWidth: '380px', textAlign: 'center' }}>
                    Select any transaction row above or trigger a live simulation to render its connected multi-bank graph topology.
                  </div>
                </div>
              ) : (
                <svg
                  width="100%"
                  height="100%"
                  viewBox={`0 0 ${flowSvgWidth} ${flowSvgHeight}`}
                  style={{
                    transform: `scale(${zoomLevel}) translate(${panOffset.x}px, ${panOffset.y}px)`,
                    transformOrigin: 'center center',
                    transition: isDraggingRef.current ? 'none' : 'transform 0.1s ease',
                  }}
                >
                  {/* Arrow marker definition */}
                  <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748B" />
                    </marker>
                    <marker id="arrow-active" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#38BDF8" />
                    </marker>
                    <marker id="arrow-halted" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#EF4444" />
                    </marker>
                    <marker id="arrow-review" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#C084FC" />
                    </marker>
                  </defs>

                  {/* Directed Curved Edges with Anti-Collision Routing */}
                  {(() => {
                    const pairCounts = {};
                    edges.forEach((e) => {
                      const key = [e.source, e.target].sort().join('---');
                      pairCounts[key] = (pairCounts[key] || 0) + 1;
                    });
                    const pairSeen = {};
                    const placedBadges = [];

                    return edges.map((e, idx) => {
                      const src = nodePositions[e.source];
                      const tgt = nodePositions[e.target];
                      if (!src || !tgt) return null;

                      const isConnectedToSelected =
                        selectedNode && (e.source === selectedNode.account_id || e.target === selectedNode.account_id);
                      const isFocusTx = selectedTx && (e.transaction_id === selectedTx.transaction_id || (e.source === selectedTx.sender_account_id && e.target === selectedTx.receiver_account_id));

                      const key = [e.source, e.target].sort().join('---');
                      const pairIndex = pairSeen[key] || 0;
                      pairSeen[key] = pairIndex + 1;
                      const isReverse = e.source > e.target;

                      const dx = tgt.x - src.x;
                      const dy = tgt.y - src.y;
                      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                      const nx = -dy / dist;
                      const ny = dx / dist;

                      const startX = src.x + (dx / dist) * 22;
                      const startY = src.y + (dy / dist) * 22;
                      const endX = tgt.x - (dx / dist) * 26;
                      const endY = tgt.y - (dy / dist) * 26;

                      const isHalted = Boolean(e.flow_stopped || e.status === 'UNDER_REVIEW' || e.status === 'RESTRICTED' || e.status === 'FROZEN');
                      const isFrozenOrRestricted = e.status === 'RESTRICTED' || e.status === 'FROZEN';
                      const isUnderReview = e.status === 'UNDER_REVIEW';

                      const colSpan = Math.abs((src.colIdx ?? 0) - (tgt.colIdx ?? 2));
                      let curveOffset = 0;

                      if (layoutMode === 'FLOW') {
                        if (colSpan >= 2) {
                          const avgY = (src.y + tgt.y) / 2;
                          const archSign = avgY < flowSvgHeight / 2 ? -1 : 1;
                          curveOffset = archSign * (85 + pairIndex * 28);
                        } else if (pairCounts[key] > 1) {
                          curveOffset = (pairIndex % 2 === 0 ? 1 : -1) * (26 + Math.floor(pairIndex / 2) * 24);
                          if (isReverse) curveOffset = -curveOffset;
                        } else {
                          curveOffset = (idx % 2 === 0 ? 1 : -1) * 18;
                        }
                      } else {
                        if (pairCounts[key] > 1) {
                          curveOffset = (pairIndex % 2 === 0 ? 1 : -1) * (24 + Math.floor(pairIndex / 2) * 22);
                        } else {
                          curveOffset = (idx % 2 === 0 ? 1 : -1) * 16;
                        }
                      }

                      const ctrlX = (startX + endX) / 2 + nx * curveOffset;
                      const ctrlY = (startY + endY) / 2 + ny * curveOffset;
                      const pathD = `M ${startX} ${startY} Q ${ctrlX} ${ctrlY} ${endX} ${endY}`;

                      let t = 0.5;
                      let bx = Math.pow(1 - t, 2) * startX + 2 * (1 - t) * t * ctrlX + Math.pow(t, 2) * endX;
                      let by = Math.pow(1 - t, 2) * startY + 2 * (1 - t) * t * ctrlY + Math.pow(t, 2) * endY;

                      for (const n of nodes) {
                        const np = nodePositions[n.account_id];
                        if (np) {
                          if (Math.abs(np.x - bx) < 64 && Math.abs(np.y - by) < 52) {
                            t = (src.colIdx ?? 0) <= (tgt.colIdx ?? 0) ? 0.30 : 0.70;
                            bx = Math.pow(1 - t, 2) * startX + 2 * (1 - t) * t * ctrlX + Math.pow(t, 2) * endX;
                            by = Math.pow(1 - t, 2) * startY + 2 * (1 - t) * t * ctrlY + Math.pow(t, 2) * endY;
                            break;
                          }
                        }
                      }

                      for (const pb of placedBadges) {
                        if (Math.abs(pb.x - bx) < 78 && Math.abs(pb.y - by) < 24) {
                          by += (by >= pb.y ? 24 : -24);
                        }
                      }
                      placedBadges.push({ x: bx, y: by });

                      const strokeColor = isFrozenOrRestricted
                        ? '#EF4444'
                        : isUnderReview
                        ? '#C084FC'
                        : isFocusTx
                        ? '#38BDF8'
                        : isConnectedToSelected
                        ? '#60A5FA'
                        : '#334155';

                      const markerEndUrl = isFrozenOrRestricted
                        ? 'url(#arrow-halted)'
                        : isUnderReview
                        ? 'url(#arrow-review)'
                        : isFocusTx || isConnectedToSelected
                        ? 'url(#arrow-active)'
                        : 'url(#arrow)';

                      return (
                        <g key={idx}>
                          <path
                            d={pathD}
                            fill="none"
                            stroke={strokeColor}
                            strokeWidth={isFocusTx ? 3.0 : isHalted ? 2.5 : isConnectedToSelected ? 2.5 : 1.8}
                            strokeDasharray={isHalted ? '6,4' : e.is_cross_bank ? '5,4' : 'none'}
                            markerEnd={markerEndUrl}
                          />

                          {/* Animated Flow Pulse if active */}
                          {!isHalted && (
                            <path
                              d={pathD}
                              fill="none"
                              stroke={isFocusTx ? '#F43F5E' : '#38BDF8'}
                              strokeWidth={isFocusTx ? 3.5 : 2}
                              strokeDasharray="6,6"
                              className="flow-line-pulse"
                              opacity="0.9"
                              pointerEvents="none"
                            />
                          )}

                          {/* Amount Chip on Edge with Protective Backdrop */}
                          <g transform={`translate(${bx}, ${by})`}>
                            <rect
                              x="-40"
                              y="-10"
                              width="80"
                              height="20"
                              rx="5"
                              fill={isFrozenOrRestricted ? 'rgba(30, 10, 15, 0.96)' : isUnderReview ? 'rgba(25, 15, 35, 0.96)' : 'rgba(8, 14, 26, 0.96)'}
                              stroke={isFocusTx ? '#38BDF8' : isFrozenOrRestricted ? '#EF4444' : isUnderReview ? '#C084FC' : 'rgba(255,255,255,0.12)'}
                              strokeWidth={isFocusTx ? 1.8 : 1}
                            />
                            <text
                              x="0"
                              y="4"
                              textAnchor="middle"
                              fill={isFrozenOrRestricted ? '#FCA5A5' : isUnderReview ? '#E9D5FF' : isFocusTx ? '#38BDF8' : '#CBD5E1'}
                              fontSize="9"
                              fontWeight="800"
                              fontFamily="JetBrains Mono, monospace"
                            >
                              ₹{(e.amount || 0).toLocaleString()} {isHalted ? (isFrozenOrRestricted ? ' [HALT]' : ' [LIEN]') : ''}
                            </text>
                          </g>
                        </g>
                      );
                    });
                  })()}

                  {/* Nodes with Protective Label Plates */}
                  {nodes.map((node) => {
                    const pos = nodePositions[node.account_id];
                    if (!pos) return null;
                    const isSelected = selectedNode?.account_id === node.account_id;
                    const color = CLASSIFICATION_COLORS[node.classification] || '#6B7280';
                    const roleColor = ROLE_COLORS[node.network_role] || '#6B7280';
                    const isSourceOrDestOfActiveTx = selectedTx && (node.account_id === selectedTx.sender_account_id || node.account_id === selectedTx.receiver_account_id);

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
                          <circle r="25" fill="none" stroke={color} strokeWidth="2" className="node-pulse-halo" />
                        )}

                        {/* Glow halo for selected or active transaction node */}
                        {(isSelected || isSourceOrDestOfActiveTx) && (
                          <circle r="22" fill={isSelected ? '#38BDF8' : color} opacity="0.3" />
                        )}

                        {/* Outer node circle */}
                        <circle
                          r="16"
                          fill="#0F172A"
                          stroke={isSelected ? '#38BDF8' : isSourceOrDestOfActiveTx ? '#F43F5E' : color}
                          strokeWidth={isSelected ? 3.5 : isSourceOrDestOfActiveTx ? 2.8 : 2}
                        />

                        {/* Inner role core */}
                        <circle r="7" fill={roleColor} />

                        {/* Live GNN Confidence Pill above Node */}
                        {node.gnn_mule_probability >= 0.35 && (
                          <g transform="translate(0, -24)">
                            <rect x="-26" y="-7" width="52" height="14" rx="3" fill="#831843" stroke="#F43F5E" strokeWidth="0.8" />
                            <text x="0" y="3" textAnchor="middle" fill="#FDA4AF" fontSize="7.5" fontWeight="900">
                              GNN {(node.gnn_mule_probability * 100).toFixed(0)}%
                            </text>
                          </g>
                        )}

                        {/* Protective Label Plate (Eliminates text collisions) */}
                        <rect
                          x="-46"
                          y="18"
                          width="92"
                          height="27"
                          rx="5"
                          fill="rgba(8, 14, 26, 0.96)"
                          stroke="rgba(255, 255, 255, 0.12)"
                          strokeWidth="0.8"
                        />

                        {/* Account label */}
                        <text y="30" textAnchor="middle" fill={isSelected ? '#38BDF8' : '#F8FAFC'} fontSize="9.5" fontWeight="700" fontFamily="JetBrains Mono, monospace">
                          {node.account_id}
                        </text>

                        {/* Role tag */}
                        <text y="41" textAnchor="middle" fill={roleColor} fontSize="8" fontWeight="800">
                          {node.network_role}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              )}

              {/* Graph Legend Overlay */}
              <div
                style={{
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
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#EF4444' }} />
                  <span style={{ color: '#E2E8F0' }}>Mule Hub / Target</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B' }} />
                  <span style={{ color: '#E2E8F0' }}>Suspicious Relay</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3B82F6' }} />
                  <span style={{ color: '#E2E8F0' }}>Source</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }} />
                  <span style={{ color: '#E2E8F0' }}>Sink</span>
                </div>
                <span style={{ color: 'var(--text-muted)' }}>• Click any node to inspect all 13 attributes</span>
              </div>
            </div>

            {/* Node Details Inspector Sidebar */}
            {selectedNode && (
              <div
                style={{
                  background: 'rgba(12, 18, 30, 0.95)',
                  border: '1px solid rgba(59, 130, 246, 0.35)',
                  borderRadius: '10px',
                  padding: '18px',
                  overflowY: 'auto',
                  maxHeight: '520px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ fontWeight: '800', fontSize: '0.95rem', color: '#FFFFFF' }}>Account Inspector</div>
                  <button
                    onClick={() => setSelectedNode(null)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  >
                    <X size={16} />
                  </button>
                </div>

                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '1.05rem', fontWeight: '900', color: '#93C5FD' }}>{selectedNode.account_id}</div>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    Bank: <strong style={{ color: '#E2E8F0' }}>{selectedNode.bank}</strong> &nbsp;•&nbsp; Role:{' '}
                    <strong style={{ color: ROLE_COLORS[selectedNode.network_role] }}>{selectedNode.network_role}</strong>
                  </div>
                </div>

                {/* 13 Attributes Grid */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.74rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Classification:</span>
                    <strong style={{ color: CLASSIFICATION_COLORS[selectedNode.classification] }}>{selectedNode.classification}</strong>
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
                    <strong style={{ color: '#EC4899' }}>{(selectedNode.gnn_mule_probability * 100).toFixed(1)}%</strong>
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
                    <strong style={{ color: selectedNode.fan_in ? '#EF4444' : '#10B981' }}>{selectedNode.fan_in ? 'DETECTED' : 'None'}</strong>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 8px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Fan-Out Pattern:</span>
                    <strong style={{ color: selectedNode.fan_out ? '#EF4444' : '#10B981' }}>{selectedNode.fan_out ? 'DETECTED' : 'None'}</strong>
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

                {/* Connected Accounts */}
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

                {/* Direct Enforcement Actions */}
                <div style={{ marginTop: '14px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '10px' }}>
                  <div style={{ fontSize: '0.72rem', fontWeight: '800', color: '#60A5FA', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Lock size={12} />
                    <span>Enforce on Account: {selectedNode.account_id}</span>
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
                      ❄️ FREEZE
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

                {/* Transaction Admin Action on Trigger Tx */}
                {networkDetail?.trigger_transaction_id && (
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '10px' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: '700', color: '#94A3B8', marginBottom: '8px' }}>
                      Txn Enforcement ({networkDetail.trigger_transaction_id}):
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
                        RELEASE
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
                )}
              </div>
            )}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* SECTION 3: CONDITIONAL CATALOG TABLE BASED ON ACTIVE NAVIGATION            */}
        {/* ========================================================================= */}
        {subNav === 'medium' ? (
          <div className="card" style={{ padding: '20px', background: 'rgba(10, 15, 25, 0.85)', order: 3 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h3 style={{ fontSize: '0.98rem', fontWeight: '800', color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={16} color="#F59E0B" />
                  <span>Dynamic Behavioral Monitoring Cases (Tier 2 Watchlist)</span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      padding: '2px 7px',
                      borderRadius: '4px',
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: '#FBBF24',
                      border: '1px solid rgba(245, 158, 11, 0.35)',
                    }}
                  >
                    {effectiveMonitoringCases.length} Active Cases
                  </span>
                </h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Accounts exhibiting anomalous velocity, balance drain, or cross-bank bursts being monitored dynamically for rapid forwarding.
                </div>
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Click any case to inspect its transaction graph and behavioural baseline
              </span>
            </div>

            <div style={{ overflowX: 'auto', maxHeight: '340px', overflowY: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                <thead style={{ position: 'sticky', top: 0, background: '#0A0F1A', zIndex: 5 }}>
                  <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px' }}>CASE ID</th>
                    <th style={{ padding: '10px' }}>ACCOUNT</th>
                    <th style={{ padding: '10px' }}>COUNTERPARTY</th>
                    <th style={{ padding: '10px' }}>AMOUNT</th>
                    <th style={{ padding: '10px' }}>INITIAL RISK</th>
                    <th style={{ padding: '10px' }}>MONITORING REASON</th>
                    <th style={{ padding: '10px' }}>FOLLOW-UPS</th>
                    <th style={{ padding: '10px' }}>STATUS</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>INVESTIGATE</th>
                  </tr>
                </thead>
                <tbody>
                  {effectiveMonitoringCases.length === 0 ? (
                    <tr>
                      <td colSpan="9" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                        <ShieldAlert size={28} style={{ margin: '0 auto 8px', opacity: 0.4, color: '#F59E0B' }} />
                        <div style={{ fontWeight: '700', color: '#E2E8F0' }}>No Active Dynamic Monitoring Cases</div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                          Cases populate automatically when transactions score in the 30–59 risk bracket.
                        </div>
                      </td>
                    </tr>
                  ) : (
                    effectiveMonitoringCases.map((c) => {
                      const isSelected = selectedTxId === c.transaction_id;
                      return (
                        <tr
                          key={c.case_id || c.id}
                          onClick={() => {
                            if (c.transaction_id) {
                              setSelectedTxId(c.transaction_id);
                              loadTransactionGraph(c.transaction_id);
                              document.getElementById('graph-forensics-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }
                          }}
                          style={{
                            borderBottom: '1px solid rgba(255,255,255,0.05)',
                            background: isSelected ? 'rgba(245, 158, 11, 0.15)' : 'transparent',
                            cursor: 'pointer',
                            transition: 'background 0.15s ease',
                          }}
                        >
                          <td style={{ padding: '10px', fontWeight: '800', color: '#FBBF24' }}>
                            <code>{c.case_id || `MON-${c.id}`}</code>
                          </td>
                          <td style={{ padding: '10px' }}>
                            <span
                              style={{
                                fontSize: '0.65rem',
                                padding: '1px 5px',
                                borderRadius: '3px',
                                background: 'rgba(255,255,255,0.06)',
                                marginRight: '6px',
                                fontWeight: '800',
                                color: c.bank === 'SBI' ? '#60A5FA' : c.bank === 'AXIS' ? '#EC4899' : '#FBBF24',
                              }}
                            >
                              {c.bank}
                            </span>
                            <span style={{ color: '#E2E8F0', fontWeight: '600' }}>{c.account_id}</span>
                          </td>
                          <td style={{ padding: '10px', color: '#CBD5E1' }}>
                            {c.counterparty_account_id || '—'}
                          </td>
                          <td style={{ padding: '10px', fontWeight: '700', color: '#E2E8F0' }}>
                            ₹{(c.amount || 0).toLocaleString('en-IN')}
                          </td>
                          <td style={{ padding: '10px', fontWeight: '800', color: '#F59E0B' }}>
                            {c.initial_risk_score}
                          </td>
                          <td
                            style={{
                              padding: '10px',
                              color: '#94A3B8',
                              maxWidth: '260px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                            title={c.monitoring_reason}
                          >
                            {c.monitoring_reason || 'Velocity surge / anomaly'}
                          </td>
                          <td style={{ padding: '10px', color: '#E2E8F0', fontWeight: '600' }}>
                            {c.follow_up_transaction_count || 0}
                          </td>
                          <td style={{ padding: '10px' }}>
                            <span
                              style={{
                                padding: '2px 8px',
                                borderRadius: '5px',
                                fontSize: '0.7rem',
                                fontWeight: '800',
                                background: c.status === 'RESOLVED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                                color: c.status === 'RESOLVED' ? '#34D399' : '#F59E0B',
                              }}
                            >
                              {c.status || 'ACTIVE'}
                            </span>
                          </td>
                          <td style={{ padding: '10px', textAlign: 'right' }}>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                if (c.transaction_id) {
                                  setSelectedTxId(c.transaction_id);
                                  loadTransactionGraph(c.transaction_id);
                                  document.getElementById('graph-forensics-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                }
                              }}
                              style={{
                                padding: '4px 10px',
                                borderRadius: '5px',
                                border: isSelected ? '1px solid #F59E0B' : '1px solid rgba(245, 158, 11, 0.4)',
                                background: isSelected ? 'rgba(245, 158, 11, 0.3)' : 'rgba(245, 158, 11, 0.15)',
                                color: '#FBBF24',
                                fontSize: '0.72rem',
                                fontWeight: '800',
                                cursor: 'pointer',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '5px',
                              }}
                            >
                              <Search size={11} />
                              <span>{isSelected ? 'Investigating (Active)' : 'Investigate'}</span>
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
        ) : (
          <div className="card" style={{ padding: '20px', background: 'rgba(10, 15, 25, 0.8)', order: 3 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#FFFFFF' }}>
                Detected Mule Network Clusters
              </h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Click any cluster row to focus the interactive graph above on that cluster
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
                      <td colSpan="10" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                        <Network size={32} style={{ margin: '0 auto 10px', opacity: 0.4, color: '#60A5FA' }} />
                        <div style={{ fontSize: '0.9rem', fontWeight: '700', color: '#E2E8F0' }}>No Mule Networks Tracked Yet</div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                          Clusters appear dynamically as live transactions stream through the ADSL Central Engine.
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
                          onClick={() => {
                            loadNetworkDetail(net.network_id);
                            document.getElementById('graph-forensics-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                          }}
                          style={{
                            borderBottom: '1px solid rgba(255,255,255,0.05)',
                            background: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                            cursor: 'pointer',
                            transition: 'background 0.15s ease',
                          }}
                        >
                          <td style={{ padding: '10px', fontWeight: '800', color: '#93C5FD' }}>{net.network_id}</td>
                          <td style={{ padding: '10px', fontWeight: '800', color: isCritical ? '#EF4444' : '#F59E0B' }}>
                            {net.risk_score}
                          </td>
                          <td style={{ padding: '10px' }}>
                            <span
                              style={{
                                padding: '2px 8px',
                                borderRadius: '5px',
                                fontSize: '0.7rem',
                                fontWeight: '800',
                                background: isCritical ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                                color: isCritical ? '#EF4444' : '#F59E0B',
                              }}
                            >
                              {net.risk_level}
                            </span>
                          </td>
                          <td style={{ padding: '10px', fontWeight: '700', color: '#F87171' }}>{net.mule_accounts}</td>
                          <td style={{ padding: '10px', color: '#FBBF24' }}>{net.suspicious_accounts}</td>
                          <td style={{ padding: '10px', color: '#E2E8F0' }}>{net.total_accounts}</td>
                          <td style={{ padding: '10px' }}>
                            <div style={{ display: 'flex', gap: '4px' }}>
                              {(net.banks_involved || []).map((b) => (
                                <span
                                  key={b}
                                  style={{
                                    fontSize: '0.68rem',
                                    padding: '1px 5px',
                                    borderRadius: '3px',
                                    background: 'rgba(255,255,255,0.06)',
                                    color: b === 'SBI' ? '#60A5FA' : b === 'AXIS' ? '#EC4899' : '#FBBF24',
                                    fontWeight: '700',
                                  }}
                                >
                                  {b}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td style={{ padding: '10px', color: '#CBD5E1', fontWeight: '600' }}>{net.primary_pattern}</td>
                          <td style={{ padding: '10px' }}>
                            <span
                              style={{
                                padding: '2px 8px',
                                borderRadius: '5px',
                                fontSize: '0.7rem',
                                fontWeight: '800',
                                background:
                                  net.status === 'FROZEN'
                                    ? 'rgba(239, 68, 68, 0.25)'
                                    : net.status === 'RESTRICTED'
                                    ? 'rgba(249, 115, 22, 0.25)'
                                    : net.status === 'UNDER_REVIEW'
                                    ? 'rgba(167, 139, 250, 0.25)'
                                    : 'rgba(245, 158, 11, 0.25)',
                                color:
                                  net.status === 'FROZEN'
                                    ? '#EF4444'
                                    : net.status === 'RESTRICTED'
                                    ? '#F97316'
                                    : net.status === 'UNDER_REVIEW'
                                    ? '#C084FC'
                                    : '#F59E0B',
                              }}
                            >
                              {net.status || 'UNDER_REVIEW'}
                            </span>
                          </td>
                          <td style={{ padding: '10px', textAlign: 'right' }}>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                loadNetworkDetail(net.network_id);
                                document.getElementById('graph-forensics-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                              }}
                              style={{
                                padding: '4px 10px',
                                borderRadius: '5px',
                                border: selectedNetwork === net.network_id ? '1px solid #EF4444' : '1px solid rgba(59, 130, 246, 0.4)',
                                background: selectedNetwork === net.network_id ? 'rgba(239, 68, 68, 0.25)' : 'rgba(59, 130, 246, 0.15)',
                                color: selectedNetwork === net.network_id ? '#F87171' : '#93C5FD',
                                fontSize: '0.72rem',
                                fontWeight: '800',
                                cursor: 'pointer',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '5px',
                              }}
                            >
                              <Search size={11} />
                              <span>{selectedNetwork === net.network_id ? 'Investigating (Active)' : 'Investigate'}</span>
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
        )}
      </div>
    </div>
  );
}
