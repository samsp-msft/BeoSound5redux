from fastapi import APIRouter, HTTPException, Query
import httpx
import logging
from typing import List, Optional
from models import MenuItem, BrowseResponse
import os
import json
from datetime import datetime, timedelta
import asyncio
from motn_service import motn_service

_LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/browse/tv", tags=["tv"])

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

TMDB_API_KEY = config.get('tmdb_api_key', '').strip()
WATCH_REGION = config.get('watch_region', 'US')
SUBSCRIPTIONS = config.get('subscriptions', [])
PROVIDER_IDS = "|".join([str(s['id']) for s in SUBSCRIPTIONS])

TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w200"

# --- ROOT GENERATORS ---

def get_tv_root() -> MenuItem:
    return MenuItem(id="tv_root_node", label="TV Shows", childrenLink="/browse/tv/tv_root")

def get_movie_root() -> MenuItem:
    return MenuItem(id="movie_root_node", label="Movies", childrenLink="/browse/tv/movie_root")

# --- CATEGORY HIERARCHY ---

@router.get("/tv_root", response_model=BrowseResponse)
async def get_tv_root_menu():
    items = [
        MenuItem(id="tv_trending", label="Trending", childrenLink="/browse/tv/discover/tv/trending"),
        MenuItem(id="tv_new", label="New to Streaming", childrenLink="/browse/tv/discover/tv/new"),
        MenuItem(id="tv_airing", label="Airing Today", childrenLink="/browse/tv/discover/tv/airing"),
        MenuItem(id="tv_genres", label="Genres", childrenLink="/browse/tv/genres/tv"),
    ]
    for sub in SUBSCRIPTIONS:
        items.append(MenuItem(
            id=f"tv_sub_{sub['id']}", 
            label=sub['name'], 
            childrenLink=f"/browse/tv/provider/{sub['id']}/tv"
        ))
    return BrowseResponse(title="TV Shows", items=items)

@router.get("/movie_root", response_model=BrowseResponse)
async def get_movie_root_menu():
    items = [
        MenuItem(id="movie_trending", label="Trending", childrenLink="/browse/tv/discover/movie/trending"),
        MenuItem(id="movie_new", label="New Releases", childrenLink="/browse/tv/discover/movie/new"),
        MenuItem(id="movie_top", label="Top Rated", childrenLink="/browse/tv/discover/movie/top_rated"),
        MenuItem(id="movie_genres", label="Genres", childrenLink="/browse/tv/genres/movie"),
    ]
    for sub in SUBSCRIPTIONS:
        items.append(MenuItem(
            id=f"movie_sub_{sub['id']}", 
            label=sub['name'], 
            childrenLink=f"/browse/tv/provider/{sub['id']}/movie"
        ))
    return BrowseResponse(title="Movies", items=items)

# --- DISCOVERY ---

@router.get("/discover/{media_type}/{category}", response_model=BrowseResponse)
async def discover_media(
    media_type: str, 
    category: str, 
    genre_id: Optional[int] = None, 
    provider_id: Optional[int] = Query(None), 
    page: int = Query(1)
):
    url = f"{TMDB_BASE_URL}/discover/{media_type}"
    params = {
        "api_key": TMDB_API_KEY,
        "watch_region": WATCH_REGION,
        "with_watch_providers": str(provider_id) if provider_id else PROVIDER_IDS,
        "with_watch_monetization_types": "flatrate"
    }

    title = category.replace("_", " ").title()

    if category == "trending":
        url = f"{TMDB_BASE_URL}/trending/{media_type}/week"
    elif category == "new":
        one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        params["first_air_date.gte" if media_type == "tv" else "primary_release_date.gte"] = one_month_ago
        params["sort_by"] = "popularity.desc"
    elif category == "airing":
        url = f"{TMDB_BASE_URL}/tv/airing_today"
    elif category == "top_rated":
        params["sort_by"] = "vote_average.desc"
        params["vote_count.gte"] = 500

    if genre_id:
        params["with_genres"] = genre_id

    # Aggregate 5 TMDB pages to get 100 items per request
    return await _fetch_from_tmdb(url, params, f"{media_type.upper()} | {title}", media_type, page)

@router.get("/provider/{provider_id}/{media_type}", response_model=BrowseResponse)
async def get_provider_content(provider_id: int, media_type: str):
    provider_name = next((s['name'] for s in SUBSCRIPTIONS if s['id'] == provider_id), "Provider")
    return BrowseResponse(
        title=provider_name,
        items=[
            MenuItem(id="p_new", label="New", childrenLink=f"/browse/tv/discover/{media_type}/new?provider_id={provider_id}"),
            MenuItem(id="p_trending", label="Trending", childrenLink=f"/browse/tv/discover/{media_type}/trending?provider_id={provider_id}")
        ]
    )

@router.get("/genres/{media_type}", response_model=BrowseResponse)
async def get_genres(media_type: str):
    url = f"{TMDB_BASE_URL}/genre/{media_type}/list?api_key={TMDB_API_KEY}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        items = []
        for g in data.get("genres", []):
            items.append(MenuItem(
                id=f"genre_{g['id']}", 
                label=g['name'], 
                childrenLink=f"/browse/tv/discover/{media_type}/genre_list?genre_id={g['id']}"
            ))
        return BrowseResponse(title="Genres", items=items)

