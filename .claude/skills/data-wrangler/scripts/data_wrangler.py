#!/usr/bin/env python3
"""
data_wrangler.py — Production-grade tabular data manipulation engine.

Supports: CSV, Excel (xlsx/xls), JSON, Parquet, TSV
Operations: read, write, inspect, filter, sort, group, merge, pivot, dedupe,
            fill, drop, rename, cast, derive, sample, split, validate, formula

Usage:
    python3 data_wrangler.py <operation> <input> [options]

Examples:
    python3 data_wrangler.py inspect data.csv
    python3 data_wrangler.py filter data.xlsx --where "Age > 30" -o filtered.xlsx
    python3 data_wrangler.py sort data.csv --by Revenue --desc -o sorted.csv
    python3 data_wrangler.py group data.csv --by Department --agg "Salary:mean,count"
    python3 data_wrangler.py merge left.csv right.csv --on ID --how left -o merged.csv
    python3 data_wrangler.py pivot data.csv --index Name --columns Month --values Sales
    python3 data_wrangler.py dedupe data.csv --subset "Email" -o clean.csv
    python3 data_wrangler.py fill data.csv --column Revenue --strategy mean -o filled.csv
    python3 data_wrangler.py drop data.csv --columns "Temp,Notes" -o trimmed.csv
    python3 data_wrangler.py rename data.csv --map "old_name:new_name,col2:Col2" -o renamed.csv
    python3 data_wrangler.py cast data.csv --column Date --dtype datetime -o typed.csv
    python3 data_wrangler.py derive data.csv --formula "Profit = Revenue - Cost" -o enriched.csv
    python3 data_wrangler.py sample data.csv --n 100 -o sample.csv
    python3 data_wrangler.py split data.csv --by Region --output-dir ./splits/
    python3 data_wrangler.py validate data.csv --rules rules.json
    python3 data_wrangler.py formula data.xlsx --expr "C2=A2+B2" --fill "C2:C100" -o result.xlsx
    python3 data_wrangler.py convert data.csv -o data.xlsx
    python3 data_wrangler.py query data.csv --sql "SELECT Name, AVG(Salary) FROM df WHERE Dept='Eng' GROUP BY Name"

Requirements:
    pip install pandas openpyxl
    Optional: pip install pyarrow (Parquet), xlrd (xls), fastparquet
"""

import argparse
import json
import os
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Dependency check
# --------------------------------------------------------------------------- #

def _check_pandas():
    """Check pandas availability, provide install instructions if missing."""
    try:
        import pandas as pd
        return pd
    except ImportError:
        print("Error: pandas is required. Install with:")
        print("  pip install pandas openpyxl")
        sys.exit(1)


def _check_openpyxl():
    """Check openpyxl for Excel support."""
    try:
        import openpyxl
        return openpyxl
    except ImportError:
        print("Error: openpyxl is required for Excel support. Install with:")
        print("  pip install openpyxl")
        sys.exit(1)


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #

def detect_format(path):
    """Detect file format from extension."""
    ext = Path(path).suffix.lower()
    FORMAT_MAP = {
        '.csv': 'csv', '.tsv': 'tsv', '.txt': 'tsv',
        '.xlsx': 'xlsx', '.xls': 'xls',
        '.json': 'json', '.jsonl': 'jsonl',
        '.parquet': 'parquet', '.pq': 'parquet',
    }
    fmt = FORMAT_MAP.get(ext)
    if not fmt:
        print(f"Error: unsupported format '{ext}'. Supported: {', '.join(sorted(set(FORMAT_MAP.values())))}")
        sys.exit(1)
    return fmt


def read_data(path, sheet=None, encoding='utf-8', dtype=None, nrows=None):
    """Read tabular data from any supported format."""
    pd = _check_pandas()
    fmt = detect_format(path)
    kwargs = {}
    if nrows:
        kwargs['nrows'] = nrows

    if fmt == 'csv':
        return pd.read_csv(path, encoding=encoding, dtype=dtype, **kwargs)
    elif fmt == 'tsv':
        return pd.read_csv(path, sep='\t', encoding=encoding, dtype=dtype, **kwargs)
    elif fmt in ('xlsx', 'xls'):
        _check_openpyxl()
        if fmt == 'xls':
            try:
                import xlrd  # noqa: F401
            except ImportError:
                print("Error: xlrd required for .xls files. Install: pip install xlrd")
                sys.exit(1)
        return pd.read_excel(path, sheet_name=sheet or 0, dtype=dtype, **kwargs)
    elif fmt == 'json':
        return pd.read_json(path, encoding=encoding, dtype=dtype, **kwargs)
    elif fmt == 'jsonl':
        return pd.read_json(path, lines=True, encoding=encoding, dtype=dtype, **kwargs)
    elif fmt == 'parquet':
        try:
            return pd.read_parquet(path, **kwargs)
        except ImportError:
            print("Error: pyarrow or fastparquet required for Parquet. Install: pip install pyarrow")
            sys.exit(1)


