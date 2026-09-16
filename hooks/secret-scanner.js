#!/usr/bin/env node
/**
 * Secret Scanner Hook — PreToolUse
 *
 * Intercepts Write and Edit tool calls. If the content being written
 * matches known secret patterns, the tool call is BLOCKED with a warning.
 *
 * Patterns detected:
 *   - Anthropic tokens: sk-ant-*, sk-ant-oat*, sk-ant-ort*
 *   - Platform tokens: ptlc_*
 *   - Bearer JWT tokens: Bearer ey...
 *   - Generic API keys: long hex/base64 assigned to key-like variables
 *   - AWS keys: AKIA*
 *   - Private keys: -----BEGIN (RSA|EC|PRIVATE) KEY-----
 *   - Hardcoded passwords in Java/JS/Python assignments
 *
 * Phase 1 of Master Plan — Security First
 */

const SECRET_PATTERNS = [
  // Anthropic tokens
  { pattern: /sk-ant-[a-zA-Z0-9_-]{20,}/, name: 'Anthropic API token' },
  // Platform tokens
  { pattern: /ptlc_[a-zA-Z0-9_-]{20,}/, name: 'Platform token' },
  // Bearer JWT (long base64 JWT tokens — dots separate JWT segments)
  { pattern: /Bearer\s+eyJ[a-zA-Z0-9_.\-]{50,}/, name: 'Bearer JWT token' },
  // AWS access keys
  { pattern: /AKIA[0-9A-Z]{16}/, name: 'AWS Access Key' },
  // Private keys
  { pattern: /-----BEGIN\s+(RSA\s+|EC\s+)?PRIVATE\s+KEY-----/, name: 'Private key' },
  // Generic long secrets assigned to variables (password = "...", api_key = "...", secret = "...")
  { pattern: /(?:password|passwd|secret|api_key|apikey|api_secret|token|auth_token)\s*[:=]\s*["'][^"']{16,}["']/i, name: 'Hardcoded credential' },
  // Hex strings that look like secrets (40+ chars assigned to key-like vars)
  { pattern: /(?:key|secret|token|password)\s*[:=]\s*["'][0-9a-fA-F]{40,}["']/i, name: 'Hex secret value' },
];

// Files that legitimately contain credentials (vault, encrypted stores)
// or whose domain vocabulary collides with credential-assignment regex
// (vault-UI components carry literal labels like `secretLabel: "Secret value..."`
// that the generic pattern 7 matches as a "hardcoded credential"). See
// memory/vault-ui-component-scanner-collision.md (TUA-X 2026-05-19).
const ALLOWED_PATHS = [
  /[/\\]vault\.py$/,
  /[/\\]vault\.json\.enc$/,
  /[/\\]\.vault[/\\]/,
  /[/\\]credential-vault[/\\]/,
  // Vault-UI React components — domain vocabulary collision allowlist.
  /[/\\]ApiKeysAdminPanel\.tsx$/,
];

function isAllowedPath(filePath) {
  return ALLOWED_PATHS.some(re => re.test(filePath));
}

function scanContent(content) {
  const matches = [];
  for (const { pattern, name } of SECRET_PATTERNS) {
    if (pattern.test(content)) {
      matches.push(name);
    }
  }
  return matches;
}

// 2026-04-25 schema migration. Legacy `{decision:'allow'}` shape is rejected
// by the current Claude Code harness with "Hook JSON output validation failed
// — Invalid input" on every hook call. Migrating to schema-version-agnostic
// signaling: exit 0 with empty stdout = pass, exit 2 with stderr = block.
// Scanner detection logic is unchanged — only the wire format of the
// decision changes. Block path still raises the same security stop.
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

    // Only scan Write and Edit operations — every other tool passes through.
    if (toolName !== 'Write' && toolName !== 'Edit') return emitPass();

    const toolInput = data.tool_input || {};
    const filePath = toolInput.file_path || '';

    // Skip vault files (legitimately contain credentials).
    if (isAllowedPath(filePath)) return emitPass();

    const contentToScan = [
      toolInput.content || '',
      toolInput.new_string || '',
    ].join('\n');

    if (!contentToScan.trim()) return emitPass();

    const found = scanContent(contentToScan);

    if (found.length > 0) {
      return emitBlock(
        `🔒 SECRET SCANNER: Blocked — detected ${found.join(', ')} in content being written to ${filePath}. Move secrets to vault or use environment variables.`
      );
    }
    return emitPass();
  } catch (e) {
    // Parse error → pass (don't block legitimate work on a JSON hiccup).
    return emitPass();
  }
});
