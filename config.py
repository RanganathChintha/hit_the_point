# ─────────────────────────────────────────────
#  FILE PATHS & CONSTANTS
# ─────────────────────────────────────────────

MAGENTO_PRODUCTS_FILE        = "data/france_products.json"
MAGENTO_CAT_FILE             = "data/france_categories.json"
MAGENTO_CUSTOMER_GROUP_FILE = "data/magento_customer_group.json"
PIM_PRODUCTS_FILE            = "data/pim_prod.json"
PIM_CAT_FILE                 = "data/pim_cat.json"

# Maps PIM product type → accepted Magento type(s)
PIM_TO_MAGENTO_TYPE = {
    "PRODUCT":         {"configurable", "simple"},
    "BUNDLE":          {"bundle"},
    "PRODUCT_VARIANT": {"simple"},
}

SEP  = "═" * 70
OK   = "✅"
ERR  = "❌"
WARN = "⚠️ "
INFO = "ℹ️ "

# ─────────────────────────────────────────────
#  MAGENTO API FETCHER CONFIG
# ─────────────────────────────────────────────
import os
from dotenv import load_dotenv

# Load .env from project root (clever: no hard path needed)
_ = load_dotenv()

# Credentials — loaded from .env (safe for sensitive data)
MAGENTO_BASE_URL   = os.getenv("MAGENTO_BASE_URL",   "")
MAGENTO_USERNAME   = os.getenv("MAGENTO_USERNAME",   "")
MAGENTO_PASSWORD   = os.getenv("MAGENTO_PASSWORD",   "")
MAGENTO_WEBSITE_ID = int(os.getenv("MAGENTO_WEBSITE_ID", "0"))

# Tuning constants
MAGENTO_API_PAGE_SIZE   = 100  # Safe page size
MAGENTO_API_DELAY       = 0.5  # Seconds between requests
MAGENTO_API_MAX_RETRIES = 5    # Retry attempts per page
MAGENTO_API_RETRY_DELAY = 10   # Seconds before retry

# Output directory for fetched data
DATA_DIR = "data"
