---
name: api-tooling-selection
description: Gated decision for how an AI agent integrates with an external system as a live tool: Postman, OpenAPI, MCP, or direct SDK/HTTP call. Triggers: "should my agent use Postman", "does MCP replace calling the API directly", "how should my agent call this API". Not for wire protocol style — `api-interface-style`. Not for app-code database access — `data-access-layer`.
---

# API Tooling Selection

"Should my agent use Postman" (or "OpenAPI", or "MCP") is rarely a single question — it's usually three different layers being talked about as if they were interchangeable. This skill places the request in the right layer before recommending a stack, so Postman doesn't end up wired into a production runtime path, and MCP doesn't end up as ceremony around a single tool nobody else will ever call.

## Step 1 — Place the request

| What's being asked | What it actually is | Owned by |
|---|---|---|
| Agent needs to call an existing, already-verified API as part of doing its job | Runtime tool implementation | This skill — recommends a plain tool function |
| Agent needs to call several APIs, and more than one agent or client (another IDE, another team's agent) will need the same tool set | Standardized tool exposure | This skill — recommends MCP |
| The target API doesn't exist yet, or exists but is unverified/undocumented, and an agent is about to be pointed at it | Dev-time API validation, before any agent tool touches it | This skill — recommends a Postman/OpenAPI pass first |
| The agent's actual job is to help a human develop, test, or debug APIs — not just call one on the way to a task | Postman-as-capability | This skill — Postman (or its CLI, Newman) becomes a tool the agent drives |
| Agent needs a database GUI/MCP tool (e.g. Beekeeper Studio's MCP integration) to explore data or verify migrations live, as part of the agent's own job | Interactive DB tool for an agent | This skill — same tested/unverified gate, a database client instead of an HTTP client |
| Deciding what wire protocol/interaction style an API surface itself should expose | API surface design | `api-interface-style` |
| Deciding whether OpenAPI/GraphQL schema/protobuf is the authoritative definition of the data or API | Source-of-truth architecture | `database-architecture` |
| *Application code itself* reading/writing a relational database in production (ORM, query builder, raw SQL) | Data access | `data-access-layer` |
| What an automated test suite uses as its database (real instance, substitute engine, mock) | Test-DB mechanism | `database-test-tooling` |
| Which LLM/model handles a given call | Model selection | `model-routing-decision` |
| Pricing the integration once volume and token/request counts are known | Cost | `technical-cost-decision` |

If the request lands in one of the last six rows, say so and hand off — do not build a Postman-vs-MCP recommendation for a question that's actually about protocol design, contract ownership, production database access, test infrastructure, or cost.

## Step 2 — Gate: name these before recommending a stack

- **Is the target API already tested and stable, or unverified/undocumented?** If unverified, the answer always includes a validation pass (Postman, a `.http` file, or plain curl) *before* the agent gets a tool wired to it — skipping straight to agent code against an unverified API just moves debugging into a harder-to-inspect place.
- **What is the agent's job with respect to this API** — is calling it a means to an end (support agent looks up an order, then issues a refund), or is the API itself the subject of the agent's work (an agent that helps an engineer build and test an API)? These get opposite answers.
- **How many distinct agents or clients need this same capability** — just this one agent/app, or will another agent, another team, or an IDE integration need the identical tool set? One consumer doesn't justify a protocol layer; more than one usually does.
- **Does a contract already exist?** An existing OpenAPI spec (or one Postman can export) should generate the tool's request/response schema, not have it hand-typed a second time — for either a plain function or an MCP server.

A bare "what's the difference between Postman and MCP" with no real integration behind it is a definitional question — answer from the Step 1 table, don't force the gate above onto it.

## Step 3 — Recommendation

| Situation | Recommendation |
|---|---|
| API untested/undocumented, agent about to be wired to it | Validate manually first (Postman collection, or curl/`.http` file): confirm auth, pagination, error shapes, edge cases. Export an OpenAPI spec if one doesn't exist. Only then write the tool. |
| Agent consumes one or a few APIs, single agent/app, contract already stable | A plain tool function (`httpx`/`requests`, or the provider's SDK) wrapping the call, given to the LLM as a tool/function definition. No protocol layer needed — it would be indirection with nothing on the other end to justify it. |
| The same tool set needs to be reused across multiple agents, multiple IDEs, or multiple teams | Wrap the tools as an MCP server so they're discovered and invoked in a standardized way, instead of every consumer re-implementing the same HTTP calls. MCP is the standardization answer to "more than one thing needs these tools," not a default for every agent that happens to call an API. |
| The agent's job is literally to help build/test/debug APIs for a human | Postman (or Newman for CLI/CI use) becomes a first-class tool the agent drives: run collections, inspect responses, generate test cases, diff against the OpenAPI contract, flag failures. This is a legitimate "Postman inside the agent's loop" case — the one place Postman stops being a pre-step and becomes the runtime. |
| A contract already exists (OpenAPI, or exportable from Postman) | Generate the tool/function schema — and, if applicable, the MCP tool definitions — from that contract rather than hand-writing both. |
| Agent's job is to explore data or verify migrations live, interactively | A database GUI's MCP integration (e.g. Beekeeper Studio) becomes a first-class tool the agent drives — the same "tool becomes the runtime, not a pre-step" case as Postman-as-capability, just aimed at a database instead of an HTTP API. Still gate on whether the target database/schema is stable or the agent is exploring an unverified migration in progress. |

## Red flags — not done

- Recommended MCP for a single agent talking to a single API with no second consumer in sight
- Pointed an agent at an untested/undocumented API with no validation pass first
- Treated Postman as something the agent's production runtime calls, for an agent whose job is *using* an API rather than *building/testing* one
- Answered "should my agent use Postman" without asking whether the agent's job is consuming the API or developing/testing it
- Hand-wrote a tool schema or MCP tool definition when an OpenAPI contract already existed to generate it from
- Treated this as a protocol-design question (REST vs GraphQL vs gRPC) instead of handing off to `api-interface-style`

## Routing boundaries (full)

- Triggers: "should my agent use Postman", "is Postman part of an AI workflow", "does MCP replace calling the API directly", "how should my agent call this API", "should I hook my agent up to Beekeeper's MCP server to explore/verify data or migrations", "what's the difference between Postman, OpenAPI and MCP", or proposes a stack and wants it checked ("I'll have the agent hit Postman collections directly in production").
- Not for how *application code itself* reads and writes a relational database in production — including when that's phrased as "MCP vs direct" for a database (an MCP database server vs a driver call baked into the app) — that's `data-access-layer`; this skill instead owns an *agent's own* interactive database tool, a different question.
