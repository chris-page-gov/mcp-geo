from __future__ import annotations

import argparse
import json
import shutil
import uuid
import zipfile
from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from server.audit.decision_record import build_decision_record
from server.audit.episode_builder import build_decision_episode
from server.audit.integrity import (
    bundle_hash_sidecar_path,
    load_bundle_hash_sidecar,
    sha256_file,
    write_bundle_hash_sidecar,
    write_integrity_manifest,
)
from server.audit.normalise import EVENT_SCHEMA_VERSION, build_event_ledger
from server.audit.retention import (
    DEFAULT_RETENTION_CLASS,
    load_retention_state,
    normalize_retention_class,
    write_retention_state,
)
from server.audit.source_register import build_source_register
from server.config import settings


REQUIRED_OUTPUTS = (
    "audit-card.json",
    "audit-card.md",
    "conversation-record.json",
    "decision-record.json",
    "event-ledger.jsonl",
    "evidence-register.json",
    "source-register.json",
    "redaction-manifest.json",
    "integrity-manifest.json",
    "transcript-visible.md",
    "generated/report.md",
)


def default_pack_root() -> Path:
    return Path(settings.AUDIT_PACK_ROOT).expanduser().resolve()


DEFAULT_PACK_ROOT = default_pack_root()


def resolve_pack_dir(pack_id: str, *, pack_root: Path | None = None) -> Path:
    candidate = Path(pack_id)
    if candidate.is_absolute():
        return candidate
    return (pack_root or default_pack_root()) / pack_id


