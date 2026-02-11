#!/usr/bin/env bun
/**
 * RLS Policy Scaffolder
 * Generates RLS policy templates for tables.
 *
 * Usage:
 *   bun scaffold_rls.ts <table_name> [--output file.sql]
 *
 * Options:
 *   --output PATH   Write to file instead of stdout
 *   --tenant        Generate multi-tenant policies
 *   --public-read   Allow public read access
 *
 * Example:
 *   bun scaffold_rls.ts products
 *   bun scaffold_rls.ts orders --tenant
 *   bun scaffold_rls.ts menu_items --output supabase/migrations/015_rls_menu_items.sql
 */

import { writeFileSync } from "fs";

const args = process.argv.slice(2);

// Get table name
const tableName = args.filter((a) => !a.startsWith("--"))[0];

// Get flags
const flags = {
  tenant: args.includes("--tenant"),
  publicRead: args.includes("--public-read"),
};

// Get output path
let outputPath: string | undefined;
const outputIndex = args.findIndex((a) => a === "--output");
if (outputIndex !== -1 && args[outputIndex + 1]) {
  outputPath = args[outputIndex + 1];
}

if (!tableName) {
  console.error("Usage: bun scaffold_rls.ts <table_name> [options]");
  console.error("\nOptions:");
  console.error("  --output PATH   Write to file instead of stdout");
  console.error("  --tenant        Generate multi-tenant policies");
  console.error("  --public-read   Allow public read access");
  console.error("\nExample:");
  console.error("  bun scaffold_rls.ts products");
  console.error("  bun scaffold_rls.ts orders --tenant");
  process.exit(1);
}

// Validate table name
const validName = /^[a-z][a-z0-9_]*$/;
if (!validName.test(tableName)) {
  console.error("Error: Table name must be lowercase alphanumeric with underscores");
  process.exit(1);
}

function generateStandardPolicies(): string {
  return `-- RLS Policies for: ${tableName}
-- Generated: ${new Date().toISOString().split("T")[0]}
-- Author: George Khananaev

-- ============================================================================
-- ENABLE RLS
-- ============================================================================

ALTER TABLE public.${tableName} ENABLE ROW LEVEL SECURITY;

-- Force RLS even for table owners (recommended for security)
ALTER TABLE public.${tableName} FORCE ROW LEVEL SECURITY;

-- ============================================================================
-- SELECT POLICIES
-- ============================================================================

-- Allow authenticated users to read their own records
CREATE POLICY "${tableName}_select_own"
  ON public.${tableName}
  FOR SELECT
  TO authenticated
  USING (
    -- Adjust condition based on your user relationship
    user_id = auth.uid()
    -- OR: created_by = auth.uid()
    -- OR: restaurant_id IN (SELECT restaurant_id FROM staff WHERE user_id = auth.uid())
  );

${
  flags.publicRead
    ? `-- Allow anonymous read access (public data)
CREATE POLICY "${tableName}_select_anon"
  ON public.${tableName}
  FOR SELECT
  TO anon
  USING (
    is_public = true
    -- OR: is_active = true
  );
`
    : `-- Uncomment to allow anonymous read access:
-- CREATE POLICY "${tableName}_select_anon"
--   ON public.${tableName}
--   FOR SELECT
--   TO anon
--   USING (is_public = true);
`
}
-- ============================================================================
-- INSERT POLICIES
-- ============================================================================

-- Allow authenticated users to insert their own records
CREATE POLICY "${tableName}_insert_own"
  ON public.${tableName}
  FOR INSERT
  TO authenticated
  WITH CHECK (
    -- Ensure user_id matches authenticated user
    user_id = auth.uid()
  );

-- ============================================================================
-- UPDATE POLICIES
-- ============================================================================

-- Allow users to update their own records
CREATE POLICY "${tableName}_update_own"
  ON public.${tableName}
  FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- ============================================================================
-- DELETE POLICIES
-- ============================================================================

-- Allow users to delete their own records
-- Consider using soft deletes instead
CREATE POLICY "${tableName}_delete_own"
  ON public.${tableName}
  FOR DELETE
  TO authenticated
  USING (user_id = auth.uid());

-- ============================================================================
-- INDEXES FOR RLS PERFORMANCE
-- ============================================================================

-- IMPORTANT: Index columns used in RLS policies for performance
CREATE INDEX IF NOT EXISTS idx_${tableName}_user_id
  ON public.${tableName}(user_id);

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant basic permissions to authenticated role
GRANT SELECT, INSERT, UPDATE, DELETE ON public.${tableName} TO authenticated;

-- Grant read-only to anon if needed
-- GRANT SELECT ON public.${tableName} TO anon;
`;
}

