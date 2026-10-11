"""W6 causal token ledger over the tennis-rf workers' own transcripts.

Reuses tools/tis_observed (one call counted once, keyed by message.id+requestId) for the
token count; session_autopsy.py has no role classifier (it reports context rent only), so
the role rules live here and are deterministic (no model, no sampling).

Usage: python -I ledger.py <out.json>
"""
import json, re, sys, pathlib, collections

PP = pathlib.Path(r"C:\Users\User\.claude\skills\claude-power-pack")
STATE = pathlib.Path(r"C:\Users\User\.claude\state")
TRANSCRIPTS = pathlib.Path(r"C:\Users\User\.claude\projects\C--Users-User-Apps-recon-work-wt-tennis-rf")
SELF_UNIT = "W6"
sys.path.insert(0, str(PP / "tools"))

CATS = ["STARTUP", "READ", "REREAD", "SEARCH", "SEMANTIC", "IMPLEMENT", "PROOF", "REPAIR",
        "CONTROL", "RECOVERY", "RECEIPT", "UNATTRIBUTED"]
BUCKET = {"SEMANTIC": "semantic", "IMPLEMENT": "work", "PROOF": "work", "REPAIR": "work",
          "RECEIPT": "work", "READ": "exploration", "SEARCH": "exploration",
          "STARTUP": "tax", "REREAD": "tax", "CONTROL": "tax", "RECOVERY": "tax",
          "UNATTRIBUTED": "unattributed"}

EDIT = {"Edit", "Write", "NotebookEdit"}
SHELL = {"Bash", "PowerShell"}
RECEIPT_RE = re.compile(r"(receipt|\.partial\.json|\.residual\.md|KNOWLEDGE\.md|MEASURE\.md|JOBS\.md|claims\.jsonl|chain\.json|progress)", re.I)
GIT_RE = re.compile(r"^\s*(?:&\s*)?(?:['\"]?[^\s'\"]*git(?:\.exe)?['\"]?|\$g|git)\b|(?:^|[;&|]\s*)(?:&\s*)?(?:\$g|git(?:\.exe)?)\s+(?:-C\s+\S+\s+)?(?:log|status|add|commit|diff|show|rev-parse|branch|worktree)", re.I)
CTRL_RE = re.compile(r"gsd|mission|chain|slot_ledger|--status|--preflight|stage\.py\s+(?:status|certify)|session_autopsy|mission_spend|Get-Process|schtasks", re.I)
PROOF_RE = re.compile(r"test_|pytest|drill|judge|oracle|objdiff|verify|certify|compile|\bw\d[ab]?_\w*\.py|transform|evidence|measure|ledger|\.py\b", re.I)
SEARCH_RE = re.compile(r"\b(grep|rg|Select-String|findstr|find)\b", re.I)
READV_RE = re.compile(r"\b(gc|cat|Get-Content|type|head|tail|ls|dir|Get-ChildItem|Test-Path|sed|wc)\b", re.I)
READPATH_RE = re.compile(r"(?:\bgc|\bcat|Get-Content|\btype)\s+(?:-\w+\s+)*[\"']?([^\s\"';|]+)", re.I)
DISASM_RE = re.compile(r"(disasm|\.s$|\.asm|m2c|ghidra|objdump|fn_[0-9A-Fa-f]{6,8})", re.I)


def _norm_cmd(t):
    return (t["name"], re.sub(r"\s+", " ", str((t["input"] or {}).get("command") or (t["input"] or {}).get("pattern") or (t["input"] or {}).get("file_path") or "")).strip())


def _path(t):
    i = t["input"] or {}
    return i.get("file_path") or i.get("path") or i.get("notebook_path")


def _read_target(t):
    if t["name"] == "Read":
        return _path(t)
    if t["name"] in SHELL:
        m = READPATH_RE.search(str((t["input"] or {}).get("command") or ""))
        return m.group(1) if m else None
    return None


