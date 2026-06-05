# LLM-Wiki Conversation Postmortem Workflow

This workflow makes the MCP-Geo conversation postmortem repeatable across repos.
It follows the pattern used for the `ai-engineering-lab-hackathon-london-2026`
postmortem, but separates private source handling from public publication.

## Directory Contract

- `postmortem/` is private and gitignored. It can contain raw transcript
  exports, local JSONL paths, candidate inventories, hashes, and working notes.
- `postmortem-public/` is tracked and publishable. It contains redacted
  derivatives: index pages, source notes, start-to-finish readers, exchange
  notes, decision registers, repository evidence, and machine-readable
  registers.

## Stage 1: Candidate Discovery

Run the inventory script from the repository root:

```bash
python3 scripts/llm_wiki_postmortem_inventory.py
```

The script scans local Codex rollout logs under `$CODEX_HOME/sessions` or
`~/.codex/sessions`, filters sessions that match the current repository, and
writes private inventories under `postmortem/candidates/`.

The inventory is sorted newest first and includes:

- session ID and start timestamp
- title inferred from the first real user prompt
- kind (`interactive`, `automation`, `review`, or `github_workflow`)
- visible message counts
- visible-character and token estimates
- tool-call counts
- curation effort band
- source JSONL path and SHA-256

It also writes a repeated-session rollup:

- scheduled automations grouped across the full observed time span
- retry batches grouped by repeated harness prompts inside a time window
- short status/check-monitoring runs grouped by repeated prompt signatures
- summed tokens, messages, tool calls, line counts, and byte counts

The default non-automation repeat window is six hours. Tune it when needed:

```bash
python3 scripts/llm_wiki_postmortem_inventory.py --repeat-window-hours 12
```

Use the rollup first when selecting sessions. Repetition-heavy rows should
usually become one compact wiki summary rather than dozens of standalone
exchange pages, for example:

| Type | Label | Time span | Sessions | Tokens |
|---|---|---|---:|---:|
| Automation | Daily bug scan | first observed -> last observed | 71 | 391,776 |

Effort bands are triage estimates, not guarantees:

| Band | Meaning |
|---|---|
| `tiny` | About 15-30 min; one to three exchanges. |
| `small` | About 30-60 min; short focused session. |
| `medium` | About 1-2 h; multiple exchanges or moderate tool use. |
| `large` | About 2-4 h; lengthy curation and redaction. |
| `very_large` | More than 4 h or split first. |

## Stage 2: Promotion To The Wiki

Promote only selected candidates. For each selected session:

1. Copy or summarize source evidence into private `postmortem/`.
2. Create or update `postmortem-public/wiki/sources/`.
3. Add standalone exchange notes under `postmortem-public/wiki/exchanges/`.
4. Add or update the start-to-finish reader under
   `postmortem-public/wiki/readers/`.
5. Update `postmortem-public/wiki/index.md`, `conversation-summary.md`,
   `decisions.md`, `repository-evidence.md`, and JSON registers.
6. Run publication checks before committing.

For unreliable connectivity or long-running curation, run Stage 2 as a
restartable task:

- keep private checkpoint state under gitignored `postmortem/stage2/`
- use public JSON registers as the visible status source
- process one planned conversation or one capture per run
- update checkpoint state only after public pages and validation checks complete
- make every run safe to repeat by checking whether target files already exist
  and whether the capture status is already complete

Minimum publication checks:

```bash
jq -e type postmortem-public/wiki/data/*.json
python3 -c 'import pathlib,re,urllib.parse,sys; bad=[]; root=pathlib.Path("postmortem-public/wiki"); pat=re.compile(r"\\[[^\\]]+\\]\\(([^)]+)\\)");\
for p in root.rglob("*.md"):\
    text=p.read_text();\
    for m in pat.finditer(text):\
        target=m.group(1).strip();\
        if target.startswith(("http://","https://","mailto:","#")): continue;\
        path=target.split("#",1)[0];\
        if path and not (p.parent / urllib.parse.unquote(path)).resolve().exists(): bad.append(f"{p}:{target}");\
print("broken_links=" + str(len(bad))); print("\\n".join(bad)); sys.exit(1 if bad else 0)'
git diff --check
```

## Publication Boundary

Public pages must not include API keys, tokens, browser session material, full
local secret-file paths, or raw private transcript paths. Use placeholders such
as `[LOCAL_PATH]`, `[EXTSSD_DATA_PATH]`, `[LOCAL_SECRET_FILE]`, and
`[PORTAL_ACCOUNT]` where operational context matters.

Raw private logs can be retained locally under `postmortem/`, but public pages
should cite hashes and durable repo artifacts instead of publishing raw logs by
default.
