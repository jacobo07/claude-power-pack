#!/usr/bin/env python3
"""Founder authority: a signature, not a label.

Until this module, "founder" was a string any caller could pass as ``actor``,
and the autonomy licence was a plain JSON file in the state directory. The
goal log's hash chain is keyless, so any principal able to write the goal
directory could append a founder event, re-chain history wholesale, or forge
the licence -- and a resident process that writes the store could therefore
grant itself autonomy and authority. (Spec: vault/specs/gdd-founder-authority.md.)

Founder-class events now carry an Ed25519 signature by a key the resident
cannot read, and the signature is checked on PROJECTION, not only on append:
the files can be written without going through this API.

Four modes, decided by the trust anchor named by ``GSDX_FOUNDER_KEYS``:

  * ABSENT       -- the variable is unset. Legacy behaviour, reported as
                    "founder authority unverified". Unsetting it is the rollback.
  * UNPROTECTED  -- the anchor is readable and valid but writable by this
                    process (POSIX ``os.access(W_OK)``, or any file on Windows):
                    signatures are checked, the anchor is not a boundary.
  * ENFORCED     -- readable, valid, and not writable by this process.
  * UNVERIFIABLE -- the variable names an anchor that cannot be used: the
                    crypto library is missing, or the file is absent, unreadable
                    or malformed. The resident refuses; this is never a pass.

A variable naming a file that does not exist is UNVERIFIABLE, not ABSENT: an
operator declared an anchor, and deleting it must not downgrade the goal store
to legacy behaviour.

No secret material is ever printed, logged or placed in an error message. A
key_id is a short sha256 of the PUBLIC key's raw bytes.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .log import GoalLogCorrupt, GoalLogError, _canonical

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    CRYPTO_ERROR = ""
except ImportError as _exc:                      # reported as UNVERIFIABLE, never a pass
    CRYPTO_ERROR = f"the cryptography library is not importable ({_exc})"

ENV_ANCHOR = "GSDX_FOUNDER_KEYS"
ENV_FOUNDER_KEY = "GSDX_FOUNDER_SIGNING_KEY"
ENV_JUDGE_KEY = "GSDX_JUDGE_SIGNING_KEY"

ABSENT = "ABSENT"
UNPROTECTED = "UNPROTECTED"
ENFORCED = "ENFORCED"
UNVERIFIABLE = "UNVERIFIABLE"
CHECKING_MODES = (UNPROTECTED, ENFORCED)

FOUNDER = "founder"
JUDGE = "judge"
ROLES = (FOUNDER, JUDGE)

SIG_FIELD = "_founder"          # inside an event's data
LICENCE_SIG_FIELD = "_judge"    # inside the autonomy record

# The event types only the Founder may write. Kept as literals here (not
# imported from contract/sweep, which import this module); the authority suite
# asserts this set equals the constants those modules declare.
FOUNDER_CLASS = frozenset({
    "goal.declared", "goal.revised", "goal.budget_set", "goal.authority_set",
    "goal.autonomous", "goal.paused", "goal.resumed", "goal.tier_set",
    "goal.decision_answered", "goal.adopted",
})

# Refusal reasons, named so a reader (and a test) can tell them apart.
FOUNDER_SIGNATURE_INVALID = "FOUNDER_SIGNATURE_INVALID"
FOUNDER_SIGNATURE_MISSING = "FOUNDER_SIGNATURE_MISSING"
JUDGE_SIGNATURE_MISSING = "JUDGE_SIGNATURE_MISSING"
UNKNOWN_KEY = "UNKNOWN_KEY"
WRONG_ROLE = "WRONG_ROLE"
BAD_SIGNATURE = "BAD_SIGNATURE"
MALFORMED_SIGNATURE = "MALFORMED_SIGNATURE"


class AuthorityError(GoalLogError):
    """Base for founder-authority refusals."""


class SigningKeyUnavailable(AuthorityError):
    """A founder-class write was asked for and no usable signing key exists."""


class AuthorityUnverifiable(AuthorityError):
    """The anchor is declared but cannot be used; nothing may be signed or trusted."""


class AuthorityAbsent(AuthorityError):
    """An operation that only means something under an anchor was asked for without one."""


@dataclass
class Anchor:
    mode: str
    path: str = ""
    detail: str = ""
    keys: dict = field(default_factory=dict)     # key_id -> (role, Ed25519PublicKey)


def key_id_of(public_raw: bytes) -> str:
    return hashlib.sha256(public_raw).hexdigest()[:16]


def _anchor_writable(path: Path) -> bool:
    if os.name == "nt":
        # NTFS ACLs are not what os.access reports; a Windows anchor is never
        # claimed as a boundary.
        return True
    # The DIRECTORY counts too: a read-only anchor in a directory the reader can
    # write is replaceable (unlink + write a new file), so it is not a boundary.
    parent = Path(os.path.realpath(path)).parent
    return os.access(path, os.W_OK) or os.access(parent, os.W_OK)


def load_anchor() -> Anchor:
    """Read the trust anchor named by the environment, and classify it."""
    raw_path = os.environ.get(ENV_ANCHOR, "").strip()
    if not raw_path:
        return Anchor(ABSENT, detail=f"{ENV_ANCHOR} is not set")
    path = Path(raw_path)
    if CRYPTO_ERROR:
        return Anchor(UNVERIFIABLE, str(path), CRYPTO_ERROR)
    if not path.is_file():
        return Anchor(UNVERIFIABLE, str(path), "ANCHOR_MISSING: the named anchor does not exist")
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return Anchor(UNVERIFIABLE, str(path), f"ANCHOR_UNREADABLE: {exc.__class__.__name__}")
    if not isinstance(doc, dict) or not doc:
        return Anchor(UNVERIFIABLE, str(path), "ANCHOR_MALFORMED: expected a non-empty object")
    keys = {}
    for kid, entry in doc.items():
        if not isinstance(entry, dict) or entry.get("role") not in ROLES:
            return Anchor(UNVERIFIABLE, str(path), f"ANCHOR_MALFORMED: entry {kid!r} has no valid role")
        try:
            raw = base64.b64decode(str(entry.get("public_key", "")), validate=True)
            pub = Ed25519PublicKey.from_public_bytes(raw)
        except (ValueError, TypeError) as exc:
            return Anchor(UNVERIFIABLE, str(path),
                          f"ANCHOR_MALFORMED: entry {kid!r} public key unusable ({exc.__class__.__name__})")
        if key_id_of(raw) != kid:
            return Anchor(UNVERIFIABLE, str(path),
                          f"ANCHOR_MALFORMED: entry {kid!r} is not the hash of its public key")
        keys[kid] = (entry["role"], pub)
    mode = UNPROTECTED if _anchor_writable(path) else ENFORCED
    return Anchor(mode, str(path), "", keys)


def describe(anchor: Anchor) -> str:
    if anchor.mode == ABSENT:
        return "founder authority unverified (no anchor: legacy behaviour)"
    if anchor.mode == UNVERIFIABLE:
        return f"founder authority UNVERIFIABLE at {anchor.path}: {anchor.detail}"
    if anchor.mode == UNPROTECTED:
        return (f"founder authority UNPROTECTED: signatures are checked, but the anchor at "
                f"{anchor.path} is writable by this process, so it is not a boundary")
    return f"founder authority ENFORCED: anchor {anchor.path} is not writable by this process"


def event_message(repo: str, goal: str, seq: int, type_: str, data: dict,
                  prev_digest: str) -> bytes:
    body = {k: v for k, v in (data or {}).items() if k != SIG_FIELD}
    return _canonical({"repo": repo, "goal": goal, "seq": int(seq), "type": type_,
                       "data": body, "prev_digest": prev_digest})


def _load_private(env_name: str, anchor: Anchor, role: str):
    if anchor.mode == UNVERIFIABLE:
        raise AuthorityUnverifiable(describe(anchor))
    key_path = os.environ.get(env_name, "").strip()
    if not key_path:
        raise SigningKeyUnavailable(f"{env_name} is not set: a {role}-class write needs the "
                                    f"{role} signing key")
    try:
        data = Path(key_path).read_bytes()
        key = serialization.load_pem_private_key(data, password=None)
    except (OSError, ValueError, TypeError) as exc:
        raise SigningKeyUnavailable(f"{env_name} names a key that cannot be loaded "
                                    f"({exc.__class__.__name__})") from None
    if not isinstance(key, Ed25519PrivateKey):
        raise SigningKeyUnavailable(f"{env_name} is not an Ed25519 key")
    raw = key.public_key().public_bytes(serialization.Encoding.Raw,
                                        serialization.PublicFormat.Raw)
    kid = key_id_of(raw)
    known = anchor.keys.get(kid)
    if known is None:
        raise SigningKeyUnavailable(f"{env_name} key {kid} is not in the anchor: what it "
                                    "signed would be refused on projection")
    if known[0] != role:
        raise SigningKeyUnavailable(f"{env_name} key {kid} is a {known[0]} key, not {role}")
    return kid, key


def sign_event_data(anchor: Anchor, repo: str, goal: str, seq: int, type_: str,
                    data: dict, prev_digest: str) -> dict:
    """The event's data with a founder signature attached, or raise."""
    kid, key = _load_private(ENV_FOUNDER_KEY, anchor, FOUNDER)
    body = {k: v for k, v in (data or {}).items() if k != SIG_FIELD}
    sig = key.sign(event_message(repo, goal, seq, type_, body, prev_digest))
    body[SIG_FIELD] = {"key_id": kid, "sig": base64.b64encode(sig).decode("ascii")}
    return body


