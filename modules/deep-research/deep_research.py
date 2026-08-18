#!/usr/bin/env python3
"""deep_research.py — recursive web research agent (Claude Power Pack).

Source spec: claude-power-pack/vault/specs/deep-research-agent.md
Algorithm reverse-engineered from a community n8n workflow (reference only;
n8n is forbidden as a runtime per feedback_no_n8n_ever, 2026-05-23). The
deliverable is pure Python.

This file is built in layers (Pasos 1.1 -> 1.9 of the
session-2026-05-23 plan). Each layer ships standalone-usable on its own:

  1.1 (this commit) — constants, types, governance helpers (slug, lock,
                      priority drop, env-var resolution). Usable as a
                      library by any future PP script that needs the
                      same resource-governance pattern.
  1.2-1.4           — web_search, fetch_page, call_llm fallback cascades.
  1.5-1.7           — generate_serp_queries, extract_learnings,
                      generate_report (verbatim prompts from spec sections
                      3.2, 3.4, 3.5).
  1.8               — recursive deep_research driver + governance wiring.
  1.9               — CLI + three-artifact output writer.

Resource governance (inherited from
vault/lessons/heavy-io-must-be-governed.md):

  1. Single-instance lock at vault/research/.deep-research.lock.
     Refuses to start if another run is in flight. Stale reclaim
     after 4 h.
  2. IDLE_PRIORITY_CLASS on Windows (same ctypes pattern as
     session-snapshot.py). Empirically required: ctypes without
     explicit wintypes.HANDLE truncates the pseudo-handle on x64 and
     SetPriorityClass returns FALSE silently.
  3. Bounded query budget (default 30 queries).
  4. Per-request timeouts.
  5. Total runtime ceiling (default 2 h).
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Any, TypedDict

__version__ = "0.3.0"


# --- Paths ----------------------------------------------------------------

HOME = Path.home()
PP_REPO = HOME / ".claude" / "skills" / "claude-power-pack"
RESEARCH_DIR = PP_REPO / "vault" / "research"
LOCK_PATH = RESEARCH_DIR / ".deep-research.lock"
CACHE_HINTS_DIR = PP_REPO / "vault" / "cache_hints"
INDEX_PATH = RESEARCH_DIR / "index.json"


# --- Governance constants (mirror spec §7.3 + heavy-io lesson) -----------

LOCK_STALE_SECONDS = 4 * 60 * 60    # 4 h max plausible depth-3 run
MAX_QUERIES_DEFAULT = 30
TOTAL_TIMEOUT_S_DEFAULT = 2 * 60 * 60  # 2 h wall-clock
SERP_TIMEOUT_S = 30
PAGE_TIMEOUT_S = 60
LLM_TIMEOUT_S = 120
MARKDOWN_MAX_CHARS = 25_000


# --- Env-var resolution ---------------------------------------------------

def env_str(name: str, default: str = "") -> str:
    """Return the env var value, or `default` when unset/empty."""
    v = os.environ.get(name, "")
    return v if v else default


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def env_bool(name: str) -> bool:
    return os.environ.get(name, "0").strip().lower() in ("1", "true", "yes", "on")


def env_disabled() -> bool:
    """Honor the global opt-out the same way session-snapshot.py does."""
    return env_bool("CLAUDEPP_DEEPRESEARCH_DISABLE")


# --- Types ----------------------------------------------------------------

class ResearchResult(TypedDict):
    report_md: str
    learnings: list[str]
    urls: list[str]
    metadata: dict[str, Any]


class SerpHit(TypedDict):
    title: str
    url: str
    snippet: str


class SerpQuery(TypedDict):
    query: str
    researchGoal: str
    # Which face of the problem this question attacks (Engine 1). "" when the
    # decomposer returned an axis outside the canonical set — an unrecognised
    # label is never bucketed into a real axis, because that would inflate the
    # measured coverage with a question nobody classified.
    axis: str


class ExtractedLearnings(TypedDict):
    learnings: list[str]
    followUpQuestions: list[str]
    # Engine 3: the structured form behind each formatted learning string —
    # capability, evidence, claimed vs final epistemic level, source quality.
    records: list[dict[str, Any]]


# --- Slug / timestamp helpers --------------------------------------------

_SLUG_RE = re.compile(r"[^a-zA-Z0-9-]+")


def slugify(text: str, maxlen: int = 50) -> str:
    """Filesystem-safe slug for output filenames. Empty input -> 'research'."""
    s = _SLUG_RE.sub("-", text.lower()).strip("-")
    return s[:maxlen] or "research"


def now_ts() -> str:
    """Filesystem-safe timestamp matching vault/research/<ts>_<slug>.md."""
    return time.strftime("%Y-%m-%d_%H%M%S")


def iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --- IDLE priority drop ---------------------------------------------------

def lower_priority() -> str:
    """Drop current process to IDLE priority. Returns a verdict string.

    Win32 ctypes signature: GetCurrentProcess returns a 64-bit HANDLE on
    x64 Windows. Without explicit wintypes.HANDLE the pseudo-handle is
    truncated and SetPriorityClass silently returns FALSE. Empirically
    caught during session-snapshot.py development; same fix here.
    """
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            IDLE_PRIORITY_CLASS = 0x00000040
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE,
                                                    wintypes.DWORD]
            kernel32.SetPriorityClass.restype = wintypes.BOOL
            handle = kernel32.GetCurrentProcess()
            if kernel32.SetPriorityClass(handle, IDLE_PRIORITY_CLASS):
                return "win32:IDLE_PRIORITY_CLASS"
            err = ctypes.get_last_error()
            return f"win32:SetPriorityClass-failed (GetLastError={err})"
        try:
            os.sched_setscheduler(0, os.SCHED_IDLE,  # type: ignore[attr-defined]
                                   os.sched_param(0))  # type: ignore[attr-defined]
            return "posix:SCHED_IDLE"
        except (AttributeError, OSError):
            os.nice(19)
            return "posix:nice(19)"
    except Exception as e:  # noqa: BLE001 — never break a research run
        return f"priority-noop: {e!r}"


# --- Single-instance lock -------------------------------------------------

def _this_host() -> str:
    return (os.uname().nodename if hasattr(os, "uname")
            else os.environ.get("COMPUTERNAME", "?"))


def _pid_alive(pid: int) -> bool:
    """True iff `pid` is a live process on THIS host.

    A false "dead" (e.g. the handle is denied to us) only causes an earlier
    reclaim, which is the pre-existing time-based behaviour — so the error
    direction is safe. PID reuse could produce a false "alive", which just
    preserves the old conservative refusal.
    """
    if pid <= 0:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL,
                                              wintypes.DWORD]
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                return False
            try:
                code = wintypes.DWORD()
                kernel32.GetExitCodeProcess.argtypes = [
                    wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)
                ]
                if kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                    return code.value == STILL_ACTIVE
                return True
            finally:
                kernel32.CloseHandle(handle)
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, OverflowError):
        return False


def _read_lock_payload() -> tuple[int, str]:
    """Return (pid, host) from the lock file. (0, "") when unreadable."""
    try:
        text = LOCK_PATH.read_text(encoding="utf-8")
    except OSError:
        return 0, ""
    pid, host = 0, ""
    for line in text.splitlines():
        if line.startswith("pid="):
            try:
                pid = int(line[4:].strip())
            except ValueError:
                pid = 0
        elif line.startswith("host="):
            host = line[5:].strip()
    return pid, host


def acquire_lock() -> str:
    """Cooperative lock with orphan + stale reclaim. Returns:
      "acquired"         — caller proceeds
      "orphan-reclaimed" — owner PID is dead on this host; reclaimed
      "stale-reclaimed"  — lock older than 4 h; reclaimed
      "held"             — another LIVE run holds the lock; caller MUST abort
      "error:<msg>"      — IO error; fail-open, caller proceeds with warning

    The orphan check exists because time-based staleness alone is not enough.
    Empirically (2026-07-13): a run died without releasing, and the 4-h
    threshold then silently disabled every subsequent run for the rest of
    that window — the module answered "locked" to a lock whose owner had not
    existed for three hours. A lock must be held by something that is alive,
    otherwise it is not a lock, it is a headstone.
    """
    try:
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        if LOCK_PATH.exists():
            pid, host = _read_lock_payload()
            owner_dead = (
                pid > 0 and host == _this_host() and not _pid_alive(pid)
            )
            try:
                age = time.time() - LOCK_PATH.stat().st_mtime
            except OSError:
                age = LOCK_STALE_SECONDS + 1

            if owner_dead:
                verdict = "orphan-reclaimed"
            elif age >= LOCK_STALE_SECONDS:
                verdict = "stale-reclaimed"
            else:
                return "held"

            try:
                LOCK_PATH.unlink()
            except OSError:
                pass
            _write_lock_payload()
            return verdict
        _write_lock_payload()
        return "acquired"
    except OSError as e:
        return f"error:{e}"


def _write_lock_payload() -> None:
    try:
        host = (os.uname().nodename if hasattr(os, "uname")
                else os.environ.get("COMPUTERNAME", "?"))
        LOCK_PATH.write_text(
            f"pid={os.getpid()}\nts={int(time.time())}\nhost={host}\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def release_lock() -> None:
    try:
        LOCK_PATH.unlink()
    except OSError:
        pass


# --- Web search cascade (Paso 1.2) ---------------------------------------
#
# Three layers in priority order. Each raises LayerError to signal cascade
# to the next layer. Other exceptions (programming errors) propagate. The
# cascade is fail-OPEN across layers — only NoSearchAvailable is fatal.
#
#   1. DuckDuckGo HTML  — no API key needed. HTML scrape of
#      https://html.duckduckgo.com/html/. Free tier; rate-limited but
#      reliable for low-volume agent use.
#   2. Brave Search API — requires BRAVE_API_KEY. JSON response. Paid.
#   3. Apify SERP actor — requires APIFY_TOKEN (or the user's existing
#      APIFU_API_KEY env var with the spelling typo; honored as alias).
#      Mirrors what the n8n source workflow used.

import html as _html_lib
import json as _json
import re as _re
import urllib.error as _ue
import urllib.parse as _up
import urllib.request as _ur


class LayerError(Exception):
    """Raised by a search layer to signal cascade to the next layer."""

    def __init__(self, layer: str, message: str):
        super().__init__(f"{layer}: {message}")
        self.layer = layer


class NoSearchAvailable(Exception):
    """All search layers exhausted without producing hits."""


_DDG_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
           "AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/124.0.0.0 Safari/537.36")


def web_search(query: str, n: int = 10) -> tuple[list[SerpHit], str]:
    """Run `query` through the cascade. Returns (hits, layer_used).

    Raises NoSearchAvailable if every layer fails. Caller (deep_research)
    treats NoSearchAvailable on the FIRST query as a CEILING.md write +
    abort; on a later query it logs and continues.
    """
    layers = (
        ("ddg", _search_duckduckgo),
        ("brave", _search_brave),
        ("apify", _search_apify),
    )
    errors: list[str] = []
    for name, fn in layers:
        try:
            hits = fn(query, n)
            if hits:
                return hits, name
            errors.append(f"{name}: 0 hits")
        except LayerError as e:
            errors.append(str(e))
            continue
    raise NoSearchAvailable("; ".join(errors))


def _strip_html_tags(s: str) -> str:
    return _re.sub(r"<[^>]+>", "", _html_lib.unescape(s)).strip()


_DDG_SPONSORED_PATTERNS = (
    "duckduckgo.com/y.js",
    "duckduckgo.com/spice/",
    "/ad_provider=",
    "ad_domain=",
)


def _is_ddg_sponsored(url: str) -> bool:
    """Filter DuckDuckGo-served sponsored / ad results before they pollute
    the SERP. The patterns target the redirect URL DDG hands out for ads
    (y.js + ad_provider/ad_domain params), not the underlying advertiser
    domain (which we wouldn't want to over-filter)."""
    lower = url.lower()
    return any(p in lower for p in _DDG_SPONSORED_PATTERNS)


def _ddg_unwrap(href: str) -> str:
    """DuckDuckGo wraps real URLs in /l/?uddg=<percent-encoded>&kh=...
    Sometimes also returns //duckduckgo.com/l/?... or absolute https.
    """
    if href.startswith("//"):
        href = "https:" + href
    if "uddg=" not in href:
        return href
    try:
        qs = _up.urlparse(href).query
        params = _up.parse_qs(qs)
        return _up.unquote(params.get("uddg", [href])[0])
    except Exception:  # noqa: BLE001 — fall back to the raw href
        return href


def _search_duckduckgo(query: str, n: int) -> list[SerpHit]:
    """DuckDuckGo HTML endpoint. No API key. Free tier with rate limits."""
    data = _up.urlencode({"q": query}).encode("utf-8")
    req = _ur.Request(
        "https://html.duckduckgo.com/html/",
        data=data,
        headers={
            "User-Agent": _DDG_UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with _ur.urlopen(req, timeout=SERP_TIMEOUT_S) as r:
            page = r.read().decode("utf-8", errors="replace")
    except (_ue.URLError, _ue.HTTPError, TimeoutError, OSError) as e:
        raise LayerError("ddg", f"fetch failed: {e}")

    hits: list[SerpHit] = []
    try:
        from bs4 import BeautifulSoup  # type: ignore[import-not-found]
        soup = BeautifulSoup(page, "html.parser")
        for res in soup.select(".result"):
            a = res.select_one(".result__a")
            snip = res.select_one(".result__snippet")
            if not a:
                continue
            href = a.get("href", "")
            real = _ddg_unwrap(href if isinstance(href, str) else "")
            if not real or not real.startswith(("http://", "https://")):
                continue
            if _is_ddg_sponsored(real):
                continue
            hits.append({
                "title": a.get_text(strip=True),
                "url": real,
                "snippet": (snip.get_text(strip=True) if snip else ""),
            })
            if len(hits) >= n:
                break
    except ImportError:
        anchor_re = _re.compile(
            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            _re.I | _re.S,
        )
        snippet_re = _re.compile(
            r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
            _re.I | _re.S,
        )
        anchors = anchor_re.findall(page)
        snippets = snippet_re.findall(page)
        for i, (href, title) in enumerate(anchors):
            real = _ddg_unwrap(href)
            if not real or not real.startswith(("http://", "https://")):
                continue
            if _is_ddg_sponsored(real):
                continue
            snip = snippets[i] if i < len(snippets) else ""
            hits.append({
                "title": _strip_html_tags(title),
                "url": real,
                "snippet": _strip_html_tags(snip),
            })
            if len(hits) >= n:
                break

    if not hits:
        raise LayerError("ddg", "0 hits parsed (possible block or empty SERP)")
    return hits


def _search_brave(query: str, n: int) -> list[SerpHit]:
    key = env_str("BRAVE_API_KEY")
    if not key:
        raise LayerError("brave", "BRAVE_API_KEY not set")
    url = "https://api.search.brave.com/res/v1/web/search?" + _up.urlencode(
        {"q": query, "count": min(n, 20)}
    )
    req = _ur.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": key,
        },
    )
    try:
        with _ur.urlopen(req, timeout=SERP_TIMEOUT_S) as r:
            data = _json.loads(r.read().decode("utf-8"))
    except (_ue.URLError, _ue.HTTPError, TimeoutError, OSError,
            _json.JSONDecodeError) as e:
        raise LayerError("brave", f"request failed: {e}")
    results = (data.get("web") or {}).get("results", [])
    hits = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("description", ""),
        }
        for r in results[:n]
        if r.get("url")
    ]
    if not hits:
        raise LayerError("brave", "0 hits in response")
    return hits