def write_data(df, path, sheet='Sheet1', index=False, encoding='utf-8'):
    """Write DataFrame to any supported format."""
    pd = _check_pandas()
    fmt = detect_format(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    if fmt == 'csv':
        df.to_csv(path, index=index, encoding=encoding)
    elif fmt == 'tsv':
        df.to_csv(path, sep='\t', index=index, encoding=encoding)
    elif fmt in ('xlsx', 'xls'):
        _check_openpyxl()
        df.to_excel(path, sheet_name=sheet, index=index, engine='openpyxl')
    elif fmt == 'json':
        df.to_json(path, orient='records', indent=2, force_ascii=False)
    elif fmt == 'jsonl':
        df.to_json(path, orient='records', lines=True, force_ascii=False)
    elif fmt == 'parquet':
        try:
            df.to_parquet(path, index=index)
        except ImportError:
            print("Error: pyarrow or fastparquet required for Parquet. Install: pip install pyarrow")
            sys.exit(1)

    size = os.path.getsize(path)
    print(f"Output: {path} ({size:,} bytes, {len(df):,} rows)")


# --------------------------------------------------------------------------- #
# Operations
# --------------------------------------------------------------------------- #

def op_inspect(args):
    """Show structure, types, stats, missing values, and sample rows."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding, nrows=args.nrows)

    print(f"=== {args.input} ===")
    print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"Memory: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    print()

    # Column info
    print("Columns:")
    print(f"  {'Name':<30} {'Type':<15} {'Non-Null':<12} {'Null':<8} {'Unique':<8}")
    print(f"  {'-'*30} {'-'*15} {'-'*12} {'-'*8} {'-'*8}")
    for col in df.columns:
        non_null = df[col].notna().sum()
        null_count = df[col].isna().sum()
        unique = df[col].nunique()
        print(f"  {str(col):<30} {str(df[col].dtype):<15} {non_null:<12} {null_count:<8} {unique:<8}")

    print()

    # Numeric summary
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 0:
        print("Numeric Summary:")
        desc = df[numeric_cols].describe().round(2)
        print(desc.to_string())
        print()

    # Sample rows
    n_sample = min(5, len(df))
    if n_sample > 0:
        print(f"First {n_sample} rows:")
        print(df.head(n_sample).to_string(max_colwidth=50))
        print()

    # Duplicates
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        print(f"Duplicate rows: {dup_count:,}")


def op_filter(args):
    """Filter rows using pandas query syntax."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)
    original_len = len(df)

    try:
        filtered = df.query(args.where)
    except Exception as e:
        print(f"Error in filter expression: {e}")
        print("Tip: Use pandas query syntax, e.g., 'Age > 30', 'Status == \"active\"'")
        sys.exit(1)

    print(f"Filtered: {original_len:,} -> {len(filtered):,} rows ({original_len - len(filtered):,} removed)")

    if args.output:
        write_data(filtered, args.output, sheet=args.sheet_out)
    else:
        print(filtered.to_string(max_colwidth=50))


def op_sort(args):
    """Sort by one or more columns."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    columns = [c.strip() for c in args.by.split(',')]
    for col in columns:
        if col not in df.columns:
            print(f"Error: column '{col}' not found. Available: {', '.join(df.columns)}")
            sys.exit(1)

    ascending = not args.desc
    df_sorted = df.sort_values(by=columns, ascending=ascending, na_position='last')
    print(f"Sorted by {columns} ({'desc' if args.desc else 'asc'})")

    if args.output:
        write_data(df_sorted, args.output, sheet=args.sheet_out)
    else:
        print(df_sorted.to_string(max_colwidth=50))


def op_group(args):
    """Group by columns and aggregate."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    by_cols = [c.strip() for c in args.by.split(',')]
    for col in by_cols:
        if col not in df.columns:
            print(f"Error: column '{col}' not found. Available: {', '.join(df.columns)}")
            sys.exit(1)

    # Parse aggregation spec: "Salary:mean,count" or "Salary:mean,Revenue:sum"
    agg_dict = {}
    if args.agg:
        for spec in args.agg.split(','):
            if ':' in spec:
                col, func = spec.rsplit(':', 1)
                col, func = col.strip(), func.strip()
                if col in agg_dict:
                    if isinstance(agg_dict[col], list):
                        agg_dict[col].append(func)
                    else:
                        agg_dict[col] = [agg_dict[col], func]
                else:
                    agg_dict[col] = func
            else:
                # Apply function to all numeric columns
                func = spec.strip()
                for col in df.select_dtypes(include='number').columns:
                    if col not in by_cols:
                        agg_dict[col] = func

    if not agg_dict:
        agg_dict = {col: ['mean', 'count'] for col in df.select_dtypes(include='number').columns if col not in by_cols}

    try:
        grouped = df.groupby(by_cols).agg(agg_dict)
    except Exception as e:
        print(f"Error in aggregation: {e}")
        sys.exit(1)

    # Flatten multi-level columns
    if isinstance(grouped.columns, pd.MultiIndex):
        grouped.columns = ['_'.join(str(c) for c in col).rstrip('_') for col in grouped.columns]
    grouped = grouped.reset_index()

    print(f"Grouped by {by_cols}: {len(grouped):,} groups")

    if args.output:
        write_data(grouped, args.output, sheet=args.sheet_out)
    else:
        print(grouped.to_string(max_colwidth=50))


def op_merge(args):
    """Merge/join two datasets."""
    pd = _check_pandas()
    df_left = read_data(args.input, sheet=args.sheet, encoding=args.encoding)
    df_right = read_data(args.right, sheet=args.sheet, encoding=args.encoding)

    on_cols = [c.strip() for c in args.on.split(',')]
    how = args.how or 'inner'

    # Validate join columns
    for col in on_cols:
        if col not in df_left.columns:
            print(f"Error: column '{col}' not in left dataset. Available: {', '.join(df_left.columns)}")
            sys.exit(1)
        if col not in df_right.columns:
            print(f"Error: column '{col}' not in right dataset. Available: {', '.join(df_right.columns)}")
            sys.exit(1)

    merged = pd.merge(df_left, df_right, on=on_cols, how=how, suffixes=('_left', '_right'))
    print(f"Merge ({how}): {len(df_left):,} + {len(df_right):,} -> {len(merged):,} rows")

    if args.output:
        write_data(merged, args.output, sheet=args.sheet_out)
    else:
        print(merged.to_string(max_colwidth=50))


def op_pivot(args):
    """Pivot / unpivot table."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    if args.unpivot:
        # Melt (unpivot)
        id_vars = [c.strip() for c in args.index.split(',')] if args.index else None
        pivoted = pd.melt(df, id_vars=id_vars, var_name=args.var_name or 'variable', value_name=args.value_name or 'value')
        print(f"Unpivot: {df.shape} -> {pivoted.shape}")
    else:
        # Pivot
        if not args.index or not args.columns or not args.values:
            print("Error: --index, --columns, and --values are required for pivot")
            sys.exit(1)

        aggfunc = args.aggfunc or 'first'
        pivoted = pd.pivot_table(
            df,
            index=[c.strip() for c in args.index.split(',')],
            columns=[c.strip() for c in args.columns.split(',')],
            values=[c.strip() for c in args.values.split(',')],
            aggfunc=aggfunc,
            fill_value=args.fill_value
        )

        # Flatten multi-level columns
        if isinstance(pivoted.columns, pd.MultiIndex):
            pivoted.columns = ['_'.join(str(c) for c in col).rstrip('_') for col in pivoted.columns]
        pivoted = pivoted.reset_index()
        print(f"Pivot: {df.shape} -> {pivoted.shape}")

    if args.output:
        write_data(pivoted, args.output, sheet=args.sheet_out)
    else:
        print(pivoted.to_string(max_colwidth=50))


def op_dedupe(args):
    """Remove duplicate rows."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)
    original_len = len(df)

    subset = [c.strip() for c in args.subset.split(',')] if args.subset else None
    keep = args.keep or 'first'

    deduped = df.drop_duplicates(subset=subset, keep=keep)
    removed = original_len - len(deduped)
    print(f"Deduplicated: {original_len:,} -> {len(deduped):,} rows ({removed:,} duplicates removed)")

    if args.output:
        write_data(deduped, args.output, sheet=args.sheet_out)
    else:
        print(deduped.to_string(max_colwidth=50))


def op_fill(args):
    """Fill missing values."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    columns = [c.strip() for c in args.column.split(',')] if args.column else df.columns.tolist()
    strategy = args.strategy or 'ffill'

    for col in columns:
        if col not in df.columns:
            print(f"Warning: column '{col}' not found, skipping")
            continue

        null_before = df[col].isna().sum()

        if strategy == 'mean':
            df[col] = df[col].fillna(df[col].mean())
        elif strategy == 'median':
            df[col] = df[col].fillna(df[col].median())
        elif strategy == 'mode':
            mode_val = df[col].mode()
            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val.iloc[0])
        elif strategy == 'zero':
            df[col] = df[col].fillna(0)
        elif strategy == 'empty':
            df[col] = df[col].fillna('')
        elif strategy == 'ffill':
            df[col] = df[col].ffill()
        elif strategy == 'bfill':
            df[col] = df[col].bfill()
        elif strategy == 'drop':
            df = df.dropna(subset=[col])
        elif strategy.startswith('value:'):
            val = strategy[6:]
            df[col] = df[col].fillna(val)
        else:
            print(f"Error: unknown strategy '{strategy}'. Use: mean, median, mode, zero, empty, ffill, bfill, drop, value:<v>")
            sys.exit(1)

        null_after = df[col].isna().sum()
        print(f"  {col}: {null_before} nulls -> {null_after} nulls")

    if args.output:
        write_data(df, args.output, sheet=args.sheet_out)
    else:
        print(df.to_string(max_colwidth=50))


def op_drop(args):
    """Drop columns or rows."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    if args.columns:
        cols = [c.strip() for c in args.columns.split(',')]
        missing = [c for c in cols if c not in df.columns]
        if missing:
            print(f"Warning: columns not found (skipping): {', '.join(missing)}")
        existing = [c for c in cols if c in df.columns]
        df = df.drop(columns=existing)
        print(f"Dropped columns: {', '.join(existing)}")

    if args.rows:
        # Parse row spec: "0-5" or "0,1,2" or "where:Age < 18"
        if args.rows.startswith('where:'):
            expr = args.rows[6:]
            mask = df.eval(expr)
            removed = mask.sum()
            df = df[~mask]
            print(f"Dropped {removed:,} rows matching '{expr}'")
        elif '-' in args.rows and ',' not in args.rows:
            start, end = args.rows.split('-')
            indices = list(range(int(start), int(end) + 1))
            df = df.drop(index=[i for i in indices if i in df.index])
            print(f"Dropped rows {start}-{end}")
        else:
            indices = [int(i.strip()) for i in args.rows.split(',')]
            df = df.drop(index=[i for i in indices if i in df.index])
            print(f"Dropped {len(indices)} rows")

    if args.null_threshold:
        thresh = float(args.null_threshold)
        before = len(df.columns)
        null_pct = df.isnull().mean()
        drop_cols = null_pct[null_pct > thresh].index.tolist()
        df = df.drop(columns=drop_cols)
        print(f"Dropped {before - len(df.columns)} columns with >{thresh*100:.0f}% nulls")

    print(f"Result: {df.shape[0]:,} rows x {df.shape[1]} columns")

    if args.output:
        write_data(df, args.output, sheet=args.sheet_out)
    else:
        print(df.to_string(max_colwidth=50))


def op_rename(args):
    """Rename columns."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    if args.map:
        rename_map = {}
        for pair in args.map.split(','):
            if ':' not in pair:
                print(f"Error: invalid rename spec '{pair}'. Use 'old:new'")
                sys.exit(1)
            old, new = pair.split(':', 1)
            rename_map[old.strip()] = new.strip()

        missing = [k for k in rename_map if k not in df.columns]
        if missing:
            print(f"Warning: columns not found: {', '.join(missing)}")

        df = df.rename(columns=rename_map)
        applied = {k: v for k, v in rename_map.items() if k not in missing}
        for old, new in applied.items():
            print(f"  {old} -> {new}")

    if args.lower:
        df.columns = [c.lower() for c in df.columns]
        print("Columns converted to lowercase")
    if args.upper:
        df.columns = [c.upper() for c in df.columns]
        print("Columns converted to uppercase")
    if args.snake:
        import re
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', re.sub(r'([A-Z])', r'_\1', str(c))).strip('_').lower() for c in df.columns]
        print("Columns converted to snake_case")

    if args.output:
        write_data(df, args.output, sheet=args.sheet_out)
    else:
        print(f"Columns: {', '.join(df.columns)}")


def op_cast(args):
    """Cast column types."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    columns = [c.strip() for c in args.column.split(',')]
    dtype = args.dtype

    for col in columns:
        if col not in df.columns:
            print(f"Warning: column '{col}' not found, skipping")
            continue

        try:
            if dtype == 'int':
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            elif dtype == 'float':
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif dtype == 'str':
                df[col] = df[col].astype(str)
            elif dtype == 'bool':
                df[col] = df[col].astype(bool)
            elif dtype == 'datetime':
                df[col] = pd.to_datetime(df[col], errors='coerce', format=args.date_format)
            elif dtype == 'category':
                df[col] = df[col].astype('category')
            else:
                df[col] = df[col].astype(dtype)
            print(f"  {col} -> {dtype}")
        except Exception as e:
            print(f"  Error casting {col} to {dtype}: {e}")

    if args.output:
        write_data(df, args.output, sheet=args.sheet_out)
    else:
        print(df.dtypes.to_string())


def op_derive(args):
    """Add computed columns."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    # Parse "NewCol = Expression"
    if '=' not in args.formula:
        print("Error: formula must be 'NewColumn = expression'")
        print("Example: 'Profit = Revenue - Cost'")
        sys.exit(1)

    col_name, expr = args.formula.split('=', 1)
    col_name = col_name.strip()
    expr = expr.strip()

    try:
        df[col_name] = df.eval(expr)
        print(f"Added column '{col_name}' = {expr}")
    except Exception as e:
        print(f"Error evaluating formula: {e}")
        print(f"Available columns: {', '.join(df.columns)}")
        sys.exit(1)

    if args.output:
        write_data(df, args.output, sheet=args.sheet_out)
    else:
        print(df.head(10).to_string(max_colwidth=50))


def op_sample(args):
    """Random sample of rows."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    n = min(int(args.n), len(df)) if args.n else None
    frac = float(args.frac) if args.frac else None

    if not n and not frac:
        n = min(100, len(df))

    sampled = df.sample(n=n, frac=frac, random_state=args.seed)
    print(f"Sampled {len(sampled):,} of {len(df):,} rows")

    if args.output:
        write_data(sampled, args.output, sheet=args.sheet_out)
    else:
        print(sampled.to_string(max_colwidth=50))


def op_split(args):
    """Split dataset by column values into separate files."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    if not args.by:
        print("Error: --by column is required for split")
        sys.exit(1)

    col = args.by
    if col not in df.columns:
        print(f"Error: column '{col}' not found. Available: {', '.join(df.columns)}")
        sys.exit(1)

    output_dir = Path(args.output_dir or './splits')
    output_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(args.input).suffix
    groups = df.groupby(col)

    for name, group_df in groups:
        safe_name = str(name).replace('/', '_').replace('\\', '_').replace(' ', '_')
        out_path = output_dir / f"{safe_name}{ext}"
        write_data(group_df, str(out_path))

    print(f"Split into {len(groups):,} files in {output_dir}/")


def op_validate(args):
    """Validate data against rules."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    if args.rules:
        with open(args.rules, 'r') as f:
            rules = json.load(f)
    else:
        rules = {}

    issues = []

    # Built-in checks
    # 1. Null check
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            issues.append({'column': str(col), 'issue': 'nulls', 'count': int(count), 'severity': 'warning'})

    # 2. Duplicate check
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues.append({'column': '*', 'issue': 'duplicate_rows', 'count': int(dup_count), 'severity': 'warning'})

    # 3. Custom rules from JSON
    for rule in rules.get('rules', []):
        col = rule.get('column')
        if col and col not in df.columns:
            issues.append({'column': col, 'issue': 'column_missing', 'count': 0, 'severity': 'error'})
            continue

        rtype = rule.get('type')
        if rtype == 'not_null':
            nulls = df[col].isnull().sum()
            if nulls > 0:
                issues.append({'column': col, 'issue': 'required_nulls', 'count': int(nulls), 'severity': 'error'})
        elif rtype == 'unique':
            dups = df[col].duplicated().sum()
            if dups > 0:
                issues.append({'column': col, 'issue': 'uniqueness_violation', 'count': int(dups), 'severity': 'error'})
        elif rtype == 'range':
            lo, hi = rule.get('min'), rule.get('max')
            if lo is not None:
                below = (pd.to_numeric(df[col], errors='coerce') < lo).sum()
                if below > 0:
                    issues.append({'column': col, 'issue': f'below_min({lo})', 'count': int(below), 'severity': 'error'})
            if hi is not None:
                above = (pd.to_numeric(df[col], errors='coerce') > hi).sum()
                if above > 0:
                    issues.append({'column': col, 'issue': f'above_max({hi})', 'count': int(above), 'severity': 'error'})
        elif rtype == 'pattern':
            import re
            pattern = rule.get('regex')
            non_match = (~df[col].astype(str).str.match(pattern, na=False)).sum()
            if non_match > 0:
                issues.append({'column': col, 'issue': f'pattern_mismatch({pattern})', 'count': int(non_match), 'severity': 'error'})
        elif rtype == 'enum':
            allowed = set(rule.get('values', []))
            invalid = (~df[col].isin(allowed)).sum()
            if invalid > 0:
                issues.append({'column': col, 'issue': f'invalid_values', 'count': int(invalid), 'severity': 'error'})

    # Report
    errors = [i for i in issues if i['severity'] == 'error']
    warnings = [i for i in issues if i['severity'] == 'warning']

    print(f"=== Validation Report: {args.input} ===")
    print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"Errors: {len(errors)}, Warnings: {len(warnings)}")
    print()

    for issue in sorted(issues, key=lambda x: (x['severity'] != 'error', x['column'])):
        icon = 'E' if issue['severity'] == 'error' else 'W'
        print(f"  [{icon}] {issue['column']}: {issue['issue']} ({issue['count']:,} rows)")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump({'file': args.input, 'shape': list(df.shape), 'issues': issues}, f, indent=2)
        print(f"\nReport saved: {args.output}")

    if errors:
        sys.exit(1)


