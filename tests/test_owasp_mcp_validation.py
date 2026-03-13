from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from server import owasp_mcp_validation as validator
from server.owasp_mcp_validation import (
    ToolSnapshot,
    ValidationDataError,
    build_backlog,
    build_tool_manifest,
    evaluate_applicability,
    load_attestations,
    load_control_catalog,
    load_safe_by_design_ids,
    load_tool_risk_inventory,
    parse_datetime,
    pretty_json,
    render_markdown_report,
    sha256_file,
    should_fail,
    validate_attestation_document,
    validate_repo,
    verify_signature,
    write_json,
    write_outputs,
)

ATT_CONTROL_IDS = [
    "OMCP-ARCH-002",
    "OMCP-ARCH-005",
    "OMCP-TOOL-003",
    "OMCP-PI-001",
    "OMCP-PI-002",
    "OMCP-AUTH-001",
    "OMCP-AUTH-003",
    "OMCP-AUTH-004",
    "OMCP-DEPLOY-001",
    "OMCP-DEPLOY-002",
    "OMCP-GOV-002",
    "OMCP-GOV-003",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _tool(name: str) -> ToolSnapshot:
    return ToolSnapshot(
        name=name,
        version="1.0.0",
        description=f"Fixture tool {name}",
        input_schema={
            "type": "object",
            "properties": {"tool": {"type": "string", "const": name}},
            "required": ["tool"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
            "additionalProperties": False,
        },
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _copy_validator_artifacts(repo_root: Path) -> None:
    source_root = _repo_root() / "security/owasp_mcp"
    for relative in ["control_catalog.json", "attestations/schema.json"]:
        target = repo_root / "security/owasp_mcp" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")
    _write(
        repo_root / "safe-by-design.json",
        json.dumps({"revisions": [{"id": "SBD-REV-003"}, {"id": "SBD-REV-004"}]}, indent=2) + "\n",
    )


def _write_inventory(
    repo_root: Path,
    tools: list[ToolSnapshot],
    *,
    high_risk_tools: set[str] | None = None,
    restricted_tools: set[str] | None = None,
) -> None:
    high_risk_tools = high_risk_tools or set()
    restricted_tools = restricted_tools or set()
    entries = []
    for tool in tools:
        entries.append(
            {
                "name": tool.name,
                "side_effect_level": "none",
                "data_sensitivity": "restricted" if tool.name in restricted_tools else "public",
                "network_write": False,
                "high_risk_action": tool.name in high_risk_tools,
                "requires_user_context": False,
            }
        )
    payload = {
        "meta": {"project": "fixture", "generated_on": "2026-03-13"},
        "tools": entries,
    }
    _write(repo_root / "security/owasp_mcp/tool_risk_inventory.json", pretty_json(payload))


def _sign_manifest(repo_root: Path) -> None:
    tmpdir = repo_root / ".tmp-signing"
    tmpdir.mkdir(parents=True, exist_ok=True)
    private_key = tmpdir / "tool_manifest_private.pem"
    subprocess.run(
        [
            "openssl",
            "genpkey",
            "-algorithm",
            "RSA",
            "-out",
            str(private_key),
            "-pkeyopt",
            "rsa_keygen_bits:2048",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "openssl",
            "rsa",
            "-pubout",
            "-in",
            str(private_key),
            "-out",
            str(repo_root / "security/owasp_mcp/tool_manifest.pub.pem"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "openssl",
            "dgst",
            "-sha256",
            "-sign",
            str(private_key),
            "-out",
            str(repo_root / "security/owasp_mcp/tool_manifest.lock.json.sig"),
            str(repo_root / "security/owasp_mcp/tool_manifest.lock.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _write_manifest(repo_root: Path, tools: list[ToolSnapshot]) -> None:
    manifest = build_tool_manifest(tools)
    _write(repo_root / "security/owasp_mcp/tool_manifest.lock.json", pretty_json(manifest))
    _sign_manifest(repo_root)


def _write_attestations(
    repo_root: Path,
    *,
    omit: set[str] | None = None,
    stale: set[str] | None = None,
) -> None:
    omit = omit or set()
    stale = stale or set()
    attestation_dir = repo_root / "security/owasp_mcp/attestations"
    attestation_dir.mkdir(parents=True, exist_ok=True)
    for control_id in ATT_CONTROL_IDS:
        if control_id in omit:
            continue
        verified_at = "2024-01-01T00:00:00Z" if control_id in stale else "2026-03-13T00:00:00Z"
        payload = {
            "attestation_id": f"att-{control_id.lower()}",
            "title": f"Evidence for {control_id}",
            "control_ids": [control_id],
            "environment": "prod-strict",
            "verifier": "fixture-suite",
            "verified_at": verified_at,
            "evidence_uri": f"file://fixtures/{control_id}.md",
            "artifact_hashes": {"fixture": "abc123"},
            "notes": "fixture attestation",
        }
        _write(attestation_dir / f"{control_id.lower()}.json", pretty_json(payload))


def _write_repo_files(
    repo_root: Path,
    *,
    token_passthrough: bool,
    include_ci_gates: bool,
    include_validator_job: bool,
    include_scorecard: bool,
) -> None:
    _write(
        repo_root / "server/mcp/http_transport.py",
        '@router.post("/mcp")\n'
        "_SESSION_STATE = {}\n"
        "_SESSION_TTL_SECONDS = 60\n"
        "def _cleanup_sessions(now):\n    return None\n"
        'msg.get("jsonrpc") != JSONRPC\n'
        "if not isinstance(params, dict):\n    pass\n"
        'content=_resp_error(msg_id, -32602, "Invalid params")\n'
        "Payload must be object\n",
    )
    _write(
        repo_root / "server/mcp/tools.py",
        '"/tools/describe"\n'
        'tool_name = data.get("tool")\n'
        "Request body must be a JSON object\n"
        '"tools": sanitized[start:end]\n',
    )
    _write(
        repo_root / "server/config.py",
        'OS_API_KEY = ""\nNOMIS_UID = ""\nNOMIS_SIGNATURE = ""\n'
        "OS_EXPORT_INLINE_MAX_BYTES = 200000\nOS_FEATURES_MAX_LIMIT = 100\n",
    )
    _write(
        repo_root / "server/security.py",
        "def configured_secrets(config):\n    return []\n"
        "def mask_in_text(text, secrets):\n    return text\n"
        "def mask_in_value(value, secrets, key_name=None):\n    return value\n",
    )
    maps_proxy = "def _resolve_upstream_auth(request):\n    return {}, {}, []\n"
    if token_passthrough:
        maps_proxy = (
            "def _resolve_upstream_auth(request):\n"
            '    bearer_value = "Bearer fixture"\n'
            '    return {"Authorization": bearer_value}, {}, [bearer_value]\n'
        )
    _write(repo_root / "server/maps_proxy.py", maps_proxy)
    _write(
        repo_root / "server/audit/pack_builder.py", "redaction-manifest.json\nevent-ledger.jsonl\n"
    )
    _write(repo_root / "server/audit/redaction.py", "redaction-manifest.json\nsha256\n")
    _write(repo_root / "server/audit/integrity.py", "sha256\n")
    _write(repo_root / "Dockerfile", "FROM python:3.11-slim\nUSER appuser\n")
    _write(repo_root / "scripts/validate-owasp-mcp-local", "#!/usr/bin/env bash\n")
    workflow_lines = ["name: CI"]
    if include_ci_gates:
        workflow_lines.extend(["ruff check", "pip-audit", "gitleaks"])
    if include_validator_job:
        workflow_lines.extend(["validate_owasp_mcp_server.py", "upload-artifact"])
    if include_scorecard:
        workflow_lines.append("scorecard-action")
    _write(repo_root / ".github/workflows/ci.yml", "\n".join(workflow_lines) + "\n")


def _make_fixture_repo(
    tmp_path: Path,
    *,
    token_passthrough: bool = False,
    high_risk_tools: set[str] | None = None,
    restricted_tools: set[str] | None = None,
    omit_attestations: set[str] | None = None,
    stale_attestations: set[str] | None = None,
    include_ci_gates: bool = True,
    include_validator_job: bool = True,
    include_scorecard: bool = True,
) -> tuple[Path, list[ToolSnapshot]]:
    repo_root = tmp_path / "repo"
    tools = [_tool("os_places.search"), _tool("os_maps.render")]
    _copy_validator_artifacts(repo_root)
    _write_inventory(
        repo_root,
        tools,
        high_risk_tools=high_risk_tools,
        restricted_tools=restricted_tools,
    )
    _write_manifest(repo_root, tools)
    _write_attestations(repo_root, omit=omit_attestations, stale=stale_attestations)
    _write_repo_files(
        repo_root,
        token_passthrough=token_passthrough,
        include_ci_gates=include_ci_gates,
        include_validator_job=include_validator_job,
        include_scorecard=include_scorecard,
    )
    return repo_root, tools


def _control_status(report: dict[str, object], control_id: str) -> str:
    controls = report["controls"]
    assert isinstance(controls, list)
    for item in controls:
        if isinstance(item, dict) and item.get("id") == control_id:
            status = item.get("status")
            assert isinstance(status, str)
            return status
    raise AssertionError(f"missing control {control_id}")


def test_seeded_pass_fixture_is_compliant(tmp_path: Path):
    repo_root, tools = _make_fixture_repo(tmp_path)
    report, backlog = validate_repo(repo_root, registered_tools=tools)
    assert report["summary"]["verdict"] == "compliant"
    assert _control_status(report, "OMCP-PI-001") == "not_applicable"
    assert backlog["items"] == []


def test_missing_attestation_fails_in_strict_mode(tmp_path: Path):
    repo_root, tools = _make_fixture_repo(tmp_path, omit_attestations={"OMCP-AUTH-001"})
    report, _ = validate_repo(repo_root, registered_tools=tools)
    assert report["summary"]["verdict"] == "non_compliant"
    assert _control_status(report, "OMCP-AUTH-001") == "fail"


def test_stale_attestation_fails(tmp_path: Path):
    repo_root, tools = _make_fixture_repo(tmp_path, stale_attestations={"OMCP-DEPLOY-001"})
    report, _ = validate_repo(repo_root, registered_tools=tools)
    assert _control_status(report, "OMCP-DEPLOY-001") == "fail"


def test_high_risk_tool_without_human_approval_fails(tmp_path: Path):
    repo_root, tools = _make_fixture_repo(
        tmp_path,
        high_risk_tools={"os_places.search"},
        omit_attestations={"OMCP-PI-001"},
    )
    report, _ = validate_repo(repo_root, registered_tools=tools)
    assert _control_status(report, "OMCP-PI-001") == "fail"


def test_signed_manifest_mismatch_fails(tmp_path: Path):
    repo_root, tools = _make_fixture_repo(tmp_path)
    manifest_path = repo_root / "security/owasp_mcp/tool_manifest.lock.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["tools"][0]["description"] = "tampered"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report, _ = validate_repo(repo_root, registered_tools=tools)
    assert _control_status(report, "OMCP-TOOL-002") == "fail"


def test_backlog_generation_is_stable(tmp_path: Path):
    repo_root, tools = _make_fixture_repo(tmp_path, token_passthrough=True)
    report_one, backlog_one = validate_repo(repo_root, registered_tools=tools)
    report_two, backlog_two = validate_repo(repo_root, registered_tools=tools)
    assert report_one["summary"] == report_two["summary"]
    assert backlog_one == backlog_two
    assert any(item["control_id"] == "OMCP-AUTH-002" for item in backlog_one["items"])


def test_current_repo_snapshot_fails_with_explicit_backlog():
    report, backlog = validate_repo(_repo_root())
    assert report["summary"]["verdict"] == "non_compliant"
    failing_ids = {item["control_id"] for item in backlog["items"]}
    assert "OMCP-AUTH-002" in failing_ids
    assert "OMCP-AUTH-001" in report["summary"]["required_failures"]


def test_helper_functions_and_safe_by_design_loading(tmp_path: Path):
    sample = tmp_path / "sample.json"
    write_json(sample, {"value": 1})
    assert sample.read_text(encoding="utf-8").endswith("\n")
    assert len(sha256_file(sample)) == 64
    assert parse_datetime("2026-03-13T10:00:00Z").tzinfo == UTC
    assert parse_datetime("2026-03-13T10:00:00").tzinfo == UTC
    assert load_safe_by_design_ids(tmp_path / "missing.json") == set()
    safe = tmp_path / "safe-by-design.json"
    safe.write_text(json.dumps({"revisions": [{"id": "SBD-REV-123"}]}) + "\n", encoding="utf-8")
    assert load_safe_by_design_ids(safe) == {"SBD-REV-123"}
    assert validator._read_text(tmp_path / "absent.txt") == ""
    assert validator._evidence("path.txt", "detail") == {"path": "path.txt", "detail": "detail"}


def test_verify_signature_and_catalog_validators_cover_error_paths(tmp_path: Path):
    missing_ok, missing_message = verify_signature(
        tmp_path / "manifest.json",
        tmp_path / "manifest.sig",
        tmp_path / "manifest.pub.pem",
    )
    assert not missing_ok
    assert "Missing manifest verification artifact" in missing_message

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}\n", encoding="utf-8")
    public_key = tmp_path / "manifest.pub.pem"
    public_key.write_text("not-a-key\n", encoding="utf-8")
    signature = tmp_path / "manifest.sig"
    signature.write_bytes(b"bogus")
    invalid_ok, invalid_message = verify_signature(manifest_path, signature, public_key)
    assert not invalid_ok
    assert invalid_message

    bad_catalog = tmp_path / "bad_catalog.json"
    bad_catalog.write_text(json.dumps([]), encoding="utf-8")
    try:
        load_control_catalog(bad_catalog)
    except ValidationDataError as exc:
        assert "control catalog must be a JSON object" in str(exc)
    else:
        raise AssertionError("expected invalid catalog to raise")

    dup_catalog = tmp_path / "dup_catalog.json"
    dup_catalog.write_text(
        json.dumps(
            {
                "controls": [
                    {
                        "id": "DUP-1",
                        "title": "A",
                        "section": "s",
                        "source_quote": "q",
                        "requirement_level": "required",
                        "applies_when": {},
                        "check_type": "static_repo",
                        "severity": "low",
                        "pass_criteria": "p",
                        "remediation_template": "r",
                    },
                    {
                        "id": "DUP-1",
                        "title": "B",
                        "section": "s",
                        "source_quote": "q",
                        "requirement_level": "required",
                        "applies_when": {},
                        "check_type": "static_repo",
                        "severity": "low",
                        "pass_criteria": "p",
                        "remediation_template": "r",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    try:
        load_control_catalog(dup_catalog)
    except ValidationDataError as exc:
        assert "duplicate control id" in str(exc)
    else:
        raise AssertionError("expected duplicate control ids to raise")

    bad_inventory = tmp_path / "bad_inventory.json"
    bad_inventory.write_text(json.dumps({"tools": [{"name": "x"}]}), encoding="utf-8")
    try:
        load_tool_risk_inventory(bad_inventory)
    except ValidationDataError as exc:
        assert "missing required field" in str(exc)
    else:
        raise AssertionError("expected invalid inventory to raise")

    dup_inventory = tmp_path / "dup_inventory.json"
    dup_inventory.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "name": "dup",
                        "side_effect_level": "none",
                        "data_sensitivity": "public",
                        "network_write": False,
                        "high_risk_action": False,
                        "requires_user_context": False,
                    },
                    {
                        "name": "dup",
                        "side_effect_level": "none",
                        "data_sensitivity": "public",
                        "network_write": False,
                        "high_risk_action": False,
                        "requires_user_context": False,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    try:
        load_tool_risk_inventory(dup_inventory)
    except ValidationDataError as exc:
        assert "duplicate tool risk entry" in str(exc)
    else:
        raise AssertionError("expected duplicate inventory entries to raise")


def test_attestation_validation_loading_and_applicability_helpers(tmp_path: Path):
    schema = {
        "required": [
            "attestation_id",
            "title",
            "control_ids",
            "environment",
            "verifier",
            "verified_at",
            "evidence_uri",
            "artifact_hashes",
        ],
        "properties": {
            "attestation_id": {"type": "string"},
            "title": {"type": "string"},
            "control_ids": {"type": "array"},
            "environment": {"type": "string"},
            "verifier": {"type": "string"},
            "verified_at": {"type": "string"},
            "expires_at": {"type": "string"},
            "evidence_uri": {"type": "string"},
            "artifact_hashes": {"type": "object"},
        },
    }
    errors = validate_attestation_document(
        {
            "attestation_id": 1,
            "title": "bad",
            "control_ids": ["", 2],
            "environment": "prod-strict",
            "verifier": "tester",
            "verified_at": "not-a-date",
            "evidence_uri": "file://evidence",
            "artifact_hashes": {"fixture": 1},
        },
        schema,
        path=tmp_path / "bad.json",
    )
    assert errors

    bad_required_schema = {"required": "not-a-list", "properties": {}}
    try:
        validate_attestation_document({}, bad_required_schema, path=tmp_path / "bad_required.json")
    except ValidationDataError as exc:
        assert "required' list" in str(exc)
    else:
        raise AssertionError("expected bad required schema to raise")

    bad_properties_schema: dict[str, Any] = {"required": [], "properties": []}
    try:
        validate_attestation_document({}, bad_properties_schema, path=tmp_path / "bad_props.json")
    except ValidationDataError as exc:
        assert "properties' object" in str(exc)
    else:
        raise AssertionError("expected bad properties schema to raise")

    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema) + "\n", encoding="utf-8")
    attestation_dir = tmp_path / "attestations"
    attestation_dir.mkdir()
    (attestation_dir / "bad.json").write_text("{}\n", encoding="utf-8")
    (attestation_dir / "ignore.json").write_text(
        json.dumps(
            {
                "attestation_id": "ignore",
                "title": "Ignore other env",
                "control_ids": ["OMCP-AUTH-001"],
                "environment": "staging",
                "verifier": "tester",
                "verified_at": "2026-03-13T00:00:00Z",
                "evidence_uri": "file://ignore",
                "artifact_hashes": {"fixture": "abc"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (attestation_dir / "expired.json").write_text(
        json.dumps(
            {
                "attestation_id": "expired",
                "title": "Expired",
                "control_ids": ["OMCP-AUTH-001"],
                "environment": "prod-strict",
                "verifier": "tester",
                "verified_at": "2026-03-13T00:00:00Z",
                "expires_at": "2026-03-01T00:00:00Z",
                "evidence_uri": "file://expired",
                "artifact_hashes": {"fixture": "abc"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    controls: list[dict[str, Any]] = [{"id": "OMCP-AUTH-001", "attestation_max_age_days": 90}]
    loaded, issues = load_attestations(
        attestation_dir,
        schema_path,
        profile="prod-strict",
        now=datetime(2026, 3, 13, tzinfo=UTC),
        controls=controls,
    )
    assert "OMCP-AUTH-001" in loaded
    assert loaded["OMCP-AUTH-001"][0]["_stale"] is True
    assert issues

    try:
        evaluate_applicability({"id": "bad", "applies_when": []}, {}, "prod-strict")
    except ValidationDataError as exc:
        assert "applies_when must be an object" in str(exc)
    else:
        raise AssertionError("expected invalid applies_when to raise")

    assert not evaluate_applicability(
        {"id": "x", "applies_when": {"profiles": ["other"]}},
        {
            "remote_mcp": True,
            "session_support": True,
            "high_risk_tools": [],
            "restricted_tools": [],
            "uses_secret_settings": True,
        },
        "prod-strict",
    )


def test_backlog_markdown_outputs_and_should_fail(tmp_path: Path):
    results: list[dict[str, Any]] = [
        {
            "id": "OMCP-DATA-002",
            "title": "Redaction and size limits",
            "section": "data validation and resource management",
            "severity": "medium",
            "status": "fail",
            "requirement_level": "required",
            "check_type": "static_repo",
            "rationale": "Missing redaction evidence.",
            "evidence": [{"path": "server/security.py", "detail": "Missing"}],
            "pass_criteria": "Have redaction.",
            "remediation_template": "Add redaction.",
        },
        {
            "id": "OMCP-REC-001",
            "title": "Recommended item",
            "section": "governance",
            "severity": "low",
            "status": "fail",
            "requirement_level": "recommended",
            "check_type": "static_repo",
            "rationale": "Optional improvement.",
            "evidence": [],
            "pass_criteria": "Optional pass.",
            "remediation_template": "Optional remediation.",
        },
    ]
    backlog = build_backlog(results, safe_by_design_ids={"SBD-REV-003", "SBD-REV-004"})
    assert len(backlog["items"]) == 1
    assert backlog["items"][0]["cross_links"]["safe_by_design"] == ["SBD-REV-003", "SBD-REV-004"]

    report: dict[str, Any] = {
        "meta": {
            "project": "fixture",
            "profile": "prod-strict",
            "run_at": "2026-03-13T00:00:00Z",
            "source": {
                "title": "OWASP guide",
                "version": "1.0",
                "url": "https://example.test",
                "pdf_sha256": "abc",
            },
        },
        "summary": {
            "verdict": "non_compliant",
            "score": 42.0,
            "counts": {"pass": 0, "fail": 1, "not_applicable": 0},
            "required_failures": ["OMCP-DATA-002"],
        },
        "controls": results,
    }
    markdown = render_markdown_report(report, backlog)
    assert "OWASP MCP Server Validation" in markdown
    assert "OMCP-DATA-002" in markdown

    outputs = write_outputs(report, backlog, output_dir=tmp_path / "out", output_format="json")
    assert Path(outputs["json_report"]).exists()
    assert Path(outputs["backlog"]).exists()
    assert not Path(outputs["markdown_report"]).exists()

    assert not should_fail(report, "none")
    assert should_fail(report, "required")
    minbar_report = {
        **report,
        "controls": [
            {
                **results[0],
                "status": "fail",
                "requirement_level": "minimum_bar",
            }
        ],
    }
    assert should_fail(minbar_report, "minimum_bar")
    try:
        should_fail(report, "bogus")
    except ValidationDataError as exc:
        assert "Unsupported fail_on mode" in str(exc)
    else:
        raise AssertionError("expected invalid fail_on to raise")


def test_validate_repo_raises_for_unhandled_control(tmp_path: Path):
    repo_root, tools = _make_fixture_repo(tmp_path)
    bad_catalog = {
        "meta": {
            "source": {
                "title": "Fixture",
                "version": "1.0",
                "url": "https://example.test",
                "pdf_sha256": "abc",
            }
        },
        "controls": [
            {
                "id": "UNKNOWN-CONTROL",
                "title": "Unknown",
                "section": "minimum-bar checklist",
                "source_quote": "fixture",
                "requirement_level": "required",
                "applies_when": {},
                "check_type": "static_repo",
                "severity": "low",
                "pass_criteria": "pass",
                "remediation_template": "remediate",
            }
        ],
    }
    catalog_path = repo_root / "security/owasp_mcp/control_catalog.json"
    catalog_path.write_text(json.dumps(bad_catalog, indent=2) + "\n", encoding="utf-8")
    try:
        validate_repo(repo_root, registered_tools=tools)
    except ValidationDataError as exc:
        assert "Unhandled control id" in str(exc)
    else:
        raise AssertionError("expected unhandled control to raise")
