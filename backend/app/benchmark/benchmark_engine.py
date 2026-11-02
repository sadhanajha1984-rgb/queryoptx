"""
Benchmark Engine Module
Executes automated scalability and accuracy benchmarks across optimization algorithms.
"""
from typing import Any, Dict, List
from app.benchmark.workloads import PREDEFINED_WORKLOADS
from app.cost.cost_model import CostModel
from app.execution.executor import QueryExecutor
from app.optimizer.branch_and_bound import BranchAndBoundOptimizer
from app.optimizer.dynamic_programming import DynamicProgrammingOptimizer
from app.optimizer.greedy import GreedyOptimizer
from app.parser.sql_parser import SQLParser
from app.rewriter.rewrite_engine import QueryRewriteEngine
from app.schemas.api_models import BenchmarkResponse, BenchmarkRunPoint
from app.statistics.stats_collector import StatisticsCollector

class BenchmarkEngine:
    """
    Executes standard and scaling benchmarks across DP, Greedy, and Branch & Bound.
    """

    @classmethod
    def run_workload_suite(cls, scale: int = 10000) -> BenchmarkResponse:
        catalog = StatisticsCollector.get_catalog(scale=scale)
        cost_model = CostModel()

        data_points: List[BenchmarkRunPoint] = []
        dp_opt = DynamicProgrammingOptimizer(catalog, cost_model)
        greedy_opt = GreedyOptimizer(catalog, cost_model)
        bnb_opt = BranchAndBoundOptimizer(catalog, cost_model)

        for wl in PREDEFINED_WORKLOADS:
            sql = wl["sql"]
            parsed = SQLParser.parse(sql)
            rewritten_plan, _ = QueryRewriteEngine.apply_rewrites(parsed, catalog)

            num_tables = len(parsed.tables)
            num_joins = len(parsed.joins)

            # 1. DP Run
            dp_res = dp_opt.optimize(parsed)
            # Safe execute to measure actual rows & time
            exec_res = None
            try:
                exec_res = QueryExecutor.execute_query(sql, dp_res.execution_plan)
            except Exception:
                pass

            act_rows = exec_res.metrics.actual_rows if exec_res else None
            act_time = exec_res.metrics.actual_time_ms if exec_res else None
            q_err = exec_res.metrics.q_error if exec_res else None

            data_points.append(
                BenchmarkRunPoint(
                    query_name=wl["name"],
                    num_tables=num_tables,
                    num_joins=num_joins,
                    algorithm="Dynamic Programming",
                    optimization_time_ms=dp_res.optimization_time_ms,
                    states_explored=dp_res.states_or_plans_explored,
                    branches_pruned=0,
                    estimated_cost=dp_res.estimated_cost,
                    estimated_rows=dp_res.estimated_cardinality,
                    actual_execution_time_ms=act_time,
                    actual_rows=act_rows,
                    q_error=q_err
                )
            )

            # 2. Greedy Run
            greedy_res = greedy_opt.optimize(parsed)
            data_points.append(
                BenchmarkRunPoint(
                    query_name=wl["name"],
                    num_tables=num_tables,
                    num_joins=num_joins,
                    algorithm="Greedy",
                    optimization_time_ms=greedy_res.optimization_time_ms,
                    states_explored=greedy_res.states_or_plans_explored,
                    branches_pruned=0,
                    estimated_cost=greedy_res.estimated_cost,
                    estimated_rows=greedy_res.estimated_cardinality,
                    actual_execution_time_ms=act_time,
                    actual_rows=act_rows,
                    q_error=q_err
                )
            )

            # 3. Branch & Bound Run
            bnb_res = bnb_opt.optimize(parsed)
            data_points.append(
                BenchmarkRunPoint(
                    query_name=wl["name"],
                    num_tables=num_tables,
                    num_joins=num_joins,
                    algorithm="Branch & Bound",
                    optimization_time_ms=bnb_res.optimization_time_ms,
                    states_explored=bnb_res.states_or_plans_explored,
                    branches_pruned=bnb_res.branches_pruned,
                    estimated_cost=bnb_res.estimated_cost,
                    estimated_rows=bnb_res.estimated_cardinality,
                    actual_execution_time_ms=act_time,
                    actual_rows=act_rows,
                    q_error=q_err
                )
            )

        avg_dp_time = sum(p.optimization_time_ms for p in data_points if p.algorithm == "Dynamic Programming") / max(1, len(PREDEFINED_WORKLOADS))
        avg_greedy_time = sum(p.optimization_time_ms for p in data_points if p.algorithm == "Greedy") / max(1, len(PREDEFINED_WORKLOADS))
        avg_bnb_time = sum(p.optimization_time_ms for p in data_points if p.algorithm == "Branch & Bound") / max(1, len(PREDEFINED_WORKLOADS))

        summary = {
            "total_queries_benchmarked": len(PREDEFINED_WORKLOADS),
            "scale_factor_tuples": scale,
            "avg_optimization_time_ms": {
                "dynamic_programming": round(avg_dp_time, 3),
                "greedy": round(avg_greedy_time, 3),
                "branch_and_bound": round(avg_bnb_time, 3)
            },
            "total_data_points": len(data_points)
        }

        return BenchmarkResponse(summary=summary, data_points=data_points)
