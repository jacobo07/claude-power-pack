# HTTP/3 (QUIC) vs HTTP/2: Measured Performance Gains on Mobile Networks

## Executive Summary

HTTP/3 over QUIC delivers substantial, quantified performance improvements over HTTP/2, but **only under specific network conditions**. Field measurements show 30–50% faster page loads at 5% packet loss and 5–15% gains at 1% loss [OBSERVED][HIGH], with improvements exceeding 250ms in high-latency emerging markets [OBSERVED][HIGH]. However, the advantage requires **simultaneous high packet loss (2–5%) and high latency (50ms+)** to materialize [OBSERVED][HIGH]. Under ideal network conditions (0% loss, 0ms delay), the protocols perform identically at approximately 9 seconds for 10MB downloads [OBSERVED][HIGH].

The mechanism underlying these gains is QUIC's per-stream ordering, which allows lost packets to stall only affected streams while others continue, whereas TCP's global ordering blocks all concurrent traffic [VERIFIED][HIGH]. This isolation is responsible for 30–50% of the speedup at 5% loss [VERIFIED][HIGH].

**Critical caveat**: HTTP/2 performance is not fixed. With proper congestion control tuning (BBR), HTTP/2 can recover 50% of the performance gap at lower operational cost than a full HTTP/3 migration [OBSERVED][HIGH]. Additionally, infrastructure and regulatory constraints—kernel-based TLS inspection, firewall UDP processing, Kubernetes controller abandonment of HTTP/3 support—have indefinitely stalled enterprise adoption, and many networks are disabling HTTP/3 at the perimeter [VERIFIED][MEDIUM] [DERIVED][MEDIUM].

---

## 1. Measured Performance Improvements: Field Data

### 1.1 Page Load and Throughput Gains

**High-Loss Networks (5% Packet Loss)**

HTTP/3 delivers 30–50% faster page loads than HTTP/2 at 5% packet loss, with independent confirmation from both Google and Cloudflare field measurements [OBSERVED][HIGH]. These gains are largest on high-latency, lossy links typical of mobile networks in developing regions [OBSERVED][HIGH], making this metric directly actionable for SLA commitments to specific user cohorts.

**Moderate-Loss Networks (1% Packet Loss)**

At 1% packet loss, HTTP/3 maintains median page-load time within 5% of baseline while HTTP/2 experiences 30%+ degradation on the same path [OBSERVED][HIGH]. A fintech API gateway production deployment showed 12% reduction in 99th-percentile latency after rolling out HTTP/3 to 30% of traffic [OBSERVED][HIGH]. This quantifies the business case: operators migrating to HTTP/3 can recover 20–30 percentage points of performance loss that HTTP/2 would have incurred under packet loss.

**Severe Conditions (4% Loss + 50ms Latency)**

Under the most severe measured conditions, HTTP/2 with default congestion control (Cubic/NewReno) requires 106 seconds for file transfer while HTTP/3 requires 15 seconds—a 87% improvement [OBSERVED][HIGH]. When HTTP/2 switches to BBR congestion control, the same transfer completes in 10 seconds, narrowing the gap to 33% of HTTP/3's time [OBSERVED][HIGH]. This suggests operators should first audit congestion control configuration before committing to HTTP/3 migration.

### 1.2 Connection Setup and Regional Impact

Wix measured 33% reductions in connection setup times when switching to HTTP/3, with improvements exceeding 250ms in emerging markets like the Philippines [OBSERVED][HIGH]. This metric is immediately observable after deployment, unlike full-page-load metrics which require traffic stabilization and confound multiple optimization efforts. It provides an early success signal for deployment.

### 1.3 Streaming Throughput on Lossy Networks

