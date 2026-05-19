import time
import requests
from datetime import date
from config import (
    ETSY_API_KEY, ETSY_SHARED_SECRET, ETSY_ACCESS_TOKEN,
    ETSY_REFRESH_TOKEN, ETSY_BASE_URL, ETSY_OAUTH_TOKEN_URL,
    QPS_LIMIT, QPD_LIMIT,
)
from core.database import get_daily_api_calls


class RateLimitExceeded(Exception):
    pass


class EtsyClient:
    def __init__(self):
        self.api_key = ETSY_API_KEY
        self.shared_secret = ETSY_SHARED_SECRET
        self.access_token = ETSY_ACCESS_TOKEN
        self.base_url = ETSY_BASE_URL

        self._last_request_time = 0.0
        self._min_interval = 1.0 / QPS_LIMIT  # 0.2s between requests
        self._session_calls = 0

    # ── Internal ──────────────────────────────────────────────

    def _enforce_rate_limits(self):
        daily_used = get_daily_api_calls() + self._session_calls
        if daily_used >= QPD_LIMIT:
            raise RateLimitExceeded(f"Daily limit reached ({QPD_LIMIT} QPD). Resets at midnight.")

        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

    def _headers(self, authenticated: bool = False) -> dict:
        headers = {"x-api-key": self.api_key}
        if authenticated and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _request(self, method: str, endpoint: str, authenticated: bool = False, **kwargs):
        self._enforce_rate_limits()

        url = f"{self.base_url}{endpoint}"
        response = requests.request(
            method, url, headers=self._headers(authenticated), **kwargs
        )
        self._last_request_time = time.time()
        self._session_calls += 1

        if response.status_code == 401 and authenticated:
            refreshed = self._refresh_token()
            if refreshed:
                return self._request(method, endpoint, authenticated, **kwargs)

        response.raise_for_status()
        return response.json()

    def _refresh_token(self) -> bool:
        try:
            resp = requests.post(
                ETSY_OAUTH_TOKEN_URL,
                json={
                    "grant_type": "refresh_token",
                    "client_id": self.api_key,
                    "refresh_token": ETSY_REFRESH_TOKEN,
                },
            )
            if resp.ok:
                data = resp.json()
                self.access_token = data["access_token"]
                return True
        except Exception:
            pass
        return False

    # ── Public endpoints (API key only) ───────────────────────

    def ping(self) -> dict:
        return self._request("GET", "/application/openapi-ping")

    def search_listings(
        self,
        keywords: str,
        limit: int = 25,
        offset: int = 0,
        sort_on: str = "score",
        sort_order: str = "desc",
    ) -> dict:
        return self._request(
            "GET",
            "/application/listings/active",
            params={
                "keywords": keywords,
                "limit": limit,
                "offset": offset,
                "sort_on": sort_on,
                "sort_order": sort_order,
            },
        )

    # ── Authenticated endpoints (OAuth token) ─────────────────

    def get_me(self) -> dict:
        return self._request("GET", "/application/users/me", authenticated=True)

    def get_my_shops(self) -> dict:
        return self._request("GET", "/application/users/me/shops", authenticated=True)

    def get_shop_listings(self, shop_id: int, limit: int = 100, offset: int = 0) -> dict:
        return self._request(
            "GET",
            f"/application/shops/{shop_id}/listings/active",
            authenticated=True,
            params={"limit": limit, "offset": offset},
        )

    def get_shop_receipts(self, shop_id: int, limit: int = 100, offset: int = 0) -> dict:
        return self._request(
            "GET",
            f"/application/shops/{shop_id}/receipts",
            authenticated=True,
            params={"limit": limit, "offset": offset},
        )

    # ── Usage info ────────────────────────────────────────────

    @property
    def calls_used_today(self) -> int:
        return get_daily_api_calls() + self._session_calls

    @property
    def calls_remaining_today(self) -> int:
        return QPD_LIMIT - self.calls_used_today
