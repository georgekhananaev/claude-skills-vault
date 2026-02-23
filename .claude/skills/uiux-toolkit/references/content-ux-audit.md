# Content UX Audit

Evaluate UX writing, readability, voice & tone, and content clarity.

## UX Writing Principles

### Core Principles

| Principle | Description | Check |
|-----------|-------------|-------|
| **Clear** | Easy to understand | No jargon, simple words |
| **Concise** | No unnecessary words | Short sentences |
| **Useful** | Helps user complete task | Actionable info |
| **Consistent** | Same terms throughout | Terminology audit |
| **Human** | Conversational tone | Not robotic |

### Word Choice Guidelines

| Instead of | Use |
|------------|-----|
| Terminate | End, Stop |
| Initialize | Start, Begin |
| Configure | Set up |
| Modify | Change, Edit |
| Utilize | Use |
| Subsequently | Then |
| Additionally | Also |
| In order to | To |
| Due to the fact that | Because |
| At this point in time | Now |

---

## Readability Assessment

### Readability Scores

| Score | Grade Level | Audience |
|-------|-------------|----------|
| Flesch-Kincaid | 6-8 | General public |
| Flesch-Kincaid | 8-10 | Professional |
| Flesch-Kincaid | 10-12 | Technical |

### Readability Targets

| Content Type | Target Grade | Flesch Score |
|--------------|--------------|--------------|
| Marketing | 6-8 | 60-70 |
| Help docs | 7-9 | 50-60 |
| Error messages | 6-8 | 60-70 |
| Technical docs | 10-12 | 30-50 |

### Readability Checklist

```
□ Average sentence length < 20 words
□ Average paragraph < 5 sentences
□ Common words preferred
□ Active voice dominant (>70%)
□ One idea per sentence
□ No walls of text
□ Scannable structure
```

---

## Scannability

### Scannable Content Elements

| Element | Purpose | Check |
|---------|---------|-------|
| Headings | Structure, navigation | Clear hierarchy |
| Bullet points | List information | Not overused |
| Bold text | Emphasis key info | Sparingly used |
| Short paragraphs | Readability | 2-4 sentences |
| White space | Visual breathing room | Adequate spacing |

### F-Pattern Optimization

```
Content placement priority:
1. Headline (top left)
2. Subheadline/intro
3. Section headers (left-aligned)
4. First words of paragraphs
5. CTAs and key actions
```

### Scannable Checklist

```
□ Key info in first 2 words of headings
□ Front-loaded paragraphs
□ Important info above the fold
□ CTAs clearly visible
□ No buried critical information
□ Lists used appropriately (not default)
```

---

## Microcopy Evaluation

### Button Copy

| Pattern | Example | Avoid |
|---------|---------|-------|
| Action + Object | "Save changes" | "Submit" |
| Clear outcome | "Create account" | "Go" |
| First person | "Start my trial" | "Start trial" |

### Button Copy Checklist

```
□ Starts with action verb
□ Specific about outcome
□ 2-4 words preferred
□ No generic "Submit" or "Click here"
□ Consistent casing (Sentence vs Title)
```

### Form Labels

| Type | Good | Bad |
|------|------|-----|
| Clear | "Email address" | "Email" |
| Helpful | "Password (min 8 characters)" | "Password" |
| Specific | "Phone number (optional)" | "Phone" |

### Form Copy Checklist

```
□ Labels are nouns, not verbs
□ Placeholder ≠ label
□ Helper text explains requirements
□ Required fields indicated
□ Optional fields marked (or vice versa)
□ Input format examples provided
```

### Error Messages

| Component | Content |
|-----------|---------|
| What happened | "That password is too short" |
| How to fix | "Use at least 8 characters" |

### Error Message Checklist

```
□ Explains the specific problem
□ Tells user how to fix it
□ Uses positive framing when possible
□ No blame ("You entered wrong...")
□ No technical jargon
□ Placed near the error source
```

### Empty States

| Component | Content |
|-----------|---------|
| What this area is | "Your cart" |
| Why it's empty | "You haven't added any items yet" |
| What to do | "Browse products" [CTA] |

---

## Voice & Tone

### Voice Attributes

Define 3-5 attributes:

| Attribute | Description | Example |
|-----------|-------------|---------|
| Friendly | Warm, approachable | "Hey there!" vs "Greetings" |
| Professional | Competent, trustworthy | "We'll help" vs "We got u" |
| Clear | Direct, no ambiguity | "Click Save" vs "You may want to..." |
| Helpful | Supportive, guiding | "Try this:" vs "Error occurred" |

### Tone Variation

| Context | Tone Shift |
|---------|------------|
| Success | Celebratory, encouraging |
| Error | Calm, supportive |
| Warning | Clear, urgent but not alarming |
| Onboarding | Welcoming, guiding |
| Help docs | Instructive, patient |

### Voice Consistency Checklist

```
□ Voice attributes documented
□ Tone variations for contexts defined
□ Examples for each scenario
□ Consistent across all touchpoints
□ Avoids jargon
□ Matches brand personality
```

---

## Content Patterns

### Confirmation Messages

```
Pattern: [Action] + [Object] + [What's next]
Example: "Message sent. You'll hear back within 24 hours."
```

### Progress Messaging

```
Pattern: [Current step] of [Total] + [What you're doing]
Example: "Step 2 of 4: Add your payment details"
```

### Instructional Text

```
Pattern: [Action verb] + [Specific object] + [Expected outcome]
Example: "Upload your photo to personalize your profile"
```

---

## Content Audit Checklist

### Global Content

```
□ Navigation labels clear and consistent
□ Page titles descriptive
□ CTAs action-oriented
□ Footer links properly labeled
□ Legal text accessible
```

### Forms

```
□ Labels clear and consistent
□ Helper text where needed
□ Error messages helpful
□ Success messages confirming
□ Required/optional indicated
```

### Notifications

```
□ Toast messages concise
□ Alert copy actionable
□ Email subjects scannable
□ Push notifications valuable
```

---

## Content Audit Template

```markdown
## Content Audit: [Page/Feature]

### Readability Scores

| Metric | Score | Target |
|--------|-------|--------|
| Flesch-Kincaid | X | 6-8 |
| Avg sentence length | X words | <20 |
| Active voice | X% | >70% |

### Microcopy Review

| Element | Current | Recommendation |
|---------|---------|----------------|
| H1 | "[Copy]" | [Suggested] |
| CTA | "[Copy]" | [Suggested] |
| Error | "[Copy]" | [Suggested] |

### Voice & Tone

| Attribute | Adherence | Notes |
|-----------|-----------|-------|
| [Attr 1] | ✅/⚠️/❌ | |
| [Attr 2] | ✅/⚠️/❌ | |

### Issues Found

| Issue | Severity | Location | Recommendation |
|-------|----------|----------|----------------|
| [Description] | 🔴/🟠/🟡 | [Where] | [Fix] |
```