#!/usr/bin/env bash
# AWS CLI preflight — run once per session BEFORE any aws operation.
# Reports: CLI version, profiles, active identity, region, account.
# Read-only: only calls `aws configure list*` + `sts get-caller-identity`.
#
# Usage: ./aws_preflight.sh [profile]

set -u

PROFILE="${1:-${AWS_PROFILE:-}}"
PFLAG=()
[ -n "$PROFILE" ] && PFLAG=(--profile "$PROFILE")

echo "=== AWS CLI Preflight ==="

if ! command -v aws >/dev/null 2>&1; then
  echo "FAIL: aws not installed. Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
  exit 1
fi
echo "version : $(aws --version 2>&1)"

PROFILES="$(aws configure list-profiles 2>/dev/null)"
if [ -z "$PROFILES" ]; then
  echo "profiles: NONE configured"
  echo "          → run \`aws configure\` (keys) or \`aws configure sso\` (IAM Identity Center)"
else
  echo "profiles: $(echo "$PROFILES" | tr '\n' ' ')"
fi
echo "active  : ${PROFILE:-<default>}"

REGION="$(aws configure get region ${PFLAG[@]+"${PFLAG[@]}"} 2>/dev/null || true)"
REGION="${REGION:-${AWS_REGION:-${AWS_DEFAULT_REGION:-}}}"
if [ -n "$REGION" ]; then
  echo "region  : $REGION"
else
  echo "region  : NOT SET — commands will fail or hit the wrong region; set with --region or \`aws configure\`"
fi

IDENTITY="$(aws sts get-caller-identity --output json ${PFLAG[@]+"${PFLAG[@]}"} 2>&1)"
if [ $? -eq 0 ]; then
  echo "identity: $(echo "$IDENTITY" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["Arn"], "(account", d["Account"] + ")")' 2>/dev/null || echo "$IDENTITY")"
  echo "OK: authenticated. Confirm account+region above match the intended target before ANY write."
else
  echo "identity: FAILED — $IDENTITY" | head -3
  case "$IDENTITY" in
    *"Token has expired"*|*"token included in the request is expired"*)
      echo "FIX: aws sso login${PROFILE:+ --profile $PROFILE}" ;;
    *"Unable to locate credentials"*)
      echo "FIX: aws configure / aws configure sso, or export AWS_PROFILE=<name>" ;;
    *"InvalidClientTokenId"*)
      echo "FIX: keys invalid/deactivated — rotate in IAM console" ;;
  esac
  exit 1
fi
