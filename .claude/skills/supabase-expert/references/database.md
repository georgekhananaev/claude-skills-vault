# Database Design & Optimization

PostgreSQL best practices for Supabase applications.

## Schema Design Principles

### 1. Use UUIDs for Primary Keys

```sql
-- Preferred: UUID with gen_random_uuid()
CREATE TABLE items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL
);

-- Alternative: ULID for sortable IDs (requires extension)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION generate_ulid() RETURNS TEXT AS $$
DECLARE
  timestamp BYTEA = E'\\000\\000\\000\\000\\000\\000';
  unix_time BIGINT;
  ulid TEXT;
BEGIN
  unix_time = (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT;
  -- Implementation details...
  RETURN ulid;
END
$$ LANGUAGE plpgsql;
```

### 2. Timestamps with Timezone

```sql
CREATE TABLE posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT,
  -- Always use TIMESTAMPTZ
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  published_at TIMESTAMPTZ
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER posts_updated_at
  BEFORE UPDATE ON posts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### 3. Foreign Keys with Cascade

```sql
-- User profiles linked to auth.users
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE,
  full_name TEXT
);

-- Posts owned by users
CREATE TABLE posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  author_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL
);

-- Comments with cascading delete
CREATE TABLE comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  author_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  content TEXT NOT NULL
);
```

### 4. Enums vs Text

```sql
-- Use TEXT with CHECK for simple cases
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))
);

-- Use ENUM for complex/shared types
CREATE TYPE order_status AS ENUM (
  'pending', 'processing', 'shipped', 'delivered', 'cancelled'
);

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status order_status NOT NULL DEFAULT 'pending'
);
```

## Indexing Strategy

### Basic Indexes

```sql
-- B-tree (default) - equality and range queries
CREATE INDEX idx_posts_author ON posts(author_id);
CREATE INDEX idx_posts_created ON posts(created_at DESC);

-- Composite index - for multi-column queries
CREATE INDEX idx_posts_author_status ON posts(author_id, status);
```

### Specialized Indexes

```sql
-- Partial index - for filtered queries
CREATE INDEX idx_active_posts ON posts(created_at)
  WHERE status = 'published';

-- GIN index - for JSONB and array operations
CREATE INDEX idx_posts_tags ON posts USING GIN(tags);

-- Full-text search
CREATE INDEX idx_posts_fts ON posts
  USING GIN(to_tsvector('english', title || ' ' || content));

-- Trigram for LIKE queries
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_users_name_trgm ON users USING GIN(name gin_trgm_ops);
```

### Index for RLS Policies

```sql
-- CRITICAL: Index every column used in RLS policies
-- Policy: USING (user_id = auth.uid())
CREATE INDEX idx_todos_user ON todos(user_id);

-- Policy: USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::UUID)
CREATE INDEX idx_items_tenant ON items(tenant_id);

-- Policy with JOIN
-- USING (EXISTS (SELECT 1 FROM memberships WHERE user_id = auth.uid() AND org_id = items.org_id))
CREATE INDEX idx_memberships_user_org ON memberships(user_id, org_id);
```

## Query Optimization

### Use EXPLAIN ANALYZE

```sql
-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM posts
WHERE author_id = 'user-uuid'
  AND status = 'published'
ORDER BY created_at DESC
LIMIT 10;

-- Look for:
-- - Seq Scan (may need index)
-- - High cost estimates
-- - Rows significantly different from estimate
```

### Common Optimizations

```sql
-- BAD: SELECT * with no limit
SELECT * FROM large_table;

-- GOOD: Select specific columns with limit
SELECT id, title, created_at FROM large_table
ORDER BY created_at DESC
LIMIT 20;

-- BAD: N+1 queries
-- (fetching posts then comments for each)

-- GOOD: Join or use Supabase's select with relations
SELECT
  p.*,
  json_agg(c.*) as comments
