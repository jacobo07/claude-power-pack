# Pillars J and M -- consumed owners not on this line of history (R2): evidence

Plane: GEX44 `kobicraft-gex44` (Linux 6.8, user `kobii`), `python3` 3.12.3, branch `mission/incremental-cognition-run`,
worktree `/home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run`, HEAD
`4315379f15b3a5b06dfac13a8faceefc793e4b2f`. Measured 2026-10-04, foreground, from the worktree root. Nothing here was run
on the laptop. No `claude` session was started and no file under `~/.claude` was written.

Pillars J and M are NOT closed by this file. Each closes only by R2: `owner_ledger` evidence read from the owner's ledger
at a commit reachable from HEAD, and no such commit exists on this line of history (see `## Measured on this host`).

## Frozen rules (verbatim from ledger.json frozen.pillars)

Pillar J ("context lifetime, rollover, zero-transcript start, context images"):

> consume CE D, E, I; the Ralph fresh worker with an 8 KB card is the zero-transcript path

Predicted terminal: `MERGED_INTO_EXISTING_OWNER`. Owner of the rule: `vault/programs/cognitive-economy/ledger.json` (the CE
ledger; read here, never edited).

## R2 inputs

R2 (`tools/test_incremental_cognition_program.py`, check `check_consumed`): this is a delta program; a pillar that closes
by consuming a CE / SC pillar (`ledger.frozen.consumes`) must cite, for each consumed pillar, an `owner_ledger` evidence
`{ref: <owner ledger path>, commit, pillar, terminal}`. The owner ledger is read AT that commit with git (the commit must
be reachable from HEAD, so the owner's work has to be on this line of history) and must show that pillar in that
terminal. A handoff file alone cannot close a consuming pillar. `--pillar X` checks only X's consumed owners (since plan
06-01); `--final` checks every consuming pillar. The inputs below are read from `frozen.consumes` of
`vault/programs/incremental-cognition/ledger.json` and from the CE ledger's `frozen.pillars` at HEAD, not from a list kept
here.

| consuming pillar | owner ledger | owner pillar | owner pillar name | owner's pre-registered prediction | terminal at HEAD |
|---|---|---|---|---|---|
| J | vault/programs/cognitive-economy/ledger.json | D | context lifetime / dead context | MERGED_INTO_EXISTING_OWNER | none |
| J | vault/programs/cognitive-economy/ledger.json | E | fresh-epoch economics | MERGED_INTO_EXISTING_OWNER | none |
| J | vault/programs/cognitive-economy/ledger.json | I | one-shot work packet | MERGED_INTO_EXISTING_OWNER | none |

The closing shape of `state.J` that J's frozen prediction needs (from the printer's `NEEDS` lines, which derive from
`ce.REQUIRED_KINDS`):

- terminal `MERGED_INTO_EXISTING_OWNER`, with a reason;
- `owner` evidence: one of `vault/programs/cognitive-economy/ledger.json`;
- `handoff` evidence: `vault/programs/incremental-cognition/handoffs/J.md` naming `[J]` and one owner, committed after
  the freeze;
- one `owner_ledger` row per consumed pillar (D, E, I), exactly as `python3 tools/ic_r2_evidence.py --pillar J --commit
  <commit>` prints them once every one of the three has a terminal at a commit reachable from HEAD.

## Measured on this host

Every command ran foreground from the worktree root; each output is quoted verbatim with its exit code.

`python3 tools/ic_r2_evidence.py --pillar J --commit HEAD`

```
OPEN vault/programs/cognitive-economy/ledger.json#D at 4315379f: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#E at 4315379f: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#I at 4315379f: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
ICR2_READY=NO pillar=J commit=4315379f15b3a5b06dfac13a8faceefc793e4b2f open=['D', 'E', 'I']
```

exit 1.

`python3 tools/ic_r2_evidence.py --pillar J --commit fa9ae2ed` (the CE P0 freeze, which holds the CE ledger with every
pillar open)

```
OPEN vault/programs/cognitive-economy/ledger.json#D at fa9ae2ed: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#E at fa9ae2ed: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#I at fa9ae2ed: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
ICR2_READY=NO pillar=J commit=fa9ae2edb894ec05b739e17e1ec83cfc44dfdc55 open=['D', 'E', 'I']
```

