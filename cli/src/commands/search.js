import { fetchManifest } from "../lib/manifest.js";
import { log, colors } from "../lib/logger.js";

export async function search(args) {
  const query = args.filter((a) => !a.startsWith("--")).join(" ").toLowerCase();

  if (!query) {
    log.error('Provide a search query. Example: npx claude-skills-vault search "react"');
    process.exit(1);
  }

  const manifest = await fetchManifest();

  const results = [];

  for (const skill of manifest.skills || []) {
    const haystack = `${skill.name} ${skill.description} ${skill.category || ""}`.toLowerCase();
    if (haystack.includes(query)) {
      results.push({ ...skill, type: "skill" });
    }
  }

  for (const cmd of manifest.commands || []) {
    const haystack = `${cmd.name} ${cmd.description}`.toLowerCase();
    if (haystack.includes(query)) {
      results.push({ ...cmd, type: "command" });
    }
  }

  for (const mcp of manifest.mcp_servers || []) {
    const haystack = `${mcp.name} ${mcp.description}`.toLowerCase();
    if (haystack.includes(query)) {
      results.push({ ...mcp, type: "mcp_server" });
    }
  }

  if (results.length === 0) {
    log.warn(`No results for "${query}"`);
    return;
  }

  log.header(`Search results for "${query}" (${results.length})`);

  const typeColor = { skill: colors.green, command: colors.blue, mcp_server: colors.magenta };
  const maxName = Math.max(...results.map((r) => r.name.length));

  for (const r of results) {
    const c = typeColor[r.type] || "";
    const tag = `${colors.dim}[${r.type}]${colors.reset}`;
    console.log(`  ${c}${r.name.padEnd(maxName + 2)}${colors.reset}${tag} ${r.description}`);
  }

  console.log(
    `\n  ${colors.dim}Install with: npx claude-skills-vault install <name>${colors.reset}\n`
  );
}
