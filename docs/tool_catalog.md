# Tool Catalog

Auto-generated list of current tools, their descriptions, versions, and JSON Schemas.

## Map delivery contracts (compatibility baseline)

For map workflows, treat `os_maps.render` as the canonical baseline and apply
fallbacks in this order:

1. `map_card`
2. `overlay_bundle`
3. `export_handoff`

Contract definitions and conformance checklist:

- `docs/spec_package/06_api_contracts.md`
- `docs/spec_package/06a_map_delivery_fallback_contracts.md`
- `docs/map_delivery_support_matrix.md`

| Tool | Version | Description |
|------|---------|-------------|
| admin_lookup.area_geometry | 0.1.0 | Return bbox geometry for a given area id |
| admin_lookup.containing_areas | 0.1.0 | Return containing administrative areas for a point (lat/lon) |
| admin_lookup.find_by_name | 0.1.0 | Substring case-insensitive search by area name |
| admin_lookup.get_cache_status | 0.1.0 | Return boundary cache status (levels, datasets, counts). |
| admin_lookup.reverse_hierarchy | 0.1.0 | Return ancestor chain for a given area id |
| admin_lookup.search_cache | 0.1.0 | Search the boundary cache by id/name/level. |
| nomis.codelists | 0.1.0 | List NOMIS codelists or return a codelist definition. |
| nomis.concepts | 0.1.0 | List NOMIS concepts or return a concept definition. |
| nomis.datasets | 0.1.0 | List NOMIS datasets (filtered and limited summary by default), or return a dataset definition. |
| nomis.query | 0.1.0 | Query NOMIS datasets (JSON-stat or SDMX JSON). |
| ons_codes.list | 0.1.0 | List available ONS dimensions for a live dataset version. |
| ons_codes.options | 0.1.0 | List codes/options for a given ONS live dimension. |
| ons_data.create_filter | 0.1.0 | Create a filter for live ONS observations. Returns filterId. |
| ons_data.dimensions | 0.1.0 | List available ONS observation dimensions from the live API. |
| ons_data.editions | 0.1.0 | List live editions for an ONS dataset. |
| ons_data.get_filter_output | 0.1.0 | Retrieve data for a previously created filter (formats: JSON, CSV, XLSX). |
| ons_data.get_observation | 0.1.0 | Fetch a single observation by geography, measure, time from the live ONS API. |
| ons_data.query | 0.1.0 | Query live ONS observations (dataset/edition/version or search term). |
| ons_data.versions | 0.1.0 | List live versions for an ONS dataset edition. |
| ons_search.query | 0.1.0 | Search live ONS datasets by term. |
| ons_select.search | 0.1.0 | Rank ONS datasets using a cached catalog with explainable scoring and elicitation prompts for missing context. |
| os_apps.log_event | 0.1.0 | Log MCP-Apps UI interaction events for tracing. |
| os_apps.render_feature_inspector | 0.1.0 | Open the MCP-Apps feature inspector widget. |
| os_apps.render_geography_selector | 0.1.0 | Open the MCP-Apps geography selector widget. |
| os_apps.render_route_planner | 0.1.0 | Open the MCP-Apps route planner widget. |
| os_apps.render_statistics_dashboard | 0.1.0 | Open the MCP-Apps statistics dashboard widget. |
| os_apps.render_ui_probe | 0.1.0 | Probe MCP-Apps UI rendering support. |
| os_features.query | 0.1.0 | Query features by bbox |
| os_linked_ids.get | 0.1.0 | Resolve linked identifiers (UPRN/TOID etc) |
| os_maps.render | 0.1.0 | Return metadata for rendering a static map image (proxy URL) |
| os_mcp.descriptor | 0.1.0 | Describe server capabilities and tool search configuration. |
| os_mcp.route_query | 0.1.0 | Classify a query and recommend the right tool/workflow. |
| os_mcp.stats_routing | 0.1.0 | Explain whether stats queries route to ONS or NOMIS. |
| os_names.find | 0.1.0 | Find place names |
| os_names.nearest | 0.1.0 | Nearest named features |
| os_places.by_postcode | 0.1.0 | Lookup UPRNs and addresses for a UK postcode via OS Places API |
| os_places.by_uprn | 0.1.0 | Lookup a single address by UPRN |
| os_places.nearest | 0.1.0 | Find nearest addresses to a point |
| os_places.search | 0.1.0 | Free text search in OS Places |
| os_places.within | 0.1.0 | Addresses within a bounding box |
| os_vector_tiles.descriptor | 0.1.0 | Return vector tiles style and tile template URLs |

