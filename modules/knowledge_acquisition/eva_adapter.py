"""EVA (Consultoria.io) knowledge-interface adapter.

Built against the DOM as observed in a live authenticated session on
2026-08-26, not against assumptions. What that observation established:

  * The app is a CROSS-ORIGIN iframe (`chatbot.nexau.es`) inside
    `programas.consultoria.io`. JS traversal of the top document cannot reach
    it and `query_selector_all` on the page returns nothing; only Playwright's
    frame API crosses the boundary. A selector strategy written against the
    top document would have found zero elements forever.
  * The markup carries no `data-*`, no `role=`, and no ARIA on the message
    nodes -- only Tailwind utilities, which are not stable anchors. The two
    genuinely semantic hooks are the custom classes `prose-chat` (one per
    assistant message) and `bg-bubble-light` (one per user message).
  * Typing swaps the `Grabar audio` control for `Enviar`. Enter also sends.
  * There is NO stop/streaming indicator to watch.

THE COMPLETION GATE, AND WHY IT IS NOT A SLEEP
----------------------------------------------
Measured timeline of one real generation: the frame text sat at 308 chars,
UNCHANGED for three consecutive seconds, before any answer streamed in. A
naive "text stopped growing" detector with a 2-3 poll threshold declares
completion inside that window and captures nothing at all -- and the capture
looks successful, because text was present (it was the sidebar and the echoed
prompt).

So stability alone is not the signal. The gate is two-phase:

  Phase 1 -- APPEARANCE: wait until the count of `.prose-chat` nodes exceeds
             what it was before sending. Until an assistant node exists there
             is nothing to be stable about, and the flat window is invisible
             to the gate by construction.
  Phase 2 -- SETTLE: only then, poll that specific node's text until it stops
             growing for N consecutive polls.

Pairing is verified independently: the last user bubble must contain the
prompt actually sent. That is what makes "this response belongs to this
prompt" an assertion rather than an assumption.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from .models import IntegrityVerdict, canonicalize
from .session import _AUTH_WALL_MARKERS, BrowserSession, SessionState

ADAPTER_VERSION = "eva-adapter/1.0.0"

FRAME_HOST = "chatbot.nexau.es"
ASSISTANT_SEL = ".prose-chat"
USER_BUBBLE_SEL = '[class*="bg-bubble-light"]'
SEND_BUTTON_LABEL = "Enviar"
NEW_CHAT_LABEL = "Nuevo Chat"

#: Phase 1 budget. Generous: a slow answer must not be misread as a failure,
#: and a genuinely dead request is caught by the ledger's retry, not by
#: shortening this.
APPEARANCE_TIMEOUT_S = 120
#: Phase 2 budget, measured from first appearance.
SETTLE_TIMEOUT_S = 600
POLL_INTERVAL_S = 1.0
#: Consecutive unchanged polls before a settled node is called finished.
STABLE_POLLS = 5
#: Below this a "successful" capture is not credible for this corpus; the
#: shortest real answer measured in the source document is 1,080 chars, and
#: the shortest observed live answer is well over this floor.
MIN_CREDIBLE_CHARS = 120
#: A response ending mid-sentence is reported TRUNCATED rather than accepted.
_SENTENCE_ENDINGS = (".", "?", "!", ":", ")", "\"", "'", "»", "”")


class AdapterError(Exception):
    """Raised on an unrecoverable adapter failure. Never swallowed."""


@dataclass(frozen=True)
class CapturedResponse:
    text: str
    html: str
    verdict: IntegrityVerdict
    reason: str
    elapsed_s: float
    paired: bool


class EvaAdapter:
    """Drives one long-lived authenticated EVA session across many prompts.

    Deliberately NOT a subclass of `sleepless_qa.dumpers.web.WebDumper`: that
    class opens a fresh context per action with no stored auth and writes to a
    temp dir, which cannot hold a login across 2,178 prompts. It follows the
    same launch/trigger/capture/teardown shape so the two remain conceptually
    interchangeable, without inheriting a lifecycle built for one-shot probes.
    """

    runtime_class = "eva"

    def __init__(self, session: BrowserSession, *, headless: bool = True) -> None:
        self.session = session
        self.headless = headless
        self._pw = None
        self._ctx = None
        self._page = None
        self._frame = None

    # -- lifecycle -----------------------------------------------------------

    def launch(self) -> None:
        """Idempotent: re-calling on a live adapter is a no-op."""
        if self._ctx is not None:
            return
        if self.session.state() is SessionState.ABSENT:
            raise AdapterError("no browser profile -- run session-bootstrap first")

        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._ctx = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(self.session.profile_dir),
            headless=self.headless,
            viewport={"width": 1440, "height": 900},
        )
        self._page = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        self._page.goto(self.session.base_url, wait_until="networkidle",
                        timeout=90_000)
        self._page.wait_for_timeout(5_000)
        self._frame = self._find_frame()
        self._assert_authenticated()

    def _find_frame(self):
        for _ in range(20):
            fr = next((f for f in self._page.frames if FRAME_HOST in f.url), None)
            if fr is not None:
                return fr
            self._page.wait_for_timeout(1_000)
        raise AdapterError(
            f"EVA frame ({FRAME_HOST}) never appeared -- the interface layout "
            f"may have changed, or the page did not load"
        )

    def _assert_authenticated(self) -> None:
        """Positive evidence, not absence of markers.

        An empty page contains no auth-wall markers either, so 'no marker
        found' on a blank document reads as authenticated. Requiring the
        composer to exist makes the check assert something real.
        """
        body = (self._frame.inner_text("body") or "").lower()
        hit = next((m for m in _AUTH_WALL_MARKERS if m in body), None)
        if hit:
            raise AdapterError(f"auth wall or challenge detected: {hit!r}")
        if self._frame.locator("textarea").count() == 0:
            raise AdapterError(
                "composer not found: the session may have expired, or the "
                "interface changed. Re-run session-bootstrap."
            )

    def teardown(self) -> None:
        for closer in (
            lambda: self._ctx and self._ctx.close(),
            lambda: self._pw and self._pw.stop(),
        ):
            try:
                closer()
            except Exception:
                pass
        self._ctx = self._page = self._frame = self._pw = None

    def __enter__(self) -> "EvaAdapter":
        self.launch()
        return self

    def __exit__(self, *exc) -> None:
        self.teardown()

    # -- conversation control ------------------------------------------------

    def new_conversation(self) -> None:
        """Start a clean thread. This is what makes ISOLATED/SECTION real."""
        self._require_live()
        try:
            self._frame.get_by_role("button", name=NEW_CHAT_LABEL).click(timeout=15_000)
            self._page.wait_for_timeout(2_500)
        except Exception as exc:
            raise AdapterError(f"could not start a new conversation: {exc}") from exc

    def _require_live(self) -> None:
        if self._frame is None:
            raise AdapterError("adapter not launched")

    def _assistant_count(self) -> int:
        return self._frame.locator(ASSISTANT_SEL).count()

    # -- the acquisition step ------------------------------------------------

    def ask(self, prompt: str) -> CapturedResponse:
        """Send one prompt and return the captured answer with a verdict."""
        self._require_live()
        if not prompt.strip():
            raise AdapterError("refusing to send an empty prompt")

        before = self._assistant_count()
        t0 = time.time()

        composer = self._frame.locator("textarea").first
        composer.click(timeout=15_000)
        composer.fill(prompt)

        # Prefer the explicit control when it materialises; Enter is the
        # fallback. Both were observed to work.
        try:
            self._frame.get_by_label(SEND_BUTTON_LABEL).click(timeout=5_000)
        except Exception:
            composer.press("Enter")

        node = self._await_appearance(before, t0)
        text, html = self._await_settle(node, t0)
        elapsed = round(time.time() - t0, 1)

        paired = self._verify_pairing(prompt)
        verdict, reason = self._judge(text, paired)
        return CapturedResponse(text, html, verdict, reason, elapsed, paired)

    def _await_appearance(self, before: int, t0: float):
        """Phase 1. Nothing is 'stable' before an assistant node exists."""
        while time.time() - t0 < APPEARANCE_TIMEOUT_S:
            if self._assistant_count() > before:
                return self._frame.locator(ASSISTANT_SEL).nth(before)
            body = (self._frame.inner_text("body") or "").lower()
            hit = next((m for m in _AUTH_WALL_MARKERS if m in body), None)
            if hit:
                raise AdapterError(f"auth wall appeared mid-request: {hit!r}")
            time.sleep(POLL_INTERVAL_S)
        raise AdapterError(
            f"no assistant response appeared within {APPEARANCE_TIMEOUT_S}s"
        )

    def _await_settle(self, node, t0: float) -> tuple[str, str]:
        """Phase 2. Poll only the node we are waiting on."""
        last, stable = -1, 0
        text, html = "", ""
        while time.time() - t0 < SETTLE_TIMEOUT_S:
            try:
                text = node.inner_text(timeout=10_000) or ""
                html = node.inner_html(timeout=10_000) or ""
            except Exception:
                time.sleep(POLL_INTERVAL_S)
                continue
            stable = stable + 1 if len(text) == last else 0
            last = len(text)
            if stable >= STABLE_POLLS:
                return text, html
            time.sleep(POLL_INTERVAL_S)
        # Budget exhausted while still growing: return what exists and let the
        # verdict say so, rather than discarding a partial paid answer.
        return text, html

    def _verify_pairing(self, prompt: str) -> bool:
        """Did the thread actually echo the prompt we just sent?"""
        try:
            bubbles = self._frame.locator(USER_BUBBLE_SEL)
            n = bubbles.count()
            if n == 0:
                return False
            echoed = canonicalize(bubbles.nth(n - 1).inner_text(timeout=10_000) or "")
        except Exception:
            return False
        sent = canonicalize(prompt)
        # The UI may soft-wrap or elide very long prompts, so compare on a
        # generous prefix rather than demanding equality.
        head = sent[:200]
        return head in echoed or echoed[:200] in sent

    @staticmethod
    def _judge(text: str, paired: bool) -> tuple[IntegrityVerdict, str]:
        stripped = text.strip()
        if not stripped:
            return IntegrityVerdict.EMPTY, "assistant node contained no text"
        if not paired:
            return (IntegrityVerdict.STALE,
                    "last user bubble does not match the prompt sent; the "
                    "captured text may belong to a different question")
        if len(stripped) < MIN_CREDIBLE_CHARS:
            return (IntegrityVerdict.TRUNCATED,
                    f"only {len(stripped)} chars, below the {MIN_CREDIBLE_CHARS} "
                    f"floor for a credible answer")
        if not stripped.endswith(_SENTENCE_ENDINGS):
            return (IntegrityVerdict.TRUNCATED,
                    f"ends mid-sentence on {stripped[-40:]!r}")
        return IntegrityVerdict.OK, f"{len(stripped)} chars, paired to its prompt"


__all__ = ["EvaAdapter", "CapturedResponse", "AdapterError", "ADAPTER_VERSION"]
