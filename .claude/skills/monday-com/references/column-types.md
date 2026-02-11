# Monday.com Column Value Formats

Reference for JSON formats when updating column values via `change_item_column_values` or `change_multiple_column_values`.

## Simple Columns (String Values)

These accept plain string values:

| Column Type | Example Value | Notes |
|-------------|---------------|-------|
| **Text** | `"Hello world"` | Plain text |
| **Long Text** | `"Multi-line\ntext"` | Supports newlines |
| **Number** | `"42"` or `"3.14"` | Numeric string |
| **Status** | `"Done"` | Must match label exactly |
| **Date** | `"2026-02-07"` | YYYY-MM-DD format |
| **Checkbox** | `"true"` or `"false"` | Boolean string |

## Complex Columns (JSON Values)

These require structured JSON:

### People Column
```json
{"personsAndTeams": [{"id": 4616666, "kind": "person"}, {"id": 51166, "kind": "team"}]}
```
Simple format: `"12345,67890"` (comma-separated user IDs)

### Dropdown Column
```json
{"ids": [3, 5]}
```
Values are dropdown option IDs (not labels). To find IDs, query the column settings.

### Email Column
```json
{"email": "user@example.com", "text": "Display Name"}
```

### Phone Column
```json
{"phone": "+1234567890", "countryShortName": "US"}
```

### Link Column
```json
{"url": "https://example.com", "text": "Click here"}
```

### Timeline Column
```json
{"from": "2026-01-01", "to": "2026-01-31"}
```

### Date Column (w/ time)
```json
{"date": "2026-02-07", "time": "14:30:00"}
```

### Rating Column
```json
{"rating": 4}
```
Value: 1-5 integer.

### Country Column
```json
{"countryCode": "US", "countryName": "United States"}
```

### Location Column
```json
{"lat": 40.7128, "lng": -74.0060, "address": "New York, NY"}
```

### World Clock Column
```json
{"timezone": "America/New_York"}
```

### Tags Column
```json
{"tag_ids": [123, 456]}
```

### Color Picker Column
```json
{"color": "#FF5733"}
```

## Clearing Column Values

To clear any column, send an empty JSON object:
```json
{}
```

Or use empty string for simple columns:
```json
""
```

## Full Mutation Example

```graphql
mutation {
  change_multiple_column_values(
    board_id: 1234567890,
    item_id: 9876543210,
    column_values: "{\"status\": \"Done\", \"date4\": \"2026-02-07\", \"text0\": \"Updated text\", \"people\": {\"personsAndTeams\": [{\"id\": 12345, \"kind\": \"person\"}]}}"
  ) {
    id
    name
  }
}
```

Note: The `column_values` argument is a JSON **string** — the entire JSON must be escaped and passed as a string value.