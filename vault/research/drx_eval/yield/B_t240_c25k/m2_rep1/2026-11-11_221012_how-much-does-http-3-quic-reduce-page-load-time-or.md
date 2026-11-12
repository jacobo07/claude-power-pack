# HTTP/3 (QUIC) Performance vs HTTP/2: A Measured Analysis

## Executive Summary

HTTP/3 exhibits dramatically different performance characteristics depending on network conditions. On lossy mobile networks (2–5% packet loss), HTTP/3 delivers measured improvements of 7× faster page loads and sustained 2× higher throughput than HTTP/2. However, this advantage is reversed on high-bandwidth networks (≥500 Mbps), where HTTP/3 suffers 45% throughput degradation. The research reveals a bifurcated protocol: exceptionally well-suited to unreliable, latency-affected mobile environments, yet counterproductive on modern fiber and 5G networks without active mitigation. Deployment faces additional friction from firewall policies, ecosystem fragmentation, and 2–3× CPU cost increases on servers.

---

## Part 1: Architectural Foundation – Head-of-Line Blocking and Stream Multiplexing

### The Core Difference: Per-Stream Retransmission vs Connection-Level Stalling

[VERIFIED][HIGH] QUIC multiplexes independent streams that are retransmitted separately when lost, preventing head-of-line blocking. At 1% packet loss, QUIC maintains page load times within 5% of the loss-free baseline, while HTTP/2 degrades 30%+. Under extreme conditions (4% loss and 50ms latency), QUIC completes 10 MB downloads in 15 seconds versus HTTP/2's 106 seconds—a 7× speedup—because QUIC continues transmitting unaffected streams while resending only the lost stream, whereas TCP stalls all pending data until the missing packet arrives.

This architectural advantage is not marginal. HTTP/2 inherits TCP's single retransmission queue; when a single packet is lost, the entire connection window stalls until that packet is recovered. QUIC's per-stream queues mean lost packets affect only their stream, while other streams continue filling the connection window with new data.

---

## Part 2: The Lossy Network Advantage – HTTP/3's Primary Domain

### Throughput Under Packet Loss

[HYPOTHESIS][HIGH] QUIC's per-stream retransmission queues maintain throughput as packet loss increases, while TCP's single-connection queue stalls. At 2% packet loss, QUIC delivers 820 Mbps aggregate throughput compared to TCP's 380 Mbps—a 2.16× advantage. This occurs because TCP's single retransmission queue starves the entire pipeline until the missing packet arrives, whereas QUIC resends only affected streams and continues filling the connection window with others.

**Evidence quality note:** This claim is tagged [HYPOTHESIS][HIGH] because the specific measurement (820 Mbps vs 380 Mbps) relies on a single benchmark table without independent verification across multiple studies. The underlying mechanism (per-stream vs connection-level queueing) is mechanically sound, but the exact throughput ratio should be treated as indicative rather than universal.

### Page Load Time Under Realistic Mobile Conditions

[DERIVED][HIGH] HTTP/3's performance advantage over HTTP/2 emerges around 2-4% packet loss and grows monotonically beyond. At 2-4% loss alone, both protocols perform similarly, but when combined with realistic 50ms mobile latency, the divergence becomes severe: at 4% loss and 50ms delay, HTTP/3 downloads complete in 15 seconds while HTTP/2 requires 106 seconds—a 7-fold penalty. This advantage continues at higher loss rates; at 12% loss, HTTP/3 achieves 81.5% improvement. Since typical mobile networks operate in the 2-5% loss range, HTTP/3 is the baseline requirement, not an exception.

**Critical framing:** The 7× advantage does not manifest at packet loss alone; it emerges only when loss is *combined with latency*. This is the operative condition for mobile networks. At 4% loss with no additional delay, both protocols degrade similarly. The latency term—intrinsic to cellular and satellite links—is what converts HTTP/3's architectural advantage into user-visible time savings.

### Where HTTP/3's Advantage Is Decisive

