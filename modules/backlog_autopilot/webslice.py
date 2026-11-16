"""Web vertical slice (ASC-03): one small REAL web surface driven through the whole
capability flow, with twelve mandatory decisions that each carry an observed verdict.

Extends backlog_autopilot; reuses capability_runtime.applicability, cdio.scorer,
cdio.motion_patterns, cdio.legal_surface, ccf.trademark_scanner and tools/design_gate.
Nothing here is a parallel evaluator: every decision delegates to the owner and this module
only supplies the glue and the instruments that prove the glue could have said no.

Flow: intent -> product type -> existing identity (DESIGN.md) -> applicability selection ->
licence + dependency check -> build -> real Chromium render -> in-page interaction check ->
CDIO scorer verdict -> Production Reality check.

Honesty rules pinned here (and driven from both poles in tools/test_asc_webslice.py):
  * BACKLOG_ONLY / SOURCE_FOUND / IMPLEMENTED are never announced AVAILABLE; only an ACTIVATED
    ledger row that carries exit-0 execution evidence is.
  * An UNKNOWN licence is refused, never waved through.
  * A command that exits 0 without its artifact is a lie, not a success.
  * A structural test that is green over a behaviour that does not work is reported as such.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.capability_runtime.applicability import MissionContext, Verdict, evaluate  # noqa: E402
from modules.capability_runtime.contract import CapabilityContract  # noqa: E402

LEDGER = "vault/programs/ascension/phase2/reconciliation_ledger.json"
EVIDENCE = "vault/programs/ascension/phase2/execution_evidence.json"
SLICE_DIR = "vault/programs/ascension/phase3"

# ----------------------------------------------------------------------------------------
# Browser instrument
# ----------------------------------------------------------------------------------------

def chrome_path() -> str | None:
    env = os.environ.get("ASC_CHROME")
    if env and os.path.exists(env):
        return env
    hits = sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome")))
    return hits[-1] if hits else None


_ERR_HOOK = ("<script>window.__errs=[];window.addEventListener('error',function(e){"
             "window.__errs.push(String(e.message||e.error))});"
             "window.addEventListener('unhandledrejection',function(e){window.__errs.push(String(e.reason))});"
             "</script>")

# Runs after the page's own scripts. It measures the RENDERED page and then performs the page's
# declared interactions (data-click-target / data-click-expect) the way a user would.
_PROBE = r"""<script>(function(){
function hex(c){var m=c.match(/\d+(\.\d+)?/g);if(!m)return null;
 return '#'+[0,1,2].map(function(i){return ('0'+Math.round(+m[i]).toString(16)).slice(-2)}).join('')}
var res={errors:[],interactions:[],motion_present:false,tap_sizes:[],ctas:0};
var all=document.querySelectorAll('*');
for(var i=0;i<all.length;i++){var cs=getComputedStyle(all[i]);
 if((cs.animationName&&cs.animationName!=='none'&&parseFloat(cs.animationDuration)>0)||
    (parseFloat(cs.transitionDuration)>0)){res.motion_present=true}}
var b=getComputedStyle(document.body);
res.body_font_px=parseFloat(b.fontSize);res.fg=hex(b.color);res.bg=hex(b.backgroundColor);
var ctl=document.querySelectorAll('button,a.btn,[role=button]');
for(var j=0;j<ctl.length;j++){var r=ctl[j].getBoundingClientRect();res.tap_sizes.push(Math.round(Math.min(r.width,r.height)))}
res.ctas=document.querySelectorAll('[data-primary]').length;
res.title=document.title;res.h1=(document.querySelector('h1')||{}).textContent||'';
var act=document.querySelectorAll('[data-click-target]');
for(var k=0;k<act.length;k++){var el=act[k],ok=false,got=null;
 try{el.click();var t=document.querySelector(el.getAttribute('data-click-target'));
  got=t?t.textContent.trim():null;ok=got===el.getAttribute('data-click-expect')}catch(e){got='THROW:'+e}
 res.interactions.push({id:el.id||el.tagName,expect:el.getAttribute('data-click-expect'),got:got,ok:ok})}
res.errors=(window.__errs||[]).slice(0);
var pre=document.createElement('pre');pre.id='__selfcheck';pre.textContent=JSON.stringify(res);
document.body.appendChild(pre)})();</script>"""


def render(html_file: str | Path, *, shot: str | Path | None = None, width: int = 390,
           height: int = 800, reduced_motion: bool = False, timeout: int = 60) -> dict:
    """Render `html_file` in headless Chromium, run the in-page probe, return its JSON.

    `ok` is True only when Chromium exited 0 AND the probe's JSON came back; a browser that
    exits 0 with no probe output is a failed render, not a pass.
    """
    chrome = chrome_path()
    if not chrome:
        return {"ok": False, "reason": "NO_CHROMIUM", "selfcheck": None}
    src = Path(html_file)
    text = src.read_text(encoding="utf-8")
    probed = text.replace("<head>", "<head>" + _ERR_HOOK, 1) if "<head>" in text else _ERR_HOOK + text
    probed = probed.replace("</body>", _PROBE + "</body>", 1) if "</body>" in probed else probed + _PROBE
    probed = probed.replace("<head>", f'<head><base href="file://{src.parent.resolve()}/">', 1)
    flags = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
             f"--window-size={width},{height}", "--virtual-time-budget=2500"]
    if reduced_motion:
        flags.append("--force-prefers-reduced-motion")
    with tempfile.TemporaryDirectory(prefix="aslice-") as td:
        probe_file = Path(td) / "probe.html"
        probe_file.write_text(probed, encoding="utf-8")
        p = subprocess.run(flags + ["--dump-dom", f"file://{probe_file}"], capture_output=True,
                           text=True, timeout=timeout)
        m = re.search(r'<pre id="__selfcheck">(.*?)</pre>', p.stdout, re.S)
        sc = None
        if m:
            try:
                import html as _h
                sc = json.loads(_h.unescape(m.group(1)))
            except ValueError:
                sc = None
        out = {"ok": p.returncode == 0 and sc is not None, "exit": p.returncode, "selfcheck": sc,
               "reduced_motion": reduced_motion}
        if shot is not None:
            s = subprocess.run(flags + [f"--screenshot={shot}", f"file://{probe_file}"],
                               capture_output=True, text=True, timeout=timeout)
            out["shot"] = str(shot)
            out["shot_exit"] = s.returncode
    return out


def png_ok(path: str | Path, min_bytes: int = 1500) -> bool:
    try:
        b = Path(path).read_bytes()
    except OSError:
        return False
    return len(b) >= min_bytes and b[:8] == b"\x89PNG\r\n\x1a\n"


# ----------------------------------------------------------------------------------------
# Case 10: a tool that reports success without its artifact
# ----------------------------------------------------------------------------------------

def run_tool(cmd: list[str], artifact: str | Path, *, valid=None, cwd: str | Path | None = None) -> dict:
    """Run `cmd`; success means the exit code AND the artifact (existing, non-empty, valid)."""
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    art = Path(artifact)
    present = art.exists() and art.stat().st_size > 0
    well_formed = present and (valid(art) if valid else True)
    if p.returncode != 0:
        verdict = "TOOL_FAILED"
    elif not present:
        verdict = "TOOL_LIED_NO_ARTIFACT"
    elif not well_formed:
        verdict = "TOOL_LIED_BAD_ARTIFACT"
    else:
        verdict = "OK"
    return {"cmd": cmd, "exit": p.returncode, "artifact": str(art), "present": present,
            "well_formed": well_formed, "verdict": verdict}


def naive_verify(result: dict) -> str:
    """The instrument under indictment: trusts the exit code. Kept so the gate can show that the
    honest verifier disagrees with it on a seeded lie."""
    return "OK" if result["exit"] == 0 else "TOOL_FAILED"


# ----------------------------------------------------------------------------------------
# Case 11: a green test over broken behaviour
# ----------------------------------------------------------------------------------------

def structural_test(html: str) -> bool:
    """The kind of test that goes green here: a button exists and a handler is mentioned."""
    return bool(re.search(r"<button[^>]+data-click-target", html)) and "addEventListener" in html


def behaviour_verdict(html_file: str | Path) -> dict:
    """Structural test vs the real browser behaviour of every declared interaction."""
    html = Path(html_file).read_text(encoding="utf-8")
    green = structural_test(html)
    r = render(html_file)
    sc = r.get("selfcheck") or {}
    inter = sc.get("interactions") or []
    works = bool(r.get("ok")) and bool(inter) and all(i["ok"] for i in inter) and not sc.get("errors")
    if not r.get("ok"):
        v = "UNMEASURED"
    elif green and not works:
        v = "GREEN_OVER_BROKEN"
    elif works:
        v = "OK"
    else:
        v = "BROKEN_TEST_RED"
    return {"structural_green": green, "behaviour_works": works, "verdict": v,
            "interactions": inter, "errors": sc.get("errors")}


# ----------------------------------------------------------------------------------------
# Cases 3, 4, 12: availability, reachability, discoverability
# ----------------------------------------------------------------------------------------

def announce(row: dict) -> str:
    """What may honestly be said about a ledger row. Law 3: backlog is not implementation,
    implementation is not activation, activation is not execution."""
    st = row.get("state")
    ev = row.get("execution_evidence")
    if st == "ACTIVATED" and ev and ev.get("exit") == 0:
        return "AVAILABLE"
    if st == "ACTIVATED":
        return "ACTIVATED_UNVERIFIED"
    if st == "IMPLEMENTED":
        return "INSTALLED_NOT_ACTIVATED"
    if st == "CLAIM_REJECTED":
        return "CLAIM_REJECTED"
    if st in ("BACKLOG_ONLY", "SOURCE_FOUND"):
        return "NOT_AVAILABLE_BACKLOG"
    return "UNKNOWN"


def naive_announce(row: dict) -> str:
    """Seeded liar: anything with a known state is 'available'."""
    return "UNKNOWN" if row.get("state") in (None, "UNKNOWN") else "AVAILABLE"


def announcement_lies(fn, rows: list[dict]) -> list[str]:
    """Ids for which `fn` says AVAILABLE although the row has no execution evidence."""
    return [r["id"] for r in rows
            if fn(r) == "AVAILABLE"
            and not (r.get("state") == "ACTIVATED" and (r.get("execution_evidence") or {}).get("exit") == 0)]


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


ACTIVATION_SURFACES = ("commands", "agents", "hooks", "modules", "tools", "vault/liveness")


def skill_reachability(root: str | Path) -> dict:
    """Installed skills that nothing outside their own directory can reach.

    A skill is reachable when its name is cited by an activation surface (a command, agent, hook,
    module, tool or the liveness registry) or by the project CLAUDE.md. Presence of SKILL.md is
    INSTALLED, not ACTIVATED."""
    root = Path(root)
    skills = sorted(p.parent.name for p in (root / "skills").glob("*/SKILL.md"))
    corpus: dict[str, str] = {}
    for d in ACTIVATION_SURFACES:
        base = root / d
        for f in base.rglob("*") if base.exists() else []:
            if f.is_file() and f.suffix in (".py", ".js", ".md", ".json", ".cjs", ".sh", ".yml"):
                corpus[str(f.relative_to(root))] = _read(f)
    corpus["CLAUDE.md"] = _read(root / "CLAUDE.md")
    unreachable, reachable = [], []
    for s in skills:
        own = f"skills/{s}/"
        cited = any(s in txt for rel, txt in corpus.items() if not rel.startswith(own))
        (reachable if cited else unreachable).append(s)
    return {"installed": len(skills), "reachable": reachable, "unreachable": unreachable}


ENTRY_DOCS = ("CLAUDE.md", "README.md")


def discoverability(root: str | Path, feature_tokens: list[str]) -> dict:
    """Can a fresh agent that reads only the normal institutional entry docs find the feature?"""
    root = Path(root)
    text = "\n".join(_read(root / d) for d in ENTRY_DOCS)
    missing = [t for t in feature_tokens if t not in text]
    return {"discoverable": not missing, "missing": missing, "read": [d for d in ENTRY_DOCS if (root / d).exists()]}


# ----------------------------------------------------------------------------------------
# Cases 1, 2, 5, 6, 7: selection, licence, dependency, expressiveness
# ----------------------------------------------------------------------------------------

LICENSE_ALLOW = ("MIT", "APACHE-2.0", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "ISC", "0BSD", "CC0-1.0", "INTERNAL")
EXPRESSIVENESS_RANK = {"none": 0, "restrained": 1, "moderate": 2, "high": 3}


@dataclass
class Candidate:
    id: str
    license: str                       # SPDX-ish, or "UNKNOWN"
    runtime: str                       # what it needs: static-html | react | ...
    applies_to: list = field(default_factory=list)
    excluded_from: list = field(default_factory=list)
    deps: list = field(default_factory=list)      # npm packages it imports
    min_expressiveness: str = "none"
    source: str = "catalog"


def license_verdict(c: Candidate) -> dict:
    lic = (c.license or "UNKNOWN").strip().upper()
    if lic == "UNKNOWN" or not lic:
        return {"ok": False, "state": "LICENSE_UNKNOWN", "reason": "licence not established; UNKNOWN is never PASS"}
    if lic in LICENSE_ALLOW:
        return {"ok": True, "state": "LICENSE_OK", "reason": lic}
    return {"ok": False, "state": "LICENSE_REFUSED", "reason": f"{lic} is outside the allow-list {LICENSE_ALLOW}"}


def dependency_verdict(c: Candidate, project: dict) -> dict:
    """Technical compatibility: runtime match and every npm dependency declared by the project."""
    if c.runtime != project.get("runtime"):
        return {"ok": False, "state": "TECH_INCOMPATIBLE",
                "reason": f"needs runtime {c.runtime!r}, project is {project.get('runtime')!r}"}
    missing = [d for d in c.deps if d not in set(project.get("npm", []))]
    if missing:
        return {"ok": False, "state": "TECH_INCOMPATIBLE", "reason": f"undeclared dependencies: {missing}"}
    return {"ok": True, "state": "TECH_OK", "reason": "runtime and dependencies resolve"}


def contract_for(c: Candidate) -> CapabilityContract:
    return CapabilityContract(
        id=c.id, name=c.id, owner="modules/backlog_autopilot/webslice.py",
        triggers=list(c.applies_to), anti_triggers=list(c.excluded_from),
        compatible_runtimes=[c.runtime], consumers=["modules/backlog_autopilot/webslice.py"],
        expected_leverage="high", failure_risk_if_omitted="high", maturity="proven",
        activation_cost="low", context_cost="low", operational_cost="low")


def select(intent: str, c: Candidate, project: dict, experience: dict | None) -> dict:
    """One candidate against one intent. Order: licence, expressiveness ceiling, applicability
    (anti-trigger/relevance), technical compatibility. Each refusal names its own gate."""
    lv = license_verdict(c)
    if not lv["ok"]:
        return {"id": c.id, "decision": "REFUSED", "gate": "license", **lv}
    ceiling = (experience or {}).get("expressiveness")
    if ceiling in EXPRESSIVENESS_RANK and EXPRESSIVENESS_RANK[c.min_expressiveness] > EXPRESSIVENESS_RANK[ceiling]:
        return {"id": c.id, "decision": "REFUSED", "gate": "expressiveness",
                "state": "EXPRESSIVENESS_CEILING",
                "reason": f"needs {c.min_expressiveness}, contract ceiling is {ceiling}"}
    ap = evaluate(contract_for(c), MissionContext(description=intent, runtime=project.get("runtime", "")))
    if ap.verdict == Verdict.NOT_APPLICABLE:
        return {"id": c.id, "decision": "REJECTED", "gate": "applicability", "state": ap.verdict.value,
                "reason": ap.reason}
    dv = dependency_verdict(c, project)
    if not dv["ok"] or ap.blocked:
        return {"id": c.id, "decision": "REFUSED", "gate": "dependency",
                "state": dv["state"] if not dv["ok"] else ap.verdict.value,
                "reason": dv["reason"] if not dv["ok"] else ap.reason}
    return {"id": c.id, "decision": "SELECTED", "gate": "applicability", "state": ap.verdict.value,
            "score": ap.score, "reason": ap.reason}


def catalog_candidates(root: str | Path = ROOT) -> list[Candidate]:
    """Candidates DISCOVERED from the vendored componentry catalog (never hand-listed)."""
    cat = json.loads(Path(root, "vault/knowledge_base/cdio/componentry/catalog.json").read_text(encoding="utf-8"))
    lic = (cat.get("license") or {})
    spdx = lic.get("spdx") if isinstance(lic, dict) else lic
    out = []
    for c in cat["components"]:
        d = c.get("derived", {})
        out.append(Candidate(
            id="componentry:" + c.get("slug", c.get("title", "?")), license=str(spdx or "UNKNOWN"),
            runtime="react", applies_to=list(d.get("applies_to", [])),
            excluded_from=list(d.get("excluded_from", [])), deps=list(c.get("deps", [])),
            min_expressiveness=d.get("min_expressiveness", "none")))
    return out


# ----------------------------------------------------------------------------------------
# Case 8: an existing design system is never overwritten
# ----------------------------------------------------------------------------------------

def sha(p: str | Path) -> str | None:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return None


def ensure_design_md(site: str | Path, proposed: str) -> dict:
    """Existing identity wins. A present DESIGN.md is preserved byte-for-byte."""
    p = Path(site) / "DESIGN.md"
    if p.exists():
        return {"action": "PRESERVED", "sha": sha(p)}
    p.write_text(proposed, encoding="utf-8")
    return {"action": "CREATED", "sha": sha(p)}


def naive_ensure_design_md(site: str | Path, proposed: str) -> dict:
    """Seeded overwriter, for the gate's positive pole."""
    p = Path(site) / "DESIGN.md"
    p.write_text(proposed, encoding="utf-8")
    return {"action": "OVERWRITTEN", "sha": sha(p)}


