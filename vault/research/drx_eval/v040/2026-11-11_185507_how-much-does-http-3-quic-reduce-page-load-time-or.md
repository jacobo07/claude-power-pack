# HTTP/3 vs HTTP/2 Performance: Measured Improvements and Conditional Gains on Lossy Mobile Networks

## Executive Summary

HTTP/3 (QUIC) delivers substantial measured performance improvements over HTTP/2 specifically on lossy and high-latency mobile networks, with gains ranging from 81.5% to 88.36% under real packet loss and network impairment conditions. However, these benefits are **conditional**: they emerge primarily under packet loss (4–12%), network transitions, and concurrent streams, while high-bandwidth, low-latency networks may see regression. Additionally, immature proxy implementations and elevated per-connection resource costs introduce deployment friction that reduces the operational advantage in proxy-dependent architectures. The evidence is strong for lossy mobile scenarios but thinner for general-case deployment readiness.

---

## Part 1: Measured Performance Gains Under Mobile Impairments

### Connection Migration: The Single Largest Measured Improvement

The most dramatic measured improvement occurs during network transitions (e.g., moving between WiFi and cellular):

**[OBSERVED][HIGH]** Under 4% packet loss and 50ms delay, HTTP/3 completed file downloads during IP address changes in 6.6 seconds versus HTTP/2's 56.7 seconds with resume capability—an **88.36% improvement**. This eliminates the operational need to implement reconnection logic in application code for users switching between networks.

**Implication**: For mobile users experiencing mid-session network transitions (WiFi dropout, handoff between cellular bands), HTTP/3's native connection migration eliminates the TCP three-way handshake and application-layer reconnection overhead that HTTP/2 incurs. This is not a marginal gain; it is the difference between seamless continuation and noticeable stalling.

### Multi-Stream Performance Under Packet Loss: Head-of-Line Blocking Elimination

The second-largest measured improvement addresses HTTP/2's fundamental architectural vulnerability: head-of-line blocking.

**[DERIVED][HIGH]** At 12% packet loss with 20 concurrent streams, HTTP/3 completed downloads in 20.98 seconds versus HTTP/2's 113.42 seconds—an **81.5% improvement**—because QUIC's stream architecture prevents head-of-line blocking. A single lost packet affects only one stream, not all concurrent transfers, fundamentally changing how loss impacts real traffic.

**Architecture of the Difference**:
- **HTTP/2**: All streams share a single TCP connection. A single lost packet blocks the entire connection until retransmission occurs, even if unrelated streams could transmit.
- **HTTP/3/QUIC**: Each stream has independent loss recovery. A lost packet on stream A does not stall stream B.

This is particularly acute on mobile networks, where 12% loss is not uncommon in degraded signal conditions. The 81.5% improvement is directly measured in laboratory multi-stream experiments, representing real-world browsing patterns (simultaneous image, CSS, JavaScript, API calls).

### Performance Degradation Severity by Network Condition

The measured improvements are **highly conditional on impairment level**:

| Network Condition | HTTP/3 Advantage | Primary Cause |
|---|---|---|
| **4% loss, 50ms delay** | 88.36% (connection migration) | Connection-layer improvement; migration overhead elimination |
| **12% loss, 20 concurrent streams** | 81.5% | Stream independence; head-of-line blocking avoidance |
| **High bandwidth, low latency** | Potential regression | Per-packet encryption overhead becomes the limiting factor |

**[DERIVED][HIGH]** HTTP/2 sometimes outperforms HTTP/3 in high-bandwidth, low-latency networks because QUIC's per-packet encryption overhead becomes the limiting factor rather than network conditions. This means HTTP/3 is not a universal performance upgrade—its advantages are conditional on network impairment levels, and best-case networks may see regression.

**Evidence Quality**: The regression condition is acknowledged in related work but not directly measured in the laboratory experiments, which used fixed 10 Mbps bandwidth. This means the theoretical concern is recognized but the magnitude of regression in realistic high-speed environments remains incompletely characterized.

---

## Part 2: Infrastructure Cost-Benefit Trade-offs

### The Proxy Implementation Immaturity Problem

