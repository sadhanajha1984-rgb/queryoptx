"""
QueryOptX Benchmark Synthetic Dataset Generator
Generates realistic university and e-commerce scale datasets (10K, 100K, 1M rows)
Can output raw SQL or populate PostgreSQL directly.
"""
import random
import sys
from datetime import datetime, timedelta

FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Evan", "Fiona", "George", "Hannah", "Ivan", "Julia", "Kevin", "Laura", "Michael", "Nadia", "Oliver", "Priya", "Quentin", "Rachel", "Sam", "Tara"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
DEPARTMENTS = ["Computer Science", "Electrical Engineering", "Mathematics", "Physics", "Mechanical Engineering", "Civil Engineering", "Biotechnology", "Economics"]
COUNTRIES = ["USA", "Germany", "India", "Japan", "UK", "Canada", "France", "Australia", "Brazil", "Singapore"]
CITIES = ["New York", "San Francisco", "London", "Berlin", "Tokyo", "Bangalore", "Toronto", "Sydney", "Paris", "Sao Paulo"]
TIERS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"]
STATUSES = ["Completed", "Shipped", "Pending", "Cancelled", "Refunded"]
GRADES = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "D", "F"]

def generate_dataset_sql(scale: int = 10000, output_file: str = "dataset.sql"):
    print(f"Generating synthetic dataset with scale factor {scale} into {output_file}...")
    num_students = scale
    num_departments = 10
    num_instructors = max(50, scale // 100)
    num_courses = max(100, scale // 50)
    num_enrollments = scale * 5

    num_categories = 50
    num_products = max(200, scale // 10)
    num_customers = scale
    num_orders = scale * 2
    num_order_items = scale * 6

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("-- QueryOptX Generated Benchmark Scale Dataset\n")
        f.write("BEGIN;\n\n")

        # 1. Departments
        f.write("-- Departments\n")
        for i in range(1, num_departments + 1):
            dept_name = f"Dept_{i}_{DEPARTMENTS[(i-1) % len(DEPARTMENTS)]}"
            building = f"Hall_{i}"
            budget = random.randint(100000, 2000000)
            f.write(f"INSERT INTO departments (dept_id, dept_name, building, budget) VALUES ({i}, '{dept_name}', '{building}', {budget}) ON CONFLICT DO NOTHING;\n")

        # 2. Instructors
        f.write("\n-- Instructors\n")
        for i in range(1, num_instructors + 1):
            name = f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            dept_id = random.randint(1, num_departments)
            salary = round(random.uniform(70000, 180000), 2)
            hire_date = (datetime(2010, 1, 1) + timedelta(days=random.randint(0, 5000))).strftime("%Y-%m-%d")
            f.write(f"INSERT INTO instructors (instructor_id, name, dept_id, salary, hire_date) VALUES ({i}, '{name}', {dept_id}, {salary}, '{hire_date}') ON CONFLICT DO NOTHING;\n")

        # 3. Students
        f.write("\n-- Students\n")
        for i in range(1, num_students + 1):
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            email = f"student_{i}@univ.edu"
            dept = random.choice(DEPARTMENTS)
            gpa = round(random.uniform(2.0, 4.0), 2)
            tot_cred = random.randint(0, 120)
            year = random.randint(2020, 2026)
            f.write(f"INSERT INTO students (student_id, name, email, department, gpa, tot_cred, enrollment_year) VALUES ({i}, '{name}', '{email}', '{dept}', {gpa}, {tot_cred}, {year}) ON CONFLICT DO NOTHING;\n")

        # 4. Courses
        f.write("\n-- Courses\n")
        for i in range(1, num_courses + 1):
            code = f"CRS{i:04d}"
            title = f"Course {i} Advanced Topics"
            dept_id = random.randint(1, num_departments)
            credits = random.choice([2, 3, 4])
            instructor_id = random.randint(1, num_instructors)
            f.write(f"INSERT INTO courses (course_id, course_code, title, dept_id, credits, instructor_id) VALUES ({i}, '{code}', '{title}', {dept_id}, {credits}, {instructor_id}) ON CONFLICT DO NOTHING;\n")

        # 5. Enrollments
        f.write("\n-- Enrollments\n")
        for i in range(1, num_enrollments + 1):
            student_id = random.randint(1, num_students)
            course_id = random.randint(1, num_courses)
            sem = random.choice(["Fall", "Spring", "Summer"])
            year = random.randint(2021, 2026)
            grade = random.choice(GRADES)
            gp = {"A+": 4.0, "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7, "C+": 2.3, "C": 2.0, "D": 1.0, "F": 0.0}[grade]
            f.write(f"INSERT INTO enrollments (enrollment_id, student_id, course_id, semester, year, grade, grade_point) VALUES ({i}, {student_id}, {course_id}, '{sem}', {year}, '{grade}', {gp}) ON CONFLICT DO NOTHING;\n")

        f.write("\nCOMMIT;\n")
    print(f"Done generating {output_file}.")

if __name__ == "__main__":
    scale_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    out_arg = sys.argv[2] if len(sys.argv) > 2 else "database/sample_benchmark.sql"
    generate_dataset_sql(scale=scale_arg, output_file=out_arg)
