---
name: trailofbits-security
description: Security-focused static analysis and code auditing skills from Trail of Bits. Includes CodeQL deep analysis, Semgrep scanning, and SARIF result processing. Use when performing security audits, running static analysis, scanning for vulnerabilities, or processing scan results.
metadata:
  author: Trail of Bits
  source: https://github.com/trailofbits/skills
  version: "1.0"
---

# Trail of Bits Security Skills

Security-focused static analysis and code auditing toolkit from Trail of Bits.

## Available Sub-Skills

| Skill | File | Use When |
|-------|------|----------|
| CodeQL Analysis | [codeql-SKILL.md](codeql-SKILL.md) | Deep interprocedural taint tracking, data flow analysis |
| Semgrep Scanning | [semgrep-SKILL.md](semgrep-SKILL.md) | Fast pattern-based security scanning with parallel execution |
| SARIF Parsing | [sarif-parsing-SKILL.md](sarif-parsing-SKILL.md) | Processing and aggregating static analysis results |

## When to Use

- **Security audit** of a codebase -> Start with Semgrep for speed, then CodeQL for depth
- **Quick vulnerability scan** -> Semgrep with "important only" mode
- **Deep data flow analysis** -> CodeQL with custom data extensions
- **Processing scan results** -> SARIF parsing for aggregation, deduplication, CI/CD integration

## Workflow

1. Run Semgrep for fast initial scan (pattern-based)
2. Run CodeQL for deep interprocedural analysis (data flow + taint tracking)
3. Use SARIF parsing to aggregate, deduplicate, and prioritize findings
4. Review and triage results by severity

## Source

From [trailofbits/skills](https://github.com/trailofbits/skills) - the `static-analysis` plugin.
