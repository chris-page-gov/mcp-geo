# AI in Action Hackathon Judging Rubric

Event: AI in Action Hackathon: Exploring AI, MCP and Real Government Use Cases
Date: 20 July 2026
Location: Databricks HQ, Windmill Street, Fitzrovia, London
Prepared: 17 June 2026

## Purpose

This rubric is for judging one-day hackathon outputs that explore how AI and
Model Context Protocol (MCP) could solve real government challenges and improve
day-to-day ways of working. It is designed for mixed teams, including policy,
delivery, product, operations, digital, data and analysis participants. Judges
should reward clear public-sector value, credible safe delivery, and standards-
aware integration, not only software polish.

The MCP references were checked against the live MCP documentation on
17 June 2026. The current live stable MCP specification is `2025-11-25`; the
live draft specification is also included in this rubric because it materially
changes future MCP design assumptions. Stable and draft behaviours should not
be mixed casually: teams should either target stable `2025-11-25`, target the
draft with a clear rationale, or explain how a dual-era design would support
both.

## How To Score

Score each team out of 100. Use the detailed criteria below, then apply the
red-flag and tie-break guidance.

Recommended judging process:

1. Watch the demo or walkthrough.
2. Ask the team to name the real user, operational problem, data involved, and
   what MCP or AI adds that a simpler tool would not.
3. Ask for the main safety, privacy, operational and adoption risks.
4. Score independently, compare scores, then agree a panel score.
5. Record two strengths, one delivery risk, and one next step for proof-of-
   concept development.

Non-technical teams can score highly if they show a strong problem definition,
workflow design, MCP interface contract, governance thinking, and evidence-led
delivery plan. A working prototype should score well only where it also shows
safe and useful behaviour.

## Summary Scorecard

| Area | Weight | What judges are looking for |
| --- | ---: | --- |
| 1. Government problem fit and public value | 15 | A real, specific government problem; clear beneficiaries; measurable public or staff value; proportional AI use. |
| 2. User-centred workflow and adoption | 10 | Understanding of users, current process, accessibility, inclusion, human control, and practical adoption. |
| 3. Prototype quality and evidence | 15 | A convincing demo or design; grounded outputs; tested assumptions; graceful failure and recovery. |
| 4. MCP standards alignment and interoperability | 20 | Correct use or design of MCP primitives, lifecycle, schemas, transport, auth, consent, extension boundaries and draft-spec implications. |
| 5. Data, knowledge and evidence management | 10 | Data provenance, quality, minimisation, traceability, reuse and source-backed outputs. |
| 6. Safety, security, privacy and governance | 15 | Lawful, ethical, secure and privacy-preserving design with risk controls and assurance route. |
| 7. Feasibility, sustainability and delivery path | 10 | Credible PoC path, maintainability, integration, commercial realism and sustainable operation. |
| 8. Collaboration and communication | 5 | Clear story, multidisciplinary contribution, reusable artefacts and honest limitations. |
| Total | 100 |  |

## Scoring Levels

Use this general scale within each weighted area:

| Score band | Interpretation |
| --- | --- |
| 0% | Missing, unsafe, irrelevant, or contradicted by the demo. |
| 25% | Basic intent is visible, but evidence is thin or risks are largely unmanaged. |
| 50% | Plausible and partly evidenced, with important gaps that a PoC would need to resolve. |
| 75% | Strong, well-evidenced, and mostly ready for a focused PoC, with manageable risks. |
| 100% | Excellent, specific, standards-aware, and immediately actionable as a PoC candidate. |

## Detailed Rubric

### 1. Government Problem Fit And Public Value (15)

Award points for:

- A specific operational, policy, analytical or service-delivery problem, not a
  generic "AI assistant" concept.
- Evidence of demand from a real workflow, such as time lost, backlog, error
  rates, handover friction, inconsistent decisions, poor knowledge discovery, or
  high-value unstructured data work.
- Clear beneficiaries: staff, citizens, service teams, analysts, policy teams,
  delivery leads or partner organisations.
