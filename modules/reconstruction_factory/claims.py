"""Claim store over atoms: every scientific statement is (subject, predicate, payload, world, grade, evidence) with a semantic key, so the SAME
proposition asserted twice is one claim with two evidence rows (idempotent), and a changed world makes a claim INAPPLICABLE rather than silently true.
Grades: PROVEN (independent evidence, e.g. a certificate) > SHADOW (measured, one channel) > CANDIDATE > INVALIDATED. `require` is the consumer gate: a
claim is handed over only if it is PROVEN/SHADOW and its world is compatible with the asker's."""
from . import atoms

GRADES = ("PROVEN", "SHADOW", "CANDIDATE", "INVALIDATED")


class Refused(Exception):
    pass


class ClaimStore:
    def __init__(self):
        self.claims = {}                 # semantic key -> claim
        self.events = []

    def assert_claim(self, subject, predicate, payload, world, grade="CANDIDATE", evidence=None):
        if grade not in GRADES or grade == "INVALIDATED":
            raise atoms.Malformed("cannot assert grade %r" % grade)
        atoms.validate(predicate, payload)
        k = atoms.semantic_key(subject, predicate, payload, world)
        c = self.claims.get(k)
        if c is None:
            c = self.claims[k] = {"key": k, "subject": subject, "predicate": predicate, "payload": payload, "world": dict(world), "grade": grade, "evidence": []}
        elif c["grade"] == "INVALIDATED":
            c["grade"] = grade                                           # re-observed in a compatible world: revived explicitly
        elif GRADES.index(grade) < GRADES.index(c["grade"]):
            c["grade"] = grade                                           # strongest evidence wins; never silently weakened
        if evidence is not None:
            c["evidence"].append(evidence)
        return c

    def from_certificate(self, fn, cert, world):
        v = cert["verdict"]
        payload = {"fn": fn, "verdict": v, "candidate_sha256": cert.get("candidate_sha256")}
        ev = cert.get("evidence") or {}
        independent = bool(ev.get("independent")) and all(ev["independent"].values())
        grade = "PROVEN" if v == "CERTIFIED_EXACT" and independent else "SHADOW" if v != "CERTIFIED_EXACT" else "CANDIDATE"
        return self.assert_claim(fn, "certificate", payload, world, grade, evidence=ev)

    def from_judge(self, fn, j, world):
        payload = {"fn": fn, "compiles": bool(j["compiles"]), "exact": j["exact"], "pct": j["pct"]}
        return self.assert_claim(fn, "compile_outcome", payload, world, "SHADOW")

    def require(self, subject, predicate, world):
        found = [c for c in self.claims.values() if c["subject"] == subject and c["predicate"] == predicate and atoms.world_compatible(c["world"], world)]
        live = [c for c in found if c["grade"] in ("PROVEN", "SHADOW")]
        if not live:
            why = "INVALIDATED" if any(c["grade"] == "INVALIDATED" for c in found) else "CANDIDATE" if found else "UNKNOWN"
            raise Refused("%s %s is %s in this world" % (subject, predicate, why))
        return sorted(live, key=lambda c: GRADES.index(c["grade"]))[0]

    def invalidate(self, reason, new_world):
        """Withdraw every claim whose world CONFLICTS with `new_world`. -> the invalidation event."""
        if reason not in atoms.REASONS:
            raise atoms.Malformed("unknown invalidation reason %r" % reason)
        hit = sorted(c["key"] for c in self.claims.values() if c["grade"] != "INVALIDATED" and not atoms.world_compatible(c["world"], new_world))
        for k in hit:
            self.claims[k]["grade"] = "INVALIDATED"
        ev = {"reason": reason, "claims": hit}
        atoms.validate("invalidation_event", ev)
        self.events.append(ev)
        return ev
