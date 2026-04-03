### User Story 3 : Overriding categories
As a user,
I want to override transaction categories
so that I can correct any misclassified transactions.

### Acceptance Criteria
- **AC1:** Given that transactions are displayed,
  When I select a transaction,
  Then I should be able to view and edit its category.
- **AC2:** Given that I change a transaction’s category,
  When I save the update,
  Then the new category should be stored successfully.
- **AC3:** Given that a category has been updated,
  When I reload the page,
  Then the updated category should remain unchanged.
- **AC4:** Given that one or more categories are updated,
  When I view the dashboard,
  Then the visualizations should reflect the updated data.
