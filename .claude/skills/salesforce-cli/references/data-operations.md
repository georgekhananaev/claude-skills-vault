# Data Operations Reference

Export, import, bulk operations, tree format, and file-converter integration patterns.

## Export Patterns

### Query Export (Small-Medium Datasets)

```bash
# CSV export
sf data query --target-org my-org \
  --query "SELECT Id, Name, Industry FROM Account LIMIT 200" \
  --result-format csv --output-file accounts.csv

# JSON export
sf data query --target-org my-org \
  --query "SELECT Id, Name, Industry FROM Account LIMIT 200" \
  --json > accounts.json

# Human-readable (terminal display)
sf data query --target-org my-org \
  --query "SELECT Id, Name FROM Account LIMIT 50"
```

### Bulk Export (Large Datasets — 10,000+ records)

```bash
# Bulk export to CSV
sf data export bulk --target-org my-org \
  --query "SELECT Id, Name, Industry, Website FROM Account" \
  --output-file accounts_bulk.csv

# Resume interrupted export
sf data export resume --job-id <jobId> --target-org my-org
```

### Tree Export (Preserves Relationships)

```bash
# Export with child relationships
sf data export tree --target-org my-org \
  --query "SELECT Id, Name, (SELECT Id, FirstName, LastName FROM Contacts) FROM Account LIMIT 50" \
  --output-dir ./data

# Export with plan file (for multi-object re-import)
sf data export tree --target-org my-org \
  --query "SELECT Id, Name, (SELECT Id, FirstName FROM Contacts) FROM Account LIMIT 50" \
  --plan --output-dir ./data
```

Tree export produces:
- `Account.json` — Account records
- `Contact.json` — Contact records with Account references
- `Account-Contact-plan.json` — Import plan (if `--plan` used)

---

## Import Patterns

### Single Record (Write tier)

```bash
# Create
sf data create record --target-org my-org \
  --sobject Account --values "Name='Acme Corp' Industry='Technology'"

# Update
sf data update record --target-org my-org \
  --sobject Account --record-id 001xx000003DGbY --values "Industry='Finance'"

# Upsert (single)
sf data upsert record --target-org my-org \
  --sobject Account --external-id External_Id__c --values "External_Id__c='EXT-001' Name='Acme'"
```

### Tree Import (Write tier)

```bash
# Import from files
sf data import tree --target-org my-org --files Account.json,Contact.json

# Import using plan file
sf data import tree --target-org my-org --plan data/Account-Contact-plan.json
```

### Bulk Import (Write tier)

```bash
# Insert from CSV
sf data import bulk --target-org my-org \
  --sobject Account --file accounts.csv

# Upsert from CSV (match on External ID)
sf data upsert bulk --target-org my-org \
  --sobject Account --file accounts.csv --external-id External_Id__c

# Update from CSV (must include Id column)
sf data update bulk --target-org my-org \
  --sobject Account --file account_updates.csv

# Resume interrupted bulk operation
sf data import resume --job-id <jobId> --target-org my-org
sf data upsert resume --job-id <jobId> --target-org my-org
sf data update resume --job-id <jobId> --target-org my-org
```

### Bulk Delete (Destructive tier)

```bash
# Delete from CSV (single "Id" column required)
sf data delete bulk --target-org my-org \
  --sobject Account --file delete-ids.csv

# Resume
sf data delete resume --job-id <jobId> --target-org my-org
```

---

## CSV Format Requirements

### For Bulk Import

```csv
Name,Industry,Website
"Acme Corp",Technology,https://acme.com
"Globex Inc",Finance,https://globex.com
```

### For Bulk Update

Must include `Id` column:

```csv
Id,Industry,Website
001xx000003DGbY,Finance,https://acme-updated.com
001xx000003DGbZ,Healthcare,https://globex-updated.com
```

### For Bulk Upsert

Must include External ID column:

```csv
External_Id__c,Name,Industry
EXT-001,Acme Corp,Technology
EXT-002,Globex Inc,Finance
```

### For Bulk Delete

