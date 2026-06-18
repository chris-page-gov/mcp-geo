from __future__ import annotations

from pathlib import Path

from server.config import settings
from tests.audit_test_utils import build_live_style_session


def test_audit_api_end_to_end(client, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "AUDIT_PACK_ROOT", str(tmp_path / "packs"), raising=False)
    session_dir = build_live_style_session(tmp_path / "session")

    normalise_resp = client.post("/audit/normalise", json={"sessionDir": str(session_dir)})
    assert normalise_resp.status_code == 200
    assert normalise_resp.json()["eventCount"] > 0

    create_resp = client.post(
        "/audit/packs",
        json={
            "sessionDir": str(session_dir),
            "retentionClass": "engineering_reconstruction",
            "legalHold": False,
        },
    )
    assert create_resp.status_code == 200
    payload = create_resp.json()
    pack_id = payload["packId"]

    get_resp = client.get(f"/audit/packs/{pack_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["packId"] == pack_id
    assert get_resp.json()["retentionClass"] == "engineering_reconstruction"
    assert get_resp.json()["bundleHash"]["fileName"] == f"DSAP-{pack_id}.zip"

    bundle_resp = client.get(f"/audit/packs/{pack_id}/bundle")
    assert bundle_resp.status_code == 200
    assert bundle_resp.headers["content-type"] == "application/zip"

    bundle_hash_resp = client.get(f"/audit/packs/{pack_id}/bundle/hash")
    assert bundle_hash_resp.status_code == 200
    assert bundle_hash_resp.json()["fileName"] == f"DSAP-{pack_id}.zip"

    verify_resp = client.post(f"/audit/packs/{pack_id}/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verified"] is True

    redact_resp = client.post(
        f"/audit/packs/{pack_id}/redact",
        json={"disclosureProfile": "internal_restricted"},
    )
    assert redact_resp.status_code == 200
    assert Path(redact_resp.json()["path"]).exists()
    get_after_redact = client.get(f"/audit/packs/{pack_id}")
    assert get_after_redact.status_code == 200
    assert any(
        entry["disclosureProfile"] == "internal_restricted"
        for entry in get_after_redact.json()["disclosures"]
    )

    hold_resp = client.post(
        f"/audit/packs/{pack_id}/legal-hold",
        json={"legalHold": True, "reason": "Investigation opened"},
    )
    assert hold_resp.status_code == 200
    assert hold_resp.json()["retentionState"]["legalHold"] is True


def test_audit_api_lists_packs_with_pagination(client, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "AUDIT_PACK_ROOT", str(tmp_path / "packs"), raising=False)
    session_a = build_live_style_session(tmp_path / "session-a")
    session_b = build_live_style_session(tmp_path / "session-b")

    first = client.post("/audit/packs", json={"sessionDir": str(session_a)}).json()
    second = client.post("/audit/packs", json={"sessionDir": str(session_b)}).json()

    list_first = client.get("/audit/packs", params={"limit": 1})
    assert list_first.status_code == 200
    payload_first = list_first.json()
    assert len(payload_first["packs"]) == 1
    assert payload_first["nextPageToken"] == "1"

    list_second = client.get("/audit/packs", params={"limit": 1, "pageToken": "1"})
    assert list_second.status_code == 200
    payload_second = list_second.json()
    assert len(payload_second["packs"]) == 1
    listed_ids = {payload_first["packs"][0]["packId"], payload_second["packs"][0]["packId"]}
    assert listed_ids == {first["packId"], second["packId"]}


def test_audit_api_requires_http_auth_and_rejects_external_output_paths(
    client,
    monkeypatch,
    tmp_path: Path,
) -> None:
    from server.mcp import http_transport

    http_transport._SESSION_STATE.clear()
    pack_root = tmp_path / "packs"
    pack_root.mkdir()
    monkeypatch.setattr(settings, "AUDIT_PACK_ROOT", str(pack_root), raising=False)
    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "static_bearer")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "audit-token")
    session_dir = build_live_style_session(tmp_path / "session")
    outside_output = tmp_path / "outside-ledger.jsonl"

    unauthorized = client.post(
        "/audit/normalise",
        json={"sessionDir": str(session_dir), "outputPath": str(outside_output)},
    )
    assert unauthorized.status_code == 401
    assert unauthorized.json()["code"] == "AUTHENTICATION_FAILED"
    assert not outside_output.exists()

    headers = {"Authorization": "Bearer audit-token"}
    rejected_output = client.post(
        "/audit/normalise",
        headers=headers,
        json={"sessionDir": str(session_dir), "outputPath": str(outside_output)},
    )
    assert rejected_output.status_code == 400
    assert "audit pack root" in rejected_output.text
    assert not outside_output.exists()

    allowed_output = pack_root / "event-ledger.jsonl"
    allowed = client.post(
        "/audit/normalise",
        headers=headers,
        json={"sessionDir": str(session_dir), "outputPath": str(allowed_output)},
    )
    assert allowed.status_code == 200
    assert allowed_output.exists()

    unauth_list = client.get("/audit/packs")
    assert unauth_list.status_code == 401
