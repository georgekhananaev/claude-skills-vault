# Plan Feature Command

**IMPORTANT: This command ONLY runs when explicitly invoked via `/plan-feature`. Creates production-grade implementation plans with multi-source validation.**

Goal: Generate bulletproof feature plans using iterative discovery, external validation, and AI cross-checking.

## 1. Planning Principles

| Principle | Focus |
|-----------|-------|
| Efficiency | Minimal code, max impact, optimal algorithms |
| Security | OWASP top 10, input validation, auth patterns |
| Observability | If it's not logged/measured, it doesn't exist |
| Reversibility | Feature flags first, DB migrations backward-compatible |
| Clean Design | SOLID, DRY, separation of concerns |

## 2. Discovery Phase (REQUIRED)

### Step 1: Initial Questions

**IMPORTANT: Use the `AskUserQuestion` tool to gather requirements interactively.**

Ask these questions using `AskUserQuestion` with appropriate options. Group related questions (max 4 per call):

**Round 1 - Core Value & Scope:**
```
Use AskUserQuestion with these questions:
1. Question: "What user problem does this solve?"
   Header: "Problem"
   Options: [Custom input expected - use open-ended options like "Let me describe...", "Show existing code"]

2. Question: "What are the success criteria?"
   Header: "Success"
   Options: ["Quantitative metrics", "Qualitative feedback", "Both", "Not sure yet"]

3. Question: "What is explicitly OUT OF SCOPE?"
   Header: "Anti-scope"
   Options: ["I'll list exclusions", "Nothing specific", "Need help defining"]
```

**Round 2 - Technical Context:**
```
Use AskUserQuestion:
4. Question: "Does this involve database schema changes?"
   Header: "Database"
   Options: ["Yes - new tables", "Yes - modify existing", "No changes", "Not sure"]

5. Question: "Are there existing patterns we MUST follow?"
   Header: "Patterns"
   Options: ["Yes, I'll specify", "Use codebase conventions", "No constraints", "Need guidance"]
```

**Round 3 - Risk & Constraints:**
```
Use AskUserQuestion:
6. Question: "What happens if this feature fails in production?"
   Header: "Risk Level"
   Options: ["Critical - system down", "High - major impact", "Medium - degraded", "Low - minimal"]

7. Question: "Any security/privacy requirements?"
   Header: "Security"
   Options: ["PII handling", "Auth/AuthZ", "Compliance (SOC2/GDPR)", "Standard practices only"]

8. Question: "Performance budgets?"
   Header: "Performance"
   Options: ["Strict latency < 100ms", "Standard < 500ms", "Relaxed < 2s", "No specific target"]
```

**Round 4 - Historical Context:**
```
Use AskUserQuestion:
9. Question: "Have we tried building this before?"
   Header: "History"
   Options: ["Yes - failed", "Yes - partial", "No - first attempt", "Unknown"]

10. Question: "Will this require new dependencies or infrastructure?"
    Header: "Dependencies"
    Options: ["New libraries", "New infrastructure", "Both", "None expected"]
```

### Step 2: Deep Dive Questions (Iterative)

Continue using `AskUserQuestion` for follow-ups until:
- [ ] Requirements are unambiguous
- [ ] "Sad path" flows are defined
- [ ] Integration seams identified
- [ ] New dependencies justified
- [ ] Edge cases documented
- [ ] Success criteria measurable

**Rule: Keep using AskUserQuestion until you have EVERYTHING needed. Never guess.**

## 3. Research Phase

### Step 1: Context7 Best Practices

Use Context7 MCP tools to fetch framework-specific patterns:

```bash
# 1. Find library ID
resolve-library-id "<framework-name>"

# 2. Get architectural patterns & best practices
get-library-docs --libraryId "<id>" --mode info
```

Query for:
- Framework-specific patterns
- Latest API design guidelines
- Performance optimization techniques
- Security best practices

### Step 2: Codebase Archaeology

Before planning:
1. `Grep` - Find similar features/patterns
2. `Glob` - Identify affected files
3. `Read` - Understand existing architecture
4. Check for potential circular dependencies

### Step 3: Pre-Mortem Simulation

Before drafting plan, ask:
- "If this fails in 6 months, what was the cause?"
- "Where is it most likely to break?" (race conditions, scale, timeouts)
- "What's the worst-case failure mode?"

