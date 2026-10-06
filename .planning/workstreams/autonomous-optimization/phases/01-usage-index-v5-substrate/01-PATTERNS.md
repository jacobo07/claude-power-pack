# Phase 1: usage_index v5 substrate - Pattern Map

**Mapped:** 2026-10-06
**Plane:** gex44 (all line numbers read this session at worktree HEAD `08ee40da`)
**Files analyzed:** 11 (3 source files modified, 1 test file created, 2 test files modified, 1 ledger, 1 evidence doc, plus the reader-compat set)
**Analogs found:** 10 / 11 fully; 3 sub-patterns have no analog (listed at the end)
**Tracked-source gate (#3645):** every analog below was verified with `git ls-files` (tools/usage_index.py, tools/tis_observed.py, tools/test_usage_index.py, tools/test_usage_index_identity.py, tools/test_ao_p0.py, tools/ic_gen2.py, wiki/tools/kme_token_audit.py, wiki/tools/kme_pillars.py all print as tracked). No `.gsd/capabilities` mirror paths are used.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tools/usage_index.py` :: `SCHEMA`/DDL + `SPAWN_SCHEMA` + `_migrate_v5` | migration | batch (zero-file-open DDL) | `usage_index.py::_migrate_spawns` (146-174) | exact |
| `tools/usage_index.py` :: v5 extractors inside `on_line` (tool events, cwd, attribution, pat_hits) | service | streaming (single read pass) | `usage_index.py::_ancestry_line` (355-405) + `_spawn_results` (177-195) | exact |
| `tools/usage_index.py` :: `_iter_files` (shapes, `_archived`, skipped_shapes) | utility | file-I/O | `usage_index.py::_iter_files` (247-255) + `tis_observed.store_identity` (349-372) | exact |
| `tools/usage_index.py` :: `refresh()` additions (call_files, files cols, parse_errors, bytes_read, wall_s, files_opened) | service | CRUD / batch | `usage_index.py::refresh` (422-515) | exact |
| `tools/usage_index.py` :: `population()` verb + CLI wiring | service + CLI | request-response (DB-only read) | `usage_index.py::holdout` (757-778, typed `UNMEASURED`) + `main()` (781-827) + `kme_pillars.py` verdict/exit codes (85-88, 227-238) | role-match |
| `tools/tis_observed.py` :: `calls_from` bad-line counter | utility | streaming | `tis_observed._calls_in` `bad` counter (80-121) vs `calls_from` (124-171) | exact |
| `tools/test_usage_index_v5.py` (NEW) | test | request-response (V-gates, hermetic) | `tools/test_usage_index_identity.py` (fixtures) + `tools/test_ao_p0.py` (paired mutants) + `tools/test_spawn_outcomes.py:125-165` (seeded old-version migration) | exact (composite) |
| `tools/test_usage_index_identity.py` (modify: Linux `junction()`) | test | file-I/O | itself, lines 63-66; corpus uses relative symlinks | exact |
| `tools/test_spawn_outcomes.py` (modify: line 162 pins `== "4"`) | test | request-response | itself | exact |
| `vault/programs/incremental-cognition/gen2/ledger.json` `state.O` (NOT `frozen`) | config | CRUD | `tools/ic_gen2.py::_close_p` (680-687) | exact |
| `.planning/.../01-EVIDENCE.md` | doc | n/a | `.planning/.../phases/00-spec-.../00-EVIDENCE.md` | exact |

## Pattern Assignments

### `tools/usage_index.py` :: v5 DDL + `_migrate_v5` (migration, batch)

**Analog:** `tools/usage_index.py::_migrate_spawns` (lines 146-174) and `connect()` (108-128).

**Rule of the house (connect, 113-128):** `connect()` ONLY re-reads for the v1->v2 bump (`< V2`); every later version migrates inside `refresh()` so a reader never takes a write lock. v5 DDL must follow that: `CREATE TABLE IF NOT EXISTS` may be appended to `SCHEMA` (executescript at line 112, idempotent, additive), but `ALTER TABLE ... ADD COLUMN` goes in `_migrate_v5` under `BEGIN IMMEDIATE`.

**Core migration shape to copy (146-174):**
```python
def _migrate_spawns(con) -> None:
    row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
    if row is not None and int(row[0]) >= SCHEMA_VERSION:
        return
    con.commit()
    con.execute("BEGIN IMMEDIATE")
    try:
        row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
        if row is None or int(row[0]) < SCHEMA_VERSION:
            have = {r[1] for r in con.execute("PRAGMA table_info(spawns)")}
            for col, typ in _SPAWN_COLUMNS:
                if col not in have:
                    con.execute(f"ALTER TABLE spawns ADD COLUMN {col} {typ}")
            ...
            con.execute("INSERT OR REPLACE INTO meta VALUES('schema_version', ?)",
                        (str(SCHEMA_VERSION),))
        con.commit()
    except BaseException:
        con.rollback()
        raise
```
Column-guard idiom: `PRAGMA table_info` then `ALTER ... ADD COLUMN` only if absent; column tuples declared as module constants (`_V2_COLUMNS` line 87, `_SPAWN_COLUMNS` 134). Add `_V5_COLUMNS = (("files", "realpath", "TEXT"), ...)` the same way.

**CRITICAL trap (RESEARCH Pitfall 1):** line 152 `int(row[0]) >= SCHEMA_VERSION` and 158 `< SCHEMA_VERSION` use the global constant. Bumping `SCHEMA_VERSION = 5` (line 65) without pinning `_migrate_spawns` to its own constant (`SPAWN_SCHEMA = 4`, used at 152, 158 AND the `INSERT OR REPLACE ... schema_version` at 169-170, which must NOT downgrade/overwrite the v5 stamp) makes a v4 DB re-queue every file holding an unanswered spawn (165-167) and re-read it via `_backfill_spawns` (209-237, `open(fp ...)` at 217). `_migrate_v5` must be the only writer of `schema_version = 5`, called in `refresh()` AFTER `_migrate_spawns` (line 437 is the call site; `_canonicalize` at 436 first).

**Existing-test coupling:** `tools/test_spawn_outcomes.py:162` asserts `ver == str(ux.SCHEMA_VERSION) == "4"`; that gate goes red the moment the constant becomes 5. Update it in the SAME commit (assert `== str(ux.SPAWN_SCHEMA)`-compatible behaviour, e.g. `ver == str(ux.SCHEMA_VERSION) == "5"`, and keep the v2 -> backfill flow at 140-165 intact: it is the existing proof that the spawn backfill still works).

**Meta record idiom for typed absence (reuse):** `INSERT OR REPLACE INTO meta VALUES('<k>', json.dumps(...))` (see 168, 330-333, 508-510). Use it for `meta.skipped_shapes` and `meta.v5_migration` `{at, files_opened: 0}`.

**Additive-only constraint:** consumers read the DB: `modules/wrapper/cost_gate.py:197-198` (`from tools.usage_index import burn, advisory_line`), `modules/frontier_intelligence/token_irr.py:142-154` (read-only URI `file:...?mode=ro`, never `connect()`), plus `ux.connect` callers in `tools/estate_shadow.py:340`, `floor_probe.py:258`, `fanout_ledger.py:418`, `root_progress.py:379`, `rollover_replay.py:280`. Never rename/retype an existing column.

---

### `tools/usage_index.py` :: v5 extractors in the `on_line` callback (service, streaming)

**Analog:** `_ancestry_line` (355-405), invoked from `refresh()` at 467-468:
```python
calls, end, ep = _tis.calls_from(
    fp, offset, on_line=lambda o, s: _ancestry_line(con, path, is_sub, state, o, s))
```
`on_line(obj, start_offset)` sees every parsed dict line in file order (tis_observed.py:157-158, docstring 136-137). Add the v5 extractor either inside `_ancestry_line` or as a second function called from the same lambda; do NOT add a second parse pass (RESEARCH: ten parsers exist, none may be added).

**Helpers to reuse verbatim:** `_epoch()` (96-105) for timestamps; `state` dict passed through the lambda (463-464: `{"prompt":..., "title":..., "call_meta": {}}`) is where per-file running state lives (add `first_ts`, `last_ts`, `cwds`, `parse_errors`).

**tool_use block extraction pattern (copy the guard style from 391-405):**
```python
msg = o.get("message") if isinstance(o.get("message"), dict) else {}
for c in msg.get("content") or []:
    if (isinstance(c, dict) and c.get("type") == "tool_use"
            and c.get("name") in SPAWN_TOOLS and c.get("id")):
        inp = c.get("input") if isinstance(c.get("input"), dict) else {}
```
For tool_events drop the `SPAWN_TOOLS` condition and key on `c["id"]` (`tool_use_id` PK). Path = `inp.get("file_path")` first, then `notebook_path`/`path` (RESEARCH A3; `kme_token_audit.tool_key` lines 46-60 shows the per-tool field choice: Read/Write/Edit/NotebookEdit -> `file_path`, Grep/Glob -> `path`, Bash/PowerShell -> `command`).

**Upsert-not-REPLACE rule (395-403):** "Upsert, not REPLACE: a re-read must not erase a recorded result." Use `INSERT ... ON CONFLICT(tool_use_id) DO UPDATE SET <non-result columns only>` so `result_bytes`/`result_chars`/`is_error` survive.

**tool_result -> UPDATE pattern (copy `_spawn_results`, 177-195):**
```python
body = c.get("content")
if isinstance(body, list):
    body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
con.execute("UPDATE spawns SET result_ts=?, is_error=?, result_head=? "
            "WHERE tool_use_id=? AND result_ts IS NULL", (...))
```
Reuse this exact str-or-list flattening for `result_chars` (`len(body)`) and `result_bytes` (`len(body.encode("utf-8", "replace"))`). It runs on `type == "user"` lines (line 372-373) before the `promptId` branch. Store NULL until a result is seen, never 0 (RESEARCH DDL comment).

**Input hash (copy `spawn_input_hash`, 139-143):** `hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:16]`, but over canonical JSON `json.dumps(inp, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`; do NOT call `spawn_input_hash` itself (it hashes only subagent_type+prompt).

**Pattern hits (single source of truth, `wiki/tools/kme_token_audit.py`):**
```python
KME_RE = re.compile(r'KobiMapEngine|KobiiMapEngine|\bKME\b|\bkme[-_/\\]|mapengine|map_engine|KMEIP', re.I)   # line 10
PATH_KME_RE = re.compile(r'kme|mapengine', re.I)                                                         # line 11
# tool-use counting, lines ~117-127:
inp = json.dumps(c.get('input'), ensure_ascii=False)
h = len(KME_RE.findall(inp))
sess['tool_uses'] += 1
if h:
    sess['tool_uses_kme'] += 1
```
Store `pat_hits` per event (JSON, only when > 0) and assert in a gate that the stored `patterns.regex == kme_token_audit.KME_RE.pattern` (import the pattern; never hard-copy). User-text rule (kme_token_audit.py:33-42): count hits only when `'<command-name>' not in tx[:400]` and `'Base directory for this skill' not in tx[:200]` and `len(tx) < 20000` (plus `isMeta` exclusion per RESEARCH); text flattening reference is `kme_token_audit.text_of` (lines 14-30).

**Classifier to reproduce in SQL (kme_token_audit.py:233-242):**
```python
share = s['tool_uses_kme'] / s['tool_uses'] if s['tool_uses'] else 0.0
if PATH_KME_RE.search(s['project']) or (s['cwd'] and PATH_KME_RE.search(s['cwd'])):  return 'KME_PATH', 1.0
if share >= 0.30 or (s['user_kme_hits'] >= 2 and share >= 0.10):                      return 'KME_STRONG', share
```
and the time cut (`wiki/tools/kme_pillars.py:291-314`, `make_keep`): a timestamp-less line inherits the last timestamp seen in its file; leading timestamp-less lines take the file's first parseable timestamp; a file with no timestamp keeps nothing; drop `t > until`. Mirror this in the extractor so `ts` on tool events/user_hits is the inherited timestamp, otherwise `ts <= until` will not match the frozen population.

**cwd/path normalization:** records carry the RECORDING machine's Windows paths; parse with `ntpath`/`PureWindowsPath` when `^[A-Za-z]:[\\/]`, never `os.path.realpath` (RESEARCH Pitfall 7). The only in-repo path-key convention is `tis_observed.project_key` (340-346: `re.sub(r"[^A-Za-z0-9]", "-", str(path))`); use it to map a cwd to its store dir name for the `home` role.

**Secrets rule:** store hash + byte counts + normalized path only; never raw tool input/result text (HR-SECRET-002). `spawns.result_head` (RESULT_HEAD = 200, line 136) is the existing ceiling; do not widen it.

---

### `tools/usage_index.py` :: `_iter_files` shapes, `_archived`, skipped_shapes (utility, file-I/O)

**Analog:** `_iter_files` (247-255) over `tis_observed.store_identity` (349-372).
```python
def _iter_files(proj: Path):
    """(path, is_subagent), one spelling per physical transcript (store_identity)."""
    if not proj.is_dir():
        return
    for sub in _tis.store_identity(proj)[0]:
        for jf in sub.glob("*.jsonl"):
            yield jf, 0
        for jf in sub.glob("*/subagents/*.jsonl"):
            yield jf, 1
```
`store_identity` returns `(canonical store dirs, {listed spelling: resolved path})`; identity = `os.path.realpath` of each IMMEDIATE child dir, keyed `os.path.normcase(str(real))`, first listing wins (366-372). It dedupes STORE DIRS only: `_archived` is one such child whose children are PROJECT dirs, so both globs match nothing (RESEARCH: 255 files silently un-ingested = the silent zero to remove). Extend by branching on `sub.name == "_archived"` and iterating its project dirs with the same two globs, yielding an `archived` flag; keep the generator's `(path, is_sub)` contract for existing callers by adding a parallel generator (e.g. `_iter_files_v5` returning a small tuple) and leaving `_iter_files` intact if any consumer imports it (grep before changing the signature).

Record unmatched `*.jsonl` (`_preserved`, `_empty_shells`) via an `os.walk` diff into `meta.skipped_shapes` as `{count, sample[:5]}` (typed absence; same `INSERT OR REPLACE INTO meta` idiom as 168/330). `*.jsonl.bak-*` is not `.jsonl` and stays ignored.

**Realpath of the transcript file** (criterion 1 "realpath + content identity"): `os.path.realpath(path)` stored in `files.realpath`; the files' `path` column stays the `store_identity` canonical spelling (so `_canonicalize` 296-338 and `_PATH_COLUMNS` 261-264 keep working). If you add path-bearing columns/tables (`call_files.file`, `tool_events.file`, `file_projects.file`, `file_cwds.file`, `user_hits.file`), ADD THEM to `_PATH_COLUMNS` (kind `"plain"` for non-PK, `"pk"` when the column is in the PK) or alias rewrites will skip them (the identity gate `paths()` in test_usage_index_identity.py:84-90 enumerates the same list; extend it too).

---

### `tools/usage_index.py` :: `refresh()` additions (service, batch/CRUD)

**Analog:** `refresh()` itself (422-515).

**Skip rule to keep (449-450):** `if prev and prev[1] == st.st_size and prev[2] == st.st_mtime_ns: continue` (stat-gate, zero bytes). Resume at `offset = prev[0] if prev else 0` (455). Rewritten-file restart (457-460) deletes `calls`/`quota` rows for the file: also delete this file's `call_files`, `tool_events`, `user_hits`, `file_cwds`, `file_projects` there, and reset `v5_from = 0`.

**Per-file transaction idiom (495-500):** one `INSERT OR REPLACE INTO files(...)` then `con.commit()` per file, so PARTIAL is resumable. Extend the column list with `realpath, store, project, archived, session_key, first_ts, last_ts, parse_errors, error, v5_from, content_id`. NOTE the `INSERT OR REPLACE` rewrites the whole row: carry forward unchanged v5 columns (read them before the REPLACE) or switch to `INSERT ... ON CONFLICT(path) DO UPDATE` so a delta refresh does not null `v5_from`.

**Occurrence table next to the global upsert (470-491):** the `calls` upsert keeps `ON CONFLICT(k) DO UPDATE` (first row's `file` wins; the measured 18-call order dependence). Add, in the same loop: `con.execute("INSERT OR IGNORE INTO call_files(k, file) VALUES(?,?)", (_key(path, c["key"]), path))`. Do not change the `calls` upsert.

**Typed outcome return (514-515) to extend:** current return `{"status","files_read","calls_upserted","pending","backfill_pending","error"}`. Add `files_opened`, `bytes_read` (sum of `end - offset` per file read), `wall_s` (`time.monotonic()` delta; `t_end` is already derived from it at 430), `parse_errors`, `skipped_shapes`. Status stays `OK|PARTIAL|FAILED`; add a typed degradation (e.g. `status: "OK"` with `parse_errors > 0` surfaced, or `PARTIAL`/`DEGRADED` — decide in the design step) and persist in `meta.last_refresh_status` (508-510, the JSON already carries `error`, `pending`). Failure style to copy (505-506): `except Exception as e:  # noqa: BLE001 -- typed, never silent` then `status, err = "FAILED", f"{type(e).__name__}: {e}"`. Parser errors per file: wrap per-file work so one unreadable file records `files.error` and continues, never aborts the pass silently.

**Cold-build trap:** CLI default `--since-days 21` (main, line 788) with `since_epoch=time.time() - a.since_days * 86400` (795) prunes by mtime (445-446). A cold build on the frozen copy needs `--since-days 0`/`--all` mapping to `since_epoch=None`, and a gate asserting `files_read == files_total`.

---

### `tools/tis_observed.py` :: `calls_from` bad-line counter (utility, streaming)

**Analog:** `_calls_in` (80-121) already counts `bad`:
```python
try:
    obj = json.loads(raw)
except json.JSONDecodeError:
    bad += 1
    continue
```
whereas `calls_from` (151-154) is the silent twin:
```python
try:
    obj = json.loads(text)
except json.JSONDecodeError:
    continue
```
Make it additive and default-compatible: accept an optional mutable out-param (e.g. `stats: dict | None = None`, incremented as `stats["bad"] += 1`) rather than changing the 3-tuple return `(calls, pos, entrypoint)`, which `tools/test_usage_index.py:89,100,105` and `usage_index.py:467` unpack. Keep the unterminated-trailing-line behaviour (145-146 `if not raw.endswith(b"\n"): break`) as NOT an error; it is pinned by `V-UIX-PARTIAL-LINE` / `V-UIX-PARTIAL-LINE-CONTROL` (test_usage_index.py:97-107). Also count an `OSError` from `open(path, "rb")` at the usage_index call site, not here.

---

### `tools/usage_index.py` :: `population()` verb + CLI (service, request-response)

**Analog 1 (typed UNMEASURED return):** `holdout()` (757-766):
```python
if not cal or not hold:
    return {"verdict": "UNMEASURED", "reason": "need one calibration and one holdout reading"}
```
**Analog 2 (verdict vocabulary / exit codes):** `wiki/tools/kme_pillars.py:85-88`: `VERDICTS = (">= 3 %", "< 3 %", "STRADDLES", "UNMEASURED")`, `EXIT_OK, EXIT_USAGE, EXIT_UNMEASURED = 0, 2, 3`; and `materiality` (227-238): `if population_match == "drifted": return "UNMEASURED", "population_not_reproduced"`; `population_match` values `exact|drifted` (kme_pillars.py ~2074-2194, `per_project` rows + `deltas` reconcile table). RESEARCH specifies `population()` returns `EXACT|DRIFTED|UNMEASURED`; `DRIFTED`/`UNMEASURED` exit non-zero (use 3 for UNMEASURED to match the champion, 2 for usage/refusal). Empty population -> `UNMEASURED` (never EXACT).

**CLI wiring to copy (781-827):** `ap.add_argument("cmd", choices=[...])` (783: add `"population"`), existing `--db`, `--proj`, `--deadline`, `--until` (790, already defined for replay), then `if a.cmd == "population": print(json.dumps(r, indent=1)); return <exit>`. Add `--root` (alias of `--proj`), `--scope kme-l`, `--include-archived`, `--all`. Reads the DB only (no transcript open). `print(json.dumps(...))` + int exit code is the house style (798, 800).

**Frozen-scope filter literals to implement (RESEARCH, from kme_pillars.py:1638-1639):** dir scope regex `'KobiiCraft-Core-Files|kme-wt-arena2'` (Run 6 `--project-filter`), session = `(project, first path component)` = `files.session_key`, KME selection = class in `KME_PATH|KME_STRONG` OR host gex44 and project matches `kobii-a[0-9]` (`wiki/tools/kme_report.py:35-39`), `until = 2026-10-03T16:13:37Z`. Hermetic gates assert relationships; the literals 102 / 34,871 / 11,549,646,300 appear only in the corpus measurement step.

---

### `tools/test_usage_index_v5.py` (NEW; test, V-gates)

Three analogs, copy each for a different job.

**(a) Gate printer + footer + hermetic tempdir + imports** (`tools/test_usage_index.py:1-37, 79-84` and `test_usage_index_identity.py:10-33`):
```python
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import usage_index as ux  # noqa: E402
PASS = FAIL = 0
def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond); FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")
...
print(f"USAGE_INDEX_PASS={PASS}/{total}  threshold={total}/{total}")
return 0 if FAIL == 0 else 1
```
Final line for the new file: `USAGE_INDEX_V5_PASS=n/n  threshold=n/n` (global rule `~/.claude/rules/python/testing.md`: `DOMAIN_PASS=n/n threshold=n/n`). Gate names `V-UX5-*` (RESEARCH list: V-UX5-SCHEMA, -TOOL-EVENT, -CWD, -MIGRATE-ZERO-REREAD, -MIXED-BOTH, -MIXED-CONTROL, -HISTORIES-NOT-MERGED, -COPY-ONCE, -ALIAS-ONCE, -ARCHIVED-RULE, -SHAPE-SKIP-VISIBLE, -PARSE-ERROR-SURFACED, -PARTIAL-LINE-NOT-ERROR, -EMPTY-REFUSES).

**(b) Fixture builders** (`test_usage_index_identity.py:36-81`): `iso(h)`, `asst(mid, h, sess, spawn=None, quota=False)`, `user(pid, h, sess)`, `build_real(proj, name, sess)` write `<proj>/<name>/<sess>.jsonl` and `<sess>/subagents/agent-a.jsonl` + `.meta.json`. Extend `asst` to take `tool_use` blocks (`{"type":"tool_use","id":..,"name":"Read","input":{"file_path":"C:\\Users\\User\\Apps\\proj\\x.py"}}`) and add `tool_result` user lines (`{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":..,"content":"..."}]}}`) and a `cwd` field with Windows-style paths. Fixture dirs use temp dirs only (`tempfile.TemporaryDirectory()`, never the corpus).

**(c) Paired control / mutant discipline** (`tools/test_ao_p0.py`):
- docstring contract (lines 8-10): "a mutant passes only when the judge reports the defect AND the matching clean control was clean, so a judge that refuses everything cannot pass."
- `gate(name, cond, evidence)` + `guarded(name, fn)` (lines 67-79: an exception is a FAIL, never a crash hiding later gates).
- clean control first, then mutants (lines 218-224): `harness_ok = not ctrl_spec and not ctrl_bind` then `gate("V-AOP0-MUT-...", harness_ok and _has(p, "READY"), ...)`.
- RED-then-GREEN in-process drill (`tools/test_gex44_env_preflight.py:842-845, 905-955`): `_patch(obj, attr, value)` returns a restore lambda; `MUTANTS = [(label, apply, groups, [target gates])]`; `run_drill()` runs the unmutated control, applies each mutant, requires every target gate to turn False ("KILLED"/"SURVIVED"), then re-runs clean (`DRILL-CLEAN-AFTER-MUTANTS`) and prints `DRILL killed=n/n`. Copy this for the mutants RESEARCH requires: drop the occurrence insert; make `population()` return EXACT on empty; remove the `parse_errors` increment; remove the archived exclusion; bypass `store_identity` dedup (`_patch(ux._tis, "store_identity", ...)` works in-process); make migration touch a file offset; pin `_migrate_spawns` back to `SCHEMA_VERSION` (must turn V-UX5-MIGRATE-ZERO-REREAD red). In-process `_patch` cannot remove a line inside a function body: for those (parse_errors increment, archived exclusion) run the gate against a temp copy of `usage_index.py` with a string replacement and import it via `importlib.util.spec_from_file_location` (no in-repo analog for source-text mutants of a tool; `ic_gen2.py::selftest` `mut(...)` at 749 mutates data, not source).

**(d) Seeded old-version migration** (`tools/test_spawn_outcomes.py:133-165`): build a DB with `ux.refresh`, then `ALTER TABLE spawns DROP COLUMN ...` + `UPDATE meta SET v='2' WHERE k='schema_version'`, reopen via `ux.connect`, assert offsets unchanged (`V-SPOUT-CONNECT-NO-RESET`: `reset = [p for p, o in con.execute("SELECT path, offset FROM files") if o != offsets[p]]`), then refresh and assert `calls_upserted == 0`. Copy for V-UX5-MIGRATE-*: seed a v4 DB (SCHEMA_VERSION 4 stamp, no v5 columns/tables, plus a spawn with `result_ts IS NULL` so the spawn-backfill trap is armed), run `connect()` + `refresh()` with the read spy active.

**(e) Alias/junction on Linux** (`test_usage_index_identity.py:63-66` fails today: `subprocess.run(["cmd", "/c", "mklink", "/J", ...])` -> `FileNotFoundError`). Hermetic helper for the new file: `os.symlink(target, link, target_is_directory=True)` (the corpus itself uses relative symlinks, e.g. alias `C--alias` listing BEFORE `C--zreal`, test lines 98-99, so the pre-fix first-writer order bug is reproduced). Keep the INCONCLUSIVE-exit-2 convention (line 9, 100-101) when the link cannot be created.

---

### `tools/test_usage_index_identity.py` (modify: Wave-0 Linux junction fallback)

**Analog:** itself. Replace the body of `junction()` (63-66):
```python
def junction(link: Path, target: Path) -> bool:
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, text=True)
    return r.returncode == 0 and link.is_dir()
```
with an `os.name == "nt"` branch keeping this call, and an `else` branch `os.symlink(str(target), str(link), target_is_directory=True)` guarded by `try/except OSError: return False`. Beware the seeded-alias migration block (135-136) builds backslash-terminated paths `str(alias) + "\\"`: on POSIX use `os.sep`; `_canonicalize` itself uses `os.sep` (309). Baseline first: `python3 tools/test_usage_index_identity.py` currently crashes with 0 PASS on this host (RESEARCH, Pitfall 6); record the post-fix PASS count in the evidence.

---

### `vault/programs/incremental-cognition/gen2/ledger.json` `state.O` (config) and `01-EVIDENCE.md`

**Analog for the state row shape:** `tools/ic_gen2.py::_close_p` (680-687):
```python
ev = [{"kind": "measurement", "ref": EV_M}]
...
e["sha256"] = _sha(files[e["ref"]])
led["state"]["P"] = {"terminal": ALLOWED_LOSS, "reason": reason, "evidence": ev, "savings": []}
```
Row for O: `{"terminal": "IMPLEMENTED_AND_VERIFIED", "reason": "...", "evidence": [{"kind":"measurement","ref":"<repo-relative tracked path>","sha256":"<hex>"}, ...], "savings": []}`. Vocabulary (`ledger.json` `terminal_vocabulary`): `IMPLEMENTED_AND_VERIFIED, MERGED_INTO_EXISTING_OWNER, FALSIFIED_OR_REJECTED_BY_EVIDENCE, DEFERRED_STRONGER_OWNER, AUTHORIZATION_BOUND, EXTERNAL_BLOCKED, RESEARCH_INSUFFICIENT_EVIDENCE`. Evidence files are sha256-pinned (`ic_gen2.py:257-260, 543-549`, `_sha` at 624 normalizes CRLF) so the evidence file must be committed in its FINAL form BEFORE the ledger row is written. Edit ONLY `state.O`; `frozen` (pillar O rule at `frozen.pillars[id=O]`) is immutable (CONTEXT). Verify with `python3 tools/test_incremental_cognition_program.py --generation 2 --status` (expect `"open": ["M","P","Q","R"]`, `"violations": []`) and `--generation 2 --selftest`.

**Analog for 01-EVIDENCE.md:** `.planning/workstreams/autonomous-optimization/phases/00-*/00-EVIDENCE.md`: header line with commits + branch + `Plane: gex44`; `## Criterion results` table with columns `ROADMAP criterion | artifact | proof command | observed line`; `## Verifier output (fresh processes, after <hash>)` with each command, its exit code, and the literal last line (e.g. `AOP0_PASS=22/22  threshold=22/22`). Add the phase-required `Product Delta` and `Intelligence Delta` sections and, for the two corpus steps, the command, the `plane: gex44` label, parity numbers with the 18-call reconcile row, and cold-build/delta wall + `bytes_read` + `/proc/self/io` rchar + page-cache state (RESEARCH, Measured Cost Baseline).

## Shared Patterns

### Typed absence, never a silent zero
**Source:** `usage_index.py` (`holdout` 765-766; `spawns` NULL result until observed 177-195; `_index_subagent_meta` 408-419 "A missing or unreadable meta is recorded with NULLs: typed unknown, never a guess"; `refresh` 505-506 `"FAILED"` with the error string).
**Apply to:** every new v5 fact. Legacy files carry `v5_from IS NULL` (UNMEASURED), `result_*` NULL until a result is seen, `<unattributed>` is a counted bucket, empty population -> `UNMEASURED`, unmatched file shapes -> `meta.skipped_shapes`.

### Additive schema + `BEGIN IMMEDIATE` + in-transaction version re-check
**Source:** `usage_index.py` 146-174 (shown above); also `_canonicalize` 296-338 (`con.commit()`, backup, `BEGIN IMMEDIATE`, `try/except BaseException: con.rollback(); raise`).
**Apply to:** `_migrate_v5` and any backfill verb (`backfill-v5` is opt-in and deadline-bound, never part of default refresh).

### Parameterized SQL only; no raw text stored
**Source:** every statement in `usage_index.py` uses `?` placeholders (e.g. 369-371, 474-490); f-strings appear only for table/column names from module constants (271, 325-327).
**Apply to:** all v5 inserts/updates/queries. Tool inputs/results are untrusted data and may hold secrets: store hash, byte counts, normalized path (HR-SECRET-002).

### Single-pass incremental read; one reader
**Source:** `tis_observed.calls_from` (124-171) via `refresh()` 467-468; stat-gate skip 449-450.
**Apply to:** every extractor. No second parse; delta cost == appended bytes (+ the declared tail-overlap if a tail fingerprint is used; Open Question 2 decides the `content_id` scheme).

### Store identity is consumed, never derived
**Source:** `usage_index.py` comment 240-244 and `tis_observed.store_identity` 349-372.
**Apply to:** shape iteration, alias handling, and `_PATH_COLUMNS` (261-264): any new path-bearing column or table must be listed there or alias rows will not be canonicalized.

### Fail-open vs surfaced failures in readers
**Source:** `modules/frontier_intelligence/token_irr.py:142-154` reads through `mode=ro` URI, never `connect()`; `cost_gate.py:197-198` imports `burn`/`advisory_line` by name.
**Apply to:** keep `burn`, `advisory_line`, `connect`, `window`, column names of v4 tables stable; run the consumer set in Wave 0 (`tools/test_estate_shadow.py`, `test_fanout_ledger.py`, `test_root_progress.py`, `test_spawn_outcomes.py`, `test_spawn_policy_v2.py`, `test_async_spawns.py`, `test_goal_journey.py`, `test_execution_shape.py`, `test_displacement.py`, `test_store_identity_consumers.py`, `test_frontier_intelligence_os.py`, `test_token_ground_truth_junction.py`).

### V-gate style
**Source:** `tools/test_usage_index.py` (`ok()` printer + `X_PASS=n/n  threshold=n/n` footer), `tools/test_ao_p0.py` (paired control + mutant, `guarded`), `tools/test_gex44_env_preflight.py` (`_patch`, `MUTANTS`, `run_drill`).
**Apply to:** `tools/test_usage_index_v5.py`; gates assert relationships on fixtures, literals only on the real-corpus step.

## No Analog Found

| File / sub-pattern | Role | Data Flow | Reason |
|---|---|---|---|
| open-spy gate (wrap `builtins.open`/`os.open`/`Path.open`, assert 0 opens under the fixture root during `connect()+_migrate_v5`, with a positive control that DOES fire on a grown file) | test | file-I/O | Existing migration gates measure by row/offset equality (V-UXID-MIGRATION-TOTALS, V-SPOUT-CONNECT-NO-RESET), which cannot prove no read happened; use RESEARCH Pattern 1 and pair it with the v2-era-DB / grown-file control. Also assert `refresh()` returns `files_opened == 0`, `bytes_read == 0` on an unchanged tree (counters are new). |
| `content_id` fingerprint (size + head 64 KiB + tail 64 KiB from buffers already read) and `dup_of` | service | streaming | No content hashing of transcripts exists in `usage_index` (stat-gate only). Only precedent for hashing style is `spawn_input_hash` (139-143) and `_backup` sha256 (283). Design decision per RESEARCH Open Question 2. |
| mutants that edit the source text of a tool (remove a line, flip a comparison) | test | batch | Repo mutant drills patch attributes in-process (`test_gex44_env_preflight.py`) or mutate data (`ic_gen2.py`); source-text mutants need a temp copy + `importlib` load. |
| attribution registry (distinct launch cwds -> project roots; segment-prefix match on normalized Windows paths; `home`/`touched` roles) | service | transform | Nothing in the repo derives project roots from data; use RESEARCH Pattern 3. Nearest helpers: `tis_observed.project_key` (340-346) and `kme_report.py:35-39` (`kobii-a[0-9]` host rule). Segment-prefix, not string-prefix (`...Core-Files` vs `...Core-Files-KobiCraftServer`). |

## Metadata

**Analog search scope:** `tools/` (usage_index, tis_observed, test_usage_index*, test_spawn_outcomes, test_ao_p0, test_gex44_env_preflight, ic_gen2), `wiki/tools/` (kme_token_audit, kme_pillars, kme_report), `modules/wrapper/cost_gate.py`, `modules/frontier_intelligence/token_irr.py`, `vault/programs/incremental-cognition/gen2/ledger.json`, `.planning/workstreams/autonomous-optimization/phases/00-*`.
**Files read in full or by range:** 13; no file under `/home/kobii/kme-corpus` was read.
**Pattern extraction date:** 2026-10-06
