# Claude Trace Analysis After ABP Revision

Date: 2026-04-10

Inputs:
- `troubleshooting/ABP/after-revision-trace-claude.md`
- Current router and tool-discovery code in `tools/os_mcp.py` and `server/mcp/tool_search.py`
- Current council-tax tools in `tools/council_tax.py`

## 1. Redaction Status

The trace has been redacted in place and is now suitable for sharing.

Sensitive values removed or normalized:
- local usernames
- host and VM paths
- Claude session identifiers and UUID-like values
- sampled UPRNs
- sampled postcodes
- user-specific filenames and order references

Verification completed:
- no remaining raw sample UPRNs from the trace review set
- no remaining raw sample postcodes from the trace review set
- no remaining raw VOA property URLs with numeric tails from the trace review set

## 2. Executive Summary

The rebuild improved server-side discoverability but did not solve the end-to-end client experience.

What improved:
- `os_mcp.descriptor` now reports both `council_tax.band_lookup` and `council_tax.query` as `always_loaded`.
- The `property_tax` toolset is present in descriptor output.
- The council-tax tools are registered in the server and covered by tests.

What still failed:
- Claude still could not call the council-tax tools from its available function surface.
- `os_mcp.route_query` misrouted a council-tax prompt to linked-ID tools.
- `os_mcp.select_toolsets` rejected a JSON-stringified array that an agent plausibly produced.
- Because the right tools were not callable, Claude fell back to shell scripting, HTML scraping, and ad hoc dependency installation.

Main conclusion:
- The current system is good enough for a human who knows the tool names and the repo, but still too brittle for autonomous AI clients. The failure was not one bug. It was a chain:
  1. discovery said the right tools existed
  2. callable tool exposure did not match that promise
  3. routing guidance pointed to the wrong domain
  4. low-level tools were exposed where a resumable batch task was actually needed

## 3. What Claude Actually Did

Observed high-level sequence from the trace:
- inspected the input CSV and row count
- called `os_mcp.descriptor`
- saw `council_tax.band_lookup` and `council_tax.query` listed as always loaded
- attempted toolset discovery for `property_tax`
- hit a shape error because `includeToolsets` was passed as a JSON string instead of an array
- retried with `toolset=property_tax` and got a correct discovery result
- still could not call the council-tax tools through the host interface
- spawned a subagent to verify whether the tools were actually callable
- pivoted to `ons_geo` tools, which were irrelevant for the user task and had only bootstrap cache data
- pivoted again to shell and web access
- discovered an existing partially-enriched CSV and local ABP xref data
- eventually inferred that `council_tax.query` used the AddressBase xref parquet, but too late to use it through MCP
- reimplemented GOV.UK council-tax scraping logic in Python
- hit rate limits, process-persistence issues, dependency issues, and path portability issues

This is the critical pattern:
- MCP usage was front-loaded
- once tool exposure and routing failed, Claude left MCP almost entirely
- after that point the session became a shell-debugging exercise rather than a tool-using workflow

## 4. Detailed Behaviour Findings

### 4.1 Descriptor success did not translate into callable tools

Evidence:
- the descriptor listed both council-tax tools as always loaded
- Claude repeatedly stated that those tools were not present in its callable interface
- the subagent independently reached the same conclusion

Interpretation:
- this is not primarily a `tools/council_tax.py` registration bug
- it is an interop bug at the host, bridge, tool-loading, or client-surface layer
- from the client point of view, the system broke its contract: "discoverable" implied "usable", but was false in practice

Operational lesson:
- `always_loaded` needs to be trustworthy from the client point of view, not only from server metadata

### 4.2 `select_toolsets` is too strict for real agent input

Observed failure:
- Claude passed `includeToolsets` as the string `["property_tax"]`
- the server treated that as one literal toolset name and rejected it as unknown

Current cause:
- `server/mcp/tool_search.py:284` only supports:
  - comma-delimited strings
  - arrays of strings
- it does not attempt to parse JSON-array strings

