/**
 * console-popup-guard — PreToolUse (Bash|PowerShell + Write|Edit|MultiEdit), block:true
 *
 * WHY THIS EXISTS
 * Console windows kept popping up in the foreground on the Owner's desktop. Windows Terminal is
 * the default terminal on this host, so any console process that is NOT handed a hidden window
 * gets a real, focused WT window. Measured 2026-10-15 (both poles, same host):
 *
 *   Invoke-CimMethod Win32_Process Create  (no startup info)        -> 1 visible window
 *   ... + ProcessStartupInformation ShowWindow=0                    -> 0
 *   Start-Process cmd.exe ...              (no window flag)         -> 1
 *   ... -WindowStyle Hidden   /   -NoNewWindow                      -> 0 / 0
 *
 * The live offender was `python receptor-preferencias.py servir`, parent WmiPrvSE.exe, plus
 * neom-portatil.ps1 creating its three bridges through Win32_Process.Create with no startup info
 * (that call is deliberate -- it escapes the scheduled task's job object -- only the window was
 * wrong). A memory already said "hidden launch for scheduled tasks"; it was violated anyway in a
 * new shape, which is the argument for a mechanical gate.
 *
 * WHAT IT BLOCKS
 *   A. Win32_Process Create (Invoke-CimMethod / Invoke-WmiMethod / [wmiclass]) with no ShowWindow
 *      in the same statement neighbourhood.
 *   B. Start-Process / saps of a CONSOLE program or script without -WindowStyle Hidden or
 *      -NoNewWindow. GUI targets (a URL, notepad, an app) are untouched.
 *   C. Registering a scheduled task whose action runs a console program directly (cmd, powershell,
 *      python, node ...) instead of wscript.exe + hidden_launch.vbs or pythonw.exe. S4U tasks run
 *      in session 0 and cannot show a window, so they pass.
 * Shell commands are judged whole. Files (.ps1/.psm1/.bat/.cmd) are judged as a RATCHET: only a
 * violation count that GROWS from the pre-edit file to the post-edit file blocks, so editing an
 * unrelated part of a file with old debt never blocks.
 *
 * Output: stderr reason + stdout { decision:"block", reason } + exit 2 on block; else exit 0.
 * Fail-open absolute. Kill switch: CLAUDE_CONSOLE_POPUP_GUARD=off
 * Tests: node hooks/tests/test-console-popup-guard.js
 */
"use strict";

const fs = require("fs");
const path = require("path");

const CONSOLE_PROG =
  "(?:cmd|powershell|pwsh|python[0-9.]*|py|node|npm|npx|pnpm|yarn|git|java|mvn|gradle|uv|deno|bun|ping|ssh|wsl|bash|conhost|claude|kclaude)";
const CONSOLE_TARGET_RE = new RegExp(
  `^(?:.*[\\\\/])?(?:${CONSOLE_PROG}(?:\\.exe|\\.cmd)?|[^\\\\/]+\\.(?:bat|cmd|ps1|py|js))$`,
  "i"
);
const SCRIPT_EXT_RE = /\.(?:ps1|psm1|bat|cmd)$/i;
const NEIGHBOURHOOD = 600;