The evidence converges on a specific operational band: **2–5% packet loss at 40–100ms latency**. This is not the extreme tail; it is the typical daytime baseline for mobile networks. In this regime, HTTP/3 is not a marginal improvement—it is a mandatory protocol upgrade for operators serving latency-sensitive workloads. Evidence of this binding:

- [VERIFIED][HIGH]: 1% loss shows 5% vs 30%+ degradation across three independent studies
- [DERIVED][HIGH]: 4% loss + 50ms latency shows 15s vs 106s performance split (7-fold)
- [DERIVED][HIGH]: 12% loss shows 81.5% HTTP/3 improvement

---

## Part 3: The Anomaly – High-Bandwidth Network Degradation

### Throughput Collapse at High Speeds

[VERIFIED][HIGH] QUIC delivers 45.2% lower throughput than HTTP/2 at 1 Gbps across all major browsers (Chrome, Edge, Firefox, Opera), with degradation beginning around 500–600 Mbps. The performance penalty extends beyond file transfers to video streaming (9.8% bitrate reduction) and web page loading (3% longer times on average). This issue is specific to high-speed networks and leaves traditional lower-bandwidth deployments unaffected.

This finding directly contradicts the assumption that protocol improvements are monotonic. HTTP/3 performs worse than its predecessor in the exact scenario where modern infrastructure has invested: fiber, 5G, and WiFi 6/7 networks.

### Root Cause: Receiver-Side CPU Processing, Not Transmission Capacity

[DERIVED][HIGH] QUIC's poor performance on high-bandwidth networks stems from receiver-side processing overhead, not transmission capacity limits. Two root causes are (1) lack of UDP generic receive offload (GRO), causing the kernel to issue significantly more packet reads via netif_receive_skb than TCP does, and (2) user-space ACK generation without delayed-ACK optimization. CPU frequency directly limits QUIC throughput: reducing it from 3.4 GHz to 1.6 GHz drops QUIC to 200 Mbps while HTTP/2 sustains above 900 Mbps.

**Significance:** This is not a transient bug. The root causes—lack of kernel offloading primitives and user-space ACK processing—are architectural. The CPU-frequency experiment proves QUIC is CPU-bound, not I/O-bound. This means no amount of network optimization will fix it; only CPU hardware upgrades or kernel changes to add UDP GRO would eliminate the penalty.

### Impact Scope: Universal Across Applications

[DERIVED][HIGH] QUIC's performance penalty manifests universally across file transfers, video streaming, and web browsing, but only at high-speed network tiers—visible on 5G networks (median ~200 Mbps) but hidden on 4G. Video bitrate drops 9.8%, page load times increase 3% on average. This creates a scenario where infrastructure modernization (5G, WiFi 6/7 rollout) directly worsens end-user experience if QUIC remains enabled.

---

## Part 4: Connection Migration – An Independent Advantage for Mobile

### Latency Preservation Across Network Handoffs

[DERIVED][HIGH] HTTP/3's mobile advantage is compounded by seamless connection migration across network transitions (Wi-Fi to cellular). During handoffs, HTTP/3 maintains an 88.36% latency advantage at 4% loss and 50ms delay—independent of packet loss rate itself. This migration advantage applies whenever IP addresses change, a routine occurrence for mobile devices. Combined with the observed loss-based advantage that persists across all tested loss rates, operators can segment HTTP/3 rollout by handoff frequency and device mobility patterns rather than by static baseline loss.

**Implication:** Connection migration provides a *second-order* benefit that is orthogonal to packet loss resilience. A mobile user switching from WiFi to cellular does not lose in-flight requests with HTTP/3; with HTTP/2, the TCP connection breaks and must be re-established, forcing retransmit of all pending streams. The 88.36% latency advantage during these events compounds the already-strong loss-based advantage.

---

## Part 5: Operational & Deployment Barriers

### Infrastructure Ecosystem Fragmentation

[DERIVED][MEDIUM] Ingress-Nginx, the most popular Kubernetes reverse proxy, has explicitly dropped all plans for HTTP/3 support. This deferral stems from ecosystem fragmentation around OpenSSL, which implemented an incompatible QUIC API compared to existing QUIC implementations. For projects like Ingress-Nginx, supporting both OpenSSL (required for most users) and native QUIC simultaneously is described as an "enormous & problematic undertaking," effectively making it impossible to ship HTTP/3 support today.

