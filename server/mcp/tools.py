
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter()

EPIC_B_TOOLS = [
    "os_places.search",
    "os_places.by_postcode",
    "os_places.by_uprn",
    "os_places.nearest",
    "os_places.within",
    "os_linked_ids.get",
    "os_features.query",
    "os_names.find",
    "os_names.nearest",
    "os_maps.render",
    "os_vector_tiles.descriptor"
]

@router.get("/tools/list")
def list_tools(limit: int = 10, page: int = 1):
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(EPIC_B_TOOLS) else None
    return {
        "tools": EPIC_B_TOOLS[start:end],
        "nextPageToken": next_page_token
    }

@router.post("/tools/call")
async def call_tool(request: Request):
    data = await request.json()
    tool = data.get("tool")
    if tool == "os_places.by_postcode":
        from server.config import settings
        import os, requests, re
        postcode = data.get("postcode", "").replace(" ", "").upper()
        if not re.match(r"^[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}$", postcode):
            return JSONResponse(
                status_code=400,
                content={
                    "isError": True,
                    "code": "INVALID_INPUT",
                    "message": "Invalid UK postcode"
                }
            )
        # Debug: Show where OS_API_KEY is being read from
        env_api_key = os.getenv("OS_API_KEY")
        settings_api_key = getattr(settings, "OS_API_KEY", None)
        api_key = env_api_key or settings_api_key or ""
        print(f"[DEBUG] OS_API_KEY from env: {bool(env_api_key)}, from settings: {bool(settings_api_key)}", flush=True)
        print(f"[DEBUG] OS_API_KEY value (redacted): {api_key[:3]}...{api_key[-3:] if len(api_key) > 6 else ''}", flush=True)
        if not api_key:
            return JSONResponse(
                status_code=501,
                content={
                    "isError": True,
                    "code": "NO_API_KEY",
                    "message": "OS_API_KEY not set"
                }
            )
        url = f"https://api.os.uk/search/places/v1/postcode?postcode={postcode}&key={api_key}"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 501:
                return JSONResponse(
                    status_code=501,
                    content={
                        "isError": True,
                        "code": "NOT_IMPLEMENTED",
                        "message": "OS Places API not implemented"
                    }
                )
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
            return JSONResponse(
                status_code=200,
                content={
                    "uprns": uprns,
                    "provenance": {"source": "os_places", "timestamp": data.get("epoch", "")}
                }
            )
        except Exception as exc:
            import traceback
            print("[DEBUG] Exception in os_places.by_postcode:", flush=True)
            print(traceback.format_exc(), flush=True)
            return JSONResponse(
                status_code=500,
                content={
                    "isError": True,
                    "code": "INTEGRATION_ERROR",
                    "message": str(exc)
                }
            )
    elif tool in EPIC_B_TOOLS:
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={
                "isError": True,
                "code": "NOT_IMPLEMENTED",
                "message": f"Tool '{tool}' is not implemented yet"
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={
                "isError": True,
                "code": "NOT_IMPLEMENTED",
                "message": f"Tool '{tool}' is not implemented yet"
            }
        )
