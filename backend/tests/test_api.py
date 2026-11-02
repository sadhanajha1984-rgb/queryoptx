"""
Integration tests for FastAPI endpoints
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

def test_analyze_endpoint():
    sql = "SELECT s.name, s.gpa FROM students s WHERE s.gpa > 3.0;"
    res = client.post("/api/query/analyze", json={"sql": sql})
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert len(data["tables"]) == 1

def test_optimize_endpoint():
    sql = "SELECT s.name, d.dept_name FROM students s JOIN departments d ON s.department = d.dept_name;"
    res = client.post("/api/query/optimize", json={"sql": sql, "use_cache": False})
    assert res.status_code == 200
    data = res.json()
    assert "algorithms" in data
    assert "dynamic_programming" in data["algorithms"]
    assert "greedy" in data["algorithms"]
    assert "branch_and_bound" in data["algorithms"]
    assert data["original_logical_plan"] is not None
    assert data["rewritten_logical_plan"] is not None

def test_execute_endpoint():
    sql = "SELECT s.name, s.department FROM students s WHERE s.department = 'Computer Science';"
    res = client.post("/api/query/execute", json={"sql": sql})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["row_count"] >= 0
    assert "metrics" in data
    assert data["metrics"]["q_error"] >= 1.0

def test_statistics_endpoint():
    res = client.get("/api/statistics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_tables"] > 0

def test_workloads_endpoint():
    res = client.get("/api/workloads")
    assert res.status_code == 200
    assert len(res.json()) >= 4
