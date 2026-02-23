#!/usr/bin/env node
/**
 * Automated Accessibility Testing with axe-core
 * Runs axe-core against a URL or HTML file and reports issues.
 *
 * Prerequisites:
 *   npm install axe-core puppeteer
 *
 * Usage:
 *   node run_axe.js --url https://example.com
 *   node run_axe.js --url https://example.com --output report.json
 */

const fs = require('fs');
const path = require('path');

// Check for dependencies
let puppeteer, axeCore;
try {
    puppeteer = require('puppeteer');
} catch {
    console.error('Error: puppeteer not installed. Run: npm install puppeteer');
    process.exit(1);
}

// Parse arguments
const args = process.argv.slice(2);
const getArg = (name) => {
    const idx = args.indexOf(`--${name}`);
    return idx !== -1 && args[idx + 1] ? args[idx + 1] : null;
};

const url = getArg('url');
const outputFile = getArg('output');
const wcagLevel = getArg('level') || 'wcag2aa';

if (!url) {
    console.log(`
Automated Accessibility Testing with axe-core

Usage:
  node run_axe.js --url <URL> [options]

Options:
  --url <URL>       URL to test (required)
  --output <file>   Save JSON report to file
  --level <level>   WCAG level: wcag2a, wcag2aa (default), wcag2aaa

Examples:
  node run_axe.js --url https://example.com
  node run_axe.js --url https://example.com --output report.json --level wcag2aa
`);
    process.exit(0);
}

// Severity mapping
const impactToSeverity = {
    critical: '🔴 Critical',
    serious: '🟠 Major',
    moderate: '🟡 Minor',
    minor: '🟢 Enhancement'
};

// Main function
async function runAccessibilityAudit(targetUrl) {
    console.log(`\n🔍 Running accessibility audit on: ${targetUrl}\n`);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 800 });

        console.log('📄 Loading page...');
        await page.goto(targetUrl, { waitUntil: 'networkidle2', timeout: 30000 });

        // Inject axe-core
        console.log('🔧 Injecting axe-core...');
        await page.addScriptTag({
            url: 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.3/axe.min.js'
        });

        // Run axe
        console.log('🧪 Running analysis...\n');
        const results = await page.evaluate(async (level) => {
            const config = {
                runOnly: {
                    type: 'tag',
                    values: [level, 'best-practice']
                }
            };
            return await axe.run(document, config);
        }, wcagLevel);

        // Process results
        const violations = results.violations;
        const passes = results.passes.length;
        const incomplete = results.incomplete.length;

        // Summary
        console.log('═'.repeat(60));
        console.log('                    ACCESSIBILITY AUDIT RESULTS');
        console.log('═'.repeat(60));
        console.log(`\nURL: ${targetUrl}`);
        console.log(`WCAG Level: ${wcagLevel.toUpperCase()}`);
        console.log(`Timestamp: ${new Date().toISOString()}\n`);

        console.log('📊 Summary:');
        console.log(`   ❌ Violations: ${violations.length}`);
        console.log(`   ✅ Passed: ${passes}`);
        console.log(`   ⚠️  Needs Review: ${incomplete}\n`);

        if (violations.length === 0) {
            console.log('🎉 No accessibility violations found!\n');
        } else {
            // Group by impact
            const byImpact = { critical: [], serious: [], moderate: [], minor: [] };
            violations.forEach(v => {
                const impact = v.impact || 'minor';
                if (byImpact[impact]) byImpact[impact].push(v);
            });

            console.log('📋 Violations by Severity:\n');

            for (const [impact, items] of Object.entries(byImpact)) {
                if (items.length === 0) continue;

                console.log(`${impactToSeverity[impact]} (${items.length})`);
                console.log('-'.repeat(40));

                items.forEach((violation, i) => {
                    console.log(`\n${i + 1}. ${violation.id}`);
                    console.log(`   Description: ${violation.description}`);
                    console.log(`   Help: ${violation.help}`);
                    console.log(`   WCAG: ${violation.tags.filter(t => t.startsWith('wcag')).join(', ')}`);
                    console.log(`   Elements affected: ${violation.nodes.length}`);

                    // Show first affected element
                    if (violation.nodes[0]) {
                        const node = violation.nodes[0];
                        console.log(`   Example: ${node.target[0]}`);
                        if (node.failureSummary) {
                            const fix = node.failureSummary.split('\n')[1] || node.failureSummary;
                            console.log(`   Fix: ${fix.trim()}`);
                        }
                    }
                });

                console.log('\n');
            }
        }

        // Save JSON report if requested
        if (outputFile) {
            const report = {
                url: targetUrl,
                timestamp: new Date().toISOString(),
                wcagLevel,
                summary: {
                    violations: violations.length,
                    passes,
                    incomplete
                },
                violations: violations.map(v => ({
                    id: v.id,
                    impact: v.impact,
                    description: v.description,
                    help: v.help,
                    helpUrl: v.helpUrl,
                    tags: v.tags,
                    nodes: v.nodes.map(n => ({
                        target: n.target,
                        html: n.html,
                        failureSummary: n.failureSummary
                    }))
                }))
            };

            fs.writeFileSync(outputFile, JSON.stringify(report, null, 2));
            console.log(`📁 Report saved to: ${outputFile}`);
        }

        return violations.length;

    } finally {
        await browser.close();
    }
}

// Run
runAccessibilityAudit(url)
    .then(violationCount => {
        process.exit(violationCount > 0 ? 1 : 0);
    })
    .catch(error => {
        console.error('❌ Error:', error.message);
        process.exit(1);
    });