async def resolve_deep_link(media_type: str, item_id: int) -> Optional[str]:
    """
    Finds a direct Apple TV deep link by:
    1. Checking Movie of the Night (via motn_service)
    2. Falling back to Apple iTunes Search API
    3. Falling back to Title Search on Apple TV
    """
    _LOGGER.info(f"Resolving deep link for {media_type} {item_id}...")
    
    tmdb_url = f"{TMDB_BASE_URL}/{media_type}/{item_id}?api_key={TMDB_API_KEY}&append_to_response=external_ids"
    
    async with httpx.AsyncClient() as client:
        try:
            tmdb_res = await client.get(tmdb_url)
            tmdb_res.raise_for_status()
            metadata = tmdb_res.json()
            
            title = metadata.get("title") or metadata.get("name")
            date = metadata.get("release_date") or metadata.get("first_air_date") or ""
            year = date[:4]
            imdb_id = metadata.get("external_ids", {}).get("imdb_id")
            
            _LOGGER.info(f"Metadata: Title='{title}', Year='{year}', IMDB='{imdb_id}'")

            if imdb_id:
                motn_link = await motn_service.get_deep_link(media_type, imdb_id)
                if motn_link:
                    _LOGGER.info(f"Using MOTN deep link: {motn_link}")
                    return motn_link
            
            _LOGGER.info(f"MOTN failed for '{title}'. Falling back to Apple Search...")
            
            async def call_apple(term: str):
                apple_entity = "movie" if media_type == "movie" else "tvShow"
                apple_url = "https://itunes.apple.com/search"
                apple_params = {
                    "term": term,
                    "country": WATCH_REGION,
                    "entity": apple_entity,
                    "limit": 1
                }
                res = await client.get(apple_url, params=apple_params)
                res.raise_for_status()
                data = res.json()
                _LOGGER.info(f"Apple Search ('{term}'): {data.get('resultCount', 0)} results found.")
                return data

            if imdb_id:
                apple_data = await call_apple(imdb_id)
                if apple_data.get("resultCount", 0) > 0:
                    deeplink = apple_data["results"][0].get("trackViewUrl")
                    _LOGGER.info(f"Found Apple deep link via IMDB: {deeplink}")
                    return deeplink

            apple_data = await call_apple(f"{title} {year}")
            if apple_data.get("resultCount", 0) > 0:
                deeplink = apple_data["results"][0].get("trackViewUrl")
                _LOGGER.info(f"Found Apple deep link via Title+Year: {deeplink}")
                return deeplink
            
            apple_data = await call_apple(title)
            if apple_data.get("resultCount", 0) > 0:
                deeplink = apple_data["results"][0].get("trackViewUrl")
                _LOGGER.info(f"Found Apple deep link via Title: {deeplink}")
                return deeplink

            _LOGGER.warning(f"No direct Apple link found for {title}. Returning title search fallback.")
            return f"https://tv.apple.com/search?term={title}"
            
        except Exception as e:
            _LOGGER.error(f"Error during deep link fallback: {e}")
            return None

# --- HELPER ---

async def _fetch_from_tmdb(url: str, params: dict, title: str, default_media_type: str, internal_page: int = 1):
    async with httpx.AsyncClient() as client:
        try:
            items = []
            total_results = 0
            
            # TMDB returns 20 items per page. User wants 100 per internal page.
            # Internal page 1 = TMDB 1-5, Internal page 2 = TMDB 6-10, etc.
            start_tmdb_page = (internal_page - 1) * 5 + 1
            
            tasks = []
            for i in range(5):
                p = params.copy()
                p["page"] = start_tmdb_page + i
                tasks.append(client.get(url, params=p))
            
            responses = await asyncio.gather(*tasks)
            
            # Get max total pages among all responses to be safe
            max_tmdb_total_pages = 0
            
            for response in responses:
                if response.status_code != 200: continue
                
                data = response.json()
                total_results = max(total_results, data.get("total_results", 0))
                max_tmdb_total_pages = max(max_tmdb_total_pages, data.get("total_pages", 0))
                
                for item in data.get("results", []):
                    media_type = item.get('media_type', default_media_type)
                    media_label = "MOVIE" if media_type == "movie" else "TV"
                    year = item.get("release_date", item.get("first_air_date", ""))[:4]
                    
                    items.append(MenuItem(
                        id=f"tmdb_{item['id']}",
                        label=item.get("title") or item.get("name"),
                        subText=f"{media_label} | {year}" if year else media_label,
                        thumbnail=f"{IMAGE_BASE_URL}{item.get('poster_path')}" if item.get('poster_path') else None,
                        childrenLink=f"/browse/tv/detail/{media_type}/{item['id']}",
                        actionLink=f"/action/atv/play/{media_type}/{item['id']}"
                    ))
            
            # Internal total pages is TMDB total pages divided by 5
            internal_total_pages = (max_tmdb_total_pages // 5) + (1 if max_tmdb_total_pages % 5 > 0 else 0)
            
            return BrowseResponse(
                title=title, 
                items=items,
                page=internal_page,
                totalPages=internal_total_pages,
                totalItems=total_results
            )
        except Exception as e:
            _LOGGER.error(f"TMDB Fetch Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
