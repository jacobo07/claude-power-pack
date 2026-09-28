"""Delegated-work contract (assimilation item 21, genesis-prompt-kit -> EXTEND).

A prompt handed to a subagent or a batch worker is a contract, and the estate learned its missing
clauses the expensive way: an agent told to REPORT instead of WRITE lost 2h31m of work on restart
(agent-solo-guard rule J), and a read-only agent was handed a mandatory write it could not make.
This renders the contract through the vendored prompt kit -- its exact key set and bounds are the
validator, reached through the one bridge, never copied -- and adds the two CPP clauses the kit
does not have, inside the kit's own fields so its key set stays exact:

    write ownership   constraints: "Write only: <paths>" (or "Writes nothing" for a read-only role)
    durable output    outputs: <path>; constraints: "Write findings to <path> as you go, appending
                      each confirmed fact before moving on" -- the clause agent-solo-guard requires

    python tools/task_contract.py --spec contract.json      -> rendered text, exit 0
exit 3 the kit refused the contract (errors printed) · 2 the bridge could not answer
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.external_assimilation import node_bridge as nb  # noqa: E402

RENDERED, REFUSED, UNJUDGED = "RENDERED", "REFUSED", "UNJUDGED"


@dataclass
class Rendered:
    outcome: str
    text: str = ""
    errors: list = field(default_factory=list)
    contract: dict = field(default_factory=dict)


def build(*, id: str, objective: str, owner: str, acceptance: list[str], stop: str,  # noqa: A002
          writes: list[str] | None, durable_output: str | None = None, inputs: list[str] = (),
          dependencies: list[str] = (), constraints: list[str] = (), attempts: int = 1,
          deadline_s: float = 600, max_output_bytes: int = 65_536) -> dict:
    """The kit's exact key set, with CPP's write-ownership and durable-output clauses folded in.

    `writes=None` is refused rather than defaulted: an unstated write scope is the thing this
    contract exists to make explicit. `writes=[]` states a read-only role."""
    if writes is None:
        raise ValueError("writes must be stated: a list of paths, or [] for a read-only role")
    cons = list(constraints)
    cons.append(f"Write only: {', '.join(writes)}" if writes else "Writes nothing: read-only role")
    outs = []
    if durable_output:
        if not writes or durable_output not in writes:
            # A mandatory output assigned to a context that may not write it (agent-solo-guard's
            # contract preflight, 2026-09-22). Refuse at build time, not at dispatch time.
            raise ValueError(f"durable_output {durable_output} is not among the paths this role may write")
        outs.append(durable_output)
        cons.append(f"Write findings to {durable_output} as you go, appending each confirmed fact "
                    f"before moving on, so a timeout costs the tail and never the whole")
    outs += [w for w in writes if w != durable_output]
    return {"id": id, "objective": objective, "owner": owner, "inputs": list(inputs), "outputs": outs,
            "dependencies": list(dependencies), "constraints": cons, "acceptance": list(acceptance),
            "budget": {"maxAttempts": int(attempts), "deadlineMs": int(deadline_s * 1000),
                       "maxOutputBytes": int(max_output_bytes)},
            "stopCondition": stop}


def render(contract: dict, timeout: float = 30.0) -> Rendered:
    """Validate and render with the kit. REFUSED carries the kit's own errors; UNJUDGED means the
    kit could not be asked, and a caller must not dispatch an unvalidated contract as if it passed."""
    v = nb.call("prompts", "validateTaskContract", [contract], timeout=timeout)
    if not v.ok:
        return Rendered(UNJUDGED, errors=[f"bridge {v.outcome}: {v.error}"], contract=contract)
    if not (v.value or {}).get("ok"):
        return Rendered(REFUSED, errors=list((v.value or {}).get("errors") or []), contract=contract)
    r = nb.call("prompts", "renderTaskContract", [contract], timeout=timeout)
    if not r.ok or not isinstance(r.value, str) or not r.value.strip():
        return Rendered(UNJUDGED, errors=[f"render {r.outcome}: {r.error or 'empty text'}"], contract=contract)
    return Rendered(RENDERED, text=r.value, contract=contract)


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, help="JSON: the keyword arguments of build()")
    a = ap.parse_args(argv)
    try:
        contract = build(**json.loads(Path(a.spec).read_text(encoding="utf-8-sig")))
    except (OSError, ValueError, TypeError) as exc:
        print(f"REFUSED: {exc}")
        return 3
    res = render(contract)
    if res.outcome == RENDERED:
        print(res.text)
        return 0
    print(f"{res.outcome}: " + "; ".join(res.errors))
    return 3 if res.outcome == REFUSED else 2


if __name__ == "__main__":
    sys.exit(main())
