from fastapi import APIRouter
from models import MenuItem, BrowseResponse

router = APIRouter(prefix="/browse/system", tags=["system"])

def get_root() -> MenuItem:
    return MenuItem(
        id="system_root",
        label="System",
        childrenLink="/browse/system/info"
    )

@router.get("/info", response_model=BrowseResponse)
async def get_info():
    return BrowseResponse(
        title="System Info",
        items=[
            MenuItem(id="version", label="Version 1.0.0"),
            MenuItem(id="uptime", label="Uptime: 2 days")
        ]
    )
