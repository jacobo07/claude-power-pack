---
phase: 05-close-the-continuation-debts
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [tools/gsd_autorun_marker.py, tools/test_gsd_long_run.py,
  extension/src/terminal_inbox.js, extension/src/extension.js,
  tools/test_terminal_inbox.py, tools/test_inbox_delivery_enter.py,
  .planning/phases/05-close-the-continuation-debts/05-RESIDUE-INVENTORY.md]
autonomous: false
requirements: [DEBT-1, DEBT-2, DEBT-3]
estimate: {tokens: 90000, raw_tokens: 45000, tasks: 3, confidence: low}
must_haves:
  truths:
    - "A ledger `armed` row names the same absolute project as the marker from that arming (DEBT-1)."
    - "An arming that cannot name a project records empty in BOTH records, never the caller's cwd (DEBT-1)."
    - "`/compact <args>` yields a tail and `/gsd-autonomous --from 3` yields none, under a gate that runs (DEBT-2)."
    - "Each residue item carries size, origin and a reasoned recommendation; none is deleted without the Owner's word (DEBT-3)."
  artifacts: [tools/test_gsd_long_run.py, extension/src/terminal_inbox.js,
    .planning/phases/05-close-the-continuation-debts/05-RESIDUE-INVENTORY.md]
  key_links:
    - "marker CLI :253 derives cwd from the marker dict read at :246, never from args.cwd"
    - "extension.js calls terminal_inbox.argumentTail() — one rule, one home"
    - "test_terminal_inbox.py's floor becomes >=, or it decays on every check added"
---

<objective>
Close the three debts milestone v1 exposed. Debts 1 and 2 land with a driven red branch each;
debt 3 is inventoried and handed to the Owner undeleted.
Purpose: two records of one arming must not disagree, and a line this estate types into a live
terminal must rest on more than one Owner observation.
Output: two gated fixes, one inventory awaiting a decision.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/phases/05-close-the-continuation-debts/05-CONTEXT.md

Windows host. Use the PowerShell tool with absolute paths; `python`, `git`, `node` and `grep`
via Bash are blocked by windows-bash-bridge-guard.js. `$PY` is
C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe; `$GIT` is
C:\Program Files\Git\cmd\git.exe.

Measured at plan time, load-bearing, do not re-derive:
- `terminal_inbox.js --selftest` prints ok=23 while test_terminal_inbox.py pins EXPECTED_OK = 12
  by EQUALITY, so that gate exits 1 TODAY — red because its population floor decayed, not
  because its subject is wrong. Task 2 repairs the instrument as well as adding to it.
- `git ls-files` reports tools/gsd_long_run.py.pre-phase-advance UNTRACKED; all others tracked.
- Residue: 49.2 KB + 629 B + 82 B + 82 B — four items, ~50 KB.
</context>

<tasks>

