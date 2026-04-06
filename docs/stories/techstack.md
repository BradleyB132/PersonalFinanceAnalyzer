# Tech Stack Decision Record

## Status  
Accepted

## Context  
The Personal Finance Analyzer is a web application that allows users to upload bank and credit card statements, automatically categorize transactions, visualize spending trends, and generate budgeting recommendations.

The system must handle structured financial data, support file uploads, provide visualizations, and store data reliably. It also needs to meet course requirements such as testing, maintainability, and consistent development environments.

The team selected a stack that prioritizes simplicity, fast development, and strong data handling.

## Decision  
We will use the following technologies:

- **Python (3.9+)** for backend logic and data processing  
- **Poetry** for dependency management and virtual environments  
- **Streamlit** for building the web interface  
- **SQLAlchemy** as the ORM for database interaction  
- **PostgreSQL** as the relational database  
- **psycopg2** for database connectivity  
- **pytest** for testing  

## Alternatives Considered  

### MERN Stack (MongoDB, Express, React, Node.js)  
- Pros: Strong full-stack ecosystem and scalability  
- Cons: More complex and less suited for structured financial data  

### Django  
- Pros: Built-in features and strong structure  
- Cons: Heavier and slower to set up  

### Flask + React  
- Pros: Flexible and scalable  
- Cons: Requires more development time  

## Consequences  

### Positive  
- Python is well-suited for financial data processing  
- Streamlit allows rapid development without a separate frontend  
- PostgreSQL ensures reliable and structured data storage  
- SQLAlchemy improves code organization and maintainability  
- Poetry keeps dependencies consistent across environments  
- pytest supports reliable testing  

### Negative  
- Streamlit has limited UI customization  
- Not ideal for large-scale applications  
- Less separation between frontend and backend  
- May require refactoring if scaling the project  