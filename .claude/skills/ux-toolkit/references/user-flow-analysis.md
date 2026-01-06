# User Flow & Friction Analysis

Map and evaluate critical user journeys.

## Flow Mapping Process

### 1. Identify Critical Paths

| Flow Type | Examples | Priority |
|-----------|----------|----------|
| Primary conversion | Signup, purchase, booking | 🔴 High |
| Core tasks | Create, edit, delete content | 🔴 High |
| Secondary flows | Settings, profile, preferences | 🟠 Medium |
| Support flows | Help, contact, error recovery | 🟡 Low |

### 2. Document Flow Steps

```
[Entry Point] → [Step 1] → [Step 2] → [Decision] → [Outcome]
                                          ↓
                                    [Alt Path]
```

### 3. Metrics Per Step

| Metric | Measurement | Tool |
|--------|-------------|------|
| Time on step | Seconds | Analytics |
| Drop-off rate | % abandonment | Analytics |
| Error rate | % validation fails | Logs |
| Clicks/taps | Count per step | Tracking |
| Backtrack rate | % going back | Analytics |

---

## Click/Tap Count Optimization

### Target Metrics

| Task Type | Target Clicks | Max Acceptable |
|-----------|---------------|----------------|
| Primary action | 1-2 | 3 |
| Common task | 2-3 | 5 |
| Complex flow | 3-5 | 7 |
| Settings/config | 2-4 | 6 |

### Reduction Strategies

| Issue | Solution |
|-------|----------|
| Too many steps | Combine screens, remove unnecessary steps |
| Buried actions | Surface to higher level nav |
| Repeated inputs | Remember, autofill, defaults |
| Confirmation overload | Reduce redundant confirms |
| Hidden features | Add shortcuts, quick actions |

### Click Audit Template

```markdown
## Flow: [Name]

| Step | Action | Clicks | Optimal | Gap |
|------|--------|--------|---------|-----|
| 1 | [action] | X | Y | +/- Z |
| 2 | [action] | X | Y | +/- Z |

**Total:** X clicks (Target: Y)
**Optimization potential:** Z clicks saved
```

---

## Cognitive Load Assessment

### Load Types

| Type | Description | Mitigation |
|------|-------------|------------|
| Intrinsic | Task complexity | Simplify task, break into steps |
| Extraneous | Poor design | Remove distractions, clarify UI |
| Germane | Learning effort | Patterns, progressive disclosure |

### High Load Indicators

| Signal | Description | Severity |
|--------|-------------|----------|
| Too many options | >7 items in list/menu | 🟠 Major |
| Dense text | Walls of content | 🟠 Major |
| Complex forms | >7 fields visible | 🟠 Major |
| Unclear hierarchy | Equal visual weight | 🟡 Minor |
| Jargon | Technical/unfamiliar terms | 🟠 Major |
| Missing context | Why is this needed? | 🟠 Major |

### Reduction Techniques

```
Progressive Disclosure  → Show details on demand
Chunking               → Group related items (max 7±2)
Smart Defaults         → Pre-fill common choices
Visual Hierarchy       → Guide eye to primary action
Contextual Help        → Tooltips, inline hints
Familiar Patterns      → Use conventions
```

---

## Form Friction Analysis

### Field-Level Checks

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Field count | Only essential fields | 🟠 Major |
| Label clarity | Purpose immediately clear | 🟠 Major |
| Placeholder text | Example, not label | 🟡 Minor |
| Input type | Correct keyboard on mobile | 🟠 Major |
| Autofill support | `autocomplete` attrs | 🟡 Minor |
| Validation timing | On blur, not on type | 🟡 Minor |
| Error messages | Specific, actionable | 🔴 Critical |

### Form-Level Checks

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Logical grouping | Related fields together | 🟡 Minor |
| Progress indicator | For multi-step | 🟠 Major |
| Save progress | Long forms auto-save | 🟠 Major |
| Mobile layout | Single column, large targets | 🟠 Major |
| Submit feedback | Clear success/failure | 🔴 Critical |
| Recovery | Errors don't clear data | 🔴 Critical |

### Friction Points Checklist

