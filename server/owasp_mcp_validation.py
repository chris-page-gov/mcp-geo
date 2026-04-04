from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any

VALID_STATUSES = {"pass", "fail", "not_applicable"}
REQUIREMENT_WEIGHTS = {"minimum_bar": 5, "required": 3, "recommended": 1}
SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
SAFE_BY_DESIGN_CROSS_LINKS = {
    "OMCP-DATA-002": ["SBD-REV-003", "SBD-REV-004"],
    "OMCP-AUTH-002": ["SBD-REV-003"],
    "OMCP-DEPLOY-003": ["SBD-REV-007"],
}


@dataclass(frozen=True)
class ToolSnapshot:
    name: str
    version: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


@dataclass(frozen=True)
class ValidatorPaths:
    repo_root: Path
    control_catalog: Path
    tool_risk_inventory: Path
    attestation_schema: Path
    attestation_dir: Path
    tool_manifest_lock: Path
    tool_manifest_signature: Path
    tool_manifest_public_key: Path
    safe_by_design_log: Path
    workflow_file: Path
    wrapper_script: Path


class ValidationDataError(RuntimeError):
    pass


def default_validator_paths(repo_root: str | Path) -> ValidatorPaths:
    root = Path(repo_root).resolve()
    return ValidatorPaths(
        repo_root=root,
        control_catalog=root / "security/owasp_mcp/control_catalog.json",
        tool_risk_inventory=root / "security/owasp_mcp/tool_risk_inventory.json",
        attestation_schema=root / "security/owasp_mcp/attestations/schema.json",
        attestation_dir=root / "security/owasp_mcp/attestations",
        tool_manifest_lock=root / "security/owasp_mcp/tool_manifest.lock.json",
        tool_manifest_signature=root / "security/owasp_mcp/tool_manifest.lock.json.sig",
        tool_manifest_public_key=root / "security/owasp_mcp/tool_manifest.pub.pem",
        safe_by_design_log=root / "safe-by-design.json",
        workflow_file=root / ".github/workflows/ci.yml",
        wrapper_script=root / "scripts/validate-owasp-mcp-local",
    )


def utc_now() -> datetime:
    return datetime.now(UTC)


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # codeql[py/clear-text-storage-sensitive-data]
    path.write_text(pretty_json(payload), encoding="utf-8")


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _evidence(path: str | Path, detail: str) -> dict[str, str]:
    return {"path": str(path), "detail": detail}


def tool_snapshots_from_registry() -> list[ToolSnapshot]:
    import server.mcp.tools  # noqa: F401
    from tools.registry import all_tools

    snapshots: list[ToolSnapshot] = []
    for tool in all_tools():
        snapshots.append(
            ToolSnapshot(
                name=tool.name,
                version=tool.version,
                description=tool.description,
                input_schema=tool.input_schema,
                output_schema=tool.output_schema,
            )
        )
    return snapshots


def build_tool_manifest(registered_tools: list[ToolSnapshot]) -> dict[str, Any]:
    tools = []
    for tool in sorted(registered_tools, key=lambda item: item.name):
        tools.append(
            {
                "name": tool.name,
                "version": tool.version,
                "description": tool.description,
                "description_sha256": sha256_text(tool.description),
                "input_schema_sha256": sha256_text(canonical_json(tool.input_schema)),
                "output_schema_sha256": sha256_text(canonical_json(tool.output_schema)),
            }
        )
    return {
        "schema_version": 1,
        "project": "mcp-geo",
        "manifest_type": "owasp-mcp-tool-lock",
        "tool_count": len(tools),
        "tools": tools,
    }


