"""
Market matching comparison between PIM customer labels and Magento customer groups.

For each SKU:
- PIM provides customerLabels (each has a code like "DL", "GA", "AC", "AX")
- Magento provides customer_group_code entries (e.g. "widex_fr_GA" where "GA" is the suffix)
- We compare every PIM label code against all Magento suffixes for that SKU
"""


def compare_markets(sku: str, pim_map: dict, magento_groups: dict) -> dict:
    """
    Compare PIM customer labels against Magento customer group codes for a single SKU.

    Returns:
        {
            "sku": str,
            "pim_markets":      [{"code": str, "description": str}, ...],
            "magento_markets":  [str, ...],
            "market_matches":   [{"code": str, "matched": bool}, ...],
            "match_count":      int,
            "total_pim_markets": int,
            "fully_matched":    bool,
        }
    """
    pim_entry = pim_map.get(sku)
    pim_labels = (
        pim_entry.get("customer_labels", [])
        if pim_entry else []
    )

    pim_markets = [
        {"code": (cl.get("code") or "").strip().upper(),
         "description": cl.get("description", "")}
        for cl in pim_labels
        if cl.get("code")
    ]

    magento_codes = sorted(magento_groups.get(sku, set()))

    market_matches = []
    for pm in pim_markets:
        code = pm["code"]
        matched = code in magento_groups.get(sku, set())
        market_matches.append({"code": code, "matched": matched})

    match_count = sum(1 for m in market_matches if m["matched"])
    fully_matched = match_count == len(pim_markets) if pim_markets else True

    return {
        "sku": sku,
        "pim_markets": pim_markets,
        "magento_markets": magento_codes,
        "market_matches": market_matches,
        "match_count": match_count,
        "total_pim_markets": len(pim_markets),
        "fully_matched": fully_matched,
    }


def batch_compare_markets(pim_map: dict, magento_groups: dict) -> list:
    """
    Run compare_markets for every SKU that exists in either PIM or Magento groups.
    """
    all_skus = set(pim_map.keys()) | set(magento_groups.keys())
    results = []
    for sku in sorted(all_skus):
        results.append(compare_markets(sku, pim_map, magento_groups))
    return results
