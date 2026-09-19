import React, { useState, useEffect } from 'react';
import {
  X,
  User,
  Building2,
  Briefcase,
  Activity,
  ArrowDownLeft,
  ArrowUpRight,
  RefreshCw,
  CreditCard,
  Calendar,
  CheckCircle,
  AlertOctagon,
  Clock,
  Smartphone,
  MapPin,
  TrendingUp,
  Download,
} from 'lucide-react';
import { simulatorApi } from '../api/simulatorApi';

export function AccountDrawer({ bank, accountId, onClose }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!bank || !accountId) return;
    let isMounted = true;
    const fetchProfile = async () => {
      setLoading(true);
      try {
        const data = await simulatorApi.getAccountProfile(bank, accountId);
        if (isMounted) setProfile(data);
      } catch (err) {
        console.error('Failed to load account profile', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchProfile();
    return () => { isMounted = false; };
  }, [bank, accountId]);

  if (!accountId) return null;

  const acc = profile?.account || {};
  const summary = profile?.transaction_summary || {};
  const txns = profile?.recent_transactions || [];

  const formatCurrency = (amt) => `₹${Number(amt || 0).toLocaleString('en-IN')}`;

  const handleDownloadDossier = async () => {
    try {
      const res = await fetch(`/api/accounts/${bank || 'SBI'}/${accountId}/report`);
      if (res.ok) {
        const data = await res.json();
        const text = data.report_text || JSON.stringify(data, null, 2);
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${bank || 'BANK'}_Account_Dossier_${accountId}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error('Failed to download dossier:', e);
    }
  };

  const isBusiness = (acc.account_category || '').toUpperCase() === 'BUSINESS' ||
                     (acc.account_type || '').toUpperCase() === 'CURRENT' ||
                     Boolean(acc.business_category);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      bottom: 0,
      width: '100%',
      maxWidth: '520px',
      background: 'rgba(10, 14, 23, 0.96)',
      backdropFilter: 'blur(25px)',
      WebkitBackdropFilter: 'blur(25px)',
      borderLeft: '1px solid var(--border-color)',
      boxShadow: '-12px 0 50px rgba(0,0,0,0.7)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      animation: 'fadeIn 0.2s ease-out',
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(16, 22, 34, 0.8)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: isBusiness ? 'rgba(192, 132, 252, 0.15)' : 'rgba(0, 229, 255, 0.15)',
            border: `1px solid ${isBusiness ? 'rgba(192, 132, 252, 0.4)' : 'rgba(0, 229, 255, 0.4)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            {isBusiness ? <Briefcase size={20} color="#C084FC" /> : <User size={20} color="var(--accent-cyan)" />}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="mono" style={{ fontSize: '1.1rem', fontWeight: '800', color: '#FFFFFF' }}>
                {accountId}
              </span>
              <span style={{
                fontSize: '0.68rem',
                fontWeight: '700',
                padding: '2px 7px',
                borderRadius: '4px',
                background: bank === 'SBI' ? 'rgba(59,130,246,0.2)' : bank === 'AXIS' ? 'rgba(236,72,153,0.2)' : 'rgba(245,158,11,0.2)',
                color: bank === 'SBI' ? '#60A5FA' : bank === 'AXIS' ? '#F472B6' : '#FBBF24',
                border: `1px solid ${bank === 'SBI' ? '#3B82F6' : bank === 'AXIS' ? '#EC4899' : '#F59E0B'}`,
              }}>
                {bank || acc.bank_code || 'BANK'}
              </span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              {acc.customer_name || 'Account Holder'}
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '6px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.15s ease',
          }}
          title="Close Drawer"
        >
          <X size={18} />
        </button>
      </div>

      {/* Drawer Body */}
      <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {loading ? (
          <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <RefreshCw size={26} className="pulse-dot" style={{ margin: '0 auto 12px auto' }} />
            <div>Loading account information from bank database...</div>
          </div>
        ) : (
          <>
            {/* 1. BASIC INFORMATION */}
            <div className="glass-panel" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--accent-cyan)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                Basic Information
              </div>

              {/* Current Balance Display */}
              <div style={{
                background: 'rgba(7, 9, 14, 0.7)',
                padding: '14px 16px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Current Balance</div>
                  <div className="mono" style={{ fontSize: '1.45rem', fontWeight: '800', color: '#10B981', marginTop: '2px' }}>
                    {formatCurrency(acc.current_balance)}
                  </div>
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '4px 10px',
                  borderRadius: '20px',
                  background: acc.is_active !== false ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  border: `1px solid ${acc.is_active !== false ? '#10B981' : '#EF4444'}`,
                  fontSize: '0.72rem',
                  fontWeight: '700',
                  color: acc.is_active !== false ? '#34D399' : '#F87171',
                }}>
                  <span style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: acc.is_active !== false ? '#10B981' : '#EF4444',
                  }} />
                  {acc.is_active !== false ? 'ACCOUNT ACTIVE' : 'RESTRICTED / FROZEN'}
                </div>
              </div>

              {/* Download Official Dossier Button */}
              <button
                onClick={handleDownloadDossier}
                style={{
                  padding: '9px 14px',
                  borderRadius: '6px',
                  border: '1px solid rgba(0, 229, 255, 0.35)',
                  background: 'rgba(0, 229, 255, 0.12)',
                  color: 'var(--accent-cyan, #00E5FF)',
                  fontSize: '0.78rem',
                  fontWeight: '800',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'all 0.15s ease',
                }}
              >
                <Download size={14} />
                <span>Download Official Account Dossier (.txt)</span>
              </button>

              {/* Grid of basic fields */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8rem' }}>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ACCOUNT ID</div>
                  <div className="mono" style={{ fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                    {acc.account_id || accountId}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ACCOUNT HOLDER</div>
                  <div style={{ fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                    {acc.customer_name || 'N/A'}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>BANK INSTITUTION</div>
                  <div style={{ fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                    {bank || acc.bank_code} (PostgreSQL Connected)
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ACCOUNT CATEGORY</div>
                  <div style={{ marginTop: '2px' }}>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: '800',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: isBusiness ? 'rgba(192, 132, 252, 0.18)' : 'rgba(59, 130, 246, 0.18)',
                      color: isBusiness ? '#C084FC' : '#60A5FA',
                      border: `1px solid ${isBusiness ? 'rgba(192, 132, 252, 0.4)' : 'rgba(59, 130, 246, 0.4)'}`,
                    }}>
                      {isBusiness ? 'BUSINESS ACCOUNT' : 'PERSONAL ACCOUNT'}
                    </span>
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ACCOUNT TYPE</div>
                  <div style={{ fontWeight: '600', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {acc.account_type || (isBusiness ? 'CURRENT' : 'SAVINGS')}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>REGISTERED LOCATION</div>
                  <div style={{ fontWeight: '600', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {acc.home_location || 'India'}
                  </div>
                </div>
              </div>
            </div>

            {/* 2. BUSINESS ACCOUNT INFORMATION (Shown for Business Accounts) */}
            {isBusiness && (
              <div className="glass-panel" style={{
                padding: '18px',
                borderLeft: '4px solid #C084FC',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                background: 'rgba(192, 132, 252, 0.04)',
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: '800', color: '#C084FC', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Briefcase size={14} />
                  <span>Business Commercial Profile</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '10px', fontSize: '0.8rem' }}>
                  <div style={{ background: 'rgba(7, 9, 14, 0.5)', padding: '10px 12px', borderRadius: '6px' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>BUSINESS CATEGORY</div>
                    <div style={{ fontWeight: '700', color: '#FFFFFF', marginTop: '2px' }}>
                      {acc.business_category || 'Commercial Entity / Merchant'}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(7, 9, 14, 0.5)', padding: '10px 12px', borderRadius: '6px' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>EXPECTED TRANSACTION RANGE</div>
                    <div className="mono" style={{ fontWeight: '700', color: '#10B981', marginTop: '2px' }}>
                      {acc.expected_tx_range || '₹50,000 - ₹50,00,000'}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(7, 9, 14, 0.5)', padding: '10px 12px', borderRadius: '6px' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>TRANSACTION FREQUENCY PATTERN</div>
                    <div style={{ fontWeight: '600', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {acc.tx_frequency_pattern || 'High frequency (Multiple daily commercial settlements)'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 3. TRANSACTION INFORMATION SUMMARY */}
            <div className="glass-panel" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--accent-cyan)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                Transaction Summary
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                {/* Total Sent */}
                <div style={{ background: 'rgba(7, 9, 14, 0.6)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>TOTAL SENT</div>
                  <div className="mono" style={{ fontSize: '0.95rem', fontWeight: '800', color: '#F43F5E', marginTop: '4px' }}>
                    {formatCurrency(summary.total_sent)}
                  </div>
                </div>

                {/* Total Received */}
                <div style={{ background: 'rgba(7, 9, 14, 0.6)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>TOTAL RECEIVED</div>
                  <div className="mono" style={{ fontSize: '0.95rem', fontWeight: '800', color: '#10B981', marginTop: '4px' }}>
                    {formatCurrency(summary.total_received)}
                  </div>
                </div>

                {/* Transaction Count */}
                <div style={{ background: 'rgba(7, 9, 14, 0.6)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>TXN COUNT</div>
                  <div className="mono" style={{ fontSize: '0.95rem', fontWeight: '800', color: '#60A5FA', marginTop: '4px' }}>
                    {summary.transaction_count || 0}
                  </div>
                </div>
              </div>
            </div>

            {/* 4. RECENT TRANSACTIONS */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--text-muted)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                  Recent Transactions ({txns.length})
                </span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Latest activity</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {txns.length === 0 ? (
                  <div style={{
                    padding: '24px',
                    textAlign: 'center',
                    color: 'var(--text-muted)',
                    background: 'rgba(7, 9, 14, 0.4)',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                  }}>
                    No recent transactions recorded for this account.
                  </div>
                ) : (
                  txns.map((t) => {
                    const isOutgoing = t.is_outgoing || t.sender_account_id === accountId;
                    return (
                      <div
                        key={t.transaction_id}
                        style={{
                          background: 'rgba(7, 9, 14, 0.6)',
                          padding: '12px 14px',
                          borderRadius: '8px',
                          border: '1px solid var(--border-color)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '0.8rem',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div style={{
                            width: '28px',
                            height: '28px',
                            borderRadius: '50%',
                            background: isOutgoing ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}>
                            {isOutgoing ? <ArrowUpRight size={15} color="#F43F5E" /> : <ArrowDownLeft size={15} color="#10B981" />}
                          </div>
                          <div>
                            <div className="mono" style={{ fontWeight: '700', color: 'var(--text-primary)' }}>
                              {isOutgoing ? `To: ${t.receiver_account_id}` : `From: ${t.sender_account_id}`}
                            </div>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                              {t.transaction_type} • {t.device || 'Mobile'} • {t.location || 'India'}
                            </div>
                          </div>
                        </div>

                        <div style={{ textAlign: 'right' }}>
                          <div className="mono" style={{ fontWeight: '800', color: isOutgoing ? '#F43F5E' : '#10B981' }}>
                            {isOutgoing ? '-' : '+'}{formatCurrency(t.amount)}
                          </div>
                          <div style={{
                            fontSize: '0.65rem',
                            fontWeight: '700',
                            marginTop: '2px',
                            color: t.transaction_status === 'COMPLETED' ? '#10B981' :
                                   t.transaction_status === 'MONITORING' ? '#F59E0B' :
                                   t.transaction_status === 'HONEYPOT' ? '#C084FC' :
                                   t.transaction_status === 'LIEN_APPLIED' ? '#3B82F6' : '#94A3B8',
                          }}>
                            {t.transaction_status || 'COMPLETED'}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
