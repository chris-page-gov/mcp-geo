---
title: "Research Project - LLM Wiki versus RAG"
kb_kind: "research_project"
source_paths:
  - "research/llm_wiki_vs_rag/README.md"
last_validated_at: "2026-04-23"
---
# Research Project - LLM Wiki versus RAG

This note defines a research project to test whether Karpathy-style **LLM
Wiki** knowledge bases are more effective than RAG, and whether the practical
answer is an enhanced RAG or hybrid wiki-backed RAG strategy.

Durable project note: `research/llm_wiki_vs_rag/README.md`

## Terminology

- **LLM Wiki** is the name used in Karpathy's original idea file for a
  persistent, interlinked markdown wiki maintained by an LLM agent.
- **WikiLLM**, **LLMWiki**, and related names currently appear as derivative
  products, demos, or packages inspired by the same pattern.
- The research should cover the whole family: LLM-maintained wiki, compiled
  knowledge base, structured memory, AI-maintained Obsidian, and wiki-backed
  RAG.

## Core Question

Does compiling raw sources into a maintained wiki produce better project
knowledge than retrieving chunks at query time, once RAG is given a fair
enhanced baseline?

## Research Questions

1. When does LLM Wiki outperform baseline RAG on synthesis, reuse, grounding,
   freshness, and contradiction handling?
2. Which claims overlap with prior knowledge-base construction, GraphRAG,
   RAPTOR, meta-knowledge retrieval, agent memory, and structured summarization?
3. Which enhanced RAG techniques solve the same problems without making a wiki
   the primary artifact?
4. Is the best architecture a hybrid: immutable raw-source RAG plus compiled
   wiki pages, graph summaries, freshness metadata, and contradiction logs?
5. What governance controls are needed before wiki-authored synthesis is
   trusted in public-sector decision support?

## Evaluation Conditions

1. **Baseline RAG**: chunk, embed, retrieve top-k raw source fragments, answer
   with citations.
2. **Enhanced RAG**: hybrid lexical/vector retrieval, metadata filters,
   reranking, query rewriting, hierarchical summaries, GraphRAG-style entity
   and community summaries, synthetic QA, meta-knowledge summaries, and answer
   verification.
3. **LLM Wiki**: immutable raw sources, LLM-owned markdown pages, index, log,
   source summaries, entity/concept pages, comparisons, overview, contradiction
   registry, and lint pass.
4. **Hybrid Wiki + RAG**: retrieve over raw evidence, curated summaries, graph
   abstractions, wiki syntheses, and audit logs; use raw sources for final
   claim verification where practical.

## Deep Research Prompt

