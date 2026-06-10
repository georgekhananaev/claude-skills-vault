---
name: aws-cli
description: Safety-first AWS CLI v2 skill for full control of AWS from the terminal — EC2, S3, IAM, Lambda, RDS, DynamoDB, CloudFormation, Route 53, EKS/ECS, logs, billing & 300+ services. Classifies every command by risk tier via a deterministic classifier script and gates destructive/breaking/cost-incurring ops behind AskUserQuestion confirmation. Account/region/profile preflight prevents wrong-account accidents. Use when running, planning, or debugging any `aws` command.
author: George Khananaev
---

# AWS CLI

Safety-first wrapper for AWS CLI v2 (`aws`). Every command is classified by risk tier BEFORE execution — full AWS control, w/ anything irreversible, breaking, or cost-incurring gated behind explicit `AskUserQuestion` confirmation. Blast radius on AWS is an entire company's infra: wrong account/region/flag can destroy data, break prod, or spend real money.

## When to Use

- Run/inspect any AWS service: EC2, S3, IAM, Lambda, RDS, DynamoDB, CloudFormation, Route 53, ECS/EKS, CloudFront, SQS/SNS, CloudWatch, KMS, Secrets Manager, …
- Audit resources, costs, security posture; tail logs; query w/ `--query` (JMESPath)
- Deploy/update infra, manage env config, rotate creds, debug failing calls
- Set up auth: profiles, IAM Identity Center (SSO), assume-role, MFA

## Prerequisites (run once per session)

```bash
bash scripts/aws_preflight.sh [profile]
```

Reports version, profiles, region, and the **active identity** (`sts get-caller-identity`). NEVER run a write op w/o knowing which account+region you're pointed at. No profiles configured → guide setup via [references/patterns.md](references/patterns.md) (keys vs SSO).

## Safety Model

| Tier | Action Required | Examples |
|------|----------------|----------|
| **Safe** | Execute immediately | `describe-*`, `get-*`, `list-*`, `s3 ls`, `sts get-caller-identity`, `logs tail`, any `--dry-run` |
| **Write** | Inform user, then execute | `create-*`, `put-*`, `tag-*`, `lambda update-function-code`, `s3 cp/sync` |
| **Destructive** | `AskUserQuestion` BEFORE executing | `delete-*`, `terminate-instances`, `stop-*`, `run-instances` (cost), `modify-db-instance` (downtime), `change-resource-record-sets` (live DNS), sg rules w/ `0.0.0.0/0` |
| **Forbidden** | Triple typed confirmation, NEVER auto-confirm | `close-account`, IAM user/role deletion, `kms schedule-key-deletion`, `delete-stack`, `s3 rb --force`, `delete-db-instance --skip-final-snapshot`, snapshot/backup deletion, disabling CloudTrail/GuardDuty, purchases (RIs, Savings Plans, domains) |

Full classification + per-service rules: [references/safety-rules.md](references/safety-rules.md).

## Decision Flow

```text
Command received
  → bash scripts/aws_preflight.sh        (once per session — identity/region)
  → python3 scripts/aws_risk.py "<cmd>"  (deterministic tier + reason)
  → Safe?        Execute immediately
  → Write?       State target account/region + what changes → execute
  → Destructive? AskUserQuestion (incl. account, region, resource, blast radius) → execute or cancel
  → Forbidden?   Warn → typed confirmation → final confirm → execute or cancel
On failure → Self-Healing (aws <svc> <op> help → docs URI)
```

The classifier is advisory — apply judgment on top (a "write" against prod during business hours may still deserve a question). When the user's request implies a **breaking change** (engine upgrade, version bump, policy change, capacity change, anything w/ downtime or no rollback), ALWAYS `AskUserQuestion` first even if the verb looks mild.

## Risk Classifier

```bash
python3 scripts/aws_risk.py "aws ec2 terminate-instances --instance-ids i-0abc"
# DESTRUCTIVE: Terminates instances — instance-store data is gone [ec2 terminate-instances]
# exit codes: 0=safe 10=write 20=destructive 30=forbidden
```

Verb-pattern based (describe/get/list→safe, create/put/update→write, delete/terminate/stop→destructive) + ~80 explicit overrides for cost, breaking, security & account-level ops. Escalation-only: overrides never lower a tier (sole exception: a 3-entry audited list of read-only ops w/ scary verbs, e.g. `logs start-query`).

Also catches:

- **Compound commands**: splits on `&&`, `;`, `|`, `$()` — EVERY aws invocation classified, highest tier wins (quoted JMESPath pipes survive intact)
- **Bulk loops**: `xargs`/`for`/`while` + destructive op → forbidden; + write op → destructive
- **Public exposure**: `0.0.0.0/0`, `--acl public-read`, `"Principal": "*"`, weakening `put-public-access-block`
- **Admin grants**: `AdministratorAccess`/`IAMFullAccess` ARNs, inline `"Action":"*"` + `"Resource":"*"` policies
- **Hidden cost/impact**: `restore-*` into new billable stores, `--desired-count 0` (scale-to-zero), `s3 sync --delete`
- Extracts `--profile`/`--region` into the output for the confirmation prompt

## Forbidden Ops (never auto-confirm)

