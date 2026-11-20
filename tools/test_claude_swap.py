#!/usr/bin/env python3
"""Done-gate for the absorbed claude-swap skill (realiti4/claude-swap, MIT).

Run from the Power Pack repo root:

    python tools/test_claude_swap.py

Exit 0 = absorption is sound. Exit 1 = a gate failed.

Each content check is also driven from its failing pole: the hash and version
comparators are fed a mutated input and must reject it, so a comparator that
always answers "match" fails here instead of passing silently.

The installed-tool gate runs only `cswap --version`, which reads no account
state. It never runs add/switch/auto/list: those touch live credentials or the
network and do not belong in a gate. When cswap is not on PATH the gate is
reported UNMEASURED (it is not a pass), and the exit code stays 0 only because
an uninstalled tool is a legitimate state on another machine.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(REPO, "skills", "claude-swap")
MIRROR = os.path.join(os.path.expanduser("~"), ".claude", "skills", "claude-swap")
UKDL = os.path.join(REPO, "vault", "knowledge_base", "ukdl-universal.md")
CLAUDE_MD = os.path.join(REPO, "CLAUDE.md")

PINNED_VERSION = "1.1.0"
UPSTREAM_COMMIT = "ee79e705cf6e1ad3f70621b88b80983a99bb2001"

# sha256 of the verbatim upstream files with CRLF normalised to LF, so a
# checkout under core.autocrlf does not read as tampering.
VERBATIM = {
    "LICENSE": "a6860f35f08a77af9268bcd10fbb57d34a1c0b3e0715ac013ce12f795d453e8b",
    "references/AGENTS.upstream.md": "f9fd317ed72a6bd32df07a0f0963b51d43391787bcf77572243d8bce80b67120",
    "references/architecture.md": "d1933f84babde88254cc70f07d21b765242018d19223f8fa52956e3c1963f49e",
    "references/auto-switch.md": "dd63d7e5d9c715e558ea16c49a80be6a00ac62ba556317d19e96797f02037336",
    "references/json-output.md": "ec148d54f9858e2b391a2703c19222476f3568ade2e679274475bb9d41ef29e2",
}

UKDL_IDS = (
    "PR-SINGLE-USE-REFRESH-SUCCESSOR-001",
    "PR-CREDENTIAL-SLOT-OWNERSHIP-001",
    "PR-FOREIGN-LOCK-ORDER-NO-NETWORK-001",
)

PASSES: list[str] = []
FAILS: list[str] = []
UNMEASURED: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    PASSES.append(gate)
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    FAILS.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


def _unmeasured(gate: str, why: str) -> None:
    UNMEASURED.append(gate)
    print(f"  ---- {gate}: UNMEASURED ({why})")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def norm_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def version_matches(version_output: str, pinned: str) -> bool:
    """True when `cswap --version` output names exactly the pinned version."""
    m = re.search(r"\bcswap\s+(\S+)", version_output)
    return bool(m) and m.group(1) == pinned


def gate_files() -> None:
    required = ["SKILL.md", "NOTICE.md", *VERBATIM]
    missing = [r for r in required if not os.path.isfile(os.path.join(SKILL, r))]
    if missing:
        _fail("V-CSWAP-FILES", f"missing {missing}")
    else:
        _ok("V-CSWAP-FILES", f"{len(required)} files present")


def gate_verbatim() -> None:
    bad = []
    for rel, want in VERBATIM.items():
        path = os.path.join(SKILL, rel)
        if not os.path.isfile(path):
            continue  # reported by V-CSWAP-FILES
        with open(path, "rb") as fh:
            if norm_sha256(fh.read()) != want:
                bad.append(rel)
    # Failing pole: one mutated byte must change the hash.
    with open(os.path.join(SKILL, "LICENSE"), "rb") as fh:
        mutated = fh.read() + b" "
    if norm_sha256(mutated) == VERBATIM["LICENSE"]:
        _fail("V-CSWAP-VERBATIM", "comparator accepted a mutated LICENSE")
    elif bad:
        _fail("V-CSWAP-VERBATIM", f"hash drift in {bad} (upstream text must stay verbatim)")
    else:
        _ok("V-CSWAP-VERBATIM", f"{len(VERBATIM)} upstream files hash-match; mutated input rejected")


def gate_license() -> None:
    text = _read(os.path.join(SKILL, "LICENSE"))
    notice = _read(os.path.join(SKILL, "NOTICE.md"))
    if "MIT License" not in text or "Onur Cetinkol" not in text:
        _fail("V-CSWAP-LICENSE", "LICENSE lacks MIT header or copyright holder")
    elif UPSTREAM_COMMIT not in notice:
        _fail("V-CSWAP-LICENSE", "NOTICE.md does not pin the upstream commit")
    else:
        _ok("V-CSWAP-LICENSE", "MIT text + holder retained; NOTICE pins commit")


def gate_frontmatter() -> None:
    text = _read(os.path.join(SKILL, "SKILL.md"))
    m = re.match(r"---\n(.*?)\n---\n", text.replace("\r\n", "\n"), re.S)
    if not m:
        _fail("V-CSWAP-FRONTMATTER", "no YAML front matter")
        return
    fm = m.group(1)
    if not re.search(r"^name:\s*claude-swap\s*$", fm, re.M):
        _fail("V-CSWAP-FRONTMATTER", "name is not claude-swap")
    elif not re.search(r"^description:\s*\S.{40,}", fm, re.M):
        _fail("V-CSWAP-FRONTMATTER", "description missing or too short to route on")
    else:
        _ok("V-CSWAP-FRONTMATTER", "name + routable description")


def gate_pin_coherent() -> None:
    needle = f"claude-swap=={PINNED_VERSION}"
    where = [f for f in ("SKILL.md", "NOTICE.md") if needle not in _read(os.path.join(SKILL, f))]
    if where:
        _fail("V-CSWAP-PIN", f"{needle} absent from {where}")
    else:
        _ok("V-CSWAP-PIN", f"{needle} stated in SKILL.md and NOTICE.md")


def gate_ukdl() -> None:
    ukdl = _read(UKDL)
    skill = _read(os.path.join(SKILL, "SKILL.md"))
    undefined = [i for i in UKDL_IDS if not re.search(rf"^### {re.escape(i)}\s*$", ukdl, re.M)]
    uncited = [i for i in UKDL_IDS if i not in skill]
    if undefined:
        _fail("V-CSWAP-UKDL", f"cited but not defined in UKDL: {undefined}")
    elif uncited:
        _fail("V-CSWAP-UKDL", f"defined but SKILL.md does not cite: {uncited}")
    else:
        _ok("V-CSWAP-UKDL", f"{len(UKDL_IDS)} ids defined as UKDL headers and cited")


def gate_activation() -> None:
    text = _read(CLAUDE_MD)
    if "## claude-swap Activation Criteria" not in text:
        _fail("V-CSWAP-ACTIVATION", "CLAUDE.md has no claude-swap activation block")
    elif "python tools/test_claude_swap.py" not in text:
        _fail("V-CSWAP-ACTIVATION", "activation block does not name this gate")
    else:
        _ok("V-CSWAP-ACTIVATION", "CLAUDE.md activation block names the gate")


def gate_mirror() -> None:
    if not os.path.isdir(MIRROR):
        _fail("V-CSWAP-MIRROR", f"live mirror absent: {MIRROR}")
        return
    drift = []
    for root, _dirs, files in os.walk(SKILL):
        for name in files:
            src = os.path.join(root, name)
            rel = os.path.relpath(src, SKILL)
            dst = os.path.join(MIRROR, rel)
            if not os.path.isfile(dst):
                drift.append(f"{rel} (missing)")
                continue
            with open(src, "rb") as a, open(dst, "rb") as b:
                if norm_sha256(a.read()) != norm_sha256(b.read()):
                    drift.append(rel)
    if drift:
        _fail("V-CSWAP-MIRROR", f"mirror drift: {drift}")
    else:
        _ok("V-CSWAP-MIRROR", "~/.claude/skills/claude-swap matches repo copy")


def gate_installed() -> None:
    # Failing pole first: the comparator must reject a different version.
    if version_matches("cswap 1.0.0", PINNED_VERSION) or not version_matches(
        f"cswap {PINNED_VERSION}", PINNED_VERSION
    ):
        _fail("V-CSWAP-INSTALLED", "version comparator is not discriminating")
        return
    exe = shutil.which("cswap")
    if not exe:
        _unmeasured("V-CSWAP-INSTALLED", "cswap not on PATH")
        return
    try:
        out = subprocess.run(
            [exe, "--version"], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _fail("V-CSWAP-INSTALLED", f"cswap --version did not run: {exc!r}")
        return
    text = (out.stdout + out.stderr).strip()
    if out.returncode != 0:
        _fail("V-CSWAP-INSTALLED", f"exit {out.returncode}: {text[:200]}")
    elif not version_matches(text, PINNED_VERSION):
        _fail("V-CSWAP-INSTALLED", f"installed '{text}' != pin {PINNED_VERSION}")
    else:
        _ok("V-CSWAP-INSTALLED", f"{exe} reports '{text}'")


def main() -> int:
    print("claude-swap absorption gate")
    gate_files()
    if "V-CSWAP-FILES" in FAILS:
        print("RESULT: FAIL (files missing; later gates would only repeat it)")
        return 1
    gate_verbatim()
    gate_license()
    gate_frontmatter()
    gate_pin_coherent()
    gate_ukdl()
    gate_activation()
    gate_mirror()
    gate_installed()
    print(
        f"RESULT: {'FAIL' if FAILS else 'PASS'}  "
        f"pass={len(PASSES)} fail={len(FAILS)} unmeasured={len(UNMEASURED)}"
    )
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
