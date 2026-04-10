---
title: "Playground and Browser Tests"
kb_kind: "code_family"
source_paths:
  - "playground/app.py"
  - "playground/index.html"
  - "playground/package-lock.json"
  - "playground/package.json"
  - "playground/playwright.compact-matrix.config.js"
  - "playground/playwright.compact.config.js"
  - "playground/playwright.config.js"
  - "playground/playwright.full.config.js"
  - "playground/playwright.live.config.js"
  - "playground/playwright.trials.config.js"
  - "playground/src/App.svelte"
  - "playground/src/components/AuditWorkbench.svelte"
  - "playground/src/components/BenchmarkWorkbench.svelte"
  - "playground/src/components/DebugWorkbench.svelte"
  - "playground/src/components/ExplorerWorkbench.svelte"
  - "playground/src/components/RoutingWorkbench.svelte"
  - "playground/src/components/UiPreviewPanel.svelte"
  - "playground/src/lib/debug.js"
  - "playground/src/lib/playgroundApi.js"
  - "playground/src/lib/uiBridge.js"
  - "playground/src/main.js"
  - "playground/tests/audit_workbench.spec.js"
  - "playground/tests/benchmark_workbench.spec.js"
  - "playground/tests/boundary_explorer_controls.spec.js"
  - "playground/tests/boundary_explorer_host_harness.spec.js"
  - "playground/tests/boundary_explorer_local_layers.spec.js"
  - "playground/tests/boundary_explorer_option_matrix.spec.js"
  - "playground/tests/bridge_security.spec.js"
  - "playground/tests/compact_windows/README.md"
  - "playground/tests/compact_windows/compact_matrix.spec.js"
  - "playground/tests/compact_windows/smoke.spec.js"
  - "playground/tests/compact_windows/support/compact_assertions.js"
  - "playground/tests/compact_windows/support/host_profiles.js"
  - "playground/tests/compact_windows/support/mcp_bridge.js"
  - "playground/tests/compact_windows/support/ui_paths.js"
  - "playground/tests/feature_inspector.spec.js"
  - "playground/tests/full/audit_full.spec.js"
  - "playground/tests/full/benchmarks_full.spec.js"
  - "playground/tests/full/debug_and_widgets_full.spec.js"
  - "playground/tests/full/explorer_full.spec.js"
  - "playground/tests/full/explorer_resources_full.spec.js"
  - "playground/tests/full/routing_full.spec.js"
  - "playground/tests/geography_selector.spec.js"
  - "playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-darwin.png"
  - "playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-linux.png"
  - "playground/tests/host_render.spec.js"
  - "playground/tests/live/live_smoke.spec.js"
  - "playground/tests/playground.spec.js"
  - "playground/tests/route_planner.spec.js"
  - "playground/tests/routing_workbench.spec.js"
  - "playground/tests/simple_map.spec.js"
  - "playground/tests/statistics_dashboard.spec.js"
  - "playground/tests/support/fixture_server.mjs"
  - "playground/tests/support/full_playground.js"
  - "playground/tests/support/live_smoke.js"
  - "playground/tests/support/mock_playground.js"
  - "playground/tests/ui_bridge.spec.js"
  - "playground/trials/fixtures/host_capability_profiles.json"
  - "playground/trials/fixtures/map_story_scenarios.json"
  - "playground/trials/fixtures/synthetic_osm_tile.png"
  - "playground/trials/tests/map_delivery_matrix.spec.js"
  - "playground/trials/tests/map_story_gallery.spec.js"
  - "playground/trials/tests/support/host_simulation.js"
  - "playground/vite.config.js"
