#!/usr/bin/env python3
"""Who already speaks on UserPromptSubmit, discovered from the registration surfaces.

The GSD X plan opened with a name-scoped grep -- "zero occurrences of GSD X in
the repo" -- and read the silence as an empty field. It was not. A posture
ladder was already reaching the model on the exact event the plan wanted, under
a different name, and a grep for the proposal's own vocabulary could never have
found it (PR-COVERAGE-BY-CONSTRUCTION-001: an audit enrolled by hand measures
what someone remembered).

So nothing here is enumerated. The population is read off the two surfaces that
actually decide what runs on this event:

    ~/.claude/settings.json          the harness registration + its timeout
    ~/.claude/hooks/hook-dispatcher  EVENT_MAP (in-process) + CHAIN_MAP (children)

and every member is then read to answer three questions that are cheap, textual,
and jointly decisive:

    EMITS      does it put text in front of the model (additionalContext)?
    VOCAB      does that text carry a classification ladder?
    LITERAL    is the line carrying that ladder a CONSTANT string?

The triple is the finding. A hook emitting a classification vocabulary from a
constant literal is a STATIC MENU: it hands the model a ladder and asks it to
place itself. That is self-assessment, which this estate has already sealed as
not-a-gate (T-PP-SILENT-SKILL-001) -- and it is invisible to any instrument
that only asks "is something registered here?".

WHY NOT "does it read the prompt", which is the obvious discriminator: the
first version of this sweep asked exactly that, and it returned a false
negative on the one hook the sweep exists to find. `power-pack-reminder.js`
contains the word `prompt` (it parses the payload for a session id) while its
emitted text comes from a zero-argument function returning a constant array.
Mentioning the prompt and branching on it are different facts, and only the
second one is about the emission. So the discriminator moved to the emission
itself, where the question is decidable from the line.

WHAT THIS DELIBERATELY DOES NOT CLAIM: that a non-literal vocabulary is
therefore MEASURED. An interpolated string is a candidate for a human to read,
not a verdict. This sweep finds static menus; it does not grade the rest.

Three outcomes, because a sweep that could not run must never look like a sweep
that found nothing (instrument-before-claim):

    0  OK                 population found, no static-menu emitters
    1  FINDINGS           population found, at least one static-menu emitter
    2  INSTRUMENT_FAILED  a surface was unreadable, or the floor was not met

    python tools/gsd_x_ups_sweep.py [--json]
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

EVENT = "UserPromptSubmit"

# Floor. A sweep that silently matched nothing must not report a clean bill, so
# the population has a minimum and a named member that must appear in it. Both
# are assertions about the INSTRUMENT, not about the subject.
MIN_POPULATION = 4
POSITIVE_CONTROL = "power-pack-reminder.js"

# The classification vocabularies this estate actually uses on this event.
# Discovered from the corpus, not invented here: the ExecutionOS Lite tiers and
# the Capability Runtime verdicts. A third vocabulary appearing on this event is
# itself a finding, which is why the miss list is reported rather than dropped.
VOCABULARIES = {
    "executionos-tier": ("LIGHT", "STANDARD", "DEEP", "FORENSIC"),
    "capability-verdict": ("MANDATORY", "RECOMMENDED", "NOT_APPLICABLE"),
}

# How a hook puts text in front of the model.
EMIT_MARKERS = ("additionalContext", "systemMessage")

# How a hook gets at what the user typed. The harness spells it `prompt` in the
# UserPromptSubmit payload; the python side reads the same JSON.
READ_MARKERS = ("prompt", "user_prompt", "userPrompt")


def claude_home() -> Path:
    override = os.environ.get("CLAUDE_HOME")
    if override:
        return Path(override)
    return Path.home() / ".claude"


class InstrumentFailure(Exception):
    """A surface could not be read. Not a finding about the subject."""


@dataclass
class Surface:
    name: str
    path: str
    origin: str          # "settings" | "EVENT_MAP" | "CHAIN_MAP"
    budget_ms: int | None
    exists: bool
    emits: bool = False
    reads_prompt: bool = False          # informational only -- see module docstring
    vocabularies: list[str] = field(default_factory=list)
    vocab_literal: bool = False
    vocab_line: int | None = None

    @property
    def static_menu(self) -> bool:
        """Emits a classification ladder from a constant string literal."""
        return self.emits and bool(self.vocabularies) and self.vocab_literal


def _read(path: Path) -> str:
    # utf-8-sig: Windows tooling emits a BOM and plain utf-8 dies on it.
    return path.read_text(encoding="utf-8-sig", errors="replace")


def registration_timeout(home: Path) -> tuple[int | None, str]:
    """The harness ceiling for the whole chain, in ms, from settings.json."""
    settings = home / "settings.json"
    if not settings.is_file():
        raise InstrumentFailure(f"no settings.json at {settings}")
    try:
        data = json.loads(_read(settings))
    except json.JSONDecodeError as exc:
        raise InstrumentFailure(f"settings.json is not JSON: {exc}") from exc

    entries = (data.get("hooks") or {}).get(EVENT)
    if not entries:
        raise InstrumentFailure(f"settings.json registers nothing on {EVENT}")

    for entry in entries:
        for hook in entry.get("hooks") or []:
            cmd = " ".join([hook.get("command", "")] + list(hook.get("args") or []))
            if "hook-dispatcher" in cmd:
                secs = hook.get("timeout")
                return (int(secs) * 1000 if secs else None, cmd)
    raise InstrumentFailure(f"no hook-dispatcher registration found on {EVENT}")


def _block(source: str, map_name: str, key: str) -> str:
    """Extract one map entry's array body by bracket matching."""
    anchor = re.search(
        rf"const\s+{map_name}\s*=", source
    ) if map_name != "__inline__" else None
    start_from = anchor.end() if anchor else 0
    key_at = source.find(f"'{key}'", start_from)
    if key_at < 0:
        key_at = source.find(f'"{key}"', start_from)
    if key_at < 0:
        return ""
    open_at = source.find("[", key_at)
    if open_at < 0:
        return ""
    depth, i = 0, open_at
    while i < len(source):
        if source[i] == "[":
            depth += 1
        elif source[i] == "]":
            depth -= 1
            if depth == 0:
                return source[open_at : i + 1]
        i += 1
    return ""


