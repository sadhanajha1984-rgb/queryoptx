"""
Unit tests for Query Rewrite Engine (Predicate & Projection Pushdown)
"""
from app.parser.sql_parser import SQLParser
from app.rewriter.rewrite_engine import QueryRewriteEngine
from app.statistics.mock_catalog import build_default_catalog

def test_predicate_pushdown():
    sql = """
    SELECT s.name, e.grade
    FROM students s
    JOIN enrollments e ON s.student_id = e.student_id
    WHERE s.department = 'Computer Science';
    """
    catalog = build_default_catalog(scale=1000)
    parsed = SQLParser.parse(sql)
    rewritten_plan, rewrites = QueryRewriteEngine.apply_rewrites(parsed, catalog)

    assert len(rewrites) >= 1
    rule_names = [r.rule_name for r in rewrites]
    assert "Predicate Pushdown" in rule_names
