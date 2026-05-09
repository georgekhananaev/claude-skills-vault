#!/usr/bin/env python3
"""Diff two workflow JSON snapshots — see what changed.

Pure local. Inputs are JSON files (e.g. from `export_workflows.py`).

Usage:
  # Diff two exports of the same workflow
  python3 compare_workflows.py old.json new.json

  # Markdown output
  python3 compare_workflows.py old.json new.json --markdown > diff.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# n8n updates these fields on every save — they're noise for diff purposes.
NOISY_FIELDS = {
    "versionId", "updatedAt", "createdAt", "webhookId",
    "triggerCount", "shared", "homeProject", "scopes",
    "isArchived", "pinData",
}


def strip_noise(wf: dict) -> dict:
    """Remove fields that update on every save, even w/o real changes."""
    out = {k: v for k, v in wf.items() if k not in NOISY_FIELDS}
    # Also strip from nested nodes
    if "nodes" in out and isinstance(out["nodes"], list):
        out["nodes"] = [
            {k: v for k, v in n.items() if k not in NOISY_FIELDS}
            if isinstance(n, dict) else n
            for n in out["nodes"]
        ]
    return out


def load_wf(path: Path, include_noise: bool = False) -> dict:
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)
    wf = json.loads(path.read_text())
    return wf if include_noise else strip_noise(wf)


def diff_dicts(a: dict, b: dict, prefix: str = "") -> list[tuple[str, str, object, object]]:
    """Recursively compare two dicts. Yields (kind, path, a_val, b_val).
    kind: 'added' | 'removed' | 'changed'.
    """
    changes: list[tuple[str, str, object, object]] = []
    a_keys = set(a.keys())
    b_keys = set(b.keys())
    for k in a_keys - b_keys:
        changes.append(("removed", f"{prefix}{k}", a[k], None))
    for k in b_keys - a_keys:
        changes.append(("added", f"{prefix}{k}", None, b[k]))
    for k in a_keys & b_keys:
        av, bv = a[k], b[k]
        if isinstance(av, dict) and isinstance(bv, dict):
            changes.extend(diff_dicts(av, bv, prefix=f"{prefix}{k}."))
        elif isinstance(av, list) and isinstance(bv, list):
            if av != bv:
                changes.append(("changed", f"{prefix}{k}", f"<list len={len(av)}>", f"<list len={len(bv)}>"))
        elif av != bv:
            changes.append(("changed", f"{prefix}{k}", av, bv))
    return changes


def diff_workflows(a: dict, b: dict) -> dict:
    out: dict = {
        "name_changed": a.get("name") != b.get("name"),
        "old_name": a.get("name"),
        "new_name": b.get("name"),
    }

    # Nodes diff (keyed by node name)
    a_nodes = {n.get("name"): n for n in (a.get("nodes") or [])}
    b_nodes = {n.get("name"): n for n in (b.get("nodes") or [])}
    out["nodes_added"] = sorted(set(b_nodes) - set(a_nodes))
    out["nodes_removed"] = sorted(set(a_nodes) - set(b_nodes))
    out["nodes_changed"] = []
    for name in sorted(set(a_nodes) & set(b_nodes)):
        if a_nodes[name] != b_nodes[name]:
            out["nodes_changed"].append(name)

    # Connection topology diff (count per source)
    def conn_summary(c: dict) -> dict:
        if not isinstance(c, dict):
            return {}
        return {src: sum(len(v) for v in dests if isinstance(v, list))
                for src, dests in c.items() if isinstance(dests, dict)}
    a_conn = conn_summary(a.get("connections") or {})
    b_conn = conn_summary(b.get("connections") or {})
    out["connection_changes"] = {
        k: (a_conn.get(k, 0), b_conn.get(k, 0))
        for k in set(a_conn) | set(b_conn)
        if a_conn.get(k, 0) != b_conn.get(k, 0)
    }

    # Settings diff
    out["settings_diff"] = diff_dicts(
        a.get("settings") or {}, b.get("settings") or {}, prefix="settings."
    )
    return out


def render(diff: dict, markdown: bool) -> str:
    lines = []
    h = "## " if markdown else "--- "
    if diff["name_changed"]:
        lines.append(f"{h}Name changed")
        lines.append(f"  - {diff['old_name']!r} → {diff['new_name']!r}")
    if diff["nodes_added"]:
        lines.append(f"\n{h}Nodes added ({len(diff['nodes_added'])})")
        for n in diff["nodes_added"]:
            lines.append(f"  + {n}")
    if diff["nodes_removed"]:
        lines.append(f"\n{h}Nodes removed ({len(diff['nodes_removed'])})")
        for n in diff["nodes_removed"]:
            lines.append(f"  - {n}")
    if diff["nodes_changed"]:
        lines.append(f"\n{h}Nodes changed ({len(diff['nodes_changed'])})")
        for n in diff["nodes_changed"]:
            lines.append(f"  ~ {n}")
    if diff["connection_changes"]:
        lines.append(f"\n{h}Connections changed")
        for src, (a, b) in diff["connection_changes"].items():
            lines.append(f"  ~ {src}: {a} → {b} outbound")
    if diff["settings_diff"]:
        lines.append(f"\n{h}Settings changed")
        for kind, key, a_val, b_val in diff["settings_diff"]:
            if kind == "added":
                lines.append(f"  + {key} = {b_val!r}")
            elif kind == "removed":
                lines.append(f"  - {key} (was {a_val!r})")
            else:
                lines.append(f"  ~ {key}: {a_val!r} → {b_val!r}")
    if not any([diff["nodes_added"], diff["nodes_removed"], diff["nodes_changed"],
                diff["connection_changes"], diff["settings_diff"], diff["name_changed"]]):
        lines.append("(identical)")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff two workflow JSON snapshots")
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--include-noise", action="store_true",
                        help=f"Include noisy fields {sorted(NOISY_FIELDS)} (default: stripped)")
    args = parser.parse_args()

    a = load_wf(args.old, include_noise=args.include_noise)
    b = load_wf(args.new, include_noise=args.include_noise)
    diff = diff_workflows(a, b)

    if args.json:
        print(json.dumps(diff, indent=2, default=str))
    else:
        if args.markdown:
            print(f"# Workflow Diff\n")
            print(f"_old_: `{args.old}`  ")
            print(f"_new_: `{args.new}`\n")
        print(render(diff, args.markdown))
    return 0


if __name__ == "__main__":
    sys.exit(main())
