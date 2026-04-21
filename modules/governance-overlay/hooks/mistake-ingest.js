#!/usr/bin/env node
/**
 * mistake-ingest.js — PostToolUse hook for governance-overlay (MC-OVO-34)
 *
 * Fires after Edit/Write tool calls. If the edited file is
 * modules/governance-overlay/mistakes-registry.md, detects newly-added
 * Mistake #N sections by diffing against a cached seen-list
 * (_audit_cache/seen_mistakes.json) and invokes
 * tools/session_checkpoint.py learn-error for each newly-added mistake.
 *
 * Hook contract:
 *   - Reads JSON from stdin (Claude Code PostToolUse payload)
 *   - Emits JSON to stdout (hook response — must be valid JSON)
 *   - Exits 0 on success, non-zero only on unrecoverable error
 *   - Never writes to stdout except the final JSON (logs go to stderr)
 *
 * Registration (put in ~/.claude/settings.json hooks array):
 *   {
 *     "matcher": "Edit|Write",
 *     "hooks": [{
 *       "type": "command",
 *       "command": "node ${PWD}/modules/governance-overlay/hooks/mistake-ingest.js"
 *     }]
 *   }
 *
 * Closes capability-audit Gap meta (+1%): self-correcting vault ingestion.
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const REGISTRY_REL = 'modules/governance-overlay/mistakes-registry.md';
const CACHE_REL = '_audit_cache/seen_mistakes.json';
const CHECKPOINT_TOOL_REL = 'tools/session_checkpoint.py';

const MISTAKE_HEADER_REGEX = /^## Mistake #(\d+):\s*(.+?)\s*$/gm;

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });

process.stdin.on('end', () => {
    let respond = (obj) => {
        try { process.stdout.write(JSON.stringify(obj)); } catch { }
        process.exit(0);
    };

    let payload;
    try {
        payload = JSON.parse(input);
    } catch {
        // Malformed payload — emit noop JSON, do not crash.
        return respond({});
    }

    const toolName = payload.tool_name || payload.toolName || '';
    const toolInput = payload.tool_input || payload.toolInput || {};
    const filePath = toolInput.file_path || toolInput.filePath || '';

    // Fast path: not an Edit/Write → noop
    if (toolName !== 'Edit' && toolName !== 'Write') {
        return respond({});
    }

    // Only care about the mistakes-registry file (handle both Windows and POSIX paths)
    const normalized = filePath.replace(/\\/g, '/');
    if (!normalized.endsWith(REGISTRY_REL)) {
        return respond({});
    }

    // Resolve project root — walk up from the edited file until we hit the repo root
    let projectRoot;
    try {
        projectRoot = path.resolve(filePath, '..', '..', '..', '..');  // modules/governance-overlay/ → repo
        // Sanity: registry should exist at the resolved root
        if (!fs.existsSync(path.join(projectRoot, REGISTRY_REL))) {
            // Fallback: walk up from filePath looking for .git
            let dir = path.dirname(path.resolve(filePath));
            while (dir !== path.dirname(dir)) {
                if (fs.existsSync(path.join(dir, '.git'))) { projectRoot = dir; break; }
                dir = path.dirname(dir);
            }
        }
    } catch (err) {
        process.stderr.write(`[mistake-ingest] could not resolve project root: ${err.message}\n`);
        return respond({});
    }

    const registryPath = path.join(projectRoot, REGISTRY_REL);
    const cachePath = path.join(projectRoot, CACHE_REL);

    // Read registry + extract current mistake numbers
    let registryText;
    try {
        registryText = fs.readFileSync(registryPath, 'utf8');
    } catch (err) {
        process.stderr.write(`[mistake-ingest] could not read registry: ${err.message}\n`);
        return respond({});
    }

    const currentMistakes = new Map();
    let match;
    MISTAKE_HEADER_REGEX.lastIndex = 0;
    while ((match = MISTAKE_HEADER_REGEX.exec(registryText)) !== null) {
        const num = parseInt(match[1], 10);
        const label = match[2].trim();
        currentMistakes.set(num, label);
    }

    // Load cached seen-list
    let seen = { seen_numbers: [], last_updated: null };
    try {
        if (fs.existsSync(cachePath)) {
            seen = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
        }
    } catch (err) {
        process.stderr.write(`[mistake-ingest] cache read error, reinitializing: ${err.message}\n`);
        seen = { seen_numbers: [], last_updated: null };
    }

    const seenSet = new Set(seen.seen_numbers || []);
    const newMistakes = [];
    for (const [num, label] of currentMistakes.entries()) {
        if (!seenSet.has(num)) newMistakes.push({ num, label });
    }

    // Nothing new → update cache timestamp and exit
    if (newMistakes.length === 0) {
        try {
            fs.mkdirSync(path.dirname(cachePath), { recursive: true });
            fs.writeFileSync(cachePath, JSON.stringify({
                seen_numbers: Array.from(currentMistakes.keys()).sort((a, b) => a - b),
                last_updated: new Date().toISOString(),
            }, null, 2));
        } catch { /* best-effort */ }
        return respond({});
    }

    // For each new mistake, fire session_checkpoint.py learn-error
    const checkpointTool = path.join(projectRoot, CHECKPOINT_TOOL_REL);
    const fires = [];
    for (const m of newMistakes) {
        const symptom = m.label;
        const rootCause = `Mistake #${m.num} entry in modules/governance-overlay/mistakes-registry.md § '#${m.num}:' section documents Detection + Example + Root Cause.`;
        const fix = `Apply the Prevention list from Mistake #${m.num} — see registry entry for the canonical steps.`;
        try {
            // Verified signature (session_checkpoint.py learn-error --help):
            // --category CATEGORY | --symptom SYMPTOM | --root-cause ROOT_CAUSE | --fix FIX
            const out = execFileSync('python', [
                checkpointTool, 'learn-error',
                '--category', 'governance-mistake',
                '--symptom', symptom,
                '--root-cause', rootCause,
                '--fix', fix,
            ], {
                cwd: projectRoot,
                encoding: 'utf8',
                stdio: ['ignore', 'pipe', 'pipe'],
                timeout: 5000,
            });
            fires.push({ num: m.num, label: m.label, status: 'fired', stdout: out.trim() });
        } catch (err) {
            // Non-fatal: the tool may not be installed or python may be missing. Log, continue.
            process.stderr.write(`[mistake-ingest] learn-error failed for #${m.num}: ${err.message || err}\n`);
            fires.push({ num: m.num, label: m.label, status: 'failed', error: String(err.message || err) });
        }
    }

    // Update cache with all current mistakes (including newly-fired ones)
    try {
        fs.mkdirSync(path.dirname(cachePath), { recursive: true });
        fs.writeFileSync(cachePath, JSON.stringify({
            seen_numbers: Array.from(currentMistakes.keys()).sort((a, b) => a - b),
            last_updated: new Date().toISOString(),
            last_fires: fires,
        }, null, 2));
    } catch (err) {
        process.stderr.write(`[mistake-ingest] cache write failed: ${err.message}\n`);
    }

    // Emit an advisory message to the Claude session so the agent knows what fired
    const summary = fires.map((f) => `#${f.num} (${f.status})`).join(', ');
    respond({
        hookSpecificOutput: {
            hookEventName: 'PostToolUse',
            additionalContext: `[mistake-ingest] ingested ${fires.length} new mistake(s): ${summary}`,
        },
    });
});
