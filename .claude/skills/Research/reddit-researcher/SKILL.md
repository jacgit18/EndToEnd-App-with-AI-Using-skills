---
name: reddit-researcher
description: "Current-awareness research across three free sources — Reddit, Hacker News, and the open web — for roughly the last 30 days. Synthesizes findings into a grounded, cited report with relevance filtering, deduplication, cross-source signal detection, and anti-hallucination guardrails. No paid APIs or MCP servers required."
argument-hint: "React vs Vue, best AI coding tools, latest news on OpenAI"
license: MIT
user-invocable: true
---

# Reddit Researcher

Research ANY topic across Reddit, Hacker News, and the open web. Surface what people are
actually discussing, recommending, and debating right now — sourced from roughly the last
30 days.

This version uses only free, no-auth sources: Reddit's public JSON search, the Algolia
Hacker News API, and Claude's native `WebSearch` / `WebFetch`. See **Notes & limitations**
at the end for the optional paid upgrade path (X, LinkedIn, YouTube via Apify).

---

## Step 0 — Parse User Intent

Before doing anything, parse the user's input for:

**1. TOPIC** — What they want to research.

**2. QUERY_TYPE** — Classify using these patterns (check in priority order):

| QUERY_TYPE | Trigger patterns |
| :---- | :---- |
| comparison | "vs", "versus", "compared to", "better than", "difference between", "switch from" |
| how_to | "how to", "tutorial", "best practices", "tips", "examples", "setup", "build a" |
| product | "price", "pricing", "buy", "alternative", "prompts", "template", "subscription" |
| opinion | "worth it", "thoughts on", "review", "should I", "pros and cons", "recommend" |
| prediction | "predict", "forecast", "odds", "chance", "probability", "outcome" |
| concept | "what is", "what are", "explain", "how does", "overview", "introduction" |
| breaking_news | "latest", "breaking", "just announced", "launched", "new", "update", "news" |
| breaking_news | (default if nothing matches) |

**3. Source priority by QUERY_TYPE** — use this to weight results during synthesis:

| QUERY_TYPE | Source priority (highest first) |
| :---- | :---- |
| product | Reddit, Web, HN |
| concept | HN, Web, Reddit |
| opinion | Reddit, HN, Web |
| how_to | Reddit, HN, Web |
| comparison | Reddit, HN, Web |
| breaking_news | Web, Reddit, HN |
| prediction | Reddit, HN, Web |

Store:

- `TOPIC` = extracted topic
- `QUERY_TYPE` = detected type
- `TOPIC_A` / `TOPIC_B` = only for comparison
- `DATE_30_DAYS_AGO` = today minus 30 days, `YYYY-MM-DD`
- `UNIX_30_DAYS_AGO` = `DATE_30_DAYS_AGO` as a Unix timestamp

**Before calling any tools, display this to the user:**

> Researching "{TOPIC}" across Reddit, Hacker News, and the web.
> Covering roughly the last 30 days ({DATE_30_DAYS_AGO} → today).
> Query type: {QUERY_TYPE}
> Pulling sources now...

---

## Step 1 — Pull the Three Sources

Run all three pulls in the same batch of tool calls where your tools allow it — do not wait
for one before starting the next. Each pull produces a plain-text list of items.

### Source A — Reddit

**Primary:** `WebFetch` this URL (URL-encode `{TOPIC}`):

```
https://www.reddit.com/search.json?q={TOPIC}&sort=relevance&t=month&limit=25&raw_json=1
```

The response is JSON. Each result is under `data.children[].data`. For each post return:

- Post title and full URL (`https://www.reddit.com` + `permalink`)
- Subreddit (`subreddit`)
- Upvotes (`ups`), upvote ratio (`upvote_ratio`), comment count (`num_comments`)
- Post date (`created_utc`, convert to a date)
- Post body (`selftext`, first 300 chars if long)

Lead with highest-upvote posts. Group by subreddit if patterns emerge.

**Fallback:** Reddit rate-limits automated access, so if the fetch errors or returns an
empty body, immediately switch to `WebSearch` for `site:reddit.com {TOPIC}` and `WebFetch`
the top 5–8 threads. Engagement numbers may be unavailable on this path — score those items
on relevance + recency only and note "engagement data unavailable" once in the report.

If both paths yield nothing: write "Reddit: No results found."

### Source B — Hacker News

`WebFetch` the Algolia HN API (free, no auth):

```
https://hn.algolia.com/api/v1/search_by_date?query={TOPIC_URL_ENCODED}&tags=story&numericFilters=created_at_i>{UNIX_30_DAYS_AGO}&hitsPerPage=30
```

