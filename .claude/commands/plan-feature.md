---
name: plan-feature
description: Production-grade feature planning with dual-AI validation (Claude + Antigravity/Gemini 3 via `agy`)
tools:
  - AskUserQuestion
  - Bash(agy *)
  - Read
  - Write
  - Glob
  - Grep
  - WebSearch
---

# Plan Feature Command

**Trigger: `/plan-feature` only. Creates production-grade implementation plans with dual-AI validation.**

**Announce**: "I'm using the plan-feature skill to create an implementation plan."

**Output**: Save plan to `docs/plans/YYYY-MM-DD-<feature-name>.md`

## 0. Pre-Check: Is the Idea Ready?

Before planning, assess if requirements are clear enough:

| Signal | Action |
|--------|--------|
| User says "I want to add..." with vague details | Use `@brainstorm` skill first to refine the idea |
| Multiple valid approaches, unclear trade-offs | Use `@brainstorm` to explore options |
| User isn't sure what they want | Use `@brainstorm` for collaborative discovery |
| Requirements are clear and specific | Proceed to Discovery Phase below |

**Brainstorm produces**: Design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`
**Plan-feature produces**: Implementation plan with TDD tasks

Typical flow for new features: `@brainstorm` → `/plan-feature` → Execute

## 1. Discovery Phase (Adaptive)

### Round 1: Core Questions (ALWAYS)

Use `AskUserQuestion`:

| Q# | Question | Header | Options |
|----|----------|--------|---------|
| 1 | What user problem does this solve? | Problem | [Describe, Show existing code] |
| 2 | What's explicitly OUT of scope? | Anti-scope | [List exclusions, Nothing specific, Help define] |
| 3 | Risk level if this fails in prod? | Risk | [Critical, High, Medium, Low] |

### Round 2: Adaptive Questions

Based on Round 1, ask ONLY relevant follow-ups:

| Trigger | Questions to Ask |
|---------|------------------|
| DB likely (data/store/CRUD keywords) | Schema changes? Migration strategy? |
| Frontend (UI/page/component) | WCAG level? Design specs available? |
| Security-sensitive (Risk=Critical/High OR auth/payment/PII) | Compliance (SOC2/GDPR)? Security requirements? |
| New dependencies (library/integration/API) | Alternatives evaluated? Vendor lock-in? |
| Performance-critical | Latency budget? Expected load? |

### Exit Criteria

Stop when: Requirements unambiguous, edge cases documented, success metrics defined.

**Rule: Keep asking until EVERYTHING is clear. Never guess.**

## 2. Research Phase

### Codebase Archaeology

```bash
# Find similar patterns
Grep: "similar feature keywords"
Glob: affected file patterns
Read: existing architecture
```

### External Research (if gaps)

- Context7: Framework best practices
- WebSearch: Latest docs, security advisories

### Pre-Mortem

Before drafting, answer:
- "If this fails in 6 months, what caused it?"
- "What breaks at 10x scale?"

## 3. Plan Template (7 Sections)

```markdown
# Feature: [Name]

## 1. Overview
- **Goal**: One-line summary
- **Success Metrics**: How we measure success
- **In Scope**: What we ARE building
- **Out of Scope**: What we are NOT building
- **Tech Stack**: [e.g., React, Supabase, Bun]

## 2. Architecture

### Component Flow
[Component A] → [Component B] → [Component C]

### Data Model (if applicable)
- Schema changes
- Migration: Expand-Contract pattern (zero-downtime)

### Security (if applicable)
| Risk | Mitigation |
|------|------------|
| XSS | Input sanitization, CSP |
| Injection | Parameterized queries |

### Performance (if applicable)
- Caching strategy (TTL, invalidation)
- Query optimization (indexes, N+1)

## 3. Implementation Tasks

Each task follows TDD cycle: failing test → verify failure → implement → verify success → commit

### Phase 1: Setup

#### Task 1.1: [Task Name]
**Files:**
- Create: `src/features/example/Example.test.ts`
- Modify: `src/features/example/Example.ts`

