# Notebook Scenario Packs

Map scenario packs convert notebook-authored scenarios into MCP resources with
provenance metadata.

## Generate packs

```bash
python scripts/map_trials/export_notebook_scenario_pack.py
```

Default output directory:

- `data/map_scenario_packs/`

## Resource URIs

- Index: `resource://mcp-geo/map-scenario-packs-index`
- Pack file: `resource://mcp-geo/map-scenario-packs/<pack>.json`

Each pack includes:

- `sourceNotebook`
- `generatedAt`
- `hash` (SHA-256)
- `scenarios[]`
- `provenance`

## Lifecycle guidance

1. Update notebook scenarios.
2. Re-export scenario packs.
3. Validate resource retrieval using `/resources/read`.
4. Keep generated packs under version control for deterministic review.
