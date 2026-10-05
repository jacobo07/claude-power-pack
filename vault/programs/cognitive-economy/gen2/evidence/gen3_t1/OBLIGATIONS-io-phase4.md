# Original Obligation Set -- InfinityOps odr-device-trust Phase 4 (Gen3 T1 K5)

Read-only extraction by quotation from `C:\Users\User\Apps\io-device-trust\.planning\workstreams\odr-device-trust\`. No obligation is invented: every row quotes a source line.
`type` is a KEYWORD HEURISTIC (security/authority/observability/production-reality/proof/invariant/deliverable, else requirement) -- UNREVIEWED; a human may re-type a row, the quote and source stay.

## Phase 4 section in ROADMAP.md: lines 141-154; IDs referenced: SEAM-01, SEAM-02, SEAM-03

## Obligations (requirements + roadmap success criteria)

| id | text (quoted) | source | type (heuristic) |
|---|---|---|---|
| SEAM-01 | - [ ] **SEAM-01**: nginx (`09_Provisioning/ascend.sh`) gets a `/socket/device` location with Upgrade headers routed to Phoenix (:4100). | REQUIREMENTS.md:47 | production-reality |
| SEAM-02 | - [ ] **SEAM-02**: The founder can mint a pairing code through a Next BFF route + dashboard control (the mint route is DNA-HMAC). | REQUIREMENTS.md:48 | authority |
| SEAM-03 | - [ ] **SEAM-03**: A backend probe (DeviceSocket connect with a bad credential returns the typed refusal) exists for the deploy gate, because the frontend SHA gate cannot see the Elixir release. | REQUIREMENTS.md:49 | security |
| SC-1 | 1. `09_Provisioning/ascend.sh` provisions a `/socket/device` location with Upgrade headers routed to Phoenix (:4100) instead of falling into `location /` (Next :3200); a check over the script's rendered nginx config asserts it (CODE_VERIFIED, the live vhost is not read). Falsifier **(proposed)**: removing the location or its Upgrade headers goes red. | ROADMAP.md:148 | production-reality |
| SC-2 | 2. The founder can mint a pairing code from a dashboard control backed by a Next BFF route: the founder sees the raw code once, the DNA-HMAC signing happens server-side only, and a non-founder session gets the `capability_denied` outcome with no code. Falsifier **(proposed)**: a BFF that omits the signature or the founder check goes red. | ROADMAP.md:149 | security |
| SC-3 | 3. A backend probe connects to DeviceSocket with a bad credential and passes only when it receives the typed refusal (`403` with an `error` code); it fails when the target answers with something else (for example Next's response because the socket route is unrouted), and it is invocable as a deploy-gate step separate from the frontend SHA gate. Control: the same probe against the local Phoenix endpoint passes. | ROADMAP.md:150 | security |

## Decisions (04-CONTEXT.md)

| id | decision (quoted) | source |
|---|---|---|
| D-01 | nginx location (SEAM-01) | 04-CONTEXT.md:27 |
| D-02 | vhost check (SEAM-01 falsifier) | 04-CONTEXT.md:34 |
| D-03 | founder mint BFF + dashboard (SEAM-02) | 04-CONTEXT.md:44 |
| D-04 | backend probe (SEAM-03) | 04-CONTEXT.md:61 |
| D-09 | binding attestation and the Phase 2 runtime-digest attestation remain OWNER DECISIONS. | 04-CONTEXT.md:143 |

## Headings of 04-UI-SPEC.md

- `04-UI-SPEC.md:11` # Phase 4 — UI Design Contract (Sistema · Dispositivos)
- `04-UI-SPEC.md:17` ## Scope
- `04-UI-SPEC.md:44` ## Decisions (auto)
- `04-UI-SPEC.md:64` ## Design System
- `04-UI-SPEC.md:83` ## Spacing Scale
- `04-UI-SPEC.md:103` ## Focal Points
- `04-UI-SPEC.md:107` ## Typography
- `04-UI-SPEC.md:127` ## Color
- `04-UI-SPEC.md:145` ## Layout and Components
- `04-UI-SPEC.md:147` ### Page anatomy (top to bottom, single column)
- `04-UI-SPEC.md:166` ### `SistemaNav` (`app/sistema/sistema-nav.tsx`)
- `04-UI-SPEC.md:175` ### `PairingForm` (client)
- `04-UI-SPEC.md:193` ### `OnceShownCode` (client, inside `pairing-form.tsx`)
- `04-UI-SPEC.md:220` ### Components used
- `04-UI-SPEC.md:231` ## States and Outcomes
- `04-UI-SPEC.md:233` ### Page state — `devicePageState(me)` in `lib/device-view.ts` (pure, unit-tested; page follows it)
- `04-UI-SPEC.md:244` ### Action result — `mintPairingCodeAction(_prev, _formData): Promise<MintState>`
- `04-UI-SPEC.md:273` ### Secret-handling invariants (each one checkable by a source scan of `pairing-form.tsx` and `actions.ts`)
- `04-UI-SPEC.md:280` ## Copywriting Contract
- `04-UI-SPEC.md:328` ## Accessibility
- `04-UI-SPEC.md:332` ### Keyboard path
- `04-UI-SPEC.md:350` ### Announcements (screen readers)
- `04-UI-SPEC.md:367` ### Other
- `04-UI-SPEC.md:377` ## Capability Inventory
- `04-UI-SPEC.md:420` ## Registry Safety
- `04-UI-SPEC.md:430` ## Checker Sign-Off

## Headings of 04-RESEARCH.md

- `04-RESEARCH.md:1` # Phase 4: Production Seams - Research
- `04-RESEARCH.md:7` ## Summary
- `04-RESEARCH.md:22` ## User Constraints (from CONTEXT.md)
- `04-RESEARCH.md:24` ### Locked Decisions
- `04-RESEARCH.md:26` #### D-01 nginx location (SEAM-01)
- `04-RESEARCH.md:33` #### D-02 vhost check (SEAM-01 falsifier)
- `04-RESEARCH.md:43` #### D-03 founder mint BFF + dashboard (SEAM-02)
- `04-RESEARCH.md:60` #### D-04 backend probe (SEAM-03)
- `04-RESEARCH.md:73` ### Claude's Discretion
- `04-RESEARCH.md:84` ### Deferred Ideas (OUT OF SCOPE)
- `04-RESEARCH.md:92` ## Phase Requirements
- `04-RESEARCH.md:101` ## Project Constraints (from CLAUDE.md)
- `04-RESEARCH.md:116` ## Architectural Responsibility Map
- `04-RESEARCH.md:127` ## Standard Stack
- `04-RESEARCH.md:131` ### Core
- `04-RESEARCH.md:141` ### Alternatives Considered
- `04-RESEARCH.md:150` ## Package Legitimacy Audit
- `04-RESEARCH.md:161` ## Architecture Patterns
- `04-RESEARCH.md:163` ### System Architecture Diagram
- `04-RESEARCH.md:200` ### Recommended Project Structure (new / edited files)
- `04-RESEARCH.md:218` ### Pattern 1: The nginx insertion point (SEAM-01)
- `04-RESEARCH.md:240` ### Pattern 2: ExUnit heredoc parser (SEAM-01 falsifier)
- `04-RESEARCH.md:264` ### Pattern 3: `mintPairingCode()` + action + page (SEAM-02)
- `04-RESEARCH.md:291` ### Pattern 4: The probe (SEAM-03)
- `04-RESEARCH.md:336` ### Anti-Patterns to Avoid
- `04-RESEARCH.md:343` ## Don't Hand-Roll
- `04-RESEARCH.md:355` ## Common Pitfalls
- `04-RESEARCH.md:357` ### Pitfall 1: Comment braces corrupt the location tree
- `04-RESEARCH.md:363` ### Pitfall 2: `proxy_pass` with a URI part
- `04-RESEARCH.md:367` ### Pitfall 3: Copying `Connection ""` from `/api/`
- `04-RESEARCH.md:372` ### Pitfall 4: `^~` versus `=` versus a regex
- `04-RESEARCH.md:375` ### Pitfall 5: Probe runs before the new nginx config is live
- `04-RESEARCH.md:379` ### Pitfall 6: Hairpin NAT: two comments contradict each other
- `04-RESEARCH.md:382` ### Pitfall 7: New vitest files never run in CI
- `04-RESEARCH.md:386` ### Pitfall 8: Copy in `lib/` escapes the LANG gate
- `04-RESEARCH.md:389` ### Pitfall 9: Secret or code reaching the client bundle or logs
- `04-RESEARCH.md:396` ### Pitfall 10: Parsing microsecond ISO timestamps
- `04-RESEARCH.md:399` ### Pitfall 11: Local Phoenix boot side effects
- `04-RESEARCH.md:402` ## Code Examples
- `04-RESEARCH.md:404` ### Pinned lookup (both callback shapes)
- `04-RESEARCH.md:418` ### Probe request (no Origin, no redirects, bounded body)
- `04-RESEARCH.md:439` ### Verdict (typed set copied verbatim from device_socket.ex:59-61)
- `04-RESEARCH.md:454` ### mintPairingCode (in holdings-client.server.ts, beside createInvitation)
- `04-RESEARCH.md:482` ### Local live control recipe (PowerShell, inline in the main session)
- `04-RESEARCH.md:484` # Postgres :5433 per PROJECT.md:21. Partition isolates boot writes (Pitfall 11).
- `04-RESEARCH.md:488` # start detached, log to disk; then:
- `04-RESEARCH.md:495` ## State of the Art
- `04-RESEARCH.md:503` ## Assumptions Log
- `04-RESEARCH.md:513` ## Open Questions
- `04-RESEARCH.md:533` ## Environment Availability
- `04-RESEARCH.md:546` ## Validation Architecture
- `04-RESEARCH.md:548` ### Test Framework
- `04-RESEARCH.md:556` ### Phase Requirements -> Test Map
- `04-RESEARCH.md:569` ### Mutation drills (each must go RED with a named failing test; green control named; restore hash-equal)
- `04-RESEARCH.md:587` ### Sampling Rate
- `04-RESEARCH.md:592` ### Wave 0 Gaps
- `04-RESEARCH.md:598` ## Security Domain
- `04-RESEARCH.md:600` ### Applicable ASVS Categories
- `04-RESEARCH.md:613` ### Known Threat Patterns
- `04-RESEARCH.md:625` ## Sources
- `04-RESEARCH.md:627` ### Primary (HIGH confidence; files read this session)
- `04-RESEARCH.md:637` ### Secondary (CITED)
- `04-RESEARCH.md:642` ### Tertiary (ASSUMED)
- `04-RESEARCH.md:645` ## Metadata

## Ambiguities / flags

- none detected by the extractor
- Decisions D-nn found: 5; obligations rows: 6. If either is 0 the line patterns did not match this file's layout (instrument blind) -- inspect the source manually.
- Obligations carried only in prose paragraphs (no list/table line) are NOT extracted: counts are a FLOOR, not the full set.
