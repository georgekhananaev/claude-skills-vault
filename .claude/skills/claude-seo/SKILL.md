---
name: claude-seo
description: SEO toolkit with 25 specialist sub-skills (upstream v2.6) — full site audits, technical SEO, content optimization & briefs, schema markup, sitemaps, image SEO, hreflang, local/maps SEO, backlinks, topic clustering, SERP experience (SXO), drift monitoring, Google APIs (GSC/PageSpeed/CrUX), e-commerce, programmatic SEO, AI-crawler readiness (llms.txt, robots rules, WebMCP), and GEO for AI Overviews/ChatGPT/Perplexity. Use when auditing websites, optimizing pages or content, tracking SEO regressions, or planning SEO strategy.
source: "https://github.com/AgriciDaniel/claude-seo"
---

# Claude SEO

Comprehensive SEO toolkit (upstream v2.6.0) with parallel sub-agent delegation for full-site audits. This folder mirrors the upstream plugin root: sub-skills live in `skills/<name>/SKILL.md`, shared references in `skills/seo/references/`, Python helpers in `scripts/`, plus `schema/`, `data/` and `requirements.txt`.

## Paths & runtime (read first)

Upstream files are synced verbatim, so they refer to the plugin root as `${CLAUDE_PLUGIN_ROOT}`. That variable is not set when this is installed as a plain skill. Wherever a sub-skill says `${CLAUDE_PLUGIN_ROOT}`, use the absolute path of THIS skill's folder (the one holding this file), e.g. `.claude/skills/claude-seo`.

Python tools run through the bundled launcher, never w/ a bare interpreter:

```bash
SEO_ROOT="<absolute path of this folder>"
"$SEO_ROOT/scripts/claude-seo" doctor                 # is the runtime ready?
"$SEO_ROOT/scripts/claude-seo" setup                  # once: isolated venv + deps + Chromium
"$SEO_ROOT/scripts/claude-seo" setup --skip-browser   # same, w/o the Chromium download
"$SEO_ROOT/scripts/claude-seo" run <script.py> [args] # run one bundled script
```

- Needs Python 3.11 to 3.14. `setup` builds `.venv/` inside this folder from `requirements.txt`; set `CLAUDE_SEO_DATA_DIR` to keep it elsewhere.
- `run` exits 3 w/ "runtime is not ready" until `setup` has completed. Run `doctor` first and offer `setup` when needed.
- API keys & OAuth tokens live under `~/.config/claude-seo/`, never in this folder.

## Sub-Skills

### Core analysis

| Skill | Description |
|-------|-------------|
| **seo-audit** | Full website SEO audit — crawls site, delegates to specialists in parallel |
| **seo-page** | Deep single-page analysis — titles, metas, headings, structured data |
| **seo-technical** | Crawlability, indexing, site speed, Core Web Vitals (incl. INP), security headers |
| **seo-content** | Content optimization — keyword use, readability, E-E-A-T, internal links |
| **seo-content-brief** | Competitive content briefs w/ per-section word counts & competitor scoring |
| **seo-schema** | Schema.org markup generation & validation |
| **seo-sitemap** | XML sitemap generation & validation |
| **seo-images** | Image SEO — alt text, compression, lazy loading, WebP |
| **seo-hreflang** | International SEO — hreflang for multi-language sites |
| **seo-competitor-pages** | Competitor page analysis & gap identification |
| **seo-programmatic** | Programmatic SEO — template pages at scale |
| **seo-plan** | SEO strategy planning w/ business-type templates |

### Search visibility & data

| Skill | Description |
|-------|-------------|
| **seo-geo** | GEO — visibility in AI Overviews, AI Mode, ChatGPT, Perplexity |
| **seo-agentic** | Agent readiness — Lighthouse Agentic Browsing, AI crawler access, llms.txt, Markdown, WebMCP |
| **seo-local** | Local SEO — Google Business Profile, NAP, citations, reviews, local schema |
| **seo-maps** | Maps intelligence — geo-grid rank tracking, GBP API audit, review mining |
| **seo-backlinks** | Backlink profile — referring domains, anchors, toxic links, gaps (free APIs: Moz, Bing, CommonCrawl) |
| **seo-cluster** | SERP-overlap topic clustering for content architecture |
| **seo-sxo** | Search Experience Optimization — SERP-derived intent & page-type match |
| **seo-drift** | "Git for SEO" — baseline, diff & track SEO-critical element regressions |
| **seo-google** | Google APIs — Search Console, PageSpeed Insights v5, CrUX history, Indexing, GA4 |
| **seo-ecommerce** | Shopping visibility, product schema, marketplace & pricing intel |
| **seo-flow** | FLOW framework — evidence-led Find → Leverage → Optimize → Win loop (prompts CC BY 4.0) |
| **seo-dataforseo** | Live SERP/keyword/competitor data via DataForSEO MCP (needs account) |
| **seo-image-gen** | AI-generated SEO assets (OG images, heroes) — needs Gemini API key |

`skills/seo/SKILL.md` is the upstream `/seo` orchestrator. Its command table and routing rules are a useful map; its `references/` folder is shared by several sub-skills.

## Usage

- Full audit → `seo-audit` orchestrates the others; single page → `seo-page`.
- Read the sub-skill's SKILL.md before use; each documents its scripts & inputs.
- API-key-dependent sub-skills (`seo-dataforseo`, `seo-google`, `seo-maps`, `seo-image-gen`, parts of `seo-backlinks`): check key availability first and fall back to the no-API path the sub-skill documents.
- Upstream ships 19 plugin sub-agents and optional extensions (Matomo, Firecrawl, Ahrefs and others) that are not part of this copy. Outside the plugin, run the agent roles as generic parallel subagents per `seo-audit`'s delegation table; for extensions, install the upstream plugin.
