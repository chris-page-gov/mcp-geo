# MCP-Geo Stakeholder Evaluation Live Rerun

Generated: 2026-03-10

This report reruns the 20 stakeholder scenarios against the live MCP-Geo surface in the current Codex session.
It is separate from the benchmark pack so the gold/reference answers remain stable while the live tool evidence changes.

## Runtime

- `OS_API_KEY` loaded in this session: `True`
- `OS_API_KEY_FILE` visible in this session: `/Users/crpage/.secrets/os_api_key`
- Boundary cache enabled for this run: `False`
- Route graph enabled for this run: `True`
- Route graph DSN present for this run: `True`
- Machine-readable live results: `data/benchmarking/stakeholder_eval/live_run_2026-03-10.json`

## Interpretation

- This report measures live tool evidence and current workflow reach, not the benchmark pack's gold-answer completeness score.
- `firstClassProductReady` stays strict: it asks whether MCP-Geo exposes the workflow natively enough to answer the question without bespoke external orchestration.

## Overall Summary

- Scenarios rerun: `20`
- First-class-ready scenarios: `1`
- Live outcomes: `{'blocked': 2, 'full': 1, 'partial': 17}`
- Scenarios with authoritative live evidence: `20`

## Scenario Table

| Scenario | Benchmark support | Live outcome | First-class ready | Successful calls | Live evidence calls |
| --- | --- | --- | --- | ---: | ---: |
| SG01 | partial | partial | False | 8/8 | 8 |
| SG02 | partial | partial | False | 10/10 | 10 |
| SG03 | partial | full | True | 6/6 | 2 |
| SG04 | partial | partial | False | 4/4 | 4 |
| SG05 | partial | partial | False | 3/3 | 3 |
| SG06 | partial | partial | False | 7/7 | 7 |
| SG07 | partial | partial | False | 7/7 | 7 |
| SG08 | partial | partial | False | 4/4 | 4 |
| SG09 | partial | partial | False | 1/3 | 1 |
| SG10 | partial | partial | False | 15/15 | 15 |
| SG11 | partial | partial | False | 1/1 | 1 |
| SG12 | partial | partial | False | 6/6 | 3 |
| SG13 | partial | partial | False | 8/8 | 8 |
| SG14 | partial | partial | False | 8/8 | 8 |
| SG15 | partial | partial | False | 8/10 | 3 |
| SG16 | partial | partial | False | 8/8 | 8 |
| SG17 | blocked | blocked | False | 6/6 | 6 |
| SG18 | partial | partial | False | 8/8 | 8 |
| SG19 | partial | partial | False | 8/8 | 8 |
| SG20 | blocked | blocked | False | 7/7 | 6 |

## Scenario Findings

### SG01 Affected premises and vulnerable households in an incident area

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: Live OS Places resolved all 7 benchmark addresses, but only 2 records fall strictly inside the clipped benchmark polygon when the returned address points are used directly. That is materially lower than the benchmark reference answer, so the live rerun reinforces that MCP-Geo still lacks the native flood-geometry, building-footprint, and record-join workflow needed to treat the benchmark total as authoritative live truth.

**Confirmed capabilities**
- Live OS Places address resolution works for the benchmark addresses.
- Live containing-area lookup confirms the affected sample sits in Bassetlaw.

**Confirmed gaps**
- The vulnerable-household data remains synthetic and external to MCP-Geo.
- Point-in-polygon filtering and record dedupe still require external orchestration.

**Evidence snapshot**
- `inputRecords`: `7`
- `resolvedRecords`: `7`
- `insidePolygonRecords`: `2`
- `insideUniquePremises`: `2`
- `duplicateInsideUprns`: `[]`
- `districtFromLiveLookup`: `Bassetlaw`
- `matchedRows`: `[{"recordId": "VH-001", "uprn": "100031280113", "matchType": "high_confidence", "score": 1.0, "insidePolygon": false}, {"recordId": "VH-002", "uprn": "10023264877", "matchType": "high_confidence", "score": 1.0, "insidePolygon": false}, {"recordId": "VH-003", "uprn": "10023264877", "matchType": "high_confidence", "score": 1.0, "insidePolygon": false}, {"recordId": "VH-004", "uprn": "10023264881", "matchType": "high_confidence", "score": 1.0, "insidePolygon": true}, {"recordId": "VH-005", "uprn": "10023264984", "matchType": "high_confidence", "score": 1.0, "insidePolygon": true}, {"recordId": "VH-006", "uprn": "100031279587", "matchType": "high_confidence", "score": 1.0, "insidePolygon": false}, {"recordId": "VH-007", "uprn": "100031269830", "matchType": "review", "score": 0.65, "insidePolygon": false}]`

