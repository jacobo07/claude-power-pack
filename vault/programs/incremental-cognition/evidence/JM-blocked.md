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

Pillar M ("optimizer, experiment compilation, negative capital, routing, events, reality model"):

> dispositions only: CE Q/N/O/M and the pre-registration pattern of this verifier already own them; an unrestricted optimizer is rejected

Predicted terminal: `MERGED_INTO_EXISTING_OWNER`. Owners of the rule: `vault/programs/cognitive-economy/ledger.json` and
`tools/baseline_ledger.py` (both read here, never edited). This program does NOT build an optimizer: the frozen rule
rejects an unrestricted one, and M closes by disposition to the owners that already hold the work.

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
| M | vault/programs/cognitive-economy/ledger.json | Q | technical capital accounting | MERGED_INTO_EXISTING_OWNER | none |
| M | vault/programs/cognitive-economy/ledger.json | N | event-driven cognition | MERGED_INTO_EXISTING_OWNER | none |
| M | vault/programs/cognitive-economy/ledger.json | O | cognitive IR / state normalization | MERGED_INTO_EXISTING_OWNER | none |
| M | vault/programs/cognitive-economy/ledger.json | M | model / processor allocation | DEFERRED_STRONGER_OWNER | none |

CE pillar M's own prediction is `DEFERRED_STRONGER_OWNER`, not `MERGED_INTO_EXISTING_OWNER`. R2 cites whatever terminal
CE M ends at: the printer prints the terminal it reads from the owner ledger, and R2 compares the cited terminal to that
one, so a CE M that lands `DEFERRED_STRONGER_OWNER` is cited as `DEFERRED_STRONGER_OWNER`.

The closing shape of `state.J` and of `state.M` that their frozen predictions need (from the printer's `NEEDS` lines,
which derive from `ce.REQUIRED_KINDS`; `python3 /tmp/ic-p6-02-needs.py J M` printed them):

```
NEEDS J MERGED_INTO_EXISTING_OWNER: owner (one of vault/programs/cognitive-economy/ledger.json)
NEEDS J MERGED_INTO_EXISTING_OWNER: handoff (vault/programs/incremental-cognition/handoffs/J.md naming [J] and one owner, committed after the freeze)
NEEDS M MERGED_INTO_EXISTING_OWNER: owner (one of vault/programs/cognitive-economy/ledger.json, tools/baseline_ledger.py)
NEEDS M MERGED_INTO_EXISTING_OWNER: handoff (vault/programs/incremental-cognition/handoffs/M.md naming [M] and one owner, committed after the freeze)
```

- terminal `MERGED_INTO_EXISTING_OWNER`, with a reason;
- `owner` evidence: for J one of `vault/programs/cognitive-economy/ledger.json`; for M one of that file and
  `tools/baseline_ledger.py`;
- `handoff` evidence: `vault/programs/incremental-cognition/handoffs/J.md` (M: `handoffs/M.md`) naming `[J]` (`[M]`) and
  one owner, committed after the freeze;
- one `owner_ledger` row per consumed pillar (J: D, E, I; M: Q, N, O, M), exactly as `python3 tools/ic_r2_evidence.py
  --pillar <P> --commit <commit>` prints them once every consumed pillar has a terminal at a commit reachable from HEAD.

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

`python3 tools/ic_r2_evidence.py --pillar M --commit HEAD`

```
OPEN vault/programs/cognitive-economy/ledger.json#Q at 4315379f: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#N at 4315379f: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#O at 4315379f: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#M at 4315379f: no terminal (owner predicted DEFERRED_STRONGER_OWNER)
ICR2_READY=NO pillar=M commit=4315379f15b3a5b06dfac13a8faceefc793e4b2f open=['Q', 'N', 'O', 'M']
```

exit 1 (HEAD was `4315379f` when this was measured).

`python3 tools/ic_r2_evidence.py --pillar M --commit fa9ae2ed`

```
OPEN vault/programs/cognitive-economy/ledger.json#Q at fa9ae2ed: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#N at fa9ae2ed: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#O at fa9ae2ed: no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)
OPEN vault/programs/cognitive-economy/ledger.json#M at fa9ae2ed: no terminal (owner predicted DEFERRED_STRONGER_OWNER)
ICR2_READY=NO pillar=M commit=fa9ae2edb894ec05b739e17e1ec83cfc44dfdc55 open=['Q', 'N', 'O', 'M']
```

exit 1.

`python3 tools/test_incremental_cognition_program.py --pillar M`

```
  FAIL L3 M: no terminal disposition
CEP_PILLAR_M=FAIL
ICP_PILLAR_M=FAIL
```

exit 1: M is open (L3), as it must be. The owner-ledger scan above covers M's inputs too (the CE ledger has no terminal on
any of its 20 pillars at HEAD and at `origin/mission/skill-capability`).

## Why this is external

R2 needs the CE ledger commit that gives D, E and I (for J) and Q, N, O and M (for M) their terminals on a commit
reachable from HEAD. The CE and SC
missions run on the laptop; the ROADMAP's Phase 6 reads "Depends on: CE and SC landing their ledger commits on this line
of history". The program plan (`vault/plans/incremental-cognition-program-2026-10-03.md`, drafting note) says: "CE ledger
on its branch: A IMPLEMENTED; D, E, I, N, O, Q MERGED (measured); K measured "no class >= 3 %" (wip)." That is a
laptop-side statement made when the plan was drafted; it was NOT measured on this host and is not evidence here. What this
host measures is the block above: neither ledger carries a terminal at HEAD or at the one SC branch tip that is an
ancestor of HEAD, and no CE ledger exists on `origin/feature/knowledge-acquisition`.

