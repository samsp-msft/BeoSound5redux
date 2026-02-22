import httpx
import json
import os
import hashlib
import base64
import logging
import time
from typing import Optional, Dict, Any, Union

_LOGGER = logging.getLogger(__name__)

class TMDBService:
    def __init__(self):
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'tmdb_cache')
        self.cache_duration = 6 * 3600  # 6 hours in seconds
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_path(self, url: str) -> str:
        """
        Calculates the bucketed path for a given URL.
        Uses MD5 hash of the URL to determine a 2-char subfolder (256 buckets).
        Uses base64 encoding of the URL as the filename/key.
        """
        url_hash = hashlib.md5(url.encode()).hexdigest()
        bucket = url_hash[:2]
        
        # Base64 encode the URL for the filename
        # Use urlsafe_b64encode to avoid issues with / or + in filenames
        encoded_url = base64.urlsafe_b64encode(url.encode()).decode()
        
        # Filename limit safety: most filesystems have a 255 char limit
        if len(encoded_url) > 200:
            # If too long, use a combination of prefix and hash to keep it unique but short enough
            encoded_url = f"{encoded_url[:100]}...{url_hash}"

        bucket_dir = os.path.join(self.cache_dir, bucket)
        if not os.path.exists(bucket_dir):
            os.makedirs(bucket_dir)
            
        return os.path.join(bucket_dir, f"{encoded_url}.json")

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, client: Optional[httpx.AsyncClient] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves TMDB data from cache or API.
        """
        # Build full URL for caching key
        full_url = str(httpx.URL(url, params=params))
        cache_path = self._get_cache_path(full_url)
        
        # Check cache
        if os.path.exists(cache_path):
            try:
                mtime = os.path.getmtime(cache_path)
                if time.time() - mtime < self.cache_duration:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        _LOGGER.debug(f"TMDB FS Cache HIT for {full_url}")
                        return json.load(f)
                else:
                    _LOGGER.debug(f"TMDB FS Cache EXPIRED for {full_url}")
            except Exception as e:
                _LOGGER.error(f"Failed to read TMDB cache file {cache_path}: {e}")

        # Cache miss or expired
        _LOGGER.info(f"TMDB FS Cache MISS for {full_url}. Fetching from API...")
        
        if client:
            return await self._fetch(client, url, params, cache_path)
        else:
            async with httpx.AsyncClient() as new_client:
                return await self._fetch(new_client, url, params, cache_path)

    async def _fetch(self, client: httpx.AsyncClient, url: str, params: Optional[Dict[str, Any]], cache_path: str) -> Optional[Dict[str, Any]]:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Save to bucketed cache with formatting
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return data

        except Exception as e:
            _LOGGER.error(f"TMDB API error for {url}: {e}")
            return None

    async def search(self, query: str, media_type: str = "multi", api_key: str = "") -> Optional[Dict[str, Any]]:
        """Searches for media by title."""
        url = f"https://api.themoviedb.org/3/search/{media_type}"
        params = {
            "api_key": api_key,
            "query": query
        }
        return await self.get(url, params=params)

    async def get_media_details(self, media_type: str, tmdb_id: int, api_key: str = "") -> Optional[Dict[str, Any]]:
        """Fetches detailed metadata for a specific movie or TV show."""
        url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}"
        params = {
            "api_key": api_key,
            "append_to_response": "images,external_ids"
        }
        return await self.get(url, params=params)

# Global instance
tmdb_service = TMDBService()
