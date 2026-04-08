-- =========================================
-- EXAMPLE_QUERIES.SQL
-- Personal Finance App Example Queries
-- =========================================

-- -------------------------------------------------
-- 1. ADD A NEW USER
-- -------------------------------------------------
-- Inserts a new user into the system.
-- RETURNING id allows the application to capture the generated user ID.

INSERT INTO users (email, password_hash)
VALUES ('newuser@example.com', 'hashed_password_here')
RETURNING id;


-- -------------------------------------------------
-- 2. ADD A NEW UPLOADED FILE
-- -------------------------------------------------
-- Each user can upload files (e.g., bank statements).
-- This query stores metadata about the uploaded file.

INSERT INTO uploaded_files (user_id, file_type, file_name)
VALUES (1, 'csv', 'feb_transactions.csv')
RETURNING id;


-- -------------------------------------------------
-- 3. ADD A TRANSACTION (MANUAL CATEGORY)
-- -------------------------------------------------
-- Inserts a transaction where the category is explicitly provided.

INSERT INTO transactions (
    user_id,
    category_id,
    amount,
    description,
    transaction_date,
    uploaded_file_id
)
VALUES (
    1,
    2, -- Example: Groceries
    45.67,
    'Walmart grocery trip',
    '2025-02-01',
    1
);


-- -------------------------------------------------
-- 4. ADD A TRANSACTION (AUTO-CATEGORIZATION)
-- -------------------------------------------------
-- Uses description_rules to automatically assign a category.
-- Priority:
--   1. User-specific rules
--   2. Global rules (user_id IS NULL)
--   3. Fallback to 'Uncategorized' (assumed id = 1)

INSERT INTO transactions (
    user_id,
    category_id,
    amount,
    description,
    transaction_date,
    uploaded_file_id
)
SELECT
    1,
    COALESCE(dr.category_id, 1),
    45.67,
    'Amazon purchase',
    '2025-02-01',
    1
FROM description_rules dr
WHERE 'Amazon purchase' ILIKE '%' || dr.keyword || '%'
  AND (dr.user_id = 1 OR dr.user_id IS NULL)
ORDER BY dr.user_id DESC
LIMIT 1;


-- -------------------------------------------------
-- 5. CREATE A USER-SPECIFIC CATEGORY (OVERRIDE)
-- -------------------------------------------------
-- Allows a user to define their own category.
-- Example: overriding "Shopping" with "Gifts"

INSERT INTO categories (name, user_id)
VALUES ('Gifts', 1)
RETURNING id;


-- -------------------------------------------------
-- 6. UPDATE A TRANSACTION TO USE OVERRIDE CATEGORY
-- -------------------------------------------------
-- Reassigns an existing transaction to a user-defined category.

UPDATE transactions
SET category_id = 16 -- Example: Gifts category
WHERE id = 3
  AND user_id = 1;


-- -------------------------------------------------
-- 7. ADD A DESCRIPTION RULE FOR AUTO-OVERRIDE
-- -------------------------------------------------
-- Ensures future transactions automatically use the user-specific category.
-- Example: "Amazon" transactions become "Gifts" for this user.

INSERT INTO description_rules (keyword, category_id, user_id)
VALUES ('Amazon', 16, 1);


-- -------------------------------------------------
-- 8. QUERY TRANSACTIONS WITH CATEGORY NAMES
-- -------------------------------------------------
-- Useful for displaying transactions in a UI.

SELECT
    t.id,
    t.amount,
    t.description,
    t.transaction_date,
    c.name AS category
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.user_id = 1
ORDER BY t.transaction_date DESC;


-- -------------------------------------------------
-- 9. VIEW CATEGORY TYPE (SYSTEM VS USER)
-- -------------------------------------------------
-- Helps determine whether a category is system-defined or user-defined.
-- If c.user_id IS NULL => system category
-- If NOT NULL => user-defined category

SELECT
    t.description,
    t.amount,
    c.name,
    c.user_id
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.user_id = 1;


-- -------------------------------------------------
-- 10. VERIFY USER CREDENTIALS (LOGIN)
-- -------------------------------------------------
-- Checks if a user exists with the given email and password hash.
-- In a real app, you should hash the incoming password and compare hashes.
-- Returns the user id if credentials are valid.

SELECT id
FROM users
WHERE email = 'newuser@example.com'
  AND password_hash = 'hashed_password_here';


  -- -------------------------------------------------
-- 11. VIEW ALL TRANSACTIONS FOR A USER
-- -------------------------------------------------
-- Retrieves all transactions for a user with category names and file info.
-- Useful for dashboards or account history pages.

SELECT
    t.id,
    t.amount,
    t.description,
    t.transaction_date,
    c.name AS category,
    uf.file_name
FROM transactions t
JOIN categories c ON t.category_id = c.id
LEFT JOIN uploaded_files uf ON t.uploaded_file_id = uf.id
WHERE t.user_id = 1
ORDER BY t.transaction_date DESC;


-- =========================================
-- END OF FILE
-- =========================================
