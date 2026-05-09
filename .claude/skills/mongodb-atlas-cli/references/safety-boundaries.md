# Safety Boundaries

Exactly what this skill will & won't do, and why.

## Three Tiers

### Tier 1 — Read-only (allowed, no confirmation)

Anything that returns data without modifying cluster/project state:

- Listing/describing clusters, processes, dbusers, alerts, events, snapshots, accessLists
- All `performanceAdvisor` reads (slow queries, suggested indexes, schema advice, drop hints)
- All `metrics` reads (process, database, disk)
- Log downloads
- Auth state inspection (`atlas auth whoami`)

These are safe to run in any environment, including production, repeatedly.

### Tier 2 — Additive write (allowed, requires `--confirm` + dry-run preview)

Only one operation falls in this tier:

- **`atlas clusters indexes create`**

Why allowed:
- Additive — does not modify or remove existing data/indexes
- Reversible (drop manually if needed)
- The most common output of an Atlas optimization workflow

Why gated:
- Build consumes cluster resources
- Long-running on big collections
- Wrong index spec wastes storage & write throughput

### Tier 3 — Destructive (REFUSED — never run)

Hard-blocked. Even if the user explicitly asks. Even w/ `--force`. The script will exit non-zero and print a refusal.

**Cluster lifecycle:**
- `atlas clusters delete` — destroys cluster
- `atlas clusters terminate` — same
- `atlas clusters pause` — interrupts service

**Index removal:**
- `atlas clusters indexes delete` — even when advisor recommends dropping. Atlas's drop-index suggestions can be wrong (e.g., index used by infrequent but critical query). Always verify w/ app team & drop manually.

**Backup ops that overwrite or destroy:**
- `atlas backups restore` — overwrites current cluster data
- `atlas backups snapshots delete` — removes recovery point

**Auth/network changes:**
- `atlas dbusers create/update/delete` — auth changes can lock out production
- `atlas networking peering create/delete` — connectivity disruption
- `atlas accessLists create/delete` — IP allowlist disruption

**Project/team destruction:**
- `atlas projects delete`
- `atlas teams delete`

**Generic destructive tokens** in any subcommand or flag value:
- `delete`, `drop`, `terminate`, `pause`, `restore`, `kill`, `force`, `destroy`, `remove`, `purge`

## Why Not Allow With Extra Confirmation?

Trade-off: convenience vs. blast radius. For Tier 3 ops, the cost of a mistake is orders of magnitude higher than the inconvenience of running the command manually:

| Op | Mistake cost | Correct workflow |
|----|--------------|------------------|
| Drop index | App-wide perf regression | Atlas UI w/ explicit confirmation |
| Restore snapshot | Data loss for changes since snapshot | Atlas UI, runbook, team review |
| Delete cluster | Total data loss | Should never happen via skill |
| Create dbuser | Credential spread, audit gap | IaC (Terraform) or UI |
| Modify allowlist | Production lockout | Out-of-band change w/ rollback ready |

Forcing these to be done in the Atlas UI or directly via `atlas` enforces a decision boundary the user has to cross deliberately.

## Refusal Pattern

When asked to do a Tier 3 op, the script raises `AtlasError` w/ this template:

```
REFUSED: `atlas <command>` is a destructive op blocked by this skill.
  Matched forbidden prefix: <prefix>
  Run it manually in Atlas UI or via `atlas` directly if you intend to.
```

Claude should relay this to the user verbatim and **not** wrap or sandbox the call. Don't suggest workarounds.

## What If Advisor Recommends a Tier 3 Op?

Surface the recommendation, never act on it:

> Performance Advisor suggests dropping these 3 indexes: [list].
> I won't drop them — please verify w/ your team & drop in Atlas UI.

## Defense In Depth

Two layers of guards in `_common.py`:

1. **`FORBIDDEN_PREFIXES`** — explicit deny list of subcommand chains
2. **`DESTRUCTIVE_TOKENS`** — generic scan for dangerous keywords

Both run on every `run_atlas()` call, including from `safe_index_create.py`. If a future change introduces a destructive arg, the token scan catches it.
