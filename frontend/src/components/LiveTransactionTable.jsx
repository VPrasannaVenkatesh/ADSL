import React, { useState, useMemo } from 'react';
import {
  Search,
  ArrowUpDown,
  Smartphone,
  Laptop,
  Monitor,
  Tablet,
  MapPin,
  Clock,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  CheckCircle2,
  Activity,
  Eye,
  Lock,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Filter,
} from 'lucide-react';

const STATUS_CONFIG = {
  PROCESSING: {
    label: 'PROCESSING',
    bg: 'rgba(139, 92, 246, 0.15)',
    color: '#A78BFA',
    border: '1px solid rgba(139, 92, 246, 0.4)',
    icon: Activity,
  },
  COMPLETED: {
    label: 'COMPLETED',
    bg: 'rgba(16, 185, 129, 0.15)',
    color: '#10B981',
    border: '1px solid rgba(16, 185, 129, 0.35)',
    icon: CheckCircle2,
  },
  MONITORING: {
    label: 'MONITORING',
    bg: 'rgba(245, 158, 11, 0.15)',
    color: '#FBBF24',
    border: '1px solid rgba(245, 158, 11, 0.4)',
    icon: Eye,
  },
  HONEYPOT: {
    label: 'HONEYPOT',
    bg: 'rgba(6, 182, 212, 0.18)',
    color: '#22D3EE',
    border: '1px solid rgba(6, 182, 212, 0.45)',
    icon: ShieldAlert,
  },
  LIEN_APPLIED: {
    label: 'LIEN APPLIED',
    bg: 'rgba(249, 115, 22, 0.18)',
    color: '#FB923C',
    border: '1px solid rgba(249, 115, 22, 0.45)',
    icon: Lock,
  },
  RELEASED: {
    label: 'RELEASED',
    bg: 'rgba(52, 211, 153, 0.18)',
    color: '#34D399',
    border: '1px solid rgba(52, 211, 153, 0.4)',
    icon: CheckCircle2,
  },
  RESTRICTED: {
    label: 'RESTRICTED',
    bg: 'rgba(239, 68, 68, 0.20)',
    color: '#EF4444',
    border: '1px solid rgba(239, 68, 68, 0.45)',
    icon: ShieldAlert,
  },
  FROZEN: {
    label: 'FROZEN',
    bg: 'rgba(159, 18, 57, 0.3)',
    color: '#FDA4AF',
    border: '1px solid rgba(244, 63, 94, 0.55)',
    icon: ShieldAlert,
  },
};

const HONEYPOT_CONFIG = {
  NOT_TRANSFERRED: {
    label: 'NO',
    bg: 'rgba(148, 163, 184, 0.08)',
    color: '#94A3B8',
    border: '1px solid rgba(148, 163, 184, 0.2)',
  },
  TRANSFERRED: {
    label: 'TRANSFERRED',
    bg: 'rgba(6, 182, 212, 0.18)',
    color: '#22D3EE',
    border: '1px solid rgba(6, 182, 212, 0.45)',
  },
  ACTIVE: {
    label: 'ACTIVE',
    bg: 'rgba(59, 130, 246, 0.18)',
    color: '#60A5FA',
    border: '1px solid rgba(59, 130, 246, 0.45)',
  },
  RELEASED: {
    label: 'RELEASED',
    bg: 'rgba(52, 211, 153, 0.18)',
    color: '#34D399',
    border: '1px solid rgba(52, 211, 153, 0.4)',
  },
  // Fallbacks for historical or raw statuses
  HONEYPOT: {
    label: 'TRANSFERRED',
    bg: 'rgba(6, 182, 212, 0.18)',
    color: '#22D3EE',
    border: '1px solid rgba(6, 182, 212, 0.45)',
  },
  NONE: {
    label: 'NO',
    bg: 'rgba(148, 163, 184, 0.08)',
    color: '#94A3B8',
    border: '1px solid rgba(148, 163, 184, 0.2)',
  },
};

