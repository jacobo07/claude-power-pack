#!/usr/bin/env python3
"""USEA canonical-corpus integrity gate.

The Universal Software Engineering Architect constitution is immutable source
material under an exactness contract: derived representations may exist, but the
canonical copy must stay recoverable and must not drift silently.

This gate is the mechanism for that contract. It seals the corpus under a
SHA-256 and verifies, on demand, that:

  * the file is present and readable,
  * its opening and closing anchors still match the constitutional contract,
  * its bytes still hash to the sealed value.

Four outcomes, not two
----------------------
A verifier that rejected its subject and a verifier that could not judge its
subject are different evidence, and a crash that exits non-zero reads as a
rejection while proving nothing. So every run resolves to exactly one of:

  VALID            exit 0   corpus matches the seal
  SUBJECT_INVALID  exit 1   corpus is present and readable, and has drifted
  UNREADABLE       exit 3   corpus or seal is missing / undecodable
  GATE_FAILED      exit 4   the gate itself failed; the corpus was NOT judged

GATE_FAILED outranks SUBJECT_INVALID: a run that broke has not established
anything about what it did not reach.

Usage
-----
    python tools/usea_corpus_gate.py --seal      # record the current hash
    python tools/usea_corpus_gate.py --verify    # check against the seal
    python tools/usea_corpus_gate.py --self-test # drive the red branches
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# --- Constitutional anchors (contract, section 3) --------------------------
# The canonical payload begins and ends with these exact strings. They are the
# structural identity of the corpus: a file that hashes correctly but no longer
# opens with the constitutional title is not the constitution.
ANCHOR_HEAD = "# UNIVERSAL SOFTWARE ENGINEERING ARCHITECT"
ANCHOR_TAIL = (
    "**RECONSTRUCT REALITY → UNDERSTAND CAUSALITY → IMPLEMENT MINIMALLY "
    "→ VERIFY EMPIRICALLY → GENERALIZE ONLY WHEN PROVEN.**"
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO_ROOT / "vault" / "constitution" / "usea"
CORPUS_PATH = CORPUS_DIR / "constitution.raw.md"
SEAL_PATH = CORPUS_DIR / "seal.json"

VALID = "VALID"
SUBJECT_INVALID = "SUBJECT_INVALID"
UNREADABLE = "UNREADABLE"
GATE_FAILED = "GATE_FAILED"

EXIT_CODES = {VALID: 0, SUBJECT_INVALID: 1, UNREADABLE: 3, GATE_FAILED: 4}


@dataclass
class Verdict:
    outcome: str
    findings: list[str]

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.outcome]


def sha256_of(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_corpus(path: Path) -> tuple[bytes, str] | None:
    """Return (raw_bytes, decoded_text), or None when unreadable.

    Read as bytes first: the hash is over bytes, and decoding is a separate
    fallible step. 'utf-8-sig' because Windows tooling emits a BOM and a BOM
    that survives into the text would corrupt the head-anchor comparison.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    try:
        return raw, raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def check_anchors(text: str) -> list[str]:
    findings: list[str] = []
    stripped = text.strip()
    if not stripped.startswith(ANCHOR_HEAD):
        findings.append(
            f"head anchor absent: corpus does not open with {ANCHOR_HEAD!r}"
        )
    if not stripped.endswith(ANCHOR_TAIL):
        findings.append(
            "tail anchor absent: corpus does not close with the "
            "RECONSTRUCT REALITY operating command"
        )
    return findings


