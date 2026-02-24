from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from socketio import AsyncServer, ASGIApp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os

from models import MenuItem, BrowseResponse
from providers import tmdb, playing, music, scenes, system

# Configure logging
logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="BeoSound5 Engine")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server
sio = AsyncServer(cors_allowed_origins="*")
asgi_app = ASGIApp(sio, app)

# Include Provider Routers
app.include_router(tmdb.router)
app.include_router(playing.router)
app.include_router(music.router)
app.include_router(scenes.router)
app.include_router(system.router)

from atv_service import atv_service
from motn_service import motn_service
from link_mapper_service import link_mapper_service
from sonos_service import sonos_service

@app.on_event("startup")
async def startup_event():
    _LOGGER.info("Application starting up...")
    atv_service.initialize()
    sonos_service.initialize()

@app.get("/")
async def read_root():
    return {
        "message": "BeoSound5 Engine Running (FastAPI)",
        "atv_status": atv_service.status,
        "sonos_status": sonos_service.status,
        "motn_cache_size": len(motn_service.cache)
    }

@app.get("/atv/status")
async def get_atv_status():
    return {"status": atv_service.status}

@app.get("/sonos/status")
async def get_sonos_status():
    return {"status": sonos_service.status}

@app.post("/atv/rescan")
async def rescan_atv():
    atv_service.initialize()
    return {"status": "rescan_triggered"}

@app.post("/sonos/rescan")
async def rescan_sonos():
    sonos_service.initialize()
    return {"status": "rescan_triggered"}

@app.get("/roots", response_model=List[MenuItem])
async def get_roots():
    """Aggregates root items from all providers."""
    return [
        playing.get_root(),
        music.get_root(),
        tmdb.get_tv_root(),
        tmdb.get_movie_root(),
        scenes.get_root(),
        system.get_root()
    ]

# --- ACTIONS ---

@app.post("/action/music/play/{am_id:path}")
async def action_music_play(am_id: str):
    _LOGGER.info(f"Action: Play Apple Music {am_id} on Sonos")
    success = await sonos_service.play_apple_music(am_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to play on Sonos")
    return {"status": "playing", "id": am_id}

@app.post("/action/atv/play/{media_type}/{item_id}")
async def action_atv_play(media_type: str, item_id: int):
    _LOGGER.info(f"Action: Play {media_type} {item_id} on Apple TV")
    
    # Resolve the best possible link (Direct link or Title-based search)
    url = await tmdb.resolve_deep_link(media_type, item_id)
    
    if not url:
        _LOGGER.error("Could not resolve any link for this item.")
        raise HTTPException(status_code=404, detail="Could not resolve a link for this item.")
    
    # NEW: Map the resolved URL to a specific provider deep link if applicable
    mapped_url = await link_mapper_service.map_to_deep_link(url)
    
    _LOGGER.info(f"DEBUG: Pushing URL to Apple TV Service: {mapped_url}")
    
    success = await atv_service.launch_app(mapped_url)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to trigger playback on Apple TV (Status: {atv_service.status})")
    return {"status": "success"}

@app.post("/action/atv/play_url")
async def action_atv_play_url(url: str):
    _LOGGER.info(f"Action: Play URL {url} on Apple TV")
    
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided.")
    
    # Map to deep link if possible
    mapped_url = await link_mapper_service.map_to_deep_link(url)
    
    success = await atv_service.launch_app(mapped_url)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to trigger playback on Apple TV")
    return {"status": "success"}

@sio.event
async def connect(sid, environ):
    _LOGGER.info(f'Client connected: {sid}')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(asgi_app, host='0.0.0.0', port=5001)
