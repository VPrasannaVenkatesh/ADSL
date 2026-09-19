import React, { useState, useEffect } from 'react';
import { AdslUnifiedDashboard } from './components/AdslUnifiedDashboard';
import { MuleNetworksView } from './components/MuleNetworksView';
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
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('mule-networks'); // 'overview' | 'mule-networks'
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
      {/* Top Header */}
      <header style={{
        background: 'rgba(4,6,10,0.98)',
        borderBottom: '1px solid var(--border, rgba(255,255,255,0.08))',
        padding: '12px 28px',
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
          <div style={{ fontWeight: 900, fontSize: '1.05rem', letterSpacing: '0.01em', color: '#F8FAFC' }}>
            ADSL DASHBOARD
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: 1 }}>
            Autonomous Decentralized Security Layer • Cross-Bank Transaction Engine & Mule Forensics &nbsp;│&nbsp;
            Ledgers: <span style={{ color: '#3B82F6', fontWeight: 700 }}>SBI</span>, <span style={{ color: '#EC4899', fontWeight: 700 }}>AXIS</span>, <span style={{ color: '#F59E0B', fontWeight: 700 }}>IOB</span>
          </div>
        </div>

        {/* Tab View & Sub-Navigation Switcher */}
        <div style={{
          display: 'flex',
          background: 'rgba(255, 255, 255, 0.04)',
          padding: '3px 4px',
          borderRadius: 10,
          border: '1px solid rgba(255,255,255,0.08)',
          gap: 6,
          alignItems: 'center',
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
              transition: 'all 0.15s ease',
            }}
          >
            <LayoutDashboard size={13} />
            <span>Central ADSL Overview</span>
          </button>

          <div style={{ width: 1, height: 18, background: 'rgba(255,255,255,0.1)' }} />

          {/* Mule Networks Navigation Group */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            background: activeTab === 'mule-networks' ? 'rgba(239, 68, 68, 0.08)' : 'transparent',
            padding: '2px 4px',
            borderRadius: 7,
            border: activeTab === 'mule-networks' ? '1px solid rgba(239, 68, 68, 0.25)' : '1px solid transparent',
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
              }}
            >
              <GitFork size={13} color={activeTab === 'mule-networks' ? '#F43F5E' : '#94A3B8'} />
              <span>Mule Networks:</span>
            </button>

            {/* Navigation 1: Medium Transactions */}
            <button
              onClick={() => {
                setActiveTab('mule-networks');
                setMuleSubTab('medium');
              }}
              style={{
                padding: '5px 12px',
                borderRadius: 6,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.75rem',
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
                boxShadow: (activeTab === 'mule-networks' && muleSubTab === 'medium')
                  ? '0 0 10px rgba(245, 158, 11, 0.35)'
                  : 'none',
                transition: 'all 0.15s ease',
              }}
              title="Navigate to Medium Transactions (Risk 30–59)"
            >
              <ShieldAlert size={12} />
              <span>Medium Transactions</span>
            </button>

            {/* Navigation 2: High Transactions */}
            <button
              onClick={() => {
                setActiveTab('mule-networks');
                setMuleSubTab('high');
              }}
              style={{
                padding: '5px 12px',
                borderRadius: 6,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.75rem',
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
                boxShadow: (activeTab === 'mule-networks' && muleSubTab === 'high')
                  ? '0 0 10px rgba(239, 68, 68, 0.4)'
                  : 'none',
                transition: 'all 0.15s ease',
              }}
              title="Navigate to High Risk Transactions (Risk ≥ 60 & Mule Rings)"
            >
              <AlertTriangle size={12} />
              <span>High Transactions</span>
            </button>

            {/* All Clusters */}
            <button
              onClick={() => {
                setActiveTab('mule-networks');
                setMuleSubTab('all');
              }}
              style={{
                padding: '5px 9px',
                borderRadius: 5,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.71rem',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                background: (activeTab === 'mule-networks' && muleSubTab === 'all')
                  ? 'rgba(139, 92, 246, 0.35)'
                  : 'transparent',
                color: (activeTab === 'mule-networks' && muleSubTab === 'all') ? '#DDD6FE' : '#94A3B8',
                transition: 'all 0.15s ease',
              }}
              title="View all clusters and full network topology"
            >
              <Network size={11} />
              <span>All Clusters</span>
            </button>
          </div>
        </div>

        {/* Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {apiOnline ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#34D399' }}>
              <span className="live-dot" />
              <Wifi size={14} />
              <span>Coordinator Active</span>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#F87171' }}>
              <WifiOff size={14} />
              <span>Offline (Port 8002)</span>
            </div>
          )}

          <span style={{ fontSize: '0.68rem', color: '#64748B' }}>
            Synced {lastUpdated.toLocaleTimeString('en-IN')}
          </span>

          <button
            className="btn btn-outline"
            onClick={checkHealth}
            style={{ padding: '5px 10px', fontSize: '0.72rem' }}
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