- A measurable value hypothesis: time saved, better decision quality, reduced
  avoidable contact, faster analysis, improved knowledge reuse, clearer audit
  trail or improved service consistency.
- Proportionality: the team can explain why AI is appropriate and where a rules-
  based, search, automation or reporting tool would be better.

References: AI Opportunities Action Plan; AI Playbook principles 1, 5 and 6;
Service Standard points 1, 2, 10 and 11; Technology Code of Practice points 1,
9 and 10.

### 2. User-Centred Workflow And Adoption (10)

Award points for:

- A clear current-state workflow and target-state workflow.
- Evidence that the team considered actual day-to-day users, including people
  who are not AI specialists.
- A design that keeps humans in control at the right stages, especially where
  outputs affect rights, entitlements, eligibility, safety, finance or public
  trust.
- Accessibility and inclusion considerations, including plain-language outputs,
  explainable next steps, and support for users with different skills or needs.
- A credible adoption plan: ownership, training, operating model, support,
  feedback channels and escalation route.

References: AI Playbook principles 2, 4, 7 and 9; Service Standard points 1, 4,
5, 6 and 8; Data and AI Ethics Framework principles on accountability, fairness
and societal impact.

### 3. Prototype Quality And Evidence (15)

Award points for:

- A working prototype, clickable mock-up, service blueprint, interface contract
  or repeatable demo that makes the idea concrete.
- Outputs grounded in supplied evidence, source documents, data or tool results,
  rather than unsupported model assertions.
- Clear handling of uncertainty, missing data, low confidence and contradictory
  evidence.
- Basic testing or evaluation: example prompts, expected outcomes, failure
  cases, acceptance criteria, or a small gold-standard comparison.
- Graceful failure: the system refuses, asks for clarification, routes to a
  human, or reports why it cannot answer instead of fabricating.

References: AI Playbook principles 1, 4 and 5; Data and AI Ethics Framework
guidance on transparency, accountability and data quality; MCP tool execution
error guidance.

### 4. MCP Standards Alignment And Interoperability (20)

This category rewards teams for using MCP correctly, or for designing an MCP-
ready integration that could be built after the event. It should not require
full implementation of every MCP feature in a one-day hackathon, but strong
entries should show that they understand the protocol's security and
interoperability model.

| Subcriterion | Points | Evidence judges should look for |
| --- | ---: | --- |
| MCP architecture and boundaries | 2 | Clear host/client/server roles; one server has a focused responsibility; no server assumes it can see the whole conversation or other servers. |
| Primitive choice: tools, resources and prompts | 3 | Actions are modelled as tools, contextual data as resources, and reusable workflows as prompts; each primitive has a clear reason to exist. |
| Tool contract quality | 3 | Tool names are stable and valid; input/output schemas are explicit; validation failures are returned as tool execution errors where useful for model self-correction. |
| Resource and knowledge design | 2 | Resources have useful URIs, MIME types, provenance, annotations or metadata; large lists or corpora use pagination or resource links rather than oversized responses. |
| Stable baseline lifecycle, capabilities and transport | 3 | For `2025-11-25`, the design includes initialization, protocol versioning, capability negotiation, and a realistic transport choice such as stdio for local demos or Streamable HTTP for remote services. |
| Draft-spec readiness and compatibility | 3 | The team identifies draft differences that matter: stateless per-request metadata, `server/discover`, explicit version compatibility, changed Streamable HTTP semantics, cache metadata, MRTR/input requests, extension negotiation, and deprecated features. |
| Authorization, consent and privacy | 3 | Auth is scoped and user-bound; token passthrough is avoided; tool calls and data access require explicit user consent; secrets are never collected through unsafe form flows. |
| Advanced or optional MCP features | 1 | Appropriate, non-overclaimed use of elicitation, progress, cancellation, tasks, MCP Apps or other extensions, with fallback when a client does not support the feature. |

High-scoring MCP designs should:

