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

__version__ = "0.1.0"


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


class ExtractedLearnings(TypedDict):
    learnings: list[str]
    followUpQuestions: list[str]


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

def acquire_lock() -> str:
    """Cooperative lock with 4-h stale-reclaim. Returns:
      "acquired"        — caller proceeds
      "stale-reclaimed" — old lock detected + reclaimed; caller proceeds
      "held"            — another live run holds the lock; caller MUST abort
      "error:<msg>"     — IO error; fail-open, caller proceeds with warning
    """
    try:
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        if LOCK_PATH.exists():
            try:
                age = time.time() - LOCK_PATH.stat().st_mtime
            except OSError:
                age = LOCK_STALE_SECONDS + 1
            if age < LOCK_STALE_SECONDS:
                return "held"
            try:
                LOCK_PATH.unlink()
            except OSError:
                pass
            _write_lock_payload()
            return "stale-reclaimed"
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

    args: list[str] = [
        str(cmd_path),
        "-p",
        "--disable-slash-commands",
        "--disallowed-tools", "*",
        "--append-system-prompt", system,
        augmented_user,
    ]

    model = env_str("CLAUDEPP_RESEARCH_MODEL")
    if model:
        args[1:1] = ["--model", model]

    try:
        r = subprocess.run(
            args, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
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
    args = sys.argv[1:]
    if not args or args[0] in ("--version", "-V"):
        raise SystemExit(_self_test())
    print(
        "deep_research: Wave-1 module exposes constants + governance helpers "
        "(slugify, now_ts, lower_priority, acquire_lock). Use as a library; "
        "the CLI driver ships in Paso 1.9 of "
        "vault/plans/deep-research-agent-2026-05-23.md.",
        file=sys.stderr,
    )
    raise SystemExit(0)
