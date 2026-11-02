"""
Unit tests for SQL Parser and Safety Validator
"""
import pytest
from app.parser.sql_parser import SQLParser
from app.parser.validator import validate_sql_safety

def test_sql_safety_valid():
    safe_sql = "SELECT s.name, s.gpa FROM students s WHERE s.gpa > 3.5;"
    is_safe, err = validate_sql_safety(safe_sql)
    assert is_safe is True
    assert err == ""

def test_sql_safety_reject_destructive():
    destructive_sqls = [
        "DROP TABLE students;",
        "DELETE FROM students WHERE id = 1;",
        "UPDATE students SET gpa = 4.0;",
        "INSERT INTO students VALUES (1, 'Eve');",
        "TRUNCATE TABLE enrollments;",
        "ALTER TABLE students ADD COLUMN phone VARCHAR;"
    ]
    for sql in destructive_sqls:
        is_safe, err = validate_sql_safety(sql)
        assert is_safe is False
        assert "prohibited" in err or "Only SELECT" in err

def test_parser_basic_select():
    sql = "SELECT s.name, s.department FROM students s WHERE s.department = 'Computer Science';"
    parsed = SQLParser.parse(sql)
    assert len(parsed.tables) == 1
    assert parsed.tables[0].name.lower() == "students"
    assert len(parsed.predicates) == 1
    assert parsed.predicates[0].operator == "="
    assert len(parsed.projections) == 2

def test_parser_multi_join():
    sql = """
    SELECT s.name, c.title, e.grade
    FROM students s
    JOIN enrollments e ON s.student_id = e.student_id
    JOIN courses c ON e.course_id = c.course_id
    WHERE e.grade = 'A';
    """
    parsed = SQLParser.parse(sql)
    assert len(parsed.tables) == 3
    assert len(parsed.joins) == 2
    assert len(parsed.predicates) == 1
    assert parsed.predicates[0].operator == "="
