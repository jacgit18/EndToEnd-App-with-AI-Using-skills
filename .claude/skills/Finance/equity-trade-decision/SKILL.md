---
name: equity-trade-decision
description: Use when a specific stock trade is on the table — a real ticker, a real entry price, real capital — and someone wants to know whether to enter it, how many shares, or whether a proposed position size is sane. Triggers include "should I buy X here", "how many shares of X should I buy", "is this position too big", "what's my risk on this trade", a stated entry/stop/capital figure to size against, or a cycle-stage/sector-tilt question tied to an actual trade decision. Forces three things in sequence: a pre-trade checklist (fundamentals, technical trend, relative performance, entry timing) that must be answered before a share count is produced; a named economic-cycle stage with at least two cited indicators — never asserted on vibes — before any sector tilt is applied; and the position size computed via risk-budget-divided-by-per-share-risk, never eyeballed, with the risk budget (money that could be lost) kept explicitly separate from the position cost (money actually spent) — the two numbers get conflated in casual reasoning, and this skill's own source material made exactly that error. Not for options, day-trading, or leveraged/aggressive income strategies — those carry different risk math this skill doesn't cover; name the gap and stop. Not portfolio-level diversification-vs-concentration policy, not a retirement-account or insurance-product decision (Backdoor Roth, Infinite Banking, death-benefit sizing — different skills' territory), not a substitute for a financial advisor, and not a bare conceptual question about how position sizing or sector rotation works with no real trade behind it — that's `learning-gate`.
---

# Equity Trade Decision

"That seems like a reasonable position" is the concept discussed fluently with no arithmetic
behind it. This skill forces three things every time a real trade is on the table: a pre-trade
checklist actually answered rather than assumed clean, an economic-cycle-stage call backed by
named evidence rather than a vibe, and a position size computed from a risk budget — not
guessed, and never confused with the dollar amount actually spent.

## What this does not do

- **Options, day-trading, or leveraged/aggressive income strategies.** Different risk math
  (theta decay, margin calls, assignment risk) that this skill doesn't model. Name the gap
  and stop rather than force this skill's checklist onto a trade shape it wasn't built for.
- **Portfolio-level diversification vs. concentration policy.** Whether to hold 5 stocks or
  50 is a portfolio-construction stance, not a single-trade decision — this skill sizes *one*
  position against *one* risk tier and stops there.
- **Retirement-account or insurance-product decisions.** Backdoor Roth mechanics, Infinite
  Banking timing, death-benefit sizing — separate territory, not a stock trade.
- **Replace a financial advisor.** Names when a real trade thesis needs more research than a
  checklist can verify; never asserts a fundamentals read it hasn't actually seen.
- **Answer a bare conceptual question.** "How does position sizing work" with no real
  capital, entry price, or stop behind it is `learning-gate` territory — this skill activates
  once a real trade with real numbers is on the table.

---

## The Trade Surface

Goes **before** any "yes, buy it" or "here's your share count" answer.

```
Ticker / position:        <symbol>

Pre-trade checklist:
  Fundamentals:            <reviewed — key takeaway | not yet reviewed — ask for the latest
                           annual report / 10-K>
  Technical trend:         <confirmed uptrend, price near its moving average | not confirmed |
                           not yet checked>
  Relative performance:    <vs. a benchmark index (SPY/S&P 500) over a comparable window:
                           outperforming | underperforming | not yet checked>
  Entry timing:            <stabilized after a drop | still falling — wait for confirmation |
                           IPO day — avoid | clean entry, no timing flag>

Cycle stage:               <post-recession recovery | recovery momentum | mid-cycle expansion |
                           late-cycle/peak | recession/contraction> — evidence: <the ≥2
                           indicators actually cited (GDP direction, unemployment trend, yield
                           curve, Fed policy direction, credit spreads) — never asserted with
                           zero indicators named>
Sector tilt:                <this stock's sector> is <favored | neutral | disfavored> for the
                           named stage → <why, from the table below>

Total capital:              $<n>
Risk tier:                  <1% high-risk | 2% medium-risk | 3% low-risk> — <why this tier for
                           this specific trade>
Entry price:                $<n>/share
Stop-loss price:            $<n>/share
Per-share risk:             $<n>   (entry − stop)
Risk budget:                $<n>   (total capital × risk-tier %)
Max shares (risk-based):    <n>    (risk budget ÷ per-share risk)
Position cost:               $<n>   (max shares × entry price) — a DIFFERENT number from the
                           risk budget; this is what actually gets spent, not what's at risk
Position as % of capital:   <pct>% — <within your own concentration comfort | flag: unusually
                           large for one position, consider capping shares by capital instead>

Red flags:                  <checklist item skipped and treated as fine | cycle stage asserted
                           with no evidence | risk budget and position cost conflated | no
                           stop-loss set (can't compute per-share risk without one) | none
                           found>
```

**Every line appears.** A field not yet known is written `not yet known — ask: <the
question>`, never silently omitted or assumed favorable.

---

## Computing position size — never skip this, and never conflate the two numbers

```
1. Risk budget ($)     = Total capital × risk-tier %
2. Per-share risk ($)  = Entry price − Stop-loss price
3. Max shares          = Risk budget ÷ Per-share risk
4. Position cost ($)   = Max shares × Entry price
5. Position % capital  = Position cost ÷ Total capital
```

Step 1 and step 4 are **not the same number** — this is the exact place casual reasoning
fails at the division. The risk budget is what you're willing to *lose* if the stop hits; the
position cost is what you actually *spend* to open the trade. A tight stop makes these two
numbers far apart (small risk, big position); a wide stop brings them closer together (the
same risk budget buys fewer shares). Both must be stated — a verdict that only mentions one of
them hasn't actually sized the trade.

**Worked example** — $10,000 total capital, entry at $12.00/share, stop at $10.50/share,
2% (medium-risk) tier:

- Risk budget = $10,000 × 2% = **$200**
- Per-share risk = $12.00 − $10.50 = **$1.50**
- Max shares = $200 ÷ $1.50 = **133 shares** (round down)
- Position cost = 133 × $12.00 = **$1,596**
- Position as % of capital = $1,596 ÷ $10,000 = **~16%**

Notice $200 (what's at risk) and $1,596 (what's spent) are very different figures — treating
them as interchangeable, or dividing the risk budget by the entry price instead of the
per-share risk, produces a share count with no relationship to the stated risk tolerance. If
the resulting position size is an uncomfortable concentration (here, 16% of capital in one
name), the fix is a tighter stop or a hard capital cap — not silently spending less of the
risk budget while calling it the same calculation.

If no stop-loss is set, say so and stop — per-share risk and everything downstream of it
cannot be computed without one. "I'll set a mental stop" is not a number.

---

## Cycle-stage sector tilt — never assert the stage, cite it

| Stage | Signal (name ≥2) | Tilt toward | Tilt away from |
|---|---|---|---|
| **Post-recession recovery** | GDP inflecting up, Fed holding or cutting, credit spreads narrowing | Banking, financial, insurance — early risk-on rebound | Late-cycle defensives already priced for a downturn |
| **Recovery momentum** | Consumer confidence rising, unemployment falling | Retail, auto, housing — consumer discretionary | Pure defensives, which lag a recovering consumer |
| **Mid-cycle expansion** | Industrial production up, capex rising | Transportation, industrials, basic materials | Early-cycle financials, which have likely already re-rated |
| **Late-cycle / peak** | Inflation firming, yield curve flattening, input costs rising | Energy — demand and pricing power peak late | Rate-sensitive growth names |
| **Recession / contraction** | GDP contracting, unemployment rising, credit spreads widening | Consumer staples, utilities, healthcare, essential services — defensive, inelastic demand | Cyclicals (industrials, discretionary, energy) |

A cycle-stage call with zero cited indicators is a guess wearing a framework's clothes. Two
named, current indicators (not "the economy feels shaky") is the minimum bar before a sector
tilt gets applied. A stock that sits in a disfavored sector for the named stage isn't
automatically a pass — it's a prompt to weight the checklist and risk sizing more
conservatively, not an automatic veto.

---

## Pre-trade checklist — the gate before a share count is produced

1. **Fundamentals.** Actually reviewed the latest annual report / 10-K, not assumed sound.
   "Financials look fine" without having opened them is the same failure `checklist item
   marked satisfied without the underlying document having been seen` is everywhere else in
   this catalog.
2. **Technical trend.** A confirmed uptrend over a meaningful window (weeks-to-months, not one
   candle), with price sitting near or above its moving average — not a single green day.
3. **Relative performance.** Compare the stock's performance to a benchmark (SPY/S&P 500)
   over a comparable window. Underperforming the benchmark while the checklist otherwise looks
   clean is itself a flag worth naming, not skipping past.
4. **Entry timing.** If the price recently dropped, wait for actual stabilization or a
   confirmed reversal before treating it as a buyable dip — a still-falling price is not
   "on sale," it's still falling. Avoid buying on IPO day specifically — no trading history
   exists yet to check the other three items against.

A checklist item silently skipped and treated as "probably fine" is a red flag on its own,
independent of whatever the position-size math says.

---

## Red flags — the decision isn't done

- A share count or "buy it" verdict given with no computed risk budget / per-share risk behind
  it.
- Risk budget and position cost used interchangeably, or position cost computed by dividing
  the risk budget by the entry price instead of the per-share risk.
- A cycle stage named with no indicators cited, or sector tilt applied as if it alone settles
  the trade.
- A pre-trade checklist item marked done without having actually been checked.
- No stop-loss stated, with sizing math produced anyway by assuming one.
- Options, margin, or day-trading brought into a checklist and risk model built for a plain
  long-equity position.

---

## Portability

Repo-agnostic. Writes nothing; produces the Trade Surface in chat. Copy the
`equity-trade-decision/` directory into another repo's `.claude/skills/` to use it there.
