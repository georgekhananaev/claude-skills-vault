# Row Level Security (RLS)

PostgreSQL's RLS is Supabase's primary security mechanism. Policies act as WHERE clauses on every query.

## Core Rules

1. **Enable RLS on ALL public tables** - No exceptions
2. **No data accessible until policies created** - After enabling, table is locked
3. **Index every column used in policies** - Critical for performance
4. **Test policies thoroughly** - Bugs = security vulnerabilities

## Basic Patterns

### User-Owned Data

```sql
-- Enable RLS
ALTER TABLE public.todos ENABLE ROW LEVEL SECURITY;

-- Users can only see their own todos
CREATE POLICY "users_own_todos" ON todos
  FOR ALL
  USING (user_id = auth.uid());

-- Or split by operation for granular control
CREATE POLICY "select_own" ON todos FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "insert_own" ON todos FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "update_own" ON todos FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY "delete_own" ON todos FOR DELETE USING (user_id = auth.uid());
```

### Public Read, Owner Write

```sql
-- Anyone can read
CREATE POLICY "public_read" ON posts
  FOR SELECT USING (true);

-- Only owner can modify
CREATE POLICY "owner_write" ON posts
  FOR ALL
  USING (author_id = auth.uid())
  WITH CHECK (author_id = auth.uid());
```

### Role-Based Access

```sql
-- Check role from JWT claims
CREATE POLICY "admin_full_access" ON users
  FOR ALL
  USING (auth.jwt() ->> 'role' = 'admin');

-- Check role from profiles table
CREATE POLICY "manager_access" ON reports
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('manager', 'admin')
    )
  );
```

## Multi-Tenant Patterns

### Tenant ID in JWT

```sql
-- Store tenant_id in app_metadata during user creation
-- Access it in policies:
CREATE POLICY "tenant_isolation" ON items
  USING (
    tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::UUID
  );
```

### Tenant ID via Lookup

```sql
-- If tenant relationship is in a separate table
CREATE POLICY "tenant_via_membership" ON items
  USING (
    tenant_id IN (
      SELECT tenant_id FROM tenant_members
      WHERE user_id = auth.uid()
    )
  );

-- IMPORTANT: Index for performance
CREATE INDEX idx_tenant_members_user ON tenant_members(user_id);
CREATE INDEX idx_items_tenant ON items(tenant_id);
```

### Organization Hierarchy

```sql
-- Users can access their org and child orgs
CREATE POLICY "org_hierarchy" ON documents
  USING (
    org_id IN (
      WITH RECURSIVE org_tree AS (
        SELECT id FROM organizations WHERE id = (auth.jwt() ->> 'org_id')::UUID
        UNION ALL
        SELECT o.id FROM organizations o
        JOIN org_tree t ON o.parent_id = t.id
      )
      SELECT id FROM org_tree
    )
  );
```

## Helper Functions

```sql
-- auth.uid() - Current user's UUID
SELECT auth.uid();

-- auth.jwt() - Full JWT claims
SELECT auth.jwt();

-- auth.role() - Current role (anon, authenticated, service_role)
SELECT auth.role();

-- Custom helper for common checks
CREATE FUNCTION is_admin() RETURNS BOOLEAN AS $$
  SELECT COALESCE(auth.jwt() ->> 'role', '') = 'admin';
$$ LANGUAGE SQL SECURITY DEFINER;

-- Use in policy
CREATE POLICY "admin_only" ON settings
  FOR ALL USING (is_admin());
```

## Performance Optimization

### Index Strategy

```sql
-- MUST index columns used in policies
CREATE INDEX idx_todos_user ON todos(user_id);
CREATE INDEX idx_items_tenant ON items(tenant_id);
CREATE INDEX idx_docs_org ON documents(org_id);

-- Composite index for complex policies
CREATE INDEX idx_posts_author_status ON posts(author_id, status);
```

### Avoid Expensive Operations

```sql
-- BAD: Subquery in every row check
CREATE POLICY "slow" ON items
  USING (
    tenant_id IN (SELECT tenant_id FROM memberships WHERE user_id = auth.uid())
  );

-- BETTER: Store tenant_id in JWT
CREATE POLICY "fast" ON items
  USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::UUID);
```

### Materialized Views for Complex Access

```sql
-- Create materialized view of user permissions
CREATE MATERIALIZED VIEW user_permissions AS
SELECT user_id, array_agg(DISTINCT permission) as permissions
FROM role_permissions rp
JOIN user_roles ur ON ur.role_id = rp.role_id
GROUP BY user_id;

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY user_permissions;

-- Use in policy (fast lookup)
CREATE POLICY "permission_check" ON resources
  USING (
    'read:resources' = ANY(
      SELECT permissions FROM user_permissions WHERE user_id = auth.uid()
    )
  );
```

## Views and RLS

```sql
-- Views bypass RLS by default (created as postgres user)
-- In PostgreSQL 15+, use security_invoker:
CREATE VIEW user_posts WITH (security_invoker = true) AS
SELECT * FROM posts WHERE status = 'published';

-- For older versions, create view as authenticated role
-- Or use function with SECURITY INVOKER
```

## Testing Policies

### In Dashboard

1. Go to SQL Editor
2. Use "Run as" dropdown to switch roles
3. Test queries as different users

### With CLI

```sql
-- Impersonate a user
SET request.jwt.claims = '{"sub": "user-uuid-here", "role": "authenticated"}';

-- Run query
SELECT * FROM todos;

-- Reset
RESET request.jwt.claims;
```

### Automated Tests

```typescript
// test/rls.test.ts
import { createClient } from '@supabase/supabase-js';

describe('RLS Policies', () => {
  const supabase = createClient(url, anonKey);

  it('user can only see own todos', async () => {
    // Sign in as test user
    await supabase.auth.signInWithPassword({ email, password });

    // Query should only return user's todos
    const { data } = await supabase.from('todos').select('*');

    expect(data.every(t => t.user_id === testUserId)).toBe(true);
  });

  it('user cannot see other user todos', async () => {
    const { data } = await supabase
      .from('todos')
      .select('*')
      .eq('user_id', otherUserId);

    expect(data).toHaveLength(0);
  });
});
```

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Forgetting to enable RLS | All data exposed | `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` |
| Using user_metadata in policy | Users can modify it | Use app_metadata (server-only) |
| No index on policy columns | 10-100x slower queries | Add indexes |
| service_role in client | Bypasses all RLS | Use anon key |
| Complex subqueries | Slow performance | Store data in JWT or materialized view |

## Debug Checklist

```sql
-- 1. Is RLS enabled?
SELECT relname, relrowsecurity, relforcerowsecurity
FROM pg_class WHERE relname = 'your_table';

-- 2. What policies exist?
SELECT * FROM pg_policies WHERE tablename = 'your_table';

-- 3. What's in the JWT?
SELECT auth.jwt();

-- 4. Is the user authenticated?
SELECT auth.uid(), auth.role();

-- 5. Explain query with policies
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM your_table;
```
