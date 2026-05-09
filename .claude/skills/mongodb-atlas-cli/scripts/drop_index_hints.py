#!/usr/bin/env python3
"""List indexes that Performance Advisor suggests dropping.

READ-ONLY by design. This skill never executes drops — it surfaces the
suggestion so the user can act manually in the Atlas UI.

Wraps `atlas api performanceAdvisor listDropIndexSuggestions`.

Usage:
  python3 drop_index_hints.py --cluster Cluster0
  python3 drop_index_hints.py --cluster Cluster0 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, resolve_project_id, run_atlas  # noqa: E402


def fetch_drop_hints(cluster: str, project_id: str | None) -> dict:
    pid = resolve_project_id(project_id)
    if not pid:
        raise AtlasError(
            "MISSING: project ID — pass --projectId, set MONGODB_ATLAS_PROJECT_ID, "
            "or run `atlas config init` to set it in your profile."
        )
    args = [
        "api", "performanceAdvisor", "listDropIndexSuggestions",
        "--clusterName", cluster,
        "--version", "2024-08-05",
        "--groupId", pid,
    ]
    data = run_atlas(args)
    return data if isinstance(data, dict) else {}


def _format_index_keys(idx_field: list | dict | None) -> str:
    """Render index spec [{field: dir}, ...] or {field: dir} as `{a:1, b:-1}`."""
    if isinstance(idx_field, list):
        parts = []
        for entry in idx_field:
            if isinstance(entry, dict):
                parts.extend(f"{k}:{v}" for k, v in entry.items())
        return "{ " + ", ".join(parts) + " }"
    if isinstance(idx_field, dict):
        return "{ " + ", ".join(f"{k}:{v}" for k, v in idx_field.items()) + " }"
    return str(idx_field or "")


def _format_idx_line(idx: dict) -> str:
    ns = idx.get("namespace", "?")
    name = idx.get("name", "?")
    spec = _format_index_keys(idx.get("index"))
    access = idx.get("accessCount")
    suffix = f"  (accessCount={access})" if access is not None else ""
    return f"  - {ns}: {name} {spec}{suffix}"


def summarize(payload: dict) -> str:
    # API response: {"content": {"hiddenIndexes":[], "redundantIndexes":[], ...}, "status":200}
    body = payload.get("content") if isinstance(payload, dict) else None
    if not isinstance(body, dict):
        body = payload if isinstance(payload, dict) else {}

    hidden = body.get("hiddenIndexes") or []
    redundant = body.get("redundantIndexes") or []
    unused = body.get("unusedIndexes") or []

    if not (hidden or redundant or unused):
        return "No drop suggestions. All indexes appear to be in use."

    lines = ["⚠️  This skill will NOT drop indexes — these are advisory only.\n"]
    if hidden:
        lines.append(f"Hidden indexes ({len(hidden)}) — already invisible to query planner:")
        for idx in hidden[:10]:
            lines.append(_format_idx_line(idx))
    if redundant:
        lines.append(f"\nRedundant indexes ({len(redundant)}) — fully covered by another index:")
        for idx in redundant[:10]:
            lines.append(_format_idx_line(idx))
            related = idx.get("relatedIndexes") or []
            for r in related[:1]:
                lines.append(f"      ↳ covered by: {r.get('name','?')} {_format_index_keys(r.get('index'))}")
    if unused:
        lines.append(f"\nUnused indexes ({len(unused)}) — no recent reads:")
        for idx in unused[:10]:
            lines.append(_format_idx_line(idx))
    lines.append(
        "\nTo drop one (do this YOURSELF, not via this skill):\n"
        "  Atlas UI → Cluster → Collections → Indexes → ⋯ → Drop\n"
        "  OR: mongosh > db.<coll>.dropIndex('<index_name>')"
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Show drop-index suggestions (advisory only)")
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        payload = fetch_drop_hints(args.cluster, args.project_id)
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        emit_human("Drop Index Suggestions (Advisory)", summarize(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
