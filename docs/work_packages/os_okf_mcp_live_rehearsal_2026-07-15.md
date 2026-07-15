# OS OKF + MCP live rehearsal evidence

Observed: 15 July 2026, 08:08 BST<br>
Scenario: Explorer House postcode `SO16 0AS`<br>
Purpose: meeting readiness evidence, not a durable data snapshot

## Credential boundary

The local server was started with `OS_API_KEY_FILE=$HOME/.secrets/os_api_key`. The browser,
generated OKF files, request arguments and this log contain no key value. The server read the
file at startup and made the upstream calls.

## Results

| Step | Result | Evidence retained |
| --- | --- | --- |
| OS Light basemap | HTTP 200 style response; real browser displayed `OS Vector Tile API light basemap`; no page errors or failed requests during the check | Status and browser observation only; the local screenshot is not published |
| Places by postcode | HTTP 200; one address record returned | Count only; the returned UPRN and coordinate were used in memory and not written here |
| Current NGD collection discovery | HTTP 200; 17 filtered collection records and nine version mappings returned | Selected current building collection: `bld-fts-building-4` |
| Bounded NGD building query | HTTP 200; 12 features returned and all 12 carried geometry | Count only; bbox was derived from the returned Places coordinate |
| Linked Identifiers | HTTP 200; live object response containing `correlations` and `linkedIdentifier` groups | Shape and group names only; no returned identifier value retained |
| Generated OKF binding over MCP HTTP | Initialize HTTP 200 with a session; generated `os_places.by_postcode` request HTTP 200; response ID matched; one address returned from `os_places` | Protocol/status/count evidence only |

## Interpretation

This validates the complete meeting claim: the checked-in OKF binding can be discovered without a
credential and then executed over MCP using a credential held by MCP Geo. It also validates the
live Places → current NGD collection → nearby geometry → Linked Identifiers chain.

The evidence does **not** assert that the returned addressable object and any particular building
feature are the same real-world object. The building query means “features near the returned
address point”; only an authoritative relationship returned by OS should establish a direct join.

Counts and the current collection version are time-sensitive. Repeat the rehearsal before using
them in a later presentation.
