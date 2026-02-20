import asyncio
import pyatv
from pyatv.const import Protocol, PowerState
import logging
import json
import os

_LOGGER = logging.getLogger(__name__)

class AppleTVService:
    def __init__(self):
        self.atv = None
        self.status = "initializing" # initializing, connecting, ready, failed
        self.config = self._load_config()
        self._lock = asyncio.Lock()

    def initialize(self):
        """Starts the connection process in the running event loop."""
        asyncio.create_task(self.connect())

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            _LOGGER.error(f"Failed to load config for AppleTVService: {e}")
            return {}

    async def connect(self):
        """Attempts to connect to the Apple TV in the background."""
        self.status = "connecting"
        atv_id = self.config.get("atv_identifier")
        credentials = self.config.get("atv_credentials", {})

        if not atv_id:
            _LOGGER.error("No atv_identifier found in config.")
            self.status = "failed"
            return

        try:
            _LOGGER.info(f"Scanning for Apple TV: {atv_id}...")
            discovered = await pyatv.scan(asyncio.get_event_loop(), timeout=10)
            target = next((d for d in discovered if atv_id in (d.identifier, d.address, d.name)), None)

            if not target:
                _LOGGER.error(f"Apple TV {atv_id} not found on network.")
                self.status = "failed"
                return

            # Apply credentials
            for protocol_str, creds in credentials.items():
                try:
                    proto = Protocol[protocol_str]
                    target.set_credentials(proto, creds)
                    _LOGGER.info(f"Set credentials for {protocol_str}")
                except KeyError:
                    _LOGGER.warning(f"Unknown protocol {protocol_str} in credentials")

            _LOGGER.info(f"Connecting to {target.name}...")
            self.atv = await pyatv.connect(target, asyncio.get_event_loop())
            self.status = "ready"
            _LOGGER.info(f"Apple TV {target.name} is READY")
            
        except Exception as e:
            _LOGGER.error(f"Failed to connect to Apple TV: {e}")
            self.status = "failed"

    async def get_power_state(self) -> PowerState:
        """Returns the current power state of the Apple TV."""
        if not self.atv:
            return PowerState.Unknown
        return self.atv.power.power_state

    async def ensure_powered_on(self):
        """Checks power state and turns on the device if necessary."""
        state = await self.get_power_state()
        if state != PowerState.On:
            _LOGGER.info(f"Apple TV is {state.name}. Turning it ON...")
            await self.atv.power.turn_on()
            # Give it a moment to wake up
            await asyncio.sleep(2)
            return True
        return False

    async def launch_app(self, url: str):
        """Launches an app or deep link on the Apple TV."""
        if self.status != "ready" or not self.atv:
            _LOGGER.warning(f"Cannot launch app, service status is {self.status}")
            return False

        try:
            # Ensure device is awake before sending the command
            await self.ensure_powered_on()
            
            _LOGGER.info(f"Launching deep link: {url}")
            await self.atv.apps.launch_app(url)
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to launch app: {e}")
            return False

# Global instance
atv_service = AppleTVService()


# Global instance
atv_service = AppleTVService()
