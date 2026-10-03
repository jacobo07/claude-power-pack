#!/usr/bin/env python
"""V-SKINV gates for tools/skill_invocations.py (PLAN-SKILL-RESIDENCY C1, audit G'8/G'9).

Fixture rows copy the SHAPES of real transcript rows (6eb83acf: name-first /clear at :9, Skill
tool_use at :37, its isMeta body with sourceToolUseID at :41, message-first /kclear at :866 and its
turnCompanion expansion at :867; 6d128db5: typed /kresume). Bodies are shortened, keys are real.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_invocations as si  # noqa: E402

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


SID = "11111111-aaaa-bbbb-cccc-000000000001"
INSTALLED = {"kclear", "kresume", "cpp-gsd-long", "concurrent-writers-shared-tree", "bmad:prd"}


def u(content, **kw):
    return {"type": "user", "sessionId": SID, "uuid": kw.pop("uuid", None), "isSidechain": False,
            "message": {"role": "user", "content": content}, **kw}


def tool(name, inp, tid):
    return {"type": "assistant", "sessionId": SID, "session_id": "eb8fcbf6-508f-4c86-8a82-180bf323d952",
            "message": {"id": "msg_" + tid, "content": [{"type": "tool_use", "id": tid, "name": name, "input": inp}]}}


ROWS_REAL = [
    tool("Skill", {"skill": "cpp-gsd-long"}, "toolu_A"),                                          # model 1
    u([{"type": "text", "text": "# /cpp-gsd-long - unattended run"}], isMeta=True,
      sourceToolUseID="toolu_A", turnCompanion=True),                                              # body: 0
    u("<command-message>kclear</command-message>\n<command-name>/kclear</command-name>", uuid="u1"),  # typed 1
    u([{"type": "text", "text": "# /kclear - Session Checkpoint"}], isMeta=True, turnCompanion=True),  # 0
    u("<command-name>/kresume</command-name>\n  <command-message>kresume</command-message>\n"
      "  <command-args></command-args>", uuid="u2"),                                               # typed 1, name-first
    u("<command-name>/bmad:prd</command-name><command-message>bmad:prd</command-message>", uuid="u3"),  # nested cmd
]
ROWS_ZERO = [
    u("<command-name>/clear</command-name>\n<command-message>clear</command-message>", uuid="z1"),  # built-in
    {"type": "attachment", "sessionId": SID, "attachment": {"type": "skill_listing",
     "content": "- concurrent-writers-shared-tree\n- kclear: Session checkpoint"}},                  # listing
    {"type": "attachment", "sessionId": SID, "attachment": {"type": "hook_additional_context",
     "content": ["<command-message>kclear</command-message><command-name>/kclear</command-name>"]}},  # hook text
    tool("Bash", {"command": "grep '\"Skill\"' x.jsonl; echo '<command-name>/kclear</command-name>'"}, "toolu_B"),
    u("Please run the concurrent-writers-shared-tree skill later", uuid="z2"),                       # mention
    u("<command-message>kclear</command-message>\n<command-name>/kclear</command-name>", uuid="z3",
      isMeta=True),                                                                                 # meta copy
]


def write(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "projects" / "C--repo"
        main_f = root / f"{SID}.jsonl"
        write(main_f, ROWS_REAL + ROWS_ZERO)

        r = si.count_file(main_f, INSTALLED)
        check("V-SKINV-MODEL", dict(r["model"]) == {"cpp-gsd-long": 1}, f"model={dict(r['model'])}")
        check("V-SKINV-TYPED-BOTH-ORDERS", r["typed"]["kclear"] == 1 and r["typed"]["kresume"] == 1,
              f"typed={dict(r['typed'])}")
        check("V-SKINV-NESTED-COMMAND", r["typed"]["bmad:prd"] == 1, "commands/bmad/prd.md -> bmad:prd")
        check("V-SKINV-BUILTIN-ZERO", "clear" not in r["typed"], "/clear is not an installed skill")
        check("V-SKINV-EXPANSION-ZERO", sum(r["model"].values()) + sum(r["typed"].values()) == 4,
              "isMeta bodies (sourceToolUseID, turnCompanion) and the isMeta command copy add nothing")
        check("V-SKINV-MENTION-ZERO", r["model"]["concurrent-writers-shared-tree"] == 0
              and r["typed"]["concurrent-writers-shared-tree"] == 0, "listing, hook text, Bash input, prose")

        # Positive control on the instrument: a naive substring counter over the SAME file must
        # over-count, or the zero-fixtures above could not have failed.
        raw = main_f.read_text(encoding="utf-8")
        naive = len(re.findall(r"<command-name>/kclear", raw)) + raw.count("concurrent-writers-shared-tree")
        check("V-SKINV-ZERO-FIXTURES-DISCRIMINATE", naive > 1 + 0, f"naive count {naive} vs real kclear=1, cwst=0")

        # Dedupe: the same rows again in a resumed copy of the transcript count once per id/uuid.
        dup = root / "22222222-resumed.jsonl"
        write(dup, ROWS_REAL)
        s = si.scan(root.parent, 1, INSTALLED)
        check("V-SKINV-DEDUPE", s["model"]["cpp-gsd-long"] == 1 and s["typed"]["kclear"] == 1,
              f"model={dict(s['model'])} typed={dict(s['typed'])}")

        # Subagent sidechain joins its parent by FILE session id, not by a row's session_id.
        sub = root / SID / "subagents" / "agent-x.jsonl"
        write(sub, [tool("Skill", {"skill": "concurrent-writers-shared-tree"}, "toolu_S")])
        rs = si.count_file(sub, INSTALLED)
        check("V-SKINV-SUBAGENT-JOIN", rs["session"] == SID and rs["model"]["concurrent-writers-shared-tree"] == 1,
              f"session={rs['session'][:8]} (row session_id is eb8fcbf6)")

        # List-form user row carrying a command tag without isMeta: an aperture, reported, not counted.
        lf = root / "33333333-listform.jsonl"
        write(lf, [u([{"type": "text", "text": "<command-message>kclear</command-message><command-name>/kclear</command-name>"}],
                     uuid="l1")])
        rl = si.count_file(lf, INSTALLED)
        check("V-SKINV-LISTFORM-UNKNOWN", rl["unknown_rows"] == 1 and not rl["typed"], f"unknown_rows={rl['unknown_rows']}")

    # Real positive control: this program's own session typed /kresume and never called Skill for it.
    real = list((Path.home() / ".claude" / "projects").glob("*/6d128db5-0b16-415e-9a38-367d870ee525.jsonl"))
    if real:
        rr = si.count_file(real[0], si.installed_names())
        check("V-SKINV-REAL-TYPED", rr["typed"]["kresume"] >= 1 and rr["model"]["kresume"] == 0,
              f"typed kresume={rr['typed']['kresume']}, model kresume={rr['model']['kresume']}")
    else:
        _fail("V-SKINV-REAL-TYPED", "positive-control transcript not found")

    print(f"SKINV_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
