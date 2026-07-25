import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  getDashboardData: async () => {
    // Simulating API call delay for placeholder data
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          kpis: {
            totalTransactions: 124500,
            highRisk: 142,
            mediumRisk: 305,
            lowRisk: 124053
          },
          volumeData: [
            { name: 'Mon', volume: 15000 },
            { name: 'Tue', volume: 18000 },
            { name: 'Wed', volume: 22000 },
            { name: 'Thu', volume: 19000 },
            { name: 'Fri', volume: 25000 },
            { name: 'Sat', volume: 14000 },
            { name: 'Sun', volume: 11500 },
          ],
          riskDistribution: [
            { name: 'High Risk', value: 142 },
            { name: 'Medium Risk', value: 305 },
            { name: 'Low Risk', value: 124053 },
          ],
          recentActivity: [
            { id: 'TXN-001', customer: 'Acme Corp', risk: 'High', status: 'Pending Review' },
            { id: 'TXN-002', customer: 'John Doe', risk: 'Low', status: 'Cleared' },
            { id: 'TXN-003', customer: 'Globex Inc', risk: 'Medium', status: 'In Progress' },
            { id: 'TXN-004', customer: 'Jane Smith', risk: 'Low', status: 'Cleared' },
            { id: 'TXN-005', customer: 'Initech', risk: 'High', status: 'Escalated' },
          ]
        });
      }, 1000);
    });
  },
  uploadTransactions: async (file) => {
    // Simulating API call delay for placeholder upload
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (!file) {
          reject(new Error("No file provided"));
        } else {
          resolve({
            status: "success",
            message: "Upload Successful",
            file_name: file.name
          });
        }
      }, 1500);
    });
  }
};

export default api;
