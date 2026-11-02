import React from "react";
import { X, BookOpen, Sparkles, Calculator, Layers, GitBranch, Zap } from "lucide-react";

interface EducationGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EducationGuideModal: React.FC<EducationGuideModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/80">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">
                AOA Algorithm & Cost Model Theoretical Guide
              </h3>
              <p className="text-xs text-slate-400">
                Analysis & Design of Algorithms (AOA) for Database Relational Query Optimization
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-slate-300 text-xs leading-relaxed">
          {/* Section 1: Problem Formulation */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
            <h4 className="text-sm font-bold text-indigo-400 flex items-center space-x-2">
              <Sparkles className="w-4 h-4" />
              <span>1. The Relational Query Optimization Problem</span>
            </h4>
            <p>
              Given an SQL SELECT query over a set of N relations R = &#123;R_1, R_2, ..., R_N&#125;, the goal is to discover an execution plan tree T that minimizes total estimated cost:
            </p>
            <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800 font-mono text-center text-amber-300 text-xs">
              Plan* = argmin_(T in PlanSpace) [ Cost(T) ]
            </div>
            <p>
              For N relations, the number of possible join permutations is N!, and the number of distinct binary join tree shapes is given by Catalan numbers, leading to an astronomical search space of (2N-2)! / (N-1)!.
            </p>
          </div>

          {/* Section 2: Dynamic Programming */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
            <h4 className="text-sm font-bold text-purple-400 flex items-center space-x-2">
              <Layers className="w-4 h-4" />
              <span>2. Dynamic Programming (Cost-Based Subset Join Enumeration)</span>
            </h4>
            <p>
              Subset DP computes the optimal join tree by solving subproblems for all non-empty subsets S in R in increasing order of cardinality k = 1, 2, ..., N:
            </p>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 font-mono text-emerald-300 text-[11px] leading-normal">
              Base Case (k=1): DP[&#123;R_i&#125;] = min(Cost_SeqScan(R_i), Cost_IndexScan(R_i))<br />
              Recurrence (k &ge; 2): DP[S] = min_(S1 subset S, S2 = S \ S1) min_(algo in HJ,MJ,NL) [ DP[S1] + DP[S2] + Cost_Join(algo, DP[S1], DP[S2]) ]
            </div>
            <p>
              <strong className="text-slate-200">Complexity Analysis:</strong> The total number of disjoint sub-partitions evaluated across all subsets is sum_(k=1)^N (N choose k)(2^k - 2) = 3^N - 2^(N+1) + 1 in O(3^N). Space complexity is O(2^N) memoized states. Dynamic programming guarantees global optimality over the entire bushy and left-deep search space.
            </p>
          </div>

          {/* Section 3: Greedy Optimizer */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
            <h4 className="text-sm font-bold text-amber-400 flex items-center space-x-2">
              <Zap className="w-4 h-4" />
              <span>3. Greedy Join Optimizer (Polynomial Heuristic Baseline)</span>
            </h4>
            <p>
              Greedy optimization constructs a left-deep join tree iteratively:
            </p>
            <ol className="list-decimal list-inside space-y-1 text-slate-300 ml-2">
              <li>Evaluate all initial pairs (R_i, R_j) and select the pair with the minimum immediate join cost.</li>
              <li>At each subsequent step, evaluate joining the current intermediate tree with each remaining unjoined relation R_k.</li>
              <li>Select the candidate R_k and join algorithm that produces the minimum local resulting cost until all relations are joined.</li>
            </ol>
            <p>
              <strong className="text-slate-200">Complexity Analysis:</strong> Time complexity is O(N^2 * |JoinAlgos|). It runs orders of magnitude faster than DP, but lacks backtracking and may commit to sub-optimal local decisions (local minima).
            </p>
          </div>

          {/* Section 4: Branch and Bound */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
            <h4 className="text-sm font-bold text-emerald-400 flex items-center space-x-2">
              <GitBranch className="w-4 h-4" />
              <span>4. Branch and Bound Optimizer (Pruned State Space Search)</span>
            </h4>
            <p>
              Branch and Bound searches the permutation space tree while maintaining a best-known upper bound (initially seeded by the Greedy heuristic):
            </p>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 font-mono text-amber-300 text-[11px]">
              LowerBound(node) = CurrentPartialCost + Sum_(R in Unjoined) [ MinScanCost(R) ]<br />
              Pruning Condition: If LowerBound(node) &ge; BestKnownCost &rarr; Prune Subtree!
            </div>
            <p>
              <strong className="text-slate-200">Admissibility:</strong> Because the lower bound is guaranteed never to overestimate future join and scan costs (LB &le; TrueCost), no optimal plan is ever pruned.
            </p>
          </div>

          {/* Section 5: Cost Model Mathematical Formulas */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
            <h4 className="text-sm font-bold text-indigo-400 flex items-center space-x-2">
              <Calculator className="w-4 h-4" />
              <span>5. QueryOptX Modular Cost Model</span>
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] font-mono">
              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <span className="text-indigo-400 font-bold block">Sequential Scan:</span>
                Cost = Pages &times; c_seq_page + Rows &times; c_cpu_tuple + Rows &times; c_cpu_filter
              </div>
              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <span className="text-purple-400 font-bold block">Index Scan:</span>
                Cost = (log2(Pages) + s &times; IdxPages) &times; c_rand + (s &times; Rows) &times; (c_rand + c_cpu)
              </div>
              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <span className="text-emerald-400 font-bold block">Hash Join:</span>
                Cost = Cost(L) + Cost(R) + Rows_Build &times; c_hash_b + Rows_Probe &times; c_hash_p + Mem
              </div>
              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <span className="text-amber-400 font-bold block">Sort-Merge Join:</span>
                Cost = Cost(L) + Cost(R) + Sort(L) + Sort(R) + (Rows_L + Rows_R) &times; c_merge
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
