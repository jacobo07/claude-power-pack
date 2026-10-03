# Phase 2: Capability subject and archetypes - Research

**Researched:** 2026-10-03
**Domain:** PP `modules/capability_runtime` (new `archetypes.py`) + an off-prompt-path structural-trait cache; pure Python stdlib, Windows host
**Confidence:** HIGH for repo facts and measured costs (every `[VERIFIED: path:line]` below was opened with Read this session, and every number was produced by running a script this session); MEDIUM for detector vocabularies and verb lists (`[ASSUMED]`, listed in the Assumptions Log)
**Worktree HEAD at research time:** `b1732af7` (Phase 1 code-review fixes WR-01..WR-04 were still landing during this research; line numbers in `modules/tower/donegate.py` moved by 9 between two reads. Re-read a line before editing it, cite by symbol.)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Owner of "what is this capability, its traits, archetypes" is `modules/capability_runtime` — new
  `archetypes.py`, reusing `_hits` from `applicability.py`; no parallel authority.
- Traits: persistent, multi_actor, bulk, destructive, distributed, external_effect, scheduled, money,
  policy_layers, ui. Archetypes are trait conjunctions. Family and archetype are independent outputs.
- Anti-triggers DEMOTE, they do not veto.
- No archetype from vocabulary alone: an archetype needs a structural repo or intent fact (invariant). Live
  evidence of the defect: a subagent hand-back that builds nothing was injected `persistent_state/B0` because
  it contained the word "schema" (plan of record, line 6).
- Structural traits come from a cache keyed by repo root + cheap fingerprint, computed OFF the prompt path; the
  prompt path only reads it [G4]. Cache miss -> traits UNJUDGED, never absent (absent is not zero).
- Intent-only traits carry fact state EXTRACTED and can yield at most CONDITIONAL, never REQUIRED [G16].
- Test file `tools/test_capability_archetypes.py`: vocabulary-overlap negative control, intent-only control,
  trait transitions (ephemeral->persistent, local->distributed) recompile differently, positive controls per
  archetype.
- Phase 1 delivered `modules/tower/baselines.discover_subjects` (walks nested axes); Phase 4 will add the
  `archetype/<ID>` axis — Phase 2 only defines archetypes in code, it writes no baseline generation.

### Claude's Discretion
Fingerprint inputs, cache location/format (must live outside the repo tree's tracked files or be gitignored,
and tests must use a hermetic HOME), structural detectors per trait, the exact archetype set defined in code
(must include at least the three Phase 4 targets: WORLD_MUTATION/persistent-state, EXTERNAL_EFFECT,
BACKGROUND_JOB), and the fact-state vocabulary — choose from existing `capability_runtime` conventions.

### Deferred Ideas (OUT OF SCOPE)
Wiring traits/archetypes into the prompt path is Phase 5-6 (envelope compiler + delivery). Open items carried
from Phase 1 EVIDENCE (14 MOVED citations, `wiki/tools/cbr_probe.py` P4 abort, a suite writing
`gsd-x-heartbeat.json` under the real HOME) are not Phase 2 scope.

Operating constraints binding this phase (CONTEXT `<specifics>`, ROADMAP): worktree `.claude/worktrees/ucep`, branch `ucep/mission`; pathspec-scoped commits; never push to main; git via `& 'C:\Program Files\Git\cmd\git.exe' -C <worktree>`; python `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` with `PYTHONIOENCODING=utf-8`; never edit `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.claude/hooks/`; each new module declared PLANNED in `vault/liveness/reachability_registry.json` with an owner-queue line in the SAME commit; never `reachability.py --baseline`; narrow oracles; hermetic HOME; never ask the Owner mid-run; phase ends with `02-EVIDENCE.md` (PROVEN / OBSERVED / UNJUDGED / BLOCKED; nothing here is on a live hook path, so OBSERVED at most).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UCEP-02 | Capability subject: traits from cached repo structure + intent; archetypes orthogonal to families; vocabulary alone never REQUIRED | F1-F3 (what exists to reuse), F4-F6 (measured detector and cache costs, absent-vs-unjudged rules), Architecture Patterns (trait/archetype/strength model, cache schema, API), Validation Architecture (a runnable gate per success criterion) |
</phase_requirements>

## Package Legitimacy Audit

No external packages are installed by this phase. Everything is Python 3.12 standard library plus in-repo modules. Section not applicable; `gsd_run query package-legitimacy check` was not run because there is nothing to check.

## Summary

The phase is small in code and large in discipline. The repo already contains every primitive it needs: the matcher (`_hits`), the accent folding (`families._fold`), the fact-state vocabulary (`obligation.OBSERVED/DERIVED/DECLARED/EXTRACTED/UNKNOWN`), the repo identity key (`repo_identity.repo_key`), an off-path producer / prompt-path reader / six-state precedent (`tower/capsule.py`, run daily by the scheduled task `PP-Tower-Capsules`), and a three-bucket held / not-held / unknown fact document with dependency-driven freshness (`gsd_x/mission/structured_facts.py`). Phase 2 should compose these into three new files and one CLI, not invent any of them again.

The two measurements that decide the design: (1) a structural detection walk costs 0.3 s (this repo, 3,977 files) to 3.0-12 s (KobiiCraft, 49,924 files) and, on KobiiSports Resort, 48 s and still truncated at 100,001 files, against a UserPromptSubmit chain deadline of 3000 ms; (2) a prompt-path read of the cache plus a depth-1 freshness fingerprint costs about 0.2 ms + 0.5-1.3 ms. So the producer is out of band by necessity, and the reader is one small file read plus one `scandir`. A cache miss, a stale entry, a truncated walk, a repo with no recognized manifest, and a trait with no structural detector at all must each read `UNJUDGED`, never `ABSENT`: the prototype found three real repos (ABSW2-Wii, CavEX, KobiiHub) where the dependency-based detectors were blind (zero manifests parsed), and a truncated walk on TUA-X and KobiiSports Resort.

The strength rule that implements [G16] is a single function: `REQUIRED` needs a fresh OBSERVED structural anchor AND an intent fact; intent alone, structure alone, a weak structural signal, or an anti-trigger yield at most `CONDITIONAL`; intent-only facts are stamped `EXTRACTED`. Vocabulary alone yields nothing: intent facts must be a verb-object structure (bilingual, accent-folded), not a bag of words, because the live defect was the single word "schema" in a family trigger list.

