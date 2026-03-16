#!/usr/bin/env node

/**
 * Checks if external skills have upstream updates available.
 * Compares local SKILL.md content hash against the latest from GitHub.
 * Maintains a .skill-hashes.json cache to skip known differences.
 *
 * Usage:
 *   node scripts/check-skill-updates.js          # Check for updates
 *   node scripts/check-skill-updates.js --skip    # Mark all current diffs as known (skip next time)
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const ROOT = path.resolve(__dirname, "..");
const SKILLS_DIR = path.join(ROOT, ".claude", "skills");
const CACHE_FILE = path.join(ROOT, "scripts", ".skill-hashes.json");

// External skills and their source SKILL.md URLs (raw GitHub)
const EXTERNAL_SKILLS = [
  {
    name: "frontend-design",
    url: "https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md",
  },
  {
    name: "webapp-testing",
    url: "https://raw.githubusercontent.com/anthropics/skills/main/skills/webapp-testing/SKILL.md",
  },
  {
    name: "trailofbits-security",
    url: "https://raw.githubusercontent.com/trailofbits/skills/main/plugins/audit-context-building/skills/audit-context-building/SKILL.md",
  },
  {
    name: "web-quality",
    url: "https://raw.githubusercontent.com/addyosmani/web-quality-skills/main/skills/accessibility/SKILL.md",
  },
  {
    name: "stripe-best-practices",
    url: "https://raw.githubusercontent.com/stripe/ai/main/skills/stripe-best-practices/SKILL.md",
  },
  {
    name: "terraform",
    url: "https://raw.githubusercontent.com/hashicorp/agent-skills/main/terraform/code-generation/skills/terraform-style-guide/SKILL.md",
  },
  {
    name: "firecrawl-cli",
    url: "https://raw.githubusercontent.com/firecrawl/cli/main/skills/firecrawl-cli/SKILL.md",
  },
  {
    name: "composition-patterns",
    url: "https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/composition-patterns/SKILL.md",
  },
  {
    name: "better-auth",
    url: "https://raw.githubusercontent.com/better-auth/skills/main/better-auth/best-practices/SKILL.md",
  },
  {
    name: "planning-with-files",
    url: "https://raw.githubusercontent.com/OthmanAdi/planning-with-files/master/skills/planning-with-files/SKILL.md",
  },
  {
    name: "obsidian-skills",
    url: "https://raw.githubusercontent.com/kepano/obsidian-skills/main/skills/obsidian-cli/SKILL.md",
  },
  {
    name: "claude-seo",
    url: "https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/skills/seo-audit/SKILL.md",
  },
  {
    name: "notebooklm-skill",
    url: "https://raw.githubusercontent.com/PleasePrompto/notebooklm-skill/master/SKILL.md",
  },
];

function hash(content) {
  return crypto.createHash("sha256").update(content).digest("hex").slice(0, 12);
}

function readLocal(skillName) {
  const skillFile = path.join(SKILLS_DIR, skillName, "SKILL.md");
  try {
    return fs.readFileSync(skillFile, "utf-8");
  } catch {
    return null;
  }
}

function loadCache() {
  try {
    return JSON.parse(fs.readFileSync(CACHE_FILE, "utf-8"));
  } catch {
    return {};
  }
}

function saveCache(cache) {
  fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2) + "\n");
}

async function fetchRemote(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return await res.text();
  } catch {
    return null;
  }
}

async function main() {
  const skipMode = process.argv.includes("--skip");
  const cache = loadCache();

  console.log("\n  Checking external skills for updates...\n");

  let updatesAvailable = 0;
  let errors = 0;
  let upToDate = 0;
  let skipped = 0;

  for (const skill of EXTERNAL_SKILLS) {
    const local = readLocal(skill.name);
    if (!local) {
      console.log(`  \u26A0  ${skill.name} — not installed locally`);
      errors++;
      continue;
    }

    const remote = await fetchRemote(skill.url);
    if (!remote) {
      console.log(`  \u26A0  ${skill.name} — could not fetch upstream`);
      errors++;
      continue;
    }

    const localHash = hash(local);
    const remoteHash = hash(remote);

    if (localHash === remoteHash) {
      console.log(`  \u2713  ${skill.name} — up to date`);
      upToDate++;
      // Clear cache entry if now matching
      if (cache[skill.name]) delete cache[skill.name];
      continue;
    }

    // Check if this diff is already known (cached)
    const cached = cache[skill.name];
    if (cached && cached.localHash === localHash && cached.remoteHash === remoteHash) {
      console.log(`  \u2500  ${skill.name} — known difference (${cached.reason || "adapted locally"})`);
      skipped++;
      continue;
    }

    if (skipMode) {
      // In --skip mode, cache the current diff with a reason
      cache[skill.name] = {
        localHash,
        remoteHash,
        reason: "adapted locally — structure differs from upstream",
        skippedAt: new Date().toISOString().slice(0, 10),
      };
      console.log(`  \u2500  ${skill.name} — marked as known (local: ${localHash}, remote: ${remoteHash})`);
      skipped++;
    } else {
      console.log(`  \u2191  ${skill.name} — UPDATE AVAILABLE (local: ${localHash}, remote: ${remoteHash})`);
      updatesAvailable++;
    }
  }

  saveCache(cache);

  console.log(
    `\n  Summary: ${upToDate} up to date, ${updatesAvailable} updates, ${skipped} known diffs, ${errors} errors\n`
  );

  if (updatesAvailable > 0) {
    console.log(
      "  To update a skill, re-fetch from the source repo."
    );
    console.log(
      "  To skip these diffs: node scripts/check-skill-updates.js --skip\n"
    );
  }

  process.exit(updatesAvailable > 0 ? 1 : 0);
}

main();
