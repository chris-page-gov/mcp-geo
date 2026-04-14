# Obsidian Agent Control Smoke Pack

This runbook evaluates the switchable agent-control plane without using the
unattended capability harness. It compares the same six prompts across the two
profiles:

- `classic`: current root-file-driven behavior
- `obsidian`: root files rewritten as adapters into
  `Obsidian/MCP Geo Agent Control/`

The canonical scenario pack is:

- `docs/benchmarking/obsidian_agent_control_smoke_pack_v1.json`

Use the evidence template at:

- `docs/benchmarking/obsidian_agent_control_smoke_evidence_template.md`

## Preconditions

1. Start on a clean working tree for the tracked files involved in mode
   switching.
2. Confirm the current branch/commit you want to evaluate.
3. Make sure the control vault is current:

   ```bash
   python3 scripts/build_agent_control_vault.py
   ```

4. Validate the control vault itself:

   ```bash
   python3 scripts/validate_agent_control.py --skip-cli
   ```

5. If Obsidian is effectively running `1.12.7+` and CLI is enabled, run the full
   preflight as well:

   ```bash
   python3 scripts/validate_agent_control.py
   ```

   If the local shell still cannot run the CLI, record the expected
   prerequisite failure such as `OBSIDIAN_CLI_NOT_REGISTERED` or
   `OBSIDIAN_CLI_BUNDLE_MISSING` in the evidence notes.

## Mode Procedure

### Classic mode

1. Restore the tracked baseline:

   ```bash
   python3 scripts/switch_agent_mode.py --mode classic
   ```

2. Validate the restored profile:

   ```bash
   python3 scripts/validate_agent_control.py --skip-cli
   ```

3. Run every scenario from
   `docs/benchmarking/obsidian_agent_control_smoke_pack_v1.json` against each
   target client:
   - Codex
   - Claude
   - Gemini
   - VS Code

4. Record results in the evidence template before moving to the next mode.

### Obsidian mode

1. Switch the working tree:

   ```bash
   python3 scripts/switch_agent_mode.py --mode obsidian
   ```

2. Validate the switched profile:

   ```bash
   python3 scripts/validate_agent_control.py --skip-cli
   ```

3. If the local Obsidian CLI is expected to work, also run:

   ```bash
   python3 scripts/validate_agent_control.py
   ```

4. Run the same six scenarios against the same four clients.
5. Record the first read surface, the path taken through the control notes, and
   any unnecessary drift into large legacy trackers.

## Expected evidence to capture

- Active branch and commit
- Whether the repo was in `classic` or `obsidian` mode
- Result of `python3 scripts/validate_agent_control.py --skip-cli`
- Result of the full CLI preflight when attempted
- Per-client answers for each scenario
- Whether the client respected the intended smallest read path
- Whether the client touched protected/non-default targets such as `.obsidian/`
  or generated notes

## Cleanup

Always restore the tracked baseline after the `obsidian` run:

```bash
python3 scripts/switch_agent_mode.py --mode classic
python3 scripts/validate_agent_control.py --skip-cli
```

The local mode manifest lives at `data/agent_control/active_mode.json` and is
ignored. The committed branch baseline stays in `classic` mode.
