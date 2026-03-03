# Validating NOMIS Trace Evidence (2026-03-03)

- Source: `logs/claude-trace.jsonl`
- Scope: failing `nomis_query` attempts for `NM_2028_1` and follow-on `os_mcp_descriptor` call

## Event Sequence

### Line 4769 (2026-03-03T19:27:25.944117+00:00)
- direction: `client->server`
- method: `tools/call`
- id: `20`
- payload:
```json
{
  "tool": "nomis_query",
  "arguments": {
    "dataset": "NM_2028_1",
    "params": {
      "geography": "E05001229,E05001233,E05001227",
      "c2021_age_92": "0",
      "measures": "20100",
      "select": "geography_name,geography_code,obs_value"
    }
  }
}
```

### Line 4771 (2026-03-03T19:27:26.356729+00:00)
- direction: `server->client`
- id: `20`
- payload:
```json
{
  "status": 400,
  "data": {
    "isError": true,
    "code": "NOMIS_QUERY_ERROR",
    "message": "Cannot create query"
  }
}
```

### Line 4772 (2026-03-03T19:27:49.585065+00:00)
- direction: `client->server`
- method: `tools/call`
- id: `21`
- payload:
```json
{
  "tool": "nomis_query",
  "arguments": {
    "dataset": "NM_2028_1",
    "format": "jsonstat",
    "params": {
      "geography": "E05001229,E05001233,E05001227,E05001220,E05001221,E05001222,E05001223,E05001224,E05001225,E05001226,E05001228,E05001230,E05001231,E05001232",
      "c2021_age_92": "0",
      "measures": "20100"
    }
  }
}
```

### Line 4774 (2026-03-03T19:27:49.853886+00:00)
- direction: `server->client`
- id: `21`
- payload:
```json
{
  "status": 400,
  "data": {
    "isError": true,
    "code": "NOMIS_QUERY_ERROR",
    "message": "Cannot create query"
  }
}
```

### Line 4775 (2026-03-03T19:28:00.982944+00:00)
- direction: `client->server`
- method: `tools/call`
- id: `22`
- payload:
```json
{
  "tool": "nomis_query",
  "arguments": {
    "dataset": "NM_2028_1",
    "format": "jsonstat",
    "params": {
      "geography": "645922049...645922066",
      "c2021_age_92": "0",
      "measures": "20100"
    }
  }
}
```

### Line 4776 (2026-03-03T19:28:01.227623+00:00)
- direction: `server->client`
- id: `22`
- payload:
```json
{
  "status": 400,
  "data": {
    "isError": true,
    "code": "NOMIS_QUERY_ERROR",
    "message": "Cannot create query"
  }
}
```

### Line 4777 (2026-03-03T19:28:17.615014+00:00)
- direction: `client->server`
- method: `tools/call`
- id: `23`
- payload:
```json
{
  "tool": "nomis_query",
  "arguments": {
    "dataset": "NM_2028_1",
    "format": "jsonstat",
    "params": {
      "geography": "E08000026",
      "c2021_age_92": "0",
      "measures": "20100"
    }
  }
}
```

### Line 4778 (2026-03-03T19:28:17.761134+00:00)
- direction: `server->client`
- id: `23`
- payload:
```json
{
  "status": 400,
  "data": {
    "isError": true,
    "code": "NOMIS_QUERY_ERROR",
    "message": "Cannot create query"
  }
}
```

### Line 4779 (2026-03-03T19:33:45.181997+00:00)
- direction: `client->server`
- method: `tools/call`
- id: `24`
- payload:
```json
{
  "tool": "os_mcp_descriptor",
  "arguments": {
    "category": "stats"
  }
}
```

