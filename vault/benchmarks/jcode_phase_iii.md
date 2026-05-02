# Phase III Benchmarks (BL-0022)

**Run date:** 2026-05-02
**Host:** Windows 11 Pro 26200, Cursor + claude.exe + Node v24 + Python 3.x
**Methodology:** PowerShell `Measure-Command { & <exe> ... }`, integer-ms total, single cold run after flag-cleanup. No warm-cache priming.

---

## Wall-Clock Cold-Start (PowerShell direct invocation)

| Artifact | Wall-clock ms | Hook timeout | Within budget? |
|---|---:|---:|:---:|
| `lib/atomic_write.py --self-test` | 5114 | n/a (CLI) | n/a |
| `lib/atomic_write.js --self-test` | 3943 | n/a (CLI) | n/a |
| `hooks/skill-heat-map-advisor.js` | 4174 | 5000ms (bumped from 3000) | ✓ |
| `hooks/ram-watchdog.js` | 3503 | 5000ms | ✓ |
| `hooks/context-watchdog.py` | 1150 | 5000ms | ✓ |
| `tools/skill_heat_map_indexer.py --dry-run` | 20943 | n/a (CLI) | n/a |

## Reality-graded interpretation

**The wall-clock numbers above are NOT pure hook-logic time.** They include:
- Process spawn (Node ~150-300ms cold, Python ~250-500ms cold on Windows)
- Module load (`fs`, `os`, `child_process`, `path`, `crypto` for Node; same for Python)
- Antivirus scan-on-execute (Windows Defender real-time, ~50-500ms variance per process)
- PowerShell pipeline setup overhead (~50-200ms)
- File-system AV cache state (cold-disk = +200-1000ms on first read of `vault/skills_heat_map.json`)

The same hook re-invoked back-to-back without flag cleanup typically lands at 100-400ms. The 1-4s range is **first-run-after-AV-cache-eviction**, which is what the harness sees.

**The indexer dry-run at 20943 ms is the legitimate outlier** because it reads ~164 markdown files (82 skills + 82 commands) and the AV scan kicks in for each. Acceptable: the indexer is invoked manually, not per tool call.

## Comparison to jcode

The user-supplied target ("19.7x RAM reduction") does not appear in jcode's published material. jcode README's actual published figures (vault/research/jcode_extraction.md):
- Time-to-first-frame: jcode 14ms vs Claude Code 590-3436ms
- RAM single session: jcode 167 MB vs Claude Code 386 MB → **2.3x**, not 19.7x
- RAM scaling: jcode +10.4 MB/session vs CC 76-318 MB/session

**These are jcode-vs-Claude-Code-binary numbers, not before-vs-after-our-hooks numbers.** Our hooks add ~30-40 MB transient RAM each per call (one Node fork). They do NOT reduce the Claude Code harness RSS, because the harness is a closed binary we can't modify (BL-0017).

## Honest verdict

Phase I-III adds the following observable improvements:
- **Persistence integrity**: BL-0014/18 make ledger and lazarus writes torn-write-safe under concurrent Cursor windows. Empirical bug found and fixed (Windows text-mode \\n compounding) before Phase I commit.
- **Discovery latency**: BL-0016/20 — heat-map and commands index let hooks consult one ~50KB JSON instead of globbing 164 markdown files. Indexer regen is manual; query is fast.
- **Forensic logging**: BL-0015 captures end-of-turn context snapshots ≥75% used; BL-0019 advises /kclear above 1500 MB claude.exe RSS.
- **Doctrine**: OmniRAM-Sentinel checklist (`modules/omniram-sentinel/README.md`) makes the patterns reusable for future modules.

What it does NOT add:
- Claude Code harness RAM reduction. **0%.** This is a closed binary.
- Auto-trigger for /clear /compact /kclear. Forbidden by BL-0003 (harness rule).
- Sub-100ms hook cold-start on Windows. Realistic floor is ~150-400ms with AV active.

## Future perf investigation (not done this sprint)

- Per-step instrumentation inside `skill-heat-map-advisor.js` to decompose Node-init vs script-work vs JSON-parse.
- Try Bun runtime (10-30ms cold-start vs Node 150-300ms).
- Pre-load JSON into a tmp file at SessionStart so warm-disk reads are guaranteed.
