<!-- The following .md is used for explaining our projects architecture decision. -->
# Architecture Decision Record: Core System Architecture

## Status

Accepted

---

## Context

The system is a personal finance management web application that allows users to:

* Authenticate securely (register, login, logout)
* Upload and process bank and credit card statements
* Automatically categorize transactions
* Override categories manually
* View dashboards with financial insights
* Search/filter transactions
* Export reports
* Receive budgeting recommendations

Key constraints and considerations:

* The development team is junior, so simplicity and maintainability are critical
* Features include file processing, categorization, and analytics, which may grow in complexity
* The system must handle user-specific financial data securely
* Initial scale is expected to be small to moderate
* Fast development and iteration are important

---

## Decision

### 1. System Roles & Communication: Client–Server Architecture

* A frontend client (web application) communicates with a backend server via HTTP APIs
* The backend handles authentication, business logic, file processing, and data access

### 2. Deployment & Evolution: Modular Monolith

* The application will be deployed as a single unit
* Internally, it will be divided into modules:

  * Auth Module
  * File Upload & Processing Module
  * Transaction Management Module
  * Dashboard & Reporting Module
  * Budgeting Module

### 3. Code Organization & Dependency Direction: Layered Architecture

Each module follows a layered structure:

* Presentation Layer (controllers / API endpoints)
* Application Layer (use cases, orchestration)
* Domain Layer (business logic, rules)
* Data Access Layer (repositories, ORM)

Dependencies flow inward:

```
Controller → Service → Domain → Repository → Database
```

### 4. Data & State Ownership: Single Shared Database

* A single relational database stores:

  * Users
  * Transactions
  * Categories
  * Budgets
  * Uploaded file metadata

### 5. Interaction Model: Synchronous Request–Response

* Most operations happen synchronously via API calls
* The client waits for the server response before proceeding

---

## Alternatives Considered

### 1. Microservices Architecture

* Splitting into separate services (Auth, Transactions, Analytics)

**Why not chosen:**

* Adds significant complexity (networking, deployment, service coordination)
* Harder to debug for a small team
* Overkill for current scale

### 2. Event-Driven / Asynchronous Architecture

* Using message queues for file processing and categorization

**Why not chosen (for now):**

* Adds infrastructure complexity (queues, workers)
* Harder to reason about for beginners
* Not required unless processing becomes slow

### 3. Database per Service

* Each module owns its own database

**Why not chosen:**

* Requires microservices
* Introduces data consistency challenges
* Unnecessary for a monolith

### 4. Feature-Based Architecture

* Organizing strictly by feature instead of layers

**Why not chosen:**

* Layered architecture is more familiar and easier for junior developers
* Provides clearer separation of concerns early on

---

## Consequences

### Positive

* Simplicity and faster development
* Easier debugging and deployment as a single system
* Straightforward unit and integration testing
* Clear separation of concerns with layered structure
* Lower operational overhead (no complex infrastructure required)
* Provides a solid foundation for future scaling

### Negative

* Limited scalability (entire system scales together)
* Risk of tight coupling between modules if not managed carefully
* Synchronous processing may become a bottleneck for large file uploads
* Single database can become a constraint as the system grows
* Future migration to microservices may require significant refactoring

---

## Final Insight

This architecture intentionally prioritizes simplicity, maintainability, and speed of development. It avoids premature optimization while leaving room for future evolution, such as introducing asynchronous processing or transitioning to microservices if scaling demands increase.
