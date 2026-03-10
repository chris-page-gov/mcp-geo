from __future__ import annotations

import json
from pathlib import Path

from server.audit.integrity import verify_pack_integrity
from server.audit.pack_builder import build_audit_pack
from server.audit.redaction import build_redacted_pack
from server.audit.source_register import build_source_register
from tests.audit_test_utils import build_live_style_session, build_partial_session


def _event_types(path: Path) -> list[str]:
    return [
        json.loads(line)["eventType"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_build_audit_pack_from_live_style_session_fixture(tmp_path: Path) -> None:
    session_dir = build_live_style_session(tmp_path / "session")
    result = build_audit_pack(
        session_dir,
        output_root=tmp_path / "packs",
        retention_class="foi_support",
        legal_hold=True,
    )

    pack_dir = Path(result["path"])
    required_paths = [
        pack_dir / "audit-card.json",
        pack_dir / "audit-card.md",
        pack_dir / "conversation-record.json",
        pack_dir / "decision-record.json",
        pack_dir / "event-ledger.jsonl",
        pack_dir / "evidence-register.json",
        pack_dir / "source-register.json",
        pack_dir / "redaction-manifest.json",
        pack_dir / "integrity-manifest.json",
        pack_dir / "transcript-visible.md",
        pack_dir / "generated" / "report.md",
        pack_dir / "bundle" / f"DSAP-{result['packId']}.zip",
        pack_dir / "bundle" / f"DSAP-{result['packId']}.zip.sha256.json",
    ]
    for path in required_paths:
        assert path.exists(), path

    audit_card = json.loads((pack_dir / "audit-card.json").read_text(encoding="utf-8"))
    assert audit_card["completeness"]["grade"] == "A"
    assert audit_card["retentionClass"] == "foi_support"
    assert audit_card["legalHold"] is True

    event_types = _event_types(pack_dir / "event-ledger.jsonl")
    assert "audit_pack.created" in event_types
    assert "audit_pack.sealed" in event_types
    assert "audit_pack.legal_hold_applied" in event_types

    source_register = json.loads((pack_dir / "source-register.json").read_text(encoding="utf-8"))
    assert source_register["counts"] == {"held": 1, "partial": 0, "not_held": 0}

    verified = verify_pack_integrity(pack_dir)
    assert verified["verified"] is True

    bundle_hash = json.loads(
        (pack_dir / "bundle" / f"DSAP-{result['packId']}.zip.sha256.json").read_text(
            encoding="utf-8"
        )
    )
    assert bundle_hash["fileName"] == f"DSAP-{result['packId']}.zip"
    assert len(bundle_hash["sha256"]) == 64


def test_build_audit_pack_from_partial_session_declares_grade_c_gaps(tmp_path: Path) -> None:
    session_dir = build_partial_session(tmp_path / "partial-session")
    result = build_audit_pack(session_dir, output_root=tmp_path / "packs")

    audit_card = json.loads(
        (Path(result["path"]) / "audit-card.json").read_text(encoding="utf-8")
    )
    assert audit_card["completeness"]["grade"] == "C"
    assert any("Conversation end marker" in reason for reason in audit_card["completeness"]["reasons"])
    assert any("Visible transcript evidence" in reason for reason in audit_card["completeness"]["reasons"])


def test_integrity_verification_catches_tampering(tmp_path: Path) -> None:
    session_dir = build_live_style_session(tmp_path / "session")
    result = build_audit_pack(session_dir, output_root=tmp_path / "packs")
    pack_dir = Path(result["path"])

    transcript_path = pack_dir / "transcript-visible.md"
    transcript_path.write_text(
        transcript_path.read_text(encoding="utf-8") + "\nTampered.\n",
        encoding="utf-8",
    )

    verified = verify_pack_integrity(pack_dir)
    assert verified["verified"] is False
    assert any(item["path"] == "transcript-visible.md" for item in verified["mismatches"])


def test_redaction_preserves_original_and_emits_derivative(tmp_path: Path) -> None:
    session_dir = build_live_style_session(tmp_path / "session")
    result = build_audit_pack(session_dir, output_root=tmp_path / "packs")
    pack_dir = Path(result["path"])

    original_transcript = (pack_dir / "transcript-visible.md").read_text(encoding="utf-8")
    derivative = build_redacted_pack(pack_dir, disclosure_profile="foi_redacted")
    derivative_dir = Path(derivative["path"])

    assert (pack_dir / "transcript-visible.md").read_text(encoding="utf-8") == original_transcript
    assert "Transcript content redacted" in (
        derivative_dir / "transcript-visible.md"
    ).read_text(encoding="utf-8")
    assert "audit_pack.redacted" in _event_types(derivative_dir / "event-ledger.jsonl")
    assert (
        derivative_dir / "bundle" / f"DSAP-{result['packId']}-foi_redacted.zip"
    ).exists()
    assert (
        derivative_dir / "bundle" / f"DSAP-{result['packId']}-foi_redacted.zip.sha256.json"
    ).exists()


def test_source_register_distinguishes_held_status_states() -> None:
    events = [
        {
            "conversationId": "conv-1",
            "eventId": "evt-1",
            "eventType": "source.http.requested",
            "occurredAt": "2026-03-10T10:00:01Z",
            "data": {
                "sourceAccessId": "src-held",
                "source": "os_places",
                "method": "GET",
                "url": "https://example.test/held",
                "heldStatus": "held",
            },
            "correlation": {},
            "evidence": [],
        },
        {
            "conversationId": "conv-1",
            "eventId": "evt-2",
            "eventType": "source.http.responded",
            "occurredAt": "2026-03-10T10:00:02Z",
            "data": {
                "sourceAccessId": "src-held",
                "statusCode": 200,
                "heldStatus": "held",
            },
            "correlation": {},
            "evidence": [],
        },
        {
            "conversationId": "conv-1",
            "eventId": "evt-3",
            "eventType": "source.http.requested",
            "occurredAt": "2026-03-10T10:00:03Z",
            "data": {
                "sourceAccessId": "src-partial",
                "source": "os_places",
                "method": "GET",
                "url": "https://example.test/partial",
            },
            "correlation": {},
            "evidence": [],
        },
        {
            "conversationId": "conv-1",
            "eventId": "evt-4",
            "eventType": "source.http.requested",
            "occurredAt": "2026-03-10T10:00:04Z",
            "data": {
                "sourceAccessId": "src-missing",
                "source": "os_places",
                "method": "GET",
                "url": "https://example.test/missing",
                "heldStatus": "not_held",
            },
            "correlation": {},
            "evidence": [],
        },
    ]

    register = build_source_register(events)

    assert register["counts"] == {"held": 1, "partial": 1, "not_held": 1}
