# NOTICE — vendored legal templates

- **Upstream:** https://github.com/General-Legal/legal-templates
- **Commit:** `6d6805425eabd41bed86fc1e2ec51612760f716c` (2026-09-22)
- **License:** CC0 1.0 Universal (see `LICENSE`). No attribution is legally required.
- **Vendored:** `templates/` (12 templates, `template.md` + some `README.md`), `LICENSE`,
  `README.md`, byte-identical to upstream. Not vendored: `docx-originals/` and `scripts/`.
- **Absorbed:** 2026-10-08 into CDIO as the source material of
  `../CDIO-10-legal-surface.md`, which decides when each template is used.

## Rules for this directory

1. **Do not edit the templates here.** They are the upstream text. Fill a copy inside the
   website being built. To update, re-vendor from upstream at a new commit and change the
   commit line above in the same change.
2. **Keep the General Legal credit footnote** in pages built from these templates. CC0 does not
   require it; the authors ask for it, and keeping it costs nothing.
3. **Filled fields are facts.** Company name, address, email, dates, vendors and jurisdiction
   come from the Owner or the client. A field nobody supplied stays visibly unfilled, and
   `python -m modules.cdio.legal_surface check` blocks the site until it is filled.
4. **These templates are drafted for a U.S. company.** For a business in Spain or the EU, read
   CDIO-10 sec. 4 before using them; several required documents have no template here.
5. **Not legal advice.** A page built from these templates is not reviewed by a lawyer because
   the template was. Nothing built here may claim it was.
