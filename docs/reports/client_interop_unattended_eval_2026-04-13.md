# MCP Geo Unattended Client Evaluation
Generated: 2026-04-13T11:44:59Z
Scenario pack: codex_vs_claude_host_v1

## Readiness Summary
| Track | Outcome | First Attempt | Final Attempt | Recovery | Live OS Ready | Config | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex CLI | ready | ready | readiness | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | none |
| Gemini CLI | ready | ready | readiness | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | none |
| Claude Code CLI | ready | ready | readiness | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | none |
| VS Code Agent | ready | ready | readiness | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | none |

## Capability Summary
| Track | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| Codex CLI | 8 | 7 | 0.71 | scored=7, startup_only=1 |
| Gemini CLI | 8 | 8 | 0.74 | scored=8 |
| Claude Code CLI | 8 | 7 | 0.76 | scored=7, startup_only=1 |
| VS Code Agent | 8 | 0 | n/a | no_mcp_traffic=2, startup_only=6 |

## Capability Breakdown
| Track | Capability | Attempts | Scored | Average |
| --- | --- | ---: | ---: | ---: |
| Codex CLI | discovery_routing | 1 | 1 | 0.82 |
| Codex CLI | error_recovery | 1 | 1 | 0.71 |
| Codex CLI | live_os_lookup | 1 | 1 | 0.76 |
| Codex CLI | map_descriptor | 1 | 1 | 0.76 |
| Codex CLI | resource_consumption | 1 | 0 | n/a |
| Codex CLI | tool_discovery | 1 | 1 | 0.65 |
| Codex CLI | ui_fallback_or_runtime | 2 | 2 | 0.65 |
| Gemini CLI | discovery_routing | 1 | 1 | 0.74 |
| Gemini CLI | error_recovery | 1 | 1 | 0.86 |
| Gemini CLI | live_os_lookup | 1 | 1 | 0.80 |
| Gemini CLI | map_descriptor | 1 | 1 | 0.78 |
| Gemini CLI | resource_consumption | 1 | 1 | 0.63 |
| Gemini CLI | tool_discovery | 1 | 1 | 0.73 |
| Gemini CLI | ui_fallback_or_runtime | 2 | 2 | 0.69 |
| Claude Code CLI | discovery_routing | 1 | 1 | 0.78 |
| Claude Code CLI | error_recovery | 1 | 1 | 0.78 |
| Claude Code CLI | live_os_lookup | 1 | 1 | 0.84 |
| Claude Code CLI | map_descriptor | 1 | 1 | 0.78 |
| Claude Code CLI | resource_consumption | 1 | 0 | n/a |
| Claude Code CLI | tool_discovery | 1 | 1 | 0.73 |
| Claude Code CLI | ui_fallback_or_runtime | 2 | 2 | 0.71 |
| VS Code Agent | discovery_routing | 1 | 0 | n/a |
| VS Code Agent | error_recovery | 1 | 0 | n/a |
| VS Code Agent | live_os_lookup | 1 | 0 | n/a |
| VS Code Agent | map_descriptor | 1 | 0 | n/a |
| VS Code Agent | resource_consumption | 1 | 0 | n/a |
| VS Code Agent | tool_discovery | 1 | 0 | n/a |
| VS Code Agent | ui_fallback_or_runtime | 2 | 0 | n/a |

## Tool Family Summary
| Tool Family | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| admin_lookup | 4 | 3 | 0.78 | no_mcp_traffic=1, scored=3 |
| discovery | 4 | 3 | 0.70 | scored=3, startup_only=1 |
| maps | 4 | 3 | 0.78 | scored=3, startup_only=1 |
| places | 4 | 3 | 0.80 | scored=3, startup_only=1 |
| resources | 4 | 1 | 0.63 | no_mcp_traffic=1, scored=1, startup_only=2 |
| routing | 4 | 3 | 0.78 | scored=3, startup_only=1 |
| ui | 8 | 6 | 0.68 | scored=6, startup_only=2 |

## Scenario Matrix
| Scenario | Codex CLI | Gemini CLI | Claude Code CLI | VS Code Agent |
| --- | --- | --- | --- | --- |
| Address lookup by postcode | scored (0.76) | scored (0.80) | scored (0.84) | startup_only<br>diagnostic=0.68 |
| Ambiguous routing prompt | scored (0.82) | scored (0.74) | scored (0.78) | startup_only<br>diagnostic=0.68 |
| Scoped discovery and tool search | scored (0.65) | scored (0.73) | scored (0.73) | startup_only<br>diagnostic=0.62 |
| Resource retrieval | startup_only<br>diagnostic=0.72 | scored (0.63) | startup_only<br>diagnostic=0.72 | no_mcp_traffic<br>client_workspace_restriction<br>diagnostic=0.47 |
| Static map render | scored (0.76) | scored (0.78) | scored (0.78) | startup_only<br>diagnostic=0.68 |
| Geography selector widget | scored (0.65) | scored (0.69) | scored (0.73) | startup_only<br>diagnostic=0.46 |
| Boundary explorer widget | scored (0.65) | scored (0.69) | scored (0.69) | startup_only<br>diagnostic=0.46 |
| Failure and error recovery | scored (0.71) | scored (0.86) | scored (0.78) | no_mcp_traffic<br>client_workspace_restriction<br>diagnostic=0.58 |

