"""Mutation drill for test_gsd_x_structured_facts.py (GSDX-M04).

Each mutant removes one semantic the W2 gate claims to protect. It is CAUGHT
only if the gate exits 1 AND the gate named for that semantic is among the
failures; a red for some other reason is scored as a survival.

Mutation is textual and in place, on files this wave owns, inside try/finally.
Every file is hashed before, and the drill fails as HARNESS if any restore does
not reproduce the original bytes. An unmutated control runs first so a broken
harness cannot manufacture catches.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "tools" / "test_gsd_x_structured_facts.py"
SF = REPO / "modules" / "gsd_x" / "mission" / "structured_facts.py"
OB = REPO / "modules" / "gsd_x" / "mission" / "obligation.py"
CLI = REPO / "tools" / "gsd_x_mission.py"

# (name, file, exact old text, replacement, gate that must go red)
MUTANTS = [
    # RE-ANCHORED 2026-09-25 (GSDX-M05). The v2 loader moved name validation
    # into `_require_name` and replaced the `seen` set with a cross-bucket
    # `claim()`. Both anchors then matched 0x and this drill exited 2 as
    # HARNESS-FAILED -- which says NOTHING about the subject while the wave's
    # regression line still quoted "7/7 mutations" as evidence. A drill pinned
    # to exact source text decays the moment that text is refactored, and it
    # decays SILENTLY into a number nobody re-earned. Re-anchor in the same
    # commit as the refactor, never in a follow-up.
    ("accept-unknown-name", SF,
     "    if name not in FACT_NAMES:\n",
     "    if False and name not in FACT_NAMES:\n",
     "V-GSDXFACTS-REFUSE-UNKNOWN-NAME"),
    ("accept-no-evidence", SF,
     "        if not isinstance(evidence, str) or not evidence.strip():\n",
     "        if not isinstance(evidence, str):\n",
     "V-GSDXFACTS-REFUSE-NO-EVIDENCE"),
    # Blinding `claim()`'s lookup disables BOTH duplicate detection and the
    # cross-bucket contradiction refusal: with `prior` always None every name
    # is recorded as first-seen and nothing can ever raise.
    ("accept-duplicate", SF,
     "        prior = seen.get(name)\n",
     "        prior = None\n",
     "V-GSDXFACTS-REFUSE-DUPLICATE"),
    ("die-on-bom", SF,
     'doc = json.loads(path.read_text(encoding="utf-8-sig"))',
     'doc = json.loads(path.read_text(encoding="utf-8"))',
     "V-GSDXFACTS-BOM-TOLERATED"),
    ("structured-ignored-by-operators", OB,
     "    out = []\n    for op in OPERATORS:\n        ob = op(facts, intent, reality)",
     "    facts = extract_facts(intent, reality)\n    out = []\n"
     "    for op in OPERATORS:\n        ob = op(facts, intent, reality)",
     "V-GSDXFACTS-G1-UNSEEN-DERIVES"),
    ("cli-never-reads-structured", CLI,
     "    source = sf.source_of(root)\n",
     '    source = "prose"\n',
     "V-GSDXFACTS-CLI-END-TO-END"),
    ("provenance-not-required", SF,
     "    if not isinstance(prov, str) or not prov.strip():\n",
     "    if False:\n",
     "V-GSDXFACTS-REFUSE-NO-PROVENANCE"),
]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _run_gate() -> tuple[int, list[str]]:
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True,
                       encoding="utf-8", timeout=180)
    failed = [ln.split()[1].rstrip(":") for ln in r.stdout.splitlines()
              if ln.strip().startswith("FAIL ")]
    return r.returncode, failed


def main() -> int:
    files = {SF, OB, CLI}
    before = {p: _sha(p) for p in files}

    code, failed = _run_gate()
    if code != 0:
        print(f"HARNESS-FAILED: unmutated gate is not green (exit {code}, failed={failed})")
        print("GSDX_FACTS_MUTATIONS_CAUGHT=0/0  threshold=HARNESS")
        return 2
    print("  CONTROL unmutated: exit 0")

    caught = 0
    for name, path, old, new, must in MUTANTS:
        original = path.read_bytes()
        text = original.decode("utf-8")
        # ANCHORS ARE WRITTEN WITH \n AND THE FILE MAY BE CRLF. `core.autocrlf`
        # is true on this host, so a file CLEAN FROM CHECKOUT arrives as CRLF
        # while a file dirty in the working tree keeps the LF its writer used.
        # Measured 2026-09-25: gsd_x_mission.py was LF=302/CRLF=302 (every line)
        # while structured_facts.py and obligation.py were pure LF -- so this
        # drill's verdict depended on whether its target happened to be
        # modified. It exited 2 as HARNESS-FAILED, which says nothing about the
        # subject, while the wave's regression line still quoted a mutation
        # count nobody had re-earned. Translate the anchor to the file's own
        # convention; the restore is byte-exact either way.
        nl = "\r\n" if "\r\n" in text else "\n"
        old_a, new_a = old.replace("\n", nl), new.replace("\n", nl)
        if text.count(old_a) != 1:
            print(f"HARNESS-FAILED: mutant {name!r} anchor found "
                  f"{text.count(old_a)}x in {path.name} (line endings: "
                  f"{'CRLF' if nl == chr(13) + chr(10) else 'LF'})")
            return 2
        try:
            # Write bytes, not text: the restore below must reproduce the file
            # exactly, and a text-mode write on Windows would convert LF to CRLF.
            path.write_bytes(text.replace(old_a, new_a).encode("utf-8"))
            code, failed = _run_gate()
        finally:
            path.write_bytes(original)
        hit = code == 1 and must in failed
        caught += hit
        print(f"  {'CAUGHT' if hit else 'SURVIVED':8} {name:34} expected {must}  "
              f"exit={code} failed={failed}")

    after = {p: _sha(p) for p in files}
    moved = [p.name for p in files if before[p] != after[p]]
    if moved:
        print(f"HARNESS-FAILED: restore did not reproduce original bytes for {moved}")
        return 2
    print(f"  restore verified by sha256 for {sorted(p.name for p in files)}")

    print(f"\nGSDX_FACTS_MUTATIONS_CAUGHT={caught}/{len(MUTANTS)}  "
          f"threshold={len(MUTANTS)}/{len(MUTANTS)}")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
