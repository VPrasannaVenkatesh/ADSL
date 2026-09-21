import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Building2,
  CheckCircle,
  AlertCircle,
  Radio,
  Play,
  Pause,
  Square,
  Zap,
  RefreshCw,
  Clock,
  Shield,
  Layers,
  Sparkles,
  Network,
} from 'lucide-react';

import { LiveTransactionTable } from './components/LiveTransactionTable';
import { BankAnalyticsView } from './components/BankAnalyticsView';
import { NetworkGraphView } from './components/NetworkGraphView';
import { AccountDrawer } from './components/AccountDrawer';
import { simulatorApi } from './api/simulatorApi';

export default function App() {
  const [activeTab, setActiveTab] = useState('LIVE_FEED'); // 'LIVE_FEED' | 'ACCOUNTS'
  const [selectedBank, setSelectedBank] = useState('ALL');

  // Simulator & Bank Data State
  const [simulatorStatus, setSimulatorStatus] = useState(null);
  const [bankStats, setBankStats] = useState(null);
  const [liveTransactions, setLiveTransactions] = useState([]);

  // Account Drawer State
  const [inspectAccount, setInspectAccount] = useState(null);

  // Toast Notification State
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  // Clock state
  const [simClockDisplay, setSimClockDisplay] = useState(new Date());

  useEffect(() => {
    if (simulatorStatus?.sim_clock) {
      const parsed = new Date(simulatorStatus.sim_clock);
      if (!isNaN(parsed.getTime())) {
        setSimClockDisplay(parsed);
      }
    }
  }, [simulatorStatus?.sim_clock]);

  useEffect(() => {
    const clockTimer = setInterval(() => {
      setSimClockDisplay((prev) => new Date(prev.getTime() + 1000));
    }, 1000);
    return () => clearInterval(clockTimer);
  }, []);

  // Fetch Full Backend State
  const refreshAllState = useCallback(async () => {
    try {
      const [statusRes, statsRes, liveRes] = await Promise.all([
        simulatorApi.getStatus().catch(() => null),
        simulatorApi.getBankStats().catch(() => null),
        simulatorApi.getLiveTransactions({ limit: 100, bank: selectedBank }).catch(() => ({ transactions: [] })),
      ]);

      if (statusRes) setSimulatorStatus(statusRes);
      if (statsRes) setBankStats(statsRes);
      if (liveRes?.transactions) setLiveTransactions(liveRes.transactions);
    } catch (err) {
      console.error('Error refreshing simulator state', err);
    }
  }, [selectedBank]);

  useEffect(() => {
    document.title = 'TRANSACTION SIMULATOR';
    refreshAllState();
  }, [refreshAllState]);

  // Live Polling Loop
  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const [statusRes, liveRes] = await Promise.all([
          simulatorApi.getStatus().catch(() => null),
          simulatorApi.getLiveTransactions({ limit: 100, bank: selectedBank }).catch(() => null),
        ]);

        if (statusRes) setSimulatorStatus(statusRes);
        if (liveRes?.transactions) setLiveTransactions(liveRes.transactions);
      } catch (err) {
        // Ignore offline ping
      }
    }, 1400);
    return () => clearInterval(timer);
  }, [selectedBank]);

  // Periodic Bank Stats Refresh
  useEffect(() => {
    const statsTimer = setInterval(async () => {
      try {
        const statsRes = await simulatorApi.getBankStats();
        if (statsRes) setBankStats(statsRes);
      } catch (err) {
        // Ignore
      }
    }, 4000);
    return () => clearInterval(statsTimer);
  }, []);

  // Simulator Control Handlers
  const handleStart = async (mode = 'normal') => {
    try {
      await simulatorApi.startSimulation({ mode });
      showToast(`Simulation started in ${mode.toUpperCase()} mode.`);
      refreshAllState();
    } catch (err) {
      showToast('Failed to start simulator.', 'error');
    }
  };

  const handlePause = async () => {
    try {
      await simulatorApi.pauseSimulation();
      showToast('Simulation paused.');
      refreshAllState();
    } catch (err) {
      showToast('Failed to pause simulator.', 'error');
    }
  };

  const handleResume = async () => {
    try {
      await simulatorApi.resumeSimulation();
      showToast('Simulation resumed.');
      refreshAllState();
    } catch (err) {
      showToast('Failed to resume simulator.', 'error');
    }
  };

  const handleStop = async () => {
    try {
      await simulatorApi.stopSimulation();
      showToast('Simulation stopped.');
      refreshAllState();
    } catch (err) {
      showToast('Failed to stop simulator.', 'error');
    }
  };

  const handleSetSpeed = async (speed) => {
    try {
      await simulatorApi.setSpeed(speed);
      showToast(`Speed set to ${speed.toUpperCase()}`);
      refreshAllState();
    } catch (err) {
      showToast('Failed to update speed.', 'error');
    }
  };

  const handleSetMix = async (mix) => {
    try {
      await simulatorApi.setMixMode(mix);
      showToast(`Pattern mix set to ${mix.toUpperCase()}`);
      refreshAllState();
    } catch (err) {
      showToast('Failed to update mix.', 'error');
    }
  };

  const handleSelectActiveBank = async (bank) => {
    try {
      await simulatorApi.setActiveBank(bank);
      setSelectedBank(bank);
      showToast(`Active ledger switched to ${bank}`);
      refreshAllState();
    } catch (err) {
      showToast('Failed to switch bank ledger.', 'error');
    }
  };

  const handleSelectAccount = (bank, accountId) => {
    setInspectAccount({ bank, accountId });
  };

  const isRunning = simulatorStatus?.is_running && !simulatorStatus?.is_paused;
  const isPaused = simulatorStatus?.is_running && simulatorStatus?.is_paused;
  const isStopped = !simulatorStatus?.is_running;
  const currentSpeed = simulatorStatus?.mode || 'normal';
  const currentMix = simulatorStatus?.mix_mode || 'balanced';

  const banksData = bankStats?.banks || {};

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary, #030712)' }}>
      
      {/* Toast Notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: toast.type === 'error' ? 'rgba(239, 68, 68, 0.95)' : 'rgba(16, 185, 129, 0.95)',
          color: '#FFFFFF',
          padding: '12px 20px',
          borderRadius: '8px',
          boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          zIndex: 9999,
          fontSize: '0.875rem',
          fontWeight: '600',
        }}>
          {toast.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle size={18} />}
          <span>{toast.message}</span>
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────────────────────
          1. UNIFIED COMMAND BAR (Consolidated Controls & Navigation)
          ────────────────────────────────────────────────────────────────────────── */}
      <header style={{
        background: 'rgba(8, 12, 20, 0.96)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '12px 28px',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        {/* Title & Engine Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.2) 0%, rgba(59, 130, 246, 0.3) 100%)',
            border: '1px solid rgba(0, 229, 255, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Activity size={22} color="var(--accent-cyan, #00E5FF)" />
          </div>
          <div>
            <div style={{ fontSize: '1.05rem', fontWeight: '900', color: '#FFFFFF', letterSpacing: '0.02em' }}>
              TRANSACTION SIMULATOR
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.7rem', marginTop: '2px' }}>
              <span className={`pulse-dot ${isRunning ? 'running' : isPaused ? 'paused' : 'stopped'}`} style={{ width: '6px', height: '6px' }} />
              <span style={{ color: isRunning ? '#34D399' : isPaused ? '#FBBF24' : '#94A3B8', fontWeight: '700' }}>
                {isRunning ? 'GENERATOR ACTIVE' : isPaused ? 'PAUSED' : 'STANDBY'}
              </span>
              <span style={{ color: '#475569' }}>•</span>
              <span style={{ color: '#94A3B8', fontFamily: 'JetBrains Mono, monospace' }}>
                {simClockDisplay.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}
              </span>
            </div>
          </div>
        </div>

        {/* Central Simulation Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Play / Pause / Resume / Stop */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '8px',
            padding: '3px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            gap: '3px',
          }}>
            {isStopped ? (
              <button
                className="btn-primary"
                onClick={() => handleStart(currentSpeed)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: '800',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Play size={13} fill="currentColor" />
                <span>START</span>
              </button>
            ) : isPaused ? (
              <button
                className="btn-primary"
                onClick={handleResume}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: '800',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: '#10B981',
                }}
              >
                <Play size={13} fill="currentColor" />
                <span>RESUME</span>
              </button>
            ) : (
              <button
                onClick={handlePause}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: '800',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(245, 158, 11, 0.2)',
                  color: '#FBBF24',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  cursor: 'pointer',
                }}
              >
                <Pause size={13} />
                <span>PAUSE</span>
              </button>
            )}

            {!isStopped && (
              <button
                onClick={handleStop}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: '800',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(239, 68, 68, 0.15)',
                  color: '#F87171',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  cursor: 'pointer',
                }}
              >
                <Square size={13} />
                <span>STOP</span>
              </button>
            )}
          </div>

          {/* Speed Mode Selector */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '8px',
            padding: '3px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}>
            {['slow', 'normal', 'fast'].map((spd) => (
              <button
                key={spd}
                onClick={() => handleSetSpeed(spd)}
                style={{
                  padding: '5px 10px',
                  borderRadius: '5px',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '0.72rem',
                  fontWeight: '800',
                  background: currentSpeed === spd ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  color: currentSpeed === spd ? 'var(--accent-cyan, #00E5FF)' : '#94A3B8',
                  transition: 'all 0.15s ease',
                }}
              >
                {spd.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Pattern Mix Dropdown */}
          <select
            value={currentMix}
            onChange={(e) => handleSetMix(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              background: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              color: '#F1F5F9',
              fontSize: '0.75rem',
              fontWeight: '700',
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="balanced">Balanced Mix</option>
            <option value="normal">Normal Heavy Mix</option>
            <option value="business">Business / Commercial Mix</option>
            <option value="mule">Mule & Fraud Heavy Mix</option>
          </select>
        </div>

        {/* View Tabs & Refresh */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            display: 'flex',
            background: 'rgba(255, 255, 255, 0.05)',
            padding: '3px',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            gap: '2px',
          }}>
            <button
              onClick={() => setActiveTab('LIVE_FEED')}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.78rem',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: activeTab === 'LIVE_FEED' ? 'rgba(0, 229, 255, 0.15)' : 'transparent',
                color: activeTab === 'LIVE_FEED' ? 'var(--accent-cyan, #00E5FF)' : '#94A3B8',
              }}
            >
              <Radio size={14} />
              <span>Live Ledger</span>
            </button>
            <button
              onClick={() => setActiveTab('ACCOUNTS')}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.78rem',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: activeTab === 'ACCOUNTS' ? 'rgba(0, 229, 255, 0.15)' : 'transparent',
                color: activeTab === 'ACCOUNTS' ? 'var(--accent-cyan, #00E5FF)' : '#94A3B8',
              }}
            >
              <Building2 size={14} />
              <span>Bank Explorer</span>
            </button>
            <button
              onClick={() => setActiveTab('GRAPH')}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.78rem',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: activeTab === 'GRAPH' ? 'rgba(0, 229, 255, 0.15)' : 'transparent',
                color: activeTab === 'GRAPH' ? 'var(--accent-cyan, #00E5FF)' : '#94A3B8',
              }}
            >
              <Network size={14} />
              <span>Network Graph</span>
            </button>
          </div>

          <button
            onClick={refreshAllState}
            style={{
              padding: '7px 10px',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#CBD5E1',
              cursor: 'pointer',
            }}
            title="Refresh state"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </header>

      {/* ──────────────────────────────────────────────────────────────────────────
          2. COMPACT BANK LEDGER METRIC RIBBON (Clean, Horizontal)
          ────────────────────────────────────────────────────────────────────────── */}
      <div style={{
        padding: '16px 28px 0 28px',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '14px',
      }}>
        {[
          { code: 'SBI', name: 'State Bank of India', color: '#3B82F6', db: 'sbi_db' },
          { code: 'AXIS', name: 'Axis Bank Ltd', color: '#EC4899', db: 'axis_db' },
          { code: 'IOB', name: 'Indian Overseas Bank', color: '#F59E0B', db: 'iob_db' },
        ].map((bank) => {
          const stats = banksData[bank.code] || {};
          const isSelected = selectedBank === bank.code;
          return (
            <div
              key={bank.code}
              onClick={() => handleSelectActiveBank(isSelected ? 'ALL' : bank.code)}
              style={{
                background: isSelected ? 'rgba(15, 23, 42, 0.95)' : 'rgba(10, 15, 25, 0.75)',
                border: '1px solid',
                borderColor: isSelected ? bank.color : 'rgba(255, 255, 255, 0.08)',
                borderRadius: '10px',
                padding: '12px 18px',
                cursor: 'pointer',
                boxShadow: isSelected ? `0 0 20px ${bank.color}25` : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: '#10B981',
                  }} />
                  <span style={{ fontSize: '0.82rem', fontWeight: '800', color: bank.color }}>
                    {bank.code}
                  </span>
                  <span style={{ fontSize: '0.72rem', color: '#64748B' }}>
                    ({bank.db})
                  </span>
                </div>
                <span style={{
                  fontSize: '0.68rem',
                  fontWeight: '700',
                  padding: '2px 7px',
                  borderRadius: '4px',
                  background: isSelected ? `${bank.color}30` : 'rgba(255, 255, 255, 0.05)',
                  color: isSelected ? '#FFFFFF' : '#94A3B8',
                }}>
                  {isSelected ? 'FILTER ACTIVE' : 'SELECT'}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '8px' }}>
                <div>
                  <div style={{ fontSize: '0.65rem', color: '#94A3B8', textTransform: 'uppercase' }}>Ledger Balance</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '900', color: '#F8FAFC', fontFamily: 'JetBrains Mono, monospace' }}>
                    ₹{Number(stats.total_balance || 0).toLocaleString('en-IN')}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.65rem', color: '#94A3B8', textTransform: 'uppercase' }}>Transactions</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: '800', color: '#38BDF8', fontFamily: 'JetBrains Mono, monospace' }}>
                    {stats.transactions || 0}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ──────────────────────────────────────────────────────────────────────────
          3. MAIN CONTENT AREA (Live Transaction Ledger / Account Explorer)
          ────────────────────────────────────────────────────────────────────────── */}
      <main style={{ flex: 1, padding: '16px 28px 24px 28px' }}>
        {activeTab === 'LIVE_FEED' && (
          <LiveTransactionTable
            transactions={liveTransactions}
            selectedBank={selectedBank}
            onSelectBank={setSelectedBank}
            onSelectAccount={handleSelectAccount}
          />
        )}

        {activeTab === 'ACCOUNTS' && (
          <BankAnalyticsView
            bankStats={bankStats}
            onSelectAccount={handleSelectAccount}
          />
        )}

        {activeTab === 'GRAPH' && (
          <NetworkGraphView
            onSelectAccount={(accId) => handleSelectAccount('ALL', accId)}
          />
        )}
      </main>

      {/* Account Details Drawer */}
      {inspectAccount && (
        <AccountDrawer
          bank={inspectAccount.bank}
          accountId={inspectAccount.accountId}
          onClose={() => setInspectAccount(null)}
        />
      )}

      {/* Footer */}
      <footer style={{
        marginTop: 'auto',
        padding: '12px 28px',
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '0.72rem',
        color: '#64748B',
        background: 'rgba(5, 7, 12, 0.95)',
      }}>
        <div>
          Multi-Bank Transaction Simulator • SBI, AXIS, and IOB PostgreSQL Core Systems
        </div>
        <div>
          Simulator UI: <code>localhost:5173</code> │ Bank SOC: <code>localhost:5174</code> │ ADSL: <code>localhost:5175</code>
        </div>
      </footer>

    </div>
  );
}
