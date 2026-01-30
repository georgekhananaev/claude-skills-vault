---
name: supabase-expert
description: Production-grade Supabase expertise for commercial applications. Covers database design, RLS policies, authentication (SSO/SAML, MFA, SSR), Edge Functions, Realtime, Storage, AI/vectors (pgvector, RAG), and deployment best practices. Emphasizes security, scalability, and enterprise compliance.
---

# Supabase Expert

Production-grade Supabase development for commercial applications. PostgreSQL-first approach with security, scalability, and enterprise compliance.

## When to Use

Invoke when:
- Designing Supabase schema for new projects
- Implementing Row Level Security (RLS) policies
- Setting up authentication (social, email, SSO/SAML)
- Building Edge Functions for serverless logic
- Optimizing database performance
- Preparing for production deployment
- Implementing enterprise features (SOC 2, HIPAA, GDPR)

## Quick Reference

| Domain | Reference | Key Topics |
|--------|-----------|------------|
| Database | `references/database.md` | Schema design, indexes, migrations, optimization |
| RLS | `references/rls-security.md` | Policies, multi-tenant, testing |
| Auth | `references/authentication.md` | Social, email, SSO/SAML, MFA, SSR, Captcha |
| Edge Functions | `references/edge-functions.md` | Serverless, scheduling, background jobs |
| Realtime | `references/realtime.md` | Subscriptions, broadcast, presence |
| Storage | `references/storage.md` | Buckets, policies, CDN, transformations |
| AI & Vectors | `references/ai-vectors.md` | pgvector, embeddings, semantic search, RAG |
| Production | `references/production.md` | Deployment, monitoring, scaling, branching |

## Documentation Research

**Always fetch latest docs** before implementing:

```bash
# Official documentation
https://supabase.com/docs

# API reference
https://supabase.com/docs/reference

# Changelog (new features)
https://supabase.com/changelog

# GitHub discussions (community patterns)
https://github.com/orgs/supabase/discussions
```

## Architecture Principles

### 1. PostgreSQL-First

Supabase is PostgreSQL. Leverage its full power:

```sql
-- Use native PostgreSQL features
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX idx_posts_gin ON posts USING gin(to_tsvector('english', content));

-- Partial indexes for common queries
CREATE INDEX idx_active_users ON users(created_at) WHERE status = 'active';

-- Generated columns
ALTER TABLE orders ADD COLUMN total_cents INTEGER
  GENERATED ALWAYS AS (quantity * price_cents) STORED;
```

### 2. Security by Default

```sql
-- ALWAYS enable RLS on public tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Force RLS even for table owners
ALTER TABLE public.profiles FORCE ROW LEVEL SECURITY;

-- Never expose service_role key to client
-- Use anon key + RLS for client access
```

### 3. Performance-Aware Design

| Pattern | When to Use |
|---------|-------------|
| Connection Pooling | Always (Supabase handles via Supavisor) |
| Read Replicas | High read workloads |
| Edge Functions | Compute-intensive, global distribution |
| Database Functions | Complex queries, reduce round trips |

## Project Structure

```
project/
├── supabase/
│   ├── migrations/           # Schema migrations (versioned)
│   │   ├── 20240101000000_init.sql
│   │   └── 20240102000000_add_profiles.sql
│   ├── functions/            # Edge Functions
│   │   ├── hello-world/
│   │   │   └── index.ts
│   │   └── stripe-webhook/
│   │       └── index.ts
│   ├── seed.sql              # Development seed data
│   └── config.toml           # Local config
├── .env.local                # Local environment
└── .env.production           # Production (gitignored!)
```

## Essential CLI Commands

```bash
# Initialize project
supabase init

# Start local development
supabase start

# Create migration
supabase migration new <name>

# Apply migrations
supabase db push

# Generate TypeScript types
supabase gen types typescript --local > types/supabase.ts

# Deploy Edge Functions
supabase functions deploy <function-name>

# Link to remote project
supabase link --project-ref <ref>
```

## Security Checklist

### Pre-Production

```
□ RLS enabled on ALL public tables
□ No service_role key in client code
□ API keys in environment variables
□ CORS configured for production domains
□ Rate limiting configured
□ SSL/TLS enforced
□ Backup strategy defined
□ PITR enabled (if >4GB database)
```

### Enterprise

```
□ SOC 2 Type II compliance (Team+ plan)
□ HIPAA BAA signed (if healthcare data)
□ GDPR data residency configured
□ SSO/SAML configured
□ Audit logging enabled
□ Custom domains configured
```

## Common Patterns

### Multi-Tenant Architecture

```sql
-- Add tenant_id to all tables
CREATE TABLE public.items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS policy for tenant isolation
CREATE POLICY "tenant_isolation" ON items
  USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::UUID);

-- Index for performance
CREATE INDEX idx_items_tenant ON items(tenant_id);
```

### Soft Deletes

```sql
ALTER TABLE items ADD COLUMN deleted_at TIMESTAMPTZ;

-- RLS policy excludes deleted
CREATE POLICY "hide_deleted" ON items
  FOR SELECT USING (deleted_at IS NULL);

-- Soft delete function
CREATE FUNCTION soft_delete(table_name TEXT, row_id UUID)
RETURNS VOID AS $$
BEGIN
  EXECUTE format('UPDATE %I SET deleted_at = now() WHERE id = $1', table_name) USING row_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Audit Trail

```sql
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name TEXT NOT NULL,
  record_id UUID NOT NULL,
  action TEXT NOT NULL, -- INSERT, UPDATE, DELETE
  old_data JSONB,
  new_data JSONB,
  user_id UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Trigger function
CREATE FUNCTION audit_trigger() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, user_id)
  VALUES (
    TG_TABLE_NAME,
    COALESCE(NEW.id, OLD.id),
    TG_OP,
    CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) END,
    CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) END,
    auth.uid()
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Pricing Tiers (2026)

| Tier | Price | Database | MAUs | Best For |
|------|-------|----------|------|----------|
| Free | $0 | 500 MB | 50K | Development, POC |
| Pro | $25/mo | 8 GB | 100K | Production startups |
| Team | $599/mo | Pro + compliance | Pro | Enterprise, regulated |
| Enterprise | Custom | Dedicated | Custom | Fortune 500, healthcare |

## Anti-Patterns

| Pattern | Problem | Solution |
|---------|---------|----------|
| Service key in client | Full DB access bypass | Use anon key + RLS |
| No RLS on public tables | Data exposed | Enable RLS immediately |
| Realtime on all tables | Performance drain | Enable only where needed |
| No indexes on RLS columns | Slow policies | Index all policy columns |
| Manual schema changes | Drift between envs | Use migrations |
| Polling instead of Realtime | Unnecessary load | Use subscriptions |

## Performance Tips

1. **Index RLS columns** - Every column in a policy needs an index
2. **Use database functions** - Reduce round trips for complex operations
3. **Connection pooling** - Supavisor handles this, but configure pool size
4. **Read replicas** - For read-heavy workloads
5. **Edge caching** - Use CDN for static assets
6. **Batch operations** - Use bulk inserts/updates

## Monitoring

```sql
-- Enable query stats
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

## Integration with MCP

This skill complements the `supabase` MCP server in `mcp-servers/supabase/`. The MCP server provides runtime access; this skill provides design guidance.

---

Load `references/*.md` for detailed patterns and examples.
