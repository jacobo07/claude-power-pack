"""Autonomy Decision Gate: CAN THE AGENT SAFELY DECIDE THIS ITSELF?

Seeded by the Self-Continuation Protocol's rubric (supplied without a license: the four
categories are used as ideas, no text copied) and EXTENDING modules/decision_review's DRK
reversibility classifier rather than competing with it.

A pending decision belongs to the Owner only when it is one of four things:
  resource-blocked  needs a credential, access or permission the agent lacks
  irreversible      destroys or overwrites state that is not cheaply undoable
  outward-facing    sends to people, publishes, spends, deploys -- UNLESS a durable
                    authorization covers that action (e.g. `git-push` for this repo)
  preference        pure taste with no derivable best answer
Everything else is the agent's: choose from the evidence, state in one line why it is safe
(reversible + internal + derivable), continue.

Fail-CLOSED at this boundary: a gate that raised hands the decision to the Owner. Upstream's
"utilities never throw" is right for a meter and wrong for an authorization.

Every verdict can be recorded as a compact receipt in ~/.claude/state/autonomy-decisions.jsonl
(question redacted through modules/secret_firewall and truncated).

    python -m modules.autonomy_gate classify "should I force-push the rebased branch?"
    python -m modules.autonomy_gate classify "push the feature branch" --authorized git-push
exit 0 = AGENT decides, 10 = OWNER decides.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

AGENT, OWNER = "AGENT", "OWNER"
RESOURCE, IRREVERSIBLE, OUTWARD, PREFERENCE, SELF = (
    "resource-blocked", "irreversible", "outward-facing", "preference", "self-answerable")

_RESOURCE = re.compile(
    r"\b(credentials?|api[\s-]?keys?|secrets?|passwords?|access\s+tokens?|oauth|2fa|otp|"
    r"log\s?in\b|login|sudo|permission\s+denied|no\s+access|need\s+access|grant\s+access)\b", re.I)
_IRREVERSIBLE = re.compile(
    r"\b(force[\s-]?push|push\s+--force|reset\s+--hard|rm\s+-rf|remove-item\s+.*-recurse|"
    r"drop\s+(table|database|schema)|truncate|purge|wipe|shred|"
    r"delete\s+(the\s+)?(branch|backups?|database|production|prod|user|account|repo|bucket|records?|rows?|history)|"
    r"overwrite\s+(uncommitted|the\s+owner|their|production|prod)|discard\s+(uncommitted|changes|work)|"
    r"production\s+data|data\s+loss|migrat\w*\s+(prod|production)|rotate\s+(the\s+)?(secret|key)|"
    r"revoke|cancel\s+(the\s+)?(order|subscription)|rewrite\s+(git\s+)?history|irreversibl\w*|permanent(ly)?)\b",
    re.I)
_OUTWARD = {
    "git-push": re.compile(r"\bgit\s+push\b|\bpush\s+(to\s+)?(the\s+)?(remote|origin|upstream|github)|\bpush\s+(the\s+)?(branch|commits?)\b", re.I),
    "deploy": re.compile(r"\b(deploy\w*|go[\s-]?live|release\s+to|ship\s+to\s+prod\w*|restart\s+(the\s+)?(prod|production|server))\b", re.I),
    "message": re.compile(r"\b(send|e-?mail|dm|tweet|post\s+(to|on)|message\s+(the|to)|notify\s+(users|customers|the\s+team)|slack)\b", re.I),
    "publish": re.compile(r"\b(publish\w*|open\s+(a\s+)?(pr|pull\s+request)|comment\s+on\s+(the\s+)?(pr|issue))\b", re.I),
    "spend": re.compile(r"\b(charge|refund|pay(ment)?|invoice|purchase|buy|subscribe|spend\s+(money|credits?|\$))\b", re.I),
}
_PREFERENCE = re.compile(
    r"\b(prefer(ence)?|your\s+call|taste|do\s+you\s+like|looks?\s+(better|nicer)|brand\s+voice|"
    r"which\s+(\w+\s+){0,2}(name|colou?r|font|style|tone|voice|theme|logo|palette|wording))\b", re.I)

RECEIPTS = Path(os.environ.get("CPP_AUTONOMY_RECEIPTS")
                or Path.home() / ".claude" / "state" / "autonomy-decisions.jsonl")


def _reversibility(question: str) -> str | None:
    """DRK's own classifier (EXTEND, not a second one). None if DRK cannot be loaded."""
    try:
        from modules.decision_review.decision_kernel import classify_reversibility
        from modules.decision_review.decision_record import DecisionObject
        # DecisionObject requires id/statement/problem/options/chosen/rationale (decision_record.py:139).
        obj = DecisionObject(id="autonomy-gate", statement=question, problem="", options=[], chosen="",
                             rationale="")
        return classify_reversibility(obj).value
    except Exception:  # noqa: BLE001 -- reported as unknown, never as reversible
        return None


