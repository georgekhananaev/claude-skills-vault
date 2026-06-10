#!/usr/bin/env python3
"""Classify an AWS CLI command by risk tier: safe | write | destructive | forbidden.

Usage:
    python3 aws_risk.py "aws ec2 terminate-instances --instance-ids i-0abc"
    python3 aws_risk.py --json "aws s3 rm s3://bucket --recursive"

Exit codes: 0=safe, 10=write, 20=destructive, 30=forbidden, 2=parse error.

Deterministic pre-check before running any aws command. Verb-pattern based
with explicit per-service overrides; escalation-only (an override can never
lower a verb-derived tier) except a tiny curated SAFE_OVERRIDES list of
genuinely read-only ops with scary verbs. Compound shell commands
(&&, ;, |, $()) are split and EVERY aws invocation is classified — the
highest tier wins. xargs/for/while feeding a mutating aws op escalates
(bulk = multiplied blast radius). Unknown verbs default to `write`.
The classifier is advisory — the model must still apply judgment for
context (prod vs sandbox, blast radius).
"""

from __future__ import annotations

import json
import shlex
import sys

TIERS = ["safe", "write", "destructive", "forbidden"]
EXIT_CODE = {"safe": 0, "write": 10, "destructive": 20, "forbidden": 30}

SHELL_OPS = set("();<>|&")

# Global options that consume a value (skip both tokens when locating service/op).
VALUE_GLOBALS = {
    "--profile", "--region", "--output", "--query", "--endpoint-url",
    "--ca-bundle", "--cli-read-timeout", "--cli-connect-timeout", "--color",
    "--cli-binary-format", "--page-size", "--max-items", "--starting-token",
}

SAFE_VERBS = {
    "describe", "get", "list", "head", "search", "lookup", "scan", "query",
    "view", "preview", "estimate", "simulate", "check", "validate", "verify",
    "wait", "help", "filter", "discover", "batch-get", "select", "ls",
    "tail", "test",
}

WRITE_VERBS = {
    "create", "put", "add", "attach", "associate", "register", "upload",
    "enable", "start", "run", "tag", "untag", "copy", "restore", "import",
    "invoke", "publish", "send", "set", "update", "modify", "apply", "assume",
    "subscribe", "allocate", "request", "merge", "complete", "execute",
    "batch-write", "sync", "cp", "mb", "mv", "presign", "configure", "login",
    "change", "increase", "renew", "rotate", "transact",
}

DESTRUCTIVE_VERBS = {
    "delete", "remove", "terminate", "destroy", "release", "revoke",
    "deregister", "detach", "disassociate", "disable", "stop", "reboot",
    "cancel", "reset", "purge", "flush", "unsubscribe", "abort", "kill",
    "reject", "rm", "rb", "wipe", "evacuate", "drain", "logout",
    "deactivate", "unassign", "suspend", "failover", "reload", "replace",
}

# Genuinely read-only ops whose verb looks mutating. The ONLY allowed
# downgrades — keep this list tiny and audited.
SAFE_OVERRIDES = {
    ("logs", "start-query"): "CW Logs Insights query — read-only",
    ("logs", "stop-query"): "stops your own Insights query — read-only",
    ("logs", "start-live-tail"): "live log streaming — read-only",
}

# `restore-*` on these services provisions a NEW billable data store.
COST_RESTORE_SERVICES = {
    "rds", "redshift", "elasticache", "opensearch", "memorydb",
    "dynamodb", "docdb", "neptune",
}

