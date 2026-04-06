---
title: "Test and Validation Surface"
kb_kind: "code_family"
source_paths:
  - "tests/__init__.py"
  - "tests/audit_test_utils.py"
  - "tests/conftest.py"
  - "tests/evaluation/__init__.py"
  - "tests/evaluation/audit_logger.py"
  - "tests/evaluation/evaluation_results.audit.txt"
  - "tests/evaluation/evaluation_results.benchmark.txt"
  - "tests/evaluation/evaluation_results.json"
  - "tests/evaluation/harness.py"
  - "tests/evaluation/live_capture.py"
  - "tests/evaluation/logs/audit/047c3949.txt"
  - "tests/evaluation/logs/audit/08eea8b1.txt"
  - "tests/evaluation/logs/audit/13ad9383.txt"
  - "tests/evaluation/logs/audit/15cb80c1.txt"
  - "tests/evaluation/logs/audit/172ff2f7.txt"
  - "tests/evaluation/logs/audit/19f40194.txt"
  - "tests/evaluation/logs/audit/1f415869.txt"
  - "tests/evaluation/logs/audit/2692a326.txt"
  - "tests/evaluation/logs/audit/271c9a92.txt"
  - "tests/evaluation/logs/audit/328c0257.txt"
  - "tests/evaluation/logs/audit/3628f5d1.txt"
  - "tests/evaluation/logs/audit/393a6d69.txt"
  - "tests/evaluation/logs/audit/3d3c1f52.txt"
  - "tests/evaluation/logs/audit/464a7d6a.txt"
  - "tests/evaluation/logs/audit/49e6e04e.txt"
  - "tests/evaluation/logs/audit/4e4bc6a9.txt"
  - "tests/evaluation/logs/audit/4f7c55c0.txt"
  - "tests/evaluation/logs/audit/4fc811e8.txt"
  - "tests/evaluation/logs/audit/4ffd83a6.txt"
  - "tests/evaluation/logs/audit/52a9f148.txt"
  - "tests/evaluation/logs/audit/53b72503.txt"
  - "tests/evaluation/logs/audit/5671006d.txt"
  - "tests/evaluation/logs/audit/58f6acfe.txt"
  - "tests/evaluation/logs/audit/5d58b670.txt"
  - "tests/evaluation/logs/audit/612fbdcf.txt"
  - "tests/evaluation/logs/audit/6a554f33.txt"
  - "tests/evaluation/logs/audit/70b26fc5.txt"
  - "tests/evaluation/logs/audit/73f6a027.txt"
  - "tests/evaluation/logs/audit/7c2d3745.txt"
  - "tests/evaluation/logs/audit/90599991.txt"
  - "tests/evaluation/logs/audit/90801c90.txt"
  - "tests/evaluation/logs/audit/91896e44.txt"
  - "tests/evaluation/logs/audit/927587df.txt"
  - "tests/evaluation/logs/audit/962f1bf1.txt"
  - "tests/evaluation/logs/audit/96e7da33.txt"
  - "tests/evaluation/logs/audit/992f80bb.txt"
  - "tests/evaluation/logs/audit/9c117f41.txt"
  - "tests/evaluation/logs/audit/9cb4ff1a.txt"
  - "tests/evaluation/logs/audit/9cf7bac5.txt"
  - "tests/evaluation/logs/audit/9d047de2.txt"
  - "tests/evaluation/logs/audit/a260375d.txt"
  - "tests/evaluation/logs/audit/a5728534.txt"
  - "tests/evaluation/logs/audit/ad63b2e9.txt"
  - "tests/evaluation/logs/audit/b7285093.txt"
  - "tests/evaluation/logs/audit/b8eb2a07.txt"
  - "tests/evaluation/logs/audit/b9ad7042.txt"
  - "tests/evaluation/logs/audit/ba5f2403.txt"
  - "tests/evaluation/logs/audit/bcc1d8ce.txt"
  - "tests/evaluation/logs/audit/c2dad4c0.txt"
  - "tests/evaluation/logs/audit/c3ad94dd.txt"
  - "tests/evaluation/logs/audit/c5ce1ef9.txt"
  - "tests/evaluation/logs/audit/c656ba2c.txt"
  - "tests/evaluation/logs/audit/cab0fd87.txt"
  - "tests/evaluation/logs/audit/d07ef1fa.txt"
  - "tests/evaluation/logs/audit/d39da7dd.txt"
  - "tests/evaluation/logs/audit/d48a07fb.txt"
  - "tests/evaluation/logs/audit/d757dce9.txt"
  - "tests/evaluation/logs/audit/d82aacd4.txt"
  - "tests/evaluation/logs/audit/d91e4c3b.txt"
  - "tests/evaluation/logs/audit/de63e4c3.txt"
  - "tests/evaluation/logs/audit/dfbafeae.txt"
  - "tests/evaluation/logs/audit/dfcc5156.txt"
  - "tests/evaluation/logs/audit/e004a327.txt"
  - "tests/evaluation/logs/audit/e3f55d98.txt"
  - "tests/evaluation/logs/audit/edbc973f.txt"
  - "tests/evaluation/logs/audit/fd4d6d98.txt"
  - "tests/evaluation/questions.py"
  - "tests/evaluation/rubric.py"
  - "tests/fixtures/council_tax/ls14ap_no_results.html"
  - "tests/fixtures/council_tax/m11ae_results.html"
  - "tests/fixtures/council_tax/sw1a1aa_results.html"
  - "tests/fixtures/council_tax/yo17hp_results.html"
  - "tests/fixtures/council_tax_band_gold.json"
  - "tests/fixtures/psr_peat_floor_question.json"
  - "tests/helpers.py"
  - "tests/outputs/CV312JF-oa-example.html"
  - "tests/outputs/northolt.html"
  - "tests/test_accessors.py"
  - "tests/test_admin_lookup.py"
  - "tests/test_admin_lookup_cache.py"
  - "tests/test_admin_lookup_extended.py"
  - "tests/test_admin_lookup_live.py"
  - "tests/test_admin_lookup_live_internals.py"
  - "tests/test_audit_api.py"
  - "tests/test_audit_normalise.py"
  - "tests/test_audit_pack_builder.py"
  - "tests/test_boundary_cache.py"
  - "tests/test_boundary_pipeline_variant_policy.py"
  - "tests/test_check_codex_startup_scope.py"
  - "tests/test_check_lmr_host4.py"
  - "tests/test_circuit_breaker.py"
  - "tests/test_client_capabilities.py"
  - "tests/test_codex_long_horizon_summary.py"
  - "tests/test_codex_mcp_local.py"
  - "tests/test_config_secret_file.py"
  - "tests/test_council_tax_band.py"
  - "tests/test_council_tax_gold_eval.py"
  - "tests/test_coverage_guardrails.py"
  - "tests/test_cross_platform_container_policy.py"
  - "tests/test_dataset_cache.py"
  - "tests/test_debug_errors.py"
  - "tests/test_devcontainer_codex_setup.py"
  - "tests/test_docx_hygiene.py"
  - "tests/test_elicitation_forms.py"
  - "tests/test_epic_b_validation.py"
  - "tests/test_error_taxonomy.py"
  - "tests/test_evaluation_audit_rate_limits.py"
  - "tests/test_evaluation_expected_errors.py"
  - "tests/test_evaluation_harness_full.py"
  - "tests/test_evaluation_harness_live_api.py"
  - "tests/test_generate_mcp_geo_analytical_index.py"
  - "tests/test_generate_mcp_geo_functionality_showcase.py"
  - "tests/test_golden_scenarios.py"
  - "tests/test_health.py"
  - "tests/test_host_benchmark.py"
  - "tests/test_http_endpoint_matrix.py"
  - "tests/test_http_transport_coverage_more.py"
  - "tests/test_landis_ingest.py"
  - "tests/test_landis_release_reconciliation.py"
  - "tests/test_landis_resources.py"
  - "tests/test_landis_tools.py"
  - "tests/test_live_missing_tools_probe.py"
  - "tests/test_logging_redaction.py"
  - "tests/test_main_observability_branches.py"
  - "tests/test_map_trials_export_notebook_scenario_pack.py"
  - "tests/test_map_trials_host_simulation_profiles.py"
  - "tests/test_map_trials_quality_checks.py"
  - "tests/test_map_trials_summary.py"
  - "tests/test_map_trials_verify.py"
  - "tests/test_maps_proxy.py"
  - "tests/test_mcp_client_if_none_match.py"
  - "tests/test_mcp_client_resources_get.py"
  - "tests/test_mcp_docker_local.py"
  - "tests/test_mcp_http.py"
  - "tests/test_mcp_stdio_trace_proxy.py"
  - "tests/test_middleware_exception.py"
  - "tests/test_nomis_common.py"
  - "tests/test_nomis_data.py"
  - "tests/test_ons_catalog_snapshot.py"
  - "tests/test_ons_catalog_validate_script.py"
  - "tests/test_ons_catalog_validator.py"
  - "tests/test_ons_codes_live.py"
  - "tests/test_ons_codes_unit.py"
  - "tests/test_ons_common.py"
  - "tests/test_ons_common_paging.py"
  - "tests/test_ons_data.py"
  - "tests/test_ons_data_internal.py"
  - "tests/test_ons_dimensions.py"
  - "tests/test_ons_dimensions_live.py"
  - "tests/test_ons_filter_formats.py"
  - "tests/test_ons_geo.py"
  - "tests/test_ons_geo_cache.py"
  - "tests/test_ons_geo_cache_refresh.py"
  - "tests/test_ons_new_tools.py"
  - "tests/test_ons_search_fallback.py"
  - "tests/test_ons_select.py"
  - "tests/test_os_apps_log_event.py"
  - "tests/test_os_apps_tools.py"
  - "tests/test_os_auth_errors.py"
  - "tests/test_os_catalog_snapshot.py"
  - "tests/test_os_common.py"
  - "tests/test_os_delivery.py"
  - "tests/test_os_downloads_tools.py"
  - "tests/test_os_features_collections.py"
  - "tests/test_os_features_helpers.py"
  - "tests/test_os_invalid_inputs.py"
  - "tests/test_os_landscape.py"
  - "tests/test_os_map_tools.py"
  - "tests/test_os_mcp_descriptor.py"
  - "tests/test_os_mcp_internals.py"
  - "tests/test_os_mcp_route_query.py"
  - "tests/test_os_names_success.py"
  - "tests/test_os_new_capability_tools.py"
  - "tests/test_os_no_api_key.py"
  - "tests/test_os_offline_tools.py"
  - "tests/test_os_peat.py"
  - "tests/test_os_places_by_postcode_success.py"
  - "tests/test_os_places_enrichment.py"
  - "tests/test_os_places_extra_more_success.py"
  - "tests/test_os_places_extra_success.py"
  - "tests/test_os_places_new_tools.py"
  - "tests/test_os_poi.py"
  - "tests/test_os_qgis_tools.py"
  - "tests/test_os_retry_errors.py"
  - "tests/test_os_route_tools.py"
  - "tests/test_os_timeout.py"
  - "tests/test_os_tools_normalization.py"
  - "tests/test_owasp_mcp_validation.py"
  - "tests/test_placeholder_tool.py"
  - "tests/test_playground.py"
  - "tests/test_playground_events.py"
  - "tests/test_postcode_tool.py"
  - "tests/test_prompts.py"
  - "tests/test_protocol_versions.py"
  - "tests/test_psr_peat_e2e.py"
  - "tests/test_rate_limit_assessor.py"
  - "tests/test_rate_limit_metrics.py"
  - "tests/test_repo_extent_complexity_report.py"
  - "tests/test_resource_catalog.py"
  - "tests/test_resource_fallback.py"
  - "tests/test_resources_code_lists.py"
  - "tests/test_resources_data_catalog.py"
  - "tests/test_resources_etag.py"
  - "tests/test_resources_ons_observations.py"
  - "tests/test_resources_paging_filtering.py"
  - "tests/test_resources_provenance_headers.py"
  - "tests/test_resources_ui_skills.py"
  - "tests/test_route_graph.py"
  - "tests/test_route_graph_integration.py"
  - "tests/test_route_graph_pipeline.py"
  - "tests/test_route_planning.py"
  - "tests/test_run_local_tool.py"
  - "tests/test_security.py"
  - "tests/test_server_landis.py"
  - "tests/test_spec_tool_operability_coverage.py"
  - "tests/test_stakeholder_benchmark_pack.py"
  - "tests/test_stakeholder_live_run.py"
  - "tests/test_stdio_adapter.py"
  - "tests/test_stdio_adapter_branches.py"
  - "tests/test_stdio_adapter_coverage_more.py"
  - "tests/test_stdio_adapter_direct.py"
  - "tests/test_stdio_adapter_main.py"
  - "tests/test_stdio_resources_etag.py"
  - "tests/test_stdio_resources_get.py"
  - "tests/test_stdio_wrapper_spawn.py"
  - "tests/test_tool_naming_aliases.py"
  - "tests/test_tool_search.py"
  - "tests/test_tool_upstream_endpoint_contracts.py"
  - "tests/test_tools_describe.py"
  - "tests/test_tools_search.py"
  - "tests/test_tools_search_validation.py"
  - "tests/test_tools_validation_branches.py"
  - "tests/test_trace_report_audit.py"
  - "tests/test_trace_report_host_metadata.py"
  - "tests/test_trace_session.py"
  - "tests/test_trace_utils.py"
  - "tests/test_typing_utils.py"
  - "tests/test_unknown_tool.py"
  - "tests/test_validation.py"