def classify_tool(t, st):
    """Category of ONE tool use given running state st (mutates st)."""
    n = t["name"]
    cmd = str((t["input"] or {}).get("command") or "")
    key = _norm_cmd(t)
    if key in st["failed"]:
        return "RECOVERY"
    if n in EDIT:
        p = _path(t) or ""
        st["edited"].add(p)
        st["read"].discard(p)
        if RECEIPT_RE.search(p):
            return "RECEIPT"
        return "REPAIR" if st["red"] else "IMPLEMENT"
    if n in ("Grep", "Glob"):
        return "SEARCH"
    if n == "Read":
        return "REREAD" if _read_target(t) in st["read"] else "READ"
    if n in SHELL:
        if GIT_RE.search(cmd) or CTRL_RE.search(cmd):
            return "CONTROL"
        if SEARCH_RE.search(cmd):
            return "SEARCH"
        tgt = _read_target(t)
        if tgt:
            return "REREAD" if tgt in st["read"] else "READ"
        if PROOF_RE.search(cmd):
            return "PROOF"
        if READV_RE.search(cmd):
            return "READ"
        return "UNATTRIBUTED"
    if n in ("TodoWrite", "ToolSearch", "Skill"):
        return "CONTROL"
    return "UNATTRIBUTED"


PRIO = ["RECOVERY", "REPAIR", "IMPLEMENT", "RECEIPT", "PROOF", "CONTROL", "SEARCH", "REREAD", "READ", "UNATTRIBUTED"]


def classify(calls):
    """calls: [{'tools':[{name,input,error}], 'has_text':bool}] in order -> [category]. Deterministic."""
    st = {"failed": set(), "read": set(), "edited": set(), "red": False}
    out = []
    for i, c in enumerate(calls):
        if i == 0:
            out.append("STARTUP")
            cats = []
        elif not c["tools"]:
            nxt = calls[i + 1]["tools"] if i + 1 < len(calls) else None
            if nxt is None:
                out.append("RECEIPT")  # closing statement of the session
            elif any(t["name"] in EDIT and not RECEIPT_RE.search(_path(t) or "") for t in nxt):
                out.append("SEMANTIC")
            else:
                out.append("UNATTRIBUTED")
            continue
        if i == 0 and not c["tools"]:
            continue
        cats = [classify_tool(t, st) for t in c["tools"]]
        if i == 0:
            chosen = "STARTUP"
        else:
            chosen = next(p for p in PRIO if p in cats)
            # reasoning that precedes a source edit and carries no edit itself -> SEMANTIC
            if c["has_text"] and chosen in ("READ", "SEARCH", "UNATTRIBUTED", "CONTROL") and i + 1 < len(calls) and \
               any(t["name"] in EDIT and not RECEIPT_RE.search(_path(t) or "") for t in calls[i + 1]["tools"]) and not c["tools"]:
                chosen = "SEMANTIC"
            out.append(chosen)
        # state updates after the decision
        for t, cat in zip(c["tools"], cats):
            if t.get("error"):
                st["failed"].add(_norm_cmd(t))
                if cat == "PROOF":
                    st["red"] = True
            elif cat == "PROOF":
                st["red"] = False
            tgt = _read_target(t)
            if tgt and cat in ("READ", "REREAD"):
                st["read"].add(tgt)
    return out


# ---------------- transcript reading ----------------

def read_calls(path):
    """[(call dict for classify, usage dict, ts, reads_disasm_paths)] deduped by message.id."""
    import tis_observed as tis
    ids, order, results = {}, [], {}
    with open(path, encoding="utf-8-sig") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                o = json.loads(raw)
            except json.JSONDecodeError:
                continue
            m = o.get("message")
            if not isinstance(m, dict):
                continue
            if o.get("type") == "user" and isinstance(m.get("content"), list):
                for b in m["content"]:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        txt = b.get("content")
                        txt = json.dumps(txt) if not isinstance(txt, str) else txt
                        results[b.get("tool_use_id")] = bool(b.get("is_error")) or ("Blocked by a PreToolUse" in txt)
            if o.get("type") != "assistant" or not isinstance(m.get("usage"), dict) or m.get("model") == "<synthetic>":
                continue
            key = (m.get("id"), o.get("requestId"))
            if key not in ids:
                ids[key] = {"usage": m["usage"], "ts": o.get("timestamp"), "tools": [], "has_text": False, "model": m.get("model")}
                order.append(key)
            e = ids[key]
            e["usage"] = m["usage"]
            for b in m.get("content") or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use" and not any(t["id"] == b.get("id") for t in e["tools"]):
                    e["tools"].append({"id": b.get("id"), "name": b.get("name"), "input": b.get("input") or {}, "error": False})
                elif b.get("type") in ("text", "thinking"):
                    e["has_text"] = True
    calls = [ids[k] for k in order]
    for c in calls:
        for t in c["tools"]:
            t["error"] = bool(results.get(t["id"]))
    return calls


