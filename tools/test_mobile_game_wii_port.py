#!/usr/bin/env python3
"""V-MGWP: done-gate for the mobile-game-wii-port skill.

Every fixture is synthesised in-process from the byte shapes the parsers
consume -- real LZMA streams from the standard library, real Lua 5.1 headers
assembled field by field, real ZIP containers holding ELF-magic binaries with
real engine literals. Nothing is drawn from any game corpus, so this gate runs
on a machine that has never seen one.

Both poles are driven for every detector, and UNKNOWN is asserted as a
REACHABLE outcome rather than only as a default -- a probe that answers UNKNOWN
to everything would pass a suite that only checks its refusals.

Run from the Power Pack repository root:
    python tools/test_mobile_game_wii_port.py
"""
from __future__ import annotations

import importlib.util
import io
import lzma
import os
import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(REPO, "skills", "mobile-game-wii-port")
CORE = os.path.join(SKILL, "core")

_passes, _fails, _unmeasured = 0, 0, 0
_failed_names = []


def _ok(name, evidence):
    global _passes
    _passes += 1
    print(f"  OK   {name}: {evidence}")


def _fail(name, diagnostic):
    global _fails
    _fails += 1
    _failed_names.append(name)
    print(f"  FAIL {name}: {diagnostic}")


def _unmeas(name, why):
    global _unmeasured
    _unmeasured += 1
    print(f"  ----  {name}: UNMEASURED -- {why}")


def _check(name, cond, ok_msg, fail_msg):
    _ok(name, ok_msg) if cond else _fail(name, fail_msg)


def _load(mod_name):
    path = os.path.join(CORE, f"{mod_name}.py")
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- fixtures

def elf_with(literals: list, pad: int = 2048) -> bytes:
    """A minimal ELF-magic blob carrying real engine literals."""
    body = b"\x7fELF\x01\x01\x01\x00" + b"\x00" * 8
    body += b"".join(lit + b"\x00" for lit in literals)
    return body + b"\x00" * pad


def make_zip(members: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".apk")
    os.close(fd)
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return path


def lua_header(num_size: int = 8, size_t: int = 4) -> bytes:
    """A real Lua 5.1 12-byte header. num_size 8 = stock double, 4 = float32."""
    return b"\x1bLua" + struct.pack(
        "<BBBBBBBB", 0x51, 0, 1, 4, size_t, 4, num_size, 0)


def lua_chunk(num_size: int = 4) -> bytes:
    return lua_header(num_size) + b"\x00" * 64


def write_tmp(data: bytes, suffix: str = ".bin") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    return path


def ciphertext_files(tmpdir, n=24, block=16, share_head=6, repeat_block=False,
                     head_magic=b"", size_mult=True):
    """Synthetic ciphertext-shaped files with controlled structure."""
    import random
    rng = random.Random(1234)
    shared = bytes(rng.randrange(256) for _ in range(block))
    paths = []
    for i in range(n):
        nblocks = 8 + (i % 5)
        body = b"".join(
            bytes(rng.randrange(256) for _ in range(block)) for _ in range(nblocks))
        if repeat_block and i == 0:
            first = body[:block]
            body = first + body[block:block * 3] + first + body[block * 4:]
        head = shared if i < share_head else bytes(
            rng.randrange(256) for _ in range(block))
        data = head_magic + head + body
        if not size_mult:
            data += b"\x01\x02\x03"
        p = os.path.join(tmpdir, f"asset_{i:03d}.dat")
        with open(p, "wb") as fh:
            fh.write(data)
        paths.append(p)
    return paths


# ---------------------------------------------------------------- gates

def gate_executables():
    named = ["fingerprint_game.py", "cipher_probe.py", "envelope_probe.py"]
    for script in named:
        path = os.path.join(CORE, script)
        if not os.path.isfile(path):
            _fail(f"V-MGWP-CORE-EXEC[{script}]", "file absent")
            continue
        proc = subprocess.run([sys.executable, path], capture_output=True, text=True)
        _check(
            f"V-MGWP-CORE-EXEC[{script}]",
            proc.returncode == 0 and "usage:" in proc.stdout,
            "runs and prints usage",
            f"rc={proc.returncode} stderr={proc.stderr.strip()[:160]!r}",
        )
    skill_md = os.path.join(SKILL, "SKILL.md")
    text = open(skill_md, encoding="utf-8").read() if os.path.isfile(skill_md) else ""
    missing = [s for s in named if s not in text]
    _check("V-MGWP-DOC-EXEC", not missing and bool(text),
           "every core tool named in SKILL.md exists and runs",
           f"SKILL.md does not name: {missing}")