# (service, operation) → (tier, reason). Escalation-only overrides.
OVERRIDES = {
    # --- account / org level: catastrophic, never automate ---
    ("account", "close-account"): ("forbidden", "Closes the AWS account itself"),
    ("organizations", "leave-organization"): ("forbidden", "Detaches account from the organization"),
    ("organizations", "delete-organization"): ("forbidden", "Deletes the organization"),
    ("organizations", "remove-account-from-organization"): ("forbidden", "Removes a member account"),
    ("organizations", "close-account"): ("forbidden", "Closes a member AWS account"),
    ("organizations", "create-account"): ("destructive", "Creates a member account — very hard to remove later"),
    # --- IAM identity destruction / lockout risk ---
    ("iam", "delete-user"): ("forbidden", "Deletes an IAM user — access + history lost"),
    ("iam", "delete-role"): ("forbidden", "Deletes an IAM role — anything assuming it breaks"),
    ("iam", "delete-group"): ("forbidden", "Deletes an IAM group"),
    ("iam", "delete-account-alias"): ("forbidden", "Removes the account sign-in alias"),
    ("iam", "delete-account-password-policy"): ("forbidden", "Removes the password policy"),
    ("iam", "deactivate-mfa-device"): ("forbidden", "Removes MFA protection"),
    ("iam", "delete-virtual-mfa-device"): ("forbidden", "Removes MFA protection"),
    ("iam", "delete-login-profile"): ("forbidden", "Removes a user's console access"),
    ("iam", "update-assume-role-policy"): ("destructive", "Changes who can assume the role — lockout risk"),
    # --- KMS: key loss makes encrypted data unrecoverable ---
    ("kms", "schedule-key-deletion"): ("forbidden", "Key deletion → ALL data encrypted under it unrecoverable"),
    ("kms", "disable-key"): ("forbidden", "Disables a CMK — decryption fails immediately"),
    ("kms", "put-key-policy"): ("destructive", "Key policy change — a bad policy locks data unreachable"),
    # --- data-store deletion with no recovery path ---
    ("s3api", "delete-bucket"): ("forbidden", "Deletes a bucket"),
    ("s3api", "delete-objects"): ("destructive", "Bulk object delete"),
    ("dynamodb", "delete-table"): ("forbidden", "Deletes a table and ALL its items"),
    ("dynamodb", "delete-backup"): ("forbidden", "Deletes a backup — last line of defense"),
    ("cloudformation", "delete-stack"): ("forbidden", "Deletes the stack AND every resource it manages"),
    ("route53", "delete-hosted-zone"): ("forbidden", "Deletes a DNS zone — can take a domain offline"),
    ("ecr", "delete-repository"): ("destructive", "Deletes an image repository"),
    # --- backups: deleting them removes the safety net ---
    ("backup", "delete-backup-vault"): ("forbidden", "Deletes a backup vault"),
    ("backup", "delete-recovery-point"): ("forbidden", "Deletes a recovery point"),
    ("ec2", "delete-snapshot"): ("forbidden", "Deletes an EBS snapshot (backup)"),
    ("rds", "delete-db-snapshot"): ("forbidden", "Deletes an RDS snapshot (backup)"),
    ("rds", "delete-db-cluster-snapshot"): ("forbidden", "Deletes a cluster snapshot (backup)"),
    ("elasticache", "delete-snapshot"): ("forbidden", "Deletes a cache snapshot (backup)"),
    # --- security monitoring / audit trail removal ---
    ("cloudtrail", "delete-trail"): ("forbidden", "Removes the audit trail"),
    ("cloudtrail", "stop-logging"): ("forbidden", "Stops audit logging"),
    ("guardduty", "delete-detector"): ("forbidden", "Disables threat detection"),
    ("securityhub", "disable-security-hub"): ("forbidden", "Disables security posture monitoring"),
    ("config", "delete-configuration-recorder"): ("forbidden", "Removes config change tracking"),
    ("config", "stop-configuration-recorder"): ("forbidden", "Stops config change tracking"),
    # --- money: purchases & long-term commitments ---
    ("ec2", "purchase-reserved-instances-offering"): ("forbidden", "Spends money — RI purchase commitment"),
    ("ec2", "purchase-host-reservation"): ("forbidden", "Spends money — host reservation"),
    ("ec2", "purchase-capacity-block"): ("forbidden", "Spends money — capacity block"),
    ("savingsplans", "create-savings-plan"): ("forbidden", "Spends money — 1-3 year billing commitment"),
    ("route53domains", "register-domain"): ("forbidden", "Spends money — registers a domain"),
    ("route53domains", "transfer-domain"): ("forbidden", "Spends money — domain transfer"),
    ("route53domains", "renew-domain"): ("forbidden", "Spends money — domain renewal"),
    # --- ongoing-cost resources: gate behind confirmation ---
    ("ec2", "run-instances"): ("destructive", "Launches billable instances (hourly cost)"),
    ("ec2", "request-spot-instances"): ("destructive", "Launches billable spot capacity"),
    ("ec2", "request-spot-fleet"): ("destructive", "Launches billable spot fleet"),
    ("ec2", "create-nat-gateway"): ("destructive", "NAT gateway bills hourly + per-GB"),
    ("ec2", "allocate-hosts"): ("destructive", "Dedicated hosts bill hourly"),
    ("ec2", "create-capacity-reservation"): ("destructive", "Reserved capacity bills while held"),
    ("rds", "create-db-instance"): ("destructive", "Launches a billable database"),
    ("rds", "create-db-cluster"): ("destructive", "Launches a billable DB cluster"),
    ("redshift", "create-cluster"): ("destructive", "Launches a billable Redshift cluster"),
    ("elasticache", "create-cache-cluster"): ("destructive", "Launches billable cache nodes"),
    ("elasticache", "create-replication-group"): ("destructive", "Launches billable cache nodes"),
    ("eks", "create-cluster"): ("destructive", "EKS control plane bills hourly"),
    ("opensearch", "create-domain"): ("destructive", "Launches a billable OpenSearch domain"),
    ("elbv2", "create-load-balancer"): ("destructive", "Load balancer bills hourly"),
    ("elb", "create-load-balancer"): ("destructive", "Load balancer bills hourly"),
    # --- live-traffic / breaking changes: confirm first ---
    ("route53", "change-resource-record-sets"): ("destructive", "Live DNS change — can break mail/site"),
    ("cloudfront", "update-distribution"): ("destructive", "Changes a live CDN distribution"),
    ("cloudfront", "delete-distribution"): ("destructive", "Removes a live CDN distribution"),
    ("cloudformation", "update-stack"): ("destructive", "Applies changes to live stack resources"),
    ("cloudformation", "execute-change-set"): ("destructive", "Applies a changeset to live stack resources"),
    ("cloudformation", "deploy"): ("destructive", "Applies template changes to live stack resources"),
    ("eks", "update-cluster-version"): ("destructive", "Cluster upgrade — IRREVERSIBLE, no downgrade"),
    ("rds", "modify-db-instance"): ("destructive", "Can reboot / change engine — possible downtime"),
    ("rds", "modify-db-cluster"): ("destructive", "Can reboot / change engine — possible downtime"),
    ("rds", "upgrade-db-instance"): ("destructive", "Engine upgrade — verify rollback path"),
    ("ec2", "modify-instance-attribute"): ("destructive", "Live instance change (type, sg, userdata)"),
    ("dynamodb", "update-table"): ("destructive", "Capacity/billing-mode change on a live table"),
    ("lambda", "delete-function"): ("destructive", "Deletes a function (redeployable if source kept)"),
    ("apigateway", "delete-rest-api"): ("destructive", "Deletes an API — endpoints die"),
    ("apigatewayv2", "delete-api"): ("destructive", "Deletes an API — endpoints die"),
    # --- remote code execution on infrastructure ---
    ("ssm", "send-command"): ("destructive", "Runs arbitrary commands on instances (fleet-wide RCE)"),
    ("ecs", "execute-command"): ("destructive", "Runs a command inside a live container"),
    # --- credential issuance (safe verb, real-world effect) ---
    ("sts", "get-session-token"): ("write", "Issues new credentials"),
    ("sts", "assume-role"): ("write", "Issues new credentials"),
}

