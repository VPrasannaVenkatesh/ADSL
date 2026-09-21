import React, { useState, useEffect, useMemo } from 'react';
import {
  Lock,
  Unlock,
  ShieldAlert,
  ShieldCheck,
  Search,
  RefreshCw,
  Printer,
  FileText,
  AlertCircle,
  Building2,
  DollarSign,
  UserCheck,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Filter,
} from 'lucide-react';

export function LienLayerTab() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({ summary: {}, records: [] });
  const [search, setSearch] = useState('');
  const [bankFilter, setBankFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(null);

  const fetchLienData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/adsl/lien/overview');
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error('Failed to fetch lien records:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLienData();
    const timer = setInterval(fetchLienData, 4000);
    return () => clearInterval(timer);
  }, []);

  const handleReleaseLien = async (record) => {
    if (!record || !record.transaction_id) return;
    if (!window.confirm(`Confirm Release of Lien for Account ${record.account_id} (Tx: ${record.transaction_id})?`)) {
      return;
    }
    setActionLoading(true);
    try {
      const res = await fetch(`/api/adsl/review/${record.transaction_id}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'RELEASE',
          investigator_id: 'COMPLIANCE_HEAD_01',
          notes: 'Lien cleared after genuine beneficiary identity and provenance verification.',
        }),
      });
      if (res.ok) {
        setActionSuccess(`Lien on ${record.account_id} released successfully! Funds unencumbered.`);
        fetchLienData();
        setTimeout(() => setActionSuccess(null), 4000);
      }
    } catch (err) {
      console.error('Error releasing lien:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handlePrintDossier = (record = null) => {
    const printWindow = window.open('', '_blank', 'width=900,height=800');
    if (!printWindow) return;

    const targetList = record ? [record] : data.records.slice(0, 30);
    const totalVal = record ? record.protected_amount : (data.summary.total_protected_funds || 0);

    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>ADSL Institutional Lien Audit Dossier</title>
        <style>
          @page { size: A4; margin: 16mm; }
          body { font-family: 'Segoe UI', Arial, sans-serif; color: #0F172A; margin: 0; padding: 20px; font-size: 13px; line-height: 1.5; }
          .header { border-bottom: 2px solid #1E293B; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; }
          .title { font-size: 20px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.05em; }
          .subtitle { font-size: 11px; color: #64748B; font-weight: 600; margin-top: 4px; }
          .badge { display: inline-block; padding: 4px 10px; background: #EEF2F6; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: 700; font-size: 11px; }
          .watermark { position: fixed; top: 40%; left: 20%; font-size: 55px; color: rgba(203, 213, 225, 0.28); transform: rotate(-30deg); font-weight: 900; z-index: -1; pointer-events: none; }
          .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
          .summary-card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px; }
          .summary-label { font-size: 10px; text-transform: uppercase; font-weight: 700; color: #64748B; }
          .summary-val { font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 4px; font-family: 'Consolas', monospace; }
          table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px; }
          th { background: #F1F5F9; text-align: left; padding: 8px 10px; border: 1px solid #CBD5E1; font-weight: 700; text-transform: uppercase; font-size: 10px; color: #334155; }
          td { padding: 8px 10px; border: 1px solid #E2E8F0; vertical-align: top; }
          tr:nth-child(even) { background: #F8FAFC; }
          .status-active { color: #DC2626; font-weight: 700; }
          .status-released { color: #16A34A; font-weight: 700; }
          .legal-notice { margin-top: 30px; border-top: 1px dashed #CBD5E1; padding-top: 15px; font-size: 10px; color: #64748B; }
          .sign-block { margin-top: 40px; display: flex; justify-content: space-between; }
          .sign-line { width: 220px; border-top: 1px solid #475569; text-align: center; padding-top: 6px; font-size: 10px; font-weight: 700; }
          @media print {
            body { padding: 0; }
            .no-print { display: none; }
          }
        </style>
      </head>
      <body>
        <div class="watermark">ADSL OFFICIAL COMPLIANCE</div>
        <div class="header">
          <div>
            <div class="title">Controlled Funds &amp; Lien Enforcement Dossier</div>
            <div class="subtitle">Inter-Bank Autonomous Security Consortium (SBI • AXIS • IOB) | PMLA Sec 12A Certified</div>
          </div>
          <div style="text-align: right;">
            <div class="badge">SECURITY CLASSIFICATION: CONFIDENTIAL</div>
            <div style="font-size: 10px; color: #64748B; margin-top: 4px;">Dossier Ref: ADSL-LN-${Date.now().toString().slice(-6)}</div>
            <div style="font-size: 10px; color: #64748B;">Generated: ${new Date().toLocaleString()}</div>
          </div>
        </div>

        <div class="summary-grid">
          <div class="summary-card">
            <div class="summary-label">Total Protected Funds</div>
            <div class="summary-val" style="color: #DC2626;">₹${Number(totalVal).toLocaleString()}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Active Protected Liens</div>
            <div class="summary-val">${data.summary.active_liens_count || targetList.length}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Accounts Under Protection</div>
            <div class="summary-val">${data.summary.accounts_protected_count || 1}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Released Liens</div>
            <div class="summary-val" style="color: #16A34A;">${data.summary.released_liens_count || 0}</div>
          </div>
        </div>

        <div style="font-weight: 800; font-size: 13px; text-transform: uppercase; margin-bottom: 6px; color: #1E293B;">
          Protected Fund Records &amp; Balance Breakdown
        </div>
        <table>
          <thead>
            <tr>
              <th>Account ID / Bank</th>
              <th>Customer / Entity</th>
              <th>Protected Lien (INR)</th>
              <th>Current Ledger Bal</th>
              <th>Unencumbered Bal</th>
              <th>Linked Transaction</th>
              <th>Restriction Status</th>
              <th>Quarantine Reason</th>
            </tr>
          </thead>
          <tbody>
            ${targetList.map(r => `
              <tr>
                <td><strong>${r.account_id}</strong><br><span style="color:#64748B;">${r.bank} Bank</span></td>
                <td>${r.customer_name}<br><span style="color:#64748B; font-size:9px;">${r.account_type}</span></td>
                <td style="font-weight:800; color:#DC2626; font-family:monospace;">₹${Number(r.protected_amount).toLocaleString()}</td>
                <td style="font-family:monospace;">₹${Number(r.current_balance).toLocaleString()}</td>
                <td style="font-family:monospace; font-weight:700; color:#16A34A;">₹${Number(r.unencumbered_balance).toLocaleString()}</td>
                <td style="font-family:monospace; font-size:10px;">${r.transaction_id}</td>
                <td><span class="${r.is_active ? 'status-active' : 'status-released'}">${r.status}</span></td>
                <td style="font-size:10px; color:#475569;">${r.restriction_reason}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <div class="legal-notice">
          <strong>LEGAL MANDATE &amp; SAFEGUARD PROTOCOL:</strong> The above funds have been ring-fenced under Autonomous Controlled Lien directives to mitigate mule network extraction and illicit asset dissipation. Notice is given pursuant to Inter-Bank Consortium Consensus. Unencumbered balances remain fully available for normal commercial usage by bona fide account holders.
        </div>

        <div class="sign-block">
          <div class="sign-line">
            ADSL Autonomous Consensus Engine<br>Cryptographic System Seal
          </div>
          <div class="sign-line">
            Senior AML &amp; Compliance Officer<br>Institutional Sign-Off &amp; Audit Seal
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
    printWindow.document.write(htmlContent);
    printWindow.document.close();
  };

  const filteredRecords = useMemo(() => {
    return (data.records || []).filter((r) => {
      const matchSearch =
        !search ||
        r.account_id.toLowerCase().includes(search.toLowerCase()) ||
        r.transaction_id.toLowerCase().includes(search.toLowerCase()) ||
        (r.customer_name && r.customer_name.toLowerCase().includes(search.toLowerCase()));

      const matchBank = bankFilter === 'ALL' || r.bank === bankFilter;
      const matchStatus =
        statusFilter === 'ALL' ||
        (statusFilter === 'ACTIVE' && r.is_active) ||
        (statusFilter === 'RELEASED' && !r.is_active);

      return matchSearch && matchBank && matchStatus;
    });
  }, [data.records, search, bankFilter, statusFilter]);

  const summary = data.summary || {};

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20, color: '#F8FAFC' }}>
      {/* Top Banner & Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              borderRadius: 8,
              padding: '6px 8px',
              display: 'flex',
            }}>
              <Lock size={20} color="#F87171" />
            </div>
            <h1 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 800, letterSpacing: '0.01em' }}>
              Controlled Funds &amp; Lien Protection Layer
            </h1>
          </div>
          <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: '#94A3B8' }}>
            Real-time isolation of suspicious and mule-routed capital. Protects victim and disputed funds under legal lien without halting bona fide account activity.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button
            onClick={() => handlePrintDossier(null)}
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
            <span>Generate Official Report (PDF)</span>
          </button>

          <button
            onClick={fetchLienData}
            style={{
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.06)',
              color: '#E2E8F0',
              border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 7,
              fontWeight: 600,
              fontSize: '0.82rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: 8,
          padding: '12px 16px',
          color: '#34D399',
          fontSize: '0.85rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <CheckCircle2 size={16} />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
        <div style={{
          background: 'rgba(15, 23, 42, 0.75)',
          border: '1px solid rgba(239, 68, 68, 0.28)',
          borderLeft: '4px solid #EF4444',
          borderRadius: 10,
          padding: '16px 20px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase' }}>
            <span>Total Protected Capital</span>
            <DollarSign size={15} color="#EF4444" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#F87171', marginTop: 8, fontFamily: 'monospace' }}>
            ₹{Number(summary.total_protected_funds || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: 4 }}>
            Held under active encumbrance &amp; escrow
          </div>
        </div>

        <div style={{
          background: 'rgba(15, 23, 42, 0.75)',
          border: '1px solid rgba(245, 158, 11, 0.28)',
          borderLeft: '4px solid #F59E0B',
          borderRadius: 10,
          padding: '16px 20px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase' }}>
            <span>Active Liens Applied</span>
            <Lock size={15} color="#F59E0B" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#FBBF24', marginTop: 8, fontFamily: 'monospace' }}>
            {Number(summary.active_liens_count || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: 4 }}>
            Transactions quarantined by ADSL rule
          </div>
        </div>

        <div style={{
          background: 'rgba(15, 23, 42, 0.75)',
          border: '1px solid rgba(59, 130, 246, 0.28)',
          borderLeft: '4px solid #3B82F6',
          borderRadius: 10,
          padding: '16px 20px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase' }}>
            <span>Accounts Under Protection</span>
            <UserCheck size={15} color="#3B82F6" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#60A5FA', marginTop: 8, fontFamily: 'monospace' }}>
            {Number(summary.accounts_protected_count || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: 4 }}>
            Unencumbered balances remain functional
          </div>
        </div>

        <div style={{
          background: 'rgba(15, 23, 42, 0.75)',
          border: '1px solid rgba(16, 185, 129, 0.28)',
          borderLeft: '4px solid #10B981',
          borderRadius: 10,
          padding: '16px 20px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase' }}>
            <span>Released / Cleared Liens</span>
            <ShieldCheck size={15} color="#10B981" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34D399', marginTop: 8, fontFamily: 'monospace' }}>
            {Number(summary.released_liens_count || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: 4 }}>
            Fully restored after AML investigator review
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 260 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'rgba(0,0,0,0.3)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 6,
            padding: '6px 12px',
            gap: 8,
            width: '100%',
            maxWidth: 360,
          }}>
            <Search size={14} color="#94A3B8" />
            <input
              type="text"
              placeholder="Search by Account ID, Transaction ID, Name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
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
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Bank Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.78rem', color: '#94A3B8' }}>
            <Building2 size={14} />
            <span>Bank:</span>
            <select
              value={bankFilter}
              onChange={(e) => setBankFilter(e.target.value)}
              style={{
                background: 'rgba(0,0,0,0.4)',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: 5,
                color: '#fff',
                padding: '4px 8px',
                fontSize: '0.78rem',
              }}
            >
              <option value="ALL">All Banks</option>
              <option value="SBI">SBI</option>
              <option value="AXIS">AXIS</option>
              <option value="IOB">IOB</option>
            </select>
          </div>

          {/* Status Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.78rem', color: '#94A3B8' }}>
            <Filter size={14} />
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                background: 'rgba(0,0,0,0.4)',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: 5,
                color: '#fff',
                padding: '4px 8px',
                fontSize: '0.78rem',
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active Lien</option>
              <option value="RELEASED">Released</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Lien Records Table */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.75)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 10,
        overflow: 'hidden',
      }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 700, color: '#94A3B8', fontSize: '0.72rem', textTransform: 'uppercase' }}>Account / Bank</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 700, color: '#94A3B8', fontSize: '0.72rem', textTransform: 'uppercase' }}>Customer &amp; Type</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 700, color: '#94A3B8', fontSize: '0.72rem', textTransform: 'uppercase' }}>Protected Funds (Lien)</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 700, color: '#94A3B8', fontSize: '0.72rem', textTransform: 'uppercase' }}>Unencumbered Bal</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 700, color: '#94A3B8', fontSize: '0.72rem', textTransform: 'uppercase' }}>Transaction ID</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 700, color: '#94A3B8', fontSize: '0.72rem', textTransform: 'uppercase' }}>Restriction Reason</th>
                <th style={{ padding: '12px 16px', textAlign: 'center', fontWeight: 700, color: '#94A3B8', fontSize: '0.72rem', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: '12px 16px', textAlign: 'center', fontWeight: 700, color: '#94A3B8', fontSize: '0.72rem', textTransform: 'uppercase' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ padding: '36px', textAlign: 'center', color: '#94A3B8' }}>
                    {loading ? 'Loading protected lien data...' : 'No lien records found matching filters.'}
                  </td>
                </tr>
              ) : (
                filteredRecords.map((r) => (
                  <tr
                    key={r.transaction_id}
                    style={{
                      borderBottom: '1px solid rgba(255,255,255,0.04)',
                      background: r.is_active ? 'rgba(239, 68, 68, 0.02)' : 'transparent',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ fontWeight: 700, fontFamily: 'monospace', color: '#F1F5F9' }}>{r.account_id}</div>
                      <div style={{ fontSize: '0.7rem', color: '#94A3B8', marginTop: 2 }}>{r.bank} Bank</div>
                    </td>

                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ fontWeight: 600, color: '#E2E8F0' }}>{r.customer_name}</div>
                      <div style={{ fontSize: '0.7rem', color: '#64748B', marginTop: 2 }}>{r.account_type}</div>
                    </td>

                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <div style={{ fontWeight: 800, fontFamily: 'monospace', color: r.is_active ? '#F87171' : '#94A3B8', fontSize: '0.92rem' }}>
                        ₹{Number(r.protected_amount).toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.68rem', color: '#64748B', marginTop: 2 }}>
                        Total: ₹{Number(r.current_balance).toLocaleString()}
                      </div>
                    </td>

                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, fontFamily: 'monospace', color: '#34D399' }}>
                        ₹{Number(r.unencumbered_balance).toLocaleString()}
                      </div>
                      <div style={{ fontSize: '0.68rem', color: '#10B981', marginTop: 2 }}>
                        100% Unlocked
                      </div>
                    </td>

                    <td style={{ padding: '12px 16px' }}>
                      <span style={{
                        fontFamily: 'monospace',
                        fontSize: '0.76rem',
                        color: '#93C5FD',
                        background: 'rgba(59, 130, 246, 0.1)',
                        padding: '2px 6px',
                        borderRadius: 4,
                      }}>
                        {r.transaction_id}
                      </span>
                      {r.restricted_at && (
                        <div style={{ fontSize: '0.68rem', color: '#64748B', marginTop: 3 }}>
                          {new Date(r.restricted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      )}
                    </td>

                    <td style={{ padding: '12px 16px', maxWidth: 220 }}>
                      <div style={{ fontSize: '0.76rem', color: '#CBD5E1', lineHeight: 1.3 }}>
                        {r.restriction_reason}
                      </div>
                    </td>

                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                      <span style={{
                        fontSize: '0.68rem',
                        fontWeight: 800,
                        padding: '3px 8px',
                        borderRadius: 4,
                        letterSpacing: '0.04em',
                        background: r.is_active ? 'rgba(239, 68, 68, 0.18)' : 'rgba(16, 185, 129, 0.18)',
                        color: r.is_active ? '#F87171' : '#34D399',
                        border: r.is_active ? '1px solid rgba(239, 68, 68, 0.35)' : '1px solid rgba(16, 185, 129, 0.35)',
                      }}>
                        {r.status}
                      </span>
                    </td>

                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: 6, justifyContent: 'center' }}>
                        {r.is_active && (
                          <button
                            onClick={() => handleReleaseLien(r)}
                            disabled={actionLoading}
                            title="Clear lien after verified review"
                            style={{
                              padding: '4px 8px',
                              background: 'rgba(16, 185, 129, 0.15)',
                              border: '1px solid rgba(16, 185, 129, 0.4)',
                              borderRadius: 5,
                              color: '#34D399',
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 4,
                            }}
                          >
                            <Unlock size={12} />
                            <span>Release</span>
                          </button>
                        )}
                        <button
                          onClick={() => handlePrintDossier(r)}
                          title="Generate printable PDF audit receipt"
                          style={{
                            padding: '4px 8px',
                            background: 'rgba(255,255,255,0.06)',
                            border: '1px solid rgba(255,255,255,0.12)',
                            borderRadius: 5,
                            color: '#E2E8F0',
                            fontSize: '0.72rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                          }}
                        >
                          <FileText size={12} />
                          <span>PDF</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
