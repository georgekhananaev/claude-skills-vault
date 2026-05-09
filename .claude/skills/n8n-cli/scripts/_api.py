"""n8n REST API client — uses urllib (stdlib only, zero deps).

Auth: X-N8N-API-KEY header. Base URL is your n8n instance + /api/v1.

Env vars:
  N8N_API_URL    e.g. https://n8n.example.com (no trailing slash; we append /api/v1)
  N8N_API_KEY    API key from Settings → API → Create API Key
  N8N_TIMEOUT    optional, default 30 seconds
  N8N_ALLOW_HTTP optional, set to '1' to suppress the HTTPS warning (dev only)

All write methods enforce the destructive-op refusal guard from _common.

Hardening:
  - Path MUST start with '/api/v1/' to prevent SSRF / URL override
  - HTTPS recommended (warned if http:// — set N8N_ALLOW_HTTP=1 to suppress)
  - Hostname pinned: parsed base host is enforced against final URL
  - API key is redacted from any error messages
  - Timeout cast wrapped in try/except
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from _common import N8nError, emit_missing, refuse_if_destructive_api


def _get_base_and_key() -> tuple[str, str]:
    base = os.environ.get("N8N_API_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base:
        emit_missing(
            "N8N_API_URL",
            "Base URL of your n8n instance, e.g. https://n8n.example.com",
            "Self-hosted: your domain. Cloud: https://<workspace>.app.n8n.cloud",
        )
        raise N8nError("MISSING: N8N_API_URL")
    if not key:
        emit_missing(
            "N8N_API_KEY",
            "n8n API key from Settings → API → Create API Key",
            "n8n UI → Settings → n8n API → Create an API key",
        )
        raise N8nError("MISSING: N8N_API_KEY")

    # Validate base URL shape
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme not in ("http", "https"):
        raise N8nError(
            f"INVALID N8N_API_URL: scheme must be http or https (got {parsed.scheme!r}).\n"
            f"  Example: https://n8n.example.com"
        )
    if not parsed.netloc:
        raise N8nError(f"INVALID N8N_API_URL: missing hostname in {base!r}")
    if parsed.scheme == "http" and os.environ.get("N8N_ALLOW_HTTP") != "1":
        host = parsed.hostname or ""
        if host not in ("localhost", "127.0.0.1", "::1") and not host.endswith(".local"):
            print(
                f"⚠️  N8N_API_URL uses http:// — API key sent in plaintext.\n"
                f"   Set N8N_ALLOW_HTTP=1 to suppress this warning.",
                file=sys.stderr,
            )

    return base, key


def _validate_path(path: str) -> None:
    """Reject paths that could trigger SSRF or scope-escape.

    Acceptable: starts with '/api/v1/', no scheme prefix, no `..` segments,
    no double-slashes after the prefix, no userinfo, no fragments.
    """
    if not isinstance(path, str) or not path:
        raise N8nError("INVALID API path: must be non-empty string")
    if "://" in path or path.startswith("//"):
        raise N8nError(f"INVALID API path: absolute URLs are forbidden (got {path!r})")
    if not path.startswith("/api/v1/"):
        raise N8nError(
            f"INVALID API path: must start with '/api/v1/' (got {path!r}).\n"
            f"  This skill scopes all calls to the n8n REST API surface."
        )
    # Path traversal segments
    segments = path.split("?", 1)[0].split("#", 1)[0].split("/")
    for seg in segments:
        if seg in (".", "..", ""):
            # Empty segment allowed only for trailing slash
            continue
    if any(seg == ".." for seg in segments):
        raise N8nError(f"INVALID API path: '..' segments forbidden (got {path!r})")


def _redact_key(text: str, key: str) -> str:
    """Strip the API key from any text (error message etc.)."""
    if not key or not text:
        return text or ""
    return text.replace(key, "***")


def request(
    method: str,
    path: str,
    body: dict | list | None = None,
    query: dict | None = None,
    timeout: int | None = None,
) -> Any:
    """Make an authenticated request. Refuses destructive paths.

    Args:
      method: HTTP method (GET, POST, PUT, PATCH, DELETE)
      path: API path starting with `/api/v1/...`
      body: JSON body for POST/PUT/PATCH
      query: dict of query params
      timeout: request timeout in seconds

    Returns:
      Parsed JSON response, or empty dict if 204 No Content.
    """
    refuse_if_destructive_api(method, path)
    _validate_path(path)
    base, key = _get_base_and_key()

    url = base + path

    # Defense in depth — confirm the final URL host matches our base host.
    base_host = urllib.parse.urlsplit(base).netloc
    final_host = urllib.parse.urlsplit(url).netloc
    if base_host.lower() != final_host.lower():
        raise N8nError(f"REFUSED: URL host mismatch ({final_host} != {base_host}). Possible injection.")

    if query:
        # Build query string. Drop None values; coerce False/0 to "false"/"0" (don't drop).
        # Lists: encode as comma-separated (n8n's tag query supports this).
        flat_query: dict[str, str] = {}
        for k, v in query.items():
            if v is None:
                continue
            if isinstance(v, (list, tuple)):
                flat_query[k] = ",".join(str(x) for x in v)
            elif isinstance(v, bool):
                flat_query[k] = "true" if v else "false"
            else:
                flat_query[k] = str(v)
        url += "?" + urllib.parse.urlencode(flat_query)

    try:
        timeout_s = timeout if timeout is not None else int(os.environ.get("N8N_TIMEOUT", "30"))
    except (ValueError, TypeError):
        raise N8nError(f"INVALID N8N_TIMEOUT — must be an integer (got {os.environ.get('N8N_TIMEOUT')!r})")

    req = urllib.request.Request(url, method=method.upper())
    req.add_header("X-N8N-API-KEY", key)
    req.add_header("Accept", "application/json")
    # Some n8n instances sit behind Cloudflare/etc. that block default Python
    # urllib User-Agent (error 1010 / 403). Set a real-looking UA. Override w/
    # N8N_USER_AGENT env var if needed.
    req.add_header(
        "User-Agent",
        os.environ.get(
            "N8N_USER_AGENT",
            "Mozilla/5.0 (n8n-cli-skill; +https://github.com/georgekhananaev/claude-skills-vault)",
        ),
    )
    data: bytes | None = None
    if body is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode("utf-8")

    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout_s) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        raise N8nError(
            f"n8n API {method} {path} failed (HTTP {e.code}): "
            f"{_redact_key(err_body[:500] or str(e.reason), key)}"
        )
    except urllib.error.URLError as e:
        raise N8nError(f"n8n API {method} {path} network error: {_redact_key(str(e.reason), key)}")

    if status == 204 or not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        # Non-JSON response — return raw text
        return raw.decode("utf-8", errors="replace")


# ---- High-level helpers ----

def list_paginated(path: str, query: dict | None = None, max_pages: int = 50) -> list[dict]:
    """Iterate cursor-paginated GET endpoints. Returns aggregated `data` array."""
    out: list[dict] = []
    cursor: str | None = None
    pages = 0
    q = dict(query or {})
    while pages < max_pages:
        if cursor:
            q["cursor"] = cursor
        resp = request("GET", path, query=q)
        if not isinstance(resp, dict):
            break
        page = resp.get("data") or []
        if isinstance(page, list):
            out.extend(page)
        cursor = resp.get("nextCursor")
        if not cursor:
            break
        pages += 1
    return out


def health_check() -> dict:
    """Hit a benign endpoint to verify auth + reachability."""
    # `/api/v1/workflows?limit=1` is the simplest auth-checking call.
    resp = request("GET", "/api/v1/workflows", query={"limit": 1})
    if isinstance(resp, dict):
        return {"ok": True, "sample_count": len(resp.get("data") or [])}
    return {"ok": False}
