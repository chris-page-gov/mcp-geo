# MCP Geo Examples

## Tool Invocation Payloads

```
POST /tools/call
{ "tool": "os_places.by_postcode", "postcode": "SW1A1AA" }

POST /tools/call
{ "tool": "os_places.search", "text": "10 Downing Street" }

POST /tools/call
{ "tool": "os_names.find", "text": "Downing" }

POST /tools/call
{ "tool": "os_names.nearest", "lat": 51.5034, "lon": -0.1276 }

POST /tools/call
{ "tool": "os_places.nearest", "lat": 51.5034, "lon": -0.1276 }

POST /tools/call
{ "tool": "os_places.within", "bbox": [-0.14, 51.50, -0.12, 51.51] }

POST /tools/call
{ "tool": "os_features.query", "collection": "buildings", "bbox": [-0.14,51.50,-0.12,51.51] }

POST /tools/call
{ "tool": "os_linked_ids.get", "identifier": "100021892956" }
```

## Error Examples

```
{ "tool": "os_places.by_postcode" }
-> 400 INVALID_INPUT (missing postcode)

{ "tool": "os_names.nearest", "lat": "abc", "lon": 1 }
-> 400 INVALID_INPUT (lat/lon must be numeric)

{ "tool": "os_places.by_postcode", "postcode": "ZZ99ZZ" }
-> 400 INVALID_INPUT (invalid postcode format)
```

## Conversation Snippets

### 1. UPRNs for a Postcode
User: List addresses for SW1A 1AA.
Assistant (internal): call os_places.by_postcode { postcode: "SW1A1AA" }
Assistant: Returns N UPRNs with addresses.

### 2. Nearest Named Feature then Addresses
User: What named features and addresses are near 51.5034,-0.1276?
Assistant (internal sequence):
1. os_names.nearest { lat: 51.5034, lon: -0.1276 }
2. os_places.nearest { lat: 51.5034, lon: -0.1276 }
Assistant: Summarize top names + count of addresses.

### 3. Features by BBox
User: Show building feature IDs in small Westminster box.
Assistant (internal): os_features.query { collection: "buildings", bbox: [...] }
Assistant: Lists feature IDs and geometry types.

### 4. Linked Identifiers
User: Given this UPRN 100021892956 what other IDs exist?
Assistant (internal): os_linked_ids.get { identifier: "100021892956" }
Assistant: Presents related USRNs / TOIDs if present.

## Pattern Guidance
- Normalize postcode (strip spaces, uppercase) before calling.
- Use nearest tools only when both lat & lon present.
- Summaries: list top 5 results; mention total count when >5.
- Chain: find geometry (features / coordinates) first, then overlay other data.

## Golden Test Philosophy
Golden tests provide deterministic inputs + mocked upstream responses verifying schema stability and transformation logic. They SHOULD NOT hit live OS APIs.