---

## admin_lookup.area_geometry

**Description:** Return bbox geometry for a given area id

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string"
    },
    "includeGeometry": {
      "type": "boolean"
    },
    "tool": {
      "const": "admin_lookup.area_geometry",
      "type": "string"
    },
    "zoom": {
      "type": "number"
    }
  },
  "required": [
    "id"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "bbox": {
      "type": "array"
    },
    "geometry": {
      "type": "object"
    },
    "id": {
      "type": "string"
    },
    "level": {
      "type": "string"
    },
    "live": {
      "type": "boolean"
    },
    "meta": {
      "type": "object"
    },
    "name": {
      "type": "string"
    }
  },
  "required": [
    "id",
    "bbox"
  ],
  "type": "object"
}
```


## admin_lookup.containing_areas

**Description:** Return containing administrative areas for a point (lat/lon)

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "lat": {
      "type": "number"
    },
    "lon": {
      "type": "number"
    },
    "tool": {
      "const": "admin_lookup.containing_areas",
      "type": "string"
    }
  },
  "required": [
    "lat",
    "lon"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "live": {
      "type": "boolean"
    },
    "meta": {
      "type": "object"
    },
    "results": {
      "items": {
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "results"
  ],
  "type": "object"
}
```


## admin_lookup.find_by_name

**Description:** Substring case-insensitive search by area name

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "level": {
      "description": "Optional single level (WARD/LSOA/etc).",
      "type": "string"
    },
    "levels": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "limit": {
      "maximum": 200,
      "minimum": 1,
      "type": "integer"
    },
    "limitPerLevel": {
      "maximum": 200,
      "minimum": 1,
      "type": "integer"
    },
    "match": {
      "enum": [
        "contains",
        "starts_with",
        "exact"
      ],
      "type": "string"
    },
    "text": {
      "type": "string"
    },
    "tool": {
      "const": "admin_lookup.find_by_name",
      "type": "string"
    }
  },
  "required": [
    "text"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "count": {
      "type": "integer"
    },
    "live": {
      "type": "boolean"
    },
    "meta": {
      "type": "object"
    },
    "results": {
      "type": "array"
    }
  },
  "required": [
    "results"
  ],
  "type": "object"
}
```


## admin_lookup.get_cache_status

**Description:** Return boundary cache status (levels, datasets, counts).

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "refresh": {
      "type": "boolean"
    },
    "tool": {
      "const": "admin_lookup.get_cache_status",
      "type": "string"
    }
  },
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "configured": {
      "type": "boolean"
    },
    "datasets": {
      "type": "array"
    },
    "dsnSet": {
      "type": "boolean"
    },
    "enabled": {
      "type": "boolean"
    },
    "geomCount": {
      "type": "integer"
    },
    "levels": {
      "type": "array"
    },
    "reloadHint": {
      "type": "string"
    },
    "total": {
      "type": "integer"
    }
  },
  "required": [
    "enabled"
  ],
  "type": "object"
}
```


## admin_lookup.reverse_hierarchy

**Description:** Return ancestor chain for a given area id

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string"
    },
    "tool": {
      "const": "admin_lookup.reverse_hierarchy",
      "type": "string"
    }
  },
  "required": [
    "id"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "chain": {
      "type": "array"
    }
  },
  "required": [
    "chain"
  ],
  "type": "object"
}
```


## admin_lookup.search_cache

**Description:** Search the boundary cache by id/name/level.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "fallbackLive": {
      "description": "Fallback to live lookup if cache unavailable.",
      "type": "boolean"
    },
    "includeGeometry": {
      "type": "boolean"
    },
    "level": {
      "type": "string"
    },
    "limit": {
      "maximum": 200,
      "minimum": 1,
      "type": "integer"
    },
    "query": {
      "type": "string"
    },
    "tool": {
      "const": "admin_lookup.search_cache",
      "type": "string"
    }
  },
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "count": {
      "type": "integer"
    },
    "live": {
      "type": "boolean"
    },
    "meta": {
      "type": "object"
    },
    "results": {
      "type": "array"
    }
  },
  "required": [
    "results"
  ],
  "type": "object"
}
```


