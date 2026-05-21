---
name: find-name
description: Generate short brand-name candidates, score each (length, memorability, brandability, cross-language safety, spelling clarity), check domain availability across multiple TLDs, and emit a ranked CSV containing ONLY names whose domains are actually available. Iterates generation until enough names pass the availability filter.
tools:
  - AskUserQuestion
  - Bash(python3 *)
  - Bash(node *)
  - Bash(mkdir *)
  - Read
  - Write
  - Edit
---

# Find Name Command

**Trigger: `/find-name` only.** Generate, score, availability-check, filter, and rank short brand names.

**Announce:** "I'm using the find-name command to generate and rank brand-name candidates."

**Core promise:** every name that appears in the output has its required TLD(s) genuinely available — no `taken`, no `aftermarket`, no `premium` slip-throughs.

## 0. Skills Used (verify they exist)

| Skill | Path | Purpose |
|-------|------|---------|
| `domain-checker` | `.claude/skills/domain-checker/scripts/check_domains.py` | Bulk availability + aftermarket/premium detection |
| `data-wrangler` | `.claude/skills/data-wrangler/scripts/data_wrangler.py` | Sort/filter the ranked CSV |

If either path is missing, STOP and report which skill needs installing.

## 1. Discovery (single AskUserQuestion batch — 5 Qs)

| Q# | Question | Header | Options |
|----|----------|--------|---------|
| 1 | What industry / what does the company do? | Industry | SaaS/tech · Consumer · B2B services · Healthcare · Finance · _Other_ |
| 2 | What vibe should the name carry? | Vibe | Modern/minimal · Bold/distinctive · Playful · Trusted/classic |
| 3 | Max characters per name (excluding TLD)? | Length | ≤6 · ≤7 · ≤8 · ≤10 |
| 4 | What MUST be available? (strictest filter) | Required | .com required · .com preferred (.ai/.io OK) · Any of .com/.ai/.io/.app/.dev · Modern only (.ai or .io) |
| 5 | Which domains should qualify? | Domain mode | Only ready-for-registration (recommended) · Include registry-premium (high registrar price) · Include aftermarket/marketplace (GoDaddy sale, Sedo, Dan) · Include both premium and aftermarket |

Note user free-text: must-include words, target geos, brands to differentiate from, max budget for premium/aftermarket if relevant.

**Important:** if the user picked `≤6` AND `.com required`, warn upfront — the .com namespace is saturated for short pronounceable names. Offer to bump to `≤8` automatically (recommended) or proceed strict.

**Q5 semantics — what each option means:**
- **Only ready-for-registration:** strictest. Domain must be unregistered and priced at the standard registrar rate. No registry-premium tier, no marketplace listings.
- **Include registry-premium:** allow domains the registry flags as premium (often $100–$10,000+/yr at the registrar). Still "available" — you just pay more on year one (and sometimes recurring).
- **Include aftermarket/marketplace:** allow domains currently registered but listed for sale on GoDaddy Auctions, Sedo, Afternic, Dan, etc. These are one-time purchases at the asking price.
- **Include both:** widest net. Use when brand fit matters more than cost and the user has budget.

## 2. The Availability Filter (the heart of this command)

Map Q4 + Q5 → filter predicate. A name **passes** the filter only if at least one TLD in the Q4-required set has a status that Q5 accepts.

### Step 2a — what statuses count as "qualifying" per Q5

| Q5 answer | Qualifying statuses |
|-----------|---------------------|
| Only ready-for-registration | `available` AND evidence does NOT contain `"premium tier"` |
| Include registry-premium | `available` (premium allowed; flag in `concerns`) |
| Include aftermarket/marketplace | `available` (no premium) OR `aftermarket` (flag in `concerns`) |
| Include both premium and aftermarket | `available` (premium allowed) OR `aftermarket` (both flagged in `concerns`) |

### Step 2b — apply the Q4 TLD predicate using qualifying statuses

| Q4 answer | Pass condition |
|-----------|----------------|
| `.com required` | `.com` is qualifying |
| `.com preferred (.ai/.io OK)` | `.com` is qualifying OR `.ai` is qualifying OR `.io` is qualifying |
| `Any of .com/.ai/.io/.app/.dev` | ≥1 of those TLDs is qualifying |
| `Modern only (.ai or .io)` | `.ai` is qualifying OR `.io` is qualifying |

