# Claude Code Skills Tutorial

A comprehensive guide to creating, managing, and using skills in Claude Code.

## Table of Contents

1. [What Are Skills?](#what-are-skills)
2. [Skill Architecture](#skill-architecture)
3. [Creating Your First Skill](#creating-your-first-skill)
4. [SKILL.md Structure](#skillmd-structure)
5. [Adding Supporting Files](#adding-supporting-files)
6. [Advanced Patterns](#advanced-patterns)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

---

## What Are Skills?

Skills are specialized knowledge modules that extend Claude Code's capabilities. They provide:

- **Domain expertise**: Coding standards, architectural patterns, review checklists
- **Workflow automation**: Structured processes for common tasks
- **Context injection**: Relevant information loaded when needed
- **Reusable knowledge**: Consistent behavior across conversations

### Skills vs MCP Servers

| Feature | Skills | MCP Servers |
|---------|--------|-------------|
| Purpose | Knowledge & instructions | External tools & APIs |
| Format | Markdown files | Executable programs |
| Scope | Guides Claude's behavior | Provides new capabilities |
| Examples | Code review checklist | Database queries |

---

## Skill Architecture

### Directory Structure

```
.claude/
└── skills/
    └── my-skill/
        ├── SKILL.md          # Main skill file (required)
        ├── reference.md      # Supporting documentation
        ├── templates/        # Template files
        │   └── template.ts
        ├── scripts/          # Helper scripts
        │   └── validate.py
        └── config.json       # Configuration data
```

### How Skills Work

1. **Discovery**: Claude Code scans `.claude/skills/` for directories with `SKILL.md`
2. **Loading**: When relevant, the skill content is injected into Claude's context
3. **Execution**: Claude follows the skill's instructions and uses its resources

---

## Creating Your First Skill

### Step 1: Create the Directory

```bash
mkdir -p .claude/skills/my-skill
```

### Step 2: Create SKILL.md

```markdown
# My Skill Name

Brief description of what this skill does.

## When to Use

Invoke this skill when:
- User asks to [specific action]
- User mentions [keywords]
- Commands: `/my-command`

## Instructions

1. First, do this...
2. Then, do that...
3. Finally, complete with...

## Examples

### Example 1
User: [sample input]
Response: [expected output]
```

### Step 3: Test the Skill

Ask Claude Code to use your skill:
```
User: Use the my-skill skill to help me with X
```

Or invoke directly:
```
User: /my-command
```

---

## SKILL.md Structure

### Essential Sections

#### 1. Title and Description
```markdown
# Skill Name

A clear, one-line description of the skill's purpose.
```

#### 2. When to Use
```markdown
## When to Use

Invoke this skill when:
- [Trigger condition 1]
- [Trigger condition 2]
- Commands: `/command-name`
```

#### 3. Capabilities
```markdown
## Capabilities

### Category 1
- Capability A
- Capability B

### Category 2
- Capability C
```

#### 4. Instructions/Process
```markdown
## Process

### Step 1: [Name]
[Detailed instructions]

### Step 2: [Name]
[Detailed instructions]
```

#### 5. Output Format
```markdown
## Output Format

\```markdown
# Title

## Section 1
[Content structure]

## Section 2
[Content structure]
\```
```

#### 6. Examples
```markdown
## Examples

### Example 1: [Scenario Name]
**Input**: [What user says]
**Output**: [What Claude produces]
```

---

## Adding Supporting Files

### Reference Documentation

Create `reference.md` for detailed documentation:

```markdown
# Reference Documentation

## Concept 1

Detailed explanation...

## Concept 2

More details...
```

Reference in SKILL.md:
```markdown
For detailed information, see `reference.md`.
```

### Templates

Create reusable templates in a `templates/` directory:

```typescript
// templates/component.tsx
interface Props {
  // Define props
}

export function Component({ }: Props) {
  return (
    // Template structure
  );
}
```

Reference in SKILL.md:
```markdown
Use the template at `templates/component.tsx` as a starting point.
```

### Configuration Data

Store structured data in JSON:

```json
{
  "rules": [
    {
      "name": "Rule 1",
      "description": "Description",
      "severity": "error"
    }
  ]
}
```

### Helper Scripts

Add scripts for validation or automation:

```python
#!/usr/bin/env python3
# scripts/validate.py

def validate(input_data):
    """Validate input according to skill rules."""
    # Validation logic
    pass

if __name__ == "__main__":
    import sys
    validate(sys.argv[1])
```

---

## Advanced Patterns

### 1. Multi-Step Workflows

```markdown
## Workflow

### Phase 1: Discovery
1. Analyze the request
2. Gather context from codebase
3. Identify constraints

### Phase 2: Design
1. Create initial design
2. Validate against patterns.json
3. Present options to user

### Phase 3: Implementation
1. Generate code
2. Apply templates
3. Validate output
```

### 2. Decision Trees

```markdown
## Decision Process

```
Is it a new feature?
├── Yes
│   ├── Simple? → Use basic template
│   └── Complex? → Use advanced pattern
└── No (bug fix)
    ├── Critical? → Immediate fix path
    └── Normal? → Standard fix path
```
```

### 3. Conditional Instructions

```markdown
## Language-Specific Instructions

### If TypeScript
- Use strict mode
- Add type annotations
- Use interfaces over types for objects

### If Python
- Use type hints
- Follow PEP 8
- Use dataclasses for data containers

### If Go
- Use interfaces for dependencies
- Handle all errors explicitly
- Use context for cancellation
```

### 4. Integration with Other Skills

```markdown
## Related Skills

After completing this skill's workflow:
- Use `code-reviewer` skill to validate output
- Use `system-architect` skill for larger designs
```

### 5. User Interaction Points

```markdown
## Checkpoints

At these points, pause and confirm with user:

1. After initial analysis - confirm understanding
2. Before major changes - approve approach
3. After implementation - review results
```

---

## Best Practices

### DO

- **Be specific**: Clear, actionable instructions
- **Provide examples**: Show expected inputs and outputs
- **Structure logically**: Use clear headings and sections
- **Include edge cases**: Handle unusual situations
- **Keep updated**: Maintain accuracy as tools evolve

### DON'T

- **Be vague**: "Do it well" is not helpful
- **Overcomplicate**: Keep instructions digestible
- **Assume context**: Provide necessary background
- **Forget validation**: Include verification steps
- **Ignore errors**: Define error handling

### Naming Conventions

```
skills/
├── code-reviewer/      # Hyphenated, lowercase
├── system-architect/   # Descriptive names
├── api-generator/      # Action-oriented
└── test-writer/        # Clear purpose
```

### File Organization

```
skill-name/
├── SKILL.md           # Always required, uppercase
├── reference.md       # Lowercase for supporting files
├── templates/         # Lowercase directories
│   └── *.ts          # Template files
├── scripts/           # Helper scripts
│   └── *.py
└── config.json        # Configuration
```

---

## Examples

### Example 1: Simple Skill (Commit Message Generator)

```markdown
# Commit Message Generator

Generate consistent, descriptive commit messages.

## When to Use

- User asks for commit message help
- Commands: `/commit-msg`

## Format

\```
<type>(<scope>): <subject>

<body>

<footer>
\```

### Types
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance

## Process

1. Analyze staged changes (`git diff --cached`)
2. Identify primary change type
3. Determine scope (affected area)
4. Write concise subject (50 chars max)
5. Add body if needed (wrap at 72 chars)

## Examples

### Feature Addition
\```
feat(auth): add OAuth2 login support

Implement OAuth2 flow with Google and GitHub providers.
Includes token refresh and session management.
\```

### Bug Fix
\```
fix(api): handle null response in user endpoint

Previously crashed when user not found.
Now returns 404 with appropriate message.

Fixes #123
\```
```

### Example 2: Complex Skill (API Designer)

```markdown
# API Designer

Design RESTful APIs following best practices.

## When to Use

- Designing new API endpoints
- Reviewing API design
- Commands: `/design-api`

## Capabilities

### Design
- Endpoint structure
- Request/response formats
- Error handling
- Versioning strategy

### Documentation
- OpenAPI/Swagger specs
- Example requests/responses
- Authentication flows

## Process

### Step 1: Requirements
Gather:
- Resource entities
- Operations needed
- Authentication requirements
- Rate limiting needs

### Step 2: Design
Follow REST principles:
- Use nouns for resources
- HTTP verbs for actions
- Consistent naming

### Step 3: Validate
Check against `api-checklist.md`:
- [ ] RESTful conventions
- [ ] Error responses
- [ ] Pagination
- [ ] Versioning

### Step 4: Document
Generate OpenAPI spec using `templates/openapi.yaml`

## Patterns (see patterns.json)

### Resource Naming
\```
GET    /users          # List users
POST   /users          # Create user
GET    /users/{id}     # Get user
PUT    /users/{id}     # Update user
DELETE /users/{id}     # Delete user
\```

### Error Responses
\```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": [
      {"field": "email", "message": "Invalid format"}
    ]
  }
}
\```

## Output

Deliver:
1. Endpoint list with descriptions
2. OpenAPI specification
3. Example requests (curl)
4. Error catalog
```

---

## Troubleshooting

### Skill Not Loading

1. Check directory is under `.claude/skills/`
2. Verify `SKILL.md` exists (case-sensitive)
3. Check for markdown syntax errors

### Skill Not Triggering

1. Make "When to Use" section clear
2. Add explicit command triggers
3. Use specific keywords

### Inconsistent Behavior

1. Add more specific instructions
2. Include more examples
3. Define edge cases explicitly

---

## Quick Reference

### Minimum Viable Skill

```markdown
# Skill Name

One-line description.

## When to Use
- [Trigger condition]

## Instructions
1. [Step 1]
2. [Step 2]

## Output
[Expected output format]
```

### Full-Featured Skill

```markdown
# Skill Name

Description.

## When to Use
## Capabilities
## Process
## Output Format
## Examples
## Configuration
## Related Skills
## Troubleshooting
```

---

Created by George Khananaev
