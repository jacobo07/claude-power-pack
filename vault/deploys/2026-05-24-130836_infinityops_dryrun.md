# Deploy receipt -- infinityops / prod (V-DEEP self-test, dry-run)

- Timestamp (UTC): 2026-05-24-130836
- HEAD: (head_sha resolution skipped -- git not on PowerShell -NonInteractive PATH on this host; live deploys via PP from a shell that has git on PATH will populate this)
- Duration: 0 ms (dry-run path is detector + planner only)
- Mode: gh-workflow
- Detection evidence: workflow file: .github\workflows\deploy-vps.yml
- Doctrine cite: §77 Deploy Sovereignty -- the workflow at .github\workflows\deploy-vps.yml is the canonical CD pipeline. This runner INVOKES it via the gh API; it does not replace it.

## 1. Mode detected

```json
{
  "mode": "gh-workflow",
  "evidence": "workflow file: .github\\workflows\\deploy-vps.yml",
  "config_path": null,
  "workflow_file": "C:\\Users\\User\\Desktop\\Cursor Projects\\InfinityOps\\.github\\workflows\\deploy-vps.yml",
  "remote": null
}
```

## 2. Runner verdict

- verdict: dry-run
- ok: true
- summary: gh-workflow dry-run for deploy-vps.yml
- §77 cite emitted to stdout: yes (verified empirically; the runner's first action on detection of `deploy-vps.yml` is to print the citation; this is a non-negotiable invariant per spec §9)

## 3. Receipt (planner output)

```
DRY RUN -- would invoke: gh workflow run deploy-vps.yml --ref main
DRY RUN -- then: gh run watch --exit-status (poll until terminal state)
DRY RUN -- workflow file: C:\Users\User\Desktop\Cursor Projects\InfinityOps\.github\workflows\deploy-vps.yml
DRY RUN -- doctrine: §77 Deploy Sovereignty -- the workflow at .github\workflows\deploy-vps.yml is the canonical CD pipeline. This runner INVOKES it via the gh API; it does not replace it.
```

## 4. Healthcheck

```
(dry-run path does not execute healthcheck -- it would run only after a real `gh run watch --exit-status` returned 0)

For reference, the configured healthcheck for infinityops is:
{
  "kind": "curl-grep",
  "url": "https://infinityops.ai/",
  "grep_pattern": "br.jula",
  "retries": 24,
  "delay_sec": 15
}
```

## V-DEEP empirical evidence

This receipt is the artefact of P12 in the Deployment Skill plan
(`vault/plans/deployment-skill-2026-05-24.md`). It captures the
following empirical facts:

1. The detector picked `gh-workflow` (the first-priority mode) on the
   real InfinityOps repo at `C:\Users\User\Desktop\Cursor
   Projects\InfinityOps`.
2. The runner identified the workflow as the `deploy-vps.yml`
   canonical pipeline and emitted the §77 Deploy Sovereignty
   citation to stdout AND in the JSON verdict's `doctrine_cite`
   field.
3. The dispatcher correctly refused to write a permanent report
   under `vault/deploys/` because the run was a dry-run. The
   present file is a manually-curated V-DEEP artefact; the
   automated receipt-writer is engaged only on non-dry-run runs.
4. The healthcheck spec was loaded from
   `vault/deploy/infinityops.json` (PP source, via `config_override`),
   confirming the schema requirement is met for a real run.

## Reality contract reaffirmed

- A deploy is **not** complete until a real healthcheck passes. This
  dry-run executes nothing on the live target; no claim of deployment
  is implied by this artefact.
- The skill never pushes to the canonical origin remote. The Owner
  pushes to origin separately, then `/deploy` invokes the CD pipeline.
- The §77 citation is mandatory. Its absence in a real run would be
  a defect; its presence here is the proof the invariant holds.
