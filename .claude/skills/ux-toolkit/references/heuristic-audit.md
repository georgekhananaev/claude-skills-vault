# UX Heuristic Audit

Systematic evaluation using Nielsen's 10 Usability Heuristics.

## Nielsen's 10 Heuristics Checklist

### H1: Visibility of System Status

System keeps users informed through timely feedback.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Loading indicators | Progress shown for actions >1s | 🟠 Major |
| Form submission feedback | Success/error msg displayed | 🔴 Critical |
| Upload progress | % or time remaining shown | 🟠 Major |
| Navigation state | Current location highlighted | 🟡 Minor |
| Save status | Auto-save indicator present | 🟡 Minor |
| Processing state | Disabled state + spinner during ops | 🟠 Major |

**Questions:**
- Does user know what's happening at all times?
- Is feedback immediate (<100ms) or delayed w/ indicator?
- Are async operations clearly communicated?

---

### H2: Match Between System & Real World

System speaks user's language w/ familiar concepts.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Terminology | Uses domain-appropriate language | 🟠 Major |
| Icons | Universally recognized symbols | 🟡 Minor |
| Metaphors | Real-world analogs (folder, trash) | 🟡 Minor |
| Date/time formats | Locale-appropriate display | 🟡 Minor |
| Currency/numbers | Correct symbols & separators | 🟠 Major |
| Error messages | Plain language, not codes | 🔴 Critical |

**Questions:**
- Would a non-technical user understand all labels?
- Are industry-standard terms used correctly?
- Do icons match mental models?

---

### H3: User Control & Freedom

Users can undo, redo, and escape from states.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Undo action | Available for destructive ops | 🔴 Critical |
| Cancel operation | Exit modals/flows easily | 🟠 Major |
| Back navigation | Works as expected | 🟠 Major |
| Clear/reset forms | Single action to clear | 🟡 Minor |
| Escape key support | Closes modals/overlays | 🟡 Minor |
| Edit after submit | Modify submitted data | 🟠 Major |

**Questions:**
- Can user recover from mistakes w/o data loss?
- Is there always a clear exit?
- Can user change their mind?

---

### H4: Consistency & Standards

Follow platform conventions & internal patterns.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Button styles | Primary/secondary consistent | 🟡 Minor |
| Link behavior | Standard colors & underlines | 🟡 Minor |
| Form patterns | Same layout across app | 🟠 Major |
| Terminology | Same words for same concepts | 🟠 Major |
| Icon usage | Same icons = same actions | 🟠 Major |
| Navigation | Consistent placement & behavior | 🟠 Major |

**Questions:**
- Does similar content look similar?
- Are platform conventions followed?
- Is internal consistency maintained?

---

### H5: Error Prevention

Prevent problems before they occur.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Confirmation dialogs | Present for destructive actions | 🔴 Critical |
| Input validation | Real-time format checking | 🟠 Major |
| Disabled states | Unavailable options greyed out | 🟡 Minor |
| Autosave | Prevent data loss | 🟠 Major |
| Smart defaults | Sensible pre-filled values | 🟡 Minor |
| Constraint feedback | Show limits before hitting | 🟡 Minor |

**Questions:**
- Are slips prevented via constraints?
- Are dangerous actions safeguarded?
- Does system guide toward valid input?

---

### H6: Recognition vs Recall

Minimize memory load w/ visible options & cues.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Visible navigation | All options accessible | 🟠 Major |
| Recent items | Quick access to history | 🟡 Minor |
| Autocomplete | Suggestions for inputs | 🟡 Minor |
| Contextual help | Info where needed | 🟡 Minor |
| Breadcrumbs | Path visible in hierarchy | 🟡 Minor |
| Labels on icons | Text accompanies icons | 🟡 Minor |

**Questions:**
- Can user operate w/o memorizing?
- Are instructions visible when needed?
- Does UI prompt next actions?

---

### H7: Flexibility & Efficiency

Support both novice & expert users.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Keyboard shortcuts | Power user accelerators | 🟡 Minor |
| Customization | User preferences supported | 🟡 Minor |
| Batch operations | Multi-select + bulk actions | 🟡 Minor |
| Search/filter | Quick data access | 🟠 Major |
| Defaults | Skip steps for common paths | 🟡 Minor |
| Templates | Pre-built starting points | ⚪ Cosmetic |

**Questions:**
- Can experts work faster?
- Are common tasks streamlined?
- Is personalization available?

---

### H8: Aesthetic & Minimalist Design

Show only relevant information.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Visual hierarchy | Important elements prominent | 🟠 Major |
| Content density | Appropriate whitespace | 🟡 Minor |
| Progressive disclosure | Details on demand | 🟡 Minor |
| Noise reduction | No decorative clutter | ⚪ Cosmetic |
| Focused CTAs | Clear primary actions | 🟠 Major |
| Consistent styling | Unified visual language | 🟡 Minor |

**Questions:**
- Is every element necessary?
- Can user focus on primary task?
- Is content scannable?

---

### H9: Error Recovery

Help users recognize, diagnose & recover from errors.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Clear error message | Explains what went wrong | 🔴 Critical |
| Solution provided | Tells how to fix | 🔴 Critical |
| Non-destructive | Preserves user input | 🔴 Critical |
| Error location | Highlights problem field | 🟠 Major |
| Retry option | Easy to try again | 🟠 Major |
| Support path | Contact/help available | 🟡 Minor |

**Questions:**
- Does user understand what failed?
- Is recovery path clear?
- Is data preserved after error?

---

### H10: Help & Documentation

Provide accessible help when needed.

| Check | Pass Criteria | Severity |
|-------|---------------|----------|
| Contextual help | Tooltips, inline hints | 🟡 Minor |
| Search docs | Searchable help content | 🟡 Minor |
| FAQ available | Common questions answered | ⚪ Cosmetic |
| Onboarding | New user guidance | 🟡 Minor |
| Task-focused | Steps for specific goals | 🟡 Minor |
| Accessible | Help reachable from any screen | 🟡 Minor |

**Questions:**
- Is help findable when needed?
- Are instructions task-oriented?
- Can user self-serve?

---

## Audit Report Template

```markdown
# Heuristic Audit Report

**Product:** [Name]
**Version:** [Version]
**Date:** [Date]
**Auditor:** [Name]

## Executive Summary

- Total issues: X
- 🔴 Critical: X
- 🟠 Major: X
- 🟡 Minor: X
- ⚪ Cosmetic: X

## Findings by Heuristic

### H1: Visibility of System Status
| Issue | Location | Severity | Recommendation |
|-------|----------|----------|----------------|
| [desc] | [screen/component] | 🔴/🟠/🟡/⚪ | [fix] |

[Repeat for H2-H10]

## Priority Actions

1. [Critical fix 1]
2. [Critical fix 2]
3. [Major fix 1]
```

---

## Severity Classification

| Level | Definition | Example |
|-------|------------|---------|
| 🔴 Critical | Prevents task completion | No error msg on failed payment |
| 🟠 Major | Causes significant delay/confusion | No loading indicator on slow op |
| 🟡 Minor | Causes minor friction | Inconsistent button styling |
| ⚪ Cosmetic | Polish/preference issue | Suboptimal whitespace |

## Remediation Priority

```
1. Critical → Fix before release
2. Major    → Fix in current sprint
3. Minor    → Next sprint backlog
4. Cosmetic → Nice-to-have backlog
```
