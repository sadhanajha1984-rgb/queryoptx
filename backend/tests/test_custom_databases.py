"""
Tests for Multi-Database Management (User Custom Databases & Queries)
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_databases():
    res = client.get("/api/databases")
    assert res.status_code == 200
    dbs = res.json()
    assert len(dbs) >= 1
    default_db = next((d for d in dbs if d["db_id"] == "default_univ"), None)
    assert default_db is not None
    assert default_db["is_active"] is True

def test_create_and_query_custom_database():
    ddl = """
    CREATE TABLE employees (
        emp_id INTEGER PRIMARY KEY,
        emp_name TEXT,
        salary REAL,
        dept_id INTEGER
    );
    CREATE TABLE company_departments (
        dept_id INTEGER PRIMARY KEY,
        dept_title TEXT
    );
    CREATE INDEX idx_emp_salary ON employees(salary);
    INSERT INTO company_departments VALUES (1, 'R&D'), (2, 'Finance');
    INSERT INTO employees VALUES (101, 'Sonam', 95000.0, 1), (102, 'Alex', 82000.0, 1), (103, 'Maria', 78000.0, 2);
    """
    
    create_res = client.post("/api/databases/create", json={
        "name": "Enterprise HR DB",
        "description": "User custom company database",
        "ddl_sql": ddl
    })
    assert create_res.status_code == 200
    custom_db = create_res.json()
    db_id = custom_db["db_id"]
    assert "employees" in custom_db["tables"]
    assert "company_departments" in custom_db["tables"]

    # Verify statistics endpoint with db_id
    stats_res = client.get(f"/api/statistics?db_id={db_id}")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert "employees" in stats_data["tables"]
    emp_table = stats_data["tables"]["employees"]
    assert emp_table["row_count"] == 3
    assert emp_table["columns"]["salary"]["has_index"] is True

    # Optimize query on this user custom database
    query_sql = "SELECT e.emp_name, d.dept_title, e.salary FROM employees e JOIN company_departments d ON e.dept_id = d.dept_id WHERE e.salary > 80000.0;"
    opt_res = client.post("/api/query/optimize", json={
        "sql": query_sql,
        "db_id": db_id,
        "use_cache": False
    })
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert "algorithms" in opt_data
    assert "dynamic_programming" in opt_data["algorithms"]
    assert len(opt_data["algorithms"]["dynamic_programming"]["join_order"]) == 2

    # Execute query on this user custom database
    exec_res = client.post("/api/query/execute", json={
        "sql": query_sql,
        "db_id": db_id
    })
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "success"
    assert exec_data["row_count"] == 2  # Sonam (95k) and Alex (82k)
    assert any("Sonam" in str(row) for row in exec_data["rows"])

    # Clean up
    del_res = client.delete(f"/api/databases/{db_id}")
    assert del_res.status_code == 200

def test_add_table_to_custom_database_without_resetting_existing_tables():
    create_res = client.post("/api/databases/create", json={
        "name": "Incremental Schema DB",
        "description": "Verifies adding tables without replacing existing schema",
        "ddl_sql": "CREATE TABLE original_records (record_id INTEGER PRIMARY KEY, value TEXT);"
    })
    assert create_res.status_code == 200
    db_id = create_res.json()["db_id"]

    add_res = client.post("/api/databases/execute-ddl", json={
        "db_id": db_id,
        "ddl_sql": "CREATE TABLE additional_records (record_id INTEGER PRIMARY KEY, value TEXT);"
    })
    assert add_res.status_code == 200
    assert set(add_res.json()["tables"]) == {"original_records", "additional_records"}

    catalog_res = client.get(f"/api/statistics?db_id={db_id}")
    assert catalog_res.status_code == 200
    assert set(catalog_res.json()["tables"]) == {"original_records", "additional_records"}

    del_res = client.delete(f"/api/databases/{db_id}")
    assert del_res.status_code == 200
