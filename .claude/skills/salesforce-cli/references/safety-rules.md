# Safety Rules — Salesforce CLI

Risk classification, confirmation templates, and production guardrails for `sf` operations.

## Core Principle

**NEVER modify Salesforce data, metadata, or org configuration without explicit user permission via AskUserQuestion.** Read-only operations are the only exception.

## Org Type Detection (Mandatory First Step)

Before ANY non-safe operation, detect the org type:

```bash
sf org display --target-org <alias> --json
```

Parse the JSON response:
- `isScratch: true` → **Scratch org** (lowest risk)
- `isSandbox: true` or `instanceUrl` contains `test.salesforce.com` or `--cs` → **Sandbox** (medium risk)
- Neither flag set, `instanceUrl` is `login.salesforce.com` or custom domain → **PRODUCTION** (highest risk)

### Risk Multiplier by Org Type

| Operation Tier | Scratch | Sandbox | Production |
|---------------|---------|---------|------------|
| Safe | Execute | Execute | Execute |
| Write | AskUserQuestion | AskUserQuestion | AskUserQuestion + org confirmation |
| Destructive | AskUserQuestion | AskUserQuestion + consequences | AskUserQuestion + consequences + typed alias |
| Forbidden | AskUserQuestion | Block w/ warning | Block — require 3-step validation |

---

## Safe Operations (Execute Immediately)

All read-only commands. No side effects, no confirmation needed.

```
sf org list [--all]
sf org display [--target-org <alias>] [--json]
sf org open [--target-org <alias>]

sf data query --target-org <alias> --query "... LIMIT N"
sf data search --target-org <alias> --query "..."
sf data get record --target-org <alias> --sobject <obj> --record-id <id>

sf project retrieve preview --target-org <alias>
sf project deploy preview --target-org <alias>

sf apex list log [--target-org <alias>]
sf apex get log [--target-org <alias>] [--number N]
sf apex tail log [--target-org <alias>]

sf api request rest <GET endpoint>

sf limits api display [--target-org <alias>]
sf schema generate sobject --sobject <name> [--target-org <alias>]

sf config list
sf config get <key>
sf alias list
sf auth list

sf package list [--target-org <alias>]
sf package version list [--target-org <alias>]
sf plugins list

sf doctor
```

### Query Safety (applies to Safe operations)

Even though queries are Safe, enforce these rules:

1. **Mandatory LIMIT**: If user omits LIMIT, add `LIMIT 200` automatically
2. **No `SELECT *`**: Block and ask user to specify fields, or use `sf schema generate sobject` to show available fields
3. **Production WHERE**: For production orgs, require a WHERE clause unless the object is known to have <1000 records
4. **PII Warning**: If query includes fields like Email, Phone, SSN, BirthDate — warn the user that PII will be displayed

---

## Write Operations (AskUserQuestion Required)

These create or modify resources. Confirm before execution.

---

### `sf data create record`

**AskUserQuestion template:**

```
question: "Create a new <sObject> record in <org-alias> (<org-type>)?\n\nFields: <field=value pairs>"
header: "SF Create"
options:
  - label: "Create record"
    description: "Insert the record with the specified field values"
  - label: "Cancel"
    description: "Do not create any records"
```

**Execution:** `sf data create record --sobject <obj> --values "<fields>" --target-org <alias>`

---

### `sf data update record`

**AskUserQuestion template:**

```
question: "Update <sObject> record <record-id> in <org-alias> (<org-type>)?\n\nChanges: <field=value pairs>"
header: "SF Update"
options:
  - label: "Update record"
    description: "Modify the specified fields on this record"
  - label: "Cancel"
    description: "Do not modify anything"
```

**Execution:** `sf data update record --sobject <obj> --record-id <id> --values "<fields>" --target-org <alias>`

---

### `sf data import tree`

**AskUserQuestion template:**