def build_audit_pack(
    session_dir: Path,
    *,
    output_root: Path | None = None,
    scope_type: str = "conversation",
    episode_id: str | None = None,
    episode_title: str | None = None,
    episode_start_sequence: int | None = None,
    episode_end_sequence: int | None = None,
    retention_class: str = DEFAULT_RETENTION_CLASS,
    legal_hold: bool = False,
) -> dict[str, Any]:
    session_dir = Path(session_dir).resolve()
    pack_root = (output_root or default_pack_root()).resolve()
    pack_root.mkdir(parents=True, exist_ok=True)
    full_events = build_event_ledger(session_dir)
    if not full_events:
        raise ValueError("No canonical events could be derived from the session.")

    episode, scoped_events = build_decision_episode(
        full_events,
        scope_type=scope_type,
        episode_id=episode_id,
        title=episode_title,
        start_sequence=episode_start_sequence,
        end_sequence=episode_end_sequence,
    )

    pack_id = uuid.uuid4().hex
    pack_dir = pack_root / pack_id
    retained_dir = pack_dir / "retained"
    generated_dir = pack_dir / "generated"
    bundle_dir = pack_dir / "bundle"
    disclosures_dir = pack_dir / "disclosures"
    retained_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    disclosures_dir.mkdir(parents=True, exist_ok=True)

    session_meta = _load_json(session_dir / "session.json")
    retained_events, evidence_register = _materialize_evidence(
        scoped_events,
        session_dir=session_dir,
        pack_dir=pack_dir,
        episode=episode,
    )
    source_register = build_source_register(retained_events)
    decision_record = build_decision_record(retained_events, episode)
    transcript_markdown = _render_transcript(retained_events)
    retention_state = write_retention_state(
        pack_dir,
        retention_class=retention_class,
        legal_hold=legal_hold,
        reason="Legal hold requested at pack creation." if legal_hold else None,
    )
    completeness = _build_completeness(
        retained_events,
        evidence_register,
        source_register,
        decision_record,
        scope_type=episode["scopeType"],
    )

    created_at = _utc_now()
    redaction_manifest = _build_original_redaction_manifest(pack_id)
    pack_events = _build_pack_events(
        conversation_id=episode["conversationId"],
        decision_episode_id=episode["decisionEpisodeId"],
        base_sequence=max(int(event.get("sequence", 0)) for event in retained_events)
        if retained_events
        else 0,
        scope_type=episode["scopeType"],
        pack_id=pack_id,
        retention_state=retention_state,
        created_at=created_at,
    )
    final_events = _renumber_events(retained_events + pack_events)
    decision_record = build_decision_record(final_events, episode)
    source_register = build_source_register(final_events)
    audit_card = _build_audit_card(
        pack_id=pack_id,
        episode=episode,
        completeness=completeness,
        session_dir=session_dir,
        event_count=len(final_events),
        evidence_register=evidence_register,
        source_register=source_register,
        retention_state=retention_state,
        created_at=created_at,
    )
    conversation_record = _build_conversation_record(
        pack_id=pack_id,
        session_dir=session_dir,
        session_meta=session_meta,
        episode=episode,
        events=final_events,
        completeness=completeness,
        evidence_register=evidence_register,
        source_register=source_register,
    )
    generated_report = _render_report(
        audit_card=audit_card,
        conversation_record=conversation_record,
        decision_record=decision_record,
        source_register=source_register,
    )

    event_ledger_path = pack_dir / "event-ledger.jsonl"
    _write_jsonl(event_ledger_path, final_events)
    evidence_register_path = pack_dir / "evidence-register.json"
    source_register_path = pack_dir / "source-register.json"
    decision_record_path = pack_dir / "decision-record.json"
    conversation_record_path = pack_dir / "conversation-record.json"
    audit_card_path = pack_dir / "audit-card.json"
    redaction_manifest_path = pack_dir / "redaction-manifest.json"
    transcript_path = pack_dir / "transcript-visible.md"
    audit_card_md_path = pack_dir / "audit-card.md"
    report_path = generated_dir / "report.md"

    _write_json(evidence_register_path, evidence_register)
    _write_json(source_register_path, source_register)
    _write_json(decision_record_path, decision_record)
    _write_json(conversation_record_path, conversation_record)
    _write_json(audit_card_path, audit_card)
    _write_json(redaction_manifest_path, redaction_manifest)
    transcript_path.write_text(transcript_markdown, encoding="utf-8")
    audit_card_md_path.write_text(_render_audit_card_markdown(audit_card), encoding="utf-8")
    report_path.write_text(generated_report, encoding="utf-8")

    artifact_paths = [
        audit_card_path,
        audit_card_md_path,
        conversation_record_path,
        decision_record_path,
        event_ledger_path,
        evidence_register_path,
        source_register_path,
        redaction_manifest_path,
        transcript_path,
        report_path,
    ]
    artifact_paths.extend(
        path for path in sorted(retained_dir.rglob("*")) if path.is_file()
    )
    integrity_manifest_path = write_integrity_manifest(
        pack_dir,
        artifact_paths,
        pack_id=pack_id,
        disclosure_profile="internal_full",
    )
    bundle_path = _write_bundle(pack_dir, pack_id)
    bundle_hash_path = write_bundle_hash_sidecar(
        bundle_path,
        pack_id=pack_id,
        disclosure_profile="internal_full",
    )

    return {
        "ok": True,
        "packId": pack_id,
        "path": str(pack_dir),
        "bundlePath": str(bundle_path),
        "bundleHashPath": str(bundle_hash_path),
        "scopeType": episode["scopeType"],
        "eventCount": len(final_events),
        "completeness": completeness,
        "integrityManifest": str(integrity_manifest_path),
    }


def load_pack_metadata(pack_dir: Path) -> dict[str, Any]:
    pack_dir = Path(pack_dir).resolve()
    audit_card = _load_json(pack_dir / "audit-card.json")
    retention_state = load_retention_state(pack_dir)
    audit_card["retentionClass"] = retention_state.get("retentionClass", audit_card.get("retentionClass"))
    audit_card["legalHold"] = retention_state.get("legalHold", audit_card.get("legalHold"))
    audit_card["retentionStatePath"] = str((pack_dir / "retention-state.json"))
    bundle_path = pack_dir / "bundle" / f"DSAP-{audit_card.get('packId', pack_dir.name)}.zip"
    audit_card["bundlePath"] = str(bundle_path) if bundle_path.exists() else None
    if bundle_path.exists():
        bundle_hash_path = bundle_hash_sidecar_path(bundle_path)
        audit_card["bundleHashPath"] = str(bundle_hash_path) if bundle_hash_path.exists() else None
        if bundle_hash_path.exists():
            audit_card["bundleHash"] = load_bundle_hash_sidecar(bundle_path)
    audit_card["disclosures"] = _discover_disclosures(pack_dir, str(audit_card.get("packId", pack_dir.name)))
    return audit_card


