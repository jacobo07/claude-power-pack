#!/usr/bin/env python3
"""The bounded cycle: `sweep` made resident, restartable and recoverable.

    recover (census, at start) -> admit governed, autonomous, unpaused goals ->
    engine reconcile -> at most one engine decision per goal -> record intent ->
    dispatch through the engine's provider -> persist the mission ->
    observe / harvest on later cycles -> receipts go to the ENGINE ->
    gain verdict -> heartbeat

What the resident never does: judge, write goal state except through engine
APIs (`epoch.begin/mark_running/recover/end/ingest_receipt`, and the sweep's
own verdict application, which defers to `convergence.satisfy`), or dispatch
anything the engine's reconciler did not decide.

WHAT IT DISPATCHES. The deterministic gate provider exactly as `sweep` does,
reading the goal root. A work epoch (codex, claude-headless,
claude-interactive) goes through the ISOLATED stage (`isolate.py`): a fresh
worktree on branch `resident/<mission-id>` at the goal root's clean HEAD, the
provider's cwd is that worktree only, and at harvest every changed path --
committed or not -- is checked against the declared write set before anything
is ingested. The resident never merges, pushes or rewrites the goal's branch:
the worktree branch is the deliverable. After an ingested harvest it re-runs
the goal's gates IN the worktree (GateProvider, bounded; evidence on the
mission, never a satisfaction) and, only if all are green, fast-forwards the
one ref `factory/integration` to the job commit by compare-and-swap.

AUTHORITY. Under an UNVERIFIABLE anchor `contract.project()` checks no
signature at all, so the resident refuses to admit ANY goal and reports
WAITING_FOR_AUTHORITY with the anchor's own description -- that mode is never
read as ABSENT. Under ENFORCED/UNPROTECTED an ungoverned goal is refused by the
sweep's `governance_refusal`. Under ABSENT legacy admission is unchanged.
"""
from __future__ import annotations

import os
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path

from .. import authority as au
from .. import contract as gc
from .. import convergence as cv
from .. import epoch as ep
from .. import git_state as gs
from .. import judge as jd
from .. import log as gl
from .. import reconcile as rc
from .. import brief as br
from .. import sweep as sw
from ..providers.gate import GateProvider
from . import control, health, isolate as iso, ledgers, missions as ms, procs, store

WORK_PROVIDERS = ("codex", "claude-headless", "claude-interactive")
DISPATCHABLE = ("gate",) + WORK_PROVIDERS
ACTIVE_KINDS = frozenset({rc.WAIT, rc.HARVEST, rc.NEXT_EPOCH, rc.RECOVER})
# Kinds that need a person: a refused isolation, a write-set violation, a
# delivered branch nobody has merged yet.
PERSON_KINDS = frozenset({"ISOLATION_REFUSED", "AWAITING_MERGE", "DELIVERED_NOT_INTEGRATED",
                          "WRITE_SET_VIOLATION"})


class SimulatedCrash(Exception):
    """Raised only by a fault hook, to prove the crash windows are recoverable."""


@dataclass
class Config:
    max_cycles_per_wake: int = 288
    sleep_busy_s: float = 30.0          # something in flight
    sleep_idle_s: float = 300.0         # nothing in flight
    mission_wall_s: float = 3600.0
    gain_window_s: float = 6 * 3600.0
    stall_k: int = 6
    lease_ttl_s: float = 900.0
    provider_caps: dict = field(default_factory=lambda: {"gate": 2})
    cancel_grace_s: float = 0.5
    # Integration: each goal gate re-run in a job's worktree is bounded by this,
    # and cancelled (process tree) at the bound. The cycle blocks while they run.
    integration_gate_wall_s: float = 900.0
    integration_poll_s: float = 0.2


@dataclass
class CycleReport:
    cycle: int
    acted: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    stopped: bool = False
    cancels: list = field(default_factory=list)
    health: str = ""
    health_reason: str = ""


def load_registry(path: Path) -> list:
    """goals.json: {"goals": [{"root": <repo>, "goal": <id>}, ...]}. Absent = none."""
    try:
        doc = store.read_json(path)
    except FileNotFoundError:
        return []
    entries = doc.get("goals") if isinstance(doc, dict) else None
    if not isinstance(entries, list):
        raise store.StateUnreadable(f"{path}: expected {{\"goals\": [...]}}")
    return [(str(e["root"]), str(e["goal"])) for e in entries]


def is_paused(state: gc.GoalState) -> bool:
    paused = False
    for ev in state.events:
        if ev.type == gc.PAUSED:
            paused = True
        elif ev.type == gc.RESUMED:
            paused = False
    return paused