Replace `{TOPIC_URL_ENCODED}` with the URL-encoded topic and `{UNIX_30_DAYS_AGO}` with the
actual Unix timestamp. For each story return:

- Story title and URL (use the `url` field, or `https://news.ycombinator.com/item?id=<objectID>`)
- Points (`points`) and comment count (`num_comments`)
- Date posted (`created_at`)

Lead with highest-points stories. Note any that sparked large comment threads. If 0 results:
write "Hacker News: No results found."

### Source C — Web

`WebSearch` with 2–3 angle variations, then `WebFetch` the full content of the top 5–10
most relevant URLs:

- `"{TOPIC}" after:{DATE_30_DAYS_AGO}`
- `"{TOPIC}" news latest`
- `"{TOPIC}" analysis` (add the current year if it sharpens results)

Authoritative tech press (TechCrunch, The Verge, Ars Technica, official blogs, etc.) counts
as web here — no separate pass for it. For each page return:

- Title and source / publication name
- URL
- Key points, findings, or quotes
- Date published (if available)

Group by theme. Lead with the most authoritative and recent sources. Only include content
from roughly the last 30 days. If nothing qualifies: write "Web: No relevant results found."

---

## Step 2 — Relevance Filtering

Before scoring, filter out items that are not relevant to the topic.

For each item returned by any source:

1. **Tokenize** the item's title/text: lowercase, remove punctuation, remove stopwords
   (the, a, an, to, for, is, in, of, on, and, with, from, by, at, this, that, it, i, we,
   you, are, do, can, be, or, not, so, if, but).
2. **Tokenize** the topic query the same way.
3. **Check overlap** — what fraction of the topic's meaningful tokens appear in the item?
   - Exact phrase match anywhere → strong relevance signal (+bonus)
   - 70%+ token overlap → relevant, keep
   - 40–69% overlap → borderline, keep but lower weight
   - Under 40% overlap → likely off-topic, discard unless very high engagement
4. **Generic tokens** ("best", "tips", "news", "update", "review", "vs") do NOT count as
   relevance on their own. An item must match at least one specific topic token to be kept.
5. **Synonym expansion** — treat these as equivalent: js ↔ javascript, ts ↔ typescript,
   ai ↔ artificial intelligence, ml ↔ machine learning, react ↔ reactjs.

---

## Step 3 — Deduplication

### Within each source

For each source's results independently:

- Compare item titles/text pairwise
- If two items share 70%+ of their meaningful words (excluding stopwords), they are
  near-duplicates
- Keep only the higher-engagement one, discard the other

### Across sources

Compare items across all three sources to find the same story appearing in multiple places:

- Strip "Show HN:" / "Ask HN:" prefixes from HN titles before comparing
- If two items from different sources share 40%+ meaningful word overlap → same story
- Tag both with `[CROSS-SOURCE: also on Reddit, HN]` — do NOT delete either
- **Cross-source items are the strongest signals in the report.** Lead with them.

---

## Step 4 — Scoring

Score every item 0–100.

### Reddit (has engagement data)

- Relevance: 45% · Recency: 25% · Engagement: 30%
- Engagement formula: `0.50 × log(upvotes+1) + 0.35 × log(comments+1) + 0.15 × upvote_ratio`
- Reddit items on the search fallback path (no engagement data): score as Web below.

### Hacker News (has engagement data)

- Relevance: 45% · Recency: 25% · Engagement: 30%
- Engagement formula: `0.60 × log(points+1) + 0.40 × log(comments+1)`

### Web (no engagement data — source penalty)

- Relevance: 55% · Recency: 45%
- Subtract 10–15 points from the final score (no crowd validation)
- Exception: `concept` and `how_to` queries → no web penalty (authoritative docs are valuable)

### Recency score

- Last 7 days: 100
- 8–14 days ago: 80
- 15–21 days ago: 60
- 22–30 days ago: 40
- Older than ~30 days: discard

### Cross-source bonus

- Item appears on 2 sources: +10 points
- Item appears on all 3 sources: +20 points

---

## Step 5 — Synthesize Into Report

**CRITICAL: Ground your synthesis in what the sources ACTUALLY returned. Do not fill gaps
with your own pre-existing knowledge.**

Structure based on `QUERY_TYPE`.

### If QUERY_TYPE = comparison

Pull all three sources TWICE — once for `TOPIC_A`, once for `TOPIC_B` — then a third pass
for "{TOPIC_A} vs {TOPIC_B}". Synthesize all three:

