# MCP Geo Unattended Client Evaluation
Generated: 2026-04-13T12:13:45Z
Scenario pack: codex_vs_claude_host_v1

## Readiness Summary
| Track | Outcome | First Attempt | Final Attempt | Recovery | Live OS Ready | Config | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VS Code Agent | ready | ready | readiness | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | none |

## Capability Summary
| Track | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| VS Code Agent | 8 | 8 | 0.68 | scored=8 |

## Capability Breakdown
| Track | Capability | Attempts | Scored | Average |
| --- | --- | ---: | ---: | ---: |
| VS Code Agent | discovery_routing | 1 | 1 | 0.65 |
| VS Code Agent | error_recovery | 1 | 1 | 0.68 |
| VS Code Agent | live_os_lookup | 1 | 1 | 0.71 |
| VS Code Agent | map_descriptor | 1 | 1 | 0.71 |
| VS Code Agent | resource_consumption | 1 | 1 | 0.54 |
| VS Code Agent | tool_discovery | 1 | 1 | 0.65 |
| VS Code Agent | ui_fallback_or_runtime | 2 | 2 | 0.76 |

## Tool Family Summary
| Tool Family | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| admin_lookup | 1 | 1 | 0.68 | scored=1 |
| discovery | 1 | 1 | 0.65 | scored=1 |
| maps | 1 | 1 | 0.71 | scored=1 |
| places | 1 | 1 | 0.71 | scored=1 |
| resources | 1 | 1 | 0.54 | scored=1 |
| routing | 1 | 1 | 0.65 | scored=1 |
| ui | 2 | 2 | 0.76 | scored=2 |

## Scenario Matrix
| Scenario | VS Code Agent |
| --- | --- |
| Address lookup by postcode | scored (0.71) |
| Ambiguous routing prompt | scored (0.65) |
| Scoped discovery and tool search | scored (0.65) |
| Resource retrieval | scored (0.54) |
| Static map render | scored (0.71) |
| Geography selector widget | scored (0.76) |
| Boundary explorer widget | scored (0.76) |
| Failure and error recovery | scored (0.68) |

## Attempt Log
- `vscode_ide` `readiness` `readiness_probe`: ready, diagnosticScore=0.82, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T120625Z-vscode-ide-readiness-probe
- `vscode_ide` `capability` `address_lookup_postcode`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T120703Z-vscode-ide-address-lookup-postcode
- `vscode_ide` `capability` `ambiguous_westminster_data`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T120747Z-vscode-ide-ambiguous-westminster-data
- `vscode_ide` `capability` `tool_search_postcode`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T120831Z-vscode-ide-tool-search-postcode
- `vscode_ide` `capability` `skills_guide_resource`: scored, score=0.54, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T120924Z-vscode-ide-skills-guide-resource
- `vscode_ide` `capability` `static_map_render`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121020Z-vscode-ide-static-map-render
- `vscode_ide` `capability` `geography_selector_widget`: scored, score=0.76, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121110Z-vscode-ide-geography-selector-widget
- `vscode_ide` `capability` `boundary_explorer_widget`: scored, score=0.76, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121206Z-vscode-ide-boundary-explorer-widget
- `vscode_ide` `capability` `boundary_not_found_recovery`: scored, score=0.68, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T121243Z-vscode-ide-boundary-not-found-recovery
