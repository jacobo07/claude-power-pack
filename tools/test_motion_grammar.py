#!/usr/bin/env python3
"""Done-gate for motion grammar (V-MGRAM-*): reference -> pattern -> decision -> render.

What this suite has to prove, and why each lane exists:

  CORPUS      the motion patterns are discovered, well-formed, carry "Cuando NO
              usar", and no single-reference entry claims more evidence than one
              reference can give (a local success must not read as a standard).
  DECISION    the resolver answers four DIFFERENT states -- unassessed, abstain,
              unknown_surface, applicable -- and discriminates between patterns
              under the same surface (a restrained dashboard gets continuity, not
              a carousel). An axis that can only ever say "animate" is a
              preference with a schema (CDIO-07 sec.1).
  BOUNDARY    the real hook, driven as the harness drives it (node -> python ->
              JSON), injects the guidance for a relevant surface and injects
              "abstain" -- never a pattern -- for an irrelevant one.
  MUTATION    each semantic check is re-run against a broken resolver and must go
              RED. A check that stays green on the mutant was never checking.
  PRODUCTION  the example page built from that guidance, in real Chromium:
              state order and dwell, causal build order, shell stability,
              opacity/transform-only animation, reduced-motion equivalence,
              keyboard control, pause, responsive width, zero console errors.

Run:  python tools/test_motion_grammar.py            (all lanes)
      python tools/test_motion_grammar.py --no-browser   (lanes A-G; exit 2 = incomplete)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.cdio import motion_patterns as mp  # noqa: E402
from tools import design_gate as dg  # noqa: E402

EXAMPLE_DIR = os.path.join(ROOT, "examples", "motion-grammar", "device-demo")
EXAMPLE_DESIGN = os.path.join(EXAMPLE_DIR, "DESIGN.md")
EXAMPLE_PAGE = os.path.join(EXAMPLE_DIR, "onboarding.html")
HOOK = os.path.join(ROOT, "hooks", "cdio_visual_advisory.js")
REF_OBS = os.path.join(mp.CORPUS_DIR, "evidence", "REF-MOTION-001", "OBSERVATION.md")

HI = {"expressiveness": "moderate", "motion_budget": "medium", "reduced_motion": "equivalent"}
LO = {"expressiveness": "restrained", "motion_budget": "low", "reduced_motion": "equivalent"}
NONE = {"expressiveness": "none", "motion_budget": "none", "reduced_motion": "equivalent"}
NO_RM = {"expressiveness": "moderate", "motion_budget": "medium", "reduced_motion": "absent"}

PASSES = 0
FAILS = 0


def _ok(gate, evidence):
    global PASSES
    PASSES += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate, diagnostic):
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def check(gate, cond, evidence, diagnostic):
    (_ok if cond else _fail)(gate, evidence if cond else diagnostic)


def ids(r):
    return sorted(p["id"] for p in r["patterns"])


# ---------------------------------------------------------------- semantic predicates
# Each takes a resolve function, so the mutation lane can run the SAME predicate
# against a broken resolver and require it to fail.

def pred_positive(resolve):
    r = resolve(HI, "app/onboarding/page.tsx")
    return r["state"] == "applicable" and {"VP-016", "VP-017"} <= set(ids(r))


def pred_discriminates(resolve):
    r = resolve(LO, "app/dashboard/orders/detail.tsx")
    return r["state"] == "applicable" and ids(r) == ["VP-018"]


def pred_contract_discriminates(resolve):
    # SAME surface, different contracts, different answers. `pred_discriminates`
    # alone could not show this: on a dashboard every pattern but VP-018 is excluded
    # by the SURFACE, so it stayed green on a resolver that ignores the contract
    # entirely (caught by the ignores-floors mutant, 2026-09-30).
    lo = resolve(LO, "app/onboarding/page.tsx")
    hi = resolve(HI, "app/onboarding/page.tsx")
    return ids(lo) == ["VP-018"] and {"VP-016", "VP-017", "VP-018"} <= set(ids(hi))


def pred_abstain(resolve):
    r = resolve(NONE, "admin/orders/table.tsx")
    return r["state"] == "abstain" and not r["patterns"]


def pred_exclusion(resolve):
    r = resolve(HI, "app/onboarding/payment/page.tsx")
    return "VP-016" not in ids(r) and "VP-017" not in ids(r)


def pred_reduced_motion_floor(resolve):
    r = resolve(NO_RM, "app/onboarding/page.tsx")
    return not r["patterns"]


def pred_unassessed(resolve):
    r = resolve(None, "app/onboarding/page.tsx")
    return r["state"] == "unassessed" and not r["patterns"]


PREDICATES = {
    "positive": pred_positive,
    "discriminates": pred_discriminates,
    "contract-discriminates": pred_contract_discriminates,
    "abstain": pred_abstain,
    "exclusion": pred_exclusion,
    "reduced-motion-floor": pred_reduced_motion_floor,
    "unassessed": pred_unassessed,
}


def mutant_everything_applies(experience, surface, corpus_dir=mp.CORPUS_DIR):
    """Resolver that ignores the contract and the surface: serves the whole corpus."""
    entries, errs = mp.load_corpus(corpus_dir)
    pats = [{"id": e["id"], "name": e["name"], "file": e["file"],
             "evidence_level": e["evidence_level"], "purpose": e["purpose"],
             "provenance": e["provenance"]} for e in entries]
    return {"state": "applicable", "patterns": pats, "withheld": [], "surface": surface,
            "surface_kinds": mp.surface_kinds(surface), "corpus_errors": errs,
            "reason": "mutant"}


def mutant_ignores_floors(experience, surface, corpus_dir=mp.CORPUS_DIR):
    """Resolver that keeps surface logic but drops the contract ceilings and floors."""
    wide = dict(experience or {}, expressiveness="high", motion_budget="high",
                reduced_motion="equivalent") if experience else None
    return mp.resolve(wide, surface, corpus_dir)


# ---------------------------------------------------------------- lanes A-G

def lane_corpus():
    print("\n[A] corpus")
    entries, errors = mp.load_corpus()
    got = {e["id"]: e for e in entries}
    check("V-MGRAM-CORPUS-CLEAN", not errors, f"{len(entries)} motion entries, 0 errors",
          f"corpus errors: {errors}")
    need = {"VP-009", "VP-010", "VP-011", "VP-016", "VP-017", "VP-018"}
    check("V-MGRAM-CORPUS-DISCOVERED", need <= set(got), f"discovered {sorted(got)}",
          f"missing {sorted(need - set(got))}")
    ref = [e for e in entries if e["provenance"] == "REF-MOTION-001"]
    over = [e["id"] for e in ref
            if mp.EVIDENCE_LEVELS.index(e["evidence_level"]) > mp.EVIDENCE_LEVELS.index("local")]
    check("V-MGRAM-NO-SINGLE-REF-PROMOTION", len(ref) >= 3 and not over,
          f"{len(ref)} REF-MOTION-001 entries, none above 'local'",
          f"single-reference entries claiming more than 'local': {over} (n={len(ref)})")
    check("V-MGRAM-PROVENANCE-RESOLVES", os.path.isfile(REF_OBS),
          "REF-MOTION-001 observation record exists", f"missing {REF_OBS}")

    # A malformed entry must be REPORTED and NOT served.
    tmp = tempfile.mkdtemp(prefix="mgram_corpus_")
    try:
        src = os.path.join(mp.CORPUS_DIR, "device-demo-state-carousel.md")
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
        broken = text.replace("  min_motion_budget: medium\n", "  min_motion_budget: lots\n")
        no_limits = re.sub(r"## Cuando NO usar.*?(?=^## )", "", text, flags=re.S | re.M)
        for name, body in (("broken.md", broken), ("nolimits.md", no_limits)):
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        r = mp.resolve(HI, "app/onboarding/page.tsx", corpus_dir=tmp)
        errs = " | ".join(r["corpus_errors"])
        check("V-MGRAM-MALFORMED-REPORTED",
              not r["patterns"] and "min_motion_budget" in errs and "HR-VP-01" in errs,
              "bad enum and missing 'Cuando NO usar' both reported, neither served",
              f"patterns={ids(r)} errors={r['corpus_errors']}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def lane_decision():
    print("\n[B] decision semantics")
    for name, pred in PREDICATES.items():
        check(f"V-MGRAM-DECIDE-{name.upper()}", pred(mp.resolve), "holds on the real resolver",
              "does not hold on the real resolver")
    r = mp.resolve(HI, "src/App.tsx")
    check("V-MGRAM-DECIDE-UNKNOWN-SURFACE", r["state"] == "unknown_surface" and not r["patterns"],
          "unnamed surface withheld, not guessed", f"state={r['state']} patterns={ids(r)}")
    r = mp.resolve(LO, "app/dashboard/orders/detail.tsx")
    w = {x["id"]: x["reason"] for x in r["withheld"]}
    check("V-MGRAM-EXPLAINS-WITHHOLDING", "VP-016" in w and "dashboard" in w["VP-016"],
          f"VP-016 withheld with reason: {w.get('VP-016')}", f"withheld={w}")
    check("V-MGRAM-ADVISORY-PROPORTIONAL",
          mp.advisory_line(mp.resolve(None, "landing.html")) == ""
          and mp.advisory_line(mp.resolve(HI, "src/App.tsx")) == ""
          and "abstain" in mp.advisory_line(mp.resolve(NONE, "admin/table.tsx")),
          "nothing injected for unassessed/unknown; abstain is stated",
          "advisory injects on a state that should be silent, or omits abstain")


def lane_rank_drift():
    print("\n[C] vocabulary drift")
    check("V-MGRAM-RANK-DRIFT",
          mp.EXPRESSIVENESS_RANK == dg.EXPRESSIVENESS_RANK and mp.MOTION_RANK == dg.MOTION_RANK,
          "resolver ranks equal design_gate ranks", "resolver and gate vocabularies diverged")


def lane_gate():
    print("\n[D] gate integration")
    plain = dg.design_gate(EXAMPLE_DESIGN)
    withs = dg.design_gate(EXAMPLE_DESIGN, surface=EXAMPLE_PAGE)
    check("V-MGRAM-GATE-ADDITIVE", "motion_guidance" not in plain,
          "no --surface => output shape unchanged for existing callers",
          "motion_guidance appeared without a surface")
    check("V-MGRAM-GATE-NO-RESCORE",
          plain["score"] == withs["score"] and plain["verdict"] == withs["verdict"],
          f"score {plain['score']} / {plain['verdict']} identical with and without surface",
          f"{plain['score']}/{plain['verdict']} vs {withs['score']}/{withs['verdict']}")
    mg = withs.get("motion_guidance") or {}
    check("V-MGRAM-GATE-GUIDANCE", mg.get("state") == "applicable" and "VP-016" in mg.get("advisory", ""),
          f"gate returns {ids(mg)} with advisory", f"guidance={mg}")

    # Only the project's own path may vote on the surface kind. A project living
    # under folders named `docs` and `demo` must not inherit those kinds (review
    # finding 2026-09-30: on Linux every path under /home/ classified as landing).
    base = tempfile.mkdtemp(prefix="mgram_rel_")
    try:
        proj = os.path.join(base, "docs", "demo", "proj")
        os.makedirs(os.path.join(proj, ".git"))
        shutil.copy(EXAMPLE_DESIGN, os.path.join(proj, "DESIGN.md"))
        plain_app = dg.design_gate(os.path.join(proj, "DESIGN.md"),
                                   surface=os.path.join(proj, "src", "App.tsx"))["motion_guidance"]
        onb = dg.design_gate(os.path.join(proj, "DESIGN.md"),
                             surface=os.path.join(proj, "src", "onboarding", "page.html"))["motion_guidance"]
        check("V-MGRAM-SURFACE-PROJECT-RELATIVE",
              plain_app["state"] == "unknown_surface" and onb["surface_kinds"] == ["onboarding"],
              "ancestor folders docs/demo do not vote; src/App.tsx is unknown, onboarding is onboarding",
              f"App.tsx -> {plain_app['state']} {plain_app['surface_kinds']}; "
              f"onboarding -> {onb['surface_kinds']}")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _run_hook(surface, env=None, session=None):
    node = shutil.which("node")
    if not node:
        return None
    payload = {"tool_name": "Write", "session_id": session or "mgram-" + uuid.uuid4().hex,
               "tool_input": {"file_path": surface, "content": "x"}}
    res = subprocess.run([node, HOOK], input=json.dumps(payload), capture_output=True,
                         text=True, encoding="utf-8", timeout=30,
                         env=dict(os.environ, **(env or {})))
    try:
        return json.loads(res.stdout or "{}")
    except json.JSONDecodeError:
        return {"_raw": res.stdout, "_err": res.stderr}


def _hook_context(surface, env=None):
    """additionalContext from the real hook. A 'NOT evaluated' answer means the gate
    did not finish (host load) -- a transport unknown, so it is re-measured ONCE. A
    second unknown is returned as-is and fails its check labelled INCONCLUSIVE; it is
    never read as a pass or as an absence of motion guidance."""
    for attempt in (1, 2):
        out = _run_hook(surface, env) or {}
        ctx = (out.get("hookSpecificOutput") or {}).get("additionalContext", "")
        if "NOT evaluated" not in ctx:
            return ctx
        print(f"         attempt {attempt}: gate unevaluated on this host ({ctx[42:120]}...)")
    return "INCONCLUSIVE " + ctx


def _fixture_project(experience_yaml, surface_rel):
    root = tempfile.mkdtemp(prefix="mgram_proj_")
    os.makedirs(os.path.join(root, ".git"))          # project boundary for the walk
    with open(EXAMPLE_DESIGN, encoding="utf-8") as fh:
        design = fh.read()
    design = re.sub(r"^experience:\n(?:[ \t]+.*\n)+", experience_yaml, design, flags=re.M)
    with open(os.path.join(root, "DESIGN.md"), "w", encoding="utf-8") as fh:
        fh.write(design)
    surface = os.path.join(root, *surface_rel.split("/"))
    os.makedirs(os.path.dirname(surface), exist_ok=True)
    return root, surface


def lane_hook():
    print("\n[E] real hook boundary (node -> python -> JSON)")
    if not shutil.which("node"):
        _fail("V-MGRAM-HOOK-REACHABLE", "node not on PATH; the boundary was not exercised")
        return set()
    # Every check here requires the gate to have RUN ("ran" below). An unevaluated
    # gate produces a non-empty, pattern-free context, which would otherwise satisfy
    # the negative and unassessed checks by accident.
    ran = lambda c: bool(c) and not c.startswith("INCONCLUSIVE") and "NOT evaluated" not in c
    ctx = _hook_context(EXAMPLE_PAGE)
    served = set(re.findall(r"\b(VP-\d{3})\b", ctx)) if ran(ctx) else set()
    check("V-MGRAM-HOOK-POSITIVE", ran(ctx) and {"VP-016", "VP-017"} <= served and "CDIO motion" in ctx,
          f"relevant surface gets {sorted(served)} without naming any subsystem",
          f"context={ctx[:300]!r}")

    none_yaml = ("experience:\n  expressiveness: none\n  motion_budget: none\n"
                 "  reduced_motion: equivalent\n")
    root, surface = _fixture_project(none_yaml, "src/admin/orders/table.html")
    try:
        c = _hook_context(surface)
        check("V-MGRAM-HOOK-NEGATIVE", ran(c) and "abstain" in c and not re.search(r"VP-\d{3}", c),
              "expressiveness:none admin table -> 'abstain', zero patterns injected",
              f"context={c[:300]!r}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # A gate that cannot run must SAY so. `node` is a real interpreter that cannot run
    # design_gate.py, so this drives the failure branch with no mock.
    out = _run_hook(EXAMPLE_PAGE, env={"PP_PYTHON": shutil.which("node")})
    c = (out.get("hookSpecificOutput") or {}).get("additionalContext", "")
    check("V-MGRAM-HOOK-UNEVALUATED-VISIBLE",
          "NOT evaluated" in c and "permissionDecision" not in json.dumps(out),
          "a gate that could not run is reported as unchecked, and never denies",
          f"hook output={json.dumps(out)[:300]}")

    # Throttle isolation. Two projects whose paths share their first 32+ characters,
    # SAME session: each must get its own advisory. The old key truncated the path to
    # a 32-char prefix, so the second project was silenced for 15 minutes. Driven with
    # the no-system tier, which never spawns python, so host load cannot blur it.
    a = tempfile.mkdtemp(prefix="mgram_throttle_isolation_a_")
    b = tempfile.mkdtemp(prefix="mgram_throttle_isolation_b_")
    try:
        sess = "mgram-throttle-" + uuid.uuid4().hex
        got = []
        for proj in (a, b):
            os.makedirs(os.path.join(proj, ".git"))
            out = _run_hook(os.path.join(proj, "landing.html"), session=sess) or {}
            got.append(bool((out.get("hookSpecificOutput") or {}).get("additionalContext")))
        check("V-MGRAM-HOOK-THROTTLE-PER-PROJECT", got == [True, True],
              "same session, two projects with a shared path prefix: both advised",
              f"advised={got} -- the second project was throttled by the first")
    finally:
        shutil.rmtree(a, ignore_errors=True)
        shutil.rmtree(b, ignore_errors=True)

    root, surface = _fixture_project("", "src/onboarding/index.html")
    try:
        c = _hook_context(surface)
        check("V-MGRAM-HOOK-UNASSESSED-SILENT", ran(c) and "CDIO design gate" in c
              and "CDIO motion" not in c,
              "no contract -> design advisory only, no motion proposed",
              f"context={c[:300]!r}")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return served


def lane_provenance(served):
    print("\n[F] page provenance")
    with open(EXAMPLE_PAGE, encoding="utf-8") as fh:
        used = set(re.findall(r'data-pattern="(VP-\d{3})"', fh.read()))
    check("V-MGRAM-PAGE-USES-ONLY-SERVED", used and used <= served,
          f"page implements {sorted(used)}, all returned by the hook for this surface",
          f"page uses {sorted(used)}, hook served {sorted(served)}")


def lane_mutation():
    print("\n[G] mutation drills (each must go RED on a broken resolver)")
    for mname, mutant, must_break in (
            ("everything-applies", mutant_everything_applies,
             ["discriminates", "contract-discriminates", "abstain", "exclusion",
              "reduced-motion-floor", "unassessed"]),
            ("ignores-floors", mutant_ignores_floors,
             ["contract-discriminates", "reduced-motion-floor"])):
        survived = [n for n in must_break if PREDICATES[n](mutant)]
        check(f"V-MGRAM-MUTANT-{mname.upper()}", not survived,
              f"killed by {must_break}", f"predicates stayed green on the mutant: {survived}")


# ---------------------------------------------------------------- lane H: production

INIT = r"""
window.__mg = {builds: [], vt: 0, frames: [], props: new Set(), longtasks: 0};
const _svt = document.startViewTransition && document.startViewTransition.bind(document);
if (_svt) document.startViewTransition = (cb) => { window.__mg.vt++; return _svt(cb); };
new MutationObserver((ms) => { for (const m of ms) {
  const t = m.target;
  if (t.classList && t.classList.contains('build-line') && t.classList.contains('is-in'))
    window.__mg.builds.push({i: Array.from(t.parentNode.querySelectorAll('.build-line')).indexOf(t),
                              t: performance.now()});
}}).observe(document, {subtree: true, attributes: true, attributeFilter: ['class']});
let _last = 0;
const tick = (ts) => { if (_last) window.__mg.frames.push(ts - _last); _last = ts;
  for (const a of document.getAnimations()) {
    if (a.transitionProperty) window.__mg.props.add(a.transitionProperty);
    else if (a.effect && a.effect.getKeyframes) {
      // View-transition snapshots are pseudo-elements; their width/height animate a
      // composited image, never page layout. Tag them apart so a REAL element
      // animating height cannot hide behind the snapshot's allowance.
      const pe = a.effect.pseudoElement || '';
      const tag = pe.startsWith('::view-transition') ? 'vt:' : 'kf:';
      for (const k of a.effect.getKeyframes())
        for (const p of Object.keys(k)) if (!['offset','easing','composite','computedOffset'].includes(p))
          window.__mg.props.add(tag + p);
    }
  }
  requestAnimationFrame(tick); };
