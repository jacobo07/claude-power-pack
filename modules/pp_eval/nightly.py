"""One automatic night (spec §3.5–3.8): preflight, pick work, run, judge, propose, report.

Everything a night decides is written down: a skipped night is a `nights.jsonl` row with its
reason, never silence, so "it did not run" and "it ran and found nothing" stay different.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from . import harvest, runner, verdict
from .common import PP, Lock, state_dir, utc_now

DEFAULTS = {
    "budget_runs": 16, "util_7d_max": 0.80, "util_5h_max": 0.50, "min_free_ram_gb": 6.0,
    "idle_minutes": 15, "repos": [str(PP)], "harvest_per_night": 5, "bank_target": 30,
    "baseline_weekday": 6,   # Sunday
}


# ---- state -----------------------------------------------------------------------------

def config() -> dict:
    p = state_dir() / "config.json"
    user = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return {**DEFAULTS, **user}


def _read_jsonl(name: str) -> list[dict]:
    p = state_dir() / name
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))   # a corrupt ledger must fail loudly, not shrink
    return rows


def _append(name: str, row: dict) -> None:
    with open(state_dir() / name, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _load(name: str, default):
    p = state_dir() / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def _save(name: str, obj) -> None:
    tmp = state_dir() / (name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    tmp.replace(state_dir() / name)


# ---- fingerprints (spec §3.5) ----------------------------------------------------------

def _home() -> Path:
    return Path(os.environ.get("PP_EVAL_HOME") or Path.home())


def layer_files(layer: str) -> list[Path]:
    c = _home() / ".claude"
    if layer == "context":
        files = list((c / "rules").rglob("*.md")) + [c / "CLAUDE.md", _home() / "CLAUDE.md"]
    elif layer == "hooks":
        files = [p for p in (c / "hooks").rglob("*") if p.suffix in (".js", ".py", ".ps1", ".json")]
        files.append(c / "settings.json")
    elif layer == "skills":
        files = list((c / "skills").glob("*/SKILL.md"))
    else:
        raise ValueError(layer)
    return sorted(p for p in files if p.is_file())


def fingerprint(layer: str) -> str:
    h = hashlib.sha256()
    base = _home()
    for p in layer_files(layer):
        h.update(str(p.relative_to(base)).replace("\\", "/").encode())
        h.update(b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()[:16]


# ---- preflight -------------------------------------------------------------------------

def quota_block(cfg: dict, now: float) -> str | None:
    """Reason to stay idle, from the last observed reading. No probe call is spent."""
    q = _load("quota.json", {})
    limits = {"seven_day": cfg["util_7d_max"], "five_hour": cfg["util_5h_max"]}
    for name, win in (q.get("windows") or {}).items():
        lim = limits.get(name)
        resets = win.get("resetsAt") or 0
        if lim is not None and win.get("utilization", 0) >= lim and now < resets:
            return f"quota {name} at {win['utilization']:.0%} >= {lim:.0%} until {dt.datetime.fromtimestamp(resets):%Y-%m-%d %H:%M}"
    return None


def owner_active(cfg: dict, now: float) -> str | None:
    projects = Path(os.environ.get("PP_EVAL_PROJECTS") or _home() / ".claude" / "projects")
    horizon = now - cfg["idle_minutes"] * 60
    for p in projects.glob("*/*.jsonl"):
        try:
            if p.stat().st_mtime > horizon:
                return f"a session transcript changed in the last {cfg['idle_minutes']} min ({p.name})"
        except OSError:
            continue
    return None


def free_ram_gb() -> float | None:
    if sys.platform == "win32":
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return m.ullAvailPhys / 2**30
        return None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 2**20
    except OSError:
        return None
    return None


def ram_block(cfg: dict) -> str | None:
    if os.environ.get("PP_EVAL_FREE_RAM_GB"):
        free = float(os.environ["PP_EVAL_FREE_RAM_GB"])
    else:
        free = free_ram_gb()
    if free is None:
        return "free RAM unmeasurable"      # unknown keeps the night idle, never assumed fine
    if free < cfg["min_free_ram_gb"]:
        return f"free RAM {free:.1f} GB < {cfg['min_free_ram_gb']} GB"
    return None


# ---- planning --------------------------------------------------------------------------

def plan(cfg: dict, rows: list[dict], tasks: dict, evaluated: dict, fps: dict, weekday: int) -> dict:
    budget = cfg["budget_runs"]
    if not tasks:
        return {"kind": "none", "reason": "bank is empty", "runs": []}
    valid_count = {t: 0 for t in tasks}
    for r in rows:
        if r.get("status") == "VALID" and r["task"] in valid_count:
            valid_count[r["task"]] += 1
    if weekday == cfg["baseline_weekday"]:
        order = sorted(tasks, key=lambda t: valid_count[t])
        return {"kind": "baseline", "layer": "baseline", "fingerprint": _stack_fp(fps),
                "runs": [(t, "baseline", "A", 1) for t in order[:budget]]}
    disc = verdict.discriminating(rows)
    for layer in runner.LAYERS:
        if evaluated.get(layer) == fps[layer]:
            continue
        done = {(r["task"], r["arm"], r["rep"]) for r in rows
                if r.get("layer") == layer and r.get("fingerprint") == fps[layer] and r.get("status") == "VALID"}
        order = sorted(tasks, key=lambda t: (t not in disc, valid_count[t]))
        runs = []
        for t in order:
            for rep in (1, 2):
                arms = ("A", "B") if rep == 1 else ("B", "A")   # alternate so host drift lands on both
                for arm in arms:
                    if (t, arm, rep) not in done and len(runs) < budget:
                        runs.append((t, layer, arm, rep))
        return {"kind": "layer", "layer": layer, "fingerprint": fps[layer], "runs": runs}
    return {"kind": "none", "reason": "every layer is evaluated at its current fingerprint", "runs": []}


def _stack_fp(fps: dict) -> str:
    return hashlib.sha256("|".join(fps[l] for l in runner.LAYERS).encode()).hexdigest()[:16]


# ---- the night -------------------------------------------------------------------------

def run_night(dry_run: bool = False, now: float | None = None, weekday: int | None = None,
              log=print) -> dict:
    now = time.time() if now is None else now
    weekday = dt.datetime.fromtimestamp(now).weekday() if weekday is None else weekday
    cfg = config()
    night = {"started": utc_now(), "dry_run": dry_run}
    lock = Lock(state_dir() / "night.lock")
    if not lock.acquire():
        night["outcome"] = "SKIPPED: another night holds the lock"
        _append("nights.jsonl", night)
        return night
    try:
        for check in (lambda: owner_active(cfg, now), lambda: ram_block(cfg)):
            reason = check()
            if reason:
                night["outcome"] = f"SKIPPED: {reason}"
                _append("nights.jsonl", night)
                return night
        # Harvesting makes no model calls, so it runs even when quota keeps the model idle:
        # otherwise the bank would stay empty until the weekly reset for no reason.
        bank = harvest.load_bank()
        if len(bank["tasks"]) < cfg["bank_target"] and not dry_run:
            night["harvest"] = harvest.harvest([Path(r) for r in cfg["repos"]], max_new=cfg["harvest_per_night"], log=log)
            bank = harvest.load_bank()
        reason = quota_block(cfg, now)
        if reason:
            night["outcome"] = f"SKIPPED: {reason}"
            _append("nights.jsonl", night)
            return night
        rows = _read_jsonl("runs.jsonl")
        evaluated = _load("evaluated.json", {})
        fps = {l: fingerprint(l) for l in runner.LAYERS}
        p = plan(cfg, rows, bank["tasks"], evaluated, fps, weekday)
        night.update(kind=p["kind"], layer=p.get("layer"), planned=len(p["runs"]))
        if dry_run or not p["runs"]:
            if p["kind"] == "layer" and not p["runs"]:
                _finalise(p["layer"], p["fingerprint"], rows, evaluated, exhausted=True)
            night["outcome"] = "DRY_RUN" if dry_run else f"NOTHING: {p.get('reason', 'no runs left for ' + str(p.get('layer')))}"
            night["plan"] = [list(r) for r in p["runs"]]
            _append("nights.jsonl", night)
            return night
        done = 0
        for task_id, layer, arm, rep in p["runs"]:
            if layer != "baseline" and fingerprint(layer) != p["fingerprint"]:
                night["stopped"] = f"{layer} changed during the night"
                break
            rec = runner.one_run(bank["tasks"][task_id], "hooks" if layer == "baseline" else layer,
                                 "A" if layer == "baseline" else arm, rep, str(harvest.bank_path()))
            rec.update(layer=layer, fingerprint=p["fingerprint"])
            _append("runs.jsonl", rec)
            done += 1
            wins = (rec.get("evidence") or {}).get("windows")
            if wins:
                _save("quota.json", {"at": utc_now(), "windows": wins})
            if rec["status"] == "DEFERRED_QUOTA":
                night["stopped"] = "usage limit reached"
                break
            if quota_block(cfg, time.time()):
                night["stopped"] = quota_block(cfg, time.time())
                break
        night["runs"] = done
        if p["kind"] == "layer":
            night["verdict"] = _finalise(p["layer"], p["fingerprint"], _read_jsonl("runs.jsonl"), evaluated)
        night["outcome"] = "RAN"
        _append("nights.jsonl", night)
        return night
    finally:
        lock.release()
        write_report()


def _finalise(layer: str, fp: str, rows: list[dict], evaluated: dict, exhausted: bool = False) -> dict:
    v = verdict.judge(rows, layer, fp)
    if v["verdict"] in ("LOSS", "HARM", "NO_LOSS") or exhausted:
        evaluated[layer] = fp
        _save("evaluated.json", evaluated)
        verdicts = _load("verdicts.json", {})
        verdicts[layer] = {**v, "at": utc_now(), "final": True, "exhausted": exhausted}
        _save("verdicts.json", verdicts)
        if v["verdict"] in ("NO_LOSS", "HARM"):
            _propose(v)
    return v


def _propose(v: dict) -> None:
    from modules.owner_queue import owner_queue
    s = v["secondary"]
    saving = ""
    if s["A"]["mean_context"] and s["B"]["mean_context"]:
        saving = f"; B used {1 - s['B']['mean_context'] / s['A']['mean_context']:.0%} less context"
    if v["verdict"] == "NO_LOSS":
        action = (f"PP Self-Eval: removing the {v['layer']} layer showed no loss on "
                  f"{v['tasks_paired']} tasks{saving}. Review moving parts of it on demand.")
    else:
        action = (f"PP Self-Eval: the {v['layer']} layer HURT results on {v['tasks']} "
                  f"(fails with it, passes without, 2/2). Review it.")
    owner_queue.append(action, "python tools/pp_eval.py report", component="pp_eval",
                       source="pp_eval.nightly", row_id=f"pp-eval-{v['layer']}-{v['fingerprint']}",
                       state_dir=os.environ.get("PP_EVAL_OWNER_QUEUE_DIR") or None)


# ---- report ----------------------------------------------------------------------------

def write_report() -> Path:
    rows, nights = _read_jsonl("runs.jsonl"), _read_jsonl("nights.jsonl")
    verdicts, bank, quota = _load("verdicts.json", {}), harvest.load_bank(), _load("quota.json", {})
    status = {}
    for r in rows:
        status[r["status"]] = status.get(r["status"], 0) + 1
    lines = ["# PP Self-Eval report", "", f"Regenerated {utc_now()} from the ledger alone "
             "(spec `vault/specs/pp-self-eval.md`).", "",
             f"Bank: {len(bank['tasks'])} validated tasks, {len(bank['rejected'])} rejected candidates. "
             f"Runs: {len(rows)} {status}. Discriminating tasks: {len(verdict.discriminating(rows))}.", ""]
    if quota.get("windows"):
        w = ", ".join(f"{k} {v.get('utilization', 0):.0%}" for k, v in quota["windows"].items())
        lines += [f"Last quota reading ({quota.get('at', 'time unknown')}): {w}.", ""]
    lines += ["## Verdicts", "", "| layer | verdict | tasks paired | detail | A mean ctx | B mean ctx |",
              "|---|---|---|---|---|---|"]
    for layer in runner.LAYERS:
        v = verdicts.get(layer)
        if not v:
            lines.append(f"| {layer} | not yet | | | | |")
            continue
        s = v["secondary"]
        detail = v.get("reason") or ", ".join(v.get("tasks", [])) or ""
        lines.append(f"| {layer} | {v['verdict']}{' (task set exhausted)' if v.get('exhausted') else ''} | "
                     f"{v['tasks_paired']} | {detail} | {s['A']['mean_context']} | {s['B']['mean_context']} |")
    lines += ["", "## Last nights", ""]
    for n in nights[-10:]:
        lines.append(f"- {n['started']} {n.get('outcome')} {n.get('kind') or ''} {n.get('layer') or ''} "
                     f"runs={n.get('runs', 0)} {n.get('stopped') or ''}".rstrip())
    p = state_dir() / "REPORT.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p
