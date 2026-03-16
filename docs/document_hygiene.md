# Document Hygiene

This repo keeps some `.docx` files as working artifacts and publishable outputs.
Those files need explicit hygiene controls because Office metadata and embedded
body text can leak local paths, personal names, tenant identifiers, and
classification workflow details.

## Scope

Treat these as public-facing document areas by default:

- `docs/`
- `docs/reports/`
- `troubleshooting/`

Treat these as excluded from repo-authored hygiene checks unless explicitly
promoted into a public deliverable:

- `data/`
- `submodules/`
- `docs/vendor/`

## Required rules

- Do not commit Office lockfiles such as `~$*.docx`.
- Public-facing `.docx` files should have sibling `.md` and `.pdf` files unless
  there is a documented reason not to.
- Public-facing `.docx` files must not retain author/modifier fields that expose
  personal names unless authorship is intentionally part of the publication.
- Public-facing `.docx` files must not retain custom Office/MSIP metadata such
  as tenant/site/action identifiers.
- Public-facing `.docx` files must not contain absolute local filesystem paths
  in the document body.

## Tooling

Use [`/Users/crpage/repos/mcp-geo/scripts/docx_hygiene.py`](/Users/crpage/repos/mcp-geo/scripts/docx_hygiene.py).

Scan and write reports:

```bash
python3 scripts/docx_hygiene.py scan \
  --root . \
  --json-output docs/reports/docx_hygiene_audit_YYYY-MM-DD.json \
  --markdown-output docs/reports/docx_hygiene_audit_YYYY-MM-DD.md
```

Fail on issues:

```bash
python3 scripts/docx_hygiene.py scan --root . --fail-on-issues
```

Strip metadata from public-facing `.docx` files in place:

```bash
python3 scripts/docx_hygiene.py sanitize --root .
```

## Release workflow

1. Run the hygiene scan.
2. Remove any Office lockfiles.
3. Sanitize metadata for public-facing `.docx` files.
4. Review the markdown audit for missing `.md` and `.pdf` siblings.
5. Render or backfill missing deliverables where the document is intended to be
   published.
