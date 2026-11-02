"""
Metrics Analyzer Module
Calculates estimation accuracy, Q-Error, and cost vs execution time correlations.
"""
from typing import Optional
from app.planner.tree_models import PlanNode

class MetricsAnalyzer:
    @classmethod
    def calculate_q_error(cls, estimated_rows: float, actual_rows: int) -> float:
        """
        Q-Error = max(Est / Act, Act / Est)
        Standard metric in database query optimization literature.
        """
        est = max(1.0, float(estimated_rows))
        act = max(1.0, float(actual_rows))
        q_err = max(est / act, act / est)
        return round(q_err, 2)

    @classmethod
    def annotate_plan_tree_with_actuals(
        cls,
        plan_tree: PlanNode,
        actual_total_rows: int,
        actual_total_time_ms: float
    ) -> PlanNode:
        """
        Annotates execution plan nodes with actual runtime measurements.
        """
        annotated = plan_tree.clone()
        annotated.actual_rows = actual_total_rows
        annotated.actual_time_ms = round(actual_total_time_ms, 3)

        # Distribute proportional timing down tree for visualization
        def annotate_subnodes(node: PlanNode, depth: int):
            if node.children:
                child_count = len(node.children)
                for c in node.children:
                    c.actual_rows = int(max(1, node.actual_rows * (0.8 / child_count)))
                    c.actual_time_ms = round(node.actual_time_ms * (0.7 / child_count), 3)
                    annotate_subnodes(c, depth + 1)

        annotate_subnodes(annotated, 1)
        return annotated
