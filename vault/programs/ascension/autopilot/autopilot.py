#!/usr/bin/env python3
"""Ascension Autopilot: self-continuing S generations on two lanes (KSR, Tennis).

Owner authorization (typed, 2026-11-11, laptop pane d957c937): "Apruebo autopilot: 400M total, 80M/dia, hasta
2026-11-30, 25M max por generacion, perfiles aditivos con condiciones S26C, dos carriles KSR y Tennis".
Plan: laptop vault/programs/ascension/AUTOPILOT-PLAN.md. One generation = one mission record:
checkpoint -> independent JUDGE -> PLANNER -> deterministic POLICY (over the exact packet bytes) -> BUDGET ->
close old, arm new (held), authority, release.
Reuses tools/gsd_mission.py for every mission act; owns only its state/ledger/digest files.
Budget semantics: the ledger books AUTHORITY GRANTED (the generation's phase caps, reserved before the arm) plus
judge/planner usage (measured, or a conservative reserve when unmeasured) plus any measured overrun beyond a
generation's authority at close. The 80M/day cap therefore limits what is granted or consumed-by-the-autopilot per UTC
day, not the processing a worker does after midnight inside authority granted the day before.
Kill switch: file OFF in this directory. Usage: autopilot.py tick | status | dry-tick
dry-tick runs against a scratch copy of state/ledger (printed), never the real files.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evolve  # noqa: E402  (EVO, Owner "y" 2026-11-12)

HOME = Path(os.environ.get("AP_HOME", "/home/kobii/agora/ascension-autopilot"))
OUT = HOME  # where state/ledger/log/digest/owner_queue are written; a scratch dir in dry-tick
PP = Path(os.environ.get("AP_PP", "/home/kobii/.claude/skills/claude-power-pack"))
STATE_DIR = Path(os.environ.get("AP_STATE_DIR", "/home/kobii/.claude/state"))
CLAUDE = os.environ.get("AP_CLAUDE", "/usr/local/bin/claude")
OWNER_TURN = "d957c937-f56d-4447-9386-5d8002fe0b90:" + os.environ.get("AP_OWNER_TS", "")
# Owner 2026-11-12 (laptop pane ddf4990e, uuid of "1. 120M"): release a 120M tranche. 285,261,779 + 120M =
# 405,261,779 unlocked; the total moves 400M -> 405,261,779 so the full 120M is usable (nothing left frozen).
TOTAL_CAP = 4_700_000_000  # Owner 2026-11-16 'Day cap 500M and total +1B' (pane 4de9b293, parallel lanes); was 3.7B: Owner 2026-11-15 'desatascalo todo y subele 600M a cada uno' (pane 4de9b293): 5 lane envelopes of 600M from 09:24Z on 659M booked; was 2.1B (Owner 2026-11-14 '600M each' FIFA+WIIPARTY, 4246d04c)
DAY_CAP = 500_000_000  # Owner 2026-11-16 'Day cap 500M and total +1B' (pane 4de9b293); was 250M: Owner 2026-11-14 "raise it" (pane 4de9b293): 6 lanes share it; was 90M (Owner 2026-11-12, c26eafbf)
GEN_CAP = 25_000_000
FRESH_GEN_CAP = 1_000_000
CALL_RESERVE = 2_000_000  # booked for a judge/planner call whose usage could not be measured (never 0)
# Ascension throughput T1 O2 (Owner "y" 2026-11-22, pane 37612bb0): what judging a checkpoint asks of the day cap. It was
# GEN_CAP + 2 * CALL_RESERVE = 29M, i.e. the NEXT generation's caps, so finished generations waited 16 h unjudged at 477M/500M.
# Measured on the GEX44 ledger 2026-11-22 (315 judges, 477 plans, 49 levers, all measured): judge p99 1.15M, plan p99 2.21M,
# lever design mean 0.9M (max about 3.5M) -> 6M. Arming keeps its own GEN_CAP ask and its kept-judgment wait.
JUDGE_ASK = 6_000_000
# Authority granted before the autopilot existed that the Owner counts inside TOTAL_CAP (not inside a day's cap:
# it was not granted by the autopilot). Owner 2026-11-11 (pane fa41bae9): "S27's 200M ... it adds to that".
PRIOR_AUTHORITY = (("m-10566700b1fe", "S27", 200_000_000),)
# Owner 2026-11-11 (pane fa41bae9) approved AUTOPILOT-REORIENT-PLAN ("y"): a 60M processed ceiling for diagnosis, pilots
# and integration on top of what was booked at approval: 225,261,779 = PRIOR 200M + ledger 25,261,779 (judge/planner
# 4,761,779 + S28K's 20.5M). Everything between UNLOCKED_CAP and TOTAL_CAP is FROZEN behind value gates: the autopilot
# can only ask for it (owner_queue), never release it.
UNLOCKED_CAP = 4_700_000_000  # Owner 2026-11-16 'Day cap 500M and total +1B' (pane 4de9b293); was 3.7B: Owner 2026-11-15 '600M a cada uno' (5 lanes), pane 4de9b293; was 2.1B (2026-11-14, 4246d04c)
WALL = dt.datetime(2026, 11, 30, 23, 59, tzinfo=dt.timezone.utc)
BLANK_STOP = 3          # consecutive NONE generations (no verified progress of any class) stop the lane
INFO_PARK = 2           # consecutive INFORMATION generations without CERT/CAPABILITY park the lane for an Owner look
NO_CONVERSION_PARK = 3  # the original 3-generation rule: 3 in a row without CERT or CAPABILITY park the lane
GIT = os.environ.get("CPP_GIT_EXE") or "git"
PARK_REASONS = ("FROZEN", "total", "wall")  # budget refusals that only the Owner can lift (the day cap is a wait)
MAX_ARM_FAILS = 2
TERMINAL = {"COMPLETED", "HALTED", "ORPHANED"}

# ---------------------------------------------------------------- policy (deterministic, no model)
_W = r"(?!via\b|through\b|with\b|using\b|by\b|under\b)[\w/.-]+"  # an object word; instrumental prepositions end it
# 2026-11-18 (Owner ruling OR-3, pane 08cba76c): canonical HEADERS may change under OR-3 (full build passes, no function
# leaves 100%); the canonical ctx stays protected, it is the certificate identity of the KSR/Tennis profiles.
_TARGET = (r"(certifier|certify\.py|certify\.decide|cert_cxx\w*|ksr_lane\w*|canonical\s+(ctx|context)|"
           r"pinned\s+stages?|(historical|existing|old|pinned|cert1[\w-]*)\s+receipts?)")
_DESTRUCTIVE = r"(modif|chang|edit|patch|rewrit|relax|weaken|replac|overwrit|delet|remov|alter|amend|truncat|regenerat)"
_WRITE = _DESTRUCTIVE[:-1] + r"|updat|add|append|writ|extend)"
_PASSIVE = (r"(modified|changed|edited|patched|rewritten|relaxed|weakened|updated|replaced|overwritten|deleted|removed|"
            r"altered|amended|extended|truncated|regenerated|appended)")
FORBIDDEN = [
    (r"\bpush\w*", "push"),
    (r"\b(merg|combin|fold)\w*\b[^.;]*\b(headline|counters?)\b|\binto\s+(the\s+|a\s+|any\s+)?headline\b",
     "merge counters into a headline"),
    (r"\brevo[kc]\w*", "revocation"),
    (r"\bR-?2\b", "R2"),
    (r"\bH-?2\b", "H2"),
    (rf"\b{_WRITE}\w*(\s+{_W}){{0,4}}?\s+{_TARGET}", "certifier/canonical/receipt change"),
    (rf"\b{_DESTRUCTIVE}\w*(\s+{_W}){{0,4}}?\s+(the\s+)?receipts?\b", "certifier/canonical/receipt change"),
    (rf"\b({_TARGET[1:-1]}|receipts?)\s+(is\s+|are\s+|will\s+be\s+|gets?\s+|be\s+)?{_PASSIVE}\b",
     "certifier/canonical/receipt change"),
    (r"\bpaid\b|ANTHROPIC_API_KEY|\bapi\s+key\b|\bcloud\b", "paid/cloud"),
    (r"\bnew\s+(budget|authority)\b|\b(raise|increase|extend|bump|lift)\w*\s+(the\s+)?(budget|authority|cap|ceiling)",
     "budget change"),
]
PROFILE_TRIGGER = (r"\b(new|additive|another|second|extra|own)\s+(\w+\s+){0,2}profiles?\b|"
                   r"\b(creat|regist|introduc|defin|establish|propos|add|open)\w*\s+(\w+\s+){0,3}profiles?\b")
PROFILE_CONDITIONS = {
    "independent target oracle": r"\bindependent\b[^;,]*\boracle\b",
    "original DOL bytes": r"\boriginal\s+DOL\b",
    "frozen pilot committed before the draw": r"\b(frozen|freez\w*)\b[^;,]*\bpilot\b|\bpilot\b[^;,]*\b(frozen|freez\w*)\b",
    "pre/post controls": r"\bpre\s*/\s*post\b[^;,]*\bcontrols?\b|\bpre-?\s+and\s+post-?\w*\b[^;,]*\bcontrols?\b",
    "A2 negatives": r"\bA2\b[^;,]*\bnegatives?\b",
    "historical receipts unchanged": r"\breceipts?\b[^;,]*\b(unchanged|byte-identical|untouched)\b|"
                                     r"\b(unchanged|byte-identical|untouched)\b[^;,]*\breceipts?\b",
    "separate counters": r"\bseparate\b[^;,]*\bcounters?\b|\bcounters?\b[^;,]*\bseparate\b",
}
NEGATION = re.compile(r"\b(no|not|non|without|skip\w*|never|later|unknown|tbd|omit\w*|absent|missing|none|deferred|"
                      r"n/a)\b|\?", re.I)
# A profile trigger is negated only when a negation word stands at most 5 plain words before "profile", with no
# punctuation between (applied to the text up to the trigger's end). "no new profile, then add another profile" still
# triggers on the second. S30T (2026-11-11) was refused for a fact ending "no new profile".
TRIGGER_NEGATED = re.compile(r"\b(no|not|never|without|nor|neither|excludes?|excluding|forbids?|rules?\s+out|ruled\s+out)"
                             r"\s+(\w+\s+){0,5}profiles?$", re.I)
PHASE_RE = re.compile(r"^Phase (\d+): (.+)$")
CAP_RE = re.compile(r"\bcap\s+(\d+(?:\.\d+)?)\s*M\b", re.I)
# 2026-11-17 (Owner 'y', pane 08cba76c): a number glued to an identifier ("F17", "S137R") is not an amount, and a bare
# number followed by a noun that is not a budget word ("fresh 131 functions") is a count. Both refused FIFA S140F/S142F,
# TENNIS S119T/S137T, MKW S122M and WSR S139R today. A unit, a budget word or nothing after the number still reads as tokens.
FRESH_RE = re.compile(r"\bfresh\b[^.;]{0,30}?(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?:\s*([MmKk])\b|(?!\w))\s*([A-Za-z][\w-]*)?")
FRESH_BUDGET_WORDS = frozenset({"tokens", "token", "tok", "budget", "authority", "capital", "allowance", "million",
                                "millions", "thousand",
                                # function words say nothing about what the number counts: still read as an amount
                                "for", "to", "of", "in", "on", "at", "and", "or", "more", "extra", "new", "additional",
                                "is", "are", "as", "per", "with", "from", "by", "the", "a", "an", "if", "then", "so"})


def normalize(text: str) -> tuple[str, list[str]]:
    """NFKC text plus violations for characters that can hide a forbidden act (format chars, non-ASCII letters)."""
    t = unicodedata.normalize("NFKC", text or "")
    bad = []
    if any(unicodedata.category(c) == "Cf" for c in t):
        bad.append("invisible format characters in planner text")
    if any(ord(c) > 127 and unicodedata.category(c).startswith("L") for c in t):
        bad.append("non-ASCII letters in planner text")
    return t, bad


def _fresh_tokens(num: str, unit: str | None) -> float:
    v = float(num.replace(",", ""))
    if unit and unit[0] in "Mm":
        return v * 1_000_000
    if unit and unit[0] in "Kk":
        return v * 1_000
    return v if v >= 1000 else v * 1_000_000  # a bare small number is read as millions (the larger reading)


def policy_check(phase_lines: list[str], command: str, extra: list[str] | tuple = ()) -> list[str]:
    """Return the list of violations (empty = admitted). Judges every planner-written string that reaches the packet
    or the launch prompt: phase lines, command notes, and `extra` (title, facts). The authority header and
    NOT-authorised block are written by the autopilot itself."""
    bad: list[str] = []
    if not 2 <= len(phase_lines) <= 8:
        bad.append(f"{len(phase_lines)} phase lines (need 2-8)")
    total = 0.0
    for i, line in enumerate(phase_lines, 1):
        if "\n" in line or "\r" in line:
            bad.append(f"Phase {i} spans several lines")
        m = PHASE_RE.match(line)
        if not m or int(m.group(1)) != i:
            bad.append(f"line {i} is not 'Phase {i}: ...'")
            continue
        caps = CAP_RE.findall(line)
        if not caps:
            bad.append(f"Phase {i} has no 'cap <N>M'")
        else:
            total += float(caps[0])
    if total * 1_000_000 > GEN_CAP:
        bad.append(f"phase caps sum {total}M > generation cap {GEN_CAP/1e6:.0f}M")
    text, nbad = normalize("\n".join(phase_lines) + "\n" + (command or "") + "\n" + "\n".join(str(x) for x in extra))
    bad += nbad
    for num, unit, word in FRESH_RE.findall(text):
        if not unit and word and word.lower() not in FRESH_BUDGET_WORDS:
            continue  # "fresh 131 functions": a count, not an amount
        if _fresh_tokens(num, unit) > FRESH_GEN_CAP:
            bad.append(f"asks fresh {num}{unit or ''} > {FRESH_GEN_CAP/1e6:.0f}M")
    for pat, label in FORBIDDEN:
        if re.search(pat, text, re.I) and f"forbidden act: {label}" not in bad:
            bad.append(f"forbidden act: {label}")
    for line in text.splitlines():
        if not any(not TRIGGER_NEGATED.search(line[:m.start()] + m.group(0))
                   for m in re.finditer(PROFILE_TRIGGER, line, re.I)):
            continue  # no trigger, or every trigger negated ("no new profile", "rules out a new profile")
        clauses = re.split(r"[;,]", line)
        for name, pat in PROFILE_CONDITIONS.items():
            if not any(re.search(pat, c, re.I) and not NEGATION.search(c) for c in clauses):
                bad.append(f"new profile without S26C condition (in the same line, not negated): {name}")
    return bad


def _scaffold_phases(text: str) -> list[str] | None:
    try:
        sys.path.insert(0, str(PP / "tools"))
        import gsd_milestone_scaffold as gms  # noqa: PLC0415 -- the scaffolder the arm really uses
        return gms.phases_from_packet(text, "\x00none")
    except Exception:  # noqa: BLE001 -- unverifiable is refused, never admitted
        return None


def packet_phase_drift(packet: str, phases: list[str]) -> str | None:
    """The milestone is scaffolded from the WHOLE packet; it must yield exactly the policy-checked phases."""
    got, want = _scaffold_phases(packet), _scaffold_phases("\n".join(phases))
    if got is None or want is None:
        return "cannot load gsd_milestone_scaffold to verify the packet's phases"
    if got != want:
        return f"packet yields phases {got[:10]} but policy checked {want[:10]}"
    return None


_NEUTRAL = ["Phase 1: a (cap 1M): x", "Phase 2: b (cap 1M): y"]
POLICY_REPLANS = 2  # re-plans after a policy refusal, each told why (S41K: the 1st re-plan fixed the profile line, not a cap)
POLICY_RETRY_TICKS = 2  # ticks that re-plan a planner-fixable refusal before it parks (_refused)
OWNER_REFUSAL = re.compile(r"budget|envelope|day cap|authority", re.I)  # refusals only the Owner lifts: they park


def plan_checks(lane: dict, name: str, p: dict):
    """-> phases, notes, title, facts, bad (policy + packet drift), packet text ("" when refused)."""
    phases, notes, title, facts = planner_strings(p)
    bad = policy_check(phases, notes, [title, *facts])
    text = packet_text(lane, name, p) if not bad else ""
    if not bad:
        drift = packet_phase_drift(text, phases)
        if drift:
            bad.append(drift)
    p["_offenders"] = ([l for l in phases if not CAP_RE.search(l)] +
                       [l for l in [*phases, title, *facts, *str(notes or "").splitlines()]
                        if l and policy_check(_NEUTRAL, "", [l])])
    return phases, notes, title, facts, bad, text


def replan_feedback(bad: list[str], offenders: list[str] | None = None) -> str:
    """What the one re-plan is told: the refusals, the lines that drew them, and the rule they break."""
    lines = "\n".join(f"  - {l[:300]}" for l in (offenders or [])[:8]) or "  - (see the refusals)"
    return ("AUTOPILOT POLICY REFUSED YOUR PREVIOUS PLAN. Write a new plan that passes; the checks are unchanged.\n"
            f"Refusals: {'; '.join(bad)[:1200]}\nLines that drew them:\n{lines}\n"
            "Rules: every phase line is 'Phase N: <id> <what> (cap <N>M): ...'. A line that names a new or additive "
            "profile must carry, in that same line and not negated: an independent target oracle on the original DOL "
            "bytes; a frozen pilot committed before the draw; pre/post controls; A2 negatives; historical receipts "
            "byte-identical; separate counters. Otherwise refer to the profile only by its name (e.g. 'the S38K "
            "profile'), never as a new one. Planted mutants are described by the check that catches them. "
            "An EVO research/repair packet names its selected lever in a phase line, carries every word the refusal "
            "says is missing, and keeps the sum of its phase caps inside the cap the refusal states.")


# ---------------------------------------------------------------- budget ledger
def _now() -> float:
    return float(os.environ.get("AP_NOW") or time.time())


def _day(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def ledger_rows() -> list[dict]:
    p = OUT / "ledger.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def ledger_add(**row) -> None:
    row.setdefault("ts", _now())
    with open(OUT / "ledger.jsonl", "a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def spend_totals(rows: list[dict], now: float) -> tuple[int, int]:
    total = sum(int(r.get("tokens") or 0) for r in rows) + sum(t for _, _, t in PRIOR_AUTHORITY)
    today = sum(int(r.get("tokens") or 0) for r in rows if _day(float(r["ts"])) == _day(now))
    return total, today


def budget_admits(rows: list[dict], now: float, ask: int = GEN_CAP) -> str | None:
    """None = admitted, else the reason. Reserves the full generation cap before arming."""
    if dt.datetime.fromtimestamp(now, dt.timezone.utc) >= WALL:
        return "wall 2026-11-30T23:59Z reached"
    total, today = spend_totals(rows, now)
    if total + ask > TOTAL_CAP:
        return f"total {total:,} + {ask:,} > {TOTAL_CAP:,}"
    if total + ask > UNLOCKED_CAP:
        return (f"FROZEN: total {total:,} + {ask:,} > unlocked {UNLOCKED_CAP:,}; the rest of {TOTAL_CAP:,} is frozen "
                "behind value gates and only the Owner releases a tranche")
    if today + ask > DAY_CAP:
        return f"today {today:,} + {ask:,} > {DAY_CAP:,} (waits for the next UTC day)"
    return None


RESERVATION_KINDS = ("arm_reserve", "auto_topup")
# T2 W1 (Owner "y" 2026-11-22, pane a52cc240): escrow a generation holds. arm_reserve is keyed by gen; the others by
# mission. Owner top-ups and grants are escrow too: before W1 they were never released (KSR S181K kept 4M).
ESCROW_GEN_KINDS = ("arm_reserve",)
ESCROW_MISSION_KINDS = ("auto_topup", "owner_topup", "owner_grant")
# rows that adjust what a generation has booked: refunds, releases, spend corrections and the close overrun
SETTLE_MISSION_KINDS = ("reserve_release", "spend_correction", "generation_closed")


def _gen_escrow(rows: list[dict], mission, gen) -> list[dict]:
    return [r for r in rows if (r.get("kind") in ESCROW_GEN_KINDS and gen and r.get("gen") == gen)
            or (r.get("kind") in ESCROW_MISSION_KINDS and mission and r.get("mission") == mission)]


def booked_net(rows: list[dict], mission, gen) -> int:
    """What the ledger books for one generation: its escrow, plus refunds, releases, spend corrections and the close
    overrun. Conservation (T2 W1): once a generation is settled, booked_net == its measured spend. That keeps SPENT
    monotonic: a release can only return booking above the measured spend, never the spend itself."""
    adj = [r for r in rows if (r.get("kind") == "arm_refund" and gen and r.get("gen") == gen)
           or (r.get("kind") in SETTLE_MISSION_KINDS and mission and r.get("mission") == mission)]
    return sum(int(r.get("tokens") or 0) for r in _gen_escrow(rows, mission, gen) + adj)


def reservation_release(rows: list[dict], mission: str | None, gen: str | None, authority, spent) -> list[tuple[float, int]]:
    """T1 O1 (Owner "y" 2026-11-22, Q1: the day cap counts measured spend + open reservations): at close, the part of a
    generation's reservations it never spent is released, each piece on the DAY its reservation was booked (ts of that
    row), newest first and never more than that row still holds. Unmeasured spend or no authority (a pre-autopilot
    generation) releases nothing: an unknown is never 0.
    T2 W1: the amount is booked_net - spent, the conservation residual. It is idempotent by construction (a settled
    generation has a residual of 0), and it never exceeds what was booked (review M1: FIFATC S95C had authority 12.5M,
    booked 9.5M, and the authority-based release erased 3M of measured spend)."""
    if spent is None or not authority or not isinstance(spent, int) or spent < 0:
        return []
    unused = booked_net(rows, mission, gen) - spent
    if unused <= 0:
        return []
    rel = [r for r in rows if r.get("kind") == "reserve_release" and mission and r.get("mission") == mission]
    out = []
    for r in sorted(_gen_escrow(rows, mission, gen), key=lambda x: -float(x["ts"])):
        t = float(r["ts"])
        held = int(r.get("tokens") or 0) + sum(int(x.get("tokens") or 0) for x in rel
                                               if abs(float(x.get("ts") or 0) - (t + 0.001)) < 1e-6)
        amt = min(unused, held)
        if amt > 0:
            out.append((t, amt))
            unused -= amt
        if unused <= 0:
            break
    return out


def spend_correction(rows: list[dict], mission, gen, spent) -> int:
    """Tokens a settled generation must still book so that booked_net == measured spend (0 = conserved). Positive only
    when the ledger holds less than was measured (an over-release, or a terminal overrun that never got a close row)."""
    if not mission or spent is None or not isinstance(spent, int) or spent < 0:
        return 0
    return max(0, spent - booked_net(rows, mission, gen))


def settle(ln: str, mission, gen, authority, spent, at: float | None = None, why: str = "close") -> dict:
    """Books one generation's settlement: releases above the measured spend (back-dated to each reservation's day), or a
    spend_correction below it, dated `at` (the close, else now). Idempotent: a second call books nothing."""
    freed = release_reservations(ln, mission, gen, authority, spent)
    fix = spend_correction(ledger_rows(), mission, gen, spent) if authority else 0
    if fix:
        ledger_add(lane=ln, kind="spend_correction", gen=gen, mission=mission, tokens=fix, spend=spent,
                   ts=(at + 0.002) if at else _now(), why=why)
    return {"freed": freed, "corrected": fix}


RESEARCH_BOOKED_KEEP = 12  # generations whose research booking is remembered for the credit (newest kept)


def book_research(ls: dict, gen, caps: int) -> None:
    """Round 6 (Owner 2026-11-26 "go ahead", pane a90ef78f): a RESEARCH generation books its whole cap at arm, as before;
    the booking is now remembered per generation so its unspent part can come back (credit_research)."""
    ls["research_spent"] = int(ls.get("research_spent") or 0) + int(caps)
    b = dict(ls.get("research_booked") or {})
    b.pop(str(gen), None)
    b[str(gen)] = int(caps)
    ls["research_booked"] = dict(list(b.items())[-RESEARCH_BOOKED_KEEP:])


def credit_research(ln: str, ls: dict, gen, freed) -> int:
    """The unspent reservation a settlement released goes back into the lane's research room, bounded by what that
    generation booked as research (an EXPLOIT generation booked none, so it credits none). Idempotent: settle frees a
    reservation once, and the credit draws down the remembered booking. -> tokens credited."""
    b = dict(ls.get("research_booked") or {})
    left = int(b.get(str(gen)) or 0)
    c = max(0, min(int(freed or 0), left, int(ls.get("research_spent") or 0)))
    if not c:
        return 0
    ls["research_spent"] = int(ls.get("research_spent") or 0) - c
    b[str(gen)] = left - c
    ls["research_booked"] = b
    ledger_add(lane=ln, kind="research_credit", gen=gen, tokens=0, credited=c, research_spent=ls["research_spent"])
    log(f"{ln}: research room +{c:,} (unspent reservation of {gen}); research_spent {ls['research_spent']:,}")
    return c


def release_reservations(ln: str, mission: str | None, gen: str | None, authority, spent) -> int:
    """Books the reserve_release rows (negative tokens, back-dated to the reservation's day). Returns tokens released."""
    total = 0
    for ts, amt in reservation_release(ledger_rows(), mission, gen, authority, spent):
        ledger_add(lane=ln, kind="reserve_release", gen=gen, mission=mission, tokens=-amt, ts=ts + 0.001,
                   released_ts=_now(), spend=spent, authority=authority)
        total += amt
    return total


def backfill_releases(rows: list[dict]) -> list[dict]:
    """One-off: the release rows closed generations would have booked under O1 (generation_closed carries mission,
    spend, authority; the gen name comes from its generation_armed row). Idempotent through reservation_release."""
    gen_of = {r.get("mission"): r.get("gen") for r in rows if r.get("kind") == "generation_armed"}
    out, seen = [], list(rows)
    for r in rows:
        if r.get("kind") != "generation_closed" or not r.get("measured"):
            continue
        m = r.get("mission")
        for ts, amt in reservation_release(seen, m, gen_of.get(m), r.get("authority"), r.get("spend")):
            row = {"lane": r.get("lane"), "kind": "reserve_release", "gen": gen_of.get(m), "mission": m,
                   "tokens": -amt, "ts": ts + 0.001, "released_ts": float(r["ts"]), "spend": r.get("spend"),
                   "authority": r.get("authority"), "backfill": True}
            out.append(row)
            seen.append(row)
    return out


def reservation_overhead(rows: list[dict]) -> dict:
    """Reserved vs released, lifetime: the share of booked reservations that closed generations never spent."""
    reserved = sum(int(r.get("tokens") or 0) for r in rows if r.get("kind") in RESERVATION_KINDS)
    released = -sum(int(r.get("tokens") or 0) for r in rows if r.get("kind") == "reserve_release")
    return {"reserved": reserved, "released": released, "ratio": round(released / reserved, 3) if reserved else None}


def call_tokens(measured) -> tuple[int, bool]:
    """(tokens to book, measured?) -- an unmeasured call books the reserve, never 0."""
    if isinstance(measured, int) and measured >= 0:
        return measured, True
    return CALL_RESERVE, False


# ---------------------------------------------------------------- state
def load_state() -> dict:
    p = OUT / "state.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save_state(st: dict) -> None:
    tmp = OUT / "state.json.tmp"
    tmp.write_text(json.dumps(st, indent=1, sort_keys=True))
    tmp.replace(OUT / "state.json")


def log(msg: str) -> None:
    line = f"{dt.datetime.now(dt.timezone.utc).strftime('%FT%TZ')} {msg}"
    with open(OUT / "autopilot.log", "a") as f:
        f.write(line + "\n")
    print(line)


def owner_queue(lane: str, text: str) -> None:
    with open(OUT / "owner_queue.md", "a") as f:
        f.write(f"- [{dt.datetime.now(dt.timezone.utc).strftime('%FT%TZ')}] {lane}: {text}\n")


OWNER_Q = re.compile(r"OWNER\s+(DECISION\s+NEEDED|QUESTION)", re.I)
# 2026-11-18 (Owner 'y', pane 08cba76c): 4 of the first QUESTION lines were "## Next route (OR-4, not an Owner question)".
# A line that negates the question, or cites a standing ruling that answers it, is not one.
OWNER_Q_NOT = re.compile(r"\bnot\s+(an?\s+)?owner\s+(question|decision)|\bno\s+owner\s+(question|decision)|\bOR-[1-6]\b",
                         re.I)


def surface_owner_questions(lane: str, checkpoint: str, product: str) -> int:
    """Copy a checkpoint's 'OWNER DECISION NEEDED / OWNER QUESTION' lines (at most 3, verbatim, 300 chars) to
    owner_queue.md as QUESTION lines, once each. 2026-11-18 (Owner 'y', pane 08cba76c): 77 such lines in ~50 checkpoints
    since 11-14 never reached the Owner, and the work routed around them. The text is the worker's: data, not orders."""
    p = Path(checkpoint) if os.path.isabs(checkpoint) else Path(product, checkpoint)
    try:
        lines = [l.strip()[:300] for l in p.read_text(errors="replace").splitlines()
                 if OWNER_Q.search(l) and not OWNER_Q_NOT.search(l)][:3]
        seen = (OUT / "owner_queue.md").read_text(errors="replace") if (OUT / "owner_queue.md").exists() else ""
    except OSError:
        return 0
    n = 0
    for q in lines:
        if q[:160] not in seen:
            owner_queue(lane, f"QUESTION (from {p.name}): {q}")
            n += 1
    return n


def digest(lane: str, text: str) -> None:
    with open(OUT / "digest.md", "a") as f:
        f.write(f"\n## {dt.datetime.now(dt.timezone.utc).strftime('%FT%TZ')} {lane}\n{text}\n")


# ---------------------------------------------------------------- mission runtime (reused, never duplicated)
def sh(cmd: list[str], cwd=None, timeout=600, dry=False) -> tuple[int, str]:
    if dry:
        print("DRY:", " ".join(str(c) for c in cmd)[:300])
        return 0, ""
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)


