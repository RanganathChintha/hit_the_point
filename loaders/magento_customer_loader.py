import json

def parse_magento_customer_groups(path: str) -> dict:
    """
    Parse a Magento customer-group JSON file into a dict:
        { sku -> set of customer group suffix codes }

    The JSON structure is:
        { "SELECT ...": [ { "sku": "...", "customer_group_code": "widex_fr_GA" }, ... ] }

    The suffix (e.g. "GA") is the last segment after the final underscore.
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # The JSON has a single key (the SQL query); unwrap it.
    items = list(raw.values())[0] if raw else []

    result = {}
    for item in items:
        sku = item.get("sku")
        code = item.get("customer_group_code", "")
        if not sku or not code:
            continue
        # Extract suffix after the last underscore
        suffix = code.split("_")[-1].upper()
        result.setdefault(sku, set()).add(suffix)

    return result


def build_sku_market_map(path: str) -> dict:
    """
    Alias for parse_magento_customer_groups for backward-compatibility.
    """
    return parse_magento_customer_groups(path)
