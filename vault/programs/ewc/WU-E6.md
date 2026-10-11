# WU-E6 -- Integrate live, Production Reality, knowledge promotion, handoff (M13, M14)

Common brief: `PROGRAMME.md`. Read ALL earlier receipts first. Route M (20 calls).
cwd `C:\Users\User\Apps\wt_ewc`; this unit alone writes code into the live checkout.

Steps:
1. Integrate: in the live checkout (`C:\Users\User\.claude\skills\claude-power-pack`, branch
   feature/knowledge-acquisition, OTHER PANES HAVE UNCOMMITTED EDITS THERE -- never stash, reset or checkout their
   files): `git merge --ff-only ewc/closure` if possible; else rebase ewc/closure onto the live HEAD in the worktree,
   re-run tools/test_ewc.py there, then ff-merge. If a path ewc touches is dirty in the live tree, stop and write
   BLOCKED_HUMAN naming the paths. Then copy canonical `hooks/closer-guard.js` (and the dispatcher only if E3/E4
   changed it) to `~/.claude/hooks/` with a hash before/after; if the classifier denies the write, BLOCKED_HUMAN with
   the exact Copy-Item lines. Verify the live heartbeat files advance on the next real turn end.
2. Production Reality (real Claude Code sessions, not test callers). Scratch repos under
   `C:\Users\User\Apps\ewc_pr\` (git init each). For each, launch ONE bounded headless session
   (`claude -p ... --max-turns 30`, env `CPP_EWC_GATE=enforce`, output to a file, < 400K tokens each):
   a. SOFTWARE: a tiny Python module with 2 failing tests and a prompt that asks to "evaluate the module and report".
   b. REFERENCE LOOP: a target PNG and a generator script whose output differs by an objective pixel threshold
      (PIL diff); prompt asks to "compare the render to the target and report".
   Evidence for each, from the transcript + autonomy-decisions.jsonl: the finding appears, a CONTINUE_* receipt with
   would_block=true and a real Stop `decision: block`, the agent then closes the work without new user input, a
   re-evaluation, and a final STOP_COMPLETE (or STOP_HUMAN_GATE for a deliberately subjective last line). Also report
   the SHADOW receipts collected from ordinary live sessions on this host since the merge (count, would_block rate).
   A run that did not show the block is NOT_PROVEN, never inferred.
3. M14 knowledge: promote KNOWLEDGE.md entries (canonical incident = EVALUATION WITHOUT CLOSURE) into
   `vault/knowledge_base/ukdl-universal.md` as CANDIDATES with evidence status (Traps: EWC, Recommendation-as-Stop,
   Analysis!=Mission; Process: evaluate->obligation loop, classify every unresolved item before Stop; Hard-rule
   candidates: no voluntary stop with an AGENT/NOW blocking obligation; unknown completion != complete). Do NOT
   auto-promote to HARD-RULES. UCR-CIF stage = highest stage actually evidenced (expected: ADVERSARIAL + PRODUCTION
   REALITY single host; CROSS-PROJECT/TRANSFER = UNPROVEN). Constitutive Baseline: LOCAL BASELINE + the V-EWC gate as
   the inheritance check; state CPP-WIDE as a candidate only.
4. CLAUDE.md: leave unchanged unless an existing line duplicates the new runtime rule (then merge/retire, never append).
5. Final receipt = the HANDOFF CONTRACT: pane/worktree/branch/HEAD (git-log verified), remote status (no push), mission
   status COMPLETE/PARTIAL/BLOCKED, token use per unit (from `tools/mission_spend.py goal-status --goal ewc`), root
   cause, ownership, obligation model, gate semantics, stop reasons, human-gate purity, anti-livelock, both PR results,
   commits in causal order, UKDL/UCR-CIF/ratchet status, UNPROVEN list, single NEXT TASK (expected: the Owner decision
   to flip interactive sessions from shadow to enforce, with the shadow false-block rate as its evidence).
