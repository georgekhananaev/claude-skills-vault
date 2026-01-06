#!/usr/bin/env python3
"""Scan project for documentation and map topics to file locations.

Usage:
    python3 scan_docs.py [project-path]
    python3 scan_docs.py .
    python3 scan_docs.py /path/to/project --json
    python3 scan_docs.py /path/to/project --verbose
"""

import argparse
import json
import os
from pathlib import Path
from typing import Optional


# Topic categories and their associated paths/patterns
TOPIC_PATTERNS = {
    "overview": {
        "paths": ["README.md", "readme.md", "README.rst", "docs/README.md", "docs/readme.md"],
        "dirs": [],
    },
    "architecture": {
        "paths": ["ARCHITECTURE.md", "architecture.md", "docs/architecture.md", "docs/ARCHITECTURE.md"],
        "dirs": ["docs/architecture", "docs/design", "architecture"],
    },
    "adr": {
        "paths": [],
        "dirs": ["docs/adr", "docs/decisions", "architecture/decisions", "adr"],
    },
    "features": {
        "paths": [],
        "dirs": ["docs/features", "docs/specs", "docs/specifications", "specs"],
    },
    "api": {
        "paths": ["openapi.yaml", "openapi.json", "swagger.yaml", "swagger.json"],
        "dirs": ["docs/api", "api-docs", "docs/endpoints"],
    },
    "setup": {
        "paths": ["INSTALL.md", "SETUP.md", "docs/setup.md", "docs/installation.md"],
        "dirs": ["docs/guides", "docs/getting-started"],
    },
    "database": {
        "paths": ["prisma/schema.prisma", "schema.sql"],
        "dirs": ["docs/database", "docs/schema", "docs/models"],
    },
    "types": {
        "paths": ["docs/types.md", "docs/models.md"],
        "dirs": ["docs/types", "docs/models", "src/types", "src/models"],
    },
    "style": {
        "paths": [
            "docs/style-guide.md", "docs/conventions.md", "STYLE.md",
            ".eslintrc", ".eslintrc.js", ".eslintrc.json",
            ".prettierrc", ".prettierrc.js", ".prettierrc.json",
            "pyproject.toml", ".flake8", "setup.cfg"
        ],
        "dirs": ["docs/style"],
    },
    "config": {
        "paths": [".env.example", "docs/environment.md", "docs/config.md"],
        "dirs": ["docs/config", "docs/environment"],
    },
    "testing": {
        "paths": ["tests/README.md", "docs/testing.md"],
        "dirs": ["docs/testing", "docs/tests"],
    },
    "deployment": {
        "paths": ["docs/deployment.md", "DEPLOY.md"],
        "dirs": ["docs/deployment", "docs/infrastructure", "docs/ops", "deploy"],
    },
    "contributing": {
        "paths": ["CONTRIBUTING.md", "contributing.md", ".github/CONTRIBUTING.md"],
        "dirs": [],
    },
    "changelog": {
        "paths": ["CHANGELOG.md", "changelog.md", "HISTORY.md", "NEWS.md"],
        "dirs": [],
    },
}

# Primary doc directories to check
DOC_DIRECTORIES = ["docs", "doc", "documentation", ".github/docs"]


def find_doc_root(project_path: Path) -> Optional[Path]:
    """Find the primary documentation directory."""
    for dir_name in DOC_DIRECTORIES:
        doc_dir = project_path / dir_name
        if doc_dir.is_dir():
            return doc_dir
    return None


def scan_directory(path: Path, depth: int = 0, max_depth: int = 3) -> list:
    """Recursively scan directory for markdown files."""
    results = []
    if depth > max_depth:
        return results

    try:
        for item in path.iterdir():
            if item.name.startswith('.'):
                continue
            if item.is_file() and item.suffix.lower() in ['.md', '.rst', '.txt']:
                results.append(item)
            elif item.is_dir():
                results.extend(scan_directory(item, depth + 1, max_depth))
    except PermissionError:
        pass

    return results


def scan_project(project_path: Path) -> dict:
    """Scan project for documentation and return topic map."""
    results = {
        "doc_root": None,
        "has_docs": False,
        "topics": {},
        "all_docs": [],
        "missing_recommended": [],
    }

    # Find doc root
    doc_root = find_doc_root(project_path)
    if doc_root:
        results["doc_root"] = str(doc_root.relative_to(project_path))
        results["has_docs"] = True

    # Scan for topics
    for topic, patterns in TOPIC_PATTERNS.items():
        found = []

        # Check specific paths
        for path_pattern in patterns["paths"]:
            full_path = project_path / path_pattern
            if full_path.exists():
                found.append(str(full_path.relative_to(project_path)))

        # Check directories
        for dir_pattern in patterns["dirs"]:
            dir_path = project_path / dir_pattern
            if dir_path.is_dir():
                # Add directory itself
                found.append(str(dir_path.relative_to(project_path)) + "/")
                # Add files within
                for f in scan_directory(dir_path, max_depth=2):
                    found.append(str(f.relative_to(project_path)))

        if found:
            results["topics"][topic] = found
            results["has_docs"] = True

    # Scan doc root for all docs
    if doc_root:
        all_docs = scan_directory(doc_root)
        results["all_docs"] = [
            str(f.relative_to(project_path)) for f in all_docs
        ]

    # Also check root for standalone docs
    root_docs = [
        f for f in project_path.iterdir()
        if f.is_file() and f.suffix.lower() == '.md'
    ]
    for doc in root_docs:
        rel_path = str(doc.relative_to(project_path))
        if rel_path not in results["all_docs"]:
            results["all_docs"].append(rel_path)

    # Sort all_docs
    results["all_docs"] = sorted(results["all_docs"])

    # Check for recommended but missing docs
    recommended = ["overview", "architecture", "contributing"]
    for topic in recommended:
        if topic not in results["topics"]:
            results["missing_recommended"].append(topic)

    return results


def print_results(results: dict, verbose: bool = False) -> None:
    """Print scan results in human-readable format."""
    if not results["has_docs"]:
        print("❌ No documentation structure found")
        print("\nRecommended: Create docs/ directory with:")
        print("  - README.md (index)")
        print("  - architecture.md")
        print("  - style-guide.md")
        print("\nRun: python3 scripts/init_docs.py to scaffold")
        return

    print(f"✅ Documentation found")
    if results["doc_root"]:
        print(f"   Root: {results['doc_root']}/")
    print()

    # Print topics
    print("📚 Topics Mapped:")
    for topic, paths in sorted(results["topics"].items()):
        print(f"\n  {topic}:")
        for path in paths[:5]:  # Limit to 5 per topic
            print(f"    → {path}")
        if len(paths) > 5:
            print(f"    ... and {len(paths) - 5} more")

    # Missing recommendations
    if results["missing_recommended"]:
        print(f"\n⚠️  Missing recommended docs:")
        for topic in results["missing_recommended"]:
            print(f"    - {topic}")

    # Verbose: show all docs
    if verbose and results["all_docs"]:
        print(f"\n📄 All documentation files ({len(results['all_docs'])}):")
        for doc in results["all_docs"]:
            print(f"    {doc}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan project for documentation structure"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project path to scan (default: current directory)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all documentation files"
    )

    args = parser.parse_args()
    project_path = Path(args.path).resolve()

    if not project_path.is_dir():
        print(f"Error: {project_path} is not a directory")
        return 1

    results = scan_project(project_path)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results, verbose=args.verbose)

    return 0 if results["has_docs"] else 1


if __name__ == "__main__":
    exit(main())
