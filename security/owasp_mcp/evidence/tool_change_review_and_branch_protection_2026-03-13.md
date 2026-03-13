# Tool Change Review and Branch Protection

Verified on 2026-03-13 for the strict OWASP MCP profile.

- `.github/CODEOWNERS` marks tool, runtime, workflow, and OWASP validation paths as code-owner protected.
- `security/owasp_mcp/evidence/github_main_branch_protection_2026-03-13.json` captures the live GitHub protection state for `main`, including required checks, stale-review dismissal, code-owner review enforcement, last-push approval, and conversation resolution.
- `.github/workflows/ci.yml` keeps the OWASP validator and supply-chain checks mandatory for protected branches.
- `security/owasp_mcp/tool_manifest.lock.json` and its detached signature provide a reviewable, signed record of the tool contract set.
