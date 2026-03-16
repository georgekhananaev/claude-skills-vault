#!/usr/bin/env node

/**
 * Auto-generates SKILLS.md, COMMANDS.md, MCP-SERVERS.md, and cli/README.md
 * from the actual repo contents. Run as part of /git-npm-release.
 *
 * Usage: node scripts/generate-docs.js
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SKILLS_DIR = path.join(ROOT, ".claude", "skills");
const COMMANDS_DIR = path.join(ROOT, ".claude", "commands");
const MCP_DIR = path.join(ROOT, "mcp-servers");

// ── Helpers ──────────────────────────────────────────────────────────

function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const fm = {};
  const lines = match[1].split("\n");
  let currentKey = null;
  for (const line of lines) {
    if (currentKey && /^\s+\S/.test(line)) {
      const cont = line.trim();
      if (fm[currentKey] && fm[currentKey] !== ">" && fm[currentKey] !== "|") {
        fm[currentKey] += " " + cont;
      } else {
        fm[currentKey] = cont;
      }
      continue;
    }
    const idx = line.indexOf(":");
    if (idx === -1) { currentKey = null; continue; }
    const key = line.slice(0, idx).trim();
    const val = line.slice(idx + 1).trim();
    if (!key) { currentKey = null; continue; }
    currentKey = key;
    fm[key] = val;
  }
  for (const key of Object.keys(fm)) {
    if (fm[key] === ">" || fm[key] === "|") fm[key] = "";
    if (typeof fm[key] === "string") fm[key] = fm[key].replace(/^["']|["']$/g, "");
  }
  return fm;
}

function firstSentence(text) {
  if (!text) return "";
  const clean = text.replace(/[*_`#\[\]]/g, "").trim();
  const m = clean.match(/^(.+?[.!?])(?:\s|$)/);
  return m ? m[1].trim() : clean.split("\n")[0].trim();
}

function truncate(str, max = 70) {
  if (!str) return "";
  if (str.length <= max) return str;
  return str.slice(0, max - 1) + "\u2026";
}

// ── SKILLS.md ────────────────────────────────────────────────────────

function generateSkillsMd() {
  const dirs = fs.readdirSync(SKILLS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .sort((a, b) => a.name.localeCompare(b.name));

  const core = [];
  const docSkills = [];

  for (const d of dirs) {
    const skillFile = path.join(SKILLS_DIR, d.name, "SKILL.md");
    if (!fs.existsSync(skillFile)) continue;

    const content = fs.readFileSync(skillFile, "utf-8");
    const fm = parseFrontmatter(content);
    let desc = fm.description || "";
    if (!desc) {
      const body = content.replace(/^---[\s\S]*?---\s*/, "");
      for (const line of body.split("\n")) {
        const t = line.trim();
        if (!t || t.startsWith("#") || t.startsWith("**IMPORTANT")) continue;
        desc = firstSentence(t.replace(/^Goal:\s*/, ""));
        break;
      }
    }

    const entry = {
      name: fm.name || d.name,
      dir: d.name,
      desc: truncate(desc),
    };

    if (d.name === "document-skills") {
      docSkills.push(entry);
    } else {
      core.push(entry);
    }
  }

  let md = `# Skills

All skills are installable via \`npx claude-skills-vault install <name>\`.

## Core Skills (${core.length})

| Skill | Description | Install |
|-------|-------------|---------|
`;

  for (const s of core) {
    md += `| **${s.name}** | ${s.desc} | \`npx claude-skills-vault install ${s.dir}\` |\n`;
  }

  if (docSkills.length > 0) {
    md += `
## Document Skills

| Skill | Description | Install |
|-------|-------------|---------|
| **docx, md, pdf, pptx, toon, xlsx** | Document processing (Word, Markdown, PDF, PowerPoint, TOON, Excel) | \`npx claude-skills-vault install document-skills\` |
`;
  }

  md += `
## External Skills (Install via npx)

Top community and official skills from external repos:

| Skill | Source | What It Does | Install |
|-------|--------|--------------|---------|
| **frontend-design** | [Anthropic](https://github.com/anthropics/skills) | Bold UI design, avoids AI slop (277K+ installs) | \`npx skills add anthropics/skills --skill frontend-design\` |
| **webapp-testing** | [Anthropic](https://github.com/anthropics/skills) | Test local web apps with Playwright | \`npx skills add anthropics/skills --skill webapp-testing\` |
| **web-design-guidelines** | [Vercel](https://github.com/vercel-labs/agent-skills) | 100+ accessibility and UX rules | \`npx skills add vercel-labs/agent-skills --skill web-design-guidelines\` |
| **superpowers** | [obra](https://github.com/obra/superpowers) | 20+ skills: brainstorm\u2192spec\u2192plan\u2192execute\u2192review (40.9K stars) | \`npx skills add obra/superpowers\` |
| **shadcn-ui** | [shadcn](https://ui.shadcn.com/docs/skills) | Component context + pattern enforcement | See [docs](https://ui.shadcn.com/docs/skills) |
| **snyk-fix** | [Snyk](https://github.com/snyk/studio-recipes) | Auto-fix vulnerabilities, validate, create PRs | See [repo](https://github.com/snyk/studio-recipes) |
`;

  return md;
}

// ── COMMANDS.md ──────────────────────────────────────────────────────