```
□ Unnecessary fields (nice-to-have vs need)
□ Repeated information entry
□ Format requirements not explained
□ Weak password rules (too strict/unclear)
□ CAPTCHA friction
□ Hidden required fields
□ Unclear validation errors
□ No inline validation
□ Submit fails without explanation
□ Data lost on error
```

---

## Error State Handling

### Error Types & Responses

| Error Type | User Sees | System Does |
|------------|-----------|-------------|
| Validation | Inline error, field highlight | Focus error field |
| Network | Toast/banner + retry | Auto-retry, queue |
| Server | Error page + actions | Log, alert on-call |
| Auth | Redirect to login | Preserve intended action |
| Permission | Explanation + upgrade path | Log attempt |

### Error UX Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Clear message | Plain language explanation | 🔴 Critical |
| Solution provided | What to do next | 🔴 Critical |
| Data preserved | Input not lost | 🔴 Critical |
| Retry available | Easy to try again | 🟠 Major |
| Support path | Help accessible | 🟡 Minor |
| Error logged | For debugging | 🟡 Minor |

---

## Loading States & Feedback

### Response Time Thresholds

| Duration | User Perception | Required Feedback |
|----------|-----------------|-------------------|
| <100ms | Instant | None |
| 100-300ms | Slight delay | Optional indicator |
| 300ms-1s | Noticeable | Spinner/progress |
| 1-5s | Wait | Progress bar + message |
| >5s | Long wait | Progress + cancel option |

### Loading State Checklist

| State | Implementation | Severity |
|-------|----------------|----------|
| Button loading | Disabled + spinner | 🟠 Major |
| Page loading | Skeleton screens | 🟡 Minor |
| Data fetching | Inline loader + placeholder | 🟠 Major |
| File upload | Progress bar + % | 🟠 Major |
| Background task | Toast notification | 🟡 Minor |

---

## Drop-off Point Identification

### Common Drop-off Causes

| Location | Likely Cause | Investigation |
|----------|--------------|---------------|
| Before form | Too complex/scary | Simplify intro |
| Mid-form | Too long/confusing | Break into steps |
| At submit | Fear of commitment | Reassure (cancel, refund) |
| At payment | Trust/cost concern | Trust signals, transparency |
| After error | Frustration | Better error handling |

### Analysis Method

```
1. Pull funnel analytics
2. Identify step w/ highest drop
3. Session recordings at drop point
4. User testing on that step
5. Hypothesis → test → iterate
```

---

## Edge Case Scenarios

### Required Edge Case Testing

| Scenario | What to Test |
|----------|--------------|
| Empty states | No data, first-time user |
| Error states | Network, validation, server |
| Loading states | Slow connection, large data |
| Timeout states | Session, request timeout |
| Boundary values | Max length, zero, negative |
| Permission states | Denied, partial access |
| Offline state | No connectivity |

### Empty State Checklist

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Helpful message | Explains why empty | 🟠 Major |
| Action provided | CTA to add first item | 🟠 Major |
| Visual interest | Not blank white | 🟡 Minor |
| Guidance | What to do next | 🟠 Major |

### Timeout Handling

| Type | Max Duration | User Feedback |
|------|--------------|---------------|
| API request | 30s | Show error, retry option |
| Session | 30min | Warning at 25min, extend |
| Upload | Progress-based | Cancel option, resume |
| Search | 10s | Partial results, refine |

---

## Flow Audit Report Template

```markdown
# User Flow Analysis Report

**Flow:** [Name]
**Date:** [Date]
**Analyst:** [Name]

## Flow Overview

[Entry] → [Step 1] → [Step 2] → [Outcome]

## Metrics

| Step | Users | Drop-off | Avg Time | Clicks |
|------|-------|----------|----------|--------|
| Entry | 100% | X% | Xs | X |
| Step 1 | X% | X% | Xs | X |

## Friction Points Identified

| Location | Issue | Severity | Recommendation |
|----------|-------|----------|----------------|
| [step] | [desc] | 🔴/🟠/🟡 | [fix] |

## Edge Cases Tested

| Scenario | Result | Issue |
|----------|--------|-------|
| Empty state | ✅/❌ | [if failed] |
| Error state | ✅/❌ | [if failed] |

## Recommendations

1. [Priority fix]
2. [Enhancement]
```
