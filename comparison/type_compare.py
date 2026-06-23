from config import PIM_TO_FRANCE_TYPE

def compare_types(pim_entry: dict, france_entry: dict) -> dict:
    """Compare PIM product type against the expected France type."""
    pt = pim_entry.get("product_type", "unknown")
    ft = france_entry.get("type_id", "unknown") if france_entry else "NOT FOUND"

    expected = PIM_TO_FRANCE_TYPE.get(pt, set())
    match    = ft in expected

    return {
        "pim_type":      pt,
        "france_type":   ft,
        "types_match":   match,
        "mismatch_note": (
            f"PIM type '{pt}' expects France type in {expected}, "
            f"but France has '{ft}'"
        ) if not match else None,
    }
