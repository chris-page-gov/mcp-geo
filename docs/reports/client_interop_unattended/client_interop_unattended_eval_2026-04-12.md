# MCP Geo Unattended Client Evaluation
Generated: 2026-04-12T20:43:39Z
Scenario pack: codex_vs_claude_host_v1

## Track Summary
| Track | Attempts | Scored | Average | Statuses |
| --- | ---: | ---: | ---: | --- |
| Codex CLI | 8 | 7 | 0.70 | scored=7, startup_only=1 |
| Gemini CLI | 8 | 0 | n/a | runner_error=8 |
| Claude Code CLI | 8 | 0 | n/a | runner_error=8 |
| VS Code Agent | 8 | 4 | 0.54 | no_mcp_traffic=4, scored=4 |

## Scenario Matrix
| Scenario | Codex CLI | Gemini CLI | Claude Code CLI | VS Code Agent |
| --- | --- | --- | --- | --- |
| Address lookup by postcode | scored (0.82) | runner_error<br>gemini_cli_timeout_after_45s<br>diagnostic=0.58 | runner_error<br>claude_cli_failed<br>diagnostic=0.72 | no_mcp_traffic<br>client produced no MCP traffic<br>diagnostic=0.58 |
| Ambiguous routing prompt | scored (0.71) | runner_error<br>gemini_cli_timeout_after_45s<br>diagnostic=0.58 | runner_error<br>claude_cli_failed<br>diagnostic=0.72 | scored (0.58) |
| Scoped discovery and tool search | scored (0.65) | runner_error<br>gemini_cli_timeout_after_45s<br>diagnostic=0.52 | runner_error<br>claude_cli_failed<br>diagnostic=0.66 | scored (0.52) |
| Resource retrieval | startup_only<br>client initialized and listed capabilities but made no tool calls<br>diagnostic=0.72 | runner_error<br>gemini_cli_timeout_after_45s<br>diagnostic=0.47 | runner_error<br>claude_cli_failed<br>diagnostic=0.61 | no_mcp_traffic<br>client produced no MCP traffic<br>diagnostic=0.47 |
| Static map render | scored (0.73) | runner_error<br>gemini_cli_timeout_after_45s<br>diagnostic=0.58 | runner_error<br>claude_cli_failed<br>diagnostic=0.72 | no_mcp_traffic<br>client produced no MCP traffic<br>diagnostic=0.58 |
| Geography selector widget | scored (0.65) | runner_error<br>gemini_cli_timeout_after_45s<br>diagnostic=0.47 | runner_error<br>claude_cli_failed<br>diagnostic=0.61 | scored (0.63) |
| Boundary explorer widget | scored (0.65) | runner_error<br>gemini_cli_timeout_after_45s<br>diagnostic=0.47 | runner_error<br>claude_cli_failed<br>diagnostic=0.61 | scored (0.41) |
| Failure and error recovery | scored (0.71) | runner_error<br>gemini_cli_timeout_after_45s<br>diagnostic=0.58 | runner_error<br>claude_cli_failed<br>diagnostic=0.72 | no_mcp_traffic<br>client produced no MCP traffic<br>diagnostic=0.58 |

