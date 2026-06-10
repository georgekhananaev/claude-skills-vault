# AWS CLI — Service & Command Map

Most-used services w/ key commands, risk tier & doc URIs for self-healing.
Per-command doc: `https://awscli.amazonaws.com/v2/documentation/api/latest/reference/<service>/<operation>.html`.
Offline (preferred, matches installed version): `aws <service> <operation> help`.

Tiers: **S**=Safe · **W**=Write · **D**=Destructive · **F**=Forbidden
(see [safety-rules.md](safety-rules.md)).

## Identity & Session (sts, iam, sso)

| Command | Tier | Purpose |
|---------|------|---------|
| `sts get-caller-identity` | S | Who am I (account, ARN) — run before any write |
| `sts assume-role --role-arn … --role-session-name …` | W | Temp creds for a role |
| `sts decode-authorization-message --encoded-message …` | S | Decode AccessDenied detail |
| `iam list-users/roles/policies`, `get-role`, `list-attached-role-policies` | S | Inspect IAM |
| `iam simulate-principal-policy` | S | Test permissions w/o executing |
| `iam create-role/policy`, `put-role-policy` | W | Create identity resources (read JSON first) |
| `iam attach-role-policy --policy-arn …` | W/F | F if AdministratorAccess or `*:*` |
| `iam create-access-key` | W | New key — show only on request, never log |
| `iam delete-user/role/group`, `deactivate-mfa-device` | F | Identity destruction |
| `sso login / logout`, `configure sso` | W | Identity Center session |

## EC2 & VPC

| Command | Tier | Purpose |
|---------|------|---------|
| `ec2 describe-instances [--filters Name=tag:Name,Values=x]` | S | List/find instances |
| `ec2 describe-security-groups/subnets/vpcs/volumes/snapshots` | S | Inspect networking/storage |
| `ec2 run-instances --image-id … --instance-type …` | D | Launch (billing starts) |
| `ec2 start-instances` | W | Start existing (cost resumes — say so) |
| `ec2 stop-instances` / `reboot-instances` | D | Service interruption |
| `ec2 terminate-instances` | D | Instance gone; instance-store data lost |
| `ec2 create-security-group`, `authorize-security-group-ingress/egress` | W | D if `0.0.0.0/0` |
| `ec2 revoke-security-group-ingress/egress` | D | May cut live connectivity |
| `ec2 create-snapshot`, `create-image` | W | Backups — encourage before risky ops |
| `ec2 delete-snapshot` | F | Deletes a backup |
| `ec2 create-nat-gateway`, `allocate-address` | D/W | NAT bills hourly; EIP cheap but billed when idle |
| `ec2 modify-instance-attribute` | D | Live change (type, sg, user-data) |

## S3 (high-level `s3` + low-level `s3api`)

| Command | Tier | Purpose |
|---------|------|---------|
| `s3 ls [s3://bucket/prefix]` | S | List buckets/objects |
| `s3 cp/sync <src> <dst> [--dryrun]` | W | Copy/sync (use `--dryrun` first on big syncs) |
| `s3 sync --delete` | D | Also DELETES dest objects missing from source |
| `s3 mv` | W | Copy + delete source — mention the delete |
| `s3 rm s3://… [--recursive]` | D | Delete objects (recursive = bulk) |
| `s3 mb s3://name` / `s3 rb` | W / D | Make / remove (empty) bucket |
| `s3 rb --force` | F | Bucket AND contents gone |
| `s3 presign s3://… [--expires-in N]` | W | Shareable URL — grants access |
| `s3api get-bucket-policy/encryption/versioning/public-access-block` | S | Audit bucket config |
| `s3api put-public-access-block` | W | D if DISABLING the block (public exposure) |
| `s3api put-bucket-policy` | W | D if policy grants `"Principal": "*"` |
| `s3api delete-bucket` | F | Bucket gone |

## Lambda, Logs & Events

| Command | Tier | Purpose |
|---------|------|---------|
| `lambda list-functions`, `get-function --function-name x` | S | Inspect |
| `lambda invoke --function-name x out.json` | W | Executes code (side effects possible) |
| `lambda update-function-code --zip-file fileb://…` | W | Deploy code |
| `lambda update-function-configuration` | W | Env vars, memory, timeout |
| `lambda delete-function` | D | Function gone |
| `logs tail /aws/lambda/x --follow --since 1h` | S | Live logs (best debug tool) |
| `logs filter-log-events --log-group-name … --filter-pattern ERROR` | S | Search logs |
| `logs delete-log-group` | D | Retained logs lost |
| `events list-rules` / `put-rule` / `disable-rule` | S/W/D | Scheduled automation |

## RDS & DynamoDB

