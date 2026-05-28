---
description: Run Omni-Singularity Agent zero-issue audit / status / budget
---

Run the OSA CLI with the supplied arguments.

Recognized flags (mirrors `python -m modules.osa.osa_command`):

- `--audit` -- evaluate triggers, decide whether to wake the agent,
  emit JSON. Does NOT spawn `claude -p` (V1 contract).
- `--status` -- throttle status + top-5 recurring NEVER_AGAIN entries.
- `--budget` -- throttle status only.
- `--never-again [--top N | --query PATTERN]` -- inspect log.
- `--force` -- with `--audit`, bypass triggers (still respects budget).
- `--project NAME` -- override project resolution.

Examples:

```bash
python -m modules.osa.osa_command --status
python -m modules.osa.osa_command --audit --project kobiicraft
python -m modules.osa.osa_command --never-again --top 5
```

Sealed 2026-05-28.
