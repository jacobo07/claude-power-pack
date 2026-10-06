#!/usr/bin/env python3
"""KME-L equivalence comparator (incremental-cognition phase 2, plan 02-02).

Judges a candidate measurement directory against the seven committed KME-L measurement files by sha256 after
masking exactly the volatile fields (`measured_at`, `command`, and the 40-hex `commit` of H's consumed owner
verdicts). SAME additionally needs an equal `corpus.sessions_scanned` and, for pillar H, an equal owner-verdict
map. It only reads: the committed files are never opened for writing. It prints keys and line numbers, never the
content of a line (HR-SECRET-002).

    kme_equivalence.py compare --candidate DIR --committed DIR [--denominator KME-L] [--date 2026-10-05]
                               [--pillars DEFGHIL]
    kme_equivalence.py selftest-perturb --committed DIR [--denominator KME-L] [--date 2026-10-05]
                               [--pillars DEFGHIL]

Exit codes: 0 every pillar SAME (or selftest PASS), 1 otherwise, 2 usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PILLARS = "DEFGHIL"
MASK = "<MASKED>"
# Each pattern has two groups, (prefix)(value); only the value is replaced by MASK. Masking is limited to the
# three proven-volatile fields (RESEARCH section 1): the front-matter and JSON forms of measured_at and command,
# and the 40-hex commit inside H's consumed_owner_verdicts (rendered details line and JSON).
VOLATILE = (
    re.compile(r"(?m)^(measured_at: )(.*)$"),
    re.compile(r"(?m)^(command: )(.*)$"),
    re.compile(r'(?m)^(\s*"measured_at": )("(?:[^"\\]|\\.)*")'),
    re.compile(r'(?m)^(\s*"command": )("(?:[^"\\]|\\.)*")'),
    re.compile(r'("commit": )("[0-9a-f]{40}")'),
)
_JSON_BLOCK = re.compile(r"<!-- (kmep|kmer)-json -->\n(.*?)\n<!-- /\1-json -->", re.S)


def normalise(text):
    for rx in VOLATILE:
        text = rx.sub(lambda m: m.group(1) + MASK, text)
    return text


def normalised_sha(text):
    return hashlib.sha256(normalise(text).encode("utf-8")).hexdigest()


def parse_json_block(text):
    """The JSON object between the instrument's markers (kmep for D..I, kmer for L); None when absent or invalid."""
    m = _JSON_BLOCK.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(2))
    except ValueError:
        return None


def sessions_of(doc):
    try:
        return doc["corpus"]["sessions_scanned"]
    except (TypeError, KeyError):
        return None


def h_verdict_map(doc):
    try:
        return doc["details"]["consumed_owner_verdicts"]["pillars"]
    except (TypeError, KeyError):
        return None


def key_at(lines, idx):
    """Name of the front-matter key, JSON path or body section holding line `idx` (0-based). Never line content."""
    if idx >= len(lines):
        return "eof"
    if lines and lines[0] == "---":
        end = next((i for i in range(1, len(lines)) if lines[i] == "---"), None)
        if end is not None and idx <= end:
            return lines[idx].split(":", 1)[0] if idx not in (0, end) else "front-matter-fence"
    start = next((i for i, ln in enumerate(lines) if re.match(r"<!-- (kmep|kmer)-json -->$", ln)), None)
    if start is not None and idx > start:
        stack = []
        for i in range(start + 1, idx + 1):
            ln = lines[i]
            indent = len(ln) - len(ln.lstrip())
            while stack and stack[-1][0] >= indent:
                stack.pop()
            m = re.match(r'\s*"([^"]+)":\s*(.*)$', ln)
            if i == idx:
                return ".".join([k for _, k in stack] + ([m.group(1)] if m else [])) or "json"
            if m and m.group(2).rstrip().endswith(("{", "[")):
                stack.append((indent, m.group(1)))
        return "json"
    heading = ""
    for i in range(idx, -1, -1):
        if lines[i].startswith("## "):
            heading = lines[i][3:].strip()
            break
    return f"body:{heading}" if heading else "body"


def compare_text(committed, candidate, pillar):
    """Verdict dict for one pillar: verdict SAME|DIFFERENT, why (list), shas, sessions pair, first diff, key."""
    nc, nn = normalise(committed), normalise(candidate)
    sha_c = hashlib.sha256(nc.encode("utf-8")).hexdigest()
    sha_n = hashlib.sha256(nn.encode("utf-8")).hexdigest()
    doc_c, doc_n = parse_json_block(committed), parse_json_block(candidate)
    sess_c, sess_n = sessions_of(doc_c), sessions_of(doc_n)
    why = []
    first_line, key = 0, "-"
    if sha_c != sha_n:
        why.append("sha")
        lc, ln_ = nc.split("\n"), nn.split("\n")
        idx = next((i for i in range(min(len(lc), len(ln_))) if lc[i] != ln_[i]), min(len(lc), len(ln_)))
        first_line, key = idx + 1, key_at(lc, idx)
    if sess_c is None or sess_n is None or sess_c != sess_n:
        why.append("sessions_scanned")
        if not first_line:
            key = "corpus.sessions_scanned"
    vmap = "n/a"
    if pillar == "H":
        map_c, map_n = h_verdict_map(doc_c), h_verdict_map(doc_n)
        if map_c is None or map_n is None or map_c != map_n:
            vmap = "DIFFERENT"
            why.append("verdict_map")
            if not first_line and key == "-":
                key = "details.consumed_owner_verdicts.pillars"
        else:
            vmap = "SAME"
    return {
        "verdict": "DIFFERENT" if why else "SAME",
        "why": why,
        "committed": sha_c,
        "candidate": sha_n,
        "sessions": (sess_n, sess_c),
        "first_diff_line": first_line,
        "key": key,
        "verdict_map": vmap,
    }


