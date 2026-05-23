---
title: Deep Research Agent — Technical Specification
date: 2026-05-23
status: PASO-0 (reverse-engineered, awaiting Accept before code)
source_material: Downloads/Prebuilt AI Agents/5000 N8N workflows/.../Pack2/AI_Research_RAG_and_Data_Analysis/Host Your Own AI Deep Research Agent with n8n, Apify and OpenAI o3.json
deliverable_path: claude-power-pack/modules/deep-research/deep_research.py
language: Python 3.10+
forbidden_runtimes: n8n (per feedback_no_n8n_ever, 2026-05-23)
---

# Deep Research Agent — Technical Specification

## 1. Origin + restated objective

This module is a **Python reverse-engineering** of a community n8n workflow
("Host Your Own AI Deep Research Agent with n8n, Apify and OpenAI o3"). The
n8n JSON is **source material only** — it documents the algorithm + verbatim
prompts. The deliverable is pure Python; n8n is forbidden as a runtime per
`feedback_no_n8n_ever.md`.

The agent performs **recursive, breadth-first web research** on a user prompt,
extracting learnings from real SERP results, recursing on follow-up questions,
and producing a markdown report with cited URLs. It runs as a **sleepy
background agent** so the Owner never blocks waiting — the report lands at
`vault/research/<ts>_<slug>.md` and is auto-discovered on the next
SessionStart.

## 2. Algorithm (extracted from the n8n graph)

```
deep_research(prompt, depth, breadth, learnings=[], urls=[])
  └─ generate_serp_queries(prompt, breadth, learnings)
        → [{query, researchGoal}, ...] up to `breadth` items
     for each {query, researchGoal} in queries (parallelisable):
         results       ← web_search(query)                  # ≤ 10 SERP hits
         top5          ← filter(results, type == "normal")[:5]
         pages         ← [fetch_page(r.url) for r in top5]   # HTML
         markdowns     ← [html_to_markdown(p)[:25_000] for p in pages]
         {new_learnings, follow_ups} ← extract_learnings(query, markdowns)
         learnings.extend(new_learnings)
         urls.extend(r.url for r in top5)
         if depth > 1:
             sub_prompt = (
                 f"Previous research goal: {researchGoal}\n"
                 f"Follow-up research directions: " +
                 "\n".join(follow_ups)
             )
             deep_research(sub_prompt, depth - 1,
                           max(1, breadth // 2),    # halve breadth on recurse
                           learnings, urls)
     if at_top_level:
         return generate_report(prompt, learnings, urls)
```

Three exits:
- **At top level**: write the markdown report + URL list.
- **`depth == 1`**: still extract learnings but do NOT recurse (leaf nodes).
- **`web_search` returns 0 organic results**: log + continue with empty
  learnings for that query (do NOT abort the whole run).

## 3. Verbatim prompts (the IP)

All four LLM-call prompts are extracted byte-for-byte from the source
workflow. Templating uses Python `string.Template` or f-strings (the n8n
`{{ ... }}` becomes Python interpolation).

### 3.1 Shared system message (every LLM call)

```
You are an expert researcher. Today is {today}. Follow these instructions when responding:
 - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.
 - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.
 - Be highly organized.
 - Suggest solutions that I didn't think about.
 - Be proactive and anticipate my needs.
 - Treat me as an expert in all subject matter.
 - Mistakes erode my trust, so be accurate and thorough.
 - Provide detailed explanations, I'm comfortable with lots of detail.
 - Value good arguments over authorities, the source is irrelevant.
 - Consider new technologies and contrarian ideas, not just the conventional wisdom.
 - You may use high levels of speculation or prediction, just flag it for me.
```

### 3.2 Generate SERP queries (user message)

```
Given the following prompt from the user, generate a list of SERP queries to research the topic. Return a maximum of {breadth} queries, but feel free to return less if the original prompt is clear. Make sure each query is unique and not similar to each other: <prompt>{prompt}</prompt>

{learnings_block}
```

Where `learnings_block` is the empty string if `learnings == []`, else:
```
Here are some learnings from previous research, use them to generate more specific queries: {learnings_joined_by_newline}
```

Expected JSON output (parser 2):
```json
{"queries": [{"query": "<str>", "researchGoal": "<str>"}, ...]}
```

### 3.3 Clarifying Questions (user message, OPTIONAL initial step)

