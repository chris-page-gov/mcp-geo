from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from server.audit.disclosure import build_redacted_pack
from server.audit.integrity import load_bundle_hash_sidecar, verify_pack_integrity
from server.audit.normalise import build_event_ledger, write_event_ledger
from server.audit.pack_builder import (
    build_audit_pack,
    default_pack_root,
    list_packs,
    load_pack_metadata,
    resolve_pack_dir,
)
from server.audit.retention import write_retention_state
from server.mcp.http_route_auth import apply_auth_headers, authorize_http_route


router = APIRouter()
_PACK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class AuditNormaliseRequest(BaseModel):
    sessionDir: str = Field(..., description="Session directory containing trace artifacts.")
    outputPath: str | None = Field(default=None, description="Optional event-ledger output path.")


class AuditPackRequest(BaseModel):
    sessionDir: str = Field(..., description="Session directory containing trace artifacts.")
    outputRoot: str | None = Field(default=None, description="Optional pack output root.")
    scopeType: str = Field(default="conversation", description="conversation, episode, or snapshot")
    episodeId: str | None = Field(default=None)
    episodeTitle: str | None = Field(default=None)
    episodeStartSequence: int | None = Field(default=None)
    episodeEndSequence: int | None = Field(default=None)
    retentionClass: str = Field(default="default_operational")
    legalHold: bool = Field(default=False)


class AuditRedactRequest(BaseModel):
    disclosureProfile: str = Field(..., description="internal_full, internal_restricted, or foi_redacted")


class AuditLegalHoldRequest(BaseModel):
    legalHold: bool = Field(default=True)
    retentionClass: str | None = Field(default=None)
    reason: str | None = Field(default=None)


def _authorize_audit_route(request: Request, response: Response) -> dict[str, str] | Response:
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    return auth_headers


def _audit_pack_root() -> Path:
    return default_pack_root().resolve()


def _resolve_under_pack_root(raw_path: str, *, label: str) -> Path:
    try:
        root = _audit_pack_root()
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = root / candidate
        resolved = candidate.resolve()
        resolved.relative_to(root)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{label} must be inside the configured audit pack root",
        ) from exc
    return resolved


def _resolve_http_pack_dir(pack_id: str) -> Path:
    if not _PACK_ID_RE.fullmatch(pack_id) or ".." in pack_id.split("."):
        raise HTTPException(status_code=400, detail="Invalid pack id")
    pack_dir = resolve_pack_dir(pack_id).resolve()
    try:
        pack_dir.relative_to(_audit_pack_root())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid pack id") from exc
    return pack_dir


@router.post("/audit/normalise")
def audit_normalise(
    payload: AuditNormaliseRequest,
    request: Request,
    response: Response,
) -> Any:
    auth_headers = _authorize_audit_route(request, response)
    if isinstance(auth_headers, Response):
        return auth_headers
    session_dir = Path(payload.sessionDir).resolve()
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session directory not found")
    output_path = (
        _resolve_under_pack_root(payload.outputPath, label="outputPath")
        if payload.outputPath
        else None
    )
    output = write_event_ledger(
        session_dir,
        output_path=output_path,
    )
    events = build_event_ledger(session_dir)
    return {
        "ok": True,
        "path": str(output),
        "eventCount": len(events),
        "conversationId": events[0]["conversationId"] if events else session_dir.name,
    }


@router.post("/audit/packs")
def audit_pack_create(payload: AuditPackRequest, request: Request, response: Response) -> Any:
    auth_headers = _authorize_audit_route(request, response)
    if isinstance(auth_headers, Response):
        return auth_headers
    session_dir = Path(payload.sessionDir).resolve()
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session directory not found")
    output_root = (
        _resolve_under_pack_root(payload.outputRoot, label="outputRoot")
        if payload.outputRoot
        else default_pack_root()
    )
    try:
        return build_audit_pack(
            session_dir,
            output_root=output_root,
            scope_type=payload.scopeType,
            episode_id=payload.episodeId,
            episode_title=payload.episodeTitle,
            episode_start_sequence=payload.episodeStartSequence,
            episode_end_sequence=payload.episodeEndSequence,
            retention_class=payload.retentionClass,
            legal_hold=payload.legalHold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/audit/packs")
def audit_pack_list(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=200),
    pageToken: str | None = Query(default=None),
) -> Any:
    auth_headers = _authorize_audit_route(request, response)
    if isinstance(auth_headers, Response):
        return auth_headers
    try:
        return list_packs(limit=limit, page_token=pageToken)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/audit/packs/{pack_id}")
