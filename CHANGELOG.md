# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed

### Fixed

## [1.8.2] - 2026-06-25

### Added
- **mcp-servers**: Added a comprehensive §5 "More verified servers (by category)" catalog to `MCP-SERVERS.md` — ~75 additional MCP servers across 12 categories (databases, vector/search, cloud, DevOps/CI/IaC, observability, payments, CRM/support, e-commerce/CMS, productivity, comms/automation, web search, AI/browser/dev tools). Each row has maintainer, an official or maintained-GitHub source link, and the exact `claude mcp add` / `/plugin install` command. Sources verified June 2026 via parallel research; deprecated servers (E2B, standalone Elasticsearch/Weaviate, generic Cassandra, etc.) excluded with successor notes.

### Changed
- **commands**: Added an **Install** column to `COMMANDS.md` showing the per-command `npx claude-skills-vault install <name>` invocation (mirrors the Install column in `SKILLS.md`). Implemented in `scripts/generate-docs.js` so it survives doc regeneration; every command name resolves via the CLI's `findItem`.
- **mcp-servers**: Rewrote `MCP-SERVERS.md` for June 2026. Leads with the official `claude-plugins-official` plugin marketplace (`/plugin install <name>@claude-plugins-official`), documents current `claude mcp add` transports (HTTP/SSE/stdio/ws) + `--scope` and the `.mcp.json` format, and references the Anthropic connector Directory, the official MCP Registry, and the plugin catalog. Reorganized official-first / all-sourced; corrected the `git` reference server (active, not archived); noted the `modelcontextprotocol/servers` April-2026 third-party-list retirement in favor of the Registry.
- **readme**: Added a **Documentation** hub to `README.md` with deep links into `SKILLS.md`, `COMMANDS.md`, and `MCP-SERVERS.md` (setup methods + 12 server categories), so the docs are navigable without searching. Fixed the "What's Inside" counts (Skills 55→59, Commands 11→12, MCP 38→34) and repaired the malformed table. All anchors verified against GitHub's slugger.

