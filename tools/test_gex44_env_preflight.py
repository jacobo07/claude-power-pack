#!/usr/bin/env python3
"""V-ENVPF-* gates: a GEX44 env launch is READY, NOT_READY with a typed reason, or UNMEASURABLE.

Pillar B of the incremental-cognition program (ledger id B), first half: the repeatable preflight
tools/gex44_env_preflight.py. Four questions, four separate checks: auth readiness, rules version (the PP
install contains the C-fix floor commit), hook health, interpreters. UNMEASURABLE is never READY.

Hermetic: every env root is a scratch directory built here. Credentials fixtures carry clearly fake canary
strings that must never appear in any output. No real ~/.claude, ~/a5-env or ~/a7-env path is written; the
-REAL gates read this worktree and (for the JS engine) the gsd-core lib under the running user's home.

    python3 tools/test_gex44_env_preflight.py            run every gate
    python3 tools/test_gex44_env_preflight.py --drill     mutation drill (each mutant must be killed)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gex44_env_preflight as ep  # noqa: E402
import provider_breaker as pb  # noqa: E402

SCRIPT = HERE / "gex44_env_preflight.py"
NOW = 1_800_000_000.0
CANARY_ACCESS = "CANARY-ACCESS-DO-NOT-PRINT"
CANARY_REFRESH = "CANARY-REFRESH-DO-NOT-PRINT"
CANARY_ENVVAR = "CANARY-ENVVAR-DO-NOT-PRINT"
CANARIES = (CANARY_ACCESS, CANARY_REFRESH, CANARY_ENVVAR)
TMP_ROOT = Path(tempfile.mkdtemp(prefix="envpf-test-"))

RESULTS: list[tuple[str, bool, str]] = []
QUIET = [False]
_COUNTER = [0]


def check(name: str, cond, ev="") -> None:
    ok = bool(cond)
    RESULTS.append((name, ok, str(ev)))
    if not QUIET[0]:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {ev}")


def skip(name: str, reason: str) -> None:
    """A skipped gate is not a pass: it is printed, never recorded as one."""
    if not QUIET[0]:
        print(f"SKIP {name} {reason}")


def guarded(name: str, fn) -> None:
    """Run one gate body returning (ok, evidence); an exception is a FAIL with its class, never a crash."""
    try:
        ok, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- a gate that crashes must read as red, not as absent
        ok, ev = False, f"{exc.__class__.__name__}: {exc}"
    check(name, ok, ev)


def scratch(prefix: str = "env") -> Path:
    _COUNTER[0] += 1
    d = TMP_ROOT / f"{prefix}{_COUNTER[0]}"
    d.mkdir(parents=True)
    return d


# --------------------------------------------------------------------------- fixtures
def make_env(tmp: Path, *, expires_at_ms, refresh=True, refresh_expires_ms=None, creds=True,
             extra_env_lines=(), settings="{}", malformed=False) -> Path:
    """A scratch env root: env.sh, home/.claude/.credentials.json (canary tokens), settings.json."""
    home = tmp / "home"
    (home / ".claude").mkdir(parents=True, exist_ok=True)
    lines =[f"export HOME={home}", f"export PATH={tmp}/npm/bin:{tmp}/node/bin:$PATH",
             "export CPP_GIT_EXE=/usr/bin/git", *extra_env_lines]
    (tmp / "env.sh").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if creds:
        cpath = home / ".claude" / ".credentials.json"
        if malformed:
            cpath.write_text("{not json " + CANARY_ACCESS, encoding="utf-8")
        else:
            oauth = {"accessToken": CANARY_ACCESS, "expiresAt": expires_at_ms}
            if refresh:
                oauth["refreshToken"] = CANARY_REFRESH
            if refresh_expires_ms is not None:
                oauth["refreshTokenExpiresAt"] = refresh_expires_ms
            cpath.write_text(json.dumps({"claudeAiOauth": oauth}), encoding="utf-8")
    (home / ".claude" / "settings.json").write_text(settings, encoding="utf-8")
    return tmp


def cli(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout, p.stderr


def auth_of(tmp: Path, now: float = NOW) -> dict:
    return ep.check_auth(ep.env_from_root(tmp), now)


FUTURE_MS = int((NOW + 3600) * 1000)
PAST_MS = int((NOW - 3600) * 1000)
REFRESH_OK_MS = int((NOW + 86400 * 20) * 1000)


# --------------------------------------------------------------------------- tracer: env root -> auth -> verdict -> CLI
def grp_auth() -> None:
    def envsh_static():
        tmp = scratch()
        sentinel = tmp / "SIDE-EFFECT"
        make_env(tmp, expires_at_ms=FUTURE_MS,
                 extra_env_lines=[f"touch {sentinel}", f"export SPAWN=$(touch {sentinel})",
                                  f"export DOLLAR_PATH=${{PATH}}:{tmp}/extra",
                                  f"export ANTHROPIC_API_KEY={CANARY_ENVVAR}"])
        env = ep.env_from_root(tmp)
        path = env["path"]
        ok = (not sentinel.exists() and env["home"] == str(tmp / "home")
              and path.split(os.pathsep)[0] == f"{tmp}/npm/bin" and os.environ.get("PATH", "") in path
              and "$PATH" not in path and "SPAWN" in env["env_var_names"]
              and env["install"] == str(tmp / "home" / ".claude" / "skills" / "claude-power-pack")
              and CANARY_ENVVAR not in json.dumps(env))
        return ok, f"sentinel_exists={sentinel.exists()} home={env['home']} path_head={path.split(os.pathsep)[0]}"
    guarded("V-ENVPF-ENVSH-STATIC", envsh_static)

    def envsh_missing():
        tmp = scratch()
        try:
            ep.env_from_root(tmp)
        except ValueError as exc:
            return True, f"ValueError({exc})"
        return False, "no ValueError for an env root without env.sh"
    guarded("V-ENVPF-ENVSH-MISSING", envsh_missing)

    def expired_zero():
        tmp = make_env(scratch(), expires_at_ms=0, refresh_expires_ms=REFRESH_OK_MS)
        r = auth_of(tmp)
        return r["state"] == ep.NOT_READY and r["reasons"] == ["auth_expired"], \
            f"state={r['state']} reasons={r['reasons']} why={r['why']}"
    guarded("V-ENVPF-AUTH-EXPIRED-ZERO", expired_zero)

    def ready():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS)
        r = auth_of(tmp)
        return r["state"] == ep.READY and r["reasons"] == [] and r["findings"] == [], \
            f"state={r['state']} findings={r['findings']}"
    guarded("V-ENVPF-AUTH-READY", ready)

    def lapsed_refreshable():
        tmp = make_env(scratch(), expires_at_ms=PAST_MS, refresh=True, refresh_expires_ms=REFRESH_OK_MS)
        r = auth_of(tmp)
        return r["state"] == ep.READY and "access_token_lapsed_refreshable" in r["findings"], \
            f"state={r['state']} findings={r['findings']}"
    guarded("V-ENVPF-AUTH-LAPSED-REFRESHABLE", lapsed_refreshable)

    def lapsed_unrefreshable():
        tmp = make_env(scratch(), expires_at_ms=PAST_MS, refresh=False)
        r = auth_of(tmp)
        return r["state"] == ep.NOT_READY and r["reasons"] == ["auth_expired"], \
            f"state={r['state']} reasons={r['reasons']}"
    guarded("V-ENVPF-AUTH-LAPSED-NO-REFRESH", lapsed_unrefreshable)

    def missing():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS, creds=False)
        r = auth_of(tmp)
        return r["state"] == ep.NOT_READY and r["reasons"] == ["auth_missing"], \
            f"state={r['state']} reasons={r['reasons']}"
    guarded("V-ENVPF-AUTH-MISSING", missing)

    def envvar_unmeasurable():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS, creds=False,
                       extra_env_lines=[f"export ANTHROPIC_API_KEY={CANARY_ENVVAR}"])
        r = auth_of(tmp)
        blob = json.dumps(r)
        return r["state"] == ep.UNMEASURABLE and CANARY_ENVVAR not in blob, \
            f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-AUTH-ENVVAR-UNMEASURABLE", envvar_unmeasurable)

    def malformed():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS, malformed=True)
        r = auth_of(tmp)
        return r["state"] == ep.UNMEASURABLE and CANARY_ACCESS not in json.dumps(r), \
            f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-AUTH-MALFORMED", malformed)

    def cli_exit():
        got = {}
        for label, kw in (("expired", dict(expires_at_ms=0)), ("ready", dict(expires_at_ms=FUTURE_MS)),
                          ("malformed", dict(expires_at_ms=FUTURE_MS, malformed=True))):
            tmp = make_env(scratch(), **kw)
            rc, out, _ = cli(["--env-root", str(tmp), "--checks", "auth", "--json", "--now", str(NOW)])
            got[label] = (rc, json.loads(out)["verdict"])
        ok = got == {"expired": (1, "NOT_READY"), "ready": (0, "READY"), "malformed": (2, "UNMEASURABLE")}
        return ok, f"{got}"
    guarded("V-ENVPF-CLI-EXIT", cli_exit)

    def cli_human():
        tmp = make_env(scratch(), expires_at_ms=0)
        rc, out, _ = cli(["--env-root", str(tmp), "--checks", "auth", "--now", str(NOW)])
        last = out.strip().splitlines()[-1]
        return rc == 1 and last == "PREFLIGHT=NOT_READY reasons=auth_expired", f"rc={rc} last={last!r}"
    guarded("V-ENVPF-CLI-HUMAN-LINE", cli_human)

    def no_secret():
        blobs = []
        for kw in (dict(expires_at_ms=0), dict(expires_at_ms=FUTURE_MS), dict(expires_at_ms=PAST_MS),
                   dict(expires_at_ms=FUTURE_MS, malformed=True),
                   dict(expires_at_ms=FUTURE_MS, creds=False,
                        extra_env_lines=[f"export ANTHROPIC_API_KEY={CANARY_ENVVAR}"])):
            tmp = make_env(scratch(), **kw)
            for extra in (["--json"], []):
                rc, out, err = cli(["--env-root", str(tmp), "--checks", "auth", "--now", str(NOW), *extra])
                blobs.append(out + err)
            blobs.append(json.dumps(ep.run(ep.env_from_root(tmp), NOW, ["auth"])))
        leaked = [c for c in CANARIES if any(c in b for b in blobs)]
        return not leaked and len(blobs) >= 15, f"outputs={len(blobs)} leaked={leaked}"
    guarded("V-ENVPF-NO-SECRET", no_secret)

    def shared_reader():
        """check_auth uses the pillar-C reader and expiry predicate, not a second copy of either."""
        src = SCRIPT.read_text(encoding="utf-8")
        ok = "credentials_expired(" in src and "credentials_state(" in src and "import provider_breaker" in src
        return ok, "credentials_state/credentials_expired from provider_breaker"
    guarded("V-ENVPF-AUTH-SHARED-READER", shared_reader)


# --------------------------------------------------------------------------- expansion fixtures
SYS_NODE = shutil.which("node")


def git(cwd: Path, *args: str, check=True) -> str:
    """A fixture git call: argv list, a throwaway identity, no global config."""
    env = {**os.environ, "HOME": str(TMP_ROOT), "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env, timeout=60)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} -> {p.returncode}: {p.stderr.strip()}")
    return p.stdout.strip()


def install_of(tmp: Path) -> Path:
    return tmp / "home" / ".claude" / "skills" / "claude-power-pack"


def make_install(tmp: Path) -> dict:
    """A PP install that is a git checkout: base -> floor -> tip, required files present from the base."""
    inst = install_of(tmp)
    (inst / "tools").mkdir(parents=True)
    git(inst, "init", "-q", "-b", "main")
    for f in ep.PP_REQUIRED_FILES:
        (inst / f).write_text("# fixture\n", encoding="utf-8")
    git(inst, "add", "-A")
    git(inst, "commit", "-q", "-m", "base")
    base = git(inst, "rev-parse", "HEAD")
    (inst / "floor.txt").write_text("floor\n", encoding="utf-8")
    git(inst, "add", "-A")
    git(inst, "commit", "-q", "-m", "floor")
    floor = git(inst, "rev-parse", "HEAD")
    (inst / "tip.txt").write_text("tip\n", encoding="utf-8")
    git(inst, "add", "-A")
    git(inst, "commit", "-q", "-m", "tip")
    return {"inst": inst, "base": base, "floor": floor, "tip": git(inst, "rev-parse", "HEAD")}


def link_node(tmp: Path) -> str:
    """The env's own node: a symlink to the system node, in the layout env.sh declares."""
    (tmp / "node" / "bin").mkdir(parents=True, exist_ok=True)
    link = tmp / "node" / "bin" / "node"
    if not link.exists():
        link.symlink_to(SYS_NODE)
    return str(link)


