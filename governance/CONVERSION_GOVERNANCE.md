# CONVERSION_GOVERNANCE.md — a conversion is a server fact, a visitor is a measured person

> Normative. Domain: any product with a landing page, pricing page, signup, onboarding, checkout or paid
> funnel. Imperative. One rule per line so a baseline can cite it. Origins cited under each rule.
> For software with no commercial funnel, only the measurement rules (CONV-01, CONV-04, CONV-07) apply.

## Rules

CONV-01 Every scripted, simulated, smoke, bot or twin visit must be stored or labelled so it can never be counted as a visitor or a conversion, and a read-only query after the run must show zero external rows from it.
(Origin: QuickLease 2026-10-22, curl probes were stored as external buyers until #582; Website Twin 2026-10-25 proved separation with a prod query.)

CONV-02 Before optimizing a landing page for a traffic source, prove that source reaches the first funnel event, with a positive control (a tagged visit is recorded) and a negative control (an untagged or bot visit is not).
(Origin: QuickLease 2026-10-25, offer_viewed carried no campaign, so paid UK clicks could not be counted against the page they landed on.)

CONV-03 Count a paid conversion only from the payment processor's server event (webhook), never from a success-page visit or a client event, and keep the case record joined to it.
(Origin: QuickLease funnel contract, payment_completed is written only by the Stripe webhook route.)

CONV-04 Report a conversion rate, lift or forecast only above a declared minimum sample; below it the answer is INCONCLUSIVE together with the sample size and minimum detectable effect still needed, never a precise percentage.
(Origin: QuickLease 2026-10-22, 0 paid conversions; TimesFM DOES_NOT_BEAT_BASELINE 8/8 and was rejected.)

CONV-05 A ratio such as visitors to starts is a page-to-form rate only if the entry event is emitted on that page; name the page that emits each event before dividing one count by another.
(Origin: QuickLease 2026-10-25, "94 intake openings, 0 starts" mixed direct entries and smoke runs with landing traffic.)

CONV-06 A hypothesis that price reduces conversion is testable only on visitors who saw the price; first measure where the price is shown and how many visitors reached that point.
(Origin: QuickLease 2026-10-25, the fee is shown only on the Review and pay step and no external visitor reached it.)

CONV-07 A text-presence check that says a page answers a visitor question must carry golden tests, including a sentence that defers or negates the answer, so neither a false present nor a false missing passes.
(Origin: Website Twin 2026-10-25, "VAT included, on the review step" was read as a stated price, and a one-way pattern missed the approved hero text.)

CONV-08 Experiments keep the price fixed unless price is the declared and authorized treatment, and their primary metric is paid, qualified conversion, never clicks or click-through rate alone.
(Origin: QuickLease experiment registry, same-price by construction; CTR can rise while paid contracting falls.)

## Simulation is an instrument, not evidence
Synthetic personas and scripted journeys measure the software (where the next step is, what the visible
text answers). They never measure people. Their output is labelled synthetic, counts runs, never forms a rate,
and is never cited as customer behaviour. (Origin: MiroFish evaluation 2026-10-25 — a social-simulation
engine has no website navigation and no calibration against buyers.)
