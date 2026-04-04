REDACTION_TOKEN = "[REDACTED]"
SENSITIVE_KEY_MARKERS = (
    "signature",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "secret",
    "password",
)


def redact(value: str | None) -> str:
    if not value:
        return ""
    v = str(value)
    if len(v) <= 6:
        return REDACTION_TOKEN
    return f"{v[:3]}...{v[-3:]}"


def mask_in_text(text: str, secrets: list[str]) -> str:
    masked = text
    for s in secrets:
        if s:
            masked = masked.replace(s, REDACTION_TOKEN)
    return masked


def _is_sensitive_key_name(key: object) -> bool:
    if not isinstance(key, str):
        return False
    normalized = key.strip().lower().replace("-", "_")
    return any(marker in normalized for marker in SENSITIVE_KEY_MARKERS)


def configured_secrets(config: object) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for key in (
        "OS_API_KEY",
        "NOMIS_UID",
        "NOMIS_SIGNATURE",
        "MCP_HTTP_AUTH_TOKEN",
        "MCP_HTTP_JWT_HS256_SECRET",
    ):
        raw = getattr(config, key, "")
        candidate = str(raw).strip() if raw is not None else ""
        if candidate and candidate not in seen:
            values.append(candidate)
            seen.add(candidate)
    return values


def mask_in_value(value: object, secrets: list[str], key_name: str | None = None) -> object:
    if _is_sensitive_key_name(key_name):
        return REDACTION_TOKEN
    if isinstance(value, str):
        return mask_in_text(value, secrets)
    if isinstance(value, list):
        return [mask_in_value(item, secrets) for item in value]
    if isinstance(value, dict):
        return {
            k: mask_in_value(v, secrets, key_name=k if isinstance(k, str) else None)
            for k, v in value.items()
        }
    return value
