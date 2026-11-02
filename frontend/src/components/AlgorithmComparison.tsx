import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { Award, Zap, GitBranch, Sparkles, CheckCircle2, TrendingUp, Clock, Compass } from "lucide-react";
import { OptimizationComparisonResponse } from "../types";

interface AlgorithmComparisonProps {
  optimization: OptimizationComparisonResponse | null;
}

export const AlgorithmComparison: React.FC<AlgorithmComparisonProps> = ({ optimization }) => {
  if (!optimization) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs">
        No optimization results available. Submit a query and run "Optimize" to view algorithmic comparison.
      </div>
    );
  }

  const { algorithms, best_algorithm, optimality_gap_percent, explanation } = optimization;

  // Chart data
  const chartData = [
    {
      name: "Dynamic Programming",
      cost: algorithms.dynamic_programming?.estimated_cost || 0,
      timeMs: algorithms.dynamic_programming?.optimization_time_ms || 0,
      explored: algorithms.dynamic_programming?.states_or_plans_explored || 0
    },
    {
      name: "Greedy Algorithm",
      cost: algorithms.greedy?.estimated_cost || 0,
      timeMs: algorithms.greedy?.optimization_time_ms || 0,
      explored: algorithms.greedy?.states_or_plans_explored || 0
    },
    {
      name: "Branch & Bound",
      cost: algorithms.branch_and_bound?.estimated_cost || 0,
      timeMs: algorithms.branch_and_bound?.optimization_time_ms || 0,
      explored: algorithms.branch_and_bound?.states_or_plans_explored || 0
    }
  ];

  const algoCards = [
    {
      key: "dynamic_programming",
      title: "Dynamic Programming",
      badge: "Global Optimum Guaranteed",
      complexity: "O(3^N) Subset DP",
      data: algorithms.dynamic_programming,
      isBest: best_algorithm === "dynamic_programming",
      color: "from-indigo-500/20 to-purple-500/10 border-indigo-500/40"
    },
    {
      key: "greedy",
      title: "Greedy Algorithm",
      badge: "Heuristic Baseline",
      complexity: "O(N^2) Local Minima",
      data: algorithms.greedy,
      isBest: best_algorithm === "greedy",
      color: "from-amber-500/20 to-orange-500/10 border-amber-500/40"
    },
    {
      key: "branch_and_bound",
      title: "Branch and Bound",
      badge: "Pruned State Space",
      complexity: "O(N!) with Lower Bound",
      data: algorithms.branch_and_bound,
      isBest: best_algorithm === "branch_and_bound",
      color: "from-emerald-500/20 to-teal-500/10 border-emerald-500/40"
    }
  ];

  return (
    <div className="space-y-6">
      {/* Explanation Banner */}
      <div className="bg-gradient-to-r from-indigo-950/60 via-purple-950/40 to-slate-900 border border-indigo-500/30 p-4 rounded-xl flex items-start space-x-3 shadow-lg">
        <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
            AOA Optimization Synthesis & Plan Selection
          </h4>
          <p className="mt-1 text-xs text-slate-300 leading-relaxed">{explanation}</p>
        </div>
      </div>

      {/* 3 Algorithm Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {algoCards.map((card) => {
          const res = card.data;
          if (!res) return null;
          const gap = optimality_gap_percent[card.key] ?? 0;

          return (
            <div
              key={card.key}
              className={`bg-slate-900 border rounded-xl p-4 shadow-xl transition-all relative overflow-hidden ${
                card.isBest ? "ring-2 ring-emerald-500/60 border-emerald-500/50" : "border-slate-800"
              }`}
            >
              {card.isBest && (
                <div className="absolute top-0 right-0 bg-emerald-600 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-bl-lg flex items-center space-x-1 shadow-md">
                  <Award className="w-3 h-3" />
                  <span>Optimal Plan</span>
                </div>
              )}

              <div className="mb-3">
                <div className="flex items-center space-x-2">
                  <h3 className="font-bold text-sm text-slate-100">{card.title}</h3>
                </div>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-mono">
                    {card.complexity}
                  </span>
                  <span className="text-[10px] text-slate-400">{card.badge}</span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-800 text-xs">
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                  <span className="text-slate-500 text-[10px] block">Estimated Cost</span>
                  <span className="text-amber-300 font-bold font-mono text-sm">{res.estimated_cost.toFixed(2)}</span>
                </div>

                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                  <span className="text-slate-500 text-[10px] block">Search Time</span>
                  <span className="text-emerald-300 font-bold font-mono text-sm">{res.optimization_time_ms.toFixed(2)} ms</span>
                </div>

                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                  <span className="text-slate-500 text-[10px] block">Plans / States Explored</span>
                  <span className="text-indigo-300 font-bold font-mono text-sm">{res.states_or_plans_explored}</span>
                </div>

                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                  <span className="text-slate-500 text-[10px] block">
                    {card.key === "branch_and_bound" ? "Branches Pruned" : "Optimality Gap"}
                  </span>
                  <span className="text-purple-300 font-bold font-mono text-sm">
                    {card.key === "branch_and_bound" ? res.branches_pruned : `${gap.toFixed(1)}%`}
                  </span>
                </div>
              </div>

              {/* Selected Join Order */}
              <div className="mt-3 pt-2 border-t border-slate-800/80">
                <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">
                  Selected Join Sequence:
                </span>
                <div className="flex flex-wrap items-center gap-1 font-mono text-[11px]">
                  {res.join_order.map((tbl, i) => (
                    <React.Fragment key={i}>
                      <span className="px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                        {tbl}
                      </span>
                      {i < res.join_order.length - 1 && <span className="text-slate-600 text-xs">⨝</span>}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Access Methods */}
              <div className="mt-2 text-[10px] text-slate-400 font-mono">
                <span className="text-slate-500">Access:</span>{" "}
                {Object.entries(res.access_methods)
                  .map(([t, m]) => `${t}(${m})`)
                  .join(", ")}
              </div>
            </div>
          );
        })}
      </div>

      {/* Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Cost & Search Time Bar Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-indigo-400" />
            <span>Estimated Plan Cost by Algorithm</span>
          </h4>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "12px" }}
                  formatter={(val: any) => [Number(val).toFixed(2), "Estimated Cost"]}
                />
                <Bar dataKey="cost" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Explored Search Space Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center space-x-2">
            <Compass className="w-4 h-4 text-purple-400" />
            <span>Search Space Explored (States / Candidate Plans)</span>
          </h4>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "12px" }}
                  formatter={(val: any) => [val, "Explored States"]}
                />
                <Bar dataKey="explored" fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