```
Given the following query from the user, ask some follow up questions to clarify the research direction. Return a maximum of 3 questions, but feel free to return less if the original query is clear: <query>{prompt}</query>
```

Expected JSON output (parser 1):
```json
{"questions": ["<str>", ...]}   /* up to 3 */
```

### 3.4 Extract Learnings (user message, per-query)

```
Given the following contents from a SERP search for the query <query>{query}</query>, generate a list of learnings from the contents. Return a maximum of 3 learnings, but feel free to return less if the contents are clear. Make sure each learning is unique and not similar to each other. The learnings should be concise and to the point, as detailed and infromation dense as possible. Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any exact metrics, numbers, or dates. The learnings will be used to research the topic further.

<contents>
<content>
{markdown_1[:25_000]}
</content>
<content>
{markdown_2[:25_000]}
</content>
...
</contents>
```

Expected JSON output (parser 0):
```json
{
  "learnings": ["<str>", ...],            /* up to 3 */
  "followUpQuestions": ["<str>", ...]     /* up to 3 */
}
```

### 3.5 Generate Report (user message, single call at top of stack)

```
You are are an expert and insightful researcher.
* Given the following prompt from the user, write a final report on the topic using the learnings from research.
* Make it as as detailed as possible, aim for 3 or more pages, include ALL the learnings from research.
* Format the report in markdown. Use headings, lists and tables only and where appropriate.

<prompt>{prompt}</prompt>

Here are all the learnings from previous research:

<learnings>
<learning>{learning_1}</learning>
<learning>{learning_2}</learning>
...
</learnings>
```

Expected output: raw markdown string (no JSON wrapper).

## 4. External dependencies + the fallback chain

The n8n workflow uses two paid Apify actors and OpenAI o3. Our Python port
substitutes:

