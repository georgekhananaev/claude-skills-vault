# Release Command

**IMPORTANT: This command ONLY runs when explicitly invoked via `/release`. Do NOT auto-release.**

Goal: Create a versioned release — bump CHANGELOG, regenerate manifest, commit, push, tag, and trigger npm publish via GitHub Actions.

## 1. Pre-Release Checks

### Step 1: Clean Working Tree
```bash
git status --porcelain
```

**If uncommitted changes exist:**
- Ask user: "You have uncommitted changes. Run /commit first?"
- **If NO**: Abort

### Step 2: Check Unreleased Content
- Read `CHANGELOG.md` → check if `## [Unreleased]` section has content
- **If empty**: Inform user "Nothing to release — Unreleased section is empty" → Exit

## 2. Version Selection

Use **AskUserQuestion** to prompt:

```
Question: "Which version bump?"
Options:
- Patch (+0.0.1) - Bug fixes, minor updates (Recommended)
- Minor (+0.1.0) - New features, backwards compatible
- Major (+1.0.0) - Breaking changes
```

**Calculate new version** from latest `## [X.X.X]` entry in CHANGELOG.

## 3. Update Files

### Step 1: Update CHANGELOG.md
1. Move `## [Unreleased]` content into new `## [X.X.X] - YYYY-MM-DD` section
2. Create fresh empty `## [Unreleased]` above it

### Step 2: Regenerate Manifest
```bash
node scripts/generate-manifest.js
```

This updates both `manifest.json` (repo root) and `cli/manifest.json` (npm package) with the new version.

### Step 3: Update CLI package version
```bash
cd cli && npm version X.X.X --no-git-tag-version --allow-same-version
```

### Step 4: Commit
```bash
git add CHANGELOG.md manifest.json cli/manifest.json cli/package.json
git commit -m "chore(release): bump version to X.X.X"
```

## 4. Push & Tag

### Step 1: Push commits
```bash
git push origin $(git branch --show-current)
```

### Step 2: Create and push tag
```bash
git tag vX.X.X
git push origin vX.X.X
```

This triggers `.github/workflows/npm-publish.yml` → auto-publishes to npm.

### Step 3: Verify Action
```bash
sleep 5
gh run list --limit 1
```

Report: "Tag vX.X.X pushed → npm publish Action triggered."

## 5. Execution Flow Summary

1. `git status --porcelain` - check clean
2. Read `CHANGELOG.md` - check Unreleased has content
3. **AskUserQuestion** - "Which version bump?" (Patch/Minor/Major)
4. Update `CHANGELOG.md` - version the Unreleased section
5. `node scripts/generate-manifest.js` - regenerate manifest
6. `cd cli && npm version X.X.X` - sync CLI package version
7. `git add && git commit` - commit release
8. `git push origin <branch>` - push commits
9. `git tag vX.X.X && git push origin vX.X.X` - create tag → triggers npm publish
10. `gh run list --limit 1` - verify Action triggered
11. Confirm success

## 6. Safety Protocols

- Never force push
- Never release with uncommitted changes
- Never release with empty Unreleased section
- Always regenerate manifest before tagging
- Always sync cli/package.json version with tag

---
Tokens: ~350 | Integrates with: git-push.md, npm-publish.yml
