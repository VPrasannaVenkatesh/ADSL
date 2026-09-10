export function getDecisionColor(decision) {
  const map = {
    ALLOW: '#10B981',
    MONITOR: '#F59E0B',
    REVIEW: '#F97316',
    CONTROLLED_ACTION: '#EF4444',
  };
  return map[decision] || '#6B7280';
}

export function getRiskColor(level) {
  const map = {
    LOW: '#10B981',
    MEDIUM: '#F59E0B',
    HIGH: '#F97316',
    CRITICAL: '#EF4444',
  };
  return map[level] || '#6B7280';
}

export function scoreColor(score) {
  if (score <= 30) return '#10B981';
  if (score <= 60) return '#F59E0B';
  if (score <= 80) return '#F97316';
  return '#EF4444';
}

export function formatINR(amount) {
  if (!amount && amount !== 0) return '–';
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toFixed(2)} Cr`;
  if (amount >= 100_000)    return `₹${(amount / 100_000).toFixed(2)} L`;
  return `₹${Number(amount).toLocaleString('en-IN')}`;
}

export function formatTS(iso) {
  if (!iso) return '–';
  const d = new Date(iso);
  return d.toLocaleString('en-IN', { hour12: false, dateStyle: 'short', timeStyle: 'medium' });
}

export function truncate(str, n = 20) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n) + '…' : str;
}

export const BANKS = ['ALL', 'SBI', 'AXIS', 'IOB'];
export const DECISIONS = ['', 'ALLOW', 'MONITOR', 'REVIEW', 'CONTROLLED_ACTION'];
export const LEVELS = ['', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export const BANK_THEME = {
  SBI: { color: '#3B82F6', bg: 'rgba(59, 130, 246, 0.15)', border: 'rgba(59, 130, 246, 0.35)' },
  AXIS: { color: '#EC4899', bg: 'rgba(236, 72, 153, 0.15)', border: 'rgba(236, 72, 153, 0.35)' },
  IOB: { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.35)' },
};
