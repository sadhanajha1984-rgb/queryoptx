"""
Unit tests for Cost Model and Cardinality Estimator
"""
from app.cost.cost_model import CostBreakdown, CostModel
from app.parser.ast_models import ExpressionInternal, JoinInternal
from app.statistics.cardinality_estimator import CardinalityEstimator
from app.statistics.mock_catalog import build_default_catalog

def test_cost_model_scans():
    cm = CostModel()
    catalog = build_default_catalog(scale=1000)
    stud_stat = catalog.get_table("students")
    assert stud_stat is not None

    seq_cost = cm.cost_seq_scan(stud_stat, filter_selectivity=1.0)
    assert seq_cost.total_cost > 0
    assert seq_cost.io_cost > 0
    assert seq_cost.cpu_cost > 0

    idx_cost = cm.cost_index_scan(stud_stat, filter_selectivity=0.01)
    assert idx_cost.total_cost > 0

def test_cost_model_joins():
    cm = CostModel()
    left_c = CostBreakdown(10.0, 5.0, 0.0, 15.0)
    right_c = CostBreakdown(20.0, 10.0, 0.0, 30.0)

    hash_c = cm.cost_hash_join(left_c, 100.0, right_c, 500.0)
    assert hash_c.total_cost > 0
    assert hash_c.memory_cost > 0

    nl_c = cm.cost_nested_loop_join(left_c, 100.0, right_c, 500.0)
    assert nl_c.total_cost > 0

    merge_c = cm.cost_merge_join(left_c, 100.0, right_c, 500.0)
    assert merge_c.total_cost > 0

def test_cardinality_estimation():
    catalog = build_default_catalog(scale=1000)
    pred = ExpressionInternal(left="students.department", operator="=", right="'Computer Science'", raw_sql="department = 'Computer Science'", table_affinity="students")
    sel = CardinalityEstimator.estimate_filter_selectivity(pred, catalog)
    assert 0.0 < sel <= 1.0

    join_info = JoinInternal("students", "enrollments", "student_id", "student_id", "INNER", "s.student_id = e.student_id")
    join_card = CardinalityEstimator.estimate_join_cardinality("students", 1000.0, "enrollments", 5000.0, join_info, catalog)
    assert join_card > 0
