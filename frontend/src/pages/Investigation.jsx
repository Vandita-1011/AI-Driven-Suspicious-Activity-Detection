import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiService } from '../services/api';
import { StatusBadge, LoadingSpinner, ErrorState } from '../components/UIComponents';
import { 
  ArrowLeft, FileText, AlertTriangle, Activity, Database, GitMerge, CheckCircle, 
  MessageSquare, User, Clock, ChevronDown, ChevronUp, Download, Eye, Tag
} from 'lucide-react';

export default function Investigation() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Feedback Modal State
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [submitting, setSubmitting] = useState(false);
  
  // Expandable sections
  const [expandedSections, setExpandedSections] = useState({
    ml: true,
    behavior: true,
    rules: true,
    linked: false
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const pollIntervalRef = useRef(null);

  const fetchInvestigation = async () => {
    try {
      const res = await apiService.getInvestigation(id);
      setData(res);
      if (res.status === "Completed") {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }
    } catch (err) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      setError("Failed to fetch investigation details.");
    }
  };

  const fetchFeedback = async () => {
    try {
      const res = await apiService.getFeedback(id);
      setFeedback(res.feedback || []);
    } catch (err) {
      console.error("Failed to load feedback");
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchInvestigation().then(() => {
      fetchFeedback();
      setLoading(false);
    });

    pollIntervalRef.current = setInterval(() => {
      fetchInvestigation();
    }, 5000);

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [id]);

  const handleSubmitFeedback = async () => {
    setSubmitting(true);
    try {
      await apiService.submitFeedback({
        investigation_id: id,
        rating: feedbackRating,
        notes: feedbackNotes,
        decision_override: "Manual Verification",
        analyst_id: "Current Analyst"
      });
      setFeedbackNotes("");
      setShowFeedbackModal(false);
      await fetchFeedback();
    } catch (err) {
      alert("Failed to submit feedback");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading investigation details..." />;
  if (error) return <ErrorState title="Investigation Error" description={error} onRetry={fetchInvestigation} />;
  if (!data) return <ErrorState title="Not Found" description="Could not find the specified investigation." />;

  const isCompleted = data.status === "Completed";
  const result = data.result || {};
  const report = result.report || {};

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6 bg-slate-50 min-h-screen">
      
      {/* Back & Header */}
      <div className="flex items-center gap-4 mb-2">
        <Link to="/alerts" className="p-2 bg-white border border-slate-200 text-slate-600 rounded-md hover:bg-slate-50 transition-colors">
          <ArrowLeft size={18} />
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Investigation: {id}</h1>
            <StatusBadge status={data.status} type="status" />
          </div>
          <p className="text-sm text-slate-500 mt-1">Review the complete analysis for the selected suspicious transaction.</p>
        </div>
        
        {/* Top Actions */}
        <div className="ml-auto flex gap-2">
          {isCompleted && (
            <>
              <button 
                onClick={() => setShowFeedbackModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 text-slate-700 text-sm font-medium rounded-md hover:bg-slate-50 transition-colors shadow-sm"
              >
                <MessageSquare size={16} /> Analyst Feedback
              </button>
              <button 
                onClick={() => alert("Report generation triggered.")}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 border border-transparent text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors shadow-sm"
              >
                <Download size={16} /> Export Report
              </button>
            </>
          )}
        </div>
      </div>

      {!isCompleted ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 flex flex-col items-center justify-center space-y-4">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-slate-100 border-t-blue-600 rounded-full animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center text-blue-600">
              <Activity size={24} />
            </div>
          </div>
          <h2 className="text-xl font-semibold text-slate-900">Analysis in Progress</h2>
          <p className="text-slate-500 text-center max-w-md">
            The AI engine is currently processing this transaction through multiple detection models. This may take a few moments.
          </p>
        </div>
      ) : (
        <>
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="text-sm font-medium text-slate-500 mb-1">Composite Risk Score</div>
              <div className="flex items-end gap-2">
                <span className={`text-3xl font-bold ${report.risk_score >= 80 ? 'text-red-600' : report.risk_score >= 50 ? 'text-amber-600' : 'text-green-600'}`}>
                  {report.risk_score}/100
                </span>
                <span className="text-sm font-medium text-slate-500 pb-1">Risk</span>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="text-sm font-medium text-slate-500 mb-1">Risk Level</div>
              <div className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                <StatusBadge status={report.risk_level} type="risk" />
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="text-sm font-medium text-slate-500 mb-1">Transaction ID</div>
              <div className="text-lg font-bold text-slate-900 truncate" title={report.transaction_id}>
                {report.transaction_id || "N/A"}
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="text-sm font-medium text-slate-500 mb-1">Customer</div>
              <div className="text-lg font-bold text-slate-900 truncate">
                {report.customer_id || "Unknown"}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Left Column - Explainability */}
            <div className="lg:col-span-2 space-y-6">
              
              {/* Primary Summary */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                <h3 className="text-lg font-bold text-slate-900 mb-2 flex items-center gap-2">
                  <FileText className="text-blue-600" size={20} /> Executive Summary
                </h3>
                <p className="text-slate-700 leading-relaxed text-sm">
                  {report.summary || "No summary available for this investigation."}
                </p>
                <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-lg">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">AI Recommendation</h4>
                  <p className="text-sm font-medium text-slate-800">{report.recommendation || "Manual review required."}</p>
                </div>
              </div>

              {/* Explanations List */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center cursor-pointer" onClick={() => toggleSection('ml')}>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <Database className="text-blue-600" size={18} /> Model Explainability (SHAP)
                  </h3>
                  {expandedSections.ml ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                </div>
                {expandedSections.ml && (
                  <div className="p-4 border-b border-slate-100">
                    <p className="text-sm text-slate-500 mb-4">Key features driving the machine learning risk assessment.</p>
                    <div className="space-y-3">
                      {report.explanations?.length > 0 ? report.explanations.map((exp, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 bg-white border border-slate-200 rounded-lg shadow-sm">
                          <CheckCircle className="text-blue-500 shrink-0 mt-0.5" size={16} />
                          <p className="text-sm text-slate-700 leading-relaxed">{exp}</p>
                        </div>
                      )) : (
                        <p className="text-sm text-slate-500 italic">No specific ML explanations provided.</p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Triggered Rules */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center cursor-pointer" onClick={() => toggleSection('rules')}>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <AlertTriangle className="text-red-500" size={18} /> Triggered Rules
                  </h3>
                  {expandedSections.rules ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                </div>
                {expandedSections.rules && (
                  <div className="p-4">
                    {report.triggered_rules?.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {report.triggered_rules.map((rule, i) => (
                          <div key={i} className="flex items-center gap-2 p-3 bg-red-50 border border-red-100 rounded-lg">
                            <Tag className="text-red-500 shrink-0" size={14} />
                            <span className="text-sm font-medium text-red-900">{rule}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-slate-500 italic">No hard rules triggered.</p>
                    )}
                  </div>
                )}
              </div>

            </div>

            {/* Right Column - Feedback & Context */}
            <div className="space-y-6">
              
              {/* Feedback History */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <MessageSquare className="text-slate-400" size={18} /> Analyst Feedback
                </h3>
                
                {feedback.length > 0 ? (
                  <div className="space-y-4">
                    {feedback.map((fb, i) => (
                      <div key={i} className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                            <User size={12} /> {fb.analyst_id}
                          </div>
                          <span className="text-xs text-slate-500 flex items-center gap-1"><Clock size={12}/> {new Date(fb.timestamp).toLocaleDateString()}</span>
                        </div>
                        <p className="text-sm text-slate-700 italic mb-2">"{fb.notes}"</p>
                        <div className="flex gap-2">
                          <span className="text-xs bg-white border border-slate-200 px-2 py-0.5 rounded text-slate-600 font-medium">Rating: {fb.rating}/10</span>
                          {fb.decision_override && <span className="text-xs bg-blue-50 border border-blue-200 px-2 py-0.5 rounded text-blue-700 font-medium">{fb.decision_override}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 border-2 border-dashed border-slate-200 rounded-lg">
                    <p className="text-sm text-slate-500">No feedback submitted yet.</p>
                  </div>
                )}
              </div>

              {/* Linked Entities (Module 5 Enhancement) */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center cursor-pointer" onClick={() => toggleSection('linked')}>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <GitMerge className="text-slate-400" size={18} /> Linked Entities
                  </h3>
                  {expandedSections.linked ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                </div>
                {expandedSections.linked && (
                  <div className="p-4">
                    <p className="text-sm text-slate-500 mb-3">Accounts sharing similar IP or behavior patterns.</p>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-2 hover:bg-slate-50 rounded border border-transparent hover:border-slate-200 transition-colors">
                        <span className="text-sm font-medium text-slate-700">Account #8892</span>
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded font-semibold">High Risk</span>
                      </div>
                      <div className="flex items-center justify-between p-2 hover:bg-slate-50 rounded border border-transparent hover:border-slate-200 transition-colors">
                        <span className="text-sm font-medium text-slate-700">Account #1102</span>
                        <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-semibold">Closed</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

            </div>
          </div>
        </>
      )}

      {/* Feedback Modal (Module 8) */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
              <h2 className="text-lg font-bold text-slate-900">Provide Analyst Feedback</h2>
              <button onClick={() => setShowFeedbackModal(false)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">&times;</button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">AI Recommendation Quality (1-10)</label>
                <input 
                  type="range" min="1" max="10" 
                  value={feedbackRating} 
                  onChange={e => setFeedbackRating(e.target.value)}
                  className="w-full accent-blue-600"
                />
                <div className="text-right text-xs font-bold text-blue-600 mt-1">{feedbackRating} / 10</div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Investigation Notes & Rationales</label>
                <textarea 
                  value={feedbackNotes}
                  onChange={e => setFeedbackNotes(e.target.value)}
                  rows={4}
                  className="w-full p-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  placeholder="Detail your findings and why you agree/disagree with the AI."
                ></textarea>
              </div>
            </div>
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end gap-2">
              <button 
                onClick={() => setShowFeedbackModal(false)}
                className="px-4 py-2 border border-slate-300 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={handleSubmitFeedback}
                disabled={submitting || !feedbackNotes.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {submitting ? "Saving..." : "Save Feedback"}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
