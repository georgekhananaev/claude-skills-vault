# Claude Code Commands Tutorial

A guide to creating and using slash commands in Claude Code.

## Table of Contents

1. [What Are Commands?](#what-are-commands)
2. [Directory Structure](#directory-structure)
3. [Creating Your First Command](#creating-your-first-command)
4. [Command Structure](#command-structure)
5. [Best Practices](#best-practices)
6. [Examples](#examples)

---

## What Are Commands?

Commands are slash-invocable workflows that extend Claude Code with custom automation. They provide:

- **Workflow automation**: Standardized processes for common tasks
- **Safety protocols**: Built-in checks and validations
- **Consistency**: Same behavior across team members
- **Reusability**: Define once, use anywhere

### Commands vs Skills vs MCP Servers

| Feature | Commands | Skills | MCP Servers |
|---------|----------|--------|-------------|
| Invocation | `/command-name` | Automatic or referenced | Tool calls |
| Purpose | Workflows & actions | Knowledge & guidance | External integrations |
| Format | Markdown | Markdown | Executable code |
| Scope | Task execution | Context injection | API/database access |

---

## Directory Structure

```
.claude/
└── commands/
    ├── commit.md
    ├── review.md
    └── deploy.md
```

Commands are placed in `.claude/commands/` directory. Each `.md` file becomes a slash command using its filename.

| File | Command |
|------|---------|
| `commit.md` | `/commit` |
| `review.md` | `/review` |
| `deploy.md` | `/deploy` |

---

## Creating Your First Command

### Step 1: Create the Directory

```bash
mkdir -p .claude/commands
```

### Step 2: Create Command File

Create `.claude/commands/hello.md`:

```markdown
# Hello Command

Goal: Greet the user with project information.

## Execution

1. Read the project's package.json or pyproject.toml
2. Extract the project name and version
3. Display a friendly greeting with project details
```

### Step 3: Use the Command

```
/hello
```

---

## Command Structure

### Basic Template

```markdown
# Command Name

Goal: One-line description of what this command does.

## Prerequisites
- Required conditions or setup

## Execution Flow
1. First step
2. Second step
3. Third step

## Output
Expected result or format
```

### Detailed Template

```markdown
# Command Name

Goal: Clear description of the command's purpose.

## 1. Prerequisites
- Required tools or configurations
- Environment variables needed
- File dependencies

## 2. Safety Protocols
**Forbidden Actions:**
- Actions that should never be performed
- Files that should never be modified

**Required Checks:**
- Validations before execution
- Conditions that must be met

## 3. Execution Flow
1. **Step Name**: Description of what to do
2. **Step Name**: Next action
3. **Step Name**: Continue process

## 4. Output Format
Expected output structure or behavior

## 5. Error Handling
- How to handle specific errors
- Fallback behaviors
```

---

## Best Practices

### DO

- **Be specific**: Clear, actionable instructions
- **Include safety checks**: Prevent destructive actions
- **Define prerequisites**: State what's needed upfront
- **Handle errors**: Specify what to do when things fail
- **Keep focused**: One command = one workflow

### DON'T

- **Be vague**: "Do it properly" is not helpful
- **Skip validation**: Always verify before destructive actions
- **Assume context**: State requirements explicitly
- **Overcomplicate**: Keep commands digestible

### Naming Conventions

```
.claude/commands/
├── commit.md           # Simple, verb-based
├── review-pr.md        # Hyphenated for multi-word
├── deploy-staging.md   # Include target/scope
└── run-tests.md        # Action-oriented
```

---

## Examples

### Example 1: Code Review Command

`.claude/commands/review.md`:

```markdown
# Code Review Command

Goal: Perform a comprehensive code review on staged changes.

## Prerequisites
- Git repository with staged changes
- No uncommitted secrets or credentials

## Execution Flow

1. **Get Changes**: Run `git diff --cached` to see staged changes
2. **Analyze Code**: Review for:
   - Code quality and readability
   - Potential bugs or edge cases
   - Security vulnerabilities
   - Performance concerns
   - Test coverage
3. **Generate Report**: Provide findings in structured format

## Output Format

### Code Review Report

**Summary**: Brief overview

**Issues Found**:
- [CRITICAL] Description
- [WARNING] Description
- [SUGGESTION] Description

**Recommendations**:
- Actionable improvements
```

### Example 2: Deploy Command

`.claude/commands/deploy.md`:

```markdown
# Deploy Command

Goal: Deploy the application to the specified environment.

## Prerequisites
- Clean git working tree
- All tests passing
- Valid deployment credentials

## Safety Protocols

**Never:**
- Deploy with failing tests
- Deploy uncommitted changes
- Skip confirmation for production

**Always:**
- Verify target environment
- Check current branch
- Confirm with user before production

## Execution Flow

1. **Verify State**:
   - Run `git status` - must be clean
   - Run tests - must pass

2. **Confirm Environment**:
   - Ask user for target: staging/production
   - For production: require explicit confirmation

3. **Execute Deploy**:
   - Run deployment script
   - Monitor for errors

4. **Verify**:
   - Check deployment status
   - Report success or failure

## Error Handling

- Test failure: Stop and report which tests failed
- Deploy failure: Show logs and rollback steps
```

### Example 3: Release Command

`.claude/commands/release.md`:

```markdown
# Release Command

Goal: Create a new versioned release.

## Prerequisites
- Clean git working tree
- On main/master branch
- All tests passing

## Execution Flow

1. **Validate State**:
   - Check branch is main/master
   - Verify clean working tree
   - Run test suite

2. **Determine Version**:
   - Ask user: major/minor/patch
   - Calculate new version number

3. **Update Files**:
   - Update version in package.json/pyproject.toml
   - Update CHANGELOG.md

4. **Create Release**:
   - Commit version changes
   - Create git tag
   - Push to remote

5. **Report**:
   - Display new version
   - Show release URL

## Version Bump Rules

- **Major** (1.0.0 → 2.0.0): Breaking changes
- **Minor** (1.0.0 → 1.1.0): New features
- **Patch** (1.0.0 → 1.0.1): Bug fixes
```

### Example 4: Database Migration Command

`.claude/commands/migrate.md`:

```markdown
# Database Migration Command

Goal: Run database migrations safely.

## Prerequisites
- Database connection configured
- Migration files exist
- Backup available for production

## Safety Protocols

**Production Checks:**
- Require explicit confirmation
- Verify backup exists
- Run in transaction when possible

## Execution Flow

1. **Check Environment**:
   - Detect current environment
   - Warn if production

2. **Preview Migrations**:
   - List pending migrations
   - Show what will change

3. **Confirm**:
   - Ask user to proceed
   - For production: require typing environment name

4. **Execute**:
   - Run migrations
   - Report success/failure

5. **Verify**:
   - Check migration status
   - Confirm database state
```

---

## Troubleshooting

### Command Not Found

1. Check file is in `.claude/commands/`
2. Verify filename ends with `.md`
3. Ensure file is not empty

### Command Not Executing Properly

1. Check markdown syntax is valid
2. Verify instructions are clear and specific
3. Add more detailed step-by-step instructions

### Inconsistent Behavior

1. Add explicit checks and validations
2. Include more specific instructions
3. Define error handling for edge cases

---

Created by George Khananaev
