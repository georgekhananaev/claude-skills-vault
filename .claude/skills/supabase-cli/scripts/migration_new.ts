#!/usr/bin/env bun
/**
 * Migration Creator
 * Creates a new timestamped migration file with proper template.
 *
 * Usage: bun migration_new.ts <name> [--dry-run]
 * Example: bun migration_new.ts add_user_roles
 * Example: bun migration_new.ts add-feature --dry-run
 */

import { readdirSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";

const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const name = args.filter((a) => !a.startsWith("--"))[0];

if (!name) {
  console.error("Usage: bun migration_new.ts <name> [--dry-run]");
  console.error("Example: bun migration_new.ts add_user_roles");
  process.exit(1);
}

// Validate migration name
const validName = /^[a-z][a-z0-9_-]*$/;
if (!validName.test(name.toLowerCase())) {
  console.error("Error: Migration name must be lowercase alphanumeric with underscores/dashes");
  console.error("Example: add_user_roles, fix-bug, update-schema");
  process.exit(1);
}

// Find migrations directory
const migrationsDir = join(process.cwd(), "supabase", "migrations");

if (!existsSync(migrationsDir)) {
  console.log(`Creating migrations directory: ${migrationsDir}`);
  if (!dryRun) {
    mkdirSync(migrationsDir, { recursive: true });
  }
}

// Find highest migration number
let highestNum = 0;

try {
  const files = readdirSync(migrationsDir);
  for (const file of files) {
    if (file.endsWith(".sql")) {
      const match = file.match(/^(\d+)_/);
      if (match) {
        const num = parseInt(match[1], 10);
        if (num > highestNum) {
          highestNum = num;
        }
      }
    }
  }
} catch {
  // Directory might not exist yet
}

// Calculate next number with gap for future insertions
const nextNum = highestNum + 1;
// Use 3-digit padding with gaps (1, 2, 10, 11, 20, etc.)
const paddedNum = String(nextNum).padStart(3, "0");

// Normalize name: convert dashes to underscores
const normalizedName = name.toLowerCase().replace(/-/g, "_");

const fileName = `${paddedNum}_${normalizedName}.sql`;
const filePath = join(migrationsDir, fileName);

// Generate migration template
const template = `-- Migration: ${normalizedName}
-- Created: ${new Date().toISOString().split("T")[0]}
-- Author: George Khananaev

BEGIN;

-- ============================================================================
-- MIGRATION: ${normalizedName.toUpperCase().replace(/_/g, " ")}
-- ============================================================================

-- Add your migration SQL here
-- Example:
-- ALTER TABLE users ADD COLUMN new_field TEXT;
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_name ON table(column);

-- ============================================================================
-- ROLLBACK (for reference):
-- ============================================================================
-- To undo this migration:
-- ALTER TABLE users DROP COLUMN new_field;

COMMIT;
`;

console.log("=" + "=".repeat(59));
console.log(" SUPABASE MIGRATION CREATOR");
console.log("=" + "=".repeat(59));
console.log(`\nMigrations dir: ${migrationsDir}`);
console.log(`Previous highest: ${highestNum || "(none)"}`);
console.log(`New migration: ${fileName}`);
console.log(`Mode: ${dryRun ? "DRY RUN" : "CREATE"}`);

if (dryRun) {
  console.log("\n" + "-".repeat(60));
  console.log("WOULD CREATE:");
  console.log("-".repeat(60));
  console.log(template);
  console.log("-".repeat(60));
  console.log("\nDry run complete. Use without --dry-run to create the file.");
} else {
  // Check if file already exists
  if (existsSync(filePath)) {
    console.error(`\nError: File already exists: ${filePath}`);
    process.exit(1);
  }

  // Write the file
  writeFileSync(filePath, template);

  console.log("\n✓ Migration file created!");
  console.log("\nNext steps:");
  console.log(`  1. Edit: ${filePath}`);
  console.log("  2. Test locally: bun .claude/skills/supabase-cli/scripts/migration_apply.ts --local");
  console.log("  3. Generate types: bun .claude/skills/supabase-cli/scripts/update_types.ts");
}
