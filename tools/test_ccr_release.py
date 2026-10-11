"""V-CCR-* gates for tools/ccr_release.py. Every case runs in a temporary root; ~/.claude is never touched."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_release as cr  # noqa: E402

passes = fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def check(gate: str, cond: bool, ev: str) -> None:
    (_ok if cond else _fail)(gate, ev)


def make_mod(base: Path, version: str, body: str) -> Path:
    mod = base / f"mod-{version}-{abs(hash(body)) % 1000}"
    (mod / ".claude-plugin").mkdir(parents=True)
    (mod / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": cr.PLUGIN, "version": version}), encoding="utf-8")
    (mod / "hooks").mkdir()
    (mod / "hooks" / "register.ts").write_text(body, encoding="utf-8")
    (mod / "hooks" / "policy.test.ts").write_text("test", encoding="utf-8")
    (mod / ".state-dev" / "receipts").mkdir(parents=True)
    (mod / ".state-dev" / "receipts" / "x.jsonl").write_text("{}", encoding="utf-8")
    return mod


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        root = base / "ccr"
        root.mkdir()
        digest = base / "DIGEST.md"
        digest.write_text("# HARD-RULES DIGEST\n", encoding="utf-8")

        # Arrange / Act: build and activate v1
        m1 = make_mod(base, "0.1.0", "export const v = 1")
        r1 = cr.build(root, m1, digest)
        cr.activate(root, r1)
        active = root / "active"
        check("V-CCR-BUILD-EXCLUDES-DEV", not (r1 / ".state-dev").exists() and not (r1 / "hooks" / "policy.test.ts").exists(),
              "release has no .state-dev and no *.test.ts")
        check("V-CCR-KERNEL-FROM-DIGEST", (r1 / "kernel" / "HARD-RULES-DIGEST.md").read_text(encoding="utf-8") == digest.read_text(encoding="utf-8"),
              "kernel copied from the compiled digest")
        check("V-CCR-IDEMPOTENT", cr.build(root, m1, digest) == r1, "same content builds the same release")
        mp = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        check("V-CCR-MARKETPLACE", mp["plugins"][0]["source"] == "./active" and mp["name"] == cr.MARKETPLACE,
              f"marketplace entry {mp['plugins'][0]}")

        # v2 then rollback restores v1 (and a second rollback restores v2)
        m2 = make_mod(base, "0.2.0", "export const v = 2")
        r2 = cr.build(root, m2, digest)
        cr.activate(root, r2)
        check("V-CCR-ACTIVATE", "v = 2" in (active / "hooks" / "register.ts").read_text(encoding="utf-8"), "active is v2")
        cr.rollback(root)
        check("V-CCR-ROLLBACK", "v = 1" in (active / "hooks" / "register.ts").read_text(encoding="utf-8")
              and cr.status(root)["version"] == "0.1.0", "rollback restores v1")
        cr.rollback(root)
        check("V-CCR-ROLLFORWARD", "v = 2" in (active / "hooks" / "register.ts").read_text(encoding="utf-8"), "second rollback restores v2")

        # kill switch: OFF exists, then is removed (control: on leaves no flag)
        check("V-CCR-OFF", cr.set_off(root, True) and (root / "state" / "OFF").exists(), "off writes state/OFF")
        check("V-CCR-ON", not cr.set_off(root, False) and not (root / "state" / "OFF").exists(), "on removes state/OFF")

        # refusals
        try:
            cr.activate(root, root / ".." / "elsewhere")
            _fail("V-CCR-REFUSE-OUTSIDE", "activate accepted a path outside root")
        except SystemExit as e:
            _ok("V-CCR-REFUSE-OUTSIDE", str(e))
        try:
            cr.build(root, m1, base / "missing.md")
            _fail("V-CCR-REFUSE-NO-KERNEL", "built a release without the kernel digest")
        except SystemExit as e:
            _ok("V-CCR-REFUSE-NO-KERNEL", str(e))
        fresh = base / "fresh"
        fresh.mkdir()
        try:
            cr.rollback(fresh)
            _fail("V-CCR-REFUSE-NO-PREV", "rolled back with no previous release")
        except SystemExit as e:
            _ok("V-CCR-REFUSE-NO-PREV", str(e))

        cmds = cr.install_commands(root)
        check("V-CCR-INSTALL-PRINTED-ONLY", len(cmds) == 2 and cmds[1].startswith("claude plugin install cpp-cognitive-runtime@cpp-local"),
              "install commands are printed, never run")

    print(f"CCR_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