const LIEN_CONFIG = {
  NO_LIEN: {
    label: 'NO',
    bg: 'rgba(148, 163, 184, 0.08)',
    color: '#94A3B8',
    border: '1px solid rgba(148, 163, 184, 0.2)',
  },
  LIEN_APPLIED: {
    label: 'LIEN HELD',
    bg: 'rgba(249, 115, 22, 0.2)',
    color: '#FB923C',
    border: '1px solid rgba(249, 115, 22, 0.45)',
  },
  LIEN_RELEASED: {
    label: 'RELEASED',
    bg: 'rgba(52, 211, 153, 0.18)',
    color: '#34D399',
    border: '1px solid rgba(52, 211, 153, 0.4)',
  },
  // Fallbacks for historical or raw receipt statuses
  LIEN: {
    label: 'LIEN HELD',
    bg: 'rgba(249, 115, 22, 0.2)',
    color: '#FB923C',
    border: '1px solid rgba(249, 115, 22, 0.45)',
  },
  RESTRICTED: {
    label: 'LIEN HELD',
    bg: 'rgba(249, 115, 22, 0.2)',
    color: '#FB923C',
    border: '1px solid rgba(249, 115, 22, 0.45)',
  },
  NONE: {
    label: 'NO',
    bg: 'rgba(148, 163, 184, 0.08)',
    color: '#94A3B8',
    border: '1px solid rgba(148, 163, 184, 0.2)',
  },
};

