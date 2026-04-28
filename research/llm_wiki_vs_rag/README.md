# Research Project: LLM Wiki versus RAG

Date opened: 2026-04-23
Status: Proposed
Owner: TBD

## Purpose

Investigate whether Karpathy-style **LLM Wiki** knowledge bases are more
effective than retrieval-augmented generation (RAG) for accumulating,
maintaining, and using project knowledge, and identify where enhanced RAG
strategies close the gap or combine well with a maintained wiki.

The working terminology should be precise:

- **LLM Wiki** is the term used in Andrej Karpathy's original idea file: a
  persistent, interlinked markdown wiki maintained by an LLM agent.
- **WikiLLM**, **LLMWiki**, and similar names appear to be product or project
  names inspired by the same pattern, not necessarily the canonical name.
- The research should treat the idea as a family of approaches: LLM-maintained
  wiki, compiled knowledge base, structured memory, agentic wiki, and
  wiki-backed RAG.

## Background

Karpathy's original proposal contrasts ordinary RAG with a compiled knowledge
artifact. In baseline RAG, the system retrieves raw chunks at query time and
re-synthesizes the answer for each question. In the LLM Wiki pattern, raw
sources remain immutable, an LLM-owned markdown wiki stores summaries,
entities, concepts, comparisons, contradictions, and syntheses, and a schema
file such as `AGENTS.md` or `CLAUDE.md` instructs the agent how to ingest,
query, and lint the wiki. The central claim is that knowledge should compound:
the system should not rediscover the same synthesis from scratch on every
query.

Current implementations and adjacent work include:

- Karpathy's original `llm-wiki` idea file:
  <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- LLM Wiki v2 / agent memory extensions:
  <https://gist.github.com/changkun/a9b5253f44f923fabe3cf500ab5819da>
- WikiLLM proof-of-concept:
  <https://www.wikillm.wiki/>
- LLM Wiki product pages and examples:
  <https://llm-wiki.app/>
- `llm-wiki-mcp`, an MCP server and skills package for local markdown wikis:
  <https://pypi.org/project/llm-wiki-mcp/>
- `obsidian-llm-wiki`, a local-first Obsidian-oriented implementation:
  <https://pypi.org/project/obsidian-llm-wiki/>
- OpenKB, a structured wiki-style knowledge-base implementation:
  <https://github.com/VectifyAI/OpenKB>
- RAG survey work:
  <https://arxiv.org/abs/2405.06211>
- Meta Knowledge for RAG:
  <https://arxiv.org/abs/2408.09017>
- GraphRAG:
  <https://www.microsoft.com/en-us/research/project/graphrag/>
- RAPTOR hierarchical retrieval:
  <https://arxiv.org/abs/2401.18059>
- Self-RAG:
  <https://arxiv.org/abs/2310.11511>
- LLM2KB:
  <https://arxiv.org/abs/2308.13207>

## Research Questions

1. For project and policy knowledge work, when does an LLM-maintained wiki
   outperform baseline RAG on factuality, synthesis, reuse, explainability, and
   maintenance?
2. Which parts of the LLM Wiki pattern are genuinely new, and which overlap
   with older knowledge-base construction, graph RAG, hierarchical retrieval,
   synthetic metadata, and summarization pipelines?
3. What failure modes appear in LLM Wiki systems: lossy summaries,
   hallucinated links, silent contradiction propagation, stale pages, source
   drift, over-confident synthesis, and schema rot?
4. What enhanced RAG strategy should be used as a strong comparator rather
   than a weak baseline?
5. Is the best architecture a hybrid: immutable raw-source RAG, compiled wiki
   pages, graph/index metadata, and citation-preserving answer generation?
6. What governance model is needed for public-sector use: provenance,
   reviewability, audit trail, retention, redaction, and human approval points?

## Experimental Design

Evaluate four conditions against the same source corpus:

1. **Baseline RAG**
   - Chunk raw documents.
   - Embed and retrieve top-k chunks.
   - Generate answers with source citations.

