from __future__ import annotations

import plistlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_OBSIDIAN_APP = Path("/Applications/Obsidian.app")
DEFAULT_OBSIDIAN_USER_DATA = Path.home() / "Library" / "Application Support" / "obsidian"
MINIMUM_OBSIDIAN_VERSION = (1, 12, 7)
UPDATED_ASAR_PATTERN = re.compile(r"^obsidian-(\d+(?:\.\d+)*)\.asar$")


def minimum_version_string() -> str:
    return ".".join(str(part) for part in MINIMUM_OBSIDIAN_VERSION)


def parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for part in version.split("."):
        if not part.isdigit():
            break
        parts.append(int(part))
    return tuple(parts)


def version_at_least(version: str, minimum: tuple[int, ...] = MINIMUM_OBSIDIAN_VERSION) -> bool:
    parsed = parse_version(version)
    if not parsed:
        return False
    padded = parsed + (0,) * max(0, len(minimum) - len(parsed))
    return padded >= minimum


def version_is_more_recent(candidate: str, baseline: str) -> bool:
    return parse_version(candidate) > parse_version(baseline)


def read_installer_version(app_path: Path = DEFAULT_OBSIDIAN_APP) -> str | None:
    info_path = app_path / "Contents" / "Info.plist"
    if not info_path.exists():
        return None
    with info_path.open("rb") as handle:
        data = plistlib.load(handle)
    raw = data.get("CFBundleShortVersionString")
    return str(raw) if raw else None


def latest_updated_asar_version(user_data_path: Path = DEFAULT_OBSIDIAN_USER_DATA) -> str | None:
    if not user_data_path.exists():
        return None
    latest: str | None = None
    for path in user_data_path.glob("obsidian-*.asar"):
        match = UPDATED_ASAR_PATTERN.match(path.name)
        if not match:
            continue
        version = match.group(1)
        if latest is None or version_is_more_recent(version, latest):
            latest = version
    return latest


def read_app_version_details(
    app_path: Path = DEFAULT_OBSIDIAN_APP,
    user_data_path: Path = DEFAULT_OBSIDIAN_USER_DATA,
) -> dict[str, str | None]:
    installer_version = read_installer_version(app_path)
    updated_asar_version = latest_updated_asar_version(user_data_path)
    effective_version = installer_version
    version_source = "installer"
    if installer_version and updated_asar_version and version_is_more_recent(
        updated_asar_version,
        installer_version,
    ):
        effective_version = updated_asar_version
        version_source = "updated_asar"
    return {
        "app_version": effective_version,
        "installer_version": installer_version,
        "updated_asar_version": updated_asar_version,
        "version_source": version_source if effective_version else None,
    }


def expected_cli_path(app_path: Path = DEFAULT_OBSIDIAN_APP) -> Path:
    return app_path / "Contents" / "MacOS" / "obsidian-cli"


def registered_cli_path() -> Path | None:
    resolved = shutil.which("obsidian")
    return Path(resolved) if resolved else None


def run_cli(args: list[str], vault_path: Path, cli_path: Path | None = None) -> str:
    binary = cli_path or registered_cli_path()
    if binary is None:
        raise FileNotFoundError("Obsidian CLI is not registered on PATH.")
    completed = subprocess.run(
        [str(binary), *args],
        cwd=vault_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def help_text(vault_path: Path, cli_path: Path | None = None) -> str:
    return run_cli(["help"], vault_path, cli_path)


def read_note(vault_path: Path, note_path: str, cli_path: Path | None = None) -> str:
    return run_cli(["read", f"path={note_path}"], vault_path, cli_path)


def search_notes(vault_path: Path, query: str, cli_path: Path | None = None) -> str:
    return run_cli(["search", f"query={query}"], vault_path, cli_path)


def preflight(
    vault_path: Path,
    *,
    app_path: Path = DEFAULT_OBSIDIAN_APP,
    user_data_path: Path = DEFAULT_OBSIDIAN_USER_DATA,
    cli_path: Path | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    resolved_cli = cli_path or registered_cli_path()
    version_details = read_app_version_details(app_path, user_data_path)
    version = version_details["app_version"]
    bundled_cli = expected_cli_path(app_path)
    result: dict[str, Any] = {
        "vault_path": str(vault_path),
        "app_path": str(app_path),
        "user_data_path": str(user_data_path),
        "minimum_version": minimum_version_string(),
        "registered_cli_path": str(resolved_cli) if resolved_cli else None,
        "bundled_cli_path": str(bundled_cli),
        "issues": issues,
        **version_details,
    }
    if not vault_path.exists():
        issues.append(
            {
                "code": "VAULT_NOT_FOUND",
                "message": f"Vault path does not exist: {vault_path}",
            }
        )
        result["ready"] = False
        return result
    if version is None:
        issues.append(
            {
                "code": "OBSIDIAN_APP_NOT_FOUND",
                "message": f"Obsidian app bundle not found at {app_path}",
            }
        )
        result["ready"] = False
        return result
    if not version_at_least(version):
        version_label = version
        installer_version = version_details["installer_version"]
        if installer_version and installer_version != version:
            version_label = f"{version} (installer {installer_version})"
        issues.append(
            {
                "code": "OBSIDIAN_VERSION_TOO_OLD",
                "message": (
                    f"Installed Obsidian runtime {version_label} is below the required "
                    f"{minimum_version_string()} for the official CLI."
                ),
            }
        )
        result["ready"] = False
        return result
    result["bundled_cli_present"] = bundled_cli.exists()
    if resolved_cli is None and not bundled_cli.exists():
        issues.append(
            {
                "code": "OBSIDIAN_CLI_BUNDLE_MISSING",
                "message": (
                    "The expected bundled CLI binary is missing at "
                    f"{bundled_cli}. Enable the CLI in Obsidian 1.12.7+ and "
                    "let it register the binary."
                ),
            }
        )
    if resolved_cli is None:
        issues.append(
            {
                "code": "OBSIDIAN_CLI_NOT_REGISTERED",
                "message": (
                    "Obsidian CLI is not registered on PATH. Enable "
                    "`Settings -> General -> Command line interface` in "
                    "Obsidian and restart the terminal."
                ),
            }
        )
        result["ready"] = False
        return result
    try:
        help_output = help_text(vault_path, resolved_cli)
        result["help_ok"] = bool(help_output)
        read_output = read_note(vault_path, "00 Home/00 - Agent Home.md", resolved_cli)
        result["read_ok"] = "# Agent Home" in read_output
        search_output = search_notes(vault_path, "Agent Home", resolved_cli)
        result["search_ok"] = bool(search_output)
    except FileNotFoundError as exc:
        issues.append({"code": "OBSIDIAN_CLI_NOT_REGISTERED", "message": str(exc)})
    except subprocess.CalledProcessError as exc:
        command = " ".join(str(part) for part in exc.cmd)
        stderr = exc.stderr.strip() if exc.stderr else "no stderr output"
        issues.append(
            {
                "code": "OBSIDIAN_CLI_COMMAND_FAILED",
                "message": f"Command `{command}` failed: {stderr}",
            }
        )
    if not result.get("read_ok"):
        issues.append(
            {
                "code": "OBSIDIAN_CLI_READ_FAILED",
                "message": "Obsidian CLI could not read `00 Home/00 - Agent Home.md`.",
            }
        )
    if not result.get("search_ok"):
        issues.append(
            {
                "code": "OBSIDIAN_CLI_SEARCH_FAILED",
                "message": "Obsidian CLI could not search the control vault.",
            }
        )
    result["ready"] = not issues
    return result
