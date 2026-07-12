---
name: codex-cli
description: Run OpenAI Codex CLI for coding tasks, implementation, reviews, and second-opinion audits with mandatory task-based routing across GPT-5.6-or-newer models. Use when a user asks to run, ask, or use Codex; says "codex prompt"; wants a Codex code/logic/plan audit; or wants Claude to delegate work to OpenAI models. Inspect the live Codex model catalog, explicitly pin an eligible model and reasoning effort on every invocation, route clear high-volume work to Luna, everyday work to Terra, and difficult or high-value work to Sol. Use Sol with max reasoning for plan audits. Never invoke or fall back to GPT-5.5, GPT-5.4, GPT-5.3-Codex-Spark, OSS, or any model older than GPT-5.6.
---

# Codex CLI

Use OpenAI's local agentic coding CLI (`codex`) for second opinions, delegated builds, code review, diagnosis, and non-interactive execution. Treat the live CLI model catalog as authoritative; the current GPT-5.6 family is:

- `gpt-5.6-sol`: frontier capability for ambiguous, difficult, or high-value work.
- `gpt-5.6-terra`: balanced everyday capability, speed, and usage.
- `gpt-5.6-luna`: rapid, economical execution for clear, repeatable, high-volume work.

Prefer explicit catalog slugs over the `gpt-5.6` alias so the selected route is auditable.

## Non-negotiable model floor

Apply these rules to every Codex call made under this skill:

1. Use only a listed OpenAI GPT model whose numeric version is `5.6` or newer.
2. If the catalog contains a newer numeric GPT family, prefer the newest family and map the task to its equivalent capability, balanced, or rapid tier when those tiers exist.
3. Explicitly pass both the model and a reasoning effort supported by that exact catalog entry. Never rely on the user's default model.
4. Never use GPT-5.5, GPT-5.4, GPT-5.3-Codex-Spark, `o3`, another older/non-GPT model, or `--oss` as a fallback.
5. If no eligible model is available, stop and report that Codex must be updated or the account needs access. Do not silently downgrade.
6. If the user explicitly requests a model below the floor, do not run it. Explain the conflict and offer the closest GPT-5.6-or-newer route.

Within the same version, escalate unavailable tiers upward in capability: Luna -> Terra -> Sol. Never cross below the version floor. For a Max-required task, choose an eligible catalog model that supports `max`; do not silently lower its effort.

## Preflight once per Claude session

Before the first Codex invocation, inspect health and the refreshed model catalog. Reuse the result for later calls in the same session unless a model error or update makes it stale.

```bash
codex doctor 2>&1 | rg "version|model|auth|updates" | head -20
codex debug models | jq -r '.models[] | select(.visibility == "list") | [.slug, .default_reasoning_level, ([.supported_reasoning_levels[].effort] | join(","))] | @tsv'
```

Use `codex debug models --bundled` only when refresh is unavailable. If `jq` is unavailable, inspect `codex debug models` directly. Confirm:

- Codex is installed, authentication is configured, and the CLI is not behind an available update.
- At least one listed model has numeric GPT version >= 5.6.
- The chosen effort appears in that model's `supported_reasoning_levels`.

Surface an available CLI update but do not run `codex update` automatically. Do not skip catalog validation for a fast request; cache the result instead.

## Route by task shape

Use the lowest-cost route below that matches the actual task. The explicit audit rule takes precedence over all other rows.

| Route | Model | Effort | Use for |
|---|---|---|---|
| Rapid | Luna | `low` | Exact, bounded, repeatable work: extraction, classification, formatting, simple searches, mechanical edits, boilerplate, and high-volume transformations |
| Rapid+ | Luna | `medium` | Clear implementation with modest checking: a narrow bug fix, a small test, or a repetitive migration with validation |
| Balanced | Terra | `medium` | Everyday coding: normal features, routine refactors, tests, documentation, and well-scoped reviews |
| Investigative | Terra | `high` | Multi-file diagnosis, non-trivial review, performance analysis, or a clear task with several dependent steps |
| Deep | Sol | `high` | Ambiguous or complex implementation, unfamiliar architecture, cross-system changes, research, or work where judgment and polish matter |
| Deep+ | Sol | `xhigh` | A very difficult single-thread problem with subtle edge cases, failed prior attempts, or demanding verification |
| Audit | Sol | `max` | Audit or challenge a plan, architecture, migration, security strategy, incident response, or other high-stakes decision; identify hidden assumptions and failure modes |
| Parallel deep | Sol | `ultra` | Broad complex work that divides into meaningful independent workstreams and benefits enough from subagents to justify extra usage |

