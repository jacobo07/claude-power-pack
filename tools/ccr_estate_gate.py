"""V-CCR-ESTATE-ELASTIC (CCR v4 A4): a Work Unit's model-facing estate bytes must not grow with the estate.

Feeds decideUnitAttachment / decideUnitSection of a mod's policy.ts this host's REAL instruction files (user
CLAUDE.md, every rules/**/*.md, the project CLAUDE.md), then the same estate 10x inflated (10x the files, 10x every
skill / agent / memory listing). Gate: the unit's out bytes for the whole estate stay within the kernel size the
runtime reads (KERNEL_CHARS = 8000, register.ts `.slice(0, 8000)`), at 1x and at 10x.

A `claude plugin test` module may import only its own files, so the gate assembles a throwaway mod: a byte-identical
copy of <mod>/hooks/policy.ts (sha256 recorded), the estate as a generated fixture, and the test. The mod under test
is only read.

    python tools/ccr_estate_gate.py --mod mods/cpp-cognitive-runtime [--claude ~/.local/bin/claude] [--json out.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KERNEL_CHARS = 8000
INFLATE = 10
LISTING_BYTES = 20_000   # 1x skill / agent / memory listing; 10x is 200,000

TEST = r"""import { expect, test } from 'claude-code/testing'
import { decideUnitAttachment, decideUnitSection } from './policy'
import { ESTATE, KERNEL } from './estate.fixture'

const KERNEL_CHARS = __KERNEL_CHARS__
const INFLATE = __INFLATE__
const LISTING = __LISTING__
type F = { path: string; kind: string; content: string }

function inflate(files: readonly F[], k: number): F[] {
  const out: F[] = []
  for (let i = 0; i < k; i++) for (const f of files) out.push({ ...f, path: i ? f.path.replace(/\.md$/, `.x${i}.md`) : f.path })
  return out
}

function unitOut(files: readonly F[], listingBytes: number): Record<string, number> {
  const kernel = KERNEL.slice(0, KERNEL_CHARS)
  const instr = decideUnitAttachment('instructions', kernel, files)
  const one = (t: string) => { const d = decideUnitAttachment(t, kernel, files); return d.action === 'drop' ? 0 : d.action === 'replace' ? (d.text ?? '').length : listingBytes }
  return {
    instructions: instr.action === 'replace' ? (instr.text ?? '').length : files.reduce((s, f) => s + f.content.length, 0),
    skills: one('skill_listing'),
    agents: one('agent_listing_delta'),
    memory: decideUnitSection('memory').action === 'drop' ? 0 : listingBytes,
  }
}

test('estate elasticity: unit out-bytes stay within the kernel size at 1x and 10x estate', () => {
  const sum = (r: Record<string, number>) => Object.values(r).reduce((a, b) => a + b, 0)
  const one = unitOut(ESTATE, LISTING)
  const ten = unitOut(inflate(ESTATE, INFLATE), INFLATE * LISTING)
  const in1 = ESTATE.reduce((s, f) => s + f.content.length, 0) + 3 * LISTING
  console.log('ESTATE_GATE ' + JSON.stringify({ kernel: KERNEL.length, bound: KERNEL_CHARS, files1x: ESTATE.length, in1x: in1, out1x: one,
    sum1x: sum(one), files10x: ESTATE.length * INFLATE, in10x: INFLATE * in1, out10x: ten, sum10x: sum(ten),
    slope: +((sum(ten) - sum(one)) / ((INFLATE - 1) * in1)).toFixed(6) }))
  expect(ten.skills + ten.agents + ten.memory).toBe(0)
  expect(sum(one)).toBeLessThanOrEqual(KERNEL_CHARS)
  expect(sum(ten)).toBeLessThanOrEqual(KERNEL_CHARS)
})
"""


def estate(home: Path) -> list[dict]:
    paths = [home / ".claude/CLAUDE.md", *sorted((home / ".claude/rules").rglob("*.md")), ROOT / "CLAUDE.md"]
    return [{"path": p.as_posix(), "kind": "project" if p == ROOT / "CLAUDE.md" else "user",
             "content": p.read_text(encoding="utf-8", errors="replace")} for p in paths if p.is_file()]


def run(mod: Path, claude: str, home: Path) -> dict:
    policy = (mod / "hooks/policy.ts").read_bytes()
    kernel = (mod / "kernel/HARD-RULES-DIGEST.md").read_text(encoding="utf-8")
    files = estate(home)
    with tempfile.TemporaryDirectory(prefix="ccr-estate-gate-") as d:
        g = Path(d)
        (g / ".claude-plugin").mkdir()
        (g / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "ccr-estate-gate", "version": "0.0.1",
                                                                  "description": "CCR A4 estate gate"}))
        (g / "hooks").mkdir()
        (g / "hooks/hooks.json").write_text('{ "modules": ["./gate.ts"] }\n')
        (g / "hooks/gate.ts").write_text("import type { Register } from 'claude-code'\nexport const register: Register = () => {}\n")
        (g / "hooks/policy.ts").write_bytes(policy)
        (g / "hooks/estate.fixture.ts").write_text(
            f"export const KERNEL: string = {json.dumps(kernel)}\n"
            f"export const ESTATE: {{ path: string; kind: string; content: string }}[] = {json.dumps(files)}\n",
            encoding="utf-8")
        (g / "hooks/estate.test.ts").write_text(TEST.replace("__KERNEL_CHARS__", str(KERNEL_CHARS))
                                                .replace("__INFLATE__", str(INFLATE)).replace("__LISTING__", str(LISTING_BYTES)))
        r = subprocess.run([claude, "plugin", "test", str(g)], capture_output=True, text=True, timeout=300)
    out = r.stdout + r.stderr
    m = re.search(r"ESTATE_GATE (\{.*\})", out)
    return {"mod": mod.as_posix(), "policy_sha256": hashlib.sha256(policy).hexdigest(), "exit": r.returncode,
            "verdict": "PASS" if r.returncode == 0 and m else "FAIL", "facts": json.loads(m.group(1)) if m else None,
            "files": [f["path"] for f in files], "tail": out.strip().splitlines()[-6:]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ccr_estate_gate")
    ap.add_argument("--mod", required=True)
    ap.add_argument("--claude", default=os.path.expanduser("~/.local/bin/claude"))
    ap.add_argument("--home", default=os.path.expanduser("~"))
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    res = run(Path(a.mod).resolve(), a.claude, Path(a.home))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("verdict", "exit", "policy_sha256", "facts", "tail")}, indent=1))
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
