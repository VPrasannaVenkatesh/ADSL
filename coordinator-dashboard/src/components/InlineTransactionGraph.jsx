import React, { useState, useEffect } from 'react';
import {
  GitFork,
  ShieldAlert,
  ArrowRight,
  Download,
  BrainCircuit,
  TrendingUp,
  Cpu,
  Lock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Layers,
  Sparkles,
} from 'lucide-react';

const ROLE_COLORS = {
  SOURCE: '#3B82F6',
  MULE_HUB: '#EF4444',
  MULE_RELAY: '#F97316',
  DISPERSER: '#EC4899',
  SINK: '#10B981',
  SUSPICIOUS: '#F59E0B',
  NORMAL: '#6B7280',
};

export function InlineTransactionGraph({ transactionId, initialTxData, onClose }) {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentHops, setCurrentHops] = useState(2);
  const [selectedNode, setSelectedNode] = useState(null);
  const [downloadingReport, setDownloadingReport] = useState(null);

  const fetchGraph = async (hops = currentHops) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/adsl/transaction-graph/${transactionId}?hops=${hops}`);
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
      }
    } catch (err) {
      console.error('Failed to load transaction graph:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph(currentHops);
  }, [transactionId, currentHops]);

  const handleExpandRLHop = () => {
    const nextHops = Math.min(4, currentHops + 1);
    setCurrentHops(nextHops);
    fetchGraph(nextHops);
  };

  const handleDownloadReport = async (accountId) => {
    if (!accountId) return;
    setDownloadingReport(accountId);
    try {
      const res = await fetch(`/api/adsl/account/${accountId}/report`);
      if (res.ok) {
        const data = await res.json();
        const textContent = data.report_text || JSON.stringify(data, null, 2);
        const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ADSL_Forensic_Report_${accountId}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to download account report:', err);
    } finally {
      setDownloadingReport(null);
    }
  };

  const rlDecision = graphData?.rl_decision || {
    action: 'EXPAND_GRAPH',
    confidence: 0.88,
    reward: 8.0,
    reason: 'Suspicious fund movement detected. Expanding graph by 1 hop to trace upstream source / downstream sink.',
    should_grow: true,
    hops_analyzed: currentHops,
  };

  const automatedVerdict = graphData?.automated_verdict || {
    policy_action: 'AUTOMATIC LIEN APPLIED & QUARANTINED',
    status: 'RESTRICTED',
    automated_reason: 'Autonomous policy: High GNN Mule Risk and velocity anomaly detected. Funds protected under lien.',
  };

  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];

  return (
    <div style={{
      background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(10, 15, 30, 0.98) 100%)',
      border: '1px solid rgba(59, 130, 246, 0.35)',
      borderRadius: '12px',
      padding: '24px',
      margin: '12px 0 20px 0',
      boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Decorative top accent glow */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '3px',
        background: 'linear-gradient(90deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%)',
      }} />

      {/* Header Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingBottom: '18px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        marginBottom: '20px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'rgba(59, 130, 246, 0.2)',
            border: '1px solid #3B82F6',
            borderRadius: '10px',
            padding: '8px 10px',
            display: 'flex',
            alignItems: 'center',
          }}>
            <GitFork size={20} color="#60A5FA" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.05rem', fontWeight: 800, color: '#FFFFFF', letterSpacing: '0.01em' }}>
                Forensic Graph Investigation
              </span>
              <span style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '0.78rem',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                background: 'rgba(255, 255, 255, 0.08)',
                color: '#93C5FD',
              }}>
                {transactionId}
              </span>
              <span style={{
                fontSize: '0.72rem',
                fontWeight: 800,
                padding: '3px 8px',
                borderRadius: '6px',
                background: 'rgba(139, 92, 246, 0.2)',
                color: '#C084FC',
                border: '1px solid rgba(139, 92, 246, 0.3)',
              }}>
                Hops Depth: {currentHops}
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '3px' }}>
              Dynamic cross-bank topology graph rendered right below transaction • Participating banks:{' '}
              <strong style={{ color: '#E2E8F0' }}>{(graphData?.banks_involved || ['SBI', 'AXIS']).join(', ')}</strong>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => fetchGraph(currentHops)}
            disabled={loading}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#CBD5E1',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <RefreshCw size={12} className={loading ? 'spin' : ''} />
            Refresh
          </button>
          <button
            onClick={onClose}
            style={{
              padding: '6px 14px',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              background: 'transparent',
              color: '#94A3B8',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Collapse
          </button>
        </div>
      </div>

      {/* Main Investigation Split: 1. Graph Visualizer (Left/Top) | 2. RL Agent & Dynamic Verdict (Right/Bottom) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.8fr) minmax(320px, 1fr)', gap: '24px' }}>
        
        {/* LEFT: VISUAL TOPOLOGY GRAPH */}
        <div style={{
          background: 'rgba(5, 10, 20, 0.7)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '10px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '380px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#CBD5E1', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Cluster Topology & Transaction Flow
            </div>
            <div style={{ display: 'flex', gap: '8px', fontSize: '0.7rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#93C5FD' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#3B82F6' }} /> Source
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#F87171' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#EF4444' }} /> Mule Hub/Relay
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#34D399' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10B981' }} /> Exit Sink
              </span>
            </div>
          </div>

          {/* Interactive Graph Canvas / SVG */}
          <div style={{
            flex: 1,
            position: 'relative',
            background: 'radial-gradient(circle at center, rgba(30, 58, 138, 0.15) 0%, rgba(2, 6, 23, 0.8) 100%)',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '300px',
            overflow: 'hidden',
          }}>
            {loading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', color: '#94A3B8' }}>
                <RefreshCw size={24} className="spin" color="#3B82F6" />
                <span style={{ fontSize: '0.82rem' }}>Resolving cross-bank graph nodes & RL decision...</span>
              </div>
            ) : nodes.length === 0 ? (
              <div style={{ color: '#94A3B8', fontSize: '0.82rem' }}>No connected graph nodes found for this transaction.</div>
            ) : (() => {
              // ── Dynamic Non-Overlapping Layered Topological Layout ──
              const nodePositions = {};
              const rank0 = []; // Sources / Initiators
              const rank1 = []; // Intermediaries / Mule Relays / Hubs
              const rank2 = []; // Sinks / Dispersers / Receivers

              nodes.forEach((n) => {
                const role = (n.network_role || n.classification || '').toUpperCase();
                const inDeg = edges.filter((e) => e.target === n.account_id).length;
                const outDeg = edges.filter((e) => e.source === n.account_id).length;

                if (role.includes('SOURCE') || (inDeg === 0 && outDeg > 0)) {
                  rank0.push(n);
                } else if (role.includes('SINK') || role.includes('DISPERSER') || (outDeg === 0 && inDeg > 0)) {
                  rank2.push(n);
                } else {
                  rank1.push(n);
                }
              });

              // Rebalance ranks if needed
              if (rank0.length === 0 && rank1.length > 0) rank0.push(rank1.shift());
              if (rank2.length === 0 && rank1.length > 0) rank2.push(rank1.pop());
              if (rank0.length === 0 && rank2.length > 1) rank0.push(rank2.shift());
              if (rank0.length === 0 && rank1.length === 0 && rank2.length === 0 && nodes.length > 0) {
                nodes.forEach((n, idx) => {
                  if (idx % 3 === 0) rank0.push(n);
                  else if (idx % 3 === 1) rank1.push(n);
                  else rank2.push(n);
                });
              }

              const maxColumnNodes = Math.max(rank0.length, rank1.length, rank2.length, 1);
              const minVerticalGap = 95;
              const svgWidth = 1060;
              const svgHeight = Math.max(380, maxColumnNodes * minVerticalGap + 70);

              const colPositions = [150, 530, 910];
              const columns = [rank0, rank1, rank2];

              columns.forEach((colNodes, colIdx) => {
                const colX = colPositions[colIdx];
                const count = colNodes.length;
                const totalH = (count - 1) * minVerticalGap;
                const startY = (svgHeight - totalH) / 2;

                colNodes.forEach((n, i) => {
                  nodePositions[n.account_id] = {
                    x: colX,
                    y: count === 1 ? svgHeight / 2 : startY + i * minVerticalGap,
                    colIdx,
                  };
                });
              });

              // Track pair occurrences for multi-edge separation
              const pairCounts = {};
              edges.forEach((e) => {
                const key = [e.source, e.target].sort().join('---');
                pairCounts[key] = (pairCounts[key] || 0) + 1;
              });
              const pairSeen = {};
              const placedBadges = [];

              return (
                <svg width="100%" height={svgHeight} viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ overflow: 'visible' }}>
                  <defs>
                    <marker
                      id="arrowhead"
                      markerWidth="8"
                      markerHeight="6"
                      refX="10"
                      refY="3"
                      orient="auto"
                    >
                      <polygon points="0 0, 8 3, 0 6" fill="#60A5FA" />
                    </marker>
                    <marker
                      id="arrowhead-halted"
                      markerWidth="8"
                      markerHeight="6"
                      refX="10"
                      refY="3"
                      orient="auto"
                    >
                      <polygon points="0 0, 8 3, 0 6" fill="#EF4444" />
                    </marker>
                  </defs>

                  {/* Render Directed Curved Edges with Anti-Collision Routing */}
                  {edges.map((e, idx) => {
                    const src = nodePositions[e.source];
                    const tgt = nodePositions[e.target];
                    if (!src || !tgt) return null;

                    const key = [e.source, e.target].sort().join('---');
                    const pairIndex = pairSeen[key] || 0;
                    pairSeen[key] = pairIndex + 1;
                    const isReverse = e.source > e.target;

                    const dx = tgt.x - src.x;
                    const dy = tgt.y - src.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;

                    // Perpendicular normal vector
                    const nx = -dy / dist;
                    const ny = dx / dist;

                    // Node boundary clearance (node radius 18)
                    const startX = src.x + (dx / dist) * 22;
                    const startY = src.y + (dy / dist) * 22;
                    const endX = tgt.x - (dx / dist) * 26;
                    const endY = tgt.y - (dy / dist) * 26;

                    // Check column leap (e.g. from Col 0 directly to Col 2 bypassing Col 1)
                    const colSpan = Math.abs((src.colIdx ?? 0) - (tgt.colIdx ?? 2));
                    let curveOffset = 0;

                    if (colSpan >= 2) {
                      // Long leap: curve cleanly ABOVE or BELOW intermediate nodes in column 1
                      const avgY = (src.y + tgt.y) / 2;
                      const archSign = avgY < svgHeight / 2 ? -1 : 1;
                      curveOffset = archSign * (68 + pairIndex * 26);
                    } else if (pairCounts[key] > 1) {
                      // Multi-edges between same node pair: curve symmetrically
                      curveOffset = (pairIndex % 2 === 0 ? 1 : -1) * (22 + Math.floor(pairIndex / 2) * 22);
                      if (isReverse) curveOffset = -curveOffset;
                    } else {
                      // Single regular edge
                      curveOffset = (idx % 2 === 0 ? 1 : -1) * 16;
                    }

                    // Quadratic Bézier control point
                    const ctrlX = (startX + endX) / 2 + nx * curveOffset;
                    const ctrlY = (startY + endY) / 2 + ny * curveOffset;

                    const isHalted = e.flow_stopped;
                    const strokeColor = isHalted ? '#EF4444' : '#3B82F6';
                    const pathD = `M ${startX} ${startY} Q ${ctrlX} ${ctrlY} ${endX} ${endY}`;

                    // Compute Badge Position along Quadratic Curve
                    let t = 0.5;
                    // If long leap, shift badge slightly off-center if needed
                    if (colSpan >= 2) {
                      t = 0.5;
                    }
                    let bx = Math.pow(1 - t, 2) * startX + 2 * (1 - t) * t * ctrlX + Math.pow(t, 2) * endX;
                    let by = Math.pow(1 - t, 2) * startY + 2 * (1 - t) * t * ctrlY + Math.pow(t, 2) * endY;

                    // Check node collision: if badge is within 56px of ANY node center, shift t
                    for (const n of nodes) {
                      const np = nodePositions[n.account_id];
                      if (np) {
                        const ndx = np.x - bx;
                        const ndy = np.y - by;
                        if (Math.abs(ndx) < 56 && Math.abs(ndy) < 48) {
                          t = (src.colIdx ?? 0) <= (tgt.colIdx ?? 0) ? 0.32 : 0.68;
                          bx = Math.pow(1 - t, 2) * startX + 2 * (1 - t) * t * ctrlX + Math.pow(t, 2) * endX;
                          by = Math.pow(1 - t, 2) * startY + 2 * (1 - t) * t * ctrlY + Math.pow(t, 2) * endY;
                          break;
                        }
                      }
                    }

                    // Check badge-to-badge collision with previously placed badges
                    for (const pb of placedBadges) {
                      if (Math.abs(pb.x - bx) < 78 && Math.abs(pb.y - by) < 24) {
                        by += (by >= pb.y ? 24 : -24);
                      }
                    }
                    placedBadges.push({ x: bx, y: by });

                    return (
                      <g key={`edge-${idx}`}>
                        <path
                          d={pathD}
                          fill="none"
                          stroke={strokeColor}
                          strokeWidth="2.2"
                          strokeDasharray={isHalted ? '5 5' : 'none'}
                          markerEnd={isHalted ? 'url(#arrowhead-halted)' : 'url(#arrowhead)'}
                          opacity="0.9"
                        />
                        {/* Flow Amount Badge with Opaque Protective Plate */}
                        <g transform={`translate(${bx}, ${by})`}>
                          <rect
                            x="-39"
                            y="-11"
                            width="78"
                            height="22"
                            rx="6"
                            fill="rgba(5, 10, 22, 0.97)"
                            stroke={strokeColor}
                            strokeWidth="1.2"
                          />
                          <text
                            x="0"
                            y="4"
                            fill={isHalted ? '#FCA5A5' : '#93C5FD'}
                            fontSize="9"
                            fontWeight="800"
                            textAnchor="middle"
                            fontFamily="JetBrains Mono, monospace"
                          >
                            ₹{Number(e.amount || 0).toLocaleString()}
                          </text>
                        </g>
                      </g>
                    );
                  })}

                  {/* Render Nodes with Protective Backing Plate */}
                  {nodes.map((n) => {
                    const pos = nodePositions[n.account_id];
                    if (!pos) return null;
                    const cx = pos.x;
                    const cy = pos.y;
                    const isSelected = selectedNode?.account_id === n.account_id;
                    const roleColor = ROLE_COLORS[n.network_role] || ROLE_COLORS[n.classification] || '#6B7280';

                    return (
                      <g
                        key={`node-${n.account_id}`}
                        onClick={() => setSelectedNode(n)}
                        style={{ cursor: 'pointer' }}
                      >
                        {/* Glow on Selected */}
                        {isSelected && (
                          <circle cx={cx} cy={cy} r="26" fill="none" stroke="#60A5FA" strokeWidth="2.5" strokeDasharray="3 3" />
                        )}

                        {/* Node Body */}
                        <circle
                          cx={cx}
                          cy={cy}
                          r="18"
                          fill="rgba(15, 23, 42, 0.95)"
                          stroke={roleColor}
                          strokeWidth="2.5"
                        />
                        <text
                          x={cx}
                          y={cy + 4}
                          fill="#FFFFFF"
                          fontSize="9"
                          fontWeight="800"
                          textAnchor="middle"
                        >
                          {n.bank ? n.bank.slice(0, 3) : 'BNK'}
                        </text>

                        {/* Protective Label Plate (Eliminates text collisions) */}
                        <rect
                          x={cx - 48}
                          y={cy + 22}
                          width="96"
                          height="28"
                          rx="6"
                          fill="rgba(8, 14, 26, 0.96)"
                          stroke="rgba(255, 255, 255, 0.12)"
                          strokeWidth="0.8"
                        />

                        {/* Account ID */}
                        <text
                          x={cx}
                          y={cy + 34}
                          fill={isSelected ? '#60A5FA' : '#E2E8F0'}
                          fontSize="9.5"
                          fontWeight="bold"
                          textAnchor="middle"
                          fontFamily="JetBrains Mono, monospace"
                        >
                          {n.account_id}
                        </text>

                        {/* Role tag */}
                        <text
                          x={cx}
                          y={cy + 45}
                          fill={roleColor}
                          fontSize="8"
                          fontWeight="800"
                          textAnchor="middle"
                        >
                          {n.network_role || n.classification}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              );
            })()}
          </div>

          {/* Node Quick Inspector Footer */}
          {selectedNode ? (
            <div style={{
              marginTop: '14px',
              padding: '12px 16px',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <div>
                <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>Inspecting Node: </span>
                <strong style={{ color: '#FFFFFF', fontFamily: 'JetBrains Mono, monospace' }}>{selectedNode.account_id}</strong>
                <span style={{ marginLeft: 10, fontSize: '0.72rem', color: ROLE_COLORS[selectedNode.network_role] || '#CBD5E1', fontWeight: 700 }}>
                  ({selectedNode.network_role} • Mule Prob: {Math.round((selectedNode.gnn_mule_probability || 0.1) * 100)}%)
                </span>
              </div>
              <button
                onClick={() => handleDownloadReport(selectedNode.account_id)}
                disabled={downloadingReport === selectedNode.account_id}
                style={{
                  padding: '5px 12px',
                  borderRadius: '6px',
                  background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
                  color: '#fff',
                  border: 'none',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Download size={13} />
                {downloadingReport === selectedNode.account_id ? 'Exporting...' : 'Download Account Dossier'}
              </button>
            </div>
          ) : (
            <div style={{ marginTop: '10px', fontSize: '0.72rem', color: '#64748B', textAlign: 'center' }}>
              Click any node in the graph to inspect account details and download its individual forensic dossier.
            </div>
          )}
        </div>

        {/* RIGHT: REINFORCEMENT LEARNING AGENT & DYNAMIC AUTONOMOUS VERDICT */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* 1. REINFORCEMENT LEARNING DECISION CARD */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(139, 92, 246, 0.35)',
            borderRadius: '10px',
            padding: '18px 20px',
            position: 'relative',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <BrainCircuit size={18} color="#C084FC" />
                <span style={{ fontSize: '0.82rem', fontWeight: 800, color: '#E2E8F0', textTransform: 'uppercase' }}>
                  RL Graph Decision Agent
                </span>
              </div>
              <span style={{
                padding: '3px 8px',
                borderRadius: '5px',
                fontSize: '0.7rem',
                fontWeight: 800,
                background: rlDecision.action === 'EXPAND_GRAPH' ? 'rgba(59, 130, 246, 0.25)' : 'rgba(239, 68, 68, 0.25)',
                color: rlDecision.action === 'EXPAND_GRAPH' ? '#60A5FA' : '#F87171',
                border: `1px solid ${rlDecision.action === 'EXPAND_GRAPH' ? '#3B82F6' : '#EF4444'}`,
              }}>
                {rlDecision.action}
              </span>
            </div>

            {/* Reasoning */}
            <div style={{ fontSize: '0.78rem', color: '#CBD5E1', lineHeight: '1.45', marginBottom: '14px' }}>
              {rlDecision.reason}
            </div>

            {/* Metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '8px 12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.68rem', color: '#94A3B8' }}>RL Confidence</div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: '#A78BFA', marginTop: '2px' }}>
                  {Math.round((rlDecision.confidence || 0.85) * 100)}%
                </div>
              </div>
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '8px 12px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.68rem', color: '#94A3B8' }}>Reward Gain</div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: '#34D399', marginTop: '2px' }}>
                  +{rlDecision.reward || 8.0}
                </div>
              </div>
            </div>

            {/* RL Action Button */}
            {rlDecision.should_grow ? (
              <button
                onClick={handleExpandRLHop}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '9px 14px',
                  borderRadius: '6px',
                  background: 'linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%)',
                  color: '#FFFFFF',
                  border: 'none',
                  fontSize: '0.78rem',
                  fontWeight: 800,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  boxShadow: '0 4px 15px rgba(139, 92, 246, 0.3)',
                }}
              >
                <Sparkles size={14} />
                Apply RL Exploration (+1 Hop to Depth {currentHops + 1})
              </button>
            ) : (
              <div style={{
                fontSize: '0.72rem',
                color: '#94A3B8',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '8px 12px',
                borderRadius: '6px',
                textAlign: 'center',
                border: '1px solid rgba(255, 255, 255, 0.06)',
              }}>
                RL Policy: Optimal exploration budget reached ({currentHops} hops). No further expansion warranted.
              </div>
            )}
          </div>

          {/* 2. DYNAMIC AUTONOMOUS SYSTEM VERDICT CARD */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            borderRadius: '10px',
            padding: '18px 20px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <ShieldAlert size={18} color="#EF4444" />
              <span style={{ fontSize: '0.82rem', fontWeight: 800, color: '#E2E8F0', textTransform: 'uppercase' }}>
                Autonomous System Verdict
              </span>
            </div>

            <div style={{
              padding: '10px 14px',
              borderRadius: '6px',
              background: automatedVerdict.status === 'RESTRICTED' || automatedVerdict.status === 'FROZEN' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
              border: `1px solid ${automatedVerdict.status === 'RESTRICTED' || automatedVerdict.status === 'FROZEN' ? '#EF4444' : '#10B981'}`,
              marginBottom: '10px',
            }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 900, color: automatedVerdict.status === 'RESTRICTED' || automatedVerdict.status === 'FROZEN' ? '#F87171' : '#34D399' }}>
                {automatedVerdict.policy_action}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#CBD5E1', marginTop: '4px', lineHeight: '1.4' }}>
                {automatedVerdict.automated_reason}
              </div>
            </div>

            <div style={{ fontSize: '0.7rem', color: '#64748B', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Lock size={12} />
              <span>Decided dynamically by ADSL decentralized consensus. No manual intervention required.</span>
            </div>
          </div>

          {/* 3. DOWNLOAD REPORT ACTIONS */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '10px',
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
          }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#E2E8F0', textTransform: 'uppercase' }}>
              Compliance & Audit Export
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <button
                onClick={() => handleDownloadReport(initialTxData?.sender_account_id || initialTxData?.sender)}
                disabled={downloadingReport !== null}
                style={{
                  padding: '8px 10px',
                  borderRadius: '6px',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  background: 'rgba(59, 130, 246, 0.15)',
                  color: '#93C5FD',
                  fontSize: '0.72rem',
                  fontWeight: 800,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <Download size={13} />
                Sender Dossier
              </button>
              <button
                onClick={() => handleDownloadReport(initialTxData?.receiver_account_id || initialTxData?.receiver)}
                disabled={downloadingReport !== null}
                style={{
                  padding: '8px 10px',
                  borderRadius: '6px',
                  border: '1px solid rgba(236, 72, 153, 0.4)',
                  background: 'rgba(236, 72, 153, 0.15)',
                  color: '#F472B6',
                  fontSize: '0.72rem',
                  fontWeight: 800,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <Download size={13} />
                Receiver Dossier
              </button>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