Why this matters:
- agents frequently serialize arrays as strings when crossing tool or host boundaries
- strict rejection is defensible for a typed client, but not pragmatic for AI-client interoperability

Lesson:
- for interop tools, permissive normalization is usually better than hard rejection when the intended meaning is obvious

### 4.3 `route_query` misclassified council-tax prompts

Observed failure:
- the prompt "council tax band lookup by UPRN or postcode" was routed to `os_linked_ids.get`

Current cause:
- `tools/os_mcp.py` has no dedicated council-tax or property-tax intent
- UPRN-heavy language biases the classifier toward `QueryIntent.LINKED_IDS`
- `INTENT_TOOLSET_MAP` has no property-tax path
- `_get_tool_for_intent` has no council-tax branch

This is a real product bug, not just an LLM mistake.

Effect:
- Claude was actively nudged away from the correct domain by the server's own guidance

Lesson:
- high-level router tools must recognize domain-specific intents whenever the server exposes domain-specific tools

### 4.4 ONS fallback created noise, not progress

Observed behaviour:
- Claude tried `ons_geo.by_uprn` and `ons_geo.by_postcode`
- results were `NOT_FOUND`
- the trace showed the local ONS caches were effectively bootstrap-only

Why this matters:
- the tools worked as designed, but they were a poor fallback for this task
- the server did not communicate cache maturity strongly enough to stop wasted exploration

Lesson:
- if a dataset is only minimally seeded, the tooling should signal "not production-ready for general lookups" rather than behaving like a normal miss

### 4.5 The user task was batch enrichment, not a single lookup

The trace exposes a design mismatch:
- we exposed low-level lookup tools
- the user actually wanted a workflow: enrich a large CSV using local ABP data and optionally live council-tax band data

Claude compensated by building its own workflow:
- scan CSV
- dedupe postcodes
- scrape GOV.UK
- checkpoint progress
- resume failed rows

That workflow belongs in `mcp-geo`, not in a client’s shell session.

### 4.6 Claude eventually learned the right data model, but too late

What Claude figured out:
- `council_tax.query` is backed by local AddressBase Premium xref data
- the parquet source is the right substrate for large UPRN batches
- GOV.UK band lookup is separate and rate-limited

What this tells us:
- the underlying server design is directionally right
- the problem is discoverability, routing, workflow surface, and fallback guidance

### 4.7 Once pushed into shell mode, Claude behaved predictably but inefficiently

Shell-side behaviours were reasonable from Claude’s perspective:
- inspected existing files
- reused the partially-enriched CSV
- wrote Python to scrape GOV.UK
- added backoff and retries
- worked around path issues

But from a product perspective these are anti-patterns:
- logic duplicated from `mcp-geo`
- dependency installation inside a task workspace
- reliance on unstable HTML and rate-limited public services
- long-running work coupled to an ephemeral client session

Lesson:
- when the MCP surface is incomplete, an AI client will try to rebuild the missing product around it

## 5. What We Can Learn From This Trace

### 5.1 Discovery is not enough

A descriptor can be correct and still fail the user if:
- the host does not expose the tools
- the router recommends the wrong branch
- the task requires orchestration rather than single calls

For AI clients, "I can see it in metadata" is not equivalent to "I can successfully use it."

### 5.2 AI clients need tolerant interfaces

Common AI-client realities:
- array-like values may arrive as JSON strings
- clients may overuse semantically nearby tools when routing is ambiguous
- they often need explicit "do this next" guidance, not only schemas

The server should absorb harmless serialization variance wherever practical.

### 5.3 High-level workflows matter more than low-level purity

The user did not ask for:
- a single UPRN classification
- an experimental band lookup page
- a schema description

The user asked for:
- add council-tax details to a real CSV

If the server does not expose that unit of work, AI agents will approximate it badly.

### 5.4 Progress, resumability, and rate limiting must be first-class

The live GOV.UK path has inherent constraints:
- HTML scrape, not formal bulk API
- rate limiting
- multi-request flow
- variable result counts per postcode

