# Parallel Mesh — Hub Wiring (Owner-side)

The mesh's Python half is shipped and tested (PM-01..PM-05, 26/26). Activating it
in the live session flow needs a few shell-out lines added to the SessionStart /
Stop hooks. These are **Owner-side** edits: auto-mode does not modify the live
`~/.claude/hooks/session_start_hub.js` (HR-001). Nothing below blocks a session —
every call is advisory and fail-open.

Let `PP="$HOME/.claude/skills/claude-power-pack"` and `CWD` = the launch dir.

## SessionStart — inject light context (Brain + Bus + Budget mode)

Add these three shell-outs; pipe their stdout into the hub's `additionalContext`:

```
# 1. Repo Shared Brain (PM-01): show the existing brain if present (empty if not).
python "$PP/modules/parallel_mesh/pm_01_brain.py" --repo "$CWD" --show

# 2. Findings Bus digest (PM-03): topics other panes already discovered.
python "$PP/modules/parallel_mesh/pm_03_bus.py" --repo "$CWD" --digest

# 3. Concurrency mode (PM-04): current Green/Yellow/Red/Black from real burn.
python "$PP/modules/parallel_mesh/pm_04_auction.py" --repo "$CWD"
```

The agent generates/refreshes the Brain on demand (it owns the expensive repo
scan); the hook only *shows* what exists so a launching pane consults before
re-reading the repo.

## Stop — publish this session's findings (Cross-Pane Commit, PM-03)

During work, publish a reusable conclusion the moment it is reached:

```
python "$PP/modules/parallel_mesh/pm_03_bus.py" --repo "$CWD" \
  --publish --topic "<short topic>" --claim "<the reusable conclusion>" \
  --evidence "<file:line or cmd>" --sid "<session id>"
```

Or, from a Stop hook that has collected the session's findings as a list of
`{topic, claim, evidence}` dicts, call
`modules.parallel_mesh.pm_03_bus.publish_session_findings(cwd, findings, sid=...)`.

## Intent + budget gates (PM-02 + PM-04) at launch

`kclaude` already runs CO-08's cap. To enable the recalibrated scope-gate, a pane
declares its intent first, then admission is scope-gated:

```
# declare (once, at launch): scope = comma-separated files the pane will touch
python "$PP/modules/parallel_mesh/pm_02_intent.py" --sid "<sid>" --cwd "$CWD" \
  --declare --scope "modules/x.py,tools/y.py" --objective "feature X"

# admission check (undeclared -> blunt CO-08 cap; declared -> scope-gate):
python "$PP/modules/parallel_mesh/pm_02_intent.py" --sid "<sid>" --cwd "$CWD" \
  --scope "modules/x.py,tools/y.py"
```

Gate order (all advisory, all fail-open): **scope (PM-02) → budget (PM-04) →
the sealed CO-00/CO-08 wrapper enforcement**.

## Honest note (CO-10)

Every surface above is a shell-out reading/writing **files on disk** — not IPC
between Claude instances. A finding published by one pane is seen by another only
at that other pane's next SessionStart. That latency is the honest cost of a
file-based mesh; nothing here promises live pane-to-pane messaging.