**Tool calls**
- `admin_lookup.containing_areas`: calls=1, ok=1, liveEvidence=1, cached=0
- `os_places.search`: calls=7, ok=7, liveEvidence=7, cached=0

### SG02 Batch match free-text addresses to UPRNs at scale

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: Live OS Places can now batch-resolve the benchmark address file record by record. The run produced candidate UPRNs for all 10 rows, but the conservative scorer only cleared 2 as high-confidence, pushed 6 into review, and left 2 unmatched. Native MCP-Geo support remains partial because the batch loop, confidence labelling, and review/export queue are still external orchestration.

**Confirmed capabilities**
- Live OS Places matching works on the full 10-row benchmark input.
- Duplicate input rows can be detected reliably once candidate UPRNs are resolved.

**Confirmed gaps**
- MCP-Geo still lacks a first-class batch matcher with confidence buckets and review exports.

**Evidence snapshot**
- `inputRecords`: `10`
- `highConfidenceMatches`: `2`
- `reviewMatches`: `6`
- `unmatched`: `2`
- `duplicateUprnInputs`: `["100031282954"]`
- `reviewQueue`: `[{"sourceId": "ADDR-003", "uprn": "10023264877", "reason": "manual_review"}, {"sourceId": "ADDR-004", "uprn": "10093191764", "reason": "manual_review"}, {"sourceId": "ADDR-005", "uprn": "100032031280", "reason": "low_similarity"}, {"sourceId": "ADDR-006", "uprn": "100031284208", "reason": "manual_review"}, {"sourceId": "ADDR-007", "uprn": "100031282954", "reason": "duplicate_input_same_uprn"}, {"sourceId": "ADDR-008", "uprn": "100031282954", "reason": "duplicate_input_same_uprn"}, {"sourceId": "ADDR-009", "uprn": "10093190272", "reason": "manual_review"}, {"sourceId": "ADDR-010", "uprn": "10090590222", "reason": "low_similarity"}]`
- `matchedRows`: `[{"sourceId": "ADDR-001", "uprn": "100031270361", "matchType": "high_confidence", "score": 1.0}, {"sourceId": "ADDR-002", "uprn": "100031280113", "matchType": "high_confidence", "score": 1.0}, {"sourceId": "ADDR-003", "uprn": "10023264877", "matchType": "review", "score": 0.65}, {"sourceId": "ADDR-004", "uprn": "10093191764", "matchType": "review", "score": 0.75}, {"sourceId": "ADDR-005", "uprn": "100032031280", "matchType": "unmatched", "score": 0.51}, {"sourceId": "ADDR-006", "uprn": "100031284208", "matchType": "review", "score": 0.75}, {"sourceId": "ADDR-007", "uprn": "100031282954", "matchType": "review", "score": 1.0}, {"sourceId": "ADDR-008", "uprn": "100031282954", "matchType": "review", "score": 1.0}, {"sourceId": "ADDR-009", "uprn": "10093190272", "matchType": "review", "score": 0.7083}, {"sourceId": "ADDR-010", "uprn": "10090590222", "matchType": "unmatched", "score": 0.225}]`

**Tool calls**
- `os_places.search`: calls=10, ok=10, liveEvidence=10, cached=0

### SG03 Shortest route between two premises using authoritative road network constraints

- Benchmark support level: `partial`
- Live outcome: `full`
- First-class ready now: `True`
- Summary: The live rerun now classifies the SG03 prompt correctly, exposes the dedicated routing surface, and returns a grounded route with distance, duration, steps, and graph provenance.

**Confirmed capabilities**
- Both benchmark premises resolve to authoritative locations before routing.
- The router correctly recommends `os_route.get` for this emergency routing prompt.
- The live route tool returns computed geometry, distance, duration, and turn-by-turn steps.

**Confirmed gaps**
- Restriction richness still depends on the currently loaded MRN and restriction tables.

**Evidence snapshot**
- `originUprn`: `100032031210`
- `destinationUprn`: `100032031287`
- `routeQueryIntent`: `route_planning`
- `routeQueryRecommendedTool`: `os_route.get`
- `routeQueryWorkflowSteps`: `["os_route.get", "os_apps.render_route_planner"]`
- `graphReady`: `True`
- `graphReason`: `None`
- `graphVersion`: `stakeholder-benchmark-2026-03-10`
- `graphSourceProduct`: `Benchmark seeded route graph`
- `routeStatusCode`: `200`
- `routeCode`: `None`
- `routeProfile`: `emergency`
- `routeDistanceMeters`: `365.0`
- `routeDurationSeconds`: `40.0`
- `routeWarningsCount`: `1`
- `routePlannerResource`: `ui://mcp-geo/route-planner`
- `interactiveCompanionTool`: `os_apps.render_route_planner`
- `distanceReturned`: `True`
- `turnByTurnReturned`: `True`