def dispatcher_surfaces(home: Path) -> tuple[list[Surface], int | None]:
    """Members of EVENT_MAP[...-default] and CHAIN_MAP[...-chain], plus concurrency."""
    dispatcher = home / "hooks" / "hook-dispatcher.js"
    if not dispatcher.is_file():
        raise InstrumentFailure(f"no hook-dispatcher.js at {dispatcher}")
    src = _read(dispatcher)

    found: list[Surface] = []

    # EVENT_MAP entries are bare relative paths: './power-pack-reminder.js'
    default_block = _block(src, "EVENT_MAP", f"{EVENT}-default")
    for rel in re.findall(r"['\"](\.\.?/[^'\"]+\.(?:js|cjs|py))['\"]", default_block):
        p = (dispatcher.parent / rel).resolve()
        found.append(Surface(Path(rel).name, str(p), "EVENT_MAP", None, p.is_file()))

    # CHAIN_MAP entries are objects carrying script + timeoutMs.
    chain_block = _block(src, "CHAIN_MAP", f"{EVENT}-chain")
    for obj in re.finditer(
        r"script:\s*['\"]([^'\"]+)['\"][^}]*?timeoutMs:\s*(\d+)", chain_block
    ):
        rel, budget = obj.group(1), int(obj.group(2))
        p = (dispatcher.parent / rel).resolve()
        found.append(Surface(Path(rel).name, str(p), "CHAIN_MAP", budget, p.is_file()))

    concurrency = None
    conc_block = _block(src, "__inline__", "CHAIN_CONCURRENCY")
    if not conc_block:
        m = re.search(
            rf"CHAIN_CONCURRENCY\s*=\s*\{{(.*?)\}}", src, re.S
        )
        if m:
            entry = re.search(rf"['\"]{EVENT}-chain['\"]\s*:\s*(\d+)", m.group(1))
            concurrency = int(entry.group(1)) if entry else None
    if not found:
        raise InstrumentFailure(
            f"parsed hook-dispatcher.js but found no {EVENT} members -- "
            "the map shape changed and this parser is now blind"
        )
    return found, concurrency


def inspect(surface: Surface) -> None:
    if not surface.exists:
        return
    try:
        src = _read(Path(surface.path))
    except OSError:
        return
    surface.emits = any(m in src for m in EMIT_MARKERS)
    surface.reads_prompt = any(
        re.search(rf"\b{re.escape(m)}\b", src) for m in READ_MARKERS
    )
    lines = src.splitlines()
    for name, words in VOCABULARIES.items():
        if not all(w in src for w in words):
            continue
        surface.vocabularies.append(name)
        # Locate the line carrying the whole ladder and ask whether it is a
        # constant. A ladder assembled from a variable is at least CAPABLE of
        # depending on the prompt; one written out in full as a literal is not.
        # Interpolation (`${`), format placeholders and `+ identifier`
        # concatenation are the three ways this codebase builds dynamic text.
        for idx, line in enumerate(lines, start=1):
            if not all(w in line for w in words):
                continue
            # Strip every quoted span, then ask whether an IDENTIFIER survives.
            # Testing for `+ name` against the raw line does not work: this very
            # ladder contains the prose "5+ files", which reads as concatenation
            # and made the sweep miss the one hook it exists to find. Outside
            # the quotes there is nothing to misread.
            outside = re.sub(r'"(?:[^"\\]|\\.)*"', "", line)
            outside = re.sub(r"'(?:[^'\\]|\\.)*'", "", outside)
            outside = re.sub(r"`(?:[^`\\]|\\.)*`", "", outside)
            dynamic = (
                "${" in line                                    # template interpolation
                or "%s" in line                                 # printf-style
                or re.search(r"[A-Za-z_$][\w$]*", outside) is not None
            )
            if not dynamic:
                surface.vocab_literal = True
                surface.vocab_line = idx
            break


