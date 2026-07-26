import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileType, CheckCircle2, X, ArrowRight, Loader2 } from 'lucide-react';
import { apiService } from '../services/api';
import { LoadingSpinner, ErrorState } from '../components/UIComponents';

export default function Upload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStep, setUploadStep] = useState(null); // 'uploading' | 'creating_investigation' | null
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    validateAndSetFile(droppedFile);
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    validateAndSetFile(selected);
  };

  const validateAndSetFile = (selected) => {
    if (selected && selected.name.endsWith('.csv')) {
      setFile(selected);
      setError(null);
      setStatus(null);
    } else {
      setFile(null);
      setError("Please select a valid CSV file.");
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setStatus(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploadStep('uploading');
    setStatus(null);
    setError(null);

    try {
      // Step 1: Upload & submit investigation to backend AI service
      const res = await apiService.uploadTransactions(file);

      setUploadStep('creating_investigation');
      
      // Short delay for UX transition
      setTimeout(() => {
        setStatus(res);
        setUploadStep(null);
        setFile(null);
      }, 800);

    } catch (err) {
      setUploadStep(null);
      const detail = err.response?.data?.detail || err.message || "Upload failed.";
      setError(detail);
    }
  };

  if (uploadStep === 'uploading') {
    return (
      <div className="p-6 lg:p-8 max-w-4xl mx-auto min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <LoadingSpinner text="Uploading transactions file..." />
        <div className="max-w-md w-full mt-4 h-2 bg-slate-200 rounded-full overflow-hidden">
          <div className="h-full bg-blue-600 rounded-full animate-[progress_1.5s_ease-in-out_infinite]" style={{ width: '50%' }}></div>
        </div>
      </div>
    );
  }

  if (uploadStep === 'creating_investigation') {
    return (
      <div className="p-6 lg:p-8 max-w-4xl mx-auto min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-4" />
        <h3 className="text-lg font-semibold text-slate-900">Creating Investigation...</h3>
        <p className="text-sm text-slate-500 mt-1">Submitting payload to AI Integration Layer</p>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto space-y-8 bg-slate-50 min-h-screen">
      
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Upload Transactions</h1>
        <p className="text-sm text-slate-500 mt-1">Upload transaction CSV files for AI-driven AML analysis.</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-10">
        
        {/* Drag & Drop Area */}
        <div 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center transition-colors cursor-pointer relative
            ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50 hover:bg-slate-100 hover:border-slate-400'}`}
        >
          <input 
            type="file" 
            accept=".csv" 
            onChange={handleFileChange} 
            ref={fileInputRef}
            className="hidden"
          />
          <div className="w-16 h-16 bg-white text-blue-600 rounded-full flex items-center justify-center mb-4 shadow-sm border border-slate-200">
            <UploadCloud size={32} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">Click to browse or drag and drop</h3>
          <p className="text-sm text-slate-500">Supported formats: .csv only</p>
        </div>

        {/* Selected File Card */}
        {file && !error && (
          <div className="mt-8 p-4 border border-slate-200 rounded-xl flex items-center justify-between bg-white shadow-sm">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg border border-blue-100">
                <FileType size={24} />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-900">{file.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <button 
                onClick={handleRemoveFile}
                className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                title="Remove file"
              >
                <X size={20} />
              </button>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mt-8">
            <ErrorState title="Upload Error" description={error} />
          </div>
        )}

        {/* Success State Toast / Card */}
        {status && (
          <div className="mt-8 p-6 bg-green-50 text-green-900 rounded-xl border border-green-200 space-y-4 shadow-sm">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 flex-shrink-0 text-green-600" size={24} />
              <div className="flex-1">
                <p className="text-base font-bold text-green-950">Upload Successful</p>
                <p className="text-sm mt-1 text-green-800">
                  File <span className="font-semibold">{status.file_name}</span> has been uploaded and an investigation has been created.
                </p>
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-white/70 p-3 rounded-lg border border-green-200/60">
                  <div>
                    <span className="text-slate-500 block">Investigation ID</span>
                    <span className="font-mono font-semibold text-slate-900">{status.investigation_id || "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Request ID</span>
                    <span className="font-mono font-semibold text-slate-900">{status.request_id || "N/A"}</span>
                  </div>
                </div>
              </div>
            </div>

            {status.investigation_id && (
              <div className="flex justify-end pt-2">
                <button
                  onClick={() => navigate(`/investigation/${status.investigation_id}`)}
                  className="inline-flex items-center gap-2 px-5 py-2 bg-green-700 text-white text-sm font-semibold rounded-lg hover:bg-green-800 transition-colors shadow-sm"
                >
                  View Investigation <ArrowRight size={16} />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Upload Action */}
        <div className="mt-8 flex justify-end">
          <button
            onClick={handleUpload}
            disabled={!file}
            className="px-6 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-lg shadow-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Start Upload
          </button>
        </div>

      </div>
    </div>
  );
}
