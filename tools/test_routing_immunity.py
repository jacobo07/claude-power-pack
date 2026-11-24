#!/usr/bin/env python3
"""V-RI-*: keyword routers fire on a request, not on a mention (T3-CT W3, FP-A/B/C).

FP-A design router (modules/cdio/design_route.classify), FP-B AKOS grounding (hooks/creative_grounding.js isCreative),
FP-C Woz veto (tools/quality_audit.scan). Shared span rule: modules/gsd_x/prompt_origin.mention_reason + its JS twin.
Each fix is driven from both poles: the mention no longer fires, the request still does, and a mutant of each rule
turns the gate red. The old rules are run as a CONTROL on the same fixtures, so a fixture that never reproduced the
false positive cannot pass as a fix. The real 2026-11-22/23 prompts are replayed from this host's transcripts when they
exist (they are Owner text and are not copied into this public repo); absent, that arm is INCONCLUSIVE, never PASS.
Run: python tools/test_routing_immunity.py   (exit 0 = all pass; exit 2 = only the replay arm was unobservable)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.cdio import design_route as dr  # noqa: E402
from modules.gsd_x import prompt_origin as po  # noqa: E402
from tools import quality_audit as qa  # noqa: E402

RESULTS: list = []
INCONCLUSIVE: list = []
ROUTES = dr.load_routes()
W = "place" + "holder"   # the stand-in word, built so this file is not vetoed by the gate it tests (FP-WOZ-*)
FILL = ("The ledger keeps one row per settled generation and the judge reads it at each checkpoint. " * 12 + "\n\n")


def ok(name: str, cond: bool, detail="") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-44s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:500]))


def big(core: str, n: int = 100_000) -> str:
    """`core` in the middle of ~n chars of unrelated engineering prose."""
    half = FILL * (n // (2 * len(FILL)) + 1)
    return half[: n // 2] + "\n\n" + core + "\n\n" + half[: n // 2]


# ---------------------------------------------------------------- fixtures (synthetic, same shape as the incidents)
LIST_MENTION = ("Output:\n\nverified artifact\n\n+\n\ninstitutional delta.\n\nArtifact may be:\n\nsoftware;\n\nwebsite;\n\n"
                "research;\n\nbusiness process;\n\ninfrastructure;\n\nreconstruction.")
META_MENTION = ("FALSE POSITIVE A\n\nDesign routing.\n\nThe string associated with web design was reportedly matched merely "
                "because a word such as website appeared incidentally in an artifact/example list.")
QUOTED_MENTION = 'Rename the token: the router keys on the word "website" and on `landing` only.'
AKOS_FAR = ("If a brief genuine preference decision could save enormous search, ask once.\n\n" + FILL * 3
            + "Do not create another loop engine.")
AKOS_META = ("FALSE POSITIVE B\n\nAKOS creative grounding.\n\nThe current detector accepts creative intent if a noun and a "
             "creative verb occur anywhere. The reported prompt contained a noun usage equivalent to brief and an "
             "unrelated create instruction elsewhere.")
AKOS_NEG = "Do not write a brief for this; the plan is engineering only."
AKOS_FAR_LINE = ("If a brief genuine preference decision could save search, ask once. " + FILL.strip()
                 + " Then we will create the ledger rows.")   # one line, verb not negated: only the window decides
VISUAL_LIST = "Pages: landing; pricing page; dashboard; logo"  # a list of visual things: only same_kind keeps it
AKOS_COPY = "Cognitive Copy-on-Write.\n\nZero-Copy knowledge sharing.\n\nDo not let agents copy the institution."

DESIGN_MENTIONS = {"list": LIST_MENTION, "meta": META_MENTION, "quoted": QUOTED_MENTION, "list-100k": big(LIST_MENTION),
                   "meta-100k": big(META_MENTION)}
DESIGN_REQUESTS = {"es": "hazme una landing page para un estudio de yoga",
                   "visual-list": "Necesito: landing, pricing page y dashboard para KobiiCraft",
                   "bullets": "Pages:\n- hero section\n- pricing page\n- testimonials",
                   "en": "redesign the website so the hero section loads faster",
                   "one-fp-word": "fix the false positives in the signup form of my landing page",
                   "visual-list2": VISUAL_LIST,
                   # review MEDIUM-1: router/routers is ONE signal, so a networking product's brief still routes
                   "plural-signal": "Redesign the website for our routers: each router gets a product card on the "
                                    "landing page.",
                   "req-100k": big("Then build me a landing page for the cafe, mobile first.")}
AKOS_MENTIONS = {"far": AKOS_FAR, "far-line": AKOS_FAR_LINE, "meta": AKOS_META, "negated": AKOS_NEG, "copy-eng": AKOS_COPY,
                 "far-100k": big(AKOS_FAR), "list-eng": "Kinds: claim; ledger; receipt; checkpoint"}
AKOS_REQUESTS = {"es": "escribe un anuncio para la campa\u00f1a de navidad", "brief": "write a creative brief for the launch",
                 "pair": "draft the landing claim for the yoga studio", "list": "make ads, banners, reels for KobiiCraft",
                 "copy-es": "escribe el copy del banner de verano", "req-100k": big("Now write the tagline for the cafe."),
                 # review MEDIUM-2: a verb header governs the list under it
                 "header-en": "Create the following:\n- 3 ads\n- 2 banners",
                 "header-es": "Escribe para Instagram:\n- un slogan\n- un claim",
                 # review MEDIUM-3: a list that starts with the verb is a request
                 "mixed-list": "write ads, emails, and blog posts"}
assert not set(AKOS_MENTIONS) & set(AKOS_REQUESTS), "case names must be unique: they are zipped into one dict"

OLD_NOUN = re.compile(r"\b(ads?|advert|creatives?|brief|campa[nñ]a|campaign|landing|slogan|claim|tagline|banner|post\s+de"
                      r"\s+instagram|reel)\b", re.I)
OLD_VERB = re.compile(r"\b(haz|hazme|crea|cr[eé]ame|genera|escribe|redacta|dise[nñ]a|mejora|make|create|generate|write|"
                      r"draft|design|improve|rework|rehaz)\b", re.I)
OLD_STRONG_COPY = re.compile(r"\bcopys?\b", re.I)


def old_design(p: str) -> bool:
    return bool([k for k, s in ROUTES["surfaces"].items() if s["_rx"].search(p)])


def old_akos(p: str) -> bool:
    return bool(OLD_STRONG_COPY.search(p)) or bool(OLD_NOUN.search(p) and OLD_VERB.search(p))


def akos_js(prompts: list, src: Path = ROOT / "hooks" / "creative_grounding.js") -> list | None:
    js = ("const c=require(%s);const a=JSON.parse(require('fs').readFileSync(0,'utf8'));"
          "process.stdout.write(JSON.stringify(a.map(c.isCreative)))" % json.dumps(str(src).replace("\\", "/")))
    r = subprocess.run(["node", "-e", js], input=json.dumps(prompts), capture_output=True, text=True, encoding="utf-8",
                       timeout=60)
    return json.loads(r.stdout) if r.stdout.strip() else None


def woz(ext: str, body: str) -> bool:
    fd, tmp = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(body + "\n")
    try:
        return bool(qa.scan(tmp, "C:/proj/src/x" + ext))
    finally:
        os.unlink(tmp)


def main() -> int:
    print("FP-A design router")
    for k, p in DESIGN_MENTIONS.items():
        ok("V-RI-DESIGN-CONTROL-%s" % k, old_design(p), "fixture never reproduced the false positive")
        ok("V-RI-DESIGN-MENTION-%s" % k, dr.classify(p, ROUTES) == [], dr.classify(p, ROUTES))
    for k, p in DESIGN_REQUESTS.items():
        ok("V-RI-DESIGN-REQUEST-%s" % k, dr.classify(p, ROUTES) != [], "a real request stopped routing")
    t0 = time.perf_counter()
    dr.classify(big(LIST_MENTION, 400_000), ROUTES)
    ok("V-RI-DESIGN-400K-UNDER-1S", time.perf_counter() - t0 < 1.0, time.perf_counter() - t0)

    print("FP-B AKOS grounding (JS, the dispatcher's in-process path)")
    names = list(AKOS_MENTIONS) + list(AKOS_REQUESTS)
    got = akos_js(list(AKOS_MENTIONS.values()) + list(AKOS_REQUESTS.values()))
    ok("V-RI-AKOS-JS-RAN", got is not None and len(got) == len(names), got)
    got = dict(zip(names, got or [None] * len(names)))
    for k, p in AKOS_MENTIONS.items():
        if k != "list-eng":   # has no verb at all: a true negative under the old rule too, kept as a floor
            ok("V-RI-AKOS-CONTROL-%s" % k, old_akos(p), "fixture never reproduced the false positive")
        ok("V-RI-AKOS-MENTION-%s" % k, got[k] is False, got[k])
    for k in AKOS_REQUESTS:
        ok("V-RI-AKOS-REQUEST-%s" % k, got[k] is True, got[k])

    print("FP-C Woz stand-in veto")
    mentions = [(".py", "  S1 the template renders for THIS host: no %s left, the 12 approved hooks." % W),
                (".md", '   - the Woz veto fired on the word "%s" in a docstring.' % W),
                (".md", '- veto ("Never ship a %s") matches the English word' % W.upper()),
                (".tsx", '<input %s="Email" />' % W), (".json", '{"%s": "Email"}' % W),
                (".py", "# substitutes each %s token the renderer knows" % W),
                (".py", '    """The renderer leaves no %s behind."""' % W),
                # review LOW-1: a forwarded prop, an arrow body and a CSS custom property are names
                (".tsx", "<input %s={%s} />" % (W, W)), (".js", "const f = () => %s;" % W),
                (".css", "  --%s-color: #999;" % W)]
    stubs = [(".py", 'return "%s"' % W), (".py", "x = 1  # %s for now" % W), (".py", "API_KEY = '%s'" % W.upper()),
             (".py", '"""%s implementation."""' % W.title()), (".tsx", "<p>%s text</p>" % W.title()),
             (".md", "{%s}" % W), (".md", "%s: fill in the price" % W.upper()), (".js", "const v = '<%s>';" % W),
             # review MEDIUM-4: stand-in CONTENT, not only a leading marker
             (".py", 'return "Some %s text"' % W), (".tsx", "<h1>Welcome to %s site</h1>" % W),
             (".py", "price = 0  # TBD, %s" % W), (".md", "%s: fill in the price" % W.title())]
    for i, (ext, body) in enumerate(mentions):
        ok("V-RI-WOZ-CONTROL-%d" % i, re.search(r"\b%s\b" % W, body, re.I) is not None)
        ok("V-RI-WOZ-NAME-NOT-VETOED-%d%s" % (i, ext), not woz(ext, body), body)
    for i, (ext, body) in enumerate(stubs):
        ok("V-RI-WOZ-STUB-VETOED-%d%s" % (i, ext), woz(ext, body), body)

    print("parity: JS mentionReason == python mention_reason")
    spans = []
    web = ROUTES["surfaces"]["web"]["_rx"]
    for p in list(DESIGN_MENTIONS.values())[:3] + list(DESIGN_REQUESTS.values())[:5] + [AKOS_META, AKOS_FAR, AKOS_NEG]:
        for rx in (web, OLD_NOUN, OLD_VERB):
            spans += [(p, m.start(), m.end(), rx.pattern) for m in rx.finditer(p)]
    py = [po.mention_reason(t, s, e, re.compile(k, re.I)) for t, s, e, k in spans]
    py_none = [po.mention_reason(t, s, e) for t, s, e, _ in spans]
    def js_reasons(kind: bool) -> list | None:
        r = subprocess.run(["node", str(ROOT / "hooks" / "prompt_origin.js")], capture_output=True, text=True,
                           encoding="utf-8", timeout=60,
                           input=json.dumps({"mentions": [[t, s, e, k if kind else None] for t, s, e, k in spans]}))
        return json.loads(r.stdout) if r.stdout.strip() else None
    ok("V-RI-PARITY-SAME-REASONS", js_reasons(True) == py, [x for x in zip(py, js_reasons(True) or []) if x[0] != x[1]])
    ok("V-RI-PARITY-NO-KIND", js_reasons(False) == py_none)
    ok("V-RI-PARITY-BOTH-POLES", {"", "meta", "list", "quoted"} <= set(py) | set(py_none), sorted(set(py)))

    print("mutants (each must turn the gate red)")
    saved = (po.META_MIN, po.list_item, po._quoted)
    try:
        po.META_MIN = 99
        ok("V-RI-MUTANT-META-KILLED", dr.classify(META_MENTION, ROUTES) != [])
        po.META_MIN = 1
        ok("V-RI-MUTANT-META-1-KILLED", dr.classify(DESIGN_REQUESTS["one-fp-word"], ROUTES) == [])
        po.META_MIN = saved[0]
        po.list_item = lambda *a, **k: False
        ok("V-RI-MUTANT-LIST-KILLED", dr.classify(LIST_MENTION, ROUTES) != [])
        po.list_item = (lambda text, start, end, same_kind=None, request_rx=None:      # ignores kind
                        saved[1](text, start, end, None, request_rx))
        ok("V-RI-MUTANT-NO-SAME-KIND-KILLED", dr.classify(VISUAL_LIST, ROUTES) == [])
        saved_family = po.signal_family
        po.signal_family = str.lower                                                    # review MEDIUM-1 mutant
        ok("V-RI-MUTANT-NO-FAMILY-KILLED", dr.classify(DESIGN_REQUESTS["plural-signal"], ROUTES) == [])
        po.signal_family = saved_family
        ok("V-RI-MUTANT-NO-SAME-KIND-KILLED", dr.classify(VISUAL_LIST, ROUTES) == [])
        po.list_item = saved[1]
        po._quoted = lambda *a: False
        ok("V-RI-MUTANT-QUOTED-KILLED", dr.classify(QUOTED_MENTION, ROUTES) != [])
    finally:
        po.META_MIN, po.list_item, po._quoted = saved
    with tempfile.TemporaryDirectory() as td:
        src = (ROOT / "hooks" / "creative_grounding.js").read_text(encoding="utf-8")
        shutil.copy(ROOT / "hooks" / "prompt_origin.js", Path(td) / "prompt_origin.js")
        for name, a, b, case in (("WINDOW", "const PAIR_WINDOW = 80;", "const PAIR_WINDOW = 1e9;", AKOS_FAR_LINE),
                                 ("NEGATION", "return NEGATION.test(", "return false && NEGATION.test(", AKOS_NEG)):
            m = Path(td) / ("cg_%s.js" % name)
            m.write_text(src.replace(a, b), encoding="utf-8")
            ok("V-RI-MUTANT-AKOS-%s-APPLIED" % name, a in src)
            ok("V-RI-MUTANT-AKOS-%s-KILLED" % name, akos_js([case], m) == [True], "mutant survived")

    print("replay: the real prompts from this host's transcripts")
    proj = Path(os.path.expanduser("~/.claude/projects/C--Users-User--claude-skills-claude-power-pack"))
    for sid, line in (("2e3b8dd4", 2008), ("218d8162", 659)):
        f = next(proj.glob(sid + "*.jsonl"), None)
        text = ""
        if f:
            with open(f, encoding="utf-8") as fh:
                for n, row in enumerate(fh, 1):
                    if n == line:
                        c = (json.loads(row).get("message") or {}).get("content")
                        text = c if isinstance(c, str) else " ".join(
                            x.get("text", "") for x in c or [] if isinstance(x, dict) and x.get("type") == "text")
                        break
        if len(text) < 20_000:
            INCONCLUSIVE.append(sid)
            print("  INCONCLUSIVE V-RI-REPLAY-%s (transcript line not on this host)" % sid)
            continue
        ok("V-RI-REPLAY-%s-CONTROL" % sid, old_design(text) and old_akos(text))
        ok("V-RI-REPLAY-%s-DESIGN-SILENT" % sid, dr.classify(po.owner_text(text), ROUTES) == [])
        ok("V-RI-REPLAY-%s-AKOS-SILENT" % sid, akos_js([text]) == [False])

    failed = [n for n, c in RESULTS if not c]
    print("V-RI: %d passed, %d failed, %d inconclusive" % (len(RESULTS) - len(failed), len(failed), len(INCONCLUSIVE)))
    return 1 if failed else (2 if INCONCLUSIVE else 0)


if __name__ == "__main__":
    raise SystemExit(main())