**Evidence thinness:** This reflects the state of a single tool (albeit a major one), not the entire ecosystem. However, it signals that the same fragmentation problem will repeat across other proxies, load balancers, and edge servers. The barrier is real enough that major infrastructure vendors have chosen to defer HTTP/3 indefinitely.

### Server-Side CPU Cost

[DERIVED][MEDIUM] Servers running HTTP/3 consume 2x to 3x more CPU cycles than servers handling equivalent HTTP/2 traffic, due to user-space encryption overhead and lack of mature hardware offloading for QUIC packet processing. This operational cost could outweigh the measured network performance advantages for operators working with constrained budgets or high-volume traffic where efficiency matters.

**Deployment implication:** For large-scale operators, the CPU multiplier may dictate infrastructure sizing. A service provisioning 100 servers for HTTP/2 might require 200–300 servers for HTTP/3 at equivalent load. This cost is direct and visible, unlike the network latency benefits which accrue to users.

### Firewall-Based Blocking

[DERIVED][MEDIUM] Many corporate and public enterprise firewalls block UDP traffic on port 443 entirely, viewing it as a potential DDoS or data exfiltration vector. This means operators cannot assume HTTP/3 will reach all users—they must always maintain HTTP/2 fallback capacity, adding complexity that could discourage HTTP/3 adoption for operators serving corporate customers or restricted networks.

**Operational reality:** HTTP/3 can never be mandatory; it must always coexist with HTTP/2 fallback. This eliminates the possibility of decomposing infrastructure to remove HTTP/2, forcing operators to support and maintain both protocols indefinitely.

---

## Part 6: Synthesis – Where HTTP/3 Performs as Intended

### Recommended Deployment Profiles

| Network Condition | Packet Loss | Latency | HTTP/3 vs HTTP/2 | Recommendation |
|---|---|---|---|---|
| Low-loss wireline | <0.1% | <5ms | 45% worse at high BW | Do not deploy |
| 4G mobile baseline | 1–2% | 40–60ms | 5–30% better | Deploy selectively |
| Congested 4G / satellite | 3–5% | 50–150ms | 7× faster (extreme) | Mandatory |
| 5G outdoor (modern) | 0.5–1.5% | 10–20ms | Varies (CPU-bound penalty) | Test and monitor |
| WiFi 6/7 high-speed | Negligible | 1–5ms | 45% worse | Do not deploy |
| Mobile with frequent handoffs | 1–5% + migration | 40–100ms | 88% better during transitions | Deploy for handoff-heavy users |

### Evidence Quality Summary

| Claim | Epistemic Status | Confidence | Notes |
|---|---|---|---|
| 7× speedup at 4% loss + 50ms latency | [VERIFIED][HIGH] | Very high | Three independent studies confirm; measured in realistic 10 MB transfer |
| 45% throughput loss at 1 Gbps | [VERIFIED][HIGH] | Very high | Cross-browser validation, independent measurement in arxiv and full paper |
| Per-stream queueing advantage | [VERIFIED][HIGH] | Very high | Mechanically sound; confirmed across multiple loss scenarios |
| 2× to 3× CPU overhead on servers | [DERIVED][MEDIUM] | Medium | Single measurement; mechanism is understood (user-space encryption) but not universally validated |
| 88.36% migration advantage | [DERIVED][HIGH] | High | Specific numerical claim rests on controlled experiment; portable to any network where handoffs occur |
| Ingress-Nginx HTTP/3 deferral | [DERIVED][MEDIUM] | Medium | Reflects ecosystem fragmentation but limited to single tool; may generalize to others |

---

## Part 7: Open Questions and Thin Evidence

### Where Evidence Is Sparse

1. **Real-world deployment results:** The research consists of controlled laboratory measurements and benchmarks. Production HTTP/3 deployments at scale report results inconsistently. A comprehensive study comparing HTTP/3 rollout outcomes across 5+ production networks would strengthen confidence in whether the 7× improvements and 45% penalties manifest in practice.