function generateCommandsMd() {
  const files = fs.readdirSync(COMMANDS_DIR)
    .filter(f => f.endsWith(".md"))
    .sort();

  const commands = [];
  for (const f of files) {
    const content = fs.readFileSync(path.join(COMMANDS_DIR, f), "utf-8");
    const fm = parseFrontmatter(content);
    const name = fm.name || f.replace(/\.md$/, "");

    let desc = fm.description || "";
    if (!desc) {
      const body = content.replace(/^---[\s\S]*?---\s*/, "");
      for (const line of body.split("\n")) {
        const t = line.trim();
        if (!t || t.startsWith("#") || t.startsWith("**IMPORTANT")) continue;
        if (t.startsWith("Goal:")) { desc = firstSentence(t.replace(/^Goal:\s*/, "")); break; }
        desc = firstSentence(t);
        break;
      }
    }

    commands.push({ name, desc: truncate(desc), file: f });
  }

  let md = `# Commands

Slash commands available in Claude Code. Install all commands with:

\`\`\`bash
npx claude-skills-vault install --commands
\`\`\`

## Available Commands (${commands.length})

| Command | Description | Invocation |
|---------|-------------|------------|
`;

  for (const c of commands) {
    md += `| **${c.name}** | ${c.desc} | \`/${c.name}\` |\n`;
  }

  md += `
## Usage

Commands are loaded automatically from \`.claude/commands/\`. Invoke them by typing the slash command in Claude Code.
`;

  return md;
}

// ── MCP-SERVERS.md ───────────────────────────────────────────────────

function generateMcpServersMd() {
  // Read the existing MCP-SERVERS.md since it has curated sections
  // that can't be fully auto-generated (custom vs official vs third-party)
  const existing = path.join(ROOT, "MCP-SERVERS.md");
  if (fs.existsSync(existing)) {
    // Just update the server count in the existing file
    let content = fs.readFileSync(existing, "utf-8");
    const serverCount = fs.readdirSync(MCP_DIR, { withFileTypes: true })
      .filter(d => d.isDirectory()).length;

    // Return existing content (MCP servers have too much structure to auto-generate)
    return content;
  }
  return null;
}

// ── cli/README.md ────────────────────────────────────────────────────

function generateCliReadme() {
  const skillCount = fs.readdirSync(SKILLS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory()).length;
  const cmdCount = fs.readdirSync(COMMANDS_DIR)
    .filter(f => f.endsWith(".md")).length;
  const mcpCount = fs.readdirSync(MCP_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory()).length;

  return `# claude-skills-vault

Install [Claude Code](https://claude.ai/code) skills, commands, and MCP servers from the community vault.

**${skillCount} skills** | **${cmdCount} commands** | **${mcpCount} MCP servers**

## Quick Start

\`\`\`bash
# List all available skills
npx claude-skills-vault list

# Install a specific skill
npx claude-skills-vault install brainstorm

# Install multiple skills
npx claude-skills-vault install brainstorm owasp-security github-cli

# Install all skills
npx claude-skills-vault install --all
\`\`\`

## Commands

| Command | Description |
|---------|-------------|
| \`list\` | List all available skills, commands, and MCP servers |
| \`install <name> [names...]\` | Install skills/commands by name |
| \`search <query>\` | Search by keyword |
| \`info <name>\` | Show details about a skill (author, source, category) |

## Install Options

| Flag | Description |
|------|-------------|
| \`--all\` | Install all skills and commands |
| \`--skills\` | Install all skills only |
| \`--commands\` | Install all commands only |
| \`--force\` | Overwrite existing files |
| \`--dry-run\` | Show what would be installed |

## How It Works

Skills are downloaded directly from the [claude-skills-vault](https://github.com/georgekhananaev/claude-skills-vault) GitHub repository and placed into your project's \`.claude/skills/\` directory. No git clone required.

## Requirements

- Node.js >= 18
- A project directory where you want to install skills

## License

MIT — See [GitHub](https://github.com/georgekhananaev/claude-skills-vault) for full details.
`;
}

// ── Main ─────────────────────────────────────────────────────────────

const skillsMd = generateSkillsMd();
fs.writeFileSync(path.join(ROOT, "SKILLS.md"), skillsMd);

const commandsMd = generateCommandsMd();
fs.writeFileSync(path.join(ROOT, "COMMANDS.md"), commandsMd);

// MCP-SERVERS.md is kept as-is (too structured to auto-generate)
// Just log that it exists
const mcpExists = fs.existsSync(path.join(ROOT, "MCP-SERVERS.md"));

const cliReadme = generateCliReadme();
fs.writeFileSync(path.join(ROOT, "cli", "README.md"), cliReadme);

const skillCount = fs.readdirSync(SKILLS_DIR, { withFileTypes: true })
  .filter(d => d.isDirectory()).length;
const cmdCount = fs.readdirSync(COMMANDS_DIR)
  .filter(f => f.endsWith(".md")).length;

console.log(`Docs generated:`);
console.log(`  SKILLS.md      ${skillCount} skills`);
console.log(`  COMMANDS.md    ${cmdCount} commands`);
console.log(`  MCP-SERVERS.md ${mcpExists ? "exists (kept)" : "MISSING"}`);
console.log(`  cli/README.md  updated (${skillCount} skills)`);