FROM posts p
LEFT JOIN comments c ON c.post_id = p.id
WHERE p.author_id = 'user-uuid'
GROUP BY p.id;
```

### Database Functions for Complex Queries

```sql
-- Encapsulate complex logic in functions
CREATE OR REPLACE FUNCTION get_user_feed(p_user_id UUID, p_limit INT DEFAULT 20)
RETURNS TABLE (
  id UUID,
  title TEXT,
  author_name TEXT,
  comment_count BIGINT,
  created_at TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.title,
    pr.full_name as author_name,
    COUNT(c.id) as comment_count,
    p.created_at
  FROM posts p
  JOIN profiles pr ON pr.id = p.author_id
  LEFT JOIN comments c ON c.post_id = p.id
  WHERE p.author_id IN (
    SELECT following_id FROM follows WHERE follower_id = p_user_id
  )
  AND p.status = 'published'
  GROUP BY p.id, pr.full_name
  ORDER BY p.created_at DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Call from client
const { data } = await supabase.rpc('get_user_feed', { p_user_id: userId });
```

## JSONB Best Practices

### When to Use JSONB

- Flexible schema (user preferences, metadata)
- Varying attributes per row
- API responses storage
- Event data

### When NOT to Use JSONB

- Structured data with known schema (use columns)
- Frequently queried fields (extract to columns)
- Data requiring foreign key constraints

### JSONB Patterns

```sql
-- Store flexible metadata
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  price_cents INTEGER NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Query JSONB
SELECT * FROM products
WHERE metadata->>'color' = 'red';

-- Index JSONB for specific keys
CREATE INDEX idx_products_color ON products((metadata->>'color'));

-- Index entire JSONB with GIN
CREATE INDEX idx_products_metadata ON products USING GIN(metadata);

-- Update JSONB
UPDATE products
SET metadata = metadata || '{"featured": true}'::jsonb
WHERE id = 'product-uuid';
```

### Generated Columns from JSONB

```sql
-- Extract frequently queried JSONB fields to columns
ALTER TABLE products ADD COLUMN category TEXT
  GENERATED ALWAYS AS (metadata->>'category') STORED;

CREATE INDEX idx_products_category ON products(category);
```

## Migrations Best Practices

### Naming Convention

```
YYYYMMDDHHMMSS_description.sql
20240115120000_create_users_table.sql
20240115130000_add_profiles_table.sql
20240116100000_add_posts_indexes.sql
```

### Safe Migration Patterns

```sql
-- Always use IF NOT EXISTS / IF EXISTS
CREATE TABLE IF NOT EXISTS users (...);
DROP TABLE IF EXISTS temp_table;
ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;

-- Create index concurrently (no lock)
CREATE INDEX CONCURRENTLY idx_posts_title ON posts(title);

-- Add column with default (no rewrite in PostgreSQL 11+)
ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active';

-- Backfill in batches for large tables
DO $$
DECLARE
  batch_size INT := 1000;
  affected INT;
BEGIN
  LOOP
    UPDATE users
    SET computed_field = expensive_calculation(data)
    WHERE id IN (
      SELECT id FROM users
      WHERE computed_field IS NULL
      LIMIT batch_size
    );
    GET DIAGNOSTICS affected = ROW_COUNT;
    EXIT WHEN affected = 0;
    COMMIT;
  END LOOP;
END $$;
```

### Avoiding Downtime

```sql
-- BAD: Rename column (breaks queries)
ALTER TABLE users RENAME COLUMN name TO full_name;

-- GOOD: Add new column, migrate data, deprecate old
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN full_name TEXT;

-- Step 2: Copy data
UPDATE users SET full_name = name WHERE full_name IS NULL;

-- Step 3: Add trigger for sync during transition
CREATE TRIGGER sync_name_columns
  BEFORE INSERT OR UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION sync_name_to_full_name();

-- Step 4: Update application code
-- Step 5: Remove old column (after app is updated)
ALTER TABLE users DROP COLUMN name;
```

## Constraints and Validation

```sql
-- NOT NULL with defaults
ALTER TABLE users ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE users ALTER COLUMN created_at SET NOT NULL;

-- CHECK constraints
ALTER TABLE products ADD CONSTRAINT positive_price
  CHECK (price_cents > 0);

ALTER TABLE users ADD CONSTRAINT valid_email
  CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- UNIQUE constraints
ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);

-- Composite unique
ALTER TABLE memberships ADD CONSTRAINT unique_user_org
  UNIQUE (user_id, org_id);

-- Exclusion constraints (no overlapping ranges)
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE reservations ADD CONSTRAINT no_overlap
  EXCLUDE USING GIST (
    room_id WITH =,
    tstzrange(start_time, end_time) WITH &&
  );
```

## Connection Management

### Supavisor (Built-in Pooler)

```typescript
// Transaction mode (default) - best for serverless
const supabase = createClient(
  'https://xxx.supabase.co',
  'anon-key',
  {
    db: {
      schema: 'public'
    }
  }
);

// Session mode - for prepared statements, LISTEN/NOTIFY
// Use port 5432 directly instead of pooler
```

### Direct Connection (When Needed)

```typescript
import { Pool } from 'pg';

// For migrations, admin tasks, or session-mode requirements
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30000
});
```

## Monitoring Queries

```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top slow queries
SELECT
  query,
  calls,
  round(mean_exec_time::numeric, 2) as avg_ms,
  round(total_exec_time::numeric, 2) as total_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Most called queries
SELECT query, calls
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 20;

-- Reset stats
SELECT pg_stat_statements_reset();
```
