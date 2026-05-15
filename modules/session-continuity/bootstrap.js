// <module>/bootstrap.js — local unconditional self-heal (registered once in ~/.claude).
// Verifies the module exists and key files are present; advisory only (fail-open).
const fs = require('fs'); const path = require('path'); const os = require('os');
const SRC = path.join(os.homedir(), '.claude', 'skills', 'claude-power-pack', 'modules', 'session-continuity');
const need = ['recorder.js', 'mark.js', 'governance-guard.js', 'restore.ps1', 'lib/registry.js'];
let ok = true;
for (const f of need) { if (!fs.existsSync(path.join(SRC, f))) { ok = false; break; } }
if (!ok) console.error('[session-continuity:bootstrap] module incomplete at ' + SRC + ' - reinstall the CPP module');
process.exit(0);
