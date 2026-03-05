# Pandas Patterns Reference

Common pandas patterns for data manipulation. Load this reference for advanced DataFrame operations.

## Reading Large Files

```python
# Chunked reading for memory efficiency
chunks = pd.read_csv('large.csv', chunksize=10000)
result = pd.concat([chunk[chunk['Status'] == 'active'] for chunk in chunks])

# Read only specific columns
df = pd.read_csv('data.csv', usecols=['Name', 'Revenue', 'Date'])

# Optimize dtypes on read
df = pd.read_csv('data.csv', dtype={'ID': 'int32', 'Status': 'category'})

# Read with date parsing
df = pd.read_csv('data.csv', parse_dates=['Date', 'Created'])
```

## String Operations

```python
# Clean strings
df['Name'] = df['Name'].str.strip().str.title()
df['Email'] = df['Email'].str.lower().str.strip()

# Extract patterns
df['Domain'] = df['Email'].str.extract(r'@(.+)$')
df['AreaCode'] = df['Phone'].str.extract(r'\((\d{3})\)')

# Contains filter
mask = df['Description'].str.contains('urgent|critical', case=False, na=False)

# Replace patterns
df['Phone'] = df['Phone'].str.replace(r'[^\d]', '', regex=True)
```

## Date Operations

```python
# Parse dates
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')

# Extract components
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['DayOfWeek'] = df['Date'].dt.day_name()
df['Quarter'] = df['Date'].dt.quarter

# Date arithmetic
df['DaysOld'] = (pd.Timestamp.now() - df['Date']).dt.days
df['NextMonth'] = df['Date'] + pd.DateOffset(months=1)

# Filter by date range
mask = (df['Date'] >= '2024-01-01') & (df['Date'] < '2025-01-01')
```

## Advanced GroupBy

```python
# Multiple aggregations per column
result = df.groupby('Dept').agg(
    avg_salary=('Salary', 'mean'),
    max_salary=('Salary', 'max'),
    headcount=('ID', 'count'),
    total_revenue=('Revenue', 'sum')
).reset_index()

# Transform (broadcast back to original shape)
df['DeptAvg'] = df.groupby('Dept')['Salary'].transform('mean')
df['PctOfDept'] = df['Salary'] / df.groupby('Dept')['Salary'].transform('sum')

# Rank within groups
df['Rank'] = df.groupby('Dept')['Revenue'].rank(ascending=False, method='dense')

# Rolling window within groups
df['Rolling3M'] = df.groupby('Product')['Revenue'].transform(lambda x: x.rolling(3).mean())
```

## Multi-Level Merge Patterns

```python
# Multiple key merge
merged = pd.merge(orders, products, on=['ProductID', 'Region'], how='left')

# Indicator column (shows merge source)
merged = pd.merge(left, right, on='ID', how='outer', indicator=True)
# _merge column: 'left_only', 'right_only', 'both'

# Cross join (cartesian product)
cross = pd.merge(df1, df2, how='cross')

# Merge with different column names
merged = pd.merge(left, right, left_on='emp_id', right_on='employee_id')
```

## Reshaping

```python
# Wide to long (melt)
long = pd.melt(df, id_vars=['Name'], value_vars=['Q1', 'Q2', 'Q3', 'Q4'],
               var_name='Quarter', value_name='Revenue')

# Long to wide (pivot)
wide = df.pivot_table(index='Name', columns='Quarter', values='Revenue', aggfunc='sum')

# Stack / unstack
stacked = df.set_index(['Name', 'Quarter'])['Revenue'].unstack()

# Explode lists into rows
df_exploded = df.explode('Tags')
```

## Performance Tips

```python
# Use category dtype for low-cardinality strings
df['Status'] = df['Status'].astype('category')  # Saves ~90% memory

# Use Int64 (nullable) instead of float for integers with nulls
df['Count'] = df['Count'].astype('Int64')

# Vectorized operations (fast) vs apply (slow)
# Good: df['Total'] = df['Price'] * df['Qty']
# Bad:  df['Total'] = df.apply(lambda r: r['Price'] * r['Qty'], axis=1)

# Use .query() for large DataFrames (faster than boolean indexing)
result = df.query('Revenue > 10000 and Status == "active"')

# Use .at[] / .iat[] for single cell access (faster than .loc/.iloc)
value = df.at[0, 'Revenue']
```

## Excel-Specific Patterns (openpyxl)

```python
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, numbers

# Load existing workbook
wb = load_workbook('data.xlsx')
ws = wb.active

# Cell formatting
ws['A1'].font = Font(bold=True, size=14, color='4472C4')
ws['A1'].fill = PatternFill(start_color='F2F2F2', fill_type='solid')
ws['A1'].alignment = Alignment(horizontal='center', wrap_text=True)

# Number formats
ws['B2'].number_format = '#,##0.00'      # Currency-like
ws['C2'].number_format = '0.0%'           # Percentage
ws['D2'].number_format = 'yyyy-mm-dd'     # Date

# Column widths
ws.column_dimensions['A'].width = 25
ws.column_dimensions['B'].width = 15

# Row heights
ws.row_dimensions[1].height = 30

# Merge cells
ws.merge_cells('A1:D1')

# Add formula
ws['E2'] = '=SUM(B2:D2)'

# Conditional formatting
from openpyxl.formatting.rule import CellIsRule
red_fill = PatternFill(start_color='FFC7CE', fill_type='solid')
ws.conditional_formatting.add('B2:B100',
    CellIsRule(operator='lessThan', formula=['0'], fill=red_fill))

# Auto-filter
ws.auto_filter.ref = ws.dimensions

# Freeze panes (freeze row 1)
ws.freeze_panes = 'A2'

# Print setup
ws.print_title_rows = '1:1'
ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
```

## Data Cleaning Recipes

```python
# Remove whitespace from all string columns
str_cols = df.select_dtypes(include='object').columns
df[str_cols] = df[str_cols].apply(lambda x: x.str.strip())

# Standardize phone numbers
df['Phone'] = df['Phone'].str.replace(r'[^\d]', '', regex=True)
df['Phone'] = df['Phone'].apply(lambda x: f'({x[:3]}) {x[3:6]}-{x[6:]}' if len(str(x)) == 10 else x)

# Handle currency strings
df['Revenue'] = df['Revenue'].str.replace(r'[$,]', '', regex=True).astype(float)

# Detect and fix encoding issues
df = pd.read_csv('data.csv', encoding='latin-1')  # or 'cp1252'

# Drop constant columns (only one unique value)
nunique = df.nunique()
df = df.drop(columns=nunique[nunique == 1].index)
```
