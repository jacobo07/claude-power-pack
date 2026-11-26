# HARD-RULE REJECTION REPORT (compiled artifact)

Compiled 2026-11-26T16:16:11Z.

**7 of 184 rules failed the schema gate.** A rejected rule is not deleted -- it is denied entry to the ACTIVE set. It cannot fire, and it is listed here so it can be repaired or retired.

A rule earns a place in the kill switch by being able to stop the agent: an observable TRIGGER, an imperative ACTION, and a real incident as EVIDENCE.

## global:core/HARD-RULES.md (7 rejected)

### HR-NICHE-BENCHMARK-SOURCED -- every economic field in niche_benchmarks.yaml has an EXTERNALLY-DOCUMENTED source (or the 
- **no_enforceable_form** -- neither a TRIGGER/ACTION block nor an imperative title -- nothing here can fire at a trigger point

### HR-FGR-EMERGENT-HONEST -- the FGR emergent notice tells the Owner the market produced a failure type the system had 
- **stop_missing** -- no ACCION/STOP field
  - observed TRIGGER: `a failure type appears that was not in the priors. emit_emergent_pattern_notices (engines/cbin/failure_genome_registry) `
  - observed EVIDENCE: `2026-06-21 -- the FGR detected emergent patterns (SL-123) but no notification reached the Owner; the event was modelled `

### HR-CBIN-RECOMMEND-OPERATOR-CHOICE -- the CBIN recommendation is a SUGGESTION based on the system's data, never a constraint; it
- **stop_missing** -- no ACCION/STOP field
  - observed TRIGGER: `build_cbin_recommendation (engines/cbin/recommendation) synthesizes WPR+FGR+HGR+CDR+ODR+MSR+CDM+KC for a (niche, market)`
  - observed EVIDENCE: `2026-06-21 -- the 6 CBIN registries were each queryable but the operator had to synthesize "what to do next" by hand; th`

### HR-SEO-TITLE-SERP-OPTIMAL -- **TRIGGER:** authoring or editing any page/post `title` that becomes the `<title>` tag (bl
- **trigger_missing** -- no TRIGGER field
  - observed ACTION: `** STOP if the rendered `<title>` exceeds **60 chars** (target band **50–60**, hard floor **40**). Google truncates >60 `
  - observed EVIDENCE: `** TUA-X blog audit 2026-06-22 found 155/214 served titles >60 chars (avg 68.7, max 120; only 44 in the 50–60 band) emit`

### HR-BLOG-CONTENT-QUALITY-SIGNAL -- **TRIGGER:** publishing dated/auto-generated/high-similarity blog content (weekly digests,
- **trigger_missing** -- no TRIGGER field
  - observed ACTION: `** keep it `noindex` (served + crawlable, OUT of the index/sitemap/grid), NOT deleted and NOT `published:false`. noindex`
  - observed EVIDENCE: `** TUA-X blog 2026-06-25 (SL-blog-noindex-weekly-digests). 20 weekly-intelligence digests (2026-w22..w26 fitness/skincar`

### HR-GEO-EPISTEMIC-HONESTY -- **TRIGGER:** making the landing / public surface "look rigorous to an LLM or operator" — r
- **trigger_missing** -- no TRIGGER field
  - observed ACTION: `** make VISIBLE what is already TRUE, never manufacture rigor. Four sub-rules: (1) **Real mechanism, not the prompt's ex`
  - observed EVIDENCE: `** TUA-X landing GEO/trust sprint 2026-06-25 (SL-landing-geo-trust, branch sprint/landing-geo-trust off main 7036769, FF`

### HR-QA-PLAYWRIGHT-VPS -- **TRIGGER:** any code path that launches a headless browser / Playwright / Chromium for a 
- **trigger_missing** -- no TRIGGER field
  - observed ACTION: `** the browser runs on the VPS (204.168.166.63, host `ubuntu-8gb-hel1`) or GEX44 — NEVER on the Owner's laptop, where a `
  - observed EVIDENCE: `** TUA-X qa-system-vps-playwright sprint 2026-07-10 (SL-115). Built `scripts/qa/` (unified runner + VPS-only visual regr`
