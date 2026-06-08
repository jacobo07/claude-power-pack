# PP Deferred Backlog — activation criteria

> Items that could NOT honestly close in the 2026-06-08 session-close
> sprint, each with an explicit activation criterion so a future session
> picks them up without re-discovery. Source audit:
> `vault/audits/session_close_2026-06-08.md`.

---

## D1 — apex-completion-standard.md bidirectional drift (verify_spp: `mirror-parity` + `drift-report`)

**State:** global `~/.claude/knowledge_vault/core/apex-completion-standard.md`
(174 350 B, LF-SHA `e553bcc`) ≠ repo copy (158 278 B, LF-SHA `03d9775`).
Both STRICT-FAIL rows share this single root cause.

**Why deferred (not a mechanical loose→PP sync):** the divergence is
**bidirectional and cross-project**, so a blind copy in either direction
destroys content (HR-006: "sync direction propagates corruption
byte-perfectly"):
- **global-only (+195 substantive lines):** *other projects'* axes —
  KobiiCraft "NL→DNA Axis" (Sesión 15), KobiMapEngine Sesiones 16-20,
  "Database Migration Doctrine". The global vault is a **shared
  multi-project accumulator**.
- **repo-only (+178 substantive lines):** PP-only clauses — C20
  MCP-Resilience, C21 Slash-Recovery, PP Dataset Baseline (v15),
  Security-First (v16), and now C26/C27 (this session).

**Activation criterion:** Owner decides the canonical model. Two options:
1. **Union-merge** — append the PP-only axes into global AND the
   cross-project axes into repo until LF-SHAs match. Tedious, must
   de-dup, must preserve both projects' content.
2. **De-scope the file from mirror-parity** — if the apex doc is
   *intentionally* a shared cross-project accumulator that cannot be
   kept in byte-parity, remove it from `verify_global_mirrors.py`'s
   PAIRS list and track PP clauses in a PP-exclusive ledger instead.

Recommended: option 2 (the file's content proves it serves multiple
projects; byte-parity is the wrong invariant for it). ~30-45 min once
the model is chosen.

---

## D2 — hooks-registration 6/7 (verify_spp: `hooks-registration`)

**State:** `verify_hooks_registration.py` reports `HOOKS_REG_PROBE=6/7`.
Sub-check `idempotency-mod` fails: 6 hook markers are built on disk but
absent from `~/.claude/settings.json`:
`restart_resume`, `output_contract_stop`, `budget_monitor`, `jit_warm`,
`cascade_check_bash`, `secret_firewall_gate`.

**Why deferred:** writing `~/.claude/settings.json` is **Owner-side** —
the classifier hard-denies agent edits to it (HR-001,
`feedback_automode_denies_self_modification`). The PP-internal half
(hook scripts) is shipped; only the registration step remains.

**Activation criterion (Owner runs):**
```
python tools/verify_hooks_registration.py        # re-run WITHOUT --dry-run to commit
```
The probe already prints "Re-run without --dry-run to commit." Once the
Owner applies it (or runs the documented `settings_merger.py register-*`
commands), the marker set reaches 11/11 and the row passes.

---

## D3 — paths+secrets residual: doc-class (35) + secret-class (9) (verify_spp: `paths+secrets`)

**State after this session's CODE-class fix:**
- `path-leak (code)`: **0** ✅ (3 benchmark JSONs allowlisted —
  machine-generated host-pinned records).
- `path-leak (doc)`: 35 in 26 files — narrative/command/setup docs that
  reference `C:\Users\User\...` (e.g. `commands/*.md`, `docs/HOOKS_SETUP.md`,
  `vault/knowledge_base/ukdl-universal.md`, dataset + audit `.md`).
- `secret hits`: 9 in 3 files — canonical **fake** AWS doc example
  access-key IDs in `tools/secret_rotation_advisor.py`, VPS-IP narrative
  in `vault/audits/manual_tools_audit_*.md`, ssh-alias narrative in
  `vault/knowledge_base/pp_dataset/pp_dataset_01_identity.md`.

`normalize_paths.py` exits 1 while `--check` sees any unallowed doc OR
secret hit, so the row stays RED until both classes reach 0.

**Why deferred:** all 35+9 are non-leaks (narrative / canonical fixtures),
but clearing them correctly means **surgical per-file allowlist entries**
(26 doc + 3 secret), not a broad glob — the allowlist is intentionally
file-specific so it never masks a *future* real leak. Doing 29 reviewed
entries exceeds the 30-min defer threshold. NOTE: the secret-class
allowlist edit also trips the HR-SECRET PreToolUse firewall when the
comment names the example-key literal — author comments without the
literal token.

**Activation criterion:** add 29 surgical allowlist entries to
`tools/normalize_paths.py::ALLOWLIST` ({"doc-path"} for the 26 narrative
docs, {"secret"} for the 3 fixture/narrative files), each with a one-line
justification matching the existing host-pinned/fixture precedent. Then
`python tools/normalize_paths.py --check` exits 0. ~30-45 min.
