from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ons_geo"


def _write_manifest(tmp_path: Path, *, bad_schema: bool = False) -> Path:
    payload = {
        "version": "2026-04-08",
        "products": [
            {
                "id": "ONSPD",
                "title": "ONSPD",
                "keyType": "postcode",
                "derivationMode": "exact",
                "priority": 10,
                "release": "2026-02",
                "resolver": {"type": "static_file", "path": str(FIXTURES / "onspd_modern.csv")},
                "semanticFields": {
                    "required": ["postcode", "lad_code" if not bad_schema else "oa_name"],
                    "optional": ["ward_code"],
                    "aliases": {"postcode": ["pcds"]},
                },
            }
        ],
        "supportProducts": [
            {
                "id": "RGC",
                "title": "RGC",
                "priority": 20,
                "release": "2025-12",
                "resolver": {
                    "type": "static_file",
                    "path": str(FIXTURES / "rgc_current_sample.csv"),
                },
                "semanticFields": {
                    "required": ["code", "name"],
                    "optional": ["status"],
                    "aliases": {
                        "code": ["GEOGRAPHY_CODE"],
                        "name": ["GEOGRAPHY_NAME"],
                        "status": ["STATUS"],
                    },
                    "defaults": {"status": "current"},
                },
            }
        ],
    }
    manifest = tmp_path / "ons_geo_sources.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return manifest


def test_ons_geo_live_validate_ok_with_static_sources(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    result = subprocess.run(
        [sys.executable, "scripts/ons_geo_live_validate.py", "--sources", str(manifest)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert all(item["status"] == "ok" for item in payload["datasets"])


def test_ons_geo_live_validate_flags_schema_drift(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, bad_schema=True)
    result = subprocess.run(
        [sys.executable, "scripts/ons_geo_live_validate.py", "--sources", str(manifest)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
        check=False,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    onspd = next(item for item in payload["datasets"] if item["id"] == "ONSPD")
    assert onspd["status"] == "schema_drift"


def test_ons_geo_live_validate_warns_for_portal_release_sources(tmp_path: Path) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/landing":
                body = (
                    b"<html><body>"
                    b'<a href="/downloads/onsud.zip">ONSUD latest zip</a>'
                    b"</body></html>"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path == "/downloads/onsud.zip":
                body = b"PK\x03\x04"
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        landing_url = f"http://127.0.0.1:{server.server_port}/landing"
        payload = {
            "version": "2026-04-08",
            "products": [
                {
                    "id": "ONSUD",
                    "title": "ONSUD",
                    "keyType": "uprn",
                    "derivationMode": "exact",
                    "priority": 10,
                    "release": "latest",
                    "resolver": {
                        "type": "portal_release_file",
                        "landingUrl": landing_url,
                        "preferredSuffixes": [".zip"],
                        "linkPatterns": ["onsud", "zip"],
                    },
                    "semanticFields": {
                        "required": ["uprn", "lad_code"],
                        "optional": ["postcode"],
                        "aliases": {"uprn": ["UPRN"]},
                    },
                }
            ],
            "supportProducts": [],
        }
        manifest = tmp_path / "ons_geo_sources.json"
        manifest.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "scripts/ons_geo_live_validate.py", "--sources", str(manifest)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.returncode == 0, result.stderr
    parsed = json.loads(result.stdout)
    assert parsed["status"] == "warning"
    onsud = next(item for item in parsed["datasets"] if item["id"] == "ONSUD")
    assert onsud["status"] == "warning"
    assert onsud["schemaProbeStatus"] == "unavailable_remote_archive"
    assert onsud["warning"]


def test_ons_geo_live_validate_flags_lagging_uprn_epoch(tmp_path: Path) -> None:
    payload = {
        "version": "2026-04-08",
        "products": [
            {
                "id": "ONSUD",
                "title": "ONSUD",
                "keyType": "uprn",
                "derivationMode": "exact",
                "priority": 10,
                "release": "December 2025 (Epoch 123)",
                "resolver": {"type": "static_file", "path": str(FIXTURES / "onsud_sample.csv")},
                "semanticFields": {
                    "required": ["uprn", "lad_code"],
                    "optional": ["postcode"],
                    "aliases": {"uprn": ["UPRN"]},
                },
            }
        ],
        "supportProducts": [],
    }
    manifest = tmp_path / "ons_geo_sources.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/ons_geo_live_validate.py", "--sources", str(manifest)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    parsed = json.loads(result.stdout)
    assert parsed["status"] == "warning"
    onsud = next(item for item in parsed["datasets"] if item["id"] == "ONSUD")
    assert onsud["status"] == "warning"
    assert onsud["freshness"]["status"] == "lagging"
    assert onsud["freshness"]["lagEpochs"] >= 1