def hook_settings(entries) -> str:
    """entries: (event, command, args|None). Builds a settings.json hooks block."""
    hooks: dict = {}
    for event, command, args in entries:
        h = {"type": "command", "command": command}
        if args is not None:
            h["args"] = args
        hooks.setdefault(event, []).append({"matcher": "", "hooks": [h]})
    return json.dumps({"hooks": hooks})


def write_script(tmp: Path, name: str, body: str = "'use strict';\nprocess.exit(0);\n") -> str:
    d = tmp / "home" / ".claude" / "hooks"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(body, encoding="utf-8")
    return str(d / name)


def hooks_env(tmp: Path, entries_fn):
    """entries_fn(tmp, node) -> entries. Returns (env, check_hooks result)."""
    node = link_node(tmp)
    make_env(tmp, expires_at_ms=FUTURE_MS, settings=hook_settings(entries_fn(tmp, node)))
    env = ep.env_from_root(tmp)
    return env, ep.check_hooks(env)


def put_engine(tmp: Path, node_range: str | None) -> None:
    d = install_of(tmp) / "vendor" / "genesis-suite"
    d.mkdir(parents=True, exist_ok=True)
    body = {"name": "x"} if node_range is None else {"name": "x", "engines": {"node": node_range}}
    (d / "package.json").write_text(json.dumps(body), encoding="utf-8")


