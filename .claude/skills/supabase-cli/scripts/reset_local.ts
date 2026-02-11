#!/usr/bin/env bun
/**
 * Local Database Reset
 * Resets local database, applies migrations, and optionally runs seed.
 *
 * Usage:
 *   bun reset_local.ts [--no-seed] [--confirm]
 *
 * Options:
 *   --no-seed   Skip running seed file after reset
 *   --confirm   Skip confirmation prompt
 *
 * Example:
 *   bun reset_local.ts
 *   bun reset_local.ts --no-seed
 */

import { existsSync } from "fs";
import { join } from "path";
import { $ } from "bun";

const args = process.argv.slice(2);

const flags = {
  noSeed: args.includes("--no-seed"),
  confirm: args.includes("--confirm"),
};

async function main() {
  console.log("=" + "=".repeat(59));
  console.log(" LOCAL DATABASE RESET");
  console.log("=" + "=".repeat(59));

  // Check if supabase is running
  console.log("\nChecking local Supabase status...");

  try {
    const status = await $`supabase status`.quiet();
    if (!status.stdout.toString().includes("DB URL")) {
      console.log("⚠️  Local Supabase doesn't appear to be running.");
      console.log("Start it with: supabase start");
      process.exit(1);
    }
    console.log("✓ Local Supabase is running");
  } catch {
    console.log("⚠️  Could not check Supabase status.");
    console.log("Make sure local Supabase is running: supabase start");
    process.exit(1);
  }

  // Check for seed file
  const seedPaths = [
    join(process.cwd(), "supabase", "seed.sql"),
    join(process.cwd(), "scripts", "seed-data.ts"),
    join(process.cwd(), "scripts", "seed.ts"),
  ];

  const seedFile = seedPaths.find((p) => existsSync(p));

  console.log("\n" + "-".repeat(60));
  console.log("RESET PLAN:");
  console.log("-".repeat(60));
  console.log("  1. Drop and recreate local database");
  console.log("  2. Apply all migrations");
  if (!flags.noSeed && seedFile) {
    console.log(`  3. Run seed: ${seedFile.replace(process.cwd() + "/", "")}`);
  } else if (flags.noSeed) {
    console.log("  3. Skip seeding (--no-seed)");
  } else {
    console.log("  3. No seed file found");
  }

  // Confirm
  if (!flags.confirm) {
    console.log("\n⚠️  This will DESTROY all local data!");
    process.stdout.write("Continue? [y/N]: ");

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

  // Reset database
  console.log("\n" + "-".repeat(60));
  console.log("Resetting database...");

  try {
    await $`supabase db reset`;
    console.log("✓ Database reset complete");
  } catch (error) {
    console.error("❌ Database reset failed!");
    console.error(error);
    process.exit(1);
  }

  // Run seed if applicable
  if (!flags.noSeed && seedFile) {
    console.log("\n" + "-".repeat(60));
    console.log(`Running seed: ${seedFile}`);

    try {
      if (seedFile.endsWith(".sql")) {
        // SQL seed is run automatically by supabase db reset
        console.log("✓ SQL seed applied during reset");
      } else if (seedFile.endsWith(".ts")) {
        await $`bun ${seedFile}`;
        console.log("✓ TypeScript seed complete");
      }
    } catch (error) {
      console.error("⚠️  Seed failed (database still reset)");
      console.error(error);
    }
  }

  // Summary
  console.log("\n" + "=".repeat(60));
  console.log("✓ LOCAL RESET COMPLETE");
  console.log("=".repeat(60));
  console.log("\nLocal database is ready with fresh schema.");
  console.log("\nNext steps:");
  console.log("  - Test your application");
  console.log("  - Update types: bun .claude/skills/supabase-cli/scripts/update_types.ts");
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
