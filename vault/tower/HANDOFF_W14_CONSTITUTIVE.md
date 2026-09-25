# Handoff — constitutive substrate → `kc-diffint-wt` W14 and the goal-spine pane

From: Power Pack pane `pp-cbr-wt`, branch `tower/constitutive-substrate`, 2026-09-25.
To: the executor of `kseip/diff-integrity-v1` (W14 "constitutional ratchet") and the
owner of `kseip/goal-spine-v1` / `feature/goal-spine-v1`. **This is a proposal packet,
not an instruction.** Nothing here edits your trees.

## 1. What now exists (Power Pack, unmerged until the Owner merges it)

| need | use | proof |
|---|---|---|
| promote a rule | `modules.tower.ratchet.promote(family, [entry], reason, authority)` → writes B<n+1>; refuses duplicates, malformed entries, empty reason/authority | 21/21 |
| retire a rule | `ratchet.revert(family, id, reason, authority)` or `tools/family_baseline.py revert <family> <id> --reason R --authority A` | CLI gate |
| prove nobody weakened one | `ratchet.verify_chain(family)` / `family_baseline.py verify` — WITHDRAWN, REVERTED, WEAKENED, CHECK_CHANGED, REWORDED, DUPLICATE_ID, TAMPERED | 6 drills |
| make a rule runnable | `check` grammar: `file:` `glob:` `regex:<path>::<re>` (evaluated, the only kinds that can PASS) · `registry:<verification_registry id>` `test:<path>` (DELEGATED) | 23/23 |
| judge a delivery | `modules.tower.donegate.judge(family, repo_root, registry=…, not_applicable={id: reason})` → per-entry verdict, stamped `judged_under` + SHA-256; REPORT-ONLY | 10/10, severing drill |

A generation is immutable and create-if-absent (a positioned two-writer race used to
erase one). Every change to a rule after promotion needs a reason and an authority —
including making its check *stronger*, because `prose → glob:**` is an unearned green.

## 2. Candidate rules, narrowed (for W14 to decide — scope is yours and the Owner's)

- **C1 — claim above its proven rung is refused.** Reuse the fusion ladder
  (NAME_ONLY→STRUCTURAL→CONSUMER_SUPPORTED→BEHAVIOURAL→RUNTIME, plus SPECIFIED); do
  not invent one. Counterexample that MUST pass: a dormant API honestly claimed at
  SPECIFIED/STRUCTURAL (`KitAccess`/`KitEntitlement` today). Evidence: ONE real
  incident (SkyParty kits). **LuckyArena is not a second one** (§3) — so this is a
  family candidate at most, not universal.
- **C7 merges into C1** (tests ≠ production consumer is the same mechanism).
- **C5 is already constitutive** in `kobiicraft_mode/B0` (`p3-player-experience-required`,
  `blind-testing-protocol`). No new entry; if anything, a runnable `registry:` check —
  but those entries are repo-generic, so no single verifier id fits (see §4).
- **C6 rewording:** the KCOO-0002 gap is the **earn rate (0)**, not `spend()` (exists,
  `bbf53859`). "Purchase-complete needs a live transaction path AND a non-zero earn rate."
- **C3** waits on your W8 provenance model.
- **C2, C4** are KSEIP-differential scope; your W6 (`5a98e972`) already implements C4's
  mechanism — promote from that, don't restate it.
- **Java aperture:** `liveness/callable_reach.py` parses Python only. A C1 check over
  Java plugins needs your W9 detector; `callable_reach` returning nothing on a plugin is
  blindness, not a clean bill.

## 3. Corrections to your MEASURED FACTS

- **`LuckyArenaKits` is NOT "same shape".** Production consumer chain:
  `KitCommand` → `KitSelectorGUI` (default `POR_DEFECTO`, PDC selection,
  `KitMigration`) → `GameSession.java:1000` applies the kit at match start. Use it as
  W9's **negative control** (must not flag) and as W12's **template** for SkyParty's loop.
- **Free SkyParty subset = exactly one kit** (Básico, `POR_DEFECTO`), pinned by
  `SkyPartyKitsTest`.
- **Do not register the census as a live gate.** A registered verifier that calls
  Pterodactyl with a write-capable client key runs on every done-gate and differs per
  checkout (`.env` absent in worktrees). Gate a sealed census artifact (hash + age);
  missing → UNMEASURED.

## 4. Contract offered to goal-spine (not an edit)

`tools/ksis/kseip/goal/obligations.py::standard()` may call `donegate.judge(...)` for the
goal's families and emit one obligation per VIOLATED/UNJUDGED entry, tagged
`source=tower-baseline`, `entry_id`, `judged_under`. The report is advisory; turning any
of it into a blocking obligation is an **Owner decision** (spec §7). Your R4 in-game
obligation and `convergence.py`'s REALITY rule already cover player reachability; the
tower report adds only what those do not judge.

## 5. Spec readings the Owner should confirm

1. **Injection ceiling** (8 entries / 1,400 chars) bounds the prompt, not the
   constitution: every B0 has 15 entries, so "overflow = compiler failure" would leave
   S4 unable to inject for any family. Implemented: deterministic selection, nothing
   lost, deferred entries named, done-gate judges all.
2. **`class` C|D is undefined** in the spec (9 of 60 entries are C). Not used anywhere.
3. **The 31 prose checks stay prose.** They are repo-generic ("grep for callers…",
   `<real-domain>`); a family entry cannot name one repo's path, and converting them
   would be invention. The done-gate reports them UNJUDGED — honest, and visible.
