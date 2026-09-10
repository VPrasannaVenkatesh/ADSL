import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Building2,
  Users,
  CheckCircle,
  AlertCircle,
  Radio,
  Sliders,
} from 'lucide-react';

import { Header } from './components/Header';
import { BankConnectionSection } from './components/BankConnectionSection';
import { SimulationControls } from './components/SimulationControls';
import { SummaryCards } from './components/SummaryCards';
import { LiveTransactionTable } from './components/LiveTransactionTable';
import { BankAnalyticsView } from './components/BankAnalyticsView';
import { AccountDrawer } from './components/AccountDrawer';
import { simulatorApi } from './api/simulatorApi';

export function App() {
  const [activeTab, setActiveTab] = useState('LIVE_FEED'); // 'LIVE_FEED' | 'ACCOUNTS'
  const [selectedBank, setSelectedBank] = useState('ALL');

  // Simulator & Bank Data State
  const [simulatorStatus, setSimulatorStatus] = useState(null);
  const [bankStats, setBankStats] = useState(null);
  const [liveTransactions, setLiveTransactions] = useState([]);

  // Account Drawer State
  const [inspectAccount, setInspectAccount] = useState(null); // { bank, accountId }

  // Toast Notification State
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

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

  // Initial Load
  useEffect(() => {
    document.title = 'TRANSACTION SIMULATOR';
    refreshAllState();
  }, [refreshAllState]);

  // Live Polling Loop (every 1.2 seconds for live transaction feed)
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
    }, 1200);
    return () => clearInterval(timer);
  }, [selectedBank]);

  // Periodic Bank Stats Refresh (every 4 seconds)
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
      showToast(`Live simulation started in ${mode.toUpperCase()} mode.`);
      refreshAllState();
    } catch (err) {
      showToast('Failed to start simulator. Ensure backend is running.', 'error');
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
      showToast(`Simulation speed set to ${speed.toUpperCase()}`);
      refreshAllState();
    } catch (err) {
      showToast('Failed to update speed.', 'error');
    }
  };

  const handleSetMix = async (mix) => {
    try {
      await simulatorApi.setMixMode(mix);
      showToast(`Simulation mix set to ${mix.toUpperCase()} MIX`);
      refreshAllState();
    } catch (err) {
      showToast('Failed to update simulation mix.', 'error');
    }
  };

  const handleSelectActiveBank = async (bank) => {
    try {
      await simulatorApi.setActiveBank(bank);
      setSelectedBank(bank);
      showToast(`Active Bank Ledger switched to ${bank} (CONNECTED)`);
      refreshAllState();
    } catch (err) {
      showToast('Failed to switch active bank ledger.', 'error');
    }
  };

  const handleSelectAccount = (bank, accountId) => {
    setInspectAccount({ bank, accountId });
  };

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

      {/* 1. HEADER */}
      <Header
        status={simulatorStatus}
        activeBank={simulatorStatus?.active_bank || selectedBank}
        onSelectActiveBank={handleSelectActiveBank}
        onStart={handleStart}
        onPause={handlePause}
        onResume={handleResume}
        onStop={handleStop}
        onSetSpeed={handleSetSpeed}
        onRefresh={refreshAllState}
      />

      {/* 2. BANK CONNECTION SECTION */}
      <div style={{ marginTop: '16px' }}>
        <BankConnectionSection
          bankStats={bankStats}
          selectedBank={selectedBank}
          onSelectBank={(bank) => {
            handleSelectActiveBank(bank);
          }}
        />
      </div>

      {/* 3. SIMULATION CONTROLS */}
      <SimulationControls
        status={simulatorStatus}
        onStart={handleStart}
        onPause={handlePause}
        onResume={handleResume}
        onStop={handleStop}
        onSetSpeed={handleSetSpeed}
        onSetMix={handleSetMix}
        onRefresh={refreshAllState}
      />

      {/* 4. SUMMARY CARDS */}
      <SummaryCards
        bankStats={bankStats}
        simulatorStatus={simulatorStatus}
      />

      {/* Navigation View Switcher (Tabs) */}
      <div style={{
        margin: '12px 24px 16px 24px',
        display: 'flex',
        gap: '10px',
        borderBottom: '1px solid var(--border-color)',
        paddingBottom: '10px',
      }}>
        <button
          onClick={() => setActiveTab('LIVE_FEED')}
          style={{
            background: activeTab === 'LIVE_FEED' ? 'rgba(0, 229, 255, 0.15)' : 'transparent',
            color: activeTab === 'LIVE_FEED' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
            border: activeTab === 'LIVE_FEED' ? '1px solid var(--accent-cyan)' : '1px solid transparent',
            padding: '8px 18px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.2s ease',
          }}
        >
          <Radio size={16} />
          <span>Live Banking Transaction Table</span>
        </button>

        <button
          onClick={() => setActiveTab('ACCOUNTS')}
          style={{
            background: activeTab === 'ACCOUNTS' ? 'rgba(0, 229, 255, 0.15)' : 'transparent',
            color: activeTab === 'ACCOUNTS' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
            border: activeTab === 'ACCOUNTS' ? '1px solid var(--accent-cyan)' : '1px solid transparent',
            padding: '8px 18px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.2s ease',
          }}
        >
          <Building2 size={16} />
          <span>Bank Databases & Account Explorer</span>
        </button>
      </div>

      {/* 5. MAIN CONTENT AREA (SEARCH, FILTERS & LIVE TRANSACTION TABLE / ACCOUNT EXPLORER) */}
      <main style={{ flex: 1 }}>
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
      </main>

      {/* 6. ACCOUNT DETAILS DRAWER */}
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
        padding: '14px 24px',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '0.75rem',
        color: 'var(--text-muted)',
        background: 'rgba(7, 9, 14, 0.9)',
      }}>
        <div>
          Multi-Bank Architecture • <strong>TRANSACTION SIMULATOR</strong> • Downstream ML & Graph Analytics in ADSL Dashboard
        </div>
        <div>
          Independent PostgreSQL Databases: <strong>sbi_db</strong> (Connected) │ <strong>axis_db</strong> (Connected) │ <strong>iob_db</strong> (Connected)
        </div>
      </footer>

    </div>
  );
}

export default App;
