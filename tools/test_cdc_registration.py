"""CDC C9: C3/C4/C6 hooks are chained in the repo dispatcher and exist; C7 gate exists.
Mutation drill: a chain missing a hook must be reported."""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ = {
    "PreToolUse-Agent-default": ["cognitive_admission.js", "semantic_breaker.js"],
    "PreToolUse-Bash-default": ["semantic_breaker.js"],
    "PreToolUse-Web-default": ["research_reuse.js"],
    "PostToolUse-Web-default": ["research_reuse.js"],
}


def chains(text):
    out = {}
    for m in re.finditer(r"'([A-Za-z]+-[A-Za-z]+-default)':\s*\[([^\]]*)\]", text):
        out[m.group(1)] = re.findall(r"'([^']+)'", m.group(2))
    return out


def missing(text, root=ROOT):
    ch = chains(text)
    bad = []
    for k, files in REQ.items():
        for f in files:
            if not any(x.endswith("/" + f) for x in ch.get(k, [])):
                bad.append(f"{k}:{f}:unchained")
            elif not os.path.isfile(os.path.join(root, "hooks", f)):
                bad.append(f"{k}:{f}:nofile")
    return bad


def main():
    text = open(os.path.join(ROOT, "hooks", "hook-dispatcher.js"), encoding="utf-8").read()
    fails = []
    b = missing(text)
    if b:
        fails.append(f"REAL {b}")
    mut = text.replace("hooks/cognitive_admission.js", "hooks/x_removed.js")
    if not missing(mut):
        fails.append("MUTANT cognitive_admission removal not detected")
    mut2 = text.replace("hooks/research_reuse.js", "hooks/x_removed.js")
    if not missing(mut2):
        fails.append("MUTANT research_reuse removal not detected")
    for f in ("tools/cognitive_ci.py",):
        if not os.path.isfile(os.path.join(ROOT, f)):
            fails.append(f"C7 gate missing {f}")
    print(f"{'FAIL' if fails else 'PASS'} test_cdc_registration {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
