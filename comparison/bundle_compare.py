from loaders.pim_loader import normalize_slot

def compare_bundle_slots(pim_entry: dict, storefront_entry: dict) -> dict:
    """Compare PIM bundle sets against Storefront bundle slots."""
    pim_slots    = {normalize_slot(k): v for k, v in pim_entry.get("bundle_sets",  {}).items()}
    storefront_slots = {normalize_slot(k): v for k, v in (storefront_entry or {}).get("bundle_slots", {}).items()}

    all_slots   = set(pim_slots) | set(storefront_slots)
    only_pim    = sorted(set(pim_slots)    - set(storefront_slots))
    only_storefront = sorted(set(storefront_slots) - set(pim_slots))

    per_slot = {}
    for slot in sorted(all_slots):
        p_skus = set(pim_slots.get(slot,    {}).get("skus", []))
        f_skus = set(storefront_slots.get(slot, {}).get("skus", []))
        per_slot[slot] = {
            "pim_sku_count":       len(p_skus),
            "storefront_sku_count":    len(f_skus),
            "count_match":         len(p_skus) == len(f_skus),
            "skus_only_in_pim":    sorted(p_skus - f_skus),
            "skus_only_in_storefront": sorted(f_skus - p_skus),
            "skus_in_both":        sorted(p_skus & f_skus),
        }

    return {
        "pim_slot_count":       len(pim_slots),
        "storefront_slot_count":    len(storefront_slots),
        "slot_count_match":     len(pim_slots) == len(storefront_slots),
        "slots_only_in_pim":    only_pim,
        "slots_only_in_storefront": only_storefront,
        "per_slot":             per_slot,
    }
