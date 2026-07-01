from comparison.orchestrator import compare_product
from reporting.html_reporter import generate_html_report

def compare_single_sku_html(
    pim_sku: str,
    pim_map: dict,
    magento_map: dict,
    id_to_sku: dict,
    output_path: str = "single_report.html",
    magento_cat_tree: list | None = None,
) -> str:
    """Compare a single SKU and generate HTML report."""
    compare_product(pim_sku, pim_map, magento_map, id_to_sku, magento_cat_tree)
    return generate_html_report(pim_map, magento_map, id_to_sku, output_path, magento_cat_tree)

def compare_single_sku(pim_sku: str, pim_map: dict, magento_map: dict, id_to_sku: dict) -> dict:
    """Compare a single SKU and return the result."""
    return compare_product(pim_sku, pim_map, magento_map, id_to_sku)