#!/usr/bin/env python3
"""Initialize minimal documentation structure for a project.

Usage:
    python3 init_docs.py [project-path]
    python3 init_docs.py .
    python3 init_docs.py /path/to/project --force
"""

import argparse
from pathlib import Path
from datetime import datetime


TEMPLATES = {
    "docs/README.md": """# Project Documentation

## Overview

Brief description of what this project does.

## Quick Links

- [Architecture](./architecture.md)
- [Data Types](./types.md)
- [Style Guide](./style-guide.md)
- [Features](./features/)
- [Architecture Decisions](./adr/)

## Getting Started

See the main [README](../README.md) for setup instructions.
""",

    "docs/architecture.md": """# Architecture Overview

## System Context

What this system does and how it fits into the larger ecosystem.

## High-Level Components

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Server    │────▶│  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Key Technologies

- **Frontend**: [framework, libraries]
- **Backend**: [language, framework]
- **Database**: [type, name]
- **Infrastructure**: [hosting, services]

## Directory Structure

```
src/
├── components/    # UI components
├── services/      # Business logic
├── models/        # Data models
└── utils/         # Shared utilities
```

## Data Flow

Describe how data moves through the system.

## External Integrations

List third-party services and their purposes.
""",

    "docs/types.md": """# Data Types Reference

## Core Entities

### [Entity Name]

```typescript
interface Entity {
  id: string;
  // Add fields
}
```

## Enums

| Value | Description |
|-------|-------------|
| | |

## Validation Rules

| Field | Rule |
|-------|------|
| | |
""",

    "docs/style-guide.md": """# Codebase Style Guide

## Naming Conventions

### Files & Directories

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Utilities | camelCase | `formatDate.ts` |
| Constants | SCREAMING_SNAKE | `API_ENDPOINTS.ts` |

### Variables & Functions

| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | `userData` |
| Functions | camelCase | `fetchUser()` |
| Classes | PascalCase | `UserService` |
| Constants | SCREAMING_SNAKE | `MAX_RETRIES` |

## Import Order

1. External packages
2. Internal aliases (@/)
3. Relative imports
4. Type-only imports

## Comment Standards

- Explain WHY, not WHAT
- Use JSDoc for public APIs
""",

    "docs/features/_template.md": """# Feature: [Name]

## Summary

One-line description of what this feature does.

## User Story

As a [user type], I want to [action] so that [benefit].

## Requirements

- [ ] Requirement 1
- [ ] Requirement 2

## Implementation Notes

Key files and components involved:

- `src/components/FeatureName/`
- `src/services/featureService.ts`

## API Endpoints (if applicable)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/... | Fetches... |
| POST | /api/... | Creates... |

## Related

- Link to related features
- Link to relevant ADRs
""",

    "docs/adr/_template.md": """# ADR-[NUMBER]: [Title]

**Date**: {date}
**Status**: Proposed

## Context

What is the issue or decision we need to make?

## Decision

What decision was made?

## Consequences

### Positive

- Benefit 1
- Benefit 2

### Negative

- Tradeoff 1
- Tradeoff 2

## Alternatives Considered

1. **Alternative A**: Why rejected
2. **Alternative B**: Why rejected
""",
}


def init_docs(project_path: Path, force: bool = False) -> None:
    """Initialize documentation structure."""
    docs_dir = project_path / "docs"

    if docs_dir.exists() and not force:
        print(f"⚠️  docs/ already exists at {project_path}")
        print("   Use --force to overwrite templates")
        return

    # Create directories
    (docs_dir / "features").mkdir(parents=True, exist_ok=True)
    (docs_dir / "adr").mkdir(parents=True, exist_ok=True)

    # Create files
    created = []
    skipped = []

    for rel_path, content in TEMPLATES.items():
        full_path = project_path / rel_path

        if full_path.exists() and not force:
            skipped.append(rel_path)
            continue

        # Replace placeholders
        content = content.replace("{date}", datetime.now().strftime("%Y-%m-%d"))

        full_path.write_text(content)
        created.append(rel_path)

    # Report
    print(f"✅ Documentation initialized at {docs_dir}/")
    print()

    if created:
        print("📄 Created:")
        for path in created:
            print(f"   → {path}")

    if skipped:
        print("\n⏭️  Skipped (already exist):")
        for path in skipped:
            print(f"   → {path}")

    print("\nNext steps:")
    print("1. Edit docs/README.md with project overview")
    print("2. Update docs/architecture.md with system design")
    print("3. Document data types in docs/types.md")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize documentation structure"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project path (default: current directory)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing files"
    )

    args = parser.parse_args()
    project_path = Path(args.path).resolve()

    if not project_path.is_dir():
        print(f"Error: {project_path} is not a directory")
        return 1

    init_docs(project_path, args.force)
    return 0


if __name__ == "__main__":
    exit(main())