def processed(u):
    g = lambda k: int(u.get(k) or 0)
    return g("input_tokens") + g("cache_creation_input_tokens") + g("cache_read_input_tokens") + g("output_tokens")


def ctx(u):
    g = lambda k: int(u.get(k) or 0)
    return g("input_tokens") + g("cache_creation_input_tokens") + g("cache_read_input_tokens")


def unit_of(packet):
    name = pathlib.Path(packet).name
    m = re.match(r"WU-(\w+?)\.md", name)
    return m.group(1) if m else None


def missions():
    rows = []
    for f in sorted(STATE.glob("gsd-mission-*.json")):
        j = json.loads(f.read_text(encoding="utf-8-sig"))
        p = (j.get("wu_packet") or {}).get("path") or ""
        if "vault\\programs\\tennis-rf\\" not in p:
            continue
        rows.append({"mission": j["mission_id"], "unit": unit_of(p), "packet": pathlib.Path(p).name,
                     "session": (j.get("owner") or {}).get("session_id"),
                     "mission_tokens": (j.get("slim_result") or {}).get("tokens"),
                     "state": j.get("state")})
    return rows


def build():
    rows = missions()
    seen_sessions, units = set(), collections.OrderedDict()
    sess_out, skipped = [], []
    for r in rows:
        if r["unit"] == SELF_UNIT:
            skipped.append({**r, "why": "this unit (RUNNING, cannot attribute itself)"})
            continue
        sid = r["session"]
        f = TRANSCRIPTS / f"{sid}.jsonl" if sid else None
        if not sid or not f.exists() or sid in seen_sessions:
            skipped.append({**r, "why": "no session/transcript" if not sid or not f.exists() else "duplicate session"})
            continue
        seen_sessions.add(sid)
        calls = read_calls(f)
        cats = classify([{"tools": c["tools"], "has_text": c["has_text"]} for c in calls])
        floor = ctx(calls[0]["usage"]) if calls else 0
        u = units.setdefault(r["unit"], {"calls": collections.Counter(), "tokens": collections.Counter(),
                                          "floor_rent": 0, "total": 0, "new_tokens": 0, "sessions": 0, "mission_tokens": 0,
                                          "errors": 0, "disasm_reads": 0, "disasm_rereads": 0})
        u["sessions"] += 1
        u["mission_tokens"] += r["mission_tokens"] or 0
        for c, cat in zip(calls, cats):
            p = processed(c["usage"])
            u["calls"][cat] += 1
            u["tokens"][cat] += p
            u["total"] += p
            u["floor_rent"] += min(floor, ctx(c["usage"])) + (0)
            ug = c["usage"]
            u["new_tokens"] += int(ug.get("input_tokens") or 0) + int(ug.get("cache_creation_input_tokens") or 0) + int(ug.get("output_tokens") or 0)
            u["errors"] += sum(1 for t in c["tools"] if t["error"])
            for t in c["tools"]:
                tgt = _read_target(t) or ""
                if cat in ("READ", "REREAD") and DISASM_RE.search(tgt):
                    u["disasm_reads" if cat == "READ" else "disasm_rereads"] += 1
        sess_out.append({"session": sid, "unit": r["unit"], "calls": len(calls), "processed": sum(processed(c["usage"]) for c in calls),
                         "mission_tokens": r["mission_tokens"]})
    return units, sess_out, skipped