def _line(pillar, r):
    base = (f"KMEQ pillar={pillar} verdict={r['verdict']} committed={r['committed'][:12]} "
            f"candidate={r['candidate'][:12]} sessions_scanned={r['sessions'][0]}/{r['sessions'][1]} "
            f"verdict_map={r['verdict_map']}")
    if r["verdict"] == "DIFFERENT":
        base += f" why={'+'.join(r['why'])} first_diff_line={r['first_diff_line']} key={r['key']}"
    return base


def compare_dirs(candidate, committed, den, date, pillars):
    out = []
    for p in pillars:
        cpath = Path(committed) / f"{p}-{den}-{date}.md"
        cands = sorted(Path(candidate).glob(f"{p}-{den}-*.md"))
        if not cpath.is_file():
            out.append((p, {"verdict": "MISSING", "reason": "committed file absent"}))
            continue
        if len(cands) != 1:
            out.append((p, {"verdict": "MISSING",
                            "reason": "ambiguous: %d candidates" % len(cands) if cands else "no candidate"}))
            continue
        out.append((p, compare_text(cpath.read_text(encoding="utf-8"), cands[0].read_text(encoding="utf-8"), p)))
    return out


def cmd_compare(args):
    rows = compare_dirs(args.candidate, args.committed, args.denominator, args.date, args.pillars)
    same = 0
    for p, r in rows:
        if r["verdict"] == "MISSING":
            print(f"KMEQ pillar={p} verdict=MISSING reason={r['reason'].replace(' ', '_')}")
            continue
        print(_line(p, r))
        same += r["verdict"] == "SAME"
    allsame = same == len(rows) and rows
    print(f"KMEQ_VERDICT={'SAME' if allsame else 'DIFFERENT'} same={same}/{len(rows)}")
    return 0 if allsame else 1


# --------------------------------------------------------------------------- selftest (independent of VOLATILE)
def _volatilise(text):
    text = re.sub(r'(?m)^(measured_at: )".*"$', r'\1"2099-01-01T00:00:00Z"', text)
    text = re.sub(r'(?m)^( *"measured_at": )".*"(,?)$', r'\1"2099-01-01T00:00:00Z"\2', text)
    text = re.sub(r'(?m)^(command: )".*"$', r'\1"selftest --volatile"', text)
    text = re.sub(r'(?m)^( *"command": )".*"(,?)$', r'\1"selftest --volatile"\2', text)
    return re.sub(r'("commit": ")[0-9a-f]{40}(")', r"\g<1>" + "e" * 40 + r"\2", text)


def _perturb_population(text):
    m = re.search(r'("population": \{.*?"calls": )(\d+)', text, re.S)
    if not m:
        return None
    n = m.group(2)
    return text[:m.end(1)] + n[:-1] + str((int(n[-1]) + 1) % 10) + text[m.end(2):]


def _perturb_h_verdict(text):
    m = re.search(r'("consumed_owner_verdicts": \{.*?"pillars": \{\s*"[A-Z]": ")([A-Z_]+)(")', text, re.S)
    if not m:
        return None
    return text[:m.start(2)] + "OPEN_PERTURBED" + text[m.end(2):]


def cmd_selftest(args):
    ok = True
    for p in args.pillars:
        path = Path(args.committed) / f"{p}-{args.denominator}-{args.date}.md"
        if not path.is_file():
            print(f"KMEQ_SELFTEST pillar={p} missing")
            ok = False
            continue
        t = path.read_text(encoding="utf-8")
        pert = _perturb_population(t)
        got = {
            "self": compare_text(t, t, p)["verdict"],
            "volatile": compare_text(t, _volatilise(t), p)["verdict"],
            "perturb": compare_text(t, pert, p)["verdict"] if pert is not None else "NO-POPULATION-BLOCK",
        }
        want = {"self": "SAME", "volatile": "SAME", "perturb": "DIFFERENT"}
        if p == "H":
            hv = _perturb_h_verdict(_volatilise(t))
            res = compare_text(t, hv, p) if hv is not None else None
            got["h_verdict"] = res["verdict_map"] if res else "NO-VERDICT-MAP"
            want["h_verdict"] = "DIFFERENT"
        good = got == want
        ok &= good
        print("KMEQ_SELFTEST pillar=%s %s%s" % (p, " ".join(f"{k}={v}" for k, v in got.items()),
                                                "" if good else " MISMATCH"))
    print(f"KMEQ_SELFTEST={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="kme_equivalence.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    for name in ("compare", "selftest-perturb"):
        sp = sub.add_parser(name)
        if name == "compare":
            sp.add_argument("--candidate", required=True)
        sp.add_argument("--committed", required=True)
        sp.add_argument("--denominator", default="KME-L")
        sp.add_argument("--date", default="2026-10-05")
        sp.add_argument("--pillars", default=PILLARS)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code not in (0, None) else 0
    if args.cmd is None:
        ap.print_usage(sys.stderr)
        return 2
    if not args.pillars or not set(args.pillars) <= set(PILLARS) or len(set(args.pillars)) != len(args.pillars):
        print(f"kme_equivalence: --pillars must be distinct letters from {PILLARS}", file=sys.stderr)
        return 2
    dirs = [args.committed] + ([args.candidate] if args.cmd == "compare" else [])
    for d in dirs:
        if not Path(d).is_dir():
            print(f"kme_equivalence: not a directory: {d}", file=sys.stderr)
            return 2
    return cmd_compare(args) if args.cmd == "compare" else cmd_selftest(args)


if __name__ == "__main__":
    sys.exit(main())
