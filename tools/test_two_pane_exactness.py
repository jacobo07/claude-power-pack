"""V-TWOPANE-* gates for the live two-pane exactness drill (Phase 1).

Three exit codes, not two:

  0  every gate passed
  1  a gate FAILED -- a verdict about the subject
  2  HARNESS-FAILED -- the evidence file, or a transcript it names, is missing or
     unreadable, so this run judged nothing. A verifier that could not judge its
     subject must never present as a verdict about that subject, and a run that
     skipped its subject must not read like a clean one.

Evidence comes from a real drill run (`tools/two_pane_drill.py`), never from a
fixture: the whole point of the phase is that the extension, the daemon and the
transcripts are the real ones.

Usage:  python tools/test_two_pane_exactness.py --runid <runid>
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = Path(os.environ.get("TEMP", "/tmp")) / "pp-two-pane-drill"

passes = fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {evidence}")


def _fail(gate: str, evidence: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {evidence}")


def _harness(why: str) -> int:
    print(f"HARNESS-FAILED: {why}")
    return 2


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def gates_unit(drill, lr) -> None:
    """Rules the drill's identity rests on, driven without a live subject.

    These exist because every one of them was wrong once, on this host, in a
    way no fixture would have surfaced (2026-09-19).
    """
    import json as _json
    import os as _os
    import tempfile as _tempfile
    import time as _time

    nonce = "DRILL-A-unitgate"
    tmp = Path(_tempfile.mkdtemp(prefix="twopane-unit-"))

    def transcript(rows) -> Path:
        p = tmp / f"t{len(list(tmp.glob('*.jsonl')))}.jsonl"
        p.write_text("\n".join(_json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        return p

    # NOW, not a fixed date. A stale timestamp is excluded by the TIME bound, so
    # the text predicate is never reached and the gate below passes for a reason
    # other than the one it names -- measured 2026-09-19, a mutation that made
    # `observe` count a mere mention survived exactly that way.
    now_iso = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
    typed = transcript([{"type": "user", "timestamp": now_iso,
                         "message": {"role": "user", "content":
                                     f"Reply with a single line beginning {nonce} and nothing else."}}])
    echoed = transcript([{"type": "user", "toolUseResult": {"stdout": nonce},
                          "timestamp": "2026-09-19T10:00:00Z",
                          "message": {"role": "user", "content":
                                      [{"type": "tool_result", "content": nonce}]}}])
    # The case only the toolUseResult guard catches: a tool result whose content
    # is a PLAIN STRING is shaped exactly like a typed prompt. Without this
    # fixture the guard is redundant with the block-shape check and a mutation
    # removing it survives -- measured 2026-09-19, it did.
    echoed_str = transcript([{"type": "user", "toolUseResult": {"stdout": nonce},
                              "timestamp": "2026-09-19T10:00:00Z",
                              "message": {"role": "user", "content": nonce}}])
    if not drill._carries_nonce(echoed_str, nonce):
        _ok("V-TWOPANE-NONCE-IGNORES-STRING-TOOL-RESULT",
            "a tool result whose content is a plain string is still not a keystroke")
    else:
        _fail("V-TWOPANE-NONCE-IGNORES-STRING-TOOL-RESULT",
              "a string-bodied tool result counted as a typed row")

    # A tool result IS a type="user" row. Counting by type reads an echo as an
    # event -- measured: a control built that way reported a keystroke into the
    # Owner's live pane that never happened.
    if drill._carries_nonce(typed, nonce) and not drill._carries_nonce(echoed, nonce):
        _ok("V-TWOPANE-NONCE-IGNORES-TOOL-RESULT", "typed row counts, tool_result does not")
    else:
        _fail("V-TWOPANE-NONCE-IGNORES-TOOL-RESULT",
              f"typed={drill._carries_nonce(typed, nonce)} echoed={drill._carries_nonce(echoed, nonce)}")

    # arm's predicate must stay WEAKER than observe's: the operator's own prompt
    # CONTAINS the nonce, so if observe used the same test the drill would pass
    # on its own setup.
    since = _time.time() - 3600
    prompt_only = lr.user_issued_command_since(typed, nonce, since)
    delivered = transcript([{"type": "user",
                             "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                         _time.gmtime(_time.time())),
                             "message": {"role": "user", "content": nonce}}])
    real = lr.user_issued_command_since(delivered, nonce, since)
    if (not prompt_only) and real:
        _ok("V-TWOPANE-OBSERVE-IGNORES-THE-SETUP-PROMPT",
            "a prompt that merely mentions the nonce is not a delivery; a line that IS it, is")
    else:
        _fail("V-TWOPANE-OBSERVE-IGNORES-THE-SETUP-PROMPT",
              f"prompt_counted={prompt_only} delivered_counted={real}")

    # Addressability: a subject no window's terminal can reach must fail BEFORE
    # fire spends its timeout discovering it. Positive control first, or a
    # sweep that finds nothing reads exactly like a clean verdict.
    mine = drill._owning_window(_os.getpid())
    system_pid = drill._owning_window(4)          # the System process: no terminal, ever
    if mine is not None and system_pid is None:
        _ok("V-TWOPANE-ADDRESSABILITY-DISCRIMINATES",
            f"this process is owned by {mine['registry']} (terminal {mine['pid']}); pid 4 is not")
    else:
        _fail("V-TWOPANE-ADDRESSABILITY-DISCRIMINATES",
              f"self={mine} system={system_pid} -- the check cannot tell the two apart")


def _typed_token_after(transcript: Path, since: float) -> str | None:
    """A token pane B's transcript GENUINELY carries in a typed row after `since`.

    The negative control needs something the predicate must answer True for, in
    the same file and the same window as the absence assertion. The plan named
    `nonce_B`, but pane B is the drill's OWN session: it is never armed, so no
    nonce is ever typed into it and `nonce_B` does not exist in this design.
    What does exist is whatever the Owner and the agent actually typed there
    after t0, and that serves the identical purpose.

    Returns the first whitespace-delimited token of the first typed user row
    after `since`, or None when the pane said nothing in the window -- which is
    NOT blindness and must not be reported as a failure.
    """
    try:
        raw = transcript.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("type") != "user" or row.get("toolUseResult") is not None:
            continue
        stamp = row.get("timestamp")
        if not stamp:
            continue
        try:
            when = _dt.datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        if when <= since:
            continue
        content = (row.get("message") or {}).get("content")
        if not isinstance(content, str):
            continue           # a block-shaped body is not a keystroke
        token = content.strip().split()[0] if content.strip().split() else ""
        # Long enough to be a needle rather than a coincidence.
        if len(token) >= 6:
            return token
    return None


INBOX_DIR = Path.home() / ".claude" / "state" / "terminal-inbox"
REAL_LEDGER = Path.home() / ".claude" / "state" / "gsd-autorun-ledger.jsonl"

# The daemon's two refusal prefixes. They are DISJOINT, and the two gates below
# must never accept each other's -- a test asserting only that both rows exist
# passes with the owner leg removed, which is the whole point of separating them.
OWNER_PREFIX = "terminal inbox refused: "
NOOWNER_PREFIX = "no exact-session delivery:"


def _refusal_vocabulary() -> tuple[set[str], Path]:
    """Every reason `decide()` can return with action "refuse", read from source.

    Hardcoding a copy is how a reason renamed in the extension drifts past the
    gate that exists to notice it. The plan named seven; the file defines NINE --
    `deferred-too-long:` and `expired-while-deferred:` were added 2026-09-21, and
    a hardcoded set would already be wrong. That is not a hypothetical drift, it
    is this file's own history.

    Prefixed reasons keep their trailing colon: they are emitted as
    `"deferred-too-long:" + String(session.status)`, so the ledger carries a
    suffix no static vocabulary can know.

    Anchored on `action: "refuse"` so the IGNORE reasons (`no-request`,
    `not-this-window`) and the DEFER reason (`status-`) cannot leak in. Those are
    exactly the answers a NON-owning window gives, and admitting one would
    destroy the property this gate rests on.
    """
    src = REPO / "extension" / "src" / "terminal_inbox.js"
    text = src.read_text(encoding="utf-8")
    return set(re.findall(r'action:\s*"refuse"\s*,\s*reason:\s*"([^"]*)"', text)), src


def _ledger_rows(path: Path) -> list[dict] | None:
    """Parsed rows, or None when the file cannot be read AT ALL.

    None is not "no rows". An unreadable ledger says nothing about whether a
    refusal ever happened, and reporting that absence as a FAIL would be a
    verdict about the subject drawn from a failure of the instrument.
    """
    if not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    rows = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def gates_refusal(run_ledger: Path | None) -> int | None:
    """The two refusal legs, which are NOT interchangeable.

    `V-TWOPANE-OWNER-REFUSED` is the strong one. Its load-bearing property is
    structural, not statistical: `decide()` resolves `ownedTerminals` FIRST
    (terminal_inbox.js:84-86) and every non-owning window returns
    `{action:"ignore"}` there. No refusal branch is reachable without ownership.
    So a ledgered `terminal inbox refused: <reason>` whose reason is in decide()'s
    own refusal vocabulary proves THE OWNING WINDOW READ THE REQUEST AND JUDGED
    IT. That is the claim the phase needs and the weak leg cannot make.

    `V-TWOPANE-NOOWNER-NOT-TYPED` is the weak one, and it is recorded separately
    precisely so the difference lives on the record rather than in a planner's
    head.

    Returns 2 on HARNESS-FAILED, else None.
    """
    vocab, vocab_src = _refusal_vocabulary()
    # Floor. A regex that silently stopped matching reports an empty vocabulary,
    # against which NO ledger reason can ever match -- and the gate would then
    # FAIL, blaming the transport for a broken parser. Seven is the plan's own
    # count; the file currently has nine.
    if len(vocab) < 7:
        return _harness(
            f"only {len(vocab)} refusal reasons parsed out of {vocab_src} "
            f"({sorted(vocab)}) -- the extractor has gone blind, so any verdict "
            "about a ledger reason would be about this regex, not the transport")

    sources: list[tuple[str, Path]] = []
    if run_ledger is not None:
        sources.append(("run-local", run_ledger))
    sources.append(("real", REAL_LEDGER))

    rows: list[tuple[str, dict]] = []
    readable: list[str] = []
    for label, path in sources:
        got = _ledger_rows(path)
        if got is None:
            continue
        readable.append(f"{label}={path}")
        rows.extend((label, r) for r in got)
    if not readable:
        return _harness(
            "no autorun ledger could be read ("
            + "; ".join(f"{lbl}:{p}" for lbl, p in sources)
            + ") -- absence of a refusal row here would be a statement about the "
              "filesystem, not about the transport")

    def _refused(prefix: str) -> list[tuple[str, dict]]:
        return [(lbl, r) for lbl, r in rows
                if r.get("event") == "refused"
                and str(r.get("detail") or "").startswith(prefix)]

    matched = []
    for lbl, r in _refused(OWNER_PREFIX):
        reason = str(r["detail"])[len(OWNER_PREFIX):].strip()
        if reason in vocab or any(v.endswith(":") and reason.startswith(v) for v in vocab):
            matched.append((lbl, r, reason))
    if matched:
        lbl, r, reason = matched[-1]
        _ok("V-TWOPANE-OWNER-REFUSED",
            f"[{lbl} ledger] {reason!r} for session {r.get('session_id')} at "
            f"{r.get('ts')} -- {reason!r} is in decide()'s refusal vocabulary "
            f"({len(vocab)} reasons read from {vocab_src.name} at gate time), and "
            "decide() gates on ownedTerminals BEFORE any refusal is reachable, so "
            "the OWNING window judged this request"
            + ("" if lbl == "run-local" else
               " -- NOTE: from the real ledger, i.e. a live autonomous crossing, "
               "not a row this drill run produced"))
    else:
        _fail("V-TWOPANE-OWNER-REFUSED",
              f"no row with event=refused and detail starting {OWNER_PREFIX!r} "
              f"naming a reason in {sorted(vocab)}; searched {len(rows)} rows "
              f"across {', '.join(readable)}")

    noowner = _refused(NOOWNER_PREFIX)
    if noowner:
        lbl, r = noowner[-1]
        _ok("V-TWOPANE-NOOWNER-NOT-TYPED",
            f"[{lbl} ledger] session {r.get('session_id')} at {r.get('ts')} -- the "
            "daemon's own timeout row. This proves NOTHING WAS TYPED into whichever "
            "window happened to be in front. It does NOT prove any window judged "
            "the request: no owner answered, so decide() may never have run at all. "
            "Not substitutable for V-TWOPANE-OWNER-REFUSED")
    else:
        _fail("V-TWOPANE-NOOWNER-NOT-TYPED",
              f"no row with event=refused and detail starting {NOOWNER_PREFIX!r}; "
              f"searched {len(rows)} rows across {', '.join(readable)}")
    return None


def _drill_sids() -> set[str]:
    """Every session id any drill run recorded, from the run manifests."""
    out: set[str] = set()
    for man in sorted(RUNS.glob("*/manifest.json")):
        try:
            data = json.loads(man.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        for pane in (data.get("panes") or {}).values():
            if isinstance(pane, dict) and pane.get("session_id"):
                out.add(str(pane["session_id"]))
        for key in ("sid", "session_id", "throwaway_sid"):
            if data.get(key):
                out.add(str(data[key]))
    return out


def gate_inbox_drained() -> int | None:
    """T-01-06: the drill must leave the SHARED inbox dir exactly as it found it.

    This is the one assertion about a directory the drill could not sandbox. A
    leftover request for a dead sid is re-read by EVERY window with the extension
    loaded, every 500 ms (extension.js:38, :63) -- so a forgotten file makes the
    drill a small permanent tax on the Owner's real windows, forever, silently.

    Returns 2 on HARNESS-FAILED, else None.
    """
    sids = _drill_sids()
    if not sids:
        return _harness(
            f"no drill session ids found in {RUNS}/*/manifest.json -- with an empty "
            "needle set this gate would pass against any inbox whatsoever")
    if not INBOX_DIR.is_dir():
        return _harness(
            f"{INBOX_DIR} does not exist -- 'no drill file is present' would be "
            "true of a directory that cannot hold one, which is not the claim")
    try:
        entries = sorted(p.name for p in INBOX_DIR.iterdir())
    except OSError as exc:
        return _harness(f"{INBOX_DIR} unreadable: {exc.__class__.__name__}: {exc}")

    # Green control, inline: prove the predicate can say YES before trusting it
    # to say no. A substring test that matched nothing -- a mangled sid set, a
    # normalisation slip -- reports a clean inbox identically to a clean inbox.
    probe = f"{sorted(sids)[0]}.req.json"
    if not any(s in probe for s in sids):
        return _harness(
            f"the drill-sid predicate does not match even a synthetic {probe} -- "
            "every absence it reports would be worthless")

    hits = [n for n in entries if any(s in n for s in sids)]
    # The two classes cost different things, and one evidence string cannot be
    # honest about both. The plan's harm argument -- "re-read by every window
    # every 500 ms" -- is TRUE OF REQUESTS ONLY: extension.js:69 filters
    # `.endsWith(".req.json")`, and the watcher at :470 does the same. An ack is
    # read by the ONE daemon that wrote the matching request, by sid
    # (extension.js:57). Quoting the request mechanism over an ack would be a
    # measured-sounding claim about a code path that does not run -- measured
    # 2026-09-21, when this gate's first version did exactly that.
    recurring = [n for n in hits if n.endswith(".req.json") or n.endswith(".claimed")]
    inert = [n for n in hits if n not in recurring]
    if recurring:
        _fail("V-TWOPANE-INBOX-DRAINED",
              f"{len(recurring)} drill REQUEST(s) left in {INBOX_DIR}: {recurring} "
              "-- every window with the extension loaded re-reads these every 500 ms "
              f"(extension.js:69, :470). Also present: {len(inert)} inert ack(s).")
    elif inert:
        _fail("V-TWOPANE-INBOX-DRAINED",
              f"no drill request remains, but {len(inert)} drill ack(s) do: {inert}. "
              "These are NOT a recurring cost -- an ack is read only by the daemon "
              "that wrote the matching request, keyed by sid (extension.js:57), and "
              "no window scans for them. They are still the drill's litter in a "
              "directory it does not own, which is what T-01-06 names. "
              "ATTRIBUTION LIMIT: the needle is a SESSION ID, and the live drill "
              "armed REAL sessions rather than the throwaway sids the plan's "
              "containment clause assumed -- so for a session that also carries "
              "real traffic, drill residue and the Owner's own ack are "
              "indistinguishable by name. This gate names candidates; it cannot "
              "prove they are ours, and nothing should be deleted on its say-so.")
    else:
        _ok("V-TWOPANE-INBOX-DRAINED",
            f"none of {len(entries)} file(s) in {INBOX_DIR} carries any of "
            f"{len(sids)} drill sid(s); the predicate matches {probe!r}, so the "
            "absence is a measurement")
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runid", default="",
                    help="a real drill run's id; omit to run only the unit gates")
    args = ap.parse_args(argv)

    drill = _load("two_pane_drill")
    lr = sys.modules.get("gsd_long_run") or _load("gsd_long_run")
    gates_unit(drill, lr)

    # The refusal legs and the shared-inbox check are claims about the TRANSPORT
    # and the SHARED directory, not about one drill run, so they are judged in
    # both modes -- including the plan's own <verify> command, which passes no
    # --runid. A gate that only ran in the mode nobody invokes is not a gate.
    run_ledger = (RUNS / args.runid / "state" / "gsd-autorun-ledger.jsonl") if args.runid else None
    for gate in (lambda: gates_refusal(run_ledger), gate_inbox_drained):
        rc = gate()
        if rc:
            return rc

    if not args.runid:
        total = passes + fails
        print(f"TWOPANE_PASS={passes}/{total}  threshold={total}/{total}  (unit, refusal "
              f"and inbox gates; no live two-pane drill evidence was judged)")
        return 0 if fails == 0 else 1

    manifest = RUNS / args.runid / "manifest.json"
    if not manifest.is_file():
        return _harness(f"no drill evidence at {manifest} -- run tools/two_pane_drill.py first")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return _harness(f"{manifest} unreadable: {exc.__class__.__name__}: {exc}")

    pane = (data.get("panes") or {}).get("A")
    if not pane:
        return _harness("pane A was never armed")
    for key in ("transcript", "nonce", "t0"):
        if key not in pane:
            return _harness(f"pane A has no {key} -- it was armed but never fired")
    transcript = Path(pane["transcript"])
    if not transcript.is_file():
        return _harness(f"pane A's transcript is gone: {transcript}")

    # The real three-part rule, imported rather than reimplemented: a second copy
    # would agree with the first on the day it was written and not afterwards.
    got = lr.user_issued_command_since(transcript, pane["nonce"], pane["t0"])
    if got:
        _ok("V-TWOPANE-A-RECEIVED",
            f"{pane['nonce']} appears in {transcript.name} after t0={pane['t0']}")
    else:
        _fail("V-TWOPANE-A-RECEIVED",
              f"{pane['nonce']} absent from {transcript.name} after t0={pane['t0']}")

    # Exactness is a claim about TWO panes. "A received it" alone is delivery.
    b = (data.get("panes") or {}).get("B")
    if not b:
        return _harness("no pane B recorded -- the run cannot speak about exactness, "
                        "only about delivery")
    b_transcript = Path(b["transcript"])
    if not b_transcript.is_file():
        return _harness(f"pane B's transcript is gone: {b_transcript}")
    b_got = lr.user_issued_command_since(b_transcript, b["nonce"], b["t0"])
    if not b_got:
        _ok("V-TWOPANE-B-UNTOUCHED",
            f"{b['nonce']} never appears in {b_transcript.name} after t0={b['t0']} "
            f"({b.get('role', 'second pane')})")
    else:
        _fail("V-TWOPANE-B-UNTOUCHED",
              f"{b['nonce']} reached {b_transcript.name} -- the line went to a pane that "
              "did not own the request")

    # THE control that makes the absence above mean anything. Without it,
    # V-TWOPANE-B-UNTOUCHED is satisfied identically by an instrument that cannot
    # see pane B at all -- a wrong path, a stale handle, an unreadable file -- and
    # a permanent silent pass is worse than a missing gate, because it reports as
    # proof. The plan calls this leg load-bearing; it was never coded.
    #
    # Same predicate, same transcript, same window, same `since`. Only the needle
    # changes: from A's nonce (must be absent) to something B really typed (must
    # be present). One of the two must be True or the instrument is blind.
    # TWO TIERS, because the first version of this control was unevaluable on the
    # very run it was written for (`live2`, 2026-09-21). It required a TYPED row
    # in B inside the observation window; the drill seals ~15 s after firing, and
    # an agent pane emits assistant and tool rows in that window, not keystrokes.
    # A control that cannot run is not a control.
    #
    #   strong -- a typed row AFTER t0: the predicate sees B in THIS window.
    #   weak   -- a typed row anywhere: the predicate can read and parse B's
    #             transcript at all, which is still decisive about BLINDNESS,
    #             the failure the control exists to exclude. It says less about
    #             currency, so it is labelled and never silently substituted.
    #
    # Only when B has no typed row at any time is this genuinely unjudgeable.
    # B's IDENTITY and the BLINDNESS control are two claims, and conflating them
    # was my error (2026-09-21, runid live3). `own_nonce` is how `arm` identified
    # B, using drill._carries_nonce -- "a typed row carries it ANYWHERE in its
    # text". The blindness control must use the SAME predicate as B-UNTOUCHED,
    # which requires a row to BEGIN with the needle. B's arming prompt reads
    # "Reply with a single line beginning DRILL-B-<runid> and nothing else", so
    # the nonce sits mid-sentence, and the only row that STARTS with it is
    # Claude's ASSISTANT reply -- which user_issued_command_since rightly
    # ignores. A tier built on that needle could never pass, whatever the
    # manifest said. Identity gets its own gate and the predicate that
    # established it.
    own = b.get("own_nonce")
    if own:
        if drill._carries_nonce(b_transcript, own):
            _ok("V-TWOPANE-B-IS-THE-ARMED-PANE",
                f"{b_transcript.name} carries {own!r} -- B is the session it was armed "
                "as, by the same rule arm() used to find it")
        else:
            _fail("V-TWOPANE-B-IS-THE-ARMED-PANE",
                  f"{own!r} is absent from {b_transcript.name} -- the manifest's pane B "
                  "is not the session that was armed, so it is the wrong control")

    token = _typed_token_after(b_transcript, b["t0"])
    since_for_check, tier = b["t0"], "after t0"
    if token is None:
        token = _typed_token_after(b_transcript, 0.0)
        since_for_check, tier = 0.0, "anywhere in the transcript (weaker: not in-window)"
    if token is None:
        # Not a verdict about exactness. Exit 2, never a silent pass.
        return _harness(
            f"pane B ({b_transcript.name}) carries no typed row at any time, so "
            "V-TWOPANE-B-UNTOUCHED cannot be distinguished from an instrument that "
            "cannot see pane B at all.")
    if lr.user_issued_command_since(b_transcript, token, since_for_check):
        _ok("V-TWOPANE-B-INSTRUMENT-CAN-SEE",
            f"the same predicate finds {token!r} in {b_transcript.name} [{tier}] -- so "
            f"the absence of {b['nonce']} is a measurement, not blindness")
    else:
        _fail("V-TWOPANE-B-INSTRUMENT-CAN-SEE",
              f"{token!r} is present in {b_transcript.name} [{tier}] but the predicate "
              "does not see it -- every absence assertion over this pane is worthless")

    total = passes + fails
    print(f"TWOPANE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
