from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


INTEGRITY_SCHEMA_VERSION = "1.0.0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_bundle_hash_record(
    bundle_path: Path,
    *,
    pack_id: str,
    disclosure_profile: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "generatedAt": _utc_now(),
        "packId": pack_id,
        "disclosureProfile": disclosure_profile,
        "algorithm": "sha256",
        "fileName": bundle_path.name,
        "sizeBytes": bundle_path.stat().st_size,
        "sha256": sha256_file(bundle_path),
    }


def bundle_hash_sidecar_path(bundle_path: Path) -> Path:
    return bundle_path.with_suffix(bundle_path.suffix + ".sha256.json")


def write_bundle_hash_sidecar(
    bundle_path: Path,
    *,
    pack_id: str,
    disclosure_profile: str,
) -> Path:
    payload = build_bundle_hash_record(
        bundle_path,
        pack_id=pack_id,
        disclosure_profile=disclosure_profile,
    )
    target = bundle_hash_sidecar_path(bundle_path)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def load_bundle_hash_sidecar(bundle_path: Path) -> dict[str, Any]:
    return json.loads(bundle_hash_sidecar_path(bundle_path).read_text(encoding="utf-8"))


def build_integrity_manifest(
    pack_dir: Path,
    artifact_paths: list[Path],
    *,
    pack_id: str,
    disclosure_profile: str,
) -> dict[str, Any]:
    artifacts = []
    for path in sorted(artifact_paths, key=lambda item: item.relative_to(pack_dir).as_posix()):
        if not path.exists():
            continue
        artifacts.append(
            {
                "path": path.relative_to(pack_dir).as_posix(),
                "sizeBytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "verificationStatus": "recorded",
            }
        )
    return {
        "schemaVersion": INTEGRITY_SCHEMA_VERSION,
        "generatedAt": _utc_now(),
        "packId": pack_id,
        "algorithm": "sha256",
        "disclosureProfile": disclosure_profile,
        "verificationStatus": "recorded",
        "artifacts": artifacts,
    }


def write_integrity_manifest(
    pack_dir: Path,
    artifact_paths: list[Path],
    *,
    pack_id: str,
    disclosure_profile: str,
) -> Path:
    manifest = build_integrity_manifest(
        pack_dir,
        artifact_paths,
        pack_id=pack_id,
        disclosure_profile=disclosure_profile,
    )
    target = pack_dir / "integrity-manifest.json"
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target


def load_integrity_manifest(pack_dir: Path) -> dict[str, Any]:
    path = pack_dir / "integrity-manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def verify_pack_integrity(pack_dir: Path) -> dict[str, Any]:
    manifest = load_integrity_manifest(pack_dir)
    mismatches = []
    missing = []
    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        rel_path = artifact.get("path")
        if not isinstance(rel_path, str):
            continue
        path = pack_dir / rel_path
        if not path.exists():
            missing.append(rel_path)
            continue
        actual_size = path.stat().st_size
        actual_hash = sha256_file(path)
        if actual_size != artifact.get("sizeBytes") or actual_hash != artifact.get("sha256"):
            mismatches.append(
                {
                    "path": rel_path,
                    "expectedSizeBytes": artifact.get("sizeBytes"),
                    "actualSizeBytes": actual_size,
                    "expectedSha256": artifact.get("sha256"),
                    "actualSha256": actual_hash,
                }
            )
    return {
        "verified": not mismatches and not missing,
        "checkedAt": _utc_now(),
        "checkedCount": len(manifest.get("artifacts", [])),
        "verificationStatus": "verified" if not mismatches and not missing else "failed",
        "mismatches": mismatches,
        "missing": missing,
    }


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    parser = argparse.ArgumentParser(description="DSAP integrity utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_parser = subparsers.add_parser("verify", help="Verify a DSAP pack against its manifest.")
    verify_parser.add_argument("pack_dir", help="Pack directory to verify.")
    args = parser.parse_args()

    if args.command == "verify":
        result = verify_pack_integrity(Path(args.pack_dir))
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
