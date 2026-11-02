# QueryOptX REST API Documentation

Base URL: `http://localhost:8000/api`

---

## 1. Query Analysis & Optimization

### `POST /api/query/analyze`
Parses SQL query into AST, validates safety, and extracts tables, joins, predicates, and projections.

**Request:**
```json
{
  "sql": "SELECT s.name, s.gpa FROM students s WHERE s.gpa >= 3.50;"
}
```

**Response:**
```json
{
  "is_valid": true,
  "query_type": "SELECT",
  "tables": [{ "name": "students", "alias": "s" }],
  "projections": ["name", "gpa"],
  "predicates": [
    {
      "table": "students",
      "operator": ">=",
      "value": "3.50",
      "raw_expression": "s.gpa >= 3.50",
      "is_join_predicate": false
    }
  ],
  "joins": [],
  "group_by": [],
  "order_by": [],
  "has_aggregates": false,
  "ast_json": { "type": "Select", "tables": [{ "name": "students", "alias": "s" }] }
}
```

---

### `POST /api/query/optimize`
Runs the complete optimization pipeline: Query Rewrites (Predicate/Projection pushdown), Dynamic Programming, Greedy, and Branch & Bound.

**Request:**
```json
{
  "sql": "SELECT s.name, c.title, e.grade FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN courses c ON e.course_id = c.course_id WHERE s.department = 'Computer Science';",
  "use_cache": true
}
```

**Response Structure:**
```json
{
  "query_sql": "...",
  "normalized_fingerprint": "a3f89b1c2e4d5678",
  "cache_hit": false,
  "original_logical_plan": { "id": "...", "node_type": "Project", "children": [...] },
  "rewritten_logical_plan": { "id": "...", "node_type": "Project", "children": [...] },
  "rewrite_steps": [
    {
      "rule_name": "Predicate Pushdown",
      "description": "Pushed single-table filtering predicates below join tree...",
      "before_summary": "...",
      "after_summary": "...",
      "nodes_affected": ["s"]
    }
  ],
  "algorithms": {
    "dynamic_programming": {
      "algorithm_name": "Dynamic Programming",
      "estimated_cost": 133.05,
      "cost_breakdown": { "io_cost": 45.0, "cpu_cost": 88.05, "memory_cost": 0.0, "total_cost": 133.05 },
      "optimization_time_ms": 1.25,
      "states_or_plans_explored": 12,
      "join_order": ["students", "enrollments", "courses"]
    },
    "greedy": { "algorithm_name": "Greedy", "estimated_cost": 145.20, "optimization_time_ms": 0.22 },
    "branch_and_bound": { "algorithm_name": "Branch & Bound", "estimated_cost": 133.05, "branches_pruned": 8 }
  },
  "best_algorithm": "dynamic_programming",
  "optimality_gap_percent": { "dynamic_programming": 0.0, "greedy": 9.13, "branch_and_bound": 0.0 },
  "explanation": "..."
}
```

---

### `POST /api/query/execute`
Safely executes read-only query against database and returns results, runtime, and Q-Error.

**Response Structure:**
```json
{
  "status": "success",
  "row_count": 2,
  "columns": ["name", "title", "grade"],
  "rows": [["Alice Johnson", "Intro to Algorithms", "A"], ["Alice Johnson", "Database Systems", "A"]],
  "metrics": {
    "estimated_rows": 2.5,
    "actual_rows": 2,
    "q_error": 1.25,
    "estimated_cost": 133.05,
    "actual_time_ms": 0.85,
    "cache_status": "Simulated Engine Execution (PostgreSQL offline)",
    "engine_used": "QueryOptX In-Memory Simulation Engine"
  }
}
```

---

## 2. Database Statistics & Benchmarks

### `GET /api/statistics`
Returns all tables, row counts, page counts, and column metadata.

### `GET /api/statistics/{table}`
Returns detailed column statistics, distinct counts ($N_{\text{distinct}}$), and index coverage for a single relation.

### `POST /api/query/benchmark`
Runs automated scalability benchmarks across $N=2 \dots 5+$ table join workloads.

### `GET /api/cache`
Inspects active cached query fingerprints, hit rate, and cached plan costs.

### `POST /api/cache/clear`
Clears in-memory LRU plan cache.

### `GET /api/workloads`
Returns predefined sample query workloads for demonstration.

### `GET /api/health`
Health check endpoint.