<task type="tracer">
  <name>Task 1: One arming, one project — the ledger row stops disagreeing with the marker</name>
  <files>tools/gsd_autorun_marker.py, tools/test_gsd_long_run.py</files>
  <read_first>gsd_autorun_marker.py:89-109 and :243-254; gsd_long_run.py:739-760 (marker_project —
  why a relative cwd is REFUSED, not resolved); test_gsd_long_run.py:481-498 (gates_cli) and :131
  (events() returns names only, so read rows directly).</read_first>
  <action>
    :253 passes raw args.cwd to ledger_append while write_marker stored resolve_cwd(cwd). Do NOT
    touch :98 — it is correct, and the asymmetry IS the defect. Fix :253 only: pass the cwd the
    marker actually recorded, from the `data` dict already loaded at :246, exactly as the adjacent
    max_cycles argument does. Derive, do not recompute — a second resolve_cwd call can drift, a
    value read back from the marker cannot disagree with it. Empty stays empty, per resolve_cwd's
    docstring. Leave :239 alone; arm_preflight runs IN the project.

    Extend gates_cli() with three gates. Arm through the CLI with --cwd . and the subprocess's own
    working directory set to the temp project, reproducing the real shape (8 of 9 markers held
    "."), then read the armed row via lr.ledger_events(sid). Assert V-GSDLR-LEDGER-CWD-ABSOLUTE
    (row cwd absolute), V-GSDLR-LEDGER-CWD-MATCHES-MARKER (row cwd equals marker cwd),
    V-GSDLR-LEDGER-CWD-EMPTY-STAYS-EMPTY (no --cwd leaves both empty). The third discriminates: a
    naive repair spelled resolve_cwd(args.cwd or ".") passes the first two and breaks it.
  </action>
  <verify>
    <automated>&amp; $PY tools\test_gsd_long_run.py</automated>
    <fails_when>exit code 1, or the suite reports any V-GSDLR-LEDGER-CWD- gate as failing, or the three new gate names are absent from stdout (they were never reached)</fails_when>
    <automated>RED BRANCH: record SHA-256 of tools\gsd_autorun_marker.py; revert :253 to args.cwd; re-run the gate; restore; recompute SHA-256 and require equality with the recorded value.</automated>
    <fails_when>the mutated run does NOT report V-GSDLR-LEDGER-CWD-ABSOLUTE as failing (the gate is vacuous), or the post-restore SHA-256 differs from the pre-mutation one</fails_when>
  </verify>
  <done>Ledger row and marker name one absolute directory; an unnamed project stays unnamed in both; GSDLR_PASS=N/N threshold=N/N with no failing line; the mutation was observed landing on its own assertion, restore verified by digest.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: The argument tail gets a red branch, by moving the rule where a gate can reach it</name>
  <files>extension/src/terminal_inbox.js, extension/src/extension.js, tools/test_terminal_inbox.py, tools/test_inbox_delivery_enter.py, ~/.claude/hooks/auto-compact-sendkeys-daemon.ps1</files>
  <read_first>extension.js:113-171 (delivery block; predicate inline at :155-157) and :35 (the
  existing require); terminal_inbox.js in full; test_terminal_inbox.py; test_inbox_delivery_enter.py.</read_first>
  <behavior>
    argumentTail(text), pure: "/compact focus on v1 phases" -> "focus on v1 phases";
    "/compact   spaced  " -> "spaced"; "/gsd-autonomous --from 3" -> ""; "/cpp-gsd-long" -> "";
    "/compact" bare -> "" (no separating whitespace); "/compaction now" -> "";
    "please /compact x" -> "" (anchored at the start); non-string and empty -> "".
  </behavior>
  <action>
    The mechanism, named: the predicate cannot be driven inside extension.js because that module
    requires vscode. Move it. Export a pure argumentTail from terminal_inbox.js — already
    vscode-free, already exported, already carrying a --selftest block, already run by
    test_terminal_inbox.py. That existing path IS the mechanism. Then destructure argumentTail from
    the require at :35 and replace the inline regex with a call, keeping the comment that records
    why the tail is scoped to /compact and why it is not free. Two copies of one rule drift.

    Add V-INBOX-ARGTAIL-* checks for every case above, on SYNTHETIC strings written for the purpose
    — never this session's real /compact line, which would decay the moment that artifact changes.
    Assert the predicate only; the Enter count belongs to the structural gate and is exactly what a
    future build is expected to change.

    SCOPE OF THE CLAIM, narrowed deliberately (plan-checker warning, 2026-09-21, and a measurement
    that arrived the same hour). The above closes the tail-EXTRACTION class. It does NOT close the
    class CONTEXT §2 names — "a future build changes the completion-popup behaviour, the tail
    becomes a stray message in every crossing and no test says so" — and that class is no longer
    hypothetical: the 18:24 crossing compacted on the command line's own two Enters and the tail
    landed in the fresh prompt as a bare user message. No unit test can close it, because the
    subject is a host popup in a build we do not own; asserting an Enter arity would pin the very
    number a build is expected to move, trading an unobservable failure for a brittle gate.

    What CAN be closed is the reason that crossing could not answer the question: the evidence is
    thrown away. writeAck already carries `enters` and `arg_tail`, but the ack file is consumed
    (`flags left=0`) and the daemon's SENT line does not record either, so nothing durable says
    what the extension did. Carry them onto the SENT line in
    ~/.claude/hooks/auto-compact-sendkeys-daemon.ps1, beside the existing via=/sid=/terminal=
    fields, reading them from the ack the daemon has already parsed. Then a popup-behaviour change
    is visible as `enters=3` on a crossing that compacted without the tail — one line per crossing,
    in an artifact that outlives the flag. Same HR-001 staging rule as the extension copies if the
    classifier refuses the write: stage it, do not retry it through a different tool.

    Record the residual in 05-SUMMARY.md by name: the popup-behaviour coupling is NOT closed by a
    drill, it is made OBSERVABLE, and the first crossing after this task is what tests it.

    Repair the instrument in the same task: test_terminal_inbox.py compares ok= by equality against
    12 while the selftest emits 23, so added checks would move the number again. Parse the integer
    from the summary line, require it to be at least the floor, re-baseline.

    Add a structural assertion to test_inbox_delivery_enter.py that the delivery block CALLS the
    shared helper rather than carrying its own regex, so the second copy cannot quietly return.

    Owner-applied, not agent-applied: the executing copy is
    ~/.cursor/extensions/kobii.pp-sessions-0.4.0/src/extension.js, which the auto-mode classifier
    refuses to write (HR-001 class). Stage identical edits for both files and hand them over; the
    live copy takes effect only on a window reload. Until the Owner mirrors,
    V-INBOX-LIVE-MATCHES-REPO reports drift — that is the gate working, and it must not be
    weakened, skipped or re-baselined to make the suite look clean.
  </action>
  <verify>
    <automated>&amp; $PY tools\test_terminal_inbox.py</automated>
    <fails_when>exit code 1, or stdout lacks TERMINAL_INBOX_PASS=1/1, or the reported ok= count is below the re-baselined floor</fails_when>
    <automated>&amp; $PY tools\test_inbox_delivery_enter.py</automated>
    <fails_when>any gate other than V-INBOX-LIVE-MATCHES-REPO is reported failing, or V-INBOX-CONTROL-PATH-FOUND reports the delivery block could not be located (exit 2, HARNESS-FAILED, every other assertion then passing vacuously)</fails_when>
    <automated>RED BRANCH, one mutation per pole. Record SHA-256 of extension\src\terminal_inbox.js. (a) make argumentTail return the empty string unconditionally, re-run the inbox gate, the positive case must be reported failing; (b) restore, drop the leading /compact anchor so every command yields a tail, re-run, the /gsd-autonomous case must be reported failing. Restore, recompute SHA-256, require equality.</automated>
    <fails_when>either mutation leaves the gate reporting a clean pass (that pole is not load-bearing), or (a) and (b) land on the same assertion (only one pole is covered), or the post-restore SHA-256 differs from the pre-mutation one</fails_when>
    <automated>The daemon's SENT line records what the extension did: after editing auto-compact-sendkeys-daemon.ps1, assert by inspection that the SENT Log call interpolates the ack's enters and arg_tail fields, and that the REFUSED and WOULD-SEND lines are untouched. If the classifier refuses the write, this is STAGED, not done — say so rather than reporting the item closed.</automated>
    <fails_when>the SENT line still carries only via=/sid=/terminal=/window=, or the fields are read from anywhere other than the ack the daemon already parsed (a second source can disagree with what was typed), or a staged-but-unapplied patch is reported as applied</fails_when>
  </verify>
  <done>argumentTail lives in terminal_inbox.js, extension.js calls it, the selftest drives both poles on synthetic subjects, test_terminal_inbox.py exits 0 against a floor that is a floor, and the two mutations landed on different assertions. The daemon's SENT line carries enters= and arg_tail= so the next crossing leaves durable evidence of what the extension actually did. The live patch is staged for the Owner with the reload requirement stated and the drift reported rather than silenced. 05-SUMMARY.md names the popup-behaviour coupling as an open residual that this task makes OBSERVABLE, never as closed — the first crossing after it is what tests it.</done>
