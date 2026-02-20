import asyncio
import json
import argparse
import sys
import pyatv
from pyatv.const import Protocol

async def load_config(config_path):
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse {config_path}.")
        sys.exit(1)

async def find_atv(atv_identifier):
    print(f"Searching for Apple TV with identifier: {atv_identifier}...")
    # Scan for Apple TVs
    discovered = await pyatv.scan(asyncio.get_event_loop(), timeout=10)
    
    for device in discovered:
        # Check against identifier (address, name, or unique ID)
        if atv_identifier in (device.identifier, device.address, device.name):
            print(f"Found: {device.name} ({device.address})")
            print("Protocols discovered:")
            for service in device.services:
                print(f" - {service.protocol}: {service.port}")
            return device
    
    print("Apple TV not found. Discovered devices:")
    for device in discovered:
        print(f" - {device.name}: {device.identifier} ({device.address})")
    return None

async def send_deeplink(atv_identifier, deeplink_url, credentials=None):
    loop = asyncio.get_event_loop()
    atv_device = await find_atv(atv_identifier)
    
    if not atv_device:
        print("Failed to find Apple TV. Please check your config.json.")
        return

    if credentials:
        for protocol_str, creds in credentials.items():
            try:
                # Convert string protocol to Enum if possible
                proto = Protocol[protocol_str]
                atv_device.set_credentials(proto, creds)
                print(f"Set credentials for {protocol_str}")
            except KeyError:
                print(f"Warning: Unknown protocol {protocol_str} in credentials")

    print(f"Connecting to {atv_device.name}...")
    atv = await pyatv.connect(atv_device, loop)
    
    try:
        # Check support status
        launch_feature = atv.features.get_feature(pyatv.interface.FeatureName.LaunchApp)
        if launch_feature.state != pyatv.interface.FeatureState.Available:
            print(f"Warning: LaunchApp state is {launch_feature.state}. This might fail if not paired.")
        
        print(f"Sending deeplink: {deeplink_url}")
        await atv.apps.launch_app(deeplink_url)
        print("Done!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        atv.close()

async def main():
    parser = argparse.ArgumentParser(description="Send a deeplink to an Apple TV.")
    parser.add_argument("url", help="The deeplink URL to send (e.g., https://tv.apple.com/...)")
    parser.add_argument("--config", default="config.json", help="Path to the config file.")
    args = parser.parse_args()

    config = await load_config(args.config)
    atv_identifier = config.get("atv_identifier")
    credentials = config.get("credentials")
    
    if not atv_identifier or atv_identifier == "YOUR_ATV_IDENTIFIER":
        print("Please set your Apple TV identifier in config.json first.")
        # Trigger a scan to help the user find the identifier
        await find_atv("")
        return

    await send_deeplink(atv_identifier, args.url, credentials)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
