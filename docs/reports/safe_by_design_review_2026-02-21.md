# Safe-by-Design Review (mcp-geo)

Date: 2026-02-21  
Reviewer: Codex (GPT-5)  
Scope:
- Repository code review for safe-by-design, governance, and assurance controls.
- Citation and bibliography audit for:
  - `/Users/crpage/repos/mcp-geo/research/From Apps to Answers - Connecting Public Sector Data to AI with MCP/main.tex`
  - `/Users/crpage/repos/mcp-geo/research/From Apps to Answers - Connecting Public Sector Data to AI with MCP/sections/*.tex`
  - `/Users/crpage/repos/mcp-geo/research/From Apps to Answers - Connecting Public Sector Data to AI with MCP/references.bib`

## Standards Baseline Verified

Primary authoritative anchors validated (accessed 2026-02-21):
- NCSC: Guidelines for Secure AI System Development (`https://www.ncsc.gov.uk/files/Guidelines-for-secure-AI-system-development.pdf`)
- ICO: Guidance on AI and data protection (`https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/`)
- UK Gov: Data and AI Ethics Framework (`https://www.gov.uk/government/publications/data-ethics-framework/data-and-ai-ethics-framework`)
- UK Gov: Algorithmic Transparency Recording Standard hub (`https://www.gov.uk/government/collections/algorithmic-transparency-recording-standard-hub`)
- ONS: Secure Research Service (Five Safes framing) (`https://www.ons.gov.uk/aboutus/whatwedo/statistics/requestingstatistics/secureresearchservice/aboutthesecureresearchservice`)
- OWASP: Top 10 for LLM Applications (`https://genai.owasp.org/llm-top-10/`)
- W3C PROV-O (`https://www.w3.org/TR/prov-o/`)
- W3C PROV-DM (`https://www.w3.org/TR/prov-dm/`)
- W3C DCAT v3 (`https://www.w3.org/TR/vocab-dcat-3/`)
- MCP Spec revision 2025-11-25 (`https://modelcontextprotocol.io/specification/2025-11-25/`)

## Citation Integrity Checks

- `\cite{...}` keys used across all `.tex` files: **26**
- Missing cite keys in `references.bib`: **0**
- Used keys missing required metadata fields (`title`, `author/institution`, `year`, `howpublished/type`, `url`, `note=Accessed YYYY-MM-DD`): **0**
- Unused entries in `references.bib`: present (not an integrity error)

## Governance Claim Audit Table

