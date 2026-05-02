#!/usr/bin/env node
/**
 * Skill Heat-Map Advisor — PreToolUse hook (BL-0018 / MC-SYS-34).
 *
 * Reads vault/skills_heat_map.json (built by tools/skill_heat_map_indexer.py)
 * and injects 1-2 skill-suggestion lines as additionalContext when the current
 * tool input has a clear keyword match.
 *
 * Advisory only — never blocks. Cold-start budget < 100ms (single small JSON
 * read + linear scan over 82 skills × keyword set).
 *
 * Triggers only on tools where a skill suggestion is meaningful:
 *   Bash, Edit, Write — about to act
 * Skips: Read, Grep, Glob — exploratory, suggestions would be noise.
 *
 * Suppression rules:
 *   - silent if max score < SCORE_FLOOR
 *   - silent if no description-substring match (keyword-only matches are weak)
 *   - dedupe per session via tmp flag (one advisory per session)
 *   - silent if any matched skill is already invoked this session (best-effort
 *     check via /tmp/claude-skills-used-<session>.txt populated by other hooks)
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const HEAT_MAP_PATH = path.join(
  os.homedir(),
  '.claude', 'skills', 'claude-power-pack', 'vault', 'skills_heat_map.json',
);

const ELIGIBLE_TOOLS = new Set(['Bash', 'Edit', 'Write']);
const SCORE_FLOOR = 6;        // minimum match score to surface
const TOP_K = 2;              // max suggestions per advisory
const TEXT_FIELD_KEYS = ['command', 'description', 'file_path', 'content', 'old_string', 'new_string', 'prompt'];
const KEYWORD_RE = /[a-zA-Z][a-zA-Z0-9_-]{2,}/g;
const STOP_WORDS = new Set([
  'the', 'and', 'for', 'use', 'this', 'that', 'with', 'your', 'you', 'from',
  'into', 'about', 'when', 'what', 'which', 'will', 'should', 'must', 'have',
  'are', 'all', 'any', 'can', 'see', 'may', 'not', 'but', 'out', 'via', 'per',
]);

function readStdin(timeoutMs) {
  return new Promise(resolve => {
    let buf = '';
    const t = setTimeout(() => resolve(buf), timeoutMs);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', c => { buf += c; });
    process.stdin.on('end', () => { clearTimeout(t); resolve(buf); });
  });
}

function loadHeatMap() {
  try {
    const raw = fs.readFileSync(HEAT_MAP_PATH, 'utf8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function extractTokens(toolInput) {
  if (!toolInput || typeof toolInput !== 'object') return [];
  const parts = [];
  for (const k of TEXT_FIELD_KEYS) {
    const v = toolInput[k];
    if (typeof v === 'string') parts.push(v);
  }
  if (!parts.length) return [];
  const text = parts.join(' ').toLowerCase();
  const tokens = text.match(KEYWORD_RE) || [];
  const seen = new Set();
  const out = [];
  for (const tok of tokens) {
    if (tok.length < 3 || STOP_WORDS.has(tok)) continue;
    if (!seen.has(tok)) { seen.add(tok); out.push(tok); }
  }
  return out;
}

function scoreSkill(tokens, entry) {
  const kws = new Set(entry.keywords || []);
  const desc = (entry.description || '').toLowerCase();
  let score = 0;
  let descHits = 0;
  for (const t of tokens) {
    if (kws.has(t)) score += 5;
    if (desc.includes(t)) { score += 2; descHits++; }
  }
  // require at least one description hit so pure keyword spray is not enough
  return descHits > 0 ? score : 0;
}

function alreadyAdvisedFlagPath(sessionId) {
  return path.join(os.tmpdir(), `claude-skill-advisor-${sessionId}.flag`);
}

function alreadyUsedSkillsPath(sessionId) {
  // Optional cooperation point with other hooks. Silently skipped if absent.
  return path.join(os.tmpdir(), `claude-skills-used-${sessionId}.txt`);
}

function loadAlreadyUsedSkills(sessionId) {
  try {
    const p = alreadyUsedSkillsPath(sessionId);
    if (!fs.existsSync(p)) return new Set();
    const text = fs.readFileSync(p, 'utf8');
    return new Set(text.split(/\r?\n/).map(l => l.trim()).filter(Boolean));
  } catch {
    return new Set();
  }
}

function pickTopK(heatMap, tokens, used) {
  const skills = heatMap.skills || {};
  const ranked = [];
  for (const [sid, entry] of Object.entries(skills)) {
    if (used.has(sid)) continue;
    const sc = scoreSkill(tokens, entry);
    if (sc >= SCORE_FLOOR) ranked.push([sid, sc, entry.description || '']);
  }
  ranked.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  return ranked.slice(0, TOP_K);
}

(async () => {
  // Default fall-through: empty stdout, exit 0.
  let payload = '';
  try { payload = await readStdin(2000); } catch { /* keep empty */ }

  let event = {};
  try { event = JSON.parse(payload || '{}'); } catch { /* keep empty */ }

  const tool = event.tool_name;
  if (!tool || !ELIGIBLE_TOOLS.has(tool)) {
    process.stdout.write('{}');
    return;
  }
  const sessionId = event.session_id;
  if (!sessionId) {
    process.stdout.write('{}');
    return;
  }

  // Per-session debounce
  const flag = alreadyAdvisedFlagPath(sessionId);
  if (fs.existsSync(flag)) {
    process.stdout.write('{}');
    return;
  }

  const tokens = extractTokens(event.tool_input);
  if (!tokens.length) {
    process.stdout.write('{}');
    return;
  }

  const heatMap = loadHeatMap();
  if (!heatMap || !heatMap.skills) {
    process.stdout.write('{}');
    return;
  }

  const used = loadAlreadyUsedSkills(sessionId);
  const top = pickTopK(heatMap, tokens, used);
  if (!top.length) {
    process.stdout.write('{}');
    return;
  }

  const lines = top.map(([sid, score, desc]) => {
    const short = desc.length > 140 ? desc.slice(0, 137) + '...' : desc;
    return `  - ${sid} (score=${score}): ${short}`;
  });
  const message =
    'SKILL ADVISOR (BL-0018, advisory only): based on the keywords in this ' +
    `${tool} input, the following skills may be relevant. Invoke via the Skill ` +
    `tool only if the match looks correct — ignore otherwise.\n${lines.join('\n')}`;

  try { fs.writeFileSync(flag, '1', 'utf8'); } catch { /* best-effort */ }

  const out = {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      additionalContext: message,
    },
  };
  process.stdout.write(JSON.stringify(out));
})();
