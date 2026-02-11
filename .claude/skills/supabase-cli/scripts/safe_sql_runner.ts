#!/usr/bin/env bun
/**
 * Safe SQL Runner
 * Executes SQL with safety checks and transaction wrapping.
 *
 * Usage:
 *   bun safe_sql_runner.ts --query "SELECT * FROM users" [--local | --remote]
 *   bun safe_sql_runner.ts --file query.sql [--local | --remote] [--confirm]
 *
 * Options:
 *   --query SQL      SQL query to execute
 *   --file PATH      Path to SQL file to execute
 *   --local          Execute on local database (default)
 *   --remote         Execute on remote database
 *   --confirm        Required for dangerous operations on remote
 *   --no-transaction Skip transaction wrapping
 *   --dry-run        Show classification without executing
 *   --json           Output results as JSON
 */

import { readFileSync, existsSync } from "fs";
import { $ } from "bun";

const args = process.argv.slice(2);

// Production detection
function isProductionEnvironment(): { isProduction: boolean; indicator: string } {
  const supabaseUrl = process.env.SUPABASE_URL || "";

  // Check for common production indicators
  const prodIndicators = [
    { pattern: /prod/i, name: "URL contains 'prod'" },
    { pattern: /production/i, name: "URL contains 'production'" },
    { pattern: /live/i, name: "URL contains 'live'" },
  ];

  for (const { pattern, name } of prodIndicators) {
    if (pattern.test(supabaseUrl)) {
      return { isProduction: true, indicator: name };
    }
  }

  // Check NODE_ENV
  if (process.env.NODE_ENV === "production") {
    return { isProduction: true, indicator: "NODE_ENV=production" };
  }

  return { isProduction: false, indicator: "" };
}

// Parse arguments
function getArg(flag: string): string | undefined {
  const index = args.findIndex((a) => a === flag);
  if (index !== -1 && args[index + 1] && !args[index + 1].startsWith("--")) {
    return args[index + 1];
  }
  return undefined;
}

const flags = {
  query: getArg("--query"),
  file: getArg("--file"),
  local: args.includes("--local"),
  remote: args.includes("--remote"),
  confirm: args.includes("--confirm"),
  noTransaction: args.includes("--no-transaction"),
  dryRun: args.includes("--dry-run"),
  json: args.includes("--json"),
};

// Validation
if (!flags.query && !flags.file) {
  console.error("Usage: bun safe_sql_runner.ts --query 'SQL' [options]");
  console.error("       bun safe_sql_runner.ts --file path.sql [options]");
  console.error("\nOptions:");
  console.error("  --local          Execute on local database (default)");
  console.error("  --remote         Execute on remote database");
  console.error("  --confirm        Required for dangerous operations on remote");
  console.error("  --no-transaction Skip transaction wrapping");
  console.error("  --dry-run        Show classification without executing");
  console.error("  --json           Output results as JSON");
  process.exit(1);
}

if (!flags.local && !flags.remote) {
  flags.local = true;
}

if (flags.local && flags.remote) {
  console.error("Error: Cannot specify both --local and --remote");
  process.exit(1);
}

type SafetyLevel = "safe" | "write" | "dangerous";

interface Classification {
  level: SafetyLevel;
  reasons: string[];
  statements: string[];
}

function classifySQL(sql: string): Classification {
  const reasons: string[] = [];
  let level: SafetyLevel = "safe";

  const normalizedSQL = sql.toUpperCase();

  // Dangerous patterns
  const dangerousPatterns = [
    { pattern: /\bDROP\s+TABLE\b/, reason: "DROP TABLE" },
    { pattern: /\bDROP\s+DATABASE\b/, reason: "DROP DATABASE" },
    { pattern: /\bDROP\s+SCHEMA\b/, reason: "DROP SCHEMA" },
    { pattern: /\bTRUNCATE\b/, reason: "TRUNCATE" },
    { pattern: /\bDELETE\s+FROM\s+\w+\s*;/, reason: "DELETE without WHERE" },
    { pattern: /\bDELETE\s+FROM\s+\w+\s*$/, reason: "DELETE without WHERE" },
    { pattern: /\bALTER\s+TABLE\s+\w+\s+DROP\s+COLUMN\b/, reason: "DROP COLUMN" },
  ];

  // Write patterns
  const writePatterns = [
    { pattern: /\bINSERT\b/, reason: "INSERT" },
    { pattern: /\bUPDATE\b/, reason: "UPDATE" },
    { pattern: /\bDELETE\b/, reason: "DELETE" },
    { pattern: /\bCREATE\b/, reason: "CREATE" },
    { pattern: /\bALTER\b/, reason: "ALTER" },
    { pattern: /\bGRANT\b/, reason: "GRANT" },
    { pattern: /\bREVOKE\b/, reason: "REVOKE" },
  ];

  // Check dangerous first
  for (const { pattern, reason } of dangerousPatterns) {
    if (pattern.test(normalizedSQL)) {
      level = "dangerous";
      reasons.push(reason);
    }
  }

  // Check write if not already dangerous
  if (level !== "dangerous") {
    for (const { pattern, reason } of writePatterns) {
      if (pattern.test(normalizedSQL)) {
        level = "write";
        reasons.push(reason);
      }
    }
  }

  // Extract statement types
  const statementTypes = new Set<string>();
  const stmtPatterns = [
    /\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|EXPLAIN|SHOW)\b/gi,
  ];

  for (const pattern of stmtPatterns) {
    const matches = sql.match(pattern);
    if (matches) {
      for (const match of matches) {
        statementTypes.add(match.toUpperCase());
      }
    }
  }

  return {
    level,
    reasons,
    statements: Array.from(statementTypes),
  };
}