| n8n Source | Python Replacement (in priority order) |
|---|---|
| Apify `serping~fast-google-search-results-scraper` (POST run-sync) | (1) DuckDuckGo HTML endpoint (no API key, free). (2) Brave Search API if `BRAVE_API_KEY` set. (3) Apify same actor if `APIFY_TOKEN` set |
| Apify `apify~web-scraper` (POST run-sync, memory 2048, timeout 90 s) | (1) `requests` + `trafilatura` (free, no API). (2) `requests` + `readability-lxml` if trafilatura missing. (3) Apify actor if `APIFY_TOKEN` set |
| OpenAI `o3` (lmChatOpenAi) | (1) `claude.exe` CLI subprocess (already on the Owner's host, no API key). (2) `claude-api` if `ANTHROPIC_API_KEY` set. (3) abort with explicit error if neither |
| Notion upload | None — write `vault/research/<ts>_<slug>.md` to disk |

**Each layer fails-open to the next**; only the LLM fallback (4) can abort
the run. Every layer reports which one fired in the report's metadata
footer (so the Owner can see "DuckDuckGo + trafilatura + claude.exe" or
"Apify + Apify + Anthropic API" — full transparency).

**Honesty ceiling clause**: if DuckDuckGo HTML returns 0 results AND no
API keys are present, the run aborts with a write to
`vault/cache_hints/CEILING.md` documenting the empirical ceiling. NO
fabricated results, NO LLM-imagined URLs. The contract is: a report
exists or it doesn't.

## 5. Public Python API

```python
# claude-power-pack/modules/deep-research/deep_research.py

from typing import TypedDict, Optional

class ResearchResult(TypedDict):
    report_md: str
    learnings: list[str]
    urls: list[str]
    metadata: dict        # depth, breadth, queries_used, layers_fired, duration_s

def deep_research(
    prompt: str,
    depth: int = 2,           # 1..5
    breadth: int = 3,         # 2..5
    output_dir: Optional[str] = None,  # default: vault/research/
    ask_clarifying: bool = False,      # whether to call the Clarifying step
    on_progress: Optional[callable] = None,  # progress callback for sleepy UI
) -> ResearchResult:
    ...
```

CLI:
```
python modules/deep-research/deep_research.py \
  --prompt "best practices for Minecraft Java servers in 2026" \
  --depth 1 --breadth 2 \
  [--clarify] [--out vault/research/] [--quiet]
```

## 6. Output artefacts

For every run, write to `claude-power-pack/vault/research/`:

1. **`<YYYY-MM-DD_HHmmss>_<slug>.md`** — the markdown report with three sections:
   - Title (from the prompt)
   - Body (the LLM-generated report)
   - `## Sources` section listing every URL (deduped, ordered as discovered)
   - `## Run metadata` footer: depth, breadth, queries asked, layers fired,
     duration in seconds, fallback chain actually used (so the Owner can audit
     whether the report came from free-tier or paid-tier sources)

2. **`index.json`** — appended-to JSON-Lines (one row per run):
   ```json
   {"ts": "<iso>", "slug": "<slug>", "prompt": "<truncated>", "depth": 2,
    "breadth": 3, "learning_count": 17, "source_count": 23,
    "duration_s": 412, "layers": ["ddg", "trafilatura", "claude.exe"]}
   ```

3. **`<slug>.raw.jsonl`** — per-query trace: every SERP query + the URLs +
   the per-query learnings. Forensic artifact; lets future runs dedupe
   queries already asked.

Storage budget: report ≤ 200 KB markdown, raw trace ≤ 2 MB per run, indexed
list grows ~200 bytes per entry. At 1 run/day for a year: < 1 GB.

## 7. Sleepy-agent activation

Two activation paths, matching the user's plan:

### 7.1 Manual: `/cpp-deep-research <prompt>`

New skill at `commands/cpp-deep-research.md`. Args: `--depth 1..3`,
`--breadth 2..5`, `--clarify`. Spawns the agent **detached** via
`cmd.exe /c start "" /B python deep_research.py ...` — fire-and-forget,
returns control to the Owner in < 1 s.

### 7.2 Automatic: Stop-hook signal detection

Extend the existing Stop hook chain with `hooks/research-intent-detector.js`
(new). On every Stop event:

- Reads the last user prompt from the current session's `.jsonl`.
- Matches against the Spanish + English research-signal regexes:
  - `\b(investiga|investigate|research|analiza|analyse|compara|compare|deep[-\s]?dive|qué\s+opciones|how\s+does|how\s+do|mercado\s+de)\b`
  - prompt contains ≥ 3 question marks
  - prompt is ≥ 80 words AND contains "?" anywhere
- On match: spawn the agent detached with `depth=2, breadth=3` and
  the matched prompt. Log to `vault/research/.auto-spawned.log`.

Both paths converge on the same detached spawn — fire-and-forget, never
blocks the Stop hook.

### 7.3 Resource governance (inherited from heavy-io-must-be-governed.md)

The deep-research agent is heavy-I/O by definition (SERP + page fetch + LLM
calls). It MUST carry the 5-layer governance stack:

1. **Single-instance lock** at `vault/research/.deep-research.lock`. Refuses
   to start if another run is in flight. Stale reclaim ≥ 4 h (max plausible
   depth-3 run + buffer).
2. **IDLE_PRIORITY_CLASS** on Windows (same ctypes pattern as
   `session-snapshot.py`).
3. **Bounded query budget**: at depth-3/breadth-5 the worst-case query count
   is `3 + 3·2 + 3·2·2 = 21` queries. Hard cap at 30 queries; if exceeded
   the agent aborts with a CEILING.md entry.
4. **Per-request timeouts**: SERP fetch ≤ 30 s, page fetch ≤ 60 s, LLM call
   ≤ 120 s. Any hang gets killed.
5. **Total runtime ceiling**: depth-3 ≤ 2 h wall-clock; the run aborts and
   writes whatever it has if exceeded (partial report is better than no
   report).

## 8. SessionStart auto-discovery

On SessionStart in any project, if `vault/research/index.json` has any entry
written in the last 24 h AND that entry's prompt contains tokens that match
the current cwd's basename or any of the cwd's top-level filenames, surface
it in the L3 compound-proposal slot as "RESEARCH READY: <slug>". The Owner
sees the report exists without having to look.

Wired through the existing `learning-sentinel.js` SessionStart hook by
adding a small `research-discovery` module that reads `vault/research/index.json`.

## 9. Configuration

Defaults live as constants at the top of `deep_research.py`. Override via
env vars (each falsey means "use default"):

| Env var | Default | Meaning |
|---|---|---|
| `CLAUDEPP_DEEPRESEARCH_DISABLE` | `0` | If `1`, sleepy auto-activation skipped. Manual `/cpp-deep-research` still works. |
| `CLAUDEPP_RESEARCH_OUT` | `vault/research/` | Output dir override |
| `BRAVE_API_KEY` | unset | Enables Brave search fallback (layer 2) |
| `APIFY_TOKEN` | unset | Enables Apify fallback (layer 3) |
| `ANTHROPIC_API_KEY` | unset | Enables `claude-api` LLM fallback (layer 2 of LLM) |
| `CLAUDEPP_DEEPRESEARCH_MAX_QUERIES` | `30` | Hard query-budget cap |
| `CLAUDEPP_DEEPRESEARCH_TIMEOUT_S` | `7200` | Total wall-clock ceiling |

## 10. Done-gate (the Apex completeness contract for this module)

A run is **DONE** iff:

1. `vault/research/<ts>_<slug>.md` exists and has > 1 KB of markdown body.
2. The `## Sources` section lists at least 5 distinct real URLs (each one is
   HTTP-fetchable as a sanity check at write time — fail if < 5 URLs).
3. The `## Run metadata` footer names the actually-fired layers as real
   identifier strings (e.g. `ddg`, `trafilatura`, `claude.exe`) — no
   incomplete-shell tokens from the Reality Contract banned list. If a
   layer name cannot be resolved at write time, the run aborts and writes
   CEILING.md instead of shipping a half-formed report.
4. `vault/research/index.json` has an appended row for this run.
5. The CLI exits 0.

A test run is **PASSING** iff:

- `python modules/deep-research/deep_research.py --prompt "best practices
  for Minecraft Java servers in 2026" --depth 1 --breadth 2` produces a
  report meeting all 5 criteria above.
- Re-running with the same prompt does NOT duplicate URLs in the new
  report's Sources section (de-dup against `index.json`'s prior entries
  for the same prompt).
