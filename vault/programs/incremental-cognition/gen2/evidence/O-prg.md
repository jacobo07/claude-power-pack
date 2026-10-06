---
pillar: O
plane: gex44
programme: IC-gen2 autonomous-optimization
head: 77e911796da94d2c90a6469a6df3acb8be196082
measured_at: 2026-10-06T21:45:00Z
---

# [O] Product reality: real CLI on the real substrate

Pillar [O] incremental substrate. The product is `tools/usage_index.py population`; the substrate is the cold-built v5
index of the Owner-authorized corpus copy `/home/kobii/kme-corpus/projects`
(`/home/kobii/ao-scratch/p1/cold.sqlite`, 489,816,064 bytes, built by the command in `O-parity-gex44.md`). Denominator `KME-L`
is read by the CLI from `vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json`; no expected number is
typed into any command below. Each run is a fresh `python3` process started from the worktree root on `plane: gex44`,
2026-10-06 ~21:40 UTC, shell exit code taken from `echo exit=$?` straight after the command (stdout redirected to
`/home/kobii/ao-scratch/p1/prg-*.json`, shown in full).

## Green (expected values untouched)

command: `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44` -> exit 0
verdict: `"verdict": "EXACT"`, `"reasons": []`, `"deltas": {}`, population `sessions_active 102, calls 34871, cache_read 11549646300`.

```json
{
 "verdict": "EXACT",
 "reasons": [],
 "host": "gex44",
 "until": 1791044017.0,
 "select": "kme",
 "population": {
  "sessions_active": 102,
  "sessions_dead": 0,
  "calls": 34871,
  "input": 69846,
  "cache_write": 209909403,
  "cache_read": 11549646300,
  "output": 37878881
 },
 "per_project": [
  {
   "project": "C--Users-User-Apps-kme-wt-arena2",
   "sessions_active": 1,
   "sessions_dead": 0,
   "calls": 1,
   "cache_read": 540
  },
  {
   "project": "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files",
   "sessions_active": 101,
   "sessions_dead": 0,
   "calls": 34870,
   "cache_read": 11549645760
  }
 ],
 "reconcile": {
  "archived_excluded": {
   "sessions": 1,
   "files": 1,
   "calls": 649,
   "cache_read": 271001260
  },
  "archived_twins": {
   "sessions": 0,
   "files": 0,
   "calls": 0,
   "cache_read": 0
  },
  "dup_files_in_scope": 0,
  "skipped_shapes": {
   "count": 50,
   "bytes": 2897590,
   "by_shape": {
    "_preserved": 14,
    "_empty_shells": 36,
    "other": 0
   },
   "samples": [
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/0a2b14ee-87e9-4886-848d-2027da82494d.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/198b9c4d-3feb-4828-8f4e-1cfb8bfdcec4.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/56c745d6-1cc9-4ab4-b0f1-875ada2495d7.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/7b7cd78e-8573-4b27-8504-2d079dac59f3.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/87a4a691-1166-4b00-9bbd-d3846616d836.jsonl"
   ],
   "walk_errors": 0
  },
  "unique": {
   "calls": 34853,
   "input": 69810,
   "cache_write": 209540353,
   "cache_read": 11544130372,
   "output": 37858159
  },
  "first_writer": {
   "calls": 34853,
   "cache_read": 11544130372
  },
  "shared_outside": {
   "keys": 0,
   "cache_read": 0,
   "sessions": []
  }
 },
 "secondary": {
  "input": {
   "observed": 69846,
   "expected": 69846,
   "match": true
  },
  "cache_write": {
   "observed": 209909403,
   "expected": 209909403,
   "match": true
  },
  "output": {
   "observed": 37878881,
   "expected": 37878881,
   "match": true
  }
 },
 "deltas": {},
 "plane": "gex44"
}
```

## Red drill 1 (expected `calls` perturbed by +34872)

command: `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44 --perturb calls=34872` -> exit 1
verdict: `"verdict": "DRIFTED"`, `"reasons": []`, population unchanged (`calls 34871`), delta shown:
`"deltas": {"calls": {"expected": 69743, "observed": 34871, "delta": -34872}}` (observed minus expected; the perturbation adds to the
expected value, so the stated expectation 34871 + 34872 = 69743).

