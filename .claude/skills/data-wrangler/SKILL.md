---
name: data-wrangler
description: >
  Production-grade tabular data manipulation using pandas & openpyxl. This skill should be used
  when editing, creating, filtering, sorting, merging, pivoting, deduplicating, validating, or
  transforming CSV, Excel (xlsx/xls), JSON, Parquet, or TSV files. Supports 18 operations via
  CLI scripts, advanced Excel formatting (multi-sheet, freeze, auto-filter, validation, styling),
  and file-converter integration for format pipelines.
author: George Khananaev
---

# Data Wrangler

Manipulate tabular data (CSV, Excel, JSON, Parquet, TSV) w/ pandas-powered scripts. Two scripts cover all operations: `data_wrangler.py` for data ops, `excel_toolkit.py` for Excel-specific features.

## When to Use

- User asks to read, edit, filter, sort, or transform CSV/Excel/JSON/Parquet/TSV files
- User asks to merge/join datasets, deduplicate, fill missing values, or validate data
- User asks to create Excel workbooks w/ formatting, dropdowns, freeze panes, or multi-sheet
- User asks to pivot, unpivot, group-by, aggregate, sample, or split datasets
- User asks to add computed columns, rename columns, cast types, or apply formulas
- User asks to convert between data formats (CSV -> Excel, JSON -> Parquet, etc.)
- User asks to inspect/profile data structure, types, nulls, stats

## Prerequisites

```bash
# Required
pip install pandas openpyxl

# Optional (per feature)
pip install pyarrow          # Parquet support
pip install xlrd             # Legacy .xls read
pip install pandasql         # SQL queries on DataFrames
pip install fastparquet      # Alternative Parquet engine
```

## Quick Routing

| Task | Script | Command |
|------|--------|---------|
| Inspect/profile data | `data_wrangler.py` | `inspect` |
| Filter rows | `data_wrangler.py` | `filter --where "expr"` |
| Sort by columns | `data_wrangler.py` | `sort --by Col --desc` |
| Group & aggregate | `data_wrangler.py` | `group --by Col --agg "Col:func"` |
| Merge/join files | `data_wrangler.py` | `merge f2 --on Key --how left` |
| Pivot / unpivot | `data_wrangler.py` | `pivot --index/--unpivot` |
| Remove duplicates | `data_wrangler.py` | `dedupe --subset "Col"` |
| Fill missing values | `data_wrangler.py` | `fill --column Col --strategy mean` |
| Drop cols/rows | `data_wrangler.py` | `drop --columns "A,B"` |
| Rename columns | `data_wrangler.py` | `rename --map "old:new"` |
| Cast types | `data_wrangler.py` | `cast --column Col --dtype datetime` |
| Computed columns | `data_wrangler.py` | `derive --formula "New = A + B"` |
| Random sample | `data_wrangler.py` | `sample --n 100` |
| Split by values | `data_wrangler.py` | `split --by Region` |
| Validate rules | `data_wrangler.py` | `validate --rules rules.json` |
| Apply formulas | `data_wrangler.py` | `formula --expr "C=A+B"` |
| Convert formats | `data_wrangler.py` | `convert -o data.xlsx` |
| SQL queries | `data_wrangler.py` | `query --sql "SELECT..."` |
| List Excel sheets | `excel_toolkit.py` | `sheets` |
| Extract sheet | `excel_toolkit.py` | `extract --sheet Sales -o sales.csv` |
| Combine -> xlsx | `excel_toolkit.py` | `combine *.csv -o combined.xlsx` |
| Format headers | `excel_toolkit.py` | `format --header-style bold,blue --autowidth` |
| Freeze panes | `excel_toolkit.py` | `freeze --at B2` |
| Auto-filter | `excel_toolkit.py` | `autofilter` |
| Dropdown validation | `excel_toolkit.py` | `validate --column Status --values "Open,Closed"` |
| Protect sheet | `excel_toolkit.py` | `protect --password secret` |
| Create workbook | `excel_toolkit.py` | `create --columns "Name,Age" -o template.xlsx` |

## Usage Patterns

### Data Operations (`data_wrangler.py`)

All operations follow: `python3 scripts/data_wrangler.py <op> <input> [options] [-o output]`

```bash
# Inspect
python3 data_wrangler.py inspect sales.csv
python3 data_wrangler.py inspect data.xlsx --sheet "Q1 Sales" --nrows 1000

# Filter
python3 data_wrangler.py filter data.csv --where "Revenue > 10000" -o high_rev.csv
python3 data_wrangler.py filter data.csv --where 'Status == "active" and Age >= 25' -o active.csv

# Sort
python3 data_wrangler.py sort data.csv --by "Revenue,Name" --desc -o sorted.csv

# Group + Aggregate
python3 data_wrangler.py group data.csv --by Department --agg "Salary:mean,Salary:count,Revenue:sum" -o summary.csv

# Merge
python3 data_wrangler.py merge orders.csv customers.csv --on CustomerID --how left -o joined.csv

# Pivot
python3 data_wrangler.py pivot data.csv --index Name --columns Month --values Sales --aggfunc sum -o pivoted.csv

# Unpivot (melt)
python3 data_wrangler.py pivot wide.csv --index ID --unpivot --var-name Metric --value-name Value -o long.csv

# Deduplicate
python3 data_wrangler.py dedupe data.csv --subset "Email" --keep first -o clean.csv

# Fill nulls
python3 data_wrangler.py fill data.csv --column "Revenue,Profit" --strategy mean -o filled.csv

# Drop columns
python3 data_wrangler.py drop data.csv --columns "TempCol,Notes" -o trimmed.csv
python3 data_wrangler.py drop data.csv --null-threshold 0.5 -o cleaned.csv

# Rename
python3 data_wrangler.py rename data.csv --map "old_name:new_name,col2:Column2" -o renamed.csv
python3 data_wrangler.py rename data.csv --snake -o snake_case.csv

# Cast types
python3 data_wrangler.py cast data.csv --column Date --dtype datetime --date-format "%Y-%m-%d" -o typed.csv

# Computed columns
python3 data_wrangler.py derive data.csv --formula "Profit = Revenue - Cost" -o enriched.csv

# Sample
python3 data_wrangler.py sample large.csv --n 500 --seed 42 -o sample.csv

# Split by value
python3 data_wrangler.py split data.csv --by Region --output-dir ./by_region/

# Validate
python3 data_wrangler.py validate data.csv --rules validation_rules.json -o report.json

# Formula
python3 data_wrangler.py formula data.xlsx --expr "Total=Price*Quantity" -o calculated.xlsx

# Convert
python3 data_wrangler.py convert data.csv -o data.xlsx
python3 data_wrangler.py convert data.xlsx -o data.json
python3 data_wrangler.py convert data.json -o data.parquet

# SQL query
python3 data_wrangler.py query data.csv --sql "SELECT Name, AVG(Salary) FROM df WHERE Dept='Eng' GROUP BY Name"
```