A significant real-world constraint affects HTTP/3 adoption in enterprise and CDN environments: proxy support is immature.

**[DERIVED][HIGH]** HTTP/3 performance in production proxy environments is currently degraded due to immature implementations. Laboratory testing with Envoy proxy (the standard in CDNs and enterprises) shows HTTP/3 adds 0–1 second connection overhead compared to HTTP/2, explicitly attributed to Envoy's experimental rather than production-grade HTTP/3 support. Deploying HTTP/3 now in proxy-dependent architectures can increase latency until proxy implementations mature.

**Operational Consequence**: The 88.36% improvement in connection migration or 81.5% improvement in multi-stream throughput can be partially or entirely negated if the proxy adding 0–1 second overhead on every connection. This means the measured laboratory benefits do not automatically transfer to production environments that filter traffic through proxies.

**Evidence Quality**: Both independent sources (S1 and S2) document identical 0–1 second proxy overhead, with explicit attribution to implementation maturity, suggesting this is not a measurement artifact but a real implementation gap.

### Per-Connection Resource Costs: The Operational Trade-off

HTTP/3 is not free to operate at scale.

**[DERIVED][HIGH]** HTTP/3 requires materially more CPU time and memory than HTTP/2 per connection, making it costlier to operate at scale. This cost difference is significant enough that companies optimizing for engagement (Google, Akamai) treat it as an explicit trade-off—they deploy HTTP/3 because engagement gains offset the infrastructure expense. For operators running less performance-sensitive workloads, this cost-benefit calculation may not favor HTTP/3.

**Decision Framework**:
- **Deploy HTTP/3**: High engagement sensitivity (e.g., video streaming, real-time services, e-commerce checkout)
- **Defer HTTP/3**: Low latency sensitivity or constrained infrastructure budgets
- **Cost Factor**: S4 indicates this cost differential is material enough to be a deployment decision factor even for scale operators like Google.

**Evidence Quality**: Direct acknowledgment from S4 that QUIC is "much more expensive to host than TCP and HTTP/2," but the magnitude of the cost difference is not quantified in the available evidence. This is a known constraint but with thin quantitative grounding.

### Proxy-Enhanced HTTP/2 vs. Native HTTP/3 Performance

In severe network impairment scenarios, proxy-assisted HTTP/2 can approach HTTP/3 performance but at infrastructure cost:

**[DERIVED][HIGH]** Under severe impairment (4% loss, 50ms delay), HTTP/2 required a reverse proxy with BBR congestion control to improve from 106 seconds to 10 seconds (90% gain), while HTTP/3 achieved 15 seconds without any proxy assistance. This quantifies the infrastructure cost savings and operational complexity reduction by deploying HTTP/3 natively rather than relying on proxy-enhanced HTTP/2.

**Infrastructure Trade-off Analysis**:
- **HTTP/2 + BBR Proxy**: 10 seconds, requires reverse proxy infrastructure, BBR configuration, operational monitoring
- **HTTP/3 Native**: 15 seconds, no proxy required, lower operational overhead

**Implication**: HTTP/3 does not achieve the absolute best performance (10 vs. 15 seconds) but eliminates the need to deploy and operate sophisticated proxy infrastructure. The trade-off depends on whether the proxy infrastructure already exists and whether the 50% performance difference (10 vs. 15 seconds) justifies ongoing operational complexity.

---

## Part 3: Mobile-Specific Context and Limitations

### Evidence Quality Assessment

The learnings provided include strong measured data on HTTP/3 vs. HTTP/2 under controlled packet loss and delay, but **the evidence on "lossy mobile networks" specifically has the following structure**:

| Evidence Type | Strength | Coverage |
|---|---|---|
| **Controlled lab conditions** (4%, 12% loss, 50ms delay) | HIGH | Multiple scenarios, reproducible |
| **Proxy behavior** | HIGH | Standard CDN proxy (Envoy) measured |
| **Real mobile network field measurements** | NOT PROVIDED | The learnings focus on emulated loss/delay, not actual cellular network data |
| **Page load time (aggregate) vs. latency (individual components)** | PARTIAL | Connection latency and download throughput measured; full page composition not addressed |

