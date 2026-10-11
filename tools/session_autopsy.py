#!/usr/bin/env python3
"""Session autopsy -- the context rent of ONE Claude Code session.

Context rent is what resident context costs because it is re-read on every
later call. The 2026-09-27 KobiiSports incident (session 04b41ed7) is the
reason this exists: 326 calls over 3 days at ~409 k resident each. Two
different levers hide inside that number, and this tool keeps them apart:

  floor              what call #1 already carried (system, tools, always-on
                     instructions, memory). A fresh session pays it again.
  growth above floor what the session accumulated. Only this is what a
                     fresh epoch can remove.

Reader: tools/tis_observed.py (one call counted once). Prices: the dated
vault/pricing/anthropic_YYYY-MM.json in force for each call's month; a model
with no price is UNKNOWN, never a default rate and never zero. USD is API
list-price equivalent; a subscription is not billed this way.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import pricing_source  # noqa: E402
import tis_observed as tis  # noqa: E402

DEFAULT_TTL_S = 3600  # Claude Code on a subscription writes 1h cache entries
_DATED = re.compile(r"^anthropic_(\d{4})-(\d{2})\.json$")


def _price_books(pricing_dir: Path = pricing_source.PRICING_DIR) -> list[tuple[tuple[int, int], dict, str]]:
    books = []
    for p in pricing_dir.glob("anthropic_*.json"):
        m = _DATED.match(p.name)
        if not m:
            continue
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        books.append(((int(m.group(1)), int(m.group(2))), data.get("models") or {},
                      f"{p.name} (fetched {data.get('fetched_iso', '?')})"))
    return sorted(books)


def _model_row(models: dict, model_id: str) -> Optional[dict]:
    for key in sorted(models, key=len, reverse=True):  # opus-5-5 before opus-5
        if key in (model_id or ""):
            return models[key]
    return None


def _ts(s: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
    except ValueError:
        return None


def _cost_parts(usage: dict, row: dict) -> dict:
    """Per-category USD through tis_observed.cost_usd, so the TTL split has one owner."""
    def part(keys):
        return tis.cost_usd({k: usage[k] for k in keys if k in usage}, row)[0]
    return {"input": part(("input_tokens",)),
            "cache_write": part(("cache_creation_input_tokens", "cache_creation")),
            "cache_read": part(("cache_read_input_tokens",)),
            "output": part(("output_tokens",))}


def autopsy(path: Path, prices: Optional[dict] = None, ttl_s: int = DEFAULT_TTL_S) -> dict:
    """prices: {model: row} to price every call with (tests); default = the dated books."""
    calls, usage_lines, synthetic, bad = tis._calls_in(Path(path))
    books = [] if prices is not None else _price_books()
    sources = set()
    cost = {"input": 0.0, "cache_write": 0.0, "cache_read": 0.0, "output": 0.0}
    unpriced = 0
    resident, times = [], []
    gaps = rewrite_after_gap = 0
    cc_total = 0
    read_rate = None
    for i, c in enumerate(calls):
        u = c["usage"]
        ctx = tis._context_of(u)
        resident.append(ctx)
        t = _ts(c.get("ts"))
        cc = tis._int(u.get("cache_creation_input_tokens"))
        cc_total += cc
        if i and t and times[-1] and (t - times[-1]).total_seconds() > ttl_s:
            gaps += 1
            rewrite_after_gap += cc
        times.append(t)
        if prices is not None:
            row = _model_row(prices, c["model"])
        else:
            ym = (t.year, t.month) if t else None
            book = next((b for b in reversed(books) if ym and b[0] <= ym), books[-1] if books else None)
            row = _model_row(book[1], c["model"]) if book else None
            if row and book:
                sources.add(book[2])
        if row is None:
            unpriced += 1
            continue
        read_rate = row["cache_read"]
        for k, v in _cost_parts(u, row).items():
            cost[k] += v or 0.0
    total_usd = None if unpriced or not calls else sum(cost.values())
    floor = resident[0] if resident else 0
    growth = sum(max(0, r - floor) for r in resident)
    n = len(resident)
    curve = []
    for q in (0.1, 0.25, 0.5, 0.75, 0.9, 1.0):
        i = max(0, min(n - 1, int(n * q) - 1))
        if n:
            curve.append({"call": i + 1, "resident": resident[i],
                          "ts": times[i].isoformat() if times[i] else None})
    return {
        "path": str(path), "calls": n, "usage_lines": usage_lines,
        "synthetic_skipped": synthetic, "bad_lines": bad,
        "span": [times[0].isoformat() if times and times[0] else None,
                 times[-1].isoformat() if times and times[-1] else None],
        "floor_tokens": floor,
        "resident_total": sum(resident), "resident_max": max(resident, default=0),
        "resident_mean": (sum(resident) / n) if n else None,
        "growth_above_floor_tokens": growth,
        "growth_share": (growth / sum(resident)) if resident and sum(resident) else None,
        "cache_creation_tokens": cc_total,
        "gaps_over_ttl": gaps, "ttl_s": ttl_s, "rewrite_after_gap_tokens": rewrite_after_gap,
        "curve": curve,
        "cost_usd": {**{k: (v if not unpriced else None) for k, v in cost.items()}, "total": total_usd},
        "unpriced_calls": unpriced,
        "price_source": sorted(sources) or (["caller-supplied"] if prices is not None else []),
        # Re-reading growth-above-floor at the read rate is the MOST a fresh epoch could
        # have saved: it ignores rehydration writes and the capsule it would carry.
        "fresh_epoch_saving_bound": {
            "kind": "UPPER_BOUND",
            "usd": (growth * read_rate / 1_000_000) if read_rate is not None and not unpriced else None,
            "excludes": "rehydration cache writes, continuation capsule, quality effects"},
    }


_EDITS = ("Edit", "Write", "MultiEdit", "NotebookEdit")


def _result_chars(content) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(b.get("text", "")) for b in content if isinstance(b, dict))
    return 0


def growth_sources(path: Path) -> dict:
    """What the session accumulated, by content kind and by tool (chars, a token ESTIMATE).

    Blocks are counted once: tool_use/tool_result by id, text/thinking by (message id, text).
    Subagent sidechain rows are the subagent's context, not this one's, and are skipped.
    A Read counts as an unchanged re-read only for the same path AND page (offset/limit) with no
    Edit/Write of that path in between; a re-read after an edit is counted apart, it is legitimate.
    """
    kinds = {"tool_result": 0, "user_text": 0, "assistant_text": 0, "thinking": 0}
    by_tool: dict[str, int] = {}
    uses: dict[str, tuple] = {}
    seen_blocks: set = set()
    read_pages: set = set()
    edited_since: set = set()
    rd = {"calls": 0, "reread_unchanged": 0, "reread_unchanged_chars": 0, "reread_after_edit": 0}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict) or row.get("isSidechain"):
                continue
            msg = row.get("message") if isinstance(row.get("message"), dict) else {}
            content = msg.get("content")
            if isinstance(content, str):
                if row.get("type") == "user" and ("u", content) not in seen_blocks:
                    seen_blocks.add(("u", content))
                    kinds["user_text"] += len(content)
                continue
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict):
                    continue
                t = b.get("type")
                if t == "tool_use":
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    uses[b.get("id")] = (b.get("name") or "?", inp)
                    if b.get("name") in _EDITS and inp.get("file_path"):
                        edited_since.add(inp["file_path"])
                elif t == "tool_result":
                    key = ("r", b.get("tool_use_id"))
                    if key in seen_blocks:
                        continue
                    seen_blocks.add(key)
                    n = _result_chars(b.get("content"))
                    name, inp = uses.get(b.get("tool_use_id"), ("?", {}))
                    kinds["tool_result"] += n
                    by_tool[name] = by_tool.get(name, 0) + n
                    fp = inp.get("file_path")
                    if name == "Read" and fp:
                        rd["calls"] += 1
                        page = (fp, inp.get("offset"), inp.get("limit"))
                        if fp in edited_since:
                            if any(p[0] == fp for p in read_pages):
                                rd["reread_after_edit"] += 1
                            read_pages = {p for p in read_pages if p[0] != fp}
                            edited_since.discard(fp)
                        elif page in read_pages:
                            rd["reread_unchanged"] += 1
                            rd["reread_unchanged_chars"] += n
                        read_pages.add(page)
                elif t in ("text", "thinking"):
                    body = b.get(t, "")
                    key = (t, msg.get("id"), body)
                    if key in seen_blocks:
                        continue
                    seen_blocks.add(key)
                    kinds["thinking" if t == "thinking" else
                          ("assistant_text" if row.get("type") == "assistant" else "user_text")] += len(body)
    return {"unit": "chars (token ESTIMATE ~chars/4)", "by_kind": kinds,
            "by_tool": dict(sorted(by_tool.items(), key=lambda kv: -kv[1])), "read": rd}


# ---------------------------------------------------------------- economic roles (CDC C1)
ROLES = ("READ", "REREAD", "RESEARCH", "PLAN", "IMPLEMENT", "PROOF", "CONTROL", "STATUS",
         "RECOVERY", "REPAIR", "CONTEXT_FAULT", "NOVELTY")
_GIT = r"(?:\bgit(?:\.exe)?|\$\{?g(?:it)?\}?)['\"]?\s+(?:-\S+\s+)*"
_PROOF = re.compile(r"pytest|unittest|\btest_\w+\.(?:py|js)|\w+_test\.(?:py|js)|npm (?:run )?test|"
                    r"land_worktree|\bgate\b|--selftest|\bnpx (?:jest|vitest)", re.I)
_STATUS = re.compile(r"handoff|status_card|render_status|--status\b|\bstatus --render")
_CONTROL = re.compile(_GIT + r"(?:status|log|diff|branch|rev-parse|show|worktree|fetch)\b|"
                      r"\b(?:mission|chain|capital|goal)[-_ ]?\w*(?:\.py|\.js)?\s+(?:status|show|list|tick)|"
                      r"\bmission_|chain_status|capital-status", re.I)
_COMMIT = re.compile(_GIT + r"commit\b", re.I)
_FAIL = re.compile(r"\bFAILED?\b|Traceback \(most recent|\b[1-9]\d* (?:failed|failures?)\b|\bRED\b|AssertionError")
_PLAN_PATH = re.compile(r"(?:^|[\\/])\.planning[\\/]|vault[\\/]plans[\\/]")
_CLAIM = re.compile(r"Status: DONE|\bPROVEN\b")
PLAN_TEXT_CHARS = 600


def _norm(p) -> str:
    return str(p or "").replace("\\", "/")


def _processed(u: dict) -> int:
    return tis._context_of(u) + tis._int(u.get("output_tokens"))


def _flat(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def _is_fail(res: Optional[dict]) -> bool:
    if res is None:
        return False
    if res.get("is_error"):
        return True
    txt = res.get("text", "")
    return bool(_FAIL.search(txt)) and not re.search(r"\b0 failed\b", txt)


def _scan(path: Path, tag: str) -> list[dict]:
    """Ordered unique calls with tool uses, tool results and text; epoch markers inline."""
    calls: dict = {}
    order: list = []
    results: dict = {}
    first_user = ""
    seq = 0
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        for raw in fh:
            try:
                row = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(row, dict):
                continue
            msg = row.get("message") if isinstance(row.get("message"), dict) else {}
            content = msg.get("content")
            seq += 1
            if row.get("isCompactSummary") or row.get("subtype") == "compact_boundary":
                order.append(("EPOCH", seq))
                continue
            if row.get("type") == "user":
                if isinstance(content, str):
                    if not first_user:
                        first_user = content
                    if content.lstrip().startswith(("/clear", "<command-name>/clear")):
                        order.append(("EPOCH", seq))
                elif isinstance(content, list):
                    for b in content:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "tool_result":
                            results[b.get("tool_use_id")] = {
                                "is_error": bool(b.get("is_error")), "text": _flat(b.get("content"))}
                        elif b.get("type") == "text" and not first_user:
                            first_user = b.get("text", "")
                continue
            if row.get("type") != "assistant" or not isinstance(msg.get("usage"), dict):
                continue
            if msg.get("model") == tis.SYNTHETIC_MODEL:
                continue
            key = (msg.get("id"), row.get("requestId"))
            if key == (None, None):
                key = ("line", seq)
            if key not in calls:
                calls[key] = {"tokens": 0, "uses": [], "text": "", "src": tag}
                order.append(key)
            c = calls[key]
            c["tokens"] = _processed(msg["usage"])
            if isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_use":
                        c["uses"].append((b.get("id"), b.get("name") or "?",
                                          b.get("input") if isinstance(b.get("input"), dict) else {}))
                    elif b.get("type") == "text":
                        c["text"] += b.get("text", "")
    out = []
    for k in order:
        if k[0] == "EPOCH":
            out.append({"epoch": True})
            continue
        c = calls[k]
        c["results"] = {i: results.get(i) for i, _, _ in c["uses"]}
        c["first_user"] = first_user
        out.append(c)
    return out


def classify_calls(items: list[dict]) -> list[dict]:
    """Deterministic role per call. Returns [{role, tokens, src, trans}]."""
    read_since: set = set()    # paths read in this epoch and not edited since
    ever_read: set = set()
    failed: set = set()
    red = False                # last proof run was red
    edit_seen = False
    out = []
    for c in items:
        if c.get("epoch"):
            read_since.clear()
            continue
        capsule = _norm(c.get("first_user"))
        found = set()
        trans = {"commit": 0, "new_file": 0, "claim": 0, "red_green": 0}
        for uid, name, inp in c["uses"]:
            res = c["results"].get(uid)
            fp = _norm(inp.get("file_path") or inp.get("path"))
            cmd = inp.get("command", "") if isinstance(inp.get("command"), str) else ""
            sig = (name, json.dumps(inp, sort_keys=True, default=str))
            if sig in failed:
                found.add("RECOVERY")
            if _is_fail(res):
                failed.add(sig)
            if name == "Read" and fp:
                if fp in read_since:
                    found.add("REREAD")
                elif capsule and (fp in capsule or Path(fp).name in capsule):
                    found.add("CONTEXT_FAULT")
                else:
                    found.add("READ")
                read_since.add(fp)
                ever_read.add(fp)
            elif name in ("Grep", "Glob", "LS"):
                found.add("READ")
            elif name in ("WebSearch", "WebFetch"):
                found.add("RESEARCH")
            elif name in _EDITS and fp:
                body = str(inp.get("content") or inp.get("new_string") or "")
                if _CLAIM.search(body):
                    trans["claim"] += 1
                if _PLAN_PATH.search(fp):
                    found.add("PLAN")
                elif red:
                    found.add("REPAIR")
                elif name == "Write" and fp not in ever_read:
                    found.add("NOVELTY")
                    trans["new_file"] += 1
                else:
                    found.add("IMPLEMENT")
                read_since.discard(fp)
                edit_seen = True
            elif name in ("Bash", "PowerShell"):
                if _COMMIT.search(cmd) and res is not None and not _is_fail(res):
                    trans["commit"] += 1
                if _STATUS.search(cmd):
                    found.add("STATUS")
                elif _PROOF.search(cmd):
                    found.add("PROOF")
                    if res is not None:
                        bad = _is_fail(res)
                        if red and not bad:
                            trans["red_green"] += 1
                        red = bad
                elif _CONTROL.search(cmd):
                    found.add("CONTROL")
        if _CLAIM.search(c["text"]):
            trans["claim"] += 1
        if not c["uses"] and len(c["text"]) >= PLAN_TEXT_CHARS and not edit_seen:
            found.add("PLAN")
        role = next((r for r in ("RECOVERY", "REPAIR", "CONTEXT_FAULT", "REREAD", "PLAN", "NOVELTY",
                                 "IMPLEMENT", "PROOF", "STATUS", "CONTROL", "RESEARCH", "READ")
                     if r in found), "unattributed")
        out.append({"role": role, "tokens": c["tokens"], "src": c["src"], "trans": trans})
    return out


def roles(path: Path) -> dict:
    """Economic role table for a session transcript plus its <sid>/subagents/*.jsonl."""
    path = Path(path)
    files = [(path, "main")]
    sub = path.with_suffix("") / "subagents"
    if sub.is_dir():
        files += [(f, "sub:" + f.stem) for f in sorted(sub.glob("*.jsonl"))]
    rows = []
    for f, tag in files:
        rows += classify_calls(_scan(f, tag))
    total = sum(r["tokens"] for r in rows)
    table = {k: {"calls": 0, "tokens": 0, "main_tokens": 0, "subagent_tokens": 0}
             for k in (*ROLES, "unattributed")}
    tr = {"commit": 0, "new_file": 0, "claim": 0, "red_green": 0}
    for r in rows:
        t = table[r["role"]]
        t["calls"] += 1
        t["tokens"] += r["tokens"]
        t["main_tokens" if r["src"] == "main" else "subagent_tokens"] += r["tokens"]
        for k, v in r["trans"].items():
            tr[k] += v
    for t in table.values():
        t["share"] = (t["tokens"] / total) if total else None
    n_tr = sum(tr.values())
    return {"path": str(path), "files": [t for _, t in files], "calls": len(rows),
            "processed_tokens": total, "roles": table,
            "unattributed_share": table["unattributed"]["share"],
            "transitions": {**tr, "total": n_tr,
                            "tokens_per_transition": (total / n_tr) if n_tr else None,
                            "tokens_per": {k: (total / v if v else None) for k, v in tr.items()}}}


def _fmt_roles(r: dict) -> str:
    L = [f"roles    {r['calls']} calls, {r['processed_tokens']:,} processed tokens over {len(r['files'])} file(s)",
         f"{'role':14}{'calls':>7}{'tokens':>16}{'share':>8}{'sub tokens':>16}"]
    for k, v in sorted(r["roles"].items(), key=lambda kv: -kv[1]["tokens"]):
        L.append(f"{k:14}{v['calls']:>7}{v['tokens']:>16,}{(v['share'] or 0):>8.1%}{v['subagent_tokens']:>16,}")
    L.append(f"UNATTRIBUTED share {(r['unattributed_share'] or 0):.1%}")
    t = r["transitions"]
    L.append("transitions " + "  ".join(f"{k} {t[k]}" for k in ("commit", "new_file", "claim", "red_green"))
             + f"  total {t['total']}  tokens/transition "
             + ("n/a" if t["tokens_per_transition"] is None else f"{t['tokens_per_transition']:,.0f}"))
    return "\n".join(L)


def _resolve(arg: str) -> Path:
    p = Path(arg)
    if p.is_file():
        return p
    hits = sorted(tis.PROJECTS_DIR.glob(f"*/{arg}*.jsonl"))
    if not hits:
        raise SystemExit(f"no transcript matches {arg!r} under {tis.PROJECTS_DIR}")
    return hits[0]


