#!/usr/bin/env python3
"""
Data format converter: CSV <-> JSON <-> YAML <-> TOML <-> XML (bidirectional).

Usage:
    python3 csv_json_yaml.py input.csv output.json
    python3 csv_json_yaml.py input.json output.yaml
    python3 csv_json_yaml.py input.yaml output.csv
    python3 csv_json_yaml.py input.toml output.json
    python3 csv_json_yaml.py input.json output.xml
    python3 csv_json_yaml.py *.csv --output-dir ./json --format json

Requirements:
    pip install pyyaml (YAML support)
    Python 3.11+ for TOML read (tomllib), pip install tomli for 3.10-
    pip install dicttoxml (XML write), pip install xmltodict (XML read)
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# YAML support
YAML_AVAILABLE = False
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    pass

# TOML support
TOML_READ = False
TOML_WRITE = False
try:
    import tomllib
    TOML_READ = True
except ImportError:
    try:
        import tomli as tomllib
        TOML_READ = True
    except ImportError:
        pass

try:
    import tomli_w
    TOML_WRITE = True
except ImportError:
    pass

# XML support
XML_READ = False
XML_WRITE = False
try:
    import xmltodict
    XML_READ = True
except ImportError:
    pass
try:
    from dicttoxml import dicttoxml
    XML_WRITE = True
except ImportError:
    pass


def read_csv(path):
    """Read CSV -> list of dicts."""
    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def read_json(path):
    """Read JSON -> data (list or dict)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {path}: {e}")
        sys.exit(1)


def read_yaml(path):
    """Read YAML -> data."""
    if not YAML_AVAILABLE:
        print("Error: pyyaml required for YAML. Install: pip install pyyaml")
        sys.exit(1)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: invalid YAML in {path}: {e}")
        sys.exit(1)


def read_toml(path):
    """Read TOML -> data."""
    if not TOML_READ:
        print("Error: TOML read requires Python 3.11+ or: pip install tomli")
        sys.exit(1)
    with open(path, 'rb') as f:
        return tomllib.load(f)


def read_xml(path):
    """Read XML -> data."""
    if not XML_READ:
        print("Error: xmltodict required for XML read. Install: pip install xmltodict")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return xmltodict.parse(f.read())


def write_csv(data, path):
    """Write list of dicts -> CSV. Unions all keys across rows."""
    if not data:
        path.write_text('', encoding='utf-8')
        return

    if isinstance(data, dict):
        data = [data]

    # Union all keys in stable order
    seen = {}
    for row in data:
        for key in row:
            if key not in seen:
                seen[key] = True
    fieldnames = list(seen.keys())

    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)


def write_json(data, path):
    """Write data -> JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def write_yaml(data, path):
    """Write data -> YAML."""
    if not YAML_AVAILABLE:
        print("Error: pyyaml required for YAML. Install: pip install pyyaml")
        sys.exit(1)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def write_toml(data, path):
    """Write data -> TOML."""
    if not TOML_WRITE:
        print("Error: tomli_w required for TOML write. Install: pip install tomli-w")
        sys.exit(1)
    with open(path, 'wb') as f:
        tomli_w.dump(data, f)


def write_xml(data, path):
    """Write data -> XML."""
    if not XML_WRITE:
        print("Error: dicttoxml required for XML write. Install: pip install dicttoxml")
        sys.exit(1)
    xml_bytes = dicttoxml(data, custom_root='root', attr_type=False)
    from xml.dom.minidom import parseString
    pretty = parseString(xml_bytes).toprettyxml(indent='  ')
    path.write_text(pretty, encoding='utf-8')


READERS = {
    '.csv': read_csv,
    '.json': read_json,
    '.yaml': read_yaml,
    '.yml': read_yaml,
    '.toml': read_toml,
    '.xml': read_xml,
}

WRITERS = {
    '.csv': write_csv,
    '.json': write_json,
    '.yaml': write_yaml,
    '.yml': write_yaml,
    '.toml': write_toml,
    '.xml': write_xml,
}


def convert_file(input_path, output_path):
    """Convert between data formats."""
    in_ext = input_path.suffix.lower()
    out_ext = output_path.suffix.lower()

    reader = READERS.get(in_ext)
    writer = WRITERS.get(out_ext)

    if not reader:
        print(f"Error: unsupported input format: {in_ext}. Supported: {', '.join(sorted(READERS.keys()))}")
        sys.exit(1)
    if not writer:
        print(f"Error: unsupported output format: {out_ext}. Supported: {', '.join(sorted(WRITERS.keys()))}")
        sys.exit(1)

    data = reader(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer(data, output_path)

    in_size = input_path.stat().st_size
    out_size = output_path.stat().st_size
    print(f"  {input_path.name} -> {output_path.name}  ({in_size:,}B -> {out_size:,}B)")


def resolve_data_files(paths):
    """Resolve paths to data files."""
    exts = set(READERS.keys())
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for ext in exts:
                files.extend(path.glob(f'*{ext}'))
        elif path.is_file() and path.suffix.lower() in exts:
            files.append(path)
    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser(description='Convert CSV/JSON/YAML/TOML/XML')
    parser.add_argument('input', nargs='+', help='Input file(s) or directory')
    parser.add_argument('output', nargs='?', help='Output file (single mode)')
    parser.add_argument('--output-dir', '-d', help='Output dir (batch mode)')
    parser.add_argument('--format', '-f',
                        choices=['csv', 'json', 'yaml', 'yml', 'toml', 'xml'],
                        help='Output format (batch)')
    args = parser.parse_args()

    # Batch mode
    if args.output_dir:
        files = resolve_data_files(args.input)
        if not files:
            print("No data files found.")
            sys.exit(1)

        fmt = args.format or 'json'
        if not fmt.startswith('.'):
            fmt = f'.{fmt}'

        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Converting {len(files)} file(s) -> {out_dir}/ as {fmt}")

        for f in files:
            out_path = out_dir / f"{f.stem}{fmt}"
            try:
                convert_file(f, out_path)
            except KeyboardInterrupt:
                print("\nAborted.")
                sys.exit(130)
            except Exception as e:
                print(f"  Error: {f.name}: {e}")
        print("Done.")
        return

    # Single mode
    if not args.output:
        if len(args.input) >= 2:
            args.output = args.input.pop()
        else:
            print("Error: provide output file or use --output-dir for batch mode")
            sys.exit(1)

    input_path = Path(args.input[0])
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    convert_file(input_path, output_path)
    print("Done.")


if __name__ == '__main__':
    main()
