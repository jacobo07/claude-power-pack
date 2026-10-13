#!/usr/bin/env python3
"""ccr_anatomy.py -- per-session, per-call decomposition of model context from CCR receipts (0 model calls).

Plan: vault/plans/ccr-v4-stage3-2026-10-13.md, unit A2.

Inputs are content-free CCR receipts (<root>/<repoKey>/<sid>.jsonl): `compose` (system-prompt sections and
their bytes, `offered` = tools offered), `attach` (attachment type, bytes in, `out` when the runtime applied
a drop/replace), `row` (per-message byte facts by door: prompt, tool-result, response), `link` (tools
deferred by the unit closure) and `call` (provider ctx per call = input + cache_read + cache_creation).

Buckets at call 1: one per system section, one per attachment type as SENT, the prompt, and the residual
`tool_schemas+framing` (ctx minus every sized bucket; the receipts carry no tool-schema bytes for tools
kept in front, so that residual is never split without a probe). Buckets at call k > 1 add carry: the
tool-result bytes, the assistant's own turns, attachments that arrived after call 1, image tokens (the
runtime's own count) and a residual UNKNOWN.

Bytes-per-token is CALIBRATED, never assumed: `calibrate` pools within-group slopes of ctx(call 1) on
sized bytes across sessions that share a tool configuration (same offered count, traits and section
bytes), so the unknown tool schemas cancel; `calibrate_carry` fits call-to-call steps on the bytes added.

CLI:
  table [--root DIR ...] [--sid PREFIX ...] [--json PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_ROOTS = [
    Path('/home/kobii/missions/ccr-s3-data/pack/receipts'),
    Path(__file__).resolve().parent.parent / 'mods/cpp-cognitive-runtime/.state-dev/receipts',
]
CLASSES = ('IRREDUCIBLE', 'REDUCIBLE', 'EMBODIABLE', 'PAGEABLE', 'ELIMINABLE', 'HOST_LIMITED', 'UNKNOWN')

# bucket -> (class, evidence). Evidence names the measurement; "candidate" means no parity run yet.
CLASSIFICATION: dict[str, tuple[str, str]] = {
    'attach:instructions': ('REDUCIBLE', 'unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5'),
    'attach:agent_listing_delta': ('ELIMINABLE', 'dropped by unit closure in V1 r2/r4, parity 5/5'),
    'attach:skill_listing': ('ELIMINABLE', 'dropped by unit closure in V1 r2/r4, parity 5/5'),
    'attach:mcp_instructions_delta': ('ELIMINABLE', 'dropped by unit closure in V1 r2/r4, parity 5/5'),
    'attach:deferred_tools_delta': ('PAGEABLE', 'names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config)'),
    'attach:hook_additional_context': ('REDUCIBLE', 'hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run'),
    'attach:remote_session_change': ('ELIMINABLE', 'absent in probe P3; no role in a -p task; candidate, no parity run'),
    'attach:total_tokens_reminder': ('ELIMINABLE', '49 B per call, kept in every probe; candidate, no parity run'),
    'attach:environment': ('IRREDUCIBLE', 'cwd/platform; kept in probe P4 (every switch off)'),
    'attach:model': ('IRREDUCIBLE', 'model identity; kept in probe P4'),
    'attach:date': ('IRREDUCIBLE', 'date; kept in probe P4'),
    'attach:session_context': ('IRREDUCIBLE', 'kept in probe P4'),
    'section:memory': ('ELIMINABLE', 'dropped by unit closure in V1 r2/r4, parity 5/5'),
    'section:heron_brook': ('REDUCIBLE', 'session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate'),
    'prompt': ('IRREDUCIBLE', 'the task itself'),
    'tool_schemas+framing': ('REDUCIBLE', 'probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands'),
    'carry:tool_result': ('PAGEABLE', 'tool-output projection and paging exist (project events)'),
    'carry:response': ('HOST_LIMITED', 'host replays the assistant\'s own prior turns; no flag removes them'),
    'carry:images': ('PAGEABLE', 'pixel GC tombstones images outside the window'),
    'carry:residual': ('UNKNOWN', 'carry not explained by sized buckets'),
}
LEAN_CORE_SECTIONS = {'lean_body', 'communication', 'pronouns', 'action_caution', 'session_guidance',
                      'env_info_simple', 'context_management', 'act_dont_rederive', 'total_tokens'}


def classify(bucket: str, *, offered: int | None = None, deterministic: bool = False) -> tuple[str, str]:
    """Class and evidence for one bucket. `deterministic`: the task's answer is script-computable."""
    if bucket == 'carry:tool_result' and deterministic:
        return 'EMBODIABLE', 'answer is script-computable (V1 truth.py): DETERMINISTIC_PATH embodies the reads'
    if bucket == 'tool_schemas+framing' and offered == 0:
        return 'UNKNOWN', 'no tools offered: residual is host framing plus calibration error, unsplit'
    if bucket in CLASSIFICATION:
        return CLASSIFICATION[bucket]
    if bucket.startswith('section:') and bucket[8:] in LEAN_CORE_SECTIONS:
        return 'IRREDUCIBLE', 'CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor'
    if bucket.startswith('carry:attach:'):
        return classify('attach:' + bucket[13:], offered=offered)
    return 'UNKNOWN', 'no measurement for this bucket'


