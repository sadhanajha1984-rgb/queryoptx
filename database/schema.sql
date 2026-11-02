-- QueryOptX Demonstration Database Schema (PostgreSQL)
-- Schema covers realistic relational workloads for query optimization:
-- University / Academic DB & E-Commerce Retail DB

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS student_courses CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS instructors CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS students CASCADE;

-- ==========================================================
-- 1. University Academic Schema
-- ==========================================================

CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE,
    building VARCHAR(100),
    budget NUMERIC(12, 2) DEFAULT 100000.00
);

CREATE TABLE instructors (
    instructor_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dept_id INT REFERENCES departments(dept_id),
    salary NUMERIC(10, 2),
    hire_date DATE
);

CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    department VARCHAR(100),
    gpa NUMERIC(3, 2),
    tot_cred INT DEFAULT 0,
    enrollment_year INT
);

CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    dept_id INT REFERENCES departments(dept_id),
    credits INT DEFAULT 3,
    instructor_id INT REFERENCES instructors(instructor_id)
);

CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(student_id),
    course_id INT REFERENCES courses(course_id),
    semester VARCHAR(20),
    year INT,
    grade VARCHAR(5),
    grade_point NUMERIC(3, 2)
);

-- Indexes for access path exploration
CREATE INDEX idx_students_dept ON students(department);
CREATE INDEX idx_students_gpa ON students(gpa);
CREATE INDEX idx_students_year ON students(enrollment_year);
CREATE INDEX idx_courses_dept ON courses(dept_id);
CREATE INDEX idx_courses_instructor ON courses(instructor_id);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_grade ON enrollments(grade);

-- ==========================================================
-- 2. E-Commerce Retail Schema
-- ==========================================================

CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    parent_category_id INT REFERENCES categories(category_id)
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category_id INT REFERENCES categories(category_id),
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    rating NUMERIC(2, 1)
);

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    country VARCHAR(50),
    city VARCHAR(50),
    loyalty_tier VARCHAR(20) DEFAULT 'Bronze',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'Completed',
    total_amount NUMERIC(10, 2)
);

CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    discount NUMERIC(4, 2) DEFAULT 0.0
);

-- Indexes for E-commerce access path exploration
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_customers_country ON customers(country);
CREATE INDEX idx_customers_tier ON customers(loyalty_tier);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