## nomis.codelists

**Description:** List NOMIS codelists or return a codelist definition.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "codelist": {
      "type": "string"
    },
    "format": {
      "enum": [
        "sdmx",
        "json"
      ],
      "type": "string"
    },
    "tool": {
      "const": "nomis.codelists",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "codelist": {
      "type": [
        "string",
        "null"
      ]
    },
    "data": {
      "type": "object"
    },
    "format": {
      "type": "string"
    },
    "live": {
      "type": "boolean"
    }
  },
  "required": [
    "live",
    "format",
    "data"
  ],
  "type": "object"
}
```


## nomis.concepts

**Description:** List NOMIS concepts or return a concept definition.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "concept": {
      "type": "string"
    },
    "format": {
      "enum": [
        "sdmx",
        "json"
      ],
      "type": "string"
    },
    "tool": {
      "const": "nomis.concepts",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "concept": {
      "type": [
        "string",
        "null"
      ]
    },
    "data": {
      "type": "object"
    },
    "format": {
      "type": "string"
    },
    "live": {
      "type": "boolean"
    }
  },
  "required": [
    "live",
    "format",
    "data"
  ],
  "type": "object"
}
```


## nomis.datasets

**Description:** List NOMIS datasets (filtered and limited summary by default), or return a dataset definition.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "description": "Optional dataset id",
      "type": "string"
    },
    "format": {
      "enum": [
        "sdmx",
        "json"
      ],
      "type": "string"
    },
    "includeRaw": {
      "default": false,
      "description": "Include the full upstream payload (required to fetch full dataset definitions when dataset is provided).",
      "type": "boolean"
    },
    "limit": {
      "default": 25,
      "maximum": 100,
      "minimum": 1,
      "type": "integer"
    },
    "q": {
      "description": "Optional case-insensitive dataset filter.",
      "type": "string"
    },
    "tool": {
      "const": "nomis.datasets",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "data": {
      "type": "object"
    },
    "dataset": {
      "type": [
        "string",
        "null"
      ]
    },
    "datasets": {
      "items": {
        "type": "object"
      },
      "type": "array"
    },
    "format": {
      "type": "string"
    },
    "hints": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "limit": {
      "type": "integer"
    },
    "live": {
      "type": "boolean"
    },
    "overview": {
      "type": "object"
    },
    "query": {
      "type": [
        "string",
        "null"
      ]
    },
    "queryTemplate": {
      "type": "object"
    },
    "raw": {
      "type": "object"
    },
    "returned": {
      "type": "integer"
    },
    "summary": {
      "type": "object"
    },
    "total": {
      "type": "integer"
    },
    "truncated": {
      "type": "boolean"
    }
  },
  "required": [
    "live",
    "format",
    "data"
  ],
  "type": "object"
}
```


## nomis.query

**Description:** Query NOMIS datasets (JSON-stat or SDMX JSON).

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string"
    },
    "format": {
      "enum": [
        "jsonstat",
        "sdmx"
      ],
      "type": "string"
    },
    "params": {
      "type": "object"
    },
    "tool": {
      "const": "nomis.query",
      "type": "string"
    }
  },
  "required": [
    "dataset"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "data": {
      "type": "object"
    },
    "dataset": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "live": {
      "type": "boolean"
    }
  },
  "required": [
    "live",
    "dataset",
    "format",
    "data"
  ],
  "type": "object"
}
```


## ons_codes.list

