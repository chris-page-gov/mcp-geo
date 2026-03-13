from __future__ import annotations

from fastapi import Request, Response
from fastapi.responses import JSONResponse


def authorize_http_route(
    request: Request,
    *,
    quota_method: str | None = None,
) -> tuple[dict[str, str], JSONResponse | None]:
    from server.mcp import http_transport

    if http_transport._auth_mode() == "off":
        return {}, None

    session_id, session_state = http_transport._get_session(request)
    headers = {"mcp-session-id": session_id}
    try:
        claims = http_transport._authenticate_request(request, session_state)
        if quota_method:
            http_transport._enforce_session_quota(quota_method, session_state, claims)
    except http_transport.AuthenticationError:
        return headers, JSONResponse(
            status_code=401,
            content={
                "isError": True,
                "code": "AUTHENTICATION_FAILED",
                "message": "Authentication failed",
            },
            headers=headers,
        )
    except http_transport.AuthorizationError:
        return headers, JSONResponse(
            status_code=403,
            content={
                "isError": True,
                "code": "FORBIDDEN",
                "message": "Forbidden",
            },
            headers=headers,
        )
    except http_transport.SessionQuotaExceeded:
        return headers, JSONResponse(
            status_code=429,
            content={
                "isError": True,
                "code": "SESSION_QUOTA_EXCEEDED",
                "message": "Session quota exceeded",
            },
            headers=headers,
        )
    return headers, None


def apply_auth_headers(response: Response, headers: dict[str, str]) -> None:
    for key, value in headers.items():
        response.headers[key] = value
