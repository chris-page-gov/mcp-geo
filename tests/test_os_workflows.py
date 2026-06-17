from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def _call(payload):
    return client.post("/tools/call", json={"tool": "os_workflows.query", **payload})


def test_os_workflows_descriptor_lists_poc_workflows():
    resp = client.post("/tools/call", json={"tool": "os_workflows.descriptor"})
    assert resp.status_code == 200
    body = resp.json()
    workflow_ids = {workflow["workflowId"] for workflow in body["workflows"]}

    assert {
        "batch_address_match",
        "incident_impact",
        "planning_constraints",
    } <= workflow_ids


def test_os_workflows_batch_address_match_flags_duplicates_and_review_rows():
    resp = _call(
        {
            "workflowId": "batch_address_match",
            "records": [
                {
                    "source_id": "ADDR-001",
                    "address_text": "1 Test Road, Retford DN22 6FE",
                    "uprn": "100000000001",
                    "matchType": "high_confidence",
                    "score": 0.98,
                },
                {
                    "source_id": "ADDR-002",
                    "address_text": "1 Test Rd, Retford DN22 6FE",
                    "uprn": "100000000001",
                    "matchType": "high_confidence",
                    "score": 0.96,
                },
                {"source_id": "ADDR-003", "address_text": "Unknown place"},
            ],
        }
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["workflowId"] == "batch_address_match"
    assert body["productSurfaceReady"] is True
    assert body["results"]["inputRecords"] == 3
    assert body["results"]["reviewMatches"] == 3
    assert body["results"]["duplicateGroups"][0]["uprn"] == "100000000001"
    reasons = {item["reason"] for item in body["reviewQueue"]}
    assert "duplicate_input" in reasons
    assert "needs_os_places_resolution" in reasons
    assert body["export"]["manualReviewRequired"] is True


def test_os_workflows_incident_impact_counts_inside_records_and_categories():
    resp = _call(
        {
            "workflowId": "incident_impact",
            "geometryWkt": (
                "POLYGON((-0.946200 53.321400,-0.946200 53.318800,"
                "-0.943000 53.318800,-0.943000 53.321400,-0.946200 53.321400))"
            ),
            "records": [
                {
                    "record_id": "VH-001",
                    "address_text": "6 Mill Bridge Close, Retford DN22 6FE",
                    "uprn": "100000000001",
                    "resident_group": "older_person",
                    "lat": 53.3195,
                    "lon": -0.9445,
                },
                {
                    "record_id": "VH-002",
                    "address_text": "6 Mill Bridge Cl, Retford DN22 6FE",
                    "uprn": "100000000001",
                    "resident_group": "medical",
                    "lat": 53.3196,
                    "lon": -0.9446,
                },
                {
                    "record_id": "VH-003",
                    "address_text": "Outside Retford DN22 6TN",
                    "resident_group": "older_person",
                    "lat": 53.3195,
                    "lon": -0.9475,
                },
                {
                    "record_id": "VH-004",
                    "address_text": "Needs coordinates Retford DN22 6FE",
                },
            ],
        }
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["workflowId"] == "incident_impact"
    assert body["answerStatus"] == "ready_for_review"
    assert body["results"]["affectedRecords"] == 2
    assert body["results"]["affectedPremises"] == 1
    assert body["results"]["duplicateGroups"][0]["recordIds"] == ["VH-001", "VH-002"]
    categories = {item["category"]: item["records"] for item in body["results"]["categorySummary"]}
    assert categories == {"medical": 1, "older_person": 1}
    assert body["reviewQueue"][0]["reason"] == "needs_coordinate_resolution"


def test_os_workflows_planning_constraints_surfaces_connector_gap():
    resp = _call(
        {
            "workflowId": "planning_constraints",
            "site": "Goodwin Hall, Chancery Lane, Retford, DN22 6DF",
        }
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["workflowId"] == "planning_constraints"
    assert body["answerStatus"] == "needs_external_layers"
    assert len(body["results"]["constraintLayers"]) >= 3
    assert {item["reason"] for item in body["reviewQueue"]} == {"connector_needed"}
    assert body["export"]["manualReviewRequired"] is True


def test_os_workflows_rejects_invalid_workflow_id():
    resp = _call({"workflowId": "does_not_exist"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"
