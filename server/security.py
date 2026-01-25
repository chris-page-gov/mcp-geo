REDACTION_TOKEN = "[REDACTED]"


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


def mask_in_value(value: object, secrets: list[str]) -> object:
    if isinstance(value, str):
        return mask_in_text(value, secrets)
    if isinstance(value, list):
        return [mask_in_value(item, secrets) for item in value]
    if isinstance(value, dict):
        return {k: mask_in_value(v, secrets) for k, v in value.items()}
    return value