- Treat MCP as a contract for safe, composable access to systems, tools and
  data, not just as a wrapper around arbitrary scripts.
- Show what the server exposes, what the host controls, and what the user must
  approve.
- Use MCP core features first. MCP Apps, Tasks, draft stateless behaviour,
  Skills over MCP and other extensions can earn credit where they fit the use
  case, but should be labelled as extension or draft-dependent.
- Provide meaningful fallback for clients without extension support, especially
  if using MCP Apps.

References: MCP Specification; MCP Architecture; MCP Lifecycle; MCP
Transports; MCP Authorization; MCP Tools; MCP Resources; MCP Prompts; MCP
Roots; MCP Sampling; MCP Elicitation; MCP Pagination; MCP Progress; MCP
Cancellation; MCP Logging; MCP Tasks; MCP Extensions; MCP Apps; MCP Draft
Specification; MCP Draft Key Changes; MCP Draft Versioning; MCP Draft
Discovery; MCP Draft Streamable HTTP; MCP Draft Deprecated Features.

#### Draft Spec Checklist

Use this checklist when a team claims draft-spec alignment, future MCP
readiness, or a dual-era design.

| Draft area | Judge check |
| --- | --- |
| Protocol era | Does the team state whether it is targeting stable `2025-11-25`, draft `2026-07-28` semantics, or both? |
| Stateless requests | If draft-targeted, does every request carry protocol version, client identity and capabilities in request metadata rather than relying on a session handshake? |
| Discovery | Does the design use or account for `server/discover` so clients can learn supported versions, capabilities and server identity up front? |
| Explicit state | If cross-call state is needed, is it represented with explicit server-minted handles or normal tool arguments rather than hidden protocol sessions? |
| Streamable HTTP | Does the remote transport model use POST to a single MCP endpoint, request-scoped SSE response streams, no GET stream endpoint and no protocol-level session header? |
| MRTR/input requests | If the server needs more information from the user or host, does the design account for input requests/input responses rather than assuming server-initiated JSON-RPC requests? |
| Caching | Do list/read responses that may be cached include freshness and cache-scope thinking, such as draft `ttlMs` and `cacheScope` semantics? |
| Extensions | Are Tasks, MCP Apps, Skills over MCP and other optional capabilities negotiated through extensions with fallback where unsupported? |
| Deprecations | Does the team avoid adopting newly deprecated features in new draft-targeted work, especially Roots, Sampling, Logging, HTTP+SSE and dynamic client registration where the draft marks them for migration? |
| Dual-era compatibility | If both stable and draft are supported, is the fallback explicit rather than mixing `initialize`-based stable assumptions with per-request draft assumptions? |

### 5. Data, Knowledge And Evidence Management (10)

Award points for:

- Clear identification of data sources, ownership, sensitivity and intended
  use.
- Provenance for source documents, records, APIs, analysis outputs and model-
  generated summaries.
- Data quality thinking: completeness, consistency, timeliness, validity,
  accuracy, representativeness and fitness for purpose.
- Data minimisation: the system uses the least data needed and avoids pulling
  sensitive material into prompts or logs.
- Reuse potential across teams or departments through documented schemas,
  resources, metadata, prompts or shared service patterns.

References: Government Data Quality Framework; Data and AI Ethics Framework
guidance on transparency, data protection, fairness and provenance; MCP
Resources and Pagination.

### 6. Safety, Security, Privacy And Governance (15)

Award points for:

- A realistic threat model for AI and MCP risks, including prompt injection,
  tool misuse, data leakage, unsafe automation, supply-chain risk, malicious
  local server configuration, SSRF and session hijacking where relevant.
- Clear user consent and control for data access, tool invocation and any
  server-initiated sampling or elicitation.
- Privacy by design: no unnecessary personal data, clear lawful basis questions,
  DPIA/EIA triggers identified, privacy notice implications considered.
- Human oversight and appeal routes where outputs influence decisions or
  service outcomes.
- Auditability: logs, source traces, model/tool call records, redaction of
  secrets, and a route to ATRS where the tool supports or influences decisions.
