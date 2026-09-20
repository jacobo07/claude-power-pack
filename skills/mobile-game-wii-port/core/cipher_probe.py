#!/usr/bin/env python3
"""Phase 2 -- characterise a packed asset corpus WITHOUT the key.

Everything here is established from structure alone. None of it needs a key,
and none of it stops being true if the algorithm guess is wrong later -- which
is the whole reason to do it before hunting a key.

What it separates, and from what:

  block vs stream   every size a multiple of 8/16 means the output is padded to
                    a block boundary. A stream cipher does not pad: its output
                    length equals its plaintext length.
  not ECB           ECB maps a repeated plaintext block to the same ciphertext
                    block anywhere in the file. Zero intra-file repeats across
                    the largest files rules it out.
  fixed key + IV    a per-file IV, nonce or salt decorrelates the heads. Files
                    sharing a byte-identical first block did not get one.
  ciphertext        entropy near 8 bits/byte. Compressed data scores the same,
                    so this CORROBORATES and never concludes.

Two readings this tool refuses to make, both paid for in the source programme:

  R-05  a shared leading block does NOT prove CBC. A reused stream keystream
        gives the identical observation. Padding is what discriminates.
  R-04  a crypto primitive found in the binary does not identify what encrypts
        these files -- run fingerprint_game.py, which checks for a linked TLS
        stack that would account for it.

Stdlib only.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter, defaultdict

KNOWN_MAGICS = {
    b"\x1bLua": "Lua bytecode",
    b"PK\x03\x04": "ZIP",
    b"7z\xbc\xaf\x27\x1c": "7z",
    b"\x1f\x8b": "gzip",
    b"\x89PNG": "PNG",
    b"RIFF": "RIFF",
    b"OggS": "Ogg",
    b"\x89LZMA\r\n\x1a\n": "LZMA-alone behind a custom magic",
}
LARGEST_FOR_ECB = 60
MAX_READ = 8 * 1024 * 1024


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def has_repeated_block(data: bytes, block: int) -> bool:
    seen = set()
    for i in range(0, len(data) - block + 1, block):
        b = data[i:i + block]
        if b in seen:
            return True
        seen.add(b)
    return False


def collect(paths):
    files = []
    for p in paths:
        try:
            with open(p, "rb") as fh:
                data = fh.read(MAX_READ)
            size = os.path.getsize(p)
        except OSError:
            continue
        files.append({"path": p, "size": size, "data": data})
    return files


def probe(files: list) -> dict:
    n = len(files)
    if not n:
        return {"error": "NO_INPUT", "why": "no readable file was found"}

    sizes = [f["size"] for f in files]
    mult16 = sum(1 for s in sizes if s % 16 == 0)
    mult8 = sum(1 for s in sizes if s % 8 == 0)

    if mult16 == n:
        block = {"verdict": "CONFIRMED", "block_size": 16,
                 "why": f"{n}/{n} files are an exact multiple of 16 B; a stream "
                        f"cipher needs no padding"}
    elif mult8 == n:
        block = {"verdict": "CONFIRMED", "block_size": 8,
                 "why": f"{n}/{n} files are an exact multiple of 8 B, but not all "
                        f"of 16 ({mult16}/{n})"}
    else:
        block = {"verdict": "ABSENT", "block_size": None,
                 "why": f"only {mult16}/{n} files are a multiple of 16 and "
                        f"{mult8}/{n} of 8 -- not block-padded, so a stream "
                        f"cipher or plain data is the reading"}

    bs = block["block_size"] or 16
    largest = sorted(files, key=lambda f: -f["size"])[:LARGEST_FOR_ECB]
    repeats = [f["path"] for f in largest if has_repeated_block(f["data"], bs)]
    if block["block_size"] is None:
        ecb = {"verdict": "UNKNOWN", "why": "no block structure to test"}
    elif repeats:
        ecb = {"verdict": "POSSIBLE_ECB", "files_with_repeats": len(repeats),
               "why": f"{len(repeats)} of {len(largest)} largest files repeat a "
                      f"{bs} B block; ECB is consistent with this"}
    else:
        ecb = {"verdict": "NOT_ECB",
               "why": f"0 of {len(largest)} largest files repeat a {bs} B block"}

    heads = defaultdict(list)
    for f in files:
        if len(f["data"]) >= bs:
            heads[f["data"][:bs]].append(f["path"])
    shared = {k: v for k, v in heads.items() if len(v) > 1}
    if block["block_size"] is None:
        iv = {"verdict": "UNKNOWN", "why": "no block structure to test"}
    elif shared:
        iv = {
            "verdict": "FIXED_KEY_AND_IV",
            "distinct_first_blocks": len(heads),
            "shared_groups": len(shared),
            "largest_group": max(len(v) for v in shared.values()),
            "why": f"{len(shared)} group(s) of files share a byte-identical "
                   f"first {bs} B block, so no per-file IV, nonce or salt is in "
                   f"play. This does NOT establish CBC -- a reused stream "
                   f"keystream produces the same observation (R-05). Padding is "
                   f"what discriminates, and it is reported above.",
        }
    else:
        iv = {"verdict": "PER_FILE_IV_OR_DISTINCT_HEADS",
              "distinct_first_blocks": len(heads),
              "why": "every file has a distinct first block; consistent with a "
                     "per-file IV/nonce, and also with distinct plaintext heads"}

    # Entropy must be read as a RATIO of what the sample size can reach, never
    # as an absolute. Empirical entropy over n bytes is capped at log2(n), so a
    # 200-byte file cannot score 7.5 bits however random it is -- and encrypted
    # script files of 144-256 B are exactly the case this tool is pointed at.
    # An absolute threshold here would refuse the real corpus.
    samples = [f["data"][:8192] for f in files]
    ents = [entropy(s) for s in samples]
    ratios = [(e / math.log2(min(256, len(s)))) if len(s) > 1 else 0.0
              for e, s in zip(ents, samples)]
    mean_ent = sum(ents) / len(ents)
    mean_ratio = sum(ratios) / len(ratios)
    low = sum(1 for r in ratios if r < 0.85)
    ceiling = sum(math.log2(min(256, max(len(s), 2))) for s in samples) / len(samples)

    magics = Counter()
    for f in files:
        hit = None
        for magic, label in KNOWN_MAGICS.items():
            if f["data"].startswith(magic):
                hit = label
                break
        magics[hit or "none"] += 1

    if magics.get("none", 0) == n:
        header = {"verdict": "NO_SIGNATURE",
                  "why": f"{n}/{n} files begin immediately in unrecognised bytes "
                         f"-- no magic, and nowhere to put a per-file IV"}
    else:
        header = {"verdict": "SIGNATURE_PRESENT", "magics": dict(magics),
                  "why": "at least one file carries a recognised magic; those "
                         "files are containers, not raw ciphertext"}

    encrypted = (
        block["verdict"] == "CONFIRMED"
        and header["verdict"] == "NO_SIGNATURE"
        and mean_ratio > 0.92
    )
    return {
        "files": n,
        "block": block,
        "ecb": ecb,
        "iv": iv,
        "entropy": {"mean_bits_per_byte": round(mean_ent, 3),
                    "mean_ceiling_bits": round(ceiling, 3),
                    "mean_ratio_of_ceiling": round(mean_ratio, 4),
                    "files_below_85pct_of_ceiling": low,
                    "why": "read as a ratio of the ceiling log2(n), because a "
                           "small file cannot reach 8 bits however random it "
                           "is. Compressed data scores the same as ciphertext "
                           "either way, so this corroborates and never "
                           "concludes"},
        "header": header,
        "overall": {
            "verdict": "ENCRYPTED_BLOCK_CIPHER" if encrypted else "UNKNOWN",
            "algorithm": "UNKNOWN",
            "why": "the algorithm is not establishable from structure. Name it "
                   "from the loader's code path, never from a primitive the "
                   "process happens to contain (R-04).",
        },
    }


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__.strip())
        print("\nusage: cipher_probe.py <directory|file> [more...] [--json]")
        return 0
    args = [a for a in argv[1:] if not a.startswith("--")]
    paths = []
    for a in args:
        if os.path.isdir(a):
            for dp, _d, fs in os.walk(a):
                paths.extend(os.path.join(dp, f) for f in fs)
        elif os.path.isfile(a):
            paths.append(a)
    if not paths:
        print("UNREADABLE_INPUT: no file found in the given paths", file=sys.stderr)
        return 2

    result = probe(collect(paths))
    if result.get("error"):
        print(f"UNREADABLE_INPUT: {result['why']}", file=sys.stderr)
        return 2

    if "--json" in argv:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print(f"=== Phase 2 cipher probe: {result['files']} files ===\n")
    for key, label in (("block", "block size"), ("ecb", "mode (ECB?)"),
                       ("iv", "IV / key reuse"), ("header", "header")):
        row = result[key]
        print(f"{label:<16} {row['verdict']}")
        for line in _wrap(row["why"]):
            print(f"                 {line}")
    e = result["entropy"]
    print(f"{'entropy':<16} {e['mean_bits_per_byte']} of a possible "
          f"{e['mean_ceiling_bits']} bits/byte "
          f"({e['mean_ratio_of_ceiling'] * 100:.1f}% of ceiling; "
          f"{e['files_below_85pct_of_ceiling']} files below 85%)")
    for line in _wrap(e["why"]):
        print(f"                 {line}")
    o = result["overall"]
    print(f"\noverall          {o['verdict']}  (algorithm: {o['algorithm']})")
    for line in _wrap(o["why"]):
        print(f"                 {line}")
    return 0


def _wrap(text: str, width: int = 60):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


if __name__ == "__main__":
    sys.exit(main(sys.argv))