**Tool calls**
- `os_apps.render_route_planner`: calls=1, ok=1, liveEvidence=0, cached=0
- `os_mcp.route_query`: calls=1, ok=1, liveEvidence=0, cached=0
- `os_places.search`: calls=2, ok=2, liveEvidence=2, cached=0
- `os_route.descriptor`: calls=1, ok=1, liveEvidence=0, cached=0
- `os_route.get`: calls=1, ok=1, liveEvidence=0, cached=0

### SG04 Maintainable road segments and total length by class

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun confirms that Rutland can be resolved to a live boundary and that live NGD road-link segments can be fetched. The scenario is still only partial because the current thin feature surface does not expose a ready-made maintainability/class aggregation workflow or statutory-quality totals by class.

**Confirmed capabilities**
- Live Rutland boundary lookup works end to end.
- Live NGD road-link collections and sample segments are available with the OS key.

**Confirmed gaps**
- Maintainability and statutory reporting aggregation are not surfaced as a first-class MCP-Geo workflow.
- Class-length totals still need external aggregation and quality review against published comparator numbers.

**Evidence snapshot**
- `districtId`: `E06000017`
- `bbox`: `[-0.8268286652905535, 52.52152179827406, -0.4263419092637883, 52.76208348039028]`
- `roadLinkCollectionPresent`: `False`
- `sampleSegmentCount`: `5`
- `samplePropertyKeys`: `["alternatename1_language", "alternatename1_text", "alternatename2_language", "alternatename2_text", "capturespecification", "changetype", "cyclefacility", "cyclefacility_wholelink"]`
- `maintainabilityFieldObserved`: `False`

**Tool calls**
- `admin_lookup.area_geometry`: calls=1, ok=1, liveEvidence=1, cached=0
- `admin_lookup.find_by_name`: calls=1, ok=1, liveEvidence=1, cached=0
- `os_features.collections`: calls=1, ok=1, liveEvidence=1, cached=0
- `os_features.query`: calls=1, ok=1, liveEvidence=1, cached=0

### SG05 Planning site constraints and evidence summary

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The site itself can be resolved live and placed in its containing administrative areas, but the constraint answer remains partial because MCP-Geo still does not expose planning.data or local-plan policy layers as first-class spatial evidence sources.

**Confirmed capabilities**
- Live site resolution works for the benchmark planning site.
- Administrative context can be recovered live from coordinates.

**Confirmed gaps**
- Planning-constraint and local-plan policy layers are still missing from the MCP-Geo tool surface.
- Any intersection evidence beyond OS base layers still has to be sourced externally.

**Evidence snapshot**
- `siteUprn`: `100032031287`
- `district`: `Bassetlaw`
- `planningKeywordCollections`: `[]`
- `planningKeywordCollectionCount`: `0`

**Tool calls**
- `admin_lookup.containing_areas`: calls=1, ok=1, liveEvidence=1, cached=0
- `os_features.collections`: calls=1, ok=1, liveEvidence=1, cached=1
- `os_places.search`: calls=1, ok=1, liveEvidence=1, cached=1

### SG06 Council asset register linked to UPRNs and overlaid with flood risk

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The asset sample can now be checked live against authoritative OS premises identifiers, which is a real improvement over the keyless run. In this session 4 of 7 asset UPRNs resolved cleanly and 3 returned null results, so the scenario remains partial even before the missing flood-risk overlay is considered.

**Confirmed capabilities**
- Live UPRN verification works across the supplied asset sample.

**Confirmed gaps**
- Flood-risk geometry is not yet available as a first-class MCP-Geo layer.
- Matched/unmatched asset exports still require external orchestration.

**Evidence snapshot**
- `assetRows`: `7`
- `resolvedUprns`: `4`
- `unresolvedUprns`: `["10023266361", "10023269092", "10023270715"]`
- `resolvedRows`: `[{"uprn": "100032031194", "site": "Land", "resolved": true, "address": "NOTTINGHAMSHIRE COUNTY COUNCIL, CHANCERY LANE, RETFORD, DN22 6DG", "classification": "Local Government Service"}, {"uprn": "100032031210", "site": "Library", "resolved": true, "address": "NOTTINGHAMSHIRE COUNTY COUNCIL, RETFORD LIBRARY, 17, CHURCHGATE, RETFORD, DN22 6PE", "classification": "Library"}, {"uprn": "100032031287", "site": "Community Centre", "resolved": true, "address": "GOODWIN HALL, CHANCERY LANE, RETFORD, DN22 6DF", "classification": "Public / Village Hall / Other Community Facility"}, {"uprn": "10023266359", "site": "Shop", "resolved": true, "address": "SHOPMOBILITY, CHANCERY LANE, RETFORD, DN22 6DF", "classification": "Community Service Centre / Office"}, {"uprn": "10023266361", "site": "Car Park", "resolved": false, "address": null, "classification": null}, {"uprn": "10023269092", "site": "Car Park", "resolved": false, "address": null, "classification": null}, {"uprn": "10023270715", "site": "Pavillion", "resolved": false, "address": null, "classification": null}]`
- `floodOverlayNativeAvailable`: `False`

