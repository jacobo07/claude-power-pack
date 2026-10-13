# NOTICE — vendored componentry source

- **Upstream:** https://github.com/harshjdhv/componentry (site: https://componentry.dev)
- **Commit:** `b602c2872fea85c9f2464016ce3bbe0af17b51b4` (main, pushed 2026-10-12)
- **License:** MIT, Copyright (c) 2026 Harsh Jadhav (see `LICENSE`). The MIT notice must
  travel with any copy of these files, including a copy pasted into a client project.
- **Vendored, byte-identical to upstream:** `LICENSE`, `README.md`, the whole
  `packages/ui/` package (64 `.tsx` components, `src/lib/`, `src/styles/globals.css`,
  package and tool config), and `apps/web/registry/index.ts` (upstream's own catalogue,
  read to discover the 54 published components). Not vendored: the website app, preview
  videos, the `blocks/` pricing and hero blocks, scripts, tests and the shadcn registry
  build output.
- **Absorbed:** 2026-10-13 into CDIO as the source material of
  `../CDIO-11-componentry-catalog.md`.

## Rules for this directory

1. **Do not edit the files here.** They are the upstream text. Copy a component into the
   project being built and change the copy. To update, re-vendor from upstream at a new
   commit, change `UPSTREAM_COMMIT` in `modules/cdio/componentry_catalog.py` and the commit
   line above in the same change, then run `python -m modules.cdio.componentry_catalog build`.
2. **`catalog.json` is generated.** It is written by the scanner, never by hand, and
   `tools/test_cdio_componentry.py` fails when it differs from what the scanner produces.
3. **These files are not type-checked or linted here.** This repo has no TypeScript
   toolchain; the source is evidence for the catalogue, not a build input.
4. **Using a component is not adopting its claims.** Upstream describes its components as
   polished. CDIO-11 records, per component, what the source does and does not do against
   the CDIO-07 floors. Read the component's `visual-patterns/componentry-<slug>.md` entry
   and clear its "Antes de usar" list first.