ENGINE_RANGE = "^22.23.2 || ^24.14.0"
JS_OK = lambda manifest, env: (0, {"verdict": "SATISFIED", "results": []})  # noqa: E731


def interp(tmp: Path, *, node_v="v24.15.0", py_v="Python 3.12.3", js=JS_OK, rng=ENGINE_RANGE):
    make_env(tmp, expires_at_ms=FUTURE_MS)
    put_engine(tmp, rng)
    env = ep.env_from_root(tmp)
    env["node"], env["python"] = "/fake/node", "/fake/python3"

    def version_of(exe):
        return node_v if exe == "/fake/node" else py_v
    return ep.check_interpreters(env, version_of=version_of, js_runner=js)


# --------------------------------------------------------------------------- rules version
def grp_pp() -> None:
    def case(name, build, expect_state, expect_reason=None, expect_finding=None, floor_of=None):
        def body():
            tmp = make_env(scratch(), expires_at_ms=FUTURE_MS)
            ctx = build(tmp)
            env = ep.env_from_root(tmp)
            floor = floor_of(ctx) if floor_of else ctx["floor"]
            r = ep.check_pp_install(env, floor=floor)
            ok = r["state"] == expect_state
            if expect_reason:
                ok = ok and r["reasons"] == [expect_reason]
            if expect_finding:
                ok = ok and expect_finding in r["findings"]
            return ok, f"state={r['state']} reasons={r['reasons']} findings={r['findings']} why={r['why']}"
        guarded(name, body)

    case("V-ENVPF-PP-STALE-FLOOR-ABSENT", make_install, ep.NOT_READY, "pp_install_stale",
         floor_of=lambda c: "1" * 40)

    def detach_to_base(tmp):
        c = make_install(tmp)
        git(c["inst"], "checkout", "-q", "--detach", c["base"])
        return c
    case("V-ENVPF-PP-STALE-NOT-ANCESTOR", detach_to_base, ep.NOT_READY, "pp_install_stale")

    case("V-ENVPF-PP-READY", make_install, ep.READY)

    def sibling(tmp):
        c = make_install(tmp)
        git(c["inst"], "checkout", "-q", "--detach", c["base"])
        (c["inst"] / "side.txt").write_text("side\n", encoding="utf-8")
        git(c["inst"], "add", "-A")
        git(c["inst"], "commit", "-q", "-m", "side")
        return c
    case("V-ENVPF-PP-STALE-SIBLING", sibling, ep.NOT_READY, "pp_install_stale")

    def required_missing(tmp):
        c = make_install(tmp)
        git(c["inst"], "rm", "-q", "tools/provider_breaker.py")
        git(c["inst"], "commit", "-q", "-m", "drop breaker")
        return c
    case("V-ENVPF-PP-REQUIRED-FILE", required_missing, ep.NOT_READY, "pp_install_stale")

    def not_git(tmp):
        install_of(tmp).mkdir(parents=True)
        return {"floor": "a" * 40}
    case("V-ENVPF-PP-NOT-GIT-UNMEASURABLE", not_git, ep.UNMEASURABLE)

    def modified(tmp):
        c = make_install(tmp)
        (c["inst"] / "tools" / "gsd_mission.py").write_text("# local edit\n", encoding="utf-8")
        return c
    case("V-ENVPF-PP-MODIFIED-IS-FINDING", modified, ep.READY, expect_finding="install_modified")

    def git_missing():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS)
        c = make_install(tmp)
        env = ep.env_from_root(tmp)
        env["git"] = None
        r = ep.check_pp_install(env, floor=c["floor"])
        return r["state"] == ep.UNMEASURABLE, f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-PP-GIT-MISSING-UNMEASURABLE", git_missing)

    def real_ready():
        r = ep.check_pp_install(ep.env_current())
        return r["state"] == ep.READY, f"state={r['state']} head={r['detail'].get('head')} floor={ep.PP_COMMIT_FLOOR}"
    guarded("V-ENVPF-PP-REAL-READY", real_ready)

    a7_head = "01199995c7d15a9540dc4180c8f3a50d6e1244b3"
    repo_root = HERE.parent
    have = subprocess.run(["git", "cat-file", "-e", f"{a7_head}^{{commit}}"], cwd=repo_root,
                          capture_output=True).returncode == 0
    if not have:
        skip("V-ENVPF-PP-STALE-REAL", f"measured a7 head {a7_head[:8]} is not in this repository's object store")
        return

    def stale_real():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS)
        inst = install_of(tmp)
        inst.parent.mkdir(parents=True, exist_ok=True)
        git(tmp, "clone", "-q", "--shared", "--no-checkout", str(repo_root), str(inst))
        git(inst, "update-ref", "--no-deref", "HEAD", a7_head)
        rc, out, _ = cli(["--env-root", str(tmp), "--checks", "pp_install", "--json", "--now", str(NOW)])
        d = json.loads(out)
        head = git(inst, "rev-parse", "HEAD")
        # Also in-process: the CLI above is a child process, which a drill's in-process mutant cannot reach.
        inproc = ep.check_pp_install(ep.env_from_root(tmp))
        ok = (rc == 1 and d["verdict"] == "NOT_READY" and d["reasons"] == ["pp_install_stale"] and head == a7_head
              and inproc["state"] == ep.NOT_READY and inproc["reasons"] == ["pp_install_stale"]
              # the ancestry test itself must fire; "required files missing" alone is a second, weaker signal
              and "does not contain the floor" in inproc["why"])
        return ok, (f"rc={rc} verdict={d['verdict']} reasons={d['reasons']} in_process={inproc['state']} "
                    f"head={head[:8]} floor={ep.PP_COMMIT_FLOOR[:8]}")
    guarded("V-ENVPF-PP-STALE-REAL", stale_real)


