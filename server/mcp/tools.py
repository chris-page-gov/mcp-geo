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
    epic_b_tools = [
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
    if tool == "os_places.by_postcode":
        # Existing implementation (can be filled in later)
        pass  # Will be implemented
    if tool in epic_b_tools:
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={
                "isError": True,
                "code": "NOT_IMPLEMENTED",
                "message": f"Tool '{tool}' is not implemented yet"
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
