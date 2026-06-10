# TLD Notes

Notes about which check method works best per TLD. The default `auto` mode
(RDAP first, WHOIS fallback) handles everything below transparently — this
reference is for cases where you want to force a method explicitly.

## RDAP-native (fast, reliable)

These TLDs respond well to RDAP — `auto` will use RDAP and never fall back.

| TLD | RDAP server (example) |
|-----|------------------------|
| `.com` | `rdap.verisign.com/com/v1` |
| `.net` | `rdap.verisign.com/net/v1` |
| `.org` | `rdap.publicinterestregistry.org/rdap` |
| `.info` | `rdap.identitydigital.services/rdap` |
| `.biz` | `rdap.nic.biz` |
| `.app`, `.dev`, `.page` | `pubapi.registry.google/rdap` |
| `.ai` | `rdap.identitydigital.services/rdap` |
| `.cloud` | `rdap.registry.cloud/rdap` |
| `.xyz` | `rdap.centralnic.com/xyz` |
| `.tech` | `rdap.radix.host/rdap` |
| `.online`, `.site`, `.store` | `rdap.centralnic.com/<tld>` |

## RDAP-missing — WHOIS fallback used

These TLDs do not currently expose public RDAP. `auto` mode falls back to
the local `whois` CLI for them.

- `.io`
- `.co` (Colombia)
- `.me`
- Most ccTLDs without a managed RDAP service

If `whois` is not installed, results for these TLDs will show `unknown`.
Install with:

```bash
# macOS (whois is pre-installed on most versions; otherwise)
brew install whois

# Debian/Ubuntu
sudo apt install whois

# Alpine
apk add whois
```

## Quirks

- **`.uk` family** (`.co.uk`, `.org.uk`) — Nominet RDAP exists but rate-limits
  hard; `auto` mode will use WHOIS fallback frequently. Prefer
  `--method whois` for bulk checks.
- **`.de`** — DENIC WHOIS returns minimal info; the script's WHOIS pattern
  matcher will usually classify correctly, but verify edge cases at a registrar.
- **Premium domains** — RDAP/WHOIS will report `available` for premium names
  that the registry actually charges $$$$ for. The skill cannot detect this;
  always check the registrar checkout for true cost.
- **Pending delete / redemption** — domains that just expired may show
  `available` in RDAP but cannot be registered yet. Re-check after 30 days,
  or use a drop-catcher service.

## IANA Bootstrap

Authoritative TLD → RDAP server mapping lives at:

```
https://data.iana.org/rdap/dns.json
```

The skill caches this for 24h at `~/.cache/domain-checker/rdap-bootstrap.json`.
To force a refresh:

```bash
rm ~/.cache/domain-checker/rdap-bootstrap.json
```

> Note: ICANN sunset the gTLD WHOIS (port-43) requirement on 2025-01-28 — RDAP is authoritative for gTLDs; WHOIS fallback remains needed only for ccTLDs (.io/.co/.me/.de) absent from the IANA RDAP bootstrap. Server examples above drift — the script always resolves live from https://data.iana.org/rdap/dns.json.