**Test First:**
```typescript
// src/features/example/Example.test.ts
import { test, expect } from "bun:test";
import { exampleFunction } from "./Example";

test("should do X when Y", () => {
  const result = exampleFunction("input");
  expect(result).toBe("expected");
});
```

**Run & Verify Failure:**
```bash
bun test src/features/example/Example.test.ts
# Expected: FAIL - exampleFunction not defined
```

**Implement:**
```typescript
// src/features/example/Example.ts
export function exampleFunction(input: string): string {
  return "expected";
}
```

**Run & Verify Success:**
```bash
bun test src/features/example/Example.test.ts
# Expected: PASS
```

**Commit:**
```bash
git add src/features/example/
git commit -m "feat(example): add exampleFunction with tests"
```

### Phase 2: Core
- [ ] Task 2.1: [Same detailed format]
- [ ] Task 2.2: [Same detailed format]

### Phase 3: Integration
- [ ] Task 3.1: [Same detailed format]
- [ ] Rollback checkpoint ←

## 4. Testing Strategy
| Type | Coverage | Focus | Files |
|------|----------|-------|-------|
| Unit | 80%+ | Core logic | `*.test.ts` |
| Integration | APIs | Contracts | `*.integration.test.ts` |
| E2E | Critical paths | User flows | `e2e/*.spec.ts` |

## 5. Rollout & Observability
| Stage | % Users | Duration | Success Criteria |
|-------|---------|----------|------------------|
| Canary | 1% | 24h | Error <0.1% |
| Beta | 10% | 48h | P95 <Xms |
| GA | 100% | - | All green |

**Logs**: Key events | **Metrics**: Latency, errors | **Alerts**: Thresholds

## 6. Rollback Plan
1. Disable feature flag (instant)
2. Revert migration (if needed)
3. Restore cached data

## 7. Execution Checklist
- [ ] All tasks have failing test first
- [ ] Each task is 2-5 minutes of work
- [ ] File paths are exact and verified
- [ ] Commands include expected output
- [ ] Commits are atomic per task
```

## 4. Dual-AI Validation

### Step 1: Claude Self-Check (Internal - Free)

Before external validation, verify:

| Check | Method | Pass Criteria |
|-------|--------|---------------|
| Pattern compliance | Grep similar features | Matches codebase conventions |
| Dependency impact | Trace imports | No circular deps |
| Test coverage | Map reqs → tests | All paths testable |
| Migration safety | Review schema changes | Expand-contract followed |
| Task granularity | Review each task | 2-5 min TDD cycles |

**Output**: Checklist with [PASS/FAIL]

### Step 2: Antigravity (`agy`) Validation — External, Gemini 3

Only run after Claude checks pass. Two sequential calls, never parallel.

**Hard rules (from `@agy-cli` skill):**
- **Never run two `agy -p` processes at once** — Antigravity shares a single OAuth quota and rate-limits aggressively
- **Default chat mode only** (no `/goal`, no `/grill-me`) — these are read-only review tasks
- **Always `run_in_background: true`** — the harness wakes Claude on process exit, no polling needed
- **Constrain output length** explicitly in the prompt — `/goal`-style vague reviews burn quota for nothing
- **Add the workspace** with `--add-dir "$(pwd)"` so `agy` can read referenced files
- **On `429` / `quota` / `RESOURCE_EXHAUSTED`**: stop, surface to user, do not retry

**Call 1 — Security + SRE Audit:**
```bash
# Run in background; harness re-invokes Claude on exit.
agy --add-dir "$(pwd)" --print-timeout 10m -p "Act as Security Engineer + SRE. \
Review the plan below. Answer in ≤10 bullets total, no code, do not modify files.
1. OWASP Top 10:2025 vulnerabilities in this design
2. Failure modes at 10x current scale
3. What wakes oncall at 3 AM

