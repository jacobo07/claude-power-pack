"""CPP-owned controls that correct the Ruflo HOLD list before any install (BCAP-2 Phase 9, CPP-RUFLO-10/11/15).

Every function returns None when the input is acceptable and a reason string when it must be refused (fail closed:
anything unparseable, unknown or absent is a refusal, never an acceptance). Pure functions, no network, no I/O except
`path_error`, which resolves symlinks. Ruflo is a candidate provider behind this gateway; none of its own checks is
trusted to be reached (a source fix is not evidence that the published package or the live path carries it).

    python3 tools/test_bcap2_ruflo.py     # both-poles gate, plus a permissive-mutant drill for every control
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

# --- GHSA-5pxg-x8g8-fw4j (critical): browser_open forwarded caller-chosen Chromium flags --------------------------
LAUNCH_ALLOW = frozenset({"--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                          "--disable-extensions", "--mute-audio", "--hide-scrollbars", "--incognito"})


def url_error(url) -> str | None:
    if not isinstance(url, str) or not url or url.startswith("-"):
        return "url must be a non-empty string that does not start with '-'"
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", url) and not re.match(r"^(https?://|about:blank$)", url, re.I):
        # scheme-less "localhost:3000" also matches; accept only host:port shapes
        if not re.match(r"^[A-Za-z0-9.-]+:\d+(/|$)", url):
            return f"scheme not allowed: {url.split(':', 1)[0]}"
    return None


def browser_args_error(args) -> str | None:
    if args is None:
        return None
    if not isinstance(args, list) or any(not isinstance(a, str) for a in args):
        return "args must be a list of strings"
    for a in args:
        if a not in LAUNCH_ALLOW:
            return f"launch arg not allowed: {a[:60]!r}"
    return None


def tool_call_error(tool: str, params: dict) -> str | None:
    """Gateway check for browser-class tools: no option smuggling through any string value."""
    if tool.startswith("browser_"):
        e = browser_args_error(params.get("args"))
        if e:
            return e
        if "url" in params:
            e = url_error(params["url"])
            if e:
                return e
        for k, v in params.items():
            if k not in ("args", "url") and isinstance(v, str) and v.startswith("-"):
                return f"value for {k!r} must not start with '-'"
    return None


# --- GHSA-vqpp-qh58-2p7h: memory_export / memory_import arbitrary paths -----------------------------------------
def path_error(path, root) -> str | None:
    try:
        base = Path(root).resolve(strict=True)
        target = Path(os.path.realpath(os.path.join(str(base), str(path))))
    except (OSError, ValueError, TypeError):
        return "path unresolvable"
    if "\x00" in str(path):
        return "NUL in path"
    if target != base and base not in target.parents:
        return "path escapes the export root"
    return None


# --- GHSA-6rwv-52g2-vx7j: prototype pollution through __proto__ ids ----------------------------------------------
_POISON = {"__proto__", "constructor", "prototype"}


def keys_error(obj, _depth=0) -> str | None:
    if _depth > 32:
        return "nesting too deep"
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _POISON:
                return f"poisoned key {k!r}"
            e = keys_error(v, _depth + 1)
            if e:
                return e
    elif isinstance(obj, list):
        for v in obj:
            e = keys_error(v, _depth + 1)
            if e:
                return e
    return None


def json_text_error(text: str) -> str | None:
    """Parse with a hook so duplicate/poisoned keys are seen before any merge."""
    bad = []

    def hook(pairs):
        for k, _ in pairs:
            if k in _POISON:
                bad.append(k)
        return dict(pairs)
    try:
        json.loads(text, object_pairs_hook=hook)
    except (ValueError, RecursionError):
        return "unparseable json"
    return f"poisoned key {bad[0]!r}" if bad else None


# --- GHSA-8jjw-xqg5-7pvx: loopback bridge without token (CORS *, DNS rebinding) ----------------------------------
def loopback_request_error(host: str, origin, token, expected_token, allowed_hosts=("127.0.0.1:7777", "localhost:7777")):
    if not expected_token or not isinstance(expected_token, str) or len(expected_token) < 16:
        return "no server token configured: loopback is not authentication"
    if token != expected_token:
        return "token missing or wrong"
    if host not in allowed_hosts:
        return "Host header not allowed (DNS rebinding)"
    if origin not in (None, "") and origin == "*":
        return "wildcard origin refused"
    return None


# --- GHSA-hgp6-gm2j-hx55: SSRF through user-supplied MCP URLs -----------------------------------------------------
def ssrf_error(url, resolver=None) -> str | None:
    try:
        u = urlsplit(url)
    except ValueError:
        return "unparseable url"
    if u.scheme not in ("http", "https") or not u.hostname:
        return "scheme/host not allowed"
    if u.username or u.password:
        return "credentials in url"
    host = u.hostname.lower()
    cands = []
    try:
        cands.append(ipaddress.ip_address(host))
    except ValueError:
        if host == "localhost" or host.endswith((".localhost", ".internal", ".local")):
            return "internal hostname"
        if resolver is None:
            return "hostname not resolvable here: refused (fail closed)"
        try:
            cands = [ipaddress.ip_address(a) for a in resolver(host)]
        except (ValueError, OSError):
            return "resolution failed"
        if not cands:
            return "resolution empty"
    for ip in cands:
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return f"address not public: {ip}"
        if getattr(ip, "ipv4_mapped", None) and (ip.ipv4_mapped.is_private or ip.ipv4_mapped.is_loopback):
            return f"mapped private address: {ip}"
    return None


# --- GHSA-rx87-v2fr-76xf: repository files injected as user memory ----------------------------------------------
def memory_origin_error(entry: dict) -> str | None:
    if entry.get("origin") != "user":
        return f"origin {entry.get('origin')!r} may not be loaded as user memory (untrusted data)"
    return None


# --- GHSA-hmmg-9p82-2m6q: X-Forwarded-For bypasses per-IP limits -------------------------------------------------
def client_ip(peer: str, xff, trusted_proxies=()) -> str:
    """XFF is honoured only when the direct peer is a configured proxy, and then only its right-most untrusted hop."""
    if peer not in trusted_proxies or not xff:
        return peer
    hops = [h.strip() for h in xff.split(",") if h.strip()]
    for h in reversed(hops):
        if h not in trusted_proxies:
            return h
    return peer


# --- GHSA-jwwq-crgq-c4c7: federation peer forges an envelope origin ----------------------------------------------
def envelope_error(envelope: dict, authenticated_peer: str) -> str | None:
    if not authenticated_peer:
        return "no authenticated peer"
    if envelope.get("origin") != authenticated_peer:
        return "envelope origin does not match the authenticated peer"
    return None


# --- #3294: one mutable MCP session shared across clients --------------------------------------------------------
class PrincipalBinding:
    """Sessions are bound to the principal that opened them at creation; there is no ambient 'current' principal."""

    def __init__(self):
        self._owner: dict[str, str] = {}

    def open(self, session_id: str, principal: str) -> None:
        if not principal or session_id in self._owner:
            raise PermissionError("session exists or principal missing")
        self._owner[session_id] = principal

    def check(self, session_id: str, principal) -> str | None:
        if not principal:
            return "request carries no principal"
        o = self._owner.get(session_id)
        if o is None:
            return "unknown session"
        return None if o == principal else "session belongs to another principal"


# --- #4750: unsigned pattern downloads ---------------------------------------------------------------------------
def pattern_error(data: bytes, pins: dict, name: str, max_bytes=1_000_000) -> str | None:
    if not isinstance(data, (bytes, bytearray)) or len(data) > max_bytes:
        return "pattern missing or over the size cap"
    want = pins.get(name)
    if not want:
        return "pattern not in the hash-pinned allowlist (unsigned downloads are refused)"
    return None if hashlib.sha256(data).hexdigest() == want else "pattern digest mismatch"


# --- unsandboxed plugins / opt-in MCP policy: default deny -------------------------------------------------------
def plugin_error(manifest_sha256: str, allow: dict) -> str | None:
    return None if allow.get(manifest_sha256) else "plugin not on the hash allowlist (default deny)"


def mcp_tool_error(tool: str, policy) -> str | None:
    if not isinstance(policy, dict) or "allow" not in policy:
        return "no explicit MCP policy: default deny"
    return None if tool in policy["allow"] else f"tool {tool!r} not allowlisted"


# --- supply chain: lifecycle scripts, install envelope, audit, version coherence ---------------------------------
_RISKY = re.compile(r"npm\s+(i|install)\b[^;&|]*\s-g\b|npm\s+(i|install)\s+-g|curl[^|;]*\|\s*(ba)?sh|base64\s+-d|\beval\b|"
                    r"child_process|execSync|\bwget\b|\bsudo\b", re.I)
LIFECYCLE = ("preinstall", "install", "postinstall", "prepare", "prepublish")


def lifecycle_findings(pkg: dict) -> list:
    out = []
    for k in LIFECYCLE:
        v = (pkg.get("scripts") or {}).get(k)
        if v and _RISKY.search(v):
            out.append((k, v[:120]))
    return out


_SECRET = re.compile(r"(TOKEN|SECRET|KEY|PASSWORD|PASSWD|CREDENTIAL|AUTH|COOKIE|SESSION)", re.I)


def scrub_env(env: dict, sandbox_home: str) -> dict:
    """Minimal environment for the sandbox: no inherited secrets, HOME and XDG redirected into the sandbox."""
    out = {k: v for k, v in env.items() if k in ("PATH", "LANG", "LC_ALL") and not _SECRET.search(k)}
    out.update({"HOME": sandbox_home, "XDG_CONFIG_HOME": sandbox_home + "/.config", "XDG_CACHE_HOME": sandbox_home + "/.cache",
                "XDG_DATA_HOME": sandbox_home + "/.local/share", "npm_config_userconfig": sandbox_home + "/.npmrc",
                "npm_config_audit": "false", "npm_config_fund": "false", "npm_config_update_notifier": "false",
                "CI": "1", "CLAUDE_CONFIG_DIR": sandbox_home + "/.claude-none"})
    return out


def install_plan_error(plan: dict, real_home: str) -> str | None:
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(plan.get("version", ""))):
        return "version must be an exact x.y.z pin"
    if not re.fullmatch(r"sha512-[A-Za-z0-9+/=]{80,}", str(plan.get("integrity", ""))):
        return "integrity (sha512) missing or malformed"
    if not plan.get("ignore_scripts"):
        return "lifecycle scripts must be disabled (--ignore-scripts)"
    if plan.get("global"):
        return "global install refused"
    if not plan.get("lockfile"):
        return "no lockfile"
    sb = str(plan.get("sandbox_dir", ""))
    rh = os.path.realpath(real_home)
    if not sb or os.path.realpath(sb).startswith(os.path.join(rh, ".claude")) or os.path.realpath(sb) == rh:
        return "sandbox dir must be outside the real ~/.claude and not the home itself"
    if plan.get("registry") != "https://registry.npmjs.org/":
        return "registry must be the pinned public registry"
    if any(_SECRET.search(k) for k in (plan.get("env") or {})):
        return "secret-like variable in the install environment"
    if (plan.get("env") or {}).get("HOME") in (None, real_home):
        return "HOME must be redirected into the sandbox"
    return None


def audit_error(audit: dict | None, waivers=()) -> str | None:
    if not audit or "metadata" not in audit:
        return "UNMEASURED: no audit result (absence is not a clean bill)"
    v = (audit["metadata"] or {}).get("vulnerabilities") or {}
    n = int(v.get("critical", 0)) + int(v.get("high", 0))
    return None if n == 0 or list(waivers) else f"{n} high/critical advisories unresolved and unwaived"


def version_coherence_error(versions: dict) -> str | None:
    """#3306 / @claude-flow/swarm not republished: the executing parts must agree with the wrapper's version."""
    want = versions.get("wrapper")
    stale = sorted(k for k, v in versions.items() if k != "wrapper" and v != want)
    return None if want and not stale else f"parts not at wrapper version {want}: {stale}"


CONTROLS = {n: f for n, f in dict(
    tool_call=tool_call_error, path=path_error, keys=keys_error, json_text=json_text_error, loopback=loopback_request_error,
    ssrf=ssrf_error, memory_origin=memory_origin_error, envelope=envelope_error, pattern=pattern_error, plugin=plugin_error,
    mcp_tool=mcp_tool_error, install_plan=install_plan_error, audit=audit_error, coherence=version_coherence_error).items()}
