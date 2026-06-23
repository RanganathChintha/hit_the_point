def compare_configurable_children(
    pim_entry:    dict,
    france_entry: dict,
    id_to_sku:    dict,
) -> dict:
    """Compare PIM configurable children against France configurable links."""
    pim_skus       = set(pim_entry.get("child_skus", []))
    france_ids     = (france_entry or {}).get("configurable_child_ids", [])
    france_skus    = set()
    unresolved_ids = []

    for fid in france_ids:
        sku = id_to_sku.get(int(fid))
        if sku:
            france_skus.add(sku)
        else:
            unresolved_ids.append(fid)

    return {
        "pim_child_count":       len(pim_skus),
        "france_child_count":    len(france_ids),
        "count_match":           len(pim_skus) == len(france_skus),
        "pim_child_skus":        sorted(pim_skus),
        "france_child_skus":     sorted(france_skus),
        "skus_only_in_pim":      sorted(pim_skus    - france_skus),
        "skus_only_in_france":   sorted(france_skus - pim_skus),
        "skus_in_both":          sorted(pim_skus    & france_skus),
        "unresolved_france_ids": unresolved_ids,
    }