**Tool calls**
- `os_places.by_uprn`: calls=7, ok=7, liveEvidence=7, cached=0

### SG07 Flood appraisal: count properties at risk and generate a verification plan

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun can now resolve the supplied property sample to authoritative premises and derive a provisional at-risk count against the benchmark’s clipped flood polygon. It remains partial because the full flood layer, building-footprint overlay, and verification workflow are still not exposed as native live tools.

**Confirmed capabilities**
- Live premises resolution works across the supplied property sample.
- A provisional at-risk subset can be derived when an exercise polygon is supplied.

**Confirmed gaps**
- The authoritative flood geometry is still external to MCP-Geo.
- Verification prioritisation remains an external workflow rather than a native tool output.

**Evidence snapshot**
- `propertyRows`: `7`
- `resolvedRows`: `7`
- `insideBenchmarkPolygon`: `3`
- `classificationSummary`: `{"Self Contained Flat (Includes Maisonette / Apartment)": 2, "Terraced": 1}`
- `verificationPriorityRows`: `[{"propertyId": "PROP-001", "uprn": "100031280113", "classification": "Detached", "priority": "outside_clipped_polygon"}, {"propertyId": "PROP-002", "uprn": "10023264877", "classification": "Self Contained Flat (Includes Maisonette / Apartment)", "priority": "outside_clipped_polygon"}, {"propertyId": "PROP-003", "uprn": "10023264881", "classification": "Terraced", "priority": "field_check_required"}, {"propertyId": "PROP-004", "uprn": "10023264984", "classification": "Self Contained Flat (Includes Maisonette / Apartment)", "priority": "field_check_required"}, {"propertyId": "PROP-005", "uprn": "10023264955", "classification": "Self Contained Flat (Includes Maisonette / Apartment)", "priority": "field_check_required"}, {"propertyId": "PROP-006", "uprn": "100031279587", "classification": "Semi-Detached", "priority": "outside_clipped_polygon"}, {"propertyId": "PROP-007", "uprn": "100031269830", "classification": "Detached", "priority": "outside_clipped_polygon"}]`

**Tool calls**
- `os_places.search`: calls=7, ok=7, liveEvidence=7, cached=6

### SG08 Normalise fragmented housing development sources and summarise by polling district or ward

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The fragmented benchmark sources can be normalised and their ward labels can be checked live against the administrative lookup surface, but the scenario stays partial because the planning inputs are synthetic and MCP-Geo still lacks authoritative planning-register geometry connectors.

**Confirmed capabilities**
- Ward-name lookups can be checked against the live admin-lookup surface.
- Duplicate candidate development records can be surfaced through external reconciliation logic.

**Confirmed gaps**
- The former-district planning sources remain synthetic benchmark fixtures.
- No first-class planning-register geometry tool exists for direct assignment to polling districts or wards.

**Evidence snapshot**
- `inputRows`: `9`
- `uniqueWards`: `4`
- `wardResolutionResults`: `[{"ward": "Cayton", "resultCount": 1}, {"ward": "Ripon South", "resultCount": 0}, {"ward": "Scarborough North", "resultCount": 0}, {"ward": "Selby West", "resultCount": 1}]`
- `duplicateCandidateGroups`: `{"ABBEY QUARTER": ["ALLOC-001", "PERM-011", "PROM-101"], "CAYTON EAST": ["ALLOC-002", "PROM-103"], "RIPON SOUTH YARD": ["ALLOC-003", "PERM-013"]}`

**Tool calls**
- `admin_lookup.find_by_name`: calls=4, ok=4, liveEvidence=4, cached=0

### SG09 BDUK-style premises status lookup with explanation of missing/new-build/epoch issues

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun does not resolve the requested UPRN through OS Places, and the benchmark BDUK subset also does not contain that exact UPRN. That is useful live evidence for the scenario’s missing/unclear branch rather than a crash condition. Exact and best-fit ONS geography lookups for the same UPRN are both `NOT_FOUND`, which strengthens the case for an evidence-ranked explanation instead of guesswork.

**Confirmed capabilities**
- The run can distinguish the requested UPRN from neighbouring benchmark rows at the same postcode.
- The live toolchain returns grounded `NOT_FOUND` outcomes instead of fabricating a premise status.

