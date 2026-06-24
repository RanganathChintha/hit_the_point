# ─────────────────────────────────────────────
#  FILE PATHS & CONSTANTS
# ─────────────────────────────────────────────

STOREFRONT_PRODUCTS_FILE  = "data/france_products.json"
STOREFRONT_CAT_FILE       = "data/france_categories.json"
PIM_PRODUCTS_FILE     = "data/pim_prod.json"
PIM_CAT_FILE          = "data/pim_cat.json"

# Maps PIM product type → accepted Storefront type(s)
PIM_TO_STOREFRONT_TYPE = {
    "PRODUCT":         {"configurable", "simple"},
    "BUNDLE":          {"bundle"},
    "PRODUCT_VARIANT": {"simple"},
}

SEP  = "═" * 70
OK   = "✅"
ERR  = "❌"
WARN = "⚠️ "
INFO = "ℹ️ "
