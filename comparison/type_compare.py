from config import PIM_TO_MAGENTO_TYPE

def compare_types(pim_entry: dict, magento_entry: dict) -> dict:
    """Compare PIM product type against the expected Magento type."""
    pt = pim_entry.get("product_type", "unknown")
    ft = magento_entry.get("type_id", "unknown") if magento_entry else "NOT FOUND"

    expected = PIM_TO_MAGENTO_TYPE.get(pt, set())
    match    = ft in expected

    return {
        "pim_type":      pt,
        "magento_type":   ft,
        "types_match":   match,
        "mismatch_note": (
            f"PIM type '{pt}' expects Magento type in {expected}, "
            f"but Magento has '{ft}'"
        ) if not match else None,
    }
