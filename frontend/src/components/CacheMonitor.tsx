import React from "react";
import { RefreshCw, Trash2, Zap, CheckCircle2, AlertCircle, Hash, Clock } from "lucide-react";
import { CacheStatusResponse } from "../types";

interface CacheMonitorProps {
  cacheStatus: CacheStatusResponse | null;
  onClearCache: () => void;
  onRefresh: () => void;
}

export const CacheMonitor: React.FC<CacheMonitorProps> = ({
  cacheStatus,
  onClearCache,
  onRefresh
}) => {
  if (!cacheStatus) return null;

  return (
    <div className="space-y-6">
      {/* Cache Status Summary */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 text-indigo-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-100">
              Query Fingerprint & Execution Plan Cache Monitor
            </h3>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={onRefresh}
              className="flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Refresh</span>
            </button>

            <button
              onClick={onClearCache}
              className="flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-semibold bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/60 transition"
            >
              <Trash2 className="w-3 h-3" />
              <span>Clear Cache</span>
            </button>
          </div>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
            <span className="text-slate-500 text-[11px] block">Cache Hit Rate</span>
            <span className="text-xl font-bold text-emerald-400 font-mono mt-1 block">
              {cacheStatus.hit_rate_percent.toFixed(1)}%
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">
              {cacheStatus.hits} hits / {cacheStatus.hits + cacheStatus.misses} requests
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
            <span className="text-slate-500 text-[11px] block">Total Cached Plans</span>
            <span className="text-xl font-bold text-indigo-400 font-mono mt-1 block">
              {cacheStatus.total_entries}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">
              Max capacity: {cacheStatus.max_size} entries
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
            <span className="text-slate-500 text-[11px] block">Total Cache Hits</span>
            <span className="text-xl font-bold text-emerald-300 font-mono mt-1 block">
              {cacheStatus.hits}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">
              Avoided re-optimization cycles
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
            <span className="text-slate-500 text-[11px] block">Total Cache Misses</span>
            <span className="text-xl font-bold text-amber-400 font-mono mt-1 block">
              {cacheStatus.misses}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">
              Triggered full AOA optimizer pipeline
            </span>
          </div>
        </div>

        {/* Normalization explanation */}
        <div className="mt-4 p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-xs text-slate-300 flex items-start space-x-2">
          <Zap className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p>
            <span className="font-semibold text-amber-300">Structural Query Fingerprinting:</span> Literal constants are masked into parameterized placeholders (e.g. <code className="text-indigo-300 font-mono">WHERE id = 10</code> and <code className="text-indigo-300 font-mono">WHERE id = 500</code> share the same SHA-256 fingerprint). This allows repeated parameterized query patterns to reuse optimal execution plans instantly with zero compilation latency.
          </p>
        </div>
      </div>

      {/* Cached Entries Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="px-4 py-3 bg-slate-950/70 border-b border-slate-800 flex items-center justify-between">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Active Cached Execution Plan Fingerprints
          </h4>
          <span className="text-[11px] text-slate-400 font-mono">
            {cacheStatus.entries.length} active entries in LRU memory
          </span>
        </div>

        <div className="overflow-x-auto max-h-80">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 sticky top-0">
              <tr>
                <th className="px-3 py-2 font-semibold">Fingerprint (SHA-256)</th>
                <th className="px-3 py-2 font-semibold">Normalized SQL Template</th>
                <th className="px-3 py-2 font-semibold">Hits</th>
                <th className="px-3 py-2 font-semibold">Optimal Cost</th>
                <th className="px-3 py-2 font-semibold">Best Algorithm</th>
                <th className="px-3 py-2 font-semibold">Cached At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
              {cacheStatus.entries.length > 0 ? (
                cacheStatus.entries.map((entry, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="px-3 py-2 text-indigo-300 font-bold">{entry.fingerprint}</td>
                    <td className="px-3 py-2 text-slate-300 font-mono max-w-xs truncate" title={entry.sql_template}>
                      {entry.sql_template}
                    </td>
                    <td className="px-3 py-2 text-emerald-400 font-bold">{entry.hits}</td>
                    <td className="px-3 py-2 text-amber-300">{entry.cost.toFixed(2)}</td>
                    <td className="px-3 py-2 text-purple-300 font-sans">{entry.best_algorithm}</td>
                    <td className="px-3 py-2 text-slate-500 text-[11px]">
                      {new Date(entry.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-3 py-6 text-center text-slate-500 italic">
                    Plan cache is empty. Run query optimizations to populate cached plans.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