def main(argv: list[str]) -> int:
    home = claude_home()
    try:
        ceiling_ms, _cmd = registration_timeout(home)
        surfaces, concurrency = dispatcher_surfaces(home)
    except InstrumentFailure as exc:
        print(f"INSTRUMENT_FAILED: {exc}")
        return 2

    for s in surfaces:
        inspect(s)

    names = [s.name for s in surfaces]
    if len(surfaces) < MIN_POPULATION:
        print(
            f"INSTRUMENT_FAILED: found {len(surfaces)} surfaces on {EVENT}, "
            f"floor is {MIN_POPULATION}. A sweep that matched almost nothing "
            "must not report a clean bill."
        )
        return 2
    if POSITIVE_CONTROL not in names:
        print(
            f"INSTRUMENT_FAILED: positive control {POSITIVE_CONTROL!r} absent "
            f"from the discovered population {names}. The parser is blind or "
            "the surface moved; either way this sweep cannot be trusted."
        )
        return 2

    sequential = concurrency in (None, 1)
    budgets = [s.budget_ms for s in surfaces if s.budget_ms]
    worst_ms = sum(budgets) if sequential else max(budgets or [0])
    static = [s for s in surfaces if s.static_menu]
    missing = [s for s in surfaces if not s.exists]

    if "--json" in argv:
        print(json.dumps({
            "event": EVENT,
            "ceiling_ms": ceiling_ms,
            "concurrency": concurrency or 1,
            "sequential": sequential,
            "worst_case_ms": worst_ms,
            "over_ceiling": bool(ceiling_ms and worst_ms > ceiling_ms),
            "surfaces": [asdict(s) for s in surfaces],
            "static_menus": [s.name for s in static],
            "missing_files": [s.name for s in missing],
        }, indent=2))
        return 1 if static else 0

    print(f"# {EVENT} — discovered population\n")
    print(f"registration ceiling : {ceiling_ms} ms")
    print(f"chain concurrency    : {concurrency or 1}"
          f"{'  (DEFAULT — sequential)' if concurrency is None else ''}")
    print(f"worst-case chain cost: {worst_ms} ms"
          f"{'  <-- OVER CEILING' if ceiling_ms and worst_ms > ceiling_ms else ''}")
    print(f"population           : {len(surfaces)}  (floor {MIN_POPULATION}, "
          f"positive control present)\n")

    print(f"| {'hook':34} | {'origin':9} | {'ms':>5} | emits | vocabulary       | literal |")
    print(f"|{'-'*36}|{'-'*11}|{'-'*7}|{'-'*7}|{'-'*18}|{'-'*9}|")
    for s in sorted(surfaces, key=lambda x: (x.origin, x.name)):
        lit = f"L{s.vocab_line}" if s.vocab_literal else ("-" if s.vocabularies else "")
        print(
            f"| {s.name:34} | {s.origin:9} | {str(s.budget_ms or '-'):>5} "
            f"| {'yes' if s.emits else '-':5} "
            f"| {','.join(s.vocabularies) or '-':16} | {lit or '-':7} |"
        )

    if missing:
        print(f"\nREGISTERED BUT ABSENT: {', '.join(s.name for s in missing)}")
        print("  A registration whose file is gone is a dead entry, not a guard.")

    if static:
        print("\n## STATIC MENU — emits a classification ladder from a constant string\n")
        for s in static:
            print(f"  {s.name}:{s.vocab_line}  [{','.join(s.vocabularies)}]")
            print(f"    {s.path}")
        print(
            "\nThis is the finding the plan's name-grep could not see. The model is "
            "handed a ladder and asked to place itself, which is self-assessment "
            "(T-PP-SILENT-SKILL-001), and it already occupies this event."
        )
        return 1

    print(f"\nNo static-menu emitter found on {EVENT}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