def gate_fingerprint():
    fp = _load("fingerprint_game")

    native = make_zip({
        "lib/armeabi-v7a/libgame.so": elf_with(
            [b"Lua 5.1", b"_LOADED", b"bad argument #", b"rovio", b"Rovio",
             b"PVRTC", b"inflate 1.", b"/crypto/", b"X509", b"libcurl"]),
        "lib/x86/libgame.so": elf_with(
            [b"Lua 5.1", b"_LOADED", b"rovio", b"/crypto/", b"X509"]),
        "assets/scripts/characters.lua": os.urandom(4096),
        "assets/scripts/level_1.lua": os.urandom(2048),
        "classes.dex": b"dex\n035\x00" + b"\x00" * 512,
    })
    try:
        r = fp.fingerprint(native)
        v = r["verdicts"]
        _check("V-MGWP-FP-NATIVE-ENGINE",
               v["Lua 5.1"]["verdict"] == "CONFIRMED"
               and v["Rovio Fusion"]["verdict"] == "CONFIRMED"
               and r["routing"]["decision"] == "NATIVE_ENGINE",
               f"Lua 5.1 + Rovio Fusion CONFIRMED, routed NATIVE_ENGINE",
               f"verdicts={v['Lua 5.1']['verdict']}/"
               f"{v['Rovio Fusion']['verdict']} routing={r['routing']['decision']}")
        _check("V-MGWP-FP-MULTI-ABI",
               v["Lua 5.1"].get("agrees_across_binaries") is True,
               "the finding is present in BOTH binaries and they agree",
               f"agreement flag = {v['Lua 5.1'].get('agrees_across_binaries')}")
        _check("V-MGWP-FP-ASSERT-INCONCLUSIVE",
               v["Box2D"]["verdict"] == "INCONCLUSIVE",
               "Box2D reads INCONCLUSIVE, not ABSENT -- an assertions-disabled "
               "build emits no markers (R-03)",
               f"Box2D read {v['Box2D']['verdict']}")
        _check("V-MGWP-FP-ABSENT",
               v["Cocos2d-x"]["verdict"] == "ABSENT"
               and v["LuaJIT"]["verdict"] == "ABSENT",
               "Cocos2d-x and LuaJIT read ABSENT on surviving literals",
               f"cocos={v['Cocos2d-x']['verdict']} luajit={v['LuaJIT']['verdict']}")
        _check("V-MGWP-FP-TLS-CONFOUND",
               bool(r["tls_stack_present"]),
               "a linked TLS stack is flagged, so a crypto primitive in the "
               "image is not read as evidence about the assets (R-04)",
               "TLS confound not detected on a binary carrying /crypto/ and X509")
    finally:
        os.unlink(native)

    java = make_zip({
        "classes.dex": b"dex\n035\x00" + b"\x00" * 4096,
        "res/layout/main.xml": b"<xml/>",
        "AndroidManifest.xml": b"\x03\x00\x08\x00" + b"\x00" * 64,
    })
    try:
        r = fp.fingerprint(java)
        _check("V-MGWP-FP-JAVA-DIVERT",
               r["routing"]["decision"] == "JAVA_KOTLIN"
               and "android-reverse-engineering" in r["routing"]["next"],
               "a Java/Kotlin app is routed to android-reverse-engineering",
               f"routing={r['routing']['decision']}")
    finally:
        os.unlink(java)

    empty = make_zip({"assets/readme.txt": b"nothing here at all"})
    try:
        r = fp.fingerprint(empty)
        _check("V-MGWP-FP-UNKNOWN-REACHABLE",
               r["routing"]["decision"] == "UNKNOWN"
               and r["verdicts"]["Unity"]["verdict"] == "UNKNOWN",
               "with no native binary the answer is UNKNOWN, not ABSENT -- "
               "the refusal pole is reachable",
               f"routing={r['routing']['decision']} "
               f"unity={r['verdicts']['Unity']['verdict']}")
    finally:
        os.unlink(empty)


