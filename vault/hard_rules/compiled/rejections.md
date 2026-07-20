# HARD-RULE REJECTION REPORT (compiled artifact)

Compiled 2026-07-20T13:31:22Z.

**13 of 161 rules failed the schema gate.** A rejected rule is not deleted -- it is denied entry to the ACTIVE set. It cannot fire, and it is listed here so it can be repaired or retired.

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

## pp:vault/hard_rules/HARD_RULES.md (6 rejected)

### HR-002 -- Test Critical Bug For Auto-propose Pipeline
- **trigger_is_smoke_fixture** -- TRIGGER is a smoke-test fixture, not a production condition
- **evidence_is_smoke_fixture** -- EVIDENCE cites a smoke-test fixture, not a real incident
  - observed TRIGGER: `Test recognizer for pipeline`
  - observed ACTION: `Run auto_HR-002 proposal drafting`
  - observed EVIDENCE: `[never_again] TEST CRITICAL bug for auto-propose pipeline ZZZ`

### HR-003 -- Ukdl S 2026-05-26
- **trigger_is_heading_scrape** -- TRIGGER is a document heading the generator scraped (a doc title is not an observable condition)
  - observed TRIGGER: `Before: UKDL S+++ 2026-05-26`
  - observed ACTION: `write body to file via Write tool, invoke `git commit -F file` (or `gh --body-file`, `mix run -f`, `node script.js`). Tr`
  - observed EVIDENCE: `[ukdl] UKDL S+++ 2026-05-26`

### HR-004 -- Osa Absorption Tco Context Fix
- **trigger_is_heading_scrape** -- TRIGGER is a document heading the generator scraped (a doc title is not an observable condition)
  - observed TRIGGER: `Before: OSA Absorption + TCO Context Fix UKDL (2026-05-28)`
  - observed ACTION: `UKDL (2026-05-28)`
  - observed EVIDENCE: `[ukdl] OSA Absorption + TCO Context Fix UKDL (2026-05-28)`

### HR-005 -- 2026-05-24 -- Deployment Skill Iteration Log
- **stop_is_table_fragment** -- ACCION/STOP is a markdown table fragment, not an imperative action -- the generator captured the wrong lines
  - observed TRIGGER: `Before initiating any production deploy or release`
  - observed ACTION: `|`
  - observed EVIDENCE: `[session_lessons] 2026-05-24 -- Deployment Skill iteration log`

### HR-006 -- L6 A1a2 Sync Direction Propagates Corruption
- **stop_is_boilerplate** -- ACCION/STOP is generator boilerplate shared verbatim with another rule -- it prescribes nothing rule-specific
  - observed TRIGGER: `Before: L6: A1/A2 sync direction propagates corruption byte-perfectly`
  - observed ACTION: `STOP. Verify preconditions in writing. Document what you are about to do. Get explicit confirmation if any step is irrev`
  - observed EVIDENCE: `[session_lessons] L6: A1/A2 sync direction propagates corruption byte-perfectly`

### HR-007 -- Neveragain 2026-05-29t200643z Claude-power-pack
- **trigger_is_heading_scrape** -- TRIGGER is a document heading the generator scraped (a doc title is not an observable condition)
- **stop_is_boilerplate** -- ACCION/STOP is generator boilerplate shared verbatim with another rule -- it prescribes nothing rule-specific
  - observed TRIGGER: `Before: NEVER_AGAIN — 2026-05-29T20:06:43Z — claude-power-pack — HIGH`
  - observed ACTION: `STOP. Verify preconditions in writing. Document what you are about to do. Get explicit confirmation if any step is irrev`
  - observed EVIDENCE: `[session_lessons] NEVER_AGAIN — 2026-05-29T20:06:43Z — claude-power-pack — HIGH`
