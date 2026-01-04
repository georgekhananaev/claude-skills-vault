# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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

### Fixed

## [1.0.0] - 2026-01-04

### Added
- **skills**: Comprehensive Claude skills collection (code-reviewer, system-architect, pydantic-model, skill-creator, token-formatter, project-change-log)
- **skills**: Document processing skills (docx, pdf, pptx, xlsx, md) with OOXML schemas
- **commands**: Commit command with conventional commits and changelog integration
- **mcp-servers**: PostgreSQL and Jira MCP server templates
- **tutorials**: Commands, Skills, and MCP Servers tutorials
- NOTICE file for attribution guidelines
- README with project documentation
