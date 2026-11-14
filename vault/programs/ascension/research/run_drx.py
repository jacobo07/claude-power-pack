"""Run the six high-leverage certification questions through Deep Research X (modules/deep-research/deep_research.py), sequentially.

Why these six (Owner 2026-11-11, "hazlas todas con Deep Research X"): the certified KSR set is dominated by tiny functions (67% of the
8,687 are <= 16 B; 3,944 of 9,269 have no relocation). What is left is medium/large functions, decided by compiler build + flags,
library identity, codegen idioms, register allocation, types and TU boundaries. Each question must end in falsifiable predictions our
pinned mwcc + objdiff can check (web research gives E2-E3 hypotheses; only our compiler grants E4, recorded in verdicts.jsonl).

USD 0: DRX searches DuckDuckGo (free) and extracts with claude.exe -p on the Owner's subscription; no paid key is set. DRX holds a
single-instance lock, so a busy lock is waited out (bounded), never forced.
Usage: python run_drx.py [Q1 Q2 ...]   (default: every question without a finished run under drx-out/<Q>/)
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parents[3]
DRX = PP / "modules" / "deep-research" / "deep_research.py"
LOCK = PP / "vault" / "research" / ".deep-research.lock"
OUT = HERE / "drx-out"
PY = sys.executable
MODEL = os.environ.get("CLAUDEPP_RESEARCH_MODEL", "claude-sonnet-5-5")
LOCK_WAIT_S, LOCK_POLL_S = 3 * 3600, 120

CTX = ("A clean-room matching-decompilation engineer for Nintendo Wii games built with Metrowerks CodeWarrior (mwcceppc, PowerPC "
       "Broadway/Gekko), using decomp-toolkit (dtk), objdiff, m2c and decomp-permuter. A function counts only when the C compiles to "
       "byte-identical code AND data under a pinned mwcc. Actionable = a concrete rule, flag, idiom or signature that predicts a "
       "compiler output and can be tested by compiling with mwcc and diffing with objdiff. Never leaked Nintendo SDK code.")

TAIL = (" For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: "
        "'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.")

QUESTIONS = {
    "Q1": ("G28", "How do Wii/GameCube decompilation projects identify, from the binary alone, which Metrowerks CodeWarrior build "
           "(GC 1.x/2.x/3.x, Wii 1.0-1.7 etc.) and which compiler flags (-O4,p vs -O4,s, -inline auto/deferred, -fp_contract, "
           "-sdata/-sdata2 thresholds, -schedule, -use_lmw_stmw, -enum, -str pool/readonly, #pragma per function) compiled each "
           "translation unit? What codegen fingerprints (prologue/epilogue shape, lmw/stmw use, register save order, scheduling, "
           "float constant placement, string pooling) discriminate them, and how do dtk configs (configure.py, mw_version, cflags "
           "per object) record the answer?"),
    "Q2": ("G19", "Which libraries linked into Nintendo Wii games (RVL SDK: OS, GX, VI, PAD, WPAD, KPAD, DVD, NAND, AX, SC; NW4R: "
           "g3d, lyt, snd, ut, math, ef; EGG; MSL_C; Runtime.PPCEABI.H; MetroTRK; HomeButtonMenu) already have byte-matching "
           "clean-room reconstructions in public decompilation projects, at which exact library versions/build dates, under which "
           "licenses, and how do projects identify the library version inside a DOL (version strings, signatures, dtk signature "
           "files) so that matched sources can be reused only when the bytes are identical?"),
    "Q3": ("G26", "Which C source idioms make mwcceppc (CodeWarrior for PowerPC, GameCube/Wii) emit specific residual assembly "
           "patterns that block matching: swapped operand order, an extra or missing mr, clrlwi/rlwinm masks from char/short/bool "
           "casts, extsh/extsb, branch layout of if/else and ternaries, loop rotation and unrolling, switch jump tables vs compare "
           "chains, int<->float conversion sequences (0x43300000 magic, frsp, fctiwz), fmadds contraction, inline asm and volatile "
           "effects, and early-return vs single-exit? Collect documented source<->asm pairs from decomp projects, decomp.me "
           "scratches and the decomp community wiki."),
    "Q4": ("G29", "How does the Metrowerks CodeWarrior PowerPC compiler (mwcceppc, GameCube/Wii versions) allocate registers, and what "
           "source changes deterministically change the allocation (variable declaration order, first-use order, temporaries, "
           "scope blocks, inline functions, casts, struct copies, -O4,p vs -O4,s)? What do decompilation projects and "
           "decomp-permuter documentation say about fixing register swaps (regswaps) on mwcc, which permuter randomizations work "
           "for mwcc, and is there any documented model of its graph-coloring order?"),
    "Q5": ("G09", "How do GameCube/Wii decompilation projects build one whole-program type model (struct layouts, field types, "
           "pointer vs integer, function prototypes) shared across translation units, inferred from how the binary uses each value "
           "(load/store widths and offsets, call arguments, vtables), and how do they keep m2c output (which types unknown values "
           "as s32/long or ?) consistent across TUs: m2c --context, ctx.h generation, Ghidra/IDA type export, dtk symbols, and "
           "which errors (pointer expected, not a struct/union, illegal operands void*+int) disappear with a shared context?"),
    "Q6": ("G12", "How does decomp-toolkit (dtk) analyse a Wii/GameCube DOL/REL and decide translation-unit boundaries, link order, "
           "section splits (.text/.data/.rodata/.sdata/.sdata2/.bss/ctors/extab), and how do projects correct wrong auto splits "
           "(splits.txt, symbols.txt), detect that one auto object merges functions from different compilation units (string pool "
           "boundaries, padding, alignment, sdata usage, static function clustering), and recover the original file order?"),
    # Q7-Q12: capability bottlenecks still open on 2026-11-14 (Owner "haz DRX de mas cuellos de botella que tengamos de
    # capacidades", session 423c9c50). Measured context: KSR 9,678/30,388 certified; CNM 9,941, NO_COMPILE 5,453,
    # FLAGS_SPLIT 3,447, NO_TARGET 2,276; Tennis type routes P1-P1e refuted (compile without match).
    "Q7": ("B-CNM", "How do decompilation projects run automated source-variant search at scale for Metrowerks mwcc (GameCube/Wii): "
           "decomp-permuter's mwcc support and its known limits, PERM macros, randomization passes that actually change mwcc "
           "output, scoring functions and why a permuter score of 0 can still differ from byte identity, parallel/distributed "
           "runs, and any other tool (decomp.me scratch automation, AI-assisted search, symbolic rewriting) with published "
           "success rates on functions that already compile but do not match?"),
    "Q8": ("B-FLAGS", "How do GameCube/Wii projects recover per-translation-unit compiler flags and #pragmas when one game mixes "
           "objects built with different flags (e.g. -O4,p vs -O4,s, -inline, -sdata thresholds, optimize_for_size, scheduling "
           "off): which binary signals (literal pools, .sdata2 float constant duplication, string pool layout, alignment padding, "
           "sbss/sdata split, function ordering) predict a unit boundary or a flag change, and how is a flag hypothesis validated "
           "on units whose boundaries are already known?"),
    "Q9": ("B-NOTARGET", "When a function in a Wii/GameCube DOL or REL has no reference object to diff against (dead-stripped, inline "
           "or weak copies, template instantiations, functions merged by the linker, objects missing from the split), how do "
           "decompilation projects obtain the target bytes, attribute the function to a unit, and still prove a byte-identical "
           "match (dtk extraction, REL relocation handling, symbol maps, ctor/dtor and extab tables)?"),
    "Q10": ("B-CXX", "What blocks matching large C++ functions under mwcc for Wii (NW4R/EGG-style code): inlining decisions "
            "(-inline auto/deferred, inline depth), constructors/destructors, virtual tables and RTTI, exception tables "
            "(extab/extabindex), templates, member-pointer and copy-constructor code, and which documented source patterns make "
            "mwcc reproduce them byte for byte?"),
    "Q11": ("B-LINK", "How do GameCube/Wii projects go from many individually matching functions to a byte-identical whole DOL/REL: "
            "link order recovery, mwld vs GNU ld differences (relocation forms such as SDA21 addends), .data/.rodata/.sdata/.bss "
            "matching, alignment and padding, string and float pools, and how is 'fully matching' verified and reported (objdiff "
            "report, sha1 of the linked DOL, progress categories)?"),
    "Q12": ("B-COMPILER", "Do commercial Wii games link libraries built with different CodeWarrior versions (SDK, NW4R, MSL, game code), "
            "how do projects detect each object's compiler version and set it per object (configure.py mw_version per unit, "
            "compiler wrappers), and what evidence decides that a function matching only under a non-baseline compiler is a true "
            "match rather than a coincidence?"),
}


def finished(q: str) -> bool:
    return (OUT / q / "DONE.json").exists()


def wait_lock() -> bool:
    t0 = time.time()
    while LOCK.exists():
        if time.time() - t0 > LOCK_WAIT_S:
            return False
        time.sleep(LOCK_POLL_S)
    return True


def run(q: str) -> str:
    gap, text = QUESTIONS[q]
    d = OUT / q
    d.mkdir(parents=True, exist_ok=True)
    if not wait_lock():
        return f"{q}: LOCK_BUSY after {LOCK_WAIT_S}s - skipped, rerun later"
    env = dict(os.environ, CLAUDEPP_RESEARCH_MODEL=MODEL)
    cmd = [PY, "-I", str(DRX), "--prompt", text + TAIL, "--depth", "2", "--breadth", "4", "--operator-context", CTX, "--out", str(d)]
    t0 = time.time()
    with (d / "run.log").open("wb") as log:
        rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=env).returncode
    rec = {"q": q, "gap": gap, "rc": rc, "model": MODEL, "wall_s": round(time.time() - t0, 1),
           "artifacts": sorted(p.name for p in d.iterdir() if p.name not in ("run.log", "DONE.json"))}
    if rc == 0 and rec["artifacts"]:
        (d / "DONE.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return f"{q} ({gap}): rc={rc} {rec['wall_s']}s artifacts={rec['artifacts']}"


def main() -> int:
    want = sys.argv[1:] or sorted(QUESTIONS)
    todo = [q for q in want if not finished(q)]
    print(f"model={MODEL} todo={todo}", flush=True)
    for q in todo:
        print(run(q), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