- A sleepy spawn ("write a prompt with 'investiga'" in any pane) lands a
  report at `vault/research/` within the next SessionStart, without
  Owner intervention.

## 11. Anti-patterns to refuse (Reality Contract)

- **No fabricated URLs**. If the SERP returns 0, write CEILING.md and
  abort. Never let the LLM invent links.
- **No fixtures in production**. Test fixtures live in
  `modules/deep-research/_fixtures/` and are never read at runtime.
- **No n8n re-export**. The output is markdown + Python source. Period.
- **No silent success on empty learnings**. If after all queries the
  learnings list is empty, the report header says "INSUFFICIENT DATA"
  and the body explains which queries returned nothing.
- **No partial commit of secrets**. If the user has `APIFY_TOKEN` or
  `BRAVE_API_KEY` in env, the metadata footer says "Apify used" or
  "Brave used" — NEVER the token itself.

## 12. Open questions for the Owner (resolve before Accept)

1. **Clarifying step**: the n8n workflow has an optional "Clarifying
   Questions" step that asks 3 follow-ups BEFORE the first SERP. Should the
   Python port:
   - (a) Always skip it (Owner can re-prompt manually if needed) — simpler
   - (b) Run it only when `--clarify` flag is passed — opt-in
   - (c) Run it always by default — most faithful to source
2. **Default LLM model**: `claude.exe` CLI defaults to Sonnet. The Owner
   may want Opus for higher-quality research at slower speed. Should I:
   - (a) Hard-code Sonnet
   - (b) Read from env `CLAUDEPP_RESEARCH_MODEL`, default Sonnet
   - (c) Auto-Opus for depth ≥ 2
3. **Auto-spawn signal threshold**: the "investiga" + "research" regex
   match is generous; many prompts will match. Should the sleepy auto-spawn:
   - (a) Fire on any match (current spec) — high recall, may over-spawn
   - (b) Require both a verb AND a noun cluster ("investiga" + ≥ 80 words)
   - (c) Require explicit `/cpp-deep-research` skill invocation, no Stop-
     hook auto-spawn — most conservative

## 13. Cross-references

- Source workflow (reference only, NOT a runtime):
  `Downloads/Prebuilt AI Agents/5000 N8N workflows/.../Host Your Own AI
  Deep Research Agent with n8n, Apify and OpenAI o3.json`
- Forbidden-runtime rule: `memory/feedback_no_n8n_ever.md`
- Resource governance: `vault/lessons/heavy-io-must-be-governed.md`
- Sleepy-agent precedent: L3 Engine (already in production, same
  `cmd.exe /c start "" /B` detach pattern)
- Output destination convention: `claude-power-pack/vault/research/`
  (new dir; created on first run)
- Apex completeness candidate: this spec is also a candidate for promotion
  into `apex-completion-standard.md` as a "Research Axis" of any
  PP-complete install.