def list_packs(
    *,
    pack_root: Path | None = None,
    limit: int = 50,
    page_token: str | None = None,
) -> dict[str, Any]:
    root = (pack_root or default_pack_root()).resolve()
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if page_token is None:
        offset = 0
    else:
        try:
            offset = int(page_token)
        except ValueError as exc:
            raise ValueError("pageToken must be an integer offset.") from exc
        if offset < 0:
            raise ValueError("pageToken must be non-negative.")
    if not root.exists():
        return {"packRoot": str(root), "packs": [], "nextPageToken": None}

    items = [
        load_pack_metadata(path)
        for path in root.iterdir()
        if path.is_dir() and (path / "audit-card.json").exists()
    ]
    items.sort(key=lambda item: str(item.get("createdAt") or ""), reverse=True)
    sliced = items[offset : offset + limit]
    next_offset = offset + limit
    next_page_token = str(next_offset) if next_offset < len(items) else None
    return {"packRoot": str(root), "packs": sliced, "nextPageToken": next_page_token}


def _discover_disclosures(pack_dir: Path, pack_id: str) -> list[dict[str, Any]]:
    disclosures_root = pack_dir / "disclosures"
    if not disclosures_root.exists():
        return []
    items: list[dict[str, Any]] = []
    for derivative_dir in sorted(path for path in disclosures_root.iterdir() if path.is_dir()):
        derivative_audit_card = _load_json(derivative_dir / "audit-card.json")
        if not derivative_audit_card:
            continue
        profile = str(derivative_audit_card.get("disclosureProfile") or derivative_dir.name)
        bundle_path = derivative_dir / "bundle" / f"DSAP-{pack_id}-{profile}.zip"
        item: dict[str, Any] = {
            "disclosureProfile": profile,
            "path": str(derivative_dir),
            "bundlePath": str(bundle_path) if bundle_path.exists() else None,
        }
        if bundle_path.exists():
            hash_path = bundle_hash_sidecar_path(bundle_path)
            item["bundleHashPath"] = str(hash_path) if hash_path.exists() else None
        items.append(item)
    return items


