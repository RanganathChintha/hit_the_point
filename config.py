# ─────────────────────────────────────────────
#  FILE PATHS & CONSTANTS
# ─────────────────────────────────────────────

FRANCE_PRODUCTS_FILE  = "data/france_products.json"
FRANCE_CAT_FILE       = "data/france_categories.json"
PIM_PRODUCTS_FILE     = "data/pim_prod.json"
PIM_CAT_FILE          = "data/pim_cat.json"

# Maps PIM product type → accepted France type(s)
PIM_TO_FRANCE_TYPE = {
    "PRODUCT":         {"configurable", "simple"},
    "BUNDLE":          {"bundle"},
    "PRODUCT_VARIANT": {"simple"},
}

SEP  = "═" * 70
OK   = "✅"
ERR  = "❌"
WARN = "⚠️ "
INFO = "ℹ️ "
