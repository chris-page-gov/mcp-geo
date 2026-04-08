---
aliases: [MCP, Model Context Protocol, semantic sheath, LandIS MCP]
tags: [mcp, architecture, ai, semantic, landis]
---

# MCP Overview

> [!abstract] Core Premise
> The **Model Context Protocol (MCP)** provides the most effective, safest, and highest-impact architecture to unlock Cranfield University's definitive national soils data for AI agents and policy workflows.

## What is MCP?

MCP is an open standard for exposing **tools**, **resources**, and **prompts** via a JSON-RPC protocol between hosts (e.g. Claude, ChatGPT), clients, and servers. It is supported by major AI platforms and is explicitly designed for composable integrations — enabling AI systems to call real-world data APIs as part of reasoning chains.

**Specification:** [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25)

## The Three-Layer Design

The LandIS MCP server acts as a **thin, deterministic semantic sheath** between the raw LandIS database and end-user applications:

```
Raw LandIS Database
        │
        ▼
┌─────────────────────────────────────────────────────┐
│              The MCP Layer                          │
│                                                     │
│  1. ACCESS      2. SEMANTIC      3. ASSURANCE       │
│  ─────────      ─────────        ─────────────      │
│  Natural        Translate raw    Auto-bind ISO       │
│  language →     codes to         metadata +          │
│  coordinates/   plain-English    version IDs +       │
│  polygons        explanations    "not for site        │
│                                  assessment"         │
└─────────────────────────────────────────────────────┘
        │
        ▼
End-User Applications
(AI agents · Defra dashboards · Utility planners)
```

### Layer 1 — Access
Translates natural language spatial queries into exact coordinate/polygon retrievals, shielding users from file formats and join complexity. Users say "what are the soils near SK432891?" — the MCP tool handles OSGB conversion, polygon lookup, and MUSID retrieval.

### Layer 2 — Semantic
Translates raw integer codes into plain-English explanations of functional constraints. "Wetness Class 4" becomes "This soil is poorly drained and likely to be waterlogged for significant periods in winter and spring, constraining construction windows and requiring drainage assessment."

### Layer 3 — Assurance
Automatically binds ISO metadata, Cranfield dataset versioning, and mandatory "not suitable for detailed site assessment" caveats to every single output. No response can be returned without provenance.

## Why MCP is a Strong Fit for LandIS

### Strengths (evidenced + inference)

**Deterministic query types** — LandIS has many high-value, well-defined queries (point lookup, polygon summary, class decoding, route intersection) that map cleanly to MCP tools.

**Rich static knowledge assets** — Classification documents, schema explanations, join guides, and glossaries map cleanly to MCP resources and prompts.

**Composability** — MCP's host/client/server model enables LandIS to be combined with other datasets (OS addresses, flood zones, network assets) without bespoke connector work.

**GIS barrier removal** — Non-GIS users can invoke spatial tools through natural language while still getting structured, auditable outputs.

### Caution Factors

> [!warning] Misinterpretation Risk
> Soil map generalisation and within-polygon variability create a strong risk of site-level overconfidence. Every MCP tool output **must** embed scale and limitation warnings. The "not suitable for detailed site assessment" caveat is mandatory, not optional.

> [!warning] Licensing Transition Risk
> The rapid open access transition creates ambiguity. The assurance layer must attach licence references and dataset versions to every response, and must not encourage reuse that may not be permitted for specific datasets.

## MCP vs Alternatives

| Option | Strengths | Weaknesses |
|---|---|---|
| **MCP** | Composable, semantic, rapid value discovery, AI-native | Not a full API; may need caching |
| OGC API / REST | High-volume, enterprise-grade, standards-compliant | Slower to build; no semantic layer |
| WMS/WFS | GIS-native, already evidenced | Poor for AI/automation; image-not-data |
| Download-only | Good for research | High barrier; not composable |
| Viewer/portal | Good for exploration | Poor for integration |

**Conclusion:** MCP is the right **first move** — but it should be paired with a roadmap to formal OGC API productisation for high-volume use cases. See [[Implementation Roadmap]].

## MCP Component Types

| Component | LandIS Use |
|---|---|
| **Tools** | Spatial queries (point, area, route) — deterministic, structured JSON outputs |
| **Resources** | Schema docs, glossaries, licence text, classification guides |
| **Prompts** | Reusable prompt templates for personas (planner, farmer, utility analyst) |

See [[Primitive Tools]], [[Derived Semantic Tools]], [[Resources and Prompts]].

## Strategic Value

> [!tip] Value Discovery Harness
> A focused MCP server acts as a "value discovery harness" during the open access transition by:
> - Rapidly surfacing which questions users actually ask
> - Enabling cross-dataset composition experiments
> - Informing subsequent formal API and portal design
>
> This is consistent with the policy intent to widen access and unlock innovation.

---
*← [[00 - Home|Home]]  |  See also: [[Primitive Tools]], [[Derived Semantic Tools]], [[Implementation Roadmap]], [[LandIS MCP Strategy Slides]]*
