-- create a schema.sql file to include your DDL (CREATE TABLE SQL statements).
-- The DDL shall match your logical ERD.

-- Schema for Personal Finance App (matches Logical Data Design)

-- USERS
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CATEGORIES
-- user_id NULL => system-defined category
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    user_id INT NULL,
    CONSTRAINT fk_categories_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_category_name_per_user
        UNIQUE (name, user_id)
);

-- UPLOADED FILES
CREATE TABLE uploaded_files (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_uploaded_files_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- TRANSACTIONS
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    description TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    uploaded_file_id INT NULL,
    CONSTRAINT fk_transactions_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_transactions_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id),
    CONSTRAINT fk_transactions_uploaded_file
        FOREIGN KEY (uploaded_file_id)
        REFERENCES uploaded_files(id)
        ON DELETE SET NULL
);

-- DESCRIPTION RULES
-- keyword maps to category (user-specific or global if user_id NULL)
CREATE TABLE description_rules (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    user_id INT NULL,
    CONSTRAINT fk_rules_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_rules_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- INDEXES FOR PERFORMANCE

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);

CREATE INDEX idx_categories_user_id ON categories(user_id);

CREATE INDEX idx_uploaded_files_user_id ON uploaded_files(user_id);

CREATE INDEX idx_description_rules_user_id ON description_rules(user_id);
CREATE INDEX idx_description_rules_keyword ON description_rules(keyword);

-- OPTIONAL: DEFAULT CATEGORY (example seed)
-- INSERT INTO categories (name, user_id) VALUES ('Uncategorized', NULL);