def build_json():
    units, sess, skipped = build()
    tot_t, tot_c = collections.Counter(), collections.Counter()
    out_units = {}
    T = N = F = D = DR = MT = ERR = 0
    for name, u in units.items():
        T += u["total"]; N += u["new_tokens"]; F += u["floor_rent"]; MT += u["mission_tokens"]; ERR += u["errors"]
        D += u["disasm_reads"]; DR += u["disasm_rereads"]
        tot_t.update(u["tokens"]); tot_c.update(u["calls"])
        out_units[name] = {"sessions": u["sessions"], "processed_tokens": u["total"], "calls": sum(u["calls"].values()),
                           "mission_tokens": u["mission_tokens"],
                           "categories": {c: {"calls": u["calls"][c], "tokens": u["tokens"][c],
                                              "share": round(u["tokens"][c] / u["total"], 4) if u["total"] else None}
                                          for c in CATS}}
    cat_tab = {c: {"calls": tot_c[c], "tokens": tot_t[c], "share": round(tot_t[c] / T, 4) if T else None} for c in CATS}
    buckets = collections.Counter()
    for c in CATS:
        buckets[BUCKET[c]] += tot_t[c]
    attributed = T - tot_t["UNATTRIBUTED"]
    return {
        "generated_by": "evidence/w6/ledger.py (deterministic)",
        "units": out_units, "total": {"processed_tokens": T, "calls": sum(tot_c.values()), "categories": cat_tab,
                                      "buckets": {k: {"tokens": v, "share": round(v / T, 4) if T else None} for k, v in buckets.items()}},
        "attribution": {"attributed_share": round(attributed / T, 4) if T else None,
                        "unattributed_share": round(tot_t["UNATTRIBUTED"] / T, 4) if T else None,
                        "transcript_processed_total": T, "mission_record_tokens_total": MT,
                        "mission_vs_transcript_note": "mission slim_result.tokens is the harness's own counter; compare, do not mix"},
        "derived": {
            "llm_invocation_density": {"calls_total": sum(tot_c.values()),
                                       "calls_per_session": round(sum(tot_c.values()) / len(sess), 2) if sess else None,
                                       "semantic_calls": tot_c["SEMANTIC"],
                                       "per_verified_function": "UNKNOWN (verified functions = 0 across W1-W5b)"},
            "context_duplication_factor": round(T / N, 2) if N else None,
            "context_duplication_def": "processed (input+cache_creation+cache_read+output) / new (input+cache_creation+output)",
            "startup_tax": {"first_call_tokens": tot_t["STARTUP"], "first_call_share": round(tot_t["STARTUP"] / T, 4) if T else None,
                            "floor_rent_tokens": F, "floor_rent_share": round(F / T, 4) if T else None,
                            "floor_rent_def": "sum over calls of min(first-call context of session, call context): the part re-read on every call that a fresh epoch pays anyway"},
            "raw_binary_page_fault_rate": {"disasm_reads": D, "disasm_rereads": DR,
                                           "rate": round(DR / (D + DR), 4) if (D + DR) else "UNKNOWN (no disassembly-path reads observed)",
                                           "note": "re-reads of disassembly-like paths by Read/gc/cat only; per-function recorded-ness is UNKNOWN"},
            "model_displacement_rate": "UNKNOWN (0 verified functions and 0 model-free closures in W5a/W5b; no layer-closed denominator)",
            "failed_tool_calls": ERR,
        },
        "tokens_per_verified_function": {"verified_functions": 0, "value": "UNKNOWN",
                                         "semantic_tokens": buckets["semantic"], "tax_tokens": buckets["tax"],
                                         "work_tokens": buckets["work"], "exploration_tokens": buckets["exploration"],
                                         "semantic_share": round(buckets["semantic"] / T, 4) if T else None,
                                         "tax_share": round(buckets["tax"] / T, 4) if T else None},
        "sessions": sess, "skipped": skipped,
    }


if __name__ == "__main__":
    res = build_json()
    pathlib.Path(sys.argv[1]).write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({"total": res["total"]["processed_tokens"], "attr": res["attribution"]}, indent=1))
