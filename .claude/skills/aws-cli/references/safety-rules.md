# AWS CLI — Safety Rules

Full risk classification & confirmation protocols. Load when handling
Destructive/Forbidden ops. The deterministic source of truth is
`scripts/aws_risk.py` — these rules explain the WHY and the human protocol.

## Four Tiers

### Tier 1 — Safe (read-only, execute immediately)

Verbs: `describe-*`, `get-*`, `list-*`, `head-*`, `search-*`, `lookup-*`,
`scan`, `query`, `batch-get-*`, `simulate-*`, `validate-*`, `check-*`,
`wait`, `help`. Plus: `s3 ls`, `sts get-caller-identity`, `logs tail`,
`logs filter-log-events`, `configure list/get`, `ce get-cost-and-usage`,
anything w/ `--dry-run` or `--generate-cli-skeleton`.

Caveat: reads of SECRETS are technically safe but treat output as sensitive —
`secretsmanager get-secret-value`, `ssm get-parameter --with-decryption`,
`iam create-access-key` output. Never print to chat unless explicitly asked.

### Tier 2 — Write (inform, then execute)

Reversible mutations, no live-traffic/cost/data-loss impact. State target
account + region + what changes, then run:

`create-*` (free resources: sg, tags, log groups, queues, topics, roles*,
policies*), `put-*`, `add-*`, `attach-*`, `associate-*`, `tag-*`/`untag-*`,
`enable-*`, `upload-*`, `register-*`, `import-*`, `s3 cp/mv/sync/mb/presign`,
`lambda update-function-code/configuration`, `start-*` (existing resources),
`sns publish`, `sqs send-message`, `lambda invoke`, `sts assume-role`,
`ecs update-service` (scaling), `restore-*` (recovery direction).

*IAM role/policy creation is Write, but ATTACHING broad policies escalates —
see IAM section below.

### Tier 3 — Destructive (AskUserQuestion required BEFORE running)

Removes resources, affects live traffic, causes downtime, or starts billing:

| Command | Why gated |
|---------|-----------|
| `delete-*` (most resources) | Removes infra; some recoverable, many not |
| `ec2 terminate-instances` | Instance gone; instance-store data lost |
| `ec2 stop-instances` / `reboot-instances` | Live service interruption |
| `ec2 run-instances`, `request-spot-*` | Starts hourly billing |
| `ec2 create-nat-gateway`, `allocate-hosts`, `create-capacity-reservation` | Ongoing cost while held |
| `rds create-db-instance/cluster`, `redshift/elasticache/eks/opensearch create-*`, `elbv2 create-load-balancer` | Ongoing cost |
| `rds modify-db-instance/cluster`, `upgrade-db-instance` | Possible reboot/downtime; engine upgrades often one-way |
| `eks update-cluster-version` | IRREVERSIBLE — no downgrade |
| `dynamodb update-table` | Capacity/billing-mode change on live table |
| `route53 change-resource-record-sets` | Live DNS — can break mail/site |
| `cloudfront update/delete-distribution` | Live CDN traffic |
| `apigateway delete-rest-api`, `apigatewayv2 delete-api` | Endpoints die |
| `lambda delete-function` | Function gone (redeployable if source kept) |
| `s3 rm --recursive`, `s3api delete-objects` | Bulk object deletion |
| `s3 sync --delete` | Deletes destination objects missing from source |
| `cloudformation update-stack` / `deploy` / `execute-change-set` | Applies changes to live stack resources (`--no-execute-changeset` → Write) |
| `ec2 revoke-security-group-*`, `detach-*`, `disassociate-*` | Connectivity breaks |
| Any sg/ACL/policy change containing `0.0.0.0/0` or `::/0` | Exposes resource to entire internet |
| `--acl public-read[-write]`, policy w/ `"Principal": "*"`, weakening `put-public-access-block` | Makes data PUBLIC |
| `iam update-assume-role-policy`, `kms put-key-policy` | Lockout risk — data/role unreachable |
| `ssm send-command`, `ecs execute-command` | Arbitrary command execution on instances/containers |
| `ecs delete-service`, `eks delete-nodegroup`, `autoscaling delete-auto-scaling-group` | Running workloads die |
| `--desired-count 0` / scale-to-zero | Effective stop of a live service |
| `restore-*` (rds/redshift/elasticache/dynamodb/…) | Provisions a NEW billable data store |
| `organizations create-account` | Member accounts are very hard to remove |
| `events disable-rule`, `scheduler delete-schedule` | Automation silently stops |

### Tier 4 — Forbidden (triple typed confirmation, NEVER auto-confirm)

Permanent data loss, money, account-level, or protection-removal. Never pass
skip flags; "force it"/"yolo" does NOT skip steps.

