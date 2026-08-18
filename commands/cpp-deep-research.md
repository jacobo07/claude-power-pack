---
name: cpp-deep-research
description: Recursive web research agent (Claude Power Pack). Spawns a detached background process that does breadth-first SERP search + page extraction + Claude-driven learning aggregation + multi-page markdown report generation. Output lands at vault/research/<ts>_<slug>.md and is auto-discovered on the next SessionStart. Use for any prompt that begins with "investiga", "research", "deep dive", "compara X vs Y", or any open-ended question that benefits from current web sources. Triggers also via the Stop-hook intent detector when a prompt matches the research-signal regex and is >=80 words.
---

# /cpp-deep-research — Recursive Web Research Agent

## What it does

Reverse-engineered Python implementation of a recursive deep-research
algorithm (n8n source workflow is reference material only — see
`vault/specs/deep-research-agent.md` and `memory/feedback_no_n8n_ever.md`).

The agent runs **detached** so the Owner never blocks waiting:

1. **Engine 1 — decomposition.** Split the prompt into sub-questions tagged
   by the axis each attacks (evidence / mechanism / boundary /
   counterexample / transferability). Gated: the accepted set must span
   ≥3 distinct axes, else one corrective re-ask. Every question also
   passes the natural-question gate (no keyword soup).
2. For each question: web_search (DuckDuckGo → Brave → Apify cascade) →
   top 5 organic → fetch each page → HTML→markdown (trafilatura →
   readability → bs4 → regex cascade).
3. **Engine 2 — landscape coverage.** Classify every page that actually
   parsed into a source family; compute the verdict for the question.
   Load-bearing families are re-ordered to be read first, so the
   extraction budget is not eaten by the vendor page.
4. **Engine 3 — capability + reality extraction.** Up to 3 learnings, each
   carrying the capability it confers, an epistemic level and an evidence
   sentence. Deterministic caps then demote anything the evidence does not
   support.
5. If `depth > 1`: recurse on each follow-up cluster with halved breadth.
6. **Engine 4 — contradiction detection.** Runs once over the full corpus,
   before synthesis. Conflicts are reported unresolved, never settled
   silently.
7. At top level: synthesise into a 3+ page markdown report, carrying the
   `[EPISTEMIC][QUALITY]` tags into the prose, plus cited sources, the
   contradictions section, and the Run metadata footer.

## The four engines (v0.3.0, 2026-08-18)

### Engine 2 — source families

| Family | What it is | Quality |
|---|---|---|
| **A — measured** | case studies, post-mortems, A/B results with real numbers | HIGH (MEDIUM if vendor-hosted: self-reported ≠ independent) |
| **B — academic** | papers, theses, preprints | HIGH |
| **C — practitioner** | first-hand operational reporting, RFCs, standards, engineer writing | MEDIUM |
| **D — vendor** | conversion surfaces — pricing, demos, agency content | LOW — corroborates, never founds |

Landscape verdicts per question:

- `COVERED` — ≥2 load-bearing families. Full epistemic range available.
- `THIN` — exactly 1 load-bearing family.
- `UNCLASSIFIED` — no page resolved to a known family. Extraction proceeds,
  capped at `DERIVED`: failing to classify a page is the classifier's
  shortcoming, not the page's.
- `VENDOR_ONLY` — **refusal.** Every source was positively recognised as
  marketing. Extraction is skipped entirely; nothing is persisted.

### Engine 3 — epistemic levels

`OBSERVED` > `VERIFIED` > `DERIVED` > `HYPOTHESIS` > `REJECTED`.

The extractor proposes; deterministic gates dispose. Every cap only ever
degrades — an unknown label, a malformed field, or an unreadable value costs
confidence and can never buy it:

- `OBSERVED` without a quantity a regex can find → `DERIVED`
- `VERIFIED` on fewer than 2 supporting sources → demoted
- claimed `supporting_sources` is capped at the number of documents fetched
- `UNCLASSIFIED` landscape → capped at `DERIVED`
- `VENDOR_ONLY` landscape → `REJECTED`, dropped, logged

Stored learnings lead with their labels:
`[VERIFIED][HIGH] <insight> — Capacidad: <decision it changes> — Evidencia: <why>`

## Args

| Arg | Default | Meaning |
|---|---|---|
| `<prompt>` | required | The research prompt (free text) |
| `--depth N` | `2` | Recursion depth, 1..5. Depth 1 = 15 min, Depth 2 = 45 min, Depth 3 = 2 h. |
| `--breadth N` | `3` | Queries per level, 2..5. Halved on each recursive call. |
| `--clarify` | off | Ask 3 follow-up questions FIRST (printed to stderr); Owner re-prompts manually. |
| `--out DIR` | `vault/research/` | Output directory override. |
| `--quiet` | off | Suppress progress chatter on stderr. |

