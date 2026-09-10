export function getRiskColor(level) {
  const map = { LOW: '#10B981', MEDIUM: '#F59E0B', HIGH: '#F97316', CRITICAL: '#EF4444' };
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

export function truncate(str, n = 18) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n) + '…' : str;
}

export const BANKS = ['ALL', 'SBI', 'AXIS', 'IOB'];
export const LEVELS = ['', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export const COMPONENT_LABELS = {
  amount_risk:              'Amount Risk',
  velocity_risk:            'Velocity Risk',
  behaviour_deviation_risk: 'Behaviour Deviation',
  device_risk:              'Device Risk',
  location_risk:            'Location Risk',
  counterparty_risk:        'Counterparty Risk',
  timing_risk:              'Timing Risk',
  network_pattern_risk:     'Network Pattern Risk',
};