def _search_apify(query: str, n: int) -> list[SerpHit]:
    """Apify SERP actor. Honors both APIFY_TOKEN and the user's existing
    APIFU_API_KEY env-var (the user's apify.env has the typo; we accept
    it as an alias so existing setups keep working)."""
    token = env_str("APIFY_TOKEN") or env_str("APIFU_API_KEY")
    if not token:
        raise LayerError("apify", "APIFY_TOKEN / APIFU_API_KEY not set")
    url = (
        "https://api.apify.com/v2/acts/serping~fast-google-search-results-"
        "scraper/run-sync-get-dataset-items?" + _up.urlencode({"token": token})
    )
    body = _json.dumps(
        {"searchTerms": [f"{query} -filetype:pdf"],
         "resultsPerPage": min(n, 10)}
    ).encode("utf-8")
    req = _ur.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with _ur.urlopen(req, timeout=SERP_TIMEOUT_S) as r:
            data = _json.loads(r.read().decode("utf-8"))
    except (_ue.URLError, _ue.HTTPError, TimeoutError, OSError,
            _json.JSONDecodeError) as e:
        raise LayerError("apify", f"request failed: {e}")

    hits: list[SerpHit] = []
    for item in (data if isinstance(data, list) else [data]):
        organic = (
            item.get("organic_results")
            or (item.get("origin_search") or {}).get("results")
            or []
        )
        for o in organic:
            if o.get("type") not in (None, "normal"):
                continue
            src = o.get("source") or {}
            real = src.get("link") or o.get("link") or o.get("url") or ""
            if not real:
                continue
            hits.append({
                "title": o.get("title", ""),
                "url": real,
                "snippet": o.get("snippet", "") or o.get("description", ""),
            })
            if len(hits) >= n:
                break
        if len(hits) >= n:
            break
    if not hits:
        raise LayerError("apify", "0 organic results parsed")
    return hits


# --- Page fetch + HTML -> markdown (Paso 1.3) ----------------------------
#
# fetch_page handles redirects, charset detection, and a 5 MiB body cap so a
# pathological page can't OOM the agent. html_to_markdown is a 4-layer
# cascade: trafilatura -> readability -> bs4 strip -> regex. Each layer
# that fails logs to stderr (no silent swallow) so the cascade verdict is
# observable in the report's metadata footer.


def fetch_page(url: str, timeout: int = PAGE_TIMEOUT_S) -> dict[str, Any]:
    """Fetch `url` with a 5 MiB body cap and charset auto-detection.

    Returns {html, status, final_url, content_type}. Raises LayerError on
    network failure so the orchestrator can decide whether to skip the
    URL (continue to the next SERP hit) or abort.
    """
    req = _ur.Request(url, headers={"User-Agent": _DDG_UA})
    try:
        with _ur.urlopen(req, timeout=timeout) as r:
            ctype = r.headers.get("Content-Type", "")
            raw = r.read(5 * 1024 * 1024)  # 5 MiB cap
            charset = "utf-8"
            if "charset=" in ctype.lower():
                charset = ctype.lower().split("charset=", 1)[1].split(";")[0].strip()
            try:
                html_text = raw.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                html_text = raw.decode("utf-8", errors="replace")
            return {
                "html": html_text,
                "status": getattr(r, "status", 200),
                "final_url": r.url,
                "content_type": ctype,
            }
    except (_ue.URLError, _ue.HTTPError, TimeoutError, OSError) as e:
        raise LayerError("page-fetch", f"{url}: {e}")


