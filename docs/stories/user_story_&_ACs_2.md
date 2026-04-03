### User Story 2 : Upload credit card statements
As a user,
I want to be able to upload my credit card statements
so that I can view all my spending in one place alongside my bank transactions.

### Acceptance Criteria
- **AC1:** Given that I am on the dashboard,
  When I click on the "Upload Credit Card Statement" button,
  Then I should be prompted to select a file from my computer.
- **AC2:** Given that I have selected a valid credit card statement file,
  When I submit the upload form,
  Then the system should process the file and extract relevant transaction data.
- **AC3:** Given that the transactions are processed,
  When processing completes,
  Then each transaction should be automatically categorized.
- **AC4:** Given that both bank and credit card transactions exist,
  When I view the dashboard,
  Then I should see a combined view of all transactions.
