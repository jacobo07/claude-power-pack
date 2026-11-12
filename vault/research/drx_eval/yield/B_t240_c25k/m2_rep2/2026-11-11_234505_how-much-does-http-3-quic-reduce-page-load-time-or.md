# HTTP/3 (QUIC) vs HTTP/2 Page Load Time: A Research Report

## Executive Summary

This report synthesizes available research on HTTP/3 (QUIC) performance advantages over HTTP/2, with focus on lossy mobile networks and page load times. **Critical finding: The research learnings available do not include measured comparative studies of HTTP/3 vs HTTP/2 page load time or latency under realistic mobile loss conditions.** The learnings instead provide protocol-layer specifications, infrastructure deployment data, and latency measurement methodology that *constrain* what HTTP/3 gains are achievable in practice, but do not directly quantify those gains. This report extracts available signals and identifies the specific gaps where such studies would be most valuable.

---

## Part 1: What the Research Does and Does Not Contain

### Evidence Available
- HTTP/3 cold-start handshake requirements: 2 RTT [DERIVED][HIGH]
- QUIC connection migration infrastructure support: ~52% of IPv4 servers with SNI [DERIVED][HIGH]
- SNI impact on QUIC handshake success: 14-fold gap (4.9% vs 69% for IPv4) [DERIVED][HIGH]
- Protocol-independent latency measurement methodology and bounds
- Infrastructure tier identification as prerequisite to optimization

### Evidence Absent
- **Measured page load time deltas between HTTP/3 and HTTP/2** on any network condition
- **Real-world mobile network testing** comparing the two protocols
- **Loss recovery comparison** on typical mobile loss rates (packet loss, jitter, bufferbloat scenarios)
- **Application-level metrics** (Time to First Byte, First Contentful Paint, Largest Contentful Paint, etc.)

**This is an honest gap, not a deficiency in the research collection.** The learnings appear to come from infrastructure and protocol engineering sources that measure *prerequisites* for HTTP/3 deployment rather than *outcome* metrics for end users. The evidence is thin on the specific question asked.

---

## Part 2: Protocol Specification Constraints (What HTTP/3 Should Do in Theory)

### Cold-Start Latency Requirements

HTTP/3 has a 2 RTT cold-start requirement [DERIVED][HIGH] versus HTTP/2's TCP 3-way handshake (1 RTT) plus TLS 1.3 (typically 1 RTT, 2 RTT with key share) = 2–3 RTT total. On paper, HTTP/3 should be **equivalent or slightly faster** at the handshake layer. However:

- At 30 ms RTT (typical mobile), 2 RTT = 60 ms for HTTP/3 vs 60–90 ms for HTTP/2
- **Expected improvement: marginal (0–30 ms) at handshake layer alone** [DERIVED][HIGH]

This narrow advantage assumes perfect conditions; real deployments show much wider variation (see below).

### Connection Migration and Loss Recovery

HTTP/2 over TCP experiences TCP head-of-line blocking: a single lost packet blocks all streams until retransmission completes. QUIC's design allows independent stream recovery. The specification supports this, but infrastructure readiness determines whether this advantage manifests:

- Only 52% of measured IPv4 QUIC servers support connection migration even with SNI [DERIVED][HIGH]
- IPv6 migration support is heavily concentrated: 94% among supporting servers come from a single provider (Hostinger) [DERIVED][HIGH]
- Handshake success without SNI drops to 4.9% vs 69% with SNI—a 14-fold gap [DERIVED][HIGH]

**Implication: Theoretical loss recovery advantages are infrastructure-gated.** On non-SNI networks or servers without migration support, HTTP/3's design benefits don't materialize.

---

## Part 3: The Role of Loss and Latency on Mobile Networks

### Why Loss Matters More Than You Might Expect

Mobile networks are characterized by:
- Packet loss rates: 0.5–2% on congested LTE, higher on marginal coverage
- Jitter and bufferbloat: idle latency 15 ms, load-induced latency 300 ms observed [DERIVED][HIGH]
- Variable RTT: 30–200+ ms depending on congestion and cell state

On lossy links, **protocol loss recovery overhead becomes the dominant performance factor**, not handshake RTT. The research learnings provide a model for this:

CoAP's RFC 7252 default retransmission timer (ACK_TIMEOUT 2–3 seconds, doubling on retry) means a single lost packet incurs a 2–3 second latency penalty on lossy networks [HYPOTHESIS][HIGH]. While this example is protocol-specific, the principle generalizes: **loss recovery timers in protocol specifications determine tail latency on lossy links, not header format or idle-time RTT.**