### Removed
- **mcp-servers**: Removed 4 bespoke custom MCP server implementations (`jira-bridge`, `mongodb`, `postgres-mcp`, `supabase`) that shipped their own source but had no maintained upstream, in favor of maintained official servers (Atlassian remote MCP, [mongodb-js/mongodb-mcp-server](https://github.com/mongodb-js/mongodb-mcp-server), [crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp), [supabase-community/supabase-mcp](https://github.com/supabase-community/supabase-mcp)). MCP server count 38 → 34 in `manifest.json`.

## [1.8.1] - 2026-06-25

### Added
- **project-change-log**: Archiving support so `CHANGELOG.md` stays small no matter how many releases accumulate (one real project had hit 197 versions / 2,508 lines / 420 KB). New safe-by-default rotation script `scripts/rotate_changelog.py` (Python stdlib only, dry-run unless `--apply`) keeps `[Unreleased]` + the newest 20 releases in the main file and moves older releases into per-major archive files (`changelog/CHANGELOG-1.x.md`), linked from an `## Older releases` index. Idempotent and content-loss-safe (verified by header-set equality on the 197-version file: 2,508 → 531 lines, all releases preserved), with newest-first ordering across main + archives; handles letter/pre-release suffixes (`1.23.0a`), hash-instead-of-date headers (`1.19.4 - e850122c`), multi-major bucketing, and a `CHANGELOG-misc.md` fallback. SKILL.md gains a "Keeping the changelog small" section plus a first-time-adoption flow (run after the skill is added/updated: dry-run to verify detected version count, then `--apply` once and commit the `changelog/` dir with the trimmed file). Adds `references/archiving.md` (policy, behavior guarantees, adoption steps, troubleshooting).

## [1.8.0] - 2026-06-10

### Added
- **skills**: Sync 6 external skills to upstream latest. `claude-seo` → v2.0.0: 12 → 24 sub-skills (backlinks, SERP-overlap clustering, SXO, drift monitoring "git for SEO", Google APIs incl. GSC/PageSpeed/CrUX, local+maps, e-commerce, content briefs, FLOW framework, DataForSEO MCP, AI image-gen) + 50 helper scripts; root orchestrator rewritten w/ API-key fallback guidance. `planning-with-files` → v2.43: pulls the scripts/ + templates/ + reference docs the SKILL.md referenced but the vault never had (11 scripts incl. check-complete/init-session/attest-plan, 3 templates), plus the new plugin-vs-skill-only install matrix and manual `/plan-goal`//`/plan-loop` fallbacks. `react-best-practices` → upstream 72-rule set (23 new rules synced: server-auth-actions, rerender-derived-state-no-effect, rendering-resource-hints, …) + current rule index. `stripe-best-practices` → API pin 2026-05-27.dahlia, `stripe sandbox create` keyless onboarding, new security.md + tax.md references. `frontend-design` → full upstream rewrite (design-lead framing, subject-grounded direction). `firecrawl-cli` → monitor `--goal` authoring guidance + refreshed rules. `check-skill-updates.js` gains per-skill `localPath` so adapted roots can track a vanilla-synced file (claude-seo now meaningfully diffable).
- **skills**: Add `aws-cli` — safety-first wrapper for AWS CLI v2 with full-surface control (EC2, S3, IAM, Lambda, RDS, DynamoDB, CloudFormation, Route 53, EKS/ECS, KMS, Secrets Manager, cost & 300+ services) and risk-tiered confirmation (Safe → execute, Write → inform, Destructive → `AskUserQuestion`, Forbidden → typed triple-confirm). Ships a deterministic classifier (`scripts/aws_risk.py`, exit codes 0/10/20/30): verb-pattern base + 78 per-service overrides covering cost-incurring launches, breaking changes (engine/cluster upgrades, live DNS/CDN, `update-stack`), security-protection removal (CloudTrail/GuardDuty/Config, MFA, KMS key disable), backup deletion, purchases/commitments, and account/org-level ops. Adversarially hardened: splits compound commands (`&&`, `;`, `|`, `$()`) and returns the worst tier (quoted JMESPath pipes survive), escalates `xargs`/`for`/`while` bulk loops over mutating ops to forbidden, catches public exposure (`0.0.0.0/0`, `--acl public-read`, `"Principal": "*"`, weakened `put-public-access-block`), admin-equivalent grants (`AdministratorAccess`/`IAMFullAccess`/inline `Action:*`+`Resource:*`), `s3 sync --delete`, scale-to-zero, billable `restore-*`, and flag escalations (`--skip-final-snapshot`, `s3 rb --force`, `--force-delete-without-recovery`). Session preflight (`scripts/aws_preflight.sh`) verifies version/profiles/region/`sts get-caller-identity` before any write (wrong-account guard), bash-3.2-safe. References: full tier rules + triple-confirmation protocol, per-service command/tier/doc-URI map, and auth (SSO/keys/assume-role), JMESPath, pagination, dry-run-matrix patterns. 17-test local suite green (tier assignments across ~80 real commands, bypass attempts, exit codes).

### Changed
- **skills**: Safety-first CLI family aligned to one template — refusal patterns added to `github-cli`/`salesforce-cli`/`supabase-cli`, self-healing doc-URI sections added to `github-cli`/`salesforce-cli`/`supabase-cli`/`mongodb-atlas-cli`, AskUserQuestion guidance added to `n8n-cli`. New-surface coverage: `gh agent-task` + `gh skill` (github-cli), 11 new 2026 Vercel commands w/ risk tiers (`upgrade`, `agent`, `ai-gateway`, `crons`, `deploy-hooks`, `edge-config`, `oauth-apps`, `sandbox`, `skills`, `tokens`, `teams members/sso`) + `integration-resource` alias note, `codex archive`/`unarchive`, Atlas Service-Account (OAuth2) auth env vars, n8n 2.0 `publish:workflow`/`unpublish:workflow`, MCP spec-revision note (2025-11-25 current, 2026-07-28 RC) + SDK floor bumps, Swift 6.3 framing, MRT dormancy + MUI-v9 lock-in warning, RDAP/WHOIS-sunset note + refreshed RDAP server examples (domain-checker). Frontmatter added to `semantic-coding` + `project-change-log` (were invisible to trigger matching).

### Fixed
- **skills**: Audit corrections from per-skill upstream verification (June 2026). `supabase-cli`: `db push` was documented (and scripted) as local-by-default — it targets the linked REMOTE; now explicit `--local`/`--linked` everywhere incl. 3 .ts scripts; replaced nonexistent commands (`db execute`→`db query -f`, `auth list`→`db query` on auth.users, `gen keys`→`gen signing-key`/`bearer-jwt`, `storage list-buckets/upload`→`storage ls/cp/mv/rm`, `branches switch`→`get/pause/unpause`); dropped unsupported `npm i -g supabase`. `salesforce-cli`: `sf schema generate sobject` misused as field-describe in 4 spots (it CREATES object metadata) → `sf sobject describe`; REST examples v60.0 → v67.0; `sf auth list` noted as legacy alias of `sf org list auth`. Next.js trio: deprecated `useFormState` → `useActionState` (4 files), single-arg `revalidateTag` → `(tag, 'max')` + `{expire: 0}`, added `refresh()` triad member + nested-cache gotcha, retired doc URLs → `/docs/app/guides/upgrading/`, added `npx @next/codemod upgrade` + `next upgrade` path + 4 v16 codemods, build step now ask-first. `gemini-cli`: default is `auto` routing (not `gemini-3-pro`); deprecated `-y` → `--approval-mode=yolo`. `n8n-cli`: API keys are JWTs (`eyJ…`), not `n8n_api_…` (4 files). `swiftui-patterns`: removed links to 2 nonexistent skills. CRLF→LF conversion across 68 scripts — all 5 `code-quality` bash scripts had hard syntax errors from `\r` (`fi\r`), and CRLF shebangs broke direct execution of ~60 Python scripts; everything now passes `bash -n`/`py_compile`.

## [1.7.3] - 2026-05-30

### Added
- **skills**: `agy-cli` gains a heartbeat-guarded runner (`scripts/agy_run.sh`) and a session preflight (`scripts/agy_preflight.sh`). The runner watches agy's `--log-file` and exits the moment agy finishes OR the log goes silent for `--stall` seconds (default 180), killing the whole process tree — turning the prior 10–45m blind wait on a stalled `/goal` into ≤3m detection. It prints a parseable `AGY_STATUS` block (done/stalled/timeout, exit 0/1/2/3, plus exit 4 + `AGY_ERROR_SIGNAL` on auth/quota) and surfaces the active model. Preflight does the session-start update check (keeps you on the newest build), reports the selected model, and repairs the 0-byte `~/.gemini/config/mcp_config.json` that throws on every startup. Behaviour verified empirically against agy 1.0.2→1.0.3 on macOS (healthy runs log every <4s; stall caught in ~13s in tests).

### Changed
- **skills**: Rework `agy-cli` SKILL.md — the heartbeat runner replaces the old "set a generous `--print-timeout` and blind-wait" advice (the root cause of the hangs); clarify there is no headless model flag (selection persists from REPL `/settings`, currently Gemini 3.5 Flash); flip the auto-update guidance to keep updates on for interactive use; add stall-cause and `mcp_config.json` gotchas.

## [1.7.2] - 2026-05-29

### Added
- **skills**: Add `vercel-cli` — safety-first wrapper for the latest Vercel CLI (`vercel`/`vc`) giving full project control with risk-tiered confirmation (Safe → execute, Write → inform, Destructive → `AskUserQuestion`, Forbidden → typed multi-step confirm). Embeds per-command doc URIs so it self-heals by fetching official docs (`/docs/cli/<command>`) when a command fails or is renamed. SKILL.md kept lean (~1741 tok, hot path) with the 4-tier model, decision flow, Forbidden list, production-deploy protocol, and doc-URI map; full command surface + safety rules in `references/`. Command tiers and subcommand names verified against live Vercel docs (May 2026) — including the routes/redirects/firewall staging model and `firewall system-mitigations pause` gated as Forbidden (removes DDoS protection).

## [1.7.1] - 2026-05-25

### Changed
- **commands**: `/plan-feature` swaps the deprecated `gemini` CLI for `@agy-cli` (Antigravity / Gemini 3) in the dual-AI validation step — tools allowlist `Bash(gemini *)` → `Bash(agy *)`. Verified `agy -p` patterns from the `@agy-cli` skill: 2 sequential calls only (shared OAuth quota — never parallel), `run_in_background: true` so the harness wakes on process exit (no polling), output-budget prompts (`≤N bullets, no code, do not modify files`), `--add-dir "$(pwd)"` for workspace access, `--print-timeout 10m`, and stop-and-report on `429` / `quota` / `RESOURCE_EXHAUSTED`. Also fixes the "Brainstore" typo, repairs the Related Skills table (drops 4 non-existent refs `@using-git-worktrees` `@component-refactor` `@beautiful-code` `@elements-of-style`; adds existing `@system-architect` `@owasp-security` `@plan-to-tdd` `@code-quality`), and updates the anti-patterns table with 4 new `agy`-specific traps (parallel calls, foreground execution, vague prompts, retry-on-429), the workflow-summary diagram (`Gemini` → `agy(Gem3)`), and the footer integration list.

## [1.7.0] - 2026-05-25

### Added
- **skills**: Add `agy-cli` — Google Antigravity CLI (`agy`) wrapper. Verified slash commands (`/help /goal /grill-me /schedule /diff /resume /usage /quota /config /settings /statusline`) from the changelog plus live testing (default chat ~18s outline vs `/goal` ~73s autonomous file-writing build). Headless `-p` patterns, conversation resume (`-c` / `--conversation`), workspace scoping (`--add-dir`), sandboxing, and the on-disk layout under `~/.gemini/antigravity-cli/` (conversations, brain, scratch, logs). Efficient-execution rules: `--print-timeout` is a ceiling not a sleep, always use `run_in_background` so the harness wakes on actual exit, no polling. Quota & abuse-heuristic safeguards: serialize calls (never parallel), reuse conversations with `-c`, no retry-on-failure loops, stop on `429`/`RESOURCE_EXHAUSTED`, `AGY_CLI_DISABLE_AUTO_UPDATE` in CI, always pair `--dangerously-skip-permissions` with `--sandbox` + narrow `--add-dir`.
- **skills**: Add `neon-postgres-agent-platforms` — Neon's official skill for multi-tenant AI agent platforms. 28 files including SKILL.md, 6 reference docs (checkpoint orchestration, compound checkpoints, management API samples, pricing, REST API), and 21 TypeScript control-plane scripts (auth-users, branch/snapshot/restore, consumption-query, transfer-project, versioning-flow, etc.). Wired into `scripts/check-skill-updates.js` for ongoing upstream tracking.

### Changed
- **gitignore**: Ignore `.antigravitycli/` — symlink folder agy drops into the workspace root pointing at `~/.gemini/config/projects/<uuid>.json`.
- **skills**: Sync `stripe-best-practices` from upstream — API version 2026-02-25.clover → 2026-04-22.dahlia, restricted API key (RAK) default recommendation, security reference, Stripe Tax routing row, Critical rules section (omit `payment_method_types` except for Terminal/card-present).
- **skills**: Sync `firecrawl-cli` from upstream — interact-vs-browser rename across the command surface, install-check verification block, references to `firecrawl-build` and `firecrawl-workflows` companion skills.
- **skills**: Sync `planning-with-files` from upstream v2.23.0 → v2.41.0 — SHA-256 plan attestation against prompt-injection, `.planning/`-scoped multi-project support, new PreCompact hook that preserves plan state across compaction, hardened skill-directory resolution.
- **scripts**: `generate-manifest.js` parser now handles YAML block-scalar strip/keep indicators (`>-` `>+` `|-` `|+`), not just bare `>` and `|`. Previously the indicator leaked into the first line of multi-line descriptions (e.g. Neon, Stripe).
- **scripts**: `generate-manifest.js` category detector uses word-boundary regex so `ui` no longer matches `build` and `auth` no longer matches `author`. Rules reordered most-specific → most-generic; added Postgres/MongoDB/Neon/Supabase/tenant/provisioning to backend, k8s/docker/terraform to devops. Neon now correctly categorized as backend.
- **skills**: Modernize `codex-cli` against Codex v0.132+ — validated every claim via `codex --help` and `codex doctor`. Now defers to the official `openai-codex` Claude Code plugin (`codex:setup`, `codex:rescue`) for delegation requests. Stops hardcoding model + reasoning effort (the skill had been pinned to deprecated `gpt-5.4` for months); examples use Codex's current default and `-m` / `-c 'model_reasoning_effort=…'` appear only as explicit-override patterns. Adds preflight (run `codex doctor` once per session to read current default model + surface available updates + check auth; never auto-update). Documents all six reasoning-effort levels (none/minimal/low/medium/high/xhigh), the three distinct dangerous flags (`--dangerously-bypass-approvals-and-sandbox`, `--dangerously-bypass-hook-trust`, deprecated `--full-auto`), missing flags (`--ephemeral`, `--json`, `--output-schema`, `--ignore-user-config`, `--ignore-rules`, `--add-dir`, `-i/--image`, `--oss`/`--local-provider`, `--no-alt-screen`), and new subcommands (`codex resume`, `codex exec resume`, `codex fork`, `codex apply`, `codex doctor`, `codex mcp`, `codex sandbox`, `codex features`, `codex update`). Adds background-execution rules (`run_in_background`, no polling), rate-limit safety (serialize calls, reuse sessions with `resume --last`, stop-and-report on 429, no retry loops), and comparison workflow with Claude.

### Fixed

## [1.6.0] - 2026-05-21

### Added
- **commands**: Add `/find-name` — brandable-name generator that scores candidates on length, memorability, brandability, cross-language safety, and spelling clarity, then filters by real domain availability. Asks a Q5 domain mode (ready-for-registration only · include registry-premium · include aftermarket/marketplace · include both) and threads it through the availability filter, scoring penalties (−8 premium, −10 aftermarket), console legend, top-3 rationale, hard rules, and the empty-accumulator fallback so premium/aftermarket reliance is always surfaced explicitly.
- **skills**: Add `domain-checker` — bulk domain availability checker. Python stdlib only (no pip, no API keys), parallel multi-TLD checks, three input modes (CLI args / file / stdin), bare-name + TLD-list expansion, table/JSON/CSV output, premium-tier and aftermarket detection.

## [1.5.1] - 2026-05-09

### Added
- **skills**: Add `n8n-cli` — comprehensive n8n automation management skill. 19 user-facing scripts + 2 internal helpers covering workflows, executions, credentials (metadata only), tags, projects, variables, source-control status, audit logs, backups, and diff. Two backends auto-detect: REST API (cloud + remote self-hosted, urllib stdlib) and `n8n` CLI (self-hosted only, full surface incl. encrypted/decrypted credential export). Read-only by default; mutations require `--confirm` + dry-run preview. Hard-blocks 14 destructive CLI prefixes and 21 destructive REST API endpoints (DELETE/PUT/PATCH/POST on workflows/credentials/executions/users/tags/variables/projects/source-control/license). CLI refusal guard uses flag-stripping + chain matching to defeat bypasses (e.g. `["--verbose", "delete:workflow"]`). Resource IDs regex-validated before URL interpolation (blocks path traversal). API client validates path against `/api/v1/` allowlist, enforces base-host pinning, redacts API key from error output, warns on http://. Decrypted credential export double-gated (`--decrypted` + `--confirm-secrets`). Output paths sanitized against shell-meaningful chars and system dirs. Audited by parallel general-purpose + Codex agents w/ ~20 issues fixed (correct `/activate`+`/deactivate` endpoints — n8n public API has no `/publish` or run endpoints, so `trigger_workflow` is CLI-only w/ webhook URL helper). Cloudflare-friendly User-Agent header (overridable via `N8N_USER_AGENT`). Live-tested against production: 16 read-only ops + 1 successful workflow create (revealed real n8n bug: `active` field is read-only on POST → fixed). 15/15 tests pass. 7 reference docs (CLI commands, REST API w/ auth, safety boundaries, backup strategy, CLI-vs-MCP comparison, quick recipes, troubleshooting).

## [1.5.0] - 2026-05-09

### Added
- **skills**: Add `mongodb-atlas-cli` — comprehensive MongoDB Atlas + mongosh skill. 21 scripts covering Performance Advisor reads (slow queries, suggested/drop indexes, schema advice, namespaces), cluster metrics, alerts, backups, events, Atlas Search & Vector Search list/create, mongosh-based index listing, query explain, profiler status, in-progress index build status, week-over-week audit diffs. Hard-blocks 44 destructive prefixes (delete/drop/restore/pause/terminate/kill/dbuser-write/network-change/cluster-update). Two-layer JS injection guard for all mongosh interactions. Password fed through stdin (not argv) to avoid `/proc/cmdline` exposure. Pre-flight duplicate detection w/ option awareness (unique/sparse/TTL/partial). Works on Atlas Cloud (full) + local Docker mongo (mongosh subset + `--print-mongosh`). 13/13 tests pass. 10 reference docs (CLI commands, Performance Advisor, index strategy, all 13+ index types, Atlas Search, local-vs-Atlas matrix, mongosh integration, quick recipes, safety boundaries, troubleshooting).

## [1.4.1] - 2026-03-16

### Added
- **commands**: Add 4 DevOps commands from wshobson/commands — docker-optimize (Dockerfile generation), k8s-manifest (Kubernetes YAML), db-migrate (migration files/rollback), doc-generate (OpenAPI/JSDoc/TypeDoc)
- **skills**: Add mermaid-diagram skill — 19 diagram types (flowchart, sequence, ER, class, state, pie, gantt, mindmap, timeline, gitgraph, C4, kanban, block, quadrant, sankey, XY, journey, requirement, architecture), Codex-audited, semantic colors, accessibility
- **skills**: Add excalidraw-diagram skill — Excalidraw JSON generation with Playwright rendering

## [1.4.0] - 2026-03-16

### Added
- **skills**: Add 13 external skills — frontend-design (Anthropic), webapp-testing (Anthropic), trailofbits-security (Trail of Bits), web-quality (Addy Osmani), stripe-best-practices (Stripe), terraform (HashiCorp), firecrawl-cli (Firecrawl), composition-patterns (Vercel), better-auth (Better Auth), planning-with-files (OthmanAdi), obsidian-skills (Kepano), claude-seo (AgriciDaniel), notebooklm-skill (PleasePrompto)
- **docs**: Create SKILLS.md, COMMANDS.md, MCP-SERVERS.md reference docs with install commands
- **cli**: Enhanced info command with author, source, risk, category labels, word-wrapped descriptions
- **scripts**: Add check-skill-updates.js to detect upstream changes for external skills
- **scripts**: Add generate-docs.js to auto-generate SKILLS.md, COMMANDS.md, cli/README.md from frontmatter
- **scripts**: Add generate-notice.js to auto-generate NOTICE with credits from source/author fields

### Changed
- **readme**: Slim down README to reference SKILLS.md, COMMANDS.md, MCP-SERVERS.md
- **scripts**: Manifest generator extracts author/source/risk from frontmatter, recursive file counting, smarter command descriptions
- **commands**: /git-commit auto-regenerates docs when skills/commands/scripts change
- **commands**: /git-npm-release runs all generators (manifest, docs, notice) before tagging

### Removed
- Removed empty CLAUDE.md

## [1.3.1] - 2026-03-16

### Changed
- **readme**: Move Quick Install section with npx commands to top of README, consolidate duplicate installation sections

## [1.3.0] - 2026-03-16

### Added
- **cli**: Add `npx claude-skills-vault` npm CLI for installing skills, commands, and MCP servers — list, install, search, info commands with giget-based GitHub downloads, path validation, version-pinned tags, CI-friendly non-TTY support, Codex-audited

### Changed
- **gitignore**: Scope Python `lib/` pattern to root only, add node_modules and lock file exclusions
- **readme**: Add npm installation section with `npx claude-skills-vault` usage examples

## [1.2.0] - 2026-03-16

### Added
- **skills**: Add multi-agent-patterns skill — orchestrator, peer-to-peer, and hierarchical multi-agent architectures with token economics and failure modes (from PR #5)
- **skills**: Add parallel-agents skill — native Claude Code agent orchestration with 17 specialist agents and 3 orchestration patterns (from PR #5)
- **skills**: Add vercel-react-native-skills — React Native and Expo best practices with 37 rules covering performance, animations, navigation, UI patterns (from PR #5)
- **skills**: Add owasp-security skill — OWASP Top 10:2025 security review, ASVS 5.0, and secure code patterns (from PR #6)
- **skills**: Add color-accessibility-audit skill — WCAG 2.1/2.2 contrast analysis with 5 Python scanners and color blindness simulation (from PR #6)
- **skills**: Add swift-concurrency skill — Swift 6.2 Approachable Concurrency patterns
- **skills**: Add swiftui-patterns skill — SwiftUI architecture, @Observable state management, view composition
- **skills**: Add ui-ux-pro-max skill — UI/UX design intelligence with 50 styles, 21 palettes, 9 framework stacks

### Changed
- **readme**: Add 8 new skills and 3 previously missing skills (data-wrangler, file-converter, salesforce-cli) to core skills table
- **readme**: Add contributor credits for garesuta (PR #5) and palakorn-moonholidays (PR #6)

## [1.1.9] - 2026-03-05

### Added
- **skills**: Add data-wrangler skill — production-grade tabular data manipulation using pandas & openpyxl with 2 scripts (data_wrangler.py: 18 operations — inspect, filter, sort, group, merge, pivot, dedupe, fill, drop, rename, cast, derive, sample, split, validate, formula, convert, query; excel_toolkit.py: 9 Excel operations — sheets, extract, combine, format, freeze, autofilter, validate, protect, create), pandas-patterns reference doc, file-converter integration, supports CSV/Excel/JSON/Parquet/TSV, all 27 operations tested and passing

### Changed
- **skills**: Update codex-cli skill — upgrade default model to gpt-5.4, add argument compatibility rules for exec/review, set medium reasoning effort as default
- **skills**: Update gemini-cli skill — add `-p` flag requirement for headless mode, update model table to Gemini 3+

### Fixed
- **config**: Add SSE type to monday-mcp server config

## [1.1.8] - 2026-02-09

### Added
- **skills**: Add salesforce-cli skill — safety-first Salesforce CLI (`sf` v2) wrapper with 4-tier risk classification (Safe/Write/Destructive/Forbidden), 4 safety-enforcing scripts (query, deploy, export, org-guard), 5 reference docs (safety rules, SOQL/SOSL, MCP integration, auth flows, data operations), production guardrails with typed alias confirmation, fail-safe org detection, PII warnings, destructive deploy blocking, governor limit checks, file-converter integration, and dual-AI security audit (Gemini 2.5 Pro + Codex GPT-5.2) with all critical/important findings fixed

## [1.1.7] - 2026-02-08

### Added
- **skills**: Add file-converter skill — 8 cross-platform conversion scripts (image resize/convert, markdown to HTML/PDF, HTML to markdown, CSV/JSON/YAML/TOML/XML, SVG, base64, text encoding) with shared platform_utils for native library loading on macOS/Linux/Windows, dual-AI audited (Gemini + Codex), 51 passing tests

## [1.1.6] - 2026-02-08

### Added
- **skills**: Add monday-com skill — Monday.com workspace management via official MCP server with direct API fallback, smart tool selection, safety classification, and comprehensive GraphQL reference docs

## [1.1.5] - 2026-02-07

### Removed
- **skills**: Remove deprecated beautiful-code, code-reviewer, pep8 (already merged into code-quality)
- **skills**: Remove deprecated prompt-compressor, token-formatter, elements-of-style (already merged into token-optimizer)

## [1.1.4] - 2026-02-07

### Added
- **skills**: Add react-best-practices skill — 45 Vercel Engineering performance rules across 8 categories (waterfalls, bundle size, server-side, client-side, re-render, rendering, JS perf, advanced patterns)
- **skills**: Add next-cache-components skill — Next.js 16 Cache Components with PPR, `use cache` directive, cacheLife, cacheTag, updateTag
- **skills**: Add next-upgrade skill — Next.js version upgrade workflow with codemods and migration guides
- **skills**: Add senior-backend skill — Node.js/Express/Fastify backend patterns with API scaffolding, database migration, and load testing scripts

### Changed
- **skills**: Enhance nextjs-senior-dev with 3 new references: scripts (next/script, 3rd-party loading), self-hosting (Docker standalone, multi-instance ISR), debug tricks (MCP debugging)

### Fixed
- **skills**: Remove non-standard metadata.json from react-best-practices causing incorrect CLI display

## [1.1.3] - 2026-02-07

### Added
- **skills**: Add github-cli skill — safety-first GitHub CLI wrapper with 4-tier risk classification (Safe/Write/Destructive/Forbidden), AskUserQuestion templates, and triple-confirmation protocol for dangerous operations
- **skills**: Add code-quality skill (merges beautiful-code + code-reviewer + pep8) with unified severity levels, review process, and multi-language standards
- **skills**: Add token-optimizer skill (merges prompt-compressor + token-formatter + elements-of-style) with prompt compression, doc formatting, prose clarity, and TOON integration

### Removed
- **skills**: Remove supabase-expert skill (consolidated into supabase-cli)
- **skills**: Deprecate beautiful-code, code-reviewer, pep8 (replaced by code-quality)
- **skills**: Deprecate prompt-compressor, token-formatter, elements-of-style (replaced by token-optimizer)

## [1.1.2] - 2026-02-07

### Added
- **skills**: Add brainstorm skill for collaborative idea refinement
- **skills**: Add codex-cli skill for OpenAI Codex CLI second-opinion audits
- **skills**: Add elements-of-style skill for clear writing following Strunk's style
- **skills**: Add supabase-cli skill for CLI automation (migrations, Edge Functions, type gen)
- **readme**: Add 5 missing skills to Core Skills table

### Changed
- **skills**: Refactor semantic-colors into semantic-coding (comprehensive design system: colors, typography, spacing, sizing, shadows, z-index)
- **commands**: Enhance plan-feature with brainstorm integration and updated template

## [1.1.1] - 2026-01-31

### Added
- **skills**: Add semantic-colors skill for automated refactoring of hardcoded colors to semantic design tokens

## [1.1.0] - 2026-01-30

### Added
- **skills**: Add upgrade-packages-js skill for safe package upgrades with breaking change detection
- **skills**: Add supabase-expert skill for production-grade Supabase development (RLS, auth, Edge Functions, enterprise)

### Changed
- **skills**: Rename uxui-tool to uiux-toolkit for clarity and consistency
- **commands**: Remove version bumping from git-commit (only adds to Unreleased)
- **commands**: Add interactive version selection to git-push (Patch/Minor/Major/Skip)

## [1.0.12] - 2026-01-21

### Changed
- **skills**: Rename ux-toolkit to uxui-tool (folder and frontmatter name aligned)
- **skills**: Apply token-formatter compression to uxui-tool SKILL.md (~40% reduction)
- **skills**: Add visual-design.md reference to uxui-tool

## [1.0.11] - 2026-01-14

### Added
- **skills**: Add test-levels skill for explaining Unit/Integration/E2E testing with car analogy and Playwright examples
- **skills**: Add plan-to-tdd skill for transforming feature plans into test-driven implementation using Outside-In methodology

### Changed
- **skills**: Normalize line endings (CRLF to LF) in doc-navigator and ux-toolkit skills

## [1.0.10] - 2026-01-10

### Added
- **ux-toolkit**: Add 4 new reference files (design-system-audit, content-ux-audit, ai-ux-patterns, privacy-ethics-audit)
- **ux-toolkit**: Add issues-database.json with 25 common UX issues and remediation guidance
- **ux-toolkit**: Add WCAG 2.2 coverage (all 9 new success criteria)
- **ux-toolkit**: Add modern UX methodologies (Cognitive Walkthrough, OOUX, JTBD, Six Minds, Baymard, Gestalt, Fitts's/Hick's Laws)

### Changed
- **ux-toolkit**: Expand SKILL.md with decision trees, priority matrix, effort estimation, platform adapters
- **ux-toolkit**: Enhance heuristic-audit.md with modern evaluation frameworks
- **ux-toolkit**: Update accessibility-inspector.md from WCAG 2.1 to WCAG 2.2
- **skills**: Add 'When to Use' sections to 7 skills (doc-navigator, fastapi-senior-dev, materialreacttable-mastery, mcp-builder, nextjs-senior-dev, skill-creator, testing-automation-expert)

## [1.0.9] - 2026-01-10

### Added
- **skills**: Add prompt-compressor skill for 40-60% token reduction on verbose prompts with protected content preservation
- **skills**: Add beautiful-code skill for multi-language code quality (TypeScript, Python, Go, Rust)
- **skills**: Add materialreacttable-mastery skill for MUI V3 data tables with CRUD, virtualization, server-side ops
- **skills**: Add nextjs-senior-dev skill for Next.js 15/16 App Router with 20 references, 6 styling-agnostic templates

### Changed
- **commands**: Compress plan-feature.md (~54% token reduction)

## [1.0.8] - 2026-01-10

### Added
- **commands**: Add git-review-pr command for comprehensive PR review (validates docs, quality, token optimization, markdown)

## [1.0.7] - 2026-01-10

### Added
- **readme**: Add code-reviewer and project-change-log skills to Core Skills
- **readme**: Add chrome-devtools MCP server to Third-Party servers

## [1.0.6] - 2026-01-10

### Added
- **skills**: Add doc-navigator skill for efficient codebase documentation navigation
- **skills**: Add ux-toolkit skill for comprehensive UX evaluation
- **commands**: Add create-pr command for GitHub pull request creation

### Changed
- Normalize line endings to LF for cross-platform consistency

### Fixed
- **readme**: Correct toon skill description to Token-Oriented Object Notation

## [1.0.5] - 2026-01-05

### Added
- **skills**: Add pep8 skill for Python 3.11+ style enforcement with check/fix scripts

### Changed
- **readme**: Add pep8 skill to core skills list

## [1.0.4] - 2026-01-05

### Added
- **mcp-servers**: Add chrome-devtools MCP server reference

### Changed
- **commands**: Enhance plan-feature with AskUserQuestion tool for interactive requirement gathering
- **skills**: Streamline fastapi-senior-dev with modular reference files (security, database, caching, observability, microservices, API lifecycle, production ops)

## [1.0.3] - 2026-01-05

### Added
- **skills**: Add gemini-cli skill for local Gemini CLI interaction (run queries, compare responses)
- **skills**: Add fastapi-senior-dev skill for production-ready FastAPI development
- **skills**: Add testing-automation-expert skill for comprehensive testing strategies
- **commands**: Add plan-feature command for production-grade feature planning

### Changed
- **commands**: Rename commit.md to git-commit.md for clarity
- **commands**: Rename push.md to git-push.md for clarity
- **readme**: Update commands table (renamed commands, add plan-feature)
- **readme**: Add new skills to Core Skills table
- **readme**: Add Changelog section with link to CHANGELOG.md

## [1.0.2] - 2026-01-04

### Added
- **mcp-servers**: Add 35 MCP server configurations and references
  - Official active: everything, fetch, filesystem, memory, sequential-thinking, time
  - Official archived: git, slack, sqlite
  - AWS Labs: 64+ servers (documentation, infrastructure, AI/ML, data, operations)
  - Third-party: Stripe, Netlify, Vercel, Canva, Sentry, PostHog, Atlassian, Monday, Figma, Linear, Notion, Playwright, Puppeteer, Airtable, GCP, MUI, Next.js, Kubernetes, Cloudflare, Codex, Context7, GitHub
  - Custom implementations with source: MongoDB, Supabase
  - SDK references for all 10 official MCP SDKs (TypeScript, Python, Go, Rust, Java, Kotlin, C#, Swift, Ruby, PHP)

### Changed
- **commands**: Add explicit invocation guards to commit.md and push.md (prevent auto-execution)
- **commands**: Remove add-mcp command
- **readme**: Add Contributing section
- **readme**: Update with comprehensive MCP server documentation (35 servers, SDK references)

## [1.0.1] - 2026-01-04

### Added
- **commands**: Add push command with uncommitted changes check and changelog versioning
- **skills**: Add mcp-builder skill with Python/Node reference docs and evaluation scripts
- **skills**: Add toon skill for token-optimized JSON notation (~40% token reduction)
- **commands**: Add comprehensive create-skill command with testing requirements
- **commands**: Add add-mcp command for MCP server setup
- CLAUDE.md project configuration file

### Changed
- Replace preview.webp with preview.jpg and add to README
- **commands**: Clarify changelog requirement in commit command as REQUIRED step
- **commands**: Compress commit.md using token-formatter (~54% reduction)
- **commands**: Make commit command dynamic (use git config for author)
- **skills**: Add author credits to document-skills (ComposioHQ for xlsx/pdf/pptx/docx, George Khananaev for toon/md)
- **skills**: Add YAML frontmatter to token-formatter and md skills
- **skills**: Remove redundant cheatsheet.md from token-formatter (content in SKILL.md)
- Update .gitignore with additional patterns
- Update README.md

## [1.0.0] - 2026-01-04

### Added
- **skills**: Comprehensive Claude skills collection (code-reviewer, system-architect, pydantic-model, skill-creator, token-formatter, project-change-log)
- **skills**: Document processing skills (docx, pdf, pptx, xlsx, md) with OOXML schemas
- **commands**: Commit command with conventional commits and changelog integration
- **mcp-servers**: PostgreSQL and Jira MCP server templates
- **tutorials**: Commands, Skills, and MCP Servers tutorials
- NOTICE file for attribution guidelines
- README with project documentation
