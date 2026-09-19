import React, { useState } from 'react';
import {
  ArrowRight,
  Smartphone,
  Laptop,
  Monitor,
  Tablet,
  MapPin,
  Search,
  CheckCircle2,
  Eye,
  ShieldAlert,
  Clock,
  Activity,
  Layers,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

const LIFECYCLE_BADGES = {
  INITIATED: {
    label: 'INITIATED',
    bg: 'rgba(6, 182, 212, 0.15)',
    color: '#06B6D4',
    border: '1px solid rgba(6, 182, 212, 0.35)',
    icon: Clock,
  },
  PROCESSING: {
    label: 'PROCESSING',
    bg: 'rgba(139, 92, 246, 0.18)',
    color: '#A78BFA',
    border: '1px solid rgba(139, 92, 246, 0.45)',
    icon: Activity,
  },
  ASSESSING: {
    label: 'PROCESSING',
    bg: 'rgba(139, 92, 246, 0.18)',
    color: '#A78BFA',
    border: '1px solid rgba(139, 92, 246, 0.45)',
    icon: Activity,
  },
  MONITORING: {
    label: 'MONITORING',
    bg: 'rgba(245, 158, 11, 0.18)',
    color: '#FBBF24',
    border: '1px solid rgba(245, 158, 11, 0.45)',
    icon: Eye,
  },
  UNDER_REVIEW: {
    label: 'UNDER REVIEW',
    bg: 'rgba(249, 115, 22, 0.20)',
    color: '#FB923C',
    border: '1px solid rgba(249, 115, 22, 0.5)',
    icon: ShieldAlert,
  },
  COMPLETED: {
    label: 'COMPLETED',
    bg: 'rgba(16, 185, 129, 0.15)',
    color: '#10B981',
    border: '1px solid rgba(16, 185, 129, 0.35)',
    icon: CheckCircle2,
  },
  SUCCESSFUL: {
    label: 'COMPLETED',
    bg: 'rgba(16, 185, 129, 0.15)',
    color: '#10B981',
    border: '1px solid rgba(16, 185, 129, 0.35)',
    icon: CheckCircle2,
  },
  RELEASED: {
    label: 'RELEASED',
    bg: 'rgba(52, 211, 153, 0.20)',
    color: '#34D399',
    border: '1px solid rgba(52, 211, 153, 0.45)',
    icon: CheckCircle2,
  },
  RESTRICTED: {
    label: 'RESTRICTED',
    bg: 'rgba(239, 68, 68, 0.22)',
    color: '#EF4444',
    border: '1px solid rgba(239, 68, 68, 0.5)',
    icon: ShieldAlert,
  },
  HONEYPOT: {
    label: 'HONEYPOT',
    bg: 'rgba(239, 68, 68, 0.25)',
    color: '#F87171',
    border: '1px solid rgba(239, 68, 68, 0.55)',
    icon: ShieldAlert,
  },
  'LIEN APPLIED': {
    label: 'LIEN APPLIED',
    bg: 'rgba(239, 68, 68, 0.25)',
    color: '#F87171',
    border: '1px solid rgba(239, 68, 68, 0.55)',
    icon: ShieldAlert,
  },
  FROZEN: {
    label: 'FROZEN',
    bg: 'rgba(159, 18, 57, 0.35)',
    color: '#FDA4AF',
    border: '1px solid rgba(244, 63, 94, 0.6)',
    icon: ShieldAlert,
  },
};


export function LiveTransactionFeed({
  transactions,
  selectedBank,
  onSelectBank,
  onSelectAccount,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [crossBankOnly, setCrossBankOnly] = useState(false);

  const getDeviceIcon = (deviceIp) => {
    const type = (deviceIp || '').split(':')[0].toLowerCase();
    if (type === 'mobile') return <Smartphone size={13} />;
    if (type === 'laptop') return <Laptop size={13} />;
    if (type === 'tablet') return <Tablet size={13} />;
    return <Monitor size={13} />;
  };

  const getBankBadgeStyle = (bank) => {
    if (bank === 'SBI') {
      return { bg: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', border: '1px solid rgba(59, 130, 246, 0.3)' };
    }
    if (bank === 'AXIS') {
      return { bg: 'rgba(168, 85, 247, 0.15)', color: '#C084FC', border: '1px solid rgba(168, 85, 247, 0.3)' };
    }
    return { bg: 'rgba(245, 158, 11, 0.15)', color: '#FBBF24', border: '1px solid rgba(245, 158, 11, 0.3)' };
  };

  const formatAmount = (amt) => `₹${Number(amt).toLocaleString('en-IN')}`;

  const formatTime = (ts) => {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return ts;
    }
  };

  // Filter transactions
  const filtered = transactions.filter((tx) => {
    if (selectedBank !== 'ALL') {
      if (tx.sender_bank !== selectedBank && tx.receiver_bank !== selectedBank) return false;
    }
    if (selectedType !== 'ALL' && tx.transaction_type !== selectedType) return false;
    if (selectedStatus !== 'ALL') {
      const st = (tx.transaction_status || 'COMPLETED').toUpperCase();
      if (selectedStatus === 'COMPLETED' && (st === 'COMPLETED' || st === 'SUCCESSFUL')) {
        // match
      } else if (st !== selectedStatus) {
        return false;
      }
    }
    if (crossBankOnly && !tx.is_cross_bank) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchId = tx.transaction_id.toLowerCase().includes(q);
      const matchSender = tx.sender_account_id.toLowerCase().includes(q);
      const matchReceiver = tx.receiver_account_id.toLowerCase().includes(q);
      const matchLoc = (tx.location || '').toLowerCase().includes(q);
      if (!matchId && !matchSender && !matchReceiver && !matchLoc) return false;
    }
    return true;
  });

  return (
    <div className="glass-panel" style={{ margin: '0 24px 24px 24px', display: 'flex', flexDirection: 'column' }}>
      
      {/* Real-Time Lifecycle Pipeline Guide Banner */}
      <div style={{
        padding: '10px 20px',
        background: 'rgba(15, 23, 42, 0.65)',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.72rem',
        color: 'var(--text-muted)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: '800', color: 'var(--accent-cyan)', letterSpacing: '0.04em' }}>
            LIFECYCLE FLOW:
          </span>
          <span style={{ color: '#06B6D4', fontWeight: '700' }}>INITIATED</span>
          <span>→</span>
          <span style={{ color: '#A78BFA', fontWeight: '700' }}>ASSESSING</span>
          <span>→</span>
          <span style={{ color: '#10B981', fontWeight: '700' }}>COMPLETED</span>
          <span style={{ color: 'var(--text-muted)' }}>/</span>
          <span style={{ color: '#FBBF24', fontWeight: '700' }}>MONITORING</span>
          <span style={{ color: 'var(--text-muted)' }}>/</span>
          <span style={{ color: '#EF4444', fontWeight: '700' }}>RESTRICTED</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={13} color="var(--accent-cyan)" />
          <span style={{ color: 'var(--text-secondary)' }}>Module 1 Transaction Generator</span>
        </div>
      </div>

      {/* Feed Controls Header */}
      <div style={{
        padding: '14px 20px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '14px',
      }}>
        {/* Left: Bank Filter Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-muted)', marginRight: '4px' }}>
            BANK VIEW:
          </span>
          {['ALL', 'SBI', 'AXIS', 'IOB'].map((b) => (
            <button
              key={b}
              onClick={() => onSelectBank(b)}
              style={{
                background: selectedBank === b ? 'rgba(0, 229, 255, 0.15)' : 'rgba(255, 255, 255, 0.04)',
                color: selectedBank === b ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                border: selectedBank === b ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)',
                padding: '4px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: '700',
                transition: 'all 0.18s ease',
              }}
            >
              {b}
            </button>
          ))}
        </div>

        {/* Right: Controls (Lifecycle, Channel, Cross-Bank, Search) */}
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '10px' }}>
          
          {/* Lifecycle Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '0.8rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="ALL">All Lifecycle Statuses</option>
            <option value="INITIATED">INITIATED</option>
            <option value="ASSESSING">ASSESSING</option>
            <option value="COMPLETED">COMPLETED</option>
            <option value="MONITORING">MONITORING</option>
            <option value="RESTRICTED">RESTRICTED</option>
          </select>

          {/* Channel Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '0.8rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="ALL">All Channels</option>
            <option value="UPI">UPI</option>
            <option value="IMPS">IMPS</option>
            <option value="NEFT">NEFT</option>
            <option value="BANK_TRANSFER">Bank Transfer</option>
          </select>

          {/* Cross-Bank Only Toggle */}
          <button
            onClick={() => setCrossBankOnly(!crossBankOnly)}
            style={{
              background: crossBankOnly ? 'rgba(168, 85, 247, 0.2)' : 'rgba(255, 255, 255, 0.04)',
              color: crossBankOnly ? '#C084FC' : 'var(--text-secondary)',
              border: crossBankOnly ? '1px solid #C084FC' : '1px solid var(--border-color)',
              padding: '6px 12px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>Cross-Bank</span>
          </button>

          {/* Search Box */}
          <div style={{ position: 'relative', minWidth: '180px' }}>
            <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search account, ID…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                padding: '6px 12px 6px 30px',
                color: 'var(--text-primary)',
                fontSize: '0.8rem',
                width: '100%',
                outline: 'none',
              }}
            />
          </div>

        </div>
      </div>

      {/* Transactions Table */}
      <div style={{ overflowX: 'auto', maxHeight: '580px', overflowY: 'auto' }}>
        {filtered.length === 0 ? (
          <div style={{
            padding: '48px 24px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.875rem',
          }}>
            Waiting for live transactions from simulator...
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
            <thead>
              <tr style={{
                background: 'rgba(255, 255, 255, 0.02)',
                borderBottom: '1px solid var(--border-color)',
                textAlign: 'left',
                color: 'var(--text-muted)',
                fontSize: '0.725rem',
                fontWeight: '700',
                letterSpacing: '0.05em',
              }}>
                <th style={{ padding: '12px 14px' }}>TIME / TXN ID</th>
                <th style={{ padding: '12px 14px' }}>LIFECYCLE STATUS</th>
                <th style={{ padding: '12px 14px' }}>SENDER</th>
                <th style={{ padding: '12px 14px', textAlign: 'center' }}>FLOW</th>
                <th style={{ padding: '12px 14px' }}>RECEIVER</th>
                <th style={{ padding: '12px 14px', textAlign: 'right' }}>AMOUNT</th>
                <th style={{ padding: '12px 14px' }}>CHANNEL & DEVICE</th>
                <th style={{ padding: '12px 14px' }}>LOCATION</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((tx) => {
                const sBadge = getBankBadgeStyle(tx.sender_bank);
                const rBadge = getBankBadgeStyle(tx.receiver_bank);
                
                const rawStatus = (tx.transaction_status || 'COMPLETED').toUpperCase();
                const statusMeta = LIFECYCLE_BADGES[rawStatus] || LIFECYCLE_BADGES.COMPLETED;
                const StatusIcon = statusMeta.icon;

                return (
                  <tr
                    key={tx.transaction_id}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      background: 'transparent',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'transparent';
                    }}
                  >
                    {/* Timestamp & ID */}
                    <td style={{ padding: '12px 14px' }}>
                      <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {formatTime(tx.transaction_timestamp)}
                      </div>
                      <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {tx.transaction_id}
                      </div>
                    </td>

                    {/* Lifecycle Status Badge */}
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '3px 8px',
                        borderRadius: '5px',
                        fontSize: '0.68rem',
                        fontWeight: '800',
                        letterSpacing: '0.04em',
                        background: statusMeta.bg,
                        color: statusMeta.color,
                        border: statusMeta.border,
                      }}>
                        <StatusIcon size={11} />
                        <span>{statusMeta.label}</span>
                      </span>
                    </td>

                    {/* Sender Account */}
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{
                          padding: '1px 5px',
                          borderRadius: '4px',
                          fontSize: '0.675rem',
                          fontWeight: '700',
                          background: sBadge.bg,
                          color: sBadge.color,
                          border: sBadge.border,
                        }}>
                          {tx.sender_bank}
                        </span>
                        <button
                          onClick={() => onSelectAccount(tx.sender_bank, tx.sender_account_id)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--accent-cyan)',
                            fontWeight: '600',
                            cursor: 'pointer',
                            textDecoration: 'underline',
                            fontSize: '0.8rem',
                          }}
                          className="mono"
                        >
                          {tx.sender_account_id}
                        </button>
                      </div>
                      {tx.sender_balance_after !== null && tx.sender_balance_after !== undefined && (
                        <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Bal: {formatAmount(tx.sender_balance_after)}
                        </div>
                      )}
                    </td>

                    {/* Flow Badge (Intra vs Cross) */}
                    <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                        <ArrowRight size={13} color={tx.is_cross_bank ? '#C084FC' : 'var(--text-muted)'} />
                        {tx.is_cross_bank && (
                          <span style={{
                            fontSize: '0.6rem',
                            fontWeight: '700',
                            padding: '1px 4px',
                            borderRadius: '4px',
                            background: 'rgba(168, 85, 247, 0.15)',
                            color: '#C084FC',
                            border: '1px solid rgba(168, 85, 247, 0.3)',
                          }}>
                            INTER
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Receiver Account */}
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{
                          padding: '1px 5px',
                          borderRadius: '4px',
                          fontSize: '0.675rem',
                          fontWeight: '700',
                          background: rBadge.bg,
                          color: rBadge.color,
                          border: rBadge.border,
                        }}>
                          {tx.receiver_bank}
                        </span>
                        <button
                          onClick={() => onSelectAccount(tx.receiver_bank, tx.receiver_account_id)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--accent-cyan)',
                            fontWeight: '600',
                            cursor: 'pointer',
                            textDecoration: 'underline',
                            fontSize: '0.8rem',
                          }}
                          className="mono"
                        >
                          {tx.receiver_account_id}
                        </button>
                        {tx.recipient_is_new && (
                          <span style={{
                            fontSize: '0.6rem',
                            fontWeight: '700',
                            padding: '1px 4px',
                            borderRadius: '3px',
                            background: 'rgba(245, 158, 11, 0.15)',
                            color: '#FBBF24',
                            border: '1px solid rgba(245, 158, 11, 0.3)',
                          }}>
                            NEW
                          </span>
                        )}
                      </div>
                      {tx.receiver_balance_after !== null && tx.receiver_balance_after !== undefined && (
                        <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Bal: {formatAmount(tx.receiver_balance_after)}
                        </div>
                      )}
                    </td>

                    {/* Amount */}
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <div className="mono" style={{ fontWeight: '700', color: '#10B981', fontSize: '0.88rem' }}>
                        {formatAmount(tx.amount)}
                      </div>
                    </td>

                    {/* Channel & Device */}
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <span style={{
                          fontSize: '0.68rem',
                          fontWeight: '700',
                          padding: '1px 5px',
                          borderRadius: '4px',
                          background: 'rgba(255, 255, 255, 0.06)',
                          color: 'var(--text-primary)',
                        }}>
                          {tx.transaction_type}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {getDeviceIcon(tx.device_ip)}
                        <span>{tx.device_ip || 'Mobile:192.168.1.1'}</span>
                      </div>
                    </td>

                    {/* Location */}
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)' }}>
                        <MapPin size={12} color="var(--accent-cyan)" />
                        <span>{tx.location || 'Chennai'}</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Status Bar */}
      <div style={{
        padding: '10px 20px',
        background: 'rgba(7, 9, 14, 0.7)',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '0.75rem',
        color: 'var(--text-muted)',
      }}>
        <div>
          Showing <strong>{filtered.length}</strong> of <strong>{transactions.length}</strong> stream events
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#10B981' }}>
            <CheckCircle2 size={13} /> Completed
          </span>
          <span style={{ color: 'var(--border-color)' }}>•</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#FBBF24' }}>
            <Eye size={13} /> Monitored
          </span>
          <span style={{ color: 'var(--border-color)' }}>•</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#EF4444' }}>
            <ShieldAlert size={13} /> Restricted
          </span>
        </div>
      </div>

    </div>
  );
}
