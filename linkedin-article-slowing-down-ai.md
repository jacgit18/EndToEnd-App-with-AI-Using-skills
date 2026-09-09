# The speed bumps I put in front of my AI

Most people using an AI coding assistant have had this moment. You describe a feature, and thirty seconds later there are forty new files in your project. It compiles. The tests pass. And you could not explain half of it to a teammate if they asked.

That trade is fine some of the time. It is a bad habit all of the time. I've spent the last few months building a set of tools to make the other choice easier: to slow the AI down on purpose and put friction back where the learning used to be.

## What I built

A personal library of "skills." Each one is a short instruction file that changes how the AI works with me on a specific kind of task. There are more than fifty now, grouped by area — architecture, data modeling, testing, prompt work, and the boring-but-necessary git rituals.

Most of them are gates. A gate withholds the answer until I've done a step myself.

The ones that get the most use:

- One classifies what I'm actually trying to do before it answers. Am I trying to learn this, or do I just need to get past it? If it's the first, the skill caps how much of the thinking the AI is allowed to do and hands the rep back to me.
- Before it helps me debug, I have to write down my hypothesis. Before an architecture call, I have to generate the options myself and say why I'm leaning one way. The AI critiques my list instead of replacing it.
- No multi-file build starts without a written spec. The work gets checked against that spec at set points, and anything that drifted gets named out loud instead of quietly folded in.
- A planned build gets delivered one file at a time. The AI writes a file, explains why it's shaped that way and how it connects to what's already there, then stops. I have to explain it back before it writes the next one.

When I add a new skill, I run it against the existing ones to find the spots where two of them fight, or one quietly overrides another, and I fix those before the skill goes in the library.

## Why bother

The friction is the point. The steps I'd skip when I let the tool run — writing the hypothesis, listing the options, reading each file as it lands — are the steps that build judgment. Skip enough of them and you end up fast at producing code and slow at knowing whether it's any good.

There's a maintenance argument too. When I've read every file in a slice as it was written, I can change one piece six weeks later without the whole thing coming apart. When I haven't, every change is archaeology.

## System design, done slower

I've changed how I approach design work. It now runs as a chain, and each link is a gate that won't let me skip ahead.

First, scoping. Instead of going to a diagram, I write a living document: what's in scope, what's explicitly out, the non-functional targets, the constraints. Then I pick the one or two decisions that actually deserve deep thought.

Then the technology choices, one at a time, the way a system design interview would run them. For each decision: the realistic options, the two or three things that actually separate them for this build, an honest comparison that includes where the option I'm about to reject is the better one, a recommendation with a reason tied to one of those things, and then my call. Each decision ends as a one-page record. Only after that does a spec get written, and only then does the build start, one file at a time.

I'm building a personal finance dashboard on this chain. Here's the part that felt strange. I had already picked the stack — language, framework, database, all of it — and written it into the plan. To do this properly I archived that decision, marked it superseded, and reopened every choice so I could reason through it in the open instead of trusting a call I'd made in a hurry. The old picks are still on file as input, not as the answer. Some of them will probably win again. This time I'll know why.

## Where agents come in

The skills are procedures that run inside one conversation, with me in the loop. Agents are the next step, and I'm being careful about where they go.

So far there's one: a subagent that takes a single already-approved slice of a spec, builds it in an isolated copy of the repo, and reports back what it did and anything that fell outside the spec. It doesn't decide scope. It doesn't merge. A human runs the result through the same drift check everything else goes through.

The rule I'm using: a fixed sequence of steps stays a script. A high-stakes step stays something I do myself. An agent has to earn its place by being genuinely open-ended and low enough stakes to hand off. Most things aren't, yet.

## The part I keep thinking about

The tools that make you productive in your first week are the same tools that can keep you from building the thing that makes you worth hiring in year three: the judgment to look at generated code and know it's wrong.

That judgment doesn't come from reading AI output. It comes from having written the thing yourself enough times that the wrong version looks wrong immediately. If you're early in your career right now, the market is already shifting from "can you produce this" to "can you review this." The second skill is built on reps of the first.

I'm somewhere in the middle of that road myself, building toward architect one joint at a time. The skill library is a dated record of the work — not a portfolio, a log. It grows every time I catch myself about to let the tool do a rep I should have done.

If you're working this way too, I'd like to hear how you're drawing the line.