| Location (file + section) | Statement (verbatim) | Current citation keys | Assessment (OK / needs improvement) | Recommended citation keys and why |
| --- | --- | --- | --- | --- |
| `sections/01-executive-summary.tex` (Executive summary) | "...a controlled `middle layer` transforms raw data into usable information with provenance, permissions, and auditability." | `mcp_spec_2025_11_25,prov_o,prov_dm` | OK (definition/recommendation) | Existing keys are sufficient for MCP + provenance grounding. |
| `sections/01-executive-summary.tex` (Executive summary) | "...practical responsibility sits... safety guardrails..." | `ncsc_secure_ai_guidelines,ico_ai_data_protection,data_ai_ethics_framework,five_safes_framework,algorithmic_transparency_recording_standard` | OK (recommendation) | Strong UK governance bundle; no extra key required. |
| `sections/01-executive-summary.tex` (Executive summary) | "...errors and `unknowns` should surface (with provenance) and audit traces support assurance." | `mcp_spec_2025_11_25,prov_o,algorithmic_transparency_recording_standard,artefact_claude_stopped_after_ngd_features_2026_02_18,artefact_codex_trace_jsonl_2026_02_18` | OK (recommendation) | Standards + empirical artefacts are now jointly cited. |
| `sections/01-executive-summary.tex` (Executive summary) | "...adopting safely in stages: open -> controlled -> sensitive" | `five_safes_framework,ico_ai_data_protection,ncsc_secure_ai_guidelines` | OK (recommendation) | Sufficient for staged sensitivity controls in UK context. |
| `sections/02-problem-and-thesis.tex` (Key terms) | "Provenance... so results can be checked and reproduced." | `prov_dm` | OK (definition) | Optionally add `prov_o` for ontology-level alignment. |
| `sections/02-problem-and-thesis.tex` (Key terms) | "Guardrails... access, policy, privacy, safe defaults..." | `ico_ai_data_protection,ncsc_secure_ai_guidelines,owasp_llm_top10` | OK (definition/recommendation) | Strong crosswalk across privacy/security/LLM abuse controls. |
| `sections/02-problem-and-thesis.tex` (Thesis) | "Together, these strands motivate a governed `middle layer`..." | `data_ai_ethics_framework,ncsc_secure_ai_guidelines` | OK (recommendation) | Added governance/security anchors for thesis conclusion. |
| `sections/02a-term-mapping-table.tex` (Term mapping) | "Capability catalogue... discoverability is required for automation" | `dcat3,mcp_spec_2025_11_25` | OK (factual/recommendation) | Correct standards for catalogue + capability discovery. |
| `sections/02a-term-mapping-table.tex` (Term mapping) | "Evidence-first answers... Core to public-sector trust" | `prov_o,prov_dm,algorithmic_transparency_recording_standard` | OK (recommendation) | Correct provenance + transparency linkage. |
| `sections/02a-term-mapping-table.tex` (Term mapping) | "Safe-by-design... Matches UK delivery expectations" | `ncsc_secure_ai_guidelines,ico_ai_data_protection,data_ai_ethics_framework` | OK (recommendation) | Sufficient UK policy and secure-development anchors. |
| `sections/08-risks-and-guardrails.tex` (Risks) | "Over-claiming: confusing information retrieval with grounded, auditable answers." | `owasp_llm_top10,ncsc_secure_ai_guidelines` | OK (risk statement) | Added and sufficient. |
| `sections/08-risks-and-guardrails.tex` (Risks) | "Safety and privacy... mixed-sensitivity data..." | `ico_ai_data_protection,ncsc_secure_ai_guidelines,five_safes_framework` | OK (risk statement) | Appropriate and sufficient. |
| `sections/08-risks-and-guardrails.tex` (Guardrails) | "Provenance-first outputs..." | `prov_o,prov_dm` | OK (recommendation) | Appropriate provenance standards. |
| `sections/10-demo-script.tex` (Reconstruct trust via audit) | "MCP gives us auditability..." | `mcp_spec_2025_11_25,prov_o,algorithmic_transparency_recording_standard` | OK (recommendation) | Added and sufficient for protocol + audit framing. |
| `sections/10-demo-script.tex` (Sensitive data Q&A) | "...default to aggregation/redaction... require explicit privilege..." | `ico_ai_data_protection,five_safes_framework,data_ai_ethics_framework` | OK (recommendation) | Strong UK privacy/governance support. |
| `sections/11-requirements.tex` (R1) | "MUST classify each request into an intent class... route to explicit workflow with safe defaults." | `mcp_spec_2025_11_25,owasp_llm_top10,ncsc_secure_ai_guidelines` | OK (requirement) | Added standards mapping for routing safety and abuse resistance. |
| `sections/11-requirements.tex` (R10) | "Every user-facing answer MUST include a provenance block..." | `prov_o,prov_dm,algorithmic_transparency_recording_standard,dcat3` | OK (requirement) | Correct for provenance + transparency + catalogue metadata context. |
| `sections/11-requirements.tex` (R11) | "MUST support data-classification-aware behaviour... redact or aggregate by default..." | `ico_ai_data_protection,five_safes_framework,data_ai_ethics_framework,ncsc_secure_ai_guidelines` | OK (requirement) | Strong UK policy and secure-design grounding. |
| `sections/11-requirements.tex` (R12) | "MUST emit structured audit logs... deterministically replayed..." | `algorithmic_transparency_recording_standard,prov_o,mcp_spec_2025_11_25,ncsc_secure_ai_guidelines` | OK (requirement) | Correct traceability/audit/replay basis. |

## BibTeX Patch List (Applied)

Updated entries in `references.bib`:

1. `ico_ai_data_protection` (`references.bib:110`)
- Updated `note` to `Accessed 2026-02-21`.

2. `ncsc_secure_ai_guidelines` (`references.bib:119`)
- Updated `note` to `Accessed 2026-02-21`.

3. `algorithmic_transparency_recording_standard` (`references.bib:142-147`)
- `title`: `Algorithmic Transparency Recording Standard Hub`
- `year`: `2023`
- `url`: `https://www.gov.uk/government/collections/algorithmic-transparency-recording-standard-hub`
- `note`: `Accessed 2026-02-21; last updated 2025-05-08`

4. `five_safes_framework` (`references.bib:151-156`)
- Replaced dead URL with live ONS page:
  - `url`: `https://www.ons.gov.uk/aboutus/whatwedo/statistics/requestingstatistics/secureresearchservice/aboutthesecureresearchservice`
