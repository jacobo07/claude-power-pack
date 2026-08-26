"""Control surface for durable knowledge acquisition.

Every command here is wired to the real runtime. There is no command that
reports a status it did not read from persisted state.

  ingest    load corpora declared in corpora.json into the registry
  status    counts by state, by corpus, vault size, current work
  next      show what would be claimed next, without claiming it
  search    full-text search over prompts
  history   the full audit trail for one prompt
  recover   expire dead leases and requeue eligible failures
  verify    re-hash every raw artifact and report corruption

Run:  python -m modules.knowledge_acquisition.cli <command>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .corpus_parser import CorpusParseError, parse_corpus
from .models import ConversationMode
from .raw_vault import RawVault
from .store import Store

_CONFIG = Path(__file__).parent / "corpora.json"


def _load_config(path: Path = _CONFIG) -> dict:
    if not path.exists():
        raise SystemExit(f"config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _open(cfg: dict) -> Store:
    root = Path(cfg["vault_root"]).expanduser()
    return Store(root / "kacq.db", RawVault(root / "raw"))


# --------------------------------------------------------------------------


def cmd_ingest(args) -> int:
    cfg = _load_config()
    store = _open(cfg)
    rc = 0
    try:
        for entry in cfg["corpora"]:
            if args.corpus and entry["corpus_id"] != args.corpus:
                continue
            path = Path(entry["path"]).expanduser()
            print(f"\n[{entry['corpus_id']}] {entry['label']}")
            print(f"  source: {path}")
            try:
                result = parse_corpus(
                    path, entry["corpus_id"], entry["expected_count"]
                )
            except CorpusParseError as exc:
                print(f"  REFUSED: {exc}")
                rc = 1
                continue

            stats = store.ingest_corpus(
                result,
                priority=entry.get("priority", 100),
                conversation_mode=ConversationMode(
                    entry.get("conversation_mode", "ISOLATED")
                ),
                source=f"corpus:{entry['corpus_id']}",
            )
            print(f"  parsed {len(result.prompts)} prompts "
                  f"({len(result.answered)} already answered, "
                  f"{len(result.rejected_markers)} markers rejected)")
            print(f"  inserted={stats['inserted']} "
                  f"already_present={stats['already_present']} "
                  f"imported_answers={stats['imported_answers']}")
        _print_status(store)
    finally:
        store.close()
    return rc


def _print_status(store: Store) -> None:
    s = store.stats()
    print("\n-- registry --")
    print(f"  prompts   {s['prompts']:>6}")
    print(f"  responses {s['responses']:>6}")
    print(f"  events    {s['events']:>6}")
    print("  by state:")
    for state, n in s["by_state"].items():
        print(f"    {state:<12} {n:>6}")
    print("  by corpus:")
    for cid, n in s["by_corpus"].items():
        print(f"    {cid:<12} {n:>6}")
    v = store.vault.stats()
    print("  raw vault:")
    for kind, d in v.items():
        print(f"    {kind:<12} {d['count']:>6} files  {d['bytes'] / 1024:>10.1f} KB")

    pending = s["by_state"].get("PENDING", 0)
    done = s["by_state"].get("COMPLETE", 0)
    total = s["prompts"] or 1
    print(f"\n  progress: {done}/{total} complete ({100 * done / total:.1f}%), "
          f"{pending} pending")


def cmd_status(args) -> int:
    store = _open(_load_config())
    try:
        _print_status(store)
    finally:
        store.close()
    return 0


def cmd_next(args) -> int:
    """Show what would be claimed next. Read-only: claims nothing."""
    store = _open(_load_config())
    try:
        row = store.con.execute(
            "SELECT p.external_id, p.corpus_id, p.family, p.ordinal, p.raw_prompt "
            "FROM job j JOIN prompt p ON p.prompt_id=j.prompt_id "
            "WHERE j.state='PENDING' ORDER BY p.priority ASC, p.ordinal ASC LIMIT ?",
            (args.limit,),
        ).fetchall()
        if not row:
            print("no pending prompts")
            return 0
        for r in row:
            print(f"[{r['corpus_id']}] {r['external_id']:>10} ord={r['ordinal']:<5} "
                  f"{r['family'][:38]:<40} {r['raw_prompt'][:70]}")
    finally:
        store.close()
    return 0


def cmd_search(args) -> int:
    store = _open(_load_config())
    try:
        hits = store.search_prompts(args.query, limit=args.limit)
        if not hits:
            print("no matches")
            return 0
        for h in hits:
            print(f"[{h['state']:<9}] {h['external_id']:>10}  {h['raw_prompt'][:90]}")
    finally:
        store.close()
    return 0


def cmd_history(args) -> int:
    store = _open(_load_config())
    try:
        rows = store.history(args.prompt_id)
        if not rows:
            print("no events for that prompt id")
            return 1
        for e in rows:
            frm = e["from_state"] or "-"
            print(f"{e['at']}  {frm:>12} -> {e['to_state']:<12} "
                  f"{e['reason']} [{e['actor']}]")
    finally:
        store.close()
    return 0


def cmd_recover(args) -> int:
    store = _open(_load_config())
    try:
        expired = store.recover_expired_leases()
        requeued = store.requeue_failed(max_attempts=args.max_attempts)
        print(f"expired leases returned to PENDING: {expired}")
        print(f"failed jobs requeued after backoff : {requeued}")
        _print_status(store)
    finally:
        store.close()
    return 0


def cmd_verify(args) -> int:
    store = _open(_load_config())
    try:
        checked, corrupt = store.vault.verify_all()
        print(f"artifacts checked: {checked}")
        if corrupt:
            print(f"CORRUPT ({len(corrupt)}):")
            for c in corrupt:
                print(f"  {c}")
            return 1
        print("all artifacts hash to their own name")
    finally:
        store.close()
    return 0


def _session(cfg: dict, name: str | None):
    from .session import BrowserSession

    key = name or cfg.get("default_interface")
    iface = cfg.get("interfaces", {}).get(key)
    if not iface:
        raise SystemExit(f"unknown interface {key!r}; check corpora.json")
    root = Path(cfg["vault_root"]).expanduser() / "session" / key
    return BrowserSession(root, iface["base_url"]), iface


def cmd_session_bootstrap(args) -> int:
    cfg = _load_config()
    sess, iface = _session(cfg, args.interface)
    print(f"Opening {iface['label']} at {iface['base_url']}")
    print("A real Chromium window will open.")
    print("  1. Log in normally.")
    print("  2. Land on the EVA chat screen.")
    print("  3. CLOSE the window. That is the completion signal.")
    print("\nNothing here reads, stores, or logs your credentials. The login")
    print("persists in a git-ignored browser profile.\n")

    r = sess.bootstrap(timeout_seconds=args.timeout)
    print(f"profile state : {r.state.value}")
    print(f"last url      : {r.url}")
    print(f"last title    : {r.title}")
    print(f"note          : {r.reason}")
    return 0


def cmd_session_probe(args) -> int:
    cfg = _load_config()
    sess, iface = _session(cfg, args.interface)
    print(f"probing {iface['label']} (headless={not args.headed})")
    r = sess.probe(headless=not args.headed)
    print(f"  state    : {r.state.value}")
    print(f"  url      : {r.url}")
    print(f"  title    : {r.title}")
    print(f"  reason   : {r.reason}")
    if r.snapshot_path:
        print(f"  snapshot : {r.snapshot_path}")
    return 0 if r.state.value == "READY" else 2


def cmd_session_status(args) -> int:
    cfg = _load_config()
    sess, iface = _session(cfg, args.interface)
    print(f"interface : {iface['label']}")
    print(f"base_url  : {iface['base_url']}")
    print(f"profile   : {sess.profile_dir}")
    print(f"state     : {sess.state().value}")
    return 0


def cmd_run(args) -> int:
    """The acquisition loop against a real interface."""
    from .eva_adapter import EvaAdapter
    from .runner import AcquisitionRunner

    cfg = _load_config()
    sess, iface = _session(cfg, args.interface)
    store = _open(cfg)

    print(f"interface : {iface['label']}")
    print(f"limit     : {args.limit if args.limit else 'until drained'}")
    print(f"pacing    : {args.pacing}s between prompts")
    print(f"headed    : {args.headed}\n")

    # A dry run touches neither the browser nor the ledger, so it needs no lock.
    if args.dry_run:
        try:
            runner = AcquisitionRunner(store, None, pacing_s=args.pacing)
            report = runner.run(
                limit=args.limit, corpus_id=args.corpus, family=args.family,
                max_attempts=args.max_attempts, dry_run=True,
            )
            print(f"\n{report.line()}")
            _print_status(store)
            return 0
        finally:
            store.close()

    from .runlock import LockBusy, ProfileLock

    lock = ProfileLock(sess.profile_dir)
    if args.steal_lock:
        prev = lock.force_release()
        if prev:
            print(f"  cleared lock held by pid {prev.get('pid')} "
                  f"(last heartbeat {prev.get('heartbeat')})")
    try:
        lock.acquire()
    except LockBusy as exc:
        print(f"REFUSED: {exc}")
        print("  If that run is dead -- it was killed, or the machine "
              "rebooted -- re-run with --steal-lock.")
        store.close()
        return 3

    adapter = EvaAdapter(sess, headless=not args.headed)
    try:
        adapter.launch()
        runner = AcquisitionRunner(store, adapter, pacing_s=args.pacing, lock=lock)
        report = runner.run(
            limit=args.limit,
            corpus_id=args.corpus,
            family=args.family,
            max_attempts=args.max_attempts,
            dry_run=False,
        )
        print(f"\n{report.line()}")
        print(report.quality_line())
        _print_status(store)
        return 0 if report.needs_human == 0 else 2
    finally:
        adapter.teardown()
        lock.release()
        store.close()


def _rebuild_ledger(store: Store, interface: str) -> list:
    """Every boundary the live source has ever declared, rebuilt from raw.

    Backfill does NOT reuse the persisted ledger, and does not accumulate in
    corpus order either. Both were tried; both make a stored verdict depend on
    when it happened to be computed. The first backfill judged early answers
    against an empty ledger and the second judged them against a full one --
    same code, same raw, different verdicts.

    A stored judgment has to be reproducible from raw alone, so it is made
    against everything the source has ever said it cannot do. Position in the
    corpus is not evidence: once the source has admitted it cannot see the
    cohort, that is true of the answer on page one as well.

    Live acquisition is the opposite case and keeps the accumulating ledger --
    there, the system genuinely does not know yet.
    """
    from .boundary import detect_boundaries

    ledger: list = []
    seen: set[str] = set()
    rows = store.con.execute(
        "SELECT r.raw_digest FROM response r JOIN prompt p "
        "ON p.prompt_id = r.prompt_id WHERE r.source = ? ORDER BY p.ordinal",
        (interface,),
    ).fetchall()
    for r in rows:
        for b in detect_boundaries(store.vault.get(r["raw_digest"], "response")):
            if b.boundary_id not in seen:
                seen.add(b.boundary_id)
                ledger.append(b)
    return ledger


def cmd_assess_backfill(args) -> int:
    """Judge answers already on disk. Reads raw; never writes it."""
    from dataclasses import replace

    from .classifier import assess
    from .expectation import CLASSIFIER_VERSION

    cfg = _load_config()
    store = _open(cfg)
    interface = args.interface or cfg.get("default_interface") or "eva"
    try:
        rows = store.unassessed_responses(CLASSIFIER_VERSION)
        if not rows:
            print(f"nothing to assess at {CLASSIFIER_VERSION}")
            _print_quality(store, interface)
            return 0

        print(f"assessing {len(rows)} response(s) at {CLASSIFIER_VERSION}")
        ledger = _rebuild_ledger(store, interface)
        print(f"  ledger rebuilt from raw: {len(ledger)} declaration(s)")
        seen = {b.boundary_id for b in ledger}
        written = 0

        for r in rows:
            answer = store.vault.get(r["raw_digest"], "response")
            a = assess(
                prompt_id=r["prompt_id"], response_id=r["response_id"],
                prompt_text=r["raw_prompt"], answer_text=answer,
                family=r["family"], known_boundaries=ledger,
            )

            # A boundary is a fact about what the LIVE source said. Answers
            # imported from the corpus document were never captured by this
            # system -- their provenance is a file, not a session -- so they
            # are judged but are not allowed to teach the ledger.
            live = r["source"] == interface
            if not live:
                a = replace(a, boundaries=())

            if store.record_assessment(a, interface=interface):
                written += 1
            for b in a.boundaries:
                if b.boundary_id not in seen:
                    seen.add(b.boundary_id)
                    ledger.append(b)

            if args.verbose:
                print(f"  {r['external_id']:>10} {a.expected.value:<11} "
                      f"{a.epistemic:<10} {a.disposition.value}")

        print(f"\nassessed {written} response(s)")
        _print_quality(store, interface)
    finally:
        store.close()
    return 0


def _print_quality(store: Store, interface: str) -> None:
    s = store.assessment_stats(interface)
    print("\n-- assessment --")
    print(f"  classifier    {s['classifier_version']}")
    print(f"  assessed      {s['assessed']:>6}")
    print(f"  context-bound {s['context_bound']:>6}")
    print(f"  route to expert {s['route_to_expert']:>4}   "
          f"(questions this source has declared it cannot satisfy)")
    for label, key in (("by disposition", "by_disposition"),
                       ("by epistemic", "by_epistemic"),
                       ("by question type", "by_expected")):
        if not s[key]:
            continue
        print(f"  {label}:")
        for k, n in sorted(s[key].items(), key=lambda kv: -kv[1]):
            print(f"    {k:<20} {n:>6}")
    if s["boundaries"]:
        print(f"\n  what '{interface}' has said it cannot do:")
        for b in s["boundaries"]:
            scope = " ".join(b["scope_text"].split())[:96]
            mark = "cohort" if b["cohort_scoped"] else "narrow"
            print(f"    [{b['kind']:<11} {mark} x{b['times_seen']}] {scope}")


def cmd_quality(args) -> int:
    cfg = _load_config()
    store = _open(cfg)
    interface = args.interface or cfg.get("default_interface") or "eva"
    try:
        _print_quality(store, interface)
        if args.disposition:
            # Scoped to one classifier version, like the summary above it.
            # Without this, a prompt appears once per version ever run and the
            # listing reads as three separate findings about the same answer.
            version = store.latest_classifier_version()
            rows = store.con.execute(
                "SELECT p.external_id, a.epistemic, a.route_to_expert, "
                "       a.followups "
                "FROM assessment a JOIN prompt p ON p.prompt_id=a.prompt_id "
                "WHERE a.disposition=? AND a.classifier_version=? "
                "ORDER BY p.ordinal LIMIT ?",
                (args.disposition, version, args.limit),
            ).fetchall()
            print(f"\n-- {args.disposition} ({version}) --")
            for r in rows:
                route = " ->expert" if r["route_to_expert"] else ""
                print(f"  {r['external_id']:>10} {r['epistemic']}{route}")
                for f in json.loads(r["followups"]):
                    print(f"      follow-up: {f[:110]}")
    finally:
        store.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="knowledge_acquisition")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="load corpora into the registry")
    p.add_argument("--corpus", help="only this corpus_id")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("status", help="counts by state and corpus")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("next", help="show what would be claimed next")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("search", help="full-text search over prompts")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("history", help="audit trail for one prompt")
    p.add_argument("prompt_id")
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("recover", help="expire dead leases, requeue failures")
    p.add_argument("--max-attempts", type=int, default=3)
    p.set_defaults(func=cmd_recover)

    p = sub.add_parser("verify", help="re-hash every raw artifact")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("session-bootstrap",
                       help="open a real window so the Owner can log in")
    p.add_argument("--interface")
    p.add_argument("--timeout", type=int, default=540)
    p.set_defaults(func=cmd_session_bootstrap)

    p = sub.add_parser("session-probe",
                       help="check the session is still authenticated")
    p.add_argument("--interface")
    p.add_argument("--headed", action="store_true",
                   help="watch the probe in a visible window")
    p.set_defaults(func=cmd_session_probe)

    p = sub.add_parser("session-status", help="show session state")
    p.add_argument("--interface")
    p.set_defaults(func=cmd_session_status)

    p = sub.add_parser("run", help="acquire answers for pending prompts")
    p.add_argument("--limit", type=int, help="stop after N prompts")
    p.add_argument("--corpus", help="restrict to one corpus_id")
    p.add_argument("--family", help="restrict to one family")
    p.add_argument("--interface")
    p.add_argument("--pacing", type=float, default=6.0,
                   help="seconds between prompts")
    p.add_argument("--max-attempts", type=int, default=3)
    p.add_argument("--headed", action="store_true",
                   help="watch the run in a visible window")
    p.add_argument("--dry-run", action="store_true",
                   help="show what would be asked; sends nothing")
    p.add_argument("--steal-lock", action="store_true",
                   help="clear a profile lock left by a run that was killed")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("assess-backfill",
                       help="judge answers already captured; reads raw, never writes it")
    p.add_argument("--interface")
    p.add_argument("--verbose", action="store_true",
                   help="one line per answer as it is judged")
    p.set_defaults(func=cmd_assess_backfill)

    p = sub.add_parser("quality",
                       help="what the source can answer, and what it has declared it cannot")
    p.add_argument("--interface")
    p.add_argument("--disposition",
                   help="list the prompts with this disposition and their follow-ups")
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(func=cmd_quality)

    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