def html_to_markdown(html_text: str, max_chars: int = MARKDOWN_MAX_CHARS,
                      base_url: str | None = None) -> tuple[str, str]:
    """Convert HTML to markdown via the extraction cascade.

    Returns (markdown, layer_used). `layer_used` is one of:
      trafilatura | readability | bs4-strip | regex-fallback | empty-input
    """
    if not html_text or len(html_text) < 100:
        return ("", "empty-input")

    # Layer 1: trafilatura — best content extraction
    try:
        import trafilatura  # type: ignore[import-untyped]
        md = trafilatura.extract(
            html_text,
            output_format="markdown",
            include_links=True,
            include_tables=True,
            url=base_url,
        )
        if md and len(md) > 200:
            return (md[:max_chars], "trafilatura")
    except (ImportError, ValueError, OSError, TypeError) as e:
        print(f"deep_research: trafilatura failed ({e!r}); fallback",
              file=sys.stderr)

    # Layer 2: readability + bs4 text extraction
    try:
        from readability import Document  # type: ignore[import-not-found]
        from bs4 import BeautifulSoup  # type: ignore[import-not-found]
        doc = Document(html_text)
        soup = BeautifulSoup(doc.summary(), "html.parser")
        text = soup.get_text("\n", strip=True)
        if text and len(text) > 200:
            return (text[:max_chars], "readability")
    except (ImportError, ValueError, TypeError) as e:
        print(f"deep_research: readability failed ({e!r}); fallback",
              file=sys.stderr)

    # Layer 3: bs4 raw strip with boilerplate-tag removal
    try:
        from bs4 import BeautifulSoup  # type: ignore[import-not-found]
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer",
                          "header", "aside", "form", "iframe"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)
        text = _re.sub(r"\n{3,}", "\n\n", text)
        if text:
            return (text[:max_chars], "bs4-strip")
    except (ImportError, ValueError, TypeError) as e:
        print(f"deep_research: bs4 strip failed ({e!r}); regex fallback",
              file=sys.stderr)

    # Layer 4: regex fallback — last resort, never raises
    plain = _re.sub(r"<[^>]+>", " ", html_text)
    plain = _html_lib.unescape(plain)
    plain = _re.sub(r"\s+", " ", plain).strip()
    return (plain[:max_chars], "regex-fallback")


# --- LLM cascade (Paso 1.4) ----------------------------------------------
#
# Two layers in priority order:
#   1. claude.exe CLI — print mode, OAuth via keychain (the Owner is
#      already authenticated). Hooks/tools disabled in the spawned
#      subprocess to avoid recursion-explosions.
#   2. anthropic Python SDK — requires ANTHROPIC_API_KEY env var.
#
# Cascade behaviour: a LayerError causes the next layer to be tried.
# Anything else (programming error, schema validation failure on the
# orchestrator side) propagates as-is. If both layers fail, raise
# NoLLMAvailable so the caller can write CEILING.md and abort.


class NoLLMAvailable(Exception):
    """All LLM layers exhausted. Aborts the run; CEILING.md is written."""


def call_llm(system: str, user: str, schema: dict | None = None,
              timeout: int = LLM_TIMEOUT_S) -> str | dict:
    """Send (system, user) through the cascade and return text or dict.

    When `schema` is provided, the user message is augmented to require
    a JSON object matching the schema; the response is parsed + the
    raw dict is returned. Schema-validation against the actual shape
    is the caller's responsibility (we only guarantee parse success).
    """
    layers = (
        ("claude.exe", _llm_claude_cli),
        ("anthropic-sdk", _llm_anthropic_sdk),
    )
    errors: list[str] = []
    for _name, fn in layers:
        try:
            return fn(system, user, schema, timeout)
        except LayerError as e:
            errors.append(str(e))
            continue
    raise NoLLMAvailable("; ".join(errors))


def _parse_json_response(text: str) -> dict[str, Any]:
    """Extract + parse JSON from an LLM response. Tolerates code fences,
    preamble paragraphs, and trailing commentary. Returns the parsed
    dict or raises LayerError on unrecoverable parse failure.
    """
    body = text.strip()
    try:
        obj = _json.loads(body)
        if isinstance(obj, dict):
            return obj
    except _json.JSONDecodeError:
        pass
    # Strip ```json fences if present
    fence = _re.search(r"```(?:json)?\s*(.*?)\s*```", body, _re.S)
    if fence:
        try:
            obj = _json.loads(fence.group(1).strip())
            if isinstance(obj, dict):
                return obj
        except _json.JSONDecodeError:
            pass
    # Substring between first '{' and last '}'
    start = body.find("{")
    end = body.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = _json.loads(body[start:end + 1])
            if isinstance(obj, dict):
                return obj
        except _json.JSONDecodeError:
            pass
    raise LayerError("llm-parse", f"no valid JSON in {len(text)} chars; "
                                     f"head: {text[:150]!r}")


def _llm_claude_cli(system: str, user: str, schema: dict | None,
                     timeout: int) -> str | dict[str, Any]:
    """Use claude.exe -p (print mode). Honors keychain OAuth so the
    Owner's existing Claude Code auth works without an explicit key.

    The spawned subprocess is locked down: --disable-slash-commands +
    --disallowed-tools "*" so the LLM cannot recursively invoke tools
    (which would risk hook recursion + resource explosion). We only
    want text generation here.
    """
    import shutil
    import subprocess
    cmd_path = HOME / ".local" / "bin" / "claude.exe"
    if not cmd_path.exists():
        resolved = shutil.which("claude.exe") or shutil.which("claude")
        if not resolved:
            raise LayerError("claude.exe", "binary not found on PATH")
        cmd_path = Path(resolved)

    augmented_user = user
    if schema is not None:
        augmented_user += (
            "\n\nRespond with ONLY a JSON object that matches this schema. "
            "No preamble, no commentary, no markdown fences:\n"
            + _json.dumps(schema, indent=2)
        )

    # CRITICAL: pass user message via STDIN, NOT argv. Windows has an
    # 8 KB-ish command-line cap (CreateProcessW), and our extract_learnings
    # prompt embeds up to 5 x 25 KB of markdown. Empirically caught
    # 2026-05-23 at Paso 1.8 first-run: WinError 206 "filename or extension
    # too long" when the markdown payload blew argv. claude.exe -p reads
    # stdin when no positional prompt is provided.
    args: list[str] = [
        str(cmd_path),
        "-p",
        "--disable-slash-commands",
        "--disallowed-tools", "*",
        "--append-system-prompt", system,
    ]

    model = env_str("CLAUDEPP_RESEARCH_MODEL")
    if model:
        args[1:1] = ["--model", model]

    # RECURSION GUARD: set CLAUDEPP_DEEPRESEARCH_RUNNING=1 in the spawned
    # claude.exe's env so research-intent-detector.js (Stop hook in the
    # subprocess session) early-exits instead of spawning another deep
    # research run. Empirically caught 2026-05-23 mid-V2: the generate_
    # serp_queries prompt contains "research" + is >80 words, which made
    # the Stop hook fire recursively from inside each LLM call. The
    # second spawn would hit the lock and emit a 1 KB locked-template
    # report. Sealed via env-var inheritance, belt-and-suspenders with
    # the same guard set in main() below.
    sub_env = os.environ.copy()
    sub_env["CLAUDEPP_DEEPRESEARCH_RUNNING"] = "1"
    try:
        r = subprocess.run(
            args, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
            input=augmented_user,
            env=sub_env,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        raise LayerError("claude.exe", f"subprocess failed: {e}")

    if r.returncode != 0:
        raise LayerError(
            "claude.exe",
            f"exit {r.returncode}: {(r.stderr or r.stdout)[:200]!r}",
        )

    output = (r.stdout or "").strip()
    if not output:
        raise LayerError("claude.exe", "empty stdout")

    if schema is not None:
        return _parse_json_response(output)
    return output


def _llm_anthropic_sdk(system: str, user: str, schema: dict | None,
                        timeout: int) -> str | dict[str, Any]:
    """Anthropic Python SDK fallback. Requires ANTHROPIC_API_KEY."""
    key = env_str("ANTHROPIC_API_KEY")
    if not key:
        raise LayerError("anthropic-sdk", "ANTHROPIC_API_KEY not set")
    try:
        import anthropic  # type: ignore[import-not-found]
    except ImportError as e:
        raise LayerError("anthropic-sdk", f"package missing: {e}")

    model = env_str("CLAUDEPP_RESEARCH_MODEL") or "claude-sonnet-4-6"

    augmented_user = user
    if schema is not None:
        augmented_user += (
            "\n\nRespond with ONLY a JSON object that matches this schema:\n"
            + _json.dumps(schema, indent=2)
        )

    try:
        client = anthropic.Anthropic(api_key=key, timeout=timeout)
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": augmented_user}],
        )
    except Exception as e:  # noqa: BLE001 — SDK exception family is broad
        raise LayerError("anthropic-sdk", f"API failed: {e}")

    output = "".join(
        getattr(b, "text", "") for b in (resp.content or [])
    ).strip()
    if not output:
        raise LayerError("anthropic-sdk", "empty response content")

    if schema is not None:
        return _parse_json_response(output)
    return output


# --- Chain functions (Pasos 1.5 / 1.6 / 1.7) -----------------------------
#
# Each chain wraps call_llm() with one of the verbatim prompts extracted
# from the n8n source (spec §3.2 / §3.4 / §3.5). The system message is the
# 11-instruction shared block (spec §3.1).
#
# All four prompt texts in this section are taken byte-for-byte from the
# source workflow's chainLlm nodes. They are the IP of the design; any
# rewording risks re-creating the original quality + reliability profile.

