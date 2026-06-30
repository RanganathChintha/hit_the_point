def compare_configurable_children(
    pim_entry:    dict,
    magento_entry: dict,
    id_to_sku:    dict,
) -> dict:
    """Compare PIM configurable children against Magento configurable links."""
    pim_skus       = set(pim_entry.get("child_skus", []))
    magento_ids     = (magento_entry or {}).get("configurable_child_ids", [])
    magento_skus    = set()
    unresolved_ids = []

    for fid in magento_ids:
        sku = id_to_sku.get(int(fid))
        if sku:
            magento_skus.add(sku)
        else:
            unresolved_ids.append(fid)

    return {
        "pim_child_count":       len(pim_skus),
        "magento_child_count":    len(magento_ids),
        "count_match":           len(pim_skus) == len(magento_skus),
        "pim_child_skus":        sorted(pim_skus),
        "magento_child_skus":     sorted(magento_skus),
        "skus_only_in_pim":      sorted(pim_skus    - magento_skus),
        "skus_only_in_magento":   sorted(magento_skus - pim_skus),
        "skus_in_both":          sorted(pim_skus    & magento_skus),
        "unresolved_magento_ids": unresolved_ids,
    }
