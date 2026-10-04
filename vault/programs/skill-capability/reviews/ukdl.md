# Skill-capability program: UKDL candidates (closeout, CE clause L8)

These are the UKDL candidates this program learned during its run, offered to the Owner. The program never writes
`vault/knowledge_base/ukdl-universal.md`: that file is read-only here (09-CONTEXT D-01 and the ROADMAP operating
constraints), so adopting any entry into the shared UKDL is the Owner's call. Each entry names the trap as it was
measured, the rule that prevents it, the files where it was found, and the pillar it came from. Host for every figure:
gex44.

## UKDL-SC-01: git options placed after `--` are read as pathspecs
- Trap: the card hook built `git diff HEAD -- <paths> -U0 --no-color --no-ext-diff`. After `--`, git took the three options as pathspecs. With `color.diff=always` set, the output carried ANSI codes and 3 context lines, the parser matched no `diff --git` line, and the card silently reported `no_opportunity`. The test probe copied the same argv order, so it could not see the defect.
- Rule: put every option before the revision and before `--`; after `--` only paths may follow. Drill the argv under a hostile config (forced colour, an external diff driver) and require the parser to still find the file.
- Source: `.planning/workstreams/skill-capability/phases/01-card-precision/01-REVIEW.md:62` `hooks/doctrine_cards.js`
- Pillar: [A]

## UKDL-SC-02: a verdict must depend on every provenance clause it prints beside
- Trap: `verdict_of` read only the token and cap clauses. With a challenger row edited by +5 tokens, DENOM-MATCH failed and the verdict still printed FALSIFIED, and `--json` exited 0. In phase 3 the provenance clauses (PINNED, SELECTION, DCARD-MATCH) were never driven red: each could be deleted and the suite stayed 36/36.
- Rule: a terminal verdict is computed from all of its clauses, and a clause that is not ok demotes it to INCONCLUSIVE. Every provenance clause gets a mutant that turns it red while the verdict changes with it.
- Source: `.planning/workstreams/skill-capability/phases/02-listing-floor/02-REVIEW.md:34` `.planning/workstreams/skill-capability/phases/03-opportunity-and-delivery-measurement/03-REVIEW.md:82`
- Pillar: [B] [C]

## UKDL-SC-03: zero, empty or absent input is UNMEASURED, never a reading
- Trap: a probe whose usage fields were all zero produced `startup_tokens = 0`, which passed an integer check and read as NOT_FALSIFIED. In phase 4, an absent or wrong live root made every row ABSENT_LIVE with zero rows compared, and the router freshness gate printed PASS.
- Rule: refuse a zero or implausible measurement and an empty comparison set as INCONCLUSIVE, with the reason named. A gate that compared nothing must not be able to print PASS.
- Source: `.planning/workstreams/skill-capability/phases/02-listing-floor/02-REVIEW.md:46` `.planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-REVIEW.md:46`
- Pillar: [B] [H]

## UKDL-SC-04: a row without a usable timestamp is UNMEASURED, not "not delivered"
- Trap: the delivery detector could treat a session whose only Skill row had no time as a non-delivery. The plan checker made it UNMEASURED and excluded it from the recall n. The review then found the opposite slip: a `deny-card` row with an unparseable ts was also made UNMEASURED, although the deny alone proves card delivery. On window F one bad ts moved recall from 4/6 to 3/5.
- Rule: mark UNMEASURED only the claim that actually needs the missing field. Absence of a timestamp leaves ordering unknown, but it does not erase evidence that stands on its own, and it is never counted as a negative.
- Source: `.planning/workstreams/skill-capability/phases/03-opportunity-and-delivery-measurement/03-01-PLAN.md:379` `.planning/workstreams/skill-capability/phases/03-opportunity-and-delivery-measurement/03-REVIEW.md:63`
- Pillar: [C]

## UKDL-SC-05: a gate re-run on another machine must read only committed blobs
- Trap: the card record, the H recordings and both evidence files were read from the working tree. In a shared checkout, an uncommitted `--record-cards` run makes the gate green on gex44, while the laptop `--final` re-runs the same argv on the committed tree and gets a different answer.
- Rule: every input of a gate that `--final` re-runs on another plane is read from `git show HEAD:<path>` (or an equivalent blob read). A dirty input makes the result INCONCLUSIVE. It never makes the result green.
- Source: `.planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-REVIEW.md:131`
- Pillar: [D] [H]

