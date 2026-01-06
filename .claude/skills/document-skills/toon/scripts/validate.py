#!/usr/bin/env python3
"""
TOON Format Validator

Validates TOON syntax and structure:
- Array length declarations [N] match actual row count
- Field count {a,b,c} matches values per row
- Proper indentation structure
- Quote balance in strings

Usage:
    python validate.py input.toon
    python validate.py --json input.json  # validate JSON before conversion
    cat data.toon | python validate.py
"""

import sys
import re
import json
from pathlib import Path
from typing import NamedTuple


class ValidationError(NamedTuple):
    line: int
    message: str
    severity: str  # 'error' | 'warning'


class ToonValidator:
    def __init__(self):
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []

    def validate(self, content: str) -> bool:
        """Validate TOON content. Returns True if valid."""
        self.errors = []
        self.warnings = []
        lines = content.split('\n')

        self._check_array_declarations(lines)
        self._check_indentation(lines)
        self._check_quotes(lines)
        self._check_empty_values(lines)

        return len(self.errors) == 0

    def _check_array_declarations(self, lines: list[str]) -> None:
        """Verify [N]{fields} declarations match actual data."""
        i = 0
        while i < len(lines):
            line = lines[i]

            # Match array declaration: name[N]{field1,field2,...}:
            match = re.match(r'^(\s*)(\w+)\[(\d+)\]\{([^}]+)\}:\s*$', line)
            if match:
                indent = match.group(1)
                name = match.group(2)
                declared_count = int(match.group(3))
                fields = match.group(4).split(',')
                field_count = len(fields)

                # Count actual rows
                actual_rows = 0
                row_start = i + 1

                while row_start < len(lines):
                    row_line = lines[row_start]

                    # Empty line or less/equal indentation = end of array
                    if not row_line.strip():
                        break

                    row_indent = len(row_line) - len(row_line.lstrip())
                    base_indent = len(indent)

                    if row_indent <= base_indent and row_line.strip():
                        break

                    # Check field count in row
                    row_content = row_line.strip()
                    if row_content:
                        row_values = self._parse_csv_values(row_content)
                        if len(row_values) != field_count:
                            self.errors.append(ValidationError(
                                row_start + 1,
                                f"Row has {len(row_values)} values, expected {field_count} ({','.join(fields)})",
                                'error'
                            ))
                        actual_rows += 1

                    row_start += 1

                # Check declared vs actual count
                if actual_rows != declared_count:
                    self.errors.append(ValidationError(
                        i + 1,
                        f"Array '{name}' declares [{declared_count}] but has {actual_rows} rows",
                        'error'
                    ))

            # Match scalar array: name[N]: val1,val2,...
            scalar_match = re.match(r'^(\s*)(\w+)\[(\d+)\]:\s*(.+)$', line)
            if scalar_match and not match:
                name = scalar_match.group(2)
                declared_count = int(scalar_match.group(3))
                values_str = scalar_match.group(4)
                values = self._parse_csv_values(values_str)

                if len(values) != declared_count:
                    self.errors.append(ValidationError(
                        i + 1,
                        f"Scalar array '{name}' declares [{declared_count}] but has {len(values)} values",
                        'error'
                    ))

            i += 1

    def _parse_csv_values(self, content: str) -> list[str]:
        """Parse CSV values respecting quotes."""
        values = []
        current = ""
        in_quotes = False
        quote_char = None

        for char in content:
            if char in '"\'':
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                current += char
            elif char == ',' and not in_quotes:
                values.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            values.append(current.strip())

        return values

    def _check_indentation(self, lines: list[str]) -> None:
        """Check for consistent indentation."""
        indent_sizes = set()

        for i, line in enumerate(lines):
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip())
            if indent > 0:
                indent_sizes.add(indent)

        # Check for mixed indent sizes (allow 2 and 4, warn on others)
        odd_indents = [s for s in indent_sizes if s % 2 != 0]
        if odd_indents:
            self.warnings.append(ValidationError(
                0,
                f"Inconsistent indentation detected: {sorted(indent_sizes)}. Use 2 or 4 spaces.",
                'warning'
            ))

    def _check_quotes(self, lines: list[str]) -> None:
        """Check for unbalanced quotes."""
        for i, line in enumerate(lines):
            double_quotes = line.count('"')
            single_quotes = line.count("'")

            if double_quotes % 2 != 0:
                self.errors.append(ValidationError(
                    i + 1,
                    "Unbalanced double quotes",
                    'error'
                ))

            if single_quotes % 2 != 0:
                self.warnings.append(ValidationError(
                    i + 1,
                    "Unbalanced single quotes (may be apostrophe)",
                    'warning'
                ))

    def _check_empty_values(self, lines: list[str]) -> None:
        """Warn about potentially problematic empty values."""
        for i, line in enumerate(lines):
            if ',,' in line:
                self.warnings.append(ValidationError(
                    i + 1,
                    "Empty value detected (,,). Use 'null' for explicit null values.",
                    'warning'
                ))

    def format_results(self) -> str:
        """Format validation results for display."""
        output = []

        if not self.errors and not self.warnings:
            return "✓ Valid TOON format"

        for err in self.errors:
            output.append(f"ERROR line {err.line}: {err.message}")

        for warn in self.warnings:
            if warn.line > 0:
                output.append(f"WARNING line {warn.line}: {warn.message}")
            else:
                output.append(f"WARNING: {warn.message}")

        summary = f"\n{len(self.errors)} error(s), {len(self.warnings)} warning(s)"
        output.append(summary)

        return '\n'.join(output)


def validate_json_for_toon(content: str) -> list[str]:
    """Check if JSON is suitable for TOON conversion."""
    issues = []

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    def check_structure(obj, path="root"):
        if isinstance(obj, list) and len(obj) > 0:
            if all(isinstance(item, dict) for item in obj):
                # Check uniform fields
                first_keys = set(obj[0].keys())
                for i, item in enumerate(obj[1:], 1):
                    if set(item.keys()) != first_keys:
                        issues.append(
                            f"{path}[{i}]: Fields differ from first item. "
                            f"Missing: {first_keys - set(item.keys())}, "
                            f"Extra: {set(item.keys()) - first_keys}"
                        )
            for i, item in enumerate(obj):
                check_structure(item, f"{path}[{i}]")
        elif isinstance(obj, dict):
            for key, value in obj.items():
                check_structure(value, f"{path}.{key}")

    check_structure(data)
    return issues


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Validate TOON format')
    parser.add_argument('file', nargs='?', help='TOON file to validate')
    parser.add_argument('--json', action='store_true',
                       help='Validate JSON for TOON compatibility')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Only show errors, not warnings')

    args = parser.parse_args()

    # Read input
    if args.file:
        content = Path(args.file).read_text()
    else:
        content = sys.stdin.read()

    if args.json:
        issues = validate_json_for_toon(content)
        if issues:
            print("JSON compatibility issues for TOON:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("✓ JSON is compatible with TOON format")
            sys.exit(0)

    validator = ToonValidator()
    is_valid = validator.validate(content)

    if args.quiet:
        validator.warnings = []

    print(validator.format_results())
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()