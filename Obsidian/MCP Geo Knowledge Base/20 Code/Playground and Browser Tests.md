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
source_commit: "bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/app.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/index.html"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/package-lock.json"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/package.json"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.compact-matrix.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.compact.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.full.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.live.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.trials.config.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/App.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/AuditWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/BenchmarkWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/DebugWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/ExplorerWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/RoutingWorkbench.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/UiPreviewPanel.svelte"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/lib/debug.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/lib/playgroundApi.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/lib/uiBridge.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/main.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/audit_workbench.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/benchmark_workbench.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/boundary_explorer_controls.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/boundary_explorer_host_harness.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/boundary_explorer_local_layers.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/boundary_explorer_option_matrix.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/bridge_security.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/README.md"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/compact_matrix.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/smoke.spec.js"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/support/compact_assertions.js"
source_hashes:
  playground/app.py: "756203ade4c461a357bd10dcad734e915849464ba46f2fc4082d3888c4220a50"
  playground/index.html: "761ae4e6c9556f3a25a157733933254d59fa81f1b877c6ca3132915749134125"
  playground/package-lock.json: "3ec73929a176f10f1c325b2864411fc3f9381ae7433342f5f294b0d1b2fe60e9"
  playground/package.json: "8b1dabf7afc744b9f1a9bed1763e397b5bae5af88a3f69d2433a39ffba39bfc6"
  playground/playwright.compact-matrix.config.js: "9e392b76853cd3fdbc011d926c099c574c5370b9d08890046a0963e1ae0c82c9"
  playground/playwright.compact.config.js: "42af0b17a5a37b70fce70e19fe6e0b88755f36c3864ed1a39d1af8d9243df807"
  playground/playwright.config.js: "d94ee3faa3a552a68b65d60950b9747a045a20e85a68018875970d912eb0802a"
  playground/playwright.full.config.js: "93a498ac07856dedbc26e2fdeee763b98ec12d2e5dd3b3bccf9eda6f3c443a36"
  playground/playwright.live.config.js: "d4c4cf3371f46897e220c0018dbbb3ef34e378f63810f9876226bcfa14504f44"
  playground/playwright.trials.config.js: "cd3854f2d5da7b463633455c76ba16e67242199137dcde3ca51a42f500e83bed"
  playground/src/App.svelte: "642b2d4ba324b4e8953092ce6dad00c2a85d756998bfc273cf414e669138a569"
  playground/src/components/AuditWorkbench.svelte: "b997a37b09cd9a3d0d88fb1f66994a90829b267980b25012451199f71d0ad95c"
  playground/src/components/BenchmarkWorkbench.svelte: "7e49c34b47d591d298fcc72a2cb04f63f86dcc4ec01c87468bb10280118f4dc9"
  playground/src/components/DebugWorkbench.svelte: "2dad9a0c67d05eab3a9b47a677180ecc213ca57017b94ac01812c13f99539fe1"
  playground/src/components/ExplorerWorkbench.svelte: "b7c07c7634438587212b4b01294f34bca7350c293446be6f46f953189289227c"
  playground/src/components/RoutingWorkbench.svelte: "55e2c27d783b228cc26708449a901dcc45e3822de7896bad389c47dd5aa102dd"
  playground/src/components/UiPreviewPanel.svelte: "15d89b5f873aecd488ee7b3818dd5401c65e0bfd8ad6fe9b7830098039514183"
  playground/src/lib/debug.js: "cc08be6785646b0df2c0fa5e513c9bcdb31dc200e6e520e432ed560aea3eaa61"
  playground/src/lib/playgroundApi.js: "8aa5d90a6ba75cf3057241b5bdda9d4eb02714ced16b8f68ca6d3cee74e85571"
  playground/src/lib/uiBridge.js: "e7ab806224f63d696d7eb7c83b96ef6e7d5753657ced2d004ccb5f003284699a"
  playground/src/main.js: "71ce757f954e3b75fec1e4be45ec3033f67a08d204d26a9d81b4f382c46e0fd4"
  playground/tests/audit_workbench.spec.js: "4e7d6fae95ee4f699dd65b8a41f7d8c28217b2593cd730b3e5866038790f613c"
  playground/tests/benchmark_workbench.spec.js: "bdff06d1b4e3db7c9894227b5f2dc03db17a1f3b27986aa9fd062cba8d31df32"
  playground/tests/boundary_explorer_controls.spec.js: "83cbebaa28aa8cd75758045a3e86f0b7c6bdbde76ef26312b241bb6f17992448"
  playground/tests/boundary_explorer_host_harness.spec.js: "66e1c3784eeed7de0235b538830fe0aa2add4fc9d138e058fb29f4ccb47debe4"
  playground/tests/boundary_explorer_local_layers.spec.js: "5345a8debae4f8590bc8bf68a5ecfe1de7c34c6111d3805eaa6ced50d1915dd7"
  playground/tests/boundary_explorer_option_matrix.spec.js: "b84c48ae9b532c924decd4f95028586a6e1e96815826d8a8637a8a15a7c697b6"
  playground/tests/bridge_security.spec.js: "1837785b277939a2addf5a57680753c3ffadd8905c4bb26cf3432f4c39c7067a"
  playground/tests/compact_windows/README.md: "058b9dc4fa30d94597a56578e78b1b2ccc350f876a9c6cf60d2cf258dee1db23"
  playground/tests/compact_windows/compact_matrix.spec.js: "801bb816188454f359d49fe01eb1aaa523d028951d1532fe5eb61b04e3b738be"
  playground/tests/compact_windows/smoke.spec.js: "09f47f8141f73db77cec8d93bb136bc7ce6384d9577ab910a7349966029a23a0"
  playground/tests/compact_windows/support/compact_assertions.js: "f3f7312d659d1390abb425980c88db4de62ca85754f1ab2f364787570e952580"
