import httpx
import json
import os
import logging
from typing import Optional, List, Dict, Any

_LOGGER = logging.getLogger(__name__)

class MOTNService:
    def __init__(self):
        self.config = self._load_config()
        # The user mentioned the key is in config.json
        # I'll check for 'motn' or 'movieofthenight' or 'rapidapi_key'
        self.api_key = (
            self.config.get("motn", {}).get("api_key") or 
            self.config.get("movieofthenight", {}).get("api_key") or
            self.config.get("rapidapi_key")
        )
        self.cache_path = os.path.join(os.path.dirname(__file__), 'motn_cache.json')
        self.cache = self._load_cache()
        self.watch_region = self.config.get("watch_region", "us").lower()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            _LOGGER.error(f"Failed to load config for MOTNService: {e}")
            return {}

    def _load_cache(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                _LOGGER.error(f"Failed to load MOTN cache: {e}")
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            _LOGGER.error(f"Failed to save MOTN cache: {e}")

    async def get_deep_link(self, media_type: str, imdb_id: str) -> Optional[str]:
        """
        Gets a deep link for a show using its IMDb ID, with caching.
        """
        if not imdb_id:
            return None

        cache_key = imdb_id
        if cache_key in self.cache:
            _LOGGER.info(f"MOTN Cache HIT for {cache_key}")
            # We store the whole response or just the link? 
            # User wants to cache episode data too.
            data = self.cache[cache_key]
            return self._extract_best_link(data)

        if not self.api_key:
            _LOGGER.error("MOTN API key not found in config.")
            return None

        _LOGGER.info(f"MOTN Cache MISS for {cache_key}. Fetching from API...")
        
        # Based on docs: https://docs.movieofthenight.com/resource/shows#get-a-show
        # Endpoint is typically: https://streaming-availability.p.rapidapi.com/v2/get/basic
        # Or if it's direct: https://api.movieofthenight.com/...
        # I'll use the RapidAPI version which is the most common one for this service.
        url = "https://streaming-availability.p.rapidapi.com/shows/" + imdb_id
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "streaming-availability.p.rapidapi.com"
        }
        params = {
        #    "imdb_id": imdb_id,
            "country": "us",
            "series_granularity": "episode",
            "output_language": "en",
            "content-type": "application/json; charset=utf-8"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                # Cache the whole result as requested (including episode data)
                self.cache[cache_key] = data
                self._save_cache()
                
                return self._extract_best_link(data)

            except Exception as e:
                _LOGGER.error(f"MOTN API error for {imdb_id}: {e}")
                return None

    def _extract_best_link(self, show_data: Any) -> Optional[str]:
        """
        Extracts the best deep link (Apple TV/iOS) from the MOTN data.
        """
        if not show_data:
            return None
        
        # streamingOptions is a dict where keys are country codes
        streaming_info = show_data.get('streamingOptions', {}).get(self.watch_region, [])
        
        if not streaming_info:
            _LOGGER.warning(f"No streaming options found for region: {self.watch_region}")
            return None

        # Get list of subscribed provider names (e.g., ['netflix', 'disney'])
        # MOTN uses lowercase service IDs
        subscribed_service_ids = [s['name'].lower().replace("+", "").replace(" ", "") for s in self.config.get("subscriptions", [])]
        # Common overrides
        if 'amazonprimevideo' in subscribed_service_ids: subscribed_service_ids.append('prime')
        if 'max' in subscribed_service_ids: subscribed_service_ids.append('hbo')

        _LOGGER.debug(f"Matching against subscriptions: {subscribed_service_ids}")

        best_link = None
        
        # 1. Try to find a match in user subscriptions
        for entry in streaming_info:
            service_id = entry.get('service', {}).get('id', '').lower()
            if service_id in subscribed_service_ids:
                # Prefer videoLink (direct playback) over link (details page)
                link = entry.get('videoLink') or entry.get('link')
                if link:
                    _LOGGER.info(f"Found subscription match: {service_id} -> {link}")
                    return link

        # 2. Fallback to ANY valid link if no subscription match found
        for entry in streaming_info:
            link = entry.get('videoLink') or entry.get('link')
            if link:
                _LOGGER.info(f"Using fallback link from: {entry.get('service', {}).get('id')}")
                return link
        
        return None

# Global instance
motn_service = MOTNService()
