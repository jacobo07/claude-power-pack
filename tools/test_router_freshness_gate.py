"""V-gates for the router freshness gate.

The point of these gates is falsifiability. A gate that cannot fail is the defect
it was built to catch, so every check below constructs a state that MUST fail and
asserts that it does -- not only that the clean repo passes.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.router_freshness_gate as gate  # noqa: E402

PASSES: list[str] = []
FAILS: list[str] = []


def _ok(name: str, evidence: str) -> None:
    PASSES.append(name)
    print(f"  PASS  {name}  {evidence}")


def _fail(name: str, diagnostic: str) -> None:
    FAILS.append(name)
    print(f"  FAIL  {name}  {diagnostic}")


class Scenario:
    """A throwaway ~/.claude tree: a repo root, a vault, and a derived router."""

    def __enter__(self) -> "Scenario":
        self.tmp = Path(tempfile.mkdtemp(prefix="rfg_"))
        self.claude = self.tmp / ".claude"
        self.repo = self.claude / "skills" / "claude-power-pack"
        (self.repo / "vault" / "knowledge_base").mkdir(parents=True)
        (self.claude / "knowledge_vault").mkdir(parents=True)
        self._saved = (gate.CLAUDE_DIR, gate.KNOWLEDGE_VAULT)
        gate.CLAUDE_DIR = self.claude
        gate.KNOWLEDGE_VAULT = self.claude / "knowledge_vault"
        self.router = gate.router_path(self.repo)
        self.router.parent.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, *exc: object) -> None:
        gate.CLAUDE_DIR, gate.KNOWLEDGE_VAULT = self._saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_router(self, body: str) -> None:
        self.router.write_text(body, encoding="utf-8")

    def make_store(self, rel: str, n_ids: int) -> Path:
        """Write a file dense enough in distinct sealed ids to count as a store."""
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        ids = "\n".join(f"- T-SYNTHETIC-RULE-{i:04d}-001 body" for i in range(n_ids))
        p.write_text(f"# store\n{ids}\n", encoding="utf-8")
        return p

    def rel_to_router(self, target: Path) -> str:
        return os.path.relpath(target, self.router.parent).replace("\\", "/")

    def run(self) -> int:
        return gate.run(self.repo)


def main() -> int:
    print("== V-RFG gates ==")

    # V-RFG-CLEAN -- the real repo, as repaired, passes.
    if gate.run() == 0:
        _ok("V-RFG-CLEAN", "live repo exits 0")
    else:
        _fail("V-RFG-CLEAN", "live repo does not pass")

    # V-RFG-BROKEN-LINK -- an unresolvable pointer must fail.
    with Scenario() as s:
        s.write_router("- [gone](does_not_exist.md) - hook\n")
        if s.run() == 1:
            _ok("V-RFG-BROKEN-LINK", "unresolvable pointer exits 1")
        else:
            _fail("V-RFG-BROKEN-LINK", "broken link did not fail the gate")

    # V-RFG-INLINE -- a bullet with no pointer is stored knowledge, not an index.
    with Scenario() as s:
        s.write_router("- knowledge written straight into the router\n")
        if s.run() == 1:
            _ok("V-RFG-INLINE", "inline entry exits 1")
        else:
            _fail("V-RFG-INLINE", "inline entry did not fail the gate")

    # V-RFG-STORE-UNREACHABLE -- a store nobody points at must fail.
    with Scenario() as s:
        s.make_store("vault/knowledge_base/corpus.md", gate.DENSITY_STORE_MIN)
        s.write_router("")
        if s.run() == 1:
            _ok("V-RFG-STORE-UNREACHABLE", "unindexed store exits 1")
        else:
            _fail("V-RFG-STORE-UNREACHABLE", "unindexed store did not fail the gate")

    # V-RFG-STORE-REACHABLE -- pointing at it clears the same state.
    with Scenario() as s:
        store = s.make_store("vault/knowledge_base/corpus.md", gate.DENSITY_STORE_MIN)
        s.write_router(f"- [corpus]({s.rel_to_router(store)}) - hook\n")
        if s.run() == 0:
            _ok("V-RFG-STORE-REACHABLE", "indexed store exits 0")
        else:
            _fail("V-RFG-STORE-REACHABLE", "indexed store still fails")

    # V-RFG-DISCOVERED -- the store set is walked off disk, not listed.
    with Scenario() as s:
        s.write_router("")
        before = len(gate.discover_stores(s.repo))
        s.make_store("vault/knowledge_base/late_arrival.md", gate.DENSITY_STORE_MIN)
        after = len(gate.discover_stores(s.repo))
        if before == 0 and after == 1:
            _ok("V-RFG-DISCOVERED", "store appears without being declared")
        else:
            _fail("V-RFG-DISCOVERED", f"before={before} after={after}, expected 0 then 1")

    # V-RFG-BELOW-THRESHOLD -- a file that merely cites rules is not a store.
    with Scenario() as s:
        s.make_store("vault/knowledge_base/citing_doc.md", gate.DENSITY_STORE_MIN - 1)
        s.write_router("")
        if s.run() == 0:
            _ok("V-RFG-BELOW-THRESHOLD", "citing document is not enrolled")
        else:
            _fail("V-RFG-BELOW-THRESHOLD", "citing document wrongly enrolled as a store")

    # V-RFG-BUDGET -- an over-budget router is inline knowledge creeping back.
    with Scenario() as s:
        s.write_router("\n".join("- [x](MEMORY.md) h" for _ in range(gate.ROUTER_MAX_LINES + 1)))
        if s.run() == 1:
            _ok("V-RFG-BUDGET", f"over {gate.ROUTER_MAX_LINES} lines exits 1")
        else:
            _fail("V-RFG-BUDGET", "over-budget router did not fail the gate")

    total = len(PASSES) + len(FAILS)
    print(f"ROUTER_GATE_TESTS={len(PASSES)}/{total}  threshold={total}/{total}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
