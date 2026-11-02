"""
Tree Models for Logical and Physical Execution Plans
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from app.cost.cost_model import CostBreakdown
from app.schemas.api_models import PlanNodeDTO

@dataclass
class PlanNode:
    node_type: str  # Scan, Filter, Project, Join, HashJoin, NestedLoopJoin, MergeJoin, Sort, Aggregate
    operator_name: str
    details: Dict[str, Any] = field(default_factory=dict)
    estimated_rows: float = 0.0
    estimated_cost: float = 0.0
    cost_breakdown: Optional[CostBreakdown] = None
    children: List["PlanNode"] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    actual_rows: Optional[int] = None
    actual_time_ms: Optional[float] = None

    def to_dto(self) -> PlanNodeDTO:
        return PlanNodeDTO(
            id=self.id,
            node_type=self.node_type,
            operator_name=self.operator_name,
            details=self.details,
            estimated_rows=round(self.estimated_rows, 2),
            estimated_cost=round(self.estimated_cost, 4),
            cost_breakdown=self.cost_breakdown.to_dict() if self.cost_breakdown else None,
            children=[c.to_dto() for c in self.children],
            actual_rows=self.actual_rows,
            actual_time_ms=self.actual_time_ms
        )

    def clone(self) -> "PlanNode":
        cloned_children = [c.clone() for c in self.children]
        return PlanNode(
            node_type=self.node_type,
            operator_name=self.operator_name,
            details=dict(self.details),
            estimated_rows=self.estimated_rows,
            estimated_cost=self.estimated_cost,
            cost_breakdown=self.cost_breakdown,
            children=cloned_children,
            id=str(uuid.uuid4())[:8]
        )
