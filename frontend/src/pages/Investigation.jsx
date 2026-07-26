import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiService } from '../services/api';
import { StatusBadge, LoadingSpinner, ErrorState } from '../components/UIComponents';
import { 
  ArrowLeft, BrainCircuit, Activity, Network, Fingerprint, 
  CheckCircle2, PlayCircle, Lock, ShieldAlert, AlertCircle, Clock,
  RefreshCw, Loader2, Info
} from 'lucide-react';

export default function Investigation() {
  const { id } = useParams();
  
  // State variables for polling & result loading
  const [statusInfo, setStatusInfo] = useState(null); // { request_id, investigation_id, status, progress, message }
  const [resultData, setResultData] = useState(null);
  const [pollingStatus, setPollingStatus] = useState('initializing'); // 'initializing' | 'polling' | 'fetching_result' | 'done' | 'error'
  const [errorMessage, setErrorMessage] = useState(null);
  const [errorTitle, setErrorTitle] = useState("Investigation Error");
  
  const pollIntervalRef = useRef(null);

  const fetchStatusAndResult = async () => {
    try {
      // 1. Fetch current investigation status
      const statusRes = await apiService.getInvestigationStatus(id);
      setStatusInfo(statusRes);
      setPollingStatus('polling');

      const currentStatus = statusRes.status?.toUpperCase() || 'UNKNOWN';

      // 2. Check for terminal statuses
      if (['COMPLETED', 'SUCCESS', 'FINISHED'].includes(currentStatus)) {
        // Stop polling interval
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        
        // Fetch full results
        setPollingStatus('fetching_result');
        const resData = await apiService.getInvestigationResult(id);
        setResultData(resData);
        setPollingStatus('done');
      } else if (['FAILED', 'ERROR'].includes(currentStatus)) {
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        setErrorTitle("Investigation Execution Failed");
        setErrorMessage(statusRes.message || "The AI engine encountered an error executing this investigation.");
        setPollingStatus('error');
      } else if (['CANCELLED', 'ABORTED'].includes(currentStatus)) {
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        setErrorTitle("Investigation Cancelled");
        setErrorMessage("This investigation was cancelled before completion.");
        setPollingStatus('error');
      }
    } catch (err) {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

      const status = err.response?.status;
      const detail = err.response?.data?.detail || err.message;

      if (status === 404) {
        setErrorTitle("Investigation Not Found");
        setErrorMessage("No investigation matching this ID was found.");
      } else if (status === 503) {
        setErrorTitle("AI Engine Unavailable");
        setErrorMessage("The AI Integration Service is currently unavailable. Please try again later.");
      } else if (status === 504) {
        setErrorTitle("Investigation Timeout");
        setErrorMessage("The request to the AI Engine timed out.");
      } else {
        setErrorTitle("Server Error");
        setErrorMessage(detail || "An unexpected error occurred while fetching investigation status.");
      }
      setPollingStatus('error');
    }
  };

  useEffect(() => {
    if (!id) return;

    // Initial fetch immediately
    fetchStatusAndResult();

    // Start 3-second polling interval
    pollIntervalRef.current = setInterval(() => {
      fetchStatusAndResult();
    }, 3000);

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [id]);

  // Loading States
  if (pollingStatus === 'initializing') {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto min-h-screen bg-slate-50 flex items-center justify-center">
        <LoadingSpinner text="Connecting to AI Service..." />
      </div>
    );
  }

  if (pollingStatus === 'error') {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto min-h-screen bg-slate-50">
        <div className="flex items-center gap-4 mb-6">
          <Link to="/alerts" className="p-2 bg-white border border-slate-200 rounded-md text-slate-500 hover:bg-slate-50">
            <ArrowLeft size={18} />
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">Investigation {id}</h1>
        </div>
        <ErrorState 
          title={errorTitle} 
          description={errorMessage} 
          onRetry={() => {
            setPollingStatus('initializing');
            setErrorMessage(null);
            fetchStatusAndResult();
            pollIntervalRef.current = setInterval(() => {
              fetchStatusAndResult();
            }, 3000);
          }} 
        />
      </div>
    );
  }

  if (pollingStatus === 'fetching_result') {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-4" />
        <h3 className="text-lg font-semibold text-slate-900">Fetching Results...</h3>
        <p className="text-sm text-slate-500 mt-1">Retrieving analysis payload from AI Integration Layer</p>
      </div>
    );
  }

  // Active Polling Status UI (when in progress or pending)
  const isPollingActive = pollingStatus === 'polling';
  const data = resultData;

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
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
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

      {/* Status & Telemetry Metadata Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Status:</span>
            <StatusBadge status={statusInfo?.status || "UNKNOWN"} type="status" />
            {isPollingActive && (
              <span className="flex items-center gap-1.5 text-xs text-blue-600 font-medium bg-blue-50 px-2.5 py-1 rounded-full animate-pulse">
                <Loader2 size={13} className="animate-spin" /> Waiting for AI...
              </span>
            )}
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-500">
            <div>
              <span className="font-semibold text-slate-700">Request ID:</span>{" "}
              <span className="font-mono">{statusInfo?.request_id || "N/A"}</span>
            </div>
            <div>
              <span className="font-semibold text-slate-700">Investigation ID:</span>{" "}
              <span className="font-mono">{statusInfo?.investigation_id || id}</span>
            </div>
          </div>
        </div>

        {/* Progress Bar & AI Message */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs font-medium text-slate-600">
            <span>Execution Progress</span>
            <span>{statusInfo?.progress ?? 100}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
              style={{ width: `${statusInfo?.progress ?? 100}%` }}
            ></div>
          </div>
          {statusInfo?.message && (
            <p className="text-xs text-slate-500 flex items-center gap-1.5 pt-1">
              <Info size={14} className="text-blue-500 shrink-0" />
              <span>AI Message: {statusInfo.message}</span>
            </p>
          )}
        </div>
      </div>

      {/* Full Results Section (Rendered when completed and available) */}
      {data && data.summary ? (
        <>
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
        </>
      ) : null}
    </div>
  );
}
