# Safe Migration Patterns

Best practices for writing and applying database migrations with Supabase.

## Migration File Structure

### Standard Template

```sql
-- Migration: <description>
-- Created: <timestamp>

BEGIN;

-- Migration code here

COMMIT;
```

### With Rollback Plan

```sql
-- Migration: add_user_roles
-- Created: 2026-02-05

BEGIN;

-- Forward migration
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'staff');
ALTER TABLE users ADD COLUMN role user_role DEFAULT 'staff';

-- To rollback:
-- ALTER TABLE users DROP COLUMN role;
-- DROP TYPE user_role;

COMMIT;
```

## Safe DDL Patterns

### Adding Columns

```sql
-- Safe: Add nullable column (no lock)
ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname TEXT;

-- Safe: Add with default (Postgres 11+ is instant)
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;

-- Avoid: Adding NOT NULL without default (table rewrite)
-- ALTER TABLE users ADD COLUMN nickname TEXT NOT NULL; -- BLOCKS
```

### Dropping Columns

```sql
-- Safe: Use IF EXISTS
ALTER TABLE users DROP COLUMN IF EXISTS deprecated_field;

-- Multi-step for production:
-- 1. Stop writing to column (code change)
-- 2. Deploy code
-- 3. Drop column in next migration
```

### Adding Indexes

```sql
-- Safe: CONCURRENTLY prevents locking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email
  ON users(email);

-- Note: Cannot run CONCURRENTLY inside transaction
-- Must be run separately or use:
SET statement_timeout = '0';
CREATE INDEX CONCURRENTLY ...
```

### Renaming Objects

```sql
-- Safe: Table rename
ALTER TABLE old_name RENAME TO new_name;

-- Safe: Column rename
ALTER TABLE users RENAME COLUMN old_col TO new_col;

-- Caution: May break application code
-- Use expand-contract pattern instead
```

## Expand-Contract Pattern

For breaking changes, use the expand-contract pattern:

### Step 1: Expand (Add New)

```sql
-- Migration: 001_add_email_new
ALTER TABLE users ADD COLUMN email_new TEXT;

-- Trigger to sync old → new
CREATE FUNCTION sync_email() RETURNS TRIGGER AS $$
BEGIN
  NEW.email_new = NEW.email;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sync_email_trigger
  BEFORE INSERT OR UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION sync_email();
```

### Step 2: Backfill

```sql
-- Migration: 002_backfill_email
UPDATE users SET email_new = email WHERE email_new IS NULL;
```

### Step 3: Switch Application

Deploy code that writes to both columns, reads from new.

### Step 4: Contract (Remove Old)

```sql
-- Migration: 003_drop_email_old
DROP TRIGGER sync_email_trigger ON users;
DROP FUNCTION sync_email();
ALTER TABLE users DROP COLUMN email;
ALTER TABLE users RENAME COLUMN email_new TO email;
```

## Table Operations

### Creating Tables

```sql
CREATE TABLE IF NOT EXISTS products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Always add indexes for foreign keys
CREATE INDEX IF NOT EXISTS idx_products_restaurant
  ON products(restaurant_id);

-- Add RLS
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
```

### Dropping Tables

```sql
-- Safe: Cascade drops dependent objects
DROP TABLE IF EXISTS old_table CASCADE;

-- Caution: May drop more than expected
-- List dependencies first:
-- SELECT * FROM pg_depend WHERE refobjid = 'old_table'::regclass;
```

## Enum Modifications

### Adding Values

```sql
-- Safe: Add value to enum
ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'processing';

-- Note: Cannot remove enum values in Postgres
-- Must recreate the type
```

### Modifying Enums (Complex)

```sql
-- Rename enum type
ALTER TYPE old_status RENAME TO old_status_deprecated;

-- Create new type
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped');

-- Migrate columns
ALTER TABLE orders
  ALTER COLUMN status TYPE order_status
  USING status::text::order_status;

-- Drop old type
DROP TYPE old_status_deprecated;
```

## RLS Policies

### Adding Policies

```sql
-- Enable RLS first
ALTER TABLE items ENABLE ROW LEVEL SECURITY;

-- Add policy
CREATE POLICY "items_select_policy" ON items
  FOR SELECT
  USING (restaurant_id = (
    SELECT restaurant_id FROM staff
    WHERE user_id = auth.uid()
  ));

-- Force RLS for owners too
ALTER TABLE items FORCE ROW LEVEL SECURITY;
```

### Modifying Policies

```sql
-- Safe: Drop and recreate
DROP POLICY IF EXISTS "items_select_policy" ON items;

CREATE POLICY "items_select_policy" ON items
  FOR SELECT
  USING (true); -- Updated condition
```

## Data Migrations

### Backfilling Data

```sql
-- Batch update for large tables
DO $$
DECLARE
  batch_size INT := 1000;
  total_updated INT := 0;
BEGIN
  LOOP
    WITH batch AS (
      SELECT id FROM users
      WHERE new_column IS NULL
      LIMIT batch_size
      FOR UPDATE SKIP LOCKED
    )
    UPDATE users u
    SET new_column = compute_value(u.old_column)
    FROM batch b
    WHERE u.id = b.id;

    GET DIAGNOSTICS total_updated = ROW_COUNT;
    EXIT WHEN total_updated < batch_size;

    COMMIT;
    PERFORM pg_sleep(0.1); -- Reduce load
  END LOOP;
END $$;
```

### Seeding Reference Data

```sql
-- Idempotent inserts
INSERT INTO categories (id, name, display_order)
VALUES
  ('cat-1', 'Appetizers', 1),
  ('cat-2', 'Main Course', 2),
  ('cat-3', 'Desserts', 3)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  display_order = EXCLUDED.display_order;
```

## Migration Naming Convention

Follow this project's convention:

```
<number>_<description>.sql

Examples:
001_initial_schema.sql
002_seed_data.sql
010_add_menu_item_archive.sql
011_add_menu_item_options.sql
```

Use 3-digit numbering with gaps (001, 002, 010, 011) to allow insertions.

## Rollback Strategies

### Option 1: Reverse Migration

Create a down migration file:

```sql
-- 010_add_feature_down.sql
BEGIN;
ALTER TABLE users DROP COLUMN feature_flag;
COMMIT;
```

### Option 2: In-Migration Comments

```sql
-- Migration: add_feature
-- Rollback: ALTER TABLE users DROP COLUMN feature_flag;
ALTER TABLE users ADD COLUMN feature_flag BOOLEAN DEFAULT false;
```

### Option 3: Database Branching (Pro+)

```bash
# Create branch before risky migration
supabase branches create pre-migration-backup

# Apply migration
supabase db push --linked

# If failed, switch back
supabase branches switch pre-migration-backup
```

## Pre-Migration Checklist

- [ ] Tested on local database
- [ ] No long-running locks (use CONCURRENTLY)
- [ ] IF EXISTS / IF NOT EXISTS used
- [ ] Rollback plan documented
- [ ] Data backfill uses batching
- [ ] RLS policies tested
- [ ] TypeScript types will regenerate cleanly
