# Incident: QuickLease sign-up is unreachable in production (found by the demo pipeline)

Date: 2026-09-24. Found while preparing the first real /product-demo capture.
Status: OPEN, reported to the Owner. No production write occurred during discovery.

## Symptom (OBSERVED)
On https://ql.infinityops.ai/sign-up, "Create account" shows
"We could not reach the auth service. Please try again or email ...".
Browser console: `Access to fetch at 'https://infinityops.ai/api/auth/sign-up/email' from origin
'https://ql.infinityops.ai' has been blocked by CORS policy`.

## Impact
/ql/new-case (the customer intake: main nav "New case", every QL CTA) requires an account.
A customer arriving on ql.infinityops.ai cannot create one, so the paid funnel is cut at its entrance.
Sign-in uses the same client and is very likely affected the same way (UNVERIFIED: no existing
account was used, by design).

## Evidence (measured 2026-09-24)
- Preflight `OPTIONS https://infinityops.ai/api/auth/sign-up/email` with
  `Origin: https://ql.infinityops.ai` -> 204 with NO `Access-Control-Allow-Origin`.
- `GET https://ql.infinityops.ai/api/auth/ok` -> 200 `{"ok":true}`: the auth API IS served
  same-origin on the QL host (proxy.ts passes /api through untouched on that host).
- `lib/auth-client.ts:16-17`: `baseURL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "https://infinityops.ai"`
  -> every auth call from the QL subdomain is cross-origin.
- `auth.ts` (`betterAuth({...})`) declares no `trustedOrigins`; Better Auth then trusts only
  its own baseURL origin, so a same-origin call from the QL host would also need the QL
  origin trusted server-side.
- auth-client.ts last changed 2026-09-14 (#405, TOTP UI); the value dates from the Clerk ->
  Better Auth migration (2026-05-28). When the QL host began failing is UNKNOWN.

## Root cause (INFERRED from the evidence above, not yet proven by a fix)
The auth client pins an absolute, apex origin, and the apex does not answer CORS for the
subdomain. The same-origin route that proxy.ts was written to preserve is never used.

## Proposed fix (NOT applied; production auth, Owner decision)
1. Client: on a QuickLease host use the page's own origin for the auth baseURL.
2. Server: add the QL origin(s) to `trustedOrigins`.
3. Verify in a real browser on the deployed host: sign-up succeeds, lands on /ql/new-case,
   session cookie set on the QL host; and the apex sign-in still works (regression control).

## Discovery hazards met on the way (instrument failures, recorded honestly)
- A fill before React hydration was silently reset to "" (fixed in the capture module as
  INPUT_NOT_ACCEPTED).
- `wait_for_url("**/new-case**")` matched the sign-up URL's own `?redirect_to=/ql/new-case`
  and returned before any navigation. Wait for leaving the page, not for a substring.

## Also seen (visual, not blocking the funnel)
The sign-up card renders near-invisible label and heading text (light ink on the light
paper card) and dark inputs on that card: a contrast defect on the customer sign-up page.

## Lesson
A demo pipeline that drives the real product is a production smoke test. Its first
honest output here was not a video: it was a refusal that located a live outage.