def op_formula(args):
    """Apply Excel-style formulas to cells."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    if not args.expr:
        print("Error: --expr is required")
        sys.exit(1)

    # Parse Excel-style formula: "C2=A2+B2" or "D=A*B+C"
    if '=' not in args.expr:
        print("Error: formula must contain '=', e.g., 'C=A+B' or 'C2=A2+B2'")
        sys.exit(1)

    target, formula = args.expr.split('=', 1)
    target = target.strip()
    formula = formula.strip()

    # Column-level formula (e.g., C=A+B applies to all rows)
    try:
        df[target] = df.eval(formula)
        print(f"Applied: {target} = {formula}")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Available columns: {', '.join(df.columns)}")
        sys.exit(1)

    if args.output:
        write_data(df, args.output, sheet=args.sheet_out)
    else:
        print(df.head(10).to_string(max_colwidth=50))


def op_convert(args):
    """Convert between formats (CSV, Excel, JSON, Parquet, TSV)."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    if not args.output:
        print("Error: -o/--output is required for convert")
        sys.exit(1)

    in_fmt = detect_format(args.input)
    out_fmt = detect_format(args.output)
    print(f"Converting: {in_fmt} -> {out_fmt} ({len(df):,} rows)")

    write_data(df, args.output, sheet=args.sheet_out)


