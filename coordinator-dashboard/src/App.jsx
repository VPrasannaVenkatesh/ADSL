import React, { useState, useEffect, useCallback } from 'react';
import { SummaryCards } from './components/SummaryCards';
import { CoordinationTable } from './components/CoordinationTable';
import { CoordinationDrawer } from './components/CoordinationDrawer';
import { TopologyView } from './components/TopologyView';
import { InvestigationView } from './components/InvestigationView';
import { MuleNetworksView } from './components/MuleNetworksView';
import { AdslUnifiedDashboard } from './components/AdslUnifiedDashboard';
import { coordinatorApi } from './api';
import { Shield, RefreshCw, Wifi, WifiOff, Cpu, Search, Network, Layers, GitFork, LayoutDashboard } from 'lucide-react';

const POLL_MS = 1500; // Poll live decisions every 1.5 seconds

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'mule-networks' | 'coordination' | 'investigation'
  const [decisions, setDecisions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selected, setSelected] = useState(null);
  const [apiOnline, setApiOnline] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    document.title = 'ADSL DASHBOARD';
  }, []);

  const [filters, setFilters] = useState({
    bank: 'ALL',
    decision: '',
    risk_level: '',
    transaction_id: '',
    coordination_id: '',
  });

  const fetchData = useCallback(async () => {
    try {
      const [decisionsRes, summaryRes] = await Promise.all([
        coordinatorApi.getDecisions({
          bank: filters.bank,
          decision: filters.decision || undefined,
          risk_level: filters.risk_level || undefined,
          transaction_id: filters.transaction_id || undefined,
          coordination_id: filters.coordination_id || undefined,
          limit: 150,
        }),
        coordinatorApi.getSummary(filters.bank),
      ]);
      setDecisions(decisionsRes.decisions || []);
      setSummary(summaryRes);
      setApiOnline(true);
      setLastUpdated(new Date());
    } catch {
      setApiOnline(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, POLL_MS);
    return () => clearInterval(timer);
  }, [fetchData]);

  const handleSelect = async (row) => {
    if (selected?.coordination_id === row.coordination_id) {
      setSelected(null);
      return;
    }
    try {
      const detail = await coordinatorApi.getDetail(row.coordination_id);
      setSelected(detail);
    } catch {
      setSelected(row);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header */}
      <header style={{
        background: 'rgba(4,6,10,0.98)',
        borderBottom: '1px solid var(--border)',
        padding: '14px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{
          background: 'rgba(139, 92, 246, 0.18)',
          border: '1px solid rgba(139, 92, 246, 0.4)',
          borderRadius: 8,
          padding: '6px 8px',
          display: 'flex',
          alignItems: 'center',
        }}>
          <Cpu size={20} color="#A78BFA" />
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 900, fontSize: '1.05rem', letterSpacing: '0.01em', color: 'var(--text-primary)' }}>
            ADSL DASHBOARD
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 1 }}>
            Autonomous Decentralized Security Layer (ADSL) • Central Transaction Processing & Mule Forensics &nbsp;│&nbsp;
            Participating: <span style={{ color: '#3B82F6', fontWeight: 700 }}>SBI</span>, <span style={{ color: '#EC4899', fontWeight: 700 }}>AXIS</span>, <span style={{ color: '#F59E0B', fontWeight: 700 }}>IOB</span>
          </div>
        </div>

        {/* Tab View Switcher */}
        <div style={{
          display: 'flex',
          background: 'rgba(255, 255, 255, 0.05)',
          padding: 3,
          borderRadius: 8,
          border: '1px solid var(--border)',
          gap: 2,
        }}>
          <button
            onClick={() => setActiveTab('overview')}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.78rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: activeTab === 'overview' ? 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)' : 'transparent',
              color: activeTab === 'overview' ? '#fff' : 'var(--text-muted)',
              transition: 'all 0.15s ease',
            }}
          >
            <LayoutDashboard size={13} />
            <span>ADSL Overview</span>
          </button>

          <button
            onClick={() => setActiveTab('mule-networks')}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.78rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: activeTab === 'mule-networks' ? 'linear-gradient(135deg, #EF4444 0%, #F97316 100%)' : 'transparent',
              color: activeTab === 'mule-networks' ? '#fff' : 'var(--text-muted)',
              transition: 'all 0.15s ease',
            }}
          >
            <GitFork size={13} />
            <span>Mule Networks</span>
          </button>

          <button
            onClick={() => setActiveTab('coordination')}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.78rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: activeTab === 'coordination' ? 'linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%)' : 'transparent',
              color: activeTab === 'coordination' ? '#fff' : 'var(--text-muted)',
              transition: 'all 0.15s ease',
            }}
          >
            <Network size={13} />
            <span>Transaction Processing</span>
          </button>

          <button
            onClick={() => setActiveTab('investigation')}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.78rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: activeTab === 'investigation' ? 'rgba(59, 130, 246, 0.25)' : 'transparent',
              color: activeTab === 'investigation' ? '#60A5FA' : 'var(--text-muted)',
              border: activeTab === 'investigation' ? '1px solid #3B82F6' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            <Search size={13} />
            <span>Lien Layer & Forensics</span>
          </button>
        </div>

        {/* Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {apiOnline === null ? null : apiOnline ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--allow)' }}>
              <span className="live-dot" />
              <Wifi size={14} />
              <span>Coordinator Active</span>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--controlled-action)' }}>
              <WifiOff size={14} />
              <span>Coordinator Offline</span>
            </div>
          )}

          {lastUpdated && (
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
              Synced {lastUpdated.toLocaleTimeString('en-IN')}
            </span>
          )}

          <button
            className="btn btn-outline"
            onClick={fetchData}
            style={{ padding: '6px 12px', fontSize: '0.75rem' }}
          >
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      </header>

      {/* Offline Alert */}
      {apiOnline === false && (
        <div style={{
          background: 'rgba(239,68,68,0.12)',
          border: '1px solid rgba(239,68,68,0.35)',
          margin: '16px 24px 0',
          borderRadius: 10,
          padding: '12px 18px',
          fontSize: '0.82rem',
          color: '#FCA5A5',
        }}>
          <strong>Coordinator API not reachable.</strong> Ensure the Coordinator backend is running on port 8002.
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <AdslUnifiedDashboard
          onNavigateToGraph={() => setActiveTab('mule-networks')}
        />
      )}

      {activeTab === 'mule-networks' && (
        <MuleNetworksView />
      )}

      {activeTab === 'coordination' && (
        <>
          {/* Architecture Topology View */}
          <div style={{ marginTop: 18 }}>
            <TopologyView />
          </div>

          {/* KPI Summary Cards */}
          <div>
            <SummaryCards summary={summary} />
          </div>

          {/* Live Coordinated Decisions Table */}
          <main style={{ flex: 1 }}>
            <CoordinationTable
              decisions={decisions}
              selected={selected}
              onSelect={handleSelect}
              filters={filters}
              onFiltersChange={setFilters}
            />
          </main>

          {/* Audit Drawer */}
          {selected && (
            <CoordinationDrawer
              decision={selected}
              onClose={() => setSelected(null)}
            />
          )}
        </>
      )}

      {activeTab === 'investigation' && (
        <div style={{ marginTop: 20 }}>
          <InvestigationView />
        </div>
      )}

      {/* Footer */}
      <footer style={{
        padding: '12px 24px',
        borderTop: '1px solid var(--border)',
        fontSize: '0.72rem',
        color: 'var(--text-muted)',
        display: 'flex',
        justifyContent: 'space-between',
        background: 'rgba(4,6,10,0.95)',
        marginTop: 'auto',
      }}>
        <span>ADSL Autonomous Decentralized Security Layer — Central Decision & Mule Forensics Engine</span>
        <span>ADSL API: <code>localhost:8002</code> │ Bank Dashboard: <code>localhost:5174</code> │ Simulator: <code>localhost:5173</code></span>
      </footer>
    </div>
  );
}

