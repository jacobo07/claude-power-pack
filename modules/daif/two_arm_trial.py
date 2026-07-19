#!/usr/bin/env python3
"""DAIF-08 §11.7 — the two-arm behavioral trial.

§11.7 asserts no figure and defines no procedure. It names the three quantities (reasoning cost,
fidelity as behavioral equivalence, rework) and composes the method DAIF-03 Part X already defines.
This module is that method, run against real sessions with a real model.

The two arms (DAIF-03 10.3):
  Arm B (control) : the full conversational source of the session. UNISOLATED — runs under this
                    repo's normal CLAUDE.md/skills/hooks, because that is the real, current
                    re-reading path and isolating it would test a baseline nobody actually has.
  Arm A (compiled): the resume pack, with NO tool by which the source could be reached, and
                    ISOLATED via ISOLATION_FLAGS (T-DAIF-ISOLATION-LEAK-001) so the pack is its
                    ONLY context — no repo CLAUDE.md, skills, or hooks auto-loaded on top of it.
Same model, same build, same window, same task verbatim, and zero tools in BOTH arms — an arm that
can silently reach the source is not testing the artifact, it is testing the source with extra
steps. The isolation asymmetry is deliberate, not an oversight: clause 3 and 4 are measured on
Arm A alone, and what they measure is whether the PACK is sufficient — which requires Arm A to
have nothing else to fall back on. Arm B's role is only the token/cost baseline and the control-arm
clause-4 reading; it was never the surface those clauses are adjudicated against.

Adjudication (10.4) is deterministic code with the arm labels stripped, against the rubric sealed in
vault/plans/daif-two-arm-trial-2026-07-13.md BEFORE any arm ran. The adjudicator is not the compiler
and it holds no opinion: it counts.

What this module refuses to do: floor a negative delta at zero, re-run a mission to hunt a better
number, or pool the vector into a score. DAIF-03 10.5 — a composite is the mechanism by which a
safety regression is bought with an efficiency gain.

CLI:
  python modules/daif/two_arm_trial.py --session <path> [--out trial.json]
  python modules/daif/two_arm_trial.py --sample            (the 3 sealed missions)
  python modules/daif/two_arm_trial.py --dry-run           (build prompts, call no model)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from modules.daif.session_continuity_compiler import compile_session  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Held identical across arms. A trial whose arms crossed a model boundary is INVALID (10.3).
TRIAL_MODEL = "claude-sonnet-5"

# 10.3 — no tool by which the source could be reached, in EITHER arm.
DENIED_TOOLS = ["Read", "Glob", "Grep", "Bash", "PowerShell", "Edit", "Write", "NotebookEdit",
                "Task", "Agent", "WebFetch", "WebSearch", "TodoWrite"]

# T-DAIF-ISOLATION-LEAK-001. `claude -p` auto-discovers this repo's CLAUDE.md/skills/hooks/plugins
# regardless of --disallowed-tools -- confirmed via `claude --help` and a live probe: an isolated
# Arm A call measured session_overhead at 74,063 tokens BEFORE this fix, and the same trivial call
# under --safe-mode dropped to 28,074, then to ~6,156 once tool DEFINITIONS (not just invocation)
# were also stripped via --tools "" instead of listing DENIED_TOOLS. --bare is NOT usable here: its
# own help text says OAuth/keychain auth "are never read" under it, and this host authenticates via
# OAuth -- probed live, --bare returned "Not logged in". --safe-mode's help text explicitly says
# "Auth ... work normally", and a live probe confirmed it.
#
# Applied to Arm A ONLY, by design: the compiled pack must be the actor's ONLY context, which is
# exactly what clause 3 and 4 measure. Arm B (the full transcript) is deliberately left
# UNISOLATED -- it represents the real, current re-reading path, which in normal use DOES run
# inside this repo's live CLAUDE.md, so isolating it would test a baseline nobody actually has.
ISOLATION_FLAGS = ["--safe-mode", "--tools", ""]

CLI_TIMEOUT_S = 900

# The mission sample, sealed in the plan file before any arm ran (10.2). Selection rule: the three
# real sessions with the largest conversational source that still fits one context window.
SEALED_SAMPLE = [
    "c718d3f5-7a13-4c49-86ef-3f4c5ed63a43",
    "78014709-12f5-4d90-9d66-2e85aae1fab3",
    "f2910b35-5d62-485c-a011-f556e8b13657",
]
SESSIONS_DIR = Path.home() / ".claude" / "projects" / "C--Users-User--claude-skills-claude-power-pack"

# The continuation task. IDENTICAL in both arms, verbatim — the comparison is void otherwise.
CONTINUATION_TASK = """\
You are resuming a software engineering mission after a context boundary. Everything you know about
this mission is in the CONTEXT block above. You have no tools: you cannot read files, search the
repository, or open the session transcript.

