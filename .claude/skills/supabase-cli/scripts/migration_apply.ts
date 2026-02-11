#!/usr/bin/env bun
/**
 * Migration Applier
 * Applies migrations to local or remote database with safety checks.
 *
 * Usage:
 *   bun migration_apply.ts --local
 *   bun migration_apply.ts --remote --confirm
 *   bun migration_apply.ts --dry-run
 *
 * Options:
 *   --local     Apply to local database
 *   --remote    Apply to remote database (requires --confirm)
 *   --confirm   Required for remote operations
 *   --dry-run   Show what would be applied without making changes
 */

import { readdirSync, readFileSync, existsSync } from "fs";
import { join } from "path";
import { $ } from "bun";

const args = process.argv.slice(2);

const flags = {
  local: args.includes("--local"),
  remote: args.includes("--remote"),
  confirm: args.includes("--confirm"),
  dryRun: args.includes("--dry-run"),
};

// Validation
if (!flags.local && !flags.remote && !flags.dryRun) {
  console.error("Usage: bun migration_apply.ts [--local | --remote] [--confirm] [--dry-run]");
  console.error("\nOptions:");
  console.error("  --local     Apply to local database");
  console.error("  --remote    Apply to remote database (requires --confirm)");
  console.error("  --confirm   Required for remote operations");
  console.error("  --dry-run   Show pending migrations without applying");
  process.exit(1);
}

if (flags.local && flags.remote) {
  console.error("Error: Cannot specify both --local and --remote");
  process.exit(1);
}

if (flags.remote && !flags.confirm) {
  console.error("Error: Remote migrations require --confirm flag");
  console.error("\nThis is a safety measure. Remote migrations affect production data.");
  console.error("If you're sure, run with: bun migration_apply.ts --remote --confirm");
  process.exit(1);
}

const migrationsDir = join(process.cwd(), "supabase", "migrations");

async function getMigrationStatus(): Promise<{ pending: string[]; applied: string[] }> {
  const pending: string[] = [];
  const applied: string[] = [];

  if (!existsSync(migrationsDir)) {
    console.log("No migrations directory found.");
    return { pending, applied };
  }

  const files = readdirSync(migrationsDir)
    .filter((f) => f.endsWith(".sql"))
    .sort();

  // Get applied migrations from supabase
  try {
    const target = flags.remote ? "--linked" : "--local";
    const result = await $`supabase migration list ${target}`.quiet();
    const output = result.stdout.toString();

    // Parse migration list output
    const appliedVersions = new Set<string>();
    for (const line of output.split("\n")) {
      // Format: "20240101000000 │ applied │ name"
      const match = line.match(/^(\d+)/);
      if (match) {
        appliedVersions.add(match[1]);
      }
    }

    for (const file of files) {
      const version = file.match(/^(\d+)_/)?.[1];
      if (version && appliedVersions.has(version)) {
        applied.push(file);
      } else {
        pending.push(file);
      }
    }
  } catch {
    // If migration list fails, assume all are pending
    pending.push(...files);
  }

  return { pending, applied };
}

async function analyzeMigration(filename: string): Promise<{
  hasDestructive: boolean;
  statements: string[];
}> {
  const filepath = join(migrationsDir, filename);
  const content = readFileSync(filepath, "utf-8");

  const destructivePatterns = [
    /\bDROP\s+TABLE\b/i,
    /\bDROP\s+COLUMN\b/i,
    /\bTRUNCATE\b/i,
    /\bDELETE\s+FROM\s+\w+\s*;/i, // DELETE without WHERE
    /\bDROP\s+DATABASE\b/i,
    /\bDROP\s+SCHEMA\b/i,
  ];

  const hasDestructive = destructivePatterns.some((p) => p.test(content));

  // Extract key statements
  const statements: string[] = [];
  const lines = content.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (
      trimmed &&
      !trimmed.startsWith("--") &&
      !trimmed.startsWith("/*") &&
      trimmed !== "BEGIN;" &&
      trimmed !== "COMMIT;"
    ) {
      // Get first 80 chars of significant statements
      if (
        /^(CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|GRANT|REVOKE)/i.test(trimmed)
      ) {
        statements.push(trimmed.slice(0, 80) + (trimmed.length > 80 ? "..." : ""));
      }
    }
  }

  return { hasDestructive, statements: statements.slice(0, 10) };
}

async function applyMigrations() {
  const target = flags.remote ? "REMOTE" : "LOCAL";

  console.log("=" + "=".repeat(59));
  console.log(` SUPABASE MIGRATION APPLY [${target}]`);
  console.log("=" + "=".repeat(59));

  const { pending, applied } = await getMigrationStatus();

  console.log(`\nMigrations directory: ${migrationsDir}`);
  console.log(`Applied: ${applied.length}`);
  console.log(`Pending: ${pending.length}`);

  if (pending.length === 0) {
    console.log("\n✓ All migrations are already applied.");
    return;
  }

  console.log("\n" + "-".repeat(60));
  console.log("PENDING MIGRATIONS:");
  console.log("-".repeat(60));

  let hasDestructive = false;

  for (const file of pending) {
    const analysis = await analyzeMigration(file);
    const warning = analysis.hasDestructive ? " ⚠️  DESTRUCTIVE" : "";
    console.log(`\n${file}${warning}`);

    if (analysis.statements.length > 0) {
      for (const stmt of analysis.statements.slice(0, 5)) {
        console.log(`  ${stmt}`);
      }
      if (analysis.statements.length > 5) {
        console.log(`  ... and ${analysis.statements.length - 5} more`);
      }
    }

    if (analysis.hasDestructive) {
      hasDestructive = true;
    }
  }

  if (flags.dryRun) {
    console.log("\n" + "-".repeat(60));
    console.log("DRY RUN - No changes made");
    return;
  }

  if (hasDestructive && flags.remote) {
    console.log("\n⚠️  WARNING: Pending migrations contain destructive operations!");
    console.log("Review the above carefully before proceeding.");
  }

  // Confirm before applying
  if (flags.remote) {
    console.log("\n" + "-".repeat(60));
    process.stdout.write("Apply migrations to REMOTE database? [y/N]: ");

    const response = await new Promise<string>((resolve) => {
      process.stdin.once("data", (data) => {
        resolve(data.toString().trim().toLowerCase());
      });
    });

    if (response !== "y") {
      console.log("Aborted.");
      process.exit(0);
    }
  }

  // Apply migrations
  console.log("\n" + "-".repeat(60));
  console.log(`Applying migrations to ${target}...`);

  try {
    if (flags.remote) {
      await $`supabase db push --linked`;
    } else {
      await $`supabase db push`;
    }

    console.log("\n✓ Migrations applied successfully!");

    // Suggest next steps
    console.log("\nNext steps:");
    console.log("  1. Verify changes in database");
    if (flags.local) {
      console.log("  2. Test application locally");
      console.log("  3. When ready, apply to remote: bun migration_apply.ts --remote --confirm");
    }
    console.log("  4. Update TypeScript types: bun .claude/skills/supabase-cli/scripts/update_types.ts");
  } catch (error) {
    console.error("\n❌ Migration failed!");
    console.error(error);
    process.exit(1);
  }
}

applyMigrations().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
