# Six retracted claims, and the rule each one buys

From the ABSW2-Wii programme's `docs/ARCHITECTURE_TRUTH.md` §3. Each was
believed, acted on, and withdrawn. They are kept because a record showing only
surviving claims teaches nothing about how the wrong ones were produced.

Read this before asserting an absence, before reading a crypto table as a
finding, and before trusting any third-party analysis report.

---

## R-01 — "The scripts are JavaScript"

**Believed because** `libjs.so` was present and there was a `cocos/` folder.

**Killed by** 622 `.lua` files and a confirmed Lua 5.1 runtime in the engine
binary. `libjs.so` exists and is not what runs the game.

> **Rule.** Infer a component's role from the engine binary, never from its
> presence in a directory listing. A shipped library may be dead weight, a
> dependency of a dependency, or used for one unrelated feature.

---

## R-02 — "The scripts are XXTEA-encrypted; recover the key from `setXXTEAKey`"

**Believed because** a third-party decompilation service's notes said so.

**Killed by** a literal count: `cocos2d` ×0, `xxtea` ×0, `setXXTEAKey` ×0 across
19.4 MB of engine binary. The service emits a Cocos2d-x analysis for *any*
upload containing `.lua` files. It tried four default Cocos keys, failed, and
reported the failure in Cocos vocabulary. It had measured its own assumption.

> **Rule.** A generated report is not a measurement of your subject. Before
> acting on one, find the claim it makes that your own instrument can check, and
> check it. The cheapest check is usually a literal count.

---

## R-03 — "No Lua or Box2D symbols, therefore neither is linked in"

**Believed because** a symbol scan returned nothing for both.

**Killed by** noticing the scan could not have returned the other answer:
**symbol names do not survive stripping**, so for a stripped static link the
result is identical whether the library is there or not. Re-run against runtime
literals — which are compiled into C source and do survive — Lua came back
CONFIRMED. Box2D did not, but a Box2D build with assertions disabled emits no
assert strings either, so it stayed INCONCLUSIVE rather than inheriting Lua's
outcome.

> **Rule.** Before asserting an absence, prove the instrument could have found
> the thing. An instrument that can only ever return one answer carries no
> information when it returns it.
>
> **Second rule, from the Box2D half.** Two components can fail the same scan
> for different reasons. One may be genuinely absent and the other merely
> invisible. Do not let a resolved neighbour resolve them both.

---

## R-04 — "The script cipher is AES"

**Believed because** the Rijndael S-box and its inverse are in both binaries.

**Killed by** OpenSSL being linked in — `/crypto/` ×127, `X509` ×54, `libcurl`
×10, `ssl/s3_` ×6. An HTTPS stack fully accounts for an AES implementation
without the scripts ever touching it.

**The warning was in hand and walked past.** The `AES` string counts *differ*
between the two ABIs, 76 against 74, noted at the time as proof that some are
unrelated — and the claim was allowed to reach CONFIRMED anyway. A count that
differs between two builds of one source is a count of several unrelated things.

**The cost was not cosmetic.** A 22,892,378-candidate key sweep was built on it,
testing AES-CBC decryption specifically. Its clean miss was reported as "the key
is not stored verbatim"; the supportable statement was "no *AES* key is stored
verbatim".

> **Rule.** A primitive present in the process does not identify the component
> that uses it. Ask which linked library would supply that primitive for its own
> reasons before reading it as evidence.
>
> **Second rule.** When two builds of one source disagree about a count, the
> count is of several things. That disagreement is a finding, not noise.

*(The cipher did turn out to be AES-256-CBC. The retraction was still correct on
the evidence it had: the tables never proved it, and the sweep built on them
measured nothing.)*

---

## R-05 — "Fixed IV, therefore CBC"

**Believed because** three sibling files share a byte-identical 64-byte
ciphertext prefix.

**Killed by** a stream cipher reusing one keystream producing exactly the same
observation: `C₁ ⊕ C₂ = P₁ ⊕ P₂`, which is zero wherever the plaintexts agree.
The prefix collision cannot discriminate the two mechanisms.

What *does* discriminate is padding: every file being an exact multiple of 16 B
means the output is padded to a block boundary, and a stream cipher does not pad.

> **Rule.** An observation consistent with two mechanisms is evidence for
> neither. Name the second mechanism explicitly, then find the measurement that
> separates them — there usually is one, and it is usually cheap.

---

## R-06 — "0 hits in 22.9M candidates, so the key is derived at runtime"

**Believed because** an exhaustive sweep of every byte-aligned 16/24/32-byte
window of the whole image found nothing, with green controls.

**Killed by** reading what the oracle accepted. Both sweeps scored a candidate
only if its plaintext was printable Lua **source** or inflated as **deflate**.
The real plaintext is an LZMA stream behind a binary magic, carrying compiled
bytecode — high entropy, not printable, not deflate. **The oracle could not have
accepted the correct key had it been in the candidate set.**

The controls were green and did not help. They proved the oracle rejects random
keys and that the cipher implementation works. They never proved it accepts the
true plaintext *format*.

> **Rule.** A positive control must be drawn from the space of **plausible**
> plaintexts, not from the one you expect. A control built for the format in
> mind certifies an oracle blind to the format that exists.
>
> **Corollary.** "Controls were green" is not a property of a sweep. Ask what
> each control would have failed on, and whether the true answer is inside the
> set it validates.

---

## The instrument failure that is not numbered

The first physics check printed `Box2D vocabulary present: NONE` directly beside
a key listing that contained `collideConnected` and `motorSpeed`. Its keyword
list held only *fixture* names and no *joint* names, so it could not have found
what was in front of it.

> **Rule.** A verdict that contradicts the evidence printed beside it indicts
> the parser, not the world. Make every check print what it matched against, so
> its own bugs are visible for free.
