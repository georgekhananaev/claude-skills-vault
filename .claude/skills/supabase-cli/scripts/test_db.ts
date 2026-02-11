#!/usr/bin/env bun
/**
 * Database Test Runner
 * Runs database tests using pgTAP or custom verification queries.
 *
 * Usage:
 *   bun test_db.ts [--local | --remote] [--file path]
 *
 * Options:
 *   --local     Run against local database (default)
 *   --remote    Run against remote database (read-only tests only)
 *   --file PATH Run specific test file
 *
 * Test file location: supabase/tests/*.sql or supabase/tests/*.ts
 *
 * Example:
 *   bun test_db.ts
 *   bun test_db.ts --file supabase/tests/rls_policies.sql
 */

import { existsSync, readdirSync, readFileSync } from "fs";
import { join } from "path";
import { $ } from "bun";

const args = process.argv.slice(2);

const flags = {
  local: args.includes("--local"),
  remote: args.includes("--remote"),
};

// Get specific file
let testFile: string | undefined;
const fileIndex = args.findIndex((a) => a === "--file");
if (fileIndex !== -1 && args[fileIndex + 1]) {
  testFile = args[fileIndex + 1];
}

if (!flags.local && !flags.remote) {
  flags.local = true;
}

if (flags.local && flags.remote) {
  console.error("Error: Cannot specify both --local and --remote");
  process.exit(1);
}

const testsDir = join(process.cwd(), "supabase", "tests");

interface TestResult {
  name: string;
  passed: boolean;
  message: string;
  duration: number;
}

async function runSQLTest(filepath: string, target: "local" | "remote"): Promise<TestResult[]> {
  const results: TestResult[] = [];
  const content = readFileSync(filepath, "utf-8");
  const filename = filepath.split("/").pop() || filepath;

  const start = Date.now();

  try {
    // Create temp file for execution
    const tempFile = `/tmp/supabase_test_${Date.now()}.sql`;
    await Bun.write(tempFile, content);

    let result;
    if (target === "remote") {
      result = await $`supabase db execute --linked < ${tempFile}`.quiet();
    } else {
      result = await $`supabase db execute < ${tempFile}`.quiet();
    }

    await $`rm -f ${tempFile}`.quiet();

    const output = result.stdout.toString();
    const duration = Date.now() - start;

    // Parse pgTAP output if present
    if (output.includes("ok ") || output.includes("not ok ")) {
      const lines = output.split("\n");
      for (const line of lines) {
        if (line.startsWith("ok ")) {
          const testName = line.replace(/^ok \d+ - /, "").trim();
          results.push({
            name: testName || filename,
            passed: true,
            message: "Passed",
            duration,
          });
        } else if (line.startsWith("not ok ")) {
          const testName = line.replace(/^not ok \d+ - /, "").trim();
          results.push({
            name: testName || filename,
            passed: false,
            message: "Failed",
            duration,
          });
        }
      }
    }

    // If no pgTAP format, treat whole file as one test
    if (results.length === 0) {
      results.push({
        name: filename,
        passed: true,
        message: output.slice(0, 100) || "Executed successfully",
        duration,
      });
    }
  } catch (error) {
    results.push({
      name: filename,
      passed: false,
      message: String(error).slice(0, 200),
      duration: Date.now() - start,
    });
  }

  return results;
}

async function runTSTest(filepath: string): Promise<TestResult[]> {
  const filename = filepath.split("/").pop() || filepath;
  const start = Date.now();

  try {
    await $`bun ${filepath}`;
    return [
      {
        name: filename,
        passed: true,
        message: "Executed successfully",
        duration: Date.now() - start,
      },
    ];
  } catch (error) {
    return [
      {
        name: filename,
        passed: false,
        message: String(error).slice(0, 200),
        duration: Date.now() - start,
      },
    ];
  }
}

async function main() {
  const target = flags.remote ? "remote" : "local";

  console.log("=" + "=".repeat(59));
  console.log(` DATABASE TESTS [${target.toUpperCase()}]`);
  console.log("=" + "=".repeat(59));

  // Safety check for remote
  if (flags.remote) {
    console.log("\n⚠️  Running tests against REMOTE database.");
    console.log("Ensure tests are READ-ONLY to avoid data corruption.");
  }

  // Find test files
  let testFiles: string[] = [];

  if (testFile) {
    if (!existsSync(testFile)) {
      console.error(`Error: Test file not found: ${testFile}`);
      process.exit(1);
    }
    testFiles = [testFile];
  } else if (existsSync(testsDir)) {
    const files = readdirSync(testsDir);
    testFiles = files
      .filter((f) => f.endsWith(".sql") || f.endsWith(".ts"))
      .map((f) => join(testsDir, f));
  }

  if (testFiles.length === 0) {
    console.log("\nNo test files found.");
    console.log(`\nCreate tests in: ${testsDir}/`);
    console.log("\nExample pgTAP test (supabase/tests/rls_policies.sql):");
    console.log("  BEGIN;");
    console.log("  SELECT plan(2);");
    console.log("  SELECT has_table('public', 'users', 'users table exists');");
    console.log("  SELECT policies_are('public', 'users', ARRAY['users_select_policy']);");
    console.log("  SELECT * FROM finish();");
    console.log("  ROLLBACK;");
    process.exit(0);
  }

  console.log(`\nFound ${testFiles.length} test file(s)`);

  // Run tests
  console.log("\n" + "-".repeat(60));
  console.log("RUNNING TESTS:");
  console.log("-".repeat(60));

  const allResults: TestResult[] = [];

  for (const file of testFiles) {
    const relPath = file.replace(process.cwd() + "/", "");
    console.log(`\n📁 ${relPath}`);

    let results: TestResult[];
    if (file.endsWith(".sql")) {
      results = await runSQLTest(file, target);
    } else {
      results = await runTSTest(file);
    }

    for (const result of results) {
      const icon = result.passed ? "✓" : "✗";
      const color = result.passed ? "" : "";
      console.log(`   ${icon} ${result.name} (${result.duration}ms)`);
      if (!result.passed) {
        console.log(`     ${result.message}`);
      }
    }

    allResults.push(...results);
  }

  // Summary
  const passed = allResults.filter((r) => r.passed).length;
  const failed = allResults.filter((r) => !r.passed).length;
  const totalDuration = allResults.reduce((sum, r) => sum + r.duration, 0);

  console.log("\n" + "=".repeat(60));
  console.log("SUMMARY:");
  console.log("-".repeat(60));
  console.log(`  Passed: ${passed}`);
  console.log(`  Failed: ${failed}`);
  console.log(`  Total:  ${allResults.length}`);
  console.log(`  Time:   ${totalDuration}ms`);

  if (failed > 0) {
    console.log("\n❌ TESTS FAILED");
    process.exit(1);
  } else {
    console.log("\n✓ ALL TESTS PASSED");
  }
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