That means this should be a job-oriented workflow with:
- checkpointing
- dedupe
- bounded concurrency
- clear output provenance

### 5.5 Local data maturity must be explicit

Bootstrap ONS caches created false hope.

AI clients need capability state, not just tool existence:
- configured and ready
- configured but partial
- unavailable
- disabled

### 5.6 Tool descriptions must reduce conceptual ambiguity

Current council-tax tool naming is reasonable, but the distinction is still easy to miss:
- `council_tax.query` classifies CT/NDR status from ABP xref
- `council_tax.band_lookup` queries live GOV.UK search results

For agents, those need to be even more explicit in:
- descriptions
- route guidance
- workflow docs
- examples

## 6. Improvement Plan For MCP-Geo

## Phase 1: Fix the immediate interop faults

1. Make `select_toolsets` tolerant of JSON-array strings.
- Target: `server/mcp/tool_search.py`
- Behavior:
  - if a string starts with `[` and parses as a JSON list of strings, accept it
  - still support comma-delimited strings
  - return normalized values in `effectiveFilters`
- Add tests for:
  - `includeToolsets='[\"property_tax\"]'`
  - `excludeToolsets='[\"maps_tiles\",\"apps_ui\"]'`

2. Add a dedicated property-tax intent to `route_query`.
- Target: `tools/os_mcp.py`
- Add:
  - `QueryIntent.PROPERTY_TAX`
  - intent-toolset mapping to `property_tax`
  - guidance and alternative tools for this domain
- Match phrases such as:
  - council tax
  - tax band
  - VOA
  - billing authority reference
  - non-domestic rates
  - business rates
  - AddressBase xref

3. Route property-tax prompts to the right tool by default.
- Examples:
  - status by UPRN -> `council_tax.query`
  - band search by postcode/address -> `council_tax.band_lookup`
  - mixed prompt -> recommend the xref classification first, then optional band lookup

4. Add golden tests directly from this trace.
- Target tests:
  - `tests/test_os_mcp_route_query.py`
  - `tests/test_os_mcp_descriptor.py`
  - new interop-focused cases for toolset parsing

## Phase 2: Expose the user’s real unit of work

5. Add a batch enrichment tool for local datasets.
- Suggested tool shape:
  - `council_tax.enrich_csv`
  - or, if you want the domain broader, `addressbase.enrich_csv`
- Input should cover:
  - input path
  - output path
  - UPRN column name
  - postcode column name
  - fields requested
  - resume or checkpoint policy
  - optional live band enrichment toggle

6. Split local and live enrichment explicitly.
- Stage A:
  - use ABP parquet via DuckDB for CT/NDR status and VOA cross-reference extraction
- Stage B:
  - optional live postcode-level or address-level GOV.UK band enrichment
- Return provenance separately so clients know which fields came from which source

7. Make it job-based, not request-bound.
- For large runs, return:
  - `jobId`
  - status resource URI
  - output resource URI
  - warnings and estimated runtime
- This removes the need for client-managed `screen`, ad hoc scripts, or persistent shells

## Phase 3: Improve capability signaling

8. Add readiness metadata for partial datasets and live integrations.
- Examples:
  - ONS cache state: bootstrap, partial, ready
  - ABP xref configured: yes or no
  - live council-tax lookup enabled: yes or no
  - recent rate-limit state for live lookup

9. Reflect readiness in routing guidance.
- If ONS cache is bootstrap-only, the router should not recommend it as a normal fallback for real geography lookups.
- If live council-tax lookup is disabled or degraded, the router should recommend ABP-only workflows first.

10. Strengthen tool descriptions.
- `council_tax.query` should say plainly:
  - "classifies council-tax and business-rates flags from AddressBase Premium xref"
- `council_tax.band_lookup` should say plainly:
  - "queries the GOV.UK council-tax band search service and may be rate-limited"

## Phase 4: Build AI-client interop protections that apply universally