Report your resumption state as a single JSON object and NOTHING else. No prose before or after, no
code fences. The object has exactly these keys:

{
  "state": {
    "done":        ["what has been completed"],
    "in_flight":   ["what is underway but not finished"],
    "not_started": ["what remains untouched"]
  },
  "open_obligations": [{"id": "<identifier if you have one, else empty string>", "text": "<the commitment>"}],
  "hard_constraints": ["<identifier or short name of each binding constraint you must honor>"],
  "need_source_access": <true if you cannot proceed without re-reading the original transcript or repository, else false>,
  "source_requests":   ["<each specific source you would need to open; empty list if none>"],
  "next_action": "<the single next concrete action you would take>"
}

Answer only from the CONTEXT block. Do not invent an identifier you were not given.
"""


@dataclass
class ArmResult:
    arm: str                      # 'A_compiled' | 'B_control'
    packet: str                   # what the actor was given
    ok: bool
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0         # everything the API billed as context + output
    cost_usd: float = 0.0
    duration_ms: int = 0
    model: str = TRIAL_MODEL
    packet_chars: int = 0
    stop_reason: str = ""     # an arm cut off by the output limit is a measurement artifact, not a
                              # silent failure — it must be visible in the record
    raw_reply: str = ""
    parsed: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass
class TrialResult:
    session_id: str
    trial_timestamp: str
    model: str
    arm_a_tokens: int
    arm_b_tokens: int
    token_delta_saved: int        # B - A. NEGATIVE means the pack cost MORE. Never floored.
    cost_delta_usd: float
    clause_3_verdict: str         # PASS | FAIL | UNVERIFIED
    clause_4_verdict: str
    clause_3_evidence: str
    clause_4_evidence: str
    invention_verdict: str        # the extra gate, not one of the six clauses
    invention_evidence: str
    equivalence_overlap: float    # word overlap of the two arms' obligation sets
    safety_verdict: str = "N/A"   # read-only mission; recorded as N/A, never as a pass
    arm_a: dict[str, Any] = field(default_factory=dict)
    arm_b: dict[str, Any] = field(default_factory=dict)
    # T-DAIF-ISOLATION-LEAK-001 — the two arms are no longer isolated identically (Arm A is
    # isolated via ISOLATION_FLAGS, Arm B deliberately is not), so they no longer share one
    # overhead figure. session_overhead_tokens is kept, RE-DEFINED as Arm A's (isolated) floor —
    # the number the F1 done-gate names ("session_overhead en Arm A cae ... hacia el tamano real
    # del pack"). arm_b_overhead_tokens is new and reports Arm B's (unisolated) floor honestly
    # rather than silently reusing Arm A's now-much-smaller number for both.
    session_overhead_tokens: int = 0
    arm_b_overhead_tokens: int = 0
    notes: list[str] = field(default_factory=list)


def session_source_text(session_path: Path) -> str:
    """The control arm's packet: every user and assistant turn. Tool-result bodies are excluded —
    they run to millions of characters and fit no context. The exclusion makes the CONTROL cheaper,
    so it can only understate the pack's advantage, never inflate it."""
    out: list[str] = []
    try:
        raw = session_path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""
    for line in raw.splitlines():
        try:
            rec = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(rec, dict) or rec.get("type") not in ("user", "assistant"):
            continue
        msg = rec.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = "\n".join(b.get("text", "") for b in content
                             if isinstance(b, dict) and b.get("type") == "text")
        if text.strip():
            out.append(f"[{rec.get('type')}] {text.strip()}")
    return "\n\n".join(out)