**Description:** List available ONS dimensions for a live dataset version.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string"
    },
    "edition": {
      "type": "string"
    },
    "tool": {
      "const": "ons_codes.list",
      "type": "string"
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "dataset",
    "edition",
    "version"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "cached": {
      "type": "boolean"
    },
    "dimensions": {
      "type": "array"
    },
    "live": {
      "type": "boolean"
    }
  },
  "required": [
    "dimensions",
    "live"
  ],
  "type": "object"
}
```


## ons_codes.options

**Description:** List codes/options for a given ONS live dimension.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string"
    },
    "dimension": {
      "type": "string"
    },
    "edition": {
      "type": "string"
    },
    "tool": {
      "const": "ons_codes.options",
      "type": "string"
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "dataset",
    "edition",
    "version",
    "dimension"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "cached": {
      "type": "boolean"
    },
    "dimension": {
      "type": "string"
    },
    "live": {
      "type": "boolean"
    },
    "options": {
      "type": "array"
    }
  },
  "required": [
    "dimension",
    "options",
    "live"
  ],
  "type": "object"
}
```


## ons_data.create_filter

**Description:** Create a filter for live ONS observations. Returns filterId.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string"
    },
    "edition": {
      "type": "string"
    },
    "geography": {
      "type": "string"
    },
    "measure": {
      "type": "string"
    },
    "timeRange": {
      "type": "string"
    },
    "tool": {
      "const": "ons_data.create_filter",
      "type": "string"
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "dataset",
    "edition",
    "version"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "filterId": {
      "type": "string"
    },
    "params": {
      "type": "object"
    }
  },
  "required": [
    "filterId",
    "params"
  ],
  "type": "object"
}
```


## ons_data.dimensions

**Description:** List available ONS observation dimensions from the live API.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string"
    },
    "dimension": {
      "description": "Return only this dimension's codes",
      "type": "string"
    },
    "edition": {
      "type": "string"
    },
    "tool": {
      "const": "ons_data.dimensions",
      "type": "string"
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "dataset",
    "edition",
    "version"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "dimensions": {
      "type": "object"
    },
    "live": {
      "type": "boolean"
    }
  },
  "required": [
    "dimensions",
    "live"
  ],
  "type": "object"
}
```


## ons_data.editions

**Description:** List live editions for an ONS dataset.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string"
    },
    "tool": {
      "const": "ons_data.editions",
      "type": "string"
    }
  },
  "required": [
    "dataset"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "count": {
      "type": "integer"
    },
    "dataset": {
      "type": "string"
    },
    "editions": {
      "type": "array"
    },
    "live": {
      "type": "boolean"
    }
  },
  "required": [
    "dataset",
    "editions",
    "count",
    "live"
  ],
  "type": "object"
}
```


## ons_data.get_filter_output

**Description:** Retrieve data for a previously created filter (formats: JSON, CSV, XLSX).

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "filterId": {
      "type": "string"
    },
    "format": {
      "enum": [
        "JSON",
        "CSV",
        "XLSX"
      ],
      "type": "string"
    },
    "tool": {
      "const": "ons_data.get_filter_output",
      "type": "string"
    }
  },
  "required": [
    "filterId"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "columns": {
      "type": [
        "integer",
        "null"
      ]
    },
    "contentType": {
      "type": [
        "string",
        "null"
      ]
    },
    "data": {
      "type": "object"
    },
    "dataBase64": {
      "type": [
        "string",
        "null"
      ]
    },
    "dataHex": {
      "type": [
        "string",
        "null"
      ]
    },
    "filterId": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "rows": {
      "type": [
        "integer",
        "null"
      ]
    }
  },
  "required": [
    "filterId",
    "format"
  ],
  "type": "object"
}
```


## ons_data.get_observation

