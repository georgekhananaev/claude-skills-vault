# Code Review Checklist

## Quick Reference Checklist

Use this checklist systematically when reviewing code.

---

## 1. Code Quality

### Structure & Organization
- [ ] Code follows single responsibility principle
- [ ] Functions/methods are appropriately sized (<50 lines preferred)
- [ ] Classes have clear, focused purposes
- [ ] File organization is logical
- [ ] No circular dependencies

### Clean Code
- [ ] No dead code (unused variables, functions, imports)
- [ ] No commented-out code blocks
- [ ] No duplicate code (DRY principle)
- [ ] Magic numbers are extracted to constants
- [ ] Complex logic has explanatory comments

### Naming
- [ ] Variables have meaningful, descriptive names
- [ ] Functions describe what they do (verb-based)
- [ ] Consistent naming convention (camelCase, snake_case, etc.)
- [ ] No abbreviations unless universally understood
- [ ] Boolean variables start with is/has/should/can

### Type Safety
- [ ] No use of `any` type (TypeScript)
- [ ] Proper null/undefined handling
- [ ] Type assertions are justified
- [ ] Generic types used appropriately
- [ ] Return types are explicit

---

## 2. Security

### Input Validation
- [ ] All user input is validated
- [ ] Input is sanitized before use
- [ ] SQL queries use parameterized statements
- [ ] No command injection vulnerabilities
- [ ] File paths are validated

### Authentication & Authorization
- [ ] Sensitive routes are protected
- [ ] Authorization checks at appropriate levels
- [ ] Session management is secure
- [ ] Tokens have appropriate expiration
- [ ] Password handling follows best practices

### Data Protection
- [ ] No hardcoded secrets/credentials
- [ ] Sensitive data is encrypted at rest
- [ ] Secure communication (HTTPS)
- [ ] PII is handled appropriately
- [ ] Logs don't contain sensitive data

### Common Vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] CSRF protection in place
- [ ] No open redirects
- [ ] Secure deserialization
- [ ] No information leakage in errors

---

## 3. Performance

### Database
- [ ] No N+1 query patterns
- [ ] Appropriate indexes exist
- [ ] Queries are optimized
- [ ] Connection pooling configured
- [ ] Transactions used appropriately

### Memory & Resources
- [ ] No memory leaks
- [ ] Event listeners are cleaned up
- [ ] Subscriptions are unsubscribed
- [ ] Large objects are disposed properly
- [ ] Caching is implemented where beneficial

### Algorithms
- [ ] Appropriate data structures used
- [ ] Algorithm complexity is acceptable
- [ ] Pagination for large datasets
- [ ] Lazy loading where appropriate
- [ ] No unnecessary iterations

### Frontend Specific
- [ ] Components avoid unnecessary re-renders
- [ ] Bundle size is reasonable
- [ ] Images are optimized
- [ ] Critical path is minimized
- [ ] Debouncing/throttling for frequent events

---

## 4. Error Handling

### Exception Management
- [ ] Errors are caught at appropriate levels
- [ ] Errors are logged with context
- [ ] User-friendly error messages
- [ ] Errors don't expose internals
- [ ] Graceful degradation where possible

### Edge Cases
- [ ] Null/undefined handled
- [ ] Empty arrays/objects handled
- [ ] Network failures handled
- [ ] Timeout scenarios handled
- [ ] Race conditions considered

### Recovery
- [ ] Retry logic with backoff
- [ ] Circuit breaker patterns where needed
- [ ] Rollback mechanisms in place
- [ ] State cleanup on failure

---

## 5. Testing

### Coverage
- [ ] Unit tests for business logic
- [ ] Integration tests for APIs
- [ ] Edge cases are tested
- [ ] Error scenarios are tested
- [ ] Mocks are appropriate

### Quality
- [ ] Tests are readable
- [ ] Tests are independent
- [ ] No flaky tests
- [ ] Test data is representative
- [ ] Assertions are meaningful

---

## 6. Documentation

### Code Documentation
- [ ] Complex logic is commented
- [ ] Public APIs are documented
- [ ] Function parameters documented
- [ ] Return values documented
- [ ] Examples provided where helpful

### External Documentation
- [ ] README updated if needed
- [ ] API documentation updated
- [ ] Changelog updated
- [ ] Migration guide if breaking changes

---

## 7. Best Practices

### SOLID Principles
- [ ] **S**ingle Responsibility
- [ ] **O**pen/Closed
- [ ] **L**iskov Substitution
- [ ] **I**nterface Segregation
- [ ] **D**ependency Inversion

### Design Patterns
- [ ] Appropriate patterns used
- [ ] Patterns not over-engineered
- [ ] Consistent with existing codebase

### Maintainability
- [ ] Code is self-explanatory
- [ ] Configuration is externalized
- [ ] Feature flags for risky changes
- [ ] Backward compatibility considered

---

## 8. Git & Versioning

### Commit Quality
- [ ] Commits are atomic
- [ ] Commit messages are descriptive
- [ ] No unrelated changes bundled
- [ ] No sensitive data in commits

### PR Quality
- [ ] PR description is complete
- [ ] Breaking changes are noted
- [ ] Migration steps if needed
- [ ] Screenshots for UI changes

---

## Severity Guide

| Finding | Severity |
|---------|----------|
| Security vulnerability | Critical |
| Data corruption risk | Critical |
| Breaking production | Critical |
| Significant bug | High |
| Performance regression | High |
| Missing error handling | Medium |
| Code quality issue | Medium |
| Minor optimization | Low |
| Style preference | Low |
| Enhancement idea | Info |

---

## Review Notes Template

```markdown
## File: `path/to/file.ts`

### Critical
- Line X: [Issue description]
  - Impact: [What could go wrong]
  - Fix: [Suggested solution]

### High
- [Issues...]

### Medium
- [Issues...]

### Positive
- Good use of [pattern/practice]
- Well-structured [component/function]
```