```json
{
 "verdict": "DRIFTED",
 "reasons": [],
 "host": "gex44",
 "until": 1791044017.0,
 "select": "kme",
 "population": {
  "sessions_active": 102,
  "sessions_dead": 0,
  "calls": 34871,
  "input": 69846,
  "cache_write": 209909403,
  "cache_read": 11549646300,
  "output": 37878881
 },
 "per_project": [
  {
   "project": "C--Users-User-Apps-kme-wt-arena2",
   "sessions_active": 1,
   "sessions_dead": 0,
   "calls": 1,
   "cache_read": 540
  },
  {
   "project": "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files",
   "sessions_active": 101,
   "sessions_dead": 0,
   "calls": 34870,
   "cache_read": 11549645760
  }
 ],
 "reconcile": {
  "archived_excluded": {
   "sessions": 1,
   "files": 1,
   "calls": 649,
   "cache_read": 271001260
  },
  "archived_twins": {
   "sessions": 0,
   "files": 0,
   "calls": 0,
   "cache_read": 0
  },
  "dup_files_in_scope": 0,
  "skipped_shapes": {
   "count": 50,
   "bytes": 2897590,
   "by_shape": {
    "_preserved": 14,
    "_empty_shells": 36,
    "other": 0
   },
   "samples": [
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/0a2b14ee-87e9-4886-848d-2027da82494d.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/198b9c4d-3feb-4828-8f4e-1cfb8bfdcec4.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/56c745d6-1cc9-4ab4-b0f1-875ada2495d7.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/7b7cd78e-8573-4b27-8504-2d079dac59f3.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/87a4a691-1166-4b00-9bbd-d3846616d836.jsonl"
   ],
   "walk_errors": 0
  },
  "unique": {
   "calls": 34853,
   "input": 69810,
   "cache_write": 209540353,
   "cache_read": 11544130372,
   "output": 37858159
  },
  "first_writer": {
   "calls": 34853,
   "cache_read": 11544130372
  },
  "shared_outside": {
   "keys": 0,
   "cache_read": 0,
   "sessions": []
  }
 },
 "secondary": {
  "input": {
   "observed": 69846,
   "expected": 69846,
   "match": true
  },
  "cache_write": {
   "observed": 209909403,
   "expected": 209909403,
   "match": true
  },
  "output": {
   "observed": 37878881,
   "expected": 37878881,
   "match": true
  }
 },
 "deltas": {
  "calls": {
   "expected": 69743,
   "observed": 34871,
   "delta": -34872
  }
 },
 "plane": "gex44"
}
```

## Red drill 2 (selection that matches nothing)

command: `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter '^no-such-project$' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44` -> exit 3
verdict: `"verdict": "UNMEASURED"`, reason `"no file in scope"`, `"population": null` (a refused answer carries no number that
could be read as zero), `"per_project": []`.

```json
{
 "verdict": "UNMEASURED",
 "reasons": [
  "no file in scope"
 ],
 "host": "gex44",
 "until": 1791044017.0,
 "select": "kme",
 "population": null,
 "per_project": [],
 "reconcile": {
  "archived_excluded": {
   "sessions": 0,
   "files": 0,
   "calls": 0,
   "cache_read": 0
  },
  "archived_twins": {
   "sessions": 0,
   "files": 0,
   "calls": 0,
   "cache_read": 0
  },
  "dup_files_in_scope": 0,
  "skipped_shapes": {
   "count": 50,
   "bytes": 2897590,
   "by_shape": {
    "_preserved": 14,
    "_empty_shells": 36,
    "other": 0
   },
   "samples": [
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/0a2b14ee-87e9-4886-848d-2027da82494d.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/198b9c4d-3feb-4828-8f4e-1cfb8bfdcec4.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/56c745d6-1cc9-4ab4-b0f1-875ada2495d7.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/7b7cd78e-8573-4b27-8504-2d079dac59f3.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/87a4a691-1166-4b00-9bbd-d3846616d836.jsonl"
   ],
   "walk_errors": 0
  },
  "unique": {
   "calls": 0,
   "input": 0,
   "cache_write": 0,
   "cache_read": 0,
   "output": 0
  },
  "first_writer": {
   "calls": 0,
   "cache_read": 0
  },
  "shared_outside": {
   "keys": 0,
   "cache_read": 0,
   "sessions": []
  }
 },
 "observed_partial": {
  "sessions_active": 0,
  "sessions_dead": 0,
  "calls": 0,
  "input": 0,
  "cache_write": 0,
  "cache_read": 0,
  "output": 0
 },
 "plane": "gex44"
}
```

## Reading

The same real CLI on the same real substrate returns EXACT (exit 0) when the corpus matches the frozen record, DRIFTED
(exit 1) with the named per-field delta when an expectation is wrong by one field, and UNMEASURED (exit 3) with a reason
and no population number when the selection is empty. The three answers are distinct exit codes; UNMEASURED is never EXACT
and never zero.
