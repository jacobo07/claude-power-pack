"""Read-only mining of dws transcripts: what the paid calls were spent on (tool mix, re-reads, sidechains)."""
import json, glob, os, sys, collections, re

root = os.path.expanduser('~/.claude/projects/C--Users-User-Apps-orca-dws-wt')
files = glob.glob(os.path.join(root, '**', '*.jsonl'), recursive=True)
seen = set()
calls = 0
ctx_by_kind = collections.Counter()
calls_by_kind = collections.Counter()
tool_names = collections.Counter()
read_paths = collections.Counter()
bash_heads = collections.Counter()
agent_types = collections.Counter()
no_tool_calls = 0
ctx_total = 0
ctx_list = []
for f in files:
    side = 'subagent' if os.sep + 'subagents' + os.sep in f or '/subagents/' in f else 'main'
    for line in open(f, encoding='utf-8', errors='replace'):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get('type') != 'assistant':
            continue
        m = o.get('message') or {}
        key = (m.get('id'), o.get('requestId'))
        u = m.get('usage') or {}
        ctx = (u.get('input_tokens') or 0) + (u.get('cache_read_input_tokens') or 0) + (u.get('cache_creation_input_tokens') or 0)
        tools = [b for b in (m.get('content') or []) if isinstance(b, dict) and b.get('type') == 'tool_use']
        for t in tools:
            n = t.get('name')
            tool_names[n] += 1
            inp = t.get('input') or {}
            if n == 'Read':
                p = (inp.get('file_path') or '').replace('\\', '/')
                read_paths[re.sub(r'^.*orca-dws-wt/', '', p)] += 1
            elif n in ('Bash', 'PowerShell'):
                c = (inp.get('command') or '').strip()
                c = re.sub(r"^\$\w+\s*=\s*'[^']*';?\s*", '', c)
                head = ' '.join(re.findall(r"[\w./:-]+", c)[:3])
                bash_heads[head[:60]] += 1
            elif n in ('Agent', 'Task'):
                agent_types[inp.get('subagent_type') or 'general'] += 1
        if key in seen:
            continue
        seen.add(key)
        calls += 1
        ctx_total += ctx
        ctx_list.append(ctx)
        kind = side
        calls_by_kind[kind] += 1
        ctx_by_kind[kind] += ctx
        if not tools:
            no_tool_calls += 1

ctx_list.sort()
out = {
    'files': len(files), 'calls': calls, 'ctx_total': ctx_total,
    'ctx_p50': ctx_list[len(ctx_list)//2] if ctx_list else None,
    'ctx_p90': ctx_list[int(len(ctx_list)*0.9)] if ctx_list else None,
    'calls_by_side': dict(calls_by_kind), 'ctx_by_side': dict(ctx_by_kind),
    'calls_without_tool_use': no_tool_calls,
    'tool_names': tool_names.most_common(25),
    'top_reads': read_paths.most_common(30),
    'distinct_read_paths': len(read_paths), 'total_reads': sum(read_paths.values()),
    'top_shell_heads': bash_heads.most_common(30),
    'agent_types': agent_types.most_common(),
}
with open(sys.argv[1], 'w', encoding='utf-8') as fh:
    json.dump(out, fh, indent=1)
