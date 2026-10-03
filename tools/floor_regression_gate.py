#!/usr/bin/env python3
"""Floor regression gate (incremental-cognition pillar K): a material rise in the startup floor is visible in review.

The startup floor is everything the model is handed before the first user turn. A session transcript records it:
every row before the first `assistant` row (the "startup window") holds the memory files, the skill and agent
listings, the hook output, the system prompt parts and the environment. This gate classifies each of those
components by LAYER (what it is) and SCOPE (who it applies to), writes a committed reference, and fails a later
transcript whose floor rose materially against that reference without an explanation.

    python3 tools/floor_regression_gate.py --write-reference OUT --transcript T.jsonl [--replace] [--json]
    python3 tools/floor_regression_gate.py --check --reference REF.json --transcript T.jsonl [--json]

Measurement source (one of): --transcript T.jsonl | --project-dir DIR (the newest top-level *.jsonl) |
--session SID (located by the owner's listing_floor_probe.transcript) | --probe [--cwd DIR] (one fresh headless
session through listing_floor_probe.main; costs one session, never started from a test).

Exit codes: 0 within bound, 1 material unexplained rise, 2 UNMEASURABLE (never 0 on anything not measured).
UNMEASURABLE reasons include: window_line_unparseable (a startup-window line is not a JSON object), layer_absent:<layer>
(a reference layer of >= 1,000 chars has no component in the checked floor), not_comparable, reference_invalid.

Classification table (layer key / scope / chars):
  instructions file, basename CLAUDE.md, type User ........ memory_global   / universal / len(content)
  instructions file, CLAUDE.md|CLAUDE.local.md, Project|Local  memory_project  / project   / len(content)
  instructions file under /.claude/rules/ ............... rules           / by file type
  any other instructions file ........................... other:instructions / by file type
  skill_listing (per entry; header lines) ............... skill_listing   / by name (below); header unattributed
  agent_listing_delta (per added type) .................. other:agent_listing_delta / by name (below)
  hook_additional_context (per element) ................. hook_context:<event>:<name> / by producing hook (below)
  hook_system_message ................................... hook_system_message:<event>:<name> / by producing hook
  prompt_snapshot (per part, identified by digest) ...... system_prompt    / unattributed
  environment, model, date, auto_mode, command_permissions, credential_org, remote_session_change,
  session_context ....................................... other:<type>     / harness (origin provable by type)
  every other attachment type ........................... other:<type>     / unattributed
  user rows and `file` attachments ...................... EXCLUDED (prompt-driven)
  hook_success rows ..................................... EXCLUDED (raw stdout, counted only)
File type -> scope: User universal; Project and Local project; anything else unattributed. Scope is never guessed:
a component whose origin cannot be proved is `unattributed` and stays under the 1,000-char rule.

Hook / skill / agent attribution (every lookup is a read; the basis is recorded as `scope_basis`):
  hook element -> the hook_success row of the same hookEvent whose stdout JSON carries the element
     (hookSpecificOutput.additionalContext, or systemMessage; for additionalContext also plain-text stdout equal to
     the element) names the command. The component source is the stable key
     `hook:<sha256(command)[:16]>[:<script basename>]`; the command text is never stored or printed.
     `${CLAUDE_PLUGIN_ROOT}` in the command: universal (plugin). Else the settings file REGISTERING the command
     decides, never where its script lives: only <cwd>/.claude/settings[.local].json -> project, only
     <install_home>/.claude/settings[.local].json -> universal, both or neither -> unattributed.
  no producing row -> unattributed (basis event_uncorrelated): the event's registrations never prove who produced the
     element. A hook that prints plain text is correlated by its stdout. Several producing commands -> unattributed.
  skill / agent entry -> a file under <cwd>/.claude (skills/<n>/SKILL.md, commands/<n>.md, commands/<ns>/<rest>.md,
     agents/**/<n>.md) -> project; under <install_home>/.claude -> universal; both -> unattributed; neither: a `ns:rest`
     plugin name -> universal, anything else (a harness built-in) -> unattributed. A name that could leave its
     directory is unattributed.
  unreadable or malformed settings -> unattributed (unknown, never empty). A cwd or install_home that is not a directory
  on the measuring host -> every one of the above is unattributed (absent is not zero).

Materiality (a rise is a positive delta of one (layer, scope) row against the reference):
  layer_3pct   delta >= 3 % of the reference total_chars
  universal_1k delta >= 1,000 chars in a universal or unattributed row
The startup window is read once; the reference records window_sha256 / window_rows (the raw lines before the first
assistant row, newline-joined), so a later check can say whether it measured the same window.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE_REL = "vault/programs/incremental-cognition/floor/reference.json"
SCHEMA = "floor-reference/1"
LAYER_PCT = 0.03
TOTAL_PCT = 0.03
TOKENS_PCT = 0.03
UNIVERSAL_MIN_CHARS = 1000
SCOPES = ("universal", "project", "harness", "unattributed")
SCOPES_UNDER_1K = ("universal", "unattributed")
HARNESS_TYPES = ("environment", "model", "date", "auto_mode", "command_permissions", "credential_org",
                 "remote_session_change", "session_context")
EXIT_OK, EXIT_RISE, EXIT_UNMEASURABLE = 0, 1, 2
_USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


class Unmeasurable(Exception):
    """A comparison that could not be made. Always mapped to exit 2 with a named reason."""

    def __init__(self, reason, detail="", probe_error=None):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail
        self.probe_error = probe_error


# --------------------------------------------------------------------------- helpers
def host_plane():
    host = socket.gethostname()
    return "gex44" if "gex44" in host.lower() else host


def _jdump(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _chars(value):
    return len(value) if isinstance(value, str) else len(_jdump(value))


def _digest12(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _norm_path(value):
    return str(value).replace("\\", "/")


def _num(value):
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def load_redactor():
    """modules.secret_firewall.redact, or Unmeasurable: nothing may leave the process unredacted (HR-SECRET-002)."""
    try:
        try:
            from modules.secret_firewall import redact
        except ImportError:
            sys.path.insert(0, str(ROOT))
            from modules.secret_firewall import redact
    except Exception as exc:  # noqa: BLE001 -- any import failure refuses; the class name is the whole detail
        raise Unmeasurable("secret_firewall_unavailable", exc.__class__.__name__)
    return redact


def redact_obj(obj, redact):
    """redact() applied to every string leaf and key; structure and numbers are untouched."""
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, list):
        return [redact_obj(v, redact) for v in obj]
    if isinstance(obj, dict):
        return {redact_obj(k, redact) if isinstance(k, str) else k: redact_obj(v, redact) for k, v in obj.items()}
    return obj


# --------------------------------------------------------------------------- reading the window
def read_window(path):
    """-> (rows before the first assistant row, that assistant row or None, raw window lines as bytes). A line inside the
    window that is not a JSON object is UNMEASURABLE (window_line_unparseable): a floor read around a missing line is
    undercounted, and the window hash would still move. Lines after the first assistant row are never read."""
    p = Path(path)
    if not p.exists():
        raise Unmeasurable("no_transcript", "no such file")
    if not p.is_file():
        raise Unmeasurable("unreadable", "not a regular file")
    rows, raw_lines, assistant, parsed, bad = [], [], None, 0, 0
    try:
        with open(p, "rb") as fh:
            for line in fh:
                raw = line[:-1] if line.endswith(b"\n") else line
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw.decode("utf-8", errors="replace"))
                except ValueError:
                    row = None
                if isinstance(row, dict):
                    parsed += 1
                    if row.get("type") == "assistant":
                        assistant = row
                        break
                    rows.append(row)
                else:
                    bad += 1   # a line the floor cannot be read from: counted, never dropped silently (CR-01)
                raw_lines.append(raw)
    except OSError as exc:
        raise Unmeasurable("unreadable", exc.__class__.__name__)
    if parsed == 0:
        raise Unmeasurable("unreadable", "no parseable JSON line")
    if bad:
        raise Unmeasurable("window_line_unparseable",
                           f"{bad} line(s) before the first assistant row are not JSON objects; the floor read from "
                           "this window would be undercounted")
    return rows, assistant, raw_lines


def window_digest(raw_lines):
    """THE one place the startup-window pin is computed: (sha256 hex over the raw lines newline-joined, row count)."""
    return hashlib.sha256(b"\n".join(raw_lines)).hexdigest(), len(raw_lines)


# --------------------------------------------------------------------------- attribution (reads only)
PLUGIN_ROOT_TOKEN = "${CLAUDE_PLUGIN_ROOT}"
_SETTINGS_FILES = ("settings.json", "settings.local.json")


def host_has(path):
    """True when `path` is an existing directory on THIS host. The one seam behind every filesystem attribution: a
    transcript measured elsewhere (a laptop path read on GEX44) must never be attributed from what happens to be here."""
    if not path:
        return False
    try:
        return os.path.isdir(str(path))
    except (OSError, ValueError):
        return False


def registrations(settings_path):
    """{event: set(command strings)} from one settings file. Missing file -> {} (measured empty); unreadable or
    malformed -> None (unknown, never empty)."""
    p = Path(settings_path)
    try:
        if not p.exists():
            return {}
        with open(p, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict):
        return None
    hooks = doc.get("hooks")
    if hooks is None:
        return {}
    if not isinstance(hooks, dict):
        return None
    regs = {}
    for event, matchers in hooks.items():
        if not isinstance(matchers, list):
            return None
        for m in matchers:
            for h in (m.get("hooks") if isinstance(m, dict) else None) or []:
                if isinstance(h, dict) and isinstance(h.get("command"), str):
                    regs.setdefault(str(event), set()).add(h["command"])
    return regs


def _merge_regs(parts):
    merged = {}
    for part in parts:
        if part is None:
            return None
        for event, cmds in part.items():
            merged.setdefault(event, set()).update(cmds)
    return merged


class AttributionContext:
    """What scope attribution may read: the transcript's cwd and install_home, and only when both exist on this host.
    Settings registrations are read once per context (one measure() call)."""

    def __init__(self, cwd=None, install_home=None):
        self.cwd = str(cwd) if cwd else None
        self.install_home = str(install_home) if install_home else None
        self.available = host_has(self.cwd) and host_has(self.install_home)
        self._regs = {}
        self._files = {}
        self._agents = {}

    def is_file(self, path):
        """Path.is_file, once per path per context (a listing holds hundreds of names)."""
        if path not in self._files:
            try:
                self._files[path] = Path(path).is_file()
            except (OSError, ValueError):
                self._files[path] = False
        return self._files[path]

    def agent_names(self, base):
        """Stems of every *.md under <base>/.claude/agents (nested), scanned once. os.walk never follows a directory link."""
        if base not in self._agents:
            names = set()
            for _dp, _dns, fns in os.walk(Path(base) / ".claude" / "agents"):
                names.update(f[:-3] for f in fns if f.endswith(".md"))
            self._agents[base] = names
        return self._agents[base]

    def _side(self, name, base):
        if name not in self._regs:
            self._regs[name] = _merge_regs(registrations(Path(base) / ".claude" / f) for f in _SETTINGS_FILES)
        return self._regs[name]

    def project_regs(self):
        return self._side("project", self.cwd)

    def user_regs(self):
        return self._side("user", self.install_home)


UNAVAILABLE = AttributionContext()


def _ctx(ctx):
    return ctx if isinstance(ctx, AttributionContext) else UNAVAILABLE


_SCRIPT_EXTS = (".js", ".mjs", ".cjs", ".ts", ".py", ".sh", ".bash", ".cmd", ".bat", ".ps1", ".rb", ".pl")
_BASENAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _script_basename(cmd):
    """The basename of the first script-looking token of a hook command (an extension from _SCRIPT_EXTS), or None.
    Flags and `NAME=value` tokens are skipped; nothing but a plain file name can come back (no argument, no path)."""
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        tokens = cmd.split()
    for tok in tokens:
        if tok.startswith("-") or ("=" in tok and "/" not in tok.split("=", 1)[0]):
            continue
        base = _norm_path(tok).rstrip("/").rsplit("/", 1)[-1]
        if base.lower().endswith(_SCRIPT_EXTS) and _BASENAME_RE.match(base):
            return base
    return None


def hook_source_key(cmd):
    """The component source of a hook (CR-02): `hook:` + sha256(command)[:16] and, at most, the script basename. The
    command text itself is NEVER stored: it can carry credentials the redactor does not recognise (env assignments,
    quoted flags), and matching between a reference and a check needs only a stable key."""
    key = "hook:" + hashlib.sha256(cmd.encode("utf-8")).hexdigest()[:16]
    base = _script_basename(cmd)
    return f"{key}:{base}" if base else key


def command_scope(cmd, ctx):
    """-> (scope, basis) for one registered hook command. Project needs a project registration and no user one."""
    ctx = _ctx(ctx)
    if not ctx.available:
        return "unattributed", "not_on_this_host"
    if PLUGIN_ROOT_TOKEN in cmd:
        return "universal", "plugin"
    proj, user = ctx.project_regs(), ctx.user_regs()
    if proj is None or user is None:
        return "unattributed", "unknown_settings"
    in_proj = any(cmd in cmds for cmds in proj.values())
    in_user = any(cmd in cmds for cmds in user.values())
    if in_proj and in_user:
        return "unattributed", "ambiguous"
    if in_proj:
        return "project", "project_settings"
    if in_user:
        return "universal", "user_settings"
    return "unattributed", "no_registration"


def correlate_hook(element, event, field, window_rows):
    """The commands of hook_success rows (same hookEvent, never hookName) whose decoded stdout carries `element`:
    hookSpecificOutput.additionalContext for field additionalContext, the top-level key for systemMessage."""
    found = set()
    for row in window_rows:
        a = row.get("attachment") if isinstance(row, dict) else None
        if not isinstance(a, dict) or a.get("type") != "hook_success" or a.get("hookEvent") != event:
            continue
        cmd, stdout = a.get("command"), a.get("stdout")
        if not isinstance(cmd, str) or not isinstance(stdout, str):
            continue
        try:
            doc = json.loads(stdout)
        except ValueError:
            # a hook that prints plain text: for additionalContext the whole stdout is the added context
            if field == "additionalContext" and isinstance(element, str) and stdout.strip() == element.strip():
                found.add(cmd)
            continue
        if not isinstance(doc, dict):
            continue
        if field == "additionalContext":
            spec = doc.get("hookSpecificOutput")
            value = spec.get(field) if isinstance(spec, dict) else None
        else:
            value = doc.get(field)
        if value is not None and value == element:
            found.add(cmd)
    return found


def uncorrelated_scope(event, ctx):
    """-> (scope, basis) for a hook element no hook_success row produced. Always unattributed (WR-02): which settings
    file registers the EVENT says nothing about who produced THIS element (a plugin hook is registered in neither), so the
    event alone can never prove project or universal; the element stays under the 1,000-char rule."""
    return "unattributed", "event_uncorrelated"


def hook_scope(element, event, field, ctx, window_rows):
    """-> (scope, source, basis) for one hook-produced element. Exactly one producing command decides; several are
    ambiguous; none falls back to the event's registrations."""
    cmds = correlate_hook(element, event, field, window_rows)
    if len(cmds) == 1:
        cmd = next(iter(cmds))
        scope, basis = command_scope(cmd, ctx)
        return scope, hook_source_key(cmd), basis
    if len(cmds) > 1:
        return "unattributed", f"ambiguous:{event}", "ambiguous"
    scope, basis = uncorrelated_scope(event, ctx)
    return scope, f"event:{event}", basis


