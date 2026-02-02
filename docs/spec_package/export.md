# Exporting the Specification Package

This package is authored in Markdown. You can export it into a more presentable
format (DOCX or PDF) using Pandoc. The repo includes a helper script:

```
scripts/export_spec_package.sh
```

## DOCX export (recommended for sharing)

1. Install Pandoc.
2. Run:

```
scripts/export_spec_package.sh
```

This produces:

- `docs/spec_package/build/mcp-geo-spec.docx`
- `docs/spec_package/build/mcp-geo-spec.pdf` (if `tectonic` is installed)

## PDF export

For PDF output, install a LaTeX engine (or `tectonic`). The script will
automatically emit PDF if `tectonic` is available.

## Prism (LaTeX-first workflow)

If you want to use Prism as a LaTeX-native authoring workflow, generate LaTeX
from Markdown with Pandoc:

```
pandoc docs/spec_package/01_aims_objectives.md \
  -o docs/spec_package/build/mcp-geo-spec.tex
```

Then open the `.tex` file in Prism for layout and export.
