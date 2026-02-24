from fastapi import APIRouter
from models import MenuItem, BrowseResponse
from apple_music_service import apple_music_service

router = APIRouter(prefix="/browse/music", tags=["music"])

def get_root() -> MenuItem:
    return MenuItem(
        id="music_root",
        label="Music",
        childrenLink="/browse/music/root"
    )

@router.get("/root", response_model=BrowseResponse)
async def get_music_root():
    return BrowseResponse(
        title="Music",
        items=[
            MenuItem(id="am_recent", label="Recently Played", childrenLink="/browse/music/apple/recent"),
            MenuItem(id="am_playlists", label="Playlists", childrenLink="/browse/music/apple/playlists"),
            MenuItem(id="am_albums", label="Albums", childrenLink="/browse/music/apple/albums"),
            MenuItem(id="am_artists", label="Artists", childrenLink="/browse/music/apple/artists"),
            MenuItem(id="am_recommendations", label="Top Picks", childrenLink="/browse/music/apple/recommendations"),
        ]
    )

@router.get("/apple/recent", response_model=BrowseResponse)
async def get_apple_recent():
    items = await apple_music_service.get_recent_played()
    return BrowseResponse(title="Recently Played", items=items)

@router.get("/apple/playlists", response_model=BrowseResponse)
async def get_apple_playlists():
    items = await apple_music_service.get_library_playlists()
    return BrowseResponse(title="Apple Music Playlists", items=items)

@router.get("/apple/playlist/{playlist_id}", response_model=BrowseResponse)
async def get_apple_playlist_tracks(playlist_id: str):
    items = await apple_music_service.get_playlist_tracks(playlist_id)
    return BrowseResponse(title="Playlist Tracks", items=items, viewType="LIST")

@router.get("/apple/albums", response_model=BrowseResponse)
async def get_apple_albums():
    items = await apple_music_service.get_library_albums()
    return BrowseResponse(title="Apple Music Albums", items=items)

@router.get("/apple/album/{album_id}", response_model=BrowseResponse)
async def get_apple_album_tracks(album_id: str):
    items = await apple_music_service.get_album_tracks(album_id)
    return BrowseResponse(title="Album Tracks", items=items, viewType="LIST")

@router.get("/apple/artists", response_model=BrowseResponse)
async def get_apple_artists():
    items = await apple_music_service.get_library_artists()
    return BrowseResponse(title="Apple Music Artists", items=items)

@router.get("/apple/artist/{artist_id}", response_model=BrowseResponse)
async def get_apple_artist_albums(artist_id: str):
    items = await apple_music_service.get_artist_albums(artist_id)
    return BrowseResponse(title="Artist Albums", items=items)

@router.get("/apple/recommendations", response_model=BrowseResponse)
async def get_apple_recommendations():
    items = await apple_music_service.get_recommendations()
    return BrowseResponse(title="Top Picks", items=items)

@router.get("/apple/recommendation/{rec_id}", response_model=BrowseResponse)
async def get_apple_recommendation_contents(rec_id: str):
    items = await apple_music_service.get_recommendation_items(rec_id)
    return BrowseResponse(title="Recommendation", items=items)

@router.get("/artists", response_model=BrowseResponse)
async def get_artists():
    return BrowseResponse(
        title="Artists",
        items=[
            MenuItem(id="a1", label="Pink Floyd", childrenLink="/browse/music/artist/a1"),
            MenuItem(id="a2", label="Daft Punk", childrenLink="/browse/music/artist/a2")
        ]
    )
