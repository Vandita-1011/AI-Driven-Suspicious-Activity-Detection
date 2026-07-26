import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { DashboardCard, StatusBadge, LoadingSpinner, ErrorState } from '../components/UIComponents';
import { 
  FileText, Download, Eye, Search, Filter, 
  Calendar, Clock, CheckCircle2, Archive, PlusCircle, Trash2, Loader2,
  FileJson, FileSpreadsheet
} from 'lucide-react';

export default function Reports() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filtering
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedType, setSelectedType] = useState("All");

  // Report Generation State
  const [reportTypeToGenerate, setReportTypeToGenerate] = useState("Investigation Summary");
  const [reportFormatToGenerate, setReportFormatToGenerate] = useState("PDF");
  const [generating, setGenerating] = useState(false);
  const [genStatus, setGenStatus] = useState(null);

  const fetchReports = async () => {
    try {
      const res = await apiService.getReports();
      setData(res);
    } catch (err) {
      setError("Failed to load reports. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setGenStatus(null);
    try {
      const res = await apiService.generateReport(reportTypeToGenerate, reportFormatToGenerate);
      setGenStatus(res);
      await fetchReports(); // refresh the list
      setTimeout(() => setGenStatus(null), 4000);
    } catch (err) {
      setGenStatus({ status: 'error', message: "Failed to generate report." });
      setTimeout(() => setGenStatus(null), 4000);
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(`Are you sure you want to delete report ${id}?`)) return;
    try {
      await apiService.deleteReport(id);
      await fetchReports();
    } catch (err) {
      alert("Failed to delete report.");
    }
  };

  const handleDownload = (id, format) => {
    // Mock download behavior
    alert(`Downloading report ${id} as ${format}...`);
  };

  if (loading) return <LoadingSpinner text="Loading reports..." />;
  if (error) return <ErrorState title="Reports Error" description={error} onRetry={fetchReports} />;

  const filteredReports = data?.reports?.filter(report => {
    const matchesSearch = 
      report.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.customer?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.alertId?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesType = selectedType === "All" || report.type === selectedType || report.format === selectedType;

    return matchesSearch && matchesType;
  }) || [];

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 bg-slate-50 min-h-screen">
      
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Reports & Export</h1>
        <p className="text-sm text-slate-500 mt-1">Generate, manage, and export AML investigation artifacts.</p>
      </div>

      {/* Summary Cards */}
      {data?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <DashboardCard 
            title="Total Reports" 
            value={data.summary.totalReports.toLocaleString()} 
            icon={FileText} 
          />
          <DashboardCard 
            title="Generated Today" 
            value={data.summary.generatedToday.toLocaleString()} 
            icon={Calendar} 
          />
          <DashboardCard 
            title="Pending Reports" 
            value={data.summary.pendingReports.toLocaleString()} 
            icon={Clock} 
          />
          <DashboardCard 
            title="Archived Reports" 
            value={data.summary.archivedReports.toLocaleString()} 
            icon={Archive} 
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left: Report Generation Card */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
              <PlusCircle className="text-blue-600" size={18} />
              <h3 className="text-base font-semibold text-slate-900">Generate Output</h3>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Content Type</label>
                <select 
                  value={reportTypeToGenerate}
                  onChange={(e) => setReportTypeToGenerate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="Investigation Summary">Investigation Summary</option>
                  <option value="Executive Summary">Executive Summary</option>
                  <option value="Full Case Report">Full Case Report</option>
                  <option value="Monthly AML Summary">Monthly AML Summary</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Export Format</label>
                <div className="grid grid-cols-3 gap-2">
                  <button 
                    onClick={() => setReportFormatToGenerate("PDF")}
                    className={`flex flex-col items-center justify-center p-2 rounded-md border text-xs font-medium transition-colors ${reportFormatToGenerate === "PDF" ? "bg-red-50 border-red-200 text-red-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                  >
                    <FileText size={18} className="mb-1" /> PDF
                  </button>
                  <button 
                    onClick={() => setReportFormatToGenerate("CSV")}
                    className={`flex flex-col items-center justify-center p-2 rounded-md border text-xs font-medium transition-colors ${reportFormatToGenerate === "CSV" ? "bg-green-50 border-green-200 text-green-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                  >
                    <FileSpreadsheet size={18} className="mb-1" /> CSV
                  </button>
                  <button 
                    onClick={() => setReportFormatToGenerate("JSON")}
                    className={`flex flex-col items-center justify-center p-2 rounded-md border text-xs font-medium transition-colors ${reportFormatToGenerate === "JSON" ? "bg-amber-50 border-amber-200 text-amber-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                  >
                    <FileJson size={18} className="mb-1" /> JSON
                  </button>
                </div>
              </div>
              
              <button 
                onClick={handleGenerate}
                disabled={generating}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 mt-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {generating ? <><Loader2 size={16} className="animate-spin" /> Generating...</> : "Generate Export"}
              </button>

              {genStatus && (
                <div className={`mt-3 p-3 text-xs rounded border flex items-start gap-2 ${genStatus.status === 'error' ? 'bg-red-50 text-red-800 border-red-200' : 'bg-green-50 text-green-800 border-green-200'}`}>
                  {genStatus.status === 'error' ? null : <CheckCircle2 size={16} className="text-green-600 shrink-0 mt-0.5" />}
                  <span>{genStatus.message}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Reports Table */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
          
          {/* Toolbar: Search & Filters */}
          <div className="p-4 border-b border-slate-200 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="relative max-w-sm w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                placeholder="Search by Report ID, Alert, Customer..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-slate-400" />
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="pl-3 pr-8 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                <option value="All">All Formats/Types</option>
                <option value="PDF">PDF</option>
                <option value="CSV">CSV</option>
                <option value="JSON">JSON</option>
                <option value="Investigation Summary">Investigation Summary</option>
              </select>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4 font-semibold whitespace-nowrap">Report ID</th>
                  <th className="px-6 py-4 font-semibold whitespace-nowrap">Context</th>
                  <th className="px-6 py-4 font-semibold whitespace-nowrap">Format</th>
                  <th className="px-6 py-4 font-semibold whitespace-nowrap">Status</th>
                  <th className="px-6 py-4 font-semibold whitespace-nowrap">Generated On</th>
                  <th className="px-6 py-4 font-semibold whitespace-nowrap text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.length > 0 ? (
                  filteredReports.map((report) => (
                    <tr key={report.id || report.report_id} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 font-medium text-slate-900 whitespace-nowrap">{report.id || report.report_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <span className="text-slate-900">{report.type || report.name}</span>
                          {(report.alertId || report.customer) && (
                            <span className="text-xs text-slate-500">
                              {report.alertId} • {report.customer}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded ${report.format === 'CSV' ? 'bg-green-100 text-green-700' : report.format === 'JSON' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>
                          {report.format || "PDF"}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={report.status || "Completed"} type="status" />
                      </td>
                      <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                        {report.generatedOn ? new Date(report.generatedOn).toLocaleString(undefined, {
                          month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
                        }) : "N/A"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button 
                            className="inline-flex items-center justify-center p-1.5 bg-white border border-slate-200 text-slate-600 rounded hover:bg-slate-50 transition-colors shadow-sm"
                            title="Preview"
                          >
                            <Eye size={16} />
                          </button>
                          <button 
                            onClick={() => handleDownload(report.id || report.report_id, report.format || "PDF")}
                            className="inline-flex items-center justify-center p-1.5 bg-white border border-slate-200 text-blue-600 rounded hover:bg-blue-50 transition-colors shadow-sm"
                            title="Download"
                          >
                            <Download size={16} />
                          </button>
                          <button 
                            onClick={() => handleDelete(report.id || report.report_id)}
                            className="inline-flex items-center justify-center p-1.5 bg-white border border-slate-200 text-red-500 rounded hover:bg-red-50 transition-colors shadow-sm"
                            title="Delete"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="px-6 py-16 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center space-y-2">
                        <Search size={32} className="text-slate-300" />
                        <p className="text-base font-medium text-slate-900">No reports found.</p>
                        <p className="text-sm">We couldn't find any reports matching your current filters.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

        </div>
      </div>
    </div>
  );
}