def load_events(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # torn line (concurrent writer): skipped, counted nowhere
    return out


def sent_bytes(e: dict) -> int:
    return int(e['out']) if e.get('applied') and e.get('out') is not None else int(e.get('bytes') or 0)


def session_facts(events: list[dict]) -> dict | None:
    """Main-thread facts of one session; None if it has no compose or no call 1."""
    main = [e for e in events if e.get('agent') is None]
    comp = next((e for e in main if e.get('ev') == 'compose'), None)
    calls = sorted((e for e in main if e.get('ev') == 'call'), key=lambda e: e['call'])
    if comp is None or not calls or calls[0]['call'] != 1:
        return None
    start = next((e for e in main if e.get('ev') == 'start'), {})
    t1 = calls[0]['ts']
    sections = {s['id']: int(s['bytes']) for s in comp.get('sections', [])}
    att1: dict[str, int] = defaultdict(int)
    for e in main:
        if e.get('ev') == 'attach' and e['ts'] <= t1:
            att1[e['type']] += sent_bytes(e)
    prompt = sum(int(e.get('text') or 0) for e in main if e.get('ev') == 'row' and e.get('door') == 'prompt' and e['ts'] <= t1)
    deferred = sum(int(e['bytes']) for e in main if e.get('ev') == 'link' and e.get('surface') == 'tool'
                   and not e.get('keep') and e.get('applied') and e['ts'] <= t1)
    per_call = []
    prev_ts = t1
    for c in calls[1:]:
        win = [e for e in main if prev_ts < e['ts'] <= c['ts']]
        add = {'tool_result': sum(int(e.get('text') or 0) for e in win if e.get('ev') == 'row' and e.get('door') == 'tool-result'),
               'response': 0, 'attach': defaultdict(int)}
        prev_ts = c['ts']
        per_call.append({'call': c['call'], 'ctx': c['ctx'], 'step': c.get('step', 0), 'imageTok': c.get('imageTok', 0), 'add': add})
        for e in win:
            if e.get('ev') == 'attach':
                add['attach'][e['type']] += sent_bytes(e)
    # call k's receipt is written after its response rows, so a row at or before call k's ts is call k's
    # output and is carried into call k + 1
    resp_by_call: dict[int, int] = defaultdict(int)
    for e in main:
        if e.get('ev') == 'row' and e.get('door') == 'response':
            k = next((c['call'] for c in calls if c['ts'] >= e['ts']), calls[-1]['call'] + 1)
            resp_by_call[k + 1] += int(e.get('text') or 0) + int(e.get('thinking') or 0) + int(e.get('sealed') or 0)
    for pc in per_call:
        pc['add']['response'] = resp_by_call.get(pc['call'], 0)
    return {'sid': events[0].get('sid', ''), 'version': start.get('version'), 'unit': start.get('unit'),
            'interactive': start.get('interactive'), 'offered': comp.get('offered'), 'traits': comp.get('traits', []),
            'sections': sections, 'attach1': dict(att1), 'prompt': prompt, 'deferred_tool_bytes': deferred,
            'ctx1': calls[0]['ctx'], 'calls': per_call, 'n_calls': len(calls)}


def sized_bytes1(f: dict) -> int:
    return sum(f['sections'].values()) + sum(f['attach1'].values()) + f['prompt']


def calibrate(facts: list[dict]) -> dict:
    """Pooled within-group slope of ctx1 on sized bytes; groups share the tool configuration."""
    groups: dict[tuple, list[tuple[int, int]]] = defaultdict(list)
    for f in facts:
        key = (f['offered'], tuple(f['traits']), sum(f['sections'].values()), f['deferred_tool_bytes'])
        groups[key].append((sized_bytes1(f), f['ctx1']))
    sxy = sxx = 0.0
    used = []
    for key, pts in groups.items():
        if len({x for x, _ in pts}) < 2:
            continue
        mx = sum(x for x, _ in pts) / len(pts)
        my = sum(y for _, y in pts) / len(pts)
        sxy += sum((x - mx) * (y - my) for x, y in pts)
        sxx += sum((x - mx) ** 2 for x, _ in pts)
        used.append({'offered': key[0], 'n': len(pts)})
    if sxx == 0 or sxy <= 0:
        return {'bpt': None, 'groups': used, 'n': sum(g['n'] for g in used)}
    return {'bpt': round(sxx / sxy, 3), 'groups': used, 'n': sum(g['n'] for g in used)}


def calibrate_carry(facts: list[dict]) -> dict:
    """Through-origin fit of step tokens on bytes added between calls (no images, positive steps)."""
    sxy = sxx = 0.0
    n = 0
    for f in facts:
        last_img = 0
        for pc in f['calls']:
            b = pc['add']['tool_result'] + pc['add']['response'] + sum(pc['add']['attach'].values())
            if pc['imageTok'] != last_img or pc['step'] <= 0 or b <= 0:
                last_img = pc['imageTok']
                continue
            sxy += b * pc['step']
            sxx += b * b
            n += 1
    return {'bpt': round(sxx / sxy, 3) if sxy > 0 else None, 'n': n}


def anatomy(f: dict, bpt1: float, bpt_carry: float, *, deterministic: bool = False) -> dict:
    """Buckets in tokens for call 1 and the last call, each with class and evidence."""
    b1: dict[str, float] = {}
    for k, v in f['sections'].items():
        b1['section:' + k] = v / bpt1
    for k, v in f['attach1'].items():
        b1['attach:' + k] = v / bpt1
    b1['prompt'] = f['prompt'] / bpt1
    b1['tool_schemas+framing'] = f['ctx1'] - sum(b1.values())
    last = f['calls'][-1] if f['calls'] else None
    carry: dict[str, float] = {}
    if last:
        tr = sum(pc['add']['tool_result'] for pc in f['calls'])
        rs = sum(pc['add']['response'] for pc in f['calls'])
        at: dict[str, int] = defaultdict(int)
        for pc in f['calls']:
            for k, v in pc['add']['attach'].items():
                at[k] += v
        carry['carry:tool_result'] = tr / bpt_carry
        carry['carry:response'] = rs / bpt_carry
        for k, v in at.items():
            carry['carry:attach:' + k] = v / bpt_carry
        carry['carry:images'] = float(last['imageTok'])
        carry['carry:residual'] = (last['ctx'] - f['ctx1']) - sum(carry.values())
    rows = []
    for k, v in list(b1.items()) + list(carry.items()):
        cls, ev = classify(k, offered=f['offered'], deterministic=deterministic)
        rows.append({'bucket': k, 'tokens': round(v), 'class': cls, 'evidence': ev})
    by_class: dict[str, int] = defaultdict(int)
    for r in rows:
        if not r['bucket'].startswith('carry:'):
            by_class[r['class']] += r['tokens']
    return {'sid': f['sid'], 'ctx1': f['ctx1'], 'ctx_last': last['ctx'] if last else f['ctx1'],
            'n_calls': f['n_calls'], 'offered': f['offered'], 'unit': f['unit'], 'buckets': rows,
            'call1_by_class': dict(by_class)}


def load_all(roots: list[Path]) -> list[dict]:
    facts = []
    for root in roots:
        for p in sorted(root.glob('*/*.jsonl')):
            f = session_facts(load_events(p))
            if f:
                f['sid'] = p.stem  # early events can carry sid 'unknown'; the file name is the session
                facts.append(f)
    return facts


def markdown(an: dict) -> str:
    lines = [f"### {an['sid'][:8]} (calls {an['n_calls']}, offered tools {an['offered']}, unit {an['unit']}; "
             f"ctx call 1 {an['ctx1']:,}, last call {an['ctx_last']:,})", '',
             '| bucket | tokens | class | evidence |', '|---|---:|---|---|']
    for r in an['buckets']:
        if abs(r['tokens']) >= 1:
            lines.append(f"| {r['bucket']} | {r['tokens']:,} | {r['class']} | {r['evidence']} |")
    return '\n'.join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n', 1)[0])
    ap.add_argument('cmd', choices=['table'])
    ap.add_argument('--root', action='append', type=Path)
    ap.add_argument('--sid', action='append', default=[])
    ap.add_argument('--deterministic', action='append', default=[], help='sid prefix whose answer is script-computable')
    ap.add_argument('--json', type=Path)
    a = ap.parse_args(argv)
    facts = load_all(a.root or DEFAULT_ROOTS)
    cal1, calc = calibrate(facts), calibrate_carry(facts)
    print(f"calibration call-1: {cal1['bpt']} B/token over {cal1['n']} sessions in {len(cal1['groups'])} groups; "
          f"carry: {calc['bpt']} B/token over {calc['n']} steps")
    if not cal1['bpt'] or not calc['bpt']:
        print('no calibration possible: refusing to decompose with an assumed rate', file=sys.stderr)
        return 2
    sel = [f for f in facts if not a.sid or any(f['sid'].startswith(s) for s in a.sid)]
    out = [anatomy(f, cal1['bpt'], calc['bpt'], deterministic=any(f['sid'].startswith(s) for s in a.deterministic)) for f in sel]
    for an in out:
        print(markdown(an) + '\n')
    if a.json:
        a.json.write_text(json.dumps({'calibration': {'call1': cal1, 'carry': calc}, 'sessions': out}, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
