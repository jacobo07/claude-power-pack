"""KSR context-admission forensics, stage 1 (PLAN-KSR-EPOCH-REHYDRATION s12, C). Read-only, deterministic.

Measures, per source class, the model-visible text ADMITTED into each main session and its CARRIAGE:
the number of later model calls it stays resident (until the next compaction boundary or session end).
Carriage x 0.1 (cache-read weight) is the item's share of weighted spend; the denominator is the
weighted usage of the SAME files (no cross-denominator mixing).

Units: chars; tokens are an ESTIMATE (chars / 3.6). Observable use and durability are stage 2.
Blind spots: text the harness sends but never writes to the JSONL is invisible here; image blocks
are counted as a flat 6000 chars; a result truncated by the harness is counted as written.
"""
import glob, hashlib, json, os, re, sys
from collections import Counter, defaultdict

CORPUS = r"C:\Users\User\.claude\projects\C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects"
CHARS_PER_TOKEN = 3.6
W = {"inp": 1.0, "cw5": 1.25, "cw1h": 2.0, "cr": 0.1, "out": 5.0}

# Ordered (needle, class); needles are lowercase, forward-slash. First match wins.
READ_CLASSES = [
    ("/.claude/projects/c--users-user-desktop-cursor-projects-wii-projects-kobiisports-resort-cursorprojects/memory/", "read:auto-memory"),
    ("/appdata/local/temp/claude/", "read:harness-temp (scratchpad/task output)"),
    ("/.claude/skills/", "read:~/.claude skills/PP"),
    ("/.claude/", "read:~/.claude other"),
    ("/downloads/promptsss/", "read:Owner prompt library"),
    ("/apps/recon_work/", "read:recon_work worktrees"),
    ("/.ksr_vault/evidence/", "read:ksr_vault/evidence"),
    ("/.ksr_vault/frontier/", "read:ksr_vault/frontier"),
    ("/.ksr_vault/handoffs/", "read:ksr_vault/handoffs"),
    ("/.ksr_vault/", "read:ksr_vault/other"),
    ("/.planning/", "read:planning"),
    ("/tools/caddie/src/", "read:caddie C++ src"),
    ("/tools/", "read:KSR tools"),
    ("/kobiisports resort/cursorprojects/", "read:KSR other"),
]
BOOT_NAMES = {"resumption_file.md", "resumption_page2.md", "session_state.md", "intocables.md",
              "lessons.md", "project_session_handoff.md", "backlog_owner_stop_20261001.md", "ksr_backlog.json"}

PS_CLASSES = [
    (r"\bgit(\.exe)?['\"]?\s+(-C\s+\S+\s+|-C\s+'[^']*'\s+|-C\s+\"[^\"]*\"\s+)*(diff|show)\b|&\s*\$g\b.*\b(diff|show)\b", "ps:git diff/show"),
    (r"\bgit(\.exe)?\b.*\b(log|status|rev-parse|branch|worktree)\b|&\s*\$g\b", "ps:git status/log/other"),
    (r"\bssh\b|\bscp\b", "ps:ssh/remote"),
    (r"\btest_\w+\.py\b|\bpytest\b|\bmix\s+test\b", "ps:tests"),
    (r"\bmake\.py\b|\bbuild\b|\bcmake\b|\bmsbuild\b|devkitppc|powerpc-eabi", "ps:build"),
    (r"\bGet-Content\b|\bcat\b|\btype\b\s", "ps:file content via shell"),
    (r"\bSelect-String\b|\bfindstr\b|\brg\b|\bgrep\b", "ps:search"),
    (r"\bGet-ChildItem\b|\bls\b|\bdir\b|\bTest-Path\b|\bGet-Item\b", "ps:discovery/metadata"),
    (r"\bGet-Process\b|\bGet-CimInstance\b|\btasklist\b|\bGet-ScheduledTask\b|\bnvidia-smi\b", "ps:process/system"),
    (r"python(\.exe)?['\"]?\s|\$py\b|\.py\b", "ps:python script (non-test)"),
]


def norm(p):
    return (p or "").replace("\\", "/").lower()


