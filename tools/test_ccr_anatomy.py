"""V-CCRANAT-*: anatomy buckets, calibration, classification, CWS proposal (both poles each)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_anatomy as an  # noqa: E402
import ccr_cws_proposal as cws  # noqa: E402

passes = fails = 0


def check(gate: str, cond: bool, ev: str) -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def session(sid: str, *, attach: dict[str, tuple[int, int | None]], offered: int = 7, sections=(('lean_body', 3000),),
            prompt: int = 300, ctx1: int, later: list[tuple[int, int, int, int]] = ()) -> list[dict]:
    """Synthetic receipt. attach: type -> (bytes, out-if-applied). later: (ctx, tool_result_bytes, response_bytes, imageTok)."""
    ev = [{'ts': 1, 'sid': 'unknown', 'ev': 'link', 'surface': 'instruction-file', 'bytes': 10, 'keep': True},
          {'ts': 2, 'sid': sid, 'ev': 'start', 'version': '2.1.296', 'unit': None, 'interactive': False},
          {'ts': 3, 'sid': sid, 'ev': 'compose', 'traits': ['lean'], 'offered': offered,
           'sections': [{'id': i, 'scope': 'session', 'bytes': b} for i, b in sections]},
          {'ts': 4, 'sid': sid, 'ev': 'row', 'agent': None, 'door': 'prompt', 'text': prompt}]
    for t, (b, out) in attach.items():
        e = {'ts': 5, 'sid': sid, 'ev': 'attach', 'agent': None, 'type': t, 'bytes': b}
        if out is not None:
            e.update(out=out, applied=True)
        ev.append(e)
    ev.append({'ts': 6, 'sid': sid, 'ev': 'row', 'agent': None, 'door': 'response', 'text': 600, 'thinking': 0, 'sealed': 0})
    ev.append({'ts': 7, 'sid': sid, 'ev': 'call', 'agent': None, 'call': 1, 'ctx': ctx1, 'step': 0, 'imageTok': 0})
    ts, prev = 10, ctx1
    for k, (ctx, tr, rs, img) in enumerate(later, start=2):
        ev.append({'ts': ts, 'sid': sid, 'ev': 'row', 'agent': None, 'door': 'tool-result', 'text': tr})
        ev.append({'ts': ts + 1, 'sid': sid, 'ev': 'row', 'agent': None, 'door': 'response', 'text': rs, 'thinking': 0, 'sealed': 0})
        ev.append({'ts': ts + 2, 'sid': sid, 'ev': 'call', 'agent': None, 'call': k, 'ctx': ctx, 'step': ctx - prev, 'imageTok': img})
        prev, ts = ctx, ts + 10
    return ev


def main() -> int:
    # V-CCRANAT-01 calibration recovers a known rate; the unknown per-group tool cost cancels
    rate = 3.0
    facts = []
    for g, tool_tok in ((7, 15000), (86, 26000)):
        for i, extra in enumerate((0, 3000, 9000)):
            att = 6000 + extra
            ctx1 = round((3000 + att + 300) / rate) + tool_tok
            facts.append(an.session_facts(session(f's{g}{i}', attach={'hook_additional_context': (att, None)}, offered=g, ctx1=ctx1)))
    cal = an.calibrate(facts)
    check('V-CCRANAT-01', cal['bpt'] is not None and abs(cal['bpt'] - rate) < 0.01 and cal['n'] == 6,
          f"fitted {cal['bpt']} B/token from 2 groups with different tool costs")
    # V-CCRANAT-02 no within-group spread -> no rate, never an assumed one
    flat = [an.session_facts(session(f'f{i}', attach={'x': (5000, None)}, ctx1=9000 + i)) for i in range(2)]
    check('V-CCRANAT-02', an.calibrate(flat)['bpt'] is None, 'identical sized bytes give no slope: bpt None')

    # V-CCRANAT-03 applied drop/replace counts the SENT bytes; shadow counts bytes in
    f = an.session_facts(session('a', attach={'instructions': (78400, 4817), 'skill_listing': (15060, 0),
                                              'environment': (946, None)}, ctx1=20000))
    check('V-CCRANAT-03', f['attach1'] == {'instructions': 4817, 'skill_listing': 0, 'environment': 946},
          f"sent bytes {f['attach1']}")
    # V-CCRANAT-04 call-1 buckets plus the residual equal ctx exactly
    a1 = an.anatomy(f, 3.0, 2.5)
    s1 = sum(r['tokens'] for r in a1['buckets'] if not r['bucket'].startswith('carry:'))
    check('V-CCRANAT-04', abs(s1 - 20000) <= len(a1['buckets']), f'call-1 bucket sum {s1} vs ctx 20000 (rounding only)')

    # V-CCRANAT-05 carry: tool results + responses (k's output carried to k+1) + images + residual = ctx_last - ctx1
    ev = session('c', attach={'environment': (900, None)}, ctx1=10000, later=[(13000, 2500, 500, 0), (16000, 2500, 0, 1000)])
    fc = an.session_facts(ev)
    resp = [pc['add']['response'] for pc in fc['calls']]
    check('V-CCRANAT-05a', resp == [600, 500], f'response bytes carried into calls 2,3 = {resp} (call-1 output lands in call 2)')
    ac = an.anatomy(fc, 3.0, 2.5)
    carry = sum(r['tokens'] for r in ac['buckets'] if r['bucket'].startswith('carry:'))
    check('V-CCRANAT-05b', abs(carry - 6000) <= 5, f'carry buckets sum {carry} vs ctx delta 6000')
    imgs = next(r['tokens'] for r in ac['buckets'] if r['bucket'] == 'carry:images')
    check('V-CCRANAT-05c', imgs == 1000, 'image tokens taken from the runtime count, not bytes')

    # V-CCRANAT-06 classification: every class is from the closed set; measured drops ELIMINABLE; unknown UNKNOWN
    check('V-CCRANAT-06a', all(r['class'] in an.CLASSES for r in a1['buckets'] + ac['buckets']), 'closed class set')
    check('V-CCRANAT-06b', an.classify('attach:skill_listing')[0] == 'ELIMINABLE'
          and an.classify('attach:never_seen_type')[0] == 'UNKNOWN', 'skill_listing ELIMINABLE; unmeasured type UNKNOWN')
    check('V-CCRANAT-06c', an.classify('carry:tool_result', deterministic=True)[0] == 'EMBODIABLE'
          and an.classify('carry:tool_result')[0] == 'PAGEABLE', 'tool-result carry EMBODIABLE only when the answer is script-computable')
    check('V-CCRANAT-06d', an.classify('tool_schemas+framing', offered=0)[0] == 'UNKNOWN'
          and an.classify('tool_schemas+framing', offered=7)[0] == 'REDUCIBLE', 'residual with no tools is not called reducible')

    # V-CCRANAT-07 torn lines are skipped; the file name is the session id
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'rk' / 'abc-123.jsonl'
        p.parent.mkdir()
        import json
        p.write_text('\n'.join(json.dumps(e) for e in session('abc-123', attach={}, ctx1=5000)) + '\n{"torn":\n')
        got = an.load_all([Path(d)])
        check('V-CCRANAT-07', len(got) == 1 and got[0]['sid'] == 'abc-123', 'torn line skipped, sid from file name')

    # V-CCRANAT-08 CWS proposal: admissible; a proposal that drops the page index or puts Edit in front is not
    check('V-CCRANAT-08a', cws.check_safe() == [], 'proposal passes its safety invariants')
    bad = dict(cws.PROPOSAL, tools=('Read', 'Edit'), drop_attachments=cws.PROPOSAL['drop_attachments'] | {'deferred_tools_delta'})
    v = cws.check_safe(bad)
    check('V-CCRANAT-08b', len(v) == 3, f'unsafe variant rejected: {v}')
    check('V-CCRANAT-08c', cws.decide_tool('mcp__cpp-cognitive-runtime__page') == 'keep' and cws.decide_tool('Edit') == 'defer'
          and cws.decide_attachment('instructions') == 'replace' and cws.decide_attachment('deferred_tools_delta') == 'keep',
          'page tool kept, Edit deferred, instructions replaced, page index kept')
    fs = an.session_facts(session('s', attach={'hook_additional_context': (5568, None), 'remote_session_change': (544, None),
                                               'deferred_tools_delta': (4307, None)}, ctx1=18308))
    sim = cws.simulate(fs, 3.0)
    check('V-CCRANAT-08d', sim['removed_tokens'] == round(5568 / 3) + round(544 / 3) and sim['tool_schema_saving'] == 'UNKNOWN',
          f"projected removal {sim['removed_tokens']} tokens; tool schemas UNKNOWN")
    # V-CCRANAT-09 the proposal is not enforced: the runtime policy has no short-lookup class
    pol = (Path(__file__).resolve().parent.parent / 'mods/cpp-cognitive-runtime/hooks/policy.ts').read_text()
    check('V-CCRANAT-09', "'short-lookup'" not in pol, 'policy.ts carries no short-lookup class (proposal only)')

    print(f"\n{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == '__main__':
    raise SystemExit(main())
