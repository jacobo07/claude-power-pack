# Skill / Capability Program -- pre-final check on gex44 (D-03)

host: gex44 (hostname kobicraft-gex44)
commit: d9e17fb8fb7e5d2312b04e6a731176ab33c58e37
date: 2026-10-04T00:36:23Z
command: python3 tools/test_skill_capability_prefinal.py --write-evidence

PF_MODE=gex44
PF_HEAD=d9e17fb8fb7e5d2312b04e6a731176ab33c58e37
  ok   V-PF-COMMITTED (whole working tree clean except the hook-written stubs)
  ok   V-PF-L8 (check_ledger(final, gates not re-run) == ['L3 N: no terminal disposition'])
  ok   V-PF-UKDL (vault/programs/skill-capability/reviews/ukdl.md entries, fields and sources hold)
  ok   V-PF-CBR (14 rows A..N match the ledger, evidence exists)
  ok   V-PF-DELTAS (product 14, intelligence 15, A..M named)
  ok   V-PF-CLOSEOUT-BUNDLE (19 owner-bundle lines numbered in order)
  ok   V-PF-CLOSEOUT-DECISIONS (every STATE decision line has a ### Q section with Options: and Recorded pick:)
  ok   V-PF-CLOSEOUT-COMMANDS (--final, CLOSE.md, state.N, run branch and the --closeout gate argv present)
  ok   V-PF-LEDGER-INVARIANT (all keys but state/reviews/deltas and state.N equal the FROZEN_AT ledger)
  ok   V-PF-UKDL-UNTOUCHED (no commit since the freeze touches vault/knowledge_base/ukdl-universal.md)
  ok   V-PF-NO-FINAL (run_wrapper(['--final']) raised ValueError; no process started)
  ok   V-PF-SELFTEST (SCP_SELFTEST=PASS rc 0, 0.4s)
  ok   V-PF-STATUS (open ['N'], closed A..M, violations [])
  ok   V-PF-PILLARS (--pillar A..M each rc 0 CEP_PILLAR_<P>=PASS, 19.9s)
  ok   V-PF-N-OPEN (--pillar N rc 1, CEP_PILLAR_N=FAIL on exactly 'L3 N: no terminal disposition')
  ok   V-PF-DIRTY-SET-STABLE (dirty set unchanged while the wrapper ran)
PF_TERMINAL=A,B,C,D,E,F,G,H,I,J,K,L,M
PF_OPEN=N (expected: state.N and --final are laptop-only)
PF_PASS=16/16
PF_FAILED=-
PF_VERDICT=PASS