**Description:** Fetch a single observation by geography, measure, time from the live ONS API.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string"
    },
    "edition": {
      "type": "string"
    },
    "geography": {
      "type": "string"
    },
    "measure": {
      "type": "string"
    },
    "time": {
      "type": "string"
    },
    "tool": {
      "const": "ons_data.get_observation",
      "type": "string"
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "dataset",
    "edition",
    "version",
    "geography",
    "measure",
    "time"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "live": {
      "type": "boolean"
    },
    "observation": {
      "type": "object"
    }
  },
  "required": [
    "observation",
    "live"
  ],
  "type": "object"
}
```


## ons_data.query

**Description:** Query live ONS observations (dataset/edition/version or search term).

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "description": "ONS dataset ID for live mode",
      "type": "string"
    },
    "edition": {
      "description": "ONS dataset edition for live mode",
      "type": "string"
    },
    "geography": {
      "type": "string"
    },
    "limit": {
      "maximum": 500,
      "minimum": 1,
      "type": "integer"
    },
    "measure": {
      "type": "string"
    },
    "page": {
      "minimum": 1,
      "type": "integer"
    },
    "query": {
      "description": "Alias for term",
      "type": "string"
    },
    "term": {
      "description": "Search term for auto-resolving dataset/edition/version",
      "type": "string"
    },
    "timeRange": {
      "description": "Format 'YYYY Qn-YYYY Qn' or single period 'YYYY Qn'",
      "type": "string"
    },
    "tool": {
      "const": "ons_data.query",
      "type": "string"
    },
    "version": {
      "description": "ONS dataset version for live mode",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "count": {
      "type": "integer"
    },
    "limit": {
      "type": "integer"
    },
    "nextPageToken": {
      "type": [
        "string",
        "null"
      ]
    },
    "page": {
      "type": "integer"
    },
    "results": {
      "items": {
        "type": "object"
      },
      "type": "array"
    },
    "timeRange": {
      "type": [
        "string",
        "null"
      ]
    },
    "timeValues": {
      "type": [
        "array",
        "null"
      ]
    }
  },
  "required": [
    "results",
    "count",
    "limit",
    "page"
  ],
  "type": "object"
}
```


## ons_data.versions

**Description:** List live versions for an ONS dataset edition.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dataset": {
      "type": "string"
    },
    "edition": {
      "type": "string"
    },
    "tool": {
      "const": "ons_data.versions",
      "type": "string"
    }
  },
  "required": [
    "dataset",
    "edition"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "count": {
      "type": "integer"
    },
    "dataset": {
      "type": "string"
    },
    "edition": {
      "type": "string"
    },
    "live": {
      "type": "boolean"
    },
    "versions": {
      "type": "array"
    }
  },
  "required": [
    "dataset",
    "edition",
    "versions",
    "count",
    "live"
  ],
  "type": "object"
}
```


## ons_search.query

**Description:** Search live ONS datasets by term.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "limit": {
      "maximum": 500,
      "minimum": 1,
      "type": "integer"
    },
    "offset": {
      "minimum": 0,
      "type": "integer"
    },
    "term": {
      "type": "string"
    },
    "tool": {
      "const": "ons_search.query",
      "type": "string"
    }
  },
  "required": [
    "term"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "count": {
      "type": "integer"
    },
    "limit": {
      "type": [
        "integer",
        "null"
      ]
    },
    "live": {
      "type": "boolean"
    },
    "offset": {
      "type": [
        "integer",
        "null"
      ]
    },
    "results": {
      "type": "array"
    },
    "total": {
      "type": [
        "integer",
        "null"
      ]
    }
  },
  "required": [
    "results",
    "count"
  ],
  "type": "object"
}
```


## ons_select.search

**Description:** Rank ONS datasets using a cached catalog with explainable scoring and elicitation prompts for missing context.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "geographyLevel": {
      "type": "string"
    },
    "includeRelated": {
      "type": "boolean"
    },
    "intentTags": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "limit": {
      "maximum": 25,
      "minimum": 1,
      "type": "integer"
    },
    "q": {
      "type": "string"
    },
    "query": {
      "type": "string"
    },
    "relatedLimit": {
      "maximum": 10,
      "minimum": 1,
      "type": "integer"
    },
    "timeGranularity": {
      "type": "string"
    },
    "tool": {
      "const": "ons_select.search",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "candidateCount": {
      "type": "integer"
    },
    "candidates": {
      "type": "array"
    },
    "catalogMeta": {
      "type": "object"
    },
    "elicitationQuestions": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "needsElicitation": {
      "type": "boolean"
    },
    "query": {
      "type": "string"
    },
    "relatedDatasets": {
      "type": "array"
    }
  },
  "required": [
    "query",
    "candidates",
    "candidateCount"
  ],
  "type": "object"
}
```


## os_apps.log_event

**Description:** Log MCP-Apps UI interaction events for tracing.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "context": {
      "type": "object"
    },
    "eventType": {
      "type": "string"
    },
    "payload": {
      "type": "object"
    },
    "sessionId": {
      "type": "string"
    },
    "source": {
      "type": "string"
    },
    "timestamp": {
      "type": "number"
    },
    "tool": {
      "const": "os_apps.log_event",
      "type": "string"
    }
  },
  "required": [
    "eventType"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "eventId": {
      "type": "string"
    },
    "logPath": {
      "type": [
        "string",
        "null"
      ]
    },
    "status": {
      "type": "string"
    },
    "timestamp": {
      "type": "number"
    }
  },
  "required": [
    "status",
    "eventId",
    "timestamp"
  ],
  "type": "object"
}
```


