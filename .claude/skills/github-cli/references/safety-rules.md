# Safety Rules — GitHub CLI

Risk classification and confirmation templates for common `gh` operations.

## Safe Operations (Execute Immediately)

All read-only commands. No side effects, no confirmation needed.

**Note:** `gh auth token` prints the active token. Never display its output to the user or log it. Pipe to clipboard or a variable if needed.

```
gh auth status

gh pr list [--state] [--label] [--assignee] [--author] [--limit]
gh pr view <number> [--json] [--comments]
gh pr checks <number>
gh pr diff <number>
gh pr status

gh issue list [--state] [--label] [--assignee] [--author] [--limit]
gh issue view <number> [--json] [--comments]
gh issue status

gh repo view [owner/repo] [--json]
gh repo list [owner] [--limit]
gh repo clone <repo>

gh release list [--limit]
gh release view <tag> [--json]

gh run list [--limit] [--status] [--workflow]
gh run view <run-id> [--log] [--log-failed] [--json]
gh run download <run-id>

gh workflow list
gh workflow view <id>

gh label list [--limit]

gh search repos <query>
gh search issues <query>
gh search prs <query>
gh search code <query>
gh search commits <query>

gh api <endpoint>                     # GET only
gh api repos/{owner}/{repo}/pulls
gh api repos/{owner}/{repo}/issues
gh api repos/{owner}/{repo}/actions/runs

gh browse [--no-browser]              # Opens URL, no side effects
gh status                             # Dashboard
gh gist list
gh gist view <id>
```

## Write Operations (Inform User, Then Execute)

These create or modify resources. Tell the user what will happen before running.

```
gh pr create --title "..." --body "..."
gh pr edit <number> [--title] [--body] [--add-label] [--add-assignee]
gh pr comment <number> --body "..."
gh pr review <number> [--approve | --request-changes | --comment] --body "..."
gh pr ready <number>
gh pr checkout <number>

gh issue create --title "..." --body "..."
gh issue edit <number> [--title] [--body] [--add-label] [--add-assignee]
gh issue comment <number> --body "..."
gh issue reopen <number>
gh issue pin <number>
gh issue unpin <number>

gh label create <name> --color <hex>
gh label edit <name> [--name] [--color] [--description]

gh release create <tag> [--title] [--notes] [--generate-notes] [files...]
gh release edit <tag> [--title] [--notes]

gh repo create <name> [--public | --private] [--clone]
gh repo edit [--description] [--homepage] [--default-branch]
gh repo fork [owner/repo] [--clone]
gh repo rename <new-name>

gh run rerun <run-id> [--failed]
gh workflow enable <id>
gh workflow disable <id>
gh workflow run <id> [--ref]

gh secret set <name> [--body]
gh variable set <name> [--body]

gh gist create <files...>
gh gist edit <id>

gh api <endpoint> -X POST -f key=value
gh api <endpoint> -X PUT -f key=value
gh api <endpoint> -X PATCH -f key=value
```

**Note:** `gh api` with `-f` or `--input` defaults to POST even without `-X`. Treat any `gh api` call with `-f`/`-F`/`--input` as a Write operation.

## Destructive Operations (AskUserQuestion Required)

Each operation below requires explicit user confirmation via `AskUserQuestion` BEFORE execution.

---

### `gh pr merge`

Merging is irreversible in most workflows. Always confirm merge strategy.

**AskUserQuestion template:**

```
question: "How should PR #<number> '<title>' be merged?"
header: "PR Merge"
options:
  - label: "Squash and merge"
    description: "Combine all commits into one on the base branch"
  - label: "Create merge commit"
    description: "Preserve full commit history with a merge commit"
  - label: "Rebase and merge"
    description: "Rebase commits onto the base branch (linear history)"
  - label: "Cancel"
    description: "Do not merge this PR"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Squash and merge | `gh pr merge <n> --squash --delete-branch` |
| Create merge commit | `gh pr merge <n> --merge --delete-branch` |
| Rebase and merge | `gh pr merge <n> --rebase --delete-branch` |
| Cancel | No action |

Note: Include `--delete-branch` by default. If the user's "Other" response says keep the branch, omit it.

---

### `gh pr close`

**AskUserQuestion template:**

```
question: "Close PR #<number> '<title>'?"
header: "PR Close"
options:
  - label: "Close only"
    description: "Close the PR, keep the source branch"
  - label: "Close and delete branch"
    description: "Close the PR and delete the source branch"
  - label: "Cancel"
    description: "Keep the PR open"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Close only | `gh pr close <n>` |
| Close and delete branch | `gh pr close <n> --delete-branch` |
| Cancel | No action |

---

### `gh issue close`

**AskUserQuestion template:**

