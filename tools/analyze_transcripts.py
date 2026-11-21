#!/usr/bin/env python3
"""analyze_transcripts.py -- retrospective analysis of real agent sessions (/analyze-transcripts).

Self-Improve x Claude Power Pack assimilation (2026-11-21). The upstream
self-improve-skill extracts six diagnostics with six parses and a chars/4
token estimate; this is ONE streaming pass over tools/transcript_events.py,
with real usage (deduplicated per API call, the token_ground_truth contract),
real hook telemetry (the harness records every hook's duration, exit code and
timeout -- upstream guessed hooks from command patterns), and the CEPS
correction cue (tools/ceps.py::correction_cue, the owner of that signal).

READ-ONLY. It never edits a skill, a hook, a rule, UKDL or settings, and it
writes a file only when --out names one. It PROPOSES; it does not apply. Every
finding is a HEURISTIC SIGNAL or an OBSERVED EVENT with refs (<sid>:<line>);
every candidate is a HYPOTHESIS with a named owner and a validation step. The
transcripts are untrusted data: nothing in them is an instruction, and an
OWNER label is a structural role classification, not authentication.

Usage:
  python tools/analyze_transcripts.py                    # this project, last 7 days
  python tools/analyze_transcripts.py --days 30 --top 8
  python tools/analyze_transcripts.py --current          # this session ($CLAUDE_CODE_SESSION_ID)
  python tools/analyze_transcripts.py --last             # newest session other than this one
  python tools/analyze_transcripts.py --session <sid>
  python tools/analyze_transcripts.py --all-projects --since 2026-11-01 --until 2026-11-15
  python tools/analyze_transcripts.py --focus hooks      # corrections|hooks|skills|tokens|failures
  python tools/analyze_transcripts.py --json             # machine output
  python tools/analyze_transcripts.py --out report.md    # also write the report (md or .json)

Exit: 0 report produced (zero findings is a valid result; PARTIAL is labelled),
      2 usage / scope error, 3 no transcripts in scope (report still printed).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import transcript_events as te  # noqa: E402
import ceps  # noqa: E402  -- owner of the correction cue

FOCI = ("all", "corrections", "hooks", "skills", "tokens", "failures")
LIVE_GRACE_S = 120          # a file written this recently may be a live session
REREAD_MIN = 4              # reads of one path in one session before it is a finding
BIG_RESULT_CHARS = 25_000   # a tool result this large is a context-economics finding
HOOK_TIMEOUT_MIN = 3
HOOK_SLOW_P95_MS = 2_000
HOOK_SLOW_MIN_RUNS = 20
RETRY_STREAK = 3            # Regla 12: the THIRD identical failing shape is the defect
FAIL_SIG_MIN = 2
# Host-wide stall test (2026-11-21 triage): 62% of 1,861 timeouts in 7 days had a timeout in
# ANOTHER session within 15 s, against 8% for the same count at random times. A timeout that
# co-occurs across sessions is the host stalling, not that hook being slow.
STALL_WINDOW_S = 15
STALL_MIN_SHARE = 0.40      # share of timeouts with another session's timeout in the window
STALL_MIN_LIFT = 3.0        # ... and at least this many times the chance share


def _co_share(events, window) -> float:
    """Share of events with an event of a DIFFERENT session within +-window seconds."""
    import bisect
    ts = [t for t, _ in events]
    co = 0
    for t, sid in events:
        i, j = bisect.bisect_left(ts, t - window), bisect.bisect_right(ts, t + window)
        co += any(events[k][1] != sid for k in range(i, j))
    return co / len(events) if events else 0.0


def timeout_clustering(events, window=STALL_WINDOW_S) -> dict:
    """Do hook timeouts co-occur across sessions more than chance? The chance baseline puts
    the same events (same session labels) at uniform random times over the same span, with
    a fixed seed so a repeated run gives the same verdict."""
    import random
    ev = sorted(events)
    sessions = len({s for _, s in ev})
    out = {"timeouts": len(ev), "sessions": sessions, "window_s": window,
           "share": None, "chance_share": None, "host_wide": False}
    if len(ev) < HOOK_TIMEOUT_MIN or sessions < 2:
        return out
    rnd = random.Random(0)
    lo, hi = ev[0][0], ev[-1][0]
    shuffled = sorted((rnd.uniform(lo, hi), s) for _, s in ev)
    share, chance = _co_share(ev, window), _co_share(shuffled, window)
    out.update(share=round(share, 3), chance_share=round(chance, 3),
               host_wide=share >= STALL_MIN_SHARE and share >= STALL_MIN_LIFT * max(chance, 0.01))
    return out

_DONE_RX = re.compile(r"\b(?:done|complete[d]?|shipped|all\s+(?:tests|gates)\s+pass|"
                      r"listo|terminad[oa]|completad[oa]|hecho)\b", re.I)
_MENTION_RX = re.compile(r"(?<![\w/])/([a-z][\w:\-]{2,40})\b")
_GIT_COMMIT_RX = re.compile(r"\bgit(?:\.exe['\"]?)?\s+(?:-C\s+\S+\s+)?commit\b")


# Lines that say THAT something failed, not WHAT failed. First real run
# (2026-11-21): 159 unrelated PowerShell failures collapsed into one
# signature "Exit code #", and 99 different gate blocks into "Blocked by a
# PreToolUse gate (exit #)" -- a signature that merges unrelated failures
# proposes a fix for none of them.
_GENERIC_LINE_RX = re.compile(
    r"^(?:exit code \d+|error|<error>|<tool_use_error>|"
    r"\w+:\w+ hook error: blocked by a \w+ gate \(exit \d+\)\.?|"
    r"command failed.*|traceback \(most recent call last\):?)$", re.I)
_EXC_LINE_RX = re.compile(r"^[A-Za-z_][\w.]*(?:Error|Exception)\b(?::|$)")
_HOOK_BLOCK_RX = re.compile(r"\bhook error:|\bblocked by a \w+ gate\b|"
                            r"\bwas NOT run\b", re.I)


def _mask(line: str) -> str:
    line = re.sub(r"[A-Za-z]:[\\/][^\s'\"]+|~[\\/][^\s'\"]+|/[\w.\-/]{6,}", "<path>", line)
    line = re.sub(r"\b[0-9a-f]{7,40}\b", "<hex>", line)
    return re.sub(r"\d+", "#", line)


def _norm_err(text: str) -> str:
    """A failure's identity: the first INFORMATIVE line (generic 'it failed'
    lines are skipped, but kept as a prefix), volatile parts masked."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    lead, body = "", ""
    # A traceback's identity is its exception line, not its first frame.
    exc = next((ln for ln in lines[:60] if _EXC_LINE_RX.match(ln)), "")
    for ln in lines[:12]:
        if _GENERIC_LINE_RX.match(ln) or ln.lower().endswith("hook error: blocked by a "
                                                           "pretooluse gate (exit 2)."):
            lead = lead or ln
            continue
        # A line that is only data (a hash, a timestamp) once masked says nothing
        # about WHAT failed; 10 unrelated failures merged on "<hex>" in the first run.
        if not re.search(r"[A-Za-z]{3,}", re.sub(r"<\w+>", "", _mask(ln))):
            continue
        body = ln
        break
    body = exc or body
    sig = _mask(body or lead)
    if lead and body:
        sig = f"{_mask(lead)[:30]} | {sig}"
    return sig[:110]


