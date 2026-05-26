#!/usr/bin/env python3
"""S+++ recovery: undo Pane-4 destructive stomp on
apex-completion-standard.md while preserving the legitimate Pterodactyl
Console API axis content.

Pane 4 wrote (non-atomically) over the head of the file, stomping the
"Testing Gate Axis (sealed 2026-05-23)" section and leaving orphan
fragments. The loose mirror was therefore corrupted before this cycle
synced loose -> PP. C6 of the Skill Completion Standard was sealed to
prevent exactly this pattern.

Recovery:
  1. git show origin/main:knowledge_vault/core/apex-completion-standard.md
     -> clean base (no Pterodactyl axis, no orphan fragments, full
     Testing Gate Axis head intact).
  2. Extract the Pterodactyl axis content (lines 3-31 of the polluted
     working tree) -> append as a proper named section AFTER the clean
     base, prefixed with the doctrine-required ---/heading structure.
  3. Atomic-write the merged result to BOTH loose and PP mirrors.
  4. Re-invoke `_apex_skill_axis_v2_append.py` to put the v2 axis back
     (idempotent on marker).

This is destructive of the Pane-4 stomp but non-destructive of Pane-4
content. The Pterodactyl axis survives -- just relocated to the end
of the file via atomic write, as C6 mandates.
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path("knowledge_vault/core/apex-completion-standard.md")
LOOSE = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/apex-completion-standard.md"))

GIT_EXE = r"C:\Program Files\Git\cmd\git.exe"
REPO = Path.cwd()

PTERODACTYL_SECTION = """

---

## Pterodactyl Console API Autopilot Axis (sealed 2026-05-26)

Relocated to file-tail by S+++ recovery (2026-05-26) per C6 atomic-write
mandate. Original Pane-4 insertion stomped the Testing Gate Axis head;
this section preserves the content, restored via atomic-append rather
than destructive overwrite.

When a Pterodactyl-managed Minecraft server has prose-flagged "Owner-in-game" PASOs in its handoff docs, the Apex bar is to verify each PASO against this 11-item empirical checklist BEFORE accepting the OWNER-MANUAL classification. A PASO is autopilot-doable on Console API iff every check below either passes or has an autopilot-side substitute.

### 11 empirical checklist items (>=10 needed to claim "Apex-complete on Console API Axis")

1. **nbtlib `<world>/level.dat` parse**: `Data.spawn.pos` (Paper 1.21+ IntArray of 3 ints) -> produces `(SpawnX, SpawnY, SpawnZ)` literal output. nbtlib must be installed; if not, `pip install nbtlib`.
2. **Console-API verb map**: WorldGuard `/rg`, Citizens `/npc`, FAWE `//world`+`//pos1`+`//pos2`+`//set/replace`, vanilla `/setworldspawn`, `/say`, `/save-all` all dispatch via `POST /api/client/servers/{id}/command` and produce log-side evidence.
3. **WorldGuard `-w PREFIX` discipline**: `/rg flag -w <world> <region_id> <flag> <value>`. Never trust HTTP 204 -- grep log for `Region flag <name> set on '<id>' to '<value>'`.
4. **Citizens comma-coord syntax**: `--at <x>,<y>,<z>,<world>` (or `--location` same form). Never space-separated. Done-evidence: `Created <name> (ID <n>).` in log; save IDs for downstream `/npc select`.
5. **DecentHolograms player-actor wall**: hologram create/attach is impossible from console. Autopilot creates NPC + ID; generate paste-ready Owner doc for the `/dh` block using the captured IDs.
6. **ND-7 cross-pane leak recovery**: before any `git add`, run `git diff --cached --name-only` to catch other panes' pre-staged files. If unexpected files in index: `git reset HEAD -- .` + re-add ONLY your explicit paths. Never `git add -A` (multi-pane race vaccine).
7. **`git reset HEAD -- .` discipline**: when an inadvertent stage from another pane appears, reset the index (not the working tree). Then re-stage with explicit paths. Preserves the other pane's working-tree work; cleans your commit's staged set.
8. **`files/write` octet-stream fallback**: the documented `files/upload` signed-URL flow (`:8080/upload/file?token=<jwt>`) returns HTTP 500 / RemoteProtocolError on this panel install. The working path is `POST /api/client/servers/{id}/files/write?file=<path>` with `Content-Type: application/octet-stream` and raw bytes as body. Empirically supports >=1.8 MB single POST.
9. **`/save-all flush` before restart**: dispatch `/save-all flush` and wait for `Saved the game` in log before issuing `POST /power {"signal": "restart"}`. Prevents chunk corruption + ensures level.dat reflects in-memory state.
10. **ND-1 `[HOTFIX-JAVA-APPROVED]` scope discipline**: this override token is sealed for explicit Owner-ratified Java edits. Pure-docs commits + Python-script commits MUST NOT include the token. Adding it for non-Java commits invites scope creep + auditor noise.
11. **Vanilla `/fill` vs. FAWE `//set` decision**: `/fill` requires loaded chunks; FAWE `//set` auto-loads via EditSession but requires `//world <world>` prefix from console. Default to FAWE for any block-manipulation in worlds without active players.

### Five-check DONE-gate (all must pass for Apex-complete)

- [ ] nbtlib `level.dat` parse executed; coords persisted to `_audit_cache/<world>_coords.json` with paper_version + sha256[:16].
- [ ] All non-player-only PASOs attempted via Console API with empirical log-grep evidence persisted to `docs/server/playtest-v200/paso<N>_*.log`.
- [ ] Owner-handoff docs generated for genuine player-actor-only PASOs (DH, fresh-player verification) with paste-ready commands using autopilot-captured IDs.
- [ ] Commit staged with explicit paths (never `-A`); ND-7 self-scan passed; ND-1 / quality-skill gate respected.
- [ ] Sec 13 of `GOLD_STANDARD_SERVERS.md` (Console API autopilot recipes) updated with any new verb/syntax/quirk discovered this run.

### Empirical receipt (Pane-4 v200 run, 2026-05-26)

Pane 4 v200 pasos-restantes run closed 5/5 OWNER-MANUAL PASOs (3, 4, 5, 6, 7) into autopilot-DONE + 1 sidecar discovery (KobiWelcome Y=70->Y=182 drift fix -- the `can't stay connected` root cause). 8/14 milestones autopilot, 6/14 docs/doctrine. Wall-clock ~25 min including syntax debugging. All 11 checklist items + all 5 DONE-gates passed.

"""


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def origin_main_content() -> str:
    proc = subprocess.run(
        [GIT_EXE, "-C", str(REPO), "show",
         "origin/main:knowledge_vault/core/apex-completion-standard.md"],
        capture_output=True, text=True, encoding="utf-8", timeout=20,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"git show failed: {proc.stderr}\n")
        sys.exit(2)
    return proc.stdout


def main() -> int:
    clean = origin_main_content()
    if not clean.endswith("\n"):
        clean += "\n"
    merged = clean + PTERODACTYL_SECTION

    for target in (LOOSE, PP):
        _atomic_write(target, merged)
        print(f"recovered {target} (bytes={target.stat().st_size})")

    # Re-append v2 axis (idempotent on marker).
    import subprocess as sp
    rc = sp.call([sys.executable, "tools/_apex_skill_axis_v2_append.py"])
    if rc != 0:
        sys.stderr.write("_apex_skill_axis_v2_append.py returned non-zero\n")
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
