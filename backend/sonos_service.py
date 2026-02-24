import soco
import logging
import asyncio
import os
import json

_LOGGER = logging.getLogger(__name__)

class SonosService:
    def __init__(self):
        self.device = None
        self.status = "initializing"
        self.sonos_name = self._load_sonos_name()

    def _load_sonos_name(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("sonos_name")
        except Exception as e:
            _LOGGER.error(f"Failed to load sonos_name from config: {e}")
        return None

    def initialize(self):
        """Starts the discovery process."""
        asyncio.create_task(self.discover())

    async def discover(self):
        """Discovers a Sonos device on the network."""
        self.status = "discovering"
        try:
            # discover is blocking, run in executor
            loop = asyncio.get_event_loop()
            devices = await loop.run_in_executor(None, soco.discover)
            
            if devices:
                if self.sonos_name:
                    for d in devices:
                        if d.player_name == self.sonos_name:
                            self.device = d
                            break
                
                if not self.device:
                    # Pick the first one if name not found or not provided
                    self.device = list(devices)[0]
                
                self.status = "ready"
                _LOGGER.info(f"Sonos device found: {self.device.player_name} ({self.device.ip_address})")
            else:
                _LOGGER.warning("No Sonos devices found.")
                self.status = "failed"
        except Exception as e:
            _LOGGER.error(f"Failed to discover Sonos: {e}")
            self.status = "failed"

    async def play_apple_music(self, am_id: str):
        """Plays an Apple Music item on the Sonos device."""
        if not self.device:
            _LOGGER.error("No Sonos device available for playback.")
            return False
        
        # Parse media type if provided in the ID (e.g. "album/123")
        media_type = None
        if "/" in am_id:
            parts = am_id.split("/", 1)
            media_type = parts[0]
            am_id = parts[1]

        # Determine item type and flags for URI
        # Using x-sonos-http format which is more reliable for enqueuing
        
        uri = ""
        is_library = am_id.startswith("l.") or am_id.startswith("p.") or am_id.startswith("i.")
        
        if not media_type:
            # Fallback to inference if type not explicitly provided
            if am_id.startswith("i."):
                media_type = "librarytrack"
            elif am_id.startswith("l."):
                media_type = "libraryalbum"
            elif am_id.startswith("p."):
                media_type = "libraryplaylist"
            elif am_id.startswith("pl."):
                media_type = "playlist"
            elif am_id.isdigit() and len(am_id) > 8:
                # This could be a catalog track or album. 
                # For now, we'll try to guess based on length or just default to album
                # since tracks are often handled differently.
                # Actually, many catalog track IDs are 10 digits too.
                media_type = "album" 
            else:
                media_type = "album"

        flags = "8300" # Default for containers
        if "track" in media_type:
            flags = "8224"

        # Format: x-sonos-http:[type]%3a[ID].mp4?sid=204&flags=[flags]&sn=4
        # Note: sn=4 is the verified account serial number for Apple Music on this system
        uri = f"x-sonos-http:{media_type}%3a{am_id}.mp4?sid=204&flags={flags}&sn=4"

        _LOGGER.info(f"Attempting playback. ID: {am_id} (Type: {media_type}) -> URI: {uri}")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Clear the current queue
            _LOGGER.info("Clearing Sonos queue...")
            await loop.run_in_executor(None, self.device.clear_queue)
            
            # Add the new URI to the queue
            _LOGGER.info(f"Adding URI to queue: {uri}")
            pos = await loop.run_in_executor(None, self.device.add_uri_to_queue, uri)
            _LOGGER.info(f"Added to queue at position: {pos}")
            
            # Start playback from the first item in the queue
            _LOGGER.info("Starting playback from queue...")
            await loop.run_in_executor(None, self.device.play_from_queue, 0)
            
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to play Apple Music on Sonos: {e}")
            # Fallback to direct play_uri if queue method fails
            _LOGGER.info("Attempting fallback direct play_uri...")
            try:
                await loop.run_in_executor(None, self.device.play_uri, uri)
                return True
            except Exception as fe:
                _LOGGER.error(f"Fallback direct play_uri also failed: {fe}")
                return False

    async def play_uri(self, uri: str, meta: str = ""):
        """Plays a URI on the Sonos device."""
        if not self.device or self.status != "ready":
            _LOGGER.warning("Sonos not ready, attempting rediscovery...")
            await self.discover()
            if not self.device:
                return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.device.play_uri, uri, meta)
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to play URI on Sonos: {e}")
            return False

    async def play_items(self, uris: list):
        """Adds items to queue and plays."""
        if not self.device:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            # Clear queue
            await loop.run_in_executor(None, self.device.clear_queue)
            # Add items
            for uri in uris:
                await loop.run_in_executor(None, self.device.add_uri_to_queue, uri)
            # Play
            await loop.run_in_executor(None, self.device.play_from_queue, 0)
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to play items on Sonos: {e}")
            return False

# Global instance
sonos_service = SonosService()
