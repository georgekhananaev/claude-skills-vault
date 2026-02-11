# Monday.com Advanced Workflows

## Building a Workspace Dashboard

To generate a text-based dashboard from Monday.com data:

### Step 1: Fetch All Boards w/ Items

```graphql
{
  boards(limit: 50) {
    id name board_kind state
    groups { id title }
    items_page(limit: 200) {
      items {
        id name
        group { id title }
        column_values { id text type value }
      }
    }
  }
}
```

### Step 2: Parse the Response

For each board, extract:
- **Board name** and item count
- **Status distribution** — count items per status label from the status-type column's `text` field
- **Owner distribution** — count items per person from the people-type column's `text` field
- **Group breakdown** — items per group using `item.group.title`

### Step 3: Identify Column Types

Filter `column_values` by `type` to find relevant data:

| Type | What It Contains | Use For |
|------|-----------------|---------|
| `status` | Status label in `text` | Status distribution charts |
| `people` | Person names in `text`, IDs in `value` | Owner assignment stats |
| `date` | Date string in `text` | Due date tracking, overdue detection |
| `timeline` | Date range in `value` (from/to) | Sprint/timeline views |
| `numeric` | Number in `text` | Numeric aggregations |
| `text` | Plain text in `text` | Notes, descriptions |
| `last_updated` | Timestamp in `text` | Activity tracking |
| `subtasks` | Subitem reference | Nested task counts |

### Step 4: Present as Dashboard

Format the parsed data as markdown tables showing:
- Workspace summary (total boards, items, completion rate)
- Per-board breakdown (items by status)
- Status distribution (with ASCII bar chart)
- Item detail tables per board
- Key observations (unassigned items, missing dates, empty boards)

### Gotchas

- **Exclude subitem boards**: Filter out boards with names starting with "Subitems of" — these are auto-generated
- **Null status**: Items with `"text": null` on status columns have no status set (display as "Not Started" or "Unset")
- **Unicode names**: Hebrew/RTL names render correctly in `text` fields
- **Pagination**: If a board has >200 items, use cursor from `items_page` response to fetch more

---

## Understanding Monday.com Field Structure

### Board Hierarchy

```
Workspace
  └── Board (e.g. "Development Tasks")
        ├── Columns (define the schema — id, title, type)
        ├── Groups (horizontal sections — "To-Do", "In Progress", "Done")
        └── Items (rows/tasks)
              ├── Column Values (cell data — status, owner, date, etc.)
              └── Subitems (child items on a separate auto-generated board)
```

### Column ID vs Title

- **Column ID** (`id`): Machine identifier used in API calls. Examples: `project_status`, `date4`, `text0`
- **Column Title** (`title`): Human-readable name shown in UI. Examples: "Status", "Due date", "Notes"
- **Column Type** (`type`): Data type. Examples: `status`, `people`, `date`, `text`, `numeric`

Column IDs are **unique per board** and cannot be predicted. The same "Status" column might be `status` on one board and `project_status` on another.

### How to Map Fields

```
1. Query board schema:
   { boards(ids: [BID]) { columns { id title type } } }

2. Match by type + title to find the right column ID:
   - Need "Owner"?  → Find column where type="people"
   - Need "Status"? → Find column where type="status" AND title matches
   - Need "Due date"? → Find column where type="date"

3. Use the column ID in mutations
```

### Common Column Type Patterns

| UI Name | API Type | ID Pattern | Notes |
|---------|----------|------------|-------|
| Name | `name` | `name` | Always present, always this ID |
| Status | `status` | `status`, `project_status`, `status_1` | Multiple status columns possible |
| Owner/Person | `people` | `person`, `project_owner`, `people` | Can hold multiple people |
| Date | `date` | `date`, `date4`, `date0` | Single date |
| Timeline | `timeline` | `timerange`, `timeline` | Date range (from/to) |
| Priority | `status` | `priority`, `priority_1` | Same type as Status — it's a labeled dropdown |
| Text/Notes | `text` | `text`, `text0`, `text_1` | Free text |
| Numbers | `numeric` | `numbers`, `numeric` | Integers or decimals |
| Files | `file` | `file`, `files` | Attachments |
| Last Updated | `last_updated` | `pulse_updated` | Auto-managed timestamp |
| Subtasks | `subtasks` | `subitems`, `subtasks_*` | Link to subitem board |
| Checkbox | `checkbox` | `checkbox`, `check` | Boolean |

### Status Column Labels

Status columns use **labels** (strings), not indices. Common default labels:

| Label | Color (default) | Meaning |
|-------|----------------|---------|
| `"Working on it"` | Orange | In progress |
| `"Done"` | Green | Completed |
| `"Stuck"` | Red | Blocked |
| `""` or `null` | Gray | Not started |

