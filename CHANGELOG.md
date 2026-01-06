# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **skills**: Add doc-navigator skill for efficient codebase documentation navigation
- **skills**: Add ux-toolkit skill for comprehensive UX evaluation
- **commands**: Add create-pr command for GitHub pull request creation

### Changed
- Normalize line endings to LF for cross-platform consistency

### Fixed

## [1.0.5] - 2026-01-05

### Added
- **skills**: Add pep8 skill for Python 3.11+ style enforcement with check/fix scripts

### Changed
- **readme**: Add pep8 skill to core skills list

## [1.0.4] - 2026-01-05

### Added
- **mcp-servers**: Add chrome-devtools MCP server reference

### Changed
- **commands**: Enhance plan-feature with AskUserQuestion tool for interactive requirement gathering
- **skills**: Streamline fastapi-senior-dev with modular reference files (security, database, caching, observability, microservices, API lifecycle, production ops)

## [1.0.3] - 2026-01-05

### Added
- **skills**: Add gemini-cli skill for local Gemini CLI interaction (run queries, compare responses)
- **skills**: Add fastapi-senior-dev skill for production-ready FastAPI development
- **skills**: Add testing-automation-expert skill for comprehensive testing strategies
- **commands**: Add plan-feature command for production-grade feature planning

### Changed
- **commands**: Rename commit.md to git-commit.md for clarity
- **commands**: Rename push.md to git-push.md for clarity
- **readme**: Update commands table (renamed commands, add plan-feature)
- **readme**: Add new skills to Core Skills table
- **readme**: Add Changelog section with link to CHANGELOG.md

## [1.0.2] - 2026-01-04

### Added
- **mcp-servers**: Add 35 MCP server configurations and references
  - Official active: everything, fetch, filesystem, memory, sequential-thinking, time
  - Official archived: git, slack, sqlite
  - AWS Labs: 64+ servers (documentation, infrastructure, AI/ML, data, operations)
  - Third-party: Stripe, Netlify, Vercel, Canva, Sentry, PostHog, Atlassian, Monday, Figma, Linear, Notion, Playwright, Puppeteer, Airtable, GCP, MUI, Next.js, Kubernetes, Cloudflare, Codex, Context7, GitHub
  - Custom implementations with source: MongoDB, Supabase
  - SDK references for all 10 official MCP SDKs (TypeScript, Python, Go, Rust, Java, Kotlin, C#, Swift, Ruby, PHP)

### Changed
- **commands**: Add explicit invocation guards to commit.md and push.md (prevent auto-execution)
- **commands**: Remove add-mcp command
- **readme**: Add Contributing section
- **readme**: Update with comprehensive MCP server documentation (35 servers, SDK references)

## [1.0.1] - 2026-01-04

### Added
- **commands**: Add push command with uncommitted changes check and changelog versioning
- **skills**: Add mcp-builder skill with Python/Node reference docs and evaluation scripts
- **skills**: Add toon skill for token-optimized JSON notation (~40% token reduction)
- **commands**: Add comprehensive create-skill command with testing requirements
- **commands**: Add add-mcp command for MCP server setup
- CLAUDE.md project configuration file

### Changed
- Replace preview.webp with preview.jpg and add to README
- **commands**: Clarify changelog requirement in commit command as REQUIRED step
- **commands**: Compress commit.md using token-formatter (~54% reduction)
- **commands**: Make commit command dynamic (use git config for author)
- **skills**: Add author credits to document-skills (ComposioHQ for xlsx/pdf/pptx/docx, George Khananaev for toon/md)
- **skills**: Add YAML frontmatter to token-formatter and md skills
- **skills**: Remove redundant cheatsheet.md from token-formatter (content in SKILL.md)
- Update .gitignore with additional patterns
- Update README.md

## [1.0.0] - 2026-01-04

### Added
- **skills**: Comprehensive Claude skills collection (code-reviewer, system-architect, pydantic-model, skill-creator, token-formatter, project-change-log)
- **skills**: Document processing skills (docx, pdf, pptx, xlsx, md) with OOXML schemas
- **commands**: Commit command with conventional commits and changelog integration
- **mcp-servers**: PostgreSQL and Jira MCP server templates
- **tutorials**: Commands, Skills, and MCP Servers tutorials
- NOTICE file for attribution guidelines
- README with project documentation
