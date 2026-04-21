# Sleepless QA — Universal Empirical Verification Pipeline

Closed-loop runtime verification for any target repo. The VPS is the arbiter of truth. No feature is "done" until the pipeline has observed it working.

Enforces **Ley 25** (Empirical Evidence Law) — `~/.claude/CLAUDE.md`.

## Architecture

```
Target Repo (web|mc|python|cli)
        |
        v
   Dumper (launches headless runtime, captures evidence)
        |
        v
   EvidenceBundle (screenshots, logs, HTTP responses)
        |
        v
   Verdict Engine (Claude Vision + log patterns + HTTP contracts)
        |
        v
   +---- PASS --------> log + return (feature empirically verified)
   |
   +---- UNCERTAIN ---> desktop notification + silent log + return
   |
   +---- FAIL --------> Healer Orchestrator
                           |
                           +-- pattern_cache hit -> apply fix -> re-verify
                           |
                           +-- pattern_cache miss -> dispatcher_bridge
                                    -> `claude -p <prompt>` in target repo
                                    -> re-verify (retry budget = 3)
```

## Guarantees

1. **Heartbeat canary** — before every verdict, a QR-code decode self-test proves the Claude Vision API is alive. Heartbeat fail → all verdicts that session are voided.
2. **Subprocess isolation** — every target runtime lives in a child process. A segfault in the target never touches the auditor.
3. **Retry budget** — healing loop is hard-bounded at 3 attempts. Fix-break-fix loops are detected via consecutive-diff comparison and aborted as `FIX_LOOP_STUCK`.
4. **UNCERTAIN protocol** — vision confidence < 0.7 never triggers auto-heal. Desktop notification goes to the Owner for manual judgment.
5. **File lock** — only one healing dispatch per repo at a time. Second dispatch queues or fails fast.
6. **Clean-worktree precondition** — healing refuses to run against a repo with uncommitted changes.

## Entry points

```bash
# Self-test (run first, always)
python -m sleepless_qa heartbeat

# Run QA against a repo
python -m sleepless_qa run <repo-path> <action-script.yml> [--runtime-class auto|web|minecraft|python_daemon|cli]

# Inspect a past run
python -m sleepless_qa show <run-id>
```

## Env vars

| Var | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude Vision + healing dispatch. Same key as omnicapture/autoresearch. |
| `VPS_HOST` | For remote deploy context. Not used by the pipeline itself (runs locally on VPS). |
| `QA_STATE_DIR` | Override default `~/.claude/sleepless-qa/`. |
| `MAX_RETRY_BUDGET` | Default 3. Override per-run via CLI `--retry-budget`. |

## VPS deploy

```bash
cd modules/sleepless_qa/vps
cp config.example.env /etc/sleepless-qa.env  # fill values
bash install.sh --dry-run                     # preview
bash install.sh                                # actually install
systemctl enable sleepless-qa.service          # enable on-boot
systemctl start sleepless-qa.service           # start now
```

## Honest limitations (read before trusting verdicts)

- Vision model may hallucinate on low-quality frames. UNCERTAIN path exists precisely for this.
- Playwright adapter requires Chromium deps — `install.sh` handles them on Debian/Ubuntu; other distros may need manual `apt`/`dnf`.
- Mineflayer bot adapter shells out to Node — requires Node 20+.
- Python daemon adapter assumes FastAPI/uvicorn. Other frameworks may work but untested.
- **The pipeline itself has not been dogfooded end-to-end at the time of this README.** The first production run will discover bugs. That is by design — the loop will heal them.

## Governance ties

- **Mistake #47** — Success Hallucination. Any "done" claim on runtime features without a PASS ticket is a violation.
- **Mistake #48** — Zero-Shot Execution. Plans required before code edits touching >1 file.
- **Mistake #49** — Untwinned Feature. Every new feature ships with a `.yml` action script twin.
- **Ley 24** — Priority ladder: Stability > Functionality > Aesthetics > Polish. L4 work blocked while L1 open.
