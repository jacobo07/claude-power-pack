---
phase: 01-two-pane-exactness-drill
plan: 01
type: execute
wave: 1
depends_on: []
autonomous: false
requirements: [C2, C3, C4, C5]
files_modified:
  - tools/two_pane_drill.py
  - tools/test_two_pane_exactness.py
  - vault/evidence/two-pane-exactness/  (run artifacts, one JSON per run)
  - vault/lessons/two-pane-exactness-drill.md
  - vault/liveness/reachability_registry.json

user_setup:
  - service: cursor-terminal-panes
    why: >
      The send leg requires a terminal inside this Cursor window's
      `vscode.window.terminals` array, because `ownedTerminals()` intersects
      request ancestors against that array (extension/src/terminal_inbox.js:54-61)
      and `INBOX_DIR` is hardcoded to the real `~/.claude/state/terminal-inbox`
      (extension/src/extension.js:36). No headless extension-host harness for
      `extension/src/extension.js` was found (01-RESEARCH.md open question 1,
      "not determined"), so a human must open the two subject terminals.
    dashboard_config:
      - task: "Open subject terminal S-A in THIS Cursor window and run the arm command the drill prints"
        location: "Cursor: Terminal -> New Terminal (Ctrl+Shift+`)"
      - task: "Open subject terminal S-B in the SAME Cursor window and run its arm command"
        location: "Cursor: Terminal -> New Terminal (Ctrl+Shift+`)"

estimate:
  tokens: 120000
  raw_tokens: 60000
  tasks: 6
  confidence: low        # zero calibration samples for this repo; not self-rated

must_haves:
  truths:
    - "A continuation armed for subject session A is submitted into A's own terminal: A's transcript gains a type=\"user\" row carrying A's nonce, after t0."
    - "The same continuation is never submitted into B: B's transcript gains no type=\"user\" row carrying A's nonce, after t0."
    - "That absence is produced by an instrument proven able to return the other answer: the same predicate, over the same B transcript, in the same window, returns True for B's own nonce."
    - "A request whose OWNER answers refused is ledgered `refused` carrying the owner's own decide() reason string."
    - "Neither pane is one of the Owner's real working sessions, and the drill's daemon can address no session but its own subjects."
  artifacts:
    - tools/two_pane_drill.py
    - tools/test_two_pane_exactness.py
    - "vault/evidence/two-pane-exactness/<run-id>.json"
    - vault/lessons/two-pane-exactness-drill.md
  key_links:
    - "flag file -> Get-ExpectState -> Request-Inbox: the typed line is the transcript's last assistant line, not a string the flag dictates (auto-compact-sendkeys-daemon.ps1:215-224, :393-394)."
    - "Request-Inbox -> <sid>.req.json -> the real extension's decide() -> <sid>.ack.json -> Poll-Inbox -> Write-LedgerRow (daemon:331-333, :344-346, :354-362)."
    - "extension.js:79 reads the LIVE ~/.claude/sessions/<claude_pid>.json, so sandboxing AC_SESSIONS_DIR contains the daemon's addressing without weakening the extension's authority."
    - "gsd_long_run.user_issued_command_since over the pane's own ~/.claude/projects/<hash>/<sid>.jsonl is the only artifact that proves submission rather than display (gsd_long_run.py:290-308)."
---

<objective>
Prove, live and once, the exactness claim the transport was rebuilt for: with two
Claude Code sessions running in two terminals of the SAME Cursor window, a
continuation armed for session A is submitted into A's own terminal and never
into B's, and a request that its owner refuses is ledgered `refused` carrying the
owner's own reason.

Purpose: every gate that today names "two panes", "ownership" or "refusal" runs
against a fake on one side of the boundary. `V-CXT-TWO-PANE-*` drives a fake Orca
subprocess (`tools/test_continuation_transport.py:31-60`, `:210-212`) for a route
this host cannot run at all — no Orca runtime here (01-CONTEXT.md:28-30).
`V-ACPS-I-*` / `V-ACPS-E-*` drive the real daemon against a scripted Python
`fake_extension()` thread (`tools/test_autocompact_per_session.py:329-344`) in
DRY-RUN, which the suite's own docstring says "never calls SendKeys, so this
suite cannot press Enter into a live pane" (`:5-6`). **No existing gate opens a
second real Cursor terminal, loads the real `extension/src/extension.js` in a
real extension host, or reads a real `~/.claude/projects/<hash>/<sid>.jsonl` to
confirm a `type:"user"` row was appended.** Closing exactly that gap is this
phase's whole value. It must not re-derive the unit coverage that already exists.

Output: a harness (`tools/two_pane_drill.py`), a sealed evidence file of
POINTERS (session ids, pids, procStarts, transcript paths, t0, nonces, ledger
row id) rather than conclusions, and a re-runnable gate
(`tools/test_two_pane_exactness.py`) that re-derives every verdict from those
real artifacts on disk.

Why the tracer leads and where the human sits: Task 1 is the tracer — one pane,
one owned request, end to end, production-quality, committed. Its subject cannot
be created by software on this host, so the operator step is written INTO the
tracer's action with the exact words the operator types, in order. The operator
is interrupted twice in the whole phase (once per pane) and never asked to judge
anything.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-two-pane-exactness-drill/01-CONTEXT.md
@.planning/phases/01-two-pane-exactness-drill/01-RESEARCH.md

