"""mongosh-based helpers — invoke mongosh as a subprocess and parse JSON output.

Resolves connection string in this order:
  1. --connection-string CLI arg
  2. MONGODB_CONNECTION_STRING env var
  3. ATLAS_CONNECTION_STRING env var

Password handling: passed via stdin (`--password` w/ no value triggers prompt;
we feed the password through stdin instead of as argv). This avoids exposure
via `/proc/<pid>/cmdline` on Linux. Username is non-secret and passed as flag.

Identifier validation: any database / collection / field name that gets
interpolated into JS is validated by `validate_identifier()` to prevent
script injection (e.g. `users); db.dropDatabase(); //`).

Usage from a script:
    from _mongo import mongosh_eval, validate_identifier
    coll = validate_identifier(args.collection, "collection")
    result = mongosh_eval(f"return db.getCollection({json.dumps(coll)}).getIndexes();")
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Any


class MongoshError(RuntimeError):
    pass


# MongoDB identifier rules:
#   - DB name: any UTF-8 except / \ . " $ NUL space
#   - Collection: similar; "system.*" is reserved but allowed in queries
#   - Field name: most chars allowed; we restrict for shell/JS safety
# We pick a CONSERVATIVE allowlist that covers all realistic real names
# while blocking any character that could break out of a JS string literal
# or shell-quote: alphanumerics, underscore, hyphen, dot, plus colon for
# user.id-style nested fields.
_IDENT_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-: ]*$")


def validate_identifier(name: str, kind: str = "name") -> str:
    """Validate a db/collection/field name for safe JS interpolation.

    Returns the name unchanged on success. Raises MongoshError on bad input.
    Blocks: quotes, backslashes, parens, semicolons, slashes, NUL, etc. —
    every char that could break out of a JS string or inject statements.
    """
    if not isinstance(name, str) or not name:
        raise MongoshError(f"INVALID: {kind} must be non-empty string (got {name!r})")
    if len(name) > 128:
        raise MongoshError(f"INVALID: {kind} too long (max 128 chars)")
    if not _IDENT_RE.match(name):
        raise MongoshError(
            f"INVALID: {kind} {name!r} contains unsafe characters.\n"
            f"  Allowed: alphanumerics, underscore, hyphen, dot, colon, space.\n"
            f"  Blocked: quotes, parens, semicolons, slashes, backslashes, etc."
        )
    return name


def _need_mongosh() -> None:
    if not shutil.which("mongosh"):
        raise MongoshError(
            "MISSING: mongosh binary.\n"
            "Install via `brew install mongosh` or it ships w/ `brew install mongodb-atlas`."
        )


def resolve_connection_string(explicit: str | None = None) -> str:
    """Resolve a MongoDB connection URI. Caller passes user/password separately."""
    if explicit:
        return explicit
    for var in ("MONGODB_CONNECTION_STRING", "ATLAS_CONNECTION_STRING", "MONGODB_URI"):
        val = os.environ.get(var)
        if val:
            return val
    raise MongoshError(
        "MISSING: connection string.\n"
        "ASK_USER: pass --connection-string or set MONGODB_CONNECTION_STRING.\n"
        "  Format: mongodb+srv://<host>/?authSource=admin\n"
        "  Get from Atlas UI → Cluster → Connect → Drivers"
    )


def resolve_credentials(
    username: str | None = None, password: str | None = None
) -> tuple[str, str]:
    user = username or os.environ.get("MONGODB_USERNAME") or os.environ.get("MONGODB_USER")
    pw = password or os.environ.get("MONGODB_PASSWORD") or os.environ.get("MONGODB_PW")
    if not user:
        raise MongoshError(
            "MISSING: username.\n"
            "ASK_USER: pass --username or set MONGODB_USERNAME."
        )
    if not pw:
        raise MongoshError(
            "MISSING: password.\n"
            "ASK_USER: pass --password or set MONGODB_PASSWORD."
        )
    return user, pw


def mongosh_eval(
    js: str,
    connection_string: str | None = None,
    username: str | None = None,
    password: str | None = None,
    db: str | None = None,
    timeout: int = 60,
    return_json: bool = True,
) -> Any:
    """Run mongosh w/ --eval and return the result.

    The JS is wrapped to print the result as JSON (via EJSON.stringify) so
    we can parse it cleanly. If return_json=False, raw stdout is returned.
    """
    _need_mongosh()
    cs = resolve_connection_string(connection_string)
    user, pw = resolve_credentials(username, password)

    if db:
        # Append db to URI path if not already present
        if "?" in cs:
            base, _, query = cs.partition("?")
            base = base.rstrip("/") + f"/{db}"
            cs = f"{base}?{query}"
        else:
            cs = cs.rstrip("/") + f"/{db}"

    if return_json:
        wrapped = (
            "(() => {"
            f"  const __r = (function(){{ {js} }})();"
            "  print(EJSON.stringify(__r, null, 0, { relaxed: true }));"
            "})()"
        )
    else:
        wrapped = js

    # Pass password via stdin (`--password` w/ no value triggers stdin read in mongosh)
    # rather than as argv — avoids /proc/<pid>/cmdline exposure on Linux.
    cmd = [
        "mongosh", cs,
        "--quiet",
        "--username", user,
        "--password",  # no value — mongosh will read from stdin/tty
        "--authenticationDatabase", "admin",
        "--eval", wrapped,
    ]

    try:
        proc = subprocess.run(
            cmd, input=pw + "\n",
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise MongoshError(f"mongosh timed out after {timeout}s")

    if proc.returncode != 0:
        # Strip the password from stderr if echoed
        stderr = (proc.stderr or "").replace(pw, "***") if pw else (proc.stderr or "")
        # Strip the prompt that appears w/ stdin password
        stderr = stderr.replace("Enter password:", "").strip()
        raise MongoshError(f"mongosh failed (exit {proc.returncode}):\n{stderr}")

    out = (proc.stdout or "").strip()
    if not return_json:
        return out

    # mongosh w/ --quiet may still emit auth warnings; find the last JSON line
    json_text = out
    # Strip lines that aren't JSON-ish
    candidates = [ln for ln in out.splitlines() if ln.strip().startswith(("{", "[", '"', "null"))]
    if candidates:
        json_text = candidates[-1]
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return out  # fall back to raw text
