import React, { useState, useCallback } from 'react';
import { apiService } from '../services/api';
import { DashboardCard, StatusBadge, LoadingSpinner, ErrorState } from '../components/UIComponents';
import { ShieldAlert, Activity, CheckCircle, Database, RefreshCw, Clock, Briefcase, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const RISK_COLORS = ['#DC2626', '#F59E0B', '#16A34A'];

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboard = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const result = await apiService.getDashboardData();
      setData(result);
      setLastUpdated(result.last_updated || new Date().toISOString());
    } catch (err) {
      const message =
        err.code === 'ECONNABORTED'
          ? 'Request timed out. Please check your connection.'
          : err.response?.status === 503
            ? 'Server is currently unavailable. Please try again later.'
            : err.message === 'Network Error'
              ? 'Unable to connect to the server. Please check your network.'
              : 'Failed to load dashboard data. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Initial load
  React.useEffect(() => {
    fetchDashboard(false);
  }, [fetchDashboard]);

  if (loading) return <LoadingSpinner text="Loading dashboard metrics..." />;
  if (error) return <ErrorState title="Dashboard Error" description={error} onRetry={() => fetchDashboard(false)} />;

  // Empty state: data loaded but nothing meaningful
  if (!data || !data.summary) {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto bg-slate-50 min-h-screen">
        <div className="flex flex-col items-center justify-center h-96 text-slate-400">
          <Database size={48} className="mb-4" />
          <h2 className="text-lg font-semibold text-slate-600 mb-2">No Dashboard Data</h2>
          <p className="text-sm mb-6">Upload transactions and run analysis to populate the dashboard.</p>
          <button
            onClick={() => fetchDashboard(false)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }

  const { summary, risk_distribution, trend, recent_activity } = data;

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 bg-slate-50 min-h-screen">
      
      {/* Top Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">AML Detection Dashboard</h1>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Clock size={14} />
              Last updated: {new Date(lastUpdated).toLocaleTimeString()}
            </div>
          )}
          <button
            onClick={() => fetchDashboard(true)}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
          <div className="flex items-center gap-2 px-3 py-1 bg-green-50 border border-green-200 text-green-700 rounded-full text-sm font-medium">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            Operational
          </div>
        </div>
      </div>

      {/* KPI Cards - Row 1: Risk Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <DashboardCard 
          title="Total Transactions" 
          value={(summary.total_transactions ?? 0).toLocaleString()} 
          icon={Database} 
        />
        <DashboardCard 
          title="High Risk" 
          value={(summary.high_risk ?? 0).toLocaleString()} 
          icon={ShieldAlert} 
        />
        <DashboardCard 
          title="Medium Risk" 
          value={(summary.medium_risk ?? 0).toLocaleString()} 
          icon={Activity} 
        />
        <DashboardCard 
          title="Low Risk" 
          value={(summary.low_risk ?? 0).toLocaleString()} 
          icon={CheckCircle} 
        />
      </div>

      {/* KPI Cards - Row 2: Investigation Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <DashboardCard
          title="Active Investigations"
          value={(summary.active_investigations ?? 0).toLocaleString()}
          icon={Briefcase}
        />
        <DashboardCard
          title="Closed Investigations"
          value={(summary.closed_investigations ?? 0).toLocaleString()}
          icon={CheckCircle}
        />
        <DashboardCard
          title="Total Investigations"
          value={(summary.total_investigations ?? 0).toLocaleString()}
          icon={Database}
        />
        <DashboardCard
          title="Success Rate"
          value={`${summary.success_rate ?? 0}%`}
          icon={TrendingUp}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Bar Chart - Transaction Volume Trend */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 mb-6">Transaction Volume (Last 7 Days)</h3>
          <div className="h-72">
            {trend && trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trend} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} tickFormatter={(val) => `${val / 1000}k`} />
                  <Tooltip cursor={{ fill: '#F8FAFC' }} contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Bar dataKey="volume" fill="#2563EB" radius={[4, 4, 0, 0]} barSize={32} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-400 text-sm">No trend data available</div>
            )}
          </div>
        </div>

        {/* Pie Chart - Risk Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 mb-6">Risk Distribution</h3>
          <div className="h-72 flex flex-col items-center justify-center">
            {risk_distribution && risk_distribution.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height="80%">
                  <PieChart>
                    <Pie
                      data={risk_distribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {risk_distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={RISK_COLORS[index % RISK_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-wrap justify-center gap-4 mt-2">
                  {risk_distribution.map((entry, index) => (
                    <div key={entry.name} className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: RISK_COLORS[index % RISK_COLORS.length] }}></span>
                      {entry.name}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-400 text-sm">No distribution data available</div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200 bg-white">
          <h3 className="text-base font-semibold text-slate-900">Recent Activity</h3>
        </div>
        {recent_activity && recent_activity.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 font-semibold">Transaction ID</th>
                  <th className="px-6 py-3 font-semibold">Customer</th>
                  <th className="px-6 py-3 font-semibold">Risk Level</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {recent_activity.map((row, idx) => (
                  <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-900">{row.id}</td>
                    <td className="px-6 py-4 text-slate-600">{row.customer}</td>
                    <td className="px-6 py-4">
                      <StatusBadge status={row.risk} type="risk" />
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={row.status} type="status" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex items-center justify-center py-12 text-slate-400 text-sm">No recent activity</div>
        )}
      </div>
      
    </div>
  );
}