Akamai measured that during a live-streaming event popular in Latin America, 69% of HTTP/3 connections sustained 5 Mbps (Netflix's Full HD minimum threshold) versus 56% of HTTP/2 connections [OBSERVED][HIGH]. Since streaming revenue correlates with video quality delivered to customers, this translates directly to revenue impact by geography.

| Scenario | HTTP/2 Performance | HTTP/3 Performance | Improvement |
|----------|-------------------|-------------------|-------------|
| 0% loss, 0ms delay | ~9 sec (10MB) | ~9 sec (10MB) | 0% |
| 1% loss | ~5% degradation | 5% degradation | ~0% |
| 5% loss | 30%+ degradation | 30–50% faster than H2 | **30–50%** |
| 4% loss + 50ms latency (default CCA) | 106 sec | 15 sec | **87%** |
| 4% loss + 50ms latency (BBR CCA) | 10 sec | 15 sec | 33% slower than H2+BBR |

---

## 2. The Network Condition Threshold: When HTTP/3 Matters

### 2.1 Simultaneous High Loss and High Latency Required

HTTP/3's performance advantage over HTTP/2 **requires both high packet loss and high latency to manifest simultaneously** [OBSERVED][HIGH]. At 0% packet loss (regardless of delay) or 0ms delay (regardless of loss), performance between the two protocols is comparable [OBSERVED][HIGH]. The advantage only emerges when both 4%+ packet loss and 50ms+ latency are present together.

This finding is critical for deployment strategy: **HTTP/3 investment in corporate LANs or low-loss networks yields no performance gain** [OBSERVED][HIGH]. Operators should deprioritize HTTP/3 deployments for clean networks and redirect engineering focus to lossy, high-latency paths where HTTP/3 provides measurable return.

### 2.2 The 2–5% Loss Threshold

HTTP/3 and HTTP/2 exhibit essentially identical performance under ideal network conditions, with HTTP/3's advantage not materializing until packet loss reaches 2–5% [OBSERVED][HIGH]. Below this threshold, HTTP/2 with proper configuration delivers equivalent results at lower operational complexity. The threshold where HTTP/3 becomes statistically justified is 2–5% packet loss, where HTTP/3 maintains approximately 80% throughput while HTTP/2 drops to approximately 50% [OBSERVED][HIGH].

### 2.3 Real-World Networks Exceeding This Threshold

Four specific network types in production-like settings exceeded 1% packet loss in 2023–2024 data [OBSERVED][MEDIUM]:

- **Congested Wi-Fi networks**: peaked at 5% UDP loss
- **Home routers**: experienced 10% bufferbloat-induced loss
- **IPv6 dual-stack protocol transitions**: caused 2% packet drops
- **Wireless spectrum interference** (ISM bands): resulted in 3% errors

Each represents a distinct root cause—QoS saturation, buffer tuning misconfiguration, dual-stack implementation issues, and spectrum contention—requiring targeted fixes rather than generic network remediation. This establishes that the 2–5% threshold is not theoretical; real networks regularly exceed it, making HTTP/3 a viable return-on-investment target for specific deployment segments.

---

## 3. The Technical Mechanism: Per-Stream Ordering and Head-of-Line Blocking

### 3.1 QUIC's Stream Isolation vs. TCP's Global Ordering

QUIC's per-stream ordering means a lost packet pauses **only the affected stream** while others continue; TCP's global ordering stalls **everything** [VERIFIED][HIGH]. On a 5% loss network, this lets you measure which content or paths experience loss independently—TCP would obscure this by blocking all concurrent streams simultaneously.

Three independent sources confirm this mechanism is responsible for 30–50% faster page loads at 5% loss and 5–15% improvement at 1% loss [VERIFIED][HIGH]. The operational consequence is that you can identify and isolate lossy network segments by monitoring which application streams stall, enabling targeted remediation before page loads degrade.

### 3.2 Protocol-Independent Performance Under Severe Conditions

Under severe network conditions (4% packet loss, 50ms latency), HTTP/3 achieved 88.36% performance improvement independent of congestion control algorithm or proxy configuration [DERIVED][HIGH], while HTTP/2 required specific algorithm selection (BBR) and proxy deployment to achieve 90% improvement. This means HTTP/3 delivers near-equivalent performance gains **without infrastructure-specific optimization work**, allowing simpler deployments.

In contrast, HTTP/2's performance variability across different network conditions stems primarily from congestion control algorithm choice, not protocol design [OBSERVED][HIGH]. This is both a weakness (requiring tuning to achieve parity) and an opportunity (tuning can close the gap substantially before migrating to HTTP/3).

---

## 4. The HTTP/2 Optimization Path: A Lower-Cost Alternative

### 4.1 Congestion Control as the Primary Lever

At 4% loss and 50ms latency, HTTP/2 with BBR completed downloads in 10 seconds (90% improvement over no proxy), while CUBIC and NewReno showed no such gain [OBSERVED][HIGH]. Yet HTTP/3 maintained consistent performance regardless of CCA. This reveals that HTTP/2 can approach HTTP/3 performance on lossy paths through algorithmic tuning.

**Implication**: Performance regressions after HTTP/2 deployment should be traced to CCA misconfiguration before assuming protocol inadequacy. Organizations can **decide whether to migrate from HTTP/2 to HTTP/3 by first auditing their H2 stack's congestion control algorithm**, potentially recovering 50% of the performance gap at lower migration cost [OBSERVED][HIGH].

### 4.2 When HTTP/2 Tuning Is Sufficient

In zero-loss environments, HTTP/2 can match QUIC because TCP overhead is minimal [OBSERVED][HIGH]. Stop deploying HTTP/3 universally and instead target it to networks where packet loss exceeds 2%, because the protocol advantage disappears entirely under ideal conditions [OBSERVED][HIGH]. For networks with acceptable loss profiles and proper congestion control tuning, HTTP/2 remains a viable, lower-complexity choice.

---

## 5. The Operational Cost of HTTP/3: Userspace Implementation and Deployment

### 5.1 CPU Overhead and Deployment Topology

HTTP/3's 15–20% additional CPU per connection becomes an unjustified cost on fiber-based origin-to-origin links [DERIVED][HIGH]. HTTP/3's 15–30% latency improvement on mobile networks concentrates on the first-mile link to the CDN edge where packet loss (2–5%) and latency (200ms+) are endemic. Behind the CDN, origin-to-edge traffic typically runs on fiber with near-zero loss, where HTTP/2 optimization is sufficient.

**Deployment implication**: Route HTTP/3 through your CDN edge rather than your origin servers, because the latency and multiplexing advantage is measurable only on high-loss or high-latency paths between client and network edge [DERIVED][HIGH].

### 5.2 Userspace Congestion Control: An Operational Advantage

QUIC's userspace implementation lets you ship congestion-control algorithm updates (BBR v3, CUBIC) via application deployment without kernel patches or system reboots [VERIFIED][HIGH]. Google deployed BBR v3 to Chrome and their edge servers in 2023 without requiring OS updates; this decouples improvement iteration from the kernel release cycle.

The operational consequence is that you can **deploy transport-layer protocol improvements to your fleet in days instead of months** by updating userspace libraries rather than waiting for OS kernel releases [VERIFIED][HIGH]. This is a long-term advantage that accrues over years of operation, though it requires accepting the initial CPU overhead and monitoring complexity.

---

## 6. Infrastructure and Regulatory Barriers: Why Adoption Is Stalled

### 6.1 Firewall and Network Perimeter Limitations

Major firewall vendors publicly recommend disabling QUIC on production networks because the required UDP/TLS termination demands high CPU or ASIC costs with degradation risks [VERIFIED][MEDIUM]. Rather than ship working solutions, vendors bet that automatic browser fallback to HTTP/2 will absorb the impact—making infrastructure-level QUIC adoption indefinitely stalled.

Many vendors recommend disabling QUIC entirely, as browsers will automatically fall back to HTTP/2 over TCP [VERIFIED][MEDIUM]. This creates a silent penalty: operators deploy HTTP/3 on their edge servers, but the traffic is intercepted and downgraded at the network perimeter without visibility or control.

### 6.2 TLS Inspection and Compliance Requirements

Enterprises with mandatory TLS inspection (compliance auditing, DLP) are disabling HTTP/3 on specific applications by configuring browsers to fall back to TCP [DERIVED][MEDIUM]. Operators report this "degrades web performance and breaks service provider SLAs," but compliance visibility outweighs speed—creating a dual-mode network where critical traffic stays on TCP while non-critical traffic runs HTTP/3.

You can **enforce HTTP/2-only on compliance-critical applications without affecting your broader network**, treating HTTP/3 disablement as a fine-grained policy tool rather than a universal requirement [DERIVED][MEDIUM].

### 6.3 Kubernetes Ecosystem Abandonment

Ingress-Nginx, used by most Kubernetes deployments, dropped all HTTP/3 development in favor of a complete architectural redesign that has not yet shipped [DERIVED][MEDIUM]. Organizations using standard Kubernetes have no HTTP/3 path for service-to-service communication—forcing either multi-year delays, adoption of non-standard controllers, or permanent TCP infrastructure [DERIVED][MEDIUM].

This is a hard blocker for container-native environments: the ecosystem's dominant controller has abandoned the work, leaving no clear migration path for Kubernetes-based services.

---

## 7. Regional and Market-Specific ROI

### 7.1 High-Loss, High-Latency Markets Drive Returns

Akamai's measurement during a popular live-streaming event in Latin America (69% of HTTP/3 connections sustaining 5 Mbps vs. 56% of HTTP/2) [OBSERVED][HIGH] demonstrates that regional deployment can be optimized by identifying which markets have endemic packet loss and latency problems. Wix's 250ms+ improvements in the Philippines [OBSERVED][HIGH] show that emerging markets with mobile-first user bases see outsized returns.

**Implication**: You can commit to lower tail-latency SLAs for mobile users in high-loss regions by routing that traffic to QUIC instead of HTTP/2 [OBSERVED][HIGH]. Regional rollout focused on high-loss geographies maximizes ROI per deployment dollar.

### 7.2 Revenue Impact Forecasting

Since streaming revenue correlates with video quality delivered to customers, operators can now predict which markets will see revenue degradation based on their user base's protocol support distribution [OBSERVED][HIGH]. Set HTTP/3 rollout success metrics by measuring connection latency gains instead of waiting for full-page-load convergence [OBSERVED][HIGH].

---

## 8. Synthesis: Decision Framework

| Decision Point | Finding | Implication |
|---|---|---|
| **Your network has <2% packet loss** | HTTP/3 offers no measurable advantage over optimized HTTP/2 [OBSERVED][HIGH] | Deploy HTTP/2 with BBR tuning; deprioritize HTTP/3 |
| **Your network has 2–5% sustained packet loss** | HTTP/3 delivers 30–50% faster page loads [OBSERVED][HIGH] | HTTP/3 ROI threshold met; target CDN edge deployment [DERIVED][HIGH] |
| **Your CDN is on fiber, origin-to-origin is the path** | 15–20% CPU overhead with minimal performance gain [DERIVED][HIGH] | Keep HTTP/2 on origin; use HTTP/3 only at edge |
| **Firewall cannot inspect QUIC cost-effectively** | Vendors recommend disabling; traffic silently downgrades [VERIFIED][MEDIUM] | Assume perimeter will downgrade; validate with tests before committing to HTTP/3 investment |
| **Kubernetes is your primary infrastructure** | Ingress-Nginx abandoned HTTP/3; no clear path forward [DERIVED][MEDIUM] | Accept TCP-based networking; revisit in 2–3 years when successor stabilizes |
| **Compliance requires TLS inspection** | HTTP/3 is disabled for compliance-critical applications [DERIVED][MEDIUM] | Use fine-grained policy to disable HTTP/3 only for sensitive traffic |
| **You operate in high-loss mobile markets** | 250ms+ latency improvements, 30–50% page-load gains [OBSERVED][HIGH] | Target HTTP/3 rollout to regions; forecast revenue impact by adoption rate [OBSERVED][HIGH] |

---

## 9. Research Gaps and Honest Limitations

### 9.1 Limited Multi-Protocol Comparison at 1% Loss

Evidence for HTTP/3 vs. HTTP/2 at exactly 1% loss exists but is sparse. The most detailed measurements report either 1% loss (showing 30%+ H2 degradation and ~5% H3 degradation) [OBSERVED][HIGH] or 4–5% loss (showing 30–50% advantage). The 1–2% range—where many production networks actually operate—has limited independent verification.

### 9.2 Unclear Duration of Loss Events

Field measurements report sustained packet loss rates but do not clarify whether loss occurs in bursty patterns (milliseconds of correlated drops) or randomly distributed. Bursty loss may favor HTTP/3 even more; random loss patterns might narrow the advantage. This distinction is operationally important for predicting real-world returns.

### 9.3 Incomplete Cost-Benefit Analysis for CPU Overhead

The 15–20% CPU overhead of userspace QUIC is stated as a deployment fact [DERIVED][HIGH], but we lack detailed measurements of total cost of ownership (infrastructure expansion, cooling, operational complexity) when deploying HTTP/3 at scale. This matters for capital budgeting decisions.

### 9.4 Firewall Testing in Real Networks

The finding that major vendors recommend disabling QUIC is documented [VERIFIED][MEDIUM], but specific vendor-by-vendor guidance and the prevalence of this practice in production networks is not quantified. Operators need clearer visibility into whether HTTP/3 will survive their perimeter without independent testing.

### 9.5 HTTP/2 Congestion Control Tuning Studies

Most evidence for HTTP/2 recovery with BBR comes from controlled lab experiments [OBSERVED][HIGH], not production deployments. Whether real-world infrastructure can achieve and maintain BBR tuning consistently across fleets is unclear.

---

## 10. Recommendations

1. **Audit congestion control algorithms on all HTTP/2 deployments before committing to HTTP/3 migration.** Recovery of 50% of the performance gap through BBR tuning is lower-risk and lower-cost than infrastructure migration [OBSERVED][HIGH].

2. **Deploy HTTP/3 selectively to CDN edge infrastructure serving high-loss geographies (>2% measured packet loss).** Measure regional performance gains before rolling out globally; focus on markets with mobile-first user bases [OBSERVED][HIGH] [DERIVED][HIGH].

3. **Disable HTTP/3 at firewall perimeter only after independent testing confirms your vendor's inspection capabilities.** Assume silent downgrade to HTTP/2 until proven otherwise; validate with packet captures [VERIFIED][MEDIUM].

4. **For Kubernetes-native infrastructure, accept TCP-based networking and revisit HTTP/3 adoption after 2–3 years when Ingress-Nginx successor stabilizes.** Do not block on HTTP/3 for infrastructure decisions today [DERIVED][MEDIUM].

5. **Enforce fine-grained policy to disable HTTP/3 only for compliance-critical applications requiring TLS inspection**, rather than disabling universally [DERIVED][MEDIUM].

6. **Measure HTTP/3 success on connection setup latency (33% improvements observed [OBSERVED][HIGH]) rather than full-page-load metrics, allowing faster iteration feedback** [OBSERVED][HIGH].

---

## Conclusion

HTTP/3 (QUIC) delivers measurable, substantial performance improvements over HTTP/2 in high-loss, high-latency environments typical of mobile networks in developing regions, with 30–50% page-load improvements at 5% packet loss and 5–15% gains at 1% loss [OBSERVED][HIGH]. The mechanism is QUIC's per-stream ordering, which eliminates TCP's head-of-line blocking [VERIFIED][HIGH]. However, this advantage exists **only in specific network conditions** (simultaneous high loss and high latency [OBSERVED][HIGH]) and is currently blocked by infrastructure constraints (firewall inspection costs [VERIFIED][MEDIUM], Kubernetes abandonment [DERIVED][MEDIUM], compliance requirements [DERIVED][MEDIUM]).

The optimal deployment path is not universal HTTP/3 adoption, but targeted rollout to high-loss edges while treating HTTP/2 optimization (particularly congestion control tuning) as the immediate, lower-cost alternative for most networks [OBSERVED][HIGH] [DERIVED][HIGH]. Organizations should first audit HTTP/2 configuration, measure their own packet loss profiles, and test HTTP/3 at the perimeter before committing capital to migration.

## Contradicciones detectadas (3)

Los conflictos siguientes se reportan SIN resolver, a propósito. Elegir un ganador en silencio sería inventar una certeza que las fuentes no dan.

**CONTRADICCIÓN** — Fuente [4] afirma: At 1% packet loss, HTTP/3 maintains performance within 5% of baseline while HTTP/2 experiences 30%+ degradation. · Fuente [10] afirma: HTTP/3 advantage does not materialize until packet loss reaches 2–5%.
El conflicto NO está resuelto. Explicación probable: distinta metodología de medición (METHODOLOGY).
Para el operador: These measurements identify incompatible thresholds for when HTTP/3 provides advantage; determine whether differences result from testing under different network conditions (production vs. synthetic), different traffic types, or different protocol implementations.

**CONTRADICCIÓN** — Fuente [3] afirma: HTTP/3 advantage requires both 4%+ packet loss AND 50ms+ latency simultaneously; neither condition alone is sufficient. · Fuente [4] afirma: At 1% packet loss in a production API gateway, HTTP/3 provides substantial performance advantage over HTTP/2.
El conflicto NO está resuelto. Explicación probable: distinto contexto (CONTEXT).
Para el operador: [3] specifies 4%+ loss as a minimum threshold, but [4] demonstrates clear advantage at 1%; if [4]'s production deployment includes the 50ms+ latency specified in [3], the threshold conflict cannot be reconciled.

**CONTRADICCIÓN** — Fuente [3] afirma: Packet loss threshold for HTTP/3 advantage is 4%+ (additionally requiring 50ms+ latency to be co-present). · Fuente [10] afirma: Packet loss threshold for HTTP/3 advantage is 2–5%.
El conflicto NO está resuelto. Explicación probable: distinta metodología de medición (METHODOLOGY).
Para el operador: At 3% loss with realistic latency, these claims conflict: [3] predicts comparable performance while [10] predicts HTTP/3 advantage; verify whether experiments differed in measurement methodology, network simulation parameters, or baseline assumptions.

## Sources

- <https://pulse.internetsociety.org/en/blog/2023/07/measuring-http-3-real-world-performance/>
- <https://arxiv.org/html/2409.16267v2>
- <https://arxiv.org/pdf/2409.16267>
- <https://performate.app/en/blog/http2-http3-load-testing-latency>
- <https://www.logicmonitor.com/deep-dive/http3-vs-http2/introduction>
- <https://kiwee.eu/blog/http-3-how-it-performs-compared-to-http-2/>
- <https://www.streamingmeme.com/articles/deep-dive-into-quic-stream-multiplexing-eliminating-head-of-line-blocking-for-high-performance-networking-martinuke0s-blog>
- <https://arxiv.org/pdf/2511.08375>
- <https://martinuke0.github.io/posts/2026-09-07-inside-quic/>
- <https://iotdigitaltwinplm.com/quic-http3-protocol-deep-dive-handshake-streams-loss-recovery-congestion-control-2026/>
- <https://www.logicmonitor.com/deep-dive/http3-vs-http2/quic-vs-tcp>
- <https://www.dev-toolbox.tech/tools/http-protocol-comparison/examples/http3-loss-recovery>
- <https://worldmetrics.org/network-state-statistics/>
- <https://www.microsoft.com/en-us/research/wp-content/uploads/2019/07/regionalloss.pdf>
- <https://www.reddit.com/r/networking/comments/fi186x/major_packet_loss_to_certain_geographical_regions/>
- <https://arxiv.org/html/2409.16267v3>
- <https://distribute.com.au/2026/09/01/http2-vs-http3/>
- <https://thecodeforge.io/cs-fundamentals/http2-http3/>
- <https://en.wikipedia.org/wiki/HTTP/3>
- <https://enterprise-browser-watch.contentwave.net/article/quic-http3-in-enterprise-browsers-strategies-to-restore-visibility>
- <https://panelica.com/blog/http2-vs-http3-quic-what-changes-for-your-server-2026>
- <https://blog.apnic.net/2023/10/23/the-challenges-ahead-for-http-3/>
- <https://httptoolkit.com/blog/http3-quic-open-source-support-nowhere/>

## Run metadata

- **Prompt:** How much does HTTP/3 (QUIC) reduce page load time or latency compared with HTTP/2, especially on lossy mobile networks, according to measured studies?
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 12)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 1274.1 s
- **Errors during run:** 10
- **Started at:** 2026-11-11T17:19:37Z
- **Module version:** deep_research 0.3.1
- **Quality gates:** 1 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 0 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 1 axis/axes covered (EVIDENCE) — minimum 3; missing: MECHANISM, BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY; only 1 axis/axes covered (COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, TRANSFERABILITY
- **E2 landscape:** A_MEASURED×2, B_ACADEMIC×6, C_PRACTITIONER×8, D_VENDOR×1, UNKNOWN×9 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** OBSERVED 9, VERIFIED 3, DERIVED 4 · 2 label(s) demoted by the evidence gates
- **E4 contradictions:** 3 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `COVERED` / HIGH [EVIDENCE] — 3 source(s), families A_MEASURED, B_ACADEMIC — _What independent measurements and published studies have quantified the page load time and_
- `COVERED` / HIGH [BOUNDARY] — 5 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _At what packet loss or latency threshold does HTTP/3's performance advantage over HTTP/2 d_
- `COVERED` / HIGH [MECHANISM] — 5 source(s), families B_ACADEMIC, C_PRACTITIONER, D_VENDOR, UNKNOWN — _Why does QUIC's connection establishment and loss recovery approach reduce page latency co_
- `THIN` / MEDIUM [EVIDENCE] — 3 source(s), families A_MEASURED, UNKNOWN — _Which of our geographic regions and network types experience packet loss rates above one p_
- `COVERED` / HIGH [BOUNDARY] — 5 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _At what packet loss rates and network latency levels does HTTP/3's latency advantage over _
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _Which organizations have deprioritized or reversed HTTP/3 deployments in production, and w_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://www.sciencedirect.com/science/article/pii/S014036642...': page-fetch: https://www.sciencedirect.com/science/article/pii/S0140366422000421: HTTP Error 403: Forbidden`
- `fetch_page 'https://dl.acm.org/doi/10.1145/3308558.3313606...': page-fetch: https://dl.acm.org/doi/10.1145/3308558.3313606: HTTP Error 403: Forbidden`
- `decomposition narrow: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `decomposition narrow: only 1 axis/axes covered (EVIDENCE) — minimum 3; missing: MECHANISM, BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY`
- `query rejected (not a question): 'What is the geographic and network-type distribution of pack' — contains code punctuation — not something a human types`
- `fetch_page 'https://www.thousandeyes.com/blog/internet-report-packet-los...': page-fetch: https://www.thousandeyes.com/blog/internet-report-packet-loss-impacts: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1010)>`
- `fetch_page 'https://www.thousandeyes.com/blog/path-quality-surprising-im...': page-fetch: https://www.thousandeyes.com/blog/path-quality-surprising-impact-one-percent-packet-loss: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1010)>`
- `decomposition narrow: only 1 axis/axes covered (COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, TRANSFERABILITY`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`

</details>
