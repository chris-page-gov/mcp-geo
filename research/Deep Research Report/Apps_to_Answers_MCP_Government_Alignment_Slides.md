---
marp: true
paginate: true
theme: default
title: From Apps to Answers - MCP capabilities for UK public sector delivery
---

# From Apps to Answers
## MCP capabilities for public-sector data to AI workflows

- Audience: public-sector data, service, and assurance leaders
- Alignment: UK government AI-ready dataset guidance (19 January 2026)
- Supporting source: research brief in this repo

---

## Evidence base reviewed

- Source A:
  `research/Deep Research Report/Research Apps to Answers_ Connecting Public Sector Data to AI with MCP.md`
- Source B:
  [Guidelines and best practices for making government datasets ready for AI](https://www.gov.uk/government/publications/making-government-datasets-ready-for-ai/guidelines-and-best-practices-for-making-government-datasets-ready-for-ai)
- Scope: show how MCP enables the transition from app-centric service delivery to
  answer-centric service delivery, with governance controls built in.

---

## Why this matters now

- Government guidance states AI outcomes are constrained by data quality,
  metadata, interoperability, and governance.
- Siloed datasets and inconsistent standards reduce trust and reuse.
- Answer-centric services increase speed, but also increase risk if controls are
  weak.
- [Inference] The practical constraint is no longer model capability alone; it
  is integration quality and assurance maturity.

---

## What the Government report says about MCP

- In the access layer, MCP can support "agentic, single record access" alongside
  GraphQL.
- MCP is positioned as an open standard interface for machine-readable capability
  sharing.
- AI systems act as MCP clients to connect securely to tools and datasets.
- MCP + agentic AI is presented as a route to automate complex pipeline tasks.
- International example: the report says the World Bank is "leading the charge"
  and includes MCP implementation.

---

## Transition model: Apps -> Answers

| Apps model | Answers model |
| --- | --- |
| User navigates many UIs | User asks one grounded question |
| Data retrieval is manual | Data retrieval is orchestrated |
| Evidence is fragmented | Evidence is compiled with provenance |
| Governance is channel-specific | Governance is enforced in one middle layer |
| Slow iteration | Faster decision cycles |

- [Inference] MCP is a key transport and capability contract in the answers
  model, not the full governance solution by itself.

---

## MCP capabilities that unlock the transition

- Capability discovery: consistent tool and resource listing.
- Safe invocation: structured inputs and outputs for tool calls.
- Resource access: large outputs via resource handles instead of token-heavy
  inline blobs.
- Multi-system composition: one client can coordinate multiple domain servers.
- Interop transport options: stdio and streamable HTTP patterns reduce
  integration friction across host environments.

---

## The governed middle layer (required for trust)

- Discovery and catalog quality: owners, schemas, freshness, and SLOs.
- Semantic alignment: units, identifiers, boundaries, and definitions.
- Policy enforcement: least privilege access control outside prompt text.
- Provenance and auditability: reproducible evidence chain per answer.
- Operations: latency budgets, retries, degradation modes, and monitoring.

- [Inference] Without these controls, MCP can accelerate unsafe automation just
  as quickly as safe automation.

---

## Practical map: Government guidance -> delivery capability

| Government direction | Delivery implementation pattern |
| --- | --- |
| Access-layer interoperability | MCP server catalog + governed tool contracts |
| Agentic single-record access | Scoped tool design with explicit schemas |
| Security and efficiency | AuthZ boundary + validation + rate limits |
| Automation for public value | Repeatable workflows with monitored outputs |
| Data quality improvement | Semantic resources + provenance-by-default |

---

## Case example: peatland survey answers workflow

- User asks for restoration evidence in a target area.
- System must geocode, select authoritative datasets, query correctly, and
  report caveats.
- Failure classes from the research source:
  - discovery failure,
  - semantic mismatch,
  - boundary/CRS mismatch,
  - operational failure,
  - provenance gaps.
- MCP contribution: standard capability exposure and retrieval orchestration.
- Non-MCP essentials: semantic contracts, policy controls, and auditable
  provenance.

---

## 30-day thin-slice pilot (recommended)

- Use case: read-only question set over one authoritative dataset domain.
- Build:
  - one MCP server exposing discovery, retrieval, and metadata resources,
  - one policy boundary with role-aware controls,
  - one provenance pipeline for every answer.
- Demo both success and degraded-path behavior (no fabricated outputs).
- Exit criteria:
  - accuracy against a gold suite,
  - provenance completeness,
  - p95 latency and cost budgets met.

---

## Success metrics for Apps -> Answers

- Answer accuracy against verified reference answers.
- Provenance completeness rate per response.
- Safe degradation rate when dependencies fail.
- Median and p95 time-to-answer.
- Cost per answer and tool call volume stability.
- User trust indicators (defensibility, reproducibility, escalation rate).

---

## Decision points for leadership

1. Which 1-2 bounded use cases should move first?
2. What minimum control gate is required before live rollout?
3. Who owns the capability catalog, semantics, and assurance sign-off?
4. What evidence threshold is required to progress from Open -> Controlled
   stages?
5. How will incidents, drift, and model/tool changes be reviewed?

---

## References

- Source A (repo research brief):
  `research/Deep Research Report/Research Apps to Answers_ Connecting Public Sector Data to AI with MCP.md`
- Source B (UK guidance):
  [Making government datasets ready for AI](https://www.gov.uk/government/publications/making-government-datasets-ready-for-ai/guidelines-and-best-practices-for-making-government-datasets-ready-for-ai)

