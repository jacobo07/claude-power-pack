#!/usr/bin/env python3
"""agent_spec.py -- AgentSpec: a capability contract that a carrier agent can run.

Spec: vault/specs/agent-capability-virtualization.md (S1).

Why this exists. Claude Code lists every resident agent file in the parent's
Agent tool (name + description + tools, measured 64-88 tokens per agent, no
ceiling). A specialist that is a FILE therefore taxes every session. A
specialist that is a SPEC costs nothing until it is dispatched: a small, fixed
set of resident CARRIER agents (one per permission class) receives the spec
compiled into its prompt.

An AgentSpec is a `CapabilityContract` (identity, triggers, scope, risk,
retirement -- `contract.py:79`) plus an `agent` section:

  permission_class  investigator | verifier | writer. Decides the carrier and
                    therefore the tool surface, which the RUNTIME enforces
                    through the carrier's frontmatter. A spec never names tools.
  pages             ordered chunks of the role body. `inline` pages go into the
                    carrier prompt; `on_demand` pages are handed over as file
                    paths the specialist Reads only when its task touches them.
                    Concatenating every page in order reproduces the source
                    body byte for byte (the reconstruction gate).
  model_policy      {"default": <alias>} -- a policy, not an identity.
  output_contract   "native" (the role body defines its own output) or the id
                    of a shared primitive under vault/capability_runtime/
                    agent_primitives/.
  description       the listing text used only for an AOT projection file.

Failures are typed (`AgentSpecError` with a code), never coerced to an empty
spec: a missing page, a hash mismatch and an unknown class are different facts.

CLI:
  python -m modules.capability_runtime.agent_spec split <source.md> <spec_dir> --markers-file <m.json>
  python -m modules.capability_runtime.agent_spec compile <spec_id> --mission-file <f> [--mode virtual|monolithic|crippled]
  python -m modules.capability_runtime.agent_spec project <spec_id>
  python -m modules.capability_runtime.agent_spec list
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CapabilityContract, ContractError, from_dict,
)

SPECS_DIR = _PP_ROOT / "vault" / "capability_runtime" / "agent_specs"
PRIMITIVES_DIR = _PP_ROOT / "vault" / "capability_runtime" / "agent_primitives"
CARRIERS_DIR = _PP_ROOT / "agents" / "carriers"

# The ONLY place tool surfaces are named. Ordered least -> most privileged.
CLASS_TOOLS = {
    "investigator": ["Read", "Grep", "Glob"],
    "verifier": ["Read", "Grep", "Glob", "Bash"],
    "writer": ["Read", "Grep", "Glob", "Bash", "Edit", "Write"],
}
CLASS_ORDER = list(CLASS_TOOLS)
CARRIER_PREFIX = "cpp-carrier-"
HEADER = "[COMPILED AGENTSPEC"
MODES = ("virtual", "monolithic", "crippled")


class AgentSpecError(ValueError):
    """Typed failure. `code` is stable and machine-readable."""

    def __init__(self, code: str, msg: str):
        super().__init__(f"{code}: {msg}")
        self.code = code


def carrier_name(permission_class: str) -> str:
    return f"{CARRIER_PREFIX}{permission_class}"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def class_rank(c: str) -> int:
    if c not in CLASS_TOOLS:
        raise AgentSpecError("UNKNOWN_CLASS", f"{c!r} not in {CLASS_ORDER}")
    return CLASS_ORDER.index(c)


class AgentSpec:
    def __init__(self, raw: dict, spec_dir: Path):
        self.raw = raw
        self.dir = spec_dir
        try:
            self.contract: CapabilityContract = from_dict(raw.get("contract") or {})
        except (ContractError, TypeError) as e:
            raise AgentSpecError("INVALID_CONTRACT", str(e)) from e
        a = raw.get("agent") or {}
        self.permission_class = a.get("permission_class", "")
        class_rank(self.permission_class)
        self.pages = a.get("pages") or []
        self.model_policy = a.get("model_policy") or {}
        self.output_contract = a.get("output_contract", "native")
        self.description = a.get("description", "")
        self.source = a.get("source") or {}
        self.validate()

    @property
    def id(self) -> str:
        return self.contract.id

    def validate(self) -> None:
        if not self.pages:
            raise AgentSpecError("NO_PAGES", f"{self.id}: a spec needs at least one page")
        if not any(p.get("load") == "inline" for p in self.pages):
            raise AgentSpecError("NO_INLINE_PAGE", f"{self.id}: nothing would reach the carrier prompt")
        for p in self.pages:
            if p.get("load") not in ("inline", "on_demand"):
                raise AgentSpecError("BAD_PAGE_LOAD", f"{self.id}: page {p.get('path')} load={p.get('load')!r}")
        # Authority coherence: an investigator cannot own a write surface. The class, not the
        # caller, decides the tool surface, and it must agree with what the contract declares.
        if self.contract.write_surfaces and self.permission_class != "writer":
            raise AgentSpecError("CLASS_BELOW_WRITE_SURFACE",
                                 f"{self.id}: write_surfaces {self.contract.write_surfaces} "
                                 f"need class writer, spec says {self.permission_class}")
        if self.output_contract != "native" and not (PRIMITIVES_DIR / f"{self.output_contract}.md").is_file():
            raise AgentSpecError("MISSING_OUTPUT_CONTRACT", f"{self.id}: {self.output_contract}")

    def page_text(self, page: dict) -> str:
        path = self.dir / page["path"]
        if not path.is_file():
            raise AgentSpecError("MISSING_PAGE", str(path))
        # Line endings are normalised before hashing: this repo checks text out with
        # core.autocrlf, so raw bytes differ between the machine that sealed the spec
        # and every fresh clone. Content, not the checkout's newline policy, is identity.
        data = path.read_bytes().replace(b"\r\n", b"\n")
        if page.get("sha256") and _sha(data) != page["sha256"]:
            raise AgentSpecError("PAGE_HASH_MISMATCH", f"{path} changed since the spec was sealed")
        return data.decode("utf-8")

    def spec_hash(self) -> str:
        """Identity of the whole spec: contract + agent section + every page's bytes."""
        h = hashlib.sha256(json.dumps(self.raw, sort_keys=True).encode())
        for p in self.pages:
            h.update(self.page_text(p).encode())
        return h.hexdigest()[:16]

    # --- projections -------------------------------------------------------

    def body(self) -> str:
        return "".join(self.page_text(p) for p in self.pages)

    def project(self) -> str:
        """AOT projection: a real agent file. The spec stays authority."""
        fm = self.source.get("frontmatter")
        if fm is None:
            model = self.model_policy.get("default", "")
            fm = (f"---\nname: {self.id}\ndescription: {self.description}\n"
                  f"tools: {', '.join(CLASS_TOOLS[self.permission_class])}\n"
                  + (f"model: {model}\n" if model else "") + "---\n")
        return fm + self.body()

    def compile(self, mission: str, mode: str = "virtual") -> str:
        """Carrier prompt. `monolithic` = every page inline (the pre-virtualization
        role); `virtual` = inline pages + on-demand page paths; `crippled` = inline
        pages only (the benchmark's positive control)."""
        if mode not in MODES:
            raise AgentSpecError("BAD_MODE", mode)
        if not mission.strip():
            raise AgentSpecError("EMPTY_MISSION", self.id)
        out = [f"{HEADER} {self.id}@{self.contract.version} class={self.permission_class} "
               f"spec={self.spec_hash()} mode={mode}]\n"]
        deep = []
        for p in self.pages:
            if p["load"] == "inline" or mode == "monolithic":
                out.append(self.page_text(p))
            else:
                deep.append(p)
        if deep and mode == "virtual":
            out.append("\n## Deep pages of this role\n\nThese are part of your role but not loaded yet. "
                       "Read a page with the Read tool as soon as your task touches its topics; "
                       "never guess what a page says.\n\n")
            for p in deep:
                out.append(f"- `{(self.dir / p['path']).as_posix()}` -- {', '.join(p.get('topics', []))}\n")
        if self.output_contract != "native":
            out.append("\n" + (PRIMITIVES_DIR / f"{self.output_contract}.md").read_text(encoding="utf-8"))
        out.append(f"\n## Mission\n\n{mission.strip()}\n")
        return "".join(out)

    def dispatch(self, mission: str, mode: str = "virtual") -> dict:
        """What the parent passes to the Agent tool."""
        return {"subagent_type": carrier_name(self.permission_class),
                "model": self.model_policy.get("default"),
                "prompt": self.compile(mission, mode)}