**Confirmed gaps**
- BDUK remains an external supplied dataset rather than a native MCP-Geo tool family.
- The requested premise is absent from the supplied BDUK subset, so final status still requires dataset-epoch validation.
- ONS geography coverage for this UPRN is incomplete in the current cache.

**Evidence snapshot**
- `requestedUprn`: `10023266361`
- `fixtureRecordPresent`: `False`
- `fixtureStatus`: `None`
- `samePostcodeFixtureUprns`: `["10023266359"]`
- `osPlacesResolved`: `False`
- `onsGeoExactStatusCode`: `404`
- `onsGeoExactSummary`: `{"code": "NOT_FOUND", "message": "No geography mapping found for uprn 10023266361 in exact mode."}`
- `onsGeoBestFitStatusCode`: `404`
- `onsGeoBestFitSummary`: `{"code": "NOT_FOUND", "message": "No geography mapping found for uprn 10023266361 in best_fit mode."}`

**Tool calls**
- `ons_geo.by_uprn`: calls=2, ok=0, liveEvidence=0, cached=0
- `os_places.by_uprn`: calls=1, ok=1, liveEvidence=1, cached=1

### SG10 Link council-tax-like and land-registry-like property datasets via UPRN and quantify unmatched records

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun can now align most of the synthetic council-tax-like rows and the price-paid subset through authoritative UPRNs. That is a real improvement, but the scenario still is not first-class-ready because the batch address resolution, join logic, mismatch labelling, and export schema all remain external orchestration.

**Confirmed capabilities**
- Live OS Places resolution supports UPRN-based joining across both benchmark datasets.

**Confirmed gaps**
- MCP-Geo still lacks a native multi-file entity-resolution and join workflow.
- Mismatch categorisation and export-ready join outputs still require external logic.

**Evidence snapshot**
- `datasetARows`: `8`
- `datasetBRows`: `7`
- `datasetAResolved`: `7`
- `datasetBResolved`: `7`
- `exactUprnMatches`: `["100031270361", "100031280113", "100031282954", "10023264877", "10023264955", "10093191764"]`
- `exactUprnMatchCount`: `6`
- `unmatchedDatasetAUprns`: `["10093190272"]`
- `unmatchedDatasetBUprns`: `["100031275744"]`

**Tool calls**
- `os_places.search`: calls=15, ok=15, liveEvidence=15, cached=2

### SG11 Authoritative postcode result set with cache-freshness guidance

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun can return the authoritative postcode result set directly from OS Places, but the cache-freshness answer still depends on the external GOV.UK comparator because MCP-Geo does not expose service-cache age, refresh timestamps, or stale-record telemetry.

**Confirmed capabilities**
- Live postcode resolution works for the benchmark sample.
- The authoritative premises count can be stated directly from the current OS response.

**Confirmed gaps**
- Cache-freshness policy remains comparator-led rather than observable from MCP-Geo runtime metadata.
- There is no native postcode-cache audit surface for last refresh, staleness, or invalidation triggers.

**Evidence snapshot**
- `postcodeRows`: `[{"sampleId": "PC-001", "postcode": "DN22 6PE", "resultCount": 1, "addresses": [{"uprn": "100032031210", "address": "NOTTINGHAMSHIRE COUNTY COUNCIL, RETFORD LIBRARY, 17, CHURCHGATE, RETFORD, DN22 6PE", "classification": "Library"}]}]`
- `cacheFreshnessObservedLive`: `False`
- `comparatorRefreshRuleDays`: `30`

**Tool calls**
- `os_places.by_postcode`: calls=1, ok=1, liveEvidence=1, cached=0

### SG12 Coordinate-to-address incident resolution and quickest responder comparison

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The incident coordinate and both responder sites resolve cleanly, and the seeded benchmark route graph now allows a grounded fastest-responder comparison. MCP-Geo still only partially supports the use case because the multi-resource comparison and dispatch decision remain external orchestration rather than a native mobilisation workflow.

**Confirmed capabilities**
- Live nearest-address resolution works for the incident coordinate.
- The responder sites resolve to authoritative OS premises records.
- The active route graph supports route comparison to identify the faster benchmark responder.

**Confirmed gaps**
- Responder ranking is still orchestrated outside MCP-Geo rather than returned as a native dispatch tool output.
- Control-room policy and appliance availability remain out of scope.

