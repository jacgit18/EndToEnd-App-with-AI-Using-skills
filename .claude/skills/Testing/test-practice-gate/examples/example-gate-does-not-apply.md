# Example: gate does not apply (execution intent)

**Context:** I maintain a payments library. We're migrating the suite from Mocha to Vitest. I have 40 existing tests whose intent is already clear from their names and bodies; I need them translated.

**Me:** "Here are 12 Mocha tests for the refund module. Port them to Vitest — same assertions, same cases, just the framework syntax and the mock API change. I know exactly what these cover."

**Why the gate does not fire:** This is plain execution. The charter already exists — it's encoded in the 12 tests in front of us. The user isn't deciding what to assert; they decided that long ago. Asking them to write a fresh charter would be the paternalism failure `learning-gate` and `problem-solving-gates` both warn against.

**Claude:** Ports the 12 tests directly — `chai.expect` → `expect`, `sinon.stub` → `vi.fn`, `before`/`after` → `beforeAll`/`afterAll` — preserving every case and assertion, flagging only the two places where Sinon and Vitest mock semantics genuinely differ and a judgment call is needed.

---

# Counter-example: superficially similar, gate DOES apply

**Me:** "Here's the refund module. I'm still learning how to test payment code well — write a good test suite for it."

**Why the gate fires here:** "still learning", "write a good suite" with no statement of what "good" covers. The rep — deciding what a refund must guarantee and where it breaks — hasn't happened. Claude asks for the charter (items 1–4 from `SKILL.md`) and points at `charter-guide.md`, rather than generating assertions the user never reasoned about.
