#!/usr/bin/env bun
/**
 * Edge Function Deployer
 * Deploys Edge Functions with validation checks.
 *
 * Usage:
 *   bun func_deploy.ts <function-name>
 *   bun func_deploy.ts --all
 *
 * Options:
 *   --all              Deploy all functions
 *   --no-verify        Skip TypeScript verification
 *   --import-map PATH  Custom import map file
 *
 * Example:
 *   bun func_deploy.ts hello-world
 *   bun func_deploy.ts --all
 */

import { existsSync, readdirSync, statSync, readFileSync } from "fs";
import { join } from "path";
import { $ } from "bun";

const args = process.argv.slice(2);

// Get function name or --all
const name = args.filter((a) => !a.startsWith("--"))[0];
const deployAll = args.includes("--all");
const noVerify = args.includes("--no-verify");

// Get import map
let importMap: string | undefined;
const importMapIndex = args.findIndex((a) => a === "--import-map");
if (importMapIndex !== -1 && args[importMapIndex + 1]) {
  importMap = args[importMapIndex + 1];
}

if (!name && !deployAll) {
  console.error("Usage: bun func_deploy.ts <function-name>");
  console.error("       bun func_deploy.ts --all");
  console.error("\nOptions:");
  console.error("  --all              Deploy all functions");
  console.error("  --no-verify        Skip TypeScript verification");
  console.error("  --import-map PATH  Custom import map file");
  process.exit(1);
}

const functionsDir = join(process.cwd(), "supabase", "functions");

interface FunctionInfo {
  name: string;
  path: string;
  size: number;
  hasIndex: boolean;
}

function getFunctions(): FunctionInfo[] {
  if (!existsSync(functionsDir)) {
    return [];
  }

  const functions: FunctionInfo[] = [];
  const entries = readdirSync(functionsDir);

  for (const entry of entries) {
    // Skip _shared and hidden directories
    if (entry.startsWith("_") || entry.startsWith(".")) {
      continue;
    }

    const funcPath = join(functionsDir, entry);
    const stat = statSync(funcPath);

    if (stat.isDirectory()) {
      const indexPath = join(funcPath, "index.ts");
      const hasIndex = existsSync(indexPath);

      let size = 0;
      if (hasIndex) {
        size = statSync(indexPath).size;
      }

      functions.push({
        name: entry,
        path: funcPath,
        size,
        hasIndex,
      });
    }
  }

  return functions;
}

async function verifyFunction(funcInfo: FunctionInfo): Promise<{ ok: boolean; errors: string[] }> {
  const errors: string[] = [];

  if (!funcInfo.hasIndex) {
    errors.push("Missing index.ts");
    return { ok: false, errors };
  }

  // Check file size (Supabase limit is ~20MB but warn above 1MB)
  if (funcInfo.size > 1024 * 1024) {
    errors.push(`Large file: ${(funcInfo.size / 1024 / 1024).toFixed(1)}MB`);
  }

  // Basic TypeScript check
  if (!noVerify) {
    const indexPath = join(funcInfo.path, "index.ts");
    const content = readFileSync(indexPath, "utf-8");

    // Check for common issues
    if (!content.includes("Deno.serve")) {
      errors.push("Missing Deno.serve handler");
    }

    // Check for import issues
    if (content.includes('from "node:')) {
      errors.push("Node.js imports may not work in Deno");
    }
  }

  return { ok: errors.length === 0, errors };
}

async function deployFunction(funcInfo: FunctionInfo): Promise<boolean> {
  console.log(`\nDeploying: ${funcInfo.name}`);

  try {
    const deployArgs = ["functions", "deploy", funcInfo.name];

    if (importMap) {
      deployArgs.push("--import-map", importMap);
    }

    await $`supabase ${deployArgs}`;

    return true;
  } catch (error) {
    console.error(`  ❌ Failed: ${error}`);
    return false;
  }
}

async function main() {
  console.log("=" + "=".repeat(59));
  console.log(" EDGE FUNCTION DEPLOYER");
  console.log("=" + "=".repeat(59));

  // Get all functions
  const allFunctions = getFunctions();

  if (allFunctions.length === 0) {
    console.log("\nNo Edge Functions found in supabase/functions/");
    console.log("Create one with: bun .claude/skills/supabase-cli/scripts/func_new.ts <name>");
    process.exit(1);
  }

  // Filter to specific function if name provided
  let functions = allFunctions;
  if (name) {
    functions = allFunctions.filter((f) => f.name === name);
    if (functions.length === 0) {
      console.error(`\n❌ Function '${name}' not found`);
      console.log("\nAvailable functions:");
      for (const f of allFunctions) {
        console.log(`  - ${f.name}`);
      }
      process.exit(1);
    }
  }

  console.log(`\nFunctions to deploy: ${functions.length}`);
  console.log(`Verification: ${noVerify ? "Skipped" : "Enabled"}`);
  if (importMap) {
    console.log(`Import map: ${importMap}`);
  }

  // Verify all functions first
  console.log("\n" + "-".repeat(60));
  console.log("VERIFICATION:");
  console.log("-".repeat(60));

  const verified: FunctionInfo[] = [];
  const failed: { func: FunctionInfo; errors: string[] }[] = [];

  for (const func of functions) {
    const result = await verifyFunction(func);

    if (result.ok) {
      console.log(`✓ ${func.name}`);
      verified.push(func);
    } else {
      console.log(`❌ ${func.name}`);
      for (const error of result.errors) {
        console.log(`   - ${error}`);
      }
      failed.push({ func, errors: result.errors });
    }
  }

  if (failed.length > 0) {
    console.log(`\n⚠️  ${failed.length} function(s) failed verification`);

    if (verified.length === 0) {
      console.log("No functions to deploy.");
      process.exit(1);
    }

    process.stdout.write("\nDeploy verified functions anyway? [y/N]: ");
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

  // Deploy functions
  console.log("\n" + "-".repeat(60));
  console.log("DEPLOYMENT:");
  console.log("-".repeat(60));

  let successCount = 0;
  let failCount = 0;

  for (const func of verified) {
    const success = await deployFunction(func);
    if (success) {
      successCount++;
    } else {
      failCount++;
    }
  }

  // Summary
  console.log("\n" + "=".repeat(60));
  console.log("SUMMARY:");
  console.log("-".repeat(60));
  console.log(`Deployed: ${successCount}`);
  console.log(`Failed: ${failCount}`);
  console.log(`Skipped: ${failed.length}`);

  if (successCount > 0) {
    console.log("\n✓ Deployment complete!");
    console.log("\nFunction URLs:");
    const projectRef = process.env.SUPABASE_PROJECT_ID || "<project-ref>";
    for (const func of verified) {
      console.log(`  https://${projectRef}.supabase.co/functions/v1/${func.name}`);
    }
  }

  if (failCount > 0) {
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