11. Be liberal in input normalization where intent is clear.
- JSON-string arrays
- comma-delimited lists
- sanitized vs dotted tool names
- mixed `name` or `tool` calling forms where safe

12. Prefer action-oriented errors.
- Instead of only `INVALID_INPUT` or `NOT_FOUND`, include next-step guidance such as:
  - "ABP xref is configured but live band lookup is disabled"
  - "ONS cache is bootstrap-only; run refresh before using `ons_geo.*` for general lookup"

13. Publish client recipes as resources.
- Examples:
  - "Enrich a CSV with council-tax status from ABP"
  - "Run optional live band enrichment safely"
  - "When to use `query` vs `band_lookup`"

14. Add cross-client regression traces.
- Claude
- Codex
- Cursor-style hosts
- generic MCP HTTP callers

15. Add a "discovery-to-callability" integration test.
- If a tool is declared `always_loaded`, verify that the same server/transport path can actually call it in the integration harness

## 7. Improvements That Matter For AI Clients In General

These lessons apply beyond Claude:

1. Distinguish "discoverable", "callable", and "ready".
- AI agents treat these as the same unless told otherwise.

2. Accept mildly malformed but unambiguous inputs.
- Strict typing is good inside the server, but boundary normalization should be forgiving.

3. Offer task-shaped tools, not only primitive tools.
- "enrich this CSV" is a better AI surface than "lookup one page of results for one postcode".

4. Expose resumable jobs and progress resources.
- Agents operate in sessions that may pause, restart, or lose state.

5. Put provenance and caveats in every result.
- AI clients need help distinguishing authoritative local data from scraped live data.

6. Route with domain awareness, not token coincidence.
- UPRN in the prompt does not automatically mean linked IDs.

7. Make degraded local state visible.
- partial caches should fail loudly and informatively

## 8. Recommended Next Implementation Order

If you want the highest leverage sequence:

1. Fix `select_toolsets` normalization.
2. Add property-tax intent and route coverage.
3. Tighten council-tax descriptions and guidance.
4. Add dataset-readiness signaling for ONS and ABP.
5. Add `council_tax.enrich_csv` as a resumable job workflow.
6. Add golden interop tests using prompts lifted from this trace.

That order gives:
- immediate routing improvement
- less wasted client exploration
- a clear path from "tool exists" to "user task completed"

## 9. Where Codex-Spark Fits

Codex-Spark should be used as a speed layer for bounded, repetitive work, not as the final decision-maker for architecture or release-critical edits.

Best uses in `mcp-geo`:
- rapid trace triage and pattern extraction across many client logs
- generating and curating route-query eval cases from real prompts
- drafting repetitive tests for schema and normalization edge cases
- scanning for same-pattern bugs across transport variants
- producing first-pass docs, recipes, and release notes for review
- checking descriptor, manifest, and docs consistency after tool changes

Recommended operating pattern:
- use the main model to define scope, acceptance criteria, and final review
- use Spark for fast, narrow subtasks with explicit ownership
- keep Spark outputs easy to verify: test files, fixture generation, route-case catalogs, docs drafts

Where not to rely on Spark alone:
- security-sensitive redaction decisions
- final interpretation of ambiguous interop failures
- large refactors that touch routing, transport, and tests at once
- release decisions and merge readiness

Concrete ways to use Spark on this workstream:
- generate a corpus of council-tax prompts and expected routed tools
- build a same-pattern matrix for "discovered but not callable" issues
- draft interop tests for JSON-string arrays and sanitized-tool-name fallbacks
- summarize fresh Claude or Codex traces into structured failure categories
- draft the resource recipes for batch council-tax enrichment

## 10. Bottom Line

This trace is useful because it shows the real failure surface, not the theoretical one.

The main problems were not that the council-tax tools were missing. The main problems were:
- the client could not actually call what discovery promised
- the router sent the client into the wrong domain
- the server exposed primitives where the task required a resumable batch workflow

If we fix those three things, `mcp-geo` will work better not just for Claude, but for AI clients generally.