## Attempt Log
- `codex_cli` `address_lookup_postcode`: scored, score=0.82, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T201412Z-codex-cli-address-lookup-postcode
- `codex_cli` `ambiguous_westminster_data`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T201524Z-codex-cli-ambiguous-westminster-data
- `codex_cli` `tool_search_postcode`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T201646Z-codex-cli-tool-search-postcode
- `codex_cli` `skills_guide_resource`: startup_only, diagnosticScore=0.72, blocker=client initialized and listed capabilities but made no tool calls, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T201720Z-codex-cli-skills-guide-resource
- `codex_cli` `static_map_render`: scored, score=0.73, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T201802Z-codex-cli-static-map-render
- `codex_cli` `geography_selector_widget`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202000Z-codex-cli-geography-selector-widget
- `codex_cli` `boundary_explorer_widget`: scored, score=0.65, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202110Z-codex-cli-boundary-explorer-widget
- `codex_cli` `boundary_not_found_recovery`: scored, score=0.71, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202143Z-codex-cli-boundary-not-found-recovery
- `gemini_cli` `address_lookup_postcode`: runner_error, diagnosticScore=0.58, blocker=gemini_cli_timeout_after_45s, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202206Z-gemini-cli-address-lookup-postcode
- `gemini_cli` `ambiguous_westminster_data`: runner_error, diagnosticScore=0.58, blocker=gemini_cli_timeout_after_45s, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202253Z-gemini-cli-ambiguous-westminster-data
- `gemini_cli` `tool_search_postcode`: runner_error, diagnosticScore=0.52, blocker=gemini_cli_timeout_after_45s, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202339Z-gemini-cli-tool-search-postcode
- `gemini_cli` `skills_guide_resource`: runner_error, diagnosticScore=0.47, blocker=gemini_cli_timeout_after_45s, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202426Z-gemini-cli-skills-guide-resource
- `gemini_cli` `static_map_render`: runner_error, diagnosticScore=0.58, blocker=gemini_cli_timeout_after_45s, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202513Z-gemini-cli-static-map-render
- `gemini_cli` `geography_selector_widget`: runner_error, diagnosticScore=0.47, blocker=gemini_cli_timeout_after_45s, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202600Z-gemini-cli-geography-selector-widget
- `gemini_cli` `boundary_explorer_widget`: runner_error, diagnosticScore=0.47, blocker=gemini_cli_timeout_after_45s, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202647Z-gemini-cli-boundary-explorer-widget
- `gemini_cli` `boundary_not_found_recovery`: runner_error, diagnosticScore=0.58, blocker=gemini_cli_timeout_after_45s, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202733Z-gemini-cli-boundary-not-found-recovery
- `claude_cli` `address_lookup_postcode`: runner_error, diagnosticScore=0.72, blocker=claude_cli_failed, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202820Z-claude-cli-address-lookup-postcode
- `claude_cli` `ambiguous_westminster_data`: runner_error, diagnosticScore=0.72, blocker=claude_cli_failed, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202825Z-claude-cli-ambiguous-westminster-data
- `claude_cli` `tool_search_postcode`: runner_error, diagnosticScore=0.66, blocker=claude_cli_failed, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202829Z-claude-cli-tool-search-postcode
- `claude_cli` `skills_guide_resource`: runner_error, diagnosticScore=0.61, blocker=claude_cli_failed, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202834Z-claude-cli-skills-guide-resource
- `claude_cli` `static_map_render`: runner_error, diagnosticScore=0.72, blocker=claude_cli_failed, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202838Z-claude-cli-static-map-render
- `claude_cli` `geography_selector_widget`: runner_error, diagnosticScore=0.61, blocker=claude_cli_failed, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202843Z-claude-cli-geography-selector-widget
- `claude_cli` `boundary_explorer_widget`: runner_error, diagnosticScore=0.61, blocker=claude_cli_failed, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202847Z-claude-cli-boundary-explorer-widget
- `claude_cli` `boundary_not_found_recovery`: runner_error, diagnosticScore=0.72, blocker=claude_cli_failed, session=/Users/crpage/repos/mcp-geo/logs/sessions/client_interop_unattended_eval_20260412/20260412T202852Z-claude-cli-boundary-not-found-recovery
- `vscode_ide` `address_lookup_postcode`: no_mcp_traffic, diagnosticScore=0.58, blocker=client produced no MCP traffic, session=/Users/crpage/repos/mcp-geo/logs/sessions/vscode_full_refresh_20260412/20260412T203751Z-vscode-ide-address-lookup-postcode
- `vscode_ide` `ambiguous_westminster_data`: scored, score=0.58, session=/Users/crpage/repos/mcp-geo/logs/sessions/vscode_full_refresh_20260412/20260412T203842Z-vscode-ide-ambiguous-westminster-data
- `vscode_ide` `tool_search_postcode`: scored, score=0.52, session=/Users/crpage/repos/mcp-geo/logs/sessions/vscode_full_refresh_20260412/20260412T203855Z-vscode-ide-tool-search-postcode
- `vscode_ide` `skills_guide_resource`: no_mcp_traffic, diagnosticScore=0.47, blocker=client produced no MCP traffic, session=/Users/crpage/repos/mcp-geo/logs/sessions/vscode_full_refresh_20260412/20260412T203929Z-vscode-ide-skills-guide-resource
- `vscode_ide` `static_map_render`: no_mcp_traffic, diagnosticScore=0.58, blocker=client produced no MCP traffic, session=/Users/crpage/repos/mcp-geo/logs/sessions/vscode_full_refresh_20260412/20260412T204020Z-vscode-ide-static-map-render
- `vscode_ide` `geography_selector_widget`: scored, score=0.63, session=/Users/crpage/repos/mcp-geo/logs/sessions/vscode_full_refresh_20260412/20260412T204111Z-vscode-ide-geography-selector-widget
- `vscode_ide` `boundary_explorer_widget`: scored, score=0.41, session=/Users/crpage/repos/mcp-geo/logs/sessions/vscode_full_refresh_20260412/20260412T204159Z-vscode-ide-boundary-explorer-widget
- `vscode_ide` `boundary_not_found_recovery`: no_mcp_traffic, diagnosticScore=0.58, blocker=client produced no MCP traffic, session=/Users/crpage/repos/mcp-geo/logs/sessions/vscode_full_refresh_20260412/20260412T204225Z-vscode-ide-boundary-not-found-recovery
