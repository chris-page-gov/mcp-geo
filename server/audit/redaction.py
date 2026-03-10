from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from server.audit.integrity import write_bundle_hash_sidecar, write_integrity_manifest
from server.audit.normalise import EVENT_SCHEMA_VERSION


VALID_DISCLOSURE_PROFILES = {"internal_full", "internal_restricted", "foi_redacted"}


def normalize_disclosure_profile(value: str | None) -> str:
    candidate = (value or "internal_full").strip().lower()
    if candidate not in VALID_DISCLOSURE_PROFILES:
        raise ValueError(f"Unsupported disclosure profile: {value}")
    return candidate


def build_redacted_pack(pack_dir: Path, *, disclosure_profile: str) -> dict[str, Any]:
    profile = normalize_disclosure_profile(disclosure_profile)
    derivative_dir = pack_dir / "disclosures" / profile
    (derivative_dir / "generated").mkdir(parents=True, exist_ok=True)
    (derivative_dir / "bundle").mkdir(parents=True, exist_ok=True)

    source_pack_id = _load_json(pack_dir / "audit-card.json").get("packId") or pack_dir.name
    redactions: list[dict[str, Any]] = []

    audit_card = _load_json(pack_dir / "audit-card.json")
    audit_card["disclosureProfile"] = profile
    audit_card["derivedFromPackId"] = source_pack_id
    audit_card["retainedEvidenceIncluded"] = False
    audit_card["redactedAt"] = _utc_now()

    conversation_record = _load_json(pack_dir / "conversation-record.json")
    conversation_record["disclosureProfile"] = profile

    decision_record = _load_json(pack_dir / "decision-record.json")
    decision_record["disclosureProfile"] = profile

    evidence_register = _redact_evidence_register(
        _load_json(pack_dir / "evidence-register.json"),
        profile,
        redactions,
    )
    source_register = _redact_source_register(
        _load_json(pack_dir / "source-register.json"),
        profile,
        redactions,
    )
    redacted_events = _redact_event_ledger(pack_dir / "event-ledger.jsonl", profile, redactions)
    redacted_events = _append_redaction_event(redacted_events, source_pack_id, profile)
    transcript_text = _redact_transcript(pack_dir / "transcript-visible.md", profile, redactions)
    report_text = _redact_report(pack_dir / "generated" / "report.md", profile)

    _write_json(derivative_dir / "audit-card.json", audit_card)
    (derivative_dir / "audit-card.md").write_text(_render_audit_card_markdown(audit_card), encoding="utf-8")
    _write_json(derivative_dir / "conversation-record.json", conversation_record)
    _write_json(derivative_dir / "decision-record.json", decision_record)
    _write_json(derivative_dir / "evidence-register.json", evidence_register)
    _write_json(derivative_dir / "source-register.json", source_register)
    (derivative_dir / "event-ledger.jsonl").write_text(
        "".join(json.dumps(event, ensure_ascii=True, separators=(",", ":")) + "\n" for event in redacted_events),
        encoding="utf-8",
    )
    (derivative_dir / "transcript-visible.md").write_text(transcript_text, encoding="utf-8")
    (derivative_dir / "generated" / "report.md").write_text(report_text, encoding="utf-8")

    redaction_manifest = {
        "schemaVersion": "1.0.0",
        "generatedAt": _utc_now(),
        "sourcePackId": source_pack_id,
        "disclosureProfile": profile,
        "redactions": redactions,
        "removedFiles": ["retained/"],
    }
    _write_json(derivative_dir / "redaction-manifest.json", redaction_manifest)

    artifact_paths = [
        derivative_dir / "audit-card.json",
        derivative_dir / "audit-card.md",
        derivative_dir / "conversation-record.json",
        derivative_dir / "decision-record.json",
        derivative_dir / "event-ledger.jsonl",
        derivative_dir / "evidence-register.json",
        derivative_dir / "source-register.json",
        derivative_dir / "redaction-manifest.json",
        derivative_dir / "transcript-visible.md",
        derivative_dir / "generated" / "report.md",
    ]
    write_integrity_manifest(
        derivative_dir,
        artifact_paths,
        pack_id=source_pack_id,
        disclosure_profile=profile,
    )
    bundle_path = _bundle_derivative(derivative_dir, source_pack_id, profile)
    bundle_hash_path = write_bundle_hash_sidecar(
        bundle_path,
        pack_id=source_pack_id,
        disclosure_profile=profile,
    )
    return {
        "sourcePackId": source_pack_id,
        "disclosureProfile": profile,
        "path": str(derivative_dir),
        "bundlePath": str(bundle_path),
        "bundleHashPath": str(bundle_hash_path),
        "redactionCount": len(redactions),
    }


