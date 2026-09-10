import React, { useState, useEffect, useCallback } from 'react';
import { SummaryCards } from './components/SummaryCards';
import { RiskTable } from './components/RiskTable';
import { AssessmentDrawer } from './components/AssessmentDrawer';
import { XGBoostRiskView } from './components/XGBoostRiskView';
import { StoredProfilesView } from './components/StoredProfilesView';
import { riskApi } from './api';
import { Shield, RefreshCw, Wifi, WifiOff, Sparkles, Activity, UserCheck } from 'lucide-react';

const POLL_MS = 1500; // Live poll every 1.5 seconds

export default function App() {
  const [activeTab, setActiveTab] = useState('profiles'); // 'profiles' | 'xgboost' | 'behavioural'
  const [assessments, setAssessments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selected, setSelected] = useState(null);
  const [apiOnline, setApiOnline] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    document.title = 'BANK DASHBOARD';
  }, []);

  const [filters, setFilters] = useState({
    bank: 'ALL',
    risk_level: '',
    account_id: '',
    transaction_id: '',
  });

  // Fetch live behavioural assessments
  const fetchData = useCallback(async () => {
    try {
      const [liveRes, summaryRes] = await Promise.all([
        riskApi.getAssessments({
          bank: filters.bank,
          risk_level: filters.risk_level || undefined,
          account_id: filters.account_id || undefined,
          transaction_id: filters.transaction_id || undefined,
          limit: 150,
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

  // Initial load + polling
  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, POLL_MS);
    return () => clearInterval(timer);
  }, [fetchData]);

  // Load full detail on click
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
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        background: 'rgba(5,7,9,0.97)',
        borderBottom: '1px solid var(--border)',
        padding: '14px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <Shield size={22} color="#EC4899" />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 900, fontSize: '1.05rem', letterSpacing: '0.01em', color: 'var(--text-primary)' }}>
            BANK DASHBOARD
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 1 }}>
            Bank Risk Provider • Account Behavioural Profiles & Predictive ML Engine &nbsp;│&nbsp;
            <span style={{ color: '#3B82F6', fontWeight: 700 }}>sbi_db</span>&nbsp;•&nbsp;
            <span style={{ color: '#EC4899', fontWeight: 700 }}>axis_db</span>&nbsp;•&nbsp;
            <span style={{ color: '#F59E0B', fontWeight: 700 }}>iob_db</span>
          </div>
        </div>

        {/* View Tabs */}
        <div style={{
          display: 'flex',
          background: 'rgba(255, 255, 255, 0.05)',
          padding: 3,
          borderRadius: 8,
          border: '1px solid var(--border)',
        }}>
          <button
            onClick={() => setActiveTab('profiles')}
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
              background: activeTab === 'profiles' ? 'linear-gradient(135deg, #3B82F6 0%, #6366F1 100%)' : 'transparent',
              color: activeTab === 'profiles' ? '#fff' : 'var(--text-muted)',
              transition: 'all 0.15s ease',
            }}
          >
            <UserCheck size={13} />
            <span>Stored Risk Profiles</span>
          </button>

          <button
            onClick={() => setActiveTab('xgboost')}
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
              background: activeTab === 'xgboost' ? 'linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%)' : 'transparent',
              color: activeTab === 'xgboost' ? '#fff' : 'var(--text-muted)',
              transition: 'all 0.15s ease',
            }}
          >
            <Sparkles size={13} />
            <span>XGBoost ML Risk</span>
          </button>

          <button
            onClick={() => setActiveTab('behavioural')}
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
              background: activeTab === 'behavioural' ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
              color: activeTab === 'behavioural' ? '#818CF8' : 'var(--text-muted)',
              border: activeTab === 'behavioural' ? '1px solid #6366F1' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            <Activity size={13} />
            <span>Behavioural History</span>
          </button>
        </div>


        {/* API Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {apiOnline === null ? null : apiOnline ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--low)' }}>
              <span className="live-dot" />
              <Wifi size={14} />
              <span>Live</span>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--critical)' }}>
              <WifiOff size={14} />
              <span>API Offline (port 8001)</span>
            </div>
          )}

          {lastUpdated && (
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginLeft: 8 }}>
              {lastUpdated.toLocaleTimeString('en-IN')}
            </span>
          )}

          <button
            className="btn btn-outline"
            onClick={fetchData}
            style={{ padding: '6px 12px', fontSize: '0.75rem', marginLeft: 8 }}
          >
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      </header>

      {/* Offline banner */}
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
          <strong>Risk API not reachable.</strong> Start it with:&nbsp;
          <code style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 4, padding: '2px 6px' }}>
            python -m uvicorn risk_api:app --port 8001
          </code>
          &nbsp;from the <code>backend/</code> directory, then run the transaction simulator.
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'profiles' && (
        <StoredProfilesView selectedBank={filters.bank} />
      )}

      {activeTab === 'xgboost' && (
        <div style={{ marginTop: 20 }}>
          <XGBoostRiskView />
        </div>
      )}

      {activeTab === 'behavioural' && (
        <>
          {/* Summary KPI Cards */}
          <div style={{ marginTop: 20 }}>
            <SummaryCards summary={summary} />
          </div>

          {/* Main Risk Assessment Table */}
          <main style={{ flex: 1 }}>
            <RiskTable
              assessments={assessments}
              selected={selected}
              onSelect={handleSelect}
              filters={filters}
              onFiltersChange={setFilters}
            />
          </main>

          {/* Detail Drawer */}
          {selected && (
            <AssessmentDrawer
              assessment={selected}
              onClose={() => setSelected(null)}
            />
          )}
        </>
      )}


      {/* Footer */}
      <footer style={{
        padding: '12px 24px',
        borderTop: '1px solid var(--border)',
        fontSize: '0.72rem',
        color: 'var(--text-muted)',
        display: 'flex',
        justifyContent: 'space-between',
        marginTop: 'auto',
      }}>
        <span>Banking Behavioural Risk Analysis — Module 2 & Module 4 (XGBoost Transaction Risk Engine)</span>
        <span>FastAPI Risk API: <code>localhost:8001</code> &nbsp;│&nbsp; Simulator: <code>localhost:5173</code></span>
      </footer>
    </div>
  );
}