Custom boards may have custom labels. To discover all available labels for a status column, check `settings_str` in the column schema:

```graphql
{ boards(ids: [BID]) { columns { id title type settings_str } } }
```

The `settings_str` JSON contains a `labels` object mapping index to label text.

---

## Complex Batch Operations

### Create Multiple Items w/ Full Details

```graphql
mutation {
  t1: create_item(board_id: BID, group_id: "GID", item_name: "Task 1",
    column_values: "{\"PEOPLE_COL\": {\"personsAndTeams\": [{\"id\": UID, \"kind\": \"person\"}]}, \"STATUS_COL\": \"Working on it\", \"DATE_COL\": \"2026-03-01\"}") { id }
  t2: create_item(board_id: BID, group_id: "GID", item_name: "Task 2",
    column_values: "{\"PEOPLE_COL\": {\"personsAndTeams\": [{\"id\": UID, \"kind\": \"person\"}]}, \"STATUS_COL\": \"\", \"DATE_COL\": \"2026-03-15\"}") { id }
  t3: create_item(board_id: BID, group_id: "GID", item_name: "Task 3",
    column_values: "{\"PEOPLE_COL\": {\"personsAndTeams\": [{\"id\": UID, \"kind\": \"person\"}]}}") { id }
}
```

### Bulk Delete Items

```graphql
mutation {
  d1: delete_item(item_id: ID1) { id }
  d2: delete_item(item_id: ID2) { id }
  d3: delete_item(item_id: ID3) { id }
}
```

### Move Items Between Groups (e.g., To-Do → Done)

```graphql
mutation {
  m1: move_item_to_group(item_id: ID1, group_id: "completed_group") { id }
  m2: move_item_to_group(item_id: ID2, group_id: "completed_group") { id }
}
```

### Cross-Board Item Transfer

```graphql
mutation {
  move_item_to_board(
    item_id: ITEM_ID,
    board_id: TARGET_BOARD_ID,
    group_id: "target_group",
    columns_mapping: [
      { source: "status", target: "project_status" },
      { source: "person", target: "project_owner" },
      { source: "date4", target: "date" }
    ]
  ) { id }
}
```

Note: `columns_mapping` is required when column IDs differ between boards. If omitted, Monday.com tries to auto-map by name and type.

---

## Sprint/Project Management Patterns

### Filter Items by Status

```graphql
{
  items_page_by_column_values(
    board_id: BID,
    limit: 100,
    columns: [{ column_id: "STATUS_COL", column_values: ["Working on it", "Stuck"] }]
  ) {
    items { id name column_values { id text type } }
  }
}
```

### Get Overdue Items

Query all items, then filter in code where:
- `date` column `text` < today's date
- `status` column `text` != "Done"

### Add Comment to Item

```graphql
mutation {
  create_update(item_id: ITEM_ID, body: "Sprint review: on track for delivery") { id }
}
```

### Create Subitem Under a Task

```graphql
mutation {
  create_subitem(
    parent_item_id: PARENT_ID,
    item_name: "Sub-task: Write tests",
    column_values: "{\"STATUS_COL\": \"\"}"
  ) { id board { id } }
}
```

Note: Subitems live on a separate auto-generated board. Column IDs on the subitem board are different from the parent board.

---

## Webhooks (Event-Driven Automation)

### Create a Webhook for Status Changes

```graphql
mutation {
  create_webhook(
    board_id: BID,
    url: "https://your-server.com/webhook",
    event: change_status_column_value,
    config: "{\"columnId\": \"STATUS_COL\"}"
  ) { id board_id }
}
```

### Supported Events

| Event | Trigger |
|-------|---------|
| `change_column_value` | Any column value change |
| `change_status_column_value` | Status column change |
| `create_item` | New item created |
| `item_archived` | Item archived |
| `item_deleted` | Item deleted |
| `create_subitem` | Subitem created |
| `create_update` | Comment/update added |

---

## Rate Limits & Complexity

### Checking Query Complexity

Add `complexity` to any query/mutation to see cost:

```graphql
{
  complexity { before after query reset_in_x_seconds }
  boards(ids: [BID]) { items_page(limit: 50) { items { id name } } }
}
```

### Budget

| Account Type | Points/Min |
|-------------|------------|
| Free/Trial | 1,000,000 |
| Paid | 10,000,000 |

### Reducing Complexity

- Fewer fields = lower cost
- Lower `limit` values = lower cost
- Avoid deep nesting (items → subitems → column_values)
- Use `items_page` with cursor instead of fetching all at once