Single `Id` column only:

```csv
Id
001xx000003DGbY
001xx000003DGbZ
```

---

## Tree Format (JSON)

### Single Object

```json
{
  "records": [
    {
      "attributes": {
        "type": "Account",
        "referenceId": "AccountRef1"
      },
      "Name": "Acme Corp",
      "Industry": "Technology"
    }
  ]
}
```

### With Child Records

```json
{
  "records": [
    {
      "attributes": {
        "type": "Account",
        "referenceId": "AccountRef1"
      },
      "Name": "Acme Corp",
      "Contacts": {
        "records": [
          {
            "attributes": {
              "type": "Contact",
              "referenceId": "ContactRef1"
            },
            "FirstName": "John",
            "LastName": "Doe"
          }
        ]
      }
    }
  ]
}
```

### Plan File

```json
[
  {
    "sobject": "Account",
    "saveRefs": true,
    "resolveRefs": false,
    "files": ["Account.json"]
  },
  {
    "sobject": "Contact",
    "saveRefs": false,
    "resolveRefs": true,
    "files": ["Contact.json"]
  }
]
```

---

## File-Converter Integration

Use the `file-converter` skill to transform Salesforce data between formats.

### Salesforce JSON → CSV

```bash
# Export from Salesforce as JSON
sf data query --target-org my-org \
  --query "SELECT Id, Name, Industry FROM Account LIMIT 200" \
  --json > accounts.json

# Convert to CSV for spreadsheets
python3 .claude/skills/file-converter/scripts/csv_json_yaml.py accounts.json accounts.csv
```

### CSV → JSON (for API import)

```bash
# Convert CSV data to JSON
python3 .claude/skills/file-converter/scripts/csv_json_yaml.py data.csv data.json
```

### JSON → YAML (for review/documentation)

```bash
python3 .claude/skills/file-converter/scripts/csv_json_yaml.py accounts.json accounts.yaml
```

### JSON → XML

```bash
python3 .claude/skills/file-converter/scripts/csv_json_yaml.py accounts.json accounts.xml
```

### Full Export Pipeline

```bash
# 1. Export data
sf data query --target-org my-org \
  --query "SELECT Id, Name, Industry, Website FROM Account LIMIT 500" \
  --result-format csv --output-file raw_accounts.csv

# 2. Convert to multiple formats
python3 .claude/skills/file-converter/scripts/csv_json_yaml.py raw_accounts.csv accounts.json
python3 .claude/skills/file-converter/scripts/csv_json_yaml.py raw_accounts.csv accounts.yaml
python3 .claude/skills/file-converter/scripts/csv_json_yaml.py raw_accounts.csv accounts.xml

# 3. Generate report
python3 .claude/skills/file-converter/scripts/md_to_pdf.py report.md report.pdf
```

### Data Migration Pipeline

```bash
# 1. Export from source org
sf data export bulk --target-org source-org \
  --query "SELECT Id, Name, Industry FROM Account" \
  --output-file source_accounts.csv

# 2. Transform data (e.g., remap fields via script)
python3 transform_data.py source_accounts.csv target_accounts.csv

# 3. Import to target org
sf data import bulk --target-org target-org \
  --sobject Account --file target_accounts.csv
```

---

## Bulk API Limits

| Limit | Value |
|-------|-------|
| Max file size per batch | 150 MB |
| Max batches per 24h rolling | 15,000 |
| Max records per batch | 10,000 |
| Max fields per record | 200 |
| Max characters per field | 32,000 |
| Max query result size | 1 GB |
| Concurrent bulk jobs | 100 |

---

## Safety Defaults for Data Operations

1. **Always LIMIT queries** used for export — prevent accidental full-table dumps
2. **Preview before import** — show first 5 rows to user before bulk operations
3. **Count before delete** — run COUNT query before bulk delete to show impact
4. **Export before modify** — for destructive operations, offer to export affected records first
5. **Validate CSV format** — check headers match sObject fields before import
6. **Check governor limits** — `sf limits api display` before large bulk operations
