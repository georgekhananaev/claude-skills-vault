import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { log, spinner } from "./logger.js";

const require = createRequire(import.meta.url);
const pkg = require("../../package.json");
const TAG = `v${pkg.version}`;

const MANIFEST_URL = `https://raw.githubusercontent.com/georgekhananaev/claude-skills-vault/${TAG}/manifest.json`;

let cached = null;

function findBundledManifest() {
  // Check for manifest.json bundled in the npm package (cli/manifest.json)
  const pkgRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
  const bundled = join(pkgRoot, "manifest.json");
  if (existsSync(bundled)) return bundled;

  // Dev fallback: repo root manifest.json (3 dirs up from cli/src/lib/)
  const repoRoot = join(pkgRoot, "..");
  const local = join(repoRoot, "manifest.json");
  if (existsSync(local)) return local;

  return null;
}

export async function fetchManifest() {
  if (cached) return cached;

  const sp = spinner("Fetching manifest...");

  // Try remote first (version-pinned)
  try {
    const res = await fetch(MANIFEST_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    cached = await res.json();
    const total =
      (cached.skills?.length || 0) +
      (cached.commands?.length || 0) +
      (cached.mcp_servers?.length || 0);
    sp.stop(`Fetched manifest (${total} items, v${cached.version})`);
    return cached;
  } catch {
    // Fallback to bundled/local manifest
    const localPath = findBundledManifest();
    if (localPath) {
      const data = await readFile(localPath, "utf-8");
      cached = JSON.parse(data);
      const total =
        (cached.skills?.length || 0) +
        (cached.commands?.length || 0) +
        (cached.mcp_servers?.length || 0);
      sp.stop(`Loaded local manifest (${total} items, v${cached.version})`);
      return cached;
    }
    sp.fail("Failed to fetch manifest");
    throw new Error(
      "Could not fetch manifest from GitHub. Check your internet connection."
    );
  }
}

export function findItem(manifest, name) {
  const lower = name.toLowerCase();
  for (const skill of manifest.skills || []) {
    if (skill.name.toLowerCase() === lower) return { ...skill, type: "skill" };
  }
  for (const cmd of manifest.commands || []) {
    if (cmd.name.toLowerCase() === lower) return { ...cmd, type: "command" };
  }
  for (const mcp of manifest.mcp_servers || []) {
    if (mcp.name.toLowerCase() === lower) return { ...mcp, type: "mcp_server" };
  }
  return null;
}
