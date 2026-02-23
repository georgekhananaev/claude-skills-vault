# Commit Command

**IMPORTANT: This command ONLY runs when explicitly invoked via `/commit`. Do NOT auto-commit after code modifications. Wait for user to explicitly run `/commit`.**

Goal: Safe, attributed git commit for the configured git user.

## 1. Identity & Attribution
- **Author**: Use `git config user.name` & `git config user.email` (linked GitHub account)
- **Credit**: No co-authors/AI attribution unless requested

## 2. Safety Protocols

**Forbidden Files:**
- Secrets: `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa`, `secrets.*`, `credentials.*`
- Logs: `*.log`, `npm-debug.log`, `yarn-error.log`
- System: `.DS_Store`, `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.venv/`

**Critical Flags:**
- No `--no-verify` (hooks must pass)
- No `--no-gpg-sign` (sign if GPG configured)
- No `--amend` (unless fixing immediate prev commit)

## 3. Execution Flow

1. `git status` - check state
2. `git diff` - review (**stop** if secrets/debug found)
3. Stage: `git add <file>` (use `-p` for mixed changes, avoid `git add .` w/ junk)
4. Construct message (Conventional Commits)
5. `git commit -m "..."`
6. `git status` - verify

## 4. Commit Message Standard

**Format**: `<type>(<scope>): <description>`

| Type | Desc |
|------|------|
| feat | new feature |
| fix | bug fix |
| docs | docs only |
| style | formatting |
| refactor | no fix/feat |
| perf | performance |
| test | tests |
| build | build/deps |
| ci | CI config |
| chore | other |
| revert | revert commit |

**Rules**: Imperative mood, no period, max 72 chars, scope opt but recommended

## 5. Grouping

- **Atomic**: Split unrelated changes into separate commits
- **Ask**: "Changes in X & Y. Separate commits?"

## 6. Changelog (REQUIRED)

After EVERY commit → update `CHANGELOG.md`

### If CHANGELOG.md missing, create:

```markdown
# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/), [SemVer](https://semver.org/)

## [Unreleased]

### Added
### Changed
### Fixed
```

### Type → Category Map

| Type | Category |
|------|----------|
| feat | Added |
| fix | Fixed |
| docs/style/refactor/perf/test/build/ci/chore | Changed |
| security | Security |
| deprecate | Deprecated |
| remove | Removed |

### Entry Format

- w/ scope: `- **scope**: Description`
- w/o scope: `- Description`

### Commit Changelog

```bash
git add CHANGELOG.md
git commit --amend --no-edit
```

**Ref**: `.claude/skills/project-change-log/SKILL.md`

## 7. README Updates

### When to Update:
- `feat`: usage/API/feature docs
- Breaking changes: install/config/migration
- New deps: requirements
- New commands: usage section
- Deprecated: mark in docs

### Skip Update:
- Bug fixes (no behavior change)
- Internal refactors
- Test additions
- Style changes

### If Needed:
1. Ask: "README needs updating?"
2. If YES: targeted updates only
3. Commit: `docs(readme): update for <change>`

---
Original: ~1200 tokens | Compressed: ~550 tokens | Saved: ~54%