def gm(*args, dry=False, timeout=600) -> tuple[int, str]:
    return sh(["python3", PP / "tools/gsd_mission.py", *args], dry=dry, timeout=timeout)


def mission(mid: str) -> dict | None:
    p = STATE_DIR / f"gsd-mission-{mid}.json"
    return json.loads(p.read_text()) if p.exists() else None


def follow_renewals(mid: str) -> str:
    """A mission halted on its iteration cap is renewed under a new id (auto-resume). Follow the chain."""
    seen = {mid}
    while True:
        nxt = None
        for p in STATE_DIR.glob("gsd-mission-m-*.json"):
            try:
                r = json.loads(p.read_text())
            except Exception:  # noqa: BLE001 -- a half-written record is skipped, re-read next tick
                continue
            if r.get("renewed_from") == mid and r["mission_id"] not in seen:
                nxt = r["mission_id"]
        if not nxt:
            return mid
        seen.add(nxt)
        mid = nxt


def mission_spend(mid: str) -> int | None:
    rc, out = gm("topology", "--mission", mid, timeout=300)
    try:
        return int(json.loads(out[out.index("{"):])["spend"])
    except Exception:  # noqa: BLE001 -- unmeasured stays None, never 0
        return None


def protected_check(lane: dict) -> str | None:
    """The autopilot's own read of the protected identities (the judge's claim is not trusted alone).
    None = intact; else why not. A missing file is a failure, never a pass."""
    import hashlib
    for p in lane.get("protected", []):
        path = Path(p["path"])
        if not path.exists():
            return f"protected file missing: {path}"
        data = path.read_bytes()
        if not hashlib.sha256(data).hexdigest().startswith(p["sha256_prefix"]):
            return f"protected file changed (sha256): {path}"
        n = data.count(b"\n")
        if "lines" in p and n != int(p["lines"]):
            return f"protected file line count {n} != {p['lines']}: {path}"
    return None


# ---------------------------------------------------------------- headless judge / planner
def run_claude(prompt: str, cwd: str, tools: list[str], add_dirs: list[str], max_turns: int, timeout: int) -> dict:
    cmd = [CLAUDE, "-p", prompt, "--output-format", "json", "--max-turns", str(max_turns), "--allowedTools", *tools]
    for d in add_dirs:
        cmd += ["--add-dir", d]
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout after {timeout}s", "tokens": None}
    try:
        out = json.loads(r.stdout)
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": f"rc={r.returncode} unparsable output: {(r.stdout + r.stderr)[-400:]}", "tokens": None}
    u = out.get("usage")
    tokens = None
    if isinstance(u, dict) and u:
        tokens = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                                  "cache_read_input_tokens", "output_tokens"))
    return {"ok": not out.get("is_error"), "result": out.get("result") or "", "tokens": tokens,
            "session": out.get("session_id")}


def last_json(text: str) -> dict | None:
    """The JSON object that ENDS the reply (only whitespace or a closing code fence may follow). No fallback to an
    earlier object: a malformed final object is None, never some object quoted further up."""
    t = re.sub(r"```\s*$", "", (text or "").rstrip()).rstrip()[-40000:]
    if not t.endswith("}"):
        return None
    i = t.rfind("{")
    while i != -1:
        try:
            obj = json.loads(t[i:])
            return obj if isinstance(obj, dict) else None
        except Exception:  # noqa: BLE001 -- a nested or malformed suffix; try the next '{' to the left
            i = t.rfind("{", 0, i)
    return None