```
# {TOPIC_A} vs {TOPIC_B}: What the Community Says (Last ~30 Days)

## Quick Verdict
[1–2 sentences: which the community prefers and why, with source counts]

## {TOPIC_A}
Community sentiment: [Positive / Mixed / Negative] ({N} mentions across {sources})
Strengths: [bullets with source attribution]
Weaknesses: [bullets with source attribution]

## {TOPIC_B}
Community sentiment: [Positive / Mixed / Negative]
Strengths: [bullets with source attribution]
Weaknesses: [bullets with source attribution]

## Head-to-Head
| Dimension | {TOPIC_A} | {TOPIC_B} |
|-----------|-----------|-----------|
| [dim 1]   | ...       | ...       |

## Bottom Line
Choose {TOPIC_A} if... | Choose {TOPIC_B} if...
(based on actual community data, not assumptions)
```

### If QUERY_TYPE = product or opinion (recommendations)

```
Most mentioned for {TOPIC}:

[Item Name] — {N}x mentions
What it is: [1 sentence]
Why people recommend it: [key reasons]
Sources: r/subreddit, HN, [publication]

[Item Name] — {N}x mentions
...

Notable mentions: [items with 1–2 mentions]
```

### If QUERY_TYPE = breaking_news, concept, how_to, or prediction

```
What I learned about {TOPIC}:

**[Finding 1]** — [1–2 sentences on what people are saying, cite source]
**[Finding 2]** — [1–2 sentences, cite source]
**[Finding 3]** — [1–2 sentences, cite source]

KEY PATTERNS from the research:
1. [Pattern] — per r/subreddit or HN
2. [Pattern] — per source
3. [Pattern] — per source
```

---

## Citation Rules

**Priority order — use the highest available:**

1. Subreddits — "per r/subreddit" (prefer quoting top posts/comments over bare thread titles)
2. Hacker News — "per HN"
3. Web — publication name, e.g. "per TechCrunch", "per Ars Technica"

**Rules:**

- 1–2 citations per finding — never chain multiple ("per r/x, r/y, r/z" → pick the strongest)
- Never paste raw URLs — use source names only
- Lead with what real people are saying, not with publications

---

## Step 6 — Stats Block

After synthesis, display this. **Calculate actual totals from what the sources returned.
Omit any line with 0 results.**

```
---
✅ Research complete!

├─ 🟠 Reddit: {N} posts │ {N} upvotes │ {N} comments
├─ 🟡 HN: {N} stories │ {N} points │ {N} comments
├─ 🌐 Web: {N} pages — Source, Source, Source
├─ 🔗 Cross-source signals: {N} stories appeared on 2+ sources
└─ 🗣️ Top voices: r/{sub}, r/{sub}, [publication]
---
```

For the Web line — strip protocol/path, use the readable publication name only
(`techcrunch.com/...` → TechCrunch). Never paste URLs.

---

## Step 7 — Follow-Up Invitation

End with an invitation referencing **specific things you actually found** — not generic
suggestions:

```
I'm now up to date on {TOPIC} from the last ~30 days.

Want me to go deeper on anything? For example:
- [Specific finding #1 from research]
- [Specific finding #2 from research]
- [Specific finding #3 from research]
```

---

## Rules

- Never fabricate findings — only synthesize what the sources actually returned
- Cross-source signals are the strongest evidence — always lead with them
- If all sources return no results, say so clearly and suggest the user refine the topic
- Keep the report focused — prioritize signal over volume
- Self-check before publishing: does your synthesis match what the research ACTUALLY says?
  Rewrite if you catch yourself using prior knowledge instead of the research output.

---

## Anti-Hallucination Guardrails

**CRITICAL: Ground your synthesis in the ACTUAL research content, not your pre-existing
knowledge.**

Read the research output carefully. Pay attention to:

- **Exact product/tool names** mentioned — if research mentions "ToolX", that is a DIFFERENT
  product than something similar you already know. Don't conflate them.
- **Specific quotes and insights** from the sources — use THESE, not generic knowledge
- **What the sources actually say**, not what you assume the topic is about

**ANTI-PATTERN TO AVOID:** If the user asks about "topic A" and research returns content
about "topic A variant", do NOT synthesize it as a different-but-related topic just because
they sound similar. Read what the research actually says.

**SELF-CHECK before displaying:** Re-read your "What I learned" section. Does it match what
the research ACTUALLY says? If you catch yourself projecting your own knowledge instead of
the research, rewrite it.

---

## WAIT FOR USER RESPONSE

**After displaying the report and follow-up invitation — STOP.**

Do NOT call any more tools. Do NOT keep writing. Wait for the user to respond.

---

## Context Memory

After research is complete, keep these for the rest of the conversation:

