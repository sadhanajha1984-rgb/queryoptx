"""
Base Optimizer Interface and Data Classes
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from app.cost.cost_model import CostBreakdown, CostModel
from app.parser.ast_models import JoinInternal, ParsedQueryInternal
from app.planner.tree_models import PlanNode
from app.statistics.stats_models import DatabaseCatalog

@dataclass
class SingleTableAccess:
    table_identifier: str
    table_name: str
    alias: Optional[str]
    access_method: str  # "SeqScan" or "IndexScan"
    index_name: Optional[str]
    estimated_rows: float
    cost_breakdown: CostBreakdown
    scan_node: PlanNode

@dataclass
class OptimizerResult:
    algorithm_name: str
    execution_plan: PlanNode
    estimated_cost: float
    cost_breakdown: CostBreakdown
    optimization_time_ms: float
    states_or_plans_explored: int
    branches_pruned: int = 0
    estimated_cardinality: float = 0.0
    join_order: List[str] = field(default_factory=list)
    access_methods: Dict[str, str] = field(default_factory=dict)
    explanation: str = ""

class BaseOptimizer(ABC):
    def __init__(self, catalog: DatabaseCatalog, cost_model: Optional[CostModel] = None):
        self.catalog = catalog
        self.cost_model = cost_model or CostModel()

    @abstractmethod
    def optimize(self, parsed: ParsedQueryInternal) -> OptimizerResult:
        pass

    def get_base_table_access_paths(self, parsed: ParsedQueryInternal) -> Dict[str, SingleTableAccess]:
        """
        Determines the optimal base access method (SeqScan vs IndexScan) for each table in the query.
        """
        from app.planner.physical_plan import PhysicalPlanGenerator
        from app.statistics.cardinality_estimator import CardinalityEstimator

        access_paths: Dict[str, SingleTableAccess] = {}

        for tbl in parsed.tables:
            t_ident = tbl.identifier.lower()
            t_name = tbl.name.lower()
            tbl_stat = self.catalog.get_table(t_name)

            # Find single-table predicates for this table
            preds = [p for p in parsed.predicates if (p.table_affinity or "").lower() in (t_ident, t_name)]
            pred_cols = [p.left.split(".")[-1].lower() for p in preds]

            # Calculate selectivity
            combined_sel = 1.0
            for p in preds:
                combined_sel *= CardinalityEstimator.estimate_filter_selectivity(p, self.catalog)

            if tbl_stat:
                method, cost = self.cost_model.find_best_access_path(tbl_stat, combined_sel, pred_cols)
                est_rows = max(1.0, float(tbl_stat.row_count) * combined_sel)
                idx_name = None
                if method == "IndexScan":
                    for col in pred_cols:
                        c_stat = tbl_stat.columns.get(col)
                        if c_stat and c_stat.has_index:
                            idx_name = c_stat.index_name
                            break
            else:
                method = "SeqScan"
                cost = CostBreakdown(10.0, 10.0, 0.0, 20.0)
                est_rows = 1000.0
                idx_name = None

            scan_node = PhysicalPlanGenerator.create_scan_node(
                table_name=t_name,
                alias=tbl.alias,
                access_method=method,
                pushed_predicates=[p.raw_sql for p in preds],
                estimated_rows=est_rows,
                cost_breakdown=cost,
                index_name=idx_name
            )

            access_paths[t_ident] = SingleTableAccess(
                table_identifier=t_ident,
                table_name=t_name,
                alias=tbl.alias,
                access_method=method,
                index_name=idx_name,
                estimated_rows=est_rows,
                cost_breakdown=cost,
                scan_node=scan_node
            )

        return access_paths

    def find_join_condition(self, subset_a: frozenset[str], subset_b: frozenset[str], joins: List[JoinInternal]) -> Optional[JoinInternal]:
        """
        Finds join predicate connecting subset_a and subset_b if any exists.
        """
        for j in joins:
            left_t = j.left_table.lower()
            right_t = j.right_table.lower()
            if (left_t in subset_a and right_t in subset_b) or (left_t in subset_b and right_t in subset_a):
                return j
        return None
