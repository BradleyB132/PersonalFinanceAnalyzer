<!-- The following .md is user stories and AC's to explain how user authentication is used. -->
### User Stories
As a user,
I want to be able to create or login to an account 
so that I can access personalized features on the website.

### Acceptance Criteria
- **AC1:** Given that I am on the registration page, 
  When I fill in the required fields and submit the form, 
  Then my account should be created successfully and I should receive a confirmation email.
- **AC2:** Given that I have an existing account, 
  When I enter my correct username and password on the login page, 
  Then I should be logged in and redirected to my dashboard.
- **AC3:** Given that I have an existing account, 
  When I enter an incorrect username or password on the login page, 
  Then I should receive an error message indicating that my credentials are invalid.
- **AC4:** Given that I am logged in, 
  When I click on the logout button, 
  Then I should be logged out and redirected to the homepage.
- **AC5:** Given that I am on the registration page, 
  When I try to create an account with an email that is already in use, 
  Then I should receive an error message indicating that the email is already registered.