```
question: "Import data from tree files into <org-alias> (<org-type>)?\n\nFiles: <file list>\nRecords: <estimated count>"
header: "SF Import"
options:
  - label: "Import data"
    description: "Insert records from the specified tree files"
  - label: "Preview first"
    description: "Show me the data before importing"
  - label: "Cancel"
    description: "Do not import anything"
```

---

### `sf data import bulk` / `sf data upsert bulk`

**AskUserQuestion template:**

```
question: "Bulk <import/upsert> <N> records into <sObject> in <org-alias> (<org-type>)?\n\nFile: <filename>\nOperation: <insert/upsert>"
header: "SF Bulk"
options:
  - label: "Proceed with bulk operation"
    description: "<N> records will be <inserted/upserted> into <sObject>"
  - label: "Preview sample rows"
    description: "Show me the first 5 rows before proceeding"
  - label: "Cancel"
    description: "Do not perform the bulk operation"
```

---

### `sf project deploy start --dry-run`

**AskUserQuestion template:**

```
question: "Validate deployment to <org-alias> (<org-type>)? This is a dry-run — no changes will be made."
header: "SF Validate"
options:
  - label: "Validate (dry-run)"
    description: "Run validation without modifying the org"
  - label: "Cancel"
    description: "Do not validate"
```

---

### `sf project retrieve start`

**AskUserQuestion template:**

```
question: "Retrieve metadata from <org-alias> (<org-type>) to local project?\n\nSource: <source-dir or metadata types>"
header: "SF Retrieve"
options:
  - label: "Retrieve"
    description: "Download metadata — local files may be overwritten"
  - label: "Preview first"
    description: "Run retrieve preview to see what will change"
  - label: "Cancel"
    description: "Do not retrieve"
```

---

### `sf org create scratch`

**AskUserQuestion template:**

```
question: "Create a new scratch org?\n\nDefinition: <def-file>\nAlias: <alias>\nDuration: <N> days"
header: "SF Scratch"
options:
  - label: "Create scratch org"
    description: "Create a new scratch org with the specified configuration"
  - label: "Cancel"
    description: "Do not create"
```

---

### `sf org assign permset`

**AskUserQuestion template:**

```
question: "Assign permission set '<permset-name>' to user in <org-alias> (<org-type>)?"
header: "SF Permset"
options:
  - label: "Assign"
    description: "Grant the permission set to the specified user"
  - label: "Cancel"
    description: "Do not assign"
```

---

### `sf package install`

**AskUserQuestion template:**

```
question: "Install package <package-id> in <org-alias> (<org-type>)?"
header: "SF Package"
options:
  - label: "Install"
    description: "Install the package — this may add metadata and data to the org"
  - label: "Cancel"
    description: "Do not install"
```

---

## Destructive Operations (AskUserQuestion w/ Consequences)

Each operation requires explicit confirmation showing what will change and potential impact.

---

### `sf project deploy start` (actual deploy, no dry-run)

**AskUserQuestion template:**

```
question: "Deploy metadata to <org-alias> (<org-type>)?\n\n<N> components will be modified.\nTest level: <test-level>\n\nThis will modify the target org."
header: "SF Deploy"
options:
  - label: "Validate only (dry-run)"
    description: "Run validation without making changes (recommended first step)"
  - label: "Deploy now"
    description: "Deploy and modify the target org"
  - label: "Cancel"
    description: "Do not deploy"
```

**For production:** Add extra option and warning:

```
question: "⚠ PRODUCTION DEPLOY to <org-alias>.\n\n<N> components will be modified.\nTest level: RunLocalTests (enforced)\n\nType the org alias to confirm."
header: "PROD Deploy"
options:
  - label: "Validate only (recommended)"
    description: "Run validation in production without deploying"
  - label: "Deploy to production"
    description: "Deploy changes to production — this cannot be easily undone"
  - label: "Cancel"
    description: "Do not deploy to production"
```

---

### `sf data delete record`

**AskUserQuestion template:**

