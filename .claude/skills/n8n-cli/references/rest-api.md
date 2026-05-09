# n8n REST API Reference

Works against both self-hosted and n8n Cloud. Required for cloud (no CLI there).

Source: `https://docs.n8n.io/api/`.

## Authentication

Header: `X-N8N-API-KEY: <your-key>`.

Get the key:
- **Self-hosted**: n8n UI → Settings → n8n API → Create an API key.
- **Cloud**: same path; subject to your plan's API quota.

Base URL:
- **Self-hosted**: `https://<your-domain>/api/v1`
- **Cloud**: `https://<workspace>.app.n8n.cloud/api/v1`

## Env vars

```bash
export N8N_API_URL="https://n8n.example.com"
export N8N_API_KEY="<key starts w/ n8n_api_>"
export N8N_TIMEOUT="30"   # optional, seconds, default 30
```

## Endpoint surface (n8n 2.x)

### Workflows

| Method | Path | Used by |
|---|---|---|
| GET | `/api/v1/workflows` | `list_workflows.py` (read, paginated) |
| GET | `/api/v1/workflows/{id}` | `get_workflow.py` (read) |
| POST | `/api/v1/workflows` | `import_workflow.py --backend api --confirm` (gated) |
| PUT | `/api/v1/workflows/{id}` | not in skill (use UI) |
| **DELETE** | `/api/v1/workflows/{id}` | **REFUSED** |
| POST | `/api/v1/workflows/{id}/publish` | `publish_workflow.py --action publish --confirm` |
| POST | `/api/v1/workflows/{id}/unpublish` | `publish_workflow.py --action unpublish --confirm` |
| POST | `/api/v1/workflows/{id}/activate` (1.x) | fallback in publish_workflow |
| POST | `/api/v1/workflows/{id}/deactivate` (1.x) | fallback |

### Executions

| Method | Path | Used by |
|---|---|---|
| GET | `/api/v1/executions` | `list_executions.py`, `execution_stats.py` |
| GET | `/api/v1/executions/{id}` | `get_execution.py` |
| **DELETE** | `/api/v1/executions/{id}` | **REFUSED** |

### Credentials

| Method | Path | Used by |
|---|---|---|
| GET | `/api/v1/credentials` | `list_credentials.py` (metadata only) |
| GET | `/api/v1/credentials/{id}` | not in skill (always strips `data` field) |
| POST | `/api/v1/credentials` | not in skill (use UI) |
| **DELETE** | `/api/v1/credentials/{id}` | **REFUSED** |

> ⚠️  REST API does NOT expose decrypted credential values. Use `n8n export:credentials --decrypted` (CLI) only when migrating between encryption keys.

### Tags

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/tags` | read |
| POST | `/api/v1/tags` | not in skill |
| **DELETE** | `/api/v1/tags/{id}` | **REFUSED** |

### Users / Projects (admin)

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/users` | read |
| **POST** | `/api/v1/users` | **REFUSED** (creates users) |
| **PATCH** | `/api/v1/users/{id}` | **REFUSED** (role changes) |
| **DELETE** | `/api/v1/users/{id}` | **REFUSED** |
| GET | `/api/v1/projects` | read |
| **DELETE** | `/api/v1/projects/{id}` | **REFUSED** |

### Audit / Source-control / License

| Method | Path | Used by |
|---|---|---|
| POST | `/api/v1/audit` | `audit_log.py --backend api` |
| GET | `/api/v1/source-control/status` | not in skill (advisory) |
| **POST** | `/api/v1/source-control/pull` | **REFUSED** (overwrites) |
| **POST** | `/api/v1/source-control/push` | **REFUSED** (writes remote) |
| GET | `/api/v1/license` | not in skill |
| **POST** | `/api/v1/license` | **REFUSED** |

## Pagination

Most list endpoints return:
```json
{
  "data": [...],
  "nextCursor": "<opaque>"
}
```

Pass `cursor` query param to get next page. `_api.py:list_paginated()` handles this.

Default `limit` is 100, max 250.

## Filter examples

```
GET /api/v1/workflows?active=true&tags=prod&projectId=<pid>&limit=250
GET /api/v1/executions?workflowId=<wfid>&status=error&limit=50
GET /api/v1/credentials?type=slackOAuth2Api
```

## Common errors

| HTTP | Meaning |
|---|---|
| 401 | Invalid / missing `X-N8N-API-KEY` |
| 403 | Key valid but user lacks permission for endpoint |
| 404 | Resource doesn't exist (or no permission to see it) |
| 429 | Rate limited (cloud) — backoff |

## n8n 2.x vs 1.x

n8n 2.0 replaced the active/inactive toggle w/ a publish/unpublish model. The REST API exposes both endpoint sets during the transition period; 2.x is canonical going forward. The `publish_workflow.py` script tries publish/unpublish first, falls back to activate/deactivate.