@extension/src/terminal_inbox.js
@extension/src/extension.js
@tools/gsd_long_run.py
@tools/test_autocompact_per_session.py
@~/.claude/hooks/auto-compact-sendkeys-daemon.ps1
</context>

<mechanism_corrections>
Two claims handed to this planner were checked against source and one needed
correcting. Both are load-bearing, so both are recorded rather than silently
applied.

**CORRECTED — the no-owner case IS ledgered `refused`, by a different writer,
with a different detail.** The finding said a request nobody answers "does NOT
write a ledgered `refused` row". That is true of `Poll-Inbox`, which only sets
local state to `fallback` and deletes the `.req.json`
(`auto-compact-sendkeys-daemon.ps1:370-375`) — but the main loop then re-reads
that flag, sees `state -eq 'fallback'`, and calls
`Refuse-NoExact $fl 'no terminal-inbox provider answered or the session is not
resolvable'` (`:411-413`), which DOES call `Write-LedgerRow ... 'refused' ...`
(`:265`). So a `refused` row appears either way.

**The finding's CONCLUSION still stands, and is the reason this matters.** The
two rows carry different `detail` strings and mean different things:

| trigger | writer | ledger `detail` | what it proves |
|---|---|---|---|
| owner's `decide()` answers `refused` | `Poll-Inbox` (`:354-362`) | `terminal inbox refused: <decide() reason>` | the OWNING window judged the request and said no |
| nobody answers in `$ackFirstSec` (10 s) | `Refuse-NoExact` (`:261-266`, reached via `:411-413`) | `no exact-session delivery: no terminal-inbox provider answered or the session is not resolvable` | the DAEMON found no provider — it says nothing about any window's judgement |

This phase's criterion — "ledgered `refused` with its reason" — is satisfied only
by the first row. The second is a real and useful observation (nothing was typed
into the focused window) but it is strictly weaker, and Task 3 records it as
such rather than counting it.

**CONFIRMED and sharpened — the evidence predicate checks only the first token.**
`user_issued_command_since` takes `name = command.split()[0]` and matches either
`<command-name>{name}</command-name>` or `text.strip().startswith(name)`, on rows
with `type == "user"` and `timestamp >= since` (`tools/gsd_long_run.py:296-308`).
Rather than work around that weakness, this plan removes it: the drill makes the
FIRST TOKEN a per-pane, per-run nonce (`DRILL-A-<runid>` / `DRILL-B-<runid>`), so
a first-token match IS a match on that pane and that run, and a stale earlier
occurrence cannot exist. Pane B's absence assertion uses the same function, the
same file and the same `since`, so a pass and a fail come out of one instrument.
</mechanism_corrections>

<tasks>