def _fmt(r: dict) -> str:
    c = r["cost_usd"]
    usd = lambda v: "UNKNOWN" if v is None else f"${v:,.2f}"
    lines = [
        f"session  {Path(r['path']).stem}  {r['span'][0]} -> {r['span'][1]}",
        f"calls    {r['calls']} ({r['usage_lines']} usage lines; one call counted once)",
        f"floor    {r['floor_tokens']:,} tokens resident at call #1",
        f"resident mean {r['resident_mean'] or 0:,.0f}  max {r['resident_max']:,}  total re-read {r['resident_total']:,}",
        f"growth above floor {r['growth_above_floor_tokens']:,} ({(r['growth_share'] or 0):.0%} of re-read volume)",
        f"cache writes {r['cache_creation_tokens']:,}; {r['gaps_over_ttl']} gaps > {r['ttl_s']}s TTL "
        f"forced {r['rewrite_after_gap_tokens']:,} of them",
        f"cost (API list equivalent)  read {usd(c['cache_read'])}  write {usd(c['cache_write'])}  "
        f"output {usd(c['output'])}  input {usd(c['input'])}  TOTAL {usd(c['total'])}"
        + (f"  [{r['unpriced_calls']} unpriced calls]" if r["unpriced_calls"] else ""),
        f"fresh-epoch saving UPPER BOUND {usd(r['fresh_epoch_saving_bound']['usd'])} "
        f"(excludes {r['fresh_epoch_saving_bound']['excludes']})",
        f"prices   {', '.join(r['price_source']) or 'none'}",
        "curve    " + "  ".join(f"#{p['call']}:{p['resident']:,}" for p in r["curve"]),
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("session", help="transcript path or session id (prefix ok)")
    ap.add_argument("--ttl", type=int, default=DEFAULT_TTL_S)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--roles", action="store_true", help="economic role per call (+ subagents)")
    a = ap.parse_args(argv)
    path = _resolve(a.session)
    if a.roles:
        rr = roles(path)
        print(json.dumps(rr, indent=2) if a.json else _fmt_roles(rr))
        return 0
    r = autopsy(path, ttl_s=a.ttl)
    r["growth_sources"] = growth_sources(path)
    if a.json:
        print(json.dumps(r, indent=2, default=str))
    else:
        g = r["growth_sources"]
        tot = sum(g["by_kind"].values()) or 1
        print(_fmt(r))
        print("growth   " + "  ".join(f"{k} {v / tot:.0%}" for k, v in g["by_kind"].items())
              + f"  ({g['unit']})")
        print("by tool  " + "  ".join(f"{k} {v:,}" for k, v in list(g["by_tool"].items())[:6]))
        rd = g["read"]
        print(f"reads    {rd['calls']}  unchanged re-reads {rd['reread_unchanged']} "
              f"({rd['reread_unchanged_chars']:,} chars)  re-reads after edit {rd['reread_after_edit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
