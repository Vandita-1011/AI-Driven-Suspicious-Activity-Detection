import React from 'react';
import { Link } from 'react-router-dom';
import { FileQuestion } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center p-6 text-center">
      <div className="w-20 h-20 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mb-6 shadow-sm border border-blue-100">
        <FileQuestion size={40} />
      </div>
      <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 mb-2">404</h1>
      <h2 className="text-xl font-semibold text-slate-700 mb-4">Page Not Found</h2>
      <p className="text-slate-500 max-w-md mb-8">
        The page you are looking for doesn't exist or has been moved. Please check the URL or navigate back to the dashboard.
      </p>
      <Link 
        to="/dashboard"
        className="px-6 py-3 bg-blue-600 text-white text-sm font-semibold rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