### Step 4: Web Research (If Gaps Exist)

For knowledge gaps:
- Search latest documentation
- Check security advisories
- Review framework changelogs
- Find proven solutions

## 4. Plan Structure

Create plan with these sections:

```markdown
# Feature: [Name]

## 1. Overview
- **Goal**: One-line summary
- **Value**: Why we're building this
- **In Scope**: What we ARE building
- **Out of Scope**: What we are NOT building (explicit exclusions)

## 2. Requirements Summary
| Requirement | Detail | Priority |
|-------------|--------|----------|
| Core | ... | P0 |
| Secondary | ... | P1 |
| Nice-to-have | ... | P2 |
| Accessibility | WCAG compliance level, a11y needs | P0 |

## 3. Architecture & Design

### Component Diagram
```
[Component A] → [Component B] → [Component C]
```

### Data Flow
1. Entry point
2. Processing steps
3. Exit point

### Data Model & Migration
- **Schema Changes**: SQL/NoSQL structure
- **Migration Strategy**: Use Expand-Contract pattern for zero-downtime
  1. EXPAND: Add new column/table (backward compatible)
  2. MIGRATE: Write to both old & new, backfill existing data
  3. CONTRACT: Switch reads to new, remove old
- **Destructive Actions**: Data loss risks?
- **Rollback SQL**: Reverse migration script

## 4. Implementation Steps

### Phase 1: Preparation
- [ ] Feature flag setup
- [ ] Interface definitions / contracts
- [ ] Database migrations (additive only)

### Phase 2: Core Implementation
- [ ] Step 2.1: ...
- [ ] Step 2.2: ...

### Phase 3: Integration
- [ ] Step 3.1: ...
- [ ] Step 3.2: ...

### Phase 4: Polish & Documentation
- [ ] Update README/API docs
- [ ] Add usage examples
- [ ] Clean up temporary code

## 5. Operational Readiness

### Observability
| Type | Implementation |
|------|----------------|
| Logs | Key events, error contexts |
| Metrics | Latency, error rate, throughput |
| Alerts | Threshold-based triggers |
| Dashboard | Key metrics visualization |

### Rollout Strategy
| Stage | % Users | Duration | Criteria |
|-------|---------|----------|----------|
| Canary | 1% | 24h | Error rate < 0.1% |
| Beta | 10% | 48h | P95 latency < X ms |
| GA | 100% | - | All metrics green |

### Resource & Cost Impact
- **Compute**: Estimated CPU/memory increase
- **Storage**: Additional DB/cache/blob storage
- **Network**: Expected bandwidth changes
- **Third-party**: New API costs (if any)
- **Infrastructure**: New services/containers required

## 6. Security Considerations
| Risk | Mitigation |
|------|------------|
| XSS | Input sanitization, CSP |
| Injection | Parameterized queries |
| AuthZ | Role-based checks |
| PII | Encryption, access logs |

## 7. Performance Strategy
- Caching approach (TTL, invalidation)
- Query optimization (indexes, N+1 prevention)
- Lazy loading / pagination
- Resource pooling

## 8. Testing Strategy
| Type | Coverage | Focus |
|------|----------|-------|
| Unit | 80%+ | Core logic |
| Integration | APIs | Contracts |
| E2E | Critical paths | User flows |
| Edge Cases | Specific | Tricky inputs |
| Accessibility | a11y | Screen reader, keyboard nav, WCAG |

## 9. Rollback Plan
1. Disable feature flag (instant)
2. Revert migration (if needed)
3. Restore cached data
4. Notify stakeholders

## 10. Success Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Adoption | X% | Analytics |
| Latency | <X ms | P95 |
| Errors | <0.1% | Monitoring |

## 11. Post-Implementation Review (PIR)
- **Review Date**: [Launch + 2 weeks]
- **Metrics Check**: Validate all success metrics hit
- **Lessons Learned**: What worked, what didn't
- **Action Items**: Follow-up improvements
```

## 5. Validation Phase (REQUIRED)

### Step 1: Persona-Based Gemini Evaluation

Run targeted reviews with specific personas:

