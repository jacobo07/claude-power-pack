"""session_delta -- the Session Delta Gate.

The post-session producer for `<cwd>/.claude/cache/learnings/`, the input path
`hooks/learning-sentinel.js` and `compound-learnings/SKILL.md` already read and
that nothing in the estate wrote. See `delta.py` for the boundary contract
against `fable_distillation` and `governance/KNOWLEDGE_CAPTURE_GOVERNANCE.md`
for the ownership ruling it operates under.
"""
from .delta import (  # noqa: F401
    SessionDelta,
    collect,
    escalate,
    render,
    run,
    takeaway,
    target_path,
)

__all__ = [
    "SessionDelta",
    "collect",
    "escalate",
    "render",
    "run",
    "takeaway",
    "target_path",
]
