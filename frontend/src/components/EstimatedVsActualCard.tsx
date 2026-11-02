import React, { useState } from "react";
import { Clock, Hash, AlertCircle, Database, CheckCircle2, ChevronRight, Terminal, Table } from "lucide-react";
import { QueryExecutionResponse } from "../types";

interface EstimatedVsActualCardProps {
  execution: QueryExecutionResponse | null;
}

export const EstimatedVsActualCard: React.FC<EstimatedVsActualCardProps> = ({ execution }) => {
  const [showRawExplain, setShowRawExplain] = useState(false);
  const [showResultRows, setShowResultRows] = useState(true);

  if (!execution) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs">
        No execution data available. Click "Execute & Verify" in the Workbench to measure actual execution metrics against database.
      </div>
    );
  }

  const { metrics, rows, columns, row_count, raw_postgres_explain } = execution;
  const qError = metrics.q_error;

  const getQErrorColor = (q: number) => {
    if (q <= 2.0) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
    if (q <= 10.0) return "text-amber-400 bg-amber-500/10 border-amber-500/30";
    return "text-rose-400 bg-rose-500/10 border-rose-500/30";
  };

  return (
    <div className="space-y-6">
      {/* Execution Summary Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-100">
                Live Query Execution & Accuracy Analysis
              </h3>
              <span className="text-[11px] text-slate-400 font-mono">Engine: {metrics.engine_used}</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className={`px-2.5 py-1 rounded-md text-xs font-bold border font-mono ${getQErrorColor(qError)}`}>
              Q-Error: {qError.toFixed(2)}x
            </span>
          </div>
        </div>

        {/* 4 Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Estimated vs Actual Rows */}
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
            <span className="text-slate-500 text-[11px] block">Cardinality Accuracy</span>
            <div className="flex items-baseline space-x-2 mt-1">
              <span className="text-sm font-bold text-indigo-300 font-mono">
                {metrics.estimated_rows.toLocaleString()}
              </span>
              <span className="text-slate-500 text-xs">est. vs</span>
              <span className="text-sm font-bold text-emerald-400 font-mono">
                {metrics.actual_rows.toLocaleString()}
              </span>
              <span className="text-slate-500 text-xs">act.</span>
            </div>
            <span className="text-[10px] text-slate-400 block mt-1">
              Estimation Accuracy Factor: {qError.toFixed(2)}x
            </span>
          </div>

          {/* Actual Execution Time */}
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
            <span className="text-slate-500 text-[11px] block">Actual Execution Time</span>
            <div className="flex items-center space-x-1.5 mt-1">
              <Clock className="w-4 h-4 text-emerald-400" />
              <span className="text-base font-bold text-emerald-400 font-mono">
                {metrics.actual_time_ms.toFixed(2)} ms
              </span>
            </div>
            <span className="text-[10px] text-slate-400 block mt-1">
              Planning: {metrics.actual_planning_time_ms ? `${metrics.actual_planning_time_ms.toFixed(2)} ms` : "< 1 ms"}
            </span>
          </div>

          {/* Estimated Cost */}
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
            <span className="text-slate-500 text-[11px] block">Estimated Cost Score</span>
            <div className="flex items-center space-x-1.5 mt-1">
              <span className="text-base font-bold text-amber-300 font-mono">
                {metrics.estimated_cost.toFixed(2)}
              </span>
              <span className="text-slate-400 text-xs">cost units</span>
            </div>
            <span className="text-[10px] text-slate-400 block mt-1">
              Theoretical I/O + CPU model units
            </span>
          </div>

          {/* Cache / DB Status */}
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
            <span className="text-slate-500 text-[11px] block">Execution Pipeline</span>
            <div className="flex items-center space-x-1.5 mt-1">
              <Database className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-semibold text-slate-200 truncate">
                {metrics.cache_status}
              </span>
            </div>
            <span className="text-[10px] text-slate-400 block mt-1">
              Safety checks & read-only enforced
            </span>
          </div>
        </div>

        {/* Academic Note on Cost vs Execution Time */}
        <div className="mt-4 p-3 bg-indigo-950/20 border border-indigo-500/20 rounded-lg text-xs text-slate-300">
          <span className="font-semibold text-indigo-300">AOA Principle (Estimated Cost vs Actual Runtime):</span>{" "}
          Optimizer cost is a dimensionless theoretical estimator used to order alternative execution plans. It does not map 1:1 to physical milliseconds because actual runtime depends on OS buffer cache hits, disk controller caching, and concurrent system load.
        </div>
      </div>

      {/* Query Result Grid */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="flex items-center justify-between px-4 py-3 bg-slate-950/70 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Table className="w-4 h-4 text-emerald-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Query Result Tuples ({row_count} rows returned)
            </h4>
          </div>

          <button
            onClick={() => setShowResultRows(!showResultRows)}
            className="text-xs text-slate-400 hover:text-slate-200"
          >
            {showResultRows ? "Collapse" : "Expand"}
          </button>
        </div>

        {showResultRows && (
          <div className="overflow-x-auto max-h-64">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 sticky top-0">
                <tr>
                  {columns.map((col, idx) => (
                    <th key={idx} className="px-3 py-2 font-mono font-semibold">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {rows.length > 0 ? (
                  rows.map((r, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-800/40">
                      {r.map((cell, cIdx) => (
                        <td key={cIdx} className="px-3 py-2 whitespace-nowrap">
                          {cell !== null && cell !== undefined ? String(cell) : "NULL"}
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={columns.length || 1} className="px-3 py-4 text-center text-slate-500 italic">
                      Empty result set.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* PostgreSQL EXPLAIN JSON */}
      {raw_postgres_explain && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-purple-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Raw PostgreSQL EXPLAIN ANALYZE Output
              </h4>
            </div>
            <button
              onClick={() => setShowRawExplain(!showRawExplain)}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              {showRawExplain ? "Hide EXPLAIN Output" : "View EXPLAIN JSON"}
            </button>
          </div>

          {showRawExplain && (
            <pre className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-[11px] text-emerald-400 overflow-x-auto max-h-60">
              {JSON.stringify(raw_postgres_explain, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};
