"""
Run this script once to authenticate with Etsy and save your tokens.

    python auth/oauth_setup.py

It will open a browser tab. Click "Allow Access", then return here.
Your access and refresh tokens are printed for you to save in Replit Secrets.
"""

import os
import hashlib
import base64
import secrets
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import requests
from config import (
    ETSY_API_KEY,
    ETSY_OAUTH_AUTHORIZE_URL,
    ETSY_OAUTH_TOKEN_URL,
    ETSY_OAUTH_REDIRECT_URI,
    ETSY_OAUTH_SCOPES,
)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def generate_pkce() -> tuple[str, str]:
    verifier = _b64url(os.urandom(32))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


_auth_code: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        _auth_code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Noctis: Authorization complete. You can close this tab.</h2>")

    def log_message(self, *args):
        pass


def run():
    verifier, challenge = generate_pkce()
    state = secrets.token_urlsafe(8)

    params = {
        "response_type": "code",
        "redirect_uri": ETSY_OAUTH_REDIRECT_URI,
        "scope": ETSY_OAUTH_SCOPES,
        "client_id": ETSY_API_KEY,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{ETSY_OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    server = HTTPServer(("localhost", 3003), _CallbackHandler)
    thread = Thread(target=server.handle_request)
    thread.start()

    print("\nOpening browser for Etsy authorization...")
    print(f"If it doesn't open automatically, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    thread.join(timeout=120)
    server.server_close()

    if not _auth_code:
        print("ERROR: No authorization code received. Did you click Allow?")
        return

    response = requests.post(
        ETSY_OAUTH_TOKEN_URL,
        json={
            "grant_type": "authorization_code",
            "client_id": ETSY_API_KEY,
            "redirect_uri": ETSY_OAUTH_REDIRECT_URI,
            "code": _auth_code,
            "code_verifier": verifier,
        },
    )

    if not response.ok:
        print(f"ERROR: Token exchange failed — {response.status_code} {response.text}")
        return

    data = response.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")

    print("\n✅ Authorization successful!\n")
    print("Add these to Replit Secrets (or your .env file):")
    print(f"\nETSY_ACCESS_TOKEN={access_token}")
    print(f"ETSY_REFRESH_TOKEN={refresh_token}")
    print()
    print("Your user_id is the prefix before the first dot in the access token:")
    if access_token:
        print(f"  User ID: {access_token.split('.')[0]}")
    print("\nRun test_connection.py next to verify everything works.")


if __name__ == "__main__":
    run()