</task>

<task type="checkpoint:decision">
  <name>Task 3: Residue — inventory it, recommend, hand the deletion to the Owner</name>
  <files>.planning/phases/05-close-the-continuation-debts/05-RESIDUE-INVENTORY.md</files>
  <action>
    Nothing is deleted here. Silence is not authorization for a deletion, so this task produces
    evidence and halts. Write a table, one row per item, columns: path, size, mtime, tracked
    (`&amp; $GIT ls-files -- &lt;path&gt;`, non-empty meaning tracked), origin, readers, recommendation.
    The four items: tools/gsd_long_run.py.pre-phase-advance (49.2 KB, UNTRACKED — removing it
    touches no history); ~/.claude/state/gsd-autorun-37cfb187-ec05-43db-b57d-4bdcb5625362.json.pre-phase4
    (629 B); ~/.claude/state/gsd-autorun-intent-ghost-30594a7d.json and -df5d917a.json (82 B each).

    Fill `readers` by searching the estate for each filename and each ghost session id BEFORE
    recommending anything: a file some gate or fixture loads is not residue, and recommending the
    deletion of a live fixture is the one move here that reverting a commit cannot undo. A search
    that could not complete is written unknown — never absent, never an assumed zero.

    For origin, name the commit or session that produced each, confirmed from the files and git
    log. Give each item a recommendation WITH its reason, and state that a kept-decision-with-reason
    closes the debt just as well as a deletion. Leave a decision line per item. Present the table
    and stop — do not delete, do not stage a deletion, do not read an unanswered checkpoint as
    approval.
  </action>
  <verify>
    <automated>&amp; $PY -c "import pathlib;t=pathlib.Path(r'.planning/phases/05-close-the-continuation-debts/05-RESIDUE-INVENTORY.md').read_text(encoding='utf-8');print('ROWS=',sum(k in t for k in ('pre-phase-advance','intent-ghost-30594a7d','intent-ghost-df5d917a','pre-phase4')))"</automated>
    <fails_when>the printed ROWS value is below 4, or the command raises FileNotFoundError because the inventory was never written</fails_when>
  </verify>
  <done>All four items appear with a size, an origin, a readers finding and a reasoned recommendation. Nothing on disk has been removed. The decision is the Owner's to record.</done>