```
question: "Delete <sObject> record <record-id> from <org-alias> (<org-type>)?\n\nRecord: <Name or identifier>"
header: "SF Delete"
options:
  - label: "Delete record"
    description: "Permanently remove this record (may be recoverable from Recycle Bin)"
  - label: "Cancel"
    description: "Do not delete"
```

---

### `sf data delete bulk`

**AskUserQuestion template:**

```
question: "Bulk delete <N> <sObject> records from <org-alias> (<org-type>)?\n\nFile: <filename>"
header: "SF Bulk Del"
options:
  - label: "Delete <N> records"
    description: "Records will be moved to Recycle Bin (recoverable for 15 days)"
  - label: "Preview IDs"
    description: "Show me the record IDs before deleting"
  - label: "Cancel"
    description: "Do not delete any records"
```

---

### `sf data update bulk`

**AskUserQuestion template:**

```
question: "Bulk update <N> <sObject> records in <org-alias> (<org-type>)?\n\nFile: <filename>"
header: "SF Bulk Upd"
options:
  - label: "Update <N> records"
    description: "Modify the specified fields on all records in the file"
  - label: "Preview sample rows"
    description: "Show me the first 5 rows before proceeding"
  - label: "Cancel"
    description: "Do not update any records"
```

---

### `sf apex run`

**MANDATORY: Always display the Apex code to the user BEFORE this confirmation.**

**AskUserQuestion template:**

```
question: "Execute the Apex code shown above in <org-alias> (<org-type>)?"
header: "SF Apex"
options:
  - label: "Execute"
    description: "Run the Apex code in the target org"
  - label: "Cancel"
    description: "Do not execute any Apex"
```

**For production:**

```
question: "⚠ PRODUCTION APEX EXECUTION in <org-alias>.\n\nThe code above will run in your production environment.\nType the org alias to confirm."
header: "PROD Apex"
options:
  - label: "Execute in production"
    description: "Run Apex in production — changes may be irreversible"
  - label: "Cancel"
    description: "Do not execute"
```

---

### `sf org delete scratch`

**AskUserQuestion template:**

```
question: "Delete scratch org '<alias>'?"
header: "SF Org Del"
options:
  - label: "Delete scratch org"
    description: "Remove the scratch org and all its data"
  - label: "Cancel"
    description: "Keep the scratch org"
```

---

### `sf org delete sandbox`

**AskUserQuestion template:**

```
question: "Delete sandbox '<alias>'? This will remove all data and customizations in the sandbox."
header: "SF Sandbox"
options:
  - label: "Delete sandbox"
    description: "Permanently remove the sandbox environment"
  - label: "Cancel"
    description: "Keep the sandbox"
```

---

### `sf org create sandbox`

**AskUserQuestion template:**

```
question: "Create a new sandbox from <prod-org>?\n\nName: <name>\nType: <Developer|Developer Pro|Partial|Full>\nAlias: <alias>"
header: "SF Sandbox"
options:
  - label: "Create sandbox"
    description: "This may take minutes to hours depending on sandbox type"
  - label: "Cancel"
    description: "Do not create"
```

---

### `sf org refresh sandbox` (Forbidden-level — data wipe)

**Sandbox refresh destroys ALL data and customizations.** Treat as Forbidden tier.

**Step 1 — Warn:**

> Refreshing sandbox '<alias>' will DESTROY:
> - All data in the sandbox (records, files, attachments)
> - All customizations not in source control
> - All test data and configurations
> - All user settings and debug logs
>
> This is equivalent to deleting and recreating the sandbox.

**Step 2 — Require typed confirmation of sandbox alias.**

**Step 3 — AskUserQuestion:**

```
question: "FINAL CONFIRMATION: Refresh sandbox '<alias>'? ALL data and customizations will be permanently destroyed and replaced with a fresh copy from production."
header: "DANGER"
options:
  - label: "Export data first"
    description: "Export important data before refreshing"
  - label: "Refresh sandbox"
    description: "Destroy all current sandbox data and replace with production copy"
  - label: "Cancel"
    description: "Keep current sandbox state"
```

