# Atlas CLI Command Map

Authoritative reference for the `atlas` subcommands this skill uses or refuses. Mirrors `mongodb.com/docs/atlas/cli/current/`.

## Authentication

| Command | Purpose | Permission |
|---------|---------|------------|
| `atlas auth login` | Browser OAuth login | none |
| `atlas auth whoami` | Show current identity | none |
| `atlas config init` | Walk through profile setup | none |
| `atlas config ls` | List profiles | none |

## Read — Allowed

| Command | Purpose | Min Role |
|---------|---------|----------|
| `atlas clusters list` | List clusters in project | Project Read Only |
| `atlas clusters describe <name>` | Cluster detail | Project Read Only |
| `atlas processes list` | List mongod/mongos hosts (gives `processName` for advisor) | Project Read Only |
| `atlas performanceAdvisor namespaces` | Hot namespaces | Project Read Only |
| `atlas performanceAdvisor slowQueryLogs list --processName <h:p>` | Slow query log lines | Project Data Access Read/Write |
| `atlas performanceAdvisor suggestedIndexes list --processName <h:p>` | Index suggestions | Project Read Only |
| `atlas api performanceAdvisor listSchemaAdvice --clusterName <n> --groupId <p>` | Schema recs | Project Read Only |
| `atlas api performanceAdvisor listDropIndexSuggestions --clusterName <n> --groupId <p>` | Drop index hints (informational only) | Project Read Only |
| `atlas metrics processes <h:p> --granularity PT1M --period PT1H` | Process metrics | Project Read Only |
| `atlas metrics databases <h:p> --database <db>` | Per-DB metrics | Project Read Only |
| `atlas metrics disks <h:p> --partitionName <part>` | Disk metrics | Project Read Only |
| `atlas logs download <h:p> mongodb.gz` | Mongod logs | Project Read Only |
| `atlas alerts list` | Active alerts | Project Read Only |
| `atlas events list` | Audit events | Project Read Only |
| `atlas backups snapshots list --clusterName <n>` | List snapshots | Project Read Only |
| `atlas dbusers list` | List users (no secrets) | Project Read Only |
| `atlas accessLists list` | IP allowlist | Project Read Only |

## Write — Additive Only (gated by `--confirm`)

| Command | Purpose | Min Role |
|---------|---------|----------|
| `atlas clusters indexes create --clusterName <n> --db <db> --collection <c> --key f:1` | Create index | Project Data Access Admin |

## REFUSED — Never Run

| Command | Why blocked |
|---------|-------------|
| `atlas clusters delete` | Deletes cluster |
| `atlas clusters terminate` | Terminates cluster |
| `atlas clusters pause` | Pauses cluster |
| `atlas clusters indexes delete` | Drops index — even when advisor suggests it |
| `atlas backups restore` | Overwrites data |
| `atlas backups snapshots delete` | Removes recovery point |
| `atlas dbusers create/update/delete` | Auth changes can lock prod |
| `atlas networking peering create/delete` | Connectivity change |
| `atlas accessLists create/delete` | IP allowlist change |
| `atlas projects delete` | Deletes project |
| Any flag/subcommand containing `delete`, `drop`, `terminate`, `pause`, `restore`, `kill`, `force`, `destroy`, `remove`, `purge` | Defense in depth |

## Common Flags

| Flag | Description |
|------|-------------|
| `--projectId <hex>` | Override project from config/env |
| `--output json` | Machine-readable output |
| `--profile <name>` | Use a named profile from config |

## Process Name Format

Performance Advisor commands need `--processName host:port`. Get it w/:

```bash
atlas processes list --output json | jq -r '.results[].id'
# atlas-abc123-shard-00-00.xyz.mongodb.net:27017
```

The skill's `_common.py:primary_process()` resolves this automatically.

## Granularity & Period (ISO 8601)

| Granularity | Period range |
|-------------|--------------|
| `PT10S` | up to 1h |
| `PT1M` | up to 8h |
| `PT5M` | up to 2 days |
| `PT1H` | up to 30 days |
| `P1D` | up to 2 years |

Common periods: `PT1H` (1h), `P1D` (1d), `P7D` (7d), `P30D` (30d).

## Sources

- https://www.mongodb.com/docs/atlas/cli/current/
- https://www.mongodb.com/docs/atlas/cli/current/command/atlas-performanceAdvisor/
- https://www.mongodb.com/docs/atlas/cli/current/command/atlas-clusters-indexes-create/
- https://www.mongodb.com/docs/atlas/cli/current/command/atlas-metrics-processes/
