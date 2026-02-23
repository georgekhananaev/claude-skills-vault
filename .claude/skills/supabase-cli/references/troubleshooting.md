# Supabase CLI Troubleshooting

Common issues and solutions when working with Supabase CLI.

## Docker Issues

### Container Not Starting

**Symptom:** `supabase start` hangs or fails

**Solutions:**

```bash
# 1. Check Docker is running
docker info

# 2. Clean up old containers
docker rm -f $(docker ps -a -q --filter "name=supabase")

# 3. Reset and start fresh
supabase stop --no-backup
supabase start

# 4. Check Docker resources
# Docker Desktop → Settings → Resources
# Recommended: 4GB+ RAM, 2+ CPUs
```

### Out of Disk Space

**Symptom:** Docker volumes filling up

```bash
# Check Docker disk usage
docker system df

# Clean up unused volumes
docker volume prune

# Clean up everything (careful!)
docker system prune -a --volumes
```

### Permission Denied

**Symptom:** Cannot connect to Docker socket

```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# macOS: Ensure Docker Desktop is running
open -a Docker
```

## Port Conflicts

### Default Ports in Use

**Symptom:** Address already in use

**Solutions:**

```bash
# Check what's using the port
lsof -i :54321  # Supabase API
lsof -i :54322  # Supabase DB
lsof -i :54323  # Supabase Studio

# Kill the process
kill -9 <PID>

# Or: Change Supabase ports in config.toml
```

**Custom Port Configuration:**

Edit `supabase/config.toml`:

```toml
[api]
port = 54321

[db]
port = 54322

[studio]
port = 54323
```

## Migration Issues

### Migration Hash Mismatch

**Symptom:** `Migration has been modified since applied`

**Solutions:**

```bash
# Option 1: Reset local database
supabase db reset

# Option 2: Repair migration status
supabase migration repair --status applied <version>

# Option 3: List and compare
supabase migration list
```

### Migration Failed Partially

**Symptom:** Migration ran partially, database in inconsistent state

```bash
# 1. Check current state
supabase db execute < "SELECT * FROM supabase_migrations.schema_migrations;"

# 2. Fix manually or reset
supabase db reset

# 3. Wrap migrations in transactions
BEGIN;
-- migration code
COMMIT;
```

### Cannot Create Index Concurrently

**Symptom:** `CREATE INDEX CONCURRENTLY cannot run inside a transaction block`

**Solution:** Move CONCURRENTLY indexes outside BEGIN/COMMIT:

```sql
-- Don't wrap in transaction
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_name ON table(column);
```

## Connection Issues

### Cannot Connect to Local DB

**Symptom:** Connection refused on localhost

```bash
# 1. Check local is running
supabase status

# 2. Get connection string
supabase status | grep DB

# 3. Default local connection:
# postgresql://postgres:postgres@127.0.0.1:54322/postgres

# 4. Test connection
psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -c "SELECT 1;"
```

### Cannot Connect to Remote

**Symptom:** Connection timeout or auth failure

```bash
# 1. Verify credentials in .env
cat .env | grep SUPABASE

# 2. Test with psql
psql "$POSTGRES_DB" -c "SELECT 1;"

# 3. Check IP allowlist in Supabase Dashboard
# Dashboard → Database → Connection Pooling → Allowed IPs

# 4. Try connection pooler
# Use port 6543 instead of 5432
postgresql://...@db.xxx.supabase.co:6543/postgres?pgbouncer=true
```

### SSL Certificate Issues

**Symptom:** SSL verification failed

```bash
# Add sslmode to connection string
postgresql://...@db.xxx.supabase.co:5432/postgres?sslmode=require

# Or disable verification (development only!)
postgresql://...?sslmode=disable
```

## Edge Function Issues

### Function Not Found

**Symptom:** 404 when calling function

```bash
# 1. Check function exists
ls supabase/functions/

# 2. Verify it's deployed
supabase functions list

# 3. Redeploy
supabase functions deploy <name>
```

### Function Timeout

**Symptom:** Function takes too long and times out

**Solutions:**
- Default timeout: 60 seconds (can increase to 150s on Pro+)
- Optimize function code
- Use background jobs for long operations

```typescript
// Return early, process in background
export default async function handler(req: Request) {
  // Start async work without await
  processInBackground(req.clone());

  // Return immediately
  return new Response(JSON.stringify({ status: 'processing' }));
}
```

### Import Errors

**Symptom:** Cannot resolve module

```bash
# 1. Check import map
cat supabase/functions/import_map.json

# 2. Deploy with explicit import map
supabase functions deploy <name> --import-map import_map.json

# 3. Use npm: specifier for npm packages
import { something } from "npm:package-name@1.0.0";
```

### CORS Errors

**Symptom:** CORS preflight failure in browser

```typescript
// Add CORS headers to function
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

export default async function handler(req: Request) {
  // Handle preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  // Normal response
  return new Response(data, {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}
```

## Secrets Issues

### Secret Not Available in Function

**Symptom:** `Deno.env.get('KEY')` returns undefined

```bash
# 1. Verify secret is set
supabase secrets list

# 2. Set it again
supabase secrets set KEY=value

# 3. Redeploy function after setting secrets
supabase functions deploy <name>
```

### Too Many Secrets

**Symptom:** Secrets limit exceeded

- Free tier: 20 secrets
- Pro tier: 100 secrets
- Solution: Consolidate related values into JSON

```bash
# Instead of multiple secrets
supabase secrets set CONFIG='{"key1":"val1","key2":"val2"}'
```

## Type Generation Issues

### Types Not Matching Schema

**Symptom:** Generated types differ from actual schema

```bash
# 1. Regenerate from correct source
supabase gen types typescript --local > types/supabase.ts
# or
supabase gen types typescript --linked > types/supabase.ts

# 2. Check for pending migrations
supabase migration list

# 3. Apply pending migrations first
supabase db push
```

### Type Generation Hangs

**Symptom:** `supabase gen types` never completes

```bash
# 1. Increase timeout
supabase gen types typescript --local --debug

# 2. Check local is healthy
supabase status

# 3. Restart local
supabase stop && supabase start
```

## CLI Authentication Issues

### Not Logged In

**Symptom:** `not logged in` or `access denied`

```bash
# 1. Login interactively
supabase login

# 2. Or use access token (CI/CD)
export SUPABASE_ACCESS_TOKEN=sbp_xxx
supabase link --project-ref xxx
```

### Token Expired

**Symptom:** Operations fail after working previously

```bash
# Refresh login
supabase login

# Check token status
supabase projects list
```

## Performance Issues

### Slow Local Development

```bash
# 1. Allocate more Docker resources
# Docker Desktop → Settings → Resources

# 2. Use SSD storage for Docker

# 3. Reduce logging
supabase start --debug false

# 4. Skip seeding for quick restarts
supabase db reset --no-seed
```

### Slow Migrations

```bash
# 1. Use CONCURRENTLY for indexes
CREATE INDEX CONCURRENTLY ...

# 2. Batch large data updates
# (See migration-patterns.md)

# 3. Monitor during migration
SELECT * FROM pg_stat_activity;
```

## Getting Help

```bash
# Built-in help
supabase --help
supabase <command> --help

# Debug mode
supabase --debug <command>

# Version info
supabase --version

# GitHub Issues
# https://github.com/supabase/cli/issues
```

## Quick Diagnostic Commands

```bash
# Full status check
supabase status

# Check all services health
docker ps --filter "name=supabase"

# View container logs
docker logs supabase_db_<project>

# Network connectivity
curl -v http://localhost:54321/rest/v1/

# Database connection test
psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -c "SELECT version();"
```
