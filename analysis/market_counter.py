# analysis/market_counter.py

from collections import defaultdict

# ─────────────────────────────────────────────
#  BUILD MARKET INDEX
# ─────────────────────────────────────────────

def build_market_index(pim_map: dict) -> dict:
    """
    Build a reverse index:
        { brand_code (str) -> { description, skus: set } }

    Each PIM product carries a list of customerLabels:
        [ { "code": "DL", "description": "Widex Storefront" }, ... ]

    A product is counted once per market it belongs to.
    """
    index = {}

    for sku, product in pim_map.items():
        for label in product.get("customer_labels", []):
            code = label.get("code", "").strip().upper()
            desc = label.get("description", "")
            if not code:
                continue
            if code not in index:
                index[code] = {"description": desc, "skus": set()}
            index[code]["skus"].add(sku)

    return index

# ─────────────────────────────────────────────
#  QUERY HELPERS
# ─────────────────────────────────────────────

def list_all_markets(market_index: dict) -> list:
    """
    Return all markets sorted by code as a list of dicts:
        [ { "code", "description", "count" }, ... ]
    """
    return sorted(
        [
            {
                "code":        code,
                "description": entry["description"],
                "count":       len(entry["skus"]),
            }
            for code, entry in market_index.items()
        ],
        key=lambda x: x["code"],
    )

def get_market_products(brand_code: str, market_index: dict, pim_map: dict) -> dict:
    """
    Return detailed info for a specific brand_code:
        {
            "code":        str,
            "description": str,
            "count":       int,
            "by_type":     { product_type -> [sku, ...] },
            "skus":        [ { sku, name, product_type }, ... ]
        }
    Returns None if the code is not found.
    """
    code  = brand_code.strip().upper()
    entry = market_index.get(code)
    if not entry:
        return None

    by_type  = defaultdict(list)
    products = []

    for sku in sorted(entry["skus"]):
        prod  = pim_map.get(sku, {})
        ptype = prod.get("product_type", "UNKNOWN")
        by_type[ptype].append(sku)
        products.append({
            "sku":          sku,
            "name":         prod.get("name", ""),
            "product_type": ptype,
        })

    return {
        "code":        code,
        "description": entry["description"],
        "count":       len(entry["skus"]),
        "by_type":     dict(by_type),
        "skus":        products,
    }

def search_market_by_description(query: str, market_index: dict) -> list:
    """
    Case-insensitive partial match on market description or code.
    Returns list of matching { code, description, count }.
    """
    q = query.strip().lower()
    return [
        {
            "code":        code,
            "description": entry["description"],
            "count":       len(entry["skus"]),
        }
        for code, entry in market_index.items()
        if q in entry["description"].lower() or q in code.lower()
    ]
