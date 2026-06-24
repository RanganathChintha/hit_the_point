from config import PIM_TO_STOREFRONT_TYPE

def compare_types(pim_entry: dict, storefront_entry: dict) -> dict:
    """Compare PIM product type against the expected Storefront type."""
    pt = pim_entry.get("product_type", "unknown")
    ft = storefront_entry.get("type_id", "unknown") if storefront_entry else "NOT FOUND"

    expected = PIM_TO_STOREFRONT_TYPE.get(pt, set())
    match    = ft in expected

    return {
        "pim_type":      pt,
        "storefront_type":   ft,
        "types_match":   match,
        "mismatch_note": (
            f"PIM type '{pt}' expects Storefront type in {expected}, "
            f"but Storefront has '{ft}'"
        ) if not match else None,
    }