- Secure implementation choices: scoped auth, no token passthrough, secure
  storage, sandboxing or least-privilege execution for local tools, and safe
  handling of credentials.

References: AI Playbook principles 2, 3, 4 and 10; Data and AI Ethics
Framework principles; ATRS; MCP security and trust principles; MCP
Authorization; MCP Security Best Practices; NCSC Guidelines for Secure AI
System Development.

### 7. Feasibility, Sustainability And Delivery Path (10)

Award points for:

- A credible PoC plan that Databricks or another delivery team could pick up:
  scope, users, data access, integration path, dependencies, risks and success
  measures.
- Realistic technical choices, with clear make/buy/reuse decisions.
- Integration with existing government systems, governance, support routes and
  operating processes.
- Maintainability: clear owner, update path, model/data refresh approach,
  monitoring, incident response and exit plan.
- Commercial and procurement awareness, especially where third-party AI, data
  platforms or MCP servers are involved.
- Environmental and cost proportionality.

References: AI Playbook principles 5, 6, 8 and 10; Technology Code of Practice;
Service Standard points 11, 13 and 14; NCSC secure AI lifecycle guidance.

### 8. Collaboration And Communication (5)

Award points for:

- A concise, compelling explanation of the problem, user, solution, risk and
  next step.
- Evidence that different disciplines shaped the design.
- Honest limitations and assumptions.
- Reusable artefacts: workflow diagram, prompt pack, tool schema, data card,
  risk log, evaluation examples, or PoC brief.
- Clear answers to judge questions without overclaiming.

References: AI Playbook principle 7; Service Standard points 6 and 8; MCP
architecture principles on composability and progressive feature adoption.

## Red Flags And Hard Stops

Judges should heavily penalise, and may disqualify, entries that show any of
the following:

- Use of live personal, confidential, classified, commercial or otherwise
  sensitive data without permission and controls.
- Secrets, API keys, credentials, tokens or private data shown in prompts, logs,
  screenshots, repositories or demos.
- AI outputs presented as authoritative decisions without human oversight,
  confidence handling, evidence or appeal routes.
- A proposal to automate high-impact decisions affecting rights, benefits,
  eligibility, enforcement, finance, safeguarding or liberty without explicit
  governance, testing and human control.
- Unsafe MCP design, such as token passthrough, arbitrary local command
  execution without consent, unscoped access to files, untrusted tool
  annotations treated as fact, or form-mode elicitation for passwords, API keys,
  access tokens or payment credentials.
- A prototype that fabricates sources, hides uncertainty, or cannot explain
  where information came from.
- A solution that is mostly a vendor pitch with no real government workflow,
  user need, adoption route or public value.

## Tie-Breakers

If scores are close, prefer the team that:

1. Addresses the clearest and most valuable government problem.
2. Has the safest and most credible path to a Databricks-developed proof of
   concept.
3. Shows the best cross-government reuse potential.
4. Demonstrates the most mature MCP contract or integration boundary.
5. Is most honest about limitations and most specific about next validation.

## Suggested Judge Questions

- What real user or team has this problem today, and how do they solve it now?
- What would make this worth developing into a proof of concept?
- What does AI do here that search, rules, workflow automation or reporting
  would not do better?
- What systems, documents, tools or data would the agent need access to?
- If this uses MCP, what are the tools, resources and prompts? What must the
  user approve?
- Which MCP version or era is this designed for: stable `2025-11-25`, the live
  draft, or both? What changes if the draft becomes the target?
- What data must never leave the source system or appear in the model context?
- What is the highest-risk failure mode, and how would the service detect or
  recover from it?
- What would you measure after 4 weeks to decide whether to continue?

## PoC Handoff Template

For the winning team, capture:

