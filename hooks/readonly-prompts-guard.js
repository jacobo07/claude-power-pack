#!/usr/bin/env node
/**
 * Readonly Prompts Guard — PreToolUse
 *
 * Origin: MC-OVO-114 forensic audit (2026-04-26).
 * Installed: MC-OVO-122 (2026-04-26) — wired in settings.json under
 *   hooks.PreToolUse with matcher "Write|Edit|MultiEdit|NotebookEdit".
 *
 * Why this exists:
 *   `permissions.deny` rules are silently bypassed when
 *   `defaultMode: bypassPermissions` is set. The MC-OVO-114 audit wrote
 *   probe files into a deny-listed directory under bypass mode. Hooks run
 *   unconditionally regardless of permission mode, so this guard restores
 *   read-only enforcement.
 *
 * Add new read-only roots to READONLY_ROOTS as needed.
 */

const READONLY_ROOTS = [
  /[/\\]Downloads[/\\]Promptsss([/\\]|$)/i,
];

const GUARDED_TOOLS = new Set(['Write', 'Edit', 'MultiEdit', 'NotebookEdit']);

function emitPass() { process.exit(0); }
function emitBlock(msg) { process.stderr.write(msg); process.exit(2); }

let input = '';
const stdinTimeout = setTimeout(emitPass, 3000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const toolName = data.tool_name || '';
    if (!GUARDED_TOOLS.has(toolName)) return emitPass();

    const toolInput = data.tool_input || {};
    const filePath = toolInput.file_path || toolInput.notebook_path || '';
    if (!filePath) return emitPass();

    const normalised = filePath.replace(/\\/g, '/');
    const isReadOnly = READONLY_ROOTS.some(re => re.test(normalised));
    if (!isReadOnly) return emitPass();

    return emitBlock(
      `READONLY PROMPTS GUARD: ${toolName} blocked on ${filePath}. ` +
      `This path is read-only (workspace expansion via additionalDirectories). ` +
      `Copy the file to a writable location before modifying.`
    );
  } catch (e) {
    return emitPass();
  }
});
