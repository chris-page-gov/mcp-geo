#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "mcp-geo-server"
DEFAULT_REF = "origin/main"
WRAPPER_PLAN_TIMEOUT_SECONDS = 15
APP_WRAPPERS = {
    "claude": "scripts/claude-mcp-local",
    "codex": "scripts/codex-mcp-local",
    "gemini": "scripts/gemini-mcp-local",
}


@dataclass
class Check:
    level: str
    name: str
    detail: str
    remediation: str | None = None


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass
class ContainerScan:
    containers: list[dict[str, Any]]
    error: str | None = None


def _command_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _run(
    args: list[str],
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
) -> CommandResult:
    try:
        proc = subprocess.run(
            args,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _command_text(exc.stdout)
        stderr = _command_text(exc.stderr)
        timeout_text = f"{timeout:g}s" if timeout is not None else "the timeout"
        detail = stderr.strip() or stdout.strip() or f"timed out after {timeout_text}"
        if check:
            raise RuntimeError(f"{' '.join(args)} failed: {detail}") from exc
        return CommandResult(124, stdout, detail)
    except OSError as exc:
        if check:
            raise RuntimeError(f"{' '.join(args)} failed: {exc}") from exc
        return CommandResult(126, "", str(exc))
    if check and proc.returncode != 0:
        stderr = proc.stderr.strip()
        stdout = proc.stdout.strip()
        detail = stderr or stdout or f"exit code {proc.returncode}"
        raise RuntimeError(f"{' '.join(args)} failed: {detail}")
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def command_failure_detail(result: CommandResult, fallback: str) -> str:
    return result.stderr.strip() or result.stdout.strip() or fallback


def parse_timestamp(value: str) -> datetime:
    """Parse git epoch seconds or Docker RFC3339 timestamps."""

    text = str(value).strip()
    if not text:
        raise ValueError("empty timestamp")
    if text.isdigit():
        return datetime.fromtimestamp(int(text), tz=UTC)

    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    if "." in text:
        prefix, suffix = text.split(".", 1)
        frac = suffix
        tz = ""
        for marker in ("+", "-"):
            if marker in suffix:
                frac, tz_part = suffix.split(marker, 1)
                tz = f"{marker}{tz_part}"
                break
        text = f"{prefix}.{frac[:6]}{tz}"

    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def is_stale(created: datetime, reference: datetime) -> bool:
    return created < reference


def format_dt(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def is_executable_file(path: str) -> bool:
    candidate = Path(path)
    return candidate.is_file() and os.access(candidate, os.X_OK)


def configured_docker_error(env: dict[str, str]) -> str | None:
    configured = env.get("MCP_GEO_DOCKER_BIN", "").strip()
    if not configured:
        return None

    candidate = Path(configured)
    if candidate.exists():
        if candidate.is_dir():
            return f"MCP_GEO_DOCKER_BIN points to a directory, not an executable: {configured}."
        if not is_executable_file(configured):
            return f"MCP_GEO_DOCKER_BIN is not executable: {configured}."
        return None

    if os.sep not in configured and shutil.which(configured):
        return None
    return f"MCP_GEO_DOCKER_BIN points to a missing path: {configured}."


def find_docker(env: dict[str, str]) -> str | None:
    configured = env.get("MCP_GEO_DOCKER_BIN", "").strip()
    if configured:
        if Path(configured).exists() and is_executable_file(configured):
            return configured
        resolved = shutil.which(configured) if os.sep not in configured else None
        if resolved:
            return resolved
        return None
    for candidate in ("/opt/homebrew/bin/docker", "/usr/local/bin/docker", "/usr/bin/docker"):
        if is_executable_file(candidate):
            return candidate
    return shutil.which("docker")


def git_fetch_args_for_ref(ref: str) -> list[str]:
    if ref.startswith("origin/") and len(ref) > len("origin/"):
        branch = ref.removeprefix("origin/")
        return ["git", "fetch", "--quiet", "origin", f"{branch}:refs/remotes/origin/{branch}"]
    if ref.startswith("refs/remotes/origin/") and len(ref) > len("refs/remotes/origin/"):
        branch = ref.removeprefix("refs/remotes/origin/")
        return ["git", "fetch", "--quiet", "origin", f"{branch}:refs/remotes/origin/{branch}"]
    return ["git", "fetch", "--quiet", "origin", ref]


def git_commit_ref(ref: str) -> str:
    return f"{ref}^{{commit}}"


def git_ref_timestamp(ref: str) -> datetime:
    return parse_timestamp(
        _run(["git", "show", "-s", "--format=%ct", git_commit_ref(ref)]).stdout
    )


def git_ref_short(ref: str) -> str:
    return _run(["git", "rev-parse", "--short", git_commit_ref(ref)]).stdout.strip()


def git_ref_full(ref: str) -> str:
    return _run(["git", "rev-parse", git_commit_ref(ref)]).stdout.strip()


def image_info(docker_bin: str, image: str) -> tuple[str, datetime] | None:
    proc = _run(
        [docker_bin, "image", "inspect", image, "--format", "{{json .}}"],
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    payload = json.loads(proc.stdout)
    return str(payload["Id"]), parse_timestamp(str(payload["Created"]))


def image_ref_variants(image: str) -> set[str]:
    variants = {image}
    image_name = image.rsplit("/", 1)[-1]
    if "@" not in image and ":" not in image_name:
        variants.add(f"{image}:latest")
    return variants


def image_ref_matches(container_image: str, target_image: str) -> bool:
    return container_image in image_ref_variants(target_image)


def running_app_containers(docker_bin: str, image: str) -> ContainerScan:
    ps = _run([docker_bin, "ps", "--format", "{{json .}}"], check=False)
    if ps.returncode != 0:
        return ContainerScan(
            [],
            command_failure_detail(ps, "docker ps failed."),
        )
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for line in ps.stdout.splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"could not parse docker ps output: {exc}")
            continue
        if not image_ref_matches(str(item.get("Image", "")), image):
            continue
        container_id = str(item.get("ID", ""))
        inspect = _run(
            [docker_bin, "container", "inspect", container_id, "--format", "{{json .}}"],
            check=False,
        )
        if inspect.returncode != 0 or not inspect.stdout.strip():
            errors.append(
                f"could not inspect container {container_id}: "
                f"{command_failure_detail(inspect, 'docker container inspect failed.')}"
            )
            continue
        try:
            payload = json.loads(inspect.stdout)
        except json.JSONDecodeError as exc:
            errors.append(f"could not parse inspect output for container {container_id}: {exc}")
            continue
        rows.append(
            {
                "id": container_id,
                "name": str(item.get("Names") or payload.get("Name", "")).lstrip("/"),
                "status": str(item.get("Status", "")),
                "image_id": str(payload.get("Image", "")),
                "created": parse_timestamp(str(payload.get("Created", ""))),
            }
        )
    return ContainerScan(rows, "; ".join(errors) or None)


def wrapper_plan(wrapper: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["MCP_GEO_DOCKER_PLAN_ONLY"] = "1"
    env["MCP_GEO_DOCKER_BUILD"] = "never"
    env["MCP_GEO_POSTGIS_BUILD"] = "never"
    proc = _run(
        [str(wrapper)],
        check=False,
        env=env,
        timeout=WRAPPER_PLAN_TIMEOUT_SECONDS,
    )
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout).strip()}
    plan: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        plan[key] = value
    return plan


def add(
    checks: list[Check],
    level: str,
    name: str,
    detail: str,
    remediation: str | None = None,
) -> None:
    checks.append(Check(level, name, detail, remediation))


def build_image(docker_bin: str, image: str) -> None:
    subprocess.run([docker_bin, "build", "-t", image, str(REPO_ROOT)], cwd=REPO_ROOT, check=True)


def run_checks(args: argparse.Namespace) -> list[Check]:
    checks: list[Check] = []
    env = dict(os.environ)

    if args.fetch:
        fetch_args = git_fetch_args_for_ref(args.ref)
        fetch = _run(fetch_args, check=False)
        if fetch.returncode == 0:
            add(checks, "PASS", "git.fetch", f"Fetched {args.ref} from origin.")
        else:
            add(
                checks,
                "WARN",
                "git.fetch",
                (fetch.stderr or fetch.stdout).strip()
                or f"Could not fetch {args.ref} from origin.",
                "Check network/GitHub auth before relying on local remote state.",
            )

    status = _run(["git", "status", "--porcelain"]).stdout.strip()
    if status:
        add(
            checks,
            "WARN",
            "git.clean",
            "Working tree has local changes.",
            "Commit, stash, or discard local changes before a repeatable demo.",
        )
    else:
        add(checks, "PASS", "git.clean", "Working tree is clean.")

    try:
        head = git_ref_full("HEAD")
    except RuntimeError as exc:
        add(
            checks,
            "FAIL",
            "git.ref",
            f"Could not resolve HEAD: {exc}",
            "Check the local checkout before running the demo.",
        )
        return checks

    try:
        ref = git_ref_full(args.ref)
        ref_short = git_ref_short(args.ref)
        ref_time = git_ref_timestamp(args.ref)
    except (RuntimeError, ValueError) as exc:
        add(
            checks,
            "FAIL",
            "git.ref",
            f"Could not resolve target ref {args.ref!r}: {exc}",
            "Fetch the correct branch/tag or pass --ref to an existing local ref.",
        )
        return checks
    if head == ref:
        add(checks, "PASS", "git.ref", f"HEAD matches {args.ref} ({ref_short}).")
    else:
        add(
            checks,
            "FAIL",
            "git.ref",
            f"HEAD does not match {args.ref} ({ref_short}).",
            f"Run: git merge --ff-only {args.ref}",
        )

    if docker_error := configured_docker_error(env):
        add(
            checks,
            "FAIL",
            "docker.available",
            docker_error,
            "Fix MCP_GEO_DOCKER_BIN or unset it to use Docker from PATH.",
        )
        return checks

    docker_bin = find_docker(env)
    if not docker_bin:
        add(
            checks,
            "FAIL",
            "docker.available",
            "Docker executable was not found.",
            "Set MCP_GEO_DOCKER_BIN or install/start Docker Desktop.",
        )
        return checks
    if _run([docker_bin, "info"], check=False).returncode != 0:
        add(
            checks,
            "FAIL",
            "docker.running",
            "Docker is not running or is not reachable.",
            "Start Docker Desktop before the demo.",
        )
        return checks
    add(checks, "PASS", "docker.running", f"Docker is reachable via {docker_bin}.")

    if args.rebuild:
        add(checks, "INFO", "docker.image.rebuild", f"Rebuilding {args.image}.")
        build_image(docker_bin, args.image)

    current_image = image_info(docker_bin, args.image)
    if current_image is None:
        add(
            checks,
            "FAIL",
            "docker.image",
            f"Image {args.image!r} does not exist.",
            f"Run: docker build -t {args.image} {REPO_ROOT}",
        )
        image_id = None
    else:
        image_id, created = current_image
        if is_stale(created, ref_time):
            add(
                checks,
                "FAIL",
                "docker.image",
                (
                    f"Image {args.image!r} was created {format_dt(created)}, before "
                    f"{args.ref} ({ref_short}) at {format_dt(ref_time)}."
                ),
                f"Run: docker build -t {args.image} {REPO_ROOT}",
            )
        else:
            add(
                checks,
                "PASS",
                "docker.image",
                (
                    f"Image {args.image!r} was created {format_dt(created)}, after "
                    f"{args.ref} ({ref_short}) at {format_dt(ref_time)}."
                ),
            )

    container_scan = running_app_containers(docker_bin, args.image)
    if container_scan.error:
        add(
            checks,
            "FAIL",
            "docker.containers",
            f"Could not fully inspect running {args.image} app containers: {container_scan.error}",
            "Fix Docker permissions/API access before relying on container readiness.",
        )

    containers = container_scan.containers
    if not containers and not container_scan.error:
        add(checks, "PASS", "docker.containers", f"No running {args.image} app containers.")
    else:
        for container in containers:
            created = container["created"]
            stale_reasons: list[str] = []
            if image_id and container["image_id"] != image_id:
                stale_reasons.append("it uses an older image id")
            if is_stale(created, ref_time):
                stale_reasons.append(f"it was created {format_dt(created)} before {args.ref}")
            if stale_reasons:
                add(
                    checks,
                    "FAIL",
                    "docker.containers",
                    f"Running container {container['name']} is stale: {', '.join(stale_reasons)}.",
                    "Restart the AI client session or stop the stale container before the demo.",
                )
            else:
                add(
                    checks,
                    "PASS",
                    "docker.containers",
                    f"Running container {container['name']} uses the current image.",
                )

    for client, rel_path in APP_WRAPPERS.items():
        wrapper = REPO_ROOT / rel_path
        if not wrapper.exists():
            add(checks, "FAIL", f"wrapper.{client}", f"Missing wrapper: {rel_path}.")
            continue
        if not os.access(wrapper, os.X_OK):
            add(checks, "FAIL", f"wrapper.{client}", f"Wrapper is not executable: {rel_path}.")
            continue
        plan = wrapper_plan(wrapper)
        if "error" in plan:
            add(checks, "WARN", f"wrapper.{client}", f"Plan check failed: {plan['error']}")
            continue
        add(
            checks,
            "PASS",
            f"wrapper.{client}",
            (
                f"{rel_path} targets {plan.get('postgis_target_container', '<unknown>')} "
                f"with toolset {plan.get('default_toolset', '<unset>')}."
            ),
        )
        if (
            plan.get("os_api_key_present") != "true"
            and plan.get("os_api_key_file_present") != "true"
        ):
            add(
                checks,
                "WARN",
                f"wrapper.{client}.os_key",
                f"{client} wrapper plan does not see OS_API_KEY or OS_API_KEY_FILE.",
                (
                    "Export OS_API_KEY_FILE/OS_API_KEY for the launching GUI/session "
                    "if live OS calls are needed."
                ),
            )

    vscode_config = REPO_ROOT / ".vscode" / "mcp.json"
    if vscode_config.exists():
        add(checks, "PASS", "vscode.config", ".vscode/mcp.json is present.")
    else:
        add(checks, "WARN", "vscode.config", ".vscode/mcp.json is missing.")

    return checks


def render_checks(checks: list[Check]) -> str:
    lines = ["MCP-Geo prepare-for-demo checks"]
    for check in checks:
        lines.append(f"{check.level}: {check.name}: {check.detail}")
        if check.remediation:
            lines.append(f"  -> {check.remediation}")
    failures = sum(1 for check in checks if check.level == "FAIL")
    warnings = sum(1 for check in checks if check.level == "WARN")
    lines.append(f"Summary: {failures} fail, {warnings} warn.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check whether local MCP-Geo clients are ready to demo the latest build."
    )
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git ref that clients should match.")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Docker app image tag to inspect.")
    parser.add_argument(
        "--no-fetch",
        dest="fetch",
        action="store_false",
        help="Do not fetch the target ref before checking it.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild the Docker image before checking timestamps.",
    )
    parser.set_defaults(fetch=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks = run_checks(args)
    print(render_checks(checks))
    return 1 if any(check.level == "FAIL" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