- **TOPIC**: {topic}
- **QUERY_TYPE**: {type}
- **KEY PATTERNS**: {top 3–5 patterns you actually found}
- **TOP SOURCES**: {highest-engagement subreddits, HN threads, publications}
- **RESEARCH FINDINGS**: {key facts and insights from the research}

When the user asks follow-up questions:

- **Do NOT run new searches** — you already have the research
- **Answer from what you learned** — cite the Reddit threads, HN stories, publications
- **Only do new research** if the user explicitly asks about a DIFFERENT topic

---

## When User Responds

Read their response and match the intent:

- A **QUESTION** about the topic → answer from your research (no new searches)
- Asks to **GO DEEPER** on a subtopic → elaborate using your research findings
- Describes something they want to **CREATE** → write one tailored prompt (see below)
- Asks for a **PROMPT** explicitly → write one tailored prompt (see below)

**Only write a prompt when the user wants one.** Don't force a prompt on someone who asked
a question.

---

## Writing a Prompt

When the user wants a prompt, write a **single, highly-tailored prompt** grounded in the
research.

**CRITICAL: Match the FORMAT the research recommends.** If the research found that a specific
structure or style works better, use it. Don't write generic prose when the research points
to structured prompts, or vice versa.

**Quality checklist before delivering:**

- [ ] Format matches what the research actually recommended
- [ ] Directly addresses what the user said they want to create
- [ ] Uses specific patterns/keywords discovered in research
- [ ] Ready to paste with zero edits (or minimal, clearly marked placeholders)

**Output format:**

```
Here's your prompt:
---
[The actual prompt]
---
This uses [brief 1-line explanation of what research insight you applied].
```

---

## After Each Prompt

End with a footer showing what the research was based on, then offer more:

```
---
📚 Based on: {N} Reddit posts ({N} upvotes) + {N} HN stories ({N} points) + {N} web pages
Want another prompt? Just tell me what you're creating next.
```

Omit any source that returned 0 results.

---

## Query-Type Follow-Up Invitations

Use the matching format based on `QUERY_TYPE` (Step 7):

**product or opinion (recommendations):**

```
I'm up to date on {TOPIC}. Want me to go deeper? For example:
- [Compare specific item A vs item B from the results]
- [Explain why item C is trending right now]
- [Help you get started with item D]
```

**breaking_news or concept (news / general):**

```
I'm up to date on {TOPIC}. Some things you could ask:
- [Specific follow-up about the biggest story from research]
- [Question about implications of a key development]
- [Question about what might happen next based on current trajectory]
```

**how_to:**

```
I'm up to date on {TOPIC}. Want me to go deeper? For example:
- [Step-by-step breakdown of the most recommended approach]
- [Common pitfall people mention and how to avoid it]
- [Write you a ready-to-use prompt/template based on the research]
```

**comparison:**

```
I've compared {TOPIC_A} vs {TOPIC_B} using the latest community data. You could ask:
- [Deep dive into {TOPIC_A} strengths from the research]
- [Deep dive into {TOPIC_B} strengths from the research]
- [Focus on a specific dimension from the comparison table]
```

**prediction:**

```
I'm up to date on {TOPIC} predictions from the last ~30 days. You could ask:
- [Most cited reason for the leading outcome, per research]
- [The biggest dissenting view from the research]
- [What signal to watch next based on what sources are tracking]
```

---

## Notes & Limitations

**What this skill does:**

- `WebFetch`es Reddit's public JSON search (`reddit.com/search.json`) — no auth, but Reddit
  rate-limits automated access, so a `site:reddit.com` `WebSearch` fallback is built in
- `WebFetch`es the Algolia Hacker News Search API (`hn.algolia.com`) — free, no auth
- Uses Claude's native `WebSearch` + `WebFetch` for the open web

**What this skill does NOT do:**

- Does not post, like, or modify content anywhere
- Does not access your accounts on any platform
- Does not use or store API keys
- Does not send data to any endpoint not listed above

**Cost:** effectively free — only your normal `WebSearch` / `WebFetch` usage. No subscription.

**Coverage trade-off:** dropping X/Twitter, YouTube, and LinkedIn removes real-time social
chatter and video transcripts. For most topics Reddit + HN + Web carry the majority of the
signal. If you specifically need X or LinkedIn sentiment, the only practical route is a paid
scraper (e.g. Apify actors `apidojo/tweet-scraper`, `harvestapi/linkedin-post-search` via
the Apify MCP, ~$29/mo) or the official X API (~$100/mo). Add those back as extra sources in
Step 1 only if that coverage is worth the cost to you.