## os_apps.render_feature_inspector

**Description:** Open the MCP-Apps feature inspector widget.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "collectionId": {
      "type": "string"
    },
    "contentMode": {
      "type": "string"
    },
    "featureId": {
      "type": "string"
    },
    "linkedIds": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "tool": {
      "const": "os_apps.render_feature_inspector",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "_meta": {
      "type": "object"
    },
    "config": {
      "type": "object"
    },
    "content": {
      "type": "array"
    },
    "instructions": {
      "type": "string"
    },
    "resourceUri": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "structuredContent": {
      "type": "object"
    },
    "uiResourceUris": {
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "status",
    "uiResourceUris"
  ],
  "type": "object"
}
```


## os_apps.render_geography_selector

**Description:** Open the MCP-Apps geography selector widget.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "contentMode": {
      "type": "string"
    },
    "focusLevel": {
      "type": "string"
    },
    "focusName": {
      "type": "string"
    },
    "initialLat": {
      "type": "number"
    },
    "initialLng": {
      "type": "number"
    },
    "initialZoom": {
      "type": "integer"
    },
    "level": {
      "type": "string"
    },
    "multiSelect": {
      "type": "boolean"
    },
    "searchTerm": {
      "type": "string"
    },
    "tool": {
      "const": "os_apps.render_geography_selector",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "_meta": {
      "type": "object"
    },
    "config": {
      "type": "object"
    },
    "content": {
      "type": "array"
    },
    "instructions": {
      "type": "string"
    },
    "resourceUri": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "structuredContent": {
      "type": "object"
    },
    "uiResourceUris": {
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "status",
    "uiResourceUris"
  ],
  "type": "object"
}
```


## os_apps.render_route_planner

**Description:** Open the MCP-Apps route planner widget.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "contentMode": {
      "type": "string"
    },
    "endLat": {
      "type": "number"
    },
    "endLng": {
      "type": "number"
    },
    "mode": {
      "type": "string"
    },
    "startLat": {
      "type": "number"
    },
    "startLng": {
      "type": "number"
    },
    "tool": {
      "const": "os_apps.render_route_planner",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "_meta": {
      "type": "object"
    },
    "config": {
      "type": "object"
    },
    "content": {
      "type": "array"
    },
    "instructions": {
      "type": "string"
    },
    "resourceUri": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "structuredContent": {
      "type": "object"
    },
    "uiResourceUris": {
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "status",
    "uiResourceUris"
  ],
  "type": "object"
}
```


## os_apps.render_statistics_dashboard

**Description:** Open the MCP-Apps statistics dashboard widget.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "areaCodes": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "contentMode": {
      "type": "string"
    },
    "dataset": {
      "type": "string"
    },
    "measure": {
      "type": "string"
    },
    "tool": {
      "const": "os_apps.render_statistics_dashboard",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "_meta": {
      "type": "object"
    },
    "config": {
      "type": "object"
    },
    "content": {
      "type": "array"
    },
    "instructions": {
      "type": "string"
    },
    "resourceUri": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "structuredContent": {
      "type": "object"
    },
    "uiResourceUris": {
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "status",
    "uiResourceUris"
  ],
  "type": "object"
}
```


## os_apps.render_ui_probe

