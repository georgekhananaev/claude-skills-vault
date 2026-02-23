---
name: plan-feature
description: Production-grade feature planning with dual-AI validation (Claude + Gemini)
tools:
  - AskUserQuestion
  - Bash(gemini *)
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

**Brainstore produces**: Design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`
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

### Step 2: Gemini Validation (External - 2 Calls)

Only if Claude checks pass:

**Call 1 - Security + SRE:**
```bash
gemini "Act as Security Engineer + SRE. Review for:
1. OWASP vulnerabilities
2. Failure modes at 10x scale
3. What wakes you at 3 AM?
Plan summary: [sections 1-3]"
```

**Call 2 - Pre-Mortem + Edge Cases:**
```bash
gemini "This feature failed 6 months from now.
1. Top 3 most likely causes
2. Missed edge cases
3. Rate readiness 1-10
Implementation: [section 3 only]"
```

### Step 3: Gap Resolution

For each gap found:
1. Research solution (WebSearch, Context7)
2. Update plan
3. Re-validate affected section only

### Acceptance Criteria

- [ ] Claude: All internal checks PASS
- [ ] Gemini Call 1: No Critical security issues
- [ ] Gemini Call 2: Rating >= 8/10, top failures addressed

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
 questions            template   Gemini    until 8+  or batch
```

## 7. Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Guess requirements | Use AskUserQuestion iteratively |
| Ask all 10 questions | Adaptive - only relevant ones |
| Skip Claude validation | Always self-check first (free) |
| Run 4 Gemini calls | Consolidate to 2 targeted calls |
| Over-engineer | Minimal viable, iterate |
| Destructive migrations | Additive-only, expand-contract |
| Skip observability | Every feature needs monitoring |
| Vague task descriptions | Exact file paths, code samples, commands |
| Large tasks | Break into 2-5 minute TDD cycles |
| Skip expected output | Every command shows success/failure |

## 8. Related Skills

Reference these skills during planning and execution:

| Phase | Skill | Use When |
|-------|-------|----------|
| **Discovery** | `@brainstorm` | Vague requirements need refinement |
| **Discovery** | `@gemini-cli` | Need second opinion on approach |
| **Design** | `@semantic-coding` | Designing component/system structure |
| **Design** | `@uiux-toolkit` | UI/UX audit or accessibility review |
| **Implementation** | `@using-git-worktrees` | Need isolated workspace for feature |
| **Implementation** | `@component-refactor` | Breaking down large React components |
| **Implementation** | `@beautiful-code` | Code quality standards (TS/Python/Go/Rust) |
| **Testing** | `@testing-automation-expert` | Unit/integration/E2E test strategy |
| **Documentation** | `@elements-of-style` | Writing clear docs, commit messages |
| **Database** | `@supabase-cli` | Migrations, Edge Functions, type gen |
| **Dependencies** | `@upgrade-packages-js` | Safe package upgrades with migrations |

---
Integrates: brainstorm, gemini-cli, context7, AskUserQuestion | ~1000 tokens
