---
name: claude-seo
description: SEO toolkit with 12 specialist sub-skills — full site audits, technical SEO, content optimization, schema markup, sitemap generation, image SEO, hreflang, geo-targeting, competitor analysis, and programmatic SEO. Use when auditing websites, optimizing pages, or planning SEO strategy.
source: "https://github.com/AgriciDaniel/claude-seo"
---

# Claude SEO

Comprehensive SEO toolkit with parallel sub-agent delegation for full-site audits.

## Sub-Skills

| Skill | Description |
|-------|-------------|
| **seo-audit** | Full website SEO audit — crawls up to 500 pages, delegates to 7 specialists |
| **seo-technical** | Technical SEO — crawlability, indexing, site speed, Core Web Vitals |
| **seo-content** | Content optimization — keyword density, readability, internal linking |
| **seo-page** | On-page SEO — title tags, meta descriptions, headings, structured data |
| **seo-schema** | Schema.org markup generation and validation |
| **seo-sitemap** | XML sitemap generation and validation |
| **seo-images** | Image SEO — alt text, compression, lazy loading, WebP |
| **seo-hreflang** | International SEO — hreflang tags for multi-language sites |
| **seo-geo** | Local/geo SEO — Google Business Profile, local schema |
| **seo-competitor-pages** | Competitor page analysis and gap identification |
| **seo-programmatic** | Programmatic SEO — template pages, dynamic content at scale |
| **seo-plan** | SEO strategy planning with business-type templates |

## Usage

Sub-skills are in `skills/` subdirectories. The `seo-audit` skill orchestrates the others for comprehensive audits.
