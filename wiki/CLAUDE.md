# PP Wiki — Schema

An LLM-maintained wiki about **Claude Power Pack (PP) and how to make it better**.
Pattern: Karpathy's LLM Wiki ([[2026-09-30-karpathy-llm-wiki]]). The agent writes and maintains every
page; the Owner picks sources, asks questions, reviews interpretations, sets direction.

This file is the operating guide. Change it when a convention stops working, and log the change.

## Layout

```
wiki/
  CLAUDE.md        this schema
  index.md         map of every page, by category — read FIRST on every query
  log.md           append-only timeline
  overview.md      evolving thesis: where PP is strong, weak, and heading
  raw/             sources, IMMUTABLE — never edit, never delete
    assets/        images downloaded from sources
  sources/         one page per raw source
  components/      PP parts: modules, hooks, skills, commands, agents, gates
  concepts/        ideas and patterns, PP-internal or external
  improvements/    proposed changes to PP, one per page, with a status
  syntheses/       answers, comparisons and analyses worth keeping
  tools/           scripts that produced a measurement cited in the wiki (reproducibility)
```

Large sources (a whole repo, a site): `raw/<name>/MANIFEST.txt` pins URL + commit + file list; copy in,
byte-for-byte, only the files a page cites. Video: store the transcript, note the caption track used
(auto / auto-dub) since a dubbed track is a translation.

## Relationship to the rest of the repo

The wiki does NOT replace `governance/`, `vault/`, `knowledge/`, `knowledge_vault/` or the UKDL.
Those are normative (rules the agent obeys). The wiki is descriptive and exploratory (what we know,
what we think, what we could change). Cite them as evidence; never copy a rule in as if the wiki
owned it. An improvement that becomes a rule graduates OUT of the wiki into its proper home, and the
improvement page records where it went.

## Language and style

- English, terse. Short sentences, bullets over paragraphs, no filler. Token cost matters.
- Quotes from sources stay in their original language, short (one sentence or less).
- Owner-facing chat about the wiki: Spanish or English, whatever the Owner uses.

## Page format

Every page starts with YAML frontmatter:

```yaml
---
type: source | component | concept | improvement | synthesis
created: 2026-09-30
updated: 2026-09-30
sources: [2026-09-30-karpathy-llm-wiki]   # source page names this page draws on
---
```

Extra fields by type:
- `component`: `path:` (repo path), `status:` LIVE | PLANNED | ABSENT
- `improvement`: `status:` IDEA | DISCUSSING | ACCEPTED | IN-PROGRESS | DONE | REJECTED,
  `effort:` S | M | L, `graduated_to:` (path, once DONE)
- `source`: `raw:` (path under raw/), `kind:` article | gist | paper | transcript | repo | note,
  `origin:` (URL or where it came from)

Filenames: lowercase-kebab, unique across the whole wiki (so bare `[[name]]` links resolve).
Source pages and raw files share the name `YYYY-MM-DD-short-title`.

## Links and citations

- Link with `[[page-name]]` (Obsidian-native). Every page links to at least one other page.
- **Every meaningful claim cites its evidence**, one of:
  - a source page: `([[2026-09-30-karpathy-llm-wiki]])`
  - repo code: `` (`modules/x/y.py:42` @ `abc1234`) `` — path, line, AND short commit hash,
    because code moves. A code citation without a hash is unverifiable later.
  - an Owner statement in chat: `(Owner, 2026-09-30)`
- A claim with no citation is marked `(unsourced)` or removed. Interpretation is marked as such:
  `Interpretation:` prefix.
- Describing a PP capability requires a `status` (LIVE / PLANNED / ABSENT), never bare present
  tense. LIVE means verified reachable, not "a file exists".

## Disagreements

When a new source contradicts an existing page, do not overwrite silently. Add a
`## Disagreements` section on the affected page: what each side says, with citations, and which
one the evidence currently favors (or "unresolved"). Log it.

## Workflows

### Ingest (one source at a time, discussed)

1. Save the source to `raw/` unchanged (`YYYY-MM-DD-short-title.ext`). Images to `raw/assets/`.
2. Read it fully. Present to the Owner: 3-7 key takeaways, what it implies for PP, which pages it
   would create or touch, and any judgment call. **Stop and wait for the Owner's input.**
3. After the Owner responds: write `sources/<name>.md`, then create or update every affected
   component / concept / improvement page (often several), add cross-links, record disagreements.
4. Update `index.md` and `overview.md` if the thesis moved.
5. Append to `log.md`.

### Query

1. Read `index.md`, open the relevant pages, drill into `raw/` or repo code when needed.
2. Answer with citations. Format fits the question (text, table, chart).
3. If the answer is a reusable comparison or insight, offer to file it in `syntheses/` and link it.
4. Log significant queries.

### Lint (on Owner request, or suggest after every ~5 ingests)

Check: stale claims superseded by newer sources; contradictions between pages; broken `[[links]]`
(skip the format examples in this file: `a`, `b`, `name`, `page-name`, `links`);
orphan pages (no inbound links); concepts mentioned repeatedly with no page; code citations whose
path no longer exists at HEAD; improvements stuck in DISCUSSING; questions the material cannot
answer, with suggested sources to fill them. Fix what the evidence already supports; report the
rest. Log the pass.

## index.md format

One section per category, one line per page:
`- [[page-name]] — one-line description (N sources)`

## log.md format

Append only. Each entry starts with a greppable header:

```
## [2026-09-30] ingest | Title
- touched: [[a]], [[b]]
- notes: one or two lines
```

Operations: `init`, `ingest`, `query`, `lint`, `schema` (a change to this file).

## Tools

Plain markdown + `index.md` until navigation gets hard (~100 sources). Then consider a local search
tool. Obsidian can open `wiki/` as a vault for reading and graph view; git is the history. None of
these are prerequisites.