const BANK_COLORS = {
  SBI: { bg: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', border: 'rgba(59, 130, 246, 0.35)' },
  AXIS: { bg: 'rgba(236, 72, 153, 0.15)', color: '#F472B6', border: 'rgba(236, 72, 153, 0.35)' },
  IOB: { bg: 'rgba(245, 158, 11, 0.15)', color: '#FBBF24', border: 'rgba(245, 158, 11, 0.35)' },
};

export function LiveTransactionTable({
  transactions = [],
  selectedBank = 'ALL',
  onSelectBank,
  onSelectAccount,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [selectedType, setSelectedType] = useState('ALL');
  const [sortDesc, setSortDesc] = useState(true);
  const [expandedTxId, setExpandedTxId] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const getDeviceIcon = (deviceIp) => {
    const type = (deviceIp || '').split(':')[0].toLowerCase();
    if (type === 'mobile') return <Smartphone size={12} />;
    if (type === 'laptop') return <Laptop size={12} />;
    if (type === 'tablet') return <Tablet size={12} />;
    return <Monitor size={12} />;
  };

  const formatAmount = (amt) => `₹${Number(amt || 0).toLocaleString('en-IN')}`;

  const formatTime = (ts) => {
    if (!ts) return '--:--:--';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      });
    } catch {
      return ts;
    }
  };

  const formatDate = (ts) => {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return '';
    }
  };

  // Filtered & Sorted Transactions
  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      // Bank filter
      if (selectedBank !== 'ALL') {
        if (tx.sender_bank !== selectedBank && tx.receiver_bank !== selectedBank) {
          return false;
        }
      }
      // Status filter
      if (selectedStatus !== 'ALL') {
        const st = (tx.transaction_status || 'COMPLETED').toUpperCase();
        if (selectedStatus === 'LIEN_APPLIED') {
          if (st !== 'LIEN_APPLIED' && tx.lien_status !== 'LIEN_APPLIED') return false;
        } else if (selectedStatus === 'HONEYPOT') {
          if (st !== 'HONEYPOT' && tx.honeypot_status !== 'TRANSFERRED') return false;
        } else if (st !== selectedStatus) {
          return false;
        }
      }
      // Type filter
      if (selectedType !== 'ALL') {
        if (tx.transaction_type !== selectedType) return false;
      }
      // Search term
      if (searchTerm) {
        const q = searchTerm.toLowerCase();
        const matchId = (tx.transaction_id || '').toLowerCase().includes(q);
        const matchSender = (tx.sender_account_id || '').toLowerCase().includes(q);
        const matchReceiver = (tx.receiver_account_id || '').toLowerCase().includes(q);
        const matchLoc = (tx.location || '').toLowerCase().includes(q);
        if (!matchId && !matchSender && !matchReceiver && !matchLoc) return false;
      }
      return true;
    }).sort((a, b) => {
      const tA = new Date(a.transaction_timestamp || 0).getTime();
      const tB = new Date(b.transaction_timestamp || 0).getTime();
      return sortDesc ? tB - tA : tA - tB;
    });
  }, [transactions, selectedBank, selectedStatus, selectedType, searchTerm, sortDesc]);

  // Pagination slice
  const totalPages = Math.max(1, Math.ceil(filteredTransactions.length / pageSize));
  const paginatedTransactions = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredTransactions.slice(start, start + pageSize);
  }, [filteredTransactions, currentPage, pageSize]);

  return (
    <div className="glass-panel" style={{
      margin: '0 24px 24px 24px',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Table Control & Filter Bar */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '14px',
        background: 'rgba(10, 15, 26, 0.75)',
      }}>
        {/* Left: Bank Filter Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-muted)', marginRight: '4px' }}>
            BANK VIEW:
          </span>
          {['ALL', 'SBI', 'AXIS', 'IOB'].map((b) => {
            const isSelected = selectedBank === b;
            return (
              <button
                key={b}
                onClick={() => {
                  onSelectBank(b);
                  setCurrentPage(1);
                }}
                style={{
                  background: isSelected ? 'rgba(0, 229, 255, 0.15)' : 'rgba(255, 255, 255, 0.04)',
                  color: isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)',
                  padding: '5px 12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.78rem',
                  fontWeight: '700',
                  transition: 'all 0.18s ease',
                }}
              >
                {b}
              </button>
            );
          })}
        </div>

        {/* Right: Search, Status, Type, and Time Sort */}
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '10px' }}>
          {/* Status Dropdown Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status:</span>
            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setCurrentPage(1);
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '6px 10px',
                borderRadius: '6px',
                fontSize: '0.78rem',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="PROCESSING">PROCESSING</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="MONITORING">MONITORING</option>
              <option value="HONEYPOT">HONEYPOT</option>
              <option value="LIEN_APPLIED">LIEN APPLIED</option>
              <option value="RELEASED">RELEASED</option>
              <option value="RESTRICTED">RESTRICTED</option>
              <option value="FROZEN">FROZEN</option>
            </select>
          </div>

          {/* Payment Type Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Type:</span>
            <select
              value={selectedType}
              onChange={(e) => {
                setSelectedType(e.target.value);
                setCurrentPage(1);
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '6px 10px',
                borderRadius: '6px',
                fontSize: '0.78rem',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="ALL">All Types</option>
              <option value="UPI">UPI</option>
              <option value="IMPS">IMPS</option>
              <option value="NEFT">NEFT</option>
              <option value="BANK_TRANSFER">BANK TRANSFER</option>
            </select>
          </div>

          {/* Search Box */}
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search account, ID, city..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                padding: '6px 12px 6px 30px',
                fontSize: '0.78rem',
                color: 'var(--text-primary)',
                width: '180px',
                outline: 'none',
              }}
            />
          </div>

          {/* Time Sort Toggle */}
          <button
            onClick={() => setSortDesc(!sortDesc)}
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)',
              padding: '6px 10px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.78rem',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
            title="Toggle time sort order"
          >
            <ArrowUpDown size={13} />
            <span>{sortDesc ? 'Newest' : 'Oldest'}</span>
          </button>
        </div>
      </div>

      {/* Main Professional Banking Transaction Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          textAlign: 'left',
          fontSize: '0.81rem',
        }}>
          <thead>
            <tr style={{
              background: 'rgba(15, 23, 42, 0.9)',
              color: 'var(--text-muted)',
              fontSize: '0.72rem',
              fontWeight: '700',
              letterSpacing: '0.05em',
              borderBottom: '1px solid var(--border-color)',
            }}>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>TIME</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>SENDER</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>SENDER BANK</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>RECEIVER</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>RECEIVER BANK</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap', textAlign: 'right' }}>AMOUNT</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>TYPE</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>DEVICE</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>LOCATION</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>STATUS</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap', textAlign: 'center' }}>HONEYPOT</th>
              <th style={{ padding: '12px 16px', whiteSpace: 'nowrap', textAlign: 'center' }}>LIEN</th>
              <th style={{ padding: '12px 16px', width: '40px' }}></th>
            </tr>
          </thead>
          <tbody>
            {paginatedTransactions.length === 0 ? (
              <tr>
                <td colSpan={13} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No transactions match the selected filters or search criteria.
                </td>
              </tr>
            ) : (
              paginatedTransactions.map((tx) => {
                const statusKey = (tx.transaction_status || 'COMPLETED').toUpperCase();
                const stCfg = STATUS_CONFIG[statusKey] || STATUS_CONFIG.COMPLETED;
                const StIcon = stCfg.icon;

                const hpKey = (tx.honeypot_status || 'NOT_TRANSFERRED').toUpperCase();
                const hpCfg = HONEYPOT_CONFIG[hpKey] || HONEYPOT_CONFIG.NOT_TRANSFERRED;

                const lienKey = (tx.lien_status || 'NO_LIEN').toUpperCase();
                const lienCfg = LIEN_CONFIG[lienKey] || LIEN_CONFIG.NO_LIEN;

                const sBankStyle = BANK_COLORS[tx.sender_bank] || BANK_COLORS.SBI;
                const rBankStyle = BANK_COLORS[tx.receiver_bank] || BANK_COLORS.SBI;

                const isExpanded = expandedTxId === tx.transaction_id;

                return (
                  <React.Fragment key={tx.transaction_id}>
                    <tr
                      onClick={() => setExpandedTxId(isExpanded ? null : tx.transaction_id)}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        background: isExpanded ? 'rgba(0, 229, 255, 0.04)' : 'transparent',
                        cursor: 'pointer',
                        transition: 'background 0.15s ease',
                      }}
                      className="table-row-hover"
                    >
                      {/* Time */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                        <div className="mono" style={{ fontWeight: '600', color: '#FFFFFF' }}>
                          {formatTime(tx.transaction_timestamp)}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {formatDate(tx.transaction_timestamp)}
                        </div>
                      </td>

                      {/* Sender */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                        <span
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectAccount && onSelectAccount(tx.sender_bank, tx.sender_account_id);
                          }}
                          className="mono"
                          style={{
                            fontWeight: '700',
                            color: 'var(--accent-cyan)',
                            cursor: 'pointer',
                            textDecoration: 'underline',
                            textUnderlineOffset: '2px',
                          }}
                          title="Click to view Account Explorer"
                        >
                          {tx.sender_account_id}
                        </span>
                      </td>

                      {/* Sender Bank */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '0.72rem',
                          fontWeight: '800',
                          background: sBankStyle.bg,
                          color: sBankStyle.color,
                          border: `1px solid ${sBankStyle.border}`,
                        }}>
                          {tx.sender_bank}
                        </span>
                      </td>

                      {/* Receiver */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                        <span
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectAccount && onSelectAccount(tx.receiver_bank, tx.receiver_account_id);
                          }}
                          className="mono"
                          style={{
                            fontWeight: '700',
                            color: 'var(--accent-cyan)',
                            cursor: 'pointer',
                            textDecoration: 'underline',
                            textUnderlineOffset: '2px',
                          }}
                          title="Click to view Account Explorer"
                        >
                          {tx.receiver_account_id}
                        </span>
                      </td>

                      {/* Receiver Bank */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '0.72rem',
                          fontWeight: '800',
                          background: rBankStyle.bg,
                          color: rBankStyle.color,
                          border: `1px solid ${rBankStyle.border}`,
                        }}>
                          {tx.receiver_bank}
                        </span>
                      </td>

                      {/* Amount */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap', textAlign: 'right' }}>
                        <span className="mono" style={{ fontWeight: '800', fontSize: '0.88rem', color: '#FFFFFF' }}>
                          {formatAmount(tx.amount)}
                        </span>
                      </td>

                      {/* Type */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                        <span style={{
                          fontSize: '0.72rem',
                          fontWeight: '700',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: 'rgba(255, 255, 255, 0.05)',
                          color: 'var(--text-secondary)',
                        }}>
                          {tx.transaction_type}
                        </span>
                      </td>

                      {/* Device */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
                          {getDeviceIcon(tx.device_ip)}
                          <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                            {(tx.device_ip || '').split(':')[0] || 'Mobile'}
                          </span>
                        </div>
                      </td>

                      {/* Location */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)' }}>
                          <MapPin size={11} color="var(--accent-cyan)" />
                          <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                            {tx.location || 'Chennai'}
                          </span>
                        </div>
                      </td>

                      {/* Status */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                          padding: '3px 9px',
                          borderRadius: '5px',
                          fontSize: '0.72rem',
                          fontWeight: '700',
                          background: stCfg.bg,
                          color: stCfg.color,
                          border: stCfg.border,
                        }}>
                          <StIcon size={11} />
                          <span>{stCfg.label}</span>
                        </span>
                      </td>

                      {/* Honeypot Status */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap', textAlign: 'center' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '0.7rem',
                          fontWeight: '700',
                          background: hpCfg.bg,
                          color: hpCfg.color,
                          border: hpCfg.border,
                        }}>
                          {hpCfg.label}
                        </span>
                      </td>

                      {/* Lien Status */}
                      <td style={{ padding: '12px 16px', whiteSpace: 'nowrap', textAlign: 'center' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '0.7rem',
                          fontWeight: '700',
                          background: lienCfg.bg,
                          color: lienCfg.color,
                          border: lienCfg.border,
                        }}>
                          {lienCfg.label}
                        </span>
                      </td>

                      {/* Expand Arrow */}
                      <td style={{ padding: '12px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
                        {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                      </td>
                    </tr>

                    {/* Expandable Transaction Details Row */}
                    {isExpanded && (
                      <tr style={{ background: 'rgba(15, 23, 42, 0.85)', borderBottom: '1px solid var(--border-color)' }}>
                        <td colSpan={13} style={{ padding: '16px 24px' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', fontSize: '0.78rem' }}>
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Transaction ID:</span>{' '}
                              <span className="mono" style={{ color: '#FFFFFF', fontWeight: '700' }}>{tx.transaction_id}</span>
                            </div>
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Cross-Bank Transfer:</span>{' '}
                              <strong style={{ color: tx.is_cross_bank ? '#C084FC' : '#60A5FA' }}>
                                {tx.is_cross_bank ? `Yes (${tx.sender_bank} ➔ ${tx.receiver_bank})` : `No (Intra-${tx.sender_bank})`}
                              </strong>
                            </div>
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Beneficiary Status:</span>{' '}
                              <span style={{ color: tx.recipient_is_new ? '#F59E0B' : '#10B981', fontWeight: '600' }}>
                                {tx.recipient_is_new ? 'New Recipient' : 'Established Beneficiary'}
                              </span>
                            </div>
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Device IP:</span>{' '}
                              <code style={{ color: 'var(--text-secondary)' }}>{tx.device_ip || 'N/A'}</code>
                            </div>
                            {tx.sender_balance_before !== undefined && (
                              <div>
                                <span style={{ color: 'var(--text-muted)' }}>Sender Balance:</span>{' '}
                                <span className="mono" style={{ color: 'var(--text-secondary)' }}>
                                  {formatAmount(tx.sender_balance_before)} ➔ {formatAmount(tx.sender_balance_after)}
                                </span>
                              </div>
                            )}
                            {tx.receiver_balance_before !== undefined && (
                              <div>
                                <span style={{ color: 'var(--text-muted)' }}>Receiver Balance:</span>{' '}
                                <span className="mono" style={{ color: 'var(--text-secondary)' }}>
                                  {formatAmount(tx.receiver_balance_before)} ➔ {formatAmount(tx.receiver_balance_after)}
                                </span>
                              </div>
                            )}
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Honeypot Decoy:</span>{' '}
                              <strong style={{ color: hpCfg.color }}>
                                {hpCfg.label === 'TRANSFERRED' ? 'Transferred to Decoy Honeypot' : (hpCfg.label === 'RELEASED' ? 'Released from Honeypot' : 'Direct Account Routing (No Decoy)')}
                              </strong>
                            </div>
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Lien Enforcement:</span>{' '}
                              <strong style={{ color: lienCfg.color }}>
                                {lienCfg.label === 'LIEN HELD' ? 'Active Capital Quarantine (Funds Protected)' : (lienCfg.label === 'RELEASED' ? 'Lien Cleared / Released' : 'Unencumbered (No Legal Lien)')}
                              </strong>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div style={{
        padding: '12px 20px',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(10, 15, 26, 0.85)',
        fontSize: '0.78rem',
        color: 'var(--text-muted)',
      }}>
        <div>
          Showing <strong>{filteredTransactions.length === 0 ? 0 : (currentPage - 1) * pageSize + 1}</strong> to{' '}
          <strong>{Math.min(currentPage * pageSize, filteredTransactions.length)}</strong> of{' '}
          <strong>{filteredTransactions.length}</strong> transactions
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-color)',
              color: currentPage === 1 ? 'var(--text-muted)' : 'var(--text-primary)',
              padding: '4px 8px',
              borderRadius: '6px',
              cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <ChevronLeft size={16} />
          </button>
          <span>Page {currentPage} of {totalPages}</span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-color)',
              color: currentPage === totalPages ? 'var(--text-muted)' : 'var(--text-primary)',
              padding: '4px 8px',
              borderRadius: '6px',
              cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
