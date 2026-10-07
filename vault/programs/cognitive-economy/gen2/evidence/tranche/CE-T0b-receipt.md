# CE-T0b receipt (finished by CE-T0bR, session c68f047f)

Contract: `COMPLETION-PLAN.md` § Master Done-Gate. I kept the partial work from worker 23501b2c (f19838dd), which adds obligation
assessment with a `check` key to `tools/cep_gen2.py`. Every case below was run in this session and is green.

## Obligations declared in `gen2/ledger.json`

`obligations_declared: true`. Each obligation has `terminal: EXECUTE`, `execution: <owner tranche>`, `status: OPEN` and
`check: null`. No other ledger key changed (asserted at write time).

| id | owner tranche | check |
|---|---|---|
| C1 ownership | T9 | OPEN |
| C2 state | T1 | OPEN |
| C3 lifecycle | T1 | OPEN |
| C4 recovery | T1 | OPEN |
| C5 context | T2 | OPEN |
| C6 read | T4 | OPEN |
| C7 transport | T4 | OPEN |
| C8 boundaries | T5 | OPEN |
| C9 agents | T5 | OPEN |
| C10 proof | T6 | OPEN |
| C11 autonomy | T6 | OPEN |
| C12 baseline | T7 | OPEN |
| C13 economics | T9 | OPEN |
| C14 original work | T9 | OPEN |

Every check is OPEN. No existing tool expresses any clause yet, and binding an unrelated command would be a forged pass.
The owning tranche binds each one.

## Tests

- `python tools/test_cep_gen2_obligations.py` printed `OBL_TEST=PASS`, exit 0. Before the ledger change, its only red line
  was `V-OBL-LIVE-LEDGER-assessed`. It now reads `status FAIL, declared=True`.
- The `cep_gen2.selftest` cases test both poles, and all are ok: `all-pass-control` green; `open`, `check-exits-1`,
  `check-tool-missing`, `check-binary-missing`, `check-not-run-is-unknown`, `open-with-check`, `checked-without-argv`,
  `unknown-status` and `recursive-check` red. `--generation 2 --selftest` printed `CEP2_SELFTEST=PASS`.
- Mutation `V-CEP2-MUT-open-obligation-passes` was killed. The test copies cep_gen2.py, rewrites the `# MUT-OPEN` return so
  that OPEN passes, imports the copy and gets a red selftest.

## `python tools/test_cognitive_economy_program.py --generation 2 --final` (exit 1, as required)

```
CEP2_OBLIGATIONS=FAIL
  FAIL W4..W9, R open: no terminal            (7 lines)
  FAIL spend not comparable: spent_measured is dict, boundary is int (UNKNOWN never passes)
  FAIL obligation 'C1' OPEN: no executable check yet (owner T9)
  ... one line per C2..C14, each naming its owner tranche
CEP2_VERDICT=FAIL failures=22
```

## Fix made here

Before this change, `--final` and `--status` crashed with `TypeError: '>' not supported between instances of 'dict' and
'int'` in `check_units`. The cause is that the live `budget_tokens.spent_measured` is `{value, sources, unknown}` and not an
int. The comparison now records a failure instead of raising.

DEBT: this is a type guard, not the right comparison. The T0 spend work (self_spend attribution) should compare
`spent_measured.value` and decide how `unknown` counts. Until then, the spend clause stays red as UNKNOWN.

COMMITS: f19838dd 8455c0b0