```bash
# Security Auditor Persona
gemini "Act as a Senior Security Engineer. Review this plan for OWASP vulnerabilities, IDOR issues, and PII leaks. Be critical: [plan summary]"

# SRE/Ops Persona (3 AM test)
gemini "Act as a Site Reliability Engineer. Review for bottlenecks, race conditions, and failure modes at 10x scale. What will wake me at 3 AM? [plan summary]"

# Architecture Review
gemini "Review architecture decisions. Identify coupling issues, scalability concerns, and anti-patterns: [architecture section]"

# Edge Case Hunter
gemini "Find logical gaps, missing edge cases, and unhappy paths in these implementation steps: [implementation section]"
```

### Step 2: Gap Analysis

After Gemini review, check:
- [ ] All requirements addressed?
- [ ] Security gaps closed?
- [ ] Performance bottlenecks mitigated?
- [ ] Edge cases covered?
- [ ] Observability complete?
- [ ] Rollback tested?

**If gaps found:**
1. Research solutions (WebSearch, Context7)
2. Run additional Gemini queries
3. Update plan with findings
4. Re-validate affected sections

### Step 3: Final Validation

```bash
# Pre-mortem check
gemini "Imagine this feature failed 6 months from now. What was the cause? Review: [complete plan]"

# Final sanity check
gemini "Final review. Rate implementation readiness 1-10. List any blocking issues or remaining concerns: [complete plan]"
```

**Acceptance criteria: Gemini rating >= 8/10**

## 6. Execution Flow

```
1. DISCOVER (use AskUserQuestion tool)
   ├── Round 1: Core value & scope questions
   ├── Round 2: Technical context questions
   ├── Round 3: Risk & constraints questions
   ├── Round 4: Historical context questions
   ├── Deep dive follow-ups (iterative)
   └── Get explicit sign-off

2. RESEARCH
   ├── Context7 best practices
   ├── Codebase archaeology
   ├── Pre-mortem simulation
   └── Web research (if gaps)

3. PLAN
   ├── Draft architecture
   ├── Define data model
   ├── Write implementation steps
   ├── Add observability plan
   ├── Include rollout strategy
   └── Define rollback procedures

4. VALIDATE
   ├── Security Auditor (Gemini)
   ├── SRE/Ops review (Gemini)
   ├── Architecture check (Gemini)
   ├── Gap analysis
   └── Final rating check

5. REFINE
   ├── Incorporate all feedback
   ├── Close remaining gaps
   ├── Update documentation
   └── Finalize plan
```

## 7. Quality Gates

Before completing, verify:

- [ ] **Anti-Scope**: Confirmed we aren't building unnecessary things
- [ ] **Clarity**: Non-technical person can understand the goal
- [ ] **Completeness**: All requirements addressed
- [ ] **Data Safety**: Migration plan is non-destructive
- [ ] **Security**: OWASP considerations, PII handling defined
- [ ] **Performance**: Optimization strategies with targets
- [ ] **Observability**: Logs, metrics, alerts defined
- [ ] **Reversibility**: Can disable via feature flag instantly
- [ ] **Testing**: Coverage strategy complete
- [ ] **Accessibility**: a11y requirements defined (if UI)
- [ ] **Cost Impact**: Resource estimates documented
- [ ] **Documentation**: README/API docs update planned
- [ ] **PIR Scheduled**: Review date set for launch + 2 weeks
- [ ] **Validated**: Gemini personas approved (8+/10)

## 8. Anti-Patterns (AVOID)

| Don't | Do Instead |
|-------|------------|
| Guess requirements | Use AskUserQuestion tool iteratively |
| Output questions as text | Use AskUserQuestion with options |
| Skip validation | Always run all Gemini personas |
| Ignore gaps | Research until resolved |
| Over-engineer | Keep it minimal, iterate |
| Generic solutions | Use project-specific patterns |
| Destructive migrations | Additive-only, backward-compatible |
| Skip observability | Every feature needs monitoring |
| Hardcode rollout | Use feature flags always |

## 9. Output Format

Final plan should be:
- Clean markdown formatting
- Tables for structured data
- Code blocks for examples
- Mermaid diagrams where helpful
- Actionable checklist items
- Clear success criteria

---
Tokens: ~1100 | Integrates with: gemini-cli, context7, WebSearch, AskUserQuestion, codebase tools