def read_class(path):
    n = norm(path)
    if os.path.basename(n) in BOOT_NAMES or n.endswith("/resumption_file.md") or \
            (n.endswith("/.planning/state.md") and "kobiisports" in n) or n.endswith("/.planning/roadmap.md") and "kobiisports" in n:
        return "read:boot docs"
    for needle, cls in READ_CLASSES:
        if needle in n:
            return cls
    return "read:unclassified"


def ps_class(cmd):
    for rx, cls in PS_CLASSES:
        if re.search(rx, cmd or "", re.I):
            return cls
    return "ps:other"


def self_test():
    """Positive controls on REAL path shapes seen in this corpus; unknown must stay unknown."""
    cases = {
        r"C:\Users\User\.claude\projects\C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects\memory\KADOS_STARLET.md": "read:auto-memory",
        r"C:\Users\User\.claude\projects\C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects\memory\SESSION_STATE.md": "read:boot docs",
        r"C:\Users\User\Desktop\Cursor Projects\Wii Projects\KobiiSports Resort\CursorProjects\tools\caddie\src\main.cpp": "read:caddie C++ src",
        r"C:\Users\User\Desktop\Cursor Projects\Wii Projects\KobiiSports Resort\CursorProjects\tools\keos\autopilot.py": "read:KSR tools",
        r"C:\Users\User\.claude\gsd-core\workflows\autonomous.md": "read:~/.claude other",
        r"C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt": "read:Owner prompt library",
        r"C:\Users\User\Apps\recon_work\wt_keosdtk_home\.planning\workstreams\decomp\ROADMAP.md": "read:recon_work worktrees",
        r"D:\elsewhere\thing.bin": "read:unclassified",
        "c:/users/user/.claude/projects/C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects/memory/X.md": "read:auto-memory",
        "C:/Users/User/.claude/projects/C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects/memoryx/X.md": "read:~/.claude other",
    }
    bad = [(p, read_class(p), want) for p, want in cases.items() if read_class(p) != want]
    ps_cases = {
        "$g='C:\\Program Files\\Git\\cmd\\git.exe'; & $g -C $r diff --stat": "ps:git diff/show",
        "& 'C:\\Program Files\\Git\\cmd\\git.exe' -C 'x' log --oneline -5": "ps:git status/log/other",
        "ssh -i $k kobicraft@host 'ls'": "ps:ssh/remote",
        "& $py tools\\governance\\test_size_gate.py": "ps:tests",
        "Get-Content foo.txt -TotalCount 50": "ps:file content via shell",
        "Write-Output hello": "ps:other",
    }
    bad += [(c, ps_class(c), want) for c, want in ps_cases.items() if ps_class(c) != want]
    if bad:
        for b in bad:
            print("SELFTEST FAIL", b)
        sys.exit(2)
    print("SELFTEST PASS", len(cases) + len(ps_cases), "cases")


def text_len(content):
    if isinstance(content, str):
        return len(content)
    n = 0
    for b in content or []:
        if isinstance(b, dict):
            if b.get("type") == "text":
                n += len(b.get("text", ""))
            elif b.get("type") == "image":
                n += 6000
            else:
                n += len(json.dumps(b))
    return n