**Evidence snapshot**
- `incidentAddress`: `GOODWIN HALL, CHANCERY LANE, RETFORD, DN22 6DF`
- `incidentUprn`: `100032031287`
- `incidentClassification`: `Public / Village Hall / Other Community Facility`
- `graphReady`: `True`
- `graphReason`: `None`
- `graphVersion`: `stakeholder-benchmark-2026-03-10`
- `resolvedResponders`: `[{"resourceId": "FR-001", "resourceName": "Retford Fire Station", "uprn": "100032031320", "matched": true, "matchType": "high_confidence", "score": 1.0}, {"resourceId": "FR-002", "resourceName": "Tuxford Fire Station", "uprn": "200002776288", "matched": true, "matchType": "high_confidence", "score": 1.0}]`
- `routeComparisons`: `[{"resourceName": "Retford Fire Station", "ok": true, "distanceMeters": 470.0, "durationSeconds": 50.0, "routeCode": null}, {"resourceName": "Tuxford Fire Station", "ok": true, "distanceMeters": 11100.0, "durationSeconds": 900.0, "routeCode": null}]`
- `fastestResponder`: `Retford Fire Station`

**Tool calls**
- `os_places.nearest`: calls=1, ok=1, liveEvidence=1, cached=0
- `os_places.search`: calls=2, ok=2, liveEvidence=2, cached=0
- `os_route.descriptor`: calls=1, ok=1, liveEvidence=0, cached=1
- `os_route.get`: calls=2, ok=2, liveEvidence=0, cached=0

### SG13 UKHSA-style property-setting classification from authoritative address records

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun supports the identifier-first classification pattern: each benchmark case can be resolved to an authoritative UPRN and class before any operational setting label is applied. The scenario remains partial because the UKHSA-style translation layer still sits outside the native tool surface.

**Confirmed capabilities**
- Live OS Places resolution works across the case-address sample.
- UPRN verification can be performed before mapping the record into an operational setting label.

**Confirmed gaps**
- The settings taxonomy remains an external translation layer, not a first-class MCP-Geo output.
- Batch classification and review queues still require orchestration outside the tool surface.

**Evidence snapshot**
- `resolvedCases`: `4`
- `summaryCounts`: `{"care_home": 1, "community_facility": 1, "prison": 1, "review": 1}`
- `caseRows`: `[{"caseId": "CASE-001", "uprn": "10013978351", "matched": true, "authoritativeClass": "HM Prison Service", "settingLabel": "prison", "expectedBenchmarkSetting": "prison"}, {"caseId": "CASE-002", "uprn": "100031280110", "matched": true, "authoritativeClass": "Care / Nursing Home", "settingLabel": "care_home", "expectedBenchmarkSetting": "care_home"}, {"caseId": "CASE-003", "uprn": "10023264877", "matched": true, "authoritativeClass": "Self Contained Flat (Includes Maisonette / Apartment)", "settingLabel": "review", "expectedBenchmarkSetting": "residential"}, {"caseId": "CASE-004", "uprn": "100032031210", "matched": true, "authoritativeClass": "Library", "settingLabel": "community_facility", "expectedBenchmarkSetting": "community_facility"}]`
- `reviewCount`: `1`

**Tool calls**
- `os_places.by_uprn`: calls=4, ok=4, liveEvidence=4, cached=1
- `os_places.search`: calls=4, ok=4, liveEvidence=4, cached=2

### SG14 North Yorkshire-style tall-building threshold review

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun can ground the building anchors and confirm that building collections exist in the NGD surface, but the threshold answer still depends on synthetic height and floor attributes because MCP-Geo does not yet expose a native tall-building query workflow.

**Confirmed capabilities**
- The building anchors can be resolved to real public locations.
- Building-related NGD collections are discoverable live.

**Confirmed gaps**
- Height and floor thresholds still rely on synthetic benchmark data.
- There is no native building-height or floors query surface in MCP-Geo today.

**Evidence snapshot**
- `resolvedBuildings`: `5`
- `exceedanceCount`: `4`
- `reviewCount`: `0`
- `buildingCollections`: `["bld-fts-building-1", "bld-fts-building-2", "bld-fts-building-3", "bld-fts-building-4", "bld-fts-buildingaccesslocation-1", "bld-fts-buildingline-1", "bld-fts-buildingpart-1", "bld-fts-buildingpart-2", "lnd-fts-land-1", "lnd-fts-land-2"]`
- `sampleQuerySummary`: `{"collection": "bld-fts-building-1", "count": 5, "live": true, "samplePropertyKeys": ["addresscount_commercial", "addresscount_other", "addresscount_residential", "addresscount_total", "buildingpartcount", "buildingpartreference", "buildinguse", "buildinguse_updatedate"]}`

**Tool calls**
- `os_features.collections`: calls=1, ok=1, liveEvidence=1, cached=1
- `os_features.query`: calls=1, ok=1, liveEvidence=1, cached=0
- `os_places.search`: calls=6, ok=6, liveEvidence=6, cached=0

