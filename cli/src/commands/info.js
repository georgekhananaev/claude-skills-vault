import { fetchManifest, findItem } from "../lib/manifest.js";
import { log, colors } from "../lib/logger.js";

export async function info(args) {
  const name = args.filter((a) => !a.startsWith("--"))[0];

  if (!name) {
    log.error("Provide a name. Example: npx claude-skills-vault info brainstorm");
    process.exit(1);
  }

  const manifest = await fetchManifest();
  const item = findItem(manifest, name);

  if (!item) {
    log.error(`Not found: "${name}"`);
    process.exit(1);
  }

  console.log();
  console.log(`  ${colors.bold}${item.name}${colors.reset}`);
  console.log(`  ${colors.dim}${"─".repeat(40)}${colors.reset}`);
  console.log(`  ${colors.cyan}Type:${colors.reset}        ${item.type}`);
  console.log(`  ${colors.cyan}Description:${colors.reset} ${item.description}`);
  if (item.category) {
    console.log(`  ${colors.cyan}Category:${colors.reset}    ${item.category}`);
  }
  if (item.author) {
    console.log(`  ${colors.cyan}Author:${colors.reset}      ${item.author}`);
  }
  if (item.files) {
    console.log(`  ${colors.cyan}Files:${colors.reset}       ${item.files}`);
  }
  console.log(`  ${colors.cyan}Path:${colors.reset}        ${item.path}`);
  console.log(
    `\n  ${colors.dim}Install: npx claude-skills-vault install ${item.name}${colors.reset}\n`
  );
}
