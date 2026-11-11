#!/usr/bin/env python3
"""Ascension Autopilot: self-continuing S generations on two lanes (KSR, Tennis).

Owner authorization (typed, 2026-11-11, laptop pane d957c937): "Apruebo autopilot: 400M total, 80M/dia, hasta
2026-11-30, 25M max por generacion, perfiles aditivos con condiciones S26C, dos carriles KSR y Tennis".
Plan: laptop vault/programs/ascension/AUTOPILOT-PLAN.md. One generation = one mission record:
checkpoint -> independent JUDGE -> PLANNER -> deterministic POLICY -> BUDGET -> close old, arm new, authority once.
Reuses tools/gsd_mission.py for every mission act; owns only its state/ledger/digest files.
Kill switch: file OFF in this directory. Usage: autopilot.py tick | status | dry-tick
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HOME = Path(os.environ.get("AP_HOME", "/home/kobii/agora/ascension-autopilot"))
PP = Path(os.environ.get("AP_PP", "/home/kobii/.claude/skills/claude-power-pack"))
STATE_DIR = Path(os.environ.get("AP_STATE_DIR", "/home/kobii/.claude/state"))
CLAUDE = os.environ.get("AP_CLAUDE", "/usr/local/bin/claude")
OWNER_TURN = "d957c937-f56d-4447-9386-5d8002fe0b90:" + os.environ.get("AP_OWNER_TS", "")
TOTAL_CAP = 400_000_000
DAY_CAP = 80_000_000
GEN_CAP = 25_000_000
FRESH_GEN_CAP = 1_000_000
WALL = dt.datetime(2026, 11, 30, 23, 59, tzinfo=dt.timezone.utc)
BLANK_STOP = 3
MAX_ARM_FAILS = 2
TERMINAL = {"COMPLETED", "HALTED", "ORPHANED"}

# ---------------------------------------------------------------- policy (deterministic, no model)
FORBIDDEN = [
    (r"\bgit\s+push\b|\bpush\b(?!ed\b)", "push"),
    (r"merg\w*\b[^.;]*\b(headline|counter|counters)\b", "merge counters into a headline"),
    (r"\brevo(ke|king|cation|ked)\b", "revocation"),
    (r"\bR2\b", "R2"),
    (r"\bH2\b", "H2"),
    (r"\b(modify|modifies|modifying|change|changes|changing|edit|edits|editing|patch|patches|patching|rewrite|"
     r"relax|relaxes|relaxing|weaken|weakens|weakening)\w*\s+(the\s+)?(certifier|certify\.py|cert_cxx(\.py)?|"
     r"canonical\s+(ctx|context|headers?)|historical\s+receipts?|pinned\s+stage|receipts?)", "certifier/canonical/receipt change"),
    (r"\bpaid\b|ANTHROPIC_API_KEY|\bapi\s+key\b|\bcloud\b", "paid/cloud"),
    (r"\bnew\s+(budget|authority)\b|\braise\w*\s+(the\s+)?(budget|authority|cap)", "budget change"),
]
PROFILE_TRIGGER = r"\b(new|create|creates|creating|add|adds|adding|register|registers)\b[^.;]{0,40}\bprofile\b"
PROFILE_CONDITIONS = {
    "independent target oracle": r"\boracle\b",
    "original DOL bytes": r"\bDOL\b",
    "frozen pilot committed before the draw": r"\b(frozen|freeze)\b[^.;]*\bpilot\b|\bpilot\b[^.;]*\b(frozen|freeze)\b",
    "pre/post controls": r"\bcontrols?\b",
    "A2 negatives": r"\bA2\b|\bnegative(s)?\b",
    "historical receipts unchanged": r"\breceipts?\b[^.;]*\b(unchanged|byte-identical|untouched)\b|\b(unchanged|byte-identical|untouched)\b[^.;]*\breceipts?\b",
    "separate counters": r"\bseparate\b[^.;]*\bcounters?\b|\bcounters?\b[^.;]*\bseparate\b",
}
PHASE_RE = re.compile(r"^Phase (\d+): (.+)$")
CAP_RE = re.compile(r"\bcap\s+(\d+(?:\.\d+)?)\s*M\b", re.I)
FRESH_RE = re.compile(r"\bfresh\b[^.;]{0,30}?(\d+(?:\.\d+)?)\s*M\b", re.I)


def policy_check(phase_lines: list[str], command: str) -> list[str]:
    """Return the list of violations (empty = admitted). Judges only the planner's phase lines and command:
    the authority header and NOT-authorised block are written by the autopilot itself."""
    bad: list[str] = []
    if not 2 <= len(phase_lines) <= 8:
        bad.append(f"{len(phase_lines)} phase lines (need 2-8)")
    total = 0.0
    for i, line in enumerate(phase_lines, 1):
        m = PHASE_RE.match(line)
        if not m or int(m.group(1)) != i:
            bad.append(f"line {i} is not 'Phase {i}: ...'")
            continue
        caps = CAP_RE.findall(line)
        if not caps:
            bad.append(f"Phase {i} has no 'cap <N>M'")
        else:
            total += float(caps[0])
        for f in FRESH_RE.findall(line):
            if float(f) * 1_000_000 > FRESH_GEN_CAP:
                bad.append(f"Phase {i} asks {f}M fresh > {FRESH_GEN_CAP/1e6:.0f}M")
    if total * 1_000_000 > GEN_CAP:
        bad.append(f"phase caps sum {total}M > generation cap {GEN_CAP/1e6:.0f}M")
    text = "\n".join(phase_lines) + "\n" + command
    for pat, label in FORBIDDEN:
        if re.search(pat, text, re.I if label not in ("R2", "H2") else 0):
            bad.append(f"forbidden act: {label}")
    if re.search(PROFILE_TRIGGER, text, re.I):
        for name, pat in PROFILE_CONDITIONS.items():
            if not re.search(pat, text, re.I if name not in ("original DOL bytes", "A2 negatives") else 0):
                bad.append(f"new profile without S26C condition: {name}")
    return bad


# ---------------------------------------------------------------- budget ledger
def _now() -> float:
    return float(os.environ.get("AP_NOW") or time.time())


def _day(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def ledger_rows() -> list[dict]:
    p = HOME / "ledger.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def ledger_add(**row) -> None:
    row.setdefault("ts", _now())
    with open(HOME / "ledger.jsonl", "a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def spend_totals(rows: list[dict], now: float) -> tuple[int, int]:
    total = sum(int(r.get("tokens") or 0) for r in rows)
    today = sum(int(r.get("tokens") or 0) for r in rows if _day(float(r["ts"])) == _day(now))
    return total, today


def budget_admits(rows: list[dict], now: float, ask: int = GEN_CAP) -> str | None:
    """None = admitted, else the reason. Reserves the full generation cap before arming."""
    if dt.datetime.fromtimestamp(now, dt.timezone.utc) >= WALL:
        return "wall 2026-11-30T23:59Z reached"
    total, today = spend_totals(rows, now)
    if total + ask > TOTAL_CAP:
        return f"total {total:,} + {ask:,} > {TOTAL_CAP:,}"
    if today + ask > DAY_CAP:
        return f"today {today:,} + {ask:,} > {DAY_CAP:,} (waits for the next UTC day)"
    return None


# ---------------------------------------------------------------- state
def load_state() -> dict:
    p = HOME / "state.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save_state(st: dict) -> None:
    tmp = HOME / "state.json.tmp"
    tmp.write_text(json.dumps(st, indent=1, sort_keys=True))
    tmp.replace(HOME / "state.json")


def log(msg: str) -> None:
    line = f"{dt.datetime.now(dt.timezone.utc).strftime('%FT%TZ')} {msg}"
    with open(HOME / "autopilot.log", "a") as f:
        f.write(line + "\n")
    print(line)


def owner_queue(lane: str, text: str) -> None:
    with open(HOME / "owner_queue.md", "a") as f:
        f.write(f"- [{dt.datetime.now(dt.timezone.utc).strftime('%FT%TZ')}] {lane}: {text}\n")


def digest(lane: str, text: str) -> None:
    with open(HOME / "digest.md", "a") as f:
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


# ---------------------------------------------------------------- headless judge / planner
def run_claude(prompt: str, cwd: str, tools: list[str], add_dirs: list[str], max_turns: int, timeout: int) -> dict:
    cmd = [CLAUDE, "-p", prompt, "--output-format", "json", "--max-turns", str(max_turns), "--allowedTools", *tools]
    for d in add_dirs:
        cmd += ["--add-dir", d]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    try:
        out = json.loads(r.stdout)
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": f"rc={r.returncode} unparsable output: {(r.stdout + r.stderr)[-400:]}", "tokens": None}
    u = out.get("usage") or {}
    tokens = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                              "cache_read_input_tokens", "output_tokens"))
    return {"ok": not out.get("is_error"), "result": out.get("result") or "", "tokens": tokens,
            "session": out.get("session_id")}


def last_json(text: str) -> dict | None:
    """The last top-level {...} object in a model's reply."""
    end = text.rfind("}")
    while end != -1:
        depth = 0
        for i in range(end, -1, -1):
            if text[i] == "}":
                depth += 1
            elif text[i] == "{":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[i:end + 1])
                    except Exception:  # noqa: BLE001
                        break
        end = text.rfind("}", 0, end)
    return None