2. **Enhanced RAG**
   - Hybrid lexical/vector search.
   - Query rewriting and decomposition.
   - Metadata filters and source-type weighting.
   - Reranking.
   - Hierarchical summaries or RAPTOR-style tree retrieval.
   - GraphRAG-style entity/relation/community summaries where useful.
   - Synthetic QA and meta-knowledge summaries for retrieval routing.
   - Answer verification against retrieved evidence.

3. **LLM Wiki**
   - Raw sources are immutable.
   - LLM compiles sources into wiki pages: source summaries, entities,
     concepts, comparisons, timeline, contradiction log, and overview.
   - Queries read the index first, then relevant wiki pages, and optionally
     file useful answers back into the wiki.
   - Lint pass checks broken links, orphan pages, stale claims, contradictions,
     and uncited claims.

4. **Hybrid Wiki + RAG**
   - RAG indexes both raw sources and compiled wiki pages.
   - Wiki pages provide stable synthesis and routing metadata.
   - Raw sources remain the final citation and verification layer.
   - Retrieval can route through wiki pages, graph summaries, and raw chunks.
   - Contradiction flags and freshness metadata influence retrieval/ranking.

Recommended corpora:

- MCP-Geo repository docs, release notes, and research packs.
- A controlled external corpus with known contradictions and dated facts.
- A meeting/transcript corpus where team knowledge changes over time.
- A policy or technical documentation corpus requiring multi-hop synthesis.

## Metrics

- **Answer quality:** correctness, completeness, specificity, and synthesis
  depth.
- **Grounding:** citation precision, citation recall, and claim-to-source
  traceability.
- **Reuse:** whether previously synthesized knowledge is reused rather than
  re-derived.
- **Maintenance:** time/cost per ingest, number of touched pages, review
  burden, and merge conflict rate.
- **Freshness:** ability to revise stale claims and preserve historical claims
  with dates.
- **Contradiction handling:** detection rate, false-positive rate, and quality
  of resolution notes.
- **Operational cost:** tokens, latency, storage, tool calls, and developer
  complexity.
- **Governance:** audit trail quality, human approval gates, privacy posture,
  and explainability.

## Strategy for Enhancing RAG

Do not compare LLM Wiki only to naive vector RAG. A serious comparator should
include the strongest practical RAG improvements:

- Combine lexical search, vector search, structured metadata, and reranking.
- Generate per-document metadata, source summaries, synthetic questions, and
  cluster-level meta-knowledge summaries.
- Use hierarchical retrieval for long documents and cross-document questions.
- Build graph summaries for entity-heavy corpora and global questions.
- Add retrieval self-critique: detect weak retrieval, reformulate the query,
  broaden the search, or ask for missing context.
- Index compiled wiki pages as first-class retrievable artifacts, but require
  answer claims to trace back to immutable raw sources where practical.
- Maintain a contradiction registry and freshness metadata independent of the
  answer-generation prompt.

The key hypothesis is not "wiki replaces RAG." The stronger hypothesis is that
RAG should retrieve over multiple knowledge layers: raw evidence, curated
summaries, graph/community abstractions, wiki syntheses, and audit logs.

## Deliverables

1. Literature and implementation survey covering Karpathy's original proposal,
   derivative tools, knowledge-base construction, and enhanced RAG research.
2. Taxonomy of architectures: baseline RAG, enhanced RAG, LLM Wiki, knowledge
   graph memory, and hybrid wiki-backed RAG.
3. Evaluation harness and reproducible corpus.
4. Side-by-side results for answer quality, provenance, freshness,
   contradiction handling, and operating cost.
5. Recommendation for MCP-Geo: whether to keep improving the existing
   Obsidian/research-pack workflow, add an LLM Wiki maintenance layer, or build
   a hybrid wiki-backed retrieval service.

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

## Open Decisions

- Should MCP-Geo's existing Obsidian knowledge base remain a generated
  descriptive catalog, or should it gain an LLM-maintained synthesis layer?
- Should source-of-truth stay as repo files with generated wiki notes, or
  should the wiki itself become a first-class source artifact?
- Should we prototype with an existing implementation such as `llm-wiki-mcp`,
  adapt the current `scripts/build_obsidian_kb.py`, or build a minimal local
  harness?
- What human review gates are required before an LLM-authored wiki page can be
  treated as evidence in public-sector decision support?
