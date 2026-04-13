# MCP Geo Unattended Client Evaluation
Generated: 2026-04-13T12:01:04Z
Scenario pack: codex_vs_claude_host_v1

## Readiness Summary
| Track | Outcome | First Attempt | Final Attempt | Recovery | Live OS Ready | Config | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VS Code Agent | ready | ready | readiness | false | true | key=false, file=true, toolset=starter, include=ons_geo_lookup,property_tax,features_layers,landis_soils | none |

## Capability Summary
| Track | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| VS Code Agent | 1 | 0 | n/a | no_mcp_traffic=1 |

## Capability Breakdown
| Track | Capability | Attempts | Scored | Average |
| --- | --- | ---: | ---: | ---: |
| VS Code Agent | live_os_lookup | 1 | 0 | n/a |

## Tool Family Summary
| Tool Family | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| places | 1 | 0 | n/a | no_mcp_traffic=1 |

## Scenario Matrix
| Scenario | VS Code Agent |
| --- | --- |
| Address lookup by postcode | no_mcp_traffic<br>client_no_mcp_traffic<br>diagnostic=0.58 |
| Ambiguous routing prompt | missing |
| Scoped discovery and tool search | missing |
| Resource retrieval | missing |
| Static map render | missing |
| Geography selector widget | missing |
| Boundary explorer widget | missing |
| Failure and error recovery | missing |

## Attempt Log
- `vscode_ide` `readiness` `readiness_probe`: ready, diagnosticScore=0.69, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T115926Z-vscode-ide-readiness-probe
- `vscode_ide` `capability` `address_lookup_postcode`: no_mcp_traffic, diagnosticScore=0.58, blocker=client_no_mcp_traffic, session=/Users/crpage/repos/mcp-geo/logs/sessions/20260413T120003Z-vscode-ide-address-lookup-postcode
