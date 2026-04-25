# vendor/

Adapter staging ground. Third-party skills wrapped by Power-Pack live here when they need to be physically present on disk.

## Rule 1 — Composition, not modification

Power-Pack does **not** fork upstream sources. If you need behaviour from someone else's skill:

1. The skill stays in its own repository, installed by the user via its own installer.
2. Power-Pack ships a thin adapter at `lib/adapters/<upstream-name>.js` that calls the upstream binary or imports the upstream module.
3. If a copy *must* live in this repo (e.g. license requires bundled redistribution, or the upstream isn't installable), it goes under `vendor/<upstream-name>/` with its **original** LICENSE file untouched.

Forking, patching in place, or stripping attribution is a Reality Contract violation and will be rejected at commit time.

## Rule 2 — License before code

Every adapter's first line of work is `node lib/license_gate.js <path-to-upstream>`. The output is recorded in `NOTICE.md` and surfaced by the installer so the human knows what they are pulling in.

The gate **classifies**, it does not block. The human decides whether AGPL or a custom EULA is acceptable for their use case.

## Rule 3 — One adapter, one entry point

Each adapter exports a single function that takes a Power-Pack input shape and returns a Power-Pack output shape. The adapter owns the translation; the rest of the pack does not learn the upstream's API. This keeps blast radius small if an upstream changes its CLI.

## Layout

```
vendor/
  NOTICE.md          # rolling attribution log; appended to per adapter
  README.md          # this file
  <upstream>/        # only if a physical copy is required
    LICENSE          # original, never edited
    SOURCE.txt       # commit hash + URL of the snapshot taken
    ...
```

## What's currently here

Nothing. `vendor/` exists as a structural slot; populated only when an adapter explicitly needs a physical bundle. See `vault/plans/SOVEREIGN_ADAPTER_PLAN.md` for the active adapter ladder.
