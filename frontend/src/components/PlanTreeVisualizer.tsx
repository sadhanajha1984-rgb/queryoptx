import React, { useState } from "react";
import { ChevronDown, ChevronRight, Cpu, HardDrive, Layers, ArrowDown, Database, Clock, Hash } from "lucide-react";
import { PlanNodeDTO } from "../types";

interface PlanTreeVisualizerProps {
  plan: PlanNodeDTO | null;
  title: string;
  isOptimal?: boolean;
}

export const PlanTreeVisualizer: React.FC<PlanTreeVisualizerProps> = ({ plan, title, isOptimal = false }) => {
  if (!plan) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs">
        No execution plan generated yet. Run optimization to visualize plan tree.
      </div>
    );
  }

  return (
    <div className={`bg-slate-900 border rounded-xl overflow-hidden shadow-xl ${isOptimal ? "border-emerald-500/50" : "border-slate-800"}`}>
      <div className="flex items-center justify-between px-4 py-3 bg-slate-950/70 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Layers className={`w-4 h-4 ${isOptimal ? "text-emerald-400" : "text-indigo-400"}`} />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">{title}</h3>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono">
            <span className="text-slate-400 text-[10px]">Est. Cost:</span>
            <span className="text-amber-300 font-bold">{plan.estimated_cost.toFixed(2)}</span>
          </div>

          <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono">
            <span className="text-slate-400 text-[10px]">Est. Rows:</span>
            <span className="text-indigo-300 font-bold">{plan.estimated_rows.toLocaleString()}</span>
          </div>
        </div>
      </div>

      <div className="p-5 bg-slate-950/40 overflow-x-auto">
        <div className="min-w-[600px] flex flex-col items-center">
          <PlanNodeCard node={plan} isRoot={true} />
        </div>
      </div>
    </div>
  );
};

interface PlanNodeCardProps {
  node: PlanNodeDTO;
  isRoot?: boolean;
}

const PlanNodeCard: React.FC<PlanNodeCardProps> = ({ node, isRoot = false }) => {
  const [expanded, setExpanded] = useState(true);

  // Badge styling based on operator type
  const getBadgeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "hashjoin":
        return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
      case "mergejoin":
        return "bg-teal-500/15 text-teal-300 border-teal-500/30";
      case "nestedloopjoin":
      case "nestedloop":
        return "bg-amber-500/15 text-amber-300 border-amber-500/30";
      case "scan":
        return node.operator_name.toLowerCase().includes("index")
          ? "bg-purple-500/15 text-purple-300 border-purple-500/30"
          : "bg-blue-500/15 text-blue-300 border-blue-500/30";
      case "filter":
        return "bg-rose-500/15 text-rose-300 border-rose-500/30";
      case "sort":
        return "bg-orange-500/15 text-orange-300 border-orange-500/30";
      case "aggregate":
        return "bg-pink-500/15 text-pink-300 border-pink-500/30";
      default:
        return "bg-indigo-500/15 text-indigo-300 border-indigo-500/30";
    }
  };

  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="flex flex-col items-center my-1.5 w-full">
      {/* Node Box */}
      <div
        className={`w-80 rounded-xl p-3 bg-slate-900/90 border border-slate-700/80 shadow-md hover:border-indigo-500/60 transition-all ${
          isRoot ? "ring-1 ring-indigo-500/40" : ""
        }`}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getBadgeColor(node.node_type)}`}>
              {node.node_type}
            </span>
            <span className="text-xs font-semibold text-slate-200 truncate max-w-[140px]" title={node.operator_name}>
              {node.operator_name}
            </span>
          </div>

          {hasChildren && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-slate-400 hover:text-slate-200 p-0.5"
              title={expanded ? "Collapse children" : "Expand children"}
            >
              {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
          )}
        </div>

        {/* Details snippet */}
        {node.details && (
          <div className="mt-2 text-[11px] text-slate-400 font-mono bg-slate-950/60 p-1.5 rounded border border-slate-800/60 space-y-0.5">
            {node.details.table && (
              <div>
                <span className="text-slate-500">Table:</span> <span className="text-slate-300">{node.details.table}</span>
              </div>
            )}
            {node.details.access_method && (
              <div>
                <span className="text-slate-500">Access:</span>{" "}
                <span className={node.details.access_method === "IndexScan" ? "text-purple-300" : "text-blue-300"}>
                  {node.details.access_method}
                </span>
                {node.details.index_name && <span className="text-slate-500 text-[10px]"> ({node.details.index_name})</span>}
              </div>
            )}
            {node.details.condition && (
              <div className="truncate" title={node.details.condition}>
                <span className="text-slate-500">On:</span> <span className="text-emerald-300">{node.details.condition}</span>
              </div>
            )}
            {node.details.filter && (
              <div className="truncate" title={node.details.filter}>
                <span className="text-slate-500">Filter:</span> <span className="text-rose-300">{node.details.filter}</span>
              </div>
            )}
          </div>
        )}

        {/* Cost & Cardinality Metrics */}
        <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
          <div className="flex items-center space-x-1 text-slate-400">
            <Cpu className="w-3 h-3 text-amber-400" />
            <span>Cost:</span>
            <span className="text-amber-300 font-semibold font-mono">{node.estimated_cost.toFixed(2)}</span>
          </div>

          <div className="flex items-center space-x-1 text-slate-400">
            <Hash className="w-3 h-3 text-indigo-400" />
            <span>Rows:</span>
            <span className="text-indigo-300 font-semibold font-mono">{node.estimated_rows.toLocaleString()}</span>
          </div>
        </div>

        {/* Actual Execution Metrics if Available */}
        {node.actual_rows !== null && node.actual_rows !== undefined && (
          <div className="mt-2 pt-1.5 border-t border-emerald-900/60 flex items-center justify-between text-[10px] bg-emerald-950/20 px-2 py-1 rounded">
            <span className="text-emerald-400 font-semibold">Actual Exec:</span>
            <div className="flex items-center space-x-2 font-mono">
              <span className="text-slate-300">{node.actual_rows.toLocaleString()} rows</span>
              {node.actual_time_ms !== null && node.actual_time_ms !== undefined && (
                <span className="text-emerald-300 font-bold">{node.actual_time_ms.toFixed(2)} ms</span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Children branches */}
      {hasChildren && expanded && (
        <div className="flex flex-col items-center w-full">
          <div className="h-4 w-px bg-slate-700" />
          <div className="flex justify-center items-start space-x-6 relative">
            {node.children.length > 1 && (
              <div
                className="absolute top-0 h-px bg-slate-700"
                style={{
                  left: "25%",
                  right: "25%"
                }}
              />
            )}
            {node.children.map((child) => (
              <div key={child.id} className="flex flex-col items-center">
                <PlanNodeCard node={child} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