```text
You are conducting a deep research study for MCP-Geo on whether Karpathy-style
LLM Wiki knowledge bases are more effective than RAG, and whether the right
strategy is actually enhanced RAG or a hybrid LLM Wiki + RAG architecture.

Scope and terminology:
- Start from Andrej Karpathy's original "LLM Wiki" idea file/post. Verify the
  original terminology, architecture, operations, and claimed advantages. Do
  not rely only on SEO summaries or product pages.
- Treat "LLM Wiki" as the canonical pattern name unless evidence shows
  otherwise. Also search for "WikiLLM", "LLMWiki", "LLM-maintained wiki",
  "compiled knowledge base", "agentic wiki", "LLM knowledge base", "structured
  memory", "wiki-backed RAG", and "AI-maintained Obsidian".
- Distinguish idea, implementation, product, academic analogue, and marketing
  claim.

Research tasks:
1. Summarize Karpathy's original proposal:
   - architecture: immutable raw sources, LLM-owned markdown wiki, schema or
     agent instruction file;
   - operations: ingest, query, lint/maintenance;
   - special files: index, log, overview, source summaries, entity/concept
     pages, comparisons;
   - intended domains: personal research, team knowledge, books, business
     knowledge, due diligence, and other accumulating knowledge tasks;
   - claims against RAG: no accumulation, repeated re-synthesis, weak
     contradiction handling, and lack of persistent synthesis.

2. Survey what has already been done:
   - open-source implementations, MCP servers, Obsidian integrations, hosted
     apps, gists, demos, and commercial tools;
   - implementations that add lifecycle, contradiction detection, git
     versioning, local-first execution, graph traversal, or memory management;
   - academic and pre-Karpathy adjacent work on LLM-generated knowledge bases,
     knowledge graph construction, structured memory, summarization indexes,
     and agent memory.

3. Survey enhanced RAG as a serious comparator:
   - GraphRAG, RAPTOR/hierarchical retrieval, meta-knowledge summaries,
     synthetic QA, query rewriting/decomposition, hybrid lexical/vector search,
     reranking, Self-RAG, Corrective RAG, adaptive retrieval, and
     citation/verification layers;
   - identify which enhanced RAG techniques solve the same problems that
     LLM Wiki claims to solve;
   - identify which problems remain hard for RAG even after enhancement.

4. Design an evaluation:
   - compare baseline RAG, enhanced RAG, LLM Wiki, and hybrid Wiki + RAG;
   - include multi-hop synthesis, contradiction, freshness, source citation,
     long-document, meeting/transcript, and project-memory tasks;
   - define metrics for factuality, citation precision/recall, synthesis
     quality, maintenance cost, latency, token cost, auditability,
     contradiction handling, and human review burden;
   - recommend corpora, including a controlled synthetic contradiction corpus
     and a real project corpus such as MCP-Geo docs/research/release notes.

5. Produce a recommendation:
   - when to use LLM Wiki;
   - when enhanced RAG is enough;
   - when to combine them;
   - what architecture MCP-Geo should prototype first;
   - what governance controls are mandatory for public-sector knowledge work.

Evidence requirements:
- Prioritize primary sources: Karpathy's original gist/post, GitHub repos,
  package pages, arXiv/OpenReview/ACL/ACM papers, Microsoft Research GraphRAG
  material, and implementation docs.
- Include recent community implementation evidence, but label it separately
  from peer-reviewed or primary technical sources.
- Provide a dated bibliography with URLs, accessed date, and short notes on why
  each source matters.
- Quote sparingly; paraphrase claims and cite sources.

Output format:
- Executive summary.
- Terminology and source-of-truth section.
- Prior-work map.
- Architecture comparison table.
- Enhanced RAG strategy section.
- Evaluation design.
- Risks and failure modes.
- Recommendation for MCP-Geo.
- Bibliography.
```

## Starting Sources

- [Karpathy `llm-wiki` gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [LLM Wiki v2 gist](https://gist.github.com/changkun/a9b5253f44f923fabe3cf500ab5819da)
- [WikiLLM proof-of-concept](https://www.wikillm.wiki/)
- [LLM Wiki app](https://llm-wiki.app/)
- [`llm-wiki-mcp` package](https://pypi.org/project/llm-wiki-mcp/)
- [`obsidian-llm-wiki` package](https://pypi.org/project/obsidian-llm-wiki/)
- [OpenKB](https://github.com/VectifyAI/OpenKB)
- [RAG survey](https://arxiv.org/abs/2405.06211)
- [Meta Knowledge for RAG](https://arxiv.org/abs/2408.09017)
- [Microsoft GraphRAG](https://www.microsoft.com/en-us/research/project/graphrag/)
- [RAPTOR](https://arxiv.org/abs/2401.18059)
- [Self-RAG](https://arxiv.org/abs/2310.11511)
- [LLM2KB](https://arxiv.org/abs/2308.13207)

## Open Decisions

- Should MCP-Geo's generated Obsidian KB remain descriptive only, or gain an
  LLM-maintained synthesis layer?
- Should source-of-truth stay in repo files, with the wiki as generated view,
  or should selected wiki pages become first-class source artifacts?
- Should a prototype adapt `scripts/build_obsidian_kb.py`, use
  `llm-wiki-mcp`, or implement a minimal MCP-Geo-specific harness?
