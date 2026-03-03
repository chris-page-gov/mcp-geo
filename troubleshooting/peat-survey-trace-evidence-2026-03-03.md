# Peat Survey Trace Evidence (2026-03-03)

- Source conversation: `docs/MCP-Geo Peatland Site Survey - Forest of Bowland National Landscape.md`
- Source transport trace: `logs/claude-trace.jsonl`
- Scope: Forest of Bowland peatland survey run where Claude reported proxy/hydrology counts and then failed on a path/road collection query.

## Conversation Evidence (Markdown Trace)

1. Query plans emitted by `os_peat_evidence_paths` recommend `resultType: "hits"` for proxy layers:
- `wtr-fts-water-3` and `lnd-fts-land-3`
- Evidence: `docs/MCP-Geo Peatland Site Survey - Forest of Bowland National Landscape.md:124`

2. First hydrology `hits` query returns `count: 0`, `numberMatched: null`, `numberReturned: 0`:
- Evidence: `docs/MCP-Geo Peatland Site Survey - Forest of Bowland National Landscape.md:142` and `:146`

3. Immediately afterwards, the same AOI/collection with `resultType: "results"` returns `count: 25` and 25 sampled features:
- Evidence: `docs/MCP-Geo Peatland Site Survey - Forest of Bowland National Landscape.md:156` and `:160`

4. Claude then calls unsupported collection `trn-fts-roadlink-1` and gets `OS_API_ERROR` 404:
- Request evidence: `docs/MCP-Geo Peatland Site Survey - Forest of Bowland National Landscape.md:232`
- Error evidence: `docs/MCP-Geo Peatland Site Survey - Forest of Bowland National Landscape.md:236`

5. Recovery was manual by calling `os_features.collections` with `q: "path"`:
- Evidence: `docs/MCP-Geo Peatland Site Survey - Forest of Bowland National Landscape.md:242` and `:250`

## Transport Evidence (JSONL)

### Request/response timeline (server-side)

- `id=18` landscape lookup succeeded (`status=200`) at `ts=1772572922.6809542`.
  - Trace line: `logs/claude-trace.jsonl:4826`
- `id=19` landscape geometry succeeded (`status=200`) at `ts=1772572927.3868039`.
  - Trace line: `logs/claude-trace.jsonl:4828`
- `id=20` peat layer catalog succeeded (`status=200`) at `ts=1772573028.5305269`.
  - Trace line: `logs/claude-trace.jsonl:4830`
- `id=21` peat evidence paths succeeded (`status=200`) at `ts=1772573119.872554`.
  - Trace line: `logs/claude-trace.jsonl:4832`
- `id=22` `os_features_query` for `wtr-fts-water-3` (`resultType=hits`) returned:
  - `status=200`, `count=0`, `numberMatched=null`, `numberReturned=0`
  - Trace line: `logs/claude-trace.jsonl:4834`
- `id=23` `os_features_query` for same collection/AOI (`resultType=results`) returned:
  - `status=200`, `count=25`, `numberMatched=null`, `numberReturned=25`
  - Trace line: `logs/claude-trace.jsonl:4836`
- `id=24` `os_features_query` for `lnd-fts-land-3` succeeded (`count=50`).
  - Trace line: `logs/claude-trace.jsonl:4838`
- `id=25` `os_features_query` with `collection=trn-fts-roadlink-1` failed:
  - `status=501`, `code=OS_API_ERROR`, upstream description says unsupported collection (404)
  - Request trace line: `logs/claude-trace.jsonl:4839`
  - Response trace line: `logs/claude-trace.jsonl:4841`
- `id=26` `os_features_collections` recovery call succeeded (`status=200`, `count=21`).
  - Trace line: `logs/claude-trace.jsonl:4843`

## Evidence Summary

- Two user-visible failures occurred in one chain:
1. Misleading `hits` result (`count=0` while `results` immediately returned 25 for the same query intent).
2. Unsupported collection id usage (`trn-fts-roadlink-1`) with no server-side compatibility alias and no structured suggestions in the returned error payload.
