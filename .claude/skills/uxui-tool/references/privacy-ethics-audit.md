# Privacy & Ethics Audit

Evaluate dark patterns, consent mechanisms, data practices, and regulatory compliance (GDPR, DSA, CCPA).

## Dark Pattern Detection

### Deceptive Patterns Checklist

| Pattern | Description | Severity |
|---------|-------------|----------|
| **Confirm-shaming** | Guilt-trip to decline | 🔴 Critical |
| **Hidden costs** | Fees revealed late | 🔴 Critical |
| **Forced continuity** | Hard to cancel | 🔴 Critical |
| **Roach motel** | Easy in, hard out | 🔴 Critical |
| **Bait & switch** | Promised ≠ delivered | 🔴 Critical |
| **Misdirection** | Attention diverted | 🟠 Major |
| **Trick questions** | Confusing wording | 🟠 Major |
| **Sneak into basket** | Items auto-added | 🟠 Major |
| **Privacy zuckering** | Oversharing default | 🟠 Major |
| **Friend spam** | Unwanted invites | 🟠 Major |
| **Disguised ads** | Ads look like content | 🟠 Major |
| **Nagging** | Persistent interruptions | 🟡 Minor |
| **Obstruction** | Complex cancellation | 🟠 Major |

### Confirm-Shaming Examples

❌ **Dark Pattern**:
```
"Yes, I want to save money"
"No, I prefer to pay full price like a fool"
```

✅ **Ethical Alternative**:
```
"Yes, sign me up"
"No thanks"
```

### Dark Pattern Audit

```
□ No guilt-tripping language in declines
□ Full costs visible before checkout
□ Subscription terms clear upfront
□ Cancellation as easy as signup
□ Pre-selected options benefit user
□ No confusing double negatives
□ Ads clearly labeled
□ No unwanted items in cart
□ No hidden auto-renewals
□ Unsubscribe process simple
```

---

## Consent Mechanisms

### Consent Requirements (GDPR)

| Requirement | Implementation |
|-------------|----------------|
| Freely given | No forced bundling |
| Specific | Per-purpose consent |
| Informed | Clear explanation |
| Unambiguous | Affirmative action |
| Withdrawable | Easy to revoke |

### Cookie Consent Checklist

```
□ Banner appears on first visit
□ Reject option equally prominent as accept
□ No pre-checked boxes
□ Granular choices available
□ Essential cookies explained
□ Easy to change preferences later
□ No cookie walls (GDPR)
□ Consent recorded
□ Consent refreshed periodically
```

### Cookie Banner Patterns

❌ **Dark Pattern**:
```
[Accept All]                    [Manage]
                        (tiny, gray text)
```

✅ **Ethical Pattern**:
```
[Accept All]    [Reject All]    [Customize]
   (equal prominence for all options)
```

### Newsletter/Marketing Consent

```
□ Opt-in (not opt-out)
□ Clear description of content
□ Frequency disclosed
□ Easy unsubscribe in every email
□ No dark patterns in consent
□ Double opt-in for GDPR regions
```

---

## Data Collection Practices

### Data Minimization

| Principle | Check |
|-----------|-------|
| Collect only what's needed | Audit each field |
| Delete when no longer needed | Retention policy |
| Anonymize when possible | PII assessment |

### Form Data Audit

```
□ Each field has clear purpose
□ Optional vs required clearly marked
□ Sensitive data justified
□ No unnecessary data collection
□ Data usage explained
□ Third-party sharing disclosed
```

### Sensitive Data Handling

| Data Type | Requirements |
|-----------|--------------|
| Financial | PCI compliance, encryption |
| Health | HIPAA (US), special consent |
| Biometric | Explicit consent, secure storage |
| Location | Purpose limitation, opt-in |
| Children | COPPA compliance, parental consent |

---

## Privacy Controls

### User Rights (GDPR)

| Right | Implementation |
|-------|----------------|
| Access | Data export/download |
| Rectification | Edit personal data |
| Erasure | Delete account/data |
| Portability | Machine-readable export |
| Object | Opt-out of processing |
| Restrict | Limit processing |

### Privacy Controls Checklist

```
□ Privacy settings accessible
□ Data download available
□ Account deletion possible
□ Marketing opt-out easy
□ Third-party sharing controls
□ Data retention info available
□ Privacy policy readable
□ Contact for privacy questions
```

### Privacy Settings UI

```
✅ Good Pattern:
┌─────────────────────────────────┐
│ Privacy Settings                │
├─────────────────────────────────┤
│ Marketing emails        [OFF]   │
│ Personalized ads        [OFF]   │
│ Data sharing            [OFF]   │
│ Analytics               [ON]    │
├─────────────────────────────────┤
│ [Download my data]              │
│ [Delete my account]             │
└─────────────────────────────────┘
```

