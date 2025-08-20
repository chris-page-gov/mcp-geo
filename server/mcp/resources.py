from fastapi import APIRouter

router = APIRouter()

@router.get("/resources/list")
def list_resources(limit: int = 10, page: int = 1):
    resources = ["code_lists", "boundaries"]
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(resources) else None
    return {
        "resources": resources[start:end],
        "nextPageToken": next_page_token
    }
