#!/usr/bin/env python3
"""Bulk domain availability checker.

Primary signal: RDAP (Registration Data Access Protocol) — JSON, standardized,
no API key. The IANA bootstrap (https://data.iana.org/rdap/dns.json) maps each
TLD to its authoritative RDAP server. A 404 means "no registration record" =>
available. A 200 with response means registered.

Fallbacks (in order):
  - `whois` CLI if installed (parsed for "no match"/"not found" patterns)
  - DNS resolution (weak signal: registered domains may have no DNS; parked
    domains DO have DNS, so this only confirms "definitely taken")

Outputs: table (default), json, csv. Parallel via thread pool.
Python stdlib only — no pip installs required.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import io
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Iterable

USER_AGENT = "domain-checker/1.0 (+claude-skills-vault)"
IANA_BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
RDAP_BOOTSTRAP_CACHE: dict | None = None
RDAP_BOOTSTRAP_FETCHED_AT = 0.0
RDAP_CACHE_TTL_SECONDS = 24 * 3600

# Status tokens used in output.
STATUS_AVAILABLE = "available"
STATUS_TAKEN = "taken"
STATUS_AFTERMARKET = "aftermarket"  # taken & held for resale (squatter/parking)
STATUS_EXPIRING = "expiring"        # taken but in pendingDelete/redemptionPeriod
STATUS_UNKNOWN = "unknown"
STATUS_INVALID = "invalid"
STATUS_RESERVED = "reserved"

# Known aftermarket / domain-resale entities (matched in RDAP vCard `fn` field).
# Substring match, lowercase. Conservative — only flag domain investors here,
# NOT mainstream registrars like GoDaddy/Namecheap (most of their customers are
# legit). GoDaddy aftermarket activity is detected via Afternic NS instead.
AFTERMARKET_ENTITIES = (
    "hugedomains",
    "sedo gmbh",
    "sedo.com",
    "afternic",
    "dan.com",
    "namejet",
    "dropcatch",
    "snapnames",
    "buydomains",
    "uniregistry market",
    "domainmarket",
    "saw.com",
    "epik holdings",
    "network solutions aftermarket",
)

# Nameserver hostnames associated with parking / resale landing pages.
# Match by substring (lowercase).
PARKING_NS_PATTERNS = (
    "sedoparking.com",
    "parkingcrew.net",
    "parkingcrew.com",
    "dan.com",
    "dnsowl.com",
    "cashparking.com",
    "bodis.com",
    "above.com",
    "expiredns.net",
    "hugedomains.com",
    "afternic.com",
    "namefind.com",          # GoDaddy domain-investor portfolio
    "uniregistrymarket",
    "parklogic.com",
    "trafficclub.com",
    "fabulous.com",
    "domainsponsor.com",
    "internettraffic.com",
    "skenzo.com",
    "voodoo.com",
    "buydomains.com",
    "domainmarket.com",
    "ns1.dan.com",
    "ns2.dan.com",
)

# RDAP status codes that mean the domain is registered but won't survive long.
EXPIRING_STATUSES = (
    "pending delete",
    "pendingdelete",
    "redemption period",
    "redemptionperiod",
    "client hold",
    "clienthold",
    "server hold",
    "serverhold",
)

# Heuristic: "premium-likely" available domains.
# Short names on premium TLDs almost always carry a premium-tier registry price,
# so an RDAP 404 here is NOT the cheap-checkout result a user might expect.
PREMIUM_TLDS = {"ai", "io", "app", "dev", "co", "tv", "me", "cc", "tech", "xyz"}
PREMIUM_LEN_ON_PREMIUM_TLD = 5   # <=5 chars on a premium TLD
PREMIUM_LEN_ON_COM = 3           # <=3 chars on .com / .net / .org

# HTTP markers indicating a "this domain is for sale" landing page.
# Bytes (not str) — we match on raw body, lowercased.
SALE_MARKERS = (
    b"this domain is for sale",
    b"buy this domain",
    b"make an offer",
    b"domain for sale",
    b"sedoparking.com",
    b"dan.com/buy",
    b"hugedomains.com",
    b"the domain you are trying",
    b"interested in this domain",
    b"this premium domain",
    b"afternic.com",
    b"is parked free",
    b"undeveloped.com",
    b"domain is parked",
)

# Conservative WHOIS "available" patterns (lowercased match).
WHOIS_AVAILABLE_PATTERNS = (
    "no match for",
    "no entries found",
    "not found",
    "no data found",
    "domain not found",
    "no object found",
    "status: free",
    "status: available",
    "status:\t\tavailable",
    "available for registration",
    "is free",
    "no such domain",
)
WHOIS_TAKEN_PATTERNS = (
    "registrar:",
    "creation date",
    "created on",
    "created:",
    "registered on",
    "registry domain id",
    "domain name:",
    "registrant",
)

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,63}$",
    re.IGNORECASE,
)


# ── RDAP ─────────────────────────────────────────────────────────────────────

def _http_get(url: str, timeout: float) -> tuple[int, bytes]:
    """GET returning (status, body). Does NOT raise for non-2xx — returns code."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rdap+json, application/json;q=0.9, */*;q=0.5",
    })
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, body


