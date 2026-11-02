"""
Default & Simulated Database Catalog for QueryOptX
Provides realistic statistics for academic university and e-commerce schemas.
"""
from app.statistics.stats_models import ColumnStatistics, DatabaseCatalog, TableStatistics

def build_default_catalog(scale: int = 10000) -> DatabaseCatalog:
    """
    Builds a realistic catalog at a given scale factor (e.g. 10,000 baseline rows).
    """
    cat = DatabaseCatalog()

    # 1. departments
    dept_rows = 10
    dept_pages = max(1, dept_rows // 50)
    cat.tables["departments"] = TableStatistics(
        name="departments",
        row_count=dept_rows,
        page_count=dept_pages,
        avg_row_width=120,
        indexes=["departments_pkey"],
        columns={
            "dept_id": ColumnStatistics("dept_id", "integer", distinct_values=dept_rows, has_index=True, index_name="departments_pkey"),
            "dept_name": ColumnStatistics("dept_name", "varchar", distinct_values=dept_rows, has_index=True, index_name="idx_departments_name"),
            "building": ColumnStatistics("building", "varchar", distinct_values=5, has_index=False),
            "budget": ColumnStatistics("budget", "numeric", distinct_values=10, min_value="100000", max_value="2000000", has_index=False)
        }
    )

    # 2. instructors
    inst_rows = max(50, scale // 100)
    inst_pages = max(2, (inst_rows * 100) // 8192)
    cat.tables["instructors"] = TableStatistics(
        name="instructors",
        row_count=inst_rows,
        page_count=inst_pages,
        avg_row_width=100,
        indexes=["instructors_pkey", "idx_instructors_dept"],
        columns={
            "instructor_id": ColumnStatistics("instructor_id", "integer", distinct_values=inst_rows, has_index=True, index_name="instructors_pkey"),
            "name": ColumnStatistics("name", "varchar", distinct_values=int(inst_rows * 0.95), has_index=False),
            "dept_id": ColumnStatistics("dept_id", "integer", distinct_values=dept_rows, has_index=True, index_name="idx_instructors_dept"),
            "salary": ColumnStatistics("salary", "numeric", distinct_values=int(inst_rows * 0.8), min_value="60000", max_value="180000", has_index=False),
            "hire_date": ColumnStatistics("hire_date", "date", distinct_values=int(inst_rows * 0.7), has_index=False)
        }
    )

    # 3. students
    stud_rows = scale
    stud_pages = max(5, (stud_rows * 150) // 8192)
    cat.tables["students"] = TableStatistics(
        name="students",
        row_count=stud_rows,
        page_count=stud_pages,
        avg_row_width=150,
        indexes=["students_pkey", "idx_students_dept", "idx_students_gpa", "idx_students_year"],
        columns={
            "student_id": ColumnStatistics("student_id", "integer", distinct_values=stud_rows, has_index=True, index_name="students_pkey"),
            "name": ColumnStatistics("name", "varchar", distinct_values=int(stud_rows * 0.9), has_index=False),
            "email": ColumnStatistics("email", "varchar", distinct_values=stud_rows, has_index=True, index_name="idx_students_email"),
            "department": ColumnStatistics("department", "varchar", distinct_values=dept_rows, has_index=True, index_name="idx_students_dept"),
            "gpa": ColumnStatistics("gpa", "numeric", distinct_values=200, min_value="2.00", max_value="4.00", has_index=True, index_name="idx_students_gpa"),
            "tot_cred": ColumnStatistics("tot_cred", "integer", distinct_values=120, min_value="0", max_value="140", has_index=False),
            "enrollment_year": ColumnStatistics("enrollment_year", "integer", distinct_values=6, min_value="2020", max_value="2026", has_index=True, index_name="idx_students_year")
        }
    )

    # 4. courses
    crs_rows = max(100, scale // 50)
    crs_pages = max(2, (crs_rows * 120) // 8192)
    cat.tables["courses"] = TableStatistics(
        name="courses",
        row_count=crs_rows,
        page_count=crs_pages,
        avg_row_width=120,
        indexes=["courses_pkey", "idx_courses_dept", "idx_courses_instructor"],
        columns={
            "course_id": ColumnStatistics("course_id", "integer", distinct_values=crs_rows, has_index=True, index_name="courses_pkey"),
            "course_code": ColumnStatistics("course_code", "varchar", distinct_values=crs_rows, has_index=True, index_name="idx_courses_code"),
            "title": ColumnStatistics("title", "varchar", distinct_values=crs_rows, has_index=False),
            "dept_id": ColumnStatistics("dept_id", "integer", distinct_values=dept_rows, has_index=True, index_name="idx_courses_dept"),
            "credits": ColumnStatistics("credits", "integer", distinct_values=4, min_value="1", max_value="4", has_index=False),
            "instructor_id": ColumnStatistics("instructor_id", "integer", distinct_values=inst_rows, has_index=True, index_name="idx_courses_instructor")
        }
    )

    # 5. enrollments
    enr_rows = scale * 5
    enr_pages = max(10, (enr_rows * 80) // 8192)
    cat.tables["enrollments"] = TableStatistics(
        name="enrollments",
        row_count=enr_rows,
        page_count=enr_pages,
        avg_row_width=80,
        indexes=["enrollments_pkey", "idx_enrollments_student", "idx_enrollments_course", "idx_enrollments_grade"],
        columns={
            "enrollment_id": ColumnStatistics("enrollment_id", "integer", distinct_values=enr_rows, has_index=True, index_name="enrollments_pkey"),
            "student_id": ColumnStatistics("student_id", "integer", distinct_values=stud_rows, has_index=True, index_name="idx_enrollments_student"),
            "course_id": ColumnStatistics("course_id", "integer", distinct_values=crs_rows, has_index=True, index_name="idx_enrollments_course"),
            "semester": ColumnStatistics("semester", "varchar", distinct_values=3, has_index=False),
            "year": ColumnStatistics("year", "integer", distinct_values=5, min_value="2021", max_value="2026", has_index=False),
            "grade": ColumnStatistics("grade", "varchar", distinct_values=10, has_index=True, index_name="idx_enrollments_grade"),
            "grade_point": ColumnStatistics("grade_point", "numeric", distinct_values=10, min_value="0.0", max_value="4.0", has_index=False)
        }
    )

    # 6. categories
    cat_rows = 50
    cat.tables["categories"] = TableStatistics(
        name="categories",
        row_count=cat_rows,
        page_count=1,
        avg_row_width=80,
        indexes=["categories_pkey"],
        columns={
            "category_id": ColumnStatistics("category_id", "integer", distinct_values=cat_rows, has_index=True, index_name="categories_pkey"),
            "category_name": ColumnStatistics("category_name", "varchar", distinct_values=cat_rows, has_index=False),
            "parent_category_id": ColumnStatistics("parent_category_id", "integer", distinct_values=10, null_fraction=0.2, has_index=False)
        }
    )

    # 7. products
    prod_rows = max(200, scale // 10)
    prod_pages = max(2, (prod_rows * 120) // 8192)
    cat.tables["products"] = TableStatistics(
        name="products",
        row_count=prod_rows,
        page_count=prod_pages,
        avg_row_width=120,
        indexes=["products_pkey", "idx_products_category", "idx_products_price"],
        columns={
            "product_id": ColumnStatistics("product_id", "integer", distinct_values=prod_rows, has_index=True, index_name="products_pkey"),
            "product_name": ColumnStatistics("product_name", "varchar", distinct_values=prod_rows, has_index=False),
            "category_id": ColumnStatistics("category_id", "integer", distinct_values=cat_rows, has_index=True, index_name="idx_products_category"),
            "price": ColumnStatistics("price", "numeric", distinct_values=int(prod_rows * 0.7), min_value="10.00", max_value="2000.00", has_index=True, index_name="idx_products_price"),
            "stock_quantity": ColumnStatistics("stock_quantity", "integer", distinct_values=100, min_value="0", max_value="500", has_index=False),
            "rating": ColumnStatistics("rating", "numeric", distinct_values=40, min_value="1.0", max_value="5.0", has_index=False)
        }
    )

    # 8. customers
    cust_rows = scale
    cust_pages = max(5, (cust_rows * 140) // 8192)
    cat.tables["customers"] = TableStatistics(
        name="customers",
        row_count=cust_rows,
        page_count=cust_pages,
        avg_row_width=140,
        indexes=["customers_pkey", "idx_customers_country", "idx_customers_tier"],
        columns={
            "customer_id": ColumnStatistics("customer_id", "integer", distinct_values=cust_rows, has_index=True, index_name="customers_pkey"),
            "name": ColumnStatistics("name", "varchar", distinct_values=int(cust_rows * 0.9), has_index=False),
            "email": ColumnStatistics("email", "varchar", distinct_values=cust_rows, has_index=True, index_name="idx_customers_email"),
            "country": ColumnStatistics("country", "varchar", distinct_values=15, has_index=True, index_name="idx_customers_country"),
            "city": ColumnStatistics("city", "varchar", distinct_values=50, has_index=False),
            "loyalty_tier": ColumnStatistics("loyalty_tier", "varchar", distinct_values=5, has_index=True, index_name="idx_customers_tier")
        }
    )

    # 9. orders
    ord_rows = scale * 2
    ord_pages = max(10, (ord_rows * 80) // 8192)
    cat.tables["orders"] = TableStatistics(
        name="orders",
        row_count=ord_rows,
        page_count=ord_pages,
        avg_row_width=80,
        indexes=["orders_pkey", "idx_orders_customer", "idx_orders_date", "idx_orders_status"],
        columns={
            "order_id": ColumnStatistics("order_id", "integer", distinct_values=ord_rows, has_index=True, index_name="orders_pkey"),
            "customer_id": ColumnStatistics("customer_id", "integer", distinct_values=cust_rows, has_index=True, index_name="idx_orders_customer"),
            "order_date": ColumnStatistics("order_date", "date", distinct_values=730, has_index=True, index_name="idx_orders_date"),
            "status": ColumnStatistics("status", "varchar", distinct_values=5, has_index=True, index_name="idx_orders_status"),
            "total_amount": ColumnStatistics("total_amount", "numeric", distinct_values=int(ord_rows * 0.6), min_value="10.00", max_value="5000.00", has_index=False)
        }
    )

    # 10. order_items
    item_rows = scale * 6
    item_pages = max(20, (item_rows * 60) // 8192)
    cat.tables["order_items"] = TableStatistics(
        name="order_items",
        row_count=item_rows,
        page_count=item_pages,
        avg_row_width=60,
        indexes=["order_items_pkey", "idx_order_items_order", "idx_order_items_product"],
        columns={
            "item_id": ColumnStatistics("item_id", "integer", distinct_values=item_rows, has_index=True, index_name="order_items_pkey"),
            "order_id": ColumnStatistics("order_id", "integer", distinct_values=ord_rows, has_index=True, index_name="idx_order_items_order"),
            "product_id": ColumnStatistics("product_id", "integer", distinct_values=prod_rows, has_index=True, index_name="idx_order_items_product"),
            "quantity": ColumnStatistics("quantity", "integer", distinct_values=10, min_value="1", max_value="20", has_index=False),
            "unit_price": ColumnStatistics("unit_price", "numeric", distinct_values=500, min_value="10.00", max_value="2000.00", has_index=False),
            "discount": ColumnStatistics("discount", "numeric", distinct_values=5, min_value="0.0", max_value="0.5", has_index=False)
        }
    )

    return cat
