"""
Pydantic API Schemas for QueryOptX
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# ==========================================================
# 1. AST & Query Analysis Schemas
# ==========================================================

class TableRef(BaseModel):
    name: str
    alias: Optional[str] = None

class PredicateInfo(BaseModel):
    table: Optional[str] = None
    column: Optional[str] = None
    operator: str
    value: Any
    raw_expression: str
    is_join_predicate: bool = False

class JoinInfo(BaseModel):
    left_table: str
    right_table: str
    left_column: str
    right_column: str
    join_type: str = "INNER"
    condition: str

class QueryAnalysisResponse(BaseModel):
    is_valid: bool
    query_type: str
    tables: List[TableRef]
    projections: List[str]
    predicates: List[PredicateInfo]
    joins: List[JoinInfo]
    group_by: List[str] = []
    order_by: List[str] = []
    has_aggregates: bool = False
    error_message: Optional[str] = None
    ast_json: Optional[Dict[str, Any]] = None

# ==========================================================
# 2. Logical & Physical Plan Schemas
# ==========================================================

class PlanNodeDTO(BaseModel):
    id: str
    node_type: str  # Scan, Filter, Project, HashJoin, NestedLoopJoin, MergeJoin, Sort, Aggregate
    operator_name: str
    details: Dict[str, Any] = Field(default_factory=dict)
    estimated_rows: float
    estimated_cost: float
    cost_breakdown: Optional[Dict[str, float]] = None
    children: List["PlanNodeDTO"] = []
    actual_rows: Optional[int] = None
    actual_time_ms: Optional[float] = None

PlanNodeDTO.model_rebuild()

class RewriteStepDTO(BaseModel):
    rule_name: str
    description: str
    before_summary: str
    after_summary: str
    nodes_affected: List[str] = []

class PlanCostBreakdown(BaseModel):
    io_cost: float
    cpu_cost: float
    memory_cost: float
    total_cost: float

# ==========================================================
# 3. Optimizer Response Schemas
# ==========================================================

class AlgorithmResultDTO(BaseModel):
    algorithm_name: str  # "Dynamic Programming", "Greedy", "Branch & Bound"
    execution_plan: PlanNodeDTO
    estimated_cost: float
    cost_breakdown: PlanCostBreakdown
    optimization_time_ms: float
    states_or_plans_explored: int
    branches_pruned: Optional[int] = 0
    estimated_cardinality: float
    join_order: List[str]
    access_methods: Dict[str, str]  # table -> access method (SeqScan, IndexScan)

class OptimizationComparisonResponse(BaseModel):
    query_sql: str
    normalized_fingerprint: str
    cache_hit: bool
    original_logical_plan: PlanNodeDTO
    rewritten_logical_plan: PlanNodeDTO
    rewrite_steps: List[RewriteStepDTO]
    algorithms: Dict[str, AlgorithmResultDTO]  # "dynamic_programming", "greedy", "branch_and_bound"
    best_algorithm: str
    optimality_gap_percent: Dict[str, float]  # comparison vs DP optimal
    explanation: str

# ==========================================================
# 4. Query Execution & Verification Schemas
# ==========================================================

class ExecuteQueryRequest(BaseModel):
    sql: str
    algorithm: Optional[str] = "dynamic_programming"
    db_id: Optional[str] = None

class ExecutionMetricDTO(BaseModel):
    estimated_rows: float
    actual_rows: int
    q_error: float  # max(est/act, act/est)
    estimated_cost: float
    actual_time_ms: float
    actual_planning_time_ms: Optional[float] = None
    cache_status: str
    engine_used: str  # "PostgreSQL Live" or "QueryOptX Simulated Engine"

class QueryExecutionResponse(BaseModel):
    status: str
    sql: str
    row_count: int
    columns: List[str]
    rows: List[List[Any]]
    execution_plan_with_metrics: PlanNodeDTO
    metrics: ExecutionMetricDTO
    raw_postgres_explain: Optional[Dict[str, Any]] = None

# ==========================================================
# 5. Statistics & Catalog Schemas
# ==========================================================

class ColumnStatDTO(BaseModel):
    column_name: str
    data_type: str
    distinct_values: int
    null_fraction: float
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    has_index: bool
    index_name: Optional[str] = None
    index_type: Optional[str] = None

class TableStatDTO(BaseModel):
    table_name: str
    row_count: int
    page_count: int
    average_row_width_bytes: int
    columns: Dict[str, ColumnStatDTO]
    indexes: List[str]

class CatalogSchemaResponse(BaseModel):
    tables: Dict[str, TableStatDTO]
    total_tables: int

# ==========================================================
# 6. Benchmark Schemas
# ==========================================================

class BenchmarkWorkloadRequest(BaseModel):
    scale: int = 10000
    workload_types: List[str] = ["simple", "medium", "complex", "multi_join"]

class BenchmarkRunPoint(BaseModel):
    query_name: str
    num_tables: int
    num_joins: int
    algorithm: str
    optimization_time_ms: float
    states_explored: int
    branches_pruned: int
    estimated_cost: float
    estimated_rows: float
    actual_execution_time_ms: Optional[float] = None
    actual_rows: Optional[int] = None
    q_error: Optional[float] = None

class BenchmarkResponse(BaseModel):
    summary: Dict[str, Any]
    data_points: List[BenchmarkRunPoint]

# ==========================================================
# 7. Cache Schemas
# ==========================================================

class CacheEntryDTO(BaseModel):
    fingerprint: str
    sql_template: str
    created_at: str
    hits: int
    cost: float
    best_algorithm: str

class CacheStatusResponse(BaseModel):
    total_entries: int
    max_size: int
    hits: int
    misses: int
    hit_rate_percent: float
    entries: List[CacheEntryDTO]

# ==========================================================
# 8. Request Schemas
# ==========================================================

class QueryOptimizeRequest(BaseModel):
    sql: str
    algorithm: Optional[str] = "all"  # "dp", "greedy", "branch_and_bound", "all"
    use_cache: bool = True
    db_id: Optional[str] = None

# ==========================================================
# 9. Database Management Schemas
# ==========================================================

class DatabaseInfoDTO(BaseModel):
    db_id: str
    name: str
    description: str
    is_custom: bool
    is_active: bool
    table_count: int
    tables: List[str]
    schema_ddl: Optional[str] = ""

class CreateDatabaseRequest(BaseModel):
    name: str
    description: str = ""
    ddl_sql: Optional[str] = ""

class ResetDatabaseSchemaRequest(BaseModel):
    db_id: str
    ddl_sql: str
    name: Optional[str] = None
    description: Optional[str] = None

class ExecuteDDLRequest(BaseModel):
    db_id: str
    ddl_sql: str

class SwitchDatabaseRequest(BaseModel):
    db_id: str