</task>

</tasks>

<threat_model>
Trust boundaries: extension -> live terminal (a string this estate composes is typed and submitted
into the Owner's running session); plan -> Owner's filesystem (a recommended deletion of files
holding no second copy).

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-05-01 | Tampering | terminal_inbox.argumentTail | medium | mitigate | the tail stays anchored to `/compact`; the negative pole is a driven assertion, so widening it to every command turns a gate red |
| T-05-02 | Denial of Service | Task 3 residue | high | mitigate | no unattended deletion; `readers` searched before any recommendation; the Owner checkpoint is blocking |
| T-05-03 | Repudiation | ledger `armed` row | low | mitigate | the row derives its cwd from the marker, so two records of one arming cannot disagree about which project ran |

No package-manager installs occur in this phase, so no legitimacy gate applies.
</threat_model>

<verification>
From the repo root: `& $PY tools\test_gsd_long_run.py` and `& $PY tools\test_terminal_inbox.py`
exit 0; `& $PY tools\test_inbox_delivery_enter.py` exits 0 or reports V-INBOX-LIVE-MATCHES-REPO
alone as drift pending the Owner's mirror. The host is under memory pressure — prefer these narrow
suites over any repo-wide sweep, and bracket the dirty-path set if one is run anyway.
</verification>

<success_criteria>
Debts 1 and 2 each carry a mutation observed landing on its own assertion, restore verified by
SHA-256. Debt 3 is inventoried, recommended and undeleted. test_terminal_inbox.py is green against
a floor that can no longer decay.
</success_criteria>

<output>
Create `.planning/phases/05-close-the-continuation-debts/05-SUMMARY.md` when done. Record the
live-extension patch as staged-not-applied, and name any premise measured false during execution.
</output>