def judge(lane: dict, checkpoint: str, product: str) -> dict:
    prompt = (HOME / "judge_prompt.md").read_text().replace("{CHECKPOINT}", checkpoint).replace("{PRODUCT}", product)
    r = run_claude(prompt, cwd=product, tools=["Read", "Grep", "Glob", "Bash(python3:*)", "Bash(timeout:*)",
                                                "Bash(sha256sum:*)", "Bash(wc:*)", "Bash(git log:*)", "Bash(git status:*)",
                                                "Bash(git show:*)", "Bash(ls:*)"],
                   add_dirs=[lane["cwd"]], max_turns=60, timeout=3600)
    v = last_json(r.get("result", "")) or {}
    v["_tokens"] = r.get("tokens")
    v["_session"] = r.get("session")
    if not r.get("ok") or v.get("verdict") not in ("AGREE", "DISAGREE", "INCONCLUSIVE"):
        v["verdict"] = "INCONCLUSIVE"
        v.setdefault("notes", r.get("error") or "judge reply had no verdict JSON")
    return v


def plan(lane: dict, name: str, checkpoint: str, product: str, verdict: dict) -> dict:
    prompt = ((HOME / "planner_prompt.md").read_text().replace("{NAME}", name).replace("{LANE}", lane["name"])
              .replace("{CHECKPOINT}", checkpoint).replace("{PRODUCT}", product)
              .replace("{VERDICT}", json.dumps({k: v for k, v in verdict.items() if not k.startswith("_")})[:3000])
              .replace("{DIGEST}", str(HOME / "digest.md")))
    r = run_claude(prompt, cwd=product, tools=["Read", "Grep", "Glob", "Bash(git log:*)", "Bash(ls:*)"],
                   add_dirs=[lane["cwd"], "/home/kobii/missions/gen3-pp"], max_turns=50, timeout=3600)
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