def gate_cipher_probe():
    cp = _load("cipher_probe")

    with tempfile.TemporaryDirectory() as d:
        paths = ciphertext_files(d, n=24, share_head=6)
        r = cp.probe(cp.collect(paths))
        _check("V-MGWP-CP-BLOCK16",
               r["block"]["verdict"] == "CONFIRMED" and r["block"]["block_size"] == 16,
               "24/24 sizes are a multiple of 16 -> block cipher, padded",
               f"{r['block']['verdict']} size={r['block']['block_size']}")
        _check("V-MGWP-CP-NOT-ECB", r["ecb"]["verdict"] == "NOT_ECB",
               "no intra-file block repeats -> ECB ruled out",
               f"ecb read {r['ecb']['verdict']}")
        _check("V-MGWP-CP-FIXED-IV",
               r["iv"]["verdict"] == "FIXED_KEY_AND_IV"
               and r["iv"]["largest_group"] == 6,
               "6 files share a first block -> no per-file IV, and the R-05 "
               "caveat is carried in the reason",
               f"iv read {r['iv']['verdict']}")
        _check("V-MGWP-CP-R05-CAVEAT", "R-05" in r["iv"]["why"],
               "the shared-prefix finding refuses to conclude CBC",
               "the fixed-IV reason does not carry the stream-cipher caveat")
        biggest = max(os.path.getsize(p) for p in paths)
        _check("V-MGWP-CP-SMALL-FILE-ENTROPY",
               r["header"]["verdict"] == "NO_SIGNATURE"
               and r["overall"]["verdict"] == "ENCRYPTED_BLOCK_CIPHER"
               and r["overall"]["algorithm"] == "UNKNOWN",
               f"files of at most {biggest} B still read as encrypted "
               f"({r['entropy']['mean_ratio_of_ceiling'] * 100:.1f}% of the "
               f"log2(n) ceiling, {r['entropy']['mean_bits_per_byte']} raw "
               f"bits) -- an absolute 7.5-bit threshold would have refused "
               f"them, and the real corpus is 144-256 B",
               f"header={r['header']['verdict']} overall={r['overall']['verdict']} "
               f"ratio={r['entropy']['mean_ratio_of_ceiling']}")

    with tempfile.TemporaryDirectory() as d:
        # Same sizes and the same block alignment, structured content. The
        # ratio must REFUSE these. Without this control, a threshold that
        # flagged everything would satisfy the assertion above and look like a
        # working detector.
        ctl = []
        for i in range(12):
            p = os.path.join(d, f"plain_{i:02d}.dat")
            with open(p, "wb") as fh:
                fh.write((f"level_{i:02d}_name=alpha_beta;".encode() * 16)[:176])
            ctl.append(p)
        r = cp.probe(cp.collect(ctl))
        _check("V-MGWP-CP-LOW-ENTROPY-CONTROL",
               r["overall"]["verdict"] == "UNKNOWN"
               and r["block"]["verdict"] == "CONFIRMED",
               f"block-aligned structured text of the same size is NOT called "
               f"encrypted ({r['entropy']['mean_ratio_of_ceiling'] * 100:.1f}% "
               f"of ceiling) -- the entropy test discriminates",
               f"overall={r['overall']['verdict']} "
               f"ratio={r['entropy']['mean_ratio_of_ceiling']}")

    with tempfile.TemporaryDirectory() as d:
        paths = ciphertext_files(d, n=12, repeat_block=True)
        r = cp.probe(cp.collect(paths))
        _check("V-MGWP-CP-ECB-DETECTED", r["ecb"]["verdict"] == "POSSIBLE_ECB",
               "a planted repeated block is detected as ECB-consistent",
               f"ecb read {r['ecb']['verdict']} on a file with a planted repeat")

    with tempfile.TemporaryDirectory() as d:
        paths = ciphertext_files(d, n=12, size_mult=False)
        r = cp.probe(cp.collect(paths))
        _check("V-MGWP-CP-NOT-BLOCK", r["block"]["verdict"] == "ABSENT",
               "sizes that are not a multiple of 16 refuse the block reading",
               f"block read {r['block']['verdict']} on unpadded sizes")

    with tempfile.TemporaryDirectory() as d:
        paths = ciphertext_files(d, n=12, share_head=0)
        r = cp.probe(cp.collect(paths))
        _check("V-MGWP-CP-DISTINCT-HEADS",
               r["iv"]["verdict"] == "PER_FILE_IV_OR_DISTINCT_HEADS",
               "all-distinct first blocks read as a per-file IV, not fixed",
               f"iv read {r['iv']['verdict']} with no shared heads")

    with tempfile.TemporaryDirectory() as d:
        paths = ciphertext_files(d, n=12, head_magic=b"\x1bLua")
        r = cp.probe(cp.collect(paths))
        _check("V-MGWP-CP-SIGNATURE",
               r["header"]["verdict"] == "SIGNATURE_PRESENT"
               and r["overall"]["verdict"] == "UNKNOWN",
               "a recognised magic stops it reading as raw ciphertext",
               f"header={r['header']['verdict']} overall={r['overall']['verdict']}")


