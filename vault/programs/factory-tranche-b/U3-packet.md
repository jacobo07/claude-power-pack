# Unit U3 — W4 pricing source (LOW-2) + credential filter digit-prefix residual (U1 review LOW-1)

Repo: C:\Users\User\.claude\skills\claude-power-pack (a git worktree on its own branch; the path is rewritten below).
Use PowerShell; git is `& 'C:\Program Files\Git\cmd\git.exe'` (not on PATH). Python is
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.

## Background
- LOW-2 (W3 review): `tools/w4_benchmark.py` line 10 hardcodes `vault/pricing/anthropic_2026-10.json` (and repeats it
  in its report text ~167). The estate resolves pricing through `tools/pricing_source.py` (see how
  `tools/usage_index.py` uses `current_pricing_path`). A hardcoded file goes stale silently on the next refetch.
- U1 review LOW-1: the packet-builder CREDENTIAL regex (vendor/genesis-suite/modules/genesis-source-packets/index.cjs
  line 21, identical copies in genesis-task-context/lib and genesis-batch-drafts/lib) now carries the lookahead
  `(?!\s*["']?(?:\$?\{|\d+\s*[,}/]\d*))` after `[:=]`. It admits any value that STARTS with digits then `,` `}` or `/`,
  e.g. `password=42,hunter2` or a base64 key starting `7/Qx...`. The accepted residual is numeric-only values
  (`password: 123,`); the wider admission is not accepted. The trailing `\d*` is dead.

## Task
1. LOW-2: make w4_benchmark resolve pricing through pricing_source (path in the report text must be the resolved
   path, not a literal). If no current pricing file resolves, fail loudly (non-zero), never price at 0.
   `python tools/test_w4_benchmark.py` must stay green; add one check that the resolved path is used.
2. Credential regex: narrow the numeric branch so it admits only a value that is wholly digits (digits, optional
   spaces, then `,` `}` `/` or end of line, with nothing secret-like after it on that value). Apply the same
   byte-identical line to all three copies. In `tools/test_credential_filter_fp.py` add, each in its own fixture
   file (built at runtime, no key-shaped literal in the test): `password=42,hunter2` -> BLOCKED,
   `token=7/Qx9AbCdEfGhIjKlMn` -> BLOCKED, and keep `"budget": 100,` style controls ADMITTED (the three existing
   controls must stay ADMITTED). Update the `FIX` constant to the new lookahead. Show the new BLOCKED checks fail on
   the current regex before your change.
3. Update the existing `governance/KNOWN_FALSE_POSITIVES.md` U1 entry's residual line; do not add a second entry.
4. Never edit any hook, CLAUDE.md, agent catalog or MEMORY.md.

## Done
- `python tools/test_w4_benchmark.py`, `python tools/test_credential_filter_fp.py`,
  `python tools/test_floor_regression_gate.py` exit 0; `node --test` on each of the three copies'
  `test/index.test.cjs` exits 0.
- Commit with a pathspec (only files you changed): `git commit -m "<msg>" -- <files>`.
- Receipt `vault/programs/factory-tranche-b/U3-receipt.md`: what you changed, red output before, test output lines,
  and `COMMITS: <hash>` reachable from HEAD.
