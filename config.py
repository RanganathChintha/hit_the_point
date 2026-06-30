# ─────────────────────────────────────────────
#  FILE PATHS & CONSTANTS
# ─────────────────────────────────────────────

MAGENTO_PRODUCTS_FILE  = "data/france_products.json"
MAGENTO_CAT_FILE       = "data/france_categories.json"
PIM_PRODUCTS_FILE     = "data/pim_prod.json"
PIM_CAT_FILE          = "data/pim_cat.json"

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