def load_rdap_bootstrap(timeout: float = 10.0) -> dict:
    """Fetch & cache IANA RDAP bootstrap (TLD -> [RDAP servers])."""
    global RDAP_BOOTSTRAP_CACHE, RDAP_BOOTSTRAP_FETCHED_AT
    now = time.time()
    if RDAP_BOOTSTRAP_CACHE and (now - RDAP_BOOTSTRAP_FETCHED_AT) < RDAP_CACHE_TTL_SECONDS:
        return RDAP_BOOTSTRAP_CACHE
    # Local disk cache keeps repeated invocations fast.
    cache_path = os.path.join(
        os.path.expanduser("~"), ".cache", "domain-checker", "rdap-bootstrap.json"
    )
    try:
        st = os.stat(cache_path)
        if (now - st.st_mtime) < RDAP_CACHE_TTL_SECONDS:
            with open(cache_path) as f:
                data = json.load(f)
            RDAP_BOOTSTRAP_CACHE = data
            RDAP_BOOTSTRAP_FETCHED_AT = st.st_mtime
            return data
    except FileNotFoundError:
        pass
    except Exception:
        pass

    status, body = _http_get(IANA_BOOTSTRAP_URL, timeout=timeout)
    if status != 200:
        raise RuntimeError(f"RDAP bootstrap fetch failed: HTTP {status}")
    data = json.loads(body.decode("utf-8"))
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(data, f)
    except Exception:
        pass
    RDAP_BOOTSTRAP_CACHE = data
    RDAP_BOOTSTRAP_FETCHED_AT = now
    return data


def rdap_servers_for(tld: str, bootstrap: dict) -> list[str]:
    tld = tld.lower().lstrip(".")
    services = bootstrap.get("services") or []
    for entry in services:
        if not isinstance(entry, list) or len(entry) < 2:
            continue
        tlds, urls = entry[0], entry[1]
        if tld in (t.lower() for t in tlds):
            return [u.rstrip("/") for u in urls]
    return []


def rdap_check(domain: str, bootstrap: dict, timeout: float) -> tuple[str, str, dict | None]:
    """Return (status, evidence, raw_rdap_or_None)."""
    parts = domain.rsplit(".", 1)
    if len(parts) != 2:
        return STATUS_INVALID, "no TLD", None
    tld = parts[1].lower()
    servers = rdap_servers_for(tld, bootstrap)
    if not servers:
        return STATUS_UNKNOWN, f"no RDAP server for .{tld}", None

    last_err = ""
    for base in servers:
        url = f"{base}/domain/{domain}"
        try:
            code, body = _http_get(url, timeout=timeout)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            continue

        if code == 404:
            return STATUS_AVAILABLE, f"RDAP 404 from {base}", None
        if code == 200:
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception:
                data = None
            # Some registries return 200 with errorCode for missing domains.
            if isinstance(data, dict) and data.get("errorCode") == 404:
                return STATUS_AVAILABLE, f"RDAP 200/errorCode=404 from {base}", None
            return STATUS_TAKEN, f"RDAP 200 from {base}", data
        if code == 400 and b"reserved" in body.lower():
            return STATUS_RESERVED, f"RDAP 400 reserved from {base}", None
        last_err = f"HTTP {code} from {base}"

    return STATUS_UNKNOWN, last_err or "all RDAP servers failed", None


