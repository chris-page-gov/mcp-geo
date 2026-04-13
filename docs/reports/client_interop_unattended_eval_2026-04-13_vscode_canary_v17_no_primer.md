# MCP Geo Unattended Client Evaluation
Generated: 2026-04-13T12:06:13Z
Scenario pack: codex_vs_claude_host_v1

## Readiness Summary
| Track | Outcome | First Attempt | Final Attempt | Recovery | Live OS Ready | Config | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VS Code Agent | ready | ready | readiness | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | none |

## Capability Summary
| Track | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| VS Code Agent | 1 | 1 | 0.71 | scored=1 |

## Capability Breakdown
| Track | Capability | Attempts | Scored | Average |
| --- | --- | ---: | ---: | ---: |
| VS Code Agent | live_os_lookup | 1 | 1 | 0.71 |

## Tool Family Summary
| Tool Family | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| places | 1 | 1 | 0.71 | scored=1 |

## Scenario Matrix
| Scenario | VS Code Agent |
| --- | --- |
| Address lookup by postcode | scored (0.71) |
| Ambiguous routing prompt | missing |
| Scoped discovery and tool search | missing |
| Resource retrieval | missing |
| Static map render | missing |
| Geography selector widget | missing |
| Boundary explorer widget | missing |
| Failure and error recovery | missing |

## Attempt Log
- `vscode_ide` `readiness` `readiness_probe`: ready, diagnosticScore=0.86, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T120458Z-vscode-ide-readiness-probe
- `vscode_ide` `capability` `address_lookup_postcode`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T120531Z-vscode-ide-address-lookup-postcode
