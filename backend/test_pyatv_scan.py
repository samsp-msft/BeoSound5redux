import asyncio
from pyatv import scan

async def main():
    print("Starting pyatv scan...")
    devices = await scan(loop=asyncio.get_event_loop(), timeout=10)
    if devices:
        print(f"Found {len(devices)} devices:")
        for device in devices:
            print(f"  Device: {device}")
    else:
        print("No devices found.")

if __name__ == "__main__":
    asyncio.run(main())