| Field | Notes |
| --- | --- |
| Problem statement | One paragraph, naming the user and operational pain. |
| Proposed solution | One paragraph, including AI and MCP role. |
| Primary users | Roles, teams, skill levels and access needs. |
| Data and systems | Sources, sensitivity, access route, quality concerns. |
| MCP contract | Candidate tools, resources, prompts, auth, transport and extensions. |
| Safety and governance | DPIA/EIA/ATRS triggers, human control, audit, red-team needs. |
| Success measures | Time, quality, adoption, cost, trust or service metrics. |
| Four-week PoC scope | What to build, what to fake, what to test, what to defer. |
| Open questions | Dependencies, blockers, decisions and owners. |

## Reference Notes

The references below are official or primary sources unless marked as local
repo context. They were checked on 17 June 2026.

- MCP stable baseline: the live MCP documentation identifies `2025-11-25` as
  the latest stable specification and describes MCP as an open protocol for
  integrating LLM applications with external data sources and tools.
- MCP draft and extensions: the live draft introduces stateless per-request
  metadata, `server/discover`, changed Streamable HTTP behaviour, explicit
  cache metadata, MRTR/input requests, extension negotiation and a deprecated-
  features registry. These are included in the MCP score as future-proofing
  evidence, but stable `2025-11-25` remains a valid target for a hackathon
  prototype if stated clearly.
- Local repo context: `docs/vendor/mcp/README.md` records the local MCP vendor
  snapshot and states that runtime defaults remain on `2025-11-25`, with
  2026 release-candidate behaviour opt-in.

## References

- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Draft Specification](https://modelcontextprotocol.io/specification/draft)
- [MCP Draft Key Changes](https://modelcontextprotocol.io/specification/draft/changelog)
- [MCP Draft Versioning and Compatibility](https://modelcontextprotocol.io/specification/draft/basic/versioning)
- [MCP Draft Discovery](https://modelcontextprotocol.io/specification/draft/server/discover)
- [MCP Draft Streamable HTTP](https://modelcontextprotocol.io/specification/draft/basic/transports/streamable-http)
- [MCP Draft Deprecated Features](https://modelcontextprotocol.io/specification/draft/deprecated)
- [MCP Architecture](https://modelcontextprotocol.io/specification/2025-11-25/architecture)
- [MCP Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)
- [MCP Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [MCP Resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources)
- [MCP Prompts](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts)
- [MCP Roots](https://modelcontextprotocol.io/specification/2025-11-25/client/roots)
- [MCP Sampling](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling)
- [MCP Elicitation](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation)
- [MCP Pagination](https://modelcontextprotocol.io/specification/2025-11-25/server/utilities/pagination)
- [MCP Progress](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/progress)
- [MCP Cancellation](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation)
- [MCP Logging](https://modelcontextprotocol.io/specification/2025-11-25/server/utilities/logging)
- [MCP Tasks](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks)
- [MCP Extensions Overview](https://modelcontextprotocol.io/extensions/overview)
- [MCP Apps](https://modelcontextprotocol.io/extensions/apps/overview)
- [MCP Security Best Practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
- [AI Playbook for the UK Government](https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government)
- [Artificial Intelligence Playbook for the UK Government - HTML](https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government/artificial-intelligence-playbook-for-the-uk-government-html)
- [AI Opportunities Action Plan](https://www.gov.uk/government/publications/ai-opportunities-action-plan)
- [Data and AI Ethics Framework](https://www.gov.uk/government/publications/data-ethics-framework)
- [Data and AI Ethics Framework - HTML](https://www.gov.uk/government/publications/data-ethics-framework/data-and-ai-ethics-framework)
- [Algorithmic Transparency Recording Standard Hub](https://www.gov.uk/government/collections/algorithmic-transparency-recording-standard-hub)
- [Service Standard](https://www.gov.uk/service-manual/service-standard)
- [Technology Code of Practice](https://www.gov.uk/guidance/the-technology-code-of-practice)
- [Government Data Quality Framework](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework)
- [NCSC Guidelines for Secure AI System Development](https://www.ncsc.gov.uk/collection/guidelines-secure-ai-system-development)
- Local repo context: `docs/vendor/mcp/README.md`