def verify_signature(
    lock_path: Path, signature_path: Path, public_key_path: Path
) -> tuple[bool, str]:
    missing = [path for path in (lock_path, signature_path, public_key_path) if not path.exists()]
    if missing:
        names = ", ".join(str(path) for path in missing)
        return False, f"Missing manifest verification artifact(s): {names}"
    try:
        result = subprocess.run(
            [
                "openssl",
                "dgst",
                "-sha256",
                "-verify",
                str(public_key_path),
                "-signature",
                str(signature_path),
                str(lock_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "openssl is not available to verify the signed tool manifest"
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode != 0:
        return False, output or "Tool manifest signature verification failed"
    return True, output or "Verified OK"


def _validate_required_fields(item: dict[str, Any], fields: list[str], label: str) -> list[str]:
    errors: list[str] = []
    for field in fields:
        if field not in item:
            errors.append(f"{label} missing required field '{field}'")
    return errors


def load_control_catalog(path: Path) -> dict[str, Any]:
    catalog = load_json(path)
    if not isinstance(catalog, dict):
        raise ValidationDataError("control catalog must be a JSON object")
    controls = catalog.get("controls")
    if not isinstance(controls, list) or not controls:
        raise ValidationDataError("control catalog must define a non-empty 'controls' list")
    ids: set[str] = set()
    for control in controls:
        if not isinstance(control, dict):
            raise ValidationDataError("control catalog entries must be JSON objects")
        missing = _validate_required_fields(
            control,
            [
                "id",
                "title",
                "section",
                "source_quote",
                "requirement_level",
                "applies_when",
                "check_type",
                "severity",
                "pass_criteria",
                "remediation_template",
            ],
            "control",
        )
        if missing:
            raise ValidationDataError("; ".join(missing))
        control_id = str(control["id"])
        if control_id in ids:
            raise ValidationDataError(f"duplicate control id '{control_id}'")
        ids.add(control_id)
    return catalog


RISK_FIELDS = [
    "name",
    "side_effect_level",
    "data_sensitivity",
    "network_write",
    "high_risk_action",
    "requires_user_context",
]


def load_tool_risk_inventory(path: Path) -> dict[str, Any]:
    inventory = load_json(path)
    if not isinstance(inventory, dict):
        raise ValidationDataError("tool risk inventory must be a JSON object")
    tools = inventory.get("tools")
    if not isinstance(tools, list):
        raise ValidationDataError("tool risk inventory must define a 'tools' list")
    seen: set[str] = set()
    for tool in tools:
        if not isinstance(tool, dict):
            raise ValidationDataError("tool risk entries must be JSON objects")
        missing = _validate_required_fields(tool, RISK_FIELDS, "tool risk entry")
        if missing:
            raise ValidationDataError("; ".join(missing))
        name = str(tool["name"])
        if name in seen:
            raise ValidationDataError(f"duplicate tool risk entry '{name}'")
        seen.add(name)
    return inventory


def load_safe_by_design_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    payload = load_json(path)
    revisions = payload.get("revisions", []) if isinstance(payload, dict) else []
    return {
        str(entry.get("id"))
        for entry in revisions
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }


def validate_attestation_document(
    document: dict[str, Any],
    schema: dict[str, Any],
    *,
    path: Path,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return [f"attestation {path} must be a JSON object"]
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise ValidationDataError("attestation schema must define a 'required' list")
    errors.extend(
        _validate_required_fields(document, [str(item) for item in required], f"attestation {path}")
    )
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise ValidationDataError("attestation schema must define a 'properties' object")
    for field, definition in properties.items():
        if field not in document:
            continue
        expected_type = definition.get("type") if isinstance(definition, dict) else None
        value = document[field]
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"attestation {path} field '{field}' must be a string")
        if expected_type == "array" and not isinstance(value, list):
            errors.append(f"attestation {path} field '{field}' must be an array")
        if expected_type == "object" and not isinstance(value, dict):
            errors.append(f"attestation {path} field '{field}' must be an object")
    if isinstance(document.get("control_ids"), list):
        if not all(isinstance(item, str) and item.strip() for item in document["control_ids"]):
            errors.append(f"attestation {path} control_ids must contain non-empty strings")
    if isinstance(document.get("artifact_hashes"), dict):
        for key, value in document["artifact_hashes"].items():
            if not isinstance(key, str) or not isinstance(value, str):
                errors.append(
                    f"attestation {path} artifact_hashes must map string names to string hashes"
                )
    for field in ("verified_at", "expires_at"):
        if field in document and isinstance(document[field], str):
            try:
                parse_datetime(document[field])
            except ValueError:
                errors.append(f"attestation {path} field '{field}' must be ISO-8601")
    return errors


def load_attestations(
    attestation_dir: Path,
    attestation_schema_path: Path,
    *,
    profile: str,
    now: datetime,
    controls: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    schema = load_json(attestation_schema_path)
    if not isinstance(schema, dict):
        raise ValidationDataError("attestation schema must be a JSON object")
    control_index = {str(control["id"]): control for control in controls}
    attestations_by_control: dict[str, list[dict[str, Any]]] = {}
    issues: list[str] = []
    if not attestation_dir.exists():
        return attestations_by_control, issues
    for path in sorted(attestation_dir.glob("*.json")):
        if path.name == attestation_schema_path.name:
            continue
        payload = load_json(path)
        errors = validate_attestation_document(payload, schema, path=path)
        if errors:
            issues.extend(errors)
            continue
        environment = str(payload.get("environment", "")).strip()
        if environment not in {profile, "all"}:
            continue
        verified_at = parse_datetime(str(payload["verified_at"]))
        stale_reasons: list[str] = []
        if "expires_at" in payload:
            expires_at = parse_datetime(str(payload["expires_at"]))
            if expires_at < now:
                stale_reasons.append("expired")
        stale = False
        max_age_days = 3650
        for control_id in payload.get("control_ids", []):
            control = control_index.get(control_id)
            control_max_age = control.get("attestation_max_age_days") if control else None
            if isinstance(control_max_age, int):
                max_age_days = min(max_age_days, control_max_age)
        if verified_at < now - timedelta(days=max_age_days):
            stale = True
            stale_reasons.append(f"verified_at older than {max_age_days} days")
        enriched = dict(payload)
        enriched["_path"] = str(path)
        enriched["_stale"] = stale or bool(stale_reasons)
        enriched["_stale_reasons"] = stale_reasons
        for control_id in payload.get("control_ids", []):
            attestations_by_control.setdefault(control_id, []).append(enriched)
    return attestations_by_control, issues


def evaluate_applicability(control: dict[str, Any], facts: dict[str, Any], profile: str) -> bool:
    applies_when = control.get("applies_when", {})
    if not isinstance(applies_when, dict):
        raise ValidationDataError(f"control {control['id']} applies_when must be an object")
    profiles = applies_when.get("profiles")
    if isinstance(profiles, list) and profile not in profiles:
        return False
    if applies_when.get("requires_remote_mcp") and not facts["remote_mcp"]:
        return False
    if applies_when.get("requires_sessions") and not facts["session_support"]:
        return False
    if applies_when.get("requires_high_risk_tools") and not facts["high_risk_tools"]:
        return False
    if applies_when.get("requires_restricted_tools") and not facts["restricted_tools"]:
        return False
    if applies_when.get("requires_secret_delivery") and not facts["uses_secret_settings"]:
        return False
    return True


def _workflow_contains(workflow_text: str, *needles: str) -> bool:
    lowered = workflow_text.lower()
    return all(needle.lower() in lowered for needle in needles)


def _workflow_has_ruff_gate(workflow_text: str) -> bool:
    return any(
        _workflow_contains(workflow_text, needle)
        for needle in ("ruff check", "./scripts/ruff-local", "scripts/ruff-local")
    )


def collect_repo_facts(
    paths: ValidatorPaths,
    inventory: dict[str, Any],
    registered_tools: list[ToolSnapshot],
) -> dict[str, Any]:
    http_transport = _read_text(paths.repo_root / "server/mcp/http_transport.py")
    tools_router = _read_text(paths.repo_root / "server/mcp/tools.py")
    config_text = _read_text(paths.repo_root / "server/config.py")
    security_text = _read_text(paths.repo_root / "server/security.py")
    maps_proxy_text = _read_text(paths.repo_root / "server/maps_proxy.py")
    workflow_text = _read_text(paths.workflow_file)
    dockerfile_text = _read_text(paths.repo_root / "Dockerfile")
    audit_pack_builder = _read_text(paths.repo_root / "server/audit/pack_builder.py")
    audit_redaction = _read_text(paths.repo_root / "server/audit/redaction.py")
    audit_integrity = _read_text(paths.repo_root / "server/audit/integrity.py")

    inventory_entries = inventory.get("tools", []) if isinstance(inventory, dict) else []
    inventory_names = [
        str(entry.get("name")) for entry in inventory_entries if isinstance(entry, dict)
    ]
    registered_names = [tool.name for tool in registered_tools]
    high_risk_tools = [
        str(entry["name"])
        for entry in inventory_entries
        if isinstance(entry, dict) and bool(entry.get("high_risk_action"))
    ]
    restricted_tools = [
        str(entry["name"])
        for entry in inventory_entries
        if isinstance(entry, dict) and entry.get("data_sensitivity") == "restricted"
    ]
    uses_secret_settings = any(
        marker in config_text for marker in ("OS_API_KEY", "NOMIS_UID", "NOMIS_SIGNATURE")
    )

    return {
        "remote_mcp": '@router.post("/mcp")' in http_transport,
        "session_support": "_SESSION_STATE" in http_transport,
        "session_cleanup": "_cleanup_sessions" in http_transport
        and "_SESSION_TTL_SECONDS" in http_transport,
        "jsonrpc_validation": all(
            needle in http_transport
            for needle in (
                'msg.get("jsonrpc") != JSONRPC',
                "if not isinstance(params, dict)",
                'content=_resp_error(msg_id, -32602, "Invalid params")',
            )
        ),
        "inventory_names": inventory_names,
        "registered_names": registered_names,
        "missing_inventory_names": sorted(set(registered_names) - set(inventory_names)),
        "unexpected_inventory_names": sorted(set(inventory_names) - set(registered_names)),
        "high_risk_tools": sorted(high_risk_tools),
        "restricted_tools": sorted(restricted_tools),
        "all_tools_have_schemas": all(
            bool(tool.input_schema) and bool(tool.output_schema) for tool in registered_tools
        ),
        "tool_list_minimized": '"tools": sanitized[start:end]' in tools_router
        and '"/tools/describe"' in tools_router,
        "structured_json_invocation": all(
            needle in (tools_router + "\n" + http_transport)
            for needle in (
                "Request body must be a JSON object",
                "Payload must be object",
                'tool_name = data.get("tool")',
            )
        ),
        "redaction_support": all(
            needle in security_text
            for needle in ("configured_secrets", "mask_in_text", "mask_in_value")
        ),
        "output_size_limits": any(
            needle in (config_text + "\n" + _read_text(paths.repo_root / "tools/os_features.py"))
            for needle in ("OS_EXPORT_INLINE_MAX_BYTES", "OS_FEATURES_MAX_LIMIT")
        ),
        "token_passthrough_detected": '{"Authorization": bearer_value}' in maps_proxy_text,
        "docker_non_root": "USER appuser" in dockerfile_text,
        "workflow_text": workflow_text,
        "wrapper_exists": paths.wrapper_script.exists(),
        "audit_trail_support": all(
            needle in (audit_pack_builder + "\n" + audit_redaction + "\n" + audit_integrity)
            for needle in ("redaction-manifest.json", "sha256", "event-ledger.jsonl")
        ),
        "uses_secret_settings": uses_secret_settings,
    }


def _attestation_outcome(
    control: dict[str, Any],
    attestations_by_control: dict[str, list[dict[str, Any]]],
) -> tuple[str, str, list[dict[str, str]]]:
    matches = attestations_by_control.get(str(control["id"]), [])
    if not matches:
        return "fail", "Missing required attestation evidence.", []
    evidence = [
        _evidence(item["_path"], str(item.get("title", control["title"]))) for item in matches
    ]
    stale = [item for item in matches if item.get("_stale")]
    if stale:
        reasons: list[str] = []
        for item in stale:
            reasons.extend(str(reason) for reason in item.get("_stale_reasons", []))
        detail = ", ".join(sorted(set(reasons))) or "stale attestation"
        return "fail", f"Attestation evidence is stale: {detail}", evidence
    return "pass", "Valid attestation evidence present.", evidence


def evaluate_control(
    control: dict[str, Any],
    *,
    profile: str,
    facts: dict[str, Any],
    attestations_by_control: dict[str, list[dict[str, Any]]],
    manifest_ok: bool,
    manifest_message: str,
    manifest_matches_registry: bool,
    previous_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    control_id = str(control["id"])
    if not evaluate_applicability(control, facts, profile):
        return {
            **control,
            "status": "not_applicable",
            "rationale": "Control does not apply for the current profile/tool inventory.",
            "evidence": [],
        }

    status = "fail"
    rationale = "Control failed."
    evidence: list[dict[str, str]] = []

    if control_id == "OMCP-ARCH-001":
        status = "pass" if facts["remote_mcp"] else "fail"
        rationale = (
            "Remote /mcp transport is present and classified as remotely reachable."
            if status == "pass"
            else "Remote /mcp transport was not found."
        )
        evidence = [_evidence("server/mcp/http_transport.py", "FastAPI route declaration for /mcp")]
    elif control_id in {
        "OMCP-ARCH-002",
        "OMCP-AUTH-001",
        "OMCP-AUTH-003",
        "OMCP-ARCH-005",
        "OMCP-TOOL-003",
        "OMCP-PI-002",
        "OMCP-DEPLOY-001",
        "OMCP-DEPLOY-002",
        "OMCP-GOV-002",
        "OMCP-GOV-003",
        "OMCP-PI-001",
        "OMCP-AUTH-004",
    }:
        status, rationale, evidence = _attestation_outcome(control, attestations_by_control)
    elif control_id == "OMCP-ARCH-003":
        status = "pass" if facts["jsonrpc_validation"] else "fail"
        rationale = (
            "JSON-RPC requests are validated before dispatch."
            if status == "pass"
            else "JSON-RPC request validation checks are incomplete."
        )
        evidence = [
            _evidence("server/mcp/http_transport.py", "JSON-RPC parse and params validation")
        ]
    elif control_id == "OMCP-ARCH-004":
        status = "pass" if facts["session_support"] and facts["session_cleanup"] else "fail"
        rationale = (
            "Session state is isolated and stale sessions are cleaned up deterministically."
            if status == "pass"
            else "Session state or cleanup hooks are missing."
        )
        evidence = [
            _evidence("server/mcp/http_transport.py", "Session map, TTL, and cleanup logic")
        ]
    elif control_id == "OMCP-TOOL-001":
        missing = facts["missing_inventory_names"]
        unexpected = facts["unexpected_inventory_names"]
        status = "pass" if not missing and not unexpected else "fail"
        details: list[str] = []
        if missing:
            details.append(f"missing entries: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected entries: {', '.join(unexpected)}")
        rationale = "Tool risk inventory matches the registered tool set."
        if details:
            rationale = "Tool risk inventory is out of sync: " + "; ".join(details)
        evidence = [
            _evidence(
                "security/owasp_mcp/tool_risk_inventory.json", "Explicit per-tool risk metadata"
            )
        ]
    elif control_id == "OMCP-TOOL-002":
        status = "pass" if manifest_ok and manifest_matches_registry else "fail"
        if not manifest_matches_registry:
            rationale = "Signed tool manifest does not match the current registered tool contracts."
        else:
            rationale = (
                "Signed tool manifest matches the registered tool contracts."
                if status == "pass"
                else manifest_message
            )
        evidence = [
            _evidence(
                "security/owasp_mcp/tool_manifest.lock.json", "Committed tool manifest lockfile"
            ),
            _evidence(
                "security/owasp_mcp/tool_manifest.lock.json.sig",
                manifest_message,
            ),
        ]
    elif control_id == "OMCP-TOOL-004":
        status = "pass" if facts["tool_list_minimized"] else "fail"
        rationale = (
            "Tool names are listed separately from richer describe metadata."
            if status == "pass"
            else "Tool discovery surfaces are not minimized to list-versus-describe behavior."
        )
        evidence = [
            _evidence("server/mcp/tools.py", "Separate /tools/list and /tools/describe surfaces")
        ]
    elif control_id == "OMCP-DATA-001":
        status = "pass" if facts["all_tools_have_schemas"] else "fail"
        rationale = (
            "Every registered tool exposes input/output schemas for structured validation."
            if status == "pass"
            else "One or more tools are missing input/output schemas."
        )
        evidence = [
            _evidence("tools/registry.py", "Structured tool registry with schemas per tool")
        ]
    elif control_id == "OMCP-DATA-002":
        status = "pass" if facts["redaction_support"] and facts["output_size_limits"] else "fail"
        rationale = (
            "Redaction helpers and output size limits are present."
            if status == "pass"
            else "Redaction helpers or output size limits are missing."
        )
        evidence = [
            _evidence("server/security.py", "Secret and key-name redaction helpers"),
            _evidence("server/config.py", "Inline/export size limits"),
        ]
    elif control_id == "OMCP-DATA-003":
        status = "pass" if facts["structured_json_invocation"] else "fail"
        rationale = (
            "Tool invocation surfaces enforce structured JSON payloads."
            if status == "pass"
            else "Tool invocation still allows non-object or non-JSON payload shapes."
        )
        evidence = [
            _evidence("server/mcp/tools.py", "HTTP tools/call expects a JSON object"),
            _evidence("server/mcp/http_transport.py", "JSON-RPC tools/call payload must be object"),
        ]
    elif control_id == "OMCP-AUTH-002":
        status = "fail" if facts["token_passthrough_detected"] else "pass"
        rationale = (
            "Bearer tokens are forwarded upstream by the map proxy."
            if status == "fail"
            else "No token passthrough surface was detected in the checked transport code."
        )
        evidence = [_evidence("server/maps_proxy.py", "Authorization bearer forwarding logic")]
    elif control_id == "OMCP-DEPLOY-003":
        workflow_text = facts["workflow_text"]
        has_required_gates = (
            _workflow_has_ruff_gate(workflow_text)
            and _workflow_contains(workflow_text, "pip-audit", "gitleaks")
        )
        status = "pass" if has_required_gates else "fail"
        rationale = (
            "CI includes static analysis, dependency auditing, and secret scanning gates."
            if status == "pass"
            else "CI is missing one or more required security gates: ruff, pip-audit, gitleaks."
        )
        evidence = [_evidence(".github/workflows/ci.yml", "CI workflow security gates")]
    elif control_id == "OMCP-GOV-001":
        status = "pass" if facts["audit_trail_support"] and facts["redaction_support"] else "fail"
        rationale = (
            "Audit packs include integrity and redaction support."
            if status == "pass"
            else "Audit or redaction support is incomplete."
        )
        evidence = [
            _evidence("server/audit/pack_builder.py", "Audit pack assembly and manifests"),
            _evidence("server/audit/redaction.py", "Disclosure/redaction derivatives"),
            _evidence("server/audit/integrity.py", "SHA-256 integrity verification"),
        ]
    elif control_id == "OMCP-CONT-001":
        workflow_text = facts["workflow_text"]
        status = (
            "pass"
            if facts["wrapper_exists"]
            and _workflow_contains(workflow_text, "validate_owasp_mcp_server.py", "upload-artifact")
            else "fail"
        )
        rationale = (
            "OWASP validator is wired into CI and artifacts are uploaded."
            if status == "pass"
            else "CI does not yet run the OWASP validator with artifact publication."
        )
        evidence = [
            _evidence(
                ".github/workflows/ci.yml", "Dedicated OWASP validation job and artifact upload"
            ),
            _evidence("scripts/validate-owasp-mcp-local", "Single local entrypoint wrapper"),
        ]
    elif control_id == "OMCP-CONT-002":
        status = (
            "pass" if _workflow_contains(facts["workflow_text"], "scorecard-action") else "fail"
        )
        rationale = (
            "Supply-chain posture checks include OpenSSF Scorecard or equivalent."
            if status == "pass"
            else "No OpenSSF Scorecard or equivalent supply-chain posture check was found in CI."
        )
        evidence = [_evidence(".github/workflows/ci.yml", "Supply-chain posture checks")]
    elif control_id == "OMCP-MIN-001":
        dependencies = control.get("depends_on_controls", [])
        failing = [
            item for item in dependencies if previous_results.get(item, {}).get("status") != "pass"
        ]
        status = "pass" if not failing else "fail"
        rationale = (
            "All minimum-bar controls passed."
            if status == "pass"
            else "Minimum-bar checklist failed due to: " + ", ".join(failing)
        )
        evidence = [
            _evidence("security/owasp_mcp/control_catalog.json", "Minimum-bar control dependencies")
        ]
    else:
        raise ValidationDataError(f"Unhandled control id '{control_id}'")

    if status not in VALID_STATUSES:
        raise ValidationDataError(f"Control {control_id} returned invalid status '{status}'")
    return {**control, "status": status, "rationale": rationale, "evidence": evidence}


def build_backlog(
    results: list[dict[str, Any]],
    *,
    safe_by_design_ids: set[str],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for result in results:
        if result["status"] != "fail":
            continue
        if result["requirement_level"] == "recommended":
            continue
        cross_links = [
            item_id
            for item_id in SAFE_BY_DESIGN_CROSS_LINKS.get(str(result["id"]), [])
            if item_id in safe_by_design_ids
        ]
        items.append(
            {
                "id": f"OWASP-MCP-REMED-{result['id']}",
                "control_id": result["id"],
                "title": result["title"],
                "section": result["section"],
                "severity": result["severity"],
                "status": "open",
                "rationale": result["rationale"],
                "evidence": result["evidence"],
                "acceptance_criteria": result["pass_criteria"],
                "remediation": result["remediation_template"],
                "cross_links": {"safe_by_design": cross_links},
            }
        )
    items.sort(
        key=lambda item: (
            -SEVERITY_RANK.get(str(item["severity"]), 0),
            str(item["control_id"]),
        )
    )
    return {"items": items}


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = dict.fromkeys(sorted(VALID_STATUSES), 0)
    applicable_total = 0
    earned_weight = 0
    total_weight = 0
    required_failures: list[str] = []
    for result in results:
        counts[result["status"]] += 1
        if result["status"] == "not_applicable":
            continue
        applicable_total += 1
        weight = REQUIREMENT_WEIGHTS[str(result["requirement_level"])]
        total_weight += weight
        if result["status"] == "pass":
            earned_weight += weight
        elif result["requirement_level"] in {"minimum_bar", "required"}:
            required_failures.append(str(result["id"]))
    verdict = "compliant" if not required_failures else "non_compliant"
    score = round((earned_weight / total_weight) * 100.0, 2) if total_weight else 100.0
    return {
        "verdict": verdict,
        "score": score,
        "counts": counts,
        "applicable_controls": applicable_total,
        "required_failures": required_failures,
    }


def render_markdown_report(report: dict[str, Any], backlog: dict[str, Any]) -> str:
    meta = report["meta"]
    summary = report["summary"]
    lines = [
        f"# OWASP MCP Server Validation ({meta['run_at'][:10]})",
        "",
        f"- Project: `{meta['project']}`",
        f"- Profile: `{meta['profile']}`",
        f"- Verdict: `{summary['verdict']}`",
        f"- Score: `{summary['score']}`",
        f"- Source baseline: `{meta['source']['title']}` `{meta['source']['version']}`",
        f"- Source URL: {meta['source']['url']}",
        f"- Source PDF SHA-256: `{meta['source']['pdf_sha256']}`",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status in ("pass", "fail", "not_applicable"):
        lines.append(f"| `{status}` | {summary['counts'][status]} |")
    lines.extend(
        [
            "",
            "## Required / Minimum-Bar Failures",
            "",
        ]
    )
    if not summary["required_failures"]:
        lines.append("- None")
    else:
        for control_id in summary["required_failures"]:
            result = next(item for item in report["controls"] if item["id"] == control_id)
            failure_line = (
                f"- `{control_id}` `{result['severity']}` "
                f"`{result['section']}`: {result['rationale']}"
            )
            lines.append(failure_line)
    lines.extend(["", "## Remediation Backlog", ""])
    if not backlog["items"]:
        lines.append("- No open remediation items.")
    else:
        for item in backlog["items"]:
            backlog_line = (
                f"- `{item['id']}` -> `{item['control_id']}` "
                f"`{item['severity']}`: {item['rationale']}"
            )
            lines.append(backlog_line)
    lines.extend(["", "## Control Results", ""])
    for result in report["controls"]:
        lines.append(f"### `{result['id']}` {result['title']} `{result['status']}`")
        lines.append("")
        lines.append(f"- Section: `{result['section']}`")
        lines.append(f"- Requirement: `{result['requirement_level']}`")
        lines.append(f"- Severity: `{result['severity']}`")
        lines.append(f"- Check type: `{result['check_type']}`")
        lines.append(f"- Rationale: {result['rationale']}")
        if result["evidence"]:
            lines.append("- Evidence:")
            for entry in result["evidence"]:
                lines.append(f"  - `{entry['path']}`: {entry['detail']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    report: dict[str, Any],
    backlog: dict[str, Any],
    *,
    output_dir: Path,
    output_format: str,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "owasp_mcp_server_validation.json"
    markdown_path = output_dir / "owasp_mcp_server_validation.md"
    backlog_path = output_dir / "owasp_mcp_server_backlog.json"
    write_json(json_path, report)
    write_json(backlog_path, backlog)
    if output_format in {"markdown", "both"}:
        # codeql[py/clear-text-storage-sensitive-data]
        markdown_path.write_text(render_markdown_report(report, backlog), encoding="utf-8")
    return {
        "json_report": str(json_path),
        "markdown_report": str(markdown_path),
        "backlog": str(backlog_path),
    }


def should_fail(report: dict[str, Any], fail_on: str) -> bool:
    if fail_on == "none":
        return False
    failures = [
        result
        for result in report["controls"]
        if result["status"] == "fail"
        and result["requirement_level"] in {"minimum_bar", "required", "recommended"}
    ]
    if fail_on == "required":
        return any(
            result["requirement_level"] in {"minimum_bar", "required"} for result in failures
        )
    if fail_on == "minimum_bar":
        return any(result["requirement_level"] == "minimum_bar" for result in failures)
    raise ValidationDataError(f"Unsupported fail_on mode '{fail_on}'")


def validate_repo(
    repo_root: str | Path,
    *,
    profile: str = "prod-strict",
    now: datetime | None = None,
    paths: ValidatorPaths | None = None,
    registered_tools: list[ToolSnapshot] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved_paths = paths or default_validator_paths(repo_root)
    evaluation_time = now or utc_now()
    control_catalog = load_control_catalog(resolved_paths.control_catalog)
    inventory = load_tool_risk_inventory(resolved_paths.tool_risk_inventory)
    tools = registered_tools or tool_snapshots_from_registry()
    manifest = build_tool_manifest(tools)
    manifest_lock = load_json(resolved_paths.tool_manifest_lock)
    manifest_matches_registry = manifest_lock == manifest
    manifest_ok, manifest_message = verify_signature(
        resolved_paths.tool_manifest_lock,
        resolved_paths.tool_manifest_signature,
        resolved_paths.tool_manifest_public_key,
    )
    facts = collect_repo_facts(resolved_paths, inventory, tools)
    controls = control_catalog["controls"]
    attestations_by_control, attestation_issues = load_attestations(
        resolved_paths.attestation_dir,
        resolved_paths.attestation_schema,
        profile=profile,
        now=evaluation_time,
        controls=controls,
    )
    results: list[dict[str, Any]] = []
    previous_results: dict[str, dict[str, Any]] = {}
    for control in controls:
        result = evaluate_control(
            control,
            profile=profile,
            facts=facts,
            attestations_by_control=attestations_by_control,
            manifest_ok=manifest_ok,
            manifest_message=manifest_message,
            manifest_matches_registry=manifest_matches_registry,
            previous_results=previous_results,
        )
        results.append(result)
        previous_results[str(result["id"])] = result
    summary = summarize_results(results)
    backlog = build_backlog(
        results,
        safe_by_design_ids=load_safe_by_design_ids(resolved_paths.safe_by_design_log),
    )
    report = {
        "meta": {
            "project": "mcp-geo",
            "profile": profile,
            "run_at": isoformat_utc(evaluation_time),
            "validator": "owasp_mcp_validation",
            "source": control_catalog["meta"]["source"],
            "artifacts": {
                "control_catalog": str(resolved_paths.control_catalog),
                "tool_risk_inventory": str(resolved_paths.tool_risk_inventory),
                "attestation_dir": str(resolved_paths.attestation_dir),
                "tool_manifest_lock": str(resolved_paths.tool_manifest_lock),
            },
            "attestation_issues": attestation_issues,
        },
        "summary": summary,
        "controls": results,
    }
    return report, backlog