## UKDL-SC-06: files written by hooks must not ride a program commit
- Trap: a PostToolUse hook writes `docs/{arch,changelog,constitution,prd}/tools__*.md` stubs and modifies `vault/progress.md` whenever an executor writes a tool. A broad `git add` would have put them into the program's history as if they were its deliverables.
- Rule: commit by explicit pathspec only, and check `git log -1 --name-only` after every commit. Leave hook output untracked or unstaged. Do not delete it, because it is not the program's to destroy.
- Source: `.planning/workstreams/skill-capability/STATE.md:58`
- Pillar: [N]

## UKDL-SC-07: a dismissal in rendered prose must use the gate's own verdict rule
- Trap: the contribution render dismissed the frozen C-fixed 2/2 PASS rows with a p-value argument ("at n=2 they cannot move the verdict"). The verdict rule never uses that p. It compares the largest committed effect with the separation floor, and under that rule those rows flip E to SEPARABLE. The owner-bundle line repeated the false claim.
- Rule: any claim of the form "these rows could not change the verdict" is checked by running the verdict function with and without the rows. Prose and owner text are emitted by the gate, never typed by hand.
- Source: `.planning/workstreams/skill-capability/phases/07-contribution/07-REVIEW.md:53` `tools/test_contribution_verdict.py`
- Pillar: [E]

## UKDL-SC-08: a normalisation drill must go red when the normalisation is removed
- Trap: the CRLF drills re-encoded JSON records. JSON treats `\r` as whitespace, so with `lf_bytes` replaced by the identity function the three drills still returned ok. They claimed to prove the CRLF handling while it could have been deleted.
- Rule: put the pole where the transformation changes the result, for example a hashed blob whose digest must stay stable under CRLF. Run the mutant with the transformation removed and require the drill to fail.
- Source: `.planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-REVIEW.md:96` `tools/test_skill_drift.py`
- Pillar: [D] [H]

## UKDL-SC-09: a key added after a block-scalar value can be swallowed by a hand-rolled reader
- Trap: the creation gate appends `metadata:` at the end of a frontmatter. The router's reader keeps collecting a block-scalar description until a line has text after the colon, and a bare `metadata:` has none, so the declaration lines became part of the skill's description. The shape had been validated only against `quick_validate.py`, never against the repo's own reader.
- Rule: validate a generated frontmatter shape against every reader that consumes it, and include a fixture whose description is a block scalar.
- Source: `.planning/workstreams/skill-capability/phases/08-owner-reconciliation-and-creation-governance/08-REVIEW.md:164` `tools/skill_creation_gate.py` `modules/skill_router/skill_index.py`
- Pillar: [J]

## UKDL-SC-10: a pin on "not landed yet" goes stale the moment its subject lands
- Trap: CE's `V-CEP-REAL-HANDOFF` pinned "frozen at 1cabd117 -> not landed". Two later commits touched the probe file, so CE's own `--selftest` and `--final` failed for a reason that had nothing to do with this program. The CE file could not be edited because it belongs to a live mission.
- Rule: pin a negative state to a commit range or a content digest, not to the claim that something has not happened. When the owner file cannot be edited, substitute exactly the stale line in a wrapper and record the substitution.
- Source: `.planning/workstreams/skill-capability/STATE.md:48` `tools/test_skill_capability_program.py`
- Pillar: [N]

## UKDL-SC-11: an isolation sentinel can go stale between dispatches
- Trap: the executor-isolation sentinel had gone stale between epochs. The guard fell back to harness-worktree and refused the dispatch, so the run stalled on a guard state that nobody had changed on purpose.
- Rule: before each dispatch, re-check any recorded isolation decision and re-record it when it differs. Treat the refusal as a state to diagnose. Do not retry against it.
- Source: `.planning/workstreams/skill-capability/STATE.md:61`
- Pillar: [N]

## UKDL-SC-12: a push refused by a hook is an Owner decision, not something to retry
- Trap: a fast-forward push of the run branch was refused by the ovo-push-gate PreToolUse hook, with its stderr withheld. Retrying, or reshaping the command to get past the hook, would have repeated a failure whose cause was invisible.
- Rule: do not retry a refused push. Keep the work committed on the local run branch, record the refusal and the exact command, and let the Owner choose. Nothing is lost while the commits exist.
- Source: `.planning/workstreams/skill-capability/STATE.md:57`
- Pillar: [N]
