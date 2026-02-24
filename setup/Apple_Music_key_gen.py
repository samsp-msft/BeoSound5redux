import jwt # pip install pyjwt cryptography
import time
import http.server
import socketserver
import webbrowser
import os
import json
import sys

def get_developer_token(team_id, key_id, private_key_path):
    try:
        with open(private_key_path, "r") as f:
            private_key = f.read()
    except FileNotFoundError:
        print(f"Error: Private key file not found at {private_key_path}")
        sys.exit(1)

    headers = {
        "alg": "ES256",
        "kid": key_id,
    }

    payload = {
        "iss": team_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 15777000, # Max valid time is 6 months
    }

    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apple Music Token Generator</title>
    <script src="https://js-cdn.music.apple.com/musickit/v3/musickit.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 40px; max-width: 800px; margin: auto; background: #121212; color: #fff; line-height: 1.6; }}
        .container {{ background: #1e1e1e; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
        h2 {{ color: #fa243c; margin-top: 0; }}
        button {{ padding: 12px 24px; font-size: 16px; cursor: pointer; background: #fa243c; color: white; border: none; border-radius: 6px; font-weight: 600; transition: background 0.2s; }}
        button:hover {{ background: #d91e34; }}
        button:disabled {{ background: #444; cursor: not-allowed; }}
        textarea {{ width: 100%; height: 200px; margin-top: 20px; padding: 15px; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; background: #000; color: #00ff00; border: 1px solid #333; border-radius: 8px; box-sizing: border-box; font-size: 13px; }}
        .instruction {{ margin-bottom: 20px; color: #bbb; }}
        .status {{ margin-top: 10px; font-weight: bold; min-height: 1.6em; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Apple Music Authentication</h2>
        <p class="instruction">1. Click the button below to sign in with your Apple ID.<br>
        2. Once authorized, the JSON configuration will be generated below.<br>
        3. Copy the JSON and paste it into your <code>backend/config.json</code> file.</p>
        
        <button id="auth-btn">Authorize Apple Music</button>
        <div id="status" class="status">Waiting for MusicKit...</div>
        
        <textarea id="config-display" placeholder="Configuration JSON will appear here after authorization..." readonly></textarea>
    </div>

    <script>
        const DEVELOPER_TOKEN = "{dev_token}";

        async function initMusicKit() {{
            const status = document.getElementById('status');
            const authBtn = document.getElementById('auth-btn');
            const configDisplay = document.getElementById('config-display');

            console.log("Initializing MusicKit...");
            status.innerText = "Configuring MusicKit...";

            try {{
                await MusicKit.configure({{
                    developerToken: DEVELOPER_TOKEN,
                    app: {{
                        name: 'BeoSound 5 Redux',
                        build: '1.0.0'
                    }}
                }});
                console.log("MusicKit configured successfully.");
                status.innerText = "MusicKit Loaded. Ready to authorize.";
            }} catch (err) {{
                console.error("Configuration error:", err);
                status.innerText = "Error loading MusicKit: " + err.message;
                status.style.color = "#fa243c";
                return;
            }}

            const music = MusicKit.getInstance();

            authBtn.addEventListener('click', async () => {{
                console.log("Authorize button clicked.");
                try {{
                    status.innerText = "Authorizing (Check for popup)...";
                    status.style.color = "#fff";
                    
                    const userToken = await music.authorize(); 
                    console.log("Authorization successful.");
                    
                    const config = {{
                        "appleMusicDeveloperToken": DEVELOPER_TOKEN,
                        "appleMusicUserToken": userToken
                    }};
                    
                    configDisplay.value = JSON.stringify(config, null, 2);
                    status.innerText = "Success! Copy the JSON below.";
                    status.style.color = "#00ff00";
                }} catch (error) {{
                    console.error("Auth error:", error);
                    status.innerText = "Error: " + (error.message || error.description || "Authorization failed");
                    status.style.color = "#fa243c";
                }}
            }});
        }}

        // Handle case where musickit is already loaded or loads via event
        if (window.MusicKit) {{
            initMusicKit();
        }} else {{
            document.addEventListener('musickitloaded', initMusicKit);
        }}
        
        // Timeout for loading
        setTimeout(() => {{
            if (!window.MusicKit) {{
                document.getElementById('status').innerText = "Error: MusicKit library failed to load from Apple CDN.";
                document.getElementById('status').style.color = "#fa243c";
            }}
        }}, 5000);
    </script>
</body>
</html>
"""

class TokenHandler(http.server.SimpleHTTPRequestHandler):
    dev_token = ""
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            content = HTML_TEMPLATE.format(dev_token=self.dev_token)
            self.wfile.write(content.encode())
        else:
            self.send_error(404)

def run_server(dev_token):
    PORT = 8080
    TokenHandler.dev_token = dev_token
    # Allow port reuse to avoid 'Address already in use' errors on restart
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), TokenHandler) as httpd:
        print(f"\nServer started at http://localhost:{PORT}")
        print("Opening browser for authentication...")
        webbrowser.open(f"http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server after you have copied the tokens.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    print("--- Apple Music Token Generator Setup ---")
    team_id = input("Enter your Apple Team ID (10 characters): ").strip()
    key_id = input("Enter your Apple Music Key ID: ").strip()
    private_key_path = input(f"Enter path to your .p8 private key file (default: AuthKey_{key_id}.p8): ").strip()
    
    if not private_key_path:
        private_key_path = f"AuthKey_{key_id}.p8"

    dev_jwt = get_developer_token(team_id, key_id, private_key_path)
    print("\nDeveloper Token Generated Successfully.")
    
    run_server(dev_jwt)
