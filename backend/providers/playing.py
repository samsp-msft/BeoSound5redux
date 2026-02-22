from fastapi import APIRouter
import logging
import os
import json
from typing import Optional
from models import MenuItem, BrowseResponse, ImageSet
from atv_service import atv_service
from tmdb_service import tmdb_service

_LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/browse/playing", tags=["playing"])

# Load TMDB config for API key
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
        TMDB_API_KEY = config.get('tmdb_api_key', '').strip()
except Exception:
    TMDB_API_KEY = ""

def get_root() -> MenuItem:
    return MenuItem(
        id="playing_root",
        label="Playing",
        childrenLink="/browse/playing/current"
    )

@router.get("/current", response_model=BrowseResponse)
async def get_current():
    playing = await atv_service.get_now_playing()
    
    if not playing or not playing.title:
        app_name = getattr(playing, 'app', "Apple TV") if playing else "Apple TV"
        
        # If nothing is actually playing (title is None), we show the app name
        return BrowseResponse(
            title="Now Playing",
            viewType="NOW_PLAYING",
            items=[
                MenuItem(
                    id="idle_status",
                    label=app_name,
                    subText="Connect to an app to start playback",
                    template="NOW_PLAYING_ITEM"
                )
            ]
        )

    # We have something!
    title = playing.title
    sub_text = playing.artist or playing.series_name or ""
    
    # Try to construct a good subtext for TV Shows: "S1 E2 | Series Name"
    if playing.series_name:
        season = f"S{playing.season_number}" if hasattr(playing, 'season_number') and playing.season_number else ""
        episode = f"E{playing.episode_number}" if hasattr(playing, 'episode_number') and playing.episode_number else ""
        parts = [p for p in [season, episode] if p]
        ep_info = " ".join(parts)
        if ep_info:
            sub_text = f"{ep_info} | {playing.series_name}"
        else:
            sub_text = playing.series_name

    # 1. Use Live Artwork from ATV if available
    images = None
    live_artwork = getattr(playing, 'artwork_url', None)
    if live_artwork:
        images = ImageSet(
            landscape_small=live_artwork,
            landscape_large=live_artwork,
            portrait_small=live_artwork,
            portrait_large=live_artwork
        )
    
    # 2. Try TMDB for richer metadata/artwork if ATV artwork is missing or we want better metadata
    description = None
    if TMDB_API_KEY:
        # If it's a TV show, search for series name, if movie, search for title
        search_query = playing.series_name or playing.title
        media_type = "tv" if playing.series_name else "movie"
        
        # Search TMDB
        try:
            results_data = await tmdb_service.search(search_query, media_type, TMDB_API_KEY)
            if results_data and results_data.get("results"):
                # Filter results to find best title match
                best_match = None
                for res in results_data["results"]:
                    res_title = res.get("name") or res.get("title")
                    if res_title and res_title.lower() == search_query.lower():
                        best_match = res
                        break
                
                if not best_match:
                    best_match = results_data["results"][0]
                
                # Fetch full details
                tmdb_id = best_match['id']
                media_type = best_match.get('media_type', media_type)
                
                url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}"
                params = {"api_key": TMDB_API_KEY, "append_to_response": "external_ids"}
                details = await tmdb_service.get(url, params=params)
                
                if details:
                    description = details.get("overview")
                    
                    # Update images
                    backdrop_path = details.get("backdrop_path")
                    poster_path = details.get("poster_path")
                    
                    if backdrop_path or poster_path:
                        tmdb_images = ImageSet(
                            portrait_small=f"https://image.tmdb.org/t/p/w185{poster_path}" if poster_path else None,
                            portrait_large=f"https://image.tmdb.org/t/p/w780{poster_path}" if poster_path else None,
                            landscape_small=f"https://image.tmdb.org/t/p/w300{backdrop_path}" if backdrop_path else None,
                            landscape_large=f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
                        )
                        
                        if not images:
                            images = tmdb_images
                        else:
                            # Merge: prefer TMDB for posters if available
                            if tmdb_images.portrait_large:
                                images.portrait_large = tmdb_images.portrait_large
                                images.portrait_small = tmdb_images.portrait_small
                            if not images.landscape_large and tmdb_images.landscape_large:
                                images.landscape_large = tmdb_images.landscape_large
                                images.landscape_small = tmdb_images.landscape_small
                    
                    # Get IMDB ID and MOTN enrichment
                    imdb_id = details.get("external_ids", {}).get("imdb_id")
                    if imdb_id:
                        motn_data = await motn_service.get_show_data(imdb_id)
                        if motn_data and media_type == "tv":
                            s_num = getattr(playing, 'season_number', None)
                            e_num = getattr(playing, 'episode_number', None)
                            
                            if s_num is None or e_num is None:
                                import re
                                text_to_scan = f"{playing.title} {playing.artist}"
                                match = re.search(r'[sS](\d+)[eE](\d+)', text_to_scan)
                                if match:
                                    s_num = int(match.group(1))
                                    e_num = int(match.group(2))

                            if s_num is not None and e_num is not None:
                                for season in motn_data.get("seasons", []):
                                    if season.get("seasonNumber") == s_num:
                                        for episode in season.get("episodes", []):
                                            if episode.get("episodeNumber") == e_num:
                                                title = episode.get("title") or title
                                                description = episode.get("overview") or description
                                                sub_text = f"S{s_num} E{e_num} | {playing.series_name}"
                                                break
                
                if not sub_text and media_type == "movie":
                    year = best_match.get("release_date", "")[:4]
                    if year:
                        sub_text = year
        except Exception as e:
            _LOGGER.error(f"Failed to fetch TMDB/MOTN data for Now Playing: {e}")

    # Final touch: Add app name as subtext if we have nothing else
    app_name = getattr(playing, 'app', None)
    if not sub_text and app_name:
        sub_text = app_name

    return BrowseResponse(
        title="Now Playing",
        viewType="NOW_PLAYING",
        currentApp=app_name,
        items=[
            MenuItem(
                id="current_media",
                label=title,
                subText=sub_text,
                description=description,
                images=images,
                template="NOW_PLAYING_ITEM",
                duration=playing.total_time,
                position=playing.position
            )
        ]
    )