def _materialize_evidence(
    events: list[dict[str, Any]],
    *,
    session_dir: Path,
    pack_dir: Path,
    episode: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    retained_events = deepcopy(events)
    retained_dir = pack_dir / "retained"
    seen: dict[str, dict[str, Any]] = {}

    for event in retained_events:
        evidence_list = event.get("evidence")
        if not isinstance(evidence_list, list):
            continue
        for evidence in evidence_list:
            if not isinstance(evidence, dict):
                continue
            source_text = str(evidence.get("path") or "").strip()
            if not source_text:
                continue
            source_path = _resolve_source_path(source_text, session_dir)
            entry = seen.get(source_text)
            if entry is None:
                entry = _retain_file(source_path, source_text, session_dir, retained_dir)
                seen[source_text] = entry
            retained_path = entry.get("retainedPath")
            if isinstance(retained_path, str):
                evidence["path"] = retained_path

    items = list(seen.values())
    counts = {"held": 0, "partial": 0, "not_held": 0}
    for item in items:
        counts[item["heldStatus"]] += 1
    gaps: list[str] = []
    if counts["not_held"]:
        gaps.append("One or more evidence files referenced by the Event Ledger were not retained.")
    if counts["partial"]:
        gaps.append("One or more evidence files are only partially retained.")

    items.sort(key=lambda item: item["evidenceItemId"])
    return retained_events, {
        "schemaVersion": "1.0.0",
        "generatedAt": _utc_now(),
        "conversationId": episode["conversationId"],
        "decisionEpisodeId": episode["decisionEpisodeId"],
        "items": items,
        "counts": counts,
        "gaps": gaps,
    }


def _retain_file(
    source_path: Path,
    source_text: str,
    session_dir: Path,
    retained_dir: Path,
) -> dict[str, Any]:
    evidence_id = f"evi_{uuid.uuid5(uuid.NAMESPACE_URL, source_text).hex[:16]}"
    if source_path.exists() and source_path.is_file():
        target_relative = _target_relative_path(source_path, session_dir)
        target_path = retained_dir / target_relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        return {
            "evidenceItemId": evidence_id,
            "evidenceClass": _evidence_class(source_path.name),
            "sourcePath": source_text,
            "retainedPath": Path("retained", target_relative).as_posix(),
            "heldStatus": "held",
            "sizeBytes": target_path.stat().st_size,
            "sha256": sha256_file(target_path),
            "capturedAt": _iso_from_mtime(target_path),
        }
    return {
        "evidenceItemId": evidence_id,
        "evidenceClass": _evidence_class(source_path.name or Path(source_text).name),
        "sourcePath": source_text,
        "retainedPath": None,
        "heldStatus": "not_held",
        "sizeBytes": 0,
        "sha256": None,
        "capturedAt": None,
    }


def _resolve_source_path(source_text: str, session_dir: Path) -> Path:
    source_path = Path(source_text)
    if source_path.is_absolute():
        return source_path
    return (session_dir / source_path).resolve()


def _target_relative_path(source_path: Path, session_dir: Path) -> Path:
    try:
        return source_path.resolve().relative_to(session_dir.resolve())
    except ValueError:
        digest = uuid.uuid5(uuid.NAMESPACE_URL, str(source_path)).hex[:8]
        return Path("external") / f"{digest}-{source_path.name}"


def _evidence_class(name: str) -> str:
    lowered = name.lower()
    if lowered == "session.json":
        return "session_metadata"
    if lowered.endswith("-trace.jsonl") or lowered.endswith("-trace.json"):
        return "trace_log"
    if lowered.startswith("transcript-visible"):
        return "transcript_export"
    if lowered.startswith("source-http") or lowered.startswith("source-access"):
        return "source_access_log"
    if lowered == "ui-events.jsonl":
        return "ui_event_log"
    if lowered.startswith("decision-log"):
        return "decision_log"
    return "artifact"


def _build_completeness(
    events: list[dict[str, Any]],
    evidence_register: dict[str, Any],
    source_register: dict[str, Any],
    decision_record: dict[str, Any],
    *,
    scope_type: str,
) -> dict[str, Any]:
    reasons: list[str] = []
    evidence_counts = evidence_register.get("counts", {})
    source_counts = source_register.get("counts", {})
    has_closed = any(event.get("eventType") == "conversation.closed" for event in events)
    has_visible_transcript = any(
        str(event.get("eventType", "")).startswith("message.") for event in events
    )
    has_explicit_conclusion = bool(decision_record.get("counts", {}).get("conclusions"))
    if scope_type == "conversation" and not has_closed:
        reasons.append("Conversation end marker was not retained.")
    if not has_visible_transcript:
        reasons.append("Visible transcript evidence was not retained for this scope.")
    if int(evidence_counts.get("not_held", 0)):
        reasons.append("One or more referenced evidence files are not held in the pack.")
    if int(source_counts.get("not_held", 0)):
        reasons.append("One or more source accesses are referenced but not held.")
    if int(source_counts.get("partial", 0)):
        reasons.append("One or more source accesses are only partially retained.")
    if not has_explicit_conclusion:
        reasons.append("No explicit conclusion evidence was retained for this scope.")

    grade = "A"
    if (
        reasons
        and (
            "Conversation end marker was not retained." in reasons
            or "Visible transcript evidence was not retained for this scope." in reasons
            or int(evidence_counts.get("not_held", 0))
            or int(source_counts.get("not_held", 0))
        )
    ):
        grade = "C"
    elif reasons:
        grade = "B"

    return {
        "grade": grade,
        "reasons": reasons,
        "evidenceCounts": evidence_counts,
        "sourceCounts": source_counts,
    }


def _build_audit_card(
    *,
    pack_id: str,
    episode: dict[str, Any],
    completeness: dict[str, Any],
    session_dir: Path,
    event_count: int,
    evidence_register: dict[str, Any],
    source_register: dict[str, Any],
    retention_state: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "packId": pack_id,
        "createdAt": created_at,
        "sealedOriginal": True,
        "conversationId": episode["conversationId"],
        "decisionEpisodeId": episode["decisionEpisodeId"],
        "scopeType": episode["scopeType"],
        "title": episode["title"],
        "sessionDir": str(session_dir),
        "disclosureProfile": "internal_full",
        "retentionClass": retention_state["retentionClass"],
        "legalHold": retention_state["legalHold"],
        "eventCount": event_count,
        "evidenceItemCount": len(evidence_register.get("items", [])),
        "sourceAccessCount": len(source_register.get("entries", [])),
        "completeness": completeness,
        "integrity": {
            "algorithm": "sha256",
            "manifest": "integrity-manifest.json",
            "verificationStatus": "recorded",
        },
        "sourceOfTruth": {
            "eventLedger": "event-ledger.jsonl",
            "retainedEvidenceRoot": "retained/",
        },
        "requiredOutputs": list(REQUIRED_OUTPUTS),
        "caveats": completeness["reasons"],
    }


def _build_original_redaction_manifest(pack_id: str) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "generatedAt": _utc_now(),
        "packId": pack_id,
        "disclosureProfile": "internal_full",
        "redactions": [],
        "removedFiles": [],
        "notes": ["Original sealed pack. No redactions applied."],
    }


