def compare_configurable_children(
    pim_entry:    dict,
    storefront_entry: dict,
    id_to_sku:    dict,
) -> dict:
    """Compare PIM configurable children against Storefront configurable links."""
    pim_skus       = set(pim_entry.get("child_skus", []))
    storefront_ids     = (storefront_entry or {}).get("configurable_child_ids", [])
    storefront_skus    = set()
    unresolved_ids = []

    for fid in storefront_ids:
        sku = id_to_sku.get(int(fid))
        if sku:
            storefront_skus.add(sku)
        else:
            unresolved_ids.append(fid)

    return {
        "pim_child_count":       len(pim_skus),
        "storefront_child_count":    len(storefront_ids),
        "count_match":           len(pim_skus) == len(storefront_skus),
        "pim_child_skus":        sorted(pim_skus),
        "storefront_child_skus":     sorted(storefront_skus),
        "skus_only_in_pim":      sorted(pim_skus    - storefront_skus),
        "skus_only_in_storefront":   sorted(storefront_skus - pim_skus),
        "skus_in_both":          sorted(pim_skus    & storefront_skus),
        "unresolved_storefront_ids": unresolved_ids,
    }
