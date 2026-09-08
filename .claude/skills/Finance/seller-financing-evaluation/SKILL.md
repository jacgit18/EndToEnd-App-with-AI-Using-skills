---
name: seller-financing-evaluation
description: Use when a seller-financed (owner-financed) business purchase is on the table — the seller acts as the lender instead of a bank — and someone wants to know if the terms are fair, whether to take the deal, or how to negotiate it. Triggers include "is this seller financing deal fair", "should I do owner financing on this business", "evaluate this seller-financed purchase", a stated or proposed set of terms (down payment, interest rate, term, purchase price), or either the buyer or seller side of a proposed structure. Forces two things Claude tends to discuss only conceptually otherwise: the actual monthly payment computed via amortization and benchmarked against real market ranges (10-50% down, 5-10% interest, 3-7yr term) — the same "reasoning fails at the division, not at the concepts" discipline `technical-cost-decision` forces for engineering costs, applied here to a deal structure instead of a cloud bill — and a named seller-motivation diagnostic (the "7 Ds": Death, Disease, Dullness, Departure, Disagreement, Distress, Divorce) that changes negotiating leverage and risk depending on why the seller is actually selling. Not a vendor or product financing plan for equipment, software, or a service — a payment
plan from a vendor is `technical-cost-decision`'s territory (there's no seller-as-lender
relationship and no business changing hands). Not for deciding whether to buy the business at
all — sourcing, non-financing due diligence, valuation methodology are a broader acquisition
decision this skill doesn't cover. Not a substitute for an attorney, accountant, or independent business appraiser — names them and defers, never drafts the actual promissory note or purchase agreement.
---

# Seller Financing Evaluation

"The terms seem reasonable" is not an evaluation — it's the concept discussed fluently with
no arithmetic behind it. This skill forces two things every time: the actual monthly payment,
computed and benchmarked against real market ranges, not eyeballed; and a direct read on *why*
the seller is financing the deal at all, because that answer changes what leverage exists and
what risk is being taken on.

## What this does not do

- **Decide whether to buy this business at all.** Sourcing the deal, screening the business,
  formal valuation methodology — that's a broader acquisition decision this skill doesn't
  cover. This skill evaluates the *financing structure* once a deal is already on the table.
- **Replace an attorney, accountant, or independent business appraiser.** The promissory
  note, the purchase agreement, UCC-1 filings, and the actual valuation number all need a
  professional. This skill benchmarks the deal's *numbers* and structure; it names where a
  professional is needed and stops there.
- **Draft the contract.** It can name what a term sheet should contain; it does not produce
  a binding legal document.

---

## The Deal Surface

Goes **before** any "this looks fair" verdict, the same way `technical-cost-decision`'s Cost
Surface goes before its recommendation.

```
Purchase price:       $<n>
Down payment:         $<n>  (<pct>% of purchase price)
Financed amount:      $<n>
Interest rate:        <pct>%  annual
Term:                 <n> years (<n> months)
Monthly payment:      $<n>  <computed via amortization, or "as stated by the deal" if given>
Balloon payment:      $<n> due at <when> | none

Benchmark check:
  Down payment:       <pct>% — <within 10-50% typical | below | above> — <what that implies>
  Interest rate:       <pct>% — <within 5-10% typical | below | above> — <what that implies>
  Term:                <n> yrs — <within 3-7yr typical | shorter | longer> — <what that implies>

Cash-flow check:      monthly payment $<n> + operating costs $<n> vs. business's monthly
                      cash flow $<n> → <covers it with margin | tight | doesn't cover it>

Seller motivation (7 Ds): <which D(s) apply, from what was actually said> → <leverage/risk
                      implication>

Red flags:            <balloon payment with no refinance plan | no UCC lien held by seller |
                      no non-compete | seller can't answer why they're selling | none found>
```

**Every line appears.** A term not yet known is written `not yet known — ask: <the question>`,
never silently omitted or assumed favorable.

---

## Computing the monthly payment — never skip this

Standard amortization: `M = P × [r(1+r)^n] / [(1+r)^n − 1]`, where `P` = financed amount,
`r` = monthly interest rate (annual ÷ 12), `n` = number of monthly payments (years × 12).

**Worked example** — $500,000 purchase, $100,000 down (20%), 7% annual interest, 5-year term:
`P = $400,000`, `r = 0.07/12 ≈ 0.00583`, `n = 60`. `M ≈ $7,920/month`. If a balloon payment is
part of the structure, the amortization covers only the portion actually paid down over the
term — say so explicitly rather than implying the loan fully amortizes when it doesn't.

If the deal already states a monthly payment, use it — but still compute it independently
once and flag a mismatch rather than trusting the stated figure blindly. A stated payment that
doesn't match the stated rate/term/amount is either a math error or a term nobody's mentioned
yet (a hidden fee, a different compounding convention) — either way, worth surfacing.

---

## Benchmarking the terms

