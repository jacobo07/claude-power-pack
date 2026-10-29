---
status: APPROVED 2026-10-29 (Owner proposed "KSR class-layout atlas", then picked the narrowed scope below after the premise probe)
covers: [recon-fabric-ksr-atlas, ksr-atlas, ksr-class-layout-atlas, ksr-field-atlas]
extends: [recon-fabric-ksr-lane.md, d21-step4-motion-closure-vs-frontier-2026-10-29.md]
tier: T2 (new persisted population derived from certified evidence; a claim surface other units will read)
---

# KSR atlas: measured field accesses of certified KSR accessors, with class candidates only where evidenced

## Objective
For every certified KSR accessor, record which receiver fields it touches: offset, width, domain, sign, read or write.
Each fact is read from the target bytes. Accessors are grouped into class candidates only where call-site evidence links
them. An accessor without that evidence stays UNGROUPED. It is never assigned to a class, and it is never left out of the
denominator.

## Premises (measured 2026-10-29 on GEX44, `~/missions/t1-campaign` @ 252a2652, read-only probes)
- **Population.** The KSR frontier has 8,687 CERTIFIED rows. Their lifted sources give these shapes:
  - 237 FIELD_GET (`return arg0->unkN;`);
  - 326 FIELD_SET (one store `arg0->unkN = ...;`);
  - 218 MULTI_SET (only stores through `arg0`). 215 of them have receiver `arg0` alone. These are the initialisers.
  - With receiver `arg0`: 778 functions.
- **Width from asm works.** First instruction of the getters: lwz 216, lbz 20, lhz 1. The setters' first instruction is
  often not the store (li 77, lwz 50, lfs 14, ...), so the decoder must find the store and cannot read only word 0.
- **Classes are not named.** 0 certified functions have a real name, and every receiver is `void *arg0`.
- **Vtables reach almost nothing.**
  - 17 initialisers store `&lbl_X` at +0, for 16 distinct labels.
  - 15 of those labels hold text pointers in main.dol (50 slots).
  - 0 certified accessors are vtable slots.
- **Co-receiver evidence.** Calls to these 778 functions appear in every m2c_main L1 source. The probe grouped them by
  (caller entity, first-argument expression):
  - 4,330 groups, 314 of which hold 2 or more distinct accessors;
  - after union-find: 73 components of size 2 or more, covering 220 accessors; the largest holds 10;
  - 35 of those components contain an initialiser;
  - 558 accessors have no co-receiver partner.
- **main.dol.** `~/decomp_work/b8d1db7edd42/inputs/main.dol` is the m2c input: 7 text and 11 data sections, with text at
  0x80004000 and 0x800071C0. It is the only place vtable contents can be read: the stage has text objects only (296
  `*_text.o` plus 8 `auto_fn_*_text.o`).
- **Cross-population.** The 10149 retype that motivated the proposal is a t1 problem. t1 may read KSR facts only through
  an identity map by target bytes (backlog item 9), which does not exist. The atlas therefore makes no t1 claim.

## Design
1. **Population.** KSR frontier rows with state CERTIFIED whose lifted source classifies as GET, SET or INIT with
   receiver `arg0`. The classifier is the probe's regex set, frozen in the module. Every other certified row is counted
   as `NOT_ACCESSOR` in counters, so the denominator stays 8,687.
2. **Identity.** Same as the KSR lane: entity `main:<ADDR>` plus the pinned object path and that object's sha256, both
   taken from the sweep row. The symbol is a field, never a key.
3. **Field facts from bytes** (the pinned object's code bytes for the symbol, via the same ELF walk as
   `cv1.func_hash`).
   - Decode the D-form loads and stores whose base register is r3, up to the first instruction that writes r3. A load
     into r3 counts and is the last one.
   - Map each opcode to a width, a domain and a sign:

     | opcode | width | domain | sign |
     |---|---|---|---|
     | lbz | 1 | int | u |
     | lbz followed by `extsb` on its destination | 1 | int | s |
     | lhz | 2 | int | u |
     | lha | 2 | int | s |
     | lwz | 4 | int | ? |
     | lfs | 4 | float | |
     | lfd | 8 | float | |
     | stb | 1 | int | ? |
     | sth | 2 | int | ? |
     | stw | 4 | int | ? |
     | stfs | 4 | float | |
     | stfd | 8 | float | |

   - Update forms (`lwzu`, ...) and indexed forms (`lwzx`, ...) based on r3 make the row `UNDECODED:<op>`. They are
     never guessed.
   - **Cross-check:** the set of first-level offsets in the lifted source (`arg0->unkN`) must equal the set of decoded
     offsets. A mismatch makes the row `ASM_DISAGREE`, and its facts are not used for grouping.
