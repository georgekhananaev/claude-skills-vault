#!/usr/bin/env python3
"""Create an Atlas index — gated, dry-run by default.

Wraps `atlas clusters indexes create`. The ONLY mutating op this skill performs.

Safety gates:
  1. Default = dry-run: prints exact command, never executes
  2. Requires explicit --confirm to execute
  3. Validates key spec (field:1 / field:-1 / field:text / field:2dsphere / hashed)
  4. Refuses if ANY destructive token appears in args (defense-in-depth)
  5. Pre-flight DUPLICATE CHECK — warns if an existing index covers the same keys
     (requires mongosh credentials; skipped if creds aren't available)
  6. Prints reminder that index builds use cluster resources

Optional flags:
  --unique             # enforce unique constraint
  --ttl-seconds N      # TTL index (mongo will auto-delete docs after N seconds past indexed date)
  --partial-filter F   # JSON file w/ partialFilterExpression

Examples:
  # Dry-run
  python3 safe_index_create.py --cluster Cluster0 --db app --collection users \\
      --key email:1

  # Execute w/ unique
  python3 safe_index_create.py --cluster Cluster0 --db app --collection users \\
      --key email:1 --unique --name email_unique --confirm

  # TTL on a sessions collection
  python3 safe_index_create.py --cluster Cluster0 --db app --collection sessions \\
      --key created_at:1 --ttl-seconds 86400 --name sessions_ttl --confirm

  # Partial filter (only index active users)
  echo '{"active": true}' > /tmp/pf.json
  python3 safe_index_create.py --cluster Cluster0 --db app --collection users \\
      --key email:1 --partial-filter /tmp/pf.json --confirm
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, refuse_if_destructive, run_atlas  # noqa: E402

VALID_DIRECTIONS = {"1", "-1", "text", "2dsphere", "2d", "hashed", "geoHaystack"}


def validate_key(key: str) -> tuple[str, str]:
    if ":" not in key:
        raise AtlasError(f"--key must be `field:type` (got: {key!r})")
    field, _, direction = key.rpartition(":")
    if not field:
        raise AtlasError(f"--key has empty field name (got: {key!r})")
    if direction not in VALID_DIRECTIONS:
        raise AtlasError(
            f"--key direction must be one of {sorted(VALID_DIRECTIONS)} (got: {direction!r})"
        )
    if any(c in field for c in '"\'$\x00'):
        raise AtlasError(f"--key field has unsafe chars (got: {field!r})")
    return field, direction


def keys_to_dict(keys: list[str]) -> dict:
    """Render --key flags as a plain {field: direction} dict (with str directions)."""
    out: dict[str, str | int] = {}
    for k in keys:
        f, d = validate_key(k)
        out[f] = int(d) if d in {"1", "-1"} else d
    return out


def _index_options(idx: dict) -> dict:
    """Extract option fields from an existing index doc for equivalence check."""
    return {
        "unique": bool(idx.get("unique", False)),
        "sparse": bool(idx.get("sparse", False)),
        "expireAfterSeconds": idx.get("expireAfterSeconds"),
        "partialFilterExpression": idx.get("partialFilterExpression"),
        "collation": idx.get("collation"),
    }


def keys_match_existing(
    proposed: dict, existing: list[dict],
    proposed_opts: dict | None = None,
) -> dict | None:
    """Return existing index w/ identical keys AND identical options, else None.

    `proposed_opts` should be the dict-form of {unique, sparse, expireAfterSeconds,
    partialFilterExpression, collation}. If None, only keys are compared (legacy).
    """
    p_keys = tuple(proposed.items())
    for e in existing:
        ek = e.get("key") or {}
        if not (isinstance(ek, dict) and tuple(ek.items()) == p_keys):
            continue
        if proposed_opts is None:
            return e
        if _index_options(e) == proposed_opts:
            return e
    return None


def keys_prefix_of(prefix: dict, full: dict) -> bool:
    """True if `prefix` keys (in order) are a strict prefix of `full`."""
    p = list(prefix.items())
    f = list(full.items())
    if len(p) >= len(f):
        return False
    return p == f[: len(p)]


def existing_covering(proposed: dict, existing: list[dict]) -> dict | None:
    """Find an existing index whose key prefix == proposed keys (covers it)."""
    for e in existing:
        ek = e.get("key") or {}
        if isinstance(ek, dict) and keys_prefix_of(proposed, ek):
            return e
    return None


def fetch_existing_indexes(db: str, coll: str) -> list[dict] | None:
    """Try to fetch existing indexes via mongosh. Returns None if creds missing.

    Distinguishes "creds missing" (skip pre-flight quietly) from real errors
    (network failure, auth fail, etc.) by checking the MongoshError message.
    """
    try:
        from _mongo import MongoshError, mongosh_eval, validate_identifier
    except ImportError:
        return None
    try:
        validate_identifier(db, "database")
        validate_identifier(coll, "collection")
        coll_q = json.dumps(coll)
        return mongosh_eval(f"return db.getCollection({coll_q}).getIndexes();", db=db)
    except MongoshError as e:
        msg = str(e)
        # "MISSING:" indicates env var not set — pre-flight is optional, skip.
        # Anything else (auth fail, network error, mongosh missing) — surface it.
        if msg.startswith("MISSING:"):
            return None
        raise AtlasError(f"pre-flight probe failed: {msg}")


def build_command(
    cluster: str, db: str, collection: str, keys: list[str],
    name: str | None, sparse: bool, unique: bool, ttl_seconds: int | None,
    partial_filter_path: str | None, project_id: str | None,
    file_path: str | None = None,
) -> tuple[list[str], str | None]:
    """Returns (cli args, optional temp-file path to clean up).

    Modes:
      * --file <path>  — user-supplied JSON (for wildcard, collation, etc.). All
        other options are ignored; the JSON is authoritative.
      * Generated --file (when unique/ttl/partial requested) — we synthesize the
        JSON config because Atlas CLI's flag surface doesn't cover those options.
      * Simple flag form — for plain b-tree / 2dsphere / hashed / sparse indexes.
    """
    if file_path:
        # User supplied a complete index definition file.
        args = ["clusters", "indexes", "create",
                "--clusterName", cluster, "--file", file_path]
        if project_id:
            args += ["--projectId", project_id]
        if name:
            args += [name]
        return args, None

    use_file = unique or ttl_seconds is not None or partial_filter_path is not None

    if use_file:
        cfg: dict = {"db": db, "collection": collection, "options": {}, "keys": []}
        for k in keys:
            f, d = validate_key(k)
            cfg["keys"].append({f: int(d) if d in {"1", "-1"} else d})
        if name:
            cfg["options"]["name"] = name
        if unique:
            cfg["options"]["unique"] = True
        if sparse:
            cfg["options"]["sparse"] = True
        if ttl_seconds is not None:
            cfg["options"]["expireAfterSeconds"] = ttl_seconds
        if partial_filter_path:
            cfg["options"]["partialFilterExpression"] = json.loads(Path(partial_filter_path).read_text())

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(cfg, tmp)
        tmp.close()
        args = ["clusters", "indexes", "create",
                "--clusterName", cluster, "--file", tmp.name]
        if project_id:
            args += ["--projectId", project_id]
        return args, tmp.name

    # Simple flag-based form for the common case
    args = ["clusters", "indexes", "create",
            "--clusterName", cluster, "--db", db, "--collection", collection]
    for k in keys:
        validate_key(k)
        args += ["--key", k]
    if sparse:
        args += ["--sparse"]
    if project_id:
        args += ["--projectId", project_id]
    if name:
        args += [name]
    return args, None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely create an Atlas index (dry-run by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--db")
    parser.add_argument("--collection")
    parser.add_argument("--key", action="append",
                        help="Index key spec `field:type`. Repeatable. type ∈ {1,-1,text,2dsphere,hashed}. "
                             "Required unless --file is used.")
    parser.add_argument("--name")
    parser.add_argument("--sparse", action="store_true")
    parser.add_argument("--unique", action="store_true")
    parser.add_argument("--ttl-seconds", type=int, dest="ttl_seconds",
                        help="Make this a TTL index (auto-expire docs after N sec from indexed date field)")
    parser.add_argument("--partial-filter", dest="partial_filter",
                        help="Path to JSON w/ partialFilterExpression (e.g. {\"active\": true})")
    parser.add_argument("--file", dest="file",
                        help="Path to JSON w/ full index definition — for wildcard, collation, etc. "
                             "Mutually exclusive w/ --key/--db/--collection (file is authoritative).")
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--skip-preflight", action="store_true",
                        help="Skip duplicate-index check (requires mongosh creds otherwise — silently skipped if missing)")
    parser.add_argument("--print-mongosh", action="store_true",
                        help="Print the equivalent mongosh createIndex() snippet (use for local mongo) and exit")
    parser.add_argument("--confirm", action="store_true", help="EXECUTE (without this, dry-run only)")
    args = parser.parse_args()

    # Validate --file exclusivity & required-arg presence
    if args.file:
        if args.key or args.db or args.collection:
            print("ERROR: --file is mutually exclusive w/ --key/--db/--collection.", file=sys.stderr)
            return 1
        if not Path(args.file).exists():
            print(f"ERROR: file not found: {args.file}", file=sys.stderr)
            return 1
    else:
        missing = [a for a in ("db", "collection", "key") if not getattr(args, a)]
        if missing:
            print(f"ERROR: missing required args: {', '.join('--' + m for m in missing)} "
                  f"(or use --file <path>)", file=sys.stderr)
            return 1

    # If user just wants the mongosh snippet (e.g. for self-hosted local mongo), print and exit
    if args.print_mongosh:
        if args.file:
            print("ERROR: --print-mongosh doesn't support --file (use mongosh directly w/ the JSON)", file=sys.stderr)
            return 1
        proposed_dict = keys_to_dict(args.key)
        # Quote every field name as JSON to handle dots/dashes/spaces safely
        key_pairs = ", ".join(f"{json.dumps(k)}: {json.dumps(v)}" for k, v in proposed_dict.items())
        keys_js = "{ " + key_pairs + " }"
        opts: dict = {}
        if args.name: opts["name"] = args.name
        if args.unique: opts["unique"] = True
        if args.sparse: opts["sparse"] = True
        if args.ttl_seconds is not None: opts["expireAfterSeconds"] = args.ttl_seconds
        if args.partial_filter:
            opts["partialFilterExpression"] = json.loads(Path(args.partial_filter).read_text())
        opts["background"] = True
        opts_js = json.dumps(opts)
        # Quote db & collection names too — handles dots/dashes/spaces
        print(f'use({json.dumps(args.db)});')
        print(f'db.getCollection({json.dumps(args.collection)}).createIndex({keys_js}, {opts_js});')
        return 0

    # Pre-flight: check for existing duplicates (only in flag-mode, not --file mode)
    proposed_dict = keys_to_dict(args.key) if args.key else {}
    proposed_opts = {
        "unique": args.unique,
        "sparse": args.sparse,
        "expireAfterSeconds": args.ttl_seconds,
        "partialFilterExpression": (json.loads(Path(args.partial_filter).read_text())
                                    if args.partial_filter else None),
        "collation": None,
    } if not args.file else None

    if not args.skip_preflight and args.db and args.collection and proposed_dict:
        try:
            existing = fetch_existing_indexes(args.db, args.collection)
        except AtlasError as e:
            existing = None
            print(f"NOTE: pre-flight skipped — {e}", file=sys.stderr)

        if existing is not None:
            dup = keys_match_existing(proposed_dict, existing, proposed_opts)
            if dup:
                print(f"⚠️  DUPLICATE: an index w/ identical keys AND options already exists:", file=sys.stderr)
                print(f"     name:    {dup.get('name')}", file=sys.stderr)
                print(f"     keys:    {dup.get('key')}", file=sys.stderr)
                print(f"     options: unique={_index_options(dup)['unique']}, sparse={_index_options(dup)['sparse']}, "
                      f"ttl={_index_options(dup)['expireAfterSeconds']}", file=sys.stderr)
                if not args.confirm:
                    print("\n[DRY RUN] Won't proceed because index would be duplicate.", file=sys.stderr)
                    return 2
                print("\nERROR: refusing to create duplicate index even w/ --confirm.", file=sys.stderr)
                return 2
            # Same keys, different options → warn but don't block
            same_keys = keys_match_existing(proposed_dict, existing, None)
            if same_keys and same_keys is not dup:
                print(f"ℹ️  NOTE: existing index `{same_keys.get('name')}` has same keys but DIFFERENT options.", file=sys.stderr)
                print(f"     existing options: {_index_options(same_keys)}", file=sys.stderr)
                print(f"     proposed options: {proposed_opts}", file=sys.stderr)
                print(f"     This will create a SECOND index — confirm that's intended.", file=sys.stderr)
                print(file=sys.stderr)
            cov = existing_covering(proposed_dict, existing)
            if cov:
                print(f"⚠️  REDUNDANT: an existing compound index already covers your proposed keys as a prefix:", file=sys.stderr)
                print(f"     name: {cov.get('name')}", file=sys.stderr)
                print(f"     keys: {cov.get('key')}", file=sys.stderr)
                print(f"     Your proposed index would be redundant. Consider skipping it.", file=sys.stderr)
                print(f"     Use --skip-preflight to override (NOT recommended).", file=sys.stderr)
                if args.confirm:
                    print("\nABORTING execution. Re-run w/ --skip-preflight if you really want this.", file=sys.stderr)
                    return 3
                print(file=sys.stderr)

    cmd_args, tmp_path = build_command(
        cluster=args.cluster,
        db=args.db or "", collection=args.collection or "",
        keys=args.key or [],
        name=args.name, sparse=args.sparse, unique=args.unique, ttl_seconds=args.ttl_seconds,
        partial_filter_path=args.partial_filter, project_id=args.project_id,
        file_path=args.file,
    )

    try:
        refuse_if_destructive(cmd_args)
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    rendered = "atlas " + " ".join(shlex.quote(a) for a in cmd_args)
    print("Planned command:", file=sys.stderr)
    print(f"  {rendered}", file=sys.stderr)
    print(file=sys.stderr)
    print("Index spec:", file=sys.stderr)
    print(f"  keys:    {proposed_dict}", file=sys.stderr)
    if args.unique: print("  unique:  yes", file=sys.stderr)
    if args.sparse: print("  sparse:  yes", file=sys.stderr)
    if args.ttl_seconds is not None: print(f"  TTL:     {args.ttl_seconds}s", file=sys.stderr)
    if args.partial_filter: print(f"  partial: {args.partial_filter}", file=sys.stderr)
    if args.name:   print(f"  name:    {args.name}", file=sys.stderr)
    print(file=sys.stderr)
    print("Pre-flight notes:", file=sys.stderr)
    print("  • Atlas builds rolling indexes — uses replica set capacity during build.", file=sys.stderr)
    print("  • Build time scales w/ collection size. Monitor cluster CPU/IOPS during.", file=sys.stderr)
    print("  • This is ADDITIVE — won't drop or modify existing indexes.", file=sys.stderr)
    print("  • To roll back, drop manually in Atlas UI (this skill won't drop).", file=sys.stderr)

    try:
        if not args.confirm:
            print("\n[DRY RUN] Add --confirm to execute.", file=sys.stderr)
            return 0

        print("\nExecuting…", file=sys.stderr)
        result = run_atlas(cmd_args, json_out=False)
        print(result)
        print("\n✓ Index creation submitted. Build runs asynchronously.", file=sys.stderr)
        print(f"  Verify w/: python3 list_indexes.py --db {args.db} --collection {args.collection}", file=sys.stderr)
    except AtlasError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