### Line 4780 (2026-03-03T19:33:45.186666+00:00)
- direction: `server->client`
- id: `24`
- payload:
```json
{
  "status": 200,
  "data": {
    "server": "mcp-geo",
    "version": "0.4.0",
    "protocolVersion": "2025-11-25",
    "supportedProtocolVersions": [
      "2025-11-25",
      "2025-06-18",
      "2025-03-26",
      "2024-11-05"
    ],
    "mcpAppsProtocolVersion": "2026-01-26",
    "capabilities": {
      "toolSearch": true,
      "skills": true,
      "extensions": {
        "io.modelcontextprotocol/ui": {
          "mimeTypes": [
            "text/html;profile=mcp-app"
          ]
        }
      }
    },
    "toolSearch": {
      "always_loaded": [
        "admin_lookup.find_by_name",
        "nomis.query",
        "ons_data.query",
        "ons_search.query",
        "ons_select.search",
        "os_apps.log_event",
        "os_apps.render_boundary_explorer",
        "os_apps.render_geography_selector",
        "os_mcp.descriptor",
        "os_mcp.route_query",
        "os_mcp.select_toolsets",
        "os_mcp.stats_routing",
        "os_names.find",
        "os_places.by_postcode",
        "os_places.search"
      ],
      "deferred": [
        "admin_lookup.area_geometry",
        "admin_lookup.containing_areas",
        "admin_lookup.get_cache_status",
        "admin_lookup.reverse_hierarchy",
        "admin_lookup.search_cache",
        "nomis.codelists",
        "nomis.concepts",
        "nomis.datasets",
        "ons_codes.list",
        "ons_codes.options",
        "ons_data.create_filter",
        "ons_data.dimensions",
        "ons_data.editions",
        "ons_data.get_filter_output",
        "ons_data.get_observation",
        "ons_data.versions",
        "ons_geo.by_postcode",
        "ons_geo.by_uprn",
        "ons_geo.cache_status",
        "os_apps.render_feature_inspector",
        "os_apps.render_route_planner",
        "os_apps.render_statistics_dashboard",
        "os_apps.render_ui_probe",
        "os_downloads.get_export",
        "os_downloads.get_product",
        "os_downloads.list_data_packages",
        "os_downloads.list_product_downloads",
        "os_downloads.list_products",
        "os_downloads.prepare_export",
        "os_features.collections",
        "os_features.query",
        "os_features.wfs_archive_capabilities",
        "os_features.wfs_capabilities",
        "os_landscape.find",
        "os_landscape.get",
        "os_linked_ids.feature_types",
        "os_linked_ids.get",
        "os_linked_ids.identifiers",
        "os_linked_ids.product_version_info",
        "os_map.export",
        "os_map.inventory",
        "os_maps.raster_tile",
        "os_maps.render",
        "os_maps.wmts_capabilities",
        "os_names.nearest",
        "os_net.rinex_years",
        "os_net.station_get",
        "os_net.station_log",
        "os_offline.descriptor",
        "os_offline.get",
        "os_peat.evidence_paths",
        "os_peat.layers",
        "os_places.by_uprn",
        "os_places.nearest",
        "os_places.polygon",
        "os_places.radius",
        "os_places.within",
        "os_poi.nearest",
        "os_poi.search",
        "os_poi.within",
        "os_qgis.export_geopackage_descriptor",
        "os_qgis.vector_tile_profile",
        "os_tiles_ota.collections",
        "os_tiles_ota.conformance",
        "os_tiles_ota.tilematrixsets",
        "os_vector_tiles.descriptor"
      ],
      "counts": {
        "always_loaded": 15,
        "deferred": 66,
        "total": 81
      },
      "categories": [
        "core",
        "places",
        "names",
        "features",
        "linked",
        "maps",
        "vector",
        "admin",
        "statistics",
        "codes",
        "apps",
        "utility"
      ],
      "toolsets": {
        "starter": {
          "patterns": [
            "admin_lookup.find_by_name",
            "nomis.query",
            "ons_data.query",
            "ons_search.query",
            "ons_select.search",
            "os_apps.log_event",
            "os_apps.render_boundary_explorer",
            "os_apps.render_geography_selector",
            "os_mcp.descriptor",
            "os_mcp.route_query",
            "os_mcp.select_toolsets",
            "os_mcp.stats_routing",
            "os_names.find",
            "os_places.by_postcode",
            "os_places.search"
          ],
          "tools": [
            "admin_lookup.find_by_name",
            "nomis.query",
            "ons_data.query",
            "ons_search.query",
            "ons_select.search",
            "os_apps.log_event",
            "os_apps.render_boundary_explorer",
            "os_apps.render_geography_selector",
            "os_mcp.descriptor",
            "os_mcp.route_query",
            "os_mcp.select_toolsets",
            "os_mcp.stats_routing",
            "os_names.find",
            "os_places.by_postcode",
            "os_places.search"
          ],
          "count": 15
        },
        "core_router": {
          "patterns": [
            "os_mcp.*"
          ],
          "tools": [
            "os_mcp.descriptor",
            "os_mcp.route_query",
            "os_mcp.select_toolsets",
            "os_mcp.stats_routing"
          ],
          "count": 4
        },
        "places_names": {
          "patterns": [
            "os_places.*",
            "os_poi.*",
            "os_names.*",
            "os_linked_ids.get"
          ],
          "tools": [
            "os_linked_ids.get",
            "os_names.find",
            "os_names.nearest",
            "os_places.by_postcode",
            "os_places.by_uprn",
            "os_places.nearest",
            "os_places.polygon",
            "os_places.radius",
            "os_places.search",
            "os_places.within",
            "os_poi.nearest",
            "os_poi.search",
            "os_poi.within"
          ],
          "count": 13
        },
        "features_layers": {
          "patterns": [
            "os_features.*",
            "os_peat.*",
            "os_landscape.*",
            "os_map.inventory",
            "os_map.export"
          ],
          "tools": [
            "os_features.collections",
            "os_features.query",
            "os_features.wfs_archive_capabilities",
            "os_features.wfs_capabilities",
            "os_landscape.find",
            "os_landscape.get",
            "os_map.export",
            "os_map.inventory",
            "os_peat.evidence_paths",
            "os_peat.layers"
          ],
          "count": 10
        },
        "peat_survey": {
          "patterns": [
            "os_peat.*",
            "os_landscape.*",
            "os_features.query"
          ],
          "tools": [
            "os_features.query",
            "os_landscape.find",
            "os_landscape.get",
            "os_peat.evidence_paths",
            "os_peat.layers"
          ],
          "count": 5
        },
        "protected_landscapes": {
          "patterns": [
            "os_landscape.*"
          ],
          "tools": [
            "os_landscape.find",
            "os_landscape.get"
          ],
          "count": 2
        },
        "maps_tiles": {
          "patterns": [
            "os_maps.render",
            "os_vector_tiles.descriptor"
          ],
          "tools": [
            "os_maps.render",
            "os_vector_tiles.descriptor"
          ],
          "count": 2
        },
        "offline_maps": {
          "patterns": [
            "os_offline.*"
          ],
          "tools": [
            "os_offline.descriptor",
            "os_offline.get"
          ],
          "count": 2
        },
        "qgis_linkage": {
          "patterns": [
            "os_qgis.*"
          ],
          "tools": [
            "os_qgis.export_geopackage_descriptor",
            "os_qgis.vector_tile_profile"
          ],
          "count": 2
        },
        "admin_boundaries": {
          "patterns": [
            "admin_lookup.*"
          ],
          "tools": [
            "admin_lookup.area_geometry",
            "admin_lookup.containing_areas",
            "admin_lookup.find_by_name",
            "admin_lookup.get_cache_status",
            "admin_lookup.reverse_hierarchy",
            "admin_lookup.search_cache"
          ],
          "count": 6
        },
        "ons_selection": {
          "patterns": [
            "ons_select.search",
            "ons_search.query",
            "ons_codes.*"
          ],
          "tools": [
            "ons_codes.list",
            "ons_codes.options",
            "ons_search.query",
            "ons_select.search"
          ],
          "count": 4
        },
        "ons_geo_lookup": {
          "patterns": [
            "ons_geo.*"
          ],
          "tools": [
            "ons_geo.by_postcode",
            "ons_geo.by_uprn",
            "ons_geo.cache_status"
          ],
          "count": 3
        },
        "ons_data": {
          "patterns": [
            "ons_data.*"
          ],
          "tools": [
            "ons_data.create_filter",
            "ons_data.dimensions",
            "ons_data.editions",
            "ons_data.get_filter_output",
            "ons_data.get_observation",
            "ons_data.query",
            "ons_data.versions"
          ],
          "count": 7
        },
        "nomis_data": {
          "patterns": [
            "nomis.*"
          ],
          "tools": [
            "nomis.codelists",
            "nomis.concepts",
            "nomis.datasets",
            "nomis.query"
          ],
          "count": 4
        },
        "apps_ui": {
          "patterns": [
            "os_apps.render_*",
            "os_apps.log_event"
          ],
          "tools": [
            "os_apps.log_event",
            "os_apps.render_boundary_explorer",
            "os_apps.render_feature_inspector",
            "os_apps.render_geography_selector",
            "os_apps.render_route_planner",
            "os_apps.render_statistics_dashboard",
            "os_apps.render_ui_probe"
          ],
          "count": 7
        }
      },
      "mcp_toolset_config": {
        "type": "mcp_toolset",
        "mcp_server_name": "mcp-geo",
        "default_config": {
          "defer_loading": true
        },
        "configs": {
          "os_mcp.route_query": {
            "defer_loading": false
          },
          "admin_lookup.find_by_name": {
            "defer_loading": false
          },
          "os_mcp.descriptor": {
            "defer_loading": false
          },
          "os_apps.render_geography_selector": {
            "defer_loading": false
          },
          "os_places.by_postcode": {
            "defer_loading": false
          },
          "ons_search.query": {
            "defer_loading": false
          },
          "os_mcp.stats_routing": {
            "defer_loading": false
          },
          "os_places.search": {
            "defer_loading": false
          },
          "nomis.query": {
            "defer_loading": false
          },
          "os_mcp.select_toolsets": {
            "defer_loading": false
          },
          "os_apps.render_boundary_explorer": {
            "defer_loading": false
          },
          "os_names.find": {
            "defer_loading": false
          },
          "os_apps.log_event": {
            "defer_loading": false
          },
          "ons_select.search": {
            "defer_loading": false
          },
          "ons_data.query": {
            "defer_loading": false
          }
        },
        "named_toolsets": {
          "starter": {
            "patterns": [
              "admin_lookup.find_by_name",
              "nomis.query",
              "ons_data.query",
              "ons_search.query",
              "ons_select.search",
              "os_apps.log_event",
              "os_apps.render_boundary_explorer",
              "os_apps.render_geography_selector",
              "os_mcp.descriptor",
              "os_mcp.route_query",
              "os_mcp.select_toolsets",
              "os_mcp.stats_routing",
              "os_names.find",
              "os_places.by_postcode",
              "os_places.search"
            ],
            "tools": [
              "admin_lookup.find_by_name",
              "nomis.query",
              "ons_data.query",
              "ons_search.query",
              "ons_select.search",
              "os_apps.log_event",
              "os_apps.render_boundary_explorer",
              "os_apps.render_geography_selector",
              "os_mcp.descriptor",
              "os_mcp.route_query",
              "os_mcp.select_toolsets",
              "os_mcp.stats_routing",
              "os_names.find",
              "os_places.by_postcode",
              "os_places.search"
            ],
            "count": 15
          },
          "core_router": {
            "patterns": [
              "os_mcp.*"
            ],
            "tools": [
              "os_mcp.descriptor",
              "os_mcp.route_query",
              "os_mcp.select_toolsets",
              "os_mcp.stats_routing"
            ],
            "count": 4
          },
          "places_names": {
            "patterns": [
              "os_places.*",
              "os_poi.*",
              "os_names.*",
              "os_linked_ids.get"
            ],
            "tools": [
              "os_linked_ids.get",
              "os_names.find",
              "os_names.nearest",
              "os_places.by_postcode",
              "os_places.by_uprn",
              "os_places.nearest",
              "os_places.polygon",
              "os_places.radius",
              "os_places.search",
              "os_places.within",
              "os_poi.nearest",
              "os_poi.search",
              "os_poi.within"
            ],
            "count": 13
          },
          "features_layers": {
            "patterns": [
              "os_features.*",
              "os_peat.*",
              "os_landscape.*",
              "os_map.inventory",
              "os_map.export"
            ],
            "tools": [
              "os_features.collections",
              "os_features.query",
              "os_features.wfs_archive_capabilities",
              "os_features.wfs_capabilities",
              "os_landscape.find",
              "os_landscape.get",
              "os_map.export",
              "os_map.inventory",
              "os_peat.evidence_paths",
              "os_peat.layers"
            ],
            "count": 10
          },
          "peat_survey": {
            "patterns": [
              "os_peat.*",
              "os_landscape.*",
              "os_features.query"
            ],
            "tools": [
              "os_features.query",
              "os_landscape.find",
              "os_landscape.get",
              "os_peat.evidence_paths",
              "os_peat.layers"
            ],
            "count": 5
          },
          "protected_landscapes": {
            "patterns": [
              "os_landscape.*"
            ],
            "tools": [
              "os_landscape.find",
              "os_landscape.get"
            ],
            "count": 2
          },
          "maps_tiles": {
            "patterns": [
              "os_maps.render",
              "os_vector_tiles.descriptor"
            ],
            "tools": [
              "os_maps.render",
              "os_vector_tiles.descriptor"
            ],
            "count": 2
          },
          "offline_maps": {
            "patterns": [
              "os_offline.*"
            ],
            "tools": [
              "os_offline.descriptor",
              "os_offline.get"
            ],
            "count": 2
          },
          "qgis_linkage": {
            "patterns": [
              "os_qgis.*"
            ],
            "tools": [
              "os_qgis.export_geopackage_descriptor",
              "os_qgis.vector_tile_profile"
            ],
            "count": 2
          },
          "admin_boundaries": {
            "patterns": [
              "admin_lookup.*"
            ],
            "tools": [
              "admin_lookup.area_geometry",
              "admin_lookup.containing_areas",
              "admin_lookup.find_by_name",
              "admin_lookup.get_cache_status",
              "admin_lookup.reverse_hierarchy",
              "admin_lookup.search_cache"
            ],
            "count": 6
          },
          "ons_selection": {
            "patterns": [
              "ons_select.search",
              "ons_search.query",
              "ons_codes.*"
            ],
            "tools": [
              "ons_codes.list",
              "ons_codes.options",
              "ons_search.query",
              "ons_select.search"
            ],
            "count": 4
          },
          "ons_geo_lookup": {
            "patterns": [
              "ons_geo.*"
            ],
            "tools": [
              "ons_geo.by_postcode",
              "ons_geo.by_uprn",
              "ons_geo.cache_status"
            ],
            "count": 3
          },
          "ons_data": {
            "patterns": [
              "ons_data.*"
            ],
            "tools": [
              "ons_data.create_filter",
              "ons_data.dimensions",
              "ons_data.editions",
              "ons_data.get_filter_output",
              "ons_data.get_observation",
              "ons_data.query",
              "ons_data.versions"
            ],
            "count": 7
          },
          "nomis_data": {
            "patterns": [
              "nomis.*"
            ],
            "tools": [
              "nomis.codelists",
              "nomis.concepts",
              "nomis.datasets",
              "nomis.query"
            ],
            "count": 4
          },
          "apps_ui": {
            "patterns": [
              "os_apps.render_*",
              "os_apps.log_event"
            ],
            "tools": [
              "os_apps.log_event",
              "os_apps.render_boundary_explorer",
              "os_apps.render_feature_inspector",
              "os_apps.render_geography_selector",
              "os_apps.render_route_planner",
              "os_apps.render_statistics_dashboard",
              "os_apps.render_ui_probe"
            ],
            "count": 7
          }
        }
      },
      "system_prompt": "Start with os_mcp.route_query for natural-language requests.\nPrimary tools:\n- os_places.search: free text address search\n- os_places.by_postcode: lookup UPRNs and addresses\n- os_poi.search: search points of interest (amenities/services)\n- os_offline.descriptor: inspect offline PMTiles/MBTiles pack contracts\n- admin_lookup.find_by_name: find administrative areas by name (use level/levels to reduce noise)\n- ons_select.search: rank ONS datasets with explainability\n- ons_search.query: discover ONS datasets (live API search)\n- ons_data.query: query ONS observations\n- nomis.query: query NOMIS labour and census statistics\n\nUse MCP-Apps widgets for interactive workflows (os_apps.* tools).\nSpecialized OS feature tools are for NGD feature collections, not place lookups.",
      "error": "Invalid category 'stats'. Valid: ['core', 'places', 'names', 'features', 'linked', 'maps', 'vector', 'admin', 'statistics', 'codes', 'apps', 'utility']"
    },
    "skillsUri": "skills://mcp-geo/getting-started",
    "transport": "stdio"
  }
}
```
