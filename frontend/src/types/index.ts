/**
 * QueryOptX Frontend TypeScript Interfaces
 */

export interface TableRef {
  name: string;
  alias?: string | null;
}

export interface PredicateInfo {
  table?: string | null;
  column?: string | null;
  operator: string;
  value: any;
  raw_expression: string;
  is_join_predicate: boolean;
}

export interface JoinInfo {
  left_table: string;
  right_table: string;
  left_column: string;
  right_column: string;
  join_type: string;
  condition: string;
}

export interface QueryAnalysisResponse {
  is_valid: boolean;
  query_type: string;
  tables: TableRef[];
  projections: string[];
  predicates: PredicateInfo[];
  joins: JoinInfo[];
  group_by: string[];
  order_by: string[];
  has_aggregates: boolean;
  error_message?: string | null;
  ast_json?: Record<string, any> | null;
}

export interface PlanNodeDTO {
  id: string;
  node_type: string;
  operator_name: string;
  details: Record<string, any>;
  estimated_rows: number;
  estimated_cost: number;
  cost_breakdown?: {
    io_cost: number;
    cpu_cost: number;
    memory_cost: number;
    total_cost: number;
  } | null;
  children: PlanNodeDTO[];
  actual_rows?: number | null;
  actual_time_ms?: number | null;
}

export interface RewriteStepDTO {
  rule_name: string;
  description: string;
  before_summary: string;
  after_summary: string;
  nodes_affected: string[];
}

export interface PlanCostBreakdown {
  io_cost: number;
  cpu_cost: number;
  memory_cost: number;
  total_cost: number;
}

export interface AlgorithmResultDTO {
  algorithm_name: string;
  execution_plan: PlanNodeDTO;
  estimated_cost: number;
  cost_breakdown: PlanCostBreakdown;
  optimization_time_ms: number;
  states_or_plans_explored: number;
  branches_pruned?: number;
  estimated_cardinality: number;
  join_order: string[];
  access_methods: Record<string, string>;
}

export interface OptimizationComparisonResponse {
  query_sql: string;
  normalized_fingerprint: string;
  cache_hit: boolean;
  original_logical_plan: PlanNodeDTO;
  rewritten_logical_plan: PlanNodeDTO;
  rewrite_steps: RewriteStepDTO[];
  algorithms: {
    dynamic_programming: AlgorithmResultDTO;
    greedy: AlgorithmResultDTO;
    branch_and_bound: AlgorithmResultDTO;
    [key: string]: AlgorithmResultDTO;
  };
  best_algorithm: string;
  optimality_gap_percent: Record<string, number>;
  explanation: string;
}

export interface ExecutionMetricDTO {
  estimated_rows: number;
  actual_rows: number;
  q_error: number;
  estimated_cost: number;
  actual_time_ms: number;
  actual_planning_time_ms?: number | null;
  cache_status: string;
  engine_used: string;
}

export interface QueryExecutionResponse {
  status: string;
  sql: string;
  row_count: number;
  columns: string[];
  rows: any[][];
  execution_plan_with_metrics: PlanNodeDTO;
  metrics: ExecutionMetricDTO;
  raw_postgres_explain?: Record<string, any> | null;
}

export interface ColumnStatDTO {
  column_name: string;
  data_type: string;
  distinct_values: number;
  null_fraction: number;
  min_value?: string | null;
  max_value?: string | null;
  has_index: boolean;
  index_name?: string | null;
  index_type?: string | null;
}

export interface TableStatDTO {
  table_name: string;
  row_count: number;
  page_count: number;
  average_row_width_bytes: number;
  columns: Record<string, ColumnStatDTO>;
  indexes: string[];
}

export interface CatalogSchemaResponse {
  tables: Record<string, TableStatDTO>;
  total_tables: number;
}

export interface BenchmarkRunPoint {
  query_name: string;
  num_tables: number;
  num_joins: number;
  algorithm: string;
  optimization_time_ms: number;
  states_explored: number;
  branches_pruned: number;
  estimated_cost: number;
  estimated_rows: number;
  actual_execution_time_ms?: number | null;
  actual_rows?: number | null;
  q_error?: number | null;
}

export interface BenchmarkResponse {
  summary: {
    total_queries_benchmarked: number;
    scale_factor_tuples: number;
    avg_optimization_time_ms: Record<string, number>;
    total_data_points: number;
  };
  data_points: BenchmarkRunPoint[];
}

export interface CacheEntryDTO {
  fingerprint: string;
  sql_template: string;
  created_at: string;
  hits: number;
  cost: number;
  best_algorithm: string;
}

export interface CacheStatusResponse {
  total_entries: number;
  max_size: number;
  hits: number;
  misses: number;
  hit_rate_percent: number;
  entries: CacheEntryDTO[];
}

export interface WorkloadItem {
  id: string;
  name: string;
  description: string;
  difficulty: string;
  sql: string;
}

export interface DatabaseInfoDTO {
  db_id: string;
  name: string;
  description: string;
  is_custom: boolean;
  is_active: boolean;
  table_count: number;
  tables: string[];
  schema_ddl?: string;
}