---

### `sf package uninstall`

**AskUserQuestion template:**

```
question: "Uninstall package from <org-alias> (<org-type>)?\n\nPackage: <package-name>"
header: "SF Uninstall"
options:
  - label: "Uninstall"
    description: "Remove the package and its components from the org"
  - label: "Cancel"
    description: "Keep the package installed"
```

---

### `sf org logout`

**AskUserQuestion template:**

```
question: "Remove authentication for org '<alias>'?"
header: "SF Logout"
options:
  - label: "Log out"
    description: "Remove stored credentials — you'll need to re-authenticate"
  - label: "Cancel"
    description: "Keep authentication"
```

---

### `sf api request rest` (POST/PUT/PATCH/DELETE)

**AskUserQuestion template:**

```
question: "Execute <METHOD> request to <endpoint> in <org-alias> (<org-type>)?"
header: "SF API"
options:
  - label: "Execute"
    description: "Send the <METHOD> request to the Salesforce REST API"
  - label: "Cancel"
    description: "Do not send the request"
```

---

## Forbidden Operations (Triple Confirmation Protocol)

These operations are extremely dangerous. NEVER auto-confirm.

### Protocol: 3-Step Validation

1. **Step 1 — Warn:** Explain consequences clearly w/ bullet points
2. **Step 2 — Typed confirmation:** Ask user to type the org alias or identifier
3. **Step 3 — Final confirm:** AskUserQuestion w/ explicit options

---

### Bulk Delete in Production

**Step 1 — Warn the user:**

> Bulk deleting records in production is extremely dangerous:
> - Records will be in Recycle Bin for 15 days, then permanently lost
> - Related records, files, and history may be affected
> - Cascade deletes may remove child records
> - This can trigger automation (workflows, flows, triggers) at scale
>
> Consider exporting data first as a backup.

**Step 2 — Require typed confirmation:**

Ask the user to type the production org alias to confirm.

**Step 3 — Final confirm (AskUserQuestion):**

```
question: "FINAL CONFIRMATION: Bulk delete <N> <sObject> records from PRODUCTION (<org-alias>)?"
header: "DANGER"
options:
  - label: "I understand, delete records"
    description: "Permanently delete <N> records from production"
  - label: "Export backup first"
    description: "Export affected records before deleting"
  - label: "Cancel"
    description: "Do NOT delete any records"
```

---

### Deploy Destructive Changes to Production

**Step 1 — Warn the user:**

> Deploying destructive changes to production will PERMANENTLY REMOVE metadata:
> - Deleted components cannot be recovered from Salesforce
> - Users may lose access to features
> - Dependent automation and integrations may break
> - This should only be done after thorough testing in sandbox
>
> Ensure you have a backup of all affected components.

**Step 2 — Require typed confirmation of org alias.**

**Step 3 — Final confirm (AskUserQuestion):**

```
question: "FINAL CONFIRMATION: Deploy destructive changes to PRODUCTION (<org-alias>)?\n\n<list of components being destroyed>"
header: "DANGER"
options:
  - label: "Deploy destructive changes"
    description: "Remove the listed components from production"
  - label: "Validate only"
    description: "Run validation without deploying"
  - label: "Cancel"
    description: "Do NOT deploy destructive changes"
```

---

### Execute Unreviewed Apex in Production

**Step 1 — Warn the user:**

> Executing Apex in production can cause irreversible damage:
> - DML operations modify live data
> - System.callout affects external systems
> - Governor limits apply — bulk operations can fail mid-transaction
> - No automatic rollback if script fails partway
>
> ALWAYS review the code carefully before execution.

**Step 2 — Display the complete Apex code and require user to confirm they've reviewed it.**

**Step 3 — Final confirm (AskUserQuestion):**

