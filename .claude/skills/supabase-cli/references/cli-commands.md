# Supabase CLI Commands Reference

Complete reference for Supabase CLI commands organized by category.

## Project Management

### Initialize & Link

```bash
# Initialize new Supabase project
supabase init

# Link to existing remote project
supabase link --project-ref <ref>
supabase link --project-ref hudhaisjslxuzcycktyp

# Get project reference from URL
# https://hudhaisjslxuzcycktyp.supabase.co → ref is hudhaisjslxuzcycktyp
```

### Local Development

```bash
# Start local Supabase (Docker required)
supabase start

# Stop local Supabase
supabase stop

# Check local status
supabase status

# Reset local database (destructive)
supabase db reset
```

## Database Operations

### Migrations

```bash
# Create new migration
supabase migration new <name>
# Creates: supabase/migrations/<timestamp>_<name>.sql

# Apply migrations to local database
supabase db push

# Apply to remote (requires link)
supabase db push --linked

# List migrations
supabase migration list

# Check migration status
supabase migration list --schema public

# Repair migration history
supabase migration repair --status applied <version>
```

### Schema Diff

```bash
# Compare local schema to remote
supabase db diff

# Generate migration from diff
supabase db diff --use-migra -f <name>

# Diff against specific schema
supabase db diff --schema public,auth

# Output to file
supabase db diff > changes.sql
```

### Direct SQL

```bash
# Execute SQL on local
supabase db execute < query.sql

# Execute on remote (use with caution)
supabase db execute --linked < query.sql

# Dump schema
supabase db dump -f schema.sql

# Dump with data
supabase db dump -f backup.sql --data-only
```

## Type Generation

```bash
# Generate types from local database
supabase gen types typescript --local > types/supabase.ts

# Generate from remote
supabase gen types typescript --linked > types/supabase.ts

# Generate with schema filter
supabase gen types typescript --local --schema public > types/supabase.ts

# Generate with Go output
supabase gen types go --local > types/supabase.go
```

## Edge Functions

### Development

```bash
# Create new function
supabase functions new <name>
# Creates: supabase/functions/<name>/index.ts

# Serve locally (with hot reload)
supabase functions serve <name>

# Serve all functions
supabase functions serve

# Serve with inspect (debugging)
supabase functions serve --inspect
```

### Deployment

```bash
# Deploy single function
supabase functions deploy <name>

# Deploy with custom import map
supabase functions deploy <name> --import-map import_map.json

# Deploy all functions
supabase functions deploy

# List deployed functions
supabase functions list
```

## Secrets Management

```bash
# List all secrets
supabase secrets list

# Set single secret
supabase secrets set KEY=value

# Set multiple secrets
supabase secrets set KEY1=value1 KEY2=value2

# Set from file
supabase secrets set --env-file .env.production

# Unset secret
supabase secrets unset KEY

# Unset multiple
supabase secrets unset KEY1 KEY2
```

## Authentication

```bash
# List auth users
supabase auth list

# Generate JWT
supabase gen keys

# Set up SSO provider
supabase sso add --type saml --metadata-file metadata.xml
```

## Storage

```bash
# List buckets
supabase storage list-buckets

# Create bucket
supabase storage create-bucket <name>

# List objects
supabase storage list-objects <bucket>

# Upload file
supabase storage upload <bucket> <local-path> <remote-path>
```

## Branching (Pro+)

```bash
# Create branch
supabase branches create <name>

# List branches
supabase branches list

# Switch branch
supabase branches switch <name>

# Delete branch
supabase branches delete <name>
```

## Common Command Combinations

### Full Local Reset

```bash
supabase db reset && supabase db push
```

### Sync Schema to Remote

```bash
supabase db push --linked
supabase gen types typescript --linked > types/supabase.ts
```

### Deploy Function with Secrets

```bash
supabase secrets set --env-file .env.production
supabase functions deploy <name>
```

### Migration Development Cycle

```bash
# 1. Make schema changes in local
# 2. Generate migration from diff
supabase db diff --use-migra -f my_change

# 3. Review generated migration
cat supabase/migrations/*_my_change.sql

# 4. Test locally
supabase db reset
supabase db push

# 5. Push to remote
supabase db push --linked
```

## Flags Reference

| Flag | Description |
|------|-------------|
| `--project-ref` | Remote project reference |
| `--linked` | Use linked remote project |
| `--local` | Use local database |
| `--schema` | Target specific schema(s) |
| `--use-migra` | Use migra for diff (more accurate) |
| `--debug` | Enable debug output |
| `--experimental` | Enable experimental features |

## Environment Variables

```bash
# Override project ref
export SUPABASE_PROJECT_ID=hudhaisjslxuzcycktyp

# Access token for CI/CD
export SUPABASE_ACCESS_TOKEN=sbp_xxx

# Custom database URL
export SUPABASE_DB_URL=postgresql://...
```

## CI/CD Integration

```bash
# Login with access token (for CI)
supabase login --token $SUPABASE_ACCESS_TOKEN

# Push migrations in CI
supabase link --project-ref $PROJECT_REF
supabase db push --linked

# Deploy functions in CI
supabase functions deploy --all
```