def _name_parts(name):
    """The ':'-separated parts of a skill / agent name, or None when any part could leave its directory."""
    parts = name.split(":")
    if not all(p and p not in (".", "..") and not re.search(r"[\\/\x00]", p) for p in parts):
        return None
    return parts


def _named_file_exists(kind, name, parts, base, ctx):
    claude = Path(base) / ".claude"
    if kind == "agent":
        return name in ctx.agent_names(base)
    return (ctx.is_file(claude / "skills" / name / "SKILL.md")
            or ctx.is_file(claude / "commands" / (os.sep.join(parts) + ".md")))


def scope_for_name(kind, name, ctx):
    """-> (scope, basis) for a skill or agent entry. A file under <cwd>/.claude is project, under <install_home>/.claude
    universal, both unattributed. A ns:rest name found in neither is a plugin namespace: universal. Reads only."""
    ctx = _ctx(ctx)
    if not ctx.available:
        return "unattributed", "not_on_this_host"
    parts = _name_parts(name)
    if parts is None:
        return "unattributed", "bad_name"
    in_proj = _named_file_exists(kind, name, parts, ctx.cwd, ctx)
    in_user = _named_file_exists(kind, name, parts, ctx.install_home, ctx)
    if in_proj and in_user:
        return "unattributed", "ambiguous"
    if in_proj:
        return "project", "project_file"
    if in_user:
        return "universal", "install_file"
    if len(parts) > 1:
        return "universal", "plugin_namespace"
    return "unattributed", "no_file"


