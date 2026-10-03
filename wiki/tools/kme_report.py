"""Aggregate kme_token_audit JSON outputs into a KME token report (JSON + console)."""
import collections, json, re, sys

# $/MTok: input, output, cache_read. Cache write = 1.25x input (5m), 2x input (1h).
PRICES = [
    (r'fable|mythos', 10.0, 50.0, 0.25),
    (r'opus-5-5', 4.0, 20.0, 0.20),
    (r'opus', 5.0, 25.0, 0.50),
    (r'sonnet-5', 2.0, 10.0, 0.20),
    (r'sonnet', 3.0, 15.0, 0.30),
    (r'haiku', 1.0, 5.0, 0.10),
]


def price(model):
    for pat, i, o, r in PRICES:
        if re.search(pat, model or ''):
            return i, o, r
    return 5.0, 25.0, 0.50


def cost(model, c):
    i, o, r = price(model)
    cw5 = c.get('cw5m', 0)
    cw1 = c.get('cw1h', 0)
    other_cw = max(0, c.get('cw', 0) - cw5 - cw1)  # unsplit writes priced as 5m
    return dict(
        inp=c.get('inp', 0) * i / 1e6,
        cw=((cw5 + other_cw) * i * 1.25 + cw1 * i * 2.0) / 1e6,
        cr=c.get('cr', 0) * r / 1e6,
        out=c.get('out', 0) * o / 1e6,
    )


def is_kme(s):
    if s['class'] in ('KME_PATH', 'KME_STRONG'):
        return True
    # GEX44: the a5/a7 envs are KobiiCraft clones dedicated to KME arena missions
    return s['host'] == 'gex44' and re.search(r'kobii-a[0-9]', s['project'] or '') is not None