| Command | Tier | Purpose |
|---------|------|---------|
| `rds describe-db-instances/clusters/snapshots` | S | Inspect |
| `rds create-db-snapshot` | W | Backup — do this BEFORE modify/delete |
| `rds create-db-instance/cluster` | D | Billing starts |
| `rds modify-db-instance [--no-apply-immediately]` | D | Possible reboot; prefer maintenance window |
| `rds delete-db-instance --final-db-snapshot-identifier x` | D | Delete WITH backup |
| `rds delete-db-instance --skip-final-snapshot` | F | Delete WITHOUT backup |
| `rds delete-db-snapshot` | F | Deletes the backup |
| `dynamodb list-tables`, `describe-table`, `scan/query` | S | Inspect (scan reads RCUs — note on huge tables) |
| `dynamodb put-item/update-item/batch-write-item` | W | Data writes |
| `dynamodb update-table` | D | Capacity/billing-mode on live table |
| `dynamodb create-backup` | W | Backup before risky changes |
| `dynamodb delete-table` / `delete-backup` | F | Table+items / backup gone |

## CloudFormation

| Command | Tier | Purpose |
|---------|------|---------|
| `cloudformation list-stacks`, `describe-stacks`, `get-template` | S | Inspect |
| `cloudformation validate-template` | S | Lint template |
| `cloudformation create-change-set` / `describe-change-set` | W/S | Preview changes — ALWAYS before update |
| `cloudformation deploy --no-execute-changeset` | W | Stage w/o applying |
| `cloudformation execute-change-set` / `deploy` | D | Applies infra changes |
| `cloudformation cancel-update-stack` / `continue-update-rollback` | D | Recovery ops |
| `cloudformation delete-stack` | F | EVERY stack resource deleted |

## Route 53 & CloudFront

| Command | Tier | Purpose |
|---------|------|---------|
| `route53 list-hosted-zones`, `list-resource-record-sets` | S | Inspect DNS |
| `route53 change-resource-record-sets` | D | Live DNS — show the change batch first |
| `route53 delete-hosted-zone` | F | Zone gone |
| `route53domains register-domain/transfer-domain` | F | Spends money |
| `cloudfront list-distributions`, `get-distribution-config` | S | Inspect CDN |
| `cloudfront create-invalidation --paths '/*'` | W | Cache purge (small cost, no data loss) |
| `cloudfront update-distribution` / `delete-distribution` | D | Live traffic |

## Containers (ecs, eks, ecr)

| Command | Tier | Purpose |
|---------|------|---------|
| `ecs list-clusters/services/tasks`, `describe-services` | S | Inspect |
| `ecs update-service --desired-count N` | W | Scale (`0` = effective stop → escalates to D) |
| `ecs update-service --force-new-deployment` | W | Rolling restart |
| `ecs stop-task` / `delete-service` | D | Kills workloads |
| `eks describe-cluster`, `update-kubeconfig` | S/W | Inspect / wire kubectl |
| `eks update-cluster-version` | D | IRREVERSIBLE upgrade |
| `eks delete-cluster/nodegroup` | D | Workloads die |
| `ecr get-login-password \| docker login …` | S | Registry auth |
| `ecr batch-delete-image`, `delete-repository [--force]` | D | Images/repo gone |

## Secrets & Config (secretsmanager, ssm)

| Command | Tier | Purpose |
|---------|------|---------|
| `secretsmanager list-secrets` | S | Names only |
| `secretsmanager get-secret-value` | S* | *Sensitive — never echo to chat |
| `secretsmanager create-secret/put-secret-value/rotate-secret` | W | Manage secrets |
| `secretsmanager delete-secret [--recovery-window-in-days 30]` | D | Recoverable in window |
| `secretsmanager delete-secret --force-delete-without-recovery` | F | NO recovery |
| `ssm get-parameter [--with-decryption]` / `get-parameters-by-path` | S* | *Sensitive if decrypted |
| `ssm put-parameter [--overwrite]` | W | Config writes |
| `ssm start-session --target i-…` | W | Shell on instance (no SSH keys needed) |
| `ssm send-command` | D | Runs arbitrary commands on fleets |

## Messaging (sqs, sns) & Cost (ce, budgets)

| Command | Tier | Purpose |
|---------|------|---------|
| `sqs list-queues`, `get-queue-attributes`, `receive-message` | S | Inspect (receive can hide msgs briefly) |
| `sqs send-message` / `purge-queue` / `delete-queue` | W / D / D | Purge = ALL messages gone |
| `sns list-topics/subscriptions`, `publish`, `delete-topic` | S / W / D | Pub-sub |
| `ce get-cost-and-usage --time-period Start=…,End=… --granularity MONTHLY --metrics UnblendedCost` | S | Bill analysis |
| `ce get-cost-forecast` | S | Forecast |
| `budgets describe-budgets` / `create-budget` | S / W | Spend alerts |

## Other Frequent

| Command | Tier | Purpose |
|---------|------|---------|
| `cloudwatch get-metric-statistics` / `describe-alarms` | S | Metrics/alarms |
| `cloudwatch put-metric-alarm` / `delete-alarms` | W / D | Alerting |
| `acm list-certificates` / `request-certificate` | S / W | Free public TLS certs |
| `kms list-keys`, `describe-key`, `encrypt/decrypt` | S/W | Crypto ops |
| `elbv2 describe-load-balancers/target-groups/target-health` | S | LB debug |
| `amplify / apprunner / lightsail list-*` | S | PaaS inspect |
| `cloudtrail lookup-events --lookup-attributes …` | S | "Who did this?" audit |
| `health describe-events` | S | AWS-side incidents |