def _redact_event_ledger(
    path: Path,
    profile: str,
    redactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        event = json.loads(line)
        rows.append(_redact_event(event, profile, redactions, line_number))
    return rows


def _append_redaction_event(
    events: list[dict[str, Any]],
    pack_id: str,
    profile: str,
) -> list[dict[str, Any]]:
    if not events:
        return events
    clone = deepcopy(events)
    next_sequence = max(int(event.get("sequence", 0)) for event in clone) + 1
    conversation_id = str(clone[0].get("conversationId") or pack_id)
    decision_episode_id = clone[0].get("decisionEpisodeId")
    occurred_at = _utc_now()
    event = {
        "schemaVersion": EVENT_SCHEMA_VERSION,
        "eventId": f"evt_redact_{pack_id[:8]}_{profile}",
        "sequence": next_sequence,
        "eventType": "audit_pack.redacted",
        "conversationId": conversation_id,
        "decisionEpisodeId": decision_episode_id,
        "occurredAt": occurred_at,
        "actor": {"kind": "system", "id": "dsap"},
        "channel": "session_metadata",
        "status": "observed",
        "message": "Derived disclosure pack created.",
        "data": {
            "packId": pack_id,
            "disclosureProfile": profile,
        },
        "correlation": {"sourceSequence": next_sequence},
        "evidence": [{"kind": "file", "path": "redaction-manifest.json"}],
    }
    clone.append(event)
    return clone


def _redact_event(
    event: dict[str, Any],
    profile: str,
    redactions: list[dict[str, Any]],
    line_number: int,
) -> dict[str, Any]:
    clone = deepcopy(event)
    if profile == "internal_full":
        return clone
    for evidence in clone.get("evidence", []):
        if isinstance(evidence, dict) and evidence.get("path"):
            evidence["path"] = Path(str(evidence["path"])).name
            redactions.append({"file": "event-ledger.jsonl", "line": line_number, "field": "evidence.path"})
    data = clone.get("data")
    if not isinstance(data, dict):
        return clone
    if profile == "internal_restricted":
        for key in ("arguments", "result", "payload", "command", "context", "capabilities"):
            if key in data:
                data[key] = "[REDACTED]"
                redactions.append({"file": "event-ledger.jsonl", "line": line_number, "field": f"data.{key}"})
        return clone
    allowed = {}
    for key in ("toolName", "resourceUri", "source", "method", "statusCode", "role", "originalEventType"):
        if key in data:
            allowed[key] = data[key]
    if clone.get("eventType", "").startswith("message."):
        allowed["content"] = "[REDACTED]"
        redactions.append({"file": "event-ledger.jsonl", "line": line_number, "field": "data.content"})
    clone["data"] = allowed
    clone["correlation"] = {}
    redactions.append({"file": "event-ledger.jsonl", "line": line_number, "field": "correlation"})
    return clone


def _redact_evidence_register(
    payload: dict[str, Any],
    profile: str,
    redactions: list[dict[str, Any]],
) -> dict[str, Any]:
    clone = deepcopy(payload)
    if profile == "internal_full":
        return clone
    for entry in clone.get("items", []):
        if not isinstance(entry, dict):
            continue
        for key in ("sourcePath", "retainedPath"):
            value = entry.get(key)
            if isinstance(value, str) and value:
                entry[key] = Path(value).name
                redactions.append({"file": "evidence-register.json", "field": key})
        if profile == "foi_redacted" and "sha256" in entry:
            entry["sha256"] = "[REDACTED]"
            redactions.append({"file": "evidence-register.json", "field": "sha256"})
    return clone


def _redact_source_register(
    payload: dict[str, Any],
    profile: str,
    redactions: list[dict[str, Any]],
) -> dict[str, Any]:
    clone = deepcopy(payload)
    if profile == "internal_full":
        return clone
    for entry in clone.get("entries", []):
        if not isinstance(entry, dict):
            continue
        if "url" in entry:
            entry["url"] = "[REDACTED]"
            redactions.append({"file": "source-register.json", "field": "url"})
        if profile == "foi_redacted":
            for key in ("requestEventId", "responseEventId", "evidence"):
                if key in entry:
                    entry[key] = "[REDACTED]" if key != "evidence" else []
                    redactions.append({"file": "source-register.json", "field": key})
    return clone


def _redact_transcript(path: Path, profile: str, redactions: list[dict[str, Any]]) -> str:
    text = path.read_text(encoding="utf-8")
    if profile == "internal_full":
        return text
    redactions.append({"file": "transcript-visible.md", "field": "content"})
    return "# Visible Transcript\n\nTranscript content redacted for disclosure.\n"


def _redact_report(path: Path, profile: str) -> str:
    text = path.read_text(encoding="utf-8")
    if profile == "internal_full":
        return text
    return f"# DSAP Report ({profile})\n\nThis derived report omits retained evidence content.\n"


def _render_audit_card_markdown(audit_card: dict[str, Any]) -> str:
    lines = [
        "# DSAP Audit Card",
        f"- Pack ID: {audit_card.get('packId')}",
        f"- Disclosure profile: {audit_card.get('disclosureProfile')}",
        f"- Completeness grade: {audit_card.get('completeness', {}).get('grade')}",
        f"- Legal hold: {audit_card.get('legalHold')}",
    ]
    return "\n".join(lines) + "\n"


def _bundle_derivative(derivative_dir: Path, pack_id: str, profile: str) -> Path:
    import zipfile

    bundle_path = derivative_dir / "bundle" / f"DSAP-{pack_id}-{profile}.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(derivative_dir.rglob("*")):
            if path.is_dir() or path == bundle_path:
                continue
            archive.write(path, path.relative_to(derivative_dir))
    return bundle_path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