exit 1.

`git cat-file -t 21671d6c` (the CE phase-1 commit the program plan names)

```
fatal: Not a valid object name 21671d6c
```

exit 128: that commit is not in this clone.

`git merge-base --is-ancestor origin/mission/skill-capability HEAD` -> exit 0 (the SC branch tip
`287b360acbe6fb3cc8492063c02270fbcbe5244f` is an ancestor of HEAD, so what it carries is already on this line of
history). `origin/feature/knowledge-acquisition` is `339ccaa91ee040e81e6171ea27e855b1f108aed0`.

The owner-ledger scan, script `/tmp/ic-p6-02-terminals.py` (quoted verbatim; `ABSENT` when `git show` fails):

```python
import json, subprocess
REFS = ["HEAD", "origin/mission/skill-capability", "origin/feature/knowledge-acquisition"]
PATHS = ["vault/programs/cognitive-economy/ledger.json", "vault/programs/skill-capability/ledger.json"]
for ref in REFS:
    for path in PATHS:
        r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            print(f"{ref}:{path} ABSENT")
            continue
        led = json.loads(r.stdout.lstrip("﻿"))
        st = led.get("state", {})
        closed = sorted(p for p, v in st.items() if isinstance(v, dict) and v.get("terminal"))
        print(f"{ref}:{path} pillars={len(st)} with_terminal={closed}")
```

```
HEAD:vault/programs/cognitive-economy/ledger.json pillars=20 with_terminal=[]
HEAD:vault/programs/skill-capability/ledger.json pillars=14 with_terminal=[]
origin/mission/skill-capability:vault/programs/cognitive-economy/ledger.json pillars=20 with_terminal=[]
origin/mission/skill-capability:vault/programs/skill-capability/ledger.json pillars=14 with_terminal=[]
origin/feature/knowledge-acquisition:vault/programs/cognitive-economy/ledger.json ABSENT
origin/feature/knowledge-acquisition:vault/programs/skill-capability/ledger.json ABSENT
```

`python3 tools/test_incremental_cognition_program.py --pillar J`

```
  FAIL L3 J: no terminal disposition
CEP_PILLAR_J=FAIL
ICP_PILLAR_J=FAIL
```

exit 1: J is open (L3), as it must be.

## Why this is external

R2 needs the CE ledger commit that gives D, E and I their terminals on a commit reachable from HEAD. The CE and SC
missions run on the laptop; the ROADMAP's Phase 6 reads "Depends on: CE and SC landing their ledger commits on this line
of history". The program plan (`vault/plans/incremental-cognition-program-2026-10-03.md`, drafting note) says: "CE ledger
on its branch: A IMPLEMENTED; D, E, I, N, O, Q MERGED (measured); K measured "no class >= 3 %" (wip)." That is a
laptop-side statement made when the plan was drafted; it was NOT measured on this host and is not evidence here. What this
host measures is the block above: neither ledger carries a terminal at HEAD or at the one SC branch tip that is an
ancestor of HEAD, and no CE ledger exists on `origin/feature/knowledge-acquisition`.

## What closes it

The `[J]` item of `vault/programs/incremental-cognition/owner-bundle.md` (section `## Phase 6 -- consumed owners (R2) and
closeout`; summary row 29). After CE lands D, E and I on a commit reachable from `mission/incremental-cognition-run`
(merged into this line of history, never rebased or squashed, because R2 cites that commit's sha): run
`python3 tools/ic_r2_evidence.py --pillar J --commit HEAD`; when it prints `ICR2_READY=J`, add the printed rows as
`owner_ledger` evidence to `state.J` with the owner and handoff evidence its `NEEDS` lines name; then run `python3
tools/test_incremental_cognition_program.py --pillar J`.

## Status: OPEN

Ledger `state.J` is not written (`{}`), `handoffs/J.md` does not exist, IC-J is not ticked, and `python3
tools/test_incremental_cognition_program.py --pillar J` still reports `FAIL L3 J: no terminal disposition`. Pillar J
closes only through the `[J]` item, after the owner commit is reachable and the rows are added.
