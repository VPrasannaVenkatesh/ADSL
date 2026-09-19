import React, { useState, useEffect, useCallback } from 'react';
import { SummaryCards } from './components/SummaryCards';
import { RiskTable } from './components/RiskTable';
import { AssessmentDrawer } from './components/AssessmentDrawer';
import { FlaggedAccountsWatchlist } from './components/FlaggedAccountsWatchlist';
import { riskApi } from './api';
import { Shield, RefreshCw, Wifi, WifiOff, Bell, UserX, Building2, Lock } from 'lucide-react';

const POLL_MS = 1800;

export default function App() {
  const [activeTab, setActiveTab] = useState('alerts'); // 'alerts' | 'flagged-accounts'
  const [assessments, setAssessments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selected, setSelected] = useState(null);
  const [apiOnline, setApiOnline] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedBank, setSelectedBank] = useState('SBI');

  useEffect(() => {
    document.title = 'BANK SECURITY OPERATIONS (SOC)';
  }, []);

  const [filters, setFilters] = useState({
    bank: 'SBI',
    risk_level: '',
    account_id: '',
    transaction_id: '',
  });

  const handleBankChange = (bank) => {
    setSelectedBank(bank);
    setFilters((prev) => ({ ...prev, bank }));
  };

  const fetchData = useCallback(async () => {
    try {
      const [liveRes, summaryRes] = await Promise.all([
        riskApi.getAssessments({
          bank: filters.bank === 'ALL' ? undefined : filters.bank,
          risk_level: filters.risk_level || undefined,
          account_id: filters.account_id || undefined,
          transaction_id: filters.transaction_id || undefined,
          limit: 100,
        }),
        riskApi.getSummary(filters.bank),
      ]);
      setAssessments(liveRes.assessments || []);
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
    if (selected?.assessment_id === row.assessment_id) {
      setSelected(null);
      return;
    }
    try {
      const detail = await riskApi.getDetail(row.assessment_id);
      setSelected(detail);
    } catch {
      setSelected(row);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#030712' }}>
      {/* Header */}
      <header style={{
        background: 'rgba(5,7,12,0.98)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        padding: '14px 28px',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{
          background: 'rgba(236, 72, 153, 0.15)',
          border: '1px solid rgba(236, 72, 153, 0.35)',
          borderRadius: 8,
          padding: '6px 8px',
          display: 'flex',
          alignItems: 'center',
        }}>
          <Shield size={20} color="#EC4899" />
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 900, fontSize: '1.05rem', letterSpacing: '0.01em', color: '#F8FAFC' }}>
            BANK SECURITY OPERATIONS CONSOLE
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: 1 }}>
            Real-Time Bank Fraud Monitoring & Behavioural Anomaly Detection &nbsp;│&nbsp;
            Selected Ledger: <strong style={{ color: selectedBank === 'SBI' ? '#3B82F6' : selectedBank === 'AXIS' ? '#EC4899' : '#F59E0B' }}>{selectedBank}</strong>
          </div>
        </div>

        {/* Bank Switcher Pills */}
        <div style={{
          display: 'flex',
          background: 'rgba(255, 255, 255, 0.05)',
          padding: 3,
          borderRadius: 8,
          border: '1px solid rgba(255, 255, 255, 0.08)',
          gap: 2,
        }}>
          {['SBI', 'AXIS', 'IOB', 'ALL'].map((b) => (
            <button
              key={b}
              onClick={() => handleBankChange(b)}
              style={{
                padding: '6px 14px',
                borderRadius: 6,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 800,
                background: selectedBank === b ? 'rgba(236, 72, 153, 0.25)' : 'transparent',
                color: selectedBank === b ? '#F472B6' : '#94A3B8',
                transition: 'all 0.15s ease',
              }}
            >
              {b === 'ALL' ? 'All Banks' : b}
            </button>
          ))}
        </div>

        {/* View Tabs: 1. Live Alerts | 2. Flagged Accounts */}
        <div style={{
          display: 'flex',
          background: 'rgba(255, 255, 255, 0.05)',
          padding: 3,
          borderRadius: 8,
          border: '1px solid rgba(255, 255, 255, 0.08)',
          gap: 4,
        }}>
          <button
            onClick={() => setActiveTab('alerts')}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.78rem',
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: activeTab === 'alerts' ? 'linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%)' : 'transparent',
              color: activeTab === 'alerts' ? '#fff' : '#94A3B8',
              transition: 'all 0.15s ease',
            }}
          >
            <Bell size={13} />
            <span>Live Risk Alerts</span>
          </button>

          <button
            onClick={() => setActiveTab('flagged-accounts')}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.78rem',
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: activeTab === 'flagged-accounts' ? 'linear-gradient(135deg, #EF4444 0%, #F97316 100%)' : 'transparent',
              color: activeTab === 'flagged-accounts' ? '#fff' : '#94A3B8',
              transition: 'all 0.15s ease',
            }}
          >
            <UserX size={13} />
            <span>Flagged Accounts Watchlist</span>
          </button>
        </div>

        {/* Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {apiOnline ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#34D399' }}>
              <span className="live-dot" />
              <Wifi size={14} />
              <span>SOC Live</span>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#F87171' }}>
              <WifiOff size={14} />
              <span>Offline (Port 8001)</span>
            </div>
          )}

          <button
            className="btn btn-outline"
            onClick={fetchData}
            style={{ padding: '6px 12px', fontSize: '0.75rem', marginLeft: 6 }}
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </header>

      {/* Main View Area */}
      <div style={{ padding: '24px 32px', maxWidth: '1440px', margin: '0 auto', width: '100%', flex: 1 }}>
        {/* KPI Summary Cards */}
        <div style={{ marginBottom: 24 }}>
          <SummaryCards summary={summary} />
        </div>

        {/* View 1: Live Risk Alerts */}
        {activeTab === 'alerts' && (
          <main style={{ flex: 1 }}>
            <RiskTable
              assessments={assessments}
              selected={selected}
              onSelect={handleSelect}
              filters={filters}
              onFiltersChange={setFilters}
            />
          </main>
        )}

        {/* View 2: Flagged Accounts Watchlist */}
        {activeTab === 'flagged-accounts' && (
          <FlaggedAccountsWatchlist
            selectedBank={selectedBank}
            onSelectAccount={(acc) => {
              // Open assessment drawer with mock or fetch detail
              handleSelect({
                assessment_id: `ACC-AUDIT-${acc.account_id}`,
                account_id: acc.account_id,
                transaction_id: `REF-${acc.account_id}`,
                bank_name: acc.bank,
                role: 'ACCOUNT_HOLDER',
                amount: acc.current_balance,
                transaction_type: acc.account_type,
                final_risk_score: acc.account_status !== 'ACTIVE' ? 88.0 : 65.0,
                risk_level: acc.account_status !== 'ACTIVE' ? 'CRITICAL' : 'HIGH',
                risk_reasons: [
                  `Account status: ${acc.account_status}`,
                  `Current balance of ₹${Number(acc.current_balance).toLocaleString()} under behavioural monitoring`,
                  'Counterparty pattern analysis flagged abnormal inbound velocity',
                ],
                components: {
                  amount_risk: 75.0,
                  velocity_risk: 68.0,
                  behaviour_deviation_risk: 72.0,
                  device_risk: 30.0,
                  location_risk: 20.0,
                  counterparty_risk: 85.0,
                  timing_risk: 40.0,
                  network_pattern_risk: 80.0,
                },
              });
            }}
          />
        )}
      </div>

      {/* Detail Drawer */}
      {selected && (
        <AssessmentDrawer
          assessment={selected}
          onClose={() => setSelected(null)}
        />
      )}

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
        <span>Bank Security Operations Center (SOC) • Automated XGBoost & Behavioural Anomaly Inference</span>
        <span>Risk API: <code>localhost:8001</code> │ Simulator: <code>localhost:5173</code> │ ADSL: <code>localhost:5175</code></span>
      </footer>
    </div>
  );
}
