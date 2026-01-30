# Production Deployment

Best practices for deploying Supabase applications to production.

## Pre-Production Checklist

### Security

```
□ RLS enabled on ALL public schema tables
□ No service_role key in client-side code
□ API keys stored in environment variables
□ CORS configured for production domains only
□ Rate limiting enabled (Auth > Settings)
□ SSL/TLS enforced
□ Database passwords rotated from defaults
□ 2FA enabled on Supabase dashboard account
```

### Database

```
□ Indexes on all frequently queried columns
□ Indexes on all columns used in RLS policies
□ Migrations version-controlled in Git
□ No manual schema changes in production
□ Connection pooling configured
□ pg_stat_statements enabled for monitoring
```

### Backups

```
□ Daily backups enabled (automatic on hosted)
□ PITR enabled if database >4GB
□ Backup restoration tested
□ Off-platform backup exports scheduled
```

### Performance

```
□ Realtime enabled only on necessary tables
□ Database functions for complex queries
□ Read replicas configured (if high read load)
□ Edge Functions optimized (no cold start issues)
```

## Environment Configuration

### Local Development

```bash
# .env.local (gitignored)
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...local-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJ...local-service-key
```

### Staging

```bash
# .env.staging
NEXT_PUBLIC_SUPABASE_URL=https://staging-xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...staging-anon
# Service key in CI/CD secrets only
```

### Production

```bash
# .env.production
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...prod-anon
# NEVER commit service_role key
```

## Migration Strategy

### Development Workflow

```bash
# 1. Create migration locally
supabase migration new add_profiles_table

# 2. Write SQL migration
# supabase/migrations/20240101000000_add_profiles_table.sql

# 3. Test locally
supabase db reset  # Applies all migrations fresh

# 4. Push to staging
supabase db push --linked

# 5. Verify in staging dashboard

# 6. Push to production
supabase db push --linked --project-ref prod-ref
```

### Migration File Best Practices

```sql
-- supabase/migrations/20240101000000_add_profiles_table.sql

-- Always use IF NOT EXISTS for idempotency
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS immediately
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Public profiles are viewable by everyone"
  ON public.profiles FOR SELECT
  USING (true);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_profiles_username ON profiles(username);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Rollback Strategy

```sql
-- Create corresponding down migration
-- supabase/migrations/20240101000000_add_profiles_table_down.sql

DROP TRIGGER IF EXISTS profiles_updated_at ON profiles;
DROP FUNCTION IF EXISTS update_updated_at;
DROP TABLE IF EXISTS public.profiles;
```

## Monitoring

### Enable pg_stat_statements

```sql
-- Check if enabled
SELECT * FROM pg_available_extensions WHERE name = 'pg_stat_statements';

-- Enable
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Query slow queries
SELECT
  query,
  calls,
  mean_exec_time,
  total_exec_time,
  rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

### Table Size Monitoring

```sql
SELECT
  schemaname,
  relname AS table_name,
  pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
  pg_size_pretty(pg_relation_size(relid)) AS data_size,
  pg_size_pretty(pg_indexes_size(relid)) AS index_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Connection Monitoring

```sql
-- Current connections
SELECT
  usename,
  application_name,
  client_addr,
  state,
  query_start,
  query
FROM pg_stat_activity
WHERE datname = current_database();

-- Connection count by state
SELECT state, count(*)
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state;
```

### Custom Alerts (via Edge Function + Cron)

```typescript
// supabase/functions/health-check/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { supabaseAdmin } from '../_shared/supabase.ts';

serve(async () => {
  // Check database
  const { data: dbCheck, error: dbError } = await supabaseAdmin
    .from('health_check')
    .select('*')
    .limit(1);

  // Check storage
  const { data: buckets, error: storageError } = await supabaseAdmin
    .storage
    .listBuckets();

  const healthy = !dbError && !storageError;

  if (!healthy) {
    // Send alert (Slack, PagerDuty, etc.)
    await fetch(Deno.env.get('SLACK_WEBHOOK_URL')!, {
      method: 'POST',
      body: JSON.stringify({
        text: `🚨 Supabase Health Check Failed: ${dbError?.message || storageError?.message}`
      })
    });
  }

  return new Response(JSON.stringify({
    healthy,
    database: !dbError,
    storage: !storageError,
    timestamp: new Date().toISOString()
  }));
});
```

## Scaling

### Connection Pooling

Supabase uses Supavisor for connection pooling. Configure in Dashboard:

- **Transaction mode**: Best for serverless (releases connection after query)
- **Session mode**: Required for prepared statements, LISTEN/NOTIFY
- **Pool size**: Default is sufficient for most apps

### Read Replicas

```typescript
// For read-heavy workloads, use read replica
const supabaseRead = createClient(
  Deno.env.get('SUPABASE_READ_REPLICA_URL')!,
  Deno.env.get('SUPABASE_ANON_KEY')!
);

// Write to primary
await supabase.from('posts').insert({ title: 'New Post' });

// Read from replica (eventual consistency)
const { data } = await supabaseRead.from('posts').select('*');
```

### Edge Function Scaling

```typescript
// Functions scale automatically
// Optimize for cold starts:

// 1. Minimize imports
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
// Not: import everything from a large library

// 2. Initialize outside handler
const supabase = createClient(url, key);