def main(paths, out):
    sess = []
    for p in paths:
        sess += json.load(open(p, encoding='utf-8'))
    # Whole-estate view: every scanned session, cost attributed to KME by tool-call share.
    print('=== atribucion proporcional (todas las sesiones escaneadas)')
    for host in sorted({s['host'] for s in sess}):
        hs = [s for s in sess if s['host'] == host]
        tot = prop = 0.0
        firsts = []
        for s in hs:
            c = sum(sum(cost(m, cc).values()) for m, cc in s['by_model'].items())
            share = 1.0 if is_kme(s) and s['class'] == 'KME_PATH' or (host == 'gex44' and is_kme(s)) else s.get('kme_share', 0)
            tot += c
            prop += c * share
            if s.get('first_ctx'):
                firsts.append(s['first_ctx'])
        firsts.sort()
        med = firsts[len(firsts) // 2] if firsts else 0
        print(f"{host}: sesiones={len(hs)} coste_total=${tot:,.2f} coste_atribuible_KME=${prop:,.2f} "
              f"first_ctx mediana={med:,} p10={firsts[len(firsts)//10] if firsts else 0:,} p90={firsts[len(firsts)*9//10] if firsts else 0:,} n={len(firsts)}")
    kme = [s for s in sess if is_kme(s)]
    weak = [s for s in sess if s['class'] == 'KME_WEAK' and not is_kme(s)]
    R = dict(hosts={}, top_sessions=[], weak=[])
    for host in sorted({s['host'] for s in kme}):
        hs = [s for s in kme if s['host'] == host]
        H = dict(sessions=len(hs), active_sessions=0, by_model={}, tokens=collections.Counter(),
                 cost=collections.Counter(), main=collections.Counter(), sub=collections.Counter(),
                 cost_main=0.0, cost_sub=0.0, tool_calls=collections.Counter(),
                 tool_result_chars=collections.Counter(), tool_input_chars=collections.Counter(),
                 attach=collections.Counter(), attach_n=collections.Counter(),
                 agent_models=collections.Counter(), by_day=collections.defaultdict(collections.Counter),
                 cost_by_day=collections.Counter(), reads=collections.Counter(), residency=[],
                 compactions=0, calls_over_150k=0, max_ctx=0, thinking_chars=0, text_chars=0,
                 user_prompts=0, projects=collections.Counter(), dead_sessions=0)
        for s in hs:
            calls = s['main'].get('calls', 0) + s['sub'].get('calls', 0)
            if calls == 0:
                H['dead_sessions'] += 1
                continue
            H['active_sessions'] += 1
            sc = 0.0
            for m, c in s['by_model'].items():
                bm = H['by_model'].setdefault(m, collections.Counter())
                bm.update(c)
                cc = cost(m, c)
                for k, v in cc.items():
                    H['cost'][k] += v
                sc += sum(cc.values())
            for k in ('inp', 'cw', 'cw1h', 'cw5m', 'cr', 'out', 'calls'):
                H['tokens'][k] += s['main'].get(k, 0) + s['sub'].get(k, 0)
            H['main'].update(s['main'])
            H['sub'].update(s['sub'])
            # main/sub cost split, priced at the session's dominant model
            dom = max(s['by_model'].items(), key=lambda x: x[1].get('cr', 0) + x[1].get('out', 0))[0]
            cm, cs = sum(cost(dom, s['main']).values()), sum(cost(dom, s['sub']).values())
            tot = (cm + cs) or 1
            H['cost_main'] += sc * cm / tot
            H['cost_sub'] += sc * cs / tot
            H['tool_calls'].update(s['tool_calls'])
            H['tool_result_chars'].update(s['tool_result_chars'])
            H['tool_input_chars'].update(s['tool_input_chars'])
            H['agent_models'].update(s['agent_models'])
            for k, (n, ch) in s['attach'].items():
                H['attach'][k] += ch
                H['attach_n'][k] += n
            for d, c in s['by_day'].items():
                H['by_day'][d].update(c)
            first_model = dom
            for d, c in s['by_day'].items():
                H['cost_by_day'][d] += sum(cost(first_model, c).values())
            H['reads'].update(s['reads'])
            H['residency'] += [r + [s['session'][:8]] for r in s['residency']]
            H['compactions'] += s['compactions']
            H['calls_over_150k'] += s['calls_over_150k']
            H['max_ctx'] = max(H['max_ctx'], s['max_ctx'])
            H['thinking_chars'] += s['thinking_chars']
            H['text_chars'] += s['assistant_text_chars']
            H['user_prompts'] += s['user_prompts']
            H['projects'][s['project']] += sc
            R['top_sessions'].append(dict(
                host=host, project=s['project'][-60:], session=s['session'], first=s['first'], last=s['last'],
                cost=round(sc, 2), calls=calls, main_calls=s['main'].get('calls', 0), sub_calls=s['sub'].get('calls', 0),
                subagent_files=s['subagent_files'], cr=s['main'].get('cr', 0) + s['sub'].get('cr', 0),
                cw=s['main'].get('cw', 0) + s['sub'].get('cw', 0), out=s['main'].get('out', 0) + s['sub'].get('out', 0),
                max_ctx=s['max_ctx'], compactions=s['compactions'], over150k=s['calls_over_150k'],
                models=sorted(s['by_model']), prompt=(s['first_prompt'] or '')[:120]))
        H['residency'] = sorted(H['residency'], key=lambda x: -x[4])[:40]
        H['reads'] = H['reads'].most_common(30)
        H['cost_total'] = round(sum(H['cost'].values()), 2)
        H['by_day'] = {d: dict(c) for d, c in sorted(H['by_day'].items())}
        R['hosts'][host] = H
    R['top_sessions'].sort(key=lambda x: -x['cost'])
    R['top_sessions'] = R['top_sessions'][:40]
    R['weak'] = [dict(host=s['host'], project=s['project'][-60:], session=s['session'][:8], hits=s['kme_hits'],
                      calls=s['main'].get('calls', 0) + s['sub'].get('calls', 0),
                      cost=round(sum(sum(cost(m, c).values()) for m, c in s['by_model'].items()), 2))
                 for s in sorted(weak, key=lambda s: -s['kme_hits'])][:30]
    json.dump(R, open(out, 'w', encoding='utf-8'), default=lambda x: dict(x) if isinstance(x, collections.Counter) else str(x), indent=1)
    for host, H in R['hosts'].items():
        t = H['tokens']
        print(f"\n=== {host}: {H['sessions']} sesiones ({H['active_sessions']} activas, {H['dead_sessions']} sin llamadas)  coste API-eq ${H['cost_total']:,.2f}")
        print(f"calls={t['calls']:,} inp={t['inp']:,} cw={t['cw']:,} (1h {t['cw1h']:,} / 5m {t['cw5m']:,}) cr={t['cr']:,} out={t['out']:,}")
        print('coste por tipo:', {k: round(v, 2) for k, v in H['cost'].items()})
        print(f"main ${H['cost_main']:,.2f}  sub ${H['cost_sub']:,.2f}  agent models {dict(H['agent_models'])}")
        print('modelos:', {m: dict(calls=c['calls'], cr=c['cr'], out=c['out']) for m, c in H['by_model'].items()})
        print(f"compactions={H['compactions']} calls>150k={H['calls_over_150k']} max_ctx={H['max_ctx']:,} thinking_chars={H['thinking_chars']:,} text_chars={H['text_chars']:,}")
        print('tool calls:', H['tool_calls'].most_common(12))
        print('tool result chars:', H['tool_result_chars'].most_common(10))
        print('attach chars:', H['attach'].most_common(12))
        print('dias:', {d: round(v, 1) for d, v in sorted(H['cost_by_day'].items())})
        print('proyectos:', [(p[-50:], round(v, 1)) for p, v in H['projects'].most_common(12)])
        print('top residency (char*turns):', [(r[0][:90], r[2], r[3]) for r in H['residency'][:12]])
        print('reads repetidos:', H['reads'][:12])
    print('\n=== top sesiones')
    for s in R['top_sessions'][:20]:
        print(f"{s['host']:5} ${s['cost']:8.2f} {s['session'][:8]} {str(s['first'])[:16]} calls={s['calls']} (sub {s['sub_calls']}) maxctx={s['max_ctx']:,} >150k={s['over150k']} comp={s['compactions']} {s['models']} {s['project'][-35:]} | {s['prompt'][:70]!r}")
    print('\n=== KME_WEAK (no contadas):', R['weak'][:10])


if __name__ == '__main__':
    main(sys.argv[2:], sys.argv[1])