**Primary recommendation:** Build `modules/capability_runtime/archetypes.py` (pure vocabulary + `resolve`, prompt-path safe, never walks), `modules/capability_runtime/trait_scan.py` (the producer: bounded walk, parsed-dependency detectors, atomic cache write to `~/.claude/state/tower/traits_<repo_key>.json`) and `tools/capability_traits.py` (out-of-band CLI, `<root>` and `--all`), prove it with `tools/test_capability_archetypes.py` (`CAPABILITY_ARCHETYPES_PASS=`), declare all three PLANNED in the liveness registry, and edit no existing file except that registry.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Trait / archetype vocabulary, strength rule, `resolve(subject)` | `modules/capability_runtime/archetypes.py` (in-process library) | — | Plan of record Ownership table: "what is this capability, its traits, archetypes -> capability_runtime". Pure function over (cache reading, prompt text); no I/O except the cache read helper |
| Structural trait detection (walk, parse manifests) | `modules/capability_runtime/trait_scan.py`, run OUT OF BAND (scheduled task / CLI) | SessionStart detached spawn (`jit_warm.js` precedent), Phase 6 / Owner step | 0.3-48 s per repo vs a 3000 ms chain deadline; capsule precedent G-3: "the producer runs OUT OF BAND of any latency-deadline chain and PERSISTS; the prompt path only READS" |
| Trait cache storage | Per-user state dir `~/.claude/state/tower/` (outside every repo tree) | — | Same directory and keying as `capsule_<key>.json`; nothing tracked, nothing to gitignore |
| Cache freshness check on read | `archetypes.py` read helper (depth-1 `scandir` + manifest stats, ~1 ms) | producer's depth-2 skip-if-unchanged (8-27 ms) | Reader must stay under a millisecond-scale budget; producer may afford more |
| Family classification | `modules/tower/families.py` (UNCHANGED) | — | Family and archetype are independent outputs; Phase 2 must not edit the family classifier |
| Fact-state vocabulary | `gsd_x/mission/obligation.py` (imported, not copied) | — | The module itself states "ONE owner for this vocabulary" |
| Archetype -> baseline axis, envelope, delivery | Phases 4, 5, 6 (out of scope) | — | Deferred in CONTEXT |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`os`, `re`, `json`, `hashlib`, `time`, `dataclasses`, `tempfile`) | 3.12 [VERIFIED: ran `Python312\python.exe`] | everything | repo is stdlib-only on this path; no installs |
| `modules.capability_runtime.applicability._hits` | in-repo | word-boundary phrase match | locked decision: reuse, no second matcher |
| `modules.tower.families._fold` / `_match` | in-repo | accent-folded matching (prompts are Spanish) | `_match(text, phrases)` = `_hits(_fold(text), [_fold(p) ...])` |
| `modules.gsd_x.mission.obligation` constants `OBSERVED DERIVED DECLARED EXTRACTED UNKNOWN FACT_STATES` | in-repo | fact-state vocabulary | see F2 |
| `modules.repo_identity.identity.repo_key` / `canonical_repo` | in-repo | cache key | already the capsule key; normalizes case, slashes, trailing slash, subdirs, `..`, 8.3 short names (measured, F6) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tools/family_scan.find_repos`, `main_repo_of`, `MARKERS`, `DEP_MANIFESTS` | in-repo | enumerate estate projects for `--all`; reuse the persistence marker vocabulary | CLI `--all` only (tools/ is not a package on the prompt path) |
| `modules/gsd_x/mission/structured_facts.FACT_STATES` shape (held / not_held / unknown buckets) | in-repo | model for the cache document | shape only; do NOT route trait facts through its loader (closed `FACT_NAMES`, F2) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New producer + own cache file | Extend `tower/capsule.produce()` to embed traits | Edits a shared, live-path file (`gsd_x/tier.py` reads it) and the capsule is 24 h-stale-gated; a separate file keeps blast radius at zero. Recommended: separate |
| New producer | Reuse `family_scan.scan_repo` as the persistent detector | `scan_repo` truncates at 4000 entries and returns no `truncated` flag, so a cut walk reads as OUT (F3, pitfall P3) |
| Content grep over source files | Name / manifest / marker detection only | Measured: a word-level content grep fired `money` on 102 of 1,483 PP source files and `persistent` on 218, i.e. it re-creates the D7 vocabulary defect one level down (F5) |

**Installation:** none.

**Version verification:** not applicable (no packages). Interpreter: Python 3.12 at `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` [VERIFIED: used throughout this session].

## Findings (evidence log)

### F1. Where families are classified today, and the live defect (D7)
- `families.classify_prompt` is prompt words only: it calls `_match(text, f.anti_triggers)` then `_match(text, f.triggers)` and never looks at the repo [VERIFIED: `modules/tower/families.py:88-99`]. The repo-side method `repo_families` exists (`:178-180`) and is used for promotion, not injection. The module docstring states the intended split: "classify_prompt(text) which families does THIS mission build? -> injection / repo_families(path) which families does THIS repo belong to? -> promotion" [VERIFIED: `families.py:15-17`].
- The false activation is a trigger word: `"triggers": ["migracion", "migration", "tabla", "base de datos", "database", "schema", "esquema", "prisma", "postgres", "supabase", "sqlite", "crud", "backend", "persistencia", "ecto", "sqlalchemy"]` [VERIFIED: `vault/tower/families/persistent_state.json:4-6`]. The plan of record records the observation: "the subagent hand-back message, which builds nothing, was injected `persistent_state/B0` because it contained the word 'schema'" [VERIFIED: `vault/plans/ucep-naked-verb-2026-10-02.md:3-7`].
- `_hits` is the matcher to reuse, verbatim: `re.search(r"\b" + re.escape(p) + r"\b", t)` over lowercased text, returning the matching phrases [VERIFIED: `modules/capability_runtime/applicability.py:97-106`]. It does not fold accents; `families._fold` does (NFKD, strip combining marks, lower) and is applied to BOTH prompt and phrases [VERIFIED: `families.py:57-62,83-85`]. All predeclared test prompts are Spanish (`"añade una tabla de suscripciones con su migración al backend de InfinityOps"`) [VERIFIED: `tools/test_family_baselines.py:33`]. Therefore intent matching for traits MUST go through `families._match` (or an equivalent fold), and the English-only verb lists in `obligation.py` (`_TRANSFER_VERB`, `_DESTRUCTIVE_VERB`, `_TRANSFORM_VERB`, `obligation.py:171-175`) cannot be reused as-is.
- Applicability gate order (anti-trigger veto first at gate 1, "no trigger matched -> dormant" at gate 1.5) is `applicability.evaluate` [VERIFIED: `applicability.py:116-143`]. Phase 2 does NOT call `evaluate`; the plan's invariant "anti-triggers DEMOTE" is the deliberate difference, so archetype assessment must be its own small function that borrows only `_hits`.
- Importing anything under `modules.capability_runtime` runs `capability_runtime/__init__.py`, which imports ten sibling modules [VERIFIED: `modules/capability_runtime/__init__.py:31-56`]. Measured import cost (7 runs, medians, contended host): bare interpreter 437 ms; `import modules.capability_runtime.applicability` 792 ms; `modules.tower.families` 510 ms; `modules.gsd_x.mission.obligation` 548 ms; `modules.gsd_x.cli` 488 ms. `gsd_x/cli.py` already pays the package import through `tier`, so `archetypes.py` adds nothing on the prompt path. Do NOT add `archetypes` to `capability_runtime/__init__.py` exports (shared file, and it would couple every consumer to the new module).

### F2. Fact-state and disposition vocabulary that already exists
- Fact states, verbatim [VERIFIED: `modules/gsd_x/mission/obligation.py:125-131`]:
  `OBSERVED = "OBSERVED"      # measured directly from an authoritative source`
  `DERIVED = "DERIVED"        # computed deterministically from authoritative evidence`
  `DECLARED = "DECLARED"      # a human asserted it; nothing mechanical established it`
  `EXTRACTED = "EXTRACTED"    # mined out of prose by the regex adapter`
  `UNKNOWN = "UNKNOWN"        # the evidence to decide does not exist`
  `FACT_STATES = frozenset({OBSERVED, DERIVED, DECLARED, EXTRACTED, UNKNOWN})`.
  The module says why it is the single owner: "ONE owner for this vocabulary, and it lives here because `Fact` lives here ... two spellings of one vocabulary is the second truth this wave exists to remove" (`obligation.py:115-119`). `EXTRACTED` is "deliberately NOT DECLARED" (`:121-124`) which is exactly the stamp [G16] requires for intent-only traits. `Fact(name, matched, source, state=DECLARED)` is frozen (`:134-146`); `extract_facts` stamps `state=EXTRACTED` (`:232-241`). Import these constants; do not re-spell them. `obligation.py` imports only `re` and `dataclasses` and `modules/gsd_x/__init__.py` has no imports (grep: 0 matches for `import`), so there is no cycle with `capability_runtime`.
- Obligation dispositions (not trait strengths): `CANDIDATE ACCEPTED NOT_APPLICABLE REJECTED DEFERRED SATISFIED STALE` [VERIFIED: `obligation.py:34-40`]. The plan's applicability words `REQUIRED / CONDITIONAL / NOT_APPLICABLE / EXPLICITLY_DEFERRED` exist nowhere in code: grep of `*.py` for `CONDITIONAL|EXPLICITLY_DEFERRED` finds only `tools/test_baseline_inheritance.py:101` (`V-INHERIT-CONDITIONAL`, an unrelated gate name) and a comment in `tools/test_usea_cross_domain_benchmark.py:344`. So Phase 2 DEFINES the strength vocabulary (`REQUIRED`, `CONDITIONAL`, plus a `NONE` for "no archetype"), and Phase 5 owns the mapping table into dispositions. Naming trap: `modules/tower/baselines.py:34` already has `REQUIRED = ("id","requirement","why","origin","class")` (entry keys); define the strength constants inside a small namespace (`class Strength` or `STRENGTH_REQUIRED = "REQUIRED"`), not a bare module-level `REQUIRED` that Phase 5 will import next to `baselines.REQUIRED`.
- Evidence verdicts used by the done gate: `APPLIED_VERIFIED, VIOLATED, DELEGATED, NOT_APPLICABLE, UNJUDGED` [VERIFIED: `modules/tower/donegate.py` `_COUNT_OF` mapping, read at lines ~100-101 in the first read]. Use the token `UNJUDGED` for "cache miss / stale / truncated / blind detector": it is the roadmap's word ("traits UNJUDGED") and donegate's.
- Trait -> N/A reason bridge (Phase 1 built it, Phase 2 should expose it). `NA_REASONS`, verbatim [VERIFIED: `modules/tower/donegate.py:90-102`]: `"no-persistent-state", "single-actor", "no-bulk-operation", "no-destructive-operation", "not-distributed", "no-external-effect", "not-scheduled", "no-money", "single-policy-layer", "no-user-interface", "platform-not-targeted", "superseded-by-entry"`. The first ten are the ten traits in the plan's order, one each. A `TRAIT_NA_REASON` dict in `archetypes.py` (persistent->`no-persistent-state`, multi_actor->`single-actor`, bulk->`no-bulk-operation`, destructive->`no-destructive-operation`, distributed->`not-distributed`, external_effect->`no-external-effect`, scheduled->`not-scheduled`, money->`no-money`, policy_layers->`single-policy-layer`, ui->`no-user-interface`) lets Phase 5 justify a NOT_APPLICABLE only from a judged-ABSENT trait. Cross-check it in the TEST (`set(values) <= set(donegate.NA_REASONS)`), not by importing `tower` from `capability_runtime`.
- The structured-facts document shape is the model for the cache body. `gsdx-facts/2` carries `facts[]`, `not_held[]`, `unknown[]` because "the fact was measured and does NOT hold / the fact could not be measured / nobody ever asked" collapse into one bucket otherwise (`structured_facts.py:9-26`). Its loader REFUSES any name not in `FACT_NAMES` (`structured_facts.py:130-138`, `FACT_NAMES` = names of `_FACT_PATTERNS`, `obligation.py:443`). Trait names are not in that closed set, so Phase 2 must not write a `FACTS.json` and must not edit `_FACT_PATTERNS`; Phase 5 maps trait readings to `Fact(...)` objects itself. Freshness there is dependency-driven with no clock: each entry carries `depends_on` fingerprints `{path, readable, bytes, mtime, sha256}`; an unreadable source is UNKNOWN, not STALE (`structured_facts.py:304-358`).
- Cheap-fingerprint precedent: `agent_resolver.fingerprint` hashes `(name, size, mtime_ns)` only, because "hashing CONTENT opened every file before a cache lookup and was 3.8 of 4.3 s on a 1,000-spec catalog" [VERIFIED: `modules/capability_runtime/agent_resolver.py:93-106`].

