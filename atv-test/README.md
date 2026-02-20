# Apple TV Deeplink Tester

A simple Python prototype to verify `pyatv` functionality by sending deeplinks to an Apple TV.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Your Apple TV**:
   - Open `config.json`.
   - Update `atv_identifier` with your Apple TV's IP address or name.
   - If you don't know it, run the script with a placeholder, and it will scan and list discovered devices.

## Usage

To send a deeplink (e.g., an Apple TV+ show):

```bash
python main.py "https://tv.apple.com/show/ted-lasso/umc.cmc.vspf084u2mky4984f09y81re"
```

## How it works

The script uses `pyatv.scan` to find the device and `pyatv.connect` to establish a session. It then uses the `atv.apps.launch_app` method, which supports opening URLs directly on the Apple TV (typically requiring the Companion protocol).