generated_at: "2026-04-06T09:00:35Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-04-06T09:00:35Z"
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
| `playground/tests/compact_windows/README.md` | This directory is the dedicated unattended test harness for compact-host MCP UI behavior. Current status: - CW-7 complet | 2026-03-01 | 2026-03-03 | `tests/test_generate_mcp_geo_analytical_index.py`, `tests/test_generate_mcp_geo_functionality_showcase.py` |
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

- `playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-darwin.png` (12.9 KB): [Pinned source](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-darwin.png)
- `playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-linux.png` (10.3 KB): [Pinned source](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/geography_selector.spec.js-snapshots/geography-selector-map-linux.png)
- `playground/trials/fixtures/synthetic_osm_tile.png` (2.3 KB): [Pinned source](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/trials/fixtures/synthetic_osm_tile.png)

## Pinned Sources

- [`playground/app.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/app.py)
- [`playground/index.html`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/index.html)
- [`playground/package-lock.json`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/package-lock.json)
- [`playground/package.json`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/package.json)
- [`playground/playwright.compact-matrix.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.compact-matrix.config.js)
- [`playground/playwright.compact.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.compact.config.js)
- [`playground/playwright.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.config.js)
- [`playground/playwright.full.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.full.config.js)
- [`playground/playwright.live.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.live.config.js)
- [`playground/playwright.trials.config.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/playwright.trials.config.js)
- [`playground/src/App.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/App.svelte)
- [`playground/src/components/AuditWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/AuditWorkbench.svelte)
- [`playground/src/components/BenchmarkWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/BenchmarkWorkbench.svelte)
- [`playground/src/components/DebugWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/DebugWorkbench.svelte)
- [`playground/src/components/ExplorerWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/ExplorerWorkbench.svelte)
- [`playground/src/components/RoutingWorkbench.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/RoutingWorkbench.svelte)
- [`playground/src/components/UiPreviewPanel.svelte`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/components/UiPreviewPanel.svelte)
- [`playground/src/lib/debug.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/lib/debug.js)
- [`playground/src/lib/playgroundApi.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/lib/playgroundApi.js)
- [`playground/src/lib/uiBridge.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/lib/uiBridge.js)
- [`playground/src/main.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/src/main.js)
- [`playground/tests/audit_workbench.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/audit_workbench.spec.js)
- [`playground/tests/benchmark_workbench.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/benchmark_workbench.spec.js)
- [`playground/tests/boundary_explorer_controls.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/boundary_explorer_controls.spec.js)
- [`playground/tests/boundary_explorer_host_harness.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/boundary_explorer_host_harness.spec.js)
- [`playground/tests/boundary_explorer_local_layers.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/boundary_explorer_local_layers.spec.js)
- [`playground/tests/boundary_explorer_option_matrix.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/boundary_explorer_option_matrix.spec.js)
- [`playground/tests/bridge_security.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/bridge_security.spec.js)
- [`playground/tests/compact_windows/README.md`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/README.md)
- [`playground/tests/compact_windows/compact_matrix.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/compact_matrix.spec.js)
- [`playground/tests/compact_windows/smoke.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/smoke.spec.js)
- [`playground/tests/compact_windows/support/compact_assertions.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/support/compact_assertions.js)
- [`playground/tests/compact_windows/support/host_profiles.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/support/host_profiles.js)
- [`playground/tests/compact_windows/support/mcp_bridge.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/support/mcp_bridge.js)
- [`playground/tests/compact_windows/support/ui_paths.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/compact_windows/support/ui_paths.js)
- [`playground/tests/feature_inspector.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/feature_inspector.spec.js)
- [`playground/tests/full/audit_full.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/full/audit_full.spec.js)
- [`playground/tests/full/benchmarks_full.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/full/benchmarks_full.spec.js)
- [`playground/tests/full/debug_and_widgets_full.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/full/debug_and_widgets_full.spec.js)
- [`playground/tests/full/explorer_full.spec.js`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/playground/tests/full/explorer_full.spec.js)