**Description:** Probe MCP-Apps UI rendering support.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "contentMode": {
      "type": "string"
    },
    "resourceUri": {
      "type": "string"
    },
    "tool": {
      "const": "os_apps.render_ui_probe",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "_meta": {
      "type": "object"
    },
    "config": {
      "type": "object"
    },
    "content": {
      "type": "array"
    },
    "instructions": {
      "type": "string"
    },
    "resourceUri": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "structuredContent": {
      "type": "object"
    },
    "uiResourceUris": {
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "status",
    "uiResourceUris"
  ],
  "type": "object"
}
```


## os_features.query

**Description:** Query features by bbox

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "bbox": {
      "items": {
        "type": "number"
      },
      "maxItems": 4,
      "minItems": 4,
      "type": "array"
    },
    "collection": {
      "type": "string"
    },
    "tool": {
      "const": "os_features.query",
      "type": "string"
    }
  },
  "required": [
    "collection",
    "bbox"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "count": {
      "type": "number"
    },
    "features": {
      "type": "array"
    }
  },
  "required": [
    "features"
  ],
  "type": "object"
}
```


## os_linked_ids.get

**Description:** Resolve linked identifiers (UPRN/TOID etc)

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "identifier": {
      "type": "string"
    },
    "tool": {
      "const": "os_linked_ids.get",
      "type": "string"
    }
  },
  "required": [
    "identifier"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "identifiers": {
      "type": [
        "array",
        "object"
      ]
    }
  },
  "required": [
    "identifiers"
  ],
  "type": "object"
}
```


## os_maps.render

**Description:** Return metadata for rendering a static map image (proxy URL)

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "bbox": {
      "items": {
        "type": "number"
      },
      "maxItems": 4,
      "minItems": 4,
      "type": "array"
    },
    "tool": {
      "const": "os_maps.render",
      "type": "string"
    }
  },
  "required": [
    "bbox"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "render": {
      "type": "object"
    }
  },
  "required": [
    "render"
  ],
  "type": "object"
}
```


## os_mcp.descriptor

**Description:** Describe server capabilities and tool search configuration.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "category": {
      "description": "Optional tool category to filter search config.",
      "type": "string"
    },
    "includeTools": {
      "default": true,
      "description": "Include per-tool metadata in toolSearch section.",
      "type": "boolean"
    },
    "tool": {
      "const": "os_mcp.descriptor",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "capabilities": {
      "type": "object"
    },
    "protocolVersion": {
      "type": "string"
    },
    "server": {
      "type": "string"
    },
    "skillsUri": {
      "type": "string"
    },
    "toolSearch": {
      "type": "object"
    },
    "transport": {
      "type": "string"
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "server",
    "version",
    "protocolVersion",
    "toolSearch"
  ],
  "type": "object"
}
```


## os_mcp.route_query

**Description:** Classify a query and recommend the right tool/workflow.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "tool": {
      "const": "os_mcp.route_query",
      "type": "string"
    }
  },
  "required": [
    "query"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "alternative_tools": {
      "type": "array"
    },
    "confidence": {
      "type": "number"
    },
    "explanation": {
      "type": "string"
    },
    "guidance": {
      "type": "string"
    },
    "intent": {
      "type": "string"
    },
    "query": {
      "type": "string"
    },
    "recommended_parameters": {
      "type": "object"
    },
    "recommended_tool": {
      "type": "string"
    },
    "workflow_steps": {
      "type": "array"
    }
  },
  "required": [
    "intent",
    "confidence",
    "recommended_tool",
    "workflow_steps"
  ],
  "type": "object"
}
```


## os_mcp.stats_routing

**Description:** Explain whether stats queries route to ONS or NOMIS.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "comparisonLevel": {
      "enum": [
        "WARD",
        "LSOA",
        "MSOA"
      ],
      "type": "string"
    },
    "providerPreference": {
      "enum": [
        "AUTO",
        "NOMIS",
        "ONS"
      ],
      "type": "string"
    },
    "query": {
      "type": "string"
    },
    "tool": {
      "const": "os_mcp.stats_routing",
      "type": "string"
    }
  },
  "required": [
    "query"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "comparisonRecommended": {
      "type": "boolean"
    },
    "matchedLevels": {
      "type": "array"
    },
    "matchedPatterns": {
      "type": "array"
    },
    "nextSteps": {
      "type": "array"
    },
    "nomisPreferred": {
      "type": "boolean"
    },
    "notes": {
      "type": "array"
    },
    "provider": {
      "type": "string"
    },
    "query": {
      "type": "string"
    },
    "reasons": {
      "type": "array"
    },
    "recommendedTool": {
      "type": "string"
    },
    "userSelections": {
      "type": "object"
    }
  },
  "required": [
    "provider",
    "nomisPreferred",
    "reasons",
    "recommendedTool"
  ],
  "type": "object"
}
```


## os_names.find

**Description:** Find place names

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "text": {
      "type": "string"
    },
    "tool": {
      "const": "os_names.find",
      "type": "string"
    }
  },
  "required": [
    "text"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "results": {
      "type": "array"
    }
  },
  "required": [
    "results"
  ],
  "type": "object"
}
```