## Attempt Log
- `codex_cli` `readiness` `readiness_probe`: ready, diagnosticScore=0.82, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112147Z-codex-cli-readiness-probe
- `codex_cli` `capability` `address_lookup_postcode`: scored, score=0.76, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112207Z-codex-cli-address-lookup-postcode
- `codex_cli` `capability` `ambiguous_westminster_data`: scored, score=0.82, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112236Z-codex-cli-ambiguous-westminster-data
- `codex_cli` `capability` `tool_search_postcode`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112411Z-codex-cli-tool-search-postcode
- `codex_cli` `capability` `skills_guide_resource`: startup_only, diagnosticScore=0.72, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112443Z-codex-cli-skills-guide-resource
- `codex_cli` `capability` `static_map_render`: scored, score=0.76, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112526Z-codex-cli-static-map-render
- `codex_cli` `capability` `geography_selector_widget`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112711Z-codex-cli-geography-selector-widget
- `codex_cli` `capability` `boundary_explorer_widget`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112820Z-codex-cli-boundary-explorer-widget
- `codex_cli` `capability` `boundary_not_found_recovery`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112847Z-codex-cli-boundary-not-found-recovery
- `gemini_cli` `readiness` `readiness_probe`: ready, diagnosticScore=0.86, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112920Z-gemini-cli-readiness-probe
- `gemini_cli` `capability` `address_lookup_postcode`: scored, score=0.80, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112941Z-gemini-cli-address-lookup-postcode
- `gemini_cli` `capability` `ambiguous_westminster_data`: scored, score=0.74, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T112957Z-gemini-cli-ambiguous-westminster-data
- `gemini_cli` `capability` `tool_search_postcode`: scored, score=0.73, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113033Z-gemini-cli-tool-search-postcode
- `gemini_cli` `capability` `skills_guide_resource`: scored, score=0.63, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113049Z-gemini-cli-skills-guide-resource
- `gemini_cli` `capability` `static_map_render`: scored, score=0.78, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113112Z-gemini-cli-static-map-render
- `gemini_cli` `capability` `geography_selector_widget`: scored, score=0.69, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113244Z-gemini-cli-geography-selector-widget
- `gemini_cli` `capability` `boundary_explorer_widget`: scored, score=0.69, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113306Z-gemini-cli-boundary-explorer-widget
- `gemini_cli` `capability` `boundary_not_found_recovery`: scored, score=0.86, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113323Z-gemini-cli-boundary-not-found-recovery
- `claude_cli` `readiness` `readiness_probe`: ready, diagnosticScore=0.89, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113437Z-claude-cli-readiness-probe
- `claude_cli` `capability` `address_lookup_postcode`: scored, score=0.84, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113449Z-claude-cli-address-lookup-postcode
- `claude_cli` `capability` `ambiguous_westminster_data`: scored, score=0.78, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113458Z-claude-cli-ambiguous-westminster-data
- `claude_cli` `capability` `tool_search_postcode`: scored, score=0.73, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113532Z-claude-cli-tool-search-postcode
- `claude_cli` `capability` `skills_guide_resource`: startup_only, diagnosticScore=0.72, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113550Z-claude-cli-skills-guide-resource
- `claude_cli` `capability` `static_map_render`: scored, score=0.78, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113613Z-claude-cli-static-map-render
- `claude_cli` `capability` `geography_selector_widget`: scored, score=0.73, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113645Z-claude-cli-geography-selector-widget
- `claude_cli` `capability` `boundary_explorer_widget`: scored, score=0.69, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113723Z-claude-cli-boundary-explorer-widget
- `claude_cli` `capability` `boundary_not_found_recovery`: scored, score=0.78, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113840Z-claude-cli-boundary-not-found-recovery
- `vscode_ide` `readiness` `readiness_probe`: ready, diagnosticScore=0.86, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113856Z-vscode-ide-readiness-probe
- `vscode_ide` `capability` `address_lookup_postcode`: startup_only, diagnosticScore=0.68, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113924Z-vscode-ide-address-lookup-postcode
- `vscode_ide` `capability` `ambiguous_westminster_data`: startup_only, diagnosticScore=0.68, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T113947Z-vscode-ide-ambiguous-westminster-data
- `vscode_ide` `capability` `tool_search_postcode`: startup_only, diagnosticScore=0.62, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T114010Z-vscode-ide-tool-search-postcode
- `vscode_ide` `capability` `skills_guide_resource`: no_mcp_traffic, diagnosticScore=0.47, blocker=client_workspace_restriction, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T114033Z-vscode-ide-skills-guide-resource
- `vscode_ide` `capability` `static_map_render`: startup_only, diagnosticScore=0.68, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T114217Z-vscode-ide-static-map-render
- `vscode_ide` `capability` `geography_selector_widget`: startup_only, diagnosticScore=0.46, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T114250Z-vscode-ide-geography-selector-widget
- `vscode_ide` `capability` `boundary_explorer_widget`: startup_only, diagnosticScore=0.46, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T114307Z-vscode-ide-boundary-explorer-widget
- `vscode_ide` `capability` `boundary_not_found_recovery`: no_mcp_traffic, diagnosticScore=0.58, blocker=client_workspace_restriction, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T114324Z-vscode-ide-boundary-not-found-recovery
