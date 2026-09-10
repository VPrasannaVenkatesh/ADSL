import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Search, 
  Filter, 
  Eye, 
  X, 
  Smartphone, 
  MapPin, 
  Clock, 
  Shield, 
  AlertTriangle,
  ArrowUpRight,
  TrendingUp
} from 'lucide-react';
import { GroundTruthBadge } from './GroundTruthBadge';
import { formatINR } from '../utils/formatters';

export const AccountExplorer = ({ accounts = [], banks = [], onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBankId, setSelectedBankId] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [selectedAccount, setSelectedAccount] = useState(null);

  const filteredAccounts = accounts.filter((acc) => {
    const matchesSearch = 
      acc.account_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      acc.account_holder_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      acc.account_number.includes(searchTerm);

    const matchesBank = selectedBankId ? acc.bank_id === selectedBankId : true;
    const matchesType = selectedType ? acc.account_type_ground_truth === selectedType : true;

    return matchesSearch && matchesBank && matchesType;
  });

  return (
    <div className="glass-panel" style={{ padding: '24px', margin: '0 20px 24px 20px' }}>
      
      {/* Header Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={18} color="var(--accent-cyan)" />
            <span>Account Explorer & Behavioural Profiles</span>
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Inspecting {filteredAccounts.length} of {accounts.length} simulated accounts
          </span>
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Search Box */}
          <div style={{ position: 'relative', width: '220px' }}>
            <Search size={15} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
            <input 
              type="text" 
              placeholder="Search ID, Name..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-control"
              style={{ paddingLeft: '32px', fontSize: '0.85rem' }}
            />
          </div>

          {/* Bank Filter */}
          <select 
            className="input-control" 
            style={{ width: '160px' }}
            value={selectedBankId}
            onChange={(e) => setSelectedBankId(e.target.value)}
          >
            <option value="">All Banks</option>
            {banks.map((b) => (
              <option key={b.id} value={b.id}>{b.bank_name}</option>
            ))}
          </select>

          {/* Type Filter */}
          <select 
            className="input-control" 
            style={{ width: '160px' }}
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          >
            <option value="">All Ground Truth</option>
            <option value="GENUINE">Genuine</option>
            <option value="MULE">Mule</option>
            <option value="COMPROMISED">Compromised</option>
          </select>
        </div>
      </div>

      {/* Account Table */}
      <div style={{ overflowX: 'auto', maxHeight: '420px', overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-secondary)', zIndex: 2 }}>
            <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
              <th style={{ padding: '10px 12px' }}>Account ID</th>
              <th style={{ padding: '10px 12px' }}>Holder Name</th>
              <th style={{ padding: '10px 12px' }}>Bank</th>
              <th style={{ padding: '10px 12px' }}>Ground Truth</th>
              <th style={{ padding: '10px 12px' }}>Age</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Ledger Balance</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Available Balance</th>
              <th style={{ padding: '10px 12px', textAlign: 'center' }}>Profile</th>
            </tr>
          </thead>
          <tbody>
            {filteredAccounts.map((acc) => (
              <tr 
                key={acc.id} 
                style={{ 
                  borderBottom: '1px solid rgba(255,255,255,0.03)',
                  cursor: 'pointer' 
                }}
                className="table-row-hover"
                onClick={() => setSelectedAccount(acc)}
              >
                <td style={{ padding: '10px 12px', fontWeight: '600' }} className="mono">
                  {acc.account_id}
                </td>
                <td style={{ padding: '10px 12px', color: 'var(--text-primary)' }}>
                  {acc.account_holder_name}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>
                    {acc.bank_name || acc.bank_code}
                  </span>
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <GroundTruthBadge type={acc.account_type_ground_truth} />
                </td>
                <td style={{ padding: '10px 12px', color: 'var(--text-muted)' }}>
                  {acc.account_age_days}d
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: '600' }} className="mono">
                  {formatINR(acc.ledger_balance)}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: '600', color: 'var(--status-genuine)' }} className="mono">
                  {formatINR(acc.available_balance)}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                  <button 
                    onClick={(e) => { e.stopPropagation(); setSelectedAccount(acc); }}
                    className="btn-secondary"
                    style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                  >
                    <Eye size={13} />
                    <span>Inspect</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Account Profile Inspector Modal */}
      {selectedAccount && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '680px', maxHeight: '90vh', overflowY: 'auto', padding: '24px', position: 'relative' }}>
            
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '14px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: '700' }} className="mono">{selectedAccount.account_id}</h3>
                  <GroundTruthBadge type={selectedAccount.account_type_ground_truth} />
                </div>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {selectedAccount.account_holder_name} — {selectedAccount.bank_name} ({selectedAccount.account_number})
                </span>
              </div>

              <button 
                onClick={() => setSelectedAccount(null)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Balances & Age Overview */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: 'rgba(7, 9, 14, 0.6)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>LEDGER BALANCE</span>
                <div style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }} className="mono">
                  {formatINR(selectedAccount.ledger_balance)}
                </div>
              </div>
              <div style={{ background: 'rgba(7, 9, 14, 0.6)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--status-genuine)' }}>AVAILABLE BALANCE</span>
                <div style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--status-genuine)', marginTop: '2px' }} className="mono">
                  {formatINR(selectedAccount.available_balance)}
                </div>
              </div>
              <div style={{ background: 'rgba(7, 9, 14, 0.6)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>ACCOUNT TENURE</span>
                <div style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                  {selectedAccount.account_age_days} Days
                </div>
              </div>
            </div>

            {/* Profile Baseline Details */}
            {selectedAccount.profile ? (
              <div>
                <h4 style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--accent-cyan)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <TrendingUp size={16} />
                  <span>Hidden Behavioural Profile (Simulation Baseline)</span>
                </h4>

                {/* Amount & Frequency Metrics */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', marginBottom: '16px' }}>
                  <div style={{ background: 'rgba(13, 17, 26, 0.8)', padding: '10px 14px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Normal Amount Range:</span>
                    <div style={{ fontSize: '0.85rem', fontWeight: '600', marginTop: '2px' }} className="mono">
                      {formatINR(selectedAccount.profile.min_txn_amount)} – {formatINR(selectedAccount.profile.max_txn_amount)} (Avg: {formatINR(selectedAccount.profile.avg_txn_amount)})
                    </div>
                  </div>

                  <div style={{ background: 'rgba(13, 17, 26, 0.8)', padding: '10px 14px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Transaction Frequency & Hours:</span>
                    <div style={{ fontSize: '0.85rem', fontWeight: '600', marginTop: '2px' }}>
                      {selectedAccount.profile.txn_frequency_per_day} txns/day | Hours: {selectedAccount.profile.typical_hours?.[0]}:00 – {selectedAccount.profile.typical_hours?.[1]}:00
                    </div>
                  </div>
                </div>

                {/* Devices & Locations */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', marginBottom: '16px' }}>
                  <div style={{ background: 'rgba(13, 17, 26, 0.8)', padding: '10px 14px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Smartphone size={13} />
                      <span>Known Hardware Devices</span>
                    </span>
                    <div style={{ marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {selectedAccount.profile.known_devices?.map((dev, i) => (
                        <span key={i} className="mono" style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.04)', padding: '2px 6px', borderRadius: '4px' }}>
                          {dev}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(13, 17, 26, 0.8)', padding: '10px 14px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MapPin size={13} />
                      <span>Known Habitual Locations</span>
                    </span>
                    <div style={{ marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {selectedAccount.profile.known_locations?.map((loc, i) => (
                        <span key={i} style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.04)', padding: '2px 6px', borderRadius: '4px' }}>
                          {loc}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Mule or Compromised Special Parameters */}
                {selectedAccount.account_type_ground_truth === 'MULE' && selectedAccount.profile.mule_behavior_params && (
                  <div style={{
                    background: 'rgba(245, 158, 11, 0.08)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    borderRadius: '6px',
                    padding: '12px',
                    marginBottom: '12px'
                  }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--status-mule)' }}>
                      Mule Layering Configuration:
                    </span>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginTop: '6px', fontSize: '0.75rem' }}>
                      <div>Fan-in Capacity: <strong>{selectedAccount.profile.mule_behavior_params.fan_in_capacity}</strong></div>
                      <div>Fan-out Capacity: <strong>{selectedAccount.profile.mule_behavior_params.fan_out_capacity}</strong></div>
                      <div>Dwell Time: <strong>{selectedAccount.profile.mule_behavior_params.dwell_time_minutes} mins</strong></div>
                    </div>
                  </div>
                )}

                {selectedAccount.account_type_ground_truth === 'COMPROMISED' && selectedAccount.profile.compromised_behavior_params && (
                  <div style={{
                    background: 'rgba(239, 68, 68, 0.08)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '6px',
                    padding: '12px',
                    marginBottom: '12px'
                  }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--status-compromised)' }}>
                      Takeover Attack Profile:
                    </span>
                    <div style={{ marginTop: '6px', fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div>Rogue Device ID: <code className="mono">{selectedAccount.profile.compromised_behavior_params.rogue_device}</code></div>
                      <div>Rogue Location/IP: <code>{selectedAccount.profile.compromised_behavior_params.rogue_location}</code></div>
                      <div>Drain Percentage: <strong>{(selectedAccount.profile.compromised_behavior_params.drain_amount_percentage * 100).toFixed(0)}%</strong></div>
                    </div>
                  </div>
                )}

              </div>
            ) : (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No behavioral profile details found.</p>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button 
                onClick={() => setSelectedAccount(null)}
                className="btn-secondary"
              >
                Close Inspector
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
