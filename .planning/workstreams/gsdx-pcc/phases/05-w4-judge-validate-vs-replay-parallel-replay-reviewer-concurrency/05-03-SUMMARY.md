# 05-03 SUMMARY -- Review ticket A->B->A hole (R05)

`tools/evidence_bundle.py`: `ticket()` still returns `(path, nonce)` but now also writes a stat journal
(mtime_ns, size, inode; ctime off Windows) and a read-only snapshot of the ticketed bytes.
`write_review` branches: a reply echoing `snapshot_line(nonce)` is checked by re-hashing the snapshot; a live read
is refused when the journal moved; a ticket without a journal fails closed.

## Gates (laptop plane)
- `EVB_ABA_PASS=10/10  threshold=10/10` (logs/05-03-aba-green.log)
- `EVB_PASS=21/21  threshold=21/21` (logs/05-03-evb.log) -- existing suite unchanged and green

## Drills (laptop plane, copy_dirs vendor/genesis-suite so the intake bridge exists in the isolated copy)
| id | mutant | verdict |
|----|--------|---------|
| d6 | journal comparison skipped | KILLED (V-ABA-LIVE-REWRITE-STALE), control valid |
| d7 | snapshot re-hash removed | KILLED (V-ABA-SNAPSHOT-TAMPERED), control valid |

## Deviations
- Executed before 05-02 (independent files); 05-02 follows.
- No separate RED log: implementation was written first; the two drills prove the gates fail when the behaviour is removed.
- First drill attempt returned CONTROL_INVALID (isolated copy lacked the vendored package); fixed with `copy_dirs`.
- Residual limit recorded in `collect`: a writer that restores mtime and inode on Windows defeats the live journal; only the snapshot read proves that case.
