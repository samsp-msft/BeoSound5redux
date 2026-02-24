import httpx
import json
import os
import logging
from typing import Optional, List, Dict, Any
from models import MenuItem, ImageSet

_LOGGER = logging.getLogger(__name__)

class AppleMusicService:
    def __init__(self):
        self.config = self._load_config()
        self.apple_music_config = self.config.get("apple_music", {})
        self.dev_token = self.apple_music_config.get("appleMusicDeveloperToken")
        self.user_token = self.apple_music_config.get("appleMusicUserToken")
        self.base_url = "https://api.music.apple.com/v1"

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            _LOGGER.error(f"Failed to load config for AppleMusicService: {e}")
        return {}

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.dev_token}",
            "Music-User-Token": self.user_token
        }

    def _map_artwork(self, artwork: Dict[str, Any]) -> Optional[ImageSet]:
        if not artwork:
            return None
        
        url_template = artwork.get("url", "")
        if not url_template:
            return None
        
        # Replace {w} and {h} with reasonable sizes
        # Portrait-like for albums/playlists, or just square
        p_small = url_template.replace("{w}", "300").replace("{h}", "300")
        p_large = url_template.replace("{w}", "600").replace("{h}", "600")
        
        return ImageSet(
            portrait_small=p_small,
            portrait_large=p_large,
            landscape_small=p_small,
            landscape_large=p_large
        )

    def _get_action_link(self, item_id: str, item_type: str) -> str:
        """Maps Apple Music types to Sonos-compatible type strings for action links."""
        # type_map keys are what Apple Music API returns in 'type' field
        type_map = {
            "albums": "album",
            "library-albums": "libraryalbum",
            "playlists": "playlist",
            "library-playlists": "libraryplaylist",
            "songs": "track",
            "library-songs": "librarytrack"
        }
        sonos_type = type_map.get(item_type, "album") # default to album
        
        # Override if ID prefix is known
        if item_id.startswith("l."): sonos_type = "libraryalbum"
        elif item_id.startswith("p."): sonos_type = "libraryplaylist"
        elif item_id.startswith("i."): sonos_type = "librarytrack"
        
        return f"/action/music/play/{sonos_type}/{item_id}"

    async def get_library_playlists(self) -> List[MenuItem]:
        url = f"{self.base_url}/me/library/playlists"
        items = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json().get("data", [])
                
                for item in data:
                    attrs = item.get("attributes", {})
                    items.append(MenuItem(
                        id=item.get("id"),
                        label=attrs.get("name", "Unknown Playlist"),
                        subText=attrs.get("curatorName", ""),
                        images=self._map_artwork(attrs.get("artwork")),
                        childrenLink=f"/browse/music/apple/playlist/{item.get('id')}",
                        actionLink=self._get_action_link(item.get("id"), "library-playlists")
                    ))
            except Exception as e:
                _LOGGER.error(f"Failed to fetch Apple Music playlists: {e}")
        return items

    async def get_playlist_tracks(self, playlist_id: str) -> List[MenuItem]:
        # Library playlists start with 'p.', catalog ones usually don't or start with 'pl.'
        is_library = playlist_id.startswith("p.")
        if is_library:
            url = f"{self.base_url}/me/library/playlists/{playlist_id}/tracks"
        else:
            # For catalog playlists, we might need a storefront, but we'll try library first
            url = f"{self.base_url}/me/library/playlists/{playlist_id}/tracks"

        items = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json().get("data", [])
                
                for item in data:
                    attrs = item.get("attributes", {})
                    items.append(MenuItem(
                        id=item.get("id"),
                        label=attrs.get("name", "Unknown Track"),
                        subText=attrs.get("artistName", ""),
                        images=self._map_artwork(attrs.get("artwork")),
                        actionLink=self._get_action_link(item.get("id"), "library-songs" if is_library else "songs")
                    ))
            except Exception as e:
                _LOGGER.error(f"Failed to fetch tracks for playlist {playlist_id}: {e}")
        return items

    async def get_library_albums(self) -> List[MenuItem]:
        url = f"{self.base_url}/me/library/albums"
        items = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json().get("data", [])
                
                for item in data:
                    attrs = item.get("attributes", {})
                    items.append(MenuItem(
                        id=item.get("id"),
                        label=attrs.get("name", "Unknown Album"),
                        subText=attrs.get("artistName", ""),
                        images=self._map_artwork(attrs.get("artwork")),
                        childrenLink=f"/browse/music/apple/album/{item.get('id')}",
                        actionLink=self._get_action_link(item.get("id"), "library-albums")
                    ))
            except Exception as e:
                _LOGGER.error(f"Failed to fetch Apple Music albums: {e}")
        return items

    async def get_album_tracks(self, album_id: str) -> List[MenuItem]:
        # Library albums start with 'l.'
        is_library = album_id.startswith("l.")
        if is_library:
            url = f"{self.base_url}/me/library/albums/{album_id}/tracks"
        else:
            # For catalog items, we need catalog/us/albums/id
            url = f"{self.base_url}/catalog/us/albums/{album_id}/tracks"

        items = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json().get("data", [])
                
                for item in data:
                    attrs = item.get("attributes", {})
                    items.append(MenuItem(
                        id=item.get("id"),
                        label=attrs.get("name", "Unknown Track"),
                        subText=attrs.get("artistName", ""),
                        images=self._map_artwork(attrs.get("artwork")),
                        actionLink=self._get_action_link(item.get("id"), "library-songs" if is_library else "songs")
                    ))
            except Exception as e:
                _LOGGER.error(f"Failed to fetch tracks for album {album_id}: {e}")
        return items

    async def get_library_artists(self) -> List[MenuItem]:
        url = f"{self.base_url}/me/library/artists"
        items = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json().get("data", [])
                
                for item in data:
                    attrs = item.get("attributes", {})
                    items.append(MenuItem(
                        id=item.get("id"),
                        label=attrs.get("name", "Unknown Artist"),
                        childrenLink=f"/browse/music/apple/artist/{item.get('id')}"
                    ))
            except Exception as e:
                _LOGGER.error(f"Failed to fetch Apple Music artists: {e}")
        return items

    async def get_artist_albums(self, artist_id: str) -> List[MenuItem]:
        url = f"{self.base_url}/me/library/artists/{artist_id}/albums"
        items = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json().get("data", [])
                
                for item in data:
                    attrs = item.get("attributes", {})
                    items.append(MenuItem(
                        id=item.get("id"),
                        label=attrs.get("name", "Unknown Album"),
                        subText=attrs.get("artistName", ""),
                        images=self._map_artwork(attrs.get("artwork")),
                        childrenLink=f"/browse/music/apple/album/{item.get('id')}",
                        actionLink=self._get_action_link(item.get("id"), "library-albums")
                    ))
            except Exception as e:
                _LOGGER.error(f"Failed to fetch albums for artist {artist_id}: {e}")
        return items

    async def get_recommendations(self) -> List[MenuItem]:
        """Fetches 'Top Picks' and other recommendations."""
        url = f"{self.base_url}/me/recommendations"
        items = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json().get("data", [])
                
                for rec in data:
                    attrs = rec.get("attributes", {})
                    title = attrs.get("title", {}).get("stringForDisplay", "Recommendation")
                    
                    # Recommendations are collections of items (albums, playlists, etc.)
                    # For the root view, we might want to show these categories
                    items.append(MenuItem(
                        id=rec.get("id"),
                        label=title,
                        childrenLink=f"/browse/music/apple/recommendation/{rec.get('id')}"
                    ))
            except Exception as e:
                _LOGGER.error(f"Failed to fetch Apple Music recommendations: {e}")
        return items

    async def get_recommendation_items(self, recommendation_id: str) -> List[MenuItem]:
        url = f"{self.base_url}/me/recommendations/{recommendation_id}"
        items = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                rec_data = response.json().get("data", [])
                if not rec_data:
                    return []
                
                # A recommendation has relationships (usually 'contents')
                contents = rec_data[0].get("relationships", {}).get("contents", {}).get("data", [])
                for item in contents:
                    attrs = item.get("attributes", {})
                    item_type = item.get("type")
                    
                    label = attrs.get("name") or attrs.get("title") or "Unknown"
                    sub_text = attrs.get("artistName") or attrs.get("curatorName") or ""
                    
                    children_link = None
                    if item_type == "albums" or item_type == "library-albums":
                        children_link = f"/browse/music/apple/album/{item.get('id')}"
                    elif item_type == "playlists" or item_type == "library-playlists":
                        children_link = f"/browse/music/apple/playlist/{item.get('id')}"
                    
                    items.append(MenuItem(
                        id=item.get("id"),
                        label=label,
                        subText=sub_text,
                        images=self._map_artwork(attrs.get("artwork")),
                        childrenLink=children_link,
                        actionLink=self._get_action_link(item.get("id"), item_type)
                    ))
            except Exception as e:
                _LOGGER.error(f"Failed to fetch recommendation items: {e}")
        return items

    async def get_recent_played(self) -> List[MenuItem]:
        url = f"{self.base_url}/me/recent/played"
        items = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json().get("data", [])
                
                for item in data:
                    attrs = item.get("attributes", {})
                    item_type = item.get("type")
                    
                    label = attrs.get("name") or "Unknown"
                    sub_text = attrs.get("artistName") or attrs.get("curatorName") or ""
                    
                    children_link = None
                    if item_type == "albums" or item_type == "library-albums":
                        children_link = f"/browse/music/apple/album/{item.get('id')}"
                    elif item_type == "playlists" or item_type == "library-playlists":
                        children_link = f"/browse/music/apple/playlist/{item.get('id')}"
                    
                    items.append(MenuItem(
                        id=item.get("id"),
                        label=label,
                        subText=sub_text,
                        images=self._map_artwork(attrs.get("artwork")),
                        childrenLink=children_link,
                        actionLink=self._get_action_link(item.get("id"), item_type)
                    ))
            except Exception as e:
                _LOGGER.error(f"Failed to fetch Apple Music recently played: {e}")
        return items

    async def search_albums(self, query: str) -> List[Dict[str, Any]]:
        """Search the Apple Music catalog for albums."""
        url = f"{self.base_url}/catalog/us/search"
        params = {
            "term": query,
            "types": "albums",
            "limit": 5
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self._get_headers(), params=params)
                response.raise_for_status()
                data = response.json().get("results", {}).get("albums", {}).get("data", [])
                return data
            except Exception as e:
                _LOGGER.error(f"Failed to search Apple Music albums: {e}")
                return []

# Global instance
apple_music_service = AppleMusicService()
