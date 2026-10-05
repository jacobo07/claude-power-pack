# E1 -- predeclared addendum for the [B] resident-rule ablation (2026-10-05, before any counted run)

Pillar [B]. Packet: `vault/programs/cognitive-economy/post-reset-packet.json` (13 candidate rule files, 56,861 B,
LF sha256 pinned). Owner: "Approve, E1 after reset", then "do the 17M tokens thing now by the way, but on GEX44",
with four preflight gates (2026-10-05). This file is committed before any counted run. A result cannot change
it; a change needs a new dated addendum and voids the runs made under this one.

## Preflight gates

| gate | rule | status |
|---|---|---|
| 1 mechanical saving | B's exclusion must cut the billed first-call context, measured on the host that runs E1 | PASS `8b5e1602`: laptop -19,051, GEX44 -19,038 tokens/call, 13/13 pins |
| 2 break-even | expected spend / measured delta, against real call volume | PASS: 17M / 19,038 = ~890 calls; 83M ceiling = ~4,400; D-W7 = 75,969 calls/week |
| 3 can change the decision | every rule has its own judgement task, so each pair decides one rule | holds by the task bank below |
| 4 sequential, bounded | this stopping contract; 17M is the first cap, 83M the ceiling, neither a target | holds by this file |

## Design

- Host GEX44, CLI `/home/kobii/.local/bin/claude` 2.1.289, model `claude-opus-5-5`. Arm A = the host prefix with all
  13 resident. Arm B = A + `claudeMdExcludes` over the 13 files. Gate 1 is the positive control: if the first
  counted pair's B first-call context is not at least 15,000 tokens below A's, STOP. The arms did not differ.
- Task bank: one judgement task per rule. Each task is a stub module with a docstring stating the caller and what
  the result drives, the prompt "implement them", and a hidden grader copied in only after the session. This is
  the shape of ADDENDUM-J / ADDENDUM-R2. Two rules are NOT re-run: technical-failure-to-product-state and
  scoped-side-effect-authority were already decided as relocation candidates by R2
  (`.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/REPORT.md` R2: 2 tasks x n=2 each, every
  run passed in both arms, 24/24 valid). E1 adds no evidence for them that R2 lacks, so they enter the result
  through R2. New tasks: one for each of the other 11 rules, so at most 11 pairs = 22 counted runs (~15M context
  at R2's measured ~0.70M per run). Before freezing, every task must pass validation with no model calls: its
  selftest is OK, and a naive solution fails ONLY its judgement checks.
- The bank is frozen by the commit that adds it, together with a `validate` log. A task file edited after that
  commit voids its runs.

## Stopping contract (fixed now)

1. Order: tasks run in descending order of their rule's bytes, so the largest rent is decided first if a stop
   comes early. Within a pair, arm order alternates task by task.
2. One matched pair (A, B) per task. No planned replicates. Maximum 11 pairs = 22 counted runs.
3. A run is valid when its precondition is red, the session ran, and the grade ran. An invalid run is rerun once.
   A second invalid run makes that task "no information".
4. Per-rule decision, final the moment its pair is valid:
   - A passes, B passes: the rule becomes a relocation candidate.
   - A passes, B fails: the rule STAYS resident. Under group exclusion the loss may belong to another excluded
     rule; it is still charged to this task's rule, which errs toward keeping.
   - A fails: no information; the rule STAYS.
   - B passes where A fails: reported, never used.
   Tokens never break a tie.
5. Early harm stop: if B loses in 4 or more of the first 8 valid pairs, stop. The group exclusion degrades
   broadly; all 13 stay and the result is reported as a falsification of the group move.
6. Spend stop: stop when the counted runs' summed context reaches 17,000,000 tokens (the first cap). Going past it,
   toward the 83,000,000 ceiling, needs a new Owner yes. Rules whose pairs did not run stay resident.
7. No further run on a rule once it is decided. No peeking rule exists because no decision is revised by later
   pairs.

## After the runs

- Relocation candidates move as in the earlier moves (rule -> skill + one-line pointer). That is a change to
  `~/.claude/rules`, a global config write, and it needs the Owner's yes on the exact list (HR-001).
- Instead of re-running every task after the move, a one-call gate-1 probe on the moved state confirms the billed
  floor fell by the relocated rules' share. Any relocated rule whose task later regresses in real use reopens.
- A ceiling (every pair passes) is reported as "no loss observed at n=1 per rule", never as "no effect".

## Known limits, stated before the numbers

- n = 1 pair per rule detects gross losses only. R1 and R2 both hit ceilings.
- One host, one model, one CLI version, this repository. GEX44's prefix is ~16.5k tokens smaller than the
  laptop's (fewer hooks). The rule bodies and the measured delta are the same on both hosts.
- Logical transcript tokens only. The account meter's weighting is unknown and is not derived from these numbers.
- Prior: R1 and R2 judged 6 rules with 0 losses in 56 counted runs. A ceiling is the likely outcome. Gate 3 still
  holds, because without E1 the status quo is to keep all 11 resident; E1 is what can move them. But the
  experiment buys "no gross loss observed", not proof of zero effect.
