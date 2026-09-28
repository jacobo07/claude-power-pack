"""V-RCON-* gates for tools/install_reviewer_contract.py -- on a synthetic agent file only.

The real ~/.claude/agents/pp-code-reviewer.md is READ (its current state is reported), never
written: installing there is the Owner's step (HR-001).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import install_reviewer_contract as irc  # noqa: E402
import review_intake as ri  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


ORIGINAL = "---\nname: pp-code-reviewer\ndescription: test double\ntools: Bash, Read\n---\n\n# Body\nKeep me.\n"


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="rcon-"))
    agent = d / "pp-code-reviewer.md"
    agent.write_text(ORIGINAL, encoding="utf-8")

    check("V-RCON-ABSENT", irc.check(agent) == irc.ABSENT)
    state, why = irc.install(agent)
    text = agent.read_text(encoding="utf-8")
    check("V-RCON-INSTALL", state == irc.INSTALLED and irc.check(agent) == irc.INSTALLED, why)
    check("V-RCON-PRESERVES", text.startswith(ORIGINAL.rstrip("\n")) and "Keep me." in text,
          "frontmatter and body untouched; the block is appended")
    check("V-RCON-CARRIES-CONTRACT", ri.REPLY_INSTRUCTION in text and "REVIEW-TICKET" in text,
          "the installed text is rendered from review_intake.REPLY_INSTRUCTION")
    backups = list(d.glob("pp-code-reviewer.md.bak-*"))
    check("V-RCON-BACKUP", len(backups) == 1 and backups[0].read_text(encoding="utf-8") == ORIGINAL)

    state, why = irc.install(agent)
    check("V-RCON-IDEMPOTENT", state == irc.INSTALLED and "nothing written" in why
          and agent.read_text(encoding="utf-8") == text and len(list(d.glob("*.bak-*"))) == 1, why)

    agent.write_text(text.replace("exactly as given", "roughly"), encoding="utf-8")
    check("V-RCON-STALE", irc.check(agent) == irc.STALE, "an edited block is STALE, not INSTALLED")
    state, _ = irc.install(agent)
    repaired = agent.read_text(encoding="utf-8")
    check("V-RCON-REPAIR", state == irc.INSTALLED and repaired.count(irc.BEGIN) == 1 and "Keep me." in repaired,
          "the stale block is replaced in place, never duplicated")

    notagent = d / "notes.md"
    notagent.write_text("# just notes\n", encoding="utf-8")
    state, why = irc.install(notagent)
    check("V-RCON-NOT-AGENT", state == irc.NO_AGENT and notagent.read_text(encoding="utf-8") == "# just notes\n", why)
    check("V-RCON-MISSING", irc.check(d / "nope.md") == irc.NO_AGENT)

    real = irc.check(Path.home() / ".claude" / "agents" / "pp-code-reviewer.md")
    print(f"INFO real agent contract state: {real} (installing is the Owner's step)")
    check("V-RCON-REAL-READABLE", real in (irc.INSTALLED, irc.ABSENT, irc.STALE), real)
    print(f"RCON_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
