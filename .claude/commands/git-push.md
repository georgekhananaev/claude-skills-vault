# Push Command

**IMPORTANT: This command ONLY runs when explicitly invoked via `/push`. Do NOT auto-push after commits or modifications. Wait for user to explicitly run `/push`.**

Goal: Safe git push with pre-push checks, commit integration, and changelog versioning.

## 1. Pre-Push Checks

### Step 1: Check Uncommitted Changes
```bash
git status --porcelain
```

**If output not empty (uncommitted changes exist):**
- Ask user: "You have uncommitted changes. Run /commit first?"
- **If YES**: Execute commit command via `.claude/commands/commit.md`, then continue
- **If NO**: Abort push with message "Push cancelled - uncommitted changes exist"

### Step 2: Check Remote Differences
```bash
git fetch origin
git log origin/$(git branch --show-current)..HEAD --oneline
```

**If no commits ahead of origin:**
- Inform user: "Nothing to push - branch is up to date with origin"
- Exit

## 2. Version Bump & Changelog

### Step 1: Check for Unreleased Changes
- Read `CHANGELOG.md` and check if `## [Unreleased]` section has content
- **If empty**: Skip version bump, proceed directly to push
- **If has content**: Continue to version selection

### Step 2: Ask User for Version Bump
Use **AskUserQuestion** tool to prompt user:

```
Question: "Which version bump for this release?"
Options:
- Patch (+0.0.1) - Bug fixes, minor updates (Recommended)
- Minor (+0.1.0) - New features, backwards compatible
- Major (+1.0.0) - Breaking changes
- Skip - Don't create release, push as-is
```

**Based on selection:**
- **Patch**: Increment last number (1.0.0 → 1.0.1)
- **Minor**: Increment middle, reset last (1.0.5 → 1.1.0)
- **Major**: Increment first, reset others (1.2.3 → 2.0.0)
- **Skip**: Proceed to push without versioning

### Step 3: Update CHANGELOG.md (if version selected)
1. Replace `## [Unreleased]` content with versioned release
2. Add today's date in format `YYYY-MM-DD`
3. Create new empty `## [Unreleased]` section above

**Before:**
```markdown
## [Unreleased]

### Added
- Feature X

## [1.0.0] - 2026-01-04
```

**After (Patch bump example):**
```markdown
## [Unreleased]

### Added

### Changed

### Fixed

## [1.0.1] - 2026-01-04

### Added
- Feature X

## [1.0.0] - 2026-01-04
```

### Step 4: Commit Changelog (if version selected)
```bash
git add CHANGELOG.md
git commit -m "chore(release): bump version to X.X.X"
```

## 3. Execute Push

```bash
git push origin $(git branch --show-current)
```

**On success:** "Successfully pushed to origin"

**On failure:** Display error, do not retry automatically

## 4. Execution Flow Summary

1. `git status --porcelain` - check uncommitted
2. **Ask**: "Uncommitted changes found. Run /commit?" (if applicable)
3. `git fetch && git log` - check if ahead of origin
4. Read `CHANGELOG.md` - check if [Unreleased] has content
5. **If has content**: Use AskUserQuestion - "Which version bump?" (Patch/Minor/Major/Skip)
6. **If version selected**: Update `CHANGELOG.md` - version Unreleased, add new Unreleased section
7. **If version selected**: `git add CHANGELOG.md && git commit` - commit changelog
8. `git push origin <branch>` - push all changes
9. Confirm success

## 5. Safety Protocols

- Never force push (`--force` or `-f`)
- Never push to protected branches without confirmation
- Always fetch before comparing with origin
- Preserve all existing changelog entries

---
Tokens: ~400 | Integrates with: commit.md