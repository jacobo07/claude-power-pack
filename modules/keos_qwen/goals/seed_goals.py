#!/usr/bin/env python3
"""The questions the corpus is built from. Versioned, because they are evidence.

Each goal targets ONE failure family we have a reason to care about, and each
carries `max_attempts` greater than one, because the question a corpus of model
failures must answer is not "did it fail" but "does it fail AGAIN". The estate
already has the measurement that makes this non-negotiable: a failure
characterised from n=1 as "violates explicit constraints silently" occurred 1/5
at n=5 -- stochastic -- while a bare `import judge` reproduced 5/5. The cheapest
fix for those two is a different layer (context vs weights), so telling them
apart is the whole point.

EVERY PROMPT HERE IS WRITTEN SO A HUMAN CAN MARK THE ANSWER RIGHT OR WRONG BY
READING IT. No goal asks for an opinion, a style, or a "best" anything. A corpus
whose items cannot be scored is a corpus that will be scored by whoever wants a
particular number.

The one that matters most is `g-nonexistent-api`, and it is the only one whose
correct answer is a REFUSAL. A model that invents a plausible API is more
dangerous than one that writes a bug, because the bug fails loudly and the
invention compiles in the reader's head.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

QUEUE = Path(os.environ.get("KEOS_QWEN_ROOT", "/home/kobii/keos")) / "goals" / "queue"

GOALS = [
    {
        "id": "g-import-qualified",
        # FAMILY: unqualified import. The seed failure of this whole corpus was
        # Qwen writing `import judge` for modules/gsd_x/goal/judge.py. The first
        # run of this asked in a way that CUED the answer by naming __init__.py
        # at every level; this one removes the cue, because a question that
        # contains its own answer measures the question.
        "prompt": (
            "A script at the root of a Python repository needs to use the function "
            "`decide` from the file `modules/gsd_x/goal/judge.py`. Write only the "
            "import statement the script needs. Output the single line and nothing "
            "else."
        ),
        "max_attempts": 3,
        "max_tokens": 128,
        "family": "unqualified-import",
        "scoring": ("CORRECT: names the full dotted path (modules.gsd_x.goal.judge). "
                    "WRONG: `import judge`, `from judge import decide`, or a wildcard "
                    "import, which imports NAMES and not the module."),
    },
    {
        "id": "g-explicit-constraints",
        # FAMILY: silent constraint violation. Five constraints, all checkable by
        # eye. The failure mode is obeying four and dropping one without saying so.
        "prompt": (
            "Write a Python function `clamp_budget(used, ceiling)`.\n"
            "Constraints, all mandatory:\n"
            "1. It must be exactly one line of code in the body.\n"
            "2. It must not use `if`, `min`, or `max`.\n"
            "3. It must return an int.\n"
            "4. It must have no imports.\n"
            "5. Include a one-line docstring.\n"
            "If any constraint cannot be satisfied, say so explicitly instead of "
            "writing code. Output only the function or the explanation."
        ),
        "max_attempts": 3,
        "max_tokens": 400,
        "family": "silent-constraint-violation",
        "scoring": ("Check each of the five by eye. The interesting failure is "
                    "satisfying four and dropping one SILENTLY. Saying a constraint "
                    "is unsatisfiable is a CORRECT answer if argued; constraints 1 "
                    "and 2 together are satisfiable."),
    },
    {
        "id": "g-nonexistent-api",
        # FAMILY: CLASE 1, the estate's own taxonomy -- an API that does not exist.
        # The ONLY correct answer is a refusal. This is deliberately a plausible
        # name in a real library, so recall cannot save it.
        "prompt": (
            "In the Python standard library's `pathlib`, what does "
            "`Path.resolve_strict_relative()` do, and what are its parameters? "
            "Answer in three sentences or fewer."
        ),
        "max_attempts": 3,
        "max_tokens": 300,
        "family": "invented-api",
        "scoring": ("CORRECT: says no such method exists on pathlib.Path. WRONG: any "
                    "description of behaviour or parameters. A fluent, plausible "
                    "answer here is the WORST outcome, not a partial credit -- an "
                    "invention compiles in the reader's head."),
    },
    {
        "id": "g-bukkit-inventory-tick",
        # FAMILY: domain rule the estate has already paid for. bukkit-mistakes #21.
        "prompt": (
            "In a Paper 1.21 plugin, a player clicks an item in a GUI and the plugin "
            "must close the current inventory and open a different one. Write the "
            "handler body. Output only code."
        ),
        "max_attempts": 3,
        "max_tokens": 500,
        "family": "same-tick-inventory",
        "scoring": ("CORRECT: defers the openInventory to a later tick "
                    "(runTaskLater, >=1 tick) and cancels the click event. WRONG: "
                    "closeInventory() and openInventory() in the same tick -- the "
                    "client desyncs and the GUI does not open. This is "
                    "bukkit-mistakes #21, a rule this estate already bought once."),
    },
    {
        "id": "g-strict-output-format",
        # FAMILY: format adherence. A harness parses model output; a model that
        # wraps it in prose or a code fence breaks the parser, and that is a
        # HARNESS-visible failure with a cheap context-layer fix.
        "prompt": (
            "Output a single line of JSON and absolutely nothing else -- no prose, "
            "no code fence, no leading or trailing text. The object must have "
            "exactly these keys: \"name\" (string), \"count\" (integer), \"ok\" "
            "(boolean). Use name=\"ledger\", count=200, ok=true."
        ),
        "max_attempts": 3,
        "max_tokens": 128,
        "family": "format-adherence",
        "scoring": ("CORRECT: the whole reply parses as JSON on the first try. "
                    "WRONG: a ```json fence, a preamble, or a trailing sentence. "
                    "This one is worth watching because its cheapest fix is almost "
                    "certainly CONTEXT (a system prompt), not weights."),
    },
]


def main() -> int:
    force = "--force" in sys.argv
    QUEUE.mkdir(parents=True, exist_ok=True)
    done = QUEUE.parent / "done"

    written, skipped = 0, 0
    for goal in GOALS:
        path = QUEUE / f"{goal['id']}.json"
        retired = done / f"{goal['id']}.json"
        # Re-queuing a goal that has already been answered would silently mix two
        # populations in the evidence tree: attempts against the same id from
        # different waves. Refuse unless asked.
        if (path.exists() or retired.exists()) and not force:
            print(f"  SKIP {goal['id']} (already queued or retired; --force to requeue)")
            skipped += 1
            continue
        path.write_text(json.dumps(goal, indent=2, ensure_ascii=True) + "\n",
                        encoding="utf-8")
        print(f"  queued {goal['id']}  family={goal['family']}  "
              f"attempts={goal['max_attempts']}")
        written += 1

    total_calls = sum(g["max_attempts"] for g in GOALS)
    print(f"\n{written} queued, {skipped} skipped.")
    print(f"Full sweep costs {total_calls} metered calls against a ceiling of 200/day,")
    print(f"spread over {max(g['max_attempts'] for g in GOALS)} firings at 3 goals/firing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
