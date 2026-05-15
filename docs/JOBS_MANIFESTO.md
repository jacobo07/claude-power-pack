# The Jobs & Wozniak Manifesto — Global Quality Sovereignty

Two permanent global guardians stand between every project and the user.
They are not reviewers. They are the last gate before mediocrity ships.

- **`steve-jobs`** — design, UX, product vision. *Simplicidad obsesiva. Honestidad brutal. No me des lo que quiero, dame lo que necesito. Elimina lo que sobra. Emocionalmente impactante, comercialmente imbatible.*
- **`woz`** — engineering elegance. *Más con menos. Cero redundancias o código inflado. Elegancia técnica y robustez. One-Shot perfection: menos código, más potencia, cero fallos.*

## The contract

1. **Nothing forgettable ships.** If a normal person would not repeat your product in one sentence to a friend, it is not done (Jobs).
2. **Every line is a liability.** If the same behavior survives with fewer parts, the longer version is a defect, not a style (Woz).
3. **Zero slop, fail-closed.** `Coming Soon`, `TODO`, `FIXME`, `PLACEHOLDER`, empty handlers, dead `href="#"`, `raise NotImplementedError`, empty `catch {}` — these do not reach the vault. The gate **blocks the write** (`permissionDecision: deny`).
4. **Vetoes compound.** Every VETO is written permanently to `~/.claude/knowledge_vault/global_vetoes.md`. A mistake vetoed once is prohibited in every future project — the Snowball Effect.
5. **On VETO, iterate — do not negotiate.** Fix using `Downloads/Promptsss/Prompts pa iterar/Universal/iteracion-avanzada-visual.txt` until `VERDICT: SHIP`. "Good enough" is the enemy.

## Enforcement architecture

```
Write|Edit|MultiEdit
   └─► jobs-woz-gatekeeper.js  (PreToolUse hook, ~/.claude/hooks/)
          │  scans NEW content only (Write.content / Edit.new_string / MultiEdit.edits[].new_string)
          ▼
       quality_audit.py  (claude-power-pack/tools/)
          ├─ UI ext  (.tsx .jsx .vue .svelte .css .html) → JOBS lens
          └─ code ext (.py .js .ts .go .rs .java …)       → WOZ lens
          ├─ exit 5 (slop) → deny + append [JOBS|WOZ]-VETO to global_vetoes.md
          └─ exit 0 (clean) → allow
   --distilled [<dir>]  → audits the 22 KobiiDistillerOS sections
                          (Jobs hardest on §1/§10, Woz hardest on §4)
```

Self-protection: `quality_audit.py` skips governance/meta files (itself, this manifesto, the ledger, `scaffold-auditor.js`, `zero-fiction-gate.js`, `secret-scanner.js`, and everything under `~/.claude/agents/`, `~/.claude/hooks/`, `knowledge_vault/`) so the gate can never veto its own detector data. It is complementary to `zero-fiction-gate.js` (generic Reality Contract) — Jobs/Woz add a *domain-routed, persona-named* verdict that feeds the compounding ledger.

Activation note: agent files and hooks **cold-load at session start**. `steve-jobs`/`woz` become dispatchable, and the gate becomes live, on the next `/restart`. The enforcement logic is verified this session by the runnable checker (see Sample Audit).

## Sample Audit — a real VETO

Input file `LandingHero.tsx` submitted for write:

```tsx
export default function LandingHero() {
  return (
    <section className="hero">
      <h1>Coming Soon</h1>
      <button onClick={() => {}}>Get Early Access</button>
    </section>
  );
}
```

`python tools/quality_audit.py LandingHero.tsx` →

```
VERDICT: VETO  [STEVE JOBS]

WHAT I SAW
  LandingHero.tsx — 2 slop defect(s). This is not shippable.

WHY
  L4: 'Coming Soon' — mediocrity reaches the user/vault here.
  L5: 'onClick={() => {}}' — mediocrity reaches the user/vault here.

CUT LIST
  - LandingHero.tsx:4  delete/replace 'Coming Soon'
  - LandingHero.tsx:5  delete/replace 'onClick={() => {}}'

THE ONE THING
  Never ship user-facing surface containing 'Coming Soon' — build it or cut it.

LEDGER
  JOBS-VETO recorded permanently.
```

Exit code `5`. The PreToolUse hook converts this to `permissionDecision: "deny"` — the file is **never written**. Two permanent prohibitions are appended to the global ledger. The only path forward is to build the real hero and the real handler, then resubmit until `VERDICT: SHIP`.

That is the standard. Brutally simple. Emotionally impactful. Commercially unbeatable. Or it does not ship.
