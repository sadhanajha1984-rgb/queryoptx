-- QueryOptX Seed Data (Baseline Sample Data)

-- Departments
INSERT INTO departments (dept_id, dept_name, building, budget) VALUES
(1, 'Computer Science', 'Turing Hall', 500000.00),
(2, 'Electrical Engineering', 'Maxwell Lab', 450000.00),
(3, 'Mathematics', 'Euler Building', 300000.00),
(4, 'Physics', 'Newton Center', 350000.00),
(5, 'Mechanical Engineering', 'Carnot Wing', 400000.00);

-- Instructors
INSERT INTO instructors (instructor_id, name, dept_id, salary, hire_date) VALUES
(1, 'Dr. Alan Turing', 1, 120000.00, '2015-08-15'),
(2, 'Dr. Claude Shannon', 1, 115000.00, '2017-01-10'),
(3, 'Dr. Nikola Tesla', 2, 110000.00, '2016-03-22'),
(4, 'Dr. Emmy Noether', 3, 125000.00, '2014-09-01'),
(5, 'Dr. Richard Feynman', 4, 130000.00, '2013-05-18');

-- Students
INSERT INTO students (student_id, name, email, department, gpa, tot_cred, enrollment_year) VALUES
(101, 'Alice Johnson', 'alice@univ.edu', 'Computer Science', 3.90, 85, 2022),
(102, 'Bob Smith', 'bob@univ.edu', 'Computer Science', 3.45, 60, 2023),
(103, 'Charlie Brown', 'charlie@univ.edu', 'Electrical Engineering', 3.20, 90, 2021),
(104, 'Diana Prince', 'diana@univ.edu', 'Mathematics', 3.95, 110, 2021),
(105, 'Evan Wright', 'evan@univ.edu', 'Physics', 2.85, 45, 2024),
(106, 'Fiona Gallagher', 'fiona@univ.edu', 'Computer Science', 3.75, 75, 2022),
(107, 'George Clark', 'george@univ.edu', 'Mechanical Engineering', 3.10, 50, 2023),
(108, 'Hannah Abbott', 'hannah@univ.edu', 'Mathematics', 3.65, 80, 2022);

-- Courses
INSERT INTO courses (course_id, course_code, title, dept_id, credits, instructor_id) VALUES
(201, 'CS101', 'Intro to Algorithms', 1, 4, 1),
(202, 'CS201', 'Database Systems', 1, 4, 2),
(203, 'EE101', 'Circuits & Signals', 2, 3, 3),
(204, 'MATH301', 'Linear Algebra', 3, 3, 4),
(205, 'PHYS201', 'Quantum Mechanics', 4, 4, 5);

-- Enrollments
INSERT INTO enrollments (enrollment_id, student_id, course_id, semester, year, grade, grade_point) VALUES
(1, 101, 201, 'Fall', 2023, 'A', 4.00),
(2, 101, 202, 'Spring', 2024, 'A', 4.00),
(3, 102, 201, 'Fall', 2023, 'B+', 3.50),
(4, 102, 202, 'Spring', 2024, 'B', 3.00),
(5, 103, 203, 'Fall', 2023, 'B', 3.00),
(6, 104, 204, 'Spring', 2024, 'A+', 4.00),
(7, 105, 205, 'Fall', 2024, 'C', 2.00),
(8, 106, 201, 'Fall', 2023, 'A-', 3.70),
(9, 106, 202, 'Spring', 2024, 'A', 4.00);

-- Categories
INSERT INTO categories (category_id, category_name, parent_category_id) VALUES
(1, 'Electronics', NULL),
(2, 'Computers', 1),
(3, 'Accessories', 1),
(4, 'Books', NULL),
(5, 'Textbooks', 4);

-- Products
INSERT INTO products (product_id, product_name, category_id, price, stock_quantity, rating) VALUES
(1001, 'Database Internals Book', 5, 59.99, 120, 4.9),
(1002, 'Introduction to Algorithms (CLRS)', 5, 89.99, 85, 4.8),
(1003, 'Ultra-wide Monitor 34"', 2, 499.99, 45, 4.7),
(1004, 'Ergonomic Mechanical Keyboard', 3, 129.99, 210, 4.6),
(1005, 'Wireless Noise-Canceling Headphones', 1, 249.99, 150, 4.5);

-- Customers
INSERT INTO customers (customer_id, name, email, country, city, loyalty_tier) VALUES
(501, 'Sarah Connor', 'sarah@skynet.com', 'USA', 'Los Angeles', 'Gold'),
(502, 'John Doe', 'johndoe@gmail.com', 'USA', 'New York', 'Silver'),
(503, 'Elena Rostova', 'elena@mail.ru', 'Germany', 'Berlin', 'Platinum'),
(504, 'Kenji Sato', 'kenji@tokyo.jp', 'Japan', 'Tokyo', 'Gold'),
(505, 'Priya Sharma', 'priya@tech.in', 'India', 'Bangalore', 'Diamond');

-- Orders
INSERT INTO orders (order_id, customer_id, order_date, status, total_amount) VALUES
(8001, 501, '2024-01-15', 'Completed', 149.98),
(8002, 502, '2024-02-10', 'Completed', 499.99),
(8003, 503, '2024-02-18', 'Completed', 379.98),
(8004, 504, '2024-03-01', 'Shipped', 129.99),
(8005, 505, '2024-03-05', 'Completed', 749.98);

-- Order Items
INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount) VALUES
(1, 8001, 1001, 1, 59.99, 0.0),
(2, 8001, 1002, 1, 89.99, 0.0),
(3, 8002, 1003, 1, 499.99, 0.0),
(4, 8003, 1004, 1, 129.99, 0.0),
(5, 8003, 1005, 1, 249.99, 0.0),
(6, 8004, 1004, 1, 129.99, 0.0),
(7, 8005, 1003, 1, 499.99, 0.0),
(8, 8005, 1005, 1, 249.99, 0.0);