### F3. Off-path compute that already exists, and what to copy
- The precedent is `modules/tower/capsule.py` and its CLI shim `tools/tower_capsule.py`. Doctrine in the module docstring: "G-3 (09_G3_DECISION.md) decided the lane: the producer runs OUT OF BAND of any latency-deadline chain and PERSISTS; the prompt path only READS ... 815 chain abandonments in 8 days ... SessionStart abandoning too, so there is no safe hook lane. A file read adds no spawn." [VERIFIED: `capsule.py:8-12`]. Conventions to copy exactly:
  - state dir computed per call, never at import: `d = os.path.join(os.path.expanduser("~"), ".claude", "state", "tower")` then `os.makedirs(d, exist_ok=True)` [VERIFIED: `capsule.py:49-52`]. (Contrast `modules/gsd_x/heartbeat.py:31`, `_STATE = Path(os.environ.get("CLAUDE_STATE_DIR") or (Path.home() / ".claude" / "state"))`, evaluated at import: that is why Phase 1 saw a heartbeat written under the temp HOME. A per-call state dir keeps a hermetic HOME honest.)
  - file name `capsule_%s.json` % key, key from `repo_identity.repo_key(os.path.abspath(path or os.getcwd()))` with the explicit warning that a relative path yields key `-` and "a capsule that never exists" [VERIFIED: `capsule.py:55-75`]. Use `traits_%s.json`.
  - atomic publish: write `out + ".tmp"` then `os.replace(tmp, out)` [VERIFIED: `capsule.py:294-298`].
  - read never raises and never returns silence: missing file -> `{"state": UNKNOWN, "reason": "no capsule produced for this repo", ...}`; unreadable -> `PRODUCER_FAILURE`; older than `FRESH_SECONDS = 24 * 3600` -> `STALE` with evidence blanked ("stale evidence is not evidence") [VERIFIED: `capsule.py:45,302-325`].
  - six states, "no output is not one of them": `AVAILABLE NOT_APPLICABLE EMPTY_BY_EVIDENCE PRODUCER_FAILURE STALE UNKNOWN` [VERIFIED: `capsule.py:37-43`].
  - a capsule contributes to `available_evidence` ONLY, never `held_scopes`/`resolved_owners` (G-4, because `applicability.py:146` disables gate 2 on an empty set) [VERIFIED: `capsule.py:13-17`, `gsd_x/tier.py:240-249`]. Phase 2 does not feed `MissionContext` at all; keep it that way.
- The off-path host already running on this machine: scheduled task `PP-Tower-Capsules`, last result 0, next run 03/10/2026 15:45, action `wscript.exe //B //Nologo "C:\Users\User\.claude\skills\claude-power-pack\tools\hidden_launch.vbs" C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe "C:\Users\User\.claude\skills\claude-power-pack\tools\tower_capsule.py" --all` [VERIFIED: `schtasks /query /tn PP-Tower-Capsules /v /fo list` this session]. It runs the MAIN checkout's file, so nothing written in this worktree is live until merge, and registering a second task or adding a second step is an OWNER step (Phase 6 / EVIDENCE owner queue), not a Phase 2 action. `tower_capsule.produce_all` also writes a symmetric `production.jsonl` row "Without this line, 'the task ran and produced 42 capsules' and 'the task never ran' look the same" [VERIFIED: `tools/tower_capsule.py:62-74`]; copy that discipline into the traits CLI.
- Other hosts surveyed: `hooks/jit_warm.js` is a SessionStart fire-and-forget pre-warmer: `spawn(PY, [JIT], {detached: true, stdio: 'ignore', ...}); child.unref()` using `payload.cwd` [VERIFIED: `hooks/jit_warm.js:49-79`]. A sibling hook running `capability_traits.py <cwd>` detached would refresh the subject's cache at session start without touching the prompt chain; it is a `hooks/` file plus an Owner registration, so Phase 6 / Owner queue, not Phase 2. `gsd_x` has no warmer; `heartbeat.record` is per-prompt telemetry. The SessionStart chain has its own 4000 ms deadline (`hook-dispatcher.js:763`).
- Prompt-path budget: `'UserPromptSubmit-chain': 3000` [VERIFIED: `hooks/hook-dispatcher.js:787`]; `gsd_x_tier.js` runs `cli.py` with `CHILD_TIMEOUT_MS = 6000` and measured the child at "full cli.py, real prompt 1233 ms median, 1443 ms max" with "python interpreter floor 681 ms median" [VERIFIED: `hooks/gsd_x_tier.js:22-26,55`]; a child killed at the deadline loses ALL stdout including the live `family_block` (audit G4). Every millisecond the reader adds comes out of that margin.
- Liveness format [VERIFIED: `vault/liveness/reachability_registry.json:1-24` and `modules/liveness/reachability.py:50-56`]: top-level `known_orphans` (list) and `modules` (object keyed `<package>/<module>` without `modules/` or `.py`, e.g. `"lease/store"`), each value `{"class": "PLANNED", "note": "..."}`. `VALID_CLASSES = (LIBRARY, DEPRECATED, PLANNED, SCHEDULED)`; `PLANNED = "PLANNED"        # wiring pending; MUST carry an OWNER_QUEUE row`. Nothing validates the owner-queue text; existing PLANNED rows put it in the note as `Owner queue: <path>`. A malformed class is "not an exemption" (`reachability.py:559-561`). `tools/` is not scanned (`reachability.py:650-653`), so a tools CLI is not itself a liveness subject, but the `modules/capability_runtime/*` units it imports are, and will read ORPHAN until a live surface imports them.
- Liveness baseline in this worktree, measured read-only (`reachability.gate()`, 23.1 s): `passed=False offenders=63 rows=486`. The gate is ALREADY red here for reasons outside this mission (for example `gsd_x/goal/*`, `capability_runtime/agent_bundle`, `capability_runtime/agent_resolver`). So the Phase 2 liveness oracle is "my new units are not in the offender set by name", compared before and after, not "gate passes". `capability_runtime/applicability` is REACHABLE via `commands/capability.md`; `tower/capsule` and `tower/families` via `modules/gsd_x/cli`; `gsd_x/mission/obligation` is ORPHAN in this scan (no live surface imports it; `tools/gsd_mission.py` is a tool). Plain `python modules/liveness/reachability.py` is read-only; only `--baseline` writes (`reachability.py:664-695`). The registry file is shared: edit it with a minute-scale pathspec commit and read the hunk headers first.
- Hermetic HOME pattern [VERIFIED: `tools/test_family_injection.py:78-84`]: `home = tempfile.mkdtemp(prefix="finj-home-"); env = dict(os.environ, HOME=home, USERPROFILE=home, PYTHONIOENCODING="utf-8"); ... os.environ.update(HOME=home, USERPROFILE=home)`, then a first gate `check("V-FINJ-HERMETIC-HOME", Path.home() == Path(home), Path.home())`. Run Python directly, never under a `timeout N` wrapper (strips HOME, 01-RESEARCH F1). Test output convention: `check(gate, cond, evidence)` printing `  PASS %-38s %s` / `  FAIL %-38s %s` and a final `<NAME>_PASS=n/m  threshold=n/m` with exit `0 if _FAIL == 0 else 1` [VERIFIED: `tools/test_family_injection.py:42-49`; Phase 1 EVIDENCE cites the same convention]. A `Counting` wrapper that proves a seam was reached is the repo idiom for drills (`test_family_injection.py:67-74`).

