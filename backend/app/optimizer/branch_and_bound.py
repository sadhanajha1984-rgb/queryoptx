"""
Branch and Bound Join Optimizer
Implements exact state-space tree search with admissible lower-bound pruning.
"""
import time
from typing import Dict, FrozenSet, List, Optional, Set
from app.cost.cost_model import CostBreakdown
from app.optimizer.base import BaseOptimizer, OptimizerResult, SingleTableAccess
from app.parser.ast_models import ParsedQueryInternal
from app.planner.physical_plan import PhysicalPlanGenerator
from app.planner.tree_models import PlanNode
from app.statistics.cardinality_estimator import CardinalityEstimator

class BranchAndBoundOptimizer(BaseOptimizer):
    """
    Branch and Bound Optimizer:
    Explores the join ordering permutation tree, pruning subtrees whenever the lower bound
    exceeds the best-known upper bound (initialized with greedy heuristic).
    """

    def optimize(self, parsed: ParsedQueryInternal) -> OptimizerResult:
        start_time = time.perf_counter()

        if not parsed.tables:
            empty_node = PlanNode(node_type="Scan", operator_name="EmptyScan")
            return OptimizerResult(
                algorithm_name="Branch & Bound",
                execution_plan=empty_node,
                estimated_cost=0.0,
                cost_breakdown=CostBreakdown(0, 0, 0, 0),
                optimization_time_ms=0.0,
                states_or_plans_explored=0,
                branches_pruned=0
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
                algorithm_name="Branch & Bound",
                execution_plan=final_plan,
                estimated_cost=final_plan.estimated_cost,
                cost_breakdown=final_plan.cost_breakdown or acc.cost_breakdown,
                optimization_time_ms=round(elapsed_ms, 3),
                states_or_plans_explored=1,
                branches_pruned=0,
                join_order=all_relations,
                access_methods={rel: acc.access_method}
            )

        # 1. Get initial upper bound from Greedy optimizer
        from app.optimizer.greedy import GreedyOptimizer
        greedy_opt = GreedyOptimizer(self.catalog, self.cost_model)
        greedy_res = greedy_opt.optimize(parsed)

        best_cost_val = greedy_res.estimated_cost
        best_plan_node = greedy_res.execution_plan
        best_cost_breakdown = greedy_res.cost_breakdown
        best_join_order = greedy_res.join_order

        # Counters
        branches_generated = 0
        branches_pruned = 0
        complete_plans_evaluated = 0

        candidate_join_types = ["HashJoin", "NestedLoopJoin", "MergeJoin"]

        # DFS Branch & Bound search
        def search(
            current_tree: PlanNode,
            current_cost: CostBreakdown,
            current_rows: float,
            joined_set: Set[str],
            current_order: List[str]
        ):
            nonlocal best_cost_val, best_plan_node, best_cost_breakdown, best_join_order
            nonlocal branches_generated, branches_pruned, complete_plans_evaluated

            # Base condition: all relations joined
            if len(joined_set) == n:
                complete_plans_evaluated += 1
                # Wrap with post-processing
                wrapped = PhysicalPlanGenerator.wrap_with_post_processing(
                    join_root=current_tree,
                    projections=[p.name for p in parsed.projections],
                    group_by=parsed.group_by,
                    order_by=parsed.order_by,
                    has_aggregates=parsed.has_aggregates,
                    cost_model=self.cost_model
                )
                if wrapped.estimated_cost < best_cost_val:
                    best_cost_val = wrapped.estimated_cost
                    best_plan_node = wrapped
                    best_cost_breakdown = wrapped.cost_breakdown or current_cost
                    best_join_order = list(current_order)
                return

            remaining = [r for r in all_relations if r not in joined_set]

            for next_rel in remaining:
                branches_generated += 1
                next_acc = base_access[next_rel]
                next_node = next_acc.scan_node
                next_cost = next_acc.cost_breakdown
                next_rows = next_acc.estimated_rows

                # Admissible lower bound: Current Cost + Sum of remaining base scan costs
                remaining_base_cost = sum(base_access[r].cost_breakdown.total_cost for r in remaining if r != next_rel)
                lower_bound = current_cost.total_cost + next_cost.total_cost + remaining_base_cost

                # PRUNING CHECK
                if lower_bound >= best_cost_val:
                    branches_pruned += 1
                    continue

                join_cond = self.find_join_condition(frozenset(joined_set), frozenset([next_rel]), parsed.joins)
                cond_str = join_cond.raw_condition if join_cond else "Cross Join"

                est_rows = CardinalityEstimator.estimate_join_cardinality(
                    left_table="intermediate",
                    left_rows=current_rows,
                    right_table=next_acc.table_name,
                    right_rows=next_rows,
                    join_info=join_cond,
                    catalog=self.catalog
                )

                for jtype in candidate_join_types:
                    if jtype == "HashJoin":
                        jcost = self.cost_model.cost_hash_join(current_cost, current_rows, next_cost, next_rows)
                    elif jtype == "NestedLoopJoin":
                        jcost = self.cost_model.cost_nested_loop_join(current_cost, current_rows, next_cost, next_rows)
                    else:
                        jcost = self.cost_model.cost_merge_join(current_cost, current_rows, next_cost, next_rows)

                    if jcost.total_cost >= best_cost_val:
                        branches_pruned += 1
                        continue

                    new_tree = PhysicalPlanGenerator.create_join_node(
                        join_type=jtype,
                        left_child=current_tree,
                        right_child=next_node,
                        join_condition=cond_str,
                        estimated_rows=est_rows,
                        cost_breakdown=jcost
                    )

                    joined_set.add(next_rel)
                    current_order.append(next_rel)

                    search(new_tree, jcost, est_rows, joined_set, current_order)

                    joined_set.remove(next_rel)
                    current_order.pop()

        # Start B&B exploration from every possible starting relation
        for start_rel in all_relations:
            acc = base_access[start_rel]
            branches_generated += 1
            search(
                current_tree=acc.scan_node,
                current_cost=acc.cost_breakdown,
                current_rows=acc.estimated_rows,
                joined_set={start_rel},
                current_order=[start_rel]
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        access_methods_map = {r: base_access[r].access_method for r in all_relations}

        return OptimizerResult(
            algorithm_name="Branch & Bound",
            execution_plan=best_plan_node,
            estimated_cost=round(best_cost_val, 4),
            cost_breakdown=best_cost_breakdown or CostBreakdown(0, 0, 0, 0),
            optimization_time_ms=round(elapsed_ms, 3),
            states_or_plans_explored=branches_generated,
            branches_pruned=branches_pruned,
            estimated_cardinality=round(best_plan_node.estimated_rows, 2),
            join_order=best_join_order,
            access_methods=access_methods_map,
            explanation=f"Branch and Bound explored {branches_generated} search branches, pruned {branches_pruned} subtrees using admissible lower bounds, and identified optimal plan cost of {round(best_cost_val, 2)}."
        )