| Term | Typical range | Outside the range means |
|---|---|---|
| **Down payment** | 10–50% of purchase price | Below 10%: unusually buyer-favorable — ask why (seller distress, illiquid business, weak buyer pool). Above 50%: unusually seller-favorable — the seller is derisking hard, worth asking what they know that isn't being said. |
| **Interest rate** | 5–10% annually | Below 5%: a favor, or the seller values a fast close over yield. Above 10%: pricing in real risk the seller sees — ask what. |
| **Term** | 3–7 years | Shorter: seller wants their money out fast (may signal Distress or Departure). Longer: seller is comfortable being tied to the business's performance — often a good sign about their actual belief in it. |

A term sitting comfortably inside every range is not automatically "fine" — it just means
nothing here forces a question. A term outside a range is not automatically bad — it's a
prompt to ask *why*, not a verdict on its own.

---

## The seller-motivation read — the 7 Ds

Why the seller is financing the deal at all changes both the risk and the leverage available.
Ask directly, don't guess:

| D | What it looks like | What it implies |
|---|---|---|
| **Death** | Owner passed; heirs selling | Estate may need liquidity → flexible terms, but verify heirs actually understand the business |
| **Disease** | Owner exiting for health reasons | May need a fast close; check how much transition support is realistically available |
| **Dullness** | Owner bored/burned out, growth stalled | Real upside for a motivated buyer; often negotiable terms since they "just want out" |
| **Departure** | Relocating, retiring, changing careers | Planned vs. abrupt matters — abrupt departures risk losing supplier/customer relationships |
| **Disagreement** | Partner/co-owner conflict forcing a sale | Higher risk — a difficult seller during financing is a real cost; verify who actually controls the sale |
| **Distress** | Financial trouble, can't find a cash buyer | Higher risk signal — seller financing may be the only option left, not a vote of confidence |
| **Divorce** | Personal breakup, needs cash fast | Urgency may mean room to negotiate, but check for a spouse's undisclosed stake |

**Ask directly, don't infer from vibes:**
- "What's prompting the sale?" — surfaces Death, Disease, Departure, Divorce, Distress.
- "Have you been actively involved in the business lately?" — surfaces Dullness or Disagreement.
- "Are you looking for a quick exit, or do you want to stay involved?" — clarifies flexibility.
- "How has the business performed the last 12–24 months?" — checks for Distress before
  trusting the financials at face value.

**Distress or Disagreement → treat as a higher-risk signal**, not just a negotiating
opportunity. **Departure or Dullness → often genuine opportunity** with room to negotiate,
since the seller's motivation to exit doesn't necessarily reflect the business's health.

---

## The checklist — name what hasn't been checked, don't assume it's fine

1. **The business itself** — 3 years of financials (P&L, balance sheet, tax returns), cash
   flow vs. the computed payment + operating costs, an independent valuation, industry/market
   conditions.
2. **The financing offer** — down payment, rate, term, balloon terms, prepayment terms (all in
   the Deal Surface above).
3. **Legal & contractual** — a promissory note, security/collateral (lien, personal
   guarantee), a non-compete, default/repossession terms. Name that a lawyer reviews the
   actual documents — don't draft them here.
4. **Due diligence on the seller** — verified ownership, no undisclosed liabilities, UCC
   filings checked, the 7-Ds read above.
5. **Transition plan** — training/handover period, key-employee retention, supplier/customer
   relationship stability.

**A checklist item not yet addressed is a named gap, not a silent assumption.** "Financials:
not yet reviewed — ask for 3 years of P&L and tax returns" is a complete, honest answer. Do
not write "financials appear sound" without having actually seen them.

---

## Negotiation levers — tie these to what the Deal Surface actually found

**Buyer-side**, when a term sits seller-favorable: push down payment toward the low end
(10–15%) and negotiate up from there; use current SBA loan rates as leverage on interest;
ask for an interest-only grace period (3–6 months); avoid a balloon payment if possible, or
negotiate a refinance option if one exists; if the seller shows real confidence in the
business, that should translate into flexible terms, not just a talking point.

**Seller-side**, when a term sits buyer-favorable: push the down payment toward 20–30%+ to
reduce exposure; price the interest rate for the actual risk being taken on; file a UCC-1 and
retain a lien on business assets; require a personal guarantee; limit the buyer's ability to
resell before the loan is repaid.

Only recommend a lever that responds to something the Deal Surface actually flagged — a
generic negotiation-tips list untethered to this specific deal's numbers is the same failure
as a verdict with no arithmetic behind it.

---

## Red flags — the evaluation isn't done

- A "this looks fair" or "this looks risky" verdict with no computed monthly payment behind
  it.
- A benchmark table with any row skipped rather than marked outside/inside the range.
- Seller motivation asserted ("they seem eager to sell") without the 7-Ds question actually
  asked.
- A checklist item marked as satisfied without the underlying document/number actually having
  been seen.
- Legal or valuation advice given as if this skill were a substitute for an attorney or an
  appraiser.
- A balloon payment present in the deal with no mention of what happens when it comes due.

---

## Portability

Repo-agnostic. Writes nothing; produces the Deal Surface in chat. Copy the
`seller-financing-evaluation/` directory into another repo's `.claude/skills/` to use it
there.