def gate_envelope_probe():
    ep = _load("envelope_probe")
    payload = lua_chunk(num_size=4) + os.urandom(3000)

    blob = ep.ROVIO_LZMA_MAGIC + lzma.compress(payload, format=lzma.FORMAT_ALONE)
    r = ep.probe(blob)
    lzma_layer = next((l for l in r["layers"] if l.get("decoder")), None)
    lua_layer = next((l for l in r["layers"] if l.get("payload") == "Lua bytecode"), None)
    _check("V-MGWP-EP-LZMA-ROUNDTRIP",
           lzma_layer is not None and lzma_layer.get("ok")
           and lzma_layer.get("produced_size") == len(payload)
           and lzma_layer.get("declared_matches_produced"),
           f"magic + real LZMA-alone decodes to {len(payload):,} B, "
           f"declared size consistent",
           f"lzma layer = {lzma_layer}")
    _check("V-MGWP-EP-LZMA-PROPS",
           lzma_layer is not None and lzma_layer.get("lc") == 3
           and lzma_layer.get("lp") == 0 and lzma_layer.get("pb") == 2,
           f"props decode to lc=3 lp=0 pb=2 "
           f"(dict {lzma_layer.get('dictionary_bytes', 0):,} B)",
           f"props decoded as {lzma_layer}")
    _check("V-MGWP-EP-LUA-FLOAT32",
           lua_layer is not None and lua_layer["sizeof_lua_Number"] == 4
           and lua_layer["stock_header"] is False,
           "the float32 lua_Number build is read and flagged NON-STOCK -- "
           "the trap that makes stock tools reject every file",
           f"lua layer = {lua_layer}")

    stock = ep.ROVIO_LZMA_MAGIC + lzma.compress(
        lua_chunk(num_size=8) + os.urandom(500), format=lzma.FORMAT_ALONE)
    r2 = ep.probe(stock)
    lua2 = next((l for l in r2["layers"] if l.get("payload") == "Lua bytecode"), None)
    _check("V-MGWP-EP-LUA-STOCK",
           lua2 is not None and lua2["sizeof_lua_Number"] == 8
           and lua2["stock_header"] is True,
           "the stock double build reads as stock -- the control that proves "
           "the float32 gate is discriminating, not always-on",
           f"lua layer = {lua2}")

    corrupt = ep.ROVIO_LZMA_MAGIC + b"\x5d\x00\x00\x01\x00" + b"\xff" * 8 + os.urandom(64)
    r3 = ep.probe(corrupt)
    bad = next((l for l in r3["layers"] if l.get("decoder")), None)
    _check("V-MGWP-EP-LZMA-FAILS-LOUD",
           bad is not None and bad.get("ok") is False and "why" in bad,
           "a corrupt stream reports a named failure instead of a partial decode",
           f"corrupt stream produced {bad}")

    z = write_tmp(zlib.compress(b"A" * 5000))
    try:
        rz = ep.probe(open(z, "rb").read())
        zl = next((l for l in rz["layers"] if l.get("decoder") == "zlib"), None)
        _check("V-MGWP-EP-ZLIB",
               zl is not None and zl.get("ok") and zl.get("produced_size") == 5000,
               "a real zlib stream is identified and inflated to 5,000 B",
               f"zlib layer = {zl}")
    finally:
        os.unlink(z)

    plain = write_tmp(lua_chunk(num_size=4))
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(CORE, "envelope_probe.py"), plain],
            capture_output=True, text=True)
        _check("V-MGWP-EP-CLI",
               proc.returncode == 0 and "lua_Number" in proc.stdout,
               "the CLI path reports the header fields a tool choice depends on",
               f"rc={proc.returncode} out={proc.stdout.strip()[:160]!r}")
    finally:
        os.unlink(plain)

    proc = subprocess.run(
        [sys.executable, os.path.join(CORE, "envelope_probe.py"),
         os.path.join(SKILL, "does-not-exist.bin")],
        capture_output=True, text=True)
    _check("V-MGWP-EP-UNREADABLE",
           proc.returncode == 2 and "UNREADABLE_INPUT" in proc.stderr,
           "a missing input exits 2 as UNREADABLE_INPUT, distinct from a "
           "verdict about a subject",
           f"rc={proc.returncode} stderr={proc.stderr.strip()[:120]!r}")


