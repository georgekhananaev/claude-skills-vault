#!/usr/bin/env node
/**
 * JSON <-> TOON Converter
 *
 * Uses official @toon-format/toon library.
 *
 * Install: npm install @toon-format/toon
 *
 * Usage:
 *   node convert.js input.json              # JSON to TOON
 *   node convert.js input.json -o out.toon  # JSON to TOON with output file
 *   node convert.js --to-json input.toon    # TOON to JSON
 *   node convert.js --verify input.json     # Verify round-trip
 */

const fs = require('fs');
const path = require('path');

let toon;
try {
    toon = require('@toon-format/toon');
} catch (e) {
    console.error('Error: @toon-format/toon not installed.');
    console.error('Run: npm install @toon-format/toon');
    process.exit(1);
}

function parseArgs() {
    const args = process.argv.slice(2);
    const opts = {
        file: null,
        output: null,
        toJson: false,
        verify: false,
        pretty: false
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '--to-json') {
            opts.toJson = true;
        } else if (arg === '--verify') {
            opts.verify = true;
        } else if (arg === '--pretty') {
            opts.pretty = true;
        } else if (arg === '-o' || arg === '--output') {
            opts.output = args[++i];
        } else if (!arg.startsWith('-')) {
            opts.file = arg;
        }
    }

    return opts;
}

function readInput(file) {
    if (file) {
        return fs.readFileSync(file, 'utf8');
    }
    // Read from stdin
    return fs.readFileSync(0, 'utf8');
}

function writeOutput(content, output) {
    if (output) {
        fs.writeFileSync(output, content);
        console.log(`Written to ${output}`);
    } else {
        console.log(content);
    }
}

function deepEqual(a, b) {
    if (a === b) return true;
    if (typeof a !== typeof b) return false;
    if (a === null || b === null) return a === b;

    if (Array.isArray(a)) {
        if (!Array.isArray(b) || a.length !== b.length) return false;
        return a.every((item, i) => deepEqual(item, b[i]));
    }

    if (typeof a === 'object') {
        const keysA = Object.keys(a);
        const keysB = Object.keys(b);
        if (keysA.length !== keysB.length) return false;
        return keysA.every(key => deepEqual(a[key], b[key]));
    }

    return false;
}

function main() {
    const opts = parseArgs();
    const content = readInput(opts.file);

    try {
        if (opts.toJson) {
            // TOON to JSON
            const data = toon.decode(content);
            const output = opts.pretty
                ? JSON.stringify(data, null, 2)
                : JSON.stringify(data);
            writeOutput(output, opts.output);
        } else {
            // JSON to TOON
            const data = JSON.parse(content);

            if (opts.verify) {
                // Verify round-trip
                const encoded = toon.encode(data);
                const decoded = toon.decode(encoded);

                if (deepEqual(data, decoded)) {
                    console.log('Round-trip successful');
                    process.exit(0);
                } else {
                    console.error('Round-trip mismatch');
                    console.error('Original:', JSON.stringify(data, null, 2));
                    console.error('Recovered:', JSON.stringify(decoded, null, 2));
                    process.exit(1);
                }
            }

            const output = toon.encode(data);
            writeOutput(output, opts.output);
        }
    } catch (err) {
        console.error('Error:', err.message);
        process.exit(1);
    }
}

main();
