#!/usr/bin/env python3
"""
JSON <-> TOON Converter (Fallback)

Basic Python implementation when Node.js is not available.
For full spec compliance, use the Node.js version with @toon-format/toon.

Usage:
    python convert.py input.json              # JSON to TOON
    python convert.py --to-json input.toon    # TOON to JSON
    python convert.py --verify input.json     # Verify round-trip
"""

import sys
import json
import re
from pathlib import Path
from typing import Any


def json_to_toon(data: Any, indent: int = 0) -> str:
    """Convert JSON data to TOON format."""
    lines = []
    prefix = "  " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(json_to_toon(value, indent + 1))
            elif isinstance(value, list):
                lines.append(_format_array(key, value, indent))
            else:
                lines.append(f"{prefix}{key}: {_format_value(value)}")

    return '\n'.join(filter(None, lines))


def _format_array(key: str, arr: list, indent: int) -> str:
    prefix = "  " * indent
    row_prefix = "  " * (indent + 1)

    if not arr:
        return f"{prefix}{key}[0]:"

    if all(isinstance(item, dict) for item in arr):
        first_keys = set(arr[0].keys())
        if all(set(item.keys()) == first_keys for item in arr) and first_keys:
            fields = list(arr[0].keys())
            lines = [f"{prefix}{key}[{len(arr)}]{{{','.join(fields)}}}:"]
            for item in arr:
                values = [_format_value(item.get(f)) for f in fields]
                lines.append(f"{row_prefix}{','.join(values)}")
            return '\n'.join(lines)

    if all(isinstance(item, (str, int, float, bool, type(None))) for item in arr):
        values = [_format_value(v) for v in arr]
        return f"{prefix}{key}[{len(arr)}]: {','.join(values)}"

    lines = [f"{prefix}{key}:"]
    for item in arr:
        lines.append(f"{row_prefix}- {json_to_toon(item, indent + 2).lstrip()}")
    return '\n'.join(lines)


def _format_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if ',' in value or '\n' in value:
            return f'"{value.replace(chr(34), chr(92)+chr(34))}"'
        return value
    return str(value)


def toon_to_json(content: str) -> Any:
    lines = content.split('\n')
    result, _ = _parse_block(lines, 0, 0)
    return result


def _parse_block(lines, start, base_indent):
    result = {}
    i = start

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent < base_indent:
            break
        if current_indent > base_indent and i > start:
            break

        stripped = line.strip()

        match = re.match(r'^(\w+)\[(\d+)\]\{([^}]+)\}:\s*$', stripped)
        if match:
            name, _, fields_str = match.groups()
            fields = fields_str.split(',')
            arr = []
            i += 1
            while i < len(lines) and lines[i].strip():
                row_indent = len(lines[i]) - len(lines[i].lstrip())
                if row_indent <= base_indent:
                    break
                values = _parse_csv(lines[i].strip())
                arr.append(dict(zip(fields, [_parse_scalar(v) for v in values])))
                i += 1
            result[name] = arr
            continue

        match = re.match(r'^(\w+)\[(\d+)\]:\s*(.+)$', stripped)
        if match:
            name, _, values_str = match.groups()
            result[name] = [_parse_scalar(v) for v in _parse_csv(values_str)]
            i += 1
            continue

        match = re.match(r'^(\w+):\s*(.*)$', stripped)
        if match:
            name, value = match.groups()
            if value:
                result[name] = _parse_scalar(value)
                i += 1
            else:
                i += 1
                nested, i = _parse_block(lines, i, base_indent + 2)
                result[name] = nested
            continue

        i += 1

    return result, i


def _parse_csv(content):
    values, current, in_quotes = [], "", False
    for char in content:
        if char == '"':
            in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            values.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        values.append(current.strip())
    return values


def _parse_scalar(value):
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value == "null":
        return None
    if value in ("true", "false"):
        return value == "true"
    try:
        return float(value) if '.' in value else int(value)
    except ValueError:
        return value


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Convert JSON <-> TOON (fallback)')
    parser.add_argument('file', nargs='?')
    parser.add_argument('-o', '--output')
    parser.add_argument('--to-json', action='store_true')
    parser.add_argument('--verify', action='store_true')

    args = parser.parse_args()
    content = Path(args.file).read_text() if args.file else sys.stdin.read()

    if args.to_json:
        output = json.dumps(toon_to_json(content), indent=2)
    else:
        data = json.loads(content)
        if args.verify:
            toon_str = json_to_toon(data)
            recovered = toon_to_json(toon_str)
            print("Round-trip successful" if data == recovered else "Round-trip mismatch")
            sys.exit(0 if data == recovered else 1)
        output = json_to_toon(data)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()