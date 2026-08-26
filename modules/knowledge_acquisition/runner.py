"""The acquisition loop: claim -> ask -> persist -> transition.

Crash safety comes from ordering, not from cleanup. Each iteration:

  1. claim_next()          job moves PENDING -> RUNNING inside one transaction
  2. adapter.ask()         the only slow, failure-prone step
  3. record_response()     RAW lands on disk BEFORE the database row
  4. transition()          RUNNING -> COMPLETE / FAILED / NEEDS_HUMAN

A kill at any point leaves a RUNNING job with an unrenewed lease, which
`recover_expired_leases()` returns to PENDING. A kill between 3 and 4 leaves
the answer safely on disk; the retry re-captures it, the content hash matches,
and the row is not duplicated. Verified by real process kills, not simulation.

Pacing is deliberately conservative and sequential. This is someone's paid
account, not a load target: one prompt at a time, with a delay between them,
and a hard stop on any sign of a rate limit or access control.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .eva_adapter import ADAPTER_VERSION, AdapterError, EvaAdapter
from .models import ConversationMode, IntegrityVerdict, JobState
from .store import Store

#: Seconds between prompts. Politeness, not throughput tuning.
DEFAULT_PACING_S = 6.0
#: Consecutive failures before the whole run stops. A repeated failure is a
#: broken assumption, and burning 2,178 prompts against it helps nobody.
CONSECUTIVE_FAILURE_LIMIT = 3


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

    def line(self) -> str:
        return (f"attempted={self.attempted} completed={self.completed} "
                f"failed={self.failed} needs_human={self.needs_human} "
                f"({self.elapsed_s:.0f}s) -- {self.stopped_reason}")


class AcquisitionRunner:
    def __init__(
        self,
        store: Store,
        adapter: EvaAdapter,
        *,
        pacing_s: float = DEFAULT_PACING_S,
        worker: str = "runner",
        lock=None,
    ) -> None:
        self.store = store
        self.adapter = adapter
        self.pacing_s = pacing_s
        self.worker = worker
        #: Optional ProfileLock. Refreshed each iteration so a live run is not
        #: mistaken for an abandoned one, and so a crash releases it by lapse.
        self.lock = lock
        self._current_family: str | None = None

    def run(
        self,
        *,
        limit: int | None = None,
        corpus_id: str | None = None,
        family: str | None = None,
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
                + "ORDER BY p.priority ASC, p.ordinal ASC LIMIT ?",
                [v for v in (corpus_id, family) if v] + [limit or 20],
            ).fetchall()
            for r in rows:
                report.attempted += 1
                print(f"  [{r['corpus_id']}] {r['external_id']} would ask: "
                      f"{r['raw_prompt'][:78]}")
            report.stopped_reason = "dry run -- nothing sent, nothing claimed"
            report.elapsed_s = time.time() - t0
            return report

        consecutive_failures = 0

        while limit is None or report.attempted < limit:
            job = self.store.claim_next(
                self.worker, lease_seconds=lease_seconds,
                corpus_id=corpus_id, family=family, max_attempts=max_attempts,
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
            digest = self.store.record_response(
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

            print(f"  {label} {status} {len(captured.text)}ch "
                  f"{captured.elapsed_s}s paired={captured.paired} "
                  f"raw={digest[:12]}")
            report.per_prompt.append({
                "external_id": job.external_id, "status": status,
                "chars": len(captured.text), "elapsed_s": captured.elapsed_s,
                "paired": captured.paired, "digest": digest,
            })

            time.sleep(self.pacing_s)
        else:
            report.stopped_reason = f"reached limit of {limit}"

        report.elapsed_s = time.time() - t0
        return report

    def _prepare_conversation(self, job) -> None:
        """Honour the conversation model, so context bleed is a decision."""
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


__all__ = ["AcquisitionRunner", "RunReport", "DEFAULT_PACING_S"]
