#!/usr/bin/env python3
"""TIS cycle recovery: undo Pane-3 destructive prepend on
apex-completion-standard.md while preserving the legitimate
"World-Env Suffix Detection Axis" content.

Pane 3 wrote (non-atomically) at the head of the file, prepending its
axis and clipping the original opening header. Loose mirror was
synced byte-perfectly to PP, importing the stomp. Same governance as
the Pane-4 recovery from the prior cycle: relocate legitimate content
to tail via atomic-append; restore the original head from
origin/main.
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

PANE3_SECTION = """

---

## World-Env Suffix Detection Axis (Pane 3, KobiiCraft -- relocated 2026-05-26 by S+++ recovery)

Relocated to file-tail by TIS-cycle recovery (2026-05-26) per C6 atomic-
write mandate. Original Pane-3 insertion stomped the Testing Gate Axis
head; this section preserves the content, restored via atomic-append
rather than destructive overwrite.

**Sealed:** 2026-05-26 evening (Pane 3 KME-env + KME-042 follow-up).

### The axis (one-line invariant)

> Any code path that creates a Bukkit World via `WorldCreator` MUST detect the target Environment from the world-name suffix (`_nether` / `_the_nether` / `_end` / `_the_end` / else NORMAL) -- NEVER hardcode `.environment(NORMAL)` at the call site. Suffix detection is the single source of truth for dimension binding; hardcoding silently mis-loads nether/end twin worlds as overworlds with empty terrain.

### Why this is an apex completion standard

The trap is silent -- no exception, no warning, no log line indicating the env was wrong. A nether twin world loaded as NORMAL still LOADS; players can teleport in; they just see overworld terrain instead of the nether content sitting on disk in `DIM-1/region/`. Discovered empirically (Pane 3 2026-05-26 Block 5 5-world deploy) only because of the `/kobimap listworlds` post-deploy review.

The canonical fix is a one-time refactor: extract a public static helper `detectEnvironment(String sanitizedName)` and call it from every WorldCreator site. Once it exists, every future WorldCreator caller inherits the right behavior. Tests are pure-logic (10 hermetic cases in `EnvironmentDetectionTest`, no MockBukkit needed).

### Mandatory checks for any future world-creation code path

1. NEVER write `.environment(World.Environment.NORMAL)` as a literal at a WorldCreator site.
2. ALWAYS call `WorldService.detectEnvironment(name)` or pass an explicit `Environment` parameter.
3. Suffix detection is case-insensitive (defensive against caller-pre-uppercased names).
4. SUFFIX match -- substring match is wrong (`netherworld_overworld` must NOT be detected as nether).
5. Defensive defaults: null / empty input -> NORMAL.
6. Log the detected env on the `[WorldService] created+registered` line so it is greppable in boot logs.

### What "done" looks like -- evidence contract

- `WorldService.detectEnvironment(String)` is public+static, called from EVERY WorldCreator site in the codebase.
- Hermetic test class with >=7 cases (NETHER suffix, alternate `_the_nether`, THE_END, alternate `_end`, NORMAL default, case-insensitive, substring rejection, null/empty defensive).
- Boot log includes `env=NETHER` / `env=THE_END` / `env=NORMAL` on the WorldService init line for each registered world.

### Related sibling axis -- Wrapper-Over-Tested-Core (KME-042)

When adding a shorter/friendlier subcommand surface that exposes already-tested behavior (e.g., `/kobimap recreate <id>` over the existing `mirror dna <id>` path), implement it as a THIN WRAPPER that translates args and delegates -- do NOT re-implement the logic. The wrapper test surface is `hasValidArgs(args)` + `buildDelegatedArgs(input)` static helpers; the delegated body is exercised by the existing tests on the core logic. KME-042 shipped in ~1.5h vs the original 6-10h estimate (which assumed re-implementation).

### Project reference

`docs/server/GOLD_STANDARD_SERVERS.md` Sec 24 (World Environment Suffix Detection + Recreate Wrapper). UKDL Trap 19 (`WorldService.createOrReuseMapWorld` silently hardcodes Environment to NORMAL). Seal addendum in `docs/server/PANE3_BLOCK5_SEAL.md` (Pane 3, 2026-05-26 evening section "Addendum 2026-05-26 evening -- KME-env + KME-042 fixes shipped").
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
    if "Pane 3, KobiiCraft -- relocated" in clean:
        print("Pane-3 relocation already present in origin/main (idempotent skip)")
        return 0
    merged = clean + PANE3_SECTION

    for target in (LOOSE, PP):
        _atomic_write(target, merged)
        print(f"recovered {target} (bytes={target.stat().st_size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
