import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiService } from '../services/api';
import { StatusBadge, LoadingSpinner, ErrorState } from '../components/UIComponents';
import { 
  ArrowLeft, BrainCircuit, Activity, Network, Fingerprint, 
  CheckCircle2, PlayCircle, Lock, ShieldAlert, AlertCircle, Clock 
} from 'lucide-react';

export default function Investigation() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchInvestigation = async () => {
      try {
        const res = await apiService.getInvestigation(id);
        setData(res);
      } catch (err) {
        setError("Failed to load investigation details.");
      } finally {
        setLoading(false);
      }
    };
    fetchInvestigation();
  }, [id]);

  if (loading) return <LoadingSpinner text="Loading case details..." />;
  if (error) return <ErrorState title="Investigation Error" description={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6 bg-slate-50 min-h-screen">
      
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link 
          to="/alerts"
          className="mt-1 p-2 bg-white border border-slate-200 rounded-md text-slate-500 hover:bg-slate-50 transition-colors shadow-sm"
        >
          <ArrowLeft size={18} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">Investigation Details</h1>
              <p className="text-sm text-slate-500 mt-1">Review the complete analysis for the selected suspicious transaction.</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="px-4 py-2 bg-white border border-slate-300 text-slate-700 text-sm font-medium rounded-md hover:bg-slate-50 transition-colors shadow-sm">
                Mark Investigating
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors shadow-sm">
                Mark Resolved
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Transaction Summary Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-6">
        <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Alert ID</p>
            <p className="text-sm font-medium text-slate-900">{data.summary.alertId}</p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Transaction ID</p>
            <p className="text-sm font-medium text-slate-900">{data.summary.transactionId}</p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Customer Name</p>
            <p className="text-sm font-medium text-slate-900">{data.summary.customerName}</p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Amount</p>
            <p className="text-sm font-medium text-slate-900">${data.summary.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Timestamp</p>
            <p className="text-sm font-medium text-slate-900">{new Date(data.summary.timestamp).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Risk Score</p>
            <p className={`text-sm font-bold ${data.summary.riskScore >= 80 ? 'text-red-600' : 'text-amber-600'}`}>
              {data.summary.riskScore}/100
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Risk Level</p>
            <StatusBadge status={data.summary.riskLevel} type="risk" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Status</p>
            <StatusBadge status={data.summary.status} type="status" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Explainability & Recommendations */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* AI Explainability Section */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-2">
              <BrainCircuit className="text-blue-600" size={20} />
              <h2 className="text-base font-semibold text-slate-900">AI Explainability Analysis</h2>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Risk Summary */}
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
                  <ShieldAlert className="text-red-500" size={16} /> Risk Summary
                </h3>
                <div className="p-4 bg-red-50 text-red-900 border border-red-100 rounded-lg text-sm">
                  {data.explainability.riskSummary}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Rules */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
                    <CheckCircle2 className="text-blue-500" size={16} /> Triggered Rules
                  </h3>
                  <ul className="space-y-2">
                    {data.explainability.triggeredRules.map((rule, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 bg-slate-50 p-2.5 rounded-md border border-slate-100">
                        <AlertCircle size={16} className="text-slate-400 mt-0.5 shrink-0" />
                        {rule}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Behaviour */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
                    <Activity className="text-purple-500" size={16} /> Behaviour Findings
                  </h3>
                  <ul className="space-y-2">
                    {data.explainability.behaviourFindings.map((finding, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 bg-slate-50 p-2.5 rounded-md border border-slate-100">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-1.5 shrink-0"></span>
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Patterns */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
                    <Network className="text-orange-500" size={16} /> Pattern Findings
                  </h3>
                  <ul className="space-y-2">
                    {data.explainability.patternFindings.map((finding, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 bg-slate-50 p-2.5 rounded-md border border-slate-100">
                        <span className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-1.5 shrink-0"></span>
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* ML Findings */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-3">
                    <Fingerprint className="text-teal-500" size={16} /> ML Findings
                  </h3>
                  <ul className="space-y-2">
                    {data.explainability.mlFindings.map((finding, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 bg-slate-50 p-2.5 rounded-md border border-slate-100">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-1.5 shrink-0"></span>
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
          
        </div>

        {/* Right Column: Recommendations & Timeline */}
        <div className="space-y-6">
          
          {/* Recommendations */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-2">
              <PlayCircle className="text-blue-600" size={18} />
              <h2 className="text-base font-semibold text-slate-900">Recommended Actions</h2>
            </div>
            <div className="p-6">
              <ul className="space-y-3">
                {data.recommendations.map((rec, idx) => {
                  let Icon = CheckCircle2;
                  let color = 'text-slate-600';
                  
                  if (rec.toLowerCase().includes('escalate')) {
                    Icon = ShieldAlert;
                    color = 'text-red-600 bg-red-50 border-red-100';
                  } else if (rec.toLowerCase().includes('freeze')) {
                    Icon = Lock;
                    color = 'text-orange-600 bg-orange-50 border-orange-100';
                  } else {
                    color = 'text-blue-700 bg-blue-50 border-blue-100';
                  }

                  return (
                    <li key={idx} className={`flex items-start gap-3 text-sm p-3 rounded-lg border ${color}`}>
                      <Icon size={18} className="shrink-0 mt-0.5" />
                      <span className="font-medium">{rec}</span>
                    </li>
                  )
                })}
              </ul>
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-2">
              <Clock className="text-blue-600" size={18} />
              <h2 className="text-base font-semibold text-slate-900">Investigation Timeline</h2>
            </div>
            <div className="p-6">
              <div className="relative border-l-2 border-slate-200 ml-3 space-y-6">
                {data.timeline.map((event, idx) => (
                  <div key={idx} className="relative pl-6">
                    <span className="absolute -left-[9px] top-1 w-4 h-4 rounded-full border-2 border-white bg-blue-500 shadow-sm"></span>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-slate-900">{event.event}</span>
                      <span className="text-xs text-slate-500">{new Date(event.time).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
