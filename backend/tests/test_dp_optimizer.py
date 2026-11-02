"""
Unit tests for Dynamic Programming, Greedy, and Branch & Bound Optimizers
"""
from app.cost.cost_model import CostModel
from app.optimizer.branch_and_bound import BranchAndBoundOptimizer
from app.optimizer.comparison import AlgorithmComparator
from app.optimizer.dynamic_programming import DynamicProgrammingOptimizer
from app.optimizer.greedy import GreedyOptimizer
from app.parser.sql_parser import SQLParser
from app.statistics.mock_catalog import build_default_catalog

SAMPLE_QUERY = """
SELECT s.name, c.title, e.grade
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id
WHERE s.gpa >= 3.5;
"""

def test_dp_optimizer():
    catalog = build_default_catalog(scale=1000)
    cost_model = CostModel()
    parsed = SQLParser.parse(SAMPLE_QUERY)

    dp_opt = DynamicProgrammingOptimizer(catalog, cost_model)
    res = dp_opt.optimize(parsed)

    assert res.algorithm_name == "Dynamic Programming"
    assert res.estimated_cost > 0
    assert res.states_or_plans_explored > 0
    assert len(res.join_order) == 3

def test_greedy_optimizer():
    catalog = build_default_catalog(scale=1000)
    cost_model = CostModel()
    parsed = SQLParser.parse(SAMPLE_QUERY)

    greedy_opt = GreedyOptimizer(catalog, cost_model)
    res = greedy_opt.optimize(parsed)

    assert res.algorithm_name == "Greedy"
    assert res.estimated_cost > 0
    assert len(res.join_order) == 3

def test_branch_and_bound_optimizer():
    catalog = build_default_catalog(scale=1000)
    cost_model = CostModel()
    parsed = SQLParser.parse(SAMPLE_QUERY)

    bnb_opt = BranchAndBoundOptimizer(catalog, cost_model)
    res = bnb_opt.optimize(parsed)

    assert res.algorithm_name == "Branch & Bound"
    assert res.estimated_cost > 0
    assert res.states_or_plans_explored > 0
    assert len(res.join_order) == 3

def test_algorithm_comparator():
    catalog = build_default_catalog(scale=1000)
    cost_model = CostModel()
    parsed = SQLParser.parse(SAMPLE_QUERY)

    results, best_algo, gaps = AlgorithmComparator.compare_all(parsed, catalog, cost_model)
    assert "dynamic_programming" in results
    assert "greedy" in results
    assert "branch_and_bound" in results
    assert best_algo in results