# Flags that escalate a specific (service, op). Empty flag = unconditional.
FLAG_ESCALATIONS = [
    ("s3", "rb", "--force", "forbidden", "Deletes bucket AND all objects in it"),
    ("s3", "rm", "--recursive", "destructive", "Bulk delete of objects under a prefix"),
    ("s3", "sync", "--delete", "destructive", "sync --delete removes destination objects missing from source"),
    ("rds", "delete-db-instance", "--skip-final-snapshot", "forbidden", "DB deleted with NO final backup"),
    ("rds", "delete-db-cluster", "--skip-final-snapshot", "forbidden", "Cluster deleted with NO final backup"),
    ("redshift", "delete-cluster", "--skip-final-cluster-snapshot", "forbidden", "Cluster deleted with NO final backup"),
    ("secretsmanager", "delete-secret", "--force-delete-without-recovery", "forbidden", "Secret deleted with NO recovery window"),
    ("ec2", "terminate-instances", "", "destructive", "Terminates instances — instance-store data is gone"),
]

ADMIN_POLICIES = ("AdministratorAccess", "IAMFullAccess")


def _tier_max(a: str, b: str) -> str:
    return a if TIERS.index(a) >= TIERS.index(b) else b


def _flag_value(tokens: list[str], flag: str) -> str | None:
    """Value of --flag, accepting both `--flag v` and `--flag=v` forms."""
    for i, t in enumerate(tokens):
        if t == flag and i + 1 < len(tokens):
            return tokens[i + 1]
        if t.startswith(flag + "="):
            return t.split("=", 1)[1]
    return None


