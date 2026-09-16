#!/usr/bin/env node
/**
 * Two-way self-test for the windows-bash-bridge-guard v15 aperture extension.
 *
 * Both branches are DRIVEN, deliberately. Half of these cases must NOT fire,
 * and that half is the half that matters: a gate exercised only where it should
 * trip would pass with every clause commented out and look identical from the
 * outside (~/.claude/rules/instrument-before-claim.md).
 *
 * The BLOCK cases are not invented. Cases 1-3 are the literal commands that
 * hung the CostaLuz Lawyers session on 2026-09-02 and walked past the previous
 * aperture untouched.
 *
 * Run: node ~/.claude/hooks/tests/test-bash-bridge-guard-v15.js
 */
"use strict";

const os = require("os");
const path = require("path");

const GUARD = path.join(os.homedir(), ".claude", "hooks", "windows-bash-bridge-guard.js");
const { run, classifyCommand } = require(GUARD);

const WIN = { platform: "win32" };
const bash = (command) => ({ tool_name: "Bash", tool_input: { command } });

let pass = 0;
let fail = 0;

function ok(gate, evidence) {
  pass++;
  console.log(`  OK   ${gate} — ${evidence}`);
}
function bad(gate, diag) {
  fail++;
  console.log(`  FAIL ${gate} — ${diag}`);
}

function expectBlock(gate, command, expectedCls, expectedToken) {
  const r = run(bash(command), WIN);
  if (!r.block) return bad(gate, `expected BLOCK, got pass (why=${r.why}) for: ${command}`);
  if (expectedCls && r.cls !== expectedCls) return bad(gate, `class ${r.cls} != ${expectedCls}`);
  if (expectedToken && r.token !== expectedToken) return bad(gate, `token '${r.token}' != '${expectedToken}'`);
  if (!r.reason || r.reason.length < 40) return bad(gate, "block carried no usable reason");
  ok(gate, `blocked '${r.token}' as ${r.cls}`);
}

function expectPass(gate, command, opts) {
  const r = run(bash(command), Object.assign({}, WIN, opts || {}));
  if (r.block) return bad(gate, `expected PASS, got BLOCK on '${r.token}' for: ${command}`);
  ok(gate, `allowed (why=${r.why})`);
}

console.log("\n--- RED branch: commands that MUST be blocked ---------------------");

// The three that actually hung the session, verbatim in shape.
expectBlock("V-BBG-HUNG-GREP", `cd "C:/repo" && grep -rn "brain_client" portal/config/`, "V15_READ_TOKEN", "grep");
expectBlock("V-BBG-HUNG-SED", `cd "C:/repo" && sed -n '1,60p' portal/test/foo_test.exs`, "V15_READ_TOKEN", "sed");
expectBlock("V-BBG-HUNG-PYHEREDOC", `cd "C:/repo" && python - <<'PY'\nprint("edit")\nPY`, "MANDATORY_POWERSHELL", "python");

// The original six must still be caught (no regression from the refactor).
expectBlock("V-BBG-GIT", "git status --short", "MANDATORY_POWERSHELL", "git");
expectBlock("V-BBG-NPM", "npm run build", "MANDATORY_POWERSHELL", "npm");

// Newly routed programs CLAUDE.md already called MANDATORY PowerShell.
expectBlock("V-BBG-PYTEST", "pytest brain/tests -q", "MANDATORY_POWERSHELL", "pytest");
expectBlock("V-BBG-UV", "uv pip install -r req.txt", "MANDATORY_POWERSHELL", "uv");

// v15 read tokens, bare.
expectBlock("V-BBG-CAT", "cat portal/mix.exs", "V15_READ_TOKEN", "cat");
expectBlock("V-BBG-TAIL", "tail -100 _logs/run.log", "V15_READ_TOKEN", "tail");
expectBlock("V-BBG-LS", "ls brain/tests", "V15_READ_TOKEN", "ls");

// The chained-pipe shape: the documented dead-screen sentinel.
expectBlock("V-BBG-PIPE", "cat foo.txt | head -5", "V15_READ_TOKEN", "cat");
expectBlock("V-BBG-CHAIN-POS2", 'echo "start" && grep -n pattern file.ex', "V15_READ_TOKEN", "grep");
expectBlock("V-BBG-WC-IN-PIPE", "wc -l a.txt | grep 5", "V15_READ_TOKEN", "wc");

// A path-qualified binary must not launder the token.
expectBlock("V-BBG-ABSPATH", "/usr/bin/grep -r foo .", "V15_READ_TOKEN", "grep");

console.log("\n--- GREEN branch: commands that MUST NOT be blocked ---------------");

// `wc -l file` alone is explicitly sanctioned by CLAUDE.md.
expectPass("V-BBG-WC-SOLO", "wc -l brain/alerts.py");

// POSIX-only scripts are exactly what Bash is for.
expectPass("V-BBG-SH-SCRIPT", "bash scripts/deploy.sh --prod");
expectPass("V-BBG-SH-DIRECT", "./scripts/migrate.sh");

// Quoted content must not create phantom chunks.
expectPass("V-BBG-QUOTED", 'echo "grep and sed are great tools"');
expectPass("V-BBG-QUOTED-SEP", "echo 'a && cat b | head'");

// Heredoc BODY text is payload, not commands.
expectPass("V-BBG-HEREDOC-BODY", "printf '%s' hi <<'EOF'\ngrep this cat that\nEOF");

// Substring false positives: a token is a whole word or nothing.
expectPass("V-BBG-SUBSTRING", "catalog-build --verbose");
expectPass("V-BBG-SUBSTRING2", "findutils_check --dry-run");

// Ordinary commands with no bridge history.
expectPass("V-BBG-MKDIR", "mkdir -p build/out");
expectPass("V-BBG-DOCKER", "docker ps -a");

// A bare `cd` chunk carries no verb.
expectPass("V-BBG-BARE-CD", 'cd "C:/Users/User/Desktop/repo"');

// Escape markers still work — and are logged.
expectPass("V-BBG-ESCAPE", "grep -rn foo . # bash-safe");
expectPass("V-BBG-ESCAPE2", "python x.py --mc-bridge-ok");

// Platform gate: this guard is Windows-only by construction.
expectPass("V-BBG-NON-WINDOWS", "git status", { platform: "linux" });

// Kill switch.
process.env.CLAUDE_BASH_GUARD = "off";
expectPass("V-BBG-KILLSWITCH", "grep -rn foo .");
delete process.env.CLAUDE_BASH_GUARD;

// Fail-open on garbage input.
const garbage = run({ tool_name: "Bash", tool_input: null }, WIN);
if (garbage.block) bad("V-BBG-FAILOPEN", "blocked on malformed input");
else ok("V-BBG-FAILOPEN", `fail-open held (why=${garbage.why})`);

// classifyCommand is pure and returns null for clean input.
if (classifyCommand("mkdir -p x") !== null) bad("V-BBG-PURE", "classifyCommand mislabelled a clean command");
else ok("V-BBG-PURE", "classifyCommand returns null on clean input");

console.log(`\nBBG_PASS=${pass}/${pass + fail}  threshold=${pass + fail}/${pass + fail}`);
process.exit(fail === 0 ? 0 : 1);
