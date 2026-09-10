const BASE = '/api/risk';
const XGB_BASE = '/api/xgboost';

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export const riskApi = {
  getLive: (bank = 'ALL', limit = 60) =>
    fetchJSON(`${BASE}/live?bank=${bank}&limit=${limit}`),

  getAssessments: (params = {}) => {
    const q = new URLSearchParams();
    if (params.bank && params.bank !== 'ALL') q.set('bank', params.bank);
    if (params.risk_level) q.set('risk_level', params.risk_level);
    if (params.account_id) q.set('account_id', params.account_id);
    if (params.transaction_id) q.set('transaction_id', params.transaction_id);
    if (params.min_score != null) q.set('min_score', params.min_score);
    q.set('limit', params.limit || 100);
    q.set('offset', params.offset || 0);
    return fetchJSON(`${BASE}/assessments?${q}`);
  },

  getDetail: (assessmentId) =>
    fetchJSON(`${BASE}/assessments/${assessmentId}`),

  getSummary: (bank = 'ALL') =>
    fetchJSON(`${BASE}/summary?bank=${bank}`),

  getAccountHistory: (accountId, bank = 'ALL', limit = 30) =>
    fetchJSON(`${BASE}/account/${accountId}?bank=${bank}&limit=${limit}`),

  health: () =>
    fetchJSON(`${BASE}/health`),

  // ── XGBoost Risk Prediction API (Module 4) ──────────────────────────────────
  getXGBoostModelInfo: () =>
    fetchJSON(`${XGB_BASE}/model-info`),

  getXGBoostPredictions: (params = {}) => {
    const q = new URLSearchParams();
    if (params.bank && params.bank !== 'ALL') q.set('bank', params.bank);
    if (params.risk_level) q.set('risk_level', params.risk_level);
    if (params.flagged_only) q.set('flagged_only', 'true');
    q.set('limit', params.limit || 60);
    q.set('offset', params.offset || 0);
    return fetchJSON(`${XGB_BASE}/predictions?${q}`);
  },

  getXGBoostSummary: (bank = 'ALL') =>
    fetchJSON(`${XGB_BASE}/summary?bank=${bank}`),

  trainXGBoostModel: (sampleLimit = 24000) =>
    fetchJSON(`${XGB_BASE}/train?sample_limit=${sampleLimit}`, { method: 'POST' }),

  getAutonomousStatus: () =>
    fetchJSON(`${XGB_BASE}/autonomous-status`),

  triggerAutonomousAdapt: (sampleLimit = 24000) =>
    fetchJSON(`${XGB_BASE}/autonomous-adapt?sample_limit=${sampleLimit}`, { method: 'POST' }),
};