4. **DOL premise check.** For every atlas function, the DOL bytes at its address must equal its object bytes. A differing
   word is allowed only when both words have the same primary opcode and the object's immediate field is zero (a
   relocation site). Any other difference fails `check`, and the masked-word count is recorded.
5. **Vtable anchor.** For an INIT that stores `&lbl_X` at +0, read words from the DOL at X while they are text
   addresses (a 0 is allowed in the first two slots). If one or more are read, X is the component's vtable anchor.
   Slot addresses are recorded, never interpreted.
6. **Grouping.**
   - An edge joins two accessors called with the same first-argument expression inside one caller's L1 source. Each
     edge records its caller entity and the expression.
   - Union-find over the edges gives components. Each component gets a verdict:
     - `CONFLICT`: two facts disagree in width, domain or known sign at one offset, or two facts overlap in bytes. No
       layout is emitted, and every member is listed.
     - `MULTI_VTABLE`: the component holds more than one anchor. No layout is emitted.
     - `CANDIDATE`: otherwise. The layout is the sorted union of the facts, and each field lists its witness functions.
   - Edges come from uncertified m2c sources. A CANDIDATE is therefore evidence that the accessors are called on one
     receiver expression, not proof that they belong to one class. The output states this in `run.json`.
   - Accessors with no edge are `UNGROUPED` (`class: null`).
7. **Pins.** `run.json` records:
   - the frontier's `rows_sha256`;
   - the sweep sha256;
   - the m2c `results.tsv` sha256;
   - the DOL sha256;
   - the stage id;
   - the module's own sha256.

   `check` refuses when an input has moved.
8. **Evidence (new paths only):** `evidence/ksr-atlas/ka1/{run.json, fields.jsonl, classes.jsonl, counters.json}`.
9. **Code.** A new module `modules/recon_fabric/ksr_atlas.py` (CLI `build | check`) and the suite
   `tools/test_recon_fabric_ksr_atlas.py`, both in the t1-campaign clone. ksr_lane, cv1 and every frozen file are
   imported, never edited.

## Acceptance (each driven red -> green; a source-mutant drill names the gate each mutant must turn red)
- A1 V-RF-KA-WIDTH:
  - real getter main:801029FC gives `{off 0x60, width 4, int, read}`, and a real lbz getter gives width 1, u;
  - on fixture words, lbz+extsb gives s, lha gives s, lfs gives float, and an update form gives UNDECODED;
  - mutant: lbz mapped to width 4.
- A2 V-RF-KA-DISAGREE:
  - a fixture source whose offset differs from its decoded asm gives ASM_DISAGREE;
  - the real rows give 0 ASM_DISAGREE, or the count is reported by name;
  - mutant: the cross-check is removed.
- A3 V-RF-KA-CONFLICT:
  - on fixtures, a width clash, a float/int clash and an overlap each give CONFLICT with no layout, and a clean pair
    gives CANDIDATE (the control);
  - mutant: the overlap check is removed.
- A4 V-RF-KA-UNGROUPED:
  - a real accessor with no edge has `class: null`;
  - UNGROUPED + grouped + ASM_DISAGREE + UNDECODED = 778;
  - mutant: singletons are emitted as classes.
- A5 V-RF-KA-VTABLE:
  - real main:80154D80 anchors lbl_806B3288 with 1 or more text slots;
  - a fixture label pointing into data gives no anchor;
  - mutant: the text-range test is dropped.
- A6 V-RF-KA-PINS:
  - a moved frontier or DOL sha makes `check` refuse;
  - the DOL premise check passes on the real set and fails on a one-byte-flipped copy.
- A7 V-RF-KA-REAL: a real `build` + `check` passes. The measured counts are reported, whatever they are.
- A8: KSR 9/9 stays green. KSR `rows_sha256` and the t1 frontier are unchanged.

## Out of scope
- Emitting Kamek headers, or any C/C++ struct text.
- Feeding a retype, in KSR or t1.
- Data-flow grouping beyond the first argument within one caller (the "stronger grouping" option, not picked).
- Joining with t1 (needs backlog item 9).
- Uncertified functions.
- Pushing.

## Rollback
Revert the commits. Evidence lives in a new path only.
