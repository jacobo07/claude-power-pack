"""Executable UX contracts absorbed from the Synsation sources (BCAP2-05; ledger vault/programs/bcap-2/synsation/DISPOSITIONS.md).

Three pure functions. They decide on DECLARED records, never on pixels: what a browser really measures is a
different plane (LAPTOP_STEPS.md). Each returns closed-vocabulary results so a gate can drive both poles.

  waiting_pattern(...)       CDIO-07 `waiting` enum chosen by scope/latency/truth (UX-07..13). Never invents progress.
  check_disabled_control(r)  causality of a disabled control (UX-01/02). A short, visible, obvious prerequisite passes.
  check_hit_targets(ts, ...) declared hit rectangles, not glyph size (UX-04..06). Floor 44 (CDIO-05/08), 48 for android.

Thresholds are HEURISTIC defaults exposed as arguments, not external evidence.
"""
from __future__ import annotations

WAITING = ("none", "spinner", "skeleton", "progress", "optimistic", "keep-content", "staged", "pending-settlement")
DISABLED_DEFECTS = ("opaque-disabled-action", "disabled-with-hidden-prerequisite", "stale-disabled-state",
                    "disabled-but-clickable", "enabled-but-inert", "validation-block-with-no-error-path")
TARGET_DEFECTS = ("undersized-hit-target", "overlapping-hit-targets", "hit-area-steals-neighbour",
                  "accidental-destructive-hit", "nested-interactive-steals-tap")
SHOW_DELAY_MS = 300     # below this no indicator at all (CDIO-07 spinner-flash defect); heuristic default
LONG_MS = 1000          # CDIO-03 >1 s no-feedback measurement
FLOOR_PX = 44


def waiting_pattern(scope, latency_ms, *, geometry_known=False, progress_measurable=False, reversible=False,
                    success_likely=False, stale_ok=False, irreversible_critical=False):
    """-> {pattern, reason}. scope in page|section|component|control. Unknown/None latency is refused, not guessed."""
    if scope not in ("page", "section", "component", "control"):
        return {"pattern": None, "reason": "unknown scope %r" % (scope,)}
    if not isinstance(latency_ms, (int, float)) or isinstance(latency_ms, bool) or latency_ms < 0:
        return {"pattern": None, "reason": "latency not measured: a pattern is not chosen from an absent value"}
    if irreversible_critical:
        # truth first: never claim completion before the system settles, whatever the latency
        return {"pattern": "pending-settlement", "reason": "irreversible/critical action: explicit pending then settled state"}
    if latency_ms < SHOW_DELAY_MS:
        return {"pattern": "none", "reason": "below show-delay %d ms: an indicator would flash" % SHOW_DELAY_MS}
    if reversible and success_likely and scope in ("control", "component"):
        return {"pattern": "optimistic", "reason": "reversible + likely success: immediate local state WITH reconciliation/rollback"}
    if stale_ok and scope != "control":
        return {"pattern": "keep-content", "reason": "stale content still trustworthy: keep it, mark refresh subtly"}
    if progress_measurable and latency_ms >= LONG_MS:
        return {"pattern": "progress", "reason": "measurable long operation: real progress only"}
    if scope in ("page", "section") and geometry_known:
        return {"pattern": "skeleton", "reason": "known final geometry: skeleton reserves it"}
    if scope in ("control", "component"):
        return {"pattern": "spinner", "reason": "local bounded work: inline indicator on the waiting control"}
    return {"pattern": "staged", "reason": "unknown structure and duration: staged/indeterminate status, no fake progress"}


def check_disabled_control(rec):
    """rec keys: disabled, reason_visible, reason_text, recoverable, perceivable_without_color, aria_disabled,
    enabled_when_valid, form_long, offscreen_prereq, click_handler_fires, has_error_path, error_summary. -> [defect]."""
    out = []
    dis = bool(rec.get("disabled"))
    if not dis:
        if rec.get("inert_when_clicked"):
            out.append("enabled-but-inert")
        return out
    if rec.get("click_handler_fires"):
        out.append("disabled-but-clickable")
    if rec.get("enabled_when_valid") is False:
        out.append("stale-disabled-state")
    if not rec.get("reason_visible") and not rec.get("reason_text"):
        out.append("opaque-disabled-action")
    if rec.get("offscreen_prereq") and not rec.get("reason_visible"):
        out.append("disabled-with-hidden-prerequisite")
    if rec.get("blocked_by_validation") and not rec.get("has_error_path"):
        out.append("validation-block-with-no-error-path")
    if rec.get("blocked_by_validation") and rec.get("form_long") and not rec.get("error_summary") \
            and "validation-block-with-no-error-path" not in out:
        out.append("validation-block-with-no-error-path")
    return out


def _rect(t):
    h = t.get("hit") or {}
    return h.get("x"), h.get("y"), h.get("w"), h.get("h")


def _overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return min(ax + aw, bx + bw) - max(ax, bx) > 0 and min(ay + ah, by + bh) - max(ay, by) > 0


def check_hit_targets(targets, *, floor=FLOOR_PX):
    """targets: [{id, hit:{x,y,w,h}, destructive?, parent?, stops_propagation?, interactive?}]. -> [{id, defect, detail}].
    A target with no declared hit rect is reported undersized (absent is not a pass)."""
    out = []
    rects = {}
    for t in targets:
        r = _rect(t)
        if any(v is None for v in r):
            out.append({"id": t.get("id"), "defect": "undersized-hit-target", "detail": "no hit rect declared"})
            continue
        rects[t["id"]] = r
        if r[2] < floor or r[3] < floor:
            out.append({"id": t["id"], "defect": "undersized-hit-target", "detail": "%sx%s < %d" % (r[2], r[3], floor)})
    byid = {t.get("id"): t for t in targets}
    ids = sorted(rects)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            ta, tb = byid[a], byid[b]
            if ta.get("parent") == b or tb.get("parent") == a:
                continue  # nesting is judged below, not as an overlap
            if _overlap(rects[a], rects[b]):
                out.append({"id": a, "defect": "overlapping-hit-targets", "detail": "%s overlaps %s" % (a, b)})
                if ta.get("destructive") != tb.get("destructive"):
                    d = a if ta.get("destructive") else b
                    out.append({"id": d, "defect": "accidental-destructive-hit",
                                "detail": "destructive target overlaps a safe one"})
    for t in targets:
        p = t.get("parent")
        if p in byid and byid[p].get("interactive") and not t.get("stops_propagation"):
            out.append({"id": t["id"], "defect": "nested-interactive-steals-tap",
                        "detail": "activation reaches parent %s" % p})
    return out
