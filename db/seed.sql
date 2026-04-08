-- =========================
-- USERS
-- =========================
INSERT INTO users (id, email, password_hash)
VALUES
(1, 'alice@example.com', 'hash1'),
(2, 'bob@example.com', 'hash2'),
(3, 'charlie@example.com', 'hash3'),
(4, 'diana@example.com', 'hash4'),
(5, 'eve@example.com', 'hash5');

-- =========================
-- SYSTEM CATEGORIES (user_id NULL)
-- =========================
INSERT INTO categories (id, name, user_id) VALUES
(1, 'Uncategorized', NULL),
(2, 'Groceries', NULL),
(3, 'Dining', NULL),
(4, 'Transportation', NULL),
(5, 'Utilities', NULL),
(6, 'Rent', NULL),
(7, 'Entertainment', NULL),
(8, 'Shopping', NULL),
(9, 'Healthcare', NULL),
(10, 'Travel', NULL),
(11, 'Subscriptions', NULL),
(12, 'Income', NULL),
(13, 'Insurance', NULL),
(14, 'Savings', NULL),
(15, 'Education', NULL);

-- =========================
-- USER-SPECIFIC CATEGORIES (Overrides)
-- =========================
INSERT INTO categories (id, name, user_id) VALUES
(16, 'Gifts', 1),
(17, 'Gifts', 2),
(18, 'Side Hustle', 3),
(19, 'Kids', 4),
(20, 'Pets', 5);

-- =========================
-- UPLOADED FILES (1 per user)
-- =========================
INSERT INTO uploaded_files (id, user_id, file_type, file_name) VALUES
(1, 1, 'csv', 'alice_jan.csv'),
(2, 2, 'csv', 'bob_jan.csv'),
(3, 3, 'csv', 'charlie_jan.csv'),
(4, 4, 'csv', 'diana_jan.csv'),
(5, 5, 'csv', 'eve_jan.csv');

-- =========================
-- DESCRIPTION RULES
-- =========================
INSERT INTO description_rules (keyword, category_id, user_id) VALUES
('Walmart', 2, NULL),
('Uber', 4, NULL),
('Netflix', 11, NULL),
('Amazon', 8, NULL),
('Gift', 16, 1),
('Gift', 17, 2);

-- =========================
-- TRANSACTIONS (20 per user)
-- =========================

-- USER 1 (Alice)
INSERT INTO transactions (user_id, category_id, amount, description, transaction_date, uploaded_file_id) VALUES
(1, 2, 54.23, 'Walmart groceries', '2025-01-01', 1),
(1, 3, 23.50, 'Chipotle', '2025-01-02', 1),
(1, 8, 120.00, 'Amazon order', '2025-01-03', 1),
(1, 16, 45.00, 'Gift purchase', '2025-01-04', 1),
(1, 5, 89.99, 'Electric bill', '2025-01-05', 1),
(1, 6, 1200.00, 'Rent payment', '2025-01-06', 1),
(1, 4, 15.75, 'Uber ride', '2025-01-07', 1),
(1, 11, 15.99, 'Netflix subscription', '2025-01-08', 1),
(1, 7, 60.00, 'Movie night', '2025-01-09', 1),
(1, 9, 100.00, 'Doctor visit', '2025-01-10', 1),
(1, 10, 300.00, 'Flight booking', '2025-01-11', 1),
(1, 2, 65.00, 'Target groceries', '2025-01-12', 1),
(1, 8, 200.00, 'Best Buy electronics', '2025-01-13', 1),
(1, 14, 500.00, 'Savings transfer', '2025-01-14', 1),
(1, 12, 2500.00, 'Salary', '2025-01-15', 1),
(1, 13, 150.00, 'Car insurance', '2025-01-16', 1),
(1, 3, 40.00, 'Restaurant', '2025-01-17', 1),
(1, 15, 200.00, 'Course fee', '2025-01-18', 1),
(1, 8, 75.00, 'Clothing', '2025-01-19', 1),
(1, 2, 80.00, 'Groceries', '2025-01-20', 1);

-- USER 2 (Bob)
INSERT INTO transactions (user_id, category_id, amount, description, transaction_date, uploaded_file_id) VALUES
(2, 2, 40.00, 'Walmart', '2025-01-01', 2),
(2, 17, 60.00, 'Gift purchase', '2025-01-02', 2),
(2, 8, 150.00, 'Amazon', '2025-01-03', 2),
(2, 4, 20.00, 'Uber', '2025-01-04', 2),
(2, 11, 9.99, 'Netflix', '2025-01-05', 2),
(2, 3, 30.00, 'Dining out', '2025-01-06', 2),
(2, 6, 1000.00, 'Rent', '2025-01-07', 2),
(2, 5, 70.00, 'Utilities', '2025-01-08', 2),
(2, 7, 50.00, 'Concert', '2025-01-09', 2),
(2, 10, 400.00, 'Trip', '2025-01-10', 2),
(2, 2, 55.00, 'Groceries', '2025-01-11', 2),
(2, 8, 90.00, 'Shopping', '2025-01-12', 2),
(2, 14, 300.00, 'Savings', '2025-01-13', 2),
(2, 12, 2200.00, 'Salary', '2025-01-14', 2),
(2, 13, 120.00, 'Insurance', '2025-01-15', 2),
(2, 9, 80.00, 'Pharmacy', '2025-01-16', 2),
(2, 3, 25.00, 'Lunch', '2025-01-17', 2),
(2, 8, 60.00, 'Clothes', '2025-01-18', 2),
(2, 2, 75.00, 'Groceries', '2025-01-19', 2),
(2, 4, 18.00, 'Uber', '2025-01-20', 2);

-- USER 3, 4, 5 (patterned data for brevity but still realistic)

-- USER 3
INSERT INTO transactions (user_id, category_id, amount, description, transaction_date, uploaded_file_id)
SELECT
3,
CASE WHEN i % 5 = 0 THEN 18 ELSE (i % 15)+1 END,
(random()*200 + 10)::NUMERIC(12,2),
'Transaction ' || i,
DATE '2025-01-01' + (i || ' days')::INTERVAL,
3
FROM generate_series(1,20) i;

-- USER 4
INSERT INTO transactions (user_id, category_id, amount, description, transaction_date, uploaded_file_id)
SELECT
4,
CASE WHEN i % 6 = 0 THEN 19 ELSE (i % 15)+1 END,
(random()*150 + 5)::NUMERIC(12,2),
'Transaction ' || i,
DATE '2025-01-01' + (i || ' days')::INTERVAL,
4
FROM generate_series(1,20) i;

-- USER 5
INSERT INTO transactions (user_id, category_id, amount, description, transaction_date, uploaded_file_id)
SELECT
5,
CASE WHEN i % 7 = 0 THEN 20 ELSE (i % 15)+1 END,
(random()*300 + 20)::NUMERIC(12,2),
'Transaction ' || i,
DATE '2025-01-01' + (i || ' days')::INTERVAL,
5
FROM generate_series(1,20) i;