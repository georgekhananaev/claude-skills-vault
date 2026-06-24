---
name: project-change-log
description: Maintain a CHANGELOG.md following the Keep a Changelog standard. Use after commits, on /commit, when the user asks to update the changelog, or when releasing a version — maps conventional-commit types to Added/Changed/Fixed/Security categories. Archives old releases into per-major files (changelog/CHANGELOG-1.x.md) so the main file stays small no matter how many versions accumulate.
---

# Project Change Log

Automatically maintain a CHANGELOG.md file following the Keep a Changelog standard.

## When to Use

- After creating a commit
- When `/commit` command is executed
- When user asks to update changelog
- When releasing a new version
- When `CHANGELOG.md` has grown large (rotate old releases into archives — see [Keeping the changelog small](#keeping-the-changelog-small-archiving))

## Changelog Format

The standard format is `CHANGELOG.md` in the project root, following [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- New feature description

### Changed
- Change description

### Fixed
- Bug fix description

## [1.0.0] - 2026-01-04

### Added
- Initial release features
```

## Change Categories

| Category | Description |
|----------|-------------|
| **Added** | New features |
| **Changed** | Changes in existing functionality |
| **Deprecated** | Soon-to-be removed features |
| **Removed** | Removed features |
| **Fixed** | Bug fixes |
| **Security** | Vulnerability fixes |

## Process

### 1. Detect Changelog

Check if `CHANGELOG.md` exists in project root:
- If exists: Read current content
- If not: Create with template

### 2. Analyze Commit

Extract from the commit:
- **Type**: feat, fix, docs, etc.
- **Scope**: Affected area
- **Description**: What changed
- **Date**: Current date (YYYY-MM-DD)
- **Author**: From git config

### 3. Map Commit Type to Category

| Commit Type | Changelog Category |
|-------------|-------------------|
| `feat` | Added |
| `fix` | Fixed |
| `docs` | Changed |
| `style` | Changed |
| `refactor` | Changed |
| `perf` | Changed |
| `test` | Changed |
| `build` | Changed |
| `ci` | Changed |
| `chore` | Changed |
| `security` | Security |
| `deprecate` | Deprecated |
| `remove` | Removed |

### 4. Update Changelog

Add entry under `[Unreleased]` section in appropriate category:

```markdown
## [Unreleased]

### Added
- New entry here with description
```

### 5. Version Release

When releasing a version:
1. Move `[Unreleased]` content to new version section
2. Add version number and date
3. Create new empty `[Unreleased]` section
4. **Rotate old releases** so the file stays small — run the archive script (it's a no-op until there are more than 20 versions):

```bash
python3 .claude/skills/project-change-log/scripts/rotate_changelog.py --apply
```

## Keeping the changelog small (archiving)

A single `CHANGELOG.md` grows without bound — one real project reached 197
releases / 2,508 lines / 420 KB. To keep it readable, rotate old releases into
per-major archive files.

**Policy:** keep `[Unreleased]` + the newest **20** versions in `CHANGELOG.md`;
move older versions into `changelog/CHANGELOG-<major>.x.md` (e.g.
`changelog/CHANGELOG-1.x.md`), linked from an `## Older releases` index at the
bottom of the main file.

```
CHANGELOG.md                 # title + intro + [Unreleased] + newest 20 + index
changelog/
  CHANGELOG-1.x.md           # archived 1.x releases, newest-first
  CHANGELOG-2.x.md           # created when a 2.x release is first rotated out
```

Use the helper script — **safe by default (dry run unless `--apply`)**, Python 3
stdlib only, idempotent, and guaranteed not to drop or duplicate any release:

```bash
# Preview what would move (no writes):
python3 .claude/skills/project-change-log/scripts/rotate_changelog.py

# Rotate for real:
python3 .claude/skills/project-change-log/scripts/rotate_changelog.py --apply
```

Run it as the last step of a version release (no-op below 20 versions) or any
time the file feels large.

**First-time adoption on an existing project** (e.g. after this skill is added
or updated): run the **dry run first** and confirm the reported version count
looks right, then `--apply` once and commit the new `changelog/` directory with
the trimmed `CHANGELOG.md` in a single commit. It's idempotent, so re-running
after later skill updates is safe. If the dry run reports `0`/too few versions,
the file uses a non-standard heading format — normalize headings to
`## [x.y.z] - YYYY-MM-DD` first. Full steps + troubleshooting:
[references/archiving.md](references/archiving.md).

Flags: `--keep N` (default 20), `--dir changelog`, `--file CHANGELOG.md`. Full
details, behavior guarantees, and edge cases: see
[references/archiving.md](references/archiving.md).

## Entry Format

Each entry should be:
- One line per change
- Start with capital letter
- No period at end
- Include scope if relevant: `**scope**: description`

**Examples:**
```markdown
### Added
- **auth**: OAuth2 login with Google and GitHub
- User profile settings page
- Dark mode toggle

### Fixed
- **api**: Handle null response in user endpoint
- Memory leak in websocket connections
```

## Template

Initial CHANGELOG.md template:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed

### Fixed

```

## Integration with Commit

After each commit:
1. Parse commit message for type and description
2. Determine changelog category
3. Add entry under `[Unreleased]`
4. Stage CHANGELOG.md (do not create separate commit)

## Examples

### Example 1: Feature Commit

**Commit:** `feat(auth): add OAuth2 login support`

**Changelog Entry:**
```markdown
### Added
- **auth**: OAuth2 login support
```

### Example 2: Bug Fix

**Commit:** `fix(api): handle null response in user endpoint`

**Changelog Entry:**
```markdown
### Fixed
- **api**: Handle null response in user endpoint
```

### Example 3: Version Release

Before:
```markdown
## [Unreleased]

### Added
- Feature A
- Feature B

### Fixed
- Bug fix X
```

After releasing v1.2.0:
```markdown
## [Unreleased]

## [1.2.0] - 2026-01-04

### Added
- Feature A
- Feature B

### Fixed
- Bug fix X
```
