#!/usr/bin/env node

import { createRequire } from "node:module";
import { list } from "../src/commands/list.js";
import { install } from "../src/commands/install.js";
import { search } from "../src/commands/search.js";
import { info } from "../src/commands/info.js";
import { log, colors } from "../src/lib/logger.js";

const require = createRequire(import.meta.url);
const { version: VERSION } = require("../package.json");

const HELP = `
${colors.bold}claude-skills-vault${colors.reset} v${VERSION}

Install Claude Code skills, commands, and MCP servers.

${colors.bold}Usage:${colors.reset}
  npx claude-skills-vault <command> [options]

${colors.bold}Commands:${colors.reset}
  list                          List all available skills, commands, and MCP servers
  install <name> [name2] ...    Install skills/commands by name
  search <query>                Search skills by keyword
  info <name>                   Show details about a skill

${colors.bold}Install options:${colors.reset}
  --all                         Install all skills and commands
  --skills                      Install all skills only
  --commands                    Install all commands only
  --force                       Overwrite existing files
  --dry-run                     Show what would be installed

${colors.bold}Examples:${colors.reset}
  npx claude-skills-vault list
  npx claude-skills-vault install brainstorm
  npx claude-skills-vault install brainstorm owasp-security github-cli
  npx claude-skills-vault install --all
  npx claude-skills-vault search react
  npx claude-skills-vault info owasp-security
`;

const command = process.argv[2];

if (!command || command === "--help" || command === "-h") {
  console.log(HELP);
  process.exit(0);
}

if (command === "--version" || command === "-v") {
  console.log(VERSION);
  process.exit(0);
}

const args = process.argv.slice(3);

try {
  switch (command) {
    case "list":
      await list();
      break;
    case "install":
    case "i":
      await install(args);
      break;
    case "search":
    case "s":
      await search(args);
      break;
    case "info":
      await info(args);
      break;
    default:
      log.error(`Unknown command: ${command}`);
      console.log(HELP);
      process.exit(1);
  }
} catch (err) {
  log.error(err.message);
  process.exit(1);
}