def gate_doctrine():
    notice = os.path.join(SKILL, "NOTICE.md")
    retr = os.path.join(SKILL, "references", "retractions.md")
    ship = os.path.join(SKILL, "references", "wii-shipping.md")
    for path, name in ((notice, "NOTICE.md"), (retr, "retractions.md"),
                       (ship, "wii-shipping.md")):
        if not os.path.isfile(path):
            _fail(f"V-MGWP-DOC[{name}]", "absent")
            return
    # Collapse whitespace before matching. These documents are hard-wrapped, so
    # a substring assertion on raw text measures where the line breaks fell
    # rather than what the document says -- which is how this check first
    # failed against a NOTICE that stated the rule correctly.
    def _flat(s):
        return " ".join(s.split())

    ntext = _flat(open(notice, encoding="utf-8").read())
    rtext = _flat(open(retr, encoding="utf-8").read())
    stext = _flat(open(ship, encoding="utf-8").read())
    _check("V-MGWP-FIREWALL",
           "firewall" in ntext.lower() and "may not be committed" in ntext,
           "the asset firewall is stated in NOTICE.md",
           "NOTICE.md does not state the asset firewall")
    missing = [r for r in ("R-01", "R-02", "R-03", "R-04", "R-05", "R-06")
               if r not in rtext]
    _check("V-MGWP-RETRACTIONS", not missing,
           "all six retractions are carried with their root causes",
           f"retractions.md is missing {missing}")
    _check("V-MGWP-SHIPPING-HONEST",
           "UNPROVEN" in stext and "boot.dol" in stext,
           "the WBFS path is marked UNPROVEN beside the proven boot.dol path",
           "wii-shipping.md does not mark the disc-image path unproven")


def gate_real_corpus():
    corpus = os.environ.get("MGWP_REAL_CORPUS")
    if not corpus:
        _unmeas("V-MGWP-REAL-CORPUS",
                "set MGWP_REAL_CORPUS to a directory of real packed assets to "
                "run the probes against one; no corpus ships with this gate")
        return
    if not os.path.isdir(corpus):
        _fail("V-MGWP-REAL-CORPUS", f"MGWP_REAL_CORPUS={corpus} is not a directory")
        return
    cp = _load("cipher_probe")
    paths = []
    for dp, _d, fs in os.walk(corpus):
        paths.extend(os.path.join(dp, f) for f in fs)
    if not paths:
        _fail("V-MGWP-REAL-CORPUS", "corpus directory holds no files")
        return
    r = cp.probe(cp.collect(paths))
    _check("V-MGWP-REAL-CORPUS", r.get("files", 0) > 0,
           f"probed {r['files']} real files: block={r['block']['verdict']} "
           f"ecb={r['ecb']['verdict']} iv={r['iv']['verdict']}",
           "the probe returned nothing on a non-empty corpus")


def main() -> int:
    print("=== V-MGWP: mobile-game-wii-port absorption gate ===\n")
    print("[executability]")
    gate_executables()
    print("\n[phase 0 -- fingerprint]")
    gate_fingerprint()
    print("\n[phase 2 -- cipher probe]")
    gate_cipher_probe()
    print("\n[phase 3 -- envelope probe]")
    gate_envelope_probe()
    print("\n[doctrine carried]")
    gate_doctrine()
    print("\n[real input]")
    gate_real_corpus()

    total = _passes + _fails
    print(f"\nMGWP_PASS={_passes}/{total}  unmeasured={_unmeasured}  "
          f"threshold={total}/{total}")
    if _failed_names:
        print(f"FAILED GATES: {', '.join(_failed_names)}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
