import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { HardDrive, Cpu, MemoryStick, Calculator } from "lucide-react";
import { PlanCostBreakdown } from "../types";

interface CostBreakdownChartProps {
  costBreakdown: PlanCostBreakdown | null;
}

export const CostBreakdownChart: React.FC<CostBreakdownChartProps> = ({ costBreakdown }) => {
  if (!costBreakdown) return null;

  const data = [
    { name: "Disk I/O Cost", value: costBreakdown.io_cost, color: "#6366f1" },
    { name: "CPU Evaluation Cost", value: costBreakdown.cpu_cost, color: "#10b981" },
    { name: "Memory / Hash Buffer Cost", value: costBreakdown.memory_cost, color: "#f59e0b" }
  ].filter((d) => d.value > 0);

  const total = costBreakdown.total_cost || 1;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center space-x-2">
          <Calculator className="w-4 h-4 text-indigo-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Cost Model Formula Breakdown
          </h3>
        </div>
        <span className="text-xs font-mono font-bold text-amber-300">
          Total: {costBreakdown.total_cost.toFixed(2)} units
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
        {/* Pie Chart */}
        <div className="h-52 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={75}
                paddingAngle={4}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "12px" }}
                formatter={(val: any) => [`${Number(val).toFixed(2)} (${((Number(val) / total) * 100).toFixed(1)}%)`, "Cost"]}
              />
              <Legend formatter={(val) => <span className="text-slate-300 text-xs">{val}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Cost Formula Cards */}
        <div className="space-y-2 text-xs">
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <HardDrive className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-slate-300">Disk Page I/O Cost</span>
            </div>
            <span className="font-mono font-bold text-indigo-300">
              {costBreakdown.io_cost.toFixed(2)} ({((costBreakdown.io_cost / total) * 100).toFixed(1)}%)
            </span>
          </div>

          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-slate-300">CPU Tuple & Join Cost</span>
            </div>
            <span className="font-mono font-bold text-emerald-300">
              {costBreakdown.cpu_cost.toFixed(2)} ({((costBreakdown.cpu_cost / total) * 100).toFixed(1)}%)
            </span>
          </div>

          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MemoryStick className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-slate-300">Memory & Hash Table Cost</span>
            </div>
            <span className="font-mono font-bold text-amber-300">
              {costBreakdown.memory_cost.toFixed(2)} ({((costBreakdown.memory_cost / total) * 100).toFixed(1)}%)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