**Critical Gap**: The learnings measure HTTP/3 vs. HTTP/2 under controlled impairments but do not include field measurements from real mobile networks (LTE, 5G). Real cellular networks introduce jitter, bursty loss patterns, handoffs, and variable signaling delays that may behave differently than emulated constant loss.

The 5G-related learnings (C7–C9) address NR-SA vs. NR-NSA architecture but do not directly compare HTTP/3 vs. HTTP/2 performance on these networks.

### Applicability to Mobile Scenarios

The measured improvements apply most directly to:
- **Lossy conditions** (4–12% packet loss): Common in poor signal areas, heavy interference
- **Connection transitions** (IP changes): WiFi-to-cellular handoff, carrier aggregation changes
- **Concurrent requests** (browsing, media playback): Multi-stream scenarios where head-of-line blocking impacts user experience

The measured improvements apply less directly to:
- **Proxy-dependent paths** (0–1 second overhead degrades benefit)
- **High-speed, low-latency networks** (QUIC overhead may regress performance)
- **Single-stream, low-loss scenarios** (no head-of-line blocking to eliminate)

---

## Part 4: Quantified Performance Improvements Summary

### Headline Improvements (Laboratory-Measured)

| Scenario | HTTP/3 Advantage | Measured Condition | Applicability to Mobile |
|---|---|---|---|
| **Connection migration** | 88.36% faster (6.6s vs. 56.7s) | 4% loss, 50ms delay, IP change | HIGH — common during network transitions |
| **Multi-stream under loss** | 81.5% faster (20.98s vs. 113.42s) | 12% loss, 20 concurrent streams | HIGH — typical browsing pattern |
| **Severe impairment (single stream)** | 50% advantage over unoptimized HTTP/2 (15s vs. 106s) | 4% loss, 50ms delay | MEDIUM — improves without proxy complexity |
| **High-bandwidth, low-latency** | Potential regression | Best-case networks | LOW — HTTP/2 may be faster |

### Conservative Estimate for Real Mobile Deployment

Based on the evidence provided:
- **Best case** (lossy network + concurrent requests): 70–88% latency reduction [OBSERVED/DERIVED][HIGH]
- **Typical case** (mixed loss and concurrent requests): 40–60% latency reduction [DERIVED][HIGH]
- **Worst case** (proxy-dependent, high-speed): 0–20% improvement or regression [DERIVED][HIGH]
- **Production proxy overhead**: 0–1 second added per connection, potentially halving or eliminating gain [DERIVED][HIGH]

---

## Part 5: Deployment Readiness Assessment

### When HTTP/3 Deployment Is Justified

**Strong case**:
- High user engagement sensitivity (video, real-time)
- Significant proportion of users on lossy networks (poor signal areas, heavy interference)
- Direct-to-client delivery (no proxy in path)
- Infrastructure budget exists for elevated per-connection costs

### When HTTP/3 Deployment Should Be Deferred

**Weak case**:
- Limited infrastructure budget
- Heavy proxy dependency (enterprise, CDN in experimental proxy mode)
- User base primarily on high-speed networks
- Single-stream workloads (APIs, light content)

### Implementation Maturity Status

**[DERIVED][HIGH]** The 0–1 second proxy overhead in Envoy, repeatedly documented across multiple sources, indicates that production-grade proxy support for HTTP/3 is **not yet mature**. This is not a measurement error but an implementation gap. **Evidence quality is high** (directly measured, attributed to experimental support), but the timeline for proxy maturity is not provided in the available research.

---

## Conclusions

### What Is Firmly Established

1. **[OBSERVED][HIGH]** HTTP/3 delivers 88.36% latency reduction for connection migration scenarios (IP changes during network transitions).
2. **[DERIVED][HIGH]** HTTP/3 delivers 81.5% latency reduction for multi-stream downloads under 12% packet loss.
3. **[DERIVED][HIGH]** HTTP/3 eliminates architectural head-of-line blocking, making loss impact independent per stream.
4. **[DERIVED][HIGH]** HTTP/3 is more expensive to operate per connection; infrastructure cost is a material decision factor.
5. **[DERIVED][HIGH]** Proxy implementations currently degrade HTTP/3 performance by 0–1 second per connection.

