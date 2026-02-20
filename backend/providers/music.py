from fastapi import APIRouter
from models import MenuItem, BrowseResponse

router = APIRouter(prefix="/browse/music", tags=["music"])

def get_root() -> MenuItem:
    return MenuItem(
        id="music_root",
        label="Music",
        childrenLink="/browse/music/artists"
    )

@router.get("/artists", response_model=BrowseResponse)
async def get_artists():
    return BrowseResponse(
        title="Artists",
        items=[
            MenuItem(id="a1", label="Pink Floyd", childrenLink="/browse/music/artist/a1"),
            MenuItem(id="a2", label="Daft Punk", childrenLink="/browse/music/artist/a2")
        ]
    )