def split_segments(command: str) -> list[list[str]]:
    """Split a shell command line into simple-command token segments.

    Uses shlex with punctuation_chars so quoted values (JMESPath pipes,
    JSON) survive intact while &&, ||, ;, |, (), <> split segments.
    """
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    try:
        tokens = list(lex)
    except ValueError as e:
        raise ValueError(f"unparseable command: {e}") from None
    segments: list[list[str]] = []
    current: list[str] = []
    for t in tokens:
        if t and all(c in SHELL_OPS for c in t):
            if current:
                segments.append(current)
                current = []
        else:
            current.append(t)
    if current:
        segments.append(current)
    return segments


def _find_aws(seg: list[str]) -> int:
    for i, t in enumerate(seg):
        if t == "aws" or t.endswith("/aws"):
            return i
    return -1


def parse(command: str):
    """Return (service, operation, tokens) for the FIRST aws invocation.

    Raises ValueError if no aws command is present.
    """
    for seg in split_segments(command):
        idx = _find_aws(seg)
        if idx >= 0:
            tokens = seg[idx:]
            service, op = _service_op(tokens)
            return service, op, tokens
    raise ValueError("not an `aws` command")


def _service_op(tokens: list[str]) -> tuple[str, str]:
    rest, positional, i = tokens[1:], [], 0
    while i < len(rest) and len(positional) < 2:
        t = rest[i]
        if t in VALUE_GLOBALS:
            i += 2
            continue
        if t.startswith("-"):
            i += 1
            continue
        positional.append(t.lower())
        i += 1
    if not positional:
        raise ValueError("no service found")
    return positional[0], (positional[1] if len(positional) > 1 else "help")


