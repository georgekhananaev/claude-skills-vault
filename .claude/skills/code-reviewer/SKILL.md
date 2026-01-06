# Code Reviewer Skill

A comprehensive code review skill that analyzes code quality, security, performance, and best practices.

## When to Use

Invoke this skill when:
- User asks to review code or a pull request
- User requests code quality analysis
- User wants security or performance audit
- Commands: `/review`, `/code-review`, `/pr-review`

## Capabilities

### 1. Code Quality Analysis
- Dead code detection
- Unused imports/variables
- Code duplication (DRY violations)
- Complexity metrics (cyclomatic complexity)
- Function/method length analysis
- Naming conventions

### 2. Security Review
- SQL injection vulnerabilities
- XSS vulnerabilities
- Command injection risks
- Hardcoded secrets/credentials
- Insecure dependencies
- Authentication/authorization issues
- Input validation gaps

### 3. Performance Analysis
- N+1 query detection
- Inefficient algorithms
- Memory leaks
- Unnecessary re-renders (React)
- Bundle size concerns
- Caching opportunities

### 4. Best Practices
- SOLID principles adherence
- Design pattern usage
- Error handling
- Logging practices
- Test coverage gaps
- Documentation completeness

## Review Process

### Step 1: Understand Context
```
1. Identify the language/framework
2. Understand the purpose of the code
3. Check for existing patterns in the codebase
4. Review any related tests
```

### Step 2: Systematic Review
Use the checklist at `checklist.md` to perform a thorough review.

### Step 3: Categorize Findings

| Severity | Description | Action Required |
|----------|-------------|-----------------|
| Critical | Security vulnerabilities, data loss risks | Must fix before merge |
| High | Bugs, significant performance issues | Should fix before merge |
| Medium | Code quality issues, minor bugs | Consider fixing |
| Low | Style issues, minor improvements | Optional |
| Info | Suggestions, alternative approaches | For consideration |

### Step 4: Provide Actionable Feedback

For each issue found:
```markdown
**[SEVERITY] Issue Title**
- File: `path/to/file.ts:line`
- Problem: Clear description of the issue
- Impact: What could go wrong
- Fix: Specific code suggestion or approach
```

## Output Format

```markdown
# Code Review Summary

## Overview
- Files reviewed: X
- Issues found: Y (X Critical, Y High, Z Medium)
- Recommendation: [Approve / Request Changes / Needs Discussion]

## Critical Issues
[List critical issues with fixes]

## High Priority
[List high priority issues]

## Medium Priority
[List medium priority issues]

## Low Priority & Suggestions
[List minor issues and improvements]

## Positive Observations
[Highlight good practices found]

## Summary
[Brief summary and next steps]
```

## Language-Specific Checks

### TypeScript/JavaScript
- Type safety (any usage, type assertions)
- Null/undefined handling
- Async/await patterns
- React hooks rules
- Memory management in closures

### Python
- Type hints usage
- Exception handling
- Resource management (context managers)
- Import organization
- PEP 8 compliance

### Go
- Error handling patterns
- Goroutine leaks
- Race conditions
- Interface design
- Context propagation

### Rust
- Ownership/borrowing patterns
- Error handling (Result/Option)
- Unsafe block justification
- Memory safety

## Integration

### With Git
```bash
# Review staged changes
git diff --cached | claude review

# Review specific commit
git show <commit> | claude review

# Review PR (with gh cli)
gh pr diff <number> | claude review
```

### Automated Checks
The skill can integrate with:
- ESLint/Prettier configurations
- SonarQube rules
- Custom linting rules
- CI/CD pipelines

## Configuration

Create `.claude/review-config.json` to customize:
```json
{
  "severity_threshold": "medium",
  "ignore_patterns": ["*.test.ts", "*.spec.ts"],
  "focus_areas": ["security", "performance"],
  "custom_rules": [],
  "max_file_size": 1000
}
```

## Examples

### Example 1: Quick Review

```
User: Review this function for issues

function getData() {
  var data = fetch('/api/data')
  return data
}
```

Response: Found 3 issues:
1. **[Medium]** Missing async/await - fetch returns Promise
2. **[Low]** Use const instead of var
3. **[Low]** Add error handling