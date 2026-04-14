# MCP Geo Unattended Client Evaluation
Generated: 2026-04-13T08:46:27Z
Scenario pack: codex_vs_claude_host_v1

## Readiness Summary
| Track | Outcome | First Attempt | Final Attempt | Recovery | Live OS Ready | Config | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex CLI | ready | ready | readiness | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | none |
| Gemini CLI | not_ready | not_ready | recovery | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | client_no_mcp_traffic |
| Claude Code CLI | ready | ready | readiness | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | none |
| VS Code Agent | not_ready | not_ready | recovery | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | client_no_mcp_traffic |

## Attempt Log
- `codex_cli` `readiness` `readiness_probe`: ready, diagnosticScore=0.82, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T084159Z-codex-cli-readiness-probe
- `gemini_cli` `readiness` `readiness_probe`: not_ready, diagnosticScore=0.58, blocker=client_launch_failure, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T084217Z-gemini-cli-readiness-probe
- `gemini_cli` `recovery` `readiness_probe`: not_ready, diagnosticScore=0.58, blocker=client_no_mcp_traffic, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T084349Z-gemini-cli-readiness-probe
- `claude_cli` `readiness` `readiness_probe`: ready, diagnosticScore=0.86, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T084429Z-claude-cli-readiness-probe
- `vscode_ide` `readiness` `readiness_probe`: not_ready, diagnosticScore=0.58, blocker=client_no_mcp_traffic, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T084444Z-vscode-ide-readiness-probe
- `vscode_ide` `recovery` `readiness_probe`: not_ready, diagnosticScore=0.58, blocker=client_no_mcp_traffic, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T084535Z-vscode-ide-readiness-probe
