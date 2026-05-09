# n8n CLI Command Reference

Authoritative map of `n8n` CLI commands. Self-hosted only — n8n Cloud has no CLI access.

Source: `https://docs.n8n.io/hosting/cli-commands/`, `n8n --help`.

## Server lifecycle (NOT used by skill)

| Command | Purpose |
|---|---|
| `n8n start` | Start the n8n server |
| `n8n start --tunnel` | Start w/ a public ngrok-style tunnel (dev only) |
| `n8n webhook` | Run as a webhook-only worker process |
| `n8n worker` | Run as a queue worker process |

## Read — allowed by skill

| Command | Purpose | Skill script |
|---|---|---|
| `n8n list:workflow` | List all workflows (text table) | `list_workflows.py --backend cli` |
| `n8n export:workflow --all --output=<path>` | Bundle all workflows to one JSON | `export_workflows.py` |
| `n8n export:workflow --all --separate --output=<dir>` | One file per workflow | `export_workflows.py --separate` |
| `n8n export:workflow --id=<wfid> --output=<path>` | Export single workflow | `export_workflows.py --id` |
| `n8n export:credentials --all --output=<path>` | Export ENCRYPTED credentials | `export_credentials.py` |
| `n8n export:credentials --all --decrypted --output=<path>` | Export DECRYPTED credentials (DANGEROUS) | `export_credentials.py --decrypted --confirm-secrets` |
| `n8n audit` | Generate security audit report (markdown) | `audit_log.py --backend cli` |
| `n8n audit --categories=credentials,nodes` | Subset of audit | `audit_log.py --categories` |
| `n8n --version` | Print CLI version | `validate_env.py` |

## Write (additive — gated by `--confirm`)

| Command | Purpose | Skill script |
|---|---|---|
| `n8n import:workflow --input=<file>` | Import single or array of workflows | `import_workflow.py --confirm` |
| `n8n import:workflow --separate --input=<dir>` | Import dir of workflow files | `import_workflow.py --confirm` |
| `n8n import:credentials --input=<file>` | Import credentials (encrypted or decrypted, depending on file) | not in skill — do manually |
| `n8n execute --id=<wfid>` | Run a workflow once (synchronous) | `trigger_workflow.py --backend cli --confirm` |
| `n8n execute-batch --ids=<id1,id2>` | Run multiple workflows sequentially | not in skill |

## REFUSED — never run by skill

| Command | Why |
|---|---|
| `n8n delete:workflow --id=<x>` | Destroys workflow |
| `n8n delete:workflow --all` | Wipes all workflows |
| `n8n delete:credentials` | Destroys credentials |
| `n8n user-management:reset` | Wipes all users |
| `n8n user-management:promote` / `--revoke` | Auth role changes |
| `n8n mfa:disable` | Disables MFA on a user |
| `n8n ldap:reset` | Wipes LDAP config |
| `n8n db:revert` | DB migration revert |
| `n8n db:drop` | DB drop |
| `n8n encryption-key:reset` / `:rotate` | Breaks all credentials |
| `n8n license:clear` | Removes paid features |
| `n8n executionData:prune` | Drops execution history |

Refusal is implemented in `scripts/_common.py:refuse_if_destructive_cli()`.

## Common flag conventions

| Flag | Meaning |
|---|---|
| `--all` | Apply to every workflow / credential |
| `--id=<n>` | Target a specific resource |
| `--separate` | One file per resource (vs. one bundle) |
| `--output=<path>` | Write target |
| `--input=<path>` | Read source |
| `--decrypted` | Plain-text credential export (DANGEROUS) |
| `--activeState=fromJson` | Preserve active state from imported file (n8n 2.x w/ multi-main / queue mode) |
| `--published` | Operate on the published version vs. draft |
