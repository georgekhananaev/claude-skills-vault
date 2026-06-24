#!/usr/bin/env python3
"""Rotate (archive) old releases out of CHANGELOG.md to keep it small.

A long-lived project accumulates hundreds of release sections in a single
CHANGELOG.md (one real-world file had 197 versions / 2,500+ lines / 420 KB).
This script keeps the main file short by leaving the `[Unreleased]` section
plus the newest N released versions in place and moving everything older into
per-major archive files (e.g. `changelog/CHANGELOG-1.x.md`), then writing an
"Older releases" index into the main file that links to each archive.

Strategy (decided for this skill):
  - keep `[Unreleased]` + newest N versions in CHANGELOG.md (default N=20)
  - archive older versions grouped by SemVer MAJOR -> CHANGELOG-<major>.x.md
  - archives stay newest-first; new archived versions are prepended
  - link every archive from an "Older releases" index in the main file

Safe by default: with no flags it performs a DRY RUN and only prints the plan.
Pass --apply to actually write files. Idempotent: re-running when nothing needs
to move makes no changes.

Edge cases handled:
  - pre-release / letter suffixes:  ## [1.23.0a] - ...,  ## [1.19.6h] - ...
  - hash-instead-of-date headers:   ## [1.19.4] - e850122c
  - re-running after an index/archives already exist
  - versions whose major can't be parsed -> CHANGELOG-misc.md (with a warning)

Python 3 standard library only -- no third-party dependencies.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

# A top-level section starts at a line beginning with "## ".
SECTION_RE = re.compile(r"^##\s")
# A version section:  "## [1.27.0] - 2026-06-25"  -> capture the bracket content.
VERSION_RE = re.compile(r"^##\s*\[(?P<ver>[^\]]+)\]")
# The Unreleased section is kept, never archived.
UNRELEASED_RE = re.compile(r"^##\s*\[unreleased\]", re.IGNORECASE)
# Our generated index section (dropped + regenerated each run).
INDEX_RE = re.compile(r"^##\s+(older releases|archived releases?|archive)\b", re.IGNORECASE)
# Leading numeric major of a version string ("v1.27.0a" -> "1").
MAJOR_RE = re.compile(r"^\s*v?(\d+)")

INDEX_HEADING = "Older releases"
MISC_BUCKET = "misc"  # archive bucket for versions without a numeric major


class Section:
    """One `## ...` block: its raw text plus a classification."""

    __slots__ = ("text", "version", "is_unreleased", "is_index")

    def __init__(self, text: str):
        self.text = text
        self.version = None          # bracket content for version sections
        self.is_unreleased = False
        self.is_index = False
        header = text.splitlines()[0] if text else ""
        if UNRELEASED_RE.match(header):
            self.is_unreleased = True
        elif INDEX_RE.match(header):
            self.is_index = True
        else:
            m = VERSION_RE.match(header)
            if m:
                self.version = m.group("ver").strip()

    @property
    def is_version(self) -> bool:
        return self.version is not None

    @property
    def major(self) -> str:
        m = MAJOR_RE.match(self.version or "")
        return m.group(1) if m else MISC_BUCKET


def parse(text: str):
    """Split changelog text into (preamble, [Section, ...]).

    `preamble` is everything before the first `## ` line (title + intro).
    Section blocks keep their exact original text (including trailing blanks),
    so reassembly is byte-faithful when nothing is changed.
    """
    lines = text.splitlines(keepends=True)
    starts = [i for i, ln in enumerate(lines) if SECTION_RE.match(ln)]
    if not starts:
        return text, []
    preamble = "".join(lines[: starts[0]])
    sections = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        sections.append(Section("".join(lines[start:end])))
    return preamble, sections


def major_sort_key(bucket: str):
    """Sort majors descending numerically; the misc bucket goes last."""
    return (0, -int(bucket)) if bucket.isdigit() else (1, 0)


def archive_filename(bucket: str) -> str:
    return f"CHANGELOG-{bucket}.x.md" if bucket.isdigit() else "CHANGELOG-misc.md"


def rel_link(from_file: str, to_file: str) -> str:
    """POSIX relative markdown link from one file to another."""
    rel = os.path.relpath(to_file, os.path.dirname(os.path.abspath(from_file)))
    return rel.replace(os.sep, "/")


def archive_label(bucket: str) -> str:
    return f"{bucket}.x releases" if bucket.isdigit() else "misc releases"


def build_index(main_file: str, archive_dir: str, buckets) -> str:
    """Build the 'Older releases' index section listing every archive file
    that exists (existing on disk) or will exist (newly created this run)."""
    existing = set()
    if os.path.isdir(archive_dir):
        for name in os.listdir(archive_dir):
            m = re.match(r"^CHANGELOG-(\d+|misc)\.x\.md$|^CHANGELOG-misc\.md$", name)
            if name.startswith("CHANGELOG-") and name.endswith(".md"):
                existing.add(name)
    wanted = {archive_filename(b) for b in buckets} | existing
    if not wanted:
        return ""
    # Recover bucket -> filename for stable, numeric-descending ordering.
    by_bucket = {}
    for name in wanted:
        m = re.match(r"^CHANGELOG-(\d+)\.x\.md$", name)
        by_bucket[m.group(1) if m else MISC_BUCKET] = name
    lines = [f"## {INDEX_HEADING}", ""]
    lines.append(
        "Older releases are archived to keep this file small. "
        "Full history:"
    )
    lines.append("")
    for bucket in sorted(by_bucket, key=major_sort_key):
        name = by_bucket[bucket]
        link = rel_link(main_file, os.path.join(archive_dir, name))
        lines.append(f"- [{archive_label(bucket)}]({link})")
    return "\n".join(lines) + "\n"


def new_archive_preamble(main_file: str, archive_file: str, bucket: str) -> str:
    back = rel_link(archive_file, main_file)
    label = archive_label(bucket).replace(" releases", "")
    return (
        f"# Changelog — {label} archive\n\n"
        f"Older {label} releases, archived from the main "
        f"[CHANGELOG.md]({back}) to keep it small.\n"
        f"The format follows [Keep a Changelog](https://keepachangelog.com/).\n\n"
    )


def prepend_to_archive(main_file, archive_path, bucket, blocks) -> str:
    """Return the new full text for an archive file with `blocks` (newest-first)
    prepended after its preamble. Creates the preamble if the file is new."""
    new_text = "".join(b.text for b in blocks)
    if os.path.exists(archive_path):
        with open(archive_path, "r", encoding="utf-8") as fh:
            existing = fh.read()
        pre, sections = parse(existing)
        if not pre.endswith("\n"):
            pre += "\n"
        rest = "".join(s.text for s in sections)
        return pre + new_text + rest
    return new_archive_preamble(main_file, archive_path, bucket) + new_text


def build_main(preamble, unreleased, kept, index_text) -> str:
    parts = [preamble]
    if unreleased is not None:
        parts.append(unreleased.text)
    parts.extend(s.text for s in kept)
    body = "".join(parts)
    if index_text:
        if not body.endswith("\n"):
            body += "\n"
        if not body.endswith("\n\n"):
            body += "\n"
        body += index_text
    if not body.endswith("\n"):
        body += "\n"
    return body


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Archive old releases out of CHANGELOG.md (dry-run unless --apply).",
    )
    ap.add_argument("--file", default="CHANGELOG.md", help="main changelog (default: CHANGELOG.md)")
    ap.add_argument("--dir", default="changelog", help="archive directory (default: changelog)")
    ap.add_argument("--keep", type=int, default=20, help="versions to keep in main file (default: 20)")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args(argv)

    if args.keep < 0:
        print("error: --keep must be >= 0", file=sys.stderr)
        return 2
    if not os.path.exists(args.file):
        print(f"error: {args.file} not found", file=sys.stderr)
        return 2

    with open(args.file, "r", encoding="utf-8") as fh:
        original = fh.read()

    preamble, sections = parse(original)
    unreleased = next((s for s in sections if s.is_unreleased), None)
    versions = [s for s in sections if s.is_version]
    unknown = [s for s in sections if not s.is_version and not s.is_unreleased and not s.is_index]
    if unknown:
        for s in unknown:
            print(f"warning: keeping unrecognized section: {s.text.splitlines()[0]!r}", file=sys.stderr)

    kept = versions[: args.keep]
    overflow = versions[args.keep :]

    # Unknown sections are preserved (appended after kept versions) so nothing is lost.
    kept_for_main = kept + unknown

    # Group overflow by major, preserving newest-first order within each bucket.
    buckets = {}
    for s in overflow:
        buckets.setdefault(s.major, []).append(s)

    index_text = build_index(args.file, args.dir, buckets.keys())
    new_main = build_main(preamble, unreleased, kept_for_main, index_text)

    main_changed = new_main != original
    if not overflow and not main_changed:
        print(f"Nothing to do: {len(versions)} version(s) <= keep={args.keep}; file already tidy.")
        return 0

    label = "APPLY" if args.apply else "DRY RUN"
    print(f"[{label}] {args.file}: {len(versions)} version(s), keep={args.keep}.")
    if overflow:
        print(f"  archive {len(overflow)} version(s):")
        for bucket in sorted(buckets, key=major_sort_key):
            blocks = buckets[bucket]
            dest = os.path.join(args.dir, archive_filename(bucket))
            newest = blocks[0].version
            oldest = blocks[-1].version
            verb = "create" if not os.path.exists(dest) else "prepend"
            print(f"    {dest}  <- {len(blocks)} version(s) [{newest} … {oldest}] ({verb})")
    else:
        print("  no versions to archive; refreshing 'Older releases' index.")

    if not args.apply:
        print("Run again with --apply to write changes.")
        return 0

    # --- write phase ---
    if overflow:
        os.makedirs(args.dir, exist_ok=True)
        for bucket, blocks in buckets.items():
            dest = os.path.join(args.dir, archive_filename(bucket))
            text = prepend_to_archive(args.file, dest, bucket, blocks)
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(text)
    with open(args.file, "w", encoding="utf-8") as fh:
        fh.write(new_main)

    print(f"Done. {args.file} now keeps {len(kept)} version(s) + [Unreleased].")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
