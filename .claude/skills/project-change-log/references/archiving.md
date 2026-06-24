# Archiving — keeping CHANGELOG.md small

A single CHANGELOG.md grows without bound: one real project reached 197 releases
/ 2,508 lines / 420 KB. This reference defines how the skill keeps the main file
short by rotating old releases into per-major archive files.

## Policy

- **Keep in `CHANGELOG.md`:** the `[Unreleased]` section + the newest **20**
  released versions.
- **Archive everything older**, grouped by SemVer **major version**, into
  `changelog/CHANGELOG-<major>.x.md` (e.g. `changelog/CHANGELOG-1.x.md`).
- **Link every archive** from an `## Older releases` index at the bottom of the
  main file.
- Archives stay **newest-first**; newly rotated versions are **prepended** so the
  global order is preserved across the main file and all archives.

## File layout

```
CHANGELOG.md                 # title + intro + [Unreleased] + newest 20 + index
changelog/
  CHANGELOG-1.x.md           # all archived 1.x releases, newest-first
  CHANGELOG-2.x.md           # created the first time a 2.x release is rotated out
```

The main file ends with:

```markdown
## Older releases

Older releases are archived to keep this file small. Full history:

- [1.x releases](changelog/CHANGELOG-1.x.md)
```

## The rotation script

`scripts/rotate_changelog.py` — Python 3 standard library only, no dependencies.

**Safe by default: it performs a dry run unless you pass `--apply`.**

```bash
# Preview what would move (no writes):
python3 .claude/skills/project-change-log/scripts/rotate_changelog.py

# Actually rotate:
python3 .claude/skills/project-change-log/scripts/rotate_changelog.py --apply
```

Run it from the project root (where `CHANGELOG.md` lives), or point it at the
file with `--file`.

### Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--file PATH` | `CHANGELOG.md` | Main changelog to rotate |
| `--dir PATH` | `changelog` | Directory for archive files |
| `--keep N` | `20` | Versions to keep in the main file |
| `--apply` | _(off)_ | Write changes (omit for a dry run) |

### Behavior & guarantees

- **Idempotent.** If the file already has ≤ `--keep` versions, it reports
  "Nothing to do" and writes nothing.
- **No content loss.** Every `## [version]` section ends up in exactly one place
  (main file or an archive) — verified by header-set equality.
- **Order preserved.** Rotated versions are prepended to their archive, keeping
  newest-first across the whole history.
- **Unknown sections preserved.** Any non-version `## ` section it doesn't
  recognize is kept in the main file (with a warning), never dropped.

### Edge cases handled

- Pre-release / letter suffixes: `## [1.23.0a]`, `## [1.19.6h]`
- Hash instead of a date: `## [1.19.4] - e850122c`
- Re-running after an index and archives already exist
- A version whose major can't be parsed → `changelog/CHANGELOG-misc.md`

## When to run it

- **As the last step of a version release** — after moving `[Unreleased]` into a
  new version section, run with `--apply`. If ≤ 20 versions, it's a no-op.
- **On demand** when the file feels large.

## Adopting on an existing changelog (first-time / after a skill update)

When this skill version first lands in a project that already has a large
`CHANGELOG.md`, run a **one-time** adoption to retrofit the archive layout.
Nothing happens automatically — you trigger it once. It is **idempotent**, so
it's also safe to re-run after any future skill update; if the file is already
tidy it's a no-op.

**Step 1 — dry run, and check the detected count.** This is the important step
for an existing file: the script only archives sections that match
`## [version]`. The dry run tells you how many versions it found.

```bash
python3 .claude/skills/project-change-log/scripts/rotate_changelog.py
```

```
[DRY RUN] CHANGELOG.md: 196 version(s), keep=20.
  archive 176 version(s):
    changelog/CHANGELOG-1.x.md  <- 176 version(s) [1.19.6h … 1.4.459] (create)
```

If the reported version count looks **right**, continue. If it reports **0 or
far too few**, your changelog uses a different heading format — normalize the
version headers to `## [x.y.z] - YYYY-MM-DD` first, then re-run (see
*Troubleshooting* below). Don't `--apply` until the count looks correct.

**Step 2 — apply, then review and commit.**

```bash
python3 .claude/skills/project-change-log/scripts/rotate_changelog.py --apply
git status        # new changelog/ dir + trimmed CHANGELOG.md
git diff -- CHANGELOG.md
```

On a 197-version file this moves 176 older releases into
`changelog/CHANGELOG-1.x.md` and leaves the newest 20 + `[Unreleased]` in
`CHANGELOG.md`. **Commit the new `changelog/` directory together with the
trimmed `CHANGELOG.md`** in one commit so history stays consistent.

From then on, rotation runs as the last step of each release (a no-op until the
file again exceeds 20 versions).

### Troubleshooting an existing file

- **"Nothing to do" but the file is huge** → your version headings aren't
  `## [version]`. The script treats unrecognized `## ` sections as preamble or
  keeps them in place; it never archives them. Convert headings to the standard
  format and re-run.
- **Versions land in `CHANGELOG-misc.md`** → those version strings have no
  numeric major the script could parse (e.g. `## [next]`). Give them a real
  SemVer number or leave them — they're still preserved, just bucketed as misc.
- **Want a different location** → pass `--dir docs/changelog` (or `--dir .` to
  keep archives next to `CHANGELOG.md` with no subfolder).
- **Recover** → no special undo is needed; everything is plain files under git.
  Restore with `git checkout -- CHANGELOG.md` and remove the generated archives
  (`rm -r changelog/`, or `git checkout -- changelog/` if they were already
  committed).
