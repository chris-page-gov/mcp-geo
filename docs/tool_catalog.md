# Tool Catalog

Auto-generated list of current tools, their descriptions, versions, and JSON Schemas.

| Tool | Version | Description |
|------|---------|-------------|
| os_apps.log_event | 0.1.0 | Log MCP-Apps UI interaction events for tracing. |
| os_apps.render_feature_inspector | 0.1.0 | Open the MCP-Apps feature inspector widget. |
| os_apps.render_geography_selector | 0.1.0 | Open the MCP-Apps geography selector widget. |
| os_apps.render_route_planner | 0.1.0 | Open the MCP-Apps route planner widget. |
| os_apps.render_statistics_dashboard | 0.1.0 | Open the MCP-Apps statistics dashboard widget. |
| os_maps.render | 0.1.0 | Return metadata for rendering a static map image (proxy URL) |
| os_mcp.descriptor | 0.1.0 | Describe server capabilities and tool search configuration. |
| os_mcp.route_query | 0.1.0 | Classify a query and recommend the right tool/workflow. |
| os_mcp.stats_routing | 0.1.0 | Explain whether stats queries route to ONS or NOMIS. |

---

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
    "config": {
      "type": "object"
    },
    "content": {
      "type": "array"
    },
    "instructions": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "structuredContent": {
      "type": "object"
    }
  },
  "required": [
    "status"
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
    "config": {
      "type": "object"
    },
    "content": {
      "type": "array"
    },
    "instructions": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "structuredContent": {
      "type": "object"
    }
  },
  "required": [
    "status"
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
    "config": {
      "type": "object"
    },
    "content": {
      "type": "array"
    },
    "instructions": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "structuredContent": {
      "type": "object"
    }
  },
  "required": [
    "status"
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
    "config": {
      "type": "object"
    },
    "content": {
      "type": "array"
    },
    "instructions": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "structuredContent": {
      "type": "object"
    }
  },
  "required": [
    "status"
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


