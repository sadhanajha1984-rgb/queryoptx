"""
FastAPI Endpoints for QueryOptX
"""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query

from app.benchmark.benchmark_engine import BenchmarkEngine
from app.benchmark.workloads import PREDEFINED_WORKLOADS
from app.cache.normalizer import QueryNormalizer
from app.cache.plan_cache import PlanCache
from app.cost.cost_model import CostModel
from app.execution.executor import QueryExecutor
from app.optimizer.comparison import AlgorithmComparator
from app.parser.sql_parser import SQLParser
from app.parser.validator import validate_sql_safety
from app.planner.logical_plan import LogicalPlanBuilder
from app.rewriter.rewrite_engine import QueryRewriteEngine
from app.schemas.api_models import (
    AlgorithmResultDTO,
    BenchmarkResponse,
    BenchmarkWorkloadRequest,
    CacheStatusResponse,
    CatalogSchemaResponse,
    ColumnStatDTO,
    CreateDatabaseRequest,
    DatabaseInfoDTO,
    ExecuteDDLRequest,
    ExecuteQueryRequest,
    JoinInfo,
    OptimizationComparisonResponse,
    PlanCostBreakdown,
    PredicateInfo,
    QueryAnalysisResponse,
    QueryExecutionResponse,
    QueryOptimizeRequest,
    ResetDatabaseSchemaRequest,
    RewriteStepDTO,
    SwitchDatabaseRequest,
    TableRef,
    TableStatDTO
)
from app.statistics.database_manager import DatabaseManager
from app.statistics.stats_collector import StatisticsCollector

router = APIRouter()

# ==========================================================
# 1. Query Analysis Endpoint
# ==========================================================

@router.post("/query/analyze", response_model=QueryAnalysisResponse)
def analyze_query(payload: QueryOptimizeRequest):
    sql = payload.sql
    is_safe, error_msg = validate_sql_safety(sql)
    if not is_safe:
        return QueryAnalysisResponse(
            is_valid=False,
            query_type="UNKNOWN",
            tables=[],
            projections=[],
            predicates=[],
            joins=[],
            error_message=error_msg
        )

    try:
        parsed = SQLParser.parse(sql)
        tables_dto = [TableRef(name=t.name, alias=t.alias) for t in parsed.tables]
        preds_dto = [
            PredicateInfo(
                table=p.table_affinity,
                operator=p.operator,
                value=p.right,
                raw_expression=p.raw_sql,
                is_join_predicate=p.is_join
            )
            for p in parsed.predicates
        ]
        joins_dto = [
            JoinInfo(
                left_table=j.left_table,
                right_table=j.right_table,
                left_column=j.left_column,
                right_column=j.right_column,
                join_type=j.join_type,
                condition=j.raw_condition
            )
            for j in parsed.joins
        ]

        return QueryAnalysisResponse(
            is_valid=True,
            query_type="SELECT",
            tables=tables_dto,
            projections=[p.name for p in parsed.projections],
            predicates=preds_dto,
            joins=joins_dto,
            group_by=parsed.group_by,
            order_by=parsed.order_by,
            has_aggregates=parsed.has_aggregates,
            ast_json=parsed.ast_dict
        )
    except Exception as e:
        return QueryAnalysisResponse(
            is_valid=False,
            query_type="SELECT",
            tables=[],
            projections=[],
            predicates=[],
            joins=[],
            error_message=str(e)
        )

# ==========================================================
# 2. Query Optimization Endpoint
# ==========================================================

