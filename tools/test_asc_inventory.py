"""V-ASC-INV gate: obligation inventory, driven from both poles.

Run from repo root: python3 tools/test_asc_inventory.py   (exit 0 == PASS)
"""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.backlog_autopilot import inventory as inv  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    print(("PASS " if cond else "FAIL ") + name + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def fixture(d: Path):
    (d / "vault/backlog").mkdir(parents=True)
    (d / "vault/plans").mkdir(parents=True)
    (d / "vault/backlog/2026-10-10_animejs-design-absorption.md").write_text(
        "# Backlog — Absorb Anime.js into Design\nStatus: PENDING\n")
    (d / "vault/backlog/2026-10-11_animejs-design-absorption-remaining.md").write_text(
        "# Absorb Anime.js into Design (remaining)\n")  # semantic duplicate
    (d / "vault/backlog/2026-10-12_taste-skill-wiring.md").write_text("# Wire the Taste Skill\n")
    (d / "vault/plans/ccf-integrity-plan.md").write_text("# CCF integrity audit plan\nStatus: DONE\n")
    (d / "vault/OWNER_QUEUE.md").write_text("# Q\n## NEW -- do X  [RESOLVED 2026-10-07]\n## NEW -- do Y\n")
    (d / "RESUMPTION_FILE.md").write_text("# resume\n")


with tempfile.TemporaryDirectory() as t:
    d = Path(t)
    fixture(d)
    full = inv.build(d)

    # NEGATIVE-GATE clean pole
    check("clean fixture verifies PASS", inv.verify(full, d) == [], str(inv.verify(full, d)))

    # POSITIVE pole 1: seeded omission (drop one member from the inventory) must FAIL
    bad = copy.deepcopy(full)
    for ident in bad["identities"]:
        ident["members"] = [m for m in ident["members"] if "taste-skill" not in m["source"]]
    bad["identities"] = [i for i in bad["identities"] if i["members"]]
    bad["raw_count"] = sum(len(i["members"]) for i in bad["identities"])
    f = inv.verify(bad, d)
    check("seeded omission FAILS the gate", any("taste-skill" in x for x in f), str(f))

    # POSITIVE pole 2: an obligation added on disk AFTER the inventory is stale -> FAIL
    (d / "vault/backlog/2026-11-01_late.md").write_text("# Late brand logo obligation\n")
    check("post-inventory new source detected", any("late" in x for x in inv.verify(full, d)))

    # duplicate collapse
    anime = [i for i in full["identities"] if any("animejs" in m["source"] for m in i["members"])]
    check("semantic duplicate collapses to ONE identity", len(anime) == 1 and len(anime[0]["members"]) == 2,
          f"{len(anime)} identities")
    # distinct items must NOT collapse
    taste = [i for i in full["identities"] if any("taste" in m["source"] for m in i["members"])]
    check("distinct obligation stays separate", len(taste) == 1 and len(taste[0]["members"]) == 1)

    # states are source-claimed only
    oq = [m["state"] for i in full["identities"] for m in i["members"] if m["kind"] == "owner_queue"]
    check("owner_queue RESOLVED vs OPEN read from source", sorted(oq) == ["OPEN", "RESOLVED"], str(oq))
    plan = [m for i in full["identities"] for m in i["members"] if m["kind"] == "plan"][0]
    check("plan state from its own Status line", plan["state"] == "RESOLVED")

    # seeds: resolved when present, UNRESOLVED (not dropped) when absent
    check("seed present is IN_INVENTORY", full["seeds"]["animejs"]["status"] == "IN_INVENTORY")
    check("seed unseen is NOT_OBSERVED (not ABSENT, not dropped)",
          full["seeds"]["meta-astryx"]["status"] == "NOT_OBSERVED" and "meta-astryx" in full["seeds"])
    (d / "notes.md").write_text("we should look at design index someday\n")
    check("seed referenced outside inventory is REFERENCED_ELSEWHERE",
          inv.build(d)["seeds"]["design-index"]["status"] == "REFERENCED_ELSEWHERE")
    (d / "notes.md").unlink()

    # unreadable source is explicit and fails verify
    p = d / "vault/backlog/2026-10-13_bad.md"
    p.write_text("x")
    orig = inv._read
    inv._read = lambda q: (None, "EACCES") if q.name == "2026-10-13_bad.md" else orig(q)
    try:
        u = inv.build(d)
    finally:
        inv._read = orig
    check("unreadable source recorded and fails verify",
          "vault/backlog/2026-10-13_bad.md" in u["unreadable"] and any("UNREADABLE" in x for x in inv.verify(u, d)))

# determinism on the REAL tree + real-tree verify
a = inv.build(ROOT)
b = inv.build(ROOT)
check("real tree: deterministic", a == b)
check("real tree: verify PASS", inv.verify(a, ROOT) == [], str(inv.verify(a, ROOT))[:300])
# NOTE: identities == raw on the real tree is the honest measured result (0.85 Jaccard; the
# 0.60-0.71 near-pairs are distinct obligations). Collapse is proven on the fixture above.
check("real tree: no seed silently missing", set(a["seeds"]) == set(inv.SEEDS))

print("V-ASC-INV", "FAIL" if FAILS else "PASS", FAILS or "")
sys.exit(1 if FAILS else 0)
