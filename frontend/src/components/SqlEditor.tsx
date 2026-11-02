import React from "react";
import { Play, Sparkles, Database, Code2, Cpu, CheckCircle2 } from "lucide-react";
import { WorkloadItem } from "../types";

interface SqlEditorProps {
  sql: string;
  setSql: (sql: string) => void;
  onAnalyze: () => void;
  onOptimize: () => void;
  onExecute: () => void;
  isAnalyzing: boolean;
  isOptimizing: boolean;
  isExecuting: boolean;
  workloads: WorkloadItem[];
  selectedWorkloadId: string;
  onSelectWorkload: (item: WorkloadItem) => void;
  useCache: boolean;
  setUseCache: (val: boolean) => void;
  activeDbName?: string;
  availableTables?: string[];
}

export const SqlEditor: React.FC<SqlEditorProps> = ({
  sql,
  setSql,
  onAnalyze,
  onOptimize,
  onExecute,
  isAnalyzing,
  isOptimizing,
  isExecuting,
  workloads,
  selectedWorkloadId,
  onSelectWorkload,
  useCache,
  setUseCache,
  activeDbName,
  availableTables = []
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Top bar with Presets and Cache toggle */}
      <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-slate-950/60 border-b border-slate-800 gap-3">
        <div className="flex items-center space-x-2">
          <Code2 className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            SQL Query Input
          </span>
          {activeDbName && (
            <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/60 font-mono">
              DB: {activeDbName}
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Workload Preset Selector */}
          <div className="flex items-center space-x-1.5">
            <Database className="w-3.5 h-3.5 text-purple-400" />
            <select
              value={selectedWorkloadId}
              onChange={(e) => {
                const found = workloads.find((w) => w.id === e.target.value);
                if (found) onSelectWorkload(found);
              }}
              aria-label="Select Workload Preset"
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-md px-2.5 py-1 text-xs font-medium focus:ring-1 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="">Load Preset Workload...</option>
              {workloads.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.difficulty})
                </option>
              ))}
            </select>
          </div>

          {/* Cache Toggle */}
          <label className="flex items-center space-x-1.5 cursor-pointer bg-slate-800/80 px-2.5 py-1 rounded-md border border-slate-700/60 text-xs">
            <input
              type="checkbox"
              checked={useCache}
              onChange={(e) => setUseCache(e.target.checked)}
              className="rounded text-indigo-600 bg-slate-900 border-slate-700 focus:ring-0 focus:ring-offset-0 w-3.5 h-3.5"
            />
            <span className="text-slate-300 text-[11px] font-medium">Plan Cache</span>
          </label>
        </div>
      </div>

      {/* Available Tables Pill Toolbar */}
      {availableTables.length > 0 && (
        <div className="px-4 py-2 bg-slate-950/90 border-b border-slate-800/80 flex items-center space-x-2 overflow-x-auto text-xs">
          <span className="text-slate-500 text-[11px] font-mono shrink-0">Available Tables:</span>
          <div className="flex items-center space-x-1.5">
            {availableTables.map((t, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded bg-slate-900 text-emerald-400 border border-slate-800 font-mono text-[11px] shrink-0"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Code Area */}
      <div className="p-4 bg-slate-950/40">
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          rows={7}
          aria-label="SQL Query Input Textarea"
          className="w-full bg-slate-950/80 text-emerald-300 font-mono text-xs sm:text-sm p-3.5 rounded-lg border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none resize-y leading-relaxed"
          placeholder="Enter safe read-only SQL query (SELECT ... FROM ... WHERE ... JOIN ...)"
          spellCheck={false}
        />
      </div>

      {/* Action Footer */}
      <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-slate-950/80 border-t border-slate-800 gap-3">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-[11px]">Strictly read-only SELECT queries are accepted</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Analyze Button */}
          <button
            onClick={onAnalyze}
            disabled={isAnalyzing || isOptimizing}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{isAnalyzing ? "Analyzing..." : "Analyze AST"}</span>
          </button>

          {/* Optimize Button */}
          <button
            onClick={onOptimize}
            disabled={isOptimizing || isAnalyzing}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-md shadow-indigo-600/25 transition disabled:opacity-50"
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>{isOptimizing ? "Optimizing (DP / Greedy / B&B)..." : "Optimize (All Algorithms)"}</span>
          </button>

          {/* Execute Query Button */}
          <button
            onClick={onExecute}
            disabled={isExecuting || isOptimizing}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-600 text-white shadow-md shadow-emerald-700/20 transition disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isExecuting ? "Executing..." : "Execute & Verify"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