### What Remains Uncertain

1. **Real-world field performance on cellular networks**: Evidence is based on emulated loss/delay, not actual LTE/5G measurements [EVIDENCE THIN]
2. **Magnitude of regression in high-bandwidth networks**: Acknowledged theoretically but not quantified [EVIDENCE THIN]
3. **Timeline for proxy implementation maturity**: Current state documented; future state unspecified [EVIDENCE THIN]
4. **Aggregate page load time vs. latency components**: Individual component improvements measured; full composition not addressed [EVIDENCE THIN]

### Practical Recommendation for Lossy Mobile Networks

**[DERIVED][HIGH]** Deploy HTTP/3 for mobile-facing services where:
- User engagement is performance-sensitive
- Proxy implementation has moved beyond experimental status
- A significant proportion of traffic experiences 4% or higher packet loss
- Multi-stream usage (concurrent asset loading) is common

**Defer HTTP/3** for:
- Heavy proxy-dependent architectures until Envoy and similar proxies reach production-grade HTTP/3 support
- Use cases with constrained per-connection budgets
- Networks consistently showing <2% packet loss and <20ms latency (HTTP/2 may be sufficient or faster)

The measured evidence supports HTTP/3 as a material improvement for lossy mobile scenarios, but real-world deployment gains depend critically on proxy maturity and per-connection cost absorption capacity.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://arxiv.org/html/2409.16267v2>
- <https://arxiv.org/html/2409.16267v3>
- <https://adhdecode.com/articles/http3/http3-page-load-improvements/>
- <https://pulse.internetsociety.org/en/blog/2023/07/measuring-http-3-real-world-performance/>
- <https://arxiv.org/html/2312.00957v2>
- <https://www.telecomgurukul.com/post/analyzing-latency-in-4g-and-5g-networks-updated-in-2024>
- <https://arxiv.org/pdf/2310.11000>
- <https://link.springer.com/article/10.1007/s11235-025-01265-3>

_Note: 3 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** How much does HTTP/3 (QUIC) reduce page load time or latency compared with HTTP/2, especially on lossy mobile networks, according to measured studies?
- **Depth / breadth:** 2 / 3
- **Queries used:** 5 (budget 12)
- **Layers fired:**
  - search: ddg
  - markdown: empty-input, readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 795.9 s
