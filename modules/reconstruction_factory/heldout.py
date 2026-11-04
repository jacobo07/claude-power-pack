"""Held-out law. The sealed set is committed as hashes (heldout.seal.json); its sources live apart from the dev corpus and certify() refuses them until RELEASED.
A release is one-way and bound to a solver freeze: the solver hash is recorded at the FIRST release and any later release under a different hash is refused
(a solver edited after it saw held-out results is a different solver, so the number would not be held-out). The seal is re-verified at every release."""
import hashlib
import json
import os
import re

from . import certify as C


class HeldoutError(Exception):
    pass


def _sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def verify_seal(project):
    """-> list of problems; empty = the sealed set is exactly what was committed."""
    P = project
    sp = P.p(P.doc["corpus"]["heldout_seal"]) if P.doc["corpus"].get("heldout_seal") else None
    if not sp or not os.path.exists(sp):
        return ["NO_SEAL"]
    with open(sp) as fh:
        seal = json.load(fh)
    bad = []
    if seal.get("manifest_sha256") != _sha(P.path):
        bad.append("MANIFEST_CHANGED")
    sealed, declared = set(seal.get("functions", {})), set(P.names(heldout=True))
    for fn in sorted(sealed ^ declared):
        bad.append("MEMBERSHIP:" + fn)
    for fn in sorted(sealed & declared):
        p = P.source_path(fn)
        if not os.path.exists(p) or _sha(p) != seal["functions"][fn]:
            bad.append("SOURCE_CHANGED:" + fn)
    return bad


def leak_scan(project):
    """A held-out function must not appear (by name or by source file) anywhere in the dev-visible corpus: ref, skeleton, mutant, include dirs."""
    P, bad = project, []
    held = {fn: P.functions[fn] for fn in P.names(heldout=True)}
    dirs = [P.source_dir(k) for k in ("ref", "skeleton", "mutant") if P.doc["corpus"].get(k + "_dir")] + list(P.include_dirs)
    for d in dirs:
        for root, _, files in os.walk(d):
            for name in files:
                for fn, spec in held.items():
                    if name == spec["source"]:
                        bad.append("FILE:%s in %s" % (fn, os.path.relpath(root, P.root)))
                try:
                    with open(os.path.join(root, name), errors="ignore") as fh:
                        text = fh.read()
                except OSError:
                    continue
                for fn in held:
                    if re.search(r"\b%s\b" % re.escape(fn), text):
                        bad.append("NAME:%s in %s" % (fn, name))
    return sorted(set(bad))


def _load(ledger):
    if not os.path.exists(ledger):
        return {"solver_sha256": None, "released": {}}
    with open(ledger) as fh:
        return json.load(fh)


def release(project, ledger, fns, solver_sha256, reason):
    """Release `fns` for evaluation under the frozen solver. Refuses on a broken seal, an unknown/dev function, a missing freeze or reason, or a changed solver."""
    if not solver_sha256 or not re.fullmatch(r"[0-9a-f]{64}", solver_sha256) or not reason:
        raise HeldoutError("release needs a 64-hex solver freeze hash and a reason")
    prob = verify_seal(project)
    if prob:
        raise HeldoutError("seal broken: " + ",".join(prob))
    held = set(project.names(heldout=True))
    for fn in fns:
        if fn not in held:
            raise HeldoutError("%s is not a sealed held-out function" % fn)
    led = _load(ledger)
    if led["solver_sha256"] not in (None, solver_sha256):
        raise HeldoutError("solver changed after the first release: held-out numbers under a new solver are not held-out")
    led["solver_sha256"] = solver_sha256
    for fn in fns:
        led["released"].setdefault(fn, {"reason": reason})
    tmp = ledger + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(led, fh, indent=1, sort_keys=True)
    os.replace(tmp, ledger)
    return led


def is_released(ledger, fn):
    return fn in _load(ledger)["released"]


def certify_released(factory, fn, text, ledger):
    """The only door to a held-out certificate: certify() with released=True iff the ledger says so AND the seal still holds."""
    ok = is_released(ledger, fn) and not verify_seal(factory.project)
    return C.certify(factory, fn, text, released=ok)
