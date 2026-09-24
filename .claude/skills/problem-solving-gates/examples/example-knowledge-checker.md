# Example: Knowledge Checker Mode

**Context:** I just read how React's `useEffect` cleanup function works and want to verify I understood it.

**Precondition check:** Have I attempted an explanation first? Yes — written below before asking.

**Me:** "My understanding: the function you return from `useEffect` runs right before the effect re-runs on the next render, and once on unmount. It's for cleaning up subscriptions, timers, or listeners so they don't pile up. Can you check this?"

**Claude:** "Take this: `useEffect(() => { const id = setInterval(tick, 1000); return () => clearInterval(id); }, [count])`, where `count` changes every tick. Walk through three consecutive re-renders — when does cleanup run relative to the effect re-running, and does the interval ever leak or duplicate?"

**Me:** "On each render where `count` changed, React runs the previous cleanup first, clearing the old interval, then the new effect sets up a fresh one. One interval at a time, no leak. But is cleanup from render N running before render N+1's effect, or could effects batch?"

**Claude:** "Order's right — cleanup then effect, paired per change, not batched across changes. Since you're asking about batching: what does your model predict if `count` changes twice in the same synchronous handler, before React re-renders at all?"

**Me:** "If updates batch into one render, the effect only sees the final value — no cleanup/effect pair runs for the intermediate value, since there's no render for it."

**Outcome:** My core explanation held up. The scenario surfaced a real gap I hadn't considered — batching — and I reasoned it through myself. Confirmed correct after the fact, not before.
