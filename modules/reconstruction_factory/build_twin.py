"""Build Twin: recover WHICH toolchain configuration produced a set of target objects, from anchors whose source is known.
Every recipe and every manifest variant is a hypothesis; each is scored by how many anchors it reproduces EXACTLY (judge). The verdict:
  TWIN_CONFIRMED     one configuration reproduces all anchors and every other configuration fails at least one
  TWIN_UNCERTAIN     two or more configurations tie on the anchors (the anchors cannot discriminate them) -> BUILD_TWIN_UNCERTAIN
  TWIN_NONE          no configuration reproduces all anchors
`discriminating` lists the anchors on which configurations disagree: only those carry information."""
from . import judge as J


def hypotheses(project):
    """-> [(id, {lang: flags})]. Configurations with identical effective flags are ONE hypothesis (their ids are joined with '=')."""
    tc = project.doc["toolchain"]
    raw = [("recipe:" + r, r, None) for r in sorted(tc["recipe"])] + [("variant:" + v, tc["variant"][v]["base"], v) for v in sorted(tc.get("variant", {}))]
    merged = {}
    for hid, base, variant in raw:
        key = tuple((lang, tuple(sorted(project.flags(base, lang, variant)))) for lang in ("c", "cxx"))
        merged.setdefault(key, []).append(hid)
    return [("=".join(ids), {lang: list(fl) for lang, fl in key}) for key, ids in merged.items()]


def twin(factory, anchors, targets):
    """anchors: [function names]; targets: {function: object path}. Compile each anchor's source under each hypothesis' flags."""
    P = factory.project
    rows = {}
    for hid, flags in hypotheses(P):
        ok = []
        for fn in anchors:
            f = P.functions[fn]
            c = factory.compile_text(fn, factory.read_source(fn, "heldout" if f.get("heldout") else "ref"), flags=flags[f["lang"]])
            ok.append(bool(c.ok and J.judge(targets[fn], c.obj, f["symbols"])["exact"]))
        rows[hid] = ok
    full = [h for h, ok in rows.items() if all(ok)]
    disc = [fn for i, fn in enumerate(anchors) if len({ok[i] for ok in rows.values()}) > 1]
    if not full:
        verdict = "TWIN_NONE"
    elif len(full) == 1:
        verdict = "TWIN_CONFIRMED"
    else:
        verdict = "TWIN_UNCERTAIN"
    return {"verdict": verdict, "matches": full, "score": {h: sum(ok) for h, ok in rows.items()}, "discriminating": disc, "anchors": len(anchors)}
