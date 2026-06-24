from comparison.orchestrator import compare_product
from reporting.html_reporter import generate_html_report

def compare_single_sku_html(pim_sku: str, pim_map: dict, france_map: dict, id_to_sku: dict, output_path: str = "single_report.html") -> str:
    """Compare a single SKU and generate HTML report."""
    result = compare_product(pim_sku, pim_map, france_map, id_to_sku)
    return generate_html_report(pim_map, france_map, id_to_sku, output_path)

def compare_single_sku(pim_sku: str, pim_map: dict, france_map: dict, id_to_sku: dict) -> dict:
    """Compare a single SKU and return the result."""
    return compare_product(pim_sku, pim_map, france_map, id_to_sku)