source_commit: "004e7d4748422b44133399279803c8cb2b766a1c"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/app.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/index.html"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/package-lock.json"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/package.json"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.compact-matrix.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.compact.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.full.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.live.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.trials.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/App.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/AuditWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/BenchmarkWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/DebugWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/ExplorerWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/RoutingWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/UiPreviewPanel.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/lib/debug.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/lib/playgroundApi.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/lib/uiBridge.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/main.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/audit_workbench.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/benchmark_workbench.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/boundary_explorer_controls.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/boundary_explorer_host_harness.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/boundary_explorer_local_layers.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/boundary_explorer_option_matrix.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/bridge_security.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/README.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/compact_matrix.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/smoke.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/support/compact_assertions.js"
source_hashes:
  playground/app.py: "sha256:756203ad-e4c461a3-57bd10dc-ad734e91-5849464b-a46f2fc4-082d3888-c4220a50"
  playground/index.html: "sha256:761ae4e6-c9556f3a-25a15773-3933254d-59fa81f1-b877c6ca-31329157-49134125"
  playground/package-lock.json: "sha256:3ec73929-a176f10f-1c325b28-64411fc3-f9381ae7-433342f5-f294b0d1-b2fe60e9"
  playground/package.json: "sha256:8b1dabf7-afc744b9-f1a9bed1-763e397b-5bae5af8-8a3f69d2-433a39ff-ba39bfc6"
  playground/playwright.compact-matrix.config.js: "sha256:9e392b76-853cd3fd-bc011d92-6c099c57-4c5370b9-d0889004-6a0963e1-ae0c82c9"
  playground/playwright.compact.config.js: "sha256:42af0b17-a5a37b70-fce70e19-fe6e0b88-755f36c3-864ed1a3-9d1af8d9-243df807"
  playground/playwright.config.js: "sha256:d94ee3fa-a3a552a6-8b65d609-50b9747a-045a20e8-5a680188-75970d91-2eb0802a"
  playground/playwright.full.config.js: "sha256:93a498ac-07856ded-bc26e2fd-eee763b9-8ec12d2e-5dd3b3bc-cf9eda6f-3c443a36"
  playground/playwright.live.config.js: "sha256:d4c4cf33-71f46897-e220c001-8dbbb3ef-34e378f6-3810f987-6226bcfa-14504f44"
  playground/playwright.trials.config.js: "sha256:cd3854f2-d5da7b46-3633455c-76ba16e6-72421991-37dcde3c-a51a42f5-00e83bed"
  playground/src/App.svelte: "sha256:642b2d4b-a324b4e8-953092ce-6dad00c2-a85d7569-98bfc273-cf414e66-9138a569"
  playground/src/components/AuditWorkbench.svelte: "sha256:b997a37b-09cd9a3d-0d88fb1f-66994a90-829b2679-80b25012-451199f7-1d0ad95c"
  playground/src/components/BenchmarkWorkbench.svelte: "sha256:7e49c34b-47d591d2-98fcc72a-2cb04f63-f86dcc4e-c01c8746-8bb10280-118f4dc9"
  playground/src/components/DebugWorkbench.svelte: "sha256:2dad9a0c-67d05eab-3a9b47a6-77180ecc-213ca570-17b94ac0-1812c13f-99539fe1"
  playground/src/components/ExplorerWorkbench.svelte: "sha256:b7c07c76-34438587-212b4b01-294f34bc-a7350c29-3446be6f-46f95318-9289227c"
  playground/src/components/RoutingWorkbench.svelte: "sha256:55e2c27d-783b228c-c2670844-9a901dcc-45e3822d-e7896bad-389c47dd-5aa102dd"
  playground/src/components/UiPreviewPanel.svelte: "sha256:15d89b5f-873aecd4-88ee7b38-18dd5401-c65e0bfd-8ad6fe9b-78300980-39514183"
  playground/src/lib/debug.js: "sha256:cc08be67-85646b0d-f2c0fa5e-513c9bcd-b31dc200-e6e520e4-32ed560a-ea3eaa61"
  playground/src/lib/playgroundApi.js: "sha256:8aa5d90a-6ba75cf3-057241b5-bdda9d4e-b02714ce-d16b8f68-ca6d3cee-74e85571"
  playground/src/lib/uiBridge.js: "sha256:e7ab8062-24f63d69-6d7eb7c8-3b96ef6e-7d575365-7ced2d00-4ccb5f00-3284699a"
  playground/src/main.js: "sha256:71ce757f-954e3b75-fec1e4be-45ec3033-f67a08d2-04d26a9d-81b4f382-c46e0fd4"
  playground/tests/audit_workbench.spec.js: "sha256:4e7d6fae-95ee4f69-9dd65b8a-41f7d8c2-8217b259-3cd730b3-e5866038-790f613c"
  playground/tests/benchmark_workbench.spec.js: "sha256:bdff06d1-b4e3db7c-9894227b-5f2dc03d-b17a1f3b-27986aa9-fd062cba-8d31df32"
  playground/tests/boundary_explorer_controls.spec.js: "sha256:83cbebaa-28aa8cd7-5758045a-3e86f0b7-c6bdbde7-6ef26312-b241bb6f-17992448"
  playground/tests/boundary_explorer_host_harness.spec.js: "sha256:66e1c378-4eeed7de-0235b538-830fe0aa-2add4fc9-d138e058-fb29f4cc-b47debe4"
  playground/tests/boundary_explorer_local_layers.spec.js: "sha256:5345a8de-bae4f859-0bc8bf68-a5ecfe1d-e7c34c61-11d3805e-aa6ced50-d1915dd7"
  playground/tests/boundary_explorer_option_matrix.spec.js: "sha256:b84c48ae-9b532c92-4decd4f9-5028586a-6e1e9681-5826d8a8-637a8a15-a7c697b6"
  playground/tests/bridge_security.spec.js: "sha256:1837785b-277939a2-addf5a57-680753c3-ffadd890-5c4bb26c-f3432f4c-39c7067a"
  playground/tests/compact_windows/README.md: "sha256:058b9dc4-fa30d945-97a56578-e78b1b2c-cc350f87-6a9c6cf6-0d2cf258-dee1db23"
  playground/tests/compact_windows/compact_matrix.spec.js: "sha256:801bb816-188454f3-59d49fe0-1eb1aaa5-23d02895-1d1532fe-5eb61b04-e3b738be"
  playground/tests/compact_windows/smoke.spec.js: "sha256:09f47f81-41f73db7-7cec8d93-bb136bc7-ce6384d9-577ab910-a7349966-029a23a0"
  playground/tests/compact_windows/support/compact_assertions.js: "sha256:f3f7312d-659d1390-abb42598-0c88db4d-e62ca857-54f1ab2f-36478757-0e952580"
