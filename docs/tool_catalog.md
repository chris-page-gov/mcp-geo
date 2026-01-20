# Tool Catalog

Auto-generated list of current tools, their descriptions, versions, and JSON Schemas.

| Tool | Version | Description |
|------|---------|-------------|
| admin_lookup.area_geometry | 0.1.0 | Return bbox geometry for a given area id |
| admin_lookup.containing_areas | 0.1.0 | Return containing administrative areas for a point (lat/lon) |
| admin_lookup.find_by_name | 0.1.0 | Substring case-insensitive search by area name |
| admin_lookup.reverse_hierarchy | 0.1.0 | Return ancestor chain for a given area id |
| ons_codes.list | 0.1.0 | List available ONS sample dimensions. |
| ons_codes.options | 0.1.0 | List codes/options for a given ONS sample dimension. |
| ons_data.create_filter | 0.1.0 | Create a filter for ONS observations (sample subset). Returns filterId. |
| ons_data.dimensions | 0.1.0 | List available ONS observation dimensions (sample or live dataset metadata). Optionally restrict to one dimension via 'dimension' field. |
| ons_data.get_filter_output | 0.1.0 | Retrieve data for a previously created filter (formats: JSON, CSV, XLSX). |
| ons_data.get_observation | 0.1.0 | Fetch a single observation by geography, measure, time (live or sample). |
| ons_data.query | 0.1.0 | Query ONS observations. Uses live ONS API when ONS_LIVE_ENABLED and dataset/edition/version provided; otherwise queries bundled sample (filters: geography, measure, timeRange; pagination). |
| ons_search.query | 0.1.0 | Search sample ONS dimensions for code fragments. |
| os_apps.render_feature_inspector | 0.1.0 | Open the MCP-Apps feature inspector widget. |
| os_apps.render_geography_selector | 0.1.0 | Open the MCP-Apps geography selector widget. |
| os_apps.render_route_planner | 0.1.0 | Open the MCP-Apps route planner widget. |
| os_apps.render_statistics_dashboard | 0.1.0 | Open the MCP-Apps statistics dashboard widget. |
| os_features.query | 0.1.0 | Query features by bbox |
| os_linked_ids.get | 0.1.0 | Resolve linked identifiers (UPRN/TOID etc) |
| os_maps.render | 0.1.0 | Return metadata for rendering a map image (URL template) |
| os_mcp.descriptor | 0.1.0 | Describe server capabilities and tool search configuration. |
| os_mcp.route_query | 0.1.0 | Classify a query and recommend the right tool/workflow. |
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
    "tool": {
      "const": "admin_lookup.area_geometry",
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
    "bbox": {
      "type": "array"
    },
    "id": {
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


## ons_codes.list

**Description:** List available ONS sample dimensions.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "tool": {
      "const": "ons_codes.list",
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
    "dimensions": {
      "type": "array"
    }
  },
  "required": [
    "dimensions"
  ],
  "type": "object"
}
```


## ons_codes.options

**Description:** List codes/options for a given ONS sample dimension.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
    "dimension": {
      "type": "string"
    },
    "tool": {
      "const": "ons_codes.options",
      "type": "string"
    }
  },
  "required": [
    "dimension"
  ],
  "type": "object"
}
```
### Output Schema

```json
{
  "properties": {
    "dimension": {
      "type": "string"
    },
    "options": {
      "type": "array"
    }
  },
  "required": [
    "dimension",
    "options"
  ],
  "type": "object"
}
```


## ons_data.create_filter

**Description:** Create a filter for ONS observations (sample subset). Returns filterId.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
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

**Description:** List available ONS observation dimensions (sample or live dataset metadata). Optionally restrict to one dimension via 'dimension' field.

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
  "required": [],
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

**Description:** Fetch a single observation by geography, measure, time (live or sample).

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

**Description:** Query ONS observations. Uses live ONS API when ONS_LIVE_ENABLED and dataset/edition/version provided; otherwise queries bundled sample (filters: geography, measure, timeRange; pagination).

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


## ons_search.query

**Description:** Search sample ONS dimensions for code fragments.

**Version:** 0.1.0

### Input Schema

```json
{
  "additionalProperties": false,
  "properties": {
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
    "results": {
      "type": "array"
    }
  },
  "required": [
    "results",
    "count"
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
    "instructions": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "uiResourceUris": {
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
    "instructions": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "uiResourceUris": {
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
    "instructions": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "uiResourceUris": {
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
    "instructions": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "uiResourceUris": {
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

**Description:** Return metadata for rendering a map image (URL template)

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
    "server": {
      "type": "string"
    },
    "skillsUri": {
      "type": "string"
    },
    "toolSearch": {
      "type": "object"
    },
    "uiResourceCatalog": {
      "type": "array"
    },
    "uiResources": {
      "type": "array"
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "server",
    "version",
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