<task type="tracer">
  <name>Task 1: Tracer — one subject pane, one owned request, proven from its own transcript</name>
  <files>tools/two_pane_drill.py, tools/test_two_pane_exactness.py</files>
  <read_first>
    extension/src/terminal_inbox.js:47-87 (validText bound 1..512 at :49; the
    check ORDER at :68-87 — ownership, expiry, text, session identity, then
    status LAST at :85);
    extension/src/extension.js:36-38 (INBOX_DIR and SESSIONS_DIR are HARDCODED
    to the real `~/.claude/...` paths), :63-80 (the watcher reads
    `SESSIONS_DIR/<req.claude_pid>.json` LIVE at :79 and calls decide at :80),
    :96-110 (claim -> ack -> delete on refuse/send);
    ~/.claude/hooks/auto-compact-sendkeys-daemon.ps1:52-54 (AC_DAEMON_DIR is the
    flag + lock + log dir), :158-176 (Get-Flags: the flag JSON carries
    `cwd`, `session_id`, `transcript`, `expect_line`, `expect_prefix`),
    :184-224 (Get-LastAssistantLine + Get-ExpectState), :236-241
    (Write-LedgerRow honours GSD_LONG_RUN_STATE_DIR), :291-296 (AC_INBOX_DIR,
    AC_SESSIONS_DIR, AC_ACK_FIRST; note `$inboxTtlMs = 60000` has NO env
    override), :298-336 (Resolve-Session + Request-Inbox), :383-402 (the loop);
    tools/gsd_long_run.py:134-136, :212-220, :290-308 (projects_dir,
    find_transcript, user_issued_command_since);
    tools/test_autocompact_per_session.py:1-45 (the `_ok`/`_fail` gate
    convention this repo prints).
  </read_first>
  <action>
    Build `tools/two_pane_drill.py` and drive its full path once, end to end,
    against ONE subject pane. This is the thin vertical slice: flag -> real
    daemon -> real request file -> real extension `decide()` -> real
    `term.sendText` -> real transcript row. Every layer the phase touches is
    crossed once here; Tasks 2-4 widen it, they do not add layers.

    Containment first — the drill owns its subjects and can address nothing else
    (constraint: never run against the Owner's real working sessions):
    - `AC_DAEMON_DIR=<run>/hooks` — the drill's daemon then scans ONLY its own
      flag dir, takes its own lock and writes its own log (daemon:52-54, :160),
      so it can neither see nor steal a real `auto-compact-*.flag`.
    - `AC_SESSIONS_DIR=<run>/sessions` — `Resolve-Session` iterates only this dir
      (daemon:300), so the drill's daemon can resolve no session but a subject
      the drill copied in. Copy the subject's real `~/.claude/sessions/<pid>.json`
      verbatim. This copy is safe because `Resolve-Session` reads only
      `sessionId`, `pid` and `procStart` (daemon:302-308) and NEVER `status`;
      `status` is read by the extension from the LIVE file at extension.js:79,
      so the extension's authority is untouched by the copy going stale.
    - `GSD_LONG_RUN_STATE_DIR=<run>/state` — the ledger goes to the drill's own
      `gsd-autorun-ledger.jsonl` (daemon:236-241). Do NOT let the drill append to
      `~/.claude/state/gsd-autorun-ledger.jsonl`: that is the file
      `gsd_long_run.py report` reads for this milestone's PROVEN/UNPROVEN
      verdict, and a drill row for a throwaway session would corrupt the
      milestone's own acceptance reading. See <reversibility> below.
    - `AC_INBOX_DIR` MUST NOT be set. `INBOX_DIR` is hardcoded in the extension
      (extension.js:36); an overridden daemon-side inbox is a dir no real
      extension watches, which would silently convert the whole drill into the
      no-provider timeout path. Collision with the Owner's traffic is already
      prevented by key: request files are named `<sid>.req.json` and the sid is
      the drill's own subject session (daemon:331).
    - `AC_DAEMON_DRYRUN` MUST NOT be set (it is what neuters the existing
      V-ACPS suite, `test_autocompact_per_session.py:5-6`), and
      `CPP_LEGACY_FOREGROUND_SENDKEYS` MUST NOT be `1` — default-off is the
      exact-or-refused posture under test (daemon:259, :404-407).

    Subcommands:
    - `probe` — assert the preconditions and name each one that fails
      individually: python present at the absolute path, the daemon script
      exists, `extension/src/terminal_inbox.js` and `extension/src/extension.js`
      exist, the PP Sessions extension version is >= 0.4.0, and
      `~/.claude/state/terminal-inbox` is writable. A precondition that could
      not be READ is a distinct outcome from one that is absent.
    - `arm --pane A` — (1) snapshot the SET of `~/.claude/sessions/*.json` paths
      (a set, not a count: a count cannot see one session leaving as another
      arrives); (2) print the exact operator command; (3) poll for the set to
      gain exactly one new entry and take THAT entry as the subject. Identity is
      captured at spawn, by set difference, and is never re-derived afterwards
      from cwd, window title or `vault/terminal_slots.json`
      (01-RESEARCH.md:134-146). Record `session_id`, `pid`, `procStart`, `cwd`,
      and the transcript path resolved via `find_transcript(session_id)`.
    - `fire --pane A` — record `t0` (epoch seconds, taken BEFORE anything is
      written), then write `<run>/hooks/auto-compact-trigger-<sid>.flag` as UTF-8
      with NO BOM, carrying `{cwd, session_id, transcript, expect_line}`. Set
      `expect_line` to the subject transcript's CURRENT last assistant line read
      with the daemon's own rule (last `type=="assistant"` row, last non-empty
      text line, `.Trim().Trim('`').Trim()`, daemon:194-205). The daemon types
      that line back — `Get-ExpectState` returns `line = $last` and the loop only
      requests when `state -eq 'ok' -and $st.line` (daemon:219-220, :393-394), so
      the drill must ADAPT to what the subject actually said rather than dictate
      it. Then start the daemon once, foreground, bounded, with the env above.
    - `observe --pane A` — call `gsd_long_run.user_issued_command_since(
      transcript_A, nonce_A, t0)` and report True/False. Import the real function
      from `tools/gsd_long_run.py`; do not reimplement the three-part rule.

    Operator step, verbatim, in order (the tracer's one human interruption):
      1. Agent runs `probe`, then `arm --pane A`, which prints a single command.
      2. OPERATOR: in THIS Cursor window, Terminal -> New Terminal, then paste
         and run the printed command. It is one line: `cd` to the drill's own
         scratch dir `<run>/panes/A` then `claude`.
      3. OPERATOR: when Claude's prompt appears, paste the ONE prompt the agent
         printed — it asks the subject to answer with a single line beginning
         `DRILL-A-<runid>` and nothing else. Then LEAVE THE PANE ALONE: do not
         type, do not switch away from it being idle. A busy pane is not a
         failure — `decide()` returns `defer` with `status-busy` (terminal_inbox
         .js:85) and the extension re-polls every 500 ms (extension.js:38) — but
         it delays the send, so idle is what the drill waits for.
      4. Agent runs `fire --pane A`, waits for the ack, then `observe --pane A`.

    Choose a per-pane scratch cwd (`<run>/panes/A`), NOT the repo root. Reasons,
    both real: it gives each subject its own `~/.claude/projects/<hash>/` dir so
    transcript attribution is structural rather than inferred; and it stops the
    subject clobbering the repo's `vault/terminal_slots.json` slot, which holds
    exactly one entry per normalized cwd and overwrites on every SessionStart
    (modules/zero-crash/hooks/terminal-slot-recorder.js:16-27, :169-178).
    Distinct cwds cost nothing here: `decide()` never reads cwd — ownership is
    pid ancestry against this window's terminal list
    (terminal_inbox.js:54-61, :70-72) — so putting the two subjects in one cwd
    would add attribution risk without adding one line of coverage of the
    mechanism under test. What makes the `ownedTerminals` "exactly one match"
    logic meaningful is that both subjects live in the SAME Cursor WINDOW, and
    that is preserved.

    Ship `tools/test_two_pane_exactness.py` in this task carrying its first gate,
    following this repo's convention (`tools/test_autocompact_per_session.py:33-40`):
    `_ok(gate, evidence)` / `_fail(gate, evidence)` printing `PASS <gate>: ...` /
    `FAIL <gate>: ...`, a final `TWOPANE_PASS=n/total` line, exit 0 only when all
    pass. Add a third exit code: exit 2 and print `HARNESS-FAILED` when the
    evidence file or a transcript named by it is missing or unreadable — a
    verifier that could not judge its subject must never present as a verdict
    about that subject.
    First gate: `V-TWOPANE-A-RECEIVED` — `user_issued_command_since(transcript_A,
    nonce_A, t0)` is True.
  </action>
  <reversibility rating="costly">
    Writing the drill's refusal rows into the real
    `~/.claude/state/gsd-autorun-ledger.jsonl` would be an append to the same
    append-only file `gsd_long_run.py report` reads to decide this milestone's
    PROVEN/UNPROVEN verdict. Reversing it means editing a shared jsonl the live
    daemon is concurrently appending to. `GSD_LONG_RUN_STATE_DIR` makes the
    choice free, so the drill takes the sandboxed ledger.
  </reversibility>
  <precondition>
    A human operator is present and will open one terminal in THIS Cursor window
    on request. The PP Sessions extension (>= 0.4.0) is loaded and answering in
    this window — 01-CONTEXT.md:31-34 records it answering live tonight; `probe`
    re-asserts it rather than trusting that record.
  </precondition>
  <verify>
    <automated>&amp; 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_two_pane_exactness.py</automated>
    <human-check>
      The operator opened exactly one new terminal and typed only the two
      strings the drill printed.
    </human-check>
  </verify>
  <done>
    `TWOPANE_PASS=1/1`, exit 0. Subject A's own transcript at
    `~/.claude/projects/<hash>/<sid_A>.jsonl` carries a `type:"user"` row, later
    than `t0`, whose text begins `DRILL-A-<runid>`. The daemon's own log shows
    `SENT ... via=extension` for that sid. No row was written to
    `~/.claude/state/gsd-autorun-ledger.jsonl` by the drill.
  </done>
</task>

<task type="auto">
  <name>Task 2: Second subject pane, the absence assertion, and its negative control</name>
  <files>tools/two_pane_drill.py, tools/test_two_pane_exactness.py</files>
  <read_first>
    tools/gsd_long_run.py:242-261 (`_tail_rows` — the transcript is read from a
    tail window; `TAIL_BYTES` was not read by the research pass
    (01-RESEARCH.md:77) and is irrelevant here only because the drill's rows are
    seconds old, which this task must assert rather than assume), :264-272
    (`_text_of` flattens string or content-block messages);
    extension/src/terminal_inbox.js:54-61, :70-72 (ownedTerminals; zero matches
    is `ignore`, which writes NOTHING — 01-RESEARCH.md:37, :42).
  </read_first>
  <action>
    Extend `arm`/`fire`/`observe` to pane B and add the assertion the phase
    exists for, together with the control that makes it mean anything.

    Operator step, verbatim (the second and last human interruption): agent runs
    `arm --pane B`, prints one command; OPERATOR opens a SECOND New Terminal in
    the SAME Cursor window, runs it (`cd <run>/panes/B` then `claude`), and
    pastes the printed prompt, which asks that subject to answer with a single
    line beginning `DRILL-B-<runid>`. Both subjects are then live in one window —
    the state in which `ownedTerminals()` must pick exactly one of two terminals.

    Then run the send leg for A exactly as in Task 1, with B live throughout, and
    with B foregrounded/focused at the moment the request is fired (focus is the
    thing the rebuild was meant to stop mattering — daemon:254-258).

    Three assertions, all through the ONE instrument
    `gsd_long_run.user_issued_command_since`, differing only in the arguments:
    - `V-TWOPANE-A-RECEIVED` — (transcript_A, nonce_A, t0) is True. Carried from
      Task 1, now re-run with B live.
    - `V-TWOPANE-B-UNTOUCHED` — (transcript_B, nonce_A, t0) is False. A's
      continuation never reached B.
    - `V-TWOPANE-B-INSTRUMENT-CAN-SEE` — (transcript_B, nonce_B, t0) is True.
      **The negative control.** The operator's own submission of B's nonce into B
      is a row the same predicate must find, in the same file, over the same
      `since`. Without this, `V-TWOPANE-B-UNTOUCHED` is satisfied identically by
      a mistyped transcript path, a transcript that does not exist, a `since`
      later than every row, a tail window that never reached the rows, and a
      predicate that returns False for everything. This gate can only pass if the
      instrument is pointed at a real, readable, in-window B transcript and is
      capable of returning True from it.
    Make the control's dependency mechanical, not documentary: when
    `V-TWOPANE-B-INSTRUMENT-CAN-SEE` fails, `V-TWOPANE-B-UNTOUCHED` must be
    reported as `INCONCLUSIVE` and must not be counted as a pass. An absence
    observed by a blind instrument is not evidence.

    Also assert the tail-window precondition rather than assuming it: record
    `os.path.getsize(transcript_B)` and the byte offset of the matched control
    row, and fail the run if the control row is not inside the tail window
    `_tail_rows` actually read. That converts 01-RESEARCH.md:77's undetermined
    `TAIL_BYTES` from an assumption into a measured fact for this run.

    Record in the evidence file, for both panes: `session_id`, `pid`,
    `procStart`, `cwd`, `transcript`, `nonce`, and the terminal-open ORDER. Never
    resolve "which one was A" later from `vault/terminal_slots.json`, from a
    window title (`V-ACPS-E-TITLE-MATCH-IS-NOT-IDENTITY`,
    tools/test_autocompact_per_session.py:415-419, is this repo's own existing
    proof that a title match is not identity), or from cwd.
  </action>
  <verify>
    <automated>&amp; 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_two_pane_exactness.py</automated>
  </verify>
  <done>
    `TWOPANE_PASS=3/3`, exit 0, with `V-TWOPANE-B-INSTRUMENT-CAN-SEE` passing —
    i.e. the instrument that reported B untouched demonstrably returns the other
    answer on the same file. Both subject session ids appear in the evidence file
    with their pid, procStart and open order.
  </done>
</task>

<task type="auto">
  <name>Task 3: The refusal leg — an owned request its owner refuses, ledgered with its reason</name>
  <files>tools/two_pane_drill.py, tools/test_two_pane_exactness.py</files>
  <read_first>
    extension/src/terminal_inbox.js:68-87 — the check ORDER is what makes this
    task deterministic. `invalid-text` (:78) and the session-identity checks
    (:80-83) all run BEFORE the status check (:85), so a refusal does NOT
    require the subject to be idle;
    ~/.claude/hooks/auto-compact-sendkeys-daemon.ps1:298-317 (Resolve-Session
    matches `sessionId` case-sensitively at :302, requires the pid to be a LIVE
    process at :303-304, and requires procStart within 10 FILETIME units at
    :305-308), :338-362 (Poll-Inbox gates on ack id equality at :346 and writes
    the ledger row at :361), :261-266 and :404-416 (the OTHER refusal writer).
  </read_first>
  <action>
    Produce the row the phase's Done criterion names: one ledgered `refused`
    carrying a reason the OWNING window's `decide()` chose.

    Primary lever — `session-mismatch`, chosen because it is deterministic, needs
    no compliance from any agent, and is semantically the exact fear the phase
    names ("armed for A, resolved to B's terminal"):
    - Write ONE extra file into the drill's sandboxed `AC_SESSIONS_DIR`:
      `sessionId` = A's session id, `pid` and `procStart` = **B's** real live
      values, copied from B's real session file.
    - `Resolve-Session` matches it on sid (`:302`), finds B's process alive
      (`:303-304`) and its procStart within tolerance (`:305-308`), walks B's
      ancestor chain (`:309-313`), and `Request-Inbox` writes a request whose
      `session_id` is A's but whose `ancestors` are B's (`:326-328`).
    - The real extension resolves ownership to exactly B's terminal
      (`ownedTerminals`, terminal_inbox.js:70), reads the LIVE
      `~/.claude/sessions/<B pid>.json` (extension.js:79), finds
      `session.sessionId !== req.session_id`, and returns
      `{action:"refuse", reason:"session-mismatch"}` (terminal_inbox.js:81).
    - `Poll-Inbox` sees `status == 'refused'` with a matching ack id, moves the
      flag to `auto-compact-refused-*` and calls
      `Write-LedgerRow <sid> 'refused' "terminal inbox refused: session-mismatch"`
      (`:354-362`).
    Say plainly in the gate's docstring that the session file the drill plants is
    a CONSTRUCTED input standing in for a stale record for a reused pid — the
    thing constructed is the daemon's input, not the judgement. The judgement is
    made by the real `decide()` reading the real live session file, and that is
    the part under test.

    Fallback lever if the sandboxed sessions dir turns out not to reach the
    daemon as read: `invalid-text` (terminal_inbox.js:49, :78) — arrange for the
    subject's last assistant line to exceed 512 characters, which
    `Get-ExpectState` then hands to `Request-Inbox` verbatim (daemon:219, :394).
    It is equally owner-answered but depends on the subject agent emitting a long
    single line, which is why it is second choice, not first. `expired` cannot be
    used: the daemon stamps `created_ms` at write time and `$inboxTtlMs = 60000`
    has no env override (daemon:295, verified by grep — no `AC_INBOX_TTL`
    exists).

    Gate: `V-TWOPANE-OWNER-REFUSED` — the drill's own ledger at
    `<run>/state/gsd-autorun-ledger.jsonl` holds a row with `event == "refused"`
    whose `detail` starts `terminal inbox refused: ` and names a reason string
    that appears in `decide()`'s own vocabulary. Assert the reason is drawn from
    the literal set `{ambiguous-terminal, expired, invalid-text,
    session-unreadable, session-mismatch, pid-mismatch, proc-start-mismatch}`,
    and read that set out of `extension/src/terminal_inbox.js` at gate time
    rather than hardcoding a copy, so a reason renamed in the extension reds the
    gate instead of drifting past it.

    ALSO run, and record separately, the weaker no-owner observation, so the
    difference is on the record rather than in a planner's head: fire a flag for
    a session id no window owns, let it reach the 10 s `$ackFirstSec` timeout
    (daemon:370), and capture the `Refuse-NoExact` row
    (`no exact-session delivery: ...`, daemon:265 via :411-413). Emit it as
    `V-TWOPANE-NOOWNER-NOT-TYPED` and state in the gate's own evidence string
    that it proves nothing was typed into the focused window and does NOT prove
    any window judged the request. It must not be substitutable for
    `V-TWOPANE-OWNER-REFUSED`; a test asserting only that both rows exist, with
    no clause telling them apart, would pass with the owner leg removed.
  </action>
  <reversibility rating="reversible">
    Everything this task writes lives under the run dir and the drill's own
    sandboxed sessions/ledger dirs; the only file touched outside them is
    `~/.claude/state/terminal-inbox/<sid>.req.json`, keyed by a throwaway sid and
    deleted by the extension on claim (extension.js:96-97, :109).
  </reversibility>
  <verify>
    <automated>&amp; 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_two_pane_exactness.py</automated>
  </verify>
  <done>
    `TWOPANE_PASS=5/5`, exit 0. The drill's sandboxed ledger holds a `refused`
    row whose detail names a `decide()` reason, and a separate row from
    `Refuse-NoExact` that the gate reports as the weaker observation.
    `~/.claude/state/gsd-autorun-ledger.jsonl` is unchanged by the run (compare
    its size and last line before and after).
  </done>
</task>

<task type="auto">
  <name>Task 4: Seal the evidence as pointers and bind it to a re-runnable gate file</name>
  <files>tools/two_pane_drill.py, tools/test_two_pane_exactness.py, vault/evidence/two-pane-exactness/</files>
  <read_first>
    tools/test_autocompact_per_session.py:33-45 (the `_ok`/`_fail` shape and the
    final `*_PASS=n/total` line this repo's done-gates grep for).
  </read_first>
  <action>
    Add `seal`, writing `vault/evidence/two-pane-exactness/<run-id>.json`, and
    make the gate re-derive every verdict from that file plus the real artifacts
    it points at.

    Store POINTERS, never conclusions: run id, the wall-clock `t0`, both panes'
    `{session_id, pid, procStart, cwd, transcript, nonce, opened_at,
    open_order}`, the request ids, the ledger path and the byte offsets of the
    two ledger rows, the daemon log path, the extension version, and the env the
    daemon ran under. Do NOT store `a_received: true`. The transcripts and the
    ledger persist on disk; the gate re-runs `user_issued_command_since` against
    them and re-reads the ledger rows on every invocation, so a later deletion or
    edit of the evidence turns the gate red instead of leaving a green describing
    a world that no longer exists.

    Keep the three outcomes separate and make the third one loud:
    - all gates pass -> exit 0, `TWOPANE_PASS=n/n`
    - a gate's subject is genuinely wrong -> exit 1, `FAIL <gate>: ...`
    - the evidence file is absent, a transcript it names is gone, the ledger is
      unreadable, or the run predates the current `decide()` reason vocabulary ->
      exit 2, `HARNESS-FAILED: <what could not be read>`, and no `PASS`/`FAIL`
      lines for gates that were never evaluated. A verifier that could not judge
      its subject must not present as a verdict about it.
    Count what was actually judged and print it; a run that evaluated zero gates
    must never print `TWOPANE_PASS=0/0` and exit 0.

    Sixth and last gate, `V-TWOPANE-INBOX-DRAINED` (the T-01-06 mitigation, and
    the one assertion about the SHARED dir the drill could not sandbox):
    `~/.claude/state/terminal-inbox/` holds no file whose name carries a drill
    sid — no `.req.json`, no `.ack.json`, no `*.claimed`. A leftover request for
    a dead sid is re-read by every window with the extension loaded every 500 ms
    (extension.js:38, :63), so leaving one behind makes the drill a small
    permanent cost to the Owner's real windows.

    Drive the red branch of each gate before calling any of them earned, and
    record the mutation and its restore SHA-256 in the summary: (1) point
    `transcript_A` at B's file — `V-TWOPANE-A-RECEIVED` must fail; (2) set
    `nonce_A` to `nonce_B` — `V-TWOPANE-B-UNTOUCHED` must fail; (3) set `since`
    to `t0 + 86400` — `V-TWOPANE-B-INSTRUMENT-CAN-SEE` must fail, which is the
    control proving the control; (4) replace the ledger's `detail` with
    `Refuse-NoExact`'s string — `V-TWOPANE-OWNER-REFUSED` must fail while
    `V-TWOPANE-NOOWNER-NOT-TYPED` still passes, proving the two rows are not
    interchangeable; (5) plant one `<drill-sid>.req.json` in the real inbox dir —
    `V-TWOPANE-INBOX-DRAINED` must fail, then remove it; (6) delete the evidence
    file — exit 2, never exit 1.
  </action>
  <verify>
    <automated>&amp; 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_two_pane_exactness.py; if ($LASTEXITCODE -ne 0) { throw "gate exit $LASTEXITCODE" }</automated>
  </verify>
  <done>
    `TWOPANE_PASS=6/6`, exit 0, from a cold process with no drill running,
    reading only the sealed pointers and the real artifacts. All six mutations
    red the gate they target and nothing else; every restore is verified by
    SHA-256.
  </done>
</task>

<task type="auto">
  <name>Task 5: Record what this drill does not prove, and wire the gate into the repo's inventories</name>
  <files>vault/lessons/two-pane-exactness-drill.md, vault/liveness/reachability_registry.json</files>
  <read_first>
    01-CONTEXT.md:28-30 and :61-67 (no Orca runtime on this host; the
    `orca-exact` leg / GSDX-C08 is deferred and must not be claimed);
    01-RESEARCH.md:148-155 (the five items the research pass left undetermined);
    modules/liveness/reachability.py (the gate that names an unreachable module).
  </read_first>
  <action>
    Write `vault/lessons/two-pane-exactness-drill.md` stating the claim at
    exactly its real size, and no larger. It must say, in its own words:

    PROVEN by this drill (once, live, on this host, on this date): with two
    Claude Code sessions in two terminals of one Cursor window, a continuation
    armed for A reached A's transcript as a submitted `type:"user"` row and did
    not reach B's; the instrument that reported B's absence was shown able to
    return the other answer from B's own transcript; and a request the owning
    window refused was ledgered with that window's own reason.

    NOT PROVEN, each with its reason:
    - The `orca-exact` route. This host has no Orca runtime
      (01-CONTEXT.md:28-30); every `V-CXT-*` gate drives a fake Orca subprocess
      (tools/test_continuation_transport.py:31-60). Deferred as GSDX-C08.
    - Two sessions in the SAME cwd. This drill deliberately used one scratch cwd
      per pane. The `vault/terminal_slots.json` clobber
      (terminal-slot-recorder.js:169-178) is therefore observed as a hazard and
      avoided, not exercised. Note that exercising it would add no coverage of
      `decide()`, which never reads cwd.
    - Two sessions in two different Cursor WINDOWS. Only the one-window case ran,
      which is the case `ownedTerminals` exists to disambiguate; the
      cross-window `ignore` path (terminal_inbox.js:71) is inferred from source,
      not observed from a second window.
    - A headless extension-host harness. None was found
      (01-RESEARCH.md:150, "not determined"). The drill needs a human for both
      panes and that stays true until someone builds one.
    - The autocompact entry point. This drill fired flags directly into the
      daemon's own flag dir. Whether
      `modules/zero-crash/hooks/context-watchdog.py::_route_for` /
      `_dispatch_continuation` chooses this route on a REAL autocompact was NOT
      exercised (01-RESEARCH.md:153). It stays open.
    - The `V-CWIRE-*` gate bodies were never read (01-RESEARCH.md:126, :152).
      This plan assumed nothing from them. State that they remain unread rather
      than implying they were checked.
    - How `~/.claude/sessions/<pid>.json` comes to exist. Determined by exclusion
      during planning: no writer exists under `~/.claude/hooks` or in this repo
      (two greps for `procStart` returning 20 and 5 files, all data files or
      consumers), and the file's own fields (`entrypoint: "sdk-cli"`,
      `peerProtocol`, `peerFeatures`, `statusUpdatedAt`) say claude.exe writes
      it. Its `status` transitions (`idle` / `busy` / others) are therefore
      outside this repo's control and were not enumerated — the drill waits for
      `idle` rather than causing it.
    - `TAIL_BYTES` in `_tail_rows` (01-RESEARCH.md:77). Task 2 measures that this
      run's rows fell inside the tail window; the constant itself is still
      unread, so the assertion is about this run, not about every run.

    Then register the gate so it cannot rot: add
    `tools/test_two_pane_exactness.py` to the repo's gate inventory the same way
    the `V-ACPS-*` / `V-CXT-*` suites are registered, and declare
    `tools/two_pane_drill.py` in `vault/liveness/reachability_registry.json` —
    honestly. It is operator-invoked, so it is not reachable from a hook or
    command; classify it explicitly (`SCHEDULED`, or a declared operator-invoked
    class with an OWNER) rather than leaving it to read as silent debt, and
    re-baseline by name.
  </action>
  <verify>
    <automated>&amp; 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' modules\liveness\reachability.py</automated>
  </verify>
  <done>
    The lessons file lists every unproven item with its reason and claims nothing
    about Orca. `reachability.py` exits 0 with the new tool declared by name, and
    the standing debt set did not grow.
  </done>
</task>

<task type="checkpoint:human-verify">
  <name>Task 6: Operator confirms the drill ran against the drill's own panes</name>
  <files>vault/evidence/two-pane-exactness/</files>
  <action>
    STOP. The agent cannot verify this from inside; it is the one claim no
    artifact settles, and it is the constraint the phase was given.

    Show the operator, from the sealed evidence file: both subject session ids,
    both pids, both cwds (`<run>/panes/A`, `<run>/panes/B`), and the open order.
    Ask them to confirm:
      1. Both terminals were ones THEY opened for this drill, in this Cursor
         window, and neither was a pane they were already working in.
      2. Both subject panes may now be closed.
    Also show them the before/after size and last line of
    `~/.claude/state/gsd-autorun-ledger.jsonl` so they can see the real ledger
    was not written to.
  </action>
  <verify>
    <human-check>
      The operator confirms both session ids belong to terminals they opened for
      the drill, and that the real ledger is unchanged.
    </human-check>
  </verify>
  <done>
    Operator confirmation recorded in the SUMMARY, naming both session ids. If
    the operator cannot confirm, the run is discarded and re-driven — a drill
    that may have typed into one of the Owner's real sessions is not a pass with
    a caveat, it is a void run.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| drill -> `~/.claude/state/terminal-inbox/` | the one shared dir the drill MUST write to, because `INBOX_DIR` is hardcoded in the extension (extension.js:36). Every real Cursor window with the extension loaded reads it. |
| drill's daemon -> `~/.claude/sessions/` | read-only; the drill copies out, never writes in. |
| drill's daemon -> `~/.claude/state/gsd-autorun-ledger.jsonl` | redirected away by `GSD_LONG_RUN_STATE_DIR`; the real file is the milestone's own acceptance input. |
| drill's daemon -> `~/.claude/hooks/*.flag` | redirected away by `AC_DAEMON_DIR`; the real dir holds the Owner's live flags and the daemon lock. |
| operator -> Cursor terminal | the only path that creates a subject; a mis-click here is what Task 6 exists to catch. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-01-01 | Tampering | `~/.claude/state/gsd-autorun-ledger.jsonl` | high | mitigate | `GSD_LONG_RUN_STATE_DIR=<run>/state`; Task 3's `<done>` compares the real ledger's size and last line before and after. |
| T-01-02 | Tampering | the Owner's live `auto-compact-*.flag` files and the daemon lock | high | mitigate | `AC_DAEMON_DIR=<run>/hooks`; `Get-Flags` scans only `$hooksDir` (daemon:160) and the lock is `$hooksDir/.auto-compact-daemon.lock` (:53), so two daemons cannot contend. |
| T-01-03 | Elevation of Privilege | the drill types into one of the Owner's real sessions | critical | mitigate | `AC_SESSIONS_DIR=<run>/sessions` holds only subjects the drill copied in, so `Resolve-Session` (daemon:300-317) can address nothing else; Task 6 is a blocking human confirmation. |
| T-01-04 | Spoofing | a request in the shared inbox is claimed by the wrong window | medium | accept | This is the mechanism under test, not a defect to mitigate. Requests are keyed `<sid>.req.json` on a throwaway sid (daemon:331) and ownership is decided by pid ancestry (terminal_inbox.js:54-61); a wrong claim would be the drill FAILING, which is a result. |
| T-01-05 | Information Disclosure | the sealed evidence file carries session ids, pids and cwds | low | accept | All three are already world-readable under `~/.claude/`; the file carries no transcript content, only pointers. |
| T-01-06 | Denial of Service | a leftover `.req.json` for a dead sid is re-read by every window every 500 ms | low | mitigate | The extension deletes the claimed file on refuse and send (extension.js:109); the daemon deletes it on fallback (daemon:373). `seal` asserts `~/.claude/state/terminal-inbox/` holds no file bearing a drill sid when the run ends. |
| T-01-SC | Tampering | npm/pip/cargo installs | high | mitigate | Not applicable: this plan installs no package. Every tool used (`python`, the daemon, the extension) is already present. If a task later needs an install, RESEARCH.md carries no `## Package Legitimacy Audit`, so the install must stop and the researcher must run the gate first. |

</threat_model>

<verification>
Run, from the repo root, with the absolute interpreter (Bash is blocked for
these by a PreToolUse guard):

```
& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_two_pane_exactness.py
& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' modules\liveness\reachability.py
& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_autocompact_per_session.py
& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_continuation_transport.py
```

The last two are regression only — this phase must not change the daemon, the
extension or `gsd_long_run.py`, so both must still pass at their existing counts.
If either moves, the phase broke something it had no business touching.

Commits use the absolute git path:
`& 'C:\Program Files\Git\cmd\git.exe' -C 'C:\Users\User\.claude\skills\claude-power-pack' commit -F <msgfile>`
(a message file, never a heredoc — HR-003).

Bracket the two wide suites on the SET of dirty paths before and after: another
session is live in this tree, and a wide oracle whose tree moved mid-run is
INCONCLUSIVE, not a verdict about this phase.
</verification>

<success_criteria>
- `TWOPANE_PASS=6/6`, exit 0, from a cold process reading only the sealed
  evidence and the real artifacts it points at.
- `V-TWOPANE-B-INSTRUMENT-CAN-SEE` passes, so the absence assertion was made by
  an instrument shown able to return the other answer.
- The ledgered `refused` row names a reason from `decide()`'s own vocabulary,
  read from `extension/src/terminal_inbox.js` at gate time.
- All six mutations in Task 4 red exactly the gate they target; restores
  verified by SHA-256.
- `~/.claude/state/gsd-autorun-ledger.jsonl` and `~/.claude/hooks/*.flag` are
  unchanged by the run, and `~/.claude/state/terminal-inbox/` holds no drill sid.
- `vault/lessons/two-pane-exactness-drill.md` lists every unproven item with its
  reason, and claims nothing about `orca-exact`.
- Operator confirmed both subject session ids were panes they opened for the
  drill.
</success_criteria>

<output>
Create `.planning/phases/01-two-pane-exactness-drill/01-SUMMARY.md` when done.
It must record: both subject session ids with pid and procStart, the run id, the
gate's final count, the five mutation results with restore hashes, the operator's
confirmation, and the unproven list verbatim from the lessons file — so the claim
in the summary cannot be larger than the claim in the evidence.
</output>
