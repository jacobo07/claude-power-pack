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
import time
import unicodedata
from pathlib import Path

HOME = Path(os.environ.get("AP_HOME", "/home/kobii/agora/ascension-autopilot"))
OUT = HOME  # where state/ledger/log/digest/owner_queue are written; a scratch dir in dry-tick
PP = Path(os.environ.get("AP_PP", "/home/kobii/.claude/skills/claude-power-pack"))
STATE_DIR = Path(os.environ.get("AP_STATE_DIR", "/home/kobii/.claude/state"))
CLAUDE = os.environ.get("AP_CLAUDE", "/usr/local/bin/claude")
OWNER_TURN = "d957c937-f56d-4447-9386-5d8002fe0b90:" + os.environ.get("AP_OWNER_TS", "")
TOTAL_CAP = 400_000_000
DAY_CAP = 80_000_000
GEN_CAP = 25_000_000
FRESH_GEN_CAP = 1_000_000
CALL_RESERVE = 2_000_000  # booked for a judge/planner call whose usage could not be measured (never 0)
# Authority granted before the autopilot existed that the Owner counts inside TOTAL_CAP (not inside a day's cap:
# it was not granted by the autopilot). Owner 2026-11-11 (pane fa41bae9): "S27's 200M ... it adds to that".
PRIOR_AUTHORITY = (("m-10566700b1fe", "S27", 200_000_000),)
# Owner 2026-11-11 (pane fa41bae9) approved AUTOPILOT-REORIENT-PLAN ("y"): a 60M processed ceiling for diagnosis, pilots
# and integration on top of what was booked at approval: 225,261,779 = PRIOR 200M + ledger 25,261,779 (judge/planner
# 4,761,779 + S28K's 20.5M). Everything between UNLOCKED_CAP and TOTAL_CAP is FROZEN behind value gates: the autopilot
# can only ask for it (owner_queue), never release it.
UNLOCKED_CAP = 285_261_779
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
_TARGET = (r"(certifier|certify\.py|certify\.decide|cert_cxx\w*|ksr_lane\w*|canonical\s+(ctx|context|headers?)|"
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
PHASE_RE = re.compile(r"^Phase (\d+): (.+)$")
CAP_RE = re.compile(r"\bcap\s+(\d+(?:\.\d+)?)\s*M\b", re.I)
FRESH_RE = re.compile(r"\bfresh\b[^.;]{0,30}?(\d[\d,]*(?:\.\d+)?)\s*([MmKk]\b)?")


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
    for num, unit in FRESH_RE.findall(text):
        if _fresh_tokens(num, unit) > FRESH_GEN_CAP:
            bad.append(f"asks fresh {num}{unit or ''} > {FRESH_GEN_CAP/1e6:.0f}M")
    for pat, label in FORBIDDEN:
        if re.search(pat, text, re.I) and f"forbidden act: {label}" not in bad:
            bad.append(f"forbidden act: {label}")
    for line in text.splitlines():
        if not re.search(PROFILE_TRIGGER, line, re.I):
            continue
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


def verify_cert(v: dict, product: str, base):
    """None = not claimed; True = verified; str = claimed but refused."""
    n = v.get("new_canonical_certs")
    if type(n) is not int or n <= 0:
        return None
    recs = v.get("cert_receipts")
    if not isinstance(recs, list) or not recs:
        return "certificates claimed without cert_receipts [{path, commit}]"
    ids: set[str] = set()
    for r in recs:
        path, commit = (str(r.get("path") or ""), str(r.get("commit") or "")) if isinstance(r, dict) else ("", "")
        if not DATA.search(path) or not in_window(product, base, commit) or path not in _changed(product, commit):
            return f"receipts {path}@{commit} is not a data file changed by a commit of this generation"
        rc, diff = _git(product, "diff", "-U0", _sha(product, base), _sha(product, commit), "--", path)
        for line in diff.splitlines() if rc == 0 else []:
            if not line.startswith("+") or line.startswith("+++"):
                continue
            try:
                row = json.loads(line[1:])
            except Exception:  # noqa: BLE001 -- a non-JSON added line is not a receipt
                continue
            if isinstance(row, dict) and "CERTIFIED" in [x for x in row.values() if isinstance(x, str)]:
                ids.add(str(row.get("id") or line[1:]))
    return True if len(ids) >= n else f"{len(ids)} distinct CERTIFIED rows added since the base < claimed {n}"


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


def classify_progress(v: dict, product: str, base=None) -> tuple[str, str]:
    """CERT > CAPABILITY > INFORMATION > NONE; the first class whose evidence verifies inside base..HEAD.
    No base recorded = nothing can be anchored = NONE. Notes say why claims failed."""
    notes = [] if base else ["no generation base recorded: no pointer can be anchored"]
    for cls, fn in (("CERT", verify_cert), ("CAPABILITY", verify_capability), ("INFORMATION", verify_information)):
        r = fn(v, product, base)
        if r is True:
            return cls, "; ".join(notes)
        if isinstance(r, str):
            notes.append(f"{cls} refused: {r}")
    return "NONE", "; ".join(notes)


def agree_supported(v: dict) -> bool:
    """AGREE counts only with its own evidence: protected_ok true and every listed gate rc == 0 (at least one)."""
    gates = v.get("gates")
    return (v.get("verdict") == "AGREE" and v.get("protected_ok") is True and isinstance(gates, list) and bool(gates)
            and all(isinstance(g, dict) and type(g.get("rc")) is int and g["rc"] == 0 for g in gates))


JUDGE_TOOLS = ["Read", "Grep", "Glob", "Bash(timeout 600 python3 tools/:*)", "Bash(python3 tools/:*)",
               "Bash(sha256sum:*)", "Bash(wc:*)", "Bash(git log:*)", "Bash(git status:*)", "Bash(git show:*)",
               "Bash(ls:*)"]


def judge(lane: dict, checkpoint: str, product: str) -> dict:
    prompt = (HOME / "judge_prompt.md").read_text().replace("{CHECKPOINT}", checkpoint).replace("{PRODUCT}", product)
    r = run_claude(prompt, cwd=product, tools=JUDGE_TOOLS, add_dirs=[lane["cwd"]], max_turns=60, timeout=3600)
    v = last_json(r.get("result", "")) or {}
    v["_tokens"] = r.get("tokens")
    v["_session"] = r.get("session")
    if not r.get("ok") or v.get("verdict") not in ("AGREE", "DISAGREE", "INCONCLUSIVE"):
        v["verdict"] = "INCONCLUSIVE"
        v["notes"] = r.get("error") or "judge reply did not end with a verdict JSON"
    return v


def plan(lane: dict, name: str, checkpoint: str, product: str, verdict: dict) -> dict:
    prompt = ((HOME / "planner_prompt.md").read_text().replace("{NAME}", name).replace("{LANE}", lane["name"])
              .replace("{CHECKPOINT}", checkpoint).replace("{PRODUCT}", product)
              .replace("{VERDICT}", json.dumps({k: v for k, v in verdict.items() if not k.startswith("_")})[:3000])
              .replace("{DIGEST}", str(OUT / "digest.md")).replace("{BRIEF}", str(HOME / "brief.md")))
    r = run_claude(prompt, cwd=product, tools=["Read", "Grep", "Glob", "Bash(git log:*)", "Bash(ls:*)"],
                   add_dirs=[lane["cwd"], "/home/kobii/missions/gen3-pp", "/home/kobii/missions/recon-general", str(HOME)],
                   max_turns=50, timeout=3600)
    p = last_json(r.get("result", "")) or {}
    p["_tokens"] = r.get("tokens")
    return p


HEADER = """# {name}: {title} (Ascension Autopilot, lane {lane}; Owner typed authorization 2026-11-11, laptop pane d957c937)

Mission terms: open-ended reconstruction, method evolution, independent certification, constitutive baseline ratchet.

Authority: this generation's own mission record, <= {cap}M processed (sum of the phase caps; closeout included), fresh <= 1M only
where a phase names it, USD 0, no push. Per-phase caps in each phase line, measured from the record spend at phase start.
NOT authorised: writes to pinned stages (ksrmb-20261001-101754, ksrmb-s25-20261111-140212) or any receipts file
(cert1-ksr 8,687, cert1-ksr-s25stage, Tennis receipts); KSR/Tennis frontier files; certify.py / cert_cxx.py / ksr_lane rules
and existing profiles; canonical ctx and headers; H2; R2; merging counters into any headline; revoking any certificate
(contradictions go to the Owner queue); push; paid or cloud usage; any budget change. A NEW additive profile is allowed only
with ALL S26C conditions: independent target oracle on original DOL bytes, frozen pilot committed before the draw, pre/post
controls, A2 negatives, historical receipts byte-identical, separate counters. UNKNOWN and INSTRUMENT_FAIL are never zero;
BINARY_EXACT is never CERTIFIED. Every gate has planted mutants that must turn it red. Freeze before you judge.

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


def command_text(lane: dict, name: str, packet: Path, notes: str) -> str:
    rel = packet.relative_to(lane["cwd"])
    return (f"Execute {name} of the Ascension programme (Autopilot lane {lane['name']}; open-ended reconstruction, method "
            f"evolution, independent certification). This cwd ({lane['cwd']}) is the CONTROL repo; the PRODUCT is "
            f"{lane['product']}. FIRST read {rel} in full (authority, NOT-authorised list, facts, phases with caps); it binds. "
            f"Then run /gsd-autonomous on the {name} milestone in .planning. {notes} "
            "Freeze in a commit before anything judged on it; gates with planted mutants; micro-commit owned files only and "
            "never stage pre-existing dirty residue; keep a budget.md with measured spend per phase (gsd_mission.py topology "
            "--mission <this mission>); stop a phase at its cap; no push, no paid API. At the end: gsd_mission.py checkpoint "
            f"CHECKPOINT_COMPLETE with an evidence checkpoint file for {name} that states new canonical certificates (per "
            "profile, by function identity) and validated capabilities.")


def _park(st: dict, ls: dict, lane: str, queue: str, dig: str | None = None) -> None:
    ls["status"] = "PARKED"
    owner_queue(lane, queue)
    if dig:
        digest(lane, dig)
    save_state(st)


# ---------------------------------------------------------------- the per-lane transition
def lane_tick(st: dict, lane: dict, dry: bool) -> None:
    ls = st.setdefault("lanes", {}).setdefault(lane["name"], {"status": "WAITING", "blank": 0, "arm_fails": 0, "gen": None})
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
            return _park(st, ls, lane["name"], f"mission {mid} ended {rec['state']} without a checkpoint hold; lane parked")
        if hold.get("kind") != "checkpoint":
            return
        checkpoint = hold.get("evidence") or ""
        if ls.get("judged_for") == f"{mid}:{hold.get('set_at')}":
            return
        ls["judged_for"] = f"{mid}:{hold.get('set_at')}"
    else:
        pat, product = lane["bootstrap_checkpoint"], lane.get("bootstrap_product", lane["product"])
        if ls.get("judged_for") == "bootstrap":
            return
        hits = sorted(Path(pat).parent.glob(Path(pat).name))
        if not hits:
            return
        checkpoint = str(hits[-1])
        ls["judged_for"] = "bootstrap"
    save_state(st)
    why = budget_admits(ledger_rows(), _now(), GEN_CAP + 2 * CALL_RESERVE)
    if why:
        ls["judged_for"] = None
        if why.startswith(PARK_REASONS):  # only the day cap is a wait; frozen/total/wall need the Owner
            return _park(st, ls, lane["name"], f"budget gate: {why}", f"PARKED at a budget gate: {why}")
        save_state(st)
        log(f"{lane['name']}: budget wait: {why}")
        return
    log(f"{lane['name']}: checkpoint {checkpoint} -> judge")
    v = ({"verdict": "AGREE", "new_canonical_certs": 0, "validated_capability": False, "protected_ok": True,
          "gates": [{"cmd": "dry", "rc": 0}], "_tokens": 0} if dry else judge(lane, checkpoint, product))
    tok, measured = call_tokens(v.get("_tokens"))
    ledger_add(lane=lane["name"], kind="judge", tokens=tok, measured=measured, verdict=v.get("verdict"), checkpoint=checkpoint)
    if v.get("verdict") == "AGREE" and not agree_supported(v):
        v["verdict"] = "INCONCLUSIVE"
        v["notes"] = f"AGREE without its own evidence (protected_ok/gates rc): {str(v.get('notes', ''))[:400]}"
    pbad = protected_check(lane)
    if v.get("verdict") == "AGREE" and pbad:
        v["verdict"] = "DISAGREE"
        v["notes"] = f"autopilot protected check: {pbad}"
    digest(lane["name"], f"JUDGE {v.get('verdict')} on {checkpoint}: new certs {v.get('new_canonical_certs')}, "
                         f"capability {v.get('validated_capability')}. {str(v.get('notes', ''))[:600]}")
    if v.get("verdict") != "AGREE":
        return _park(st, ls, lane["name"], f"judge {v.get('verdict')} on {checkpoint}: {str(v.get('notes', ''))[:300]}")
    snap = {k: ls.get(k, 0) for k in ("blank", "info_streak", "no_conversion")}  # restored if this judgment is redone
    cls, cnotes = classify_progress(v, product, ls.get("base"))
    conv = cls in ("CERT", "CAPABILITY")
    ls["blank"] = ls.get("blank", 0) + 1 if cls == "NONE" else 0
    ls["info_streak"] = ls.get("info_streak", 0) + 1 if cls == "INFORMATION" else 0
    ls["no_conversion"] = 0 if conv else ls.get("no_conversion", 0) + 1
    ls["last_progress"] = cls
    digest(lane["name"], f"PROGRESS {cls} (verified by the autopilot). {cnotes[:500]}")
    if ls["blank"] >= BLANK_STOP:
        ls["status"] = "STOPPED"
        owner_queue(lane["name"], f"{BLANK_STOP} consecutive generations with no verified progress of any class; lane stopped")
        digest(lane["name"], "STOPPED: no-progress rule")
        save_state(st)
        return
    if ls["info_streak"] >= INFO_PARK or ls["no_conversion"] >= NO_CONVERSION_PARK:
        why = (f"{INFO_PARK} consecutive INFORMATION generations without a certificate or capability: research without "
               "conversion" if ls["info_streak"] >= INFO_PARK else
               f"{NO_CONVERSION_PARK} consecutive generations without a certificate or capability")
        # An Owner un-park starts a fresh window: the checkpoint is planned again, the streaks begin at 0.
        ls.update(info_streak=0, no_conversion=0, judged_for=None)
        return _park(st, ls, lane["name"], f"{why}; Owner look before the next one")
    st["next_gen"] = int(st.get("next_gen") or 28)
    name = f"S{st['next_gen']}{lane['letter']}"
    p = ({"title": "dry", "facts": ["dry"], "phases": ["Phase 1: x (cap 1M)", "Phase 2: y (cap 1M)"], "_tokens": 0}
         if dry else plan(lane, name, checkpoint, product, v))
    tok, measured = call_tokens(p.get("_tokens"))
    ledger_add(lane=lane["name"], kind="plan", tokens=tok, measured=measured, gen=name)
    if p.get("stop"):
        ls["status"] = "STOPPED"
        owner_queue(lane["name"], f"planner found no admissible next lever: {str(p.get('stop'))[:300]}")
        digest(lane["name"], f"STOPPED by planner: {str(p.get('stop'))[:400]}")
        save_state(st)
        return
    phases, notes, title, facts = planner_strings(p)
    bad = policy_check(phases, notes, [title, *facts])
    text = packet_text(lane, name, p) if not bad else ""
    if not bad:
        drift = packet_phase_drift(text, phases)
        if drift:
            bad.append(drift)
    if bad:
        return _park(st, ls, lane["name"], f"policy refused {name}: {'; '.join(bad)[:400]}",
                     f"POLICY REFUSED {name}: {'; '.join(bad)[:400]}")
    caps = int(sum(float(CAP_RE.findall(l)[0]) for l in phases) * 1_000_000)
    why = budget_admits(ledger_rows(), _now(), caps)
    if why:
        ls["judged_for"] = None
        ls.update(snap)  # this checkpoint will be judged again: its class must not be counted twice
        if why.startswith(PARK_REASONS):
            return _park(st, ls, lane["name"], f"budget gate before arming {name}: {why}",
                         f"PARKED at a budget gate before arming {name}: {why}")
        save_state(st)
        log(f"{lane['name']}: budget wait before arming {name}: {why}")
        return
    res = arm_generation(st, lane, ls, name, text, notes, phases, caps, dry)
    if res == "OK":
        st["next_gen"] += 1
        ls.update(status="RUNNING", gen=name, arm_fails=0)
    elif res == "RETRY":
        ls["arm_fails"] = ls.get("arm_fails", 0) + 1
        ls["judged_for"] = None
        if ls["arm_fails"] >= MAX_ARM_FAILS:
            ls["status"] = "PARKED"
            owner_queue(lane["name"], f"arming {name} failed {MAX_ARM_FAILS} times before any mission act; see autopilot.log")
    else:
        ls["status"] = "PARKED"
    save_state(st)


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
    rc, out = sh(["git", "-C", cwd, "add", "-A", "--", arch, str(packet)], dry=dry)
    if rc != 0:
        log(f"{ln}: git add failed: {out[-300:]}")
        return "RETRY"
    sh(["git", "-C", cwd, "commit", "-q", "-m", f"{name}: autopilot packet + archive previous milestone"], dry=dry)
    # ---- mission acts from here on: a failure parks the lane with its exact step
    if old and (mission(old) or {}).get("state") not in TERMINAL:
        step("close_old")
        spent = mission_spend(old) if not dry else 0
        prior_auth = ls.get("authority")  # None = a generation armed before the autopilot (outside its ledger)
        over = max(0, spent - prior_auth) if (spent is not None and prior_auth) else 0
        rc, out = gm("close", "--mission", old, "--outcome", "COMPLETED", "--owner-turn", OWNER_TURN, "--reason",
                     f"Autopilot: checkpoint judged AGREE; next generation {name}", dry=dry)
        if rc != 0:
            ls.pop("pending_arm", None)
            log(f"{ln}: close {old} failed (nothing armed): {out[-300:]}")
            return "RETRY"
        ledger_add(lane=ln, kind="generation_closed", mission=old, tokens=over, spend=spent, authority=prior_auth,
                   measured=spent is not None)
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


def main(argv: list[str]) -> int:
    global OUT
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "status":
        print(json.dumps(load_state(), indent=1))
        rows = ledger_rows()
        total, today = spend_totals(rows, _now())
        print(f"ledger total {total:,} / {TOTAL_CAP:,}; today {today:,} / {DAY_CAP:,}; "
              f"unmeasured calls {sum(1 for r in rows if r.get('measured') is False)}")
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
    dry = cmd == "dry-tick"
    if dry:
        OUT = Path(tempfile.mkdtemp(prefix="ap-dry-"))
        for f in ("state.json", "ledger.jsonl"):
            if (HOME / f).exists():
                shutil.copy2(HOME / f, OUT / f)
        print(f"dry-tick: scratch state in {OUT}")
    lanes = json.loads((HOME / "lanes.json").read_text())
    st = load_state()
    for lane in lanes:
        try:
            lane_tick(st, lane, dry)
        except Exception as exc:  # noqa: BLE001 -- one lane's failure never stops the other; it is logged and parked
            log(f"{lane['name']}: ERROR {type(exc).__name__}: {exc}")
            st.setdefault("lanes", {}).setdefault(lane["name"], {})["status"] = "PARKED"
            owner_queue(lane["name"], f"autopilot error {type(exc).__name__}: {str(exc)[:200]}")
            save_state(st)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
