import os
from pathlib import Path


def _load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader; no external dependency needed."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


_load_dotenv()

# ─────────────────────────────────────────────
#  FILE PATHS & CONSTANTS
# ─────────────────────────────────────────────

MAGENTO_PRODUCTS_FILE        = os.getenv("MAGENTO_PRODUCTS_FILE", "")
MAGENTO_CAT_FILE             = os.getenv("MAGENTO_CAT_FILE", "")
MAGENTO_CUSTOMER_GROUP_FILE = "data/magento_customer_group.json"
PIM_PRODUCTS_FILE            = "data/pim_prod.json"
PIM_CAT_FILE                 = "data/pim_cat.json"

# Magento website ID is declared here in config.py and forwarded to fetchers.
# Do not declare this in .env; change it only in this file.
MAGENTO_WEBSITE_ID = 12

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

# Credentials — loaded from .env (safe for sensitive data)
MAGENTO_BASE_URL   = os.getenv("MAGENTO_BASE_URL",   "")
MAGENTO_USERNAME   = os.getenv("MAGENTO_USERNAME",   "")
MAGENTO_PASSWORD   = os.getenv("MAGENTO_PASSWORD",   "")
# Magento website ID is configured in config.py only.
# MAGENTO_WEBSITE_ID from .env is ignored intentionally.

# Tuning constants
MAGENTO_API_PAGE_SIZE   = 100  # Safe page size
MAGENTO_API_DELAY       = 0.5  # Seconds between requests
MAGENTO_API_MAX_RETRIES = 5    # Retry attempts per page
MAGENTO_API_RETRY_DELAY = 10   # Seconds before retry

# Output directory for fetched data
DATA_DIR = "data"


def _find_latest_magento_output(suffix: str, default_path: str) -> str:
    directory = Path(DATA_DIR)
    if not directory.exists():
        return default_path

    candidates = sorted(
        directory.glob(f"*{suffix}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return str(candidates[0])
    return default_path


def get_magento_products_file() -> str:
    if MAGENTO_PRODUCTS_FILE:
        return MAGENTO_PRODUCTS_FILE
    return _find_latest_magento_output("_products.json", "data/france_products.json")


def get_magento_cat_file() -> str:
    if MAGENTO_CAT_FILE:
        return MAGENTO_CAT_FILE
    return _find_latest_magento_output("_categories.json", "data/france_categories.json")