def audit_pack_get(pack_id: str, request: Request, response: Response) -> Any:
    auth_headers = _authorize_audit_route(request, response)
    if isinstance(auth_headers, Response):
        return auth_headers
    pack_dir = _resolve_http_pack_dir(pack_id)
    if not pack_dir.exists():
        raise HTTPException(status_code=404, detail="Pack not found")
    return load_pack_metadata(pack_dir)


@router.get("/audit/packs/{pack_id}/bundle")
def audit_pack_bundle(pack_id: str, request: Request, response: Response) -> Response:
    auth_headers = _authorize_audit_route(request, response)
    if isinstance(auth_headers, Response):
        return auth_headers
    pack_dir = _resolve_http_pack_dir(pack_id)
    if not pack_dir.exists():
        raise HTTPException(status_code=404, detail="Pack not found")
    bundle_path = pack_dir / "bundle" / f"DSAP-{pack_id}.zip"
    if not bundle_path.exists():
        raise HTTPException(status_code=404, detail="Bundle not found")
    return FileResponse(
        bundle_path,
        media_type="application/zip",
        filename=bundle_path.name,
        headers=auth_headers,
    )


@router.get("/audit/packs/{pack_id}/bundle/hash")
def audit_pack_bundle_hash(pack_id: str, request: Request, response: Response) -> Any:
    auth_headers = _authorize_audit_route(request, response)
    if isinstance(auth_headers, Response):
        return auth_headers
    pack_dir = _resolve_http_pack_dir(pack_id)
    if not pack_dir.exists():
        raise HTTPException(status_code=404, detail="Pack not found")
    bundle_path = pack_dir / "bundle" / f"DSAP-{pack_id}.zip"
    if not bundle_path.exists():
        raise HTTPException(status_code=404, detail="Bundle not found")
    hash_path = bundle_path.with_suffix(bundle_path.suffix + ".sha256.json")
    if not hash_path.exists():
        raise HTTPException(status_code=404, detail="Bundle hash sidecar not found")
    return load_bundle_hash_sidecar(bundle_path)


@router.post("/audit/packs/{pack_id}/verify")
def audit_pack_verify(pack_id: str, request: Request, response: Response) -> Any:
    auth_headers = _authorize_audit_route(request, response)
    if isinstance(auth_headers, Response):
        return auth_headers
    pack_dir = _resolve_http_pack_dir(pack_id)
    if not pack_dir.exists():
        raise HTTPException(status_code=404, detail="Pack not found")
    return verify_pack_integrity(pack_dir)


@router.post("/audit/packs/{pack_id}/redact")
def audit_pack_redact(
    pack_id: str,
    payload: AuditRedactRequest,
    request: Request,
    response: Response,
) -> Any:
    auth_headers = _authorize_audit_route(request, response)
    if isinstance(auth_headers, Response):
        return auth_headers
    pack_dir = _resolve_http_pack_dir(pack_id)
    if not pack_dir.exists():
        raise HTTPException(status_code=404, detail="Pack not found")
    try:
        return build_redacted_pack(pack_dir, disclosure_profile=payload.disclosureProfile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/audit/packs/{pack_id}/legal-hold")
def audit_pack_legal_hold(
    pack_id: str,
    payload: AuditLegalHoldRequest,
    request: Request,
    response: Response,
) -> Any:
    auth_headers = _authorize_audit_route(request, response)
    if isinstance(auth_headers, Response):
        return auth_headers
    pack_dir = _resolve_http_pack_dir(pack_id)
    if not pack_dir.exists():
        raise HTTPException(status_code=404, detail="Pack not found")
    try:
        state = write_retention_state(
            pack_dir,
            retention_class=payload.retentionClass,
            legal_hold=payload.legalHold,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "packId": pack_id, "retentionState": state}
