# Heuristic Audit

Evaluate usability using Nielsen's 10 heuristics plus modern methodologies (Cognitive Walkthrough, OOUX, JTBD).

## Nielsen's 10 Usability Heuristics

### 1. Visibility of System Status

**Principle**: Keep users informed through appropriate, timely feedback.

| Check | Pass Criteria |
|-------|---------------|
| Loading states | Shown for operations >300ms |
| Progress indicators | Multi-step processes show progress |
| Success feedback | Actions confirm completion |
| Error feedback | Failures clearly communicated |
| Current location | Navigation shows active state |
| Real-time validation | Input feedback as user types |
| Sync status | Cloud/save state visible |

**Common Violations**: Silent failures, missing spinners, unclear selection state

**Severity**: 🔴 Critical when users don't know if action succeeded

---

### 2. Match Between System and Real World

**Principle**: Use familiar language, concepts, and conventions.

| Check | Pass Criteria |
|-------|---------------|
| Language | User-friendly, not developer jargon |
| Information order | Logical, not alphabetical |
| Iconography | Familiar, recognizable |
| Mental models | Matches user expectations |
| Metaphors | Users understand them |

**Common Violations**: Technical error codes, non-standard icons, unfamiliar terms

**Severity**: 🟠 Major when users can't understand interface

---

### 3. User Control and Freedom

**Principle**: Provide clear exits and undo capabilities.

| Check | Pass Criteria |
|-------|---------------|
| Undo/redo | Available for destructive actions |
| Cancel | Modals and forms have clear exit |
| Back navigation | Works as expected |
| Draft auto-save | Long forms preserve data |
| Confirmation | Before destructive actions |

**Common Violations**: No cancel button, irreversible actions, broken back button

**Severity**: 🔴 Critical when users trapped in unwanted states

---

### 4. Consistency and Standards

**Principle**: Follow platform conventions; maintain internal consistency.

| Check | Pass Criteria |
|-------|---------------|
| Terminology | Same words for same concepts |
| Component behavior | Same patterns throughout |
| Platform conventions | Follows OS/web standards |
| Visual consistency | Uniform spacing, typography |
| Interaction patterns | Predictable behaviors |

**Common Violations**: Multiple button styles, inconsistent terms, non-standard gestures

**Severity**: 🟠 Major when inconsistency causes confusion

---

### 5. Error Prevention

**Principle**: Design to prevent errors before they occur.

| Check | Pass Criteria |
|-------|---------------|
| Input constraints | Validation rules enforced |
| Smart defaults | Reasonable pre-selections |
| Confirmation dialogs | For risky actions |
| Disabled states | Invalid options grayed out |
| Format hints | Input examples shown |
| Auto-complete | Suggestions reduce errors |

**Common Violations**: Free-form where structured needed, no validation until submit

**Severity**: 🟠 Major when errors are frequent/costly

---

### 6. Recognition Rather Than Recall

**Principle**: Minimize memory load with visible options.

| Check | Pass Criteria |
|-------|---------------|
| Navigation visible | Options discoverable |
| Contextual help | Tooltips where needed |
| Recent items | Frequently used accessible |
| Search | With suggestions |
| Persistent info | Important data stays visible |

**Common Violations**: Hidden navigation, requiring memorization, info disappears

**Severity**: 🟠 Major when users must remember too much

---

### 7. Flexibility and Efficiency of Use

**Principle**: Cater to both novice and expert users.

| Check | Pass Criteria |
|-------|---------------|
| Keyboard shortcuts | Available for power users |
| Customization | Workflows adaptable |
| Bulk actions | Multiple items at once |
| Saved preferences | Settings remembered |
| Multiple paths | Different ways to same goal |

**Common Violations**: No keyboard nav, forced single workflow

**Severity**: 🟡 Minor unless power users are primary audience

---

### 8. Aesthetic and Minimalist Design

**Principle**: Remove unnecessary elements; prioritize essential information.

| Check | Pass Criteria |
|-------|---------------|
| Visual hierarchy | Clear, scannable |
| No redundancy | Each element serves purpose |
| Progressive disclosure | Complexity revealed gradually |
| Focused CTAs | Single primary action |
| Information density | Appropriate for context |

