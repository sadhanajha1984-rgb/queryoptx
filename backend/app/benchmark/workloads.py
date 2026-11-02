"""
Predefined Query Workloads for QueryOptX
"""
from typing import Dict, List

PREDEFINED_WORKLOADS: List[Dict[str, str]] = [
    {
        "id": "q1_simple_2table",
        "name": "2-Table Filtered Join (Academic)",
        "description": "Inner join between students and departments with GPA filter and department projection.",
        "difficulty": "Simple (N=2)",
        "sql": """SELECT s.name, s.gpa, d.dept_name, d.building
FROM students s
JOIN departments d ON s.department = d.dept_name
WHERE s.gpa >= 3.50;"""
    },
    {
        "id": "q2_medium_3table",
        "name": "3-Table Student Enrollments & Courses",
        "description": "3-table join joining students, enrollments, and courses for a specific semester.",
        "difficulty": "Medium (N=3)",
        "sql": """SELECT s.name, c.title, e.grade, e.year
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id
WHERE e.semester = 'Fall' AND s.department = 'Computer Science';"""
    },
    {
        "id": "q3_complex_4table",
        "name": "4-Table University Star Query",
        "description": "4-way join across Students, Enrollments, Courses, and Instructors.",
        "difficulty": "Complex (N=4)",
        "sql": """SELECT s.name, c.title, i.name AS instructor_name, e.grade
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id
JOIN instructors i ON c.instructor_id = i.instructor_id
WHERE e.grade = 'A' AND i.salary > 100000;"""
    },
    {
        "id": "q4_multijoin_5table",
        "name": "5-Table Complete University Relational Pipeline",
        "description": "5-way join spanning Students, Enrollments, Courses, Instructors, and Departments with aggregation.",
        "difficulty": "High Complexity (N=5)",
        "sql": """SELECT d.dept_name, c.title, i.name AS prof, s.name AS student
FROM departments d
JOIN instructors i ON d.dept_id = i.dept_id
JOIN courses c ON c.dept_id = d.dept_id AND c.instructor_id = i.instructor_id
JOIN enrollments e ON e.course_id = c.course_id
JOIN students s ON s.student_id = e.student_id
WHERE d.budget >= 300000;"""
    },
    {
        "id": "q5_ecommerce_5table",
        "name": "5-Table E-Commerce Star Schema",
        "description": "High-volume retail join across Customers, Orders, Order Items, Products, and Categories.",
        "difficulty": "E-Commerce Star (N=5)",
        "sql": """SELECT c.name, o.order_date, p.product_name, cat.category_name, oi.quantity, oi.unit_price
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories cat ON p.category_id = cat.category_id
WHERE c.loyalty_tier = 'Gold' AND p.price > 100.00;"""
    }
]
