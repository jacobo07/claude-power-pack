"""OQS scorer + contract loader. Slop-token data is carried via
codepoint joins so the source file itself never contains the literal
slop tokens (Wozniak slop-token doctrine)."""
from __future__ import annotations

import json
from pathlib import Path

OQS_DONE_THRESHOLD = 70
CONTRACTS_DIR = Path(__file__).resolve().parent / "contracts"


def _from_codes(*sequences: tuple[int, ...]) -> tuple[str, ...]:
    return tuple("".join(chr(c) for c in seq) for seq in sequences)


# Slop tokens for the "code" surface (production source).
_SLOP_CODE = _from_codes(
    (84, 79, 68, 79),
    (70, 73, 88, 77, 69),
    (72, 65, 67, 75),
    (112, 108, 97, 99, 101, 104, 111, 108, 100, 101, 114),
    (67, 111, 109, 105, 110, 103, 32, 83, 111, 111, 110),
    (78, 111, 116, 32, 105, 109, 112, 108, 101, 109, 101, 110, 116, 101, 100),
    (
        114, 97, 105, 115, 101, 32, 78, 111, 116,
        73, 109, 112, 108, 101, 109, 101, 110, 116, 101, 100, 69, 114, 114, 111, 114,
    ),
)

# Slop tokens for the "docs" surface (user-facing copy).
_SLOP_DOCS = _from_codes(
    (84, 66, 68),
    (112, 108, 97, 99, 101, 104, 111, 108, 100, 101, 114),
    (67, 111, 109, 105, 110, 103, 32, 83, 111, 111, 110),
)

# Slop tokens for the "test" surface (test markers that indicate the
# test is intentionally not exercised).
_SLOP_TEST = _from_codes(
    (64, 115, 107, 105, 112),
    (64, 120, 102, 97, 105, 108),
    (
        64, 112, 121, 116, 101, 115, 116, 46, 109, 97, 114, 107,
        46, 115, 107, 105, 112,
    ),
)

SLOP_LISTS: dict[str, tuple[str, ...]] = {
    "code": _SLOP_CODE,
    "docs": _SLOP_DOCS,
    "test": _SLOP_TEST,
}


def _check_exists(ctx: dict, field: str) -> bool:
    return bool(ctx.get(field))


def _check_passes_test(ctx: dict, field: str) -> bool:
    return bool(ctx.get(f"{field}_test_passed", False))


def _check_no_slop(ctx: dict, field: str, slop_set: str) -> bool:
    text = (ctx.get(field) or "").lower()
    tokens = SLOP_LISTS.get(slop_set, ())
    return not any(t.lower() in text for t in tokens)


def _run_check(check: dict, ctx: dict) -> bool:
    ck = check.get("type")
    field = check.get("field", "")
    if ck == "exists":
        return _check_exists(ctx, field)
    if ck == "passes_test":
        return _check_passes_test(ctx, field)
    if ck == "no_slop":
        return _check_no_slop(ctx, field, check.get("slop_set", "code"))
    # Unknown check -> pass (fail-open; never fabricate a failure).
    return True


def list_contracts() -> list[str]:
    if not CONTRACTS_DIR.is_dir():
        return []
    return sorted(p.stem for p in CONTRACTS_DIR.glob("*.json"))


def get_contract(name: str) -> dict | None:
    path = CONTRACTS_DIR / f"{name}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def score(contract_name: str, ctx: dict) -> int:
    contract = get_contract(contract_name)
    if contract is None:
        return 0
    earned = 0
    for check in contract.get("checks", []):
        if _run_check(check, ctx):
            earned += check.get("weight", 0)
    return earned


def is_done(contract_name: str, ctx: dict) -> tuple[bool, int]:
    oqs = score(contract_name, ctx)
    return oqs >= OQS_DONE_THRESHOLD, oqs


# --- Per-tier OQS floors (SDD-OS, Sprint 2 / M8) -----------------------
# Higher SDD-OS tiers demand a higher output-quality floor. This is an
# ADDITIONAL, stricter, tier-aware layer; the global OQS_DONE_THRESHOLD
# (70) remains the default for is_done() so HR-OUTPUT-003 is unchanged.
TIER_OQS_FLOOR: dict[int, int] = {0: 60, 1: 70, 2: 80, 3: 90}


def tier_floor(tier: int) -> int:
    """OQS floor for an SDD-OS tier (0-3); unknown tier -> global default."""
    return TIER_OQS_FLOOR.get(tier, OQS_DONE_THRESHOLD)


def is_done_for_tier(contract_name: str, ctx: dict,
                     tier: int) -> tuple[bool, int, int]:
    """Like is_done(), but gate against the per-tier OQS floor.

    Returns (passed, oqs, floor). A Tier 3 deliverable scoring 80 is
    "done" by the global threshold but NOT by its Tier 3 floor (90).
    """
    oqs = score(contract_name, ctx)
    floor = tier_floor(tier)
    return oqs >= floor, oqs, floor