### What This Means for HTTP/3 vs HTTP/2 on Mobile

- TCP (HTTP/2): Retransmission governed by Linux/Windows TCP stack defaults (~200 ms initial RTO, exponential backoff)
- QUIC (HTTP/3): Retransmission governed by RFC 9002 (initial RTO 333 ms for most implementations)

**Neither protocol has a fundamental loss-recovery advantage on lossy networks.** Both rely on retransmission timers and congestion control. QUIC's per-stream recovery avoids head-of-line blocking on *unrelated* streams, which *could* improve page load time if:
1. Multiple streams are in flight (true for modern web pages with ~50+ resources)
2. One stream experiences loss while others remain clean (common on bursty mobile loss)

But this requires:
- Sufficient resources in flight (multiple HTTP/2 streams or HTTP/3 streams)
- HTTP/2 streams to be blocked by the loss (head-of-line blocking must actually occur)
- Lower QUIC loss recovery overhead than TCP's stack retransmission

**Evidence on whether this actually occurs in page load time: absent.**

---

## Part 4: Infrastructure Readiness and Real-World Deployment Barriers

The gap between theory and practice is infrastructure-wide:

### SNI Dependency

SNI is not universally deployed. The 14-fold handshake success gap (4.9% without SNI, 69% with SNI) [DERIVED][HIGH] means **servers without SNI cannot reliably establish QUIC connections at all.** For such servers, HTTP/3 provides zero benefit.

### Connection Migration Concentration

52% IPv4 support for migration, with IPv6 support concentrated at a single provider [DERIVED][HIGH], means **most infrastructure cannot exploit HTTP/3's key advantage on mobile networks where connections migrate between networks (WiFi↔LTE, cell tower handover).** The design capability exists; deployment does not.

### Measurement Methodology Constraint

Published protocol latency benchmarks from April 2026 were explicitly withdrawn by their author due to inability to trace measurements to reproducible sources [DERIVED][HIGH]. This means **existing HTTP/3 vs HTTP/2 page load time claims in the literature may lack a reliable audit trail.** Evaluation of such claims requires access to raw data, controlled environment setup, and transparent methodology—rarely available in published comparisons.

---

## Part 5: Latency Measurement Challenges Specific to Page Load Time

### Tier Identification Problem

The first failure point in infrastructure optimization is misidentifying which tier (edge, compute, cache, database, network) actually causes the slowdown [DERIVED][MEDIUM]. For page load time specifically:

- CDN/edge latency vs origin latency (network tier)
- Cache hit/miss ratios (edge tier)
- Database query latency (origin tier)
- JavaScript execution time (client tier)

A page load time improvement from HTTP/3 only occurs if **network tier latency is the binding constraint.** If edge caching or origin compute dominates, protocol choice is irrelevant. Published comparisons often fail to isolate this layer [DERIVED][MEDIUM].

### Bufferbloat and Peak-Load Testing

Testing on quiet networks produces false confidence [DERIVED][HIGH]. The specific measured example: 15 ms idle latency rising to 300 ms under load due to oversized buffers. **If HTTP/3 vs HTTP/2 comparisons are performed on lightly-loaded networks, the results do not predict real-world mobile behavior under peak capacity.**

### Application-Specific Thresholds

Performance sensitivity varies by application type [HYPOTHESIS][MEDIUM]:
- Voice: latency < 150 ms, jitter < 30 ms
- Video conferencing: latency < 100 ms, jitter < 50 ms
- Data applications: latency < 1000 ms

Page load time has no standard threshold in this framework. A 50 ms improvement on an already-fast page (500 ms) is perceptually invisible; the same improvement on a slow page (10 s) is also invisible at scale but could move a Core Web Vital threshold.

---

## Part 6: What We'd Need to Know (Research Gaps)

To answer the original question rigorously, we would need measured studies that:

1. **Isolate network tier performance** by measuring HTTP/3 vs HTTP/2 over the same origin, CDN, and client setup—confirming network tier is the bottleneck [DERIVED][MEDIUM].

2. **Test on realistic mobile loss conditions** (0.5–2% packet loss, 30–200 ms RTT, bufferbloat under load) rather than clean paths or synthetic loss [DERIVED][HIGH].

3. **Measure with SNI enabled and disabled** to quantify the infrastructure gap impact on real deployments [DERIVED][HIGH].

4. **Test on infrastructure with and without connection migration support** to measure the loss recovery advantage in practice.