def verify(corpus_path: Path = CORPUS_PATH, seal_path: Path = SEAL_PATH) -> Verdict:
    """Judge the corpus against its seal. Never raises for subject problems."""
    try:
        loaded = read_corpus(corpus_path)
        if loaded is None:
            return Verdict(UNREADABLE, [f"corpus unreadable at {corpus_path}"])
        raw, text = loaded

        try:
            seal = json.loads(seal_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            return Verdict(UNREADABLE, [f"seal unreadable at {seal_path}: {exc}"])

        sealed_hash = seal.get("sha256")
        if not sealed_hash:
            return Verdict(UNREADABLE, ["seal carries no sha256 field"])

        findings = check_anchors(text)

        actual = sha256_of(raw)
        if actual != sealed_hash:
            findings.append(
                f"hash drift: sealed {sealed_hash[:16]}... != actual {actual[:16]}..."
            )

        if findings:
            return Verdict(SUBJECT_INVALID, findings)
        return Verdict(VALID, [])
    except Exception as exc:  # noqa: BLE001 - the gate's own failure branch
        # The gate broke. It has NOT judged the corpus, and must not be read as
        # having rejected it.
        return Verdict(GATE_FAILED, [f"{type(exc).__name__}: {exc}"])


def seal(corpus_path: Path = CORPUS_PATH, seal_path: Path = SEAL_PATH) -> Verdict:
    loaded = read_corpus(corpus_path)
    if loaded is None:
        return Verdict(UNREADABLE, [f"corpus unreadable at {corpus_path}"])
    raw, text = loaded

    anchor_findings = check_anchors(text)
    if anchor_findings:
        # Refuse to seal a payload that is not the constitution. Sealing it
        # would make a wrong file authoritative and every later verify would
        # cheerfully confirm the wrong thing.
        return Verdict(SUBJECT_INVALID, anchor_findings)

    payload = {
        "sha256": sha256_of(raw),
        "bytes": len(raw),
        "chars": len(text),
        "anchor_head": ANCHOR_HEAD,
        "anchor_tail_tail40": ANCHOR_TAIL[-40:],
        "fidelity": "INFERRED",
        "fidelity_note": (
            "Transport collapsed the payload's line structure; words and order "
            "are intact, whitespace is not proven identical to the Owner's "
            "source. See PROVENANCE.md. Upgrade to PROVEN only by replacing "
            "this file with the Owner's original bytes and re-sealing."
        ),
    }
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return Verdict(VALID, [f"sealed {payload['bytes']} bytes -> {payload['sha256']}"])


def self_test() -> int:
    """Positive control: drive every red branch.

    A gate whose failure path nobody exercised could have every clause removed
    and return the same green. These cases prove each outcome is reachable.
    """
    passes, fails = 0, 0

    def check(gate_id: str, condition: bool, evidence: str) -> None:
        nonlocal passes, fails
        if condition:
            passes += 1
            print(f"  OK   {gate_id}  {evidence}")
        else:
            fails += 1
            print(f"  FAIL {gate_id}  {evidence}")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        good = tmp / "good.md"
        good_seal = tmp / "good.json"
        body = f"{ANCHOR_HEAD}\nbody text\n{ANCHOR_TAIL}"
        good.write_text(body, encoding="utf-8")

        v = seal(good, good_seal)
        check("V-USEA-SEAL", v.outcome == VALID, f"seal of well-formed corpus -> {v.outcome}")

        v = verify(good, good_seal)
        check("V-USEA-VALID", v.outcome == VALID, f"unmodified corpus -> {v.outcome}")

        # RED 1: content drift
        good.write_text(body.replace("body text", "tampered"), encoding="utf-8")
        v = verify(good, good_seal)
        check(
            "V-USEA-DRIFT",
            v.outcome == SUBJECT_INVALID and any("hash drift" in f for f in v.findings),
            f"tampered corpus -> {v.outcome}",
        )

        # RED 2: anchor loss (a truncated corpus that someone re-sealed)
        bad = tmp / "bad.md"
        bad.write_text("# SOMETHING ELSE\nnot the constitution", encoding="utf-8")
        v = seal(bad, tmp / "bad.json")
        check(
            "V-USEA-ANCHOR",
            v.outcome == SUBJECT_INVALID and len(v.findings) == 2,
            f"non-constitution refused at seal time -> {v.outcome} ({len(v.findings)} anchors)",
        )

        # RED 3: unreadable subject
        v = verify(tmp / "absent.md", good_seal)
        check("V-USEA-UNREADABLE", v.outcome == UNREADABLE, f"missing corpus -> {v.outcome}")

        # RED 4: missing seal is UNREADABLE, never a rejection of the corpus
        v = verify(good, tmp / "absent.json")
        check("V-USEA-NOSEAL", v.outcome == UNREADABLE, f"missing seal -> {v.outcome}")

        # RED 5: the gate's own failure branch must outrank a subject verdict.
        # Drive it with a path object whose read raises something the subject
        # branches do not anticipate.
        class Exploding:
            def read_bytes(self):
                raise RuntimeError("simulated gate fault")

            def __str__(self):
                return "<exploding>"

        v = verify(Exploding(), good_seal)  # type: ignore[arg-type]
        check(
            "V-USEA-GATEFAIL",
            v.outcome == GATE_FAILED,
            f"gate fault -> {v.outcome} (must not read as SUBJECT_INVALID)",
        )

        # Ordering claim: the four outcomes carry distinct exit codes.
        codes = {EXIT_CODES[o] for o in (VALID, SUBJECT_INVALID, UNREADABLE, GATE_FAILED)}
        check("V-USEA-EXITCODES", len(codes) == 4, f"distinct exit codes: {sorted(codes)}")

    print(f"USEA_CORPUS_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="USEA canonical-corpus integrity gate")
    ap.add_argument("--seal", action="store_true", help="record the current hash")
    ap.add_argument("--verify", action="store_true", help="check against the seal")
    ap.add_argument("--self-test", action="store_true", help="drive the red branches")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    verdict = seal() if args.seal else verify()
    action = "SEAL" if args.seal else "VERIFY"
    print(f"USEA {action}: {verdict.outcome}")
    for f in verdict.findings:
        print(f"  - {f}")
    if verdict.outcome == GATE_FAILED:
        print("  NOTE: the gate failed; the corpus was NOT judged.")
    return verdict.exit_code


if __name__ == "__main__":
    sys.exit(main())