Current GPT-5.6 catalog behavior: Sol and Terra support `low`, `medium`, `high`, `xhigh`, `max`, and `ultra`; Luna supports `low`, `medium`, `high`, `xhigh`, and `max`. Always re-check the live catalog because this can change.

### Routing decision order

Classify before invoking:

1. If the task audits a plan or another high-stakes proposed approach, use the Audit route: Sol + `max` + read-only sandbox.
2. Otherwise, if the task has multiple genuinely independent complex workstreams, consider Sol + `ultra`. Do not use Ultra merely because a task has several steps.
3. Otherwise, use Sol for ambiguity, high stakes, broad context, or substantial judgment.
4. Otherwise, use Terra for ordinary engineering that needs reasoning and tool use.
5. Use Luna only when the goal, inputs, output shape, and success check are explicit and repeatable.

Do not start cheap and rerun the same clearly difficult task through several models. Route correctly once. Escalate effort only after a result misses stated success criteria, except for Audit tasks, which start at `max` by policy.

## Mandatory invocation pattern

Pin the selected model and effort on every new run:

```bash
codex exec -m <catalog-model> \
  -c 'model_reasoning_effort="<supported-effort>"' \
  -s <sandbox> \
  "<outcome-focused prompt>"
```

For `codex review`, `-m` is not exposed. Set the model through config:

```bash
codex review \
  -c 'model="<catalog-model>"' \
  -c 'model_reasoning_effort="<supported-effort>"' \
  --uncommitted "<review focus>"
```

For `codex exec resume`, override the model and effort again, especially when the original session may have used an older model:

```bash
codex exec resume --last \
  -m <catalog-model> \
  -c 'model_reasoning_effort="<supported-effort>"' \
  "<follow-up>"
```

When the user says "codex prompt", treat it as `codex exec`, classify the prompt, and apply the same mandatory model/effort routing.

## Canonical GPT-5.6 examples

Replace these slugs with the equivalent newer-family catalog slugs when a version above 5.6 is available.

```bash
# Rapid, bounded operation
codex exec -m gpt-5.6-luna \
  -c 'model_reasoning_effort="low"' \
  -s read-only --ephemeral \
  "Extract every TODO as file:line:text. Do not modify files."

# Balanced implementation
codex exec -m gpt-5.6-terra \
  -c 'model_reasoning_effort="medium"' \
  -s workspace-write \
  "Implement the health endpoint and its unit tests. Run the focused test suite."

# Non-trivial code review
codex review \
  -c 'model="gpt-5.6-terra"' \
  -c 'model_reasoning_effort="high"' \
  --uncommitted "Find correctness regressions, security risks, and missing tests."

# Plan audit: always Sol + max + read-only
codex exec -m gpt-5.6-sol \
  -c 'model_reasoning_effort="max"' \
  -s read-only --ephemeral \
  "Audit docs/plan.md. Challenge assumptions, find failure modes and omitted dependencies, rank findings by severity, and propose concrete mitigations. Do not modify files."
```

## Prompt efficiently

Give Codex an outcome-focused prompt containing only what changes its work:

- State the objective, relevant scope, hard constraints, approval boundary, success criteria, and required output shape.
- Point to files or directories instead of pasting large content already available in the workspace.
- For audits, demand evidence such as file/line or plan-step references and ask for findings in severity order.
- For implementations, ask Codex to verify with the narrowest relevant tests.
- Set a useful output bound, such as "top five findings" or "answer in at most eight bullets."
- Reuse a session with `codex exec resume` when prior context remains relevant; use `--ephemeral` for unrelated one-shot work.

## Sandbox and approvals

Choose access from user intent, independently of model route:

| Mode | Use |
|---|---|
| `read-only` | Audits, reviews, explanations, diagnostics, research, and second opinions |
| `workspace-write` | Requested implementation, fixes, refactors, and test changes inside the workspace |
| `danger-full-access` | Only with explicit user approval and a trusted prompt/environment |

`-a, --ask-for-approval` is a top-level flag and must appear before `exec` or `review`. Values are `untrusted`, `on-request`, and `never`.