async function runSQL(sql: string, target: "local" | "remote"): Promise<string> {
  // Create a temp file for the SQL
  const tempFile = `/tmp/supabase_query_${Date.now()}.sql`;
  await Bun.write(tempFile, sql);

  try {
    let result;
    if (target === "remote") {
      result = await $`supabase db execute --linked < ${tempFile}`.quiet();
    } else {
      result = await $`supabase db execute < ${tempFile}`.quiet();
    }
    return result.stdout.toString();
  } finally {
    // Clean up temp file
    await $`rm -f ${tempFile}`.quiet();
  }
}

async function main() {
  const target = flags.remote ? "remote" : "local";

  // Get SQL content
  let sql: string;
  if (flags.file) {
    if (!existsSync(flags.file)) {
      console.error(`Error: File not found: ${flags.file}`);
      process.exit(1);
    }
    sql = readFileSync(flags.file, "utf-8");
  } else {
    sql = flags.query!;
  }

  // Classify the SQL
  const classification = classifySQL(sql);

  if (!flags.json) {
    console.log("=" + "=".repeat(59));
    console.log(` SAFE SQL RUNNER [${target.toUpperCase()}]`);
    console.log("=" + "=".repeat(59));

    console.log("\nSQL:");
    console.log("-".repeat(60));
    // Show first 500 chars of SQL
    const preview = sql.length > 500 ? sql.slice(0, 500) + "..." : sql;
    console.log(preview);
    console.log("-".repeat(60));

    console.log("\nClassification:");
    const levelIcon =
      classification.level === "safe"
        ? "🟢"
        : classification.level === "write"
          ? "🟡"
          : "🔴";
    console.log(`  Level: ${levelIcon} ${classification.level.toUpperCase()}`);
    console.log(`  Statements: ${classification.statements.join(", ")}`);
    if (classification.reasons.length > 0) {
      console.log(`  Reasons: ${classification.reasons.join(", ")}`);
    }
  }

  // Safety checks for dangerous operations
  if (classification.level === "dangerous" && flags.remote && !flags.confirm) {
    if (flags.json) {
      console.log(
        JSON.stringify({
          error: "Dangerous operations on remote require --confirm flag",
          classification,
        })
      );
    } else {
      console.log("\n❌ BLOCKED: Dangerous operations on remote require --confirm flag");
      console.log("\nIf you're sure, run with --confirm");
    }
    process.exit(1);
  }

  // Dry run - just show classification
  if (flags.dryRun) {
    if (flags.json) {
      console.log(JSON.stringify({ dryRun: true, classification }));
    } else {
      console.log("\nDRY RUN - No execution performed");
    }
    return;
  }

  // Wrap in transaction if needed
  let finalSQL = sql;
  if (
    classification.level !== "safe" &&
    !flags.noTransaction &&
    !sql.includes("BEGIN") &&
    !sql.includes("CONCURRENTLY")
  ) {
    finalSQL = `BEGIN;\n${sql}\nCOMMIT;`;
    if (!flags.json) {
      console.log("\n📦 Wrapping in transaction");
    }
  }

  // Confirm dangerous operations
  if (classification.level === "dangerous" && !flags.json) {
    console.log("\n⚠️  WARNING: This is a dangerous operation!");
    process.stdout.write("Proceed? [y/N]: ");

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

  // Execute
  if (!flags.json) {
    console.log("\nExecuting...");
  }

  try {
    const result = await runSQL(finalSQL, target);

    if (flags.json) {
      // Try to parse as JSON if it looks like JSON
      try {
        const parsed = JSON.parse(result);
        console.log(JSON.stringify({ success: true, result: parsed, classification }));
      } catch {
        console.log(JSON.stringify({ success: true, result, classification }));
      }
    } else {
      console.log("\n" + "-".repeat(60));
      console.log("RESULT:");
      console.log("-".repeat(60));
      console.log(result || "(no output)");
      console.log("\n✓ Query executed successfully");
    }
  } catch (error) {
    if (flags.json) {
      console.log(
        JSON.stringify({ success: false, error: String(error), classification })
      );
    } else {
      console.error("\n❌ Query failed!");
      console.error(error);
    }
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