def _check(anchor: Anchor, block, message: bytes, role: str) -> tuple[bool, str]:
    if not isinstance(block, dict):
        return False, FOUNDER_SIGNATURE_MISSING if role == FOUNDER else JUDGE_SIGNATURE_MISSING
    kid, sig_b64 = block.get("key_id"), block.get("sig")
    if not isinstance(kid, str) or not isinstance(sig_b64, str):
        return False, MALFORMED_SIGNATURE
    known = anchor.keys.get(kid)
    if known is None:
        return False, UNKNOWN_KEY
    if known[0] != role:
        return False, WRONG_ROLE
    try:
        known[1].verify(base64.b64decode(sig_b64, validate=True), message)
    except (InvalidSignature, ValueError, TypeError):
        return False, BAD_SIGNATURE
    return True, kid


def verify_event(anchor: Anchor, repo: str, goal: str, ev) -> tuple[bool, str]:
    """Is this founder-class event validly signed by a founder-role key?"""
    msg = event_message(repo, goal, ev.seq, ev.type, ev.data, ev.prev_digest)
    return _check(anchor, (ev.data or {}).get(SIG_FIELD), msg, FOUNDER)


def check_founder_chain(anchor: Anchor, repo: str, goal: str, events) -> int:
    """Raise unless the founder events obey spec section 4. Returns the first
    validly signed seq (0 when the goal is ungoverned).

    A founder-class event that CARRIES a signature block must verify wherever it
    sits: legacy events never carry one, so an invalid block before governance
    is either forgery or a re-chained history whose signed event no longer
    matches its predecessor -- exactly the rewrite this exists to catch.
    """
    if anchor.mode not in CHECKING_MODES:
        return 0
    first = 0
    for ev in events:
        if ev.type not in FOUNDER_CLASS:
            continue
        carries = SIG_FIELD in (ev.data or {})
        ok, why = verify_event(anchor, repo, goal, ev)
        if ok:
            first = first or ev.seq
            continue
        if first or carries:
            raise GoalLogCorrupt(f"{goal} seq {ev.seq}: {FOUNDER_SIGNATURE_INVALID} "
                                 f"({ev.type}: {why})")
    return first


