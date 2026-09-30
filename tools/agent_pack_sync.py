"""Install and drift-check project-scoped agent packs.

Claude Code loads agents from ~/.claude/agents (every session, every project) and from a
project's own .claude/agents. A pack that only some projects need is kept canonical here,
in agent-packs/<pack>/*.md, and copied into the projects listed in agent-packs/<pack>/targets.txt
(one absolute path per line, # comments allowed). That keeps its descriptions out of the
agent listing of every other session.

  python tools/agent_pack_sync.py <pack> --check    report per target: OK / MISSING / DRIFT
  python tools/agent_pack_sync.py <pack> --apply    copy MISSING files; never overwrite DRIFT

It never deletes and never overwrites a file whose content differs: a drifted copy may hold a
project's deliberate edit, so it is reported and left for a human. Exit 0 = every target OK
after the run, 1 = some DRIFT or MISSING remains, 2 = the pack itself is unreadable.
"""
import hashlib
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load(pack):
    pdir = os.path.join(ROOT, 'agent-packs', pack)
    tfile = os.path.join(pdir, 'targets.txt')
    if not os.path.isdir(pdir) or not os.path.isfile(tfile):
        print(f'UNREADABLE: {pdir} or its targets.txt is missing')
        sys.exit(2)
    agents = sorted(f for f in os.listdir(pdir) if f.endswith('.md'))
    if not agents:
        print(f'UNREADABLE: {pdir} holds no agent .md files')
        sys.exit(2)
    with open(tfile, encoding='utf-8-sig') as fh:
        targets = [ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith('#')]
    return pdir, agents, targets


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in ('--check', '--apply'):
        print(__doc__)
        sys.exit(2)
    pack, apply = sys.argv[1], sys.argv[2] == '--apply'
    pdir, agents, targets = load(pack)
    bad = 0
    for tgt in targets:
        if not os.path.isdir(tgt):
            print(f'MISSING-PROJECT  {tgt}')
            bad += 1
            continue
        adir = os.path.join(tgt, '.claude', 'agents')
        counts = {'OK': 0, 'MISSING': 0, 'DRIFT': 0, 'COPIED': 0}
        for name in agents:
            src, dst = os.path.join(pdir, name), os.path.join(adir, name)
            if not os.path.exists(dst):
                if apply:
                    os.makedirs(adir, exist_ok=True)
                    shutil.copyfile(src, dst)
                    counts['COPIED' if sha(dst) == sha(src) else 'DRIFT'] += 1
                else:
                    counts['MISSING'] += 1
            elif sha(dst) == sha(src):
                counts['OK'] += 1
            else:
                counts['DRIFT'] += 1
                print(f'  DRIFT {dst}  (left untouched)')
        state = 'OK' if counts['MISSING'] == counts['DRIFT'] == 0 else 'NOT-OK'
        bad += state != 'OK'
        print(f'{state:6} {tgt}  ' + ' '.join(f'{k.lower()}={v}' for k, v in counts.items() if v))
    print(f'pack={pack} agents={len(agents)} targets={len(targets)} not_ok={bad}')
    sys.exit(0 if bad == 0 else 1)


if __name__ == '__main__':
    main()