def durable_authorizations(extra=()) -> set[str]:
    env = os.environ.get("CPP_AUTONOMY_AUTHORIZED", "")
    return {a.strip() for a in env.split(",") if a.strip()} | set(extra or ())


def classify(question: str | None, *, authorized=()) -> dict:
    try:
        q = " ".join(str(question or "").split())
        auth = durable_authorizations(authorized)
        rev = _reversibility(q) if q else None
        if not q:
            return {"owner": AGENT, "category": SELF, "reversibility": rev,
                    "why": "no decision was posed: continue the current plan"}
        if _RESOURCE.search(q):
            return {"owner": OWNER, "category": RESOURCE, "reversibility": rev,
                    "why": "needs a credential or access the agent does not hold"}
        if _IRREVERSIBLE.search(q):
            return {"owner": OWNER, "category": IRREVERSIBLE, "reversibility": rev,
                    "why": "destroys or overwrites state that is not cheaply undoable"}
        for kind, rx in _OUTWARD.items():
            if rx.search(q):
                if kind in auth:
                    return {"owner": AGENT, "category": OUTWARD, "authorized_by": kind, "reversibility": rev,
                            "why": f"outward-facing, covered by the durable authorization '{kind}'"}
                return {"owner": OWNER, "category": OUTWARD, "kind": kind, "reversibility": rev,
                        "why": f"outward-facing ({kind}) and no durable authorization covers it"}
        if _PREFERENCE.search(q):
            return {"owner": OWNER, "category": PREFERENCE, "reversibility": rev,
                    "why": "pure preference: no best answer can be derived from evidence"}
        return {"owner": AGENT, "category": SELF, "reversibility": rev,
                "why": "internal and reversible (git-tracked) with a derivable best option: decide and continue"}
    except Exception as exc:  # noqa: BLE001 -- FAIL CLOSED: an authorization that crashed is not a yes
        return {"owner": OWNER, "category": "gate-error", "reversibility": None,
                "why": f"autonomy gate failed ({exc.__class__.__name__}); surfacing instead of guessing"}


def record(verdict: dict, question: str | None, *, source: str, session: str | None = None,
           chosen: str | None = None) -> bool:
    try:
        try:
            from modules.secret_firewall.redactor import redact_for_log
            q = redact_for_log(str(question or ""), max_len=160)
        except Exception:  # noqa: BLE001 -- no redactor: record length only, never raw text
            q = f"<{len(str(question or ''))} chars, redactor unavailable>"
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": source, "session": session,
               "owner": verdict.get("owner"), "category": verdict.get("category"),
               "reversibility": verdict.get("reversibility"), "why": verdict.get("why"), "question": q}
        if chosen:
            row["chosen"] = chosen[:160]
        RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
        with open(RECEIPTS, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


# One source for the text both the Python side and the subprocess-free Stop hook inject.
_RUBRIC_FILE = Path(__file__).with_name("rubric.json")
_R = json.loads(_RUBRIC_FILE.read_text(encoding="utf-8"))
RUBRIC = _R["rubric"]
WAKE_ORDER = _R["wake_order"]