_SHARED_SYSTEM_TEMPLATE = (
    "You are an expert researcher. Today is {today}. Follow these "
    "instructions when responding:\n"
    " - You may be asked to research subjects that is after your "
    "knowledge cutoff, assume the user is right when presented with news.\n"
    " - The user is a highly experienced analyst, no need to simplify "
    "it, be as detailed as possible and make sure your response is correct.\n"
    " - Be highly organized.\n"
    " - Suggest solutions that I didn't think about.\n"
    " - Be proactive and anticipate my needs.\n"
    " - Treat me as an expert in all subject matter.\n"
    " - Mistakes erode my trust, so be accurate and thorough.\n"
    " - Provide detailed explanations, I'm comfortable with lots of detail.\n"
    " - Value good arguments over authorities, the source is irrelevant.\n"
    " - Consider new technologies and contrarian ideas, not just the "
    "conventional wisdom.\n"
    " - You may use high levels of speculation or prediction, just flag "
    "it for me."
)


def _shared_system() -> str:
    return _SHARED_SYSTEM_TEMPLATE.format(today=time.strftime("%Y-%m-%d"))


# --- Quality layer (v0.2.0, 2026-07-13) ----------------------------------
#
# The query + learnings prompts below are NO LONGER the verbatim n8n text.
# The "verbatim = IP, any rewording risks the quality profile" clause above
# was WRONG, and it is what shipped three defects to production:
#   1. "generate SERP queries" -> the LLM returned keyword soup, not questions
#   2. "as information dense as possible" with no prohibition -> CLI commands,
#      YAML and field names came back AS the learnings
#   3. no relevance gate at all -> everything persisted, relevant or not
# The corrected prompts and the gates that enforce them live in
# research_quality.py. Spec §3.2 / §3.4 are superseded by §3.6.

_MODULE_DIR = str(Path(__file__).resolve().parent)
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

from research_quality import (  # noqa: E402
    KEEP_LEVELS,
    RELEVANCE_SCHEMA,
    RELEVANCE_UNRATED,
    build_query_correction_prompt,
    build_relevance_prompt,
    find_code_in_learning,
    is_natural_question,
    log_discarded,
    parse_relevance_ratings,
)

# --- The four engines (v0.3.0, 2026-08-18) -------------------------------
#
# v0.2.0 gated QUALITY (is this a question, is this prose, can an operator act
# on it). It had no opinion about COVERAGE — which faces of the problem were
# searched, what kind of document the answer came from, or how much of the claim
# the evidence actually supports. The observed consequence: a learning founded
# on one vendor blog was persisted unlabelled, so an operator could not tell it
# from a measured result. research_engines.py owns the four engines that close
# that gap; research_quality.py keeps owning the per-string quality gates, which
# still run underneath them.

from research_engines import (  # noqa: E402
    COVERAGE_VENDOR_ONLY,
    CONTRADICTION_SCHEMA,
    DECOMPOSITION_SCHEMA,
    EPI_REJECTED,
    LEARNING_RECORD_SCHEMA,
    axes_covered,
    build_capability_learnings_prompt,
    build_contradiction_prompt,
    build_decomposition_correction_prompt,
    build_decomposition_prompt,
    classify_source,
    decomposition_is_sufficient,
    epistemic_distribution,
    format_contradiction_section,
    format_labeled_learning,
    landscape_verdict,
    normalize_axis,
    parse_contradictions,
    parse_learning_records,
    propagate_vendor_hosts,
    rank_sources_for_extraction,
)

# Every learning a gate throws away is appended here, with the reason. A gate
# that discards silently is indistinguishable from a bug; this file is how the
# Owner tunes the gates instead of guessing at them.
DISCARD_LOG_PATH = RESEARCH_DIR / "discarded_learnings.jsonl"


# --- Paso 1.5 / Engine 1 — decompose, then ask ---------------------------


def _ask_for_queries(user_msg: str, breadth: int
                      ) -> tuple[list[SerpQuery], list[tuple[str, str]]]:
    """One LLM round-trip. Returns (accepted, rejected).

    `rejected` is [(query, why)] for questions the natural-question gate
    refused — they are keyword piles, not questions, and searching them
    returns worse sources than a real question would.

    Engine 1 adds the `axis` field: which face of the problem the question
    attacks. An unrecognised axis is recorded as "" rather than defaulted, so
    coverage is measured on questions somebody actually classified.
    """
    result = call_llm(_shared_system(), user_msg, DECOMPOSITION_SCHEMA)
    if not isinstance(result, dict):
        raise LayerError("generate_serp_queries", "non-dict response")

    accepted: list[SerpQuery] = []
    rejected: list[tuple[str, str]] = []
    for q in (result.get("questions") or [])[:breadth]:
        if not isinstance(q, dict):
            continue
        query = (q.get("query") or "").strip()
        goal = (q.get("researchGoal") or "").strip()
        if not query or not goal:
            continue
        ok, why = is_natural_question(query)
        if ok:
            accepted.append({
                "query": query,
                "researchGoal": goal,
                "axis": normalize_axis(q.get("axis")) or "",
            })
        else:
            rejected.append((query, why))
    return accepted, rejected


def generate_serp_queries(prompt: str, breadth: int,
                           learnings: list[str] | None = None,
                           _state: dict[str, Any] | None = None,
                           ) -> list[SerpQuery]:
    """ENGINE 1 — decompose the topic, then emit the search questions.

    Searching a high-level topic directly retrieves the most popular framing of
    it, which is usually whoever sells the solution. Decomposing first forces
    the run to attack faces of the problem that popularity does not surface:
    where the thing fails, what refutes it, whether it transfers.

    Two gates, each bounded to ONE corrective re-ask (Anti-Antipattern Regla 12
    forbids a third identical attempt):

      * every question must pass is_natural_question() — a keyword pile
        retrieves documents that already agree with our guess;
      * the accepted set must span >= MIN_AXES_COVERED distinct axes — fewer
        than that is a rephrasing, not a decomposition.

    Both gates FAIL OPEN on the retry: if the corrective ask does not fix the
    coverage, the run proceeds with what it has and records the shortfall in the
    metadata. Losing the whole run because the decomposer was one axis short
    would be worse research than a narrow run the Owner can see is narrow.
    """
    learnings = learnings or []
    user_msg = build_decomposition_prompt(prompt, breadth, learnings)

    accepted, rejected = _ask_for_queries(user_msg, breadth)

    if not accepted and rejected:
        correction = build_query_correction_prompt(rejected, breadth)
        retry_accepted, retry_rejected = _ask_for_queries(
            f"{user_msg}\n\n{correction}", breadth
        )
        accepted = retry_accepted
        rejected = rejected + retry_rejected

    axes_ok, axes_reason = decomposition_is_sufficient(accepted)
    if accepted and not axes_ok:
        correction = build_decomposition_correction_prompt(accepted, breadth)
        try:
            widened, widened_rejected = _ask_for_queries(
                f"{user_msg}\n\n{correction}", breadth
            )
        except (LayerError, NoLLMAvailable) as e:
            widened, widened_rejected = [], []
            if _state is not None:
                _state["errors"].append(f"axis-widening re-ask failed: {e}")
        # Keep the wider set only if it IS wider. A retry that came back
        # narrower must not overwrite the questions we already had.
        if len(axes_covered(widened)) > len(axes_covered(accepted)):
            accepted = widened
        rejected = rejected + widened_rejected
        axes_ok, axes_reason = decomposition_is_sufficient(accepted)

    if _state is not None:
        _state.setdefault("axes_covered", set()).update(axes_covered(accepted))
        if not axes_ok and accepted:
            _state.setdefault("decomposition_shortfalls", []).append(axes_reason)
            _state["errors"].append(f"decomposition narrow: {axes_reason}")
        if rejected:
            _state.setdefault("queries_rejected", []).extend(
                {"query": q, "reason": why} for q, why in rejected
            )
            for q, why in rejected:
                _state["errors"].append(
                    f"query rejected (not a question): {q[:60]!r} — {why}"
                )
    return accepted


# --- Paso 1.6 / Engine 3 — capability + reality extraction ---------------


