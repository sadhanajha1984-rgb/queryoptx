"""
Algorithm Comparison Engine
Runs Dynamic Programming, Greedy, and Branch & Bound concurrently on a query and computes optimality metrics.
"""
from typing import Dict, Tuple
from app.cost.cost_model import CostModel
from app.optimizer.base import OptimizerResult
from app.optimizer.branch_and_bound import BranchAndBoundOptimizer
from app.optimizer.dynamic_programming import DynamicProgrammingOptimizer
from app.optimizer.greedy import GreedyOptimizer
from app.parser.ast_models import ParsedQueryInternal
from app.statistics.stats_models import DatabaseCatalog

class AlgorithmComparator:
    """
    Executes and cross-benchmarks DP, Greedy, and Branch & Bound.
    """

    @classmethod
    def compare_all(
        cls,
        parsed: ParsedQueryInternal,
        catalog: DatabaseCatalog,
        cost_model: CostModel
    ) -> Tuple[Dict[str, OptimizerResult], str, Dict[str, float]]:
        # 1. Run DP Optimizer
        dp_opt = DynamicProgrammingOptimizer(catalog, cost_model)
        dp_res = dp_opt.optimize(parsed)

        # 2. Run Greedy Optimizer
        greedy_opt = GreedyOptimizer(catalog, cost_model)
        greedy_res = greedy_opt.optimize(parsed)

        # 3. Run Branch & Bound Optimizer
        bnb_opt = BranchAndBoundOptimizer(catalog, cost_model)
        bnb_res = bnb_opt.optimize(parsed)

        results = {
            "dynamic_programming": dp_res,
            "greedy": greedy_res,
            "branch_and_bound": bnb_res
        }

        # Determine best algorithm (lowest cost, with tie-break on execution time)
        best_name = "dynamic_programming"
        best_cost = dp_res.estimated_cost
        best_time = dp_res.optimization_time_ms

        for key, res in results.items():
            if res.estimated_cost < best_cost - 1e-4:
                best_cost = res.estimated_cost
                best_time = res.optimization_time_ms
                best_name = key
            elif abs(res.estimated_cost - best_cost) <= 1e-4 and res.optimization_time_ms < best_time:
                best_time = res.optimization_time_ms
                best_name = key

        # Calculate Optimality Gap relative to optimal cost
        opt_cost = min(dp_res.estimated_cost, bnb_res.estimated_cost)
        gaps: Dict[str, float] = {}
        for key, res in results.items():
            if opt_cost > 0:
                gap = ((res.estimated_cost - opt_cost) / opt_cost) * 100.0
                gaps[key] = round(max(0.0, gap), 2)
            else:
                gaps[key] = 0.0

        return results, best_name, gaps