// 3. Keep functions small and focused
```

## CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/supabase.yml
name: Supabase CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1
        with:
          version: latest

      - name: Start Supabase
        run: supabase start

      - name: Run migrations
        run: supabase db reset

      - name: Run tests
        run: npm test
        env:
          SUPABASE_URL: http://localhost:54321
          SUPABASE_ANON_KEY: ${{ secrets.LOCAL_ANON_KEY }}

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1

      - name: Link project
        run: supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      - name: Push migrations
        run: supabase db push

      - name: Deploy functions
        run: supabase functions deploy
```

## Disaster Recovery

### Backup Restoration

```bash
# Download backup from Dashboard
# Or use pg_dump for custom backup

# Restore to new project
pg_restore -h db.xxx.supabase.co -U postgres -d postgres backup.dump
```

### Point-in-Time Recovery (PITR)

1. Enable PITR in Dashboard (Database > Backups)
2. Select recovery point (up to 7 days back)
3. Restore to new project or in-place

### Multi-Region Strategy

```typescript
// For critical apps, consider:
// 1. Primary in US
// 2. Read replica in EU
// 3. Edge Functions for global distribution

const getRegionalClient = (region: 'us' | 'eu') => {
  const urls = {
    us: 'https://us-xxx.supabase.co',
    eu: 'https://eu-xxx.supabase.co'
  };
  return createClient(urls[region], key);
};
```

## Enterprise Compliance

### SOC 2 Type II

- Available on Team plan ($599/mo)
- Audit reports available on request
- Includes security controls documentation

### HIPAA

- Available on Enterprise plan
- Requires BAA (Business Associate Agreement)
- Additional data handling requirements

### GDPR

- Data residency options (EU region)
- Data export/deletion APIs
- Consent management via Auth hooks

### Audit Logging

```sql
-- Enable audit logging for sensitive tables
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name TEXT NOT NULL,
  record_id UUID,
  action TEXT NOT NULL,
  old_data JSONB,
  new_data JSONB,
  user_id UUID,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS: Only admins can read audit logs
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "admin_only" ON audit_log
  FOR SELECT USING (
    auth.jwt() -> 'app_metadata' ->> 'role' = 'admin'
  );
```

## Database Branching (Preview Environments)

Supabase Branching creates isolated database environments for each PR/branch, enabling safe schema testing before production.

### How It Works

1. **Git Integration**: Connect your GitHub repo to Supabase project
2. **Automatic Branches**: Each PR gets a preview database branch
3. **Isolated Environment**: Separate schema, data, auth, and storage
4. **Migration Testing**: Runs migrations against production snapshot

### Setup

```bash
# 1. Install Supabase GitHub App
# Dashboard: Project Settings > Integrations > GitHub

# 2. Enable Branching
# Dashboard: Branching > Enable Preview Branches

# 3. Configure branch settings
# - Select production branch (main)
# - Choose whether to seed data
# - Set branch timeout (auto-pause after inactivity)
```

### Configuration File

```toml
# supabase/config.toml

[branching]
# Enable branching for this project
enabled = true

# Seed data for preview branches
[branching.preview]
seed_on_create = true
seed_file = "supabase/seed.sql"

# Timeout for inactive branches (in hours)
timeout_hours = 24
```

### CI/CD Integration

```yaml
# .github/workflows/supabase-preview.yml
name: Supabase Preview Branch

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1

      - name: Link to preview branch
        run: |
          # Branch is auto-created by Supabase GitHub integration
          # Get preview URL from GitHub deployment
          PREVIEW_URL=$(gh api repos/${{ github.repository }}/deployments \
            --jq '.[] | select(.environment | startswith("preview")) | .payload.web_url' \
            | head -1)
          echo "SUPABASE_URL=$PREVIEW_URL" >> $GITHUB_ENV
        env:
          GH_TOKEN: ${{ github.token }}

      - name: Run tests against preview
        run: npm test
        env:
          SUPABASE_URL: ${{ env.SUPABASE_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.PREVIEW_ANON_KEY }}
```

### Preview Branch Lifecycle

```
PR Opened → Branch Created → Migrations Applied → Ready for Testing
     ↓
PR Updated → Migrations Re-applied → Tests Run
     ↓
PR Merged → Branch Deleted → Migrations Applied to Production
     ↓
PR Closed → Branch Deleted (no migration)
```

### Working with Preview Branches

```typescript
// Get preview branch URL from environment
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!, // Varies per environment
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Preview branches have separate:
// - Database (schema + data)
// - Auth users (starts empty or seeded)
// - Storage buckets
// - Edge Functions (if deployed)
```

### Data Seeding for Previews

```sql
-- supabase/seed.sql
-- Runs when preview branch is created

-- Create test users
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'test@example.com', crypt('password123', gen_salt('bf')), now()),
  ('00000000-0000-0000-0000-000000000002', 'admin@example.com', crypt('password123', gen_salt('bf')), now());

-- Seed test data
INSERT INTO public.profiles (id, username, role)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'testuser', 'user'),
  ('00000000-0000-0000-0000-000000000002', 'admin', 'admin');

-- Add sample content
INSERT INTO public.posts (user_id, title, content)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'Test Post', 'Content for testing');
```

### Best Practices

| Practice | Description |
|----------|-------------|
| Use consistent seed data | Same test scenarios across all previews |
| Set appropriate timeouts | Save resources on inactive branches |
| Test migrations thoroughly | Preview catches issues before production |
| Include edge cases in seed | Test boundary conditions |
| Document preview access | Share preview URLs in PR comments |

### Limitations

- Preview branches pause after inactivity timeout
- Storage files not copied from production
- Edge Functions require separate deployment
- Some integrations may not work in preview