## What closes it

The `[J]` and `[M]` items of `vault/programs/incremental-cognition/owner-bundle.md` (section `## Phase 6 -- consumed
owners (R2) and closeout`; summary rows 29 and 30). After CE lands D, E and I (J) and Q, N, O and M (M) on a commit
reachable from `mission/incremental-cognition-run` (merged into this line of history, never rebased or squashed, because
R2 cites that commit's sha): run `python3 tools/ic_r2_evidence.py --pillar <P> --commit HEAD`; when it prints
`ICR2_READY=<P>`, add the printed rows as `owner_ledger` evidence to `state.<P>` with the owner and handoff evidence its
`NEEDS` lines name; then run `python3 tools/test_incremental_cognition_program.py --pillar <P>`.

## The same printer for H and I

H and I also consume owner pillars and share the blocker. Their pairs are read from `frozen.consumes`: H consumes CE P
and G; I consumes CE B and SC B. The printer takes either pillar; measured one command at a time, at `4315379f`:

`python3 tools/ic_r2_evidence.py --pillar H --commit 4315379f`

```
OPEN vault/programs/cognitive-economy/ledger.json#P at 4315379f: no terminal (owner predicted FALSIFIED_OR_REJECTED_BY_EVIDENCE)
OPEN vault/programs/cognitive-economy/ledger.json#G at 4315379f: no terminal (owner predicted FALSIFIED_OR_REJECTED_BY_EVIDENCE)
ICR2_READY=NO pillar=H commit=4315379f15b3a5b06dfac13a8faceefc793e4b2f open=['P', 'G']
```

exit 1.

`python3 tools/ic_r2_evidence.py --pillar I --commit 4315379f`

```
OPEN vault/programs/cognitive-economy/ledger.json#B at 4315379f: no terminal (owner predicted AUTHORIZATION_BOUND)
OPEN vault/programs/skill-capability/ledger.json#B at 4315379f: no terminal (owner predicted FALSIFIED_OR_REJECTED_BY_EVIDENCE)
ICR2_READY=NO pillar=I commit=4315379f15b3a5b06dfac13a8faceefc793e4b2f open=['B', 'B']
```

exit 1.

The `[H]` and `[I]` items of phase 3 in the owner bundle already state their R2 need (CE P and G terminals for H; CE B
and SC B terminals for I). No bundle line is added for them here: their pillars close through their own measurement
files first, and plan 06-02's scope is J and M.

## Product Delta

One command now prints, for any consuming pillar, the exact `owner_ledger` rows R2 accepts (full 40-hex commit, the
terminal read from the owner ledger at that commit) or names the owner pillars still open, and prints nothing pasteable
while any is open. The per-pillar done-gate (`--pillar <P>`) checks R2 since plan 06-01. The Owner holds two runnable
bundle items, `[J]` and `[M]`, each with the two commands and what closes it. Pillars J and M themselves are unchanged:
open.

## Intelligence Delta

Measured facts only, each with its command:

- No owner terminal exists on this history: `python3 /tmp/ic-p6-02-terminals.py` printed `with_terminal=[]` for both
  ledgers at HEAD and at `origin/mission/skill-capability`.
- CE's phase-1 commit is absent: `git cat-file -t 21671d6c` -> `fatal: Not a valid object name 21671d6c`, exit 128.
- The SC branch is an ancestor of HEAD and carries no terminal: `git merge-base --is-ancestor origin/mission/skill-capability
  HEAD` exit 0, plus the scan above.
- Before plan 06-01, `--pillar X` did not run R2, and the CE clause L4 accepts any `owner_ledger` row without reading it
  (06-01-SUMMARY.md: a J terminal with a misquoted owner terminal printed `ICP_PILLAR_J=PASS`; fixed by `check_consumed(...,
  only=[pid])`, proven by `python3 tools/test_incremental_cognition_program.py --selftest`, `V-ICP-R2-PILLAR-MODE`).

## Named debts

- J and M close only after CE lands its terminals on a commit reachable from this branch; that is external to this
  program (the CE and SC missions run on the laptop).
- H and I share the blocker (above) and are not given bundle items by this plan.
- The program plan's note "CE ledger on its branch: A IMPLEMENTED; D, E, I, N, O, Q MERGED (measured)" is unverified
  here: it is a laptop-side statement, and no CE ledger carrying a terminal is reachable from this host.
- The printer reads the owner ledger at one commit and does not judge whether that commit is CE's own work: a branch
  tip that carries terminals but was never CE's closing commit would print rows. Choosing the commit is the Owner's step.
- The bundle commands are proven to parse with the printer's own parser and to run on GEX44; none has produced
  `ICR2_READY=<P>` on a real closed owner, because none exists.

## Status: OPEN

Ledger `state.J` and `state.M` are not written (`{}`), `handoffs/J.md` and `handoffs/M.md` do not exist, IC-J and IC-M are
not ticked, and `python3 tools/test_incremental_cognition_program.py --pillar J` and `--pillar M` still report `FAIL L3
<P>: no terminal disposition`. Pillars J and M close only through the `[J]` and `[M]` items, after the owner commit is
reachable and the rows are added.
