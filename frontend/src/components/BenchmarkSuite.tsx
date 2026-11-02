import React, { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  BarChart,
  Bar
} from "recharts";
import { Play, Cpu, TrendingUp, Scissors, Compass, Database, CheckCircle2 } from "lucide-react";
import { BenchmarkResponse } from "../types";

interface BenchmarkSuiteProps {
  benchmarkData: BenchmarkResponse | null;
  isRunning: boolean;
  onRunBenchmark: (scale: number) => void;
}

export const BenchmarkSuite: React.FC<BenchmarkSuiteProps> = ({
  benchmarkData,
  isRunning,
  onRunBenchmark
}) => {
  const [scale, setScale] = useState<number>(10000);

  const points = benchmarkData?.data_points || [];

  // Group by Number of Tables for Scaling Chart
  const tableCounts = Array.from(new Set(points.map((p) => p.num_tables))).sort((a, b) => a - b);

  const scalingChartData = tableCounts.map((n) => {
    const dpPoint = points.find((p) => p.num_tables === n && p.algorithm === "Dynamic Programming");
    const greedyPoint = points.find((p) => p.num_tables === n && p.algorithm === "Greedy");
    const bnbPoint = points.find((p) => p.num_tables === n && p.algorithm === "Branch & Bound");

    return {
      num_tables: `${n} Tables`,
      dpTime: dpPoint ? dpPoint.optimization_time_ms : 0,
      greedyTime: greedyPoint ? greedyPoint.optimization_time_ms : 0,
      bnbTime: bnbPoint ? bnbPoint.optimization_time_ms : 0,
      dpStates: dpPoint ? dpPoint.states_explored : 0,
      greedyStates: greedyPoint ? greedyPoint.states_explored : 0,
      bnbPruned: bnbPoint ? bnbPoint.branches_pruned : 0
    };
  });

  return (
    <div className="space-y-6">
      {/* Benchmark Control Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-100 flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <span>Automated Algorithmic Scalability & Complexity Benchmark</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Benchmarks DP exponential subset search vs Greedy polynomial heuristic vs Branch & Bound bounding efficiency.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-medium">Dataset Scale:</span>
            <select
              value={scale}
              onChange={(e) => setScale(Number(e.target.value))}
              aria-label="Dataset Scale Factor"
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value={10000}>10,000 Tuples (Standard)</option>
              <option value={100000}>100,000 Tuples (Medium)</option>
              <option value={1000000}>1,000,000 Tuples (Large Scale)</option>
            </select>
          </div>

          <button
            onClick={() => onRunBenchmark(scale)}
            disabled={isRunning}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{isRunning ? "Running Benchmarks..." : "Run Benchmark Suite"}</span>
          </button>
        </div>
      </div>

      {benchmarkData && (
        <>
          {/* Summary Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg">
              <span className="text-xs font-medium text-slate-400 block">Avg. Dynamic Programming Search Time</span>
              <span className="text-xl font-bold text-indigo-400 font-mono mt-1 block">
                {benchmarkData.summary.avg_optimization_time_ms.dynamic_programming} ms
              </span>
              <span className="text-[11px] text-slate-500 mt-1 block">Exhaustive subset DP: O(3^N) space</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg">
              <span className="text-xs font-medium text-slate-400 block">Avg. Greedy Algorithm Search Time</span>
              <span className="text-xl font-bold text-amber-400 font-mono mt-1 block">
                {benchmarkData.summary.avg_optimization_time_ms.greedy} ms
              </span>
              <span className="text-[11px] text-slate-500 mt-1 block">Local minimum heuristic: O(N^2)</span>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg">
              <span className="text-xs font-medium text-slate-400 block">Avg. Branch & Bound Search Time</span>
              <span className="text-xl font-bold text-emerald-400 font-mono mt-1 block">
                {benchmarkData.summary.avg_optimization_time_ms.branch_and_bound} ms
              </span>
              <span className="text-[11px] text-slate-500 mt-1 block">Lower bound pruning engine</span>
            </div>
          </div>

          {/* Scaling Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1: Optimization Time vs Table Count */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-4 flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-indigo-400" />
                <span>Optimization Time (ms) vs Number of Tables (N)</span>
              </h4>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={scalingChartData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="num_tables" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "12px" }}
                      formatter={(val: any) => [`${Number(val).toFixed(2)} ms`, "Time"]}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="dpTime" name="Dynamic Programming" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="greedyTime" name="Greedy" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="bnbTime" name="Branch & Bound" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Branch & Bound Pruning Efficiency */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-4 flex items-center space-x-2">
                <Scissors className="w-4 h-4 text-emerald-400" />
                <span>Branch & Bound Subtree Pruning Count</span>
              </h4>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={scalingChartData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="num_tables" stroke="#64748b" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "12px" }}
                      formatter={(val: any) => [val, "Branches Pruned"]}
                    />
                    <Legend />
                    <Bar dataKey="bnbPruned" name="Branches Pruned via Lower Bound" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Full Benchmark Data Points Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
            <div className="px-4 py-3 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Detailed Workload Benchmark Log
              </h4>
              <span className="text-[11px] text-slate-400 font-mono">
                {points.length} measurements recorded
              </span>
            </div>

            <div className="overflow-x-auto max-h-80">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 font-semibold">Workload Name</th>
                    <th className="px-3 py-2 font-semibold">Tables (N)</th>
                    <th className="px-3 py-2 font-semibold">Algorithm</th>
                    <th className="px-3 py-2 font-semibold">Opt. Time</th>
                    <th className="px-3 py-2 font-semibold">States / Plans</th>
                    <th className="px-3 py-2 font-semibold">Pruned</th>
                    <th className="px-3 py-2 font-semibold">Est. Cost</th>
                    <th className="px-3 py-2 font-semibold">Actual Time</th>
                    <th className="px-3 py-2 font-semibold">Q-Error</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {points.map((p, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="px-3 py-2 font-sans font-medium text-slate-200">{p.query_name}</td>
                      <td className="px-3 py-2 text-indigo-300">{p.num_tables}</td>
                      <td className="px-3 py-2 font-semibold text-slate-100">{p.algorithm}</td>
                      <td className="px-3 py-2 text-emerald-400">{p.optimization_time_ms.toFixed(2)} ms</td>
                      <td className="px-3 py-2 text-purple-300">{p.states_explored}</td>
                      <td className="px-3 py-2 text-amber-300">{p.branches_pruned}</td>
                      <td className="px-3 py-2 text-amber-400 font-bold">{p.estimated_cost.toFixed(2)}</td>
                      <td className="px-3 py-2 text-slate-300">
                        {p.actual_execution_time_ms ? `${p.actual_execution_time_ms.toFixed(2)} ms` : "-"}
                      </td>
                      <td className="px-3 py-2 text-indigo-300">
                        {p.q_error ? `${p.q_error.toFixed(2)}x` : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
