# AWS CLI — Auth, Output & Operational Patterns

Load when setting up auth, parsing output, paginating, or debugging errors.

## Auth Setup (decision)

```text
Human, org uses IAM Identity Center?  → aws configure sso   (BEST: temp creds, auto-expiry)
Human, plain IAM user?                → aws configure        (long-lived keys — least preferred)
CI/automation?                        → OIDC role (GitHub Actions) or env vars from secret store
Cross-account?                        → role_arn + source_profile in ~/.aws/config
EC2/ECS/Lambda runtime?               → instance/task role — NO keys needed
```

### IAM Identity Center (SSO)

```bash
aws configure sso          # interactive: SSO start URL, region, account, role
aws sso login --profile myprofile
aws sts get-caller-identity --profile myprofile   # verify
```

Session expired → `Token has expired` → `aws sso login --profile x`.

### Static keys

```bash
aws configure --profile myprofile   # prompts key id, secret, region, output
```

Newer CLI versions also offer `aws login` (browser-based sign-in, surfaced in
v2.35+ error hints) — check `aws login help` on the installed version.

Never paste keys into commands/args. Rotate via `iam create-access-key` +
`iam update-access-key --status Inactive` (old) → verify → `delete-access-key`.

### Profiles & precedence

Config files: `~/.aws/config` (profiles, region, sso) + `~/.aws/credentials` (keys).
Resolution order (first wins): CLI flags (`--profile`, `--region`) → env
(`AWS_PROFILE`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`…) → profile config → instance role.

Cross-account role profile:

```ini
[profile prod-admin]
role_arn = arn:aws:iam::222222222222:role/Admin
source_profile = base
mfa_serial = arn:aws:iam::111111111111:mfa/george   # if MFA-gated
region = eu-west-1
```

## JMESPath `--query` Cookbook

```bash
# instance ids only
--query 'Reservations[].Instances[].InstanceId'
# pick fields → table
--query 'Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,State:State.Name,Name:Tags[?Key==`Name`]|[0].Value}' --output table
# filter client-side
--query 'Functions[?Runtime==`python3.12`].FunctionName'
# sort + top N (largest log groups)
--query 'reverse(sort_by(logGroups,&storedBytes))[:10].[logGroupName,storedBytes]'
# scalar output w/o quotes
--output text
```

Prefer SERVER-side `--filters` (ec2/rds) or `--prefix` (s3api) when available —
less data transferred, no pagination surprises.

## Pagination

v2 auto-paginates by default — full result set returned. Control:

- `--max-items N` — cap total (returns `NextToken` to continue)
- `--starting-token <t>` — resume
- `--page-size N` — smaller API pages (throttling relief; same total)
- `--no-paginate` — first page only

## Dry-Run / Preview Matrix

| Service | Preview mechanism |
|---------|------------------|
| EC2/VPC | `--dry-run` → success = `DryRunOperation` error (exit 254 is EXPECTED) |
| S3 `cp/sync/rm/mv` | `--dryrun` |
| CloudFormation | `create-change-set` → `describe-change-set` → review → `execute-change-set` |
| IAM | `simulate-principal-policy` / `simulate-custom-policy` |
| Any command | `--generate-cli-skeleton` (input shape) / `--generate-cli-skeleton output` |
| Auto Scaling, others w/o dry-run | Describe current state first; show the diff you intend |

## Waiters & Long Ops

```bash
aws ec2 wait instance-running --instance-ids i-0abc       # blocks until state
aws cloudformation wait stack-create-complete --stack-name x
aws rds wait db-instance-available --db-instance-identifier x
```

List waiters: `aws <service> wait help`. For very long ops prefer polling
`describe-*` w/ status field in a loop (waiters time out ~40 attempts).

## Common Service Errors

| Error | Meaning | Action |
|-------|---------|--------|
| `DryRunOperation` | Dry-run SUCCEEDED (would have worked) | Proceed to real run (w/ tier gate) |
| `UnauthorizedOperation` (ec2) | IAM deny | `sts decode-authorization-message` if encoded blob present |
| `RequestLimitExceeded` / `Throttling` | Rate limit | `export AWS_MAX_ATTEMPTS=10 AWS_RETRY_MODE=adaptive` |
| `DependencyViolation` | Resource in use (sg attached, subnet busy) | Find dependents via describe-*; never force-cascade w/o confirm |
| `BucketNotEmpty` | rb on non-empty bucket | List contents; deleting them = Forbidden-tier flow |
| `OptInRequired` | Region/service not enabled | Enable region in account settings |
| `AuthFailure` | Clock skew or bad keys | Check system time; rotate keys |
| `KMSKeyDisabledException` | CMK disabled | Re-enable key (`kms enable-key`) |

## Useful Env Vars

| Var | Purpose |
|-----|---------|
| `AWS_PROFILE` | Default profile (prefer explicit `--profile` on writes) |
| `AWS_REGION` | Region override |
| `AWS_PAGER=""` | Kill the pager globally (same as `--no-cli-pager`) |
| `AWS_MAX_ATTEMPTS` / `AWS_RETRY_MODE=adaptive` | Retry tuning |
| `AWS_CLI_AUTO_PROMPT=on-partial` | Interactive command completion (human use) |
| `AWS_ENDPOINT_URL` | LocalStack/custom endpoints (v2.13+) |

## Cost-Investigation Recipe (Safe-only)

```bash
aws ce get-cost-and-usage --time-period Start=2026-05-01,End=2026-06-01 \
  --granularity MONTHLY --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE --no-cli-pager
# then drill: Key=USAGE_TYPE or Key=REGION; forecast: ce get-cost-forecast
# top spenders → describe the resources → SURFACE findings, never auto-delete
```

## Multi-Region Sweep (read-only)

```bash
for r in $(aws ec2 describe-regions --query 'Regions[].RegionName' --output text); do
  echo "== $r"; aws ec2 describe-instances --region "$r" \
    --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output text
done
```

Loops are fine for Safe ops. NEVER loop Destructive/Forbidden ops — list
first, confirm count+ids once, then act (and still no Forbidden in loops).

## LocalStack / Testing

```bash
aws --endpoint-url http://localhost:4566 s3 ls    # or AWS_ENDPOINT_URL
```

Against LocalStack, tiers may relax to Write (still announce) — confirm the
endpoint is local BEFORE relaxing anything.