### Excel Operations (`excel_toolkit.py`)

All operations follow: `python3 scripts/excel_toolkit.py <op> <input> [options] [-o output]`

```bash
# List sheets
python3 excel_toolkit.py sheets workbook.xlsx

# Extract sheet
python3 excel_toolkit.py extract workbook.xlsx --sheet "Sales Q1" -o sales_q1.csv

# Combine multiple files into multi-sheet xlsx
python3 excel_toolkit.py combine sales.csv inventory.csv orders.csv -o report.xlsx

# Format
python3 excel_toolkit.py format data.xlsx --header-style bold,blue --autowidth --zebra -o styled.xlsx

# Freeze panes
python3 excel_toolkit.py freeze data.xlsx --at B2 -o frozen.xlsx

# Auto-filter
python3 excel_toolkit.py autofilter data.xlsx -o filtered.xlsx

# Dropdown validation
python3 excel_toolkit.py validate data.xlsx --column Status --values "Open,Closed,Pending" -o validated.xlsx

# Protect
python3 excel_toolkit.py protect data.xlsx --password mypass -o protected.xlsx

# Create template
python3 excel_toolkit.py create --columns "Name,Email,Department,Start Date,Salary" -o template.xlsx
```

## Validation Rules Format

Create a JSON rules file for `validate`:

```json
{
  "rules": [
    {"column": "Email", "type": "not_null"},
    {"column": "Email", "type": "pattern", "regex": "^[^@]+@[^@]+\\.[^@]+$"},
    {"column": "ID", "type": "unique"},
    {"column": "Age", "type": "range", "min": 0, "max": 150},
    {"column": "Status", "type": "enum", "values": ["active", "inactive", "pending"]}
  ]
}
```

Rule types: `not_null`, `unique`, `range` (min/max), `pattern` (regex), `enum` (allowed values).

## Fill Strategies

| Strategy | Behavior |
|----------|----------|
| `mean` | Fill w/ column mean (numeric) |
| `median` | Fill w/ column median (numeric) |
| `mode` | Fill w/ most frequent value |
| `zero` | Fill w/ 0 |
| `empty` | Fill w/ empty string |
| `ffill` | Forward fill (carry last value) |
| `bfill` | Backward fill |
| `drop` | Drop rows w/ nulls in column |
| `value:<v>` | Fill w/ specific value |

## Supported Formats

| Format | Read | Write | Dependency |
|--------|------|-------|------------|
| CSV | Y | Y | (builtin) |
| TSV | Y | Y | (builtin) |
| XLSX | Y | Y | openpyxl |
| XLS | Y | N | xlrd |
| JSON | Y | Y | (builtin) |
| JSONL | Y | Y | (builtin) |
| Parquet | Y | Y | pyarrow |

## Integration w/ file-converter

Pipeline data between skills:

```bash
# 1. Convert YAML -> CSV (file-converter), then wrangle
python3 .claude/skills/file-converter/scripts/csv_json_yaml.py data.yaml data.csv
python3 .claude/skills/data-wrangler/scripts/data_wrangler.py filter data.csv --where "Status == 'active'" -o filtered.csv

# 2. Wrangle, then convert to PDF report
python3 data_wrangler.py group data.csv --by Dept --agg "Salary:mean,count" -o summary.csv
# (Use file-converter to render summary as markdown -> PDF)

# 3. Excel -> JSON -> YAML pipeline
python3 data_wrangler.py convert data.xlsx -o data.json
python3 .claude/skills/file-converter/scripts/csv_json_yaml.py data.json data.yaml
```

## Pandas Query Syntax Reference

Filter expressions use pandas query syntax:

| Pattern | Example |
|---------|---------|
| Comparison | `Age > 30`, `Revenue >= 10000` |
| Equality | `Status == "active"`, `Region != "East"` |
| String contains | `Name.str.contains("Smith")` |
| Multiple conditions | `Age > 25 and Status == "active"` |
| OR conditions | `Region == "East" or Region == "West"` |
| IN list | `Status in ["active", "pending"]` |
| NOT IN | `Status not in ["closed", "archived"]` |
| Null check | `Revenue.notna()`, `Email.isna()` |
| Between | `Age >= 18 and Age <= 65` |

## Aggregation Functions

Available for `group --agg` and `pivot --aggfunc`:

`sum`, `mean`, `median`, `min`, `max`, `count`, `std`, `var`, `first`, `last`, `nunique`

Spec format: `"Column:function"` — multiple: `"Salary:mean,Salary:count,Revenue:sum"`