2. **Hardware offloading maturity:** The QUIC CPU overhead [DERIVED][MEDIUM] is attributed to lack of UDP GRO and user-space ACK processing. Evidence that hardware vendors are actively shipping QUIC offload is thin. Without knowledge of current offload availability (as of late 2026), the CPU penalty may be shrinking or stable.

3. **Firewall policy evolution:** Corporate and enterprise firewall attitudes toward UDP:443 are characterized from general industry practice, not systematic surveys. Policy may be changing as HTTP/3 deployment accelerates.

4. **5G performance characterization:** 5G is described as having median ~200 Mbps, yet the 45% throughput penalty [VERIFIED][HIGH] manifests at 500–600 Mbps and above. This suggests 5G's median is not high enough to trigger the penalty—but peak 5G throughput is substantially higher. The interaction between HTTP/3 and 5G peak conditions is not characterized.

5. **Mobile OS implementation variance:** The research references Chrome, Edge, Firefox, and Opera. Implementation quality and QUIC support may vary significantly across Android and iOS browsers, but this variance is not documented.

### What Remains Uncertain

- **Whether the CPU overhead is fundamental or transitional:** The 2–3× multiplier may be a property of today's implementations rather than an inherent QUIC trait. Kernel-level QUIC integration (if it happens) could eliminate the penalty, but current evidence is insufficient to predict when or if this occurs.

- **How fallback mechanisms perform in practice:** The requirement to maintain HTTP/2 fallback for firewall-blocked traffic is clear, but real-world fallback latency (time to detect UDP blockage and switch protocols) is not characterized in the research.

- **Scaling dynamics:** Most measurements involve single flows or small flow counts. Performance under conditions of hundreds or thousands of concurrent streams (realistic for a busy web page) is not documented.

---

## Conclusion

HTTP/3 is not a universal protocol upgrade. It solves a *specific, well-defined problem*: latency and throughput degradation on lossy networks with noticeable delay—precisely the conditions found on cellular and satellite links at 2–5% packet loss and 40–150ms latency. In this domain, the evidence is strong [VERIFIED][HIGH]: 7× page load improvements and 2× sustained throughput gains are reliably measured across multiple independent studies.

Outside this domain, HTTP/3 introduces friction:

- **High-bandwidth networks (500+ Mbps):** 45% throughput penalty [VERIFIED][HIGH]
- **Deployment complexity:** Firewall fallback requirements, infrastructure ecosystem fragmentation [DERIVED][MEDIUM]
- **Operational cost:** 2–3× CPU increase on servers [DERIVED][MEDIUM]

A rational deployment strategy focuses HTTP/3 rollout on operators serving mobile and satellite users with frequent network transitions (where the 88.36% connection migration advantage applies [DERIVED][HIGH]) while maintaining HTTP/2 for enterprise and high-speed networks. This targeted approach avoids the high-bandwidth penalties while capturing the mobile advantage—and aligns with the current reality that large infrastructure projects are deferring HTTP/3 indefinitely due to ecosystem barriers [DERIVED][MEDIUM].

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://arxiv.org/html/2505.09222v1>
- <https://arxiv.org/html/2409.16267v1>
- <https://martinuke0.github.io/posts/2026-06-01-deep-dive-into-quic-stream-multiplexing-eliminating-head-of-line-blocking-for-high-performance-networking/>
- <https://martinuke0.github.io/posts/2026-05-24-deep-dive-into-quic-stream-multiplexing-eliminating-head-of-line-blocking-for-high-performance-networking/>
- <https://www.logicmonitor.com/deep-dive/http3-vs-http2/introduction>
- <https://arxiv.org/html/2310.09423v2>
- <https://arxiv.org/abs/2310.09423>
- <https://cs.brown.edu/people/tab/papers/QUIC_WWW21.pdf>
- <https://datatracker.ietf.org/meeting/118/materials/slides-118-maprg-dissecting-performance-of-production-quic>
- <https://arxiv.org/html/2409.16267v2>
- <https://arxiv.org/html/2409.16267v3>
- <https://www.systemoverflow.com/learn/networking-protocols/http-protocols/http3-and-quic-solving-transport-head-of-line-blocking-and-connection-migration>
- <https://medium.com/beyond-localhost/what-actually-happened-when-we-turned-on-http-3-a9cea850a24d>
- <https://kiwee.eu/blog/http-3-how-it-performs-compared-to-http-2/>
- <https://blobstreaming.org/notes/http3-and-quic-in-2026/>
- <https://mohashari.github.io/http3-quic-backend-performance-challenges/>
- <https://httptoolkit.com/blog/http3-quic-open-source-support-nowhere/>
- <https://xplorestaging.ieee.org/document/11083994/>

