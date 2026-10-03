"""KSR boot-rehydration archaeology (PLAN-KSR-EPOCH-REHYDRATION T1). EXPERIMENTAL, read-only.

PRE-REGISTERED (written 2026-10-03 before the first run; any change after the first run is
recorded in the T2 audit file as a deviation):

  Boot window   : from session start to the first Edit/Write tool_use (or session end).
  Boot docs     : BOOT_DOCS below, matched by absolute path (case-insensitive).
  Eligible      : (a) main session file (not subagents/), (b) not 489739e3, (c) >=1 boot-doc
                  Read inside the boot window, (d) EVERY boot doc read in the boot window has a
                  current mtime earlier than that read's timestamp (it read today's bytes).
  Sample        : if eligible N <= 12 use all; else a seeded draw (seed 20261003) of 12,
                  round-robin over strata (regime x first-boot-doc). N < 6 -> T8 INCONCLUSIVE.
  Regime        : PRE_STOP if session start < 2026-10-01T11:52:19Z (commit 14f7840), else POST_STOP.
  Fact          : an identifier token (FACT_RE) from a boot-window SOURCE: boot-doc read results,
                  git-log shell results, Owner messages.
  Consumed      : the fact appears later in the same session in assistant text or tool_use input.
  Controls      : planted positive, planted negative, cross-session shuffle, A/A rerun.
Blind spot: identifier-free facts ("do not touch X" without a token) are invisible here; the
critical set is therefore labelled by hand in T2 and frozen before any generator code.
"""
import glob, hashlib, json, os, random, re, sys
from datetime import datetime, timezone

CORPUS = r"C:\Users\User\.claude\projects\C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects"
K = r"C:\Users\User\Desktop\Cursor Projects\Wii Projects\KobiiSports Resort\CursorProjects"
M = CORPUS + r"\memory"
BOOT_DOCS = [K + r"\RESUMPTION_FILE.md", K + r"\RESUMPTION_PAGE2.md", K + r"\.planning\STATE.md",
             K + r"\.planning\ROADMAP.md", M + r"\SESSION_STATE.md", M + r"\INTOCABLES.md",
             M + r"\LESSONS.md", M + r"\project_session_handoff.md",
             K + r"\.ksr_vault\frontier\BACKLOG_OWNER_STOP_20261001.md",
             K + r"\.ksr_vault\frontier\KSR_BACKLOG.json"]
BOOT = {os.path.normcase(p): p for p in BOOT_DOCS}
EXCLUDE = {"489739e3"}
STOP_TS = datetime(2026, 10, 1, 11, 52, 19, tzinfo=timezone.utc)
FACT_RE = re.compile(r"0x[0-9A-Fa-f]{6,8}\b|\b[A-Z][A-Z0-9]*(?:[-_][A-Z0-9]+)+\b|[\w./\\-]+\.(?:py|md|cpp|h|json|sh|ps1|dol|wbfs|elf|txt)\b")
STOPWORDS = {"UTF-8", "SHA-256", "UTF_8", "CLAUDE_CODE", "GPT-4", "X-API"}


def ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def text_of(content):
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if isinstance(b, dict) and b.get("type") == "text":
            out.append(b.get("text", ""))
    return "\n".join(out)


def facts(text):
    return {f for f in FACT_RE.findall(text or "") if f not in STOPWORDS and len(f) >= 5}


def owner_text(d):
    if d.get("type") != "user" or d.get("isMeta") or d.get("isSidechain"):
        return None
    c = (d.get("message") or {}).get("content")
    if isinstance(c, str):
        t = c
    elif isinstance(c, list) and c and all(isinstance(b, dict) and b.get("type") == "text" for b in c):
        t = text_of(c)
    else:
        return None
    if t.lstrip().startswith(("<command-", "<local-command", "<system-reminder", "<task-notification", "Caveat:")):
        return None
    return t


