from loaders.pim_loader import normalize_slot

def compare_bundle_slots(pim_entry: dict, magento_entry: dict) -> dict:
    """Compare PIM bundle sets against Magento bundle slots."""
    pim_slots    = {normalize_slot(k): v for k, v in pim_entry.get("bundle_sets",  {}).items()}
    magento_slots = {normalize_slot(k): v for k, v in (magento_entry or {}).get("bundle_slots", {}).items()}

    all_slots   = set(pim_slots) | set(magento_slots)
    only_pim    = sorted(set(pim_slots)    - set(magento_slots))
    only_magento = sorted(set(magento_slots) - set(pim_slots))

    per_slot = {}
    for slot in sorted(all_slots):
        p_skus = set(pim_slots.get(slot,    {}).get("skus", []))
        f_skus = set(magento_slots.get(slot, {}).get("skus", []))
        per_slot[slot] = {
            "pim_sku_count":       len(p_skus),
            "magento_sku_count":    len(f_skus),
            "count_match":         len(p_skus) == len(f_skus),
            "skus_only_in_pim":    sorted(p_skus - f_skus),
            "skus_only_in_magento": sorted(f_skus - p_skus),
            "skus_in_both":        sorted(p_skus & f_skus),
        }

    return {
        "pim_slot_count":       len(pim_slots),
        "magento_slot_count":    len(magento_slots),
        "slot_count_match":     len(pim_slots) == len(magento_slots),
        "slots_only_in_pim":    only_pim,
        "slots_only_in_magento": only_magento,
        "per_slot":             per_slot,
    }