**Common Violations**: Cluttered UI, competing CTAs, decorative noise

**Severity**: 🟡 Minor unless severely impacting comprehension

---

### 9. Help Users Recognize, Diagnose, and Recover from Errors

**Principle**: Error messages should be clear, specific, and helpful.

| Check | Pass Criteria |
|-------|---------------|
| Plain language | No technical codes |
| Specific problem | Identifies exactly what's wrong |
| Resolution steps | Tells user how to fix |
| Input preserved | Form data not lost |
| Contextual placement | Error near relevant field |
| Non-alarming tone | Constructive, not scary |

**Error Message Pattern**: `[What happened] + [Why] + [How to fix]`

✅ Good: "Password must be at least 8 characters. Add 3 more characters."
❌ Bad: "Error 500", "Invalid input", "Validation failed"

**Severity**: 🟠 Major when users can't recover from errors

---

### 10. Help and Documentation

**Principle**: Provide accessible, task-focused help.

| Check | Pass Criteria |
|-------|---------------|
| Contextual tooltips | Where needed |
| Inline help | Complex fields explained |
| Searchable docs | If extensive help needed |
| Onboarding | For new users |
| Empty states | Guide users what to do |

**Common Violations**: No help, buried documentation, generic tooltips

**Severity**: 🟡 Minor for simple UIs, 🟠 Major for complex ones

---

## Heuristic Severity Matrix

| Heuristic | Typical Impact | Default Severity |
|-----------|----------------|------------------|
| System Status | High | 🔴 Critical |
| Real World Match | Medium | 🟠 Major |
| User Control | High | 🔴 Critical |
| Consistency | Medium | 🟠 Major |
| Error Prevention | High | 🟠 Major |
| Recognition | Medium | 🟠 Major |
| Flexibility | Low | 🟡 Minor |
| Minimalist Design | Medium | 🟡 Minor |
| Error Recovery | High | 🟠 Major |
| Help/Docs | Low | 🟡 Minor |

---

## Modern Methodologies

### Cognitive Walkthrough

For each task step, answer:

1. Will user try to achieve the right effect?
2. Will user notice the correct action is available?
3. Will user associate correct action with desired effect?
4. Will user see progress is being made?

**Use for**: Complex flows, onboarding, critical paths

### OOUX (Object-Oriented UX)

| Check | Criteria |
|-------|----------|
| Objects identified | Core nouns clear (User, Order, Product) |
| Consistent naming | Same object = same name everywhere |
| Object structure | Attributes and relationships clear |
| CTAs map to objects | Actions relate to visible objects |

**Use for**: Information architecture, navigation design

### JTBD (Jobs to Be Done)

Validate features against job stories:

```
When [situation], I want to [motivation], so I can [expected outcome].
```

| Check | Criteria |
|-------|----------|
| Job clarity | User's actual goal understood |
| Feature alignment | Features serve real jobs |
| Progress visibility | User sees job getting done |
| Outcome achievement | Job completable in UI |

**Use for**: Feature validation, prioritization

### Baymard Heuristics (E-commerce)

| Category | Key Checks |
|----------|------------|
| Product Page | Image zoom, specs visibility, reviews |
| Cart | Edit quantity, remove items, save for later |
| Checkout | Guest checkout, progress indicator, trust signals |
| Forms | Inline validation, smart defaults, auto-format |
| Search | Autocomplete, filters, no dead ends |

**Use for**: Shopping flows, conversion optimization

---

## Quick Heuristic Audit Template

```markdown
## Heuristic Audit: [Screen/Flow]

### Summary
- Total Issues: [X]
- Critical: [X] | Major: [X] | Minor: [X]

### Findings

| # | Heuristic | Issue | Severity | Effort |
|---|-----------|-------|----------|--------|
| 1 | [H#] | [Description] | 🔴/🟠/🟡 | L/M/H |

### Priority Recommendations
1. [Most impactful fix]
2. [Second priority]
3. [Third priority]
```