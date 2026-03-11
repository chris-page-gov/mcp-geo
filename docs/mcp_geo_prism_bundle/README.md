# MCP-Geo Analytical Index Prism Bundle

This bundle is generated from `docs/reports/mcp_geo_analytical_index_2026-03-11.md` and pinned to commit
`fe862910da246ca77f374cfbe484985f5df4d316` for stable GitHub citations.

## Contents

- `main.md`: bundle-friendly Markdown mirror of the canonical report
- `main.tex`: Prism-ready LaTeX wrapper
- `sections/*.tex`: generated section fragments
- `figures/*.png`: generated infographic assets
- `references.bib`: starter bibliography scaffolding

## Compile locally

```bash
cd docs/mcp_geo_prism_bundle
pdflatex main.tex
pdflatex main.tex
```

The canonical draft PDF remains `docs/reports/mcp_geo_analytical_index_2026-03-11.pdf`; `main.tex` exists so Prism can
import the same content with editable section files and pinned links.