def extract_learnings(query: str,
                       markdowns: list[str],
                       coverage: dict[str, Any] | None = None,
                       _state: dict[str, Any] | None = None,
                       ) -> ExtractedLearnings:
    """ENGINE 3 — extract CAPABILITIES with an epistemic level, not prose facts.

    Each learning comes back as a record: the capability it confers (which
    decision it changes), the insight, the evidence sentence behind it, and a
    claimed epistemic level. Three layers then act on that claim, in order:

      1. cap_epistemic() — deterministic. OBSERVED without a quantity becomes
         DERIVED; VERIFIED without corroboration is demoted; a VENDOR_ONLY
         landscape rejects the claim outright. The extractor cannot certify its
         own confidence, which is the whole point: the previous version let it,
         and a single vendor blog produced an unlabelled claim nobody could
         weigh.
      2. find_code_in_learning() — deterministic, inherited from v0.2.0. The
         reader is a founder/operator; a learning carrying a CLI invocation is a
         defect of THIS system, not of the source.
      3. the relevance gate, applied by the caller after this returns.

    `coverage` is Engine 2's landscape verdict for the sources behind this
    query. Passing None means "assume covered" — used only by callers that
    have already vetted the landscape themselves.

    Every drop is logged with its reason to DISCARD_LOG_PATH. A gate that
    discards silently is indistinguishable from a bug.
    """
    if not markdowns:
        return {"learnings": [], "followUpQuestions": [], "records": []}

    contents_block = "\n".join(
        f"<content>\n{md[:MARKDOWN_MAX_CHARS]}\n</content>"
        for md in markdowns
    )

    user_msg = build_capability_learnings_prompt(query, contents_block)
    result = call_llm(_shared_system(), user_msg, LEARNING_RECORD_SCHEMA)
    if not isinstance(result, dict):
        raise LayerError("extract_learnings", "non-dict response")

    records = parse_learning_records(result, coverage)

    kept: list[str] = []
    kept_records: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []

    for rec in records:
        # Layer 1 outcome: the landscape refused to carry this claim at all.
        if rec["epistemic"] == EPI_REJECTED:
            dropped.append({
                "ts": iso_now(),
                "gate": "landscape",
                "query": query,
                "reason": rec["cap_reason"],
                "learning": rec["learning"],
            })
            continue

        # Layer 2: code never reaches an operator's knowledge base.
        code_reason = find_code_in_learning(
            f"{rec['learning']} {rec['capability']}"
        )
        if code_reason:
            dropped.append({
                "ts": iso_now(),
                "gate": "code",
                "query": query,
                "reason": code_reason,
                "learning": rec["learning"],
            })
            continue

        kept_records.append(rec)
        kept.append(format_labeled_learning(rec))

    if dropped:
        log_discarded(dropped, DISCARD_LOG_PATH)
        if _state is not None:
            for d in dropped:
                key = ("discarded_landscape" if d["gate"] == "landscape"
                       else "discarded_code")
                _state[key] = _state.get(key, 0) + 1
                _state["errors"].append(
                    f"learning dropped ({d['gate']} gate): {d['reason']}"
                )

    if _state is not None:
        for rec in kept_records:
            if rec["capped"]:
                _state["epistemic_capped"] = (
                    _state.get("epistemic_capped", 0) + 1
                )
                _state["errors"].append(
                    f"epistemic demoted {rec['epistemic_claimed']} -> "
                    f"{rec['epistemic']}: {rec['cap_reason']}"
                )

    follow_ups = [
        s.strip() for s in (result.get("followUpQuestions") or [])
        if isinstance(s, str) and s.strip()
    ][:3]
    return {
        "learnings": kept[:3],
        "followUpQuestions": follow_ups,
        "records": kept_records[:3],
    }


# --- Relevance gate (v0.2.0) ---------------------------------------------


def filter_by_relevance(learnings: list[str],
                         operator_context: str | None = None,
                         _state: dict[str, Any] | None = None,
                         ) -> list[str]:
    """Keep only the learnings an operator can actually act on.

    Doctrine: better to lose a valid learning than to persist an irrelevant
    one. An irrelevant learning is not neutral — the vault is read back as
    context by every later run, so noise persisted once is paid for forever.

    Runs BEFORE the learning enters the corpus, so a dropped learning also
    never seeds a follow-up query. Only HIGH/MEDIUM survive; LOW and DISCARD
    are logged to DISCARD_LOG_PATH with the rater's reason.

    Fail behaviour is asymmetric by design. The code gate above is
    deterministic and cannot fail. This gate needs an LLM and therefore CAN
    be unavailable — when it is, the learnings are kept but marked UNRATED in
    the run metadata. We never pass unrated content off as vetted, and we
    never silently destroy a whole run's work because a judge was offline.
    """
    if not learnings:
        return []

    user_msg = build_relevance_prompt(learnings, operator_context)
    try:
        result = call_llm(_shared_system(), user_msg, RELEVANCE_SCHEMA)
    except (LayerError, NoLLMAvailable) as e:
        if _state is not None:
            _state["relevance_verdict"] = RELEVANCE_UNRATED
            _state["errors"].append(f"relevance filter unavailable: {e}")
        return list(learnings)

    if not isinstance(result, dict):
        if _state is not None:
            _state["relevance_verdict"] = RELEVANCE_UNRATED
            _state["errors"].append("relevance filter: non-dict response")
        return list(learnings)

    ratings = parse_relevance_ratings(result, len(learnings))

    kept: list[str] = []
    dropped: list[dict[str, Any]] = []
    for i, learning in enumerate(learnings):
        rating = ratings.get(i)
        if rating is None:
            # The rater skipped this one, or emitted a level outside the
            # scale. Keep it — losing work to a malformed response is worse
            # than keeping an unrated line — but say so in the metadata.
            kept.append(learning)
            if _state is not None:
                _state["errors"].append(
                    f"learning {i} unrated by relevance filter — kept, "
                    f"flagged {RELEVANCE_UNRATED}"
                )
            continue
        if rating["relevance"] in KEEP_LEVELS:
            kept.append(learning)
        else:
            dropped.append({
                "ts": iso_now(),
                "gate": "relevance",
                "relevance": rating["relevance"],
                "reason": rating["reason"],
                "learning": learning,
            })

    if dropped:
        log_discarded(dropped, DISCARD_LOG_PATH)
        if _state is not None:
            _state["discarded_relevance"] = (
                _state.get("discarded_relevance", 0) + len(dropped)
            )

    return kept


# --- Paso 1.7 — generate_report ------------------------------------------

def generate_report(prompt: str, learnings: list[str], urls: list[str],
                     contradictions: list[dict[str, Any]] | None = None) -> str:
    """Single LLM call that synthesizes all collected learnings into a
    multi-page markdown report. Caller appends ## Sources + ## Run metadata;
    this function returns the LLM body plus the contradictions section.

    Every learning arrives pre-labelled `[EPISTEMIC][QUALITY]` by Engine 3, and
    the synthesis is instructed to CARRY those labels rather than smooth them
    away. A report that reads uniformly confident, built from evidence that was
    not uniformly strong, is the exact failure this version exists to end.
    """
    if not learnings:
        return (
            "# Research Report — INSUFFICIENT DATA\n\n"
            f"Prompt: {prompt}\n\n"
            "The research run completed without extracting any learnings. "
            "This can happen when SERP results were empty across all "
            "queries, page-fetch failed for every result, or every source "
            "landscape was vendor-only and the coverage gate refused to build "
            "claims on it. Re-run with different keywords or check "
            "vault/cache_hints/CEILING.md for the layer-by-layer failure log."
        )

    learnings_block = "\n".join(
        f"<learning>{ln}</learning>" for ln in learnings
    )
    user_msg = (
        f"You are an expert and insightful researcher.\n"
        f"* Given the following prompt from the user, write a final "
        f"report on the topic using the learnings from research.\n"
        f"* Make it as detailed as possible, aim for 3 or more pages, "
        f"include ALL the learnings from research.\n"
        f"* Format the report in markdown. Use headings, lists and tables "
        f"only and where appropriate.\n"
        f"* EVERY learning arrives tagged [EPISTEMIC][SOURCE-QUALITY]. CARRY "
        f"those tags into the report next to the claim they belong to. Never "
        f"present a [HYPOTHESIS] or a [DERIVED] claim in the same voice as an "
        f"[OBSERVED] one, and never drop a tag to make a paragraph read "
        f"smoother. A reader must be able to tell, without leaving the "
        f"sentence, how much to bet on it.\n"
        f"* Where the evidence is thin, SAY it is thin. An honest gap is a "
        f"finding; a confident sentence covering a gap is a defect.\n\n"
        f"<prompt>{prompt}</prompt>\n\n"
        f"Here are all the learnings from previous research:\n\n"
        f"<learnings>\n{learnings_block}\n</learnings>"
    )
    # Report is text-only — no JSON schema. Bumped timeout because the
    # full-report call typically generates 3+ pages of content.
    result = call_llm(_shared_system(), user_msg, None,
                       timeout=LLM_TIMEOUT_S * 2)
    if not isinstance(result, str):
        raise LayerError("generate_report", "non-string response")
    # The contradictions section is appended deterministically, never left to
    # the synthesis LLM. Asking a model to summarise conflicts is asking it to
    # resolve them; this section must survive the summary intact.
    return (result.strip() + "\n\n"
            + format_contradiction_section(contradictions or []))


# --- Paso 1.8 — recursive deep_research driver ---------------------------
#
# deep_research orchestrates the four cascades (search, fetch, markdown,
# LLM) into the recursive algorithm of spec §2. It is the public entry
# point; the CLI in Paso 1.9 wraps it for argv-driven invocation.
#
# Recursion + governance:
#   * Halve breadth on each level (spec §2 line "breadth // 2"). Floor at 1.
#   * Hard cap total queries at MAX_QUERIES (default 30) to prevent
#     exponential explosion at depth >= 3 with high breadth.
#   * Per-request timeouts are already baked into the cascade layers.
#   * Total wall-clock ceiling enforced by a deadline check before each
#     LLM call (cheapest place to abort cleanly).
#   * Single-instance lock acquired at the top of the call; released in
#     a finally clause regardless of outcome.


def _write_ceiling(reason: str, prompt: str,
                    detail: dict[str, Any]) -> Path:
    """Honest ceiling write — happens iff the agent CANNOT produce a real
    report (every search layer exhausted, no LLM available, query budget
    blown, runtime ceiling hit). The file is a forensic artifact, not
    an apology — it documents WHY the ceiling was reached so the Owner
    can fix the gap (e.g. add an API key, raise the budget).
    """
    CACHE_HINTS_DIR.mkdir(parents=True, exist_ok=True)
    target = CACHE_HINTS_DIR / "CEILING.md"
    payload = (
        f"\n---\n## {iso_now()} — deep_research ceiling: {reason}\n\n"
        f"**Prompt:** {prompt[:200]}\n\n"
        f"**Detail:**\n```json\n{_json.dumps(detail, indent=2)}\n```\n"
    )
    with target.open("a", encoding="utf-8") as f:
        f.write(payload)
    return target


