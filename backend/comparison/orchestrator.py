from comparison.type_compare         import compare_types
from comparison.bundle_compare       import compare_bundle_slots
from comparison.configurable_compare import compare_configurable_children
from comparison.category_compare     import compare_category_links
from reporting.html_reporter         import generate_html_report

def compare_product(
    pim_sku:    str,
    pim_map:    dict,
    magento_map: dict,
    id_to_sku:  dict,
    magento_cat_tree: list | None = None,
) -> dict:
    """Run a full PIM-driven comparison for a single SKU."""
    pim_entry    = pim_map.get(pim_sku)
    magento_entry = magento_map.get(pim_sku)

    report = {
        "sku":                     pim_sku,
        "found_in_pim":            pim_entry    is not None,
        "found_in_magento":         magento_entry is not None,
        "type_comparison":         None,
        "bundle_comparison":       None,
        "configurable_comparison": None,
        "category_comparison":     None,
    }

    if not pim_entry:
        return report

    report["type_comparison"] = compare_types(pim_entry, magento_entry)
    report["category_comparison"] = compare_category_links(
        pim_entry,
        magento_entry,
        magento_cat_tree,
    )

    pt = pim_entry.get("product_type")
    ft = (magento_entry or {}).get("type_id")

    if pt == "BUNDLE" and ft == "bundle":
        report["bundle_comparison"] = compare_bundle_slots(pim_entry, magento_entry)

    elif pt == "PRODUCT" and ft == "configurable":
        report["configurable_comparison"] = compare_configurable_children(
            pim_entry, magento_entry, id_to_sku
        )

    return report

def batch_compare(pim_map: dict, magento_map: dict, id_to_sku: dict, magento_cat_tree: list | None = None) -> list:
    """Run compare_product() for every SKU in PIM."""
    return [
        compare_product(sku, pim_map, magento_map, id_to_sku, magento_cat_tree)
        for sku in sorted(pim_map)
    ]

def batch_compare_html(
    pim_map: dict,
    magento_map: dict,
    id_to_sku: dict,
    output_path: str = "batch_report.html",
    magento_cat_tree: list | None = None,
) -> str:
    """Run batch comparison and generate HTML report."""
    batch_compare(pim_map, magento_map, id_to_sku, magento_cat_tree)
    return generate_html_report(pim_map, magento_map, id_to_sku, output_path, magento_cat_tree)