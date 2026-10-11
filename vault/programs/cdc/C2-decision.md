# C2 decision -- one effect vocabulary

Enum (tools/cognitive_effects.py): ZERO_COGNITION, DETERMINISTIC, BOUNDED_COGNITION, NOVEL_COGNITION, OWNER_COGNITION.

| existing name (kept as alias) | source | effect |
|---|---|---|
| satisfied, sleeping | cost_to_completion ZERO_CLASSES | ZERO_COGNITION |
| deterministic | cost_to_completion / tier_routing | DETERMINISTIC |
| known_transform, bounded_coding | both | BOUNDED_COGNITION |
| novel | both | NOVEL_COGNITION |
| owner_reality | both | OWNER_COGNITION |
| tier ZERO_MODEL / SLIM / DEFAULT | tier_routing | tier_for(effect): ZERO+DET -> ZERO_MODEL, BOUNDED -> SLIM, NOVEL+OWNER -> DEFAULT |

No rename: CLASS_TIER and CLASSES stay; tier_for additionally accepts enum names. Unknown name -> None from
`normalize` (callers keep their own default; tier_for stays DEFAULT: absence is not cheap).

ABI fields on route.json / unit packets: `effect`, `deopt` (list of explicit assumptions whose violation allows
escalation), `invalidators`, `expected_boundaries`. Absent `effect` = BOUNDED_COGNITION, reported as `defaulted`.

Gate: route_admission.admit -> REFUSED_EFFECT when effect is ZERO/DETERMINISTIC, the route has workers, and `deopt`
is empty. Kill switch CDC_EFFECT_GATE=off; own error fails OPEN (route proceeds, reason logged).
Note: satisfied/sleeping were DEFAULT in tier_for before; they stay so (no behaviour change outside enum names).
