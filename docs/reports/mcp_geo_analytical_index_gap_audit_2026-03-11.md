# MCP-Geo Analytical Index Gap Audit

This short note records how the replacement analytical index differs from the earlier rough appendix at the pinned public commit.

Baseline inputs: [rough Prism bundle appendix](https://github.com/chris-page-gov/mcp-geo/blob/fe862910da246ca77f374cfbe484985f5df4d316/docs/mcp_geo_prism_bundle/main.md#L122-L292), [slide deck](https://github.com/chris-page-gov/mcp-geo/blob/fe862910da246ca77f374cfbe484985f5df4d316/docs/slides/20260225%20-%20From_Apps_to_Answers.pdf), and [event record DOCX](https://github.com/chris-page-gov/mcp-geo/blob/fe862910da246ca77f374cfbe484985f5df4d316/docs/reports/mcp_geo_ai_community_event_record.docx).

## What the earlier appendix already did well

- The earlier Appendix A already identified the right broad reading domains: root orientation, runtime implementation, documentation, research, tests, and release material.
- The tracked slide deck, event record, and rough Prism bundle already established the design intention that visuals should sit inside the index rather than outside it.
- The previous appendix already linked representative repo locations and proved that a GitHub-first analytical index was viable.

## What was incomplete

- The earlier appendix stopped too early in the runtime and evidence surfaces, especially around resources, playground, release operations, and the dense report library.
- The summaries were helpful but often too thin to guide different reader types toward the right reading path.
- The visual layer was not yet strong enough to carry the story independently, and the prompt provenance for each infographic was not recorded.

## What the replacement now changes

- The replacement turns the appendix into a standalone analytical index first, then derives an appendix-ready version from the same source.
- The replacement adds a pinned commit source policy, a manifest-backed validation workflow, a full figure-prompt appendix, and a Prism-ready bundle with section files.
- The replacement treats the public repo as a curated full surface: all top-level tracked areas are accounted for, but bulky zones are summarized analytically instead of catalogued file by file.
