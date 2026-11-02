import React from "react";
import { Database, Zap, BookOpen, BarChart3, HardDrive, Cpu, ShieldCheck, RefreshCw, FolderCog } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenTheoryGuide: () => void;
  backendOnline: boolean;
  cacheHitRate: number;
  activeDbName?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onOpenTheoryGuide,
  backendOnline,
  cacheHitRate,
  activeDbName = "Predefined DB"
}) => {
  const tabs = [
    { id: "optimizer", label: "Optimizer", icon: Zap },
    { id: "databases", label: "My Databases", icon: FolderCog },
    { id: "comparison", label: "Algo Comparison", icon: BarChart3 },
    { id: "execution", label: "Est vs Actual", icon: HardDrive },
    { id: "statistics", label: "DB Statistics", icon: Database },
    { id: "benchmarks", label: "Benchmarks", icon: Cpu },
    { id: "cache", label: "Plan Cache", icon: RefreshCw }
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top row: Logo + Status */}
        <div className="flex items-center justify-between pt-3 pb-2">
          {/* Logo & Branding */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
                  QueryOptX
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 hidden sm:inline">
                  v1.0 • AOA Engine
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
                Intelligent Database Query Plan Optimizer &amp; Execution Analyzer
              </p>
            </div>
          </div>

          {/* Right Status & Guide Button */}
          <div className="flex items-center space-x-2 flex-shrink-0">
            {/* Active DB pill indicator */}
            <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-indigo-950/40 border border-indigo-500/30 text-xs">
              <span className="text-slate-400 text-[10px]">Active DB:</span>
              <span className="text-indigo-300 font-semibold text-xs max-w-[120px] truncate" title={activeDbName}>
                {activeDbName}
              </span>
            </div>

            <button
              onClick={onOpenTheoryGuide}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-purple-300 border border-purple-500/30 transition shadow-sm"
              title="AOA Algorithms & Cost Model Guide"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">AOA Theory Guide</span>
            </button>

            <div className="flex items-center space-x-2 px-2.5 py-1 rounded-md bg-slate-800/60 border border-slate-700/60 text-xs">
              <span className={`w-2 h-2 rounded-full ${backendOnline ? "bg-emerald-400 animate-pulse" : "bg-rose-400"}`} />
              <span className="text-slate-300 text-[11px] font-medium hidden sm:inline">
                {backendOnline ? "Engine Online" : "Connecting..."}
              </span>
            </div>
          </div>
        </div>

        {/* Bottom row: Desktop Navigation Tabs */}
        <nav className="hidden md:flex overflow-x-auto border-t border-slate-800/60 pb-0 -mb-px space-x-0.5 scrollbar-none">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold transition-all whitespace-nowrap border-b-2 ${
                  isActive
                    ? "border-indigo-500 text-indigo-300 bg-indigo-500/10"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                }`}
              >
                <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Mobile navigation bar */}
      <div className="md:hidden flex overflow-x-auto px-4 py-2 bg-slate-900 border-t border-slate-800 space-x-1 scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs whitespace-nowrap font-medium ${
                isActive ? "bg-indigo-600 text-white" : "text-slate-400 bg-slate-800/40"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};
