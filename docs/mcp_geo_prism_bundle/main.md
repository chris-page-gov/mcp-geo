# From Apps to Answers
## Formal event record of the AI Community talk delivered on 25 February 2026

Prepared from the supplied slide deck and transcript, with failed live demonstration sequences omitted from the narrative record.

![Title slide](figures/slide_01.jpg)

### Executive summary

This report records the principal argument of the talk as a formal narrative rather than a transcript. It reconstructs the progression of ideas from the presentation materials: first, that public-sector decision support is moving beyond dashboards and application switching; second, that this shift requires a governed middle layer rather than direct “chat with data”; and third, that MCP can be shaped into such a layer when combined with semantics, permissions, provenance, and auditability.

The talk presented MCP-Geo as a research prototype built to test how far agentic software generation and tool-mediated reasoning could be pushed against demanding public-sector datasets, particularly Ordnance Survey and Office for National Statistics sources. The prototype was described not as a production service but as an exploratory system intended to surface both opportunity and constraint.

Across the talk, five capabilities were repeatedly emphasised: discovery of tools and meaning; cross-domain composition of data; security and role-aware access; provenance by default; and auditability strong enough to support scrutiny. The concluding discussion linked these ideas to a broader UK public-sector agenda for AI-ready datasets and machine-readable, governed access to evidence.

## 1. Opening frame: from interfaces to answers

The opening of the talk established the central contrast that shaped everything that followed. Existing public-sector information work was described as heavily application-led: analysts and policy users move between dashboards, reports, databases, spreadsheets, mapping tools, and local notes before they can assemble a defensible answer. The proposed alternative was an answer-led model in which a governed orchestration layer coordinates the retrieval, combination, and explanation of evidence.

![Codex usage summary](figures/slide_02.jpg)

To motivate the seriousness of the experiment, the talk briefly quantified the engineering effort invested in the prototype. The figures presented on screen showed hundreds of hours of Codex-mediated development, very large token consumption, and a sizeable codebase. These numbers were used rhetorically to make one point: the system was not a superficial mock-up but a substantial research build intended to probe the practical limits of current AI-assisted development.

![Architectural contrast](figures/slide_03.jpg)

![Delivery shift](figures/slide_04.jpg)

The presentation then sharpened the distinction between the current and proposed modes of work. In the current model, users must know which dashboard to open, which filters to apply, how to interpret the resulting fragments, and how to synthesise them into an answer. In the proposed model, that cognitive burden moves into the system. The user still asks the question and still reviews the evidence, but the assembly of the answer is handled through a controlled middle layer.

![Shift from UI-first to answer-first](figures/slide_05.jpg)

## 2. Why direct chat with data is inadequate

A substantial part of the argument turned on what the speaker regarded as the wrong design choice: direct conversational access to databases without an intervening governance layer. In that model, language models may produce plausible but incorrect SQL, misread the meaning of fields, or generate answers without carrying forward the operational constraints that would normally be enforced by an application or analyst workflow.

![Chat with database critique](figures/slide_06.jpg)

This problem was described as the risk of an “empty middle”: a space in which the user’s question and the organisation’s raw data are joined only by an ungoverned model. In such a configuration, access policy, semantic controls, and provenance are weak or absent.

![The empty middle](figures/slide_07.jpg)

The proposed remedy was a “glass box” rather than a black box. In the talk’s model, the client asks, the MCP layer mediates, the server executes, and the evidence remains tied to its originating system. That design choice matters because it allows the answer to remain inspectable.

![Glass box workflow](figures/slide_08.jpg)

![Strategic alignment](figures/slide_09.jpg)

![Government guidance alignment](figures/slide_10.jpg)

## 3. MCP as a governed middle layer

The next movement of the talk explained MCP in operational rather than purely technical terms. MCP was presented as a standardised interface through which AI hosts can discover tools, consume resources, and use prompt templates supplied by a server.

![MCP connectivity standard](figures/slide_11.jpg)

Within that model, the MCP server was portrayed as the place where five responsibilities belong: discovery, semantic alignment, policy enforcement, provenance, and operational controls such as rate limits.

![Governed middle layer](figures/slide_12.jpg)

![Discovery and semantics](figures/slide_13.jpg)

The second capability was composition across domains. The talk used the example of separate departmental MCP servers being orchestrated together while each department retained control of its own access rules.

