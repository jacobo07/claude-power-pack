#!/usr/bin/env node
// PreToolUse (Bash|PowerShell) -- the concurrent-writers COMMIT card (PLAN-SKILL-RESIDENCY C4).
//
// WHY THIS EXISTS. The rule `concurrent-writers-shared-tree` left the prefix on 2026-10-03 (Move 4).
// A two-sided delivery test then measured 6/6 runs committing an unlabeled foreign hunk at the commit:
// with the pointer only, with the FULL rule body resident, and with the paged skill (invoked 0/2,
// listed without its description). A natural production commit at 10:27 did the same with the rule
// resident. Neither residency nor model-judged paging delivers this behaviour, so its hard part has
// to reach the moment of use by an EVENT: the commit itself (R2 plan evidence log, results-delivery*).
//
// WHAT IT DOES. On a shell command that commits, it works out what the commit will contain, reads which
// lines THIS session wrote (Edit/Write/MultiEdit/NotebookEdit inputs and structuredPatch results, in the
// session transcript and its subagents/), and counts the lines it did not write: an OPPORTUNITY.
//   CLAUDE_DOCTRINE_CARDS=ledger (default)  record only; the commit runs. A ledger row is NOT delivery.
//   CLAUDE_DOCTRINE_CARDS=deny              first time a given foreign set is seen: deny with the card
//                                           listing each foreign hunk; re-issuing the same commit passes.
//   CLAUDE_DOCTRINE_CARDS=off               nothing at all.
// Unknown is a first-class answer, never "no opportunity": a commit form it cannot plan (--amend,
// --pathspec-from-file, GIT_INDEX_FILE, an unresolved variable), a git timeout, or a file the session
// wrote through the shell (its lines are invisible to the transcript) is recorded as unknown.
//
// WINDOW RULE (skill-capability pillar A, D-01). A file with foreign hunks is ALSO recorded as unknown
// (reason `mtime-in-own-shell-window`, listed in the ledger row's `unknown_reasons`) when its current mtime
// lies inside one of THIS session's shell tool-call windows [tool_use row timestamp, tool_result row
// timestamp] (1 s slack for fs/clock granularity) AND after this session's last Edit/Write/MultiEdit/
// NotebookEdit of that file. Measured cause: a tool-mediated write by the session's own script or
// formatter (gsd-tools, oxfmt, a census script) is invisible to the line ledger and read as foreign
// (5 false denies, 0 true positives). A missing file or stat, a transcript row without a timestamp, an
// unfinished shell call (no result row) and a failed toplevel lookup yield no window: the file stays
// foreign, i.e. the failure goes toward the card, which asks once and is never an authority.
//
// APERTURE. Untracked files staged by `git add -A` in the same command are not checked; aliases and
// commits made inside scripts are not seen; peers can stage between this check and the commit (TOCTOU).
// Ownership is by exact trimmed line text, so a foreign line identical to one this session wrote reads
// as own, and lines of 1-2 characters (braces) are not judged. Window rule aperture, stated and not hidden:
// a peer writing the same file during one of this session's shell windows reads as unknown; a file this
// session's shell touched after a pre-session foreign edit reads as unknown; pre-session foreign hunks whose
// mtime precedes every shell window stay foreign; a rollover-resumed session committing lines its
// predecessor wrote (mtime = its own Edit, not a shell window) stays foreign. Ownership is by lowercased
// basename, so two files with one basename in different directories share an edit time.
//
// COST. Returns before ANY I/O unless the command matches the commit pattern (every shell call in every
// pane pays this hook). One bounded git spawn (2.5 s), plus one more bounded `rev-parse --show-toplevel`
// ONLY on the foreign-with-windows path. Pure node: no python on the hook path.
// State: DOCTRINE_CARDS_STATE_DIR (tests, benchmarks) or ~/.claude/state/doctrine-cards/.
'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');

const STATE_DIR = process.env.DOCTRINE_CARDS_STATE_DIR
  || path.join(os.homedir(), '.claude', 'state', 'doctrine-cards');