requestAnimationFrame(tick);
window.__mg.longtasks = [];
try { new PerformanceObserver((l) => { for (const e of l.getEntries())
  window.__mg.longtasks.push([e.startTime, e.duration]); })
  .observe({type: 'longtask', buffered: true}); } catch (e) { window.__mg.longtasks = null; }
"""


def lane_production(evidence_dir):
    print("\n[H] Production Reality (real Chromium, real page)")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        _fail("V-MGRAM-PR-BROWSER", f"playwright unavailable ({exc}); production lane not run")
        return
    url = "file:///" + EXAMPLE_PAGE.replace("\\", "/")
    os.makedirs(evidence_dir, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # --- H1 normal motion, desktop ------------------------------------------------
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.add_init_script(INIT)
        page.goto(url)
        page.wait_for_load_state("load")
        page.mouse.move(5, 5)
        copy_shots, device_boxes, seen = [], [], []
        t_end = time.time() + 13.0
        while time.time() < t_end:
            st = page.get_attribute("#device", "data-active-state")
            if not seen or seen[-1] != st:
                seen.append(st)
                page.wait_for_timeout(400)
                copy_shots.append(page.locator(".copy").screenshot())
                device_boxes.append(page.locator("#device").bounding_box())
                page.locator(".demo").screenshot(path=os.path.join(evidence_dir, f"state_{len(seen)}_{st}.png"))
            page.wait_for_timeout(60)
        marks = page.evaluate("performance.getEntriesByType('mark')"
                              ".filter(m => m.name.startsWith('state:'))"
                              ".map(m => [m.name.slice(6), m.startTime])")
        mg = page.evaluate("({builds: __mg.builds, vt: __mg.vt, frames: __mg.frames,"
                           " props: Array.from(__mg.props), longtasks: __mg.longtasks})")

        order = [m[0] for m in marks]
        check("V-MGRAM-PR-ORDER", order[:5] == ["capture", "summary", "board", "detail", "capture"],
              f"states advanced in narrative order and wrapped: {order}", f"order={order}")
        holds = {"capture": 2400, "summary": 1800 + 4 * 420, "board": 2400, "detail": 2600}
        dev = []
        for (a, ta), (_, tb) in zip(marks, marks[1:]):
            dev.append((a, round(tb - ta), holds[a]))
        # 180 ms: above the measured timer jitter on this host (<=160 on a cold first
        # state), below the 200 ms error of arming the dwell with the previous
        # state's hold (review finding: 250 let that defect pass).
        bad = [d for d in dev if abs(d[1] - d[2]) > 180]
        check("V-MGRAM-PR-DWELL", dev and not bad,
              f"measured dwell vs declared (ms): {dev}", f"out of tolerance: {bad}")

        by_cycle = [b for b in mg["builds"]]
        first4 = [b["i"] for b in by_cycle[:4]]
        gaps = [round(b["t"] - a["t"]) for a, b in zip(by_cycle[:4], by_cycle[1:4])]
        check("V-MGRAM-PR-BUILD-CAUSAL", first4 == [0, 1, 2, 3] and all(350 <= g <= 520 for g in gaps),
              f"summary built in causal order {first4}, gaps {gaps} ms (token 420)",
              f"order={first4} gaps={gaps}")
        check("V-MGRAM-PR-SHARED-ELEMENT", mg["vt"] >= 1,
              f"board->note used a view transition ({mg['vt']} call(s))", "no view transition ran")
        stable = len(set(copy_shots)) == 1 and len({json.dumps(b) for b in device_boxes}) == 1
        check("V-MGRAM-PR-SHELL-STABLE", stable and len(copy_shots) >= 4,
              f"copy/CTA pixels identical across {len(copy_shots)} states; device box fixed",
              f"distinct copy renders={len(set(copy_shots))}, device boxes="
              f"{len({json.dumps(b) for b in device_boxes})}")
        # Real elements: opacity/transform only. `vt:` = a ::view-transition-*
        # snapshot pseudo-element, which may animate any property because it is a
        # composited image that never lays out the page.
        allowed = {"opacity", "transform", "kf:opacity", "kf:transform"}
        props = set(mg["props"])
        real = {p for p in props if not p.startswith("vt:")}
        check("V-MGRAM-PR-COMPOSITED-ONLY", real and real <= allowed,
              f"element properties {sorted(real)}; snapshot properties "
              f"{sorted(props - real)}", f"non-composited element properties: {sorted(real - allowed)}")
        # APERTURE: the claim is "the motion causes no long tasks", so only tasks
        # starting after loadEventEnd are the motion's. Attribution measured
        # 2026-09-30: every long task in 4 runs started before loadEventEnd (parse
        # and first paint), with or without screenshots; none fell in a cycle.
        # Load-time tasks are reported, not hidden. `None` = observer unsupported,
        # which is UNMEASURED and fails rather than reading as zero.
        load_end = page.evaluate("performance.getEntriesByType('navigation')[0].loadEventEnd")
        lts = mg["longtasks"]
        during = None if lts is None else [t for t in lts if t[0] > load_end]
        frames = sorted(mg["frames"][5:])
        if frames:
            p95 = frames[int(len(frames) * 0.95) - 1]
            print(f"         measured: {len(frames)} frames, median {statistics.median(frames):.1f} ms, "
                  f"p95 {p95:.1f} ms; long tasks at load {len(lts or []) - len(during or [])}, "
                  f"during motion {during}")
        check("V-MGRAM-PR-NO-LONG-TASKS", during == [],
              "zero long tasks (>50 ms) after load across a full cycle",
              f"long tasks during motion={during} (None = unmeasured)")

        # keyboard + pause + focus + visibility
        page.locator("#pause").focus()
        check("V-MGRAM-PR-FOCUS-PAUSES", page.get_attribute("#device", "data-playing") == "false",
              "focus inside the demo pauses autoplay", "autoplay kept running under focus")
        page.keyboard.press("Space")
        pressed = page.get_attribute("#pause", "aria-pressed")
        page.locator("#t-capture").click()
        page.keyboard.press("ArrowRight")
        a1 = page.get_attribute("#device", "data-active-state")
        f1 = page.evaluate("document.activeElement.id")
        page.keyboard.press("End")
        a2 = page.get_attribute("#device", "data-active-state")
        inert_ok = page.evaluate("Array.from(document.querySelectorAll('.state'))"
                                 ".every(s => s.classList.contains('is-active') || s.inert)")
        check("V-MGRAM-PR-KEYBOARD", pressed == "true" and a1 == "summary" and f1 == "t-summary"
              and a2 == "detail" and inert_ok,
              "Space pauses; Arrow/End move state and focus; hidden states inert",
              f"pressed={pressed} arrow={a1}/{f1} end={a2} inert={inert_ok}")
        page.locator(".cta").click()
        page.wait_for_timeout(200)
        hash_ok = page.evaluate("location.hash") == "#what-you-get"
        check("V-MGRAM-PR-CTA-LIVE", hash_ok, "CTA navigates to its section", "CTA is dead")
        page.locator("#pause").click()            # resume, then leave focus so only visibility gates
        page.evaluate("document.activeElement.blur()")
        page.evaluate("Object.defineProperty(document, 'hidden', {value: true, configurable: true});"
                      "document.dispatchEvent(new Event('visibilitychange'))")
        check("V-MGRAM-PR-HIDDEN-PAUSES", page.get_attribute("#device", "data-playing") == "false",
              "hidden tab stops autoplay (simulated visibilitychange)", "autoplay continued while hidden")
        check("V-MGRAM-PR-NO-CONSOLE-ERRORS", not errors, "zero console/page errors", f"errors={errors}")
        ctx.close()

        # --- H2 reduced motion ------------------------------------------------------
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
        page = ctx.new_page()
        page.add_init_script(INIT)
        page.goto(url)
        page.wait_for_timeout(3500)
        still = page.get_attribute("#device", "data-active-state")
        label = page.text_content("#pause")
        reached = []
        for tab in ("#t-summary", "#t-board", "#t-detail", "#t-capture"):
            page.locator(tab).click()
            page.wait_for_timeout(60)
            reached.append(page.get_attribute("#device", "data-active-state"))
            if tab == "#t-summary":
                built = page.evaluate("Array.from(document.querySelectorAll('#s-summary .build-line'))"
                                      ".every(l => l.classList.contains('is-in'))")
        anims = page.evaluate("document.getAnimations().length")
        vt = page.evaluate("__mg.vt")
        page.locator("#t-summary").click()
        page.locator(".demo").screenshot(path=os.path.join(evidence_dir, "reduced_summary.png"))
        check("V-MGRAM-PR-REDUCED-NO-AUTOPLAY", still == "capture" and label == "Play demo",
              "reduced motion: no autoplay, control offers Play", f"state={still} label={label!r}")
        check("V-MGRAM-PR-REDUCED-EQUIVALENT",
              reached == ["summary", "board", "detail", "capture"] and built and anims == 0 and vt == 0,
              "every state reachable, summary shown whole, zero running animations, no view transition",
              f"reached={reached} built={built} animations={anims} vt={vt}")
        ctx.close()

        # --- H3 responsive -------------------------------------------------------------
        for w, h in ((390, 844), (1280, 800)):
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            page.goto(url)
            page.wait_for_timeout(300)
            sw = page.evaluate("document.documentElement.scrollWidth")
            box = page.locator("#device").bounding_box()
            ctrl = page.locator(".controls").bounding_box()
            page.screenshot(path=os.path.join(evidence_dir, f"viewport_{w}.png"), full_page=True)
            check(f"V-MGRAM-PR-RESPONSIVE-{w}",
                  sw <= w and box["x"] >= 0 and box["x"] + box["width"] <= w
                  and ctrl["x"] >= 0 and ctrl["x"] + ctrl["width"] <= w,
                  f"no horizontal scroll (scrollWidth {sw}), device and controls inside {w}px",
                  f"scrollWidth={sw} device={box} controls={ctrl}")
            ctx.close()
        browser.close()
    print(f"         evidence: {evidence_dir}")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    no_browser = "--no-browser" in argv
    evidence = os.path.join(ROOT, "_logs", "motion_grammar", time.strftime("%Y%m%d_%H%M%S"))
    print("V-MGRAM motion grammar done-gate")
    lane_corpus()
    lane_decision()
    lane_rank_drift()
    lane_gate()
    served = lane_hook()
    lane_provenance(served)
    lane_mutation()
    if not no_browser:
        lane_production(evidence)
    print(f"\nMGRAM_PASS={PASSES}/{PASSES + FAILS}"
          + ("  production lane NOT RUN (--no-browser): incomplete, not a pass" if no_browser else ""))
    if FAILS:
        return 1
    return 2 if no_browser else 0


if __name__ == "__main__":
    sys.exit(main())
