import json
import os
import sys
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Scopes required for video uploads and metadata checks
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

class CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    
    # Suppress log messages in the console to avoid clutter
    def log_message(self, format, *args):
        return

    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if 'code' in params:
            CallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization successful!</h1><p>You can close this tab and return to the terminal.</p></body></html>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No authorization code found.")

def main():
    secret_path = 'C:\\Users\\Preethve\\client_secret.json'
    if not os.path.exists(secret_path):
        print(f"Error: GCP client secret file not found at {secret_path}")
        sys.exit(1)
        
    with open(secret_path, 'r', encoding='utf-8') as f:
        creds = json.load(f)
        
    client_type = 'installed' if 'installed' in creds else 'web'
    client_data = creds[client_type]
    client_id = client_data['client_id']
    client_secret = client_data['client_secret']
    
    # 1. Build Authorization URL
    auth_base = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": client_id,
        "redirect_uri": "http://localhost",
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"{auth_base}?{urllib.parse.urlencode(params)}"
    
    print("\n=== YouTube OAuth2 Refresh Token Generator ===")
    print("1. Opening authorization link in browser...")
    print(f"\nLink: {auth_url}\n")
    
    try:
        webbrowser.open(auth_url)
    except Exception as e:
        print(f"Failed to open browser: {e}. Please copy and paste the link above into your browser.")
    
    # 2. Start local HTTP server on port 80 to catch the redirect
    code = None
    server = None
    try:
        # Binding to 127.0.0.1 on port 80
        server = HTTPServer(('127.0.0.1', 80), CallbackHandler)
        print("2. Waiting for redirect on http://localhost:80 ...")
        server.handle_request() # Wait for one request
        code = CallbackHandler.auth_code
    except Exception as e:
        print(f"\n[Warning] Local server failed to start (port 80 might be in use or requires admin): {e}")
        print("Please log in via the browser window. Once authorized, the browser will redirect to http://localhost/?code=...")
        print("Copy the entire redirected URL (or the 'code' parameter value) from the browser address bar.")
        code_input = input("\nPaste the redirected URL or authorization code here: ").strip()
        
        # Extract code from URL if URL was pasted
        if 'code=' in code_input:
            parsed = urllib.parse.urlparse(code_input)
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get('code', [code_input])[0]
        else:
            code = code_input
            
    if not code:
        print("Error: No authorization code provided.")
        sys.exit(1)
        
    print("\n3. Exchanging authorization code for tokens...")
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": "http://localhost",
        "grant_type": "authorization_code"
    }
    
    res = requests.post(token_url, data=token_data)
    if res.status_code != 200:
        print(f"Error exchanging code: {res.status_code} {res.text}")
        sys.exit(1)
        
    res_json = res.json()
    refresh_token = res_json.get('refresh_token')
    
    if not refresh_token:
        print("\nWarning: Google did not return a refresh token.")
        print("This happens if you have already authorized this app.")
        print("Please go to https://myaccount.google.com/connections, find this App, delete its connection, and rerun this script.")
        sys.exit(1)
        
    print("\n================ SUCCESS ================")
    print("New Refresh Token successfully generated!")
    print("\nCopy the refresh token below:")
    print(refresh_token)
    print("\nTo update GitHub Secrets, run the following commands in your terminal:")
    print(f'gh secret set YOUTUBE_CLIENT_ID --body "{client_id}"')
    print(f'gh secret set YOUTUBE_CLIENT_SECRET --body "{client_secret}"')
    print(f'gh secret set YOUTUBE_REFRESH_TOKEN --body "{refresh_token}"')
    print("=========================================\n")

if __name__ == '__main__':
    main()
