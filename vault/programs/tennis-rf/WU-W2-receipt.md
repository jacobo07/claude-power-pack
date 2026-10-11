# W2 receipt
Status: DONE

Commits: wt_tennis_rf 3dc1d2f (stage.py certify/certificate_problem/send gate/CLI, runner_lib.py:1472 trim_objdiff_report, test_send_cert.py; pre-certificate drills test_transport/test_reproduce/test_p2a set KSR_SEND_CERT=off).

- PROVEN: certificate lives in preflight.json under 'certificate' (hash over capsule id + manifest sha256, CURRENT value, tool identities/hashes, pins sha, job key, binary identity, unit-list hash, W1 lint per unit, OUT budget). Command: python test_send_cert.py -> SEND_CERT_DRILL 10/10 (missing cert refuses; capsule touched after certify refuses INPUT_CHANGED; units changed refuses; one lint-failing unit refuses whole job naming it; READY send proceeds to preflight with an exploding remote double, no SSH; tamper -> CERT_HASH; own error -> CERT_ERROR fail closed; KSR_SEND_CERT=off kill switch; OUT_BUDGET over 20971520 -> NOT_READY:OUT_BUDGET).
- Refusal: send result NOT_READY, exit 17, text NOT_READY:<check>. Placed after the W1 CAPSULE_NOT_CURRENT guard (W1 drill still expects that code first), before preflight/remote.
- PROVEN (CPX): runner_lib.py:1472 shutil.copyfile -> trim_objdiff_report.
- Replay (copy of candidate-20261001T101650Z in a temp root, no CURRENT_CAPSULE = C2b state): CERTIFY NOT_READY with CURRENT_CAPSULE and PINS; with one unit replaced by raw m2c text also LINT: unit p4-main_805FB3F4 UNRESOLVED_TYPE. NOTE: the original C2b job dir (cap1-ba8a3cfe2822) no longer exists in the factory root; the replay uses the nearest real job plus the C2b condition, the lint line is synthetic.
- NOT_PROVEN: RED-first order was not recorded (gate written after the code); the real-pins live path (PINS check) only exercised as a refusal. Pre-existing failures seen, not caused by W2: test_fanout_preconditions V-VAULT-EOL-PINNED-LF, test_runner_gates V-RUNNER-NO-CR, test_contract missing 06_ksr_match_batch.py, test_return_path P1/P8, test_p2a V-P2A-CAP INVALID_PARAMS (not a baseline-compared claim).
- Next unit: every real send now needs 'python stage.py certify <tag>' after build; KSR_SEND_CERT=off only for drills.
