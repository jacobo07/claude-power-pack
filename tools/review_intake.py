"""Reviewer output intake (assimilation item 24, genesis-review-gate -> CONNECT).

A reviewer agent's reply becomes a verdict here, and the failure this exists for is the silent
one: a reviewer that crashed, timed out, answered in prose, or used a severity nobody counts must
not come out the other end as APPROVE. "Zero Findings Is Valid" (the ECC doctrine) is kept -- but
only for a reviewer that SAID zero, i.e. returned an explicit `"findings": []`. Absence of findings
is not a finding count.

Schema: the vendored review gate's strict finder response, validated through the one bridge --
    {"findings": [{"id", "severity": critical|high|medium|low|info, "title", "description", "evidence"}]}
The provider identity is supplied by the CALLER, who knows what it dispatched; a reviewer's claim
about itself is not identity.

Verdicts: BLOCK (a critical) · WARNING (a high) · APPROVE (only medium/low/info, or an explicit
empty list) · INCOMPLETE (no reply, no JSON, more than one JSON object, schema refused, or the
bridge could not answer -- each with its reason). INCOMPLETE is never an approval.

    python tools/review_intake.py --reply reply.txt --provider pp-code-reviewer --model claude-sonnet-5
exit 0 APPROVE · 1 WARNING · 4 BLOCK · 3 INCOMPLETE
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.external_assimilation import node_bridge as nb  # noqa: E402

APPROVE, WARNING, BLOCK, INCOMPLETE = "APPROVE", "WARNING", "BLOCK", "INCOMPLETE"

# Append to any reviewer dispatch: a reviewer cannot meet a schema it was never shown (the batch
# drafts run on 2026-09-28 was refused for exactly that). The reviewer agents live in
# ~/.claude/agents, outside this repo (HR-001), so the contract travels with the prompt instead.
REPLY_INSTRUCTION = (
    "End your reply with exactly one ```json fenced block and nothing after it: "
    '{"findings": [{"id": "short-unique-id", "severity": "critical|high|medium|low|info", '
    '"title": "...", "description": "...", "evidence": "file:line and the quoted code"}]}. '
    'If you found nothing, the block is {"findings": []} -- say it explicitly; a reply without the '
    "block is recorded as an INCOMPLETE review, never as an approval.")
# Any json-family label, any case (a real reviewer may write ```JSON or ```jsonc): a label this
# regex did not know sent a good review to INCOMPLETE (real review of this file, 2026-09-28).
_FENCE = re.compile(r"```[ \t]*(?:json\w*)?[ \t]*\r?\n?\s*(\{.*?\})\s*```", re.S | re.I)
# A reviewer may quote a dict from the code in a BARE fence beside the one ```json block it was
# asked for; counting both as candidates refused a compliant review (third real review). When a
# json-labelled fence exists, only labelled fences count.
_LABELLED = re.compile(r"```[ \t]*json\w*[ \t]*\r?\n?\s*(\{.*?\})\s*```", re.S | re.I)


class _Duplicate(ValueError):
    pass


def _no_duplicates(pairs):
    # json.loads keeps the LAST duplicate key, so {"findings":[critical],"findings":[]} collapsed
    # to an approval before anything could judge it (same review). A duplicate is malformed.
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise _Duplicate(f"duplicate key {sorted(k for k in set(keys) if keys.count(k) > 1)}")
    return dict(pairs)


@dataclass
class Intake:
    verdict: str
    reason: str = ""
    findings: list = field(default_factory=list)
    counts: dict = field(default_factory=dict)


def _one_json(text: str):
    """Exactly one JSON object: a fenced block, or the whole reply. Two candidates is ambiguous."""
    fenced = _LABELLED.findall(text) or _FENCE.findall(text)
    if len(fenced) > 1:
        return None, f"{len(fenced)} JSON blocks in the reply; exactly one is required"
    candidate = fenced[0] if fenced else text.strip()
    try:
        return json.loads(candidate, object_pairs_hook=_no_duplicates), ""
    except _Duplicate as exc:
        return None, f"malformed JSON: {exc}"
    except ValueError:
        return None, "no parseable JSON findings object in the reply"


def intake(reply: str | None, provider: str, model: str, timeout: float = 30.0) -> Intake:
    if not reply or not reply.strip():
        return Intake(INCOMPLETE, "empty reply: the reviewer produced nothing (failed, timed out or never ran)")
    obj, why = _one_json(reply)
    if obj is None:
        return Intake(INCOMPLETE, why)
    if not isinstance(obj, dict) or set(obj) != {"findings"}:
        return Intake(INCOMPLETE, "the reply object must contain exactly the key `findings`")
    r = nb.call("review", "validateFinderResponse",
                [{"provider": {"name": provider, "model": model}, "findings": obj["findings"]}], timeout=timeout)
    if not r.ok:
        return Intake(INCOMPLETE, f"bridge {r.outcome}: {r.error}")
    if r.value:  # upstream returns an error string, or null when valid
        return Intake(INCOMPLETE, f"schema: {r.value}")
    counts = {s: 0 for s in ("critical", "high", "medium", "low", "info")}
    for f in obj["findings"]:
        counts[f["severity"]] += 1
    verdict = BLOCK if counts["critical"] else WARNING if counts["high"] else APPROVE
    return Intake(verdict, "" if obj["findings"] else "explicit empty findings list", obj["findings"], counts)


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reply", required=True, help="file holding the reviewer's reply text")
    ap.add_argument("--provider", required=True)
    ap.add_argument("--model", required=True)
    a = ap.parse_args(argv)
    try:
        text = Path(a.reply).read_text(encoding="utf-8-sig")
    except OSError as exc:
        text = ""
        print(f"note: reply unreadable ({exc.__class__.__name__})")
    res = intake(text, a.provider, a.model)
    print(f"{res.verdict} {json.dumps(res.counts) if res.counts else ''} {res.reason}".strip())
    for f in res.findings:
        print(f"  [{f['severity']}] {f['id']}: {f['title']}")
    return {APPROVE: 0, WARNING: 1, BLOCK: 4}.get(res.verdict, 3)


if __name__ == "__main__":
    sys.exit(main())
