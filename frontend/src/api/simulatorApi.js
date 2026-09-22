import api from './client';

export const simulatorApi = {
  // Simulator Control
  getStatus: async () => {
    const res = await api.get('/status');
    return res.data;
  },

  startSimulation: async (payload = { mode: 'normal', mix_mode: 'balanced' }) => {
    const res = await api.post('/simulator/start', payload);
    return res.data;
  },

  pauseSimulation: async () => {
    const res = await api.post('/simulator/pause');
    return res.data;
  },

  resumeSimulation: async () => {
    const res = await api.post('/simulator/resume');
    return res.data;
  },

  stopSimulation: async () => {
    const res = await api.post('/simulator/stop');
    return res.data;
  },

  setSpeed: async (speed) => {
    const res = await api.post('/simulator/speed', { speed });
    return res.data;
  },

  setMixMode: async (mix_mode) => {
    const res = await api.post('/simulator/mix', { mix_mode });
    return res.data;
  },

  // Single Active Bank Ledger
  getActiveBank: async () => {
    const res = await api.get('/simulator/active-bank');
    return res.data;
  },

  setActiveBank: async (bank) => {
    const res = await api.post('/simulator/active-bank', { bank });
    return res.data;
  },

  // Transactions
  getLiveTransactions: async ({ limit = 60, bank = null } = {}) => {
    const params = { limit };
    if (bank && bank !== 'ALL') params.bank = bank;
    const res = await api.get('/transactions/live', { params });
    return res.data;
  },

  queryTransactions: async (params = {}) => {
    const res = await api.get('/transactions', { params });
    return res.data;
  },

  // Bank & Account Analytics
  getBankStats: async () => {
    const res = await api.get('/banks/stats');
    return res.data;
  },

  getAccounts: async (params = {}) => {
    const res = await api.get('/accounts', { params });
    return res.data;
  },

  getAccountProfile: async (bank, accountId) => {
    const res = await api.get(`/accounts/${bank}/${accountId}`);
    return res.data;
  },

  getNetworkGraph: async (params = {}) => {
    const res = await api.get('/network/graph', { params });
    return res.data;
  },
};