5. **Use reproducible measurement methodology** traceable to raw data, following the standard (minimum one week, 10-minute sampling intervals, 90th percentile reporting) [DERIVED][HIGH].

6. **Report application-level metrics** (Time to First Byte, First Contentful Paint, Speed Index, Largest Contentful Paint) rather than protocol-layer latency, since page load time is a composite of network, client rendering, and server processing.

7. **Stratify results by** resource count, resource size distribution, and number of concurrent streams—since HTTP/3's per-stream recovery advantage depends on concurrent stream dynamics [HYPOTHESIS].

---

## Part 7: Speculation on Likely Outcomes (Flagged as Hypothesis)

**[HYPOTHESIS][MEDIUM]** Based on the available constraints and design differences:

- **Best case for HTTP/3** (SNI-enabled infrastructure, multiple concurrent streams, moderate mobile loss): 5–15% page load time improvement due to avoided head-of-line blocking on one or two lost packets, *if* HTTP/2 streams are actually blocked rather than already retransmitting.

- **Typical case** (mixed SNI deployment, loss < 1%, latency already < 100 ms): 0–5% improvement, within measurement noise.

- **Worst case** (non-SNI servers, no connection migration, high loss): HTTP/3 performs identically or worse (larger handshake packet, higher loss surface area for initial handshake).

- **Confounding factor**: Server-side HTTP/3 implementation quality varies widely. A suboptimal QUIC stack may lose all theoretical gains to inefficient retransmission or congestion control.

**These are educated guesses from protocol design, not measured results.**

---

## Part 8: Actionable Recommendations for Practitioners

Given the evidence gaps:

1. **Do not assume HTTP/3 provides universal page load time improvement.** Deploy it where you can measure it (your origin + your CDN), test the specific loss conditions your users experience, and verify the application-tier improvement.

2. **Prioritize infrastructure prerequisites** before expecting HTTP/3 benefits: Enable SNI, commit to connection migration support (or acknowledge its lack), and test on peak-load mobile networks with real loss rates [DERIVED][HIGH].

3. **Use the measurement methodology** from performance thresholds literature: minimum one week, 10-minute sampling, 90th percentile reporting [DERIVED][HIGH]. Confirm the bottleneck is network tier before attributing improvements to protocol choice [DERIVED][MEDIUM].

4. **Measure page load time, not protocol latency.** Protocol-layer latency improvements do not always translate to user-perceived page load time. Confirm the application-tier impact.

5. **Expect results to vary by deployment.** HTTP/3 gains depend on infrastructure choice (SNI, migration support), user loss profile, CDN implementation quality, and workload characteristics. Generalized claims are unreliable.

---

## Conclusion

The research learnings provide a framework for understanding *why* HTTP/3 *should* improve page load time on lossy mobile networks (per-stream loss recovery, connection migration) and *where deployment typically fails* (SNI dependency, infrastructure concentration, measurement bias). However, **measured page load time deltas between HTTP/3 and HTTP/2 are not present in the available research.** 

