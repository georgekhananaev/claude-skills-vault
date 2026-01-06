---
name: pr
description: Prepare GitHub Pull Request with essential details
tools:
  - Bash(git config user.name)
  - Bash(git config user.email)
  - Bash(git branch --show-current)
  - Bash(git log *)
  - Bash(git diff *)
  - Bash(git status)
  - Bash(git rev-list --count *)
  - Bash(git shortlog *)
  - Bash(gh pr create *)
  - Bash(gh pr view *)
---

# Pull Request Workflow

Execute this workflow to prepare a GitHub Pull Request:

## 1. **Gather Branch Information**
- Run `git branch --show-current` to get current branch name
- Run `git config user.name` and `git config user.email`
- Show: "📍 Current branch: [branch_name]"
- Show: "👤 Author: [name] <[email]>"

## 2. **Determine Base Branch**
- Check if `main` or `master` exists as the default branch
- Use the appropriate base branch for comparison

## 3. **Analyze Changes**
- Run `git rev-list --count [base]..HEAD` to count commits
- Run `git log [base]..HEAD --oneline` to list all commits
- Run `git diff [base]..HEAD --stat` to show changed files summary
- Run `git diff [base]..HEAD` for detailed changes (summarize, don't show all)

## 4. **Generate PR Details**

Present the PR information in this format:

```markdown
## PR Title
<type>: <concise description>

## PR Description

### 📋 Summary
<2-3 sentence overview of what this PR does>

### 🔄 Changes
- Change 1: description
- Change 2: description
- Change 3: description

### 📁 Files Changed
- `path/to/file1.ts` - description of changes
- `path/to/file2.tsx` - description of changes

### 🧪 Testing
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] No breaking changes

### 📝 Notes
<Any additional context, screenshots needed, or deployment notes>
```

## 5. **ASK FOR APPROVAL**
Stop here and ask:
```
Ready to create PR?
1. Copy details to clipboard (manual PR)
2. Create PR via GitHub CLI (gh pr create)
3. Edit details first
```
WAIT for my response before proceeding.

## 6. **If Option 2 (GitHub CLI)**
Run:
```bash
gh pr create --title "<title>" --body "<body>" --base [base_branch]
```
Show the PR URL when complete.

---

## PR Title Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style/formatting
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

## IMPORTANT
- Always wait for approval before creating the PR
- Detect breaking changes and highlight them
- Include relevant issue numbers if found in commits (e.g., "Fixes #123")
- Keep the summary concise but informative
- Never include sensitive information in PR descriptions