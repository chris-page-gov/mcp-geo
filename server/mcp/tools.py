from fastapi import APIRouter

router = APIRouter()


@router.get("/tools/list")
def list_tools(limit: int = 10, page: int = 1):
    # Pagination stub
    tools = ["placeholder_tool"]
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(tools) else None
    return {
        "tools": tools[start:end],
        "nextPageToken": next_page_token
    }



from fastapi import Request, status
from fastapi.responses import JSONResponse

@router.post("/tools/call")
async def call_tool(request: Request):
    data = await request.json()
    tool = data.get("tool")
    # Route tool calls
    if tool == "os_places.by_postcode":
        postcode = data.get("postcode", "").replace(" ", "").upper()
        import re
        if not re.match(r"^[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}$", postcode):
            return JSONResponse(
                status_code=400,
                content={
                    "isError": True,
                    "code": "INVALID_INPUT",
                    "message": "Invalid UK postcode"
                }
            )
        # Call OS Places API
        import os
        import requests
        from server.config import settings
        api_key = os.getenv("OS_API_KEY", getattr(settings, "OS_API_KEY", ""))
        if not api_key:
            return JSONResponse(
                status_code=500,
                content={
                    "isError": True,
                    "code": "NO_API_KEY",
                    "message": "OS_API_KEY not set"
                }
            )
        url = f"https://api.os.uk/search/places/v1/postcode?postcode={postcode}&key={api_key}"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                return JSONResponse(
                    status_code=resp.status_code,
                    content={
                        "isError": True,
                        "code": "OS_API_ERROR",
                        "message": f"OS API error: {resp.text}"
                    }
                )
            data = resp.json()
            uprns = []
            for result in data.get("results", []):
                dpa = result.get("DPA", {})
                uprns.append({
                    "uprn": dpa.get("UPRN"),
                    "address": dpa.get("ADDRESS"),
                    "lat": float(dpa.get("LAT", 0)),
                    "lon": float(dpa.get("LNG", 0)),
                    "classification": dpa.get("CLASS"),
                    "local_custodian_code": dpa.get("LOCAL_CUSTODIAN_CODE")
                })
            return {
                "uprns": uprns,
                "provenance": {"source": "os_places", "timestamp": data.get("epoch", "")}
            }
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={
                    "isError": True,
                    "code": "INTEGRATION_ERROR",
                    "message": str(exc)
                }
            )
    # Default stub
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "isError": True,
            "code": "NOT_IMPLEMENTED",
            "message": f"Tool '{tool}' is not implemented yet"
        }
    )