![Cross-domain composition](figures/slide_14.jpg)

Semantics occupied a central place in the argument. The talk repeatedly stressed that place-based and policy questions fail when systems do not preserve the meaning and granularity of their underlying data.

![Semantics and meaning alignment](figures/slide_15.jpg)

![BDUK semantic access layer](figures/slide_16.jpg)

![Geospatial and statistical context](figures/slide_17.jpg)

## 4. Permissions, security and transport

The third capability in the talk’s framework was security and governance. Identity alone is not enough; meaningful control requires role-aware and policy-aware access so that the same question may legitimately yield different answers to different users.

![Security and governance](figures/slide_18.jpg)

This was reinforced by a simple warning: prompts are not policies. A system is unsafe if a prompt is the only mechanism preventing a model from requesting or revealing protected information.

![Policy and permissions](figures/slide_19.jpg)

Transport was then discussed in a practical way. The presentation described gRPC transport support as a significant development because it offers a route to stronger enterprise control and higher-performance server communication.

![gRPC transport](figures/slide_20.jpg)

## 5. Provenance, auditability and data cards

The fourth capability was provenance by default. In the talk’s framing, an answer without evidence is functionally a hallucination, even when it sounds plausible.

![Provenance by default](figures/slide_21.jpg)

Auditability followed naturally from this. The talk proposed that MCP systems should generate durable records of question, tool usage, source access, and resulting claims that would be strong enough for scrutiny by auditors or investigators.

![Provenance and auditability](figures/slide_22.jpg)

The UPRN examples made the argument concrete. A single location can contain several distinct reference entities, such as a building shell and the premises within it. If the system answers against the wrong entity, the policy conclusion can be wrong even when the underlying data are accurate.

![UPRN audit](figures/slide_23.jpg)

![Anatomy of a data card](figures/slide_24.jpg)

![UPRN data card view 1](figures/slide_25.jpg)

![UPRN data card view 2](figures/slide_26.jpg)

## 6. Discussion and closing remarks

The closing discussion broadened the implications of the prototype. When asked which dataset might follow, the speaker pointed to BDUK’s broadband-delivery data as the next major extension area: a domain characterised by very large volumes, supplier returns, changing forward plans, and difficult premise-level interpretation.

Questions about client support highlighted a more mixed reality. Different MCP clients were said to expose protocol features unevenly, particularly around elicitation and interactive UI elements. That limitation was important because part of the prototype’s value lies in guided user input, such as map-based selection rather than purely textual disambiguation.

Finally, the audience discussion confirmed that the repository itself was intended as part of the contribution. The codebase, supporting documentation, traces, research notes, and testing harnesses were all described as evidence of a learning journey as well as of a working prototype.

## 7. Overall assessment

Taken as a whole, the talk argued for a specific architectural discipline in public-sector AI. It did not claim that conversational interfaces alone can safely replace existing information systems. Instead, it argued that useful AI-mediated answers require a governed layer able to discover tools, preserve semantics, compose sources, enforce permissions, and capture provenance.

MCP-Geo was offered as a practical experiment in that direction: ambitious enough to test difficult geospatial and statistical problems, but explicit about its research status and its remaining gaps.

# Appendix A. Annotated index to the public MCP-Geo repository

Repository reviewed: <https://github.com/chris-page-gov/mcp-geo>

![Repository at a glance](figures/infographic_repo_map.png)

![Documentation path](figures/infographic_documentation_path.png)

![Governed answer loop](figures/infographic_governed_loop.png)

## A1. Root orientation

The repository root establishes the project’s status, startup route, operating assumptions, and principal supporting files.

### A1.1 README and first-use path

The quickest route into the project. It explains the research purpose, the public-launch caveat, how to obtain OS and ONS keys, how to run the Docker container, and how to ask a first question.

