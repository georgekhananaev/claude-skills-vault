import { fetchManifest, findItem } from "../lib/manifest.js";
import { downloadPath } from "../lib/downloader.js";
import { log, colors } from "../lib/logger.js";

export async function install(args) {
  const flags = {
    all: args.includes("--all"),
    skills: args.includes("--skills"),
    commands: args.includes("--commands"),
    force: args.includes("--force"),
    dryRun: args.includes("--dry-run"),
  };

  const names = args.filter((a) => !a.startsWith("--"));

  if (!flags.all && !flags.skills && !flags.commands && names.length === 0) {
    log.error("Specify skill names or use --all, --skills, --commands");
    console.log(
      `\n  ${colors.dim}Examples:${colors.reset}` +
        `\n    npx claude-skills-vault install brainstorm` +
        `\n    npx claude-skills-vault install --all\n`
    );
    process.exit(1);
  }

  const manifest = await fetchManifest();
  const opts = { force: flags.force, dryRun: flags.dryRun };
  let installed = 0;
  let failed = 0;

  // Install all skills
  if (flags.all || flags.skills) {
    for (const skill of manifest.skills) {
      const ok = await downloadPath(skill.path, skill.path, opts);
      if (ok) installed++;
      else failed++;
    }
  }

  // Install all commands (downloads entire commands directory)
  if (flags.all || flags.commands) {
    const ok = await downloadPath(".claude/commands", ".claude/commands", opts);
    if (ok) installed += manifest.commands.length;
    else failed += manifest.commands.length;
  }

  // Install by name
  for (const name of names) {
    const item = findItem(manifest, name);
    if (!item) {
      log.error(`Not found: "${name}"`);
      failed++;
      continue;
    }

    if (item.type === "skill") {
      const ok = await downloadPath(item.path, item.path, opts);
      if (ok) installed++;
      else failed++;
    } else if (item.type === "command") {
      // Commands are single .md files — download entire commands dir
      const ok = await downloadPath(
        ".claude/commands",
        ".claude/commands",
        opts
      );
      if (ok) installed++;
      else failed++;
    } else if (item.type === "mcp_server") {
      log.warn(
        `MCP server "${name}" — copy the config from: ${item.path}/README.md`
      );
      log.info(
        `MCP installation via \`claude mcp add\` coming in a future version.`
      );
    }
  }

  // Summary
  console.log();
  if (flags.dryRun) {
    log.info(`Dry run complete. ${installed} items would be installed.`);
  } else if (installed > 0) {
    log.success(
      `Done! Installed ${installed} item${installed > 1 ? "s" : ""}.${failed > 0 ? ` ${failed} failed.` : ""}`
    );
  } else {
    log.warn("Nothing was installed.");
  }
}
