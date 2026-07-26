import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Upload, AlertCircle, Search, FileText, Menu, X, Activity } from 'lucide-react';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/upload', label: 'Upload Data', icon: Upload },
  { path: '/alerts', label: 'Alerts', icon: AlertCircle },
  { path: '/investigation/mock', label: 'Investigation', icon: Search },
  { path: '/reports', label: 'Reports', icon: FileText },
];

export default function Sidebar({ isOpen, setIsOpen }) {
  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/50 z-20 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside 
        className={`fixed lg:static inset-y-0 left-0 w-64 bg-slate-900 text-slate-300 h-screen flex flex-col border-r border-slate-800 z-30 transition-transform duration-300 ease-in-out transform ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-2 text-white font-bold text-lg tracking-tight">
            <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white">
              <Activity size={20} />
            </div>
            AML Detect
          </div>
          <button className="lg:hidden text-slate-400 hover:text-white" onClick={() => setIsOpen(false)}>
            <X size={20} />
          </button>
        </div>
        
        <nav className="flex-1 py-6 px-3 flex flex-col gap-1 overflow-y-auto">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 px-3">
            Menu
          </div>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setIsOpen(false)}
              className={({ isActive }) => {
                // Handle partial matching for investigation
                const isItemActive = isActive || (item.path.includes('/investigation') && window.location.pathname.includes('/investigation'));
                return `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                  isItemActive
                    ? 'bg-blue-600 text-white font-medium'
                    : 'hover:bg-slate-800 hover:text-white'
                }`;
              }}
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm font-medium text-white border border-slate-600">
              HA
            </div>
            <div className="text-sm">
              <div className="text-white font-medium">Harsh Analyst</div>
              <div className="text-slate-500 text-xs">harsh@amldetect.com</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
