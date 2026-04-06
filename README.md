# PersonalFinanceAnalyzer
A web application that allows users to upload bank transactions and automatically categorize spending, visualize trends, and generate budgeting

# Logical Data Design

```mermaid
erDiagram
    USER {
        int id PK
        string email
        string password_hash
        datetime created_at
    }

    CATEGORY {
        int id PK
        string name
        int user_id FK "nullable for system categories"
    }

    TRANSACTION {
        int id PK
        int user_id FK
        int category_id FK
        decimal amount
        string description
        date transaction_date
        int uploaded_file_id FK
    }

    DESCRIPTION_RULE {
        int id PK
        string keyword
        int category_id FK
        int user_id FK "nullable for global rules"
    }

    UPLOADED_FILE {
        int id PK
        int user_id FK
        string file_type
        string file_name
        datetime uploaded_at
    }

    USER ||--o{ TRANSACTION : owns
    USER ||--o{ CATEGORY : creates
    USER ||--o{ UPLOADED_FILE : uploads
    USER ||--o{ DESCRIPTION_RULE : defines

    CATEGORY ||--o{ TRANSACTION : categorizes
    CATEGORY ||--o{ DESCRIPTION_RULE : maps_to

    DESCRIPTION_RULE ||--o{ TRANSACTION : auto_assigns

    UPLOADED_FILE ||--o{ TRANSACTION : generates
```

## Notes

* **Categories** can be either system-defined (user_id = null) or user-defined
* **Description rules** map keywords (e.g., "Walmart", "Uber") to categories
* When a transaction is processed:

  * The system checks description rules
  * If a match is found → category is auto-assigned
  * If no match → fallback to a default category (e.g., "Uncategorized")
* Users can override categories, and optionally create new rules from their changes
