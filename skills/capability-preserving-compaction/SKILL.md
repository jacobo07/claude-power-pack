---
name: capability-preserving-compaction
metadata:
  opportunity_detector: none
  opportunity_detector_reason: "doctrine skill relocated from ~/.claude/rules by cognitive-economy E1; no opportunity detector exists for it yet"
description: "Use when a rich control becomes a smaller one (row to icon, toolbar to overflow menu, desktop layout reflowed to a phone) or when a component is deleted together with its tests. Inventory every interaction from the source (hover reveals, context menus, disabled states, badges, keyboard paths, drag targets) before removal, give each a destination, land the new surface beside the old one, re-pin relocated behaviours, then assert the old surface is gone. Core rule - a green suite is not evidence that a compaction preserved behaviour."
---

# Capability-Preserving Compaction

When a rich control becomes a smaller one — a row becomes an icon, a toolbar collapses into an
overflow menu, a desktop layout reflows to a phone — the visible primary action survives because it
is the thing you were looking at. The secondary affordances are what disappear, silently, and they
are usually the ones a power user relies on.

## The trap that makes this invisible

**Deleting a component deletes its tests.** The coverage that would have caught the loss is removed
in the same commit as the thing it protected, so the suite goes green *because* the capability is
gone. Nothing turns red. A migration can therefore delete a dozen affordances and report a clean
run.

This is why "the tests still pass" is not evidence for a compaction. The only evidence is an
inventory taken **before** the original is removed.

## The procedure

1. **Read the component and enumerate every interaction**, not the design description of it.
   Hover reveals, right-click menus, disabled states, prefetch on focus, badges, tour anchors,
   keyboard paths, drag targets. Descriptions systematically omit these; the source does not.
2. **Give every item a destination** before deleting anything. Each must land on exactly one of:
   - RETAINED in the new primary interaction
   - RELOCATED to a named secondary surface
   - REPLACED by a better canonical interaction
   - REMOVED, with evidence it was dead or redundant
3. **Land the new surface first, with the old one still present.** One commit where both exist is
   duplicate chrome for a moment; it is also the only state in which you can compare them.
4. **Re-pin the relocated behaviours** against the new surface, then remove the old. Coverage moves
   rather than shrinks.
5. **Add one assertion that the old surface is gone**, so the duplicate-chrome state cannot quietly
   become permanent.

## Treat compaction as an accessibility opportunity

A capability that was hover-only was already unreachable from the keyboard. Moving it into a
context menu or an overflow list is a gain, not a compromise — do not preserve a weak interaction
just because it is the one that existed. Conversely, do not let "it's in a menu now" excuse dropping
something that was previously one click away without saying so.

Badges and counts are capabilities too. If a number no longer fits, keep the number in the
accessible name; information that survives only as a coloured dot is information you removed for
anyone not looking at it.

## DON'T

- **Don't infer the inventory from the mockup.** The mockup shows the resting state; the affordances
  live in the interaction states.
- **Don't call a green suite evidence** that a compaction preserved behaviour — see the trap above.
- **Don't delete the old surface in the same commit that adds the new one.** You lose the ability to
  bisect which of the two broke the behaviour.
- **Don't assume a shrunken control keeps its gating.** Disabled states, permission checks and
  empty-state handling are easy to drop when the markup changes shape.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/capability-preserving-compaction.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
