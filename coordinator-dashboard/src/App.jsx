import React, { useState, useEffect } from 'react';
import { AdslUnifiedDashboard } from './components/AdslUnifiedDashboard';
import { MuleNetworksView } from './components/MuleNetworksView';
import { LienLayerTab } from './components/LienLayerTab';
import { ForensicsTab } from './components/ForensicsTab';
import {
  Cpu,
  Wifi,
  WifiOff,
  LayoutDashboard,
  GitFork,
  RefreshCw,
  ShieldAlert,
  AlertTriangle,
  Network,
  Lock,
  Search,
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('mule-networks'); // 'overview' | 'mule-networks' | 'lien-layer' | 'forensics'
  const [muleSubTab, setMuleSubTab] = useState('medium'); // 'medium' | 'high' | 'all'
  const [apiOnline, setApiOnline] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  useEffect(() => {
    document.title = 'ADSL DASHBOARD';
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/coordinator/health');
      setApiOnline(res.ok);
      setLastUpdated(new Date());
    } catch {
      setApiOnline(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const timer = setInterval(checkHealth, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg, #04060A)' }}>
      {/* Top Header - Well-proportioned & Elegant */}
      <header style={{
        background: 'rgba(4,6,10,0.98)',
        borderBottom: '1px solid var(--border, rgba(255,255,255,0.08))',
        padding: '11px 24px',
        minHeight: '56px',
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        {/* Brand Block */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 11, flexShrink: 0 }}>
          <div style={{
            background: 'rgba(139, 92, 246, 0.18)',
            border: '1px solid rgba(139, 92, 246, 0.4)',
            borderRadius: 7,
            padding: '6px 8px',
            display: 'flex',
            alignItems: 'center',
          }}>
            <Cpu size={19} color="#A78BFA" />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <span style={{ fontWeight: 800, fontSize: '0.98rem', letterSpacing: '0.02em', color: '#F8FAFC', whiteSpace: 'nowrap' }}>
              ADSL CONSORTIUM
            </span>
            <span style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 5,
              background: 'rgba(59, 130, 246, 0.12)',
              color: '#60A5FA',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              whiteSpace: 'nowrap',
            }}>
              SBI • AXIS • IOB
            </span>
          </div>
        </div>

        {/* Tab View & Sub-Navigation Switcher */}
        <div style={{
          display: 'flex',
          background: 'rgba(255, 255, 255, 0.04)',
          padding: '3px 5px',
          borderRadius: 8,
          border: '1px solid rgba(255,255,255,0.08)',
          gap: 5,
          alignItems: 'center',
          flexShrink: 0,
        }}>
          {/* Central Overview Button */}
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
              color: activeTab === 'overview' ? '#fff' : '#94A3B8',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease',
            }}
          >
            <LayoutDashboard size={14} />
            <span>Central Overview</span>
          </button>

          <div style={{ width: 1, height: 18, background: 'rgba(255,255,255,0.1)' }} />

          {/* Mule Networks Navigation Group */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            background: activeTab === 'mule-networks' ? 'rgba(239, 68, 68, 0.08)' : 'transparent',
            padding: '3px 4px',
            borderRadius: 6,
            border: activeTab === 'mule-networks' ? '1px solid rgba(239, 68, 68, 0.25)' : '1px solid transparent',
            flexShrink: 0,
          }}>
            <button
              onClick={() => {
                setActiveTab('mule-networks');
              }}
              style={{
                padding: '5px 8px',
                borderRadius: 5,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 800,
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                background: 'transparent',
                color: activeTab === 'mule-networks' ? '#FDA4AF' : '#94A3B8',
                whiteSpace: 'nowrap',
              }}
            >
              <GitFork size={13} color={activeTab === 'mule-networks' ? '#F43F5E' : '#94A3B8'} />
              <span>Mule Forensics:</span>
            </button>

            {/* Navigation 1: Medium Transactions */}
            <button
              onClick={() => {
                setActiveTab('mule-networks');
                setMuleSubTab('medium');
              }}
              style={{
                padding: '5px 12px',
                borderRadius: 5,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                background: (activeTab === 'mule-networks' && muleSubTab === 'medium')
                  ? 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'
                  : 'rgba(245, 158, 11, 0.08)',
                color: (activeTab === 'mule-networks' && muleSubTab === 'medium') ? '#FFFFFF' : '#FBBF24',
                border: (activeTab === 'mule-networks' && muleSubTab === 'medium')
                  ? '1px solid rgba(245, 158, 11, 0.6)'
                  : '1px solid rgba(245, 158, 11, 0.25)',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
              }}
              title="Tier 2 Medium Risk Surveillance (30–59)"
            >
              <ShieldAlert size={13} />
              <span>Tier 2 (Medium)</span>
            </button>

            {/* Navigation 2: High Transactions */}
            <button
              onClick={() => {
                setActiveTab('mule-networks');
                setMuleSubTab('high');
              }}
              style={{
                padding: '5px 12px',
                borderRadius: 5,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                background: (activeTab === 'mule-networks' && muleSubTab === 'high')
                  ? 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)'
                  : 'rgba(239, 68, 68, 0.08)',
                color: (activeTab === 'mule-networks' && muleSubTab === 'high') ? '#FFFFFF' : '#F87171',
                border: (activeTab === 'mule-networks' && muleSubTab === 'high')
                  ? '1px solid rgba(239, 68, 68, 0.6)'
                  : '1px solid rgba(239, 68, 68, 0.25)',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
              }}
              title="Tier 3 High Risk Mule Rings & Liens (≥ 60)"
            >
              <AlertTriangle size={13} />
              <span>Tier 3 (High)</span>
            </button>

            {/* Topology Graph Tab Button */}
            <button
              onClick={() => {
                setActiveTab('mule-networks');
                setMuleSubTab('graph');
              }}
              style={{
                padding: '5px 12px',
                borderRadius: 5,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.76rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                background: (activeTab === 'mule-networks' && (muleSubTab === 'graph' || muleSubTab === 'all'))
                  ? 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)'
                  : 'rgba(139, 92, 246, 0.08)',
                color: (activeTab === 'mule-networks' && (muleSubTab === 'graph' || muleSubTab === 'all')) ? '#FFFFFF' : '#C084FC',
                border: (activeTab === 'mule-networks' && (muleSubTab === 'graph' || muleSubTab === 'all'))
                  ? '1px solid rgba(139, 92, 246, 0.6)'
                  : '1px solid rgba(139, 92, 246, 0.25)',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
              }}
              title="Interactive Multi-Bank Network Topology Graph"
            >
              <Network size={13} />
              <span>Topology Graph</span>
            </button>
          </div>

          <div style={{ width: 1, height: 18, background: 'rgba(255,255,255,0.1)' }} />

          {/* Lien Protection Layer Tab Button */}
          <button
            onClick={() => setActiveTab('lien-layer')}
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
              background: activeTab === 'lien-layer' ? 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)' : 'transparent',
              color: activeTab === 'lien-layer' ? '#fff' : '#94A3B8',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease',
            }}
            title="Controlled Funds & Lien Protection Layer"
          >
            <Lock size={14} />
            <span>Lien Layer</span>
          </button>

          <div style={{ width: 1, height: 18, background: 'rgba(255,255,255,0.1)' }} />

          {/* Forensics Tab Button */}
          <button
            onClick={() => setActiveTab('forensics')}
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
              background: activeTab === 'forensics' ? 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)' : 'transparent',
              color: activeTab === 'forensics' ? '#fff' : '#94A3B8',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease',
            }}
            title="Transaction Graph Forensics, RL Intelligence & PDF Audit Dossier"
          >
            <GitFork size={14} />
            <span>Forensics &amp; Dossier</span>
          </button>
        </div>

        {/* Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginLeft: 'auto', flexShrink: 0 }}>
          {apiOnline ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.76rem', color: '#34D399', whiteSpace: 'nowrap' }}>
              <span className="live-dot" />
              <Wifi size={13} />
              <span>Active</span>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.76rem', color: '#F87171', whiteSpace: 'nowrap' }}>
              <WifiOff size={13} />
              <span>Offline</span>
            </div>
          )}

          <span style={{ fontSize: '0.70rem', color: '#64748B', whiteSpace: 'nowrap' }}>
            {lastUpdated.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>

          <button
            className="btn btn-outline"
            onClick={checkHealth}
            style={{ padding: '4px 8px', fontSize: '0.72rem' }}
            title="Refresh status"
          >
            <RefreshCw size={12} />
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1 }}>
        {activeTab === 'overview' && (
          <AdslUnifiedDashboard
            onNavigateToGraph={() => {
              setActiveTab('mule-networks');
              setMuleSubTab('high');
            }}
          />
        )}

        {activeTab === 'mule-networks' && (
          <MuleNetworksView
            activeSubNav={muleSubTab}
            onSubNavChange={(sub) => setMuleSubTab(sub)}
          />
        )}

        {activeTab === 'lien-layer' && <LienLayerTab />}

        {activeTab === 'forensics' && <ForensicsTab />}
      </main>

      {/* Footer */}
      <footer style={{
        padding: '12px 28px',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        fontSize: '0.72rem',
        color: '#64748B',
        display: 'flex',
        justifyContent: 'space-between',
        marginTop: 'auto',
      }}>
        <span>ADSL Autonomous Decentralized Security Layer • GATv2 PyTorch Graph Neural Networks</span>
        <span>Coordinator API: <code>localhost:8002</code> │ Simulator: <code>localhost:5173</code> │ Bank SOC: <code>localhost:5174</code></span>
      </footer>
    </div>
  );
}
