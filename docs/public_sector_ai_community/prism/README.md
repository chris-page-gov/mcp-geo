# Prism-Ready LaTeX Package

## Contents

- `main.tex`
- `references.bib`
- `sections/*.tex`

## Compile Locally

```bash
cd docs/public_sector_ai_community/prism
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Prism Workflow

1. Create a new Prism project.
2. Upload this folder contents.
3. Compile `main.tex`.
4. Use Prism editing tools to adapt house style while preserving section labels and bibliography keys.

## Scope

This publication package summarizes the `mcp-geo` journey for UK Public Sector AI Community audiences, with novice-readable language and evidence cross-references.
