const BASE = '/api/coordinator';
const NET_BASE = '/api/network';

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export const coordinatorApi = {
  getLive: (bank = 'ALL', limit = 60) =>
    fetchJSON(`${BASE}/live?bank=${bank}&limit=${limit}`),

  getDecisions: (params = {}) => {
    const q = new URLSearchParams();
    if (params.bank && params.bank !== 'ALL') q.set('bank', params.bank);
    if (params.decision) q.set('decision', params.decision);
    if (params.risk_level) q.set('risk_level', params.risk_level);
    if (params.transaction_id) q.set('transaction_id', params.transaction_id);
    if (params.coordination_id) q.set('coordination_id', params.coordination_id);
    q.set('limit', params.limit || 100);
    q.set('offset', params.offset || 0);
    return fetchJSON(`${BASE}/decisions?${q}`);
  },

  getDetail: (coordinationId) =>
    fetchJSON(`${BASE}/decisions/${coordinationId}`),

  getSummary: (bank = 'ALL') =>
    fetchJSON(`${BASE}/summary?bank=${bank}`),

  getConfig: () =>
    fetchJSON(`${BASE}/config`),

  health: () =>
    fetchJSON(`${BASE}/health`),

  // ── Network Monitoring, Provenance & Investigation APIs ────────────────────
  getMonitoredEntities: (limit = 60) =>
    fetchJSON(`${NET_BASE}/monitored?limit=${limit}`),

  getSubgraph: (accountId, depth = 2) =>
    fetchJSON(`${NET_BASE}/subgraph/${accountId}?depth=${depth}`),

  getChains: (accountId, depth = 3) =>
    fetchJSON(`${NET_BASE}/chains/${accountId}?depth=${depth}`),

  getProvenance: (accountId, maxHops = 3) =>
    fetchJSON(`${NET_BASE}/provenance/${accountId}?max_hops=${maxHops}`),

  getRiskPropagation: (accountId, directRisk = 0, behavRisk = 0) =>
    fetchJSON(`${NET_BASE}/propagation/${accountId}?direct_risk=${directRisk}&behav_risk=${behavRisk}`),

  getLiens: (params = {}) => {
    const q = new URLSearchParams();
    if (params.status && params.status !== 'ALL') q.set('status', params.status);
    if (params.bank && params.bank !== 'ALL') q.set('bank', params.bank);
    if (params.search) q.set('search', params.search);
    if (params.limit) q.set('limit', params.limit || 150);
    return fetchJSON(`${NET_BASE}/liens?${q}`);
  },

  getLienHistory: (params = {}) => {
    const q = new URLSearchParams();
    if (params.status && params.status !== 'ALL') q.set('status', params.status);
    if (params.bank && params.bank !== 'ALL') q.set('bank', params.bank);
    if (params.search) q.set('search', params.search);
    if (params.limit) q.set('limit', params.limit || 150);
    return fetchJSON(`${NET_BASE}/liens/history?${q}`);
  },

  releaseLien: (lienId, investigatorId, reason) =>
    fetchJSON(`${NET_BASE}/liens/${lienId}/release`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ investigator_id: investigatorId, reason }),
    }),

  getGNNRepresentation: () =>
    fetchJSON(`${NET_BASE}/gnn-representation`),

  // ── ADSL Central & Mule Network APIs ──────────────────────────────────────
  getMuleNetworks: () =>
    fetchJSON(`/api/adsl/mule-networks`),

  getMuleNetworkDetail: (networkId) =>
    fetchJSON(`/api/adsl/mule-networks/${networkId}`),

  getUnderReview: () =>
    fetchJSON(`/api/adsl/under-review`),

  executeReviewAction: (transactionId, action, investigatorId = 'COMPLIANCE_OFFICER_01', notes = '') =>
    fetchJSON(`/api/adsl/review/${transactionId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, investigator_id: investigatorId, notes }),
    }),

  executeAccountAction: (accountId, action, bank = 'SBI', investigatorId = 'COMPLIANCE_OFFICER_01', notes = '') =>
    fetchJSON(`/api/adsl/account/${accountId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, bank, investigator_id: investigatorId, notes }),
    }),

  getMonitoringCases: (status) =>
    fetchJSON(`/adsl/monitoring-cases${status ? `?status=${status}` : ''}`),

  getRlDecisions: (limit = 50) =>
    fetchJSON(`/adsl/rl-decisions?limit=${limit}`),

  getAdslTransactions: (limit = 60) =>
    fetchJSON(`/api/adsl/transactions?limit=${limit}`),

  getTransactionGraph: (transactionId) =>
    fetchJSON(`/api/adsl/transaction-graph/${transactionId}`),

  triggerMuleSinkFlow: () =>
    fetchJSON(`/api/adsl/simulate/mule-sink`, { method: 'POST' }),
};