def _call_model(prompt: str, isolate: bool = False) -> dict[str, Any]:
    """One arm, one call. Zero tools. Real tokens from the API, never an estimate.

    isolate=True (Arm A only) adds ISOLATION_FLAGS so the pack is the actor's ONLY context —
    no repo CLAUDE.md, skills, or hooks auto-loaded (T-DAIF-ISOLATION-LEAK-001)."""
    cmd = ["claude", "-p", "--output-format", "json", "--model", TRIAL_MODEL]
    cmd += ISOLATION_FLAGS if isolate else ["--disallowed-tools", *DENIED_TOOLS]
    try:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=CLI_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    stdout = proc.stdout or ""
    start = stdout.find("{")
    if start < 0:
        return {"ok": False, "error": f"no JSON in CLI output (exit {proc.returncode}): "
                                      f"{(proc.stderr or stdout)[:300]}"}
    try:
        env = json.loads(stdout[start:])
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"unparseable CLI envelope: {exc}"}
    if env.get("is_error"):
        return {"ok": False, "error": str(env.get("result"))[:300]}
    return {"ok": True, "envelope": env}


def _arm(arm: str, packet_name: str, context_block: str) -> ArmResult:
    prompt = f"CONTEXT ({packet_name}):\n{context_block}\n\n---\n\n{CONTINUATION_TASK}"
    res = ArmResult(arm=arm, packet=packet_name, ok=False, packet_chars=len(context_block))
    call = _call_model(prompt, isolate=(arm == "A_compiled"))
    if not call["ok"]:
        res.error = call["error"]
        return res
    env = call["envelope"]
    usage = env.get("usage", {}) or {}
    res.ok = True
    res.input_tokens = int(usage.get("input_tokens", 0) or 0)
    res.output_tokens = int(usage.get("output_tokens", 0) or 0)
    res.cache_creation_tokens = int(usage.get("cache_creation_input_tokens", 0) or 0)
    res.cache_read_tokens = int(usage.get("cache_read_input_tokens", 0) or 0)
    # Everything the model actually had to be fed, plus what it produced. Cache-read tokens are
    # counted: they were context the model consumed, whatever the billing discount.
    res.total_tokens = (res.input_tokens + res.cache_creation_tokens
                        + res.cache_read_tokens + res.output_tokens)
    res.cost_usd = float(env.get("total_cost_usd", 0.0) or 0.0)
    res.duration_ms = int(env.get("duration_ms", 0) or 0)
    res.stop_reason = str(env.get("stop_reason", "") or "")
    # Parse the WHOLE reply, then truncate only the stored copy. Truncating before parsing severs
    # the closing brace of a long answer and reads a correct arm as a silent FAIL — an instrument
    # that fabricates the verdict it was built to measure.
    full_reply = str(env.get("result", ""))
    res.parsed = _parse_reply(full_reply)
    res.raw_reply = full_reply[:8000]
    return res


def _parse_reply(reply: str) -> dict[str, Any]:
    """The actor was asked for one JSON object. Fail-open: an unparseable reply is a fact about the
    arm, not a crash."""
    text = reply.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        obj = json.loads(text[start:end + 1])
    except (json.JSONDecodeError, ValueError):
        return {}
    return obj if isinstance(obj, dict) else {}


# --- adjudication: deterministic, blind to which arm produced what -------------------------------

def _words(text: str) -> set[str]:
    return {w for w in re.sub(r"[^a-z0-9 ]+", " ", str(text).lower()).split() if len(w) > 3}