source_commit: "bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851"
source_commit_dirty: true
source_urls:
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/__init__.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/audit_test_utils.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/conftest.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/__init__.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/audit_logger.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/evaluation_results.audit.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/evaluation_results.benchmark.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/evaluation_results.json"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/harness.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/live_capture.py"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/047c3949.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/08eea8b1.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/13ad9383.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/15cb80c1.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/172ff2f7.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/19f40194.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/1f415869.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/2692a326.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/271c9a92.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/328c0257.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/3628f5d1.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/393a6d69.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/3d3c1f52.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/464a7d6a.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/49e6e04e.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/4e4bc6a9.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/4f7c55c0.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/4fc811e8.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/4ffd83a6.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/52a9f148.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/53b72503.txt"
  - "https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/5671006d.txt"
source_hashes:
  tests/__init__.py: "90c1c0862b10341eea2bdb1a0caf307b6a4c8b7a7b9db6086cfbf4d3257bda88"
  tests/audit_test_utils.py: "c78f8d013c67cfbfac8146492016214b886627f6aaccf83d69c85ea7d58cd40e"
  tests/conftest.py: "134e1d72938838162f5643ae5a1d305d21665e91434595812b45d179e72f01b0"
  tests/evaluation/__init__.py: "083df5cd20bdb002668fa0e8614a164873e06aab47afa892b976f2aa719cd21d"
  tests/evaluation/audit_logger.py: "b534afcb2cf15fe46ad6650da2c8394b9377c69d1e8c4fe488c11e2077b20441"
  tests/evaluation/evaluation_results.audit.txt: "5f0e926a26e4a708f671dd84ed87fc6ef02b75a06c7981ba371bf6ef7593a8da"
  tests/evaluation/evaluation_results.benchmark.txt: "395199f9f9fa902128200f6885cc487f94c95cbb711bb2844e99074d59b116ba"
  tests/evaluation/evaluation_results.json: "10becc74bfa7f9e74d6bb3567cc5df891097c86665416495c60967069c2bc667"
  tests/evaluation/harness.py: "743f226233bdbc97b71dc7b86d268c90c1ab4d0a7bb98f44a935a5a4e13309b1"
  tests/evaluation/live_capture.py: "35bce5245d52aea3e3a9f7a24d51b156293a667fdd1ebc2d17e9e870d26aaee7"
  tests/evaluation/logs/audit/047c3949.txt: "64cd184c4fcbf99e7e475ad91632f32a9b3548acf6b1bf1e656a1caa6c2179db"
  tests/evaluation/logs/audit/08eea8b1.txt: "04c55fc725024e82a6b949618fde42e645c62b4d310c6f1122a2af3c5e3cfddd"
  tests/evaluation/logs/audit/13ad9383.txt: "2b269de0fc9bc9fa57d62719e95f067155fb5cc1ce7b27c8a3f81362ab7d8046"
  tests/evaluation/logs/audit/15cb80c1.txt: "db0c2fe5d0c7369b21743c9a430b42e8df203fc2079c3cd5c3423bd2fd484f53"
  tests/evaluation/logs/audit/172ff2f7.txt: "dc541b9f233767fcd216f0dc4a82dfbc0e1ffadd20aa5f9e2a145a53dda4cbdb"
  tests/evaluation/logs/audit/19f40194.txt: "faaeffe30ad43a9bee0aeccea557818a4220b37a12130bbb2d834840c6d79d57"
  tests/evaluation/logs/audit/1f415869.txt: "1f8b85c404b063045b17dc20d454b0f92ab95f7ceb177b1bd4c7c69f654f4445"
  tests/evaluation/logs/audit/2692a326.txt: "483c880d83930785460b9f2b5a309dc114528ee13039a07b5cef11f7a6c58184"
  tests/evaluation/logs/audit/271c9a92.txt: "89aa5bdfd683d9f587f5e620586ec16f3570389cc016a41880d30dc95166463a"
  tests/evaluation/logs/audit/328c0257.txt: "f491a0fa1b7370c0d6f26ba5a2d4932ee3ec391041f41122a8d3c3911331866f"
  tests/evaluation/logs/audit/3628f5d1.txt: "eb746b3031338228f53b03a0f03f4c56bf0e158732b606cca164ed2bb41356b7"
  tests/evaluation/logs/audit/393a6d69.txt: "807171a5f04645817e05c43ed03e6380a93e334962085b55c798f37fcf796eba"
  tests/evaluation/logs/audit/3d3c1f52.txt: "8ab8e303f7426c985eef1d724ca39e66e8a89ee714f9a024adf5cc603d3c07ff"
  tests/evaluation/logs/audit/464a7d6a.txt: "7d93f9eaaf75f4acc7ca83527147f3069be98d493f5acece9b2041c2d4751210"
  tests/evaluation/logs/audit/49e6e04e.txt: "5af282bfc9282fce1dffc3d7f651317de5f60a21e8f9ed90443f05740cc4b2de"
  tests/evaluation/logs/audit/4e4bc6a9.txt: "f79608d1513862d87693b8af627a0f6009c7e96205454e2458e659a8c6528d52"
  tests/evaluation/logs/audit/4f7c55c0.txt: "62204f40f76df7723df7b85a14800fd62be90fb3453b5a38fdea62d438ae6ae9"
  tests/evaluation/logs/audit/4fc811e8.txt: "6d9687b6bfef36229edd692ca7ca9fe3451ad153d7d52459f57196c443ef2015"
  tests/evaluation/logs/audit/4ffd83a6.txt: "110b3cb9c05f9c73d519e240e86b864cd2914028365e2a6d405ad47859b7b8a6"
  tests/evaluation/logs/audit/52a9f148.txt: "5afa7bba78d2b308ae9375610aab6644f2f61852f91d02fa316fa0e67fc6c536"
  tests/evaluation/logs/audit/53b72503.txt: "2eb1db480b8247a79c5c37df1c6dff012e35ac208fc7ad0e82b28c87da601d5c"
  tests/evaluation/logs/audit/5671006d.txt: "8272b0a98fde148362432bc2363bf93f52819d462c18dd5f990f11bdce13972a"
