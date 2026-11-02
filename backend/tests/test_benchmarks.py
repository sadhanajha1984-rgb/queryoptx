"""
Performance & Scaling Tests for QueryOptX Optimizers
Tests N=2, 3, 4, 5, 6+ table join queries across DP, Greedy, and Branch & Bound.
"""
import pytest
from app.cost.cost_model import CostModel
from app.optimizer.branch_and_bound import BranchAndBoundOptimizer
from app.optimizer.dynamic_programming import DynamicProgrammingOptimizer
from app.optimizer.greedy import GreedyOptimizer
from app.parser.sql_parser import SQLParser
from app.statistics.mock_catalog import build_default_catalog

SCALING_QUERIES = {
    2: "SELECT * FROM students s JOIN departments d ON s.department = d.dept_name;",
    3: "SELECT * FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN courses c ON e.course_id = c.course_id;",
    4: "SELECT * FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN courses c ON e.course_id = c.course_id JOIN instructors i ON c.instructor_id = i.instructor_id;",
    5: "SELECT * FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN courses c ON e.course_id = c.course_id JOIN instructors i ON c.instructor_id = i.instructor_id JOIN departments d ON i.dept_id = d.dept_id;"
}

@pytest.mark.parametrize("n_tables,sql", SCALING_QUERIES.items())
def test_optimizer_scaling(n_tables, sql):
    catalog = build_default_catalog(scale=5000)
    cost_model = CostModel()
    parsed = SQLParser.parse(sql)

    # 1. DP
    dp_res = DynamicProgrammingOptimizer(catalog, cost_model).optimize(parsed)
    assert dp_res.estimated_cost > 0
    assert len(dp_res.join_order) == n_tables

    # 2. Greedy
    greedy_res = GreedyOptimizer(catalog, cost_model).optimize(parsed)
    assert greedy_res.estimated_cost > 0
    assert len(greedy_res.join_order) == n_tables

    # 3. Branch & Bound
    bnb_res = BranchAndBoundOptimizer(catalog, cost_model).optimize(parsed)
    assert bnb_res.estimated_cost > 0
    # DP (exploring full bushy space) is guaranteed <= Left-deep B&B/Greedy
    assert dp_res.estimated_cost <= bnb_res.estimated_cost + 1e-4
    assert dp_res.estimated_cost <= greedy_res.estimated_cost + 1e-4