function joinContinuations(text) {
  // PowerShell backtick continuations: one logical statement per line afterwards.
  return String(text).replace(/`\r?\n\s*/g, " ");
}

function unquote(tok) {
  return String(tok || "").replace(/^[("'\s]+|[)"'\s,;]+$/g, "");
}

// A. Win32_Process Create without ShowWindow near it.
function wmiCreateViolations(text) {
  const out = [];
  const re = /(?:Invoke-CimMethod|Invoke-WmiMethod|\[wmiclass\])[^\n]{0,200}?Win32_Process[^\n]{0,200}?\bCreate\b|Win32_Process['"]?\)\s*\.Create\s*\(/gi;
  let m;
  while ((m = re.exec(text))) {
    const lo = Math.max(0, m.index - NEIGHBOURHOOD);
    const hi = Math.min(text.length, m.index + m[0].length + NEIGHBOURHOOD);
    if (!/ShowWindow/i.test(text.slice(lo, hi))) out.push(`A:${m[0].slice(0, 80)}`);
  }
  return out;
}

// B. Start-Process of a console program without a hidden/no-new-window flag.
function startProcessViolations(text) {
  const out = [];
  const lines = joinContinuations(text).split(/\r?\n/);
  for (const line of lines) {
    const re = /(?:^|[;|{(&\s"'])(?:Start-Process|saps)\b([^;|\n]*)/gi;
    let m;
    while ((m = re.exec(line))) {
      const seg = m[1];
      if (/-WindowStyle\s+['"]?Hidden/i.test(seg) || /-NoNewWindow\b/i.test(seg)) continue;
      let target = null;
      const fp = seg.match(/-FilePath\s+("[^"]*"|'[^']*'|\S+)/i);
      if (fp) target = fp[1];
      else {
        const pos = seg.replace(/-\w+\s+("[^"]*"|'[^']*'|\S+)/g, " ").trim().match(/^("[^"]*"|'[^']*'|\S+)/);
        if (pos) target = pos[1];
      }
      target = unquote(target);
      if (!target || target.startsWith("$")) continue; // unknown at parse time: never guess
      if (CONSOLE_TARGET_RE.test(target)) out.push(`B:Start-Process ${target}`);
    }
  }
  return out;
}

// C. Scheduled task whose action runs a console program directly.
function scheduledTaskViolations(text) {
  const out = [];
  const flat = joinContinuations(text);
  if (/-LogonType\s+['"]?S4U/i.test(flat)) return out;
  const re = /New-ScheduledTaskAction\b[^\n]*?-Execute\s+("[^"]*"|'[^']*'|\S+)/gi;
  let m;
  while ((m = re.exec(flat))) {
    const exe = unquote(m[1]);
    if (!exe || exe.startsWith("$")) continue;
    if (/wscript|pythonw/i.test(exe)) continue;
    if (CONSOLE_TARGET_RE.test(exe)) out.push(`C:task -Execute ${exe}`);
  }
  const st = /schtasks(?:\.exe)?\s+\/create\b[^\n]*?\/tr\s+("[^"]*"|'[^']*'|\S+)/gi;
  while ((m = st.exec(flat))) {
    const tr = unquote(m[1]);
    if (/wscript|pythonw/i.test(tr)) continue;
    const first = unquote(tr.split(/\s+/)[0]);
    if (CONSOLE_TARGET_RE.test(first)) out.push(`C:schtasks /tr ${first}`);
  }
  return out;
}

function violations(text) {
  if (!text) return [];
  return [...wmiCreateViolations(text), ...startProcessViolations(text), ...scheduledTaskViolations(text)];
}

function readFileSafe(p) {
  try { return fs.readFileSync(p, "utf8"); } catch { return ""; }
}

function postEditText(tool, ti, pre) {
  if (tool === "Write") return String(ti.content || "");
  const edits = tool === "MultiEdit" ? (ti.edits || []) : [ti];
  let text = pre;
  for (const e of edits) {
    const oldS = String(e.old_string || ""), newS = String(e.new_string || "");
    if (!oldS) { text += newS; continue; }
    text = e.replace_all ? text.split(oldS).join(newS) : text.replace(oldS, () => newS);
  }
  return text;
}

function buildReason(found, subject) {
  return [
    "CONSOLE POPUP: this would open a visible console window in the Owner's foreground.",
    "Windows Terminal is the default terminal here; any console process not given a hidden",
    "window becomes a focused WT window (measured 2026-10-15: 1 window without the flag, 0 with).",
    "",
    "Found:",
    ...found.map((f) => `  - ${f}`),
    "",
    "PIVOT (pick the one for your shape):",
    "  A. Win32_Process Create -> add hidden startup info:",
    "     $si = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }",
    "     Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = ...; ProcessStartupInformation = $si }",
    "  B. Start-Process <console prog> -> add -WindowStyle Hidden (detached) or -NoNewWindow (inherit console).",
    "  C. Scheduled task -> -Execute wscript.exe -Argument '//B //Nologo <PP>\\tools\\hidden_launch.vbs <cmd>'",
    "     (or pythonw.exe for Python). -WindowStyle Hidden on powershell.exe still flashes.",
    "",
    "Kill switch: CLAUDE_CONSOLE_POPUP_GUARD=off",
    `Subject: ${String(subject).slice(0, 300)}`,
  ].join("\n");
}

function run(input, opts) {
  try {
    const platform = (opts && opts.platform) || process.platform;
    if (platform !== "win32") return { block: false, why: "not-windows" };
    if (String(process.env.CLAUDE_CONSOLE_POPUP_GUARD || "").toLowerCase() === "off") {
      return { block: false, why: "kill-switch" };
    }
    const tool = input && input.tool_name;
    const ti = (input && input.tool_input) || {};

    if (tool === "Bash" || tool === "PowerShell") {
      const command = String(ti.command || "");
      const found = violations(command);
      if (!found.length) return { block: false, why: "clean-command" };
      return { block: true, why: "command", found, reason: buildReason(found, command) };
    }

    if (tool === "Write" || tool === "Edit" || tool === "MultiEdit") {
      const fp = String(ti.file_path || "");
      if (!SCRIPT_EXT_RE.test(fp)) return { block: false, why: "not-a-script-file" };
      const pre = (opts && typeof opts.preText === "string") ? opts.preText : readFileSafe(fp);
      const post = postEditText(tool, ti, pre);
      const before = violations(pre).length;
      const found = violations(post);
      if (found.length <= before) return { block: false, why: "ratchet-not-grown" };
      return { block: true, why: "file-ratchet", found, reason: buildReason(found, path.basename(fp)) };
    }
    return { block: false, why: "not-a-guarded-tool" };
  } catch (error) {
    return { block: false, why: `guard-error:${error && error.message}` };
  }
}

module.exports = { run, violations };

if (require.main === module) {
  let raw = "";
  const t = setTimeout(() => { process.exit(0); }, 4000);
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (c) => { raw += c; });
  process.stdin.on("end", () => {
    clearTimeout(t);
    let data = {};
    try { data = JSON.parse(String(raw || "{}").replace(/^﻿/, "")); } catch { process.exit(0); }
    const r = run(data);
    if (r.block) {
      try { process.stderr.write(String(r.reason) + "\n"); } catch {}
      try { process.stdout.write(JSON.stringify({ decision: "block", reason: r.reason })); } catch {}
      process.exit(2);
    }
    process.exit(0);
  });
}
