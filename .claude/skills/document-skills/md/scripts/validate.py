#!/usr/bin/env python3
"""
Markdown Validator
Checks markdown files for common issues that cause IDE errors.

Usage:
    python validate.py <file.md>
    python validate.py <directory>

Requirements:
    pip install mistune
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Any

# Try to use mistune for parsing, fallback to basic regex
HAS_MISTUNE = False
_mistune: Any = None

try:
    import mistune as _mistune_module
    _mistune = _mistune_module
    HAS_MISTUNE = True
except ImportError:
    print("Note: Install 'mistune' for better validation: pip install mistune", file=sys.stderr)


@dataclass
class Issue:
    line: int
    column: int
    severity: str  # error, warning, info
    code: str
    message: str
    suggestion: Optional[str] = None


class MarkdownValidator:
    def __init__(self, content: str, filename: str = ""):
        self.content = content
        self.lines = content.split('\n')
        self.filename = filename
        self.issues: list[Issue] = []

    def validate(self) -> list[Issue]:
        """Run all validation checks."""
        self.check_unclosed_code_blocks()
        self.check_heading_syntax()
        self.check_list_indentation()
        self.check_table_columns()
        self.check_link_syntax()
        self.check_unclosed_html()
        self.check_trailing_spaces()

        if HAS_MISTUNE:
            self.check_with_parser()

        return self.issues

    def check_with_parser(self):
        """Use mistune parser to detect issues."""
        if not HAS_MISTUNE or _mistune is None:
            return
        try:
            md = _mistune.create_markdown()
            md(self.content)
        except Exception as e:
            self.issues.append(Issue(
                line=1,
                column=1,
                severity="error",
                code="MD010",
                message=f"Parser error: {e}",
                suggestion="Check markdown syntax"
            ))

    def check_unclosed_code_blocks(self):
        """Check for unclosed code fences."""
        fence_stack: list[tuple[str, int, int]] = []
        fence_pattern = re.compile(r'^(\s*)(```+|~~~+)(\w*)?')

        for i, line in enumerate(self.lines, 1):
            match = fence_pattern.match(line)
            if match:
                fence = match.group(2)
                fence_char = fence[0]
                fence_len = len(fence)

                if fence_stack and fence_stack[-1][0] == fence_char and fence_stack[-1][1] <= fence_len:
                    fence_stack.pop()
                else:
                    fence_stack.append((fence_char, fence_len, i))

        for fence_char, fence_len, line_num in fence_stack:
            self.issues.append(Issue(
                line=line_num,
                column=1,
                severity="error",
                code="MD001",
                message=f"Unclosed code block (opened with {fence_char * fence_len})",
                suggestion=f"Add closing {fence_char * fence_len} fence"
            ))

    def check_heading_syntax(self):
        """Check heading syntax - no space after #."""
        heading_pattern = re.compile(r'^(#{1,6})([^ #\n])')
        in_code_block = False

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            match = heading_pattern.match(line)
            if match:
                self.issues.append(Issue(
                    line=i,
                    column=len(match.group(1)) + 1,
                    severity="warning",
                    code="MD003",
                    message="No space after heading hashes",
                    suggestion=f"Add space: {match.group(1)} {match.group(2)}..."
                ))

    def check_list_indentation(self):
        """Check for inconsistent list indentation."""
        list_pattern = re.compile(r'^(\s*)([-*+]|\d+\.)\s')
        prev_indent = 0
        prev_line_was_list = False
        in_code_block = False

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            match = list_pattern.match(line)
            if match:
                indent = len(match.group(1))
                if prev_line_was_list and indent > 0:
                    if indent % 2 != 0 and indent != prev_indent + 2:
                        self.issues.append(Issue(
                            line=i,
                            column=1,
                            severity="warning",
                            code="MD004",
                            message=f"Inconsistent list indentation ({indent} spaces)",
                            suggestion="Use 2 or 4 space indentation consistently"
                        ))
                prev_indent = indent
                prev_line_was_list = True
            elif line.strip():
                prev_line_was_list = False

    def check_table_columns(self):
        """Check table column consistency."""
        table_pattern = re.compile(r'^\|.*\|$')
        in_table = False
        in_code_block = False
        expected_cols = 0

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            if table_pattern.match(stripped):
                # Count unescaped pipes
                clean_line = line.replace(r'\|', 'X')
                cols = clean_line.count('|') - 1
                if not in_table:
                    in_table = True
                    expected_cols = cols
                elif cols != expected_cols:
                    self.issues.append(Issue(
                        line=i,
                        column=1,
                        severity="error",
                        code="MD005",
                        message=f"Table column mismatch: expected {expected_cols}, got {cols}",
                        suggestion="Ensure all rows have same number of columns"
                    ))
            elif in_table and stripped:
                in_table = False

    def check_link_syntax(self):
        """Check for malformed links."""
        in_code_block = False

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Check for space between ] and ( using string search
            if '] (' in line or ']\t(' in line:
                self.issues.append(Issue(
                    line=i,
                    column=1,
                    severity="error",
                    code="MD006",
                    message="Space between ] and ( in link",
                    suggestion="Remove space: [text](url)"
                ))

            # Check for unclosed link: [text](url without closing )
            # Simple heuristic: has ]( but line doesn't end with ) and no ) after (
            if '](' in line:
                idx = line.find('](')
                after_paren = line[idx + 2:]
                if '(' in after_paren and ')' not in after_paren:
                    self.issues.append(Issue(
                        line=i,
                        column=1,
                        severity="error",
                        code="MD006",
                        message="Unclosed link parenthesis",
                        suggestion="Add closing )"
                    ))

    def check_unclosed_html(self):
        """Check for unclosed HTML tags."""
        html_tags = ['details', 'summary', 'div', 'span', 'table', 'pre']
        in_code_block = False

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            for tag in html_tags:
                open_pattern = re.compile(rf'<{tag}(?:\s[^>]*)?>(?!.*</{tag}>)', re.IGNORECASE)
                if open_pattern.search(line):
                    # Check if closed later
                    remaining = '\n'.join(self.lines[i:])
                    if f'</{tag}>' not in remaining.lower():
                        self.issues.append(Issue(
                            line=i,
                            column=1,
                            severity="warning",
                            code="MD007",
                            message=f"Potentially unclosed <{tag}> tag",
                            suggestion=f"Add closing </{tag}> tag"
                        ))

    def check_trailing_spaces(self):
        """Check for trailing whitespace."""
        in_code_block = False

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Single trailing space (not intentional line break which is 2 spaces)
            if line.endswith(' ') and not line.endswith('  '):
                self.issues.append(Issue(
                    line=i,
                    column=len(line),
                    severity="info",
                    code="MD008",
                    message="Trailing whitespace",
                    suggestion="Remove trailing space"
                ))


def format_issue(issue: Issue, filename: str = "") -> str:
    """Format issue for console output."""
    prefix = f"{filename}:" if filename else ""
    colors = {"error": "\033[91m", "warning": "\033[93m", "info": "\033[94m"}
    reset = "\033[0m"
    color = colors.get(issue.severity, "")

    msg = f"{prefix}{issue.line}:{issue.column}: {color}{issue.severity}{reset} [{issue.code}] {issue.message}"
    if issue.suggestion:
        msg += f"\n    Suggestion: {issue.suggestion}"
    return msg


def validate_file(filepath: Path) -> list[Issue]:
    """Validate a markdown file."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return [Issue(0, 0, "error", "MD000", f"Could not read file: {e}")]

    validator = MarkdownValidator(content, str(filepath))
    return validator.validate()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = list(path.rglob("*.md"))
    else:
        print(f"Error: {path} not found")
        sys.exit(1)

    all_issues: list[Issue] = []

    for file in files:
        issues = validate_file(file)
        for issue in issues:
            print(format_issue(issue, str(file)))
        all_issues.extend(issues)

    # Summary
    errors = sum(1 for i in all_issues if i.severity == "error")
    warnings = sum(1 for i in all_issues if i.severity == "warning")
    infos = sum(1 for i in all_issues if i.severity == "info")

    print(f"\n{'='*50}")
    print(f"Files: {len(files)} | Issues: {len(all_issues)} ({errors} errors, {warnings} warnings, {infos} info)")

    sys.exit(1 if errors > 0 else 0)


if __name__ == "__main__":
    main()
