---
description: Launch a new SaaS project using the internalized 14-phase methodology
---

# SaaS Launch Protocol

You are executing the **SaaS Launch Doctrine** — a governed 14-phase methodology for shipping production-ready SaaS applications with Claude Code.

## PHASE 0: PLANNING (ask these 5 questions NOW)

Ask the user these questions before ANY code is written:

1. **What problem does this solve?** (one sentence — if they can't answer, stop)
2. **Who is the primary user?** (one persona)
3. **What are the MVP features?** (3-5 max, everything else is post-launch)
4. **What is the monetization model?** (free trial, freemium, one-time, subscription)
5. **What is the product name and deployment target?**

Write the answers into a PRD.md at the project root.

## THEN EXECUTE THE 12 PHASES IN ORDER:

1. **Planning** — PRD complete, user flows defined, data models listed, tech stack confirmed
2. **Bootstrap** — Initialize from starter kit, configure CLAUDE.md, git init, verify build passes
3. **Deploy Empty Shell** — Deploy to Vercel/Cloudflare BEFORE building. Live URL required before Phase 4.
4. **Database Schema** — Drizzle schema, migrations, seed data, verify in studio
5. **UI Shell** — Root layout, all routes as empty pages, navigation, mobile responsive
6. **Authentication** — BetterAuth + Google OAuth, protected routes at middleware, admin roles
7. **Core Feature #1** — The single most important feature
8. **Core Feature #2** — Second feature + regression check
9. **AI Integration** (if applicable) — AI SDK + OpenRouter, server-side, streaming
10. **Payments** — Polar, sandbox first, webhooks, database-backed products, full flow test
11. **Landing Page** — PRD-driven, hero + features + social proof + pricing + CTA
12. **Polish & Ship** — Full build, mobile check, analytics (PostHog), commit everything
13. **Go-to-Market Readiness** — Legal, email, SEO, support, monitoring, compliance — everything needed for first paying customer
14. **Launch & Sell** — Public launch, first users, payment verification, iterate

## DEFAULT TECH STACK:
- Next.js 14+ (App Router) + ShadCN + Tailwind
- BetterAuth (auth) + PostgreSQL/Neon (DB) + Drizzle (ORM)
- Polar (payments) + Inngest (background jobs)
- AI SDK + OpenRouter (AI) + Vercel (deploy) + PostHog (analytics)

## CLAUDE CODE OPERATING RULES:
- One phase per session. Clear context between phases.
- Plan mode before coding. Review plan before execution.
- Build → verify in browser → commit after every phase.
- Sub-agents for code review after each feature.
- Never guess at third-party APIs — provide current docs first.
- Custom commands: /checkpoint, /create-feature, /check-build

## PHASE 13: GO-TO-MARKET READINESS (detailed checklist)

This phase closes every gap between "it compiles" and "customers can pay me."

### 13a. Legal Pages (generate with Claude Code)
- [ ] Privacy Policy — GDPR + CCPA compliant, references actual data you collect
- [ ] Terms of Service — liability limits, refund policy, account termination
- [ ] Cookie Policy — if using analytics/tracking
- [ ] Refund Policy — clear, linked from checkout
- [ ] Add footer links to all legal pages from every route

### 13b. Transactional Email (Resend recommended)
- [ ] Install Resend (or Postmark). Add API key to env vars.
- [ ] Welcome email on signup (confirm they're in, show next steps)
- [ ] Payment receipt email on purchase (Polar can handle this, verify it's enabled)
- [ ] Password reset email (if using email/password auth)
- [ ] Create branded email templates (logo, colors, footer with unsubscribe)
- [ ] Set up custom domain email: hello@yourapp.com (Cloudflare Email Routing = free)

### 13c. SEO Essentials
- [ ] Page titles and meta descriptions on every route (use Next.js metadata API)
- [ ] Open Graph images for social sharing (generate with Claude Code or og-image)
- [ ] sitemap.xml (auto-generate with next-sitemap)
- [ ] robots.txt (allow all, disallow /dashboard, /admin)
- [ ] Canonical URLs on all pages
- [ ] Structured data (JSON-LD) for landing page (Organization + SoftwareApplication)
- [ ] Verify in Google Search Console

### 13d. Customer Support
- [ ] Support email configured (hello@yourapp.com or support@)
- [ ] Contact page or support widget (Crisp free tier, or simple contact form)
- [ ] FAQ page with top 5-10 questions (generate from your PRD + features)
- [ ] In-app help link in the header/footer

### 13e. Monitoring & Reliability
- [ ] Uptime monitoring — BetterStack (free tier) or UptimeRobot. Alert on downtime.
- [ ] Error tracking — Sentry free tier. Catch runtime errors before users report them.
- [ ] Database backups — Verify Neon's point-in-time recovery is enabled (default on paid)
- [ ] Rate limiting on auth endpoints (BetterAuth has built-in, verify it's active)
- [ ] CORS configured correctly (Next.js handles most, verify API routes)

### 13f. Compliance & Trust
- [ ] Cookie consent banner (if serving EU users) — use a lightweight lib like cookie-consent
- [ ] Data deletion flow — users must be able to request account + data deletion (GDPR Art. 17)
- [ ] SSL verified (Vercel auto, but check custom domain cert is valid)
- [ ] Security headers — Content-Security-Policy, X-Frame-Options (Next.js config)
- [ ] Test with Lighthouse — aim for 90+ on Performance, Accessibility, Best Practices, SEO

### 13g. Pre-Launch Testing
- [ ] Full user flow test: landing → signup → free trial → use features → hit paywall → pay → use paid features
- [ ] Mobile test on real device (not just browser devtools)
- [ ] Test with a real non-technical person (watch them, don't guide them)
- [ ] Payment test with real card in production (refund yourself after)
- [ ] Email delivery test (check spam folder)

**GATE:** All checkboxes complete. The product is commercially ready.

## PHASE 14: LAUNCH & SELL

### 14a. Soft Launch (Day 1)
- [ ] Share with 5-10 trusted people. Collect feedback.
- [ ] Monitor Sentry for errors, PostHog for drop-offs, BetterStack for uptime
- [ ] Fix any critical issues same-day

### 14b. Public Launch (Day 2-3)
- [ ] Post on: Product Hunt, Hacker News (Show HN), Reddit (relevant subreddits), Twitter/X, LinkedIn
- [ ] Have a launch discount code ready in Polar (e.g., LAUNCH25 for 25% off)
- [ ] Reply to every comment and DM within 24 hours

### 14c. First Revenue Gate
- [ ] First paying customer received and can use the product
- [ ] Payment webhook confirmed working in production
- [ ] Invoice/receipt delivered to customer
- [ ] Celebrate, then iterate

## GATE: Each phase must pass verification before proceeding to the next.

Start by asking the 5 planning questions.
