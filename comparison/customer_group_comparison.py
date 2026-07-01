"""
Customer group comparison between PIM customer labels and Magento customer groups.

For each SKU:
- PIM provides customerLabels (each has a code like "DL", "GA", "AC", "AX")
- Magento provides customer_group_code entries (e.g. "widex_fr_GA" where "GA" is the suffix)
- We compare every PIM label code against all Magento suffixes for that SKU
- Comparison is bidirectional: shows what's in PIM but not Magento AND vice versa
"""


def compare_customer_groups(sku: str, pim_map: dict, magento_groups: dict) -> dict:
    """
    Compare PIM customer labels against Magento customer groups for a single SKU.
    Bidirectional: shows groups unique to each system and shared groups.

    "Fully matched" means:
      - Every PIM group is also in Magento, AND
      - Every Magento group is also in PIM.
    A difference in EITHER direction is a problem.

    Returns:
        {
            "sku": str,
            "pim_groups":        [{"code": str, "description": str}, ...],
            "magento_groups":      [str, ...],
            "shared":            [str, ...],              -- present in both
            "pim_only":          [str, ...],              -- in PIM but not Magento
            "magento_only":      [str, ...],              -- in Magento but not PIM
            "match_count":       int,                     -- number of shared groups
            "total_pim_groups":   int,
            "total_magento_groups": int,
            "fully_matched":    bool,                     -- no pim_only AND no magento_only
            "missing_in_magento": bool,                   -- pim_only > 0
            "missing_in_pim":     bool,                   -- magento_only > 0
        }
    """
    pim_entry = pim_map.get(sku)
    pim_labels = (
        pim_entry.get("customer_labels", [])
        if pim_entry else []
        
    )

    pim_groups = {
        (cl.get("code") or "").strip().upper(): cl.get("description", "")
        for cl in pim_labels
        if cl.get("code")
    }

    magento_codes = sorted(magento_groups.get(sku, set()))
    pim_codes = sorted(pim_groups.keys())

    shared = set(pim_codes) & set(magento_codes)
    pim_only = set(pim_codes) - set(magento_codes)
    magento_only = set(magento_codes) - set(pim_codes)

    # For the legacy fields, maintain backward compatibility
    market_matches = []
    for code in pim_codes:
        market_matches.append({"code": code, "matched": code in shared})

    # Bidirectional "fully matched": nothing unique on either side.
    fully_matched = len(pim_only) == 0 and len(magento_only) == 0

    return {
        "sku": sku,
        "pim_groups": [{"code": c, "description": pim_groups[c]} for c in pim_codes],
        "magento_groups": magento_codes,
        "shared": sorted(shared),
        "pim_only": sorted(pim_only),
        "magento_only": sorted(magento_only),
        "match_count": len(shared),
        "total_pim_groups": len(pim_codes),
        "total_magento_groups": len(magento_codes),
        "fully_matched": fully_matched,
        "missing_in_magento": len(pim_only) > 0,
        "missing_in_pim": len(magento_only) > 0,
    }


def batch_compare_customer_groups(pim_map: dict, magento_groups: dict, magento_map: dict = None) -> list:
    """
    Run compare_customer_groups for every SKU in PIM.

    If magento_map is provided, only SKUs that also exist in the Magento
    product catalog are included. This ensures we start from PIM as the
    source of truth and only compare against SKUs actually present in Magento.
    """
    skus = set(pim_map.keys())
    if magento_map is not None:
        skus = {sku for sku in skus if sku in magento_map}

    results = []
    for sku in sorted(skus):
        results.append(compare_customer_groups(sku, pim_map, magento_groups))
    return results