| Command | Why |
|---------|-----|
| `aws account close-account` / `organizations leave-organization` | Account-level — catastrophic |
| `iam delete-user/role/group`, `deactivate-mfa-device` | Identity destruction, lockout risk |
| `kms schedule-key-deletion` / `disable-key` | All data encrypted under the key → unrecoverable |
| `cloudformation delete-stack` | Deletes EVERY resource the stack manages |
| `s3 rb --force` / `s3api delete-bucket`, `dynamodb delete-table` | Bulk permanent data loss |
| `rds delete-db-instance --skip-final-snapshot` | DB gone w/ NO backup |
| `ec2 delete-snapshot`, `rds delete-db-snapshot`, `backup delete-*` | Deletes the backups themselves |
| `cloudtrail delete-trail/stop-logging`, `guardduty delete-detector` | Removes audit/security monitoring |
| RI/Savings-Plan purchases, `route53domains register-domain` | Spends real money, multi-year commitments |
| Bulk destructive loops (`xargs … delete`) | Multiplies blast radius |

## AskUserQuestion Integration

For **Destructive** ops, always show account, region & resource; include a "Cancel" option:

```text
Q: "Terminate i-0abc123 (prod-api, account 1234…, eu-west-1)?"
  - "Terminate it" — aws ec2 terminate-instances --instance-ids i-0abc123
  - "Stop instead (reversible)" — aws ec2 stop-instances --instance-ids i-0abc123
  - "Cancel"

Q: "Upgrade RDS prod-db to engine 16.4? Causes downtime; downgrade NOT possible."
  - "Upgrade now" / "Upgrade in maintenance window (--no-apply-immediately)" / "Cancel"
```

Also ask (not just for deletes) when: choosing between profiles/accounts, picking a region for new resources, anything creating ongoing cost, IAM policy changes, version upgrades, or ambiguous resource matches (multiple instances match a name). Forbidden ops → triple-confirmation protocol in [references/safety-rules.md](references/safety-rules.md).

## Wrong-Account/Region Guard

#1 real-world AWS accident. Before EVERY Write+ op:

1. `aws sts get-caller-identity` (or trust session preflight) — confirm account
2. Confirm region: explicit `--region` beats env beats profile default. New resources default to the profile region — state it
3. Multi-profile setups: prefer explicit `--profile X --region Y` on mutating commands over ambient env

## Dry-Run & Preview

Prefer previews before mutating: EC2/VPC support `--dry-run` (returns `DryRunOperation` on success); CloudFormation → `deploy --no-execute-changeset` / `create-change-set` then review; IAM → `simulate-principal-policy`; S3 sync/rm → `--dryrun`; any command → `--generate-cli-skeleton` to inspect shape w/o executing.

## Self-Healing

CLI surface is huge & evolves; on any error: read the message → `aws <service> <op> help` (offline, authoritative for the installed version) → if still unclear, WebFetch the v2 reference:

- Per-command: `https://awscli.amazonaws.com/v2/documentation/api/latest/reference/<service>/<operation>.html`
- Index: https://awscli.amazonaws.com/v2/documentation/api/latest/reference/index.html
- Userguide: https://docs.aws.amazon.com/cli/latest/userguide/
- Service errors (`AccessDenied`, throttling, etc.): see [references/patterns.md](references/patterns.md)

Service/command map + doc URIs: [references/services.md](references/services.md).

## Output & Querying

| Need | Flag |
|------|------|
| Machine-readable | `--output json` (pipe to `jq` or use `--query`) |
| Human table | `--output table` |
| Filter server-side | `--filters Name=…,Values=…` (cheaper than client-side) |
| Filter client-side | `--query '<JMESPath>'` e.g. `'Reservations[].Instances[].InstanceId'` |
| No pager | `--no-cli-pager` (ALWAYS append for non-interactive runs) |
| Big lists | auto-paginated; tune w/ `--max-items`, `--page-size` |

JMESPath cookbook + pagination details: [references/patterns.md](references/patterns.md).

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Unable to locate credentials` | No profile/env creds | `aws configure` / `aws configure sso`, or `export AWS_PROFILE=x` |
| `Token has expired` / `ExpiredToken` | SSO/STS session ended | `aws sso login --profile x` |
| `AccessDenied` / `UnauthorizedOperation` | Missing IAM permission | Decode w/ `sts decode-authorization-message` if encoded; check policy |
| `InvalidClientTokenId` | Deactivated/wrong keys | Rotate keys in IAM |
| `Could not connect to the endpoint URL` | Wrong/missing region | Set `--region`; verify service exists in that region |
| `ThrottlingException` / `Rate exceeded` | API rate limits | Retry w/ backoff; CLI retries automatically (`AWS_MAX_ATTEMPTS`) |
| `ValidationError`/`InvalidParameterValue` | Bad arg shape | `aws <svc> <op> help`; `--generate-cli-skeleton` for the schema |

## Shell Safety

- ALWAYS `--no-cli-pager` (or pipe `| cat`) — aws v2 invokes a pager by default
- Quote JSON args in single quotes; for complex JSON prefer `file://params.json`
- NEVER echo secrets: `secretsmanager get-secret-value`, `ssm get-parameter --with-decryption` → redirect to file/var, never display unless asked
- NEVER put access keys on the command line; use profiles/env
- No `--force`-style skip flags on Destructive/Forbidden tiers w/o the confirmation flow
- Bulk ops: print the resource list FIRST, confirm once w/ exact count, only then loop

## Integration

Pairs w/: **terraform** (IaC instead of imperative changes — prefer for repeatable infra), **github-cli** (CI/CD wiring), **mongodb-atlas-cli** / **supabase-cli** (other data planes), **owasp-security** / **trailofbits-security** (security audits of what the CLI finds), **file-converter** (transform exported JSON/CSV).
