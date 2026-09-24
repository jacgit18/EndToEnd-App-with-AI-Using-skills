# Example invocations (disclosure-gap-audit)

Contents: AI support-reply feature · endpoint removal (routed away) · login handler diff (routed away) · conceptual question

> "We just added a feature that sends the user's support message to GPT to draft a reply.
> Our privacy policy is from last year. What do we need to disclose?"

Inventory gate first: which model provider, is it their API (a subprocessor), are the
messages retained or used for training by the provider, does anything automated act on the
model's output. Spine pass hits probes 1 (AI processing of user input — not disclosed),
3 (subprocessor list — missing the AI vendor), and 12 (policy-vs-practice drift — written
before the feature). Likely findings: one High (`not-disclosed` AI processing of
user-submitted content), one Medium (`disclosed-inadequately` subprocessor list). Security
pass: is the support message scrubbed of anything it shouldn't send to a third party.
Recommendation: policy revision to the "How we use your data" and "Who we share with"
sections; confirm the provider's data-use terms.

> "We're removing the `/v1/export` endpoint, nobody uses it. What breaks?"

Not this skill — that's a blast-radius question → `change-surface-audit`. If the endpoint's
*removal* also means a data flow to a partner stops and the policy claims that flow exists,
the disclosure half of that comes back here; the "what depends on the endpoint" half does
not.

> "Is this login handler secure?" (a diff is pasted)

Not this skill — code-level review of the diff → `security-review`. This skill's security
pass asks whether login *has rate limiting and an authz model at all*, as one row in a
product-wide register, not whether this handler's code is correct.

> "What does GDPR Article 22 actually require?"

Conceptual question → answered directly. No audit, no inventory gate.