# ---------------------------------------------------------------- progress taxonomy (verified here, not taken from text)
# Owner 2026-11-11: separate certifications, useful new information, verified instrumental capabilities and work without
# progress; none of them may be faked by documentation or effect-less commits. The judge REPORTS evidence pointers; this
# code checks them in git (ancestry, file presence per commit, non-prose effects) and re-runs a claimed gate itself.
# Woz review 2026-11-11 (VETO, fixed here): every pointer must be anchored to THIS generation's commit window
# (base..HEAD, base = product HEAD recorded at arm); "exists in git" is history, not progress. Effects are an ALLOWLIST
# of data/code extensions; CERT counts distinct CERTIFIED rows ADDED since base; the gate that runs must be the cited blob.
DATA = re.compile(r"\.(json|jsonl|csv|tsv)$", re.I)
CODE = re.compile(r"\.py$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _git(product: str, *args) -> tuple[int, str]:
    return sh([GIT, "-c", "core.quotePath=false", "-C", product, *args], timeout=120)


def _sha(product: str, ref) -> str | None:
    ref = str(ref or "")
    if ref != "HEAD" and not SHA_RE.match(ref):
        return None
    rc, out = _git(product, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    out = out.strip()
    return out if rc == 0 and SHA_RE.match(out) else None


def in_window(product: str, base, commit) -> bool:
    """commit is strictly after this generation's base and reachable from HEAD."""
    b, c = _sha(product, base), _sha(product, commit)
    return bool(b and c and b != c and _git(product, "merge-base", "--is-ancestor", b, c)[0] == 0
                and _git(product, "merge-base", "--is-ancestor", c, "HEAD")[0] == 0)


def _changed(product: str, commit) -> list[str]:
    """Files the commit changed against its first parent (merge commits included)."""
    c = _sha(product, commit)
    if not c:
        return []
    rc, out = _git(product, "diff", "--name-only", f"{c}^1", c)
    return [] if rc != 0 else [f.strip() for f in out.splitlines() if f.strip()]


def _blob(product: str, ref: str, path: str) -> str | None:
    rc, out = _git(product, "rev-parse", "--verify", "--quiet", f"{ref}:{path}")
    return out.strip() if rc == 0 and out.strip() else None


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# 2026-11-21 (Owner "y", pane 3581ade8): a receipts profile (WIIPARTY wp-dol-link-v1, 184 rows over 7 generations, none
# ever counted) writes rows with NO verdict field and keeps CERTIFIED in a sibling counters file. Such rows count only
# when, at the receipts commit: one `counters*.json` in the same directory was changed by that commit; its
# decide.CERTIFIED == certified_total == the distinct verdict-less rows this generation added to the receipts file; and a
# `receipt_registry.json` at that commit lists BOTH files under the rows' one profile with the sha256 of the exact
# committed bytes, entries absent from the registry at the base (this generation registered them; a pre-registered hash
# does not count). A row that carries any "verdict" key is judged by the CERTIFIED-string rule alone.
COUNTERS_RE = re.compile(r"^counters[\w.-]*\.json$")


def _blob_bytes(product: str, commit: str, path: str) -> bytes | None:
    try:
        r = subprocess.run([GIT, "-C", product, "show", f"{commit}:{path}"], capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def _json_at(product: str, commit: str, path: str):
    b = _blob_bytes(product, commit, path)
    try:
        return None if b is None else json.loads(b.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


def counters_ok(product: str, base, commit: str, path: str, rows: dict) -> str | None:
    """None when the verdict-less rows `rows` {id: row} added to receipts `path` are certified by their sibling counters
    file and the receipt registry (rule above); else why not."""
    import hashlib
    c = _sha(product, commit)
    if not c:
        return f"commit {commit} unknown"
    changed = _changed(product, c)
    folder = path.rsplit("/", 1)[0] if "/" in path else ""
    cands = [f for f in changed if (f.rsplit("/", 1)[0] if "/" in f else "") == folder
             and COUNTERS_RE.match(f.rsplit("/", 1)[-1])]
    if len(cands) != 1:
        return f"{len(cands)} counters*.json beside {path} changed by {c[:12]} (need exactly 1)"
    cpath = cands[0]
    cnt = _json_at(product, c, cpath)
    dec = cnt.get("decide") if isinstance(cnt, dict) else None
    k = dec.get("CERTIFIED") if isinstance(dec, dict) else None
    if type(k) is not int or k != cnt.get("certified_total") or k != len(rows):
        return (f"counters {cpath}: decide.CERTIFIED {k!r} / certified_total {cnt.get('certified_total') if isinstance(cnt, dict) else None!r}"
                f" != {len(rows)} verdict-less rows added")
    profiles = {r.get("profile") for r in rows.values()}
    if len(profiles) != 1 or not isinstance(next(iter(profiles)), str):
        return f"receipt rows of {path} do not share one profile: {sorted(map(str, profiles))[:4]}"
    prof = next(iter(profiles))
    b = _sha(product, base)
    rc, tree = _git(product, "ls-tree", "-r", "--name-only", c)
    regs = [f for f in tree.splitlines() if f.rsplit("/", 1)[-1] == "receipt_registry.json"] if rc == 0 else []
    need = {p: hashlib.sha256(_blob_bytes(product, c, p) or b"").hexdigest() for p in (path, cpath)}

    def entries(ref, reg):
        doc = _json_at(product, ref, reg) if ref else None
        ents = doc.get("entries") if isinstance(doc, dict) else doc
        return {(e.get("path"), e.get("sha256"), e.get("profile")) for e in ents if isinstance(e, dict)} \
            if isinstance(ents, list) else set()
    want = {(p, need[p], prof) for p in need}
    for reg in regs:
        # listed at the receipts commit, and NOT already at the base: this generation registered them
        if want <= entries(c, reg) and not (want & entries(b, reg)):
            return None
    return f"no receipt_registry.json lists {path} and {cpath} ({prof}) with their sha256, added by this generation"


def verify_cert(v: dict, product: str, base):
    """None = not claimed; True = verified; str = claimed but refused."""
    n = v.get("new_canonical_certs")
    if type(n) is not int or n <= 0:
        return None
    recs = v.get("cert_receipts")
    if not isinstance(recs, list) or not recs:
        return "certificates claimed without cert_receipts [{path, commit}]"
    ids: set[str] = set()
    why = ""
    for r in recs:
        path, commit = (str(r.get("path") or ""), str(r.get("commit") or "")) if isinstance(r, dict) else ("", "")
        if not DATA.search(path) or not in_window(product, base, commit) or path not in _changed(product, commit):
            return f"receipts {path}@{commit} is not a data file changed by a commit of this generation"
        rc, diff = _git(product, "diff", "-U0", _sha(product, base), _sha(product, commit), "--", path)
        bare: dict[str, dict] = {}
        for line in diff.splitlines() if rc == 0 else []:
            if not line.startswith("+") or line.startswith("+++"):
                continue
            try:
                row = json.loads(line[1:])
            except Exception:  # noqa: BLE001 -- a non-JSON added line is not a receipt
                continue
            if not isinstance(row, dict):
                continue
            if "CERTIFIED" in [x for x in row.values() if isinstance(x, str)]:
                ids.add(str(row.get("id") or line[1:]))
            elif "verdict" not in row:
                bare[str(row.get("id") or row.get("addr") or row.get("symbol") or line[1:])] = row
        if bare:
            bad = counters_ok(product, base, commit, path, bare)
            if bad is None:
                ids.update(f"{path}::{i}" for i in bare)
            else:
                why = f"; counters rule: {bad}"
    return True if len(ids) >= n else f"{len(ids)} distinct CERTIFIED rows added since the base < claimed {n}{why}"


def verify_capability(v: dict, product: str, base):
    c = v.get("capability")
    if v.get("validated_capability") is not True:
        return None
    if not isinstance(c, dict):
        return "capability claimed without {gate, commit, heldout_file, mutant_rc, heldout_before, heldout_after}"
    gate, commit, hf = str(c.get("gate") or ""), str(c.get("commit") or ""), str(c.get("heldout_file") or "")
    if not CODE.search(gate) or not in_window(product, base, commit) or gate not in _changed(product, commit):
        return f"gate {gate}@{commit} is not code changed by a commit of this generation"
    blob = _blob(product, commit, gate)
    if not blob or blob != _blob(product, "HEAD", gate) or blob != _git(product, "hash-object", gate)[1].strip():
        return "the gate that would run (HEAD / working tree) is not the cited one"
    if not DATA.search(hf) or _blob(product, "HEAD", hf) is None \
            or not _git(product, "diff", "--name-only", _sha(product, base), "HEAD", "--", hf)[1].strip():
        return f"held-out measure {hf} is not a data file written in this generation"
    if type(c.get("mutant_rc")) is not int or c["mutant_rc"] == 0:  # judge-attested
        return "no planted mutant turned the gate red"
    if not (_num(c.get("heldout_before")) and _num(c.get("heldout_after"))) or c["heldout_before"] == c["heldout_after"]:
        return "no measured change on a frozen held-out cohort"
    rc, _ = sh([sys.executable, gate], cwd=product, timeout=600)
    return True if rc == 0 else f"gate re-run by the autopilot rc={rc}"


def _data_nonempty(body: str, path: str) -> bool:
    try:
        if path.lower().endswith(".json"):
            return bool(json.loads(body))
        if path.lower().endswith(".jsonl"):
            return any(json.loads(l) for l in body.splitlines() if l.strip())
    except Exception:  # noqa: BLE001 -- unparsable data is not a result
        return False
    return len([l for l in body.splitlines() if l.strip()]) >= 2  # csv/tsv: header + a row


def verify_information(v: dict, product: str, base):
    i = v.get("information")
    if not isinstance(i, dict):
        return None
    fz, rs = str(i.get("freeze_commit") or ""), str(i.get("result_commit") or "")
    hyp, res = str(i.get("hypothesis_file") or ""), str(i.get("result_file") or "")
    if i.get("verdict") not in ("SUPPORTED", "REFUTED"):
        return f"hypothesis not resolved ({i.get('verdict')})"
    if i.get("positive_control") is not True:
        return "positive control not seen"
    if not (in_window(product, base, fz) and in_window(product, base, rs) and in_window(product, fz, rs)):
        return "freeze and result must be commits of this generation, the freeze strictly first"
    if hyp not in _changed(product, fz):
        return f"hypothesis {hyp} was not written by the freeze commit"
    if not DATA.search(res) or res not in _changed(product, rs) or _blob(product, fz, res) is not None:
        return f"result {res} is not a data file first written after the freeze"
    if not _data_nonempty(_git(product, "show", f"{_sha(product, rs)}:{res}")[1], res):
        return f"result {res} holds no data"
    return True


def _tracked_dirty(product: str) -> set | None:
    """Tracked paths that differ from HEAD; None outside a git work tree."""
    rc, out = _git(product, "diff", "--name-only", "HEAD")
    return {l.strip() for l in str(out).splitlines() if l.strip()} if rc == 0 else None


def match_at100(lane: dict, product: str):
    """-> (set of 'unit::function' at 100% in the lane's objdiff report, None), or (None, why). The autopilot builds the
    report itself in the product at HEAD (SPEC-match-exploit.md); (None, None) when the lane has no match_report."""
    mr = (lane or {}).get("match_report") or {}
    cmd, path = mr.get("cmd"), mr.get("path")
    if not (isinstance(cmd, list) and cmd and isinstance(path, str) and path):
        return None, None
    before = _tracked_dirty(product)
    try:
        rc, out = sh([str(c) for c in cmd], cwd=product, timeout=1800)
    finally:
        # 2026-11-18 (Owner 'y', pane 08cba76c): the MKW report build rewrote config/RMCP01/module/splits.txt at 01:11Z;
        # the dirty control repo held S151M's launch for 6.7 h (behind_dirty). The autopilot measures, never edits: a
        # tracked file its build dirtied is restored; one that was already dirty is left as it was.
        after = _tracked_dirty(product) if before is not None else None
        for f in sorted((after or set()) - (before or set())):
            _git(product, "checkout", "--", f)
            log(f"{lane.get('name')}: MATCH build dirtied tracked {f}; restored")
    if rc != 0:
        return None, f"report command rc={rc}: {str(out)[-200:]}"
    try:
        r = json.loads(Path(product, path).read_text())
    except Exception as e:  # noqa: BLE001 -- an unreadable report is a refusal with its reason, never a match
        return None, f"report {path} unreadable: {e}"
    return {f"{u.get('name')}::{f.get('name')}" for u in r.get("units") or [] if isinstance(u, dict)
            for f in u.get("functions") or [] if isinstance(f, dict) and f.get("fuzzy_match_percent") == 100}, None


def match_lost(old: set, cur: set) -> list:
    """Functions the snapshot had at 100% that HEAD no longer has: any one refuses the MATCH."""
    return sorted(old - cur)


def read_snap(snap: Path, lane_name: str) -> set | None:
    """The MATCH snapshot, or None when there is none. 2026-11-25 (WIIPARTY S357W, 56 CERTIFIED and AGREE): the disk filled
    at 06:16Z while the snapshot was being rewritten, left it 0 bytes, and every later judgment of the lane died on
    json.loads (ERROR JSONDecodeError, lane parked). An unreadable snapshot is moved aside (.corrupt-<ts>) and the caller
    re-seeds from HEAD with nothing claimed: no MATCH is credited twice and none is invented."""
    if not snap.exists():
        return None
    try:
        return set(json.loads(snap.read_text()))
    except (ValueError, TypeError, OSError) as exc:
        bad = snap.with_name(f"{snap.name}.corrupt-{int(time.time())}")
        snap.replace(bad)
        log(f"{lane_name}: MATCH snapshot unreadable ({type(exc).__name__}); moved to {bad.name}, re-seeded from HEAD")
        owner_queue(lane_name, f"NOTICE (no action needed): MATCH snapshot was unreadable ({type(exc).__name__}); kept as "
                               f"{bad.name} and re-seeded from HEAD, nothing claimed from it")
        return None


def write_snap(snap: Path, cur: set) -> None:
    """Atomic: a full disk fails the write and leaves the previous snapshot whole."""
    snap.parent.mkdir(parents=True, exist_ok=True)
    tmpf = snap.with_name(snap.name + ".tmp")
    tmpf.write_text(json.dumps(sorted(cur)))
    os.replace(tmpf, snap)


def verify_match(lane, product: str, notes: list):
    """None = not configured or nothing new; True = MATCH (snapshot advanced); str = refused. Owner 2026-11-17: MKW
    S112M/S116M put 113 functions at 100% and were classified INFORMATION, because only KSR receipts could convert."""
    if not lane or not lane.get("match_report"):
        return None
    cur, why = match_at100(lane, product)
    if cur is None:
        return why
    snap = OUT / "match" / f"{lane['name']}.json"
    old = read_snap(snap, lane["name"])
    if old is None:
        write_snap(snap, cur)
        return f"no MATCH snapshot yet: seeded from HEAD ({len(cur)} at 100%), nothing claimed"
    lost, new = match_lost(old, cur), sorted(cur - old)
    if lost:
        return f"{len(lost)} functions dropped from 100%: {', '.join(lost[:5])}"
    if not new:
        return None
    write_snap(snap, cur)
    notes.append(f"MATCH: +{len(new)} functions at 100% ({len(cur)} total): {', '.join(new[:5])}")
    return True


def classify_progress(v: dict, product: str, base=None, lane=None) -> tuple[str, str]:
    """CERT > MATCH > CAPABILITY > INFORMATION > NONE; the first class whose evidence verifies inside base..HEAD.
    No base recorded = nothing can be anchored = NONE. Notes say why claims failed. MATCH is measured by the autopilot
    (objdiff report built at HEAD, lanes with match_report) before CERT, so its snapshot advances either way."""
    notes = [] if base else ["no generation base recorded: no pointer can be anchored"]
    m = verify_match(lane, product, notes)
    for cls, fn in (("CERT", verify_cert), ("MATCH", None), ("CAPABILITY", verify_capability),
                    ("INFORMATION", verify_information)):
        r = m if fn is None else fn(v, product, base)
        if r is True:
            return cls, "; ".join(notes)
        if isinstance(r, str):
            notes.append(f"{cls} refused: {r}")
    return "NONE", "; ".join(notes)


def _gate_path(g) -> str:
    m = GATE_PATH.search(str(g.get("cmd") or "")) if isinstance(g, dict) else None
    return m.group(0) if m else ""


def _superseded(g, n, prior=None) -> bool:
    """A red gate the judge says only fails because certificates left the pool it pins: its whole delta from the pin
    is the delta already accepted against that gate (prior, by path) plus this generation's part, which is at least 1 and
    at most its n new certificates. 2026-11-18 (KSR S169K): S168K's 9 then S169K's 43 made the delta 52, and an equality
    to 43 alone parked 43 certs. (KSR S171K): 38 new certificates, only 10 of them from the pinned pool (62 = 52 + 10)."""
    s = g.get("superseded_by_certs") if isinstance(g, dict) else None
    p = int((prior or {}).get(_gate_path(g)) or 0)
    return (type(g.get("rc")) is int and g["rc"] != 0 and type(s) is int and type(n) is int and n > 0
            and 0 < s - p <= n)


def _superseded_m(g, prior=None) -> bool:
    """A red gate the judge says only fails because functions the build now matches at 100% left the pool it pins.
    2026-11-18 (MKW S151M, Owner 'haz ambos'): test_decl_synth drifted 73 rows on in-tree build matches, 0 certificates,
    so it could not be superseded and the judge said DISAGREE. Its part of the delta must be positive here; superseded_ok
    bounds it by the functions the autopilot's own objdiff report newly shows at 100%."""
    s = g.get("superseded_by_matches") if isinstance(g, dict) else None
    p = int((prior or {}).get("m:" + _gate_path(g)) or 0)
    return type(g.get("rc")) is int and g["rc"] != 0 and type(s) is int and s - p > 0


def agree_supported(v: dict, prior=None) -> bool:
    """AGREE counts only with its own evidence: protected_ok true and every listed gate rc == 0 (at least one rc 0).
    2026-11-18 (Owner 'y', pane 08cba76c): KSR S168K certified 9 functions and two older gates that pin the pool count
    went red (POOL_COUNT 2265 != 2274), so success parked the lane. A red gate superseded by certificates (_superseded)
    is admitted here; superseded_ok then proves it in git before the verdict stands."""
    gates, n = v.get("gates"), v.get("new_canonical_certs")
    return (v.get("verdict") == "AGREE" and v.get("protected_ok") is True and isinstance(gates, list) and bool(gates)
            and all(isinstance(g, dict) and type(g.get("rc")) is int
                    and (g["rc"] == 0 or _superseded(g, n, prior) or _superseded_m(g, prior) or _pre_red(g))
                    for g in gates)
            and any(g["rc"] == 0 for g in gates))


GATE_PATH = re.compile(r"\btools/[\w./-]+\.py\b")


def superseded_record(v: dict, prior=None) -> dict:
    """The lane's accepted pool deltas by gate path after this AGREE (the next generation adds its own to them);
    match-superseded gates are kept under 'm:<path>'."""
    out = dict(prior or {})
    for g in v.get("gates") or []:
        if _superseded(g, v.get("new_canonical_certs"), prior):
            out[_gate_path(g)] = g["superseded_by_certs"]
        elif _superseded_m(g, prior):
            out["m:" + _gate_path(g)] = g["superseded_by_matches"]
    return out


def _gate_age_ok(g, product: str, base, receipts=None) -> bool:
    """The gate existed at the generation base; or (certificate gates, 2026-11-18 KSR S173K, Owner 'haz ambos': the
    generation's own test_s171k_exp.py pinned the pool at its 38-cert stage and its next 480 certs turned it red) this
    generation's last change to it is a strict ancestor of a commit that wrote its receipts, so it pinned the pool before
    those certificates and was not touched after them."""
    p = _gate_path(g)
    if not p or not base:
        return False
    b = _sha(product, base)
    if _git(product, "cat-file", "-e", f"{b}:{p}")[0] == 0:
        return True
    rc, last = _git(product, "log", "-1", "--format=%H", f"{b}..HEAD", "--", p)
    last = str(last).strip() if rc == 0 else ""
    for r in receipts or []:
        c = _sha(product, str(r.get("commit") or "")) if isinstance(r, dict) else None
        if last and c and last != c and _git(product, "merge-base", "--is-ancestor", last, c)[0] == 0:
            return True
    return False


def match_new(lane, product: str) -> tuple[int, str | None]:
    """Functions the lane's objdiff report shows at 100% beyond its MATCH snapshot, built by the autopilot at HEAD."""
    if not lane or not lane.get("match_report"):
        return 0, "the lane has no match_report"
    cur, why = match_at100(lane, product)
    if cur is None:
        return 0, why
    old = read_snap(OUT / "match" / f"{lane['name']}.json", lane["name"])
    if old is None:
        return 0, "no MATCH snapshot"
    return len(cur - old), None


def superseded_ok(v: dict, product: str, base, prior=None, lane=None) -> str | None:
    """None when no gate is superseded or every superseded gate holds; else why the AGREE cannot stand. A superseded
    gate must pass _gate_age_ok; certificates must verify in git; a match-superseded gate's part of the delta must not
    exceed the functions the autopilot's objdiff report newly shows at 100%."""
    n = v.get("new_canonical_certs")
    sup = [g for g in v.get("gates") or [] if _superseded(g, n, prior)]
    supm = [g for g in v.get("gates") or [] if g not in sup and _superseded_m(g, prior)]
    if not sup and not supm:
        return None
    for g in sup:
        if not _gate_age_ok(g, product, base, v.get("cert_receipts")):
            return (f"superseded gate {g.get('cmd')} neither existed before this generation nor was written by it "
                    "before the receipts that made it red and left unchanged after them")
    for g in supm:
        if not _gate_age_ok(g, product, base):
            return f"match-superseded gate {g.get('cmd')} is not a gate that existed before this generation"
    if sup:
        c = verify_cert(v, product, base)
        if c is not True:
            return f"superseded gates need verified certificates: {c or 'none claimed'}"
    if supm:
        new, why = match_new(lane, product)
        for g in supm:
            d = g["superseded_by_matches"] - int((prior or {}).get("m:" + _gate_path(g)) or 0)
            if d > new:
                return f"match-superseded gate {_gate_path(g)} drops {d} > {new} functions newly at 100%" + (
                    f" ({why})" if why else "")
    return None


def excluded_ok(v: dict, product: str, base) -> str | None:
    """None when every gate the judge excluded is older than the generation and unchanged by it; else why the AGREE
    cannot stand. 2026-11-18 (FIFA S170F, Owner 'y'): 33/34 gates green and F27 SUPPORTED 195/200, INCONCLUSIVE only
    because the pre-existing test_f20_leafentry needs arguments and exits 2 in the bare form the judge must use."""
    for g in v.get("excluded_gates") or []:
        p = _gate_path(g)
        if not p or not base:
            return f"excluded gate {str(g)[:120]} names no tools/ script, or the generation has no base"
        b = _sha(product, base)
        if _git(product, "cat-file", "-e", f"{b}:{p}")[0] != 0:
            return f"excluded gate {p} did not exist before this generation"
        if _git(product, "diff", "--quiet", b, "HEAD", "--", p)[0] != 0:
            return f"excluded gate {p} was changed by this generation"
    return None


# 2026-11-20 (Owner "Rojo en la base", pane 34385bd2): WIIPARTY S216W claimed 40 certificates and the judge said
# DISAGREE because 7 of 28 OLDER gates failed on rerun; S216W had not touched them. A red gate the judge marks
# "pre_existing_red" counts as not broken by this generation only when the autopilot itself observes it red, with the same
# rc, at the generation base AND at HEAD (scratch worktrees carrying copies of the product's untracked inputs), and never on
# a timeout, which observes nothing. The reruns hold cron.lock: bounded by PRE_RED_MAX gates and PRE_RED_WALL_S in total.
# LIMIT (review MEDIUM-2): git cannot show the IGNORED inputs (build/, orig/) as they were at the base, so the base run uses
# today's copies; a gate red only because this generation corrupted ignored data would read red at both. This proves the
# tracked tree, not ignored state.
PRE_RED_MAX = 8
PRE_RED_WALL_S = 3600
PRE_RED_TIMEOUT_S = 1200          # per run; replaces the judge's inner `timeout N`
TIMEOUT_RCS = (124, 137)           # coreutils timeout / SIGKILL: nothing was observed
PRE_RED_CMD = re.compile(r"(?:timeout \d+ )?python3 (tools/[\w./-]+\.py)")


def _pre_red(g) -> bool:
    return (isinstance(g, dict) and g.get("pre_existing_red") is True and type(g.get("rc")) is int
            and g["rc"] != 0)


def _untracked_inputs(product: str) -> list[str] | None:
    """Top-level ignored entries of the product (orig/, build/ ...): a scratch worktree without them fails for want of
    them, which would read as a red gate. None when git cannot say (review MEDIUM-1: never run without them)."""
    rc, out = _git(product, "status", "--ignored", "--porcelain")
    if rc != 0:
        return None
    names = {ln[3:].strip().strip('"').rstrip("/").split("/")[0] for ln in out.splitlines() if ln.startswith("!! ")}
    return sorted(n for n in names if n and n not in (".claude", "__pycache__", ".git"))


def gate_rc_at(product: str, ref: str, script: str, timeout: int, inputs=None) -> tuple[int | None, str]:
    """Run `python3 <script>` in a detached scratch worktree of `ref` with copies of the product's untracked inputs.
    (rc, tail), or (None, why) when nothing could be observed. The worktree and its directory are always removed."""
    if inputs is None:
        inputs = _untracked_inputs(product)
    if inputs is None:
        return None, "git status --ignored failed: the product's untracked inputs are unknown"
    scratch = Path(tempfile.mkdtemp(prefix="prered-", dir=str(OUT)))
    wt = scratch / "wt"
    try:
        rc, out = _git(product, "worktree", "add", "--detach", str(wt), ref)
        if rc != 0:
            return None, f"worktree add {ref[:12]} failed: {out[-200:]}"
        try:
            for n in inputs:
                src, dst = Path(product, n), wt / n
                if dst.exists() or dst.is_symlink():
                    continue  # a tracked directory holding an ignored path (tools/__pycache__): the checkout has it
                if src.is_symlink():
                    os.symlink(os.readlink(src), dst)
                elif src.is_dir():
                    shutil.copytree(src, dst, symlinks=True)
                elif src.exists():
                    shutil.copy2(src, dst)
        except OSError as e:
            return None, f"copying the untracked inputs failed: {e}"
        try:
            r = subprocess.run(["python3", script], cwd=str(wt), capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None, f"timed out after {timeout}s"
        return r.returncode, (r.stdout + r.stderr).strip()[-200:]
    finally:
        _git(product, "worktree", "remove", "--force", str(wt))
        shutil.rmtree(scratch, ignore_errors=True)
        _git(product, "worktree", "prune")


def pre_existing_ok(v: dict, product: str, base, runner=None) -> str | None:
    """None when no gate is marked pre_existing_red or every marked gate is proven red before this generation; else why
    the AGREE cannot stand."""
    gates = [g for g in v.get("gates") or [] if _pre_red(g)]
    if not gates:
        return None
    b = _sha(product, base) if base else None
    if not b:
        return "pre-existing-red gates need a recorded generation base"
    if len(gates) > PRE_RED_MAX:
        return f"{len(gates)} pre-existing-red gates > {PRE_RED_MAX}: too many to re-run under cron.lock"
    if runner is None:
        inputs = _untracked_inputs(product)  # once per judgment (review LOW-1)
        if inputs is None:
            return "git status --ignored failed: the product's untracked inputs are unknown"
        run = lambda prod, ref, script, t: gate_rc_at(prod, ref, script, t, inputs)  # noqa: E731
    else:
        run = runner
    deadline = time.monotonic() + PRE_RED_WALL_S
    for g in gates:
        cmd = str(g.get("cmd") or "").strip()
        m = PRE_RED_CMD.fullmatch(cmd)
        if not m:
            return f"pre-existing-red gate {cmd[:120]} is not a bare `python3 tools/...` gate"
        p = m.group(1)
        if _git(product, "cat-file", "-e", f"{b}:{p}")[0] != 0:
            return f"pre-existing-red gate {p} did not exist before this generation"
        if _git(product, "diff", "--quiet", b, "HEAD", "--", p)[0] != 0:
            return f"pre-existing-red gate {p} was changed by this generation"
        rcs = []
        for ref in (b, "HEAD"):
            left = int(deadline - time.monotonic())
            if left < 60:
                return f"pre-existing-red reruns exceeded {PRE_RED_WALL_S}s before {p} at {ref[:12]}"
            rc, tail = run(product, ref, p, min(PRE_RED_TIMEOUT_S, left))
            if rc is None or rc in TIMEOUT_RCS:
                return f"pre-existing-red gate {p} at {ref[:12]} observed nothing: {tail or rc}"
            rcs.append((rc, tail))
        (rb, tb), (rh, th) = rcs
        if rb == 0:
            return f"pre-existing-red gate {p} is GREEN at the generation base {b[:12]}: this generation turned it red"
        if rh == 0:
            return f"pre-existing-red gate {p} is green at HEAD when re-run by the autopilot: it is not red"
        if not _rc_consistent(rb, rh, g["rc"]):
            return f"pre-existing-red gate {p}: rc base {rb} / HEAD {rh} / judge {g['rc']} differ"
        log(f"pre-existing red proven: {p} rc {rb} at base {b[:12]} and HEAD ({tb[-80:]!r})")
    return None


def _rc_consistent(rb: int, rh: int, judge_rc: int) -> bool:
    """Red for the SAME reason before and after: base rc == HEAD rc, and == the judge's unless the judge timed out. A red
    at the base for one reason and at HEAD for a new one (rc 1 -> 3) is this generation's failure (review MEDIUM-3)."""
    return rb == rh and (judge_rc in TIMEOUT_RCS or judge_rc == rh)


UNFINISHED_MAX = 1  # consecutive continuations of checkpoints their worker marked not final


def continue_unfinished(st: dict, lane: dict, ls: dict, key: str, checkpoint: str, product: str, v: dict,
                        dry: bool) -> bool:
    """2026-11-18 (MKW S151M, Owner 'y'): the worker committed a checkpoint it marked NOT final with its own gate red;
    the judge said INCONCLUSIVE and the lane parked. Such a generation is continued from the judgment it was planned
    from, told the judge's notes, UNFINISHED_MAX times in a row (an AGREE resets it); otherwise False and the caller parks."""
    pf = ls.get("planned_from") or {}
    n = int(ls.get("unfinished_streak") or 0)
    if (v.get("verdict") != "INCONCLUSIVE" or v.get("checkpoint_final") is not False or n >= UNFINISHED_MAX
            or not isinstance(pf.get("verdict"), dict) or not pf.get("checkpoint")):
        return False
    ls["unfinished_streak"] = n + 1
    mid = ls.get("mission")
    log(f"{lane['name']}: {checkpoint} is marked not final and judged INCONCLUSIVE; continuing {ls.get('gen')} once")
    ledger_add(lane=lane["name"], kind="unfinished_continue", tokens=0, mission=mid, gen=ls.get("gen"),
               checkpoint=checkpoint)
    digest(lane["name"], f"CONTINUE {ls.get('gen')}: checkpoint not final, judge INCONCLUSIVE: "
                         f"{str(v.get('notes') or '')[:300]}")
    directive = (f"CONTINUATION of {ls.get('gen')} ({mid}): its checkpoint {checkpoint} says it is not final, and the "
                 f"judge could not agree: {str(v.get('notes') or '')[:400]}. The product holds its branch: work from "
                 "it, read that checkpoint and its evidence first, do not redo what it proved, finish what it left "
                 "open, and commit a final checkpoint before 75% of the caps is processed.")
    plan_and_arm(st, lane, ls, key, pf["checkpoint"], product, dict(pf["verdict"]), directive, {}, dry)
    return True


def design_before_park(st: dict, lane: dict, ls: dict, key: str, checkpoint: str, product: str, v: dict, pbad,
                       why: str, dry: bool) -> str | None:
    """2026-11-21 (Owner "apply the thing that makes them figure out ways before parking themselves", pane 3581ade8):
    a judge DISAGREE / INCONCLUSIVE parked the lane and it waited for the Owner to name a route. EVO now designs a lever of
    another family from the judged checkpoint first (evolve._synth_or_park: deterministic admission, SYNTH_MAX in a row
    without a conversion) and plans the next generation told the judgment, crediting nothing from it.
    Never for a protected-identity failure (the autopilot's own read or the judge's protected_ok False) and never for a
    judge call that failed: those park as before. -> None when handled (planned and armed, or a policy refusal kept in
    pending_plan); else the park reason (the design's refusal appended when there was one)."""
    if pbad or v.get("protected_ok") is False or v.get("_judge_failed"):
        return why
    levers, graph = evolve.load_levers(HOME), evolve.load_graph(HOME)
    cur = evolve.lever_by_id(levers, lane["name"], ls.get("lever"))
    fam = (cur or {}).get("family") or "UNREGISTERED"
    snap = design_snap(ls)  # review 0ba4 MEDIUM-1: an envelope/budget park before the arm restores what the design moved
    d = evolve._synth_or_park(ls, levers, lane["name"], product, fam, None if dry else lever_designer(lane, checkpoint, product),
                              checkpoint, why, f"judge {v.get('verdict')} (design before park)")
    persist_designed(lane, d, levers, dry)
    note_extensions(lane["name"], ls)
    ledger_add(lane=lane["name"], kind="evo_decision", tokens=0, cls=f"JUDGE_{v.get('verdict')}", instruments=[],
               action=d["action"], why=d["why"][:300], lever=(d.get("lever") or {}).get("id"), mode=ls.get("mode"),
               selection=evolve.selection_evidence(d.get("lever"), graph))
    digest(lane["name"], f"EVO after judge {v.get('verdict')}: {d['action']}: {d['why'][:300]}")
    if d["action"] != "research":
        return d["why"]
    ls["next_lever"] = d["lever"]["id"]
    owner_queue(lane["name"], f"NOTICE (no action needed): {why[:300]}; instead of parking, the next generation researches "
                              f"designed lever {d['lever']['id']} and is told the judgment")
    pre = (f"PREVIOUS GENERATION NOT AGREED: the independent judge said {v.get('verdict')} on {checkpoint}: "
           f"{str(v.get('notes') or '')[:500]}. Nothing it claimed is credited (no certificate, capability or "
           "information counts from it). Read the judge's reasons first, build on nothing it left unverified, and answer "
           "them where the new lever touches them.")
    # review 0ba4 MEDIUM-2: the next generation's base holds this not-agreed generation's commits, so a gate it left red
    # would read as red "at base". Until an AGREE stands, pre-existing red is proven at the last base before it.
    ls.setdefault("not_agreed_base", ls.get("base"))
    plan_and_arm(st, lane, ls, key, checkpoint, product, v, (pre + "\n\n" + d.get("directive", "")).strip(), snap, dry)
    return None


DESIGN_SNAP_KEYS = ("mode", "next_lever", "synth_streak", "research_fail", "repair", "escape_streak")


def design_snap(ls: dict) -> dict:
    """What design_before_park moves (evolve._synth_or_park + next_lever), as plan_and_arm's `snap`: restored when the
    plan parks at the envelope or a budget gate before arming, so the re-judge does not count a design that never ran."""
    s = {k: ls.get(k, 0) for k in ("blank", "info_streak", "no_conversion")}
    s.update({k: ls.get(k) for k in DESIGN_SNAP_KEYS})
    return s


def prered_base(ls: dict):
    """The base pre_existing_ok proves a red gate at: the last base before a not-agreed generation, else the lane's."""
    return ls.get("not_agreed_base") or ls.get("base")


JUDGE_TOOLS = ["Read", "Grep", "Glob", "Bash(timeout 600 python3 tools/:*)", "Bash(python3 tools/:*)",
               "Bash(sha256sum:*)", "Bash(wc:*)", "Bash(git log:*)", "Bash(git status:*)", "Bash(git show:*)",
               "Bash(ls:*)"]


def owner_exclusion_text(ls: dict, checkpoint: str) -> str:
    """2026-11-21 (Owner "Excepción puntual", pane 34385bd2): WIIPARTY S216W's old gate tools/test_wp_lib_donor2.py
    relinks main.dol per mutant and no longer finishes in 1 h since the factory's ~2,000 units (114 s before), and no S216W
    certificate depends on it. The Owner excluded it for that checkpoint only: lane state `owner_excluded` {checkpoint
    (a path suffix), gates [tools/...py], why} is told to the judge once, and excluded_ok still proves each gate predates
    the generation and is unchanged by it. Empty when nothing matches."""
    oe = ls.get("owner_excluded") or {}
    ck = str(oe.get("checkpoint") or "")
    gates = [str(g) for g in oe.get("gates") or [] if GATE_PATH.fullmatch(str(g))]
    out = ""
    if ck and gates and str(checkpoint).endswith(ck):
        out += ("\n\nOWNER RULING (recorded by the autopilot from the Owner, not by the checkpoint): for THIS checkpoint only, "
                f"the Owner excluded {', '.join(gates)} ({str(oe.get('why') or '')[:300]}). Do not run it; list it under "
                "\"excluded_gates\" with why \"Owner ruling\". Every other rule above still applies to every other gate.\n")
    # 2026-11-21 (Owner "Standing exclusion", pane 3581ade8): the one-off above recurred on the very next WIIPARTY
    # judgment (S226W reran lib_donor2 as pre-existing red for ~1 h under cron.lock). `owner_excluded_standing`
    # {gates, why} applies to EVERY checkpoint of the lane and is never consumed; excluded_ok still proves each gate
    # predates the generation and is unchanged by it, and it is never the evidence of a pointer.
    so = ls.get("owner_excluded_standing") or {}
    sg = [str(g) for g in so.get("gates") or [] if GATE_PATH.fullmatch(str(g)) and str(g) not in gates]
    if sg:
        out += ("\n\nSTANDING OWNER RULING (recorded by the autopilot from the Owner, not by the checkpoint): for every "
                f"checkpoint of this lane the Owner excluded {', '.join(sg)} ({str(so.get('why') or '')[:300]}). Do not run "
                "it and never mark it pre_existing_red; list it under \"excluded_gates\" with why \"Owner ruling\". Every "
                "other rule above still applies to every other gate.\n")
    return out


def apply_standing_exclusion(v: dict, ls: dict) -> list[str]:
    """A gate under the lane's standing Owner exclusion that the judge still listed (red, pre_existing_red or not) moves
    to excluded_gates (why "Owner ruling (standing)"), so it is never re-run at base and HEAD under cron.lock. excluded_ok
    then proves it predates the generation and is unchanged by it. Returns the moved gate paths."""
    so = {str(g) for g in (ls.get("owner_excluded_standing") or {}).get("gates") or [] if GATE_PATH.fullmatch(str(g))}
    if not so or not isinstance(v.get("gates"), list):
        return []
    keep, moved = [], []
    for g in v["gates"]:
        m = PRE_RED_CMD.fullmatch(str(g.get("cmd") or "").strip()) if isinstance(g, dict) else None
        if m and m.group(1) in so:
            moved.append(m.group(1))
        else:
            keep.append(g)
    if moved:
        v["gates"] = keep
        v["excluded_gates"] = list(v.get("excluded_gates") or []) + [
            {"cmd": f"python3 {p}", "why": "Owner ruling (standing)"} for p in moved]
    return moved


NOT_FINAL_RE = re.compile(r"^[ \t>*_-]*CHECKPOINT_FINAL[*_]*\s*[:=]\s*[*_`]*\s*(false|no)\b", re.I | re.M)
# Review M3 (2026-11-22, pane a52cc240): a checkpoint that kept an interim `CHECKPOINT_FINAL: false` and later says
# `true` is final. Only the LAST declaration counts.
FINAL_DECL_RE = re.compile(r"^[ \t>*_-]*CHECKPOINT_FINAL[*_]*\s*[:=]\s*[*_`]*\s*(true|yes|false|no)\b", re.I | re.M)


def declared_not_final(checkpoint: str, product: str) -> str | None:
    """T1 O3 (judgment executability): a checkpoint that DECLARES itself not final, in the machine line
    `CHECKPOINT_FINAL: false`, is not judged by a model (the FIFATC S261C judge spent 183,084 tokens to read that). None =
    no declaration or unreadable: the judge runs as before (prose saying "interim" is still the judge's to read)."""
    p = Path(checkpoint)
    p = p if p.is_absolute() else Path(product) / p
    try:
        text = p.read_text(errors="replace")
    except OSError:
        return None
    decls = list(FINAL_DECL_RE.finditer(text))
    m = decls[-1] if decls else None
    if not m or not NOT_FINAL_RE.match(m.group(0)):
        return None  # no declaration, or the last one says final: the judge runs
    return (f"JUDGMENT_NOT_EXECUTABLE: {p.name} declares '{m.group(0).strip()}' "
            "(deterministic, no judge call)")


POOL_FLOOR_RE = re.compile(r"^[ \t>*_`-]*POOL_FLOOR[*_`]*\s*:\s*[*_`]*\s*([\w.\-/]+)\s+count\s+(\d+)\s+floor\s+(\d+)"
                           r"(?:[*_`]*\s+via\s+python3?\s+([\w.\-/]+\.py))?", re.I | re.M)
J0_TIMEOUT = 300  # one re-count under cron.lock; a tool slower than this is unobserved, and the judge decides


def pool_floor_below(checkpoint: str, product: str) -> list[dict]:
    """W3 (Owner 2026-11-22 '(b) Count-first P1', pane a52cc240): the machine lines `POOL_FLOOR: <name> count <N> floor
    <F>` of a checkpoint whose count is below its floor. [] = no such line, or the file is unreadable. Measurement only: the
    judge still runs (skipping it would bypass its protected-identity and gate checks for ~0.4M)."""
    p = Path(checkpoint)
    p = p if p.is_absolute() else Path(product) / p
    try:
        text = p.read_text(errors="replace")
    except OSError:
        return []
    return [dict({"name": m.group(1), "count": int(m.group(2)), "floor": int(m.group(3))},
                 **({"tool": m.group(4)} if m.group(4) else {}))
            for m in POOL_FLOOR_RE.finditer(text) if int(m.group(2)) < int(m.group(3))]


def count_via_tool(product: str, ref: str, tool, name: str, runner=None) -> tuple[int | None, int | None, str]:
    """T2 W2: (count, floor, why) from the `POOL_FLOOR: <name> ...` line that a COMMITTED counting tool prints when run
    bare at `ref` in a scratch worktree (gate_rc_at). (None, None, why) when the tool is not a relative .py path, is
    absent at that ref, fails, times out, or prints no line for `name`: unobserved is never a count."""
    t = str(tool or "").strip()
    if not t.endswith(".py") or t.startswith(("/", "-")) or ".." in Path(t).parts:
        return None, None, f"not a relative .py tool path: {t[:80]!r}"
    sha = _sha(product, ref)
    if not sha:
        return None, None, f"{ref} does not resolve in {product}"
    if _git(product, "cat-file", "-e", f"{sha}:{t}")[0] != 0:
        return None, None, f"{t} is not committed at {sha[:12]}"
    rc, tail = (runner or gate_rc_at)(product, sha, t, J0_TIMEOUT)
    if rc is None:
        return None, None, f"{t} unobserved: {tail[:160]}"
    if rc != 0:
        return None, None, f"{t} rc {rc}: {tail[-160:]}"
    for m in POOL_FLOOR_RE.finditer(tail):
        if m.group(1) == name:
            return int(m.group(2)), int(m.group(3)), "ok"
    return None, None, f"{t} printed no POOL_FLOOR line for {name}"


def j0_pool_floor(lane: dict, checkpoint: str, product: str, runner=None) -> dict | None:
    """T2 W2 (a) J0: a below-floor halt is INSTRUMENT_FAIL(population) with no model call only when EVERY below-floor line
    names `via python3 <tool>`, that tool re-counts the same count and floor at the product's HEAD, and the protected
    identities are intact. Anything else is JUDGE. None = no below-floor line. SHADOW: the caller only logs it."""
    below = pool_floor_below(checkpoint, product)
    if not below:
        return None
    why = []
    for b in below:
        if not b.get("tool"):
            why.append(f"{b['name']}: no `via python3 <tool>`")
            continue
        n, f, w = count_via_tool(product, "HEAD", b["tool"], b["name"], runner)
        if n is None:
            why.append(f"{b['name']}: {w}")
        elif (n, f) != (b["count"], b["floor"]):
            why.append(f"{b['name']}: re-count {n} floor {f} != declared {b['count']} floor {b['floor']}")
    pbad = protected_check(lane)
    if pbad:
        why.append(pbad)
    return {"j0": "JUDGE" if why else "INSTRUMENT_FAIL(population)", "why": [w[:200] for w in why[:4]],
            "pools": [b["name"] for b in below]}


def j0_shadow_agreements(rows=None) -> int:
    """Live J0 verdicts of INSTRUMENT_FAIL(population) that the judge, called anyway, agreed with (AGREE, naming an
    instrument failure). ENFORCE is an Owner act after 3 (plan T2 W2, sequential stopping)."""
    return sum(1 for r in (ledger_rows() if rows is None else rows)
               if r.get("kind") == "j0_shadow" and r.get("agree") is True)


def prearm_shadow(lane: dict, name: str, product: str, p: dict, runner=None) -> dict | None:
    """T2 W2 (b): a plan whose `precheck` {name, tool, floor} cites a counting tool ALREADY committed in the product is
    counted at HEAD before arming. SHADOW: one 0-token `prearm_shadow` row says what enforcement would do (REPLAN below
    the floor, ARM at or above it, UNOBSERVED when no count was read); the generation is armed either way."""
    pc = p.get("precheck")
    if not isinstance(pc, dict):
        return None
    pool, tool = str(pc.get("name") or ""), pc.get("tool")
    try:
        floor = int(pc.get("floor"))
    except (TypeError, ValueError):
        floor = None
    if not pool or floor is None:
        n, f, why = None, None, f"malformed precheck: {json.dumps(pc)[:160]}"
    else:
        n, f, why = count_via_tool(product, "HEAD", tool, pool, runner)
    row = {"gen": name, "pool": pool, "tool": str(tool or "")[:120], "floor": floor, "count": n, "tool_floor": f,
           "would": "UNOBSERVED" if n is None else ("REPLAN" if n < floor else "ARM"), "why": why[:200]}
    ledger_add(lane=lane["name"], kind="prearm_shadow", tokens=0, **row)
    log(f"{lane['name']}: pre-arm shadow {name}: {pool} count {n} floor {floor} -> would {row['would']} ({why[:120]})")
    return row


def book_pool_floor_halt(lane: dict, checkpoint: str, product: str) -> int:
    """One ledger row `pool_floor_halt` (0 tokens) per below-floor line of a checkpoint, once per (lane, checkpoint):
    a re-judgment of the same checkpoint books nothing. Returns the rows booked."""
    below = pool_floor_below(checkpoint, product)
    if not below:
        return 0
    name = lane.get("name")
    if any(r.get("kind") == "pool_floor_halt" and r.get("lane") == name and r.get("checkpoint") == checkpoint
           for r in ledger_rows()):
        return 0
    for b in below:
        ledger_add(lane=name, kind="pool_floor_halt", tokens=0, checkpoint=checkpoint, **b)
    log(f"{name}: {checkpoint} halted below its declared floor: "
        + ", ".join(f"{b['name']} {b['count']} < {b['floor']}" for b in below))
    return len(below)


def judge(lane: dict, checkpoint: str, product: str, ruling: str = "") -> dict:
    try:
        book_pool_floor_halt(lane, checkpoint, product)
    except Exception as e:  # noqa: BLE001 -- a measurement never blocks a judgment
        log(f"{lane.get('name')}: pool_floor_halt not booked: {e!r}")
    nf = declared_not_final(checkpoint, product)
    if nf:
        log(f"{lane.get('name')}: {nf}")
        return {"verdict": "INCONCLUSIVE", "checkpoint_final": False, "notes": nf, "_tokens": 0, "_session": None,
                "_not_executable": True}
    j0 = None
    try:  # T2 W2 (a) SHADOW: decided before the model call, booked beside its verdict; once per (lane, checkpoint)
        if not any(r.get("kind") == "j0_shadow" and r.get("lane") == lane.get("name")
                   and r.get("checkpoint") == checkpoint for r in ledger_rows()):
            j0 = j0_pool_floor(lane, checkpoint, product)
    except Exception as e:  # noqa: BLE001 -- a shadow never blocks a judgment
        log(f"{lane.get('name')}: j0 shadow failed: {e!r}")
    prompt = (HOME / "judge_prompt.md").read_text().replace("{CHECKPOINT}", checkpoint).replace("{PRODUCT}", product)
    prompt += ruling
    # 2026-11-19 (pane 08cba76c): the judge's bare gate runs rewrote tracked evidence (MKW s184m/seq_gate_run.json,
    # FIFA f3x/gate_mutants.json); the dirty product held S191M's and S196F's launch ~6 h (behind_dirty). The judge
    # measures, never edits: a tracked file its run dirtied is restored; one that was already dirty is left as it was.
    repos = list(dict.fromkeys([product, lane["cwd"]]))
    before = {p: _tracked_dirty(p) for p in repos}
    try:
        r = run_claude(prompt, cwd=product, tools=JUDGE_TOOLS, add_dirs=[lane["cwd"]], max_turns=60, timeout=3600)
    finally:
        for p in repos:
            if before[p] is None:
                continue
            for f in sorted((_tracked_dirty(p) or set()) - before[p]):
                _git(p, "checkout", "--", f)
                log(f"{lane.get('name')}: judge run dirtied tracked {f}; restored")
    v = last_json(r.get("result", "")) or {}
    v["_tokens"] = r.get("tokens")
    v["_session"] = r.get("session")
    if not r.get("ok") or v.get("verdict") not in ("AGREE", "DISAGREE", "INCONCLUSIVE"):
        v["verdict"] = "INCONCLUSIVE"
        v["notes"] = r.get("error") or "judge reply did not end with a verdict JSON"
        v["_judge_failed"] = True  # the instrument failed, not the generation: never answered with a designed lever
    if j0:
        try:
            inst = [str(f.get("instrument") or "")[:80] for f in v.get("instrument_failures") or [] if isinstance(f, dict)]
            agree = (None if j0["j0"] != "INSTRUMENT_FAIL(population)"
                     else bool(v.get("verdict") == "AGREE" and inst and not v.get("_judge_failed")))
            ledger_add(lane=lane.get("name"), kind="j0_shadow", tokens=0, checkpoint=checkpoint, j0=j0["j0"],
                       why=j0["why"], pools=j0["pools"], judge_verdict=v.get("verdict"), judge_instruments=inst,
                       agree=agree)
            log(f"{lane.get('name')}: j0 shadow {j0['j0']} vs judge {v.get('verdict')} {inst}: agree={agree}; "
                f"{j0_shadow_agreements()} live agreement(s), ENFORCE is the Owner's after 3")
        except Exception as e:  # noqa: BLE001
            log(f"{lane.get('name')}: j0 shadow not booked: {e!r}")
    return v


def planner_prompt(lane: dict, name: str, checkpoint: str, product: str, verdict: dict,
                   evo_directive: str = "") -> str:
    return ((HOME / "planner_prompt.md").read_text().replace("{NAME}", name).replace("{LANE}", lane["name"])
              .replace("{CHECKPOINT}", checkpoint).replace("{PRODUCT}", product)
              .replace("{VERDICT}", json.dumps({k: v for k, v in verdict.items() if not k.startswith("_")})[:3000])
              .replace("{DIGEST}", str(OUT / "digest.md")).replace("{BRIEF}", str(HOME / "brief.md"))
              .replace("{EVOLUTION}", evo_directive or "EVO: no method transition this generation.")) \
        + rulings_block(lane["name"])


def plan(lane: dict, name: str, checkpoint: str, product: str, verdict: dict, evo_directive: str = "") -> dict:
    prompt = planner_prompt(lane, name, checkpoint, product, verdict, evo_directive)
    r = run_claude(prompt, cwd=product, tools=["Read", "Grep", "Glob", "Bash(git log:*)", "Bash(ls:*)"],
                   add_dirs=[lane["cwd"], "/home/kobii/missions/gen3-pp", "/home/kobii/missions/recon-general", str(HOME)],
                   max_turns=50, timeout=3600)
    p = last_json(r.get("result", "")) or {}
    p["_tokens"] = r.get("tokens")
    return p


def design_lever(lane: dict, checkpoint: str, product: str, family, refused=None) -> dict | None:
    """One read-only model call that designs the next lever from the residual (evolve.synthesize admits it). Owner
    2026-11-16 (pane 08cba76c): a lane that has no admissible lever designs one instead of waiting on the Owner.
    2026-11-18 (Owner 'y', pane 08cba76c): KSR's design reused the id ksr_handsource_regalloc, which sat past the 12,000-
    char cut of {LEVERS}, and the lane parked. Every existing id is now listed whole, and `refused` (the admission's
    reasons) asks for a second design."""
    all_levers = evolve.load_levers(HOME)
    levers = all_levers.get(lane["name"], [])
    ids = sorted({str(x.get("id")) for xs in all_levers.values() if isinstance(xs, list) for x in xs if isinstance(x, dict)})
    prompt = ((HOME / "lever_designer_prompt.md").read_text().replace("{LANE}", lane["name"])
              .replace("{CHECKPOINT}", checkpoint).replace("{PRODUCT}", product).replace("{FAMILY}", str(family))
              .replace("{LEVERS}", json.dumps(levers)[:12000]).replace("{BRIEF}", str(HOME / "brief.md"))
              .replace("{DIGEST}", str(OUT / "digest.md")))
    prompt += f"\n\nExisting lever ids (every lane; never reuse one): {', '.join(ids)}\n"
    if refused:
        prompt += ("\nYOUR PREVIOUS DESIGN WAS REFUSED by the deterministic admission: " + "; ".join(refused)[:1200] +
                   "\nDesign again so that every refusal is answered: a new id, the residual cited in 'what'.\n")
    r = run_claude(prompt, cwd=product, tools=["Read", "Grep", "Glob", "Bash(git log:*)", "Bash(ls:*)"],
                   add_dirs=[lane["cwd"], "/home/kobii/missions/gen3-pp", "/home/kobii/missions/recon-general", str(HOME),
                             "/home/kobii/wsr-decomp", "/home/kobii/missions/mkw-lib", "/home/kobii/missions/mkw-decomp"],
                   max_turns=40, timeout=2400)
    tok, measured = call_tokens(r.get("tokens"))
    ledger_add(lane=lane["name"], kind="lever_design", tokens=tok, measured=measured)
    return last_json(r.get("result", ""))


def lever_designer(lane: dict, checkpoint: str, product: str):
    """The designer callable evolve.synthesize takes; looked up at call time so the gate can stub design_lever."""
    def des(family):
        return design_lever(lane, checkpoint, product, family)
    des.retry = lambda family, refused: design_lever(lane, checkpoint, product, family, refused=refused)
    return des


def persist_designed(lane: dict, d: dict, levers: dict, dry: bool) -> None:
    """A lever the autopilot designed goes into levers.json (origin "autopilot") and the Owner queue (a notice, not a
    gate: the lane does not wait)."""
    lv = d.get("lever") or {}
    if lv.get("origin") != "autopilot" or dry:
        return
    evolve.save_levers(HOME, levers)
    ledger_add(lane=lane["name"], kind="lever_designed", tokens=0, lever=lv["id"], family=lv.get("family"))
    owner_queue(lane["name"], f"NOTICE (no action needed): autopilot designed lever {lv['id']} ({lv.get('family')}) and "
                              f"researches with it: {str(lv.get('what'))[:300]}")


HEADER = """# {name}: {title} (Ascension Autopilot, lane {lane}; Owner typed authorization 2026-11-11, laptop pane d957c937)

Mission terms: open-ended reconstruction, method evolution, independent certification, constitutive baseline ratchet.

Authority: this generation's own mission record, <= {cap}M processed (sum of the phase caps; closeout included), fresh <= 1M only
where a phase names it, USD 0, no push. Per-phase caps in each phase line, measured from the record spend at phase start.
Owner standing rulings OR-1..OR-6 in the brief apply; a residual's next route is never an Owner question (OR-4).
NOT authorised: writes to pinned stages (ksrmb-20261001-101754, ksrmb-s25-20261111-140212) or any EXISTING receipts file
(cert1-ksr 8,687, cert1-ksr-s25stage, Tennis receipts); KSR/Tennis frontier files; certify.py / cert_cxx.py / ksr_lane rules
and existing profiles; the canonical ctx; canonical headers, splits.txt and symbols.txt except under OR-3 (full build
passes and no function leaves 100% in the objdiff report); H2; R2; merging counters into any headline; revoking any certificate
(contradictions go to the Owner queue); push; paid or cloud usage; any budget change. A NEW additive profile is allowed only
with ALL S26C conditions: independent target oracle on original DOL bytes, frozen pilot committed before the draw, pre/post
controls, A2 negatives, historical receipts byte-identical, separate counters. UNKNOWN and INSTRUMENT_FAIL are never zero;
BINARY_EXACT becomes CERTIFIED only under OR-1: the exact match is confirmed by an independent oracle on the original
bytes, and its receipts go in this generation's own receipts file, registered in receipt_registry.json. Every gate has
planted mutants that must turn it red. Freeze before you judge.

Facts (from the planner; re-derive, do not trust):
{facts}

Phases (the only phases of this generation):
"""


def _one_line(s, limit: int) -> str:
    return " ".join(str(s or "").split())[:limit]


def planner_strings(p: dict) -> tuple[list[str], str, str, list[str]]:
    """(phases, command_notes, title, facts) exactly as they will be written -- the policy judges these bytes."""
    phases = [str(l).strip() for l in (p.get("phases") or []) if str(l).strip()]
    facts = [_one_line(f, 300) for f in (p.get("facts") or [])[:12]]
    return phases, _one_line(p.get("command_notes"), 600), _one_line(p.get("title") or "next generation", 120), facts


def packet_text(lane: dict, name: str, p: dict) -> str:
    phases, _, title, facts = planner_strings(p)
    caps = sum(float(CAP_RE.findall(l)[0]) for l in phases)
    body = HEADER.format(name=name, title=title, lane=lane["name"], cap=f"{caps:g}",
                         facts="\n".join(f"- fact: {f}" for f in facts) or "- fact: (none given)")
    return body + "\n".join(phases) + "\n"


def write_packet(lane: dict, name: str, text: str) -> Path:
    path = Path(lane["cwd"]) / lane["packet_dir"] / f"{name}-PHASES.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


SLIM_LOOP = ("Then execute the packet's phases yourself, in order, one at a time (this worker has no slash commands "
             "and no GSD re-orientation): for each phase do its work, commit its evidence, record its measured spend "
             "and status in .planning/STATE.md, and go on to the next only when it is done or at its cap.")


SLIM_PILOT_MAX = 2  # Owner 2026-11-22: "arm 2 WIIPARTY generations"; lanes.json `worker_profile_max` overrides


def worker_profile(lane: dict, rows=None) -> str | None:
    """T2 W3b pilot (Owner 'slim-t2 + inline loop', '12-hook list'): lanes.json `worker_profile: "slim-asc"` arms that
    lane's generations as slim workers. Absent or null = the default launch (the kill switch); any other value is
    ignored, so a typo never arms an unvetted profile. Bounded: after SLIM_PILOT_MAX successful `worker_profile_set`
    rows on the lane, the default launch returns by itself (the pilot runs unattended overnight)."""
    if lane.get("worker_profile") != "slim-asc":
        return None
    done = sum(1 for r in (ledger_rows() if rows is None else rows)
               if r.get("kind") == "worker_profile_set" and r.get("lane") == lane.get("name") and r.get("ok") is True)
    return "slim-asc" if done < int(lane.get("worker_profile_max") or SLIM_PILOT_MAX) else None


def command_text(lane: dict, name: str, packet: Path, notes: str) -> str:
    rel = packet.relative_to(lane["cwd"])
    run = SLIM_LOOP if worker_profile(lane) else f"Then run /gsd-autonomous on the {name} milestone in .planning."
    return (f"Execute {name} of the Ascension programme (Autopilot lane {lane['name']}; open-ended reconstruction, method "
            f"evolution, independent certification). This cwd ({lane['cwd']}) is the CONTROL repo; the PRODUCT is "
            f"{lane['product']}. FIRST read {rel} in full (authority, NOT-authorised list, facts, phases with caps); it binds. "
            f"{run} {notes} "
            "Freeze in a commit before anything judged on it; gates with planted mutants; micro-commit owned files only and "
            "never stage pre-existing dirty residue; keep a budget.md with measured spend per phase (gsd_mission.py topology "
            "--mission <this mission>); stop a phase at its cap; no push, no paid API. Each tool call costs ~120k processed "
            "tokens (the resident context is re-read): commit evidence as you go, never leave results uncommitted, and "
            "commit the checkpoint (or a pivot residual) before 75% of the authority is processed. Count before you spend: "
            "the phase that freezes a population with a declared floor writes the machine line `POOL_FLOOR: <name> count "
            "<N> floor <F>` into its evidence (append ` via python3 tools/<x>.py` when a committed tool, run bare, prints "
            "that same line as its last line); when N < F, stop the generation there (no further phase) and commit an "
            "INSTRUMENT_FAIL (population) checkpoint carrying that line and `CHECKPOINT_FINAL: true`. At the end: "
            "gsd_mission.py checkpoint "
            f"CHECKPOINT_COMPLETE with an evidence checkpoint file for {name} that states new canonical certificates (per "
            "profile, by function identity) and validated capabilities. The checkpoint carries one machine line, "
            "`CHECKPOINT_FINAL: true` or `CHECKPOINT_FINAL: false` (false = work remains: it is continued, not judged).")


def envelope_admits(lane: dict, rows: list[dict], caps: int) -> str | None:
    """An Owner envelope on one lane (lanes.json "envelope": {"tokens", "since", "note"}): everything the ledger books
    for this lane since `since` (judge, plan, reserves, overruns, refunds) plus the next generation's caps must fit.
    None = admitted (or no envelope). Global day/total caps still apply on top (budget_admits)."""
    env = lane.get("envelope")
    if not env:
        return None
    since, cap = float(env["since"]), int(env["tokens"])
    used = sum(int(r.get("tokens") or 0) for r in rows
               if r.get("lane") == lane["name"] and float(r.get("ts") or 0) >= since)
    if used + caps <= cap:
        return None
    return f"{lane['name']} envelope {cap:,} ({env.get('note', '')}): {used:,} booked since it opened + {caps:,} > {cap:,}"


# Owner 2026-11-13 ("sí", pane c84eb8e1): S37K sat 2 h 50 min on a cost hold inside the 300M KSR envelope while it was
# certifying. A cost hold is topped up by the autopilot only inside an Owner envelope that names its Owner turn, only
# while the generation keeps registering certificates, at most MAX_TOPUPS per generation; otherwise the Owner hears once.
TOPUP = 6_000_000
MAX_TOPUPS = 2
PROGRESS_FILE = "evidence/ascension/receipt_registry.json"  # every new receipts file gets an entry (brief, one coordinator)


def certified_since(product: str, base) -> bool:
    """True when the receipt registry changed in base..HEAD (a new certificate file was registered this generation)."""
    return bool(base) and _git(product, "diff", "--quiet", str(base), "HEAD", "--", PROGRESS_FILE)[0] == 1


# Spec ascension-autopilot-stall-fixes (Owner "y" 2026-11-16, pane 4de9b293). Measured 2026-11-15: 93-97% of what a
# generation "processes" is cache reads (~120k per tool call), so a 10M generation is cut off before its certification
# phase and a certificate-only top-up can never fund that phase.
AGE_MIN_H = 1.5     # F2: a top-up on a mission with less wall than this also extends the wall (one Owner act)
AGE_EXTEND_H = 4.0


def gen_head(rec: dict) -> str | None:
    """HEAD of the generation's work tree (gsd_mission binding), else the binding's recorded head. A mission with no
    binding works in its work_dir (or cwd) itself: that HEAD. 2026-11-16 S77M: unbound, 6 commits in the product
    (35/40 held-out at 100) read as 0 commits and its cost-hold top-up was refused as 'no proven progress'."""
    b = rec.get("binding") or {}
    root = b.get("root")
    h = _sha(root, "HEAD") if root and Path(root).exists() else None
    h = h or (b.get("head") if SHA_RE.match(str(b.get("head") or "")) else None)
    if h or b:
        return h
    wd = rec.get("work_dir") or rec.get("cwd")
    return _sha(wd, "HEAD") if wd and Path(wd).exists() else None


def branch_commits(product: str, since, head) -> int:
    """Commits in since..head (0 when unknown: unknown is never progress)."""
    if not since or not head or since == head:
        return 0
    rc, out = _git(product, "rev-list", "--count", f"{since}..{head}")
    out = out.strip()
    return int(out) if rc == 0 and out.isdigit() else 0


def progressed_since(product: str, ls: dict, rec: dict) -> str | None:
    """F1: proven progress since the generation began or the last top-up: >= 1 new commit on the generation branch AND
    a gsd_mission cost_mark (progress fingerprint moved) after the last top-up. Returns the range text, else None."""
    since, head = ls.get("topup_head") or ls.get("base"), gen_head(rec)
    n = branch_commits(product, since, head)
    if n < 1:
        return None
    if float((rec.get("cost_mark") or {}).get("at") or 0) <= float(ls.get("topup_at") or 0):
        return None
    return f"{str(since)[:12]}..{str(head)[:12]} ({n} commits)"


def hours_left(rec: dict, now: float) -> float:
    """Wall left before gsd_mission halts the mission on age (its rule: now - created_at - waited_s > max_hours)."""
    mh = float(rec.get("max_hours") or 24.0)  # gsd_long_run.DEFAULT_MAX_HOURS when the record carries none (review L1)
    used = now - float(rec.get("created_at") or now) - int(rec.get("waited_s") or 0)
    return mh - used / 3600


def cost_topup(st: dict, lane: dict, ls: dict, mid: str, rec: dict, hold: dict, dry: bool) -> None:
    key = f"{mid}:{hold.get('set_at')}"
    if ls.get("topup_for") == key:
        return "REFUSED" if ls.get("topup_refused") == key else None
    env, n, ln = lane.get("envelope") or {}, int(ls.get("topups") or 0), lane["name"]
    rows, now, basis = ledger_rows(), _now(), None
    if not env.get("owner_turn"):
        why = "the lane has no Owner envelope naming its Owner turn"
    elif n >= MAX_TOPUPS:
        why = f"{n} top-ups already in this generation (max {MAX_TOPUPS})"
    else:
        if certified_since(lane["product"], ls.get("base")):
            basis = "certificates registered this generation"
        else:
            prog = progressed_since(lane["product"], ls, rec)
            basis = f"proven progress {prog}" if prog else None
        if not basis:
            why = (f"no certificate registered since the generation began ({PROGRESS_FILE} unchanged) and no proven "
                   "progress (a new commit on the generation branch with a moved progress fingerprint)")
        else:
            why = envelope_admits(lane, rows, TOPUP)
            if not why:
                why = budget_admits(rows, now, TOPUP)
                if why and not why.startswith(PARK_REASONS):  # the day cap is a wait: decide again on a later tick
                    log(f"{ln}: cost hold on {mid}: top-up waits: {why}")
                    return
    ext = 0.0
    if not why and hours_left(rec, now) < AGE_MIN_H:  # F2: never spend a top-up on a mission minutes from its wall
        ext = round(min(AGE_EXTEND_H, (WALL - dt.datetime.fromtimestamp(now, dt.timezone.utc)).total_seconds() / 3600), 1)
        if ext < 0.5:
            why = f"mission wall {hours_left(rec, now):.1f} h left and the programme wall is too close to extend it"
            ledger_add(lane=ln, kind="topup_skipped_age", gen=ls.get("gen"), mission=mid, tokens=0)
    ls["topup_for"] = key
    if why:
        ls["topup_refused"] = key
        save_state(st)
        owner_queue(ln, f"cost hold on {mid} not topped up: {why}. Hold: {str(hold.get('reason'))[:200]}")
        return "REFUSED"
    auth = int(rec.get("authority_tokens") or 0) + TOPUP
    args = ["authority", "--mission", mid, "--tokens", str(auth)] + (["--extend-hours", f"{ext:g}"] if ext else [])
    rc, out = gm(*args, "--owner-turn", env["owner_turn"], "--reason",
                 f"Autopilot top-up {n + 1}/{MAX_TOPUPS}: +{TOPUP:,} inside the {ln} envelope ({env.get('note', '')}); "
                 f"{basis}" + (f"; wall +{ext:g} h ({hours_left(rec, now):.1f} h left)" if ext else ""), dry=dry)
    if rc != 0:
        ls["topup_refused"] = key
        save_state(st)
        owner_queue(ln, f"top-up of {mid} refused by gsd_mission: {out[-300:]}")
        return "REFUSED"
    ledger_add(lane=ln, kind="auto_topup", gen=ls.get("gen"), mission=mid, tokens=TOPUP, authority=auth,
               basis=basis[:160], extend_hours=ext or None)
    ls.update(topups=n + 1, authority=auth, topup_at=now, topup_head=gen_head(rec) or ls.get("topup_head"))
    save_state(st)
    rc, out = gm("release", "--mission", mid, dry=dry)
    log(f"{ln}: cost hold on {mid}: authority -> {auth:,} (top-up {n + 1}/{MAX_TOPUPS}, {basis[:80]})"
        + (f", wall +{ext:g} h" if ext else "") + f"; release rc={rc}")
    digest(ln, f"TOP-UP {mid}: +{TOPUP:,} -> {auth:,} inside the lane envelope ({basis})")


BREAKER_REPLAN_MAX = 2


HELD_REPLAN_S = 7200  # round 2 (Owner "hazlas todas"): MKW S338M sat 15 h on "launch held: cwd diverged"


def held_too_long(rec: dict, now: float | None = None, age: float = 0.0) -> bool:
    """A RUNNING mission with no hold whose every relaunch has been held ('launch held: ...') for HELD_REPLAN_S.
    Round 2c (MKW 22:02Z): gsd_mission renewed the aged-out m-c32ebb609572 as m-905388a9fcc8, which sat PREPARED on the
    same 'launch held: cwd diverged'; a renewal that never launched is the same stall.
    Round 8: `age` is held_age (the autopilot's own first sighting); updated_at alone is reset by every gsd_mission touch."""
    now = _now() if now is None else now
    return (rec.get("state") in ("RUNNING", "PREPARED") and str(rec.get("reason") or "").startswith("launch held")
            and max(float(age or 0), now - float(rec.get("updated_at") or now)) >= HELD_REPLAN_S)


HELD_REPAIR_S = 600  # round 8: a held launch the autopilot can align mechanically is aligned after this long
HELD_CAUSE_RE = re.compile(r"^launch held:\s*([^:]*)")


def held_age(st: dict, ls: dict, mid: str, rec: dict, now: float | None = None) -> float:
    """Round 8 (Owner 2026-11-26 "aumenta autonomia para que esto se hubiera solucionado solo", pane 31498a3e): seconds
    since the autopilot FIRST saw this mission's launch held for this cause. gsd_mission rewrites updated_at on every
    touch: FIFA m-fce673ebe202 was held 'diverged' from 14:57Z, yet read 30 min at 20:40Z, so the HELD_REPLAN_S re-plan
    never fired. The sighting is kept per mission and cause in ls['held_seen'] and dropped when the hold ends."""
    now = _now() if now is None else now
    m = HELD_CAUSE_RE.match(str(rec.get("reason") or ""))
    if not m or rec.get("state") not in ("RUNNING", "PREPARED"):
        if ls.pop("held_seen", None) is not None:
            save_state(st)
        return 0.0
    key = f"{mid}:{m.group(1).strip()[:100]}"
    seen = ls.get("held_seen") if isinstance(ls.get("held_seen"), dict) else {}
    if seen.get("key") != key:
        seen = {"key": key, "since": min(now, float(rec.get("updated_at") or now))}
        ls["held_seen"] = seen
        save_state(st)
    return max(0.0, now - float(seen.get("since") or now))


def _declares_final(product: str, ref: str, path: str) -> bool:
    """The checkpoint at `ref` ends its CHECKPOINT_FINAL declarations with true/yes (the last one counts, as judged)."""
    rc, text = _git(product, "show", f"{ref}:{path}")
    decls = list(FINAL_DECL_RE.finditer(text)) if rc == 0 else []
    return bool(decls) and not NOT_FINAL_RE.match(decls[-1].group(0))


def held_final_checkpoint(lane: dict, ls: dict) -> str:
    """Round 8: the generation's own checkpoint committed on the product since its base, declaring itself final; '' when
    none. Named after the generation (checkpoint_s392f.md for S392F), so an older generation's file is never taken."""
    product, gen = lane.get("product"), str(ls.get("gen") or "").lower()
    if not product or not gen or not Path(product).is_dir():
        return ""
    ck = checkpoint_from_branch(product, ls.get("base"), "HEAD")
    return ck if ck and gen in Path(ck).name.lower() and _declares_final(product, "HEAD", ck) else ""


def held_align(st: dict, lane: dict, ls: dict, mid: str, rec: dict, dry: bool) -> str:
    """Round 8. A launch held 'cwd not aligned with work_dir' with the generation's work intact sat for hours, and the
    re-plan meant to end it would have thrown that work away: FIFATC S383C (work tree 2 commits ahead, product dirty
    only in evidence/f36/mutant_rc.json, which the branch never touches; held 'behind_dirty' 9.5 h); MKW S382M (hand
    merge 690dd855). Every tick while the launch is held (a few git reads), the product is aligned with the work tree:
      - product HEAD is an ancestor of the work-tree head and no uncommitted product change touches a path the branch
        changes -> `merge --ff-only` (git keeps the uncommitted file; it refuses an overlap itself);
      - the two sides diverged, share no changed path, and neither tree has tracked changes -> `merge --no-ff` of the
        work-tree head into the product, then the work tree is fast-forwarded to that merge (cwd == work_dir).
    A refusal is told once per mission, cause and reason; a later tick still aligns once the obstacle is gone.
    Never a reset, rebase, checkout or stash; nothing is discarded. -> 'ff' | 'merge' | '' (nothing moved)."""
    product, wd, ln = lane.get("product"), str(rec.get("work_dir") or ""), lane["name"]
    key = (ls.get("held_seen") or {}).get("key")
    if (not key or not str(rec.get("reason") or "").startswith("launch held: cwd")
            or not product or not wd or not Path(wd).is_dir() or Path(wd).resolve() == Path(product).resolve()):
        return ""

    def owner_queue(lane_name: str, text: str) -> None:  # noqa: F811 -- the module's, told once per key and reason
        tag = f"{key}:{text.split(':', 1)[-1][:60]}"
        if ls.get("held_align_told") != tag:
            ls["held_align_told"] = tag
            save_state(st)
            globals()["owner_queue"](lane_name, text)
    cur, head = _sha(product, "HEAD"), _sha(wd, "HEAD")
    if not (cur and head) or cur == head or not _sha(product, head):  # another repository's work tree: not ours
        return ""
    changed = _diff_paths(product, cur, head)
    if changed is None:
        return ""
    if _git(product, "merge-base", "--is-ancestor", cur, head)[0] == 0:
        rc, out = _git(product, "diff", "--name-only", "HEAD")
        dirty = {p.strip() for p in out.splitlines() if p.strip()} if rc == 0 else {"<git diff failed>"}
        if dirty & set(changed):
            owner_queue(ln, f"held launch of {mid} not aligned: uncommitted product changes touch the branch's paths "
                            f"{sorted(dirty & set(changed))[:3]}")
            return ""
        how, note = "ff", f"fast-forwarded the product {cur[:12]} -> {head[:12]} ({len(dirty)} uncommitted file(s) kept)"
        if not dry:
            rc, out = _git(product, "merge", "--ff-only", head)
            if rc != 0:
                owner_queue(ln, f"held launch of {mid}: fast-forward failed: {out[-200:]}")
                return ""
    else:
        rc, base = _git(product, "merge-base", cur, head)
        base = base.strip()
        both = evolve._overlap(product, base, head) if rc == 0 and base else ["<no merge base>"]
        if both or _git(product, "status", "--porcelain", "--untracked-files=no")[1] \
                or _git(wd, "status", "--porcelain", "--untracked-files=no")[1]:
            owner_queue(ln, f"held launch of {mid} not aligned: the product and its work tree diverged"
                            + (f" and both change {both[:3]}" if both else " and a tree has tracked changes"))
            return ""
        how, note = "merge", f"merged the work-tree head {head[:12]} over product {cur[:12]} (no shared paths)"
        if not dry:
            rc, out = _git(product, "-c", "user.name=kobii-gex44-mission", "-c", "user.email=mission@gex44.local",
                           "merge", "--no-ff", "-m", f"merge generation branch {head[:12]} ({ls.get('gen')}, {mid}) "
                           "over product commits (no shared files; autopilot round 8 held-launch repair)", head)
            if rc != 0:
                _git(product, "merge", "--abort")
                owner_queue(ln, f"held launch of {mid}: merge failed: {out[-200:]}")
                return ""
            new = _sha(product, "HEAD")
            rc, out = _git(wd, "merge", "--ff-only", new or "HEAD")
            if rc != 0:
                owner_queue(ln, f"held launch of {mid}: product merged as {str(new)[:12]}, work tree not "
                                f"fast-forwarded: {out[-200:]}")
    ledger_add(lane=ln, kind="held_align", tokens=0, mission=mid, gen=ls.get("gen"), how=how, head=head, was=cur)
    log(f"{ln}: held launch of {mid} ({key.split(':', 1)[-1]}): {note}")
    digest(ln, f"HELD-ALIGN {ls.get('gen')} ({mid}): {note}")
    return how


def breaker_replan(st: dict, lane: dict, ls: dict, mid: str, rec: dict, hold: dict, dry: bool,
                   cause: str = "cost") -> None:
    """Owner 2026-11-25 (laptop pane 5f1414ed, "anadele permisos al autopilot para que esto no pase mas"): a cost-breaker
    hold whose top-up was refused left the lane RUNNING with no worker, forever (WSR from 11-23, WIIPARTY 11-25), because
    only an Owner act could end the generation. The autopilot now ends it itself: the next generation is planned from the
    judgment this one was planned from (no re-judge; arm_generation closes and settles the stalled mission), told why and
    told to change route. Once per hold; BREAKER_REPLAN_MAX in a row per lane (a judged checkpoint resets the streak),
    then the lane parks visibly (park_kind breaker), never RUNNING-idle.
    Round 2 (Owner "hazlas todas", same pane): cause "held" does the same for a launch held >= HELD_REPLAN_S; and a
    re-plan that drew a policy refusal resumes from its kept plan at the next tick (before, the second tick returned on
    breaker_replan_for and the lane sat RUNNING-idle again)."""
    ln, key = lane["name"], f"{mid}:{hold.get('set_at')}"
    what = "cost hold" if cause == "cost" else "launch held"
    if ls.get("breaker_replan_for") == key:
        pend = resumable_plan(ls, key)
        if not pend or ls.get("judged_for") == key or resume_wait(pend):
            return
        ls["judged_for"] = key
        d0 = pend.get("directive") or ""
        if pend.get("bad"):
            d0 = (d0 + "\n\n" + replan_feedback(pend["bad"], pend.get("offenders"))).strip()
        log(f"{ln}: breaker re-plan of {mid} resumed from its kept plan (no re-judge)")
        save_state(st)
        return plan_and_arm(st, lane, ls, key, (ls.get("planned_from") or {}).get("checkpoint"), lane["product"],
                            dict(pend["verdict"]), d0, pend.get("snap") or {}, dry)
    ls["breaker_replan_for"] = key
    pf = ls.get("planned_from") or {}
    ck, v, n = pf.get("checkpoint"), pf.get("verdict"), int(ls.get("breaker_replans") or 0)
    if not (ck and isinstance(v, dict)):
        return _park(st, ls, ln, f"{what} on {mid} and no kept judgment to re-plan from; lane parked",
                     f"PARKED: {what} on {mid}, nothing to re-plan from", kind="breaker")
    if n >= BREAKER_REPLAN_MAX:
        return _park(st, ls, ln, f"{what} on {mid}: {n} breaker re-plans in a row without a judged checkpoint; "
                                 "lane parked for the Owner", f"PARKED: {n} breaker re-plans in a row", kind="breaker")
    ls["breaker_replans"] = n + 1
    ls["judged_for"] = key
    ledger_add(lane=ln, kind="breaker_replan", tokens=0, mission=mid, gen=ls.get("gen"), n=n + 1, checkpoint=ck,
               cause=cause)
    log(f"{ln}: {what} on {mid}: breaker re-plan {n + 1}/{BREAKER_REPLAN_MAX} from the kept judgment of {ck} "
        "(no re-judge)")
    digest(ln, f"BREAKER RE-PLAN {n + 1}/{BREAKER_REPLAN_MAX} ({what}): {ls.get('gen')} stalled; next generation "
               f"planned from {ck}")
    save_state(st)
    if cause == "cost":
        directive = (f"COST BREAKER (autopilot authority, Owner 2026-11-25): generation {ls.get('gen')} ({mid}) was "
                     f"stopped: {str(hold.get('reason'))[:300]}. Its lever {ls.get('lever')} made no proven progress (no "
                     "new commit with a moved progress fingerprint). Do not repeat that route: name a materially "
                     "different method or a smaller bounded step, cite the residual it answers, and plan it inside the caps.")
    else:
        hrs = (_now() - float(rec.get("updated_at") or _now())) / 3600
        directive = (f"LAUNCH HELD (autopilot authority, Owner 2026-11-25): generation {ls.get('gen')} ({mid}) could not "
                     f"relaunch its worker for {hrs:.1f} h: {str(hold.get('reason'))[:300]}. It is re-planned from the "
                     "same judgment: read its branch and evidence first, do not redo what it proved, and plan the rest "
                     "inside the caps.")
    return plan_and_arm(st, lane, ls, key, ck, lane["product"], dict(v), directive, design_snap(ls), dry)


def recover_interrupted_tick(st: dict, ln: str, ls: dict) -> None:
    """2026-11-25 (FIFATC S339C, disk full): a tick judged a hold, saved judged_for, then died while planning; the
    except's own save failed too, so the lane kept status RUNNING and every later tick returned on judged_for == key.
    tick_lane marks each lane's tick open on disk; a mark found at the next tick means that tick never finished:
    the judgment it left is cleared so the hold is judged (or its kept plan re-planned) again."""
    ls.pop("tick_open", None)
    jf = ls.get("judged_for")
    if ls.get("status") in ("RUNNING", "WAITING") and jf:
        ls["judged_for"] = None
        ledger_add(lane=ln, kind="tick_recovered", tokens=0, judged_for=jf)
        log(f"{ln}: the previous tick died before finishing (judged_for {jf}): cleared, the hold is taken again")
        owner_queue(ln, f"NOTICE (no action needed): an interrupted tick left judged_for {jf}; cleared and retried")
    else:
        log(f"{ln}: the previous tick died before finishing; nothing to undo ({ls.get('status')})")


WATCHDOG_S = 3 * 3600  # round 2 (Owner "hazlas todas"): WSR sat RUNNING-idle 2 days unseen


def _wd_fingerprint(ls: dict, rec: dict) -> str:
    return json.dumps([ls.get("status"), ls.get("mission"), ls.get("gen"), ls.get("judged_for"),
                       (ls.get("pending_plan") or {}).get("gen"), rec.get("state"), rec.get("updated_at"),
                       (rec.get("owner_hold") or {}).get("set_at"), (rec.get("cost_mark") or {}).get("tokens")],
                      default=str)


def watchdog(st: dict, lane: dict, ls: dict) -> None:
    """One notice when a RUNNING/WAITING lane has not changed at all for WATCHDOG_S: not its own state, not its mission's
    (state, updated_at, hold, processed tokens). It covers every silent `return` in lane_tick, known or not. Never
    parks: a day-cap or weekly wait is legitimate and is only told. Once per fingerprint."""
    ln = lane["name"]
    if ls.get("status") not in ("RUNNING", "WAITING"):
        ls.pop("wd", None)
        return
    rec = (mission(ls["mission"]) if ls.get("mission") else None) or {}
    fp, now = _wd_fingerprint(ls, rec), _now()
    wd = ls.get("wd") or {}
    if wd.get("fp") != fp:
        wd = ls["wd"] = {"fp": fp, "since": now}
    if wd.get("told") or now - float(wd["since"]) < WATCHDOG_S:
        return
    hold = rec.get("owner_hold") or {}
    why = (f"lane {ls.get('status')} gen {ls.get('gen')}, judged_for {ls.get('judged_for')}; mission "
           f"{ls.get('mission')} {rec.get('state')}, hold {hold.get('kind')}, reason: {str(rec.get('reason') or '')[:200]}")
    hrs = (now - float(wd["since"])) / 3600
    wd.update(told=now, why=why)
    ledger_add(lane=ln, kind="watchdog_idle", tokens=0, mission=ls.get("mission"), hours=round(hrs, 1))
    log(f"{ln}: WATCHDOG: nothing changed for {hrs:.1f} h ({why})")
    owner_queue(ln, f"WATCHDOG: nothing changed for {hrs:.1f} h: {why}")
    digest(ln, f"WATCHDOG idle {hrs:.1f} h: {why}")


OWN_TMP_RE = re.compile(r"^ap-(dry|test)-\w+$")
TMP_SWEEP_AGE_S = 24 * 3600
TMP_SWEEP_MAX = 2000


def sweep_own_tmp(root=None, now: float | None = None) -> int:
    """2026-11-25: 12,382 /tmp/ap-dry-* scratch dirs since 11-11 (test_autopilot's dry-tick check, ~167 per gate run)
    were never removed. Only this programme's two prefixes, only directories this user owns, only older than
    TMP_SWEEP_AGE_S (a hand-run dry-tick's scratch stays inspectable for a day), at most TMP_SWEEP_MAX per tick."""
    root = Path(root or os.environ.get("AP_SWEEP_ROOT") or tempfile.gettempdir())  # the gate points it at its own tmp
    if not root.is_dir():
        return 0
    now = time.time() if now is None else now
    uid = os.getuid() if hasattr(os, "getuid") else None
    n = 0
    with os.scandir(root) as it:
        for e in it:
            if n >= TMP_SWEEP_MAX:
                break
            try:
                if not OWN_TMP_RE.match(e.name) or not e.is_dir(follow_symlinks=False):
                    continue
                s = e.stat(follow_symlinks=False)
                if (uid is not None and s.st_uid != uid) or now - s.st_mtime < TMP_SWEEP_AGE_S:
                    continue
            except OSError:
                continue
            shutil.rmtree(e.path, ignore_errors=True)
            n += 0 if os.path.exists(e.path) else 1
    return n


DISK_FLOOR_GB = 20.0


def disk_admits() -> str | None:
    """2026-11-25: the disk was 100% full from ~06:16Z; FIFATC died mid-plan (judged_for left set), MKWLIB on ENOSPC,
    and MKW's worker spent a generation to report 'disk 4G<10G'. Below the floor no lane is ticked (nothing judged,
    planned or armed; state untouched), so nothing is left half-done for lack of space. AP_DISK_FLOOR_GB=0 = off."""
    try:
        floor = float(os.environ.get("AP_DISK_FLOOR_GB") or DISK_FLOOR_GB)
        free = shutil.disk_usage(str(OUT)).free / 2 ** 30
    except (OSError, ValueError):
        return None
    return None if free >= floor else f"disk {free:.1f}G free < floor {floor:g}G on {OUT}"


ALERT_STATUSES = ("PARKED", "STOPPED")
QUEUE_LINE_RE = re.compile(r"^- \[([^\]]+)\] (\S+): (.*)$")


def _last_queue_lines(tail_bytes: int = 400_000) -> dict:
    """lane -> (ts, text) of its last owner_queue line that is not a NOTICE or a QUESTION (the park reason)."""
    p = OUT / "owner_queue.md"
    try:
        with open(p, "rb") as f:
            f.seek(max(0, p.stat().st_size - tail_bytes))
            text = f.read().decode("utf-8", "replace")
    except OSError:
        return {}
    last = {}
    for line in text.splitlines():
        m = QUEUE_LINE_RE.match(line)
        if m and not m.group(3).startswith(("QUESTION", "NOTICE")):
            last[m.group(2)] = (m.group(1), m.group(3))
    return last


def stranded_due(rec: dict) -> bool:
    """When to look for stranded work: the mission ended, or its relaunch is held on a cwd/work_dir divergence."""
    return bool(rec) and (rec.get("state") in TERMINAL
                          or str(rec.get("reason") or "").startswith("launch held: cwd not aligned"))


def _diff_paths(product: str, a: str, b: str):
    rc, out = _git(product, "diff", "--name-only", a, b)
    return None if rc else [p.strip() for p in out.splitlines() if p.strip()]


def reconcile_stranded(lane: dict, ls: dict, rec: dict, dry: bool) -> str:
    """Round 4 (Owner 2026-11-26 "subele la autonomia"). FIFATC S364C did its work in the PREVIOUS generation's worktree
    (worktree-s359c: phases 1-3, held-out 55/60 SUPPORTED, provisional checkpoint) while the product kept only the S364C
    scaffold. gsd_mission saw "3.9M processed since the work tree last changed", cut it on cost and it was settled
    HALTED, so the lane parked over a checkpoint nobody judged. MKW S369M did the same in worktree-s362m; its relaunch
    was then held "cwd diverged" and two held re-plans re-created it.
    Commits whose subject starts with the lane's current generation, sitting on a worktree branch the product lacks,
    whose worktree is NOT this generation's own (its directory name does not start with the generation), are merged
    into the product (--no-ff, never a rewrite). This happens only when the product's own side since the merge base is
    the autopilot scaffold alone (.planning/ and the lane packet dir), the two sides share no path, and no uncommitted
    product change touches the merged paths. The worktree is then fast-forwarded to the merge, so cwd == work_dir.
    Anything else is a 'skip: ...' and nothing moves. -> '' when nothing is stranded."""
    product, gen = lane.get("product"), str(ls.get("gen") or "")
    if not gen or not product or not Path(product).is_dir():
        return ""
    pkt = str(lane.get("packet_dir") or "vault/autopilot").strip("/") + "/"
    rc, out = _git(product, "worktree", "list", "--porcelain")
    if rc:
        return ""
    wts, cur = [], {}
    for line in [*out.splitlines(), ""]:
        if not line.strip():
            if cur.get("worktree") and cur.get("branch"):
                wts.append((cur["worktree"], cur["branch"].replace("refs/heads/", "", 1)))
            cur = {}
            continue
        k, _, v = line.partition(" ")
        cur[k] = v
    me = os.path.realpath(product)
    hits = []
    for path, br in wts:
        if os.path.realpath(path) == me or Path(path).name.lower().startswith(gen.lower()):
            continue  # the product itself, or this generation's own worktree (normal work, merged at the checkpoint)
        rc, subj = _git(product, "log", "--format=%s", f"HEAD..{br}")
        if not rc and any(s.startswith(gen) for s in subj.splitlines()):
            hits.append((path, br))
    if not hits:
        return ""
    if len(hits) > 1:
        return f"skip: {gen} commits on {len(hits)} worktree branches ({', '.join(b for _, b in hits)[:200]})"
    path, br = hits[0]
    tip = _git(product, "rev-parse", br)[1].strip()
    base = _git(product, "merge-base", "HEAD", br)[1].strip()
    mine, theirs = (_diff_paths(product, base, "HEAD"), _diff_paths(product, base, tip)) if base else (None, None)
    if mine is None or theirs is None:
        return f"skip: {br} unreadable"
    beyond = [p for p in mine if not (p.startswith(".planning/") or p.startswith(pkt))]
    if beyond:
        return f"skip: the product moved beyond the scaffold since {base[:12]} ({', '.join(beyond[:3])})"
    both = sorted(set(mine) & set(theirs))
    if both:
        return f"skip: {br} and the product both touch {', '.join(both[:3])}"
    dirty = {l[3:].strip() for l in _git(product, "status", "--porcelain", "--untracked-files=no")[1].splitlines() if l.strip()}
    if dirty & set(theirs):
        return f"skip: uncommitted product changes in {', '.join(sorted(dirty & set(theirs))[:3])}"
    msg = (f"autopilot: bring {gen} work home from {br} ({len(theirs)} paths; the product side since {base[:12]} "
           "is only the scaffold)")
    if dry:
        return "DRY " + msg
    rc, o = _git(product, "merge", "--no-ff", "--no-edit", "-m", msg, br)
    if rc:
        _git(product, "merge", "--abort")
        return f"skip: merge of {br} failed: {o[-200:]}"
    m = _git(product, "rev-parse", "HEAD")[1].strip()
    rc2, o2 = _git(path, "merge", "--ff-only", m)
    ledger_add(lane=lane["name"], kind="stranded_merged", tokens=0, gen=gen, branch=br, tip=tip, merge=m,
               paths=len(theirs), worktree_ff=rc2 == 0, mission=(rec or {}).get("mission_id"))
    log(f"{lane['name']}: {msg} -> {m[:12]}; worktree {path} ff {'ok' if rc2 == 0 else 'refused: ' + o2[-120:]}")
    owner_queue(lane["name"], f"NOTICE (no action needed): {msg} -> {m[:12]}")
    return msg


ANSWERS = "answers.jsonl"  # round 3: the Owner's rulings inbox (`autopilot.py answer <LANE> <text>`), under HOME
RULINGS_MAX = 5  # newest rulings kept per lane
_RULINGS: dict = {}  # lane -> its rulings, set by tick_lane for plan() (which has no lane state)


def record_answer(lane_name: str, text: str, now: float | None = None) -> dict:
    """Round 3 (Owner 2026-11-26, KSR cohort-exclusion clause: 'autorizo y deberia tener la capacidad'). KSR's
    mission asked an Owner decision, blocked, and died on age 16 h later; the only way in was a hand-run `decide` on
    a mission that was already terminal. An answer is now one appended line here; the next tick takes it."""
    import hashlib  # noqa: PLC0415
    text = " ".join(str(text or "").split())[:1000]
    if not text:
        raise ValueError("empty answer")
    at = _now() if now is None else now
    row = {"lane": lane_name, "text": text, "at": at,
           "id": hashlib.sha1(f"{lane_name}|{text}|{at}".encode()).hexdigest()[:8]}
    with open(HOME / ANSWERS, "a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def take_answers(st: dict, names) -> int:
    """Each new complete line of answers.jsonl becomes a binding ruling on its lane (kept, newest RULINGS_MAX). A
    PARKED/STOPPED lane goes WAITING with its judgment cleared, so its last checkpoint is judged and planned again
    with the ruling in the planner prompt. The Owner answering is what unparks: an honest stall stays parked until
    they do. -> rulings taken (the caller saves the state)."""
    try:
        raw = (HOME / ANSWERS).read_text()
    except FileNotFoundError:
        return 0
    lines = raw[:raw.rfind("\n") + 1].splitlines()  # a line still being written waits for the next tick
    seen, n = int(st.get("answers_seen") or 0), 0
    for line in lines[seen:]:
        try:
            a = json.loads(line)
        except ValueError:
            log(f"owner answer line unreadable, ignored: {line[:120]!r}")
            continue
        ln = a.get("lane")
        ls = (st.get("lanes") or {}).get(ln)
        if ln not in names or ls is None or not str(a.get("text") or "").strip() or not a.get("id"):
            log(f"owner answer for unknown lane {ln!r} ignored")
            continue
        rs = [r for r in ls.get("owner_rulings") or [] if r.get("id") != a["id"]]
        rs.append({"id": a["id"], "text": str(a["text"])[:1000], "at": a.get("at") or _now(), "delivered": []})
        ls["owner_rulings"] = rs[-RULINGS_MAX:]
        was = ls.get("status")
        if was in ALERT_STATUSES:
            ls.update(status="WAITING", park_kind=None, judged_for=None)
        ledger_add(lane=ln, kind="owner_answer", tokens=0, ruling=a["id"], was=was)
        owner_queue(ln, f"NOTICE (no action needed): Owner ruling {a['id']} recorded"
                        + (f"; lane {was} -> WAITING (last checkpoint judged again with it)" if was in ALERT_STATUSES
                           else "") + f": {str(a['text'])[:200]}")
        log(f"{ln}: Owner ruling {a['id']} recorded (lane was {was})")
        n += 1
    st["answers_seen"] = len(lines)
    return n


def rulings_block(lane_name: str) -> str:
    rs = _RULINGS.get(lane_name) or []
    if not rs:
        return ""
    return ("\n\nOWNER RULINGS for this lane (binding, newest last; recorded with `autopilot.py answer`). They settle "
            "the questions they answer: plan inside them and never plan a generation that asks them again.\n"
            + "\n".join(f"- {r['id']}: {r['text']}" for r in rs))


def decide_ruling(mid: str, rid: str, text: str) -> tuple[bool, str]:
    rc, out = gm("decide", "--mission", mid, "--id", f"AP-{rid}", "--text", text, timeout=180)
    return rc == 0, out[-300:]


def deliver_rulings(ln: str, ls: dict, dry: bool) -> int:
    """Each ruling reaches the lane's live mission once, as a durable gsd_mission decision (its launch card carries it;
    a background owner that stopped to ask is resumed with it). A terminal mission is skipped: the planner carries
    the ruling into the next generation. 3 refusals per mission -> one notice, no more tries. -> delivery attempts."""
    mid, rs = ls.get("mission"), ls.get("owner_rulings") or []
    if dry or not mid or not rs:
        return 0
    rec = mission(mid) or {}
    if not rec or rec.get("state") in TERMINAL:
        return 0
    n = 0
    for r in rs:
        if mid in (r.get("delivered") or []) or (r.get("failed") or {}).get(mid, 0) >= 3:
            continue
        ok, why = decide_ruling(mid, r["id"], f"Owner ruling for lane {ln} ({r['id']}): {r['text']}")
        n += 1
        if ok:
            r["delivered"] = [*(r.get("delivered") or []), mid][-20:]
            ledger_add(lane=ln, kind="owner_ruling_delivered", tokens=0, ruling=r["id"], mission=mid)
            log(f"{ln}: Owner ruling {r['id']} delivered to {mid}")
            continue
        f = r.setdefault("failed", {})
        f[mid] = f.get(mid, 0) + 1
        log(f"{ln}: Owner ruling {r['id']} not delivered to {mid}: {why!r}")
        if f[mid] >= 3:
            owner_queue(ln, f"Owner ruling {r['id']} could not reach {mid} after 3 tries ({why[:200]}); "
                            "the planner still carries it")
    return n


def open_question(ls: dict, rec: dict) -> str:
    """The Owner decision a lane's mission asked and no ruling has answered since. '' when none."""
    bi = rec.get("blocked_intent") or {}
    if bi.get("kind") != "DECISION_REQUEST" or bi.get("answer"):
        return ""
    asked = float((rec.get("blocker") or {}).get("at") or 0)
    if any(float(r.get("at") or 0) >= asked for r in ls.get("owner_rulings") or []):
        return ""
    return str(bi.get("needs") or (rec.get("blocker") or {}).get("reason") or "Owner decision requested")[:500]


# Round 9 (Owner 2026-11-27, pane 31498a3e: "todas estas deberian haber continuado de forma autonoma toda la noche ...
# subele el nivel de autonomia brutalmente"). WIIPARTY S400W (a worktree-local `rm build; cp -a`) and WSR S405R (R2
# first or certify first, with its own recommendation) sat all night on questions the mission could settle. After
# AUTO_RULE_S unanswered, the autopilot answers through the Owner's own inbox (answers.jsonl), so the ruling is
# recorded, delivered and planned exactly like a typed one. What it never answers: a command that is not plainly
# worktree-local, and any question naming money, budget, authority, credentials, publishing or other outside effects.
AUTO_RULE_S = 1800
BRANCH_RETRY_S = 900  # a lane parked "branch" is ticked again this often (round 9)


def branch_retry_due(ls: dict) -> bool:
    """A lane parked on a git state (park_kind 'branch') with a mission is due another look every BRANCH_RETRY_S."""
    return (ls.get("status") == "PARKED" and ls.get("park_kind") == "branch" and bool(ls.get("mission"))
            and _now() >= float(ls.get("branch_retry_at") or 0))
AUTO_RULE_DENY_RE = re.compile(
    r"\b(budget|tokens?|authority|spend|cost|money|price|pay|paid|credentials?|passwords?|secrets?|api[ _-]?keys?|"
    r"push|publish|deploy|production|prod|e-?mail|send|post|sudo|purchase|accounts?|wipe|force|legal|licen[cs]e)\b",
    re.I)
APPROVE_RE = re.compile(r"\bapprove\s+(?:the\s+)?(?:Bash|shell|command)(?:\s+command)?\s*[:=]\s*(.+)$", re.I | re.S)
_CMD_DENY = {"sudo", "su", "ssh", "scp", "rsync", "curl", "wget", "git", "chmod", "chown", "kill", "pkill", "killall",
             "systemctl", "service", "crontab", "dd", "mkfs", "mount", "umount", "docker", "eval", "exec", "shutdown",
             "reboot", "nc", "ncat", "pip", "pip3", "npm", "apt", "apt-get", "find", "xargs", "bash", "sh", "env"}
_WRITE_ALL = {"rm", "rmdir", "touch", "mkdir", "truncate"}  # every operand is written
_WRITE_LAST = {"mv", "cp", "ln", "install"}  # the last operand is written (mv also removes its sources)


def worktree_safe_cmd(cmd: str, product: str) -> tuple[bool, str]:
    """(True, '') when `cmd` plainly stays inside the worker's own tree: no pipe, redirect, background, substitution or
    glob; no denied program; no '..' or '~'; absolute paths only inside the product (read) or /tmp; every path a
    command writes (and every mv source) relative. Anything unclear is refused, never guessed."""
    import shlex  # noqa: PLC0415
    flat = str(cmd or "").strip().strip("`").replace("&&", ";").replace("||", ";")
    if not flat.strip(" ;"):
        return False, "no command"
    if any(t in flat for t in ("$(", "`", "|", "&", ">", "<", "\n", "*", "?", "{")):
        return False, "uses a pipe, redirect, background, substitution, glob or several lines"
    root = os.path.realpath(product)
    for seg in flat.split(";"):
        try:
            toks = shlex.split(seg)
        except ValueError:
            return False, f"unparseable: {seg.strip()[:60]}"
        while toks and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):
            toks.pop(0)
        if not toks:
            continue
        name = os.path.basename(toks[0])
        if name in _CMD_DENY:
            return False, f"{name} is never auto-approved"
        for t in toks[1:]:
            if t.startswith("~") or ".." in t.replace("\\", "/").split("/"):
                return False, f"argument {t[:60]} may leave the worktree"
            if t.startswith("/"):
                p = os.path.realpath(t)
                if not (p == root or p.startswith(root + os.sep) or p.startswith("/tmp/")):
                    return False, f"absolute path {t[:60]} is outside the product"
        ops = [t for t in toks[1:] if not t.startswith("-")]
        written = ops if name in _WRITE_ALL else (ops if name == "mv" else ops[-1:]) if name in _WRITE_LAST else []
        for t in written:
            if t.startswith("/") or t.strip("/") in ("", "."):
                return False, f"{name} writes {t or '?'}: only relative paths inside the worktree"
    return True, ""


def auto_rule(st: dict, lanes: list, now: float | None = None) -> int:
    """Answer every question open >= AUTO_RULE_S that the round 9 rules allow; each question is considered once (its
    key in ls.auto_ruled). A refused one stays the Owner's (owner_queue line; its alert keeps mailing). -> rulings."""
    import hashlib  # noqa: PLC0415
    now = _now() if now is None else now
    n = 0
    for lane in lanes:
        ln = lane["name"]
        ls = (st.get("lanes") or {}).get(ln)
        if not ls or not ls.get("mission"):
            continue
        rec = mission(ls["mission"]) or {}
        qa = open_question(ls, rec)
        asked = float((rec.get("blocker") or {}).get("at") or 0)
        if not qa or not asked or now - asked < AUTO_RULE_S:
            continue
        key = f"{ls['mission']}:{hashlib.sha1(qa.encode()).hexdigest()[:10]}"
        if ls.get("auto_ruled") == key:
            continue
        ls["auto_ruled"] = key
        why = AUTO_RULE_DENY_RE.search(qa)
        m = APPROVE_RE.search(qa)
        if m:
            ok, why = worktree_safe_cmd(m.group(1), lane["product"])
            text = (f"APPROVED by the autopilot auto-ruling (round 9, Owner 2026-11-27 'subele el nivel de autonomia "
                    f"brutalmente'; unanswered {int((now - asked) // 60)} min): run exactly {m.group(1).strip()[:400]!r} "
                    "inside your own worktree and nothing outside it.")
        elif why:
            ok, why = False, f"it names {why.group(0)!r}"
        else:
            ok = True
            text = (f"AUTO-RULING by the autopilot (round 9, Owner 2026-11-27 'subele el nivel de autonomia "
                    f"brutalmente'; unanswered {int((now - asked) // 60)} min): decide it yourself inside the mission "
                    "envelope. Where you stated a recommendation, take it. Write the choice and why in your next "
                    f"checkpoint; the Owner may overrule it later. The question was: {qa[:300]}")
        if not ok:
            log(f"{ln}: question of {ls['mission']} left to the Owner by the auto-ruling ({why})")
            owner_queue(ln, f"question left to the Owner (auto-ruling refused: {why}): {qa[:300]}")
            continue
        row = record_answer(ln, text, now=now)
        ledger_add(lane=ln, kind="auto_ruling", tokens=0, ruling=row["id"], mission=ls["mission"])
        log(f"{ln}: auto-ruling {row['id']} for {ls['mission']} after {int((now - asked) // 60)} min unanswered")
        digest(ln, f"AUTO-RULING {row['id']} ({ls['mission']}): {text[:240]}")
        n += 1
    return n


def build_alerts(st: dict) -> list[dict]:
    """What needs the Owner now. 2026-11-25: every gsd_mission notice on GEX44 ended `incident_notify_failed` (no
    channel), and KSR/MKW sat PARKED over missions that were still live (one BLOCKED on an Owner decision)."""
    import hashlib  # noqa: PLC0415
    q, out = _last_queue_lines(), []
    dw = st.get("disk_wait")
    if dw:
        out.append({"key": f"disk:{int(dw.get('since') or 0)}", "lane": "ALL", "level": "disk",
                    "since": dw.get("since"), "text": str(dw.get("why"))})
    for ln, ls in sorted((st.get("lanes") or {}).items()):
        s = ls.get("status")
        rec = (mission(ls["mission"]) if ls.get("mission") else None) or {}
        qa = open_question(ls, rec)
        if qa:  # round 3: the question itself, and how to answer it
            out.append({"key": f"{ln}:question:{hashlib.sha1(qa.encode()).hexdigest()[:10]}", "lane": ln,
                        "level": "question", "since": (rec.get("blocker") or {}).get("at"),
                        "text": (f"QUESTION from {ls.get('mission')} ({rec.get('state')}): {qa} | answer with: "
                                 f"autopilot.py answer {ln} \"<ruling>\"")[:700]})
        if s in ALERT_STATUSES:
            at, text = q.get(ln, ("", f"{s} (no queue line)"))
            live = (f" | its mission {ls.get('mission')} is still {rec.get('state')}: {str(rec.get('reason') or '')[:200]}"
                    if rec and rec.get("state") not in TERMINAL else "")
            out.append({"key": f"{ln}:{s}:{hashlib.sha1(text.encode()).hexdigest()[:10]}", "lane": ln,
                        "level": s.lower(), "since": at, "park_kind": ls.get("park_kind"), "text": (text + live)[:700]})
        wd = ls.get("wd") or {}
        if s in ("RUNNING", "WAITING") and wd.get("told"):
            out.append({"key": f"{ln}:idle:{int(wd['since'])}", "lane": ln, "level": "idle", "since": wd["since"],
                        "text": str(wd.get("why"))[:700]})
        hs = ls.get("held_seen") if isinstance(ls.get("held_seen"), dict) else {}
        reason = str(rec.get("reason") or "")
        if (s == "RUNNING" and hs.get("since") and reason.startswith("launch held")
                and _now() - float(hs["since"]) >= HELD_NOTICE_S):
            # round 8: FIFA/FIFATC held for 7-9.5 h reached only owner_queue.md on GEX44, which nobody reads
            out.append({"key": f"{ln}:held:{hs.get('key')}:{int(float(hs['since']))}", "lane": ln, "level": "held",
                        "since": hs["since"],
                        "text": (f"HELD {ls.get('mission')} for {int((_now() - float(hs['since'])) / 60)} min with no "
                                 f"worker (autopilot could not align it): {reason[:400]}")[:700]})
    return out


def write_alerts(st: dict) -> None:
    """alerts.json, rewritten every tick. The laptop task PP-Ascension-Alerts mails new keys, and notices when this
    file stops being rewritten (the autopilot itself not ticking)."""
    try:
        tmpf = OUT / "alerts.json.tmp"
        tmpf.write_text(json.dumps({"at": _now(), "alerts": build_alerts(st)}, indent=1, default=str))
        os.replace(tmpf, OUT / "alerts.json")
    except Exception as exc:  # noqa: BLE001 -- alerts never stop a tick
        try:
            log(f"alerts.json not written: {exc!r}")
        except OSError:
            pass


def tick_lane(st: dict, lane: dict, dry: bool) -> None:
    """One lane's tick with an on-disk open mark (see recover_interrupted_tick) and the per-lane error park."""
    ln = lane["name"]
    ls = st.setdefault("lanes", {}).get(ln)
    if ls is not None:  # round 3: the lane's Owner rulings, for its planner and its live mission
        _RULINGS[ln] = list(ls.get("owner_rulings") or [])
        try:
            if deliver_rulings(ln, ls, dry):
                save_state(st)
        except Exception as exc:  # noqa: BLE001 -- a delivery never stops a tick
            log(f"{ln}: owner ruling delivery failed: {exc!r}")
        if ls.get("status") in ("RUNNING", "WAITING") and ls.get("mission"):  # round 4: stranded work, before judging
            try:
                rec0 = mission(ls["mission"]) or {}
                if stranded_due(rec0):
                    why = reconcile_stranded(lane, ls, rec0, dry)
                    if why.startswith("autopilot: bring"):
                        ls["held_grace_until"] = _now() + HELD_REPLAN_S
                        save_state(st)
                    if why.startswith("skip") and ls.get("stranded_note") != why:
                        ls["stranded_note"] = why
                        owner_queue(ln, f"NOTICE (no action needed): stranded {ls.get('gen')} work not merged: {why[:300]}")
                        save_state(st)
            except Exception as exc:  # noqa: BLE001 -- a reconcile never stops a tick
                log(f"{ln}: stranded-work reconcile failed: {exc!r}")
    if ls is not None:
        if ls.get("tick_open"):
            recover_interrupted_tick(st, ln, ls)
        ls["tick_open"] = _now()
        save_state(st)
    try:
        lane_tick(st, lane, dry)
    except Exception as exc:  # noqa: BLE001 -- one lane's failure never stops the other; it is logged and parked
        log(f"{ln}: ERROR {type(exc).__name__}: {exc}")
        ls2 = st.setdefault("lanes", {}).setdefault(ln, {})
        ls2.pop("tick_open", None)
        ls2["status"] = "PARKED"
        owner_queue(ln, f"autopilot error {type(exc).__name__}: {str(exc)[:200]}")
        save_state(st)  # if this save fails too, the open mark stays on disk and the next tick recovers the lane
        return
    ls2 = st.get("lanes", {}).get(ln)
    if ls2 is not None:
        ls2.pop("tick_open", None)
        try:
            watchdog(st, lane, ls2)
        except Exception as exc:  # noqa: BLE001 -- a watch never stops a tick
            log(f"{ln}: watchdog failed: {exc!r}")
        save_state(st)


def halt_resumable(ls: dict, mid: str) -> bool:
    """A halted mission may be continued by a RUNNING lane, or by one un-parked (WAITING) that keeps the refused
    continuation plan of this very mission. 2026-11-18 (FIFA S146F, Owner 'y'): the un-park set WAITING and the lane
    re-parked at the next tick with 'ended HALTED without a checkpoint hold', its continuation plan never re-planned."""
    return (ls.get("status") == "RUNNING"
            or (ls.get("status") == "WAITING" and (ls.get("pending_plan") or {}).get("for") == f"continue:{mid}"))


def terminal_checkpoint(ls: dict, product: str, rec: dict) -> str:
    """The checkpoint a mission that ended without a checkpoint hold committed on its branch, '' when none. 2026-11-18
    (FIFA S170F, MKW S151M): both wrote their checkpoint, were judged, then spent their authority (CAPITAL_EXHAUSTED) and
    were settled HALTED with a cost hold; the Owner's un-park for a re-judge parked them at once. (KSR S171K): the
    mission works from the control repo gen3-pp and commits in the product t1-campaign, so gen_head named a gen3-pp
    commit the product does not have; then the product's own HEAD is the generation's head."""
    h = gen_head(rec)
    return checkpoint_from_branch(product, ls.get("base"), h if h and _sha(product, h) else "HEAD")


def continue_halted(st: dict, lane: dict, ls: dict, mid: str, rec: dict, dry: bool) -> bool:
    """F4: a generation that halted without a checkpoint but committed work on its branch is continued ONCE from the
    judgment it was planned from (2026-11-15: S57F, S56T and S65M left commits that the lane park threw away).
    False = not continued (the caller parks as before). True = handled: armed, waiting on the day cap, or retrying.
    Review 2026-11-16 (M1): a mission someone closed on purpose ("owner close ...") is never continued. (M2): the one
    continuation is spent only when a new generation was actually armed; a transient arm failure or a day-cap wait keeps
    it, and plan_and_arm's own arm_fails bound still parks a lane that cannot arm."""
    pf = ls.get("planned_from") or {}
    if ls.get("continued_from") or not isinstance(pf.get("verdict"), dict) or not pf.get("checkpoint") or owner_closed(rec):
        return False
    head = gen_head(rec)
    n = branch_commits(lane["product"], ls.get("base"), head)
    if n < 1:
        return False
    why = budget_admits(ledger_rows(), _now(), GEN_CAP + 2 * CALL_RESERVE)
    if why:
        if why.startswith(PARK_REASONS):
            return False
        log(f"{lane['name']}: continuation of {mid} waits: {why}")
        return True
    br = (rec.get("binding") or {}).get("branch") or "the generation branch"
    ok, note = evolve.ff_to(lane["product"], head, dry)  # F4b: the next packet lands on a product holding the branch
    if not ok:
        owner_queue(lane["name"], f"continuation of {mid} not armed: {note} ({n} commits on {br}); lane parked")
        return False
    log(f"{lane['name']}: continuation of {mid}: {note}")
    ledger_add(lane=lane["name"], kind="halt_continue", tokens=0, mission=mid, gen=ls.get("gen"), commits=n, head=head)
    log(f"{lane['name']}: {mid} ended {rec.get('state')} without a checkpoint with {n} commits on {br}; continuing once")
    digest(lane["name"], f"CONTINUE {ls.get('gen')} ({mid} {rec.get('state')}: {str(rec.get('reason'))[:200]}): "
                         f"{n} commits on {br} at {str(head)[:12]}")
    directive = (f"CONTINUATION of {ls.get('gen')} ({mid} ended {rec.get('state')} with no checkpoint: "
                 f"{str(rec.get('reason'))[:160]}). Its work is {n} commits on branch {br} at {str(head)[:12]}; the "
                 f"product {lane['product']} has been fast-forwarded to that commit, so work from the product like any "
                 f"generation and never commit in the old work tree {(rec.get('binding') or {}).get('root')}: copy any "
                 "file it left uncommitted into the product and commit it there first. Read its budget.md and evidence "
                 "first, do not redo what it proved, and commit the checkpoint before 75% of the caps is processed.")
    pend = ls.get("pending_plan") or {}
    if pend.get("for") == f"continue:{mid}" and pend.get("bad"):  # un-parked after a refusal: the planner is told why
        directive += "\n\n" + replan_feedback(pend["bad"], pend.get("offenders"))
    plan_and_arm(st, lane, ls, f"continue:{mid}", pf["checkpoint"], lane["product"], dict(pf["verdict"]), directive,
                 {}, dry)
    if ls.get("mission") != mid:  # a new generation was armed: the one continuation is spent
        ls["continued_from"] = mid
        save_state(st)
    return True


HELD_NOTICE_S = 1800  # F6: a RUNNING mission whose launch has been held this long is told to the Owner once
AGE_DEFER_SPENT = 0.75  # F2b: at or past this share of its authority a cost hold is near; the top-up extends instead


def running_watch(st: dict, lane: dict, ls: dict, mid: str, rec: dict, dry: bool, age: float = 0.0) -> None:
    """A live mission with no hold. F6 (2026-11-16, S71F/S69T): RUNNING with every relaunch held ('launch held: cwd not
    aligned') sat 8 h unseen after both workers finished; it is now told to the Owner once per mission and reason.
    F2b (2026-11-16, S65M): a mission with work on its branch halted on age at 07:45 because the wall was only
    extended alongside a cost top-up; below AGE_MIN_H it is extended once, inside the lane envelope. gsd_mission lets
    one Owner turn authorise one act per mission, so after a top-up the extension is refused and the Owner is told
    BEFORE the wall, not after."""
    now, ln = _now(), lane["name"]
    reason = str(rec.get("reason") or "")
    held_s = max(float(age or 0), now - float(rec.get("updated_at") or now))  # round 8: held_age, not updated_at alone
    if reason.startswith("launch held") and held_s >= HELD_NOTICE_S and ls.get("held_notice") != f"{mid}:{reason[:120]}":
        ls["held_notice"] = f"{mid}:{reason[:120]}"
        save_state(st)
        owner_queue(ln, f"{mid} is RUNNING with no worker for {int(held_s / 60)} min: {reason[:300]}")
        digest(ln, f"HELD {mid} for {int(held_s / 60)} min with no worker: {reason[:400]}")
    # 2026-11-17 (S108W): BLOCKED on a host permission prompt ('rm config/config; git commit ...') with no hold sat
    # ~10 h unseen; the lane still read RUNNING. Told once per mission and blocker. Not parked: when the prompt is
    # answered the mission resumes and this lane must still see its checkpoint.
    blk = rec.get("blocker") if isinstance(rec.get("blocker"), dict) else {}
    b_s = now - float(blk.get("at") or rec.get("updated_at") or now)
    bkey = f"{mid}:BLOCKED:{blk.get('at')}"
    if rec.get("state") == "BLOCKED" and b_s >= HELD_NOTICE_S and ls.get("held_notice") != bkey:
        uc = blk.get("unblock_condition") or {}
        ls["held_notice"] = bkey
        save_state(st)
        owner_queue(ln, f"{mid} is BLOCKED for {int(b_s / 60)} min on {blk.get('class', '?')} ({uc.get('gate', '')}): "
                        f"the worker waits for a human; needs: {str(uc.get('needs') or reason)[:300]}")
        digest(ln, f"BLOCKED {mid} for {int(b_s / 60)} min: {str(uc.get('needs') or reason)[:400]}")
    left = hours_left(rec, now)
    if left >= AGE_MIN_H or ls.get("age_ext_for") == mid:
        return
    auth, spent = float(rec.get("authority_tokens") or 0), float((rec.get("cost_mark") or {}).get("tokens") or 0)
    if auth and spent >= AGE_DEFER_SPENT * auth:
        return  # review 2026-11-16 (MEDIUM): a cost hold is near; cost_topup extends the wall in that same one act
    if branch_commits(lane["product"], ls.get("base"), gen_head(rec)) < 1:
        return
    ls["age_ext_for"] = mid
    save_state(st)
    env = lane.get("envelope") or {}
    ext = round(min(AGE_EXTEND_H, (WALL - dt.datetime.fromtimestamp(now, dt.timezone.utc)).total_seconds() / 3600), 1)
    if not env.get("owner_turn") or ext < 0.5:
        why = "the lane has no Owner envelope turn" if not env.get("owner_turn") else "the programme wall is too close"
        owner_queue(ln, f"{mid} reaches its age wall in {left:.1f} h with work on its branch and is not extended: {why}")
        return
    rc, out = gm("authority", "--mission", mid, "--extend-hours", f"{ext:g}", "--owner-turn", env["owner_turn"],
                 "--reason", f"Autopilot age extension +{ext:g} h inside the {ln} envelope ({env.get('note', '')}); "
                             f"{left:.1f} h left with work on the generation branch", dry=dry)
    if rc != 0:
        owner_queue(ln, f"{mid} reaches its age wall in {left:.1f} h with work on its branch; +{ext:g} h refused by "
                        f"gsd_mission (a new Owner turn is needed): {out[-300:]}")
        return
    ledger_add(lane=ln, kind="age_extend", gen=ls.get("gen"), mission=mid, tokens=0, extend_hours=ext)
    log(f"{ln}: {mid} wall +{ext:g} h ({left:.1f} h left, work on its branch)")


def owner_closed(rec: dict) -> bool:
    """A mission closed by an explicit close act (gsd_mission close: reason 'owner close (...)'), not one halted by a
    budget, age, iteration or cost mechanism. Those stops are the Owner's and are never continued."""
    return str(rec.get("reason") or "").startswith("owner close")


def _park(st: dict, ls: dict, lane: str, queue: str, dig: str | None = None, kind: str | None = None) -> None:
    ls["status"] = "PARKED"
    ls["park_kind"] = kind
    owner_queue(lane, queue)
    if dig:
        digest(lane, dig)
    save_state(st)


def hold_checkpoint(hold: dict) -> str:
    """The path a checkpoint hold names: `evidence`, or `residual` for a pivot hold (gsd_mission leaves evidence null
    there). Owner 2026-11-13 (pane c26eafbf): S36K's METHOD_PIVOT_REQUIRED hold was judged with an empty path.
    A commit sha (or the string "None") in `evidence` is not a path: 2026-11-15 S58W's hold carried 8afbd99 there and
    the lane parked CHECKPOINT_ON_BRANCH with its residual unread (spec ascension-autopilot-stall-fixes F3).
    "<sha>:<path>" names the path at a commit (2026-11-16 S70W: c235442:evidence/ascension/s70w/checkpoint_s70w.md
    parked as a path that exists nowhere): the path part is the checkpoint, found on its branch by discovery."""
    ev = str(hold.get("evidence") or "")
    m = SHA_PATH_RE.match(ev) or PATH_AT_SHA_RE.match(ev)
    if m:
        # 2026-11-18 (S177M): "evidence/ascension/s177m/checkpoint_s177m_r1b.md@74cbfef" parked CHECKPOINT_ON_BRANCH
        ev = m.group(1)
    if ev == "None" or SHA_RE.match(ev):
        ev = ""
    if re.search(r"\s", ev):
        # 2026-11-17 (S113R): "branch worktree-s113r commit ac2201a: evidence/ascension/s113r/checkpoint.md" was taken
        # whole as a path and parked CHECKPOINT_ON_BRANCH; prose names its file, the last one named is the checkpoint
        found = PATH_IN_TEXT_RE.findall(ev)
        ev = found[-1] if found else ""
    if not ev and not hold.get("residual"):
        # 2026-11-19 (KSR S202K): evidence null, the path only in the reason prose ("...; see evidence/ascension/s202k/
        # checkpoint_s202k.md"); the control-repo head hid the branch fallback and the lane parked unjudged. A checkpoint
        # or residual file the reason names is the checkpoint.
        found = [p for p in PATH_IN_TEXT_RE.findall(str(hold.get("reason") or "")) if CKPT_NAME_RE.search(p)]
        ev = found[-1] if found else ""
    return ev or hold.get("residual") or ""


SHA_PATH_RE = re.compile(r"^[0-9a-f]{7,40}:(\S.*)$")
PATH_AT_SHA_RE = re.compile(r"^(\S+?)@[0-9a-f]{7,40}$")
PATH_IN_TEXT_RE = re.compile(r"(?<![\w./-])(/?(?:[\w.-]+/)+[\w.-]+\.(?:md|json))\b")
CKPT_NAME_RE = re.compile(r"(?:^|/)[^/]*(?:checkpoint|residual)[^/]*\.md$", re.I)


def checkpoint_from_branch(product: str, base, head) -> str:
    """The checkpoint a hold forgot to name: the most recently committed checkpoint*/residual* .md file between the
    generation base and its branch head, present at the head. '' when there is none. 2026-11-17 (S111C): a
    CHECKPOINT_COMPLETE hold with evidence null parked FIFATC with 'F17 SUPPORTED, held-out 11/40' unread, while
    evidence/f17/checkpoint_s111c.md was the branch's last commit."""
    h, b = _sha(product, head), _sha(product, base)
    if not (h and b) or b == h:
        return ""  # no window: an older generation's checkpoint must never be judged as this hold's
    rc, out = _git(product, "log", "--format=", "--name-only", "--diff-filter=AM", f"{b}..{h}")
    for path in (l.strip() for l in out.splitlines() if rc == 0):
        if path and CKPT_NAME_RE.search(path) and _git(product, "cat-file", "-e", f"{h}:{path}")[0] == 0:
            return path
    return ""


NOPATH_WAIT_S = 1800  # round 2: gsd_mission auto-pivoted KSR S329K's and MKW S338M's holds 4 and 11 min after setting them


def checkpoint_from_sha(product: str, hold: dict, base) -> str:
    """2026-11-25 (KSR S329K `5cb05abd`, MKW S338M `289143e1`): the hold's evidence was the product commit that adds the
    checkpoint, and both lanes parked "names no path" while their missions went on unwatched. A sha in evidence or
    residual that is a product commit strictly after the generation base resolves to the checkpoint*/residual*.md it
    adds or modifies. Reachability from HEAD is NOT required (MKW's sat on its worktree branch; discover_checkpoint
    fast-forwards). '' when none."""
    b = _sha(product, base)
    if not b:
        return ""
    for x in (hold.get("evidence"), hold.get("residual")):
        c = _sha(product, str(x or "").strip())
        if not c or c == b or _git(product, "merge-base", "--is-ancestor", b, c)[0] != 0:
            continue
        rc, out = _git(product, "show", "--format=", "--name-only", "--diff-filter=AM", c)
        for path in (l.strip() for l in out.splitlines() if rc == 0):
            if path and CKPT_NAME_RE.search(path):
                return path
    return ""


# 2026-11-21 (Owner "y", pane b9040a8e): a day-cap WAIT before arming dropped the judgment (judged_for None, pending_plan
# popped, snap restored), so every later tick re-judged, re-designed and re-planned the same checkpoint (~1-3M tokens)
# until the caps fitted. Measured before the fix: 0 such waits in cron.out since 11-11 (the judge step reserves GEN_CAP
# + 2 reserves first); reachable when other lanes spend during a ~30 min judgment near the day cap. The wait now keeps
# the judgment like a RETRY, with the caps it waits for, and a resumed wait makes no model call until they fit.
BUDGET_WAIT_KEEPS_JUDGMENT = True


def _governor(*args, timeout=120) -> tuple[int, str]:
    """tools/account_governor.py, the account-level weekly guard that gsd_mission arm enforces (Owner Q2, 85%)."""
    try:
        r = subprocess.run([sys.executable, str(PP / "tools" / "account_governor.py"), *args], capture_output=True,
                           text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as exc:  # noqa: BLE001 -- unreadable: the arm's own governor check stays authoritative
        return -1, f"{type(exc).__name__}: {exc}"


_WEEKLY = {"at": 0.0, "why": None}
WEEKLY_TTL_S = 240  # one governor read per tick for every lane, not one per lane


def weekly_admits(now: float | None = None) -> str | None:
    """T1 O4 (Owner "y" 2026-11-22): the arm-time weekly guard, asked BEFORE arming instead of discovered as a
    MissionError inside `gsd_mission arm` (11-19/20: tracebacks, arm_refund, a parked lane). None = admitted or not
    measurable (the arm's own check still refuses then); else a day-cap-like wait reason, so the judgment is kept.
    Kill switch AP_WEEKLY_CHECK=off."""
    if os.environ.get("AP_WEEKLY_CHECK", "").strip().lower() == "off":
        return None
    now = _now() if now is None else now
    if now - _WEEKLY["at"] < WEEKLY_TTL_S:
        return _WEEKLY["why"]
    rc, out = _governor("check", "--action", "arm")
    why = None
    if rc == 3:
        line = next((l.strip() for l in reversed(out.splitlines()) if "refused" in l), out.strip()[-200:])
        nxt = ""
        src, sout = _governor("status", "--json")
        try:
            ra = float(json.loads(sout[sout.index("{"):]).get("reset_at") or 0)
            while ra and ra <= now:
                ra += 7 * 86400
            if ra:
                nxt = "; next weekly reset " + dt.datetime.fromtimestamp(ra, dt.timezone.utc).strftime("%FT%H:%MZ")
        except (ValueError, TypeError, json.JSONDecodeError):
            nxt = "; next weekly reset unreadable"
        why = f"weekly guard: {line[:200]}{nxt} (waits for the reset or a lower bound under the guard)"
    _WEEKLY.update(at=now, why=why)
    return why


def resume_wait(pend: dict) -> str | None:
    """The budget reason a kept budget-wait plan still waits for (a day-cap or weekly wait), else None."""
    caps = pend.get("wait_caps")
    if type(caps) is not int or caps <= 0:
        return None
    why = budget_admits(ledger_rows(), _now(), caps) or weekly_admits()
    return why if why and not why.startswith(PARK_REASONS) else None


def resumable_plan(ls: dict, key: str) -> dict | None:
    """The judgment a policy refusal parked with, when the lane is un-parked on the SAME checkpoint hold: the re-plan
    starts from it and the judge is not called again. 2026-11-14 (S39K, Owner "y"): every un-park after a refusal
    re-judged the checkpoint, so one result added a second lever_history row and a second method-graph credit."""
    pp = ls.get("pending_plan")
    return pp if isinstance(pp, dict) and key and pp.get("for") == key and isinstance(pp.get("verdict"), dict) else None


def _refused(st: dict, ls: dict, lane: str, pend: dict, queue: str, dig: str, kind: str | None = None,
             retry: bool = True) -> None:
    """Park on a policy refusal, keeping the judgment for the re-plan after the Owner's look. 2026-11-18 (Owner 'y', pane
    08cba76c; MKWLIB S150L parked on 'no rival'/'no decision rule'/'no positive control', each re-plan fixing one and
    dropping another): a refusal the planner can fix (no budget reason in it) is re-planned at the next tick instead,
    POLICY_RETRY_TICKS times, from the kept judgment and told EVERY refusal so far. Budget refusals still park, and so
    does a re-plan whose planner stopped with no designed lever (retry=False): it has said it has no route."""
    old = ls.get("pending_plan") or {}
    if old.get("for") == pend.get("for"):
        pend = dict(pend, bad=list(dict.fromkeys([*(old.get("bad") or []), *(pend.get("bad") or [])])))
    ls["pending_plan"] = pend
    n = int(ls.get("policy_retry") or 0)
    if (retry and n < POLICY_RETRY_TICKS and pend.get("bad")
            and not any(OWNER_REFUSAL.search(str(b)) for b in pend["bad"])):
        ls.update(policy_retry=n + 1, judged_for=None)
        log(f"{lane}: {queue[:300]}; planner-fixable: re-plan at the next tick ({n + 1}/{POLICY_RETRY_TICKS})")
        digest(lane, f"{dig[:300]}; re-plan at the next tick from the kept judgment")
        save_state(st)
        return None
    ls["policy_retry"] = 0
    return _park(st, ls, lane, queue, dig, kind=kind)


# ---------------------------------------------------------------- the per-lane transition
def lane_tick(st: dict, lane: dict, dry: bool) -> None:
    ls = st.setdefault("lanes", {}).setdefault(lane["name"], {"status": "WAITING", "blank": 0, "arm_fails": 0, "gen": None})
    evo = evolve.enabled(HOME)
    if evo and ls.get("status") == "PARKED" and ls.get("park_kind") == "budget":
        # EVO continuity: a budget park is lifted by an Owner release, which the ledger shows; nothing else is assumed
        if evolve.budget_resume(ls, budget_admits(ledger_rows(), _now(), GEN_CAP + 2 * CALL_RESERVE)):
            ls.update(status="WAITING", park_kind=None, judged_for=None)
            log(f"{lane['name']}: budget admits again (Owner release): lane resumed")
            save_state(st)
        else:
            return
    if branch_retry_due(ls):
        # Round 9 (FIFATC S383C, TENNIS S428T, KSR S441K parked "branch" from ~01:00Z to 07:30Z with nobody to unpark
        # them): a branch park is a state of git, which the next commit, relaunch or round 9 fast-forward can change.
        # Every BRANCH_RETRY_S the lane is ticked again with its judgment cleared; the same park again is silent.
        ls.update(status="RUNNING", park_kind=None, judged_for=None, branch_retry_at=_now() + BRANCH_RETRY_S)
        save_state(st)
    if ls.get("status") in ("PARKED", "STOPPED"):
        return
    if ls.get("pending_arm"):
        # A previous tick died inside an arm. Its mission state is not known here: reconcile by hand, never guess.
        return _park(st, ls, lane["name"], f"arm interrupted: {json.dumps(ls['pending_arm'])}; reconcile the mission "
                                           "records and the ledger reservation by hand, then clear pending_arm")
    rf = lane.get("ready_file")
    if rf and (not Path(rf["path"]).exists() or Path(rf["path"]).read_text().strip() != rf["content"]):
        return
    mid = ls.get("mission") or lane.get("mission")
    checkpoint, product = None, lane["product"]
    if mid:
        mid = follow_renewals(mid)
        ls["mission"] = mid
        rec = mission(mid)
        if rec is None:
            return
        hold = rec.get("owner_hold") or {}
        if rec["state"] in TERMINAL:
            if halt_resumable(ls, mid) and continue_halted(st, lane, ls, mid, rec, dry):
                return
            tck = terminal_checkpoint(ls, product, rec)
            if not tck:
                return _park(st, ls, lane["name"], f"mission {mid} ended {rec['state']} without a checkpoint hold; lane parked")
            if ls.get("judged_for") != f"{mid}:terminal":
                log(f"{lane['name']}: {mid} ended {rec['state']} with {tck} committed on its branch; judged as its checkpoint")
            hold = {"kind": "checkpoint", "set_at": "terminal", "evidence": tck}
        if not hold and ls.get("status") == "RUNNING":
            age = held_age(st, ls, mid, rec)
            if age >= HELD_REPAIR_S and held_align(st, lane, ls, mid, rec, dry):
                return  # round 8: gsd_mission's next relaunch finds cwd == work_dir
            fck = held_final_checkpoint(lane, ls) if age >= HELD_REPAIR_S else ""
            if fck:  # round 8 (FIFA S392F): the held generation already wrote its FINAL checkpoint: judge it
                if ls.get("held_final_for") != f"{mid}:{fck}":
                    ls["held_final_for"] = f"{mid}:{fck}"
                    save_state(st)
                    log(f"{lane['name']}: {mid} launch held with its FINAL checkpoint {fck} on the product; judged")
                    digest(lane["name"], f"HELD-FINAL {ls.get('gen')} ({mid}): {fck} declares final; judged as its "
                                         "checkpoint instead of waiting for a relaunch")
                hold = {"kind": "checkpoint", "set_at": f"held-final:{fck}", "evidence": fck}
        if not hold and ls.get("status") == "RUNNING":
            if held_too_long(rec, age=age) and _now() >= float(ls.get("held_grace_until") or 0):
                # round 2: a launch held for hours is re-planned like a refused cost breaker. Round 4b (MKW 12:15Z): not
                # within HELD_REPLAN_S of a stranded merge home, which is what lets the held relaunch align
                return breaker_replan(st, lane, ls, mid, rec, {"set_at": f"held:{rec.get('updated_at')}",
                                                               "reason": rec.get("reason")}, dry, cause="held")
            return running_watch(st, lane, ls, mid, rec, dry, age=age)
        if hold.get("kind") == "cost" and ls.get("status") == "RUNNING":
            if cost_topup(st, lane, ls, mid, rec, hold, dry) == "REFUSED":
                return breaker_replan(st, lane, ls, mid, rec, hold, dry)
            return
        if hold.get("kind") != "checkpoint":
            return
        checkpoint = hold_checkpoint(hold)
        if SHA_RE.match(checkpoint):  # a bare commit sha in `residual` is not a path either (MKW S338M pivot)
            checkpoint = ""
        if ls.get("judged_for") == f"{mid}:{hold.get('set_at')}":
            return
        if not checkpoint:  # 2026-11-25 (KSR S329K, MKW S338M): the hold names the product commit that adds it
            checkpoint = checkpoint_from_sha(product, hold, ls.get("base"))
            if checkpoint:
                log(f"{lane['name']}: hold of {mid} names a commit; its checkpoint is {checkpoint}")
        if not checkpoint:  # 2026-11-17 (S111C): look on the generation branch before parking
            gh = gen_head(rec)  # KSR: a control-repo head the product lacks -> the product HEAD (as terminal_checkpoint)
            checkpoint = checkpoint_from_branch(product, ls.get("base"), gh if gh and _sha(product, gh) else "HEAD")
            if checkpoint:
                log(f"{lane['name']}: hold of {mid} names no path; found {checkpoint} on the generation branch")
        if not checkpoint:  # a judge with no path can only say INCONCLUSIVE: wait for the mission, then park
            hk = f"{mid}:{hold.get('set_at')}"
            if ls.get("nopath_for") != hk:
                ls.update(nopath_for=hk, nopath_since=_now())
                save_state(st)
                log(f"{lane['name']}: checkpoint hold of {mid} names no path; waiting up to {NOPATH_WAIT_S // 60} min "
                    "(the mission may pivot or name it)")
                return
            if _now() - float(ls.get("nopath_since") or 0) < NOPATH_WAIT_S:
                return
            ls["judged_for"] = hk
            return _park(st, ls, lane["name"], f"checkpoint hold of {mid} names no evidence or residual path after "
                                               f"{NOPATH_WAIT_S // 60} min; not judged")
        kept = resumable_plan(ls, f"{mid}:{hold.get('set_at')}")
        if kept and kept.get("checkpoint"):
            # 2026-11-19 (FIFATC S118C, pane 08cba76c): the halted worker sat on a stale side branch, so discovery parked
            # on its old checkpoint forever. A kept judgment that names its own checkpoint is planned from that one;
            # the branch checkpoint is neither discovered, fast-forwarded nor judged.
            checkpoint = kept["checkpoint"]
        elif evo and checkpoint:
            how, note = evolve.discover_checkpoint(product, checkpoint, dry)
            if how == "PARK":
                if ls.get("branch_note") == note:  # round 9 retry: still the same git state, already told
                    ls.update(status="PARKED", park_kind="branch", judged_for=None)
                    save_state(st)
                    return
                ls["branch_note"] = note
                return _park(st, ls, lane["name"], note, f"PARKED: {note}", kind="branch")
            ls.pop("branch_note", None)
            ls.pop("branch_retry_at", None)
            if how == "FF":
                log(f"{lane['name']}: {note}")
            wr = evolve.worktree_rel(product, checkpoint)
            if wr:  # F3: judged where its gates run, the product (now holding the branch), not the worker's tree
                checkpoint = os.path.join(product, wr[1])
        ls.pop("continued_from", None)  # a checkpoint was reached: a later halt may be continued again
        ls.pop("breaker_replans", None)  # ... and a cost-breaker streak is over
        ls["judged_for"] = key = f"{mid}:{hold.get('set_at')}"
    else:
        pat, product = lane["bootstrap_checkpoint"], lane.get("bootstrap_product", lane["product"])
        if ls.get("judged_for") == "bootstrap":
            return
        hits = sorted(Path(pat).parent.glob(Path(pat).name))
        if not hits:
            return
        checkpoint = str(hits[-1])
        ls["judged_for"] = key = "bootstrap"
    save_state(st)
    # T1 O2: judging asks only what a judge + planner (+ lever) call costs; the next generation's caps are asked at arming,
    # whose day-cap wait keeps the judgment (BUDGET_WAIT_KEEPS_JUDGMENT), so no finished generation waits a day unjudged.
    why = budget_admits(ledger_rows(), _now(), JUDGE_ASK)
    if why:
        ls["judged_for"] = None
        if why.startswith(PARK_REASONS):  # only the day cap is a wait; frozen/total/wall need the Owner
            return _park(st, ls, lane["name"], f"budget gate: {why}", f"PARKED at a budget gate: {why}", kind="budget")
        save_state(st)
        log(f"{lane['name']}: budget wait: {why}")
        return
    pend = resumable_plan(ls, key)
    if pend:
        wwhy = resume_wait(pend)
        if wwhy:
            ls["judged_for"] = None
            save_state(st)
            log(f"{lane['name']}: budget wait before arming {pend.get('gen')} (judgment kept, no call): {wwhy}")
            return
        ledger_add(lane=lane["name"], kind="replan_resume", tokens=0, checkpoint=checkpoint,
                   verdict=pend["verdict"].get("verdict"), gen=pend.get("gen"))
        log(f"{lane['name']}: un-parked after a policy refusal on {key}: re-plan from the kept judgment, no re-judge")
        digest(lane["name"], f"RE-PLAN after the Owner's look on {checkpoint}: judgment kept, not re-judged")
        if pend.get("next_lever"):
            ls["next_lever"] = pend["next_lever"]
        d0 = pend.get("directive") or ""
        if pend.get("bad"):
            d0 = (d0 + "\n\n" + replan_feedback(pend["bad"], pend.get("offenders"))).strip()
        return plan_and_arm(st, lane, ls, key, checkpoint, product, dict(pend["verdict"]), d0,
                            pend.get("snap") or {}, dry)
    ls.pop("pending_plan", None)  # a new hold: whatever an older refusal kept no longer describes this checkpoint
    log(f"{lane['name']}: checkpoint {checkpoint} -> judge")
    ruling = owner_exclusion_text(ls, checkpoint)
    v = ({"verdict": "AGREE", "new_canonical_certs": 0, "validated_capability": False, "protected_ok": True,
          "gates": [{"cmd": "dry", "rc": 0}], "_tokens": 0} if dry else judge(lane, checkpoint, product, ruling))
    tok, measured = call_tokens(v.get("_tokens"))
    ledger_add(lane=lane["name"], kind="judge", tokens=tok, measured=measured, verdict=v.get("verdict"), checkpoint=checkpoint)
    oe = ls.get("owner_excluded") or {}
    if (not dry and oe.get("checkpoint") and str(checkpoint).endswith(str(oe["checkpoint"]))):
        # one judgment only: the one-off ruling named this checkpoint, not the lane's future
        ledger_add(lane=lane["name"], kind="owner_exclusion_used", tokens=0, checkpoint=checkpoint,
                   gates=(ls.pop("owner_excluded", None) or {}).get("gates"))
    apply_standing_exclusion(v, ls)
    prior = ls.get("superseded") or {}
    if v.get("verdict") == "AGREE" and not agree_supported(v, prior):
        v["verdict"] = "INCONCLUSIVE"
        v["notes"] = f"AGREE without its own evidence (protected_ok/gates rc): {str(v.get('notes', ''))[:400]}"
    sbad = None if dry or v.get("verdict") != "AGREE" else superseded_ok(v, product, ls.get("base"), prior, lane)
    if sbad:
        v["verdict"] = "INCONCLUSIVE"
        v["notes"] = f"autopilot superseded-gate check: {sbad}; {str(v.get('notes', ''))[:300]}"
    ebad = None if dry or v.get("verdict") != "AGREE" else excluded_ok(v, product, ls.get("base"))
    if ebad:
        v["verdict"] = "INCONCLUSIVE"
        v["notes"] = f"autopilot excluded-gate check: {ebad}; {str(v.get('notes', ''))[:300]}"
    rbad = None if dry or v.get("verdict") != "AGREE" else pre_existing_ok(v, product, prered_base(ls))
    if rbad:
        v["verdict"] = "INCONCLUSIVE"
        v["notes"] = f"autopilot pre-existing-red check: {rbad}; {str(v.get('notes', ''))[:300]}"
    pbad = protected_check(lane)
    if v.get("verdict") == "AGREE" and pbad:
        v["verdict"] = "DISAGREE"
        v["notes"] = f"autopilot protected check: {pbad}"
    if v.get("verdict") == "AGREE":
        ls["superseded"] = superseded_record(v, prior)
        ls.pop("unfinished_streak", None)
        ls.pop("not_agreed_base", None)
    digest(lane["name"], f"JUDGE {v.get('verdict')} on {checkpoint}: new certs {v.get('new_canonical_certs')}, "
                         f"capability {v.get('validated_capability')}. {str(v.get('notes', ''))[:600]}")
    if not dry:
        surface_owner_questions(lane["name"], checkpoint, product)
    if v.get("verdict") != "AGREE":
        protected = bool(pbad) or v.get("protected_ok") is False  # review 0ba4 LOW: never continued, never designed
        if (key != "bootstrap" and not protected
                and continue_unfinished(st, lane, ls, key, checkpoint, product, v, dry)):
            return
        why = f"judge {v.get('verdict')} on {checkpoint}: {str(v.get('notes', ''))[:300]}"
        if evo:
            why = design_before_park(st, lane, ls, key, checkpoint, product, v, pbad, why, dry)
            if why is None:
                return
        # round 5: an escape that demonstrated its limits is an honest stop, not an evo park
        return _park(st, ls, lane["name"], why,
                     kind="limits" if str(why).startswith(evolve.ESCAPE_LIMITS_TAG) else None)
    snap = {k: ls.get(k, 0) for k in ("blank", "info_streak", "no_conversion")}  # restored if this judgment is redone
    cls, cnotes = classify_progress(v, product, ls.get("base"), None if dry else lane)
    evo_dir = ""
    if evo:
        helpers = types.SimpleNamespace(in_window=in_window, _changed=_changed, DATA=DATA, _git=_git, _sha=_sha)
        instruments = evolve.verify_instrument_failures(v, product, ls.get("base"), helpers)
        cls = evolve.classify(cls, instruments)
        graph, levers = evolve.load_graph(HOME), evolve.load_levers(HOME)
        d = evolve.after_judgment(ls, cls, instruments, levers, lane["name"], product, graph,
                                  (BLANK_STOP, INFO_PARK, NO_CONVERSION_PARK),
                                  designer=None if dry else lever_designer(lane, checkpoint, product), residual=checkpoint)
        persist_designed(lane, d, levers, dry)
        note_extensions(lane["name"], ls)
        if not dry:
            evolve.save_graph(HOME, graph)
        ls["last_progress"] = cls
        ledger_add(lane=lane["name"], kind="evo_decision", tokens=0, cls=cls, instruments=instruments,
                   action=d["action"], why=d["why"][:300], lever=(d.get("lever") or {}).get("id"), mode=ls.get("mode"),
                   selection=evolve.selection_evidence(d.get("lever"), graph))
        digest(lane["name"], f"PROGRESS {cls} (verified by the autopilot). {cnotes[:400]} EVO: {d['action']}: {d['why'][:300]}")
        if d["action"] == "stop":
            ls["status"] = "STOPPED"
            owner_queue(lane["name"], d["why"] + "; lane stopped")
            save_state(st)
            return
        if d["action"] == "park":
            ls["judged_for"] = None
            return _park(st, ls, lane["name"], f"EVO: {d['why']}; Owner look before the next one",
                         kind=d.get("park_kind") or "evo")
        if d.get("lever"):
            ls["next_lever"] = d["lever"]["id"]
        evo_dir = d.get("directive", "")
    conv = cls in evolve.CONVERSIONS
    if not evo:
        ls["blank"] = ls.get("blank", 0) + 1 if cls == "NONE" else 0
        ls["info_streak"] = ls.get("info_streak", 0) + 1 if cls == "INFORMATION" else 0
        ls["no_conversion"] = 0 if conv else ls.get("no_conversion", 0) + 1
        ls["last_progress"] = cls
        digest(lane["name"], f"PROGRESS {cls} (verified by the autopilot). {cnotes[:500]}")
    if not evo and ls["blank"] >= BLANK_STOP:
        ls["status"] = "STOPPED"
        owner_queue(lane["name"], f"{BLANK_STOP} consecutive generations with no verified progress of any class; lane stopped")
        digest(lane["name"], "STOPPED: no-progress rule")
        save_state(st)
        return
    if not evo and (ls["info_streak"] >= INFO_PARK or ls["no_conversion"] >= NO_CONVERSION_PARK):
        why = (f"{INFO_PARK} consecutive INFORMATION generations without a certificate or capability: research without "
               "conversion" if ls["info_streak"] >= INFO_PARK else
               f"{NO_CONVERSION_PARK} consecutive generations without a certificate or capability")
        # An Owner un-park starts a fresh window: the checkpoint is planned again, the streaks begin at 0.
        ls.update(info_streak=0, no_conversion=0, judged_for=None)
        return _park(st, ls, lane["name"], f"{why}; Owner look before the next one")
    return plan_and_arm(st, lane, ls, key, checkpoint, product, v, evo_dir, snap, dry)


AUTO_EXT_TRANCHE = 50_000_000  # one auto-extension of a research allowance (the Owner's own raises were +50M)


def note_extensions(lane_name: str, ls: dict) -> None:
    """Every auto-extension the lane consumed (evolve.consume_extension) is booked once: ledger row, digest, and an
    Owner-queue notice naming its number and the Owner turn of the grant."""
    ax = ls.get("auto_extend")
    if not isinstance(ax, dict):
        return
    noted = int(ax.get("noted") or 0)
    for e in ax.get("log") or []:
        if int(e.get("n") or 0) <= noted:
            continue
        ledger_add(lane=lane_name, kind="auto_extend", tokens=0, n=e["n"], max=ax.get("max"), why=e.get("why"))
        owner_queue(lane_name, f"NOTICE (no action needed): auto-extension {e['n']}/{ax.get('max')} under the Owner grant "
                               f"{ax.get('owner_turn')}: {e.get('why')}")
        digest(lane_name, f"AUTO-EXTENSION {e['n']}/{ax.get('max')}: {e.get('why')}")
        noted = int(e["n"])
    ax["noted"] = noted


def extend_research_if_spent(lane_name: str, ls: dict) -> bool:
    """An auto-extending lane whose research allowance cannot hold one more generation gets one tranche more."""
    left = evolve.lane_research_cap(ls) - int(ls.get("research_spent") or 0)
    if left >= evolve.RESEARCH_GEN_CAP:
        return False
    tr = int((ls.get("auto_extend") or {}).get("tranche") or AUTO_EXT_TRANCHE)
    if not evolve.consume_extension(ls, f"research allowance {left:,} left < one generation "
                                        f"({evolve.RESEARCH_GEN_CAP:,}): +{tr:,} -> "
                                        f"{evolve.lane_research_cap(ls) + tr:,}", _now()):
        return False
    ls["research_cap"] = evolve.lane_research_cap(ls) + tr
    note_extensions(lane_name, ls)
    return True


def extend_after_stop(lane_name: str, ls: dict, pend: dict, stop) -> bool:
    """An auto-extending lane whose planner stopped (after the designer had its turn) is re-planned on the next tick
    from the same judgment, told why, instead of STOPPED; each such re-plan consumes one extension."""
    if not evolve.consume_extension(ls, f"planner stop: {str(stop)[:200]}", _now()):
        return False
    note_extensions(lane_name, ls)
    pend = dict(pend, bad=[], directive=(
        "AUTO-EXTENSION (Owner 2026-11-19: 'hasta que termine todas sus funciones'): the previous plan stopped with: "
        f"{str(stop)[:700]}\nDo not stop. Name a route of a family not refuted in this lane's negative rows that "
        "targets functions not yet at 100%, cite the residual it answers, and plan it inside the research caps."))
    ls.update(pending_plan=pend, status="WAITING", judged_for=None)
    return True


def plan_and_arm(st: dict, lane: dict, ls: dict, key: str, checkpoint: str, product: str, v: dict, evo_dir: str,
                 snap: dict, dry: bool) -> None:
    """Plan the next generation from an AGREE judgment, apply the policy, arm. A policy refusal keeps the judgment
    (pending_plan, keyed by the checkpoint hold), so the re-plan after the Owner's look does not re-judge."""
    evo = evolve.enabled(HOME)
    st["next_gen"] = int(st.get("next_gen") or 28)
    name = f"S{st['next_gen']}{lane['letter']}"
    pdir = evo_dir
    pend = {"for": key, "gen": name, "verdict": {k: x for k, x in v.items() if k != "_tokens"}, "snap": snap,
            "directive": evo_dir, "next_lever": ls.get("next_lever")}
    if evo and not dry:
        extend_research_if_spent(lane["name"], ls)
    p = ({"title": "dry", "facts": ["dry"], "phases": ["Phase 1: x (cap 1M)", "Phase 2: y (cap 1M)"], "_tokens": 0}
         if dry else plan(lane, name, checkpoint, product, v, pdir))
    tok, measured = call_tokens(p.get("_tokens"))
    ledger_add(lane=lane["name"], kind="plan", tokens=tok, measured=measured, gen=name)
    designed = []

    def design_after_stop(p: dict) -> dict:
        """EVO: a planner that stops is answered with a lever (an open one of another family, else a designed one), then
        planned again. Once per plan_and_arm call. 2026-11-17 (Owner "arreglalo", pane 08cba76c): the stop of a POLICY
        RE-PLAN parked without this (KSR S143K at 19:02Z, lever retired) and waited for the Owner to invent a route."""
        nonlocal pdir
        if not (p.get("stop") and evo) or designed:
            return p
        designed.append(1)
        plevers, pgraph = evolve.load_levers(HOME), evolve.load_graph(HOME)
        cur = evolve.lever_by_id(plevers, lane["name"], ls.get("lever"))
        fam = (cur or {}).get("family") or "UNREGISTERED"
        des = None if dry else lever_designer(lane, checkpoint, product)
        if ls.get("mode") not in ("RESEARCH", "REPAIR"):
            d = evolve.plateau(ls, plevers, lane["name"], product, pgraph, fam, False, des, checkpoint)
        else:  # 2026-11-16 (WIIPARTY S98W): a research lane whose planner found no route designs one instead of stopping
            d = evolve._synth_or_park(ls, plevers, lane["name"], product, fam, des, checkpoint,
                                      f"planner stop in {ls.get('mode')}: {str(p.get('stop'))[:200]}", "planner stop")
        persist_designed(lane, d, plevers, dry)
        note_extensions(lane["name"], ls)
        ledger_add(lane=lane["name"], kind="evo_decision", tokens=0, cls="PLANNER_STOP", instruments=[],
                   action=d["action"], why=d["why"][:300], lever=(d.get("lever") or {}).get("id"), mode=ls.get("mode"),
                   selection=evolve.selection_evidence(d.get("lever"), pgraph))
        digest(lane["name"], f"EVO after planner stop: {d['action']}: {d['why'][:300]}")
        if d["action"] == "research" and not dry:
            ls["next_lever"] = d["lever"]["id"]
            pdir = d["directive"]
            p = plan(lane, name, checkpoint, product, v, pdir)
            tok, measured = call_tokens(p.get("_tokens"))
            ledger_add(lane=lane["name"], kind="plan", tokens=tok, measured=measured, gen=name)
        return p
    p = design_after_stop(p)
    if p.get("stop") and evo and not dry and extend_after_stop(lane["name"], ls, pend, p.get("stop")):
        log(f"{lane['name']}: planner stop on {name}; auto-extension: re-plan on the next tick")
        save_state(st)
        return
    if p.get("stop"):
        ls["status"] = "STOPPED"
        owner_queue(lane["name"], f"planner found no admissible next lever: {str(p.get('stop'))[:300]}")
        digest(lane["name"], f"STOPPED by planner: {str(p.get('stop'))[:400]}")
        save_state(st)
        return
    def checked(p: dict):
        """The policy checks, then (only on a policy-clean plan, whose every phase has a cap) the EVO packet checks."""
        phases, notes, title, facts, bad, text = plan_checks(lane, name, p)
        caps = 0 if bad else int(sum(float(CAP_RE.findall(l)[0]) for l in phases) * 1_000_000)
        ebad = evolve.packet_problems(ls.get("mode") or "EXPLOIT", ls.get("next_lever"), phases, caps, ls) \
            if evo and not bad else []
        return phases, notes, text, bad, ebad, caps
    phases, notes, text, bad, ebad, caps = checked(p)
    seen_bad: list = []  # every refusal of this call, told to each re-plan (S150L fixed one and dropped another)
    for attempt in range(POLICY_REPLANS if not dry else 0):
        # 2026-11-14 (S35K, S37K, S38K, S40K, S40T, S41K refused; each parked a lane for hours): bounded re-plans, each
        # told why. The policy is unchanged: every plan meets the same checks, and the last refusal parks as before.
        # 2026-11-17 (Owner "b", pane 08cba76c): an EVO packet refusal is re-planned the same way. S112T (no 'rival')
        # and S114M (caps 10.5M > 10M) parked on their first plan and sat ~10 h with 417M of the day unused.
        if not (bad or ebad):
            break
        why = bad or ebad
        seen_bad[:] = list(dict.fromkeys([*seen_bad, *why]))
        log(f"{lane['name']}: {'policy' if bad else 'EVO policy'} refused {name} (plan {attempt + 1}): "
            f"{'; '.join(why)[:300]}; re-plan with the reasons")
        p = plan(lane, name, checkpoint, product, v,
                 (pdir + "\n\n" + replan_feedback(seen_bad, p.get("_offenders"))).strip())
        tok, measured = call_tokens(p.get("_tokens"))
        ledger_add(lane=lane["name"], kind="plan", tokens=tok, measured=measured, gen=name, replan=attempt + 1)
        p = design_after_stop(p)
        if p.get("stop"):
            return _refused(st, ls, lane["name"], dict(pend, bad=why, offenders=p.get("_offenders")),
                            f"policy refused {name}; the re-plan stopped: {str(p.get('stop'))[:300]}",
                            f"POLICY REFUSED {name}; re-plan stopped", retry=False)
        phases, notes, text, bad, ebad, caps = checked(p)
    if bad:
        off = "; ".join(l[:200] for l in (p.get("_offenders") or [])[:2])
        return _refused(st, ls, lane["name"], dict(pend, bad=bad, offenders=p.get("_offenders")),
                        f"policy refused {name}: {'; '.join(bad)[:400]}" + (f" | line: {off}" if off else ""),
                        f"POLICY REFUSED {name}: {'; '.join(bad)[:400]}")
    if ebad:
        return _refused(st, ls, lane["name"], dict(pend, bad=ebad), f"EVO policy refused {name}: {'; '.join(ebad)[:400]}",
                        f"EVO POLICY REFUSED {name}: {'; '.join(ebad)[:400]}", kind="evo")
    ew = envelope_admits(lane, ledger_rows(), caps)
    if ew:
        ls["judged_for"] = None
        ls.pop("pending_plan", None)  # this park re-judges on purpose (counters restored below), as before
        ls.update(snap)  # judged again after the Owner's look: its class must not be counted twice
        return _park(st, ls, lane["name"], f"lane envelope before arming {name}: {ew}",
                     f"PARKED at the lane envelope before arming {name}: {ew}", kind="envelope")
    why = budget_admits(ledger_rows(), _now(), caps) or weekly_admits()  # T1 O4: daily and weekly, jointly
    if why and BUDGET_WAIT_KEEPS_JUDGMENT and not why.startswith(PARK_REASONS):
        # a day-cap wait: keep the judgment, the design and the directive (counted once, like a RETRY)
        ls["judged_for"] = None
        ls["pending_plan"] = dict(pend, directive=pdir, next_lever=ls.get("next_lever"), wait_caps=caps, bad=[])
        save_state(st)
        log(f"{lane['name']}: budget wait before arming {name} (judgment kept): {why}")
        return
    if why:
        ls["judged_for"] = None
        ls.pop("pending_plan", None)
        ls.update(snap)  # this checkpoint will be judged again: its class must not be counted twice
        if why.startswith(PARK_REASONS):
            return _park(st, ls, lane["name"], f"budget gate before arming {name}: {why}",
                         f"PARKED at a budget gate before arming {name}: {why}", kind="budget")
        save_state(st)
        log(f"{lane['name']}: budget wait before arming {name}: {why}")
        return
    if not dry:
        try:  # T2 W2 (b) SHADOW: counted and booked, never refused here (ENFORCE after 3 live agreements, Owner)
            prearm_shadow(lane, name, product, p)
        except Exception as e:  # noqa: BLE001 -- a shadow never blocks an arm
            log(f"{lane['name']}: pre-arm shadow failed: {e!r}")
    res = arm_generation(st, lane, ls, name, text, notes, phases, caps, dry)
    if res == "OK":
        st["next_gen"] += 1
        ls.update(status="RUNNING", gen=name, arm_fails=0, topups=0,
                  planned_from={"checkpoint": checkpoint, "verdict": {k: (str(x)[:1500] if isinstance(x, str) else x)
                                                                      for k, x in v.items() if k != "_tokens"}})
        for k in ("pending_plan", "topup_at", "topup_head", "policy_retry"):
            ls.pop(k, None)
        if evo:
            ls["lever"] = ls.pop("next_lever", None) or ls.get("lever")
            if ls.get("mode") == "RESEARCH":
                book_research(ls, name, caps)
            ledger_add(lane=lane["name"], kind="evo_arm", tokens=0, gen=name, mode=ls.get("mode") or "EXPLOIT",
                       lever=ls.get("lever"))
    elif res == "RETRY":
        ls["arm_fails"] = ls.get("arm_fails", 0) + 1
        ls["judged_for"] = None
        # 2026-11-14 (Owner 'y', pane c26eafbf): nothing irreversible happened, but the judgment and EVO already
        # counted this checkpoint; the next tick re-plans from it (resumable_plan) instead of re-judging it
        ls["pending_plan"] = pend
        if ls["arm_fails"] >= MAX_ARM_FAILS:
            ls["status"] = "PARKED"
            owner_queue(lane["name"], f"arming {name} failed {MAX_ARM_FAILS} times before any mission act; see autopilot.log")
    else:
        ls["status"] = "PARKED"
    save_state(st)


def git_ident_ok(cwd: str) -> bool:
    """A commit needs a configured identity. Without one git refuses the commit, and the arm would leave a staged tree
    that holds the next worker launch ("behind_dirty"; MKW 2026-11-14, 3.5 h idle). Read-only: checked before any change."""
    rc, _ = sh(["git", "-C", cwd, "var", "GIT_COMMITTER_IDENT"])
    return rc == 0


def arm_commit(cwd: str, paths: list, msg: str, dry: bool) -> str:
    """git add + commit of exactly `paths` (only paths that exist). '' on success, else the failing step and its output."""
    rc, out = sh(["git", "-C", cwd, "add", "-A", "--", *paths], dry=dry)
    if rc != 0:
        return f"git add failed: {out[-300:]}"
    rc, out = sh(["git", "-C", cwd, "commit", "-q", "-m", msg], dry=dry)
    return "" if rc == 0 else f"git commit failed: {out[-300:]}"


def arm_generation(st, lane, ls, name, text, notes, phases, caps, dry) -> str:
    """OK | RETRY (nothing irreversible happened) | PARK (a mission act happened and the next step failed).
    Order: every local precondition, then close old, reserve, arm, hold at once, authority, release."""
    cwd, ln = lane["cwd"], lane["name"]
    old = ls.get("mission") or lane.get("mission")

    def step(s: str, **kw) -> None:
        ls["pending_arm"] = {"gen": name, "step": s, "old": old, **kw}
        save_state(st)

    def park(why: str) -> str:
        log(f"{ln}: {why}")
        owner_queue(ln, f"arming {name} stopped after a mission act: {why[:400]} (state: {json.dumps(ls.get('pending_arm'))})")
        ls.pop("pending_arm", None)
        return "PARK"

    rc, dirty = sh(["git", "-C", cwd, "status", "--porcelain", "--", ".planning/PROJECT.md", ".planning/ROADMAP.md",
                    ".planning/STATE.md"])
    if (rc != 0 or dirty.strip()) and not dry:
        log(f"{ln}: .planning dirty or unreadable in {cwd} (rc={rc}); not arming")
        return "RETRY"
    if not dry and not git_ident_ok(cwd):
        log(f"{ln}: no git identity in {cwd} (git var GIT_COMMITTER_IDENT failed); set user.name/user.email there; "
            "not arming")
        return "RETRY"
    if lane.get("ff_from") and not ls.get("ff_done"):
        rc, out = sh(["git", "-C", cwd, "merge", "--ff-only", lane["ff_from"]], dry=dry)
        if rc != 0:
            log(f"{ln}: ff to {lane['ff_from']} failed: {out[-300:]}")
            return "RETRY"
        if not dry:
            ls["ff_done"] = True
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M")
    arch = f".planning/milestones/{(ls.get('gen') or 'pre-autopilot').lower()}-archived-{stamp}"
    present = [f for f in (".planning/PROJECT.md", ".planning/ROADMAP.md", ".planning/STATE.md") if (Path(cwd) / f).exists()]
    if present:
        sh(["mkdir", "-p", f"{cwd}/{arch}"], dry=dry)
        rc, out = sh(["git", "-C", cwd, "mv", *present, arch], dry=dry)
        if rc != 0:
            log(f"{ln}: archive failed: {out[-300:]}")
            return "RETRY"
    packet = write_packet(lane, name, text) if not dry else Path(cwd) / lane["packet_dir"] / f"{name}-PHASES.md"
    cmd = command_text(lane, name, packet, notes)
    # the archive dir exists only when there was a .planning to move (a new lane has none: MKW 2026-11-14)
    why = arm_commit(cwd, ([arch] if present else []) + [str(packet)],
                     f"{name}: autopilot packet + archive previous milestone", dry)
    if why:
        log(f"{ln}: {why}")
        return "RETRY"
    # ---- mission acts from here on: a failure parks the lane with its exact step
    if old and (mission(old) or {}).get("state") not in TERMINAL:
        step("close_old")
        spent = mission_spend(old) if not dry else 0
        prior_auth = ls.get("authority")  # None = a generation armed before the autopilot (outside its ledger)
        over = max(0, spent - prior_auth) if (spent is not None and prior_auth) else 0
        rc, out = gm("close", "--mission", old, "--outcome", "COMPLETED", "--owner-turn", OWNER_TURN, "--reason",
                     f"Autopilot: checkpoint judged; next generation {name}", dry=dry)
        if rc != 0:
            ls.pop("pending_arm", None)
            log(f"{ln}: close {old} failed (nothing armed): {out[-300:]}")
            return "RETRY"
        ledger_add(lane=ln, kind="generation_closed", mission=old, tokens=over, spend=spent, authority=prior_auth,
                   measured=spent is not None)
        freed = 0 if dry else settle(ln, old, ls.get("gen"), prior_auth, spent)["freed"]
        if freed:
            log(f"{ln}: released {freed:,} unspent reservation of {ls.get('gen')} ({old}): spent {spent:,} of {prior_auth:,}")
            credit_research(ln, ls, ls.get("gen"), freed)
    elif old and not dry and ls.get("authority"):
        # the mission ended on its own (terminal): nothing to close, but it is settled: its unspent reservation is
        # released, a spend above its booking is corrected (T2 W1: before, a terminal overrun was never booked), and
        # a generation_settled row marks it so the stranded sweep never settles it twice.
        spent = mission_spend(old)
        s = settle(ln, old, ls.get("gen"), ls.get("authority"), spent, why="terminal")
        ledger_add(lane=ln, kind="generation_settled", mission=old, gen=ls.get("gen"), tokens=0, spend=spent,
                   measured=spent is not None, why="terminal")
        credit_research(ln, ls, ls.get("gen"), s["freed"])
        if s["freed"] or s["corrected"]:
            log(f"{ln}: settled {ls.get('gen')} ({old}, terminal): spent {spent:,}; released {s['freed']:,}, "
                f"corrected {s['corrected']:,}")
    step("arm")
    ledger_add(lane=ln, kind="arm_reserve", gen=name, tokens=caps)
    hours = min(16.0, max(1.0, (WALL - dt.datetime.now(dt.timezone.utc)).total_seconds() / 3600))
    args = ["arm", "--cwd", cwd, "--command", cmd, "--milestone-from", str(packet), "--max-cycles", "12",
            "--max-hours", f"{hours:.1f}", "--permission-mode", "auto", "--no-launch"]
    for d in lane.get("add_dirs", []):
        args += ["--add-dir", d]
    rc, out = gm(*args, dry=dry)
    m = re.search(r'"mission_id":\s*"(m-[0-9a-f]+)"', out)
    new = "m-dry" if dry else (m.group(1) if m else None)
    if not new:
        ledger_add(lane=ln, kind="arm_refund", gen=name, tokens=-caps)
        return park(f"arm failed rc={rc} with no mission id (old {old} closed if it was live): {out[-300:]}")
    step("hold", new=new)
    rc, out = gm("hold", "--mission", new, "--reason", f"autopilot: arming {name}; held until authority is set", dry=dry)
    if rc != 0:
        gm("close", "--mission", new, "--outcome", "HALTED", "--owner-turn", OWNER_TURN,
           "--reason", "autopilot: could not hold the new record before authority; never launch unbounded", dry=dry)
        return park(f"hold of new {new} failed: {out[-300:]}")
    rc, out = gm("authority", "--mission", new, "--tokens", str(caps), "--owner-turn", OWNER_TURN,
                 "--reason", f"Autopilot {name}: phase caps {caps:,} <= 25M per generation (Owner typed authorization)", dry=dry)
    if rc != 0:
        ledger_add(lane=ln, kind="arm_refund", gen=name, tokens=-caps)
        return park(f"authority on {new} refused (record stays held): {out[-300:]}")
    step("scaffold_commit", new=new)
    sh(["git", "-C", cwd, "add", ".planning/PROJECT.md", ".planning/ROADMAP.md", ".planning/STATE.md"], dry=dry)
    sh(["git", "-C", cwd, "commit", "-q", "-m", f"{name}: scaffold milestone (mission {new}, authority {caps:,})"], dry=dry)
    base = None if dry else _sha(lane["product"], "HEAD")  # the window this generation's evidence must fall in
    if not base and not dry:
        log(f"{ln}: product HEAD unreadable at arm; {name}'s progress will classify NONE")
    prof = worker_profile(lane)
    if prof:  # T2 W3b: set while the record is still held, so its first launch is already the slim one
        rc, out = gm("envelope", "--mission", new, "--worker-profile", prof, dry=dry)
        ledger_add(lane=ln, kind="worker_profile_set", mission=new, gen=name, tokens=0, profile=prof, ok=rc == 0)
        if rc != 0:
            return park(f"worker profile {prof} on {new} refused (record stays held): {out[-300:]}")
    rc, out = gm("release", "--mission", new, dry=dry)
    if rc != 0:
        return park(f"release of {new} failed (armed with authority, still held): {out[-300:]}")
    ls["mission"], ls["authority"], ls["base"] = new, caps, base
    ls.pop("pending_arm", None)
    ledger_add(lane=ln, kind="generation_armed", mission=new, gen=name, tokens=0, authority=caps)
    digest(ln, f"ARMED {name} as {new}, authority {caps:,}. Phases:\n" + "\n".join(f"  {l[:200]}" for l in phases))
    log(f"{ln}: armed {name} as {new} ({caps:,})")
    return "OK"


def killed() -> bool:
    return (HOME / "OFF").exists()


def _lock():
    """Exclusive non-blocking lock inside the process (the cron flock is not the only guard). None = not acquired."""
    try:
        import fcntl
    except ImportError:  # Windows test host: no concurrent ticks there
        return True
    f = open(HOME / "autopilot.lock", "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f


def factory_applying(name: str) -> bool:
    """Owner 2026-11-20 ("yes, all for autonomy", pane aa9f2e25): the 0-token factory lane (agora/factory/lane.py)
    applies a gated commit holding HOME/factory-apply-<LANE>.lock instead of cron.lock for a whole lane build (a WSR
    apply held cron.lock ~50 min and every lane's tick waited). It takes that lock under cron.lock, so a lane whose
    lock is held is mid-apply: this tick leaves that lane alone and runs the others. True = held (skip the lane)."""
    try:
        import fcntl
    except ImportError:  # Windows test host: no factory lane there
        return False
    f = open(HOME / f"factory-apply-{name}.lock", "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return True
    finally:
        f.close()
    return False


SETTLED_KINDS = ("generation_closed", "generation_settled")


def stranded(rows: list[dict], state_of, live: set) -> list[dict]:
    """T2 W1: armed generations with no close/settle row whose mission is terminal and is no lane's live mission
    (current, halted-but-resumable, or a pending continuation). Measured 2026-11-22: 71 HALTED held 705.7M of escrow."""
    done = {r.get("mission") for r in rows if r.get("kind") in SETTLED_KINDS}
    out = {}
    for r in rows:
        m = r.get("mission")
        if r.get("kind") != "generation_armed" or not m or m in done or m in live or m in out:
            continue
        if state_of(m) in TERMINAL:
            out[m] = {"lane": r.get("lane"), "mission": m, "gen": r.get("gen"),
                      "authority": r.get("authority"), "ts": float(r["ts"])}
    return list(out.values())


def live_missions(st: dict) -> set:
    live = set()
    for ls in (st.get("lanes") or {}).values():
        for k in ("mission", "halted_mission", "continued_from"):
            if ls.get(k):
                live.add(ls[k])
        f = str((ls.get("pending_plan") or {}).get("for") or "")
        if f.startswith("continue:"):
            live.add(f.split(":", 1)[1])
    return live


def conservation(rows: list[dict]) -> dict:
    """Per settled generation: booked_net - measured spend. 0 = conserved; < 0 = spend the ledger does not count."""
    gen_of = {r.get("mission"): r.get("gen") for r in rows if r.get("kind") == "generation_armed"}
    res = {}
    for r in rows:
        if r.get("kind") in SETTLED_KINDS and r.get("measured") and isinstance(r.get("spend"), int):
            m = r.get("mission")
            if m in gen_of:
                res[m] = booked_net(rows, m, gen_of[m]) - r["spend"]
    bad = {m: d for m, d in res.items() if d}
    return {"settled": len(res), "conserved": len(res) - len(bad), "under": {m: d for m, d in bad.items() if d < 0},
            "over": {m: d for m, d in bad.items() if d > 0}}


def settle_stranded(st: dict, apply: bool) -> dict:
    """The sweep: each stranded generation is settled at its measured spend (unmeasured releases nothing and is
    marked). Dry unless `apply`. A spend correction is dated on the generation's arm day."""
    rows = ledger_rows()
    todo = stranded(rows, lambda m: (mission(m) or {}).get("state"), live_missions(st))
    rep = {"stranded": len(todo), "measured": 0, "unmeasured": 0, "freed": 0, "corrected": 0}
    for g in todo:
        spent = mission_spend(g["mission"])
        if spent is None:
            rep["unmeasured"] += 1
        else:
            rep["measured"] += 1
        if not apply:
            if spent is not None:
                rep["freed"] += max(0, booked_net(rows, g["mission"], g["gen"]) - spent)
                rep["corrected"] += spend_correction(rows, g["mission"], g["gen"], spent)
            continue
        auth = g["authority"] or 1  # an autopilot-armed generation: its arm row is the authority evidence
        s = settle(g["lane"], g["mission"], g["gen"], auth, spent, at=g["ts"], why="stranded_sweep") if spent is not None \
            else {"freed": 0, "corrected": 0}
        ledger_add(lane=g["lane"], kind="generation_settled", mission=g["mission"], gen=g["gen"], tokens=0,
                   spend=spent, measured=spent is not None, why="stranded_sweep")
        rep["freed"] += s["freed"]
        rep["corrected"] += s["corrected"]
        lsx = (st.get("lanes") or {}).get(g["lane"])
        if lsx is not None and s["freed"]:
            credit_research(g["lane"], lsx, g["gen"], s["freed"])
    # already-settled generations whose books do not balance (FIFATC S95C -3M, KSR S53K/S181K owner escrow kept)
    rows = ledger_rows()
    close = {r.get("mission"): r for r in rows if r.get("kind") in SETTLED_KINDS and r.get("measured")}
    gen_of = {r.get("mission"): r.get("gen") for r in rows if r.get("kind") == "generation_armed"}
    cons = conservation(rows)
    rep["reconciled"] = {**cons["under"], **cons["over"]}
    for m, d in rep["reconciled"].items():
        c = close[m]
        if apply:
            settle(c.get("lane"), m, gen_of[m], 1, c["spend"], at=float(c["ts"]), why="reconcile")
        elif d > 0:
            rep["freed"] += d
        else:
            rep["corrected"] += -d
    return rep


def main(argv: list[str]) -> int:
    global OUT
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "conservation":
        print(json.dumps(conservation(ledger_rows()), indent=1))
        return 0
    if cmd == "status":
        print(json.dumps(load_state(), indent=1))
        rows = ledger_rows()
        total, today = spend_totals(rows, _now())
        print(f"ledger total {total:,} / {TOTAL_CAP:,}; today {today:,} / {DAY_CAP:,}; "
              f"unmeasured calls {sum(1 for r in rows if r.get('measured') is False)}")
        return 0
    if cmd == "answer":  # round 3: `autopilot.py answer <LANE> <ruling text>` ('-' reads the text from stdin)
        names = [l["name"] for l in json.loads((HOME / "lanes.json").read_text())]
        if len(argv) < 4 or argv[2] not in names:
            print(f"usage: autopilot.py answer <LANE> <ruling text | ->; lanes: {', '.join(names)}")
            return 2
        text = sys.stdin.read() if argv[3:] == ["-"] else " ".join(argv[3:])
        try:
            print(json.dumps(record_answer(argv[2], text)))
        except ValueError as exc:
            print(f"refused: {exc}")
            return 2
        print("recorded; the next autopilot tick (at most ~5 min) applies it")
        return 0
    if killed():
        return 0
    if not OWNER_TURN.split(":", 1)[1]:
        log("refused: AP_OWNER_TS unset")
        return 2
    lock = _lock()
    if lock is None:
        print("another tick holds the lock; nothing done")
        return 0
    if cmd == "reconcile":  # round 4: `autopilot.py reconcile <LANE> [--apply]`, under the tick lock; dry by default
        lanes_ = {l["name"]: l for l in json.loads((HOME / "lanes.json").read_text())}
        st_ = load_state()
        if len(argv) < 3 or argv[2] not in lanes_ or argv[2] not in (st_.get("lanes") or {}):
            print(f"usage: autopilot.py reconcile <LANE> [--apply]; lanes: {', '.join(lanes_)}")
            return 2
        ls_ = st_["lanes"][argv[2]]
        rec_ = (mission(ls_["mission"]) if ls_.get("mission") else None) or {}
        res = reconcile_stranded(lanes_[argv[2]], ls_, rec_, "--apply" not in argv) or "nothing stranded"
        if res.startswith("autopilot: bring"):
            ls_["held_grace_until"] = _now() + HELD_REPLAN_S
            save_state(st_)
        print(res)
        return 0
    if cmd == "settle-stranded":  # T2 W1: under the tick lock; dry unless --apply
        print(json.dumps(settle_stranded(load_state(), "--apply" in argv), indent=1, default=str))
        return 0
    dry = cmd == "dry-tick"
    if dry:
        OUT = Path(tempfile.mkdtemp(prefix="ap-dry-"))
        for f in ("state.json", "ledger.jsonl"):
            if (HOME / f).exists():
                shutil.copy2(HOME / f, OUT / f)
        print(f"dry-tick: scratch state in {OUT}")
    lanes = json.loads((HOME / "lanes.json").read_text())
    st = load_state()
    if not dry:
        try:
            n = sweep_own_tmp()
            if n:
                log(f"tmp sweep: removed {n} own scratch dirs older than {TMP_SWEEP_AGE_S // 3600} h")
        except Exception as exc:  # noqa: BLE001 -- a sweep never stops a tick
            log(f"tmp sweep failed: {exc!r}")
    dwhy = disk_admits()
    if dwhy:
        try:
            if not st.get("disk_wait"):
                st["disk_wait"] = {"since": _now(), "why": dwhy}
                log(f"disk floor: {dwhy}; no lane is ticked until it clears")
                owner_queue("ALL", f"disk floor: {dwhy}; every lane waits (nothing judged, planned or armed)")
            save_state(st)
        except OSError:
            pass  # a full disk: nothing was changed, the next tick tries again
        write_alerts(st)
        return 0
    if st.pop("disk_wait", None) is not None:
        log("disk floor cleared: lanes are ticked again")
        save_state(st)
    seen0 = st.get("answers_seen")
    try:
        if not dry:
            auto_rule(st, lanes)
            save_state(st)  # also keeps each refused question's key, so it is told once
    except Exception as exc:  # noqa: BLE001 -- the auto-ruling never stops a tick
        log(f"auto-ruling skipped: {exc!r}")
    try:
        took = take_answers(st, {l["name"] for l in lanes})
    except Exception as exc:  # noqa: BLE001 -- an unreadable inbox never stops a tick
        took = 0
        log(f"owner answers not taken: {exc!r}")
    if took or st.get("answers_seen") != seen0:
        save_state(st)
    for lane in lanes:
        if factory_applying(lane["name"]):
            log(f"{lane['name']}: factory lane mid-apply (factory-apply-{lane['name']}.lock held); lane skipped this tick")
            continue
        tick_lane(st, lane, dry)
    write_alerts(st)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
