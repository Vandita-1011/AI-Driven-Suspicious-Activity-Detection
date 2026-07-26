import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // ----------------------------------------------------------------
  // Dashboard APIs
  // ----------------------------------------------------------------

  getDashboardData: async () => {
    const response = await api.get('/dashboard');
    return response.data;
  },

  getDashboardSummary: async () => {
    const response = await api.get('/dashboard/summary');
    return response.data;
  },

  getDashboardTrend: async () => {
    const response = await api.get('/dashboard/trend');
    return response.data;
  },

  getRiskDistribution: async () => {
    const response = await api.get('/dashboard/risk-distribution');
    return response.data;
  },

  // ----------------------------------------------------------------
  // Upload & Analysis APIs
  // ----------------------------------------------------------------

  uploadTransactions: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload-transactions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // ----------------------------------------------------------------
  // Investigation APIs
  // ----------------------------------------------------------------

  getInvestigationStatus: async (investigationId) => {
    const response = await api.get(`/investigation/${investigationId}/status`);
    return response.data;
  },

  getInvestigationResult: async (investigationId) => {
    const response = await api.get(`/investigation/${investigationId}/result`);
    return response.data;
  },

  getInvestigation: async (investigationId) => {
    const response = await api.get(`/investigation/${investigationId}`);
    return response.data;
  },

  // ----------------------------------------------------------------
  // Alerts APIs
  // ----------------------------------------------------------------

  getAlerts: async () => {
    const response = await api.get('/alerts');
    return response.data;
  },

  // ----------------------------------------------------------------
  // Reports APIs
  // ----------------------------------------------------------------

  getReports: async () => {
    const response = await api.get('/reports');
    return response.data;
  },

  generateReport: async (type) => {
    return { status: 'success', message: `Report generation for ${type} initiated.` };
  },
};

export default api;