# --------------------------------------------------------------------------- hook health
def grp_hooks() -> None:
    def none():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS, settings="{}")
        r = ep.check_hooks(ep.env_from_root(tmp))
        return r["state"] == ep.NOT_READY and r["reasons"] == ["hooks_broken"], f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-HOOKS-NONE", none)

    def missing_script():
        """A missing JS script and a missing shell script (no syntax check to catch it second-hand)."""
        env, js = hooks_env(scratch(), lambda t, n: [("PreToolUse", n, [str(t / "home/.claude/hooks/gone.js")])])
        env, sh = hooks_env(scratch(), lambda t, n: [("PreToolUse", f'bash "{t}/home/.claude/hooks/gone.sh"', None)])
        ok = all(r["state"] == ep.NOT_READY and r["reasons"] == ["hooks_broken"] for r in (js, sh))
        return ok, f"js={js['state']}({js['why']}) sh={sh['state']}({sh['why']})"
    guarded("V-ENVPF-HOOKS-MISSING-SCRIPT", missing_script)

    def syntax():
        env, r = hooks_env(scratch(), lambda t, n: [("PreToolUse", n, [write_script(t, "bad.js", "function (\n")])])
        return r["state"] == ep.NOT_READY and r["reasons"] == ["hooks_broken"], f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-HOOKS-SYNTAX", syntax)

    def interpreter_missing():
        env, r = hooks_env(scratch(), lambda t, n: [("PreToolUse", str(t / "node/bin/nonode"),
                                                     [write_script(t, "ok.js")])])
        return r["state"] == ep.NOT_READY and r["reasons"] == ["hooks_broken"], f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-HOOKS-INTERPRETER-MISSING", interpreter_missing)

    dispatcher = ("'use strict';\nmodule.exports = { CHAIN_NAMES: ['A-chain'], EVENT_NAMES: ['PreCompact'] };\n"
                  "if (require.main === module) { process.exit(0); }\n")

    def dispatcher_chain():
        _, bad = hooks_env(scratch(), lambda t, n: [("PreToolUse", n, [write_script(t, "hook-dispatcher.js", dispatcher),
                                                                      "--event=B-chain"])])
        _, ok = hooks_env(scratch(), lambda t, n: [("PreToolUse", n, [write_script(t, "hook-dispatcher.js", dispatcher),
                                                                     "--event=A-chain"]),
                                                   ("PreCompact", n, [str(t / "home/.claude/hooks/hook-dispatcher.js"),
                                                                      "--event=PreCompact"])])
        good = ok["state"] == ep.READY and ok["reasons"] == []
        refused = bad["state"] == ep.NOT_READY and bad["reasons"] == ["hooks_broken"]
        return good and refused, f"B-chain={bad['state']}({bad['why']}) A-chain={ok['state']}({ok['why']})"
    guarded("V-ENVPF-HOOKS-DISPATCHER-CHAIN", dispatcher_chain)

    def healthy():
        env, r = hooks_env(scratch(), lambda t, n: [("PreToolUse", n, [write_script(t, "a.js")]),
                                                    ("Stop", n, [write_script(t, "b.cjs"), "--x"])])
        return r["state"] == ep.READY and r["findings"] == [] and r["detail"].get("scripts_checked") == 2, \
            f"state={r['state']} findings={r['findings']} detail={r['detail']}"
    guarded("V-ENVPF-HOOKS-HEALTHY", healthy)

    def unreadable():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS, settings="{not json")
        r = ep.check_hooks(ep.env_from_root(tmp))
        return r["state"] == ep.UNMEASURABLE, f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-HOOKS-UNREADABLE", unreadable)

    def foreign():
        outside = scratch("other") / "x.js"
        outside.write_text("process.exit(0);\n", encoding="utf-8")
        env, r = hooks_env(scratch(), lambda t, n: [("PreToolUse", n, [str(outside)])])
        return r["state"] == ep.READY and "hooks_foreign_env" in r["findings"], \
            f"state={r['state']} findings={r['findings']}"
    guarded("V-ENVPF-HOOKS-FOREIGN-IS-FINDING", foreign)

    def shell_unjudged():
        sentinel = scratch("sentinel") / "RAN"
        env, r = hooks_env(scratch(), lambda t, n: [("PreToolUse", n, [write_script(t, "a.js")]),
                                                    ("Stop", f"touch {sentinel} ; echo hi | cat", None)])
        return r["state"] == ep.READY and "hook_entries_unjudged" in r["findings"] and not sentinel.exists(), \
            f"state={r['state']} findings={r['findings']} shell_ran={sentinel.exists()}"
    guarded("V-ENVPF-HOOKS-SHELL-UNJUDGED", shell_unjudged)

    def all_unjudged():
        env, r = hooks_env(scratch(), lambda t, n: [("Stop", "echo a && echo b", None)])
        return r["state"] == ep.UNMEASURABLE, f"state={r['state']} findings={r['findings']}"
    guarded("V-ENVPF-HOOKS-ALL-UNJUDGED", all_unjudged)

    def bash_command_form():
        """The measured a5/a7 form: `bash "<script.sh>"` with no args key."""
        tmp = scratch()
        script = tmp / "home" / ".claude" / "hooks" / "v.sh"
        script.parent.mkdir(parents=True)
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        make_env(tmp, expires_at_ms=FUTURE_MS, settings=hook_settings([("PreToolUse", f'bash "{script}"', None)]))
        r = ep.check_hooks(ep.env_from_root(tmp))
        script.unlink()
        gone = ep.check_hooks(ep.env_from_root(tmp))
        return r["state"] == ep.READY and gone["state"] == ep.NOT_READY, f"present={r['state']} removed={gone['state']}"
    guarded("V-ENVPF-HOOKS-BASH-FORM", bash_command_form)

    def cap_reported():
        tmp = scratch()
        node = link_node(tmp)
        entries = [("PreToolUse", node, [write_script(tmp, f"h{i}.js")]) for i in range(5)]
        make_env(tmp, expires_at_ms=FUTURE_MS, settings=hook_settings(entries))
        saved = ep.MAX_HOOK_SCRIPTS
        ep.MAX_HOOK_SCRIPTS = 3
        try:
            r = ep.check_hooks(ep.env_from_root(tmp))
        finally:
            ep.MAX_HOOK_SCRIPTS = saved
        return r["detail"].get("script_cap_hit") is True and r["detail"].get("scripts_checked") == 3, \
            f"detail={r['detail']}"
    guarded("V-ENVPF-HOOKS-CAP-REPORTED", cap_reported)


