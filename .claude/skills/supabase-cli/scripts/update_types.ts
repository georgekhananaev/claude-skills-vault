#!/usr/bin/env bun
/**
 * TypeScript Type Generator
 * Generates TypeScript types from Supabase schema.
 *
 * Usage:
 *   bun update_types.ts [--local | --remote] [--output path]
 *
 * Options:
 *   --local       Generate from local database (default)
 *   --remote      Generate from remote/linked database
 *   --output PATH Output file path (default: src/types/supabase.ts)
 *   --show-diff   Show diff with existing file
 */

import { existsSync, readFileSync, writeFileSync, mkdirSync } from "fs";
import { dirname, join } from "path";
import { $ } from "bun";

const args = process.argv.slice(2);

const flags = {
  local: args.includes("--local"),
  remote: args.includes("--remote"),
  showDiff: args.includes("--show-diff"),
};

// Get output path
let outputPath = "src/types/supabase.ts";
const outputIndex = args.findIndex((a) => a === "--output");
if (outputIndex !== -1 && args[outputIndex + 1]) {
  outputPath = args[outputIndex + 1];
}

// Default to local if neither specified
if (!flags.local && !flags.remote) {
  flags.local = true;
}

if (flags.local && flags.remote) {
  console.error("Error: Cannot specify both --local and --remote");
  process.exit(1);
}

async function generateTypes() {
  const source = flags.remote ? "remote" : "local";

  console.log("=" + "=".repeat(59));
  console.log(" SUPABASE TYPE GENERATOR");
  console.log("=" + "=".repeat(59));
  console.log(`\nSource: ${source}`);
  console.log(`Output: ${outputPath}`);

  // Check if output file exists for diff
  const existingContent = existsSync(outputPath)
    ? readFileSync(outputPath, "utf-8")
    : null;

  console.log(`\nExisting file: ${existingContent ? "Yes" : "No"}`);

  // Generate types
  console.log("\nGenerating types...");

  try {
    let result;
    if (flags.remote) {
      result = await $`supabase gen types typescript --linked`.quiet();
    } else {
      result = await $`supabase gen types typescript --local`.quiet();
    }

    const newContent = result.stdout.toString();

    if (!newContent || newContent.length < 100) {
      console.error("Error: Generated types are empty or too short.");
      console.error("Make sure Supabase local is running or you're linked to a project.");
      process.exit(1);
    }

    // Show diff if requested
    if (flags.showDiff && existingContent) {
      console.log("\n" + "-".repeat(60));
      console.log("CHANGES:");
      console.log("-".repeat(60));

      const existingLines = existingContent.split("\n");
      const newLines = newContent.split("\n");

      let added = 0;
      let removed = 0;

      // Simple diff - just count differences
      const existingSet = new Set(existingLines);
      const newSet = new Set(newLines);

      for (const line of newLines) {
        if (!existingSet.has(line) && line.trim()) {
          added++;
          if (added <= 10) {
            console.log(`+ ${line.slice(0, 70)}${line.length > 70 ? "..." : ""}`);
          }
        }
      }

      for (const line of existingLines) {
        if (!newSet.has(line) && line.trim()) {
          removed++;
          if (removed <= 10) {
            console.log(`- ${line.slice(0, 70)}${line.length > 70 ? "..." : ""}`);
          }
        }
      }

      console.log(`\nTotal: +${added} lines, -${removed} lines`);
    }

    // Ensure output directory exists
    const outputDir = dirname(outputPath);
    if (!existsSync(outputDir)) {
      mkdirSync(outputDir, { recursive: true });
    }

    // Write the file
    writeFileSync(outputPath, newContent);

    // Report stats
    const lines = newContent.split("\n").length;
    const size = (newContent.length / 1024).toFixed(1);

    console.log("\n" + "-".repeat(60));
    console.log("✓ Types generated successfully!");
    console.log(`\nOutput: ${outputPath}`);
    console.log(`Lines: ${lines}`);
    console.log(`Size: ${size} KB`);

    // Parse some stats from the generated types
    const tableMatches = newContent.match(/^\s+\w+: \{$/gm);
    const enumMatches = newContent.match(/export type \w+ =/g);

    if (tableMatches) {
      console.log(`Tables: ~${tableMatches.length}`);
    }
    if (enumMatches) {
      console.log(`Types: ${enumMatches.length}`);
    }
  } catch (error) {
    console.error("\n❌ Type generation failed!");

    if (flags.local) {
      console.error("\nMake sure Supabase local is running:");
      console.error("  supabase start");
    } else {
      console.error("\nMake sure you're linked to a project:");
      console.error("  supabase link --project-ref <ref>");
    }

    console.error("\nError details:", error);
    process.exit(1);
  }
}

generateTypes().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
