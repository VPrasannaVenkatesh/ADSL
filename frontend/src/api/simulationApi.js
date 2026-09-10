import api from './client';

export const simulationApi = {
  // Auth
  login: async (username, password) => {
    const res = await api.post('/auth/login', { username, password });
    return res.data;
  },

  // Simulation Lifecycle
  createSimulation: async (configPayload) => {
    const res = await api.post('/simulation/create', configPayload);
    return res.data;
  },
  startSimulation: async () => {
    const res = await api.post('/simulation/start');
    return res.data;
  },
  pauseSimulation: async () => {
    const res = await api.post('/simulation/pause');
    return res.data;
  },
  resumeSimulation: async () => {
    const res = await api.post('/simulation/resume');
    return res.data;
  },
  resetSimulation: async () => {
    const res = await api.post('/simulation/reset');
    return res.data;
  },
  setSpeed: async (speed) => {
    const res = await api.post(`/simulation/speed?speed=${speed}`);
    return res.data;
  },
  getStatus: async () => {
    const res = await api.get('/simulation/status');
    return res.data;
  },
  getConfig: async () => {
    const res = await api.get('/simulation/config');
    return res.data;
  },

  // Banks & Accounts
  getBanks: async () => {
    const res = await api.get('/banks');
    return res.data;
  },
  getAccounts: async (params = {}) => {
    const res = await api.get('/accounts', { params });
    return res.data;
  },
  getAccountById: async (accountId) => {
    const res = await api.get(`/accounts/${accountId}`);
    return res.data;
  },

  // Scenarios
  getScenarios: async () => {
    const res = await api.get('/scenarios');
    return res.data;
  },
  generateScenario: async (scenarioCode, customParameters = {}) => {
    const res = await api.post('/scenarios/generate', {
      scenario_code: scenarioCode,
      custom_parameters: customParameters,
    });
    return res.data;
  },
};
