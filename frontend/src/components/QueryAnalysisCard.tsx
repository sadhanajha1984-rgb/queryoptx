import React, { useState } from "react";
import { Table, Link2, Filter, Layers, Code, CheckCircle, AlertTriangle } from "lucide-react";
import { QueryAnalysisResponse } from "../types";

interface QueryAnalysisCardProps {
  analysis: QueryAnalysisResponse | null;
}

export const QueryAnalysisCard: React.FC<QueryAnalysisCardProps> = ({ analysis }) => {
  const [showAstJson, setShowAstJson] = useState(false);

  if (!analysis) return null;

  if (!analysis.is_valid) {
    return (
      <div className="bg-rose-950/40 border border-rose-800/80 p-4 rounded-xl text-rose-200 text-xs flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold text-rose-300">Query Validation / Syntax Error</h4>
          <p className="mt-1 text-slate-300">{analysis.error_message || "Invalid SQL syntax or unsafe operation."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-emerald-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Query AST Analysis & Relational Decomposition
          </h3>
        </div>

        <button
          onClick={() => setShowAstJson(!showAstJson)}
          className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[11px] text-indigo-300 border border-slate-700"
        >
          <Code className="w-3 h-3" />
          <span>{showAstJson ? "Hide AST Tree" : "View Raw AST"}</span>
        </button>
      </div>

      {/* Grid of Extracted Metadata */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Tables */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
          <div className="flex items-center space-x-1.5 text-indigo-400 text-xs font-semibold mb-1">
            <Table className="w-3.5 h-3.5" />
            <span>Tables ({analysis.tables.length})</span>
          </div>
          <div className="flex flex-wrap gap-1 mt-1">
            {analysis.tables.map((t, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded text-[11px] bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono"
              >
                {t.name} {t.alias ? `(${t.alias})` : ""}
              </span>
            ))}
          </div>
        </div>

        {/* Joins */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
          <div className="flex items-center space-x-1.5 text-purple-400 text-xs font-semibold mb-1">
            <Link2 className="w-3.5 h-3.5" />
            <span>Joins ({analysis.joins.length})</span>
          </div>
          <div className="space-y-1 mt-1">
            {analysis.joins.length > 0 ? (
              analysis.joins.map((j, idx) => (
                <div key={idx} className="text-[11px] text-slate-300 font-mono truncate" title={j.condition}>
                  {j.left_table}.{j.left_column} = {j.right_table}.{j.right_column}
                </div>
              ))
            ) : (
              <span className="text-[11px] text-slate-500 italic">No joins (Single relation)</span>
            )}
          </div>
        </div>

        {/* Predicates */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
          <div className="flex items-center space-x-1.5 text-amber-400 text-xs font-semibold mb-1">
            <Filter className="w-3.5 h-3.5" />
            <span>Predicates ({analysis.predicates.length})</span>
          </div>
          <div className="space-y-1 mt-1">
            {analysis.predicates.length > 0 ? (
              analysis.predicates.map((p, idx) => (
                <div key={idx} className="text-[11px] text-slate-300 font-mono truncate" title={p.raw_expression}>
                  {p.raw_expression}
                </div>
              ))
            ) : (
              <span className="text-[11px] text-slate-500 italic">No WHERE filters</span>
            )}
          </div>
        </div>

        {/* Projections & Aggregates */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
          <div className="flex items-center space-x-1.5 text-emerald-400 text-xs font-semibold mb-1">
            <Layers className="w-3.5 h-3.5" />
            <span>Projections ({analysis.projections.length})</span>
          </div>
          <div className="flex flex-wrap gap-1 mt-1">
            {analysis.projections.map((p, idx) => (
              <span
                key={idx}
                className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700 font-mono truncate max-w-[120px]"
                title={p}
              >
                {p}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Raw AST Viewer Drawer */}
      {showAstJson && analysis.ast_json && (
        <div className="mt-4 p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-[11px] text-emerald-400 overflow-x-auto max-h-48">
          <pre>{JSON.stringify(analysis.ast_json, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
