"""K4 challenger builder (vault/plans/skill-virtualization-k-slice-2026-10-03.md).

Derives the gateway cohort from MEASURED inputs, never a hand list:
  - the champion's initial skill_listing (transcript id),
  - 7-day invocations (tools/skill_invocations.py output, both channels),
  - the Owner protection rule (2026-10-03 Q4): moved-rule skills, authority/security/recovery-critical,
    production-dependent, claude-power-pack / kresume / kclear, anything invoked in 7 d,
  - pageability: only a skill with a SKILL.md on disk (skill_index.directory_rows) can leave the listing.
Writes, under --out (default ~/Apps/listing-probe):
  champion/                                    empty cwd, current settings
  challenger/.claude/skills/capability-directory/SKILL.md   project-level gateway (no live pane sees it)
  challenger-settings.json                     per-run skillOverrides: cohort -> user-invocable-only
Nothing under ~/.claude is written.

  python capability_directory_experiment.py --listing-from <session_id> --invocations <skill_invocations.txt>
"""
import argparse, glob, json, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from modules.skill_router.skill_index import directory_rows  # noqa: E402

MOVED = {"concurrent-writers-shared-tree", "destructive-state-authorization", "develop-here-prove-there",
         "evaluation-corpus-governance", "guard-event-reachability", "instrument-before-claim",
         "monetary-quantity-integrity", "presence-is-not-residency", "real-context-reachability",
         "recurring-work-cardinality"}
CRITICAL = {"claude-power-pack", "kresume", "kclear", "lazarus", "resume-clean", "restart", "session-handoff-protocol",
            "secrets-management", "security-review", "security-scan",   # authority / security / recovery
            "kobiicraft-ops"}                                           # production-dependent (live server ops)
GATEWAY_DESC = ("Directory of installed specialist capabilities that are NOT in this skill list (e.g. APK reverse "
                "engineering, Wii homebrew and ports, data visualization, mobile app UI, video analysis, KobiiCraft "
                "plugin work, Claude Code configuration). Read it whenever a task might need a specialized method "
                "you do not see listed.")


def listing_entries(session_id):
    f = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session_id}.jsonl"))[0]
    for line in open(f, encoding="utf-8"):
        if '"skill_listing"' in line:
            a = json.loads(line).get("attachment") or {}
            if a.get("type") == "skill_listing" and a.get("isInitial"):
                return [ln[2:].partition(":")[0].strip() for ln in a["content"].splitlines() if ln.startswith("- ")]
    sys.exit("no initial skill_listing in that transcript")


def invoked(path):
    out = set()
    for ln in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\s+(\d+)\s+(\d+)\s+(\S+)", ln)
        if m and int(m.group(1)) + int(m.group(2)) > 0:
            out.add(m.group(3))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listing-from", required=True)
    ap.add_argument("--invocations", required=True)
    ap.add_argument("--out", default=str(Path.home() / "Apps" / "listing-probe"))
    a = ap.parse_args()
    names = listing_entries(a.listing_from)
    used = invoked(a.invocations)
    candidates = [n for n in names if n not in used and n not in MOVED and n not in CRITICAL and ":" not in n]
    rows, unpageable = directory_rows(candidates)
    out = Path(a.out)
    (out / "champion").mkdir(parents=True, exist_ok=True)
    gw = out / "challenger" / ".claude" / "skills" / "capability-directory"
    gw.mkdir(parents=True, exist_ok=True)
    body = ["---", "name: capability-directory", f"description: {GATEWAY_DESC}", "---", "",
            "# Capability directory", "",
            "These capabilities are installed but kept out of the skill list. When one fits the task, Read",
            "`~/.claude/skills/<folder>/SKILL.md` and follow it exactly as if the skill had been invoked.",
            "The folder is the capability name unless another folder is given in brackets.", ""]
    # Page cost is paid on every read: one line per capability, no absolute paths (K4 economics).
    body += [f"- {r['name']}" + ("" if Path(r["path"]).parent.name == r["name"] else f" [{Path(r['path']).parent.name}]")
             + f": {r['line'][:100].replace(chr(10), ' ')}" for r in rows]
    (gw / "SKILL.md").write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")
    settings = {"skillOverrides": {r["name"]: "user-invocable-only" for r in rows}}
    (out / "challenger-settings.json").write_text(json.dumps(settings, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({"listed": len(names), "invoked_7d": len(used & set(names)), "protected": len(set(names) & (MOVED | CRITICAL)),
                      "moved_to_gateway": len(rows), "unpageable_kept_listed": len(unpageable),
                      "gateway_body_chars": len("\n".join(body)), "out": str(out)}, indent=1))
    print("unpageable:", ", ".join(unpageable))
    return 0


if __name__ == "__main__":
    sys.exit(main())