generated_at: "2026-04-06T14:09:00Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-04-06T14:09:00Z"
---
# Playground and Browser Tests

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 64

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `playground/app.py` | Legacy FastAPI stub for the playground UI. The active playground is the Svelte + Vite app under `playground/`. Run `npm  | 2025-08-20 | 2026-01-28 | `tests/conftest.py`, `tests/evaluation/audit_logger.py`, `tests/evaluation/harness.py`, `tests/evaluation/live_capture.py` |
| `playground/index.html` | MCP Geo Playground | 2026-01-25 | 2026-01-28 | - |
| `playground/package-lock.json` | JSON object keys: lockfileVersion, name, packages, requires, version | 2026-01-25 | 2026-03-16 | - |
| `playground/package.json` | JSON object keys: dependencies, devDependencies, engines, name, overrides, private, scripts, type | 2026-01-25 | 2026-03-11 | `tests/__init__.py`, `tests/test_docx_hygiene.py`, `tests/test_evaluation_harness_full.py`, `tests/test_os_downloads_tools.py` |
| `playground/playwright.compact-matrix.config.js` | import { defineConfig, devices } from "@playwright/test"; | 2026-03-01 | 2026-03-01 | - |
| `playground/playwright.compact.config.js` | import { defineConfig, devices } from "@playwright/test"; | 2026-03-01 | 2026-03-01 | - |
| `playground/playwright.config.js` | import { defineConfig } from "@playwright/test"; | 2026-01-25 | 2026-02-11 | - |
| `playground/playwright.full.config.js` | import { defineConfig, devices } from "@playwright/test"; | 2026-03-11 | 2026-03-12 | - |
| `playground/playwright.live.config.js` | import { defineConfig, devices } from "@playwright/test"; | 2026-03-11 | 2026-03-17 | - |
| `playground/playwright.trials.config.js` | import { defineConfig, devices } from "@playwright/test"; | 2026-02-13 | 2026-02-22 | - |
| `playground/src/App.svelte` | <script> | 2026-01-25 | 2026-03-13 | - |
| `playground/src/components/AuditWorkbench.svelte` | <script> | 2026-03-11 | 2026-03-11 | - |
| `playground/src/components/BenchmarkWorkbench.svelte` | <script> | 2026-03-11 | 2026-03-11 | - |
| `playground/src/components/DebugWorkbench.svelte` | <script> | 2026-03-11 | 2026-03-11 | - |
| `playground/src/components/ExplorerWorkbench.svelte` | <script> | 2026-03-11 | 2026-03-12 | - |
| `playground/src/components/RoutingWorkbench.svelte` | <script> | 2026-03-11 | 2026-03-11 | - |
| `playground/src/components/UiPreviewPanel.svelte` | <script> | 2026-03-11 | 2026-03-11 | - |
| `playground/src/lib/debug.js` | export const DEBUG_LOG_LIMIT = 150; | 2026-03-11 | 2026-03-11 | - |
| `playground/src/lib/playgroundApi.js` | import { Client } from "@modelcontextprotocol/sdk/client/index.js"; | 2026-03-11 | 2026-03-11 | - |
| `playground/src/lib/uiBridge.js` | export const UI_PROTOCOL_VERSION = "2026-01-26"; | 2026-03-11 | 2026-03-14 | - |
| `playground/src/main.js` | import { mount } from "svelte"; | 2026-01-25 | 2026-03-11 | - |
| `playground/tests/audit_workbench.spec.js` | import { expect, test } from "@playwright/test"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/benchmark_workbench.spec.js` | import { expect, test } from "@playwright/test"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/boundary_explorer_controls.spec.js` | import { test, expect } from "@playwright/test"; | 2026-03-01 | 2026-03-01 | - |
| `playground/tests/boundary_explorer_host_harness.spec.js` | import { test, expect } from "@playwright/test"; | 2026-02-23 | 2026-03-01 | - |
| `playground/tests/boundary_explorer_local_layers.spec.js` | import { test, expect } from "@playwright/test"; | 2026-02-11 | 2026-03-12 | - |
| `playground/tests/boundary_explorer_option_matrix.spec.js` | import { test, expect } from "@playwright/test"; | 2026-03-01 | 2026-03-01 | - |
| `playground/tests/bridge_security.spec.js` | import { expect, test } from "@playwright/test"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/compact_windows/README.md` | This directory is the dedicated unattended test harness for compact-host MCP UI behavior. Current status: - CW-7 complet | 2026-03-01 | 2026-03-03 | `tests/test_generate_mcp_geo_analytical_index.py`, `tests/test_generate_mcp_geo_functionality_showcase.py`, `tests/test_obsidian_kb.py` |
| `playground/tests/compact_windows/compact_matrix.spec.js` | import { test, expect } from "@playwright/test"; | 2026-03-01 | 2026-03-03 | - |
| `playground/tests/compact_windows/smoke.spec.js` | import { test, expect } from "@playwright/test"; | 2026-03-01 | 2026-03-12 | - |
| `playground/tests/compact_windows/support/compact_assertions.js` | import { expect } from "@playwright/test"; | 2026-03-02 | 2026-03-03 | - |
| `playground/tests/compact_windows/support/host_profiles.js` | export const HOST_PROFILES = { | 2026-03-01 | 2026-03-06 | - |
| `playground/tests/compact_windows/support/mcp_bridge.js` | function normalizeHostContext(input) { | 2026-03-01 | 2026-03-02 | - |
| `playground/tests/compact_windows/support/ui_paths.js` | import path from "path"; | 2026-03-01 | 2026-03-01 | - |
| `playground/tests/feature_inspector.spec.js` | import { test, expect } from "@playwright/test"; | 2026-03-01 | 2026-03-01 | - |
| `playground/tests/full/audit_full.spec.js` | import { connectPlayground, expect, openWorkbenchTab, test } from "../support/full_playground.js"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/full/benchmarks_full.spec.js` | import { connectPlayground, expect, openWorkbenchTab, test } from "../support/full_playground.js"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/full/debug_and_widgets_full.spec.js` | import { connectPlayground, expect, loadHostedWidget, openWorkbenchTab, test } from "../support/full_playground.js"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/full/explorer_full.spec.js` | import { connectPlayground, expect, loadHostedWidget, openWorkbenchTab, test } from "../support/full_playground.js"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/full/explorer_resources_full.spec.js` | import { connectPlayground, expect, openWorkbenchTab, test } from "../support/full_playground.js"; | 2026-03-13 | 2026-03-13 | - |
| `playground/tests/full/routing_full.spec.js` | import { connectPlayground, expect, openWorkbenchTab, selectScenario, test } from "../support/full_playground.js"; | 2026-03-11 | 2026-03-13 | - |
| `playground/tests/geography_selector.spec.js` | import { test, expect } from "@playwright/test"; | 2026-01-29 | 2026-03-01 | - |
| `playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-darwin.png` | Binary artifact | 2026-02-11 | 2026-02-11 | - |
| `playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-linux.png` | Binary artifact | 2026-02-09 | 2026-02-09 | - |
| `playground/tests/host_render.spec.js` | import { test, expect } from "@playwright/test"; | 2026-02-11 | 2026-02-11 | - |
| `playground/tests/live/live_smoke.spec.js` | import { createAuditSmokeSession, getLiveRoutePreflight } from "../support/live_smoke.js"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/playground.spec.js` | import { expect, test } from "@playwright/test"; | 2026-01-25 | 2026-03-11 | - |
| `playground/tests/route_planner.spec.js` | import { test, expect } from "@playwright/test"; | 2026-03-01 | 2026-03-10 | - |
| `playground/tests/routing_workbench.spec.js` | import { expect, test } from "@playwright/test"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/simple_map.spec.js` | import { test, expect } from "@playwright/test"; | 2026-03-01 | 2026-03-01 | - |
| `playground/tests/statistics_dashboard.spec.js` | import { test, expect } from "@playwright/test"; | 2026-03-01 | 2026-03-01 | - |
| `playground/tests/support/fixture_server.mjs` | import { readFileSync } from "fs"; | 2026-03-11 | 2026-03-12 | - |
| `playground/tests/support/full_playground.js` | import { expect, test as base } from "@playwright/test"; | 2026-03-11 | 2026-03-13 | - |
| `playground/tests/support/live_smoke.js` | import os from "os"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/support/mock_playground.js` | import fs from "fs"; | 2026-03-11 | 2026-03-11 | - |
| `playground/tests/ui_bridge.spec.js` | import { expect, test } from "@playwright/test"; | 2026-03-12 | 2026-03-14 | - |
| `playground/trials/fixtures/host_capability_profiles.json` | JSON object keys: profiles, version | 2026-02-14 | 2026-03-06 | `tests/test_map_trials_host_simulation_profiles.py` |
| `playground/trials/fixtures/map_story_scenarios.json` | JSON object keys: stories, version | 2026-02-17 | 2026-02-17 | - |
| `playground/trials/fixtures/synthetic_osm_tile.png` | Binary artifact | 2026-02-13 | 2026-02-13 | - |
| `playground/trials/tests/map_delivery_matrix.spec.js` | import { test, expect } from "@playwright/test"; | 2026-02-13 | 2026-03-12 | - |
| `playground/trials/tests/map_story_gallery.spec.js` | import { test, expect } from "@playwright/test"; | 2026-02-17 | 2026-02-22 | - |
| `playground/trials/tests/support/host_simulation.js` | import fs from "fs"; | 2026-02-14 | 2026-02-22 | - |
| `playground/vite.config.js` | import { svelte } from "@sveltejs/vite-plugin-svelte"; | 2026-01-25 | 2026-03-14 | - |

## Visible Headings

- `playground/tests/compact_windows/README.md`: `Compact Windows Test Suite`

## Binary Artifacts

- `playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-darwin.png` (12.9 KB): [Pinned source](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-darwin.png)
- `playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-linux.png` (10.3 KB): [Pinned source](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-linux.png)
- `playground/trials/fixtures/synthetic_osm_tile.png` (2.3 KB): [Pinned source](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/trials/fixtures/synthetic_osm_tile.png)

## Pinned Sources

- [`playground/app.py`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/app.py)
- [`playground/index.html`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/index.html)
- [`playground/package-lock.json`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/package-lock.json)
- [`playground/package.json`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/package.json)
- [`playground/playwright.compact-matrix.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.compact-matrix.config.js)
- [`playground/playwright.compact.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.compact.config.js)
- [`playground/playwright.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.config.js)
- [`playground/playwright.full.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.full.config.js)
- [`playground/playwright.live.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.live.config.js)
- [`playground/playwright.trials.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/playwright.trials.config.js)
- [`playground/src/App.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/App.svelte)
- [`playground/src/components/AuditWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/AuditWorkbench.svelte)
- [`playground/src/components/BenchmarkWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/BenchmarkWorkbench.svelte)
- [`playground/src/components/DebugWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/DebugWorkbench.svelte)
- [`playground/src/components/ExplorerWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/ExplorerWorkbench.svelte)
- [`playground/src/components/RoutingWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/RoutingWorkbench.svelte)
- [`playground/src/components/UiPreviewPanel.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/components/UiPreviewPanel.svelte)
- [`playground/src/lib/debug.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/lib/debug.js)
- [`playground/src/lib/playgroundApi.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/lib/playgroundApi.js)
- [`playground/src/lib/uiBridge.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/lib/uiBridge.js)
- [`playground/src/main.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/src/main.js)
- [`playground/tests/audit_workbench.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/audit_workbench.spec.js)
- [`playground/tests/benchmark_workbench.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/benchmark_workbench.spec.js)
- [`playground/tests/boundary_explorer_controls.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/boundary_explorer_controls.spec.js)
- [`playground/tests/boundary_explorer_host_harness.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/boundary_explorer_host_harness.spec.js)
- [`playground/tests/boundary_explorer_local_layers.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/boundary_explorer_local_layers.spec.js)
- [`playground/tests/boundary_explorer_option_matrix.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/boundary_explorer_option_matrix.spec.js)
- [`playground/tests/bridge_security.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/bridge_security.spec.js)
- [`playground/tests/compact_windows/README.md`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/README.md)
- [`playground/tests/compact_windows/compact_matrix.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/compact_matrix.spec.js)
- [`playground/tests/compact_windows/smoke.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/smoke.spec.js)
- [`playground/tests/compact_windows/support/compact_assertions.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/support/compact_assertions.js)
- [`playground/tests/compact_windows/support/host_profiles.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/support/host_profiles.js)
- [`playground/tests/compact_windows/support/mcp_bridge.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/support/mcp_bridge.js)
- [`playground/tests/compact_windows/support/ui_paths.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/compact_windows/support/ui_paths.js)
- [`playground/tests/feature_inspector.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/feature_inspector.spec.js)
- [`playground/tests/full/audit_full.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/full/audit_full.spec.js)
- [`playground/tests/full/benchmarks_full.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/full/benchmarks_full.spec.js)
- [`playground/tests/full/debug_and_widgets_full.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/full/debug_and_widgets_full.spec.js)
- [`playground/tests/full/explorer_full.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/004e7d4748422b44133399279803c8cb2b766a1c/playground/tests/full/explorer_full.spec.js)