### SG15 ONS-style address-to-geography allocation by UPRN

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun now exercises both exact and best-fit UPRN geography lookup directly, including explicit `NOT_FOUND` branches. The scenario remains partial because the cache is still intentionally sparse and the multi-row comparison/export workflow is not native to MCP-Geo.

**Confirmed capabilities**
- Exact and best-fit ONS geography lookups can be compared directly for the same UPRN.
- Cache status is available live and can be reported alongside row-level coverage gaps.

**Confirmed gaps**
- The current cache does not cover every public UPRN in the benchmark sample.
- Batch comparison, mismatch highlighting, and export shaping still require orchestration outside MCP-Geo.

**Evidence snapshot**
- `cacheStatus`: `ready`
- `cacheAvailable`: `True`
- `cacheProductCount`: `4`
- `coveredRows`: `2`
- `missingRows`: `[{"uprn": "100032031210", "label": "Retford Library", "exactStatus": "NOT_FOUND", "bestFitStatus": "NOT_FOUND"}]`
- `comparisonRows`: `[{"uprn": "100023336959", "address": "FOREIGN COMMONWEALTH & DEVELOPMENT OFFICE, KING CHARLES STREET, LONDON, SW1A 2AH", "exactLad": null, "bestFitLad": null, "differenceFlag": false}, {"uprn": "100120786206", "address": "3, THE MAGNOLIAS, BICESTER, OX26 3YG", "exactLad": null, "bestFitLad": null, "differenceFlag": false}]`

**Tool calls**
- `ons_geo.by_uprn`: calls=6, ok=4, liveEvidence=0, cached=0
- `ons_geo.cache_status`: calls=1, ok=1, liveEvidence=0, cached=0
- `os_places.by_uprn`: calls=3, ok=3, liveEvidence=3, cached=1

### SG16 NHS SCW-style patient distance-to-pharmacy validation

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun can resolve the synthetic patient anchors and the public pharmacy sites, then calculate a nearest-site distance externally. MCP-Geo still only partially supports the use case because there is no native category-aware nearest-facility workflow or patient-distance dashboard.

**Confirmed capabilities**
- The benchmark patient anchors and pharmacy sites can be resolved live.
- A grounded nearest-pharmacy comparison can be produced once coordinates are available.

**Confirmed gaps**
- Nearest-facility calculation still depends on external orchestration rather than a native MCP-Geo tool.
- The patient rows remain synthetic benchmark data.

**Evidence snapshot**
- `resolvedPatients`: `4`
- `resolvedPharmacies`: `3`
- `distanceRows`: `[{"patientId": "PT-001", "matched": true, "nearestPharmacy": "Worksop Pharmacy", "distanceKm": 0.66, "thresholdStatus": "within"}, {"patientId": "PT-002", "matched": true, "nearestPharmacy": "Worksop Pharmacy", "distanceKm": 5.08, "thresholdStatus": "beyond"}, {"patientId": "PT-003", "matched": true, "nearestPharmacy": "Manton Pharmacy", "distanceKm": 16.22, "thresholdStatus": "beyond"}, {"patientId": "PT-004", "matched": false, "nearestPharmacy": "Manton Pharmacy", "distanceKm": 21.23, "thresholdStatus": "beyond"}, {"patientId": "PT-005", "matched": true, "nearestPharmacy": "Manton Pharmacy", "distanceKm": 11.08, "thresholdStatus": "review"}]`
- `breachCount`: `3`
- `reviewCount`: `1`

**Tool calls**
- `os_places.search`: calls=8, ok=8, liveEvidence=8, cached=3

### SG17 Transport for West Midlands-style street width and gradient bottleneck review

- Benchmark support level: `blocked`
- Live outcome: `blocked`
- First-class ready now: `False`
- Summary: The live rerun can ground the Birmingham street names and confirm that road-link features exist, but the bottleneck answer is still blocked as a first-class MCP-Geo workflow because width and gradient are not derived natively and remain synthetic benchmark attributes.

**Confirmed capabilities**
- Street names can be grounded to live named features.
- Road-link collections are available for nearby contextual queries.

**Confirmed gaps**
- Street width and gradient are not derived or queryable natively in MCP-Geo.
- The thresholding relies entirely on synthetic benchmark values.

**Evidence snapshot**
- `resolvedSegments`: `0`
- `roadCollectionPresent`: `False`
- `bottleneckCount`: `3`
- `sampleRoadQuery`: `{}`

**Tool calls**
- `os_features.collections`: calls=1, ok=1, liveEvidence=1, cached=1
- `os_names.find`: calls=5, ok=5, liveEvidence=5, cached=0

### SG18 Birmingham and Solihull referral inequity review by ward

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun can resolve the Birmingham wards and service sites, then prioritise synthetic under-referral wards with grounded site context. It remains partial because the inequity scoring and nearest-site assignment still rely on external logic over synthetic benchmark counts.