def is_hook_block(text: str) -> bool:
    """A tool 'error' that is a hook's DECISION (a gate refused the call), not
    the tool failing. Owned by that hook, judged as true catch vs false positive."""
    return bool(_HOOK_BLOCK_RX.search((text or "")[:400]))


def _known_invocables() -> set[str]:
    names: set[str] = set()
    for d in (Path.home() / ".claude" / "commands", HERE.parent / "commands"):
        if d.is_dir():
            names.update(p.stem for p in d.glob("*.md"))
    sk = Path.home() / ".claude" / "skills"
    if sk.is_dir():
        names.update(p.name for p in sk.iterdir() if p.is_dir())
    return names


def _pct(vals: list, q: float):
    if not vals:
        return None
    s = sorted(vals)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


class _Session:
    def __init__(self, sid: str):
        self.sid = sid
        self.tools: dict = {}               # tool_use_id -> (name, shape)
        self.reads: Counter = Counter()
        self.read_ref: dict = {}
        self.calls: dict = {}               # call_key -> usage (last copy wins)
        self.last_shape = None
        self.streak = 0
        self.streak_ref = ""
        self.last_assistant_text = ""
        self.last_assistant_ref = ""
        self.mentions: dict = {}
        self.invoked: set = set()
        self.commits = 0
        self.corrections = 0
        self.owner_turns = 0