# --------------------------------------------------------------------------- interpreters
def grp_interp() -> None:
    def table():
        rows = [("v24.15.0", ENGINE_RANGE, True), ("v24.14.0", ENGINE_RANGE, True), ("24.13.9", "^24.14.0", False),
                ("25.0.0", "^24.14.0", False), ("24.15.0", "^24.14.0", True), ("22.23.2", ENGINE_RANGE, True),
                ("22.23.1", ENGINE_RANGE, False), ("23.5.0", ENGINE_RANGE, False), ("18.19.1", ENGINE_RANGE, False),
                ("3.9.0", ">=3.9.0", True), ("3.8.9", ">=3.9.0", False), ("1.2.3", "1.2.3", True),
                ("1.2.4", "1.2.3", False), ("0.3.5", "^0.3.1", True), ("0.4.0", "^0.3.1", False),
                ("1.2.3", "~1.2.3", None), ("1.2.3", "", None), ("1.2.3", "^1.x", None), ("banana", "^1.0.0", None),
                ("v24.15.0\n", "^24.14.0", True)]
        bad = [(v, r, want, ep.satisfies(v, r)) for v, r, want in rows if ep.satisfies(v, r) is not want]
        return not bad, f"{len(rows)} rows, mismatches={bad}"
    guarded("V-ENVPF-SEMVER-TABLE", table)

    def v18():
        r = interp(scratch(), node_v="v18.19.1")
        return r["state"] == ep.NOT_READY and r["reasons"] == ["interpreter_unsupported"] and "v18.19.1" in r["why"], \
            f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-NODE-V18-UNSUPPORTED", v18)

    def ok():
        r = interp(scratch())
        return r["state"] == ep.READY and r["reasons"] == [], f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-INTERP-READY", ok)

    def node_absent():
        tmp = scratch()
        make_env(tmp, expires_at_ms=FUTURE_MS)
        put_engine(tmp, ENGINE_RANGE)
        env = ep.env_from_root(tmp)
        env["node"] = None
        r = ep.check_interpreters(env, version_of=lambda exe: "Python 3.12.3", js_runner=JS_OK)
        return r["state"] == ep.NOT_READY and r["reasons"] == ["interpreter_unsupported"] and "no node" in r["why"], \
            f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-NODE-ABSENT", node_absent)

    def range_unmeasurable():
        out = {"missing": interp(scratch(), rng=None)["state"],
               "unsupported_syntax": interp(scratch(), rng="~22.1.0 || >=24")["state"]}
        return set(out.values()) == {ep.UNMEASURABLE}, f"{out}"
    guarded("V-ENVPF-RANGE-UNMEASURABLE", range_unmeasurable)

    def python_old():
        r = interp(scratch(), py_v="Python 3.8.10")
        return r["state"] == ep.NOT_READY and r["reasons"] == ["interpreter_unsupported"] and "3.8" in r["why"], \
            f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-PYTHON-OLD", python_old)

    def js_unmet():
        js = lambda m, e: (1, {"verdict": "UNMET", "results": [{"id": "git", "state": "UNMET", "why": "x"},  # noqa: E731
                                                              {"id": "python3", "state": "SATISFIED", "why": "y"}]})
        r = interp(scratch(), js=js)
        return (r["state"] == ep.NOT_READY and r["reasons"] == ["interpreter_unsupported"] and "git" in r["why"]
                and "python3" not in r["why"]), f"state={r['state']} why={r['why']}"
    guarded("V-ENVPF-JS-UNMET", js_unmet)

    def js_unmeasurable():
        def timeout(m, e):
            raise TimeoutError("engine")
        cases = {"exit2": lambda m, e: (2, {"verdict": "UNMEASURABLE", "results": []}),
                 "timeout": timeout, "unparseable": lambda m, e: (0, None),
                 "satisfied_but_rc1": lambda m, e: (1, {"verdict": "SATISFIED", "results": []})}
        out = {k: interp(scratch(), js=v)["state"] for k, v in cases.items()}
        return set(out.values()) == {ep.UNMEASURABLE}, f"{out}"
    guarded("V-ENVPF-JS-UNMEASURABLE", js_unmeasurable)

    def refusal_beats_unmeasured():
        r = interp(scratch(), node_v="v18.19.1", js=lambda m, e: (2, {"verdict": "UNMEASURABLE", "results": []}))
        return r["state"] == ep.NOT_READY and bool(r["detail"].get("unmeasured")), \
            f"state={r['state']} detail={r['detail']}"
    guarded("V-ENVPF-INTERP-REFUSAL-BEATS-UNMEASURED", refusal_beats_unmeasured)

    def manifest_shape():
        tmp = scratch()
        make_env(tmp, expires_at_ms=FUTURE_MS)
        env = ep.env_from_root(tmp)
        env.update({"node": "/n/node", "python": "/p/python3", "git": "/g/git", "claude": "/c/claude"})
        by = {r["id"]: r for r in ep.js_manifest(env)["runtimeRequirements"]["requirements"]}
        claude = by.get("claude-cli", {})
        ok = (set(by) == {"posix-shell", "env-node", "python3", "git", "claude-cli"}
              and claude.get("kind") == "file" and claude.get("path") == "/c/claude"
              and all(by[i].get("kind") == "executable" for i in by if i != "claude-cli")
              and by["env-node"]["name"] == "/n/node")
        return ok, f"ids={sorted(by)} claude={claude}"
    guarded("V-ENVPF-JS-MANIFEST-SHAPE", manifest_shape)

    def probe_isolation():
        tmp = scratch()
        make_env(tmp, expires_at_ms=FUTURE_MS)
        put_engine(tmp, ENGINE_RANGE)
        (tmp / "node" / "bin").mkdir(parents=True)
        fake = tmp / "node" / "bin" / "node"
        seen = tmp / "probe-env.txt"
        fake.write_text(f'#!/bin/sh\necho "$HOME|$GIT_OPTIONAL_LOCKS" > {seen}\necho v24.15.0\n', encoding="utf-8")
        fake.chmod(0o755)
        env = ep.env_from_root(tmp)
        ep.check_interpreters(env, js_runner=JS_OK)
        got = seen.read_text(encoding="utf-8").strip() if seen.exists() else ""
        home, _, locks = got.partition("|")
        ok = bool(got) and not home.startswith(env["home"]) and locks == "0"
        return ok, f"probe saw HOME={home!r} GIT_OPTIONAL_LOCKS={locks!r} (env home {env['home']})"
    guarded("V-ENVPF-PROBE-ISOLATION", probe_isolation)

    gsd_lib = Path.home() / ".claude" / "gsd-core" / "bin" / "lib"
    if not (gsd_lib / "shell-command-projection.cjs").exists() or not SYS_NODE:
        skip("V-ENVPF-JS-REAL", f"gsd-core lib not found at {gsd_lib}")
        return

    def js_real():
        env = {"node": SYS_NODE, "python": sys.executable, "git": shutil.which("git"), "claude": sys.executable,
               "home": str(Path.home()), "path": os.environ.get("PATH", "")}
        good = ep.run_js_engine(ep.js_manifest(env), env)
        env_bad = {**env, "git": "/nonexistent/definitely-not-git"}
        bad = ep.run_js_engine(ep.js_manifest(env_bad), env_bad)
        ok = (good[0] == 0 and good[1]["verdict"] == "SATISFIED" and bad[0] == 1 and bad[1]["verdict"] == "UNMET"
              and [r["id"] for r in bad[1]["results"] if r["state"] == "UNMET"] == ["git"])
        return ok, f"good=(rc {good[0]}, {good[1] and good[1]['verdict']}) bad=(rc {bad[0]}, {bad[1] and bad[1]['verdict']})"
    guarded("V-ENVPF-JS-REAL", js_real)


