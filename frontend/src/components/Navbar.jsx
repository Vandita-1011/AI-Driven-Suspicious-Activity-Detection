import React from 'react';
import { Bell, Search, Settings, Menu } from 'lucide-react';

export default function Navbar({ toggleSidebar }) {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-10 shadow-sm shrink-0">
      
      <div className="flex items-center gap-4">
        <button 
          className="lg:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-md"
          onClick={toggleSidebar}
        >
          <Menu size={20} />
        </button>
        <div className="hidden sm:flex items-center w-64 lg:w-96 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Search across platform..." 
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-shadow"
          />
        </div>
      </div>

      <div className="flex items-center gap-3 lg:gap-4 text-slate-500">
        <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-green-50 border border-green-200 text-green-700 rounded-full text-xs font-semibold shadow-sm">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          System Operational
        </div>

        <button className="p-2 hover:bg-slate-100 rounded-full transition-colors relative text-slate-600">
          <Bell size={20} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
        </button>
        <button className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-600 hidden sm:block">
          <Settings size={20} />
        </button>
        <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-300 ml-2 overflow-hidden sm:hidden">
          <img src="https://ui-avatars.com/api/?name=Harsh+Analyst&background=random" alt="Avatar" className="w-full h-full object-cover" />
        </div>
      </div>
    </header>
  );
}
