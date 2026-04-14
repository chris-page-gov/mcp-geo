# Obsidian Agent Control Smoke Evidence

Date:
Operator:
Branch:
Commit:

## Environment

- Obsidian app version:
- CLI enabled:
- `python3 scripts/validate_agent_control.py --skip-cli`:
- `python3 scripts/validate_agent_control.py`:

## Modes

| Mode | Switch command | Validation result | Notes |
| --- | --- | --- | --- |
| classic | `python3 scripts/switch_agent_mode.py --mode classic` |  |  |
| obsidian | `python3 scripts/switch_agent_mode.py --mode obsidian` |  |  |

## Scenario Results

### active_profile_discovery

| Client | Mode | Pass/Fail | First read surface | Notes |
| --- | --- | --- | --- | --- |
| Codex | classic |  |  |  |
| Codex | obsidian |  |  |  |
| Claude | classic |  |  |  |
| Claude | obsidian |  |  |  |
| Gemini | classic |  |  |  |
| Gemini | obsidian |  |  |  |
| VS Code | classic |  |  |  |
| VS Code | obsidian |  |  |  |

### current_focus_lookup

| Client | Mode | Pass/Fail | First read surface | Notes |
| --- | --- | --- | --- | --- |
| Codex | classic |  |  |  |
| Codex | obsidian |  |  |  |
| Claude | classic |  |  |  |
| Claude | obsidian |  |  |  |
| Gemini | classic |  |  |  |
| Gemini | obsidian |  |  |  |
| VS Code | classic |  |  |  |
| VS Code | obsidian |  |  |  |

### work_queue_lookup

| Client | Mode | Pass/Fail | First read surface | Notes |
| --- | --- | --- | --- | --- |
| Codex | classic |  |  |  |
| Codex | obsidian |  |  |  |
| Claude | classic |  |  |  |
| Claude | obsidian |  |  |  |
| Gemini | classic |  |  |  |
| Gemini | obsidian |  |  |  |
| VS Code | classic |  |  |  |
| VS Code | obsidian |  |  |  |

### repo_navigation_lookup

| Client | Mode | Pass/Fail | First read surface | Notes |
| --- | --- | --- | --- | --- |
| Codex | classic |  |  |  |
| Codex | obsidian |  |  |  |
| Claude | classic |  |  |  |
| Claude | obsidian |  |  |  |
| Gemini | classic |  |  |  |
| Gemini | obsidian |  |  |  |
| VS Code | classic |  |  |  |
| VS Code | obsidian |  |  |  |

### update_discipline_behavior

| Client | Mode | Pass/Fail | First read surface | Notes |
| --- | --- | --- | --- | --- |
| Codex | classic |  |  |  |
| Codex | obsidian |  |  |  |
| Claude | classic |  |  |  |
| Claude | obsidian |  |  |  |
| Gemini | classic |  |  |  |
| Gemini | obsidian |  |  |  |
| VS Code | classic |  |  |  |
| VS Code | obsidian |  |  |  |

### guardrail_adherence

| Client | Mode | Pass/Fail | First read surface | Notes |
| --- | --- | --- | --- | --- |
| Codex | classic |  |  |  |
| Codex | obsidian |  |  |  |
| Claude | classic |  |  |  |
| Claude | obsidian |  |  |  |
| Gemini | classic |  |  |  |
| Gemini | obsidian |  |  |  |
| VS Code | classic |  |  |  |
| VS Code | obsidian |  |  |  |

## Summary

- Strongest client in classic mode:
- Strongest client in obsidian mode:
- Common failure pattern:
- Any unexpected edits or guardrail violations:

## Cleanup

- Restored classic mode:
- Final validation command:
