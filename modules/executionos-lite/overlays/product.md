# Overlay: Product/SaaS

- **Auth:** BetterAuth or equivalent. Session + refresh tokens. Never roll custom auth crypto.
- **Payments:** Polar or Stripe. Webhook verification mandatory. Idempotency keys on all payment operations.
- **Deployment:** Vercel for frontend, Railway/Fly for backend. CI/CD pipeline required before launch.
- **Database:** Neon (serverless Postgres) preferred. Connection pooling enabled. Migrations versioned.
- **Observability:** PostHog for analytics + feature flags. Error tracking (Sentry or equivalent) from day one.
- **Growth:** Waitlist before build. Launch on Product Hunt + relevant communities. Track activation metrics.
- **Pricing:** Start simple: free + one paid tier. Validate willingness to pay before adding tiers.
- **Security:** OWASP Top 10 baseline. Rate limiting on auth endpoints. Input validation on all forms.
- **Mobile:** Responsive-first. Test on real devices. PWA if native not justified.
- **Launch Sequence:** Idea > Waitlist > MVP > Beta users > Feedback > Iterate > Public launch.
