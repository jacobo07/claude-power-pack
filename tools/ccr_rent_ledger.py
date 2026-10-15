#!/usr/bin/env python3
"""ccr_rent_ledger.py -- Context Rent Ledger: what a session's FIRST model call is made of (0 model calls).

Plan: .planning/workstreams/ccr-v5 Phase 1 (plan 01-01). Extends tools/ccr_anatomy.py: the class vocabulary and
the evidence for each class come from anatomy.classify, so there is one source for "reducible / eliminable /
irreducible" and this module never grades a category on its own authority.

Input is a Claude Code transcript (<project dir>/<sid>.jsonl). Before the first assistant usage row the
transcript carries, as `attachment` records, everything the host sent that is not the tool schema block: the
instruction files (CLAUDE.md, rules, auto-memory), hook injections, skill / agent / deferred-tool listings, MCP
instructions, the system-prompt snapshot, the environment, and the first user message. Their BYTES are measured.
Tokens are not: `calibrate` fits ctx(call 1) = c0 + k * counted_bytes across sessions, so k (tokens per byte) is a
fitted quantity with an R2, and c0 is the part no attachment explains (tool schemas + framing + calibration
error). That intercept is never split: UNKNOWN is never zero, and a negative per-session residual is reported as
None, not clipped to 0.

CLI:
  table --dir DIR [--min-ctx N]            ledger for the sessions with call-1 ctx >= N (default 150000)
  json  --dir DIR --out PATH [--min-ctx N] the same, machine readable
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_anatomy  # noqa: E402  (single source of the class vocabulary)

CATEGORIES = ('constitution', 'rules', 'memory', 'hook_injections', 'skills', 'agent_listing', 'deferred_tools',
              'mcp_instructions', 'system_prompt', 'environment', 'file_attach', 'other_attach', 'prompt')
RESIDUAL = 'tool_schemas+framing'
LEDGER_COLUMNS = ('category', 'bytes', 'tokens', 'share', 'basis', 'cls', 'age_axis', 'class_evidence')
# Which ccr_anatomy bucket grades each category. None = no measurement exists for it.
ANATOMY_BUCKET = {
    'constitution': 'attach:instructions', 'rules': 'attach:instructions', 'memory': 'section:memory',
    'hook_injections': 'attach:hook_additional_context', 'skills': 'attach:skill_listing',
    'agent_listing': 'attach:agent_listing_delta', 'deferred_tools': 'attach:deferred_tools_delta',
    'mcp_instructions': 'attach:mcp_instructions_delta', 'system_prompt': 'section:heron_brook',
    'environment': 'attach:environment', 'prompt': 'prompt', RESIDUAL: 'tool_schemas+framing',
    'file_attach': None, 'other_attach': None,
}
# Driver axis by construction. PROJECT: grows with the project's accumulated config. EPOCH: set by this epoch's
# own task. HOST: set by the host build and tool set. The empirical drift in `age_split` tests the PROJECT rows.
AGE_AXIS = {
    'constitution': 'PROJECT', 'rules': 'PROJECT', 'memory': 'PROJECT', 'skills': 'PROJECT', 'agent_listing': 'PROJECT',
    'deferred_tools': 'PROJECT', 'mcp_instructions': 'PROJECT', 'hook_injections': 'EPOCH', 'prompt': 'EPOCH',
    'file_attach': 'EPOCH', 'other_attach': 'EPOCH', 'system_prompt': 'HOST', 'environment': 'HOST', RESIDUAL: 'HOST',
}
ATTACH_CATEGORY = {
    'hook_additional_context': 'hook_injections', 'hook_system_message': 'hook_injections',
    'skill_listing': 'skills', 'agent_listing_delta': 'agent_listing', 'deferred_tools_delta': 'deferred_tools',
    'deferred_tools_record': 'deferred_tools', 'mcp_instructions_delta': 'mcp_instructions',
    'prompt_snapshot': 'system_prompt', 'environment': 'environment', 'model': 'environment',
    'session_context': 'environment', 'date': 'environment', 'file': 'file_attach',
}
# hook_success repeats the hook's stdout (the same text arrives as hook_additional_context), hook_cancelled has none.
NOT_COUNTED = {'hook_success', 'hook_cancelled'}
G1_HOST_FIXED_SHARE = 0.70
HOST_FIXED_CLASSES = ('IRREDUCIBLE', 'HOST_LIMITED')


def _blen(s: str) -> int:
    return len(s.encode('utf-8', errors='replace'))


def instruction_category(f: dict) -> str:
    path = str(f.get('path', '')).replace('/', '\\').lower()
    if f.get('type') == 'AutoMem':
        return 'memory'
    return 'rules' if '\\rules\\' in path else 'constitution'


def attachment_bytes(a: dict) -> dict[str, int]:
    """Bytes this attachment adds, by category ({} when the host does not send it)."""
    t = a.get('type')
    if t in NOT_COUNTED:
        return {}
    if t == 'instructions':
        out: dict[str, int] = {}
        for f in a.get('files') or []:
            c = instruction_category(f)
            out[c] = out.get(c, 0) + _blen(str(f.get('content', '')))
        return out
    if t == 'prompt_snapshot':
        sp = a.get('systemPrompt') or []
        return {'system_prompt': sum(_blen(str(x)) for x in (sp if isinstance(sp, list) else [sp]))}
    cat = ATTACH_CATEGORY.get(t, 'other_attach')
    return {cat: _blen(json.dumps(a, ensure_ascii=False))}


def measure_session(path: Path) -> dict | None:
    """{sid, ts, ctx, bytes{category}} up to the first assistant usage row, or None if the session has no model call."""
    by: dict[str, int] = {}
    ts = None
    sid = path.stem
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get('isSidechain'):
                    continue
                ts = ts or o.get('timestamp')
                m = o.get('message') or {}
                t = o.get('type')
                if t == 'assistant' and m.get('usage') and not str(m.get('model', '')).startswith('<'):
                    u = m['usage']
                    ctx = int(u.get('input_tokens', 0)) + int(u.get('cache_read_input_tokens', 0)) + int(u.get('cache_creation_input_tokens', 0))
                    if ctx > 0:
                        return {'sid': sid, 'ts': ts or '', 'ctx': ctx, 'bytes': by}
                elif t == 'attachment':
                    for c, n in attachment_bytes(o.get('attachment') or {}).items():
                        by[c] = by.get(c, 0) + n
                elif t == 'user' and not o.get('isMeta'):
                    c = m.get('content')
                    by['prompt'] = by.get('prompt', 0) + _blen(c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
    except OSError:
        return None
    return None


def calibrate(rows: list[dict]) -> dict:
    """OLS ctx1 = c0 + k*counted_bytes. `ok` False (k, c0 None) when n < 10 or R2 < 0.5: no token split is claimed."""
    xs = [float(sum(r['bytes'].values())) for r in rows]
    ys = [float(r['ctx']) for r in rows]
    n = len(rows)
    out = {'n': n, 'k_tok_per_byte': None, 'c0': None, 'r2': None, 'ok': False}
    if n < 10:
        return out
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return out
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    c0 = my - k * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (c0 + k * x)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    out.update(k_tok_per_byte=k, c0=c0, r2=r2, ok=(r2 >= 0.5 and k > 0 and c0 >= 0))
    return out


def ledger(row: dict, cal: dict) -> list[dict]:
    """Per-category rows for one session. tokens is None (UNKNOWN) when the calibration is not ok."""
    ctx = row['ctx']
    k = cal['k_tok_per_byte'] if cal['ok'] else None
    rows = []
    for c in CATEGORIES:
        b = row['bytes'].get(c, 0)
        if b == 0 and c in ('other_attach', 'file_attach'):
            continue
        tok = round(b * k) if k is not None else None
        rows.append(_row(c, b, tok, ctx, 'CALIBRATED' if k is not None else 'BYTES_ONLY'))
    if k is not None:
        resid = ctx - sum(r['tokens'] for r in rows)
        rows.append(_row(RESIDUAL, None, resid if resid >= 0 else None, ctx, 'RESIDUAL' if resid >= 0 else 'UNKNOWN_NEGATIVE'))
    else:
        rows.append(_row(RESIDUAL, None, None, ctx, 'UNKNOWN_UNCALIBRATED'))
    return rows


def _row(cat: str, b, tok, ctx: int, basis: str) -> dict:
    bucket = ANATOMY_BUCKET.get(cat)
    cls, ev = ccr_anatomy.classify(bucket) if bucket else ('UNKNOWN', 'no measurement for this category')
    return {'category': cat, 'bytes': b, 'tokens': tok, 'share': (tok / ctx if tok is not None and ctx else None),
            'basis': basis, 'cls': cls, 'age_axis': AGE_AXIS.get(cat, 'EPOCH'), 'class_evidence': ev}


def g1(rows: list[dict]) -> dict:
    """Gate G1: share of the floor in host-fixed classes (IRREDUCIBLE / HOST_LIMITED) against 70 %. UNKNOWN rows are not counted as fixed."""
    total = sum(r['tokens'] for r in rows if r['tokens'] is not None)
    fixed = sum(r['tokens'] for r in rows if r['tokens'] is not None and r['cls'] in HOST_FIXED_CLASSES)
    unknown = sum(r['tokens'] for r in rows if r['tokens'] is not None and r['cls'] == 'UNKNOWN')
    share = fixed / total if total else None
    return {'host_fixed_tokens': fixed, 'unknown_class_tokens': unknown, 'floor_tokens': total, 'host_fixed_share': share,
            'gate': G1_HOST_FIXED_SHARE, 'triggered': (share is not None and share > G1_HOST_FIXED_SHARE),
            'upper_bound_share': ((fixed + unknown) / total if total else None)}


def age_split(rows: list[dict]) -> dict:
    """Per category: median bytes in the earliest vs latest third of sessions by first timestamp. A PROJECT-axis category
    that drifts up is project-age rent; a flat one is not. p10..p90 inside the latest third is the epoch-to-epoch spread."""
    srt = sorted((r for r in rows if r['ts']), key=lambda r: r['ts'])
    if len(srt) < 6:
        return {}
    third = len(srt) // 3
    early, late = srt[:third], srt[-third:]
    out = {}
    for c in CATEGORIES:
        e = [r['bytes'].get(c, 0) for r in early]
        l = sorted(r['bytes'].get(c, 0) for r in late)
        out[c] = {'early_median_bytes': statistics.median(e), 'late_median_bytes': statistics.median(l),
                  'drift_bytes': statistics.median(l) - statistics.median(e),
                  'late_p10_bytes': l[len(l) // 10], 'late_p90_bytes': l[min(len(l) - 1, (len(l) * 9) // 10)],
                  'age_axis': AGE_AXIS.get(c, 'EPOCH')}
    return out


def build(dir_: Path, min_ctx: int) -> dict:
    allrows = [m for m in (measure_session(p) for p in sorted(dir_.glob('*.jsonl'))) if m]
    rows = [r for r in allrows if r['ctx'] >= min_ctx]
    cal = calibrate(allrows)
    res = {'dir': str(dir_), 'sessions_with_call': len(allrows), 'sessions_ge_min_ctx': len(rows), 'min_ctx': min_ctx,
           'calibration': cal, 'age_split': age_split(rows)}
    if rows:
        ctxs = sorted(r['ctx'] for r in rows)
        res['first_call_ctx'] = {'p50': statistics.median(ctxs), 'min': ctxs[0], 'max': ctxs[-1]}
        near = min(rows, key=lambda r: abs(r['ctx'] - 206186))
        res['nearest_206186'] = {'sid': near['sid'], 'ts': near['ts'], 'ctx': near['ctx'], 'rows': ledger(near, cal), 'g1': g1(ledger(near, cal))}
        med = {c: statistics.median(r['bytes'].get(c, 0) for r in rows) for c in CATEGORIES}
        medrow = {'sid': 'p50', 'ts': '', 'ctx': int(statistics.median(ctxs)), 'bytes': med}
        res['p50_ledger'] = {'ctx': medrow['ctx'], 'rows': ledger(medrow, cal), 'g1': g1(ledger(medrow, cal))}
    return res


def _print(res: dict) -> None:
    cal = res['calibration']
    print(f"sessions with a model call {res['sessions_with_call']}, >= {res['min_ctx']} ctx: {res['sessions_ge_min_ctx']}")
    print(f"calibration n={cal['n']} k={cal['k_tok_per_byte']} tok/byte c0={cal['c0']} R2={cal['r2']} ok={cal['ok']}")
    for key in ('nearest_206186', 'p50_ledger'):
        if key in res:
            blk = res[key]
            print(f"\n{key} ctx={blk['ctx']} g1={blk['g1']}")
            for r in blk['rows']:
                print(f"  {r['category']:<22} bytes={r['bytes']!s:>8} tok={r['tokens']!s:>8} share={r['share'] if r['share'] is None else round(r['share'], 3)!s:>6} {r['cls']:<12} {r['age_axis']:<8} {r['basis']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('table', 'json'):
        p = sub.add_parser(name)
        p.add_argument('--dir', required=True)
        p.add_argument('--min-ctx', type=int, default=150000)
        if name == 'json':
            p.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    res = build(Path(a.dir), a.min_ctx)
    if a.cmd == 'json':
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf-8')
    _print(res)
    return 0


if __name__ == '__main__':
    sys.exit(main())
