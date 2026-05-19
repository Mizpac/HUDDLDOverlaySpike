"""
Run after oauth_setup.py to verify your API key and OAuth token both work.

    python test_connection.py
"""

from core.database import init_db
from core.etsy_client import EtsyClient


def main():
    print("Noctis — connection test\n")

    init_db()
    print("✅ Database initialized")

    client = EtsyClient()

    print("\n── API key test (ping) ──────────────────────────")
    try:
        result = client.ping()
        print(f"✅ API key valid — application_id: {result.get('application_id')}")
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return

    print("\n── OAuth test (your account) ────────────────────")
    try:
        me = client.get_me()
        print(f"✅ OAuth token valid — logged in as: {me.get('login', 'unknown')}")
    except Exception as e:
        print(f"❌ OAuth test failed — run auth/oauth_setup.py first: {e}")

    print("\n── Public search test ───────────────────────────")
    try:
        results = client.search_listings("personalized gift", limit=5)
        count = results.get("count", 0)
        print(f"✅ Public search working — {count} results for 'personalized gift'")
    except Exception as e:
        print(f"❌ Search test failed: {e}")

    print(f"\n── API usage today ──────────────────────────────")
    print(f"   Calls used this session: {client._session_calls}")
    print(f"   Daily limit: 5,000 QPD")
    print("\nAll done. Ready to build.")


if __name__ == "__main__":
    main()
