# Effective-state closure — 2026-09-02

## Verified reality (read-only, this session)

| Claim | Instrument | Result |
|---|---|---|
| head `4703b45`, pushed | `git rev-parse` / `origin/...` | CONFIRMED, worktree clean (CRLF only) |
| PowerShell majority of command traffic | `measure_command_surface.py --since 2026-08-19` | 72.4% (84 transcripts, 841 MB) — 4th independent figure, same conclusion |
| capture surface still narrow | `capture_liveness.py` | FAIL, both producers NARROW-REGISTRATION |
| migration applied by Owner | live `settings.json` | NOT applied; both matchers still `Bash` |
| corpus still bash-biased | `vault/ceps/events.jsonl` | 103 of 118 events `bash:*` while Bash is 27.6% of traffic |
| dispatcher divergence | `verify_global_mirrors.py` | DRIFT confirmed, exit 5 |

## The finding this session added

The install location **is** a git working tree. `~/.claude/skills/claude-power-pack`
is simultaneously the repo and the directory 11 live hook registrations execute from.
It is currently checked out on `feature/knowledge-acquisition` — another pane's branch.

Measured against the running tree, of the 27 files my 45 commits changed:

    identical 0    diverged 16    absent 11

Both fixes sealed on 2026-08-27 (`PP_PATH` from `__dirname`, quoted-path `leadingExe`)
are absent from the bytes that execute. The live corpus still carries `bash:Program`
rows produced by the unfixed function.

Three branches are unmerged — 45, 41 and 3 commits ahead of a `main` last moved
2026-08-25. Exactly one of them is effective, by accident of checkout.

## Why no gate caught it

`verify_global_mirrors.py` is the estate's parity instrument. Its docstring records
that reading the PP side from the working tree produced false DRIFT when concurrent
panes flipped branches, so it was rebuilt to read **the committed blob on a named ref**
and is documented as branch-flip-immune. The repair for a false positive removed the
only aperture through which this true positive was visible.

`mirror_unpaired_audit.py` already enrolls these files and classes them
`LIVE_FROM_REPO` — "registered by a repo path, and the file is there." Correct, and
silent on *which version* is there. That unexamined half is the gap.

Parity therefore speaks for 24 of 35 registrations. The 11 it cannot speak for are
exactly those whose installed copy is a working tree.

## Mode router (§10)

| # | Workstream | Mode | Why |
|---|---|---|---|
| W1 | Extend `mirror_unpaired_audit` with the version dimension | EXECUTION | known owner, bounded blast radius, reversible |
| W2 | Effective-state gate + tests, wired to the existing `mirror-divergence` row | EXECUTION | established idiom |
| W3 | Re-measure the three forwarded Owner actions; collapse what is now resolvable | EXECUTION | measurement |
| W4 | Seal the trap in UKDL | EXECUTION | prose, no runtime |
| — | Branch integration | HEC | Owner-sovereign; agent must not touch a concurrent pane's branch |

## D2A (§7, §9)

`EXTEND`, not `CREATE`. `mirror_unpaired_audit.py` already owns the denominator and
already resolves which copy is live. Adding a version dimension to its existing
`LIVE_FROM_REPO` class is the tightest fold. In `HR-NOVELTY-001` vocabulary this is
`NEW_SCANNER_OR_GATE` inside an existing owner — the 13-question proof does not apply
and is not claimed.

Rejected: folding into `verify_global_mirrors.py`. Its branch-flip immunity is a
sealed fix for a real false positive; re-introducing working-tree reads there would
undo it (§92, §96). The new property carries its own verdict vocabulary instead.

## Not done, and why

No global mutation. `settings.json` and `~/.claude/hooks/` remain Owner-sovereign
under HR-001. No merge, rebase, reset or checkout touching
`feature/knowledge-acquisition` (§140) — 41 commits of live concurrent work.

## Stop conditions

- Any evidence that the version dimension produces a false positive on a normal
  branch flip → the gate reports, it does not fail, until that is resolved.
- Any need to write outside this worktree → stop, escalate.