```
question: "Close issue #<number> '<title>'?"
header: "Issue Close"
options:
  - label: "Close as completed"
    description: "Mark the issue as resolved"
  - label: "Close as not planned"
    description: "Close without resolution (won't fix)"
  - label: "Cancel"
    description: "Keep the issue open"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Close as completed | `gh issue close <n> --reason completed` |
| Close as not planned | `gh issue close <n> --reason "not planned"` |
| Cancel | No action |

---

### `gh issue delete`

This is **permanent** — the issue cannot be recovered.

**AskUserQuestion template:**

```
question: "PERMANENTLY delete issue #<number> '<title>'? This cannot be undone."
header: "Issue Delete"
options:
  - label: "Delete permanently"
    description: "The issue and all comments will be permanently removed"
  - label: "Close instead"
    description: "Close the issue (reversible, preserves history)"
  - label: "Cancel"
    description: "Take no action"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Delete permanently | `gh issue delete <n> --yes` |
| Close instead | `gh issue close <n> --reason completed` |
| Cancel | No action |

---

### `gh issue transfer`

**AskUserQuestion template:**

```
question: "Transfer issue #<number> '<title>' to <target-repo>?"
header: "Transfer"
options:
  - label: "Transfer"
    description: "Move issue to <target-repo> (a redirect will remain here)"
  - label: "Cancel"
    description: "Keep issue in current repo"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Transfer | `gh issue transfer <n> <target-repo>` |
| Cancel | No action |

---

### `gh release delete`

**AskUserQuestion template:**

```
question: "Delete release '<tag>'?"
header: "Release Delete"
options:
  - label: "Delete release only"
    description: "Remove the release but keep the git tag"
  - label: "Delete release and tag"
    description: "Remove both the release and the underlying git tag"
  - label: "Cancel"
    description: "Keep the release"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Delete release only | `gh release delete <tag> --yes` |
| Delete release and tag | `gh release delete <tag> --yes --cleanup-tag` |
| Cancel | No action |

Note: `--yes` is acceptable here because the user already confirmed via AskUserQuestion. This flag only skips `gh`'s own interactive prompt.

---

### `gh repo archive`

**AskUserQuestion template:**

```
question: "Archive repository '<owner/repo>'? The repo becomes read-only."
header: "Archive"
options:
  - label: "Archive"
    description: "Make the repo read-only (reversible via GitHub web UI)"
  - label: "Cancel"
    description: "Keep the repo active"
```

**Execution:** `gh repo archive <owner/repo> --yes`

---

### `gh label delete`

**AskUserQuestion template:**

```
question: "Delete label '<name>'? It will be removed from all issues and PRs."
header: "Label Delete"
options:
  - label: "Delete"
    description: "Remove the label from the repo and all associated items"
  - label: "Cancel"
    description: "Keep the label"
```

**Execution:** `gh label delete <name> --yes`

---

### `gh secret delete` / `gh variable delete`

**AskUserQuestion template:**

```
question: "Delete secret/variable '<name>'?"
header: "Secret Delete"
options:
  - label: "Delete"
    description: "Remove permanently — workflows using this will fail"
  - label: "Cancel"
    description: "Keep the secret/variable"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Delete | `gh secret delete <name>` or `gh variable delete <name>` |
| Cancel | No action |

---

### `gh run cancel`

**AskUserQuestion template:**

```
question: "Cancel workflow run #<run-id> (<workflow-name>)?"
header: "Run Cancel"
options:
  - label: "Cancel run"
    description: "Stop the running workflow — jobs in progress will be terminated"
  - label: "Keep running"
    description: "Let the workflow continue"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Cancel run | `gh run cancel <run-id>` |
| Keep running | No action |

---

### `gh auth logout`

**AskUserQuestion template:**

```
question: "Log out of GitHub CLI for account '<user>'?"
header: "Auth Logout"
options:
  - label: "Log out"
    description: "Remove local authentication credentials for this account"
  - label: "Cancel"
    description: "Stay logged in"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Log out | `gh auth logout` |
| Cancel | No action |

---

### `gh api -X DELETE`

**AskUserQuestion template:**

```
question: "Execute DELETE request to '<endpoint>'?"
header: "API Delete"
options:
  - label: "Execute"
    description: "Send DELETE to the GitHub API endpoint"
  - label: "Cancel"
    description: "Do not send the request"
```

**Execution mapping:**

| Choice | Command |
|--------|---------|
| Execute | `gh api <endpoint> -X DELETE` |
| Cancel | No action |

---

## Forbidden Operations (Triple Confirmation Protocol)

These operations are extremely dangerous. NEVER auto-confirm. NEVER pass `--yes` to bypass `gh`'s own prompts for these commands.

### Protocol: 3-Step Validation

1. **Step 1 — Warn:** Explain consequences clearly
2. **Step 2 — Typed confirmation:** Ask user to type the repo name or target
3. **Step 3 — Final confirm:** One last AskUserQuestion with explicit options

---

### `gh repo delete`

**PERMANENT and IRREVERSIBLE.** All code, issues, PRs, wikis, releases, and Actions history are destroyed.

**Step 1 — Warn the user:**

> Deleting `<owner/repo>` is PERMANENT. This will destroy:
> - All code and branches
> - All issues, PRs, and discussions
> - All releases and tags
> - All Actions history and secrets
> - All wikis and project boards
>
> This action CANNOT be undone.

**Step 2 — Require typed confirmation:**

Ask the user to type the full repository name (`owner/repo`) to confirm. If it does not match exactly, REFUSE to proceed.

**Step 3 — Final confirm (AskUserQuestion):**

```
question: "FINAL CONFIRMATION: Permanently delete '<owner/repo>'? Type the repo name above to confirm."
header: "DANGER"
options:
  - label: "I understand, delete it"
    description: "PERMANENTLY destroy the repository and all its data"
  - label: "Cancel"
    description: "Do NOT delete — keep the repository"