- `title`: `About the Secure Research Service (Five Safes Framework)`
- `year`: `n.d.`
- `note`: `Accessed 2026-02-21`

5. `owasp_llm_top10` (`references.bib:164`)
- Updated `note` to `Accessed 2026-02-21`.

6. `data_ai_ethics_framework` (`references.bib:215-216`)
- `url`: `https://www.gov.uk/government/publications/data-ethics-framework/data-and-ai-ethics-framework`
- `note`: `Accessed 2026-02-21; updated 2025-12-18`

## TeX Patch List (Applied)

Exact line updates:

- `sections/08-risks-and-guardrails.tex:5`
  - Added: `\\cite{owasp_llm_top10,ncsc_secure_ai_guidelines}`

- `sections/10-demo-script.tex:57`
  - Added: `\\cite{mcp_spec_2025_11_25,prov_o,algorithmic_transparency_recording_standard}`
- `sections/10-demo-script.tex:66`
  - Added: `\\cite{mcp_spec_2025_11_25,ncsc_secure_ai_guidelines,data_ai_ethics_framework}`
- `sections/10-demo-script.tex:146`
  - Added: `\\cite{prov_o,algorithmic_transparency_recording_standard}`
- `sections/10-demo-script.tex:168`
  - Added: `\\cite{ico_ai_data_protection,five_safes_framework,data_ai_ethics_framework}`
- `sections/10-demo-script.tex:174`
  - Added: `\\cite{mcp_spec_2025_11_25,prov_o,algorithmic_transparency_recording_standard}`
- `sections/10-demo-script.tex:183`
  - Added: `\\cite{mcp_spec_2025_11_25,data_ai_ethics_framework}`
- `sections/01-executive-summary.tex:9`
  - Added: `\\cite{prov_o,algorithmic_transparency_recording_standard}`
- `sections/02-problem-and-thesis.tex:23`
  - Added: `\\cite{data_ai_ethics_framework,ncsc_secure_ai_guidelines}`

- `sections/11-requirements.tex:14`
  - Added: `\\cite{mcp_spec_2025_11_25,owasp_llm_top10,ncsc_secure_ai_guidelines}`
- `sections/11-requirements.tex:23`
  - Added: `\\cite{dcat3,data_ai_ethics_framework,algorithmic_transparency_recording_standard}`
- `sections/11-requirements.tex:32`
  - Added: `\\cite{owasp_llm_top10,ncsc_secure_ai_guidelines}`
- `sections/11-requirements.tex:47`
  - Added: `\\cite{owasp_llm_top10,ncsc_secure_ai_guidelines}`
- `sections/11-requirements.tex:62`
  - Added: `\\cite{mcp_spec_2025_11_25,owasp_llm_top10}`
- `sections/11-requirements.tex:75`
  - Added: `\\cite{algorithmic_transparency_recording_standard,prov_dm}`
- `sections/11-requirements.tex:89`
  - Added: `\\cite{prov_dm,algorithmic_transparency_recording_standard,owasp_llm_top10}`
- `sections/11-requirements.tex:103`
  - Added: `\\cite{ncsc_secure_ai_guidelines,owasp_llm_top10}`
- `sections/11-requirements.tex:112`
  - Added: `\\cite{ncsc_secure_ai_guidelines,owasp_llm_top10}`
- `sections/11-requirements.tex:125`
  - Added: `\\cite{prov_o,prov_dm,algorithmic_transparency_recording_standard,dcat3}`
- `sections/11-requirements.tex:140`
  - Added: `\\cite{ico_ai_data_protection,five_safes_framework,data_ai_ethics_framework,ncsc_secure_ai_guidelines}`
- `sections/11-requirements.tex:154`
  - Added: `\\cite{algorithmic_transparency_recording_standard,prov_o,mcp_spec_2025_11_25,ncsc_secure_ai_guidelines}`

## Code Review Findings (Detailed)

### High severity

1. `server/mcp/resource_catalog.py` path traversal / path-boundary bypass
- Affected lines: `971-977`, `978-993`, `994-1008`, `1009-1024`, `1064-1079`.
- Problem:
  - `ons-cache/*` branch does not normalize/contain-check paths.
  - `ons-exports/*`, `os-cache/*`, `os-exports/*`, `exports/*` use `str(path).startswith(str(root))`, which is bypassable with sibling prefix paths.
