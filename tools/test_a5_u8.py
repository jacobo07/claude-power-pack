#!/usr/bin/env python3
"""test_a5_u8.py -- gsd_state_projection tests (ce-a5 U8). Hermetic. Prints A5_U8_PASS=n/m."""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gsd_state_projection as P

FIX = """---
current_phase: 2 - Offload
current_plan: 02-07
status: executing
stopped_at: plan 02-06 done
---

# Project State

## Current Position

**Status:** Executing
**Current Phase:** 2 - Offload

## Decisions

- [Stage Zero, Owner "y" 2026-09-25] D1 Broker law: bind lanes to GEX44.
  continued line.
- [2026-09-28, 02-04] D7 SC3 agent leg BLOCKED on login; SC4 INCONCLUSIVE.

## Weird Custom Section

Free text the parser does not model.

## Deferred Verification

| Phase | State | Resume |
|-------|-------|--------|
| 4 | blocked | UWCP verbs not built |
| 2 | verification_deferred_gaps | rerun e2e |

## Session Continuity

**Last session:** 2026-09-30 (s1)
**Stopped At:** x
Next, in order:
  1. do A
  2. do B
**Resume File:** None
"""
MATRIX = '// c\n{"rows":[{"id":1,"row":"R1","state":"PASS","required":true},{"id":2,"row":"R2","state":"ABSENT","required":true}]}'
RM = "- [x] **Phase 1: Base** - x\n- [ ] **Phase 2: Offload** - y\n"
res = []

def check(name, fn):
    try:
        ok = bool(fn())
    except Exception as e:
        ok = False; name += f' (exc {e!r})'
    res.append(ok); print(('PASS ' if ok else 'FAIL ') + name)

def parse():
    return P.parse_state(FIX, 'STATE.md', RM, P.strip_jsonc(MATRIX))

def invariants(proj, card):
    """returns list of violations"""
    v = []
    if not proj['blockers']: v.append('no blockers')
    if 'Weird Custom Section' not in card: v.append('unknown section dropped')
    if len(card.encode()) > P.CARD_MAX: v.append('too big')
    if 'blocked' not in card.lower() and 'BLOCKED' not in card: v.append('blocker not in card')
    return v

def synth(n=1100):
    L = FIX.split('\n')
    i = L.index('## Weird Custom Section')
    pad = [f'- [2026-09-{1 + k % 28:02d}, P{k}] D{k + 10} note {k} ' + 'lorem ipsum ' * 6 for k in range(n - len(L))]
    return '\n'.join(L[:i - 1] + pad + [''] + L[i - 1:])

proj = parse(); card = P.render_card(proj)
check('parse: phase/plan/status', lambda: proj['current']['phase'].startswith('2') and proj['current']['plan'] == '02-07')
check('parse: decisions id/date/continuation', lambda: [d['id'] for d in proj['decisions']] == ['D1', 'D7'] and proj['decisions'][0]['date'] == '2025-09-25'.replace('2025', '2026') and 'continued line' in proj['decisions'][0]['text'])
check('parse: blockers from deferred row and decision', lambda: any(b.get('phase') == '4' for b in proj['blockers']) and any(b.get('decision') == 'D7' for b in proj['blockers']))
check('parse: open unknown found', lambda: any(u['kw'] == 'INCONCLUSIVE' for u in proj['open_unknowns']))
check('parse: proof state open row', lambda: proj['proof_state']['open_required'][0]['id'] == 2 and proj['proof_state']['rows'] == 2)
check('parse: frontier next', lambda: len(proj['frontier']['next']) == 2)
check('roundtrip: json dumps/loads equal', lambda: json.loads(json.dumps(proj)) == proj)
check('roundtrip: card carries frontier + blocker + pointer', lambda: 'plan: 02-07' in card and 'UWCP verbs' in card and 'STATE.md#L' in card)
check('roundtrip: deterministic render', lambda: P.render_card(parse()) == card)
check('unknown section kept as pointer', lambda: 'Weird Custom Section' in card and any(s['heading'] == 'Weird Custom Section' for s in proj['sections_unmodeled']))
big = synth(); bp = P.parse_state(big, 'STATE.md', RM, P.strip_jsonc(MATRIX)); bc = P.render_card(bp)
check('synthetic 1100-line STATE: lines', lambda: len(big.splitlines()) >= 1100)
check('synthetic 1100-line STATE: card <= 8 KB', lambda: len(bc.encode()) <= 8192)
check('synthetic: unknown section pointer survives', lambda: 'Weird Custom Section' in bc)
check('control: invariants admit the good card', lambda: invariants(proj, card) == [])
mut = dict(proj); mut['blockers'] = []
check('mutant: drop blockers -> invariants red', lambda: invariants(mut, P.render_card(mut)) != [])
check('mutant: drop unmodeled sections -> invariants red', lambda: (lambda m: invariants(proj, P.render_card(m)) != [])(dict(proj, sections_unmodeled=[])) )
def git_changed():
    with tempfile.TemporaryDirectory() as d:
        g = lambda *a: subprocess.run(['git', '-C', d, '-c', 'user.name=t', '-c', 'user.email=t@t'] + list(a), capture_output=True, text=True, check=True)
        g('init', '-q'); open(os.path.join(d, 'STATE.md'), 'w').write(FIX); g('add', '.'); g('commit', '-qm', 'a')
        new = FIX.replace('## Weird', '- [2026-10-01] D9 added later\n\n## Weird')
        open(os.path.join(d, 'STATE.md'), 'w').write(new); g('commit', '-qam', 'b')
        pr = P.parse_state(new, 'STATE.md')
        c = P.changed_since(pr, d, 'HEAD~1', 'STATE.md')
        c0 = P.changed_since(pr, d, 'HEAD', 'STATE.md')
        return [x['id'] for x in c['new_decisions']] == ['D9'] and c0['new_decisions'] == []
check('changed-since: new decision shown; control: same rev shows none', git_changed)
print(f'A5_U8_PASS={sum(res)}/{len(res)}')
sys.exit(0 if all(res) else 1)
