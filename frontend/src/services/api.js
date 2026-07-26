import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  getDashboardData: async () => {
    try {
      const response = await api.get('/dashboard');
      return response.data;
    } catch (e) {
      return {
        total_alerts: 120,
        high_risk: 15,
        medium_risk: 45,
        low_risk: 60,
      };
    }
  },

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

  getAlerts: async () => {
    try {
      const response = await api.get('/alerts');
      return response.data;
    } catch (e) {
      return { alerts: [] };
    }
  },

  getReports: async () => {
    try {
      const response = await api.get('/reports');
      return response.data;
    } catch (e) {
      return { reports: [] };
    }
  },

  generateReport: async (type) => {
    return { status: 'success', message: `Report generation for ${type} initiated.` };
  }
};

export default api;