def op_query(args):
    """Run SQL-like queries on data using pandas."""
    pd = _check_pandas()
    df = read_data(args.input, sheet=args.sheet, encoding=args.encoding)

    if not args.sql:
        print("Error: --sql is required")
        sys.exit(1)

    try:
        # pandasql-like: simple SQL parsing
        # Use df.query for WHERE, groupby for GROUP BY, etc.
        sql = args.sql.strip()

        # Try using pandasql if available
        try:
            import pandasql
            result = pandasql.sqldf(sql, {'df': df})
        except ImportError:
            # Fallback: parse simple SQL manually
            print("Note: For full SQL support, install pandasql: pip install pandasql")
            print("Falling back to pandas query syntax...")

            # Extract WHERE clause if present
            import re
            where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP|\s+ORDER|\s+LIMIT|$)', sql, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1).strip()
                # Convert SQL operators to pandas
                where_clause = where_clause.replace(' AND ', ' and ').replace(' OR ', ' or ')
                result = df.query(where_clause)
            else:
                result = df

        print(f"Query result: {len(result):,} rows")

        if args.output:
            write_data(result, args.output, sheet=args.sheet_out)
        else:
            print(result.to_string(max_colwidth=50))

    except Exception as e:
        print(f"Error executing query: {e}")
        sys.exit(1)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser():
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description='Data Wrangler — tabular data manipulation engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Operations:
  inspect    Show structure, types, stats, nulls, sample rows
  filter     Filter rows using pandas query syntax
  sort       Sort by columns (asc/desc)
  group      GroupBy + aggregate (sum, mean, count, min, max, std)
  merge      Join two datasets (inner, left, right, outer, cross)
  pivot      Pivot / unpivot (melt) tables
  dedupe     Remove duplicate rows
  fill       Fill missing values (mean, median, mode, ffill, bfill, zero, value)
  drop       Drop columns, rows, or high-null columns
  rename     Rename columns (map, lowercase, uppercase, snake_case)
  cast       Cast column types (int, float, str, bool, datetime, category)
  derive     Add computed columns (Profit = Revenue - Cost)
  sample     Random sample of rows
  split      Split by column values into separate files
  validate   Validate data against rules (JSON)
  formula    Apply column-level formulas
  convert    Convert between formats (CSV, Excel, JSON, Parquet, TSV)
  query      SQL-like queries on data

