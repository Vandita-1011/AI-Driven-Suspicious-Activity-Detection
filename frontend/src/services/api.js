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
  },
  getInvestigation: async (alertId) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          summary: {
            alertId: alertId,
            transactionId: 'TXN-9876543210',
            customerName: 'Global Trade Ltd',
            amount: 450000.00,
            timestamp: '2023-10-25T08:30:00Z',
            riskScore: 92,
            riskLevel: 'High',
            status: 'Open'
          },
          explainability: {
            riskSummary: 'High probability of layering detected. Multiple rapid transfers across jurisdictions immediately following a large deposit.',
            triggeredRules: [
              'Rule 101: Deposit exceeds $10,000 threshold',
              'Rule 405: Structuring pattern detected over 3 days'
            ],
            behaviourFindings: [
              'Deviation from historical baseline by 450%',
              'Unusual login location (IP Address anomaly)'
            ],
            patternFindings: [
              'Smurfing pattern matches confirmed AML typology 4',
              'High velocity of funds transfer'
            ],
            mlFindings: [
              'Autoencoder anomaly score: 0.94',
              'Isolation Forest outlier detected'
            ]
          },
          recommendations: [
            'Escalate for manual review',
            'Request additional KYC documentation',
            'Freeze transaction pending review'
          ],
          timeline: [
            { time: '2023-10-25T08:30:00Z', event: 'Alert Generated by AML Engine' },
            { time: '2023-10-25T08:45:00Z', event: 'Analyst Assigned (Harsh)' },
            { time: '2023-10-25T09:00:00Z', event: 'Investigation Started' },
            { time: '2023-10-25T09:30:00Z', event: 'Review Pending' }
          ]
        });
      }, 1200);
    });
  },
  getReports: async () => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          summary: {
            totalReports: 145,
            generatedToday: 12,
            pendingReports: 3,
            archivedReports: 130
          },
          reports: [
            { id: 'REP-1001', alertId: 'ALT-1001', customer: 'Global Trade Ltd', type: 'Investigation Summary', status: 'Completed', generatedOn: '2023-10-25T10:30:00Z' },
            { id: 'REP-1002', alertId: 'ALT-1002', customer: 'Acme Corp', type: 'PDF', status: 'Completed', generatedOn: '2023-10-24T16:15:00Z' },
            { id: 'REP-1003', alertId: 'ALT-1003', customer: 'John Doe', type: 'CSV', status: 'Pending', generatedOn: '2023-10-24T09:45:00Z' },
            { id: 'REP-1004', alertId: 'ALT-1004', customer: 'Jane Smith', type: 'Executive Summary', status: 'Completed', generatedOn: '2023-10-23T11:20:00Z' },
            { id: 'REP-1005', alertId: 'ALT-1005', customer: 'Initech', type: 'Full Case Report', status: 'Pending', generatedOn: '2023-10-22T16:50:00Z' },
            { id: 'REP-1006', alertId: 'ALT-1006', customer: 'Globex Inc', type: 'Investigation Summary', status: 'Completed', generatedOn: '2023-10-22T10:10:00Z' },
            { id: 'REP-1007', alertId: 'ALT-1007', customer: 'Alice Johnson', type: 'PDF', status: 'Completed', generatedOn: '2023-10-21T13:40:00Z' },
            { id: 'REP-1008', alertId: 'ALT-1008', customer: 'Bob Williams', type: 'Investigation Summary', status: 'Archived', generatedOn: '2023-10-21T09:05:00Z' },
            { id: 'REP-1009', alertId: 'ALT-1009', customer: 'Stark Industries', type: 'CSV', status: 'Archived', generatedOn: '2023-10-20T15:25:00Z' },
            { id: 'REP-1010', alertId: 'ALT-1010', customer: 'Wayne Enterprises', type: 'Full Case Report', status: 'Pending', generatedOn: '2023-10-19T11:55:00Z' }
          ]
        });
      }, 1000);
    });
  },
  generateReport: async (type) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'success',
          message: `Successfully requested ${type} report generation.`
        });
      }, 1500);
    });
  }
};

export default api;
