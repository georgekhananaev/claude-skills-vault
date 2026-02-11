# Monday.com GraphQL Examples

Direct GraphQL queries/mutations for use w/ Dynamic API Tools (`all_monday_api`) or the `monday_api.sh` script.

API endpoint: `https://api.monday.com/v2`

## IMPORTANT: Column IDs Are Per-Board

Column IDs differ between boards (`status` vs `project_status`, `person` vs `project_owner`).
**Always query board schema first** to discover the correct column IDs before any mutation.

## Queries

### List Boards
```graphql
{ boards(limit: 25) { id name state board_kind } }
```

### Get Board Schema (ALWAYS DO THIS FIRST)
```graphql
{
  boards(ids: [BOARD_ID]) {
    name
    columns { id title type settings_str }
    groups { id title color }
  }
}
```

### Get Users (for people column assignments)
```graphql
{ users { id name email } }
```

### Get Current User
```graphql
{ me { id name email } }
```

### Get Board Items w/ Column Values
```graphql
{
  boards(ids: [BOARD_ID]) {
    items_page(limit: 50) {
      cursor
      items {
        id name group { id title }
        column_values { id text type value }
      }
    }
  }
}
```

Note: `column_values` does NOT have a `title` field. Use `id`, `text`, `type`, `value`.

### Paginate Items (cursor-based)
```graphql
{
  boards(ids: [BOARD_ID]) {
    items_page(limit: 50, cursor: "CURSOR_FROM_PREV") {
      cursor
      items { id name column_values { id text } }
    }
  }
}
```

### Search Items by Column Value
```graphql
{
  items_page_by_column_values(
    board_id: BOARD_ID,
    limit: 25,
    columns: [{ column_id: "STATUS_COL_ID", column_values: ["Done"] }]
  ) {
    items { id name column_values { id text } }
  }
}
```

### Get Specific Item
```graphql
{ items(ids: [ITEM_ID]) { id name column_values { id text value type } } }
```

### List Teams
```graphql
{ teams { id name users { id name } } }
```

### Get Item Updates (Comments)
```graphql
{ items(ids: [ITEM_ID]) { updates(limit: 10) { id body creator { name } created_at } } }
```

## Mutations

### Create Item w/ Owner & Status
```graphql
mutation {
  create_item(
    board_id: BOARD_ID,
    group_id: "GROUP_ID",
    item_name: "New Task",
    column_values: "{\"PEOPLE_COL_ID\": {\"personsAndTeams\": [{\"id\": USER_ID, \"kind\": \"person\"}]}, \"STATUS_COL_ID\": \"Working on it\", \"DATE_COL_ID\": \"2026-02-07\"}"
  ) { id name }
}
```

### Assign Owner to Existing Item
```graphql
mutation {
  change_multiple_column_values(
    board_id: BOARD_ID,
    item_id: ITEM_ID,
    column_values: "{\"PEOPLE_COL_ID\": {\"personsAndTeams\": [{\"id\": USER_ID, \"kind\": \"person\"}]}}"
  ) { id }
}
```

### Assign Owner to Multiple Items (batch)
```graphql
mutation {
  t1: change_multiple_column_values(board_id: BID, item_id: ID1, column_values: "{\"PEOPLE_COL_ID\": {\"personsAndTeams\": [{\"id\": UID, \"kind\": \"person\"}]}}") { id }
  t2: change_multiple_column_values(board_id: BID, item_id: ID2, column_values: "{\"PEOPLE_COL_ID\": {\"personsAndTeams\": [{\"id\": UID, \"kind\": \"person\"}]}}") { id }
  t3: change_multiple_column_values(board_id: BID, item_id: ID3, column_values: "{\"PEOPLE_COL_ID\": {\"personsAndTeams\": [{\"id\": UID, \"kind\": \"person\"}]}}") { id }
}
```

### Update Multiple Columns at Once
```graphql
mutation {
  change_multiple_column_values(
    board_id: BOARD_ID,
    item_id: ITEM_ID,
    column_values: "{\"STATUS_COL_ID\": \"Done\", \"TEXT_COL_ID\": \"Updated\", \"PEOPLE_COL_ID\": {\"personsAndTeams\": [{\"id\": USER_ID, \"kind\": \"person\"}]}}"
  ) { id name }
}
```

### Change Single Column (Simple)
```graphql
mutation {
  change_simple_column_value(
    board_id: BOARD_ID,
    item_id: ITEM_ID,
    column_id: "STATUS_COL_ID",
    value: "Done"
  ) { id }
}
```

### Create Item w/ Subitem
```graphql
mutation {
  create_subitem(
    parent_item_id: PARENT_ITEM_ID,
    item_name: "Sub-task"
  ) { id name board { id } }
}
```

### Move Item to Group
```graphql
mutation {
  move_item_to_group(item_id: ITEM_ID, group_id: "new_group") { id }
}
```

### Move Item to Board
```graphql
mutation {
  move_item_to_board(
    item_id: ITEM_ID,
    board_id: TARGET_BOARD_ID,
    group_id: "target_group"
  ) { id }
}
```

### Delete Item
```graphql
mutation { delete_item(item_id: ITEM_ID) { id } }
```

### Archive Item
```graphql
mutation { archive_item(item_id: ITEM_ID) { id } }
```

### Add Comment/Update
```graphql
mutation {
  create_update(item_id: ITEM_ID, body: "Comment text here") { id }
}
```

### Create Board
```graphql
mutation {
  create_board(
    board_name: "New Board",
    board_kind: public,
    workspace_id: WORKSPACE_ID
  ) { id }
}
```

### Create Group
```graphql
mutation {
  create_group(board_id: BOARD_ID, group_name: "New Group") { id }
}
```

### Create Column
```graphql
mutation {
  create_column(
    board_id: BOARD_ID,
    title: "Priority",
    column_type: status
  ) { id }
}
```

### Delete Column
```graphql
mutation {
  delete_column(board_id: BOARD_ID, column_id: "COLUMN_ID") { id }
}
```

### Archive Board
```graphql
mutation { archive_board(board_id: BOARD_ID) { id } }
```

### Duplicate Item
```graphql
mutation {
  duplicate_item(
    board_id: BOARD_ID,
    item_id: ITEM_ID,
    with_updates: true
  ) { id }
}
```

## Rate Limits

- **Complexity budget**: 10,000,000 points/min per account
- Each query/mutation has a complexity cost based on fields requested
- Check remaining budget in response headers
- On `429 Too Many Requests`: wait 60s before retrying

## Query Complexity Tips

- Request only needed fields (avoid `*`)
- Use `limit` param on all list queries
- Use cursor-based pagination (`items_page`) instead of offset
- Batch mutations with aliases (t1:, t2:, t3:) in a single request