Examples:
  %(prog)s inspect sales.csv
  %(prog)s filter sales.xlsx --where "Region == 'West'" -o west.xlsx
  %(prog)s sort data.csv --by Revenue --desc -o sorted.csv
  %(prog)s group data.csv --by Dept --agg "Salary:mean,count" -o summary.csv
  %(prog)s merge orders.csv customers.csv --on CustomerID --how left -o joined.csv
  %(prog)s convert data.csv -o data.xlsx
        """
    )

    subparsers = parser.add_subparsers(dest='operation', help='Operation to perform')

    # Common args function
    def add_common_args(p):
        p.add_argument('input', help='Input file path')
        p.add_argument('-o', '--output', help='Output file path')
        p.add_argument('--sheet', help='Sheet name (Excel)')
        p.add_argument('--sheet-out', default='Sheet1', help='Output sheet name (Excel)')
        p.add_argument('--encoding', default='utf-8', help='File encoding (def: utf-8)')

    # inspect
    p = subparsers.add_parser('inspect', help='Inspect data structure and stats')
    add_common_args(p)
    p.add_argument('--nrows', type=int, help='Only read first N rows')

    # filter
    p = subparsers.add_parser('filter', help='Filter rows')
    add_common_args(p)
    p.add_argument('--where', required=True, help='Filter expression (pandas query syntax)')

    # sort
    p = subparsers.add_parser('sort', help='Sort by columns')
    add_common_args(p)
    p.add_argument('--by', required=True, help='Column(s) to sort by (comma-sep)')
    p.add_argument('--desc', action='store_true', help='Sort descending')

    # group
    p = subparsers.add_parser('group', help='Group by columns and aggregate')
    add_common_args(p)
    p.add_argument('--by', required=True, help='Column(s) to group by (comma-sep)')
    p.add_argument('--agg', help='Aggregation spec: "Col:func,Col:func" or "func"')

    # merge
    p = subparsers.add_parser('merge', help='Merge/join two datasets')
    add_common_args(p)
    p.add_argument('right', help='Right-side file to merge')
    p.add_argument('--on', required=True, help='Join column(s) (comma-sep)')
    p.add_argument('--how', choices=['inner', 'left', 'right', 'outer', 'cross'], default='inner', help='Join type')

    # pivot
    p = subparsers.add_parser('pivot', help='Pivot / unpivot table')
    add_common_args(p)
    p.add_argument('--index', help='Row index column(s)')
    p.add_argument('--columns', help='Column to pivot on')
    p.add_argument('--values', help='Value column(s)')
    p.add_argument('--aggfunc', default='first', help='Aggregation function (def: first)')
    p.add_argument('--fill-value', dest='fill_value', help='Fill value for missing cells')
    p.add_argument('--unpivot', action='store_true', help='Unpivot (melt) instead')
    p.add_argument('--var-name', help='Variable column name (unpivot)')
    p.add_argument('--value-name', help='Value column name (unpivot)')

    # dedupe
    p = subparsers.add_parser('dedupe', help='Remove duplicates')
    add_common_args(p)
    p.add_argument('--subset', help='Column(s) to check for duplicates (comma-sep)')
    p.add_argument('--keep', choices=['first', 'last', False], default='first', help='Which duplicate to keep')

    # fill
    p = subparsers.add_parser('fill', help='Fill missing values')
    add_common_args(p)
    p.add_argument('--column', help='Column(s) to fill (comma-sep, default: all)')
    p.add_argument('--strategy', default='ffill', help='Fill strategy: mean, median, mode, zero, empty, ffill, bfill, drop, value:<v>')

    # drop
    p = subparsers.add_parser('drop', help='Drop columns or rows')
    add_common_args(p)
    p.add_argument('--columns', help='Columns to drop (comma-sep)')
    p.add_argument('--rows', help='Rows to drop: "0-5", "0,1,2", or "where:expr"')
    p.add_argument('--null-threshold', help='Drop columns with null ratio above threshold (0-1)')

    # rename
    p = subparsers.add_parser('rename', help='Rename columns')
    add_common_args(p)
    p.add_argument('--map', help='Rename map: "old:new,old2:new2"')
    p.add_argument('--lower', action='store_true', help='Lowercase all columns')
    p.add_argument('--upper', action='store_true', help='Uppercase all columns')
    p.add_argument('--snake', action='store_true', help='Snake_case all columns')

    # cast
    p = subparsers.add_parser('cast', help='Cast column types')
    add_common_args(p)
    p.add_argument('--column', required=True, help='Column(s) to cast (comma-sep)')
    p.add_argument('--dtype', required=True, help='Target type: int, float, str, bool, datetime, category')
    p.add_argument('--date-format', help='Date format string (e.g., %%Y-%%m-%%d)')

    # derive
    p = subparsers.add_parser('derive', help='Add computed column')
    add_common_args(p)
    p.add_argument('--formula', required=True, help='Formula: "NewCol = expression"')

    # sample
    p = subparsers.add_parser('sample', help='Random sample')
    add_common_args(p)
    p.add_argument('--n', type=int, help='Number of rows to sample')
    p.add_argument('--frac', type=float, help='Fraction of rows to sample (0-1)')
    p.add_argument('--seed', type=int, default=42, help='Random seed (def: 42)')

    # split
    p = subparsers.add_parser('split', help='Split by column values')
    add_common_args(p)
    p.add_argument('--by', required=True, help='Column to split by')
    p.add_argument('--output-dir', help='Output directory (def: ./splits/)')

    # validate
    p = subparsers.add_parser('validate', help='Validate against rules')
    add_common_args(p)
    p.add_argument('--rules', help='Rules JSON file')

    # formula
    p = subparsers.add_parser('formula', help='Apply column formulas')
    add_common_args(p)
    p.add_argument('--expr', required=True, help='Formula: "ColName=expression"')

    # convert
    p = subparsers.add_parser('convert', help='Convert between formats')
    add_common_args(p)

    # query
    p = subparsers.add_parser('query', help='SQL-like queries')
    add_common_args(p)
    p.add_argument('--sql', required=True, help='SQL query (use "df" as table name)')

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.operation:
        parser.print_help()
        sys.exit(0)

    operations = {
        'inspect': op_inspect,
        'filter': op_filter,
        'sort': op_sort,
        'group': op_group,
        'merge': op_merge,
        'pivot': op_pivot,
        'dedupe': op_dedupe,
        'fill': op_fill,
        'drop': op_drop,
        'rename': op_rename,
        'cast': op_cast,
        'derive': op_derive,
        'sample': op_sample,
        'split': op_split,
        'validate': op_validate,
        'formula': op_formula,
        'convert': op_convert,
        'query': op_query,
    }

    op_func = operations.get(args.operation)
    if op_func:
        try:
            op_func(args)
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(130)
        except FileNotFoundError as e:
            print(f"Error: file not found: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