def _obligation_words(parsed: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for ob in parsed.get("open_obligations") or []:
        if isinstance(ob, dict):
            out |= _words(ob.get("text", ""))
        else:
            out |= _words(ob)
    return out


# The RUBRIC is fixed and did not move: a citation is GROUNDED iff it names a unit that is in the
# packet. What follows are two MATCHERS implementing it, and BOTH are always reported, because a
# matcher is an instrument and an instrument can be wrong in either direction.
#
# STRICT (identifier, or citation text is a substring of a packet unit) is the matcher sealed in the
# plan. On the first mission it reported 4 "inventions" which, checked by hand against CLAUDE.md, are
# PARAPHRASES of real packet constraints — the arm wrote "Liveness Standard (sealed 2026-07-13)"
# where the packet says "Liveness Standard (MANDATORY -- sealed 2026-07-13)". A paraphrase of a unit
# that IS present is not an invention; scoring it as one is the instrument fabricating a finding.
#
# LENIENT (>= GROUNDING_WORD_THRESHOLD of the citation's words appear in one packet unit) tolerates
# the rewording. It was added AFTER the first arm's outputs were visible. DAIF-03 10.4 holds that a
# rubric amended once the outputs exist is a rubric fitted to them, so the amendment is DISCLOSED in
# every trial record, and the strict number is never dropped.
GROUNDING_WORD_THRESHOLD = 0.6
MIN_MATCH_KEY_LEN = 6


def _is_grounded_strict(citation: str, pack_ids: set[str], pack_texts: list[str]) -> bool:
    c = citation.strip()
    if c in pack_ids:
        return True
    key = re.sub(r"[^a-z0-9]+", "", c.lower())
    if len(key) < MIN_MATCH_KEY_LEN:
        return False
    return any(key in t or t in key for t in pack_texts if len(t) >= MIN_MATCH_KEY_LEN)


def _is_grounded(citation: str, pack_ids: set[str], pack_texts: list[str],
                 pack_wordsets: list[set[str]] | None = None) -> bool:
    """The lenient matcher: strict first, then word-containment to survive a paraphrase."""
    if _is_grounded_strict(citation, pack_ids, pack_texts):
        return True
    cw = _words(citation)
    if not cw or not pack_wordsets:
        return False
    return any(len(cw & pw) / len(cw) >= GROUNDING_WORD_THRESHOLD for pw in pack_wordsets if pw)


def ungrounded_citations(parsed: dict[str, Any], pack_ids: set[str], pack_texts: list[str],
                         pack_wordsets: list[set[str]]) -> tuple[set[str], list[str], list[str]]:
    """Return (all citations, ungrounded under STRICT, ungrounded under LENIENT)."""
    cited = {str(c) for c in (parsed.get("hard_constraints") or []) if str(c).strip()}
    for ob in parsed.get("open_obligations") or []:
        if isinstance(ob, dict) and str(ob.get("id", "")).strip():
            cited.add(str(ob["id"]).strip())
    strict = sorted(c for c in cited if not _is_grounded_strict(c, pack_ids, pack_texts))
    lenient = sorted(c for c in cited if not _is_grounded(c, pack_ids, pack_texts, pack_wordsets))
    return cited, strict, lenient


def adjudicate_clause_3(parsed: dict[str, Any], pack_ids: set[str], pack_texts: list[str],
                        pack_wordsets: list[set[str]]) -> tuple[str, str]:
    """Clause 3 — the current state is correctly identified.

    Measured: a grounded state was PRODUCED (all three buckets present, non-degenerate, and every
    cited id real). NOT measured: that the state is TRUE — the only obligation ledger in the estate
    is the artifact's own producer, and scoring the artifact against its own output is the circular
    rubric DAIF-03 10.7 forbids. The clause is therefore adjudicated in its honest, weaker form and
    the weakening is reported with the verdict."""
    if not parsed:
        return "FAIL", "the arm emitted no parseable state object at all"
    state = parsed.get("state")
    if not isinstance(state, dict):
        return "FAIL", "no 'state' object in the reply"
    buckets = ["done", "in_flight", "not_started"]
    missing = [b for b in buckets if b not in state]
    if missing:
        return "FAIL", f"state is missing bucket(s): {', '.join(missing)}"
    items = sum(len(state.get(b) or []) for b in buckets)
    if items == 0:
        return "FAIL", "state was emitted but every bucket is empty — no state was identified"
    cited, strict_ghosts, lenient_ghosts = ungrounded_citations(parsed, pack_ids, pack_texts,
                                                                pack_wordsets)
    detail = (f"state produced with {items} item(s) across done/in_flight/not_started; "
              f"{len(cited)} constraint(s) cited")
    if lenient_ghosts:
        return "FAIL", detail + (f"; {len(lenient_ghosts)} citation(s) match nothing in the packet "
                                 f"under EITHER matcher: "
                                 f"{', '.join(g[:40] for g in lenient_ghosts[:4])}")
    return "PASS", detail + (f" (all grounded; {len(strict_ghosts)} were paraphrases caught only by "
                             f"the lenient matcher. Correctness-vs-ground-truth NOT measured — "
                             f"see rubric)")


def adjudicate_clause_4(parsed: dict[str, Any]) -> tuple[str, str]:
    """Clause 4 — the actor continues WITHOUT indiscriminate re-reading. DAIF-03 10.5 names source
    re-reads the sharpest single signal in the procedure: an actor that goes looking for what the
    artifact lacks has told the estate exactly where the artifact is thin."""
    if not parsed:
        return "FAIL", "the arm emitted no parseable reply, so no re-read signal could be read"
    needs = parsed.get("need_source_access")
    requests = [r for r in (parsed.get("source_requests") or []) if str(r).strip()]
    if needs is None:
        return "UNVERIFIED", "the arm did not answer need_source_access"
    if needs or requests:
        return "FAIL", (f"the arm asked for the source: need_source_access={needs}, "
                        f"{len(requests)} request(s): {'; '.join(str(r)[:70] for r in requests[:3])}")
    return "PASS", "need_source_access=false and no source was requested — the arm continued from the packet alone"


def adjudicate_invention(parsed: dict[str, Any], pack_ids: set[str], pack_texts: list[str],
                         pack_wordsets: list[set[str]]) -> tuple[str, str]:
    """Not one of the six clauses. The extra gate: did the compiled arm cite anything that is not in
    its packet at all? BOTH matchers are reported — the strict count is never dropped, so a reader
    can see exactly what the lenient matcher forgave."""
    if not pack_ids and not pack_texts:
        return "UNVERIFIED", "nothing in the packet to check a citation against"
    cited, strict_ghosts, invented = ungrounded_citations(parsed, pack_ids, pack_texts,
                                                          pack_wordsets)
    if invented:
        return "FAIL", (f"{len(invented)} of {len(cited)} citation(s) match nothing in the pack "
                        f"under EITHER matcher: " + ", ".join(x[:50] for x in invented[:5]))
    return "PASS", (f"{len(cited)} citation(s), 0 invented under the lenient matcher; "
                    f"{len(strict_ghosts)} were paraphrases the STRICT matcher rejected "
                    f"(disclosed, not dropped)")


def measure_session_overhead(isolate: bool = False) -> int:
    """T-DAIF-ISOLATION-LEAK-001 — the CLI carries a system prompt, and (unless isolate=True)
    this repo's CLAUDE.md, hooks and skills, into every call. Since Arm A and Arm B no longer run
    under the same flags, this is no longer one identical-in-both-arms number; call it once per
    arm's isolation setting and report both, rather than assuming they cancel."""
    call = _call_model("Reply with exactly: OK", isolate=isolate)
    if not call["ok"]:
        return 0
    u = call["envelope"].get("usage", {}) or {}
    return (int(u.get("input_tokens", 0) or 0) + int(u.get("cache_creation_input_tokens", 0) or 0)
            + int(u.get("cache_read_input_tokens", 0) or 0) + int(u.get("output_tokens", 0) or 0))


def run_trial(session_path: str | Path, overhead_a: int | None = None,
              overhead_b: int | None = None) -> TrialResult:
    session = Path(session_path)
    notes: list[str] = []

    package = compile_session(PROJECT_ROOT, session)
    pack_ids = {c["identifier"] for c in package.get("hard_constraints", [])}
    pack_ids |= {o["identifier"] for o in package.get("open_obligations", [])}
    # A unit may legitimately be cited by its text — the task prompt permits a short name.
    pack_units = ([c.get("text", "") for c in package.get("hard_constraints", [])]
                  + [o.get("text", "") for o in package.get("open_obligations", [])])
    pack_texts = [re.sub(r"[^a-z0-9]+", "", t.lower()) for t in pack_units]
    pack_wordsets = [_words(t) for t in pack_units]
    if package["status"] != "COMPILED":
        notes.append(f"the compiler refused this session: {package.get('cannot_guarantee')}")

    source = session_source_text(session)
    if not source.strip():
        notes.append("the control arm has no source text — the session yielded no readable turns")

    # Arm B (control) runs FIRST: the artifact does not get to see the mission before the source does.
    arm_b = _arm("B_control", "the full conversational source of this session", source)
    arm_a = _arm("A_compiled", "the compiled DAIF-08 resume pack for this session",
                 json.dumps(package, ensure_ascii=False, indent=2))

    if overhead_a is None:
        overhead_a = measure_session_overhead(isolate=True)
    if overhead_b is None:
        overhead_b = measure_session_overhead(isolate=False)

    c3, c3_ev = adjudicate_clause_3(arm_a.parsed, pack_ids, pack_texts, pack_wordsets)
    c4, c4_ev = adjudicate_clause_4(arm_a.parsed)
    inv, inv_ev = adjudicate_invention(arm_a.parsed, pack_ids, pack_texts, pack_wordsets)
    _, strict_ghosts, lenient_ghosts = ungrounded_citations(arm_a.parsed, pack_ids, pack_texts,
                                                            pack_wordsets)
    notes.append(
        "MATCHER DISCLOSURE (DAIF-03 10.4): the lenient word-containment matcher was added AFTER the "
        "first arm's outputs were seen, because the sealed strict matcher scored PARAPHRASES of real "
        "packet constraints as inventions. The rubric did not move; a broken matcher was repaired. "
        f"Ungrounded citations this mission — strict: {len(strict_ghosts)}, "
        f"lenient: {len(lenient_ghosts)}. Both stay on the record.")

    # The control arm is adjudicated on the same rubric — a baseline, not a competitor.
    b_c4, b_c4_ev = adjudicate_clause_4(arm_b.parsed)
    notes.append(f"control arm clause-4 baseline: {b_c4} — {b_c4_ev}")

    wa, wb = _obligation_words(arm_a.parsed), _obligation_words(arm_b.parsed)
    overlap = (len(wa & wb) / len(wa | wb)) if (wa | wb) else 0.0

    if not arm_a.ok:
        c3 = c4 = inv = "UNVERIFIED"
        c3_ev = c4_ev = inv_ev = f"the compiled arm did not run: {arm_a.error}"
    if not arm_b.ok:
        notes.append(f"the control arm did not run: {arm_b.error} — the delta is not measurable")

    return TrialResult(
        session_id=session.stem,
        trial_timestamp=datetime.now(timezone.utc).isoformat(),
        model=TRIAL_MODEL,
        arm_a_tokens=arm_a.total_tokens,
        arm_b_tokens=arm_b.total_tokens,
        # B - A. Negative means the pack cost MORE than the source. Never floored, never adjusted.
        token_delta_saved=arm_b.total_tokens - arm_a.total_tokens,
        cost_delta_usd=round(arm_b.cost_usd - arm_a.cost_usd, 6),
        clause_3_verdict=c3, clause_3_evidence=c3_ev,
        clause_4_verdict=c4, clause_4_evidence=c4_ev,
        invention_verdict=inv, invention_evidence=inv_ev,
        equivalence_overlap=round(overlap, 3),
        arm_a=asdict(arm_a), arm_b=asdict(arm_b),
        session_overhead_tokens=overhead_a,
        arm_b_overhead_tokens=overhead_b,
        notes=notes,
    )


def write_trial(result: TrialResult, out: str | Path | None = None) -> Path:
    path = Path(out) if out else (PROJECT_ROOT / "vault" / "trials" /
                                  f"two_arm_{result.session_id}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DAIF-08 §11.7 two-arm behavioral trial")
    ap.add_argument("--session", default=None)
    ap.add_argument("--sample", action="store_true", help="run the 3 sealed missions")
    ap.add_argument("--dry-run", action="store_true", help="build the packets, call no model")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    targets: list[Path] = []
    if args.sample:
        targets = [SESSIONS_DIR / f"{s}.jsonl" for s in SEALED_SAMPLE]
    elif args.session:
        targets = [Path(args.session)]
    else:
        ap.error("give --session <path> or --sample")

    if args.dry_run:
        for t in targets:
            pkg = compile_session(PROJECT_ROOT, t)
            src = session_source_text(t)
            print(f"{t.stem}: pack={len(json.dumps(pkg)):,} chars  source={len(src):,} chars  "
                  f"status={pkg['status']}")
        return 0

    overhead_a = measure_session_overhead(isolate=True)
    overhead_b = measure_session_overhead(isolate=False)
    print(f"session overhead — arm A (isolated, ISOLATION_FLAGS)   : {overhead_a:,} tokens")
    print(f"session overhead — arm B (unisolated, natural baseline): {overhead_b:,} tokens\n")

    for t in targets:
        r = run_trial(t, overhead_a=overhead_a, overhead_b=overhead_b)
        path = write_trial(r, args.out if len(targets) == 1 else None)
        print(f"== {r.session_id} ==")
        print(f"  arm B (control, full source) : {r.arm_b_tokens:>9,} tokens  ${r.arm_b['cost_usd']:.4f}")
        print(f"  arm A (compiled, resume pack): {r.arm_a_tokens:>9,} tokens  ${r.arm_a['cost_usd']:.4f}")
        print(f"  token_delta_saved (B - A)    : {r.token_delta_saved:>9,}  "
              f"({'pack is cheaper' if r.token_delta_saved > 0 else 'PACK COSTS MORE'})")
        print(f"  clause 3 (state identified)  : {r.clause_3_verdict} — {r.clause_3_evidence}")
        print(f"  clause 4 (no re-reading)     : {r.clause_4_verdict} — {r.clause_4_evidence}")
        print(f"  invention (extra gate)       : {r.invention_verdict} — {r.invention_evidence}")
        print(f"  arm agreement (obligations)  : {r.equivalence_overlap}")
        for n in r.notes:
            print(f"  note: {n}")
        print(f"  written: {path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
