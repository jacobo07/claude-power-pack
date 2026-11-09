"""Mission self-heal remedies (spec vault/specs/mission-self-heal.md).

Repairs only what is provably safe, before a launch or at a held alignment, and tells the Owner about the rest:
  * phantom_dirty(): dirty paths that differ only by line endings and that a fast-forward does not touch.
  * preflight(): workspace trust for cwds under host-local `trust_roots`; reject unrunnable `.mcp.json` servers.
  * notify_incident(): tell the Owner per liveness-incident key until a channel accepts it (bounded retries).
Every function returns facts and never raises; the caller decides. Kill switch: CPP_MISSION_SELF_HEAL=off.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402  (state_dir, ledger)

NOTIFY_MAX_ATTEMPTS = 3        # failed channel attempts per incident key before we stop retrying
WRITE_MAX_ATTEMPTS = 3         # re-reads when ~/.claude.json moved under us between read and replace
_NOT_DELIVERED = ("no channel", "telegram failed", "notify failed")


def enabled() -> bool:
    return (os.environ.get("CPP_MISSION_SELF_HEAL") or "").strip().lower() not in ("off", "0", "false", "no")


def _norm(p: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(p))).replace("\\", "/").rstrip("/")


# ---------------------------------------------------------------- phantom dirt
def _porcelain_paths(git, cwd: str) -> set[str] | None:
    """Every tracked path `status` calls dirty (index OR worktree), unquoted. None if unreadable."""
    r = git(cwd, "-c", "core.quotePath=false", "status", "--porcelain", "-z", "--untracked-files=no")
    if r.returncode != 0:
        return None
    out, parts, i = set(), (r.stdout or "").split("\0"), 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        out.add(entry[3:])
        if entry[0] in "RC" or entry[1] in "RC":   # a rename/copy carries its source as the next field
            if i < len(parts):
                out.add(parts[i])
            i += 1
    return out


def phantom_dirty(git, cwd: str, cwd_head: str, work_dir_head: str) -> list[str] | None:
    """The dirty tracked paths in `cwd` if EVERY one is phantom, else None.

    Phantom = the worktree AND the index differ from HEAD by line endings only, and the fast-forward from cwd_head to
    work_dir_head does not change the path. The phantom set must equal everything `status` calls dirty, so a staged
    change or a path git would print quoted can never slip through. `git` is git(path, *args) -> CompletedProcess.
    Measured 2026-11-09 (m-9444639a3c78): a blob committed `-text` under `text eol=lf` is re-normalised on every read,
    so `status --porcelain` is never empty and the mission was held 21 h on a file nobody edited."""
    try:
        r = git(cwd, "-c", "core.quotePath=false", "diff", "--name-only", "-z", "HEAD")
        if r.returncode != 0:
            return None
        paths = sorted(p for p in (r.stdout or "").split("\0") if p)
        if not paths or set(paths) != _porcelain_paths(git, cwd):
            return None
        # Every name must be a real file. The caller's runner decodes git's output with the locale (cp1252 on
        # Windows turns `café.md` into `cafÃ©.md`), and a pathspec that matches nothing makes `diff --quiet` exit 0:
        # a mangled name would pass every check below without comparing anything. A deletion is a real change too.
        if not all((Path(cwd) / p).is_file() for p in paths):
            return None
        lit = ("--literal-pathspecs",)
        for args in (("diff", "--quiet", "--ignore-cr-at-eol", "HEAD"),             # worktree vs HEAD
                     ("diff", "--cached", "--quiet", "--ignore-cr-at-eol", "HEAD"),  # index vs HEAD
                     ("diff", "--quiet", cwd_head, work_dir_head)):                  # the ff leaves them alone
            if git(cwd, *lit, *args, "--", *paths).returncode != 0:
                return None
        return paths
    except Exception:  # noqa: BLE001 -- an unanswered question is never phantom
        return None


# ---------------------------------------------------------------- preflight
def _roots_file() -> Path:
    return lr.state_dir() / "mission-self-heal.json"


def trust_roots() -> list[str]:
    """Host-local, never in the shared repo. Missing/unreadable = no roots. An empty or filesystem-root entry
    (`/`, `C:\\`) is ignored: it would trust every path."""
    try:
        data = json.loads(_roots_file().read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for r in data.get("trust_roots", []) if isinstance(data, dict) else []:
        if not isinstance(r, str) or not r.strip() or not os.path.isabs(r.strip()):
            continue   # a relative entry (on Linux `C:\` is one) would resolve under whatever cwd the sweep has
        n = _norm(r)
        if n and n.count("/") >= 2 and not (len(n) <= 3 and n.endswith(":")):
            out.append(n)
    return out


def _claude_json() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(base) / ".claude.json" if base else Path.home() / ".claude.json"


def _project_key(cfg: dict, cwd: str) -> str:
    """The projects key Claude uses for this cwd: an existing key that normalises equal, else cwd as given."""
    want = _norm(cwd)
    for k in (cfg.get("projects") or {}):
        if _norm(k) == want:
            return k
    return str(cwd).replace("\\", "/") if os.name == "nt" else str(cwd)


def _stamp(path: Path) -> tuple[int, int]:
    st = os.stat(path)
    return st.st_mtime_ns, st.st_size


def _write_merged(path: Path, mutate) -> dict:
    """Read, mutate, write atomically, read back. Keys we do not model are preserved. If the file moved between our
    read and our replace (the Claude CLI rewrites it), start again from the new content rather than overwrite it."""
    for _ in range(WRITE_MAX_ATTEMPTS):
        stamp = _stamp(path)
        cfg = json.loads(path.read_text(encoding="utf-8"))
        mutate(cfg)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(cfg, fh, indent=2)
            try:
                os.chmod(tmp, os.stat(path).st_mode & 0o777)
            except OSError:
                pass
            if _stamp(path) != stamp:
                os.unlink(tmp)
                continue
            os.replace(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        return json.loads(path.read_text(encoding="utf-8"))
    raise RuntimeError(f"{path} kept changing under the write ({WRITE_MAX_ATTEMPTS} attempts)")


def _unrunnable_stdio(server: dict, cwd: str) -> bool:
    """True only for a stdio server whose command provably cannot start here. URL servers, `${...}` expansions and
    anything we cannot judge are False: never reject what might run."""
    if not isinstance(server, dict) or "command" not in server:
        return False
    if (server.get("type") or "stdio") != "stdio":
        return False
    command = str(server.get("command") or "")
    if not command or "${" in command or "$" in command:
        return False
    p = Path(command)
    if p.is_absolute() or "/" in command or "\\" in command:
        return not (p if p.is_absolute() else Path(cwd) / p).exists()
    return shutil.which(command) is None


def preflight(rec: dict, ledger=None, notifier=None) -> list[dict]:
    """Repair the host setup a headless worker cannot answer, before it is launched. Returns the rows it ledgered."""
    if not enabled():
        return []
    mid, cwd = rec.get("mission_id", "?"), rec.get("cwd") or ""
    log = ledger or (lambda event, **kw: lr.ledger_append(mid, event, mission_id=mid, **kw))
    rows: list[dict] = []

    def row(event, **kw):
        rows.append({"event": event, **kw})
        log(event, **kw)

    path = _claude_json()
    try:
        if not path.is_file() or not cwd:
            return rows
        cfg = json.loads(path.read_text(encoding="utf-8"))
        key = _project_key(cfg, cwd)
        proj = (cfg.get("projects") or {}).get(key) or {}

        # Trust: only under a host-local root (Owner 2026-11-09, "Sí, solo en lista").
        if proj.get("hasTrustDialogAccepted") is not True:
            want = _norm(cwd)
            if any(want == r or want.startswith(r + "/") for r in trust_roots()):
                def set_trust(c):
                    c.setdefault("projects", {}).setdefault(key, {})["hasTrustDialogAccepted"] = True
                back = _write_merged(path, set_trust)
                ok = (back.get("projects") or {}).get(key, {}).get("hasTrustDialogAccepted") is True
                row("remedy_applied" if ok else "remedy_error", kind="trust", cwd=cwd, readback=ok)
                proj = (back.get("projects") or {}).get(key) or {}
            else:
                row("remedy_refused", kind="trust", cwd=cwd, why="cwd is not under a host-local trust root")

        # MCP: reject stdio servers that cannot run on this host; never approve one that might.
        mcp_file = Path(cwd) / ".mcp.json"
        if mcp_file.is_file():
            servers = (json.loads(mcp_file.read_text(encoding="utf-8")).get("mcpServers") or {})
            decided = set(proj.get("enabledMcpjsonServers") or []) | set(proj.get("disabledMcpjsonServers") or [])
            pending = {n: s for n, s in servers.items() if n not in decided}
            dead = [n for n, s in pending.items() if _unrunnable_stdio(s, cwd)]
            live = [n for n in pending if n not in dead]
            if dead:
                def disable(c):
                    p = c.setdefault("projects", {}).setdefault(key, {})
                    p["disabledMcpjsonServers"] = sorted(set(p.get("disabledMcpjsonServers") or []) | set(dead))
                    p.setdefault("enabledMcpjsonServers", [])
                back = _write_merged(path, disable)
                got = set((back.get("projects") or {}).get(key, {}).get("disabledMcpjsonServers") or [])
                row("remedy_applied" if set(dead) <= got else "remedy_error", kind="mcp", disabled=dead,
                    why="stdio command does not resolve on this host")
            if live:
                why = f"project .mcp.json servers awaiting approval (may run here, never auto-approved): {live}"
                row("remedy_refused", kind="mcp", servers=live, why=why)
                notify_incident(mid, f"mcp-pending:{','.join(sorted(live))}", f"{why}; cwd {cwd}",
                                ledger=log, notifier=notifier)
    except Exception as exc:  # noqa: BLE001 -- a failed repair never blocks the launch
        row("remedy_error", kind="preflight", why=f"{type(exc).__name__}: {exc}"[:300])
    return rows


# ---------------------------------------------------------------- notification
def notify_incident(mid: str, key: str, why: str, ledger=None, notifier=None) -> str | None:
    """Tell the Owner about (mission, key) until a channel accepts it. A failed or unconfigured channel is ledgered
    `incident_notify_failed` and retried on the next call, at most NOTIFY_MAX_ATTEMPTS times. Returns the channel
    result, or None when off / already delivered / attempts exhausted. Never raises."""
    if not enabled():
        return None
    log = ledger or (lambda event, **kw: lr.ledger_append(mid, event, mission_id=mid, **kw))
    try:
        mine = [e for e in lr.ledger_events(mid) if e.get("key") == key]
    except Exception:  # noqa: BLE001
        mine = []
    if any(e.get("event") == "incident_notified" for e in mine):
        return None
    if sum(1 for e in mine if e.get("event") == "incident_notify_failed") >= NOTIFY_MAX_ATTEMPTS:
        return None
    text = f"Mission {mid} needs attention: {why}"[:3900]
    try:
        if notifier is not None:
            result = str(notifier(text))
        else:
            import mission_topup
            result = str(mission_topup.notify(text))
    except Exception as exc:  # noqa: BLE001
        result = f"notify failed: {type(exc).__name__}"
    delivered = not result.lower().startswith(_NOT_DELIVERED)
    log("incident_notified" if delivered else "incident_notify_failed", key=key, channel=result[:120])
    return result
