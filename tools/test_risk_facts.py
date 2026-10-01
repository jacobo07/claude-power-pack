#!/usr/bin/env python3
"""V-RISK-* gates for modules/autonomy_gate/risk_facts.py -- both poles of every dimension.

Each dimension is driven by positives AND near-neighbour negatives that share its scary word:
the same verb on a harmless object, the same word negated, quoted or fenced, staging instead of
production. A detector that fires on the word alone fails the negatives; one that never fires
fails the positives.

    python tools/test_risk_facts.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("SDD_OS_PP_ROOT") or Path(__file__).resolve().parents[1])
sys.path.insert(0, str(ROOT))

from modules.autonomy_gate import risk_facts as rf  # noqa: E402

D, P, A, PR, X = (rf.DESTRUCTIVE_DATA, rf.PUBLIC_CONTRACT, rf.AUTH_SECRETS, rf.PRODUCTION,
                  rf.IRREVERSIBLE_EXTERNAL)

# (gate suffix, text, dimension, expected present?)
CASES = [
    ("DESTROY-TABLE", "drop the old table", D, True),
    ("DESTROY-PLURAL", "drop the old tables", D, True),
    ("DESTROY-RECORDS", "delete all records older than 2020 from the orders table", D, True),
    ("DESTROY-ES-TABLA", "borra la tabla de usuarios", D, True),
    ("DESTROY-ES-REGISTROS", "elimina los registros duplicados de la base de datos", D, True),
    ("DESTROY-NEG-NEGATED", "don't drop any tables, just fix the wording", D, False),
    ("DESTROY-NEG-CODE", "delete the unused helper function in utils.py", D, False),
    ("DESTROY-NEG-UI-BUTTON", "add a delete button for users", D, False),
    ("DESTROY-NEG-DROPDOWN", "add a dropdown for users", D, False),
    ("DESTROY-NEG-FENCED", "the test fails with:\n```\nDROP TABLE users;\n```\nwhy?", D, False),
    ("DESTROY-NEG-QUOTED", "the log says \"DROP TABLE users failed: permission denied\", why?", D, False),
    ("DESTROY-NEG-ES-NEGATED", "pero no me estarias eliminando ningun proyecto, no?", D, False),
    ("DESTROY-NEG-ES-HERE", "que podemos borrar de aqui?", D, False),
    ("PUBLIC-SDK", "rename get_user to fetch_user across the public SDK", P, True),
    ("PUBLIC-ES", "renombra el parámetro público de la API v2", P, True),
    ("PUBLIC-BREAKING", "this is a breaking change to the client", P, True),
    ("PUBLIC-ES-INCOMPATIBLE", "es un cambio incompatible", P, True),
    ("PUBLIC-NEG-LOCAL", "rename the local helper _norm to _normalize", P, False),
    ("PUBLIC-NEG-INTERNAL", "refactor the internal api client module", P, False),
    ("PUBLIC-NEG-BUGREPORT", "la API pública de pagos devuelve 500", P, False),
    ("PUBLIC-NEG-ADDITIVE", "add a public API endpoint for invoices", P, False),
    ("AUTH-ROTATE", "rotate the leaked API key", A, True),
    ("AUTH-SCOPES", "change the OAuth scopes for admin users", A, True),
    ("AUTH-ES-PERMISOS", "cambia los permisos de los administradores", A, True),
    ("AUTH-NEG-TOKENS", "how does fixing a typo cost 500k tokens", A, False),
    ("AUTH-NEG-LOGIN-TYPO", "fix the login page typo", A, False),
    ("PROD-DEPLOY", "deploy main to the VPS", PR, True),
    ("PROD-ES-SUBELO", "subelo a produccion", PR, True),
    ("PROD-MIGRATION", "run the migration against production", PR, True),
    ("PROD-ES-PUBLICA", "publica la web", PR, True),
    ("PROD-NEG-STAGING", "deploy the world on the staging server and test it", PR, False),
    ("PROD-NEG-MENTION", "the bug only happens in production, investigate the logs", PR, False),
    ("PROD-NEG-ADJECTIVE", "renombra el parámetro público de la API v2", PR, False),
    ("PROD-NEG-NEGATED", "do not deploy anything yet", PR, False),
    ("EXT-NEWSLETTER", "send the newsletter to all subscribers", X, True),
    ("EXT-CHARGE", "charge the customer's card again", X, True),
    ("EXT-ES-CORREO", "envia el correo a todos los clientes", X, True),
    ("EXT-NEG-BUTTON", "fix the send button style for users", X, False),
    ("EXT-NEG-TEMPLATE", "update the email template typo for users", X, False),
    ("EXT-NEG-BILLING", "update the billing page for customers", X, False),
    # Stem traps: a verb stem also matches a noun (each was a real false fact before verb forms).
    ("AUTH-NEG-QUITE", "it's quite slow on the login page", A, False),
    ("AUTH-NEG-CONFIG-NOUN", "the auth configuration page has a typo", A, False),
    ("PUBLIC-NEG-ALTERNATIVE", "compare the alternative public API clients", P, False),
    ("PROD-NEG-ES-NOUN", "logged-in prod probe of the lanzamiento page", PR, False),
    ("EXT-NEG-ES-NOUN", "las notificaciones de usuarios se ven mal", X, False),
    # Negation scope (code review W2, F3): a negator far back in the clause, or inside "no-op",
    # must not cancel a fact; a curly apostrophe must still negate.
    ("DESTROY-NOOP-IS-NOT-NEGATION", "Remove the no-op handler and drop the users table in production", D, True),
    ("PROD-NOOP-IS-NOT-NEGATION", "Remove the no-op handler and drop the users table in production", PR, True),
    ("DESTROY-FAR-NEGATOR", "There are no tests yet so delete the old records table", D, True),
    ("DESTROY-NEG-CURLY-APOSTROPHE", "don’t drop the users table, just fix the label", D, False),
]

# Pathological whitespace (code review W2, F4): the clause splitter backtracked quadratically,
# 36 s on 40k spaces, on the per-prompt hook path.
TIMING_INPUTS = [("SPACES", "fix it" + " " * 40000), ("TABS", "fix it" + "\t" * 40000),
                 ("CRLF", "fix it" + "\r\n" * 20000)]
TIMING_BUDGET_S = 1.0

passes = fails = 0


def check(name: str, cond: bool, evidence: str) -> None:
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {name}  {evidence}")


def main() -> int:
    for suffix, text, dim, want in CASES:
        a = rf.assess(text)
        got = dim in a.dims
        ev = "; ".join(f"{f.dim}:{f.rule}[{f.match}]" for f in a.facts) or a.state
        check(f"V-RISK-{suffix}", got == want, f"{dim} {'present' if got else 'absent'} -- {ev}")

    # Every dimension must be driven from both poles, or one side is untested.
    for dim in rf.RISK_DIMS:
        poles = {want for _, _, d, want in CASES if d == dim}
        check(f"V-RISK-POLES-{dim.upper()}", poles == {True, False}, f"poles={sorted(poles)}")

    # A prompt that is ONLY reference material is the request itself (missions pasted in a fence);
    # the same fence beside a question stays reference (DESTROY-NEG-FENCED above).
    a = rf.assess("```\n/ultra plan\nMISSION: drop the legacy tables in production\n```")
    check("V-RISK-ALL-REFERENCE-IS-REQUEST", rf.DESTRUCTIVE_DATA in a.dims and rf.PRODUCTION in a.dims,
          f"dims={a.dims}")
    import time
    for label, text in TIMING_INPUTS:
        t0 = time.perf_counter()
        rf.assess(text)
        secs = time.perf_counter() - t0
        check(f"V-RISK-LINEAR-{label}", secs < TIMING_BUDGET_S,
              f"{secs:.3f}s on {len(text)} chars (budget {TIMING_BUDGET_S}s)")

    kept = rf.intent_text('[Pasted text #1 +3399 lines] "Orca X Backlog System 1.md"')
    check("V-RISK-QUOTED-ARTIFACT-KEPT", "backlog system 1.md" in kept, f"intent={kept.strip()!r}")
    dropped = rf.intent_text('continue with this: "Opus 5 (1M) v2.0 code-injection-custom-sports done"')
    check("V-RISK-QUOTED-STATUS-DROPPED", "opus" not in dropped, f"intent={dropped.strip()!r}")
    a = rf.assess("   ")
    check("V-RISK-UNASSESSED-EMPTY", a.state == rf.UNASSESSED,
          f"state={a.state} (nothing to judge is not 'no risk')")
    a = rf.assess("fix the README typo")
    check("V-RISK-NONE-DETECTED", a.state == rf.NONE_DETECTED and not a.facts, f"state={a.state}")

    print(f"RISK_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
