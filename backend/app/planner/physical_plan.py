"""
Physical Plan Generator
Constructs concrete execution plans with physical operators (SeqScan, IndexScan, HashJoin, MergeJoin, NestedLoopJoin).
"""
from typing import Dict, List, Optional
from app.cost.cost_model import CostBreakdown, CostModel
from app.planner.tree_models import PlanNode

class PhysicalPlanGenerator:
    """
    Assembles physical execution trees and calculates exact costs.
    """

    @classmethod
    def create_scan_node(
        cls,
        table_name: str,
        alias: Optional[str],
        access_method: str,  # "SeqScan" or "IndexScan"
        pushed_predicates: List[str],
        estimated_rows: float,
        cost_breakdown: CostBreakdown,
        index_name: Optional[str] = None
    ) -> PlanNode:
        return PlanNode(
            node_type="Scan",
            operator_name=f"{access_method} on {alias if alias else table_name}",
            details={
                "table": table_name,
                "alias": alias,
                "access_method": access_method,
                "index_name": index_name,
                "filter": " AND ".join(pushed_predicates) if pushed_predicates else None
            },
            estimated_rows=estimated_rows,
            estimated_cost=cost_breakdown.total_cost,
            cost_breakdown=cost_breakdown
        )

    @classmethod
    def create_join_node(
        cls,
        join_type: str,  # "HashJoin", "MergeJoin", "NestedLoopJoin"
        left_child: PlanNode,
        right_child: PlanNode,
        join_condition: str,
        estimated_rows: float,
        cost_breakdown: CostBreakdown
    ) -> PlanNode:
        return PlanNode(
            node_type=join_type,
            operator_name=f"{join_type} ({join_condition})",
            details={
                "join_type": join_type,
                "condition": join_condition,
                "left_input": left_child.operator_name,
                "right_input": right_child.operator_name
            },
            estimated_rows=estimated_rows,
            estimated_cost=cost_breakdown.total_cost,
            cost_breakdown=cost_breakdown,
            children=[left_child, right_child]
        )

    @classmethod
    def wrap_with_post_processing(
        cls,
        join_root: PlanNode,
        projections: List[str],
        group_by: List[str],
        order_by: List[str],
        has_aggregates: bool,
        cost_model: CostModel
    ) -> PlanNode:
        """
        Wraps top of physical join tree with Aggregate, Sort, and Projection if needed.
        """
        current = join_root

        # Aggregate
        if group_by or has_aggregates:
            agg_cost = cost_model.cost_aggregate(current.cost_breakdown or CostBreakdown(0, 0, 0, 0), current.estimated_rows)
            agg_rows = max(1.0, current.estimated_rows * 0.5 if group_by else 1.0)
            current = PlanNode(
                node_type="Aggregate",
                operator_name=f"HashAggregate ({', '.join(group_by) if group_by else 'Global'})",
                details={"group_by": group_by, "aggregates": [p for p in projections if "(" in p]},
                estimated_rows=agg_rows,
                estimated_cost=agg_cost.total_cost,
                cost_breakdown=agg_cost,
                children=[current]
            )

        # Sort
        if order_by:
            sort_cost = cost_model.cost_sort(current.cost_breakdown or CostBreakdown(0, 0, 0, 0), current.estimated_rows)
            current = PlanNode(
                node_type="Sort",
                operator_name=f"Sort (Key: {', '.join(order_by)})",
                details={"order_by": order_by},
                estimated_rows=current.estimated_rows,
                estimated_cost=sort_cost.total_cost,
                cost_breakdown=sort_cost,
                children=[current]
            )

        # Projection
        current = PlanNode(
            node_type="Project",
            operator_name="Result Projection",
            details={"projections": projections},
            estimated_rows=current.estimated_rows,
            estimated_cost=current.estimated_cost,
            cost_breakdown=current.cost_breakdown,
            children=[current]
        )

        return current