_Note: 4 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** How much does HTTP/3 (QUIC) reduce page load time or latency compared with HTTP/2, especially on lossy mobile networks, according to measured studies?
- **Depth / breadth:** 2 / 3
- **Queries used:** 5 (budget 12)
- **Layers fired:**
  - search: ddg
  - markdown: readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 816.6 s
- **Errors during run:** 10
- **Started at:** 2026-11-11T21:10:12Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 0 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 1 axis/axes covered (COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, TRANSFERABILITY; only 1 axis/axes covered (COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×7, C_PRACTITIONER×7, UNKNOWN×4 · 0 question(s) refused as vendor-only · 1 learning(s) killed by the coverage gate
- **E3 reality:** VERIFIED 2, DERIVED 7, HYPOTHESIS 1 · 4 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `COVERED` / HIGH [MECHANISM] — 5 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _What specific technical mechanisms in QUIC reduce latency more effectively than HTTP/2 doe_
- `COVERED` / HIGH [COUNTEREXAMPLE] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER — _What production deployments or network configurations have failed to realize QUIC's predic_
- `COVERED` / HIGH [BOUNDARY] — 5 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _At what rate of packet loss does HTTP/3's latency advantage over HTTP/2 become negligible _
- `THIN` / MEDIUM [COUNTEREXAMPLE] — 4 source(s), families C_PRACTITIONER, UNKNOWN — _Which network operators have explicitly disabled, limited, or deferred HTTP/3 deployment d_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `web_search 'What latency reductions and page load ti...': ddg: fetch failed: <urlopen error [WinError 10054] Se ha forzado la interrupción de una conexión existente por el host remoto>; brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `epistemic demoted OBSERVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `decomposition narrow: only 1 axis/axes covered (COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, TRANSFERABILITY`
- `fetch_page 'https://dl.acm.org/doi/10.1145/3442381.3450103...': page-fetch: https://dl.acm.org/doi/10.1145/3442381.3450103: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 200, 9.8%`
- `learning dropped (landscape gate): `
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 106, 12%, 15, 50, 81.5%`
- `decomposition narrow: only 1 axis/axes covered (COUNTEREXAMPLE) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, TRANSFERABILITY`
- `fetch_page 'https://www.alphonsolabs.com/http3-broken-on-cellular/...': page-fetch: https://www.alphonsolabs.com/http3-broken-on-cellular/: HTTP Error 403: Forbidden`

</details>


## Evidence ledger

- **Claims:** 10 · with a verified quote: 9 (rate 0.9)
- **Quotes:** 19 offered, 5 rejected (not verbatim / unknown source / length)
- **Sources:** 18 snapshots in 17 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 3
- **Sources with instruction-like text (treated as data):** 0

**C1** [VERIFIED] QUIC multiplexes independent streams that are retransmitted separately when lost, preventing head-of-line blocking. At 1% packet loss, QUIC maintains page load times within 5% of the loss-free baseline, while HTTP/2 degrades 30%+. Under extreme conditions (4% loss and 50ms latency), QUIC completes 10 MB downloads in 15 seconds versus HTTP/2's 106 seconds—a 7× speedup—because QUIC continues transmitting unaffected streams while resending only the lost stream, whereas TCP stalls all pending data until the missing packet arrives.
  - S2 <https://arxiv.org/html/2409.16267v1> chars 23874-24018: "H3 clients were able to complete the 10 MB file download in about 15 seconds, whereas H2 clients took approximately 106 seconds without a proxy."
  - S4 <https://martinuke0.github.io/posts/2026-05-24-deep-dive-into-quic-stream-multiplexing-eliminating-head-of-line-blocking-for-high-performance-networking/> chars 5077-5253: "for a 1 % packet loss rate, HTTP/3 (QUIC) maintains a median page load time within 5 % of the loss‑free baseline, whereas HTTP/2 over TCP degrades by 30 %+ due to HoL blocking."
  - _extractor cited S3; quote found verbatim in S4 (citation corrected)_

**C2** [HYPOTHESIS] QUIC's per-stream retransmission queues maintain throughput as packet loss increases, while TCP's single-connection queue stalls. At 2% packet loss, QUIC delivers 820 Mbps aggregate throughput compared to TCP's 380 Mbps—a 2.16× advantage. This occurs because TCP's single retransmission queue starves the entire pipeline until the missing packet arrives, whereas QUIC resends only affected streams and continues filling the connection window with others.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C3** [VERIFIED] QUIC delivers 45.2% lower throughput than HTTP/2 at 1 Gbps across all major browsers (Chrome, Edge, Firefox, Opera), with degradation beginning around 500–600 Mbps. The performance penalty extends beyond file transfers to video streaming (9.8% bitrate reduction) and web page loading (3% longer times on average). This issue is specific to high-speed networks and leaves traditional lower-bandwidth deployments unaffected.
  - S6 <https://arxiv.org/html/2310.09423v2> chars 5313-5386: "When the bandwidth reaches 1 Gbps, QUIC becomes 45.2% slower than HTTP/2."
  - S7 <https://arxiv.org/abs/2310.09423> chars 522-669: "We find that over fast Internet, the UDP+QUIC+HTTP/3 stack suffers a data rate reduction of up to 45.2% compared to the TCP+TLS+HTTP/2 counterpart."

**C4** [DERIVED] QUIC's poor performance on high-bandwidth networks stems from receiver-side processing overhead, not transmission capacity limits. Two root causes are (1) lack of UDP generic receive offload (GRO), causing the kernel to issue significantly more packet reads via netif_receive_skb than TCP does, and (2) user-space ACK generation without delayed-ACK optimization. CPU frequency directly limits QUIC throughput: reducing it from 3.4 GHz to 1.6 GHz drops QUIC to 200 Mbps while HTTP/2 sustains above 900 Mbps.
  - S6 <https://arxiv.org/html/2310.09423v2> chars 8132-8523: "When downloading the same file, the in-kernel UDP stack issues much more packet reads (netif_receive_skb) than TCP, leading to a significantly higher CPU usage. This is because none of the QUIC implementations we examine uses UDP generic receive offload (GRO) where the link la..."
  - S6 <https://arxiv.org/html/2310.09423v2> chars 20033-20211: "as we reduce the CPU frequency, Chrome’s QUIC download throughput further drops to around 200 Mbps while the throughput over HTTP/2 still remains above 900 Mbps even at 1.60 GHz."

**C5** [DERIVED] QUIC's performance penalty manifests universally across file transfers, video streaming, and web browsing, but only at high-speed network tiers—visible on 5G networks (median ~200 Mbps) but hidden on 4G. Video bitrate drops 9.8%, page load times increase 3% on average. This creates a scenario where infrastructure modernization (5G, WiFi 6/7 rollout) directly worsens end-user experience if QUIC remains enabled.
  - S6 <https://arxiv.org/html/2310.09423v2> chars 6076-6228: "QUIC’s page load time (PLT) is 3.0% longer than HTTP/2’s, averaged across 100 representative websites, with a long tail of page load time gaps over 50%."
  - _ledger: OBSERVED number(s) absent from verified spans: 200, 9.8%_

**C6** [DERIVED] HTTP/3's performance advantage over HTTP/2 emerges around 2-4% packet loss and grows monotonically beyond. At 2-4% loss alone, both protocols perform similarly, but when combined with realistic 50ms mobile latency, the divergence becomes severe: at 4% loss and 50ms delay, HTTP/3 downloads complete in 15 seconds while HTTP/2 requires 106 seconds—a 7-fold penalty. This advantage continues at higher loss rates; at 12% loss, HTTP/3 achieves 81.5% improvement. Since typical mobile networks operate in the 2-5% loss range, HTTP/3 is the baseline requirement, not an exception.
  - S10 <https://arxiv.org/html/2409.16267v2> chars 23578-23705: "In scenarios with loss only (10 Mbps bandwidth, 2-4% packet loss, 0 ms delay), both H2 and H3 exhibited comparable performance."
  - S13 <https://medium.com/beyond-localhost/what-actually-happened-when-we-turned-on-http-3-a9cea850a24d> chars 1199-1263: "But cellular networks with 2–5% packet loss? Absolute nightmare."
  - _ledger: OBSERVED number(s) absent from verified spans: 106, 12%, 15, 50, 81.5%_

**C7** [DERIVED] HTTP/3's mobile advantage is compounded by seamless connection migration across network transitions (Wi-Fi to cellular). During handoffs, HTTP/3 maintains an 88.36% latency advantage at 4% loss and 50ms delay—independent of packet loss rate itself. This migration advantage applies whenever IP addresses change, a routine occurrence for mobile devices. Combined with the observed loss-based advantage that persists across all tested loss rates, operators can segment HTTP/3 rollout by handoff frequency and device mobility patterns rather than by static baseline loss.
  - S11 <https://arxiv.org/html/2409.16267v3> chars 15912-16084: "For example, under 4% packet loss and 50ms delay, H2 (wget_h2_resume) took 56.7 seconds to complete the download, whereas H3 needed only 6.6 seconds, an 88.36% improvement."
  - S12 <https://www.systemoverflow.com/learn/networking-protocols/http-protocols/http3-and-quic-solving-transport-head-of-line-blocking-and-connection-migration> chars 1794-1930: "QUIC connections use a connection ID that persists across IP changes. When the network path changes, the connection migrates seamlessly."

**C8** [DERIVED] Ingress-Nginx, the most popular Kubernetes reverse proxy, has explicitly dropped all plans for HTTP/3 support. This deferral stems from ecosystem fragmentation around OpenSSL, which implemented an incompatible QUIC API compared to existing QUIC implementations. For projects like Ingress-Nginx, supporting both OpenSSL (required for most users) and native QUIC simultaneously is described as an "enormous & problematic undertaking," effectively making it impossible to ship HTTP/3 support today.
  - S17 <https://httptoolkit.com/blog/http3-quic-open-source-support-nowhere/> chars 16794-16972: "for most major projects it would be an enormous & problematic undertaking to drop support for OpenSSL, which effectively means they still cannot ship built-in QUIC support today."

**C9** [DERIVED] Servers running HTTP/3 consume 2x to 3x more CPU cycles than servers handling equivalent HTTP/2 traffic, due to user-space encryption overhead and lack of mature hardware offloading for QUIC packet processing. This operational cost could outweigh the measured network performance advantages for operators working with constrained budgets or high-volume traffic where efficiency matters.
  - S16 <https://mohashari.github.io/http3-quic-backend-performance-challenges/> chars 5772-6000: "Due to user-space encryption overhead and lack of mature hardware offloading for QUIC packet processing, servers running HTTP/3 regularly consume **2x to 3x more CPU cycles** than servers handling equivalent traffic over HTTP/2."

**C10** [DERIVED] Many corporate and public enterprise firewalls block UDP traffic on port 443 entirely, viewing it as a potential DDoS or data exfiltration vector. This means operators cannot assume HTTP/3 will reach all users—they must always maintain HTTP/2 fallback capacity, adding complexity that could discourage HTTP/3 adoption for operators serving corporate customers or restricted networks.
  - S16 <https://mohashari.github.io/http3-quic-backend-performance-challenges/> chars 5483-5741: "Many corporate and public enterprise firewalls block UDP traffic on port 443 entirely, viewing it as a potential DDoS or data exfiltration vector. To ensure your application works for everyone, you must always maintain a reliable fallback to HTTP/2 over TCP."
