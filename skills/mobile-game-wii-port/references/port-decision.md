# Phase 5 — extract the data, or port the runtime?

This is the decision the whole archaeology exists to serve, and it is the one
most often made on preference. Make it on the Phase 4 measurement.

## The two answers

**Extract-and-drive.** Recover the game's data — levels, entity definitions,
rosters, tuning tables — into a format your own engine reads, and write native
code for the behaviour. The original scripting runtime never ships.

**Port-the-runtime.** Build the original's script interpreter for the target,
implement every native function its scripts call, and run the original scripts
largely unmodified.

## The measurement that decides it

Count **by instruction, not by file**, and interpret nested function bodies
separately from top-level constructors.

A file-level sweep gets this badly wrong. In the source corpus, 432 of 622 files
are at least 99% data construction *in their main prototype* — which reads like
"the corpus is data" until you notice the sweep never entered the nested
function bodies, and that is exactly where behaviour lives.

Done properly:

| | instructions | share |
|---|---|---|
| main prototypes (data construction) | 2,171,347 | **91.6%** |
| nested function bodies (behaviour) | 199,758 | **8.4%** |

That 8.4% is roughly 200,000 instructions of real behaviour concentrated in the
190 files that are not pure constructors. It is also the part that would justify
a decompiler.

## Reading the number

**Data-dominant (roughly 85% and above).** Extract-and-drive. The scripting
runtime would be carried for a minority of the corpus, and porting it means
implementing every native binding the scripts touch — an open-ended surface you
do not control and cannot enumerate until late.

**Behaviour-dominant (roughly 50% and below).** Porting the runtime becomes
competitive, because rewriting that much logic by hand is the larger risk.

**In between.** Neither answer is free. Decide on the *binding surface* instead:
count the distinct native globals and methods the scripts reach for. A small,
enumerable surface favours porting; a wide or dynamically-dispatched one favours
extraction, because you cannot finish implementing what you cannot list.

In the source corpus the scripts reach the engine through a small number of
globals — one dominant native bridge used 6,725 times across 119 files, beside a
UI namespace, an event system and a settings wrapper — but with 1,663 distinct
globals read and dynamic lookup through the global table in 137 files. The
*callee* side was never enumerated, which is precisely the risk: the list of
functions to implement was not knowable from the scripts alone.

## What the target platform adds

A console port changes the arithmetic against porting a runtime:

- **Memory.** An interpreter plus its heap plus the script corpus competes with
  your own assets on a fixed budget with no swap.
- **No JIT.** An interpreter loop is the slow path on an in-order PowerPC core.
- **Numeric semantics.** If the original built its interpreter with
  single-precision numbers, a stock build of that interpreter does not reproduce
  the original's arithmetic.

## What extraction must not lose

Extraction is only safe if the extractor reports its own gaps.

- Every value it cannot establish is emitted as an explicit unknown **with a
  count**, so a partial recovery can never read as a complete one.
- Drive that path in the gate and require the count to be exact. A recovery that
  silently drops what it did not understand is the failure this rule exists for.
- Cross-check at least one recovered total by a second, independent path. In the
  source programme the 56-character roster was confirmed by counting keys
  straight off the instruction stream, without the register model that produced
  the first number.

## The thing extraction cannot decide for you

The content's **semantics** still have to be reproduced. If levels are authored
in a physics library's vocabulary — fixture density, friction, restitution;
joint motor speed, max torque, lower and upper limits; a pixels-per-metre ratio
— then your engine must reproduce that library's behaviour for those parameters,
or the levels do not play the same.

This is established from the *content*, not from the binary. Whether the
original links that library is a separate and much less important question: a
compatible implementation would look identical from the content side, and the
port's obligation is the same either way.