function generateTenantPolicies(): string {
  return `-- Multi-Tenant RLS Policies for: ${tableName}
-- Generated: ${new Date().toISOString().split("T")[0]}
-- Author: George Khananaev

-- ============================================================================
-- ENABLE RLS
-- ============================================================================

ALTER TABLE public.${tableName} ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.${tableName} FORCE ROW LEVEL SECURITY;

-- ============================================================================
-- TENANT ISOLATION POLICIES
-- ============================================================================

-- Helper function to get current user's tenant (if not exists)
-- CREATE OR REPLACE FUNCTION get_user_tenant_id()
-- RETURNS UUID AS $$
--   SELECT (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::UUID;
-- $$ LANGUAGE sql SECURITY DEFINER STABLE;

-- Or use staff table lookup:
-- CREATE OR REPLACE FUNCTION get_user_restaurant_id()
-- RETURNS UUID AS $$
--   SELECT restaurant_id FROM staff WHERE user_id = auth.uid() LIMIT 1;
-- $$ LANGUAGE sql SECURITY DEFINER STABLE;

-- SELECT: Users can only see records from their tenant
CREATE POLICY "${tableName}_tenant_select"
  ON public.${tableName}
  FOR SELECT
  TO authenticated
  USING (
    restaurant_id IN (
      SELECT restaurant_id FROM staff WHERE user_id = auth.uid()
    )
  );

-- INSERT: Users can only insert into their tenant
CREATE POLICY "${tableName}_tenant_insert"
  ON public.${tableName}
  FOR INSERT
  TO authenticated
  WITH CHECK (
    restaurant_id IN (
      SELECT restaurant_id FROM staff WHERE user_id = auth.uid()
    )
  );

-- UPDATE: Users can only update their tenant's records
CREATE POLICY "${tableName}_tenant_update"
  ON public.${tableName}
  FOR UPDATE
  TO authenticated
  USING (
    restaurant_id IN (
      SELECT restaurant_id FROM staff WHERE user_id = auth.uid()
    )
  )
  WITH CHECK (
    restaurant_id IN (
      SELECT restaurant_id FROM staff WHERE user_id = auth.uid()
    )
  );

-- DELETE: Users can only delete their tenant's records
CREATE POLICY "${tableName}_tenant_delete"
  ON public.${tableName}
  FOR DELETE
  TO authenticated
  USING (
    restaurant_id IN (
      SELECT restaurant_id FROM staff WHERE user_id = auth.uid()
    )
  );

-- ============================================================================
-- ROLE-BASED POLICIES (Optional)
-- ============================================================================

-- Managers can do everything in their tenant
CREATE POLICY "${tableName}_manager_all"
  ON public.${tableName}
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM staff
      WHERE staff.user_id = auth.uid()
        AND staff.restaurant_id = ${tableName}.restaurant_id
        AND staff.role IN ('owner', 'manager')
    )
  );

-- ============================================================================
-- INDEXES FOR RLS PERFORMANCE
-- ============================================================================

-- CRITICAL: Index tenant column for RLS performance
CREATE INDEX IF NOT EXISTS idx_${tableName}_restaurant_id
  ON public.${tableName}(restaurant_id);

-- Composite index if filtering by tenant + other columns
-- CREATE INDEX IF NOT EXISTS idx_${tableName}_restaurant_status
--   ON public.${tableName}(restaurant_id, status);

-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON public.${tableName} TO authenticated;
`;
}

// Generate output
const output = flags.tenant ? generateTenantPolicies() : generateStandardPolicies();

if (outputPath) {
  writeFileSync(outputPath, output);
  console.log(`✓ RLS policies written to: ${outputPath}`);
  console.log("\nNext steps:");
  console.log("  1. Review and customize the generated policies");
  console.log("  2. Apply: bun .claude/skills/supabase-cli/scripts/migration_apply.ts --local");
  console.log("  3. Test RLS with different user contexts");
} else {
  console.log(output);
}