def is_governed(state, anchor: Anchor | None = None) -> bool:
    """At least one validly signed founder event, under an anchor that checks."""
    anchor = anchor or load_anchor()
    if anchor.mode not in CHECKING_MODES:
        return False
    return any(ev.type in FOUNDER_CLASS and verify_event(anchor, state.repo, state.goal_id, ev)[0]
               for ev in state.events)


def sign_licence(payload: dict, anchor: Anchor) -> dict:
    kid, key = _load_private(ENV_JUDGE_KEY, anchor, JUDGE)
    body = {k: v for k, v in payload.items() if k != LICENCE_SIG_FIELD}
    sig = key.sign(_canonical(body))
    body[LICENCE_SIG_FIELD] = {"key_id": kid, "sig": base64.b64encode(sig).decode("ascii")}
    return body


def verify_licence(payload: dict, anchor: Anchor) -> tuple[bool, str]:
    body = {k: v for k, v in payload.items() if k != LICENCE_SIG_FIELD}
    return _check(anchor, payload.get(LICENCE_SIG_FIELD), _canonical(body), JUDGE)


def generate_keypair(out: Path, role: str) -> tuple[str, dict]:
    """Write a new Ed25519 private key to ``out`` and return (key_id, anchor entry).

    The private PEM is created exclusively with mode 0600 where the OS honours
    it; an existing file is never overwritten. Only the PUBLIC half is returned.
    """
    if CRYPTO_ERROR:
        raise AuthorityUnverifiable(CRYPTO_ERROR)
    if role not in ROLES:
        raise AuthorityError(f"role must be one of {ROLES}, not {role!r}")
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption())
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                     0o600)
    except FileExistsError:
        raise AuthorityError(f"{out} already exists; a key is never overwritten") from None
    with os.fdopen(fd, "wb") as fh:
        fh.write(pem)
    raw = key.public_key().public_bytes(serialization.Encoding.Raw,
                                        serialization.PublicFormat.Raw)
    kid = key_id_of(raw)
    return kid, {kid: {"role": role, "public_key": base64.b64encode(raw).decode("ascii")}}