def _build_pack_events(
    *,
    conversation_id: str,
    decision_episode_id: str,
    base_sequence: int,
    scope_type: str,
    pack_id: str,
    retention_state: dict[str, Any],
    created_at: str,
) -> list[dict[str, Any]]:
    next_sequence = base_sequence
    events: list[dict[str, Any]] = []
    if scope_type == "snapshot":
        next_sequence += 1
        events.append(
            _audit_event(
                event_type="conversation.snapshot_requested",
                conversation_id=conversation_id,
                decision_episode_id=decision_episode_id,
                sequence=next_sequence,
                occurred_at=created_at,
                evidence_path="audit-card.json",
                data={"packId": pack_id, "scopeType": scope_type},
                message="Audit snapshot requested.",
            )
        )
    next_sequence += 1
    events.append(
        _audit_event(
            event_type="audit_pack.created",
            conversation_id=conversation_id,
            decision_episode_id=decision_episode_id,
            sequence=next_sequence,
            occurred_at=created_at,
            evidence_path="audit-card.json",
            data={
                "packId": pack_id,
                "scopeType": scope_type,
                "retentionClass": retention_state["retentionClass"],
                "legalHold": retention_state["legalHold"],
            },
            message="Decision Support Audit Pack created.",
        )
    )
    if retention_state.get("legalHold"):
        next_sequence += 1
        history = retention_state.get("history") or []
        hold_timestamp = history[-1].get("occurredAt") if history else created_at
        events.append(
            _audit_event(
                event_type="audit_pack.legal_hold_applied",
                conversation_id=conversation_id,
                decision_episode_id=decision_episode_id,
                sequence=next_sequence,
                occurred_at=str(hold_timestamp),
                evidence_path="retention-state.json",
                data={
                    "packId": pack_id,
                    "retentionClass": retention_state["retentionClass"],
                    "legalHold": True,
                },
                message="Legal hold applied to the audit pack.",
            )
        )
    next_sequence += 1
    events.append(
        _audit_event(
            event_type="audit_pack.sealed",
            conversation_id=conversation_id,
            decision_episode_id=decision_episode_id,
            sequence=next_sequence,
            occurred_at=_utc_now(),
            evidence_path="integrity-manifest.json",
            data={"packId": pack_id, "algorithm": "sha256"},
            message="Decision Support Audit Pack sealed.",
        )
    )
    return events


