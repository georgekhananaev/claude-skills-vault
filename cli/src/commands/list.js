import { fetchManifest } from "../lib/manifest.js";
import { log, colors } from "../lib/logger.js";

function truncate(str, max = 80) {
  if (!str) return "";
  // Strip quotes from frontmatter descriptions
  const clean = str.replace(/^["']|["']$/g, "");
  if (clean.length <= max) return clean;
  return clean.slice(0, max - 1) + "\u2026";
}

export async function list() {
  const manifest = await fetchManifest();

  // Skills
  if (manifest.skills?.length) {
    log.header(`Skills (${manifest.skills.length})`);
    const maxName = Math.max(...manifest.skills.map((s) => s.name.length));
    for (const skill of manifest.skills) {
      const cat = skill.category
        ? `${colors.dim}[${skill.category.padEnd(12)}]${colors.reset} `
        : "";
      console.log(
        `  ${colors.green}${skill.name.padEnd(maxName + 2)}${colors.reset}${cat}${truncate(skill.description)}`
      );
    }
  }

  // Commands
  if (manifest.commands?.length) {
    log.header(`Commands (${manifest.commands.length})`);
    const maxName = Math.max(...manifest.commands.map((c) => c.name.length));
    for (const cmd of manifest.commands) {
      console.log(
        `  ${colors.blue}${cmd.name.padEnd(maxName + 2)}${colors.reset}${truncate(cmd.description)}`
      );
    }
  }

  // MCP Servers
  if (manifest.mcp_servers?.length) {
    log.header(`MCP Servers (${manifest.mcp_servers.length})`);
    const maxName = Math.max(...manifest.mcp_servers.map((m) => m.name.length));
    for (const mcp of manifest.mcp_servers) {
      console.log(
        `  ${colors.magenta}${mcp.name.padEnd(maxName + 2)}${colors.reset}${truncate(mcp.description)}`
      );
    }
  }

  console.log(
    `\n  ${colors.dim}Install with: npx claude-skills-vault install <name>${colors.reset}\n`
  );
}