```

**Execution:** Only if ALL three steps pass. NEVER add `--yes` flag.

---

### `gh repo transfer`

Transfers repository ownership. Original owner loses admin access.

**Step 1 — Warn the user:**

> Transferring `<owner/repo>` to `<new-owner>`:
> - The current owner will lose admin access
> - URLs will redirect, but forks may break
> - GitHub Pages will be unpublished
> - Actions secrets will NOT transfer
>
> Verify the target account/org exists before proceeding.

**Before proceeding,** verify target exists: `gh api users/<new-owner>` or `gh api orgs/<new-owner>`.

**Step 2 — Require typed confirmation:**

Ask the user to type both the repo name AND the target owner.

**Step 3 — Final confirm (AskUserQuestion):**

```
question: "FINAL CONFIRMATION: Transfer '<owner/repo>' to '<new-owner>'?"
header: "DANGER"
options:
  - label: "Transfer ownership"
    description: "Transfer the repo — current owner loses admin access"
  - label: "Cancel"
    description: "Do NOT transfer — keep current ownership"
```

---

### `gh repo edit --visibility`

Changing visibility has serious consequences:

- **Private → Public:** All code becomes visible to everyone. Cannot be undone if forks are created.
- **Public → Private:** All forks are detached and become independent repos. Star/watch counts reset.
- **Internal → Public/Private:** Org-specific access rules change.

**Step 1 — Warn with specific consequences** based on the direction of change.

**Step 2 — Require typed confirmation** of the repo name.

**Step 3 — Final confirm (AskUserQuestion):**

```
question: "Change '<owner/repo>' visibility from <current> to <target>?"
header: "DANGER"
options:
  - label: "Change visibility"
    description: "<specific consequence for this direction>"
  - label: "Cancel"
    description: "Keep current visibility (<current>)"
```

---

### Bulk Destructive Loops

**NEVER** execute a loop that runs destructive operations without batch confirmation.

If the user asks to close/delete/merge multiple items:

1. List ALL items that will be affected
2. Show the count and full list
3. Use AskUserQuestion to confirm the entire batch

```
question: "Perform <action> on <count> items? See list above."
header: "Bulk Op"
options:
  - label: "Proceed with all <count>"
    description: "Apply <action> to every item listed"
  - label: "Let me pick individually"
    description: "I'll confirm each item one by one"
  - label: "Cancel"
    description: "Do not perform any <action>"
```

If "individually" is selected, confirm each item with its own AskUserQuestion.

---

## Edge Cases

### The `--admin` Flag

`gh pr merge --admin` bypasses branch protection rules. Treat as **Destructive** with an additional warning:

> This will bypass branch protection rules (required reviews, status checks). Are you sure?

### The `--delete-branch` Flag

When used with `gh pr merge` or `gh pr close`, always inform the user the branch will be deleted. If unsure, default to including it for merge (standard practice) but omitting it for close.

### Interactive Mode Avoidance

Never run `gh` without arguments that would trigger interactive mode. Always provide:
- `--title` and `--body` for create commands
- Explicit flags rather than relying on interactive prompts
- Use `--yes` only for destructive operations AFTER AskUserQuestion confirmation (never for forbidden operations)

### Secrets Hygiene

- Never display `gh auth token` output to the user or include it in logs
- When using `gh secret set`, prefer `--body` over piping to avoid leaking values in shell history
- Never echo secret values in commands — use `gh secret set NAME < file` or `--body` flag
- If a secret value appears in output, warn the user immediately

### Cross-Repo Targeting (`-R`)

When using `-R owner/repo` with any Write or Destructive command, always echo the target repo back to the user before executing. This prevents accidental operations on the wrong repository.

### Auth Scopes

Some operations require additional scopes:
- `delete_repo` scope for `gh repo delete`
- `admin:org` scope for org-level operations
- `workflow` scope for Actions secrets

Check with `gh auth status` before operations that may need elevated scopes.

### Rate Limits

GitHub API has rate limits (5,000 req/hr authenticated). For bulk operations:
- Use `--limit` to cap result sets
- Avoid tight loops of API calls
- Check `gh api rate_limit` if hitting limits
