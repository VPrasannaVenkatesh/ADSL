import React, { useState, useEffect, useMemo } from 'react';
import {
  GitFork,
  Search,
  ShieldAlert,
  BrainCircuit,
  Lock,
  FileText,
  Printer,
  TrendingUp,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  ExternalLink,
  Layers,
  ArrowRight,
  Info,
  DollarSign,
  UserCheck,
} from 'lucide-react';

export function ForensicsTab() {
  const [searchTx, setSearchTx] = useState('');
  const [activeTxId, setActiveTxId] = useState('');
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedNode, setSelectedNode] = useState(null);

  // Fetch recent candidate transactions for quick selection
  const fetchRecent = async () => {
    try {
      const res = await fetch('/api/adsl/transactions?limit=20');
      if (res.ok) {
        const json = await res.json();
        const txs = json.transactions || [];
        setRecentTransactions(txs);
        if (!activeTxId && txs.length > 0) {
          setActiveTxId(txs[0].transaction_id);
          loadForensicDossier(txs[0].transaction_id);
        }
      }
    } catch (err) {
      console.error('Failed to load candidate transactions:', err);
    }
  };

  useEffect(() => {
    fetchRecent();
  }, []);

  const loadForensicDossier = async (txId) => {
    if (!txId) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/adsl/transaction/${txId}/report`);
      if (res.ok) {
        const json = await res.json();
        setReportData(json);
        setActiveTxId(txId);
      } else {
        // Fallback demo structure if not found directly
        setReportData(createFallbackReport(txId));
        setActiveTxId(txId);
      }
    } catch (err) {
      console.error('Failed to fetch forensic report:', err);
      setReportData(createFallbackReport(txId));
      setActiveTxId(txId);
    } finally {
      setLoading(false);
    }
  };

  const createFallbackReport = (txId) => {
    return {
      transaction_id: txId,
      ledger_bank: 'SBI',
      generated_at: new Date().toLocaleString() + ' IST',
      transaction_metadata: {
        amount: 250000,
        timestamp: new Date().toISOString(),
        type: 'IMPS',
        device_ip: 'Mobile:192.168.1.105',
        location: 'Bengaluru',
        recipient_is_new: true,
        transaction_status: 'RESTRICTED',
        honeypot_status: 'TRANSFERRED',
        lien_status: 'LIEN_APPLIED',
      },
      parties: {
        sender: {
          account_id: 'SBI-00124',
          bank: 'SBI',
          name: 'Arjun Kumar',
          account_type: 'SAVINGS',
          current_balance: 450000,
          risk_score: 82.5,
          risk_level: 'CRITICAL',
          factors: ['Rapid forwarding burst detected', 'Counterparty is new entity', 'Drains 85% of balance'],
        },
        receiver: {
          account_id: 'AXIS-00892',
          bank: 'AXIS',
          name: 'Sneha Desai Retail Traders',
          account_type: 'CURRENT',
          current_balance: 1450000,
          unencumbered_balance: 1200000,
          risk_score: 18.0,
          risk_level: 'LOW',
          is_genuine_account: true,
          factors: ['Established merchant baseline (540 days old)', 'Low historical risk (<20)', 'KYC Fully Verified'],
        },
      },
      reinforcement_learning: {
        action: 'STOP_INVESTIGATION_GENUINE_RECIPIENT',
        confidence: 0.96,
        reward: 15.0,
        policy_rationale:
          'Terminal Genuine Boundary Reached: Recipient account is verified as a legitimate merchant (KYC verified, established baseline, risk 18.0). RL Agent halted graph expansion to protect normal economic trade. Targeted Inward Lien of ₹2,50,000 applied strictly to disputed funds, leaving remaining ₹12,00,000 unencumbered balance 100% active.',
      },
      lien_protection: {
        is_protected: true,
        lien_status: 'LIEN_APPLIED',
        protected_amount: 250000,
        affected_account: 'AXIS-00892',
        unencumbered_balance: 1200000,
        legal_basis: 'PMLA Sec 12A & ADSL Consensus Safeguard Protocol',
      },
    };
  };

  const handlePrintDossier = () => {
    if (!reportData) return;
    const printWindow = window.open('', '_blank', 'width=950,height=850');
    if (!printWindow) return;

    const rep = reportData;
    const s = rep.parties?.sender || {};
    const r = rep.parties?.receiver || {};
    const m = rep.transaction_metadata || {};
    const rl = rep.reinforcement_learning || {};
    const ln = rep.lien_protection || {};

    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>ADSL Institutional Forensic Investigation Report — ${rep.transaction_id}</title>
        <style>
          @page { size: A4; margin: 15mm; }
          body { font-family: 'Segoe UI', Arial, sans-serif; color: #0F172A; margin: 0; padding: 20px; font-size: 13px; line-height: 1.5; }
          .header { border-bottom: 2px solid #0F172A; padding-bottom: 12px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: flex-start; }
          .title { font-size: 20px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.04em; }
          .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 10px; text-transform: uppercase; }
          .badge-critical { background: #FEE2E2; color: #991B1B; border: 1px solid #F87171; }
          .badge-low { background: #DCFCE7; color: #166534; border: 1px solid #4ADE80; }
          .watermark { position: fixed; top: 40%; left: 15%; font-size: 60px; color: rgba(203, 213, 225, 0.22); transform: rotate(-30deg); font-weight: 900; z-index: -1; pointer-events: none; }
          .section-title { font-size: 12px; font-weight: 800; text-transform: uppercase; color: #1E293B; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin: 16px 0 10px; }
          .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 12px; }
          .card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px; }
          .card-title { font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 8px; }
          .row { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 11px; }
          .row-label { color: #64748B; font-weight: 600; }
          .row-val { font-weight: 700; color: #0F172A; }
          .rl-box { background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A; border-radius: 6px; padding: 12px; margin-top: 14px; font-size: 11px; }
          .lien-box { background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid #DC2626; border-radius: 6px; padding: 12px; margin-top: 14px; font-size: 11px; }
          .flow-diagram { background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 6px; padding: 12px; display: flex; justify-content: space-around; align-items: center; margin: 14px 0; }
          .flow-node { text-align: center; }
          .flow-arrow { font-size: 18px; color: #64748B; font-weight: 800; }
          .sign-block { margin-top: 36px; display: flex; justify-content: space-between; }
          .sign-line { width: 220px; border-top: 1px solid #475569; text-align: center; padding-top: 6px; font-size: 10px; font-weight: 700; }
          @media print { body { padding: 0; } .no-print { display: none; } }
        </style>
      </head>
      <body>
        <div class="watermark">ADSL FORENSIC AUDIT</div>
        <div class="header">
          <div>
            <div class="title">Institutional Forensic Transaction Dossier</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">
              Autonomous Decentralized Security Layer (ADSL) Consortium • Multi-Bank Core Audit
            </div>
          </div>
          <div style="text-align: right;">
            <div class="badge" style="background:#0F172A; color:#fff;">OFFICIAL AUDIT REPORT</div>
            <div style="font-size: 10px; color: #64748B; margin-top: 4px;">Case Ref: ADSL-TX-${rep.transaction_id}</div>
            <div style="font-size: 10px; color: #64748B;">Date: ${rep.generated_at}</div>
          </div>
        </div>

        <div class="flow-diagram">
          <div class="flow-node">
            <div style="font-size: 9px; font-weight: 700; color: #64748B; text-transform: uppercase;">Origin / Source</div>
            <div style="font-weight: 800; color: #0F172A; font-family: monospace;">${s.account_id}</div>
            <div style="font-size: 10px; color: #DC2626; font-weight: 700;">Risk: ${s.risk_score} [${s.risk_level}]</div>
          </div>
          <div class="flow-arrow">➔</div>
          <div class="flow-node">
            <div style="font-size: 9px; font-weight: 700; color: #64748B; text-transform: uppercase;">Transfer Channel</div>
            <div style="font-weight: 800; color: #2563EB; font-family: monospace;">₹${Number(m.amount).toLocaleString()}</div>
            <div style="font-size: 10px; color: #475569;">${m.type} • Status: ${m.transaction_status}</div>
          </div>
          <div class="flow-arrow">➔</div>
          <div class="flow-node">
            <div style="font-size: 9px; font-weight: 700; color: #64748B; text-transform: uppercase;">Terminal Recipient</div>
            <div style="font-weight: 800; color: #0F172A; font-family: monospace;">${r.account_id}</div>
            <div style="font-size: 10px; color: #16A34A; font-weight: 700;">${r.is_genuine_account ? 'GENUINE RECIPIENT' : 'UNDER SURVEILLANCE'}</div>
          </div>
        </div>

        <div class="section-title">Parties &amp; KYC Risk Profiling</div>
        <div class="grid-2">
          <div class="card">
            <div class="card-title">Originating Entity (Sender)</div>
            <div class="row"><span class="row-label">Account ID:</span><span class="row-val">${s.account_id} (${s.bank} Bank)</span></div>
            <div class="row"><span class="row-label">Entity Name:</span><span class="row-val">${s.name}</span></div>
            <div class="row"><span class="row-label">Account Type:</span><span class="row-val">${s.account_type}</span></div>
            <div class="row"><span class="row-label">Ledger Balance:</span><span class="row-val">₹${Number(s.current_balance).toLocaleString()}</span></div>
            <div class="row"><span class="row-label">Assessed Risk Score:</span><span class="row-val" style="color:#DC2626;">${s.risk_score} / 100</span></div>
            <div style="margin-top: 6px; font-size: 10px; color: #475569;">
              <strong>Risk Anomaly Flags:</strong>
              <ul style="margin: 4px 0 0 16px; padding: 0;">
                ${(s.factors || []).map(f => `<li>${f}</li>`).join('')}
              </ul>
            </div>
          </div>

          <div class="card">
            <div class="card-title">Beneficiary Entity (Receiver)</div>
            <div class="row"><span class="row-label">Account ID:</span><span class="row-val">${r.account_id} (${r.bank} Bank)</span></div>
            <div class="row"><span class="row-label">Entity Name:</span><span class="row-val">${r.name}</span></div>
            <div class="row"><span class="row-label">Account Type:</span><span class="row-val">${r.account_type}</span></div>
            <div class="row"><span class="row-label">Ledger Balance:</span><span class="row-val">₹${Number(r.current_balance).toLocaleString()}</span></div>
            <div class="row"><span class="row-label">Unencumbered Bal:</span><span class="row-val" style="color:#16A34A; font-weight:800;">₹${Number(r.unencumbered_balance).toLocaleString()}</span></div>
            <div class="row"><span class="row-label">Assessed Risk Score:</span><span class="row-val" style="color:#16A34A;">${r.risk_score} / 100 [${r.risk_level}]</span></div>
            <div style="margin-top: 6px; font-size: 10px; color: #475569;">
              <strong>Verification Baseline:</strong>
              <ul style="margin: 4px 0 0 16px; padding: 0;">
                ${(r.factors || []).map(f => `<li>${f}</li>`).join('')}
              </ul>
            </div>
          </div>
        </div>

        <div class="rl-box">
          <div style="font-weight: 800; text-transform: uppercase; color: #166534; margin-bottom: 4px; display:flex; justify-content:space-between;">
            <span>Reinforcement Learning (RL) Policy Decision: ${rl.action}</span>
            <span>Confidence: ${(rl.confidence * 100).toFixed(0)}%</span>
          </div>
          <div>${rl.policy_rationale}</div>
        </div>

        <div class="lien-box">
          <div style="font-weight: 800; text-transform: uppercase; color: #991B1B; margin-bottom: 4px; display:flex; justify-content:space-between;">
            <span>Controlled Funds &amp; Lien Layer Receipt: ${ln.lien_status}</span>
            <span>Protected Amount: ₹${Number(ln.protected_amount).toLocaleString()}</span>
          </div>
          <div>
            <strong>Funds Protection Directive:</strong> Disputed transaction capital of ₹${Number(ln.protected_amount).toLocaleString()} is held in escrow under autonomous lien on account ${ln.affected_account}.
            In compliance with customer safeguard policies, the customer's legitimate remaining balance of ₹${Number(ln.unencumbered_balance).toLocaleString()} is 100% active and unencumbered.
          </div>
        </div>

        <div class="sign-block">
          <div class="sign-line">
            Autonomous Graph Forensics Engine<br>System Verification Stamp
          </div>
          <div class="sign-line">
            Head of Financial Crime Compliance<br>Institutional Sign-Off
          </div>
        </div>

        <div class="no-print" style="margin-top: 25px; text-align: center;">
          <button onclick="window.print()" style="padding: 10px 24px; font-weight: 700; background: #2563EB; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">
            Print / Save Dossier as PDF
          </button>
        </div>
      </body>
      </html>
    `;

    printWindow.document.open();
    printWindow.document.write(html);
    printWindow.document.close();
  };

  const rep = reportData;
  const s = rep?.parties?.sender || {};
  const r = rep?.parties?.receiver || {};
  const m = rep?.transaction_metadata || {};
  const rl = rep?.reinforcement_learning || {};
  const ln = rep?.lien_protection || {};

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20, color: '#F8FAFC' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              background: 'rgba(59, 130, 246, 0.15)',
              border: '1px solid rgba(59, 130, 246, 0.35)',
              borderRadius: 8,
              padding: '6px 8px',
              display: 'flex',
            }}>
              <GitFork size={20} color="#60A5FA" />
            </div>
            <h1 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 800, letterSpacing: '0.01em' }}>
              Transaction Graph Forensics &amp; RL Dossier
            </h1>
          </div>
          <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: '#94A3B8' }}>
            Multi-hop provenance analysis, Left-to-Right stage flow visualization, and RL boundary-stopping verification.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button
            onClick={handlePrintDossier}
            style={{
              padding: '8px 16px',
              background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: 7,
              fontWeight: 700,
              fontSize: '0.82rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: '0 4px 14px rgba(37,99,235,0.3)',
            }}
          >
            <Printer size={15} />
            <span>Generate Forensic Report (PDF)</span>
          </button>
        </div>
      </div>

      {/* Search & Transaction Selector */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.65)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 8,
        padding: '12px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 280 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'rgba(0,0,0,0.35)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 6,
            padding: '6px 12px',
            gap: 8,
            width: '100%',
            maxWidth: 400,
          }}>
            <Search size={14} color="#94A3B8" />
            <input
              type="text"
              placeholder="Enter Transaction ID (e.g. TX-..., SBI-..., MULE-...)"
              value={searchTx}
              onChange={(e) => setSearchTx(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') loadForensicDossier(searchTx.trim());
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#fff',
                fontSize: '0.82rem',
                outline: 'none',
                width: '100%',
              }}
            />
          </div>
          <button
            onClick={() => loadForensicDossier(searchTx.trim())}
            style={{
              padding: '6px 14px',
              background: '#3B82F6',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              fontWeight: 700,
              fontSize: '0.8rem',
              cursor: 'pointer',
            }}
          >
            Inspect
          </button>
        </div>

        {/* Quick select pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflowX: 'auto' }}>
          <span style={{ fontSize: '0.72rem', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase' }}>Recent:</span>
          {recentTransactions.slice(0, 5).map((t) => (
            <button
              key={t.transaction_id}
              onClick={() => {
                setSearchTx(t.transaction_id);
                loadForensicDossier(t.transaction_id);
              }}
              style={{
                padding: '3px 8px',
                background: activeTxId === t.transaction_id ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255,255,255,0.04)',
                border: activeTxId === t.transaction_id ? '1px solid #3B82F6' : '1px solid rgba(255,255,255,0.08)',
                color: activeTxId === t.transaction_id ? '#93C5FD' : '#94A3B8',
                borderRadius: 4,
                fontSize: '0.7rem',
                fontFamily: 'monospace',
                cursor: 'pointer',
              }}
            >
              {t.transaction_id}
            </button>
          ))}
        </div>
      </div>

      {/* Main Forensic Viewport */}
      {rep ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          {/* 1. Hierarchical Flow Graph Canvas */}
          <div style={{
            background: 'rgba(11, 15, 25, 0.85)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 12,
            padding: '20px 24px',
            position: 'relative',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#3B82F6' }}>
                  Stage Flow Architecture
                </span>
                <h3 style={{ margin: '2px 0 0', fontSize: '1.05rem', fontWeight: 700 }}>
                  Directed Multi-Hop Fund Provenance Flow
                </h3>
              </div>

              {/* Zoom Controls */}
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <button
                  onClick={() => setZoomLevel((z) => Math.max(0.7, z - 0.1))}
                  style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: 4, cursor: 'pointer' }}
                >
                  <ZoomOut size={13} />
                </button>
                <span style={{ fontSize: '0.72rem', fontFamily: 'monospace', color: '#94A3B8' }}>{(zoomLevel * 100).toFixed(0)}%</span>
                <button
                  onClick={() => setZoomLevel((z) => Math.min(1.4, z + 0.1))}
                  style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: 4, cursor: 'pointer' }}
                >
                  <ZoomIn size={13} />
                </button>
                <button
                  onClick={() => setZoomLevel(1)}
                  style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: 4, cursor: 'pointer' }}
                >
                  <Maximize2 size={13} />
                </button>
              </div>
            </div>

            {/* Stage Indicators */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              paddingBottom: 10,
              marginBottom: 20,
              textAlign: 'center',
              fontSize: '0.7rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}>
              <div style={{ color: '#3B82F6' }}>Stage 1: Source Inflow</div>
              <div style={{ color: '#F97316' }}>Stage 2: Layering / Relays</div>
              <div style={{ color: '#EF4444' }}>Stage 3: Mule Concentration</div>
              <div style={{ color: '#10B981' }}>Stage 4: Extraction / Genuine Sink</div>
            </div>

            {/* Interactive SVG Flow Canvas */}
            <div style={{ overflowX: 'auto', display: 'flex', justifyContent: 'center' }}>
              <div style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top center', transition: 'transform 0.2s ease' }}>
                <svg width="1020" height="280" viewBox="0 0 1020 280" style={{ overflow: 'visible' }}>
                  <defs>
                    <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8" />
                      <stop offset="50%" stopColor="#F97316" stopOpacity="0.9" />
                      <stop offset="100%" stopColor="#10B981" stopOpacity="0.8" />
                    </linearGradient>

                    <marker id="arrow" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#F59E0B" />
                    </marker>
                    <marker id="arrow-green" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#10B981" />
                    </marker>
                  </defs>

                  {/* Flow Paths */}
                  <path
                    d="M 160 140 C 260 140, 310 100, 410 100"
                    fill="none"
                    stroke="#F97316"
                    strokeWidth="3"
                    strokeDasharray="6,4"
                    markerEnd="url(#arrow)"
                  />
                  <path
                    d="M 410 100 C 510 100, 560 140, 660 140"
                    fill="none"
                    stroke="#EF4444"
                    strokeWidth="3.5"
                    strokeDasharray="6,4"
                    markerEnd="url(#arrow)"
                  />
                  <path
                    d="M 660 140 C 760 140, 810 140, 910 140"
                    fill="none"
                    stroke="#10B981"
                    strokeWidth="3.5"
                    markerEnd="url(#arrow-green)"
                  />

                  {/* Animated Transfer Badge along central edge */}
                  <g transform="translate(785, 125)">
                    <rect x="-45" y="-12" width="90" height="24" rx="12" fill="rgba(16,185,129,0.2)" stroke="#10B981" strokeWidth="1.2" />
                    <text x="0" y="4" textAnchor="middle" fill="#34D399" fontSize="10" fontWeight="800" fontFamily="monospace">
                      ₹{Number(m.amount).toLocaleString()}
                    </text>
                  </g>

                  {/* Node 1: Origin Source (x=160, y=140) */}
                  <g transform="translate(160, 140)" style={{ cursor: 'pointer' }} onClick={() => setSelectedNode('SOURCE')}>
                    <circle r="36" fill="rgba(59, 130, 246, 0.15)" stroke="#3B82F6" strokeWidth="2.5" />
                    <circle r="18" fill="rgba(59, 130, 246, 0.3)" />
                    <text y="4" textAnchor="middle" fill="#FFFFFF" fontSize="11" fontWeight="800">SRC</text>
                    <text y="50" textAnchor="middle" fill="#E2E8F0" fontSize="11" fontWeight="700" fontFamily="monospace">{s.account_id || 'SRC-01'}</text>
                    <text y="64" textAnchor="middle" fill="#64748B" fontSize="9">{s.bank} Bank</text>
                  </g>

                  {/* Node 2: Smurfing Forwarder (x=410, y=100) */}
                  <g transform="translate(410, 100)" style={{ cursor: 'pointer' }} onClick={() => setSelectedNode('FORWARDER')}>
                    <circle r="32" fill="rgba(249, 115, 22, 0.15)" stroke="#F97316" strokeWidth="2.2" />
                    <circle r="16" fill="rgba(249, 115, 22, 0.3)" />
                    <text y="4" textAnchor="middle" fill="#FFFFFF" fontSize="10" fontWeight="800">RLY</text>
                    <text y="46" textAnchor="middle" fill="#E2E8F0" fontSize="10" fontWeight="700" fontFamily="monospace">RLY-FWD</text>
                    <text y="58" textAnchor="middle" fill="#F97316" fontSize="9">Smurfing Hub</text>
                  </g>

                  {/* Node 3: Primary Mule Node (x=660, y=140) */}
                  <g transform="translate(660, 140)" style={{ cursor: 'pointer' }} onClick={() => setSelectedNode('MULE')}>
                    <circle r="40" fill="rgba(239, 68, 68, 0.18)" stroke="#EF4444" strokeWidth="3" />
                    <circle r="22" fill="rgba(239, 68, 68, 0.35)" />
                    <text y="4" textAnchor="middle" fill="#FFFFFF" fontSize="11" fontWeight="800">MULE</text>
                    <text y="54" textAnchor="middle" fill="#E2E8F0" fontSize="11" fontWeight="700" fontFamily="monospace">{s.account_id}</text>
                    <text y="68" textAnchor="middle" fill="#EF4444" fontSize="9" fontWeight="700">Flagged Mule</text>
                  </g>

                  {/* Node 4: Terminal Genuine Beneficiary (x=910, y=140) */}
                  <g transform="translate(910, 140)" style={{ cursor: 'pointer' }} onClick={() => setSelectedNode('BENEFICIARY')}>
                    <circle r="42" fill="rgba(16, 185, 129, 0.18)" stroke="#10B981" strokeWidth="3" />
                    <circle r="24" fill="rgba(16, 185, 129, 0.35)" />
                    <text y="4" textAnchor="middle" fill="#FFFFFF" fontSize="11" fontWeight="800">SINK</text>
                    <text y="56" textAnchor="middle" fill="#E2E8F0" fontSize="11" fontWeight="700" fontFamily="monospace">{r.account_id}</text>
                    <text y="70" textAnchor="middle" fill="#10B981" fontSize="9" fontWeight="800">Genuine Beneficiary</text>
                  </g>
                </svg>
              </div>
            </div>
          </div>

          {/* 2. Reinforcement Learning (RL) Policy Intelligence Box */}
          <div style={{
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderLeft: '5px solid #10B981',
            borderRadius: 10,
            padding: '18px 24px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <BrainCircuit size={20} color="#10B981" />
                <span style={{ fontSize: '0.92rem', fontWeight: 800, color: '#34D399', letterSpacing: '0.02em', textTransform: 'uppercase' }}>
                  Reinforcement Learning (RL) Agent Action: {rl.action || 'STOP_INVESTIGATION_GENUINE_RECIPIENT'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <span style={{ fontSize: '0.74rem', background: 'rgba(16, 185, 129, 0.2)', color: '#6EE7B7', padding: '3px 8px', borderRadius: 4, fontWeight: 700 }}>
                  Confidence: {((rl.confidence || 0.96) * 100).toFixed(0)}%
                </span>
                <span style={{ fontSize: '0.74rem', background: 'rgba(59, 130, 246, 0.2)', color: '#93C5FD', padding: '3px 8px', borderRadius: 4, fontWeight: 700 }}>
                  Reward: +{rl.reward || 15.0} pts
                </span>
              </div>
            </div>
            <p style={{ margin: 0, fontSize: '0.84rem', color: '#E2E8F0', lineHeight: 1.5 }}>
              {rl.policy_rationale ||
                'Terminal Genuine Boundary Reached: Recipient account is verified as a legitimate merchant / citizen. RL Agent halted graph expansion to protect normal economic trade. Targeted Inward Lien applied strictly to the disputed transfer funds, preserving 100% of customer unencumbered balance.'}
            </p>
          </div>

          {/* 3. Detailed Account Dossier Split View */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 16 }}>
            {/* Origin Entity */}
            <div style={{
              background: 'rgba(15, 23, 42, 0.75)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: 10,
              padding: '18px 20px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 10, marginBottom: 12 }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', color: '#F87171' }}>Originating Sender Entity</span>
                <span style={{ fontSize: '0.72rem', background: 'rgba(239, 68, 68, 0.18)', color: '#F87171', padding: '2px 8px', borderRadius: 4, fontWeight: 800 }}>
                  Risk Score: {s.risk_score || 82.5}
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.82rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Account ID:</span>
                  <span style={{ fontFamily: 'monospace', fontWeight: 700 }}>{s.account_id} ({s.bank} Bank)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Account Holder:</span>
                  <span style={{ fontWeight: 600 }}>{s.name}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Account Type:</span>
                  <span>{s.account_type}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Ledger Balance:</span>
                  <span style={{ fontFamily: 'monospace' }}>₹{Number(s.current_balance || 0).toLocaleString()}</span>
                </div>
              </div>

              <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase' }}>Behavioural Anomaly Indicators:</span>
                <ul style={{ margin: '6px 0 0 16px', padding: 0, fontSize: '0.78rem', color: '#FCA5A5', lineHeight: 1.4 }}>
                  {(s.factors || ['Velocity burst over 1h window', 'Rapid balance drainage ratio']).map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recipient Entity */}
            <div style={{
              background: 'rgba(15, 23, 42, 0.75)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              borderRadius: 10,
              padding: '18px 20px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 10, marginBottom: 12 }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', color: '#34D399' }}>Terminal Beneficiary Entity</span>
                <span style={{ fontSize: '0.72rem', background: 'rgba(16, 185, 129, 0.18)', color: '#34D399', padding: '2px 8px', borderRadius: 4, fontWeight: 800 }}>
                  Genuine Beneficiary (Risk: {r.risk_score || 18.0})
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.82rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Account ID:</span>
                  <span style={{ fontFamily: 'monospace', fontWeight: 700 }}>{r.account_id} ({r.bank} Bank)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Customer / Business:</span>
                  <span style={{ fontWeight: 600 }}>{r.name}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Total Ledger Balance:</span>
                  <span style={{ fontFamily: 'monospace' }}>₹{Number(r.current_balance || 0).toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Protected Lien Amount:</span>
                  <span style={{ fontFamily: 'monospace', color: '#F87171', fontWeight: 700 }}>₹{Number(ln.protected_amount || m.amount).toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94A3B8' }}>Unencumbered Usable Bal:</span>
                  <span style={{ fontFamily: 'monospace', color: '#34D399', fontWeight: 800 }}>₹{Number(r.unencumbered_balance || 0).toLocaleString()}</span>
                </div>
              </div>

              <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase' }}>Beneficiary Legitimate Baseline:</span>
                <ul style={{ margin: '6px 0 0 16px', padding: 0, fontSize: '0.78rem', color: '#A7F3D0', lineHeight: 1.4 }}>
                  {(r.factors || ['Established merchant commercial entity', 'KYC fully compliant & verified', 'Low historical risk (<20)']).map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8' }}>
          Select or enter a transaction ID above to view its forensic stage flow and dossier.
        </div>
      )}
    </div>
  );
}
