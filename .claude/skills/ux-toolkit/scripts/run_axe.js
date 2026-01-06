#!/usr/bin/env node
/**
 * Run axe-core accessibility tests on a URL or HTML file.
 *
 * Usage:
 *   node run_axe.js https://example.com
 *   node run_axe.js ./path/to/file.html
 *   node run_axe.js https://example.com --output results.json
 *
 * Prerequisites:
 *   npm install puppeteer @axe-core/puppeteer
 */

const fs = require('fs');
const path = require('path');

async function runAxe(target, outputFile) {
    let puppeteer, AxePuppeteer;

    try {
        puppeteer = require('puppeteer');
        AxePuppeteer = require('@axe-core/puppeteer').AxePuppeteer;
    } catch (e) {
        console.error('Missing dependencies. Install with:');
        console.error('  npm install puppeteer @axe-core/puppeteer');
        process.exit(1);
    }

    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();

    try {
        // Handle local files or URLs
        const url = target.startsWith('http')
            ? target
            : `file://${path.resolve(target)}`;

        console.log(`\nAnalyzing: ${url}\n`);

        await page.goto(url, { waitUntil: 'networkidle0' });

        const results = await new AxePuppeteer(page)
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .analyze();

        // Process results
        const summary = {
            url: target,
            timestamp: new Date().toISOString(),
            violations: results.violations.length,
            passes: results.passes.length,
            incomplete: results.incomplete.length,
            inapplicable: results.inapplicable.length
        };

        // Print summary
        console.log('='.repeat(60));
        console.log('AXE-CORE ACCESSIBILITY REPORT');
        console.log('='.repeat(60));
        console.log(`\nSummary:`);
        console.log(`  ❌ Violations:   ${summary.violations}`);
        console.log(`  ✅ Passes:       ${summary.passes}`);
        console.log(`  ⚠️  Incomplete:   ${summary.incomplete}`);
        console.log(`  ➖ Inapplicable: ${summary.inapplicable}`);

        if (results.violations.length > 0) {
            console.log(`\n${'─'.repeat(60)}`);
            console.log('VIOLATIONS');
            console.log('─'.repeat(60));

            results.violations.forEach((violation, i) => {
                const severity = {
                    critical: '🔴',
                    serious: '🟠',
                    moderate: '🟡',
                    minor: '⚪'
                }[violation.impact] || '❓';

                console.log(`\n${i + 1}. ${severity} [${violation.impact.toUpperCase()}] ${violation.id}`);
                console.log(`   ${violation.description}`);
                console.log(`   Help: ${violation.helpUrl}`);
                console.log(`   Affected elements: ${violation.nodes.length}`);

                violation.nodes.slice(0, 3).forEach(node => {
                    console.log(`   - ${node.target.join(' > ')}`);
                });

                if (violation.nodes.length > 3) {
                    console.log(`   ... and ${violation.nodes.length - 3} more`);
                }
            });
        }

        if (results.incomplete.length > 0) {
            console.log(`\n${'─'.repeat(60)}`);
            console.log('NEEDS REVIEW (Manual Check Required)');
            console.log('─'.repeat(60));

            results.incomplete.slice(0, 5).forEach((item, i) => {
                console.log(`\n${i + 1}. ${item.id}`);
                console.log(`   ${item.description}`);
            });

            if (results.incomplete.length > 5) {
                console.log(`\n... and ${results.incomplete.length - 5} more items need review`);
            }
        }

        // Save full results if output specified
        if (outputFile) {
            const output = {
                ...summary,
                violations: results.violations,
                incomplete: results.incomplete,
                passes: results.passes.map(p => ({ id: p.id, description: p.description }))
            };
            fs.writeFileSync(outputFile, JSON.stringify(output, null, 2));
            console.log(`\n✅ Full results saved to: ${outputFile}`);
        }

        console.log('\n');

        // Exit with error code if violations found
        process.exitCode = results.violations.length > 0 ? 1 : 0;

    } catch (error) {
        console.error('Error running axe:', error.message);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
}

// CLI
const args = process.argv.slice(2);

if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log(`
Usage: node run_axe.js <url-or-file> [options]

Arguments:
  url-or-file    URL or path to HTML file to test

Options:
  --output, -o   Save full results to JSON file
  --help, -h     Show this help

Examples:
  node run_axe.js https://example.com
  node run_axe.js ./index.html
  node run_axe.js https://example.com --output results.json
`);
    process.exit(0);
}

const target = args[0];
const outputIndex = args.findIndex(a => a === '--output' || a === '-o');
const outputFile = outputIndex !== -1 ? args[outputIndex + 1] : null;

runAxe(target, outputFile);