### F4. Measured cost: structural walk vs prompt-path read (host is contended; ranges, not points)
All numbers produced this session by throwaway scripts in `%TEMP%\ucep_r2\` (not in the repo), Python 3.12, Windows 11, live host with other sessions running. Walk = `os.walk` with the skip set `{.git, node_modules, __pycache__, .venv, venv, dist, build, .next, target, _build, deps, .claude}`.

| Repo (read-only) | Files walked | Plain walk | Walk + manifest parse (prototype v2) | Notes |
|---|---|---|---|---|
| PP worktree (this repo) | 3,977 (3,376 with vendor skipped) | 0.22 / 0.27 / 0.37 s | 0.34 s | 28 parsed dependency names |
| InfinityOps | 10,165 | 0.40-1.27 s | 1.4 s | 87 parsed dependency names |
| ABSW2-Wii | 10,127 | 0.93 s | 0.93 s | 0 manifests parsed |
| KobiiCraft Core Files | 49,924 | 3.02 s | 12.4 s (contended run) | 205 manifests |
| TUA-X | >=30,001 (cap hit) | — | 3.1 s at cap 30,000 | truncated |
| KobiiSports Resort | >100,001 (cap hit) | 48.0 s at cap 100,000 | 9.0 s at cap 60,000 | truncated; Unity `Library/PackageCache` inside |

Prompt-path candidates (7-50 repeats each):
| Operation | PP | InfinityOps | KobiiCraft |
|---|---|---|---|
| depth-1 fingerprint: `scandir(root)` + `(size, mtime_ns)` of manifest-named root files + sha of the name set | 0.44 ms median (max 1.3) | 0.50 ms (max 1.2) | 1.04 ms (max 4.3) |
| depth-2 fingerprint (adds every child directory's mtime and one more `scandir` level) | 12.1 ms (max 38) | 8.4 ms (max 27) | 27.5 ms (max 104) |
| depth-3 fingerprint | 81 ms (max 112) | 128 ms (max 367) | 542 ms (max 9,025) |
| read + `json.load` of an 876-byte cache document | 0.20 ms median (max 15.5 cold) | | |

Consequences: (a) detection cannot run on the prompt path (0.3-48 s vs a 3000 ms chain deadline that also has to pay ~0.5-0.8 s of interpreter + import); (b) the reader may afford a depth-1 fingerprint (about 1 ms) and nothing deeper; (c) the producer may use a depth-2 fingerprint (<=104 ms) to skip a rewalk when nothing moved, and must carry a file cap, a wall-clock budget and a `truncated` flag because KobiiSports Resort cannot be walked to completion in a reasonable time.

### F5. What structural signals reliably indicate each trait (measured on 9 real repos; prototype detectors)
Method: one `os.walk`, a manifest parser per ecosystem that extracts DECLARED DEPENDENCY NAMES (package.json `dependencies/devDependencies/...` keys via `json`; requirements.txt line heads; pyproject quoted names; mix.exs `{:name,`; pom `artifactId/groupId`; gradle `group:artifact`; Cargo/go.mod heads), filename/dir/extension counters, and `.github/workflows/*.yml` for `cron:`. Observed results:

| Repo | Structural traits found (evidence) | Reading |
|---|---|---|
| InfinityOps | persistent (ecto_sql, postgrex, drizzle-orm, pg), external_effect (finch, req, resend, stripe), money (stripe, @stripe/stripe-js), multi_actor (phoenix, phoenix_live_view, phoenix_pubsub), scheduled (oban), distributed (`docker-compose.yml`, `Dockerfile`), ui (224 UI files) | matches the predeclared IN pole of `family_scan.PREDECLARED` [VERIFIED: `tools/family_scan.py:69-78`] |
| KobiiCraft Core Files | persistent (`level.dat`, `.mca` x2,696, `.db` x2, a `playerdata` dir), external_effect (requests, openai, anthropic, discord), money (vault, vaultapi), multi_actor (paper-api, bukkit, `plugin.yml`, `paper-plugin.yml`), ui (108) | persistent evidence here is DATA files (staging worlds, reference schematics), not code: WEAK-class evidence |
| TUA-X (cap 30,000, truncated) | persistent (asyncpg, sqlalchemy), external_effect (anthropic, httpx), scheduled (celery), distributed (`docker-compose.yml`) | positives found before the cut are sound; absences (ui, money, ...) must read UNJUDGED |
| PP worktree | external_effect (aiohttp, anthropic, httpx from nested `modules/*/vps/requirements.txt`), ui (5 files, threshold-borderline) | nested manifests are real component deps: record the path in evidence |
| Mytilus Belgian Restaurant | ui only | correct for a static site |
| Club Nautico | persistent via ONE `.db` file, ui | weak (single data-file extension) |
| ABSW2-Wii, CavEX, KobiiHub | nothing found, `manifest_deps=0` | the dependency detectors were BLIND, not negative: no recognized manifest ecosystem. Reading this as "no persistence" would be absent-is-zero |
| KobiiSports Resort (cap 60,000, truncated) | persistent via a `docs/migrations` dir inside `Library/PackageCache/.tmp-.../clone/` (a FALSE positive from a vendored package cache) and `.db` x4 | the real persistence is a source module `KobiSports_Fut/source/engine/save/save_manager.c` (+ `include/engine/save/save_manager.h`, `Assets/Scripts/Core/SaveManager.cs`) found by Glob: a name-level "persistence module" signal exists and the skip set must include Unity/Android build caches |

Findings that shape the detectors:
1. **Substring/word matching over manifest TEXT is wrong; parse declared dependencies.** The first prototype matched `schedule` in `vendor/genesis-suite/modules/genesis-plan-graph/package.json`, a description string, and reported `scheduled`. Parsed dependency keys plus a larger skip set (`vendor`, `third_party`, `site-packages`, Unity `Library`, `PackageCache`, `Temp`, `obj`, `bin`, `Pods`, `.gradle`, generated `_knowledge_graph`) removed it. `family_scan`'s own comment records the same class of bug: plain `dep in blob` reported `orm_dependency` on 129 of 163 repos because "ecto" is a substring of "vector", "detector", "selector" (`tools/family_scan.py:208-214`).
2. **Source-text content grep is vocabulary, not structure.** A bounded regex over the first 32 KB of 1,483 PP source files fired `money` on 102 files (words `price/currency/balance/payment`) and `persistent` on 218 in a repo with no persistence markers. Do not content-grep source for trait words. Content reads are allowed only for files selected by NAME and only for a decisive token (workflow `cron:`, `vercel.json` `"crons"`, `plugin.yml` existence).
3. **Evidence strength has two classes.** STRONG = declared runtime dependency, schema/migration artifact, scheduler config, orchestration file, plugin descriptor. WEAK = a data-file extension (`.db`, `.sqlite`, `.mca`, `level.dat`), a single marker, a dev-only dependency, a UI-file count near its threshold. WEAK evidence may carry a trait to `CONDITIONAL` and never to `REQUIRED`.
4. **Absent needs a visible ecosystem.** A dependency-class detector is only entitled to say ABSENT if at least one manifest was parsed and the walk was not truncated; a marker-class detector is entitled if the walk was not truncated; otherwise the trait is UNJUDGED. Per-trait: `bulk` and `destructive` have NO structural detector worth shipping (they describe what a mission does, not what a repo is): they are intent-only traits and their structural reading is always UNJUDGED ("no detector"), which is different from ABSENT. `policy_layers` has only weak structure (a `policies`/`rls` dir, an authz library), so it is mostly intent plus weak structural.
5. A persistence **source-module** signal is needed for the proving grounds (Phase 7 needs a naked "add coin save" intent on KobiiSports Resort to compile an envelope requiring save integrity, ROADMAP Phase 7 item 4). Recommended detector class `code-module-name`: a source file (`.c .cpp .h .cs .java .py .ex .rs .go .kt`) under a directory segment in `{save, saves, savegame, savedata, persistence, persist, storage}` outside the skip set. Calibrate on KSR in Phase 7 (Open Question 3). [ASSUMED]
6. Evidence strings must use one separator: the prototype produced `modules/omnicapture/vps\requirements.txt` (mixed `/` and `\`). Normalize to forward slashes so evidence is deterministic across hosts and comparable in tests.

### F6. Cache key, normalization and staleness
- `repo_key` normalizes: forward slashes, lowercase and UPPERCASE paths, trailing backslash, a subdirectory, `..` segments, 8.3 short names, and drive-letter case all produced the SAME key as the canonical spelling (measured, key `C--Users-User--claude-skills-claude-power-pack--claude-worktrees-ucep`, 7/7 same). It does NOT normalize an MSYS-form path (`/c/Users/...`, key differs) or a nonexistent / relative path (returned untouched by design: `identity.py:73-74`, "a caller that passed something which is not an existing absolute path gets it back untouched"). A Git Bash cwd can arrive in MSYS form, so the cache layer needs a small `_abs_root()`: convert `^/([a-zA-Z])/` to `X:\` on `os.name == "nt"` (the same conversion `family_scan.main_repo_of` performs for worktree pointers, `family_scan.py:146-153`), then require `os.path.isabs and os.path.isdir`, else treat the subject as unresolvable and answer UNJUDGED (never invent a key).
- `canonical_repo` stops at the first `.git` ancestor and accepts a worktree's `.git` FILE (`identity.py:46-49,85-89`), so each worktree has its OWN key and cache. That is correct for traits (a branch's structure differs) but means a Phase 7 worktree (KC `ucep/world-mutation`) starts with a cache miss: the producer must be runnable on an arbitrary subject root, and `--all` runs on main repos only (`tower_capsule.produce_all` rationale, `tools/tower_capsule.py:40-44`).
- Freshness design (recommended): reader checks the depth-1 fingerprint (`scandir` name set + `(size, mtime_ns)` of the manifest-named root files) and an age bound. Mismatch -> state STALE and every trait reads UNJUDGED (prior values may be returned as `last_known` for display, never for judging). Documented blind spot: a new file deep in the tree changes no depth-1 fingerprint; it is bounded by the age bound and by the producer's depth-2 skip check. Directory mtime on NTFS changes only when a DIRECT child is created, deleted or renamed, so editing a manifest does not move its parent directory's mtime: manifests are stat'ed individually (that is why they are in the fingerprint).

## Architecture Patterns

### System Architecture Diagram

```
 OFF the prompt path                                                     ON the prompt path (reader only)
 ───────────────────                                                     ───────────────────────────────
 scheduled task PP-Tower-Capsules (daily, main checkout) ─┐
 Owner step: add `capability_traits.py --all` (Phase 6)   │             prompt text + subject root
 SessionStart detached spawn (jit_warm.js pattern, Ph 6)  │                       │
 manual: python tools/capability_traits.py <root>         ▼                       ▼
                                       tools/capability_traits.py  ──►  archetypes.resolve(prompt, root)
                                                │                                  │
                                                ▼                                  ├─ _abs_root(root) ── unresolvable ──► traits UNJUDGED
                                    trait_scan.scan(root)                          ├─ read cache  traits_<repo_key>.json ─ missing ─► UNJUDGED (never absent)
                                     bounded os.walk (cap, budget)                 │        └─ depth-1 fingerprint + age ─ mismatch ─► STALE ─► UNJUDGED
                                     parse declared deps / markers                 ├─ intent facts: verb+object, bilingual, folded ─► EXTRACTED
                                     truncated? blind ecosystem? ─► UNJUDGED       ├─ per archetype: anchor trait + intent + modifiers + demoters
                                                │                                  │      strength = REQUIRED | CONDITIONAL | NONE   (ceiling rules)
                                                ▼                                  ├─ families = families.classify_prompt(prompt)    (independent output)
                         atomic write ~/.claude/state/tower/traits_<key>.json      ▼
                                                                          Subject{traits[10], archetypes[], families[], signature}
                                                                                   │
                                                          Phase 4: archetype/<ID> axis    Phase 5: envelope.py maps strength -> Obligation
```

### Recommended Project Structure (new files only)
```
modules/capability_runtime/
├── archetypes.py        # TRAITS, ARCHETYPES (conjunctions), Strength, intent facts, read_traits(), resolve(); stdlib + _hits + obligation constants; NEVER walks
└── trait_scan.py        # producer: scan(root, cap, budget), fingerprint(), write_cache(); stdlib only; off-path only
tools/
├── capability_traits.py        # CLI: <root> | --all | --show <root>; writes production.jsonl row; exit codes like tower_capsule.py
└── test_capability_archetypes.py   # V-ARCH-* gates, CAPABILITY_ARCHETYPES_PASS=n/m
vault/liveness/reachability_registry.json   # EDIT (shared): two PLANNED rows, same commit as the modules
```
Do NOT edit: `modules/tower/families.py`, `modules/gsd_x/cli.py`, `modules/gsd_x/tier.py`, `modules/capability_runtime/applicability.py`, `modules/capability_runtime/__init__.py`, `modules/tower/capsule.py`, `tools/tower_capsule.py`, `obligation.py`, anything under `vault/tower/`.

### Pattern 1: Trait reading = state + fact state + evidence + reason, always ten keys
**What:** every call returns all ten `TRAITS`; each reading is `{state: PRESENT|WEAK|ABSENT|UNJUDGED, fact_state: OBSERVED|UNKNOWN|EXTRACTED, evidence: [...<=5], reason}`. A cache miss yields ten `UNJUDGED/UNKNOWN` readings, never a shorter dict and never `ABSENT`.
**Mapping to existing buckets:** PRESENT/WEAK -> held (OBSERVED, or DERIVED when a rule combines two signals); ABSENT -> not-held (OBSERVED, with `reason`); UNJUDGED -> unknown (UNKNOWN, with `reason` naming the cause: `no-cache`, `stale`, `truncated`, `no-manifest-ecosystem`, `no-structural-detector`, `unresolvable-root`). Intent readings (separate field, `intent_hits`) are EXTRACTED and record the matched span (<=160 chars) as `obligation.extract_facts` does.
**Example (shape, derived from verified conventions):**
```python
# Source: shapes verified in obligation.py:125-146, capsule.py:302-325, structured_facts.py:9-26
from modules.gsd_x.mission.obligation import OBSERVED, DERIVED, EXTRACTED, UNKNOWN, FACT_STATES

TRAITS = ("persistent", "multi_actor", "bulk", "destructive", "distributed",
          "external_effect", "scheduled", "money", "policy_layers", "ui")
PRESENT, WEAK, ABSENT, UNJUDGED = "PRESENT", "WEAK", "ABSENT", "UNJUDGED"

def unjudged_reading(cause: str) -> dict:
    return {"state": UNJUDGED, "fact_state": UNKNOWN, "evidence": [], "reason": cause}

def read_traits(root) -> dict:
    """Never raises, never short: always every trait. Miss/stale/unreadable -> UNJUDGED."""
    ...
```

### Pattern 2: Archetype = anchor + intent + modifiers + demoters, with one ceiling function
**What:** an archetype is a declarative conjunction in code (`ARCHETYPES` dict, Phase 2 is the sole authority; Phase 4's JSON files describe donors and baselines and must reference ids that exist here). Fields: `anchor` (traits that must be structurally PRESENT, fresh, OBSERVED for REQUIRED), `intent` (name of the verb-object detector), `modifiers` (traits that raise consequence, never create the archetype: "Consequence strengthens an envelope; complexity alone does not", plan invariants), `anti_triggers` (intent phrases that DEMOTE REQUIRED to CONDITIONAL, never veto), `na_reasons`.

Recommended set and conjunctions (grounded in the Phase 4 donors named in the roadmap; donor files themselves are Phase 4's to verify):

| id (single path segment: `archetype/<ID>` is a directory name that `discover_subjects` walks, `baselines.py:111-136`) | anchor (STRONG structural) | intent fact (EXTRACTED) | modifiers | demoters | donor (Phase 4) |
|---|---|---|---|---|---|
| `WORLD_MUTATION` (the plan's "WORLD_MUTATION/persistent-state": use the bare id, a slash in the id creates a 3-level axis) | `persistent` | mutate durable state: write/save/persist/store/record/delete/migrate/update + state object (table, row, record, schema, migration, save, world, inventory, balance, coins, file) | `destructive`, `bulk`, `multi_actor`, `distributed`, `money` | persistent evidence WEAK only; read-only phrases (`read-only`, `solo lectura`, `dry run`, `sin escribir`) | KC `world_persistence_gate` |
| `EXTERNAL_EFFECT` | `external_effect` (runtime dependency, not dev-only) | act on the outside world: send/post/call/publish/charge/notify/email/webhook + external object | `money`, `scheduled`, `distributed`, `multi_actor` | dev-only dependency; `mock`/`sandbox`/`dry run` phrases | InfinityOps `web_surface-effect-keeps-http-status`, generalized |
| `BACKGROUND_JOB` | `scheduled` | run unattended: schedule/cron/every/nightly/daemon/worker/background/queue/loop + job object | `distributed`, `persistent`, `external_effect` | scheduler found only under a vendored/skip path | PP gsd sweep lease/heartbeat/bounded stages + KC stale-lock reclaim |

`ui`, `policy_layers`, `money`, `bulk`, `destructive`, `multi_actor`, `distributed` are modifiers (and `ui` relates to the existing `web_surface` family) in Phase 2; no further archetype is required. Local->distributed transition recompiles differently because `distributed` is a modifier of all three: a scheduled repo gaining `docker-compose.yml` moves BACKGROUND_JOB's modifiers from `[]` to `[distributed]` and changes the subject `signature` (overlapping runs on N hosts is the consequence that justifies a lease surface).

**Strength rule (the [G16] single point of enforcement):**
```
anchor_state   = structural reading of the anchor trait(s): PRESENT / WEAK / ABSENT / UNJUDGED
intent_hit     = intent detector matched (EXTRACTED, span recorded)
demoted        = any anti_trigger hit
REQUIRED     iff anchor_state == PRESENT (fresh) and intent_hit and not demoted
CONDITIONAL  iff (anchor_state == PRESENT and not intent_hit)          # repo has it, mission may touch it
              or (anchor_state == PRESENT and intent_hit and demoted)
              or (anchor_state == WEAK)                                 # weak evidence never reaches REQUIRED, with or without intent
              or (anchor_state in (UNJUDGED, ABSENT) and intent_hit)    # intent-only: EXTRACTED, cap CONDITIONAL
NONE         otherwise                                                    # reason always recorded
```
`basis` is reported (`structural`, `intent`, `structural+intent`) next to `strength`, plus `unjudged: [traits...]` so Phase 5 can write the NOT_APPLICABLE / CANDIDATE reasons. Structural-only with no intent yielding CONDITIONAL (not NONE) is a deliberate safety choice because the intent vocabulary is closed and fitted ("a lookup table wearing a rule's name", obligation.py:149-170, GSDX-M04 debt): an intent miss must not let a naked verb escape. Phase 5's mapping (CONDITIONAL -> CANDIDATE + condition) keeps this cheap. Flag for Owner review (Open Question 2). [ASSUMED]

**Intent facts must be structure, not bag-of-words.** Pattern: `ACTION ... OBJECT` within a 0-60 character window in either order, bilingual (ES+EN), matched on `families._fold`ed text through `_hits`-style word boundaries, bounded input (first 20,000 characters of the prompt) and no nested quantifiers (ReDoS). The single word `schema`, `database` or `tabla` alone never matches. Record the span. This is the construction that makes the hand-back defect unrepresentable: "schema" with no action verb yields no intent fact. A hand-back that says "I updated the table" in a repo with PRESENT persistence legitimately yields REQUIRED (it did touch it); in a repo without structure it yields CONDITIONAL, EXTRACTED. [ASSUMED vocabularies, see Assumptions]

### Pattern 3: Producer / reader split with a shared fingerprint function
`trait_scan.fingerprint(root, depth)` is the ONE implementation; the reader calls it with `depth=1`, the producer stores `fp1` and `fp2` and skips a rewalk when `fp2` and age are unchanged (8-27 ms vs 0.3-48 s). The reader never imports the walk (keep `trait_scan` out of `archetypes` imports; prove with a `Counting` wrapper that `resolve` makes zero scans).

### Cache document (recommended, schema `ucep-traits/1`)
```
{ "schema": "ucep-traits/1", "repo_key": "...", "repo": "<canonical abs path>",
  "produced_at": <epoch>, "producer": "trait_scan/1",
  "fingerprint": {"fp1": "<16 hex>", "fp2": "<16 hex>", "manifests": [{"path","size","mtime_ns"}...]},
  "walk": {"files": n, "cap": 100000, "truncated": false, "seconds": x, "manifests_parsed": k, "ecosystems": ["npm","mix"], "budget_s": 120, "budget_hit": false},
  "traits": { "<each of the 10>": {"state","fact_state","evidence":[<=5],"reason"} } }
```
Location `~/.claude/state/tower/traits_<repo_key>.json` (same directory and key function as `capsule_<key>.json`), outside every repo tree: nothing tracked, no `.gitignore` entry needed. The document carries paths and counts only, never file contents. Reader validates `schema` and that all ten trait keys exist; anything else -> UNJUDGED (`reason: "cache-malformed"`).

### Anti-Patterns to Avoid
- **Computing anything walk-shaped inside `resolve`.** One slow repo makes the child exceed the chain deadline and drops `family_block` too (audit G4).
- **Returning fewer than ten traits, or `ABSENT`, on any miss.** Absent is not zero; this is the same defect `families.py:155-166` documents for a family with no membership route ("silently OUT of every repo on the host").
- **Reusing `family_scan.scan_repo` for detection.** Its 4000-entry cap yields no `truncated` flag, and `repo_family_report` only puts a family in `unjudged` for the delegate-exception case, so a cut walk is silently OUT (`families.py:144-154`; `family_scan.py:162-205`). KC's first `pom.xml` is at entry 5,408 (`families.py:36-41`).
- **A bare module-level `REQUIRED`.** Collides in meaning with `baselines.REQUIRED` (entry keys).
- **Evaluating state paths at import** (`heartbeat.py:31` style). Compute the state dir per call so a temp HOME is honoured.
- **Treating a data file as code evidence.** `.mca`, `.db`, `level.dat` are WEAK.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Word-boundary phrase match | a new regex helper | `applicability._hits` via `families._match` (accent fold) | locked decision; the fold is already correct for Spanish prompts |
| Fact-state names | new enum or strings | `obligation.OBSERVED/DERIVED/EXTRACTED/UNKNOWN/FACT_STATES` | "ONE owner for this vocabulary" |
| Repo identity / cache key | a path slug | `repo_identity.repo_key(os.path.abspath(root))` after `_abs_root` | already the capsule key; handles case, slashes, subdir, 8.3 |
| Atomic publish | open-write-close | tmp + `os.replace` (`capsule.py:294-298`) | no observable half-written cache |
| Estate enumeration for `--all` | a new repo finder | `family_scan.find_repos` + `main_repo_of` | worktree collapse and MSYS gitdir conversion already solved |
| Dependency-name parsing | substring search of manifest text | per-ecosystem declared-name parsers (stdlib `json`, small regexes) | measured false positive from description text (F5.1) |
| Hermetic state | monkeypatching individual paths | temp `HOME`+`USERPROFILE` plus per-call state dir | the repo's own pattern (`test_family_injection.py:78-84`) |
| Freshness | a clock-only TTL | depth-1 fingerprint + age backstop | dependency-driven freshness is the repo's doctrine (`structured_facts.py:300-303`) |

**Key insight:** the only genuinely new logic is (1) the declarative archetype table with one ceiling function, (2) the bilingual verb-object intent detector, and (3) the detectors' absent-versus-unjudged bookkeeping. Everything else is composition.

## Common Pitfalls

### Pitfall 1: Vocabulary-only activation re-enters through the intent channel
**What goes wrong:** "intent fact" is implemented as a keyword list ("schema", "database", "tabla"); the hand-back defect returns one layer up.
**Why it happens:** the closed-vocabulary fitting trap documented in `obligation.py:162-170` (each unseen wording costs one more verb) pushes authors toward bag-of-words.
**How to avoid:** intent = verb + object structure inside a short window; a lone noun matches nothing; the ceiling function caps every intent-only path at CONDITIONAL with fact state EXTRACTED; the negative control feeds the literal word "schema" with no verb and asserts zero archetypes while `families.classify_prompt` DOES hit `persistent_state` for the same text (proves the instrument could have said otherwise).
**Warning signs:** an archetype with `basis == "intent"` and `strength == "REQUIRED"` anywhere in a test output.

### Pitfall 2: Absent is not zero (six ways to be UNJUDGED)
**What goes wrong:** a miss returns `{}` or ABSENT and Phase 5 turns it into a NOT_APPLICABLE (the exact "presence without reachability" defect of `families.py:155-166`).
**How to avoid:** the ONLY route to `ABSENT` is: fresh cache, walk not truncated, budget not hit, and (for dependency-class detectors) at least one manifest ecosystem visible. Otherwise `UNJUDGED` with a named cause from a closed set: `no-cache`, `stale`, `cache-malformed`, `truncated`, `no-manifest-ecosystem`, `no-structural-detector` (bulk, destructive), `unresolvable-root`. A test asserts each cause is reachable and that `set(read_traits(x)) == set(TRAITS)` in every case.
**Warning signs:** a repo with `manifest_deps=0` (ABSW2-Wii, CavEX, KobiiHub, measured) reporting ABSENT for `persistent`.

### Pitfall 3: Reusing `family_scan.scan_repo` or a capped walk without a `truncated` flag
**What goes wrong:** a 4000-entry cut reads as "OUT" (`family_scan.py:162-205` has no truncated field; KC's first `pom.xml` is entry 5,408, `families.py:36-41`). KSR cannot be walked to completion in 48 s.
**How to avoid:** own walk with `cap` (100,000, the `families._MAX_ENTRIES` convention), a wall-clock `budget_s`, and `truncated`/`budget_hit` recorded in the cache; positives found before the cut stay valid, absences become UNJUDGED.

### Pitfall 4: Cache staleness blind spots
**What goes wrong:** the depth-1 fingerprint misses a deep new file; a manifest edit does not move its directory's mtime.
**How to avoid:** manifests are stat'ed individually in the fingerprint; the age bound is the backstop; the producer's depth-2 fingerprint decides skip-if-unchanged; the blind spot is stated in the module docstring and pinned by a test that mutates only a deep file and asserts the documented behaviour (fresh by fingerprint, bounded by age), so nobody later claims more than is true. Stale evidence is not evidence: STALE reads UNJUDGED (`capsule.py:320-322` precedent).

### Pitfall 5: Windows path normalization for repo-root keys
**What goes wrong:** a Git Bash cwd (`/c/Users/...`) or a relative path gets a different key (measured: `repo_key` returns the argument untouched for both, `identity.py:73-74`), so the reader looks for a cache that was written under another key and reports UNJUDGED forever. A worktree has its own key.
**How to avoid:** `_abs_root()` (MSYS `^/([a-zA-Z])/` -> `X:\`, then `isabs` and `isdir`, else unresolvable -> UNJUDGED), then `repo_key(os.path.abspath(root))`. Evidence strings use `/`. Tests cover forward slashes, case variants, trailing separator, a subdirectory, and an MSYS form against one cache entry (the first five already resolve to one key; the MSYS form needs `_abs_root`).

### Pitfall 6: Hermetic HOME and the production ledger
**What goes wrong:** a test writes `traits_*.json` under the real `~/.claude/state/tower` (1,561 files there at Phase 1; concurrent live writers make a listing-equality bracket meaningless, Phase 1 EVIDENCE section 2).
**How to avoid:** per-call state dir; temp `HOME` + `USERPROFILE` set before any call; first gate asserts `Path.home() == Path(home)`; additionally inject `state_dir=` into the producer/reader functions so unit gates need no env; control run of the whole test with the outer HOME on an empty temp dir and assert zero files created under `<temp>/.claude/state/tower` other than the test's own `traits_*` files. The CLI's `--all` is never run by a test against the estate.

### Pitfall 7: Write-gate false positives on prose
**What goes wrong:** the Woz/scaffold write gate flags literal slop tokens even in comments (memory: prose naming such tokens trips the gate; Phase 1 EVIDENCE notes its `NA_REASONS` comment "says so without quoting the phrase as a token"). A comment in `archetypes.py` or the test that spells out the banned words can block the Write.
**How to avoid:** describe the idea without the token ("a fixed filler value", "a fake collaborator"); name test doubles "fixture" or "counting wrapper".

### Pitfall 8: The liveness gate is already red here, and the registry is shared
**What goes wrong:** an executor runs the gate, sees 63 offenders, and either panics or baselines them. **How to avoid:** compare the offender SET before and after by unit name (measured baseline: 63 offenders, 486 rows, 23 s); never `--baseline`; declare the two new units PLANNED in the same commit that creates them; read the diff hunk headers of `reachability_registry.json` before committing (another session may have edited it).

### Pitfall 9: Phase 1 files are still moving
**What goes wrong:** line citations in `modules/tower/*` drift (donegate moved 9 lines during this research; `tools/baseline_population.py` is a new untracked file; Phase 1 review fixes WR-01..04 landed at 14:30-14:44). **How to avoid:** Phase 2 creates new files only; cite symbols; `git status --short` first and bracket the dirty-path SET around each oracle.

### Pitfall 10: Prompts are Spanish
**What goes wrong:** English-only verbs. **How to avoid:** `families._fold` on prompt and phrases; both languages in every intent list; both languages in positive controls (one Spanish, one English prompt per archetype).

### Pitfall 11: Archetype id with a slash, or a non-segment id
**What goes wrong:** `WORLD_MUTATION/persistent-state` as the id makes `archetype/WORLD_MUTATION/persistent-state` and `discover_subjects` reports a three-level subject. **How to avoid:** id shape `^[A-Z][A-Z0-9_]*$`, asserted by a gate; the descriptor "persistent-state" belongs in a `description` field.

### Pitfall 12: Junctions, generated trees and giant vendored caches
**What goes wrong:** KSR's `Library/PackageCache/.tmp-*/clone/docs/migrations` produced a false `persistent` signal; a Windows directory junction may be descended by `os.walk` (Python 3.12 `os.path.islink` is False for junctions; `os.path.isjunction` exists) and could loop or balloon. **How to avoid:** extend the skip set (F5.1) and skip junction entries explicitly; the file cap and wall-clock budget bound any miss. Junction behaviour was not reproduced this session [ASSUMED].

### Pitfall 13: Coupling to the shared package `__init__`
**What goes wrong:** adding `archetypes` to `capability_runtime/__init__.py` makes every consumer (including the live prompt child) import it and edits a shared file. **How to avoid:** leave `__init__.py` untouched; import by full module path.

## Code Examples

### Depth-limited fingerprint (measured: 0.44-1.04 ms at depth 1)
```python
# Source: prototype run this session (%TEMP%\ucep_r2\fp.py, fp2.py); convention from agent_resolver.fingerprint (stat only, no content hash)
import hashlib, os
MANIFEST_NAMES = {"package.json", "mix.exs", "requirements.txt", "pyproject.toml", "pom.xml", "build.gradle",
                  "cargo.toml", "go.mod", "docker-compose.yml", "dockerfile", "vercel.json", "fly.toml",
                  "schema.prisma", "plugin.yml"}

def fingerprint_depth1(root: str) -> str:
    h, names = hashlib.sha256(), []
    with os.scandir(root) as it:
        for e in it:
            names.append(e.name)
            if e.name.lower() in MANIFEST_NAMES:
                st = e.stat()
                h.update(("%s|%d|%d;" % (e.name, st.st_size, st.st_mtime_ns)).encode())
    h.update("|".join(sorted(names)).encode())
    return h.hexdigest()[:16]
```

### Reader skeleton (never raises, never short, never ABSENT on a miss)
```python
# Source: shape from tower/capsule.read (capsule.py:302-325) with the trait contract of this research
def read_traits(root, *, state_dir=None, now=None, max_age=TRAIT_MAX_AGE_S) -> dict:
    ab = _abs_root(root)
    if ab is None:
        return _all_unjudged("unresolvable-root")
    path = _cache_path(ab, state_dir)               # os.path.expanduser("~") evaluated HERE, per call
    try:
        doc = json.load(open(path, "r", encoding="utf-8-sig"))
    except FileNotFoundError:
        return _all_unjudged("no-cache")
    except Exception:
        return _all_unjudged("cache-malformed")
    if not _valid(doc) or _age(doc, now) > max_age or doc["fingerprint"]["fp1"] != fingerprint_depth1(ab):
        return _all_unjudged("stale", last_known=doc.get("traits"))
    return doc["traits"]                            # all ten keys, validated above
```

### Gate shape (Phase 1 / family-injection convention)
```python
# Source: tools/test_family_injection.py:42-49, 67-74, 78-84 (read this session)
def check(gate, cond, evidence): ...                       # PASS/FAIL lines, counters
class Counting:                                            # proves the seam was reached
    def __init__(self, fn): self.fn, self.calls = fn, 0
    def __call__(self, *a, **k): self.calls += 1; return self.fn(*a, **k)
# final line:  print("CAPABILITY_ARCHETYPES_PASS=%d/%d  threshold=%d/%d" % (p, p + f, n, n)); return 0 if f == 0 else 1
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Families classified by prompt words alone (`classify_prompt`) | Subject = structural traits (cached) + intent facts; family kept as an independent output | this phase (D7) | a word can no longer create an archetype |
| Capsule gated whole behind one family | universal layer + family layer with separate states (`capsule.py:218-227`) | 2026-09 | same two-layer discipline applies: archetype is a layer, not a replacement |
| `gsdx-facts/1` presence = holds | `gsdx-facts/2` held / not_held / unknown with `state` + `depends_on` | GSDX-M05 | the trait cache copies the three-bucket honesty |

**Deprecated/outdated:** the ROADMAP/plan wording "WORLD_MUTATION/persistent-state" as an id (use `WORLD_MUTATION`); `family_scan.scan_repo` as a membership oracle for anything that must distinguish OUT from truncated.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Strength vocabulary `REQUIRED / CONDITIONAL / NONE` defined in `archetypes.py`, mapped by Phase 5 | F2, Pattern 2 | Phase 5 may want other words; cheap to rename before Phase 5 starts |
| A2 | Age backstop `TRAIT_MAX_AGE_S = 7 days` (capsule uses 24 h, but traits have a fingerprint; a laptop-off daily task would leave 24 h always STALE) | F6 | too long -> deep changes served stale; too short -> UNJUDGED most mornings |
| A3 | Structural-only (no intent) yields CONDITIONAL, not NONE | Pattern 2 | inflates envelopes with CONDITIONAL surfaces (anti-bloat); alternative is NONE with a recorded reason, riskier for naked verbs |
| A4 | Detector dependency vocabularies (names in the prototype: persistence ORMs/drivers, HTTP/mail/payment SDKs, schedulers, auth/realtime libs) | F5 | missed ecosystems read as ABSENT only when a manifest is visible; unknown libraries are a recall gap, not a precision gap |
| A5 | Bilingual verb/object lists for the three intent detectors | Pattern 2 | a closed list misses wordings (GSDX-M04 debt); CONDITIONAL-from-structure compensates |
| A6 | `code-module-name` persistence signal (source under a `save`/`persistence`/`storage` directory segment) is STRONG when outside the skip set | F5.5 | false positives (editor utilities) or, if WEAK, KSR cannot reach REQUIRED for Phase 7 |
| A7 | Modifier sets per archetype (distributed, money, multi_actor, ...) | Pattern 2 | wrong modifiers change only consequence text, not membership |
| A8 | `ui` threshold of 5 UI files; PP measured 5 (borderline) | F5 | flapping `ui` on small repos; make it WEAK below 20 |
| A9 | The archetype set stays exactly three (Phase 4 may change donors) | Pattern 2 | extra archetypes are additive |
| A10 | Windows directory junctions are descended by `os.walk` on 3.12 | Pitfall 12 | if false, the explicit skip is merely redundant |
| A11 | Hosting the producer: `PP-Tower-Capsules` second step or a SessionStart detached spawn are Owner steps in Phase 6 | F3 | Owner may prefer a separate scheduled task |
| A12 | Absence claims about ABSW2-Wii/CavEX/KobiiHub ("no traits") are detector blindness, not facts about those repos | F5 | none: they are recorded as UNJUDGED-class by design |

## Open Questions (RESOLVED)

All five are resolved in the plans: Q1 = R-2, Q2 = R-1, Q3 = R-3, Q4 = R-4 (02-01-PLAN.md objective), Q5 = `subject_root` takes the root as a required argument (02-01).

1. **(RESOLVED, R-2) Does Phase 4 keep `vault/tower/archetypes/<ID>.json` as pure donor/baseline descriptors, with `ARCHETYPES` in code as the sole conjunction authority?**
   - What we know: CONTEXT says Phase 2 defines archetypes in code; ROADMAP Phase 4 lists JSON definitions.
   - What's unclear: whether JSON may restate conjunctions (two truths).
   - Recommendation: code is authoritative; JSON carries `id`, `description`, `donor`, and a Phase 4 gate asserts every JSON id exists in `ARCHETYPES` and no JSON restates a conjunction.
2. **Structural-only, no intent -> CONDITIONAL (recommended) or NONE?** See A3. Planner may keep CONDITIONAL and let Phase 5's mapping control bloat.
3. **Which evidence class makes KobiiSports Resort's `engine/save/` module PRESENT?** Phase 7 needs it; calibrate the `code-module-name` detector on KSR read-only then, not now (KSR walk is >48 s).
4. **Where does the `--all` trait refresh run?** Candidate: second action of `PP-Tower-Capsules`. Owner step; record it in `02-EVIDENCE.md` section "Owner queue" and in the registry note; no Phase 2 file changes the task.
5. **Should `resolve` accept the subject root explicitly only?** Yes: G2 says `cwd` is PP under `--add-dir`; Phase 2 takes `root` as a required argument and never reads `os.getcwd()` (the capsule precedent uses `os.getcwd()` as a default, `capsule.py:228`; do not copy that default).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | everything | yes | 3.12 (`Python312\python.exe`) | — |
| git.exe (`C:\Program Files\Git\cmd\git.exe`) | commits | yes | used this session | — |
| `schtasks` | read-only verification of the scheduled host | yes | `PP-Tower-Capsules` present, Ready, last result 0 | — |
| PowerShell tool | executor convenience | NOT available to this research agent (only Bash with `# bash-safe` marker and `MSYS_NO_PATHCONV=1` for `schtasks`) | — | executors use the PowerShell tool per CLAUDE.md |
| KobiiCraft Core Files / InfinityOps / KobiiSports Resort paths | optional real-repo poles | yes (read-only; KSR walk >48 s) | — | gate prints UNJUDGED (not PASS) when a path is absent |
| Task Scheduler write access | wiring the producer | not needed in this phase (Owner step) | — | document in EVIDENCE |

**Missing dependencies with no fallback:** none. **Missing with fallback:** none blocking.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | plain Python scripts printing `<NAME>_PASS=n/m  threshold=n/m`, exit 0 iff all pass (repo convention; `check()` + `Counting` idioms above) |
| Config file | none |
| Quick run command | `$env:PYTHONIOENCODING='utf-8'; & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_capability_archetypes.py` (run directly, no `timeout` wrapper) |
| Full suite command | the new file + regression set: `test_family_baselines`, `test_family_injection`, `test_tower_capsule`, `test_tower_inheritance`, `test_tower_ratchet`, `test_baseline_generations`, `test_tower_donegate` (all green at Phase 1 close: `FAMILY_BASELINES_PASS=20/20`, `FINJ_PASS=23/23`, `TOWER_CAPSULE_PASS=16/16`, `TOWER_INHERITANCE_PASS=16/16`, `TOWER_RATCHET_PASS=21/21`, `BASELINE_GENERATIONS_PASS=16/16`, `TOWER_DONEGATE_PASS=10/10`) |
| Estimated runtime | new file < 30 s on synthetic fixtures (temp dirs, tens of files); real-repo poles optional and slower |

### Phase Requirements -> Test Map
| Success criterion | Behavior | Test type | Automated command / gate | File exists? |
|---|---|---|---|---|
| SC1 | ten traits, archetypes are conjunctions, family and archetype independent | unit | `V-ARCH-TRAITS-TEN` (set equality with the roadmap list), `V-ARCH-ID-SHAPE` (`^[A-Z][A-Z0-9_]*$`), `V-ARCH-VOCAB-SHARED` (`archetypes.EXTRACTED is obligation.EXTRACTED`, states subset of `FACT_STATES`), `V-ARCH-NA-BRIDGE` (`TRAIT_NA_REASON` values subset of `donegate.NA_REASONS`), `V-ARCH-ORTHOGONAL-A/B` (a prompt hitting `persistent_state` by word with an ephemeral repo -> family hit, zero archetypes; an InfinityOps-like fixture with a prompt carrying no family word -> archetype REQUIRED, no family) | Wave 0 (new) |
| SC2 | cache keyed by root+fingerprint; producer off path; reader read-only; miss -> UNJUDGED | integration | `V-ARCH-MISS-UNJUDGED` (no file -> ten UNJUDGED/UNKNOWN, none ABSENT, key set == TRAITS), `V-ARCH-READ-ONLY` (`Counting` wrapper on `trait_scan.scan`/`os.walk`: `resolve` makes 0 calls; latency printed, informational), `V-ARCH-STALE-MANIFEST` (edit a manifest after production -> STALE -> UNJUDGED), `V-ARCH-STALE-AGE` (injected clock), `V-ARCH-TRUNCATED` (tiny cap: positives kept, absences UNJUDGED), `V-ARCH-BLIND-ECOSYSTEM` (zero-manifest C-style fixture: dependency-class traits UNJUDGED, not ABSENT), `V-ARCH-KEY-NORMALIZATION` (slashes, case, trailing sep, subdir, MSYS form -> one entry), `V-ARCH-CACHE-OUTSIDE-REPO` (no file created under the fixture repo or `vault/`), `V-ARCH-HERMETIC-HOME` (first gate) | Wave 0 (new) |
| SC3 | intent-only yields at most CONDITIONAL with EXTRACTED | unit + drill | `V-ARCH-INTENT-ONLY-CAP` (no cache + build-intent prompt -> CONDITIONAL, fact_state EXTRACTED, never REQUIRED, `basis=="intent"`), `V-ARCH-INTENT-CONTROL` (same prompt + fresh PRESENT anchor -> REQUIRED), `V-ARCH-WEAK-CAP` (anchor WEAK -> CONDITIONAL), `V-ARCH-DEMOTE-NOT-VETO` (anti-trigger phrase demotes REQUIRED to CONDITIONAL, never NONE when structure exists), `V-ARCH-DRILL-CEILING` (in-process: replace the ceiling function with one that returns REQUIRED for intent-only -> the cap gate must FAIL; proves the gate can go red) | Wave 0 (new) |
| SC4 | negative/intent-only controls, transitions recompile differently, positive control per archetype | integration | `V-ARCH-VOCAB-OVERLAP-NEG` (docs full of "schema database table" prose, no structural markers, prompt = the bare word "schema": zero archetypes AND `classify_prompt` hits `persistent_state`), `V-ARCH-TRANSITION-PERSISTENT` (ephemeral fixture -> produce -> no WORLD_MUTATION REQUIRED; add `prisma/schema.prisma` + dependency, re-produce -> REQUIRED; `signature` and `fp1` differ), `V-ARCH-TRANSITION-DISTRIBUTED` (scheduled fixture without then with `docker-compose.yml`: BACKGROUND_JOB modifiers `[]` -> `[distributed]`, signature differs), `V-ARCH-POSITIVE-WORLD_MUTATION`, `-EXTERNAL_EFFECT`, `-BACKGROUND_JOB` (Spanish and English prompt each, evidence cites a file path), `V-ARCH-REAL-POLES` (optional: InfinityOps persistent PRESENT; ABSW2-Wii persistent UNJUDGED not ABSENT; prints UNJUDGED and does not count as PASS when the path is missing) | Wave 0 (new) |
| liveness | new units declared PLANNED, no new orphan by name | tool | before/after offender-set diff of `reachability.gate()` (read-only; baseline 63 offenders, 486 rows); registry rows present for `capability_runtime/archetypes` and `capability_runtime/trait_scan` | n/a |
| no side effects | no baseline written, no ledger row, no tracked-file change outside the registry | tool | sha256 of `vault/tower/baselines/**` before/after equal; sorted dirty-path SET before/after (only the phase's own files); temp-HOME control shows zero files outside the test's own cache files | n/a |

### Sampling Rate
- **Per task commit:** the new test file plus the touched module's neighbours (`test_family_baselines.py`, `test_family_injection.py`).
- **Per wave merge:** the full suite above, bracketed by the sorted dirty-path SET; a changed set during the run makes the verdict INCONCLUSIVE (concurrent-writers doctrine), not green.
- **Phase gate:** full suite green, the RED record for each gate family kept in EVIDENCE (write the gates first against a missing module or a deliberately weak ceiling and record `PASS=k/n` before the fix, as Phase 1 did), then `02-EVIDENCE.md`.

### Wave 0 Gaps
- [ ] `tools/test_capability_archetypes.py` — covers SC1-SC4, RED first
- [ ] a fixture builder inside the test (temp repos: ephemeral, persistent, scheduled, scheduled+docker, external-effect, zero-manifest, truncated, vocabulary-only docs) — no shared conftest needed
- [ ] Framework install: none

Mutation / falsification expected inside this phase (the "instrument could have returned the other answer" bar): (1) ceiling returns REQUIRED for intent-only -> `V-ARCH-INTENT-ONLY-CAP` red; (2) reader returns ABSENT on a miss -> `V-ARCH-MISS-UNJUDGED` red; (3) reader performs a scan -> `V-ARCH-READ-ONLY` red; (4) fingerprint ignores manifests -> `V-ARCH-STALE-MANIFEST` red; (5) intent detector degraded to a bare noun list -> `V-ARCH-VOCAB-OVERLAP-NEG` red. Each drill proves its mutation was reached (a `Counting` wrapper) before scoring. The cross-process severing drill (`tools/mutation_drill.py`, mutation ratchet) is Phase 8, not here.

### Suggested plan slicing (for the planner, not binding)
Wave 1 (parallel, disjoint files): (a) test harness RED + `archetypes.py` vocabulary/ceiling/intent/read_traits; (b) `trait_scan.py` producer with detectors and fingerprint. Wave 2: `tools/capability_traits.py` CLI + registry PLANNED rows + liveness before/after + key normalization. Wave 3: transitions, positives, orthogonality, drills, `02-EVIDENCE.md` with the Owner-queue section (producer hosting, Phase 6 registration). Every plan: pathspec-scoped commit within minutes, `git log -1 --format=%s` verified.

## Security Domain

`security_enforcement` is not set in `.planning/config.json` (only `hooks` and `workflow.skip_discuss` are present) -> treated as enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | partly | cache lives in the per-user state dir; no cross-user path; the reader trusts only its own schema-validated file |
| V5 Input Validation | yes | prompt text is untrusted: bound the scanned length (first 20,000 chars), no nested quantifiers in intent regexes (ReDoS), `json.load` of the cache validated against `schema` + ten keys, refuse malformed -> UNJUDGED |
| V6 Cryptography | no | `hashlib.sha256` only for fingerprints (non-security); no secrets |
| V8 Data Protection | yes | cache stores paths and counts only, never file contents; never read `.env*`, key files or credentials (detectors read manifests and workflow files only, bounded 20-40 KB each) |
| V12 Files and Resources | yes | `os.walk(followlinks=False)`, skip junctions, file cap + wall-clock budget, cache filename derived from `repo_key` (`[^a-zA-Z0-9]` -> `-`, no traversal), atomic replace |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt text crafted to trigger a trait (poisoned hand-back, "schema" injection) | Tampering / Spoofing | verb-object structure; intent-only capped at CONDITIONAL, EXTRACTED; enforcement is report-only until Phase 8 |
| Forged `PRESENT` in the cache inflating to REQUIRED | Tampering | consequence is an advisory/report-only envelope; schema + key-set validation; fingerprint mismatch -> UNJUDGED; the file is in the user's own state dir |
| Walk exhaustion (huge or looping tree) | Denial of Service | cap, budget, skip set, junction skip; producer is off the prompt path |
| Secret exposure through evidence strings | Information Disclosure | evidence = relative paths and dependency names only; no contents |
| Unreviewed deployment of the live hook | Elevation | no live file edited; hook registration and task wiring are recorded as Owner steps |

## Sources

### Primary (HIGH confidence, opened with Read or measured this session)
- `modules/capability_runtime/applicability.py` (1-297), `modules/capability_runtime/__init__.py`, `modules/capability_runtime/contract.py:60-214`, `modules/capability_runtime/agent_resolver.py:80-120`
- `modules/tower/families.py` (1-181), `modules/tower/capsule.py` (1-370), `modules/tower/baselines.py:98-147`, `modules/tower/donegate.py:78-108`
- `modules/gsd_x/mission/obligation.py:1-260,440-535`, `modules/gsd_x/mission/structured_facts.py:1-300,290-360`, `modules/gsd_x/cli.py:1-220`, `modules/gsd_x/tier.py:190-297`
- `modules/repo_identity/identity.py:20-139`, `modules/liveness/reachability.py:30-160,380-700`, `vault/liveness/reachability_registry.json:1-70`
- `tools/family_scan.py` (1-301), `tools/tower_capsule.py` (1-104), `tools/test_family_injection.py:1-130`, `tools/test_family_baselines.py:28-70`
- `hooks/gsd_x_tier.js`, `hooks/jit_warm.js`, `hooks/hook-dispatcher.js:783-790`, `vault/tower/families/persistent_state.json`, `web_surface.json`
- `vault/plans/ucep-naked-verb-2026-10-02.md`, `.audit.md`, ROADMAP, REQUIREMENTS, STATE, `01-RESEARCH.md`, `01-EVIDENCE.md`, `01-VALIDATION.md`
- Measurements: `schtasks /query /tn PP-Tower-Capsules /v /fo list`; walk, prototype detectors v1/v2, fingerprint depth 1-3, cache-read, import-time, `repo_key` normalization and `reachability.gate()` scripts in `%TEMP%\ucep_r2\` (not in the repo)

### Secondary (MEDIUM)
- none (no web sources were needed; this phase is entirely in-repo)

### Tertiary (LOW)
- Detector dependency lists and verb vocabularies are training knowledge (`[ASSUMED]`, A4/A5).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib plus in-repo modules, each read this session.
- Architecture: HIGH for the producer/reader split, cache conventions and the strength rule's shape (all copied from verified precedents); MEDIUM for the exact archetype conjunction table and modifier sets (A3, A7).
- Pitfalls: HIGH — each one was either measured (truncation, blind ecosystems, MSYS key, vendored false positive, content-grep noise) or read from code comments recording a prior incident.

**Research date:** 2026-10-03
**Valid until:** 2026-10-10 (Phase 1 files and the shared registry are still moving; re-read `git status --short` and symbol locations before planning)