# ----------------------------------------------------------------------------------------
# Case 9: a reference too close to a known brand
# ----------------------------------------------------------------------------------------

def brand_verdict(concept_id: str, description: str) -> dict:
    from modules.ccf.trademark_scanner import scan
    r = scan(concept_id, description)
    refused = r["verdict"] in ("BLOCK", "WARN")      # WARN needs a recorded acknowledgment we do not have
    return {"decision": "REFUSED" if refused else "ACCEPTED", "scanner": r["verdict"],
            "risk": r["risk_score"], "nearest": r.get("nearest_known_mark")}


# ----------------------------------------------------------------------------------------
# The slice: build, render, score, Production Reality
# ----------------------------------------------------------------------------------------

DESIGN_TEMPLATE = """---
version: alpha
name: Fernlight
description: Warm editorial signup page for a field-notes newsletter, still and quiet
aesthetic_family: F3
required_wcag: AA
bundle_budget_kb: 40
experience:
  expressiveness: {expr}
  motion_budget: {budget}
  reduced_motion: equivalent
  feedback_latency_ms: 100
  progress_threshold_ms: 1000
  waiting: none
  progress_language: none
  success_posture: confirm
  error_posture: explain_and_recover
  celebration_policy: never
  character_policy: none
  trust_posture: standard
colors:
  primary: "#191817"
  secondary: "#6b665f"
  accent: "#a8452a"
  neutral: "#f4f3ee"
  surface: "#fffdf9"
  on-surface: "#191817"
  error: "#a33a28"
typography:
  h1:
    fontFamily: Instrument Serif
    fontSize: 36px
    fontWeight: 400
    lineHeight: 1.1
---

# Fernlight

A single-purpose signup page. Quiet, editorial, one action.
"""

