# MCP Geo Unattended Client Evaluation
Generated: 2026-04-13T12:42:37Z
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
| Codex CLI | 8 | 7 | 0.70 | scored=7, startup_only=1 |
| Gemini CLI | 8 | 6 | 0.71 | runner_error=2, scored=6 |
| Claude Code CLI | 8 | 6 | 0.77 | runner_error=1, scored=6, startup_only=1 |
| VS Code Agent | 8 | 7 | 0.70 | scored=7, startup_only=1 |

## Capability Breakdown
| Track | Capability | Attempts | Scored | Average |
| --- | --- | ---: | ---: | ---: |
| Codex CLI | discovery_routing | 1 | 1 | 0.71 |
| Codex CLI | error_recovery | 1 | 1 | 0.71 |
| Codex CLI | live_os_lookup | 1 | 1 | 0.76 |
| Codex CLI | map_descriptor | 1 | 1 | 0.76 |
| Codex CLI | resource_consumption | 1 | 0 | n/a |
| Codex CLI | tool_discovery | 1 | 1 | 0.65 |
| Codex CLI | ui_fallback_or_runtime | 2 | 2 | 0.65 |
| Gemini CLI | discovery_routing | 1 | 1 | 0.74 |
| Gemini CLI | error_recovery | 1 | 0 | n/a |
| Gemini CLI | live_os_lookup | 1 | 1 | 0.80 |
| Gemini CLI | map_descriptor | 1 | 0 | n/a |
| Gemini CLI | resource_consumption | 1 | 1 | 0.63 |
| Gemini CLI | tool_discovery | 1 | 1 | 0.69 |
| Gemini CLI | ui_fallback_or_runtime | 2 | 2 | 0.71 |
| Claude Code CLI | discovery_routing | 1 | 1 | 0.78 |
| Claude Code CLI | error_recovery | 1 | 1 | 0.78 |
| Claude Code CLI | live_os_lookup | 1 | 1 | 0.84 |
| Claude Code CLI | map_descriptor | 1 | 1 | 0.78 |
| Claude Code CLI | resource_consumption | 1 | 0 | n/a |
| Claude Code CLI | tool_discovery | 1 | 1 | 0.73 |
| Claude Code CLI | ui_fallback_or_runtime | 2 | 1 | 0.73 |
| VS Code Agent | discovery_routing | 1 | 1 | 0.71 |
| VS Code Agent | error_recovery | 1 | 1 | 0.71 |
| VS Code Agent | live_os_lookup | 1 | 1 | 0.71 |
| VS Code Agent | map_descriptor | 1 | 1 | 0.71 |
| VS Code Agent | resource_consumption | 1 | 1 | 0.54 |
| VS Code Agent | tool_discovery | 1 | 0 | n/a |
| VS Code Agent | ui_fallback_or_runtime | 2 | 2 | 0.76 |

## Tool Family Summary
| Tool Family | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| admin_lookup | 4 | 3 | 0.73 | runner_error=1, scored=3 |
| discovery | 4 | 3 | 0.69 | scored=3, startup_only=1 |
| maps | 4 | 3 | 0.75 | runner_error=1, scored=3 |
| places | 4 | 4 | 0.78 | scored=4 |
| resources | 4 | 2 | 0.59 | scored=2, startup_only=2 |
| routing | 4 | 4 | 0.73 | scored=4 |
| ui | 8 | 7 | 0.71 | runner_error=1, scored=7 |

## Scenario Matrix
| Scenario | Codex CLI | Gemini CLI | Claude Code CLI | VS Code Agent |
| --- | --- | --- | --- | --- |
| Address lookup by postcode | scored (0.76) | scored (0.80) | scored (0.84) | scored (0.71) |
| Ambiguous routing prompt | scored (0.71) | scored (0.74) | scored (0.78) | scored (0.71) |
| Scoped discovery and tool search | scored (0.65) | scored (0.69) | scored (0.73) | startup_only<br>diagnostic=0.62 |
| Resource retrieval | startup_only<br>diagnostic=0.72 | scored (0.63) | startup_only<br>diagnostic=0.72 | scored (0.54) |
| Static map render | scored (0.76) | runner_error<br>scenario_tool_failure<br>diagnostic=0.74 | scored (0.78) | scored (0.71) |
| Geography selector widget | scored (0.65) | scored (0.73) | runner_error<br>scenario_tool_failure<br>diagnostic=0.73 | scored (0.76) |
| Boundary explorer widget | scored (0.65) | scored (0.69) | scored (0.73) | scored (0.76) |
| Failure and error recovery | scored (0.71) | runner_error<br>scenario_tool_failure<br>diagnostic=0.74 | scored (0.78) | scored (0.71) |

