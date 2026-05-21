---
name: domain-checker
description: >
  Bulk domain availability checker. Use when the user wants to check whether
  one or many domain names are available for registration (e.g., "is acme.com
  free", "check these 50 domains", "find an available .io for my brand").
  Supports any TLD (.com/.net/.io/.ai/.dev/.app/...), parallel checking, three
  input modes (CLI args / file / stdin), bare-name + TLD-list expansion, and
  table/JSON/CSV output. Python stdlib only — no pip installs, no API keys.
author: George Khananaev
---

# Domain Checker

Check domain availability in bulk using RDAP (Registration Data Access Protocol) as the primary signal, with WHOIS and DNS fallbacks. Python stdlib only.

## When to Use

- User asks "is `<domain>` available / taken / registered?"
- User wants to check many domains at once (a list, a file, names piped in)
- User wants to test a brand name across many TLDs (`acme.com`, `acme.net`, `acme.io`, …)
- User wants machine-readable output (CSV/JSON) for further processing
- User wants only available (or only taken) results filtered

Do NOT use for: WHOIS contact lookup (this skill only checks existence), DNS record inspection (use `dig`), trademark/legal availability (this only checks registration status).

## How It Works

1. **RDAP first** — fetches the IANA RDAP bootstrap (`data.iana.org/rdap/dns.json`, cached 24h in `~/.cache/domain-checker/`) to find the authoritative RDAP server for each TLD. `HTTP 404` = available, `HTTP 200` = taken.
2. **WHOIS fallback** — if RDAP is unavailable for a TLD (notably `.io`, some ccTLDs) or returns ambiguous, shells out to the local `whois` CLI and matches well-known "not found"/"registered" patterns.
3. **DNS** — optional, weak signal. Resolves A/AAAA records. Confirms "taken" only — registered-but-unhosted domains will show no DNS, so DNS alone cannot prove "available".

After the primary check, three enrichment passes refine accuracy:

4. **Aftermarket detection** — parses the RDAP response we already fetched. Flags `aftermarket` when the registrant/entity name matches a known reseller (HugeDomains, Sedo, Afternic, Dan.com, NameJet, DropCatch, …) OR when the nameservers match parking patterns (`sedoparking.com`, `parkingcrew.net`, `namefind.com`, `afternic.com`, `bodis.com`, …). Free — no extra requests.
5. **RDAP status parsing** — surfaces `pendingDelete` / `redemptionPeriod` / `clientHold` / `serverHold` as a separate `expiring` status (these domains may drop and become available within ~30 days).
6. **Premium-likely hint** — for `available` results, appends a warning when the name is short (`≤5` chars on `.ai/.io/.app/.dev/.co/.tv/.me/.cc/.tech/.xyz` or `≤3` chars on `.com/.net/.org`). This is a heuristic, not a hard claim — the registrar checkout has the real price.
7. **Optional HTTP sale-page probe** (`--probe-sale`) — fetches the homepage and looks for "for sale" / Sedo / Dan.com / HugeDomains / Afternic markers. Reclassifies `taken` → `aftermarket` on a hit. Off by default; adds ~1s per checked domain.

Concurrency via `ThreadPoolExecutor` (default 10 workers). Per-request timeout default 8s.

## Prerequisites

- Python 3.8+ (stdlib only)
- Outbound HTTPS to RDAP servers
- Optional: `whois` CLI (`brew install whois` / `apt install whois`) for fallback on TLDs without RDAP

## Quick Routing

| Task | Command |
|------|---------|
| Check single domain | `check_domains.py acme.com` |
| Check many domains | `check_domains.py acme.com acme.net acme.io` |
| Bare name across TLDs | `check_domains.py acme --tlds com,net,io,ai,dev` |
| From a file | `check_domains.py --file domains.txt` |
| From stdin | `cat list.txt \| check_domains.py --stdin` |
| Only available | `check_domains.py --file list.txt --only-available` |
| JSON output | `check_domains.py acme.com --format json` |
| CSV output | `check_domains.py acme.com --format csv` |
| Force WHOIS only | `check_domains.py acme.io --method whois` |
| Fastest (DNS only) | `check_domains.py acme.com --method dns` |

## Usage

```bash
python3 .claude/skills/domain-checker/scripts/check_domains.py [DOMAINS...] [OPTIONS]
```

### Examples

```bash
# Single domain
python3 scripts/check_domains.py google.com

# Many domains
python3 scripts/check_domains.py acme.com acme.net brandidea.io

# Brand-name search across TLDs
python3 scripts/check_domains.py mybrand --tlds com,net,io,ai,dev,app

# From a file (one domain per line, # comments allowed)
python3 scripts/check_domains.py --file domains.txt

# From stdin
printf 'foo.com\nbar.io\n' | python3 scripts/check_domains.py --stdin

# Only available, as CSV (great for piping into a sheet)
python3 scripts/check_domains.py --file candidates.txt --only-available --format csv > available.csv

# JSON for programmatic use
python3 scripts/check_domains.py acme --tlds com,net,io --format json

# Higher parallelism for big lists
python3 scripts/check_domains.py --file 500-domains.txt -c 25

# Exit code reflects unknown/invalid results (for CI)
python3 scripts/check_domains.py --file list.txt --exit-code
```

## Output

Default `table` format:

```
   domain         status        method  evidence                                                    ms
-  -------------  ------------  ------  ----------------------------------------------------------  ----
✓  acme.dev       available     rdap    RDAP 404 from https://pubapi.registry.google/rdap           437
✓  bzqj.dev       available     rdap    RDAP 404 …; likely premium tier (.dev <=5 chars)            383
✗  google.com     taken         rdap    RDAP 200 from https://rdap.verisign.com/com/v1              333
$  foothill.com   aftermarket   rdap    RDAP 200 …; parking NS: ns1.afternic.com                    352
~  someone.com    expiring      rdap    RDAP 200 …; status: pendingdelete                           340
?  bizarre.tld    unknown       rdap    no RDAP server for .tld                                     12
!  bad..domain    invalid               invalid domain syntax                                       0
```

| Symbol | Status | Meaning |
|--------|--------|---------|
| `✓` | `available` | No registration record found (RDAP 404 or WHOIS no-match) |
| `✗` | `taken` | Domain is registered (legit ownership) |
| `$` | `aftermarket` | Registered but held by a domain investor / parking service — usually for resale at premium prices |
| `~` | `expiring` | Registered but in `pendingDelete` / `redemptionPeriod` / `clientHold` — may drop and become available |
| `?` | `unknown` | Neither method could decide (rate-limited, no RDAP server, etc.) — retry, or use a registrar to confirm |
| `!` | `invalid` | Domain syntax invalid |
| `·` | `reserved` | TLD-reserved (rare, e.g. some registry-internal names) |

For `available` results, the `evidence` column may include `likely premium tier (...)` — a heuristic warning that the registry probably charges a premium for this short name on this TLD.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| positional `DOMAINS` | — | Zero or more domains or bare names |
| `-f`, `--file PATH` | — | Read domains from file (one per line, `#` comments OK) |
| `--stdin` | off | Read domains from stdin |
| `--tlds com,net,...` | — | TLDs to append to bare names (only used for inputs without a `.`) |
| `-m`, `--method` | `auto` | `auto` (rdap→whois), `rdap`, `whois`, `dns`, or comma list |
| `-c`, `--concurrency N` | `10` | Parallel workers |
| `-t`, `--timeout S` | `8.0` | Per-request timeout, seconds |
| `--format` | `table` | `table`, `json`, or `csv` |
| `--only-available` | off | Filter output to `available` only |
| `--only-taken` | off | Filter output to `taken` / `aftermarket` / `expiring` |
| `--no-color` | off | Disable ANSI colors in table output |
| `--no-aftermarket-detect` | off | Skip RDAP entity / nameserver analysis (faster, less accurate) |
| `--no-premium-hint` | off | Don't warn on short available names |
| `--probe-sale` | off | HTTP-probe taken domains for "for sale" landing pages (~1s/domain) |
| `--exit-code` | off | Exit non-zero if any `unknown`/`invalid` result (useful in CI) |

`--only-available` and `--only-taken` are mutually exclusive (last one wins).

## Method Notes

| Method | Pros | Cons |
|--------|------|------|
| `rdap` | Standardized JSON; works for nearly all gTLDs; fast; no parsing fragility | Some ccTLDs (`.io`, `.co.uk`, …) don't expose RDAP |
| `whois` | Covers TLDs without RDAP | Output format varies per registry; rate-limited; requires CLI installed |
| `dns` | Very fast | Cannot prove "available" — registered-but-unhosted domains have no DNS |
| `auto` (default) | RDAP first, WHOIS fallback when RDAP is unavailable/inconclusive | Slightly slower on TLDs that need fallback |

## Improving Accuracy

Default mode already runs aftermarket detection + premium hints (no extra cost — they reuse the RDAP response). For maximum accuracy on important brand searches, add `--probe-sale`:

```bash
python3 scripts/check_domains.py mybrand --tlds com,net,io,ai,dev --probe-sale
```

What each enrichment catches:

| Enrichment | Detects | Cost |
|------------|---------|------|
| Aftermarket via RDAP entities | HugeDomains / Sedo / Afternic / Dan.com / NameJet etc. as the registrar or registrant | Free — re-uses RDAP response |
| Aftermarket via parking nameservers | `afternic.com`, `sedoparking.com`, `parkingcrew.net`, `namefind.com` (GoDaddy investor portfolio), `bodis.com`, `dan.com`, `hugedomains.com` | Free |
| RDAP status parsing | `pendingDelete` / `redemptionPeriod` / `clientHold` | Free |
| Premium-likely hint | `≤5` chars on `.ai/.io/.app/.dev/.co/.tv/.me/.cc/.tech/.xyz`; `≤3` chars on `.com/.net/.org` | Free (local) |
| `--probe-sale` HTTP fetch | "For sale" landing pages (Sedo, Dan.com, HugeDomains, GoDaddy Auctions, Afternic) | ~1s/domain |

### What this can't catch

| Limitation | Why |
|------------|-----|
| Exact premium price | No free API exposes registry-tier pricing. Always check the registrar checkout. |
| Trademark conflicts | Requires USPTO TESS / WIPO lookups (out of scope). |
| Privately-held investor domains | Brokers using cloaked WHOIS + non-parking nameservers (e.g. Cloudflare) will look like normal "taken" — only `--probe-sale` can sometimes catch these via the landing page. |
| Domains in pendingCreate / about to register | RDAP shows them as available; you'll race the registrant at checkout. |

## Caching

The IANA RDAP bootstrap is cached for 24 hours at:

```
~/.cache/domain-checker/rdap-bootstrap.json
```

Delete that file to force a refresh.

## Limitations

- **Rate limits**: registry RDAP servers will rate-limit aggressive bulk checks. For lists >200 domains, consider `-c 5` and reasonable spacing.
- **Truth-source**: a domain marked `available` here may still be unregisterable (premium, reserved by registry, or held in pending-delete). Always confirm at the registrar checkout.
- **Privacy**: every RDAP/WHOIS query is logged by the registry. Don't bulk-check competitor brand lists from infrastructure you don't want associated with the queries.
- **No registrar pricing**: this skill only reports availability — pricing varies wildly across registrars and is not queried.

## See Also

- `references/tlds.md` — common TLDs and which method works best for each
