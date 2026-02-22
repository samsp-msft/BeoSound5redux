import httpx
import json
import os
import hashlib
import logging
from typing import Optional, List, Dict, Any

_LOGGER = logging.getLogger(__name__)

class MOTNService:
    def __init__(self):
        self.config = self._load_config()
        self.api_key = (
            self.config.get("motn", {}).get("api_key") or 
            self.config.get("movieofthenight", {}).get("api_key") or
            self.config.get("rapidapi_key")
        )
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'motn_cache')
        self.old_cache_path = os.path.join(os.path.dirname(__file__), 'motn_cache.json')
        self.watch_region = self.config.get("watch_region", "us").lower()
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        # Run migration if old file exists
        if os.path.exists(self.old_cache_path):
            self._migrate_old_cache()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            _LOGGER.error(f"Failed to load config for MOTNService: {e}")
            return {}

    def _get_cache_path(self, imdb_id: str) -> str:
        """
        Calculates the bucketed path for a given IMDb ID.
        Uses MD5 hash of the ID to determine a 2-char subfolder (256 buckets).
        """
        bucket = hashlib.md5(imdb_id.encode()).hexdigest()[:2]
        bucket_dir = os.path.join(self.cache_dir, bucket)
        if not os.path.exists(bucket_dir):
            os.makedirs(bucket_dir)
        return os.path.join(bucket_dir, f"{imdb_id}.json")

    def _migrate_old_cache(self):
        """
        Migrates data from the single motn_cache.json file into the bucketed structure.
        """
        _LOGGER.info("Migrating old MOTN cache to bucketed structure...")
        try:
            with open(self.old_cache_path, 'r') as f:
                old_data = json.load(f)
                for imdb_id, data in old_data.items():
                    path = self._get_cache_path(imdb_id)
                    with open(path, 'w') as out_f:
                        json.dump(data, out_f, indent=2)
            
            # Rename old cache instead of deleting, for safety
            os.rename(self.old_cache_path, self.old_cache_path + ".bak")
            _LOGGER.info(f"Migration complete. Old cache backed up to {self.old_cache_path}.bak")
        except Exception as e:
            _LOGGER.error(f"Migration failed: {e}")

    async def get_show_data(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the full show data object from cache or API.
        """
        if not imdb_id:
            return None

        cache_path = self._get_cache_path(imdb_id)
        
        # Check filesystem cache
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                _LOGGER.error(f"Failed to read cache file {cache_path}: {e}")

        if not self.api_key:
            _LOGGER.error("MOTN API key not found in config.")
            return None

        _LOGGER.info(f"MOTN FS Cache MISS for {imdb_id}. Fetching full show data from API...")
        
        url = "https://streaming-availability.p.rapidapi.com/shows/" + imdb_id
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "streaming-availability.p.rapidapi.com"
        }
        params = {
            "country": "us",
            "series_granularity": "episode",
            "output_language": "en"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                # Save to bucketed cache with formatting
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                return data

            except Exception as e:
                _LOGGER.error(f"MOTN API error for {imdb_id}: {e}")
                return None

    async def get_deep_link(self, media_type: str, imdb_id: str) -> Optional[str]:
        """
        Gets a deep link for a show using its IMDb ID, with bucketed filesystem caching.
        """
        data = await self.get_show_data(imdb_id)
        if data:
            return self._extract_best_link(data)
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

        # Get list of subscribed motn_ids from config
        subscribed_motn_ids = {s.get('motn_id') for s in self.config.get("subscriptions", []) if s.get('motn_id')}

        _LOGGER.debug(f"Matching against subscriptions (motn_ids): {subscribed_motn_ids}")

        # 1a. Try to find a 'subscription' match in user subscriptions first
        for entry in streaming_info:
            service_id = entry.get('service', {}).get('id', '').lower()
            service_type = entry.get('type')
            if service_id in subscribed_motn_ids and service_type == 'subscription':
                # Prefer videoLink (direct playback) over link (details page)
                link = entry.get('videoLink') or entry.get('link')
                if link:
                    _LOGGER.info(f"Found primary subscription match: {service_id} -> {link}")
                    return link

        # 1b. Try to find any other match in user subscriptions (e.g., addons)
        for entry in streaming_info:
            service_id = entry.get('service', {}).get('id', '').lower()
            if service_id in subscribed_motn_ids:
                link = entry.get('videoLink') or entry.get('link')
                if link:
                    _LOGGER.info(f"Found secondary (addon/other) subscription match: {service_id} -> {link}")
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
