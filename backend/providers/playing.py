from fastapi import APIRouter
from models import MenuItem, BrowseResponse

router = APIRouter(prefix="/browse/playing", tags=["playing"])

def get_root() -> MenuItem:
    return MenuItem(
        id="playing_root",
        label="Playing",
        childrenLink="/browse/playing/current"
    )

@router.get("/current", response_model=BrowseResponse)
async def get_current():
    return BrowseResponse(
        title="Now Playing",
        viewType="NOW_PLAYING",
        items=[]
    )