def analyse(fp):
    """Return per-class admitted chars and carriage (chars x later model calls), two windows."""
    events = []        # (call_index_at_admission, cls, chars, pre_edit)
    boundaries = []    # call indices where a compaction boundary sits
    calls = 0
    seen = set()
    id2 = {}
    edited = False
    usage = Counter()
    for line in open(fp, encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("isCompactSummary") or (d.get("type") == "system" and d.get("subtype") == "compact_boundary"):
            boundaries.append(calls)
        m = d.get("message") or {}
        a = d.get("attachment")
        if isinstance(a, dict):
            events.append((calls, "attach:" + str(a.get("type")), len(json.dumps(a)), not edited))
        if d.get("type") == "assistant":
            u = m.get("usage")
            mid = m.get("id")
            if u and mid and mid not in seen:
                seen.add(mid)
                calls += 1
                cc = u.get("cache_creation") or {}
                cw1 = cc.get("ephemeral_1h_input_tokens", 0) or 0
                cwt = u.get("cache_creation_input_tokens", 0) or 0
                usage["inp"] += u.get("input_tokens", 0) or 0
                usage["cw1h"] += cw1
                usage["cw5"] += (cc.get("ephemeral_5m_input_tokens") if cc.get("ephemeral_5m_input_tokens") is not None else cwt - cw1)
                usage["cr"] += u.get("cache_read_input_tokens", 0) or 0
                usage["out"] += u.get("output_tokens", 0) or 0
            for b in m.get("content") or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    events.append((calls, "assistant:text", len(b.get("text", "")), not edited))
                elif b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    events.append((calls, "assistant:tool_input", len(json.dumps(inp)), not edited))
                    id2[b.get("id")] = (b.get("name"), inp)
                    if b.get("name") in ("Edit", "Write", "NotebookEdit"):
                        edited = True
        elif d.get("type") == "user":
            c = m.get("content")
            if isinstance(c, str):
                events.append((calls, "user:text", len(c), not edited))
            elif isinstance(c, list):
                for b in c:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_result":
                        nm, inp = id2.get(b.get("tool_use_id"), ("?", {}))
                        if nm == "Read":
                            cls = read_class(inp.get("file_path"))
                        elif nm in ("PowerShell", "Bash"):
                            cls = ps_class(inp.get("command")) if nm == "PowerShell" else "bash:" + ps_class(inp.get("command"))[3:]
                        else:
                            cls = "tool:" + str(nm)
                        events.append((calls, cls, text_len(b.get("content")), not edited))
                    elif b.get("type") == "text":
                        events.append((calls, "user:text", len(b.get("text", "")), not edited))
    total_calls = calls
    out = defaultdict(Counter)
    for ci, cls, n, pre in events:
        nxt = next((x for x in boundaries if x > ci), total_calls)
        carried = max(nxt - ci, 0)
        out[cls]["chars"] += n
        out[cls]["carriage"] += n * carried
        if pre:
            out[cls]["pre_chars"] += n
    return out, usage, total_calls, len(boundaries)


def weighted(u):
    return sum(u[k] * W[k] for k in W)


def main():
    self_test()
    files = sorted(glob.glob(os.path.join(CORPUS, "*.jsonl")))
    agg = defaultdict(Counter)
    usage = Counter()
    calls = 0
    for fp in files:
        o, u, c, _ = analyse(fp)
        usage.update(u)
        calls += c
        for k, v in o.items():
            agg[k].update(v)
    den = weighted(usage)
    cr = usage["cr"]
    car_tok = {k: v["carriage"] / CHARS_PER_TOKEN for k, v in agg.items()}
    tot_car = sum(car_tok.values())
    pre_tot = sum(v["pre_chars"] for v in agg.values())
    res = {"files": len(files), "model_calls": calls, "weighted_denominator": round(den),
           "cache_read_tokens": cr, "carriage_tokens_total_est": round(tot_car),
           "carriage_over_cache_read": round(tot_car / max(cr, 1), 4),
           "classes": {k: {"chars": v["chars"], "pre_edit_chars": v["pre_chars"],
                           "pre_edit_share": round(v["pre_chars"] / max(pre_tot, 1), 4),
                           "carriage_tokens_est": round(car_tok[k]),
                           "estate_share_of_weighted": round(car_tok[k] * W["cr"] / den, 4)}
                       for k, v in sorted(agg.items(), key=lambda x: -car_tok[x[0]])}}
    blob = json.dumps(res, indent=1, sort_keys=True)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctx_admission_out.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(blob)
    print("sha256", hashlib.sha256(blob.encode()).hexdigest())
    print("files", len(files), "calls", calls, "weighted_den %.1fM" % (den / 1e6), "cache_read %.1fM" % (cr / 1e6),
          "carriage_est %.1fM" % (tot_car / 1e6), "carriage/cache_read %.2f" % (tot_car / max(cr, 1)))
    print("%-44s %12s %9s %12s %8s" % ("class", "chars", "pre_edit%", "carriage_tok", "estate%"))
    for k, v in list(res["classes"].items())[:30]:
        print("%-44s %12d %8.1f%% %12d %7.2f%%" % (k[:44], v["chars"], 100 * v["pre_edit_share"], v["carriage_tokens_est"], 100 * v["estate_share_of_weighted"]))


if __name__ == "__main__":
    main()