## Output

For every run, three files land in `vault/research/`:

1. **`<YYYY-MM-DD_HHmmss>_<slug>.md`** — markdown report:
   - LLM-generated body (3+ pages)
   - `## Sources` — every URL discovered (deduped, ordered)
   - `## Run metadata` — depth, breadth, queries used, layers fired
     (e.g. "ddg + trafilatura + claude.exe"), duration, errors logged

2. **`index.json`** — JSONL append (one row per run): timestamp, slug,
   prompt, depth/breadth, learning_count, source_count, duration_s,
   layers used, errors count, URL sample for dedup-on-rerun.

3. **`<slug>.raw.jsonl`** — per-query forensic trace.

## Activation

**Manual**: type `/cpp-deep-research <prompt>` in any pane. The agent
spawns detached via `cmd.exe /c start "" /B python deep_research.py ...`
and returns control to the Owner in < 1 s. Progress is observable via
`vault/research/.deep-research.lock` (PID + start time).

**Automatic (sleepy)**: the Stop-hook `hooks/research-intent-detector.js`
fires on every assistant turn. If the LAST user prompt:
- matches the regex `\b(investiga|investigate|research|analiza|analyse|compara|compare|deep[-\s]?dive|qué\s+opciones|how\s+does|how\s+do|mercado\s+de)\b`, AND
- is >=80 words OR contains >=3 question marks,

the agent spawns automatically. Logged to
`vault/research/.auto-spawned.log`.

## Constraints

- **No fabricated URLs**: if every SERP layer fails AND no API keys are
  set, the run aborts and writes `vault/cache_hints/CEILING.md`. The
  agent never invents links to look productive.
- **Single-instance lock** at `vault/research/.deep-research.lock`
  prevents concurrent runs from piling up. 4-hour stale-reclaim.
- **IDLE_PRIORITY_CLASS** on Windows so the agent yields to interactive
  work.
- **Query budget**: hard cap at 30 SERP queries per run (override via
  `CLAUDEPP_DEEPRESEARCH_MAX_QUERIES`).
- **Runtime ceiling**: 2 h wall-clock (override via
  `CLAUDEPP_DEEPRESEARCH_TIMEOUT_S`).
- **Opt-out**: set `CLAUDEPP_DEEPRESEARCH_DISABLE=1`. Sleepy auto-spawn
  is skipped; manual invocation still works.

## Environment

| Var | Effect |
|---|---|
| `CLAUDEPP_DEEPRESEARCH_DISABLE` | `1` to skip the sleepy auto-spawn |
| `CLAUDEPP_RESEARCH_MODEL` | Override Claude model (default Sonnet) |
| `BRAVE_API_KEY` | Enables Brave search fallback (layer 2) |
| `APIFY_TOKEN` (or legacy `APIFU_API_KEY`) | Enables Apify fallback (layer 3) |
| `ANTHROPIC_API_KEY` | Enables anthropic SDK LLM fallback (layer 2) |

## Examples

```
/cpp-deep-research best practices for Minecraft Java servers in 2026
/cpp-deep-research --depth 3 --breadth 4 Folia vs Paper production-readiness 2026
/cpp-deep-research --clarify  qué arquitectura de hosting Minecraft escala mejor con 1000 jugadores
```

## Empirical verification (V1, 2026-05-23)

`--prompt "best practices for Minecraft Java servers in 2026" --depth 1 --breadth 2`
produced a 16.9 KB report with 6 learnings + 8 real URLs (github,
low.ms, gameserver.rentals, dedicatedminecraft.host, supercraft.host,
feedly, youtube, reddit) in 220 s. All cascade layers fired primary
(ddg + trafilatura + claude.exe) with no API keys. CLI exit 0.

## Cross-references

- Spec: `vault/specs/deep-research-agent.md` (13 sections including
  the 5 verbatim LLM prompts from the n8n source)
- Plan: `vault/plans/deep-research-agent-2026-05-23.md`
- Module: `modules/deep-research/deep_research.py`
- Sleepy spawn: `hooks/research-intent-detector.js` (Stop hook)
- Heavy-IO governance: `vault/lessons/heavy-io-must-be-governed.md`
- Forbidden runtime: `memory/feedback_no_n8n_ever.md` (n8n is banned;
  this skill is the Python replacement)