---

## Regulatory Compliance

### GDPR (EU) Checklist

```
□ Lawful basis for processing
□ Privacy notice provided
□ Consent properly obtained
□ Data subject rights implemented
□ Data breach procedures
□ DPO appointed (if required)
□ Records of processing
□ Cross-border transfer compliance
```

### CCPA (California) Checklist

```
□ "Do Not Sell My Info" link
□ Privacy policy with CCPA disclosures
□ Opt-out mechanism
□ Data deletion requests honored
□ Financial incentive disclosures
□ No discrimination for opt-out
```

### DSA (EU Digital Services Act) Checklist

```
□ Transparent advertising
□ No targeting minors with ads
□ Recommender system transparency
□ No dark patterns
□ Content moderation transparency
□ User complaint mechanism
```

### Accessibility of Legal Docs

```
□ Privacy policy readable (grade 8 level)
□ Terms of service summarized
□ Key points highlighted
□ Available in user's language
□ Version history accessible
□ Easy to find from any page
```

---

## Ethical Design Principles

### Ethical Checklist

```
Respect
□ User autonomy respected
□ No manipulation tactics
□ Honest communication
□ Dignity preserved

Transparency
□ Data practices disclosed
□ AI use disclosed
□ Business model clear
□ No hidden agendas

Fairness
□ No discriminatory outcomes
□ Accessible to all users
□ Fair pricing practices
□ Equal service quality

Safety
□ User safety prioritized
□ Harmful content prevented
□ Secure data handling
□ Mental health considered
```

### Inclusive Design Check

```
□ Content appropriate for all ages
□ No exclusionary language
□ Cultural sensitivity
□ Economic accessibility
□ Technical accessibility
□ Cognitive accessibility
```

---

## Attention Ethics

### Attention Checklist

```
□ No infinite scroll without pause
□ No autoplay video with sound
□ Notification defaults reasonable
□ No artificial urgency
□ No FOMO manipulation
□ Usage insights available
□ Break reminders (if relevant)
□ Easy to pause/snooze
```

### Notification Ethics

| Pattern | Status |
|---------|--------|
| Default to minimal notifications | ✅/❌ |
| Granular notification controls | ✅/❌ |
| No notification guilt ("You missed...") | ✅/❌ |
| Batch vs individual choice | ✅/❌ |
| Quiet hours respected | ✅/❌ |

---

## Children's Safety

### COPPA Compliance (Under 13)

```
□ Age gate implemented
□ Verifiable parental consent
□ Limited data collection
□ No behavioral advertising
□ Safe content only
□ No in-app purchases without consent
□ Privacy policy for children
```

### Teen Safety

```
□ Default to private profiles
□ Limited public sharing
□ No location sharing by default
□ Restricted DMs from strangers
□ Content moderation active
□ Reporting mechanism clear
```

---

## Privacy & Ethics Audit Template

```markdown
## Privacy & Ethics Audit: [Product/Feature]

### Dark Patterns

| Pattern | Found | Location | Severity |
|---------|-------|----------|----------|
| Confirm-shaming | ✅/❌ | | 🔴 |
| Hidden costs | ✅/❌ | | 🔴 |
| Forced continuity | ✅/❌ | | 🔴 |
| Misdirection | ✅/❌ | | 🟠 |
| Pre-selected options | ✅/❌ | | 🟠 |

### Consent Mechanisms

| Mechanism | Compliant | Notes |
|-----------|-----------|-------|
| Cookie consent | ✅/❌ | |
| Marketing consent | ✅/❌ | |
| Data sharing consent | ✅/❌ | |

### Privacy Controls

| Control | Available | Discoverable |
|---------|-----------|--------------|
| Data export | ✅/❌ | ✅/❌ |
| Account deletion | ✅/❌ | ✅/❌ |
| Marketing opt-out | ✅/❌ | ✅/❌ |

### Regulatory Compliance

| Regulation | Status | Gaps |
|------------|--------|------|
| GDPR | ✅/⚠️/❌ | |
| CCPA | ✅/⚠️/❌ | |
| DSA | ✅/⚠️/❌ | |

### Issues Found

| Issue | Category | Severity | Recommendation |
|-------|----------|----------|----------------|
| [Description] | [Dark pattern/Consent/Privacy] | 🔴/🟠/🟡 | [Fix] |

### Priority Actions
1. [Critical fixes]
2. [Major improvements]
3. [Minor enhancements]
```