**These NEVER count as qualifying, regardless of Q5:**
- `taken` (registered, not for sale)
- `expiring` (still registered — speculative; only ever surfaced as a bonus note, never as the pass reason)
- `unknown` (couldn't determine — skip and note)

**Premium / aftermarket — always flagged:**
Even when Q5 permits them, every premium or aftermarket TLD that contributes to a pass MUST be flagged in the `concerns` column and shown distinctly in the console table (`! premium`, `$ aftermkt`). The user must never be surprised by a price.

## 3. Iterative Generation Loop

**Goal:** accumulate ≥10 candidates that pass the availability filter.
**Budget:** up to 6 batches × ~12 names = ~72 candidates. Stop early when goal met.

```
accumulator = []     # passing candidates
batch_num = 0
MAX_BATCHES = 6
TARGET = 10

while len(accumulator) < TARGET and batch_num < MAX_BATCHES:
    batch_num += 1
    candidates = generate_batch(n=12, avoid=accumulator+all_previous_attempts)
    candidates = pre_filter(candidates)  # length / brand-collision / pronounceable
    results = domain_check(candidates, tld_set)  # one parallel call
    passing = [c for c in results if passes_availability_filter(c)]
    accumulator.extend(passing)
```

### Per-batch generation techniques (rotate / combine)

| Technique | Example | Best for |
|-----------|---------|----------|
| **Coined / brandable** | Vexyl, Noxly, Quivo | Modern/minimal |
| **Vowel-drop real words** | Lyft, Tumblr, Flickr | Playful |
| **Latin/Greek roots** | Lumen, Vexel, Quora | Trusted/classic |
| **Short compounds (≤max)** | Wavkit, Joopli, Pinepay | When .com required |
| **Rare-letter pivots** | Quix, Zorlo, Klemo | When .com required (Q/X/Z/K) |
| **Suffix patterns** | -hq, -ly, -fy, -ix, -ora | When .com required |
| **Two-word merged** | Brightpost, Quickship | Length 8-10 only |

### .com-required mode — specific guidance

Pure 4-5 letter pronounceable .com is **almost extinct**. To find available .com:
- Bias toward **length 7-8** (still short, vastly more available)
- Use **double letters** (e.g. `Spello`, `Vexxa`) — many singles taken, doubles often free
- Use **Q/X/Z + vowel** combos — much less explored
- Use **two-syllable compounds** (`Wavkit`, `Joopli`) — strong availability
- Avoid pure dictionary words — every English word ≤6 chars on .com is gone

### Anti-duplicate guard

Track names tried across batches. Never re-emit a candidate that already failed in a prior batch.

## 4. Domain Check (one call per batch)

Choose TLD set based on Q4 answer:

| Q4 answer | TLDs to check |
|-----------|---------------|
| `.com required` | `com,io,ai,app,dev,co,net` |
| `.com preferred` | `com,io,ai,app,dev,co,net` |
| `Any premium` | `com,io,ai,app,dev,co` |
| `Modern only` | `io,ai,app,dev` |

Single parallel call per batch:

```bash
python3 .claude/skills/domain-checker/scripts/check_domains.py \
  cand1 cand2 cand3 cand4 cand5 cand6 cand7 cand8 cand9 cand10 cand11 cand12 \
  --tlds <chosen-set> \
  --format json --no-color
```

Parse JSON. For each name, build a per-TLD status: `available` / `taken` / `aftermarket` / `expiring` / `unknown`. Mark as `premium` if status is `available` AND `evidence` contains `likely premium tier`.

Then apply the availability filter from Section 2.

## 5. Score Each PASSING Candidate (5 dims × 0-10, max 50)

Score only the names that survived availability filtering — no point scoring losers.

### A. Length (deterministic)
| chars | score |
|-------|-------|
| 3-4 | 10 |
| 5 | 9 |
| 6 | 8 |
| 7 | 6 |
| 8 | 4 |
| 9 | 2 |
| 10+ | 0 |

### B. Memorability (judgment, 0-10)
Pronounceable on first sight, vowel/consonant balance, ≤2 syllables ideal.

### C. Brandability (judgment, 0-10)
Distinct, evocative, brandable (Stripe, Bolt). Generic descriptors score low.

### D. Cross-Language Safety (judgment, 0-10) — CRITICAL
Check each candidate against these languages. Deduct for negative meaning, awkward homophone, or offensive sound:

| Language | Watch for |
|----------|-----------|
| Spanish | Body-part words, swears (kaka, polla, joder, coño) |
| French | Con, merde, awkward double meanings |
| German | Tod (death), Krank (sick), Furz, false-friends |
| Italian | Cazzo, fica, stronzo |
| Portuguese (BR/PT) | Pinto, buceta, BR-PT slang |
| Russian | Cognates with negative meanings |
| Mandarin (pinyin) | Tonal homophones for 死 (sǐ — death/"4"); avoid bare "si"; check for 笨/蠢 |
| Japanese (romaji) | Shi (death), ku (suffering); avoid bare "shi" |
| Korean | Romanizations to avoid |
| Hindi/Urdu | Common slurs |
| Arabic | Religiously sensitive words, common slurs |
| Turkish | Common slurs |

Rubric:
- 10: no negative meaning in any language above
- 7: neutral across all
- 4: mildly negative in 1 language → flag in `concerns`
- 0: offensive in 1+ major language → **drop from top 5 entirely**

### E. Spelling Clarity (judgment, 0-10)
Easy to spell from hearing once. Penalize K/C, PH/F, vowel-drop ambiguity, silent letters.

## 6. Domain Bonus (deterministic, on PASSING names only)

| Signal | Bonus |
|--------|-------|
| `.com` available (not premium) | +15 |
| `.ai` or `.io` available (not premium) | +10 each |
| `.app` / `.dev` / `.co` / `.net` available (not premium) | +5 each |
| Any TLD `expiring` | +2 (note in `concerns`) |

**Penalties (only relevant when Q5 permits premium/aftermarket):**

| Signal | Penalty |
|--------|---------|
| Required-tier TLD only qualifies via `premium` | −8 |
| Required-tier TLD only qualifies via `aftermarket` | −10 |
| (Premium/aftermarket on a non-required TLD that also has a free required-tier) | 0 (just flag) |

Rationale: names that only "pass" because the user opted into premium/aftermarket should still rank below names with truly free domains. The penalty keeps free names on top while still surfacing premium options the user explicitly asked for.

**Final total** = sum of 5 quality scores + domain_bonus + penalties. Practical max ~80.

## 7. Write CSV

```bash
mkdir -p out
```

Path: `out/name-search-YYYY-MM-DD-<topic-slug>.csv`
(today's date; topic-slug from industry+vibe, kebab-case)

Columns:
```
name,length,score_length,score_memorability,score_brandability,score_linguistic_safety,score_spelling,subtotal,com,io,ai,app,dev,co,net,domain_bonus,total_score,concerns
```

Rules:
- **Only include candidates that passed the availability filter.** This is the entire point of the rewrite. Do not write rejected names to the CSV.
- `subtotal` = sum of 5 score columns
- Each TLD column = `available` / `taken` / `aftermarket` / `expiring` / `premium` / `unknown` / `-`
- `concerns` = semicolon-separated notes (language warnings, TM hints, expiring TLD, etc.)
- Quote any field containing `,` or `;`

Use the `Write` tool — direct CSV emission. Do NOT use echo/cat heredocs.

## 8. Sort with data-wrangler

```bash
python3 .claude/skills/data-wrangler/scripts/data_wrangler.py sort \
  out/name-search-<date>-<slug>.csv \
  --by total_score --desc \
  -o out/name-search-<date>-<slug>-ranked.csv
```

## 9. Console Output

Print the ranked table (everything in the CSV — these are all valid under the chosen Q4+Q5 modes):

```
Rank  Name      Total  Sub  .com       .ai       .io       .app     .dev     Concerns
----  --------  -----  ---  ---------  --------  --------  -------  -------  ---------------------------
 1    Loomly      78   43   ✓ free     ✓ free    ✓ free    ✓ free   ✓ free   -
 2    Vexyl       72   46   ✓ free     ✓ free    ✓ free    taken    taken    TM check (Vexel exists)
 3    Zoryx       65   40   ! premium  ✓ free    ✓ free    taken    ✓ free   .com=premium ($$$); RU: zorja=dawn
 4    Brello      58   44   $ aftermkt ✓ free    ✓ free    ✓ free   ✓ free   .com on GoDaddy auction
```

Symbols: `✓ free`, `✗ taken`, `$ aftermkt`, `~ expiring`, `! premium`, `?` unknown.

When the table contains any `! premium` or `$ aftermkt` rows, print a short legend right under it explaining the symbols and reminding the user these involve extra cost (registry premium pricing or marketplace asking price).

Then a **Recommended top 3** block: name + 1-line rationale (why it wins on the rubric). If any top-3 name relies on a premium or aftermarket TLD, the rationale MUST state that explicitly (e.g. "best fit but .com is on GoDaddy aftermarket — confirm budget").

## 10. Hard Rules

1. **AVAILABILITY FILTER IS ABSOLUTE.** No name appears in the CSV if it fails the filter from Section 2 under the chosen Q4+Q5 modes. Don't even score names that fail.
2. **NEVER** recommend a name with `score_linguistic_safety < 7` in the top 5.
3. **ALWAYS** flag any `aftermarket` / `premium` / `expiring` TLD in the `concerns` column — including when Q5 permits them as pass reasons. The user must never be surprised by a price.
4. **Q5 = "Only ready-for-registration" is strict.** In this mode, any TLD with `premium` or `aftermarket` status is treated identically to `taken` for filter purposes (the name only passes if a *different* TLD in the Q4 set qualifies cleanly).
5. If after **6 batches** the accumulator has fewer than 10 passing names, save what we have (could be 3 names, could be 0) and emit a clear warning explaining why (saturation + which constraint is biting — Q3 length, Q4 TLD, or Q5 mode).
6. If the accumulator is **empty** after 6 batches, before writing CSV: ask the user via `AskUserQuestion` whether to **broaden** the filter one notch — options should include relaxing Q4 (e.g. `.com required` → `.com preferred`), relaxing Q5 (e.g. add registry-premium or aftermarket), or relaxing Q3 (e.g. ≤6 → ≤8). Don't silently produce an empty file.
7. Never include must-include user words silently dropped — if the user asked for "must contain 'health'" and no candidate uses it, keep generating.

## 11. Output Summary

Final assistant message must contain:
- Path to the ranked CSV
- The console table (all rows — all are by definition viable under the chosen Q4+Q5 modes)
- The recommended top 3 with rationales (call out premium/aftermarket reliance explicitly when present)
- A stats line: `Generated N candidates across M batches; K passed availability filter (Q4=<mode>, Q5=<mode>); P of K rely on premium/aftermarket`
- Any warnings (saturation, fallback applied, < target hit, premium/aftermarket prevalence)