## os_names.nearest

**Description:** Nearest named features

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "coordSystem": {
      "default": "EPSG:4326",
      "enum": [
        "EPSG:4326",
        "EPSG:27700"
      ],
      "type": "string"
    },
    "lat": {
      "type": "number"
    },
    "lon": {
      "type": "number"
    },
    "tool": {
      "const": "os_names.nearest",
      "type": "string"
    }
  },
  "required": [
    "lat",
    "lon"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "results": {
      "type": "array"
    }
  },
  "required": [
    "results"
  ],
  "type": "object"
}
```


## os_places.by_postcode

**Description:** Lookup UPRNs and addresses for a UK postcode via OS Places API

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "postcode": {
      "description": "UK postcode",
      "type": "string"
    },
    "tool": {
      "const": "os_places.by_postcode",
      "type": "string"
    }
  },
  "required": [
    "postcode"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "additionalProperties": true,
  "properties": {
    "provenance": {
      "type": "object"
    },
    "uprns": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "address": {
            "type": [
              "string",
              "null"
            ]
          },
          "classification": {
            "type": [
              "string",
              "null"
            ]
          },
          "classificationDescription": {
            "type": [
              "string",
              "null"
            ]
          },
          "lat": {
            "type": "number"
          },
          "localCustodianName": {
            "type": [
              "string",
              "null"
            ]
          },
          "local_custodian_code": {
            "type": [
              "string",
              "number",
              "null"
            ]
          },
          "lon": {
            "type": "number"
          },
          "uprn": {
            "type": [
              "string",
              "null"
            ]
          }
        },
        "required": [
          "uprn",
          "address",
          "lat",
          "lon"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "uprns"
  ],
  "type": "object"
}
```


## os_places.by_uprn

**Description:** Lookup a single address by UPRN

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "tool": {
      "const": "os_places.by_uprn",
      "type": "string"
    },
    "uprn": {
      "type": "string"
    }
  },
  "required": [
    "uprn"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "result": {
      "type": [
        "object",
        "null"
      ]
    }
  },
  "required": [
    "result"
  ],
  "type": "object"
}
```


## os_places.nearest

**Description:** Find nearest addresses to a point

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "lat": {
      "type": "number"
    },
    "lon": {
      "type": "number"
    },
    "tool": {
      "const": "os_places.nearest",
      "type": "string"
    }
  },
  "required": [
    "lat",
    "lon"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "results": {
      "type": "array"
    }
  },
  "required": [
    "results"
  ],
  "type": "object"
}
```


## os_places.search

**Description:** Free text search in OS Places

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "text": {
      "type": "string"
    },
    "tool": {
      "const": "os_places.search",
      "type": "string"
    }
  },
  "required": [
    "text"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "count": {
      "type": "number"
    },
    "results": {
      "type": "array"
    }
  },
  "required": [
    "results"
  ],
  "type": "object"
}
```


## os_places.within

**Description:** Addresses within a bounding box

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "bbox": {
      "items": {
        "type": "number"
      },
      "maxItems": 4,
      "minItems": 4,
      "type": "array"
    },
    "tool": {
      "const": "os_places.within",
      "type": "string"
    }
  },
  "required": [
    "bbox"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "additionalProperties": true,
  "properties": {
    "provenance": {
      "type": "object"
    },
    "results": {
      "type": "array"
    }
  },
  "required": [
    "results"
  ],
  "type": "object"
}
```


## os_vector_tiles.descriptor

**Description:** Return vector tiles style and tile template URLs

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "tool": {
      "const": "os_vector_tiles.descriptor",
      "type": "string"
    }
  },
  "required": [],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "vectorTiles": {
      "type": "object"
    }
  },
  "required": [
    "vectorTiles"
  ],
  "type": "object"
}
```