"""


def write_packet(lane: dict, name: str, p: dict) -> Path:
    phases = [l.strip() for l in p["phases"]]
    caps = sum(float(CAP_RE.findall(l)[0]) for l in phases)
    body = HEADER.format(name=name, title=p.get("title", "next generation")[:120], lane=lane["name"],
                         cap=f"{caps:g}", facts="\n".join(f"- {f}" for f in p.get("facts", [])[:12]))
    path = Path(lane["cwd"]) / lane["packet_dir"] / f"{name}-PHASES.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + "\n".join(phases) + "\n")
    return path


def command_text(lane: dict, name: str, packet: Path, p: dict) -> str:
    rel = packet.relative_to(lane["cwd"])
    return (f"Execute {name} of the Ascension programme (Autopilot lane {lane['name']}; open-ended reconstruction, method "
            f"evolution, independent certification). This cwd ({lane['cwd']}) is the CONTROL repo; the PRODUCT is "
            f"{lane['product']}. FIRST read {rel} in full (authority, NOT-authorised list, facts, phases with caps); it binds. "
            f"Then run /gsd-autonomous on the {name} milestone in .planning. {p.get('command_notes', '')[:600]} "
            "Freeze in a commit before anything judged on it; gates with planted mutants; micro-commit owned files only and "
            "never stage pre-existing dirty residue; keep a budget.md with measured spend per phase (gsd_mission.py topology "
            "--mission <this mission>); stop a phase at its cap; no push, no paid API. At the end: gsd_mission.py checkpoint "
            f"CHECKPOINT_COMPLETE with an evidence checkpoint file for {name} that states new canonical certificates (per "
            "profile, by function identity) and validated capabilities.")


# ---------------------------------------------------------------- the per-lane transition
def lane_tick(st: dict, lane: dict, dry: bool) -> None:
    ls = st.setdefault("lanes", {}).setdefault(lane["name"], {"status": "WAITING", "blank": 0, "arm_fails": 0, "gen": None})
    if ls["status"] in ("PARKED", "STOPPED"):
        return
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
            ls["status"] = "PARKED"
            owner_queue(lane["name"], f"mission {mid} ended {rec['state']} without a checkpoint hold; lane parked")
            log(f"{lane['name']}: PARKED, {mid} {rec['state']}")
            return
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
    now = _now()
    why = budget_admits(ledger_rows(), now, GEN_CAP + 4_000_000)
    if why:
        ls["judged_for"] = None
        save_state(st)
        log(f"{lane['name']}: budget wait: {why}")
        return
    log(f"{lane['name']}: checkpoint {checkpoint} -> judge")
    v = {"verdict": "AGREE", "new_canonical_certs": 0, "validated_capability": False, "_tokens": 0} if dry \
        else judge(lane, checkpoint, product)
    ledger_add(lane=lane["name"], kind="judge", tokens=v.get("_tokens") or 0, verdict=v.get("verdict"), checkpoint=checkpoint)
    digest(lane["name"], f"JUDGE {v.get('verdict')} on {checkpoint}: new certs {v.get('new_canonical_certs')}, "
                         f"capability {v.get('validated_capability')}. {str(v.get('notes', ''))[:600]}")
    if v.get("verdict") != "AGREE":
        ls["status"] = "PARKED"
        owner_queue(lane["name"], f"judge {v.get('verdict')} on {checkpoint}: {str(v.get('notes', ''))[:300]}")
        save_state(st)
        return
    blank = not (int(v.get("new_canonical_certs") or 0) > 0 or v.get("validated_capability") is True)
    ls["blank"] = ls.get("blank", 0) + 1 if blank else 0
    if ls["blank"] >= BLANK_STOP:
        ls["status"] = "STOPPED"
        owner_queue(lane["name"], f"{BLANK_STOP} consecutive generations without a new certificate or capability; lane stopped")
        digest(lane["name"], "STOPPED: blank-generation rule")
        save_state(st)
        return
    st["next_gen"] = int(st.get("next_gen") or 28)
    name = f"S{st['next_gen']}{lane['letter']}"
    p = {"title": "dry", "facts": ["dry"], "phases": ["Phase 1: x (cap 1M)", "Phase 2: y (cap 1M)"], "_tokens": 0} if dry \
        else plan(lane, name, checkpoint, product, v)
    ledger_add(lane=lane["name"], kind="plan", tokens=p.get("_tokens") or 0, gen=name)
    if p.get("stop"):
        ls["status"] = "STOPPED"
        owner_queue(lane["name"], f"planner found no admissible next lever: {str(p.get('stop'))[:300]}")
        digest(lane["name"], f"STOPPED by planner: {str(p.get('stop'))[:400]}")
        save_state(st)
        return
    phases = [l.strip() for l in (p.get("phases") or []) if l.strip()]
    tmp_cmd = p.get("command_notes", "")
    bad = policy_check(phases, tmp_cmd)
    if bad:
        ls["status"] = "PARKED"
        owner_queue(lane["name"], f"policy refused {name}: {'; '.join(bad)[:400]}")
        digest(lane["name"], f"POLICY REFUSED {name}: {'; '.join(bad)[:400]}")
        save_state(st)
        return
    caps = int(sum(float(CAP_RE.findall(l)[0]) for l in phases) * 1_000_000)
    why = budget_admits(ledger_rows(), _now(), caps)
    if why:
        ls["judged_for"] = None
        save_state(st)
        log(f"{lane['name']}: budget wait before arming {name}: {why}")
        return
    if arm_generation(st, lane, ls, name, p, phases, caps, dry):
        st["next_gen"] += 1
        ls.update(status="RUNNING", gen=name, arm_fails=0)
    else:
        ls["arm_fails"] = ls.get("arm_fails", 0) + 1
        ls["judged_for"] = None
        if ls["arm_fails"] >= MAX_ARM_FAILS:
            ls["status"] = "PARKED"
            owner_queue(lane["name"], f"arming {name} failed {MAX_ARM_FAILS} times; see autopilot.log")
    save_state(st)


def arm_generation(st, lane, ls, name, p, phases, caps, dry) -> bool:
    cwd = lane["cwd"]
    old = ls.get("mission") or lane.get("mission")
    if old and (mission(old) or {}).get("state") not in TERMINAL:
        rec = mission(old)
        spent = mission_spend(old) if not dry else 0
        ledger_add(lane=lane["name"], kind="generation_closed", mission=old, tokens=0, spend=spent)
        rc, out = gm("close", "--mission", old, "--outcome", "COMPLETED", "--owner-turn", OWNER_TURN, "--reason",
                     f"Autopilot: checkpoint judged AGREE; next generation {name}", dry=dry)
        if rc != 0:
            log(f"{lane['name']}: close {old} failed: {out[-300:]}")
            return False
    rc, dirty = sh(["git", "-C", cwd, "status", "--porcelain", "--", ".planning/PROJECT.md", ".planning/ROADMAP.md",
                    ".planning/STATE.md"])
    if dirty.strip() and not dry:
        log(f"{lane['name']}: .planning dirty in {cwd}; not arming")
        return False
    if lane.get("ff_from") and not ls.get("ff_done"):
        rc, out = sh(["git", "-C", cwd, "merge", "--ff-only", lane["ff_from"]], dry=dry)
        if rc != 0:
            log(f"{lane['name']}: ff to {lane['ff_from']} failed: {out[-300:]}")
            return False
        ls["ff_done"] = True
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M")
    arch = f".planning/milestones/{(ls.get('gen') or 'pre-autopilot').lower()}-archived-{stamp}"
    present = [f for f in (".planning/PROJECT.md", ".planning/ROADMAP.md", ".planning/STATE.md") if (Path(cwd) / f).exists()]
    if present:
        sh(["mkdir", "-p", f"{cwd}/{arch}"], dry=dry)
        rc, out = sh(["git", "-C", cwd, "mv", *present, arch], dry=dry)
        if rc != 0:
            log(f"{lane['name']}: archive failed: {out[-300:]}")
            return False
    packet = write_packet(lane, name, p) if not dry else Path(cwd) / lane["packet_dir"] / f"{name}-PHASES.md"
    cmd = command_text(lane, name, packet, p)
    sh(["git", "-C", cwd, "add", "-A", "--", arch, str(packet)], dry=dry)
    sh(["git", "-C", cwd, "commit", "-q", "-m", f"{name}: autopilot packet + archive previous milestone"], dry=dry)
    hours = min(16.0, max(1.0, (WALL - dt.datetime.now(dt.timezone.utc)).total_seconds() / 3600))
    args = ["arm", "--cwd", cwd, "--command", cmd, "--milestone-from", str(packet), "--max-cycles", "12",
            "--max-hours", f"{hours:.1f}", "--permission-mode", "auto", "--no-launch"]
    for d in lane.get("add_dirs", []):
        args += ["--add-dir", d]
    rc, out = gm(*args, dry=dry)
    new = None if dry else (re.search(r'"mission_id":\s*"(m-[0-9a-f]+)"', out) or [None, None])[1]
    if not dry and (rc != 0 or not new):
        log(f"{lane['name']}: arm failed rc={rc}: {out[-400:]}")
        return False
    rc, out = gm("authority", "--mission", new or "m-dry", "--tokens", str(caps), "--owner-turn", OWNER_TURN,
                 "--reason", f"Autopilot {name}: phase caps {caps:,} <= 25M per generation (Owner typed authorization)", dry=dry)
    if rc != 0:
        log(f"{lane['name']}: authority failed: {out[-300:]}; holding the new record")
        gm("hold", "--mission", new, "--reason", "autopilot: authority refused, never launch unbounded")
        return False
    sh(["git", "-C", cwd, "add", ".planning/PROJECT.md", ".planning/ROADMAP.md", ".planning/STATE.md"], dry=dry)
    sh(["git", "-C", cwd, "commit", "-q", "-m", f"{name}: scaffold milestone (mission {new}, authority {caps:,})"], dry=dry)
    ls["mission"] = new
    ledger_add(lane=lane["name"], kind="generation_armed", mission=new, gen=name, tokens=caps, authority=caps)
    digest(lane["name"], f"ARMED {name} as {new}, authority {caps:,}. Phases:\n" + "\n".join(f"  {l[:200]}" for l in phases))
    log(f"{lane['name']}: armed {name} as {new} ({caps:,})")
    return True


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "status":
        print(json.dumps(load_state(), indent=1))
        total, today = spend_totals(ledger_rows(), _now())
        print(f"ledger total {total:,} / {TOTAL_CAP:,}; today {today:,} / {DAY_CAP:,}")
        return 0
    if (HOME / "OFF").exists():
        return 0
    if not OWNER_TURN.split(":", 1)[1]:
        log("refused: AP_OWNER_TS unset")
        return 2
    dry = cmd == "dry-tick"
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