# --------------------------------------------------------------------------- aggregate / run
def grp_aggregate() -> None:
    def st(check, state, reasons=()):
        return ep._result(check, state, f"{check} {state}", reasons=reasons)

    def unmeasurable_not_ready():
        agg = ep.aggregate([st("auth", ep.READY), st("hooks", ep.UNMEASURABLE)])
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS, malformed=True)
        rc, out, _ = cli(["--env-root", str(tmp), "--checks", "auth", "--json", "--now", str(NOW)])
        ok = agg["verdict"] == ep.UNMEASURABLE and rc == 2 and json.loads(out)["verdict"] == "UNMEASURABLE"
        return ok, f"aggregate={agg['verdict']} cli_rc={rc}"
    guarded("V-ENVPF-UNMEASURABLE-NOT-READY", unmeasurable_not_ready)

    def measured_wins():
        agg = ep.aggregate([st("auth", ep.NOT_READY, ["auth_expired"]), st("hooks", ep.UNMEASURABLE),
                            st("interpreters", ep.NOT_READY, ["interpreter_unsupported"])])
        tmp = make_env(scratch(), expires_at_ms=0, settings="{not json")
        res = ep.run(ep.env_from_root(tmp), NOW, ["auth", "hooks"])
        ok = (agg["verdict"] == ep.NOT_READY and [u["check"] for u in agg["unmeasured"]] == ["hooks"]
              and agg["reasons"] == ["auth_expired", "interpreter_unsupported"]
              and res["verdict"] == ep.NOT_READY and [u["check"] for u in res["unmeasured"]] == ["hooks"])
        return ok, f"agg={agg['verdict']} unmeasured={[u['check'] for u in agg['unmeasured']]} run={res['verdict']}"
    guarded("V-ENVPF-MEASURED-WINS", measured_wins)

    guarded("V-ENVPF-AGG-EMPTY-UNMEASURABLE", lambda: (
        ep.aggregate([])["verdict"] == ep.UNMEASURABLE, "no checks run -> UNMEASURABLE, never READY"))

    def unknown_check():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS)
        res = ep.run(ep.env_from_root(tmp), NOW, ["auth", "nonsense"])
        return res["verdict"] == ep.UNMEASURABLE and any("unknown check" in u["why"] for u in res["unmeasured"]), \
            f"verdict={res['verdict']}"
    guarded("V-ENVPF-UNKNOWN-CHECK", unknown_check)

    def budget():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS)
        saved = ep.BUDGET_S
        ep.BUDGET_S = -1
        try:
            res = ep.run(ep.env_from_root(tmp), NOW, ["auth", "hooks"])
        finally:
            ep.BUDGET_S = saved
        return res["verdict"] == ep.UNMEASURABLE and all(c["why"] == "budget exhausted" for c in res["checks"]), \
            f"verdict={res['verdict']} whys={[c['why'] for c in res['checks']]}"
    guarded("V-ENVPF-BUDGET-EXHAUSTED", budget)

    def result_shape():
        tmp = make_env(scratch(), expires_at_ms=FUTURE_MS)
        res = ep.run(ep.env_from_root(tmp), NOW, ["auth"])
        keys = {"verdict", "reasons", "unmeasured", "findings", "checks", "host", "plane", "checked_at", "env"}
        return keys <= set(res) and (res["plane"] == "gex44" or "gex44" not in res["host"].lower()), \
            f"plane={res['plane']} host={res['host']}"
    guarded("V-ENVPF-RESULT-SHAPE", result_shape)

    def no_shell():
        src = SCRIPT.read_text(encoding="utf-8")
        bad = [t for t in ("shell=True", "os.system(", "os.popen(") if t in src]
        return not bad, f"forbidden={bad}"
    guarded("V-ENVPF-NO-SHELL", no_shell)

    def current_completes():
        t0 = time.monotonic()
        rc, out, _ = cli(["--current", "--json"])
        dt = time.monotonic() - t0
        d = json.loads(out)
        return rc in (0, 1, 2) and rc == ep.EXIT[d["verdict"]] and dt < 120 and len(d["checks"]) == 4, \
            f"rc={rc} verdict={d['verdict']} reasons={d['reasons']} elapsed={dt:.1f}s"
    guarded("V-ENVPF-CURRENT-COMPLETES", current_completes)