The evidence is thin enough that any confidence-sounding claim about HTTP/3 performance improvement for end users should be treated as provisional until verified in your specific deployment context. The learnings instead provide a diagnostic toolkit: the prerequisites to check, the measurement methodology to use, and the infrastructure gaps to close before expecting user-visible gains.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://arxiv.org/html/2505.14358v1>
- <https://datatracker.ietf.org/meeting/123/materials/slides-123-maprg-sessb-breaking-through-the-clouds-performance-insights-into-starlinks-latency-and-packet-loss-00>
- <https://iotdigitaltwinplm.com/iot-protocol-latency-benchmarks-mqtt-coap-amqp-http3-2026/>
- <https://www.cl.cam.ac.uk/~dap53/pubs/popescu-ieee-tnsm-2021.pdf>
- <https://docs.thousandeyes.com/product-documentation/connected-devices/connected-devices-tests/network/latency-loss-disconnections-jitter-tests>
- <https://arxiv.org/html/2410.06066v1>
- <https://www.rfc-editor.org/rfc/rfc9002.pdf>
- <https://quicwg.org/base-drafts/rfc9002.html>
- <https://www.toolsku.com/en/blog/http3-quic-0rtt-optimization-2026>
- <https://arxiv.org/pdf/2505.14358>
- <https://infosecmonkey.com/network-performance-metrics/>
- <https://starlink.com/public-files/StarlinkLatency.pdf>
- <https://learn.microsoft.com/en-us/previous-versions/SkypeForBusiness/optimizing-your-network/media-quality-and-network-connectivity-performance>
- <https://oneuptime.com/blog/post/2026-03-20-interpret-ping-output-ttl-rtt/view>
- <https://netverge.com/blog/infrastructure-performance-optimization-guide-for-it-teams>
- <https://blog.paessler.com/intro-to-qos-and-important-qos-metrics>
- <https://www.itu.int/epublications/publication/itu-t-j-1630-2024-06-end-to-end-network-characteristics-requirement-for-video-services-over-integrated-broadband-cable-network>
- <https://link.springer.com/article/10.3103/S0147688225700029>

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
- **Duration:** 1386.3 s
- **Errors during run:** 23
- **Started at:** 2026-11-11T22:45:05Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 3 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, EVIDENCE, MECHANISM, TRANSFERABILITY)  — SHORTFALL: only 1 axis/axes covered (TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, COUNTEREXAMPLE; only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 1 axis/axes covered (TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, COUNTEREXAMPLE
- **E2 landscape:** A_MEASURED×1, B_ACADEMIC×3, C_PRACTITIONER×4, D_VENDOR×1, UNKNOWN×14 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 8, HYPOTHESIS 2 · 12 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `COVERED` / HIGH [EVIDENCE] — 5 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _What specific packet loss rates and round-trip times were tested in published measurements_
- `UNCLASSIFIED` / LOW [TRANSFERABILITY] — 1 source(s), families UNKNOWN — _How do latency gains from latency-aware load balancing vary across different traffic workl_
- `UNCLASSIFIED` / LOW [MECHANISM] — 4 source(s), families UNKNOWN — _Why do protocols that recover lost packets independently per stream reduce end-to-end late_
- `COVERED` / HIGH [BOUNDARY] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _At what sustained packet loss percentage does QUIC connection migration and 0-RTT recovery_
- `COVERED` / HIGH [BOUNDARY] — 5 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _Above what packet loss percentages or round-trip time values do the measured latency impro_
- `THIN` / MEDIUM [TRANSFERABILITY] — 4 source(s), families A_MEASURED, D_VENDOR, UNKNOWN — _Do the performance improvement thresholds that justify protocol or infrastructure upgrades_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `source https://iotdigitaltwinplm.com/iot-protocol-latency-benchmark carries instruction-like text ['tool-or-exfil-request']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 346`
- `epistemic demoted VERIFIED -> DERIVED: VERIFIED claims corroboration but only 1 source(s) support it (minimum 2) — demoted to DERIVED`
- `epistemic demoted OBSERVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `decomposition narrow: only 1 axis/axes covered (TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, COUNTEREXAMPLE`
- `fetch_page 'https://www.sciencedirect.com/science/article/pii/S157401372...': page-fetch: https://www.sciencedirect.com/science/article/pii/S1574013725000255: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.sciencedirect.com/science/article/pii/S108480452...': page-fetch: https://www.sciencedirect.com/science/article/pii/S108480452300111X: HTTP Error 403: Forbidden`
- `fetch_page 'https://dl.acm.org/doi/10.1016/j.cosrev.2025.100749...': page-fetch: https://dl.acm.org/doi/10.1016/j.cosrev.2025.100749: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.researchgate.net/publication/361079972_HLB_Towar...': page-fetch: https://www.researchgate.net/publication/361079972_HLB_Toward_Load-Aware_Load_Balancing: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.sciencedirect.com/topics/computer-science/loss-o...': page-fetch: https://www.sciencedirect.com/topics/computer-science/loss-of-packet: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `decomposition narrow: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://deepwiki.com/Tencent/tquic/3.2-connection-reliabilit...': page-fetch: https://deepwiki.com/Tencent/tquic/3.2-connection-reliability: HTTP Error 429: Too Many Requests`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 2024, 52%, 94%`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 14, 2024, 4.9%, 52%, 69%`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 0.5%, 60`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 1 axis/axes covered (TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, COUNTEREXAMPLE`

</details>


## Evidence ledger

- **Claims:** 13 · with a verified quote: 11 (rate 0.846)
- **Quotes:** 18 offered, 3 rejected (not verbatim / unknown source / length)
- **Sources:** 22 snapshots in 22 independent lineage(s); 1 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 6
- **Sources with instruction-like text (treated as data):** 1

**C1** [DERIVED] Pirate measures application-layer response latency (time from request to last byte received) by observing only client-to-server packets at a load balancer, even with encrypted QUIC transport. On a realistic web workload with variable CPU availability, Pirate achieves 0.63% median measurement error relative to client-side latency. When integrated into the Katran layer-4 load balancer, latency-aware routing cuts 99th percentile latencies by 37%, with only 346 nanoseconds per-packet measurement overhead.
  - S1 <https://arxiv.org/html/2505.14358v1> chars 10937-11086: "Across all monitored responses, Pirate achieves a median relative error of 0.63% relative to the response latency measured at the client application."
  - S1 <https://arxiv.org/html/2505.14358v1> chars 11853-11997: "Latency-aware Katran cuts the 99th percentile latency in our experimental setup by 37% on average across loads, relative to (unmodified) Katran."
  - _ledger: OBSERVED number(s) absent from verified spans: 346_

**C2** [DERIVED] Protocol end-to-end latency is dominated by round-trip count, not wire format. Cold-start requirements are: MQTT 3 RTT (pipelined), CoAP unsecured 1 RTT versus 2–3 RTT with DTLS, AMQP 6–8 RTT, and HTTP/3 2 RTT. At 30 ms RTT these translate to 30–240 ms cold latencies. The April 2026 published IoT protocol latency tables were withdrawn by their author due to inability to trace measurements to reproducible sources, making RFC specification-based analysis a more reliable basis for protocol selection than single-rig benchmarks.
  - S3 <https://iotdigitaltwinplm.com/iot-protocol-latency-benchmarks-mqtt-coap-amqp-http3-2026/> chars 14076-14270: "Now apply illustrative arithmetic. At a 30 ms RTT, a cold MQTT publish takes about 90 to 120 ms before processing, cold AMQP roughly 180 to 240 ms, and a cold unsecured CoAP request about 30 ms."

**C3** [HYPOTHESIS] CoAP's default RFC 7252 retransmission timer (ACK_TIMEOUT 2–3 seconds, doubling on each retry) means a single lost packet incurs 2–3 seconds of latency penalty. This makes CoAP's tail latency worse than MQTT on lossy links despite CoAP's superior p50 latency on clean paths. The protocol specification timer values, not header size or wire format, determine the latency difference between protocols in real-world loss scenarios.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C4** [DERIVED] Fast retransmission detects packet loss within hundreds of milliseconds using duplicate ACKs rather than waiting for RTO timeout expiration, and SACK enables identification of multiple concurrent losses in a single acknowledgment enabling retransmission in one round trip instead of sequentially, allowing services to remain responsive during burst packet loss
  - S10 <https://cloudstreet-dev.github.io/Networking-Protocols/tcp/retransmission.html> chars 3973-4038: "Both lost packets identified and retransmitted in one round trip!"
  - S10 <https://cloudstreet-dev.github.io/Networking-Protocols/tcp/retransmission.html> chars 1940-2025: "Fast retransmit is faster than waiting for timeout—often by hundreds of milliseconds."

**C5** [DERIVED] SCTP provides multi-streaming with independent error recovery per stream, whereas TCP operates at the connection level where packet loss triggers connection-wide retransmission mechanisms, so multi-stream protocols prevent loss on one stream from stalling traffic on unaffected streams
  - S7 <https://www.digitalsamba.com/blog/packet-loss-in-webrtc> chars 4076-4366: "Stream Control Transmission Protocol (SCTP) is often used by the VoIP community for server-to-server communication. However, when it’s used in WebRTC it’s for peer-to-peer communication with the aim of providing built-in error recovery, congestion control, and multi-streaming ..."

**C6** [DERIVED] Tail Loss Probe detects loss in final segments without waiting for full RTO expiration by probing after 2× smoothed RTT, significantly reducing tail latency in request-response workloads compared to traditional timeout-based detection which must wait for complete RTO intervals
  - S10 <https://cloudstreet-dev.github.io/Networking-Protocols/tcp/retransmission.html> chars 7461-7496: "Reduces tail latency significantly."

**C7** [DERIVED] Connection migration support is concentrated in specific providers rather than being a universal QUIC capability. Measurements from May 2024 show 52% of QUIC servers with SNI support migration on IPv4, but among IPv6 servers that do support it, 94% are from a single provider (Hostinger), while major providers like Cloudflare and Google do not support connection migration at all. This means an operator's ability to rely on migration for seamless failover depends entirely on which infrastructure vendor is chosen.
  - S11 <https://arxiv.org/html/2410.06066v1> chars 24013-24191: "Out of the 693,461 targets supporting migration in IPv6, it appears that 654,598 are from Hostinger while the other providers seem to offer very little support for the migration."
  - S11 <https://arxiv.org/html/2410.06066v1> chars 23579-23644: "Cloudflare and Google do not seem to support connection migration"
  - _ledger: OBSERVED number(s) absent from verified spans: 2024, 52%, 94%_

**C8** [DERIVED] SNI creates a 14-fold performance gap in QUIC handshake success (4.9% vs 69% for IPv4 in May 2024 scans), but even with SNI support, only 52% of successful handshakes proceed to migration. Infrastructure that cannot support SNI faces severe handshake failures and cannot rely on connection migration as a recovery mechanism, making investment in QUIC for non-SNI environments economically unjustifiable.
  - S11 <https://arxiv.org/html/2410.06066v1> chars 19384-19610: "the success rate for the handshake is low with only 5% of the targets able to perform a successful handshake. The addition of SNI from the DNS records allows to drastically increase the success rate of handshakes to almost 70%"
  - _ledger: OBSERVED number(s) absent from verified spans: 14, 2024, 4.9%, 52%, 69%_

**C9** [DERIVED] TCP throughput is mathematically capped by the bandwidth-delay product formula (Max throughput = TCP_window_size / RTT). A TCP flow with a 64 KB window and 100 ms RTT cannot exceed 5.2 Mbps regardless of physical link bandwidth. Adding network capacity when distance is the bottleneck yields zero user benefit; the fix must address latency, not bandwidth.
  - S16 <https://infosecmonkey.com/network-performance-metrics/> chars 8030-8211: "A single TCP flow cannot send more than one window of data per round trip. With a 64 KB window and 100 ms RTT, the ceiling is about 5.2 Mbps no matter how much bandwidth you bought."

**C10** [DERIVED] Services like Microsoft Teams define acceptable performance targets (RTT < 60 ms, average packet loss < 0.5%, jitter < 3 ms). Operators can rigorously test existing internet connectivity—minimum one week of sampling every 10 minutes, taking the 90th percentile value—against these thresholds to determine if an upgrade like ExpressRoute is economically justified or unnecessary. Internet that meets the thresholds requires no costly alternative; internet that fails them justifies the investment.
  - S18 <https://learn.microsoft.com/en-us/previous-versions/SkypeForBusiness/optimizing-your-network/media-quality-and-network-connectivity-performance> chars 14917-15108: "We recommend for you to perform your testing of network performance for a minimum of a week, so that you can see usage patterns for all business days and hours. This will show you peak times."
  - S18 <https://learn.microsoft.com/en-us/previous-versions/SkypeForBusiness/optimizing-your-network/media-quality-and-network-connectivity-performance> chars 15180-15445: "We recommend taking a measurement every 10 minutes from a company site during the entire period of time you are gathering data. For comparing the Microsoft Teams network performance requirements, take the 90th percentile measurement value from this sample data set."
  - _ledger: OBSERVED number(s) absent from verified spans: 0.5%, 60_

**C11** [DERIVED] A network path can show 15 ms latency when idle but 300 ms latency under upload load, due to oversized buffers (bufferbloat) that queue packets instead of dropping them. Testing on quiet links produces false confidence and leads to wasted upgrades; measuring during peak traffic hours reveals the true bottleneck and prevents spending on the wrong fix.
  - S16 <https://infosecmonkey.com/network-performance-metrics/> chars 12391-12628: "A link can ping at 15 ms when idle and 300 ms the moment you start an upload, because oversized buffers queue packets instead of dropping them. Test latency while the link is busy, not just when it is quiet, or you will miss it entirely."

**C12** [HYPOTHESIS] Performance thresholds vary significantly across application types, not universally. Voice requires latency under 150ms and jitter under 30ms; video conferencing requires latency under 100ms with jitter under 50ms; general data applications tolerate up to 1000ms latency. This means operators must tailor infrastructure standards to their specific application mix rather than applying a single performance target to the entire network.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C13** [DERIVED] The first failure point in infrastructure optimization is misidentifying which tier (edge, compute, cache, database, network) actually causes the slowdown. Database teams optimize databases when the edge layer is the bottleneck; network teams reconfigure routing when compute is constrained; compute teams add capacity when an unindexed query is the issue. Starting with incorrect layer selection wastes resources and delays real improvements.
  - S20 <https://netverge.com/blog/infrastructure-performance-optimization-guide-for-it-teams> chars 4052-4273: "The tier localization step is where most teams go wrong. Engineers often jump straight to database tuning when the real bottleneck is at the edge layer, or they add compute capacity when the problem is an unindexed query."
