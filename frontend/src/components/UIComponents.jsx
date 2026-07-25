import React from 'react';
import { Loader2 } from 'lucide-react';

export function DashboardCard({ title, value, icon: Icon }) {
  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col">
      <div className="flex justify-between items-start mb-2">
        <div className="text-slate-500 text-sm font-medium">{title}</div>
        {Icon && <div className="text-slate-400"><Icon size={20} /></div>}
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
    </div>
  );
}

export function StatusBadge({ status, type = 'status' }) {
  let colors = 'bg-slate-100 text-slate-800 border-slate-200';
  
  if (type === 'risk') {
    switch (status?.toUpperCase()) {
      case 'HIGH': colors = 'bg-red-100 text-red-800 border-red-200'; break;
      case 'MEDIUM': colors = 'bg-amber-100 text-amber-800 border-amber-200'; break;
      case 'LOW': colors = 'bg-green-100 text-green-800 border-green-200'; break;
    }
  } else {
    switch (status?.toUpperCase()) {
      case 'CLEARED': colors = 'bg-green-100 text-green-800 border-green-200'; break;
      case 'PENDING REVIEW': colors = 'bg-blue-100 text-blue-800 border-blue-200'; break;
      case 'IN PROGRESS': colors = 'bg-purple-100 text-purple-800 border-purple-200'; break;
      case 'ESCALATED': colors = 'bg-red-100 text-red-800 border-red-200'; break;
    }
  }

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${colors}`}>
      {status || 'UNKNOWN'}
    </span>
  );
}

export function LoadingSpinner({ text = "Loading..." }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-slate-500 h-full w-full">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-4" />
      <p className="text-sm font-medium">{text}</p>
    </div>
  );
}

export function ErrorState({ title = "Error", description, onRetry }) {
  return (
    <div className="p-6 bg-red-50 border border-red-100 rounded-xl text-red-800 max-w-lg mx-auto mt-12">
      <h4 className="font-semibold mb-2">{title}</h4>
      <p className="text-sm mb-4">{description}</p>
      {onRetry && (
        <button 
          onClick={onRetry}
          className="px-4 py-2 bg-white border border-red-200 rounded-md text-sm font-medium hover:bg-red-50 transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
