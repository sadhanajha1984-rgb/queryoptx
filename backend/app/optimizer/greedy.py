"""
Greedy Optimizer Module
Implements heuristic greedy join ordering: picks local minimum join at each step.
"""
import time
from typing import Dict, List, Optional, Tuple
from app.cost.cost_model import CostBreakdown
from app.optimizer.base import BaseOptimizer, OptimizerResult
from app.parser.ast_models import ParsedQueryInternal
from app.planner.physical_plan import PhysicalPlanGenerator
from app.planner.tree_models import PlanNode
from app.statistics.cardinality_estimator import CardinalityEstimator

class GreedyOptimizer(BaseOptimizer):
    """
    Greedy Join Optimizer:
    Constructs a left-deep execution plan by iteratively selecting the locally cheapest join.
    Time Complexity: O(N^2 * |JoinTypes|), significantly faster than DP but does not guarantee global optimality.
    """

    def optimize(self, parsed: ParsedQueryInternal) -> OptimizerResult:
        start_time = time.perf_counter()

        if not parsed.tables:
            empty_node = PlanNode(node_type="Scan", operator_name="EmptyScan")
            return OptimizerResult(
                algorithm_name="Greedy",
                execution_plan=empty_node,
                estimated_cost=0.0,
                cost_breakdown=CostBreakdown(0, 0, 0, 0),
                optimization_time_ms=0.0,
                states_or_plans_explored=0
            )

        base_access = self.get_base_table_access_paths(parsed)
        all_relations = [t.identifier.lower() for t in parsed.tables]
        n = len(all_relations)

        if n == 1:
            rel = all_relations[0]
            acc = base_access[rel]
            final_plan = PhysicalPlanGenerator.wrap_with_post_processing(
                join_root=acc.scan_node,
                projections=[p.name for p in parsed.projections],
                group_by=parsed.group_by,
                order_by=parsed.order_by,
                has_aggregates=parsed.has_aggregates,
                cost_model=self.cost_model
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return OptimizerResult(
                algorithm_name="Greedy",
                execution_plan=final_plan,
                estimated_cost=final_plan.estimated_cost,
                cost_breakdown=final_plan.cost_breakdown or acc.cost_breakdown,
                optimization_time_ms=round(elapsed_ms, 3),
                states_or_plans_explored=1,
                join_order=all_relations,
                access_methods={rel: acc.access_method}
            )

        plans_evaluated = 0

        # Step 1: Find best initial pair (R1, R2)
        best_initial_pair: Optional[Tuple[str, str]] = None
        best_pair_plan: Optional[PlanNode] = None
        best_pair_cost: Optional[CostBreakdown] = None
        best_pair_rows: float = float("inf")

        candidate_join_types = ["HashJoin", "NestedLoopJoin", "MergeJoin"]

        for i in range(n):
            for j in range(i + 1, n):
                r1 = all_relations[i]
                r2 = all_relations[j]
                node1, cost1, rows1 = base_access[r1].scan_node, base_access[r1].cost_breakdown, base_access[r1].estimated_rows
                node2, cost2, rows2 = base_access[r2].scan_node, base_access[r2].cost_breakdown, base_access[r2].estimated_rows

                join_cond = self.find_join_condition(frozenset([r1]), frozenset([r2]), parsed.joins)
                cond_str = join_cond.raw_condition if join_cond else "Cross Join"

                est_rows = CardinalityEstimator.estimate_join_cardinality(
                    left_table=base_access[r1].table_name,
                    left_rows=rows1,
                    right_table=base_access[r2].table_name,
                    right_rows=rows2,
                    join_info=join_cond,
                    catalog=self.catalog
                )

                for jtype in candidate_join_types:
                    plans_evaluated += 1
                    if jtype == "HashJoin":
                        jcost = self.cost_model.cost_hash_join(cost1, rows1, cost2, rows2)
                    elif jtype == "NestedLoopJoin":
                        jcost = self.cost_model.cost_nested_loop_join(cost1, rows1, cost2, rows2)
                    else:
                        jcost = self.cost_model.cost_merge_join(cost1, rows1, cost2, rows2)

                    if best_pair_cost is None or jcost.total_cost < best_pair_cost.total_cost:
                        best_pair_cost = jcost
                        best_pair_rows = est_rows
                        best_initial_pair = (r1, r2)
                        best_pair_plan = PhysicalPlanGenerator.create_join_node(
                            join_type=jtype,
                            left_child=node1,
                            right_child=node2,
                            join_condition=cond_str,
                            estimated_rows=est_rows,
                            cost_breakdown=jcost
                        )

        current_tree = best_pair_plan
        current_cost = best_pair_cost
        current_rows = best_pair_rows
        joined_relations = set(best_initial_pair)
        join_order = list(best_initial_pair)

        # Step 2: Iteratively join remaining relations greedily
        while len(joined_relations) < n:
            best_next_rel = None
            best_next_plan = None
            best_next_cost = None
            best_next_rows = float("inf")

            remaining = [r for r in all_relations if r not in joined_relations]
            current_subset = frozenset(joined_relations)

            for cand in remaining:
                cand_acc = base_access[cand]
                cand_node = cand_acc.scan_node
                cand_cost = cand_acc.cost_breakdown
                cand_rows = cand_acc.estimated_rows

                join_cond = self.find_join_condition(current_subset, frozenset([cand]), parsed.joins)
                cond_str = join_cond.raw_condition if join_cond else "Cross Join"

                est_rows = CardinalityEstimator.estimate_join_cardinality(
                    left_table="intermediate",
                    left_rows=current_rows,
                    right_table=cand_acc.table_name,
                    right_rows=cand_rows,
                    join_info=join_cond,
                    catalog=self.catalog
                )

                for jtype in candidate_join_types:
                    plans_evaluated += 1
                    if jtype == "HashJoin":
                        jcost = self.cost_model.cost_hash_join(current_cost, current_rows, cand_cost, cand_rows)
                    elif jtype == "NestedLoopJoin":
                        jcost = self.cost_model.cost_nested_loop_join(current_cost, current_rows, cand_cost, cand_rows)
                    else:
                        jcost = self.cost_model.cost_merge_join(current_cost, current_rows, cand_cost, cand_rows)

                    if best_next_cost is None or jcost.total_cost < best_next_cost.total_cost:
                        best_next_cost = jcost
                        best_next_rows = est_rows
                        best_next_rel = cand
                        best_next_plan = PhysicalPlanGenerator.create_join_node(
                            join_type=jtype,
                            left_child=current_tree,
                            right_child=cand_node,
                            join_condition=cond_str,
                            estimated_rows=est_rows,
                            cost_breakdown=jcost
                        )

            current_tree = best_next_plan
            current_cost = best_next_cost
            current_rows = best_next_rows
            joined_relations.add(best_next_rel)
            join_order.append(best_next_rel)

        # Wrap with post processing
        final_plan = PhysicalPlanGenerator.wrap_with_post_processing(
            join_root=current_tree,
            projections=[p.name for p in parsed.projections],
            group_by=parsed.group_by,
            order_by=parsed.order_by,
            has_aggregates=parsed.has_aggregates,
            cost_model=self.cost_model
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        access_methods_map = {r: base_access[r].access_method for r in all_relations}

        return OptimizerResult(
            algorithm_name="Greedy",
            execution_plan=final_plan,
            estimated_cost=round(final_plan.estimated_cost, 4),
            cost_breakdown=final_plan.cost_breakdown or current_cost,
            optimization_time_ms=round(elapsed_ms, 3),
            states_or_plans_explored=plans_evaluated,
            branches_pruned=0,
            estimated_cardinality=round(final_plan.estimated_rows, 2),
            join_order=join_order,
            access_methods=access_methods_map,
            explanation=f"Greedy optimizer made local minimum cost selections in O(N^2) time, exploring {plans_evaluated} candidate configurations in {round(elapsed_ms, 2)} ms."
        )
