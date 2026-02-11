# SOQL & SOSL Reference

Query patterns, date literals, aggregate functions, and safety rules for Salesforce queries.

## SOQL Patterns

### Basic Queries

```sql
-- Simple query (always include LIMIT)
SELECT Id, Name, Industry FROM Account WHERE Industry = 'Technology' LIMIT 100

-- Multiple conditions
SELECT Id, Name FROM Contact
  WHERE AccountId != null AND MailingCity = 'San Francisco'
  ORDER BY LastName ASC LIMIT 200

-- IN clause
SELECT Id, Name FROM Account WHERE Industry IN ('Technology', 'Finance', 'Healthcare') LIMIT 100

-- LIKE (wildcard)
SELECT Id, Name FROM Account WHERE Name LIKE 'Acme%' LIMIT 50
```

### Relationship Queries

```sql
-- Child-to-Parent (dot notation)
SELECT Id, Name, Account.Name, Account.Industry FROM Contact LIMIT 100

-- Parent-to-Child (subquery)
SELECT Id, Name, (SELECT Id, FirstName, LastName FROM Contacts) FROM Account LIMIT 50

-- Multi-level relationships (up to 5 levels)
SELECT Id, Contact.Account.Name FROM Case LIMIT 50
```

### Aggregate Queries

```sql
-- COUNT
SELECT COUNT(Id) total FROM Account WHERE Industry = 'Technology'

-- GROUP BY
SELECT Industry, COUNT(Id) cnt FROM Account GROUP BY Industry

-- SUM, AVG, MIN, MAX
SELECT StageName, SUM(Amount) total, AVG(Amount) avg_amount
  FROM Opportunity GROUP BY StageName

-- HAVING
SELECT Industry, COUNT(Id) cnt FROM Account
  GROUP BY Industry HAVING COUNT(Id) > 10
```

### Date Literals

| Literal | Description |
|---------|-------------|
| `TODAY` | Current day |
| `YESTERDAY` | Previous day |
| `THIS_WEEK` | Current week (Sun-Sat) |
| `LAST_WEEK` | Previous week |
| `THIS_MONTH` | Current month |
| `LAST_MONTH` | Previous month |
| `THIS_QUARTER` | Current quarter |
| `LAST_QUARTER` | Previous quarter |
| `THIS_YEAR` | Current year |
| `LAST_YEAR` | Previous year |
| `LAST_N_DAYS:n` | Last N days |
| `NEXT_N_DAYS:n` | Next N days |
| `LAST_N_MONTHS:n` | Last N months |
| `LAST_N_YEARS:n` | Last N years |
| `THIS_FISCAL_QUARTER` | Current fiscal quarter |
| `THIS_FISCAL_YEAR` | Current fiscal year |

```sql
-- Date literal examples
SELECT Id, Name FROM Opportunity WHERE CloseDate = THIS_QUARTER LIMIT 200
SELECT Id, Name FROM Account WHERE CreatedDate > LAST_N_DAYS:30 LIMIT 200
SELECT Id, Subject FROM Task WHERE ActivityDate = TODAY LIMIT 100
```

### Polymorphic Relationships (TYPEOF)

```sql
-- Query polymorphic fields
SELECT Id, Subject,
  TYPEOF What
    WHEN Account THEN Phone, Website
    WHEN Opportunity THEN Amount, StageName
  END
FROM Task LIMIT 100

-- Filter by polymorphic type
SELECT Id, What.Type, What.Name FROM Task WHERE What.Type = 'Account' LIMIT 100
```

### Tooling API Queries

Use `--use-tooling-api` flag for metadata queries.

```sql
-- List Apex classes
SELECT Id, Name, ApiVersion, LengthWithoutComments FROM ApexClass LIMIT 200

-- List Apex triggers
SELECT Id, Name, TableEnumOrId, Status FROM ApexTrigger LIMIT 100

-- Code coverage
SELECT ApexClassOrTriggerId, ApexClassOrTrigger.Name, NumLinesCovered, NumLinesUncovered
  FROM ApexCodeCoverageAggregate LIMIT 200

-- Custom objects
SELECT Id, DeveloperName, Label FROM CustomObject LIMIT 200

-- Validation rules
SELECT Id, EntityDefinition.DeveloperName, ValidationName, Active
  FROM ValidationRule LIMIT 200
```