@router.post("/query/optimize", response_model=OptimizationComparisonResponse)
def optimize_query(payload: QueryOptimizeRequest):
    sql = payload.sql
    is_safe, err_msg = validate_sql_safety(sql)
    if not is_safe:
        raise HTTPException(status_code=400, detail=err_msg)

    # 1. Normalization & Cache Check
    template_sql, fingerprint = QueryNormalizer.normalize_and_fingerprint(sql)
    plan_cache = PlanCache.get_instance()

    if payload.use_cache:
        cached_entry = plan_cache.get(fingerprint)
        if cached_entry and "result" in cached_entry:
            cached_res = cached_entry["result"]
            cached_res["cache_hit"] = True
            return cached_res

    # 2. Parse SQL
    try:
        parsed = SQLParser.parse(sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parser Error: {str(e)}")

    catalog = StatisticsCollector.get_catalog(db_id=payload.db_id)
    cost_model = CostModel()

    # 3. Build Canonical Logical Plan
    canonical_plan = LogicalPlanBuilder.build_canonical_plan(parsed, catalog)

    # 4. Apply Query Rewrites (Predicate & Projection Pushdown)
    rewritten_plan, rewrites = QueryRewriteEngine.apply_rewrites(parsed, catalog)
    rewrite_steps_dto = [
        RewriteStepDTO(
            rule_name=r.rule_name,
            description=r.description,
            before_summary=r.before_summary,
            after_summary=r.after_summary,
            nodes_affected=r.nodes_affected
        )
        for r in rewrites
    ]

    # 5. Run Optimization Algorithms (DP, Greedy, Branch & Bound)
    results, best_algo, gaps = AlgorithmComparator.compare_all(parsed, catalog, cost_model)

    algorithms_dto: Dict[str, AlgorithmResultDTO] = {}
    for key, res in results.items():
        cost_bd = res.cost_breakdown or CostBreakdown(0, 0, 0, 0)
        algorithms_dto[key] = AlgorithmResultDTO(
            algorithm_name=res.algorithm_name,
            execution_plan=res.execution_plan.to_dto(),
            estimated_cost=res.estimated_cost,
            cost_breakdown=PlanCostBreakdown(
                io_cost=cost_bd.io_cost,
                cpu_cost=cost_bd.cpu_cost,
                memory_cost=cost_bd.memory_cost,
                total_cost=cost_bd.total_cost
            ),
            optimization_time_ms=res.optimization_time_ms,
            states_or_plans_explored=res.states_or_plans_explored,
            branches_pruned=res.branches_pruned,
            estimated_cardinality=res.estimated_cardinality,
            join_order=res.join_order,
            access_methods=res.access_methods
        )

    explanation = (
        f"Algorithm '{results[best_algo].algorithm_name}' produced the optimal execution plan "
        f"with estimated cost of {round(results[best_algo].estimated_cost, 2)} cost units in "
        f"{round(results[best_algo].optimization_time_ms, 2)} ms. "
        f"Dynamic programming guaranteed global optimality over the state space."
    )

    response_data = {
        "query_sql": sql,
        "normalized_fingerprint": fingerprint,
        "cache_hit": False,
        "original_logical_plan": canonical_plan.to_dto(),
        "rewritten_logical_plan": rewritten_plan.to_dto(),
        "rewrite_steps": rewrite_steps_dto,
        "algorithms": algorithms_dto,
        "best_algorithm": best_algo,
        "optimality_gap_percent": gaps,
        "explanation": explanation
    }

    # Store in cache
    plan_cache.put(fingerprint, template_sql, response_data)

    return response_data

# ==========================================================
# 3. Query Execution Endpoint
# ==========================================================

@router.post("/query/execute", response_model=QueryExecutionResponse)
def execute_query(payload: ExecuteQueryRequest):
    sql = payload.sql
    is_safe, err_msg = validate_sql_safety(sql)
    if not is_safe:
        raise HTTPException(status_code=400, detail=err_msg)

    # First optimize to get physical plan
    try:
        parsed = SQLParser.parse(sql)
        catalog = StatisticsCollector.get_catalog(db_id=payload.db_id)
        cost_model = CostModel()
        from app.optimizer.dynamic_programming import DynamicProgrammingOptimizer
        opt = DynamicProgrammingOptimizer(catalog, cost_model)
        opt_res = opt.optimize(parsed)
        
        exec_response = QueryExecutor.execute_query(sql, opt_res.execution_plan, db_id=payload.db_id)
        return exec_response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Execution Failed: {str(e)}")

# ==========================================================
# 4. Benchmark Endpoint
# ==========================================================

@router.post("/query/benchmark", response_model=BenchmarkResponse)
def run_benchmark(payload: BenchmarkWorkloadRequest):
    try:
        res = BenchmarkEngine.run_workload_suite(scale=payload.scale)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark Failed: {str(e)}")

# ==========================================================
# 5. Database Statistics & Schema Endpoints
# ==========================================================

@router.get("/statistics", response_model=CatalogSchemaResponse)
def get_all_statistics(db_id: str = Query(None)):
    catalog = StatisticsCollector.get_catalog(db_id=db_id)
    tables_dto: Dict[str, TableStatDTO] = {}

    for tname, tstat in catalog.tables.items():
        cols_dto: Dict[str, ColumnStatDTO] = {}
        for cname, cstat in tstat.columns.items():
            cols_dto[cname] = ColumnStatDTO(
                column_name=cstat.name,
                data_type=cstat.data_type,
                distinct_values=cstat.distinct_values,
                null_fraction=cstat.null_fraction,
                min_value=cstat.min_value,
                max_value=cstat.max_value,
                has_index=cstat.has_index,
                index_name=cstat.index_name,
                index_type=cstat.index_type
            )
        tables_dto[tname] = TableStatDTO(
            table_name=tstat.name,
            row_count=tstat.row_count,
            page_count=tstat.page_count,
            average_row_width_bytes=tstat.avg_row_width,
            columns=cols_dto,
            indexes=tstat.indexes
        )

    return CatalogSchemaResponse(tables=tables_dto, total_tables=len(tables_dto))

@router.get("/statistics/{table}", response_model=TableStatDTO)
def get_table_statistics(table: str, db_id: str = Query(None)):
    catalog = StatisticsCollector.get_catalog(db_id=db_id)
    tstat = catalog.get_table(table.lower())
    if not tstat:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found in catalog.")

    cols_dto: Dict[str, ColumnStatDTO] = {}
    for cname, cstat in tstat.columns.items():
        cols_dto[cname] = ColumnStatDTO(
            column_name=cstat.name,
            data_type=cstat.data_type,
            distinct_values=cstat.distinct_values,
            null_fraction=cstat.null_fraction,
            min_value=cstat.min_value,
            max_value=cstat.max_value,
            has_index=cstat.has_index,
            index_name=cstat.index_name,
            index_type=cstat.index_type
        )

    return TableStatDTO(
        table_name=tstat.name,
        row_count=tstat.row_count,
        page_count=tstat.page_count,
        average_row_width_bytes=tstat.avg_row_width,
        columns=cols_dto,
        indexes=tstat.indexes
    )

# ==========================================================
# 6. Plan Cache Endpoints
# ==========================================================

@router.get("/cache", response_model=CacheStatusResponse)
def get_cache_status():
    cache = PlanCache.get_instance()
    return cache.get_status()

@router.post("/cache/clear")
def clear_cache():
    cache = PlanCache.get_instance()
    cache.clear()
    return {"message": "Plan cache cleared successfully."}

# ==========================================================
# 7. Database Management Endpoints (Custom & Predefined DBs)
# ==========================================================

@router.get("/databases", response_model=List[DatabaseInfoDTO])
def list_databases():
    mgr = DatabaseManager.get_instance()
    return mgr.list_databases()

@router.post("/databases/create", response_model=DatabaseInfoDTO)
def create_database(payload: CreateDatabaseRequest):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Database name is required.")
    mgr = DatabaseManager.get_instance()
    new_db = mgr.create_database(
        name=payload.name.strip(),
        description=payload.description.strip(),
        ddl=payload.ddl_sql
    )
    return {
        "db_id": new_db.db_id,
        "name": new_db.name,
        "description": new_db.description,
        "is_custom": new_db.is_custom,
        "is_active": new_db.db_id == mgr.active_db_id,
        "table_count": len(new_db.catalog.tables),
        "tables": list(new_db.catalog.tables.keys())
    }

@router.post("/databases/switch")
def switch_database(payload: SwitchDatabaseRequest):
    mgr = DatabaseManager.get_instance()
    success = mgr.set_active_db(payload.db_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Database '{payload.db_id}' not found.")
    return {"message": f"Switched to database '{payload.db_id}'", "active_db_id": payload.db_id}

@router.delete("/databases/{db_id}")
def delete_database(db_id: str):
    mgr = DatabaseManager.get_instance()
    if db_id == "default_univ":
        raise HTTPException(status_code=400, detail="Cannot delete default demonstration database.")
    success = mgr.delete_database(db_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Database '{db_id}' not found.")
    return {"message": f"Database '{db_id}' deleted successfully.", "active_db_id": mgr.active_db_id}

@router.post("/databases/reset-schema", response_model=DatabaseInfoDTO)
def reset_database_schema(payload: ResetDatabaseSchemaRequest):
    """
    Completely reset a custom database's schema by dropping all tables and
    re-executing the provided DDL from scratch. Useful for editing/updating
    schema without 'table already exists' conflicts.
    """
    mgr = DatabaseManager.get_instance()
    db = mgr.databases.get(payload.db_id)
    if not db:
        raise HTTPException(status_code=404, detail=f"Database '{payload.db_id}' not found.")
    if not db.is_custom:
        raise HTTPException(status_code=400, detail="Cannot reset schema of a predefined database.")
    if payload.name:
        db.name = payload.name.strip()
    if payload.description is not None:
        db.description = payload.description.strip()
    success, msg, executed = db.reset_and_reload(payload.ddl_sql)
    if not success:
        raise HTTPException(status_code=400, detail=f"Schema reset error: {msg}")
    return {
        "db_id": db.db_id,
        "name": db.name,
        "description": db.description,
        "is_custom": db.is_custom,
        "is_active": db.db_id == mgr.active_db_id,
        "table_count": len(db.catalog.tables),
        "tables": list(db.catalog.tables.keys()),
        "schema_ddl": db.schema_ddl
    }

@router.post("/databases/execute-ddl")
def execute_ddl(payload: ExecuteDDLRequest):
    mgr = DatabaseManager.get_instance()
    db = mgr.databases.get(payload.db_id)
    if not db:
        raise HTTPException(status_code=404, detail=f"Database '{payload.db_id}' not found.")
    success, msg, executed = db.execute_ddl(payload.ddl_sql)
    if not success:
        raise HTTPException(status_code=400, detail=f"DDL/Insert execution error: {msg}")
    return {
        "status": "success",
        "message": msg,
        "statements_executed": executed,
        "table_count": len(db.catalog.tables),
        "tables": list(db.catalog.tables.keys())
    }

# ==========================================================
# 8. Predefined Workloads & Health
# ==========================================================

@router.get("/workloads")
def get_workloads():
    return PREDEFINED_WORKLOADS

@router.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "QueryOptX Intelligent Query Optimizer",
        "version": "1.0.0"
    }