# ── WHOIS fallback ───────────────────────────────────────────────────────────

_WHOIS_BIN = shutil.which("whois")


def whois_check(domain: str, timeout: float) -> tuple[str, str]:
    """Shell out to the `whois` CLI. Returns (status, evidence)."""
    if not _WHOIS_BIN:
        return STATUS_UNKNOWN, "whois CLI not installed"
    try:
        proc = subprocess.run(
            [_WHOIS_BIN, domain],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return STATUS_UNKNOWN, "whois timeout"
    except Exception as e:
        return STATUS_UNKNOWN, f"whois error: {e}"

    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    low = text.lower()
    for pat in WHOIS_AVAILABLE_PATTERNS:
        if pat in low:
            return STATUS_AVAILABLE, f"whois: matched '{pat}'"
    for pat in WHOIS_TAKEN_PATTERNS:
        if pat in low:
            return STATUS_TAKEN, f"whois: matched '{pat}'"
    return STATUS_UNKNOWN, "whois: no decisive pattern"


# ── DNS quick check ──────────────────────────────────────────────────────────

def dns_has_record(domain: str, timeout: float) -> bool:
    """True if any A/AAAA record resolves. Weak positive signal only."""
    socket.setdefaulttimeout(timeout)
    try:
        socket.getaddrinfo(domain, None)
        return True
    except Exception:
        return False


# ── RDAP response analysis ───────────────────────────────────────────────────

def _vcard_fn(entity: dict) -> str:
    """Pull the `fn` (full name) value from an RDAP entity's vcardArray."""
    vcard = entity.get("vcardArray") or []
    if not (isinstance(vcard, list) and len(vcard) >= 2 and isinstance(vcard[1], list)):
        return ""
    for prop in vcard[1]:
        if isinstance(prop, list) and len(prop) >= 4 and prop[0] == "fn":
            return str(prop[3] or "")
    return ""


def _all_entity_names(data: dict) -> list[str]:
    """Recursively walk RDAP entities (including nested sub-entities) and
    return every full-name string we can find. Lowercased."""
    out: list[str] = []
    def walk(node):
        if not isinstance(node, dict):
            return
        if node.get("objectClassName") == "entity":
            fn = _vcard_fn(node)
            if fn:
                out.append(fn.lower())
            # roles + handle as secondary signals
            for k in ("handle",):
                v = node.get(k)
                if isinstance(v, str):
                    out.append(v.lower())
        for sub in (node.get("entities") or []):
            walk(sub)
    walk(data)
    for sub in (data.get("entities") or []):
        walk(sub)
    return out


def _nameservers(data: dict) -> list[str]:
    out: list[str] = []
    for ns in (data.get("nameservers") or []):
        name = ns.get("ldhName") or ns.get("unicodeName") or ""
        if name:
            out.append(name.lower())
    return out


def _status_codes(data: dict) -> list[str]:
    raw = data.get("status") or []
    return [str(s).lower() for s in raw if isinstance(s, str)]


def analyze_rdap_response(data: dict | None) -> tuple[str | None, str]:
    """Re-classify a 'taken' RDAP response.

    Returns (override_status_or_None, evidence_suffix).
    - override_status is one of STATUS_AFTERMARKET, STATUS_EXPIRING, or None
      (no override — keep generic 'taken').
    """
    if not isinstance(data, dict):
        return None, ""

    statuses = _status_codes(data)
    for code in statuses:
        for pat in EXPIRING_STATUSES:
            if pat in code:
                return STATUS_EXPIRING, f"; status: {code}"

    names = _all_entity_names(data)
    for nm in names:
        for pat in AFTERMARKET_ENTITIES:
            if pat in nm:
                return STATUS_AFTERMARKET, f"; reseller: {nm[:40]}"

    nss = _nameservers(data)
    for ns in nss:
        for pat in PARKING_NS_PATTERNS:
            if pat in ns:
                return STATUS_AFTERMARKET, f"; parking NS: {ns}"

    return None, ""


# ── Premium-likely heuristic ─────────────────────────────────────────────────

def premium_hint(domain: str) -> str:
    """If `domain` is likely registry-premium (so 'available' from RDAP probably
    means $$$$ at checkout), return a short hint. Empty string otherwise."""
    parts = domain.rsplit(".", 1)
    if len(parts) != 2:
        return ""
    name, tld = parts[0].lower(), parts[1].lower()
    name_len = len(name)
    if tld in PREMIUM_TLDS and name_len <= PREMIUM_LEN_ON_PREMIUM_TLD:
        return f"likely premium tier (.{tld} <={PREMIUM_LEN_ON_PREMIUM_TLD} chars)"
    if tld in ("com", "net", "org") and name_len <= PREMIUM_LEN_ON_COM:
        return f"likely premium tier (.{tld} <={PREMIUM_LEN_ON_COM} chars)"
    return ""


# ── HTTP sale-page probe ─────────────────────────────────────────────────────

def probe_sale_page(domain: str, timeout: float) -> str:
    """Fetch http(s)://<domain>/ and look for sale-page markers.
    Returns a short marker string if found, else "". Best-effort only."""
    for scheme in ("https", "http"):
        url = f"{scheme}://{domain}/"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read(64 * 1024).lower()
        except urllib.error.HTTPError as e:
            try:
                body = e.read(64 * 1024).lower()
            except Exception:
                body = b""
        except Exception:
            continue
        for marker in SALE_MARKERS:
            if marker in body:
                return marker.decode("latin-1", errors="replace")
    return ""


# ── Orchestration ────────────────────────────────────────────────────────────

def validate_domain(d: str) -> str | None:
    d = d.strip().lower().rstrip(".")
    if not d:
        return None
    if not DOMAIN_RE.match(d):
        return None
    return d


def check_one(
    domain: str,
    method: str,
    bootstrap: dict,
    timeout: float,
    detect_aftermarket: bool = True,
    hint_premium: bool = True,
    probe_sale: bool = False,
) -> dict:
    """Run the configured methods for a single domain. Returns a result dict."""
    start = time.time()
    out: dict = {
        "domain": domain,
        "status": STATUS_UNKNOWN,
        "method": "",
        "evidence": "",
        "elapsed_ms": 0,
    }

    norm = validate_domain(domain)
    if norm is None:
        out["status"] = STATUS_INVALID
        out["evidence"] = "invalid domain syntax"
        out["elapsed_ms"] = int((time.time() - start) * 1000)
        return out
    out["domain"] = norm

    methods = [m.strip() for m in method.split(",") if m.strip()]
    if "auto" in methods or not methods:
        methods = ["rdap", "whois"]

    rdap_raw: dict | None = None
    for m in methods:
        if m == "rdap":
            try:
                status, evidence, rdap_raw = rdap_check(norm, bootstrap, timeout)
            except Exception as e:
                status, evidence = STATUS_UNKNOWN, f"rdap error: {e}"
            out.update(status=status, method="rdap", evidence=evidence)
            if status in (STATUS_AVAILABLE, STATUS_TAKEN, STATUS_RESERVED):
                break
        elif m == "whois":
            status, evidence = whois_check(norm, timeout)
            out.update(status=status, method="whois", evidence=evidence)
            if status in (STATUS_AVAILABLE, STATUS_TAKEN):
                break
        elif m == "dns":
            has = dns_has_record(norm, timeout)
            out.update(
                status=STATUS_TAKEN if has else STATUS_UNKNOWN,
                method="dns",
                evidence="DNS resolves" if has else "DNS no record (inconclusive)",
            )
            if has:
                break
        else:
            out["evidence"] = f"unknown method: {m}"

    # ── Enrichment passes ─────────────────────────────────────────────────
    # Reclassify "taken" via RDAP entity / NS / status analysis.
    if detect_aftermarket and out["status"] == STATUS_TAKEN and rdap_raw:
        override, extra = analyze_rdap_response(rdap_raw)
        if override:
            out["status"] = override
            out["evidence"] = (out["evidence"] or "") + extra

    # Optional HTTP probe for sale pages — runs only on taken/aftermarket.
    if probe_sale and out["status"] in (STATUS_TAKEN, STATUS_AFTERMARKET):
        marker = probe_sale_page(norm, timeout=min(timeout, 4.0))
        if marker:
            out["status"] = STATUS_AFTERMARKET
            out["evidence"] = (out["evidence"] or "") + f"; sale page: '{marker[:30]}'"

    # Premium-likely hint on "available" results.
    if hint_premium and out["status"] == STATUS_AVAILABLE:
        hint = premium_hint(norm)
        if hint:
            out["evidence"] = (out["evidence"] or "") + f"; {hint}"

    out["elapsed_ms"] = int((time.time() - start) * 1000)
    return out


def expand_domains(
    raw_inputs: Iterable[str], tlds: list[str] | None
) -> list[str]:
    """Expand inputs: bare names + --tlds list -> name.tld combinations."""
    out: list[str] = []
    for item in raw_inputs:
        item = item.strip().lower().rstrip(".")
        if not item:
            continue
        if "." in item:
            out.append(item)
        elif tlds:
            for t in tlds:
                out.append(f"{item}.{t.lstrip('.')}")
        else:
            out.append(item)  # will fail validation -> reported as invalid
    # De-dupe while preserving order.
    seen = set()
    deduped = []
    for d in out:
        if d not in seen:
            seen.add(d)
            deduped.append(d)
    return deduped


def collect_inputs(args) -> list[str]:
    items: list[str] = list(args.domains or [])
    if args.file:
        with open(args.file) as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if line:
                    items.append(line)
    if args.stdin:
        for line in sys.stdin:
            line = line.split("#", 1)[0].strip()
            if line:
                items.append(line)
    return items


# ── Output ───────────────────────────────────────────────────────────────────

STATUS_SYMBOL = {
    STATUS_AVAILABLE: "✓",
    STATUS_TAKEN: "✗",
    STATUS_AFTERMARKET: "$",
    STATUS_EXPIRING: "~",
    STATUS_UNKNOWN: "?",
    STATUS_INVALID: "!",
    STATUS_RESERVED: "·",
}


def render_table(results: list[dict], use_color: bool) -> str:
    if not results:
        return "(no domains)\n"
    headers = ["", "domain", "status", "method", "evidence", "ms"]
    rows = []
    for r in results:
        sym = STATUS_SYMBOL.get(r["status"], "?")
        rows.append([
            sym,
            r["domain"],
            r["status"],
            r.get("method", ""),
            (r.get("evidence", "") or "")[:80],
            str(r.get("elapsed_ms", 0)),
        ])

    widths = [max(len(headers[i]), max(len(row[i]) for row in rows)) for i in range(len(headers))]
    def line(cells):
        return "  ".join(c.ljust(w) for c, w in zip(cells, widths))

    def colorize(s: str, status: str) -> str:
        if not use_color:
            return s
        code = {
            STATUS_AVAILABLE: "\033[32m",   # green
            STATUS_TAKEN: "\033[31m",       # red
            STATUS_AFTERMARKET: "\033[33m", # yellow — bought, but for sale
            STATUS_EXPIRING: "\033[35m",    # magenta — may drop soon
            STATUS_UNKNOWN: "\033[33m",     # yellow
            STATUS_INVALID: "\033[35m",     # magenta
            STATUS_RESERVED: "\033[36m",    # cyan
        }.get(status, "")
        return f"{code}{s}\033[0m" if code else s

    out = [line(headers), line(["-" * w for w in widths])]
    for row, r in zip(rows, results):
        out.append(colorize(line(row), r["status"]))
    return "\n".join(out) + "\n"


def render_csv(results: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(
        buf, fieldnames=["domain", "status", "method", "evidence", "elapsed_ms"]
    )
    w.writeheader()
    for r in results:
        w.writerow({k: r.get(k, "") for k in w.fieldnames})
    return buf.getvalue()


def render_json(results: list[dict]) -> str:
    return json.dumps(results, indent=2) + "\n"


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="check_domains.py",
        description="Bulk domain availability checker (RDAP + WHOIS + DNS).",
    )
    p.add_argument("domains", nargs="*", help="Domains or bare names (use --tlds for bare names).")
    p.add_argument("-f", "--file", help="Read domains from file (one per line, # comments).")
    p.add_argument("--stdin", action="store_true", help="Read domains from stdin.")
    p.add_argument(
        "--tlds",
        default="",
        help="Comma-separated TLDs to append to bare names (e.g. 'com,net,io').",
    )
    p.add_argument(
        "-m", "--method",
        default="auto",
        help="Check methods: auto (rdap then whois), rdap, whois, dns, or comma list.",
    )
    p.add_argument("-c", "--concurrency", type=int, default=10, help="Parallel workers (default 10).")
    p.add_argument("-t", "--timeout", type=float, default=8.0, help="Per-request timeout seconds.")
    p.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default table).",
    )
    p.add_argument("--only-available", action="store_true", help="Output only available domains.")
    p.add_argument("--only-taken", action="store_true",
                   help="Output only taken/aftermarket/expiring domains.")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors in table output.")
    p.add_argument("--no-aftermarket-detect", action="store_true",
                   help="Disable RDAP entity/NS analysis (faster, less accurate).")
    p.add_argument("--no-premium-hint", action="store_true",
                   help="Disable premium-tier warning on short available names.")
    p.add_argument("--probe-sale", action="store_true",
                   help="HTTP-probe taken domains for 'for sale' landing pages (~1s/domain).")
    p.add_argument("--exit-code", action="store_true",
                   help="Exit non-zero if any UNKNOWN/INVALID result.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    raw = collect_inputs(args)
    if not raw:
        print("error: no domains provided (use positional args, --file, or --stdin)", file=sys.stderr)
        return 2

    tlds = [t.strip() for t in args.tlds.split(",") if t.strip()] if args.tlds else []
    domains = expand_domains(raw, tlds)
    if not domains:
        print("error: no domains to check after expansion", file=sys.stderr)
        return 2

    try:
        bootstrap = load_rdap_bootstrap(timeout=args.timeout)
    except Exception as e:
        print(f"warning: RDAP bootstrap unavailable ({e}); falling back to WHOIS/DNS only",
              file=sys.stderr)
        bootstrap = {"services": []}

    results: list[dict] = []
    with cf.ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as ex:
        futs = {
            ex.submit(
                check_one,
                d,
                args.method,
                bootstrap,
                args.timeout,
                detect_aftermarket=not args.no_aftermarket_detect,
                hint_premium=not args.no_premium_hint,
                probe_sale=args.probe_sale,
            ): d
            for d in domains
        }
        for fut in cf.as_completed(futs):
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({
                    "domain": futs[fut],
                    "status": STATUS_UNKNOWN,
                    "method": "",
                    "evidence": f"worker error: {e}",
                    "elapsed_ms": 0,
                })

    # Preserve input order in output.
    order = {d: i for i, d in enumerate(domains)}
    results.sort(key=lambda r: order.get(r["domain"], 1 << 30))

    if args.only_available:
        results = [r for r in results if r["status"] == STATUS_AVAILABLE]
    elif args.only_taken:
        results = [
            r for r in results
            if r["status"] in (STATUS_TAKEN, STATUS_AFTERMARKET, STATUS_EXPIRING)
        ]

    use_color = (not args.no_color) and sys.stdout.isatty()
    if args.format == "json":
        sys.stdout.write(render_json(results))
    elif args.format == "csv":
        sys.stdout.write(render_csv(results))
    else:
        sys.stdout.write(render_table(results, use_color))

    if args.exit_code:
        bad = any(r["status"] in (STATUS_UNKNOWN, STATUS_INVALID) for r in results)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