const MODE = (process.env.CLAUDE_DOCTRINE_CARDS || 'ledger').toLowerCase();
const GIT_TIMEOUT_MS = 2500;
const GIT_FALLBACK = 'C:\\Program Files\\Git\\cmd\\git.exe';
// git is a literal or a PowerShell variable holding its path (`& $g -C $r commit`).
const GITCMD = String.raw`(?:\bgit(?:\.exe)?['"]?|\$\w+)(?:\s+-C\s+(?:'[^']*'|"[^"]*"|\S+))?\s+`;
const COMMIT_RE = new RegExp(GITCMD + String.raw`commit(?![\w-])`);
const ADD_RE = new RegExp(GITCMD + String.raw`add(?![\w-])([^;\n|&]*)`);
// A shell command WRITES a file only when a write operator's TARGET is that file. Measured 2026-10-03
// (arm C, both runs): "any `>` + the command mentions the basename" flagged the judged commit itself
// (its message ended `<noreply@anthropic.com>`, and `test_pricing.py` contains `pricing.py`), so the
// card called its own subject unknowable, failed open, and the swallow went through.
const WRITE_TARGETS = [
  /(?:^|[^\d&*\w-])>>?[ \t]*(?!&)['"]?([^\s'";|&<>()]+)/g,                       // > f, >> f (not 2>&1)
  /\b(?:Set-Content|Add-Content|Out-File)\b(?:\s+-(?:Literal)?(?:File)?Path)?\s+['"]?([^\s'";|]+)/gi,
  /\b(?:WriteAllText|AppendAllText|WriteAllLines|AppendAllLines)\(\s*['"]?([^'",)]+)/g,
  /\bsed\s+-i\S*\s+(?:'[^']*'|"[^"]*"|\S+)\s+['"]?([^\s'";|]+)/g,
  /\bopen\(\s*r?['"]([^'"]+)['"]\s*,\s*['"][wa]/g,
  /\bPath\(\s*r?['"]([^'"]+)['"]\s*\)\.write_(?:text|bytes)\(/g,
];
function shellTargets(command) {
  const out = new Set(); const cmd = elideLiteralBodies(command);
  for (const re of WRITE_TARGETS) for (const m of cmd.matchAll(re)) {
    const b = path.basename(m[1].replace(/\\/g, '/')).toLowerCase();
    if (b && b !== '$null' && b !== 'null') out.add(b);
  }
  return out;
}
const VALUE_FLAGS = new Set(['-m', '--message', '-F', '--file', '-c', '-C', '--reuse-message', '--reedit-message',
  '--author', '--date', '--cleanup', '--fixup', '--squash', '-t', '--template', '--trailer']);

function elideLiteralBodies(cmd) {
  return cmd
    .replace(/@(['"])[\s\S]*?\1@/g, "'<here-string>'")
    .replace(/<<-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1[\s\S]*?^[ \t]*\2[ \t]*$/gm, '<<HEREDOC');
}

function ledger(rec) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.appendFileSync(path.join(STATE_DIR, 'ledger.jsonl'), JSON.stringify({
      ts: new Date().toISOString(), card: 'commit', mode: MODE,
      source: process.env.CLAUDE_CODE_ENTRYPOINT || 'unknown', ...rec,
    }) + '\n');
  } catch (_) { /* a receipt failure must not change the verdict */ }
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj));
  process.exit(0);
}

function tokens(s) {
  const out = [];
  const re = /'([^']*)'|"([^"]*)"|(\S+)/g;
  let m;
  while ((m = re.exec(s))) out.push(m[1] ?? m[2] ?? m[3]);
  return out;
}

// Variables a commit can rely on (audit G1-G3, 2026-10-03). `text` is the here-string-elided command
// BEFORE the commit. A variable resolves only when it is assigned exactly once, at brace depth 0, by `=`,
// to a literal, a comma list of literals or @(literals) that ENDS at `;`, a newline or the end. Anything
// else -- reassigned, `+=`, inside a block, concatenated, a method call, a pipeline -- maps to null, so it
// stays unknown instead of being half-resolved (`$p='a','b'` used to bind 'a' alone and judge b unseen).
function psVars(text) {
  const seen = {};
  const re = /\$(\w+)\s*(\+?=)(?!=)/g;
  let m;
  while ((m = re.exec(text))) {
    const name = m[1].toLowerCase();
    const prefix = text.slice(0, m.index);
    const depth = (prefix.match(/\{/g) || []).length - (prefix.match(/\}/g) || []).length;
    const value = m[2] === '=' && depth === 0 ? literalValue(text.slice(re.lastIndex), seen) : null;
    seen[name] = name in seen ? null : value;   // a second assignment makes the value unknowable
  }
  return seen;
}

function literalValue(rest, vars) {
  let s = rest.replace(/^[ \t]*/, '');
  const array = s.startsWith('@(');
  if (array) s = s.slice(2);
  const out = [];
  for (;;) {
    s = s.replace(array ? /^\s*/ : /^[ \t]*/, '');
    const m = /^'([^']*)'|^"([^"]*)"/.exec(s);
    if (!m) return null;
    const v = m[1] != null ? m[1] : expand(m[2], vars);
    if (v == null) return null;
    out.push(v);
    s = s.slice(m[0].length).replace(array ? /^\s*/ : /^[ \t]*/, '');
    if (s.startsWith(',')) { s = s.slice(1); continue; }
    if (array) { if (!s.startsWith(')')) return null; s = s.slice(1).replace(/^[ \t]*/, ''); }
    return /^(?:;|\r?\n|$)/.test(s) ? out : null;
  }
}

