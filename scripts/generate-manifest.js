#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

// ── Helpers ──────────────────────────────────────────────────────────

function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const fm = {};
  const lines = match[1].split('\n');
  let currentKey = null;

  for (const line of lines) {
    // Continuation line (indented) for multi-line values (YAML folded/literal scalars)
    if (currentKey && /^\s+\S/.test(line)) {
      const continuation = line.trim();
      if (fm[currentKey] && fm[currentKey] !== '>' && fm[currentKey] !== '|') {
        fm[currentKey] += ' ' + continuation;
      } else {
        fm[currentKey] = continuation;
      }
      continue;
    }
    const idx = line.indexOf(':');
    if (idx === -1) { currentKey = null; continue; }
    const key = line.slice(0, idx).trim();
    const val = line.slice(idx + 1).trim();
    if (!key) { currentKey = null; continue; }
    currentKey = key;
    // If value is > or | (YAML block scalar indicator), wait for continuation lines
    if (val === '>' || val === '|') {
      fm[key] = val;
    } else {
      fm[key] = val;
    }
  }

  // Clean up any remaining block scalar indicators
  for (const key of Object.keys(fm)) {
    if (fm[key] === '>' || fm[key] === '|') fm[key] = '';
  }

  return fm;
}

function firstSentence(text) {
  if (!text) return '';
  // Strip markdown links, bold, etc.
  const clean = text.replace(/[*_`#\[\]]/g, '').trim();
  const m = clean.match(/^(.+?[.!?])(?:\s|$)/);
  return m ? m[1].trim() : clean.split('\n')[0].trim();
}

function detectCategory(text) {
  if (!text) return 'productivity';
  const t = text.toLowerCase();
  const rules = [
    { keywords: ['security', 'owasp', 'auth'], category: 'security' },
    { keywords: ['react', 'next.js', 'nextjs', 'frontend', 'ui', 'css'], category: 'frontend' },
    { keywords: ['backend', 'api', 'database', 'express', 'fastapi'], category: 'backend' },
    { keywords: ['test', 'qa', 'coverage', 'tdd'], category: 'testing' },
    { keywords: ['swift', 'swiftui', 'ios', 'mobile', 'react native'], category: 'mobile' },
    { keywords: ['git', 'cli', 'deploy'], category: 'devops' },
    { keywords: ['mcp', 'agent', 'orchestr'], category: 'ai' },
  ];
  for (const rule of rules) {
    for (const kw of rule.keywords) {
      if (t.includes(kw)) return rule.category;
    }
  }
  return 'productivity';
}

function countFiles(dir) {
  try {
    return fs.readdirSync(dir, { withFileTypes: true })
      .filter(e => e.isFile())
      .length;
  } catch {
    return 0;
  }
}

function readVersion() {
  try {
    const cl = fs.readFileSync(path.join(ROOT, 'CHANGELOG.md'), 'utf8');
    const m = cl.match(/## \[(\d+\.\d+\.\d+)\]/);
    return m ? m[1] : '0.0.0';
  } catch {
    return '0.0.0';
  }
}

// ── Skills ───────────────────────────────────────────────────────────

function scanSkills() {
  const skillsDir = path.join(ROOT, '.claude', 'skills');
  if (!fs.existsSync(skillsDir)) return [];

  return fs.readdirSync(skillsDir, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => {
      const dir = path.join(skillsDir, d.name);
      const skillFile = path.join(dir, 'SKILL.md');
      if (!fs.existsSync(skillFile)) return null;

      const content = fs.readFileSync(skillFile, 'utf8');
      const fm = parseFrontmatter(content);
      let description = fm.description || '';

      // Fallback: extract from body if no frontmatter description
      if (!description) {
        const body = content.replace(/^---[\s\S]*?---\s*/, '');
        const lines = body.split('\n');
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith('#')) continue;
          if (trimmed.startsWith('>') || trimmed.startsWith('```') || trimmed.startsWith('-')) continue;
          description = firstSentence(trimmed);
          break;
        }
      }

      return {
        name: fm.name || d.name,
        description,
        path: `.claude/skills/${d.name}`,
        files: countFiles(dir),
        category: detectCategory(description + ' ' + (fm.name || d.name)),
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));
}

// ── Commands ─────────────────────────────────────────────────────────

function scanCommands() {
  const cmdDir = path.join(ROOT, '.claude', 'commands');
  if (!fs.existsSync(cmdDir)) return [];

  return fs.readdirSync(cmdDir)
    .filter(f => f.endsWith('.md'))
    .map(f => {
      const filePath = path.join(cmdDir, f);
      const content = fs.readFileSync(filePath, 'utf8');
      const fm = parseFrontmatter(content);

      let description = fm.description || '';
      if (!description) {
        // Try first heading line after frontmatter, then first paragraph
        const body = content.replace(/^---[\s\S]*?---\s*/, '');
        const headingMatch = body.match(/^#\s+(.+)/m);
        const paraMatch = body.match(/^(?!#)(\S.+)/m);
        description = firstSentence(paraMatch ? paraMatch[1] : (headingMatch ? headingMatch[1] : ''));
      }

      const name = fm.name || f.replace(/\.md$/, '');
      return {
        name,
        description,
        path: `.claude/commands/${f}`,
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));
}

// ── MCP Servers ──────────────────────────────────────────────────────

function scanMcpServers() {
  const mcpDir = path.join(ROOT, 'mcp-servers');
  if (!fs.existsSync(mcpDir)) return [];

  return fs.readdirSync(mcpDir, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => {
      const readme = path.join(mcpDir, d.name, 'README.md');
      if (!fs.existsSync(readme)) return null;

      const content = fs.readFileSync(readme, 'utf8');
      // Extract first heading
      const headingMatch = content.match(/^#\s+(.+)/m);
      const name = headingMatch ? headingMatch[1].trim() : d.name;

      // Extract first non-heading, non-empty paragraph line as description
      const lines = content.split('\n');
      let description = '';
      let pastFirstHeading = false;
      for (const line of lines) {
        if (line.startsWith('# ')) { pastFirstHeading = true; continue; }
        if (!pastFirstHeading) continue;
        const trimmed = line.trim();
        if (!trimmed) continue;
        if (trimmed.startsWith('#') || trimmed.startsWith('```') || trimmed.startsWith('-') || trimmed.startsWith('|')) break;
        description = firstSentence(trimmed);
        break;
      }

      return {
        name: d.name,
        description,
        path: `mcp-servers/${d.name}`,
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));
}

// ── Main ─────────────────────────────────────────────────────────────

const manifest = {
  version: readVersion(),
  generated: new Date().toISOString(),
  skills: scanSkills(),
  commands: scanCommands(),
  mcp_servers: scanMcpServers(),
};

const json = JSON.stringify(manifest, null, 2) + '\n';
const outPath = path.join(ROOT, 'manifest.json');
fs.writeFileSync(outPath, json);

// Also copy to cli/ for npm bundling
const cliPath = path.join(ROOT, 'cli', 'manifest.json');
if (fs.existsSync(path.join(ROOT, 'cli'))) {
  fs.writeFileSync(cliPath, json);
}

console.log(`manifest.json generated (${manifest.version})`);
console.log(`  Skills:      ${manifest.skills.length}`);
console.log(`  Commands:    ${manifest.commands.length}`);
console.log(`  MCP Servers: ${manifest.mcp_servers.length}`);
