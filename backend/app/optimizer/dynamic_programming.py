"""
Dynamic Programming (Subset DP) Join Optimizer
Implementation of cost-based join ordering via bottom-up memoization.
"""
import itertools
import time
from typing import Dict, FrozenSet, List, Optional, Tuple
from app.cost.cost_model import CostBreakdown
from app.optimizer.base import BaseOptimizer, OptimizerResult, SingleTableAccess
from app.parser.ast_models import ParsedQueryInternal
from app.planner.physical_plan import PhysicalPlanGenerator
from app.planner.tree_models import PlanNode
from app.statistics.cardinality_estimator import CardinalityEstimator

class DynamicProgrammingOptimizer(BaseOptimizer):
    r"""
    Dynamic Programming Join Enumeration Optimizer:
    Computes DP[S] = min { DP[S1] ⨝ DP[S2] } for all S1 ⊂ S, S2 = S \ S1.
    Guarantees global cost optimality within the search space.
    """

    def optimize(self, parsed: ParsedQueryInternal) -> OptimizerResult:
        start_time = time.perf_counter()

        if not parsed.tables:
            empty_node = PlanNode(node_type="Scan", operator_name="EmptyScan")
            return OptimizerResult(
                algorithm_name="Dynamic Programming",
                execution_plan=empty_node,
                estimated_cost=0.0,
                cost_breakdown=CostBreakdown(0, 0, 0, 0),
                optimization_time_ms=0.0,
                states_or_plans_explored=0
            )

        # 1. Base table access paths
        base_access = self.get_base_table_access_paths(parsed)
        all_relations = [t.identifier.lower() for t in parsed.tables]
        n = len(all_relations)

        # DP Memoization Table: frozenset(tables) -> (PlanNode, CostBreakdown, estimated_rows, join_order_list)
        dp_table: Dict[FrozenSet[str], Tuple[PlanNode, CostBreakdown, float, List[str]]] = {}

        plans_evaluated_count = 0

        # Size 1: Base relations
        for rel in all_relations:
            acc = base_access[rel]
            dp_table[frozenset([rel])] = (acc.scan_node, acc.cost_breakdown, acc.estimated_rows, [rel])
            plans_evaluated_count += 1

        # Size k = 2 .. n
        for k in range(2, n + 1):
            for subset in itertools.combinations(all_relations, k):
                subset_set = frozenset(subset)
                best_plan_for_subset: Optional[PlanNode] = None
                best_cost_for_subset: Optional[CostBreakdown] = None
                best_rows_for_subset: float = float("inf")
                best_order_for_subset: List[str] = []

                # Partition subset into S1 and S2
                # (For left-deep and bushy space exploration)
                for s1_size in range(1, k):
                    for s1_comb in itertools.combinations(subset, s1_size):
                        s1 = frozenset(s1_comb)
                        s2 = subset_set - s1

                        if s1 not in dp_table or s2 not in dp_table:
                            continue

                        left_node, left_cost, left_rows, left_order = dp_table[s1]
                        right_node, right_cost, right_rows, right_order = dp_table[s2]

                        join_cond = self.find_join_condition(s1, s2, parsed.joins)
                        cond_str = join_cond.raw_condition if join_cond else "Cross Join"

                        # Join cardinality
                        left_t = left_node.details.get("table", "left")
                        right_t = right_node.details.get("table", "right")
                        est_join_rows = CardinalityEstimator.estimate_join_cardinality(
                            left_table=left_t,
                            left_rows=left_rows,
                            right_table=right_t,
                            right_rows=right_rows,
                            join_info=join_cond,
                            catalog=self.catalog
                        )

                        # Evaluate physical join operator candidates
                        candidate_join_types = ["HashJoin", "NestedLoopJoin", "MergeJoin"]

                        for jtype in candidate_join_types:
                            plans_evaluated_count += 1
                            if jtype == "HashJoin":
                                jcost = self.cost_model.cost_hash_join(left_cost, left_rows, right_cost, right_rows)
                            elif jtype == "NestedLoopJoin":
                                jcost = self.cost_model.cost_nested_loop_join(left_cost, left_rows, right_cost, right_rows)
                            else:  # MergeJoin
                                jcost = self.cost_model.cost_merge_join(left_cost, left_rows, right_cost, right_rows)

                            if best_cost_for_subset is None or jcost.total_cost < best_cost_for_subset.total_cost:
                                best_cost_for_subset = jcost
                                best_rows_for_subset = est_join_rows
                                best_order_for_subset = left_order + right_order
                                best_plan_for_subset = PhysicalPlanGenerator.create_join_node(
                                    join_type=jtype,
                                    left_child=left_node,
                                    right_child=right_node,
                                    join_condition=cond_str,
                                    estimated_rows=est_join_rows,
                                    cost_breakdown=jcost
                                )

                if best_plan_for_subset and best_cost_for_subset:
                    dp_table[subset_set] = (best_plan_for_subset, best_cost_for_subset, best_rows_for_subset, best_order_for_subset)

        # Retrieve optimal join tree for all relations
        full_set = frozenset(all_relations)
        opt_join_root, opt_cost, opt_rows, opt_order = dp_table[full_set]

        # Wrap with aggregations, sorts, projections
        final_plan = PhysicalPlanGenerator.wrap_with_post_processing(
            join_root=opt_join_root,
            projections=[p.name for p in parsed.projections],
            group_by=parsed.group_by,
            order_by=parsed.order_by,
            has_aggregates=parsed.has_aggregates,
            cost_model=self.cost_model
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        access_methods_map = {r: base_access[r].access_method for r in all_relations}

        return OptimizerResult(
            algorithm_name="Dynamic Programming",
            execution_plan=final_plan,
            estimated_cost=round(final_plan.estimated_cost, 4),
            cost_breakdown=final_plan.cost_breakdown or opt_cost,
            optimization_time_ms=round(elapsed_ms, 3),
            states_or_plans_explored=plans_evaluated_count,
            branches_pruned=0,
            estimated_cardinality=round(final_plan.estimated_rows, 2),
            join_order=opt_order,
            access_methods=access_methods_map,
            explanation=f"Dynamic programming searched the exact power-set space (2^{n} subsets, {len(dp_table)} states, {plans_evaluated_count} candidate plans) and guaranteed the global cost-optimal plan ({round(final_plan.estimated_cost, 2)} cost units)."
        )