class Resident:
    def __init__(self, pp_root: Path, providers: dict, goals=None, state_dir: Path | None = None,
                 config: Config | None = None, info: procs.ProcInfo | None = None,
                 runner=control.run_command, fault=None, clock=time.time,
                 actor: str = "resident", integration_gates=None, sleep=time.sleep):
        self.pp_root = Path(pp_root)
        self.providers = dict(providers)
        self._goals = goals
        self.sd = store.StateDir(state_dir)
        self.sd.ensure()
        self.cfg = config or Config()
        self.info = info or procs.ProcInfo()
        self.runner = runner
        self._fault_hook = fault
        self.clock = clock
        self.actor = actor
        self.missions = ms.MissionStore(self.sd.missions)
        self.intents = ledgers.IntentLedger(self.sd.intents)
        self.gain = ledgers.GainLedger(self.sd.gain)
        self.escalations = ledgers.EscalationLedger(self.sd.escalations)
        self.leases = ledgers.Leases(self.sd.leases, clock=clock)
        self.lock = procs.InstanceLock(self.sd.lock, self.info)
        self.holder = f"resident:{socket.gethostname()}:{os.getpid()}"
        self.engine = gs.head(Path(sw.__file__).resolve().parents[3])
        self.cycle_no = 0
        self.generation = 0
        self.last_census: list = []
        self.last_evidence_ts: float | None = None
        self.current: dict = {}
        # The gate machinery, reused: a DEDICATED GateProvider instance, so an
        # integration run never shares handles or run files with a gate epoch.
        self.integration_gates = integration_gates or GateProvider(
            self.sd.runs / "integration", wall_bound_s=self.cfg.integration_gate_wall_s)
        self._sleep = sleep

    # --- lifecycle -------------------------------------------------------------
    def _fault(self, point: str, **ctx) -> None:
        if self._fault_hook is not None:
            self._fault_hook(point, **ctx)

    def stop_requested(self) -> bool:
        return self.sd.stop.exists()

    def start(self, beat: bool = True) -> dict:
        """Take the lock, bump the generation, run the recovery census.

        `beat=False` for the standalone `census` (ExecStopPost): it must not leave
        a heartbeat claiming a loop that is not running."""
        got = self.lock.acquire()               # raises procs.LockRefused
        try:
            prev = store.read_json(self.sd.heartbeat)
            self.generation = int(prev.get("generation", 0)) + 1
        except FileNotFoundError:
            self.generation = 1
        except store.StateUnreadable:
            self.generation = 1
        self.last_census = control.census(self.missions, self.providers, self.intents,
                                          self.info)
        self.cleanup_worktrees()
        for row in self.last_census:
            store.append_jsonl(self.sd.census, {**row, "generation": self.generation,
                                                "ts": self.clock()})
        if not beat:
            return {"lock": got, "census": self.last_census, "generation": self.generation}
        self._heartbeat(health.RECOVERING if any(r["classification"] == control.UNCERTAIN
                                                 for r in self.last_census)
                        else health.RUNNING, "started; census complete", [])
        return {"lock": got, "census": self.last_census, "generation": self.generation}

    def close(self) -> None:
        for res in self.leases.held_by(self.holder):
            self.leases.release(res, self.holder)
        self.lock.release()

    def run(self, max_cycles: int | None = None, sleep=time.sleep) -> str:
        """The loop systemd calls. Bounded: at most `max_cycles_per_wake` cycles,
        then exit so the unit restarts it fresh (Restart=always)."""
        limit = max_cycles if max_cycles is not None else self.cfg.max_cycles_per_wake
        for _ in range(limit):
            rep = self.once()
            if rep.stopped:
                return "STOPPED"
            busy = any(m["state"] in ms.HAS_HANDLE for m in self.missions.non_terminal())
            wait = self.cfg.sleep_busy_s if busy else self.cfg.sleep_idle_s
            deadline = self.clock() + wait
            while self.clock() < deadline:
                if self.stop_requested():
                    rep = self.once()          # honours STOP: cancels owned missions
                    return "STOPPED"
                sleep(min(1.0, max(0.0, deadline - self.clock())))
        return "WAKE_BOUND_REACHED"

    # --- one cycle -------------------------------------------------------------
    def once(self) -> CycleReport:
        self.cycle_no += 1
        rep = CycleReport(self.cycle_no)
        facts = health.HealthFacts()
        try:
            self._cycle(rep, facts)
            rep.notes.extend(self.cleanup_worktrees())
        except Exception as exc:
            facts.failed = f"{exc.__class__.__name__}: {exc}"
            h, why = health.compute(facts, self.clock(), self.cfg.gain_window_s)
            rep.health, rep.health_reason = h, why
            self._heartbeat(h, why, [facts.failed])
            raise
        facts.last_gain_ts = self.gain.last_gain_ts()
        facts.running_missions = sum(1 for m in self.missions.non_terminal()
                                     if m["state"] in ms.HAS_HANDLE)
        facts.recovering = sorted(set(facts.recovering) | {
            m["id"] for m in self.missions.all() if m.get("state") == ms.UNCERTAIN})
        h, why = health.compute(facts, self.clock(), self.cfg.gain_window_s)
        rep.health, rep.health_reason = h, why
        blockers = ([facts.authority_refusal] if facts.authority_refusal else []) \
            + [f"stalled {g}" for g in facts.stalled] + [f"uncertain {m}" for m in facts.recovering]
        self._heartbeat(h, why, blockers)
        return rep

    def _load_goals(self, rep: CycleReport, facts: health.HealthFacts) -> list:
        if self._goals is not None:
            return list(self._goals() if callable(self._goals) else self._goals)
        try:
            entries = load_registry(self.sd.goals)
        except store.StateUnreadable as exc:
            facts.degraded.append(f"registry: {exc}")
            rep.skipped.append(f"REGISTRY_UNREADABLE: {exc}")
            return []
        out = []
        for root, goal in entries:
            try:
                out.append((gl.GoalLog(gl.repo_id(Path(root)), goal), Path(root)))
            except gl.GoalLogError as exc:
                facts.degraded.append(f"{goal}@{root}")
                rep.skipped.append(f"{goal}: REPO_UNREADABLE: {exc}")
        return out

    def _cycle(self, rep: CycleReport, facts: health.HealthFacts) -> None:
        if self.stop_requested():
            self._honour_stop(rep)
            return
        anchor = au.load_anchor()
        if anchor.mode == au.UNVERIFIABLE:
            facts.authority_refusal = f"AUTHORITY_UNVERIFIABLE: {au.describe(anchor)}"
            rep.skipped.append(f"ALL GOALS: {facts.authority_refusal}")
            return
        allowed, why = sw.autonomy_verdict(self.pp_root)
        if not allowed:
            facts.authority_refusal = f"LICENCE_REFUSED: {why}"
            rep.skipped.append(f"ALL GOALS: {facts.authority_refusal}")
            return
        uncertain_goals = {m.get("goal") for m in self.missions.all()
                           if m.get("state") == ms.UNCERTAIN}
        for log, root in self._load_goals(rep, facts):
            if self.stop_requested():
                self._honour_stop(rep)
                return
            key = f"{log.repo[:12]}/{log.goal_id}"
            try:
                state = gc.project(log)
            except gl.GoalLogError as exc:
                facts.degraded.append(key)
                rep.skipped.append(f"{key}: GOAL_UNREADABLE: {exc}")
                continue
            refusal = sw.governance_refusal(state)
            if refusal:
                rep.skipped.append(f"{key}: UNGOVERNED: {refusal}")
                continue
            if is_paused(state):
                rep.skipped.append(f"{key}: PAUSED by a {gc.PAUSED} event")
                continue
            if not sw.is_autonomous(state):
                rep.skipped.append(f"{key}: NOT_AUTONOMOUS")
                continue
            if key in uncertain_goals:
                facts.recovering.append(key)
                rep.skipped.append(f"{key}: UNRESOLVED_UNCERTAIN_MISSION: reconcile it before "
                                   "anything else is dispatched for this goal")
                continue
            try:
                self.leases.acquire(f"goal:{log.repo}:{log.goal_id}", self.holder,
                                    self.cfg.lease_ttl_s)
            except ledgers.LeaseRefused as exc:
                rep.skipped.append(f"{key}: {exc.reason}: {exc.detail}")
                continue
            kind, tree = self._drive(log, root, state, key, rep, facts)
            after = gc.project(log)
            snap = ledgers.goal_snapshot(after, jd.current(after, tree, after.revision))
            g = self.gain.record(key, self.cycle_no, snap, kind in ACTIVE_KINDS,
                                 now=self.clock())
            if g["gain"]:
                rep.acted.append(f"{key}: GAIN -- {g['reason']}")
            k = max(1, int(self.cfg.stall_k))
            if g["no_gain_streak"] >= k:
                facts.stalled.append(key)
                if g["no_gain_streak"] % k == 0:
                    e = self.escalations.record(
                        key, f"{g['no_gain_streak']} active cycles without information gain")
                    rep.acted.append(f"{key}: STALLED -> escalation {e['step']}")
            if kind != rc.CONVERGED:
                facts.admitted += 1
            if kind in ACTIVE_KINDS:
                facts.active += 1
            if kind == rc.READY_FOR_JUDGE:
                facts.waiting_evidence.append(key)
            elif kind in (rc.ESCALATE, rc.BLOCKED) or kind in PERSON_KINDS:
                facts.waiting_authority.append(key)
            elif kind == "UNDISPATCHED":
                facts.waiting_provider.append(key)
            self._fault("after_goal", goal=log.goal_id)

    # --- driving one goal through the engine ---------------------------------------
    def _drive(self, log: gl.GoalLog, root: Path, state: gc.GoalState, key: str,
               rep: CycleReport, facts: health.HealthFacts) -> tuple[str, str]:
        paths = state.scope.get("paths") or ["."]
        tree = gs.tree_id(root, paths)
        eps = ep.project_epochs(state)
        now = self.clock()
        observations = {}
        for e in eps.values():
            if e.state != "running" or not e.handle:
                continue
            prov = self.providers.get(e.provider)
            if prov is None:
                rep.notes.append(f"{key}: {e.epoch_id} runs on {e.provider}, not held here")
                continue
            try:
                obs = prov.observe(e.handle)
            except Exception as exc:        # unreadable observation: engine WAITs on it
                rep.notes.append(f"{key}: observe {e.epoch_id} raised "
                                 f"{exc.__class__.__name__}: {exc}")
                continue
            m = self.missions.get(e.epoch_id)
            if (obs.state == ep.OBS_RUNNING and m is not None
                    and now - float(m.get("dispatched_ts") or now) > self.cfg.mission_wall_s):
                res = self._cancel_mission(m, rep)
                if res["clean"]:
                    ep.end(log, gc.project(log), e.epoch_id, ep.EXPIRED,
                           f"over the resident's {self.cfg.mission_wall_s:.0f}s wall", self.actor)
                    self.missions.advance(e.epoch_id, ms.EXPIRED)
                    rep.acted.append(f"{key}: {e.epoch_id} EXPIRED at the mission wall")
                    return rc.WAIT, tree       # work was in motion this cycle
                continue
            observations[e.epoch_id] = obs
        d = rc.decide(rc.Context(state=state, tree_hash=tree,
                                 scope_hash=ep.scope_hash(root, paths),
                                 observations=observations, now=now, budget=state.budget,
                                 providers=tuple(self.providers),
                                 judge=jd.current(state, tree, state.revision),
                                 engine=self.engine))
        self.current = {"goal": f"{log.goal_id}@{state.revision}", "decision": d.kind,
                        "mission": d.epoch_id, "provider": d.provider}
        if d.kind == rc.RECOVER:
            self._recover(log, state, eps[d.epoch_id], key, rep)
        elif d.kind == rc.HARVEST:
            k = self._harvest(log, state, root, paths, eps[d.epoch_id],
                              observations.get(d.epoch_id), key, rep)
            return (k or d.kind), tree
        elif d.kind == rc.NEXT_EPOCH:
            return self._dispatch(log, state, root, paths, tree, d, key, rep), tree
        elif d.kind != rc.WAIT:
            rep.notes.append(f"{key}: {d.kind} -- {d.reason[:160]}")
        return d.kind, tree

    def _recover(self, log, state, e, key, rep) -> None:
        prov = self.providers.get(e.provider)
        if prov is None:
            rep.notes.append(f"{key}: {e.epoch_id} needs {e.provider} to be recovered")
            return
        out = ep.recover(log, state, prov, e.epoch_id, self.actor)
        rep.acted.append(f"{key}: engine recovered {e.epoch_id} -> {out}")
        m = self.missions.get(e.epoch_id)
        if m is None or m["state"] in ms.TERMINAL:
            return
        if out == "adopted":
            handle = ep.project_epochs(gc.project(log))[e.epoch_id].handle
            if m["state"] in (ms.ADMITTED, ms.ISOLATED):
                m = self.missions.advance(e.epoch_id, ms.DISPATCHED, handle=handle,
                                          pid=(handle or {}).get("pid"),
                                          dispatched_ts=self.clock())
            self.missions.advance(e.epoch_id, ms.RUNNING, handle=handle)
        else:
            self.missions.advance(e.epoch_id, ms.LOST, lost_reason="engine recovery: no run")

    def _harvest(self, log, state, root, paths, e, obs, key, rep) -> str:
        prov = self.providers.get(e.provider)
        if prov is None:
            rep.notes.append(f"{key}: {e.epoch_id} ended but {e.provider} is not held here")
            return ""
        m0 = self.missions.get(e.epoch_id)
        isolated = bool(m0 and m0.get("isolated"))
        if e.provider in WORK_PROVIDERS and not isolated:
            # A work epoch this resident did not isolate (another driver, or a
            # record from before this stage): its writes cannot be judged against a
            # base, so nothing of it is ingested here.
            rep.notes.append(f"{key}: {e.epoch_id} is a {e.provider} epoch with no isolation "
                             "record here; not harvested by the resident")
            return ""
        if isolated:
            verdict = iso.check_harvest(m0)
            if not verdict["ok"]:
                return self._refuse_harvest(log, e, m0, verdict, key, rep)
            root = Path(m0["worktree"])      # providers harvest in the worktree, never the root
        spec = {"epoch_id": e.epoch_id, "revision": state.revision, "root": str(root),
                "scope_paths": paths, **{k: v for k, v in e.spec.items() if k != "gate"}}
        if e.provider == "gate":
            spec["gate"] = e.spec.get("gate") or {"id": e.spec.get("obligation", "gate"),
                                                  "command": [], "class": "unit", "files": []}
        rid = ""
        try:
            receipt = prov.harvest(e.handle or {}, spec)
            rid = ep.ingest_receipt(log, gc.project(log), receipt, self.actor)
            rep.acted.extend(sw._apply_verdicts(log, receipt, e, self.actor))
            self.last_evidence_ts = self.clock()
        except (ep.EpochError, KeyError) as exc:
            rep.notes.append(f"{key}: {e.epoch_id} harvest refused: {exc}")
        outcome = (obs.outcome if obs else ep.LOST) or ep.LOST
        ep.end(log, gc.project(log), e.epoch_id, outcome,
               obs.detail if obs else "unobservable", self.actor)
        rep.acted.append(f"{key}: harvested {e.epoch_id} ({outcome})")
        m = self.missions.get(e.epoch_id)
        if m is None or m["state"] in ms.TERMINAL:
            return ""
        if m["state"] in (ms.DISPATCHED, ms.RUNNING):
            m = self.missions.advance(e.epoch_id, ms.RETURNED, outcome=outcome)
        if m["state"] == ms.RETURNED:
            m = self.missions.advance(e.epoch_id, ms.HARVESTED, receipt_id=rid)
        extra = {}
        if isolated and rid:
            extra["deliverable_head"] = gs.head(Path(m0["worktree"]))
            extra["deliverable_branch"] = m0.get("branch")
        self.missions.advance(e.epoch_id, ms.RECONCILED, **extra)
        if isolated and rid:
            self._integrate(log, e.epoch_id, key, rep)
        return ""

    # --- integration (Owner decision "option 1") -----------------------------------
    def _integration_gates(self, state: gc.GoalState) -> list:
        """The goal's live gates, built exactly as a gate epoch builds them."""
        out = []
        for o in cv.project_convergence(state).obligations.values():
            if o.disposition in cv.RETIRED_DISPOSITIONS or not (o.done_gate or "").strip():
                continue
            out.append({"id": o.identifier, "command": jd._argv(o.done_gate),
                        "class": o.gate_class or "unit", "files": [rel for rel, _ in o.gate_pin]})
        return out

    def _run_gate_in(self, wt: Path, gate: dict, mid: str, n: int, revision: str,
                     write_set: list) -> dict:
        """One gate, cwd = the job's worktree, through the GateProvider: its own
        supervised process (own session on POSIX), result file, tree-kill cancel.
        Bounded; a run that did not report an exit status is not green."""
        prov = self.integration_gates
        token = f"integ-{mid}-{n}-{os.urandom(4).hex()}"
        spec = {"epoch_id": f"integration:{mid}:{gate['id']}", "revision": revision,
                "root": str(wt), "identity": {"run_token": token},
                "scope_paths": list(write_set), "gate": gate}
        row = {"gate": gate["id"], "command": gate["command"], "class": gate["class"],
               "cwd": str(wt), "exit_status": None, "green": False, "detail": ""}
        try:
            handle = prov.dispatch(spec)
        except Exception as exc:
            row["detail"] = f"dispatch raised {exc.__class__.__name__}: {exc}"[:300]
            return row
        bound = float(getattr(prov, "wall_bound_s", self.cfg.integration_gate_wall_s))
        deadline = time.monotonic() + bound
        obs = None
        while True:
            try:
                obs = prov.observe(handle)
            except Exception as exc:
                obs = None
                row["detail"] = f"observe raised {exc.__class__.__name__}: {exc}"[:300]
            if obs is not None and obs.state != ep.OBS_RUNNING:
                break
            if time.monotonic() >= deadline:
                try:
                    prov.cancel(handle)
                except Exception as exc:
                    row["detail"] = f"cancel raised {exc.__class__.__name__}: {exc}"[:300]
                row["timed_out"] = True
                break
            self._sleep(self.cfg.integration_poll_s)
        try:
            receipt = prov.harvest(handle, spec)
        except Exception as exc:
            row["detail"] = (row["detail"] + f"; harvest raised {exc.__class__.__name__}: "
                             f"{exc}")[:300]
            return row
        v = receipt.verdicts[0] if receipt.verdicts else None
        if v is not None:
            row.update(exit_status=v.get("exit_status"), observed=v.get("observed", ""),
                       tree_hash=v.get("tree_hash", ""), gate_pin=v.get("gate_pin", []))
        row["failures"] = [f.get("summary", "") for f in receipt.failures]
        row["green"] = (v is not None and v.get("exit_status") == 0 and not receipt.failures
                        and not row.get("timed_out"))
        return row

    def _integrate(self, log: gl.GoalLog, mid: str, key: str, rep: CycleReport) -> None:
        m = self.missions.get(mid)
        wt, root = Path(m["worktree"]), Path(m["root"])
        base, job = m.get("base_commit", ""), m.get("deliverable_head", "")
        rec = {"state": iso.INTEGRATION_REFUSED, "reason": "", "detail": "", "gates": [],
               "ref": iso.INTEGRATION_REF, "ref_before": "", "ref_after": "",
               "job_commit": job, "base": base}

        def done(reason: str = "", detail: str = "", **more) -> None:
            rec.update(more)
            rec.update(reason=reason, detail=detail[:400])
            self.missions.advance(mid, integration=rec)
            what = rec["state"] if not rec["reason"] else f"{rec['state']} {rec['reason']}"
            rep.acted.append(f"{key}: {mid} integration: {what} {rec['detail'][:160]}")

        if not job or job == base:
            return done(iso.NOTHING_TO_INTEGRATE, "the worktree HEAD is the base: no commit "
                        "was delivered", state=iso.NOTHING_TO_INTEGRATE)
        try:
            dirty = iso.uncommitted_paths(wt)
        except OSError as exc:
            return done(iso.UNREADABLE, f"worktree status unreadable: {exc}")
        if dirty:
            return done(iso.INTEGRATION_WORKTREE_DIRTY,
                        f"uncommitted bytes the commit does not carry: {dirty[:10]}")
        gates = self._integration_gates(gc.project(log))
        if not gates:
            return done(iso.NO_GATES, "the goal has no live gate; nothing was proved")
        rows = [self._run_gate_in(wt, g, mid, i, m.get("revision", ""), m.get("write_set") or [])
                for i, g in enumerate(gates)]
        rec["gates"] = rows
        red = [r["gate"] for r in rows if not r["green"]]
        if red:
            return done(iso.GATES_RED, f"not green in the worktree: {red}")
        now_head = gs.head(wt)
        if now_head != job:
            return done(iso.INTEGRATION_HEAD_MOVED,
                        f"worktree HEAD {now_head[:12]} after the gates is not the judged "
                        f"commit {job[:12]}")
        res = iso.integrate(root, job, base)
        rec.update(state=res["state"], ref_before=res["ref_before"], ref_after=res["ref_after"],
                   created=res["created"])
        if not res["ok"]:
            return done(res["reason"], res["detail"])
        return done(detail=res["detail"])

    def _refuse_harvest(self, log, e, m, verdict, key, rep) -> str:
        """WRITE_SET_VIOLATION: nothing is ingested, the epoch ends FAILED (so the
        reconciler never blind-retries exactly this), the mission is REFUSED with
        the evidence, and nothing is merged or reverted."""
        ev = verdict["evidence"]
        detail = f"{iso.WRITE_SET_VIOLATION}: " + "; ".join(ev["reasons"])
        try:
            ep.end(log, gc.project(log), e.epoch_id, ep.FAILED, detail[:500], self.actor)
        except ep.EpochError as exc:
            rep.notes.append(f"{key}: {e.epoch_id} not ended ({exc})")
        cur = self.missions.get(e.epoch_id)
        if cur["state"] in (ms.DISPATCHED, ms.RUNNING):
            cur = self.missions.advance(e.epoch_id, ms.RETURNED, outcome=ep.FAILED)
        if cur["state"] == ms.RETURNED:
            self.missions.advance(e.epoch_id, ms.REFUSED, refusal=iso.WRITE_SET_VIOLATION,
                                  refusal_evidence=ev)
        rep.acted.append(f"{key}: {e.epoch_id} REFUSED {detail[:200]}")
        return "WRITE_SET_VIOLATION"

    def _dispatch(self, log, state, root, paths, tree, d, key, rep) -> str:
        prov = self.providers.get(d.provider)
        if d.provider not in DISPATCHABLE or prov is None:
            rep.notes.append(f"{key}: NEXT_EPOCH needs {d.provider}: PROVIDER_NOT_HELD "
                             "-- reported, nothing spent")
            return "UNDISPATCHED"
        work = d.provider in WORK_PROVIDERS
        base = ""
        write_set: list = []
        if work:
            write_set = list(state.scope.get("paths") or [])
            reason, detail = iso.validate_write_set(root, write_set)
            if not reason:
                base, reason, detail = iso.clean_base(root, write_set)
            pending_kind = ""
            if not reason:
                pending_kind, pending = self._awaiting_merge(key, root)
                if pending_kind:
                    reason, detail = iso.WORK_AWAITING_MERGE, pending
            if reason:
                rep.notes.append(f"{key}: NEXT_EPOCH {d.provider} refused before any spend: "
                                 f"{reason}: {detail}")
                return pending_kind if reason == iso.WORK_AWAITING_MERGE \
                    else "ISOLATION_REFUSED"
        cap = int(self.cfg.provider_caps.get(d.provider, 1))
        in_flight = sum(1 for m in self.missions.non_terminal()
                        if m.get("provider") == d.provider)
        if in_flight >= cap:
            rep.notes.append(f"{key}: PROVIDER_CAP {d.provider} {in_flight}/{cap}")
            return "UNDISPATCHED"
        if work:
            return self._dispatch_work(log, state, root, write_set, base, tree, d, prov, key, rep)
        o = cv.project_convergence(state).obligations[d.spec["obligation"]]
        if o.plane in cv.REALITY_PLANES and o.gate_class not in cv.RUNTIME_GATE_CLASSES:
            rep.notes.append(f"{key}: {o.identifier} declares no runtime gate class; a "
                             f"{o.plane} obligation is not dispatched on an inferred one")
            return "UNDISPATCHED"
        gate = {"id": o.identifier, "command": jd._argv(o.done_gate),
                "class": o.gate_class or "unit", "files": [rel for rel, _ in o.gate_pin]}
        e = ep.begin(log, state, d.provider,
                     {"obligation": o.identifier, "tree_hash": tree, "gate": gate},
                     d.info_key, d.hypothesis, self.actor)
        spec = {"epoch_id": e.epoch_id, "revision": state.revision, "root": str(root),
                "identity": e.identity, "scope_paths": paths, "gate": gate}
        attempt = e.identity["run_token"]
        self.current["mission"] = e.epoch_id
        self.missions.create(e.epoch_id, ms.ADMITTED, goal=key, goal_id=log.goal_id,
                             repo=log.repo, revision=state.revision, provider=d.provider,
                             attempt_id=attempt, identity=e.identity, worktree=str(root),
                             base_commit=gs.head(root), write_set=list(paths),
                             obligation=o.identifier, handle=None, pid=None, pgid=None,
                             start_time=None, scope_unit=None, claude_bg_id=None,
                             generation=self.generation)
        return self._launch(log, e, prov, spec, d, key, rep, o.identifier)

    def _launch(self, log, e, prov, spec, d, key, rep, what: str) -> str:
        """intent -> dispatch -> DISPATCHED -> engine running -> RUNNING."""
        attempt = e.identity["run_token"]
        # F9: the intent is durable BEFORE the provider is asked to do anything.
        self.intents.record(attempt, e.epoch_id, log.goal_id, log.repo, d.provider, spec)
        self._fault("after_intent", mission=e.epoch_id)
        try:
            handle = prov.dispatch(spec)
        except Exception as exc:
            # The provider's own record decides what happened -- never a guess.
            rep.notes.append(f"{key}: dispatch of {e.epoch_id} raised "
                             f"{exc.__class__.__name__}: {exc}")
            self._recover(log, gc.project(log), ep.project_epochs(gc.project(log))[e.epoch_id],
                          key, rep)
            return rc.RECOVER
        self._fault("after_dispatch", mission=e.epoch_id)
        pid = handle.get("pid")
        pgid = handle.get("pgid")
        if pgid is None and pid is not None and d.provider == "gate" and os.name == "posix":
            pgid = pid                      # the gate provider starts its own session
        self.missions.advance(e.epoch_id, ms.DISPATCHED, handle=handle, pid=pid, pgid=pgid,
                              start_time=self.info.start_time(pid) if pid else None,
                              dispatched_ts=self.clock(),
                              scope_unit=handle.get("scope_unit"),
                              claude_bg_id=handle.get("claude_bg_id"))
        ep.mark_running(log, gc.project(log), e.epoch_id, handle, self.actor)
        self.missions.advance(e.epoch_id, ms.RUNNING)
        rep.acted.append(f"{key}: dispatched {e.epoch_id} for {what}")
        return rc.NEXT_EPOCH

    # --- the ISOLATED stage ----------------------------------------------------------
    def _awaiting_merge(self, key: str, root: Path) -> tuple[str, str]:
        """(kind, detail) for a delivered work branch of this goal that the goal
        root does not yet contain; ('', '') when none. The reconciler cannot see an
        unmerged branch, so without this it would pay for the same work again
        against the same tree. The kind says which person is needed for what:
        AWAITING_MERGE -- factory/integration carries it, the Owner merges that;
        DELIVERED_NOT_INTEGRATED -- red gates or a refused integration."""
        for m in self.missions.all():
            head = m.get("deliverable_head", "")
            if not (m.get("goal") == key and m.get("isolated") and m.get("state") == ms.RECONCILED
                    and iso.awaiting_merge(root, head, m.get("base_commit", ""))):
                continue
            integ = m.get("integration") or {}
            where = f"branch {m.get('branch')} ({str(head)[:12]}) from {m['id']}"
            if (integ.get("state") in (iso.INTEGRATED, iso.ALREADY_INTEGRATED)
                    and iso.integration_carries(root, head)):
                return "AWAITING_MERGE", (
                    f"INTEGRATED: {where} is on {iso.INTEGRATION_BRANCH}; the Owner merges "
                    f"{iso.INTEGRATION_BRANCH} into the goal branch")
            why = integ.get("reason") or ("integration moved away since"
                                          if integ.get("state") in (iso.INTEGRATED,
                                                                    iso.ALREADY_INTEGRATED)
                                          else "never attempted")
            return "DELIVERED_NOT_INTEGRATED", (
                f"NOT_INTEGRATED({why}): {where} is not merged into the goal root and not on "
                f"{iso.INTEGRATION_BRANCH}; a person merges, repairs or discards it")
        return "", ""

    def _dispatch_work(self, log, state, root, write_set, base, tree, d, prov, key, rep) -> str:
        obligation = d.spec.get("obligation", "")
        task = d.spec.get("task") or obligation
        e = ep.begin(log, state, d.provider,
                     {"obligation": obligation, "tree_hash": tree, "task": task,
                      "base_commit": base, "write_set": list(write_set)},
                     d.info_key, d.hypothesis, self.actor)
        mid = e.epoch_id
        self.current["mission"] = mid
        branch = iso.branch_for(mid)
        wt = self.sd.worktrees / mid
        self.missions.create(mid, ms.ADMITTED, goal=key, goal_id=log.goal_id, repo=log.repo,
                             revision=state.revision, provider=d.provider,
                             attempt_id=e.identity["run_token"], identity=e.identity,
                             root=str(root), worktree=str(wt), branch=branch, base_commit=base,
                             write_set=list(write_set), obligation=obligation, isolated=True,
                             handle=None, pid=None, pgid=None, start_time=None, scope_unit=None,
                             claude_bg_id=None, generation=self.generation)
        try:
            iso.create(root, wt, branch, base)
        except iso.IsolationRefused as exc:
            # A path that existed before us, or one inside the repo, is NOT ours:
            # cleanup must never touch it.
            self.missions.advance(mid, ms.REFUSED, refusal=exc.reason,
                                  refusal_evidence={"detail": exc.detail, "worktree": str(wt)},
                                  worktree_foreign=exc.reason in (iso.WORKTREE_PATH_EXISTS,
                                                                  iso.WORKTREE_INSIDE_REPO))
            ep.end(log, gc.project(log), mid, ep.CANCELLED,
                   f"{exc.reason}: nothing ran ({exc.detail})"[:500], self.actor)
            rep.notes.append(f"{key}: {mid} REFUSED before dispatch: {exc}")
            return "ISOLATION_REFUSED"
        self.missions.advance(mid, ms.ISOLATED, root_head_at_isolation=gs.head(root),
                              root_ref_at_isolation=iso.root_ref(root))
        self._fault("after_isolated", mission=mid)
        closure = cv.goal_closure(state, tree, ep.open_epochs(state))
        text = br.compile_brief(state, closure.blocking, str(wt), task)
        spec = {"epoch_id": mid, "revision": state.revision, "root": str(wt),
                "identity": e.identity, "scope_paths": list(write_set), "task": task,
                "prompt": text, "brief": text, "must_be_worktree": True}
        return self._launch(log, e, prov, spec, d, key, rep, f"{obligation} in {branch}")

    def cleanup_worktrees(self) -> list:
        """Remove the worktree of a finished mission when it holds nothing
        uncommitted. The branch is kept. UNCERTAIN missions are left for a person."""
        notes = []
        for m in self.missions.all():
            if (not m.get("isolated") or m.get("state") not in ms.TERMINAL
                    or m.get("state") == ms.UNCERTAIN or m.get("worktree_removed")
                    or m.get("worktree_foreign") or not m.get("root") or not m.get("worktree")):
                continue
            res = iso.remove_if_clean(Path(m["root"]), Path(m["worktree"]), m.get("branch", ""))
            if res["removed"] or not res["kept"]:
                self.missions.advance(m["id"], worktree_removed=True, worktree_cleanup=res)
            elif m.get("worktree_kept") != res["detail"]:
                self.missions.advance(m["id"], worktree_kept=res["detail"])
                notes.append(f"{m['id']}: worktree KEPT -- {res['detail']}")
        return notes

    # --- stop and cancel ---------------------------------------------------------
    def _cancel_mission(self, m: dict, rep: CycleReport) -> dict:
        res = control.cancel_by_handle(m, self.providers.get(m.get("provider")), self.info,
                                       self.runner, grace_s=self.cfg.cancel_grace_s)
        rep.cancels.append({"mission": m["id"], **res})
        if res["clean"]:
            self.missions.advance(m["id"], cancel=res)
        else:
            # A failed stop is a recorded failure: the mission is UNCERTAIN (terminal)
            # and blocks its goal until someone reconciles it.
            self.missions.advance(m["id"], ms.UNCERTAIN, cancel=res,
                                  uncertain=list(m.get("uncertain") or [])
                                  + [f"cancel not clean: {res['failures']}"])
        return res

    def _honour_stop(self, rep: CycleReport) -> None:
        rep.stopped = True
        for m in self.missions.non_terminal():
            if m["state"] not in (ms.DISPATCHED, ms.RUNNING):
                rep.notes.append(f"{m['id']}: {m['state']} has no handle to cancel by; "
                                 "the next census reconciles it")
                continue
            res = self._cancel_mission(m, rep)
            if not res["clean"]:
                rep.notes.append(f"{m['id']}: cancel FAILED {res['failures']}")
                continue
            self.missions.advance(m["id"], ms.CANCELLED)
            try:
                glog = gl.GoalLog(m["repo"], m["goal_id"])
                ep.end(glog, gc.project(glog), m["id"], ep.CANCELLED, "resident STOP",
                       self.actor)
            except ep.EpochError as exc:
                rep.notes.append(f"{m['id']}: epoch not ended by STOP ({exc})")
            rep.acted.append(f"{m['id']}: CANCELLED on STOP")

    # --- heartbeat -------------------------------------------------------------------
    def _heartbeat(self, h: str, why: str, blockers: list) -> None:
        ident = procs.self_identity(self.info)
        store.atomic_write_json(self.sd.heartbeat, {
            "generation": self.generation, "pid": ident["pid"], "host": ident["host"],
            "start_time": ident["start_time"], "health": h, "health_reason": why,
            "cycle": self.cycle_no, "ts": self.clock(),
            "current": self.current, "mission": self.current.get("mission", ""),
            "provider": self.current.get("provider", ""),
            "last_progress_ts": self.gain.last_gain_ts(),
            "last_evidence_ts": self.last_evidence_ts,
            "budget": {"provider_caps": self.cfg.provider_caps,
                       "max_cycles_per_wake": self.cfg.max_cycles_per_wake,
                       "mission_wall_s": self.cfg.mission_wall_s},
            "blockers": blockers})
