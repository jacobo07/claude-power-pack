#!/usr/bin/env python3
"""rehydration.py -- FASE A rehydration verifier (the G4 gate for waking a pane).

The kclaude wrapper performs the mechanical ``--resume``; this module answers the
acceptance question CO-07 + G4 pose: did the pane come back as the SAME session?

It restores the CO-07 archive (integrity re-check + resume-anchor re-check ->
RECOVERED / PARTIAL / FAILED) and ADDITIONALLY asserts the restored session id
equals the one we resumed. Any verdict other than RECOVERED is surfaced with its
missing dimensions, never silently accepted (Reality Contract / kernel vMAX-NULL-
ERROR): a rehydration that "returned" is not a recovery until the anchor + the
identity both check out.

This is pure composition over hibernation.restore() -- no new persistence, no
process access. Deterministic + unit-testable end to end with a real archive.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

RECOVERED = "RECOVERED"
PARTIAL = "PARTIAL"
FAILED = "FAILED"


@dataclass
class RehydrationVerdict:
    verdict: str                   # RECOVERED | PARTIAL | FAILED
    reason: str
    sid: str | None = None         # the session id actually restored
    missing: list = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return self.verdict == RECOVERED


def verify_rehydration(archive_id: str, expected_sid: str | None, *,
                       registry_path=None, proj_base=None,
                       restore_fn=None, anchor_exists_fn=None
                       ) -> RehydrationVerdict:
    """Restore the CO-07 archive and confirm the woken session's identity.

    RECOVERED  -- archive integrity + anchor intact AND restored sid == expected.
    PARTIAL    -- anchor intact + identity OK but a host dimension (e.g. cwd) is
                  gone; surfaced, not failed.
    FAILED     -- archive corrupt / anchor gone / restored sid != resumed sid.
    """
    if restore_fn is None:
        from modules.cognitive_os import hibernation
        restore_fn = hibernation.restore
    rr = restore_fn(archive_id, registry_path=registry_path, proj_base=proj_base,
                    anchor_exists_fn=anchor_exists_fn)

    if rr.verdict == FAILED:
        return RehydrationVerdict(FAILED, rr.reason, None, list(rr.missing or []))

    restored_sid = (rr.state or {}).get("sid")
    # Identity gate: a woken pane that is a DIFFERENT session is a failed recovery,
    # even if the archive itself was intact (never resume the wrong conversation).
    if expected_sid and restored_sid != expected_sid:
        return RehydrationVerdict(
            FAILED,
            f"session identity mismatch: restored '{restored_sid}' != "
            f"resumed '{expected_sid}'",
            restored_sid, ["identity"])

    if rr.verdict == PARTIAL:
        return RehydrationVerdict(PARTIAL, rr.reason, restored_sid,
                                  list(rr.missing or []))
    return RehydrationVerdict(RECOVERED, "anchor intact + identity verified",
                              restored_sid)


def main(argv=None) -> int:  # pragma: no cover - thin CLI
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--archive-id", required=True)
    ap.add_argument("--expect-sid", default=None)
    ap.add_argument("--registry", default=None)
    args = ap.parse_args(argv)
    v = verify_rehydration(args.archive_id, args.expect_sid,
                           registry_path=args.registry)
    print(f"{v.verdict}: {v.reason} (sid={v.sid})")
    return 0 if v.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
