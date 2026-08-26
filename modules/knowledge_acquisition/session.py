"""Authenticated browser session lifecycle for a private, paid account.

WHY NOT REUSE `sleepless_qa.dumpers.web.WebDumper`
--------------------------------------------------
It calls `new_context()` with no stored auth state and hardcodes `headless=True`,
so it cannot hold a login. It also writes evidence to `tempfile.mkdtemp()` and
relaunches Chromium per action -- fine for a one-shot QA probe, wrong for 2,178
prompts against an account that would have to re-authenticate every time.

SESSION MODEL
-------------
A persistent Chromium profile directory, not an exported auth-state blob. The
profile is what the browser itself treats as durable, so there is no moment
where the session "has been captured" or "has not yet been captured" -- the
login is simply already there on the next launch. That removes the timing
coordination an export needs, which is the part that breaks when a human is in
the loop.

SECURITY
--------
The profile holds live session cookies. It lives under a directory this module
git-ignores, is never parsed by any code here, and is never logged. Nothing in
this file prints a cookie, a token, or a URL query string. No credential ever
enters source or configuration.

ACCESS CONTROLS
---------------
When the interface presents a login wall, a challenge, or a block page, this
module reports it and stops. It does not attempt to solve, bypass, or disguise
any of them. That is a hard boundary, not a current limitation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .models import utc_now


class SessionState(str, Enum):
    ABSENT = "ABSENT"            # never bootstrapped
    READY = "READY"              # profile present and believed authenticated
    NEEDS_HUMAN = "NEEDS_HUMAN"  # login wall / challenge observed


class SessionError(Exception):
    """Raised on a genuine session failure. Never swallowed."""


@dataclass(frozen=True)
class ProbeResult:
    state: SessionState
    url: str
    title: str
    reason: str
    snapshot_path: Path | None = None


#: Substrings that indicate an unauthenticated or challenged page. Deliberately
#: broad: a false NEEDS_HUMAN costs one human glance, a false READY sends 2,178
#: prompts into a login form.
_AUTH_WALL_MARKERS = (
    "log in", "login", "iniciar sesion", "iniciar sesión", "acceder",
    "sign in", "registrarse", "contraseña",
    "captcha", "recaptcha", "cloudflare", "verify you are human",
    "too many requests", "rate limit", "acceso denegado", "forbidden",
)

#: Grab every attribute rather than a fixed list: the adapter is written against
#: whatever this interface actually exposes, and a hardcoded subset would hide
#: the one stable hook that turns out to matter.
_ATTR_JS = "e => Object.fromEntries([...e.attributes].map(a => [a.name, a.value]))"

_INTERACTIVE_SELECTOR = (
    "textarea, input, button, [role=textbox], [role=button], "
    "[contenteditable=true], form"
)


class BrowserSession:
    """Owns the persistent profile directory and its lifecycle."""

    def __init__(self, root: Path, base_url: str) -> None:
        self.root = Path(root).expanduser()
        self.profile_dir = self.root / "profile"
        self.state_file = self.root / "session.json"
        self.snapshot_dir = self.root / "snapshots"
        self.base_url = base_url
        self.root.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._write_gitignore()

    def _write_gitignore(self) -> None:
        """Belt and braces: the profile must never be committable."""
        gi = self.root / ".gitignore"
        if not gi.exists():
            gi.write_text(
                "# Live session cookies for a private paid account.\n"
                "# Never commit any of this.\n"
                "*\n",
                encoding="utf-8",
            )

    # -- state ---------------------------------------------------------------

    def state(self) -> SessionState:
        if not self.profile_dir.exists() or not any(self.profile_dir.iterdir()):
            return SessionState.ABSENT
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                return SessionState(data.get("state", SessionState.READY.value))
            except (json.JSONDecodeError, ValueError):
                return SessionState.READY
        return SessionState.READY

    def _record(self, state: SessionState, reason: str) -> None:
        self.state_file.write_text(
            json.dumps(
                {"state": state.value, "reason": reason, "at": utc_now(),
                 "base_url": self.base_url},
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )

    # -- bootstrap -----------------------------------------------------------

    def bootstrap(self, *, timeout_seconds: int = 540) -> ProbeResult:
        """Open a real window so the Owner can authenticate by hand.

        Returns when the Owner closes the window. Closing is the completion
        signal: it needs no sentinel file, no polling of a DOM this module has
        not seen yet, and no guess about what "logged in" looks like.
        """
        from playwright.sync_api import sync_playwright

        self.profile_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                viewport={"width": 1440, "height": 900},
                args=["--start-maximized"],
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(self.base_url, wait_until="domcontentloaded", timeout=60_000)

            closed = {"v": False}
            ctx.on("close", lambda *_: closed.update(v=True))
            page.on("close", lambda *_: closed.update(v=True))

            waited, step = 0.0, 0.5
            while not closed["v"] and waited < timeout_seconds:
                try:
                    if not ctx.pages:
                        break
                    ctx.pages[0].wait_for_timeout(int(step * 1000))
                except Exception:
                    break  # window went away -- that is the signal, not an error
                waited += step

            try:
                url, title = page.url, page.title()
            except Exception:
                url, title = self.base_url, "(window closed)"

            try:
                ctx.close()
            except Exception:
                pass

        self._record(SessionState.READY, "bootstrapped by Owner")
        return ProbeResult(SessionState.READY, url, title,
                           "profile persisted; verify with probe")

    # -- probe ---------------------------------------------------------------

    def probe(self, *, headless: bool = True, snapshot: bool = True) -> ProbeResult:
        """Open the profile and report whether it is still authenticated.

        Also captures an accessibility-tree snapshot, which is what the adapter
        is built against. Roles and accessible names survive CSS refactors that
        break class-based selectors.
        """
        from playwright.sync_api import sync_playwright

        if self.state() is SessionState.ABSENT:
            raise SessionError("no profile yet -- run bootstrap first")

        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=headless,
                viewport={"width": 1440, "height": 900},
            )
            try:
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                page.goto(self.base_url, wait_until="domcontentloaded",
                          timeout=60_000)
                page.wait_for_timeout(3_000)  # let a SPA settle

                url, title = page.url, page.title()
                body = (page.inner_text("body") or "")[:4000].lower()

                snap_path = self._capture(page) if snapshot else None

                hit = next((m for m in _AUTH_WALL_MARKERS if m in body), None)
                if hit:
                    self._record(SessionState.NEEDS_HUMAN, f"page shows {hit!r}")
                    return ProbeResult(
                        SessionState.NEEDS_HUMAN, url, title,
                        f"auth wall or challenge: page text contains {hit!r}",
                        snap_path,
                    )

                self._record(SessionState.READY, "probe clean")
                return ProbeResult(SessionState.READY, url, title,
                                   "no auth wall detected", snap_path)
            finally:
                try:
                    ctx.close()
                except Exception:
                    pass

    def _capture(self, page) -> Path:
        """Persist what the adapter will be written against."""
        stamp = utc_now().replace(":", "").replace("-", "")[:15]
        out = self.snapshot_dir / f"probe_{stamp}"
        out.mkdir(parents=True, exist_ok=True)

        try:
            page.screenshot(path=str(out / "page.png"), full_page=True)
        except Exception:
            pass

        try:
            (out / "accessibility.json").write_text(
                json.dumps(page.accessibility.snapshot() or {},
                           ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

        try:
            rows = []
            for h in page.query_selector_all(_INTERACTIVE_SELECTOR)[:150]:
                try:
                    rows.append({
                        "tag": h.evaluate("e => e.tagName.toLowerCase()"),
                        "attrs": h.evaluate(_ATTR_JS),
                        "text": (h.inner_text() or "")[:80].strip(),
                        "visible": h.is_visible(),
                    })
                except Exception:
                    continue
            (out / "interactive.json").write_text(
                json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

        try:
            (out / "body.txt").write_text(
                (page.inner_text("body") or "")[:20000], encoding="utf-8"
            )
        except Exception:
            pass

        return out


__all__ = ["BrowserSession", "SessionState", "ProbeResult", "SessionError"]