def _classify_tokens(tokens: list[str]) -> dict:
    service, op = _service_op(tokens)
    parts = op.split("-")
    verb = op if service == "s3" else parts[0]
    verb2 = "-".join(parts[:2])
    joined = " ".join(tokens)
    compact = joined.replace(" ", "").replace("'", "")

    base = {
        "service": service, "operation": op,
        "profile": _flag_value(tokens, "--profile"),
        "region": _flag_value(tokens, "--region"),
    }

    if op == "help" or tokens[-1] == "help" or "--dry-run" in tokens or "--generate-cli-skeleton" in tokens:
        return {**base, "tier": "safe", "reason": "help/dry-run/skeleton — nothing executes"}
    if "--dryrun" in tokens and service == "s3":
        return {**base, "tier": "safe", "reason": "s3 --dryrun preview — nothing executes"}
    if "--no-execute-changeset" in tokens and service == "cloudformation":
        return {**base, "tier": "write", "reason": "stages a changeset w/o applying it"}
    if (service, op) in SAFE_OVERRIDES:
        return {**base, "tier": "safe", "reason": SAFE_OVERRIDES[(service, op)]}

    if verb in SAFE_VERBS or verb2 in SAFE_VERBS:
        tier, reason = "safe", f"read-only verb `{verb}`"
    elif verb in DESTRUCTIVE_VERBS or verb2 in DESTRUCTIVE_VERBS:
        tier, reason = "destructive", f"destructive verb `{verb}`"
    elif verb in WRITE_VERBS or verb2 in WRITE_VERBS:
        tier, reason = "write", f"mutating verb `{verb}`"
    else:
        tier, reason = "write", f"unknown verb `{verb}` — verify in docs before running"

    if (service, op) in OVERRIDES:
        o_tier, o_reason = OVERRIDES[(service, op)]
        if TIERS.index(o_tier) > TIERS.index(tier):
            tier, reason = o_tier, o_reason

    for f_svc, f_op, flag, f_tier, f_reason in FLAG_ESCALATIONS:
        if service == f_svc and op == f_op and (not flag or flag in tokens):
            if TIERS.index(f_tier) > TIERS.index(tier):
                tier, reason = f_tier, f_reason

    if verb == "restore" and service in COST_RESTORE_SERVICES:
        if TIERS.index(tier) < TIERS.index("destructive"):
            tier, reason = "destructive", "restores into a NEW billable data store"

    # --- cross-cutting escalations ---
    mutating = verb in ("authorize", "create", "put", "modify", "update", "replace", "attach", "add", "set")
    if ("0.0.0.0/0" in joined or "::/0" in joined) and mutating:
        tier = _tier_max(tier, "destructive")
        reason = "opens a resource to the ENTIRE internet (0.0.0.0/0)"
    if mutating and ("public-read" in tokens or "public-read-write" in tokens):
        tier = _tier_max(tier, "destructive")
        reason = "makes a bucket/object ACL PUBLIC"
    if mutating and ('"Principal":"*"' in compact or '"AWS":"*"' in compact):
        tier = _tier_max(tier, "destructive")
        reason = "policy grants access to EVERYONE (Principal:*)"
    if service == "s3api" and op == "put-public-access-block" and "false" in joined.lower():
        tier = _tier_max(tier, "destructive")
        reason = "weakens the public-access block — public-exposure risk"
    if any(p in joined for p in ADMIN_POLICIES) and verb in ("attach", "put", "create", "add", "set"):
        tier, reason = "forbidden", "grants full admin — privilege escalation"
    if '"Action":"*"' in compact and '"Resource":"*"' in compact and mutating:
        tier, reason = "forbidden", "policy is admin-equivalent (Action:* on Resource:*)"
    if _flag_value(tokens, "--desired-count") == "0":
        tier = _tier_max(tier, "destructive")
        reason = "scales the service to ZERO — effective stop"
    if "--no-verify-ssl" in tokens:
        reason += " · WARNING: --no-verify-ssl disables TLS verification"

    return {**base, "tier": tier, "reason": reason}


def classify(command: str) -> dict:
    """Classify a full command line; compound commands → highest tier wins."""
    segments = split_segments(command)
    loop_ctx = any(s and s[0] in ("for", "while", "until") for s in segments)
    results = []
    for seg in segments:
        idx = _find_aws(seg)
        if idx < 0:
            continue
        r = _classify_tokens(seg[idx:])
        if "xargs" in seg[:idx] or loop_ctx:
            if r["tier"] in ("destructive", "forbidden"):
                r["tier"] = "forbidden"
                r["reason"] = f"BULK loop over a destructive op ({r['reason']}) — multiplied blast radius"
            elif r["tier"] == "write":
                r["tier"] = "destructive"
                r["reason"] = f"bulk mutation via xargs/loop ({r['reason']})"
        results.append(r)
    if not results:
        raise ValueError("not an `aws` command")
    worst = max(results, key=lambda r: TIERS.index(r["tier"]))
    if len(results) > 1:
        worst = dict(worst)
        worst["segments"] = len(results)
        worst["reason"] += f" · compound command: {len(results)} aws invocations, highest tier shown"
    return worst


def main() -> int:
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    if not args:
        print("usage: aws_risk.py [--json] '<aws command>'", file=sys.stderr)
        return 2
    try:
        result = classify(" ".join(args))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if as_json:
        print(json.dumps(result))
    else:
        ctx = "".join(
            f" {k}={result[k]}" for k in ("profile", "region") if result.get(k)
        )
        print(f"{result['tier'].upper()}: {result['reason']} "
              f"[{result['service']} {result['operation']}{ctx}]")
    return EXIT_CODE[result["tier"]]


if __name__ == "__main__":
    sys.exit(main())