# --- catalog ---------------------------------------------------------------

def load(spec_id: str, specs_dir: Path | None = None) -> AgentSpec:
    d = (specs_dir or SPECS_DIR) / spec_id
    f = d / "spec.json"
    if not f.is_file():
        raise AgentSpecError("UNKNOWN_SPEC", spec_id)
    try:
        raw = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise AgentSpecError("UNREADABLE_SPEC", f"{f}: {e}") from e
    return AgentSpec(raw, d)


def catalog(specs_dir: Path | None = None) -> tuple[list[AgentSpec], list[dict]]:
    """Every spec that loads, plus a typed record for every one that does not."""
    root = specs_dir or SPECS_DIR
    ok, bad = [], []
    if not root.is_dir():
        return ok, [{"spec": str(root), "code": "NO_CATALOG"}]
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        try:
            ok.append(load(d.name, root))
        except AgentSpecError as e:
            bad.append({"spec": d.name, "code": e.code, "detail": str(e)})
    return ok, bad


# --- split: turn a monolithic agent file into pages ------------------------

_FM = re.compile(r"^---\r?\n.*?\r?\n---\r?\n", re.S)


def split(source: Path, spec_dir: Path, markers: list[dict], contract: dict, agent: dict) -> dict:
    """Cut `source`'s body at each marker line prefix (in order). Each marker:
    {"prefix": <line start or "" for body start>, "slug", "load", "topics"}."""
    text = source.read_text(encoding="utf-8")
    m = _FM.match(text)
    if not m:
        raise AgentSpecError("NO_FRONTMATTER", str(source))
    frontmatter, body = text[:m.end()], text[m.end():]
    starts = []
    for mk in markers:
        if mk["prefix"] == "":
            starts.append(0)
            continue
        hits = [x.start() for x in re.finditer(r"(?m)^" + re.escape(mk["prefix"]), body)]
        if len(hits) != 1:
            raise AgentSpecError("MARKER_NOT_UNIQUE", f"{mk['prefix']!r} matched {len(hits)} times")
        starts.append(hits[0])
    if starts != sorted(starts) or starts[0] != 0:
        raise AgentSpecError("MARKERS_OUT_OF_ORDER", str(starts))
    (spec_dir / "pages").mkdir(parents=True, exist_ok=True)
    pages = []
    for i, mk in enumerate(markers):
        chunk = body[starts[i]: starts[i + 1] if i + 1 < len(starts) else len(body)]
        rel = f"pages/{i + 1:02d}-{mk['slug']}.md"
        (spec_dir / rel).write_bytes(chunk.encode("utf-8"))
        pages.append({"path": rel, "load": mk["load"], "topics": mk.get("topics", []),
                      "bytes": len(chunk.encode()), "sha256": _sha(chunk.encode())})
    raw = {"contract": contract,
           "agent": {**agent, "pages": pages,
                     "source": {"file": source.as_posix(), "sha256": _sha(text.encode()),
                                "frontmatter": frontmatter}}}
    (spec_dir / "spec.json").write_text(json.dumps(raw, indent=1), encoding="utf-8")
    spec = AgentSpec(raw, spec_dir)
    if spec.project() != text:
        raise AgentSpecError("RECONSTRUCTION_FAILED", f"{source} does not round-trip")
    return raw


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="agent_spec")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split"); s.add_argument("source"); s.add_argument("spec_dir"); s.add_argument("--markers-file", required=True)
    c = sub.add_parser("compile"); c.add_argument("spec_id"); c.add_argument("--mission-file", required=True)
    c.add_argument("--mode", default="virtual", choices=MODES); c.add_argument("--json", action="store_true")
    p = sub.add_parser("project"); p.add_argument("spec_id")
    sub.add_parser("list")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "split":
            cfg = json.loads(Path(a.markers_file).read_text(encoding="utf-8"))
            raw = split(Path(a.source), Path(a.spec_dir), cfg["markers"], cfg["contract"], cfg["agent"])
            pages = raw["agent"]["pages"]
            inline = sum(p["bytes"] for p in pages if p["load"] == "inline")
            print(f"SPLIT ok pages={len(pages)} inline_bytes={inline} total_bytes={sum(p['bytes'] for p in pages)}")
        elif a.cmd == "compile":
            spec = load(a.spec_id)
            mission = Path(a.mission_file).read_text(encoding="utf-8")
            if a.json:
                print(json.dumps(spec.dispatch(mission, a.mode)))
            else:
                sys.stdout.write(spec.compile(mission, a.mode))
        elif a.cmd == "project":
            sys.stdout.write(load(a.spec_id).project())
        elif a.cmd == "list":
            ok, bad = catalog()
            for sp in ok:
                print(f"{sp.id}\t{sp.permission_class}\t{sp.contract.maturity.value}\t{sp.spec_hash()}")
            for b in bad:
                print(f"BROKEN\t{b['spec']}\t{b['code']}")
            return 1 if bad else 0
    except AgentSpecError as e:
        print(f"AGENTSPEC_ERROR {e.code} {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