# --------------------------------------------------------------------------- classification
def scope_for_instruction(file_type):
    if file_type == "User":
        return "universal"
    if file_type in ("Project", "Local"):
        return "project"
    return "unattributed"


def scope_for_system_prompt_part(part_text):
    """A system prompt part's origin is not provable by type: output styles, appended prompts and plugin text land
    here. It is never `harness`; it is `unattributed` and so stays under the 1,000-char rule."""
    return "unattributed"


def scope_key(component):
    """THE scope-split seam: compare attributes every delta through it."""
    return component["scope"]


def _instruction_layer(path, file_type):
    p = _norm_path(path)
    base = p.rsplit("/", 1)[-1]
    if base == "CLAUDE.md" and file_type == "User":
        return "memory_global", "universal"
    if base in ("CLAUDE.md", "CLAUDE.local.md") and file_type in ("Project", "Local"):
        return "memory_project", "project"
    if "/.claude/rules/" in p:
        return "rules", scope_for_instruction(file_type)
    return "other:instructions", scope_for_instruction(file_type)


def classify(rows, ctx=None):
    """-> (components [{layer, source, scope, scope_basis, chars}], excluded {...}, prompt_digest). Duplicate
    (layer, source) merge; a merge of two different scopes is unattributed, never the first one's."""
    ctx = _ctx(ctx)
    comps = []
    excluded = {"prompt_chars": 0, "file_chars": 0, "hook_success_rows": 0}
    pdig = hashlib.sha256()

    def add(layer, source, scope, chars, basis="origin_unprovable"):
        comps.append({"layer": layer, "source": source, "scope": scope, "scope_basis": basis, "chars": chars})

    for row in rows:
        rtype = row.get("type")
        if rtype == "user":
            content = (row.get("message") or {}).get("content")
            excluded["prompt_chars"] += _chars(content)
            pdig.update(_jdump(["user", content]).encode("utf-8"))
            continue
        if rtype != "attachment":
            continue
        a = row.get("attachment") or {}
        at = a.get("type")
        if at == "file":
            excluded["file_chars"] += _chars(a.get("content"))
            pdig.update(_jdump(["file", a.get("filename"), a.get("content")]).encode("utf-8"))
        elif at == "hook_success":
            excluded["hook_success_rows"] += 1
        elif at == "instructions":
            for f in a.get("files") or []:
                if not isinstance(f, dict):
                    continue
                layer, scope = _instruction_layer(f.get("path", ""), f.get("type"))
                add(layer, str(f.get("path", "")), scope, _chars(f.get("content") or ""), "file_type")
        elif at == "skill_listing":
            content = a.get("content") or ""
            parts = content.split("\n")
            lines = [p + "\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])
            current = "listing:header"
            for ln in lines:
                if ln.startswith("- "):
                    current = ln[2:].partition(": ")[0].rstrip("\r\n")
                if current == "listing:header":
                    add("skill_listing", current, "unattributed", len(ln), "header")
                else:
                    scope, basis = scope_for_name("skill", current, ctx)
                    add("skill_listing", current, scope, len(ln), basis)
        elif at == "agent_listing_delta":
            types, lines = a.get("addedTypes") or [], a.get("addedLines") or []
            for i, t in enumerate(types):
                scope, basis = scope_for_name("agent", str(t), ctx)
                add("other:agent_listing_delta", str(t), scope, _chars(lines[i]) if i < len(lines) else 0, basis)
            for i in range(len(types), len(lines)):
                add("other:agent_listing_delta", f"extra#{i}", "unattributed", _chars(lines[i]))
        elif at == "hook_additional_context":
            content = a.get("content")
            elems = content if isinstance(content, list) else [content]
            layer = f"hook_context:{a.get('hookEvent')}:{a.get('hookName')}"
            for el in elems:
                scope, source, basis = hook_scope(el, a.get("hookEvent"), "additionalContext", ctx, rows)
                add(layer, source, scope, _chars(el), basis)
        elif at == "hook_system_message":
            content = a.get("content")
            scope, source, basis = hook_scope(content, a.get("hookEvent"), "systemMessage", ctx, rows)
            add(f"hook_system_message:{a.get('hookEvent')}:{a.get('hookName')}", source, scope, _chars(content), basis)
        elif at == "prompt_snapshot":
            seen = {}
            for part in a.get("systemPrompt") or []:
                text = part if isinstance(part, str) else _jdump(part)
                src = "part:" + _digest12(text)
                seen[src] = seen.get(src, 0) + 1
                if seen[src] > 1:
                    src += f"#{seen[src]}"
                add("system_prompt", src, scope_for_system_prompt_part(text), len(text))
        elif at in HARNESS_TYPES:
            add(f"other:{at}", at, "harness", len(_jdump({k: v for k, v in a.items() if k != "type"})), "harness_type")
        elif at:
            add(f"other:{at}", str(at), "unattributed", len(_jdump({k: v for k, v in a.items() if k != "type"})))
    merged = {}
    for c in comps:
        key = (c["layer"], c["source"])
        if key in merged:
            merged[key]["chars"] += c["chars"]
            if merged[key]["scope"] != c["scope"]:
                merged[key]["scope"], merged[key]["scope_basis"] = "unattributed", "ambiguous"
        else:
            merged[key] = dict(c)
    return list(merged.values()), excluded, pdig.hexdigest()


def _initial_listing(rows):
    for row in rows:
        a = row.get("attachment") or {}
        if row.get("type") == "attachment" and a.get("type") == "skill_listing" and a.get("isInitial"):
            content = a.get("content") or ""
            return {"chars": len(content), "entries": sum(1 for ln in content.split("\n") if ln.startswith("- ")),
                    "skill_count": a.get("skillCount")}
    return None


def _aggregate_layers(components):
    agg = {}
    for c in components:
        key = (c["layer"], scope_key(c))
        agg[key] = agg.get(key, 0) + c["chars"]
    return [{"layer": k[0], "scope": k[1], "chars": v} for k, v in sorted(agg.items())]


def _install_home(path):
    p = Path(os.path.abspath(path))
    if p.parent.parent.name == "projects" and p.parent.parent.parent.name == ".claude":
        return str(p.parent.parent.parent.parent)
    return None


def first_call_tokens(assistant):
    """Model-visible tokens of the first assistant row, or None when that row is not a model call (absent, a
    `<synthetic>` row such as "Login expired", or zero usage). The owner's analyse() cannot tell these from a zero."""
    msg = (assistant or {}).get("message") or {}
    usage = msg.get("usage") or {}
    total = sum(_num(usage.get(k)) for k in _USAGE_KEYS)
    if assistant is not None and msg.get("model") != "<synthetic>" and total > 0:
        return total
    return None


def load_lfp():
    """The owner's wiki/tools/listing_floor_probe module (imported, never copied or edited)."""
    try:
        import listing_floor_probe as lfp
        return lfp
    except ImportError:
        pass
    bases = [ROOT] + [Path(p) for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
    for base in bases:
        tools = str(base / "wiki" / "tools")
        if os.path.isfile(os.path.join(tools, "listing_floor_probe.py")):
            if tools not in sys.path:
                sys.path.insert(0, tools)
            break
    try:
        import listing_floor_probe as lfp
    except Exception as exc:  # noqa: BLE001 -- the class name is the whole detail
        raise Unmeasurable("probe_unavailable", exc.__class__.__name__)
    return lfp


def probe_view(path):
    """What the owner's analyse() says about the same transcript: startup_tokens and the initial listing."""
    try:
        row = load_lfp().analyse(str(path), [])
    except Exception as exc:  # noqa: BLE001 -- a side view never fails the measurement
        return {"unavailable": exc.__class__.__name__}
    return {"startup_tokens": row.get("startup_tokens"), "listing": row.get("listing")}


def measure(path):
    rows, assistant, raw = read_window(path)
    listing = _initial_listing(rows)
    if listing is None:
        raise Unmeasurable("no_skill_listing", "the startup window holds no initial skill_listing")
    platform = cwd = None
    for r in rows:
        a = r.get("attachment") or {}
        if platform is None and a.get("type") == "environment":
            platform = (a.get("snapshot") or {}).get("platform")
            if cwd is None:
                cwd = (a.get("snapshot") or {}).get("workingDirectory")
    for r in rows:
        if r.get("cwd"):
            cwd = r["cwd"]
            break
    install_home = _install_home(path)
    components, excluded, prompt_digest = classify(rows, AttributionContext(cwd, install_home))
    total = first_call_tokens(assistant)
    if total is not None:
        tokens = {"status": "measured", "first_call_total": total, "prompt_digest": prompt_digest}
    else:
        tokens = {"status": "no_model_call", "first_call_total": None, "prompt_digest": prompt_digest}
    sha, nrows = window_digest(raw)
    return {
        "components": components,
        "layers": _aggregate_layers(components),
        "total_chars": sum(c["chars"] for c in components),
        "tokens": tokens,
        "skill_listing": listing,
        "excluded": excluded,
        "probe_view": probe_view(path),
        "provenance": {
            "plane": host_plane(), "platform": platform, "install_home": install_home, "cwd": cwd,
            "transcript": os.path.abspath(path), "session_id": Path(path).stem,
            "measured_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "first_call_at": (assistant or {}).get("timestamp"),
            "window_sha256": sha, "window_rows": nrows,
        },
    }


# --------------------------------------------------------------------------- measurement sources
SESSION_ID_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z-]{2,63}$")


def newest_transcript(directory):
    """-> (the newest `*.jsonl` directly in `directory` by mtime, ties broken by name; the candidate count).
    Sub-directories (sub-agent trees) and other extensions never count."""
    d = Path(directory)
    if not d.is_dir():
        raise Unmeasurable("no_transcript", "no such directory")
    stamped = []
    try:
        for p in d.glob("*.jsonl"):
            if p.is_file():
                stamped.append((p.stat().st_mtime_ns, p.name, p))
    except OSError as exc:
        raise Unmeasurable("unreadable", exc.__class__.__name__)
    if not stamped:
        raise Unmeasurable("no_transcript", "no *.jsonl directly in the directory")
    best = max(stamped, key=lambda t: (t[0], t[1]))
    return best[2], len(stamped)


def session_transcript(sid):
    """The transcript of session `sid`, located by the owner's own lookup. A malformed id is refused before any glob."""
    if not isinstance(sid, str) or not SESSION_ID_RE.match(sid):
        raise Unmeasurable("invalid_session_id", "the id must match [0-9A-Za-z][0-9A-Za-z-]{2,63}")
    found = load_lfp().transcript(sid)
    if not found:
        raise Unmeasurable("no_transcript", "no transcript for that session id under ~/.claude/projects")
    return found


PROBE_PROMPT = "Reply with the single word OK."


def _under(root, path):
    try:
        r, p = Path(root).resolve(), Path(path).resolve()
    except (OSError, RuntimeError):
        return False
    return r in p.parents


def resolve_probe_exe(lfp):
    """The claude executable --probe may start: env CPP_CLAUDE_EXE, else the owner's CLAUDE when it is a file, else
    `claude` on PATH. With the test fence on (CPP_FLOOR_GATE_TEST == "1") an executable outside
    CPP_FLOOR_GATE_TEST_ROOT is refused before anything is spawned: the fence only restricts, so it can never let a
    real claude run from a test."""
    exe = os.environ.get("CPP_CLAUDE_EXE")
    if exe:
        if not os.path.isfile(exe):
            raise Unmeasurable("claude_exe_not_found", "CPP_CLAUDE_EXE is not a file")
    elif os.path.isfile(lfp.CLAUDE):
        exe = lfp.CLAUDE
    else:
        exe = shutil.which("claude")
        if not exe:
            raise Unmeasurable("claude_exe_not_found", "no CPP_CLAUDE_EXE, no usable listing_floor_probe.CLAUDE, no claude on PATH")
    if os.environ.get("CPP_FLOOR_GATE_TEST") == "1":
        fence = os.environ.get("CPP_FLOOR_GATE_TEST_ROOT")
        if not fence or not _under(fence, exe):
            raise Unmeasurable("probe_fenced", "the test fence refuses an executable outside CPP_FLOOR_GATE_TEST_ROOT")
    return exe


def probe_transcript(cwd):
    """Start ONE fresh headless session through the owner's listing_floor_probe.main and return (transcript path,
    {label, session_id, cost_usd, exe}). The owner's CLAUDE / OUT globals and sys.argv are rebound for the call and
    restored in a finally; every way the probe can fail is Unmeasurable("probe_failed") naming the exception CLASS only
    (a message can carry argv or output)."""
    lfp = load_lfp()
    wd = str(cwd) if cwd else str(lfp.REPO)
    if not os.path.isdir(wd):
        raise Unmeasurable("probe_cwd_missing", "the probe working directory is not a directory")
    exe = resolve_probe_exe(lfp)
    label = "floor-gate-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    saved = (lfp.CLAUDE, lfp.OUT, list(sys.argv))
    out_buf, err_buf = io.StringIO(), io.StringIO()
    try:
        lfp.CLAUDE = exe
        if os.environ.get("CPP_FLOOR_PROBE_RESULTS"):
            lfp.OUT = os.environ["CPP_FLOOR_PROBE_RESULTS"]
        sys.argv = ["listing_floor_probe.py", "--label", label, "--prompt", PROBE_PROMPT, "--cwd", wd, "--max-turns", "1"]
        try:
            with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
                rc = lfp.main()
        except (SystemExit, OSError, subprocess.SubprocessError) as exc:
            raise Unmeasurable("probe_failed", exc.__class__.__name__, probe_error=exc.__class__.__name__)
    finally:
        lfp.CLAUDE, lfp.OUT = saved[0], saved[1]
        sys.argv = saved[2]
    if rc != 0:
        raise Unmeasurable("probe_failed", f"the probe returned {rc}")
    try:
        doc = json.loads(out_buf.getvalue())
    except ValueError:
        raise Unmeasurable("probe_failed", "the probe output is not one JSON document")
    sid = doc.get("session_id") if isinstance(doc, dict) else None
    if not isinstance(sid, str) or not sid:
        raise Unmeasurable("probe_failed", "the probe output carries no session_id")
    path = lfp.transcript(sid)
    if not path:
        raise Unmeasurable("no_transcript", "the probe session left no transcript under ~/.claude/projects")
    return path, {"label": label, "session_id": sid, "cost_usd": doc.get("cost_usd"), "exe": exe}


def resolve_source(args):
    """-> (transcript path, source dict). The source dict is what the SOURCE line and provenance.source name."""
    if args.cwd and not args.probe:
        raise Unmeasurable("cwd_without_probe", "--cwd only applies to --probe")
    if args.probe:
        path, info = probe_transcript(args.cwd)
        return str(path), {"kind": "probe", "session": info["session_id"], "probe": info}
    if args.transcript:
        return args.transcript, {"kind": "transcript", "name": os.path.basename(str(args.transcript))}
    if args.project_dir:
        path, count = newest_transcript(args.project_dir)
        return str(path), {"kind": "project_dir", "selected": Path(path).name, "candidates": count}
    path = session_transcript(args.session)
    return str(path), {"kind": "session", "id": args.session}


# --------------------------------------------------------------------------- reference
def _invalid(detail):
    return Unmeasurable("reference_invalid", detail)


def load_reference(path):
    p = Path(path)
    if not p.is_file():
        raise Unmeasurable("reference_missing", "no such reference file")
    try:
        with open(p, encoding="utf-8") as fh:
            ref = json.load(fh)
    except (OSError, ValueError):
        raise _invalid("not readable JSON")
    if not isinstance(ref, dict) or ref.get("schema") != SCHEMA:
        raise _invalid(f"schema is not {SCHEMA}")
    for key, typ in (("provenance", dict), ("components", list), ("tokens", dict), ("explanations", list)):
        if not isinstance(ref.get(key), typ):
            raise _invalid(f"{key} missing or of the wrong type")
    total = 0
    for c in ref["components"]:
        if (not isinstance(c, dict) or not isinstance(c.get("layer"), str) or not isinstance(c.get("source"), str)
                or c.get("scope") not in SCOPES or not isinstance(c.get("chars"), int) or isinstance(c.get("chars"), bool)
                or c["chars"] < 0):
            raise _invalid("a component is malformed")
        total += c["chars"]
    if ref.get("total_chars") != total:
        raise _invalid("total_chars does not equal the sum of the components")
    err = validate_explanations(ref["explanations"])
    if err:
        raise Unmeasurable("explanation_refused", err)
    return ref


def _git_head(cwd):
    try:
        p = subprocess.run(["git", "--no-optional-locks", "-C", str(cwd), "rev-parse", "HEAD"], capture_output=True,
                           text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    out = p.stdout.strip()
    return out if p.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", out) else None


def _refuse_target(target):
    """HR-001: nothing under ~/.claude except the checkout itself (the laptop's checkout lives there)."""
    t = Path(target).expanduser().resolve()
    try:
        claude = (Path.home() / ".claude").resolve()
    except (RuntimeError, OSError):
        return
    root = Path(ROOT).resolve()
    under_claude = t == claude or claude in t.parents
    under_root = t == root or root in t.parents
    if under_claude and not under_root:
        raise Unmeasurable("refused_path", "the target is under ~/.claude and outside the checkout")


def stamp_source(prov, src):
    """provenance.source (and the probe's label / session_id / cost_usd) from the resolved source."""
    prov["source"] = src["kind"]
    if src.get("probe"):
        prov["probe"] = {k: src["probe"].get(k) for k in ("label", "session_id", "cost_usd")}
    return prov


def precheck_write(out, replace):
    """Refuse a doomed reference write BEFORE a source is resolved (a --probe source costs a session)."""
    target = Path(out)
    _refuse_target(target)
    if target.exists() and not replace:
        raise Unmeasurable("reference_exists", "the target exists; pass --replace to replace it")


def write_reference(out, measured, argv=None, replace=False, redact=None):
    redact = redact or load_redactor()
    target = Path(out)
    _refuse_target(target)
    if measured["tokens"]["status"] != "measured":
        raise Unmeasurable("no_model_call", "the first assistant row is not a model call; no reference without tokens")
    if target.exists() and not replace:
        raise Unmeasurable("reference_exists", "the target exists; pass --replace to replace it")
    prov = dict(measured["provenance"])
    home = prov.get("install_home")
    install = _git_head(Path(home) / ".claude" / "skills" / "claude-power-pack") if home else None
    prov["install_commit"] = install
    if install is None:
        prov["install_commit_reason"] = "no git work tree at <install_home>/.claude/skills/claude-power-pack"
    prov["repo_commit"] = _git_head(ROOT)
    prov["command"] = " ".join([os.path.basename(sys.executable), "tools/floor_regression_gate.py"] + list(argv or []))
    ref = {
        "schema": SCHEMA, "provenance": prov, "components": measured["components"], "layers": measured["layers"],
        "total_chars": measured["total_chars"], "tokens": measured["tokens"],
        "skill_listing": measured["skill_listing"], "excluded": measured["excluded"], "explanations": [],
        "caveats": list(CAVEATS),
    }
    text = json.dumps(redact_obj(ref, redact), indent=1, sort_keys=True) + "\n"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if replace:
            tmp = target.with_name(target.name + f".tmp{os.getpid()}")
            with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            os.replace(tmp, target)
        else:
            with open(target, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    except FileExistsError:
        raise Unmeasurable("reference_exists", "the target appeared during the write")
    except OSError as exc:
        raise Unmeasurable("write_failed", exc.__class__.__name__)
    return ref


# --------------------------------------------------------------------------- comparison
_COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")

CAVEATS = [
    "skill_listing is bounded by the harness listing budget (30,000 chars on both GEX44 sessions and the laptop "
    "champion row): at the budget a new skill displaces descriptions instead of adding chars, so entries and "
    "skill_count are reported beside chars",
    "prompt-driven rows (user rows, file attachments) are excluded from the floor",
    "tokens are comparable only when the excluded prompt digests are equal",
    "scopes are computed on the measuring host, at measure time, from the settings files and skill / agent files "
    "present then; deltas are per source, so a later relabel of the same chars (a settings file added after the "
    "reference) costs nothing",
    "a plugin `ns:name` skill or agent with no file under the project is filed universal (the stricter side of the "
    "1,000-char rule); a project-scoped plugin is therefore over-reported, never under-reported",
    "system prompt parts are compared by digest: a reference and a check of different session kinds (an "
    "interactive session against a mission worker whose launcher appends a prompt) differ by that part and go red "
    "unless explained",
]


def validate_explanations(items):
    """None when every entry is well formed, else 'explanation_refused: <index> <field>' (one bad entry refuses all)."""
    if not isinstance(items, list):
        return "explanation_refused: - explanations"
    for i, e in enumerate(items):
        if not isinstance(e, dict):
            return f"explanation_refused: {i} entry"
        if not isinstance(e.get("layer"), str) or not e["layer"].strip():
            return f"explanation_refused: {i} layer"
        if "scope" in e and e["scope"] not in SCOPES:
            return f"explanation_refused: {i} scope"
        if e.get("unit") not in ("chars", "tokens"):
            return f"explanation_refused: {i} unit"
        bound = e.get("delta_bound")
        if not isinstance(bound, int) or isinstance(bound, bool) or bound <= 0:
            return f"explanation_refused: {i} delta_bound"
        if not isinstance(e.get("reason"), str) or not e["reason"].strip():
            return f"explanation_refused: {i} reason"
        if not isinstance(e.get("commit"), str) or not _COMMIT_RE.match(e["commit"]):
            return f"explanation_refused: {i} commit"
    return None


def covering_explanation(finding, items):
    """First entry with the same layer, scope (when given) and unit whose delta_bound is >= the finding's delta."""
    for e in items:
        if e["layer"] != finding["layer"] or e["unit"] != finding["unit"]:
            continue
        if "scope" in e and e["scope"] != finding["scope"]:
            continue
        if finding["delta"] <= e["delta_bound"]:
            return e
    return None


def is_material(row, ref_total):
    """Rules triggered by one (layer, scope) row {layer, scope, delta}."""
    rules = []
    delta = row["delta"]
    if delta > 0 and delta >= LAYER_PCT * ref_total:
        rules.append("layer_3pct")
    if delta > 0 and row["scope"] in SCOPES_UNDER_1K and delta >= UNIVERSAL_MIN_CHARS:
        rules.append("universal_1k")
    return rules


def exit_code(verdict):
    return {"WITHIN_BOUND": EXIT_OK, "MATERIAL_RISE": EXIT_RISE, "UNMEASURABLE": EXIT_UNMEASURABLE,
            "REFERENCE_WRITTEN": EXIT_OK}.get(verdict, EXIT_UNMEASURABLE)


def _tokens_axis(ref, now):
    rt, nt = ref.get("tokens") or {}, now["tokens"]
    if rt.get("status") != "measured" or nt.get("status") != "measured":
        return {"status": "no_model_call", "ref": rt.get("first_call_total"), "now": nt.get("first_call_total"),
                "delta": None}
    if not rt.get("prompt_digest") or rt.get("prompt_digest") != nt.get("prompt_digest"):
        return {"status": "not_comparable", "ref": rt["first_call_total"], "now": nt["first_call_total"], "delta": None}
    return {"status": "measured", "ref": rt["first_call_total"], "now": nt["first_call_total"],
            "delta": nt["first_call_total"] - rt["first_call_total"]}


def _comparable_value(v):
    return None if v is None else str(v).replace("\\", "/").rstrip("/")


def absent_layers(ref, now):
    """The reference layers holding >= UNIVERSAL_MIN_CHARS (1,000) chars in total that have no component at all in the
    checked floor. A floor missing a whole layer is a different kind of session (resumed, compacted, a wrong
    transcript), not a fall in size: the comparison cannot be made (WR-01)."""
    present = {c["layer"] for c in now["components"]}
    totals = {}
    for c in ref["components"]:
        totals[c["layer"]] = totals.get(c["layer"], 0) + c["chars"]
    return sorted(layer for layer, chars in totals.items() if chars >= UNIVERSAL_MIN_CHARS and layer not in present)


def compare(ref, now):
    rp0, np0 = ref.get("provenance", {}), now["provenance"]
    differing = [f for f in ("plane", "platform", "install_home", "cwd")
                 if _comparable_value(rp0.get(f)) != _comparable_value(np0.get(f))]
    if differing:
        raise Unmeasurable("not_comparable", "fields differ: " + ", ".join(differing))
    gone = absent_layers(ref, now)
    if gone:
        raise Unmeasurable(f"layer_absent:{gone[0]}",
                           f"{len(gone)} reference layer(s) of >= {UNIVERSAL_MIN_CHARS} chars are absent from the checked "
                           f"floor: {', '.join(gone)}; this is not the same kind of session")
    items = ref.get("explanations") or []
    ref_idx = {(c["layer"], c["source"]): c for c in ref["components"]}
    now_idx = {(c["layer"], c["source"]): c for c in now["components"]}
    acc = {}
    for key in sorted(set(ref_idx) | set(now_idx)):
        rc, nc = ref_idx.get(key), now_idx.get(key)
        scope = scope_key(nc if nc is not None else rc)
        row = acc.setdefault((key[0], scope), {"ref": 0, "now": 0})
        row["ref"] += rc["chars"] if rc else 0
        row["now"] += nc["chars"] if nc else 0
    rows = [{"layer": k[0], "scope": k[1], "ref": v["ref"], "now": v["now"], "delta": v["now"] - v["ref"]}
            for k, v in sorted(acc.items())]
    ref_total = ref["total_chars"]
    findings, explained, unexplained_sum = [], [], 0

    def settle(f, rules):
        exp = covering_explanation(f, items)
        if exp is not None:
            explained.append({**f, "by": exp["commit"]})
            return True
        if rules:
            findings.append({**f, "rules": rules})
        return False

    for row in rows:
        if row["delta"] <= 0:
            continue
        f = {"layer": row["layer"], "scope": row["scope"], "delta": row["delta"], "unit": "chars"}
        if not settle(f, is_material(row, ref_total)):
            unexplained_sum += row["delta"]
    if (unexplained_sum > 0 and unexplained_sum >= TOTAL_PCT * ref_total
            and not any("layer_3pct" in f["rules"] for f in findings)):
        settle({"layer": "total", "scope": "unattributed", "delta": unexplained_sum, "unit": "chars"}, ["total_3pct"])
    axis = _tokens_axis(ref, now)
    if axis["status"] == "measured" and axis["delta"] > 0 and axis["delta"] >= TOKENS_PCT * axis["ref"]:
        settle({"layer": "tokens", "scope": "unattributed", "delta": axis["delta"], "unit": "tokens"}, ["tokens_3pct"])
    scope_deltas = {s: 0 for s in SCOPES}
    for row in rows:
        scope_deltas[row["scope"]] = scope_deltas.get(row["scope"], 0) + row["delta"]
    rp, np_ = ref.get("provenance", {}), now["provenance"]
    return {
        "verdict": "MATERIAL_RISE" if findings else "WITHIN_BOUND",
        "reason": "material_rise" if findings else "within_bound",
        "rows": rows, "findings": findings, "explained": explained, "scope_deltas": scope_deltas,
        "tokens_axis": axis,
        "ratchet_hint": ref_total > 0 and (ref_total - now["total_chars"]) >= TOTAL_PCT * ref_total,
        "totals": {"ref": ref_total, "now": now["total_chars"], "delta": now["total_chars"] - ref_total},
        "window": {"ref_sha256": rp.get("window_sha256"), "now_sha256": np_["window_sha256"],
                   "ref_rows": rp.get("window_rows"), "now_rows": np_["window_rows"],
                   "same": rp.get("window_sha256") == np_["window_sha256"]},
        "skills": {"ref": ref.get("skill_listing"), "now": now["skill_listing"]},
    }


def _s(n):
    return f"{n:+d}"


def source_line(src):
    rest = " ".join(f"{k}={v}" for k, v in src.items() if k != "kind" and not isinstance(v, dict))
    return f"SOURCE {src['kind']} {rest}".rstrip()


def probe_line(src):
    p = src.get("probe")
    if not p:
        return None
    return f"PROBE exe={p.get('exe')} session={p.get('session_id')} label={p.get('label')} cost_usd={p.get('cost_usd')}"


def render(r):
    lines = []
    if r.get("source"):
        lines.append(source_line(r["source"]))
        if probe_line(r["source"]):
            lines.append(probe_line(r["source"]))
    if r["verdict"] == "UNMEASURABLE":
        lines.append(f"UNMEASURABLE {r['reason']}: {r.get('detail', '')}".rstrip(": "))
    elif r["verdict"] == "REFERENCE_WRITTEN":
        lines.append(r.get("detail", ""))
    else:
        t = r["totals"]
        lines.append(f"FLOOR total_chars ref={t['ref']} now={t['now']} delta={_s(t['delta'])}")
        w = r["window"]
        lines.append(f"WINDOW ref_sha256={str(w['ref_sha256'])[:12]} now_sha256={str(w['now_sha256'])[:12]} "
                     f"ref_rows={w['ref_rows']} now_rows={w['now_rows']} same={'yes' if w['same'] else 'no'}")
        for row in r["rows"]:
            if row["delta"] != 0:
                lines.append(f"LAYER {row['layer']} scope={row['scope']} ref={row['ref']} now={row['now']} "
                             f"delta={_s(row['delta'])}")
        for f in r["findings"]:
            lines.append(f"RISE {f['layer']} scope={f['scope']} delta=+{f['delta']} unit={f['unit']} "
                         f"rules={','.join(f['rules'])}")
        for e in r["explained"]:
            lines.append(f"EXPLAINED {e['layer']} scope={e['scope']} delta=+{e['delta']} by={e['by']}")
        sd = r["scope_deltas"]
        lines.append("SCOPE " + " ".join(f"{s}={_s(sd.get(s, 0))}" for s in SCOPES))
        sk = r["skills"]
        lines.append(f"SKILLS ref_chars={(sk['ref'] or {}).get('chars')} now_chars={sk['now']['chars']} "
                     f"ref_entries={(sk['ref'] or {}).get('entries')} now_entries={sk['now']['entries']} "
                     f"ref_skill_count={(sk['ref'] or {}).get('skill_count')} now_skill_count={sk['now']['skill_count']}")
        ta = r["tokens_axis"]
        delta = _s(ta["delta"]) if ta["delta"] is not None else "na"
        lines.append(f"TOKENS status={ta['status']} ref={ta['ref']} now={ta['now']} delta={delta}")
    lines.append(f"FLOOR verdict={r['verdict']} exit={r['exit']} reason={r['reason']}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- CLI
def build_parser():
    ap = argparse.ArgumentParser(prog="floor_regression_gate.py", description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="compare a transcript's floor with the reference")
    mode.add_argument("--write-reference", metavar="OUT", help="measure and write the reference JSON to OUT")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--transcript", metavar="PATH", help="session transcript (jsonl)")
    src.add_argument("--project-dir", metavar="DIR", help="the newest top-level *.jsonl of a project directory")
    src.add_argument("--session", metavar="SID", help="a session id, located by listing_floor_probe.transcript")
    src.add_argument("--probe", action="store_true",
                     help="start ONE fresh headless session through listing_floor_probe (costs a session)")
    ap.add_argument("--cwd", metavar="DIR", default=None, help="working directory of the --probe session")
    ap.add_argument("--reference", metavar="PATH", default=None)
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--json", action="store_true")
    return ap


JSON_KEYS = ("verdict", "exit", "reason", "rows", "findings", "explained", "scope_deltas", "tokens_axis",
             "ratchet_hint", "reference", "provenance", "caveats")


def _ascii(text):
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _emit(result, as_json, redact):
    """Everything that leaves the process passes redact() first; without a redactor only fixed tokens are printed."""
    if redact is None:
        result = {"verdict": result["verdict"], "reason": result["reason"], "exit": result["exit"], "detail": ""}
        redact = lambda s: s  # noqa: E731 -- nothing but fixed tokens can reach it
    if as_json:
        doc = {k: result.get(k) for k in JSON_KEYS}
        for k in ("rows", "findings", "explained", "caveats"):
            doc[k] = doc[k] or []
        print(json.dumps(redact_obj(doc, redact), indent=1, sort_keys=True))
    else:
        for line in render(result).split("\n"):
            print(_ascii(redact(line)))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_UNMEASURABLE
    redact = None
    src = None
    ref_path = Path(args.reference) if args.reference else ROOT / DEFAULT_REFERENCE_REL
    try:
        redact = load_redactor()
        if args.write_reference:
            precheck_write(args.write_reference, args.replace)
            path, src = resolve_source(args)
            measured = measure(path)
            stamp_source(measured["provenance"], src)
            write_reference(args.write_reference, measured, argv, replace=args.replace, redact=redact)
            prov = measured["provenance"]
            tok = measured["tokens"]["first_call_total"]
            result = {"verdict": "REFERENCE_WRITTEN", "reason": "written",
                      "detail": f"FLOOR reference written path={args.write_reference} total_chars={measured['total_chars']} "
                                f"tokens={tok} window_sha256={prov['window_sha256'][:12]} window_rows={prov['window_rows']}",
                      "provenance": prov, "reference": {"path": str(args.write_reference)}}
        else:
            ref = load_reference(ref_path)
            path, src = resolve_source(args)
            now = measure(path)
            result = compare(ref, now)
            rp = ref.get("provenance", {})
            result["provenance"] = {**stamp_source(now["provenance"], src), "probe_view": now["probe_view"]}
            result["reference"] = {"path": str(ref_path), "schema": ref.get("schema"), "total_chars": ref.get("total_chars"),
                                   "window_sha256": rp.get("window_sha256"), "window_rows": rp.get("window_rows")}
    except Unmeasurable as exc:
        result = {"verdict": "UNMEASURABLE", "reason": exc.reason, "detail": exc.detail}
        if exc.probe_error:
            result["probe_error"] = exc.probe_error
    except Exception as exc:  # noqa: BLE001 -- a bug must read UNMEASURABLE, never a traceback and never exit 0
        result = {"verdict": "UNMEASURABLE", "reason": "internal_error", "detail": exc.__class__.__name__}
    if src is not None:
        result["source"] = src
    result["caveats"] = list(CAVEATS)
    result["exit"] = exit_code(result["verdict"])
    _emit(result, args.json, redact)
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main())