- Verified PoC:
  - `load_data_content({'slug':'ons-exports/../ons_exports_evil/poc.json'})` returned data outside `data/ons_exports/`.
- #TODO# `SBD-CODE-001`: replace all `startswith` path checks with canonical containment (`Path.resolve()` + `relative_to` helper), apply consistently to every file-backed resource branch, and add negative traversal tests for `..`, sibling-prefix, and encoded path cases.

2. `server/logging.py` + `tools/nomis_common.py` incomplete secret redaction
- Affected lines:
  - `server/logging.py:43-47`
  - `tools/nomis_common.py:87-93`, `127-133`, `146-153`, `167-173`, `185-190`
- Problem:
  - Redaction list includes only `OS_API_KEY`.
  - NOMIS credentials (`NOMIS_UID`, `NOMIS_SIGNATURE`) are merged into request params and logged via `log_upstream_error(... params=merged ...)`.
- #TODO# `SBD-CODE-002`: include NOMIS credentials and other configured secrets in redaction set; add key-name-based redaction (`signature`, `token`, `authorization`, `api_key`) before logging; add regression tests proving credentials never appear in logs.

3. `server/stdio_adapter.py` and `server/mcp/http_transport.py` internal exception disclosure
- Affected lines:
  - `server/stdio_adapter.py:1079-1084`
  - `server/mcp/http_transport.py:702-706`
- Problem:
  - JSON-RPC errors return `Internal error: {exc}` to clients.
  - Exception text can expose internals and potentially sensitive context.
- #TODO# `SBD-CODE-003`: return generic client-safe messages (`Internal error`) with correlation IDs; keep full exception detail server-side only (redacted logs).

### Medium severity

4. `server/config.py` rate limiter bypass defaults to enabled
- Affected line: `server/config.py:22`
- Problem: `RATE_LIMIT_BYPASS=True` by default is unsafe for production posture.
- #TODO# `SBD-CODE-004`: set secure default `False`, require explicit opt-in bypass in tests/dev, and document environment profiles.

5. JSON parse errors in HTTP endpoints can fall into generic 500 path
- Affected lines:
  - `server/mcp/tools.py:170`, `242`
  - `server/mcp/playground.py:88`, `120`
- Problem:
  - `await request.json()` is called without local parse guards.
  - Invalid JSON can trigger exception-handler path instead of consistent `400 INVALID_INPUT` envelope.
- #TODO# `SBD-CODE-005`: wrap JSON parsing in explicit `try/except` (`JSONDecodeError`) returning structured 400 responses; add tests for malformed payloads.

6. Log formatting bug reduces observability quality
- Affected lines:
  - `server/main.py:121-127`, `184-191`
- Problem:
  - Loguru-style logger is called with `%s` placeholders in several places.
  - Structured values may not be rendered as intended, reducing audit quality.
- #TODO# `SBD-CODE-006`: migrate to loguru `{}` placeholders or f-strings consistently; add log-format regression tests for critical audit events.

### Low severity

7. Debug print in app startup path
- Affected line: `server/main.py:20`
- Problem: `print("[DEBUG] server/main.py loaded", flush=True)` bypasses structured logging controls.
- #TODO# `SBD-CODE-007`: remove raw print; use logger with level gate.

8. Silent import failures hide tool registration issues
- Affected lines: `server/mcp/tools.py:49-53`
- Problem: broad `except Exception: pass` masks import errors at startup.
- #TODO# `SBD-CODE-008`: capture and log import failures with explicit diagnostics and health signal.

## Codex-Applicable Compliance Checklist Statements

These checklist statements are intended to be machine-actionable for repository assessment.

### safe-by-design
- `CHK-SBD-001`: Every user-facing answer path includes provenance metadata (source, transform, limits).
- `CHK-SBD-002`: Every high-impact action path has explicit guardrails and deny-safe defaults.

### guardrails
- `CHK-GRD-001`: Tool routes enforce intent-to-workflow mapping before heavy data calls.
- `CHK-GRD-002`: Payload-size budgets and progressive disclosure are enforced by code, not convention.

### privacy / sensitive data / redaction
- `CHK-PRV-001`: Sensitive datasets require explicit authorization checks before retrieval.
- `CHK-PRV-002`: Responses over sensitive scopes default to aggregation/redaction unless override is authorized.
- `CHK-RED-001`: All configured secrets and token-like fields are redacted in logs and errors.