GROUPS = [grp_auth, grp_pp, grp_hooks, grp_interp, grp_aggregate]


def run_all() -> int:
    for g in GROUPS:
        g()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"ENVPF_PASS={passed}/{total}  threshold={total}/{total}")
    return 0 if passed == total else 1


# --------------------------------------------------------------------------- mutation drill
def _quiet(groups) -> dict[str, bool]:
    """Run groups with printing off; {gate: passed} for what they recorded."""
    start = len(RESULTS)
    QUIET[0] = True
    try:
        for g in groups:
            g()
    finally:
        QUIET[0] = False
    return {n: ok for n, ok, _ in RESULTS[start:]}


def _patch(obj, attr, value):
    saved = getattr(obj, attr)
    setattr(obj, attr, value)
    return lambda: setattr(obj, attr, saved)


def _m_unmeasurable_to_ready():
    real = ep.aggregate

    def mutant(checks):
        out = real(checks)
        if out["verdict"] == ep.UNMEASURABLE:
            out["verdict"] = ep.READY
        return out
    return _patch(ep, "aggregate", mutant)


def _m_expiry_always_false():
    return _patch(pb, "credentials_expired", lambda cred, now: False)


def _m_ancestor_always_true():
    return _patch(ep, "_is_ancestor", lambda sbx, git, install, floor: True)


