from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ProbePoint:
    rpm: int
    duration_sec: int
    requests: int
    success: int
    limited: int
    errors: int
    mean_ms: float
    p95_ms: float

    @property
    def limited_ratio(self) -> float:
        if self.requests <= 0:
            return 0.0
        return self.limited / self.requests


def parse_prometheus_metrics(text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        name, value = parts
        # Strip labels, e.g. app_request_latency_ms_bucket{le="50"}.
        metric_name = name.split("{", 1)[0]
        try:
            parsed = float(value)
        except ValueError:
            continue
        values[metric_name] = parsed
    return values


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * (p / 100.0)
    lower = int(math.floor(idx))
    upper = int(math.ceil(idx))
    if lower == upper:
        return ordered[lower]
    weight = idx - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _build_request(
    url: str,
    method: str,
    headers: dict[str, str],
    body: dict[str, Any] | None,
) -> urllib.request.Request:
    method_upper = method.upper()
    payload: bytes | None = None
    req_headers = dict(headers)
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    return urllib.request.Request(url=url, data=payload, headers=req_headers, method=method_upper)


def probe_step(
    *,
    base_url: str,
    path: str,
    method: str,
    headers: dict[str, str],
    body: dict[str, Any] | None,
    rpm: int,
    duration_sec: int,
    timeout_sec: float,
) -> ProbePoint:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    total_requests = max(1, int(round(rpm * duration_sec / 60.0)))
    interval = 60.0 / rpm if rpm > 0 else 0.0
    latencies_ms: list[float] = []
    success = 0
    limited = 0
    errors = 0
    start = time.monotonic()

    for idx in range(total_requests):
        scheduled = start + idx * interval
        now = time.monotonic()
        if scheduled > now:
            time.sleep(scheduled - now)
        req = _build_request(url, method, headers, body)
        t0 = time.monotonic()
        status = 0
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                status = int(resp.status)
                _ = resp.read()
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            _ = exc.read()
        except Exception:
            errors += 1
        elapsed_ms = (time.monotonic() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)
        if status == 429:
            limited += 1
        elif 200 <= status < 400:
            success += 1
        elif status != 0:
            errors += 1

    mean_ms = (sum(latencies_ms) / len(latencies_ms)) if latencies_ms else 0.0
    p95_ms = percentile(latencies_ms, 95.0)
    return ProbePoint(
        rpm=rpm,
        duration_sec=duration_sec,
        requests=total_requests,
        success=success,
        limited=limited,
        errors=errors,
        mean_ms=round(mean_ms, 2),
        p95_ms=round(p95_ms, 2),
    )


def recommend_limit(
    points: list[ProbePoint],
    *,
    target_429_ratio: float,
    headroom_percent: float,
    target_p95_ms: float | None,
) -> dict[str, Any]:
    if not points:
        return {
            "recommended_rate_limit_per_min": None,
            "reason": "no_probe_points",
            "max_stable_rpm": None,
            "first_limited_rpm": None,
        }

    sorted_points = sorted(points, key=lambda item: item.rpm)

    def _stable(point: ProbePoint) -> bool:
        if point.limited_ratio > target_429_ratio:
            return False
        if target_p95_ms is not None and point.p95_ms > target_p95_ms:
            return False
        return True

    stable = [point for point in sorted_points if _stable(point)]
    first_limited = next(
        (
            point
            for point in sorted_points
            if point.limited_ratio > target_429_ratio
            or (target_p95_ms is not None and point.p95_ms > target_p95_ms)
        ),
        None,
    )

    if not stable:
        floor = max(1, int(round(sorted_points[0].rpm * 0.8)))
        return {
            "recommended_rate_limit_per_min": floor,
            "reason": "all_points_unstable",
            "max_stable_rpm": None,
            "first_limited_rpm": first_limited.rpm if first_limited else None,
        }

    max_stable = stable[-1]
    proposed = int(round(max_stable.rpm * (1.0 + headroom_percent / 100.0)))
    proposed = max(1, proposed)

    if (
        first_limited is not None
        and target_p95_ms is not None
        and first_limited.p95_ms > target_p95_ms
        and first_limited.limited_ratio <= target_429_ratio
    ):
        proposed = max_stable.rpm
        reason = "latency_guardrail"
    elif first_limited is not None and proposed >= first_limited.rpm:
        proposed = max_stable.rpm
        reason = "limited_at_next_probe_step"
    elif first_limited is None:
        reason = "no_limiter_hit_in_probe_range"
    else:
        reason = "stable_with_headroom"

    return {
        "recommended_rate_limit_per_min": proposed,
        "reason": reason,
        "max_stable_rpm": max_stable.rpm,
        "first_limited_rpm": first_limited.rpm if first_limited else None,
    }


def _fetch_metrics(base_url: str, timeout_sec: float) -> dict[str, float] | None:
    url = f"{base_url.rstrip('/')}/metrics"
    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            if int(resp.status) != 200:
                return None
            text = resp.read().decode("utf-8", errors="replace")
            return parse_prometheus_metrics(text)
    except Exception:
        return None


def _headers_from_args(raw_headers: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in raw_headers:
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        k = key.strip()
        v = value.strip()
        if k:
            parsed[k] = v
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Probe an mcp-geo server and suggest RATE_LIMIT_PER_MIN based on observed "
            "429 ratio and latency."
        )
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--path", default="/tools/list")
    parser.add_argument("--method", default="GET")
    parser.add_argument("--json-body", default=None, help="Optional JSON body for POST/PUT/PATCH.")
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="Optional request header in 'Key: Value' format. Can be repeated.",
    )
    parser.add_argument("--start-rpm", type=int, default=60)
    parser.add_argument("--step-rpm", type=int, default=30)
    parser.add_argument("--max-rpm", type=int, default=300)
    parser.add_argument("--duration-sec", type=int, default=20)
    parser.add_argument("--timeout-sec", type=float, default=5.0)
    parser.add_argument("--target-429-ratio", type=float, default=0.01)
    parser.add_argument(
        "--target-p95-ms",
        type=float,
        default=None,
        help="Optional p95 latency cap. If set, probe points above this are unstable.",
    )
    parser.add_argument("--headroom-percent", type=float, default=15.0)
    parser.add_argument("--output", default=None, help="Optional JSON output file path.")
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.start_rpm <= 0 or args.step_rpm <= 0 or args.max_rpm < args.start_rpm:
        parser.error("Expected: start-rpm > 0, step-rpm > 0, and max-rpm >= start-rpm.")
    if args.duration_sec <= 0:
        parser.error("Expected: duration-sec > 0.")
    if args.target_429_ratio < 0 or args.target_429_ratio > 1:
        parser.error("Expected: target-429-ratio between 0 and 1.")

    headers = _headers_from_args(args.header)
    body = None
    if args.json_body:
        body = json.loads(args.json_body)

    before_metrics = _fetch_metrics(args.base_url, args.timeout_sec)

    points: list[ProbePoint] = []
    for rpm in range(args.start_rpm, args.max_rpm + 1, args.step_rpm):
        point = probe_step(
            base_url=args.base_url,
            path=args.path,
            method=args.method,
            headers=headers,
            body=body,
            rpm=rpm,
            duration_sec=args.duration_sec,
            timeout_sec=args.timeout_sec,
        )
        points.append(point)
        print(
            f"[probe] rpm={point.rpm} requests={point.requests} "
            f"429={point.limited} errors={point.errors} p95_ms={point.p95_ms}"
        )

    recommendation = recommend_limit(
        points,
        target_429_ratio=args.target_429_ratio,
        headroom_percent=args.headroom_percent,
        target_p95_ms=args.target_p95_ms,
    )

    after_metrics = _fetch_metrics(args.base_url, args.timeout_sec)
    metrics_delta: dict[str, float] | None = None
    if before_metrics is not None and after_metrics is not None:
        metrics_delta = {}
        for key in ("app_requests_total", "app_rate_limited_total"):
            if key in before_metrics and key in after_metrics:
                metrics_delta[key] = after_metrics[key] - before_metrics[key]

    result = {
        "baseUrl": args.base_url,
        "path": args.path,
        "method": args.method.upper(),
        "target429Ratio": args.target_429_ratio,
        "targetP95Ms": args.target_p95_ms,
        "headroomPercent": args.headroom_percent,
        "probe": [asdict(point) | {"limited_ratio": round(point.limited_ratio, 4)} for point in points],
        "recommendation": recommendation,
        "metricsDelta": metrics_delta,
        "timestamp": int(time.time()),
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"[saved] {out_path}")

    print(
        f"[recommendation] RATE_LIMIT_PER_MIN={recommendation['recommended_rate_limit_per_min']} "
        f"reason={recommendation['reason']}"
    )
    return 0


def main() -> None:
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