VARIANTS = ("good", "broken_handler", "animated", "animated_no_reduce")


def build_site(out: str | Path, *, variant: str = "good", expressiveness: str = "restrained") -> dict:
    """Write the small real site. `variant` injects exactly one delta from the good page so a
    failing variant differs from the passing one by a single causal change."""
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    budget = "none" if expressiveness == "none" else "low"
    motion_css = ""
    if expressiveness != "none" or variant.startswith("animated"):
        motion_css = "button{transition:background-color .15s}\n"
    if variant.startswith("animated"):
        motion_css += "@keyframes pulse{from{opacity:1}to{opacity:.7}}\nbutton{animation:pulse 1s infinite alternate}\n"
    if variant != "animated_no_reduce" and motion_css:
        motion_css += "@media (prefers-reduced-motion:reduce){button{transition:none;animation:none}}\n"
    target = "#statusx" if variant == "broken_handler" else "#status"
    index = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Fernlight field notes</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{margin:0;font:18px/1.55 Georgia,serif;color:#191817;background:#f4f3ee}}
main{{max-width:34rem;margin:0 auto;padding:2rem 1.25rem}}
h1{{font-size:2.25rem;line-height:1.1;font-weight:400}}
button{{min-height:48px;min-width:48px;padding:0 1.5rem;font:inherit;color:#fffdf9;background:#a8452a;border:0;border-radius:6px}}
#status{{min-height:1.6em;margin-top:1rem}}
footer{{margin-top:3rem;font-size:1rem;color:#6b665f}}
{motion_css}</style></head>
<body><main>
<h1>Notes from the field, once a month</h1>
<p>One short letter about ferns, light and slow walking. No tracking, no noise.</p>
<button id="subscribe" data-primary data-click-target="#status" data-click-expect="You are on the list.">Join the list</button>
<p id="status" role="status"></p>
<footer><a href="privacy.html">Privacy</a> &middot; <a href="terms-of-use.html">Terms of use</a></footer>
</main>
<script>
document.getElementById('subscribe').addEventListener('click', function () {{
  document.querySelector('{target}').textContent = 'You are on the list.';
}});
</script>
</body></html>
"""
    privacy = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Privacy</title></head>
<body><main><h1>Privacy</h1>
<p>This page collects no personal data and sets no cookies. Joining the list is a placeholder
action in this fixture and stores nothing.</p><p><a href="index.html">Back</a></p></main></body></html>
"""
    terms = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Terms of use</title></head>
<body><main><h1>Terms of use</h1>
<p>This page is a fixture. It makes no offer and creates no account; joining the list stores
nothing.</p><p><a href="index.html">Back</a></p></main></body></html>
"""
    (out / "terms-of-use.html").write_text(terms, encoding="utf-8")
    (out / "index.html").write_text(index, encoding="utf-8")
    (out / "privacy.html").write_text(privacy, encoding="utf-8")
    dm = ensure_design_md(out, DESIGN_TEMPLATE.format(expr=expressiveness, budget=budget))
    return {"site": str(out), "variant": variant, "design_md": dm}


def check_surface(site: str | Path, *, shot: str | Path | None = None) -> dict:
    """Render, probe, score. Returns the CDIO gate result plus every measurement."""
    from modules.cdio import scorer as S
    from tools.design_gate import parse_design_md
    site = Path(site)
    page = site / "index.html"
    design = parse_design_md(str(site / "DESIGN.md"))
    declared = design["experience"]
    r = render(page, shot=shot)
    rr = render(page, reduced_motion=True)
    sc, scr = (r.get("selfcheck") or {}), (rr.get("selfcheck") or {})
    measured = bool(r.get("ok") and rr.get("ok"))
    observed = None
    verdicts = []
    if measured:
        motion = bool(sc["motion_present"])
        equivalent = (not scr["motion_present"]) if motion else None
        observed = {"motion_present": motion, "reduced_motion_equivalent": equivalent,
                    "motion_budget": "low" if motion else "none"}
        verdicts = [
            S.check_contrast(sc["fg"], sc["bg"]),
            S.check_tap_target(min(sc["tap_sizes"] or [0])),
            S.check_mobile_font(sc["body_font_px"]),
            S.check_single_primary_cta(sc["ctas"]),
            S.check_design_md_exists(str(site / "DESIGN.md")),
            S.check_reduced_motion(motion, bool(equivalent)),
        ]
    gate = S.review_gate(verdicts, declared_experience=declared, observed_experience=observed)
    return {"measured": measured, "render": r, "render_reduced": rr, "declared": declared,
            "observed": observed, "gate": gate.to_json(),
            "interactions": sc.get("interactions"), "errors": sc.get("errors")}


def production_reality(site: str | Path, surface: dict) -> dict:
    """Law 1: green tests are not Production Reality. Every item must hold on the rendered page."""
    site = Path(site)
    sc = (surface.get("render") or {}).get("selfcheck") or {}
    shot = (surface.get("render") or {}).get("shot")
    inter = surface.get("interactions") or []
    checks = {
        "artifacts_present": all((site / f).exists() for f in ("index.html", "privacy.html", "terms-of-use.html", "DESIGN.md")),
        "screenshot_valid_png": bool(shot) and png_ok(shot),
        "rendered_h1_nonempty": bool(str(sc.get("h1", "")).strip()),
        "interaction_declared_and_works": bool(inter) and all(i["ok"] for i in inter),
        "no_page_errors": surface.get("errors") == [],
        "cdio_gate_done": bool(surface["gate"]["is_done"]),
    }
    return {"verdict": "REAL" if all(checks.values()) else "NOT_REAL", "checks": checks}


def slice_run(out_dir: str | Path, *, variant: str = "good", expressiveness: str = "restrained",
              shot: bool = True) -> dict:
    """The whole flow on one surface."""
    out = Path(out_dir)
    info = build_site(out, variant=variant, expressiveness=expressiveness)
    surf = check_surface(out, shot=(out / "render.png") if shot else None)
    from modules.cdio import legal_surface as L
    legal = L.check(str(out), "us")
    return {"build": info, "surface": surf, "legal": {"required": legal["required"], "pages": legal["pages"],
                                                      "verdict": legal["score"]["verdict"]},
            "reality": production_reality(out, surf)}


# ----------------------------------------------------------------------------------------
# Execution evidence: the only thing that raises OPERATIONAL coverage
# ----------------------------------------------------------------------------------------

def record_execution(root: str | Path, obl_id: str, cmd: list[str], *, cwd: str | Path | None = None) -> dict:
    """Actually run `cmd`; record {exit, cmd} for `obl_id`. A non-zero exit is recorded as such
    (the ledger only counts exit 0), never papered over."""
    root = Path(root)
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd or root))
    f = root / EVIDENCE
    ev = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    ev[obl_id] = {"exit": p.returncode, "cmd": " ".join(cmd),
                  "stdout_sha256": hashlib.sha256(p.stdout.encode()).hexdigest()[:16]}
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(ev, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return ev[obl_id]
