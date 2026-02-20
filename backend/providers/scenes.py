from fastapi import APIRouter
from models import MenuItem, BrowseResponse

router = APIRouter(prefix="/browse/scenes", tags=["scenes"])

def get_root() -> MenuItem:
    return MenuItem(
        id="scenes_root",
        label="Scenes",
        childrenLink="/browse/scenes/all"
    )

@router.get("/all", response_model=BrowseResponse)
async def get_scenes():
    return BrowseResponse(
        title="Scenes",
        items=[
            MenuItem(id="s1", label="Relax", actionLink="/action/scene/relax"),
            MenuItem(id="s2", label="Party", actionLink="/action/scene/party"),
            MenuItem(id="s3", label="Movie", actionLink="/action/scene/movie")
        ]
    )