```
question: "FINAL CONFIRMATION: Execute Apex in PRODUCTION (<org-alias>)?"
header: "DANGER"
options:
  - label: "Execute in production"
    description: "Run the reviewed Apex code in production"
  - label: "Run in sandbox first"
    description: "Execute in a sandbox environment for testing"
  - label: "Cancel"
    description: "Do NOT execute"
```

---

### `sf org logout --all` (Forbidden — can break CI/CD)

**Step 1 — Warn:**

> Logging out of ALL orgs will remove ALL stored authentication:
> - Every authorized org connection will be removed
> - CI/CD pipelines that depend on local auth will fail
> - You will need to re-authenticate each org individually
>
> Consider using `sf org logout --target-org <alias>` to remove a single org instead.

**Step 2 — Require typed confirmation: user must type "LOGOUT ALL".**

**Step 3 — AskUserQuestion:**

```
question: "FINAL CONFIRMATION: Remove ALL Salesforce org authentication?"
header: "DANGER"
options:
  - label: "Remove single org instead"
    description: "I'll specify which org to log out of"
  - label: "Log out of all orgs"
    description: "Remove all stored auth — will need to re-authenticate everything"
  - label: "Cancel"
    description: "Keep all authentication"
```

---

### Dangerous Deploy Flags (Forbidden in production)

The following flags bypass safety mechanisms and are FORBIDDEN for production deployments:

- `--ignore-conflicts` — Skips conflict detection, can overwrite production changes
- `--ignore-warnings` — Hides deployment warnings that may indicate breaking changes
- `--purge-on-delete` — Permanently removes deleted metadata from Recycle Bin

If user requests these flags for production, BLOCK and explain the risks.

---

## Cascade Impact Warnings

### Permission Set Changes

When assigning or removing permission sets (`sf org assign permset`), warn about:

- **Privilege escalation**: Granting "Modify All Data", "View All Data", or "Manage Users" permissions
- **Lockout risk**: Removing permission sets that grant access to essential objects or apps
- **Profile conflicts**: Permission sets that override restrictive profile settings

Always show what permissions will be granted/removed before confirming.

### Field/Object Deletions in Deploys

When a deployment includes metadata deletions (via `destructiveChanges.xml`), warn about cascade impacts:

- **Reports & Dashboards**: Reports referencing deleted fields will break
- **Flows & Process Builder**: Automations using deleted fields/objects will fail
- **Validation Rules**: Rules referencing deleted fields become inactive
- **Apex Code**: Classes/triggers referencing deleted schema will fail to compile
- **Integrations**: External systems reading deleted fields will receive errors
- **List Views**: Views filtering on deleted fields will break
- **Page Layouts**: Layouts referencing deleted fields lose those sections

Always list ALL components being deleted and warn about potential cascade impacts.

### Package Install Impact

When installing packages (`sf package install`), warn about:

- **Schema modifications**: Packages can add custom objects, fields, and relationships
- **Automation**: Post-install scripts can modify data and create records
- **Apex code**: Package Apex runs in the org's context and can modify data
- **Dependencies**: Uninstalling may not be possible if other metadata depends on package components

---

## Edge Cases

### Org Alias Ambiguity

If the target org alias could be production (e.g., named "prod", "production", "live", or any custom alias pointing to `login.salesforce.com`), always verify:

```bash
sf org display --target-org <alias> --json
```

### Cascading Operations

When a single command triggers multiple changes (e.g., deploying a destructive manifest that removes objects with dependent fields, relationships, and automation), list ALL affected components before confirmation.

### Bulk Operations Without Limits

NEVER execute a loop of write/delete operations without:
1. A total count confirmation
2. A LIMIT on the source query
3. Batch confirmation from the user

### Auth Token Security

- Never display `sf org display` output that contains `accessToken` to the user
- When displaying org info, use `--json` and filter out sensitive fields
- Never log or echo SFDX Auth URLs, JWT keys, or access tokens

### Governor Limits Awareness

Before bulk operations, check limits:

```bash
sf limits api display --target-org <alias>
```

Warn if API calls remaining is below 20% of the daily limit.
