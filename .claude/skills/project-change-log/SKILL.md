# Project Change Log

Automatically maintain a CHANGELOG.md file following the Keep a Changelog standard.

## When to Use

- After creating a commit
- When `/commit` command is executed
- When user asks to update changelog
- When releasing a new version

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
