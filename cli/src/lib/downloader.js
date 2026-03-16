import { downloadTemplate } from "giget";
import { existsSync } from "node:fs";
import { resolve, relative } from "node:path";
import { createRequire } from "node:module";
import { spinner, log } from "./logger.js";

const require = createRequire(import.meta.url);
const pkg = require("../../package.json");
const TAG = `v${pkg.version}`;

const REPO = "github:georgekhananaev/claude-skills-vault";

// Allowlisted path prefixes for safety
const ALLOWED_PREFIXES = [".claude/skills/", ".claude/commands"];

/**
 * Validate that destPath is safe (no traversal, stays under cwd, allowlisted prefix).
 */
function validatePath(destPath) {
  if (/^[/\\]/.test(destPath)) {
    throw new Error(`Absolute paths are not allowed: ${destPath}`);
  }
  if (/\.\./.test(destPath)) {
    throw new Error(`Path traversal is not allowed: ${destPath}`);
  }
  const abs = resolve(process.cwd(), destPath);
  const rel = relative(process.cwd(), abs);
  if (rel.startsWith("..")) {
    throw new Error(`Path escapes project directory: ${destPath}`);
  }
  if (!ALLOWED_PREFIXES.some((prefix) => destPath.startsWith(prefix))) {
    throw new Error(`Path not in allowed prefix (.claude/): ${destPath}`);
  }
}

/**
 * Download a specific path from the repo into the target directory.
 * @param {string} repoPath - Path within repo (e.g., ".claude/skills/brainstorm")
 * @param {string} destPath - Local destination path
 * @param {object} opts - { force: boolean, dryRun: boolean }
 */
export async function downloadPath(repoPath, destPath, opts = {}) {
  validatePath(destPath);
  const absPath = resolve(process.cwd(), destPath);

  if (existsSync(absPath) && !opts.force) {
    log.warn(`Already exists: ${destPath} (use --force to overwrite)`);
    return false;
  }

  if (opts.dryRun) {
    log.info(`Would install: ${repoPath} → ${destPath}`);
    return true;
  }

  const sp = spinner(`Downloading ${repoPath.split("/").pop()}...`);
  try {
    // Try version-pinned tag first, fall back to main
    try {
      await downloadTemplate(`${REPO}/${repoPath}#${TAG}`, {
        dir: absPath,
        force: opts.force,
      });
    } catch {
      await downloadTemplate(`${REPO}/${repoPath}#main`, {
        dir: absPath,
        force: opts.force,
      });
    }
    sp.stop(`Installed ${destPath}`);
    return true;
  } catch (err) {
    sp.fail(`Failed to download ${repoPath}: ${err.message}`);
    return false;
  }
}