| Command | Why |
|---------|-----|
| `account close-account` | Closes the AWS account |
| `organizations leave-organization` / `delete-organization` / `remove-account-from-organization` / `close-account` | Org structure — catastrophic |
| `iam delete-user/role/group/login-profile/account-alias/account-password-policy` | Identity destruction, lockout |
| `iam deactivate-mfa-device` / `delete-virtual-mfa-device` | Removes MFA protection |
| Attaching `AdministratorAccess` (or equivalent `*:*` policy) | Privilege escalation |
| `kms schedule-key-deletion` / `disable-key` | Data encrypted under key → unrecoverable |
| `cloudformation delete-stack` | Deletes EVERY stack-managed resource |
| `s3 rb --force` / `s3api delete-bucket` | Bucket + contents gone |
| `dynamodb delete-table` / `delete-backup` | Table + items / backup gone |
| `rds delete-db-instance/cluster --skip-final-snapshot` | DB gone, NO backup |
| `redshift delete-cluster --skip-final-cluster-snapshot` | Same |
| `secretsmanager delete-secret --force-delete-without-recovery` | No recovery window |
| `ec2 delete-snapshot`, `rds delete-db-snapshot/cluster-snapshot`, `elasticache delete-snapshot`, `backup delete-backup-vault/recovery-point` | Deletes the BACKUPS |
| `route53 delete-hosted-zone` | Domain can go offline |
| `cloudtrail delete-trail` / `stop-logging` | Kills the audit trail |
| `guardduty delete-detector`, `securityhub disable-security-hub`, `config delete/stop-configuration-recorder` | Disables security monitoring |
| `ec2 purchase-*`, `savingsplans create-savings-plan` | Money; 1–3 yr commitments |
| `route53domains register-domain/transfer-domain/renew-domain` | Money |
| Bulk destructive loops (xargs/for + any Tier 3/4 op) | Multiplies blast radius |

## IAM Escalation Rules

- Creating roles/policies → Write.
- Attaching scoped policies → Write (show the policy summary first).
- Attaching `AdministratorAccess`, `IAMFullAccess`, or any policy w/
  `"Action": "*"` + `"Resource": "*"` → **Forbidden-level confirm**.
- `put-user-policy`/`put-role-policy` inline JSON: READ the JSON before
  running; wildcard actions on `*` resources escalate as above.
- Trust-policy edits (`update-assume-role-policy`) → Destructive: a wrong
  principal locks out the role or hands it to a foreign account.

## Cost Rules

- Anything starting hourly billing → Destructive (confirm w/ rough cost:
  e.g. NAT gateway ≈ $32/mo + data; `db.r6g.large` ≈ $230/mo).
- Purchases/commitments (RI, Savings Plan, domains, capacity blocks) →
  Forbidden tier.
- When the user asks "why is my bill high" → `ce get-cost-and-usage` (Safe);
  NEVER auto-delete cost findings — surface, don't act.

## Confirmation Templates

### Destructive — AskUserQuestion

Always include: resource id+name, ACCOUNT, REGION, blast radius, reversibility.

```text
Question: "Delete log group /aws/lambda/prod-api (account 1234…, us-east-1)?
           All retained logs are lost."
Options:
  - "Delete it"        → aws logs delete-log-group --log-group-name …
  - "Export to S3 first" → aws logs create-export-task …
  - "Cancel"
```

### Forbidden — Triple-Confirmation Protocol

1. **Warn:** exactly what is permanent/costly + blast radius (e.g. "Deleting
   stack `prod-vpc` deletes its VPC, subnets, NAT gateways, and route tables —
   anything running inside loses networking").
2. **Typed confirmation:** user types the resource name or `DELETE`/`BUY`/
   `CLOSE`. A thumbs-up or "yes" is not enough.
3. **Final confirm:** restate the exact command verbatim (account + region
   visible), ask once more, then run. Never add skip/force flags yourself.

Any step unanswered/ambiguous → **do not run**. Offer the AWS Console instead.

## Hard Rules

- Verify identity (`sts get-caller-identity`) + region before ANY Write+ op.
- Never run a Forbidden op inside a script/loop/xargs. The classifier splits
  compound commands (`&&`, `;`, `|`) and escalates xargs/loops over mutating
  ops — do not try to sneak a delete behind a safe first command.
- Never display secret values, access keys, or session tokens in output.
- Never create access keys for the root user; flag root-credential usage.
- When an audit/cost review suggests deleting something → surface, don't act.
- Prefer reversible alternative when one exists (stop vs terminate, disable
  vs delete, snapshot-then-delete, 30-day recovery window on secrets).
- Before deleting anything stateful: check for a backup/snapshot; offer to
  create one first.

## Refusal Pattern

```text
REFUSED: `aws <command>` is permanent/costly/protection-removing.
  I won't skip confirmation. Either (1) walk the confirmation steps,
  or (2) run it yourself in the AWS Console where guardrails apply.
```