**Confirmed capabilities**
- Ward geography lookup works with live admin geometry context.
- The public service sites resolve to authoritative premises records.

**Confirmed gaps**
- Referral and need values are synthetic benchmark data.
- There is no native inequity dashboard or ward-to-service prioritisation workflow in MCP-Geo.

**Evidence snapshot**
- `resolvedWardCount`: `2`
- `resolvedSiteCount`: `3`
- `priorityRows`: `[{"wardName": "Sparkbrook", "priorityScore": 70.0, "nearestSite": "Small Heath Health Centre", "distanceKm": 1.18}, {"wardName": "Small Heath", "priorityScore": 62.0, "nearestSite": "Small Heath Health Centre", "distanceKm": 1.55}, {"wardName": "Ladywood", "priorityScore": 45.0, "nearestSite": "Small Heath Health Centre", "distanceKm": 3.26}]`
- `topWardNames`: `["Sparkbrook", "Small Heath"]`

**Tool calls**
- `admin_lookup.find_by_name`: calls=5, ok=5, liveEvidence=5, cached=0
- `os_places.search`: calls=3, ok=3, liveEvidence=3, cached=0

### SG19 Cheshire and Wirral service-location coverage versus client distribution

- Benchmark support level: `partial`
- Live outcome: `partial`
- First-class ready now: `False`
- Summary: The live rerun can resolve the town anchors and trust sites, then compare the synthetic demand clusters with the current site pattern. The scenario remains partial because the coverage ranking is still an external heuristic over synthetic client counts rather than a native service-network planning workflow.

**Confirmed capabilities**
- Town clusters can be grounded through live place-name resolution.
- The trust service sites resolve to authoritative premises records.

**Confirmed gaps**
- Client counts and need indices are synthetic benchmark data.
- MCP-Geo does not yet expose service-network optimisation or coverage ranking as a native tool.

**Evidence snapshot**
- `resolvedTownCount`: `0`
- `resolvedSiteCount`: `3`
- `topUnderservedRows`: `[{"townName": "Ellesmere Port", "nearestSite": null, "distanceKm": null, "underservedScore": 88.0, "syntheticClients": 73, "syntheticNeedIndex": 88}, {"townName": "Crewe", "nearestSite": null, "distanceKm": null, "underservedScore": 81.0, "syntheticClients": 67, "syntheticNeedIndex": 81}, {"townName": "Macclesfield", "nearestSite": null, "distanceKm": null, "underservedScore": 76.0, "syntheticClients": 91, "syntheticNeedIndex": 76}]`

**Tool calls**
- `os_names.find`: calls=5, ok=5, liveEvidence=5, cached=0
- `os_places.search`: calls=3, ok=3, liveEvidence=3, cached=0

### SG20 Policing patrol-planning hotspot review with live resource locations

- Benchmark support level: `blocked`
- Live outcome: `blocked`
- First-class ready now: `False`
- Summary: The live rerun can ground the synthetic hotspot places and police resource sites, but the scenario remains blocked as a first-class MCP-Geo workflow because there is still no native patrol-optimisation or demand-prediction surface. The router also does not produce a policing-specific planning workflow for this prompt.

**Confirmed capabilities**
- The hotspot place names and public police resource sites can be resolved live.
- A grounded distance-to-resource context can be assembled for review.

**Confirmed gaps**
- The demand and vulnerability values are synthetic benchmark data.
- MCP-Geo still lacks native patrol optimisation, demand prediction, or patrol-allocation workflows.

**Evidence snapshot**
- `routeQueryIntent`: `place_lookup`
- `routeQueryRecommendedTool`: `admin_lookup.find_by_name`
- `resolvedHotspotCount`: `0`
- `resolvedResourceCount`: `2`
- `hotspotRows`: `[{"placeName": "Worksop", "nearestResource": null, "distanceKm": null, "syntheticIncidents": 52, "syntheticVulnerabilityIndex": 73}, {"placeName": "Retford", "nearestResource": null, "distanceKm": null, "syntheticIncidents": 38, "syntheticVulnerabilityIndex": 77}, {"placeName": "Newark-on-Trent", "nearestResource": null, "distanceKm": null, "syntheticIncidents": 29, "syntheticVulnerabilityIndex": 69}, {"placeName": "Tuxford", "nearestResource": null, "distanceKm": null, "syntheticIncidents": 17, "syntheticVulnerabilityIndex": 64}]`

**Tool calls**
- `os_mcp.route_query`: calls=1, ok=1, liveEvidence=0, cached=0
- `os_names.find`: calls=4, ok=4, liveEvidence=4, cached=0
- `os_places.search`: calls=2, ok=2, liveEvidence=2, cached=0
