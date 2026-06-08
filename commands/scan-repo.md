---
name: scan-repo
description: Run the CPP Setup OS Project Intelligence Scanner on a repo. Builds a read-only ProjectProfile from disk (language, framework, package manager, test runner, CI, Docker, external APIs, existing Claude config, secret-sensitive files, readiness score) where every field carries its detection source -- no inference presented as fact. The repo on disk is the source of truth. Pillar 1 of the Setup OS.
---

# /scan-repo -- Project Intelligence Scanner

## What it does

Profiles a repo before any automation is recommended. Read-only, one
bounded directory walk, stdlib-only. Each field reports its detection
source (`detected_from_file` / `_config` / `_command` /
`inferred_from_structure` / `missing` / `unknown`).

## Run

Works from ANY cwd (the scanner bootstraps the PP repo onto sys.path), so you
can profile the repo you are currently in:

```
python -m modules.setup_os.scanner --path .               # human summary
python -m modules.setup_os.scanner --path . --json        # full profile
python -m modules.setup_os.scanner --path . --save        # persist to registry
```

`--save` writes the ProjectProfile to the Setup-OS registry in the PP repo
(`vault/setup_os/profiles/<slug>_<pathhash>.json`, keyed by the repo's resolved
path — never written into the scanned repo). Once saved, the cross-repo
`pp-setup-scan` signal stays silent for that repo (it stops nudging you to scan).

## Output
- A one-line profile summary + a `setup_readiness_score` (0-100).
- Notes for risks (e.g. secret-sensitive files without `.env.example`).

Feed the profile into `/analyze-roi` for ranked recommendations.