def _m_missing_scripts_ignored():
    return _patch(ep, "_script_exists", lambda path: True)


def _m_satisfies_always_true():
    return _patch(ep, "satisfies", lambda version, rng: True)


def _m_js_unmet_is_ready():
    real = ep._judge_js

    def mutant(rc, parsed):
        kind, text = real(rc, parsed)
        return ("ok", text) if kind == "refuse" else (kind, text)
    return _patch(ep, "_judge_js", mutant)


MUTANTS = [
    ("M1 aggregate maps UNMEASURABLE to READY", _m_unmeasurable_to_ready, [grp_aggregate],
     ["V-ENVPF-UNMEASURABLE-NOT-READY"]),
    ("M2 credentials_expired always False", _m_expiry_always_false, [grp_auth], ["V-ENVPF-AUTH-EXPIRED-ZERO"]),
    ("M3 ancestor test always passes", _m_ancestor_always_true, [grp_pp], ["V-ENVPF-PP-STALE-REAL"]),
    ("M4 missing scripts ignored", _m_missing_scripts_ignored, [grp_hooks], ["V-ENVPF-HOOKS-MISSING-SCRIPT"]),
    ("M5 satisfies() always True", _m_satisfies_always_true, [grp_interp], ["V-ENVPF-NODE-V18-UNSUPPORTED"]),
    ("M6 JS UNMET mapped to READY", _m_js_unmet_is_ready, [grp_interp], ["V-ENVPF-JS-UNMET"]),
]


def run_drill() -> int:
    """Each mutant is applied in-process, the gates it must kill are re-run, the mutant is restored. The
    unmutated control runs first and must be green: a drill whose control is red proves nothing."""
    control = _quiet(GROUPS)
    control_ok = bool(control) and all(control.values())
    print(f"{'PASS' if control_ok else 'FAIL'} DRILL-CONTROL unmutated run: {sum(control.values())}/{len(control)} gates green")
    killed = 0
    for label, apply, groups, targets in MUTANTS:
        restore = apply()
        try:
            seen = _quiet(groups)
        finally:
            restore()
        by = [t for t in targets if seen.get(t) is False]
        if len(by) == len(targets):
            killed += 1
            print(f"KILLED {label} by {', '.join(by)}")
        else:
            print(f"SURVIVED {label} (still green or absent: {', '.join(t for t in targets if seen.get(t) is not False)})")
    after = _quiet(GROUPS)
    clean = bool(after) and all(after.values())
    print(f"{'PASS' if clean else 'FAIL'} DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: {sum(after.values())}/{len(after)} gates green")
    print(f"DRILL killed={killed}/{len(MUTANTS)}")
    return 0 if (killed == len(MUTANTS) and control_ok and clean) else 1


if __name__ == "__main__":
    sys.exit(run_drill() if "--drill" in sys.argv[1:] else run_all())
