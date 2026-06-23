from loaders.pim_loader import normalize_slot

def compare_bundle_slots(pim_entry: dict, france_entry: dict) -> dict:
    """Compare PIM bundle sets against France bundle slots."""
    pim_slots    = {normalize_slot(k): v for k, v in pim_entry.get("bundle_sets",  {}).items()}
    france_slots = {normalize_slot(k): v for k, v in (france_entry or {}).get("bundle_slots", {}).items()}

    all_slots   = set(pim_slots) | set(france_slots)
    only_pim    = sorted(set(pim_slots)    - set(france_slots))
    only_france = sorted(set(france_slots) - set(pim_slots))

    per_slot = {}
    for slot in sorted(all_slots):
        p_skus = set(pim_slots.get(slot,    {}).get("skus", []))
        f_skus = set(france_slots.get(slot, {}).get("skus", []))
        per_slot[slot] = {
            "pim_sku_count":       len(p_skus),
            "france_sku_count":    len(f_skus),
            "count_match":         len(p_skus) == len(f_skus),
            "skus_only_in_pim":    sorted(p_skus - f_skus),
            "skus_only_in_france": sorted(f_skus - p_skus),
            "skus_in_both":        sorted(p_skus & f_skus),
        }

    return {
        "pim_slot_count":       len(pim_slots),
        "france_slot_count":    len(france_slots),
        "slot_count_match":     len(pim_slots) == len(france_slots),
        "slots_only_in_pim":    only_pim,
        "slots_only_in_france": only_france,
        "per_slot":             per_slot,
    }