Plan sections 1-3:
<paste overview, architecture, implementation tasks>"
```

**Call 2 — Pre-Mortem + Edge Cases (only after Call 1 returns):**
```bash
agy --add-dir "$(pwd)" --print-timeout 10m -p "Pre-mortem: assume this feature has failed in production 6 months from now. \
Answer in ≤8 bullets, no code, do not modify files.
1. Top 3 most likely root causes
2. Edge cases the plan misses (≤5)
3. Readiness rating 1-10, one-line reason

Implementation tasks:
<paste section 3 only>"
```

> If `--add-dir "$(pwd)"` would expose secrets/IP the audit doesn't need, omit it and inline the plan text in the prompt instead.

### Step 3: Gap Resolution

For each gap `agy` surfaces:
1. Research solution (WebSearch, Context7)
2. Update the plan in place
3. Re-validate **only** the section that changed — don't re-run both calls

### Acceptance Criteria

- [ ] Claude: all internal checks PASS
- [ ] agy Call 1: no Critical security findings
- [ ] agy Call 2: rating ≥ 8/10, top-3 failures addressed in plan

## 5. Execution Handoff

After plan approval, offer:

### Option A: Task-by-Task (Same Session)
Execute each task sequentially with code review between tasks:
```
Task 1.1 → Review → Task 1.2 → Review → ...
```

### Option B: Batch Execution (New Session)
Hand off to fresh session with plan file:
```bash
# In new session:
"Execute plan at docs/plans/YYYY-MM-DD-feature.md starting from Task 1.1"
```

## 6. Workflow Summary

```
DISCOVER → RESEARCH → PLAN → VALIDATE → REFINE → EXECUTE
    │          │         │        │         │         │
 Adaptive   Grep+C7   7-section  Claude→   Iterate   Task-by-task
 questions            template   agy(Gem3) until 8+  or batch
```

## 7. Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Guess requirements | Use AskUserQuestion iteratively |
| Ask all 10 questions | Adaptive — only relevant ones |
| Skip Claude validation | Always self-check first (free) |
| Run 4+ `agy` calls | 2 sequential calls only (shared OAuth quota) |
| Run `agy -p` in foreground | Always `run_in_background: true`, let exit-notification wake Claude |
| Run two `agy -p` in parallel | Strictly sequential — Antigravity rate-limits aggressively |
| Vague `agy` prompts | Cap output (`≤N bullets`), say "do not modify files" |
| Retry on `429`/quota error | Stop and report — never auto-retry |
| Over-engineer | Minimal viable, iterate |
| Destructive migrations | Additive-only, expand-contract |
| Skip observability | Every feature needs monitoring |
| Vague task descriptions | Exact file paths, code samples, commands |
| Large tasks | Break into 2–5 minute TDD cycles |
| Skip expected output | Every command shows success/failure |

## 8. Related Skills

Reference these skills during planning and execution:

| Phase | Skill | Use When |
|-------|-------|----------|
| **Discovery** | `@brainstorm` | Vague requirements need refinement before planning |
| **Discovery** | `@agy-cli` | Need autonomous Gemini-3 second opinion or build delegation |
| **Architecture** | `@system-architect` | Microservices/monolith, DB choice, scalability planning |
| **Design** | `@semantic-coding` | Designing component/system structure |
| **Design** | `@uiux-toolkit` | UI/UX audit or accessibility review |
| **Security** | `@owasp-security` | Auth, payments, PII — OWASP Top 10:2025 hardening |
| **Implementation** | `@plan-to-tdd` | Convert this plan into Outside-In TDD tasks |
| **Implementation** | `@code-quality` | TS/Python/Go/Rust standards and review |
| **Testing** | `@testing-automation-expert` | Unit/integration/E2E strategy + CI gates |
| **Database** | `@supabase-cli` | Migrations, Edge Functions, type gen |
| **Dependencies** | `@upgrade-packages-js` | Safe package upgrades with migrations |

---
Integrates: brainstorm, agy-cli, context7, AskUserQuestion | ~1000 tokens