def analyse(fp, plant=None):
    sid = os.path.basename(fp)[:8]
    id2 = {}
    sources = {}          # fact -> (source kind, order index)
    later_text = []       # (order, text)
    boot_reads = []       # (ts, path, chars)
    first_doc = None
    instructed = "ambient"
    first_owner = None
    start = None
    boot_end = None
    order = 0
    for line in open(fp, encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        order += 1
        t = ts(d.get("timestamp", ""))
        if t and start is None:
            start = t
        ot = owner_text(d)
        if ot is not None:
            if first_owner is None:
                first_owner = ot
            if boot_end is None:
                for f in facts(ot):
                    sources.setdefault(f, ("owner", order))
        m = d.get("message") or {}
        c = m.get("content")
        if d.get("type") == "assistant" and isinstance(c, list):
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    later_text.append((order, b.get("text", "")))
                elif b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    later_text.append((order, json.dumps(inp)))
                    if b.get("name") in ("Edit", "Write", "NotebookEdit") and boot_end is None:
                        boot_end = order
                    if boot_end is None:
                        id2[b.get("id")] = (b.get("name"), inp)
        elif d.get("type") == "user" and isinstance(c, list) and boot_end is None:
            for b in c:
                if not (isinstance(b, dict) and b.get("type") == "tool_result"):
                    continue
                nm, inp = id2.pop(b.get("tool_use_id"), (None, {}))
                body = text_of(b.get("content")) if not isinstance(b.get("content"), str) else b.get("content")
                if nm == "Read":
                    p = os.path.normcase(inp.get("file_path", ""))
                    if p in BOOT:
                        if plant and plant.get("boot"):
                            body = body + "\n" + plant["boot"]
                        boot_reads.append((t, BOOT[p], len(body)))
                        if first_doc is None:
                            first_doc = os.path.basename(BOOT[p])
                            if first_owner and os.path.basename(BOOT[p]).lower() in first_owner.lower():
                                instructed = "prompt"
                        for f in facts(body):
                            sources.setdefault(f, ("doc:" + os.path.basename(BOOT[p]), order))
                elif nm in ("PowerShell", "Bash") and re.search(r"\bgit\b.*\blog\b", inp.get("command", "")):
                    for f in facts(body):
                        sources.setdefault(f, ("gitlog", order))
    if plant and plant.get("later"):
        later_text.append((order + 1, plant["later"]))
    consumed = {}
    for f, (kind, o) in sources.items():
        for lo, tx in later_text:
            if lo > o and f in tx:
                consumed[f] = kind
                break
    return {"sid": sid, "start": start.isoformat() if start else None, "first_doc": first_doc,
            "instructed": instructed, "boot_reads": [(r[0].isoformat() if r[0] else None, os.path.basename(r[1]), r[2]) for r in boot_reads],
            "boot_doc_paths": sorted({r[1] for r in boot_reads}), "boot_read_ts": [r[0] for r in boot_reads],
            "sources_n": len(sources), "consumed": consumed, "_later": later_text, "_sources": sources}


def eligible(r):
    if r["sid"] in EXCLUDE or not r["boot_reads"]:
        return False, "no boot-doc read" if not r["boot_reads"] else "excluded"
    for rts_s, name, _ in r["boot_reads"]:
        path = next(p for p in BOOT_DOCS if os.path.basename(p) == name)
        mt = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
        if rts_s is None or ts(rts_s) <= mt:
            return False, f"{name} changed after it was read"
    return True, "ok"


def main():
    files = sorted(glob.glob(os.path.join(CORPUS, "*.jsonl")))
    recs = [analyse(f) for f in files]
    elig = []
    reasons = {}
    for r in recs:
        ok, why = eligible(r)
        reasons[why] = reasons.get(why, 0) + 1
        if ok:
            r["regime"] = "POST_STOP" if ts(r["start"]) >= STOP_TS else "PRE_STOP"
            elig.append(r)
    if len(elig) <= 12:
        sample = elig
    else:
        rnd = random.Random(20261003)
        strata = {}
        for r in sorted(elig, key=lambda x: x["sid"]):
            strata.setdefault((r["regime"], r["first_doc"]), []).append(r)
        for v in strata.values():
            rnd.shuffle(v)
        sample, keys = [], sorted(strata)
        while len(sample) < 12:
            for k in keys:
                if strata[k] and len(sample) < 12:
                    sample.append(strata[k].pop())
    # controls
    ctrl = {}
    if sample:
        fp0 = os.path.join(CORPUS, [f for f in files if os.path.basename(f).startswith(sample[0]["sid"])][0])
        pos = analyse(fp0, plant={"boot": "ZZPLANT-4242", "later": "uses ZZPLANT-4242 here"})
        neg = analyse(fp0, plant={"boot": "ZZPLANT-9191"})
        ctrl["positive_planted_consumed"] = "ZZPLANT-4242" in pos["consumed"]
        ctrl["negative_planted_consumed"] = "ZZPLANT-9191" in neg["consumed"]
        self_rate, cross_rate = [], []
        for i, a in enumerate(sample):
            b = sample[(i + 1) % len(sample)]
            srcs = a["_sources"]
            if not srcs:
                continue
            self_rate.append(len(a["consumed"]) / len(srcs))
            cross = sum(1 for f in srcs if any(f in tx for _, tx in b["_later"]))
            cross_rate.append(cross / len(srcs))
        ctrl["self_consumption_mean"] = round(sum(self_rate) / max(len(self_rate), 1), 4)
        ctrl["cross_session_shuffle_mean"] = round(sum(cross_rate) / max(len(cross_rate), 1), 4)
    union = {}
    for r in sample:
        for f, kind in r["consumed"].items():
            union.setdefault(f, set()).add(r["sid"])
    overlap = {k: v for k, v in sorted(union.items()) if len(v) >= 2}
    out = {
        "corpus_files": len(files), "eligibility_reasons": reasons, "eligible_n": len(elig),
        "eligible": [{k: r[k] for k in ("sid", "start", "regime", "first_doc", "instructed")} for r in elig],
        "sample": [{"sid": r["sid"], "start": r["start"], "regime": r["regime"], "first_doc": r["first_doc"],
                    "instructed": r["instructed"], "boot_reads": r["boot_reads"], "sources_n": r["sources_n"],
                    "consumed_n": len(r["consumed"]),
                    "consumed_by_source": {s: sum(1 for v in r["consumed"].values() if v == s) for s in set(r["consumed"].values())},
                    "consumed": sorted(r["consumed"])} for r in sample],
        "consumed_union_n": len(union), "consumed_in_2plus_sessions_n": len(overlap),
        "consumed_union": sorted(union), "controls": ctrl,
        "all_sessions_first_doc": {r["sid"]: [r["first_doc"], r["instructed"]] for r in recs if r["first_doc"]},
    }
    blob = json.dumps(out, indent=1, sort_keys=True, default=str)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boot_facts_out.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(blob)
    print("sha256", hashlib.sha256(blob.encode()).hexdigest())
    print("eligible_n", len(elig), "sample_n", len(sample), "reasons", reasons)
    print("controls", ctrl)
    print("consumed_union_n", len(union), "in_2plus_sessions", len(overlap))
    for r in out["sample"]:
        print(" ", r["sid"], r["start"][:16], r["regime"], r["first_doc"], r["instructed"],
              "reads", len(r["boot_reads"]), "sources", r["sources_n"], "consumed", r["consumed_n"], r["consumed_by_source"])


if __name__ == "__main__":
    main()