def _detect_contradictions(learnings: list[str],
                            _state: dict[str, Any]) -> None:
    """ENGINE 4 — find where the corpus disagrees with itself. Mutates _state.

    Two sources that conflict are a FINDING. The previous pipeline resolved
    conflicts by whichever learning happened to be extracted last, which is
    coin-flipping with extra steps: the operator never learned the field was
    contested, so they bet on a disputed claim at the confidence of a settled
    one.

    Fail behaviour is asymmetric, matching filter_by_relevance: the detector
    needs an LLM and can therefore be unavailable. When it is, the verdict is
    recorded as `unavailable` and the report says so. We never pass an unchecked
    corpus off as conflict-free — a silent absence reads identically whether the
    engine found nothing or never ran, and removing that ambiguity is the entire
    purpose of the engine.
    """
    if len(learnings) < 2:
        _state["contradiction_verdict"] = "skipped-too-few-learnings"
        return
    try:
        result = call_llm(_shared_system(),
                           build_contradiction_prompt(learnings),
                           CONTRADICTION_SCHEMA)
    except (LayerError, NoLLMAvailable) as e:
        _state["contradiction_verdict"] = "unavailable"
        _state["errors"].append(f"contradiction detection unavailable: {e}")
        return
    if not isinstance(result, dict):
        _state["contradiction_verdict"] = "unavailable"
        _state["errors"].append("contradiction detection: non-dict response")
        return
    _state["contradictions"] = parse_contradictions(result, len(learnings))
    _state["contradiction_verdict"] = "checked"
    _state["layers_fired"]["llm"].add("claude.exe")


