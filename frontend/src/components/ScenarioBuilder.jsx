import React, { useState, useEffect } from 'react';
import { 
  Sliders, 
  Building2, 
  Users, 
  ShieldAlert, 
  Zap, 
  GitBranch, 
  HelpCircle, 
  CheckCircle2, 
  AlertTriangle,
  Sparkles,
  Layers,
  ArrowRight
} from 'lucide-react';
import { formatINR } from '../utils/formatters';

export const ScenarioBuilder = ({ 
  scenarios = [], 
  onGenerate, 
  isGenerating = false,
  lastConfig = null
}) => {
  const [numBanks, setNumBanks] = useState(5);
  const [genuineCount, setGenuineCount] = useState(100);
  const [muleCount, setMuleCount] = useState(15);
  const [compromisedCount, setCompromisedCount] = useState(5);
  
  const [minBalance, setMinBalance] = useState(10000);
  const [maxBalance, setMaxBalance] = useState(500000);
  const [historicalTxnCount, setHistoricalTxnCount] = useState(1000);
  
  const [distributionType, setDistributionType] = useState('RANDOM');
  const [customBanks, setCustomBanks] = useState([]);
  
  const [selectedScenarioCode, setSelectedScenarioCode] = useState('MULTI_HOP_MULE_NETWORK');
  const [numHops, setNumHops] = useState(4);
  const [participatingBanks, setParticipatingBanks] = useState(3);
  const [transactionVolume, setTransactionVolume] = useState('HIGH');
  
  const [validationError, setValidationError] = useState('');

  // Sync custom distribution template when numBanks or distributionType changes
  useEffect(() => {
    if (distributionType === 'CUSTOM') {
      const baseG = Math.floor(genuineCount / numBanks);
      const baseM = Math.floor(muleCount / numBanks);
      const baseC = Math.floor(compromisedCount / numBanks);

      const items = Array.from({ length: numBanks }, (_, i) => ({
        bank_name: `Bank ${String(i + 1).padStart(3, '0')}`,
        bank_code: `BNK${String(i + 1).padStart(2, '0')}`,
        genuine_count: i === 0 ? baseG + (genuineCount % numBanks) : baseG,
        mule_count: i === 0 ? baseM + (muleCount % numBanks) : baseM,
        compromised_count: i === 0 ? baseC + (compromisedCount % numBanks) : baseC,
      }));
      setCustomBanks(items);
    }
  }, [numBanks, distributionType]);

  const handleCustomBankChange = (index, field, value) => {
    const updated = [...customBanks];
    updated[index] = { ...updated[index], [field]: value };
    setCustomBanks(updated);
  };

  // Pre-fill parameters when scenario changes
  const handleScenarioChange = (code) => {
    setSelectedScenarioCode(code);
    const sc = scenarios.find((s) => s.scenario_code === code);
    if (!sc) return;

    if (code === 'NORMAL_GENUINE_ACTIVITY') {
      setMuleCount(0);
      setCompromisedCount(0);
      setGenuineCount(100);
      setNumBanks(4);
    } else if (['HIGH_VALUE_GENUINE_TRANSACTION', 'NEW_DEVICE_GENUINE_USER', 'NEW_LOCATION_GENUINE_USER'].includes(code)) {
      setMuleCount(2);
      setCompromisedCount(0);
      setGenuineCount(60);
      setNumBanks(3);
    } else if (code === 'MULE_FAN_IN') {
      setMuleCount(6);
      setCompromisedCount(2);
      setGenuineCount(50);
      setNumBanks(4);
    } else if (code === 'MULE_FAN_OUT') {
      setMuleCount(12);
      setCompromisedCount(1);
      setGenuineCount(40);
      setNumBanks(4);
    } else if (code === 'MULTI_HOP_MULE_NETWORK') {
      setMuleCount(20);
      setCompromisedCount(4);
      setGenuineCount(70);
      setNumHops(4);
      setNumBanks(5);
    } else if (code === 'CROSS_BANK_MULE_NETWORK') {
      setMuleCount(25);
      setCompromisedCount(5);
      setGenuineCount(90);
      setNumBanks(8);
    } else if (code === 'ACCOUNT_TAKEOVER') {
      setMuleCount(15);
      setCompromisedCount(10);
      setGenuineCount(60);
      setNumBanks(4);
    } else if (code === 'MIXED_NETWORK') {
      setMuleCount(25);
      setCompromisedCount(8);
      setGenuineCount(120);
      setNumBanks(6);
    }
  };

  const validateAndSubmit = (e) => {
    e.preventDefault();
    setValidationError('');

    if (numBanks <= 0) {
      setValidationError('Number of banks must be at least 1.');
      return;
    }
    const totalAccounts = genuineCount + muleCount + compromisedCount;
    if (totalAccounts <= 0) {
      setValidationError('Total account count must be at least 1.');
      return;
    }
    if (minBalance < 0 || maxBalance < minBalance) {
      setValidationError('Maximum starting balance must be greater than or equal to minimum starting balance.');
      return;
    }

    let customDistPayload = null;
    if (distributionType === 'CUSTOM') {
      const sumG = customBanks.reduce((acc, b) => acc + (parseInt(b.genuine_count) || 0), 0);
      const sumM = customBanks.reduce((acc, b) => acc + (parseInt(b.mule_count) || 0), 0);
      const sumC = customBanks.reduce((acc, b) => acc + (parseInt(b.compromised_count) || 0), 0);

      if (sumG !== genuineCount) {
        setValidationError(`Custom distribution Genuine accounts sum (${sumG}) must equal requested total (${genuineCount}).`);
        return;
      }
      if (sumM !== muleCount) {
        setValidationError(`Custom distribution Mule accounts sum (${sumM}) must equal requested total (${muleCount}).`);
        return;
      }
      if (sumC !== compromisedCount) {
        setValidationError(`Custom distribution Compromised accounts sum (${sumC}) must equal requested total (${compromisedCount}).`);
        return;
      }

      customDistPayload = customBanks.map((b) => ({
        bank_name: b.bank_name,
        bank_code: b.bank_code,
        genuine_count: parseInt(b.genuine_count) || 0,
        mule_count: parseInt(b.mule_count) || 0,
        compromised_count: parseInt(b.compromised_count) || 0,
      }));
    }

    const payload = {
      name: `ADSL Simulation - ${selectedScenarioCode}`,
      num_banks: numBanks,
      num_genuine_accounts: genuineCount,
      num_mule_accounts: muleCount,
      num_compromised_accounts: compromisedCount,
      min_starting_balance: parseFloat(minBalance),
      max_starting_balance: parseFloat(maxBalance),
      distribution_type: distributionType,
      custom_distribution: customDistPayload,
      scenario_type: selectedScenarioCode,
      scenario_parameters: {
        num_hops: numHops,
        participating_banks: participatingBanks,
        transaction_velocity: transactionVolume,
      },
      transaction_volume: transactionVolume,
      historical_transactions_count: parseInt(historicalTxnCount) || 1000,
    };

    onGenerate(payload);
  };

  const selectedScenarioMeta = scenarios.find((s) => s.scenario_code === selectedScenarioCode);
  const totalAccounts = genuineCount + muleCount + compromisedCount;

  return (
    <div className="glass-panel" style={{ padding: '24px', margin: '0 20px 24px 20px' }}>
      
      {/* Title Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sliders size={20} color="var(--accent-cyan)" />
          <h2 style={{ fontSize: '1.15rem', fontWeight: '700' }}>ADSL SIMULATION BUILDER</h2>
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          Configurable Multi-Bank Ground Truth Setup
        </span>
      </div>

      {validationError && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid #EF4444',
          borderRadius: '8px',
          padding: '12px 16px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: '#FCA5A5',
          fontSize: '0.875rem'
        }}>
          <AlertTriangle size={18} color="#EF4444" />
          <span>{validationError}</span>
        </div>
      )}

      <form onSubmit={validateAndSubmit}>
        
        {/* Top Grid: Sizing & Balances */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '18px', marginBottom: '24px' }}>
          
          {/* Bank Sizing Card */}
          <div style={{ background: 'rgba(7, 9, 14, 0.5)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--accent-cyan)', marginBottom: '8px' }}>
              <Building2 size={16} />
              <span>Number of Banks: [{numBanks}]</span>
            </label>
            <input 
              type="range" 
              min="1" 
              max="20" 
              value={numBanks} 
              onChange={(e) => setNumBanks(parseInt(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-cyan)', marginBottom: '8px' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <span>1 Bank</span>
              <span>10 Banks</span>
              <span>20 Banks</span>
            </div>
          </div>

          {/* Account Breakdown Card */}
          <div style={{ background: 'rgba(7, 9, 14, 0.5)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '10px' }}>
              <Users size={16} color="var(--accent-cyan)" />
              <span>Account Ground-Truth Distribution</span>
            </label>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--status-genuine)', fontWeight: '600' }}>GENUINE</span>
                <input 
                  type="number" 
                  min="0" 
                  className="input-control" 
                  value={genuineCount} 
                  onChange={(e) => setGenuineCount(Math.max(0, parseInt(e.target.value) || 0))}
                />
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--status-mule)', fontWeight: '600' }}>MULE</span>
                <input 
                  type="number" 
                  min="0" 
                  className="input-control" 
                  value={muleCount} 
                  onChange={(e) => setMuleCount(Math.max(0, parseInt(e.target.value) || 0))}
                />
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--status-compromised)', fontWeight: '600' }}>COMPROMISED</span>
                <input 
                  type="number" 
                  min="0" 
                  className="input-control" 
                  value={compromisedCount} 
                  onChange={(e) => setCompromisedCount(Math.max(0, parseInt(e.target.value) || 0))}
                />
              </div>
            </div>

            <div style={{ marginTop: '8px', fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'right' }}>
              Total Accounts: <strong style={{ color: 'var(--text-primary)' }}>{totalAccounts}</strong>
            </div>
          </div>

          {/* Starting Balance Range */}
          <div style={{ background: 'rgba(7, 9, 14, 0.5)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '10px' }}>
              <span>Starting Balance Range</span>
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input 
                type="number" 
                min="0" 
                step="1000"
                className="input-control" 
                value={minBalance} 
                onChange={(e) => setMinBalance(parseFloat(e.target.value) || 0)}
                placeholder="Min ₹"
              />
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>to</span>
              <input 
                type="number" 
                min="0" 
                step="5000"
                className="input-control" 
                value={maxBalance} 
                onChange={(e) => setMaxBalance(parseFloat(e.target.value) || 0)}
                placeholder="Max ₹"
              />
            </div>
            <div style={{ marginTop: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {formatINR(minBalance)} – {formatINR(maxBalance)}
            </div>
          </div>

          {/* Historical Txns & Velocity */}
          <div style={{ background: 'rgba(7, 9, 14, 0.5)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '10px' }}>
              <span>Volume & Distribution Mode</span>
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Distribution</span>
                <select 
                  className="input-control"
                  value={distributionType}
                  onChange={(e) => setDistributionType(e.target.value)}
                >
                  <option value="RANDOM">Random ▼</option>
                  <option value="CUSTOM">Custom Matrix ▼</option>
                </select>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Txn Volume</span>
                <select 
                  className="input-control"
                  value={transactionVolume}
                  onChange={(e) => setTransactionVolume(e.target.value)}
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High ▼</option>
                  <option value="EXTREME">Extreme</option>
                </select>
              </div>
            </div>
          </div>

        </div>

        {/* Custom Distribution Matrix Table (shown when CUSTOM is selected) */}
        {distributionType === 'CUSTOM' && (
          <div style={{
            background: 'rgba(7, 9, 14, 0.8)',
            border: '1px solid rgba(0, 229, 255, 0.3)',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--accent-cyan)' }}>
                Per-Bank Account Allocation Matrix
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Target: {genuineCount} Genuine | {muleCount} Mule | {compromisedCount} Compromised
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '8px' }}>Bank Name</th>
                    <th style={{ padding: '8px' }}>Code</th>
                    <th style={{ padding: '8px', color: 'var(--status-genuine)' }}>Genuine</th>
                    <th style={{ padding: '8px', color: 'var(--status-mule)' }}>Mule</th>
                    <th style={{ padding: '8px', color: 'var(--status-compromised)' }}>Compromised</th>
                    <th style={{ padding: '8px' }}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {customBanks.map((b, idx) => {
                    const rowTotal = (parseInt(b.genuine_count) || 0) + (parseInt(b.mule_count) || 0) + (parseInt(b.compromised_count) || 0);
                    return (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={{ padding: '6px 8px' }}>
                          <input 
                            type="text" 
                            className="input-control" 
                            value={b.bank_name} 
                            onChange={(e) => handleCustomBankChange(idx, 'bank_name', e.target.value)}
                          />
                        </td>
                        <td style={{ padding: '6px 8px' }}>
                          <input 
                            type="text" 
                            className="input-control" 
                            style={{ width: '80px' }}
                            value={b.bank_code} 
                            onChange={(e) => handleCustomBankChange(idx, 'bank_code', e.target.value)}
                          />
                        </td>
                        <td style={{ padding: '6px 8px' }}>
                          <input 
                            type="number" 
                            min="0" 
                            className="input-control" 
                            style={{ width: '80px' }}
                            value={b.genuine_count} 
                            onChange={(e) => handleCustomBankChange(idx, 'genuine_count', e.target.value)}
                          />
                        </td>
                        <td style={{ padding: '6px 8px' }}>
                          <input 
                            type="number" 
                            min="0" 
                            className="input-control" 
                            style={{ width: '80px' }}
                            value={b.mule_count} 
                            onChange={(e) => handleCustomBankChange(idx, 'mule_count', e.target.value)}
                          />
                        </td>
                        <td style={{ padding: '6px 8px' }}>
                          <input 
                            type="number" 
                            min="0" 
                            className="input-control" 
                            style={{ width: '80px' }}
                            value={b.compromised_count} 
                            onChange={(e) => handleCustomBankChange(idx, 'compromised_count', e.target.value)}
                          />
                        </td>
                        <td style={{ padding: '6px 8px', fontWeight: '600' }}>
                          {rowTotal}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 12 Pre-built Scenarios Selector */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)' }}>
              <GitBranch size={16} color="var(--accent-cyan)" />
              <span>Select Pre-Built Simulation Scenario (12 Scenarios)</span>
            </label>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Choose a scenario to auto-calibrate topology parameters
            </span>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '12px',
            maxHeight: '280px',
            overflowY: 'auto',
            padding: '4px',
          }}>
            {scenarios.map((sc) => {
              const isSelected = selectedScenarioCode === sc.scenario_code;
              return (
                <div
                  key={sc.scenario_code}
                  onClick={() => handleScenarioChange(sc.scenario_code)}
                  style={{
                    background: isSelected ? 'rgba(0, 229, 255, 0.08)' : 'rgba(13, 17, 26, 0.6)',
                    border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    position: 'relative'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: '700', color: isSelected ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                      {sc.scenario_id}. {sc.scenario_name}
                    </div>
                    {isSelected && <CheckCircle2 size={16} color="var(--accent-cyan)" />}
                  </div>

                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px', lineHeight: '1.3' }}>
                    {sc.description}
                  </p>

                  <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    <strong>Hypothesis:</strong> {sc.target_hypothesis}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Scenario Dynamic Tuners (e.g. Hops) */}
        {selectedScenarioMeta && (
          <div style={{
            background: 'rgba(0, 229, 255, 0.03)',
            border: '1px dashed rgba(0, 229, 255, 0.2)',
            borderRadius: '8px',
            padding: '12px 16px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Active Scenario Target:</span>
              <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--accent-cyan)' }}>
                {selectedScenarioMeta.scenario_name}
              </div>
            </div>

            {['MULTI_HOP_MULE_NETWORK', 'CROSS_BANK_MULE_NETWORK', 'CUSTOM_SCENARIO'].includes(selectedScenarioCode) && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Number of Hops:</span>
                <input 
                  type="number" 
                  min="2" 
                  max="10" 
                  value={numHops} 
                  onChange={(e) => setNumHops(parseInt(e.target.value) || 2)}
                  className="input-control"
                  style={{ width: '70px' }}
                />
              </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Historical Txns:</span>
              <input 
                type="number" 
                min="0" 
                max="50000" 
                value={historicalTxnCount} 
                onChange={(e) => setHistoricalTxnCount(parseInt(e.target.value) || 0)}
                className="input-control"
                style={{ width: '90px' }}
              />
            </div>
          </div>
        )}

        {/* Action Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '16px' }}>
          <button 
            type="submit" 
            className="btn-primary"
            disabled={isGenerating}
            style={{ padding: '12px 28px', fontSize: '0.95rem' }}
          >
            <Sparkles size={18} />
            <span>{isGenerating ? 'GENERATING SIMULATION...' : 'GENERATE ENVIRONMENT'}</span>
          </button>
        </div>

      </form>

    </div>
  );
};