### Advanced Patterns

```sql
-- Offset (pagination)
SELECT Id, Name FROM Account ORDER BY Name LIMIT 100 OFFSET 200

-- FOR UPDATE (record locking — use with caution)
SELECT Id, Name FROM Account WHERE Id = '001xx...' FOR UPDATE

-- WITH SECURITY_ENFORCED (FLS enforcement)
SELECT Id, Name FROM Account WITH SECURITY_ENFORCED LIMIT 100

-- ALL ROWS (include deleted records)
SELECT Id, Name, IsDeleted FROM Account WHERE IsDeleted = true ALL ROWS LIMIT 100

-- FIELDS(ALL) — returns all fields (avoid in production, use LIMIT 200 max)
SELECT FIELDS(ALL) FROM Account LIMIT 200

-- FIELDS(STANDARD) — standard fields only
SELECT FIELDS(STANDARD) FROM Account LIMIT 200
```

---

## SOSL Patterns

### Basic Search

```sql
-- Search across all fields
FIND {search term} IN ALL FIELDS
  RETURNING Account(Id, Name), Contact(Id, FirstName, LastName)

-- Search in specific fields
FIND {John Smith} IN NAME FIELDS
  RETURNING Contact(Id, Name, Phone, Email LIMIT 20)

-- Search with filters
FIND {Acme} RETURNING Account(Id, Name, Industry WHERE Industry = 'Technology' LIMIT 10)
```

### Search Scopes

| Scope | Description |
|-------|-------------|
| `IN ALL FIELDS` | Search all searchable fields |
| `IN NAME FIELDS` | Search Name fields only |
| `IN EMAIL FIELDS` | Search Email fields only |
| `IN PHONE FIELDS` | Search Phone fields only |
| `IN SIDEBAR FIELDS` | Search sidebar-configured fields |

### SOSL vs SOQL

| Scenario | Use |
|----------|-----|
| Know exact field to query | SOQL |
| Full-text search across objects | SOSL |
| Aggregate/GROUP BY needed | SOQL |
| Search multiple objects at once | SOSL |
| Complex WHERE clauses | SOQL |
| Fuzzy/partial text matching | SOSL |

---

## Governor Limits

| Limit | Synchronous | Asynchronous |
|-------|------------|--------------|
| SOQL queries per transaction | 100 | 200 |
| Records per SOQL query | 50,000 | 50,000 |
| SOSL queries per transaction | 20 | 20 |
| SOSL results per object | 2,000 | 2,000 |
| DML statements | 150 | 150 |
| DML rows | 10,000 | 10,000 |
| Query timeout | 120s | 120s |
| Heap size | 6 MB | 12 MB |
| CPU time | 10,000 ms | 60,000 ms |

---

## CLI Command Reference

```bash
# SOQL query w/ output formats
sf data query --target-org <alias> --query "SELECT ..." --result-format human|csv|json
sf data query --target-org <alias> --query "SELECT ..." --output-file output.csv --result-format csv
sf data query --target-org <alias> --file query.soql   # query from file

# SOSL search
sf data search --target-org <alias> --query "FIND {term} RETURNING ..."
sf data search --target-org <alias> --file search.sosl --result-format csv

# Tooling API
sf data query --target-org <alias> --use-tooling-api --query "SELECT ..."

# Bulk query (for >10,000 records)
sf data export bulk --target-org <alias> --query "SELECT ..." --output-file output.csv
```

## Indexed Fields (for performance)

Always filter on indexed fields for selective queries:
- `Id` (always indexed)
- `Name` (standard indexed)
- `CreatedDate`, `SystemModstamp` (indexed)
- Foreign key fields (lookups, master-detail)
- External ID fields (custom, marked as External ID)
- Custom fields marked as Unique

Avoid functions in WHERE clauses (e.g., `CALENDAR_YEAR(CreatedDate)`) — they prevent index usage.
