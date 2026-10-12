# WU-APR7 -- Close the independent-review findings on APR-2..4 (woz VETO + pp-code-reviewer WARNING)

Common brief: `PROGRAMME.md`. Findings with file:line: `REVIEW-APR.md` sections "Independent review 1/2" (read them first).
Route L. cwd `C:\Users\User\Apps\wt_apr`. RED first: every fix lands with a V-gate that fails on the current code.

Fix, smallest change each, no new engine:
1. Dup-arm (woz F1 / pp LOW-2, gsdx_chain.py:592-595): the re-read under the lock checks the chain unit's ORIGINAL packet
   (and its residual) on every arm, residual or not. Gate: a base-packet mission created between decide and _arm -> `running`, no arm.
2. Atomic facts (woz F2): `_wr` writes tmp + fsync + os.replace (reuse gsd_mission's atomic writer, do not add a third).
3. One lock (woz F3): try_seal / finalize take the same per-goal `Exclusive` as tick. Gate: two real processes, one finalize.
4. Seal scope (pp HIGH-1, :244): seal only when status in {None, UNREADABLE, STUB}; explicit PARTIAL / IN_PROGRESS is the
   worker's verdict. Gate: PARTIAL receipt + passing gates -> no seal (both via tick and via try_seal(force=True)).
5. Fingerprint per attempt (pp M1, :256): append only when the receipt sha changed. Gate: HEAD moves twice, same receipt -> 1 fp.
6. Infra is not FALSE_DONE (pp M2, :146/:231): a gate that cannot start gives no verdict (no refusal, no seal) and alerts.
7. Human gate purity (recorded faults): a receipt `BLOCKED_HUMAN` (or any human-gate status) is classed `human_gate`, never
   re-armed as WORKER_STOPPED; and a unit in human_gate / residual_exhausted is re-judged every tick from its receipt and
   seal, so a resolved gate advances without a coordinator edit. Gate: BLOCKED_HUMAN -> human_gate, 0 arms; receipt later
   DONE -> advance.
8. One owner rule (woz F4): try_seal finds its chain through discover_chains. 9. wait_finalizer into SILENT (pp LOW-1);
   rewrite a refusal whose sha is stale (pp LOW-3); decide uses _done_ids/_by_packet (woz F7). Skip F5/F6/F8 if budget is
   short and say so in the receipt.
9b. APR-6 findings (`REPORT.md` UNPROVEN 3-4, `PRODUCTION-REALITY.md`, KNOWLEDGE A8): A8 -- the mission layer said "no
   receipt" for the closed C2 receipt and a duplicate worker (m-7a5265092233) ran: on the residual path the mission must
   locate the receipt through the chain unit and judge it with receipt_judge; RED then green. Then explain from code why
   C2/C3 have no seal.json and C2 no refusal.json after the canary (expected or defect); fix if a defect.
10. Suites green from wt_apr (receipt_judge, halt_continues, mission_steward, gsdx_chain, apr_seal, apr_event, gsd_mission,
    gsd_epoch, gsd_sweep_pass); cherry-pick the commits into the live checkout (feature/knowledge-acquisition) by pathspec,
    re-run the suites there, and dry-run every live chain before/after (no action change except the fixed classes).
Receipt (line 2 `Status: DONE`): each item FIXED/SKIPPED with commit + gate id; live install hashes; suite counts.

## Residual
Written by the coordinator (not the steward) for mission m-a7d355320929, which NEVER LAUNCHED: the coordinator amended
WU-APR7.md (3e3df8ab, 20:29) two minutes after the chain admitted it (20:27), every sweep pass refused the launch with
"the packet changed since it was admitted: admit it again", and the mission halted at 24 h with 0 spend and no session,
so the steward had nothing to settle and the chain sat at wait_steward. Nothing was done; start from item 1.
Add to item 7 (human-gate purity / silent stalls): a launch refused for the same reason on N consecutive passes must
alert (and the chain must not read a never-launched mission as WORKER_STOPPED waiting on a steward that cannot act).