def _audit_event(
    *,
    event_type: str,
    conversation_id: str,
    decision_episode_id: str,
    sequence: int,
    occurred_at: str,
    evidence_path: str,
    data: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    event = {
        "schemaVersion": EVENT_SCHEMA_VERSION,
        "eventType": event_type,
        "conversationId": conversation_id,
        "decisionEpisodeId": decision_episode_id,
        "occurredAt": occurred_at,
        "actor": {"kind": "system", "id": "dsap"},
        "channel": "session_metadata",
        "status": "observed",
        "message": message,
        "data": data,
        "correlation": {"sourceSequence": sequence},
        "evidence": [{"kind": "file", "path": evidence_path}],
    }
    event["sequence"] = sequence
    event["eventId"] = _event_id(conversation_id, sequence, event_type, occurred_at)
    return event


def _renumber_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        deepcopy(events),
        key=lambda event: (
            str(event.get("occurredAt") or ""),
            int(event.get("sequence", 0)),
            str(event.get("eventType") or ""),
        ),
    )
    for sequence, event in enumerate(ordered, start=1):
        correlation = event.get("correlation")
        if not isinstance(correlation, dict):
            correlation = {}
            event["correlation"] = correlation
        if "sourceSequence" not in correlation and event.get("sequence") is not None:
            correlation["sourceSequence"] = event.get("sequence")
        event["sequence"] = sequence
        event["eventId"] = _event_id(
            str(event.get("conversationId") or ""),
            sequence,
            str(event.get("eventType") or ""),
            str(event.get("occurredAt") or ""),
        )
    return ordered


def _build_conversation_record(
    *,
    pack_id: str,
    session_dir: Path,
    session_meta: dict[str, Any],
    episode: dict[str, Any],
    events: list[dict[str, Any]],
    completeness: dict[str, Any],
    evidence_register: dict[str, Any],
    source_register: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "generatedAt": _utc_now(),
        "packId": pack_id,
        "conversationId": episode["conversationId"],
        "decisionEpisode": episode,
        "sessionDir": str(session_dir),
        "sessionMetadata": session_meta,
        "eventCount": len(events),
        "eventTypeCounts": dict(Counter(str(event.get("eventType")) for event in events)),
        "evidenceItemCount": len(evidence_register.get("items", [])),
        "sourceAccessCount": len(source_register.get("entries", [])),
        "completeness": completeness,
        "sourceOfTruth": {
            "eventLedger": "event-ledger.jsonl",
            "retainedEvidenceRoot": "retained/",
        },
        "gaps": completeness["reasons"],
    }


def _render_transcript(events: list[dict[str, Any]]) -> str:
    lines = ["# Visible Transcript", ""]
    visible = [
        event
        for event in events
        if event.get("eventType")
        in {"message.user_visible", "message.assistant_visible", "message.assistant_conclusion"}
    ]
    if not visible:
        lines.append("No visible transcript evidence retained for this pack.")
        lines.append("")
        return "\n".join(lines)
    for event in visible:
        role = "assistant"
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        if event.get("eventType") == "message.user_visible":
            role = "user"
        elif event.get("eventType") == "message.assistant_conclusion":
            role = "assistant_conclusion"
        lines.append(f"## {role} @ {event.get('occurredAt')}")
        lines.append(str(data.get("content") or event.get("message") or ""))
        lines.append("")
    return "\n".join(lines)


