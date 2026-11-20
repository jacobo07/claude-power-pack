"""Derivatives, tokens, release proof, preview contexts, similarity honesty, applicability (BCAP2-07 / BI-15, 22-23, 25, 26, 29, 34).
Pure policy/validators; no provider, no network, no shell. Everything derives from ONE approved source.
"""
from __future__ import annotations

import hashlib
import re

# --- BI-22/23: export profile; one source, requested derivatives only
FORMATS = {"svg", "png", "webp", "ico", "pdf"}
ICO_SIZES = {16, 24, 32, 48, 64, 128, 256}


def check_export_profile(profile: dict) -> list:
    p = []
    if not profile.get("source_sha256"):
        p.append("no approved source hash: derivatives need one vector/Visual DNA source")
    items = profile.get("derivatives") or []
    if not items:
        p.append("no derivatives requested")
    for i, d in enumerate(items):
        if d.get("format") not in FORMATS:
            p.append(f"derivative {i}: unknown format {d.get('format')!r}")
        if d.get("generated_independently"):
            p.append(f"derivative {i}: independent generative rerun refused; derive from the source")
        if d.get("format") != "svg" and not (d.get("size") or d.get("sizes")):
            p.append(f"derivative {i}: explicit output size required")
        if d.get("format") == "ico":
            bad = [s for s in (d.get("sizes") or []) if s not in ICO_SIZES]
            if bad or not d.get("sizes"):
                p.append(f"derivative {i}: ico sizes {bad or 'missing'} invalid")
            if d.get("container") != "ico":
                p.append(f"derivative {i}: ico must be a real ICO container, not renamed PNG")
        if d.get("shell_command"):
            p.append(f"derivative {i}: shell execution refused")
        if d.get("font_fallback") == "silent":
            p.append(f"derivative {i}: silent font fallback refused")
    return p


# --- BI-25: DTCG tokens
def check_dtcg(tokens: dict) -> list:
    p = []

    def walk(node, path):
        if "$value" in node:
            if "$type" not in node:
                p.append(f"{path}: $value without $type")
            v = node["$value"]
            if isinstance(v, str) and v.startswith("{") and v.endswith("}") and not _resolve(tokens, v[1:-1]):
                p.append(f"{path}: alias {v} does not resolve")
            return
        for k, v in node.items():
            if not k.startswith("$") and isinstance(v, dict):
                walk(v, f"{path}.{k}" if path else k)
    walk(tokens, "")
    return p


def _resolve(tokens, ref):
    n = tokens
    for part in ref.split("."):
        if not isinstance(n, dict) or part not in n:
            return False
        n = n[part]
    return isinstance(n, dict) and "$value" in n


def to_css(tokens: dict) -> str:
    out = []

    def walk(node, path):
        if "$value" in node:
            v = node["$value"]
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                v = f"var(--{v[1:-1].replace('.', '-')})"
            out.append(f"  --{'-'.join(path)}: {v};"); return
        for k, v in node.items():
            if not k.startswith("$") and isinstance(v, dict):
                walk(v, path + [k])
    walk(tokens, [])
    return ":root {\n" + "\n".join(out) + "\n}\n"


# --- BI-26: release manifest
def build_manifest(version: str, files: dict, meta: dict) -> dict:
    """files: name->bytes. Refuses (raises ValueError) when approval/refs missing: no partial manifest."""
    need = [k for k in ("owner_approval", "generator_ref", "license_notice", "brief_ref", "visual_dna_ref") if not meta.get(k)]
    if need or not version or not files:
        raise ValueError(f"manifest refused: missing {need or 'version/files'}")
    return {"version": version, "immutable": True, "meta": dict(meta),
            "files": {n: {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)} for n, b in sorted(files.items())}}


def verify_manifest(manifest: dict, files: dict) -> list:
    p = []
    for n, e in manifest["files"].items():
        if n not in files:
            p.append(f"{n}: listed but absent")
        elif hashlib.sha256(files[n]).hexdigest() != e["sha256"]:
            p.append(f"{n}: hash mismatch")
    p += [f"{n}: present but not in manifest (contamination)" for n in files if n not in manifest["files"]]
    return p


# --- BI-15: application preview contexts
CONTEXTS = ("masthead", "avatar", "favicon", "photography", "packaging", "print", "ad_overlay", "mobile_screen", "social_canvas")


def check_preview(preview: dict, dna_id: str) -> list:
    p = []
    seen = {c.get("context"): c for c in preview.get("contexts", [])}
    for c in CONTEXTS:
        e = seen.get(c)
        if not e:
            p.append(f"context {c}: not tested"); continue
        if e.get("visual_dna") != dna_id:
            p.append(f"context {c}: identity reinvented (visual_dna {e.get('visual_dna')!r} != {dna_id!r})")
        if e.get("is_mock") is not True and not e.get("real_evidence"):
            p.append(f"context {c}: neither marked mock nor backed by real evidence")
    return p


# --- BI-29: similarity screening with honest status
def similarity_report(corpus: dict, nearest: list, human_review: bool = False) -> dict:
    """corpus: {size, provenance_logged, coverage_note}. A PASS is only 'no near match in THIS corpus', never clearance."""
    problems = []
    if not corpus.get("provenance_logged"):
        problems.append("corpus provenance not logged")
    if not corpus.get("size"):
        return {"verdict": "ABSTAIN", "problems": problems + ["empty corpus"], "clearance": "NOT_ASSESSED"}
    verdict = "REVIEW" if any(n.get("score", 0) >= 0.8 for n in nearest) else ("SCREEN_NO_NEAR_MATCH" if not problems else "ABSTAIN")
    return {"verdict": verdict, "problems": problems, "corpus_size": corpus["size"], "nearest": nearest[:5],
            "clearance": "NOT_ASSESSED", "legal_review_required": True, "human_review_done": bool(human_review),
            "limitation": "screening against the stated corpus only; not trademark clearance or universal uniqueness"}


# --- BI-34: automatic applicability
TRIGGERS = (r"\bnew (brand|logo|identity)\b", r"\b(design|make|create) (a |an )?(logo|wordmark|brand mark|icon)\b",
            r"\bbrand (kit|package|palette|typography)\b", r"\blogo variants?\b", r"\bvisual identity\b")


def applicable(prompt: str, budget_ok: bool = True) -> dict:
    hit = next((t for t in TRIGGERS if re.search(t, prompt or "", re.I)), None)
    if not hit:
        return {"route": "NONE", "reason": "no CCF trigger"}
    if not budget_ok:
        return {"route": "ABSTAIN", "reason": "budget gate"}
    return {"route": "CCF", "load": ["ccf"], "human_approval_required": True}
