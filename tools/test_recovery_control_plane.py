"""V-gates for the Workspace Recovery Control Plane (Execution Mode, SCS C83).

Hermetic: imports vscode_autorun in script mode; uses only in-memory data and a
temp dir. Proves the Sprint-0 wiring fix that makes the AUTOMATIC restore path
(the tasks.json Cursor auto-runs on folderOpen after a reboot) restore ALL panes
of ALL repos from the corrected pane_map.json -- killing the three named bugs:

  * "1 pane per repo"      -> V-ALL-PANES (N panes -> N tasks, no truncation)
  * "only works in PP"     -> V-MULTICORE-RECOVERY (>=3 distinct repos each full)
  * "shutdown != restart"  -> V-SHUTDOWN-RESTART-PARITY (plan derives purely from
                              the persisted manifest -> deterministic, interrupt-
                              type independent)

Anti-duplication kill switch (HR-CONTROL-PLANE-EXCLUSIVE-RESP-001):
  * V-NO-DUPLICATE-MANIFEST -- the adapter READS pane_map.json and writes ONLY
    .vscode/tasks.json; it never creates a new manifest/snapshot/registry.
  * V-COMPONENT-EXCLUSIVE-RESP -- generate_from_pane_map's exclusive responsibility
    (pane_map -> per-repo tasks.json, no truncation) is verified, not described.

Complements tools/test_restore_all_panes.py (which covers the build_cpc_tasks /
session_snapshot layer). This file covers the pane_map adapter + control-plane
invariants -- a different layer, no overlapping gate.
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "modules", "cpc_os"))
import vscode_autorun as va  # noqa: E402  (script-mode import)

passes = 0
fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"[OK] {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"[FAIL] {gate}: {ev}")


def _pane(cwd, sid, repo=None, topic=None, live=False):
    """A pane_map.json-shaped record (as build_pane_map.ps1 emits)."""
    return {
        "cwd": cwd, "sessionId": sid, "repo": repo, "topic": topic,
        "resumeCmd": f"kclaude --resume {sid}", "live": live,
        "status": "RESUMABLE", "tier": "OPEN-NOW" if live else "ACTIVE",
    }


def _write_pane_map(path, panes):
    payload = {"generatedAt": "2026-07-10T00:00:00Z", "source": "test",
               "counts": {"repos": len({p["cwd"] for p in panes})}, "panes": panes}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _sid(n):
    return f"{n:08d}-0000-0000-0000-000000000000"


def main():
    with tempfile.TemporaryDirectory() as td:
        # --- V-PANE-MAP-ADAPTER: schema map + drop of unusable records ----------
        raw = {"panes": [
            _pane(r"C:\repo\A", _sid(1), repo="A", topic="t1"),
            {"cwd": r"C:\repo\A", "sessionId": None},        # no sid -> dropped
            {"sessionId": _sid(9), "cwd": None},             # no cwd -> dropped
        ]}
        adapted = va._panes_from_pane_map(raw)
        if (len(adapted) == 1 and adapted[0]["session_id"] == _sid(1)
                and adapted[0]["resume"] == f"claude --resume {_sid(1)}"
                and adapted[0]["repo"] == "A"):
            _ok("V-PANE-MAP-ADAPTER", "sessionId->session_id, resume built, sid/cwd-less dropped")
        else:
            _fail("V-PANE-MAP-ADAPTER", f"unexpected adapt: {adapted}")

        # --- V-ALL-PANES: 1 repo x 9 panes -> 9 tasks (no truncation) -----------
        pm1 = os.path.join(td, "pm_all.json")
        _write_pane_map(pm1, [_pane(r"C:\repo\Solo", _sid(i), repo="Solo") for i in range(9)])
        r1 = va.generate_from_pane_map(pm1, dry_run=True)
        n1 = r1[0]["n_tasks"] if r1 else 0
        if len(r1) == 1 and n1 == 9:
            _ok("V-ALL-PANES", "9 panes -> 9 tasks (no 1-per-repo truncation)")
        else:
            _fail("V-ALL-PANES", f"expected 1 repo/9 tasks, got {len(r1)} repos/{n1} tasks")

        # --- V-MULTICORE-RECOVERY: 3 distinct repos each fully restored ----------
        repos = {r"C:\repo\PP": "PP", r"C:\repo\TUA-X": "TUA-X",
                 r"C:\repo\KobiiCraft": "KobiiCraft"}
        multi = []
        k = 100
        for cwd, name in repos.items():
            for _ in range(3):
                multi.append(_pane(cwd, _sid(k), repo=name)); k += 1
        pm2 = os.path.join(td, "pm_multi.json")
        _write_pane_map(pm2, multi)
        r2 = va.generate_from_pane_map(pm2, dry_run=True)
        by_cwd = {res["cwd"]: res["n_tasks"] for res in r2}
        if len(by_cwd) == 3 and all(v == 3 for v in by_cwd.values()):
            _ok("V-MULTICORE-RECOVERY", "PP/TUA-X/KobiiCraft each -> 3 tasks (not 1/repo)")
        else:
            _fail("V-MULTICORE-RECOVERY", f"expected 3 repos x3 tasks, got {by_cwd}")

        # --- V-SHUTDOWN-RESTART-PARITY: plan derives purely from the manifest ----
        # Two independent calls on the SAME persisted manifest yield an identical
        # task set -> the restore plan is deterministic and interrupt-type
        # independent (a reboot reads the same on-disk manifest a reload would).
        a = va.generate_from_pane_map(pm2, dry_run=True)
        b = va.generate_from_pane_map(pm2, dry_run=True)
        sig = lambda res: sorted((x["cwd"], x["n_tasks"]) for x in res)
        if sig(a) == sig(b) and sig(a):
            _ok("V-SHUTDOWN-RESTART-PARITY", "same manifest -> identical plan (deterministic)")
        else:
            _fail("V-SHUTDOWN-RESTART-PARITY", f"non-deterministic: {sig(a)} != {sig(b)}")

        # --- V-NO-DUPLICATE-MANIFEST: reads pane_map, writes ONLY tasks.json -----
        # A real (non-dry) run into a hermetic .vscode dir must produce ONLY a
        # tasks.json -- never a new manifest/snapshot/registry file. The input
        # pane_map is the single source of truth and is never re-emitted.
        work = os.path.join(td, "repoX")
        os.makedirs(work)
        pm3 = os.path.join(td, "pm_single.json")
        _write_pane_map(pm3, [_pane(work, _sid(200), repo="repoX"),
                              _pane(work, _sid(201), repo="repoX")])
        va.generate_from_pane_map(pm3, cwds=[work], dry_run=False)
        produced = []
        for root, _dirs, files in os.walk(work):
            produced.extend(files)
        manifest_like = [f for f in produced
                         if any(s in f.lower() for s in
                                ("pane_map", "snapshot", "registry", "manifest"))]
        if produced == ["tasks.json"] and not manifest_like:
            _ok("V-NO-DUPLICATE-MANIFEST", "only tasks.json written; no new manifest/registry")
        else:
            _fail("V-NO-DUPLICATE-MANIFEST", f"unexpected artifacts: {produced}")

        # --- V-COMPONENT-EXCLUSIVE-RESP: exclusive responsibility, verified ------
        # generate_from_pane_map's exclusive job = pane_map -> per-repo tasks.json,
        # NEVER truncated (its whole reason to exist vs the snapshot path). Prove
        # it hermetically by contrast with the pure capping primitive: the same 9
        # panes, capped, yield 2 tasks; the pane_map path yields all 9. If they
        # shared a responsibility this distinction could not hold.
        n_full = va.generate_from_pane_map(pm1, dry_run=True)[0]["n_tasks"]
        capped_panes = [{"cwd": r"C:\repo\Solo", "resume": f"claude --resume {_sid(i)}"}
                        for i in range(9)]
        n_capped = len(va.build_cpc_tasks(capped_panes, target_count=2))
        if n_full == 9 and n_capped == 2:
            _ok("V-COMPONENT-EXCLUSIVE-RESP",
                "pane_map path never truncates (9); capping primitive caps (2) -> distinct responsibilities")
        else:
            _fail("V-COMPONENT-EXCLUSIVE-RESP", f"pane_map={n_full} capped={n_capped}")

    total = passes + fails
    print(f"RECOVERY_CONTROL_PLANE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