## Attempt Log
- `codex_cli` `readiness` `readiness_probe`: ready, diagnosticScore=0.82, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121358Z-codex-cli-readiness-probe
- `codex_cli` `capability` `address_lookup_postcode`: scored, score=0.76, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121425Z-codex-cli-address-lookup-postcode
- `codex_cli` `capability` `ambiguous_westminster_data`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121453Z-codex-cli-ambiguous-westminster-data
- `codex_cli` `capability` `tool_search_postcode`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121653Z-codex-cli-tool-search-postcode
- `codex_cli` `capability` `skills_guide_resource`: startup_only, diagnosticScore=0.72, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121739Z-codex-cli-skills-guide-resource
- `codex_cli` `capability` `static_map_render`: scored, score=0.76, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121836Z-codex-cli-static-map-render
- `codex_cli` `capability` `geography_selector_widget`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122031Z-codex-cli-geography-selector-widget
- `codex_cli` `capability` `boundary_explorer_widget`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122151Z-codex-cli-boundary-explorer-widget
- `codex_cli` `capability` `boundary_not_found_recovery`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122235Z-codex-cli-boundary-not-found-recovery
- `gemini_cli` `readiness` `readiness_probe`: ready, diagnosticScore=0.89, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122300Z-gemini-cli-readiness-probe
- `gemini_cli` `capability` `address_lookup_postcode`: scored, score=0.80, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122318Z-gemini-cli-address-lookup-postcode
- `gemini_cli` `capability` `ambiguous_westminster_data`: scored, score=0.74, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122334Z-gemini-cli-ambiguous-westminster-data
- `gemini_cli` `capability` `tool_search_postcode`: scored, score=0.69, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122441Z-gemini-cli-tool-search-postcode
- `gemini_cli` `capability` `skills_guide_resource`: scored, score=0.63, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122504Z-gemini-cli-skills-guide-resource
- `gemini_cli` `capability` `static_map_render`: runner_error, diagnosticScore=0.74, blocker=scenario_tool_failure, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122523Z-gemini-cli-static-map-render
- `gemini_cli` `capability` `geography_selector_widget`: scored, score=0.73, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122723Z-gemini-cli-geography-selector-widget
- `gemini_cli` `capability` `boundary_explorer_widget`: scored, score=0.69, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122739Z-gemini-cli-boundary-explorer-widget
- `gemini_cli` `capability` `boundary_not_found_recovery`: runner_error, diagnosticScore=0.74, blocker=scenario_tool_failure, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122756Z-gemini-cli-boundary-not-found-recovery
- `claude_cli` `readiness` `readiness_probe`: ready, diagnosticScore=0.89, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T122956Z-claude-cli-readiness-probe
- `claude_cli` `capability` `address_lookup_postcode`: scored, score=0.84, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123008Z-claude-cli-address-lookup-postcode
- `claude_cli` `capability` `ambiguous_westminster_data`: scored, score=0.78, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123018Z-claude-cli-ambiguous-westminster-data
- `claude_cli` `capability` `tool_search_postcode`: scored, score=0.73, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123100Z-claude-cli-tool-search-postcode
- `claude_cli` `capability` `skills_guide_resource`: startup_only, diagnosticScore=0.72, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123122Z-claude-cli-skills-guide-resource
- `claude_cli` `capability` `static_map_render`: scored, score=0.78, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123141Z-claude-cli-static-map-render
- `claude_cli` `capability` `geography_selector_widget`: runner_error, diagnosticScore=0.73, blocker=scenario_tool_failure, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123212Z-claude-cli-geography-selector-widget
- `claude_cli` `capability` `boundary_explorer_widget`: scored, score=0.73, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123342Z-claude-cli-boundary-explorer-widget
- `claude_cli` `capability` `boundary_not_found_recovery`: scored, score=0.78, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123405Z-claude-cli-boundary-not-found-recovery
- `vscode_ide` `readiness` `readiness_probe`: ready, diagnosticScore=0.82, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123424Z-vscode-ide-readiness-probe
- `vscode_ide` `capability` `address_lookup_postcode`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123525Z-vscode-ide-address-lookup-postcode
- `vscode_ide` `capability` `ambiguous_westminster_data`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123609Z-vscode-ide-ambiguous-westminster-data
- `vscode_ide` `capability` `tool_search_postcode`: startup_only, diagnosticScore=0.62, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123713Z-vscode-ide-tool-search-postcode
- `vscode_ide` `capability` `skills_guide_resource`: scored, score=0.54, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123809Z-vscode-ide-skills-guide-resource
- `vscode_ide` `capability` `static_map_render`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123855Z-vscode-ide-static-map-render
- `vscode_ide` `capability` `geography_selector_widget`: scored, score=0.76, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T123951Z-vscode-ide-geography-selector-widget
- `vscode_ide` `capability` `boundary_explorer_widget`: scored, score=0.76, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T124045Z-vscode-ide-boundary-explorer-widget
- `vscode_ide` `capability` `boundary_not_found_recovery`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T124139Z-vscode-ide-boundary-not-found-recovery