// "$d/x" with $d a single literal; $env:, $(...) and lists stay unknown.
function expand(str, vars) {
  if (/\$\(|\$\{|\$env:/i.test(str)) return null;
  let ok = true;
  const v = str.replace(/\$(\w+)/g, (_, n) => {
    const val = vars[n.toLowerCase()];
    if (!val || val.length !== 1) { ok = false; return ''; }
    return val[0];
  });
  return ok ? v : null;
}

// A token resolves to a list of literal values, or null when it cannot be known.
function resolve(tok, vars) {
  if (tok == null) return null;
  const m = /^[$@](\w+)$/.exec(tok);          // `$p`, or `@p` = PowerShell splatting of the array $p
  if (m) return vars[m[1].toLowerCase()] || null;
  if (!tok.includes('$')) return [tok];
  const v = expand(tok, vars);
  return v == null ? null : [v];
}

// Redirections are not pathspecs: `2>$null`, `2>&1`, `>out.txt`, `*> log`, `> out.txt` (audit G4).
function dropRedirects(t) {
  const out = [];
  for (let i = 0; i < t.length; i++) {
    if (/^(?:\d|\*)?>>?(?:&\d)?$/.test(t[i])) { if (!/&\d$/.test(t[i])) i++; continue; }
    if (/^(?:\d|\*)?>>?\S/.test(t[i])) continue;
    out.push(t[i]);
  }
  return out;
}

// What will this commit contain? Returns {repo, args} for one `git diff`, or {unknown: reason}.
function plan(command, cwd) {
  const cmd = elideLiteralBodies(command);
  if (/\bGIT_INDEX_FILE\b/.test(cmd)) return { unknown: 'GIT_INDEX_FILE' };
  const cm = COMMIT_RE.exec(cmd);
  const before = cmd.slice(0, cm.index);
  const vars = psVars(before);   // only what is bound before the commit runs (G2), here-strings elided (G3)
  const seg = cmd.slice(cm.index).split(/;|&&|\|\||\||\n/)[0];
  // Repository: -C on the commit, else the last cd/Set-Location before it, else the hook's cwd.
  const one = (tok) => { const v = resolve(tok, vars); return v && v.length === 1 ? v[0] : null; };
  let repo = cwd;
  const cl = [...before.matchAll(/(?:\bSet-Location|\bcd|\bPush-Location)\s+(?:-(?:Literal)?Path\s+)?('[^']*'|"[^"]*"|[^\s;]+)/gi)].pop();
  if (cl) repo = one(tokens(cl[1])[0]);
  const cflag = /\s-C\s+('[^']*'|"[^"]*"|\S+)/.exec(seg);
  if (cflag) repo = one(tokens(cflag[1])[0]);
  if (!repo) return { unknown: 'repository path is an unresolved variable' };
  const t = dropRedirects(tokens(seg.replace(/^[\s\S]*?commit/, '')));
  let all = false; const paths = [];
  for (let i = 0; i < t.length; i++) {
    const a = t[i];
    if (a === '--amend' || a.startsWith('--pathspec-from-file') || a === '-i' || a === '--include'
        || a === '--interactive' || a === '-p' || a === '--patch') return { unknown: `commit ${a}` };
    if (a === '--') { paths.push(...t.slice(i + 1)); break; }
    if (VALUE_FLAGS.has(a)) { i++; continue; }
    if (a === '-a' || a === '--all') { all = true; continue; }
    if (/^-[a-zA-Z]+$/.test(a)) {          // short cluster: -am "msg", -aF file
      if (a.includes('a')) all = true;
      if (/[mFcCt]$/.test(a)) i++;
      continue;
    }
    if (a.startsWith('-')) continue;
    paths.push(a);
  }
  const rv = paths.map((p) => resolve(p, vars));
  if (rv.some((p) => p == null)) return { unknown: 'pathspec is an unresolved variable' };
  const rp = rv.flat();
  // A commit pathspec commits exactly those paths' working-tree state (--only), whatever was added before
  // it: judge the pathspec. `git add X; git commit -- Y` used to diff X and never look at Y.
  if (rp.length) return { repo, args: ['diff', 'HEAD', '--', ...rp], basis: 'only-paths' };
  const adds = [...before.matchAll(new RegExp(ADD_RE.source, 'g'))];   // every `git add` before it (G4)
  if (adds.length) {                       // `git add X; git commit` in ONE call: nothing staged yet
    const each = adds.map((a) => dropRedirects(tokens(a[1])).filter((x) => !x.startsWith('-') || x === '-A' || x === '--all'));
    const addAll = each.some((at) => at.length === 0 || at.some((x) => x === '-A' || x === '--all' || x === '.'));
    const av = addAll ? [] : each.flat().map((p) => resolve(p, vars));
    if (av.some((p) => p == null)) return { unknown: 'add pathspec is an unresolved variable' };
    const ap = av.flat();
    return { repo, args: ['diff', 'HEAD', ...(ap.length ? ['--', ...ap] : [])], basis: 'add-then-commit', aperture: 'untracked not checked' };
  }
  if (all) return { repo, args: ['diff', 'HEAD'], basis: 'all-tracked' };
  return { repo, args: ['diff', '--cached'], basis: 'index' };
}

function spawnGit(full) {
  let r = spawnSync('git', full, { encoding: 'utf8', timeout: GIT_TIMEOUT_MS, windowsHide: true });
  if (r.error && r.error.code === 'ENOENT' && fs.existsSync(GIT_FALLBACK)) {
    r = spawnSync(GIT_FALLBACK, full, { encoding: 'utf8', timeout: GIT_TIMEOUT_MS, windowsHide: true });
  }
  return r;
}

function git(repo, args) {
  return spawnGit(['--no-optional-locks', '-C', repo, ...args, '-U0', '--no-color', '--no-ext-diff']);
}

function parseDiff(out) {
  const files = [];
  let cur = null; let hunk = null;
  for (const line of out.split('\n')) {
    if (line.startsWith('diff --git ')) { cur = { file: null, hunks: [] }; files.push(cur); continue; }
    if (!cur) continue;
    if (line.startsWith('+++ ')) { cur.file = line.slice(4).replace(/^b\//, '').trim(); continue; }
    if (line.startsWith('--- ')) { if (!cur.file) cur.from = line.slice(4).replace(/^a\//, '').trim(); continue; }
    if (line.startsWith('@@')) { hunk = { header: line.replace(/^(@@[^@]*@@).*$/, '$1'), added: [], removed: [] }; cur.hunks.push(hunk); continue; }
    if (!hunk) continue;
    if (line.startsWith('+')) hunk.added.push(line.slice(1));
    else if (line.startsWith('-')) hunk.removed.push(line.slice(1));
  }
  for (const f of files) if (f.file === '/dev/null') f.file = f.from;
  return files.filter((f) => f.file);
}

// Lines this session wrote, from its own transcript and its subagents' transcripts.
function ownership(transcriptPath) {
  const added = new Set(); const removed = new Set(); const whole = new Set(); const shell = new Set();
  // Window provenance (D-01): tool_use id -> {kind, base, start, end}, filled from tool_use rows and closed
  // by the tool_result row carrying the same id. A row without a timestamp gives NaN and contributes nothing.
  const calls = new Map();
  const files = [];
  if (transcriptPath && fs.existsSync(transcriptPath)) {
    files.push(transcriptPath);
    const sub = path.join(transcriptPath.replace(/\.jsonl$/i, ''), 'subagents');
    try { for (const f of fs.readdirSync(sub)) if (f.endsWith('.jsonl')) files.push(path.join(sub, f)); } catch (_) { /* none */ }
  }
  const addLines = (set, text) => { for (const l of String(text || '').split('\n')) { const s = l.trim(); if (s.length > 2) set.add(s); } };
  for (const f of files) {
    let raw;
    try { raw = fs.readFileSync(f, 'utf8'); } catch (_) { continue; }
    for (const line of raw.split('\n')) {
      const usesTool = /"(?:Edit|Write|MultiEdit|NotebookEdit|Bash|PowerShell)"|structuredPatch/.test(line);
      // A result line is parsed only when it closes a call we are tracking (no JSON.parse of every result).
      const closesCall = !usesTool && line.includes('"tool_result"')
        && [...line.matchAll(/"tool_use_id"\s*:\s*"([^"]+)"/g)].some((m) => calls.has(m[1]));
      if (!usesTool && !closesCall) continue;
      let d;
      try { d = JSON.parse(line); } catch (_) { continue; }
      const rowTs = Date.parse(d.timestamp);
      for (const b of ((d.message || {}).content || [])) {
        if (b && b.type === 'tool_result' && calls.has(b.tool_use_id)) { calls.get(b.tool_use_id).end = rowTs; continue; }
        if (!b || b.type !== 'tool_use') continue;
        const i = b.input || {};
        if (b.name === 'Bash' || b.name === 'PowerShell') calls.set(b.id, { kind: 'shell', start: rowTs, end: NaN });
        else if (EDIT_TOOLS.has(b.name)) {
          const fp = String(i.file_path || i.notebook_path || '').replace(/\\/g, '/');
          calls.set(b.id, { kind: 'edit', base: path.basename(fp).toLowerCase(), start: rowTs, end: NaN });
        }
        if (b.name === 'Edit') { addLines(added, i.new_string); addLines(removed, i.old_string); }
        else if (b.name === 'Write') { addLines(added, i.content); if (i.file_path) whole.add(path.basename(i.file_path).toLowerCase()); }
        else if (b.name === 'MultiEdit') for (const e of (i.edits || [])) { addLines(added, e.new_string); addLines(removed, e.old_string); }
        else if (b.name === 'NotebookEdit') addLines(added, i.new_source);
        else if (b.name === 'Bash' || b.name === 'PowerShell') for (const t of shellTargets(String(i.command || ''))) shell.add(t);
      }
      const sp = (d.toolUseResult || {}).structuredPatch;
      if (Array.isArray(sp)) for (const h of sp) for (const l of (h.lines || [])) {
        const s = String(l).slice(1).trim();
        if (s.length <= 2) continue;
        if (l[0] === '+') added.add(s); else if (l[0] === '-') removed.add(s);
      }
    }
  }
  const windows = []; const lastOwnEdit = new Map();
  for (const c of calls.values()) {
    if (c.kind === 'shell') { if (Number.isFinite(c.start) && Number.isFinite(c.end)) windows.push({ start: c.start, end: c.end }); continue; }
    const t = Number.isFinite(c.end) ? c.end : c.start;
    if (c.base && Number.isFinite(t) && !(lastOwnEdit.get(c.base) >= t)) lastOwnEdit.set(c.base, t);
  }
  return { added, removed, whole, shell, windows, lastOwnEdit, read: files.length };
}

const EDIT_TOOLS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit']);
const WINDOW_SLACK_MS = 1000;

// The window rule, in ONE declaration (the replay gate's mutant replaces exactly this body).
function ownShellWindowHit(m, base, own) {
  if (!Number.isFinite(m) || !own || !own.windows) return false;
  if (!own.windows.some((w) => w.start - WINDOW_SLACK_MS <= m && m <= w.end + WINDOW_SLACK_MS)) return false;
  return m > (own.lastOwnEdit && own.lastOwnEdit.has(base) ? own.lastOwnEdit.get(base) : -Infinity);
}

function judge(diff, own, mtimeOf) {
  const foreign = []; const unknown = []; const unknownReasons = {};
  for (const f of diff) {
    const base = path.basename(f.file).toLowerCase();
    if (own.shell.has(base)) { unknown.push(f.file); unknownReasons[f.file] = 'shell-write-target'; continue; }
    const hunks = [];
    for (const h of f.hunks) {
      const fa = h.added.filter((l) => l.trim().length > 2 && !own.added.has(l.trim()));
      const fr = own.whole.has(base) ? [] : h.removed.filter((l) => l.trim().length > 2 && !own.removed.has(l.trim()));
      if (fa.length || fr.length) hunks.push({ header: h.header, added: fa.length, removed: fr.length, sample: (fa[0] || fr[0]).trim().slice(0, 80) });
    }
    if (!hunks.length) continue;
    // mtimeOf is optional (judge stays pure for callers without a filesystem) and is only asked about a file
    // that already has foreign hunks, and only when this session has at least one closed shell window.
    if (typeof mtimeOf === 'function' && own.windows && own.windows.length && ownShellWindowHit(mtimeOf(f.file), base, own)) {
      unknown.push(f.file); unknownReasons[f.file] = 'mtime-in-own-shell-window'; continue;
    }
    foreign.push({ file: f.file, hunks });
  }
  return { foreign, unknown, unknownReasons };
}

function card(foreign) {
  const lines = ['concurrent-writers -- this commit was NOT run. It would include lines this session did not write:'];
  for (const f of foreign.slice(0, 8)) for (const h of f.hunks.slice(0, 4)) {
    lines.push(`  ${f.file} ${h.header}  +${h.added}/-${h.removed}  e.g. "${h.sample}"`);
  }
  lines.push(
    'A pathspec names a FILE, not your hunks: if another session (or a person) is writing in the same file,',
    'committing it takes their work under your message. For each hunk above: is it yours?',
    '- Not yours: commit only your own lines (build a patch of your hunks and stage it with `git apply --cached`),',
    '  and leave the other lines uncommitted and untouched. Never stash, reset or checkout them away.',
    '- Yours (written through a shell command or a tool this check cannot see): re-issue the same commit;',
    '  it will not be stopped again.',
    'Full rule: the `concurrent-writers-shared-tree` skill. Do NOT end the turn here: say what you do next.',
  );
  return lines.join('\n');
}

async function main() {
  if (MODE === 'off') return emit({ continue: true });
  let payload = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const chunk of process.stdin) payload += chunk;
  } catch (_) { return emit({ continue: true }); }
  if (payload.charCodeAt(0) === 0xFEFF) payload = payload.slice(1);
  let req;
  try { req = JSON.parse(payload); } catch (_) { return emit({ continue: true }); }
  if (!['Bash', 'PowerShell'].includes(req.tool_name || '')) return emit({ continue: true });
  const command = String((req.tool_input || {}).command || '');
  if (!COMMIT_RE.test(elideLiteralBodies(command))) return emit({ continue: true });   // no I/O before this

  const session = String(req.session_id || 'unknown').replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 80);
  const p = plan(command, req.cwd || process.cwd());
  if (p.unknown) { ledger({ decision: 'unknown', session, reason: p.unknown }); return emit({ continue: true }); }
  const r = git(p.repo, p.args);
  if (r.error || r.status !== 0) {
    ledger({ decision: r.error && r.error.code === 'ETIMEDOUT' ? 'timeout' : 'unknown', session, basis: p.basis,
      reason: r.error ? r.error.code : `git exit ${r.status}` });
    return emit({ continue: true });
  }
  const own = ownership(req.transcript_path);
  if (!own.read) { ledger({ decision: 'unknown', session, basis: p.basis, reason: 'transcript unreadable' }); return emit({ continue: true }); }
  // mtime of a diffed file: one bounded toplevel lookup, made lazily (only for a foreign-with-windows file).
  let top;
  const mtimeOf = (file) => {
    if (top === undefined) {
      const t = spawnGit(['--no-optional-locks', '-C', p.repo, 'rev-parse', '--show-toplevel']);
      top = !t.error && t.status === 0 && (t.stdout || '').trim() ? (t.stdout || '').trim() : null;
    }
    if (!top) return null;
    try { return fs.statSync(path.join(top, file)).mtimeMs; } catch (_) { return null; }
  };
  const { foreign, unknown, unknownReasons } = judge(parseDiff(r.stdout || ''), own, mtimeOf);
  const rec = { session, basis: p.basis, aperture: p.aperture, unknown_files: unknown, unknown_reasons: unknownReasons,
    foreign: foreign.map((f) => ({ file: f.file, hunks: f.hunks.map((h) => h.header) })) };
  if (!foreign.length) { ledger({ decision: unknown.length ? 'unknown' : 'no_opportunity', ...rec }); return emit({ continue: true }); }
  if (MODE !== 'deny') { ledger({ decision: 'opportunity', ...rec }); return emit({ continue: true }); }

  const key = crypto.createHash('sha1').update(JSON.stringify([p.repo, rec.foreign])).digest('hex').slice(0, 12);
  const flag = path.join(STATE_DIR, `shown-commit-${session}-${key}`);
  if (fs.existsSync(flag)) { ledger({ decision: 'pass-after-card', ...rec }); return emit({ continue: true }); }
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
    fs.writeFileSync(flag, new Date().toISOString());
  } catch (_) {
    ledger({ decision: 'pass-unrecordable', ...rec });   // denying now would deny forever
    return emit({ continue: true });
  }
  ledger({ decision: 'deny-card', ...rec });
  return emit({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny',
    permissionDecisionReason: card(foreign) } });
}

if (require.main === module) main().catch(() => emit({ continue: true }));
module.exports = { plan, parseDiff, judge, ownership, COMMIT_RE };
