"""V-PATHEXEMPT-* -- a remediation that is wrong must not be proposed.

normalize_paths reported 163 doc-level path leaks. 26 of the proposed
rewrites would have damaged the file or contradicted standing doctrine,
which is why the backlog sat unapplied for months: a fix that is wrong one
time in six cannot be run, so the 137 correct ones never got applied
either. An unsafe remediation suppresses the safe ones.

The exemption must be NARROW. A rule that quietly swallows real leaks
would turn a noisy gate into a silent one, which is strictly worse, so
every exemption here is paired with a bookend proving a plain leak still
gets rewritten.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from tools.normalize_paths import (  # noqa: E402
    _unsafe_rewrite, doctrine_safe_sub,
)

EXPECTED_GATES = 13
_passes: list[str] = []
_fails: list[str] = []


def _ok(g, e):
    _passes.append(g)
    print(f"  PASS {g}: {e}")


def _fail(g, d):
    _fails.append(g)
    print(f"  FAIL {g}: {d}")


def main() -> int:
    # --- doctrine: the interpreter path must stay absolute ---------------
    doc = (r"Run python via "
           r"`C:\Users\User\AppData\Local\Programs\Python\Python312"
           r"\python.exe`")
    after = doc.replace(r"C:\Users\User", "~")
    why = _unsafe_rewrite(doc, after)
    if why and "doctrine" in why:
        _ok("V-PATHEXEMPT-DOCTRINE", why)
    else:
        _fail("V-PATHEXEMPT-DOCTRINE",
              f"the mandated interpreter path would be rewritten ({why})")

    # Forward-slash spelling of the same literal.
    doc2 = ("use C:/Users/User/AppData/Local/Programs/Python/Python312"
            "/python.exe here")
    if _unsafe_rewrite(doc2, doc2.replace("C:/Users/User", "~")):
        _ok("V-PATHEXEMPT-DOCTRINE-SLASH", "posix spelling also exempt")
    else:
        _fail("V-PATHEXEMPT-DOCTRINE-SLASH",
              "only the backslash spelling is protected")

    # --- token duplication: the rewrite would destroy a distinction ------
    enum = r"a home directory (`~`, `/home/user`, `C:\Users\user`)"
    why = _unsafe_rewrite(enum, enum.replace(r"C:\Users\user", "~"))
    if why and "duplicate" in why:
        _ok("V-PATHEXEMPT-DUPLICATE-TOKEN", why)
    else:
        _fail("V-PATHEXEMPT-DUPLICATE-TOKEN",
              f"a 3-item list would collapse to 2 ({why})")

    # --- BOOKENDS: real leaks must still be rewritten --------------------
    # This is what keeps the exemption honest. If these start returning a
    # reason, the gate has stopped protecting anything.
    plain = r"Repo: `C:\Users\User\.claude\skills\claude-power-pack`."
    if _unsafe_rewrite(plain, plain.replace(r"C:\Users\User", "~")) is None:
        _ok("V-PATHEXEMPT-PLAIN-STILL-FIXED",
            "an ordinary home-path leak is still proposed for rewrite")
    else:
        _fail("V-PATHEXEMPT-PLAIN-STILL-FIXED",
              "the exemption swallowed a real leak -- a silent gate is "
              "worse than a noisy one")

    # A python.exe that is NOT the doctrine path earns no exemption.
    other = r"see `C:\Users\User\scripts\python.exe` for the helper"
    if _unsafe_rewrite(other, other.replace(r"C:\Users\User", "~")) is None:
        _ok("V-PATHEXEMPT-NARROW",
            "only the mandated interpreter path is exempt, not any exe")
    else:
        _fail("V-PATHEXEMPT-NARROW",
              "the doctrine exemption is matching too broadly")

    # A `~` inside a PATH is not a standalone token and must not exempt.
    tilde_in_path = r"`~/.ssh/id` and `C:\Users\User\.claude\state`"
    why = _unsafe_rewrite(
        tilde_in_path, tilde_in_path.replace(r"C:\Users\User", "~"))
    if why is None:
        _ok("V-PATHEXEMPT-TILDE-IN-PATH-NOT-A-TOKEN",
            "`~/.ssh/id` does not license skipping a real leak")
    else:
        _fail("V-PATHEXEMPT-TILDE-IN-PATH-NOT-A-TOKEN",
              f"a tilde inside a path suppressed a rewrite ({why})")

    # --- the exemption must not swallow a CO-LOCATED leak ----------------
    # An adversarial pass built this: the interpreter path must stay
    # absolute, the key path must not, and they share a line. Exempting
    # the line carried the key through AND counted it as allowed.
    mixed = (r"`C:\Users\User\AppData\Local\Programs\Python\Python312"
             r"\python.exe` deploy.py --key C:\Users\User\.ssh\id_rsa")
    out = doctrine_safe_sub(mixed)
    kept_doctrine = r"Python312\python.exe" in out
    fixed_leak = r"~\.ssh\id_rsa" in out
    if kept_doctrine and fixed_leak:
        _ok("V-PATHEXEMPT-SPAN-GRANULAR",
            "interpreter path kept, co-located .ssh leak rewritten")
    else:
        _fail("V-PATHEXEMPT-SPAN-GRANULAR",
              f"kept_doctrine={kept_doctrine} fixed_leak={fixed_leak}: "
              f"{out}")
    if _unsafe_rewrite(mixed, out) is None:
        _ok("V-PATHEXEMPT-MIXED-IS-A-FINDING",
            "a line with a real leak beside doctrine is still reported")
    else:
        _fail("V-PATHEXEMPT-MIXED-IS-A-FINDING",
              "a line carrying a real leak was marked exempt")

    # --- the tilde token must be a TOKEN, not any squiggle ---------------
    # Each of these exempted a genuine leak before the pattern was
    # narrowed. A gate that keeps a username out of the repo fails by
    # being too permissive, so all three are pinned.
    for gate, text in (
        ("V-PATHEXEMPT-STRIKETHROUGH",
         r"~~old path~~ the log lives at C:\Users\User\AppData\Local\pp.log"),
        ("V-PATHEXEMPT-APPROXIMATION",
         r"takes ~ 300 ms; artifacts under C:\Users\User\Downloads\x"),
        ("V-PATHEXEMPT-TILDE-SLASH",
         r"see ~/notes and also C:\Users\User\.claude\state"),
    ):
        after = text.replace(r"C:\Users\User", "~").replace(
            "C:/Users/User", "~")
        if _unsafe_rewrite(text, after) is None:
            _ok(gate, "not treated as a token; the leak is still rewritten")
        else:
            _fail(gate, "a squiggle exempted a real home-path leak")

    # BOOKEND: a genuinely quoted tilde token still earns the exemption.
    quoted = (r"a home directory (`~`, `/home/user`, `C:\Users\user`)")
    if _unsafe_rewrite(quoted, quoted.replace(r"C:\Users\user", "~")):
        _ok("V-PATHEXEMPT-QUOTED-TILDE-STILL-EXEMPT",
            "`~` as a delimited token still protects the enumeration")
    else:
        _fail("V-PATHEXEMPT-QUOTED-TILDE-STILL-EXEMPT",
              "narrowed too far -- the three-item list would collapse again")

    # --- the mechanism is actually reached on the real tree --------------
    # A rule nobody's corpus triggers is indistinguishable from an unwired
    # one, and this repo has been bitten by exactly that.
    from tools.normalize_paths import _normalize_for  # noqa: PLC0415
    target = PP / "commands" / "customclaw.md"
    exempted = 0
    if target.is_file():
        _t, changes = _normalize_for(
            target.read_text(encoding="utf-8", errors="replace"), target)
        exempted = sum(1 for c in changes
                       if str(c[3]).startswith("doc-exempt:"))
    if exempted:
        _ok("V-PATHEXEMPT-REACHED",
            f"{exempted} exemption(s) fire on a real repo file")
    else:
        _fail("V-PATHEXEMPT-REACHED",
              "no exemption fires anywhere -- the rule is unreachable")

    ran = len(_passes) + len(_fails)
    print(f"\nPATHEXEMPT_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
