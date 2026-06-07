---
name: setup-drift
description: Detect when a repo drifts from a captured baseline -- both ProjectProfile field changes AND content changes in key config files (settings.json, CLAUDE.md, package.json, requirements.txt, pyproject.toml). This is repo-CONFIG drift (the gap modules/monitoring does not cover; monitoring is service health). Snapshot once, compare any time.
---

# /setup-drift -- repo-config drift detector

Composes `setup_os.scanner`. Captures a baseline (watched profile fields
+ config-file content hashes), then reports what changed.

## Run

```
# capture a baseline
python -m modules.setup_os.drift_detector --path <repo> --baseline bl.json --snapshot
# later, compare
python -m modules.setup_os.drift_detector --path <repo> --baseline bl.json
```

## Output
- "No drift" when the repo matches the baseline,
- otherwise a list of `[field|file] name: baseline -> current` changes,
- graceful "no baseline" message if the baseline file is absent.
