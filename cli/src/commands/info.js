import { fetchManifest, findItem } from "../lib/manifest.js";
import { log, colors } from "../lib/logger.js";

const TYPE_LABELS = {
  skill: `${colors.green}skill${colors.reset}`,
  command: `${colors.blue}command${colors.reset}`,
  mcp_server: `${colors.magenta}mcp server${colors.reset}`,
};

const CATEGORY_LABELS = {
  frontend: "Frontend & UI",
  backend: "Backend & APIs",
  security: "Security & Code Quality",
  testing: "Testing & QA",
  mobile: "Mobile Development",
  devops: "DevOps & CLI Tools",
  ai: "AI & Agent Orchestration",
  productivity: "Productivity & Workflow",
};

export async function info(args) {
  const name = args.filter((a) => !a.startsWith("--"))[0];

  if (!name) {
    log.error(
      "Provide a name. Example: npx claude-skills-vault info brainstorm"
    );
    process.exit(1);
  }

  const manifest = await fetchManifest();
  const item = findItem(manifest, name);

  if (!item) {
    log.error(`Not found: "${name}"`);
    process.exit(1);
  }

  const label = TYPE_LABELS[item.type] || item.type;
  const catLabel = CATEGORY_LABELS[item.category] || item.category;

  console.log();
  console.log(`  ${colors.bold}${item.name}${colors.reset}  ${colors.dim}(${label})${colors.reset}`);
  console.log(`  ${colors.dim}${"─".repeat(50)}${colors.reset}`);

  // Description — word-wrap at ~80 chars
  if (item.description) {
    const desc = item.description.replace(/^["']|["']$/g, "");
    const words = desc.split(" ");
    let line = "";
    const lines = [];
    for (const word of words) {
      if ((line + " " + word).length > 76) {
        lines.push(line);
        line = word;
      } else {
        line = line ? line + " " + word : word;
      }
    }
    if (line) lines.push(line);
    for (const l of lines) {
      console.log(`  ${l}`);
    }
    console.log();
  }

  // Details table
  if (item.category) {
    console.log(`  ${colors.cyan}Category:${colors.reset}    ${catLabel}`);
  }
  if (item.author) {
    console.log(`  ${colors.cyan}Author:${colors.reset}      ${item.author}`);
  }
  if (item.source) {
    console.log(`  ${colors.cyan}Source:${colors.reset}      ${item.source}`);
  }
  if (item.risk) {
    const riskColor = item.risk === "safe" ? colors.green : colors.yellow;
    console.log(`  ${colors.cyan}Risk:${colors.reset}        ${riskColor}${item.risk}${colors.reset}`);
  }
  if (item.files) {
    console.log(`  ${colors.cyan}Files:${colors.reset}       ${item.files}`);
  }
  if (item.invocable !== undefined) {
    console.log(`  ${colors.cyan}Invocable:${colors.reset}   ${item.invocable ? "yes (slash command)" : "no (auto-loaded)"}`);
  }
  console.log(`  ${colors.cyan}Path:${colors.reset}        ${item.path}`);

  // Install instructions
  console.log();
  if (item.type === "skill") {
    console.log(`  ${colors.bold}Install:${colors.reset}`);
    console.log(`  ${colors.green}npx claude-skills-vault install ${item.name}${colors.reset}`);
  } else if (item.type === "command") {
    console.log(`  ${colors.bold}Install:${colors.reset}`);
    console.log(`  ${colors.blue}npx claude-skills-vault install --commands${colors.reset}`);
    console.log(`  ${colors.dim}Invoke with: /${item.name}${colors.reset}`);
  } else if (item.type === "mcp_server") {
    console.log(`  ${colors.bold}Setup:${colors.reset}`);
    console.log(`  ${colors.dim}See ${item.path}/README.md for configuration${colors.reset}`);
  }
  console.log();
}
