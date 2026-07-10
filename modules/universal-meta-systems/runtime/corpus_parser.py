"""Parse a read-only meta-systems corpus dataset into a structured spec.

The corpus is pure doctrine but *machine-parseable*: every dataset carries a
uniform contract layer -- PART V (Interfaces & Contracts: named operations with
Guarantee/optional-Never clauses), PART VI (Registries & Internal Pipelines:
`a -> b -> c` chains), PART VII (Governance & Lifecycle: a state machine + hard
`GV-N` gates). This module extracts exactly that layer. It reads only; it never
writes to the corpus.

Empirical shape (verified against MS-0/MS-2/MS-6, 7 datasets, 38 ops):
  - An op bullet: ``- **`NAME(args) -> output`** -- *Guarantee:* ... *Never:* ...``
    or the same with Guarantee/Never on the continuation line (MS-0 form).
  - `Never:` is OPTIONAL (27 of 38 ops have it); absence is normal, not an error.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


# ---- data model -----------------------------------------------------------

@dataclass(frozen=True)
class Op:
    """One published operation from PART V (Interfaces & Contracts)."""
    name: str
    args: str          # raw args text inside the parens ("" for no-arg ops)
    output: str        # text right of the arrow
    guarantee: str
    never: str = ""    # optional -- empty when the op declares no *Never:* clause

    @property
    def signature(self) -> str:
        return f"{self.name}({self.args}) -> {self.output}".strip()


@dataclass(frozen=True)
class Pipeline:
    """One internal pipeline from PART VI -- an ordered chain of steps."""
    name: str
    steps: tuple[str, ...]


@dataclass(frozen=True)
class Gate:
    """One hard governance gate (GV-N) from PART VII."""
    gid: str
    text: str


@dataclass
class MetaSystemSpec:
    ms_id: str                       # e.g. "MS-0"
    title: str                       # e.g. "THE PROVENANCE SUBSTRATE"
    source_path: str
    ops: list[Op] = field(default_factory=list)
    pipelines: list[Pipeline] = field(default_factory=list)
    lifecycle: tuple[str, ...] = ()
    gates: list[Gate] = field(default_factory=list)
    frozen_semantics: str = ""


# ---- corpus discovery (mirror of corpus-reference.md, read-only) ----------

_DEFAULT_CORPUS = Path(r"C:\Users\User\Apps\universal-meta-systems-corpus")


def find_corpus_root(start: Path | None = None) -> Path | None:
    """Locate the corpus root (the dir containing MASTER_INDEX.md), read-only.

    Order (per corpus-reference.md): env var -> sibling of the workspace ->
    Owner default. Returns None if none resolve; the caller reports honestly
    rather than fabricating a path.
    """
    import os

    env = os.environ.get("UNIVERSAL_META_SYSTEMS_CORPUS")
    if env:
        p = Path(env)
        if (p / "MASTER_INDEX.md").is_file():
            return p

    start = (start or Path.cwd()).resolve()
    for base in (start, *start.parents):
        cand = base / "universal-meta-systems-corpus"
        if (cand / "MASTER_INDEX.md").is_file():
            return cand

    if (_DEFAULT_CORPUS / "MASTER_INDEX.md").is_file():
        return _DEFAULT_CORPUS
    return None


def find_dataset(ms_id: str, corpus_root: Path) -> Path | None:
    """Resolve MS-N -> datasets/MS-N_*.md (glob, robust to the slug)."""
    n = ms_id.strip().upper()
    if not re.fullmatch(r"MS-[0-6]", n):
        return None
    matches = sorted((corpus_root / "datasets").glob(f"{n}_*.md"))
    return matches[0] if matches else None


# ---- parsing --------------------------------------------------------------

_PART_RE = re.compile(r"^##\s+PART\s+[IVXL]+\s+[—-]\s+(.+?)\s*$", re.MULTILINE)
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_ARROW = re.compile(r"\s*(?:->|→|-->)\s*")
_GUARANTEE_RE = re.compile(r"\*Guarantee:\*\s*(.*?)(?=\*Never:\*|$)", re.DOTALL)
_NEVER_RE = re.compile(r"\*Never:\*\s*(.*)", re.DOTALL)
_GATE_RE = re.compile(r"^-\s+\*\*(GV-\d+)\*\*\s*(.+?)\s*$", re.MULTILINE)
_TITLE_RE = re.compile(r"^#\s+META-SYSTEM\s+MS-\d+\s+[—-]\s+(.+?)\s*$", re.MULTILINE)


def _split_parts(text: str) -> dict[str, str]:
    """Map a PART's title-tail (upper-cased) -> its body text."""
    parts: dict[str, str] = {}
    matches = list(_PART_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = m.group(1).upper()
        parts[title] = text[m.end():end]
    return parts


def _find_part(parts: dict[str, str], needle: str) -> str:
    needle = needle.upper()
    for title, body in parts.items():
        if needle in title:
            return body
    return ""


def _op_blocks(body: str) -> list[str]:
    """Split a PART V body into per-op blocks (each begins ``- **```)."""
    blocks: list[str] = []
    cur: list[str] = []
    for line in body.splitlines():
        is_op_start = line.lstrip().startswith("- **`")
        if is_op_start:
            if cur:
                blocks.append("\n".join(cur))
            cur = [line]
        elif cur:
            stripped = line.strip()
            # a new non-op bullet, a bold sub-heading, or a rule ends the block
            if stripped.startswith("- ") or stripped.startswith("**") or stripped == "---":
                blocks.append("\n".join(cur))
                cur = []
            else:
                cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def _parse_ops(body: str) -> list[Op]:
    ops: list[Op] = []
    for block in _op_blocks(body):
        m = _BACKTICK_RE.search(block)
        if not m:
            continue
        sig = m.group(1).strip()
        if "(" not in sig:
            continue
        # Split on the arrow FIRST -- the call (left) never contains the arrow,
        # but the output CAN contain nested parens (e.g. "{Accepted | Rejected(reason)}"),
        # so paren-scanning the whole signature would swallow the output into args.
        sig_parts = _ARROW.split(sig, maxsplit=1)
        left = sig_parts[0].strip()
        output = sig_parts[1].strip() if len(sig_parts) > 1 else ""
        name = left.split("(", 1)[0].strip()
        if "(" in left:
            lo = left.find("(") + 1
            args = left[lo:left.rfind(")")] if ")" in left else left[lo:]
        else:
            args = ""
        rest = block[m.end():]
        gm = _GUARANTEE_RE.search(rest)
        guarantee = " ".join(gm.group(1).split()) if gm else ""
        nm = _NEVER_RE.search(rest)
        never = " ".join(nm.group(1).split()) if nm else ""
        ops.append(Op(name=name, args=args.strip(), output=output,
                      guarantee=guarantee, never=never))
    return ops


def _parse_pipelines(body: str) -> list[Pipeline]:
    pipes: list[Pipeline] = []
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("- **"):
            continue
        nm = re.match(r"-\s+\*\*(.+?):\*\*", s)
        if not nm:
            continue
        chain = _BACKTICK_RE.search(s)
        if not chain:
            continue
        steps = tuple(x.strip() for x in _ARROW.split(chain.group(1)) if x.strip())
        if len(steps) >= 2:
            pipes.append(Pipeline(name=nm.group(1).strip(), steps=steps))
    return pipes


def _parse_lifecycle(body: str) -> tuple[str, ...]:
    for line in body.splitlines():
        if "lifecycle:" in line.lower():
            chain = _BACKTICK_RE.search(line)
            if chain:
                return tuple(x.strip() for x in _ARROW.split(chain.group(1)) if x.strip())
    return ()


def _parse_frozen(body: str) -> str:
    # PART V tail: "**Frozen semantics:** ..." or "**Semantic contract ...:** ..."
    m = re.search(r"\*\*(?:Frozen semantics|Semantic contract[^:]*):\*\*\s*(.+)", body)
    return " ".join(m.group(1).split()) if m else ""


def parse_dataset(path: str | Path) -> MetaSystemSpec:
    """Parse one dataset markdown file into a MetaSystemSpec (read-only)."""
    p = Path(path)
    text = p.read_text(encoding="utf-8-sig")  # strip any BOM on cross-tool reads

    ms_m = re.search(r"MS-\d+", p.name)
    ms_id = ms_m.group(0) if ms_m else p.stem
    title_m = _TITLE_RE.search(text)
    title = title_m.group(1).strip() if title_m else ms_id

    parts = _split_parts(text)
    v_body = _find_part(parts, "INTERFACES & CONTRACTS")
    vi_body = _find_part(parts, "REGISTRIES & INTERNAL PIPELINES")
    vii_body = _find_part(parts, "GOVERNANCE & LIFECYCLE")

    spec = MetaSystemSpec(ms_id=ms_id, title=title, source_path=str(p))
    spec.ops = _parse_ops(v_body)
    spec.frozen_semantics = _parse_frozen(v_body)
    spec.pipelines = _parse_pipelines(vi_body)
    spec.lifecycle = _parse_lifecycle(vii_body)
    spec.gates = [Gate(gid=g, text=" ".join(t.split()))
                  for g, t in _GATE_RE.findall(vii_body)]
    return spec


def load_spec(ms_id: str, corpus_root: Path) -> MetaSystemSpec:
    """Resolve and parse MS-N from a corpus root. Raises if unresolved."""
    ds = find_dataset(ms_id, corpus_root)
    if ds is None:
        raise FileNotFoundError(f"dataset for {ms_id} not found under {corpus_root}")
    return parse_dataset(ds)
