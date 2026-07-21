# Institutional Extraction — CCF Phase 1

> Extracted from `REVERSE_ENGINEERING_REPORT.md` (Phase 0). Labels carried forward:
> **EXTRACTED** / **INFERRED** / **GENERALIZED** / **NOVEL**.

## A. Creative Workflow Patterns (universal, domain-independent)

| Pattern | Label | Description |
|---|---|---|
| Config-driven fan-out | GENERALIZED | One config file enumerates N variant specs; a script expands it into N independent generation jobs. Domain-independent — works for logos, UI layouts, deck slides, anything with an enumerable variant axis. |
| Showcase-then-pick | GENERALIZED | All N variants render onto one comparison sheet before any is developed further. The showcase is cheap (one shared layout script); depth is expensive (Phase 2) and reserved for the single picked item. This is the load-bearing human-in-the-loop gate — see F. |
| Deterministic finisher, stochastic generator | EXTRACTED→GENERALIZED | The stochastic step (model call) is isolated to exactly one stage; every stage before and after it (config parsing, HTML assembly, PDF printing) is a deterministic script with no model call. This bounds where non-reproducibility can enter the pipeline. |
| Same-source multi-render via symbolic recolor | EXTRACTED, brand-specific | SVG `<symbol>` + CSS custom properties produce on-white/on-green/mono variants from one path set. Generalizes to any vector-based visual identity; does NOT generalize to raster-only or non-vector domains (UI screenshots, presentation slide images). |
| Zero-dependency build chain | GENERALIZED | config → plain script → HTML → headless-browser-print-to-PDF, no PDF library, no design-tool SDK. Any domain that needs a print-ready or shareable document artifact can reuse this shape verbatim (see `CCF_ARCHITECTURE.md` Artifact Compiler). |
| Named-entity avoidance ≠ semantic avoidance | EXTRACTED, universal risk | A text-based "don't do X" instruction only catches what it names. Any generation domain with a collision risk (trademark, plagiarism, protected likeness, copyrighted style) inherits this same gap unless a separate semantic check exists. |

## B. Failure Corpus Seed

| failure_id | Description | Root cause | Signal | Detectable? | Recovery | Recurrence risk |
|---|---|---|---|---|---|---|
| **CCF-F01 — Trademark Collision Failure** (founding failure) | Concept "Thread" rendered as a near-identical copy of Airbnb's Bélo mark | The icon description ("a continuous rounded line that loops back on itself") is effectively a textual description *of* the competitor's mark, not an original concept; the `avoid` field only bans explicitly *named* marks | Visual similarity to a well-known mark, invisible in the config/prompt text itself | **Yes, but not by the existing tool** — requires a dedicated visual/semantic similarity check (see Phase 2 §7) | Human/Claude re-reads the generated sheet and manually re-specs the icon prompt with an explicit named ban, then retries | **HIGH** — any sufficiently generic icon description ("rounded line," "interlocking shapes," "abstract bird") risks re-deriving a known mark; this is structural, not a one-off |
| CCF-F02 — Empty-shell PDF footgun | `to-pdf.mjs` rebuilds every company in `config.json` regardless of whether PNGs exist for it, producing tiny (~57KB) content-free PDFs | No existence check before the build step | File size far below expected (~57KB vs 4.7MB with imagery); no error raised | Yes — trivial existence check | None automatic; user must notice small file size | MEDIUM — silent by design until someone opens the file |
| CCF-F03 — Total provider lock-in | Only `gpt-image-2` is wired; no fallback path if the provider errors, rate-limits, or is deprecated | No provider abstraction in `generate.mjs` | API error / outage | Yes, at generation time | None — pipeline simply fails | MEDIUM — single point of failure, not yet observed to trigger, but structural |
| CCF-F04 — Unbounded serial cost/latency | ~90s per image call, no parallelization observed; N companies × 6 concepts scales linearly with wall-clock | Sequential design, no fan-out in `generate.mjs` | Wall-clock time | Yes, measurable directly | None — user waits | LOW at small scale (1 company), HIGH at the "100+ brands" scale the CCF spec targets |

## C. Decision Corpus Seed

