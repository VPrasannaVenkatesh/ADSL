import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Network,
  Download,
  Filter,
  RefreshCw,
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Share2,
  Code,
  Layers,
  ArrowRight,
  Info,
  Check,
} from 'lucide-react';
import { simulatorApi } from '../api/simulatorApi';

export function NetworkGraphView({ onSelectAccount }) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);

  // Filters
  const [selectedBank, setSelectedBank] = useState('ALL');
  const [crossBankOnly, setCrossBankOnly] = useState(false);
  const [minAmount, setMinAmount] = useState(0);
  const [edgeLimit, setEdgeLimit] = useState(120);
  const [searchAccount, setSearchAccount] = useState('');

  // Selected Node / Hover State
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [copied, setCopied] = useState(false);

  // Canvas ref & viewport transformation
  const canvasRef = useRef(null);
  const [transform, setTransform] = useState({ x: 400, y: 300, k: 1 });
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });

  // Load Graph Data
  const loadGraph = async () => {
    setLoading(true);
    try {
      const params = {
        bank: selectedBank,
        cross_bank_only: crossBankOnly,
        limit: edgeLimit,
      };
      if (minAmount > 0) params.min_amount = minAmount;
      if (searchAccount) params.account_id = searchAccount;

      const res = await simulatorApi.getNetworkGraph(params);
      setGraphData(res.graph || { nodes: [], edges: [] });
      setMetadata(res.metadata || null);
    } catch (err) {
      console.error('Failed to load network graph', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [selectedBank, crossBankOnly, minAmount, edgeLimit]);

  // Compute 2D Node Layout using Force Simulation approximation
  const layout = useMemo(() => {
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    if (!nodes.length) return { nodesMap: new Map(), nodePositions: [] };

    const positions = new Map();
    const width = 800;
    const height = 600;

    // Arrange nodes in bank cluster circles initially
    const bankCenters = {
      SBI: { x: width * 0.25, y: height * 0.35 },
      AXIS: { x: width * 0.75, y: height * 0.35 },
      IOB: { x: width * 0.50, y: height * 0.75 },
    };

    nodes.forEach((n, idx) => {
      const center = bankCenters[n.bank] || { x: width * 0.5, y: height * 0.5 };
      const angle = (idx * (2 * Math.PI / Math.max(1, nodes.length))) + Math.random() * 0.5;
      const radius = 60 + Math.random() * 120;
      positions.set(n.id, {
        ...n,
        x: center.x + Math.cos(angle) * radius,
        y: center.y + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      });
    });

    // Run simple relaxation iterations
    for (let iter = 0; iter < 40; iter++) {
      // Repulsion between all nodes
      const posArray = Array.from(positions.values());
      for (let i = 0; i < posArray.length; i++) {
        for (let j = i + 1; j < posArray.length; j++) {
          const n1 = posArray[i];
          const n2 = posArray[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < 180) {
            const force = (180 - dist) / dist * 0.15;
            n1.x -= dx * force;
            n1.y -= dy * force;
            n2.x += dx * force;
            n2.y += dy * force;
          }
        }
      }

      // Attraction along edges
      edges.forEach((e) => {
        const s = positions.get(e.source);
        const t = positions.get(e.target);
        if (s && t) {
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 100) * 0.04;
          s.x += (dx / dist) * force;
          s.y += (dy / dist) * force;
          t.x -= (dx / dist) * force;
          t.y -= (dy / dist) * force;
        }
      });
    }

    return { nodesMap: positions, nodePositions: Array.from(positions.values()) };
  }, [graphData]);

  // Render Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    const { nodesMap } = layout;
    const edges = graphData.edges || [];

    // 1. Draw Edges
    edges.forEach((edge) => {
      const s = nodesMap.get(edge.source);
      const t = nodesMap.get(edge.target);
      if (!s || !t) return;

      const isCross = edge.is_cross_bank;
      const isHalted = Boolean(edge.flow_stopped || edge.status === 'UNDER_REVIEW' || edge.status === 'RESTRICTED' || edge.status === 'FROZEN');
      const isFrozenOrRestricted = edge.status === 'RESTRICTED' || edge.status === 'FROZEN';
      const isUnderReview = edge.status === 'UNDER_REVIEW';

      const isHighlighted =
        (selectedNode && (edge.source === selectedNode.id || edge.target === selectedNode.id)) ||
        (hoveredNode && (edge.source === hoveredNode.id || edge.target === hoveredNode.id));

      ctx.beginPath();
      if (isHalted) {
        ctx.setLineDash([5, 4]);
      } else {
        ctx.setLineDash([]);
      }
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);

      if (isFrozenOrRestricted) {
        ctx.strokeStyle = '#EF4444';
        ctx.lineWidth = 2.2;
        ctx.shadowColor = 'rgba(239, 68, 68, 0.6)';
        ctx.shadowBlur = 6;
      } else if (isUnderReview) {
        ctx.strokeStyle = '#C084FC';
        ctx.lineWidth = 2.0;
        ctx.shadowColor = 'rgba(192, 132, 252, 0.6)';
        ctx.shadowBlur = 5;
      } else if (isHighlighted) {
        ctx.strokeStyle = '#00E5FF';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = 'rgba(0, 229, 255, 0.8)';
        ctx.shadowBlur = 8;
      } else if (isCross) {
        ctx.strokeStyle = 'rgba(168, 85, 247, 0.45)';
        ctx.lineWidth = 1.6;
        ctx.shadowBlur = 0;
      } else {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 1;
        ctx.shadowBlur = 0;
      }

      ctx.stroke();
      ctx.setLineDash([]);
      ctx.shadowBlur = 0;

      // Draw arrow head
      const angle = Math.atan2(t.y - s.y, t.x - s.x);
      const arrowDist = 18;
      const ax = t.x - Math.cos(angle) * arrowDist;
      const ay = t.y - Math.sin(angle) * arrowDist;

      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(ax - 6 * Math.cos(angle - Math.PI / 6), ay - 6 * Math.sin(angle - Math.PI / 6));
      ctx.lineTo(ax - 6 * Math.cos(angle + Math.PI / 6), ay - 6 * Math.sin(angle + Math.PI / 6));
      ctx.fillStyle = isFrozenOrRestricted
        ? '#EF4444'
        : isUnderReview
        ? '#C084FC'
        : isHighlighted
        ? '#00E5FF'
        : isCross
        ? 'rgba(168, 85, 247, 0.8)'
        : 'rgba(255, 255, 255, 0.25)';
      ctx.fill();
    });

    // 2. Draw Nodes
    layout.nodePositions.forEach((node) => {
      const isSelected = selectedNode && selectedNode.id === node.id;
      const isHovered = hoveredNode && hoveredNode.id === node.id;

      let fillColor = '#3B82F6';
      if (node.bank === 'AXIS') fillColor = '#EC4899';
      if (node.bank === 'IOB') fillColor = '#F59E0B';

      ctx.beginPath();
      ctx.arc(node.x, node.y, isSelected || isHovered ? 11 : 8, 0, 2 * Math.PI);
      ctx.fillStyle = fillColor;

      if (isSelected || isHovered) {
        ctx.shadowColor = fillColor;
        ctx.shadowBlur = 15;
      } else {
        ctx.shadowBlur = 0;
      }

      ctx.fill();
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = isSelected ? 2.5 : 1;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Node Label
      ctx.font = '10px JetBrains Mono, monospace';
      ctx.fillStyle = isSelected || isHovered ? '#FFFFFF' : 'rgba(240, 244, 248, 0.7)';
      ctx.fillText(node.id, node.x + 12, node.y + 3);
    });

    ctx.restore();
  }, [layout, transform, selectedNode, hoveredNode]);

  // Pan & Zoom handlers
  const handleMouseDown = (e) => {
    isDraggingRef.current = true;
    dragStartRef.current = { x: e.clientX - transform.x, y: e.clientY - transform.y };
  };

  const handleMouseMove = (e) => {
    if (isDraggingRef.current) {
      setTransform((prev) => ({
        ...prev,
        x: e.clientX - dragStartRef.current.x,
        y: e.clientY - dragStartRef.current.y,
      }));
      return;
    }

    // Check hit test for node hover
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - transform.x) / transform.k;
    const mouseY = (e.clientY - rect.top - transform.y) / transform.k;

    let found = null;
    for (const node of layout.nodePositions) {
      const dx = node.x - mouseX;
      const dy = node.y - mouseY;
      if (Math.sqrt(dx * dx + dy * dy) <= 14) {
        found = node;
        break;
      }
    }
    setHoveredNode(found);
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleCanvasClick = (e) => {
    if (hoveredNode) {
      setSelectedNode(hoveredNode);
    }
  };

  const handleZoom = (factor) => {
    setTransform((prev) => ({
      ...prev,
      k: Math.max(0.3, Math.min(3, prev.k * factor)),
    }));
  };

  const handleResetView = () => {
    setTransform({ x: 250, y: 150, k: 0.85 });
    setSelectedNode(null);
  };

  const handleCopyJson = () => {
    const exportData = {
      directed: true,
      nodes: graphData.nodes,
      edges: graphData.edges,
      metadata,
    };
    navigator.clipboard.writeText(JSON.stringify(exportData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ margin: '0 24px 24px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* Top Filter Bar */}
      <div className="glass-panel" style={{
        padding: '14px 20px',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '14px',
      }}>
        {/* Left: View Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '700', color: 'var(--accent-cyan)', fontSize: '0.85rem' }}>
            <Network size={18} />
            <span>TOPOLOGY & GRAPH PREPARATION</span>
          </div>

          <div style={{ height: '18px', width: '1px', background: 'var(--border-color)' }} />

          {/* Bank Select */}
          <select
            value={selectedBank}
            onChange={(e) => setSelectedBank(e.target.value)}
            className="input-control"
            style={{ width: '130px', padding: '5px 10px', fontSize: '0.785rem' }}
          >
            <option value="ALL">All Banks</option>
            <option value="SBI">SBI Network</option>
            <option value="AXIS">AXIS Network</option>
            <option value="IOB">IOB Network</option>
          </select>

          {/* Cross Bank Toggle */}
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer', userSelect: 'none' }}>
            <input
              type="checkbox"
              checked={crossBankOnly}
              onChange={(e) => setCrossBankOnly(e.target.checked)}
              style={{ accentColor: 'var(--accent-cyan)' }}
            />
            <span>Cross-Bank Links Only</span>
          </label>

          {/* Edge Limit Slider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.785rem', color: 'var(--text-muted)' }}>
            <span>Edges:</span>
            <input
              type="range"
              min="30"
              max="300"
              step="30"
              value={edgeLimit}
              onChange={(e) => setEdgeLimit(Number(e.target.value))}
              style={{ accentColor: 'var(--accent-cyan)', width: '90px' }}
            />
            <span className="mono" style={{ color: 'var(--text-primary)' }}>{edgeLimit}</span>
          </div>
        </div>

        {/* Right: Actions (Search, Export, Refresh) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn-secondary"
            onClick={() => setShowExportModal(true)}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Code size={14} color="var(--accent-cyan)" />
            <span>GNN / NetworkX JSON</span>
          </button>

          <button
            className="btn-secondary"
            onClick={loadGraph}
            disabled={loading}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <RefreshCw size={14} className={loading ? 'pulse-dot' : ''} />
            <span>{loading ? 'Analyzing...' : 'Refresh Graph'}</span>
          </button>
        </div>
      </div>

      {/* Main Graph Canvas & Side Inspector Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedNode ? '1fr 340px' : '1fr', gap: '16px' }}>
        
        {/* Canvas Card */}
        <div className="glass-panel" style={{ position: 'relative', overflow: 'hidden', minHeight: '560px', background: '#05070B' }}>
          
          {/* Zoom & Pan Controls Overlay */}
          <div style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
            zIndex: 10,
          }}>
            <button className="btn-secondary" onClick={() => handleZoom(1.2)} style={{ padding: '8px' }} title="Zoom In">
              <ZoomIn size={15} />
            </button>
            <button className="btn-secondary" onClick={() => handleZoom(0.8)} style={{ padding: '8px' }} title="Zoom Out">
              <ZoomOut size={15} />
            </button>
            <button className="btn-secondary" onClick={handleResetView} style={{ padding: '8px' }} title="Reset View">
              <Maximize2 size={15} />
            </button>
          </div>

          {/* Graph Legend Overlay */}
          <div style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            background: 'rgba(13, 17, 26, 0.85)',
            backdropFilter: 'blur(10px)',
            padding: '10px 14px',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            fontSize: '0.725rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
            zIndex: 10,
          }}>
            <div style={{ fontWeight: '700', color: 'var(--text-muted)' }}>NETWORK TOPOLOGY</div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#60A5FA' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3B82F6' }} />
                SBI Account
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#F472B6' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#EC4899' }} />
                AXIS Account
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#FBBF24' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B' }} />
                IOB Account
              </span>
            </div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '2px', color: 'var(--text-muted)' }}>
              <span>─ Same Bank Transfer</span>
              <span style={{ color: '#C084FC' }}>━━ Cross-Bank Transfer</span>
            </div>
          </div>

          {/* Stats Badge Overlay */}
          {metadata && (
            <div style={{
              position: 'absolute',
              top: '16px',
              left: '16px',
              background: 'rgba(13, 17, 26, 0.85)',
              padding: '6px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              zIndex: 10,
            }}>
              Active Subgraph: <strong>{metadata.node_count}</strong> nodes • <strong>{metadata.edge_count}</strong> links ({metadata.cross_bank_edge_count} cross-bank)
            </div>
          )}

          {/* Interactive HTML5 Canvas */}
          <canvas
            ref={canvasRef}
            width={950}
            height={560}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onClick={handleCanvasClick}
            style={{ width: '100%', height: '100%', cursor: isDraggingRef.current ? 'grabbing' : 'grab' }}
          />
        </div>

        {/* Selected Node Details Side Inspector */}
        {selectedNode && (
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-muted)' }}>NODE INSPECTOR</span>
              <button
                onClick={() => setSelectedNode(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem' }}
              >
                ✕
              </button>
            </div>

            {/* Account Title */}
            <div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }} className="mono">
                {selectedNode.id}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', marginTop: '2px' }}>
                {selectedNode.customer_name || 'Account Holder'}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', fontSize: '0.75rem' }}>
              <span style={{
                padding: '2px 8px',
                borderRadius: '4px',
                background: selectedNode.bank === 'SBI' ? 'rgba(59,130,246,0.15)' : selectedNode.bank === 'AXIS' ? 'rgba(236,72,153,0.15)' : 'rgba(245,158,11,0.15)',
                color: selectedNode.bank === 'SBI' ? '#60A5FA' : selectedNode.bank === 'AXIS' ? '#F472B6' : '#FBBF24',
                fontWeight: '700',
              }}>
                {selectedNode.bank} Bank
              </span>
              <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)' }}>
                {selectedNode.account_type}
              </span>
            </div>

            {/* Balances & Location */}
            <div style={{ background: 'rgba(7, 9, 14, 0.6)', padding: '12px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Current Balance</span>
                <span className="mono" style={{ fontWeight: '700', color: '#10B981' }}>
                  ₹{Number(selectedNode.current_balance || 0).toLocaleString('en-IN')}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Home Location</span>
                <span style={{ color: 'var(--text-primary)' }}>{selectedNode.home_location || 'Chennai'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Account Created</span>
                <span style={{ color: 'var(--text-secondary)' }}>{selectedNode.account_created_date || 'N/A'}</span>
              </div>
            </div>

            {/* Action button to open full drawer */}
            <button
              className="btn-primary"
              onClick={() => onSelectAccount(selectedNode.bank, selectedNode.id)}
              style={{ width: '100%', justifyContent: 'center', fontSize: '0.825rem' }}
            >
              <span>View Full Behaviour Profile</span>
              <ArrowRight size={14} />
            </button>
          </div>
        )}
      </div>

      {/* GNN / NetworkX JSON Export Modal */}
      {showExportModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '24px',
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '720px', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-cyan)', fontWeight: '700' }}>
                <Code size={18} />
                <span>GNN & NetworkX Graph Data Export</span>
              </div>
              <button
                onClick={() => setShowExportModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <div style={{ padding: '16px 20px', overflowY: 'auto', flex: 1 }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                This JSON payload contains directed multi-graph nodes and edge attributes, formatted for direct ingestion into <code>networkx.node_link_graph</code> or PyTorch Geometric (PyG) GNN pipelines.
              </div>
              <pre className="mono" style={{
                background: '#04060A',
                padding: '14px',
                borderRadius: '8px',
                fontSize: '0.725rem',
                color: '#A5F3FC',
                maxHeight: '340px',
                overflow: 'auto',
                border: '1px solid var(--border-color)',
              }}>
                {JSON.stringify({
                  directed: true,
                  multigraph: true,
                  nodes: graphData.nodes,
                  edges: graphData.edges,
                  metadata,
                }, null, 2)}
              </pre>
            </div>

            <div style={{ padding: '14px 20px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="btn-secondary" onClick={() => setShowExportModal(false)}>
                Close
              </button>
              <button className="btn-primary" onClick={handleCopyJson}>
                {copied ? <Check size={15} /> : <Share2 size={15} />}
                <span>{copied ? 'Copied to Clipboard!' : 'Copy Graph JSON'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
