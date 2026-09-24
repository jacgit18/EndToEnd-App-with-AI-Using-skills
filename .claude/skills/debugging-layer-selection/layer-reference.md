# Layer reference

## Abstraction model

```text
Application
    |
Browser
    |
HTTP / HTTPS / WebSocket
    |
TCP / UDP
    |
IP
    |
Ethernet / Network Interface
```

Chrome DevTools operates near the browser/application/HTTP layer. Wireshark/tshark operates
at the packet layer, below all of it. Backend observability (logs, traces, metrics) sits
beside the browser layer, not below it — it's a different vantage point on the same
application-layer request, not a deeper layer to descend to.

## Symptom → tool lookup

**Chrome DevTools** is the default for anything the browser can see directly:

| Symptom | Panel |
|---|---|
| JS error, unhandled exception | Console, Sources (debugger, breakpoints) |
| DOM/CSS not matching expectations | Elements |
| Wrong/missing API response, status code, headers, payload | Network |
| CORS error | Network (look at the preflight `OPTIONS` and its response headers) |
| Auth/cookie not sent or rejected | Network → request headers, Application → Cookies/Storage |
| Caching serving stale content | Network (disable cache toggle, check `Cache-Control`/`ETag`), Application |
| WebSocket messages / disconnects from the app's view | Network → WS frames |
| Service worker intercepting/breaking requests | Application → Service Workers |
| Slow page, high CPU | Performance panel (flame chart, main-thread work) |
| Memory leak, growing heap | Memory panel (heap snapshots, allocation timeline) |
| Which code initiated a request | Network → Initiator column, or "Copy as fetch" |
| Frontend framework state/render bug | React/Vue DevTools extension alongside the above |

**Wireshark/tshark** is for what's happening below that abstraction:

| Symptom | What to capture |
|---|---|
| TCP retransmissions, out-of-order segments | Filter `tcp.analysis.retransmission` |
| Connection resets | Filter `tcp.flags.reset == 1` |
| Slow/failed TCP handshake | SYN / SYN-ACK / ACK sequence and timing |
| DNS resolution issues | UDP/TCP port 53 traffic, response codes |
| TLS handshake failures or slow negotiation | `tls.handshake` filter, look for alerts/renegotiation |
| Traffic between two non-browser services | Capture on both hosts, correlate by stream (`tcp.stream eq N`) |
| Non-HTTP protocol traffic | Protocol-specific dissector/filter |
| "The network itself seems wrong" with no other explanation | Full capture around the reproduction window, then narrow by filter |

**Backend observability** (not a separate tool decision this skill makes, but the frequent
next step after DevTools step 3 resolves): application logs for that request/trace ID,
distributed tracing spans, server-side metrics. If this doesn't exist yet as a way to
investigate anything beyond ad hoc log-grepping, that gap is `observability-strategy`'s
territory, not something to build under incident pressure.

## Do not default to the packet layer

Wireshark exposes more raw information than DevTools, but more raw information is not
automatically more useful information. Jumping to a packet capture when the DevTools Network
panel already shows a clean request/response with the delay entirely in "Waiting" (i.e., the
server took a long time, which is a backend question) wastes capture/analysis effort on a
question the browser already answered. Descend a layer only when the current layer's
evidence is genuinely insufficient to explain the symptom — not because the lower layer is
more powerful in general.

## AI-assisted variant of this same procedure

When an agent (rather than a person) is doing the triage and investigation, the same
layer-selection logic applies, with one addition: ground every step in a real tool call
against real output, not inference from a raw capture handed to an LLM.

```text
Weak:   PCAP -> LLM -> guess what happened
Strong: Agent -> MCP/tool call -> Chrome DevTools (or tshark) -> real output -> reasoning
```

Chrome DevTools MCP lets an agent inspect real console output, network activity, performance
timings, and other browser state directly rather than being told about it secondhand.
Similarly, an agent wrapping `tshark` can query and filter a capture programmatically instead
of having a raw PCAP summarized into a guess. The layer decision above still applies
first — an agent should not reach for a packet-capture tool call before checking whether the
browser-layer tool call already answers the question.

## Learning priority for a generalist engineer

A software engineer does not need network-engineer-level Wireshark mastery, but should know
enough to recognize when an application problem is actually a network problem underneath it.

**Tier 1 — essential, use constantly:** Chrome DevTools Console, Sources/debugger, Network,
Application, Performance, Memory.

**Tier 2 — essential supporting tools, not covered by either tool above:** `curl` (reproduce
a request outside the browser to isolate browser-specific behavior), backend logs,
application tracing/observability, database/query inspection.

**Tier 3 — specialized, learn enough to recognize the trigger, not to master:** Wireshark/
tshark fundamentals — Ethernet, IP, TCP, UDP, DNS, TLS, display filters, following a TCP
stream, recognizing retransmissions/resets, reading packet timing.
