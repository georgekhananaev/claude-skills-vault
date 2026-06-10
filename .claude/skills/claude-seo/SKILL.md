---
name: claude-seo
description: SEO toolkit with 24 specialist sub-skills (upstream v2.0) — full site audits, technical SEO, content optimization & briefs, schema markup, sitemaps, image SEO, hreflang, local/maps SEO, backlinks, topic clustering, SERP experience (SXO), drift monitoring, Google APIs (GSC/PageSpeed/CrUX), e-commerce, programmatic SEO, and GEO for AI Overviews/ChatGPT/Perplexity. Use when auditing websites, optimizing pages or content, tracking SEO regressions, or planning SEO strategy.
source: "https://github.com/AgriciDaniel/claude-seo"
---

# Claude SEO

Comprehensive SEO toolkit (upstream v2.0.0) with parallel sub-agent delegation for full-site audits. Sub-skills live in `skills/<name>/SKILL.md`; shared Python helpers in `scripts/` (referenced by sub-skills as the plugin-root scripts dir — resolve them relative to THIS skill's root).

## Sub-Skills

### Core analysis

| Skill | Description |
|-------|-------------|
| **seo-audit** | Full website SEO audit — crawls site, delegates to specialists in parallel |
| **seo-page** | Deep single-page analysis — titles, metas, headings, structured data |
| **seo-technical** | Crawlability, indexing, site speed, Core Web Vitals (incl. INP) |
| **seo-content** | Content optimization — keyword use, readability, E-E-A-T, internal links |
| **seo-content-brief** | Competitive content briefs w/ per-section word counts & competitor scoring |
| **seo-schema** | Schema.org markup generation & validation |
| **seo-sitemap** | XML sitemap generation & validation |
| **seo-images** | Image SEO — alt text, compression, lazy loading, WebP |
| **seo-hreflang** | International SEO — hreflang for multi-language sites |
| **seo-competitor-pages** | Competitor page analysis & gap identification |
| **seo-programmatic** | Programmatic SEO — template pages at scale |
| **seo-plan** | SEO strategy planning w/ business-type templates |

### New in v2.0

| Skill | Description |
|-------|-------------|
| **seo-geo** | GEO — visibility in AI Overviews, ChatGPT, Perplexity |
| **seo-local** | Local SEO — Google Business Profile, NAP, citations, reviews, local schema |
| **seo-maps** | Maps intelligence — geo-grid rank tracking, GBP API audit, review mining |
| **seo-backlinks** | Backlink profile — referring domains, anchors, toxic links, gaps (free APIs: Moz, CommonCrawl) |
| **seo-cluster** | SERP-overlap topic clustering for content architecture |
| **seo-sxo** | Search Experience Optimization — SERP-derived intent & page-type match |
| **seo-drift** | "Git for SEO" — baseline, diff & track SEO-critical element regressions |
| **seo-google** | Google APIs — Search Console, PageSpeed Insights v5, CrUX history, Indexing |
| **seo-ecommerce** | Shopping visibility, product schema, marketplace & pricing intel |
| **seo-flow** | FLOW framework — evidence-led Find → Leverage → Optimize → Win loop |
| **seo-dataforseo** | Live SERP/keyword/competitor data via DataForSEO MCP (needs account) |
| **seo-image-gen** | AI-generated SEO assets (OG images, heroes) — needs Gemini API key |

## Usage

- Full audit → `seo-audit` orchestrates the others; single page → `seo-page`.
- Read the sub-skill's SKILL.md before use; each documents its scripts & inputs.
- API-key-dependent sub-skills (`seo-dataforseo`, `seo-google`, `seo-maps`, `seo-image-gen`, parts of `seo-backlinks`): check key availability first and fall back to the no-API path the sub-skill documents.
- Upstream ships 18 plugin sub-agents; outside the plugin, run their roles as generic parallel subagents per `seo-audit`'s delegation table.
