"""The acquisition loop: claim -> ask -> persist -> transition -> assess.

Crash safety comes from ordering, not from cleanup. Each iteration:

  1. claim_next()          job moves PENDING -> RUNNING inside one transaction
  2. adapter.ask()         the only slow, failure-prone step
  3. record_response()     RAW lands on disk BEFORE the database row
  4. transition()          RUNNING -> COMPLETE / FAILED / NEEDS_HUMAN
  5. assess()              derived judgment, strictly last and fully guarded

A kill at any point leaves a RUNNING job with an unrenewed lease, which
`recover_expired_leases()` returns to PENDING. A kill between 3 and 4 leaves
the answer safely on disk; the retry re-captures it, the content hash matches,
and the row is not duplicated. Verified by real process kills, not simulation.

Step 5 is deliberately after step 4 and wrapped: an assessment is derived data
and must never be able to cost a capture that was already paid for. If the
classifier raises, the answer stays COMPLETE and simply has no assessment --
which `assess-backfill` will pick up later. The failure is printed, never
swallowed.

Pacing is deliberately conservative and sequential. This is someone's paid
account, not a load target: one prompt at a time, with a delay between them,
and a hard stop on any sign of a rate limit or access control.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .classifier import Disposition, assess
from .eva_adapter import ADAPTER_VERSION, AdapterError, EvaAdapter
from .models import ConversationMode, IntegrityVerdict, JobState
from .store import Store

#: Seconds between prompts. Politeness, not throughput tuning.
DEFAULT_PACING_S = 6.0
#: Consecutive failures before the whole run stops. A repeated failure is a
#: broken assumption, and burning 2,178 prompts against it helps nobody.
CONSECUTIVE_FAILURE_LIMIT = 3
#: Consecutive substanceless answers before stopping. The eight measured live
#: answers averaged ~2,560 chars and the shortest was 1,221; a run of five in a
#: row below the substantive floor means the session, the page or the source
#: changed, and continuing would spend hours collecting nothing.
CONSECUTIVE_LOW_VALUE_LIMIT = 5


@dataclass
class RunReport:
    started_at: str
    attempted: int = 0
    completed: int = 0
    failed: int = 0
    needs_human: int = 0
    stopped_reason: str = ""
    elapsed_s: float = 0.0
    per_prompt: list[dict] = field(default_factory=list)
    by_disposition: dict = field(default_factory=dict)
    boundaries_learned: int = 0

    def line(self) -> str:
        return (f"attempted={self.attempted} completed={self.completed} "
                f"failed={self.failed} needs_human={self.needs_human} "
                f"({self.elapsed_s:.0f}s) -- {self.stopped_reason}")

    def quality_line(self) -> str:
        if not self.by_disposition:
            return "  no answers assessed this run"
        parts = " ".join(f"{k}={v}" for k, v in sorted(self.by_disposition.items()))
        return f"  dispositions: {parts}  boundaries_learned={self.boundaries_learned}"


class AcquisitionRunner:
    def __init__(
        self,
        store: Store,
        adapter: EvaAdapter,
        *,
        pacing_s: float = DEFAULT_PACING_S,
        worker: str = "runner",
        lock=None,
        interface: str = "eva",
        assess_answers: bool = True,
    ) -> None:
        self.store = store
        self.adapter = adapter
        self.pacing_s = pacing_s
        self.worker = worker
        #: Optional ProfileLock. Refreshed each iteration so a live run is not
        #: mistaken for an abandoned one, and so a crash releases it by lapse.
        self.lock = lock
        self.interface = interface
        self.assess_answers = assess_answers
        self._current_family: str | None = None
        self._ledger: list = []
        self._ledger_ids: set[str] = set()

    # -- assessment ----------------------------------------------------------

    def _load_ledger(self) -> None:
        """Everything the source has already told us it cannot do."""
        self._ledger = []
        self._ledger_ids = set()
        if not self.assess_answers:
            return
        try:
            for b in self.store.known_boundaries(self.interface):
                self._remember(b)
        except Exception as exc:  # noqa: BLE001
            # A ledger we cannot read costs precision, never a capture: the run
            # proceeds and every claim is judged against an empty history.
            print(f"  boundary ledger unavailable ({exc}); "
                  f"judging without prior boundaries")

    def _remember(self, boundary) -> bool:
        if boundary.boundary_id in self._ledger_ids:
            return False
        self._ledger_ids.add(boundary.boundary_id)
        self._ledger.append(boundary)
        return True

    def _assess_answer(self, job, captured, response_id: str, report: RunReport) -> str:
        """Judge one answer. Derived, guarded, and never load-bearing.

        Only OK captures are judged. An answer the integrity gate would not
        vouch for must not be allowed to write a boundary into the ledger --
        a truncated refusal would record a capability limit the source never
        actually stated.
        """
        if not self.assess_answers or captured.verdict is not IntegrityVerdict.OK:
            return ""
        try:
            a = assess(
                prompt_id=job.prompt_id,
                response_id=response_id,
                prompt_text=job.raw_prompt,
                answer_text=captured.text,
                family=job.family,
                known_boundaries=self._ledger,
            )
            self.store.record_assessment(a, interface=self.interface)
            for b in a.boundaries:
                if self._remember(b):
                    report.boundaries_learned += 1
            key = a.disposition.value
            report.by_disposition[key] = report.by_disposition.get(key, 0) + 1
            return key
        except Exception as exc:  # noqa: BLE001 -- see module docstring, step 5
            # Broad on purpose: no classifier defect may cost an answer that was
            # already captured and paid for. Recorded as unrated and printed, so
            # a judgment layer that is down is visible rather than assumed to
            # have passed.
            print(f"    assessment unavailable ({type(exc).__name__}: {exc})")
            key = Disposition.UNRATED.value
            report.by_disposition[key] = report.by_disposition.get(key, 0) + 1
            return key

    # -- the loop ------------------------------------------------------------

    def run(
        self,
        *,
        limit: int | None = None,
        corpus_id: str | None = None,
        family: str | None = None,
        prompt_ids: list[str] | None = None,
        max_attempts: int = 3,
        lease_seconds: int = 900,
        dry_run: bool = False,
    ) -> RunReport:
        report = RunReport(started_at=datetime.now(timezone.utc).isoformat())
        t0 = time.time()

        # Anything stranded by a previous crash rejoins the work set first.
        recovered = self.store.recover_expired_leases()
        requeued = self.store.requeue_failed(max_attempts=max_attempts)
        if recovered or requeued:
            print(f"  recovery: {recovered} expired lease(s), {requeued} requeued")

        if dry_run:
            # Read-only. Claiming here would inflate attempt counts and, with
            # no limit, re-claim the same prompt forever once it was requeued.
            rows = self.store.con.execute(
                "SELECT p.corpus_id, p.external_id, p.family, p.raw_prompt "
                "FROM job j JOIN prompt p ON p.prompt_id=j.prompt_id "
                "WHERE j.state='PENDING' "
                + ("AND p.corpus_id=? " if corpus_id else "")
                + ("AND p.family=? " if family else "")
                + (f"AND p.prompt_id IN ({','.join('?' * len(prompt_ids))}) "
                   if prompt_ids else "")
                + "ORDER BY p.priority ASC, p.ordinal ASC LIMIT ?",
                [v for v in (corpus_id, family) if v] + list(prompt_ids or [])
                + [limit or 20],
            ).fetchall()
            for r in rows:
                report.attempted += 1
                print(f"  [{r['corpus_id']}] {r['external_id']} would ask: "
                      f"{r['raw_prompt'][:78]}")
            report.stopped_reason = "dry run -- nothing sent, nothing claimed"
            report.elapsed_s = time.time() - t0
            return report

        self._load_ledger()
        if self._ledger:
            print(f"  boundary ledger: {len(self._ledger)} declaration(s) "
                  f"already known for '{self.interface}'")

        consecutive_failures = 0
        consecutive_low_value = 0

        while limit is None or report.attempted < limit:
            job = self.store.claim_next(
                self.worker, lease_seconds=lease_seconds,
                corpus_id=corpus_id, family=family, prompt_ids=prompt_ids,
                max_attempts=max_attempts,
            )
            if job is None:
                report.stopped_reason = "no pending prompts"
                break

            report.attempted += 1
            label = f"[{job.corpus_id}] {job.external_id}"
            if self.lock is not None:
                self.lock.refresh()

            try:
                self._prepare_conversation(job)
                captured = self.adapter.ask(job.raw_prompt)
            except AdapterError as exc:
                consecutive_failures += 1
                report.failed += 1
                fatal = self._is_access_control(exc)
                target = JobState.NEEDS_HUMAN if fatal else JobState.FAILED
                self.store.transition(
                    job.prompt_id, target, reason=str(exc)[:400],
                    actor=self.worker, error_class=type(exc).__name__,
                    error=str(exc)[:2000],
                )
                if fatal:
                    report.needs_human += 1
                    report.stopped_reason = f"access control: {exc}"
                    print(f"  {label} NEEDS_HUMAN -- {exc}")
                    break
                print(f"  {label} FAILED -- {exc}")
                if consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT:
                    report.stopped_reason = (
                        f"{consecutive_failures} consecutive failures -- stopping "
                        f"rather than burning the corpus against a broken assumption"
                    )
                    break
                time.sleep(self.pacing_s)
                continue

            consecutive_failures = 0

            # Raw first, always.
            response_id = self.store.record_response(
                job.prompt_id, captured.text,
                source="eva", source_version=ADAPTER_VERSION,
                verdict=captured.verdict, reason=captured.reason,
            )

            if captured.verdict is IntegrityVerdict.OK:
                self.store.transition(
                    job.prompt_id, JobState.COMPLETE,
                    reason=f"captured {len(captured.text)} chars", actor=self.worker,
                )
                report.completed += 1
                status = "COMPLETE"
            else:
                # The answer is kept -- it was paid for -- but the job does not
                # close on a response the integrity gate would not vouch for.
                self.store.transition(
                    job.prompt_id, JobState.FAILED,
                    reason=f"integrity {captured.verdict.value}: {captured.reason}",
                    actor=self.worker, error_class=captured.verdict.value,
                    error=captured.reason,
                )
                report.failed += 1
                status = captured.verdict.value

            disposition = self._assess_answer(job, captured, response_id, report)

            print(f"  {label} {status} {len(captured.text)}ch "
                  f"{captured.elapsed_s}s paired={captured.paired} "
                  f"{disposition or '-'}")
            report.per_prompt.append({
                "external_id": job.external_id, "status": status,
                "chars": len(captured.text), "elapsed_s": captured.elapsed_s,
                "paired": captured.paired, "response_id": response_id,
                "disposition": disposition,
            })

            if disposition == Disposition.LOW_VALUE.value:
                consecutive_low_value += 1
                if consecutive_low_value >= CONSECUTIVE_LOW_VALUE_LIMIT:
                    report.stopped_reason = (
                        f"{consecutive_low_value} consecutive substanceless "
                        f"answers -- the source or the session changed; stopping "
                        f"rather than spending hours collecting nothing"
                    )
                    break
            else:
                consecutive_low_value = 0

            time.sleep(self.pacing_s)
        else:
            report.stopped_reason = f"reached limit of {limit}"

        report.elapsed_s = time.time() - t0
        return report

    def _prepare_conversation(self, job) -> None:
        """Honour the conversation model, so context bleed is a decision.

        Note the honest limit, measured 2026-08-26: SF30-024 referred to advice
        never given in this run, so the account carries memory across sessions
        that no client-side action can clear. ISOLATED reduces bleed within a
        run; it cannot deliver isolation, and the classifier flags what leaks.
        """
        mode = ConversationMode(job.conversation_mode)
        if mode is ConversationMode.ISOLATED:
            self.adapter.new_conversation()
        elif mode is ConversationMode.SECTION:
            if job.family != self._current_family:
                self.adapter.new_conversation()
                self._current_family = job.family

    @staticmethod
    def _is_access_control(exc: Exception) -> bool:
        """Distinguish 'try again' from 'a human must act'."""
        m = str(exc).lower()
        return any(k in m for k in (
            "auth wall", "challenge", "captcha", "rate limit",
            "too many requests", "session may have expired", "forbidden",
        ))


__all__ = [
    "AcquisitionRunner",
    "RunReport",
    "DEFAULT_PACING_S",
    "CONSECUTIVE_LOW_VALUE_LIMIT",
]