def _render_report(
    *,
    audit_card: dict[str, Any],
    conversation_record: dict[str, Any],
    decision_record: dict[str, Any],
    source_register: dict[str, Any],
) -> str:
    lines = [
        "# Decision Support Audit Pack Report",
        "",
        f"Pack ID: {audit_card['packId']}",
        f"Scope: {audit_card['scopeType']}",
        f"Completeness grade: {audit_card['completeness']['grade']}",
        f"Retention class: {audit_card['retentionClass']}",
        f"Legal hold: {audit_card['legalHold']}",
        "",
        "## Coverage",
        f"- Events: {conversation_record['eventCount']}",
        f"- Evidence items: {conversation_record['evidenceItemCount']}",
        f"- Source accesses: {conversation_record['sourceAccessCount']}",
        "",
        "## Decision Record",
        f"- Assumptions: {decision_record['counts']['assumptions']}",
        f"- Uncertainties: {decision_record['counts']['uncertainties']}",
        f"- Conclusions: {decision_record['counts']['conclusions']}",
        "",
        "## Source Register",
        f"- Held: {source_register['counts']['held']}",
        f"- Partial: {source_register['counts']['partial']}",
        f"- Not held: {source_register['counts']['not_held']}",
    ]
    if audit_card["completeness"]["reasons"]:
        lines.extend(["", "## Gaps"])
        lines.extend(f"- {reason}" for reason in audit_card["completeness"]["reasons"])
    lines.append("")
    return "\n".join(lines)


def _render_audit_card_markdown(audit_card: dict[str, Any]) -> str:
    lines = [
        "# DSAP Audit Card",
        "",
        f"- Pack ID: {audit_card['packId']}",
        f"- Scope: {audit_card['scopeType']}",
        f"- Title: {audit_card['title']}",
        f"- Completeness grade: {audit_card['completeness']['grade']}",
        f"- Disclosure profile: {audit_card['disclosureProfile']}",
        f"- Retention class: {audit_card['retentionClass']}",
        f"- Legal hold: {audit_card['legalHold']}",
        f"- Event count: {audit_card['eventCount']}",
        f"- Evidence items: {audit_card['evidenceItemCount']}",
        f"- Source accesses: {audit_card['sourceAccessCount']}",
        "",
        "## Caveats",
    ]
    caveats = audit_card.get("caveats") or ["None declared."]
    lines.extend(f"- {item}" for item in caveats)
    lines.append("")
    return "\n".join(lines)


def _write_bundle(pack_dir: Path, pack_id: str) -> Path:
    bundle_path = pack_dir / "bundle" / f"DSAP-{pack_id}.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(pack_dir.rglob("*")):
            if path.is_dir():
                continue
            if path == bundle_path:
                continue
            if "disclosures" in path.parts:
                continue
            archive.write(path, path.relative_to(pack_dir))
    return bundle_path


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _iso_from_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat().replace("+00:00", "Z")


def _event_id(conversation_id: str, sequence: int, event_type: str, occurred_at: str) -> str:
    source = f"{conversation_id}:{sequence}:{event_type}:{occurred_at}"
    return f"evt_{uuid.uuid5(uuid.NAMESPACE_URL, source).hex[:16]}"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble a Decision Support Audit Pack.")
    parser.add_argument("session_dir", help="Session directory containing trace artifacts.")
    parser.add_argument("--output-root", help="Optional output directory for DSAP packs.")
    parser.add_argument(
        "--scope-type",
        default="conversation",
        help="conversation, episode, or snapshot.",
    )
    parser.add_argument("--episode-id")
    parser.add_argument("--episode-title")
    parser.add_argument("--episode-start-sequence", type=int)
    parser.add_argument("--episode-end-sequence", type=int)
    parser.add_argument("--retention-class", default=DEFAULT_RETENTION_CLASS)
    parser.add_argument("--legal-hold", action="store_true")
    args = parser.parse_args()

    result = build_audit_pack(
        Path(args.session_dir),
        output_root=Path(args.output_root).resolve() if args.output_root else None,
        scope_type=args.scope_type,
        episode_id=args.episode_id,
        episode_title=args.episode_title,
        episode_start_sequence=args.episode_start_sequence,
        episode_end_sequence=args.episode_end_sequence,
        retention_class=normalize_retention_class(args.retention_class),
        legal_hold=args.legal_hold,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
