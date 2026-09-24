# Example: Rubber Duck Mode

**Context:** I'm building a small job queue. Workers occasionally process the same job twice under load.

**Precondition check:** Do I have a hypothesis? Yes — I think two workers poll the same "pending" row before either marks it claimed, so both grab it.

**Me:** "I'm debugging duplicate job processing. My hypothesis: there's a race between the SELECT that finds a pending job and the UPDATE that marks it claimed — two workers can both SELECT the same row before either UPDATEs it. Can you rubber-duck this with me?"

**Claude:** "So worker A reads row 7 as pending, worker B reads it as pending too before A's UPDATE lands, and both process it. If that's right — does the duplication rate track with the number of concurrent workers, or does it happen even with a single worker?"

**Me:** "Good question. It happens even with one worker sometimes, just less often."

**Claude:** "A single worker duplicating rules out a cross-worker race — there's no second reader in that window. What else touches 'pending' status? Anything retry-related, a timeout requeue?"

**Me:** "...I do have a stale-job sweep that resets anything 'claimed' for over 30s back to 'pending', in case a worker crashed. If a job takes just over 30s, the sweep requeues it while the original worker is still finishing."

**Outcome:** I found the actual bug myself — not the race I guessed, but the sweep's timeout being too aggressive. Claude never told me this; the falsification question (does it happen with one worker?) pointed me at a different mechanism. Fix: extend the timeout, have workers heartbeat instead of using a fixed window.
