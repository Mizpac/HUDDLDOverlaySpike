import os
from dotenv import load_dotenv

load_dotenv()

# Etsy credentials
ETSY_API_KEY = os.getenv("ETSY_API_KEY", "")
ETSY_SHARED_SECRET = os.getenv("ETSY_SHARED_SECRET", "")
ETSY_ACCESS_TOKEN = os.getenv("ETSY_ACCESS_TOKEN", "")
ETSY_REFRESH_TOKEN = os.getenv("ETSY_REFRESH_TOKEN", "")
ETSY_SHOP_ID = os.getenv("ETSY_SHOP_ID", "")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Etsy API endpoints
ETSY_BASE_URL = "https://api.etsy.com/v3"
ETSY_OAUTH_AUTHORIZE_URL = "https://www.etsy.com/oauth/connect"
ETSY_OAUTH_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
ETSY_OAUTH_REDIRECT_URI = "http://localhost:3003/oauth/redirect"

# OAuth scopes needed across all modules
ETSY_OAUTH_SCOPES = "listings_r transactions_r shops_r profile_r"

# Rate limits (your approved limits)
QPS_LIMIT = 5      # queries per second
QPD_LIMIT = 5000   # queries per day

# Collection settings
MIN_LISTINGS_PER_SAMPLE = 25
SAMPLE_B_DELAY_HOURS = 48
CALIBRATION_OVERLAP_THRESHOLD = 0.4  # 40% Jaccard overlap minimum to pass gate

# Etsy ToS: listing data can't be displayed if older than 6 hours
MAX_DISPLAY_AGE_HOURS = 6

# Dream Lab
DREAM_LAB_MODEL = "claude-sonnet-4-6"
DREAM_LAB_MAX_TOKENS = 2048

# Database
DB_PATH = "data/noctis.db"
