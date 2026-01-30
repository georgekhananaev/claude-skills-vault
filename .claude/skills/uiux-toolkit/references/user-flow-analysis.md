# User Flow Analysis

Evaluate task paths, identify friction points, and assess cognitive load throughout user journeys.

## Flow Mapping

### Flow Documentation Template

```
Flow: [Name]
Goal: [What user wants to accomplish]
Entry: [Where user starts]
Exit: [Success state]

Steps:
1. [Action] → [Result] → [Next screen]
2. [Action] → [Result] → [Next screen]
...

Decision Points:
- [Where users must choose]
- [Branching paths]

Error Paths:
- [What can go wrong]
- [Recovery mechanism]
```

### Flow Types

| Type | Description | Key Metrics |
|------|-------------|-------------|
| Happy Path | Ideal completion | Steps, time |
| Error Path | When things go wrong | Recovery rate |
| Edge Cases | Unusual scenarios | Handling quality |
| Return User | Repeat task | Efficiency |

---

## Friction Point Analysis

### Friction Categories

| Category | Signs | Impact |
|----------|-------|--------|
| **Cognitive** | Confusion, hesitation | Drop-off |
| **Interaction** | Mis-taps, retries | Frustration |
| **Technical** | Slow loading, errors | Abandonment |
| **Emotional** | Anxiety, distrust | Bounce |

### Common Friction Points

| Friction | Detection | Severity |
|----------|-----------|----------|
| Unclear next step | No visible CTA | 🔴 Critical |
| Too many choices | Decision paralysis | 🟠 Major |
| Unexpected page | Flow disruption | 🟠 Major |
| Required info not ready | Abandonment | 🟠 Major |
| Form too long | Fatigue | 🟠 Major |
| Hidden costs | Trust break | 🔴 Critical |
| Account required early | Bounce | 🟠 Major |
| Slow response | Perceived failure | 🟠 Major |
| Unclear error | Can't recover | 🔴 Critical |

### Friction Audit Checklist

```
□ Clear value proposition at entry
□ Progress visibility (where am I?)
□ Single primary action per screen
□ Required info communicated upfront
□ Inline validation (not just on submit)
□ Back/undo always available
□ Data preserved on errors
□ Guest options before account
□ Trust signals at commitment points
□ Confirmation at completion
```

---

## Cognitive Load Assessment

### Load Types

| Type | Description | Reduce By |
|------|-------------|-----------|
| **Intrinsic** | Task complexity | Simplify steps |
| **Extraneous** | Poor design | Better UX |
| **Germane** | Learning effort | Progressive disclosure |

### Cognitive Load Indicators

| Indicator | High Load Sign | Target |
|-----------|----------------|--------|
| Choices per screen | >7 options | 3-5 options |
| Info to remember | Multi-screen | Single screen |
| New concepts | Many at once | Introduce gradually |
| Visual complexity | Cluttered | Clean hierarchy |
| Reading required | Walls of text | Scannable |

### Hick's Law Application

```
Decision time = a + b × log₂(n)
Where n = number of choices
```

**Practical limit**: 5-7 options before decision fatigue

### Miller's Law Application

```
Working memory ≈ 7 ± 2 chunks
```

**Practical limit**: Group information into 5-9 chunks max

---

## Flow Efficiency Metrics

### Key Metrics

| Metric | Calculation | Target |
|--------|-------------|--------|
| Task completion rate | Completions / Attempts | >90% |
| Time on task | Start to completion | Minimize |
| Click count | Interactions to goal | Minimize |
| Error rate | Errors / Tasks | <5% |
| Recovery rate | Recovered / Errors | >80% |
| Drop-off rate | Abandoned / Started | <10% |

### Step Analysis

For each step, measure:

```
Step X: [Action]
├── Entry rate: [X]% reach this step
├── Exit rate: [X]% complete this step  
├── Drop-off: [X]% abandon here
├── Time: [X] seconds average
├── Errors: [X]% make mistakes
└── Severity: Critical/Major/Minor
```

---

## Flow Patterns

### Optimal Patterns

| Pattern | Use Case | Benefits |
|---------|----------|----------|
| **Linear** | Simple tasks | Clear progress |
| **Wizard** | Complex multi-step | Guided, less overwhelming |
| **Hub & Spoke** | Multiple related tasks | Flexibility |
| **Progressive Disclosure** | Feature-rich | Reduces initial load |
| **Inline Editing** | Quick edits | Efficient |

### Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Forced registration | Early friction | Guest first |
| Buried CTA | Missed conversions | Above fold |
| Too many steps | Abandonment | Consolidate |
| Dead ends | Confusion | Always show next step |
| Loop backs | Frustration | Linear progress |
| Info repetition | Redundant effort | Pre-fill |

---

## Critical Path Analysis

### Identify Critical Paths

1. **Conversion paths**: Signup → Activation → Purchase
2. **Core tasks**: Primary user jobs
3. **Recovery paths**: Error → Resolution

### Critical Path Audit

```
Path: [Name]
Business Impact: [High/Medium/Low]
User Frequency: [Daily/Weekly/Monthly]

Steps Analysis:
| Step | Required? | Friction | Priority |
|------|-----------|----------|----------|
| 1    | Yes/No    | H/M/L    | P0-P3    |

Optimization Opportunities:
- [Step to remove/simplify]
- [Step to combine]
- [Friction to eliminate]
```

---

## Task Analysis Template

### For Each Core Task

```markdown
## Task: [Name]

### User Goal
[What user wants to accomplish]

### Current Flow
1. [Step] - [Time] - [Friction level]
2. [Step] - [Time] - [Friction level]
...

### Metrics
- Steps: [X]
- Time: [X] seconds
- Error rate: [X]%
- Drop-off: [X]%

### Friction Points
| Step | Issue | Severity | Fix |
|------|-------|----------|-----|

### Recommendations
1. [Highest impact improvement]
2. [Second priority]
3. [Third priority]

### Ideal Flow (Proposed)
1. [Optimized step]
2. [Optimized step]
...

Expected improvement: [X]% faster / [X]% higher completion
```

---

## Flow Audit Checklist

```
Entry Points
□ Clear value proposition
□ Immediate path to goal visible
□ Trust signals present
□ Loading under 3 seconds

Progress
□ Current step indicated
□ Total steps visible
□ Can go back without data loss
□ Progress saved automatically

Actions
□ Primary action clear
□ Secondary actions subordinate
□ Destructive actions safeguarded
□ Next step always visible

Completion
□ Success clearly indicated
□ Next steps offered
□ Easy to share/save result
□ Return path clear
```