- [README.md](https://github.com/chris-page-gov/mcp-geo/blob/main/README.md)
- [tutorial.md](https://github.com/chris-page-gov/mcp-geo/blob/main/tutorial.md)
- [mcp.json](https://github.com/chris-page-gov/mcp-geo/blob/main/mcp.json)
- [Dockerfile](https://github.com/chris-page-gov/mcp-geo/blob/main/Dockerfile)

### A1.2 Context, progress and operating notes

These files frame the project for collaborators and AI coding agents: durable context, progress tracking, safe-by-design statements, and contributor instructions.

- [CONTEXT.md](https://github.com/chris-page-gov/mcp-geo/blob/main/CONTEXT.md)
- [PROGRESS.MD](https://github.com/chris-page-gov/mcp-geo/blob/main/PROGRESS.MD)
- [safe-by-design.json](https://github.com/chris-page-gov/mcp-geo/blob/main/safe-by-design.json)
- [AGENTS.md](https://github.com/chris-page-gov/mcp-geo/blob/main/AGENTS.md)
- [xCOPILOT_INSTRUCTIONS.md](https://github.com/chris-page-gov/mcp-geo/blob/main/xCOPILOT_INSTRUCTIONS.md)

## A2. Runtime implementation

The core executable system is split between server logic, domain tools, and UI artefacts.

### A2.1 server/

This is the runtime backbone: configuration, caches, transport, logging, observability, boundary handling, and the main application entry point.

- [server/](https://github.com/chris-page-gov/mcp-geo/tree/main/server)
- [main.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/main.py)
- [config.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/config.py)
- [observability.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/observability.py)
- [boundary_cache.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/boundary_cache.py)

### A2.1.1 server/mcp/

The protocol-facing layer. It contains transport support, prompts, resources, tool search, elicitation forms, and the playground UI used for local inspection.

- [server/mcp/](https://github.com/chris-page-gov/mcp-geo/tree/main/server/mcp)
- [http_transport.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/mcp/http_transport.py)
- [elicitation_forms.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/mcp/elicitation_forms.py)
- [playground.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/mcp/playground.py)
- [resource_catalog.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/mcp/resource_catalog.py)
- [tools.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/mcp/tools.py)

### A2.1.2 server/audit/

The audit subsystem packages the kind of provenance and disclosure logic emphasised in the talk: decision records, source registers, redaction, retention, integrity checks, and pack building.

- [server/audit/](https://github.com/chris-page-gov/mcp-geo/tree/main/server/audit)
- [decision_record.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/audit/decision_record.py)
- [episode_builder.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/audit/episode_builder.py)
- [pack_builder.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/audit/pack_builder.py)
- [source_register.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/audit/source_register.py)
- [redaction.py](https://github.com/chris-page-gov/mcp-geo/blob/main/server/audit/redaction.py)

### A2.2 tools/

This directory holds the domain-facing tool layer. It is where OS, ONS, NOMIS, admin lookup and delivery-specific logic are exposed as callable capabilities.

- [tools/](https://github.com/chris-page-gov/mcp-geo/tree/main/tools)
- [admin_lookup.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tools/admin_lookup.py)
- [ons_data.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tools/ons_data.py)
- [ons_geo.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tools/ons_geo.py)
- [os_features.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tools/os_features.py)
- [os_linked_ids.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tools/os_linked_ids.py)
- [os_map.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tools/os_map.py)

### A2.3 ui/

These HTML artefacts are the visual components surfaced through MCP-Apps-style resources: geography selection, route planning, feature inspection, simple maps and statistics dashboards.

- [ui/](https://github.com/chris-page-gov/mcp-geo/tree/main/ui)
- [geography_selector.html](https://github.com/chris-page-gov/mcp-geo/blob/main/ui/geography_selector.html)
- [feature_inspector.html](https://github.com/chris-page-gov/mcp-geo/blob/main/ui/feature_inspector.html)
- [route_planner.html](https://github.com/chris-page-gov/mcp-geo/blob/main/ui/route_planner.html)
- [statistics_dashboard.html](https://github.com/chris-page-gov/mcp-geo/blob/main/ui/statistics_dashboard.html)

## A3. Documentation and specification

The repository is unusually rich in explanatory material, making it suitable for both technical reviewers and non-specialist readers.

### A3.1 docs/public_sector_ai_community/

This is the most accessible narrative route through the repo. It explains the origin story, architecture, timeline, troubleshooting journey, evaluation, governance questions and future direction in chapter form.

- [docs/public_sector_ai_community/](https://github.com/chris-page-gov/mcp-geo/tree/main/docs/public_sector_ai_community)
- [README.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/public_sector_ai_community/README.md)
- [01_overview_for_novices.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/public_sector_ai_community/01_overview_for_novices.md)
- [03_architecture_and_components.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/public_sector_ai_community/03_architecture_and_components.md)
- [07_harness_permissions_and_debugging_journey.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/public_sector_ai_community/07_harness_permissions_and_debugging_journey.md)
- [14_evidence_and_report_index.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/public_sector_ai_community/14_evidence_and_report_index.md)

### A3.1.1 docs/public_sector_ai_community/prism/

Publication assets for the repo narrative. This is the clearest precedent for turning the repository into a polished manuscript.

- [prism/](https://github.com/chris-page-gov/mcp-geo/tree/main/docs/public_sector_ai_community/prism)
- [main.tex](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/public_sector_ai_community/prism/main.tex)
- [references.bib](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/public_sector_ai_community/prism/references.bib)

### A3.2 docs/spec_package/

A test-ready specification package covering aims, personas, architecture, design, data flow, API contracts, security, operations, testing, UI, walkthroughs and backlog.

- [docs/spec_package/](https://github.com/chris-page-gov/mcp-geo/tree/main/docs/spec_package)
- [README.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/spec_package/README.md)
- [03_architecture.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/spec_package/03_architecture.md)
- [06_api_contracts.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/spec_package/06_api_contracts.md)
- [07_security_privacy.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/spec_package/07_security_privacy.md)
- [08_observability_ops.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/spec_package/08_observability_ops.md)
- [09_testing_quality.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/spec_package/09_testing_quality.md)
- [11_walkthroughs.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/spec_package/11_walkthroughs.md)

### A3.3 docs/ root working papers

The wider docs/ directory includes benchmark material, case-study outputs, boundary notes, getting-started material and mapping reviews.

- [docs/](https://github.com/chris-page-gov/mcp-geo/tree/main/docs)
- [getting_started.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/getting_started.md)
- [evaluation.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/evaluation.md)
- [golden_prompts_mcp_geo.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/golden_prompts_mcp_geo.md)
- [examples.md](https://github.com/chris-page-gov/mcp-geo/blob/main/docs/examples.md)

## A4. Research, quality and supporting evidence

These areas show that the repository is both a codebase and an evidence pack for iterative development.

### A4.1 research/

Holds deeper research outputs, including the “From Apps to Answers” work package, dataset-selection studies and packaged reports.

- [research/](https://github.com/chris-page-gov/mcp-geo/tree/main/research)
- [From Apps to Answers - Connecting Public Sector Data to AI with MCP/](https://github.com/chris-page-gov/mcp-geo/tree/main/research/From%20Apps%20to%20Answers%20-%20Connecting%20Public%20Sector%20Data%20to%20AI%20with%20MCP)
- [Deep Research Report/](https://github.com/chris-page-gov/mcp-geo/tree/main/research/Deep%20Research%20Report)
- [os_dataset_selection/](https://github.com/chris-page-gov/mcp-geo/tree/main/research/os_dataset_selection)
- [ons_dataset_selection/](https://github.com/chris-page-gov/mcp-geo/tree/main/research/ons_dataset_selection)

### A4.2 tests/

A broad test harness covering accessors, admin lookup, audit pack building, boundary handling, client capabilities, configuration and other runtime behaviours.

- [tests/](https://github.com/chris-page-gov/mcp-geo/tree/main/tests)
- [test_audit_api.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tests/test_audit_api.py)
- [test_audit_pack_builder.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tests/test_audit_pack_builder.py)
- [test_boundary_cache.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tests/test_boundary_cache.py)
- [test_client_capabilities.py](https://github.com/chris-page-gov/mcp-geo/blob/main/tests/test_client_capabilities.py)

### A4.3 Operations and release materials

These files help a reader assess maturity, change history and the practicalities of running the prototype.

- [CHANGELOG.md](https://github.com/chris-page-gov/mcp-geo/blob/main/CHANGELOG.md)
- [RELEASE_NOTES/](https://github.com/chris-page-gov/mcp-geo/tree/main/RELEASE_NOTES)
- [scripts/](https://github.com/chris-page-gov/mcp-geo/tree/main/scripts)
- [troubleshooting/](https://github.com/chris-page-gov/mcp-geo/tree/main/troubleshooting)

## Appendix B. External references

- Government guidance: <https://www.gov.uk/government/publications/making-government-datasets-ready-for-ai/guidelines-and-best-practices-for-making-government-datasets-ready-for-ai>
- Public repository reviewed: <https://github.com/chris-page-gov/mcp-geo>
