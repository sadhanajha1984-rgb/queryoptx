"""
Query Executor Module
Executes validated read-only SELECT queries with timeouts and limit enforcement.
Supports live PostgreSQL execution and high-fidelity embedded SQLite fallback.
"""
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings
from app.execution.metrics_analyzer import MetricsAnalyzer
from app.parser.validator import validate_sql_safety
from app.planner.tree_models import PlanNode
from app.schemas.api_models import ExecutionMetricDTO, QueryExecutionResponse

class QueryExecutor:
    _sqlite_conn: Optional[sqlite3.Connection] = None

    @classmethod
    def execute_query(
        cls,
        sql: str,
        execution_plan: PlanNode,
        db_id: Optional[str] = None
    ) -> QueryExecutionResponse:
        is_safe, err_msg = validate_sql_safety(sql)
        if not is_safe:
            raise ValueError(f"SQL Safety Error: {err_msg}")

        from app.statistics.database_manager import DatabaseManager
        db_mgr = DatabaseManager.get_instance()
        target_db = db_mgr.databases.get(db_id) if db_id else db_mgr.get_active_db()

        # If custom database, execute directly on target_db SQLite instance
        if target_db and target_db.is_custom:
            return cls._execute_custom_sqlite(sql, execution_plan, target_db)

        # Otherwise try PostgreSQL first
        try:
            return cls._execute_postgres(sql, execution_plan)
        except Exception as pg_err:
            # Fall back to embedded simulation SQLite engine
            return cls._execute_sqlite_simulation(sql, execution_plan, str(pg_err), target_db=target_db)

    @classmethod
    def _execute_custom_sqlite(
        cls,
        sql: str,
        execution_plan: PlanNode,
        target_db
    ) -> QueryExecutionResponse:
        cur = target_db.conn.cursor()
        start_t = time.perf_counter()
        try:
            cur.execute(sql)
            rows = cur.fetchmany(settings.MAX_RESULT_ROWS)
            exec_time_ms = (time.perf_counter() - start_t) * 1000.0
            columns = [d[0] for d in cur.description] if cur.description else []
            formatted_rows = [list(r) for r in rows]
        except Exception as sql_err:
            raise ValueError(f"Execution Error in custom database '{target_db.name}': {str(sql_err)}")

        row_count = len(formatted_rows)
        q_err = MetricsAnalyzer.calculate_q_error(execution_plan.estimated_rows, row_count)
        annotated_plan = MetricsAnalyzer.annotate_plan_tree_with_actuals(execution_plan, row_count, exec_time_ms)

        metric_dto = ExecutionMetricDTO(
            estimated_rows=execution_plan.estimated_rows,
            actual_rows=row_count,
            q_error=q_err,
            estimated_cost=execution_plan.estimated_cost,
            actual_time_ms=round(exec_time_ms, 3),
            actual_planning_time_ms=0.10,
            cache_status=f"Executed on Custom DB: {target_db.name}",
            engine_used=f"User Database Engine ({target_db.name})"
        )

        return QueryExecutionResponse(
            status="success",
            sql=sql,
            row_count=row_count,
            columns=columns,
            rows=formatted_rows,
            execution_plan_with_metrics=annotated_plan.to_dto(),
            metrics=metric_dto,
            raw_postgres_explain={"note": "Executed against user custom database instance", "database": target_db.name}
        )

    @classmethod
    def _execute_postgres(
        cls,
        sql: str,
        execution_plan: PlanNode
    ) -> QueryExecutionResponse:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            dbname=settings.POSTGRES_DB,
            connect_timeout=2
        )
        conn.set_session(readonly=True, autocommit=True)

        explain_json = None
        planning_time_ms = None

        with conn.cursor() as cur:
            # Set statement timeout
            timeout_ms = int(settings.MAX_EXECUTION_TIME_SECONDS * 1000)
            cur.execute(f"SET statement_timeout = {timeout_ms};")

            # Run EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            try:
                cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}")
                explain_raw = cur.fetchone()[0]
                if explain_raw and len(explain_raw) > 0:
                    explain_json = explain_raw[0]
                    planning_time_ms = explain_json.get("Planning Time", 0.0)
            except Exception:
                pass

            # Execute query and fetch results up to MAX_RESULT_ROWS
            start_t = time.perf_counter()
            cur.execute(sql)
            rows = cur.fetchmany(settings.MAX_RESULT_ROWS)
            exec_time_ms = (time.perf_counter() - start_t) * 1000.0

            columns = [desc[0] for desc in cur.description] if cur.description else []
            formatted_rows = [list(r) for r in rows]

        conn.close()

        row_count = len(formatted_rows)
        q_err = MetricsAnalyzer.calculate_q_error(execution_plan.estimated_rows, row_count)
        annotated_plan = MetricsAnalyzer.annotate_plan_tree_with_actuals(execution_plan, row_count, exec_time_ms)

        metric_dto = ExecutionMetricDTO(
            estimated_rows=execution_plan.estimated_rows,
            actual_rows=row_count,
            q_error=q_err,
            estimated_cost=execution_plan.estimated_cost,
            actual_time_ms=round(exec_time_ms, 3),
            actual_planning_time_ms=planning_time_ms,
            cache_status="Executed on PostgreSQL",
            engine_used="PostgreSQL Live"
        )

        return QueryExecutionResponse(
            status="success",
            sql=sql,
            row_count=row_count,
            columns=columns,
            rows=formatted_rows,
            execution_plan_with_metrics=annotated_plan.to_dto(),
            metrics=metric_dto,
            raw_postgres_explain=explain_json
        )

    @classmethod
    def _execute_sqlite_simulation(
        cls,
        sql: str,
        execution_plan: PlanNode,
        pg_err_msg: str,
        target_db = None
    ) -> QueryExecutionResponse:
        conn = target_db.conn if target_db else cls._get_sqlite_db()
        cur = conn.cursor()

        start_t = time.perf_counter()
        try:
            cur.execute(sql)
            rows = cur.fetchmany(settings.MAX_RESULT_ROWS)
            exec_time_ms = (time.perf_counter() - start_t) * 1000.0
            columns = [d[0] for d in cur.description] if cur.description else []
            formatted_rows = [list(r) for r in rows]
        except Exception as sql_err:
            raise ValueError(f"Execution Error: {str(sql_err)}")

        row_count = len(formatted_rows)
        q_err = MetricsAnalyzer.calculate_q_error(execution_plan.estimated_rows, row_count)
        annotated_plan = MetricsAnalyzer.annotate_plan_tree_with_actuals(execution_plan, row_count, exec_time_ms)

        metric_dto = ExecutionMetricDTO(
            estimated_rows=execution_plan.estimated_rows,
            actual_rows=row_count,
            q_error=q_err,
            estimated_cost=execution_plan.estimated_cost,
            actual_time_ms=round(exec_time_ms, 3),
            actual_planning_time_ms=0.15,
            cache_status="Simulated Engine Execution (PostgreSQL offline)",
            engine_used="QueryOptX In-Memory Simulation Engine"
        )

        return QueryExecutionResponse(
            status="success",
            sql=sql,
            row_count=row_count,
            columns=columns,
            rows=formatted_rows,
            execution_plan_with_metrics=annotated_plan.to_dto(),
            metrics=metric_dto,
            raw_postgres_explain={"note": "Simulated engine execution", "pg_connection_status": pg_err_msg}
        )

    @classmethod
    def _get_sqlite_db(cls) -> sqlite3.Connection:
        if cls._sqlite_conn is not None:
            return cls._sqlite_conn

        conn = sqlite3.connect(":memory:", check_same_thread=False)
        cur = conn.cursor()

        # Build schema & seed tables in memory
        cur.executescript("""
            CREATE TABLE departments (
                dept_id INTEGER PRIMARY KEY,
                dept_name TEXT NOT NULL UNIQUE,
                building TEXT,
                budget REAL
            );

            CREATE TABLE instructors (
                instructor_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                dept_id INTEGER,
                salary REAL,
                hire_date TEXT
            );

            CREATE TABLE students (
                student_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                department TEXT,
                gpa REAL,
                tot_cred INTEGER,
                enrollment_year INTEGER
            );

            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY,
                course_code TEXT UNIQUE,
                title TEXT,
                dept_id INTEGER,
                credits INTEGER,
                instructor_id INTEGER
            );

            CREATE TABLE enrollments (
                enrollment_id INTEGER PRIMARY KEY,
                student_id INTEGER,
                course_id INTEGER,
                semester TEXT,
                year INTEGER,
                grade TEXT,
                grade_point REAL
            );

            CREATE TABLE categories (
                category_id INTEGER PRIMARY KEY,
                category_name TEXT,
                parent_category_id INTEGER
            );

            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT,
                category_id INTEGER,
                price REAL,
                stock_quantity INTEGER,
                rating REAL
            );

            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                country TEXT,
                city TEXT,
                loyalty_tier TEXT,
                created_at TEXT
            );

            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_date TEXT,
                status TEXT,
                total_amount REAL
            );

            CREATE TABLE order_items (
                item_id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                unit_price REAL,
                discount REAL
            );

            -- Sample Data
            INSERT INTO departments VALUES
            (1, 'Computer Science', 'Turing Hall', 500000.00),
            (2, 'Electrical Engineering', 'Maxwell Lab', 450000.00),
            (3, 'Mathematics', 'Euler Building', 300000.00),
            (4, 'Physics', 'Newton Center', 350000.00),
            (5, 'Mechanical Engineering', 'Carnot Wing', 400000.00);

            INSERT INTO instructors VALUES
            (1, 'Dr. Alan Turing', 1, 120000.00, '2015-08-15'),
            (2, 'Dr. Claude Shannon', 1, 115000.00, '2017-01-10'),
            (3, 'Dr. Nikola Tesla', 2, 110000.00, '2016-03-22'),
            (4, 'Dr. Emmy Noether', 3, 125000.00, '2014-09-01'),
            (5, 'Dr. Richard Feynman', 4, 130000.00, '2013-05-18');

            INSERT INTO students VALUES
            (101, 'Alice Johnson', 'alice@univ.edu', 'Computer Science', 3.90, 85, 2022),
            (102, 'Bob Smith', 'bob@univ.edu', 'Computer Science', 3.45, 60, 2023),
            (103, 'Charlie Brown', 'charlie@univ.edu', 'Electrical Engineering', 3.20, 90, 2021),
            (104, 'Diana Prince', 'diana@univ.edu', 'Mathematics', 3.95, 110, 2021),
            (105, 'Evan Wright', 'evan@univ.edu', 'Physics', 2.85, 45, 2024),
            (106, 'Fiona Gallagher', 'fiona@univ.edu', 'Computer Science', 3.75, 75, 2022),
            (107, 'George Clark', 'george@univ.edu', 'Mechanical Engineering', 3.10, 50, 2023),
            (108, 'Hannah Abbott', 'hannah@univ.edu', 'Mathematics', 3.65, 80, 2022);

            INSERT INTO courses VALUES
            (201, 'CS101', 'Intro to Algorithms', 1, 4, 1),
            (202, 'CS201', 'Database Systems', 1, 4, 2),
            (203, 'EE101', 'Circuits & Signals', 2, 3, 3),
            (204, 'MATH301', 'Linear Algebra', 3, 3, 4),
            (205, 'PHYS201', 'Quantum Mechanics', 4, 4, 5);

            INSERT INTO enrollments VALUES
            (1, 101, 201, 'Fall', 2023, 'A', 4.00),
            (2, 101, 202, 'Spring', 2024, 'A', 4.00),
            (3, 102, 201, 'Fall', 2023, 'B+', 3.50),
            (4, 102, 202, 'Spring', 2024, 'B', 3.00),
            (5, 103, 203, 'Fall', 2023, 'B', 3.00),
            (6, 104, 204, 'Spring', 2024, 'A+', 4.00),
            (7, 105, 205, 'Fall', 2024, 'C', 2.00),
            (8, 106, 201, 'Fall', 2023, 'A-', 3.70),
            (9, 106, 202, 'Spring', 2024, 'A', 4.00);

            INSERT INTO categories VALUES
            (1, 'Electronics', NULL),
            (2, 'Computers', 1),
            (3, 'Accessories', 1),
            (4, 'Books', NULL),
            (5, 'Textbooks', 4);

            INSERT INTO products VALUES
            (1001, 'Database Internals Book', 5, 59.99, 120, 4.9),
            (1002, 'Introduction to Algorithms (CLRS)', 5, 89.99, 85, 4.8),
            (1003, 'Ultra-wide Monitor 34"', 2, 499.99, 45, 4.7),
            (1004, 'Ergonomic Mechanical Keyboard', 3, 129.99, 210, 4.6),
            (1005, 'Wireless Noise-Canceling Headphones', 1, 249.99, 150, 4.5);

            INSERT INTO customers VALUES
            (501, 'Sarah Connor', 'sarah@skynet.com', 'USA', 'Los Angeles', 'Gold', '2023-01-10'),
            (502, 'John Doe', 'johndoe@gmail.com', 'USA', 'New York', 'Silver', '2023-02-14'),
            (503, 'Elena Rostova', 'elena@mail.ru', 'Germany', 'Berlin', 'Platinum', '2023-03-01'),
            (504, 'Kenji Sato', 'kenji@tokyo.jp', 'Japan', 'Tokyo', 'Gold', '2023-03-15'),
            (505, 'Priya Sharma', 'priya@tech.in', 'India', 'Bangalore', 'Diamond', '2023-04-20');

            INSERT INTO orders VALUES
            (8001, 501, '2024-01-15', 'Completed', 149.98),
            (8002, 502, '2024-02-10', 'Completed', 499.99),
            (8003, 503, '2024-02-18', 'Completed', 379.98),
            (8004, 504, '2024-03-01', 'Shipped', 129.99),
            (8005, 505, '2024-03-05', 'Completed', 749.98);

            INSERT INTO order_items VALUES
            (1, 8001, 1001, 1, 59.99, 0.0),
            (2, 8001, 1002, 1, 89.99, 0.0),
            (3, 8002, 1003, 1, 499.99, 0.0),
            (4, 8003, 1004, 1, 129.99, 0.0),
            (5, 8003, 1005, 1, 249.99, 0.0),
            (6, 8004, 1004, 1, 129.99, 0.0),
            (7, 8005, 1003, 1, 499.99, 0.0),
            (8, 8005, 1005, 1, 249.99, 0.0);
        """)
        conn.commit()
        cls._sqlite_conn = conn
        return conn
