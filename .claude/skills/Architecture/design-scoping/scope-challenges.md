# Design Scoping — challenging a proposed scope

Read when the user opens with scope already sketched; each bullet is a pushback to raise as a question.

## Challenge a proposed scope

If the user opens with scope already sketched (a design doc, a set of requirements), put it
under the gate and test it:

- **"the requirements are all functional"** — where are the numbers? A design with no
  throughput, latency, or availability target will be over- or under-built and nobody can
  tell which. Push for item 4 or an explicit "no constraint".
- **"everything is in scope for v1"** — then nothing is prioritized and the timeline
  (item 5) is fiction. What is the *smallest* thing that delivers the purpose (item 2)?
- **no out-of-scope list** — add one. Name the five things people will assume are included
  that aren't.
- **compliance not mentioned** — ask directly. "Do any of GDPR, HIPAA, PCI DSS, SOC 2, or
  data-residency rules apply?" A retrofitted compliance boundary is a redesign.
- **jumped to technology** — "we'll use Kafka and Cassandra" before purpose and numbers is
  a solution in search of a problem. What load and what access pattern make those the
  answer?
- **10 features all "critical"** — run the significance filter. Usually one or two are
  whole-system blast radius and the rest are deferrable.

Flag the load-bearing gap as a question, not a correction.