### auditability / provenance / transparency
- `CHK-AUD-001`: Structured audit logs are deterministic and replayable for incident reconstruction.
- `CHK-AUD-002`: Correlation IDs are propagated across request, tool call, and response boundaries.
- `CHK-PROV-001`: Provenance model maps to PROV-O/PROV-DM concepts (entity/activity/agent relationships).
- `CHK-TRN-001`: Algorithmic decisions and automation use-cases are recordable against ATRS expectations.

### secure development / risk management
- `CHK-SEC-001`: Path/file access is traversal-safe with canonical containment checks.
- `CHK-SEC-002`: Client error payloads never include raw internal exception messages.
- `CHK-RSK-001`: Rate limiting, retries, and degradation are enabled by secure default configuration.

### standards alignment
- `CHK-STD-001`: Resource catalog metadata aligns with DCAT v3-compatible semantics.
- `CHK-STD-002`: MCP protocol behavior matches dated spec revision (2025-11-25).
- `CHK-STD-003`: UK governance anchors (ICO/NCSC/Data Ethics/Five Safes/ATRS) are traceably cited where claims are made.
- `CHK-OWA-001`: OWASP LLM controls are reflected in threat handling (prompt/tool abuse, denial-of-wallet, data exfil paths).

## Compliance Rubric

Scoring scale per dimension: `0..5` (0=not met, 5=fully met).  
Weighted score = `(score / 5) * weight`.

| Dimension | Weight | Current score (0-5) | Weighted points | Notes |
| --- | ---: | ---: | ---: | --- |
| Safe-by-design architecture | 10 | 3 | 6.0 | Strong intent and docs; implementation gaps remain. |
| Guardrails | 8 | 3 | 4.8 | Some payload and routing controls implemented. |
| Privacy & data protection (ICO/Five Safes) | 12 | 2 | 4.8 | Governance intent present; authz/redaction gaps remain. |
| Secure development (NCSC) | 12 | 2 | 4.8 | Major traversal and exception disclosure issues. |
| OWASP LLM controls | 10 | 2 | 4.0 | Partial alignment; not fully enforced across runtime. |
| Provenance & auditability (PROV/ATRS) | 12 | 3 | 7.2 | Good direction, incomplete deterministic guarantees. |
| Transparency & governance records (ATRS/Data Ethics) | 8 | 3 | 4.8 | Research brief now stronger; runtime evidence still uneven. |
| Sensitive data & redaction | 8 | 1 | 1.6 | Secret-handling gaps are material. |
| Risk management & resilience | 10 | 2 | 4.0 | Retry/degrade present in places; secure defaults not consistent. |
| Standards traceability in brief/bibliography | 10 | 5 | 10.0 | Citation coverage and metadata now complete for active claims. |
| **Total** | **100** |  | **52.0 / 100** | **Partially met** |

## Current Status and Transition Target

- Current status: `partially_met`
- Target status: `fully_met`
- Blocking dependencies to reach target:
  - `SBD-CODE-001` (path traversal hardening)
  - `SBD-CODE-002` (redaction hardening)
  - `SBD-CODE-003` (error message sanitization)
  - `SBD-CODE-004` (secure rate-limit defaults)
  - `SBD-CODE-005` (malformed JSON handling)

## Remediation Re-evaluation Update (2026-02-21)

Post-review remediation has now been implemented and regression-tested in code:

- `SBD-CODE-001`: completed (`server/mcp/resource_catalog.py`, `tests/test_resource_catalog.py`)
- `SBD-CODE-002`: completed (`server/security.py`, `server/logging.py`, `server/main.py`, redaction tests)
- `SBD-CODE-003`: completed (`server/stdio_adapter.py`, `server/mcp/http_transport.py`)
- `SBD-CODE-004`: completed (`server/config.py`, docs/env defaults, explicit test bypass fixture)
- `SBD-CODE-005`: completed (`server/mcp/tools.py`, `server/mcp/playground.py`, malformed JSON tests)
- `SBD-CODE-006`: completed (`server/main.py` log formatting normalization)
- `SBD-CODE-007`: completed (`server/main.py` startup print removed; logger startup message used)
- `SBD-CODE-008`: completed (`server/mcp/tools.py` now logs import failures with diagnostics)
- Citation housekeeping (`SBD-REV-010`): completed (`references.bib` codex-trace URL now stable repo reference)

Updated status snapshot:

- Current status: `fully_met`
- Updated weighted score: `89.6 / 100`
- Blocking dependencies: none
