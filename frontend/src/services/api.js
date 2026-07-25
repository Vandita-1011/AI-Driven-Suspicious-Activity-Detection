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
  },
  getAlerts: async () => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          alerts: [
            { id: 'ALT-1001', customer: 'Global Trade Ltd', riskScore: 92, riskLevel: 'High', status: 'Open', createdAt: '2023-10-25T08:30:00Z' },
            { id: 'ALT-1002', customer: 'Acme Corp', riskScore: 85, riskLevel: 'High', status: 'Investigating', createdAt: '2023-10-24T14:15:00Z' },
            { id: 'ALT-1003', customer: 'John Doe', riskScore: 65, riskLevel: 'Medium', status: 'Open', createdAt: '2023-10-24T09:45:00Z' },
            { id: 'ALT-1004', customer: 'Jane Smith', riskScore: 42, riskLevel: 'Low', status: 'Resolved', createdAt: '2023-10-23T11:20:00Z' },
            { id: 'ALT-1005', customer: 'Initech', riskScore: 78, riskLevel: 'Medium', status: 'Investigating', createdAt: '2023-10-22T16:50:00Z' },
            { id: 'ALT-1006', customer: 'Globex Inc', riskScore: 95, riskLevel: 'High', status: 'Open', createdAt: '2023-10-22T10:10:00Z' },
            { id: 'ALT-1007', customer: 'Alice Johnson', riskScore: 35, riskLevel: 'Low', status: 'Resolved', createdAt: '2023-10-21T13:40:00Z' },
            { id: 'ALT-1008', customer: 'Bob Williams', riskScore: 88, riskLevel: 'High', status: 'Open', createdAt: '2023-10-21T09:05:00Z' },
            { id: 'ALT-1009', customer: 'Stark Industries', riskScore: 70, riskLevel: 'Medium', status: 'Resolved', createdAt: '2023-10-20T15:25:00Z' },
            { id: 'ALT-1010', customer: 'Wayne Enterprises', riskScore: 60, riskLevel: 'Medium', status: 'Open', createdAt: '2023-10-19T11:55:00Z' }
          ]
        });
      }, 1200);
    });
  }
};

export default api;
