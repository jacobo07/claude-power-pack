STATUS: DONE
COMMITS: 7537be39 (receipt+code in one commit)
Packet sha256 74ea88f6222f verified. Unit: A5-U5 visual residual compiler.
Files: tools/visual_residual.py, tools/test_a5_u5.py
Gate: `python3 tools/test_a5_u5.py` -> A5_U5_PASS=13/13, runtime ~0.2 s.
Reference: /home/kobii/.claude/skills/image-calco/scripts/gate_boxes.py and detect_scale.py present, read-only; only the idea
  (numeric tolerance, self-test that the gate can fail) was extended; no code edited or imported. Standalone copy.
Libs: Pillow 12.2.0 + numpy 2.4.4 importable by python3 (no pure-zlib fallback built).
Semantics: region PASS iff max channel diff <= tol; FROZEN_OK/FROZEN_REGRESSED only when the stored reference-region hash
  matches; a changed reference re-evaluates the region. Gate exit 0 = all regions PASS or FROZEN_OK. Size mismatch -> exit 2, refused.
Tests: identical PASS; changed region -> only r1c1 FAIL and mask lit only there; size mismatch refused + same-size control;
  tol boundary (noise 3: tol3 PASS, tol2 FAIL); FROZEN_OK and FROZEN_REGRESSED; mutant (tol ignored) -> red detected.
Residual packet (fixture 400x300, 3x4 grid, one failing region; source: test run):
  packet JSON 238 B (+ 2 crop PNGs 621 B) = 859 B vs full candidate+reference PNGs 2286 B.
Deviations: FROZEN_REGRESSED regions are also included in the residual packet (they are failures); the fixture is tiny, so the
  ratio is indicative only. No real-screenshot or DWS measurement made (UNKNOWN).
HANDOFF NOTE: U5 tool and tests green; the residual packet is a pure function of the compare result, so later units can feed it to a model.
