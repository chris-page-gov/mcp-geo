
## annotated-bibliography.md

### Annotated bibliography (prioritised, UK-public-sector relevant)

1. **Model Context Protocol Specification (2025-11-25)** – Defines MCP as an open protocol for integrating LLM applications with external tools and data sources; useful for grounding what MCP is (without sales language). ([Model Context Protocol][1])

2. **Shannon (1948), “A Mathematical Theory of Communication”** – Foundational information theory; supports the “information ≠ meaning” distinction and why we need a semantic middle layer beyond Shannon. ([people.math.harvard.edu][2])

3. **Ackoff, “From Data to Wisdom” (1989 address; widely circulated)** – Classic articulation of data→information→knowledge framing; helpful narrative device (with caveats) for a non-technical audience. ([faculty.ung.edu][3])

4. **Dammann (2019), “Data, Information, Evidence, and Knowledge”** – A readable critique/extension of DIKW, useful to pre-empt “DIKW is simplistic” objections while keeping the ladder as a communication tool. ([PMC][8])

5. **Berners-Lee, Hendler, Lassila (2001), “The Semantic Web”** – Canonical “make data meaningful to computers” reference; aligns strongly with your “middle layer” thesis. ([Scientific American][5])

6. **W3C RDF 1.1 Concepts (2014)** – Defines the RDF data model; useful as a citation for “graph-based representations of meaning”. ([w3.org][9])

7. **W3C OWL 2 Overview (2012)** – Formal grounding for ontologies; supports the claim that “meaning” can be modelled in machine-processable ways (carefully). ([w3.org][10])

8. **W3C PROV-O (2013)** – Standard for provenance representation; supports your auditability and traceability story. ([w3.org][7])

9. **W3C DCAT v3 (2024)** – Data catalog interoperability; strongly relevant to “capability catalogue” and discoverability across organisations. ([w3.org][6])

10. **Wilkinson et al. (2016), FAIR Guiding Principles** – A mainstream stewardship framework that explicitly aims for machine-findable/usable assets; pairs nicely with MCP as “machine-consumable capabilities”. ([Nature][4])

11. **ICO: Guidance on AI and data protection (under review due to DUAA 2025)** – The UK’s regulator view on applying UK GDPR principles to AI; crucial for your safe adoption path and for reassuring the audience. ([ICO][11])

12. **NCSC: Guidelines for secure AI system development (2023)** – Security lifecycle guidance (design → deployment → ops) with explicit emphasis on logging/monitoring and secure-by-default thinking. ([NCSC][12])

13. **HMG Generative AI Framework (PDF report)** – Practical UK government guidance for building genAI solutions; relevant to framing how to adopt MCP-enabled patterns safely. ([GOV.UK Assets][13])

14. **UK Government AI Playbook (2025)** – Updated principles and guidance for government AI adoption; useful “anchor” reference for an 80-person mixed audience. ([GOV.UK][14])

15. **Algorithmic Transparency Recording Standard (ATRS) hub (GOV.UK)** – A concrete public-sector transparency mechanism for algorithmic tools; useful for connecting “capabilities” to documentation and trust. ([GOV.UK][15])

16. **Five Safes framework (GOV.UK / ONS heritage)** – Widely used UK model for safe access to data; a natural backbone for your open→controlled→sensitive progression. ([GOV.UK][16])

17. **OWASP Top 10 for LLM Applications** – Widely-cited risk taxonomy (prompt injection, insecure output handling, etc.); supports why guardrails must sit *around* the model and tools. ([owasp.org][17])