generated_at: "2026-04-06T09:00:35Z"
evidence_scope: "canon"
first_seen_date: "2025-08-20"
last_validated_at: "2026-04-06T09:00:35Z"
---
# Test and Validation Surface

## Evidence Scope

- Categories: `code_runtime`
- Source file count: 249

## Source Inventory

| Path | Summary | First Seen | Last Commit | Related Tests |
| --- | --- | --- | --- | --- |
| `tests/__init__.py` | Test package for MCP Geo. | 2026-01-20 | 2026-01-20 | `tests/evaluation/audit_logger.py`, `tests/evaluation/harness.py`, `tests/evaluation/live_capture.py`, `tests/test_admin_lookup_live_internals.py` |
| `tests/audit_test_utils.py` | from __future__ import annotations | 2026-03-10 | 2026-03-10 | `tests/test_audit_api.py`, `tests/test_audit_pack_builder.py` |
| `tests/conftest.py` | import pytest | 2025-09-16 | 2026-02-21 | - |
| `tests/evaluation/__init__.py` | Evaluation framework for MCP Geo. | 2026-01-20 | 2026-01-20 | `tests/evaluation/audit_logger.py`, `tests/evaluation/harness.py`, `tests/evaluation/live_capture.py`, `tests/test_admin_lookup_live_internals.py` |
| `tests/evaluation/audit_logger.py` | Audit logger for MCP Geo evaluation runs. | 2026-01-20 | 2026-02-11 | `tests/evaluation/harness.py`, `tests/test_evaluation_audit_rate_limits.py` |
| `tests/evaluation/evaluation_results.audit.txt` | ============================================================ | 2026-01-20 | 2026-01-27 | - |
| `tests/evaluation/evaluation_results.benchmark.txt` | MCP Geo Evaluation Benchmark | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/evaluation_results.json` | JSON object keys: effectiveness, results, summary, timestamp, utilization | 2026-01-20 | 2026-01-27 | `tests/evaluation/harness.py`, `tests/test_evaluation_harness_full.py`, `tests/test_evaluation_harness_live_api.py` |
| `tests/evaluation/harness.py` | Test harness for MCP Geo evaluation questions. | 2026-01-20 | 2026-02-22 | `tests/evaluation/harness.py`, `tests/test_evaluation_audit_rate_limits.py`, `tests/test_evaluation_expected_errors.py`, `tests/test_evaluation_harness_full.py` |
| `tests/evaluation/live_capture.py` | from __future__ import annotations | 2026-01-24 | 2026-01-24 | `tests/evaluation/live_capture.py`, `tests/test_evaluation_harness_live_api.py` |
| `tests/evaluation/logs/audit/047c3949.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/08eea8b1.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/13ad9383.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/15cb80c1.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/172ff2f7.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/19f40194.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/1f415869.txt` | ============================================================ | 2026-01-20 | 2026-01-24 | - |
| `tests/evaluation/logs/audit/2692a326.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/271c9a92.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/328c0257.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/3628f5d1.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/393a6d69.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/3d3c1f52.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/464a7d6a.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/49e6e04e.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/4e4bc6a9.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/4f7c55c0.txt` | ============================================================ | 2026-01-20 | 2026-01-24 | - |
| `tests/evaluation/logs/audit/4fc811e8.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/4ffd83a6.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/52a9f148.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/53b72503.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/5671006d.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/58f6acfe.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/5d58b670.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/612fbdcf.txt` | ============================================================ | 2026-01-20 | 2026-01-24 | - |
| `tests/evaluation/logs/audit/6a554f33.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/70b26fc5.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/73f6a027.txt` | ============================================================ | 2026-01-20 | 2026-01-24 | - |
| `tests/evaluation/logs/audit/7c2d3745.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/90599991.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/90801c90.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/91896e44.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/927587df.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/962f1bf1.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/96e7da33.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/992f80bb.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/9c117f41.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/9cb4ff1a.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/9cf7bac5.txt` | ============================================================ | 2026-01-20 | 2026-01-24 | - |
| `tests/evaluation/logs/audit/9d047de2.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/a260375d.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/a5728534.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/ad63b2e9.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/b7285093.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/b8eb2a07.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/b9ad7042.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/ba5f2403.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/bcc1d8ce.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/c2dad4c0.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/c3ad94dd.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/c5ce1ef9.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/c656ba2c.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/cab0fd87.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/d07ef1fa.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/d39da7dd.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/d48a07fb.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/d757dce9.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/d82aacd4.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/d91e4c3b.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/de63e4c3.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/dfbafeae.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/dfcc5156.txt` | ============================================================ | 2026-01-20 | 2026-01-24 | - |
| `tests/evaluation/logs/audit/e004a327.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/e3f55d98.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/edbc973f.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/logs/audit/fd4d6d98.txt` | ============================================================ | 2026-01-20 | 2026-01-20 | - |
| `tests/evaluation/questions.py` | Evaluation Question Suite for MCP Geo Server. | 2026-01-20 | 2026-03-10 | `tests/evaluation/__init__.py`, `tests/evaluation/harness.py`, `tests/evaluation/questions.py`, `tests/evaluation/rubric.py` |
| `tests/evaluation/rubric.py` | Evaluation Rubric for MCP Geo Server. | 2026-01-20 | 2026-01-20 | `tests/evaluation/__init__.py`, `tests/evaluation/harness.py` |
| `tests/fixtures/council_tax/ls14ap_no_results.html` | No results - Check and challenge your Council Tax band - GOV.UK | 2026-04-04 | 2026-04-04 | - |
| `tests/fixtures/council_tax/m11ae_results.html` | Search results - Check and challenge your Council Tax band - GOV.UK | 2026-04-04 | 2026-04-04 | - |
| `tests/fixtures/council_tax/sw1a1aa_results.html` | Search results - Check and challenge your Council Tax band - GOV.UK | 2026-04-04 | 2026-04-04 | - |
| `tests/fixtures/council_tax/yo17hp_results.html` | Search results - Check and challenge your Council Tax band - GOV.UK | 2026-04-04 | 2026-04-04 | - |
| `tests/fixtures/council_tax_band_gold.json` | JSON object keys: cases, provider, scope, verifiedOn | 2026-04-04 | 2026-04-04 | `tests/test_council_tax_gold_eval.py` |
| `tests/fixtures/psr_peat_floor_question.json` | JSON object keys: evidenceRequest, expected, id, question | 2026-02-22 | 2026-02-22 | `tests/test_psr_peat_e2e.py` |
| `tests/helpers.py` | import json | 2026-01-24 | 2026-01-24 | `tests/test_http_transport_coverage_more.py`, `tests/test_mcp_http.py`, `tests/test_ons_codes_unit.py`, `tests/test_ons_data_internal.py` |
| `tests/outputs/CV312JF-oa-example.html` | MCP Geo - Boundary Explorer | 2026-02-08 | 2026-02-12 | - |
| `tests/outputs/northolt.html` | MCP Geo - Statistics Dashboard | 2026-02-09 | 2026-02-09 | - |
| `tests/test_accessors.py` | from tools.accessors import get_gaz, get_dpa | 2025-09-16 | 2025-09-16 | `tests/test_accessors.py` |
| `tests/test_admin_lookup.py` | import pytest | 2025-09-17 | 2026-02-01 | `tests/test_admin_lookup.py`, `tests/test_admin_lookup_cache.py`, `tests/test_admin_lookup_live.py`, `tests/test_tool_upstream_endpoint_contracts.py` |
| `tests/test_admin_lookup_cache.py` | from types import SimpleNamespace | 2026-01-30 | 2026-02-22 | `tests/test_admin_lookup_cache.py` |
| `tests/test_admin_lookup_extended.py` | import pytest | 2025-09-17 | 2026-03-10 | - |
| `tests/test_admin_lookup_live.py` | from fastapi.testclient import TestClient | 2026-01-22 | 2026-03-14 | - |
| `tests/test_admin_lookup_live_internals.py` | from typing import Any | 2026-01-22 | 2026-03-15 | - |
| `tests/test_audit_api.py` | from __future__ import annotations | 2026-03-10 | 2026-03-10 | `tests/test_audit_api.py` |
| `tests/test_audit_normalise.py` | from __future__ import annotations | 2026-03-10 | 2026-03-10 | - |
| `tests/test_audit_pack_builder.py` | from __future__ import annotations | 2026-03-10 | 2026-03-10 | - |
| `tests/test_boundary_cache.py` | import datetime as dt | 2026-01-30 | 2026-02-22 | `tests/test_boundary_cache.py`, `tests/test_resource_catalog.py` |
| `tests/test_boundary_pipeline_variant_policy.py` | from __future__ import annotations | 2026-02-23 | 2026-02-23 | - |
| `tests/test_check_codex_startup_scope.py` | from __future__ import annotations | 2026-03-06 | 2026-03-06 | `tests/test_check_codex_startup_scope.py` |
| `tests/test_check_lmr_host4.py` | from __future__ import annotations | 2026-02-22 | 2026-02-22 | - |
| `tests/test_circuit_breaker.py` | from __future__ import annotations | 2026-02-02 | 2026-02-02 | `tests/test_circuit_breaker.py` |
| `tests/test_client_capabilities.py` | from server.mcp.client_capabilities import summarize_client_capabilities | 2026-02-13 | 2026-02-13 | - |
| `tests/test_codex_long_horizon_summary.py` | from __future__ import annotations | 2026-02-25 | 2026-02-25 | - |
| `tests/test_codex_mcp_local.py` | from __future__ import annotations | 2026-03-07 | 2026-04-05 | - |
| `tests/test_config_secret_file.py` | from server.config import ( | 2026-03-03 | 2026-04-06 | - |
| `tests/test_council_tax_band.py` | from __future__ import annotations | 2026-04-04 | 2026-04-04 | `tests/test_council_tax_band.py`, `tests/test_council_tax_gold_eval.py` |
| `tests/test_council_tax_gold_eval.py` | from __future__ import annotations | 2026-04-04 | 2026-04-04 | - |
| `tests/test_coverage_guardrails.py` | from fastapi.testclient import TestClient | 2026-01-20 | 2026-01-20 | - |
| `tests/test_cross_platform_container_policy.py` | from pathlib import Path | 2026-03-10 | 2026-03-14 | - |
| `tests/test_dataset_cache.py` | from server.dataset_cache import DatasetCache | 2026-01-25 | 2026-01-25 | `tests/test_dataset_cache.py` |
| `tests/test_debug_errors.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2025-09-16 | `tests/test_debug_errors.py` |
| `tests/test_devcontainer_codex_setup.py` | from __future__ import annotations | 2026-03-06 | 2026-03-17 | - |
| `tests/test_docx_hygiene.py` | from __future__ import annotations | 2026-03-16 | 2026-03-16 | - |
| `tests/test_elicitation_forms.py` | from server.mcp import elicitation_forms as forms | 2026-02-07 | 2026-02-07 | - |
| `tests/test_epic_b_validation.py` | from collections.abc import Callable | 2025-08-20 | 2025-09-16 | - |
| `tests/test_error_taxonomy.py` | from server.error_taxonomy import classify_error | 2026-01-25 | 2026-04-04 | - |
| `tests/test_evaluation_audit_rate_limits.py` | from __future__ import annotations | 2026-02-11 | 2026-02-11 | - |
| `tests/test_evaluation_expected_errors.py` | from __future__ import annotations | 2026-02-22 | 2026-02-22 | - |
| `tests/test_evaluation_harness_full.py` | import json | 2026-01-24 | 2026-04-05 | `tests/test_evaluation_harness_full.py` |
| `tests/test_evaluation_harness_live_api.py` | import os | 2026-01-24 | 2026-01-24 | - |
| `tests/test_generate_mcp_geo_analytical_index.py` | import subprocess | 2026-03-11 | 2026-03-12 | - |
| `tests/test_generate_mcp_geo_functionality_showcase.py` | from pathlib import Path | 2026-03-07 | 2026-03-07 | - |
| `tests/test_golden_scenarios.py` | import itertools | 2025-09-16 | 2026-02-25 | `tests/test_golden_scenarios.py` |
| `tests/test_health.py` | from fastapi.testclient import TestClient | 2025-08-20 | 2026-01-20 | `tests/test_health.py`, `tests/test_validation.py` |
| `tests/test_host_benchmark.py` | from __future__ import annotations | 2026-03-06 | 2026-03-17 | `tests/test_host_benchmark.py` |
| `tests/test_http_endpoint_matrix.py` | from fastapi.testclient import TestClient | 2026-02-11 | 2026-02-11 | - |
| `tests/test_http_transport_coverage_more.py` | import base64 | 2026-02-07 | 2026-03-13 | - |
| `tests/test_landis_ingest.py` | from __future__ import annotations | 2026-04-04 | 2026-04-05 | - |
| `tests/test_landis_release_reconciliation.py` | from scripts.landis_release_reconciliation import strip_html | 2026-04-06 | 2026-04-06 | - |
| `tests/test_landis_resources.py` | from __future__ import annotations | 2026-04-04 | 2026-04-05 | `tests/test_landis_resources.py` |
| `tests/test_landis_tools.py` | from __future__ import annotations | 2026-04-04 | 2026-04-05 | `tests/test_landis_resources.py` |
| `tests/test_live_missing_tools_probe.py` | from __future__ import annotations | 2026-02-22 | 2026-02-22 | - |
| `tests/test_logging_redaction.py` | from __future__ import annotations | 2026-02-21 | 2026-03-24 | - |
| `tests/test_main_observability_branches.py` | from __future__ import annotations | 2026-02-11 | 2026-03-24 | - |
| `tests/test_map_trials_export_notebook_scenario_pack.py` | from __future__ import annotations | 2026-02-14 | 2026-02-17 | - |
| `tests/test_map_trials_host_simulation_profiles.py` | from __future__ import annotations | 2026-02-14 | 2026-03-06 | - |
| `tests/test_map_trials_quality_checks.py` | from __future__ import annotations | 2026-02-14 | 2026-02-22 | - |
| `tests/test_map_trials_summary.py` | import json | 2026-02-14 | 2026-02-14 | - |
| `tests/test_map_trials_verify.py` | from pathlib import Path | 2026-02-14 | 2026-02-14 | - |
| `tests/test_maps_proxy.py` | from __future__ import annotations | 2026-01-29 | 2026-03-13 | - |
| `tests/test_mcp_client_if_none_match.py` | import json, subprocess, sys | 2025-09-17 | 2026-01-24 | - |
| `tests/test_mcp_client_resources_get.py` | import json, subprocess, sys | 2025-09-17 | 2026-01-24 | - |
| `tests/test_mcp_docker_local.py` | from __future__ import annotations | 2026-04-05 | 2026-04-06 | `tests/test_mcp_docker_local.py` |
| `tests/test_mcp_http.py` | import base64 | 2026-01-21 | 2026-03-22 | `tests/test_http_transport_coverage_more.py`, `tests/test_mcp_http.py`, `tests/test_resource_fallback.py` |
| `tests/test_mcp_stdio_trace_proxy.py` | from __future__ import annotations | 2026-02-09 | 2026-02-09 | - |
| `tests/test_middleware_exception.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2025-09-16 | - |
| `tests/test_nomis_common.py` | import json | 2026-02-06 | 2026-02-06 | - |
| `tests/test_nomis_data.py` | from typing import Any, Dict, Tuple | 2026-02-05 | 2026-03-16 | `tests/test_nomis_data.py` |
| `tests/test_ons_catalog_snapshot.py` | import json | 2026-02-07 | 2026-02-07 | - |
| `tests/test_ons_catalog_validate_script.py` | from __future__ import annotations | 2026-02-11 | 2026-02-11 | `tests/test_ons_catalog_validate_script.py` |
| `tests/test_ons_catalog_validator.py` | import json | 2026-02-11 | 2026-02-27 | - |
| `tests/test_ons_codes_live.py` | from typing import Any, Dict, Tuple | 2026-01-25 | 2026-02-22 | - |
| `tests/test_ons_codes_unit.py` | from __future__ import annotations | 2026-02-27 | 2026-02-27 | - |
| `tests/test_ons_common.py` | from typing import Any, Dict | 2025-09-17 | 2026-02-11 | - |
| `tests/test_ons_common_paging.py` | from typing import Any, Dict, Tuple | 2026-01-25 | 2026-01-25 | - |
| `tests/test_ons_data.py` | import json | 2025-09-17 | 2026-03-14 | `tests/test_ons_data_internal.py` |
| `tests/test_ons_data_internal.py` | from __future__ import annotations | 2026-02-27 | 2026-02-27 | - |
| `tests/test_ons_dimensions.py` | from fastapi.testclient import TestClient | 2025-09-17 | 2026-01-24 | `tests/test_ons_dimensions_live.py` |
| `tests/test_ons_dimensions_live.py` | from fastapi.testclient import TestClient | 2025-09-17 | 2026-01-27 | `tests/test_ons_dimensions_live.py` |
| `tests/test_ons_filter_formats.py` | from typing import Any, Dict, Tuple | 2025-11-03 | 2026-01-24 | - |
| `tests/test_ons_geo.py` | from __future__ import annotations | 2026-02-22 | 2026-02-23 | `tests/test_ons_geo.py`, `tests/test_ons_geo_cache_refresh.py`, `tests/test_resource_catalog.py` |
| `tests/test_ons_geo_cache.py` | from __future__ import annotations | 2026-02-22 | 2026-03-01 | `tests/test_ons_geo.py`, `tests/test_ons_geo_cache_refresh.py` |
| `tests/test_ons_geo_cache_refresh.py` | from __future__ import annotations | 2026-02-22 | 2026-03-01 | `tests/test_ons_geo_cache_refresh.py` |
| `tests/test_ons_new_tools.py` | from typing import Any, Dict, Tuple | 2025-11-03 | 2026-01-25 | - |
| `tests/test_ons_search_fallback.py` | from fastapi.testclient import TestClient | 2026-01-22 | 2026-03-14 | - |
| `tests/test_ons_select.py` | import json | 2026-02-07 | 2026-03-14 | `tests/test_ons_select.py`, `tests/test_stdio_adapter_direct.py` |
| `tests/test_os_apps_log_event.py` | import json | 2026-01-21 | 2026-01-21 | `tests/test_os_apps_log_event.py` |
| `tests/test_os_apps_tools.py` | from fastapi.testclient import TestClient | 2026-01-20 | 2026-03-14 | - |
| `tests/test_os_auth_errors.py` | import requests | 2026-01-27 | 2026-01-27 | - |
| `tests/test_os_catalog_snapshot.py` | from __future__ import annotations | 2026-02-08 | 2026-02-13 | `tests/test_os_catalog_snapshot.py` |
| `tests/test_os_common.py` | from typing import ClassVar | 2025-09-16 | 2026-02-13 | - |
| `tests/test_os_delivery.py` | from __future__ import annotations | 2026-02-13 | 2026-02-13 | - |
| `tests/test_os_downloads_tools.py` | from __future__ import annotations | 2026-02-13 | 2026-03-14 | - |
| `tests/test_os_features_collections.py` | from __future__ import annotations | 2026-02-08 | 2026-03-03 | `tests/test_os_features_collections.py`, `tests/test_os_new_capability_tools.py` |
| `tests/test_os_features_helpers.py` | from __future__ import annotations | 2026-03-03 | 2026-03-03 | - |
| `tests/test_os_invalid_inputs.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2026-03-14 | - |
| `tests/test_os_landscape.py` | from fastapi.testclient import TestClient | 2026-02-19 | 2026-02-19 | `tests/test_os_landscape.py` |
| `tests/test_os_map_tools.py` | from __future__ import annotations | 2026-02-08 | 2026-03-15 | - |
| `tests/test_os_mcp_descriptor.py` | from fastapi.testclient import TestClient | 2026-01-20 | 2026-03-15 | `tests/test_coverage_guardrails.py`, `tests/test_os_mcp_descriptor.py` |
| `tests/test_os_mcp_internals.py` | from tools import os_mcp | 2026-02-06 | 2026-02-06 | - |
| `tests/test_os_mcp_route_query.py` | from fastapi.testclient import TestClient | 2026-01-20 | 2026-03-16 | - |
| `tests/test_os_names_success.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2026-02-13 | - |
| `tests/test_os_new_capability_tools.py` | from __future__ import annotations | 2026-02-13 | 2026-02-13 | - |
| `tests/test_os_no_api_key.py` | import requests | 2025-09-16 | 2025-09-16 | - |
| `tests/test_os_offline_tools.py` | from __future__ import annotations | 2026-02-14 | 2026-02-17 | - |
| `tests/test_os_peat.py` | from __future__ import annotations | 2026-02-22 | 2026-03-14 | `tests/test_os_peat.py` |
| `tests/test_os_places_by_postcode_success.py` | import tools.os_places as os_places | 2025-09-16 | 2026-02-22 | `tests/test_os_places_by_postcode_success.py` |
| `tests/test_os_places_enrichment.py` | import tools.os_places as os_places | 2025-09-16 | 2026-01-25 | `tests/test_os_places_enrichment.py` |
| `tests/test_os_places_extra_more_success.py` | import pytest | 2025-09-16 | 2026-03-15 | - |
| `tests/test_os_places_extra_success.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2026-02-13 | - |
| `tests/test_os_places_new_tools.py` | from __future__ import annotations | 2026-02-13 | 2026-02-13 | - |
| `tests/test_os_poi.py` | from fastapi.testclient import TestClient | 2026-02-11 | 2026-03-07 | `tests/test_os_poi.py` |
| `tests/test_os_qgis_tools.py` | from __future__ import annotations | 2026-02-13 | 2026-03-14 | - |
| `tests/test_os_retry_errors.py` | import requests | 2025-09-16 | 2026-01-20 | - |
| `tests/test_os_route_tools.py` | from fastapi.testclient import TestClient | 2026-03-10 | 2026-03-13 | - |
| `tests/test_os_timeout.py` | import requests | 2025-09-16 | 2025-09-16 | - |
| `tests/test_os_tools_normalization.py` | import json | 2025-09-16 | 2026-02-22 | - |
| `tests/test_owasp_mcp_validation.py` | from __future__ import annotations | 2026-03-13 | 2026-03-24 | - |
| `tests/test_placeholder_tool.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2025-09-16 | `tests/test_placeholder_tool.py` |
| `tests/test_playground.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2026-04-06 | `tests/test_playground.py`, `tests/test_playground_events.py` |
| `tests/test_playground_events.py` | import json | 2026-01-25 | 2026-03-24 | `tests/test_playground.py`, `tests/test_playground_events.py` |
| `tests/test_postcode_tool.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2026-01-27 | - |
| `tests/test_prompts.py` | import json | 2026-01-29 | 2026-01-29 | - |
| `tests/test_protocol_versions.py` | from server.protocol import ( | 2026-02-11 | 2026-02-11 | - |
| `tests/test_psr_peat_e2e.py` | from __future__ import annotations | 2026-02-22 | 2026-02-22 | - |
| `tests/test_rate_limit_assessor.py` | from scripts.rate_limit_assessor import ProbePoint, parse_prometheus_metrics, percentile, recommend_limit | 2026-02-11 | 2026-02-11 | - |
| `tests/test_rate_limit_metrics.py` | from fastapi.testclient import TestClient | 2025-09-17 | 2026-02-13 | - |
| `tests/test_repo_extent_complexity_report.py` | from __future__ import annotations | 2026-02-25 | 2026-02-25 | - |
| `tests/test_resource_catalog.py` | from __future__ import annotations | 2026-02-02 | 2026-03-14 | `tests/test_resource_catalog.py` |
| `tests/test_resource_fallback.py` | from __future__ import annotations | 2026-03-14 | 2026-04-04 | - |
| `tests/test_resources_code_lists.py` | from fastapi.testclient import TestClient | 2025-11-03 | 2026-01-24 | - |
| `tests/test_resources_data_catalog.py` | from __future__ import annotations | 2026-02-02 | 2026-03-14 | - |
| `tests/test_resources_etag.py` | from typing import Any, Dict, List | 2025-09-17 | 2026-02-11 | `tests/test_resources_etag.py` |
| `tests/test_resources_ons_observations.py` | from fastapi.testclient import TestClient | 2025-09-17 | 2026-01-24 | - |
| `tests/test_resources_paging_filtering.py` | from fastapi.testclient import TestClient | 2025-09-17 | 2026-02-11 | - |
| `tests/test_resources_provenance_headers.py` | from fastapi.testclient import TestClient | 2025-11-03 | 2026-01-24 | - |
| `tests/test_resources_ui_skills.py` | from fastapi.testclient import TestClient | 2026-01-20 | 2026-03-12 | - |
| `tests/test_route_graph.py` | from __future__ import annotations | 2026-03-10 | 2026-03-10 | `tests/test_route_graph.py`, `tests/test_route_graph_integration.py` |
| `tests/test_route_graph_integration.py` | from __future__ import annotations | 2026-03-10 | 2026-04-04 | - |
| `tests/test_route_graph_pipeline.py` | from __future__ import annotations | 2026-03-10 | 2026-03-10 | - |
| `tests/test_route_planning.py` | from server import route_planning | 2026-03-10 | 2026-03-10 | - |
| `tests/test_run_local_tool.py` | from __future__ import annotations | 2026-03-24 | 2026-03-24 | - |
| `tests/test_security.py` | from server.security import configured_secrets, mask_in_text, mask_in_value, redact | 2025-09-16 | 2026-03-24 | - |
| `tests/test_server_landis.py` | from __future__ import annotations | 2026-04-04 | 2026-04-06 | - |
| `tests/test_spec_tool_operability_coverage.py` | from __future__ import annotations | 2026-02-22 | 2026-02-22 | - |
| `tests/test_stakeholder_benchmark_pack.py` | from __future__ import annotations | 2026-03-09 | 2026-03-11 | - |
| `tests/test_stakeholder_live_run.py` | from __future__ import annotations | 2026-03-09 | 2026-03-10 | - |
| `tests/test_stdio_adapter.py` | import json, subprocess, sys, textwrap | 2025-09-17 | 2026-01-24 | - |
| `tests/test_stdio_adapter_branches.py` | import io, json | 2025-11-03 | 2026-01-24 | - |
| `tests/test_stdio_adapter_coverage_more.py` | import io | 2026-02-07 | 2026-03-14 | - |
| `tests/test_stdio_adapter_direct.py` | import io, json, re | 2025-11-03 | 2026-03-22 | - |
| `tests/test_stdio_adapter_main.py` | import io, json | 2025-11-03 | 2026-01-24 | - |
| `tests/test_stdio_resources_etag.py` | import json, subprocess, sys | 2025-09-17 | 2026-01-24 | - |
| `tests/test_stdio_resources_get.py` | import json, subprocess, sys | 2025-09-17 | 2026-01-24 | `tests/test_stdio_resources_get.py` |
| `tests/test_stdio_wrapper_spawn.py` | import json, subprocess, sys | 2025-09-17 | 2025-11-03 | - |
| `tests/test_tool_naming_aliases.py` | from server.tool_naming import resolve_tool_name | 2026-02-14 | 2026-02-14 | - |
| `tests/test_tool_search.py` | from server.mcp.tool_search import STARTER_TOOLS, get_tool_search_config, search_tools | 2026-01-27 | 2026-04-04 | - |
| `tests/test_tool_upstream_endpoint_contracts.py` | from __future__ import annotations | 2026-02-11 | 2026-02-25 | - |
| `tests/test_tools_describe.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2026-04-04 | `tests/test_tools_describe.py` |
| `tests/test_tools_search.py` | from fastapi.testclient import TestClient | 2026-01-20 | 2026-03-15 | `tests/test_coverage_guardrails.py`, `tests/test_tools_describe.py`, `tests/test_tools_search.py`, `tests/test_tools_search_validation.py` |
| `tests/test_tools_search_validation.py` | def test_tools_search_invalid_mode(client): | 2026-01-29 | 2026-03-14 | - |
| `tests/test_tools_validation_branches.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2026-02-13 | - |
| `tests/test_trace_report_audit.py` | from __future__ import annotations | 2026-03-10 | 2026-03-10 | - |
| `tests/test_trace_report_host_metadata.py` | from __future__ import annotations | 2026-03-06 | 2026-03-07 | - |
| `tests/test_trace_session.py` | from __future__ import annotations | 2026-03-07 | 2026-03-17 | `tests/test_trace_session.py` |
| `tests/test_trace_utils.py` | from __future__ import annotations | 2026-03-07 | 2026-03-07 | - |
| `tests/test_typing_utils.py` | from tools.typing_utils import parse_float | 2025-09-16 | 2025-09-16 | - |
| `tests/test_unknown_tool.py` | from fastapi.testclient import TestClient | 2025-09-16 | 2025-09-16 | `tests/test_unknown_tool.py` |
| `tests/test_validation.py` | def call(client, endpoint, method="get", **kwargs): | 2025-08-20 | 2026-01-20 | - |

## Pinned Sources

- [`tests/__init__.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/__init__.py)
- [`tests/audit_test_utils.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/audit_test_utils.py)
- [`tests/conftest.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/conftest.py)
- [`tests/evaluation/__init__.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/__init__.py)
- [`tests/evaluation/audit_logger.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/audit_logger.py)
- [`tests/evaluation/evaluation_results.audit.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/evaluation_results.audit.txt)
- [`tests/evaluation/evaluation_results.benchmark.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/evaluation_results.benchmark.txt)
- [`tests/evaluation/evaluation_results.json`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/evaluation_results.json)
- [`tests/evaluation/harness.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/harness.py)
- [`tests/evaluation/live_capture.py`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/live_capture.py)
- [`tests/evaluation/logs/audit/047c3949.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/047c3949.txt)
- [`tests/evaluation/logs/audit/08eea8b1.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/08eea8b1.txt)
- [`tests/evaluation/logs/audit/13ad9383.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/13ad9383.txt)
- [`tests/evaluation/logs/audit/15cb80c1.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/15cb80c1.txt)
- [`tests/evaluation/logs/audit/172ff2f7.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/172ff2f7.txt)
- [`tests/evaluation/logs/audit/19f40194.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/19f40194.txt)
- [`tests/evaluation/logs/audit/1f415869.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/1f415869.txt)
- [`tests/evaluation/logs/audit/2692a326.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/2692a326.txt)
- [`tests/evaluation/logs/audit/271c9a92.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/271c9a92.txt)
- [`tests/evaluation/logs/audit/328c0257.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/328c0257.txt)
- [`tests/evaluation/logs/audit/3628f5d1.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/3628f5d1.txt)
- [`tests/evaluation/logs/audit/393a6d69.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/393a6d69.txt)
- [`tests/evaluation/logs/audit/3d3c1f52.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/3d3c1f52.txt)
- [`tests/evaluation/logs/audit/464a7d6a.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/464a7d6a.txt)
- [`tests/evaluation/logs/audit/49e6e04e.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/49e6e04e.txt)
- [`tests/evaluation/logs/audit/4e4bc6a9.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/4e4bc6a9.txt)
- [`tests/evaluation/logs/audit/4f7c55c0.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/4f7c55c0.txt)
- [`tests/evaluation/logs/audit/4fc811e8.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/4fc811e8.txt)
- [`tests/evaluation/logs/audit/4ffd83a6.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/4ffd83a6.txt)
- [`tests/evaluation/logs/audit/52a9f148.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/52a9f148.txt)
- [`tests/evaluation/logs/audit/53b72503.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/53b72503.txt)
- [`tests/evaluation/logs/audit/5671006d.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/5671006d.txt)
- [`tests/evaluation/logs/audit/58f6acfe.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/58f6acfe.txt)
- [`tests/evaluation/logs/audit/5d58b670.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/5d58b670.txt)
- [`tests/evaluation/logs/audit/612fbdcf.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/612fbdcf.txt)
- [`tests/evaluation/logs/audit/6a554f33.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/6a554f33.txt)
- [`tests/evaluation/logs/audit/70b26fc5.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/70b26fc5.txt)
- [`tests/evaluation/logs/audit/73f6a027.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/73f6a027.txt)
- [`tests/evaluation/logs/audit/7c2d3745.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/7c2d3745.txt)
- [`tests/evaluation/logs/audit/90599991.txt`](https://github.com/chris-page-gov/mcp-geo/blob/bc8b6be29df0d1dcecd755e6f2e6e0cedcb5f851/tests/evaluation/logs/audit/90599991.txt)