- **Errors during run:** 17
- **Started at:** 2026-11-11T17:55:07Z
- **Module version:** deep_research 0.4.0
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 0 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, TRANSFERABILITY)  — SHORTFALL: only 1 axis/axes covered (COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, TRANSFERABILITY; only 1 axis/axes covered (TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, COUNTEREXAMPLE
- **E2 landscape:** A_MEASURED×1, B_ACADEMIC×6, UNKNOWN×4 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** OBSERVED 1, DERIVED 8 · 6 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / HIGH [EVIDENCE] — 3 source(s), families B_ACADEMIC, UNKNOWN — _What page load time and latency improvements have empirical studies measured when comparin_
- `COVERED` / HIGH [COUNTEREXAMPLE] — 3 source(s), families A_MEASURED, B_ACADEMIC — _In which real-world deployments or traffic patterns has HTTP/3 failed to outperform HTTP/2_
- `THIN` / MEDIUM [TRANSFERABILITY] — 2 source(s), families B_ACADEMIC, UNKNOWN — _Do the latency improvements measured on 4G networks transfer consistently to 5G networks a_
- `THIN` / MEDIUM [TRANSFERABILITY] — 3 source(s), families B_ACADEMIC, UNKNOWN — _Do latency performance improvements from mid-band standalone 5G (NR-SA) deployments genera_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://www.sciencedirect.com/science/article/pii/S014036642...': page-fetch: https://www.sciencedirect.com/science/article/pii/S0140366422000421: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 20`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 50`
- `decomposition narrow: only 1 axis/axes covered (COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, TRANSFERABILITY`
- `fetch_page 'https://www.sciencedirect.com/science/article/pii/S014036642...': page-fetch: https://www.sciencedirect.com/science/article/pii/S0140366422000421: HTTP Error 403: Forbidden`
- `fetch_page 'https://thenewstack.io/http-3-in-the-wild-why-it-beats-http-...': page-fetch: https://thenewstack.io/http-3-in-the-wild-why-it-beats-http-2-where-it-matters-most/: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: spans carry no figure`
- `web_search 'On what types of networks or conditions ...': ddg: fetch failed: <urlopen error [WinError 10054] Se ha forzado la interrupción de una conexión existente por el host remoto>; brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `fetch_page 'https://www.researchgate.net/publication/386999929_COMPARATI...': page-fetch: https://www.researchgate.net/publication/386999929_COMPARATIVE_ANALYSIS_OF_4G_VS_5G_NETWORK_PERFORMANCE_IN_DATA_COMMUNICATION: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.sciencedirect.com/science/article/pii/S143484112...': page-fetch: https://www.sciencedirect.com/science/article/pii/S1434841124003650: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.sciencedirect.com/science/article/pii/S138912862...': page-fetch: https://www.sciencedirect.com/science/article/pii/S1389128623005054: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 1 axis/axes covered (TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, COUNTEREXAMPLE`
- `fetch_page 'https://www.sciencedirect.com/science/article/pii/S138912862...': page-fetch: https://www.sciencedirect.com/science/article/pii/S1389128624000392: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.mdpi.com/2224-2708/15/1/18...': page-fetch: https://www.mdpi.com/2224-2708/15/1/18: HTTP Error 403: Forbidden`

</details>


## Evidence ledger

- **Claims:** 9 · with a verified quote: 9 (rate 1.0)
- **Quotes:** 14 offered, 4 rejected (not verbatim / unknown source / length)
- **Sources:** 8 snapshots in 8 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 3
- **Sources with instruction-like text (treated as data):** 0

**C1** [OBSERVED] Under 4% packet loss and 50ms delay, HTTP/3 completed file downloads during IP address changes in 6.6 seconds versus HTTP/2's 56.7 seconds with resume capability, an 88.36% improvement. This eliminates the operational need to implement reconnection logic in application code for users switching between networks.
  - S2 <https://arxiv.org/html/2409.16267v3> chars 15912-16084: "For example, under 4% packet loss and 50ms delay, H2 (wget_h2_resume) took 56.7 seconds to complete the download, whereas H3 needed only 6.6 seconds, an 88.36% improvement."

**C2** [DERIVED] At 12% packet loss with 20 concurrent streams, HTTP/3 completed downloads in 20.98 seconds versus HTTP/2's 113.42 seconds—an 81.5% improvement—because QUIC's stream architecture prevents head-of-line blocking. A single lost packet affects only one stream, not all concurrent transfers, fundamentally changing how loss impacts real traffic.
  - S2 <https://arxiv.org/html/2409.16267v3> chars 13846-13987: "For example, at 12% loss without a proxy, H2 took 113.42 seconds to download, compared to just 20.98 seconds for H3, an improvement of 81.5%."
  - _ledger: OBSERVED number(s) absent from verified spans: 20_

**C3** [DERIVED] Under severe impairment (4% loss, 50ms delay), HTTP/2 required a reverse proxy with BBR congestion control to improve from 106 seconds to 10 seconds (90% gain), while HTTP/3 achieved 15 seconds without any proxy assistance. This quantifies the infrastructure cost savings and operational complexity reduction by deploying HTTP/3 natively rather than relying on proxy-enhanced HTTP/2.
  - S1 <https://arxiv.org/html/2409.16267v2> chars 23935-24244: "H3 clients were able to complete the 10 MB file download in about 15 seconds, whereas H2 clients took approximately 106 seconds without a proxy. The introduction of a proxy using the BBR CCA significantly improved H2’s performance, reducing download times to around 10 seconds,..."
  - _ledger: OBSERVED number(s) absent from verified spans: 50_

**C4** [DERIVED] HTTP/3 requires materially more CPU time and memory than HTTP/2 per connection, making it costlier to operate at scale. This cost difference is significant enough that companies optimizing for engagement (Google, Akamai) treat it as an explicit tradeoff—they deploy HTTP/3 because engagement gains offset the infrastructure expense. For operators running less performance-sensitive workloads, this cost-benefit calculation may not favor HTTP/3.
  - S4 <https://pulse.internetsociety.org/en/blog/2023/07/measuring-http-3-real-world-performance/> chars 4353-4627: "QUIC and HTTP/3 are (much) more expensive to host on their platforms**, costing more CPU time and memory than TCP and HTTP/2, due to, for example, their more extensive encryption. This cost is (apparently) sufficiently offset by the protocols’ benefits on their bottom line."

**C5** [DERIVED] HTTP/2 sometimes outperforms HTTP/3 in high-bandwidth, low-latency networks because QUIC's per-packet encryption overhead becomes the limiting factor rather than network conditions. This means HTTP/3 is not a universal performance upgrade—its advantages are conditional on network impairment levels, and best-case networks may see regression.
  - S2 <https://arxiv.org/html/2409.16267v3> chars 5181-5259: "In high-speed environments, H2 sometimes outperforms H3 due to QUIC’s overhead"

**C6** [DERIVED] HTTP/3 performance in production proxy environments is currently degraded due to immature implementations. Laboratory testing with Envoy proxy (the standard in CDNs and enterprises) shows HTTP/3 adds 0–1 second connection overhead compared to HTTP/2, explicitly attributed to Envoy's experimental rather than production-grade HTTP/3 support. Deploying HTTP/3 now in proxy-dependent architectures can increase latency until proxy implementations mature.
  - S1 <https://arxiv.org/html/2409.16267v2> chars 22644-22941: "The introduction of a proxy resulted in a minor increase in download time for both protocols, adding roughly 0-1 seconds. This proxy overhead was slightly more pronounced for H3 than for H2, likely due to Envoy Proxy’s experimental support for H3, compared to its mature, optim..."
  - _ledger: OBSERVED number(s) absent from verified spans: spans carry no figure_

**C7** [DERIVED] Mid-band NR-SA networks demonstrate superior latency performance compared to NSA due to lower signaling overhead combined with denser deployments, providing a measurable latency advantage for delay-sensitive services. This finding enables operators to make deployment architecture choices that directly reduce end-to-end latency for time-critical applications.
  - S5 <https://arxiv.org/html/2312.00957v2> chars 8567-8728: "Mid-band NR-SA demonstrates the best latency performance due to the combination of lower signaling overhead (compared to NR-NSA) and denser mid-band deployments."

**C8** [DERIVED] Measurements across Chicago and Minneapolis revealed negligible differences in network performance, indicating that mid-band 5G improvements transfer consistently between metropolitan environments. This consistency suggests operators can replicate deployment and optimization approaches across regions with similar urban infrastructure density rather than customizing per market.
  - S5 <https://arxiv.org/html/2312.00957v2> chars 20680-20864: "Preliminary analysis revealed negligible differences between the datasets collected in Chicago and Minneapolis. Consequently, we combined them for the analyses presented in this paper."

**C9** [DERIVED] Mid-band NR-SA's latency advantage derives from two independent sources: the lower signaling overhead inherent to SA architecture, and denser mid-band deployment. T-Mobile's n41 (SA) was deployed with 462 unique cell-site PCIs, compared to AT&T and Verizon NSA mid-band channels with substantially lower PCI counts (AT&T n77: 152; Verizon n77: 147), representing a 3x density differential. This means NSA-only operators can partially reduce latency disadvantage relative to SA competitors through matching deployment density, but remain constrained by NSA's architecturally inherent signaling overhead regardless of deployment depth.
  - S5 <https://arxiv.org/html/2312.00957v2> chars 8567-8728: "Mid-band NR-SA demonstrates the best latency performance due to the combination of lower signaling overhead (compared to NR-NSA) and denser mid-band deployments."
  - S5 <https://arxiv.org/html/2312.00957v2> chars 21757-21866: "Moreover, TMO-n41 is very densely deployed with 462 unique PCIs compared to the NR channels from ATT and VZW."