| Decision | Alternatives considered | Reason for choice | Would change if... |
|---|---|---|---|
| Use OpenAI `gpt-image-2` over Claude-native SVG/image generation | Claude generating SVG path data directly; Claude Design | GPT-image-2's text rendering and creative range for logos observed to be materially better ("the creativity that Claude has is not really a match") | A future Claude image model closes this specific gap — this is an evidenced, revisitable call, not dogma |
| Build script over design-tool/PDF-library dependency | Puppeteer wrapper libraries, a PDF-generation package, a design-tool plugin | Zero dependencies, reuses whatever Chrome is already installed, keeps the repo trivially portable | A target environment lacks any headless-Chrome-capable runtime |
| One image call per concept, no auto-regenerate loop | Auto-critique-and-retry per concept before showing the user | Keeps cost/latency bounded and predictable; treats human/Claude review of the finished sheet as the correction point instead of an automatic loop | The trademark-collision gap (CCF-F01) is closed by a pre-generation semantic check — see Phase 2 §7 — at which point a bounded auto-retry becomes safe to add |
| SVG `<symbol>` + CSS-variable recolor over separate hand-edited variant files | Manually authoring on-white/on-green/mono as separate assets | Single source of truth; recolor is "free" once the symbol exists | Never, for vector-based identity — this is a strict improvement with no observed downside |
| Manual PNG→SVG + Vectorpea step, not scripted | A scripted vectorization step (e.g. potrace) | Not stated by the creator — INFERRED to be "good enough, external tool already free," not evidence of a considered tradeoff | This is the clearest NOVEL opportunity: scripting this step removes the only fully-manual, un-versioned step in the whole chain |

## D. Quality Heuristics

**Objective (verifiable without a human):**
- Wordmark spelling matches config `spelled` field exactly.
- Named marks in `avoid` do not appear.
- Output resolution/format matches spec (1536×1024, PNG; A4 PDF page geometry).
- PDF page count and file size are within expected bounds for the number of images actually present (closes CCF-F02).
- **NEW, not present in the reference repo, required by CCF**: trademark/visual-similarity score against a known-marks reference set is below threshold (closes CCF-F01).

**Subjective (requires human judgment):**
- Which of the 6 concepts best fits the brand.
- Whether a recolor variant reads correctly against a given background.
- Whether typography pairing (display/heading/body/label) feels coherent as a system, not just individually correct.

## E. Automation Opportunities, Ranked by ROI

Given the real cost profile (~90s/call, single provider, no parallelization):

1. **Existence-check before PDF rebuild (CCF-F02 fix)** — near-zero cost to implement, eliminates a silent, confusing failure mode. Highest ROI: trivial effort, real bug closed.
2. **Semantic trademark/similarity scan (CCF-F01 fix)** — highest *value* (closes the founding failure, avoids real legal exposure) but non-trivial to build (needs a reference-mark corpus and a similarity method, not just string matching). Second-highest priority because of severity, even though effort is higher than #1.
3. **Scripted PNG→SVG vectorization** — removes the one fully-manual, external-tool-dependent step; moderate effort (a tracer library), moderate value (mostly convenience/reproducibility, not correctness).
4. **Parallelized concept generation** — only pays off at the "100+ brands" scale the CCF is meant to serve; not worth building for a single-brand workflow, but blocking for the institutional-platform framing.
5. **Provider fallback (CCF-F03 fix)** — lowest immediate ROI; the failure has not been observed to trigger yet, and a second provider adapter is real engineering cost. Worth specifying the interface now (Model Adapter Layer, Phase 2 §4) without necessarily implementing a second provider on day one.

## F. Human-Irreducible Points

- **Concept selection** — picking 1 of 6 generated logo concepts. This is the clearest, most directly evidenced human-irreducible gate in the entire corpus: the whole two-phase structure (cheap showcase, expensive deepen-one) exists specifically to defer this choice to a human before any further cost is spent. Automating this away would collapse the pipeline's central safety valve, not just remove a step.
- **Final "verified page by page" brand-kit review** — Claude's own stated practice; a generated multi-page document being internally consistent is a judgment call about the *system* reading coherently, not a per-field check.
- **Trademark-collision WARN acknowledgment** — even once a semantic scanner exists (Phase 2 §7), a WARN verdict (as opposed to a hard BLOCK on high-confidence collision) should require an explicit human sign-off before release, not a silent pass-through — the Airbnb case shows how easily a collision can be unintentional and how costly it would be to ship unnoticed.
