"""Install the review reply contract into the pp-code-reviewer agent -- run BY THE OWNER.

The live review protocol (tools/evidence_bundle.py + tools/review_intake.py) accepts a review only
when the reply (a) echoes the one-time `REVIEW-TICKET: <nonce>` line of its dispatch and (b) ends
with exactly one ```json findings block. Until now that contract travelled only inside each
review prompt, because the agent definition lives at ~/.claude/agents/pp-code-reviewer.md and
HR-001 bars the agent from writing under ~/.claude. This tool is the Owner-side half: the text is
version-controlled HERE and rendered from review_intake.REPLY_INSTRUCTION, so the two cannot drift.

    python tools/install_reviewer_contract.py --check     read-only: INSTALLED 0 · ABSENT 3 · STALE 4 · NO_AGENT 5
    python tools/install_reviewer_contract.py --install   Owner: backs up, replaces ONLY the marked block

Nothing outside the marked block is touched; installing twice is a no-op.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import review_intake as ri  # noqa: E402

BEGIN, END = "<!-- CPP-REVIEW-REPLY-CONTRACT", "<!-- /CPP-REVIEW-REPLY-CONTRACT -->"
INSTALLED, ABSENT, STALE, NO_AGENT = "INSTALLED", "ABSENT", "STALE", "NO_AGENT"


def agent_path() -> Path:
    return Path(os.environ.get("CPP_REVIEWER_AGENT_PATH")
                or (Path.home() / ".claude" / "agents" / "pp-code-reviewer.md"))


def body() -> str:
    return "\n".join([
        "## Reply contract (CPP review protocol -- mandatory)",
        "",
        "When your dispatch contains a line `REVIEW-TICKET: <nonce>`, copy that line into your reply",
        "exactly as given. The nonce proves your reply was written for THIS dispatch of THESE bytes; a",
        "reply without it is recorded as unbound and cannot approve anything.",
        "",
        ri.REPLY_INSTRUCTION,
        "",
        "Severity words outside critical|high|medium|low|info are not understood by the intake and",
        "make the review INCOMPLETE -- use exactly these five.",
    ])


def block() -> str:
    b = body()
    return f"{BEGIN} sha256={hashlib.sha256(b.encode('utf-8')).hexdigest()[:16]} -->\n{b}\n{END}"


_BLOCK_RE = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)


def check(path: Path | None = None) -> str:
    p = path or agent_path()
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return NO_AGENT
    m = _BLOCK_RE.search(text)
    if not m:
        return ABSENT
    return INSTALLED if m.group(0) == block() else STALE


def install(path: Path | None = None) -> tuple[str, str]:
    p = path or agent_path()
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return NO_AGENT, f"cannot read {p}: {exc}"
    if not text.startswith("---"):
        return NO_AGENT, f"{p} has no frontmatter; refusing to edit something that is not an agent file"
    if check(p) == INSTALLED:
        return INSTALLED, "already installed; nothing written"
    backup = p.with_name(p.name + f".bak-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(p, backup)
    new = _BLOCK_RE.sub(lambda _m: block(), text) if _BLOCK_RE.search(text) else text.rstrip("\n") + "\n\n" + block() + "\n"
    p.write_text(new, encoding="utf-8")
    after = check(p)
    if after != INSTALLED or not new.startswith(text.split("\n", 1)[0]):
        shutil.copy2(backup, p)
        return STALE, f"post-write check read {after}; original restored from {backup}"
    return INSTALLED, f"installed; backup at {backup}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--install", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        state = check()
        print(f"{state}: {agent_path()}")
        return {INSTALLED: 0, ABSENT: 3, STALE: 4}.get(state, 5)
    state, why = install()
    print(f"{state}: {why}")
    return 0 if state == INSTALLED else 1


if __name__ == "__main__":
    sys.exit(main())
