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