```bash
codex -a on-request exec -m gpt-5.6-terra \
  -c 'model_reasoning_effort="medium"' \
  -s workspace-write "Implement the requested change."
```

Use `--dangerously-bypass-approvals-and-sandbox` only in an externally sandboxed container or VM with explicit user approval. Never use it on a bare developer machine. `--full-auto` is deprecated; use `--sandbox workspace-write`.

## Argument compatibility

### `codex exec`

- `[PROMPT]` is the only prompt positional argument.
- Use `codex exec ... -` when the entire prompt comes from stdin.
- When stdin is piped and a quoted prompt is supplied, current Codex appends stdin as a `<stdin>` block; do not also add the `-` positional.
- Put `--search` before `exec`: `codex --search exec ...`.

```bash
# Stdin only
git diff HEAD~1..HEAD | codex exec -m gpt-5.6-terra \
  -c 'model_reasoning_effort="high"' -s read-only --ephemeral -

# Instructions plus piped context
git diff HEAD~1..HEAD | codex exec -m gpt-5.6-terra \
  -c 'model_reasoning_effort="high"' -s read-only --ephemeral \
  "Review the supplied diff for concurrency bugs."
```

### `codex review`

- Use `-c 'model="..."'`; `codex review` does not expose `-m`.
- Use one target: `--uncommitted`, `--base <BRANCH>`, or `--commit <SHA>`.
- If a CLI version rejects custom instructions with `--commit`, pipe the commit diff to `codex exec -s read-only` instead.

## Background execution and quota safety

Run long Sol, Max, Ultra, and implementation calls with Claude Code's Bash `run_in_background: true`; read the result after the completion notification. A short Luna call may run in the foreground. Do not poll with sleep loops.

Use `-o <file>` when Claude must consume a clean final response and `--json` when progress events are useful.

```text
Bash(command="codex exec -m gpt-5.6-sol -c 'model_reasoning_effort=\"max\"' -s read-only --ephemeral -o /tmp/codex.out 'Audit the plan...'",
     run_in_background=true)
```

- Serialize Codex processes. Do not run multiple `codex exec` processes in parallel; Ultra's internal delegation remains one invocation.
- Batch similar high-volume operations into one well-scoped Luna request when practical.
- On `429`, `rate limit`, or `quota exceeded`, stop and report it. Do not retry-loop or downgrade the model.
- On `model_not_found` or unsupported effort, refresh `codex debug models` and select another eligible >=5.6 route. Never fall through to an older model.
- Do not repeat an unchanged failed prompt. Tighten scope or success criteria before one justified retry.

## Claude Code plugin compatibility

Direct CLI invocation is the canonical path when enforcing this skill's model floor. If the official OpenAI Codex Claude Code plugin is installed, use its delegation wrapper only when it accepts or verifiably preserves an explicit >=5.6 model and supported effort. Include the floor and selected route in the delegated instructions. Otherwise use direct `codex exec`; do not double-invoke.

## Useful commands

| Command | Purpose |
|---|---|
| `codex --version` | Confirm installation |
| `codex doctor` | Diagnose install, auth, config, connectivity, and updates |
| `codex debug models` | Refresh and inspect the live model catalog |
| `codex exec [PROMPT]` | Run a non-interactive task |
| `codex exec resume [ID\|--last] [PROMPT]` | Continue a previous non-interactive session |
| `codex review {--uncommitted\|--base BRANCH\|--commit SHA}` | Review repository changes |
| `codex apply <TASK_ID>` | Apply a Codex-produced patch |
| `codex mcp {list,get,add,remove,login,logout}` | Manage MCP servers |
| `codex update` | Update Codex after informing the user |
| `codex login` / `codex logout` | Manage authentication |

## Final checklist

- Preflight once with `codex doctor` and `codex debug models`.
- Select the newest available GPT family whose numeric version is >=5.6.
- Route Luna for clear/repeatable work, Terra for everyday work, and Sol for difficult/high-value work.
- Route every plan audit to Sol + `max` + `read-only`.
- Pin model and supported effort on every `exec`, `review`, and resumed run.
- Fail closed if no eligible model exists; never downgrade or use OSS.
- Match sandbox to user intent and reserve dangerous access for explicit approval.
- Use background execution for long calls, serialize invocations, and stop on rate limits.