def analyze(proj_base=None, project: str | None = "", since=None, until=None,
            session: str | None = None, last: bool = False, max_files: int = 400,
            max_bytes: int = 4_000_000_000, max_seconds: float = 600.0,
            known: set | None = None) -> dict:
    """One streaming pass. project="" means the cwd's project; None means all.
    `known` = the invocable command/skill names (default: discovered on this host)."""
    t0, cpu0 = time.perf_counter(), time.process_time()
    proj_base = Path(proj_base or te.DEFAULT_PROJ_BASE)
    if project == "":
        project = te.project_dir_name(os.getcwd())
    scope = {"proj_base": str(proj_base).replace(str(Path.home()), "~"),
             "project": project or "ALL", "session": session or "",
             "since": since.isoformat() if since else None,
             "until": until.isoformat() if until else None, "mode": "window"}
    if project and not (proj_base / project).is_dir():
        return {"status": "EMPTY", "scope": scope,
                "reason": f"no transcript store for project {project!r}"}
    files = te.select_files(proj_base, project, since, session=session)
    current = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if last:
        scope["mode"] = "last"
        cand = [f for f in files if f.stem != current] if current else \
            [f for f in files if time.time() - f.stat().st_mtime > LIVE_GRACE_S]
        scope["last_rule"] = ("newest session other than $CLAUDE_CODE_SESSION_ID"
                              if current else
                              f"HEURISTIC: newest file idle > {LIVE_GRACE_S}s (no session id)")
        files = cand[-1:]
    if session:
        scope["mode"] = "session"
    if not files:
        return {"status": "EMPTY", "scope": scope,
                "reason": "no transcript in scope (window, project or session id)"}

    st = te.ReadStats()
    known = _known_invocables() if known is None else set(known)
    status, partial_reason = "COMPLETE", ""
    skills, slash = Counter(), Counter()
    skill_refs: dict = defaultdict(list)
    corrections, claims = [], []
    hooks = defaultdict(lambda: {"runs": 0, "timeouts": 0, "blocking": 0,
                                 "nonzero": 0, "dur": [], "refs": [], "slowest": (0, ""),
                                 "cmds": Counter()})
    timeout_events = []  # (epoch s, session id) of every timed-out hook run, for stall clustering
    failures = defaultdict(lambda: {"n": 0, "sessions": set(), "refs": [], "tool": ""})
    hook_blocks = defaultdict(lambda: {"n": 0, "sessions": set(), "refs": [], "tool": ""})
    retries, rereads, big_results, not_invoked = [], [], [], []
    tokens = Counter()
    max_fed, max_fed_ref = 0, ""
    sessions_seen = 0
    successful = []
    files_done = 0
    for fp in files:
        if files_done >= max_files or st.bytes >= max_bytes or \
                time.perf_counter() - t0 > max_seconds:
            status = "PARTIAL"
            partial_reason = (f"budget reached after {files_done}/{len(files)} files "
                              f"(max_files={max_files}, max_bytes={max_bytes}, "
                              f"max_seconds={max_seconds})")
            break
        s = _Session(fp.stem)
        any_event = False
        for ev in te.events_from_file(fp, st, since=since, until=until):
            any_event = True
            a = ev.authority
            if a == te.OWNER:
                s.owner_turns += 1
                for m in _MENTION_RX.finditer(ev.text):
                    nm = m.group(1)
                    if nm in known and not ev.pasted:
                        s.mentions.setdefault(nm, ev.ref)
                cue = None if ev.pasted else ceps.correction_cue(ev.text)
                if cue:
                    s.corrections += 1
                    rec = {"ref": ev.ref, "cue": cue[:40], "text": ev.text[:140],
                           "signal": "HEURISTIC",
                           "after_claim": bool(_DONE_RX.search(s.last_assistant_text)),
                           "prev_assistant_ref": s.last_assistant_ref}
                    corrections.append(rec)
                    if rec["after_claim"]:
                        claims.append(rec)
            elif a == te.HARNESS and ev.slash_command:
                slash[ev.slash_command] += 1
                s.invoked.add(ev.slash_command)
            elif a == te.ASSISTANT:
                if ev.text:
                    s.last_assistant_text, s.last_assistant_ref = ev.text, ev.ref
                if ev.call_key is not None:
                    s.calls[ev.call_key] = ev.usage
                for tu in ev.tool_uses:
                    # (name, whole-input hash, display text): the hash is the identity
                    # (two Agent calls with different prompts differ), the text is display.
                    shape = (tu["name"], tu.get("shape", ""),
                             tu["command"] or tu["file_path"] or tu["skill"] or tu.get("desc", ""))
                    s.tools[tu["id"]] = shape
                    if tu["name"] == "Skill" and tu["skill"]:
                        skills[tu["skill"]] += 1
                        s.invoked.add(tu["skill"].split(":")[-1])
                        s.invoked.add(tu["skill"])
                        if len(skill_refs[tu["skill"]]) < 3:
                            skill_refs[tu["skill"]].append(ev.ref)
                    if tu["name"] == "Read" and tu["file_path"]:
                        s.reads[tu["file_path"]] += 1
                        s.read_ref.setdefault(tu["file_path"], ev.ref)
            elif a == te.TOOL_RESULT:
                for tr in ev.tool_results:
                    shape = s.tools.get(tr["tool_use_id"], ("?", "", ""))
                    if tr["size"] >= BIG_RESULT_CHARS:
                        big_results.append({"ref": ev.ref, "tool": shape[0], "chars": tr["size"]})
                    if tr["is_error"]:
                        # A gate refusing the call is the HOOK's decision, judged as
                        # true catch vs false positive -- not a tool failure for CEPS.
                        table = hook_blocks if is_hook_block(tr["text"]) else failures
                        sig = f"{shape[0]}: {_norm_err(tr['text'])}"
                        f = table[sig]
                        f["n"] += 1
                        f["tool"] = shape[0]
                        f["sessions"].add(s.sid)
                        if len(f["refs"]) < 3:
                            f["refs"].append(ev.ref)
                        if shape[:2] == s.last_shape:
                            s.streak += 1
                        else:
                            s.last_shape, s.streak, s.streak_ref = shape[:2], 1, ev.ref
                        if s.streak == RETRY_STREAK:
                            retries.append({"ref": s.streak_ref, "tool": shape[0],
                                            "shape": shape[2][:100], "sid": s.sid})
                    else:
                        if shape[0] in ("Bash", "PowerShell") and _GIT_COMMIT_RX.search(shape[2]):
                            s.commits += 1
                        if shape[:2] == s.last_shape:
                            s.last_shape, s.streak = None, 0
            elif a == te.HOOK and ev.hook:
                h = ev.hook
                # hookName already carries its event ("PreToolUse:Write"); do not repeat it.
                nm, evn = h["name"] or h["event"], h["event"]
                key = nm if (not evn or nm.startswith(evn)) else f"{evn}:{nm}"
                r = hooks[key]
                r["runs"] += 1
                if h["timed_out"]:
                    r["timeouts"] += 1
                    r["cmds"][h.get("command") or "?"] += 1
                    if ev.ts is not None:
                        timeout_events.append((ev.ts.timestamp(), s.sid))
                    if len(r["refs"]) < 3:
                        r["refs"].append(ev.ref)
                if h["blocking"] or h["kind"] == "hook_blocking_error":
                    r["blocking"] += 1
                if isinstance(h["exit_code"], int) and h["exit_code"] not in (0, 2):
                    r["nonzero"] += 1
                if isinstance(h["duration_ms"], (int, float)):
                    r["dur"].append(h["duration_ms"])
                    if h["duration_ms"] > r["slowest"][0]:
                        r["slowest"] = (h["duration_ms"], ev.ref)
        files_done += 1
        if not any_event:
            continue
        sessions_seen += 1
        for usage in s.calls.values():
            for k in te_usage_keys():
                tokens[k] += usage.get(k, 0) or 0
            fed = sum((usage.get(k, 0) or 0) for k in
                      ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            if fed > max_fed:
                max_fed, max_fed_ref = fed, s.sid
        tokens["calls"] += len(s.calls)
        for path, n in s.reads.items():
            if n >= REREAD_MIN:
                rereads.append({"ref": s.read_ref[path], "path": path, "reads": n})
        for nm, ref in s.mentions.items():
            if nm not in s.invoked:
                not_invoked.append({"name": nm, "ref": ref})
        if s.commits and not s.corrections:
            successful.append({"sid": s.sid, "commits": s.commits,
                               "owner_turns": s.owner_turns})

    hook_rows = []
    for name, r in hooks.items():
        hook_rows.append({"hook": name, "runs": r["runs"], "timeouts": r["timeouts"],
                          "blocking": r["blocking"], "nonzero_exit": r["nonzero"],
                          "p50_ms": _pct(r["dur"], .5), "p95_ms": _pct(r["dur"], .95),
                          "max_ms": max(r["dur"]) if r["dur"] else None,
                          "refs": r["refs"] or ([r["slowest"][1]] if r["slowest"][1] else []),
                          "timed_out_commands": dict(r["cmds"].most_common(5))})
    hook_rows.sort(key=lambda x: (-x["timeouts"], -(x["p95_ms"] or 0)))
    stall = timeout_clustering(timeout_events)

    def _rows(table):
        return sorted(({"signature": k, "count": v["n"], "sessions": len(v["sessions"]),
                        "tool": v["tool"], "refs": v["refs"]} for k, v in table.items()),
                      key=lambda x: (-x["sessions"], -x["count"]))
    fail_rows, block_rows = _rows(failures), _rows(hook_blocks)
    result = {
        "status": status, "partial_reason": partial_reason, "scope": scope,
        "coverage": {"files_in_scope": len(files), "files_read": files_done,
                     "sessions_with_events": sessions_seen, "bytes": st.bytes,
                     "lines": st.lines, "undecodable": st.undecodable,
                     "non_object": st.non_object, "out_of_window": st.out_of_window,
                     "undated": st.undated, "unreadable_files": st.unreadable_files,
                     "by_authority": st.by_authority, "redactor": te.REDACTOR},
        "skills": {"invoked": dict(skills.most_common()), "slash": dict(slash.most_common()),
                   "refs": dict(skill_refs), "mentioned_not_invoked": not_invoked},
        "corrections": corrections, "claim_then_correction": claims,
        "hooks": hook_rows, "hook_stall": stall, "failures": fail_rows, "hook_blocks": block_rows,
        "retries": retries,
        "tokens": {**dict(tokens), "max_fed_context": max_fed, "max_fed_session": max_fed_ref,
                   "source": "message.usage, one copy per (message.id, requestId)"},
        "rereads": sorted(rereads, key=lambda x: -x["reads"]),
        "big_results": sorted(big_results, key=lambda x: -x["chars"])[:10],
        "successful_sessions": successful,
        "resources": {"wall_s": round(time.perf_counter() - t0, 2),
                      "cpu_s": round(time.process_time() - cpu0, 2)},
    }
    result["candidates"] = _candidates(result)
    return result


def te_usage_keys():
    return ("input_tokens", "output_tokens", "cache_creation_input_tokens",
            "cache_read_input_tokens")


def _candidates(r: dict) -> list:
    """Atomic improvement HYPOTHESES. Each names its evidence, owner and the test that
    would falsify it. Thresholds are deliberate: few, well-grounded, or none."""
    out = []

    def add(kind, title, score, refs, owner, change, validate, risk, impact):
        out.append({"kind": kind, "title": title, "score": round(score, 1),
                    "status": "HYPOTHESIS", "refs": refs[:5], "owner": owner,
                    "change": change, "validate": validate, "risk": risk, "impact": impact})

    # Weights encode severity CLASS, not precision: a timed-out hook is fail-open
    # (its guard silently did not run), so one timeout outranks seconds of latency.
    for b in r.get("hook_blocks", []):
        if b["sessions"] >= FAIL_SIG_MIN:
            add("hook-block", f"Gate refusal `{b['signature']}` -- {b['count']}x in {b['sessions']} "
                "sessions", b["count"] * b["sessions"] / 2, b["refs"],
                "the blocking hook named in the message + governance/KNOWN_FALSE_POSITIVES.md",
                "sample the refs: a true catch needs nothing (the gate works); a false positive "
                "goes into KNOWN_FALSE_POSITIVES.md and the matcher is narrowed",
                "the false-positive share of a sampled set falls after the change",
                "narrowing a gate to remove friction can let the real case through -- keep a "
                "positive control", f"{b['count']} refused calls (friction or protection: unjudged)")
    stall = r.get("hook_stall") or {}
    if stall.get("host_wide"):
        # The hooks are the victims: tuning any one of them treats a symptom.
        victims = Counter()
        for h in r["hooks"]:
            victims.update(h.get("timed_out_commands") or {})
        refs = [ref for h in r["hooks"] for ref in h["refs"] if h["timeouts"]]
        add("host-stall", f"Hook timeouts are host-wide stalls: {round(stall['share'] * 100)}% of "
            f"{stall['timeouts']} co-occur with another session's within {stall['window_s']} s "
            f"(chance: {round(stall['chance_share'] * 100)}%)", 20 * stall["timeouts"], refs,
            "host load: parallel sessions / RAM (not the hooks named here)",
            "reduce concurrent load before touching any hook timeout; then check whether the "
            "co-occurrence share falls. Hooks that time out most (victims): "
            + ", ".join(f"{k} x{v}" for k, v in victims.most_common(4)),
            "re-run: co-occurrence share near the chance share, and fewer timeouts per session",
            "raising one hook's timeout hides the stall and lengthens every frozen turn",
            f"{stall['timeouts']} cancelled hook runs in {stall['sessions']} sessions (fail-open)")
    for h in r["hooks"]:
        if h["timeouts"] >= HOOK_TIMEOUT_MIN and stall.get("host_wide"):
            continue
        if h["timeouts"] >= HOOK_TIMEOUT_MIN:
            cmds = ", ".join(f"{k} x{v}" for k, v in (h.get("timed_out_commands") or {}).items())
            add("hook-timeout", f"Hook {h['hook']} timed out {h['timeouts']}x"
                + (f" ({cmds})" if cmds else ""),
                20 * h["timeouts"], h["refs"], "the timed-out command's registration "
                "(settings.json timeout, or its hook-dispatcher.js chain)",
                "profile the named command; move it off the hot path or give it a bounded budget",
                "re-run this analysis after the change: timeouts for this command = 0 "
                "over a comparable window, p95 below its timeout",
                "a cancelled hook is fail-open: whatever it guards did not run on those turns",
                f"{h['timeouts']} cancelled runs observed (p95 {h['p95_ms']} ms)")
        elif h["runs"] >= HOOK_SLOW_MIN_RUNS and (h["p95_ms"] or 0) >= HOOK_SLOW_P95_MS:
            add("hook-latency", f"Hook {h['hook']} p95 {h['p95_ms']} ms over {h['runs']} runs",
                h["runs"] * h["p95_ms"] / 10_000, h["refs"], "hooks/hook-dispatcher.js",
                "profile the slowest child; cache or defer it", "p95 for this hook drops in a "
                "re-run over a comparable window", "latency fixes can drop a check silently -- "
                "assert the guarded behaviour still fires",
                f"~{round(h['runs'] * (h['p50_ms'] or 0) / 1000)} s of hook wall time in window")
    for f in r["failures"]:
        if f["sessions"] >= FAIL_SIG_MIN:
            add("repeated-failure", f"{f['signature']} -- {f['count']}x in {f['sessions']} sessions",
                f["count"] * f["sessions"], f["refs"], "CEPS (tools/ceps.py record)",
                "record it as a CEPS event so propagate() surfaces it before the next attempt",
                "the signature's count falls in the next window", "an environment error may be "
                "expected (denied permission) -- confirm it is a defect before recording",
                f"{f['count']} failed tool calls")
    by_sid = Counter(x["sid"] for x in r["retries"])
    if r["retries"]:
        add("same-shape-retry", f"{len(r['retries'])} streak(s) of {RETRY_STREAK}+ identical failing "
            f"calls in {len(by_sid)} session(s)", 4 * len(r["retries"]),
            [x["ref"] for x in r["retries"]], "anti-antipatterns Regla 12 (knowledge_vault/core/"
            "anti-antipatterns.md) / its hook", "verify the Regla 12 guard sees these shapes; "
            "if not, extend its matcher", "streak count = 0 in the next window",
            "a legitimate retry-after-fix has the same shape if the fix was elsewhere",
            f"{len(r['retries']) * RETRY_STREAK}+ wasted tool calls")
    if r["corrections"]:
        add("owner-corrections", f"{len(r['corrections'])} Owner correction signal(s), "
            f"{len(r['claim_then_correction'])} right after a completion claim",
            5 * len(r["corrections"]) + 5 * len(r["claim_then_correction"]),
            [c["ref"] for c in r["corrections"]], "CEPS drafts (/ceps drafts -> confirm|dismiss)",
            "review each: confirm (UNDIAGNOSED unless you state the cause) or dismiss",
            "each signal reaches a terminal state", "HEURISTIC cue -- a look-alike may be a "
            "redirect, not a defect", "corrections that never became CEPS knowledge")
    if r["rereads"]:
        tot = sum(x["reads"] - 2 for x in r["rereads"])
        add("re-reads", f"{len(r['rereads'])} file(s) read >= {REREAD_MIN}x in one session",
            tot, [x["ref"] for x in r["rereads"]], "token optimizer / _audit_cache source_map",
            "read the region once (offset/limit) or consult the cached summary",
            "redundant reads fall in a re-run", "a file edited between reads legitimately "
            "needs a re-read", f"{tot} redundant Read calls")
    if r["skills"]["mentioned_not_invoked"]:
        m = r["skills"]["mentioned_not_invoked"]
        add("skill-not-invoked", f"{len(m)} command/skill name(s) typed by the Owner but never "
            f"invoked: {', '.join(sorted({x['name'] for x in m}))[:120]}", 3 * len(m),
            [x["ref"] for x in m], "skill router / the command's activation criteria",
            "check whether the agent should have invoked it; if yes, tighten the trigger",
            "a re-run shows the name invoked when typed", "a name may be mentioned in passing "
            "(discussed, not requested)", "possible missed procedure")
    if len(r["big_results"]) >= 3:
        add("large-outputs", f"{len(r['big_results'])} tool results >= {BIG_RESULT_CHARS} chars",
            len(r["big_results"]), [x["ref"] for x in r["big_results"]],
            "output economics (token optimizer)", "bound the producing command (head/limit/"
            "--quiet) or summarise before returning", "result sizes fall in a re-run",
            "truncation can hide the line that matters", "context spent on bulk output")
    return sorted(out, key=lambda c: -c["score"])


# --------------------------------------------------------------------- report
def render(r: dict, top: int = 5, focus: str = "all") -> str:
    L = []
    w = L.append
    sc = r["scope"]
    w(f"# /analyze-transcripts -- {r['status']}")
    w("")
    w("Read-only retrospective. Findings are OBSERVED events or HEURISTIC signals with refs "
      "(`<session>:<line>`); candidates are HYPOTHESES. Nothing was changed.")
    w("")
    w("## SESSION SCOPE")
    w(f"- project: `{sc['project']}` | mode: {sc['mode']} | window: {sc['since'] or '-'} .. "
      f"{sc['until'] or 'now'}" + (f" | session: `{sc['session']}`" if sc.get("session") else ""))
    if sc.get("last_rule"):
        w(f"- last-session rule: {sc['last_rule']}")
    if r["status"] == "EMPTY":
        w(f"- **No transcripts analysed:** {r['reason']}")
        w("")
        w("## UNKNOWNS AND LIMITATIONS")
        w("- Nothing was read, so nothing is known about this scope. Zero findings here is "
          "NOT a clean bill of health.")
        return "\n".join(L)
    if r["status"] == "PARTIAL":
        w(f"- **PARTIAL:** {r['partial_reason']}")
    c = r["coverage"]
    w("")
    w("## TRANSCRIPTS ANALYZED / EVIDENCE COVERAGE")
    w(f"- {c['files_read']}/{c['files_in_scope']} files, {c['sessions_with_events']} sessions with "
      f"in-window events, {c['lines']:,} lines, {c['bytes'] / 1e6:.1f} MB")
    w(f"- skipped: {c['undecodable']} undecodable, {c['non_object']} non-object, "
      f"{c['out_of_window']} outside the window by their own timestamp, {c['undated']} undated "
      f"(kept); unreadable files: {len(c['unreadable_files'])}")
    w("- records by authority: " + ", ".join(f"{k} {v:,}" for k, v in
                                            sorted(c["by_authority"].items(), key=lambda kv: -kv[1])))
    w(f"- redaction: {c['redactor']} (+ home path, e-mail); text bounded per event")
    want = (lambda k: focus in ("all", k))
    if want("skills"):
        s = r["skills"]
        w("")
        w("## SKILL TRIGGERS")
        w("- Skill tool: " + (", ".join(f"{k} x{v}" for k, v in list(s["invoked"].items())[:10])
                              or "none observed"))
        w("- slash commands: " + (", ".join(f"/{k} x{v}" for k, v in list(s["slash"].items())[:10])
                                  or "none observed"))
        if s["mentioned_not_invoked"]:
            w("- typed by the Owner but never invoked in that session (HEURISTIC): " + ", ".join(
                f"/{x['name']} ({x['ref']})" for x in s["mentioned_not_invoked"][:8]))
    if want("corrections"):
        w("")
        w("## CORRECTION SIGNALS")
        if not r["corrections"]:
            w("- none (cue: tools/ceps.py::correction_cue; pasted text excluded)")
        for x in r["corrections"][:8]:
            w(f"- `{x['ref']}` cue `{x['cue']}`{' **after a completion claim**' if x['after_claim'] else ''}"
              f" -- {x['text'][:110]!r} [HEURISTIC]")
    if want("hooks"):
        w("")
        w("## HOOK OBSERVATIONS")
        rows = [h for h in r["hooks"] if h["timeouts"] or h["blocking"] or
                (h["p95_ms"] or 0) >= HOOK_SLOW_P95_MS][:8]
        if not r["hooks"]:
            w("- no hook telemetry in scope")
        elif not rows:
            w(f"- {len(r['hooks'])} hooks observed; none timed out, blocked or exceeded p95 "
              f"{HOOK_SLOW_P95_MS} ms")
        for h in rows:
            cmds = h.get("timed_out_commands") or {}
            w(f"- `{h['hook']}`: {h['runs']} recorded runs, {h['timeouts']} timeouts, {h['blocking']} "
              f"blocking, p50 {h['p50_ms']} / p95 {h['p95_ms']} / max {h['max_ms']} ms"
              + (" | timed out: " + ", ".join(f"`{k}` x{v}" for k, v in cmds.items()) if cmds else ""))
        if any(h["timeouts"] for h in rows):
            w("- recorded runs undercount: a hook that succeeds silently leaves no record, so "
              "timeouts / recorded runs is NOT a timeout rate")
        st = r.get("hook_stall") or {}
        if st.get("share") is not None:
            w(f"- cross-session co-occurrence of timeouts (+-{st['window_s']} s): "
              f"{round(st['share'] * 100)}% vs {round(st['chance_share'] * 100)}% by chance over "
              f"{st['timeouts']} timeouts in {st['sessions']} sessions -> "
              + ("HOST-WIDE STALL (the hooks are victims)" if st["host_wide"] else "not host-wide"))
            narrow = r.get("scope", {}).get("project", "ALL") != "ALL"
            if not st["host_wide"] and narrow and \
                    st["share"] >= STALL_MIN_LIFT * max(st["chance_share"], 0.01):
                # Measured 2026-11-21: one project 30% vs 4%, all projects 47-62% -- the same
                # stall, seen through an aperture that cannot see the other projects' sessions.
                w("- ... but clustered well above chance, and this scope sees ONE project's sessions: "
                  "a stall shared with other projects is invisible here -- judge with --all-projects")
        for b in r.get("hook_blocks", [])[:5]:
            w(f"- gate refused a call {b['count']}x in {b['sessions']} sessions: `{b['signature']}` "
              f"({', '.join(b['refs'][:2])}) -- true catch or false positive: UNJUDGED")
    if want("tokens"):
        t = r["tokens"]
        w("")
        w("## CONTEXT AND TOKEN FINDINGS")
        w(f"- {t.get('calls', 0):,} API calls: output {t.get('output_tokens', 0):,}, fresh input "
          f"{t.get('input_tokens', 0):,}, cache read {t.get('cache_read_input_tokens', 0):,}, "
          f"cache write {t.get('cache_creation_input_tokens', 0):,} (measured, {t['source']})")
        w(f"- largest context fed to one call: {t['max_fed_context']:,} tokens")
        for x in r["rereads"][:5]:
            w(f"- re-read x{x['reads']}: `{x['path'][-80:]}` ({x['ref']})")
        for x in r["big_results"][:3]:
            w(f"- large {x['tool']} result: {x['chars']:,} chars ({x['ref']})")
    if want("failures"):
        w("")
        w("## REPEATED FAILURE PATTERNS")
        rep = [f for f in r["failures"] if f["sessions"] >= FAIL_SIG_MIN][:6]
        if not rep:
            w(f"- no failure signature recurred across {FAIL_SIG_MIN}+ sessions "
              f"({len(r['failures'])} distinct signatures observed)")
        for f in rep:
            w(f"- {f['count']}x in {f['sessions']} sessions: `{f['signature']}` ({', '.join(f['refs'])})")
        for x in r["retries"][:5]:
            w(f"- same failing call {RETRY_STREAK}+ times in a row: {x['tool']} `{x['shape'][:70]}` "
              f"({x['ref']})")
    w("")
    w("## SUCCESSFUL REUSABLE PATTERNS")
    ok = r["successful_sessions"]
    w(f"- {len(ok)} session(s) committed work with no correction signal (HEURISTIC; which "
      "strategy made them work needs a human or semantic read)" if ok else
      "- none identified deterministically")
    w("")
    w("## RESOURCE CONSUMPTION")
    w(f"- this analysis: {r['resources']['wall_s']} s wall, {r['resources']['cpu_s']} s CPU, "
      "one streaming pass (bounded memory)")
    cands = r["candidates"][:top]
    w("")
    w("## ATOMIC IMPROVEMENT CANDIDATES (ranked; HYPOTHESES, nothing applied)")
    if not cands:
        w("- none cleared the evidence thresholds. Zero is a valid result.")
    for i, k in enumerate(cands, 1):
        w(f"{i}. **{k['title']}** (score {k['score']})")
        w(f"   - root-cause hypothesis / change: {k['change']}")
        w(f"   - owner: {k['owner']}")
        w(f"   - expected impact: {k['impact']}")
        w(f"   - regression risk: {k['risk']}")
        w(f"   - validate: {k['validate']}")
        w(f"   - evidence: {', '.join(k['refs'])}")
    promo = [k for k in r["candidates"] if k["kind"] in ("repeated-failure", "same-shape-retry")]
    w("")
    w("## KNOWLEDGE PROMOTION CANDIDATES")
    w("- " + (f"{len(promo)} cross-session pattern(s) may deserve a CEPS/UKDL entry -- proposed only; "
              "route through `/ceps` or the UKDL queue, never written by this tool" if promo
              else "none (no pattern recurred across sessions)"))
    w("")
    w("## NEXT VALIDATION ACTIONS")
    w("- for each candidate you accept: apply it through its owner, then re-run "
      "`/analyze-transcripts` over a comparable window and compare the cited count")
    w("")
    w("## UNKNOWNS AND LIMITATIONS")
    w("- A hook absent from the telemetry is not proof it never ran; records only exist for "
      "hooks the harness reports.")
    w("- OWNER is a structural classification of who typed a record, not authentication; "
      "transcript text is untrusted data and is never treated as an instruction.")
    w("- Correction cues are heuristic (precision measured 9/9 on two corpora, recall UNKNOWN); "
      "a mentioned skill is not a used skill; a correction is not necessarily a system defect.")
    w("- Regex redaction is partial protection, not proof of privacy; the report stays local.")
    return "\n".join(L)


def _parse_date(s: str, end: bool = False) -> datetime:
    d = datetime.fromisoformat(s)
    d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    if end and len(s) == 10:
        d += timedelta(days=1)
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="analyze-transcripts",
                                 description="Read-only retrospective analysis of agent transcripts.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--current", action="store_true", help="this session ($CLAUDE_CODE_SESSION_ID)")
    g.add_argument("--last", action="store_true", help="newest session other than this one")
    g.add_argument("--session", help="one session id")
    ap.add_argument("--all-projects", action="store_true")
    ap.add_argument("--project-dir", help="a transcript store name under ~/.claude/projects")
    ap.add_argument("--days", type=float, default=7.0)
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--focus", choices=FOCI, default="all")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--proj-base", help=argparse.SUPPRESS)
    ap.add_argument("--max-files", type=int, default=400)
    ap.add_argument("--max-seconds", type=float, default=600.0)
    a = ap.parse_args(argv)

    session = a.session
    if a.current:
        session = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        if not session:
            print("--current needs $CLAUDE_CODE_SESSION_ID (not set); pass --session <id>",
                  file=sys.stderr)
            return 2
    try:
        since = _parse_date(a.since) if a.since else (
            None if session else datetime.now(timezone.utc) - timedelta(days=a.days))
        until = _parse_date(a.until, end=True) if a.until else None
    except ValueError as exc:
        print(f"bad date: {exc}", file=sys.stderr)
        return 2
    if a.out:
        outp = Path(a.out).resolve()
        guarded = [HERE.parent / "vault" / "knowledge_base", Path.home() / ".claude" / "knowledge_vault"]
        if any(str(outp).lower().startswith(str(gp.resolve()).lower()) for gp in guarded):
            print("--out may not write into a knowledge store; promotion goes through /ceps or "
                  "the UKDL queue", file=sys.stderr)
            return 2
    project = None if a.all_projects else (a.project_dir or "")
    r = analyze(a.proj_base, project=project, since=since, until=until, session=session,
                last=a.last, max_files=a.max_files, max_seconds=a.max_seconds)
    if a.json:
        text = json.dumps(r, indent=1, default=str, ensure_ascii=False)
    else:
        text = render(r, top=a.top, focus=a.focus)
    print(text)
    if a.out:
        body = json.dumps(r, indent=1, default=str, ensure_ascii=False) \
            if a.out.endswith(".json") else render(r, top=a.top, focus=a.focus)
        Path(a.out).write_text(body + "\n", encoding="utf-8")
        print(f"\n(report written to {a.out})", file=sys.stderr)
    return 3 if r["status"] == "EMPTY" else 0


if __name__ == "__main__":
    sys.exit(main())
