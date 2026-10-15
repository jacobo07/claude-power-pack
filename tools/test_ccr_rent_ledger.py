#!/usr/bin/env python3
"""V-RENT-* gates for tools/ccr_rent_ledger.py. Synthetic transcripts only; each detector is driven from both poles."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_rent_ledger as L  # noqa: E402

passes = fails = 0


def _ok(name: str, ev: str) -> None:
    global passes
    passes += 1
    print(f'PASS {name} {ev}')


def _fail(name: str, diag: str) -> None:
    global fails
    fails += 1
    print(f'FAIL {name} {diag}')


def check(name: str, cond: bool, ev: str) -> None:
    (_ok if cond else _fail)(name, ev)


def write_session(d: Path, sid: str, ts: str, rules_b: int, prompt_b: int, k: float, c0: int, *, with_usage=True) -> None:
    files = [{'path': 'C:\\u\\.claude\\CLAUDE.md', 'type': 'User', 'content': 'c' * 1000},
             {'path': 'C:\\u\\.claude\\rules\\x.md', 'type': 'User', 'content': 'r' * rules_b},
             {'path': 'C:\\u\\mem\\MEMORY.md', 'type': 'AutoMem', 'content': 'm' * 500}]
    recs = [{'type': 'attachment', 'timestamp': ts, 'attachment': {'type': 'instructions', 'files': files}},
            {'type': 'attachment', 'attachment': {'type': 'hook_success', 'stdout': 'z' * 9999}},
            {'type': 'attachment', 'attachment': {'type': 'hook_additional_context', 'content': ['h' * 300]}},
            {'type': 'user', 'message': {'role': 'user', 'content': 'p' * prompt_b}}]
    total = 1000 + rules_b + 500 + prompt_b + len(json.dumps({'type': 'hook_additional_context', 'content': ['h' * 300]}))
    ctx = int(c0 + k * total)
    if with_usage:
        recs.append({'type': 'assistant', 'message': {'model': 'claude-x', 'usage': {'input_tokens': 5, 'cache_read_input_tokens': ctx - 5, 'cache_creation_input_tokens': 0}}})
    (d / f'{sid}.jsonl').write_text('\n'.join(json.dumps(r) for r in recs) + '\n', encoding='utf-8')


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        # planted model: 0.25 tok/byte, 30000 intercept; rules grow with time (project age), prompt varies (epoch)
        for i in range(30):
            write_session(d, f's{i:02d}', f'2026-09-{i + 1:02d}T00:00:00Z', 2000 + 3000 * i, 500 + (i * 7919) % 4000, 0.25, 30000)
        write_session(d, 'nocall', '2026-09-01T00:00:00Z', 10, 10, 0.25, 30000, with_usage=False)
        rows = [m for m in (L.measure_session(p) for p in sorted(d.glob('*.jsonl'))) if m]
        check('V-RENT-01 measure', len(rows) == 30 and rows[0]['bytes']['rules'] == 2000 and rows[0]['bytes']['memory'] == 500
              and rows[0]['bytes']['constitution'] == 1000, f"n={len(rows)} bytes={rows[0]['bytes']}")
        check('V-RENT-02 not-counted', 'hook_success' not in rows[0]['bytes'] and rows[0]['bytes']['hook_injections'] < 2000,
              f"hook_injections={rows[0]['bytes']['hook_injections']} (hook_success stdout 9999 B excluded)")
        cal = L.calibrate(rows)
        check('V-RENT-03 calibration recovers planted slope', cal['ok'] and abs(cal['k_tok_per_byte'] - 0.25) < 0.01 and abs(cal['c0'] - 30000) < 1500,
              f"k={cal['k_tok_per_byte']} c0={cal['c0']} r2={cal['r2']}")
        led = L.ledger(rows[10], cal)
        by = {r['category']: r for r in led}
        check('V-RENT-04 rows sum to ctx', sum(r['tokens'] for r in led if r['tokens'] is not None) == rows[10]['ctx'] and by[L.RESIDUAL]['basis'] == 'RESIDUAL',
              f"sum={sum(r['tokens'] for r in led)} ctx={rows[10]['ctx']}")
        check('V-RENT-05 class from anatomy', by['prompt']['cls'] == 'IRREDUCIBLE' and by['skills']['cls'] in ('ELIMINABLE', 'UNKNOWN') and by['rules']['cls'] == 'REDUCIBLE',
              f"prompt={by['prompt']['cls']} rules={by['rules']['cls']}")
        # poor fit refuses a token split (control for 03: the same rows with ctx shuffled)
        shuf = [dict(r, ctx=rows[(i * 7 + 3) % len(rows)]['ctx']) for i, r in enumerate(rows)]
        bad = L.calibrate(shuf)
        badled = L.ledger(rows[0], bad)
        check('V-RENT-06 poor fit claims no tokens', (not bad['ok']) and all(r['tokens'] is None for r in badled),
              f"ok={bad['ok']} r2={bad['r2']} tokens={[r['tokens'] for r in badled][:3]}")
        # negative residual is UNKNOWN, never clipped to 0
        neg = L.ledger(dict(rows[0], ctx=1000), cal)
        res = {r['category']: r for r in neg}[L.RESIDUAL]
        check('V-RENT-07 negative residual is UNKNOWN', res['tokens'] is None and res['basis'] == 'UNKNOWN_NEGATIVE', f"tokens={res['tokens']} basis={res['basis']}")
        # G1: fixed vs not
        fixed_rows = [{'tokens': 800, 'cls': 'IRREDUCIBLE'}, {'tokens': 100, 'cls': 'REDUCIBLE'}, {'tokens': 100, 'cls': 'UNKNOWN'}]
        free_rows = [{'tokens': 100, 'cls': 'IRREDUCIBLE'}, {'tokens': 900, 'cls': 'REDUCIBLE'}]
        check('V-RENT-08 G1 both poles', L.g1(fixed_rows)['triggered'] and not L.g1(free_rows)['triggered'] and L.g1(fixed_rows)['unknown_class_tokens'] == 100,
              f"fixed={L.g1(fixed_rows)['host_fixed_share']} free={L.g1(free_rows)['host_fixed_share']}")
        sp = L.age_split(rows)
        check('V-RENT-09 age split separates drift', sp['rules']['drift_bytes'] > 20000 and abs(sp['constitution']['drift_bytes']) == 0,
              f"rules drift={sp['rules']['drift_bytes']} constitution drift={sp['constitution']['drift_bytes']}")
        check('V-RENT-10 table on directory', L.build(d, 0)['sessions_with_call'] == 30, 'build() ignores the session with no model call')
    print(f'RENT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}')
    return 0 if fails == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