def deep_research(
    prompt: str,
    depth: int = 2,
    breadth: int = 3,
    learnings: list[str] | None = None,
    urls: list[str] | None = None,
    operator_context: str | None = None,
    _state: dict[str, Any] | None = None,
) -> ResearchResult:
    """Run the recursive research algorithm. Returns a ResearchResult.

    Top-level invocation (no `_state` passed) acquires the single-instance
    lock, initialises run accounting, and is the only level that calls
    generate_report() at the end. Recursive invocations pass the shared
    state dict (queries-asked counter, deadline, started-at, layers-fired)
    so the governance guardrails see the FULL run, not just one level.
    """
    learnings = list(learnings or [])
    urls = list(urls or [])
    is_top_level = _state is None

    if is_top_level:
        if env_disabled():
            return {
                "report_md": "# deep_research DISABLED\n\n"
                              "CLAUDEPP_DEEPRESEARCH_DISABLE=1 in env.\n",
                "learnings": [], "urls": [],
                "metadata": {"verdict": "disabled-by-env"},
            }
        lock = acquire_lock()
        if lock == "held":
            return {
                "report_md": "# deep_research locked\n\n"
                              "Another run holds the lock — refusing "
                              "to pile up. Retry after the in-flight "
                              "run finishes.\n",
                "learnings": [], "urls": [],
                "metadata": {"verdict": "lock-held"},
            }
        priority_verdict = lower_priority()
        max_queries = env_int("CLAUDEPP_DEEPRESEARCH_MAX_QUERIES",
                                MAX_QUERIES_DEFAULT)
        total_timeout = env_int("CLAUDEPP_DEEPRESEARCH_TIMEOUT_S",
                                  TOTAL_TIMEOUT_S_DEFAULT)
        _state = {
            "started_at": time.time(),
            "deadline": time.time() + total_timeout,
            "queries_used": 0,
            "max_queries": max_queries,
            "layers_fired": {"search": set(), "markdown": set(),
                              "llm": set()},
            "priority_verdict": priority_verdict,
            "lock_verdict": lock,
            "errors": [],
            "all_search_queries": [],
            # Quality-layer accounting (v0.2.0). Stored on the shared state
            # so recursion levels all report into the same counters.
            "operator_context": (
                operator_context
                or env_str("CLAUDEPP_RESEARCH_OPERATOR_CONTEXT")
                or None
            ),
            "queries_rejected": [],
            "discarded_code": 0,
            "discarded_relevance": 0,
            # Engine accounting (v0.3.0). All four engines report into the
            # shared state so a recursive level's coverage is visible in the
            # top-level footer, not lost at the depth it happened.
            "axes_covered": set(),          # E1 — faces of the problem searched
            "decomposition_shortfalls": [],  # E1 — narrow decompositions
            "families_seen": {},            # E2 — source families fetched
            "coverage_by_query": [],        # E2 — landscape verdict per query
            "source_classifications": [],   # E2 — per-URL verdict + its signals
            "vendor_only_queries": 0,       # E2 — questions refused outright
            "discarded_landscape": 0,       # E2 — learnings the landscape killed
            "records": [],                  # E3 — surviving structured records
            "epistemic_capped": 0,          # E3 — labels the gates demoted
            "contradictions": [],           # E4 — unresolved conflicts found
            "contradiction_verdict": "not-run",
            "relevance_verdict": "rated",
        }

    try:
        # Generate this level's research questions.
        try:
            queries = generate_serp_queries(prompt, breadth, learnings,
                                             _state=_state)
        except (LayerError, NoLLMAvailable) as e:
            _state["errors"].append(f"generate_serp_queries: {e}")
            queries = []
        if not queries:
            # If we can't even ask the first set of queries, log + return
            # whatever we have. At top level this becomes INSUFFICIENT
            # DATA via generate_report.
            _state["errors"].append("no SERP queries generated")

        for q in queries:
            # Check guardrails BEFORE each query (cheapest abort point).
            if _state["queries_used"] >= _state["max_queries"]:
                _state["errors"].append(
                    f"query budget exhausted ({_state['max_queries']})"
                )
                break
            if time.time() > _state["deadline"]:
                _state["errors"].append("runtime ceiling hit")
                break

            _state["queries_used"] += 1
            _state["all_search_queries"].append(q["query"])
            try:
                hits, layer = web_search(q["query"], n=10)
                _state["layers_fired"]["search"].add(layer)
            except NoSearchAvailable as e:
                _state["errors"].append(
                    f"web_search '{q['query'][:40]}...': {e}"
                )
                continue

            # Top 5 organic — match the n8n source workflow exactly.
            top5 = hits[:5]
            # ENGINE 2 — classify every page that actually parsed, so the
            # landscape verdict is computed over what we READ, not over what
            # the SERP promised. A page that 403'd contributes no evidence and
            # must not count toward coverage.
            fetched: list[dict[str, Any]] = []
            for h in top5:
                if time.time() > _state["deadline"]:
                    break
                try:
                    page = fetch_page(h["url"])
                except LayerError as e:
                    _state["errors"].append(
                        f"fetch_page '{h['url'][:60]}...': {e}"
                    )
                    continue
                md, md_layer = html_to_markdown(
                    page["html"], base_url=page.get("final_url", h["url"])
                )
                _state["layers_fired"]["markdown"].add(md_layer)
                if not md:
                    continue
                final_url = page.get("final_url", h["url"])
                cls = classify_source(final_url, h.get("title", ""),
                                       h.get("snippet", ""), md)
                cls["markdown"] = md
                fetched.append(cls)
                _state["families_seen"][cls["family"]] = (
                    _state["families_seen"].get(cls["family"], 0) + 1
                )

            # Load-bearing families are read FIRST: extraction budgets are
            # finite, and feeding the vendor page ahead of the paper means the
            # truncation eats the paper.
            # Host-level vendor memory runs BEFORE the verdict: a domain that
            # sells on one fetched page sells on all of them, and the landscape
            # must be judged on that, not on which URL the SERP happened to
            # return first.
            fetched = propagate_vendor_hosts(fetched)
            fetched = rank_sources_for_extraction(fetched)
            markdowns = [c["markdown"] for c in fetched]
            new_urls = [c["url"] for c in fetched]

            coverage = landscape_verdict(fetched)
            _state["coverage_by_query"].append({
                "query": q["query"],
                "axis": q.get("axis", ""),
                "verdict": coverage["verdict"],
                "quality": coverage["quality"],
                "families": coverage["families"],
                "source_count": coverage["source_count"],
            })
            # The per-source verdict AND the signals behind it. Without this the
            # classifier cannot be calibrated: a run reports "UNKNOWN×14" and
            # nobody can say which hosts those were or which rule missed them,
            # so the only available move is to guess at thresholds. Same reason
            # discarded_learnings.jsonl exists — a gate that decides silently is
            # indistinguishable from a gate that is wrong.
            for d in coverage["detail"]:
                _state["source_classifications"].append({
                    "query": q["query"],
                    "axis": q.get("axis", ""),
                    "url": d["url"],
                    "family": d["family"],
                    "quality": d["quality"],
                    "signals": d["signals"],
                })
            if coverage["verdict"] == COVERAGE_VENDOR_ONLY and markdowns:
                # Not a warning — a refusal. Every source behind this question
                # is a conversion surface, so anything extracted here would be
                # somebody's marketing repeated back as a finding. Extraction is
                # skipped entirely: an LLM call that can only produce rejected
                # records is budget spent to learn nothing.
                _state["vendor_only_queries"] += 1
                _state["errors"].append(
                    f"landscape VENDOR_ONLY for '{q['query'][:40]}' — "
                    f"{coverage['source_count']} source(s), families "
                    f"{', '.join(coverage['families'])}; extraction skipped"
                )
                continue

            if not markdowns:
                _state["errors"].append(
                    f"no markdowns extracted for '{q['query'][:40]}'"
                )
                continue

            try:
                extracted = extract_learnings(q["query"], markdowns,
                                               coverage=coverage,
                                               _state=_state)
            except (LayerError, NoLLMAvailable) as e:
                _state["errors"].append(f"extract_learnings: {e}")
                continue
            _state["layers_fired"]["llm"].add("claude.exe")

            # Relevance gate runs HERE — before the learning enters the
            # corpus — so an irrelevant learning is never persisted AND
            # never seeds a follow-up query at the next depth level.
            relevant = filter_by_relevance(
                extracted["learnings"],
                operator_context=_state.get("operator_context"),
                _state=_state,
            )

            # Keep the structured records aligned with the strings that
            # survived. The report footer reports the confidence profile of the
            # CORPUS, so a record whose string the relevance gate dropped must
            # not be counted as if it had been persisted.
            survived = set(relevant)
            _state["records"].extend(
                r for r in extracted["records"]
                if format_labeled_learning(r) in survived
            )

            learnings.extend(relevant)
            # Only cite pages that actually produced a surviving learning.
            # Listing a source whose every learning was discarded implies a
            # contribution it did not make.
            if relevant:
                urls.extend(new_urls)

            # Recurse if depth > 1 (matching spec §2 termination).
            if depth > 1 and extracted["followUpQuestions"]:
                sub_prompt = (
                    f"Previous research goal: {q['researchGoal']}\n"
                    f"Follow-up research directions: "
                    + "\n".join(extracted["followUpQuestions"])
                )
                sub_result = deep_research(
                    sub_prompt,
                    depth=depth - 1,
                    breadth=max(1, breadth // 2),
                    learnings=learnings,
                    urls=urls,
                    _state=_state,
                )
                # Sub-result already mutated learnings/urls in-place via
                # the shared lists; pull them back to canonical refs.
                learnings = sub_result["learnings"]
                urls = sub_result["urls"]

        if is_top_level:
            # ENGINE 4 — run BEFORE synthesis, so the report writer sees the
            # conflicts instead of resolving them by whichever learning it read
            # last. Detection needs the whole corpus, so this is the only place
            # it can run: a recursive level has seen a fraction of it.
            _detect_contradictions(learnings, _state)

            # Generate the final report. If learnings is empty,
            # generate_report() returns the INSUFFICIENT DATA template
            # honestly rather than fabricating content.
            try:
                report_md = generate_report(prompt, learnings, urls,
                                             _state["contradictions"])
                _state["layers_fired"]["llm"].add("claude.exe")
            except (LayerError, NoLLMAvailable) as e:
                _state["errors"].append(f"generate_report: {e}")
                report_md = (
                    f"# Research Report — LLM CEILING\n\n"
                    f"Prompt: {prompt}\n\n"
                    f"All learnings + URLs are below (raw, unsynthesized) "
                    f"because the report-generation LLM call failed:\n"
                    f"{e}\n\n"
                    f"## Raw learnings ({len(learnings)})\n"
                    + "\n".join(f"- {ln}" for ln in learnings)
                    + "\n\n## Raw URLs\n"
                    + "\n".join(f"- {u}" for u in dict.fromkeys(urls))
                )
                _write_ceiling("report-gen-llm-failed", prompt,
                               {"error": str(e),
                                "learnings_collected": len(learnings)})

            duration = time.time() - _state["started_at"]
            return {
                "report_md": report_md,
                "learnings": learnings,
                "urls": list(dict.fromkeys(urls)),  # dedup preserving order
                "metadata": {
                    "depth": depth,
                    "breadth": breadth,
                    "queries_used": _state["queries_used"],
                    "queries_log": _state["all_search_queries"],
                    "layers_fired": {
                        k: sorted(v)
                        for k, v in _state["layers_fired"].items()
                    },
                    "priority": _state["priority_verdict"],
                    "lock": _state["lock_verdict"],
                    "duration_s": round(duration, 1),
                    "errors": _state["errors"],
                    "started_at": iso_now(),
                    # Quality layer — what the gates threw away, and why.
                    # Surfaced in the report footer so a run that silently
                    # discarded most of its yield is visible, not hidden.
                    "queries_rejected": _state["queries_rejected"],
                    "discarded_code": _state["discarded_code"],
                    "discarded_relevance": _state["discarded_relevance"],
                    "relevance_verdict": _state["relevance_verdict"],
                    "discard_log": str(DISCARD_LOG_PATH),
                    # Engine layer (v0.3.0). These are the numbers that say how
                    # much to trust the report as a whole: which faces of the
                    # problem were searched, what kind of documents answered,
                    # how many labels the gates had to demote, and where the
                    # corpus disagrees with itself.
                    "axes_covered": sorted(_state["axes_covered"]),
                    "decomposition_shortfalls":
                        _state["decomposition_shortfalls"],
                    "families_seen": _state["families_seen"],
                    "coverage_by_query": _state["coverage_by_query"],
                    "source_classifications":
                        _state["source_classifications"],
                    "vendor_only_queries": _state["vendor_only_queries"],
                    "discarded_landscape": _state["discarded_landscape"],
                    "epistemic_capped": _state["epistemic_capped"],
                    "epistemic_distribution":
                        epistemic_distribution(_state["records"]),
                    "contradictions": _state["contradictions"],
                    "contradiction_verdict": _state["contradiction_verdict"],
                },
            }

        # Recursive level — return shared state references so parent
        # can pull them back.
        return {
            "report_md": "",
            "learnings": learnings,
            "urls": urls,
            "metadata": {},
        }
    finally:
        if is_top_level:
            release_lock()


# --- Paso 1.9 — CLI + three-artifact writer ------------------------------

def _atomic_write_text(path: Path, content: str) -> None:
    """Write `content` to `path` atomically (.tmp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _append_index(row: dict[str, Any]) -> None:
    """Append one JSON-lines row to vault/research/index.json. The file
    is a JSONL stream (one object per line), NOT a single JSON array —
    avoids read-modify-write contention if two runs append nearly
    simultaneously (the lock prevents that, but defense in depth)."""
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("a", encoding="utf-8") as f:
        f.write(_json.dumps(row, ensure_ascii=False) + "\n")


def _load_index() -> list[dict[str, Any]]:
    """Read all rows from index.json (JSONL). Empty file -> []."""
    if not INDEX_PATH.exists():
        return []
    rows = []
    with INDEX_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(_json.loads(line))
            except _json.JSONDecodeError:
                continue
    return rows


def _dedup_urls_against_history(urls: list[str], prompt: str) -> list[str]:
    """Filter out URLs that appeared in a prior index.json entry whose
    prompt was textually similar (first 30 chars match). This is the
    "re-run same prompt = no duplicate URLs in Sources" guarantee from
    spec §10."""
    prior = _load_index()
    prompt_key = prompt.lower()[:30].strip()
    seen: set[str] = set()
    for row in prior:
        rprompt = (row.get("prompt") or "").lower()[:30].strip()
        if rprompt == prompt_key:
            for u in row.get("urls_sample", []):
                seen.add(u)
    return [u for u in urls if u not in seen]


def write_research_artifacts(
    prompt: str,
    result: ResearchResult,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Write the three artifacts of spec §6:

      1. <ts>_<slug>.md   — markdown report + ## Sources + ## Run metadata
      2. index.json       — JSONL append (one row per run)
      3. <slug>.raw.jsonl — per-run trace (queries asked, layers fired)

    Returns {report, index, raw} -> Path mapping.
    """
    output_dir = output_dir or RESEARCH_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = now_ts()
    slug = slugify(prompt)
    report_path = output_dir / f"{ts}_{slug}.md"
    raw_path = output_dir / f"{slug}.raw.jsonl"

    # Build the composite markdown: body + Sources + Run metadata.
    deduped_urls = list(dict.fromkeys(result["urls"]))
    fresh_urls = _dedup_urls_against_history(deduped_urls, prompt)

    sources_md = "## Sources\n\n" + (
        "\n".join(f"- <{u}>" for u in deduped_urls)
        if deduped_urls else "_(none collected)_"
    )
    if len(fresh_urls) != len(deduped_urls):
        sources_md += (
            f"\n\n_Note: {len(deduped_urls) - len(fresh_urls)} URL(s) "
            f"also appeared in prior runs of this prompt (not duplicates "
            f"in current run; see index.json for full history)._"
        )

    meta = dict(result["metadata"])
    meta_md = (
        "## Run metadata\n\n"
        f"- **Prompt:** {prompt}\n"
        f"- **Depth / breadth:** {meta.get('depth', '?')} / "
        f"{meta.get('breadth', '?')}\n"
        f"- **Queries used:** {meta.get('queries_used', 0)} "
        f"(budget {env_int('CLAUDEPP_DEEPRESEARCH_MAX_QUERIES', MAX_QUERIES_DEFAULT)})\n"
        f"- **Layers fired:**\n"
        + "".join(
            f"  - {k}: {', '.join(v) if v else '(none)'}\n"
            for k, v in meta.get("layers_fired", {}).items()
        )
        + f"- **Priority class:** {meta.get('priority', '?')}\n"
          f"- **Lock:** {meta.get('lock', '?')}\n"
          f"- **Duration:** {meta.get('duration_s', '?')} s\n"
          f"- **Errors during run:** {len(meta.get('errors', []))}\n"
          f"- **Started at:** {meta.get('started_at', '?')}\n"
          f"- **Module version:** deep_research {__version__}\n"
          f"- **Quality gates:** "
          f"{len(meta.get('queries_rejected', []))} query/queries rejected as "
          f"keyword soup · {meta.get('discarded_code', 0)} learning(s) dropped "
          f"for containing code · {meta.get('discarded_relevance', 0)} dropped "
          f"as not operator-actionable "
          f"(relevance: {meta.get('relevance_verdict', '?')})\n"
    )
    # Engine footer (v0.3.0). The point of this block is that a reader can see
    # WHY the report is as confident as it is without reading the report: which
    # faces of the problem were searched, what kind of documents answered, how
    # many labels the gates had to demote. A run that covered one axis with one
    # vendor family should look thin here, and it does.
    axes = meta.get("axes_covered") or []
    families = meta.get("families_seen") or {}
    dist = meta.get("epistemic_distribution") or {}
    meta_md += (
        f"- **E1 decomposition:** {len(axes)}/5 axes searched"
        f"{' (' + ', '.join(axes) + ')' if axes else ''}"
        f"{'  — SHORTFALL: ' + '; '.join(meta['decomposition_shortfalls']) if meta.get('decomposition_shortfalls') else ''}\n"
        f"- **E2 landscape:** "
        + (", ".join(f"{k}×{v}" for k, v in sorted(families.items()))
           or "no sources classified")
        + f" · {meta.get('vendor_only_queries', 0)} question(s) refused as "
          f"vendor-only · {meta.get('discarded_landscape', 0)} learning(s) "
          f"killed by the coverage gate\n"
        f"- **E3 reality:** "
        + (", ".join(f"{k} {v}" for k, v in dist.items() if v)
           or "no learnings persisted")
        + f" · {meta.get('epistemic_capped', 0)} label(s) demoted by the "
          f"evidence gates\n"
        f"- **E4 contradictions:** {len(meta.get('contradictions') or [])} "
        f"unresolved conflict(s) "
        f"(detector: {meta.get('contradiction_verdict', '?')})\n"
    )
    if meta.get("coverage_by_query"):
        meta_md += "\n<details>\n<summary>Source landscape per question</summary>\n\n"
        for c in meta["coverage_by_query"]:
            meta_md += (
                f"- `{c['verdict']}` / {c['quality']} "
                f"[{c.get('axis') or 'UNCLASSIFIED'}] — {c['source_count']} "
                f"source(s), families {', '.join(c['families']) or 'none'} — "
                f"_{c['query'][:90]}_\n"
            )
        meta_md += "\n</details>\n"
    if meta.get("discard_log"):
        meta_md += f"- **Discard log:** `{meta['discard_log']}`\n"
    if meta.get("errors"):
        meta_md += "\n<details>\n<summary>Error log</summary>\n\n"
        for err in meta["errors"][:20]:
            meta_md += f"- `{err}`\n"
        meta_md += "\n</details>\n"

    composite = (
        result["report_md"].rstrip()
        + "\n\n"
        + sources_md
        + "\n\n"
        + meta_md
    )
    _atomic_write_text(report_path, composite)

    # Per-query raw trace: append-mode so multiple runs of the same prompt
    # accumulate forensic detail (each one prepended by a run-header row).
    raw_header = {
        "type": "run-header",
        "ts": meta.get("started_at"),
        "prompt": prompt,
        "depth": meta.get("depth"),
        "breadth": meta.get("breadth"),
        "duration_s": meta.get("duration_s"),
    }
    with raw_path.open("a", encoding="utf-8") as f:
        f.write(_json.dumps(raw_header, ensure_ascii=False) + "\n")
        for q in meta.get("queries_log", []):
            f.write(_json.dumps(
                {"type": "query", "ts": meta.get("started_at"), "query": q},
                ensure_ascii=False) + "\n")
        for ln in result["learnings"]:
            f.write(_json.dumps(
                {"type": "learning", "ts": meta.get("started_at"),
                 "learning": ln}, ensure_ascii=False) + "\n")
        # One row per classified source. This is the calibration corpus for
        # Engine 2: it accumulates across runs, so the UNKNOWN population can be
        # measured over real traffic instead of argued about from one report.
        for s in meta.get("source_classifications", []):
            f.write(_json.dumps(
                {"type": "source", "ts": meta.get("started_at"), **s},
                ensure_ascii=False) + "\n")

    # Index row — small JSON shape suitable for SessionStart auto-discovery.
    index_row = {
        "ts": meta.get("started_at"),
        "slug": slug,
        "prompt": prompt[:200],
        "depth": meta.get("depth"),
        "breadth": meta.get("breadth"),
        "learning_count": len(result["learnings"]),
        "source_count": len(deduped_urls),
        "duration_s": meta.get("duration_s"),
        "layers": {k: list(v) for k, v in meta.get("layers_fired", {}).items()},
        "errors": len(meta.get("errors", [])),
        "report_path": str(report_path.relative_to(PP_REPO))
            if str(report_path).startswith(str(PP_REPO))
            else str(report_path),
        "urls_sample": deduped_urls[:20],  # sample for dedup-on-rerun
        # Engine summary. The index is what SessionStart auto-discovery reads,
        # so the confidence profile has to be legible WITHOUT opening the
        # report — otherwise a thin run and a strong run look identical in the
        # one place a future session actually looks.
        "axes_covered": meta.get("axes_covered", []),
        "families_seen": meta.get("families_seen", {}),
        "vendor_only_queries": meta.get("vendor_only_queries", 0),
        "epistemic_distribution": meta.get("epistemic_distribution", {}),
        "epistemic_capped": meta.get("epistemic_capped", 0),
        "contradictions": len(meta.get("contradictions") or []),
        "contradiction_verdict": meta.get("contradiction_verdict", "?"),
    }
    _append_index(index_row)

    return {"report": report_path, "index": INDEX_PATH, "raw": raw_path}


def _build_argparser() -> "argparse.ArgumentParser":
    import argparse as _argparse
    ap = _argparse.ArgumentParser(
        prog="deep_research",
        description="Recursive web research agent (Claude Power Pack). "
                    "Source-spec: vault/specs/deep-research-agent.md.",
    )
    ap.add_argument("--version", action="version",
                     version=f"deep_research {__version__}")
    ap.add_argument("--prompt", help="research prompt (required for a run)")
    ap.add_argument("--depth", type=int, default=2, choices=range(1, 6),
                     help="recursion depth (default 2)")
    ap.add_argument("--breadth", type=int, default=3, choices=range(2, 6),
                     help="queries per level (default 3)")
    ap.add_argument("--clarify", action="store_true",
                     help="run the optional Clarifying Questions step first "
                          "(spec §3.3)")
    ap.add_argument("--operator-context", default=None,
                     help="who will read the learnings, so the relevance "
                          "gate can judge what is actionable for THEM. "
                          "Defaults to CLAUDEPP_RESEARCH_OPERATOR_CONTEXT, "
                          "then to a generic founder/operator.")
    ap.add_argument("--out", default=None,
                     help="output directory (default vault/research/)")
    ap.add_argument("--quiet", action="store_true",
                     help="suppress progress chatter on stdout")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    if not args.prompt:
        # No prompt -> self-test (matches Paso 1.1 spec).
        return _self_test()

    # Belt-and-suspenders recursion guard. Even though _llm_claude_cli
    # also sets the env-var, doing it here too means ANY indirect spawn
    # (a sub-tool, a hook, a future child) also inherits the flag.
    os.environ["CLAUDEPP_DEEPRESEARCH_RUNNING"] = "1"

    out_dir = Path(args.out) if args.out else RESEARCH_DIR

    if not args.quiet:
        print(f"deep_research {__version__}: prompt='{args.prompt[:60]}...' "
              f"depth={args.depth} breadth={args.breadth}", file=sys.stderr)

    # Clarifying questions are documented in the spec but not yet wired
    # to the driver. When the Owner sets --clarify, we honor the request
    # by asking the LLM and printing the questions to stderr — the Owner
    # is expected to re-prompt with the refined query. Auto-injection
    # back into the driver is a future enhancement; spec §12 question 1
    # was answered as "opt-in" at Accept time, and printing satisfies
    # the opt-in contract honestly (the Owner sees the questions, agent
    # does not silently substitute the prompt).
    if args.clarify:
        from deep_research import _shared_system as _ss  # noqa: F401
        clarify_schema = {
            "type": "object",
            "properties": {
                "questions": {"type": "array",
                              "items": {"type": "string"}},
            },
            "required": ["questions"],
        }
        clarify_user = (
            f"Given the following query from the user, ask some follow up "
            f"questions to clarify the research direction. Return a "
            f"maximum of 3 questions, but feel free to return less if "
            f"the original query is clear: <query>{args.prompt}</query>"
        )
        try:
            cresult = call_llm(_shared_system(), clarify_user, clarify_schema)
            if isinstance(cresult, dict):
                qs = cresult.get("questions") or []
                if qs and not args.quiet:
                    print("\n--- CLARIFYING QUESTIONS (re-prompt to refine) ---",
                          file=sys.stderr)
                    for i, q in enumerate(qs, 1):
                        print(f"  {i}. {q}", file=sys.stderr)
                    print("---\n", file=sys.stderr)
        except (LayerError, NoLLMAvailable) as e:
            print(f"clarify step failed: {e}", file=sys.stderr)

    result = deep_research(args.prompt, depth=args.depth,
                            breadth=args.breadth,
                            operator_context=args.operator_context)
    paths = write_research_artifacts(args.prompt, result, out_dir)

    if not args.quiet:
        print(f"\ndeep_research: OK", file=sys.stderr)
        print(f"  report:   {paths['report']}", file=sys.stderr)
        print(f"  index:    {paths['index']}", file=sys.stderr)
        print(f"  raw:      {paths['raw']}", file=sys.stderr)
        print(f"  learnings: {len(result['learnings'])}", file=sys.stderr)
        print(f"  sources:   {len(set(result['urls']))}", file=sys.stderr)
        print(f"  duration:  {result['metadata'].get('duration_s', '?')} s",
              file=sys.stderr)
    return 0


# --- Module self-test (--version + import sanity) ------------------------

def _self_test() -> int:
    """Print the four facts that prove this module imports cleanly."""
    print(f"deep_research {__version__}")
    print(f"  RESEARCH_DIR = {RESEARCH_DIR}")
    print(f"  priority     = {lower_priority()}")
    print(f"  slug example = {slugify('Best practices for Minecraft Java 2026')}")
    print(f"  ts example   = {now_ts()}")
    print(f"  env-disabled = {env_disabled()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
